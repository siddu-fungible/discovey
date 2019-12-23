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
from lib.fun.fs import *


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class LinuxAdditions(Linux):

    def ifconfig(self, **kwargs):
        result = []
        cmd = "ifconfig"
        for i in kwargs:
            cmd += " -" + i
        ifconfig_output = self.command(cmd)
        if ifconfig_output:
            interfaces = ifconfig_output.split("\n\r")
            for interface in interfaces:
                one_data_set = {}
                match_ifconfig = re.search(r"(?P<interface>\S+)[\s\S]*(HWaddr\s+(?P<hw_addr>\w+:\w+:\w+:\w+))?[\s\S]*inet\s+(addr:)?(?P<ipv4>\d+.\d+.\d+.\d+)[\s\S]"
                                           r"*inet6\s+(addr:)?\s?(?P<ipv6>\w+::\w+:\w+:\w+:\w+)[\s\S]*", interface)
                match_interface = re.match(r'(?P<interface>\S+)', interface)
                match_ipv4 = re.search(r'(?P<ipv4>\d+.\d+.\d+.\d+)', interface)
                if match_ifconfig:
                    one_data_set["interface"] = match_ifconfig.group("interface")
                    one_data_set["ipv4"] = match_ifconfig.group("ipv4")
                    one_data_set["ipv6"] = match_ifconfig.group("ipv6")
                    one_data_set["hw_addr"] = match_ifconfig.group("hw_addr")
                    result.append(one_data_set)
        return result


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
        # self.switch_to_py3_env()

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
                                    target_port=self.come_handle.get_dpc_port(0, statistics=True),
                                    verbose=False)
        self.f1_1_dpc = DpcshClient(target_ip=self.come_handle.host_ip,
                                    target_port=self.come_handle.get_dpc_port(1, statistics=True),
                                    verbose=False)
        fs = Fs.get(self.fs)
        self.fpga_console_handle = fs.get_terminal()
        self.handles_list = {"come": self.come_handle, "bmc": self.bmc_handle, "fpga": self.fpga_handle}

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
        result = {"status": False, "data": {}}
        handle = self.handles_list[system]
        output = handle.uname()
        if output:
            result["status"] = True
            result["data"] = output
        return result

    def set_platform_ip_information(self, system="come"):
        # todo: how to set it
        result = {"status": False}
        fun_test.log("Platform : {} IP set to : {}".format("", ""))
        return result

    def get_platform_ip_information(self, system="come"):
        result = {"status": False, "data": {}}
        handle = self.handles_list[system]
        data = handle.ifconfig()
        if data:
            result["data"] = data
            result["status"] = True
        return result

    def set_platform_link(self, system="bmc", action="up"):
        # action can be : up or down
        result = {"status": False, "data": "", "message": ""}
        if system == "bmc":
            interface = "bond0"
            max_time = 10
            self.fpga_console_handle.switch_to_bmc_console(max_time)
            timer = FunTimer(max_time=max_time)
            self.fpga_console_handle.command("pwd")
            output = self.fpga_console_handle.ifconfig(interface, action)
            output = self.fpga_console_handle.ifconfig(interface, action)
            if "Cannot assign" in output:
                result["status"] = False
                result["message"] = "Unable to set interface : {}".format(interface)
            else:
                result["status"] = True
                result["message"] = "set interface : {} to: {}".format(interface, action)
                result["data"] = output
            fun_test.sleep("For BMC console to close", seconds=timer.remaining_time())
        return result

    def get_platform_link(self, system="bmc"):
        result = {"status": False, "link_detected": False}
        if system == "bmc":
            interface = "bond0"
            max_time = 10
            self.fpga_console_handle.switch_to_bmc_console(max_time)
            timer = FunTimer(max_time=max_time)
            self.fpga_console_handle.command("pwd")
            self.fpga_console_handle.ethtool(interface)
            output = self.fpga_console_handle.ethtool(interface)
            if output:
                result["status"] = True
                result["link_detected"] = True if output.get("link_detected", "no") == "yes" else False
            fun_test.sleep("For BMC console to close", seconds=timer.remaining_time())
        return result

    def get_platform_version_information(self, system="bmc"):
        result = {"status": False, "data": {}}
        handle = self.handles_list[system]
        output = handle.command("cat /etc/lsb-release")
        if output:
            if "No such file" not in output:
                lines = output.split("\n")
                result["status"] = True
                for line in lines:
                    k, v = line.split("=")
                    result["data"][k] = v.strip().replace("\"", "")
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
        result = {"status": False}
        apc_pdu = ApcPdu(host_ip=self.apc_info['host_ip'], username=self.apc_info['username'],
                         password=self.apc_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)
        apc_outlet_on_msg = apc_pdu.outlet_on(self.outlet_no)
        fun_test.log("APC PDU outlet on message {}".format(apc_outlet_on_msg))
        outlet_on = self.match_success(apc_outlet_on_msg)
        fun_test.test_assert(outlet_on, "Power on FS")
        result["status"] = True
        apc_pdu.disconnect()
        return result

    def power_off(self):
        result = {"status": False}
        apc_pdu = ApcPdu(host_ip=self.apc_info['host_ip'], username=self.apc_info['username'],
                         password=self.apc_info['password'])
        fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)
        apc_outlet_off_msg = apc_pdu.outlet_off(self.outlet_no)
        fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
        outlet_off = self.match_success(apc_outlet_off_msg)
        fun_test.test_assert(outlet_off, "Power down FS")
        result["status"] = True
        apc_pdu.disconnect()
        return result


    def connect_get_set_get_jtag(self):
        # todo: how to do this
        pass

    def connect_get_set_get_i2c(self):
        # todo: how to do this
        pass

    def telnet_test(self):
        pass

    def cleanup(self):
        pass


class FpgaConsole:
    def asd(self):
        pass


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(Platform())
    myscript.run()
