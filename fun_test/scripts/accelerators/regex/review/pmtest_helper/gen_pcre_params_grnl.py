import os
import time
import re
import json
from rgx_config import *
from rgx_params_lib import *
from commands import  getoutput

## Create N parallel(load,search,unload) sequences 

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

json_files =[]
for pat, plds  in pat_pld_files.items():
    if pat in exclude_lst:
        print "Excluding: ", pat
        continue
    pat_base = pat
    for idx, pld in enumerate(plds):
        pld_base = str(idx+1)
        a_struct = action_struct(pat_base+"_"+pld_base, "test_"+pat_base+"_"+pld_base)
        action_seq = []
        fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"
        json_fl_name = pat_base+"_"+pld_base+".json"
        cp_cmd = "cp "+res_dir+json_fl_name+" /Users/admin/workspace/FunOS"

        # Fetch gather lengths and expected matches from test_*exp.json file
        try:
           f_res = open(fl_name, "r")
        except Exception as e:
           #print e, "Continue with next pat/pld"
           continue
        parsed_json = json.loads(f_res.read())
        f_res.close()
        g_lths = parsed_json["gather_lengths"]
        e_res = parsed_json["expected"]

        act_l_dict = action_load(dfa_pc_map, nfa_pc_map, pat_base+"_graph.json")
        act_s_dict = action_search(pat_base+"_graph.json", [pld], g_lths, e_res)
        act_u_dict = action_unload(pat_base+"_graph")

        action_seq.append(act_l_dict)
        action_seq.append(act_s_dict)
        action_seq.append(act_u_dict)

        a_struct["parallel"].append(action_seq)
        json_file =  open(json_fl_name, "w")
        json.dump(a_struct, json_file, indent=4, sort_keys=True)
        json_file.close()
        json_files.append(json_fl_name)
        #print cp_cmd
        getoutput(cp_cmd)

print json_files
         

