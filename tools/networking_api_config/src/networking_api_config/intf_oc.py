from __future__ import print_function
import json
from ydk.models.openconfig import openconfig_bgp
from ydk.models.openconfig import openconfig_bgp_types
from ydk.models.openconfig.openconfig_routing_policy import RoutingPolicy
from ydk.providers import CodecServiceProvider
from ydk.services import CodecService
from api_config import SDKClient
from ydk.services import CRUDService
from ydk.models.openconfig.openconfig_interfaces import Interfaces
from ydk.errors import YError

class IntfOCConfig(CodecService , CodecServiceProvider):
    def __init__(self, target_ip='127.0.0.1', target_port='8000', verbose=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sdk_client = SDKClient(target_ip=target_ip, target_port=target_port)
        self.provider = CodecServiceProvider(type='json')
        self.codec_service = CodecService()

    def read_intf_config(self, intf_config, loopback=False, irb=False):

        # Configure Interface 
        interfaces=Interfaces()
        interface = interfaces.Interface()
        interface.config.name = intf_config["id"]
        if loopback:
            interface.config.loopback_mode = True
        elif irb:
            pass 
        else:
            interface.config.description = intf_config["description"]
        interface.name = interface.config.name
        interface.config.enabled = True

        # Configure IP Subinterface 
        if "ip" in intf_config: 
            subinterface = interface.subinterfaces.Subinterface()        
            subinterface.index = 1
            subinterface.config.index = 1
            subinterface.ipv4  =  subinterface.Ipv4()      
            addresses=subinterface.ipv4.Addresses() 
            address = addresses.Address()    
            if loopback:
                address.ip =  intf_config["ip"]
                address.config.ip  =  intf_config["ip"]
                address.config.prefix_length  =  int(intf_config["netmask"])
            elif irb:
                address.ip =  intf_config["ip"]
                address.config.ip  =  intf_config["ip"]
                address.config.prefix_length  =  int(intf_config["netmask"])
            else:    
                address.ip =  intf_config["ip"]["my_ip"]
                address.config.ip  =  intf_config["ip"]["my_ip"]
                address.config.prefix_length  =  int(intf_config["ip"]["netmask"])    

            subinterface.ipv4.addresses.address.append(address)     
            interface.subinterfaces.subinterface.append(subinterface)    
        interfaces.interface.append(interface)
        interface.parent = interfaces
        return interfaces

    def create_oc_intf(self, intf_config):
        intf_cfg = self.read_intf_config(intf_config)
        url = "http://%s:%s/v1/update/openconfig-interfaces:interfaces" %(self.target_ip, self.target_port)
        intf_payload = self.codec_service.encode(self.provider, intf_cfg)
        self.sdk_client.patchall(url=url, data=intf_payload)

    def create_oc_loopback_intf(self, intf_config):
        intf_cfg = self.read_intf_config(intf_config, loopback=True)
        url = "http://%s:%s/v1/update/openconfig-interfaces:interfaces" %(self.target_ip, self.target_port)
        intf_payload = self.codec_service.encode(self.provider, intf_cfg)
        self.sdk_client.patchall(url=url, data=intf_payload)

    def create_oc_irb_intf(self, intf_config):
        intf_cfg = self.read_intf_config(intf_config, irb=True)
        url = "http://%s:%s/v1/update/openconfig-interfaces:interfaces" %(self.target_ip, self.target_port)
        intf_payload = self.codec_service.encode(self.provider, intf_cfg)
        self.sdk_client.patchall(url=url, data=intf_payload) 

