import debug_memory_calculation
# one_data_set is assumed to have time1 and output1 and time2 and output2


def dict_difference(one_data_set, cmd):
    result = {}
    dict_1 = one_data_set["output1"]
    time_1 = one_data_set["time1"]
    dict_2 = one_data_set["output2"]
    time_2 = one_data_set["time2"]
    time_difference = (time_2 - time_1).seconds
    if cmd == "eqm":
        diff_dict = dict_difference_div(dict_1, dict_2, time_difference)
        for field in ["EFI->EQC Enqueue Interface valid", "EQC->EFI Dequeue Interface valid"]:
            result[field] = diff_dict[field]
    elif cmd == "le":
        # peek_value = 320
        result = dict_difference_level_2_div(dict_1, dict_2, time_difference)
        # result = dict_level_1_div(diff_dict, peek_value)
    elif cmd == "hbm":
        # diff_dict = dict_difference_level_2(dict_1, dict_2, time_difference)
        pass
    elif cmd == "cdu":
        result = dict_difference_level_2_div(dict_1, dict_2, time_difference)
    elif cmd == "pc_dma":
        result = dict_difference_level_3_div(dict_1, dict_2, time_difference)

    return result


def dict_difference_div(dict_1, dict_2, time_difference):
    return {x: round((dict_2[x] - dict_1[x]) / float(time_difference), 2)
            for x in dict_1 if ((x in dict_2) and (type(dict_2[x]) == int or type(dict_2[x]) == float))}


def dict_difference_level_2_div(dict_1, dict_2, time_difference):
    result = {}
    for each_field in dict_1:
        result[each_field] = dict_difference_div(dict_1[each_field], dict_2[each_field], time_difference)
    return result

def dict_difference_level_3_div(dict_1, dict_2, time_difference):
    result = {}
    for each_field in dict_1:
        result[each_field] = dict_difference_level_2_div(dict_1[each_field], dict_2[each_field], time_difference)
    return result

def dict_level_1_div(dict_lev1, peek_value):
    for k, v in dict_lev1.iteritems():
        for field, value in v.iteritems():
            dict_lev1[k][field] = value/peek_value
    return dict_lev1


# def dict_sum_level_2(dict_lev1):
#     for k, v in dict_lev1.iteritems():
#         for field, value in v.iteritems():
#             dict_lev1[k][field] = value/peek_value
#     return dict_lev1
