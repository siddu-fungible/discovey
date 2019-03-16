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

    def get_bgp_config(self, file_name):
        all_config= self.parse_file_to_json_in_order(file_name=file_name)
        bgp_dict = all_config["bgp"]
        return bgp_dict
