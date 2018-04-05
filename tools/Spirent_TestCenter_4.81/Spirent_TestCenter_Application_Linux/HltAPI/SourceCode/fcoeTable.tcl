# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::fcoe:: {
}

set ::sth::fcoe::fcoeTable {
   ::sth::fcoe::
   {fcoe_config
      {hname           stcobj       stcattr       type       priority   default   range   supported  dependency mandatory mode     procfunc    constants}
      {port_handle     _none_         _none_      ALPHANUM        1     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {handle          _none_         _none_      ALPHANUM        1     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {mode            _none_         _none_ {CHOICES create modify reset} 1 _none_ _none_  TRUE     _none_     TRUE     {create "" modify "" reset ""}       _none_    _none_}
      {vnport_count    _none_         deviceCount      NUMERIC         2     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {device_count    _none_         _none_      NUMERIC         2     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {mac_addr        ethiiif         SourceMac  ANY             3     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {mac_addr_step   ethiiif         SrcMacStep ANY             4     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {encap  _none_ _none_ {CHOICES ethernet_ii ethernet_ii_vlan ethernet_ii_qinq} 5 ethernet_ii _none_ TRUE  _none_ FALSE {create "" modify "" reset ""}     _none_    _none_}
      {vlan_id         VlanIf         VlanId      NUMERIC         6     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_pri        VlanIf         Priority      NUMERIC         7     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_user_priority        VlanIf         _none_      NUMERIC         7     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_cfi        VlanIf         Cfi      {CHOICES 0 1}   8     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_id_outer   VlanIf_Outer         VlanId      NUMERIC         9     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_pri_outer  VlanIf_Outer         Priority      NUMERIC         10    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_user_priority_outer  VlanIf_Outer         _none_      NUMERIC         10    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {vlan_cfi_outer  VlanIf_Outer         Cfi      {CHOICES 0 1}   11    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {wwpn            fcif           WorldWideName     ANY       12    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {wwpn_step       fcif           WorldWideNameStep ANY       13    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      
      {protocol        _none_ _none_ {CHOICES fcoe fip } 15 _none_ _none_ TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {login_delay     fcoeglobalparams LoginDelay  NUMERIC         16    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {logout_delay    fcoeglobalparams logoutDelay NUMERIC         17    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      
      {addressing_mode fcoehostconfig AddressingMode {CHOICES fpma spma both} 18 _none_ _none_ TRUE  _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {bb_credit       fcoehostconfig BbCredit    NUMERIC         19    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {fcf_mac_addr    fcoehostconfig FcfMacAddr  ANY             20    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {fc_map          fcoehostconfig FcMap       ALPHANUM        21    _none_    _none_    TRUE     _none_     FALSE     {create "processFcMapConfig" modify "processFcMapConfig" reset ""}       _none_    _none_}
      {fip_priority    fcoehostconfig FipPriority NUMERIC         22    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {enable_vlan_discovery fcoehostconfig VlanDiscovery   {CHOICES 0 1} 23 _none_ _none_  TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {host_type       fcoehostconfig HostType    {CHOICES initiator target both} 23 _none_ _none_ TRUE _none_  FALSE     {create "" modify "" reset ""}       _none_    _none_}      
      {max_rx_size     fcoehostconfig MaxRxSize   NUMERIC         25    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {use_wwpn        fcoehostconfig UseFcIfWorldWidePortName {CHOICES 0 1} 26 _none_ _none_ TRUE   _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {wwnn            fcoehostconfig WorldWideNodeName     ANY   28    _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {wwnn_step       fcoehostconfig WorldWideNodeNameStep ANY   3     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {enode_count     fcoehostconfig EnodeCount  NUMERIC         3     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      
      {vnport_name     _none_         _none_      ALPHANUM       101     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
      {wwpn_count      _none_         _none_      NUMERIC        101     _none_    _none_    TRUE     _none_     FALSE     {create "" modify "" reset ""}       _none_    _none_}
   }
   {fcoe_control
      {hname      stcobj      stcattr     type             priority        default   range   supported dependency mandatory procfunc action constants}
      {handle     _none_    _none_      ALPHANUM           1                _none_   _none_  TRUE      _none_     TRUE     _none_   _none_ _none_}
      {action  _none_ _none_ {CHOICES discovery login logout start stop}  1 _none_   _none_  TRUE      _none_     TRUE      _none_   _none_ {discovery FcoeDiscovery login FcoeLogin logout Fcoelogout start FcoeStart stop FcoeStop}}
   }
   {fcoe_stats
      {hname         stcobj      stcattr     type                        priority  default   range   supported  dependency   mandatory  procfunc  mode   constants}
      {handle        _none_      _none_      ALPHANUM                       1      _none_    _none_    TRUE     _none_       TRUE       _none_    _none_ _none_}
      {mode          _none_      _none_      {CHOICES summary vnport all}    2      summary   _none_   TRUE     _none_       FALSE      _none_    _none_ _none_}     
   }
   {fcoe_stats_summary
      {hname         stcobj                stcattr           type     priority    default    range  supported  dependency   mandatory  procfunc   mode    constants}
      {vnport_down   FcoeSummaryResults    VnPortDownCount   ANY          16      _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {vnport_up     FcoeSummaryResults    VnPortUpCount     ANY          16      _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {ka_period     FcoeSummaryResults    KeepAlivePeriod   ANY          16      _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {rx_uni_adv    FcoeSummaryResults  RxUnicastAdvertisementCount ANY  16 _none_ _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {rx_multi_adv  FcoeSummaryResults    RxMulticastAdvertisementCount  ANY     16 _none_ _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {rx_cvl        FcoeSummaryResults    RxClearVirtualLinksCount ANY   16 _none_ _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {rx_acc        FcoeSummaryResults    RxacceptCount     ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {rx_rjt        FcoeSummaryResults    RxrejectCount     ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_uni_soli  FcoeSummaryResults     TxUnicastSolicatationCount ANY 16 _none_ _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_ka         FcoeSummaryResults    TxKeepAliveCount  ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_flogi      FcoeSummaryResults    TxFlogiCount      ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_fdisc      FcoeSummaryResults    TxfdiscCount      ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_plogi      FcoeSummaryResults    TxPlogiCount      ANY          16     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
      {tx_logo       FcoeSummaryResults    TxlogoCount       ANY           6     _none_    _none_    TRUE     _none_     _none_       _none_    _none_    _none_    }
   }
   {fcoe_stats_vnport
      {hname           stcobj               stcattr            type     priority  default  range    supported  dependency  mandatory procfunc  mode     constants}
      {state           FcoeVnPortResults    State              ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {substate        FcoeVnPortResults    SubState           ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {rx_vlan_notification  FcoeVnPortResults RxVlanNotificationCount ANY  16    _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {tx_vlan_req     FcoeVnPortResults    TxVlanRequestCount ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {granted_macaddr FcoeVnPortResults    GrantedMacAddr     ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {fcid            FcoeVnPortResults    FcId               ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {dst_mac_adddr   FcoeVnPortResults    DstMacAddr         ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {wwpn            FcoeVnPortResults    WorldWidePortName  ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {wwnn            FcoeVnPortResults    WorldWideNodeName  ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
      {granted_vlanid  FcoeVnPortResults    GrantedVlanId      ANY      16        _none_    _none_    TRUE     _none_      _none_    _none_    _none_    _none_    }
   }
}