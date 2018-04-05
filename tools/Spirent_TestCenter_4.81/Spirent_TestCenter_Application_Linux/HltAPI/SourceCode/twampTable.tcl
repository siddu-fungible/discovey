# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::twamp:: {
}

set ::sth::twamp::twampTable {
   ::sth::twamp::
   {emulation_twamp_config
      {hname                         stcobj                     stcattr                      type                        priority         default     range     supported     dependency  mandatory              mode                        procfunc    constants}
      {handle                        _none_                      _none_                      ALPHANUM                           1          _none_   _none_          TRUE      _none_      TRUE         {create "" modify "" delete ""}       _none_    _none_}
      {mode                          _none_                      _none_                      {CHOICES create modify delete}     1          _none_   _none_          TRUE      _none_      FALSE       {create "" modify "" delete ""}       _none_    _none_}
      {type                          _none_                      _none_                      {CHOICES server client}            1          _none_   _none_          TRUE      _none_      FALSE         {create "" modify "" delete ""}       _none_    _none_}
      {connection_retry_cnt       TwampClientConfig             ConnectionRetryCount         NUMERIC                            2           100   0-65535           TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {connection_retry_interval  TwampClientConfig             ConnectionRetryInterval      NUMERIC                            2           30    10-300            TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {ipv6_if_type               TwampClientConfig             Ipv6IfType                   {CHOICES global linklocal}         2           global  _none_          TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {ip_version                 TwampClientConfig             IpVersion                    {CHOICES ipv4 ipv6}                2           ipv4    _none_          TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {peer_ipv4_addr             TwampClientConfig             PeerIpv4Addr                 ANY                                2          _none_    _none_         TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {peer_ipv6_addr             TwampClientConfig             PeerIpv6Addr                 ANY                                2          _none_    _none_         TRUE      _none_      FALSE         {create configTwampClient modify configTwampClient}       _none_    _none_}
      {scalability_mode           TwampClientConfig             ScalabilityMode              {CHOICES discard_test_session_statistics normal}   \
                                                                                                                                2           normal   _none_         TRUE      _none_      FALSE         {create configTwampServer modify configTwampServer}       _none_    _none_}
      {server_ipv6_if_type        TwampServerConfig             Ipv6IfType                   {CHOICES global linklocal}         2           global  _none_          TRUE      _none_      FALSE         {create configTwampServer modify configTwampServer}       _none_    _none_}
      {server_ip_version          TwampServerConfig             IpVersion                    {CHOICES ipv4 ipv6}                2           ipv4    _none_          TRUE      _none_      FALSE         {create configTwampServer modify configTwampServer}       _none_    _none_}
      {server_mode                TwampServerConfig             Mode                         {CHOICES unauthenticated}          2           unauthenticated  _none_ TRUE      _none_      FALSE         {create configTwampServer modify configTwampServer}       _none_    _none_}
      {server_willing_to_participate TwampServerConfig         WillingToParticipate          {CHOICES true false}               2          true      _none_         TRUE      _none_      FALSE         {create configTwampServer modify configTwampServer}       _none_    _none_}
        
   }
   
   {emulation_twamp_session_config
      {hname                         stcobj                     stcattr                      type                        priority         default     range     supported     dependency  mandatory              mode                        procfunc    constants}
      {handle                        _none_                      _none_                      ALPHANUM                           1          _none_   _none_          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {mode                          _none_                      _none_                      {CHOICES create modify delete}     1          _none_   _none_          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_   _none_}
      {dscp                       TwampTestSession             DSCP                         NUMERIC                            2           0     0-63              TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {duration                   TwampTestSession             Duration                     NUMERIC                            2           60    _none_            TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {duration_mode              TwampTestSession             DurationMode                 {CHOICES continuous packets seconds} 2     seconds  _none_             TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {frame_rate                 TwampTestSession             FrameRate                    NUMERIC                            2           10    1-1000            TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_   _none_}
      {session_name               TwampTestSession             Name                         ANY                                2          _none_    _none_         TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_   _none_}
      {pck_cnt                    TwampTestSession             PacketCount                  NUMERIC                            2           100      _none_         TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {padding_len                TwampTestSession             PaddingLength                NUMERIC                            2           128     27-9000         TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {padding_pattern            TwampTestSession             PaddingPattern               {CHOICES random user_defined}      2           random  _none_          TRUE      _none_      FALSE        {create configTwampSession modify configTwampSession}      _none_    _none_}
      {padding_user_defined_pattern TwampTestSession           PaddingUserDefinedPattern      ANY                              2           0x0000  _none_          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_   _none_}
      {scalability_mode           TwampTestSession             ScalabilityMode             {CHOICES discard_test_session_statistics normal} 2  normal  _none_          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {session_dst_udp_port       TwampTestSession             SessionDstUdpPort            NUMERIC                            2           5450   1-65535          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {session_src_udp_port       TwampTestSession             SessionSrcUdpPort            NUMERIC                            2           5450   1-65535          TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {start_delay                TwampTestSession             StartDelay                   NUMERIC                            2           5     _none_            TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {timeout                    TwampTestSession             timeout                      NUMERIC                            2           30    _none_            TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
      {ttl                        TwampTestSession             Ttl                          NUMERIC                            2           255   1-255             TRUE      _none_      FALSE         {create configTwampSession modify configTwampSession}      _none_    _none_}
   }
      
   {emulation_twamp_control
      {hname               stcobj    stcattr     type                    priority   default   range    supported   dependency mandatory  procfunc action  constants}
      {handle              _none_    _none_      ALPHANUM                   1        _none_    _none_    TRUE        _none_     FALSE      _none_   _none_  _none_} 
      {port_handle         _none_    _none_      ALPHANUM                   1        _none_   _none_    TRUE       _none_     FALSE       _none_    _none_  _none_}
      {mode                _none_    _none_      {CHOICES start stop establish request_twamp_sessions start_twamp_sessions stop_twamp_sessions pause_twamp_session_traffic resume_twamp_session_traffic} \
                                                                            1        _none_    _none_    TRUE        _none_     FALSE       _none_   _none_  _none_}
      {delay_time         _none_    _none_       ANY                        2          30      _none_    TRUE        _none_     FALSE       _none_    _none_  _none_}
   }
   {emulation_twamp_stats
      {hname         stcobj   stcattr    type                    priority    default  range   supported   dependency   mandatory  procfunc  mode    constants}
      {handle        _none_   _none_     ALPHANUM                    1       _none_    _none_    TRUE       _none_     FALSE       _none_    _none_  _none_}
      {port_handle   _none_   _none_     ALPHANUM                    1       _none_    _none_    TRUE       _none_     FALSE       _none_    _none_  _none_}
      {mode          _none_   _none_     {CHOICES state_summary client server test_session port_test_session aggregated_client aggregated_server clear_stats} 2       state_summary   _none_    TRUE       _none_     FALSE      _none_    _none_  _none_}     
   }
   {twamp_stats_summary
      {hname                  stcobj                stcattr             type      priority    default  ange     supported  dependency   mandatory  procfunc   mode   constants}
      {connect_cnt         TwampStateSummary     ConnectCount           ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {connections_down_cnt TwampStateSummary    ConnectionsDownCount   ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {connections_up_cnt  TwampStateSummary     ConnectionsUpCount     ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {established_cnt     TwampStateSummary     EstablishedCount       ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {idle_cnt            TwampStateSummary     IdleCount              ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
      {sess_requested_cnt  TwampStateSummary     SessionRequestedCount  ANY          16       _none_    _none_    TRUE     _none_       _none_     _none_    _none_    _none_    }
   }
   {twamp_stats_client
      {hname                   stcobj            stcattr           type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {rx_accept_sess_cnt TwampClientResults  RxAcceptSessionCount  ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_failed_sess_cnt TwampClientResults  RxFailedSessionCount  ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_start_ack_cnt   TwampClientResults  RxStartAckCount       ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_req_tw_sess_cnt TwampClientResults  TxReqTwSessionCount   ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }    
      {tx_start_sess_cnt  TwampClientResults  TxStartSessionCount   ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }      
      {tx_stop_sess_cnt   TwampClientResults  TxStopSessionCount    ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   }
   {twamp_stats_server
      {hname                   stcobj            stcattr           type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {rx_req_tw_sess_cnt  TwampServerResults  RxReqTwSessionCount  ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_start_sess_cnt   TwampServerResults  RxStartSessionCount  ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {rx_stop_sess_cnt    TwampServerResults  RxStopSessionCount   ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {tx_accept_sess_cnt  TwampServerResults  TxAcceptSessionCount ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }    
      {tx_failed_sess_cnt  TwampServerResults  TxFailedSessionCount ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }      
      {tx_start_ack_cnt    TwampServerResults  TxStartAckCount      ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   }
   {twamp_stats_porttestsession
      {hname                        stcobj                         stcattr                type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {avg_jitter                   TwampPortTestSessionResults    AvgJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {avg_latency                  TwampPortTestSessionResults    AvgLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {avg_server_processing_time   TwampPortTestSessionResults    AvgServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_jitter                   TwampPortTestSessionResults    MaxJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_latency                  TwampPortTestSessionResults    MaxLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_server_processing_time   TwampPortTestSessionResults    MaxServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_jitter                   TwampPortTestSessionResults    MinJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_latency                  TwampPortTestSessionResults    MinLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_server_processing_time   TwampPortTestSessionResults    MinServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   }
   {twamp_stats_testsession
      {hname                        stcobj                         stcattr                type   priority    default    range supported  dependency mandatory  procfunc     mode    constants}
      {avg_jitter                   TwampTestSessionResults    AvgJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {avg_latency                  TwampTestSessionResults    AvgLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {avg_server_processing_time   TwampTestSessionResults    AvgServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_jitter                   TwampTestSessionResults    MaxJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_latency                  TwampTestSessionResults    MaxLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {max_server_processing_time   TwampTestSessionResults    MaxServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_jitter                   TwampTestSessionResults    MinJitter               ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_latency                  TwampTestSessionResults    MinLatency              ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
      {min_server_processing_time   TwampTestSessionResults    MinServerProcessingTime ANY       16       _none_    _none_    TRUE    _none_       _none_     _none_    _none_    _none_ }
   }
   

}
