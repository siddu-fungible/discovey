# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::fc:: {
}

set ::sth::fc::fcTable {
   ::sth::fc::
   {fc_config
      {hname        stcobj          stcattr          type      priority     default     range     supported     dependency  mandatory         mode     procfunc    constants}
      {port_handle  _none_          _none_      ALPHANUM          1          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {handle       _none_          _none_      ALPHANUM          1          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {mode         _none_          _none_      {CHOICES create modify reset}     1   _none_          _none_    TRUE   _none_            FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {nport_count  host            DeviceCount      NUMERIC     2          1   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {wwpn         fcif            WorldWideName      ANY        3          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {wwpn_step    fcif            WorldWideNameStep  ANY        3          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {host_type    fchostconfig  HostType            {CHOICES INITIATOR initiator TARGET target BOTH both}   4          initiator     _none_      TRUE    _none_            FALSE         {create "" modify "" reset ""}       _none_    _none_}      
      {wwnn         fchostconfig|fcfportconfig  WorldWideNodeName   ANY       4          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {wwnn_step    fchostconfig|fcfportconfig  WorldWideNodeNameStep  ANY        4          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {login_delay  fcglobalparams LoginDelay   NUMERIC   5       10    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {logout_delay fcglobalparams logoutDelay  NUMERIC   5       10    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {retry_count  fcglobalparams RetryCount   NUMERIC   5       0    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {retry_timer  fcglobalparams RetryTimer   NUMERIC   5       10    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {remote_retry_count  fcglobalparams RemoteDiscoveryRetryCount   NUMERIC   5       100    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {remote_retry_timer  fcglobalparams RemoteDiscoveryRetryTimer   NUMERIC   5       1000    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {reset_link    fcglobalparams  ResetPhysicalLinkOnLogout            {CHOICES true false}   4          false     _none_      TRUE    _none_            FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {use_interface  fchostconfig|fcfportconfig      UseFcIfWorldWidePortName   {CHOICES true false}    5     false   _none_     TRUE    _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {ed_tov  fcfportconfig  edtov   NUMERIC   5       2000    1-2000   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {ra_tov_port  fcfportconfig  ratov   NUMERIC   5       10000    1-10000   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {ra_tov_host  fchostconfig  ratov   NUMERIC   5       10000    1-10000   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {rxcredit_port  FcLeftSidePortParams RxCredit   NUMERIC   5        3    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {rxcredit_host  FcRightSidePortParams RxCredit   NUMERIC   5        3    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {domain_id  fcfportconfig Domainid   NUMERIC   5       16    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {domain_id_step  fcfportconfig DomainidStep   NUMERIC   5       1    1-255    TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {fc_topology            FcTestGenParams      _none_   {CHOICES VN_N_PORT_TO_VN_N_PORT N_PORT_TO_F_PORT VN_PORT_TO_VF_PORT}    1       _none_    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {host_per_port          _none_      _none_   NUMERIC   5       1    1-1000  TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {group_method           _none_      _none_   {CHOICES AGGREGATE aggregate HOST host} 5       aggregate    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {create_traffic         _none_      _none_   {CHOICES true false}     5   true          _none_    TRUE   _none_            FALSE         {create "" modify "" reset ""}       _none_    _none_}
      {traffic_flow           _none_      _none_   {CHOICES BIDIRECTIONAL bidirectional LEFT_TO_RIGHT left_to_right RIGHT_TO_LEFT right_to_left BACKBONE backbone}   5       bidirectional    _none_   TRUE        _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {traffic_flow_size      _none_      _none_   NUMERIC   5     2112  12-16383   TRUE    _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
      {traffic_percent_ports  _none_      _none_   NUMERIC   5     10.0   0-100     TRUE    _none_     FALSE      {create "" modify "" reset ""}       _none_    _none_}
   }
   
   {fc_control
      {hname      stcobj    stcattr     type                priority   default   range    supported   dependency mandatory  procfunc action  constants}
      {handle     _none_    _none_      ALPHANUM               1       _none_    _none_   TRUE        _none_     FALSE      _none_   _none_  _none_}
      {action     _none_    _none_      {CHOICES login logout delete start stop} 1       _none_    _none_   TRUE        _none_     TRUE       _none_   _none_  {login FcLogin logout Fclogout delete Fcdelete start FPortStart stop FPortStop}}
   }
   {fc_stats
      {hname       stcobj   stcattr    type                    priority    default  range   supported   dependency   mandatory  procfunc  mode    constants}
      {handle      _none_   _none_     ALPHANUM                    1       _none_    _none_    TRUE       _none_     TRUE       _none_    _none_  _none_}
      {mode        _none_   _none_     {CHOICES summary discovery nport fport fportneighbor all} 2       summary   _none_    TRUE       _none_     FALSE      _none_    _none_  _none_}     
   }
   {fc_stats_summary
      {hname           stcobj                stcattr        type      priority    default  ange     supported  dependency   mandatory  procfunc   mode   constants}
      {max_rx_size    FcSummaryResults    MaxRxSize         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {nport_down     FcSummaryResults    nPortDownCount    ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {nport_up       FcSummaryResults    nPortUpCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {rx_acc         FcSummaryResults    RxacceptCount     ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {rx_fdisc_acc   FcSummaryResults    RxFdiscAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_fdisc_rjt   FcSummaryResults    RxFdiscRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_acc   FcSummaryResults    RxFlogiAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_rjt   FcSummaryResults    RxFlogiRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_acc   FcSummaryResults    RxPlogiAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_rjt   FcSummaryResults    RxPlogiRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_rjt         FcSummaryResults    RxrejectCount     ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_flogi       FcSummaryResults    TxFlogiCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_fdisc       FcSummaryResults    TxfdiscCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_plogi       FcSummaryResults    TxPlogiCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_logo        FcSummaryResults    TxlogoCount       ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_scr        FcSummaryResults TxStateChangeRegisterCount   ANY  16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
   }
   {fc_stats_discovery
      {hname                stcobj                stcattr        type      priority    default  ange     supported  dependency   mandatory  procfunc   mode   constants}
      {rx_gid_pn_accept_count     FcRemoteDiscoveryResults    RxGidPnAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_gid_pn_reject_count     FcRemoteDiscoveryResults    RxGidPnRejectCount    ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {rx_remote_plogi_count     FcRemoteDiscoveryResults    RxRemotePlogiCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {rx_remote_prli_accept_count        FcRemoteDiscoveryResults    RxRemotePrliAcceptCount     ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {rx_remote_prli_count   FcRemoteDiscoveryResults    RxRemotePrliCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_remote_prli_reject_count   FcRemoteDiscoveryResults    RxRemotePrliRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_gid_pn_count   FcRemoteDiscoveryResults    TxGidPnCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_remote_plogi_accept_count   FcRemoteDiscoveryResults    TxRemotePlogiAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_remote_plogi_reject_count   FcRemoteDiscoveryResults    TxRemotePlogiRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_remote_prli_accept_count   FcRemoteDiscoveryResults    TxRemotePrliAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_remote_prli_count         FcRemoteDiscoveryResults    TxRemotePrliCount     ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {tx_remote_prli_reject_count       FcRemoteDiscoveryResults    TxRemotePrliRejectCount      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {world_wide_node_name       FcRemoteDiscoveryResults    WorldWideNodeName      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {world_wide_port_name       FcRemoteDiscoveryResults    WorldWidePortName      ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
   }
   {fc_stats_nport
      {hname          stcobj            stcattr           type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {substate       FcNPortResults    SubState          ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {fcid           FcNPortResults    FcId              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_rx_size    FcNPortResults    MaxRxSize         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {wwpn           FcNPortResults    WorldWidePortName ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {wwnn           FcNPortResults    WorldWideNodeName ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_acc         FcNPortResults    RxacceptCount     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_fdisc_acc   FcNPortResults    RxFdiscAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_fdisc_rjt   FcNPortResults    RxFdiscRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_acc   FcNPortResults    RxFlogiAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_rjt   FcNPortResults    RxFlogiRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_acc   FcNPortResults    RxPlogiAcceptCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_rjt   FcNPortResults    RxPlogiRejectCount         ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_rjt         FcNPortResults    RxrejectCount     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_flogi       FcNPortResults    TxFlogiCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_fdisc       FcNPortResults    TxfdiscCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_plogi       FcNPortResults    TxPlogiCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_logo        FcNPortResults    TxlogoCount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_scr        FcNPortResults TxStateChangeRegisterCount ANY 16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   
   }
   {fc_stats_fport
      {hname                 stcobj            stcattr           type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {neighbor_count       FcFPortResults    NeighborCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_fdisc_count       FcFPortResults    RxFDISCCount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_count       FcFPortResults    RxFLOGICount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_logo_count        FcFPortResults    RxLOGOCount        ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_count       FcFPortResults    RxPLOGICount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_fdisc_count       FcFPortResults    TxFDISCAcceptCount     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_flogi_count       FcFPortResults    TxFLOGIAcceptCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_logo_count        FcFPortResults    TxLOGOCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_plogi_count       FcFPortResults    TxPLOGIAcceptCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ } 
   }
   {fc_stats_fportneighbor
      {hname                 stcobj            stcattr           type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {fcid                 FcFPortNeighborResults     FcId      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_fdisc_count       FcFPortNeighborResults    RxFDISCCount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_flogi_count       FcFPortNeighborResults    RxFLOGICount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_logo_count        FcFPortNeighborResults    RxLOGOCount        ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_plogi_count       FcFPortNeighborResults    RxPLOGICount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {sub_state            FcFPortNeighborResults    SubState          ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_fdisc_count       FcFPortNeighborResults    TxFDISCAcceptCount     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_flogi_count       FcFPortNeighborResults    TxFLOGIAcceptCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_logo_count        FcFPortNeighborResults    TxLOGOCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_plogi_count       FcFPortNeighborResults    TxPLOGIAcceptCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {wwnn             FcFPortNeighborResults    WorldWideNodeName     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {wwpn             FcFPortNeighborResults    WorldWidePortName     ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   }
}