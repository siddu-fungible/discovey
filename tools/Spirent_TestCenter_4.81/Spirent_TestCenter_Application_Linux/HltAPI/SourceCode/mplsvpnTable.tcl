# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Mplsvpn:: {
}

set ::sth::Mplsvpn::MplsvpnTable {
    ::sth::Mplsvpn::
    {   emulation_mpls_l2vpn_pe_config
        {hname                      stcobj                      stcattr                 type                                priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle                _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {mode                       _none_                      _none_                  {CHOICES enable disable}            1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
        {handle                     _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_type                   _none_                      _none_                  {CHOICES  martini_pwe ldp_vpls bgp_vpls} 1               ldp_vpls    _none_      true        _none_      false        _none_          { }          _none_}
        {enable_p_router            _none_                      _none_                  FLAG                                1               0           _none_      true        _none_      false       _none_          { }          _none_}
        {mpls_session_handle        _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {igp_session_handle         _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {targeted_ldp_session_handle _none_                     _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {vpls_bgp_session_handle    _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {pe_count                   _none_                      _none_                  NUMERIC                             1               1           _none_      true        _none_      false       _none_          { }          _none_}
        {tunnel_handle              _none_                      _none_                  ANY                                 1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
    }
    {   emulation_mpls_l2vpn_site_config
        {hname                      stcobj                      stcattr                 type                                priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle                _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {mode                       _none_                      _none_                  {CHOICES create modify delete}      1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
        {handle                     _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_handle                  _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_addr        VpnSiteVplsxx               PeIpv4Addr              IP                                  1               10.1.1.1    _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_step        _none_                      _none_                  IP                                  1               0.0.0.0     _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_prefix      VpnSiteVplsxx               PeIpv4PrefixLength      NUMERIC                             1               32          _none_      true        _none_      false        _none_          { }          _none_}
        {site_count                 _none_                      _none_                  NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_type                   _none_                      _none_                  {CHOICES martini_pwe ldp_vpls bgp_vpls}     1       ldp_vpls    _none_      true        _none_      false        _none_          { }           _none_}
        {vc_type                    VcLsp                       Encap                   {CHOICES 4 5 B b}                   1               5           _none_      true        _none_      false        _none_          { }          {4 "LDP_LSP_ENCAP_ETHERNET_VLAN" 5 "LDP_LSP_ENCAP_ETHERNET" B "LDP_LSP_ENCAP_ETHERNET_VPLS" b "LDP_LSP_ENCAP_ETHERNET_VPLS"}}
        {vc_id                      VpnSiteInfoVplsLdp          StartVcId               NUMERIC                             1               1       0-4294967295    true        _none_      false        _none_          { }          _none_}
        {vc_id_step                 VpnSiteInfoVplsLdp          VcIdStep                NUMERIC                             1               1       0-4294967295    true        _none_      false        _none_          { }          _none_}
        {vc_id_count                VpnSiteInfoVplsLdp          VcIdCount               NUMERIC                             1               1       0-4294967295    true        _none_      false        _none_          { }          _none_}
        {ve_id                      VpnSiteInfoVplsBgp          StartVeId               NUMERIC                             1               1       0-65535         true        _none_      false        _none_          { }          _none_}
        {ve_id_step                 VpnSiteInfoVplsBgp          VeIdStep                NUMERIC                             1               1       0-65535         true        _none_      false        _none_          { }          _none_}
        {rd_start                   VpnSiteInfoVplsBgp          RouteDistinguisher      ANY                                 1               1:0         _none_      true        _none_      false        _none_          { }          _none_}
        {rd_step                    VpnSiteInfoVplsBgp          RouteDistinguisherStep  ANY                                 1               0:0         _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_block_count            VpnSiteInfoVplsBgp          Count                   NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_id                     _none_                      _none_                  NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_id_step                _none_                      _none_                  NUMERIC                             1               0           _none_      true        _none_      false        _none_          { }          _none_}
        {vlan_id                    VlanIf                      VlanId                  NUMERIC                             1               _none_      1-4095      true        _none_      false        _none_          { }          _none_}
        {vlan_id_step               VlanIf                      IdStep                  NUMERIC                             1               0           0-4095      true        _none_      false        _none_          { }          _none_}
        {vlan_id_count              VlanIf                      IfCountPerLowerIf       NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vlan_id_outer              VlanIf_Outer                VlanId                  NUMERIC                             1               _none_      1-4095      true        _none_      false        _none_          { }          _none_}
        {vlan_id_outer_step         VlanIf_Outer                IdStep                  NUMERIC                             1               0           0-4095      true        _none_      false        _none_          { }          _none_}
        {vlan_id_outer_count        VlanIf_Outer                IfRecycleCount          NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {mac_addr                   EthIIIf                     SourceMac               ANY                                 1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {mac_addr_step              EthIIIf                     SrcMacStep              ANY                                 1       00:00:00:00:00:01   _none_      true        _none_      false        _none_          { }          _none_}
        {mac_addr_count             EthIIIf                     IfRecycleCount          ANY                                 1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
    }
    {   emulation_mpls_l3vpn_pe_config
        {hname                      stcobj                      stcattr                 type                                priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle                _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {mode                       _none_                      _none_                  {CHOICES enable disable}      1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
        {handle                     _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_count                   _none_                      _none_                  NUMERIC                             1               1           _none_      true        _none_      false       _none_          { }          _none_}
        {enable_p_router            _none_                      _none_                  FLAG                                1               0           _none_      true        _none_      false       _none_          { }          _none_}
        {mpls_session_handle        _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {bgp_session_handle         _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {igp_session_handle         _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
        {tunnel_handle              _none_                      _none_                  ANY                                 1               _none_      _none_      true        _none_      false       _none_          { }          _none_}
    }
    {   emulation_mpls_l3vpn_site_config
        {hname                      stcobj                      stcattr                 type                                priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
        {port_handle                _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {mode                       _none_                      _none_                  {CHOICES create modify delete}      1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
        {handle                     _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_handle                  _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_addr        VpnSiteInfoRfc2547          PeIpv4Addr              IP                                  1               10.0.0.1    _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_step        _none_                      _none_                  IP                                  1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {pe_loopback_ip_prefix      VpnSiteInfoRfc2547          PeIpv4PrefixLength      NUMERIC                             1               32          _none_      true        _none_      false        _none_          { }          _none_}
        {ce_session_handle          _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      false        _none_          { }          _none_}
        {site_count                 _none_                      _none_                  NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {device_count               Router                      DeviceCount             NUMERIC                             1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {rd_start                   VpnSiteInfoRfc2547          RouteDistinguisher      ANY                                 1               1:0         _none_      true        _none_      false        _none_          { }          _none_}
        {rd_step                    _none_                      _none_                  ANY                                 1               0:0         _none_      true        _none_      false        _none_          { }          _none_}
        {interface_ip_addr          Ipv4If                      Address                 IP                                  1               192.85.1.1  _none_      true        _none_      false       _none_          { }          _none_}
        {interface_ip_step          _none_                      _none_                  IP                                  1               0.0.1.0     _none_      true        _none_      false       _none_          { }          _none_}
        {interface_ip_prefix        Ipv4If                      PrefixLength            NUMERIC                             1               24          _none_      true        _none_      false       _none_          { }          _none_}
        {vpn_id                     _none_                      _none_                  ALPHANUM                            1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vpn_id_step                _none_                      _none_                  ALPHANUM                            1               1           _none_      true        _none_      false        _none_          { }          _none_}
        {vlan_id                    VlanIf                      VlanId                  NUMERIC                             1               _none_      1-4095      true        _none_      false        _none_          { }          _none_}
        {vlan_id_step               VlanIf                      IdStep                  NUMERIC                             1               1           0-4095      true        _none_      false        _none_          { }          _none_}
    }
    #{   emulation_mpls_vpn_control
    #    {hname                      stcobj                      stcattr                 type                                priority        default     range       supported   dependency  mandatory   procfunc        mode            constants}
    #    {handle                     _none_                      _none_                  ALPHANUM                            1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
    #    {action                     _none_                      _none_                  {CHOICES start stop}                1               _none_      _none_      true        _none_      true        _none_          { }          _none_}
    #}
}