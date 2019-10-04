from lib.system.fun_test import *
from start_traffic_helper import *
from asset.asset_manager import AssetManager
from lib.fun.fs import ComE, Bmc
import bmc_commands
import dpcsh_commands
import file_helper
import debug_memory_calculation


from scripts.storage.storage_helper import *


import get_params_for_time

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps= """""")

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
        # 3. 3.5 hour - 210min

        job_inputs = fun_test.get_job_inputs()
        self.details = {
            "fs": "fs-65",
            "duration": "1m",
            "le_firewall": True,
            "interval": 5
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

            self.fs = AssetManager().get_fs_by_name(self.details["fs"])
            fun_test.log(json.dumps(self.fs, indent=4))
            fun_test.log("Details: {}, Input: {}".format(self.details, job_inputs))
            # Power files
            self.power_shell = fun_test.get_test_case_artifact_file_name(post_fix_name="power_shell_script_logs.txt")
            self.power_output = fun_test.get_test_case_artifact_file_name(post_fix_name="power_output_logs.txt")
            fun_test.add_auxillary_file(description="Power shell script output", filename=self.power_shell)
            fun_test.add_auxillary_file(description="FS and F1 power output", filename=self.power_output)

            # Debug files
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

            # Traffic
            self.methods = {"crypto": crypto, "zip": zip, "rcnvme":rcnvme, "fio":fio}

            if self.details["duration"] == "1m":
                self.test_duration = 60
            elif self.details["duration"] == "1h":
                self.test_duration = 3600
            elif self.details["duration"] == "4h":
                self.test_duration = 14400


    def run(self):
        # Initialise the
        # Power files
        self.f_power_shell = open(self.power_shell, 'w+')
        self.f_power_output = open(self.power_output, 'w+')


        # Debug memory files

        self.f_debug_memory_f1_0 = open(self.f1_0_debug_memory_dpc_logs, "w+")
        self.f_debug_memory_f1_1 = open(self.f1_1_debug_memory_dpc_logs, "w+")
        self.f_debug_memory_difference_f1_0 = open(self.f1_0_debug_memory_difference_dpc_logs, "w+")
        self.f_debug_memory_difference_f1_1 = open(self.f1_1_debug_memory_difference_dpc_logs, "w+")


        ############## Before traffic #####################
        self.initial_debug_memory_stats = self.get_debug_memory_stats_initially(self.f_debug_memory_f1_0,
                                                                                self.f_debug_memory_f1_1)
        self.capture_data(count=3, heading="Before starting traffic")

        fun_test.test_assert(True, "Initial debug stats is saved")


        #############  Starting Traffic ################
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        come_handle.command("pwd")

        app_params = get_params_for_time.get(self.test_duration)
        fun_test.log("App parameters: {}".format(app_params))

        if self.details["le_firewall"]:
            le_firewall(self.test_duration)

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


        #################### After the traffic ################
        if self.details["le_firewall"]:
            kill_le_firewall()
        fun_test.sleep("To make sure traffic is completed", seconds=5)
        count = 3
        heading = "After the traffic"
        fun_test.log("Capturing the data {}".format(heading))
        self.capture_data(count=count, heading=heading)

        self.f_power_shell.close()
        self.f_power_output.close()
        self.f_debug_memory_f1_0.close()
        self.f_debug_memory_f1_1.close()

    def cleanup(self):
        pass

    ############## power #############
    def power_output_to_file(self, count, f_power_shell, f_power_output, heading):
        bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                         ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                         ssh_password=self.fs['bmc']['mgmt_ssh_password'],
                         set_term_settings=True,
                         disable_uart_logger=False)
        bmc_handle.set_prompt_terminator(r'# $')

        for i in range(count):
            raw_output, cal_output = bmc_commands.power_manager(bmc_handle=bmc_handle)
            time_now = datetime.datetime.now()
            print_data = {"output": raw_output, "time": time_now}
            file_helper.add_data(f_power_shell, print_data, heading=heading)
            print_data = {"output": cal_output, "time": time_now}
            file_helper.add_data(f_power_output, print_data, heading=heading)
            fun_test.sleep("before next iteration", seconds=self.details["interval"])
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
        return result


    ####### Data Capturing function

    def capture_data(self, count, heading):
        thread_id_power = fun_test.execute_thread_after(func=self.power_output_to_file,
                                                        time_in_seconds=1,
                                                        count=count,
                                                        f_power_shell=self.f_power_shell,
                                                        f_power_output=self.f_power_output,
                                                        heading=heading)

        fun_test.test_assert(True, "Started capturing the power logs {}".format(heading))
        thread_id_debug_memory_f1_0 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
                                                                    time_in_seconds=2,
                                                                    f1=0,
                                                                    file_handler=self.f_debug_memory_f1_0,
                                                                    file_difference=self.f_debug_memory_difference_f1_0,
                                                                    count=count,
                                                                    heading=heading)

        fun_test.test_assert(True, "Started capturing the debug memory logs {} on F1_0".format(heading))
        thread_id_debug_memory_f1_1 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
                                                                    time_in_seconds=3,
                                                                    f1=1,
                                                                    file_handler=self.f_debug_memory_f1_1,
                                                                    file_difference=self.f_debug_memory_difference_f1_1,
                                                                    count=count,
                                                                    heading=heading)
        fun_test.test_assert(True, "Started capturing the debug memory logs {} on F1_1".format(heading))

        fun_test.join_thread(thread_id_power)
        fun_test.join_thread(thread_id_debug_memory_f1_0)
        fun_test.join_thread(thread_id_debug_memory_f1_1)
        fun_test.test_assert(True, "Power logs captured successfully")
        fun_test.test_assert(True, "Debug memory on F1_0 logs captured successfully")
        fun_test.test_assert(True, "Debug memory on F1_0 logs captured successfully")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()