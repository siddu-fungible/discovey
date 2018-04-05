# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::igmp {
   set igmpTable {
      ::sth::igmp::
      {emulation_igmp_info
         {hname                           stcobj                  stcattr                          type            priority         default            range            supported      dependency        mandatory         procfunc            mode            constants         }
         {handle                          _none_                  _none_                           ALPHANUM            0            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {port_handle                     _none_                  _none_                           ALPHANUM            0            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {mode                            _none_                  _none_               {CHOICES stats clear_stats}     0            stats            _none_             true            _none_            false            _none_            _none_            _none_         }
         {invalid_pkts                 IgmpPortResults {RxIgmpCheckSumErrorCount RxIgmpLengthErrorCount RxUnknownTypeCount} NUMERIC  100    _none_    _none_            true            _none_            false            _none_            _none_            _none_         }
         {dropped_pkts                    _none_                  _none_                           NUMERIC            100            _none_            0                false            _none_            false            _none_            _none_            _none_         }
         {igmpv1_queries_rx            IgmpPortResults            RxV1QueryCount                   NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv1_group_queries_rx      IgmpPortResults            RxGroupSpecificQueryCount        NUMERIC            100            _none_            _none_            false            _none_            false            _none_            _none_            _none_         }
         {igmpv1_mem_reports_tx        IgmpPortResults            TxV1ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv1_mem_reports_rx        IgmpPortResults            RxV1ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv2_queries_rx            IgmpPortResults            RxV2QueryCount                   NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv2_group_queries_rx      IgmpPortResults            RxGroupSpecificQueryCount        NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv2_mem_reports_tx        IgmpPortResults            TxV2ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv2_mem_reports_rx        IgmpPortResults            RxV2ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv2_leave_tx              IgmpPortResults            TxLeaveGroupCount                NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv3_queries_rx            IgmpPortResults            RxV3QueryCount                   NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv3_group_queries_rx      IgmpPortResults            RxGroupSpecificQueryCount        NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv3_group_src_queries_rx  IgmpPortResults            TxGroupSpecificQueryCount        NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv3_mem_reports_tx        IgmpPortResults            TxV3ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmpv3_mem_reports_rx        IgmpPortResults            RxV3ReportCount                  NUMERIC            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
      }
      {emulation_igmp_config
         {hname                           stcobj               stcattr                    type                 priority          default            range            supported      dependency        mandatory         procfunc            mode            constants         }
         {count                           EmulatedDevice|Host  DeviceCount                NUMERIC                 100            1                 1-65535           true            _none_            false            _none_            _none_            _none_         }
         {pppox_handle                    _none_               _none_                     ALPHANUM                100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {filter_mode                     IgmpGroupMembership  FilterMode        {CHOICES include exclude}        100            include           _none_            true            _none_            false            _none_            _none_            {include include exclude exclude}         }
         {filter_ip_addr                  Ipv4NetworkBlock     StartIpList                IPV4                    100            192.0.1.0         _none_            true            _none_            false            _none_            _none_            _none_         }
         {general_query                   _none_               _none_                     {CHOICES 1 true}        100            1                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {group_query                     _none_               _none_                     {CHOICES 1 true}        100            1                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {handle                          _none_               _none_                     ALPHANUM                100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {igmp_version                    IgmpHostConfig       Version                    {CHOICES v1 v2 v3}      100            v2                _none_            true            _none_            false            _none_            _none_            {v1 igmp_v1 v2 igmp_v2 v3 igmp_v3}         }
         {force_single_join               IgmpHostConfig       ForceSimpleJoin            {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {force_robust_join               IgmpHostConfig       ForceRobustJoin            {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {force_leave                     IgmpHostConfig       ForceLeave                 {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {insert_checksum_errors          IgmpHostConfig       InsertCheckSumErrors       {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {insert_length_errors            IgmpHostConfig       InsertLengthErrors         {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {enable_df                       IgmpHostConfig       IpV4DontFragment           {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {tos                             IgmpHostConfig       IpV4Tos                    NUMERIC                 100            192               0-255             true            _none_            false            _none_            _none_            _none_         }
         {pack_reports                    IgmpHostConfig       PackReports                {CHOICES true false}    100            false             _none_            true            _none_            false            _none_            _none_            _none_         }
         {enable_router_alert             IgmpHostConfig       RouterAlert                {CHOICES true false}    100            true              _none_            true            _none_            false            _none_            _none_            _none_         }
         {tos_type                        IgmpHostConfig       TosType                    {CHOICES tos diffserv}  100            tos               _none_            true            _none_            false            _none_            _none_            _none_         }
         {intf_ip_addr                    Ipv4If               Address                    IPV4                    100            192.85.1.3        _none_            true            _none_            false            _none_            _none_            _none_         }
         {intf_ip_addr_step               Ipv4If               AddrStep                   IPV4                    100            0.0.0.1           _none_            true            _none_            false            _none_            _none_            _none_         }
         {intf_prefix_len                 Ipv4If               PrefixLength               NUMERIC                 100            24                1-32              true            _none_            false            _none_            _none_            _none_         }
         {source_mac                      EthiiIf              SourceMac                  MAC                     100            00:10:94:00:00:02 _none_            true            _none_            false            _none_            _none_            _none_         }
         {source_mac_step                 EthiiIf              SrcMacStep                 MAC                     100            00:00:00:00:00:01 _none_            true            _none_            false            _none_            _none_            _none_         }
         {ip_router_alert                 _none_               _none_                     {CHOICES 1 true}        100            1                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {max_groups_per_pkts             _none_               _none_                     NUMERIC                 100            _none_            _none_            true            igmp_version      false            _none_            _none_            _none_         }
         {max_response_control            _none_               _none_                     {CHOICES 0 false}       100            0                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {max_response_time               _none_               _none_                     NUMERIC                 100            0              0-4294967295         false        max_response_control false            _none_            _none_            _none_         }
         {mode                            _none_               _none_ {CHOICES create modify delete disable_all}  100            _none_            _none_            true            _none_            true             _none_            _none_            _none_         }
         {msg_interval                    IgmpPortConfig       RatePps                    NUMERIC                 100            0            0-4294967295           true            none              false            _none_            _none_            _none_         }
         {neighbor_intf_ip_addr           Ipv4If               Gateway                    IPV4                    100            "192.85.1.1"      _none_            true            _none_            false            _none_            _none_            _none_         }
         {neighbor_intf_ip_addr_step      Ipv4If               GatewayStep                IP                      100            0.0.0.0            _none_           true            _none_            false            _none_            _none_            _none_         }
         {older_version_timeout           IgmpHostConfig       V1RouterPresentTimeout     NUMERIC                 100            4000            0-4294967295        true            _none_            false            _none_            _none_            _none_         }
         {port_handle                     _none_               _none_                     ALPHANUM                100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {robustness                      IgmpHostConfig       RobustnessVariable         NUMERIC                 100            2                 2-255             true            igmp_version      false            _none_            _none_            _none_         }
         {suppress_report                 _none_               _none_                     {CHOICES true 1}        100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {unsolicited_report_interval     IgmpHostConfig       UnsolicitedReportInterval  NUMERIC                 100            _none_         0-4294967295         true            igmp_version      false            _none_            _none_            _none_         }
         {vlan_cfi                        VlanIf               cfi                        {CHOICES 0 1}           100            0                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {vlan_id                         VlanIf               VlanId                     NUMERIC                 100            100               0-4095            true            _none_            false            _none_            _none_            _none_         }
         {vlan_id_mode                    VlanIf               _none_            {CHOICES fixed increment}        100            fixed            _none_             true            _none_            false            _none_            _none_            {fixed fixed increment increment}         }
         {vlan_id_step                    VlanIf               IdStep                     NUMERIC                 100            1                 0-32767           true            _none_            false            _none_            _none_            _none_         }
         {vlan_id_count                   VlanIf               IfRecycleCount             NUMERIC                 100            1                 1-4095            true            _none_            false            _none_            _none_            _none_        }
         {vlan_user_priority              VlanIf               Priority                   NUMERIC                 100            7                 0-7               true            _none_            false            _none_            _none_            _none_         }
         {vlan_outer_cfi                  VlanIf_Outer         cfi                        {CHOICES 0 1}           100            0                 _none_            true            _none_            false            _none_            _none_            _none_         }
         {vlan_id_outer                   VlanIf_Outer         VlanId                     NUMERIC                 100            100               0-4095            true            _none_            false            _none_            _none_            _none_         }
         {vlan_id_outer_mode              VlanIf_Outer         _none_            {CHOICES fixed increment}        100            fixed            _none_             true            _none_            false            _none_            _none_            {fixed fixed increment increment}         }
         {vlan_id_outer_step              VlanIf_Outer         IdStep                     NUMERIC                 100            1                 0-32767           true            _none_            false            _none_            _none_            _none_         }
         {vlan_id_outer_count             VlanIf_Outer         IfRecycleCount             NUMERIC                 100            1                 1-4095            true            _none_            false            _none_            _none_            _none_         }
         {qinq_incr_mode                  _none_               _none_            {CHOICES inner outer both}       100            inner             _none_            true            _none_            false            _none_            _none_            {inner inner outer outer both both}         }
         {vlan_outer_user_priority        VlanIf_Outer         Priority                   NUMERIC                 100            7                 0-7               true            _none_            false            _none_            _none_            _none_         }
         {calculate_latency               _none_               _none_            {CHOICES true false}             100            _none_           _none_             true            _none_            false            _none_            _none_            _none_         }
      }
      {emulation_igmp_control
         {hname                  stcobj            stcattr            type                         priority       default            range            supported      dependency        mandatory         procfunc            mode            constants         }
         {group_member_handle    _none_            _none_            ALPHANUM                         0           _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {handle                 _none_            _none_            ALPHANUM                         0           _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {mode                   _none_            _none_            {CHOICES join restart leave}     100         _none_            _none_            true            _none_            true             _none_            _none_            _none_         }
         {port_handle            _none_            _none_            ALPHANUM                         100         _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {data_duration          _none_            _none_            NUMERIC                          100            10             0-4294967295      true            _none_            false            _none_            _none_            _none_         }
         {leave_join_delay       _none_            _none_            NUMERIC                          100            0              0-4294967295      true            _none_            false            _none_            _none_            _none_         }
         {calculate_latency      _none_            _none_            {CHOICES 1 true 0 false}         100            0              _none_            true            _none_            false            _none_            _none_            _none_         }
      }
      {emulation_igmp_group_config
         {hname                  stcobj            stcattr            type                            priority          default            range            supported      dependency        mandatory         procfunc            mode            constants}
         {group_pool_handle      _none_            _none_            ALPHANUM                            0              _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {handle                 _none_            _none_            ALPHANUM                            0              _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {mode                   _none_            _none_   {CHOICES create modify delete clear_all}     100            _none_            _none_            true            _none_            true             _none_            _none_            _none_         }
         {session_handle         _none_            _none_            ALPHANUM                            100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {source_pool_handle     _none_            _none_            ANY                                 100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {device_group_mapping   _none_            _none_            ANY                                 100            _none_            _none_            true            _none_            false            _none_            _none_            _none_         }
         {filter_mode       IgmpGroupMembership  FilterMode        {CHOICES include exclude INCLUDE EXCLUDE }             100            _none_           _none_            true            _none_            false            _none_            _none_            {include include exclude exclude}         }
         {ip_addr_list      Ipv4NetworkBlock     StartIpList        IPV4                                  100            _none_         _none_            true            _none_            false            _none_            _none_            _none_         }
         {enable_user_defined_sources  IgmpGroupMembership   userDefinedSources  {CHOICES 0 1}            100            _none_         _none_            true            _none_            false            _none_            _none_            _none_         }
         {specify_sources_as_list      IgmpGroupMembership   userDefinedSources  {CHOICES 0 1}            100            _none_         _none_            true            _none_            false            _none_            _none_            _none_         }
         {source_filters     _none_            _none_            ALPHANUM                                  0              _none_        _none_            true            _none_            false            _none_            _none_            _none_         }
      }
   }
}
