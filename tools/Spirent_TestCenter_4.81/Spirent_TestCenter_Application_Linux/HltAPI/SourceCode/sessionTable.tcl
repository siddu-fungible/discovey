# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Session:: {
    
}
set ::sth::Session::sessionTable {
 ::sth::Session::
  {    labserver_connect
    {hname                  stcobj        stcattr      type        priority   default         range       supported    dependency mandatory     procfunc     mode       constants                        }
    {server_ip              _none_      _none_        IP            2          _none_          _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    {session_name           _none_      _none_        ANY           2          _none_          _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    {user_name              _none_      _none_        ANY           2          _none_          _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    {create_new_session     _none_      _none_        {CHOICES 1 0} 2          1               _none_      true         _none_        _none_    _none_      _none_     _none_                           }
    {keep_session           _none_      _none_        {CHOICES 1 0} 2          0               _none_      true         _none_        _none_    _none_      _none_     _none_                           }

  }
    {    labserver_disconnect
    {hname                  stcobj        stcattr      type        priority   default         range       supported    dependency mandatory     procfunc     mode       constants                        }
    {server_ip              _none_      _none_        IP            2          _none_          _none_      true         _none_        _none_    _none_      _none_     _none_                           }
    {session_name           _none_      _none_        ANY           2          _none_          _none_      true         _none_        _none_    _none_      _none_     _none_                           }
    {user_name              _none_      _none_        ANY           2          _none_          _none_      true         _none_        _none_    _none_      _none_     _none_                           }
    {terminate_session      _none_      _none_        {CHOICES 1 0} 2          1               _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    
  }
 {    connect
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory procfunc                           mode       constants                        }
    {device            _none_        hostname      ANY         2          _none_          _none_      true         _none_         true   ::sth::Session::processConnectDevice    _none_     _none_                           }
    {port_list         _none_        _none_        ANY         3          _none_          _none_      true         _none_         true   ::sth::Session::processConnectPort_list _none_     _none_                           }
    {username          _none_        UserId        ALPHANUM    4          _none_          _none_      true         _none_         false   _none_                            _none_     _none_                           }
    {timeout           _none_        _none_        NUMERIC     4          _none_          _none_      true         _none_         false  _none_                                 _none_     {0 0 1 1 3 3 10 10 30 30 100 100 300 300 1000 1000}    }
    {nobios            _none_         _none_       NUMERIC     4          _none_          _none_      false        _none_         false  ::sth::Session::processConnectNobios   _none_     {0 0 1 1}    }
    {sync              _none_        _none_        NUMERIC     4          _none_          _none_      true         _none_         false  _none_                                 _none_     {none _none_ 1 _none_ 3 _none_ 10 _none_ 30 _none_ 100 _none_ 300 _none_ 1000 _none_}    }
    {break_locks       _none_         _none_       NUMERIC     4          _none_          _none_      true         _none_         false  _none_                                 _none_     {0 0 1 1}    }
    {reset             _none_         _none_       FLAG        1          _none_          _none_      true         _none_         false  ::sth::Session::processConnectReset    _none_     _none_    }
    {offline           _none_         _none_       FLAG        1          _none_          _none_      true         _none_         false  _none_     _none_     _none_    }
    {scheduling_mode   _none_         _none_       ALPHANUM    2       RATE_BASED         _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_loadunit     _none_         _none_       ALPHANUM     2    PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {port_load         _none_         _none_       NUMERIC     2          10            _none_      true         _none_         false  _none_     _none_      _none_  }   

  } 
 {    interface_config_EthernetCopper
    {hname                  stcobj              stcattr            type                 priority        default         range     supported    dependency   mandatory           procfunc                                           mode       constants                        }
    {port_handle            _none_              _none_              ALPHANUM                1          _none_          _none_      true         _none_        true              _none_                                             _none_     _none_                           }
    {mode                   _none_              _none_              ALPHANUM                1          _none_          _none_      true         _none_        true              _none_                                             _none_     _none_                           }
    {intf_mode              EthernetCopper      _none_          {CHOICES ethernet}          2          _none_          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ethernet PORT_TYPE_ETH}         }
    {autonegotiation        EthernetCopper      AutoNegotiation {CHOICES 0 1}               3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 false 1 true}                           }
    {autonegotiation_role_enable EthernetCopper AutoNegotiationMasterSlaveEnable {CHOICES 0 1 true false}             3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 false 1 true}                           }
    {autonegotiation_role   EthernetCopper      AutoNegotiationMasterSlave {CHOICES slave master fault}               3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {slave SLAVE master MASTER fault FAULT}                           }
    {control_plane_mtu      EthernetCopper      Mtu                 NUMERIC                 3          1500          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }

    {create_host            _none_              _none_          {CHOICES true false}        3           true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_              _none_              NUMERIC                 3          _none_              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
	{block_mode             _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {dst_mac_addr           Ipv4If              GatewayMAC          ANY                     2          00:00:01:00:00:01          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }

    {duplex                 EthernetCopper      Duplex          {CHOICES full half}         3          full            _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {full FULL half HALF}             }
    {gateway                Ipv4If              Gateway             IP                      3          _none_      _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {gateway_step           Ipv4If              GatewayStep         IP                      3          _none_         _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {resolve_gateway_mac    Ipv4If              ResolveGatewayMac  {CHOICES true false}     3          true            _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}                           }
    {intf_ip_addr           Ipv4If              Address             IP                      3          _none_      _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {intf_ip_addr_step      Ipv4If              AddrStep            IP                      3          _none_         _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway           Ipv6If              Gateway             IPV6                    3          _none_             _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway_step      Ipv6If              GatewayStep         IPV6                    3          _none_      _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_resolve_gateway_mac Ipv6If           ResolveGatewayMac  {CHOICES true false}      3          _none_          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}                           }
    {ipv6_prefix_length     Ipv6If              PrefixLength        NUMERIC                 3          _none_         _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr         Ipv6If              Address             IPV6                    3          _none_         _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr_step    Ipv6If              AddrStep            IPV6                    3          _none_         _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {netmask                Ipv4If              AddrStepMask        IP                      3          255.255.255.255           _none_      true         _none_        false              ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {phy_mode               EthernetCopper      _none_          {CHOICES fiber copper}      3          _none_          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {speed                  EthernetCopper      LineSpeed {CHOICES ether10 ether100 ether1000 ether10000} 3 ether1000   _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ether10 SPEED_10M ether100 SPEED_100M ether1000 SPEED_1G ether10000 SPEED_10G}      }
    {vlan                   EthernetCopper      _none_          {CHOICES 0 1}               3          1               _none_      true         _none_        false            ::sth::Session::processConfigFwdCmd                _none_     {0 0 1 1}                        }
    {qinq_incr_mode         _none_              _none_       {CHOICES inner outer both}     3          both            _none_      true         _none_        false            _none_                                             _none_     _none_    }
    {vlan_id                VlanIf              VlanId              NUMERIC                 3          _none_          0-4095      true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_cfi               VlanIf              Cfi                 NUMERIC                 3          _none_          0-1         true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_id_count          _none_              _none_              NUMERIC                 3          _none_          1-4096      true         _none_        false            _none_                                             _none_     _none_    }
    {vlan_id_step           VlanIf              IdStep              NUMERIC                 3          _none_          0-4095      true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_user_priority     VlanIf              Priority            NUMERIC                 3          _none_          0-7         true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_cfi         VlanOuterIf         Cfi                 NUMERIC                 3          _none_          0-1         true         _none_        false            ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id          VlanOuterIf         VlanId              NUMERIC                 3          _none_          0-4095      true         _none_        false            ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id_step     VlanOuterIf         IdStep              NUMERIC                 3          _none_          0-4095      true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_id_count    _none_              _none_              NUMERIC                 3          _none_          1-4096      true         _none_        false            _none_                                           _none_     _none_    }
    {vlan_outer_user_priority VlanOuterIf       Priority            NUMERIC                 3          _none_          0-7         true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {src_mac_addr           ethiiif             SourceMac           ANY                     3          _none_         _none_       true         _none_        false            ::sth::Session::macAddressToStcFormat             _none_     _none_                           }
    {src_mac_addr_step      ethiiif             SrcMacStep          ANY                     3          00:00:00:00:00:01          _none_       true         _none_        false            ::sth::Session::macAddressToStcFormat             _none_     _none_                           }   
    {arp_req_timer          EthernetCopper      _none_              NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_req_retries        EthernetCopper      RetryCount          NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_send_req           EthernetCopper      _none_              NUMERIC                 3          1               _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_req_timeout        EthernetCopper      TimeOut             NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_cache_retrieve     _none_             _none_              NUMERIC                 3          0               _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {arpnd_report_retrieve  _none_             _none_              NUMERIC                 3          0               _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {arp_target             _none_              _none_  {CHOICES port device stream all}    3          port            _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {enable_ping_response   host              EnablePingResponse  {CHOICES 0 1}           3          0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_              _none_              ALPHANUM                2      _none_      _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
  }
  {    interface_config_Ethernet10GigCopper
    {hname                  stcobj              stcattr            type                 priority        default         range     supported    dependency   mandatory           procfunc                                           mode       constants                        }
    {port_handle            _none_              _none_              ALPHANUM                1          _none_          _none_      true         _none_        true              _none_                                             _none_     _none_                           }
    {mode                   _none_              _none_              ALPHANUM                1          _none_          _none_      true         _none_        true              _none_                                             _none_     _none_                           }
    {intf_mode              Ethernet10GigCopper _none_          {CHOICES ethernet}          2          _none_          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ethernet PORT_TYPE_ETH}         }
    {autonegotiation        Ethernet10GigCopper AutoNegotiation {CHOICES 0 1}               3          1               _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 false 1 true}                           }
    {autonegotiation_role_enable Ethernet10GigCopper AutoNegotiationMasterSlaveEnable {CHOICES 0 1 true false}             3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 FALSE 1 TRUE true TRUE false FALSE}                           }
    {autonegotiation_role   Ethernet10GigCopper      AutoNegotiationMasterSlave {CHOICES slave master fault}               3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {slave SLAVE master MASTER fault FAULT}                           }
    {control_plane_mtu      Ethernet10GigCopper Mtu                 NUMERIC                 3          1500            _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {create_host            _none_              _none_          {CHOICES true false}        3           true           _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_              _none_              NUMERIC                 3          _none_               _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {block_mode             _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
	{dst_mac_addr           Ipv4If              GatewayMAC          ANY                     2          00:00:01:00:00:01          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {duplex                 Ethernet10GigCopper Duplex          {CHOICES full half}         3          full          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {full FULL half HALF}             }
    {gateway                Ipv4If              Gateway             IP                      3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {gateway_step           Ipv4If              GatewayStep         IP                      3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {resolve_gateway_mac    Ipv4If              ResolveGatewayMac   {CHOICES true false}    3          true          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}                           }
    {intf_ip_addr           Ipv4If              Address             IP                      3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {intf_ip_addr_step      Ipv4If              AddrStep            IP                      3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway           Ipv6If              Gateway             IPV6                    3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway_step      Ipv6If              GatewayStep         IPV6                    3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_prefix_length     Ipv6If              PrefixLength        NUMERIC                 3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr         Ipv6If              Address             IPV6                    3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr_step    Ipv6If              AddrStep            IPV6                    3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_resolve_gateway_mac Ipv6If           ResolveGatewayMac   {CHOICES true false}     3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}                           }
    {netmask                Ipv4If              AddrStepMask        IP                      3          _none_        _none_      true         _none_        false              ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {phy_mode               Ethernet10GigCopper _none_          {CHOICES fiber copper}      3          _none_        _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {speed                  Ethernet10GigCopper LineSpeed {CHOICES ether10 ether100 ether1000 ether10000 ether5Gig ether2500}   3   ether10000  _none_     true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ether10 SPEED_10M ether100 SPEED_100M ether1000 SPEED_1G ether10000 SPEED_10G ether5Gig SPEED_5G ether2500 SPEED_2500M}      }
    {alternate_speeds       Ethernet10GigCopper AlternateSpeeds     ANY                     3          _none_          _none_     true         _none_        false             _none_                _none_     _none_ }
    {vlan                   Ethernet10GigCopper _none_          {CHOICES 0 1}               3          1          _none_      true         _none_        false            ::sth::Session::processConfigFwdCmd                _none_     {0 0 1 1}                        }
    {qinq_incr_mode         _none_              _none_       {CHOICES inner outer both}     3          both       _none_      true         _none_        false            _none_                                             _none_     _none_    }
    {vlan_id                VlanIf              VlanId              NUMERIC                 3          _none_     0-4095      true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_cfi               VlanIf              Cfi                 NUMERIC                 3          _none_     0-1         true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_id_count          _none_              _none_              NUMERIC                 3          _none_     1-4096      true         _none_        false            _none_                                             _none_     _none_    }
    {vlan_id_step           VlanIf              IdStep              NUMERIC                 3          _none_     0-4095      true         _none_        false            ::sth::Session::processConfigCmd                   _none_     _none_    }
    {vlan_user_priority     VlanIf              Priority            NUMERIC                 3          _none_     0-7         true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_cfi         VlanOuterIf         Cfi                 NUMERIC                 3          _none_     0-1         true         _none_        false            ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id          VlanOuterIf         VlanId              NUMERIC                 3          _none_     0-4095      true         _none_        false            ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id_step     VlanOuterIf         IdStep              NUMERIC                 3          _none_     0-4095      true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_id_count    _none_              _none_              NUMERIC                 3          _none_     1-4096      true         _none_        false            _none_                                           _none_     _none_    }
    {vlan_outer_user_priority VlanOuterIf       Priority            NUMERIC                 3          _none_     0-7         true         _none_        false            ::sth::Session::processConfigCmd                 _none_     _none_    }
    {src_mac_addr           ethiiif             SourceMac           ANY                     3          _none_     _none_      true         _none_        false            ::sth::Session::macAddressToStcFormat             _none_     _none_                           }
    {src_mac_addr_step      ethiiif             SrcMacStep          ANY                     3          _none_          _none_       true         _none_        false            ::sth::Session::macAddressToStcFormat             _none_     _none_                           }   
    {arp_req_timer          Ethernet10GigCopper _none_              NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_req_retries        Ethernet10GigCopper RetryCount          NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_send_req           Ethernet10GigCopper _none_              NUMERIC                 3          1               _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_req_timeout        Ethernet10GigCopper TimeOut             NUMERIC                 3          _none_          _none_       true         _none_        false            ::sth::Session::processConfigArpCmd               _none_     _none_                           }
    {arp_cache_retrieve     _none_             _none_               NUMERIC                 3          0               _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {arpnd_report_retrieve  _none_             _none_               NUMERIC                 3          0               _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {arp_target             _none_              _none_  {CHOICES port device stream all}    3          port            _none_       true         _none_        false            _none_                                            _none_     _none_                           }
    {enable_ping_response   host              EnablePingResponse  {CHOICES 0 1}             3          0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {pfc_negotiate_by_dcbx  Ethernet10GigCopper      IsPfcNegotiated   {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority0              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority1              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority2              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority3              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority4              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority5              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority6              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority7              Ethernet10GigCopper      _none_            {CHOICES 0 1}        5          0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {scheduling_mode        _none_              _none_              ALPHANUM                2          _none_          _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {pfc_priority_enable     PfcMeasurementConfig    PriorityEnable       MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_priority_pause_quanta    PfcMeasurementConfig    Time            MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_send_xon            PfcMeasurementConfig    EnableXon            {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_xon_delay           PfcMeasurementConfig    XonDelay             NUMERIC                                    5       1              1-3273000    true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_}
    {pfc_xon_delay_unit      PfcMeasurementConfig    XonDelayUnit         {CHOICES pause_quanta microseconds}        5    pause_quanta       _none_      true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_  }
    {pfc_auto_trigger        PfcMeasurementConfig    AutoTrigger          {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
}
  {    interface_config_EthernetFiber
    {hname                  stcobj              stcattr            type                 priority        default         range       supported    dependency mandatory           procfunc                                           mode       constants                        }
    {port_handle            _none_              _none_              ALPHANUM                1          _none_          _none_       true         _none_        true              _none_                                             _none_     _none_                           }
    {mode                   _none_              _none_              ALPHANUM                1          _none_          _none_       true         _none_        true              _none_                                             _none_     _none_                           }
    {intf_mode              _none_              _none_      {CHOICES ethernet}              2          _none_          _none_       true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ethernet PORT_TYPE_ETH}         }
    {autonegotiation        EthernetFiber       AutoNegotiation {CHOICES 0 1}               3          1          _none_       true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 false 1 true}                           }
    {autonegotiation_role_enable EthernetFiber AutoNegotiationMasterSlaveEnable {CHOICES 0 1 true false}             3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 false 1 true}                           }
    {autonegotiation_role   EthernetFiber      AutoNegotiationMasterSlave {CHOICES slave master fault}               3          1          _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {slave SLAVE master MASTER fault FAULT}                           }
    {control_plane_mtu      EthernetFiber       Mtu                 NUMERIC                 3          1500          _none_       true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {create_host            _none_              _none_          {CHOICES true false}        3           true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_              _none_              NUMERIC                 3          _none_              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {block_mode             _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
	{phy_mode               EthernetFiber       _none_      {CHOICES fiber copper}          3          _none_          _none_       true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {speed                  EthernetFiber       LineSpeed {CHOICES ether10 ether100 ether1000 ether10000}   3   ether1000  _none_      true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {ether10 SPEED_10M ether100 SPEED_100M ether1000 SPEED_1G ether10000 SPEED_10G}      }
    {vlan                   EthernetFiber      _none_          {CHOICES 0 1}               3          1               _none_       true         _none_        false             ::sth::Session::processConfigFwdCmd                _none_     {0 0 1 1}                        }
    {qinq_incr_mode         _none_              _none_    {CHOICES inner outer both}        3          both            _none_       true         _none_        false              _none_                                            _none_     _none_    }
    {vlan_id                VlanIf              VlanId              NUMERIC                 3          _none_           0-4095      true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_cfi               VlanIf              Cfi                 NUMERIC                 3          _none_       0-1         true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_id_count          _none_              _none_              NUMERIC                 3          _none_           1-4096      true         _none_        false              _none_                                            _none_     _none_    }
    {vlan_id_step           VlanIf              IdStep              NUMERIC                 3          _none_      0-4095      true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_user_priority     VlanIf              Priority            NUMERIC                 3          _none_      0-7         true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_cfi         VlanOuterIf         Cfi                 NUMERIC                 3          _none_      0-1         true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id          VlanOuterIf         VlanId              NUMERIC                 3          _none_        0-4095      true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id_step     VlanOuterIf         IdStep              NUMERIC                 3          _none_      0-4095      true         _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {vlan_outer_id_count    _none_              _none_              NUMERIC                 3          _none_           1-4096      true         _none_        false              _none_                                            _none_     _none_    }
    {vlan_outer_user_priority VlanOuterIf       Priority            NUMERIC                 3          _none_      0-7        true          _none_        false              ::sth::Session::processConfigCmd                  _none_     _none_    }
    {flow_control           EthernetFiber       FlowControl         ALPHANUM                3          false          _none_      true          _none_        false              ::sth::Session::processConfigFwdCmd               _none_     {true TRUE TRUE TRUE false FALSE FALSE FALSE}      }
    {data_path_mode         EthernetFiber       DataPathMode        {CHOICES normal local_loopback} 3  normal          _none_      true          _none_        false              ::sth::Session::processConfigFwdCmd               _none_     {normal NORMAL local_loopback LOCAL_LOOPBACK}      }
    {gateway                Ipv4If              Gateway             IP                      3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                 _none_     _none_                           }
    {gateway_step           Ipv4If              GatewayStep         IP                      3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                 _none_     _none_                           }
    {resolve_gateway_mac    Ipv4If              ResolveGatewayMac   {CHOICES true false}    3          true          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}  }
    {duplex                 EthernetFiber       _none_          {CHOICES full half}         3          full          _none_      true         _none_        false                _none_                                           _none_     {full FULL half HALF}             }
    {src_mac_addr           ethiiif             SourceMac           ANY                     3          _none_                     _none_      true         _none_        false                ::sth::Session::macAddressToStcFormat              _none_     _none_                           }
    {src_mac_addr_step      ethiiif             SrcMacStep          ANY                     3          _none_          _none_      true         _none_        false                ::sth::Session::macAddressToStcFormat              _none_     _none_                           }   
    {dst_mac_addr           Ipv4If              GatewayMAC          ANY                     2          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {intf_ip_addr           Ipv4If              Address             IP                      3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {intf_ip_addr_step      Ipv4If              AddrStep            IP                      3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway           Ipv6If              Gateway             IPV6                    3          _none_       _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway_step      Ipv6If              GatewayStep         IPV6                    3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_resolve_gateway_mac  Ipv6If           ResolveGatewayMac   {CHOICES true false}    3          _none_          _none_      true         _none_        false             ::sth::Session::processConfigCmd     _none_     {true TRUE false FALSE}   }
    {ipv6_prefix_length     Ipv6If              PrefixLength        NUMERIC                 3          _none_      _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr         Ipv6If              Address             IPV6                    3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr_step    Ipv6If              AddrStep            IPV6                    3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {netmask                Ipv4If              AddrStepMask        IP                      3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                     _none_     _none_                           }
    {arp_req_timer          EthernetFiber       _none_              NUMERIC                 3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigArpCmd                   _none_     _none_                           }
    {arp_req_retries        EthernetFiber       RetryCount          NUMERIC                 3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigArpCmd                   _none_     _none_                           }
    {arp_send_req           EthernetFiber       _none_              NUMERIC                 3          1               _none_      true         _none_        false                ::sth::Session::processConfigArpCmd                   _none_     _none_                           }
    {arp_req_timeout        EthernetFiber       TimeOut             NUMERIC                 3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigArpCmd                   _none_     _none_                           }
    {arp_cache_retrieve     _none_              _none_             NUMERIC                  3          0               _none_      true         _none_        false                _none_                                               _none_     _none_                           }
    {arpnd_report_retrieve  _none_              _none_             NUMERIC                  3          0               _none_      true         _none_        false                _none_                                               _none_     _none_                           }
    {arp_target             _none_              _none_  {CHOICES port device stream all}    3          port            _none_      true         _none_        false                _none_                                               _none_     _none_                           }
    {enable_ping_response   host              EnablePingResponse  {CHOICES 0 1}           3          0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_              _none_              ALPHANUM                2      _none_      _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
}
  {    interface_config_Ethernet10GigFiber
    {hname                      stcobj                  stcattr             type        priority        default         range       supported    dependency mandatory            procfunc                                           mode       constants                        }
    {port_handle                _none_                  _none_              ALPHANUM        1          _none_          _none_       true         _none_        true               _none_                                            _none_     _none_                           }
    {mode                       _none_                  _none_              ALPHANUM        1          _none_          _none_       true         _none_        true               _none_                                            _none_     _none_                           }
    {intf_mode                  _none_                  _none_      {CHOICES ethernet}      2          _none_          _none_       true        _none_        false              _none_                                            _none_     {ethernet PORT_TYPE_ETH}         }
    {autonegotiation            Ethernet10GigFiber      AutoNegotiation     {CHOICES 0 1}   3          1          _none_       true        _none_        false              ::sth::Session::processConfigFwdCmd               _none_     {0 false 1 true}                           }
    {speed                      Ethernet10GigFiber      LineSpeed   {CHOICES ether10 ether100 ether1000 ether10000}     3   ether10000  _none_ true  _none_        false              ::sth::Session::processConfigFwdCmd               _none_     {ether10 SPEED_10M ether100 SPEED_100M ether1000 SPEED_1G ether10000 SPEED_10G}      }
    {vlan                       Ethernet10GigFiber      _none_          {CHOICES 0 1}       3          1                _none_      true         _none_        false               ::sth::Session::processConfigFwdCmd              _none_     {0 0 1 1}                        }
    {control_plane_mtu          Ethernet10GigFiber      Mtu                 NUMERIC                 3          1500          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {create_host                _none_                  _none_          {CHOICES true false}        3          true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                      _none_                  _none_              NUMERIC                 3          _none_        _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                     _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {block_mode                 _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
	{data_path_mode             Ethernet10GigFiber      DataPathMode    {CHOICES normal local_loopback} 3  normal       _none_      true         _none_        false              ::sth::Session::processConfigFwdCmd               _none_     {normal NORMAL local_loopback LOCAL_LOOPBACK} }
    {qinq_incr_mode             _none_                  _none_   {CHOICES inner outer both} 3           both            _none_      true         _none_        false               _none_                                           _none_     _none_    }
    {vlan_id                    VlanIf                  VlanId              NUMERIC         3          _none_         0-4095      true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_cfi                   VlanIf                  Cfi                 NUMERIC         3          _none_      0-1         true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_id_count              _none_                  _none_              NUMERIC         3          _none_           1-4096      true         _none_        false               _none_                                           _none_     _none_    }
    {vlan_id_step               VlanIf                  IdStep              NUMERIC         3          _none_      0-4095      true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_user_priority         VlanIf                  Priority            NUMERIC         3          _none_      0-7         true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_cfi             VlanOuterIf             Cfi                 NUMERIC         3          _none_      0-1        true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_id              VlanOuterIf             VlanId              NUMERIC         3          _none_        0-4095     true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_id_step         VlanOuterIf             IdStep              NUMERIC         3          _none_      0-4095      true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {vlan_outer_id_count        _none_                  _none_              NUMERIC         3          _none_           1-4096      true         _none_        false               _none_                                           _none_     _none_    }
    {vlan_outer_user_priority   VlanOuterIf             Priority            NUMERIC         3          _none_      0-7         true         _none_        false               ::sth::Session::processConfigCmd                 _none_     _none_    }
    {phy_mode                   Ethernet10GigFiber      _none_      {CHOICES fiber copper}  3          fiber          _none_       true         _none_        false               ::sth::Session::processConfigFwdCmd              _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {transmit_clock_source      Ethernet10GigFiber      TransmitClockSource ALPHANUM        3          INTERNAL          _none_       true        _none_         false               ::sth::Session::processConfigFwdCmd              _none_     {INTERNAL INTERNAL BITS BITS LOOP LOOP EXTERNAL EXTERNAL}      }
    {port_mode                  Ethernet10GigFiber      PortMode            ALPHANUM        3          LAN          _none_      true         _none_         false            ::sth::Session::processConfigFwdCmd              _none_     {LAN LAN WAN WAN}      }
    {deficit_idle_count         Ethernet10GigFiber      DeficitIdleCount    ALPHANUM        3          false          _none_      true        _none_          false               ::sth::Session::processConfigFwdCmd              _none_     {true TRUE TRUE TRUE false FALSE FALSE FALSE}      }
    {flow_control               Ethernet10GigFiber      FlowControl         ALPHANUM        3          false          _none_      true        _none_          false               ::sth::Session::processConfigFwdCmd              _none_     {true TRUE TRUE TRUE false FALSE FALSE FALSE}      }
    {gateway                    Ipv4If                  Gateway             IP              3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {gateway_step               Ipv4If                  GatewayStep         IP              3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {resolve_gateway_mac        Ipv4If              ResolveGatewayMac   {CHOICES true false} 3          true          _none_      true         _none_        false             ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}      }
    {src_mac_addr               ethiiif                 SourceMac           ANY             3          _none_                     _none_      true         _none_        false                ::sth::Session::macAddressToStcFormat              _none_     _none_                           }
    {src_mac_addr_step          ethiiif                 SrcMacStep          ANY             3          _none_          _none_      true         _none_        false                ::sth::Session::macAddressToStcFormat              _none_     _none_                           }   
    {dst_mac_addr               Ipv4If                  GatewayMAC          ANY             2          _none_          _none_      true        _none_         false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {duplex                     Ethernet10GigFiber      Duplex      {CHOICES full half}     3          full          _none_      true         _none_        false                 ::sth::Session::processConfigCmd                                            _none_     {full FULL half HALF}             }
    {intf_ip_addr               Ipv4If                  Address             IP              3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {intf_ip_addr_step          Ipv4If                  AddrStep            IP              3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway               Ipv6If                  Gateway             IPV6            3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_gateway_step          Ipv6If                  GatewayStep         IPV6            3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_resolve_gateway_mac   Ipv6If           ResolveGatewayMac          {CHOICES true false} 3     _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     {true TRUE false FALSE}       }
    {ipv6_prefix_length         Ipv6If                  PrefixLength        NUMERIC         3          _none_      _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr             Ipv6If                  Address             IPV6            3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {ipv6_intf_addr_step        Ipv6If                  AddrStep            IPV6            3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {netmask                    Ipv4If                  AddrStepMask        IP              3          _none_          _none_      true         _none_        false                ::sth::Session::processConfigCmd                   _none_     _none_                           }
    {framing                    EthernetWan             FramingMode         ALPHANUM        3          SONET_FRAMING          _none_      true        _none_        false                 ::sth::Session::processConfigFwdCmd                _none_     {SONET SONET_FRAMING sonet SONET_FRAMING SDH SDH_FRAMING sdh SDH_FRAMING}                           }
    {scramble                   EthernetWan             SectionScramble     ALPHANUM        3          _none_          _none_      true        _none_        false                 ::sth::Session::processConfigFwdCmd                _none_     {true TRUE TRUE TRUE false FALSE FALSE FALSE}                           }
    {path_signal_label          EthernetWan             PathSignalLabel     ALPHANUM        3          HDLC_PATH_SIGNAL_LABEL          _none_      true        _none_        false                 ::sth::Session::processConfigFwdCmd                _none_     {HDLC HDLC_PATH_SIGNAL_LABEL PPP PPP_PATH_SIGNAL_LABEL ATM ATM_PATH_SIGNAL_LABEL ETHERNET_10G_WAN ETHERNET_10G_WAN_PATH_SIGNAL_LABEL}                           }
    {crc32                      EthernetWan             Crc32               ALPHANUM        3          false          _none_      true        _none_        false                 ::sth::Session::processConfigFwdCmd                _none_     {true TRUE TRUE TRUE false FALSE FALSE FALSE}                            }
    {arp_req_timer              Ethernet10GigFiber      _none_              NUMERIC         3          _none_          _none_      true        _none_        false                 ::sth::Session::processConfigArpCmd                _none_     _none_                           }
    {arp_req_retries            Ethernet10GigFiber      RetryCount          NUMERIC         3          _none_          _none_      true        _none_        false                 ::sth::Session::processConfigArpCmd                _none_     _none_                           }
    {arp_send_req               Ethernet10GigFiber      _none_              NUMERIC         3          1               _none_      true        _none_        false                 ::sth::Session::processConfigArpCmd                _none_     _none_                           }
    {arp_req_timeout            Ethernet10GigFiber      TimeOut             NUMERIC         3          _none_          _none_      true        _none_        false                 ::sth::Session::processConfigArpCmd                _none_     _none_                           }
    {arp_cache_retrieve         _none_                  _none_              NUMERIC         3          0               _none_      true        _none_        false                 _none_                                             _none_     _none_                           }
    {arpnd_report_retrieve      _none_                  _none_              NUMERIC         3          0               _none_      true         _none_        false                _none_                                             _none_     _none_                           }
    {arp_target                 _none_          _none_  {CHOICES port device stream all}    3          port            _none_      true        _none_        false                 _none_                                             _none_     _none_                           }
    {enable_ping_response       host              EnablePingResponse  {CHOICES 0 1}       3          0               _none_      true        _none_        false                 _none_                                             _none_     {1 TRUE 0 FALSE}}
    {pfc_negotiate_by_dcbx     Ethernet10GigFiber      IsPfcNegotiated      {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority0                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority1                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority2                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority3                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority4                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority5                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority6                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority7                 Ethernet10GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {scheduling_mode           _none_                  _none_               ALPHANUM                2      _none_                _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load                 _none_                  _none_               DECIMAL                 2      _none_                _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit             _none_                  _none_               ALPHANUM                2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }
    {pfc_priority_enable     PfcMeasurementConfig    PriorityEnable       MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_priority_pause_quanta    PfcMeasurementConfig    Time            MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_send_xon            PfcMeasurementConfig    EnableXon            {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_xon_delay           PfcMeasurementConfig    XonDelay             NUMERIC                                    5       1              1-3273000    true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_}
    {pfc_xon_delay_unit      PfcMeasurementConfig    XonDelayUnit         {CHOICES pause_quanta microseconds}        5    pause_quanta       _none_      true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_  }  
    {pfc_auto_trigger        PfcMeasurementConfig    AutoTrigger          {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
}
  {    interface_config_Ethernet100GigFiber
    {hname                   stcobj                 stcattr               type                                  priority   default         range       supported    dependency    mandatory   procfunc                                mode      constants}
    {port_handle            _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {mode                   _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {intf_mode              _none_                  _none_          {CHOICES ethernet}                              2       _none_          _none_      true         _none_         false       _none_                                  _none_      {ethernet PORT_TYPE_ETH}}
    {phy_mode               Ethernet100GigFiber     _none_          {CHOICES fiber copper}                          3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}}
    {autonegotiation        Ethernet100GigFiber     AutoNegotiation      {CHOICES 0 1}                              3       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 false 1 true}}
    {speed                  Ethernet100GigFiber     LineSpeed       {CHOICES ether100Gig}                           3       ether100Gig          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {ether100Gig SPEED_100G}}
    {duplex                 Ethernet100GigFiber     Duplex               {CHOICES half full}                        3       full          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {full FULL half HALF}}
    {flow_control           Ethernet100GigFiber     FlowControl          {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {control_plane_mtu      Ethernet100GigFiber     Mtu                  NUMERIC                                    5       1500            0-16383     true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {forward_error_correct  Ethernet100GigFiber     ForwardErrorCorrection {CHOICES true false}                     5       true          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_     {true TRUE false FALSE}          }
    {create_host            _none_                 _none_          {CHOICES true false}                             3       true            _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_                 _none_              NUMERIC                 3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {block_mode             _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
	{data_path_mode         Ethernet100GigFiber     DataPathMode         {CHOICES normal local_loopback}            5       normal          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {normal NORMAL local_loopback LOCAL_LOOPBACK}}
    {transmit_clock_source  Ethernet100GigFiber     TransmitClockSource  {CHOICES internal internal_ppm_adj loop}   5       internal        _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {internal INTERNAL internal_ppm_adj INTERNAL_PPM_ADJ loop LOOP}}
    {deficit_idle_count     Ethernet100GigFiber     DeficitIdleCount     {CHOICES true false}                       5       true            _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {internal_ppm_adjust    Ethernet100GigFiber     InternalPpmAdjust    ANY                                        5       0               _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_main_tap  Ethernet100GigFiber   TxPreEmphasisMainTap NUMERIC                                    5       21              0-31        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_post_tap  Ethernet100GigFiber   TxPreEmphasisPostTap NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {rx_equalization        Ethernet100GigFiber     RxEqualization       NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {collision_exponent     Ethernet100GigFiber     CollisionExponent    NUMERIC                                    5       10              1-10        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {enforce_mtu_on_rx      Ethernet100GigFiber     EnforceMtuOnRx       {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {vlan                   EthernetCopper          _none_               {CHOICES 0 1}                              4       1               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 FALSE 1 TRUE}}
    {qinq_incr_mode         _none_                  _none_               {CHOICES inner outer both}                 4       both            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id                VlanIf                  VlanId               NUMERIC                                    4       _none_        0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_cfi               VlanIf                  Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_id_count          _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id_step           VlanIf                  IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_user_priority     VlanIf                  Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_cfi         VlanOuterIf             Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id          VlanOuterIf             VlanId               NUMERIC                                    4       _none_       0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_step     VlanOuterIf             IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_count    _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_outer_user_priority   VlanOuterIf         Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {src_mac_addr           ethiiif                 SourceMac            ANY                                        3       _none_                     _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {src_mac_addr_step      ethiiif                 SrcMacStep           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}   
    {dst_mac_addr           Ipv4If                  GatewayMAC           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {intf_ip_addr           Ipv4If                  Address              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {intf_ip_addr_step      Ipv4If                  AddrStep             IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway                Ipv4If                  Gateway              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway_step           Ipv4If                  GatewayStep          IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {resolve_gateway_mac       Ipv4If              ResolveGatewayMac     {CHOICES true false}                       3       _none_          _none_      true         _none_        false             ::sth::Session::processConfigCmd       _none_     {true TRUE false FALSE} }
    {ipv6_prefix_length     Ipv6If                  PrefixLength         NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr         Ipv6If                  Address              IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr_step    Ipv6If                  AddrStep             IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway           Ipv6If                  Gateway              IPV6                                       3       _none_       _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway_step      Ipv6If                  GatewayStep          IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_resolve_gateway_mac  Ipv6If           ResolveGatewayMac        {CHOICES true false}                       3       true          _none_      true         _none_        false             ::sth::Session::processConfigCmd      _none_     {true TRUE false FALSE}    }
    {netmask                Ipv4If                  AddrStepMask         IP                                         3       _none_           _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {arp_req_timer          Ethernet100GigFiber      _none_              NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_req_retries        Ethernet100GigFiber      RetryCount          NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_send_req           Ethernet100GigFiber      _none_              NUMERIC                                    3       1               _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_cache_retrieve     _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arpnd_report_retrieve  _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arp_target             _none_                  _none_              {CHOICES port device stream all}            3       port            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {enable_ping_response   host                  EnablePingResponse  {CHOICES 0 1}                               3       0               _none_       true         _none_        false       _none_                                  _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_                  _none_              ALPHANUM                                    2      _none_           _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {pfc_priority_enable     PfcMeasurementConfig    PriorityEnable       MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_priority_pause_quanta    PfcMeasurementConfig    Time            MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_send_xon            PfcMeasurementConfig    EnableXon            {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_xon_delay           PfcMeasurementConfig    XonDelay             NUMERIC                                    5       1              1-3273000    true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_}
    {pfc_xon_delay_unit      PfcMeasurementConfig    XonDelayUnit         {CHOICES pause_quanta microseconds}        5    pause_quanta       _none_      true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_  }  
    {pfc_auto_trigger        PfcMeasurementConfig    AutoTrigger          {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_negotiate_by_dcbx  Ethernet100GigFiber      IsPfcNegotiated      {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority0              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority1              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority2              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority3              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority4              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority5              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority6              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority7              Ethernet100GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
}
  {    interface_config_Ethernet40GigFiber
    {hname                   stcobj                 stcattr               type                                  priority   default         range       supported    dependency    mandatory   procfunc                                mode      constants}
    {port_handle            _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {mode                   _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {intf_mode              _none_                  _none_          {CHOICES ethernet}                              2       _none_          _none_      true         _none_         false       _none_                                  _none_      {ethernet PORT_TYPE_ETH}}
    {phy_mode               Ethernet40GigFiber      _none_          {CHOICES fiber copper}                          3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}}
    {autonegotiation        Ethernet40GigFiber      AutoNegotiation      {CHOICES 0 1}                              3       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 false 1 true}}
    {speed                  Ethernet40GigFiber      LineSpeed            {CHOICES ether40Gig}                       3       ether40Gig          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {ether40Gig SPEED_40G}}
    {duplex                 Ethernet40GigFiber      Duplex               {CHOICES half full}                        3       full          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {full FULL half HALF}}
    {flow_control           Ethernet40GigFiber      FlowControl          {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {control_plane_mtu      Ethernet40GigFiber      Mtu                  NUMERIC                                    5       1500            0-16383     true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {create_host            _none_                  _none_          {CHOICES true false}                            3        true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_                  _none_              NUMERIC                                     3        _none_            _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_              _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
	{block_mode             _none_              _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
    {data_path_mode         Ethernet40GigFiber      DataPathMode         {CHOICES normal local_loopback}            5       normal          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {normal NORMAL local_loopback LOCAL_LOOPBACK}}
    {transmit_clock_source  Ethernet40GigFiber      TransmitClockSource  {CHOICES internal internal_ppm_adj loop}   5       internal        _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {internal INTERNAL internal_ppm_adj INTERNAL_PPM_ADJ loop LOOP}}
    {deficit_idle_count     Ethernet40GigFiber      DeficitIdleCount     {CHOICES true false}                       5       true            _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {internal_ppm_adjust    Ethernet40GigFiber      InternalPpmAdjust    ANY                                        5       0               _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_main_tap  Ethernet40GigFiber    TxPreEmphasisMainTap NUMERIC                                    5       21              0-31        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_post_tap  Ethernet40GigFiber    TxPreEmphasisPostTap NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {rx_equalization        Ethernet40GigFiber      RxEqualization       NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {collision_exponent     Ethernet40GigFiber      CollisionExponent    NUMERIC                                    5       10              1-10        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {enforce_mtu_on_rx      Ethernet40GigFiber      EnforceMtuOnRx       {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {vlan                   Ethernet40GigFiber      _none_               {CHOICES 0 1}                              4       1               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 FALSE 1 TRUE}}
    {qinq_incr_mode         _none_                  _none_               {CHOICES inner outer both}                 4       both            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id                VlanIf                  VlanId               NUMERIC                                    4       _none_        0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_cfi               VlanIf                  Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_id_count          _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id_step           VlanIf                  IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_user_priority     VlanIf                  Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_cfi         VlanOuterIf             Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id          VlanOuterIf             VlanId               NUMERIC                                    4       _none_       0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_step     VlanOuterIf             IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_count    _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_outer_user_priority   VlanOuterIf         Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {src_mac_addr           ethiiif                 SourceMac            ANY                                        3       _none_                      _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {src_mac_addr_step      ethiiif                 SrcMacStep           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}   
    {dst_mac_addr           Ipv4If                  GatewayMAC           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {intf_ip_addr           Ipv4If                  Address              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {intf_ip_addr_step      Ipv4If                  AddrStep             IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway                Ipv4If                  Gateway              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway_step           Ipv4If                  GatewayStep          IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {resolve_gateway_mac    Ipv4If              ResolveGatewayMac        {CHOICES true false}                       3       true          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      {true TRUE false FALSE}}
    {ipv6_prefix_length     Ipv6If                  PrefixLength         NUMERIC                                    3       _none_      _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr         Ipv6If                  Address              IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr_step    Ipv6If                  AddrStep             IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway           Ipv6If                  Gateway              IPV6                                       3       _none_       _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway_step      Ipv6If                  GatewayStep          IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_resolve_gateway_mac   Ipv6If           ResolveGatewayMac       {CHOICES true false}                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_     {true TRUE false FALSE} }
    {netmask                Ipv4If                  AddrStepMask         IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {arp_req_timer          Ethernet40GigFiber      _none_               NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_req_retries        Ethernet40GigFiber      RetryCount           NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_send_req           Ethernet40GigFiber      _none_               NUMERIC                                    3       1               _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_cache_retrieve     _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arpnd_report_retrieve  _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arp_target             _none_                  _none_               {CHOICES port device stream all}           3       port            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {pfc_negotiate_by_dcbx  Ethernet40GigFiber      IsPfcNegotiated      {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority0              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority1              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority2              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority3              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority4              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority5              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority6              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority7              Ethernet40GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {enable_ping_response   host                  EnablePingResponse   {CHOICES 0 1}                              3       0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_                  _none_                  ALPHANUM                                2      _none_           _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {pfc_priority_enable     PfcMeasurementConfig    PriorityEnable       MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_priority_pause_quanta    PfcMeasurementConfig    Time            MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_send_xon            PfcMeasurementConfig    EnableXon            {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_xon_delay           PfcMeasurementConfig    XonDelay             NUMERIC                                    5       1              1-3273000    true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_}
    {pfc_xon_delay_unit      PfcMeasurementConfig    XonDelayUnit         {CHOICES pause_quanta microseconds}        5    pause_quanta       _none_      true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_  }  
    {pfc_auto_trigger        PfcMeasurementConfig    AutoTrigger          {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
}

 {    interface_config_Ethernet25GigFiber
    {hname                   stcobj                 stcattr               type                                  priority   default         range       supported    dependency    mandatory   procfunc                                mode      constants}
    {port_handle            _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {mode                   _none_                  _none_               ALPHANUM                                   1       _none_          _none_      true         _none_         true        _none_                                  _none_      _none_}
    {intf_mode              _none_                  _none_          {CHOICES ethernet}                              2       _none_          _none_      true         _none_         false       _none_                                  _none_      {ethernet PORT_TYPE_ETH}}
    {phy_mode               Ethernet25GigFiber      _none_          {CHOICES fiber copper}                          3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}}
    {autonegotiation        Ethernet25GigFiber      AutoNegotiation      {CHOICES 0 1}                              3       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 false 1 true}}
    {speed                  Ethernet25GigFiber      LineSpeed            {CHOICES ether25Gig}                       3       ether25Gig      _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {ether25Gig SPEED_25G}}
    {duplex                 Ethernet25GigFiber      Duplex               {CHOICES half full}                        3       full            _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {full FULL half HALF}}
    {flow_control           Ethernet25GigFiber      FlowControl          {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {control_plane_mtu      Ethernet25GigFiber      Mtu                  NUMERIC                                    5       1500            0-16383     true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {create_host            _none_                  _none_          {CHOICES true false}                            3        true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {count                  _none_                  _none_              NUMERIC                                     3        _none_            _none_      true         _none_        false              _none_                                             _none_     _none_    }
    {expand                 _none_                  _none_          {CHOICES true false}        3          1              _none_      true         _none_        false              _none_                                             _none_     _none_    }
	{block_mode             _none_                  _none_          {CHOICES ONE_HOST_PER_BLOCK ONE_DEVICE_PER_BLOCK ONE_NETWORK_PER_BLOCK MULTIPLE_NETWORKS_PER_BLOCK MULTIPLE_DEVICE_PER_BLOCK}        3          ONE_DEVICE_PER_BLOCK          _none_      true         _none_        false              _none_            _none_     _none_    }
    {data_path_mode         Ethernet25GigFiber      DataPathMode         {CHOICES normal local_loopback}            5       normal          _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {normal NORMAL local_loopback LOCAL_LOOPBACK}}
    {transmit_clock_source  Ethernet25GigFiber      TransmitClockSource  {CHOICES internal internal_ppm_adj loop}   5       internal        _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {internal INTERNAL internal_ppm_adj INTERNAL_PPM_ADJ loop LOOP}}
    {deficit_idle_count     Ethernet25GigFiber      DeficitIdleCount     {CHOICES true false}                       5       true            _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {internal_ppm_adjust    Ethernet25GigFiber      InternalPpmAdjust    ANY                                        5       0               _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_main_tap  Ethernet25GigFiber    TxPreEmphasisMainTap NUMERIC                                    5       21              0-31        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {tx_preemphasis_post_tap  Ethernet25GigFiber    TxPreEmphasisPostTap NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {rx_equalization        Ethernet25GigFiber      RxEqualization       NUMERIC                                    5       8               0-15        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {collision_exponent     Ethernet25GigFiber      CollisionExponent    NUMERIC                                    5       10              1-10        true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {enforce_mtu_on_rx      Ethernet25GigFiber      EnforceMtuOnRx       {CHOICES true false}                       5       false           _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {true TRUE false FALSE}}
    {vlan                   Ethernet25GigFiber      _none_               {CHOICES 0 1}                              4       1               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd     _none_      {0 FALSE 1 TRUE}}
    {qinq_incr_mode         _none_                  _none_               {CHOICES inner outer both}                 4       both            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id                VlanIf                  VlanId               NUMERIC                                    4       _none_        0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_cfi               VlanIf                  Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_id_count          _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_id_step           VlanIf                  IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_user_priority     VlanIf                  Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_cfi         VlanOuterIf             Cfi                  NUMERIC                                    4       _none_     0-1         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id          VlanOuterIf             VlanId               NUMERIC                                    4       _none_       0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_step     VlanOuterIf             IdStep               NUMERIC                                    4       _none_     0-4095      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {vlan_outer_id_count    _none_                  _none_               NUMERIC                                    4       _none_          1-4096      true         _none_         false       _none_                                  _none_      _none_}
    {vlan_outer_user_priority   VlanOuterIf         Priority             NUMERIC                                    4       _none_     0-7         true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {src_mac_addr           ethiiif                 SourceMac            ANY                                        3       _none_                      _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {src_mac_addr_step      ethiiif                 SrcMacStep           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}   
    {dst_mac_addr           Ipv4If                  GatewayMAC           ANY                                        3       _none_          _none_      true         _none_         false       ::sth::Session::macAddressToStcFormat   _none_      _none_}
    {intf_ip_addr           Ipv4If                  Address              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {intf_ip_addr_step      Ipv4If                  AddrStep             IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway                Ipv4If                  Gateway              IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {gateway_step           Ipv4If                  GatewayStep          IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {resolve_gateway_mac    Ipv4If              ResolveGatewayMac        {CHOICES true false}                       3       true          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      {true TRUE false FALSE}}
    {ipv6_prefix_length     Ipv6If                  PrefixLength         NUMERIC                                    3       _none_      _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr         Ipv6If                  Address              IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_intf_addr_step    Ipv6If                  AddrStep             IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway           Ipv6If                  Gateway              IPV6                                       3       _none_       _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_gateway_step      Ipv6If                  GatewayStep          IPV6                                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {ipv6_resolve_gateway_mac   Ipv6If           ResolveGatewayMac       {CHOICES true false}                       3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_     {true TRUE false FALSE} }
    {netmask                Ipv4If                  AddrStepMask         IP                                         3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigCmd        _none_      _none_}
    {arp_req_timer          Ethernet25GigFiber      _none_               NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_req_retries        Ethernet25GigFiber      RetryCount           NUMERIC                                    3       _none_          _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_send_req           Ethernet25GigFiber      _none_               NUMERIC                                    3       1               _none_      true         _none_         false       ::sth::Session::processConfigArpCmd     _none_      _none_}
    {arp_cache_retrieve     _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arpnd_report_retrieve  _none_                  _none_               NUMERIC                                    3       0               _none_      true         _none_         false       _none_                                  _none_      _none_}
    {arp_target             _none_                  _none_               {CHOICES port device stream all}           3       port            _none_      true         _none_         false       _none_                                  _none_      _none_}
    {pfc_negotiate_by_dcbx  Ethernet25GigFiber      IsPfcNegotiated      {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority0              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority1              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority2              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority3              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority4              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority5              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority6              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {priority7              Ethernet25GigFiber      _none_               {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_}
    {enable_ping_response   host                  EnablePingResponse   {CHOICES 0 1}                              3       0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_                  _none_                  ALPHANUM                                2      _none_           _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
    {pfc_priority_enable     PfcMeasurementConfig    PriorityEnable       MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_priority_pause_quanta    PfcMeasurementConfig    Time            MULTILIST                                  5       0               _none_      true         _none_         false       ::sth::Session::processConfigPfcCmd     _none_      _none_ }    
    {pfc_send_xon            PfcMeasurementConfig    EnableXon            {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
    {pfc_xon_delay           PfcMeasurementConfig    XonDelay             NUMERIC                                    5       1              1-3273000    true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_}
    {pfc_xon_delay_unit      PfcMeasurementConfig    XonDelayUnit         {CHOICES pause_quanta microseconds}        5    pause_quanta       _none_      true         _none_         false       ::sth::Session::processConfigCmd          _none_      _none_  }  
    {pfc_auto_trigger        PfcMeasurementConfig    AutoTrigger          {CHOICES 0 1}                              5       0               _none_      true         _none_         false       ::sth::Session::processConfigFwdCmd       _none_      {0 FALSE 1 TRUE}}
}


  {    interface_config_POSPhy
    {hname                   stcobj                stcattr                type        priority     default         range       supported    dependency      mandatory     procfunc                                              mode       constants                        }
    {port_handle            _none_                  _none_              ALPHANUM        1          _none_          _none_      true         _none_          true            _none_                                             _none_     _none_                           }
    {mode                   _none_                  _none_              ALPHANUM        1          _none_          _none_      true         _none_          true            _none_                                             _none_     _none_                           }
    {phy_mode               SonetConfig             _none_      {CHOICES fiber copper}  3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {create_host            _none_                  _none_          {CHOICES true false} 3          true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {intf_mode              SonetConfig             HdlcEnable  {CHOICES pos_hdlc pos_ppp}        2          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {pos_hdlc ENABLE pos_ppp DISABLE}         }
    {speed                  SonetConfig             LineSpeed   {CHOICES ether10 ether100 ether1000 ether10000 ether9_286 oc3 oc12 oc48 oc192}        3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {ether10 SPEED_10M ether100 SPEED_100M ether1000 SPEED_1G ether10000 SPEED_10G ether9_286 SPEED_9_286G oc3 OC3 oc12 OC12 oc48 OC48 oc192 OC192}                           }
    {clocksource            SonetConfig             TxClockSrc          ALPHANUM        3          INTERNAL          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {internal INTERNAL loop RX_LOOP external EXTERNAL}      }
    {control_plane_mtu      POSPhy                  Mtu                 NUMERIC         3          1500          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {framing                SonetConfig             Framing             ALPHANUM        3          SONET          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {SONET SONET sonet SONET SDH SDH sdh SDH}                           }
    {lais_lrdi_threshold    SonetConfig             LaisLrdiThreshold   NUMERIC         3          5          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {tx_s1                  SonetConfig             TxS1                NUMERIC         3          0          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {tx_fcs                 SonetConfig             FCS                 ALPHANUM        3          FCS32          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {16 FCS16 32 FCS32}                        }
    {enable_ping_response   host                  EnablePingResponse  {CHOICES 0 1}   3          0               _none_       true         _none_        false            _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode        _none_                  _none_              ALPHANUM        2           _none_          _none_      true         _none_         false  _none_     _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
}
   {    interface_config_AtmPhy
    {hname                   stcobj                 stcattr                 type        priority   default         range       supported    dependency      mandatory       procfunc                                           mode       constants                        }
    {port_handle            _none_                  _none_                  ALPHANUM    1          _none_          _none_      true         _none_          true            _none_                                             _none_     _none_                           }
    {mode                   _none_                  _none_                  ALPHANUM    1          _none_          _none_      true         _none_          true            _none_                                             _none_     _none_                           }
    {phy_mode               SonetConfig             _none_      {CHOICES fiber copper}  3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {create_host            _none_                  _none_          {CHOICES true false} 3          true          _none_      true         _none_        false              _none_                                             _none_     {true TRUE false FALSE}         }
    {intf_mode              SonetConfig             HdlcEnable          {CHOICES atm}   2          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {atm DISABLE}         }
    {speed                  SonetConfig             LineSpeed   {CHOICES oc3 oc12 oc48} 3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     { oc3 OC3 oc12 OC12 oc48 OC48 }                           }
    {clocksource            SonetConfig             TxClockSrc              ALPHANUM    3          INTERNAL          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {internal INTERNAL loop RX_LOOP external EXTERNAL}      }
    {control_plane_mtu      AtmPhy                  Mtu                     NUMERIC     3          1500          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {rx_hec                 AtmPhy                  HecRxCorrectionEnable   NUMERIC     3          _none_          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}  }
    {framing                SonetConfig             Framing                 ALPHANUM    3          SONET          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {SONET SONET sonet SONET SDH SDH sdh SDH}                           }
    {lais_lrdi_threshold    SonetConfig             LaisLrdiThreshold       NUMERIC     3          5          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {tx_s1                  SonetConfig             TxS1                    NUMERIC     3          0          _none_      true         _none_          false             ::sth::Session::processConfigCmd                   _none_     {0 0 1 1}                        }
    {tx_fcs                 SonetConfig             FCS                     ALPHANUM    3          FCS32          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd                _none_     {16 FCS16 32 FCS32}                        }
    {arp_send_req           SonetConfig             FCS                     ALPHANUM    3          FCS32          _none_      true         _none_          false           _none_                                             _none_     {}                        }
    {enable_ping_response   host                  EnablePingResponse  {CHOICES 0 1}   3          0               _none_      true         _none_          false           _none_                                            _none_     {1 TRUE 0 FALSE}}
    {scheduling_mode       _none_                   _none_                  ALPHANUM    2          _none_          _none_      true         _none_          false           _none_                                            _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
}
  {    interface_config_FcPhy
    {hname                      stcobj         stcattr                type                                             priority     default         range       supported    dependency      mandatory     procfunc                                         mode       constants                        }
    {port_handle                _none_          _none_              ALPHANUM                                              1          _none_          _none_      true         _none_          true           _none_                                        _none_     _none_                           }
    {mode                       _none_          _none_              ALPHANUM                                              1          _none_          _none_      true         _none_          true           _none_                                        _none_     _none_                           }
    {phy_mode                   _none_          _none_             {CHOICES fiber copper}                                 3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_     {copper PORT_MODE_COPPER  fiber PORT_MODE_FIBER}                          }
    {create_host                _none_          _none_          {CHOICES true false}                                      3          true          _none_      true         _none_          false          _none_                                        _none_     {true TRUE false FALSE}         }
    {intf_mode                  _none_          _none_             {CHOICES fc}                                           2          _none_          _none_      true         _none_          false          _none_                                        _none_     _none_         }
    {speed                      FcPhy          LineSpeed           {CHOICES ether2000 ether4000 ether8000 ether10000 ether16000 ether32000}     3          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_     {ether2000 SPEED_2G ether4000 SPEED_4G ether8000 SPEED_8G ether10000 SPEED_10G ether16000 SPEED_16G ether32000 SPEED_32G }                           }
    {data_path_mode             FcPhy          DataPathMode        {CHOICES normal local_loopback}                        2          _none_          _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_     {normal NORMAL local_loopback LOCAL_LOOPBACK}      }
    {internal_ppm_adjust        FcPhy          InternalPpmAdjust   ANY                                                    2          0          _none_      true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {control_plane_mtu          FcPhy          Mtu                 NUMERIC                                                2          1500            0-16383     true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {transmit_clock_source      FcPhy          TransmitClockSource {CHOICES internal internal_ppm_adj }                   5          internal        _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_      {internal INTERNAL internal_ppm_adj INTERNAL_PPM_ADJ}}
    {receiver_ready_delay_max   FcPhy          IrgMax              NUMERIC                                                2          100             0-500000    true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {receiver_ready_delay_min   FcPhy          IrgMin              NUMERIC                                                2          0               0-500000    true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {receiver_ready_delay_mode  FcPhy          IrgMode             {CHOICES fixed  random}                                2          fixed           _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_      {fixed FIXED random RANDOM}}
    {receiver_ready_delay_units FcPhy          IrgUnits            {CHOICES us ms}                                        2            ms            _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_      {us MICROSECONDS ms MILLISECONDS}}
    {max_recv_size              FcPhy          MaxRecvSize         NUMERIC                                                2          2112            64-2120     true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {receiver_timeout           FcPhy          ReceiverTimeOut     NUMERIC                                                2          12              1-65535     true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {rx_credits                 FcPhy          RxCredits           NUMERIC                                                2          16              1-65535     true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {topology                   FcPhy          Topology            {CHOICES ptp_private ptp_public}                       2          ptp_public      _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_      {ptp_private PTP_PRIVATE ptp_public PTP_PUBLIC}}
    {traffic_class              FcPhy          TrafficClass        {CHOICES traffic_class_2 traffic_class_3}              2          traffic_class_3 _none_      true         _none_          false          ::sth::Session::processConfigFwdCmd           _none_      {traffic_class_2 TRAFFIC_CLASS_2 traffic_class_3 TRAFFIC_CLASS_3}}
    {tx_credits                 FcPhy          TxCredits           NUMERIC                                                2          16              1-65535     true         _none_          false          ::sth::Session::processConfigCmd              _none_     _none_    }
    {scheduling_mode            _none_         _none_              ALPHANUM                                               2          _none_          _none_      true         _none_          false           _none_                                       _none_     {RATE_BASED PORT_BASED PRIORITY_BASED MANUAL_BASED} }
    {port_load           _none_              _none_              DECIMAL                 2          _none_            _none_      true         _none_         false  _none_     _none_      _none_  }   
    {enable_ping_response   host                  EnablePingResponse  {CHOICES 0 1}   3          0               _none_      true         _none_          false           _none_                                            _none_     {1 TRUE 0 FALSE}}
    {port_loadunit           _none_              _none_              ALPHANUM                 2      PERCENT_LINE_RATE     _none_      true         _none_         false  _none_     _none_     _none_  }  
}
  {    interface_stats
    {hname                                    stcobj               stcattr                       type                               priority   default          range       supported    dependency mandatory  procfunc                         mode         constants   SA                     }
    {port_handle                              _none_               _none_                        ALPHANUM                            1          _none_          _none_      true         _none_        false    _none_                           _none_       _none_                           }
    {port_handle_list                         _none_               _none_                        ALPHANUM                            1          _none_          _none_      true         _none_        false    _none_                           _none_       _none_                           }
    {properties                               _none_               _none_                        ANY                           20          _none_          _none_      true         _none_        false    _none_                           _none_       _none_                           }
    {mode		                              _none_	           _none_		         {CHOICES common 10100 gbic 10gige}         20	        _none_	        _none_      true         _none_        false   _none_		                _none_       _none_                           }					
    {intf_type                                _none_               _none_                        ANY                                25          _none_          _none_      false        _none_        false   ::sth::Session::processGetInfType        {common ""}   _none_                           }
    {card_name                                _none_               ProductFamily                 ANY                                25          _none_          _none_      true         _none_        false   ::sth::Session::processGetCardName        {common ""}   _none_                           }
    {port_name                                _none_               _none_                        ANY                                25          _none_          _none_      false        _none_        false   ::sth::Session::processGetPortName        {common ""}   _none_                           }
    {intf_speed                               EthernetCopper       LinkSpeed                     ANY                                25          _none_          _none_      true         _none_        false   ::sth::Session::processGetLineSpeed        {common ""}   _none_                           }
    {tx_frames                                GeneratorPortResults TotalFrameCount               ANY                                25          _none_          _none_      true         _none_        false   _none_                               {10100 "" gbic "" 10gige ""}    _none_                           }
    {rx_frames                                AnalyzerPortResults  FrameCount                    ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}    _none_                           }
    {total_deferrals                          _none_               _none_                        ANY                                25          _none_          _none_      false        _none_        false   _none_        {10100 ""}    _none_                           }
    {link                                     EthernetCopper       LinkStatus                    ANY                                25          _none_          _none_      true         _none_        false   ::sth::Session::processGetLinkStatus         {10100 "" gbic "" 10gige ""}    _none_                           }
    {data_rate                                _none_               _none_                        ANY                                25          _none_          _none_      false        _none_        false  _none_        {10100 ""}    _none_                           }
    {duplex                                   EthernetCopper       Duplex                        ANY                                25          full          _none_      true         _none_        false   ::sth::Session::processGetDuplexMode        {10100 ""}    _none_                           }
    {tx_bytes                                 GeneratorPortResults TotalOctetCount               ANY                                25          _none_          _none_      true         _none_        false   _none_        {gbic "" 10gige ""}     _none_                           }
    {rx_bytes                                 AnalyzerPortResults  TotalOctetCount               ANY                                25         _none_           _none_      true         _none_        false   _none_        {gbic "" 10gige ""}    _none_                            }
    {mac_address                              _none_               _none_                        ANY                                25          _none_          _none_      false        _none_        false   _none_        {gbic ""}     _none_                           }
    {rx_fcs_error                             AnalyzerPortResults  FCSErrCount                   ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_runt_frames                           AnalyzerPortResults  UndersizeFrameCount           ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_counter_timestamp                     AnalyzerPortResults  CounterTimestamp              ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_rate_timestamp                        AnalyzerPortResults  RateTimestamp                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_sig_count                             AnalyzerPortResults  SigCount                      ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_min_frame_length                      AnalyzerPortResults  MinFrameLength                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_max_frame_length                      AnalyzerPortResults  MaxFrameLength                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_prbs_fill_byte_count                  AnalyzerPortResults  PRBSFillByteCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_jumbo_frame_count                     AnalyzerPortResults  JumboFrameCount               ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_pause_frame_count                     AnalyzerPortResults  PauseFrameCount               ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_ipv6_frame_count                      AnalyzerPortResults  IPv6FrameCount                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_ipv6_over_ipv4_frame_count            AnalyzerPortResults  IPv6OverIPv4FrameCount        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_icmp_frame_count                      AnalyzerPortResults  ICMPFrameCount                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_vlan_frame_count                      AnalyzerPortResults  VLANFrameCount                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_mpls_frame_count                      AnalyzerPortResults  MPLSFrameCount                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_ipv4_CheckSum_error_count             AnalyzerPortResults  Ipv4ChecksumErrorCount        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_tcp_CheckSum_error_count              AnalyzerPortResults  TcpChecksumErrorCount         ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_udp_xsum_error_count                  AnalyzerPortResults  UDPXSumErrCount               ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_oversize_frame_count                  AnalyzerPortResults  OversizeFrameCount            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_prbsbit_error_count                   AnalyzerPortResults  PRBSBitErrCount               ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger0_count                        AnalyzerPortResults  Trigger0Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger1_count                        AnalyzerPortResults  Trigger1Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger2_count                        AnalyzerPortResults  Trigger2Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger3_count                        AnalyzerPortResults  Trigger3Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger4_count                        AnalyzerPortResults  Trigger4Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger5_count                        AnalyzerPortResults  Trigger5Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger6_count                        AnalyzerPortResults  Trigger6Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger7_count                        AnalyzerPortResults  Trigger7Count                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_combo_trigger_count                   AnalyzerPortResults  ComboTriggerCount             ANY                                25          _none_          _none_      true         _none_        false   _none_       {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_frame_rate                            AnalyzerPortResults  FrameRate                     ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_byte_rate                             AnalyzerPortResults  ByteRate                      ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_sig_rate                              AnalyzerPortResults  SigRate                       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_prbs_fill_byte_rate                   AnalyzerPortResults  PRBSFillByteRate              ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_jumbo_frame_rate                      AnalyzerPortResults  JumboFrameRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_pause_frame_rate                      AnalyzerPortResults  PauseFrameRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_hw_frame_rate                         AnalyzerPortResults  HWFrameRate                   ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}                      _none_                           }
    {rx_hw_frame_count                        AnalyzerPortResults  HWFrameCount                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}                      _none_                           }
    {rx_ipv4_frame_rate                       AnalyzerPortResults  IPv4FrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_ipv6_frame_rate                       AnalyzerPortResults  IPv6FrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_ipv6_over_ipv4_frame_rate             AnalyzerPortResults  IPv6OverIPv4FrameRate         ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_udp_frame_rate                        AnalyzerPortResults  UDPFrameRate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_icmp_frame_rate                       AnalyzerPortResults  ICMPFrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_vlan_frame_rate                       AnalyzerPortResults  VLANFrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_mpls_frame_rate                       AnalyzerPortResults  MPLSFrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_fcs_error_rate                        AnalyzerPortResults  FCSErrRate                    ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_iphdr_xsum_err_rate                   AnalyzerPortResults  IPHdrXSumErrRate              ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_tcp_CheckSum_error_count              AnalyzerPortResults  TCPXSumErrRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_udp_CheckSum_err_rate                 AnalyzerPortResults  UdpChecksumErrorRate          ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_undersize_frame_rate                  AnalyzerPortResults  UndersizeFrameRate            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_oversize_frame_rate                   AnalyzerPortResults  OversizeFrameRate             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_prbs_bit_rate                         AnalyzerPortResults  PRBSBitErrRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger0_rate                         AnalyzerPortResults  Trigger0Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger1_rate                         AnalyzerPortResults  Trigger1Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger2_rate                         AnalyzerPortResults  Trigger2Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger3_rate                         AnalyzerPortResults  Trigger3Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger4_rate                         AnalyzerPortResults  Trigger4Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger5_rate                         AnalyzerPortResults  Trigger5Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger6_rate                         AnalyzerPortResults  Trigger6Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_trigger7_rate                         AnalyzerPortResults  Trigger7Rate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_combo_trigger_rate                    AnalyzerPortResults  ComboTriggerRate              ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {rx_pfc_frame_rate                        AnalyzerPortResults  PfcFrameRate                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {rx_fcoe_frame_rate                       AnalyzerPortResults  FcoeFrameRate                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {rx_pfc_frame_count                       AnalyzerPortResults  PfcFrameCount                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri0_frame_count                  AnalyzerPortResults  PfcPri0FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri1_frame_count                  AnalyzerPortResults  PfcPri1FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri2_frame_count                  AnalyzerPortResults  PfcPri2FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri3_frame_count                  AnalyzerPortResults  PfcPri3FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri4_frame_count                  AnalyzerPortResults  PfcPri4FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri5_frame_count                  AnalyzerPortResults  PfcPri5FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri6_frame_count                  AnalyzerPortResults  PfcPri6FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_pfc_pri7_frame_count                  AnalyzerPortResults  PfcPri7FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }    
    {rx_fcoe_frame_count                      AnalyzerPortResults  FcoeFrameCount                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_counter_timestamp                     GeneratorPortResults CounterTimestamp              ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_rate_timestamp                        GeneratorPortResults RateTimestamp                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_frame_count                 GeneratorPortResults GeneratorFrameCount           ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_sig_frame_count             GeneratorPortResults GeneratorSigFrameCount        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_octet_count                 GeneratorPortResults GeneratorOctetCount           ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_jumbo_frame_count           GeneratorPortResults GeneratorJumboFrameCount      ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_total_mpls_frame_count                GeneratorPortResults TotalMplsFrameCount           ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_ipv4_frame_count            GeneratorPortResults GeneratorIPv4FrameCount       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_ipv6_frame_count            GeneratorPortResults GeneratorIPv6FrameCount       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_vlan_frame_count            GeneratorPortResults GeneratorVlanFrameCount       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_mpls_frame_count            GeneratorPortResults GeneratorMplsFrameCount       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_crc_error_frame_count       GeneratorPortResults GeneratorCrcErrorFrameCount   ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_l3_checksum_error_count     GeneratorPortResults GeneratorL3ChecksumErrorCount ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_l4_checksum_error_count     GeneratorPortResults GeneratorL4ChecksumErrorCount ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_undersize_frame_count       GeneratorPortResults GeneratorUndersizeFrameCount  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_oversize_frame_count        GeneratorPortResults GeneratorOversizeFrameCount   ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_total_frame_rate                      GeneratorPortResults TotalFrameRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_frame_rate                  GeneratorPortResults GeneratorFrameRate            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_sig_frame_rate              GeneratorPortResults GeneratorSigFrameRate         ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_total_octet_rate                      GeneratorPortResults TotalOctetRate                ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_octet_rate                  GeneratorPortResults GeneratorOctetRate            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_jumbo_frame_rate            GeneratorPortResults GeneratorJumboFrameRate       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_total_vlan_frame_rate                 GeneratorPortResults TotalVlanFrameRate            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_ipv4_frame_rate             GeneratorPortResults GeneratorIPv4FrameRate        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_total_mpls_frame_rate                 GeneratorPortResults TotalMplsFrameRate            ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_ipv6_frame_rate             GeneratorPortResults GeneratorIPv6FrameRate        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_vlan_frame_rate             GeneratorPortResults GeneratorVlanFrameRate        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_mpls_frame_rate             GeneratorPortResults GeneratorMplsFrameRate        ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_crc_error_frame_rate        GeneratorPortResults GeneratorCrcErrorFrameRate    ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_l3_checksum_error_rate      GeneratorPortResults GeneratorL3ChecksumErrorRate  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_l4_checksum_error_rate      GeneratorPortResults GeneratorL4ChecksumErrorRate  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_undersize_frame_rate        GeneratorPortResults GeneratorUndersizeFrameRate   ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_oversize_frame_rate         GeneratorPortResults GeneratorOversizeFrameRate    ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_abort_frame_count           GeneratorPortResults GeneratorAbortFrameCount      ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_generator_abort_frame_rate            GeneratorPortResults GeneratorAbortFrameRate       ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_hw_frame_count                        GeneratorPortResults HwFrameCount                  ANY                                25          _none_          _none_      true         _none_        false   _none_        {10100 "" gbic "" 10gige ""}     _none_                           }
    {tx_pfc_frame_count		                  GeneratorPortResults PfcFrameCount                 ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri0_frame_count                  GeneratorPortResults PfcPri0FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri1_frame_count                  GeneratorPortResults PfcPri1FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri2_frame_count                  GeneratorPortResults PfcPri2FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri3_frame_count                  GeneratorPortResults PfcPri3FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri4_frame_count                  GeneratorPortResults PfcPri4FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri5_frame_count                  GeneratorPortResults PfcPri5FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri6_frame_count                  GeneratorPortResults PfcPri6FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
    {tx_pfc_pri7_frame_count                  GeneratorPortResults PfcPri7FrameCount             ANY                                25          _none_          _none_      true         _none_        false   _none_        {10gige ""}     _none_                           }
}
  {    cleanup_session
    {hname              stcobj        stcattr            type           priority   default         range       supported    dependency  mandatory procfunc                                                  mode       constants    }
    {port_handle        _none_        _none_             ALPHANUM       1          _none_          _none_      true         _none_        false   ::sth::Session::processCleanup_sessionPort_list         _none_     _none_         }
    {port_list          _none_        _none_             ALPHANUM       1          _none_          _none_      true         _none_        false   ::sth::Session::processCleanup_sessionPort_list         _none_     _none_         }
    {clean_dbfile       _none_        _none_             {CHOICES 0 1}  2           1              _none_      true         _none_        false   _none_                                                  _none_     _none_         }
    {clean_logs         _none_        _none_             {CHOICES 0 1}  2           0              _none_      true         _none_        false   _none_                                                  _none_     _none_         }
    {maintain_lock      _none_        _none_             {CHOICES 0 1}  3           0              _none_      true         _none_        false   _none_                                                  _none_     _none_         }
    {reset              _none_        _none_             FLAG           3           0              _none_      true         _none_        false   _none_                                                  _none_     _none_         }
    {clean_labserver_session       _none_        _none_             {CHOICES 0 1}  2           1              _none_      true         _none_        false   _none_                                                  _none_     _none_         }
  }
  {    device_info
    {hname              stcobj        stcattr            type        priority       default              range       supported    dependency mandatory procfunc                                      mode       constants                        }
    {fspec_version       _none_        _none_            FLAG           1          HLTAPI_5.10_STC_2.0  _none_      true         _none_        false   ::sth::Session::processInfoFspec_version         _none_     _none_                           }
    {ports               _none_        _none_            FLAG           1          _none_               _none_      true         _none_        false   ::sth::Session::processdeviceInfo                 _none_     _none_                           }
    {port_handle         _none_        _none_            ALPHANUM       1          _none_               _none_      true         _none_        false   ::sth::Session::processdeviceInfoPortHandle       _none_     _none_                           }
  }
  {    interface_control
    {hname              stcobj        stcattr            type                               priority   default         range       supported    dependency  mandatory procfunc                                                  mode       constants    }
    {port_handle        _none_        _none_             ALPHANUM                           1          _none_          _none_      true         _none_        true   _none_                                                     _none_     _none_         }
    {mode               _none_        _none_             {CHOICES break_link restore_link pfc_response_time restart_autonegotiation enable_monitor disable_monitor}  2  _none_  _none_      true       _none_        true   _none_                                                     _none_     _none_         }
  }
  {    load_xml
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
    {filename           _none_        none        ANY         1          _none_          _none_      true         _none_         true   _none_    _none_     _none_                           }
  }
  {    save_xml
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
    {filename           _none_        none        ANY         1          _none_          _none_      true         _none_         false   _none_    _none_     _none_                           }
  }
  {    reserve_ports
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
    {chassis_list      _none_        none         ANY         1          ""          _none_      true         _none_         false   _none_    _none_     _none_                           }
    {slot_list         _none_        none         ANY         1          ""          _none_      true         _none_         false   _none_    _none_     _none_                           }
    {location_list     _none_        none         ANY         1          ""          _none_      true         _none_         false   _none_    _none_     _none_                           }
  }
  {    start_devices
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
	{device_list           _none_        none        ALPHANUM         1          _none_          _none_      true         _none_         false   _none_    _none_     _none_                   }
    {order            _none_        none          ANY         1          _none_          _none_      true         _none_         false   _none_    _none_     {SERIALLY  INTERLEAVED}          }
  }
  {    stop_devices
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
    {device_list           _none_        none        ALPHANUM         1          _none_          _none_      true         _none_         false   _none_    _none_     _none_                   }
  }
  {    get_handles
    {hname             stcobj        stcattr      type        priority   default         range       supported    dependency mandatory  procfunc   mode       constants                        }
    {type           _none_        none           ANY         1          _none_          _none_      true         _none_         true   _none_    _none_     _none_                           }
    {from_ports     _none_        none           ANY         1          _none_          _none_      true         _none_         false   _none_    _none_     _none_                           }
    {from_devices     _none_        none           ANY         1          _none_          _none_      true         _none_         false   _none_    _none_     _none_                           }
  }
  {    link_config
    {hname                  stcobj        stcattr      type        priority   default         range       supported    dependency mandatory     procfunc     mode       constants                        }
    {link_src                _none_      _none_        ALPHANUM         1          _none_          _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    {link_dst                _none_      _none_        ANY              1          _none_          _none_      true         _none_        TRUE      _none_      _none_     _none_                           }
    {link_type               _none_      _none_        ANY              1   L3_Forwarding_Link   _none_      true         _none_        FALSE     _none_      _none_     _none_                           }
   }
  {    arp_control
    {hname                  stcobj              stcattr             type                                            priority   default         range       supported    dependency   mandatory      procfunc    mode       constants }
	{port_handle             port               _none_            ALPHANUM                                              1        _none_         _none_        true         _none_       false        _none_     _none_       _none_}
    {handle                  port               _none_            ALPHANUM                                              2        _none_         _none_        true         _none_       false        _none_     _none_       _none_}
    {arp_cache_retrieve     _none_              _none_            NUMERIC                                               3         0             _none_        true         _none_       false        _none_     _none_      _none_}
    {arpnd_report_retrieve  _none_              _none_            NUMERIC                                               3         0             _none_        true         _none_       false        _none_     _none_      _none_}
    {arp_target             _none_              _none_     {CHOICES port device stream all allstream alldevice}         3        port           _none_        true         _none_       true         _none_     _none_      _none_}
    {wait                   _none_              _none_            {CHOICES true false}                                  3         true          _none_        true         _none_       false        _none_     _none_      _none_}
   }
   {  arp_nd_config
    {hname                              stcobj              stcattr                                             type                                            priority       default         range       supported    dependency   mandatory      procfunc    mode       constants }
	{apply_configured_gw_mac            ArpNdConfig         ApplyConfiguredGatewayMac                           {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {duplicate_gw_detection             ArpNdConfig         DuplicateGatewayDetection                           {CHOICES true false}                                  3        true           _none_        true         _none_       false        _none_     {modify configArpNd}        _none_}
    {auto_arp_enable                    ArpNdConfig         EnableAutoArp                                       {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {cyclic_arp_enable                  ArpNdConfig         EnableCyclicArp                                     {CHOICES true false}                                  3        true           _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {unique_mac_addr_in_reply_enable    ArpNdConfig         EnableUniqueMacAddrInReply                          {CHOICES true false}                                  3        false          _none_        true         _none_       false         _none_    {modify configArpNd}       _none_}
    {unique_mac_pattern                 ArpNdConfig         EnableUniqueMacPattern                              NUMERIC                                               3        2222           0-65535       true         _none_       false        _none_     {modify configArpNd}        _none_}
    {ignore_failures                    ArpNdConfig         IgnoreFailures                                      {CHOICES true false}                                  3        true           _none_        true         _none_       false        _none_     {modify configArpNd}        _none_}
    {learning_rate                      ArpNdConfig         LearningRate                                        NUMERIC                                               3        250            _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {max_burst                          ArpNdConfig         MaxBurst                                            NUMERIC                                               3        16             _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {process_gratuitous_arp_requests    ArpNdConfig         ProcessGratuitousArpRequests                        {CHOICES true false}                                  3        true           _none_        true         _none_       false         _none_    {modify configArpNd}       _none_}
    {process_unsolicited_arp_replies    ArpNdConfig         ProcessUnsolicitedArpReplies                        {CHOICES true false}                                  3        true           _none_        true         _none_       false        _none_     {modify configArpNd}        _none_}
    {retry_count	                    ArpNdConfig         RetryCount	                                        NUMERIC                                               3        3              0-100         true         _none_       false        _none_     {modify configArpNd}        _none_}
    {time_out                           ArpNdConfig         TimeOut                                             NUMERIC                                               3        1000           _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {update_dest_mac                    ArpNdConfig         UpdateDestMacUponNonGratuitousArpRequestsReceived   {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {use_configured_link_local_addr     ArpNdConfig         UseConfiguredLinkLocalAddrForNeighborDiscovery      {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {use_gw_for_target                  ArpNdConfig         UseGatewayForTarget                                 {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {use_link_layer_cache_in_stack      ArpNdConfig         UseLinklayerCacheInStack                            {CHOICES true false}                                  3        false          _none_        true         _none_       false        _none_     {modify configArpNd}       _none_}
    {use_link_local_addr                ArpNdConfig         UseLinkLocalAddrForNeighborDiscovery                {CHOICES true false}                                  3        false          _none_        true         _none_       false         _none_    {modify configArpNd}       _none_}
   }
   {    system_settings
    {hname             stcobj                stcattr            type                                  priority   default         range       supported    dependency mandatory      procfunc        mode       constants                        }
    {realism_mode      RealismOptions        RealismMode        {CHOICES NORMAL CONTROL_PLANE}         1          _none_          _none_      true         _none_         false   {create configRealismMode modify configRealismMode}    _none_     _none_                           }
    {tshark_path        TrafficOptions        TSharkPath         ANY                                    1          _none_          _none_      true         _none_         false   _none_                                                 _none_     _none_                           }
   }
}

array set ::sth::Session::interface_stats_commonArray {
    intf_type                                       _none_        
    card_name                                       ProductFamily        
    port_name                                       _none_          
    intf_speed                                      LinkSpeed              
    link                                            LinkStatus              
    duplex                                          Duplex                       
    mac_address                                     _none_
}

array set ::sth::Session::device_classname_map_array {
    1                   bfdRouter/device/BfdRouterConfig/Bfd
    2                   bgpRouter/device/BgpRouterConfig/emulateddevice/Bgp
    3                   bgpRoute/config/BgpIpv4RouteConfig,BgpIpv6RouteConfig,BgpIpv4VplsConfig,BgpIpv6VplsConfig,BgpVplsAdConfig,BgpLsLinkConfig,BgpLsNodeConfig,BgpFlowSpecConfig,BgpEvpnAdRouteConfig,BgpEvpnMacAdvRouteConfig,BgpEvpnInclusiveMcastRouteConfig,BgpEvpnEthernetSegmentRouteConfig,BgpEvpnIpPrefixRouteConfig,BgpCustomAttribute,BgpMpReachUnReachAttr,BgpLsCustomTlv,BgpAsPathSegment,Ipv4NetworkBlock,Ipv6NetworkBlock,BgpMpNlri/emulateddevice/Bgp/BgpRouterConfig
    4                   eoamMsg/config/EoamMaintenancePointConfig/router/Eoam
    5                   fcoeHost/device/FcoeHostConfig/host/fcoe
    6                   isisRouter/device/IsisRouterConfig/emulateddevice/IsIs
    7                   isisLsp/config/IsisLspConfig,Ipv4IsisRoutesConfig,Ipv6IsisRoutesConfig,Ipv4NetworkBlock,Ipv6NetworkBlock/emulateddevice/IsIs/IsisRouterConfig
    8                   ospfRouter/device/Ospfv2RouterConfig,Ospfv3RouterConfig/emulateddevice/ospf
    9                   ospfLsa/config/AsbrSummaryLsa,ExternalLsaBlock,RouterLsa,RouterLsaLink,NetworkLsa,SummaryLsaBlock,TeLsa,RouterInfoLsa,ExtendedPrefixLsa,ExtendedLinkLsa,Ospfv3InterAreaPrefixLsaBlk,Ospfv3IntraAreaPrefixLsaBlk,Ospfv3InterAreaRouterLsaBlock,Ospfv3AsExternalLsaBlock,Ospfv3NssaLsaBlock,Ospfv3RouterLsa,Ospfv3NetworkLsa,Ospfv3LinkLsaBlk,Ipv4NetworkBlock,Ipv6NetworkBlock/emulateddevice/ospf/Ospfv2RouterConfig,Ospfv3RouterConfig/
    10                  ospfTlv/config/SrAlgorithmTlv,SidLabelRangeTlv,ExtendedPrefixTlv,PrefixSidSubTlv,SidLabelBindingSubTlv,EroSubTlv,Ipv4EroSubTlv,ExtendedLinkTlv,AdjSidSubTlv,LanAdjSidSubTlv,Ipv4NetworkBlock,Ipv6NetworkBlock/emulateddevice/ospf/Ospfv2RouterConfig,Ospfv3RouterConfig/
    11                  streamblock/config/StreamBlock/port/traffic
}

array set ::sth::Session::interface_stats_common {
    card_name processGetCardName
    port_name {processGetPortCmd}
    intf_speed {processGetSpeedCmd} \
    link {processGetLinkCmd} 
    duplex {processGetDuplexCmd} \
    mac_address {processGetMacCmd} \
}
    
    

array set ConstArray {
    PORT_TYPE_ETH {ethernet}
    10MBPS {10}
    100MBPS {100}
    1GBPS {1000}
    10GBPS {10000}\
    LINK_STATUS_DOWN {0}
    LINK_STATUS_UP {1}
    LINK_STATUS_NONE {0} \
    FULL_DUPLEX {full}
    HALF_DUPLEX half \
}
    
    
array set ::sth::Session::interface_stats_Analyzer_10100 {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_frame_rate                                   TotalFrameRate           
    rx_byte_rate                                    TotalOctetRate            
    rx_sig_rate                                     SigFrameRate             
    rx_jumbo_frame_rate                             JumboFrameRate      
    rx_pause_frame_rate                             PauseFrameRate      
    rx_hw_frame_count                                HwFrameCount         
    rx_ipv4_frame_rate                              Ipv4FrameRate       
    rx_ipv6_frame_rate                              Ipv6FrameRate       
    rx_ipv6_over_ipv4_frame_rate                    Ipv6OverIpv4FrameRate                             
}

array set ::sth::Session::interface_stats_Generator_10100 {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate      
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
}

array set ::sth::Session::interface_stats_Analyzer_gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_frame_rate                                   TotalFrameRate           
    rx_byte_rate                                    TotalOctetRate            
    rx_sig_rate                                     SigFrameRate             
    rx_jumbo_frame_rate                             JumboFrameRate      
    rx_pause_frame_rate                             PauseFrameRate      
    rx_hw_frame_count                                HwFrameCount         
    rx_ipv4_frame_rate                              Ipv4FrameRate       
    rx_ipv6_frame_rate                              Ipv6FrameRate       
    rx_ipv6_over_ipv4_frame_rate                    Ipv6OverIpv4FrameRate                                 
}

array set ::sth::Session::interface_stats_Generator_gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate    
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
}

array set ::sth::Session::interface_stats_Analyzer_10gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_frame_rate                                   TotalFrameRate           
    rx_byte_rate                                    TotalOctetRate            
    rx_sig_rate                                     SigFrameRate             
    rx_jumbo_frame_rate                             JumboFrameRate      
    rx_pause_frame_rate                             PauseFrameRate      
    rx_hw_frame_count                               HwFrameCount         
    rx_ipv4_frame_rate                              Ipv4FrameRate       
    rx_ipv6_frame_rate                              Ipv6FrameRate       
    rx_ipv6_over_ipv4_frame_rate                    Ipv6OverIpv4FrameRate
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                             FcoeFrameRate                          
    rx_pfc_frame_count                             PfcFrameCount                          
    rx_fcoe_frame_count                            FcoeFrameCount
    rx_pfc_pri0_frame_count                        PfcPri0FrameCount
    rx_pfc_pri1_frame_count                        PfcPri1FrameCount
    rx_pfc_pri2_frame_count                        PfcPri2FrameCount
    rx_pfc_pri3_frame_count                        PfcPri3FrameCount
    rx_pfc_pri4_frame_count                        PfcPri4FrameCount
    rx_pfc_pri5_frame_count                        PfcPri5FrameCount
    rx_pfc_pri6_frame_count                        PfcPri6FrameCount
    rx_pfc_pri7_frame_count                        PfcPri7FrameCount
}

array set ::sth::Session::interface_stats_Generator_10gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate     
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_pfc_frame_count		     	               PfcFrameCount     
    tx_pfc_pri0_frame_count                        PfcPri0FrameCount
    tx_pfc_pri1_frame_count                        PfcPri1FrameCount
    tx_pfc_pri2_frame_count                        PfcPri2FrameCount
    tx_pfc_pri3_frame_count                        PfcPri3FrameCount
    tx_pfc_pri4_frame_count                        PfcPri4FrameCount
    tx_pfc_pri5_frame_count                        PfcPri5FrameCount
    tx_pfc_pri6_frame_count                        PfcPri6FrameCount
    tx_pfc_pri7_frame_count                        PfcPri7FrameCount
}


array set ::sth::Session::interface_stats_Generator_100gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate     
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_pfc_frame_count                             PfcFrameCount
    tx_pfc_pri0_frame_count                        PfcPri0FrameCount
    tx_pfc_pri1_frame_count                        PfcPri1FrameCount
    tx_pfc_pri2_frame_count                        PfcPri2FrameCount
    tx_pfc_pri3_frame_count                        PfcPri3FrameCount
    tx_pfc_pri4_frame_count                        PfcPri4FrameCount
    tx_pfc_pri5_frame_count                        PfcPri5FrameCount
    tx_pfc_pri6_frame_count                        PfcPri6FrameCount
    tx_pfc_pri7_frame_count                        PfcPri7FrameCount    
}

array set ::sth::Session::interface_stats_Analyzer_100gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_frame_rate                                   TotalFrameRate           
    rx_byte_rate                                    TotalOctetRate            
    rx_sig_rate                                     SigFrameRate             
    rx_jumbo_frame_rate                             JumboFrameRate      
    rx_pause_frame_rate                             PauseFrameRate      
    rx_hw_frame_count                               HwFrameCount         
    rx_ipv4_frame_rate                              Ipv4FrameRate       
    rx_ipv6_frame_rate                              Ipv6FrameRate       
    rx_ipv6_over_ipv4_frame_rate                    Ipv6OverIpv4FrameRate
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                              FcoeFrameRate                          
    rx_pfc_frame_count                              PfcFrameCount                          
    rx_fcoe_frame_count                             FcoeFrameCount  
    rx_pfc_pri0_frame_count                        PfcPri0FrameCount
    rx_pfc_pri1_frame_count                        PfcPri1FrameCount
    rx_pfc_pri2_frame_count                        PfcPri2FrameCount
    rx_pfc_pri3_frame_count                        PfcPri3FrameCount
    rx_pfc_pri4_frame_count                        PfcPri4FrameCount
    rx_pfc_pri5_frame_count                        PfcPri5FrameCount
    rx_pfc_pri6_frame_count                        PfcPri6FrameCount
    rx_pfc_pri7_frame_count                        PfcPri7FrameCount    
}

array set ::sth::Session::interface_stats_Generator_40gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate     
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_pfc_frame_count		     	               PfcFrameCount     
    tx_pfc_pri0_frame_count                        PfcPri0FrameCount
    tx_pfc_pri1_frame_count                        PfcPri1FrameCount
    tx_pfc_pri2_frame_count                        PfcPri2FrameCount
    tx_pfc_pri3_frame_count                        PfcPri3FrameCount
    tx_pfc_pri4_frame_count                        PfcPri4FrameCount
    tx_pfc_pri5_frame_count                        PfcPri5FrameCount
    tx_pfc_pri6_frame_count                        PfcPri6FrameCount
    tx_pfc_pri7_frame_count                        PfcPri7FrameCount
}

array set ::sth::Session::interface_stats_Analyzer_40gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_frame_rate                                   TotalFrameRate           
    rx_byte_rate                                    TotalOctetRate            
    rx_sig_rate                                     SigFrameRate             
    rx_jumbo_frame_rate                             JumboFrameRate      
    rx_pause_frame_rate                             PauseFrameRate      
    rx_hw_frame_count                               HwFrameCount         
    rx_ipv4_frame_rate                              Ipv4FrameRate       
    rx_ipv6_frame_rate                              Ipv6FrameRate       
    rx_ipv6_over_ipv4_frame_rate                    Ipv6OverIpv4FrameRate
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                              FcoeFrameRate                          
    rx_pfc_frame_count                              PfcFrameCount                          
    rx_fcoe_frame_count                             FcoeFrameCount
    rx_pfc_pri0_frame_count                        PfcPri0FrameCount
    rx_pfc_pri1_frame_count                        PfcPri1FrameCount
    rx_pfc_pri2_frame_count                        PfcPri2FrameCount
    rx_pfc_pri3_frame_count                        PfcPri3FrameCount
    rx_pfc_pri4_frame_count                        PfcPri4FrameCount
    rx_pfc_pri5_frame_count                        PfcPri5FrameCount
    rx_pfc_pri6_frame_count                        PfcPri6FrameCount
    rx_pfc_pri7_frame_count                        PfcPri7FrameCount    
}

array set ::sth::Session::interface_stats_Generator_ocPOS {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate     
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
}

array set ::sth::Session::interface_stats_Analyzer_ocPOS {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_hw_frame_count                               HwFrameCount                                   
}

####EOT
array set ::sth::Session::interface_stats_eotGenerator_ocPOS {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_total_frame_rate                            TotalFrameRate           
    tx_total_octet_rate                            TotalOctetRate     
    tx_total_mpls_frame_rate                       TotalMplsFrameRate
    tx_generator_frame_rate                        GeneratorFrameRate
    tx_generator_sig_frame_rate                    GeneratorSigFrameRate
    tx_generator_octet_rate                        GeneratorOctetRate
    tx_generator_ipv4_frame_rate                   GeneratorIpv4FrameRate
    tx_generator_ipv6_frame_rate                   GeneratorIpv6FrameRate
    tx_generator_vlan_frame_rate                   GeneratorVlanFrameRate
    tx_generator_mpls_frame_rate                   GeneratorMplsFrameRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_undersize_frame_rate              GeneratorUndersizeFrameRate
    tx_generator_oversize_frame_rate               GeneratorOversizeFrameRate
    tx_generator_jumbo_frame_rate                  GeneratorJumboFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
}



####EOT

array set ::sth::Session::interface_stats_eotAnalyzer_10100 {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_hw_frame_count                                HwFrameCount                                   
}

array set ::sth::Session::interface_stats_eotAnalyzer_ocPOS {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount   
    rx_hw_frame_count                               HwFrameCount                                   
}

array set ::sth::Session::interface_stats_eotGenerator_10100 {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
}

array set ::sth::Session::interface_stats_eotAnalyzer_gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount                                
}

array set ::sth::Session::interface_stats_eotGenerator_gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
}

array set ::sth::Session::interface_stats_eotAnalyzer_10gbic {
    rx_frames                                       TotalFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                              FcoeFrameRate                          
    rx_pfc_frame_count                              PfcFrameCount                          
    rx_fcoe_frame_count                             FcoeFrameCount                        
}

array set ::sth::Session::interface_stats_eotGenerator_10gbic {   
    tx_frames                                      TotalFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_pfc_frame_count		     	           PfcFrameCount     
}

array set ::sth::Session::interface_stats_eotAnalyzer_100gbic {
    rx_frames                                       SigFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                              FcoeFrameRate                          
    rx_pfc_frame_count                              PfcFrameCount                          
    rx_fcoe_frame_count                             FcoeFrameCount                        
}

array set ::sth::Session::interface_stats_eotGenerator_100gbic {   
    tx_frames                                      GeneratorSigFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_pfc_frame_count		     	           PfcFrameCount     
}

array set ::sth::Session::interface_stats_eotAnalyzer_40gbic {
    rx_frames                                       SigFrameCount           
    rx_bytes                                        TotalOctetCount
    rx_fcs_error                                    FcsErrorFrameCount          
    rx_runt_frames                                  UndersizeFrameCount                
    rx_sig_count                                    SigFrameCount                      
    rx_max_frame_length                             MaxFrameLength         
    rx_prbs_fill_byte_count                         PrbsFillOctetCount     
    rx_jumbo_frame_count                            JumboFrameCount               
    rx_ipv6_over_ipv4_frame_count                   Ipv6OverIpv4FrameCount                     
    rx_mpls_frame_count                             MplsFrameCount        
    rx_ipv4_CheckSum_error_count                    Ipv4ChecksumErrorCount      
    rx_tcp_CheckSum_error_count                     TcpChecksumErrorCount             
    rx_oversize_frame_count                         OversizeFrameCount   
    rx_prbsbit_error_count                          PrbsBitErrorCount      
    rx_trigger1_count                               Trigger1Count       
    rx_trigger2_count                               Trigger2Count        
    rx_trigger4_count                               Trigger4Count     
    rx_trigger5_count                               Trigger5Count     
    rx_trigger6_count                               Trigger6Count        
    rx_combo_trigger_count                          ComboTriggerCount
    rx_pfc_frame_rate                               PfcFrameRate                                      
    rx_fcoe_frame_rate                              FcoeFrameRate                          
    rx_pfc_frame_count                              PfcFrameCount                          
    rx_fcoe_frame_count                             FcoeFrameCount                        
}


array set ::sth::Session::interface_stats_eotGenerator_40gbic {   
    tx_frames                                      GeneratorSigFrameCount        
    tx_bytes                                       TotalOctetCount
    tx_total_mpls_frame_count                      TotalMplsFrameCount
    tx_generator_frame_count                       GeneratorFrameCount
    tx_generator_sig_frame_count                   GeneratorSigFrameCount
    tx_generator_octet_count                       GeneratorOctetCount
    tx_generator_ipv4_frame_count                  GeneratorIpv4FrameCount
    tx_generator_ipv6_frame_count                  GeneratorIpv6FrameCount
    tx_generator_vlan_frame_count                  GeneratorVlanFrameCount
    tx_generator_mpls_frame_count                  GeneratorMplsFrameCount
    tx_generator_crc_error_frame_count             GeneratorCrcErrorFrameCount
    tx_generator_l3_checksum_error_count           GeneratorL3ChecksumErrorCount
    tx_generator_l4_checksum_error_count           GeneratorL4ChecksumErrorCount
    tx_generator_l3_checksum_error_rate            GeneratorL3ChecksumErrorRate
    tx_generator_l4_checksum_error_rate            GeneratorL4ChecksumErrorRate
    tx_generator_crc_error_frame_rate              GeneratorCrcErrorFrameRate
    tx_generator_abort_frame_rate                  GeneratorAbortFrameRate
    tx_generator_undersize_frame_count             GeneratorUndersizeFrameCount
    tx_generator_oversize_frame_count              GeneratorOversizeFrameCount
    tx_generator_jumbo_frame_count                 GeneratorJumboFrameCount
    tx_generator_abort_frame_count                 GeneratorAbortFrameCount
    tx_hw_frame_count                              HwFrameCount
    tx_pfc_frame_count		     	           PfcFrameCount     
}
