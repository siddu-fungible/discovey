import os
import time
import re
import json
from collections import OrderedDict

class BaseSetup (object):

    def describe(self):
        self.set_test_details(steps="""
                Local Library
                """)

    def parse_file_to_json_in_order(self, file_name):
        result = None
        try:
            with open(file_name, "r") as infile:
                contents = infile.read()
                result = json.loads(contents, object_pairs_hook=OrderedDict)
        except Exception as ex:
            #scheduler_logger.critical(str(ex))
            print(str(ex))
        return result

    def get_access_details(self, file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        access_dict = all_config["access"]
        return access_dict  
 

    def get_bgp_config(self, file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        bgp_dict = all_config["Config"]["bgp"]
        return bgp_dict

    def get_intf_config(self,file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        intf_dict = all_config["Config"]["intfs"]
        return intf_dict

    def get_prefix_config(self,file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        prefix_dict = all_config["Config"]["prefix"]
        return prefix_dict

    def get_route_config(self,file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        route_dict = all_config["Config"]["route"]
        return route_dict
   

    def get_fcp_config(self,file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        fcp_dict = all_config["Config"]["global"]
        return fcp_dict

    def get_intf_config_by_id(self, id, intf_json):
        result = []
        try:
            for item in intf_json:
                if item['id'] == id:
                    result=item
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_prefix_config_by_id(self, id, prefix_json):
        result = []
        try:
            for item in prefix_json:
                if item['id'] == id:
                    result=item
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_route_config_by_id(self, id, route_json):
        result = []
        try:
            for item in route_json:
                if item['id'] == id:
                    result=item
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

