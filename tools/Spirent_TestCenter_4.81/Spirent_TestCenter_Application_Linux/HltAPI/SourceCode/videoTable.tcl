namespace eval ::sth::video:: {
}

set ::sth::video::videoTable {
    ::sth::video::
    {emulation_video_config
        {hname                                             stcobj                                  stcattr                                 type              priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {handle                                            _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          true          _none_          _none_          _none_}
        {mode                                              _none_                                  _none_                        {CHOICES enable modify }    10          _none_          _none_          true          _none_          true          _none_          _none_          _none_}
        {type                                              _none_                                  _none_                        {CHOICES client server }    10          _none_          _none_          true          _none_          true          _none_          _none_          _none_}
        {server_clip_file                             VideoServerProtocolConfig                    ClipFiles                               ANY               10          _none_          _none_          true          {type server}   false          _none_          _none_          _none_}
        {client_clip_file                             VideoClientProtocolConfig                    ClipFile                                ANY               10          _none_          _none_          true          {type client}   false          _none_          _none_          _none_}
        {event_rec_enable                             VideoServerProtocolConfig                    EnableEventRecording          {CHOICES true false }       10          false           _none_          true          {type server}   false          _none_          _none_          _none_}
        {rtsp_enable                                  VideoServerProtocolConfig                    RtspEnabled                   {CHOICES true false }       10          true            _none_          true          {type server}   false          _none_          _none_          _none_}
        {rtsp_port_num                                VideoServerProtocolConfig                    RtspPortNum                         NUMERIC               10          554             _none_          true          {type server}   false          _none_          _none_          _none_}
        {server_name                                  VideoServerProtocolConfig                    ServerName                              ANY               10          _none_          _none_          false         {type server}   false          _none_          _none_          _none_}
        {use_partial_block_state         VideoServerProtocolConfig|VideoClientProtocolConfig       UsePartialBlockState          {CHOICES true false }       10          _none_          _none_          false         _none_          false          _none_          _none_          _none_}
        {server_profile                               VideoServerProtocolConfig                    AffiliatedServerProfile-targets         ANY               10          _none_          _none_          true          {type server}   false          _none_          _none_          _none_}
        {client_name                                  VideoClientProtocolConfig                    ClientName                              ANY               10          _none_          _none_          false          {type client}   false          _none_          _none_          _none_}
        {dst_ip_addr                                  VideoClientProtocolConfig                    DstIpAddr                               IP                10          0.0.0.0          _none_          true          {type client}   false          _none_          _none_          _none_}
        {dst_port                                     VideoClientProtocolConfig                    DstPort                             NUMERIC               10          50050           _none_          true          {type client}   false          _none_          _none_          _none_}
        {dynamic_load                                 VideoClientProtocolConfig                    DynamicLoad                          NUMERIC              10          30              1-1000000       false         {type client}   false          _none_          _none_          _none_}
        {endpoint_connection_pattern                  VideoClientProtocolConfig                    EndpointConnectionPattern  {CHOICES pair backbone_src_first backbone_dst_first backbone_interleaved}  10          pair          _none_          false         {type client}   false          _none_          _none_          _none_}
        {loop                                         VideoClientProtocolConfig                    Loop                          {CHOICES true false }       10          false          _none_          true          {type client}   false          _none_          _none_          _none_}
        {client_profile                               VideoClientProtocolConfig                    AffiliatedClientProfile-targets         ANY               10          _none_          _none_          true          {type client}   false          _none_          _none_          _none_}
        {load_profile                                 VideoClientProtocolConfig                    AffiliatedClientLoadProfile-targets     ANY               10          _none_          _none_          false          {type client}   false          _none_          _none_          _none_}
        {connected_server                             VideoClientProtocolConfig                    ConnectionDestination-targets           ANY               10          _none_          _none_          true          {type client}   false          _none_          _none_          _none_}
    }
    {emulation_video_server_streams_config
        {hname                                             stcobj                                  stcattr                                 type              priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {handle                                            _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          false          _none_          _none_          _none_}
        {stream_handle                                     _none_                                  _none_                                  ANY               10          _none_          _none_          true         {mode modify}    false          _none_          _none_          _none_}
        {mode                                              _none_                                  _none_                        {CHOICES create modify delete}    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {dst_ip_addr                                  VideoServerStream                            DstIpAddr                               IP                10          0.0.0.0         _none_          true          _none_          false          _none_          _none_          _none_}
        {dst_port                                     VideoServerStream                            DstPort                              NUMERIC              10          50050           _none_          true          _none_          false          _none_          _none_          _none_}
        {loop_enable                                  VideoServerStream                            Loop                            {CHOICES true false}      10          true            _none_          true          _none_          false          _none_          _none_          _none_}
        {transport_type                               VideoServerStream                            Transport                       {CHOICES udp rtp}         10          udp             _none_          true          _none_          false          _none_          _none_          _none_}
        {name                                         VideoServerStream                            Name                                    ANY               10          _none_           _none_          true          _none_          false          _none_          _none_          _none_}
}

    {emulation_profile_config
        {hname                                             stcobj                             stcattr                                 type              priority    default         range           supported       dependency          mandatory       procfunc        mode           constants}
        {mode                                              _none_                             _none_                        {CHOICES create modify delete}    10          _none_          _none_          true            _none_              true            _none_          _none_          _none_}
        {handle                                            _none_                             _none_                                  ANY               10          _none_          _none_          true            {mode modify}       false           _none_          _none_          _none_}
        {profile_type                                      _none_                             _none_                       {CHOICES client server load} 10          _none_          _none_          true            _none_              true            _none_          _none_          _none_}
        {load_type                                       ClientLoadProfile                    LoadType {CHOICES connections connections_per_time_unit transactions transactions_per_time_unit bandwidth playlists}  10 connections  _none_  true {type load}   false _none_ _none_  _none_}
        {max_connections_attempted                       ClientLoadProfile                    MaxConnectionsAttempted                 NUMERIC           10          4294967295      _none_          true            {type load}         false           _none_          _none_          _none_}
        {max_open_connections                            ClientLoadProfile                    MaxOpenConnections                      NUMERIC           10          4096            _none_          true            {type load}         false           _none_          _none_          _none_}
        {max_transactions_attempted                      ClientLoadProfile                    MaxTransactionsAttempted                NUMERIC           10          4294967295      _none_          true            {type load}         false           _none_          _none_          _none_}
        {randomization_seed                              ClientLoadProfile                    RandomizationSeed                       NUMERIC           10          123456          _none_          true            {type load}         false           _none_          _none_          _none_}
        {use_dynamic_load                                ClientLoadProfile                    UseDynamicLoad                 {CHOICES true false}       10          false           _none_          true            {type load}         false           _none_          _none_          _none_}
        {delayed_ack_enable                              ClientProfile|ServerProfile          EnableDelayedAck               {CHOICES true false}       10          false           _none_          true            {type client server} false          _none_          _none_          _none_}
        {ipv4_tos                                        ClientProfile|ServerProfile          Ipv4Tos                                 NUMERIC           10          192             0-255           true            {type client server} false          _none_          _none_          _none_}
        {ipv6_traffic_class                              ClientProfile|ServerProfile          Ipv6TrafficClass                        NUMERIC           10          0               0-255           true            {type client server} false          _none_          _none_          _none_}
        {profile_name                       ClientProfile|ServerProfile|ClientLoadProfile     ProfileName                             ANY               10          _none_          _none_          true            _none_              false           _none_          _none_          _none_}
        {rx_window_size_limit                            ClientProfile|ServerProfile          RxWindowSizeLimit                       NUMERIC           10          32768           _none_          true            {type client server} false          _none_          _none_          _none_}
        {tostype                                         ClientProfile|ServerProfile          TosType                        {CHOICES tos diffserv}     10          tos             _none_          false            {type client server} false          _none_          _none_          _none_}
    }
    {emulation_client_load_phase_config
        {hname                                  stcobj                                          stcattr                             type                                      priority       default        range           supported   dependency  mandatory   procfunc      mode                              constants   }
        {mode                                   _none_                                          _none_                  {CHOICES create modify delete}                          1           create         _none_           true        _none_      true        _none_      _none_                              _none_     }
        {load_pattern                           ClientLoadPhase                                 LoadPattern             {CHOICES stair flat burst sinusoid random sawtooth}     2           flat           _none_           true        _none_      false       _none_      {create load_phase_config modify load_phase_config}           _none_      }
        {duration_units                         ClientLoadPhase                                 LoadPhaseDurationUnits  {CHOICES milliseconds seconds minutes hours}            2           seconds         _none_           true        _none_      false       _none_      {create load_phase_config modify load_phase_config}           _none_      }
	    {phase_name                             ClientLoadPhase                                 PhaseName                           ANY                                         2           _none_         _none_           true        _none_      false       _none_      {create load_phase_config modify load_phase_config}           _none_      }
	    {phase_num                              ClientLoadPhase                                 PhaseNum                            NUMERIC                                     2           _none_           0-7            false        _none_      false       _none_      {create load_phase_config modify load_phase_config}           _none_      }
	    {profile_handle                         _none_                                          _none_                              ANY                                         1           _none_         _none_           true        _none_      false       _none_      _none_ 	                            _none_      }
        {phase_handle                           _none_                                          _none_                              ANY                                         1           _none_         _none_           true        _none_      false       _none_      _none_                              _none_      }
        {height  StairPatternDescriptor|FlatPatternDescriptor|BurstPatternDescriptor|SinusoidPatternDescriptor|SawToothPatternDescriptor|RandomPatternDescriptor  Height  NUMERIC                       2           30              _none_          true        _none_      false       _none_      _none_                              _none_      }
        {ramp_time              StairPatternDescriptor|FlatPatternDescriptor|RandomPatternDescriptor                    RampTime                            NUMERIC                                     2           20              0-4294967295    true        _none_      false       _none_      _none_                              _none_  }
        {repetitions     StairPatternDescriptor|BurstPatternDescriptor|SinusoidPatternDescriptor|SawToothPatternDescriptor|RandomPatternDescriptor Repetitions NUMERIC                                  2           1               0-4294967295    true        _none_      false       _none_      _none_                              _none_      }
        {steady_time     StairPatternDescriptor|FlatPatternDescriptor|SawToothPatternDescriptor|RandomPatternDescriptor SteadyTime                          NUMERIC                                     2           40              0-4294967295    true        _none_      false       _none_      _none_                              _none_      }
        {burst_time                         BurstPatternDescriptor                              BurstTime                           NUMERIC                                     2           20              0-4294967295    true        _none_      false       _none_      _none_                              _none_      }
        {pause_time      BurstPatternDescriptor|SawToothPatternDescriptor                       PauseTime                           NUMERIC                                     2           40              0-4294967295    true        _none_      false       _none_      _none_                              _none_      }
        {period                             SinusoidPatternDescriptor                           Period                              NUMERIC                                     2           600             0-4294967295    true        _none_      false       _none_      _none_                              _none_   }
    }
    {emulation_video_control
        {hname                                             stcobj                                  stcattr                                 type              priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {port_handle                                       _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          false          _none_          _none_          _none_}
        {handle                                            _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          false          _none_          _none_          _none_}
        {mode                                              _none_                                  _none_                        {CHOICES start stop}        10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
    }
    {emulation_video_clips_manage
        {hname                                             stcobj                                  stcattr                                 type              priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {mode                                              _none_                                  _none_                        {CHOICES upload delete }    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {file_name                        VideoClipDownloadCommand|VideoClipDeleteCommand          FileName                                ANY               10          _none_         _none_           true          _none_          false          _none_          _none_          _none_}
        {server_list                      VideoClipDownloadCommand|VideoClipDeleteCommand          ServerRefList                           ANY               10          _none_         _none_           true          _none_          false          _none_          _none_          _none_}
    }

    {emulation_video_stats
        {hname                                             stcobj                                  stcattr                                 type              priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {port_handle                                       _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          false          _none_          _none_          _none_}
        {handle                                            _none_                                  _none_                                  ANY               10          _none_          _none_          true          _none_          false          _none_          _none_          _none_}
        {mode                                              _none_                                  _none_                        {CHOICES client server session}    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
    }

    {emulation_video_stats_client
        {hname                                             stcobj                                           stcattr                                 type      priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {aborted_connections                            VideoClientResults                                  AbortedConnections                      _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {aborted_transactions                           VideoClientResults                                  AbortedTransactions                     _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {attempted_connections                          VideoClientResults                                  AttemptedConnections                    _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {attempted_transactions                         VideoClientResults                                  AttemptedTransactions                   _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {block_index                                    VideoClientResults                                  BlockIndex                              _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {last_modified                                  VideoClientResults                                  LastModified                            _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {parent_name                                    VideoClientResults                                  ParentName                              _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code200                            VideoClientResults                                  RxResponseCode200                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code400                            VideoClientResults                                  RxResponseCode400                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code403                            VideoClientResults                                  RxResponseCode403                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code404                            VideoClientResults                                  RxResponseCode404                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code405                            VideoClientResults                                  RxResponseCode405                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code454                            VideoClientResults                                  RxResponseCode454                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code459                            VideoClientResults                                  RxResponseCode459                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {rx_response_code461                            VideoClientResults                                  RxResponseCode461                       _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {successful_connections                         VideoClientResults                                  SuccessfulConnections                   _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {successful_transactions                        VideoClientResults                                  SuccessfulTransactions                  _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {unsuccessful_connections                       VideoClientResults                                  UnsuccessfulConnections                 _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {unsuccessful_transactions                      VideoClientResults                                  UnsuccessfulTransactions                _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
    }
    {emulation_video_stats_server
        {hname                                             stcobj                                             stcattr                                  type      priority    default         range           supported     dependency      mandatory       procfunc        mode           constants}
        {block_index                                       VideoServerResults                                  BlockIndex                               _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {last_modified                                     VideoServerResults                                  LastModified                             _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {parent_name                                       VideoServerResults                                  ParentName                               _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {successful_transactions                           VideoServerResults                                  SuccessfulTransactions                   _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {sotal_connections                                 VideoServerResults                                  TotalConnections                         _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code200                                VideoServerResults                                  TxResponseCode200                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code400                                VideoServerResults                                  TxResponseCode400                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code403                                VideoServerResults                                  TxResponseCode403                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code404                                VideoServerResults                                  TxResponseCode404                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code405                                VideoServerResults                                  TxResponseCode405                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code454                                VideoServerResults                                  TxResponseCode454                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code459                                VideoServerResults                                  TxResponseCode459                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {tx_response_code461                                VideoServerResults                                  TxResponseCode461                        _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
        {unsuccessful_transactions                         VideoServerResults                                  UnsuccessfulTransactions                 _none_    10          _none_          _none_          true          _none_          true           _none_          _none_          _none_}
   }
}
