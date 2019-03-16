from __future__ import print_function
import os
import time
import re
import json
from api_config import SDKClient
from bgp_oc import BGPConfig
from helper import BaseSetup
from collections import OrderedDict

class ConfigManager(BaseSetup):
    def __init__(self, target_ip, target_port,input_json):
        self.target_ip = target_ip
        self.target_port = target_port
        self.config_file = input_json
        self.sdk_client = SDKClient(target_ip=self.target_ip, target_port=self.target_port)

    def configure_f1(self):
        self.crate_bgp_oc_config()

        #TODO
        #self.create_intf_sdk()
        #self.create_intf_oc()
        #self.create_global_oc()

    def crate_bgp_oc_config(self):
        
        bgp_config=self.get_bgp_config(self.config_file)
        bgp_oc_handle = BGPConfig(target_ip=self.target_ip, target_port=self.target_port)
        bgp_oc_handle.create_oc_bgp(bgp_json=bgp_config)

    def create_intf_sdk(self):
        return True 

    def create_intf_oc(self):
        return True

    def create_global_oc(self):
        return True


if __name__ == '__main__':
    conf_handle=ConfigManager(target_ip='127.0.0.1', target_port='8000', input_json="/home/cmukherjee/github/Integration/tools/networking_api_config/inputs/1_1_0.json")
    conf_handle.configure_f1()
