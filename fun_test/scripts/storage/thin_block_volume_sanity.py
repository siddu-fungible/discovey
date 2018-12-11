from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.system import utils
from lib.topology.dut import DutInterface, Dut
from lib.host.traffic_generator import TrafficGenerator
from lib.fun.f1 import F1

topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
        }
    }
}


class BLTSanityScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Setup traffic generator container - fio
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["ctrl_created"] = False

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # pass


class BLTSanityTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance0 = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut_instance0, "Retrieved dut instance 0")
        self.linux_host = self.topology.get_tg_instance(tg_index=0)

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

        self.storage_controller = StorageController(target_ip=self.dut_instance0.host_ip,
                                                    target_port=self.dut_instance0.external_dpcsh_port)

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False

            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT Instance 0")

            self.thin_uuid = utils.generate_uuid()

            # Configuring controller
            if not fun_test.shared_variables["ctrl_created"]:
                result_ip_cfg = self.storage_controller.ip_cfg(ip=self.dut_instance0.data_plane_ip)
                fun_test.test_assert(result_ip_cfg["status"],
                                     "ip_cfg {} on Dut Instance".format(self.dut_instance0.data_plane_ip))
                fun_test.shared_variables["ctrl_created"] = True

            # Creating Thin block volume
            result_create_volume = self.storage_controller.create_thin_block_volume(
                capacity=self.volume_params["capacity"], block_size=self.volume_params["block_size"],
                uuid=self.thin_uuid, name=self.volume_params["name"],
                command_duration=self.volume_params["command_timeout"])
            fun_test.test_assert(result_create_volume["status"], "Thin Block volume is created")

            # Attaching volume to remote server - to linux container
            result_attach_volume = self.storage_controller.volume_attach_remote(uuid=self.thin_uuid,
                                                                                ns_id=self.volume_params["ns_id"],
                                                                                remote_ip=self.linux_host.internal_ip)
            fun_test.test_assert(result_attach_volume["status"], "Thin Block volume is attached")

            fun_test.shared_variables["blt"]["setup_created"] = True
            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid

    def run(self):
        testcase = self.__class__.__name__
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_params["type"],
                                                          self.thin_uuid, "stats")

        # Fetching initial stats
        initial_volume_status = {}
        command_result = self.storage_controller.peek(self.storage_props_tree)
        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
        initial_volume_status = command_result["data"]
        fun_test.log("Volume Status at the beginning of the test:")
        fun_test.log(initial_volume_status)

        # Generating traffic from remote server using fio
        destination_ip = self.dut_instance0.data_plane_ip
        fio_result = self.linux_host.remote_fio(destination_ip=destination_ip, **self.fio_params)

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

        expected_counter_stat = int(filter(str.isdigit,
                                           str(self.fio_params["size"]))) / int(filter(str.isdigit,
                                                                                       str(self.fio_params["bs"])))
        fun_test.log("Expected counters are: {}".format(expected_counter_stat))
        fun_test.test_assert_expected(expected=expected_counter_stat, actual=diff_volume_stats["num_writes"],
                                      message="Write counter is correct")
        fun_test.test_assert_expected(expected=expected_counter_stat, actual=diff_volume_stats["num_reads"],
                                      message="Read counter is correct")

    def cleanup(self):
        # pass
        fun_test.log("***** Entering into Clean up section *****")
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        self.storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_params["type"],
                                                          self.thin_uuid, "stats")
        result_detach_volume = self.storage_controller.volume_detach_remote(ns_id=self.volume_params["ns_id"],
                                                                            uuid=self.thin_uuid,
                                                                            remote_ip=self.linux_host.internal_ip)
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.test_assert(result_detach_volume["status"], "Thin Block volume is detached")

        result_delete_volume = self.storage_controller.delete_thin_block_volume(capacity=self.volume_params["capacity"],
                                                                                uuid=self.thin_uuid,
                                                                                block_size=self.volume_params["block_size"],
                                                                                name=self.volume_params["name"])
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.test_assert(result_delete_volume["status"], "Thin Block volume is deleted")

        command_result = self.storage_controller.peek(self.storage_props_tree)
        fun_test.log(command_result)
        self.storage_controller.disconnect()

        # Below assert will cause an error due to bug: SWOS-3597
        fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                      message="Stat and Counters are reset after deleting volume")


class BLTFioSequentialWrite(BLTSanityTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity case - Configure BLT volume and Run Sequential Traiffic using fio",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create volume
        4. Attach volume to remote server
        5. Write data using fio from remote server
        6. Read data with Read IO and validate with data write
        7. Detach volume
        8. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(BLTFioSequentialWrite, self).setup()


    def run(self):
        super(BLTFioSequentialWrite, self).run()

    def cleanup(self):
        super(BLTFioSequentialWrite, self).cleanup()


class BLTFioRandomWrite(BLTSanityTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Sanity case - Configure BLT volume and Run Random Traiffic using fio",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create volume
        4. Attach volume to remote server
        5. Write data using fio from remote server
        6. Read data with Read IO and validate with data write
        7. Detach volume
        8. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(BLTFioRandomWrite, self).setup()

    def run(self):
        super(BLTFioRandomWrite, self).run()

    def cleanup(self):
        super(BLTFioRandomWrite, self).cleanup()


if __name__ == "__main__":
    thin_block_vol_sanity = BLTSanityScript()
    thin_block_vol_sanity.add_test_case(BLTFioSequentialWrite())
    thin_block_vol_sanity.add_test_case(BLTFioRandomWrite())
    thin_block_vol_sanity.run()
