from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.fun.fs import ComE, Bmc
import bmc_commands
import file_helper


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
        self.power_shell = fun_test.get_test_case_artifact_file_name(post_fix_name="power_shell_script_logs.txt")
        self.power_output = fun_test.get_test_case_artifact_file_name(post_fix_name="power_output_logs.txt")
        fun_test.add_auxillary_file(description="Power shell script output", filename=self.power_shell)
        fun_test.add_auxillary_file(description="FS and F1 power output", filename=self.power_output)

    def run(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        # come_handle.command("pwd")

        f_power_shell = open(self.power_shell, 'w+')
        f_power_output = open(self.power_output, 'w+')

        # timer = FunTimer(self.details["duration"])
        count = int(self.details["duration"] / self.details["interval"])

        thread_id_power = fun_test.execute_thread_after(func=self.power_output_to_file,
                                                        time_in_seconds=5,
                                                        count=count,
                                                        f_power_shell=f_power_shell,
                                                        f_power_output=f_power_output,
                                                        heading="Before starting traffic")
        fun_test.test_assert(True, "Started capturing the power logs")
        fun_test.join_thread(thread_id_power)

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
            # file_helper.add_data(f_power_shell, one_dataset, heading="debug memory")

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = Setup()
    ts.add_test_case(TestCase1())
    ts.run()