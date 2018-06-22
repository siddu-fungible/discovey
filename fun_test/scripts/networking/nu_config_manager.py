from lib.system.fun_test import *
from collections import OrderedDict


class NuConfigManager(object):
    NU_CONFIGS_SPEC = SCRIPTS_DIR + "/networking/nu_configs.json"
    DUT_TYPE_QFX = "qfx"
    DUT_TYPE_F1 = "f1"
    DUT_TYPE_PALLADIUM = "palladium"
    DUT_INTERFACE_MODE_25G = "25G"
    DUT_INTERFACE_MODE_50G = "50G"
    DUT_INTERFACE_MODE_100G = "100G"
    CHASSIS_TYPE_PHYSICAL = "physical"
    CHASSIS_TYPE_VIRTUAL = "virtual"
    TRAFFIC_GENERATOR_TYPE_SPIRENT = "spirent_traffic_generator"

    def __int__(self, chassis_type=CHASSIS_TYPE_PHYSICAL):
        self._get_chassis_type()

    def _get_chassis_type(self):
        self.chassis_type = self.CHASSIS_TYPE_PHYSICAL
        return self.chassis_type

    def _get_nu_configs(self):
        all_configs = []
        try:
            all_configs = parse_file_to_json(file_name=self.NU_CONFIGS_SPEC)
            fun_test.simple_assert(all_configs, "Read Configs")
        except Exception as ex:
            fun_test.critical(str(ex))
        return all_configs

    def read_dut_config(self, dut_type=None):
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
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

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

    def get_spirent_dut_port_mapper(self, dut_type=DUT_TYPE_PALLADIUM,
                                   num_fpg_ports=2, num_hnu_ports=0):
        chassis_type = self._get_chassis_type()
        result = OrderedDict()
        try:
            spirent_traffic_configs = self.read_traffic_generator_config()
            chassis_configs = spirent_traffic_configs[chassis_type]
            dut_configs = self.read_dut_config(dut_type=dut_type)

            if num_fpg_ports:
                output = self._do_port_mapping(num_ports=num_fpg_ports, chassis_configs=chassis_configs,
                                               dut_configs=dut_configs, fpg_ports=True)
                result.update(output)
            if num_hnu_ports:
                output = self._do_port_mapping(num_ports=num_hnu_ports, chassis_configs=chassis_configs,
                                               dut_configs=dut_configs, hnu_ports=True)
                result.update(output)

        except Exception as ex:
            fun_test.critical(str(ex))
        return result



nu_config_obj = NuConfigManager()
