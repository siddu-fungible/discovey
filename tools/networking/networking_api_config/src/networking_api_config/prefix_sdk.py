import os
import time
import re
import json
from api_config import SDKClient
from collections import OrderedDict

class RouteConfig(object):
    def __init__(self, target_ip='127.0.0.1', target_port='8000'):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sdk_client = SDKClient(target_ip=target_ip, target_port=target_port)

    def create_prefix_config(self, prefix_json): 

        prefix_config = prefix_json
        data_dict={}
        data_dict["nhip"] = prefix_config["nhip"]
        data_dict["mac"] = prefix_config["mac"]
        data_dict["ifname"] = prefix_config["ifname"]
        data = json.dumps(data_dict)
        url = "http://%s:%s/v1/cfg/FIBNH/%d" %(self.target_ip, self.target_port, int(prefix_json["id"]))
        self.sdk_client.postall(url=url, data=data)

    def create_route_config(self, route_json):

        route_config = route_json
        data_dict={}
        data_dict["vrfid"] = route_config["vrfid"]
        data_dict["pfx"]   = route_config["pfx"]
        data_dict["outgoingnh"] = route_config["outgoingnh"]
        data = json.dumps(data_dict)
        url = "http://%s:%s/v1/cfg/FIBPREFIX/%d" %(self.target_ip, self.target_port, int(route_json["id"]))
        self.sdk_client.postall(url=url, data=data)  



