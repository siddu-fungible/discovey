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
        try:
            dict_1 = dict_1["eqm_stats"]
            dict_2 = dict_2["eqm_stats"]
        except:
            pass
        diff_dict = dict_difference_div(dict_1, dict_2, time_difference)
        if diff_dict:
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
    elif cmd == "STORAGE_IOPS":
        diff_dict = dict_difference_level_2_div(dict_1, dict_2, time_difference)
        result = filter_rcnvme_and_sum(diff_dict)
    return result


def dict_difference_div(dict_1, dict_2, time_difference):
    return {x: int(round((dict_2[x] - dict_1[x]) / float(time_difference), 2))
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
    result["qsys_write_requests"] = int(round(qsys_write_requests, 2))
    result["qsys_read_requests"] = int(round(qsys_read_requests, 2))
    result["na_requests"] = int(round(na_requests, 2))
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
    result["qsys_write_requests"] = int(round(qsys_write_requests, 2))
    result["qsys_read_requests"] = int(round(qsys_read_requests, 2))
    result["na_requests"] = int(round(na_requests, 2))
    return result

def filter_dict(one_dataset, stat_name):
    result = {}
    if stat_name == "DEBUG_VP_UTIL":
        result = filter_out_debug_vp_util(one_dataset)
    return result

def filter_out_debug_vp_util(one_dataset):
    dpcsh_data = one_dataset["output"]
    simplified_output = simplify_debug_vp_util(dpcsh_data)
    cluster_wise_result = calculate_for_each_cluster(simplified_output)
    return cluster_wise_result

def simplify_debug_vp_util( dpcsh_data):
    result = []
    if dpcsh_data:
        for cluster in range(8):
            for core in range(6):
                for vp in range(4):
                    try:
                        value = dpcsh_data["CCV{}.{}.{}".format(cluster, core, vp)]
                        one_data_set = {"core": core,
                                        "cluster": cluster,
                                        "vp": vp,
                                        "value": value
                                        }
                        # print(one_data_set)
                        result.append(one_data_set)
                    except:
                        print ("Data error")
    return result

def calculate_for_each_cluster(simplified_output):
    result = {}
    for one_data in simplified_output:
        cluster = one_data["cluster"]
        result.setdefault("cluster{}".format(cluster), 0)
        result["cluster{}".format(cluster)] += one_data["value"]
    for each_cluster in result:
        result[each_cluster] = int(round(result[each_cluster] / 24.0, 4))
    result["average_value"] = int(round(sum(result.values()) / 8, 4))
    return result

def filter_rcnvme_and_sum(dpcsh_data):
    result = {}
    allow = ["rcnvme_write_count", "rcnvme_read_count"]
    sum_read_count = 0
    if dpcsh_data:
        for ssd, value in dpcsh_data.iteritems():
            result[ssd] = {}
            for allowed in allow:
                result[ssd][allowed] = value[allowed]
                if allowed == "rcnvme_read_count":
                    sum_read_count += value[allowed]
        result["100"] = {}
        result["100"]["rcnvme_read_count"] = sum_read_count
    return result

