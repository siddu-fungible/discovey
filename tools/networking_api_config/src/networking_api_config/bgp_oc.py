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

        # Create routing policy for nexthop self 
        routing_policy = RoutingPolicy()
        next_hop_self_defn = RoutingPolicy.PolicyDefinitions.PolicyDefinition()
        next_hop_self_defn.name = 'Next-Hop-Self'
        statement=next_hop_self_defn.statements.Statement()
        statement.name="next-hop-self" 
        statement.actions.BgpActions().config.set_next_hop = "SELF"
        next_hop_self_defn.statements.statement.append(statement)
        routing_policy.policy_definitions.policy_definition.append(next_hop_self_defn)
        next_hop_self_defn.parent = routing_policy.policy_definitions
        
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

            # Configure allow own as 
            nbr_ipv4.as_path_options.config.allow_own_as=1

            
            # Append nexthop-self policy
            #nbr_ipv4_afsf = nbr_ipv4.afi_safis.AfiSafi()
            #nbr_ipv4_afsf.afi_safi_name = openconfig_bgp_types.IPV4UNICAST()
            #nbr_ipv4_afsf.config.afi_safi_name = openconfig_bgp_types.IPV4UNICAST()
            #nbr_ipv4_afsf.config.enabled = True

            # Create afi-safi policy instances
            #nbr_ipv4_afsf.apply_policy.config.import_policy.append('Next-Hop-Self')
            #nbr_ipv4_afsf.apply_policy.config.export_policy.append('Next-Hop-Self')
            #nbr_ipv4.afi_safis.afi_safi.append(nbr_ipv4_afsf)

            bgp_cfg.neighbors.neighbor.append(nbr_ipv4)
            nbr_ipv4.parent = bgp_cfg.neighbors
        return bgp_cfg

    def create_oc_bgp(self, bgp_json):
        bgp_cfg = self.read_bgp_config(config_json=bgp_json)
        bgp_payload = self.codec_service.encode(self.provider, bgp_cfg)
        url = "http://%s:%s/v1/update/openconfig-bgp:bgp" %(self.target_ip, self.target_port)
        self.sdk_client.patchall(url=url, data=bgp_payload)
