from lib.host.linux import Linux
from asset.asset_manager import AssetManager
from lib.fun.fs import ComE, Bmc
import bmc_commands
import dpcsh_commands
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
from scripts.system.metrics_parser import MetricParser

# inputs: {"run_le_firewall":false,"specific_apps":["ZIP"],"add_to_database":true,"collect_stats":["POWER","DEBUG_MEMORY","LE"],"end_sleep":30}
# --environment={\"test_bed_type\":\"fs-65\",\"tftp_image_path\":\"ranga/funos-f1_onkar.stripped.gz\"}
# --environment={\"test_bed_type\":\"fs-65\",\"tftp_image_path\":\"ranga/funos-f1_onkar.stripped.gz\"} --inputs={\"boot_new_image\":false,\"collect_stats\":[\"POWER\"],\"ec_vol\":false,\"traffic_profile\":[\"rcnvme\"]}

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
APPSVALUES = "APPSVALUES"
STORAGE_IOPS = "STORAGE_IOPS"

# APPS
RCNVME = "rcnvme"
FIO_COME = "FIO_COME"
FIO_SERVER = "FIO_SERVER"
CRYPTO = "crypto"
ZIP = "zip"
LE = "le"
BUSY_LOOP = "busy_loop"
MEMCPY = "memcpy"
DMA_SPEED = "dma_speed"


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
            self.create_vol_and_attach()
            self.connect_the_volume_to_host()
        else:
            self.clear_uart_logs()

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
        # f1_0_boot_args = 'cc_huid=3 app=mdt_test,load_mods workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303%s' % (
        #     self.add_boot_arg)
        # f1_1_boot_args = 'cc_huid=2 app=mdt_test,load_mods workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303%s' % (
        #     self.add_boot_arg)
        f1_0_boot_args = 'cc_huid=3 app=mdt_test,load_mods workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats'
        f1_1_boot_args = 'cc_huid=2 app=mdt_test,load_mods workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr --sync-uart --disable-wu-watchdog --dis-stats'

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

    def create_vol_and_attach(self):
        for f1 in self.run_on_f1:
            storage_ctrl = StorageController(target_ip=self.come_handle.host_ip,
                                             target_port=self.come_handle.get_dpc_port(f1))
            storage_ctrl.ip_cfg(ip="29.1.{}.1".format(1), port=1099)
            ec_info = self.get_vol_creation_info(f1)
            command_timeout = 200
            res = storage_ctrl.configure_ec_volume(ec_info, command_timeout)
            uuid_lsv = res[1]["uuids"][0]["lsv"][0]
            ctrlr_uuid = "20000000000030{}".format(random.randint(10, 99))
            command_result = storage_ctrl.create_controller(ctrlr_uuid=ctrlr_uuid,
                                                            transport="TCP",
                                                            remote_ip="22.1.{}.1".format(1),
                                                            nqn="nqn-{}".format(f1 + 1), port=1099,
                                                            command_duration=5)
            storage_ctrl.attach_volume_to_controller(ctrlr_uuid=ctrlr_uuid, ns_id=f1+1, vol_uuid=uuid_lsv)

    def connect_the_volume_to_host(self, retry=3):
        for f1 in self.run_on_f1:
            host_handle = self.get_host_handle(f1)
            host_handle.enter_sudo()
            host_handle.command("modprobe nvme")
            host_handle.command("modprobe nvme_tcp")
            self.modify_the_ip(host_handle)
            for iter in range(retry):
                fun_test.log("Trying to connect to nvme, Iteration no: {} out of {}".format(iter + 1, retry))
                nqn = "nqn-{}".format(f1+1)
                target_ip = "29.1.{}.1".format(1)
                remote_ip = "22.1.{}.1".format(1)
                result = host_handle.nvme_connect(target_ip=target_ip,
                                                  nvme_subsystem=nqn,
                                                  nvme_io_queues=16,
                                                  retries=5,
                                                  timeout=100,
                                                  hostnqn=remote_ip)
                if result:
                    break

    def modify_the_ip(self, host_handle):
        host_handle.command("ip addr add 22.1.1.1/24 dev enp216s0")
        # mac address of :   fe:dc:ba:44:66:32
        host_handle.command("ip link set enp216s0 address fe:dc:ba:44:66:32")
        host_handle.command("ip link set enp216s0 up")
        host_handle.command("ifconfig enp216s0 up")
        host_handle.command("route add -net 29.1.1.0/24 gw 22.1.1.2")
        host_handle.command("arp -s 22.1.1.2 00:de:ad:be:ef:00")


    def get_vol_creation_info(self, f1):
        ec_info = {}
        if f1 == 0:
            ec_info = {
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
        elif f1 == 1:
            ec_info = {
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
        return ec_info

    def get_host_handle(self, f1):
        self.vm_info = self.fio_vm_details[str(f1)]
        handle = Linux(host_ip=self.vm_info["host_ip"],
                       ssh_username=self.vm_info["ssh_username"],
                       ssh_password=self.vm_info["ssh_password"])
        return handle


class FrsTestCase(FunTestCase):
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
        self.start_collecting_stats(heading="Before starting traffic")
        self.stop_collection_of_stats_for_count(count=1)
        self.run_the_traffic()
        self.start_collecting_stats(heading="During traffic")
        fun_test.sleep("For the apps to stop", seconds=self.duration + 20)
        # timer = FunTimer(max_time=1200)
        # apps_are_done = False
        # while not timer.is_expired():
        #     apps_are_done = self.are_apps_done(timer)
        #     if apps_are_done :
        #         break
        #     fun_test.sleep("before checking the apps status", seconds=30)
        self.stop_traffic()
        self.stop_collection_of_stats()

    def func_not_found(self):
        print "Function not found"

    def start_collecting_stats(self, heading):
        # power stats
        # function name standard format: func_'stats_name'
        self.stats_thread_map = {}
        thread_count = 0
        time_in_seconds = 5
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
                    fun_test.shared_variables["stat_{}".format(stat_name)] = {"run_status": True, "count": 0}
                    self.stats_thread_map[thread_count] = fun_test.execute_thread_after(func=func_def,
                                                                                        time_in_seconds=time_in_seconds,
                                                                                        heading=heading,
                                                                                        stat_name=stat_name)
                elif system == "come":
                    for f1 in self.run_on_f1:
                        fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)] = {"run_status": True,
                                                                                            "count": 0}
                        self.stats_thread_map[thread_count] = fun_test.execute_thread_after(func=func_def,
                                                                                            time_in_seconds=time_in_seconds,
                                                                                            heading=heading,
                                                                                            f1=f1,
                                                                                            stat_name=stat_name)
                thread_count += 1
                time_in_seconds += 1
                fun_test.test_assert(True, "Started capturing the {} stats {}".format(stat_name, heading))
        fun_test.sleep("For apps too start", seconds=time_in_seconds)

        # for i in range(thread_count):
        #     fun_test.join_thread(self.stats_thread_map[i])

    def stats_deco(func):
        def function_wrapper(self, *args, **kwargs):
            come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                               ssh_username=self.fs['come']['mgmt_ssh_username'],
                               ssh_password=self.fs['come']['mgmt_ssh_password'])
            come_handle = self.set_cmd_env_come_handle(come_handle)
            stat_name = kwargs["stat_name"]
            f1 = kwargs["f1"]
            heading = kwargs["heading"]
            kwargs["come_handle"] = come_handle
            func(self, **kwargs)
            fun_test.test_assert(True, "Stats collected for stat :{} on f1 :{} {}".format(stat_name,
                                                                                          f1,
                                                                                          heading))
            come_handle.destroy()
            return

        return function_wrapper

    def stats_deco_bmc(func):
        def function_wrapper(self, *args, **kwargs):
            bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                             ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                             ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                             set_term_settings=True,
                             disable_uart_logger=False)
            bmc_handle.set_prompt_terminator(r'# $')
            stat_name = kwargs["stat_name"]
            heading = kwargs["heading"]
            kwargs["bmc_handle"] = bmc_handle
            func(self, **kwargs)
            bmc_handle.destroy()
            fun_test.test_assert(True, "Stats collected for stat :{} {}".format(stat_name, heading))
            return

        return function_wrapper

    @stats_deco
    def func_eqm(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.eqm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.eqm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                  heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_eqm_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_le(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            one_dataset = {}
            dpcsh_output = dpcsh_commands.le(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.le(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                  heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_le_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_cdu(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker["run_status"]:
            one_dataset = {}
            dpcsh_output = dpcsh_commands.cdu(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.cdu(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                  heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_cdu_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_pc_dma(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.pc_dma(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.pc_dma(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                  heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_pc_dma_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_bam(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.bam(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            fun_test.sleep("before next iteration", seconds=self.stats_interval)
            self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1

    @stats_deco
    def func_debug_vp_util(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker["run_status"]:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_vp_utils(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            time_taken = 0
            if dpcsh_output:
                if self.upload_to_file:
                    self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
                cal_dpc_out = stats_calculation.filter_dict(one_dataset, stat_name)
                one_dataset["output"] = cal_dpc_out
                if self.upload_to_file:
                    self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                          heading=heading)
                if self.stats_info["come"][stat_name].get("upload_to_es", False):
                    # dpcsh_data = self.simplify_debug_vp_util(dpcsh_output)
                    dpcsh_data = self.simplify_debug_vp_util_core_utilisation(dpcsh_output)
                    time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name + "_PER_CLUSTER")
            fun_test.sleep("Before next iteration", seconds=self.stats_interval)

            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1

    @stats_deco
    def func_hbm(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.hbm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.hbm(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                      heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_hbm_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])

            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_ddr(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.ddr(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.ddr(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), one_dataset,
                                      heading=heading)

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_ddr_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

            # fun_test.sleep("before next iteration", seconds=self.details["interval"])
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

    @stats_deco
    def func_execute_leaks(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker["run_status"]:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.execute_leaks(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=10)

    @stats_deco_bmc
    def func_power(self, heading, stat_name, bmc_handle):
        linker = fun_test.shared_variables["stat_{}".format(stat_name)]
        while linker["run_status"]:
            linker = fun_test.shared_variables["stat_{}".format(stat_name)]
            raw_output, cal_output, pro_data = bmc_commands.power_manager(bmc_handle=bmc_handle)
            time_now = datetime.datetime.now()
            raw_data = {"output": raw_output + "\n\n" + cal_output, "time": time_now}
            print_data = {"output": cal_output, "time": time_now}

            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}".format(stat_name)), raw_data, heading=heading)
                self.add_data_to_file(getattr(self, "f_calculated_{}".format(stat_name)), print_data, heading=heading)

            time_taken = 0
            if self.stats_info["bmc"][stat_name].get("upload_to_es", False):
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=pro_data, stat_name=stat_name)

            fun_test.shared_variables["stat_{}".format(stat_name)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)
            if heading == "During traffic" and self.add_to_database:
                self.add_to_database = False
                fun_test.log("Result : {}".format(pro_data))
                self.add_to_data_base(pro_data)
                fun_test.log("Data added to the database, Data: {}".format(pro_data))


    @stats_deco_bmc
    def func_die_temperature(self, heading, stat_name, bmc_handle):
        linker = fun_test.shared_variables["stat_{}".format(stat_name)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}".format(stat_name)]
            output = bmc_commands.die_temperature(bmc_handle)
            time_now = datetime.datetime.now()
            print_data = {"output": output, "time": time_now}
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}".format(stat_name)), print_data, heading=heading)
            fun_test.sleep("before next iteration")
            fun_test.shared_variables["stat_{}".format(stat_name)]["count"] += 1

    @stats_deco
    def func_debug_memory(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        dpcsh_output_list = []
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.debug_memory(come_handle=come_handle, f1=f1)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = dpcsh_output
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset, heading=heading)

            differnce_data_set = {}
            difference_output = debug_memory_calculation.debug_difference(self.initial_debug_memory_stats, one_dataset,
                                                                          f1=f1)
            differnce_data_set["output"] = difference_output
            differnce_data_set["time"] = datetime.datetime.now()
            differnce_data_set["time_difference"] = difference_output["time_difference"]
            if self.upload_to_file:
                self.add_data_to_file(getattr(self, "f_calculated_{}_f1_{}".format(stat_name, f1)), differnce_data_set,
                                      heading=heading)

            dpcsh_output_list.append(one_dataset)
            fun_test.sleep("before next iteration", seconds=3)
            fun_test.shared_variables["stat_{}".format(stat_name)]["count"] += 1

    @stats_deco
    def func_storage_iops(self, f1, heading, stat_name, come_handle):
        linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
        while linker['run_status']:
            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
            one_dataset = {}
            dpcsh_output = dpcsh_commands.storage_iops(come_handle=come_handle, f1=f1)
            one_dataset["time1"] = datetime.datetime.now()
            one_dataset["output1"] = dpcsh_output

            fun_test.sleep("Before capturing next set of data", seconds=5)

            dpcsh_output = dpcsh_commands.storage_iops(come_handle=come_handle, f1=f1)
            one_dataset["time2"] = datetime.datetime.now()
            one_dataset["output2"] = dpcsh_output

            difference_dict = stats_calculation.dict_difference(one_dataset, stat_name)
            one_dataset["time"] = datetime.datetime.now()
            one_dataset["output"] = difference_dict

            if self.stats_info["come"][stat_name].get("upload_to_es", False):
                dpcsh_data = self.simplify_storage_iops_stats(difference_dict)
                time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)
            fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["count"] += 1
            fun_test.sleep("before next iteration", seconds=self.stats_interval)

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
            if self.upload_to_file:
                if f1 == 0:
                    self.add_data_to_file(f_debug_memory_f1_0, one_dataset, heading=heading)
                else:
                    self.add_data_to_file(f_debug_memory_f1_1, one_dataset, heading=heading)
            result["f1_{}".format(f1)] = one_dataset.copy()
        come_handle.destroy()
        return result

    def set_cmd_env_come_handle(self, come_handle):
        come_handle.enter_sudo()
        come_handle.command("cd /tmp/workspace/FunSDK/bin/Linux")
        return come_handle

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
                             disable_uart_logger=False,
                             bundle_compatible=False)
            bmc_handle.set_prompt_terminator(r'# $')
            # bmc_handle.cleanup()
            # Capture the UART logs also
            artifact_file_name_f1_0 = bmc_handle.get_uart_log_file(0)
            artifact_file_name_f1_1 = bmc_handle.get_uart_log_file(1)
            self.upload_the_values(artifact_file_name_f1_0, artifact_file_name_f1_1)
            fun_test.add_auxillary_file(description="DUT_0_fs-65_F1_0 UART Log", filename=artifact_file_name_f1_0)
            fun_test.add_auxillary_file(description="DUT_0_fs-65_F1_1 UART Log", filename=artifact_file_name_f1_1)

    def add_the_links(self):
        # Todo: Get the links for each individual app
        # for system in self.stats_info:
        #     if system == "files":
        #         continue
        #     for stat_name, value in self.stats_info[system].iteritems():
        #         if value.get("disable", False) or (not value.get("upload_to_es", True)):
        #             fun_test.log("stat: {} has been disabled".format(stat_name))
        #             continue
        #
        #         if stat_name == DEBUG_VP_UTIL:
        #             href = "http://10.1.20.52:5601/app/kibana#/dashboard/a37ce420-9190-11e9-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
        #                 self.test_start_time, self.test_end_time)
        #             checkpoint = '<a href="{}" target="_blank">ELK {} stats</a>'.format(href, stat_name)
        #             fun_test.add_checkpoint(checkpoint=checkpoint)
        #         elif stat_name == POWER:
        #             href = "http://10.1.20.52:5601/app/kibana#/dashboard/240d54d0-9bff-11e9-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
        #                 self.test_start_time, self.test_end_time)
        #             checkpoint = '<a href="{}" target="_blank">ELK {} stats</a>'.format(href, stat_name)
        #             fun_test.add_checkpoint(checkpoint=checkpoint)
        href = "http://10.1.20.52:5601/app/kibana#/dashboard/8e6e8330-0a9a-11ea-8475-15977467c007?_g=(refreshInterval:(pause:!t,value:0),time:(from:'{}',mode:absolute,to:'{}'))".format(
            self.test_start_time, self.test_end_time)
        checkpoint = '<a href="{}" target="_blank">ELK Overall dashboard</a>'.format(href)
        fun_test.add_checkpoint(checkpoint=checkpoint)

    def upload_the_values(self, artifact_file_name_f1_0, artifact_file_name_f1_1):
        for f1 in self.run_on_f1:
            if f1 == 0:
                file_name = artifact_file_name_f1_0
            else:
                file_name = artifact_file_name_f1_1
            lines = open(file_name, "r").readlines()
            if RCNVME in self.traffic_profile:
                result = MetricParser().rcnvme(lines, "", "TeraMarkRcnvmeReadWriteAllPerformance")
                if result['status']:
                    app = RCNVME
                    field = "read iops"
                    value = round(float(result["data"][1]["output_iops"] / 1000000.0), 3)
                    unit = "M iops"
                    self.apps_upload_helper(app, field, unit, value, f1)
            if CRYPTO in self.traffic_profile:
                result = MetricParser().teramark_crypto(lines, "", "F1", "TeraMarkMultiClusterCryptoPerformance")
                if result['status']:
                    app = CRYPTO
                    field = "throughput"
                    value = result["data"][0]["output_throughput"]
                    unit = result["data"][0]["output_throughput_unit"]
                    self.apps_upload_helper(app, field, unit, value, f1)

            if ZIP in self.traffic_profile:
                result = self.zip_parser(lines)
                if result['status']:
                    app = ZIP
                    field = "bandwidth"
                    value = result["data"][0]["output_bandwidth_avg"]
                    unit = result["data"][0]["output_bandwidth_avg_unit"]
                    self.apps_upload_helper(app, field, unit, value, f1)

    def zip_parser(self, lines):
        result = {}
        result["data"] = []
        result["status"] = False
        metrics = collections.OrderedDict()
        teramark_begin = False
        for line in lines:
            if "TeraMark Begin" in line:
                teramark_begin = True
            if "TeraMark End" in line:
                teramark_begin = False
            if teramark_begin:
                m = re.search(
                    r'{"Type":\s+"(?P<type>\S+)",\s+"Operation":\s+(?P<operation>\S+),\s+"Effort":\s+(?P<effort>\S+),'
                    r'.*\s+"Duration"\s+:\s+(?P<latency_json>{.*}),\s+"Throughput":\s+(?P<throughput_json>{.*})}', line)
                if m:
                    self.match_found = True
                    input_type = m.group("type")
                    input_operation = m.group("operation")
                    input_effort = int(m.group("effort"))
                    bandwidth_json = json.loads(m.group("throughput_json"))
                    output_bandwidth_avg = bandwidth_json['value']
                    output_bandwidth_avg_unit = bandwidth_json["unit"]
                    latency_json = json.loads(m.group("latency_json"))
                    output_latency_avg = latency_json['value']
                    output_latency_unit = latency_json["unit"]

                    fun_test.log("type: {}, operation: {}, effort: {}, stats {}".format(input_type, input_operation,
                                                                                        input_effort,
                                                                                        bandwidth_json))
                    metrics["input_type"] = input_type
                    metrics["input_operation"] = input_operation
                    metrics["input_effort"] = input_effort
                    metrics["output_bandwidth_avg"] = output_bandwidth_avg
                    metrics["output_bandwidth_avg_unit"] = output_bandwidth_avg_unit
                    metrics["output_latency_avg"] = output_latency_avg
                    metrics["output_latency_avg_unit"] = output_latency_unit
                    self.status = RESULTS["PASSED"]
                    result["data"].append(metrics)
                    result["status"] = True
        return result

    def apps_upload_helper(self, app, field, unit, value, f1):
        stat_name = APPSVALUES
        dpcsh_data = {"app": app,
                      "field": field,
                      "unit": unit,
                      "value": value}
        time_taken = self.upload_dpcsh_data_to_elk(dpcsh_data=dpcsh_data, f1=f1, stat_name=stat_name)

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
        come_handle = self.set_cmd_env_come_handle(come_handle)
        fun_test.test_assert(True, "Started BUSY LOOP on F1: {}".format(f1))
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
        come_handle = self.set_cmd_env_come_handle(come_handle)
        fun_test.test_assert(True, "Started MEMCPY on F1: {}".format(f1))
        while track_app:
            dpcsh_out = dpcsh_commands.memcpy_1MB(come_handle, f1)
            track_app = fun_test.shared_variables["var_{}_f1_{}".format(app, f1)]
            fun_test.sleep("Before next iteration app: {}".format(app))

    def start_fio_traffic(self, percentage=100):
        fio_thread_map = {}
        fio_capacity_map = {"f1_0": 26843545600, "f1_1": 32212254720}
        fio_data = self.get_parameters_for(FIO_COME, percentage)
        self.fio_params.update(fio_data)
        for f1 in self.run_on_f1:
            try:
                come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                   ssh_username=self.fs['come']['mgmt_ssh_username'],
                                   ssh_password=self.fs['come']['mgmt_ssh_password'])

                fetch_nvme = fetch_nvme_device(come_handle, 1, size=fio_capacity_map["f1_{}".format(f1)])
                if fetch_nvme["status"]:
                    fun_test.test_assert(True, "{} traffic started on F1_{}".format("fio", f1))
                    self.fio_params["runtime"] = self.duration
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
                self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(stat_name, f1)), one_dataset)
            except Exception as ex:
                fun_test.log(ex)

    def func_fio(self, come_handle, filename, f1, **params):
        try:
            fio_output = come_handle.pcie_fio(timeout=self.duration + 100,
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

    def simplify_debug_vp_util_core_utilisation(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for cluster in range(8):
                for core in range(6):
                    vp_sum = 0
                    for vp in range(4):
                        try:
                            value = dpcsh_data["CCV{}.{}.{}".format(cluster, core, vp)]
                            vp_sum += value
                        except:
                            print ("Data error")
                    one_data_set = {"core": core,
                                    "cluster": cluster,
                                    "value": round((vp_sum / 4), 4)
                                    }
                    # print(one_data_set)
                    result.append(one_data_set)
        return result


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

    def simplify_eqm_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for k, v in dpcsh_data.iteritems():
                one_data_set = {"field": k,
                                "value": v}
                result.append(one_data_set.copy())
        return result

    def simplify_cdu_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            cdu_cnts = dpcsh_data["cdu_cnts"]
            for k, v in cdu_cnts.iteritems():
                one_data_set = {"field": k,
                                "value": v}
                result.append(one_data_set.copy())
        return result

    def simplify_pc_dma_stats(self, dpcsh_data):
        result = []
        allow = ["lsn_bm_rd_req_cnt", "lsn_hbm_rd_req_cnt", "lsn_ddr_rd_req_cnt",
                 "ldn_bm_wr_req_cnt", "ldn_hbm_wr_req_cnt", "ldn_ddr_wr_req_cnt",
                 ]
        if dpcsh_data:
            dma_dmi_stats = dpcsh_data["dma_dmi_stats"]
            for cluster, fields in dma_dmi_stats.iteritems():
                for k, v in fields.iteritems():
                    if k in allow:
                        one_data_set = {"field": k,
                                        "value": v,
                                        "cluster": cluster}
                        result.append(one_data_set.copy())
        return result

    def simplify_hbm_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for k, v in dpcsh_data.iteritems():
                one_data_set = {"field": k,
                                "value": v}
                result.append(one_data_set.copy())
        return result

    def simplify_ddr_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for k, v in dpcsh_data.iteritems():
                one_data_set = {"field": k,
                                "value": v}
                result.append(one_data_set.copy())
        return result

    def simplify_storage_iops_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for ssd, value in dpcsh_data.iteritems():
                for k, v in value.iteritems():
                    one_data_set = {"ssd": ssd,
                                    "field": k,
                                    "value": round(v, 2)}
                    result.append(one_data_set.copy())
        return result

    def simplify_le_stats(self, dpcsh_data):
        result = []
        if dpcsh_data:
            for k, v in dpcsh_data.iteritems():
                one_data_set = {"field": k,
                                "value": v}
                result.append(one_data_set.copy())
        return result

    def add_basics_req_elk(self, dpcsh_data, f1, time_stamp=True, system_name="fs-65"):
        utc_time = datetime.datetime.utcnow()
        time_strf = utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")
        if type(dpcsh_data) is not list:
            dpcsh_data = [dpcsh_data]
        for each_data_set in dpcsh_data:
            if time_stamp:
                each_data_set["Time"] = time_strf
            if f1 != None:
                each_data_set["f1"] = "f1_{}".format(f1)
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

    def get_index(self, stat_name):
        if stat_name == DEBUG_VP_UTIL:
            index = "cmd_debug_vp_utils"
        else:
            index = "cmd_{}".format(stat_name.lower())
        return index

    def doc_type(self, stat_name):
        if stat_name == DEBUG_VP_UTIL:
            doctype = "ccv_data"
        else:
            doctype = "{}_stats".format(stat_name.lower())

        return doctype

    def create_files_based_on_the_stats(self):
        # Create the files
        self.stats_info = {}
        # post_fix_name: "{calculated_}{app_name}_OUTPUT"
        # post_fix_name: "{calculated_}{app_name}_DPCSH_OUTPUT_F1_{f1}_logs.txt"
        # description : "{calculated_}_{app_name}_DPCSH_OUTPUT_F1_{f1}"
        self.stats_info["bmc"] = {POWER: {"calculated": True, "upload_to_es": True},
                                  DIE_TEMPERATURE: {"calculated": False, "disable": True}}
        self.stats_info["come"] = {DEBUG_MEMORY: {"disable": True}, CDU: {"upload_to_es": True},
                                   EQM: {"upload_to_es": True},
                                   BAM: {"calculated": False, "disable": True}, DEBUG_VP_UTIL: {"upload_to_es": True},
                                   "LE": {"upload_to_es": True},
                                   HBM: {"calculated": True, "upload_to_es": True},
                                   EXECUTE_LEAKS: {"calculated": False, "disable": True},
                                   PC_DMA: {"calculated": True, "upload_to_es": True},
                                   DDR: {"calculated": True, "upload_to_es": True},
                                   STORAGE_IOPS: {"upload_to_es": True}}
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
        self.apps_run_done = {}

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
        self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                              ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                              ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                              set_term_settings=True,
                              disable_uart_logger=False)

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

        if FIO_COME in self.traffic_profile:
            self.fio_thread_map = self.start_fio_traffic(percentage=100)

        if FIO_SERVER in self.traffic_profile:
            self.start_fio_from_server()

        for f1 in self.run_on_f1:
            if RCNVME in self.traffic_profile:
                self.start_rcnvme_traffic(come_handle, f1, self.traffic_profile[RCNVME]["per"])

            if CRYPTO in self.traffic_profile:
                self.start_crypto_traffic(come_handle, f1, self.traffic_profile[CRYPTO]["per"])

            if ZIP in self.traffic_profile:
                self.start_zip_traffic(come_handle, f1, self.traffic_profile[ZIP]["per"])

            if DMA_SPEED in self.traffic_profile:
                self.start_dma_app(come_handle, f1)

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

    def start_fio_from_server(self):
        for f1 in self.run_on_f1:
            fun_test.execute_thread_after(func=self.start_fio,
                                          time_in_seconds=5,
                                          f1=f1)

    def start_fio(self, f1):
        host_handle = self.get_host_handle(f1)
        fio_data = self.get_parameters_for(FIO_COME, self.traffic_profile[FIO_SERVER]["per"])
        self.fio_params.update(fio_data)
        self.fio_params["runtime"] = self.duration
        self.fio_params["timeout"] = self.duration + 30
        host_handle.pcie_fio(filename="/dev/nvme0n1",
                             **self.fio_params)

    def get_host_handle(self, f1):
        self.vm_info = self.fio_vm_details[str(f1)]
        handle = Linux(host_ip=self.vm_info["host_ip"],
                       ssh_username=self.vm_info["ssh_username"],
                       ssh_password=self.vm_info["ssh_password"])
        return handle

    def start_rcnvme_traffic(self, come_handle, f1=0, percentage=100):
        get_parameters = self.get_parameters_for(RCNVME, percentage)
        self.rcnvme_app(come_handle, f1, **get_parameters)
        fun_test.test_assert(True, "Started RCNVME on F1: {}".format(f1))

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
                cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":true, "f1": %s}' ''' % (
                    tmp_run_time, f1)
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
        f1=0
        for vm, vm_details in vm_info.iteritems():
            cmd = '''python run_nu_transit_only.py --inputs '{"speed":"SPEED_100G", "run_time":%s, "initiate":false, "nu_tr":false, "f1":%s}' ''' % (run_time, f1)
            self.initiate_or_run_le_firewall(cmd, vm_details)
            fun_test.sleep("for le to start", seconds=10)
            running = self.check_if_le_firewall_is_running(vm_details)
            if running:
                fun_test.test_assert(running, "Le started on VM: {}".format(vm))
            f1 += 1

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

    def poll_untill_le_stops(self, vm_details, max_time=1200):
        timer = FunTimer(max_time=max_time)
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
            rcnvme_run_time = self.duration
            perc_dict = {
                "10": {"qdepth": 4, "nthreads": 1, "duration": rcnvme_run_time},
                "20": {"qdepth": 6, "nthreads": 1, "duration": rcnvme_run_time},
                "30": {"qdepth": 4, "nthreads": 2, "duration": rcnvme_run_time},
                "40": {"qdepth": 6, "nthreads": 6, "duration": rcnvme_run_time},
                "50": {"qdepth": 8, "nthreads": 2, "duration": rcnvme_run_time},
                "60": {"qdepth": 8, "nthreads": 8, "duration": rcnvme_run_time},
                "70": {"qdepth": 9, "nthreads": 9, "duration": rcnvme_run_time},
                "75": {"qdepth": 11, "nthreads": 11, "duration": rcnvme_run_time},
                "80": {"qdepth": 10, "nthreads": 10, "duration": rcnvme_run_time},
                "90": {"qdepth": 12, "nthreads": 12, "duration": rcnvme_run_time},
                "100": {"qdepth": 16, "nthreads": 16, "duration": rcnvme_run_time},
            }
            result = perc_dict[str(percentage)]
        if app == FIO_SERVER or app == FIO_COME:
            fio_run_time = self.duration
            perc_dict = {
                "10": {"numjobs": 8, "iodepth": 1, "runtime": fio_run_time},
                "35": {"numjobs": 8, "iodepth": 4, "runtime": fio_run_time},
                "65": {"numjobs": 8, "iodepth": 8, "runtime": fio_run_time},
                "100": {"numjobs": 8, "iodepth": 16, "runtime": fio_run_time}
            }
            result = perc_dict[str(percentage)]

        if app == CRYPTO:
            if self.duration == 600:
                crypto_factor = 4
            elif self.duration == 60:
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
            if self.duration == 600:
                zip_factor = 9
            elif self.duration == 60:
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
        fun_test.test_assert(True, "Started CRYPTO on F1: {}".format(f1))

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
        fun_test.test_assert(True, "Started ZIP on F1: {}".format(f1))

    def start_dma_app(self, come_handle, f1):
        get_parameters = {"dma_mode":1, "num_iter": 1500000}
        self.dma_app(come_handle, f1, **get_parameters)
        fun_test.test_assert(True, "Started DMA SPEED on F1: {}".format(f1))

    def zip_app(self, come_handle, f1, compress=True, nflows=7680, niterations=100, max_effort=0, npcs=None):
        json_data = {"niterations": niterations,
                     "nflows": nflows,
                     "max_effort": max_effort,
                     }
        if npcs:
            json_data['npcs'] = npcs
        cmd = "async deflate_perf_multi {}".format(json.dumps(json_data))
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)

    def dma_app(self, come_handle, f1, dma_mode=1, num_iter=500000):
        json_data = {"dma_mode": dma_mode,
                     "num_iter": num_iter}
        cmd = "async dma_speed {}".format(json.dumps(json_data))
        dpcsh_nocli.start_dpcsh_bg(come_handle, cmd, f1)

    def stop_traffic(self):
        if LE in self.traffic_profile:
            self.start_le_firewall(self.duration, self.boot_new_image, True)
        for f1 in self.run_on_f1:
            if FIO_COME in self.traffic_profile:
                one_dataset = {}
                fun_test.join_thread(self.fio_thread_map[str(f1)])
                fun_test.test_assert(True, "FIO successfully completed on f1 : {}".format(f1))
                try:
                    fun_test.sleep("Generating fio output")
                    output = fun_test.shared_variables["fio_output_f1_{}".format(f1)]
                    one_dataset["time"] = datetime.datetime.now()
                    one_dataset["output"] = output
                    self.add_data_to_file(getattr(self, "f_{}_f1_{}".format(FIO_COME, f1)), one_dataset)
                except Exception as ex:
                    fun_test.log(ex)
            if BUSY_LOOP in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(BUSY_LOOP, f1)] = False
                fun_test.join_thread(self.busy_loop_thread_map[f1])
            if MEMCPY in self.traffic_profile:
                fun_test.shared_variables["{}_{}".format(MEMCPY, f1)] = False
                fun_test.join_thread(self.memcpy_loop_thread_map[f1])

    def find_apps_time(self):
        result = []
        self.bmc_handle.command("cd /mnt/sdmmc0p1/log")
        f1 = 0
        for factor in range(9, 11):
            one_data_set = {}
            self.clear_uart_logs()
            if CRYPTO in self.traffic_profile:
                crypto_parameters = {"vp_iters": 5000000 * factor, "nvps": 192}
                self.crypto_app(self.come_handle, f1, **crypto_parameters)
                crypto_done = False
            else:
                crypto_done = True
            if ZIP in self.traffic_profile:
                zip_parameters = {"nflows": 7680, "niterations": 500 * factor}
                self.zip_app(self.come_handle, f1, **zip_parameters)
                zip_done = False
            else:
                zip_done = True

            timer = FunTimer(max_time=1200)
            while not timer.is_expired() and not (crypto_done and zip_done):
                data = self.bmc_handle.command("cat f1_0_uart_log.txt")
                match_crypto_end = re.search(r'Connection tore down before async ack sent for crypto_raw_speed', data)
                match_zip_end = re.search(r'"Operation": Decompress', data)
                if match_crypto_end and not crypto_done:
                    time_taken_crypto = round(timer.elapsed_time(), 2)
                    minutes = round((time_taken_crypto / 60.0), 2)
                    one_data_set["app"] = "CRYPTO"
                    one_data_set["time_taken"] = time_taken_crypto
                    one_data_set["crypto_parameters"] = crypto_parameters
                    one_data_set["factor"] = factor
                    result.append(one_data_set)
                    fun_test.log("Crypto took : {} sec or {} min for parameters: {} ".format(time_taken_crypto, minutes,
                                                                                             crypto_parameters))
                    crypto_done = True
                if match_zip_end and not zip_done:
                    fun_test.log("Parsing for ZIP app end logs")
                    time_taken_zip = round(timer.elapsed_time(), 2)
                    minutes = round((time_taken_zip / 60.0), 2)
                    one_data_set["app"] = "ZIP"
                    one_data_set["time_taken"] = time_taken_zip
                    one_data_set["zip_parameters"] = zip_parameters
                    one_data_set["factor"] = factor
                    result.append(one_data_set)
                    fun_test.log("Crypto took : {} sec or {} min for parameters: {} ".format(time_taken_zip, minutes,
                                                                                             zip_parameters))
                    zip_done = True
                fun_test.sleep("waiting before next iteration", seconds=20)
            fun_test.sleep("Before next crypto run", seconds=30)
        fun_test.log("Final results: {}".format(result))

    def are_apps_done(self, timer):
        for f1 in self.run_on_f1:
            self.apps_run_done.setdefault("crypto_f1_{}".format(f1), False)
            self.apps_run_done.setdefault("zip_f1_{}".format(f1), False)
            self.are_apps_done_on_f1(f1, timer)
        result = True if all(self.apps_run_done.values()) else False
        return result

    def are_apps_done_on_f1(self, f1, timer):
        data = self.bmc_handle.command("cat /mnt/sdmmc0p1/log/funos_f1_{}.log".format(f1))
        if CRYPTO in self.traffic_profile and not self.apps_run_done["crypto_f1_{}".format(f1)]:
            res = self.is_crypto_done(data=data, f1=f1)
            if res:
                self.apps_run_done["crypto_f1_{}".format(f1)] = True
                time_taken = round(timer.elapsed_time(), 2)
                fun_test.test_assert(True, "Crypto app completed on F1: {} time taken: {}".format(f1, time_taken))
        else:
            self.apps_run_done["crypto_f1_{}".format(f1)] = True

        if ZIP in self.traffic_profile and (not self.apps_run_done["zip_f1_{}".format(f1)]):
            res = self.is_zip_done(data=data, f1=f1)
            if res:
                self.apps_run_done["zip_f1_{}".format(f1)] = True
                time_taken = round(timer.elapsed_time(), 2)
                fun_test.test_assert(True, "ZIP app completed on F1: {} time taken: {}".format(f1, time_taken))
        else:
            self.apps_run_done["zip_f1_{}".format(f1)] = True

    def is_crypto_done(self, data, f1):
        result = False
        fun_test.log("checking if CRYPTO app has ended on F1: {}".format(f1))
        match_app_end = re.search(r'Connection tore down before async ack sent for crypto_raw_speed', data)
        if match_app_end:
            result = True
        else:
            fun_test.log("CRYPTO app has not ended on F1: {}".format(f1))
        return result

    def is_zip_done(self, data, f1):
        result = False
        fun_test.log("checking if ZIP app has ended on F1: {}".format(f1))
        match_app_end = re.search(r'Connection tore down before async ack sent for deflate_perf_multi', data)
        if match_app_end:
            result = True
        else:
            fun_test.log("ZIP app has not ended on F1: {}".format(f1))
        return result

    def add_data_to_file(self, f, data, extra_line=False, heading="Result"):
        if not self.upload_to_file:
            return
        # for data in data_list:
        f.write("\n")
        f.write("-----------------{}------------------".format(heading))
        f.write('\n')
        f.write("Time = {}".format(data["time"]))
        f.write("\n")
        if "time_difference" in data:
            f.write("Time difference with the initial stats: {}".format(data["time_difference"]))
        f.write("\n")
        if type(data["output"]) is dict:
            self.add_json_data(f, data["output"])
        else:
            f.write(data["output"])
        f.write("\n")
        if extra_line:
            f.write("\n")

    def add_json_data(self, f, data):
        json.dump(data, f, indent=4)
        f.write("\n")

    def stop_collection_of_stats(self):
        for system, system_value in self.stats_info.iteritems():
            for stat_name, stat_value in system_value.iteritems():
                if stat_value.get("disable", False):
                    continue
                if system == "bmc":
                    fun_test.shared_variables["stat_{}".format(stat_name)]["run_status"] = False
                if system == "come":
                    for f1 in self.run_on_f1:
                        fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["run_status"] = False

        for thread_name, thread_id in self.stats_thread_map.iteritems():
            fun_test.join_thread(thread_id)

    def stop_collection_of_stats_for_count(self, count=5):
        app_result = {}
        for system, system_value in self.stats_info.iteritems():
            for stat_name, stat_value in system_value.iteritems():
                if stat_value.get("disable", False):
                    continue
                if system == "bmc":
                    app_result[stat_name] = False
                if system == "come":
                    for f1 in self.run_on_f1:
                        app_result["{}_f1_{}".format(stat_name, f1)] = False

        are_all_apps_done = all(app_result.values())
        while not are_all_apps_done:
            for system, system_value in self.stats_info.iteritems():
                for stat_name, stat_value in system_value.iteritems():
                    if stat_value.get("disable", False):
                        continue
                    if system == "bmc":
                        linker = fun_test.shared_variables["stat_{}".format(stat_name)]
                        fun_test.log("App : {} has completed : {}".format(stat_name, linker["count"]))
                        if linker["count"] >= count:
                            fun_test.shared_variables["stat_{}".format(stat_name)]["run_status"] = False
                            app_result[stat_name] = True
                    if system == "come":
                        for f1 in self.run_on_f1:
                            linker = fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]
                            fun_test.log("App : {} has completed on F1: {} : {}".format(stat_name, f1, linker["count"]))
                            if linker["count"] >= count:
                                fun_test.shared_variables["stat_{}_f1_{}".format(stat_name, f1)]["run_status"] = False
                                app_result["{}_f1_{}".format(stat_name, f1)] = True

            are_all_apps_done = all(app_result.values())
            fun_test.sleep("Before checking the count iteration")

        for thread_name, thread_id in self.stats_thread_map.iteritems():
            fun_test.join_thread(thread_id)


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FrsTestCase())
    myscript.run()
