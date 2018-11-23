from lib.system.fun_test import *

qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)


def get_load_value_from_load_percent(load_percent, max_egress_load):
    result = None
    try:
        if load_percent == 0:
            result = 0
        else:
            result = (load_percent * max_egress_load) / 100.0
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def verify_load_output(actual_value, expected_value, accept_range=0.2, compare=False):
    result = False
    try:
        fun_test.log("Actual load output seen is %s" % actual_value)
        if not compare:
            fun_test.log("Expected load output is %s" % expected_value)
        else:
            fun_test.log("Actual load output seen for comparing stream is %s" % expected_value)
        if actual_value < expected_value:
            diff = expected_value - actual_value
        else:
            diff = actual_value - expected_value

        if diff < accept_range:
            result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def reset_queue_scheduler_config(network_controller_obj, dut_port, queue_list=[]):
    result = False
    try:
        if not queue_list:
            queue_list = [x for x in range(16)]
        for queue in queue_list:
            strict_priority = 0
            extra_bandwidth = 0
            if queue in [0, 8]:
                strict_priority = 1
                extra_bandwidth = 1
            strict = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                     strict_priority_enable=strict_priority,
                                                                     extra_bandwidth=extra_bandwidth)
            fun_test.test_assert(strict,"Set strict priority of %s on queue %s" % (strict_priority, queue),
                                 ignore_on_success=True)

            shaper = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                     shaper_enable=False,
                                                                     min_rate=qos_json_output['shaper']['default_cir'],
                                                                     shaper_threshold=qos_json_output['shaper'][
                                                                         'default_threshold'])
            fun_test.test_assert(shaper, "Reset shaper cir and threshold to default values for queue %s" % queue,
                                 ignore_on_success=True)

            dwrr = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                   weight=qos_json_output['dwrr']['default_weight'])
            fun_test.test_assert(dwrr, "Reset dwrr to default values for queue %s" % queue,
                                 ignore_on_success=True)
            result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result
