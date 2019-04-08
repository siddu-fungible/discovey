from __future__ import print_function
import json
from ydk.models.openconfig.openconfig_fcp import FcpGlobal
from ydk.providers import CodecServiceProvider
from ydk.services import CodecService
from api_config import SDKClient
from ydk.services import CRUDService
from ydk.errors import YError

class FCPConfig(CodecService , CodecServiceProvider):
    def __init__(self, target_ip='127.0.0.1', target_port='8000', verbose=False):
        self.target_ip = target_ip
        self.target_port = target_port
        self.sdk_client = SDKClient(target_ip=target_ip, target_port=target_port)
        self.provider = CodecServiceProvider(type='json')
        self.codec_service = CodecService()

    def read_fcp_config(self, fcp_config):

        # Configure FCP Global
        fcp_global=FcpGlobal()
        # TODO
        # F1 Number 
        # FTEP 

        fcp_global.config.fcp_req_dscp_ecn  = fcp_config["fcp_config"]["fcp_req_dscp_ecn"]
        fcp_global.config.fcp_data_dscp_ecn = fcp_config["fcp_config"]["fcp_data_dscp_ecn"]
        fcp_global.config.fcp_gnt_dscp_ecn  = fcp_config["fcp_config"]["fcp_gnt_dscp_ecn"]
        fcp_global.config.fcp_hdr_ver       = fcp_config["fcp_config"]["fcp_hdr_ver"] 
        fcp_global.config.fcp_hdr_udp_dport = fcp_config["fcp_config"]["fcp_hdr_udp_dport"]
        fcp_global.config.fcp_blk_size      = fcp_global.config.FcpBlkSize.B256
        fcp_global.config.fcp_hdr_ipv4_id   = fcp_config["fcp_config"]["fcp_hdr_ipv4_id"]  
        fcp_global.config.fcp_hdr_v4_ethertype  = fcp_config["fcp_config"]["fcp_hdr_v4_etype"] 
        fcp_global.config.fcp_hdr_udp_sport_ctl = fcp_global.config.FcpHdrUdpSportCtl.RANDOM
        fcp_global.config.fcp_qos_count         = fcp_global.config.FcpQosCount.EIGHT
        return fcp_global 

    def create_oc_fcp(self, fcp_config):
        fcp_cfg = self.read_fcp_config(fcp_config)
        url = "http://%s:%s/v1/update/openconfig-fcp:fcp-global" %(self.target_ip, self.target_port)
        fcp_payload = self.codec_service.encode(self.provider, fcp_cfg)
        self.sdk_client.patchall(url=url, data=fcp_payload)

