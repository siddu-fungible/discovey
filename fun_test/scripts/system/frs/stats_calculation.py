import debug_memory_calculation
# one_data_set is assumed to have time1 and output1 and time2 and output2


def dict_difference(one_data_set):
    result = {}
    dict_1 = one_data_set["output1"]
    time_1 = one_data_set["time1"]
    dict_2 = one_data_set["output2"]
    time_2 = one_data_set["time2"]
    time_difference = (time_2 - time_1).seconds
    dif_dict = dict_difference_div(dict_1, dict_2, time_difference)
    for field in ["EFI->EQC Enqueue Interface valid", "EQC->EFI Dequeue Interface valid"]:
        result[field] = dif_dict[field]
    return result


def dict_difference_div(dict_1, dict_2, time_difference):
    return {x: round((dict_2[x] - dict_1[x]) / float(time_difference), 2)
            for x in dict_1 if ((x in dict_2) and (type(dict_2[x]) == int or type(dict_2[x]) == float))}


def cal_le_stat(dpcsh_output):
    peek_value = 320
    for k, v in dpcsh_output.iteritems():
        for each_filed, value in v.iteritems():
            v[each_filed] = value/peek_value
    return dpcsh_output
