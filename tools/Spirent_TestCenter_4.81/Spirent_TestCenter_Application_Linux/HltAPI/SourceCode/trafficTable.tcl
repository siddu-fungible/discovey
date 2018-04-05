# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Traffic:: {
}

set ::sth::Traffic::trafficTable {
 ::sth::Traffic::
 {    traffic_control
    {hname          stcobj        stcattr       type      priority      default         range       supported    dependency mandatory   procfunc                                            mode       constants    }
    {port_handle    _none_        _none_        ALPHANUM    1           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_controlPort_handle     _none_     _none_       }
    {action         _none_        _none_        ALPHANUM    3           _none_          _none_      true         _none_        true   ::sth::Traffic::processTraffic_controlAction          _none_     _none_       }
    {elapsed_time   _none_        _none_      {CHOICES 0 1} 1              0            _none_      true         _none_        false  _none_                                                _none_     _none_       }
    {latency_bins   _none_        _none_        NUMERIC     2           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_configlatency_bins     _none_     _none_       }
    {latency_values _none_        _none_        ANY         2           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_configlatency_values   _none_     _none_       }
    {bucket_size_unit  LatencyHistogram   BucketSizeUnit  {CHOICES ten_nanoseconds microseconds milliseconds seconds} 2 ten_nanoseconds   _none_   true    _none_   false   _none_          _none_     _none_       }
    {traffic_start_mode _none_    _none_   {CHOICES async sync}  2      _none_          _none_      true         _none_        false  _none_                                                _none_     _none_       }
    {duration       _none_        Duration      ANY         1           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_controlDuration        _none_     _none_       }
    {get            _none_        _none_        ANY         2           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_setFilter              _none_     _none_       }
    {stream_handle  _none_        _none_        ALPHANUM    1           _none_          _none_      true         _none_        false  ::sth::Traffic::processTraffic_controlPort_handle     _none_     _none_       }
    {db_file        _none_        _none_       {CHOICES 0 1} 4             1            _none_      true         _none_        false  _none_                                                _none_     _none_       }
    {enable_arp       _none_        _none_     {CHOICES 0 1} 4             1            _none_      true         _none_        false  _none_                                                _none_     _none_       }
  }
{   start_test
    {hname          stcobj     stcattr         type        priority   default       range     supported    dependency      mandatory   procfunc         mode       constants  }
    {duration       _none_     _none_         NUMERIC       1        _none_          _none_      true         _none_         false      _none_         _none_        _none_}
    {wait           _none_     _none_         NUMERIC       2           1           _none_      true         _none_          false      _none_         _none_        _none_}
    {clear_stats    _none_     _none_     {CHOICES 0 1}     2           1           _none_      true         _none_          false      _none_         _none_        _none_}
    {stream_handle  _none_     _none_         ALPHANUM      1        _none_          _none_      true         _none_         false      _none_         _none_        _none_}
}
{    traffic_stats
    {hname          stcobj     stcattr         type        priority   default         range       supported    dependency      mandatory  procfunc         mode     constants    }
    {mode           port     _none_            ALPHANUM       1       _none_          _none_      true         _none_             true      _none_         _none_        _none_}
    {streams        port     _none_            ALPHANUM       2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {port_handle    port     _none_            ALPHANUM       2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {rx_port_handle port     _none_            ALPHANUM       2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {properties     _none_   _none_            ANY            2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {detailed_rx_stats _none_  _none_          {CHOICES 0 1}  2       0               _none_      true         _none_             false     _none_         _none_        _none_}
    {records_per_page  _none_   _none_         NUMERIC        2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {scale_mode   _none_    _none_             {CHOICES 0 1}  2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
}
{    drv_stats
    {hname          stcobj                      stcattr             type                    priority   default          range       supported    dependency      mandatory  procfunc         mode     constants    }
    {force_load     _none_                      _none_              {CHOICES true false}        2       false          _none_      true         _none_             false     _none_         _none_        _none_}
    {size           PresentationResultQuery     LimitSize           NUMERIC                     2       50              _none_      true         _none_             false     _none_         _none_        _none_}
    {properties     PresentationResultQuery     SelectProperties    ANY                         2       ""              _none_      true         _none_             false     _none_         _none_        _none_}
    {handle         _none_                      _none_              ANY                         2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {drv_name       DynamicResultView           name                ANY                         2       custom_drv      _none_      true         _none_             false     _none_         _none_        _none_}
    {query_from           PresentationResultQuery     FromObjects         ANY                         2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {sort_by        PresentationResultQuery     SortBy              ANY                         2       ""          _none_      true         _none_             false     _none_         _none_        _none_}
    {group_by       PresentationResultQuery     GroupByProperties   ANY                         2       ""          _none_      true         _none_             false     _none_         _none_        _none_}
    {where          PresentationResultQuery     WhereConditions     ANY                         2       ""          _none_      true         _none_             false     _none_         _none_        _none_}
    {drv_xml         _none_                      _none_              ANY                        2       _none_          _none_      true         _none_             false     _none_         _none_        _none_}
    {disable_autogroup         _none_           _none_              {CHOICES true false}        2       false          _none_      true         _none_             false     _none_         _none_        _none_}
}
{ create_csv_file
    {hname                  stcobj                      stcattr             type                        priority   default          range       supported    dependency         mandatory   procfunc         mode       constants}
    {column_style        ExportResultsCommand        ColumnHeaderStyle      {CHOICES display property}  2           display         _none_      true            _none_          false       _none_          _none_      _none_}
    {file_name           ExportResultsCommand        FileNamePrefix         ANY                         2           results         _none_      true            _none_          false       _none_          _none_      _none_}
    {result_view_handle  ExportResultsCommand        ResultView             ANY                         2           _none_          _none_      true            _none_          true        _none_          _none_      _none_}
    {write_mode          ExportResultsCommand        WriteMode              {CHOICES append overwrite}  2           overwrite       _none_      true            _none_          false       _none_          _none_      _none_}
}
  {    traffic_stats_aggregate_tx_results
    {hname                    stcobj     stcattr               type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {elapsed_time             port        hlt                   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_count                port     GeneratorSigFrameCount  _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_byte_count           port     TotalOctetCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_rate                 port     GeneratorSigFrameRate  _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_bit_rate             port     GeneratorBitRate      _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {datagram_byte_count      _none_     _none_            _none_         _none_    _none_          _none_   false         _none_             false    _none_         _none_        _none_}
    {datagram_bit_rate        _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_bandwidth           _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {substream_count          _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {substream_error_count    _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {filter_count             _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkts               port       TotalFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {raw_pkt_count            port       TotalFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bytes          port       TotalOctetCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkts               _none_      _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bytes          _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bytes     _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate          _none_     TotalFrameRate    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {raw_pkt_rate          _none_     TotalFrameRate    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkt_rate           _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bit_rate       _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bit_rate  _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_rate_percentage    _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_pkts                _none_      _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_ratio               _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_checksum_errors     _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {udp_pkts                _none_      _none_            _none_       _none_    _none_          _none_    false         _none_             false    _none_         _none_        _none_}
    {ip_pkts                 _none_      _none_              _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv4_pkts               _none_  GeneratorIpv4FrameCount _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv6_pkts               _none_  GeneratorIpv6FrameCount _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_count        _none_    PfcFrameCount   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
 {    traffic_stats_aggregate_rx_results
    {hname                    stcobj     stcattr         type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants  }
    {pkt_count                port     SigFrameCount     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_byte_count           port     TotalOctetCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_rate                 port     SigFrameRate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_bit_rate             port     TotalBitRate       _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {datagram_byte_count      _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {datagram_bit_rate        _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {line_bandwidth           _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {substream_count          _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {substream_error_count    _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {filter_count             _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkts               port     TotalFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {raw_pkt_count            port     TotalFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {total_pkt_bytes          port     TotalOctetCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {good_pkts                _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bytes           _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bytes      _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkt_rate           _none_   TotalFrameRate    _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {good_pkt_rate            _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bit_rate        _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bit_rate   _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {line_rate_percentage     _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_pkts                 _none_   TcpFrameCount     _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {tcp_ratio                _none_   _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_checksum_errors      _none_   TcpChecksumErrorCount  _none_  _none_    _none_          _none_     true        _none_             false    _none_         _none_        _none_ }
    {udp_pkts                 _none_   UdpFrameCount     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {ip_pkts                 _none_    _none_            _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv4_pkts               _none_    Ipv4FrameCount    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv6_pkts               _none_    Ipv6FrameCount    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_rate          _none_  PfcFrameRate                                       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {fcoe_frame_rate     _none_     FcoeFrameRate                           _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_count         _none_     PfcFrameCount                          _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {fcoe_frame_count        _none_     FcoeFrameCount                        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {vlan_pkts_count        _none_     VlanFrameCount     _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {vlan_pkts_rate        _none_     VlanFrameRate       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {oversize_count        _none_     OversizeFrameCount  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {oversize_rate         _none_     OversizeFrameRate   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {undersize_count       _none_   UndersizeFrameCount   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {undersize_rate        _none_     UndersizeFrameRate  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
  {    traffic_stats_aggregate_txjoin_results
    {hname                                         stcobj               stcattr                       type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {elapsed_time                                  port                 hlt                           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_count                                     port                 GeneratorSigFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_byte_count                                port                 GeneratorOctetCount           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_bit_rate                                  port                 GeneratorBitRate         _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {datagram_byte_count                           _none_               _none_                        _none_       _none_    _none_          _none_   false         _none_             false    _none_         _none_        _none_}
    {datagram_bit_rate                             _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_bandwidth                                _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {substream_count                               _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {substream_error_count                         _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {filter_count                                  _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkts                                    port                 TotalFrameCount               _none_       _none_    _none_          _none_     true         _none_              false    _none_         _none_        _none_}
    {raw_pkt_count                                 port                 TotalFrameCount               _none_       _none_    _none_          _none_     true         _none_              false    _none_         _none_        _none_}
    {total_pkt_bytes                               port                 TotalOctetCount               _none_       _none_    _none_          _none_     true         _none_              false    _none_         _none_        _none_}
    {good_pkts                                     _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bytes                                _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bytes                           _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate                                _none_               TotalFrameRate                _none_       _none_    _none_          _none_     true         _none_              false    _none_         _none_        _none_}
    {raw_pkt_rate                                _none_               TotalFrameRate                _none_       _none_    _none_          _none_     true         _none_              false    _none_         _none_        _none_}
    {good_pkt_rate                                 _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bit_rate                             _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bit_rate                        _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_rate_percentage                          _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_pkts                                      _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_ratio                                     _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {tcp_checksum_errors                           _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {udp_pkts                                      _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {ip_pkts                                       _none_               _none_                        _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {ipv4_pkts                                     _none_               GeneratorIpv4FrameCount       _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_}
    {ipv6_pkts                                     _none_               GeneratorIpv6FrameCount       _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_}
    {tx_frames                                     GeneratorPortResults TotalFrameCount               _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_}
    {tx_bytes                                      GeneratorPortResults TotalOctetCount               _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_ipv4_frame_count                 GeneratorPortResults GeneratorIPv4FrameCount       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_ipv6_frame_count                 GeneratorPortResults GeneratorIPv6FrameCount       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_frame_count                      GeneratorPortResults GeneratorFrameCount           _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_sig_frame_count                  GeneratorPortResults GeneratorSigFrameCount        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_octet_count                      GeneratorPortResults GeneratorOctetCount           _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_jumbo_frame_count                 GeneratorPortResults GeneratorJumboFrameCount     _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_total_mpls_frame_count                     GeneratorPortResults TotalMplsFrameCount           _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_mpls_frame_count                 GeneratorPortResults GeneratorMplsFrameCount       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_crc_error_frame_count            GeneratorPortResults GeneratorCrcErrorFrameCount   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_l3_checksum_error_count          GeneratorPortResults GeneratorL3ChecksumErrorCount _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_l4_checksum_error_count          GeneratorPortResults GeneratorL4ChecksumErrorCount _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_vlan_frame_count                 GeneratorPortResults GeneratorVlanFrameCount       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_l3_checksum_error_rate           GeneratorPortResults GeneratorL3ChecksumErrorRate  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_vlan_frame_rate                  GeneratorPortResults GeneratorVlanFrameRate        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_sig_frame_rate                   GeneratorPortResults GeneratorSigFrameRate         _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_rate                                      port                 GeneratorSigFrameRate         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_abort_frame_count                GeneratorPortResults GeneratorAbortFrameCount      _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_undersize_frame_count            GeneratorPortResults GeneratorUndersizeFrameCount  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_oversize_frame_count             GeneratorPortResults GeneratorOversizeFrameCount   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_total_frame_rate                           GeneratorPortResults TotalFrameRate                _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_frame_rate                       GeneratorPortResults GeneratorFrameRate            _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_total_octet_rate                           GeneratorPortResults TotalOctetRate                _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_octet_rate                       GeneratorPortResults GeneratorOctetRate            _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_jumbo_frame_rate                 GeneratorPortResults GeneratorJumboFrameRate       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_ipv4_frame_rate                  GeneratorPortResults GeneratorIpv4FrameRate        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_total_mpls_frame_rate                      GeneratorPortResults TotalMplsFrameRate            _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_ipv6_frame_rate                  GeneratorPortResults GeneratorIpv6FrameRate        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_mpls_frame_rate                  GeneratorPortResults GeneratorMplsFrameRate        _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_crc_error_frame_rate             GeneratorPortResults GeneratorCrcErrorFrameRate    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_l4_checksum_error_rate           GeneratorPortResults GeneratorL4ChecksumErrorRate  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_undersize_frame_rate             GeneratorPortResults GeneratorUndersizeFrameRate   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_oversize_frame_rate              GeneratorPortResults GeneratorOversizeFrameRate    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_generator_abort_frame_rate                 GeneratorPortResults GeneratorAbortFrameRate       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_hw_frame_count                             GeneratorPortResults HwFrameCount                  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_frame_count                            GeneratorPortResults    PfcFrameCount                    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_count                               GeneratorPortResults    PfcFrameCount                    _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri0_frame_count                       GeneratorPortResults PfcPri0FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri1_frame_count                       GeneratorPortResults PfcPri1FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri2_frame_count                       GeneratorPortResults PfcPri2FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri3_frame_count                       GeneratorPortResults PfcPri3FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri4_frame_count                       GeneratorPortResults PfcPri4FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri5_frame_count                       GeneratorPortResults PfcPri5FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri6_frame_count                       GeneratorPortResults PfcPri6FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {tx_pfc_pri7_frame_count                       GeneratorPortResults PfcPri7FrameCount             _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
  {    traffic_stats_aggregate_rxjoin_results
    {hname                          stcobj               stcattr                type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants  }
    {pkt_count                      port                 SigFrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_byte_count                 port                 TotalOctetCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_rate                       port                 SigFrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {pkt_bit_rate                   port                 TotalBitRate           _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {datagram_byte_count            _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {datagram_bit_rate              _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {line_bandwidth                 _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {substream_count                _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {substream_error_count          _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {filter_count                   _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkts                     port                 TotalFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {raw_pkt_count                  port                 TotalFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {total_pkt_bytes                port                 TotalOctetCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {good_pkts                      _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bytes                 _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bytes            _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkt_rate                 _none_               TotalFrameRate         _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {good_pkt_rate                  _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bit_rate              _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bit_rate         _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {line_rate_percentage           _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_pkts                       _none_               TcpFrameCount          _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {tcp_ratio                      _none_               _none_                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_checksum_errors            _none_               TcpChecksumErrorCount  _none_       _none_    _none_          _none_     true        _none_             false    _none_         _none_        _none_ }
    {udp_pkts                       _none_               UdpFrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {ip_pkts                        _none_               _none_                 _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv4_pkts                      _none_               Ipv4FrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {ipv6_pkts                      _none_               Ipv6FrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_frames                      AnalyzerPortResults  TotalFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_bytes                       AnalyzerPortResults  TotalOctetCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_fcs_error                   AnalyzerPortResults  FcsErrorFrameCount            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_runt_frames                 AnalyzerPortResults  UndersizeFrameCount    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_count                   AnalyzerPortResults  SigFrameCount               _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_min_frame_length            AnalyzerPortResults  MinFrameLength         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_max_frame_length            AnalyzerPortResults  MaxFrameLength         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_prbs_fill_byte_count        AnalyzerPortResults  PrbsFillOctetCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_jumbo_frame_count           AnalyzerPortResults  JumboFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pause_frame_count           AnalyzerPortResults  PauseFrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv6_over_ipv4_frame_count  AnalyzerPortResults  Ipv6OverIpv4FrameCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_icmp_frame_count            AnalyzerPortResults  IcmpFrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_vlan_frame_count            AnalyzerPortResults  VlanFrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_mpls_frame_count            AnalyzerPortResults  MplsFrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv4_CheckSum_error_count   AnalyzerPortResults  Ipv4ChecksumErrorCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_tcp_CheckSum_error_count    AnalyzerPortResults  TcpChecksumErrorCount  _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_udp_xsum_error_count        AnalyzerPortResults  UdpChecksumErrorCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_oversize_frame_count        AnalyzerPortResults  OversizeFrameCount     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_prbsbit_error_count         AnalyzerPortResults  PrbsBitErrorCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger8_count              AnalyzerPortResults  Trigger8Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger1_count              AnalyzerPortResults  Trigger1Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger2_count              AnalyzerPortResults  Trigger2Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger3_count              AnalyzerPortResults  Trigger3Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger4_count              AnalyzerPortResults  Trigger4Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger5_count              AnalyzerPortResults  Trigger5Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger6_count              AnalyzerPortResults  Trigger6Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger7_count              AnalyzerPortResults  Trigger7Count          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_combo_trigger_count         AnalyzerPortResults  ComboTriggerCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_frame_rate                  AnalyzerPortResults  TotalFrameRate              _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_byte_rate                   AnalyzerPortResults  TotalOctetRate               _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_rate                    AnalyzerPortResults  SigFrameRate                _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_prbs_fill_byte_rate         AnalyzerPortResults  PrbsFillOctetRate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_jumbo_frame_rate            AnalyzerPortResults  JumboFrameRate         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pause_frame_rate            AnalyzerPortResults  PauseFrameRate         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv4_frame_rate             AnalyzerPortResults  Ipv4FrameRate          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv6_frame_rate             AnalyzerPortResults  Ipv6FrameRate          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv6_over_ipv4_frame_rate   AnalyzerPortResults  Ipv6OverIpv4FrameRate  _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_udp_frame_rate              AnalyzerPortResults  UdpFrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_icmp_frame_rate             AnalyzerPortResults  IcmpFrameRate          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_vlan_frame_rate             AnalyzerPortResults  VlanFrameRate          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_mpls_frame_rate             AnalyzerPortResults  MplsFrameRate          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_fcs_error_rate              AnalyzerPortResults  FcsErrorFrameRate             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_ipv4_xsum_err_rate         AnalyzerPortResults  Ipv4ChecksumErrorRate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_udp_CheckSum_err_rate       AnalyzerPortResults  UdpChecksumErrorRate   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_undersize_frame_rate        AnalyzerPortResults  UndersizeFrameRate     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_oversize_frame_rate         AnalyzerPortResults  OversizeFrameRate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_prbs_bit_rate               AnalyzerPortResults  PrbsBitErrorRate         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger8_rate               AnalyzerPortResults  Trigger8Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger1_rate               AnalyzerPortResults  Trigger1Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger2_rate               AnalyzerPortResults  Trigger2Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger3_rate               AnalyzerPortResults  Trigger3Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger4_rate               AnalyzerPortResults  Trigger4Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger5_rate               AnalyzerPortResults  Trigger5Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger6_rate               AnalyzerPortResults  Trigger6Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_trigger7_rate               AnalyzerPortResults  Trigger7Rate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_combo_trigger_rate          AnalyzerPortResults  ComboTriggerRate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_frame_count             AnalyzerPortResults  PfcFrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_fcoe_frame_count            AnalyzerPortResults  FcoeFrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_frame_rate                 AnalyzerPortResults  PfcFrameRate            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_fcoe_frame_rate             AnalyzerPortResults  FcoeFrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {fcoe_frame_rate                AnalyzerPortResults  FcoeFrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {fcoe_frame_count               AnalyzerPortResults  FcoeFrameCount         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_rate                 AnalyzerPortResults  PfcFrameRate            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pfc_frame_count                AnalyzerPortResults  PfcFrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_hw_frame_count              AnalyzerPortResults  PfcFrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri0_frame_count        AnalyzerPortResults  PfcPri0FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri1_frame_count        AnalyzerPortResults  PfcPri1FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri2_frame_count        AnalyzerPortResults  PfcPri2FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri3_frame_count        AnalyzerPortResults  PfcPri3FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri4_frame_count        AnalyzerPortResults  PfcPri4FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri5_frame_count        AnalyzerPortResults  PfcPri5FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri6_frame_count        AnalyzerPortResults  PfcPri6FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_pfc_pri7_frame_count        AnalyzerPortResults  PfcPri7FrameCount      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {vlan_pkts_count        _none_     VlanFrameCount     _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {vlan_pkts_rate        _none_     VlanFrameRate       _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {oversize_count        _none_     OversizeFrameCount  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {oversize_rate         _none_     OversizeFrameRate   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {undersize_count       _none_   UndersizeFrameCount   _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {undersize_rate        _none_     UndersizeFrameRate  _none_    _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
 {    traffic_stats_out_of_filter_results
    {hname                    stcobj     stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {ipv6_present             port       _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_present             _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_present              _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {udp_present              _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {maxtag_present           _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkts               _none_     FrameCount            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {total_pkt_bytes          _none_     OctetCount           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {total_pkt_rate           _none_     FrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {total_pkt_bit_rate       _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkts                _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bytes           _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_rate            _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_pkt_bit_rate        _none_     BitRate             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bytes      _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {good_datagram_bit_rate   _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {line_rate_percentage     _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {physical_crc_errors      _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {bad_encapsulation_errors _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {bad_encapsulation_ratio  _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {avg_pkt_length           _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {min_pkt_length           _none_     MinFrameLength            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {max_pkt_length           _none_     MaxFrameLength            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {mtu_errors               _none_     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
  }
  {    traffic_stats_stream_tx_results
    {hname                     stcobj              stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {ipv6_present             txstreamresults     hlt              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_present             txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_present              txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {udp_present              txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv6_outer_present       txstreamresults     hlt              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_outer_present       txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {elapsed_time              txstreamresults    hlt           _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_}
    {encap                     txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkts                txstreamresults     FrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bytes           txstreamresults     OctetCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkts                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bytes            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bytes       txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate            txstreamresults     FrameRate         _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bit_rate        txstreamresults     BitRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkt_rate             txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bit_rate         txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bit_rate    txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_rate_percentage      txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {phy_crc_errors            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {bad_encaps_errors         txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {bad_encaps_ratio          txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {mtu_errors                txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {ip_checksum_errors        txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {avg_pkt_length            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {min_pkt_length            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {max_pkt_length            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {avg_delay                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {min_delay                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {max_delay                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {lost_pkts                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {misinserted_pkts          txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {out_of_sequence_pkts      txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {lost_pkt_ratio            txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {misinserted_pkt_rate      txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {out_of_sequence_pkt_ratio txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {prbs_bit_error_rate       txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {prbs_bit_errors           txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {test_block_errors         txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkts                 txstreamresults     _none_            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
  }
 {    traffic_stats_stream_rx_results
    {hname                     stcobj                       stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {ipv6_present              rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_present              rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_present               rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {udp_present               rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv6_outer_present        rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_outer_present        rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {elapsed_time              rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {encap                     rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {duplicate_pkts            rxstreamsummaryresults     DuplicateFrameCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {dropped_pkts              rxstreamsummaryresults     DroppedFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {dropped_pkts_percent      rxstreamsummaryresults     DroppedFramePercent _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts                rxstreamsummaryresults     FrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bytes           rxstreamsummaryresults     OctetCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkts                 rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bytes            rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bytes       rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate            rxstreamsummaryresults     FrameRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bit_rate        rxstreamsummaryresults     BitRate             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {good_pkt_rate             rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkt_bit_rate         rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_datagram_bit_rate    rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {line_rate_percentage      rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {phy_crc_errors            rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {bad_encaps_errors         rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {bad_encaps_ratio          rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {mtu_errors                rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {ip_checksum_errors        rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {avg_pkt_length            rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {min_pkt_length            rxstreamsummaryresults     MinFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {max_pkt_length            rxstreamsummaryresults     MaxFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {avg_delay                 rxstreamsummaryresults     AvgLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {min_delay                 rxstreamsummaryresults     MinLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {max_delay                 rxstreamsummaryresults     MaxLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {lost_pkts                 rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {misinserted_pkts          rxstreamsummaryresults     ReorderedFrameCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {out_of_sequence_pkts      rxstreamsummaryresults     OutSeqFrameCount    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {lost_pkt_ratio            rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {misinserted_pkt_rate      rxstreamsummaryresults     ReorderedFrameRate  _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {out_of_sequence_pkt_ratio rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {prbs_bit_error_rate       rxstreamsummaryresults     PrbsBitErrorRate    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {prbs_bit_errors           rxstreamsummaryresults     PrbsBitErrorCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {test_block_errors         rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {good_pkts                 rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {lost_pkt_ratio            rxstreamsummaryresults     _none_              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_}
    {out_of_pkt_frame_rate     rxstreamsummaryresults     OutSeqFrameRate     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {first_tstamp              rxstreamsummaryresults     FirstArrivalTime    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {last_tstamp               rxstreamsummaryresults     LastArrivalTime     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {Max                       rxstreamsummaryresults     MaxFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {Min                       rxstreamsummaryresults     MinFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts                rxstreamsummaryresults     FrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_byte_rate             rxstreamsummaryresults     OctetRate           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_port                   rxstreamsummaryresults     RxPort              _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts1                rxstreamsummaryresults     HistBin1Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts2                rxstreamsummaryresults     HistBin2Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts3                rxstreamsummaryresults     HistBin3Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts4                rxstreamsummaryresults     HistBin4Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts5                rxstreamsummaryresults     HistBin5Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts6                rxstreamsummaryresults     HistBin6Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts7                rxstreamsummaryresults     HistBin7Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts8                rxstreamsummaryresults     HistBin8Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts9                rxstreamsummaryresults     HistBin9Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts10                rxstreamsummaryresults     HistBin10Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts11                rxstreamsummaryresults     HistBin11Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts12                rxstreamsummaryresults     HistBin12Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts13                rxstreamsummaryresults     HistBin13Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts14                rxstreamsummaryresults     HistBin14Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts15                rxstreamsummaryresults     HistBin15Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate1             rxstreamsummaryresults     HistBin1Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate2             rxstreamsummaryresults     HistBin2Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate3             rxstreamsummaryresults     HistBin3Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate4             rxstreamsummaryresults     HistBin4Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate5             rxstreamsummaryresults     HistBin5Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate6             rxstreamsummaryresults     HistBin6Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate7             rxstreamsummaryresults     HistBin7Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate8             rxstreamsummaryresults     HistBin8Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate9             rxstreamsummaryresults     HistBin9Rate       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate10            rxstreamsummaryresults     HistBin10Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate11            rxstreamsummaryresults     HistBin11Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate12            rxstreamsummaryresults     HistBin12Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate13            rxstreamsummaryresults     HistBin13Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate14            rxstreamsummaryresults     HistBin14Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {pkt_frame_rate15            rxstreamsummaryresults     HistBin15Rate      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_port                    rxstreamsummaryresults    RxPort             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_count               rxstreamsummaryresults    SigFrameCount             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_rate                rxstreamsummaryresults    SigFrameRate             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
  {    traffic_stats_streameot_rx_results
    {hname                     stcobj                       stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {ipv6_present              rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_present              rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_present               rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {udp_present               rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv6_outer_present        rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_outer_present        rxstreamsummaryresults     hlt                 _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkts                rxstreamsummaryresults     FrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {dropped_pkts              rxstreamsummaryresults     DroppedFrameCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {dropped_pkts_percent      rxstreamsummaryresults     DroppedFramePercent _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {duplicate_pkts            rxstreamsummaryresults     DuplicateFrameCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_       _none_}
    {total_pkt_bytes           rxstreamsummaryresults     OctetCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {min_pkt_length            rxstreamsummaryresults     MinFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {max_pkt_length            rxstreamsummaryresults     MaxFrameLength      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {avg_delay                 rxstreamsummaryresults     AvgLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {min_delay                 rxstreamsummaryresults     MinLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {max_delay                 rxstreamsummaryresults     MaxLatency          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {misinserted_pkts          rxstreamsummaryresults     ReorderedFrameCount _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {out_of_sequence_pkts      rxstreamsummaryresults     OutSeqFrameCount    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {prbs_bit_errors           rxstreamsummaryresults     PrbsBitErrorCount   _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {first_tstamp              rxstreamsummaryresults     FirstArrivalTime    _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {last_tstamp               rxstreamsummaryresults     LastArrivalTime     _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts                rxstreamsummaryresults     FrameCount          _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts1                rxstreamsummaryresults     HistBin1Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts2                rxstreamsummaryresults     HistBin2Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts3                rxstreamsummaryresults     HistBin3Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts4                rxstreamsummaryresults     HistBin4Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts5                rxstreamsummaryresults     HistBin5Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts6                rxstreamsummaryresults     HistBin6Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts7                rxstreamsummaryresults     HistBin7Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts8                rxstreamsummaryresults     HistBin8Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts9                rxstreamsummaryresults     HistBin9Count       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts10                rxstreamsummaryresults     HistBin10Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts11                rxstreamsummaryresults     HistBin11Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts12                rxstreamsummaryresults     HistBin12Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts13                rxstreamsummaryresults     HistBin13Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts14                rxstreamsummaryresults     HistBin14Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkts15                rxstreamsummaryresults     HistBin15Count      _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate               rxstreamsummaryresults      _none_            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bit_rate           rxstreamsummaryresults      _none_            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_port                      rxstreamsummaryresults     PortName           _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_count               rxstreamsummaryresults      SigFrameCount       _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {rx_sig_rate                rxstreamsummaryresults      _none_              _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
 }
  {    traffic_stats_streameot_tx_results
    {hname                     stcobj              stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {ipv6_present             txstreamresults     hlt              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_present             txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {tcp_present              txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {udp_present              txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv6_outer_present       txstreamresults     hlt              _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv4_outer_present       txstreamresults     hlt            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_pkts                txstreamresults     FrameCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bytes           txstreamresults     OctetCount        _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_rate            txstreamresults      _none_             _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {total_pkt_bit_rate         txstreamresults     _none_            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
    {elapsed_time              txstreamresults      hlt            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_}
  }
  
  { traffic_stats_diffserv_results
    {hname                    stcobj     stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {qos_binary         diffservresults     QosBinary            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {ip_precedence     diffservresults      IpPrecedence            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {Ecn                diffservresults    Ecn            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {diffserv         diffservresults     DiffServ            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {ipv4_pkts         diffservresults     Ipv4FrameCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {ipv6_pkts         diffservresults     Ipv6FrameCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {rx_ipv4_frame_rate         diffservresults     Ipv4FrameRate            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {rx_ipv6_frame_rate         diffservresults     Ipv6FrameRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
  }
  
 { traffic_stats_userdefined_results
    {hname                    stcobj     stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {user_defined_frame_count1         AnalyzerPortResults     UserDefinedFrameCount1            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate1     AnalyzerPortResults      UserDefinedFrameRate1            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_count2                AnalyzerPortResults    UserDefinedFrameCount2            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate2         AnalyzerPortResults     UserDefinedFrameRate2            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_count3         AnalyzerPortResults     UserDefinedFrameCount3            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate3         AnalyzerPortResults     UserDefinedFrameRate3          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_count4         AnalyzerPortResults     UserDefinedFrameCount4            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate4         AnalyzerPortResults     UserDefinedFrameRate4          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_count5         AnalyzerPortResults     UserDefinedFrameCount5            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate5         AnalyzerPortResults     UserDefinedFrameRate5          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_count6         AnalyzerPortResults     UserDefinedFrameCount6            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {user_defined_frame_rate6         AnalyzerPortResults     UserDefinedFrameRate6          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
  }
  
   { traffic_stats_fc_port_results
    {hname                    stcobj     stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants    }
    {b2b_tx_credit_count         FcResults     B2BTxCreditCount            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {b2b_tx_credit_na_count      FcResults    B2BTxCreditUnavailableCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class2_tx_frame_count        FcResults     Class2TxFrameCount            _none_       _none_    _none_          _none_     true         _none_             false    _none_         _none_        _none_ }
    {class2_rx_frame_count         FcResults     Class2RxFrameCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class3_tx_frame_count         FcResults     Class3TxFrameCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class3_rx_frame_count         FcResults     Class3RxFrameCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {othercls_tx_frame_count         FcResults     OtherClassTxFrameCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {othercls_rx_frame_count         FcResults     OtherClassRxFrameCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class2_tx_frame_rate         FcResults     Class2TxFrameRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class2_rx_frame_rate         FcResults     Class2RxFrameRate            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class3_tx_frame_rate         FcResults     Class3TxFrameRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {class3_rx_frame_rate         FcResults     Class3RxFrameRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {othercls_tx_frame_rate         FcResults     OtherClassTxFrameRate            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {othercls_rx_frame_rate         FcResults     OtherClassRxFrameRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls2_tx_byte_count         FcResults     TotalClass2TxByteCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls2_rx_byte_count         FcResults     TotalClass2RxByteCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls3_tx_byte_count         FcResults     TotalClass3TxByteCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls3_rx_byte_count         FcResults     TotalClass3RxByteCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_othercls_tx_byte_count         FcResults     TotalOtherClassTxByteCount            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_othercls_rx_byte_count         FcResults     TotalOtherClassRxByteCount          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls2_tx_byte_rate         FcResults     TotalClass2TxByteRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls2_rx_byte_rate         FcResults     TotalClass2RxByteRate            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls3_tx_byte_rate         FcResults     TotalClass3TxByteRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_cls3_rx_byte_rate         FcResults     TotalClass3RxByteRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_othercls_tx_byte_rate         FcResults     TotalOtherClassTxByteRate            _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {total_othercls_rx_byte_rate         FcResults     TotalOtherClassRxByteRate          _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
  }
 { traffic_stats_system_monitor_results
    {hname                    stcobj            stcattr            type        priority   default         range       supported    dependency      mandatory procfunc         mode     constants   }
    {cpu_percent         SystemMonitorResults   CpuPercent         _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {daemon_name         SystemMonitorResults   DaemonName         _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {memory              SystemMonitorResults   Memory             _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
    {memory_percent      SystemMonitorResults   MemoryPercent      _none_       _none_    _none_          _none_     true          _none_             false    _none_         _none_        _none_ }
    {port_group_name     SystemMonitorResults   PortGroupName      _none_       _none_    _none_          _none_     false         _none_             false    _none_         _none_        _none_ }
  }
}
