
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dot1x:: {
}


set ::sth::Dot1x::Dot1xTable {
   ::sth::Dot1x::
   {emulation_dot1x_config
      {hname                        stcobj                        stcattr                       type                                               priority        default           range        supported   dependency                  mandatory      procfunc                         mode                                                          constants}
      {port_handle                  _none_                        _none_                        ALPHANUM                                              1              _none_         _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {handle                       _none_                        _none_                        ALPHANUM                                              1              _none_         _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {mode                         _none_                        _none_                        {CHOICES create modify delete}                        2              _none_         _none_         TRUE         _none_                        TRUE           _none_                         _none_                                                             _none_}
      {num_sessions                 Emulateddevice|Host         DeviceCount                   NUMERIC                                               3              1              _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {name                         Emulateddevice|Host         Name                          ALPHANUM                                              3              _none_         _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {ip_version                   _none_                        _none_                        {CHOICES ipv4 ipv6 ipv4_6 none}                              3              ipv4           _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {encapsulation                _none_                        _none_                  {CHOICES ethernet_ii ethernet_ii_vlan ethernet_ii_qinq}     3              ethernet_ii    _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {mac_addr                     EthIIIf                       SourceMac                     ANY                                                   4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configEthIIIntf modify configEthIIIntf}                    _none_}
      {mac_addr_step                EthIIIf                       SrcMacStep                    ANY                                                   4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configEthIIIntf modify configEthIIIntf}                    _none_}
      {local_ip_addr                Ipv4If                        Address                       IPV4                                                  4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv4Intf modify configIpv4Intf}                          _none_}
      {local_ip_addr_step           Ipv4If                        AddrStep                      IPV4                                                  4              0.0.0.1        _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv4Intf modify configIpv4Intf}                          _none_}
      {local_ip_prefix_len          Ipv4If                        PrefixLength                  NUMERIC                                               4              24             0-32           TRUE         _none_                        FALSE          _none_                         {create configIpv4Intf modify configIpv4Intf}                          _none_}
      {local_ipv6_addr              Ipv6If                        Address                       IPV6                                                  4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv6Intf modify configIpv6Intf}                          _none_}
      {local_ipv6_addr_step         Ipv6If                        AddrStep                      IPV6                                                  4              ::1            _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv6Intf modify configIpv6Intf}                          _none_}
      {local_ipv6_prefix_len        Ipv6If                        PrefixLength                  NUMERIC                                               4              64             0-128          TRUE         _none_                        FALSE          _none_                         {create configIpv6Intf modify configIpv6Intf}                          _none_}
      {gateway_ip_addr              Ipv4If                        Gateway                       IPV4                                                  4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv4Intf modify configIpv4Intf}                          _none_}
      {gateway_ip_addr_step         Ipv4If                        GatewayStep                   IPV4                                                  4              0.0.0.0        _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv4Intf modify configIpv4Intf}                          _none_}
      {gateway_ipv6_addr            Ipv6If                        Gateway                       IPV6                                                  4              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv6Intf modify configIpv6Intf}                          _none_}
      {gateway_ipv6_addr_step       Ipv6If                        GatewayStep                   IPV6                                                  4              ::             _none_         TRUE         _none_                        FALSE          _none_                         {create configIpv6Intf modify configIpv6Intf}                          _none_}
      {qinq_incr_mode               _none_                        _none_                        {CHOICES inner outer both}                            4              _none_         _none_         TRUE         _none_                        FALSE          processConfigCmd_qinqIncrMode  {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {vlan_id                      VlanIf                        VlanId                        NUMERIC                                               5              100            0-4095         TRUE         _none_                        FALSE          processConfigCmd_vlanId        {create configVlanIfInner modify configVlanIfInner}                _none_}
      {vlan_id_step                 VlanIf                        IdStep                        NUMERIC                                               5              1              0-4095         TRUE         _none_                        FALSE          _none_                         {create configVlanIfInner modify configVlanIfInner}                _none_}
      {vlan_id_count                VlanIf                        IfRecycleCount                NUMERIC                                               5              1              1-4096         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {vlan_user_priority           VlanIf                        Priority                      NUMERIC                                               5              0              0-7            TRUE         _none_                        FALSE          _none_                         {create configVlanIfInner modify configVlanIfInner}                _none_}
      {vlan_ether_type              VlanIf                        Tpid                          NUMERIC                                               5             33024           0-65535        TRUE         _none_                        FALSE          _none_                         {create configVlanIfInner modify configVlanIfInner}                _none_}
      {vlan_cfi                     VlanIf                        Cfi                           {CHOICES 0 1}                                         5              1              _none_         TRUE         _none_                        FALSE          _none_                         {create configVlanIfInner modify configVlanIfInner}                _none_}  
      {vlan_outer_id                VlanIf_Outer                  VlanId                        NUMERIC                                               5              100            0-4095         TRUE         _none_                        FALSE          processConfigCmd_vlanId        {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {vlan_outer_id_step           VlanIf_Outer                  IdStep                        NUMERIC                                               5              1              0-4095         TRUE         _none_                        FALSE          _none_                         {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {vlan_outer_id_count          VlanIf_Outer                  IfRecycleCount                NUMERIC                                               5              1              1-4096         TRUE         _none_                        FALSE          _none_                         _none_                                                             _none_}
      {vlan_outer_user_priority     VlanIf_Outer                  Priority                      NUMERIC                                               5              0              0-7            TRUE         _none_                        FALSE          _none_                         {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {vlan_outer_ether_type        VlanIf_Outer                  Tpid                          NUMERIC                                               5             33024           0-65535        TRUE         _none_                        FALSE          _none_                         {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {vlan_outer_cfi               VlanIf_Outer                  Cfi                           {CHOICES 0 1}                                         5              1              _none_         TRUE         _none_                        FALSE          _none_                         {create configVlanIfOuter modify configVlanIfOuter}                _none_}
      {supplicant_auth_rate         Dot1xPortConfig               SupplicantAuthRate            NUMERIC                                               6              100            1-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xPortConfig modify configDot1xPortConfig}                 _none_}
      {supplicant_logoff_rate       Dot1xPortConfig               SupplicantLogoffRate          NUMERIC                                               6              100            1-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xPortConfig modify configDot1xPortConfig}                 _none_}
      {max_authentications          Dot1xPortConfig               MaxOutstandingSupplicantAuth  NUMERIC                                               6              100            1-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xPortConfig modify configDot1xPortConfig}                 _none_}
      {eap_auth_method              Dot1xSupplicantBlockConfig    EapAuthMethod                 {CHOICES md5 fast tls}                                7              md5            _none_         TRUE         _none_                        FALSE          processConfigCmd_auth          {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {retransmit_count             Dot1xSupplicantBlockConfig    RetransmitCount               NUMERIC                                               7              10             0-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {retransmit_interval          Dot1xSupplicantBlockConfig    RetransmitIntervaInMsec       NUMERIC                                               7              1000           0-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {auth_retry_count             Dot1xSupplicantBlockConfig    AuthRetryCount                NUMERIC                                               7              10             0-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {auth_retry_interval          Dot1xSupplicantBlockConfig    AuthRetryIntervalInMsec       NUMERIC                                               7              1000           0-4294967295   TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {authenticator_mac            Dot1xSupplicantBlockConfig    AuthenticatorMac              ANY                                                   7              _none_         _none_         TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {use_pae_group_mac            Dot1xSupplicantBlockConfig    UsePaeGroupMac                {CHOICES 0 1}                                         7              1              _none_         TRUE         _none_                        FALSE          _none_                         {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {username                     Dot1xEapMd5Config             UserId                        REGEXP                                                7              spirent        _none_         TRUE         _none_                        FALSE         processConfigCmd_auth           {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {password                     Dot1xEapMd5Config             Password                      REGEXP                                                7              spirent        _none_         TRUE         _none_                        FALSE         processConfigCmd_auth           {create configDot1xSupplicantConfig modify configDot1xSupplicantConfig}     _none_}
      {pac_key_file                 Dot1xEapFastConfig            PacKeyFileName                REGEXP                                                7              _none_         _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {certificate                  Dot1xEapTlsConfig             Certificate                   REGEXP                                                7              _none_         _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {username_wildcard            _none_                        _none_                        {CHOICES 0 1}                                         7              0              _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {password_wildcard            _none_                        _none_                        {CHOICES 0 1}                                         7              0              _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {pac_key_file_wildcard        _none_                        _none_                        {CHOICES 0 1}                                         7              0              _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {certificate_wildcard         _none_                        _none_                        {CHOICES 0 1}                                         7              0              _none_         TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_pound_start         _none_                        _none_                        NUMERIC                                               7              1              0-65535        TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_pound_end           _none_                        _none_                        NUMERIC                                               7              1              0-65535        TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_pound_fill          _none_                        _none_                        NUMERIC                                               7              0              0-9            TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_question_start      _none_                        _none_                        NUMERIC                                               7              1              0-65535        TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_question_end        _none_                        _none_                        NUMERIC                                               7              1              0-65535        TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
      {wildcard_question_fill       _none_                        _none_                        NUMERIC                                               7              0              0-9            TRUE         _none_                        FALSE          _none_                         _none_                                                                      _none_}
   }
   {emulation_dot1x_control
      {hname                        stcobj                        stcattr                type                                   priority        default         range       supported   dependency           mandatory      procfunc               mode           constants}
      {port_handle                  _none_                        _none_                 ALPHANUM                                  1             _none_          _none_       TRUE        _none_                FALSE          _none_              _none_            _none_}
      {handle                       _none_                        _none_                 ALPHANUM                                  2             _none_          _none_       TRUE        _none_                FALSE          _none_              _none_            _none_}
      {mode                         _none_                        _none_                 {CHOICES start stop logout abort}        3             _none_          _none_       TRUE        _none_                FALSE          _none_              _none_            _none_}
      {action                       _none_                        _none_                 {CHOICES download delete_all}             4             _none_          _none_       TRUE        _none_                FALSE          _none_              _none_            _none_}
      {certificate_dir              _none_                        _none_                 REGEXP                                    5             _none_          _none_       TRUE        _none_                FALSE          _none_              _none_            _none_}
   }
   {emulation_dot1x_stats
      {hname                            stcobj                          stcattr                          type                      priority          default          range        supported  dependency            mandatory      procfunc           mode                     constants}
      {handle                           _none_                          _none_                           ALPHANUM                       1             _none_          _none_        TRUE       _none_                 FALSE         _none_             _none_                     _none_}
      {port_handle                      _none_                          _none_                           ALPHANUM                       2             _none_          _none_        TRUE       _none_                 FALSE         _none_             _none_                     _none_}
      {mode                             _none_                          _none_                           {CHOICES aggregate session}    3             session         _none_        TRUE       _none_                 FALSE         _none_             _none_                     _none_}
      {authentication_state             Dot1xSupplicantBlockConfig      AuthState                        NUMERIC                        4             _none_          _none_        TRUE       _none_                 FALSE         _none_             _none_                     _none_}
      {attempt_auth_count               Dot1xSupplicantAuthResults      AuthAttemptCount                 NUMERIC                        5             _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {success_auth_count               Dot1xSupplicantAuthResults      AuthSuccessCount                 NUMERIC                        6             _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {failed_auth_count                Dot1xSupplicantAuthResults      AuthFailCount                    NUMERIC                        7             _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {aborted_auth_count               Dot1xSupplicantAuthResults      AuthAbortCount                   NUMERIC                        8             _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {attempt_re_auth_count            Dot1xSupplicantAuthResults      ReAuthAttemptCount               NUMERIC                        9             _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {success_re_auth_count            Dot1xSupplicantAuthResults      ReAuthSuccessCount               NUMERIC                        10            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {failed_re_auth_count             Dot1xSupplicantAuthResults      ReAuthFailCount                  NUMERIC                        11            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {logoff_attempts                  Dot1xSupplicantAuthResults      LogoffAttemptCount               NUMERIC                        12            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {failed_logoff_attempts           Dot1xSupplicantAuthResults      LogoffFailCount                  NUMERIC                        13            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {success_logoff_attempts          Dot1xSupplicantAuthResults      LogoffSuccessCount               NUMERIC                        14            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {avg_auth_success_duration        Dot1xSupplicantAuthResults      AvgAuthSuccessDurationInMsec     NUMERIC                        15            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {max_auth_success_duration        Dot1xSupplicantAuthResults      MaxAuthSuccessDurationInMsec     NUMERIC                        16            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {min_auth_success_duration        Dot1xSupplicantAuthResults      MinAuthSuccessDurationInMsec     NUMERIC                        17            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {tx_start_pkts                    Dot1xEapolResults               TxStartPktCount                  NUMERIC                        18            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_logoff_pkts                   Dot1xEapolResults               TxLogoffPktCount                 NUMERIC                        19            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_key_pkts                      Dot1xEapolResults               TxKeyPktCount                    NUMERIC                        20            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_pkts                      Dot1xEapolResults               TxEapPktCount                    NUMERIC                        21            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_pkts                      Dot1xEapolResults               RxEapPktCount                    NUMERIC                        22            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_invalid_pkts                  Dot1xEapolResults               RxInvalidPktCount                NUMERIC                        23            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {avg_start_pkt_latency            Dot1xEapolResults               AvgStartPktLatencyInMsec         NUMERIC                        24            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {min_start_pkt_latency            Dot1xEapolResults               MinStartPktLatencyInMsec         NUMERIC                        25            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {max_start_pkt_latency            Dot1xEapolResults               MaxStartPktLatencyInMsec         NUMERIC                        26            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {avg_logoff_pkt_latency           Dot1xEapolResults               AvgLogoffPktLatencyInMsec        NUMERIC                        27            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {min_logoff_pkt_latency           Dot1xEapolResults               MinLogoffPktLatencyInMsec        NUMERIC                        28            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {max_logoff_pkt_latency           Dot1xEapolResults               MaxLogoffPktLatencyInMsec        NUMERIC                        29            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {avg_key_pkt_latency              Dot1xEapolResults               AvgKeyPktLatencyInMsec           NUMERIC                        30            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {min_key_pkt_latency              Dot1xEapolResults               MinKeyPktLatencyInMsec           NUMERIC                        31            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {max_key_pkt_latency              Dot1xEapolResults               MaxKeyPktLatencyInMsec           NUMERIC                        32            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {avg_eap_pkt_latency              Dot1xEapolResults               AvgEapPktLatencyInMsec           NUMERIC                        33            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {min_eap_pkt_latency              Dot1xEapolResults               MinEapPktLatencyInMsec           NUMERIC                        34            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {max_eap_pkt_latency              Dot1xEapolResults               MaxEapPktLatencyInMsec           NUMERIC                        35            _none_          _none_        TRUE       _none_                 FALSE         _none_             {session ""}               _none_}
      {tx_eap_req_pkts                  Dot1xEapPktResults              TxRequestPktCount                NUMERIC                        36            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_req_pkts                  Dot1xEapPktResults              RxRequestPktCount                NUMERIC                        37            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_resp_pkts                 Dot1xEapPktResults              TxResponsePktCount               NUMERIC                        38            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_resp_pkts                 Dot1xEapPktResults              RxResponsePktCount               NUMERIC                        39            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_success_pkts              Dot1xEapPktResults              RxSuccessPktCount                NUMERIC                        40            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_failure_pkts              Dot1xEapPktResults              RxFailurePktCount                NUMERIC                        41            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_} 
      {tx_eap_resp_id_pkts              Dot1xEapMethodResults           TxIdentityPktCount               NUMERIC                        42            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_req_id_pkts               Dot1xEapMethodResults           RxIdentityPktCount               NUMERIC                        43            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_resp_notif_pkts           Dot1xEapMethodResults           TxNotificationPktCount           NUMERIC                        44            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_resp_notif_pkts           Dot1xEapMethodResults           RxNotificationPktCount           NUMERIC                        45            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_resp_legacy_nak_pkts      Dot1xEapMethodResults           TxLegacyNakPktCount              NUMERIC                        46            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_} 
      {tx_eap_resp_expanded_nak_pkts    Dot1xEapMethodResults           TxIdentityPktCount               NUMERIC                        47            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_resp_expanded_types_pkts  Dot1xEapMethodResults           RxIdentityPktCount               NUMERIC                        48            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_resp_expanded_types_pkts  Dot1xEapMethodResults           TxNotificationPktCount           NUMERIC                        49            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {tx_eap_resp_md5_chal_pkts        Dot1xEapMethodResults           RxNotificationPktCount           NUMERIC                        50            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
      {rx_eap_resp_md5_chal_pkts        Dot1xEapMethodResults           RxNotificationPktCount           NUMERIC                        51            _none_          _none_        TRUE       _none_                 FALSE         _none_             {aggregate "" session ""}  _none_}
   }
}
