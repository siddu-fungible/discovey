from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
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


# Different huid ctlid combination used for S2FULL simulation, we will change this when we know what is supported for
# FS1600

host_dict = {1:{'huid':0,'ctlid':0}, 2:{'huid':1,'ctlid':0}, 3:{'huid':1,'ctlid':1}, 4:{'huid':2,'ctlid':0},
             5: {'huid': 2, 'ctlid': 1}, 6:{'huid':2,'ctlid':2}}


class NvmeSanityScript(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Setup qemu host for EP
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance")
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller

    def cleanup(self):
        if self.topology:
            self.storage_controller.disconnect()
            TopologyHelper(spec=self.topology).cleanup()


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

        for k, v in config_dict[testcase].iteritems():
            setattr(self, k, v)

        self.topology = fun_test.shared_variables["topology"]
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.dut = self.topology.get_dut_instance(index=0)
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.funos_running = True
        install_status = self.host.install_package("fio")
        fun_test.test_assert(install_status, "fio installed successfully")
        self.blt_create_count = 0
        self.blt_attach_count = 0
        self.blt_detach_count = 0
        self.blt_delete_count = 0

        # Wrapper for creating and attaching namespace(s)
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")
        # Create volumes for all hosts
        self.total_num_ns = self.num_namespace * self.num_host
        self.thin_uuid = {}
        for i in range(1, self.total_num_ns + 1, 1):
            self.thin_uuid[i] = utils.generate_uuid()
            command_result = {}
            command_result = self.storage_controller.create_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                   capacity=self.namespace_params["capacity"],
                                                                   block_size=self.namespace_params["block_size"],
                                                                   uuid=self.thin_uuid[i],
                                                                   name="thin_blk" + str(i),
                                                                   command_duration=self.command_timeout)
            if command_result["status"]:
                self.blt_create_count += 1
            else:
                fun_test.test_assert(command_result["status"],
                                     "Thin Block volume {} creation with capacity {}".
                                     format(i, self.namespace_params["capacity"]))
        # Creating host_list having huid & ctlid
        self.num_host += 1
        self.host_list = []
        for i in range(1, self.num_host, 1):
            self.host_list.append(i)

        # We are initializing the uuid index as same uuid shouldn't be attached to 2 hosts.
        cur_uuid = 1
        for key in self.host_list:
            self.val = host_dict[key]
            for i in range(1, self.num_namespace + 1, 1):
                command_result = {}
                command_result = self.storage_controller.volume_attach_pcie(ns_id=i,
                                                                            uuid=self.thin_uuid[cur_uuid],
                                                                            huid=self.val['huid'],
                                                                            ctlid=self.val['ctlid'],
                                                                            command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_attach_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} attach with capacity {}".
                                          format(i, self.namespace_params["capacity"]))
                cur_uuid += 1
        fun_test.simple_assert(expression=self.total_num_ns == self.blt_create_count,
                               message="Total NS is {}, NS created is {}".
                               format(self.total_num_ns, self.blt_create_count))
        fun_test.simple_assert(expression=self.total_num_ns == self.blt_attach_count,
                               message="Total NS is {}, NS attached is {}".
                               format(self.total_num_ns, self.blt_attach_count))
        fun_test.add_checkpoint("Total BLT created & attached match total NS",
                                "PASSED",
                                self.total_num_ns,
                                self.blt_create_count)

    def run(self):
        testcase = self.__class__.__name__
        initial_volume_stats = {}
        # Fetching initial stats
        fio_result = {}
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.host.systemctl(service_name=service, action="stop")
            fun_test.test_assert(service_status, "Stopping {} service".format(service))

        for i in range(1, self.total_num_ns + 1, 1):
            command_result = {}
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



        # Fetching final stats after running traffic
        final_volume_stats = {}
        diff_volume_stats = {}
        cur_uuid = 1
        for key in self.host_list:
            self.val = host_dict[key]
            if self.val['huid'] == 0 and self.val['ctlid'] == 0:
                for i in range(1, self.num_namespace + 1, 1):
                    command_result = {}
                    final_volume_stats[i] = {}
                    diff_volume_stats[i] = {}
                    self.fname = "/dev/nvme0n" + str(i)
                    # Calculating the expected stats
                    size_in_bytes = utils.convert_to_bytes(str(self.fio_params["size"]))
                    bs_in_bytes = utils.convert_to_bytes(str(self.namespace_params["block_size"]))
                    fun_test.simple_assert(size_in_bytes != -1, "Invalid test size ")
                    fun_test.simple_assert(bs_in_bytes != -1, "Invalid volume block size")
                    expected_counter_stat = (size_in_bytes / bs_in_bytes)

                    fio_result = self.host.pcie_fio(filename=self.fname, **self.fio_params)
                    fun_test.test_assert(fio_result, "fio {} test".format(self.fio_params["rw"]))
                    self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage",
                                                                      "volumes",
                                                                      "VOL_TYPE_BLK_LOCAL_THIN",
                                                                      self.thin_uuid[cur_uuid],
                                                                      "stats")
                    command_result = self.storage_controller.peek(self.storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Volume stats of DUT after IO")
                    final_volume_stats[i] = command_result["data"]
                    fun_test.log(final_volume_stats[i])

                    for fkey, fvalue in final_volume_stats[i].items():
                        if fkey == "fault_injection":
                            diff_volume_stats[i][fkey] = fvalue
                            continue
                        if fkey in initial_volume_stats[cur_uuid]:
                            ivalue = initial_volume_stats[cur_uuid][fkey]
                            diff_volume_stats[i][fkey] = fvalue - ivalue
                        fun_test.log("Difference of {} stats is {}".format(fkey, diff_volume_stats[i][fkey]))
                    fun_test.log("Difference of volume stats before and after the test:")
                    fun_test.log(diff_volume_stats[i])

                    fun_test.log("Expected counters are: {}".format(expected_counter_stat))
                    fun_test.test_assert_expected(expected=expected_counter_stat,
                                                  actual=diff_volume_stats[i]["num_writes"],
                                                  message="Write counter for nsid {}, uuid:{}"
                                                  .format(i, self.thin_uuid[cur_uuid]))
                    # SWOS-3839 Read counters are inconsistent
                    # fun_test.test_assert_expected(expected=expected_counter_stat,
                    #                              actual=diff_volume_stats[i]["num_reads"],
                    #                              message="Read counter for nsid{}, uuid:{}"
                    #                              .format(self.nsid, self.thin_uuid[self.uuid_count]))
                    cur_uuid += 1


    def cleanup(self):
        cur_uuid = 1
        for key in self.host_list:
            self.val = host_dict[key]
            for i in range(1, self.num_namespace + 1, 1):
                command_result = {}
                command_result = self.storage_controller.volume_detach_pcie(ns_id=i,
                                                                            uuid=self.thin_uuid[cur_uuid],
                                                                            huid=self.val['huid'],
                                                                            ctlid=self.val['ctlid'],
                                                                            command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_detach_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} detach with capacity {}".
                                         format(i, self.namespace_params["capacity"]))
                command_result = {}
                command_result = self.storage_controller.delete_volume(type="VOL_TYPE_BLK_LOCAL_THIN",
                                                                       capacity=self.namespace_params["capacity"],
                                                                       uuid=self.thin_uuid[cur_uuid],
                                                                       block_size=self.namespace_params["block_size"],
                                                                       name="thin_blk" + str(i),
                                                                       command_duration=self.command_timeout)
                if command_result["status"]:
                    self.blt_delete_count += 1
                else:
                    fun_test.test_assert(command_result["status"],
                                         "Thin Block volume {} delete with capacity {}".
                                         format(i, self.namespace_params["capacity"]))
                cur_uuid += 1

        fun_test.simple_assert(expression=self.total_num_ns == self.blt_detach_count,
                               message="Total NS is {}, NS detach is {}".
                               format(self.total_num_ns, self.blt_detach_count))
        fun_test.simple_assert(expression=self.total_num_ns == self.blt_delete_count,
                               message="Total NS is {}, NS deleted is {}".
                               format(self.total_num_ns, self.blt_delete_count))
        fun_test.add_checkpoint("Total BLT detach & deleted match total NS",
                                "PASSED",
                                self.total_num_ns,
                                self.blt_delete_count)

        # Check if there is any residual volumes
        fun_test.log("Volume stats after cleanup {}")
        self.storage_props_tree = "{}/{}".format("storage", "volumes")
        command_result = self.storage_controller.peek(self.storage_props_tree)


class TestInitialization(NvmeSanityTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="PCIe controller initialization",
                              steps="""
        1. Create and attach namespace. 
        2. Load nvme driver on host. 
        3. Check lspci for fungible pcie devices 
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
        nvme_reload = self.host.nvme_restart()
        fun_test.test_assert(nvme_reload, "nvme driver module reloaded")
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
        nvme_reload = self.host.nvme_restart()
        fun_test.test_assert(nvme_reload, "nvme driver module reloaded")
        fun_test.sleep("Sleeping for {}", 2)
        ns_list = int(self.host.command("nvme list-ns /dev/nvme0 | wc -l"))
        fun_test.test_assert_expected(expected=self.num_namespace, actual=ns_list,
                                      message="Expected number of namespaces created")
        super(TestMultipleNS, self).run()

    def cleanup(self):
        self.ns_list = -1
        super(TestMultipleNS, self).cleanup()
        nvme_reload = self.host.nvme_restart()
        fun_test.test_assert(nvme_reload, "nvme driver module reloaded")
        fun_test.sleep("Sleeping for {}", 1)
        ns_list = int(self.host.command("nvme list-ns /dev/nvme0 | wc -l"))
        fun_test.test_assert_expected(expected=0, actual=ns_list,
                                      message="All namespaces deleted")


if __name__ == "__main__":
    nvme_script = NvmeSanityScript()
    nvme_script.add_test_case(TestInitialization())
    nvme_script.add_test_case(TestMultipleNS())
    nvme_script.run()