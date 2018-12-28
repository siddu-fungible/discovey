from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.templates.storage.nvme_template import NvmeTemplate
from lib.host.storage_controller import StorageController
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


def fio_parser(arg1, **kwargs):
    arg1.pcie_fio(**kwargs)


# To Do
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
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        self.topology_obj_helper.save(file_name="/tmp/divya_nvme.pkl")
        # self.topology = self.topology_obj_helper.load(file_name="/tmp/divya_nvme.pkl")
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["ctrl_created"] = False

    def cleanup(self):
        if self.topology:
            pass
            # self.storage_controller.disconnect()
            # TopologyHelper(spec=self.topology).cleanup()


class NvmeSanityTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
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
        #
        for k, v in config_dict[testcase].iteritems():
            setattr(self, k, v)

        self.topology = fun_test.shared_variables["topology"]
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.host_inst = {}
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.qemu = QemuStorageTemplate(host=self.host, dut=self.dut)
        self.funos_running = True
        self.nvme_template = NvmeTemplate(self.host)
        fun_test.shared_variables["host"] = self.host
        fun_test.shared_variables["nvme_template"] = self.nvme_template
        self.host.command("sudo apt install fio")
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False

            if self.namespace_params["capacity"] % self.namespace_params["block_size"]:
                fun_test.test_assert(
                    False,
                    "{} capacity not a multiple of {} blocksize".format(self.namespace_params["capacity"],
                                                                        self.namespace_params["block_size"]))

            # Wrapper for creating and attaching namespace(s)
            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")
            fun_test.shared_variables["num_ns"] = self.num_namespace + 1
            self.thin_uuid = {}
            for i in range(1, fun_test.shared_variables["num_ns"], 1):
                self.thin_uuid[i] = utils.generate_uuid()
                command_result = {}
                command_result = self.storage_controller.create_volume(
                    type="VOL_TYPE_BLK_LOCAL_THIN",
                    capacity=self.namespace_params["capacity"],
                    block_size=self.namespace_params["block_size"],
                    uuid=self.thin_uuid[i],
                    name="thin_blk" + str(i),
                    command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_create_count += 1
                else:
                    fun_test.test_assert(
                        command_result["status"],
                        "Thin Block volume {} creation with capacity {}".format(i, self.namespace_params["capacity"]))

                command_result = {}
                command_result = self.storage_controller.volume_attach_pcie(
                    ns_id=i,
                    uuid=self.thin_uuid[i],
                    huid=0,
                    ctlid=self.namespace_params["ctl_id"],
                    fnid=2,
                    command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_attach_count += 1
                else:
                    fun_test.test_assert(
                        command_result["status"],
                        "Thin Block volume {} attach with capacity {}".format(i, self.namespace_params["capacity"]))

            if self.blt_create_count == self.num_namespace:
                fun_test.add_checkpoint("Total BLT create count {}".format(self.blt_create_count),
                                        "PASSED",
                                        self.num_namespace,
                                        self.blt_create_count)
            else:
                fun_test.test_assert(False, "Create and namespace count")
            if self.blt_attach_count == self.num_namespace:
                fun_test.add_checkpoint("Total BLT attach count {}".format(self.blt_attach_count),
                                        "PASSED",
                                        self.num_namespace,
                                        self.blt_attach_count)
            else:
                fun_test.test_assert(False, "Attach and namespace count")

    def run(self):
        testcase = self.__class__.__name__
        initial_volume_stats = {}
        # Fetching initial stats
        fio_result = {}
        wait_time = 0
        for i in range(1, fun_test.shared_variables["num_ns"], 1):
            initial_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)
            fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT")
            initial_volume_stats[i] = command_result["data"]
            fun_test.log("Volume Stats at the beginning of the test:")
            fun_test.log(initial_volume_stats[i])
            # for i in range(1, fun_test.shared_variables["num_ns"], 1):
            self.fname = "/dev/nvme0n" + str(i)
            self.host.pcie_fio(filename=self.fname, **self.fio_params)

        # Calculating the expected stats
        size_in_bytes = byte_converter(str(self.fio_params["size"]))
        bs_in_bytes = byte_converter(str(self.namespace_params["block_size"]))
        fun_test.test_assert(size_in_bytes != -1, "Invalid fio size ")
        fun_test.test_assert(bs_in_bytes != -1, "Invalid volume block size")
        expected_counter_stat = (size_in_bytes / bs_in_bytes)

        # Fetching final stats after running traffic
        final_volume_stats = {}
        diff_volume_stats = {}
        for i in range(1, fun_test.shared_variables["num_ns"], 1):
            final_volume_stats[i] = {}
            diff_volume_stats[i] = {}
            self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                              "volumes",
                                                              "VOL_TYPE_BLK_LOCAL_THIN",
                                                              self.thin_uuid[i],
                                                              "stats")
            command_result = self.storage_controller.peek(self.storage_props_tree)
            fun_test.simple_assert(command_result["status"], "Volume stats of DUT after IO")
            final_volume_stats[i] = command_result["data"]
            fun_test.log(final_volume_stats[i])

            # Finding the difference between the internal volume stats before and after the test

            for fkey, fvalue in final_volume_stats[i].items():
                # Not going to calculate the difference for the value stats which are not in the expected volume
                # dictionary and also for the fault_injection attribute
                if fkey == "fault_injection":
                    diff_volume_stats[i][fkey] = fvalue
                    continue
                if fkey in initial_volume_stats[i]:
                    ivalue = initial_volume_stats[i][fkey]
                    diff_volume_stats[i][fkey] = fvalue - ivalue
            fun_test.log("Difference of volume status before and after the test:")
            fun_test.log(diff_volume_stats[i])

            fun_test.log("Expected counters are: {}".format(expected_counter_stat))
            fun_test.test_assert_expected(expected=expected_counter_stat,
                                          actual=diff_volume_stats[i]["num_writes"],
                                          message="Write counter is correct")
            # To do check read counter
            # fun_test.test_assert_expected(expected=expected_counter_stat, actual=diff_volume_stats["num_reads"],
            #                              message="Read counter is correct")

    def cleanup(self):
        if "blt" in fun_test.shared_variables:
            for i in range(1, fun_test.shared_variables["num_ns"], 1):
                command_result = {}
                command_result = self.storage_controller.volume_detach_pcie(
                    ns_id=i,
                    uuid=self.thin_uuid[i],
                    huid=0,
                    ctlid=self.namespace_params["ctl_id"],
                    fnid=2,
                    command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_detach_count += 1
                else:
                    fun_test.test_assert(
                        command_result["status"],
                        "Thin Block volume {} detach with capacity {}".format(i, self.namespace_params["capacity"]))

                command_result = {}
                command_result = self.storage_controller.delete_volume(
                    type="VOL_TYPE_BLK_LOCAL_THIN",
                    capacity=self.namespace_params["capacity"],
                    uuid=self.thin_uuid[i],
                    block_size=self.namespace_params["block_size"],
                    name="thin_blk" + str(i),
                    command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_delete_count += 1
                else:
                    fun_test.test_assert(
                        command_result["status"],
                        "Thin Block volume {} delete with capacity {}".format(i, self.namespace_params["capacity"]))
            if self.blt_detach_count == self.num_namespace:
                fun_test.add_checkpoint("Total BLT detach count {}".format(self.blt_detach_count),
                                        "PASSED",
                                        self.num_namespace,
                                        self.blt_detach_count)
            else:
                fun_test.test_assert(False, "Detach and namespace count")
            if self.blt_delete_count == self.num_namespace:
                fun_test.add_checkpoint("Total BLT delete count {}".format(self.blt_delete_count),
                                        "PASSED",
                                        self.num_namespace,
                                        self.blt_delete_count)
            else:
                fun_test.test_assert(False, "Delete and namespace count")

        fun_test.shared_variables["blt"]["setup_created"] = False


class TestInitialization(NvmeSanityTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="PCIe device initialization",
                              steps="""
        1. Create and attach namespace. 
        2. Load nvme driver on host. 
        2. Check lspci for fungible pcie devices 
        4. Check nvme controller under /dev/
        5. Run fio on the namespace
        6. Detach and delete namespace
        7. Check whether the namespace is deleted 
                             """)

    def setup(self):
        super(TestInitialization, self).setup()

    def run(self):
        lspci_cmd = self.host.command("lspci | grep -i 1dad")
        fun_test.test_assert("Non-Volatile" in lspci_cmd, "PCIe device is present")
        self.nvme_template.reload_nvme()
        nv_ctrlr = self.host.command("ls /dev/nvme*")
        fun_test.test_assert("No such file or directory" not in nv_ctrlr, "Controller is present")
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
        3. Check and verify namespace count
        4. Detach and delete namespace
        5. Check all namespaces are deleted 
                             """)

    def setup(self):
        super(TestMultipleNS, self).setup()

    def run(self):
        self.ns_list = 0
        self.nvme_template.reload_nvme()
        fun_test.sleep("Sleeping for {}", 2)
        ns_list = int(self.host.command("nvme list-ns /dev/nvme0 | wc -l"))
        fun_test.test_assert_expected(expected=self.num_namespace, actual=ns_list,
                                      message="Expected number of namespaces created")
        super(TestMultipleNS, self).run()

    def cleanup(self):
        self.ns_list = -1
        super(TestMultipleNS, self).cleanup()
        self.nvme_template.reload_nvme()
        ns_list = int(self.host.command("nvme list-ns /dev/nvme0 | wc -l"))
        fun_test.test_assert_expected(expected=0, actual=ns_list,
                                      message="All namespaces deleted")


if __name__ == "__main__":
    nvme_script = NvmeSanityScript()
    nvme_script.add_test_case(TestInitialization())
    nvme_script.add_test_case(TestMultipleNS())
    nvme_script.run()
