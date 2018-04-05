# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Lldp:: {
    set PDU_DcbxType1 {
        lldp:DcbxTlvt1 { value { DcbxSubTlvt1 { dcbxCtlTlv {}}}}
    }
    set TLV_DcbxCtrl1 {
        DcbxSubTlvt1 { dcbxCtlTlv {}}
    }
    set TLV_DcbxPG_Type1 {
        DcbxSubTlvt1 {
            pgTlv {
                header {}
                bwg_percentage {}
                priority0Allocation {}
                priority1Allocation {}
                priority2Allocation {}
                priority3Allocation {}
                priority4Allocation {}
                priority5Allocation {}
                priority6Allocation {}
                priority7Allocation {}
            }
        }
    }
    set TLV_DcbxPFC_Type1 {
        DcbxSubTlvt1 {
            pfcTlv {
                header {}
            }
        }
    }
    set TLV_DcbxBCN_Type1 {
        DcbxSubTlvt1 {
            bcnTlv {
                header {}
                bcnMode {
                     bcnMode0 {}
                     bcnMode1 {}
                     bcnMode2 {}
                     bcnMode3 {}
                     bcnMode4 {}
                     bcnMode5 {}
                     bcnMode6 {}
                     bcnMode7 {}
                }
            }
        }
    }
    set TLV_DcbxApp_Type1 {
        DcbxSubTlvt1 {
            applicatonTlv {
                header {}
            }
        }
    }
    set TLV_DcbxLLD_Type1 {
        DcbxSubTlvt1 {
            logicLinkDownTlv {
                header {}
            }
        }
    }
    set TLV_DcbxCustom_Type1 {
        DcbxSubTlvt1 {
            customTlv {
                header {}
            }
        }
    }
    
    set PDU_DcbxType2 {
        lldp:DcbxTlvt2 { value { DcbxSubTlvt2 { dcbxCtlTlv {}}}}
    }
    set TLV_DcbxCtrl2 {
        DcbxSubTlvt2 { dcbxCtlTlv {}}
    }
    set TLV_DcbxPG_Type2 {
        DcbxSubTlvt2 {
            pgTlv {
                header {}
                pgAllocation {}
                prioAllocation {}
            }
        }
    }
    set TLV_DcbxPFC_Type2 {
        DcbxSubTlvt2 {
            pfcTlv {
                header {}
            }
        }
    }
    set TLV_DcbxAppPro_Type2 {
        DcbxSubTlvt2 {
            applicatonTlv {
                header {}
                app {
                    AppStruct {}
                }
            }
        }
    }
    set TLV_DcbxCustom_Type2 {
        DcbxSubTlvt2 {
            customTlv {
                header {}
            }
        }
    }
}

set ::sth::Lldp::lldpTable {
    ::sth::Lldp::
    {emulation_lldp_config
        {hname                              stcobj                          stcattr           type       priority    default         range    supported  dependency  mandatory   procfunc    mode    constants}
        {port_handle                        _none_                          _none_            ALPHANUM    0           _none_          _none_      TRUE    _none_    FALSE    _none_    {create ""}    _none_}
        {mode                               _none_                          _none_ {CHOICES create modify reset_tlv delete}  0 _none_ _none_      TRUE    _none_    TRUE     _none_    _none_    _none_}
        {handle                             _none_                          _none_            ALPHANUM    0           _none_          _none_      TRUE    _none_    FALSE    _none_    {modify "" reset_tlv "" delete ""}    _none_}
        {count                              Router                          count             NUMERIC     0               1           _none_      TRUE    _none_    FALSE    _none_    {create ""}    _none_}
        {loopback_ip_addr                   Router                          RouterId          IPV4        0           192.0.0.1       _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {loopback_ip_addr_step              Router                          RouterId          IPV4        0           0.0.0.1         _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {local_mac_addr                     Router-EthIIIf                  SourceMac         ANY         0       00:10:94:00:00:01   _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {local_mac_addr_step                Router-EthIIIf                  SourceMac         ANY         0       00:00:00:00:00:01   _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {vlan_id                            Router-VlanIf                   VlanId            NUMERIC     0           _none_          0-4095      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {vlan_id_step                       Router-VlanIf                   VlanId            NUMERIC     0           1               0-4095      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {intf_ip_addr                       Router-Ipv4If                   Address           IPV4        0           _none_          _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {intf_ip_addr_step                  Router-Ipv4If                   Address           IPV4        0           0.0.0.1         _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {intf_ip_prefix_length              Router-Ipv4If                   PrefixLength      NUMERIC     0           24               0-32       TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {gateway_ip_addr                    Router-Ipv4If                   Gateway           IPV4        0           192.85.1.1      _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {gateway_ip_addr_step               Router-Ipv4If                   Gateway           IPV4        0           0.0.0.0         _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {intf_ipv6_addr                     Router-Ipv6If                   Address           IPV6        0            _none_         _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {intf_ipv6_addr_step                Router-Ipv6If                   Address           IPV6        0           0000::1         _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {intf_ipv6_prefix_length            Router-Ipv6If                   PrefixLength      NUMERIC     0               64          0-128       TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {gateway_ipv6_addr                  Router-Ipv6If                   Gateway           IPV6        0           ::0             _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {gateway_ipv6_addr_step             Router-Ipv6If                   Gateway           IPV6        0          0000::0000       _none_      TRUE    _none_    FALSE    StepConfigProcess    {create ""}    _none_}
        {enable_ipv6_gateway_learning       Router-Ipv6If                   EnableGatewayLearning FLAG     0              0           _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {intf_ipv6_link_local_addr          Router-LinkLocalIpv6If          Address               IPV6     0             fe80::1      _none_      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {msg_tx_interval                    Router-LldpNodeConfig           MsgTxInterval         NUMERIC  0              30          5-32768     TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {msg_tx_hold_mutiplier              Router-LldpNodeConfig           MsgTxHoldMultiplier   NUMERIC  0              4          2-10        TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {reinitialize_delay                 Router-LldpNodeConfig           ReinitializeDelay     NUMERIC  0              2          1-10        TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {tx_delay                           Router-LldpNodeConfig           TxDelay               NUMERIC  0            2            1-8192      TRUE    _none_    FALSE    CommonConfigProcess    {create "" modify ""}    _none_}
        {tlv_chassis_id_subtype             lldp:ChassisIdTlv-chassisid     _none_    {CHOICES chassis_component intf_alias port_component mac_addr network_addr_4 network_addr_6 intf_name locally_assigned customized}    0    network_addr_4    _none_    TRUE    _none_    FALSE    OtherConfigProcess-ConfigMandatoryTlvs    {create "" modify ""}    {chassis_component chassisComponent intf_alias interfaceAlias port_component portComponent mac_addr macAddress network_addr_4 networkAddress4 network_addr_6 networkAddress6 intf_name interfaceName locally_assigned locallyAssigned customized custom}}
        {tlv_chassis_id_value               lldp:ChassisIdTlv-chassisid     id                  ANY         0           _none_       _none_      TRUE    _none_    FALSE    OtherConfigProcess-ConfigMandatoryTlvs    {create "" modify ""}    _none_}
        {tlv_port_id_subtype                lldp:PortIdTlv-portid           _none_    {CHOICES intf_alias port_component mac_addr network_addr_4 network_addr_6 intf_name agent_circuit_id locally_assigned customized}    0    mac_addr    _none_    TRUE    _none_    FALSE    OtherConfigProcess-ConfigMandatoryTlvs    {create "" modify ""}    {intf_alias pidInterfaceAlias port_component pidPortComponent mac_addr pidMacAddress network_addr_4 pidNetworkAddress4 network_addr_6 pidNetworkAddress6 intf_name pidInterfaceName agent_circuit_id pidAgentCircuitID locally_assigned pidLocallyAssigned customized pidCustom}}
        {tlv_port_id_value                  lldp:PortIdTlv-portid           id                  ANY         0           _none_       _none_     TRUE    _none_    FALSE    OtherConfigProcess-ConfigMandatoryTlvs    {create "" modify ""}    _none_}
        {tlv_ttl_value                      lldp:TimeToLiveTlv              ttl              NUMERIC        0           120          0-65535    TRUE    _none_    FALSE    OtherConfigProcess-ConfigMandatoryTlvs    {create "" modify ""}    _none_}
        {reset_tlv_type                     _none_                          _none_   {CHOICES lldp dcbx both} 0         both        _none_      TRUE    _none_    FALSE    _none_    {reset_tlv ""}    _none_}
        {lldp_optional_tlvs                 _none_                          _none_            ANY           0           _none_       _none_      TRUE    _none_    FALSE    OtherConfigProcess-ConfigOptionalTlvs    {create "" modify ""}    _none_}
        {dcbx_tlvs                          _none_                          _none_            ANY           0           _none_       _none_      TRUE    _none_    FALSE    OtherConfigProcess-ConfigDcbxTlvs    {create "" modify ""}    _none_}
    }
    {emulation_lldp_optional_tlv_config 
        {hname                                                  stcobj                                       stcattr                        type                        priority    default           range    supported dependency mandatory     procfunc    mode    constants}
        {tlv_port_description_enable                            _none_                                       _none_                         FLAG                        0           0               _none_      true    _none_     FALSE     OtherConfigProcess-PortDescription    _none_    _none_}
        {tlv_port_description_value                         lldp:PortDescriptionTlv                         description                     ALPHANUM                    0    "Spirent Port"         _none_      true    _none_     FALSE     OtherConfigProcess-PortDescription    _none_    _none_}
        {tlv_system_name_enable                                 _none_                                      _none_                          FLAG                        0           0               _none_      true    _none_     FALSE     OtherConfigProcess-SystemName    _none_    _none_}
        {tlv_system_name_value                              lldp:SystemNameTlv                              name                            ALPHANUM                    0    "Spirent Test Center"  _none_      true    _none_     FALSE     OtherConfigProcess-SystemName    _none_    _none_}
        {tlv_system_description_enable                          _none_                                      _none_                          FLAG                        0           0               _none_      true    _none_     FALSE     OtherConfigProcess-SystemDescription    _none_    _none_}
        {tlv_system_description_value                       lldp:SystemDescriptionTlv                       description                     ANY                         0    "Spirent Test Center"  _none_      true    _none_     FALSE     OtherConfigProcess-SystemDescription    _none_    _none_}
        {tlv_system_capabilities_enable                         _none_                                      _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-SystemCapabilities    _none_    _none_}
        {tlv_system_capabilities_value                      lldp:SystemCapabilitiesTlv-systemCapabilities   _none_                          {REGEXP (0|1){8}}           0       00010000            _none_     true    _none_     FALSE     OtherConfigProcess-SystemCapabilities    _none_    _none_}
        {tlv_enabled_capabilities_value                     lldp:SystemCapabilitiesTlv-enabledCapabilities  _none_                          {REGEXP (0|1){8}}           0       00010000            _none_     true    _none_     FALSE     OtherConfigProcess-SystemCapabilities    _none_    _none_}
        {tlv_management_addr_enable                              _none_                                     _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_count                              _none_                                      _none_                          NUMERIC                     0           1               _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_subtype_list                   lldp:ManagementAddrTlv-managementAddr-customAddr addrSubtype                    ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_value_list                     lldp:ManagementAddrTlv-managementAddr-customAddr managementAddr                 ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_intf_numbering_subtype_list    lldp:ManagementAddrTlv                          ifNumberingSubtype              ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_intf_number_value_list         lldp:ManagementAddrTlv                          ifNumber                        ANY                         0        _none_             _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_management_addr_oid_value_list                 lldp:ManagementAddrTlv                          oid                             ANY                         0        _none_             _none_     true    _none_     FALSE     OtherConfigProcess-ManagementAddress    _none_    _none_}
        {tlv_port_vlanid_enable                                 _none_                                      _none_                          FLAG                        0           0               _none_     true    _none_     FALSE       OtherConfigProcess-PortVlanId    _none_    _none_}
        {tlv_port_vlanid_value                              lldp:PortVlanIdTlv                              portVlanId                      {REGEXP [0-9a-fA-F]{1,4}}   0           0001            _none_     true    _none_     FALSE     OtherConfigProcess-PortVlanId    _none_    _none_}
        {tlv_port_and_protocol_vlanid_enable                    _none_                                      _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-PortAndProtocolVlanId    _none_    _none_}
        {tlv_port_and_protocol_vlanid_count                     _none_                                      _none_                          NUMERIC                     0           1               _none_     true    _none_     FALSE     OtherConfigProcess-PortAndProtocolVlanId    _none_    _none_}
        {tlv_port_and_protocol_vlanid_value_list             lldp:PortAndProtocolVlanIdTlv                  portAndProtocolVlanId           {REGEXP ([0-9a-fA-F]{1,4} ?)+} 0        0000            _none_     true    _none_     FALSE     OtherConfigProcess-PortAndProtocolVlanId    _none_    _none_}
        {tlv_port_and_protocol_vlanid_enabled_flag_list      lldp:PortAndProtocolVlanIdTlv-flags            portAndProtocolVlanEnabled      {REGEXP ([01] ?)+}          0           1               _none_     true    _none_     FALSE     OtherConfigProcess-PortAndProtocolVlanId    _none_    _none_}
        {tlv_port_and_protocol_vlanid_supported_flag_list    lldp:PortAndProtocolVlanIdTlv-flags            portAndProtocolVlanSupport      {REGEXP ([01] ?)+}          0           1               _none_     true    _none_     FALSE     OtherConfigProcess-PortAndProtocolVlanId    _none_    _none_}
        {tlv_vlan_name_enable                               _none_                                          _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-VlanName    _none_    _none_}
        {tlv_vlan_name_count                                _none_                                          _none_                          NUMERIC                     0           1               _none_     true    _none_     FALSE     OtherConfigProcess-VlanName    _none_    _none_}
        {tlv_vlan_name_vid_list                              lldp:VlanNameTlv                               vlanid                          ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-VlanName    _none_    _none_}
        {tlv_vlan_name_value_list                            lldp:VlanNameTlv                               vlanName                        ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-VlanName    _none_    _none_}
        {tlv_protocol_identity_enable                          _none_                                       _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-ProtocolIdentity    _none_    _none_}
        {tlv_protocol_identity_count                           _none_                                       _none_                          NUMERIC                     0           1               _none_     true    _none_     FALSE     OtherConfigProcess-ProtocolIdentity    _none_    _none_}
        {tlv_protocol_identity_value_list                    lldp:ProtocolIdentityTlv                       protocolIdentity                ANY                         0         _none_            _none_     true    _none_     FALSE     OtherConfigProcess-ProtocolIdentity    _none_    _none_}
        {tlv_mac_phy_config_status_enable                      _none_                                       _none_                          FLAG                        0           0               _none_     true    _none_     FALSE     OtherConfigProcess-MacPhyConfigStatus    _none_    _none_}
        {tlv_mac_phy_config_status_auto_negotiation_supported_flag            lldp:MacPhyConfigStatusTlv-autoNegotiationSupportAndStatus    autoNegotiationSupported        FLAG     0    0         _none_    true    _none_     FALSE     OtherConfigProcess-MacPhyConfigStatus    _none_    _none_}
        {tlv_mac_phy_config_status_auto_negotiation_status_flag               lldp:MacPhyConfigStatusTlv-autoNegotiationSupportAndStatus    autoNegotiationEnabled          FLAG     0    0         _none_    true    _none_     FALSE     OtherConfigProcess-MacPhyConfigStatus    _none_    _none_}
        {tlv_mac_phy_config_status_auto_negotiation_advertised_capability     lldp:MacPhyConfigStatusTlv-autoNegotiationAdvertisedCapability    _none_      {REGEXP [0-9a-fA-F]{4}}  0    "0800"    _none_    true    _none_     FALSE     OtherConfigProcess-MacPhyConfigStatus    _none_    _none_}
        {tlv_mac_phy_config_status_operational_mau_type     lldp:MacPhyConfigStatusTlv                      operationalMauType              {REGEXP [0-9a-fA-F]{4}}     0           "0800"          _none_    true    _none_     FALSE     OtherConfigProcess-MacPhyConfigStatus    _none_    _none_}
        {tlv_power_via_mdi_enable                                _none_                                     _none_                          FLAG                        0               0          _none_    true    _none_     FALSE     OtherConfigProcess-PowerViaMdi    _none_    _none_}
        {tlv_power_via_mdi_power_support_bits               lldp:PowerViaMdiTlv-mdiPowerSupport             _none_                          {REGEXP [01]{4}}            0               "0000"     _none_    true    _none_     FALSE     OtherConfigProcess-PowerViaMdi    _none_    _none_}
        {tlv_power_via_mdi_pse_power_pair                   lldp:PowerViaMdiTlv                             psePowerPairs                   {CHOICES signal spare}      0               signal     _none_    true    _none_     FALSE     OtherConfigProcess-PowerViaMdi    _none_    {signal "01" spare "02"}}
        {tlv_power_via_mdi_pse_power_class                  lldp:PowerViaMdiTlv                             psePowerClass                   {CHOICES class1 class2 class3 class4 class5}   0    class1    _none_    true    _none_     FALSE     OtherConfigProcess-PowerViaMdi    _none_    {class1 "01" class2 "02" class3 "03" class4 "04" class5 "05"}}
        {tlv_link_aggregation_enable                        _none_                                          _none_                          FLAG                        0               0          _none_    true    _none_     FALSE     OtherConfigProcess-LinkAggregation    _none_    _none_}
        {tlv_link_aggregation_status_flag                   lldp:LinkAggregationTlv-aggregationStatus       aggregationStatus               FLAG                        0               1          _none_    true    _none_     FALSE     OtherConfigProcess-LinkAggregation    _none_    _none_}
        {tlv_link_aggregation_capability_flag               lldp:LinkAggregationTlv-aggregationStatus       aggregationCapability           FLAG                        0               1          _none_    true    _none_     FALSE     OtherConfigProcess-LinkAggregation    _none_    _none_}
        {tlv_link_aggregation_aggregated_port_id            lldp:LinkAggregationTlv                         aggregatedPortid                {REGEXP [0-9a-fA-F]{8}}     0               "0000000E" _none_    true    _none_     FALSE     OtherConfigProcess-LinkAggregation    _none_    _none_}
        {tlv_maximum_frame_size_enable                      _none_                                          _none_                          FLAG                        0               0          _none_    true    _none_     FALSE     OtherConfigProcess-MaxFrameSize    _none_    _none_}
        {tlv_maximum_frame_size_value                       lldp:MaxFrameSizeTlv                            frameSize                       NUMERIC                     0               1518      0-65535    true    _none_     FALSE     OtherConfigProcess-MaxFrameSize    _none_    _none_}
        {tlv_customized_enable                              _none_                                          _none_                          FLAG                        0               0          _none_    true    _none_     FALSE     OtherConfigProcess-Custom    _none_    _none_}
        {tlv_customized_type                                lldp:CustomTlv                                  type                            NUMERIC                     0               9           0-127    true    _none_     FALSE     OtherConfigProcess-Custom    _none_    _none_}
        {tlv_customized_value                               lldp:CustomTlv                                  length                          {REGEXP [0-9a-fA-F]+}       0               "00"       _none_    true    _none_     FALSE     OtherConfigProcess-Custom    _none_    _none_}
    }
    {emulation_lldp_dcbx_tlv_config
        {hname                                                  stcobj                              stcattr             type     priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {version_num                                        Common-LldpTlvConfig                     _none_             {CHOICES ver_100 ver_103}    0    ver_100    _none_    TRUE    _none_    false    CreateObject    _none_    {ver_100 "PDU_DcbxType1" ver_103 "PDU_DcbxType2"}}
        {control_tlv_oper_version                           Common-dcbxCtlTlv                       operVer             NUMERIC         11    0    0-255    TRUE    _none_    FALSE    ConfigParameter    _none_    _none_}
        {control_tlv_max_version                            Common-dcbxCtlTlv                       maxVer              NUMERIC         11    0    0-255    TRUE    _none_    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_enable                             Common-value                            _none_              FLAG            20    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxPG_Type1" 0 ""}}
        {pg_feature_tlv1_oper_version                       TLV_DcbxPG_Type1-header                 operVer             NUMERIC         21    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_max_version                        TLV_DcbxPG_Type1-header                 maxVer              NUMERIC         21    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_enabled_flag                       TLV_DcbxPG_Type1-header                 en                  FLAG            21    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_willing_flag                       TLV_DcbxPG_Type1-header                 w                   FLAG            21    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_error_flag                         TLV_DcbxPG_Type1-header                 er                  FLAG            21    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_subtype                            TLV_DcbxPG_Type1-header                 subtype             NUMERIC         21    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv1_bwg_percentage_list                TLV_DcbxPG_Type1-bwg_percentage         {bwg_percentage0 bwg_percentage1 bwg_percentage2 bwg_percentage3 bwg_percentage4 bwg_percentage5 bwg_percentage6 bwg_percentage7}    ANY    30    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiAttributesVaryParameters    _none_    _none_}
        {pg_feature_tlv1_prio_alloc_bwg_id_list             {TLV_DcbxPG_Type1-priority0Allocation priority1Allocation priority2Allocation priority3Allocation priority4Allocation priority5Allocation priority6Allocation priority7Allocation}    bwg_id    ANY    30    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {pg_feature_tlv1_prio_alloc_strict_prio_list        {TLV_DcbxPG_Type1-priority0Allocation priority1Allocation priority2Allocation priority3Allocation priority4Allocation priority5Allocation priority6Allocation priority7Allocation}    strict_prio    ANY    30    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {pg_feature_tlv1_prio_alloc_bw_percentage_list      {TLV_DcbxPG_Type1-priority0Allocation priority1Allocation priority2Allocation priority3Allocation priority4Allocation priority5Allocation priority6Allocation priority7Allocation}    bw_percentage    ANY    30    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {pfc_feature_tlv1_enable                            Common-value                            _none_              FLAG            40    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxPFC_Type1" 0 ""}}
        {pfc_feature_tlv1_oper_version                      TLV_DcbxPFC_Type1-header                operVer             NUMERIC         41    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_max_version                       TLV_DcbxPFC_Type1-header                maxVer              NUMERIC         41    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_enabled_flag                      TLV_DcbxPFC_Type1-header                en                  FLAG            41    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_willing_flag                      TLV_DcbxPFC_Type1-header                w                   FLAG            41    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_error_flag                        TLV_DcbxPFC_Type1-header                er                  FLAG            41    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_subtype                           TLV_DcbxPFC_Type1-header                subtype             NUMERIC         41    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv1_admin_mode_bits                   TLV_DcbxPFC_Type1-pfcTlv                {pe0 pe1 pe2 pe3 pe4 pe5 pe6 pe7}    {REGEXP [01]{8}}    45    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiAttributesVaryParameters    _none_    _none_}
        {application_feature_tlv1_enable                    Common-value                            _none_              FLAG            60    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxApp_Type1" 0 ""}}
        {application_feature_tlv1_oper_version              TLV_DcbxApp_Type1-header                operVer             NUMERIC         61    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {application_feature_tlv1_max_version               TLV_DcbxApp_Type1-header                maxVer              NUMERIC         61    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {application_feature_tlv1_enabled_flag              TLV_DcbxApp_Type1-header                en                  FLAG            61    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {application_feature_tlv1_error_flag                TLV_DcbxApp_Type1-header                er                  FLAG            61    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {application_feature_tlv1_subtype                   TLV_DcbxApp_Type1-header                subtype             NUMERIC         61    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {application_feature_tlv1_prio_map                  TLV_DcbxApp_Type1-applicatonTlv         priorityMap        {REGEXP [01]{8}} 70    1000    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_enable                            Common-value                            _none_              FLAG            80    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxBCN_Type1" 0 ""}}
        {bcn_feature_tlv1_oper_version                      TLV_DcbxBCN_Type1-header                operVer             NUMERIC         81    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_max_version                       TLV_DcbxBCN_Type1-header                maxVer              NUMERIC         81    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_enabled_flag                      TLV_DcbxBCN_Type1-header                en                  FLAG            81    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_willing_flag                      TLV_DcbxBCN_Type1-header                w                   FLAG            81    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_error_flag                        TLV_DcbxBCN_Type1-header                er                  FLAG            81    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_subtype                           TLV_DcbxBCN_Type1-header                subtype             NUMERIC         81    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_bcna_value                        TLV_DcbxBCN_Type1-bcnTlv                bcna                {REGEXP [0-9a-fA-F]{1,16}}    85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_cp_admin_mode_list                {TLV_DcbxBCN_Type1-bcnMode0 bcnMode1 bcnMode2 bcnMode3 bcnMode4 bcnMode5 bcnMode6 bcnMode7}    cpAdmin    ANY    91    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {bcn_feature_tlv1_rp_admin_mode_list                {TLV_DcbxBCN_Type1-bcnMode0 bcnMode1 bcnMode2 bcnMode3 bcnMode4 bcnMode5 bcnMode6 bcnMode7}    rpAdmin    ANY    91    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {bcn_feature_tlv1_rp_oper_mode_list                 {TLV_DcbxBCN_Type1-bcnMode0 bcnMode1 bcnMode2 bcnMode3 bcnMode4 bcnMode5 bcnMode6 bcnMode7}    rpOper    ANY    91    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {bcn_feature_tlv1_rem_tag_oper_mode_list            {TLV_DcbxBCN_Type1-bcnMode0 bcnMode1 bcnMode2 bcnMode3 bcnMode4 bcnMode5 bcnMode6 bcnMode7}    remTagOper     ANY    91    _none_    _none_    TRUE    {version_num ver_100}    FALSE    ConfigMultiObjectTypesVaryParameters    _none_    _none_}
        {bcn_feature_tlv1_rp_gd                             TLV_DcbxBCN_Type1-bcnTlv                rpGd                ANY             85    _none_    _none_    FALSE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_gi                             TLV_DcbxBCN_Type1-bcnTlv                rpGi                ANY             85    _none_    _none_    FALSE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_w                              TLV_DcbxBCN_Type1-bcnTlv                rpW                 NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_tmax                           TLV_DcbxBCN_Type1-bcnTlv                rpTmax              NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_rmin                           TLV_DcbxBCN_Type1-bcnTlv                rpRmin              NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_alpha                          TLV_DcbxBCN_Type1-bcnTlv                rpAlpha             ANY             85    _none_    _none_    FALSE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_beta                           TLV_DcbxBCN_Type1-bcnTlv                rpBeta              ANY             85    _none_    _none_    FALSE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_td                             TLV_DcbxBCN_Type1-bcnTlv                rpTd                NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_rp_rd                             TLV_DcbxBCN_Type1-bcnTlv                rpRd                NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {bcn_feature_tlv1_cp_sf                             TLV_DcbxBCN_Type1-bcnTlv                cpSf                NUMERIC         85    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_enable                            Common-value                            _none_              FLAG            120    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxLLD_Type1" 0 ""}}
        {lld_feature_tlv1_oper_version                      TLV_DcbxLLD_Type1-header                operVer             NUMERIC         121    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_max_version                       TLV_DcbxLLD_Type1-header                maxVer              NUMERIC         121    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_enabled_flag                      TLV_DcbxLLD_Type1-header                en                  FLAG            121    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_willing_flag                      TLV_DcbxLLD_Type1-header                w                   FLAG            121    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_error_flag                        TLV_DcbxLLD_Type1-header                er                  FLAG            121    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_subtype                           TLV_DcbxLLD_Type1-header                subtype             NUMERIC         121    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {lld_feature_tlv1_status_value                      TLV_DcbxLLD_Type1-logicLinkDownTlv      status              FLAG            130    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_enable                     Common-value                            _none_              FLAG            140    0    _none_    TRUE    {version_num ver_100}    FALSE    CreateObject    _none_    {1 "TLV_DcbxCustom_Type1" 0 ""}}
        {customized_feature_tlv1_oper_version               TLV_DcbxCustom_Type1-header             operVer             NUMERIC         141    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_max_version                TLV_DcbxCustom_Type1-header             maxVer              NUMERIC         141    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_enabled_flag               TLV_DcbxCustom_Type1-header             en                  FLAG            141    1    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_willing_flag               TLV_DcbxCustom_Type1-header             w                   FLAG            141    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_error_flag                 TLV_DcbxCustom_Type1-header             er                  FLAG            141    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_subtype                    TLV_DcbxCustom_Type1-header             subtype             NUMERIC         141    0    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_type                       TLV_DcbxCustom_Type1-header             type                NUMERIC         141    10    0-255    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv1_value                      TLV_DcbxCustom_Type1-customTlv          value       {REGEXP [0-9a-fA-F]+}   150    0    _none_    TRUE    {version_num ver_100}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_enable                             Common-value                            Children            FLAG            20    0    _none_    TRUE    {version_num ver_103}    FALSE    CreateObject    _none_    {1 "TLV_DcbxPG_Type2" 0 ""}}
        {pg_feature_tlv2_oper_version                       TLV_DcbxPG_Type2-header                 operVer             NUMERIC         21    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_max_version                        TLV_DcbxPG_Type2-header                 maxVer              NUMERIC         21    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_enabled_flag                       TLV_DcbxPG_Type2-header                 en                  FLAG            21    1    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_willing_flag                       TLV_DcbxPG_Type2-header                 w                   FLAG            21    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_error_flag                         TLV_DcbxPG_Type2-header                 er                  FLAG            21    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_subtype                            TLV_DcbxPG_Type2-header                 subtype             NUMERIC         21    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pg_feature_tlv2_prio_alloc_pgid_list               TLV_DcbxPG_Type2-prioAllocation         {pgid0 pgid1 pgid2 pgid3 pgid4 pgid5 pgid6 pgid7}    ANY    35    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiAttributesVaryParameters    _none_    _none_}
        {pg_feature_tlv2_pg_alloc_bw_percentage_list        TLV_DcbxPG_Type2-pgAllocation           {BW0 BW1 BW2 BW3 BW4 BW5 BW6 BW7}    ANY    35    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiAttributesVaryParameters    _none_    _none_}
        {pg_feature_tlv2_num_tcs_supported                  TLV_DcbxPG_Type2-pgTlv                  numTCs              NUMERIC         35    0    0-7    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_enable                            Common-value                            _none_              FLAG            40    0    _none_    TRUE    {version_num ver_103}    FALSE    CreateObject    _none_    {1 "TLV_DcbxPFC_Type2" 0 ""}}
        {pfc_feature_tlv2_oper_version                      TLV_DcbxPFC_Type2-header                operVer             NUMERIC         41    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_max_version                       TLV_DcbxPFC_Type2-header                maxVer              NUMERIC         41    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_enabled_flag                      TLV_DcbxPFC_Type2-header                en                  FLAG            41    1    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_willing_flag                      TLV_DcbxPFC_Type2-header                w                   FLAG            41    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_error_flag                        TLV_DcbxPFC_Type2-header                er                  FLAG            41    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_subtype                           TLV_DcbxPFC_Type2-header                subtype             NUMERIC         41    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_admin_mode_bits                   TLV_DcbxPFC_Type2-pfcTlv                {pe0 pe1 pe2 pe3 pe4 pe5 pe6 pe7}    {REGEXP [01]{8}}    45    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {pfc_feature_tlv2_num_tcpfcs_supported              TLV_DcbxPFC_Type2-pfcTlv                numTCPFCs           NUMERIC         50    0    0-7    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_enable                           Common-value                            _none_              FLAG            160    0    _none_    TRUE    {version_num ver_103}    FALSE    CreateObject    _none_    {1 "TLV_DcbxAppPro_Type2" 0 ""}}
        {app_protocol_tlv2_oper_version                     TLV_DcbxAppPro_Type2-header             operVer             NUMERIC         161    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_max_version                      TLV_DcbxAppPro_Type2-header             maxVer              NUMERIC         161    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_enabled_flag                     TLV_DcbxAppPro_Type2-header             en                  FLAG            161    1    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_willing_flag                     TLV_DcbxAppPro_Type2-header             w                   FLAG            161    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_error_flag                       TLV_DcbxAppPro_Type2-header             er                  FLAG            161    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_subtype                          TLV_DcbxAppPro_Type2-header             subtype             NUMERIC         161    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {app_protocol_tlv2_protocol_count                   TLV_DcbxAppPro_Type2-app                AppStruct           NUMERIC         170    0    _none_    TRUE    {version_num ver_103}    FALSE    CreateMultiObjects    _none_    _none_}
        {app_protocol_tlv2_app_id_list                      TLV_DcbxAppPro_Type2-AppStruct          appId               ANY             171    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiObjectsVaryParameters    _none_    _none_}
        {app_protocol_tlv2_oui_upper_6_bits_list            TLV_DcbxAppPro_Type2-AppStruct          upperOUI            ANY             171    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiObjectsVaryParameters    _none_    _none_}
        {app_protocol_tlv2_sf_list                          TLV_DcbxAppPro_Type2-AppStruct          sf                  ANY             171    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiObjectsVaryParameters    _none_    _none_}
        {app_protocol_tlv2_oui_lower_2_bytes_list           TLV_DcbxAppPro_Type2-AppStruct          lowerOUI            ANY             171    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiObjectsVaryParameters    _none_    _none_}
        {app_protocol_tlv2_prio_map_list                    TLV_DcbxAppPro_Type2-AppStruct          priorityMap         ANY             171    _none_    _none_    TRUE    {version_num ver_103}    FALSE    ConfigMultiObjectsVaryParameters    _none_    _none_}
        {customized_feature_tlv2_enable                     Common-value                            _none_              FLAG            140    0    _none_    TRUE    {version_num ver_103}    FALSE    CreateObject    _none_    {1 "TLV_DcbxCustom_Type2" 0 ""}}
        {customized_feature_tlv2_oper_version               TLV_DcbxCustom_Type2-header             operVer             NUMERIC         141    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_max_version                TLV_DcbxCustom_Type2-header             maxVer              NUMERIC         141    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_enabled_flag               TLV_DcbxCustom_Type2-header             en                  FLAG            141    1    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_willing_flag               TLV_DcbxCustom_Type2-header             w                   FLAG            141    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_error_flag                 TLV_DcbxCustom_Type2-header             er                  FLAG            141    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_subtype                    TLV_DcbxCustom_Type2-header             subtype             NUMERIC         141    0    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_type                       TLV_DcbxCustom_Type2-header             type                NUMERIC         141    10    0-255    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
        {customized_feature_tlv2_value                      TLV_DcbxCustom_Type2-customTlv          value      {REGEXP [0-9a-fA-F]+}    150    0    _none_    TRUE    {version_num ver_103}    FALSE    ConfigParameter    _none_    _none_}
    }
    {emulation_lldp_control 
        {hname     stcobj    stcattr     type     priority    default    range    supported    dependency     mandatory     procfunc    mode    constants}
        {handle     _none_    _none_     ALPHANUM     0    _none_    _none_    true    _none_     TRUE     _none_    _none_    _none_}
        {mode     _none_    _none_     {CHOICES start stop pause resume}     0    _none_    _none_    true    _none_     TRUE     _none_    _none_    _none_}
   }
    {emulation_lldp_info
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {handle    _none_    _none_    ALPHANUM    0    _none_    _none_    true    _none_    TRUE    _none_    _none_    _none_}
        {mode    _none_    _none_    {CHOICES lldp dcbx both}    0    lldp    _none_    true    _none_    TRUE    _none_    _none_    _none_}
        {dcbx_info_type    _none_    _none_    {REGEXP ((basic|feature_basic|prio_alloc|bw_alloc|pfc|fcoe_prio|logic_link|bcn_parameter|bcn_mode)\|)*(basic|feature_basic|prio_alloc|bw_alloc|pfc|fcoe_prio|logic_link|bcn_parameter|bcn_mode) }    0    "basic|feature_basic"    _none_    true    _none_    FALSE    _none_    {dcbx "" both "" }    _none_}
    }
    {emulation_lldp_node_results
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {lldp.lldp_session_state    LldpNodeConfig    DeviceState    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both ""}    _none_}
        {lldp.tx_port_frame_count    LldpNodeResults    TxPortFrameCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both ""}    _none_}
        {lldp.rx_port_frame_discarded_count    LldpNodeResults    RxPortFrameDiscardedCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp.rx_port_error_frame_count    LldpNodeResults    RxPortErrorFrameCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp.rx_port_frame_count    LldpNodeResults    RxPortFrameCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp.rx_port_tlvs_discarded_count    LldpNodeResults    RxPortTlvsDiscardedCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp.rx_port_tlvs_unrecognized_count    LldpNodeResults    RxPortTlvsUnrecognizedCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp.rx_port_age_outs_count    LldpNodeResults    RxPortAgeOutsCount    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
    }
    {emulation_lldp_neighbor_results
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {lldp_neighbor.xxx.neighbor_chassis_id_subtype    LldpNeighborResults    ChassisIdSubtype    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp_neighbor.xxx.neighbor_chassis_id    LldpNeighborResults    ChassisId    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp_neighbor.xxx.neighbor_port_id_subtype    LldpNeighborResults    PortIdSubtype    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp_neighbor.xxx.neighbor_port_id    LldpNeighborResults    PortId    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
        {lldp_neighbor.xxx.neighbor_time_to_live    LldpNeighborResults    TimeToLive    ANY    0    _none_    _none_    true    _none_    FALSE        {lldp "" both "" }    _none_}
    }
    {emulation_lldp_dcbx_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.max_version    LldpDcbxResult    MaxVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.peer_max_version    LldpDcbxResult    PeerMaxVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic ""}    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.operating_version    LldpDcbxResult    OperatingVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic ""}    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.seq_number    LldpDcbxResult    SeqNumber    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic ""}    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.ack_number    LldpDcbxResult    AckNumber    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.peer_seq_number    LldpDcbxResult    PeerSeqNumber    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.peer_ack_number    LldpDcbxResult    PeerAckNumber    ANY    0    _none_    _none_    true    {dcbx_info_type "" basic "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_lldp_dcbx_feature_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.feature_basic.xxx.type    LldpDcbxFeatureResult    Type    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.subtype    LldpDcbxFeatureResult    Subtype    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.max_version    LldpDcbxFeatureResult    MaxVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.peer_max_version    LldpDcbxFeatureResult    PeerMaxVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.operating_version    LldpDcbxFeatureResult    OperatingVersion    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.enable    LldpDcbxFeatureResult    Enable    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.advertise    LldpDcbxFeatureResult    Advertise    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.peer_advertise    LldpDcbxFeatureResult    PeerAdvertise    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.willing    LldpDcbxFeatureResult    Willing    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.error    LldpDcbxFeatureResult    Error    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.operating_mode    LldpDcbxFeatureResult    OperatingMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.syncd    LldpDcbxFeatureResult    Syncd    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.feature_seq_number    LldpDcbxFeatureResult    FeatureSeqNumber    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.peer_willing    LldpDcbxFeatureResult    PeerWilling    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.peer_error    LldpDcbxFeatureResult    PeerError    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.feature_basic.xxx.peer_enable    LldpDcbxFeatureResult    PeerEnable    ANY    0    _none_    _none_    true    {dcbx_info_type "" feature_basic "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_priority_allocation_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.prio_alloc.xxx.priority    DcbxPriorityAllocationResult    Priority    ANY    0    _none_    _none_    true    {dcbx_info_type "" prio_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.prio_alloc.xxx.priority_group_id    DcbxPriorityAllocationResult    PriorityGroupId    ANY    0    _none_    _none_    true    {dcbx_info_type "" prio_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.prio_alloc.xxx.desired_priority_group_id    DcbxPriorityAllocationResult    DesiredPriorityGroupId    ANY    0    _none_    _none_    true    {dcbx_info_type "" prio_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.prio_alloc.xxx.peer_priority_group_id    DcbxPriorityAllocationResult    PeerPriorityGroupId    ANY    0    _none_    _none_    true    {dcbx_info_type "" prio_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_bandwidth_allocaton_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.bw_alloc.xxx.priority_group_id    DcbxBandwidthAllocationResult    PriorityGroupId    ANY    0    _none_    _none_    true    {dcbx_info_type "" bw_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bw_alloc.xxx.bandwidth_percentage    DcbxBandwidthAllocationResult    BandwidthPercentage    ANY    0    _none_    _none_    true    {dcbx_info_type "" bw_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bw_alloc.xxx.desired_bandwidth_percentage    DcbxBandwidthAllocationResult    DesiredBandwidthPercentage    ANY    0    _none_    _none_    true    {dcbx_info_type "" bw_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bw_alloc.xxx.peer_bandwidth_percentage    DcbxBandwidthAllocationResult    PeerBandwidthPercentage    ANY    0    _none_    _none_    true    {dcbx_info_type "" bw_alloc "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_priority_flow_control_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.pfc.xxx.priority    DcbxPriorityFlowControlResult    Priority    ANY    0    _none_    _none_    true    {dcbx_info_type "" pfc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.pfc.xxx.status    DcbxPriorityFlowControlResult    Status    ANY    0    _none_    _none_    true    {dcbx_info_type "" pfc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.pfc.xxx.desired_status    DcbxPriorityFlowControlResult    DesiredStatus    ANY    0    _none_    _none_    true    {dcbx_info_type "" pfc "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.pfc.xxx.peer_status    DcbxPriorityFlowControlResult    PeerStatus    ANY    0    _none_    _none_    true    {dcbx_info_type "" pfc "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulatiion_dcbx_fcoe_priority_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.fcoe_prio.xxx.selector_field    DcbxFcoePriorityResult    SelectorField    ANY    0    _none_    _none_    true    {dcbx_info_type "" fcoe_prio "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.fcoe_prio.xxx.protocol_id    DcbxFcoePriorityResult    ProtocolId    ANY    0    _none_    _none_    true    {dcbx_info_type "" fcoe_prio "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.fcoe_prio.xxx.priority_map    DcbxFcoePriorityResult    PriorityMap    ANY    0    _none_    _none_    true    {dcbx_info_type "" fcoe_prio "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.fcoe_prio.xxx.desired_priority_map    DcbxFcoePriorityResult    DesiredPriorityMap    ANY    0    _none_    _none_    true    {dcbx_info_type "" fcoe_prio "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.fcoe_prio.xxx.peer_priority_map    DcbxFcoePriorityResult    PeerPriorityMap    ANY    0    _none_    _none_    true    {dcbx_info_type "" fcoe_prio "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_logic_link_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.logic_link.xxx.type    DcbxLogicalLinkResult    Type    ANY    0    _none_    _none_    true    {dcbx_info_type "" logic_link "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.logic_link.xxx.status    DcbxLogicalLinkResult    Status    ANY    0    _none_    _none_    true    {dcbx_info_type "" logic_link "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.logic_link.xxx.peer_status    DcbxLogicalLinkResult    PeerStatus    ANY    0    _none_    _none_    true    {dcbx_info_type "" logic_link "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_bcn_parameter_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.bcn_parameter.xxx.type    DcbxBcnParameterResult    Type    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.bcna    DcbxBcnParameterResult    Bcna    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_alpha    DcbxBcnParameterResult    RpAlpha    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_beta    DcbxBcnParameterResult    RpBeta    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_gd    DcbxBcnParameterResult    RpGd    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_gi    DcbxBcnParameterResult    RpGi    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_tmax    DcbxBcnParameterResult    RpTmax    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.cp_sf    DcbxBcnParameterResult    CpSf    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_td    DcbxBcnParameterResult    RpTd    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_rmin    DcbxBcnParameterResult    RpRmin    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_w    DcbxBcnParameterResult    Rpw    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_parameter.xxx.rp_rd    DcbxBcnParameterResult    Rprd    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_parameter "" }    FALSE        {dcbx "" both "" }    _none_}
    }
    {emulation_dcbx_bcn_mode_result
        {hname    stcobj    stcattr    type    priority    default    range    supported    dependency    mandatory    procfunc    mode    constants}
        {dcbx.bcn_mode.xxx.priority    DcbxBcnModeResult    Priority    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.cp_admin_mode    DcbxBcnModeResult    CpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.rp_admin_mode    DcbxBcnModeResult    RpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.rp_operating_mode    DcbxBcnModeResult    RpOperatingMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.remove_tag_operational_mode    DcbxBcnModeResult    RemoveTagOperationalMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.peer_cp_admin_mode    DcbxBcnModeResult    PeerCpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.peer_rp_admin_mode    DcbxBcnModeResult    PeerRpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.peer_rp_operating_mode    DcbxBcnModeResult    PeerRpOperatingMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.peer_remove_tag_operational_mode    DcbxBcnModeResult    PeerRemoveTagOperationalMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.desired_cp_admin_mode    DcbxBcnModeResult    DesiredCpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.desired_rp_admin_mode    DcbxBcnModeResult    DesiredRpAdminMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.desired_rp_operating_mode    DcbxBcnModeResult    DesiredRpOperatingMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
        {dcbx.bcn_mode.xxx.desired_remove_tag_operational_mode    DcbxBcnModeResult    DesiredRemoveTagOperationalMode    ANY    0    _none_    _none_    true    {dcbx_info_type "" bcn_mode "" }    FALSE        {dcbx "" both "" }    _none_}
    }
}