from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *
from lib.host.storage_controller import StorageController
import random



class Singledpu(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        fun_test.shared_variables["fio"] = {}
        fun_test.shared_variables["ctrl_created"] = False

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = 2
            self.command_timeout = 30
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        # Declaring default values if not defined in config files
        if not hasattr(self, "dut_start_index"):
            self.dut_start_index = 0
        if not hasattr(self, "host_start_index"):
            self.host_start_index = 0
        if not hasattr(self, "update_workspace"):
            self.update_workspace = False
        if not hasattr(self, "update_deploy_script"):
            self.update_deploy_script = False

        # Using Parameters passed during execution, this will override global and config parameters
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = False
        if "syslog" in job_inputs:
            self.syslog = job_inputs["syslog"]
        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]

        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")

        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["transport_port"] = self.transport_port
        fun_test.shared_variables["transport_type"] = self.transport_type
        fun_test.shared_variables["nqn"] = self.nqn
        fun_test.shared_variables["ns_id"] = self.ns_id
        fun_test.shared_variables["command_timeout"] = self.command_timeout
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.end_host = self.host_handles[self.host_ips[0]]


    def cleanup(self):
        # Cleanup
        # Executing NVMe disconnect from  the hosts
        nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)
        nvme_disconnect_output = self.end_host.sudo_command(command=nvme_disconnect_cmd, timeout=60)
        nvme_disconnect_exit_status = self.end_host.exit_status()
            fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                          message="Host {} - NVME Disconnect Status".format(self.host_ips[0]))
        self.ctrlr_uuid1 = fun_test.shared_variables["ctrlr_uuid1"]
        self.target_uuid = fun_test.shared_variables["target_uuid"]
        self.thin_uuid = fun_test.shared_variables["thin_uuid"]

        # Delete Clone volume w/o detaching it - Negative TC#C34501
        command_result = self.storage_controller.delete_volume(
            command_duration=self.command_timeout,
            uuid=self.target_uuid,
            type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.test_assert(not command_result["status"], "Deleting Clone volume while  attached  uuid {}".
                                 format(self.target_uuid))


        # Detach Clone volume from its controller
        command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid1,
                                                                               ns_id=self.ns_id + 1,
                                                                               command_duration=self.command_timeout)

            fun_test.test_assert(command_result["status"], "Detached Clone volume from ctrlr {}".
                                 format(self.ctrlr_uuid1))

        # Delete Clone volume
        command_result = self.storage_controller.delete_volume(
            command_duration=self.command_timeout,
            uuid=self.target_uuid,
            type="VOL_TYPE_BLK_LOCAL_THIN")
            fun_test.test_assert(command_result["status"], "Deleted Clone volume  uuid {}".
                                 format(self.target_uuid))


        # Detach Base volume from its controller
        command_result = self.storage_controller.detach_volume_from_controller(ctrlr_uuid=self.ctrlr_uuid1,
                                                                               ns_id=self.ns_id,
                                                                               command_duration=self.command_timeout)

            fun_test.test_assert(command_result["status"], "Detached Base volume   from ctrlr".
                                 format(self.ctrlr_uuid1))


        # Delete the controller detached from Base and Clone volume
        command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid1,
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Deleted the controller {}".
                                 format(self.ctrlr_uuid1))


        # Delete Base volume
        command_result = self.storage_controller.delete_volume(
            name="base_vol_" + str(1),
            uuid=self.thin_uuid,
            type="VOL_TYPE_BLK_LOCAL_THIN")

            fun_test.test_assert(command_result["status"], "Deleted BV with uuid {}".
                                 format(self.thin_uuid))



class CloneTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):


        testcase = self.__class__.__name__

        benchmark_parsing = True
        testcase_file = ""
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))

        testcase_dict = {}
        testcase_dict = utils.parse_file_to_json(testcase_file)

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase".format(testcase))
        else:
            for k, v in testcase_dict[testcase].iteritems():
                setattr(self, k, v)

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_ip"] = fun_test.shared_variables["f1_ips"][0]
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.host_numa_cpus = fun_test.shared_variables["numa_cpus"]

        # contrller, base and clone uids
        self.ctrlr_uuid1 = utils.generate_uuid()
        fun_test.shared_variables["ctrlr_uuid1"] = self.ctrlr_uuid1
        self.thin_uuid = utils.generate_uuid()  # base
        fun_test.shared_variables["thin_uuid"] = self.thin_uuid
        self.target_uuid = utils.generate_uuid() # clone
        fun_test.shared_variables["target_uuid"] = self.target_uuid

        # Configuring controller IP
        command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_ip"])
        fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

        # Create Controller for Base and Clone volume
        command_result = self.storage_controller.create_controller(
            ctrlr_uuid=self.ctrlr_uuid1,
            transport=self.transport_type.upper(),
            command_duration=self.command_timeout,
            ctrlr_id=1,
            ctrlr_type="BLOCK",
            remote_ip=self.host_ips[0],
            subsys_nqn=self.nqn,
            host_nqn=self.host_ips[0],
            port=self.transport_port,
        )
        fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                             format(self.host_ips[0], self.ctrlr_uuid1))
        # Create Base volume
        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="base_vol_" + str(1),
                                                               uuid=self.thin_uuid,
                                                               command_duration=self.command_timeout
                                                               )
        fun_test.test_assert(command_result["status"], "Base volume with uuid {} created".format(self.thin_uuid))

        # Attach Base volume to the controller
        command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid1,
                                                                             vol_uuid=self.thin_uuid,
                                                                             ns_id=self.ns_id,
                                                                             command_duration=self.command_timeout)

        fun_test.test_assert(command_result["status"], "Attached thed Base volume to the controller")

        # Loading nvme modules and do nvme connect on host1

        command_result = self.end_host.command("lsmod | grep -w nvme")
        if "nvme" in command_result:
            fun_test.log("nvme driver is loaded")
        else:
            fun_test.log("Loading nvme")
            self.end_host.modprobe("nvme")
        command_result = self.end_host.lsmod("nvme_tcp")
        if "nvme_tcp" in command_result:
            fun_test.log("nvme_tcp driver is loaded")
        else:
            fun_test.log("Loading nvme_tcp")
            self.end_host.modprobe("nvme_tcp")
        self.end_host.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
        if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
            command_result = self.end_host.sudo_command(
                "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                          self.test_network["f1_ip"],
                                                                          self.transport_port, self.nqn,
                                                                          self.nvme_io_queues, self.host_ips[0]))
            fun_test.log("nvme_connect_status output is: {}".format(command_result))
        else:
            command_result = self.end_host.sudo_command(
                "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                    self.test_network["f1_ip"],
                                                                    self.transport_port, self.nqn, self.host_ips[0]))

            fun_test.log("nvme_connect_status output is: {}".format(command_result))

        fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)

        # check nvme device is visible on end host
        fetch_nvme = fetch_nvme_device(self.end_host, 1)  # 1 is ns_id
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")

        # Write into the Base volume
        fio_output = self.end_host.pcie_fio(filename=fetch_nvme['nvme_device'],
                                            cpus_allowed=self.host_numa_cpus,
                                            **self.fio_write_cmd_args)
        fun_test.log("FIO Command Output:\n{}".format(fio_output))
        fun_test.test_assert(fio_output, "Write completed on Base volume from host")

        # Create Clone volume
        command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                               capacity=self.blt_details["capacity"],
                                                               block_size=self.blt_details["block_size"],
                                                               name="clone_vol_" + str(1),
                                                               uuid=self.target_uuid,
                                                               base_uuid=self.thin_uuid,
                                                               clone='true',
                                                               command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Clone volume created with uuid {}".format(self.target_uuid))

        # Attach Clone volume to the controller
        command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid1,
                                                                             vol_uuid=self.target_uuid,
                                                                             ns_id=self.ns_id + 1,
                                                                             command_duration=self.command_timeout)
        # nvme disconnect (work around to swos-8544)
        nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nqn)
        nvme_disconnect_output = self.end_host.sudo_command(command=nvme_disconnect_cmd, timeout=60)
        nvme_disconnect_exit_status = self.end_host.exit_status()
        fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                      message="Host {} - NVME Disconnect Status".format(self.host_ips[0]))
        # nvme re-connect
        command_result = self.end_host.sudo_command(
            "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                      self.test_network["f1_ip"],
                                                                      self.transport_port, self.nqn,
                                                                      self.nvme_io_queues, self.host_ips[0]))
        fun_test.log("nvme_connect_status output is: {}".format(command_result))

        # check nvme device2 is visible after Clone attached
        fetch_nvme = fetch_nvme_device(self.end_host, 2)  # x is ns_id
        fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device 2 visible on end host")

    def run(self):
        testcase = self.__class__.__name__
        self.test_method = testcase[:]



        if self.test_method == 'CloneRead':

            # check nvme device is visible on end host
            fetch_nvme = fetch_nvme_device(self.end_host, 2)  # x is ns_id
            fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")

            # Perform read from Clone
            fio_output = self.end_host.pcie_fio(filename=fetch_nvme['nvme_device'],
                                              cpus_allowed=self.host_numa_cpus,
                                              **self.fio_read_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Reading from Clone volume "
                                 )

        if self.test_method == 'CloneWrite':

            # check nvme device is visible on end host
            fetch_nvme = fetch_nvme_device(self.end_host, 2)  # x is ns_id
            fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")

            # Perform write into the Clone

            fio_output = self.end_host.pcie_fio(filename=fetch_nvme['nvme_device'],
                                              cpus_allowed=self.host_numa_cpus,
                                              **self.fio_write_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Write completed on Base volume from host")

            # Perform read from Clone
            fio_output = self.end_host.pcie_fio(filename=fetch_nvme['nvme_device'],
                                              cpus_allowed=self.host_numa_cpus,
                                              **self.fio_read_cmd_args)
            fun_test.log("FIO Command Output:\n{}".format(fio_output))
            fun_test.test_assert(fio_output, "Reading from Clone volume ")



class CloneCreation(CloneTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create a BLT Clone volume ",
                              test_rail_case_ids=["C18702","C34501"],
                              steps='''
                                      1. Create a BLT base volume 
                                      2. Attach the BV to controller
                                      3. Connect from host1 to BV
                                      4. Create a Clone volume for the BV
                                      5. Attach the Clone to another controller
                                      6. Connect from host2 to the Controller
                            ''')

    def run(self):
        pass
    def cleanup(self):
        pass

class CloneRead(CloneTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Verify Base volume data through its Clone ",
                              test_rail_case_ids=["C18751"],
                              steps='''
                                      1. Read data from Clone
                                      2. Verify the data is matching what was written in Base
                            ''')
    def setup(self):
        testcase = self.__class__.__name__

        benchmark_parsing = True
        testcase_file = ""
        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Test case file being used: {}".format(testcase_file))

        testcase_dict = {}
        testcase_dict = utils.parse_file_to_json(testcase_file)

        if testcase not in testcase_dict or not testcase_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Input is not available for the current testcase {} in {} file".
                              format(testcase, testcase_file))
            fun_test.test_assert(benchmark_parsing, "Parsing json file for this {} testcase".format(testcase))
        else:
            for k, v in testcase_dict[testcase].iteritems():
                setattr(self, k, v)

    def cleanup(self):
        pass









if __name__ == "__main__":
    clonesript1 = Singledpu()
    clonesript1.add_test_case(CloneCreation())
    clonesript1.add_test_case(CloneRead())

    clonesript1.run()
