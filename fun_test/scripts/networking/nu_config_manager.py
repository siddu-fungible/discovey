from lib.system.fun_test import *


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

    def __int__(self, chassis_type):
        self.chassis_type = chassis_type

    def _get_nu_configs(self):
        all_configs = []
        try:
            all_configs = parse_file_to_json(file_name=self.NU_CONFIGS_SPEC)
            fun_test.simple_assert(all_configs, "Read Configs")
        except Exception as ex:
            fun_test.critical(str(ex))
        return all_configs

    def read_dut_config(self, dut_type=DUT_TYPE_PALLADIUM):
        result = {}
        try:
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


nu_config_obj = NuConfigManager()
