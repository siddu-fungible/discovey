from lib.system.fun_test import *
from collections import OrderedDict
import re

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
    FLOW_DIRECTION_FPG_CC = "FPG_CC"
    FLOW_DIRECTION_CC_FPG = "CC_FPG"
    FLOW_DIRECTION_HU_CC = "HU_CC"
    FLOW_DIRECTION_HNU_CC = "HNU_CC"
    FLOW_DIRECTION_FPG_HNU = "FPG_HNU"
    FLOW_DIRECTION_HNU_FPG = "HNU_FPG"
    FLOW_DIRECTION_FPG_HU = "FPG_HU"
    FLOW_DIRECTION_HU_FPG = "HU_FPG"

    def __int__(self, chassis_type=CHASSIS_TYPE_PHYSICAL):
        self._get_chassis_type()

    def _get_chassis_type(self):
        self.chassis_type = self.CHASSIS_TYPE_PHYSICAL
        return self.chassis_type

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

    def read_dut_config(self, dut_type=None, flow_type=TRANSIT_FLOW_TYPE, flow_direction=None):
        result = {}
        try:
            if not dut_type:
                dut_type = self.DUT_TYPE_PALLADIUM
            configs = self._get_nu_configs()
            fun_test.simple_assert(configs, "Failed to read config spec")
            for config in configs:
                if config["type"] == dut_type:
                    result = config
                    break
            dut_spirent_map = self.read_dut_spirent_map()
            result['ports'] = []
            if flow_type == self.TRANSIT_FLOW_TYPE:
                for key, value in sorted(dut_spirent_map[flow_type].items()):
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
                for key, value in sorted(dut_spirent_map[flow_type][vp_flow_direction].iteritems()):
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
            for config in configs:
                if config["name"] == "dut_spirent_map":
                    result.update(config)
                    break
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
    '''
    def _do_port_mapping(self, num_ports, chassis_configs, dut_configs, fpg_ports=False, hnu_ports=False):
        result = {}
        try:
            fun_test.simple_assert(fpg_ports or hnu_ports, "Neither flag fpg_ports or hnu_ports specified. "
                                                           "Please sepcify one.")
            if fpg_ports:
                key = 'ports'
            else:
                key = 'hnu_ports'

            fun_test.simple_assert(num_ports <= len(chassis_configs[key]),
                                   message="Number of ports asked %s is greater than available on spirent %s"
                                           % (num_ports, len(chassis_configs[key])))
            fun_test.simple_assert(num_ports <= len(chassis_configs[key]),
                                   message="Number of ports asked %s is greater than available on dut %s"
                                           % (num_ports, len(dut_configs[key])))

            chassis_slot_num = chassis_configs['slot_no']
            for i in range(0, num_ports):
                current_port_num = chassis_configs[key][i]
                port_location = '%s/%s' % (chassis_slot_num, current_port_num)
                result[port_location] = dut_configs[key][i]
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
    '''

    def get_spirent_dut_port_mapper(self, flow_type=TRANSIT_FLOW_TYPE, no_of_ports_needed=2,
                                    flow_direction=None):
        result = OrderedDict()
        try:
            dut_spirent_map = self.read_dut_spirent_map()
            spirent_assets = self.read_traffic_generator_asset()
            if flow_type == self.TRANSIT_FLOW_TYPE:
                fun_test.log("Fetching NU Transit Flow Map")
                fun_test.simple_assert(len(dut_spirent_map[flow_type]) >= no_of_ports_needed,
                                       "Ensure No of ports needed are available in config. Needed: %d Available: %d" %
                                       (no_of_ports_needed, len(dut_spirent_map[flow_type])))
                count = 0
                for key, value in sorted(dut_spirent_map[flow_type].items()):
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
        except Exception as ex:
            fun_test.critical(str(ex))
        return result



nu_config_obj = NuConfigManager()
