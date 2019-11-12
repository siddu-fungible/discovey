import os
import re
from collections import OrderedDict

# Set random_gather to False to override the gather_lths with conf_gather_lths
random_gather = True
conf_gather_lths = [2, 4]
ffac_args = " -e 1 -t f1 --res_buff_size=65534 -d"
n_gather_entries = 1

## File naming type
name_convention = "hc"

########### DEBUGGIN cases #############
pat_dir = "/Users/admin/python_scripts/pcre_extracted_new/dfa_filtered_patterns1/"
pld_dir = "/Users/admin/python_scripts/pcre_extracted_new/dfa_filtered_payloads1/"
res_dir = "/Users/admin/python_scripts/pcre_extracted_new/dfa_filtered_graphs1/"
# General logic for pat pld dict creation
#NFA
#exclude_lst = ["test_16", "test_17", "test_19", "test_20", "test_24"]
pld_files = os.listdir(pld_dir)
obj = re.compile("test_\d+")
pat_pld_files = {}
# PCRE1 exclude list for FFA
pcre_exclude_lst = ['test_798_1', 'test_111_1', 'test_49_1', 'test_854_1', 'test_740_2', 'test_275_1', 'test_845_1', 'test_741_1', 'test_11_1', 'test_744_1', 'test_791_3', 'test_791_2', 'test_749_1', 'test_1002_1', 'test_1057_1', 'test_866_1', 'test_70_2', 'test_1084_1', 'test_113_1', 'test_128_3', 'test_128_2', 'test_480_1', 'test_129_1', 'test_288_1', 'test_797_1', 'test_130_1', 'test_652_1', 'test_792_1', 'test_1000_1', 'test_739_2', 'test_993_1', 'test_280_1', 'test_791_1', 'test_50_2', 'test_745_1', 'test_105_2', 'test_995_1', 'test_672_1', 'test_275_2', 'test_845_2', 'test_741_2', 'test_221_1', 'test_654_1', 'test_740_1', 'test_653_1', 'test_739_1', 'test_3_1', 'test_792_2', 'test_916_1', 'test_943_1', 'test_92_2', 'test_129_2', 'test_277_3', 'test_381_1', 'test_70_1', 'test_796_1', 'test_128_1']
sw_fb_exclude_lst = ['test_787_params.json', 'test_1003_params.json', 'test_748_params.json', 'test_223_params.json', 'test_280_params.json', 'test_623_params.json', 'test_741_params.json', 'test_578_params.json', 'test_20_40_params.json', 'test_25_params.json', 'test_744_params.json', 'test_849_params.json', 'test_30_params.json', 'test_233_params.json', 'test_577_params.json', 'test_230_params.json', 'test_672_params.json', 'test_693_params.json', 'test_33_params.json', 'test_80_100_params.json', 'test_747_params.json', 'test_249_params.json', 'test_14_params.json', 'test_826_params.json', 'test_64_params.json', 'test_494_params.json', 'test_139_params.json', 'test_1057_params.json', 'test_823_params.json', 'test_853_params.json', 'test_593_params.json', 'test_1000_params.json', 'test_232_params.json', 'test_750_params.json', 'test_31_params.json', 'test_609_params.json', 'test_848_params.json', 'test_40_60_params.json', 'test_745_params.json', 'test_824_params.json', 'test_995_params.json', 'test_227_params.json', 'test_496_params.json', 'test_622_params.json', 'test_222_params.json', 'test_610_params.json', 'test_13_params.json', 'test_821_params.json', 'test_281_params.json', 'test_749_params.json', 'test_237_params.json', 'test_605_params.json', 'test_247_params.json', 'test_694_params.json', 'test_1002_params.json', 'test_619_params.json', 'test_1_20_params.json', 'test_275_params.json', 'test_1001_params.json', 'test_244_params.json', 'test_852_params.json', 'test_822_params.json', 'test_993_params.json', 'test_621_params.json', 'test_495_params.json', 'test_224_params.json', 'test_65_params.json', 'test_15_params.json', 'test_746_params.json', 'test_624_params.json', 'test_60_80_params.json', 'test_248_params.json', 'test_32_params.json', 'test_597_params.json', 'test_231_params.json']

exclude_lst = [obj.search(y).group() for y in pcre_exclude_lst] + [x.split("_params.json")[0] for  x  in sw_fb_exclude_lst] + nfa_cross_pass_lst

# Junniper 
#exclude_lst =["ymsg-p2p-put-filename.pat", "ymsg-message.pat", "nbname-resource-address.pat", "http-header-content-language.pat", "pop3-list.pat", "h225ras-admission.pat", "imap-fetch.pat", "mssql-login-user.pat"]

# Snort
#exclude_lst = ["file-multimedia.pat", "os-windows.pat", "malware-backdoor.pat"]
exclude_lst = []

if name_convention == "hc":
   for pld in pld_files:
       try:
           base = obj.search(pld).group()
       except:
           print "File is not in test_*.in format. Ignoring: ", pld
           continue
       if base in exclude_lst:
           continue
       try:
           pat_pld_files[base+".pat"].append(pld)
       except:
           pat_pld_files[base+".pat"] = [pld]

if name_convention == "snort":
   for pld in pld_files:
       if pld in exclude_lst:
           continue
       base = pld.split(".in")[0]
       try:
           pat_pld_files[base+".pat"].append(pld)
       except:
           pat_pld_files[base+".pat"] = [pld]


#pat_pld_files =  {"test_1.pat":["test_1_1.in", "test_1_2.in"]}
if __name__ == "__main__":
    print pat_pld_files

