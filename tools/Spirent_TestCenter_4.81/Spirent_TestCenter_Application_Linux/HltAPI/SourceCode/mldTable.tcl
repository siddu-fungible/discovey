# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::Mld:: {
}

set ::Mld::mldTable {
   ::Mld::
   {emulation_mld_config
      {hname                           stcobj                  stcattr                                 type                                            priority        default                 range           supported       dependency                      mandatory       procfunc                mode                                                    constants}
      {port_handle                     _none_                  _none_                                  ALPHANUM                                        1               _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {handle                          _none_                  _none_                                  ALPHANUM                                        2               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {mode                            _none_                  _none_                                  {CHOICES create modify delete enable_all}       3               _none_                  _none_          TRUE            _none_                          TRUE            <procName>              _none_                                                  _none_}
      {count                           EmulatedDevice          count                             NUMERIC                                         10              1                       0-65535         TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {filter_mode                     mldGroupMembership      FilterMode                              {CHOICES include exclude}                       11              include                 _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {include include exclude exclude}}
      {filter_ip_addr        Ipv6NetworkBlock      StartIpList                                 IPV6                                                                           11             2008::8                 _none_         TRUE           _none_                           FALSE           <procName>              _none_                                                  _none_}
      {general_query                   _none_                  _none_                                  {CHOICES 1 TRUE}                                12              TRUE                    _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {0 FALSE 1 TRUE TRUE TRUE FALSE FALSE}}
      {group_query                     _none_                  _none_                                  {CHOICES 1 TRUE}                                13              TRUE                    _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {0 FALSE 1 TRUE TRUE TRUE FALSE FALSE}}
      {intf_ip_addr                    Ipv6If                  Address                                 IPV6                                            14              2000::2                _none_          TRUE            _none_                           FALSE           <procName>              _none_                                                  _none_}
      {intf_ip_addr_step               Ipv6If                  AddrStep                                IPV6                                            15              ::1                     _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {intf_prefix_len                 Ipv6If                  PrefixLength                            NUMERIC                                         16              64                      1-128           TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {ip_router_alert                 _none_                  _none_                                  {CHOICES 1 TRUE}                                17              TRUE                    _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {0 FALSE 1 TRUE TRUE TRUE FALSE FALSE}}
      {max_groups_per_pkts             _none_                  _none_                                  NUMERIC                                         18              1                       1-1             TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {max_response_control            _none_                  _none_                                  {CHOICES 0 FALSE}                               19              0                       0-0             TRUE            _none_                          FALSE           <procName>              _none_                                                  {0 FALSE 1 TRUE TRUE TRUE FALSE FALSE}}
      {mld_version                     MldHostConfig           Version                                 {CHOICES v1 v2}                                 21              v1                      _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {v1 mld_v1 v2 mld_v2}}
      {msg_interval                    MldPortConfig           RatePps                                 NUMERIC                                         22              0                       0-4294967295    TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {neighbor_intf_ip_addr           Ipv6If                  Gateway                                 IPV6                                            23              2000::1                 _none_          TRUE            _none_                          FALSE            <procName>              _none_                                                  _none_}
      {neighbor_intf_ip_addr_step      Ipv6If                  GatewayStep                                  IPV6                                            24              ::0                     _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {robustness                      MldHostConfig           robustnessVariable                      NUMERIC                                         25              2                       2-255           TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {suppress_report                 _none_                  _none_                                  {CHOICES 1 TRUE}                                26              1                       _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {unsolicited_report_interval     MldHostConfig           UnsolicitedReportInterval               NUMERIC                                         27              _none_                  0-4294967295    TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_cfi                        VlanIf                  Cfi                                     {CHOICES 1 TRUE 0 FALSE}                        28              0                       _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_id                         VlanIf                  VlanId                                  NUMERIC                                         29              1                       0-4095          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_id_step                    VlanIf                  IdStep                                  NUMERIC                                         30              1                       0-4094          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {vlan_id_mode                    _none_                  _none_                                  {CHOICES fixed increment}                       31              fixed                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {fixed fixed increment increment}}
      {vlan_id_count                   VlanIf                  IfRecycleCount                                  NUMERIC                                         32              1                       1-4095          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {vlan_user_priority              VlanIf                  Priority                                NUMERIC                                         32              0                       0-7             TRUE            _none_                          FALSE           doGenericConfig         _none_                                                  _none_}
      {use_partial_block_state         MldHostConfig           UsePartialBlockState                    {CHOICES 1 TRUE 0 FALSE}                        33              FALSE                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {force_leave                     MldHostConfig           ForceLeave                              {CHOICES 1 TRUE 0 FALSE}                        34              FALSE                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {force_robust_join               MldHostConfig           ForceRobustJoin                         {CHOICES 1 TRUE 0 FALSE}                        35              FALSE                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {insert_checksum_errors          MldHostConfig           InsertCheckSumErrors                    {CHOICES 1 TRUE 0 FALSE}                        36              FALSE                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {insert_length_errors            MldHostConfig           InsertLengthErrors                      {CHOICES 1 TRUE 0 FALSE}                        37              FALSE                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {link_local_intf_ip_addr         Ipv6If                  Address                                 IPV6                                            14              FE80::0                 _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {link_local_intf_ip_addr_step    Ipv6If                  AddrStep                                IPV6                                            15              ::1                     _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {link_local_intf_prefix_len      Ipv6If                  PrefixLength                            NUMERIC                                         16              128                      1-128           TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_outer_cfi                  VlanIf_Outer                  Cfi                                     {CHOICES 1 TRUE 0 FALSE}                        28              0                       0-0xFFFFFFFF    TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_id_outer                   VlanIf_Outer                  VlanId                                  NUMERIC                                         29              1                       0-4095          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {vlan_id_outer_step              VlanIf_Outer                  IdStep                                  NUMERIC                                         30              1                       0-4094          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {vlan_id_outer_mode              _none_                  _none_                                  {CHOICES fixed increment}                       31              fixed                   _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  {fixed fixed increment increment}}
      {vlan_id_outer_count             VlanIf_Outer                  IfRecycleCount                                  NUMERIC                                         32              1                       1-4095          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {qinq_incr_mode                  _none_                  _none_                                  {CHOICES inner outer both}                     33              inner                   _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  {inner inner outer outer both both}}
      {vlan_outer_user_priority        VlanIf_Outer                  Priority                                NUMERIC                                         34              0                       0-7             TRUE            _none_                          FALSE           doGenericConfig         _none_                                                  _none_}
   }
   {emulation_mld_group_config
      {hname                           stcobj                  stcattr                                 type                                            priority        default                 range           supported       dependency                      mandatory       procfunc                mode                                                    constants}
      {handle                          _none_                  _none_                                  ALPHANUM                                        2               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {group_pool_handle               _none_                  _none_                                  ALPHANUM                                        3               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {mode                            _none_                  _none_                                  {CHOICES create modify delete clear_all}        6               _none_                  _none_          TRUE            _none_                          TRUE            <procName>              _none_                                                  _none_}
      {session_handle                  _none_                  _none_                                  ALPHANUM                                        4               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {source_pool_handle              _none_                  _none_                                  ANY                                             5               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {host_handle                     _none_                  _none_                                  ALPHANUM                                        2               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {user_defined_src        MldGroupMembership    UserDefinedSources                              {CHOICES true false}                              34               true                   _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {device_group_mapping              _none_                  _none_                              {CHOICES many_to_many one_to_one round_robin}     34             many_to_many             _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
   }
   {emulation_mld_control
      {hname                           stcobj                  stcattr                                 type                                            priority        default                 range           supported       dependency                      mandatory       procfunc                mode                                                    constants}
      {handle                          _none_                  _none_                                  ALPHANUM                                        2               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {group_member_handle             _none_                  _none_                                  ALPHANUM                                        5               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {port_handle                     _none_                  _none_                                  ALPHANUM                                        5               _none_                  _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {mode                            _none_                  _none_                                  {CHOICES join leave leave_join}                            6               _none_                  _none_          TRUE            _none_                          TRUE            <procName>              _none_                                                  _none_}
      {delay                           _none_                  _none_                                  NUMERIC                                         5               0                       _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {data_duration                   _none_                  _none_                                  NUMERIC                                         5               10                      _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {calculate_latency               _none_                  _none_                                  {CHOICES 1 true 0 false}                        5               0                       _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
   }
   {emulation_mld_info
      {hname                           stcobj                  stcattr                        	       type                                            priority        default         	       range           supported       dependency                      mandatory       procfunc                mode                                                    constants}
      {handle                          _none_                  none_                                   ALPHANUM                                        2               _none_          	       _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {port_handle                     _none_                  none_                          	       ALPHANUM                                        2               _none_          	       _none_          TRUE            _none_                          FALSE           _none_                  _none_                                                  _none_}
      {invalid_pkts                    MldPortResults          {RxMldCheckSumErrorCount RxMldLengthErrorCount RxUnknownTypeCount}                    ANY                                             10              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {dropped_pkts                    _none_                  _none_                                  ANY                                             11              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_queries_rx                MldPortResults          RxV1QueryCount                          ANY                                             12              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_group_queries_rx          MldPortResults          RxGroupSpecificQueryCount               ANY                                             13              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_queries_tx                MldPortResults          TxV1QueryCount                          ANY                                             14              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_mem_reports_tx            MldPortResults          TxV1ReportCount                         ANY                                             15              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_mem_reports_rx            MldPortResults          RxV1ReportCount                         ANY                                             16              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv1_leave_tx                  MldPortResults          TxStopListenGroupCount                  ANY                                             17              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_queries_rx                MldPortResults          RxV2QueryCount                          ANY                                             18              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_group_queries_tx          MldPortResults          TxV2QueryCount                          ANY                                             19              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_group_src_queries_rx      MldPortResults          RxGroupSpecificQueryCount               ANY                                             20              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_mem_reports_tx            MldPortResults          TxV2ReportCount                         ANY                                             21              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_mem_reports_rx            MldPortResults          RxV2ReportCount                         ANY                                             22              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_frames_rx                   MldPortResults          RxFrameCount                            ANY                                             23              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_general_queries_rx          MldPortResults          RxGeneralQueryCount                     ANY                                             24              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_group_src_queries_rx        MldPortResults          RxGroupAndSourceSpecificQueryCount      ANY                                             25              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_group_queries_rx            MldPortResults          RxGroupSpecificQueryCount               ANY                                             26              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_checksum_errors_rx          MldPortResults          RxMldCheckSumErrorCount                   ANY                                             27              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_length_errors_rx            MldPortResults          RxMldLengthErrorCount                   ANY                                             28              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_unknown_rx                  MldPortResults          RxUnknownTypeCount                      ANY                                             29              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_timestamp                   MldPortResults          Timestamp                               ANY                                             30              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_frames_tx                   MldPortResults          TxFrameCount                            ANY                                             31              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_general_queries_tx          MldPortResults          TxGeneralQueryCount                     ANY                                             32              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_group_src_queries_tx        MldPortResults          TxGroupAndSourceSpecificQueryCount      ANY                                             33              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mld_group_queries_tx            MldPortResults          TxGroupSpecificQueryCount               ANY                                             34              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_allow_new_src_tx          MldPortResults          TxV2AllowNewSourcesCount                ANY                                             35              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_block_old_src_tx          MldPortResults          TxV2BlockOldSourcesCount                ANY                                             36              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_filter_exclude_tx         MldPortResults          TxV2ChangeToExcludeModeCount            ANY                                             37              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_filter_include_tx         MldPortResults          TxV2ChangeToIncludeModeCount            ANY                                             38              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_exclude_tx                MldPortResults          TxV2ModeIsExcludeCount                  ANY                                             39              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
      {mldv2_include_tx                MldPortResults          TxV2ModeIsIncludeCount                  ANY                                             40              _none_                  _none_          TRUE            _none_                          FALSE           <procName>              _none_                                                  _none_}
   }
}
