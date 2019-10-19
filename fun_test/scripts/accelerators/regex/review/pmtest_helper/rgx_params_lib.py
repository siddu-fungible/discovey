import os
import re
import json

def action_load(dfa_pc_map, nfa_pc_map, graph_file):
    load_dict = {}
    load_dict["action"] = "load"
    load_dict["graph_name"] = graph_file.split(".json")[0]
    load_dict["graph_file"] = graph_file
    load_dict["dfa_pc_map"] = dfa_pc_map
    load_dict["nfa_pc_map"] = nfa_pc_map
    return load_dict

def action_search(graph_fl, pld_fls_lst, gthr_lths_lst, exp_res_lst):
    if len(pld_fls_lst) != len(gthr_lths_lst):
        print "No. of payloads and respective gather entries are not the same!"
        print "pld_files: ", pld_fls_lst, "gthr_lths: ", gthr_lths_lst
    search_dict = {}
    search_dict["action"] = "search"
    search_dict["graph_name"] = graph_fl.split(".json")[0]
    search_dict["enforce_order"] = "no"
    #search_dict["payload"] = [ {"file": pld}  for pld in pld_fls]
    search_dict["payload"] = []
    #for idx, pld_fl in enumerate(pld_fls_lst):
    for idx in range(len(pld_fls_lst)):
        search_dict["payload"].append({"file": pld_fls_lst[idx]})                 # New change for multiple payloads
        #search_dict["payload"][idx]["file"] = pld_fls_lst[idx]                 # New change for multiple payloads
        search_dict["payload"][idx]["name"] = "search_"+pld_fls_lst[idx]
        search_dict["payload"][idx]["gather_lengths"] =  gthr_lths_lst[idx]
        search_dict["payload"][idx]["expected"] = exp_res_lst[idx]
    return search_dict


def action_unload(graph_name):
    unload_dict = {}
    unload_dict["action"] = "unload"
    unload_dict["graph_name"] = graph_name
    return unload_dict


def action_struct(name, desc):
    struct_dict = {}
    struct_dict["name"] = name
    struct_dict["description"] = desc
    struct_dict["parallel"] = []
    return struct_dict 

