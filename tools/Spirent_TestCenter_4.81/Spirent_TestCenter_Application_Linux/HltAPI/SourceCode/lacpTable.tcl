# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Lacp:: {
}

set ::sth::Lacp::lacpTable {
    ::sth::Lacp::
    {   emulation_lag_config
        {hname              stcobj              stcattr             type            priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle        _none_              _none_              ALPHANUM        1               _none_      _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete ""}   _none_}
        {lag_handle        _none_              _none_              ALPHANUM        1               _none_      _none_      true        _none_      false        _none_          {create "" enable ""  disable "" modify "" delete ""}   _none_}
        {mode               _none_              _none_              {CHOICES create enable disable modify  delete}  0  create  _none_      true        _none_      true        _none_          { create "" enable ""  disable "" modify "" delete ""}  _none_}
        {protocol              _none_              _none_              {CHOICES none lacp bfd lacp_bfd}  1  lacp  _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_port_mac_addr     LacpPortConfig              PortMacAddress              ANY             2               00:10:94:00:00:02      _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_port_mac_addr_step     LacpPortConfig              PortMacAddressStep              ANY             2               00:00:00:00:00:01      _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_actor_key       LacpPortConfig               ActorKey                NUMERIC         3               1      0-65535     true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete ""}  _none_}
        {lacp_actor_key_step       LacpPortConfig               ActorKeyStep                NUMERIC         3               1      0-65535     true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_actor_port_priority     LacpPortConfig              ActorPortPriority      NUMERIC         4  1    0-65535      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_actor_port_priority_step    LacpPortConfig              ActorPortPriorityStep      NUMERIC         4  1    0-65535      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_actor_port_number     LacpPortConfig             ActorPort             NUMERIC         5  1    0-65535      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_actor_port_step     LacpPortConfig              ActorPortStep             NUMERIC         5  1    0-65535      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_timeout     LacpPortConfig               LacpTimeout              {CHOICES long short}  6  long    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {lacp_activity     LacpPortConfig              LacpActivity              {CHOICES passive active}  7  active    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete ""}  _none_}
        {actor_system_priority     LacpGroupConfig              ActorSystemPriority         NUMERIC         8  1    0-65535      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {actor_system_id     LacpGroupConfig              ActorSystemId               ANY             9  00:00:00:00:00:01    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete ""}  _none_}
        {lag_name     _none_             _none_                ANY             9   _none_    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {transmit_algorithm     lag             TransmitAlgorithm              {CHOICES hashing round_robin}             9  "hashing"    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
        {l2_hash_option     lag             L2HashOption              ANY             9  "ETH_SRC|ETH_DST|VLAN|MPLS"    _none_      true        _none_      false        _none_          {create "" enable ""  disable "" modify "" delete ""}  _none_}
        {l3_hash_option     lag             L3HashOption              ANY             9  "IPV4_SRC|IPV4_DST|IPV6_SRC|IPV6_DST|UDP|TCP"    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete ""}  _none_}
        {aggregatorresult     portoptions             AggregatorResult               {CHOICES member aggregated}             9    aggregated    _none_      true        _none_      false        _none_          { create "" enable ""  disable "" modify "" delete "" }  _none_}
      
    }
    {   emulation_lacp_config
        {hname              stcobj              stcattr             type            priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle        _none_              _none_              ALPHANUM        1               _none_      _none_      true        _none_      true        _none_          { enable "" modify "" disable ""}   _none_}
        {mode               _none_              _none_              {CHOICES enable modify disable}  0  _none_  _none_      true        _none_      true        _none_          { enable "" modify "" disable "" }  _none_}
        {local_mac_addr     EthIIIf              SourceMac              ANY             2               00:10:94:00:00:02      _none_      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_port_key       LacpPortConfig               ActorKey                NUMERIC         3               1      0-65535     true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_lacp_port_priority     LacpPortConfig              ActorPortPriority      NUMERIC         4  1    0-65535      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_port_number     LacpPortConfig              ActorPort             NUMERIC         5  1    0-65535      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_lacp_timeout     LacpPortConfig               LacpTimeout              {CHOICES long short}  6  long    _none_      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {lacp_activity     LacpPortConfig              LacpActivity              {CHOICES passive active}  7  active    _none_      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_system_priority     LacpGroupConfig              ActorSystemPriority         NUMERIC         8  1    0-65535      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
        {act_system_id     LacpGroupConfig              ActorSystemId               ANY             9  00:00:00:00:00:01    _none_      true        _none_      false        _none_          { enable "" modify "" disable "" }  _none_}
    }
    
    {   emulation_lacp_control
        {hname              stcobj              stcattr             type            priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle        _none_              _none_              ALPHANUM        1               _none_      _none_      true        _none_      true        _none_          { start "" stop "" }  _none_}
        {action             _none_              _none_              {CHOICES start stop}  0  _none_  _none_      true        _none_      true        _none_          { start "" stop "" }  _none_}
    }
    
    {   emulation_lacp_info
        {hname              stcobj              stcattr             type            priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle        _none_              _none_              ALPHANUM        1               _none_      _none_      true        _none_      true        _none_          _none_  _none_}
        {action             _none_              _none_              {CHOICES collect clear}  0  _none_  _none_      true        _none_      true        _none_          _none_  _none_}
        {mode               _none_              _none_              {CHOICES aggregate state stats}  0  aggregate  _none_      true        _none_      false        _none_          { collect "" }  _none_}
        {pdus_rx             LacpPortResults              RxLacpPduCount              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {marker_response_pdus_rx             LacpPortResults              RxMarkerResponsePduCount              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {marker_pdus_rx             LacpPortResults              RxMarkerPduCount              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {marker_response_pdus_tx             LacpPortResults           TxMarkerResponsePduCount                 NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {pdus_tx             LacpPortResults              TxLacpPduCount              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {marker_pdus_tx             LacpPortResults              TxMarkerPduCount              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {partner_collector_max_delay             LacpPortResults              PartnerCollectorMaxDelay              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { stats "" }  _none_}
        {partner_operational_key             LacpPortResults              PartnerOperationalKey              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {partner_port             LacpPortResults              PartnerPort              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {partner_port_priority             LacpPortResults              PartnerPortPriority              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {partner_system_id             LacpPortResults              PartnerSystemId              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {partner_system_priority             LacpPortResults              PartnerSystemPriority              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {actor_operational_key             LacpPortResults              ActorOperationalKey              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {actor_port             LacpPortResults              ActorPort              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {actor_systemid             LacpPortResults              ActorSystemId              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {actor_state            LacpPortConfig              ActorState              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {partner_state             LacpPortConfig              PartnerState              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
        {lacp_state             LacpPortConfig              LacpState              NUMERIC  0  _none_  _none_      true        _none_      false        _none_          { state ""}  _none_}
    }
}