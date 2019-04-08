import os
import time
import re
import json
from api_config import SDKClient
from collections import OrderedDict


# Default field and mandatory 

##- Mandatory 
# id
# type

# Below will go away when control plane is up 
# gph_index
# spine_index 
# remote_f1_id 

##-Default value
#vrf = 1 
#speed = 100



class IntfConfig(object):
    def __init__(self, target_ip='127.0.0.1', target_port='8000'):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sdk_client = SDKClient(target_ip=target_ip, target_port=target_port)

    def create_intf_config(self, intf_json): 

        intf_config = intf_json
        data_dict={}

        speed = intf_config.get("bandwidth", 100) 
        link_speed = str('BW_'+ str(speed) + 'G')
        intf_gphs_list=[]
        for item in intf_config["gph_index"]:
            intf_dict={}
            intf_dict["gph_index"] = item["index"]
            intf_dict["spine_index"] = item["index"]
            intf_gphs_list.append(intf_dict)

        if intf_config['type'] == 'fabric_facing':

            data_dict["status"] = True
            data_dict["vrfid"] = intf_config.get("vrf", 1)
            data_dict["remote_f1_id"] = intf_config['remote_f1_id']
            data_dict["name"] = intf_json["id"]
            data_dict["Interface_type"] = 'Fabric_Facing'
            data_dict["bandwidth"] = link_speed
            data_dict["intf_gphs"] = intf_gphs_list
            data_dict["logicport"] = int(re.findall("\d+", intf_json["id"])[0])
            data = json.dumps(data_dict)

        else:
            data_dict["status"] = True
            data_dict["vrfid"] = 1
            data_dict["name"] = intf_json["id"]
            data_dict["Interface_type"] = intf_config['type']
            data_dict["bandwidth"] = link_speed
            data_dict["intf_gphs"] = intf_gphs_list
            data_dict["logicport"] = int(re.findall("\d+", intf_json["id"])[0])
            data_dict["spine_index"] = intf_config['spine_index']
            data = json.dumps(data_dict)
        url = "http://%s:%s/v1/cfg/INTERFACE/%d" %(self.target_ip, self.target_port, int(re.findall("\d+", intf_json["id"])[0])+1)
        self.sdk_client.postall(url=url, data=data)

    def create_gph_index(self,gph_index): 
        data_dict={}
        data_dict["gph_index"] = gph_index
        data_dict["enable"] = True
        data = json.dumps(data_dict)
        url = "http://%s:%s/v1/cfg/GPHINDEX/%d" %(self.target_ip, self.target_port, int(gph_index+1)) 
        self.sdk_client.postall(url=url, data=data)        
