import debug_memory_calculation
from lib.system.fun_test import *
import re
# one_data_set is assumed to have time1 and output1 and time2 and output2


def dict_difference(one_data_set, cmd):
    result = {}
    dict_1 = one_data_set["output1"]
    time_1 = one_data_set["time1"]
    dict_2 = one_data_set["output2"]
    time_2 = one_data_set["time2"]
    time_difference = (time_2 - time_1).seconds
    if cmd == "EQM":
        diff_dict = dict_difference_div(dict_1, dict_2, time_difference)
        for field in ["EFI->EQC Enqueue Interface valid", "EQC->EFI Dequeue Interface valid"]:
            result[field] = diff_dict[field]
    elif cmd == "LE":
        # peek_value = 320
        field = "cmh_egress_cnt"
        result_dict = dict_difference_level_2_div(dict_1, dict_2, time_difference)
        result = find_field_sum_le(result_dict, field)
        # result = dict_level_1_div(diff_dict, peek_value)
    elif cmd == "HBM":
        diff_dict = dict_difference_level_4_div(dict_1, dict_2, time_difference)
        result = sum_important_fields_hbm(diff_dict)
    elif cmd == "CDU":
        result = dict_difference_level_2_div(dict_1, dict_2, time_difference)
    elif cmd == "PC_DMA":
        result = dict_difference_level_3_div(dict_1, dict_2, time_difference)
    elif cmd == "DDR":
        diff_dict = dict_difference_level_3_div(dict_1, dict_2, time_difference)
        result = sum_important_fields_ddr(diff_dict)
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

def dict_difference_level_4_div(dict_1, dict_2, time_difference):
    result = {}
    for each_field in dict_1:
        result[each_field] = dict_difference_level_3_div(dict_1[each_field], dict_2[each_field], time_difference)
    return result

def dict_level_1_div(dict_lev1, peek_value):
    for k, v in dict_lev1.iteritems():
        for field, value in v.iteritems():
            dict_lev1[k][field] = value/peek_value
    return dict_lev1


def dict_sum_level_2(dict_lev1):
    for k, v in dict_lev1.iteritems():
        for field, value in v.iteritems():
            dict_lev1[k][field] = value
    return dict_lev1


def find_field_sum_le(result_dict,field):
    result = {}
    le_sum = 0
    for cluster, value in result_dict.iteritems():
        result[cluster] = value[field]
        le_sum += value[field]
        fun_test.log("Cluster: {} field: {} value: {}".format(cluster, field, value[field]))
    result["overall"] = le_sum
    return result

def sum_important_fields_hbm(diff_dict):
    result = {}
    na_requests=qsys_read_requests=qsys_write_requests=0
    for hbm_cnts in diff_dict:
        print hbm_cnts
        for muh in diff_dict[hbm_cnts]:
            print muh
            for node in diff_dict[hbm_cnts][muh]:
                print node
                for field, value in diff_dict[hbm_cnts][muh][node].iteritems():
                    match_qsys = re.match(r'qsys\d_(\w+)_requests', field)
                    match_na = re.match(r'dna_write_requests|cna_read_requests|sna_read_requests', field)
                    if match_qsys:
                        mode = match_qsys.group(1)
                        exec("qsys_{}_requests += value".format(mode))
                    if match_na:
                        na_requests += value
    result["qsys_write_requests"] = round(qsys_write_requests, 2)
    result["qsys_read_requests"] = round(qsys_read_requests, 2)
    result["na_requests"] = round(na_requests, 2)
    return result

def sum_important_fields_ddr(diff_dict):
    result = {}
    na_requests = qsys_read_requests = qsys_write_requests = 0
    for ddr_cnt in diff_dict:
        print ddr_cnt
        for mud in diff_dict[ddr_cnt]:
            print mud
            for field, value in diff_dict[ddr_cnt][mud].iteritems():
                match_qsys = re.match(r'qsys\d?_(\w+)_requests', field)
                match_na = re.match(r'dna_write_requests|cna\d?_read_requests|sna_read_requests', field)
                if match_qsys:
                    mode = match_qsys.group(1)
                    exec ("qsys_{}_requests += value".format(mode))
                if match_na:
                    na_requests += value
    result["qsys_write_requests"] = round(qsys_write_requests, 2)
    result["qsys_read_requests"] = round(qsys_read_requests, 2)
    result["na_requests"] = round(na_requests, 2)
    return result
