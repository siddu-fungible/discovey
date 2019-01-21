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


class BltF1RestartScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Setup traffic generator container - fio
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")

        self.dut_instance = self.topology.get_dut_instance(index=0)
        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["ctrl_created"] = False
        fun_test.shared_variables["setup_after_restart"] = False

    def cleanup(self):
        self.storage_controller.disconnect()
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


class BLTF1RestartTestCase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__

        if not fun_test.shared_variables["setup_after_restart"]:
            self.topology = fun_test.shared_variables["topology"]
            self.dut_instance = self.topology.get_dut_instance(index=0)
            fun_test.test_assert(self.dut_instance, "Retrieved dut instance")
            self.storage_controller = fun_test.shared_variables["storage_controller"]
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

            # Ensuring TC configuration has flag "use_lsv" as a config parameter
            if 'use_lsv' not in config_dict[testcase]:
                config_parsing = False
                fun_test.critical("use lsv flag should be set for this {} testcase is not available in "
                                  "the {} file".format(testcase, config_file))
            if 'lsv_pct' not in config_dict[testcase]:
                config_parsing = False
                fun_test.critical("use lsv flag should be set for this {} testcase is not available in "
                                  "the {} file".format(testcase, config_file))
                fun_test.test_assert(config_parsing,
                                     "Parsing Config json file for this {} testcase".format(testcase))

            for k, v in config_dict[testcase].iteritems():
                setattr(self, k, v)

            if not hasattr(self, "vol_stats_threshold_pass"):
                self.vol_stats_threshold_pass = 0

            # LS volume capacity is the ndata times of the BLT volume capacity
            if self.use_lsv:
                fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                             "rounding that to the nearest 8MB value")
                eight_kb = 1024 * 8
                tmp = self.volume_params["capacity"]["lsv"] * (1 + self.lsv_pct)
                self.volume_params["capacity"]["blt"] = int(tmp + (eight_kb - (tmp % eight_kb)))

                fun_test.log("Recalculated volume capacity: {}".format(self.volume_params["capacity"]["blt"]))

        # Creating Storage Controller
        if not fun_test.shared_variables["ctrl_created"]:
            result_ip_cfg = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip)
            fun_test.test_assert(result_ip_cfg["status"],
                                 "ip_cfg {} on Dut Instance".format(self.dut_instance.data_plane_ip))
            fun_test.shared_variables["ctrl_created"] = True

        # Creating setup
        if not fun_test.shared_variables["setup_after_restart"]:
            self.uuids = {}
            fun_test.shared_variables["setup_created"] = False
            self.uuids["blt"] = []

            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT Instance")

            # Create BLT volume
            self.blt_uuid = utils.generate_uuid()
            self.uuids["blt"].append(self.blt_uuid)
            command_result = self.storage_controller.create_volume(
                type=self.volume_params["type"]["blt"], capacity=self.volume_params["capacity"]["blt"],
                block_size=self.volume_params["block_size"]["blt"], name=self.volume_params["name"]["blt"],
                uuid=self.blt_uuid, command_duration=self.volume_params["command_timeout"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create {} volume on DUT instance".format(self.volume_params["type"]["blt"]))
            self.attach_uuid = self.blt_uuid

            # Creating journal volume and LS volume
            if self.use_lsv:
                self.uuids["jvol"] = []
                self.uuids["lsv"] = []

                self.jvol_uuid = utils.generate_uuid()
                self.uuids["jvol"].append(self.jvol_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.volume_params["type"]["jvol"], capacity=self.volume_params["capacity"]["jvol"],
                    block_size=self.volume_params["block_size"]["jvol"], name=self.volume_params["name"]["jvol"],
                    uuid=self.jvol_uuid, command_duration=self.volume_params["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create Journal volume on DUT instance")

                self.lsv_uuid = utils.generate_uuid()
                self.uuids["lsv"].append(self.lsv_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.volume_params["type"]["lsv"], capacity=self.volume_params["capacity"]["lsv"],
                    block_size=self.volume_params["block_size"]["lsv"], name=self.volume_params["name"]["lsv"],
                    uuid=self.lsv_uuid, group=self.group, jvol_uuid=self.jvol_uuid, pvol_id=self.uuids["blt"],
                    command_duration=self.volume_params["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create LS volume on the DUT instance")
                self.attach_uuid = self.lsv_uuid

        # If F1 is restarted, Mounting the Journal volume and LS volume
        if fun_test.shared_variables["setup_after_restart"]:

            # Inducing fault in blt volume if trigger_blt_failure flag is set
            if hasattr(self, "trigger_blt_failure") and self.trigger_blt_failure:
                command_result = self.storage_controller.fail_volume(
                    uuid=self.uuids["blt"][0], command_duration=self.volume_params["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to BLT volume having the "
                                                               "UUID {}".format(self.uuids["blt"][0]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_params["type"]["blt"],
                                                     self.uuids["blt"][0], "stats")
                command_result = self.storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                              message="Ensuring fault_injection got enabled")

            if self.use_lsv:
                fun_test.log("Mounting journal volume and LS volume after F1 restart")

                command_result = self.storage_controller.mount_volume(
                    type=self.volume_params["type"]["jvol"], capacity=self.volume_params["capacity"]["jvol"],
                    block_size=self.volume_params["block_size"]["jvol"], name=self.volume_params["name"]["jvol"],
                    uuid=self.jvol_uuid, command_duration=self.volume_params["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Mounting Journal volume in the DUT instance")

                command_result = self.storage_controller.mount_volume(
                    type=self.volume_params["type"]["lsv"], capacity=self.volume_params["capacity"]["lsv"],
                    block_size=self.volume_params["block_size"]["lsv"], name=self.volume_params["name"]["lsv"],
                    uuid=self.lsv_uuid, group=self.group, jvol_uuid=self.jvol_uuid, pvol_id=self.uuids["blt"],
                    command_duration=self.volume_params["command_timeout"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Mounting LS volume in the DUT instance")

                '''
                # TODO: Inject fault for LSV, if trigger_lsv_failure is enabled
                # Currently fault injection is not supported for VOL_TYPE_BLK_LSV, code is in place, 
                # once VOL_TYPE_BLK_LSV fault injection can be enabled, set trigger_lsv_failure to enable
                #
                # Posix Logs:
                # 1545803225.731756 @ FA0:13:0[VP] INFO volume_manager "Volume of type VOL_TYPE_BLK_LSV does not 
                # support fault injections"
                '''

                if hasattr(self, "trigger_lsv_failure") and self.trigger_lsv_failure:
                    command_result = self.storage_controller.fail_volume(
                        uuid=self.uuids["lsv"][0], command_duration=self.volume_params["command_timeout"])
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Inject failure to LSV having the "
                                                                   "UUID {}".format(self.uuids["lsv"][0]))
                    fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                    props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_params["type"]["lsv"],
                                                         self.uuids["lsv"][0], "stats")
                    command_result = self.storage_controller.peek(props_tree)
                    fun_test.log(command_result)
                    fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                                  message="Ensuring fault_injection got enabled")

        # Attaching BLT [or LS volume] to the external server
        command_result = self.storage_controller.volume_attach_remote(
            ns_id=self.ns_id, uuid=self.attach_uuid, remote_ip=self.linux_host.internal_ip,
            command_duration=self.volume_params["command_timeout"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Attaching volume in the DUT instance")

        fun_test.shared_variables["setup_created"] = True
        fun_test.shared_variables["uuids"] = self.uuids

    def run(self):
        testcase = self.__class__.__name__
        destination_ip = self.dut_instance.data_plane_ip
        self.uuids = fun_test.shared_variables["uuids"]

        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_status = {}
        final_volume_status = {}
        diff_volume_stats = {}
        # vol_type = None

        for mode in self.fio_modes:
            fio_result[mode] = True
            internal_result[mode] = True

            # Pulling initial volume stats of all the volumes from the DUT in dictionary format
            fun_test.log("Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                         "the test")
            initial_volume_status[mode] = {}
            volumes = sorted(self.volume_params["type"])
            for type in volumes:
                initial_volume_status[mode][type] = {}
                for index, uuid in enumerate(self.uuids[type]):
                    initial_volume_status[mode][type][index] = {}
                    storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                 self.volume_params["type"][type], uuid, "stats")
                    command_result = {}
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                           format(type, index))
                    initial_volume_status[mode][type][index] = command_result["data"]
                    fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                    fun_test.log(initial_volume_status[mode][type][index])

            # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
            fun_test.log("Running FIO for mode {}".format(mode))
            fio_output[mode] = {}
            fio_output[mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode, **self.fio_params)

            fun_test.test_assert(fio_output[mode], "Fio {} run is completed".format(mode))
            fun_test.log("FIO Command Output:")
            fun_test.log(fio_output[mode])
            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                           self.iter_interval)

            # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
            fun_test.log("Pulling volume stats of all volumes after the FIO test")
            final_volume_status[mode] = {}
            for type in volumes:
                final_volume_status[mode][type] = {}
                for index, uuid in enumerate(self.uuids[type]):
                    final_volume_status[mode][type][index] = {}
                    storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                 self.volume_params["type"][type], uuid, "stats")
                    command_result = {}
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                           format(type, index))
                    final_volume_status[mode][type][index] = command_result["data"]
                    fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                    fun_test.log(final_volume_status[mode][type][index])

            # Finding the difference between the internal volume stats before and after the test
            diff_volume_stats[mode] = {}
            for type in volumes:
                diff_volume_stats[mode][type] = {}
                for index in range(len(self.uuids[type])):
                    diff_volume_stats[mode][type][index] = {}
                    for fkey, fvalue in final_volume_status[mode][type][index].items():
                        # Don't compute the difference of stats which is not defined in expected_volume_stats in
                        # the json config file
                        if fkey == "fault_injection":
                            diff_volume_stats[mode][type][index][fkey] = fvalue
                            continue
                        if fkey in initial_volume_status[mode][type][index]:
                            ivalue = initial_volume_status[mode][type][index][fkey]
                            diff_volume_stats[mode][type][index][fkey] = fvalue - ivalue
                    fun_test.log("Difference of {} {} volume status before and after the test:".
                                 format(type, index))
                    fun_test.log(diff_volume_stats[mode][type][index])
            fun_test.log("Diff volume stats is: {}".format(diff_volume_stats[mode]))

            size_in_bytes = utils.convert_to_bytes(str(self.fio_params["size"]))
            fun_test.test_assert(size_in_bytes != -1, "Converted fio size in bytes")

            for type in volumes:
                if type == "jvol":
                    continue
                fun_test.log("Stats validation for volume {}".format(type))
                bs_in_bytes = utils.convert_to_bytes(str(self.volume_params["block_size"][type]))
                fun_test.test_assert(bs_in_bytes != -1, "Converted volume block size in bytes")

                expected_write = (size_in_bytes / bs_in_bytes)
                expected_read = (size_in_bytes / bs_in_bytes)
                actual_write = diff_volume_stats[mode][type][0]["num_writes"]
                actual_read = diff_volume_stats[mode][type][0]["num_reads"]

                # Validating expected Write and Read stat counters
                if mode == "write":
                    fun_test.log("Expected counters are: write {}, read {}".format(expected_write, expected_read))
                    # expected_read = 0
                if mode == "read":
                    fun_test.log("Expected counters are: write 0, read {}".format(expected_read))
                    expected_write = 0

                # For LSV on to of BLT, stats on BLT might not match - checking if stats are in expected pass range
                if expected_write != actual_write:
                    fun_test.log("Write Stats are not as expected, checking if it is in pass threshold")
                    fun_test.log("Stats pass threshold defined is: {}".format(self.vol_stats_threshold_pass))
                    if (expected_write > actual_write) and (expected_write - actual_write) \
                            <= self.vol_stats_threshold_pass or (actual_write > expected_write) and \
                            (actual_write - expected_write) <= self.vol_stats_threshold_pass:
                        fun_test.add_checkpoint("Actual {} write stat is within expected range {}".
                                                format(actual_write, expected_write), "PASSED",
                                                expected_write, actual_write)
                        fun_test.critical(
                            "Write stat: actual: {}, expected: {} it's within the expected range".format(
                                actual_write, expected_write))
                    else:
                        fun_test.log("Actual Stats are not within pass threshold range")
                        fun_test.test_assert_expected(expected=expected_write, actual=actual_write,
                                                          message="Write counter is correct")
                else:
                    fun_test.test_assert_expected(expected=expected_write, actual=actual_write,
                                                  message="Write counter is correct")

                if expected_read != actual_read:
                    fun_test.log(
                        "Read Stats are not as expected, checking if it is in pass threshold range: {}".format(
                            self.vol_stats_threshold_pass))
                    if (expected_read > actual_read) and (expected_read - actual_read) \
                            <= self.vol_stats_threshold_pass or (actual_read > expected_read) and \
                            (actual_read - expected_read) <= self.vol_stats_threshold_pass:
                        fun_test.add_checkpoint("Actual {} read stat is within expected range {}".
                                                format(actual_read, expected_read), "PASSED",
                                                expected_read, actual_read)
                        fun_test.critical("Actual {} Read stat is within the expected range {}".format(
                            actual_read, expected_read))
                    else:
                        fun_test.log("Actual Stats are not within pass threshold range")
                        fun_test.test_assert_expected(expected=expected_read, actual=actual_read,
                                                      message="Read counter is correct")
                else:
                    fun_test.test_assert_expected(expected=expected_read, actual=actual_read,
                                                  message="Read counter is correct")

        if self.restart_f1:
            sc_disconnect = self.storage_controller.disconnect()
            fun_test.test_assert_expected(True, sc_disconnect, "Disconnecting Storage Controller before F1 restart")
            fun_test.log("Restarting F1....")

            # Restarting F1 without app=mdt_test run, to retain storage disk and data after reboot
            restart_result = self.dut_instance.restart(mdt_rebuild=False)
            fun_test.test_assert(restart_result, "FunOS is restarted")

            fun_test.log("Reset variables")
            # self.restart_f1 = False
            fun_test.shared_variables["setup_after_restart"] = True
            fun_test.shared_variables["ctrl_created"] = False
            fun_test.shared_variables["setup_created"] = False

            fun_test.log("Recalling setup to attach volume/s after restart...")
            self.setup()
            fun_test.shared_variables["setup_after_restart"] = False

            fio_result = {}
            fio_output = {}
            internal_result = {}
            initial_volume_status = {}
            final_volume_status = {}
            diff_volume_stats = {}

            mode = "read"
            fio_result[mode] = True
            internal_result[mode] = True

            # Pulling initial volume stats of all the volumes from the DUT in dictionary format
            fun_test.log(
                "Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                "the test")
            initial_volume_status[mode] = {}
            volumes = sorted(self.volume_params["type"])
            for type in volumes:
                initial_volume_status[mode][type] = {}
                for index, uuid in enumerate(self.uuids[type]):
                    initial_volume_status[mode][type][index] = {}
                    storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                 self.volume_params["type"][type], uuid,
                                                                 "stats")
                    command_result = {}
                    command_result = self.storage_controller.peek(storage_props_tree)
                    fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                           format(type, index))
                    initial_volume_status[mode][type][index] = command_result["data"]
                    fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                    fun_test.log(initial_volume_status[mode][type][index])

            # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
            fun_test.log("Running FIO for mode {}".format(mode))
            fio_output[mode] = {}
            fio_output[mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode, **self.fio_params)
            fun_test.log("FIO Command Output:")
            fun_test.log(fio_output[mode])
            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                           self.iter_interval)

            if not ((hasattr(self, "trigger_blt_failure") and self.trigger_blt_failure)
                    or (hasattr(self, "trigger_lsv_failure") and self.trigger_lsv_failure)):
                fun_test.test_assert(fio_output[mode], "Fio {} run is completed".format(mode))
                # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
                fun_test.log("Pulling volume stats of all volumes after the FIO test")
                final_volume_status[mode] = {}
                for type in volumes:
                    final_volume_status[mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes",
                                                                     self.volume_params["type"][type], uuid,
                                                                     "stats")
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[mode][type][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[mode] = {}
                for type in volumes:
                    diff_volume_stats[mode][type] = {}
                    for index in range(len(self.uuids[type])):
                        diff_volume_stats[mode][type][index] = {}
                        for fkey, fvalue in final_volume_status[mode][type][index].items():
                            # Don't compute the difference of stats which is not defined in expected_volume_stats in
                            # the json config file
                            if fkey not in fkey == "fault_injection":
                                diff_volume_stats[mode][type][index][fkey] = fvalue
                                continue
                            if fkey in initial_volume_status[mode][type][index]:
                                ivalue = initial_volume_status[mode][type][index][fkey]
                                diff_volume_stats[mode][type][index][fkey] = fvalue - ivalue
                        fun_test.log("Difference of {} {} volume status before and after the test:".
                                     format(type, index))
                        fun_test.log(diff_volume_stats[mode][type][index])
                fun_test.log("Diff volume stats is: {}".format(diff_volume_stats))

                for type in volumes:
                    if type == "jvol":
                        continue
                    bs_in_bytes = utils.convert_to_bytes(str(self.volume_params["block_size"][type]))
                    fun_test.test_assert(bs_in_bytes != -1, "Converted volume block size in bytes")
                    expected_read = (size_in_bytes / bs_in_bytes)
                    actual_read = diff_volume_stats[mode][type][0]["num_reads"]
                    if ((hasattr(self, "trigger_blt_failure") and self.trigger_blt_failure)
                            or (hasattr(self, "trigger_lsv_failure") and self.trigger_lsv_failure)):
                        expected_read = 0
                    fun_test.log("Expected counters are: write 0, read {}".format(expected_read))

                    # For LSV on to of BLT, stats on BLT might not match - checking if stats are in expected pass range
                    if expected_read != actual_read:
                        fun_test.log("Stats are not as expected, checking if it is in pass threshold range")
                        fun_test.log("Stats pass threshold defined is: {}".format(self.vol_stats_threshold_pass))
                        if (expected_read > actual_read) and (expected_read - actual_read) \
                                <= self.vol_stats_threshold_pass or (actual_read > expected_read) and \
                                (actual_read - expected_read) <= self.vol_stats_threshold_pass:
                            fun_test.add_checkpoint("Actual {} read stat is within expected range {}".
                                                    format(actual_read, expected_read), "PASSED",
                                                    expected_read, actual_read)
                            fun_test.critical("Actual {} value is within the expected range {}".format(
                                actual_read, expected_read))
                        else:
                            fun_test.log("Actual Stats are not within pass threshold range")
                            fun_test.test_assert_expected(expected=expected_read, actual=actual_read,
                                                          message="Read counter is correct")
                    else:
                        fun_test.test_assert_expected(expected=expected_read, actual=actual_read,
                                                      message="Read counter is correct")
                    fun_test.test_assert_expected(expected=0, actual=actual_write, message="Write counter is correct")
            else:
                fun_test.test_assert(not fio_output[mode], "Expected fio error".format(mode))

    def cleanup(self):
        fun_test.shared_variables["setup_after_restart"] = False
        # Detaching volume/s
        if fun_test.shared_variables["setup_created"]:
            self.uuids = fun_test.shared_variables["uuids"]
            if self.use_lsv:
                type = "lsv"
                uuid = self.uuids
            else:
                type = "blt"
                uuid = self.uuids[type][0]

            result_detach_volume = self.storage_controller.volume_detach_remote(
                ns_id=self.ns_id, uuid=uuid, remote_ip=self.linux_host.internal_ip)
            fun_test.test_assert(result_detach_volume["status"], "{} volume is detached".format(type))

            # Deleting LS volume and Journal volume
            if self.use_lsv:
                result_delete_lsv = self.storage_controller.delete_volume(
                    type=self.volume_params["type"]["lsv"], capacity=self.volume_params["capacity"]["lsv"],
                    uuid=self.uuids["lsv"][0], block_size=self.volume_params["block_size"]["lsv"],
                    name=self.volume_params["name"]["lsv"])
                fun_test.shared_variables["setup_created"] = False
                fun_test.test_assert(result_delete_lsv["status"], "LS volume is deleted")

                result_delete_jvol = self.storage_controller.delete_volume(
                    type=self.volume_params["type"]["jvol"], capacity=self.volume_params["capacity"]["jvol"],
                    uuid=self.uuids["jvol"][0], block_size=self.volume_params["block_size"]["jvol"],
                    name=self.volume_params["name"]["jvol"])
                fun_test.shared_variables["setup_created"] = False
                fun_test.test_assert(result_delete_jvol["status"], "Journal volume is deleted")

            # Deleting BLT volume
            uuid = self.uuids["blt"][0]
            result_delete_volume = self.storage_controller.delete_thin_block_volume(
                capacity=self.volume_params["capacity"][type], uuid=uuid,
                block_size=self.volume_params["block_size"][type], name=self.volume_params["name"][type])
            fun_test.shared_variables["setup_created"] = False
            fun_test.test_assert(result_delete_volume["status"], "{} volume is deleted".format(type))

            # self.storage_controller.disconnect()


class BLTF1RestartFio(BLTF1RestartTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Verify data retention after F1 Restart for BLT volume",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create volume
        4. Attach volume to remote server
        5. Write data (buffer pattern) using fio from remote server
        6. Read data (buffer pattern) with Read IO and validate with data write
        7. Restart F1 (without mdt_test)
        8. Attach same volume
        9. Read data (buffer pattern) with Read IO after restart and validate with data write
        10. Detach volume
        11. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(BLTF1RestartFio, self).setup()

    def run(self):
        super(BLTF1RestartFio, self).run()

    def cleanup(self):
        super(BLTF1RestartFio, self).cleanup()


class LSVOnBLTF1RestartFio(BLTF1RestartTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Verify data retention after F1 Restart for LSV on top of BLT",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create BLT volume
        4. Create Journal volume
        5. Create LS volume on top of BLT volume
        6. Attach LS volume to remote server
        7. Write data (buffer pattern) using fio from remote server
        8. Read data (buffer pattern) with Read IO and validate with data write
        9. Restart F1 (without rebuilding mdt_test)
        10. Attach same volume
        11. Read data (buffer pattern) with Read IO after restart and validate with data write
        12. Detach LSV volume
        13. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(LSVOnBLTF1RestartFio, self).setup()

    def run(self):
        super(LSVOnBLTF1RestartFio, self).run()

    def cleanup(self):
        super(LSVOnBLTF1RestartFio, self).cleanup()


class BLTF1FaultInjectFio(BLTF1RestartTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Verify BLT with fault injection and F1 restart",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create volume
        4. Attach volume to remote server
        5. Inject failure
        6. Write data (buffer pattern) using fio from remote server
        7. Read data (buffer pattern) with Read IO and validate with data write
        8. Restart F1 (without mdt_test)
        9. Attach same volume
        10. Read data (buffer pattern) with Read IO after restart and validate with data write
        11. Detach volume
        12. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(BLTF1FaultInjectFio, self).setup()

    def run(self):
        super(BLTF1FaultInjectFio, self).run()

    def cleanup(self):
        super(BLTF1FaultInjectFio, self).cleanup()


class LSVOnBLTF1FaultInjectFio(BLTF1RestartTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Verify LSV on top of BLT with fault injection and F1 restart",
                              steps="""
        1. Use StorageController to connect to the dpcsh tcp proxy to F1
        2. Configure ip_cfg
        3. Create BLT volume
        4. Create Journal volume
        5. Create LS volume on top of BLT volume
        6. Attach LS volume to remote server
        7. Attach volume to remote server
        8. Inject failure
        9. Write data (buffer pattern) using fio from remote server
        10. Read data (buffer pattern) with Read IO and validate with data write
        11. Restart F1 (without mdt_test)
        12. Attach same volume
        13. Read data (buffer pattern) with Read IO after restart and validate with data write
        14. Detach volume
        15. Delete volume and verify stats are cleared for deleted volume
                              """)

    def setup(self):
        super(LSVOnBLTF1FaultInjectFio, self).setup()

    def run(self):
        super(LSVOnBLTF1FaultInjectFio, self).run()

    def cleanup(self):
        super(LSVOnBLTF1FaultInjectFio, self).cleanup()


if __name__ == "__main__":
    blt_f1_restart = BltF1RestartScript()
    blt_f1_restart.add_test_case(BLTF1RestartFio())
    blt_f1_restart.add_test_case(LSVOnBLTF1RestartFio())
    blt_f1_restart.add_test_case(BLTF1FaultInjectFio())
    blt_f1_restart.add_test_case(LSVOnBLTF1FaultInjectFio())
    blt_f1_restart.run()
