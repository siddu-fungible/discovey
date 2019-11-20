from lib.host.linux import Linux
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
from collections import deque
from elasticsearch import helpers
from elasticsearch import Elasticsearch
import dpcsh_nocli

# Environment: --environment={\"test_bed_type\":\"fs-65\",\"tftp_image_path\":\"ranga/funos-f1_ranga.stripped.gz\"} --inputs={\"boot_new_image\":true,\"le_firewall\":true,\"collect_stats\":[\"\"],\"ec_vol\":true}
# inputs: {"run_le_firewall":false,"specific_apps":["ZIP"],"add_to_database":true,"collect_stats":["POWER","DEBUG_MEMORY","LE"],"end_sleep":30}
# --environment={\"test_bed_type\":\"fs-65\",\"tftp_image_path\":\"ranga/funos-f1_onkar.stripped.gz\"} --inputs={\"boot_new_image\":false,\"le_firewall\":false,\"collect_stats\":[\"DEBUG_VP_UTIL\",\"POWER\"],\"ec_vol\":false,\"specific_apps\":[\"crypto\"],\"disable_f1_index\":0}

POWER = "POWER"
DIE_TEMPERATURE = "DIE_TEMPERATURE"
DEBUG_MEMORY = "DEBUG_MEMORY"
CDU = "CDU"
EQM = "EQM"
BAM = "BAM"
DEBUG_VP_UTIL = "DEBUG_VP_UTIL"
HBM = "HBM"
EXECUTE_LEAKS = "EXECUTE_LEAKS"
PC_DMA = "PC_DMA"
DDR = "DDR"
# APPS
RCNVME = "rcnvme"
FIO = "fio"
CRYPTO = "crypto"
ZIP = "zip"
LE = "le"
BUSY_LOOP = "busy_loop"
MEMCPY = "memcpy"


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        if self.boot_new_image:
            self.boot_fs()
        self.verify_dpcsh_started()
        if not self.boot_new_image:
            self.clear_uart_logs()
        if self.ec_vol:
            self.create_4_et_2_ec_volume()
        fun_test.shared_variables["run_on_f1"] = self.run_on_f1
        fun_test.shared_variables["fs"] = self.fs
        self.come_handle.destroy()

    def cleanup(self):
        fun_test.log("Script-level cleanup")

    def verify_dpcsh_started(self):
        for f1 in self.run_on_f1:
            fun_test.log("Verifying if the DPCSH has started on F1 {}".format(f1))
            dpcsh_pid = self.come_handle.get_process_id_by_pattern("/nvme{}".format(f1))
            if not dpcsh_pid:
                self.come_handle.enter_sudo()
                self.come_handle.command("cd /scratch/FunSDK/bin/Linux")
                self.come_handle.command(
                    "./dpcsh --pcie_nvme_sock=/dev/nvme{f1} --nvme_cmd_timeout=600000"
                    " --tcp_proxy=4222{f1} &> /tmp/f1_{f1}_dpc.txt &".format(f1=f1))
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
                if index == 0:
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

    def initialize_json_data(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Input: {}".format(job_inputs))
        if job_inputs:
            if "disable_f1_index" in job_inputs:
                self.disable_f1_index = job_inputs["disable_f1_index"]
            if "boot_new_image" in job_inputs:
                self.boot_new_image = job_inputs["boot_new_image"]
            if "ec_vol" in job_inputs:
                self.ec_vol = job_inputs["ec_vol"]
            if "add_boot_arg" in job_inputs:
                self.add_boot_arg = job_inputs["add_boot_arg"]
                self.add_boot_arg = " --" + self.add_boot_arg

    def initialize_variables(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)
        fun_test.log(json.dumps(self.fs, indent=4))
        if self.disable_f1_index == 0:
            self.run_on_f1 = [1]
        elif self.disable_f1_index == 1:
            self.run_on_f1 = [0]
        else:
            self.run_on_f1 = [0, 1]

        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])

    def boot_fs(self):
        f1_0_boot_args = 'cc_huid=3 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303%s' % (
            self.add_boot_arg)
        f1_1_boot_args = 'cc_huid=2 app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303%s' % (
            self.add_boot_arg)

        topology_helper = TopologyHelper()
        if self.disable_f1_index == 0 or self.disable_f1_index == 1:
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}},
                                               skip_funeth_come_power_cycle=True,
                                               dut_index=0,
                                               disable_f1_index=self.disable_f1_index)
        else:
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}},
                                               skip_funeth_come_power_cycle=True,
                                               dut_index=0)

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.create_files_based_on_the_stats()
        self.intialise_handles()

    def run(self):
        self.initial_stats()
        self.collect_the_stats(count=3, heading="Before starting traffic")
        self.run_the_traffic()
        count = int(self.duration / 5)
        # count = 6
        self.collect_the_stats(count=count, heading="During traffic")
        self.stop_traffic()
        fun_test.sleep("To traffic to stop", seconds=10)
        self.collect_the_stats(count=3, heading="After traffic")
        self.come_handle.destroy()

    def func_not_found(self):
        print "Function not found"

    def collect_the_stats(self, count, heading):
        # power stats
        # function name standard format: func_'stats_name'
        thread_map = {}
        thread_count = 0
        time_in_seconds = 1
        for system in self.stats_info:
            if system == "files":
                continue
            for stat_name, value in self.stats_info[system].iteritems():
                if value.get("disable", False):
                    fun_test.log("stat: {} has been disabled".format(stat_name))
                    continue
                func_name = "func_{}".format(stat_name.lower())
                func_def = getattr(self, func_name, self.func_not_found)
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
                thread_count += 1
                time_in_seconds += 1
                if time_in_seconds > 10:
                    time_in_seconds = 1
                fun_test.test_assert(True, "Started capturing the {} stats {}".format(stat_name, heading))

        for i in range(thread_count):
            fun_test.join_thread(thread_map[i])

    ############# EQM ################
    def func_eqm(self, f1, count, heading):
        stat_name = EQM
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
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)

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
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

        come_handle.destroy()

    ############# CDU ################
    def func_cdu(self, f1, count, heading):
        stat_name = CDU
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
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)
            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
        come_handle.destroy()

    ####### PC DMA #########
    def func_pc_dma(self, count, heading, f1):
        stat_name = PC_DMA
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
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                 heading=heading)
            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
        come_handle.destroy()

    ############# BAM ################
    def func_bam(self, f1, count, heading):
        stat_name = BAM
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
        stat_name = DEBUG_VP_UTIL
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        for i in range(count):
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_vp_utils(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            time_taken = 0
            if dpcsh_output:
                file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
                cal_dpc_out = stats_calculation.filter_dict(one_dataset, stat_name)
                one_dataset["output"] = cal_dpc_out
                file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                     heading=heading)
                if self.stats_info["come"][stat_name].get("upload_to_es", False):
                    dpcsh_data = self.simplify_debug_vp_util(dpcsh_output)
                    time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)
            fun_test.sleep("Before next iteration", seconds=(5 - time_taken))

        come_handle.destroy()

    ########### HBM ##################
    def func_hbm(self, f1, count, heading):
        stat_name = HBM
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
        stat_name = DDR
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
    def func_execute_leaks(self, f1, count, heading):
        stat_name = EXECUTE_LEAKS
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
        stat_name = POWER
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
            time_taken = 0
            if self.stats_info["bmc"][stat_name].get("upload_to_es", False):
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=pro_data, stat_name=stat_name)
            fun_test.sleep("before next iteration", seconds=5-time_taken)
            if heading == "During traffic" and self.add_to_database:
                self.add_to_database = False
                print ("Result : {}".format(pro_data))
                self.add_to_data_base(pro_data)
                fun_test.log("Data added to the database, Data: {}".format(pro_data))
        bmc_handle.destroy()

    ############ Die temperature #########
    def func_die_temperature(self, count, heading):
        stat_name = DIE_TEMPERATURE
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
        stat_name = DEBUG_MEMORY
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
            difference_output = debug_memory_calculation.debug_difference(self.initial_debug_memory_stats, one_dataset,
                                                                          f1=f1)
            differnce_data_set["output"] = difference_output
            differnce_data_set["time"] = datetime.datetime.now()
            differnce_data_set["time_difference"] = difference_output["time_difference"]
            file_helper.add_data(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), differnce_data_set,
                                 heading=heading)

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
                    " --tcp_proxy=4222{f1} &> /tmp/f1_{f1}_dpc.txt &".format(f1=f1))
                self.come_handle.exit_sudo()
                fun_test.log("Started DPCSH on F1 {}".format(f1))
            else:
                fun_test.log("Dpcsh is already running for F1 {}".format(f1))
        fun_test.test_assert(True, "DPCSH running")

    def cleanup(self):
        self.test_end_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=60)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        self.add_the_links()
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

    def add_the_links(self):
        for system in self.stats_info:
            if system == "files":
                continue
            for stat_name, value in self.stats_info[system].iteritems():
                if value.get("disable", False) or (not value.get("upload_to_es", True)):
                    fun_test.log("stat: {} has been disabled".format(stat_name))
                    continue

                if stat_name == DEBUG_VP_UTIL:
                    href = "http://10.1.20.52:5601/app/kibana#/dashboard/a37ce420-9190-11e9-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
                        self.test_start_time, self.test_end_time)
                    checkpoint = '<a href="{}" target="_blank">ELK {} stats</a>'.format(href, stat_name)
                    fun_test.add_checkpoint(checkpoint=checkpoint)
                elif stat_name == POWER:
                    href = "http://10.1.20.52:5601/app/kibana#/dashboard/240d54d0-9bff-11e9-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
                        self.test_start_time, self.test_end_time)
                    checkpoint = '<a href="{}" target="_blank">ELK {} stats</a>'.format(href, stat_name)
                    fun_test.add_checkpoint(checkpoint=checkpoint)
        href = "http://10.1.20.52:5601/app/kibana#/dashboard/8e6e8330-0a9a-11ea-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
            self.test_start_time, self.test_end_time)
        checkpoint = '<a href="{}" target="_blank">ELK Overall dashboard</a>'.format(href, stat_name)
        fun_test.add_checkpoint(checkpoint=checkpoint)




    def start_threaded_apps(self):
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
                    func=getattr(self, app, self.func_not_found),
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
        app = BUSY_LOOP
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        track_app = fun_test.shared_variables["{}_{}".format(app, f1)]
        while track_app:
            dpcsh_out = dpcsh_commands.busy_loop(come_handle, f1)
            track_app = fun_test.shared_variables["{}_{}".format(app, f1)]
            fun_test.sleep("Before next iteration app: {}".format(app))

    def memcpy_1MB(self, f1):
        app = MEMCPY
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
        while track_app:
            dpcsh_out = dpcsh_commands.memcpy_1MB(come_handle, f1)
            track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
            fun_test.sleep("Before next iteration app: {}".format(app))

    def start_fio_traffic(self, percentage=100):
        fio_thread_map = {}
        fio_capacity_map = {"f1_0": 26843545600, "f1_1": 32212254720}
        fio_data = self.get_parameters_for(FIO, percentage)
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
            fun_test.test_assert(True, "FIO successfully completed on f1 : {}".format(f1))
            try:
                fun_test.sleep("Generating fio output")
                output = fun_test.shared_variables["fio_output_f1_{}".format(f1)]
                one_dataset["time"] = datetime.datetime.now()
                one_dataset["output"] = output
                file_helper.add_data(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset)
            except Exception as ex:
                fun_test.log(ex)

    def func_fio(self, come_handle, filename, f1, **params):
        try:
            fio_output = come_handle.pcie_fio(timeout=params["runtime"] + 100,
                                              filename=filename,
                                              **params)
        except Exception as ex:
            fun_test.critical(ex)
        fun_test.shared_variables["fio_output_f1_{}".format(f1)] = fio_output

    def upload_dpcsh_data_to_elk(self, dpcsh_data, stat_name, f1=None):
        time_taken = 0
        data_dict = self.add_basics_req_elk(dpcsh_data, f1=f1)
        if data_dict:
            fun_test.log("Uploading data for command : {}".format(stat_name))
            index = self.get_index(stat_name)
            doctype = self.doc_type(stat_name)
            time_taken = self.upload_bulk(index, doctype, data_dict)
        return time_taken

    def simplify_debug_vp_util(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for cluster in range(8):
                for core in range(6):
                    for vp in range(4):
                        try:
                            value = dpcsh_data["CCV{}.{}.{}".format(cluster, core, vp)]
                            one_data_set = {"core": core,
                                            "cluster": cluster,
                                            "vp": vp,
                                            "value": value
                                            }
                            # print(one_data_set)
                            result.append(one_data_set)
                        except:
                            print ("Data error")
        return result

    def add_basics_req_elk(self, dpcsh_data, f1, time_stamp=True, system_name="fs-65"):
        utc_time = datetime.datetime.utcnow()
        time_strf = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        if type(dpcsh_data) is not list:
            dpcsh_data = [dpcsh_data]
        for each_data_set in dpcsh_data:
            if time_stamp:
                each_data_set["Time"] = time_strf
            if f1:
                each_data_set["f1"] = f1
            each_data_set["system_name"] = self.fs['name']
        return dpcsh_data

    def upload_bulk(self, index, doctype, data_list):
        res = False
        if data_list:
            print("Uploading bulk data for index: {} data: {} count : {}".format(index, data_list[0], len(data_list)))
            actions = [
                {
                    "_index": index,
                    "_type": doctype,
                    "_source": each_data
                }
                for each_data in data_list
            ]
            start = time.time()
            res = deque(helpers.parallel_bulk(self.es, actions))
            end = time.time()
            time_taken = end - start
            print("Data uploaded for index: {} to es: {} time taken: {} ".format(index, self.es, time_taken))
        else:
            print("NO data present to upload")
        return time_taken

    def get_index(self, cmd):
        if cmd == "peek stats/resource/bam":
            index = "cmd_peek_stats_resource_bam"
        elif cmd == "peek storage/devices/nvme":
            index = "cmd_storage_device_nvme"
        elif cmd == "DEBUG_VP_UTIL":
            index = "cmd_debug_vp_utils"
        elif cmd == "peek stats/crypto":
            index = "cmds_stats_crypto"
        elif "storage/devices/nvme" in cmd:
            index = "cmd_storage_device_nvme"
        elif cmd == POWER:
            index = "cmd_power"
        else:
            sec_part = cmd.split(' ')[1]
            index = "cmd_" + sec_part.replace('/', '_')
        return index

    def doc_type(self, stat_name):
        if stat_name == "DEBUG_VP_UTIL":
            doctype = "ccv_data"
        elif stat_name == "peek stats/resource/bam":
            doctype = "resource_bam"
        elif "storage/devices/nvme" in stat_name:
            doctype = "storage_ssd_iops"
        elif stat_name == POWER:
            doctype = "power_stats"

        return doctype

    def create_files_based_on_the_stats(self):
        # Create the files
        self.stats_info = {}
        # post_fix_name: "{calculated_}{app_name}_OUTPUT"
        # post_fix_name: "{calculated_}{app_name}_DPCSH_OUTPUT_F1_{f1}_logs.txt"
        # description : "{calculated_}_{app_name}_DPCSH_OUTPUT_F1_{f1}"
        self.stats_info["bmc"] = {POWER: {"calculated": True, "upload_to_es": True},
                                  DIE_TEMPERATURE: {"calculated": False, "disable": True}}
        self.stats_info["come"] = {DEBUG_MEMORY: {}, CDU: {}, EQM: {},
                                   BAM: {"calculated": False, "disable": True}, DEBUG_VP_UTIL: {"upload_to_es": True}, "LE": {},
                                   HBM: {"calculated": True},
                                   EXECUTE_LEAKS: {"calculated": False}, PC_DMA: {"calculated": True},
                                   DDR: {"calculated": True}}
        self.stats_info["files"] = {"fio": {"calculated": False}}

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
                        globals()[
                            "{}{}_OUTPUT".format(calculated, stat_name)] = fun_test.get_test_case_artifact_file_name(
                            post_fix_name="{}{}_OUTPUT_logs.txt".format(calculated, stat_name))
                        fun_test.add_auxillary_file(description="{}{}_OUTPUT".format(calculated.upper(), stat_name),
                                                    filename=globals()["{}{}_OUTPUT".format(calculated, stat_name)])
                        setattr(self, "f_{}{}".format(calculated, stat_name),
                                open(globals()["{}{}_OUTPUT".format(calculated, stat_name)], "w+"))
                    elif system == "come":
                        for f1 in self.run_on_f1:
                            globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name,
                                                                       f1)] = fun_test.get_test_case_artifact_file_name(
                                post_fix_name="{}{}_DPCSH_OUTPUT_F1_{}_logs.txt".format(calculated, stat_name, f1))
                            fun_test.add_auxillary_file(
                                description="{}{}_DPCSH_OUTPUT_F1_{}".format(calculated.upper(), stat_name, f1),
                                filename=globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name, f1)])
                            setattr(self, "f_{}{}_f1_{}".format(calculated, stat_name, f1),
                                    open(globals()["{}{}_DPCSH_OUTPUT_F1_{}".format(calculated, stat_name, f1)], "w+"))
                    elif system == "files":
                        for f1 in self.run_on_f1:
                            globals()[
                                "{}_OUTPUT_F1_{}".format(stat_name, f1)] = fun_test.get_test_case_artifact_file_name(
                                post_fix_name="{}_OUTPUT_F1_{}_logs.txt".format(stat_name, f1))
                            fun_test.add_auxillary_file(description="{}_OUTPUT_F1_{}".format(stat_name, f1),
                                                        filename=globals()["{}_OUTPUT_F1_{}".format(stat_name, f1)])
                            setattr(self, "f_{}_f1_{}".format(stat_name, f1),
                                    open(globals()["{}_OUTPUT_F1_{}".format(stat_name, f1)], "w+"))

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        if job_inputs:
            if "traffic_profile" in job_inputs:
                self.traffic_profile = job_inputs["traffic_profile"]
            if "add_to_database" in job_inputs:
                self.add_to_database = job_inputs["add_to_database"]
            if "duration" in job_inputs:
                self.duration = job_inputs["duration"]
            if "collect_stats" in job_inputs:
                self.collect_stats = job_inputs["collect_stats"]
            if "disable_stats" in job_inputs:
                self.disable_stats = job_inputs["disable_stats"]
            if "boot_new_image" in job_inputs:
                self.boot_new_image = job_inputs["boot_new_image"]
            if "end_sleep" in job_inputs:
                self.end_sleep = job_inputs["end_sleep"]
            if "elk_ip" in job_inputs:
                self.elasticsearch_config["ip"] = job_inputs["ip"]

    def initialize_variables(self):
        self.test_start_time = (datetime.datetime.utcnow() - datetime.timedelta(seconds=60)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        self.run_on_f1 = fun_test.shared_variables["run_on_f1"]
        self.fs = fun_test.shared_variables["fs"]
        self.es = Elasticsearch(
            [{'host': '%s' % self.elasticsearch_config["ip"], 'port': '%s' % self.elasticsearch_config["port"]}])
        self.busy_loop_thread_map = {}
        self.memcpy_loop_thread_map = {}

    def initialize_json_data(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

    def crypto(self, come_handle, vp_iters=500000, src='ddr', dst='ddr', f1=0, nvps=48):
        result = False
        try:
            json_data = {'src': src, 'dst': dst, 'vp_iters': vp_iters, 'cr_test_mute': True, "nvps": nvps}
            cmd = "async crypto_raw_speed %s" % json_data
            dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
            result = True
        except Exception as ex:
            fun_test.critical(ex)
        return result

    def zip_deflate(self, come_handle, compress=True, nflows=7680, niterations=100, max_effort=0, f1=0, npcs=None):
        result = False
        try:
            json_data = {"niterations": niterations,
                         "nflows": nflows,
                         "max_effort": max_effort,
                         }
            if npcs:
                json_data['npcs'] = npcs
            cmd = "async deflate_perf_multi %s" % json_data
            # cmd = "async deflate_perf_multi"
            print (cmd)
            dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
            result = True
        except Exception as ex:
            fun_test.critical(ex)
        return result

    def rcnvme(self, come_handle,
               all_ctrlrs='true',
               duration=60,
               qdepth=12,
               nthreads=12,
               test_type='read_only',
               hbm='true',
               prealloc='true',
               iosize=4096,
               random='true',
               f1=0):
        result = False
        try:
            json_data = '"all_ctrlrs" : {}, "qdepth": {}, "nthreads" : {},"test_type":{},' \
                        '  "hbm" : {},  "prealloc":{}, "iosize":{}, "random": {}, "duration" : {}'.format(all_ctrlrs,
                                                                                                          qdepth,
                                                                                                          nthreads,
                                                                                                          test_type,
                                                                                                          hbm,
                                                                                                          prealloc,
                                                                                                          iosize,
                                                                                                          random,
                                                                                                          duration)

            cmd = 'async rcnvme_test {%s}' % json_data
            dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)
            result = True
        except Exception as ex:
            fun_test.critical(ex)
        return result

    def intialise_handles(self):
        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])

    def initial_stats(self):
        if not self.stats_info["come"]["DEBUG_MEMORY"].get("disable", True):
            self.initial_debug_memory_stats = self.get_debug_memory_stats_initially(self.f_DEBUG_MEMORY_f1_0,
                                                                                    self.f_DEBUG_MEMORY_f1_1)

    def run_the_traffic(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])

        if LE in self.traffic_profile:
            self.restart_dpcsh()
            self.start_le_firewall(self.duration, self.boot_new_image)

        if FIO in self.traffic_profile:
            self.fio_thread_map = self.start_fio_traffic(percentage=100)

        for f1 in self.run_on_f1:
            if RCNVME in self.traffic_profile:
                self.start_rcnvme_traffic(come_handle, f1, 70)

            if CRYPTO in self.traffic_profile:
                self.start_crypto_traffic(come_handle, f1, 100)

            if ZIP in self.traffic_profile:
                self.start_zip_traffic(come_handle, f1, 100)

            if BUSY_LOOP in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(BUSY_LOOP, f1)] = True
                self.busy_loop_thread_map["{}".format(f1)] = fun_test.execute_thread_after(func=self.busy_loop,
                                                                                           time_in_seconds=5,
                                                                                           f1=f1)
            if MEMCPY in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(MEMCPY, f1)] = True
                self.memcpy_loop_thread_map["{}".format(f1)] = fun_test.execute_thread_after(func=self.memcpy_1MB,
                                                                                           time_in_seconds=5,
                                                                                           f1=f1)

        come_handle.destroy()

    def start_rcnvme_traffic(self, come_handle, f1=0, percentage=100):
        get_parameters = self.get_parameters_for(RCNVME, percentage)
        self.rcnvme_app(come_handle, f1, **get_parameters)

    def rcnvme_app(self, come_handle, f1=0, all_ctrlrs=True, duration=60, qdepth=12, nthreads=12, test_type='read_only',
                   hbm=True, prealloc=True, iosize=4096, random=True, hsu_rc=True):
        json_data = {"all_ctrlrs": all_ctrlrs,
                     "qdepth": qdepth,
                     "nthreads": nthreads,
                     "test_type": test_type,
                     "hbm": hbm,
                     "prealloc": prealloc,
                     "iosize": iosize,
                     "random": random,
                     "duration": duration,
                     "hsu_rc": hsu_rc}
        cmd = 'async rcnvme_test {}'.format(json.dumps(json_data))
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)

    def start_le_firewall(self, run_time, new_image, just_kill=False):
        run_time += 400
        vm_info = {}

        for vm_number in range(2):
            vm = getattr(self, "vm_{}".format(vm_number))
            handle = Linux(host_ip=vm["host_ip"], ssh_username=vm["ssh_username"], ssh_password=vm["ssh_password"])
            vm_info[vm["name"]] = {}
            vm_info[vm["name"]]["handle"] = handle
            vm_info[vm["name"]].update(vm)

        if just_kill:
            for vm, vm_details in vm_info.iteritems():
                self.kill_le_firewall(vm_details)
            return
        f1 = 0
        for vm, vm_details in vm_info.iteritems():
            running = self.check_if_le_firewall_is_running(vm_details)
            if running:
                self.kill_le_firewall(vm_details)
                running = False
            if not running and new_image:
                tmp_run_time = 30
                cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":true, "f1": %s}' ''' % (tmp_run_time,f1)
                self.initiate_or_run_le_firewall(cmd, vm_details, f1)
                f1 += 1
                fun_test.sleep("to check if le -firewall has started on vm: {}".format(vm), seconds=10)
                running = self.check_if_le_firewall_is_running(vm_details)
                fun_test.test_assert(running, "Le initiate started on the VM: {}".format(vm))
        if new_image:
            pid_info = {}
            time_in_seconds = 5
            for vm, vm_details in vm_info.iteritems():
                pid_info[vm] = fun_test.execute_thread_after(func=self.poll_untill_le_stops,
                                                             time_in_seconds=time_in_seconds,
                                                             vm_details=vm_details)
                time_in_seconds += 1
            for vm in vm_info:
                fun_test.join_thread(pid_info[vm])
                fun_test.test_assert(True, "Le initiate completed on the VM: {}".format(vm))

        for vm, vm_details in vm_info.iteritems():
            cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":false}' ''' % run_time
            self.initiate_or_run_le_firewall(cmd, vm_details)
            fun_test.sleep("for le to start", seconds=10)
            running = self.check_if_le_firewall_is_running(vm_details)
            if running:
                fun_test.test_assert(running, "Le started on VM: {}".format(vm))

        fun_test.sleep("For Le-firewall traffic to start", seconds=200)

    def kill_le_firewall(self, vm_details):
        result = False
        try:
            pid = self.check_if_le_firewall_is_running(vm_details)
            if pid:
                vm_details["handle"].kill_process(pid, signal=9)
                fun_test.log("Process killed successfully on the VM : {}".format(vm_details["name"]))
            else:
                fun_test.log("The process is not running")
            result = True
        except Exception as ex:
            fun_test.log(ex)
        return result

    def initiate_or_run_le_firewall(self, cmd, vm_details):
        # vm_details["handle"].enter_sudo()
        vm_details["handle"].command('export WORKSPACE="{}"'.format(vm_details["WORKSPACE"]))
        vm_details["handle"].command('export PYTHONPATH="{}"'.format(vm_details["PYTHONPATH"]))
        vm_details["handle"].command("cd {}".format(vm_details["SCRIPT_PATH"]))
        vm_details["handle"].start_bg_process(cmd)
        vm_details["handle"].command("ps -ef | grep python")
        # vm_details["handle"].exit_sudo()

        # vm_details["handle"].destroy()

    def check_if_le_firewall_is_running(self, vm_detail):
        process_id = vm_detail["handle"].get_process_id_by_pattern("run_nu_transit_only.py")
        result = process_id if process_id else False
        return result

    def poll_untill_le_stops(self, vm_details):
        timer = FunTimer(max_time=1200)
        while not timer.is_expired():
            running = self.check_if_le_firewall_is_running(vm_details)
            if running:
                fun_test.log("Remaining time: {}".format(timer.remaining_time()))
                fun_test.sleep("Before next check", seconds=30)
            else:
                if timer.elapsed_time() < 100:
                    fun_test.test_assert(False, "Le firewall initiate on vm: {}".format(vm_details["name"]))
                fun_test.log("Le initiated successfully, time taken: {}".format(timer.elapsed_time()))
                break

    def reset_the_status(self, vm_detail):
        pass
        # TODO: Reset the LE-firewall traffic

    def get_parameters_for(self, app, percentage=100):
        result = False
        if app == RCNVME:
            rcnvme_run_time = 100
            perc_dict = {
                "10": {"qdepth": 4, "nthreads": 1, "duration": rcnvme_run_time},
                "20": {"qdepth": 6, "nthreads": 1, "duration": rcnvme_run_time},
                "30": {"qdepth": 4, "nthreads": 2, "duration": rcnvme_run_time},
                "40": {"qdepth": 6, "nthreads": 2, "duration": rcnvme_run_time},
                "50": {"qdepth": 8, "nthreads": 2, "duration": rcnvme_run_time},
                "60": {"qdepth": 8, "nthreads": 4, "duration": rcnvme_run_time},
                "70": {"qdepth": 12, "nthreads": 12, "duration": rcnvme_run_time},
                "100": {"qdepth": 16, "nthreads": 16, "duration": rcnvme_run_time},
            }
            result = perc_dict[str(percentage)]
        if app == FIO:
            fio_run_time = 120
            perc_dict = {
                "10": {"numjobs": 8, "iodepth": 1, "runtime": fio_run_time},
                "35": {"numjobs": 8, "iodepth": 4, "runtime": fio_run_time},
                "65": {"numjobs": 8, "iodepth": 8, "runtime": fio_run_time},
                "100": {"numjobs": 8, "iodepth": 16, "runtime": fio_run_time}
            }
            result = perc_dict[str(percentage)]

        if app == CRYPTO:
            crypto_factor = 1
            perc_dict = {
                "10": {"vp_iters": 15000000 * crypto_factor, "nvps": 3},
                "20": {"vp_iters": 15000000 * crypto_factor, "nvps": 13},
                "30": {"vp_iters": 15000000 * crypto_factor, "nvps": 17},
                "40": {"vp_iters": 15000000 * crypto_factor, "nvps": 22},
                "50": {"vp_iters": 15000000 * crypto_factor, "nvps": 25},
                "60": {"vp_iters": 15000000 * crypto_factor, "nvps": 32},
                "70": {"vp_iters": 15000000 * crypto_factor, "nvps": 45},
                "80": {"vp_iters": 10000000 * crypto_factor, "nvps": 55},
                "90": {"vp_iters": 10000000 * crypto_factor, "nvps": 70},
                "100": {"vp_iters": 5000000 * crypto_factor, "nvps": 192}
            }
            result = perc_dict[str(percentage)]
        if app == ZIP:
            zip_factor = 1
            perc_dict = {
                "10": {"nflows": 6, "niterations": 40000 * zip_factor},
                "20": {"nflows": 30, "niterations": 40000 * zip_factor},
                "30": {"nflows": 60, "niterations": 40000 * zip_factor},
                "40": {"nflows": 70, "niterations": 40000 * zip_factor},
                "50": {"nflows": 90, "niterations": 40000 * zip_factor},
                "60": {"nflows": 105, "niterations": 40000 * zip_factor},
                "70": {"nflows": 120, "niterations": 40000 * zip_factor},
                "80": {"nflows": 130, "niterations": 40000 * zip_factor},
                "90": {"nflows": 140, "niterations": 40000 * zip_factor},
                "100": {"nflows": 7680, "niterations": 500 * zip_factor}
            }
            result = perc_dict[str(percentage)]
        return result

    def start_crypto_traffic(self, come_handle, f1, percentage):
        get_parameters = self.get_parameters_for(CRYPTO, percentage)
        self.crypto_app(come_handle, f1, **get_parameters)

    def crypto_app(self, come_handle, f1, vp_iters=15000000, nvps=192, src='ddr', dst='ddr'):
        json_data = {"vp_iters": vp_iters,
                     "nvps": nvps,
                     "src": src,
                     "dst": dst}
        cmd = 'async crypto_raw_speed {}'.format(json.dumps(json_data))
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)

    def start_zip_traffic(self, come_handle, f1, percentage):
        get_parameters = self.get_parameters_for(ZIP, percentage)
        self.zip_app(come_handle, f1, **get_parameters)

    def zip_app(self, come_handle, f1, compress=True, nflows=7680, niterations=100, max_effort=0, npcs=None):
        json_data = {"niterations": niterations,
                     "nflows": nflows,
                     "max_effort": max_effort,
                     }
        if npcs:
            json_data['npcs'] = npcs
        cmd = "async deflate_perf_multi {}".format(json.dumps(json_data))
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)

    def stop_traffic(self):
        if LE in self.traffic_profile:
            self.start_le_firewall(self.duration, self.boot_new_image, True)
        for f1 in self.run_on_f1:
            if FIO in self.traffic_profile:
                one_dataset = {}
                fun_test.join_thread(self.fio_thread_map[str(f1)])
                fun_test.test_assert(True, "FIO successfully completed on f1 : {}".format(f1))
                try:
                    fun_test.sleep("Generating fio output")
                    output = fun_test.shared_variables["fio_output_f1_{}".format(f1)]
                    one_dataset["time"] = datetime.datetime.now()
                    one_dataset["output"] = output
                    file_helper.add_data(getattr(self, "f_{}_f1_{}".format(FIO, f1)), one_dataset)
                except Exception as ex:
                    fun_test.log(ex)
            if BUSY_LOOP in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(BUSY_LOOP, f1)] = False
                fun_test.join_thread(self.busy_loop_thread_map[f1])
            if MEMCPY in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(MEMCPY, f1)] = False
                fun_test.join_thread(self.memcpy_loop_thread_map[f1])


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
