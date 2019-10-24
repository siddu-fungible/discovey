import os
import re
import json
from rgx_config import *
from rgx_params_lib import *

## Create N parallel(load,search,unload) sequences 
json_file =  open("all_lsu.json", "w")
a_struct = action_struct("all_lsu", "test_all_lsu")

dfa_pc_map = [ 3, 0, 0, 0, 0, 0, 0, 0 ]
nfa_pc_map = 1

#for idx, pl in enumerate(pld_files):
#    try:
#       base = re.search("test_\d+",pl).group()
#    except:
#       print "IGNORE: file is not starting with test_", pl
#       continue
#    if base in exclude_lst:
#       print "Excluding ", base, ".......\n"
#       continue
action_seq = []
for pat, plds  in pat_pld_files.items():
    pat_base = pat.split(".pat")[0]
    jnpr_pat_dir = pat_dir+pat_base+"/"
    jnpr_pld_dir = pld_dir+pat_base+"/payloads/"
    for idx, pld in enumerate(plds):
        pld_base = str(idx+1)
        fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"

        # Fetch gather lengths and expected matches from test_*exp.json file
        f_res = open(fl_name, "r")
        parsed_json = json.loads(f_res.read())
        f_res.close()
        g_lths = parsed_json["gather_lengths"]
        e_res = parsed_json["expected"]
        #if e_res == []:
        #    continue

        act_l_dict = action_load(dfa_pc_map, nfa_pc_map, pat_base+"_graph.json")
        act_s_dict = action_search(pat_base+"_graph.json", [pld], g_lths, e_res)
        act_u_dict = action_unload(pat_base+"_graph")

        action_seq.append(act_l_dict)
        action_seq.append(act_s_dict)
        action_seq.append(act_u_dict)

a_struct["parallel"].append(action_seq)

json.dump(a_struct, json_file, indent=4, sort_keys=True)

