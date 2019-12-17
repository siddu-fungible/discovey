import os
from lib.host.linux import Linux
from lib.host.storage_controller import StorageController
from lib.system.fun_test import *
from lib.system import utils
from asset.asset_manager import AssetManager
import re
from lib.fun.fs import ComE, Bmc, Fpga
from lib.host.dpcsh_client import DpcshClient
from scripts.storage.pocs.apple.apc_pdu_auto import ApcPduTestcase


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class Platform(ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.intialize_handles()
        self.switch_to_py3_env()

    def run(self):
        self.chassis_power()
        self.chassis_thermal()
        fan_speed = self.read_fans_data()
        temperature = self.get_temperature()
        fun_test.log("\nFan speed: {}\nTemperature : {}".format(fan_speed, temperature))
        self.check_ssd_status(self.expected_ssds)
        self.check_nu_ports(self.expected_ports_up)

    def redfishtool(self, bmc_ip, username, password, sub_command=None, **kwargs):
        cmd = "python3 redfishtool -r {bmc_ip} -u {username} -p {password}".format(bmc_ip=bmc_ip,
                                                                                   username=username,
                                                                                   password=password)
        for k, v in kwargs.iteritems():
            cmd += " -" + k + " " + v
        if sub_command:
            cmd += " " + sub_command

        output = self.qa_02.command(cmd)
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
        self.qa_02 = Linux(**service_host_spec)

    def intialize_handles(self):
        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])
        self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                              ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                              ssh_password=self.fs['bmc']['mgmt_ssh_password'])
        self.fpga_handle = Fpga(host_ip=self.fs['fpga']['mgmt_ip'],
                                ssh_username=self.fs['fpga']['mgmt_ssh_username'],
                                ssh_password=self.fs['fpga']['mgmt_ssh_password'])
        self.f1_0_dpc = DpcshClient(target_ip=self.come_handle.host_ip,
                                    target_port=self.come_handle.get_dpc_port(0),
                                    verbose=False)
        self.f1_1_dpc = DpcshClient(target_ip=self.come_handle.host_ip,
                                    target_port=self.come_handle.get_dpc_port(1),
                                    verbose=False)

    def switch_to_py3_env(self):
        self.qa_02.command("cd /local/auto_admin/.local/bin")

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

    def get_dpcsh_data_for_cmds(self, cmd, f1=0, peek=True):
        result = getattr(self, "f1_{}_dpc".format(f1)).command(cmd, legacy=True)
        fun_test.simple_assert(result["status"], "Get DPCSH Data")
        return result["data"]

    def validate_fans(self):
        output = self.chassis_thermal()
        fans = output["Fans"]
        for fan in fans:
            fan_status = fan["Status"]
            if (fan_status["Health"] == "OK") and (fan_status["State"] == "Enabled") and (fan["Reading"] <= fan["MaxReadingRange"]):
                result = True
            else:
                result = False
            fun_test.simple_assert(result, "Fan : {} is healthy".format(fan["Name"]))
        fun_test.log("Successfully validated all the fans")
        fun_test.test_assert(True, "Fans healthy")

    def validate_temperaure_sensors(self):
        output = self.chassis_thermal()
        temperature_sensors = output["Temperatures"]
        for sensor in temperature_sensors:
            sensor_status = sensor["Status"]
            if (sensor_status["Health"] == "OK") and (sensor_status["State"] == "Enabled") and sensor["ReadingCelsius"] < sensor["UpperThresholdFatal"]:
                result = True
            else:
                result = False
            fun_test.simple_assert(result, "Temperature Sensor : {} is healthy".format(sensor["Name"]))
        fun_test.log("Successfully validated all the temperature sensors")
        fun_test.test_assert(True, "Temperature sensors healthy")

    def get_platform_drop_information(self, system="come"):
        # todo: no idea
        result = {"status":False, "dropname":""}
        fun_test.log("Platform drop informtion: {}".format(""))
        return result

    def set_platform_ip_information(self, system="come"):
        # todo: how to set it
        result = {"status": False}
        fun_test.log("Platform : {} IP set to : {}".format("", ""))
        return result

    def get_platform_ip_information(self):
        result = {"status": False, "data": {}}
        handles_list = {"come": self.come_handle, "bmc": self.bmc_handle,
                        "fpga": self.fpga_handle}
        try:
            for system, handle in handles_list.iteritems():
                output = handle.command("ifconfig")
                if system == "come" or system == "fpga":
                    split_with = "flags"
                elif system == "bmc":
                    split_with = "Link"
                interfaces = output.split(split_with)
                for interface in interfaces:
                    match_inet = re.search(r'inet\s+(addr:)?\s?(?P<ipv4>\d+.\d+.\d+.\d+)', interface)
                    match_inet6 = re.search(r'inet6\s+(addr:)?\s?(?P<ipv6>\w+::\w+:\w+:\w+:\w+)', interface)
                    if match_inet and match_inet6:
                        ipv4 = match_inet.group("ipv4")
                        ipv6 = match_inet6.group("ipv6")
                        result["data"][system] = {"ipv4": ipv4, "ipv6": ipv6}
                        fun_test.log("System : {} IP : {}".format(system, result["data"][system]))
                result["status"] = True
            fun_test.log("IPV6 addresses: {}".format(result))
        except Exception as ex:
            fun_test.log(ex)
            result["status"] = False
        return result

    def set_platform_link(self):
        # todo: need to verify with Parag if this is what we need to do
        self.get_port_link_status()
        cmd = "port enableall"
        output = self.get_dpcsh_data_for_cmds(cmd)
        result = {"status": True}
        fun_test.sleep("Enabling all the ports", seconds=30)
        self.get_port_link_status()
        return result

    def get_platform_link(self, f1=0):
        # todo: Verify with Parag if this is what we want to do
        result = {"status": False}
        return result

    def get_platform_version_information(self):
        # todo: how to get the version
        result = {"status": False, "linkparams": ""}
        return result

    # def get_platform_ip_information(self):
    #     #  Loop through all array (fpga, come, bcc)
    #     # todo : check with parag what is the bcc thing
    #     result = self.get_platform_ip_information()
    #     fun_test.log("Platform ip info: {}".format(result["data"]))
    #     return result

    def get_ssd_info(self, f1=0):
        cmd = "peek storage/devices/nvme/ssds"
        dpcsh_data = self.get_dpcsh_data_for_cmds(cmd, f1)
        result = {"status": True, "data": dpcsh_data}
        fun_test.log("SSD info : {}".format(dpcsh_data))
        return result

    def get_port_link_status(self, f1=0):
        result = {"status": False}
        cmd = "port linkstatus"
        dpcsh_output = self.get_dpcsh_data_for_cmds(cmd, f1)
        data = self.parse_link_status_out(dpcsh_output, f1)
        if data:
            result = {"status": True, "data": data}
            fun_test.log("Port linkstatus: {}".format(data))
        return result

    def read_fans_data(self):
        # todo: check with Parag if just fan speed is enough
        result = {"status": False, "data": {}}
        try:
            output = self.chassis_thermal()
            fans = output["Fans"]
            for fan in fans:
                result["data"][fan["Name"]] = fan["Reading"]
            result["status"] = True
        except Exception as ex:
            fun_test.log(ex)
            result = {"status": False}
        fun_test.simple_assert(result["status"], "Read fan speed")
        fun_test.log("Fan Readings: {}".format(result["data"])) if (result["status"]) else None
        return result

    def read_dpu_data(self):
        # todo: dont know how to read the dpu data
        result = {"status": False}
        return result

    def reboot(self, system="come", max_wait_time=180):
        if system == "come":
            self.come_handle.reboot(max_wait_time=max_wait_time)
        elif system == "bmc":
            self.bmc_handle.reboot(max_wait_time=max_wait_time)
        elif system == "fpga":
            self.fpga_handle.reboot(max_wait_time=max_wait_time)
        self.intialize_handles()

    def power_on(self):
        # todo: is it redfish or any other tool, what are the commands
        pass

    def power_off(self):
        # todo: is it redfish or any other tool, what are the commands
        pass

    def connect_get_set_get_jtag(self):
        # todo: how to do this
        pass

    def connect_get_set_get_i2c(self):
        # todo: how to do this
        pass

    def cleanup(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(Platform())
    myscript.run()
