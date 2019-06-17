from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.fun.fs import Fs
from scripts.storage.ec_perf_helper import *

'''
Sanity Script for EC Volume via NVME/TCP
'''


class ECVolumeSanityScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Setup COMe, launch DPC cli
        3. Configure Network interface between F1 and remote host.
        4. Create 4:2 EC volume and attach it to remote host.
        5. Execute write traffic to populate the EC volume.
        """)

    def setup(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        testbed_type = fun_test.get_job_environment_variable("test_bed_type")

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog_level = 6
            self.command_timeout = 5
            self.reboot_timeout = 300
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                           disable_f1_index=self.disable_f1_index)

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        fs = topology.get_dut_instance(index=0)
        come = fs.get_come()
        storage_controller = StorageController(target_ip=come.host_ip,
                                               target_port=come.get_dpc_port(self.f1_in_use))

        end_host = None
        test_interface_name = None
        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=self.f1_in_use)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            if "test_interface_name" in host_info["host_obj"].extra_attributes:
                if testbed_type == "fs-6" and host_ip != "poc-server-01":
                    continue
                end_host = host_info["host_obj"]
                test_interface_name = end_host.extra_attributes["test_interface_name"]
                fpg_inteface_index = host_info["interfaces"][self.f1_in_use].index
                fun_test.log("Test Interface is connected to FPG Index: {}".format(fpg_inteface_index))
                break
        else:
            fun_test.test_assert(end_host, "Fetch host with required test interface for configuration")

        test_network = self.csr_network[str(fpg_inteface_index)]
        remote_ip = test_network["test_interface_ip"].split('/')[0]

        fun_test.shared_variables["end_host"] = end_host
        fun_test.shared_variables["test_network"] = test_network
        fun_test.shared_variables["storage_controller"] = storage_controller
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables['topology'] = topology
        self.end_host = end_host
        self.storage_controller = storage_controller

        # configure end host
        # Ensure host is up
        # fun_test.test_assert(self.end_host.reboot(max_wait_time=self.reboot_timeout),
        #                     message="End Host is up")

        # end host network interface
        configure_endhost_interface(end_host=end_host, test_network=test_network,
                                    interface_name=test_interface_name)

        # load nvme
        load_nvme_module(end_host)
        # load nvme_tcp
        load_nvme_tcp_module(end_host)

        # enable_counters(storage_controller, self.command_timeout)

        # configure ip on fs
        fun_test.test_assert(storage_controller.ip_cfg(ip=test_network['f1_loopback_ip'])["status"],
                             "Configure IP {} on FS".format(test_network['f1_loopback_ip']))

        # create controller
        ctrlr_uuid = utils.generate_uuid()
        fun_test.test_assert(storage_controller.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                                  transport=self.attach_transport,
                                                                  remote_ip=remote_ip,
                                                                  nqn=self.nvme_subsystem,
                                                                  port=self.transport_port,
                                                                  command_duration=self.command_timeout)["status"],
                             "Create Storage Controller for {} with controller uuid {} on DUT".
                             format(self.attach_transport, ctrlr_uuid))
        fun_test.shared_variables["ctrlr_uuid"] = ctrlr_uuid

        # Create EC volume
        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)  # ToDo Assert it
        fun_test.test_assert(ec_config_status, message="Configure EC volume on F1")
        # attach volume to controller
        ec_uuid = self.ec_info["attach_uuid"][0]
        fun_test.test_assert(self.storage_controller.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                 ns_id=self.ns_id,
                                                                                 vol_uuid=ec_uuid),
                             message="Attaching EC Vol nsid: {} with uuid {} to controller".format(self.ns_id, ec_uuid))

        # Set syslog level
        set_syslog_level(storage_controller, fun_test.shared_variables['syslog_level'])

        # execute nvme connect
        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(self.attach_transport.lower(),
                                                                         test_network["f1_loopback_ip"],
                                                                         self.transport_port,
                                                                         self.nvme_subsystem)

        nvme_connect_status = end_host.sudo_command(command=nvme_connect_cmd, timeout=60)
        fun_test.log("nvme_connect_status output is: {}".format(nvme_connect_status))
        fun_test.test_assert_expected(expected=0, actual=self.end_host.exit_status(), message="NVME Connect Status")

        # check nvme device is visible on end host
        fetch_nvme = fetch_nvme_device(end_host, self.ns_id)
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
        fun_test.shared_variables['nvme_block_device'] = fetch_nvme['nvme_device']
        fun_test.shared_variables['volume_name'] = fetch_nvme['volume_name']

        # execute fio write to populate device
        fun_test.test_assert(self.end_host.pcie_fio(filename=fun_test.shared_variables['nvme_block_device'],
                                                    **self.warm_up_fio_cmd_args), "Pre-populating the volume")
        fun_test.shared_variables["setup_created"] = True

    def cleanup(self):
        try:
            if fun_test.shared_variables['setup_created']:
                ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.end_host.sudo_command("nvme disconnect -d {}".format(fun_test.shared_variables['volume_name']))

                # disconnect device from controller
                fun_test.test_assert(self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=ctrlr_uuid,
                    ns_id=self.ns_id,
                    command_duration=self.command_timeout)['status'],
                                     message="Detach nsid: {} from controller: {}".format(self.ns_id, ctrlr_uuid))

                # delete controller
                fun_test.test_assert(self.storage_controller.delete_controller(ctrlr_uuid=ctrlr_uuid,
                                                                               command_duration=self.command_timeout),
                                     message="Delete Controller uuid: {}".format(ctrlr_uuid))
                fun_test.sleep(seconds=2, message="EC volume detached from controller")

                # delete EC
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)
                self.storage_controller.disconnect()
        except Exception as ex:
            fun_test.critical(ex.message)
        finally:
            fun_test.shared_variables["topology"].cleanup()


class ECTcpSanityTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        mode = self.fio_mode
        end_host = fun_test.shared_variables["end_host"]
        nvme_block_device = fun_test.shared_variables['nvme_block_device']
        fio_numjob_iodepths = self.fio_numjobs_iodepth
        fun_test.simple_assert(nvme_block_device, "nvme block device available for test")
        for combo in fio_numjob_iodepths:
            num_jobs, iodepth = eval(combo)
            fio_job_name = "{}_{}_{}".format(self.fio_job_name, mode, iodepth * num_jobs)
            fio_output = end_host.pcie_fio(filename=nvme_block_device,
                                           rw=mode,
                                           numjobs=num_jobs,
                                           iodepth=iodepth,
                                           name=fio_job_name,
                                           **self.fio_cmd_args)
            fun_test.log("FIO Command Output:{}".format(fio_output))
            fun_test.test_assert(fio_output,
                                 "Fio {} test for numjobs {} & iodepth {}".format(mode, num_jobs, iodepth))

    def cleanup(self):
        pass


class ECTcpRandRead(ECTcpSanityTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test random read queries on 4:2 EC volume over nvme-tcp fabric",
                              steps='''
        1. Execute random read traffic on a 4:2 EC volume via nvme-tcp fabric.''')


if __name__ == "__main__":
    ecscript = ECVolumeSanityScript()
    ecscript.add_test_case(ECTcpRandRead())
    ecscript.run()
