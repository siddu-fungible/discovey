from lib.system.fun_test import *
from lib.system import utils
from asset.asset_manager import AssetManager
from collections import OrderedDict
from lib.fun.fs import *
from lib.templates.storage.storage_controller_api import StorageControllerApi
import dlipower
from lib.topology.topology_helper import TopologyHelper


class IpmiTool:
    IPMIUSERNAME = "admin"
    IPMIPASSWORD = "admin"

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_spec(fs_name)

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

    def verify_ipmi_sdr_info(self, rpm_threshold=20000, exhaust_threshold=60, inlet_threshold=55,
                             f1_temperature=75):
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
        if not getattr(self, "qa_02", False):
            self.intialize_qa_02()
        self.qa_02.command("cd /local/auto_admin/.local/bin")
        self.in_py3_env = True

    def intialize_qa_02(self):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.qa_02 = Linux(**service_host_spec)

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_spec(fs_name)

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

    def chassis(self):
        result = {"status": False, "data": {}}
        sub_command = "Chassis -1"
        output = self.redfishtool(sub_command)
        if output:
            result["status"] = True
            result["data"] = output
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


class Platform(RedFishTool, IpmiTool):
    DROP_FILE_PATH = "fs_drop_version.json"

    def __init__(self):
        self.initialize_json_data()
        self.initialize_job_inputs()
        self.initialize_variables()
        self.intialize_handles()

    def initialize_dpcsh(self):
        if getattr(self, "load_new_image", False):
            dut_index = 0
            topology_helper = TopologyHelper()
            topology_helper.set_dut_parameters(dut_index=dut_index,
                                               fs_parameters={"already_deployed": True})
            topology = topology_helper.deploy()
            fun_test.test_assert(topology, "Topology deployed")
            fun_test.shared_variables["topology"] = topology
        else:
            topology = fun_test.shared_varables["topology"]
        fs_obj = topology.get_dut_instance(index=0)
        self.dpc_f1_0 = fs_obj.get_dpc_client(0)
        self.dpc_f1_1 = fs_obj.get_dpc_client(1)


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
        self.fs = AssetManager().get_fs_spec(fs_name)

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

        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        fun_test.simple_assert(service_host_spec, "Service host spec")
        self.qa_02 = Linux(**service_host_spec)
        self.handles_list = {"come": self.come_handle, "bmc": self.bmc_handle, "fpga": self.fpga_handle}

    def initialise(sel):

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

    def verify_ifconfig(self, if_config_output):
        pass

        # if not match_ipv4:
        #     fun_test.test_assert(False, "IPv4 address available for the interface: {}".format(interface))
        # if not match_ipv6:
        #     fun_test.test_assert(False, "IPv6 address available for the interface: {}".format(interface))
        # if not(match_ehter or match_hwaddr):
        #     fun_test.test_assert(False, "Mac address available  for the interface: {}".format(interface))

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

    def switch_to_bmc_console_for(self, for_time=40):
        self.fpga_handle.switch_to_bmc_console(time_out=for_time)
        self.bmc_console = self.fpga_handle

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
        self.fpga_console_handle.switch_to_bmc_console(self.bmc_handle.ssh_username,
                                                       self.bmc_handle.ssh_password,
                                                       time_out=bmc_console_time)
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
        if result:
            data_present = self.verify_ifconfig_interface(result)
            fun_test.simple_assert(data_present, "ifconfig data verified")
        fun_test.simple_assert(result, "Get data for the interface :{} on system : {}".format(interface, system))
        return result

    def verify_ifconfig_interface(self, ifconfig_dict):
        result = True
        msg = ""
        if not ifconfig_dict["interface"]:
            result = False
            msg += "interface not present, "
        if not (ifconfig_dict["HWaddr"] or ifconfig_dict["ether"]):
            result = False
            msg += "MAC address missing, "
        if not ifconfig_dict["ipv4"]:
            result = False
            msg += "IPV4 missing, "
        if not ifconfig_dict["ipv6"]:
            result = False
            msg += "IPV6 missing, "
        if msg:
            fun_test.critical(msg)
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
        output = self.fpga_handle.command("./dump_fpga_regs.sh | grep a8")
        output = self.fpga_handle.command("./dump_fpga_regs.sh | grep a8")
        regop_output = self.parse_fpga_ssd_output(output)
        # self.verify_fpga_ssd_data(regop_output, self.expected_ssds_f1_0)

        output = self.fpga_handle.command("./dump_fpga_regs.sh | grep b0")
        regop_output = self.parse_fpga_ssd_output(output)
        self.verify_fpga_ssd_data(regop_output, self.expected_ssds_f1_1)

    def parse_fpga_ssd_output(self, output):
        result = False
        lines = output.split("\n")
        for line in lines:
            match_ssd = re.search(r"OFFSET.*:(?P<hex_value>\w+)", line)
            if match_ssd:
                hex_value = match_ssd.group("hex_value")
                ssd_data = hex_value[5]
                result = int(ssd_data, 16)
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
        try:
            logs = {}
            logs["Dmesg"] = self.come_handle.command("dmesg")
            logs["Uname"] = self.come_handle.command("uname -a")
            logs["DPU_information"] = self.come_handle.command("lspci -vv -d 1dad:")
            logs["F1_0_ssd_status"] = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1=0, get_raw_output=True)
            logs["F1_1_ssd_status"] = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1=1, get_raw_output=True)
            logs["F1_0_ssd_info"] = self.get_dpcsh_data_for_cmds("peek nvme/ssds/info", f1=0, get_raw_output=True)
            logs["F1_1_ssd_info"] = self.get_dpcsh_data_for_cmds("peek nvme/ssds/info", f1=1, get_raw_output=True)
            logs["F1_0_port_info"] = self.get_dpcsh_data_for_cmds("port linkstatus", f1=0, get_raw_output=True)
            logs["F1_1_port_info"] = self.get_dpcsh_data_for_cmds("port linkstatus", f1=1, get_raw_output=True)
            self.add_these_logs(logs, "come")
        except:
            fun_test.critical("Unable to collect the COMe logs")

    def collect_bmc_logs(self):
        try:
            logs = {}
            logs["Dmesg"] = self.bmc_handle.command("dmesg")
            logs["Uname"] = self.bmc_handle.command("uname -a")
            self.add_these_logs(logs, "bmc")
        except:
            fun_test.critical("Unable to collect the BMC logs")

    def collect_fpga_logs(self):
        try:
            logs = {}
            logs["Dmesg"] = self.fpga_handle.command("dmesg")
            logs["Uname"] = self.fpga_handle.command("uname -a")
            self.add_these_logs(logs, "fpga")
        except:
            fun_test.critical("Unable to collect the FPGA logs")

    def add_these_logs(self, log_dict, system):
        result = ""
        test_case = self.__class__.__name__
        filename = fun_test.get_test_case_artifact_file_name(post_fix_name="{}_{}_logs.txt".format(test_case, system))
        fun_test.add_auxillary_file(description="{} {} logs".format(test_case, system), filename=filename)
        for k, v in log_dict.iteritems():
            result += "\n\n\n" + "-"*60 + str(k) + "-"*60 + "\n\n" + str(v)
        with open(filename, "w+") as f:
            f.write(result)

    def initialize_basic_checks(self):
        for k, v in self.basic_checks.iteritems():
            setattr(self, k, v)

    def fs_basic_checks(self):
        # If we want to use this function you need to provide the basic checks dict in the json
        if getattr(self, "basic_checks", False):
            self.initialize_basic_checks()
        else:
            fun_test.crtical("No fs_basic_checks in the JSON provided")
            return False

        fun_test.log("Checking if COMe is UP")
        come_up = self.come_handle.ensure_host_is_up(max_wait_time=600)
        fun_test.test_assert(come_up, "COMe is UP")

        fun_test.log("Checking if BMC is UP")
        bmc_up = self.bmc_handle.ensure_host_is_up(max_wait_time=600)
        fun_test.test_assert(bmc_up, "BMC is UP")

        fun_test.log("Check if F1_0 is detected")
        self.check_pci_dev(f1=0)

        fun_test.log("Check if F1_1 is detected")
        self.check_pci_dev(f1=1)

        if getattr(self, "check_docker", False):
            self.check_expected_dockers_up()

        if getattr(self, "check_ssd", False):
            fun_test.log("Checking if SSD's are Active on F1_0")
            self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_0, f1=0)

            fun_test.log("Checking if SSD's are Active on F1_1")
            self.check_ssd_status(expected_ssds_up=self.expected_ssds_f1_1, f1=1)

        if getattr(self, "check_ports", False):
            fun_test.log("Checking if NU and HNU port's are active on F1_0")
            expected_ports_up_f1_0 = {'NU': self.expected_nu_ports_f1_0,
                                      'HNU': self.expected_hnu_ports_f1_0}
            self.check_nu_ports(f1=0, expected_ports_up=expected_ports_up_f1_0)

            expected_ports_up_f1_1 = {'NU': self.expected_nu_ports_f1_1,
                                      'HNU': self.expected_hnu_ports_f1_1}
            fun_test.log("Checking if NU and HNU port's are active on F1_1")
            self.check_nu_ports(f1=1, expected_ports_up=expected_ports_up_f1_1)

    def check_expected_dockers_up(self):
        fun_test.log("Check if all the Dockers are up")
        docker_count = 0
        max_time = 100
        timer = FunTimer(max_time)
        while not timer.is_expired():
            docker_count = self.get_docker_count()
            if docker_count == self.expected_dockers:
                break
            else:
                fun_test.sleep("{} docker to be up".format(self.expected_dockers), seconds=5)
        fun_test.test_assert_expected(expected=self.expected_dockers, actual=docker_count, message="Docker's up")

    def check_nu_ports(self,
                       expected_ports_up=None,
                       f1=0):
        result = False
        dpcsh_output = self.get_dpcsh_data_for_cmds("port linkstatus", f1)
        if dpcsh_output:
            ports_up = self.validate_link_status_out(dpcsh_output,
                                                     f1=f1,
                                                     expected_port_up=expected_ports_up)
            if ports_up:
                result = True
        fun_test.test_assert(result, "F1_{}: NU ports are present, Expected: {}".format(f1, expected_ports_up))
        return result

    def validate_link_status_out(self, link_status_out, expected_port_up, f1=0):
        result = True
        link_status = self.parse_link_status_out(link_status_out, f1=f1, iteration=getattr(self, "pc_no", 1))
        if link_status:
            for port_type, ports_list in expected_port_up.iteritems():
                for each_port in ports_list:
                    port_details = self.get_dict_for_port(port_type, each_port, link_status)
                    if port_details["xcvr"] == "ABSENT":
                        result = False
                        break
                if not result:
                    break
        else:
            result = False
        return result

    def get_dict_for_port(self, port_type, port, link_status):
        result = {}
        for lport, value in link_status.iteritems():
            if port_type == value.get("type", "") and port == value.get("port", ""):
                result = value
                break
        return result

    @staticmethod
    def parse_link_status_out(link_status_output,
                              f1=0,
                              create_table=True,
                              iteration=1):
        result = OrderedDict()
        if link_status_output:
            port_list = [i for i in link_status_output]
            port_list.sort()
            table_data_rows = []
            for each_port in port_list:
                value = link_status_output[each_port]
                each_port = each_port.replace(' ', '')
                try:
                    match_fields = re.search(r'\s?(?P<name>.*)\s+xcvr:(?P<xcvr>\w+)\s+speed:\s+(?P<speed>\w+)\s+'
                                             r'admin:\s{0,10}(?P<admin>[\w ]+)\s+SW:\s+(?P<sw>\d+)\s+HW:\s+(?P<hw>\d+)\s+'
                                             r'LPBK:\s+(?P<lpbk>\d+)\s+FEC:\s+(?P<fec>\d+)', value)
                    if match_fields:
                        one_data_set = {}
                        one_data_set['name'] = match_fields.group('name').replace(' ', '')
                        if "FPG" in one_data_set['name']:
                            one_data_set['type'] = "HNU" if "HNU" in one_data_set['name'] else "NU"
                        one_data_set['port'] = int(re.search(r'\d+', one_data_set['name']).group())
                        one_data_set['xcvr'] = match_fields.group('xcvr')
                        one_data_set['speed'] = match_fields.group('speed')
                        one_data_set['admin'] = match_fields.group('admin')
                        one_data_set['SW'] = int(match_fields.group('sw'))
                        one_data_set['HW'] = int(match_fields.group('hw'))
                        one_data_set['LPBK'] = match_fields.group('lpbk')
                        one_data_set['FEC'] = match_fields.group('fec')
                        table_data_rows.append([one_data_set['name'], one_data_set['xcvr'], one_data_set['speed'],
                                                one_data_set['admin'], one_data_set['SW'], one_data_set['HW'],
                                                one_data_set['LPBK'], one_data_set['FEC']])
                        result[each_port] = one_data_set
                except:
                    fun_test.log("Unable to parse the port linkstatus output")
            if create_table:
                try:
                    table_data_headers = ["Name", "xcvr", "speed", "admin", "sw", "hw", "lpbk", "fec"]
                    table_data = {"headers": table_data_headers, "rows": table_data_rows}
                    fun_test.add_table(panel_header="Link stats table iteration {}".format(iteration),
                                       table_name="Fs = {}".format(f1), table_data=table_data)
                except:
                    fun_test.log("Unable to create the table")
        return result

    def get_docker_count(self):
        output = self.come_handle.sudo_command("docker ps -a")
        num_docker = self.docker_ps_a_wrapper(output)
        return num_docker

    def check_ssd_status(self, expected_ssds_up, f1=0):
        result = False
        if expected_ssds_up == 0:
            return True
        dpcsh_data = self.get_dpcsh_data_for_cmds("peek storage/devices/nvme/ssds", f1)
        if dpcsh_data:
            validate = self.validate_ssd_status(dpcsh_data, expected_ssds_up, f1)
            if validate:
                result = True
        fun_test.test_assert(result, "F1_{}: SSD's ONLINE".format(f1))
        return result

    def get_dpcsh_data_for_cmds(self, cmd, f1=0, command_duration=10):
        split_cmd = cmd.split(" ", 1)
        verb = split_cmd[0]
        data = split_cmd[1]
        if not getattr(self, "dpc_f1_0", False):
            self.load_new_image = True
            self.initialize_dpcsh()
        if f1 == 0:
            output = self.dpc_f1_0.json_execute(verb=verb, data=data, command_duration=command_duration)
        elif f1 == 1:
            output = self.dpc_f1_1.json_execute(verb=verb, data=data, command_duration=command_duration)
        result = output["data"]
        return result


    # def get_dpcsh_data_for_cmds(self, cmd, f1=0, get_raw_output=False):
    #     result = False
    #     try:
    #         self.come_handle.enter_sudo()
    #         output = self.come_handle.command("cd /opt/fungible/FunSDK/bin/Linux/dpcsh")
    #         if "No such file" in output:
    #             self.come_handle.command("cd /tmp/workspace/FunSDK/bin/Linux")
    #         run_cmd = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout=60000 --nocli {}".format(f1, cmd)
    #         output = self.come_handle.command(run_cmd)
    #         if get_raw_output:
    #             return output
    #         result = self.parse_dpcsh_output(output)
    #         if "result" in result:
    #             result = result["result"]
    #         self.come_handle.exit_sudo()
    #     except:
    #         fun_test.log("Unable to get the DPCSH data for command: {}".format(cmd))
    #     return result

    @staticmethod
    def parse_dpcsh_output(data):
        result = {}
        data = data.replace('\r', '')
        data = data.replace('\n', '')
        # \s+=>\s+(?P<json_output>{.*})
        match_output = re.search(r'output\s+=>\s+(?P<json_output>{.*})', data)
        if match_output:
            try:
                result = json.loads(match_output.group('json_output'))
                if "result" in result:
                    result = result["result"]
            except:
                fun_test.log("Unable to parse the output obtained from dpcsh")
        return result

    @staticmethod
    def validate_ssd_status(dpcsh_data, expected_ssd_count, f1):
        result = True
        if dpcsh_data:
            ssds_count = len(dpcsh_data)
            fun_test.test_assert_expected(expected=expected_ssd_count,
                                          actual=ssds_count,
                                          message="F1_{}: SSD count".format(f1))
            for each_ssd, value in dpcsh_data.iteritems():
                if "device state" in value:
                    if not (value["device state"] == "DEV_ONLINE"):
                        result = False
        return result

    @staticmethod
    def docker_ps_a_wrapper(output):
        # Just a basic function , will have to advance it using regex
        lines = output.split("\n")
        lines.pop(0)
        number_of_dockers = len(lines)
        print ("number_of_dockers: %s" % number_of_dockers)
        return number_of_dockers

    def check_pci_dev(self, f1=0):
        result = True
        bdf_list = ['04:00.']
        if f1 == 1:
            bdf_list = ['06:00.', '05:00.']
        for bdf in bdf_list:
            lspci_output = self.come_handle.command("lspci -d 1dad: | grep {}".format(bdf), timeout=120)
            if lspci_output:
                sections = ['Ethernet controller', 'Non-Volatile', 'Unassigned class', 'encryption device']
                result = all([s in lspci_output for s in sections])
                if result:
                    break
            else:
                result = False

        fun_test.test_assert(result, "F1_{} PCIe devices detected".format(f1))
        return result

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

    def collect_logs(self):
        self.collect_come_logs()
        self.collect_bmc_logs()
        self.collect_fpga_logs()

    def enter_docker(self, f1=0):
        result = True
        self.come_handle.enter_sudo()
        self.come_handle.command("docker exec -it F1-{} bash".format(f1))
        return result

    def exit_docker(self):
        self.come_handle.command("exit")

    def linkstatus_via_docker(self, f1=0):
        result = False
        self.enter_docker(f1)
        self.come_handle.ifconfig()
        result = self.come_handle.ifconfig()
        self.exit_docker()
        return result

    def start_snake_test_verify(self, runtime=60):
        self.come_handle.enter_sudo()
        output = self.come_handle.command("./system_test.sh {}".format(runtime), timeout=600)
        self.verify_snake_test(output)
        self.come_handle.exit_sudo()

    def verify_snake_test(self, output):
        f1_0_network_result = False
        f1_1_network_result = False
        f1_0_nt_match = re.search(r'F1-0:\s+Network\s+test\s+(?P<result>\w+)', output)
        f1_1_nt_match = re.search(r'F1-1:\s+Network\s+test\s+(?P<result>\w+)', output)
        if f1_0_nt_match:
            result = f1_0_nt_match.group("result")
            f1_0_network_result = True if result == "PASS" else False
        if f1_1_nt_match:
            result = f1_1_nt_match.group("result")
            f1_1_network_result = True if result == "PASS" else False

        fun_test.test_assert(f1_0_network_result, "Snake test on F1_0")
        fun_test.test_assert(f1_1_network_result, "Snake test on F1_1")

    def verify_port_link_status(self, f1=0, port_num_list=[0], speed="100g", verify_sw=True, verify_hw=True, verfiy_fec=False, strict=True):
        link_status = self.get_dpcsh_data_for_cmds("port linkstatus", f1=0)
        link_status_json = self.parse_link_status_out(link_status, f1, create_table=False)
        result_list = []
        for port_num in port_num_list:
            result = self.verify_link_status_json(link_status_json, port_num, speed, verify_sw, verify_hw, verfiy_fec)
            result_list.append(result)
            if strict:
                fun_test.test_assert(result, "Validate port : {}".format(port_num))
        final_result = all(result_list)
        return final_result

    def verify_link_status_json(self, link_status_json, port_num, speed, verify_sw, verify_hw, verfiy_fec,
                                verify_xcvr=True):
        result = True
        key = "lport-{}".format(port_num)
        link_details = link_status_json[key]
        speed = speed.upper()
        if verify_sw and link_details["SW"] != 1:
            result = False
        if verify_hw and link_details["HW"] != 1:
            result = False
        if verfiy_fec and link_details["FEC"] != 1:
            result = False
        if verify_xcvr and link_details["xcvr"] != "PRESENT":
            result = False
        if link_details["speed"] != speed:
            result = False
        return result

    def brk_mode_speed_conversion(self, speed=None, brkmode=None):
        result = None
        if speed == "100g":
            result = "no_brk_100g"
        if speed == "25g":
            result = "brk_4x25g"
        if brkmode == "brk_4x25g":
            result = "25g"
        if brkmode == "no_brk_100g":
            result = "100g"
        return result


    def split_n_verify_port_link_status(self, port_num, speed, f1=0, verify_sw=True, verify_hw=True, verfiy_fec=False,
                                        verify_using_ethtool=True):
        brkmode = self.brk_mode_speed_conversion(speed=speed)
        if speed == "100g":
            port_num_list = [port_num]
            self.port_break_dpcsh(port_num, brkmode)
        elif speed == "25g":
            port_num_list = range(port_num, port_num + 8)
            self.port_break_dpcsh(port_num, brkmode)

            port_num_next = port_num + 4
            self.port_break_dpcsh(port_num_next, brkmode)

        self.verify_port_link_status(f1, port_num_list, speed, verify_sw=verify_sw, verify_hw=verify_hw,
                                     verfiy_fec=verfiy_fec)
        if verify_using_ethtool:
            self.verify_port_link_status_ethtool(f1, port_num_list, speed)

    def verify_port_link_status_ethtool(self, f1, port_num_list=[0], speed="100g", link_detected="yes"):
        docker = self.come_handle.get_funcp_container(f1)
        for fpg_port in port_num_list:
            result = True
            fpg = "fpg" + str(fpg_port)
            response = docker.ethtool(fpg)
            fun_test.test_assert_expected(link_detected, response["link_detected"], fpg + " link detected status")
            eth_speed = str(int(re.search(r"\d+", response["speed"]).group())/1000) + "g"
            fun_test.test_assert_expected(speed, eth_speed, fpg + "speed")
        docker.disconnect()

    def port_break_dpcsh(self, port_num=0, brkmode="no_brk_100g", f1=0):
        port_num_list = [port_num]
        speed = self.brk_mode_speed_conversion(brkmode=brkmode)
        fpg = "fpg" + str(port_num)

        port_break_cmd = 'port breakoutset {"portnum":%s, "shape":0} {"brkmode":%s}' % (port_num, brkmode)
        self.get_dpcsh_data_for_cmds(f1=f1, cmd=port_break_cmd)
        fun_test.sleep("Port breakout set", seconds=10)

        result = self.verify_port_link_status(f1, port_num_list, speed, verify_sw=False, verify_hw=False, verfiy_fec=False, strict=False)
        fun_test.test_assert(result, "{} set to brkmode: {}".format(fpg, brkmode))

    def docker_bringup_all_fpg_ports(self, f1):
        docker = self.come_handle.get_funcp_container(f1)
        cmd = "for e in $(ifconfig -a | grep fpg | awk -F: '{print $1}'); do ifconfig $e up; done"
        docker.command(cmd)
        fun_test.sleep("All the fpg ports to be up", seconds=20)


class StorageApi:
    def __init__(self):
        if not getattr(self, "fs", False):
            self.initialise_fs()
        if not getattr(self, "come_handle", False):
            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
        self.sc_api = StorageControllerApi(self.fs["come"]["mgmt_ip"])
        HOSTS_ASSET = ASSET_DIR + "/hosts.json"
        self.hosts_asset = fun_test.parse_file_to_json(file_name=HOSTS_ASSET)

    def handle_volume_deco(func):
        def function_wrapper(self):
            try:
                func(self)
            except Exception as ex:
                # fun_test.critical(ex)
                self.detach_delete_volume()
        return function_wrapper

    @handle_volume_deco
    def create_volume_and_run_fio(self):
        if not getattr(self, "volume_creation_details", False):
            fun_test.critical("Volume creation details JSON missing")
            return
        self.pool_uuid = self.get_pool_id()
        self.volume_creation_details["pool_uuid"] = self.pool_uuid
        response = self.sc_api.create_stripe_volume(**self.volume_creation_details)
        fun_test.log("volume creation response:{}".format(response))
        self.verify_volume_creation(response)
        self.uuid = response["data"]["uuid"]
        response = self.sc_api.volume_attach_pcie(self.uuid, remote_ip=self.fs["come"]["mgmt_ip"])
        fun_test.log("volume attach response:{}".format(response))
        self.verify_volume_attach_detach(response, "attach")
        self.attach_info = response["data"]
        self.nvme_device = self.get_nvme(self.come_handle, self.come_handle.host_ip)
        thread_details = self.start_fio_and_verify(self.fio_read)
        self.join_fio_thread(thread_details)
        self.detach_delete_volume()

    def join_fio_thread(self, thread_details):
        for k, v in thread_details.iteritems():
            fun_test.join_thread(v)
            fun_test.test_assert(True, "Completed {}".format(k))

    def start_fio_and_verify(self, fio_params):
        thread_details = {}
        host_name = self.come_handle.host_ip
        run_time = fio_params.get("runtime", 120)
        namespace = re.findall(r'\d', self.nvme_device)
        iostat_device = "nvme" + namespace[0] + "c2n" + namespace[1]
        thread_details["check"] = fun_test.execute_thread_after(func=self.check_traffic,
                                                                time_in_seconds=5,
                                                                device="nvme0c2n1",
                                                                fio_run_time=run_time)
        thread_details["fio"] = fun_test.execute_thread_after(func=self.start_fio,
                                                              time_in_seconds=7,
                                                              fio_params=fio_params,
                                                              run_time=run_time,
                                                              device=self.nvme_device)
        return thread_details

    def start_fio(self, fio_params, run_time, device):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        come_handle.pcie_fio(timeout=run_time+20,
                             filename=device,
                             **fio_params)
        come_handle.destroy()

    def check_traffic(self, device, fio_run_time, interval=10):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        device_name = device.replace("/dev/", '')
        count = fio_run_time / interval
        output_iostat = come_handle.iostat(device=device, interval=interval, count=count, background=False)
        self.ensure_io_running(device_name, output_iostat, "COMe")
        come_handle.destroy()

    def detach_delete_volume(self):
        if getattr(self, "attach_info", False):
            response = self.sc_api.detach_volume(self.attach_info["uuid"])
            fun_test.log("volume detach response:{}".format(response))
            self.verify_volume_attach_detach(response, "detach")

        if getattr(self, "uuid", False):
            response = self.sc_api.delete_volume(self.uuid)
            fun_test.log("Volume delete response: " + str(response))
            fun_test.test_assert(response["status"],
                                 "{} Volume deleted successfully".format(self.volume_creation_details["name"]))

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_spec(fs_name)

    def get_pool_id(self):
        response = self.sc_api.get_pools()
        fun_test.log("pools log: {}".format(response))
        pool_id = str(response['data'].keys()[0])
        fun_test.log("pool_id: {}".format(pool_id))
        return pool_id

    def verify_volume_attach_detach(self, response, action="attach"):
        result = True
        if not response["status"]:
            result = False
        if result and (not "Success" in response["message"]):
            result = False
        fun_test.test_assert(result, "{} Volume {}ed successfully".format(self.volume_creation_details["name"], action))
        return result

    def get_nvme(self, handle, host_name):
        result = False
        output_lsblk = handle.sudo_command("nvme list")
        lines = output_lsblk.split("\n")
        for line in lines:
            match_nvme_list = re.search(r'(?P<nvme_device>/dev/nvme\w+n\w+)', line)
            if match_nvme_list:
                result = True
                nvme_device = match_nvme_list.group("nvme_device")
        fun_test.test_assert(result, "Host: {} nvme: {} verified NVME connect".format(host_name, nvme_device))
        return nvme_device

    def verify_volume_creation(self, response):
        result = True
        if not response["status"]:
            result = False
        if not "successful" in response["message"]:
            result = False
        fun_test.test_assert(result, "{} Volume created successfully".format(self.volume_creation_details["name"]))
        return result

    @staticmethod
    def ensure_io_running(device, output_iostat, host_name):
        fio_read = False
        fio_write = False
        result = False
        lines = output_iostat.split("\n")

        # Remove the initial iostat values
        lines_clean = lines[8:]

        iostat_sum = [0, 0, 0, 0, 0]
        for line in lines_clean:
            match_nvme = re.search(r'{}'.format(device), line)
            if match_nvme:
                match_numbers = re.findall(r'(?<= )[\d.]+', line)
                if len(match_numbers) == 5:
                    numbers = map(float, match_numbers)
                    iostat_sum = [sum(x) for x in zip(numbers, iostat_sum)]

        # read
        fun_test.log("IOstat sum: {}".format(iostat_sum))
        if iostat_sum[1] > 20:
            fio_read = True
        # fun_test.test_assert(fio_read, "{} reads are resumed".format(host_name))

        # write
        if iostat_sum[2] > 20:
            fio_write = True
        # fun_test.test_assert(fio_write, "{} writes are resumed".format(host_name))

        if fio_read or fio_write:
            result = True
        fun_test.test_assert(result, "Host: {}  IO running".format(host_name))


class RebootFs:

    def __init__(self, fs_spec):
        self.fs = fs_spec

    def apc_pdu_reboot(self):
        '''
        1. check if COMe is up, than power off.
        2. check COMe now, if its down tha power on
        :param come_handle:
        :return:
        '''
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        apc_info = self.fs.get("apc_info")
        outlet_no = apc_info.get("outlet_number")
        try:
            fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))

            fun_test.log("Checking if COMe is UP")
            come_up = come_handle.ensure_host_is_up()
            fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                    self.to_str(come_up), True, come_up)
            come_handle.destroy()

            apc_pdu = ApcPdu(host_ip=apc_info['host_ip'], username=apc_info['username'],
                             password=apc_info['password'])
            fun_test.sleep(message="Wait for few seconds after connect with apc power rack", seconds=5)

            apc_outlet_off_msg = apc_pdu.outlet_off(outlet_no)
            fun_test.log("APC PDU outlet off mesg {}".format(apc_outlet_off_msg))
            outlet_off = self.match_success(apc_outlet_off_msg)
            fun_test.test_assert(outlet_off, "Power down FS")

            fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

            fun_test.log("Checking if COMe is down")
            come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
            fun_test.test_assert(come_down, "COMe is Down")

            apc_outlet_on_msg = apc_pdu.outlet_on(outlet_no)
            fun_test.log("APC PDU outlet on message {}".format(apc_outlet_on_msg))
            outlet_on = self.match_success(apc_outlet_on_msg)
            fun_test.test_assert(outlet_on, "Power on FS")

            apc_pdu.disconnect()
        except Exception as ex:
            fun_test.critical(ex)

        return

    @staticmethod
    def to_str(boolean_data):
        if boolean_data:
            return FunTest.PASSED
        return FunTest.FAILED

    @staticmethod
    def match_success(output_message):
        result = False
        match_success = re.search(r'Success', output_message)
        if match_success:
            result = True
        return result

    def dli_pdu_reboot(self):
        come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                           ssh_username=self.fs['come']['mgmt_ssh_username'],
                           ssh_password=self.fs['come']['mgmt_ssh_password'])
        dli_info = self.fs.get("dli_info")
        outlet_no = dli_info.get("outlet_number")

        fun_test.log("Iteration no: {} out of {}".format(self.pc_no + 1, self.iterations))

        fun_test.log("Checking if COMe is UP")
        come_up = come_handle.ensure_host_is_up()
        fun_test.add_checkpoint("COMe is UP (before switching off fs outlet)",
                                self.to_str(come_up), True, come_up)
        come_handle.destroy()

        dli_pdu = DliPower(hostname=dli_info['host_ip'], userid=dli_info['username'], password=dli_info['password'])

        dli_outlet_off_result = dli_pdu.outlet_off(outlet_no)
        fun_test.log("DLI PDU outlet off result: {}".format(dli_outlet_off_result))
        fun_test.test_assert(dli_outlet_off_result, "Power down FS")

        fun_test.sleep(message="Wait for few seconds after switching off fs outlet", seconds=15)

        fun_test.log("Checking if COMe is down")
        come_down = not (come_handle.ensure_host_is_up(max_wait_time=15))
        fun_test.test_assert(come_down, "COMe is Down")

        dli_outlet_on_result = dli_pdu.outlet_on(outlet_no)
        fun_test.log("DLI PDU outlet on message {}".format(dli_outlet_on_result))
        fun_test.test_assert(dli_outlet_on_result, "Power on FS")

        return


class DliPower:

    def __init__(self, hostname, userid="admin", password="Precious1*"):
        self.switch = dlipower.PowerSwitch(hostname=hostname, userid=userid, password=password)

    def outlet_on(self, outlet):
        # Reason for implementing this is to verify that the outlet is for sure turned on/off
        # >> switch.off(3) >> False
        # with this package False = Success. https://pypi.org/project/dlipower/0.2.33/
        result = True
        status = self.switch_status(outlet)
        if not status == "ON":
            self.switch.on(outlet)
            fun_test.sleep("After powering on")
            status = self.switch_status(outlet)
            if status == "ON":
                result = True
            else:
                result = False
        return result

    def outlet_off(self, outlet):
        result = True
        status = self.switch_status(outlet)
        if not status == "OFF":
            self.switch.off(outlet)
            status = self.switch_status(outlet)
            if status == "OFF":
                result = True
            else:
                result = False
        return result

    def switch_status(self, outlet):
        result = self.switch.status(outlet)
        return result

    def cycle(self, outlet):
        result = self.switch.cycle(outlet)
        return result

    def get_outlet_name(self, outlet):
        name = self.switch.get_outlet_name(outlet)
        return name

class PwmTachtool:
    DEVICE_ID = 0

    def __init__(self, bmc_handle=None):
        if bmc_handle:
            self.bmc_handle = bmc_handle
        else:
            if not getattr(self, "fs", False):
                self.initialise_fs()
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_spec(fs_name)

    def pwmtachtool(self, cmd):
        pwm_cmd = "pwmtachtool 0 " + cmd
        result = self.bmc_handle.command(pwm_cmd)
        return result

    def set_pwm_dutycycle(self, fan, speed):
        cmd = "--set-pwm-dutycycle %s %s" % (fan, speed)
        result = self.pwmtachtool(cmd)
        fun_test.sleep("To set fan speed", seconds=3)
        fun_test.log("Fan {} speed set to dutycycle: {}".format(fan, speed))
        return result

    def get_fan_speed(self, fan):
        speed = False
        cmd = "--get-fan-speed {}".format(fan)
        result = self.pwmtachtool(cmd)
        match_speed = re.search(r"speed\s+is\s+(?P<speed>\d+)", result)
        if match_speed:
            speed = int(match_speed.group("speed"))
            fun_test.log("Fan {} speed: {}".format(fan, speed))
        return speed

