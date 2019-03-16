from __future__ import print_function
import json
from ydk.models.openconfig import openconfig_bgp
from ydk.models.openconfig import openconfig_bgp_types
from ydk.models.openconfig.openconfig_routing_policy import RoutingPolicy
from ydk.providers import CodecServiceProvider
from ydk.services import CodecService
from api_config import SDKClient


class BGPConfig(CodecService , CodecServiceProvider):
    def __init__(self, target_ip='127.0.0.1', target_port='8000', verbose=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sdk_client = SDKClient(target_ip=target_ip, target_port=target_port)
        self.provider = CodecServiceProvider(type='json')
        self.codec_service = CodecService()

    def read_bgp_config(self, config_json):
        bgp_cfg = openconfig_bgp.Bgp()

        # Config Local AS
        bgp_cfg.global_.config.as_ = config_json["as"]
        # Config Router ID
        bgp_cfg.global_.config.router_id = config_json["router_id"]
        # Config Network 
        #bgp_cfg.global_.config._prefix = config_json["network"]

        # Config Neighbour 
        for item in config_json["neighbors"]:
            nbr_ipv4 = bgp_cfg.neighbors.Neighbor()
            nbr_ipv4.neighbor_address = item["ip"]
            nbr_ipv4.config.neighbor_address = item["ip"]
            nbr_ipv4.config.peer_as = item["as"]
            bgp_cfg.neighbors.neighbor.append(nbr_ipv4)
            nbr_ipv4.parent = bgp_cfg.neighbors
        return bgp_cfg

    def create_oc_bgp(self, bgp_json):
        bgp_cfg = self.read_bgp_config(config_json=bgp_json)
        bgp_payload = self.codec_service.encode(self.provider, bgp_cfg)
        url = "http://%s:%s/v1/update/openconfig-bgp:bgp" %(self.target_ip, self.target_port)
        self.sdk_client.patchall(url=url, data=bgp_payload)
