from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.fun.fs import ComE
import dpcsh_commands
import file_helper
import debug_memory_calculation


class Setup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="")

    def setup(self):
        pass

    def cleanup(self):
        pass


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="")

    def setup(self):
        job_inputs = fun_test.get_job_inputs()
        self.details = {
            "fs": "fs-65",
            "duration": 60,
            "interval": 5
        }
        if job_inputs:
            if "fs" in job_inputs:
                self.details["fs"] = job_inputs["fs"]
            if "duration" in job_inputs:
                self.details["duration"] = job_inputs["duration"]
            if "interval" in job_inputs:
                self.details["interval"] = job_inputs["interval"]

        self.fs = AssetManager().get_fs_by_name(self.details["fs"])
        fun_test.log(json.dumps(self.fs, indent=4))
        fun_test.log("Details: {}, Input: {}".format(self.details, job_inputs))
        self.f1_0_debug_memory_dpc_logs = fun_test.get_test_case_artifact_file_name(post_fix_name="debug_memory_F1_0_logs.txt")
        self.f1_1_debug_memory_dpc_logs = fun_test.get_test_case_artifact_file_name(post_fix_name="debug_memory_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="debug memory dpcsh output F1_0", filename=self.f1_0_debug_memory_dpc_logs)
        fun_test.add_auxillary_file(description="debug memory dpcsh output F1_1", filename=self.f1_1_debug_memory_dpc_logs)

        self.f1_0_debug_memory_difference_dpc_logs = fun_test.get_test_case_artifact_file_name(post_fix_name="debug_memory_difference_F1_0_logs.txt")
        self.f1_1_debug_memory_difference_dpc_logs = fun_test.get_test_case_artifact_file_name(post_fix_name="debug_memory_difference_F1_1_logs.txt")
        fun_test.add_auxillary_file(description="debug memory dpcsh output difference stats F1_0", filename=self.f1_0_debug_memory_difference_dpc_logs)
        fun_test.add_auxillary_file(description="debug memory dpcsh output difference stats F1_1", filename=self.f1_1_debug_memory_difference_dpc_logs)

    def run(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        come_handle.command("pwd")
        f_debug_memory_f1_0 = open(self.f1_0_debug_memory_dpc_logs, "w+")
        f_debug_memory_f1_1 = open(self.f1_1_debug_memory_dpc_logs, "w+")
        f_debug_memory_difference_f1_0 = open(self.f1_0_debug_memory_difference_dpc_logs, "w+")
        f_debug_memory_difference_f1_1 = open(self.f1_1_debug_memory_difference_dpc_logs, "w+")

        # timer = FunTimer(self.details["duration"])
        count = int(self.details["duration"] / self.details["interval"])

        self.initial_debug_memory_stats = self.get_debug_memory_stats_initially(f_debug_memory_f1_0,f_debug_memory_f1_1)
        fun_test.test_assert(True, "Initial debug stats is saved")

        thread_id_f1_0 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
                                                       time_in_seconds=5,
                                                       f1=0,
                                                       file_handler=f_debug_memory_f1_0,
                                                       file_difference=f_debug_memory_difference_f1_0,
                                                       count=count,
                                                       heading="Before traffic",
                                                       find_difference=True)
        thread_id_f1_1 = fun_test.execute_thread_after(func=self.dpcsh_debug_memory,
                                                       time_in_seconds=6,
                                                       f1=1,
                                                       file_handler=f_debug_memory_f1_1,
                                                       file_difference=f_debug_memory_difference_f1_1,
                                                       count=count,
                                                       heading="Before traffic",
                                                       find_difference=True)

        fun_test.join_thread(thread_id_f1_0)
        # fun_test.join_thread(thread_id_f1_1)
        # f_debug_memory_f1_0.close()
        # f_debug_memory_f1_1.close()

    def dpcsh_debug_memory(self, f1, file_handler, file_difference, count, heading, find_difference=False):
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

    def get_debug_memory_stats_initially(self,f_debug_memory_f1_0, f_debug_memory_f1_1):
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

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = Setup()
    ts.add_test_case(TestCase1())
    ts.run()