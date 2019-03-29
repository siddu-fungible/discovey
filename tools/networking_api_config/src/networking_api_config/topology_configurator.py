from __future__ import print_function
import os
import time
import re
import json
from api_config import SDKClient
from bgp_oc import BGPConfig
from intf_sdk import IntfConfig
from intf_oc import IntfOCConfig
from fcp_oc import FCPConfig
from helper import BaseSetup
from collections import OrderedDict

class ConfigManager(BaseSetup):
    def __init__(self, input_json):
        self.config_file = input_json
 
    def configure_f1(self):
        access_details = self.get_access_details(file_name = self.config_file)
  
        # Get access details 
        self.target_ip = access_details["ip"]
        self.target_port = access_details["apisvr"]

        # Create BGP config 
        self.crate_bgp_oc_config()

        # Create Interface config
        self.create_intf_sdk()
        self.create_intf_oc()

        # Create Global config
        self.create_global_oc()

    def crate_bgp_oc_config(self):
        print("Configure BGP via Openconfig")  
        bgp_config=self.get_bgp_config(self.config_file)
        bgp_oc_handle = BGPConfig(target_ip=self.target_ip, target_port=self.target_port)
        bgp_oc_handle.create_oc_bgp(bgp_json=bgp_config)

    def create_intf_sdk(self):
        print("Configure Interface via SDK") 
        intf_config=self.get_intf_config(self.config_file)
        intf_sdk_handle = IntfConfig(target_ip=self.target_ip, target_port=self.target_port)
        for intf in intf_config:
            if "fpg" in intf["id"]:
                intf_json=self.get_intf_config_by_id(id=intf["id"] ,intf_json=intf_config) 
                intf_sdk_handle.create_intf_config(intf_json=intf_json)
            
 

    def create_intf_oc(self):
        print("Configure Interface via Openconfig") 
        intf_config=self.get_intf_config(self.config_file)
        intf_oc_handle = IntfOCConfig(target_ip=self.target_ip, target_port=self.target_port)
        for intf in intf_config:
            if "fpg" in intf["id"]:
                intf_json=self.get_intf_config_by_id(id=intf["id"] ,intf_json=intf_config) 
                intf_oc_handle.create_oc_intf(intf_config=intf_json)

            if "lo" in intf["id"]:
                intf_json=self.get_intf_config_by_id(id=intf["id"] ,intf_json=intf_config)
                intf_oc_handle.create_oc_loopback_intf(intf_config=intf_json)
 
            if "vlan" in intf["id"]:
                intf_json=self.get_intf_config_by_id(id=intf["id"] ,intf_json=intf_config)
                intf_oc_handle.create_oc_irb_intf(intf_config=intf_json)
        return True

    def create_global_oc(self):
        print("Configure FCP global via Openconfig") 
        fcp_config=self.get_fcp_config(self.config_file)
        fcp_oc_handle = FCPConfig(target_ip=self.target_ip, target_port=self.target_port)
        fcp_oc_handle.create_oc_fcp(fcp_config)
        return True


if __name__ == '__main__':
 
    # Input file dir  
    input_dir= "/home/cmukherjee/github/Integration/tools/networking_api_config/inputs/demo/"
  
    for filename in os.listdir(input_dir):   
        if filename.endswith(".json"):
            filename= input_dir + filename
            conf_handle=ConfigManager(input_json=filename)  
            conf_handle.configure_f1()  
