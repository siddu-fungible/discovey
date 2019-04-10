from __future__ import print_function
import json
from ydk.models.openconfig import openconfig_bgp
from ydk.models.openconfig import openconfig_bgp_types
from ydk.models.openconfig import iana_if_type
from ydk.models.openconfig.openconfig_routing_policy import RoutingPolicy
from ydk.providers import CodecServiceProvider
from ydk.services import CodecService
from api_config import SDKClient
from ydk.services import CRUDService
from ydk.models.openconfig.openconfig_interfaces import Interfaces
from ydk.models.openconfig.ietf_interfaces import InterfaceType
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
        if loopback:
            interface.config.type = iana_if_type.SoftwareLoopback()
            interface.config.loopback_mode = False
            loopback_name= intf_config["id"] + ":0"
            interface.config.name = loopback_name
        elif irb:
            interface.config.name = intf_config["id"] 
        else:
            interface.config.name = intf_config["id"] 
            interface.config.description = intf_config["description"]

        interface.name = interface.config.name
        interface.config.enabled = True

        # Configure IP Subinterface 
        if "ip" in intf_config: 
            subinterface = interface.subinterfaces.Subinterface()        
            subinterface.index = 1
            subinterface.config.index = 1
            subinterface.config.enabled = True
            subinterface.ipv4  =  subinterface.Ipv4()     
            subinterface.ipv4.config.enabled=True
            subinterface.ipv4.config.dhcp_client=False 
            addresses=subinterface.ipv4.Addresses() 
            address = addresses.Address()   
            if loopback:
                address.ip =  intf_config["ip"]["address"]
                address.config.ip  =  intf_config["ip"]["address"]
                address.config.prefix_length  =  int(intf_config["ip"]["netmask"])
            elif irb:
                address.ip =  intf_config["ip"]["address"]
                address.config.ip  =  intf_config["ip"]["address"]
                address.config.prefix_length  =  int(intf_config["ip"]["netmask"])
            else:    
                address.ip =  intf_config["ip"]["address"]
                address.config.ip  =  intf_config["ip"]["address"]
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

