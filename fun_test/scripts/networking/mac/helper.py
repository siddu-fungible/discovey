from lib.system.fun_test import *

TEST_CONFIGS_FILE = SCRIPTS_DIR + "/networking/mac/test_configs.json"


def get_test_config_by_dut_type(nu_config_obj, name):
    result = None
    try:
        all_configs = nu_config_obj._parse_file_to_json_in_order(file_name=TEST_CONFIGS_FILE)
        fun_test.simple_assert(all_configs, "Read all Configs")
        for config in all_configs:
            if config['dut_type'] == nu_config_obj.DUT_TYPE and config['name'] == name:
                fun_test.log("Test Config Fetched: %s" % config)
                result = config
                break
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_nearest_key(dict, max_frame_length):
    nearest_small_key = 0
    for key in dict.keys():

        if key != 'max' and int(key) < max_frame_length:
            current_difference = max_frame_length - int(key)
            if current_difference < max_frame_length - nearest_small_key:
                nearest_small_key = int(key)
    return nearest_small_key


def get_modified_dictionary(my_dict, nearest_key, max_frame_length):
    output_dict = {}
    if nearest_key == 1518:
        output_dict = dict
        output_dict['max'] = max_frame_length - 1518
    else:
        for key, val in my_dict.iteritems():
            if key == 'max':
                pass
            elif int(key) < nearest_key:
                output_dict[key] = val
            elif int(key) == nearest_key:
                new_val = max_frame_length - int(key)
                output_dict[key] = new_val
    return output_dict


