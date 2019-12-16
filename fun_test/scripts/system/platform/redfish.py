import os
from subprocess import Popen, PIPE
from lib.host.linux import Linux
from lib.host.storage_controller import StorageController
from lib.system.fun_test import *
from lib.system import utils
from asset.asset_manager import AssetManager
import re


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.switch_to_py3_env()

    def run(self):
        # self.chassis_power()
        # self.chassis_thermal()
        fan_speed = self.get_fan_speed()
        temperature = self.get_temperature()
        fun_test.log("\nFan speed: {}\nTemperature : {}".format(fan_speed, temperature))

    def redfishtool(self, bmc_ip, username, password, sub_command=None, **kwargs):
        cmd = "python3 redfishtool -r {bmc_ip} -u {username} -p {password}".format(bmc_ip=bmc_ip,
                                                                                   username=username,
                                                                                   password=password)
        for k, v in kwargs.iteritems():
            cmd += " -" + k + " " + v
        if sub_command:
            cmd += " " + sub_command

        output = self.handle.command(cmd)
        json_output = self.parse_output(output)
        return json_output

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
            for k, v in job_inputs.iteritems():
                setattr(self, k, v)

    def initialize_variables(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.handle = Linux(**service_host_spec)

        self.f1_0_dpc = StorageController(target_ip=self.come_handle.host_ip,
                                          target_port=self.come_handle.get_dpc_port(0))
        self.f1_1_dpc = StorageController(target_ip=self.come_handle.host_ip,
                                          target_port=self.come_handle.get_dpc_port(1))

    def switch_to_py3_env(self):
        self.handle.command("cd /local/auto_admin/.local/bin")

    def chassis_power(self):
        sub_command = "Chassis -1 Power"
        additional = {"A": "Basic", "S": "Always"}
        output = self.redfishtool(self.fs['bmc']['mgmt_ip'], self.credentials["username"], self.credentials["password"],
                                  sub_command, **additional)
        return output

    def chassis_thermal(self):
        sub_command = "Chassis -1 Thermal"
        additional = {"A": "Basic", "S": "Always"}
        output = self.redfishtool(self.fs['bmc']['mgmt_ip'], self.credentials["username"], self.credentials["password"],
                                  sub_command, **additional)
        return output

    def get_fan_speed(self):
        result = {}
        output = self.chassis_thermal()
        fans = output["Fans"]
        for fan in fans:
            result[fan["Name"]] = fan["Reading"]
        return result

    def get_temperature(self):
        result = {}
        output = self.chassis_thermal()
        temperatures = output["Temperatures"]
        for temperature in temperatures:
            result[temperature["Name"]] = temperature["ReadingCelsius"]
        return result

    def parse_output(self, data):
        result = {}
        data = data.replace('\r', '')
        data = data.replace('\n', '')
        # \s+=>\s+(?P<json_output>{.*})
        match_output = re.search(r'(?P<json_output>{.*})', data)
        if match_output:
            try:
                result = json.loads(match_output.group('json_output'))
            except:
                fun_test.log("Unable to parse the output obtained from dpcsh")
        return result

    def ssd_info(self):
        cmd = ""

    def port_status(self):
        pass

    def cleanup(self):
        pass

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
