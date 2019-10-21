import os
import re
import json
from rgx_config import *
from rgx_params_lib import *

## Create N parallel (load) action sequences 
json_file =  open("all_parl_load.json", "w")
a_struct = action_struct("all_lsu", "test_all_lsu")

dfa_pc_map = [ 3, 0, 0, 0, 0, 0, 0, 0 ]
nfa_pc_map = 1

for gr in graph_files:
    action_seq = []
    act_l_dict = action_load(dfa_pc_map, nfa_pc_map, gr)
    action_seq.append(act_l_dict)

    a_struct["parallel"].append(action_seq)

json.dump(a_struct, json_file, indent=4, sort_keys=True)

