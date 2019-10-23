import os
import time
import re
import json
from rgx_config import *
from rgx_params_lib import *
from commands import  getoutput
from random import randint

## load n, search n ,unload n 
json_file =  open("all_llss_prl.json", "w")
a_struct = action_struct("all_llss_prl", "test_all_llss_prl")

dfa_pc_map = [ 1, 0, 0, 0, 0, 0, 0, 0 ]
dfa_pc_map = [ 7, 7, 7, 7, 7, 7, 7, 7 ]
dfa_pc_map = []
nfa_pc_map = 1

def gen_random_dfa_pc_map():
    pc_map = []
    for i in range(8):
        pc_map.append(randint(1,7))
    #print pc_map
    return pc_map

for pat, plds  in pat_pld_files.items():
    action_seq = []
    if pat in exclude_lst:
       print "Excluding: ", pat
       continue 
    pat_base = pat.split(".pat")[0]
    dfa_pc_map = gen_random_dfa_pc_map()
    act_l_dict = action_load(dfa_pc_map, nfa_pc_map, pat_base+"_graph.json")
    action_seq.append(act_l_dict)
    a_struct["parallel"].append(action_seq)

for pat, plds  in pat_pld_files.items():
    action_seq = []
    if pat in exclude_lst:
       print "Excluding: ", pat
       continue
    pat_base = pat.split(".pat")[0]
    for idx, pld in enumerate(plds):
        pld_base = str(idx+1)
        fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"

        # Fetch gather lengths and expected matches from test_*exp.json file
        f_res = open(fl_name, "r")
        parsed_json = json.loads(f_res.read())
        f_res.close()
        g_lths = parsed_json["gather_lengths"]
        e_res = parsed_json["expected"]

        act_s_dict = action_search(pat_base+"_graph.json", [pld], g_lths, e_res)
        action_seq.append(act_s_dict)
        a_struct["parallel"].append(action_seq)

json.dump(a_struct, json_file, indent=4, sort_keys=True)
time.sleep(2)
cmd = "cp all_llss_prl.json /Users/admin/workspace/FunOS"
print cmd
getoutput(cmd)

