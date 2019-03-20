from __future__ import print_function
import os
import time
import re
import json
from api_config import SDKClient
from bgp_oc import BGPConfig
from intf_sdk import IntfConfig
from intf_oc import IntfOCConfig
from helper import BaseSetup
from collections import OrderedDict

class ConfigManager(BaseSetup):
    def __init__(self, target_ip, target_port,input_json):
        self.target_ip = target_ip
        self.target_port = target_port
        self.config_file = input_json

    def configure_f1(self):
        #self.crate_bgp_oc_config()
        self.create_intf_sdk()
        #self.create_intf_oc()
        # TODO 
        #self.create_global_oc()

    def crate_bgp_oc_config(self):
        
        bgp_config=self.get_bgp_config(self.config_file)
        bgp_oc_handle = BGPConfig(target_ip=self.target_ip, target_port=self.target_port)
        bgp_oc_handle.create_oc_bgp(bgp_json=bgp_config)

    def create_intf_sdk(self):
        intf_config=self.get_intf_config(self.config_file)
        intf_sdk_handle = IntfConfig(target_ip=self.target_ip, target_port=self.target_port)
        for intf in intf_config:
            if "FPG" in intf["id"]:
                intf_json=self.get_intf_config_by_id(id=intf["id"] ,intf_json=intf_config) 
                intf_sdk_handle.create_intf_config(intf_json=intf_json)
            
 

    def create_intf_oc(self):
        intf_config=self.get_intf_config(self.config_file)
        intf_oc_handle = IntfOCConfig(target_ip=self.target_ip, target_port=self.target_port)
        for intf in intf_config:
            if "FPG" in intf["id"]:
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
        return True


if __name__ == '__main__':
    conf_handle=ConfigManager(target_ip='127.0.0.1', target_port='8000', input_json="/home/cmukherjee/github/Integration/tools/networking_api_config/inputs/1_1_0.json")
    conf_handle.configure_f1()
