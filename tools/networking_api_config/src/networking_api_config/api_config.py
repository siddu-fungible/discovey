import json, time, re
import requests


class SDKClient(object):
    def __init__(self, target_ip, target_port):
        self.target_ip = target_ip
        self.target_port = target_port
        self.headers = {
             'Content-Type': 'application/json',
        }
         

    def postall(self, url, data, verify=False):
        try:
            response = requests.post(url, headers=self.headers, data=data, verify=False)
            return response
        except requests.exceptions.HTTPError as e:
            return "Error: " + str(e)


    def patchall(self, url, data, verify=False):
        try:
            import pdb;pdb.set_trace() 
            response = requests.patch(url, headers=self.headers, data=data, verify=False)
            return response
        except requests.exceptions.HTTPError as e:
            return "Error: " + str(e)
