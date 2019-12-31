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


class IpmiTool:
    IPMIUSERNAME = "admin"
    IPMIPASSWORD = "admin"

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

    def intialize_qa_02(self):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.qa_02 = Linux(**service_host_spec)

    def ipmitool(self, sub_command=None):
        if not getattr(self, "fs", False):
            self.initialise_fs()
        cmd = "ipmitool -I lanplus -H {} -U {} -P {}".format(self.fs['bmc']['mgmt_ip'], self.IPMIUSERNAME, self.IPMIPASSWORD)
        if sub_command:
            cmd += " " + sub_command
        if not getattr(self, "qa_02", False):
            self.intialize_qa_02()
        output = self.qa_02.command(cmd)
        return output

    def check_ipmi_tool_connect(self):
        output = self.ipmitool("raw")
        result = False if "Unable to establish" in output else True
        return result

    def ipmitool_sdr(self):
        result = {"status": True, "data": {}}
        sub_command = "sdr"
        output = self.ipmitool(sub_command)
        data = self.parse_sdr(output)
        if data:
            result["status"] = True
            result["data"] = data
        return result

    def ipmitool_reset(self, action="soft"):
        # TODO: this is little conofusing heere with warm and soft reboots
        result = {"status": True, "data": {}}
        if action == "warm":
            action = "cycle"
        sub_command = "chassis power {}".format(action)
        output = self.ipmitool(sub_command)
        if output:
            result["status"] = True
            result["data"] = output
        else:
            result["status"] = False
        return result

    def parse_sdr(self, data):
        lines = data.split("\n")
        result = {}
        for line in lines:
            cols = line.split("|")
            cols_strip = [x.strip() for x in cols]
            result[cols_strip[0]] = {}
            match_readings = re.search(r'(\d+)\s+([\w ]+)', cols_strip[1])
            match_hexa = re.search(r'\d+x\d+', cols_strip[1])
            if match_readings:
                result[cols_strip[0]]["reading"] = int(match_readings.group(1))
                result[cols_strip[0]]["unit"] = match_readings.group(2)
            if match_hexa:
                result[cols_strip[0]]["reading"] = match_hexa.group(0)
            result[cols_strip[0]]["status"] = cols_strip[2]
        return result

    def verify_ipmi_sdr_info(self, rpm_threshold=20000, exhaust_threshold=90, inlet_threshold=90,
                             f1_temperature=90):
        sdr = self.ipmitool_sdr()
        result = self.validate_sdr_data(sdr, rpm_threshold, exhaust_threshold, inlet_threshold, f1_temperature)
        fun_test.test_assert(result, "Validated sensor data with ipmitool sdr")
        return result

    def validate_sdr_data(self, sdr_output, rpm_threshold=20000, exhaust_threshold=90, inlet_threshold=90,
                          f1_temperature=90):
        result = True
        sdr_data = sdr_output["data"]
        for sensor, readings in sdr_data.iteritems():
            if readings.get("unit", False):
                if not readings["status"] == "ok":
                    result = False
                    break
                if "Fan" in sensor:
                    if readings["reading"] > rpm_threshold:
                        result = False
                        break
                if "Inlet" in sensor:
                    if readings["reading"] > inlet_threshold:
                        result = False
                        break
                if "Exhaust" in sensor:
                    if readings["reading"] > exhaust_threshold:
                        result = False
                        break
                if "F1" in sensor:
                    if readings["reading"] > f1_temperature:
                        result = False
                        break

        if result:
            fun_test.test_assert(result, "Validated Fan readings")
            fun_test.test_assert(result, "Validated Inlet readings")
            fun_test.test_assert(result, "Validated Exhaust readings")
            fun_test.test_assert(result, "Validated F1 readings")
        else:
            fun_test.log("Error with sensor: {} readings: {}".format(sensor, readings))
        return result


class RedFishTool:
    REDFISH_USERNAME = "Administrator"
    REDFISH_PASSWORD = "superuser"

    def switch_to_py3_env(self):
        self.qa_02.command("cd /local/auto_admin/.local/bin")
        self.in_py3_env = True

    def intialize_qa_02(self):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.qa_02 = Linux(**service_host_spec)

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

    def check_if_redfish_is_active(self):
        response = self.chassis_power()
        result = True if response["status"] else False
        keyword = "" if result else "in-"
        fun_test.log("Redfishtool is {}active".format(keyword))
        return result

    def redfishtool(self, sub_command=None, **kwargs):
        if not getattr(self, "in_py3_env", False):
            self.switch_to_py3_env()
        if not getattr(self, "fs", False):
            self.initialise_fs()
        cmd = "python3 redfishtool -A Basic -S Always -r {bmc_ip} -u {username} -p {password}".format(
            bmc_ip=self.fs["bmc"]["mgmt_ip"],
            username=self.REDFISH_USERNAME,
            password=self.REDFISH_PASSWORD)
        for k, v in kwargs.iteritems():
            cmd += " -" + k + " " + v
        if sub_command:
            cmd += " " + sub_command

        output = self.qa_02.command(cmd)
        json_output = self.parse_output(output)
        return json_output

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

    def read_fans_data(self):
        # todo: check with Parag if just fan speed is enough
        result = {"status": False, "data": {}}
        response = self.chassis_thermal()
        if response["status"]:
            fans = response["data"]["Fans"]
            for fan in fans:
                result["data"][fan["Name"]] = fan["Reading"]
            result["status"] = True
        fun_test.simple_assert(result["status"], "Read fan speed")
        fun_test.log("Fan Readings: {}".format(result["data"])) if (result["status"]) else None
        return result

    def chassis_power(self):
        result = {"status": False, "data":{}}
        sub_command = "Chassis -1 Power"
        output = self.redfishtool(sub_command)
        if output:
            result["status"] = True
            result["data"] = output
        return result

    def chassis_thermal(self):
        result = {"status": False, "data": {}}
        sub_command = "Chassis -1 Thermal"
        output = self.redfishtool(sub_command)
        if output:
            result["status"] = True
            result["data"] = output
        return result

    def get_temperature(self):
        result = {}
        response = self.chassis_thermal()
        if response["status"]:
            temperatures = response["data"]["Temperatures"]
            for temperature in temperatures:
                result[temperature["Name"]] = temperature["ReadingCelsius"]
        return result

    def validate_fans(self):
        result = False
        response = self.chassis_thermal()
        if response["status"]:
            fans = response["data"]["Fans"]
            for fan in fans:
                fan_status = fan["Status"]
                if (fan_status["Health"] == "OK") and (fan_status["State"] == "Enabled") and (
                        fan["Reading"] <= fan["MaxReadingRange"] and fan["Reading"] >= fan["MinReadingRange"]):
                    result = True
                else:
                    result = False
                fun_test.simple_assert(result, "Fan : {} is healthy".format(fan["Name"]))
            fun_test.log("Successfully validated all the fans")

        fun_test.test_assert(result, "Fans healthy")
        return result

    def validate_temperaure_sensors(self):
        result = False
        response = self.chassis_thermal()
        if response["status"]:
            temperature_sensors = response["data"]["Temperatures"]
            for sensor in temperature_sensors:
                sensor_status = sensor["Status"]
                if (sensor_status["Health"] == "OK") and (sensor_status["State"] == "Enabled") and sensor["ReadingCelsius"] < sensor["UpperThresholdFatal"]:
                    result = True
                else:
                    result = False
                fun_test.simple_assert(result, "Temperature Sensor : {} is healthy".format(sensor["Name"]))
            fun_test.log("validated all the temperature sensors")
        fun_test.test_assert(result, "Temperature sensors healthy")
        return result


class Platform(ApcPduTestcase, RedFishTool, IpmiTool):
    DROP_FILE_PATH = "fs_drop_version.json"

    def describe(self):
        self.set_test_details(id=1,
                              summary="",
                              steps="""""")

    def setup(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.intialize_handles()

    def run(self):
        pass

    def initialize_json_data(self):
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)
        for k, v in config_dict.iteritems():
            setattr(self, k, v)

    def initialize_test_case_variables(self, test_case_name):
        test_case_dict = getattr(self, test_case_name, {})
        if not test_case_dict:
            fun_test.critical("Unable to find the test case: {} in the json file".format(test_case_name))
        for k, v in test_case_dict.iteritems():
            setattr(self, k, v)
        fun_test.log("Initialized the test case variables: {}".format(test_case_dict))

    def initialize_job_inputs(self):
        job_inputs = fun_test.get_job_inputs()
        fun_test.log("Input: {}".format(job_inputs))
        if job_inputs:
            for k, v in job_inputs.iteritems():
                setattr(self, k, v)

    def initialize_variables(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

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
        fs.cleanup_attempted = True
        self.fpga_console_handle = fs.get_terminal()

        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.qa_02 = Linux(**service_host_spec)
        self.handles_list = {"come": self.come_handle, "bmc": self.bmc_handle, "fpga": self.fpga_handle}

    # def get_dpcsh_data_for_cmds(self, cmd, f1=0, peek=True):
    #     result = getattr(self, "f1_{}_dpc".format(f1)).command(cmd, legacy=True)
    #     fun_test.simple_assert(result["status"], "Get DPCSH Data")
    #     return result["data"]

    def get_platform_drop_information(self, system="come"):
        result = {"status": False, "data": {}}
        handle = self.handles_list[system]
        if system == "fpga":
            # FPGA sometimes is found to not run the command at once
            handle.uname()
        output = handle.uname()
        if output:
            result["status"] = True
            result["data"] = output
            fun_test.log("Drop info of system: {} {}".format(system, output))
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

    def set_platform_link(self, system="bmc", action="up", max_time=40):
        # action can be : up or down
        result = {"status": False, "data": "", "message": ""}
        if system == "bmc":
            interface = "bond0"
            self.bmc_console.ifconfig(interface, action)
            output = self.bmc_console.ifconfig(interface, action)
            if "Cannot assign" not in output or "No such device" not in output:
                result["status"] = True
                result["message"] = "set interface : {} to: {}".format(interface, action)
                result["data"] = output
            else:
                result["status"] = False
                result["message"] = "Unable to set interface : {}".format(interface)
        return result

    def switch_to_bmc_console(self, max_time=100):
        self.fpga_console_handle.switch_to_bmc_console(max_time)
        self.bmc_console = self.fpga_console_handle

    def get_platform_link(self, system="bmc", interface="bond0"):
        result = {"status": False, "link_detected": False}
        if system == "bmc":
            self.bmc_console.ethtool(interface)
            output = self.bmc_console.ethtool(interface)
            if output:
                result["status"] = True
                result["link_detected"] = True if output.get("link_detected", "no") == "yes" else False
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



    def read_dpu_data(self):
        # todo: dont know how to read the dpu data
        result = {"status": False}
        return result

    def reboot_system(self, system="come", max_wait_time=180, non_blocking=True):
        result = False
        if system == "come":
            result = self.come_handle.reboot(max_wait_time=max_wait_time, non_blocking=non_blocking)
        elif system == "bmc":
            result = self.bmc_handle.reboot(max_wait_time=max_wait_time, non_blocking=non_blocking)
        elif system == "fpga":
            result = self.fpga_handle.reboot(max_wait_time=max_wait_time, non_blocking=non_blocking)
        self.intialize_handles()
        return result

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

    def verify_drop_version(self, system):
        result = False
        drop_info = self.get_platform_drop_information(system=system)
        if drop_info["status"]:
            drop_data = drop_info["data"]
            config_dict = utils.parse_file_to_json(self.DROP_FILE_PATH)
            known_drop_info = config_dict[self.fs["name"]][system]
            result = all([drop_data[k] == v for k, v in known_drop_info.iteritems()])
            keyword = "match" if result else "mismatch"
            fun_test.log("DROP info of {} {}: \nExpected : {} \nActual: {}".format(system,
                                                                                   keyword,
                                                                                   known_drop_info,
                                                                                   drop_data))
        else:
            fun_test.log("Unable to get the drop information for system: {}".format(system))
        return result

    def check_bmc_serial_console(self):
        bmc_console_time = 40
        timer = FunTimer(max_time=bmc_console_time)
        self.fpga_console_handle.command("pwd")
        self.fpga_console_handle.switch_to_bmc_console(bmc_console_time)
        self.fpga_console_handle.ifconfig()
        ifconfig = self.fpga_console_handle.ifconfig()
        bond0 = {}
        bmc_ip = self.name_to_ip("bmc")
        for interface in ifconfig:
            if interface["interface"] == "bond0":
                bond0 = interface
                break
        if bond0.get("ipv4", "") == bmc_ip:
            result = True
            fun_test.log("BMC serial successful")
            fun_test.sleep("For BMC console to disconnect", seconds=timer.remaining_time())
        else:
            result = False
            fun_test.log("Unable to establish BMC serial")
        return result

    def name_to_ip(self, system):
        result = False
        try:
            host_name = self.fs[system]["mgmt_ip"]
            result = socket.gethostbyname(host_name)
        except Exception as ex:
            fun_test.critical(ex)
        return result

    def ensure_host_is_down(self, max_wait_time, system="come"):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        if service_host_spec:
            service_host = Linux(**service_host_spec)
        else:
            fun_test.log("Regression service host could not be instantiated", context=self.context)

        max_down_timer = FunTimer(max_time=max_wait_time)
        result = False
        ping_result = True
        while ping_result and not max_down_timer.is_expired():
            if service_host and ping_result:
                ping_result = service_host.ping(dst=self.fs[system]['mgmt_ip'], count=5)
        if not ping_result:
            result = True
        return result

    def check_if_system_is_down(self, system="come", time_out=30):
        handle = self.handles_list[system]
        system_down = handle.ensure_host_is_down(time_out)
        fun_test.test_assert(system_down, system + " is down")
        fun_test.shared_variables["{}_is_down".format(system)] = system_down

    def get_mac_n_ip_addr_info_of_systems(self):
        result = {}

        come_interface = "enp3s0f0"
        system = "come"
        come_ifconfig = self.get_interface(come_interface, system)
        result[system] = come_ifconfig

        bmc_interface = "bond0"
        system = "bmc"
        bmc_ifconfig = self.get_interface(bmc_interface, system)
        result[system] = bmc_ifconfig

        fpga_interface = "eth0"
        system = "fpga"
        fpga_ifconfig = self.get_interface(fpga_interface, system)
        result[system] = fpga_ifconfig

        return result

    def get_interface(self, interface, system="come"):
        result = False
        handle = self.handles_list[system]
        if system == "fpga":
            handle.ifconfig()
        ifconfig = handle.ifconfig()
        for each_interface in ifconfig:
            if each_interface.get("interface", "") == interface:
                result = each_interface
                break
        fun_test.simple_assert(result, "Get data for the interface :{} on system : {}".format(interface, system))
        return result

    def compare_two_dict(self, dict_1, dict_2):
        result = True
        for system, ip_data in dict_1.iteritems():
            match = all([dict_1[system][k] == dict_2[system][k] for k, v in ip_data.iteritems()])
            fun_test.simple_assert(match, "{} ip mac details match".format(system))
        fun_test.test_assert(True, "System IP and MAC matches with the data before reboot")
        return result

    def check_ipmitoll(self):
        # todo : complete this function
        pass

    def check_if_f1s_detected(self):
        fun_test.log("Check if F1_0 is detected")
        self.check_pci_dev(f1=0)

        fun_test.log("Check if F1_1 is detected")
        self.check_pci_dev(f1=1)

    def check_ssd_via_dpcsh(self):
        fun_test.log("Checking if SSD's are Active on F1_0")
        self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_0, f1=0)

        fun_test.log("Checking if SSD's are Active on F1_1")
        self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_1, f1=1)

    def check_ssd_via_fpga(self):
        self.fpga_handle.command("cd apps")
        output = self.fpga_handle.command("./regop -b 0xff200510 -s 0x100 -o 0x0 -c 5 -v 0x2f")
        output = self.fpga_handle.command("./regop -b 0xff200510 -s 0x100 -o 0x0 -c 5 -v 0x2f")
        regop_output = self.parse_fpga_ssd_output(output)
        self.verify_fpga_ssd_data(regop_output, self.expected_ssds_f1_0)

        output = self.fpga_handle.command("./regop -b 0xff200910 -s 0x100 -o 0x0 -c 5 -v 0x2f")
        regop_output = self.parse_fpga_ssd_output(output)
        self.verify_fpga_ssd_data(regop_output, self.expected_ssds_f1_1)

    def parse_fpga_ssd_output(self, output):
        result = {}
        lines = output.split("\n")
        ssd_count = 0
        for line in lines:
            match_ssd = re.search(r"OFFSET.*:(?P<hex_value>\w+)", line)
            if match_ssd:
                result[ssd_count] = match_ssd.group("hex_value")
                ssd_count += 1
        return result

    def verify_fpga_ssd_data(self, regop_output, expected_ssds_up):
        ssd_status_list = [hex_value[-3:] == "000" for ssd, hex_value in regop_output.iteritems()]
        ssds_up = ssd_status_list.count(True)
        fun_test.log("ssd status list(1-12): " + str(ssd_status_list))
        fun_test.test_assert_expected(expected=expected_ssds_up, actual=ssds_up, message="SSD count")

    def intialize_bmc_handle(self):
        self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                              ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                              ssh_password=self.fs['bmc']['mgmt_ssh_password'])
        self.bmc_handle.set_prompt_terminator(r'~ #')

    def dmesg(self, system="come", store_logs=False):
        handle = self.handles_list[system]
        output = handle.command("dmesg")
        if store_logs:
            test_case = self.__class__.__name__
            filename = fun_test.get_test_case_artifact_file_name(post_fix_name="{}_{}_logs.txt".format(test_case, system))
            fun_test.add_auxillary_file(description="{} {} logs".format(test_case, system), filename=filename)
            with open(filename, "w+") as f:
                f.write(output)
        return output

    def collect_come_logs(self):
        logs = {}
        logs["Dmesg"] = self.come_handle.command("dmesg")
        logs["Uname"] = self.come_handle.command("uname -a")
        logs["DPU information"] = self.come_handle.command("lspci -vv -d 1dad:")
        try:
            logs["F1 0 ssd info"] = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1=0, get_raw_output=True)
            logs["F1 1 ssd info"] = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1=1, get_raw_output=True)
            logs["F1 0 port info"] = self.get_dpcsh_data_for_cmds("port linkstatus", f1=0, get_raw_output=True)
            logs["F1 1 port info"] = self.get_dpcsh_data_for_cmds("port linkstatus", f1=1, get_raw_output=True)
        except:
            fun_test.log("Unable to collect the DPCSH data")
        self.add_these_logs(logs, "come")

    def collect_bmc_logs(self):
        logs = {}
        logs["Dmesg"] = self.bmc_handle.command("dmesg")
        logs["Uname"] = self.bmc_handle.command("uname -a")
        self.add_these_logs(logs, "bmc")

    def collect_fpga_logs(self):
        logs = {}
        logs["Dmesg"] = self.fpga_handle.command("dmesg")
        logs["Uname"] = self.fpga_handle.command("uname -a")
        self.add_these_logs(logs, "fpga")

    def add_these_logs(self, log_dict, system):
        result = ""
        test_case = self.__class__.__name__
        filename = fun_test.get_test_case_artifact_file_name(post_fix_name="{}_{}_logs.txt".format(test_case, system))
        fun_test.add_auxillary_file(description="{} {} logs".format(test_case, system), filename=filename)
        for k, v in log_dict.iteritems():
            result += "\n\n\n" + "-"*60 + str(k) + "-"*60 + "\n\n" + str(v)
        with open(filename, "w+") as f:
            f.write(result)

    def install_image(self, system="come"):
        #todo
        pass

    def upgrade_image(self, system="come"):
        # todo
        pass

    def downgrade_image(self):
        # todo
        pass

    def disable_fans(self):
        # todo
        pass

    def load_module(self, module_name):
        # todo
        pass

    def unload_module(self, module_name):
        # todo
        pass

    def cleanup(self):
        self.collect_come_logs()
        self.collect_bmc_logs()
        self.collect_fpga_logs()


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(Platform())
    myscript.run()
