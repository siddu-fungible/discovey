from lib.system.fun_test import *


def debug_difference(initial_dict, current_dict, f1):
    f1_dict = initial_dict["f1_{}".format(f1)].copy()
    dict_1 = f1_dict["output"]
    # print ("dict_1")
    # print(json.dumps(dict_1, indent=4))
    time_1 = f1_dict["time"]
    dict_2 = current_dict["output"]
    time_2 = current_dict["time"]
    # print ("dict_2")
    # print(json.dumps(dict_2, indent=4))
    time_difference = (time_2 - time_1).seconds
    result = debug_difference_helper(dict_1, dict_2)
    result["time_difference"] = time_difference
    # print(json.dumps(result, indent=4))
    return result


def debug_difference_helper(debug_memory_1, debug_memory_5):
    result = {}
    result_coh = main_fields(debug_memory_1, debug_memory_5, "coherent")
    result_non = main_fields(debug_memory_1, debug_memory_5, "non_coh")
    result.update(result_coh)
    result.update(result_non)
    return result


def main_fields(debug_memory_1, debug_memory_5, field):
    result = {}
    clean_coherent_1, biggies_1 = filter_coh(debug_memory_1, field)
    clean_coherent_5, biggies_5 = filter_coh(debug_memory_5, field)
    dif_coherent = dict_difference(clean_coherent_1, clean_coherent_5)
    dif_biggies = dict_difference(biggies_1, biggies_5)
    dif_coherent["biggies"] = dif_biggies
    result[field] = dif_coherent
    return result


def dict_difference(dict_1, dict_2):
    return {x: (dict_2[x] - dict_1[x]) for x in dict_1 if ((x in dict_2) and
                                                           (type(dict_2[x]) == int or type(dict_2[x]) == float))}


def filter_coh(dict, field="coherent"):
    coherent = dict[field]
    biggies = coherent["biggies"].copy()
    # del coherent["biggies"]
    regions = coherent["regions"]
    # del coherent["regions"]
    return coherent, biggies