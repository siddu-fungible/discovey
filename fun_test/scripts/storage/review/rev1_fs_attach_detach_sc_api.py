from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import get_data_collection_time
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from lib.templates.storage.storage_controller_api import *
from scripts.storage.storage_helper import *
from lib.system.utils import *
from lib.host.storage_controller import *
from collections import OrderedDict, Counter
from math import ceil


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.log("Fio test for thread {}: {}".format(host_index, fio_output))
    arg1.disconnect()


class StripeVolAttachDetachTestScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):

        pass

    def cleanup(self):
        pass


class StripeVolAttachDetachTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        self.testcase = self.__class__.__name__

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        for k, v in config_dict[self.testcase].items():
            setattr(self, k, v)

        fun_test.log("Config Config: {}".format(self.__dict__))

    def run(self):
        testcase = self.__class__.__name__

        fun_test.shared_variables["stripe_vol"] = {}
        fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_output = {}
        test_thread_id = {}
        host_clone = {}
        self.pcap_started = {}
        self.pcap_stopped = {}
        self.pcap_pid = {}
        fun_test.shared_variables["fio"] = {}

        fun_test.shared_variables["stripe_uuid"] = "54c3165dfd874df0"
        self.stripe_uuid = fun_test.shared_variables["stripe_uuid"]
        fun_test.shared_variables["attach_detach_count"] = self.attach_detach_count

        self.sc_api = StorageControllerApi(api_server_ip="10.1.105.58",
                                           api_server_port=50220, username="admin",
                                           password="password")

        self.num_hosts = 1
        self.host_info = OrderedDict()
        host_name = "cab02-qa-10"
        host_handle = Linux(host_ip=host_name, ssh_username="localadmin", ssh_password="Precious1*")

        self.host_info[host_name] = {}
        self.host_info[host_name]["handle"] = host_handle
        self.host_info[host_name]["ip"] = ['15.1.15.3']

        if hasattr(self, "create_file_system") and self.create_file_system:
            test_filename = "/mnt/testfile.dat"
        else:
            test_filename = "/dev/nvme0n1"

        if self.attach_detach_loop:
            for iteration in range(self.attach_detach_count):
                fun_test.log("Iteration: {} - Executing Attach Detach in loop".format(iteration))
                fun_test.sleep("before attaching volume", self.attach_detach_wait)
                self.pcap_started[iteration] = {}
                self.pcap_stopped[iteration] = {}
                self.pcap_pid[iteration] = {}

                for index, host_name in enumerate(self.host_info):
                    # Attaching volume to NVMeOF controller
                    # host_handle = self.host_info[host_name]["handle"]
                    attach_volume = self.sc_api.volume_attach_remote(vol_uuid=self.stripe_uuid,
                                                                     transport=self.transport_type.upper(),
                                                                     remote_ip=self.host_info[host_name]["ip"][0])
                    fun_test.log("Iteration {} - Attach volume API response: {}".format(iteration, attach_volume))
                    fun_test.test_assert(attach_volume["status"],
                                         "Iteration: {} - Attach stripe vol {} over {} for host {}".
                                         format(iteration, self.stripe_uuid, self.transport_type.upper(), host_name))
                    self.nqn = "nqn-1"
                    self.detach_uuid = attach_volume["data"]["uuid"]
                    hostnqn = "15.1.15.3"

                    if self.nvme_connect:
                        # test_interface = self.host_info[host_name]["test_interface"].name
                        test_interface = "enp216s0"
                        self.pcap_started[iteration][host_name] = False
                        self.pcap_stopped[iteration][host_name] = True
                        self.pcap_pid[iteration][host_name] = {}
                        tcpdump_filename = "/tmp/nvme_connect_iter_{}.pcap".format(iteration)
                        self.pcap_pid[iteration][host_name] = host_handle.tcpdump_capture_start(
                            interface=test_interface, tcpdump_filename=tcpdump_filename, snaplen=1500)
                        if self.pcap_pid[iteration][host_name]:
                            fun_test.log("Iteration: {} - Started packet capture in {}".format(iteration,
                                                                                               host_name))
                            self.pcap_started[iteration][host_name] = True
                            self.pcap_stopped[iteration][host_name] = False
                        else:
                            fun_test.critical("Iteration: {} - Unable to start packet capture in {}".
                                              format(iteration, host_name))

                        if not fun_test.shared_variables["stripe_vol"]["nvme_connect"]:
                            # Checking nvme-connect status
                            if not hasattr(self, "nvme_io_queues") or self.nvme_io_queues != 0:
                                nvme_connect_status = host_handle.nvme_connect(
                                    target_ip="15.47.1.2", nvme_subsystem=self.nqn,
                                    port=self.transport_port, transport=self.transport_type.lower(),
                                    nvme_io_queues=self.nvme_io_queues, hostnqn=hostnqn)
                            else:
                                nvme_connect_status = host_handle.nvme_connect(
                                    target_ip="15.47.1.2", nvme_subsystem=self.nqn,
                                    port=self.transport_port, transport=self.transport_type.lower(),
                                    hostnqn=hostnqn)

                            if self.pcap_started[iteration][host_name]:
                                host_handle.tcpdump_capture_stop(process_id=self.pcap_pid[iteration][host_name])
                                self.pcap_stopped[iteration][host_name] = True

                            fun_test.test_assert(nvme_connect_status,
                                                 message="Iteration: {} - {} - NVME Connect Status".
                                                 format(iteration, host_name))

                            lsblk_output = host_handle.lsblk("-b")
                            fun_test.simple_assert(lsblk_output, "Listing available volumes")

                            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(
                                self.stripe_details["ns_id"])
                            host_handle.sudo_command("dmesg -c")
                            lsblk_output = host_handle.lsblk()
                            fun_test.test_assert(self.volume_name in lsblk_output,
                                                 "Iteration: {} - {} device available".format(iteration,
                                                                                              self.volume_name))
                            fun_test.test_assert_expected(expected="disk",
                                                          actual=lsblk_output[self.volume_name]["type"],
                                                          message="Iteration: {} - {} device type check".
                                                          format(iteration, self.volume_name))
                            fun_test.shared_variables["stripe_vol"]["nvme_connect"] = True

                    if self.io_during_attach_detach:
                        wait_time = self.num_hosts - index
                        host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                        # Starting Read for whole volume on first host
                        test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                              func=fio_parser,
                                                                              arg1=host_clone[host_name],
                                                                              host_index=index,
                                                                              filename=test_filename,
                                                                              **self.fio_cmd_args)

                    if self.disconnect_detach_during_io:
                        if self.disconnect_before_detach:
                            fun_test.sleep("Iteration: {} - before disconnect".format(iteration), self.nvme_disconn_wait)
                            try:
                                fun_test.log("Disconnecting volume from the host")
                                # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)  # TODO: SWOS-6165
                                nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)
                                host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                                nvme_disconnect_exit_status = host_handle.exit_status()
                                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                              message="Iteration: {} - {} - NVME Disconnect Status".
                                                              format(iteration, host_name))
                                fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
                            except Exception as ex:
                                fun_test.critical(str(ex))
                        try:
                            # Detach volume from NVMe-OF controller
                            detach_volume = self.sc_api.detach_volume(port_uuid=self.detach_uuid)
                            fun_test.log("Iteration: {} - Detach volume API response: {}".format(iteration,
                                                                                                 detach_volume))
                            fun_test.test_assert(detach_volume["status"],
                                                 "Iteration: {} - {} - Detach NVMeOF controller".
                                                 format(iteration, host_name))
                        except Exception as ex:
                            fun_test.critical(str(ex))

                if self.io_during_attach_detach:
                    # Waiting for all the FIO test threads to complete
                    try:
                        fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                        for index, host_name in enumerate(self.host_info):
                            fio_output[host_name] = {}
                            fun_test.log("Joining fio thread {}".format(index))
                            fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                            if self.disconnect_detach_during_io:
                                if fun_test.shared_variables["fio"][index]:
                                    fun_test.add_checkpoint(
                                        "Iteration: {} - FIO output on Disconnect and Detach during an IO on {}".
                                            format(iteration, host_name), "PASSED")
                                else:
                                    fun_test.add_checkpoint(
                                        "Iteration: {} - FIO output on Disconnect and Detach during an IO on {}".
                                            format(iteration, host_name), "FAILED")
                            else:
                                fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                                     "Iteration: {} - FIO output before Disconnect and Detach on {}".
                                                     format(iteration, host_name))
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fun_test.log("FIO failure {}:\n {}".format(host_name, fun_test.shared_variables["fio"][index]))

                if not self.disconnect_detach_during_io:
                    if self.disconnect_before_detach:
                        fun_test.sleep("Iteration: {} - before disconnect".format(iteration), self.nvme_disconn_wait)
                        try:
                            fun_test.log("Disconnecting volume from the host")
                            # nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)  # TODO: SWOS-6165
                            nvme_disconnect_cmd = "nvme disconnect -d {}".format(self.volume_name)
                            host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                            nvme_disconnect_exit_status = host_handle.exit_status()
                            fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                          message="Iteration: {} - {} - NVME Disconnect Status".
                                                          format(iteration, host_name))
                            fun_test.shared_variables["stripe_vol"]["nvme_connect"] = False
                        except Exception as ex:
                            fun_test.critical(str(ex))
                    try:
                        # Detach volume from NVMe-OF controller
                        detach_volume = self.sc_api.detach_volume(port_uuid=self.detach_uuid)
                        fun_test.log("Iteration: {} - Detach volume API response: {}".format(iteration,
                                                                                             detach_volume))
                        fun_test.test_assert(detach_volume["status"], "Iteration: {} - {} - Detach NVMeOF controller".
                                             format(iteration, host_name))
                    except Exception as ex:
                        fun_test.critical(str(ex))
        else:
            for index, host_name in enumerate(self.host_info):
                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                # Starting Read for whole volume on first host
                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      filename=test_filename,
                                                                      **self.fio_cmd_args)
            # Waiting for all the FIO test threads to complete
            try:
                fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                for index, host_name in enumerate(self.host_info):
                    fio_output[host_name] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                           fun_test.shared_variables["fio"][index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))

        fun_test.sleep("Waiting in between iterations", self.iter_interval)

    def cleanup(self):
        try:
            bmc_handle = Linux(host_ip='10.1.105.53', ssh_username="sysadmin", ssh_password="superuser")
            uart_post_fix_name = "fs47_f1_0_uart_log.txt"
            uart_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=uart_post_fix_name)
            fun_test.scp(source_port=bmc_handle.ssh_port, source_username=bmc_handle.ssh_username,
                         source_password=bmc_handle.ssh_password, source_ip=bmc_handle.host_ip,
                         source_file_path="/mnt/sdmmc0p1/log/funos_f1_0.log", target_file_path=uart_artifact_file)
            fun_test.add_auxillary_file(description="fs47_f1_0_uart_log.txt", filename=uart_artifact_file)

        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                for filename in ["/tmp/nvme_connect.pcap"]:
                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path=filename, target_file_path=pcap_artifact_file)
                fun_test.add_auxillary_file(description="{}: Host {} NVME connect pcap".
                                            format(self.testcase, host_name), filename=pcap_artifact_file)
        except Exception as ex:
            fun_test.critical(str(ex))


class StripedVolAttachConnDisConnDetachDisconnDuringIO(StripeVolAttachDetachTestCase):
    def describe(self):
        self.set_test_details(
            id=1,
            summary="Multiple Attach-NvmeConnect-NvmeDisconnect-Detach with IO - Disconnect & Detach During IO",
            steps='''
                1. Create Stripe volume
                2. Attach volume to one host
                3. Do nvme_connect and perform sequential write and nvme_disconnect and detach
                4. Perform Attach-NvmeConnect- IO With DI -NvmeDisconnect-Disconnect in loop
                5. Disconnect and Detach during Read-Write, FIO should fail
                ''')

    def setup(self):
        super(StripedVolAttachConnDisConnDetachDisconnDuringIO, self).setup()

    def run(self):
        super(StripedVolAttachConnDisConnDetachDisconnDuringIO, self).run()

    def cleanup(self):
        super(StripedVolAttachConnDisConnDetachDisconnDuringIO, self).cleanup()



if __name__ == "__main__":
    testscript = StripeVolAttachDetachTestScript()
    testscript.add_test_case(StripedVolAttachConnDisConnDetachDisconnDuringIO())
    testscript.run()
