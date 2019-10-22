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
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        # we have the combination for
        # 1. 1min
        # 2. 1hour - 60 min
        # 3. 3.5 hour - 210 min
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

        self.f1_0_boot_args = 'cc_huid=3 sku=SKU_FS1600_0 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303'
        self.f1_1_boot_args = 'cc_huid=2 sku=SKU_FS1600_1 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303'
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": self.f1_0_boot_args},
                                                          1: {"boot_args": self.f1_1_boot_args}},
                                           skip_funeth_come_power_cycle=True,
                                           dut_index=0)

        job_inputs = fun_test.get_job_inputs()
        self.details = {
            "fs": "fs-65",
            "duration": "1m",
            "le_firewall": True,
            "interval": 5,
            "boot_new_image": True,
            "specific_app": [],
            "add_to_database": False
        }
        if job_inputs:
            if "fs" in job_inputs:
                self.details["fs"] = job_inputs["fs"]
            if "duration" in job_inputs:
                self.details["duration"] = job_inputs["duration"]
            if "le_firewall" in job_inputs:
                self.details["le_firewall"] = job_inputs["le_firewall"]
            if "interval" in job_inputs:
                self.details["interval"] = job_inputs["interval"]
            if "boot_new_image" in job_inputs:
                self.details["boot_new_image"] = job_inputs["boot_new_image"]
            if "specific_app" in job_inputs:
                self.details["specific_app"] = job_inputs["specific_app"]
            if "add_to_database" in job_inputs:
                self.details["add_to_database"] = job_inputs["add_to_database"]

        if self.details["boot_new_image"]:
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology deployed")
            self.verify_dpcsh_started()
            self.create_ec_volume(topology)
        self.clear_uart_logs()

        fun_test.log(json.dumps(self.fs, indent=4))
        fun_test.log("Details: {}, Input: {}".format(self.details, job_inputs))

        # Power files - finding the right number, so its done
        self.power_shell = fun_test.get_test_case_artifact_file_name(post_fix_name="power_shell_script_logs.txt")
        self.power_output = fun_test.get_test_case_artifact_file_name(post_fix_name="power_output_logs.txt")
        fun_test.add_auxillary_file(description="Power shell script output", filename=self.power_shell)
        fun_test.add_auxillary_file(description="FS and F1 power output", filename=self.power_output)
        self.f_power_shell = open(self.power_shell, 'w+')
        self.f_power_output = open(self.power_output, 'w+')
        self.upload_first_data = True

        # Debug memory files
        self.f1_0_debug_memory_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_memory_F1_0_logs.txt")
        self.f1_1_debug_memory_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_memory_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="debug memory dpcsh output F1_0",
                                    filename=self.f1_0_debug_memory_dpc_logs)
        fun_test.add_auxillary_file(description="debug memory dpcsh output F1_1",
                                    filename=self.f1_1_debug_memory_dpc_logs)
        self.f1_0_debug_memory_difference_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_memory_difference_F1_0_logs.txt")
        self.f1_1_debug_memory_difference_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_memory_difference_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="debug memory dpcsh output difference stats F1_0",
                                    filename=self.f1_0_debug_memory_difference_dpc_logs)
        fun_test.add_auxillary_file(description="debug memory dpcsh output difference stats F1_1",
                                    filename=self.f1_1_debug_memory_difference_dpc_logs)
        self.f_debug_memory_f1_0 = open(self.f1_0_debug_memory_dpc_logs, "w+")
        self.f_debug_memory_f1_1 = open(self.f1_1_debug_memory_dpc_logs, "w+")
        self.f_debug_memory_difference_f1_0 = open(self.f1_0_debug_memory_difference_dpc_logs, "w+")
        self.f_debug_memory_difference_f1_1 = open(self.f1_1_debug_memory_difference_dpc_logs, "w+")

        # cdu files -
        # Todo:Onkar has mailed - wait for there response
        self.f1_0_cdu_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="cdu_F1_0_logs.txt")
        self.f1_1_cdu_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="cdu_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="cdu stats F1_0", filename=self.f1_0_cdu_dpc_logs)
        fun_test.add_auxillary_file(description="cdu stats F1_1", filename=self.f1_1_cdu_dpc_logs)
        self.f_cdu_f1_0 = open(self.f1_0_cdu_dpc_logs, "w+")
        self.f_cdu_f1_1 = open(self.f1_1_cdu_dpc_logs, "w+")

        # EQM files
        self.f1_0_eqm_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="eqm_F1_0_logs.txt")
        self.f1_1_eqm_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="eqm_F1_1_logs.txt")
        self.f1_0_eqm_dif_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="eqm_F1_0_dif_logs.txt")
        self.f1_1_eqm_dif_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="eqm_F1_1_dif_logs.txt")
        fun_test.add_auxillary_file(description="EQM stats F1_0", filename=self.f1_0_eqm_dpc_logs)
        fun_test.add_auxillary_file(description="EQM stats F1_1", filename=self.f1_1_eqm_dpc_logs)
        fun_test.add_auxillary_file(description="Difference EQM stats F1_0", filename=self.f1_0_eqm_dif_logs)
        fun_test.add_auxillary_file(description="Difference EQM stats F1_1", filename=self.f1_1_eqm_dif_logs)
        self.f_eqm_f1_0 = open(self.f1_0_eqm_dpc_logs, "w+")
        self.f_eqm_f1_1 = open(self.f1_1_eqm_dpc_logs, "w+")
        self.f_eqm_dif_f1_0 = open(self.f1_0_eqm_dif_logs, "w+")
        self.f_eqm_dif_f1_1 = open(self.f1_1_eqm_dif_logs, "w+")

        # BM files
        # Todo: we wanted with respect to the speed, they have provided it for the storage
        self.f1_0_bam_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="bam_F1_0_logs.txt")
        self.f1_1_bam_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="bam_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="bam stats F1_0", filename=self.f1_0_bam_dpc_logs)
        fun_test.add_auxillary_file(description="bam stats F1_1", filename=self.f1_1_bam_dpc_logs)
        self.f_bam_f1_0 = open(self.f1_0_bam_dpc_logs, "w+")
        self.f_bam_f1_1 = open(self.f1_1_bam_dpc_logs, "w+")

        # Debug vp util
        self.f1_0_debug_vp_utils_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_vp_utils_F1_0_logs.txt")
        self.f1_1_debug_vp_utils_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="debug_vp_utils_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="Debug vp_util stats F1_0", filename=self.f1_0_debug_vp_utils_dpc_logs)
        fun_test.add_auxillary_file(description="Debug vp_util stats F1_1", filename=self.f1_1_debug_vp_utils_dpc_logs)
        self.f_debug_vp_utils_f1_0 = open(self.f1_0_debug_vp_utils_dpc_logs, "w+")
        self.f_debug_vp_utils_f1_1 = open(self.f1_1_debug_vp_utils_dpc_logs, "w+")

        # Le firewall
        self.f1_0_le_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="le_F1_0_logs.txt")
        self.f1_1_le_dpc_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="le_F1_1_logs.txt")
        self.f1_0_le_dif_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="le_F1_0_dif_logs.txt")
        self.f1_1_le_dif_logs = fun_test.get_test_case_artifact_file_name(
            post_fix_name="le_F1_1_dif_logs.txt")
        fun_test.add_auxillary_file(description="LE stats F1_0", filename=self.f1_0_le_dpc_logs)
        fun_test.add_auxillary_file(description="LE stats F1_1", filename=self.f1_1_le_dpc_logs)
        fun_test.add_auxillary_file(description="Calculated LE stats F1_0", filename=self.f1_0_le_dif_logs)
        fun_test.add_auxillary_file(description="Calculated LE stats F1_1", filename=self.f1_1_le_dif_logs)
        self.f_le_f1_0 = open(self.f1_0_le_dpc_logs, "w+")
        self.f_le_f1_1 = open(self.f1_1_le_dpc_logs, "w+")
        self.f_le_dif_f1_0 = open(self.f1_0_le_dif_logs, "w+")
        self.f_le_dif_f1_1 = open(self.f1_1_le_dif_logs, "w+")

        # F1 die temperature
        self.die_temperature = fun_test.get_test_case_artifact_file_name(post_fix_name="fs_die_temperature_logs.txt")
        fun_test.add_auxillary_file(description="FS die temperature", filename=self.die_temperature)
        self.f_die_temperature = open(self.die_temperature, 'w+')

        # TODO: Clear the Uart log files if the new image is not built

        # Traffic
        self.methods = {"crypto": crypto, "zip": zip_deflate, "rcnvme": rcnvme, "fio": fio}

        if self.details["duration"] == "1m":
            self.test_duration = 60
        elif self.details["duration"] == "1h":
            self.test_duration = 3600
        elif self.details["duration"] == "3h":
            self.test_duration = 10800

    def run(self):
        ############## Before traffic #####################
        # self.initial_debug_memory_stats = self.get_debug_memory_stats_initially(self.f_debug_memory_f1_0,
        #                                                                         self.f_debug_memory_f1_1)
        self.capture_data(count=3, heading="Before starting traffic")

        fun_test.test_assert(True, "Initial debug stats is saved")

        ############# Starting Traffic ################
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        come_handle.command("pwd")

        app_params = get_params_for_time.get(self.test_duration)
        if self.details["specific_app"]:
            app_params = get_params_for_time.get(self.test_duration, specific_field=self.details["specific_app"])
        fun_test.log("App parameters: {}".format(app_params))

        if self.details["le_firewall"]:
            le_firewall(self.test_duration, self.details["boot_new_image"])

        for app, parameters in app_params.iteritems():
            parameters["f1"] = 0
            result = self.methods[app](come_handle, **parameters)
            fun_test.test_assert(result, "{} traffic started on F1_0".format(app))
            parameters["f1"] = 1
            result = self.methods[app](come_handle, **parameters)
            fun_test.test_assert(result, "{} traffic started on F1_1".format(app))

        ################ During traffic ##################
        count = int(self.test_duration / self.details["interval"])
        heading = "During traffic"
        fun_test.log("Capturing the data {}".format(heading))
        self.capture_data(count=count, heading=heading)

        #################### After the traffic ############
        if self.details["le_firewall"]:
            kill_le_firewall()
        count = 3
        heading = "After the traffic"
        fun_test.log("Capturing the data {}".format(heading))
        self.capture_data(count=count, heading=heading)

        self.f_power_shell.close()
        self.f_power_output.close()
        self.f_debug_memory_f1_0.close()
        self.f_debug_memory_f1_1.close()
        self.f_cdu_f1_0.close()
        self.f_cdu_f1_1.close()

    def cleanup(self):
        if not self.details["boot_new_image"]:
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

    ############## power #############
    def power_output_to_file(self, count, f_power_shell, f_power_output, heading):
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
            file_helper.add_data(f_power_shell, print_data, heading=heading)
            print_data = {"output": cal_output, "time": time_now}
            file_helper.add_data(f_power_output, print_data, heading=heading)
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
            if heading == "During traffic" and self.upload_first_data and self.details["add_to_database"]:
                self.upload_first_data = False
                print ("Result pro_data: {}".format(pro_data))
                self.add_to_data_base(pro_data)
        bmc_handle.destroy()

    ###########  debug memory ########
    def dpcsh_debug_memory(self, f1, file_handler, file_difference, count, heading, find_difference=True):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        dpcsh_output_list = []
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_memory(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            if find_difference:
                differnce_data_set = {}
                difference_output = debug_memory_calculation.debug_difference(self.initial_debug_memory_stats,
                                                                              one_dataset,
                                                                              f1=f1)
                differnce_data_set["output"] = difference_output
                differnce_data_set["time"] = datetime.datetime.now()
                differnce_data_set["time_difference"] = difference_output["time_difference"]
                file_helper.add_data(file_difference, differnce_data_set, heading=heading)

            dpcsh_output_list.append(one_dataset)
            if self.details["interval"] > 1:
                interval = self.details["interval"] - 1
            else:
                interval = self.details["interval"]
            fun_test.sleep("before next iteration", seconds=interval)
            file_helper.add_data(file_handler, one_dataset, heading=heading)
        come_handle.destroy()

    ############# CDU ########
    def cdu_stats(self, f1, count, file_cdu, heading):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.cdu(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
            file_helper.add_data(file_cdu, one_dataset, heading=heading)
        come_handle.destroy()

    ############# EQM ################
    def eqm_stats(self, f1, count, file_eqm, file_eqm_dif, heading):
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
            file_helper.add_data(file_eqm, one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.eqm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(file_eqm, one_dataset, heading=heading)
            difference_dict = stats_calculation.dict_difference(one_dataset, "eqm")
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            file_helper.add_data(file_eqm_dif, one_dataset, heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()

    ############# LE Firewall #############
    def le_stats(self, f1, count, file_le, file_le_dif, heading):
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
            file_helper.add_data(file_le, one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.le(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            file_helper.add_data(file_le, one_dataset, heading=heading)

            div_by_peek_value = stats_calculation.dict_difference(one_dataset, "le")
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = div_by_peek_value
            file_helper.add_data(file_le_dif, one_dataset, heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()

    ############# BAM ################
    def bam_stats(self, f1, count, file_bm, heading):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.bam(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
            file_helper.add_data(file_bm, one_dataset, heading=heading)
        come_handle.destroy()

    ############### debug vp_utils #######
    def debug_vp_utils(self, f1, count, file_debug, heading):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_vp_utils(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
            file_helper.add_data(file_debug, one_dataset, heading=heading)
        come_handle.destroy()

    ############ Die temperature #########
    def die_temperature_func(self, count, f_die_temperature, heading):
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
            file_helper.add_data(f_die_temperature, print_data, heading=heading)
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
        bmc_handle.destroy()

    ###########

    def get_debug_memory_stats_initially(self, f_debug_memory_f1_0, f_debug_memory_f1_1):
        result = {}
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        heading = "Initial stats"
        for f1 in [0, 1]:
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

    def capture_data(self, count, heading):
        # # power stats
        # thread_id_power = fun_test.execute_thread_after(func=self.power_output_to_file,
        #                                                 time_in_seconds=1,
        #                                                 count=count,
        #                                                 f_power_shell=self.f_power_shell,
        #                                                 f_power_output=self.f_power_output,
        #                                                 heading=heading)
        #
        # # Debug memory F1_0
        #
        # fun_test.test_assert(True, "Started capturing the power logs {}".format(heading))
        # thread_id_debug_memory_f1_0 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
        #                                                             time_in_seconds=2,
        #                                                             f1=0,
        #                                                             file_handler=self.f_debug_memory_f1_0,
        #                                                             file_difference=self.f_debug_memory_difference_f1_0,
        #                                                             count=count,
        #                                                             heading=heading)
        #
        # fun_test.test_assert(True, "Started capturing the debug memory logs {} on F1_0".format(heading))
        # # Debug memory F1_1
        # thread_id_debug_memory_f1_1 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
        #                                                             time_in_seconds=3,
        #                                                             f1=1,
        #                                                             file_handler=self.f_debug_memory_f1_1,
        #                                                             file_difference=self.f_debug_memory_difference_f1_1,
        #                                                             count=count,
        #                                                             heading=heading)
        # fun_test.test_assert(True, "Started capturing the debug memory logs {} on F1_1".format(heading))
        #
        # # CDU stats
        # thread_id_cdu_f1_0 = fun_test.execute_thread_after(func=self.cdu_stats,
        #                                                    time_in_seconds=4,
        #                                                    count=count,
        #                                                    f1=0,
        #                                                    file_cdu=self.f_cdu_f1_0,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/cdu logs {} on F1_0".format(heading))
        #
        # thread_id_cdu_f1_1 = fun_test.execute_thread_after(func=self.cdu_stats,
        #                                                    time_in_seconds=5,
        #                                                    count=count,
        #                                                    f1=1,
        #                                                    file_cdu=self.f_cdu_f1_1,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/cdu logs {} on F1_1".format(heading))
        #
        # # EQM stats
        #
        # thread_id_eqm_f1_0 = fun_test.execute_thread_after(func=self.eqm_stats,
        #                                                    time_in_seconds=6,
        #                                                    count=count,
        #                                                    f1=0,
        #                                                    file_eqm=self.f_eqm_f1_0,
        #                                                    file_eqm_dif=self.f_eqm_dif_f1_0,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/eqm logs {} on F1_0".format(heading))
        #
        # thread_id_eqm_f1_1 = fun_test.execute_thread_after(func=self.eqm_stats,
        #                                                    time_in_seconds=7,
        #                                                    count=count,
        #                                                    f1=1,
        #                                                    file_eqm=self.f_eqm_f1_1,
        #                                                    file_eqm_dif=self.f_eqm_dif_f1_1,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/eqm logs {} on F1_1".format(heading))
        #
        # LE firewall stats

        thread_id_le_f1_0 = fun_test.execute_thread_after(func=self.le_stats,
                                                          time_in_seconds=13,
                                                          count=count,
                                                          f1=0,
                                                          file_le=self.f_le_f1_0,
                                                          file_le_dif=self.f_le_dif_f1_0,
                                                          heading=heading)
        fun_test.test_assert(True, "Started capturing the peek stats/le/counters logs {} on F1_0".format(heading))

        thread_id_le_f1_1 = fun_test.execute_thread_after(func=self.le_stats,
                                                          time_in_seconds=14,
                                                          count=count,
                                                          f1=1,
                                                          file_le=self.f_le_f1_1,
                                                          file_le_dif=self.f_le_dif_f1_1,
                                                          heading=heading)
        fun_test.test_assert(True, "Started capturing the peek stats/le/counters logs {} on F1_1".format(heading))
        #
        # # BM stats
        #
        # thread_id_bam_f1_0 = fun_test.execute_thread_after(func=self.bam_stats,
        #                                                    time_in_seconds=8,
        #                                                    count=count,
        #                                                    f1=0,
        #                                                    file_bm=self.f_bam_f1_0,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/bam logs {} on F1_0".format(heading))
        #
        # thread_id_bam_f1_1 = fun_test.execute_thread_after(func=self.bam_stats,
        #                                                    time_in_seconds=9,
        #                                                    count=count,
        #                                                    f1=1,
        #                                                    file_bm=self.f_bam_f1_1,
        #                                                    heading=heading)
        # fun_test.test_assert(True, "Started capturing the peek stats/bam logs {} on F1_1".format(heading))
        #
        # # Debug vp_utils stats
        # thread_id_debug_vp_utils_f1_0 = fun_test.execute_thread_after(func=self.debug_vp_utils,
        #                                                               time_in_seconds=10,
        #                                                               count=count,
        #                                                               f1=0,
        #                                                               file_debug=self.f_debug_vp_utils_f1_0,
        #                                                               heading=heading)
        # fun_test.test_assert(True, "Started capturing the debug vp_utils logs {} on F1_0".format(heading))
        #
        # thread_id_debug_vp_utils_f1_1 = fun_test.execute_thread_after(func=self.debug_vp_utils,
        #                                                               time_in_seconds=11,
        #                                                               count=count,
        #                                                               f1=1,
        #                                                               file_debug=self.f_debug_vp_utils_f1_1,
        #                                                               heading=heading)
        # fun_test.test_assert(True, "Started capturing the debug vp_utils logs {} on F1_1".format(heading))
        #
        # # Die temperature
        #
        # thread_id_die_temp = fun_test.execute_thread_after(func=self.die_temperature_func,
        #                                                    time_in_seconds=12,
        #                                                    count=count,
        #                                                    f_die_temperature=self.f_die_temperature,
        #                                                    heading=heading)
        #
        # fun_test.join_thread(thread_id_power)
        # fun_test.join_thread(thread_id_debug_memory_f1_0)
        # fun_test.join_thread(thread_id_debug_memory_f1_1)
        # fun_test.join_thread(thread_id_cdu_f1_0)
        # fun_test.join_thread(thread_id_cdu_f1_1)
        # fun_test.join_thread(thread_id_eqm_f1_0)
        # fun_test.join_thread(thread_id_eqm_f1_1)
        # fun_test.join_thread(thread_id_bam_f1_0)
        # fun_test.join_thread(thread_id_bam_f1_1)
        # fun_test.join_thread(thread_id_debug_vp_utils_f1_0)
        # fun_test.join_thread(thread_id_debug_vp_utils_f1_1)
        # fun_test.join_thread(thread_id_die_temp)
        fun_test.join_thread(thread_id_le_f1_0)
        fun_test.join_thread(thread_id_le_f1_1)
        # fun_test.test_assert(True, "Power logs captured successfully")
        # fun_test.test_assert(True, "Debug memory on F1_0 logs captured successfully")
        # fun_test.test_assert(True, "Debug memory on F1_1 logs captured successfully")
        # fun_test.test_assert(True, "CDU logs on F1_0 captured successfully")
        # fun_test.test_assert(True, "CDU logs on F1_1 captured successfully")
        # fun_test.test_assert(True, "EQM logs on F1_0 captured successfully")
        # fun_test.test_assert(True, "EQM logs on F1_1 captured successfully")
        # fun_test.test_assert(True, "BAM logs on F1_0 captured successfully")
        # fun_test.test_assert(True, "BAM logs on F1_1 captured successfully")
        # fun_test.test_assert(True, "Debug vp_util logs on F1_0 captured successfully")
        # fun_test.test_assert(True, "Debug vp_util logs on F1_1 captured successfully")
        # fun_test.test_assert(True, "Die temperature captured successfully captured successfully")
        # fun_test.test_assert(True, "LE logs on F1_0 captured successfully")
        # fun_test.test_assert(True, "LE logs on F1_1 captured successfully")

    ##### EC vol creation
    def create_ec_volume(self, topology):
        fun_test.sleep("Getting started with creation of 4:2 EC volume", seconds=30)
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
            fs = topology.get_dut_instance(index=0)
            end_host = fs.get_come()
            index = 0
            storage_controller_0 = StorageController(target_ip=end_host.host_ip,
                                                     target_port=end_host.get_dpc_port(f1_in_use[index]))
            ctrlr_uuid = utils.generate_uuid()
            fun_test.test_assert(storage_controller_0.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                                        transport=transport,
                                                                        huid=huid[index],
                                                                        ctlid=ctlid[index],
                                                                        fnid=fnid,
                                                                        command_duration=120)['status'],
                                 message="Create Controller with UUID: {}".format(ctrlr_uuid))
            # create ec_vol
            (ec_config_status, ec_info_0) = storage_controller_0.configure_ec_volume(ec_info_0, command_timeout)

            ec_uuid = ec_info_0["attach_uuid"][0]

            fun_test.test_assert(storage_controller_0.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                  ns_id=ns_id[index],
                                                                                  vol_uuid=ec_uuid),
                                 message="Attaching EC Vol nsid: {} with uuid {} to controller".format(ns_id[index],
                                                                                                       ec_uuid))
            fetch_nvme = fetch_nvme_device(end_host, 1, size=ec_info_0["capacity"])
            fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
            fio_output = end_host.pcie_fio(filename=fetch_nvme["nvme_device"], **warm_up_fio_cmd_args)

            ##########################1

            index = 1
            storage_controller_1 = StorageController(target_ip=end_host.host_ip,
                                                     target_port=end_host.get_dpc_port(f1_in_use[index]))
            ctrlr_uuid = utils.generate_uuid()
            fun_test.test_assert(storage_controller_1.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                                        transport=transport,
                                                                        huid=huid[index],
                                                                        ctlid=ctlid[index],
                                                                        fnid=fnid,
                                                                        command_duration=120)['status'],
                                 message="Create Controller with UUID: {}".format(ctrlr_uuid))
            # create ec_vol
            (ec_config_status, ec_info_1) = storage_controller_1.configure_ec_volume(ec_info_1, command_timeout)

            ec_uuid = ec_info_1["attach_uuid"][0]

            fun_test.test_assert(storage_controller_1.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid,
                                                                                  ns_id=ns_id[index],
                                                                                  vol_uuid=ec_uuid),
                                 message="Attaching EC Vol nsid: {} with uuid {} to controller".format(ns_id[index],
                                                                                                       ec_uuid))
            fetch_nvme = fetch_nvme_device(end_host, 1, size=ec_info_1["capacity"])
            fun_test.test_assert(fetch_nvme['status'], message="Check: nvme device visible on end host")
            fio_output = end_host.pcie_fio(filename=fetch_nvme["nvme_device"], **warm_up_fio_cmd_args)
            result = True

        except Exception as ex:
            fun_test.critical(ex)
        fun_test.sleep("for fio to settle", seconds=30)
        fun_test.test_assert(result, "Created 4:2 EC volume")

    def verify_dpcsh_started(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        # out = come_handle.command("cd $WORKSPACE/FunSDK/bin/Linux")
        # if "No such file" in out or "not found" in out:
        come_handle.enter_sudo()
        come_handle.command("cd /scratch/FunSDK/bin/Linux")
        come_handle.command(
            "./dpcsh --pcie_nvme_sock=/dev/nvme0 --nvme_cmd_timeout=600000 --tcp_proxy=40220 &> /tmp/f1_0_dpc.txt &")
        come_handle.command(
            "./dpcsh --pcie_nvme_sock=/dev/nvme1 --nvme_cmd_timeout=600000 --tcp_proxy=40221 &> /tmp/f1_1_dpc.txt &")
        come_handle.exit_sudo()

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


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
