import os
import re
import json
from rgx_config import *
from rgx_params_lib import *

## Create N serial (load,search,unload) action sequences 
json_file =  open("all_lsu.json", "w")
a_struct = action_struct("all_lsu", "test_all_lsu")

dfa_pc_map = [ 3, 0, 0, 0, 0, 0, 0, 0 ]
nfa_pc_map = 1
action_seq = []
for idx, pl in enumerate(pld_files):
    try:
       base = re.search("test_\d+",pl).group()
    except:
       print "IGNORE: file is not starting with test_", pl
       continue
    if base in exclude_lst:
       print "Excluding ", base, ".......\n"
       continue
    pl_base = re.search("test_\d+_\d+", pl).group()

    # Fetch gather lengths and expected matches from test_*exp.json file
    f_res = open(res_dir + pl_base + "_exp.json", "r")
    parsed_json = json.loads(f_res.read())
    f_res.close()
    g_lths = parsed_json["gather_lengths"]
    e_res = parsed_json["expected"]

    act_l_dict = action_load(dfa_pc_map, nfa_pc_map, base+"graph.json")
    act_s_dict = action_search(base+"graph.json", [pl], g_lths, e_res)
    act_u_dict = action_unload(base+"graph.json")

    action_seq.append(act_l_dict)
    action_seq.append(act_s_dict)
    action_seq.append(act_u_dict)

a_struct["parallel"].append(action_seq)
json.dump(a_struct, json_file, indent=4, sort_keys=True)

