'''
Utility script to generate graphs and expected results for the given gather lenghts

Input: 
Pattern, Payload, Gather lenght ...  details are fetched from rgx_config.py 

Output:
Graph and Expected results are stored in the  res_dir mentioned in rgx_config.py

'''

import os
import re
import json
from commands import  getoutput
from collections import OrderedDict
import random as r
from rgx_config import *


## Function to generate random gather entries that sums to given pld length
def random_sum_to(n, num_terms = None):
    num_terms = (num_terms or r.randint(2, n)) - 1
    a = r.sample(range(1, n), num_terms) + [0, n]
    list.sort(a)
    return [a[i+1] - a[i] for i in range(len(a) - 1)]


for pat, plds  in pat_pld_files.items():
    pat_base = pat.split(".pat")[0]
    jnpr_pat_dir = pat_dir+pat_base+"/"
    jnpr_pld_dir = pld_dir+pat_base+"/payloads/"
    for idx, pld in enumerate(plds):
        pld_base = str(idx+1)
        pld_len = os.path.getsize(jnpr_pld_dir+pld)
        if random_gather:
            gather_lths = random_sum_to(pld_len, n_gather_entries)
        else:
            gather_lths = conf_gather_lths
        
        cmd = "./ffac -j {} -r {}{} -p {}{} -o {}{}_graph.json --drop_unsupported".format(ffac_args, jnpr_pat_dir, pat, jnpr_pld_dir, pld, res_dir, pat.split(".pat")[0])
        print cmd
        cmd_out = getoutput(cmd)
        cp_cmd = "cp {}{} {}{}_graph.json /Users/admin/workspace/FunOS/".format(jnpr_pld_dir, pld, res_dir, pat.split(".pat")[0])
        print cp_cmd
        cp_cmd_out = getoutput(cp_cmd)   
        try:
           # Check if zero matches returned
           s = re.search("HERE ARE THE FINAL ANSWERS \((\d+)\)", cmd_out)
           if s == None:
              print " Unable to catch the matches! Check if there is any change in ffac output?", s
           if int(s.group(1)) == 0:
               #print "Zero matches found. Setting match_list=[]"
               match_list = []
               op = cmd_out
           if int(s.group(1)) != 0:
               op = cmd_out.split("HERE ARE THE FINAL ANSWERS")[-1]
               match_list = re.findall("(?:Id:\s.*)", op)
               if "NONE" in match_list[-1]:
                  del match_list[-1]
        except:
           print "ERROR? Could not compile!\n"
           op = cmd_out
           continue

        ## Create exp dict
        exp_matches = []
        if match_list != []:
           for match in match_list:
               try:
                   pat_name = re.search("pat_name: (\w+)", match).group(1)
                   start_offset = re.search("start: (\w+|\d+|-1)", match).group(1)
                   end_offset = re.search("end: (\w+|\d+|-1)", match).group(1)

                   if start_offset == "xx":
                       start_offset = "-1"

                   for sgid in range(len(gather_lths)):
                       if int(start_offset) <= sum(gather_lths[:sgid+1]):
                           if sgid == 0:
                               new_start_offset = int(start_offset)
                               s_gidx = sgid
                               break
                           else:
                               new_start_offset = int(start_offset) - sum(gather_lths[:sgid])   
                               s_gidx = sgid

                   for egid in range(len(gather_lths)):
                       if int(end_offset) <= sum(gather_lths[:egid+1]):
                           if egid == 0:
                               new_end_offset = int(end_offset)
                               e_gidx = egid
                               break
                           else:
                               new_end_offset = int(end_offset) - sum(gather_lths[:egid])  
                               e_gidx = egid
                           
               except:
                  print ("No matches found or Incorrect output format:")
                  print match
               match_dict = { "name":pat_name, "s_gidx":s_gidx, "s_goff":new_start_offset, "e_gidx":e_gidx, "e_goff":new_end_offset}
               exp_matches.append(match_dict)

        ## Store the exp results in test_*exp.json file
        fl_name = res_dir+pat_base+"_"+pld_base+"_exp.json"
        print "exp file: ",fl_name
        with open(fl_name, "w") as json_file:
             json.dump({"gather_lengths" : gather_lths, "expected": exp_matches} , json_file)



