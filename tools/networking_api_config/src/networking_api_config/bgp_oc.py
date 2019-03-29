from __future__ import print_function
import json
from ydk.models.openconfig import openconfig_bgp
from ydk.models.openconfig import openconfig_bgp_types
from ydk.models.openconfig import openconfig_routing_policy as oc_routing_policy 
from ydk.models.openconfig import openconfig_policy_types as oc_policy_types
from ydk.types import Empty
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

    def read_routing_policy(self):
       
        routing_policy = oc_routing_policy.RoutingPolicy() 
        # Create routing policy for nexthop self
        next_hop_self_defn = routing_policy.PolicyDefinitions.PolicyDefinition()
        next_hop_self_defn.name = 'Next-Hop-Self'
        statement=next_hop_self_defn.statements.Statement()
        statement.name="next-hop-self"
        statement.actions.BgpActions().config.set_next_hop = "SELF"
        next_hop_self_defn.statements.statement.append(statement)
        routing_policy.policy_definitions.policy_definition.append(next_hop_self_defn)
        next_hop_self_defn.parent = routing_policy.policy_definitions     
        return routing_policy

    def read_multiple_bgp(self, config_json):
        bgp_cfg = self.read_bgp_config(config_json=config_json)
        policy_cfg = self.read_routing_policy()
        return {"bgp":bgp_cfg, "routing-policy":policy_cfg}
  

    def read_bgp_config(self, config_json):
 
        bgp_cfg = openconfig_bgp.Bgp()
        # Config Local AS
        bgp_cfg.global_.config.as_ = config_json["as"]
        
        # Config Router ID
        bgp_cfg.global_.config.router_id = config_json["router_id"]

        # Config Neighbour 
        for item in config_json["neighbors"]:
            nbr_ipv4 = bgp_cfg.neighbors.Neighbor()
            nbr_ipv4.neighbor_address = item["ip"]
            nbr_ipv4.config.neighbor_address = item["ip"]
            nbr_ipv4.config.peer_as = item["as"]

            # Configure allow own as 
            nbr_ipv4.as_path_options.config.allow_own_as=1

            bgp_cfg.neighbors.neighbor.append(nbr_ipv4)
            nbr_ipv4.parent = bgp_cfg.neighbors
        return bgp_cfg

    def create_oc_bgp(self, bgp_json):
        bgp_cfg = self.read_bgp_config(config_json=bgp_json)
        bgp_payload = self.codec_service.encode(self.provider, bgp_cfg)
        url = "http://%s:%s/v1/update/openconfig-bgp:bgp" %(self.target_ip, self.target_port)
        self.sdk_client.patchall(url=url, data=bgp_payload)

    def create_oc_routing_policy(self):
        policy_cfg = self.read_routing_policy()
        policy_payload = self.codec_service.encode(self.provider, policy_cfg)
        url = "http://%s:%s/v1/update/openconfig-routing-policy:routing-policy" %(self.target_ip, self.target_port)
        self.sdk_client.patchall(url=url, data=policy_payload)
