import os
import time
import re
import json
from rgx_config import *
from rgx_params_lib import *
from commands import  getoutput

## Create N serial(load,search,unload) sequences 
#a_struct = action_struct("all_lsu", "test_all_lsu")

dfa_pc_map = [ 7, 0, 0, 0, 0, 0, 0, 0 ]
nfa_pc_map = 1


ignored_plds =[]

for pat, plds  in pat_pld_files.items():
    #print  pat, exclude_lst
    if pat in exclude_lst:
       print "Excluding: ", pat
       continue 
    pat_base = pat.split(".pat")[0]
    action_seq = []
    a_struct = action_struct(pat_base+"_params", "test_"+pat_base+"_params")
    exp_fl = res_dir+pat_base+"_"+pat_base+"_exp.json"
    #print exp_fl
    if not os.path.exists(exp_fl):
    #   pass
       print "Excluding...", pat_base
       continue
    json_fl_name = pat_base+"_params.json"
    cp_cmd = "cp "+res_dir+json_fl_name+" /Users/admin/workspace/FunOS"
    act_l_dict = action_load(dfa_pc_map, nfa_pc_map, pat_base+"_graph.json")
    action_seq.append(act_l_dict)

    plds_lst = []
    gthr_lth_lst = []
    exp_res_lst = []
    for idx, pld in enumerate(plds):
        if name_convention == "hc":
            pld_base = re.search("test_\d+_(\d+).(in|pcap)", pld).group(1)  
            fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"
        if name_convention == "snort":
            pld_base = pat_base
            fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"
            #fl_name = res_dir+pat_base+"_exp.json"
        #pld_base = str(idx+1)

        # Fetch gather lengths and expected matches from test_*exp.json file
        try:
            f_res = open(fl_name, "r")
        except:
            print "File not found. Continue wiht other plds: ", pld
            ignored_plds.append(pld)
            continue
        parsed_json = json.loads(f_res.read())
        f_res.close()
        g_lths = parsed_json["gather_lengths"]
        e_res = parsed_json["expected"]
        gthr_lth_lst.append(g_lths)
        exp_res_lst.append(e_res)
        plds_lst.append(pld)

    act_s_dict = action_search(pat_base+"_graph.json", plds_lst, gthr_lth_lst, exp_res_lst)
    act_u_dict = action_unload(pat_base+"_graph")

    action_seq.append(act_s_dict)
    action_seq.append(act_u_dict)

    a_struct["parallel"].append(action_seq)
    json_file =  open(res_dir+json_fl_name, "w")
    json.dump(a_struct, json_file, indent=4, sort_keys=True)
    #json_file.close()
    print cp_cmd
    #op = getoutput(cp_cmd)
    #print op

