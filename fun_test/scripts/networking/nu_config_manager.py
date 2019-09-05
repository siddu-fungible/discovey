from lib.system.fun_test import *
from collections import OrderedDict
import re
import json


class NuConfigManager(object):
    NU_CONFIGS_SPEC = SCRIPTS_DIR + "/networking/nu_configs.json"
    SPIRENT_TRAFFIC_GENERATOR_ASSETS = ASSET_DIR + "/traffic_generator_hosts.json"
    DUT_TYPE_QFX = "qfx"
    DUT_TYPE_F1 = "f1"
    DUT_TYPE_PALLADIUM = "palladium"
    DUT_INTERFACE_MODE_25G = "25G"
    DUT_INTERFACE_MODE_50G = "50G"
    DUT_INTERFACE_MODE_100G = "100G"
    CHASSIS_TYPE_PHYSICAL = "physical"
    CHASSIS_TYPE_VIRTUAL = "virtual"
    TRAFFIC_GENERATOR_TYPE_SPIRENT = "spirent_traffic_generator"
    TRANSIT_FLOW_TYPE = "transit_flow"
    CC_FLOW_TYPE = "cc_flow"
    VP_FLOW_TYPE = "vp_flow"
    SAMPLE_FLOW_TYPE = "sample_flow"
    ACL_FLOW_TYPE = "acl_flow"
    FLOW_DIRECTION_NU_NU = "NU_NU"
    FLOW_DIRECTION_NU_NU_100G = "NU_NU_100G"
    FLOW_DIRECTION_FPG_CC = "NU_CC"
    FLOW_DIRECTION_CC_FPG = "CC_NU"
    FLOW_DIRECTION_HU_CC = "HU_CC"
    FLOW_DIRECTION_HNU_CC = "HNU_CC"
    FLOW_DIRECTION_FPG_HNU = "NU_HNU"
    FLOW_DIRECTION_FCP_HNU_HNU = "HNU_HNU_FCP"
    FLOW_DIRECTION_HNU_FPG = "HNU_NU"
    FLOW_DIRECTION_FPG_HU = "NU_HU"
    FLOW_DIRECTION_HU_FPG = "HU_NU"
    FLOW_DIRECTION_HNU_HNU = "HNU_HNU_NFCP"
    FLOW_DIRECTION_ALL = "ALL"
    FLOW_DIRECTION = "flow_direction"
    ECMP_FLOW_TYPE='ecmp_flow'
    FLOW_DIRECTION_ECMP = "FPG_ECMP"
    IP_VERSION = "ip_version"
    SPRAY_ENABLE = "spray_enable"
    INTEGRATION_FLOW_TYPE = "integration_flow"
    DUT_TYPE = None
    CHASSIS_TYPE = None
    F1_INDEX_1 = 1  # Will ignore F1_1 and boot F1_0 during bootup
    F1_INDEX_0 = 0  # Will ignore F1_0 and boot F1_1 during bootup
    F1_INDEX = None

    def __init__(self):
        self.get_dut_type()
        self.get_chassis_type()
        self.get_speed()

    def get_chassis_type(self):
        if self.DUT_TYPE == self.DUT_TYPE_F1:
            self.CHASSIS_TYPE = self.CHASSIS_TYPE_PHYSICAL
        else:
            self.CHASSIS_TYPE = self.CHASSIS_TYPE_VIRTUAL
        return self.CHASSIS_TYPE

    def get_speed(self):
        self.SPEED = None
        job_inputs = fun_test.get_job_inputs()
        if job_inputs and 'speed' in job_inputs:
            set_speed = job_inputs['speed'].split('_')[1]
            if set_speed[-1] == 'G':
                self.SPEED = int(set_speed[:-1]) * 1000
        return self.SPEED

    def get_f1_index(self):
        self.F1_INDEX = None
        job_inputs = fun_test.get_job_inputs()
        if job_inputs and 'disable_f1_index' in job_inputs:
            if int(job_inputs['disable_f1_index']) == self.F1_INDEX_0:
                self.F1_INDEX = self.F1_INDEX_0
            elif int(job_inputs['disable_f1_index']) == self.F1_INDEX_1:
                self.F1_INDEX = self.F1_INDEX_1
        else:
            self.F1_INDEX = None
        return self.F1_INDEX

    def _parse_file_to_json_in_order(self, file_name):
        result = None
        try:
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = json.loads(contents, object_pairs_hook=OrderedDict)
        except Exception as ex:
            scheduler_logger.critical(str(ex))
        return result

    def _get_nu_configs(self):
        all_configs = []
        try:
            all_configs = self._parse_file_to_json_in_order(file_name=self.NU_CONFIGS_SPEC)
            fun_test.simple_assert(all_configs, "Read Configs")
        except Exception as ex:
            fun_test.critical(str(ex))
        return all_configs

    def read_dut_config(self, dut_type=None, flow_type=TRANSIT_FLOW_TYPE, flow_direction=FLOW_DIRECTION_NU_NU):
        result = {}
        try:
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            for config in configs:
                if config["type"] == self.DUT_TYPE:
                    result = config
                    job_environment = fun_test.get_job_environment()
                    if type(job_environment) == unicode:
                        job_environment = json.loads(job_environment)
                    if 'UART_HOST' in job_environment and 'UART_TCP_PORT_0' in job_environment:
                        result['dpcsh_tcp_proxy_ip'] = job_environment['UART_HOST']
                        result['dpcsh_tcp_proxy_port'] = int(job_environment['UART_TCP_PORT_0'])
                    if self.F1_INDEX == self.F1_INDEX_1:
                        result['dpcsh_tcp_proxy_ip'] = result['dpcsh_tcp_proxy_ip']
                        result['dpcsh_tcp_proxy_port'] = result['dpcsh_tcp_proxy_port1']
                    elif self.F1_INDEX == self.F1_INDEX_0:
                        result['dpcsh_tcp_proxy_ip'] = result['dpcsh_tcp_proxy_ip']
                        result['dpcsh_tcp_proxy_port'] = result['dpcsh_tcp_proxy_port2']
                    else:
                        result['dpcsh_tcp_proxy_ip'] = result['dpcsh_tcp_proxy_ip']
                        result['dpcsh_tcp_proxy_port'] = result['dpcsh_tcp_proxy_port1']
                    break
            dut_spirent_map = self.read_dut_spirent_map()
            result['ports'] = []
            if flow_type == self.TRANSIT_FLOW_TYPE:
                for key, value in (dut_spirent_map[flow_type][flow_direction].iteritems()):
                    m = re.search(r'(\d+)', key)
                    if m:
                        result['ports'].append(int(m.group(1)))
            elif flow_type == self.CC_FLOW_TYPE:
                if flow_direction:
                    cc_flow_direction = flow_direction
                else:
                    cc_flow_direction = self.FLOW_DIRECTION_FPG_CC

                for key, value in sorted(dut_spirent_map[flow_type][cc_flow_direction].iteritems()):
                    m = re.search(r'(\d+)', key)
                    if m:
                        result['ports'].append(int(m.group(1)))
            elif flow_type == self.VP_FLOW_TYPE:
                if flow_direction:
                    vp_flow_direction = flow_direction
                else:
                    vp_flow_direction = self.FLOW_DIRECTION_FPG_HNU
                for key, value in (dut_spirent_map[flow_type][vp_flow_direction].iteritems()):
                    m = re.search(r'(\d+)', key)
                    if m:
                        result['ports'].append(int(m.group(1)))
            elif flow_type == self.SAMPLE_FLOW_TYPE or flow_type == self.ACL_FLOW_TYPE or flow_type == self.ECMP_FLOW_TYPE:
                for key, value in (dut_spirent_map[flow_type][flow_direction].iteritems()):
                    m = re.search(r'(\d+)', key)
                    if m:
                        result['ports'].append(int(m.group(1)))
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def read_dut_spirent_map(self):
        result = OrderedDict()
        try:
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            if self.DUT_TYPE == self.DUT_TYPE_F1:
                name = "f1_spirent_map"
            else:
                name = "palladium_spirent_map"
            for config in configs:
                if config["name"] == name:
                    result.update(config)
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def read_integration_flow_config(self, cc_flow_direction, vp_flow_direction):
        result = {}
        try:
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            for config in configs:
                if config["type"] == self.DUT_TYPE_PALLADIUM:
                    result = config
                    break
            dut_spirent_map = self.read_dut_spirent_map()
            result['ports'] = {self.TRANSIT_FLOW_TYPE: [], self.CC_FLOW_TYPE: [], self.VP_FLOW_TYPE: []}
            # Fetching Transit DUT ports
            for key, value in sorted(dut_spirent_map[self.TRANSIT_FLOW_TYPE].items()):
                m = re.search(r'(\d+)', key)
                if m:
                    result['ports'][self.TRANSIT_FLOW_TYPE].append(int(m.group(1)))

            # Fetching CC DUT ports
            for key, value in sorted(dut_spirent_map[self.CC_FLOW_TYPE][cc_flow_direction].iteritems()):
                m = re.search(r'(\d+)', key)
                if m:
                    result['ports'][self.TRANSIT_FLOW_TYPE].append(int(m.group(1)))

            # Fetching VP DUT ports
            for key, value in sorted(dut_spirent_map[self.VP_FLOW_TYPE][vp_flow_direction].iteritems()):
                m = re.search(r'(\d+)', key)
                if m:
                    result['ports'][self.TRANSIT_FLOW_TYPE].append(int(m.group(1)))
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def read_traffic_generator_asset(self):
        spirent_config = {}
        try:
            configs = self._parse_file_to_json_in_order(file_name=self.SPIRENT_TRAFFIC_GENERATOR_ASSETS)
            fun_test.simple_assert(expression=configs, message="Read Config File")
            for config in configs:
                if config['name'] == "spirent_test_center":
                    spirent_config = config
                    break
            fun_test.debug("Found: %s" % spirent_config)
        except Exception as ex:
            fun_test.critical(str(ex))
        return spirent_config

    def read_traffic_generator_config(self, traffic_generator_type=TRAFFIC_GENERATOR_TYPE_SPIRENT):
        result = {}
        try:
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            for config in configs:
                if config['type'] == traffic_generator_type:
                    result = config
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_traffic_routes_by_chassis_type(self, spirent_config, ip_version="ipv4", overlay=False):
        routes_dict = {'l3_config': None, 'routermac': None, 'status': False}
        try:
            if overlay:
                routes_dict['l3_config'] = spirent_config[self.CHASSIS_TYPE]['overlay_routes'][ip_version]
            else:
                routes_dict['l3_config'] = spirent_config[self.CHASSIS_TYPE]['routes'][ip_version]
            routes_dict['routermac'] = spirent_config[self.CHASSIS_TYPE]['routermac']
            routes_dict['status'] = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return routes_dict

    def get_spirent_dut_port_mapper(self, flow_type=TRANSIT_FLOW_TYPE, no_of_ports_needed=2,
                                    flow_direction=FLOW_DIRECTION_NU_NU):
        result = OrderedDict()
        try:
            dut_spirent_map = self.read_dut_spirent_map()
            spirent_assets = self.read_traffic_generator_asset()
            if flow_type == self.TRANSIT_FLOW_TYPE:
                fun_test.log("Fetching NU Transit Flow Map")
                fun_test.simple_assert(len(dut_spirent_map[flow_type][flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type])))
                count = 0
                for key, value in (dut_spirent_map[flow_type][flow_direction].iteritems()):
                    if count == no_of_ports_needed:
                        break
                    fun_test.debug("FPG Port: %s connected to Spirent Port: %s" % (key, value))
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1

            elif flow_type == self.CC_FLOW_TYPE:
                if flow_direction:
                    cc_flow_direction = flow_direction
                else:
                    cc_flow_direction = self.FLOW_DIRECTION_FPG_CC
                fun_test.log("Fetching NU CC path map. Traffic Direction: %s" % cc_flow_direction)
                fun_test.simple_assert(len(dut_spirent_map[flow_type][cc_flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type][cc_flow_direction])))
                count = 0
                for key, value in sorted(dut_spirent_map[flow_type][cc_flow_direction].iteritems()):
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1
            elif flow_type == self.VP_FLOW_TYPE:
                if flow_direction:
                    vp_flow_direction = flow_direction
                else:
                    vp_flow_direction = self.FLOW_DIRECTION_FPG_HNU
                fun_test.log("Fetching NU VP path map. Traffic Direction: %s" % vp_flow_direction)
                fun_test.simple_assert(len(dut_spirent_map[flow_type][vp_flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type][vp_flow_direction])))
                count = 0
                for key, value in dut_spirent_map[flow_type][vp_flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1
            elif flow_type == self.INTEGRATION_FLOW_TYPE:
                if type(flow_direction) != dict:
                    raise Exception("Please provide dict with diff flow directions. E.g {'cc': 'HU_CC', 'vp': 'FPG_HU'}")
                cc_flow_direction = flow_direction['cc']
                vp_flow_direction = flow_direction['vp']
                # Fetching Transit Flow
                count = 0
                for key, value in dut_spirent_map[self.TRANSIT_FLOW_TYPE].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1

                # Fetching CC Flow
                count = 0
                for key, value in dut_spirent_map[self.CC_FLOW_TYPE][cc_flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception(
                            "Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1

                # Fetching VP Flow
                count = 0
                for key, value in dut_spirent_map[self.VP_FLOW_TYPE][vp_flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception(
                            "Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1
            elif flow_type == self.SAMPLE_FLOW_TYPE:
                fun_test.log("Fetching NU VP path map. Traffic Direction: %s" % flow_direction)
                fun_test.simple_assert(len(dut_spirent_map[flow_type][flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type][flow_direction])))
                count = 0
                for key, value in dut_spirent_map[flow_type][flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1
            elif flow_type == self.ACL_FLOW_TYPE:
                fun_test.log("Fetching NU VP path map. Traffic Direction: %s" % flow_direction)
                fun_test.simple_assert(len(dut_spirent_map[flow_type][flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type][flow_direction])))
                count = 0
                for key, value in dut_spirent_map[flow_type][flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1
            
            elif flow_type == self.ECMP_FLOW_TYPE:
                fun_test.log("Fetching NU VP path map. Traffic Direction: %s" % flow_direction)
                fun_test.simple_assert(len(dut_spirent_map[flow_type][flow_direction]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type][flow_direction])))
                count = 0
                for key, value in dut_spirent_map[flow_type][flow_direction].iteritems():
                    if count == no_of_ports_needed:
                        break
                    chassis_ip = value.split('/')[0]
                    if chassis_ip not in spirent_assets['chassis_ips']:
                        raise Exception("Chassis IP: %s not found in Spirent Asset. Ensure Chassis exists" % chassis_ip)
                    result[key] = value
                    count += 1  
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_local_settings_parameters(self, flow_direction=False, ip_version=False, spray_enable=False):
        result = {}
        try:
            fun_test.simple_assert(flow_direction or ip_version or spray_enable,
                                   "No parameter provided to be fetcehd from local settings")
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Get NU Configs")
            for config in configs:
                if config['name'] == "local_settings":
                    if flow_direction:
                        result[self.FLOW_DIRECTION] = config[self.FLOW_DIRECTION]
                    if ip_version:
                        result[self.IP_VERSION] = config[self.IP_VERSION]
                    if spray_enable:
                        result[self.SPRAY_ENABLE] = config[self.SPRAY_ENABLE]
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_dut_type(self):
        try:
            job_environment = fun_test.get_job_environment()
            # job_environment = {"EMULATION_TARGET": "F1", "UART_HOST": "10.1.40.21", "UART_TCP_PORT_0": "40221"}
            if type(job_environment) == unicode:
                job_environment = json.loads(job_environment)
                fun_test.log(job_environment)

            job_inputs = fun_test.get_job_inputs()
            if job_environment and "RUN_TARGET" in job_environment:
                if job_environment["RUN_TARGET"] == self.DUT_TYPE_PALLADIUM:
                    self.DUT_TYPE = self.DUT_TYPE_PALLADIUM
                elif job_environment["RUN_TARGET"] == self.DUT_TYPE_F1.upper():
                    self.DUT_TYPE = self.DUT_TYPE_F1
            else:
                if job_inputs and "speed" in job_inputs:
                    if job_inputs['speed'] == "SPEED_1G":
                        self.DUT_TYPE = self.DUT_TYPE_PALLADIUM
                    elif job_inputs['speed'] == "SPEED_25G" or job_inputs['speed'] == "SPEED_100G":
                        self.DUT_TYPE = self.DUT_TYPE_F1
                else:
                    self.DUT_TYPE = self.DUT_TYPE_PALLADIUM
        except Exception as ex:
            fun_test.critical(str(ex))
        return self.DUT_TYPE

    def read_test_configs_by_dut_type(self, config_file, config_name=None):
        result = None
        try:
            all_configs = self._parse_file_to_json_in_order(file_name=config_file)
            fun_test.simple_assert(all_configs, "Read all Configs")
            for config in all_configs:
                if config['dut_type'] == self.DUT_TYPE:
                    if config_name:
                        if config['name'] == config_name:
                            fun_test.log("Test Config Fetched: %s" % config)
                            result = config
                            break
                    else:
                        fun_test.log("Test Config Fetched: %s" % config)
                        result = config
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
