from start_traffic_helper import *
from asset.asset_manager import AssetManager
from lib.fun.fs import ComE, Bmc
import bmc_commands
import dpcsh_commands
import file_helper
import debug_memory_calculation
from lib.topology.topology_helper import TopologyHelper
from fun_global import PerfUnit, FunPlatform
from web.fun_test.analytics_models_helper import get_data_collection_time, ModelHelper
import stats_calculation
from lib.fun import fs
from scripts.storage.storage_helper import *
import get_params_for_time


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        job_inputs = fun_test.get_job_inputs()
        config_file = fun_test.get_script_name_without_ext() + ".json"
        self.fs = AssetManager().get_fs_by_name(fs_name)
        fun_test.log(json.dumps(self.fs, indent=4))
        fun_test.log("Input: {}".format(job_inputs))

        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

        if job_inputs:
            if "disable_f1_index" in job_inputs:
                self.disable_f1_index = job_inputs["disable_f1_index"]
            if "boot_new_image" in job_inputs:
                self.boot_new_image = job_inputs["boot_new_image"]
            if "ec_vol" in job_inputs:
                self.ec_vol = job_inputs["ec_vol"]
            if "add_boot_arg" in job_inputs:
                self.add_boot_arg = job_inputs["add_boot_arg"]
                self.add_boot_arg = "--" + self.add_boot_arg

        f1_0_boot_args = 'cc_huid=3 sku=SKU_FS1600_0 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303 %s'%(self.add_boot_arg)
        f1_1_boot_args = 'cc_huid=2 sku=SKU_FS1600_1 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303 %s'%(self.add_boot_arg)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}},
                                           skip_funeth_come_power_cycle=True,
                                           dut_index=0)

        if self.disable_f1_index == 0 or self.disable_f1_index == 1:
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}},
                                               skip_funeth_come_power_cycle=True,
                                               dut_index=0,
                                               disable_f1_index=self.disable_f1_index)
        if self.disable_f1_index == 0:
            self.run_on_f1 = [1]
        elif self.disable_f1_index == 1:
            self.run_on_f1 = [0]
        else:
            self.run_on_f1 = [0, 1]

        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])
        if self.boot_new_image:
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology deployed")
        self.verify_dpcsh_started()
        if not self.boot_new_image:
            self.clear_uart_logs()
        if self.ec_vol:
            self.create_4_et_2_ec_volume()

        fun_test.shared_variables["run_on_f1"] = self.run_on_f1
        fun_test.shared_variables["fs"] = self.fs

    def verify_dpcsh_started(self):
        for f1 in self.run_on_f1:
            fun_test.log("Verifying if the DPCSH has started on F1 {}".format(f1))
            dpcsh_pid = self.come_handle.get_process_id_by_pattern("/nvme{}".format(f1))
            if not dpcsh_pid:
                self.come_handle.enter_sudo()
                self.come_handle.command("cd /scratch/FunSDK/bin/Linux")
                self.come_handle.command(
                    "./dpcsh --pcie_nvme_sock=/dev/nvme{f1} --nvme_cmd_timeout=600000"
                    " --tcp_proxy=4022{f1} &> /tmp/f1_{f1}_dpc.txt &".format(f1=f1))
                self.come_handle.exit_sudo()
                fun_test.log("Started DPCSH on F1 {}".format(f1))
            else:
                fun_test.log("Dpcsh is already running for F1 {}".format(f1))
        fun_test.test_assert(True, "DPCSH running")

    def create_4_et_2_ec_volume(self):
        for f1 in self.run_on_f1:
            # fun_test.sleep("Getting started with creation of 4:2 EC volume on F1_0".format(f1), seconds=30)
            transport = "PCI"
            huid = [3, 2]
            ctlid = [2, 2]
            ns_id = [1, 1]
            fnid = 2
            command_timeout = 120
            f1_in_use = [0, 1]
            warm_up_fio_cmd_args = {
                "bs": "8k",
                "iodepth": 1,
                "size": "100%",
                "rw": "write",
                "direct": 1,
                "prio": 0,
                "timeout": 720
            }

            ec_info_0 = {
                "volume_types": {
                    "ndata": "VOL_TYPE_BLK_LOCAL_THIN",
                    "nparity": "VOL_TYPE_BLK_LOCAL_THIN",
                    "ec": "VOL_TYPE_BLK_EC",
                    "lsv": "VOL_TYPE_BLK_LSV",
                    "jvol": "VOL_TYPE_BLK_NV_MEMORY"
                },
                "volume_block": {
                    "ndata": 4096,
                    "nparity": 4096,
                    "ec": 4096,
                    "lsv": 4096,
                    "jvol": 512
                },
                "ndata": 4,
                "nparity": 2,
                "capacity": 26843545600,
                "use_lsv": 1,
                "lsv_pct": 1,
                "lsv_chunk_size": 128,
                "jvol_size_multiplier": 8,
                "num_volumes": 1
            }

            ec_info_1 = {
                "volume_types": {
                    "ndata": "VOL_TYPE_BLK_LOCAL_THIN",
                    "nparity": "VOL_TYPE_BLK_LOCAL_THIN",
                    "ec": "VOL_TYPE_BLK_EC",
                    "lsv": "VOL_TYPE_BLK_LSV",
                    "jvol": "VOL_TYPE_BLK_NV_MEMORY"
                },
                "volume_block": {
                    "ndata": 4096,
                    "nparity": 4096,
                    "ec": 4096,
                    "lsv": 4096,
                    "jvol": 512
                },
                "ndata": 4,
                "nparity": 2,
                "capacity": 32212254720,
                "use_lsv": 1,
                "lsv_pct": 1,
                "lsv_chunk_size": 128,
                "jvol_size_multiplier": 8,
                "num_volumes": 1
            }
            result = False
            try:
                index = f1
                storage_controller_0 = StorageController(target_ip=self.come_handle.host_ip,
                                                         target_port=self.come_handle.get_dpc_port(f1_in_use[index]))
                ctrlr_uuid = utils.generate_uuid()
                fun_test.test_assert(storage_controller_0.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                                            transport=transport,
                                                                            huid=huid[index],
                                                                            ctlid=ctlid[index],
                                                                            fnid=fnid,
                                                                            command_duration=120)['status'],
                                     message="Create Controller with UUID: {}".format(ctrlr_uuid))
                # create ec_vol
                if index==0:
                    ec_info = ec_info_0
                else:
                    ec_info = ec_info_1
                (ec_config_status, ec_info) = storage_controller_0.configure_ec_volume(ec_info, command_timeout)

                ec_uuid = ec_info["attach_uuid"][0]

                fun_test.test_assert(storage_controller_0.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                      ns_id=ns_id[index],
                                                                                      vol_uuid=ec_uuid),
                                     message="Attaching EC Vol nsid: {} with uuid {} to controller".format(ns_id[index],
                                                                                                           ec_uuid))
                fetch_nvme = fetch_nvme_device(self.come_handle, 1, size=ec_info["capacity"])
                fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
                fio_output = self.come_handle.pcie_fio(filename=fetch_nvme["nvme_device"], **warm_up_fio_cmd_args)
                result = True
                fun_test.test_assert(result, "Created 4:2 EC volume on F1 {}".format(f1))
            except Exception as ex:
                fun_test.log(ex)
        return result


    def clear_uart_logs(self):
        result = False
        try:
            bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                             ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                             ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                             set_term_settings=True,
                             disable_uart_logger=False)
            bmc_handle.set_prompt_terminator(r'# $')
            f1_index = 0
            f1_0_uart_file = bmc_handle.get_f1_uart_log_file_name(f1_index=f1_index)
            bmc_handle.command("echo '' > {}".format(f1_0_uart_file))
            f1_index = 1
            f1_1_uart_file = bmc_handle.get_f1_uart_log_file_name(f1_index=f1_index)
            bmc_handle.command("echo '' > {}".format(f1_1_uart_file))
            result = True
        except Exception as ex:
            fun_test.log(ex)
        fun_test.test_assert(result, "Cleared the uart logs")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.run_on_f1 = fun_test.shared_variables["run_on_f1"]
        self.fs = fun_test.shared_variables["fs"]
        job_inputs = fun_test.get_job_inputs()
        config_file = fun_test.get_script_name_without_ext() + ".json"
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)
        if job_inputs:
            if "specific_apps" in job_inputs:
                self.specific_apps = job_inputs["specific_apps"]
            if "add_to_database" in job_inputs:
                self.add_to_database = job_inputs["add_to_database"]
            if "duration" in job_inputs:
                self.duration = job_inputs["duration"]
            if "run_le_firewall" in job_inputs:
                self.run_le_firewall = job_inputs["run_le_firewall"]
            if "collect_stats" in job_inputs:
                self.collect_stats = job_inputs["collect_stats"]
            if "disable_stats" in job_inputs:
                self.disable_stats = job_inputs["disable_stats"]
            if "boot_new_image" in job_inputs:
                self.boot_new_image = job_inputs["boot_new_image"]
            if "end_sleep" in job_inputs:
                self.end_sleep = job_inputs["end_sleep"]

        # Create the files
        self.stats_info = {}
        # post_fix_name: "{calculated_}{app_name}_OUTPUT"
        # post_fix_name: "{calculated_}{app_name}_DPCSH_OUTPUT_F1_{f1}_logs.txt"
        # description : "{calculated_}_{app_name}_DPCSH_OUTPUT_F1_{f1}"
        self.stats_info["bmc"] = {"POWER": {"calculated": True}, "DIE_TEMPERATURE": {"calculated": False, "disable":True}}
        self.stats_info["come"] = {"DEBUG_MEMORY": {}, "CDU": {}, "EQM": {}, "BAM": {"calculated": False, "disable":True}, "DEBUG_VP_UTIL": {"calculated": False, "disable": True}, "LE": {}, "HBM": {"calculated": True},
                                   "EXECUTE_LEAKS": {"calculated": False}, "PC_DMA": {"calculated": True}, "DDR":{"calculated": True}}
        self.stats_info["files"] = {"fio":{"calculated": False}}

        if self.collect_stats:
            for system in self.stats_info:
                for stat_name, value in self.stats_info[system].iteritems():
                    if stat_name in self.collect_stats:
                        value["disable"] = False
                    else:
                        value["disable"] = True

        if self.disable_stats:
            for system in self.stats_info:
                for stat_name, value in self.stats_info[system].iteritems():
                    if stat_name in self.disable_stats:
                        value["disable"] = True

        for system in self.stats_info:
            for stat_name, value in self.stats_info[system].iteritems():
                if value.get("disable", False):
                    fun_test.log("stat: {} has been disabled".format(stat_name))
                    continue
                cal = ["", "calculated_"] if value.get("calculated", True) else [""]
                for calculated in cal:
                    if system == "bmc":
                        globals()["{}{}_OUTPUT".format(calculated, stat_name)] = fun_test.get_test_case_artifact_file_name(post_fix_name="{}{}_OUTPUT_logs.txt".format(calculated, stat_name))
                        fun_test.add_auxillary_file(description="{}{}_OUTPUT".format(calculated.upper(), stat_name), filename=globals()["{}{}_OUTPUT".format(calculated, stat_name)])
                        setattr(self, "f_{}{}".format(calculated,stat_name), open(globals()["{}{}_OUTPUT".format(calculated, stat_name)], "w+"))
                    elif system == "come":
                        for f1 in self.run_on_f1:
                            globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name,f1)] = fun_test.get_test_case_artifact_file_name(post_fix_name="{}{}_DPCSH_OUTPUT_F1_{}_logs.txt".format(calculated, stat_name, f1))
                            fun_test.add_auxillary_file(description="{}{}_DPCSH_OUTPUT_F1_{}".format(calculated.upper(), stat_name, f1),filename=globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name, f1)])
                            setattr(self, "f_{}{}_f1_{}".format(calculated, stat_name, f1),open(globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name, f1)],"w+"))
                    elif system == "files":
                        for f1 in self.run_on_f1:
                            globals()["{}_OUTPUT_F1_{}".format(stat_name,f1)] = fun_test.get_test_case_artifact_file_name(post_fix_name="{}_OUTPUT_F1_{}_logs.txt".format(stat_name, f1))
                            fun_test.add_auxillary_file(description="{}_OUTPUT_F1_{}".format(stat_name, f1),filename=globals()["{}_OUTPUT_F1_{}".format(stat_name, f1)])
                            setattr(self, "f_{}_f1_{}".format(stat_name, f1),open(globals()["{}_OUTPUT_F1_{}".format(stat_name, f1)], "w+"))

        # Traffic
        self.methods = {"crypto": crypto, "zip": zip_deflate, "rcnvme": rcnvme}
        self.threaded_apps = {}
        # self.threaded_apps = {"busy_loop": "soak_flows_busy_loop_10usecs", "memcpy_1MB":"soak_flows_memcpy_1MB_non_coh"}

        if self.duration == "1m":
            self.test_duration = 60
        elif self.duration == "1h":
            self.test_duration = 3600
        elif self.duration == "3h":
            self.test_duration = 10800

    def run(self):
        ############## Before traffic #####################
        if not self.stats_info["come"]["DEBUG_MEMORY"]["disable"]:
            self.initial_debug_memory_stats = self.get_debug_memory_stats_initially(self.f_DEBUG_MEMORY_f1_0,
                                                                                    self.f_DEBUG_MEMORY_f1_0)
        self.capture_data(count=3, heading="Before starting traffic")

        fun_test.test_assert(True, "Initial debug stats is saved")

        ############# Starting Traffic ################
        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])

        app_params = get_params_for_time.get(self.test_duration)
        if self.specific_apps:
            app_params = get_params_for_time.get(self.test_duration, specific_field=self.specific_apps)
        fun_test.log("App parameters: {}".format(app_params))

        if self.run_le_firewall:
            self.restart_dpcsh()
            le_firewall(self.test_duration, self.boot_new_image)
            # self.restart_dpcsh()

        if "fio" in app_params:
            fio_data = app_params["fio"]
            fio_data["runtime"] += 40
            fio_thread_map = self.start_fio_as_thread(fio_data)

        # thread_map_for_soak_apps = self.start_threaded_apps()

        for app, parameters in app_params.iteritems():
            if app == "fio":
                continue
            for f1 in self.run_on_f1:
                parameters["f1"] = f1
                result = self.methods[app](self.come_handle, **parameters)
                fun_test.test_assert(result, "{} traffic started on F1_{}".format(app, f1))

        ################ During traffic ##################
        # fun_test.sleep("Wait for traffic to start")
        count = int(self.test_duration / 5)
        heading = "During traffic"
        fun_test.log("Capturing the data {}".format(heading))
        self.capture_data(count=count, heading=heading)

        if "fio" in app_params:
            self.join_fio_thread(fio_thread_map)

        #################### After the traffic ############
        if self.run_le_firewall:
            le_firewall(self.test_duration, self.boot_new_image, True)
        # self.stop_threaded_apps(thread_map_for_soak_apps)

        count = 3
        heading = "After the traffic"
        fun_test.log("Capturing the data {}".format(heading))
        self.capture_data(count=count, heading=heading)

        self.come_handle.destroy()

        fun_test.sleep("Waiting for all the things to settle", seconds=self.end_sleep)


    def capture_data(self, count, heading):
        def func_not_found():
            print "Function not found"
        # power stats
        # function name standard format: func_'stats_name'
        thread_map = {}
        thread_count = 0
        time_in_seconds = 1
        for system in self.stats_info:
            if system == "files":
                continue
            for stat_name,value  in self.stats_info[system].iteritems():
                if value.get("disable", False):
                    fun_test.log("stat: {} has been disabled".format(stat_name))
                    continue
                func_name = "func_{}".format(stat_name.lower())
                func_def = getattr(self, func_name, func_not_found)
                if system == "bmc":
                    thread_map[thread_count] = fun_test.execute_thread_after(func=func_def,
                                                                             time_in_seconds=time_in_seconds,
                                                                             count=count,
                                                                             heading=heading)
                elif system == "come":
                    for f1 in self.run_on_f1:
                        thread_map[thread_count] = fun_test.execute_thread_after(func=func_def,
                                                                                 time_in_seconds=time_in_seconds,
                                                                                 count=count,
                                                                                 heading=heading,
                                                                                 f1=f1)
                thread_count +=1
                time_in_seconds += 1
                if time_in_seconds > 10:
                    time_in_seconds = 1
                fun_test.test_assert(True, "Started capturing the {} stats {}".format(stat_name, heading))

        for i in range(thread_count):
            fun_test.join_thread(thread_map[i])

    ############# EQM ################
    def func_eqm(self, f1, count, heading):
        stat_name = "EQM"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.eqm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.eqm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()

    ############# LE Firewall #############
    def func_le(self, f1, count, heading):
        stat_name = "LE"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.le(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.le(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()


    ############# CDU ################
    def func_cdu(self, f1, count, heading):
        stat_name = "CDU"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.cdu(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.cdu(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
        come_handle.destroy()

    ####### PC DMA #########
    def func_pc_dma(self, count, heading, f1):
        stat_name = "PC_DMA"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.pc_dma(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.pc_dma(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
        come_handle.destroy()

    ############# BAM ################
    def func_bam(self, f1, count, heading):
        stat_name = "BAM"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.bam(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration")
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
        come_handle.destroy()

    ############### debug vp_utils #######
    def func_debug_vp_util(self, f1, count, heading):
        stat_name = "DEBUG_VP_UTIL"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_vp_utils(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration")
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
        come_handle.destroy()

    ########### HBM ##################
    def func_hbm(self, f1, count, heading):
        stat_name = "HBM"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.hbm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.hbm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()

    ############   DDR #############
    def func_ddr(self, f1, count, heading):
        stat_name = "DDR"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.ddr(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.ddr(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()


    ######## EXECUTE LEAKS ###########
    def func_execute_leaks(self,f1,count, heading):
        stat_name = "EXECUTE_LEAKS"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        count = 1
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.execute_leaks(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

    ############## power #############
    def func_power(self, count, heading):
        stat_name = "POWER"
        bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                         ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                         ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                         set_term_settings=True,
                         disable_uart_logger=False)
        bmc_handle.set_prompt_terminator(r'# $')

        for i in range(count):
            raw_output, cal_output, pro_data = bmc_commands.power_manager(bmc_handle=bmc_handle)
            time_now = datetime.datetime.now()
            print_data = {"output": raw_output, "time": time_now}
            file_helper.add_data(getattr(self, "f_{}".format(stat_name)), print_data, heading=heading)
            print_data = {"output": cal_output, "time": time_now}
            file_helper.add_data(getattr(self, "f_calculated_{}".format(stat_name)), print_data, heading=heading)
            fun_test.sleep("before next iteration", seconds=5)
            if heading == "During traffic" and self.add_to_database:
                self.add_to_database = False
                print ("Result : {}".format(pro_data))
                self.add_to_data_base(pro_data)
                fun_test.log("Data added to the database, Data: {}".format(pro_data))
        bmc_handle.destroy()

    ############ Die temperature #########
    def func_die_temperature(self, count, heading):
        stat_name = "DIE_TEMPERATURE"
        bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                         ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                         ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                         set_term_settings=True,
                         disable_uart_logger=False)
        bmc_handle.set_prompt_terminator(r'# $')
        for i in range(count):
            output = bmc_commands.die_temperature(bmc_handle)
            time_now = datetime.datetime.now()
            print_data = {"output": output, "time": time_now}
            file_helper.add_data(getattr(self, "f_{}".format(stat_name)), print_data, heading=heading)
            fun_test.sleep("before next iteration")
        bmc_handle.destroy()

    ###########  debug memory ########
    def func_debug_memory(self, f1, count, heading):
        stat_name = "DEBUG_MEMORY"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        dpcsh_output_list = []
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_memory(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            differnce_data_set = {}
            difference_output = debug_memory_calculation.debug_difference(self.initial_debug_memory_stats,one_dataset,f1=f1)
            differnce_data_set["output"] = difference_output
            differnce_data_set["time"] = datetime.datetime.now()
            differnce_data_set["time_difference"] = difference_output["time_difference"]
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), differnce_data_set, heading=heading)

            dpcsh_output_list.append(one_dataset)
            fun_test.sleep("before next iteration", seconds=3)

        come_handle.destroy()


    ########## MUD ###################
    def get_debug_memory_stats_initially(self, f_debug_memory_f1_0, f_debug_memory_f1_1):
        result = {}
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        heading = "Initial stats"
        for f1 in self.run_on_f1:
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_memory(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            if f1 == 0:
                file_helper.add_data(f_debug_memory_f1_0, one_dataset, heading=heading)
            else:
                file_helper.add_data(f_debug_memory_f1_1, one_dataset, heading=heading)
            result["f1_{}".format(f1)] = one_dataset.copy()
        come_handle.destroy()
        return result

    ####### Data Capturing function ############

    def add_to_data_base(self, value_dict):
        unit_dict = {
            "fs_power_unit": PerfUnit.UNIT_WATT,
            "f1_0_power_unit": PerfUnit.UNIT_WATT,
            "f1_1_power_unit": PerfUnit.UNIT_WATT,
        }
        value_dict["date_time"] = get_data_collection_time()
        value_dict["version"] = fun_test.get_version()
        model_name = "PowerPerformance"
        status = fun_test.PASSED
        try:
            generic_helper = ModelHelper(model_name=model_name)
            generic_helper.set_units(validate=True, **unit_dict)
            generic_helper.add_entry(**value_dict)
            generic_helper.set_status(status)
            print "used generic helper to add an entry"
        except Exception as ex:
            fun_test.critical(str(ex))

    def clear_uart_logs(self):
        bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                         ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                         ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                         set_term_settings=True,
                         disable_uart_logger=False)
        bmc_handle.set_prompt_terminator(r'# $')
        f1_index = 0
        f1_0_uart_file = bmc_handle.get_f1_uart_log_file_name(f1_index=f1_index)
        bmc_handle.command("echo '' > {}".format(f1_0_uart_file))
        f1_index = 1
        f1_1_uart_file = bmc_handle.get_f1_uart_log_file_name(f1_index=f1_index)
        bmc_handle.command("echo '' > {}".format(f1_1_uart_file))

    def restart_dpcsh(self):
        for f1 in self.run_on_f1:
            dpcsh_pid = self.come_handle.get_process_id_by_pattern("/nvme{}".format(f1))
            if dpcsh_pid:
                self.come_handle.kill_process(process_id=dpcsh_pid, signal=9)
        self.verify_dpcsh_started()

    def verify_dpcsh_started(self):
        for f1 in self.run_on_f1:
            fun_test.log("Verifying if the DPCSH has started on F1 {}".format(f1))
            dpcsh_pid = self.come_handle.get_process_id_by_pattern("/nvme{}".format(f1))
            if not dpcsh_pid:
                self.come_handle.enter_sudo()
                self.come_handle.command("cd /scratch/FunSDK/bin/Linux")
                self.come_handle.command(
                    "./dpcsh --pcie_nvme_sock=/dev/nvme{f1} --nvme_cmd_timeout=600000"
                    " --tcp_proxy=4022{f1} &> /tmp/f1_{f1}_dpc.txt &".format(f1=f1))
                self.come_handle.exit_sudo()
                fun_test.log("Started DPCSH on F1 {}".format(f1))
            else:
                fun_test.log("Dpcsh is already running for F1 {}".format(f1))
        fun_test.test_assert(True, "DPCSH running")

    def cleanup(self):
        if not self.boot_new_image:
            bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                             ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                             ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                             set_term_settings=True,
                             disable_uart_logger=False)
            bmc_handle.set_prompt_terminator(r'# $')
            # bmc_handle.cleanup()
            # Capture the UART logs also
            artifact_file_name_f1_0 = bmc_handle.get_uart_log_file(0)
            artifact_file_name_f1_1 = bmc_handle.get_uart_log_file(1)
            fun_test.add_auxillary_file(description="DUT_0_fs-65_F1_0 UART Log", filename=artifact_file_name_f1_0)
            fun_test.add_auxillary_file(description="DUT_0_fs-65_F1_1 UART Log", filename=artifact_file_name_f1_1)

    def start_threaded_apps(self):
        def func_not_found():
            print "Function not found"
        self.required_apps = {}
        if self.specific_apps:
            for app in self.specific_apps:
                if app in self.threaded_apps:
                    self.required_apps[app] = self.threaded_apps[app]
        else:
            self.required_apps.update(self.threaded_apps)

        thread_map = {}
        for app in self.required_apps:
            for f1 in self.run_on_f1:
                fun_test.shared_variables["var_{}_f1_{}".format(app, f1)] = True
                thread_map["{}_{}".format(app, f1)] = fun_test.execute_thread_after(
                    func=getattr(self, app, func_not_found),
                    time_in_seconds=1,
                    f1=f1)
                fun_test.log("Started the app : {} on f1: {}".format(app, f1))
        return thread_map

    def stop_threaded_apps(self, thread_map):
        for app in self.required_apps:
            for f1 in self.run_on_f1:
                fun_test.shared_variables["var_{}_f1_{}".format(app, f1)] = False
                fun_test.log("Stopped the app : {} on f1: {}".format(app, f1))

        for name, thread in thread_map.iteritems():
            fun_test.join_thread(thread)



    def busy_loop(self, f1):
        app = "busy_loop"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
        while track_app:
            dpcsh_out = dpcsh_commands.busy_loop(come_handle, f1)
            track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
            fun_test.sleep("Before next iteration app: {}".format(app))

    def memcpy_1MB(self, f1):
        app = "memcpy_1MB"
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
        while track_app:
            dpcsh_out = dpcsh_commands.memcpy_1MB(come_handle, f1)
            track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
            fun_test.sleep("Before next iteration app: {}".format(app))

    def start_fio_as_thread(self,fio_data):
        fio_thread_map = {}
        fio_capacity_map = {"f1_0": 26843545600, "f1_1": 32212254720}
        self.fio_params.update(fio_data)
        for f1 in self.run_on_f1:
            try:
                come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                   ssh_username=self.fs['come']['mgmt_ssh_username'],
                                   ssh_password=self.fs['come']['mgmt_ssh_password'])

                fetch_nvme = fetch_nvme_device(come_handle, 1, size=fio_capacity_map["f1_{}".format(f1)])
                if fetch_nvme["status"]:
                    fun_test.test_assert(True, "{} traffic started on F1_{}".format("fio", f1))
                    fio_thread_map["{}".format(f1)] = fun_test.execute_thread_after(func=self.func_fio,
                                                                                           time_in_seconds=5,
                                                                                           filename=fetch_nvme["nvme_device"],
                                                                                           come_handle=come_handle,
                                                                                           f1=f1,
                                                                                           **self.fio_params)
                else:
                    fun_test.critical("Volumes not create on F1: {}".format(f1))
                come_handle.destroy()
            except Exception as ex:
                fun_test.log(ex)
        return fio_thread_map

    def join_fio_thread(self, thread_map):
        stat_name = "fio"
        for f1, thread in thread_map.iteritems():
            one_dataset = {}
            fun_test.log("Trying to join fio thread f1: {}".format(f1))
            fun_test.join_thread(thread)
            fun_test.test_assert(True,"FIO successfully completed on f1 : {}".format(f1))
            try:
                fun_test.sleep("Generating fio output")
                output = fun_test.shared_variables["fio_output_f1_{}".format(f1)]
                one_dataset["time"] = datetime.datetime.now()
                one_dataset["output"] = output
                file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset)
            except Exception as ex:
                fun_test.log(ex)

    def func_fio(self, come_handle, filename, f1,**params):
        try:
            fio_output = come_handle.pcie_fio(timeout=params["runtime"] + 100,
                                              filename=filename,
                                              **params)
        except Exception as ex:
            fun_test.critical(ex)
        fun_test.shared_variables["fio_output_f1_{}".format(f1)] = fio_output




if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
