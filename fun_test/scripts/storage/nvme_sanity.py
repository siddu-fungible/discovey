from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
import uuid
import re
from lib.templates.storage.nvme_template import NvmeTemplate
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
from lib.host.linux import *


topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 1,
                    "type": DutInterface.INTERFACE_TYPE_PCIE,
                    "vm_start_mode": "VM_START_MODE_QEMU_PLUS_DPCSH",
                    "vm_host_os": "fungible_ubuntu"
                }
            },
            "start_mode": "START_MODE_QEMU_PLUS_DPCSH"
        }
    }
}


def byte_converter(size):
    if (size.isdigit()):
        bytes = int(size)
    else:
        bytes = size[:-1]
        unit = size[-1]
        if bytes.isdigit():
            bytes = int(bytes)
            if unit == 'G' or unit == 'g':
                bytes *= 1024 * 1024 * 1024
            elif unit == 'M' or unit == 'm':
                bytes *= 1024 * 1024
            elif unit == 'K' or unit == 'k':
                bytes *= 1024
            elif unit == 'B':
                pass
            else:
                bytes = -1
        else:
            bytes = -1
    return bytes


class NvmeSanityScript(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Setup qemu host for EP
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["ctrl_created"] = False

    def cleanup(self):
        if self.topology:
            TopologyHelper(spec=self.topology).cleanup()


class NvmeSanityTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
        self.need_dpc_server_start = True
        self.iter_interval = 2
        config_parsing = True
        config_file = ""
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = {}
        config_dict = utils.parse_file_to_json(config_file)

        if testcase not in config_dict or not config_dict[testcase]:
            config_parsing = False
            fun_test.critical("Configuration is not available for the current testcase {} in {} file".
                              format(testcase, config_file))
            fun_test.test_assert(config_parsing, "Parsing Config json file for this {} testcase".format(testcase))

        for k, v in config_dict[testcase].iteritems():
            setattr(self, k, v)

        self.topology = fun_test.shared_variables["topology"]
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        self.qemu = QemuStorageTemplate(host=self.host, dut=self.dut)
        self.funos_running = True
        self.nvme_template = NvmeTemplate(self.host)
        fun_test.shared_variables["host"] = self.host
        fun_test.shared_variables["nvme_template"] = self.nvme_template
        self.host.command("sudo apt install fio")

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False

        # Preserving the funos-posix and qemu commandline
        self.funos_cmdline = self.qemu.get_process_cmdline(F1.FUN_OS_SIMULATION_PROCESS_NAME)
        fun_test.log("\nfunos-posix commandline: {}".format(self.funos_cmdline))
        self.qemu_cmdline = self.qemu.get_process_cmdline(DockerContainerOrchestrator.QEMU_PROCESS)
        fun_test.log("\nQemu commandline: {}".format(self.qemu_cmdline))
        self.qemu_cmdline = re.sub(r'(.*append)\s+(root.*mem=\d+M)(.*)', r'\1 "\2"\3', self.qemu_cmdline)
        fun_test.log("\nProcessed Qemu commandline: {}".format(self.qemu_cmdline))

        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        self.num_dpcsh_cmds = 0

        # Wrapper for creating and attaching namespace(s)
        num_ns = self.volume_params["num_ns"]
        print(num_ns)
        counter = 0
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")
        self.num_dpcsh_cmds += 1

        for i in range(num_ns):
            counter += 1
            self.thin_uuid = utils.generate_uuid()
            command_result = {}
            command_result = self.storage_controller.create_thin_block_volume(
                capacity=self.volume_params["capacity"],
                block_size=self.volume_params["block_size"],
                uuid=self.thin_uuid,
                name=self.volume_params["name"],
                use_ls=self.volume_params["use_ls"],
                command_duration=self.volume_params["command_timeout"])
            fun_test.test_assert(command_result["status"], "Thin Block volume is created")

            command_result = {}
            command_result = self.storage_controller.volume_attach_pcie(
                ns_id=self.volume_params["ns_id"],
                uuid=self.thin_uuid,
                huid=self.volume_params["hu_id"],
                ctlid=self.volume_params["ctl_id"],
                fnid=self.volume_params["fn_id"],
                command_duration=self.volume_params["command_timeout"])
            fun_test.test_assert(command_result["status"], "Thin Block volume is attached")

            fun_test.shared_variables["blt"][self.thin_uuid] = {}
            fun_test.shared_variables["blt"][self.thin_uuid]["uuid"] = self.thin_uuid
            fun_test.shared_variables["blt"][self.thin_uuid]["ns_id"] = self.volume_params["ns_id"]
            self.volume_params["ns_id"] += 1

    def run(self):
        testcase = self.__class__.__name__
        # self.uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_params["type"],
                                                          self.thin_uuid, "stats")

        # Fetching initial stats
        initial_volume_status = {}
        command_result = self.storage_controller.peek(self.storage_props_tree)
        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
        initial_volume_status = command_result["data"]
        fun_test.log("Volume Status at the beginning of the test:")
        fun_test.log(initial_volume_status)

        # nvmedisk = self.host.command("nvme list | awk {'print $1'} | grep nvme")
        # Generating traffic from pcie connected host using fio
        # fio_result = self.host.pcie_fio(filename=nvmedisk, **self.fio_params)
        fio_result = self.host.pcie_fio(**self.fio_params)

        # Fetching final stats after running traffic
        final_volume_status = {}
        command_result = self.storage_controller.peek(self.storage_props_tree)
        fun_test.simple_assert(command_result["status"], "Volume stats of DUT Instance 0 after IO")
        final_volume_status = command_result["data"]
        fun_test.log(final_volume_status)

        # Finding the difference between the internal volume stats before and after the test
        diff_volume_stats = {}
        for fkey, fvalue in final_volume_status.items():
            # Not going to calculate the difference for the value stats which are not in the expected volume
            # dictionary and also for the fault_injection attribute
            if fkey == "fault_injection":
                diff_volume_stats[fkey] = fvalue
                continue
            if fkey in initial_volume_status:
                ivalue = initial_volume_status[fkey]
                diff_volume_stats[fkey] = fvalue - ivalue
        fun_test.log("Difference of volume status before and after the test:")
        fun_test.log(diff_volume_stats)

        # expected_counter_stat = int(filter(str.isdigit,
        #                                   str(self.fio_params["size"]))) / int(filter(str.isdigit,
        #                                                                                   str(self.fio_params["bs"])))

        size_in_bytes = byte_converter(str(self.fio_params["size"]))
        bs_in_bytes = byte_converter(str(self.volume_params["block_size"]))
        fun_test.test_assert(size_in_bytes != -1, "Invalid fio size ")
        fun_test.test_assert(bs_in_bytes != -1, "Invalid volume block size")
        expected_counter_stat = (size_in_bytes / bs_in_bytes)

        fun_test.log("Expected counters are: {}".format(expected_counter_stat))
        fun_test.test_assert_expected(expected=expected_counter_stat, actual=diff_volume_stats["num_writes"],
                                      message="Write counter is correct")
        # fun_test.test_assert_expected(expected=expected_counter_stat, actual=diff_volume_stats["num_reads"],
        #                              message="Read counter is correct")

    def cleanup(self):

        if "blt" in fun_test.shared_variables:
            blt_params = fun_test.shared_variables['blt']
            for tmp in blt_params:
                if isinstance(blt_params[tmp], dict):
                    if 'uuid' in blt_params[tmp]:
                        command_result = {}
                        command_result = self.storage_controller.volume_detach_pcie(
                            ns_id=blt_params[tmp]["ns_id"],
                            uuid=blt_params[tmp]["uuid"],
                            huid=self.volume_params["hu_id"],
                            ctlid=self.volume_params["ctl_id"],
                            fnid=self.volume_params["fn_id"],
                            command_duration=self.volume_params["command_timeout"])

                        fun_test.shared_variables["blt"]["setup_created"] = False
                        fun_test.test_assert(command_result["status"], "Thin Block volume is detached")

                        command_result = {}
                        command_result = self.storage_controller.delete_thin_block_volume(
                            capacity=self.volume_params["capacity"],
                            uuid=blt_params[tmp]["uuid"],
                            block_size=self.volume_params["block_size"],
                            name=self.volume_params["name"],
                            command_duration=self.volume_params["command_timeout"])
                        fun_test.shared_variables["blt"]["setup_created"] = False
                        fun_test.test_assert(command_result["status"], "Thin Block volume is deleted")

                        fun_test.log(command_result)
                        self.storage_controller.disconnect()


class TestInitialization(NvmeSanityTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="PCIe device initialization",
                              steps="""
        1. Create and attach volume. 
        2. Load nvme driver on host. 
        2. Check lspci for fungible pcie devices 
        4. Check nvme controller under /dev/
                             """)

    def setup(self):
        super(TestInitialization, self).setup()

    def run(self):
        lspci_cmd = self.host.command("lspci | grep -i 1dad")
        fun_test.test_assert("Non-Volatile" in lspci_cmd, "PCIe device is present")
        self.nvme_template.reload_nvme()
        nv_ctrlr = self.host.command("ls /dev/nvme*")
        fun_test.test_assert("nvme" in nv_ctrlr, "Controller is present")
        super(TestInitialization, self).run()

    def cleanup(self):
        super(TestInitialization, self).cleanup()


class TestMultipleNS(NvmeSanityTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Create/Attach/Detach/Delete multiple namespaces",
                              steps="""
        1. Create and attach multiple namespaces. 
        2. Load nvme driver on host. 
        2. Check and verify namespace count
                             """)

    def setup(self):
        super(TestMultipleNS, self).setup()

    def run(self):
        self.nvme_template.reload_nvme()
        fun_test.sleep("Sleeping for {}", 10)
        ns_list = self.host.command("nvme list-ns /dev/nvme0 | wc -l")
        # fun_test.test_assert_expected(expected=self.volume_params["num_ns"], actual=ns_list,
        #                              message="Expected")

    def cleanup(self):
        super(TestMultipleNS, self).cleanup()
        self.nvme_template.reload_nvme()
        ns_list = self.host.command("nvme list-ns /dev/nvme0 | wc -l")
        print("++++++++++++++++++++++++++++++++++")
        print(ns_list)
        print("++++++++++++++++++++++++++++++++++")

        # fun_test.test_assert_expected(expected=0, actual=ns_list,
        #                             message="Deleted volumes are not present")


if __name__ == "__main__":
    nvme_script = NvmeSanityScript()
    nvme_script.add_test_case(TestInitialization())
    nvme_script.add_test_case(TestMultipleNS())
    nvme_script.run()
