namespace eval ::sth::microBfd:: {
}

set ::sth::microBfd::microBfdTable {
::sth::microBfd::

  { emulation_micro_bfd_config 
    { hname                               stcobj                  stcattr                    type                      priority           default                range         supported       dependency          mandatory    procfunc      mode    constants}
    { port_handle                         _none_                  _none_                     ALPHANUM                      1               _none_                _none_          true            _none_              false       _none_      _none_      _none_ }
    { handle                              _none_                  _none_                     ALPHANUM                      1               _none_                _none_          true            _none_              false       _none_      _none_      _none_ }
    { mode                                _none_                  _none_                     {CHOICES create modify reset} 2               _none_                _none_          true            _none_              true        _none_      _none_      _none_ }
    { active                        LagBfdPortConfig              Active                     {CHOICES true false}          6                true                 _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { detect_multiplier             LagBfdPortConfig              DetectMultiplier           NUMERIC                       6                3                    _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { echo_rx_interval              LagBfdPortConfig              EchoRxInterval             NUMERIC                       6                0                    _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { enable_my_discriminator_ipv4  LagBfdPortConfig              EnableMyDiscriminatorIpv4  {CHOICES true false}          6                false                _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { enable_my_discriminator_ipv6  LagBfdPortConfig              EnableMyDiscriminatorIpv6  {CHOICES true false}          6                false                _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { interval_time_unit            LagBfdPortConfig              IntervalTimeUnit           {CHOICES msec usec}           6                msec                 _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { ipv4_dest_addr                LagBfdPortConfig              Ipv4SessionAddr            IPV4                          6                192.0.0.1            _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { ipv4_src_addr                 LagBfdPortConfig              Ipv4SrcAddr                IPV4                          6                190.0.0.1            _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { ipv6_mask                     LagBfdPortConfig              Ipv6Mask                   NUMERIC                       6                128                  _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { ipv6_dest_addr                LagBfdPortConfig              Ipv6SessionAddr            IPV6                          6                "2001::1"            _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { ipv6_src_addr                 LagBfdPortConfig              Ipv6SrcAddr                IPV6                          6                "2000::1"            _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { my_discriminator_ipv4         LagBfdPortConfig              MyDiscriminatorIpv4        NUMERIC                       6                1                    _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { my_discriminator_ipv6         LagBfdPortConfig              MyDiscriminatorIpv6        NUMERIC                       6                1                    _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { name                          LagBfdPortConfig              Name                       ANY                           6                _none_               _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { router_role                   LagBfdPortConfig              RouterRole                 {CHOICES active passive}      6                active               _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { rx_interval                   LagBfdPortConfig              RxInterval                 NUMERIC                       6                50                   _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { source_mac                    LagBfdPortConfig              SourceMac                  MAC                           6                "00:10:94:00:00:02"  _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { tx_interval                   LagBfdPortConfig              TxInterval                 NUMERIC                       6                50                   _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { udp_dst_port                  LagBfdPortConfig              UdpDstPort                 NUMERIC                       6                6784                 _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { use_partial_block_state       LagBfdPortConfig              UsePartialBlockState       {CHOICES true false}          6                false                _none_          true            _none_              false       _none_      {create configLagBfdport modify configLagBfdport}      _none_ }
    { authentication                BfdAuthenticationParams       Authentication             {CHOICES md5 none simple}     7                none                 _none_          true            _none_              false       _none_      {create configBfdAuth modify configBfdAuth}      _none_ }
    { md5_key_id                    BfdAuthenticationParams       Md5KeyId                   NUMERIC                       7                1                    _none_          true            _none_              false       _none_      {create configBfdAuth modify configBfdAuth}      _none_ }
    { password                      BfdAuthenticationParams       Password                   ANY                           7                "Spirent"            _none_          true            _none_              false       _none_      {create configBfdAuth modify configBfdAuth}      _none_ }
  }                                                                                                                                                                                                                                    

  { emulation_micro_bfd_control 
    { hname             stcobj             stcattr             type                    priority         default            range      supported       dependency          mandatory    procfunc      mode    constants}
    { port_handle       _none_             _none_              ALPHANUM                    1             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { handle            _none_             _none_              ALPHANUM                    1             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { action            _none_             _none_      {CHOICES start stop delete admin_up admin_down initiate_poll resume_pdus stop_pdus set_diagnostic_state}         5             _none_            _none_       true            _none_              true        _none_      _none_   _none_}
    { bfd_diagnostic_code  _none_          _none_      {CHOICES admin_down cd_time_expire concat_path_down echo_function_failed for_plane_reset nbor_sig_session_down no_diagnostic path_down reverse_concat_path_down} \
    7              no_diagnostic    _none_      true            {action set_diagnostic_state}     false       _none_      {create configBfdAuth modify configBfdAuth}      _none_ }
  }

  { emulation_micro_bfd_info 
    { hname             stcobj             stcattr             type                    priority         default            range      supported       dependency          mandatory    procfunc      mode    constants}
    { port_handle       _none_             _none_              ALPHANUM                    1             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { handle            _none_             _none_              ALPHANUM                    1             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { mode              _none_             _none_              ANY                         3             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
  }
  { emulation_micro_bfd_info_port
    { hname                               stcobj                  stcattr                   type                    priority     default            range      supported       dependency          mandatory    procfunc      mode    constants}
    { sessions_down_count           LagBfdPortConfig              SessionsDownCount          ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { sessions_up_count             LagBfdPortConfig              SessionsUpCount            ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { flap_count                    LagBfdPortResults             FlapCount                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_count                      LagBfdPortResults             RxCount                    ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { timeout_count                 LagBfdPortResults             TimeoutCount               ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_count                      LagBfdPortResults             TxCount                    ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
  }
  { emulation_micro_bfd_info_session
    { hname                                    stcobj             stcattr                   type                priority         default            range      supported       dependency          mandatory    procfunc      mode    constants}
    { bfd_control_bits              LagBfdPortIpv4SessionResults  BfdControlBits             ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { bfd_diagnostic_code           LagBfdPortIpv4SessionResults  BfdDiagnosticCode          ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { bfd_session_state             LagBfdPortIpv4SessionResults  BfdSessionState            ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { flap_count                    LagBfdPortIpv4SessionResults  FlapCount                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { ipv4dst_addr                  LagBfdPortIpv4SessionResults  ipv4DstAddr                ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { ipv4src_addr                  LagBfdPortIpv4SessionResults  ipv4SrcAddr                ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { last_bfd_diagnostic_error_rx  LagBfdPortIpv4SessionResults  LastBfdDiagnosticErrorRx   ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { my_discriminator              LagBfdPortIpv4SessionResults  MyDiscriminator            ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_avg_rate                   LagBfdPortIpv4SessionResults  RxAvgRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_count                      LagBfdPortIpv4SessionResults  RxCount                    ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_desired_min_rx_interval    LagBfdPortIpv4SessionResults  RxDesiredMinRxInterval     ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_max_rate                   LagBfdPortIpv4SessionResults  RxMaxRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { rx_min_rate                   LagBfdPortIpv4SessionResults  RxMinRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { timeout_count                 LagBfdPortIpv4SessionResults  TimeoutCount               ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_avg_rate                   LagBfdPortIpv4SessionResults  TxAvgRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_count                      LagBfdPortIpv4SessionResults  TxCount                    ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_interval                   LagBfdPortIpv4SessionResults  TxInterval                 ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_max_rate                   LagBfdPortIpv4SessionResults  TxMaxRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { tx_min_rate                   LagBfdPortIpv4SessionResults  TxMinRate                  ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
    { your_discriminator            LagBfdPortIpv4SessionResults  YourDiscriminator          ANY                    2             _none_            _none_       true            _none_              false       _none_      _none_   _none_}
  }
}