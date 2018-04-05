# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

#source trafficFunctions.tcl

# open issues still
# updated 11/29/2006
# 1.    parse dashed args takes ipv6 address in the form #:#:#:#:#:#:#:#
#       Thus it will break if we give the short notation FEC0::0
#       Thus normalize it before calling commandInit
#
# 2.    All error types should be like this
#       parse_dashed_args: Invalid value "12" for "-ip_src_addr" argument.
#       Valid values are: "A v4 format IP address (of form #.#.#.#)"}}

namespace eval ::sth::Traffic:: {
    set modeOfOperation "";
    set handleTxStream 0;
    set handleRxStream 0;
    set handleCurrentStream 0;
    set handleCurrentHeader 0;
    set handleCurrentl2Header 0;
    set handleCurrentl3Header 0;
    set handleCurrentl4Header 0;
    
    # Enable stream option in rangemodifier, default value is true
    set enableStream true;
    
    #add for gre
    set greIPHeader "";
    set greHeader "";
    set greRangeModifierSrc "";
    set greRangeModifierDst "";
    set greIPHeaderType "";
    
    array set arrayPortHnd {};
    array set arraystreamHnd {};
    array set arraystreamIpv6NextHeadersHnd {};
    array set arraystreamIpv4RouterAlertHeadersHnd {};
    array set arrayHeaderTypesInCreate {};
    array set arraystreamCustomParam {};
    
    # move later to trafficFunctions.tcl file
    set l2EncapType "_none_";
    set l3HeaderType "_none_";
    set l4PHeaderType "_none_";
    
    set listGeneralAttributes {};
    set listProcessedList {};
    set listSbLoadProfileList {};
    set listTransmitModeAttributes {};
    set listl2encap_EthernetII {};
    set listl2encap_EthernetII_bidirectional {};
    set listl2encap_Ethernet8022 {};
    set listl2encap_Ethernet8022_bidirectional {};
    set listl2encap_EthernetSnap {};
    set listl2encap_EthernetSnap_bidirectional {};
    set listl2encap_Ethernet8023Raw {};
    set listl2encap_Ethernet8023Raw_bidirectional {};
    set listl2encap_Vlan {};
    set listl2encap_ATM {};
    set listl2encap_FC {};
    set listl2encap_FcSofEof {};
    set listl3Header_Ipv4 {};
    set listl3Header_Ipv6 {};
    set listl3Header_Arp {};
    set listl2encap_OuterVlan {};
    set listl2encap_OtherVlan {};
    set listl3Header_OuterIpv4 {};
    set listl3Header_OuterIpv6 {};
    set listl3Header_Gre {};
    set listl4Headertcp {};
    set listl4Headerudp {};
    set listl4Headerisis {};
    set listl4Headerigmp {};
    set listl4Headericmp {};
    set listl4Headericmpv6 {};
    set listl4Headeripv4 {};
    set listl4Headeripv6 {};
    set listl2VlanRangeModifier {};
    set listl2VlanPriorityRangeModifier {};
    set listl2VpiRangeModifier {};
    set listl2VciRangeModifier {};
    set listl2OuterVlanRangeModifier {};
    set listl2OtherVlanRangeModifier {};
    set listl2SrcRangeModifier {};
    set listl2DstRangeModifier {};
    set listl2Src2RangeModifier {};
    set listl2Dst2RangeModifier {};
    set listl3SrcRangeModifier {};
    set listl3DstRangeModifier {};
    set listl3OuterSrcRangeModifier {};
    set listl3OuterDstRangeModifier {};
    set listl3precedenceRangeModifier {};
    set listl3tosRangeModifier {};
    set listl3OuterPrecedenceRangeModifier {};
    set listl3OuterTosRangeModifier {};
    set listl3QosBits {};
    set listl4QosBits {};
    set listl3OuterQosBits {};
    set listl4precedenceRangeModifier {};
    set listl4tosRangeModifier {};
    set listMplsHeaderAttributes_Mpls {};
    set listMacGwRangeModifier {};
    set listArpMacSrcRangeModifier {};
    set listArpMacDstRangeModifier {};
    set listIgmpGroupAddrRangeModifier {};
    set listMplsLabelTableModifier {};
    set listMplsLabelRangeModifier {};
    set listMplsLabelModifier {};
    set listMplsCosTableModifier {};
    set listMplsCosRangeModifier {};
    set listMplsCosModifier {};
    set listMplsTtlTableModifier {};
    set listMplsTtlRangeModifier {};
    set listMplsTtlModifier {};
    set listTcpPortSrcRangeModifier {};
    set listTcpPortDstRangeModifier {};
    set listUdpPortSrcRangeModifier {};
    set listUdpPortDstRangeModifier {};
    set listl4DstRangeModifier {};
    set listl4SrcRangeModifier {};
    set listVxlanHeader {};
    set listInnerl2encap_EthernetII {};
    set listInnerl2encap_OuterVlan {};
    set listInnerl2encap_Vlan {};
    set listInnerl3Header_Ipv4 {};
    set listInnerl2SrcRangeModifier {};
    set listInnerl2DstRangeModifier {};
    set listInnerl3SrcRangeModifier {};
    set listInnerl3DstRangeModifier {};
    set listInnerl2OuterVlanRangeModifier {};
    set listInnerl2VlanPriorityRangeModifier {};
    set listInnerl2VlanRangeModifier {};
    set listInnerGwRangeModifier {};
    set listl4DstRangeModifier {};
    set listl4SrcRangeModifier {};
    set listThresholdList {};
    #set listip_precedenceRangeModifier {};
    #set listip_tosRangeModifier {};
    
    #{listl2encap_OuterVlan listl2encap_Vlan}
    # add more elements to this later as we go on adding more encap types
    array set arrayHeaderLists {ethernet_ii                 {ethernet:EthernetII    {listl2encap_EthernetII listInnerl2encap_EthernetII}}
                                ethernet_ii_vlan            {ethernet:EthernetII    {listl2encap_EthernetII listInnerl2encap_EthernetII}    ethernet:Vlan  {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan listInnerl2encap_OuterVlan listInnerl2encap_Vlan}}
                                ethernet_8022               {ethernet:Ethernet8022  listl2encap_Ethernet8022}
                                ethernet_8022_vlan          {ethernet:Ethernet8022  {listl2encap_Ethernet8022} ethernet:Vlan  {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}}
                                ethernet_8023_snap          {ethernet:EthernetSnap  {listl2encap_EthernetSnap}}
                                ethernet_8023_snap_vlan     {ethernet:EthernetSnap  {listl2encap_EthernetSnap} ethernet:Vlan  {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}}
                                ethernet_8023_raw           {ethernet:Ethernet8023Raw  {listl2encap_Ethernet8023Raw}}
                                ethernet_8023_raw_vlan      {ethernet:Ethernet8023Raw  {listl2encap_Ethernet8023Raw} ethernet:Vlan  {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}}
                                atm_vc_mux                  {atm:ATM listl2encap_ATM}
                                atm_llcsnap                 {atm:ATM listl2encap_ATM}
                                fibre_channel               {fc:FC listl2encap_FC   fc:FcSofEof listl2encap_FcSofEof}
                                ethernet_ii_pppoe           {ethernet:EthernetII    listl2encap_EthernetII}
                                ethernet_ii_vlan_pppoe      {ethernet:EthernetII    {listl2encap_EthernetII}    ethernet:Vlan   {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}}
                                ethernet_ii_qinq_pppoe      {ethernet:EthernetII    {listl2encap_EthernetII}    ethernet:Vlan   {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}}
                                ethernet_ii_unicast_mpls    {ethernet:EthernetII    {listl2encap_EthernetII}    mpls:Mpls       {listMplsHeaderAttributes_Mpls}}
                                ethernet_ii_vlan_mpls       {ethernet:EthernetII    {listl2encap_EthernetII}    ethernet:Vlan  {listl2encap_OtherVlan listl2encap_OuterVlan listl2encap_Vlan}    mpls:Mpls {listMplsHeaderAttributes_Mpls}}
                                ipv4                        {ipv4:IPv4              listl3Header_Ipv4}
                                arp                         {arp:ARP                listl3Header_Arp}
                                outer_ipv4                  {ipv4:IPv4              listl3Header_OuterIpv4}
                                ipv6                        {ipv6:IPv6              listl3Header_Ipv6}
                                outer_ipv6                  {ipv6:IPv6              listl3Header_OuterIpv6}
                                inner_ipv4                  {ipv4:IPv4              listInnerl3Header_Ipv4}
                                tcp                         {tcp:Tcp                listl4Headertcp}
                                udp                         {udp:Udp                listl4Headerudp}
                                rtp                         {udp:Udp                listl4Headerudp}                             
                                icmp                        {icmp:Icmp              listl4Headericmp}
                                icmpv6                      {icmpv6:Icmpv6          listl4Headericmpv6}
                                igmp                        {igmp:Igmp              listl4Headerigmp}
                                l4_ipv4                     {ipv4:IPv4              listl4Headeripv4}
                                l4_ipv6                     {ipv6:IPv6              listl4Headeripv6}
                                gre                         {gre:Gre                listl3Header_Gre}
};
                                
    array set arrayLengthModeSwitches { fixed       {{l3_length 110}}
                                        random      {{l3_length_min 110} {l3_length_max 238}}
                                        imix        {}
                                        auto        {}
                                        increment   {{l3_length_min 110} {l3_length_max 238}}
                                    }

    array set arrayTransmitModeSwitches {   continuous          {pkts_per_burst 1}
                                            continuous_burst    {pkts_per_burst _none_ inter_stream_gap _none_ inter_stream_gap_unit _none_}
                                            multi_burst         {burst_loop_count _none_    pkts_per_burst _none_ inter_stream_gap _none_ inter_stream_gap_unit _none_}
                                            single_burst        {burst_loop_count 1         pkts_per_burst _none_ inter_stream_gap _none_ inter_stream_gap_unit _none_}
                                            single_pkt          {burst_loop_count 1         pkts_per_burst 1} }
    
    array set arrayModeFunctionMap {create processTrafficConfigModecreate
                                    modify processTrafficConfigModemodify
                                    remove processTrafficConfigModeEnableDisable
                                    disable processTrafficConfigModeEnableDisable
                                    enable processTrafficConfigModeEnableDisable
                                    reset  processTrafficConfigModereset}
    
    array set arrayDecimal2Bin {0 0000 1 0001 2 0010 3 0011 4 0100 5 0101 \
                                6 0110 7 0111 8 1000 9 1001 \
                                10 1010 11 1011 12 1100 13 1101 14 1110 15 1111}
    
    array set arrayBin2Decimal {0000 0 0001 1 0010 2 0011 3 0100 4 0101 5 \
                                0110 6 0111 7 1000 8 1001 9 \
                                1010 10 1011 11 1100 12 1101 13 1110 14 1111 15}
}


#
##Procedure Header
#
# Name:
#    sth::traffic_config
#
# Purpose:
#    Creates, modifies, removes, or resets a stream block of network traffic on
#    the specified test port(s). A stream is a series of packets that can be
#    tracked by Spirent HLTAPI. A stream block is a collection of one or
#    more streams represented by a base stream definition plus one or more rules
#    that describe how the base definition is modified to produce additional
#    streams.
#
# Synopsis:
#    sth::traffic_config
#         -mode   {create|modify|remove|enable|disable|reset }
#              -stream_id <stream_handle>
#              -port_handle  <handle>
#              [-emulation_src_handle <handle>]
#              [-emulation_dst_handle <handle>]
#              [-bidirectional {1|0}]
#                   [-port_handle2   <handle>]
#                   [-mac_dst2       <aa:bb:cc:dd:ee:ff>]
#                   [-mac_dst2_count <1-2147483647>]
#                   [-mac_dst2_mode  {fixed|increment|decrement}]
#                   [-mac_dst2_step  <1-255>]
#                   [-mac_src2       <aa:bb:cc:dd:ee:ff>]
#                   [-mac_src2_count <1-2147483647>]
#                   [-mac_src2_mode  {fixed|increment|decrement}]
#                   [-mac_src2_step  <1-255>]
#              -l2_encap   {ethernet_ii | ethernet_ii_vlan}
#                   [-mac_dst        <aa:bb:cc:dd:ee:ff>]
#                   [-mac_dst_count  <1-2147483647>]
#                   [-mac_dst_mode   {fixed|increment|decrement}]
#                   [-mac_dst_step   <1-255>]
#                   [-mac_src        <aa:bb:cc:dd:ee:ff>]
#                   [-mac_src_count  <1-2147483647>]
#                   [-mac_src_mode   {fixed|increment|decrement}]
#                   [-mac_src_step   <1-255>]
#                   [-length_mode    {fixed | random}]
#                        [-l3_length <40-16383>]
#                        [-l3_length_max  <40-16383>]
#                        [-l3_length_min  <40-16383>]
#                   [-vlan_cfi {0 | 1}]
#                   [-vlan_outer_cfi {0 | 1}]
#                   [-vlan_id  <0-4094>]
#                        [-vlan_id_count  <1-65535>]
#                        [-vlan_id_mode   {fixed|increment|decrement}]
#                        [-vlan_id_step   <1-255>]
#                        [-vlan_user_priority <0-7>]
#                        [-vlan_id_repeat ]
#                   [-vlan_id_outer <0-4095>]
#                        [-vlan_id_outer_mode {fixed|increment|decrement}]
#                        [-vlan_id_outer_count <1-4096>]
#                        [-vlan_id_outer_step <1-4095>]
#                        [-vlan_outer_user_priority <0-7>]
#                        [-vlan_id_outer_repeat <>]
#              -l2_encap {ethernet_ii_pppoe | ethernet_ii_vlan_pppoe |
#                        ethernet_ii_qinq_pppoe}
#              -l3_protocol  {ipv4 | ipv6}
#                   [-ip_bit_flags {0 | 1}]
#                   [-ip_checksum  {0 | 1}]
#                   [-ip_dscp  <0-63>]
#                   [-ip_dst_addr   <a.b.c.d>]
#                   [-ip_dst_count  <1-2147483647>]
#                   [-ip_dst_mode   {fixed|increment|decrement}]
#                   [-ip_dst_step   <a.b.c.d>]
#                   [-ip_fragment   {1|0}]
#                   [-ip_fragment_offset  <0-8191>]
#                   [-ip_hdr_length  <0-15>]
#                   [-ip_id <0-65535> ]
#                   [-ip_precedence <0-7> ]
#                   [-ip_precedence_count <integer>]
#                   [-ip_precedence_step <1-7> ]
#                   [-ip_protocol   <0-255>]
#                   [-ip_src_addr   <a.b.c.d>]
#                   [-ip_src_count  <1-2147483647>]
#                   [-ip_src_mode   {fixed|increment|decrement}]
#                   [-ip_src_step   <a.b.c.d>]
#                   [-ip_tos_field  <0-15>]
#                   [-ip_tos_count <integer>]
#                   [-ip_tos_step <1-15> ]
#                   [-ip_ttl        <0-255>]
#                   [-ipv6_dst_addr  <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#                   [-ipv6_dst_count <1-2147483647>]
#                   [-ipv6_dst_mode  {fixed|increment|decrement}]
#                   [-ipv6_dst_step  <1-65535>]
#                   [-ipv6_dstprefix_len <1-128>]
#                   [-ipv6_flow_label  <0-1048575 ]
#                   [-ipv6_hop_limit  <0-255> ]
#                   [-ipv6_length    <0-65535> ]
#                   [-ipv6_next_header <0-255> ]
#                   [-ipv6_src_addr  <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#                   [-ipv6_src_count <1-2147483647>]
#                   [-ipv6_src_mode  {fixed|increment|decrement}]
#                   [-ipv6_src_step  <1-65535>]
#                   [-ipv6_srcprefix_len <1-128>]
#                   [-ipv6_traffic_class <0-255> ]
#              -l3_outer_protocol  {ipv4 | ipv6}
#                   [-ip_dst_outer_addr   <a.b.c.d>]
#                   [-ip_dst_outer_count  <1-2147483647>]
#                   [-ip_dst_outer_mode   {fixed|increment|decrement}]
#                   [-ip_dst_outer_step   <a.b.c.d>]
#                   [-ip_fragment_outer_offset  <0-8191>]
#                   [-ip_hdr_outer_length  <0-15>]
#                   [-ip_outer_checksum  {0 | 1}]
#                   [-ip_outer_ttl        <0-255>]
#                   [-ip_outer_id <0-65535> ]
#                   [-ip_outer_protocol   <0-255>]
#                   [-ip_src_outer_addr   <a.b.c.d>]
#                   [-ip_src_outer_count  <1-2147483647>]
#                   [-ip_src_outer_mode   {fixed|increment|decrement}]
#                   [-ip_src_outer_step   <a.b.c.d>]
#                   [-ipv6_dst_outer_count <1-2147483647>]
#                   [-ipv6_dst_outer_mode  {fixed|increment|decrement}]
#                   [-ipv6_dst_outer_step  <1-65535>]
#                   [-ipv6_src_outer_count <1-2147483647>]
#                   [-ipv6_src_outer_mode  {fixed|increment|decrement}]
#                   [-ipv6_src_outer_step  <1-65535>]
#              -l4_protocol        {tcp | udp }
#                   [-tcp_src_port  <0-65535>]
#                   [-tcp_dst_port  <0-65535 }]
#                   [-tcp_ack_num   <^[0-9]+$>]
#                   [-tcp_reserved <0-63>]
#                   [-tcp_seq_num   <1-2147483647>]
#                   [-tcp_urgent_ptr <0-65535>]
#                   [-tcp_window    <0-65535>]
#                   [-tcp_ack_flag  {0|1}]
#                   [-tcp_fin_flag  {0|1}]
#                   [-tcp_psh_flag  {0|1}]
#                   [-tcp_rst_flag  {0|1}]
#                   [-tcp_syn_flag  {0|1}]
#                   [-tcp_urg_flag  {0|1}]
#                   [-udp_dst_port  <0-65535>]
#                   [-udp_src_port  <0-65535>]
#                   [-udp_checksum {0 | 1}]
#              [-transmit_mode   {continuous | continuous_burst | multi_burst |
#                   single_burst | single_pkt}]
#                   [-burst_loop_count <numeric>]
#                   [-rate_bps   <bits_per_second>]
#                   [-rate_percent <0.00 - 100.00>]
#                   [-rate_pps   <packets_per_second>]
#                   [-pkts_per_burst <1-16777215>]
#              [-mpls_labels "{
#                   [fec_type = none, label <0-104857> ] |
#                   [fec_type = ipv4, ip_addr = a.b.c.d]  |
#                   [fec_type = vpn_ipv4, route_dist = abcd:ab,
#                        route_tgt = abcd:ab, ip_addr = a.b.c.d ] |
#                   [fec_type = rsvp, lsp_handle <fec_lsp_handle> ] |
#                   [fec_type = vc, vc_id <0- 2147483647> ]
#                   }"
#              [-mac_discovery_gw <a.b.c.d>]
#                   [-ppp_link 0|1]
#                        [-ppp_link_traffic_src_list <session_block_handle>]
#                        [-downstream_traffic_src_list <session_block_handle>]
#                   [-ppp_session_id <integer>]
#                   [-dhcp_link 0|1]
#                        [-dhcp_downstream <session_block_handle>]
#                        [-dhcp_upstream <session_block_handle> ]
#
#                        [-enable_stream_only_gen 0|1]
#
# Arguments:
#
#    -bidirectional
#                   Sets up bidirectional traffic between the ports identified
#                   by the port_handle and port_handle2 arguments. Valid values
#                   are 0 and 1. Specify the value 1 to use bidirectional
#                   traffic. The default is 0.
#
#                   To configure the bidirectional flow, Spirent HLTAPI uses
#                   the Layer 3 protocol (IPv4 or IPv6) source and destination
#                   addresses for both ports. (See the -l3_protocol,
#                   -ip_src_addr, -ip_dst_addr, -ipv6_src_addr, and
#                   -ipv6_dst_addr arguments.) Spirent HLTAPI uses the
#                   source and destination addresses for the first port
#                   (-port_handle), and then swaps the addresses to use them for
#                   the second port (-port_handle2). Any additional values
#                   specified in the function call are duplicated for both
#                   transmitting ports.
#
#                   MAC addresses are handled in two ways:
#                   1) Spirent HLTAPI uses the addresses specified in the
#                   -mac_dst and -mac_dst2. The-mac_dst2 argument applies to the
#                   port associated with -port_handle2.
#
#                   2) If you do not specify MAC destination addresses, Spirent
#                   HLTAPI uses ARP (Address Resolution Protocol) to get the
#                   next hop MAC address from the gateway IP address specified
#                   in the call to the interface_config function.
#
#    -burst_loop_count
#                   Specifies the number of times to transmit a burst (that is,
#                   a continuous transfer of data without interruption from one
#                   device to another). The default is 1. Use this argument when
#                   transmit mode is set to either multi_burst, single_burst, or
#                   single_pkt. Set this argument to 1 if transmit mode is set
#                   to either single_burst or single_pkt.
#
#    -dhcp_downstream
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the DHCP session block handle from which to
#                   retrieve source IP addresses and creates dynamic downstream
#                   traffic. The sth::dhcp_config function returns this handle
#                   in the keyed list. The -dhcp_link argument must be set to 1.
#
#    -dhcp_link
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables or disables DHCP dynamic traffic. Valid values are 1
#                   and 0. Specify the value 1 to enable dynamic binding from
#                   the bound DHCP sessions. Specify the value 0 to disable DHCP
#                   dynamic traffic. The default is 0.
#
#                   Note: For both PPPoX and DHCP bound traffic, for subsequent
#                   connects and disconnect you do not have to delete and re-
#                   create traffic when adding new sessions. To disconnect and
#                   re-connect multiple PPPoX or DHCP sessions, you must stop
#                   and then restart traffic AFTER all new sessions have
#                   connected so the traffic configuration can get the newly
#                   updated session information. If you do not stop traffic, the
#                   old session information will not be replaced by the new one.
#
#    -dhcp_upstream
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the DHCP session block handle from which to
#                   retrieve source IP addresses and creates dynamic upstream
#                   traffic. The sth::dhcp_config function returns this handle
#                   in the keyed list. The -dhcp_link argument must be set to 1.
#
#    -downstream_traffic_src_list
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the PPPoX session block handle from which to
#                   retrieve the source IP addresses and use for the downstream
#                   bindings. The sth::pppox_config function returns this
#                   handle in the keyed list. If you use this option, you must
#                   set -ppp_link to 1.
#
#    -emulation_src_handle
#                   The handle used to retrieve information for L2 or L3
#                   IPv4 source addresses. This handle is returned by an 
#                   emulation configuration function such as 
#                   sth::emulation_bgp_config, sth::emulation_ospf_config, or
#                   sth::emulation_ldp_config. (The -emulation_src_handle 
#                   argument currently only supports BGP, OSPF, and LDP.)
#                   An emulation handle can be a host handle, a router handle, 
#                   or a router block handle.
#                   
#                   The following example creates a new stream block of traffic 
#                   on port2, uses the default source and default destination 
#                   MAC addresses for the stream as Ethernet II, retrieves the 
#                   IPv4 source address from the specified BGP route block 
#                   handle, and retrieves the IPv4 destination address from the 
#                   specified BGP route block handle:
#
#                   ::sth::traffic_config -mode create -port_handle port2\
#                        -l2_encap ethernet_ii\
#                        -length_mode fixed -l3_length 128 -l3_protocol ipv4 \
#                        -emulation_dst_handle $port1BgpRouter1RouteBlk1 \
#                        -emulation_src_handle $port2BgpRouter1RouteBlk2
#
#    -emulation_dst_handle
#                   The handle used to retrieve information for L2 or L3 IPv4
#                   destination addresses. This handle is returned by an 
#                   emulation configuration function such as 
#                   sth::emulation_bgp_config, sth::emulation_ospf_config, or
#                   sth::emulation_ldp_config. (The -emulation_src_handle 
#                   argument currently only supports BGP, OSPF, and LDP.)
#                   An emulation handle can be a host handle, a router handle, 
#                   or a router block handle. 
#
#                   The following example creates a new stream block of traffic 
#                   on port2, defines the source and destination MAC addresses 
#                   for the stream as Ethernet II, generates ten source IP 
#                   addresses for the stream block, uses the default source MAC 
#                   address and default destination MAC address, and retrieves
#                   the IPv4 destination address from the specified BGP route 
#                   block handle:
#
#                   ::sth::traffic_config -mode create -port_handle port2\
#                        -l2_encap ethernet_ii\
#                        -length_mode fixed \
#                        -l3_length 128\
#                        -l3_protocol ipv4\
#                        -ip_src_count 10\
#                        -ip_src_addr 150.111.0.22\
#                        -ip_src_step 0.0.0.1\
#                        -mac_discovery_gw 150.111.0.1\
#                        -mac_src 00.05.00.01.00.01\
#                        -emulation_dst_handle $port1BgpRouter1RouteBlk1
#
#    -ip_bit_flags
#                   Three-bit value flag field in the IP header for controlling
#                   whether routers are allowed to fragment a packet and to
#                   indicate whether the packet is the last fragment in a series
#                   of fragmented packets. Possible value are 0-7. The default
#                   is 0. You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_checksum
#                   Verifies that packets are not corrupted. Possible values are
#                   0 (not corrupted) and 1 (corrupted). The default is 0.
#                   You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_dscp
#                   Specifies the Differentiated Service Code Point (DSCP)
#                   precedence for a particular stream. The DSCP is made of the
#                   six most significant bits of the DiffServ field. Possible
#                   values are 0 to 7. The default is 0. You must specify
#                   IPv4 in the -l3_protocol argument. See RFC 2474 and 2475 for
#                   more information.
#
#    -ip_dst_addr
#                   Specifies the destination IPv4 address of the first
#                   generated packet. The default is 192.0.0.1. You must specify
#                   IPv4 in the -l3_protocol argument.
#
#    -ip_dst_count
#                   Specifies the number of destination IPv4 addresses to
#                   generate for a stream. Possible values range from 1 to
#                   2147483647. The default is 1. You must specify IPv4 in the
#                   -l3_protocol argument.
#
#    -ip_dst_mode
#                   Specifies how Spirent HLTAPI will assign the IPv4 IP
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The destination IP address is the same for all
#                   packets.
#
#                   increment - For all packets, the destination IP address
#                        increments by the step specified in the -ip_dst_step
#                        argument.
#
#                   decrement - For all packets, the destination IP address
#                        decrements by the step specified in the -ip_dst_step
#                        argument.
#
#                   You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_dst_step
#                   The amount by which to increment the specified IPv4
#                   destination IP address (-ip_dst_addr) for subsequent
#                   packets. The modifier is in the format of 0.0.0.0 for IPv4.
#                   See -ip_src_step for an example. You must specify IPv4 in
#                   the -l3_protocol argument.
#
#    -ip_dst_outer_addr
#                   Specifies the destination IPv4 address of the first
#                   generated packet in the outer header. The default is
#                   192.0.0.1. You must specify IPv4 in the -l3_protocol
#                   argument.
#
#    -ip_dst_outer_count
#                   Specifies the number of destination IPv4 addresses to
#                   generate for the outer header. Possible values range from 1
#                   to 2147483647. The default is 1. You must specify IPv4 in
#                   the -l3_protocol argument.
#
#    -ip_dst_outer_mode
#                   Specifies how Spirent HLTAPI will assign the IPv4 IP
#                   addresses for the outer header. Possible values are:
#
#                   fixed - The destination IP address is the same for all
#                   packets.
#
#                   increment - For all packets, the destination IP address
#                        increments by the step specified in the
#                        -ip_dst_outer_step argument.
#
#                   decrement - For all packets, the destination IP address
#                        decrements by the step specified in the
#                        -ip_dst_outer_step argument.
#
#                   You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_dst_outer_step
#                   The amount by which to increment the specified IPv4
#                   destination IP address (-ip_dst_outer_addr) for subsequent
#                   packets. The modifier is in the format of 0.0.0.0 for IPv4.
#                   See -ip_src_outer_step for an example. You must specify IPv4
#                   in the -l3_protocol argument.
#
#    -ip_fragment
#                   Specifies whether the datagram is fragmented. Possible
#                   values are 0 (not fragmented) and 1 (fragmented).
#                   Fragmentation is a method for dividing large packets into
#                   smaller packets at any point on a route between the source
#                   and destination. You must specify IPv4 in the -l3_protocol
#                   argument.
#
#    -ip_fragment_offset
#                   The byte count from the start of the original sent packet.
#                   If the IP packet is a fragment, the fragment offset
#                   indicates the location of the fragment in the final
#                   datagram. The fragment offset is measured in 8-octet
#                   increments (64 bits). Possible values range from 0 to 8191.
#                   The default is 0. You must specify IPv4 in the -l3_protocol
#                   argument.
#
#    -ip_fragment_outer_offset
#                   The byte count from the start of the original sent packet in
#                   the outer header. If the IP packet is a fragment, the
#                   fragment offset indicates the location of the fragment in
#                   the final datagram. The fragment offset is measured in
#                   8-octet increments (64 bits). Possible values range from 0
#                   to 8191. The default is 0. You must specify IPv4 in the
#                   -l3_protocol argument.
#
#    -ip_hdr_length
#                   The length of the IP header field in number of bytes.
#                   Possible values range from 0 to 15. The default is 5. This
#                   argument is mandatory because without it the receiver would
#                   not know where the TCP portion of the packet begins. You
#                   must specify IPv4 in the -l3_protocol argument.
#
#    -ip_hdr_outer_length
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The length of the outer IP header field in number of bytes.
#                   Possible values range from 0 to 15. The default is 5. This
#                   argument is mandatory because without it the receiver would
#                   not know where the TCP portion of the packet begins. You
#                   must specify IPv4 in the -l3_protocol argument.
#
#    -ip_id
#                   Specifies the identifying value used to help assemble the
#                   fragments of a datagram. Possible values range from 0 to
#                   65535. The default is 0. You must specify IPv4 in the
#                   -l3_protocol argument.
#
#    -ip_outer_checksum
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Verifies that packets in the outer header are not corrupted.
#                   Possible values are 0 (not corrupted) and 1 (corrupted). The
#                   default is 0. You must specify IPv4 in the -l3_protocol
#                   argument.
#
#    -ip_outer_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the identifying value used to help assemble the
#                   fragments of a datagram in the outer header. Possible values
#                   range from 0 to 65535. The default is 0. You must specify
#                   IPv4 in the -l3_protocol argument.
#
#    -ip_outer_protocol
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Indicates the type of L4 protocol in the outer header.
#                   Possible values range from 0 to 255. The default is 253.
#                   See -ip_protocol for descriptions of the possible values.
#
#    -ip_outer_ttl
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Sets the time-to-live (TTL) for the IP packet in the outer
#                   header. The TTL is a counter measured in units of seconds
#                   that gradually decrements to zero, at which point the
#                   datagram is discarded. Possible values are 0-255. The
#                   default is 64. You must specify IPv6 in the -l3_protocol
#                   argument.
#
#    -ip_precedence
#                   Configure the TOS three-bit Precedence field in the IP
#                   header. Possible values are 0 to 7. The default is 0. You
#                   must specify IPv4 in the -l3_protocol argument.
#
#                   Value     Description
#                     7       Network Control
#                     6       Internetwork Control
#                     5       CRITIC/ECP
#                     4       Flash Override
#                     3       Flash
#                     2       Immediate
#                     1       Priority
#                     0       Routine
#
#    -ip_precedence_count
#                   Specifies the number of values to use in increment mode.
#                   The default is 0. You must specify IPv4 in the -l3_protocol
#                   argument.
#
#                   Note: A large ip precedence count value can degrade
#                   performance. If it takes too long to create the stream, try
#                   reducing this count.
#
#    -ip_precedence_step
#                   Increment step to use in increment mode. Possible values are
#                   1 to 7. You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_protocol
#                   Indicates the type of L4 protocol in the IP header. Possible
#                   values range from 0 to 255. The default is 253.
#                   Possible values are:
#
#                   Value Description
#
#                   0     HOPOPT
#                   1     ICMP
#                   2     IGMP
#                   3     GGP
#                   4     IP
#                   5     ST
#                   6     TCP
#                   7     CBT
#                   8     EGP
#                   9     IGP
#                   10    BBN-RCC-MON
#                   11    NVP-II
#                   12    PUP
#                   13    ARGUS
#                   14    EMCON
#                   15    XNET
#                   16    CHAOS
#                   17    UDP
#                   18    MUX
#                   19    DCN-MEAS
#                   20    HMP
#                   21    PRM
#                   22    XNS-IDP
#                   23    TRUNK-1
#                   24    TRUNK-2
#                   25    LEAF-1
#                   26    LEAF-2
#                   27    RDP
#                   28    IRTP
#                   29    ISO-TP4
#                   30    NETBLT
#                   31    MFE-NSP
#                   32    MERIT-INP
#                   33    SEP
#                   34    3PC
#                   35    IDPR
#                   36    XTP
#                   37    DDP
#                   38    IDPR-CMTP
#                   39    TP++
#                   40    IL
#                   41    IPv6
#                   42    SDRP
#                   43    IPv6-Route
#                   44    IPv6-Frag
#                   45    IDRP
#                   46    RSVP
#                   47    GRE
#                   48    MHRP
#                   49    BNA
#                   50    ESP
#                   51    AH
#                   52    I-NLSP
#                   53    SWIPE
#                   54    NARP
#                   55    MOBILE
#                   56    TLSP
#                   57    SKIP
#                   58    IPv6-ICMP
#                   59    IPv6-NoNxt
#                   60    IPv6-Opts
#                   62    CFTP
#                   64    SAT-EXPAK
#                   65    KRYPTOLAN
#                   66    RVD
#                   67    IPPC
#                   69    SAT-MON
#                   70    VISA
#                   71    IPCV
#                   72    CPNX
#                   73    CPHB
#                   74    WSN
#                   75    PVP
#                   76    BR-SAT-MON
#                   77    SUN-ND
#                   78    WB-MON
#                   79    WB-EXPAK
#                   80    ISO-IP
#                   81    VMTP
#                   82    SECURE-VMTP
#                   83    VINES
#                   84    TTP
#                   85    NSFNET-IGP
#                   86    DGP
#                   87    TCF
#                   88    EIGRP
#                   89    OSPFIGP
#                   90    Sprite-RPC
#                   91    LARP
#                   92    MTP
#                   93    AX.25
#                   94    IPIP
#                   95    MICP
#                   96    SCC-SP
#                   97    ETHERIP
#                   98    ENCAP
#                   100   GMTP
#                   101   IFMP
#                   102   PNNI
#                   103   PIM
#                   104   ARIS
#                   105   SCPS
#                   106   QNX
#                   107   A/N
#                   108   IPComp
#                   109   SNP
#                   110   Compaq-Peer
#                   111   IPX-in-IP
#                   112   VRRP
#                   113   PGM
#                   115   L2TP
#                   116   DDX
#                   117   IATP
#                   118   STP
#                   119   SRP
#                   120   UTI
#                   121   SMP
#                   122   SM
#                   123   PTP
#                   124   ISIS over IPv4
#                   125   FIRE
#                   126   CRTP
#                   127   CRUDP
#                   128   SSCOPMCE
#                   129   IPLT
#                   130   SPS
#                   131   PIPE
#                   132   SCTP
#                   133   FC
#                   134   RSVP-E2E-IGNORE
#                   135   Mobility Header
#                   136   UDPLite
#                   137   MPLS-in-IP
#                   253   Experimental
#                   255   Reserved
#
#                   You must specify IPv4 in the -l3_protocol argument.
#
#    -ip_src_addr
#                   Specifies the source IPv4 address of the first generated
#                   packet. The default is 0.0.0.0. You must specify IPv4 in the
#                   -l3_protocol argument.
#
#    -ip_src_count
#                   The number of source IP addresses to generate for a stream.
#                   Possible values range from 1 to 2147483647. The default is
#                   1.
#
#    -ip_src_outer_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the source IPv4 address of the first generated
#                   packet in the outer header. The default is 0.0.0.0. You
#                   must specify IPv4 in the -l3_protocol argument.
#
#    -ip_src_outer_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The number of source IP addresses to generate for a stream
#                   in the outer header. Possible values range from 1 to
#                   2147483647. The default is 1.
#
#    -ip_src_outer_mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies how Spirent HLTAPI will assign the IP
#                   addresses for the outer header. Possible values are:
#
#                   fixed - The source IP address is the same for all packets.
#
#                   increment - For all packets, the source IP address
#                        increments by the step specified in the
#                        -ip_src_outer_step argument.
#
#                   decrement - For all packets, the source IP address
#                        decrements by the step specified in the
#                        -ip_src_outer_step argument.
#
#    -ip_src_mode
#                   Specifies how Spirent HLTAPI will assign the IP
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The source IP address is the same for all packets.
#
#                   increment - For all packets, the source IP address
#                        increments by the step specified in the -ip_src_step
#                        argument.
#
#                   decrement - For all packets, the source IP address
#                        decrements by the step specified in the -ip_src_step
#                        argument.
#
#    -ip_src_step
#                   Indicates both the step value and the prefix length that
#                   Spirent HLTAPI applies to the specified source address
#                   (-ip_src_addr). The format of the ip_src_step value is an
#                   IPv4 address, for example, 0.0.1.0. Use a single decimal
#                   digit equal to a power of 2; the remaining three digits must
#                   be zero (0). The numeric value identifies a bit location in
#                   the address; the location determines the prefix length.
#                   Spirent HLTAPI also uses the value to increment the host
#                   ID portion of the address.
#
#                   For example, if you specify 0.0.8.0 for the -ip_src_step
#                   argument, then the step value is 8 and the prefix length is
#                   21. However, if you specify 0.8.0.0, then the step value is
#                   8 but the prefix length is 13.
#
#                   sth::traffic_config -mode create {other needed switches} \
#                                       -ip_src_addr 10.100.20.5 \
#                                       -ip_src_mode increment \
#                                       -ip_src_step 0.8.0.0 \
#                                       -ip_src_count 5
#
#    -ip_tos_count
#                   Specifies the number of times the value will change before
#                   reverting to the initial value. The default is 0. You must
#                   specify IPv4 in the -l3_protocol argument.
#
#    -ip_tos_field
#                   Sets the four-bit type of service (ToS) field in the IP
#                   header. The ToS field specifies the priority of the packet.
#                   Possible values range from 0 to 15. The default is 0. You
#                   must specify Ipv4 in the -l3_protocol argument.
#
#    -ip_tos_step
#                   Specifies the number of values to use in increment mode.
#                   Possible values range from 1 to 15. The default is 0. You
#                   must specify IPv4 in the -l3_protocol argument.
#
#    -ip_ttl
#                   Sets the time-to-live (TTL) for the IP packet. The TTL is a
#                   counter measured in units of seconds that gradually
#                   decrements to zero, at which point the datagram is
#                   discarded. Possible values are 0-255. The default is 64. You
#                   must specify IPv6 in the -l3_protocol argument.
#
#    -ipv6_dst_addr
#                   The destination IPv6 address of the first generated packet.
#                   The default is fe80:0:0:0:0:0:0:22. You must specify IPv6
#                   in the -l3_protocol argument.
#
#    -ipv6_dst_count
#                   The number of destination IPv6 addresses to generate for a
#                   stream. Possible values range from 1 to 2147483647. The
#                   default is 1. You must specify IPv6 in the -l3_protocol
#                   argument.
#
#    -ipv6_dst_mode
#                   Specifies how Spirent HLTAPI will assign the Ipv6
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The destination Ipv6 address is the same for all
#                        packets.
#
#                   increment - For all packets, the destination Ipv6 address
#                        increments by the step specified in the -ipv6_dst_step
#                        argument.
#
#                   decrement - For all packets, the destination Ipv6 address
#                        decrements by the step specified in the -ipv6_dst_step
#                        argument.
#
#                   You must specify Ipv6 in the -l3_protocol argument.
#
#    -ipv6_dst_step
#                   The amount by which to increment the specified IPv6
#                   destination IP address (-ip_dst_addr) for subsequent
#                   packets. Possible values range from 1 to 65535. The default
#                   is 1. You must specify IPv6 in the -l3_protocol argument.
#
#    -ipv6_dst_outer_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The number of destination IPv6 addresses to generate for the
#                   outer header. Possible values range from 1 to 2147483647.
#                   The default is 1. You must specify IPv6 in the -l3_protocol
#                   argument.
#
#    -ipv6_dst_outer_mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies how Spirent HLTAPI will assign the Ipv6
#                   addresses for the outer header. Possible values are:
#
#                   fixed - The destination Ipv6 address is the same for all
#                        packets.
#
#                   increment - For all packets, the destination Ipv6 address
#                        increments by the step specified in the
#                        -ipv6_dst_outer_step argument.
#
#                   decrement - For all packets, the destination Ipv6 address
#                        decrements by the step specified in the
#                        -ipv6_dst_outer_step argument.
#
#                   You must specify Ipv6 in the -l3_protocol argument.
#
#    -ipv6_dst_outer_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The amount by which to increment the specified IPv6
#                   destination IP address (-ip_dst_outer_addr) for subsequent
#                   packets. Possible values range from 1 to 65535. The default
#                   is 1. You must specify IPv6 in the -l3_protocol argument.
#
#    -ipv6_dstprefix_len
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the prefix length of the destination IPv6 address.
#                   Possible values range from 1 to 128. The default is 64.
#
#    -ipv6_flow_label
#                   The flow label value of the IPv6 stream, which is a twenty-
#                   bit field used for QoS management. Typical packets not
#                   associated with a particular flow, but which require special
#                   treatment are set to 0. Possible values range from 0 to
#                   1048575, The default is 0.
#
#    -ipv6_hop_limit
#                   The hop limit field in the IPv6 header, which is an eight-
#                   bit field similar to TTL in IPv4. Possible values range from
#                   0 to 255. The default is 64.
#
#    -ipv6_length
#                   The two-byte payload length field in the IPv6 header.
#                   Possible values range from 0 to 65535. The default is 128.
#
#    -ipv6_next_header
#                   The next header field in the IPv6 header. For datagrams with
#                   extension headers, this field specifies the identity of the
#                   first extension header, which is the next header in the
#                   datagram. Possible values range from 0 to 255. The default
#                   is 59.
#
#    -ipv6_src_addr
#                   Specifies the source IPv6 address of the first generated
#                   packet. The default is fe80:0:0:0:0:0:0:12. You must specify
#                   IPv6 in the -l3_protocol argument.
#
#    -ipv6_src_count
#                   The number of source IPv6 addresses to generate for a
#                   stream. Possible values range from 1 to 2147483647. The
#                   default is 1.
#
#    -ipv6_src_mode
#                   Specifies how Spirent HLTAPI will assign the Ipv6
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The source IP address is the same for all packets.
#
#                   increment - For all packets, the source IP address
#                        increments by the step specified in the
#                        -ip_src_step argument.
#
#                   decrement - For all packets, the source IP address
#                        decrements by the step specified in the
#                        -ip_src_step argument.
#
#                   You must specify Ipv6 in the -l3_protocol argument.
#
#    -ipv6_src_step
#                   The amount by which to increment the specified IPv6
#                   source IP address (-ip_src_addr) for subsequent
#                   packets. Possible values range from 1 to 65535. The default
#                   is 1.
#
#    -ipv6_src_outer_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The number of source IPv6 addresses to generate for the
#                   outer header. Possible values range from 1 to 2147483647.
#                   The default is 1.
#
#    -ipv6_src_outer_mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies how Spirent HLTAPI will assign the Ipv6
#                   addresses for the outer header. Possible values are:
#
#                   fixed - The source IP address is the same for all packets.
#
#                   increment - For all packets, the source IP address
#                        increments by the step specified in the
#                        -ip_src_outer_step argument.
#
#                   decrement - For all packets, the source IP address
#                        decrements by the step specified in the
#                        -ip_src_outer_step argument
#
#                   You must specify Ipv6 in the -l3_protocol argument.
#
#    -ipv6_src_outer_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The amount by which to increment the specified IPv6
#                   source IP address (-ip_src_outer_addr) for subsequent
#                   packets. Possible values range from 1 to 65535. The default
#                   is 1.
#
#    -ipv6_srcprefix_len
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the prefix length of the source IPv6 address.
#                   Possible values range from 1 to 128. The default is 64.
#
#
#    -ipv6_traffic_class
#                   The traffic class field in the IPv6 header, which is an
#                   eight-bit field that describes the packet's priority. This
#                   value is used at the application layer. Possible values
#                   range from 0 to 255. The default is 0.
#
#    -l2_encap
#                   Identifies the type of Layer2 encapsulation to use to define
#                   source and destination MAC addresses for a stream. Possible
#                   values are ethernet_ii_pppoe, ethernet_ii_vlan_pppoe, and
#                   ethernet_ii_qinq_pppoe.
#
#                   The ethernet_ii_vlan option supports VLAN tagging on 
#                   Ethernet networks; ethernet_ii does not. If you use the 
#                   -vlan_* arguments to define a VLAN interface, you must set 
#                   the L2 encapsulation type to ethernet_ii_vlan.
#
#    -l3_length
#                   Sets the stream frame size in bytes. To set the frame
#                   size, the -length_mode argument must be set to fixed.
#                   Possible values range from 40 to 16383. The default is 128.
#
#    -l3_length_max
#                   Sets the maximum frame length in bytes. Use this argument
#                   when -length_mode is set to random. Possible values range
#                   from 40 to 16383. The default is 256.
#
#    -l3_length_min
#                   Sets the minimum frame length in bytes. Use this argument
#                   when -length_mode is set to random. Possible values range
#                   from 40 to 16383. The default is 128.
#
#    -l3_protocol
#                   Identifies the Layer3 protocol to use when creating packets.
#                   Possible values are IPv4 and IPv6. This argument is
#                   mandatory for the sth::traffic_config function.
#
#                   IPv4 uses 32-bit addresses, generally represented in dotted
#                   decimal notation (for example, 10.10.100.1). IPv6 use 128-
#                   bit addresses, normally written as eight groups of up to
#                   four hexadecimal digits, separated by colons (for example,
#                   1001:0ac8:11a1:02e1:2244:3a2e:8260:6443).
#
#    -l3_outer_protocol
#                   Identifies the Layer3 protocol to use when creating packets
#                   for the outer header. Possible values are IPv4 and IPv6.
#
#    -l4_protocol
#                   Identifies the Layer4 protocol to use as a transport
#                   service. Possible values are TCP and UDP.
#
#                   When you define a TCP header object, you can define the
#                   source and destination ports for the traffic, control bits
#                   to specify TCP segments (FIN, SYN, RST, PSH, ACK, URG), ACK,
#                   SEQ, and window attributes, and TCP frame length and urgent
#                   data pointer values.
#
#                   A UDP header contains fields that specify the source and
#                   destination ports, the length, and the checksum. When you
#                   create a UDP header object, you define the source and
#                   destination ports and the length of the combined UDP header
#                   and data.
#
#    -length_mode
#                   Specifies how Spirent HLTAPI generates the size of each
#                   packet. Possible values are fixed and random. The default is
#                   fixed.
#
#                   In fixed mode, all frames in a stream have the same length.
#                   If you set the length mode to "fixed", use the -l3_length
#                   argument to specify the size of each frame. In fixed mode,
#                   the frames are fixed per stream, so fixed mode applies to
#                   only one stream. All frames for that stream will have a
#                   fixed frame size.
#
#                   In random mode, the frames have variable lengths. If you set
#                   the length mode to "random", use the -l3_length_min and
#                   l3_length_max arguments to specify the minimum and maximum
#                   size of each frame. Because "random" applies to the entire
#                   port, not per stream, Spirent HLTAPI will generate
#                   frame sizes within the range last specified. The most recent
#                   random mode range specification affects all random mode
#                   streams defined for a port.
#
#                   For example, suppose you have four streams of traffic coming
#                   out of the same port but with the following settings:
#
#                   stream 1: -length mode fixed -l3_length 64
#                   stream 2: -length mode random -l3_length_min 128
#                             -l3_length_max 256
#                   stream 3: -length mode random-l3_length_min 60
#                             -l3_length_max 150
#                   stream 4: -length mode fixed -l3_length 128
#
#                   In the above example, stream 1 is 64 bytes, stream 2 ranges
#                   between 60 and 150 bytes, stream 3 is 128 bytes, and stream
#                   4 ranges between 60 and 150 bytes.
#
#    -mac_discovery_gw
#                   Specify the gateway for the stream, so you can send an ARP
#                   for this stream. You must also enable the ARP send request
#                   (sth::interface_config -arp_send_req 1), and then call
#                   sth::traffic_control -action run -port_handle $porthandle
#                   send the ARP. ARP is sent each time you call this function.
#
#                   Spirent HLTAPI 2.00 requires that you set -mac_discovery_gw
#                   for each stream. You must also specify ethernet_ii in the
#                   -l2_encap argument.
#
#                   Note: The -mac_discovery_gw attribute did not exist in
#                   Spirent HLTAPI 1.3; therefore, version 1.3 did not require
#                   setting this attribute.
#
#    -mac_dst
#                   Specifies the destination MAC address for the port. The
#                   default is 00-00-00-00-00-00.
#
#    -mac_dst_count
#                   The number of destination MAC addresses to generate for a
#                   particular stream. Possible values are 1 to 2147483647. The
#                   default is 1.
#
#    -mac_dst_mode
#                   Specifies how Spirent HLTAPI will assign the destination
#                   MAC addresses for a particular stream. Possible values are:
#
#                   fixed - The destination MAC address is the same for all
#                   packets.
#
#                   increment - For all packets, the destination MAC address
#                        increments by the step specified in the -mac_dst_step
#                        argument.
#
#                   decrement - For all packets, the destination MAC address
#                        decrements by the step specified in the -mac_dst_step
#                        argument
#
#                   This attribute is mandatory. You must set it for each stream.
#                   You must also set -mac_discovery_gw for each stream.
#
#    -mac_dst_step
#                   The amount by which to increment the specified destination
#                   MAC address (-mac_dst) for subsequent packets. Possible
#                   values range from 1 to 255, expressed as a power-of-two
#                   value (1,2,4,8,16...). The default is 1.
#    -mac_dst2
#                   Specifies the destination MAC address for the port specified
#                   in -port-handle2. The default is 00-00-00-00-00-00.
#
#    -mac_dst2_count
#                   The number of destination MAC addresses to generate for a
#                   particular stream. Possible values are 1 to 2147483647. The
#                   default is 1.
#
#    -mac_dst2_mode
#                   Specifies how Spirent HLTAPI will assign the destination
#                   MAC addresses for a particular stream. Possible values are:
#
#                   fixed - The destination MAC address is the same for all
#                   packets.
#
#                   increment - For all packets, the destination MAC address
#                        increments by the step specified in the -mac_dst2_step
#                        argument.
#
#                   decrement - For all packets, the destination MAC address
#                        decrements by the step specified in the -mac_dst2_step
#                        argument
#
#    -mac_dst2_step
#                   The amount by which to increment the specified destination
#                   MAC address (-mac_dst) for subsequent packets. Possible
#                   values range from 1 to 255, expressed as a power-of-two
#                   value (1,2,4,8,16...). The default is 1.
#
#    -mac_src
#                   Specifies the source MAC address for the port. The default
#                   is 00-00-01-00-00-01.
#
#    -mac_src_count
#                   The number of the source MAC addresses to generate for a
#                   particular stream. The default is 1.
#
#    -mac_src_mode
#                   Specifies how Spirent HLTAPI will assign the source MAC
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The source MAC address is the same for all packets.
#
#                   increment - For all packets, the source MAC address
#                        increments by the step specified in the -mac_src_step
#                        argument.
#
#                   decrement - For all packets, the source MAC address
#                        decrements by the step specified in the -mac_src_step
#                        argument
#
#    -mac_src_step
#                   The amount by which to increment the specified source MAC
#                   address (-mac_src) for subsequent packets. Possible values
#                   range from 1 to 255, expressed as a power-of-two value
#                   (1,2,4,8,16...). The default is 1.
#
#    -mac_src2
#                   Specifies the source MAC address for the port specified
#                   in -port-handle2. The default is 00-00-01-00-00-01.
#
#    -mac_src2_count
#                   The number of the source MAC addresses to generate for a
#                   particular stream. The default is 1.
#
#    -mac_src2_mode
#                   Specifies how Spirent HLTAPI will assign the source MAC
#                   addresses for a particular stream. Possible values are:
#
#                   fixed - The source MAC address is the same for all packets.
#
#                   increment - For all packets, the source MAC address
#                        increments by the step specified in the -mac_src2_step
#                        argument.
#
#                   decrement - For all packets, the source MAC address
#                        decrements by the step specified in the -mac_src2_step
#                        argument.
#
#    -mac_src2_step
#                   The amount by which to increment the specified source MAC
#                   address (-mac_src) for subsequent packets. Possible values
#                   range from 1 to 255, expressed as a power-of-two value
#                   (1,2,4,8,16...). The default is 1.
#
#    -mode
#                   Specifies the action to perform. Possible values are create,
#                   disable, enable, modify, remove, or reset. The modes are
#                   described below:
#
#                   create -  Creates a new stream block of traffic for the
#                             specified port. If you enable bidirectional
#                             traffic, Spirent HLTAPI creates two stream
#                             blocks between the specified ports, one for each
#                             direction of traffic. This argument is mandatory
#                             for the sth::traffic_config function. This mode
#                             returns the stream ID (stream_id).
#                             Example:
#                             traffic_config -mode create -port_handle $port1
#
#                   disable - Deactivates the existing stream blocks for the
#                             specified port(s). Same as "-mode remove".
#                             Example:
#                             traffic_config -mode disable -stream_id {list} \
#                             -port_handle $port1
#
#                   enable -  Activates the existing stream blocks for the
#                             specified port(s).
#                             Example:
#                             traffic_config -mode enable -stream_id {list} \
#                             -port_handle $port1
#
#                   modify -  Modifies the existing stream block for the
#                             specified port(s).
#                             Example:
#                             traffic_config -mode modify -stream_id {list} \
#                             -port_handle $port1
#
#                   remove -  Deactivates the existing stream blocks for the
#                             specified port(s). Same as "-mode disable".
#                             Example:
#                             traffic_config -mode remove -stream_id {list} \
#                             -port_handle $port1
#
#                   reset -   Deletes all of the existing stream blocks from the
#                             system.
#                             Example: traffic_config -mode reset
#
#                   Note: For both PPPoX and DHCP bound traffic, for subsequent
#                   connects and disconnect you do not have to delete and re-
#                   create traffic when adding new sessions. To disconnect and
#                   re-connect multiple PPPoX or DHCP sessions, you must stop
#                   and then restart traffic AFTER all new sessions have
#                   connected so the traffic configuration can get the newly
#                   updated session information. If you do not stop traffic, the
#                   old session information will not be replaced by the new one.
#
#    -mpls_labels
#                   The value of the MPLS label. Depending on which FEC type you
#                   specify, this label contains a list of parameters. Possible
#                   values for FEC types are as follows:
#
#                   none -    None. If you specify "none", you must also specify
#                             the label parameter.
#
#                             label - The explicit value of the MPLS label.
#                             Possible values range from 0 to 1048575. The
#                             default is 16.
#
#                   ipv4 -    IP version 4. If you specify "ipv4", you must also
#                             specify the FEC IP address as ip_addr = a.b.c.d.
#                             The default FEC IP address is 1.1.1.1.
#
#                   vpn_ipv4 - IP version 4 VPN. If you specify "vpn_ipv4", you
#                              must also specify the route distribution
#                             (route_dist), route target (route_tgt).and IP
#                             address parameters.
#
#                             route_dist - VPLS FEC. Included in the BGP NLRI
#                             for VPLS. Specifies the route distinguisher for
#                             the VPLS route,
#
#                             route_tgt - Identifies the VPLS to which a route
#                             belongs. This association allows the route to be
#                             placed in the appropriate VRF(s).
#
#                   rsvp -    RSVP. If you specify "rsvp", you must also specify
#                             the FEC RSVP LSP handle (lsp_handle).
#
#                   vc -      Virtual circuit. If you specify "vc", you must
#                             also specify the FEC VC ID (vc_id). Possible
#                             values range from 0 to 2147483647. The default is
#                             1.
#
#                   The default is none. Spirent HLTAPI supports multiple
#                   MPLS labels in a single packet.
#
#                   Here's an example of a port 1 stream configuration using
#                   MPLS labels:
#
#                   sth::traffic_config
#                             -mode create \
#                             -port_handle   $hPort($device.4/0) \
#                             -l2_encap      ethernet_ii_unicast_mpls \
#                             -mpls_labels   "{fec_type = vpn_ipv4, \
#                                  route_dist = 1212:10, route_tgt = 1212:10, \
#                                  ip_addr = 78.14.0.10}" \
#                             -l3_protocol   ipv4 \
#                             -l3_length     256 \
#                             -length_mode   fixed \
#                             -ip_src_addr   79.13.1.10 \
#                             -ip_src_mode   fixed \
#                             -ip_dst_addr   78.14.0.10 \
#                             -ip_dst_mode   fixed
#
#    -pkts_per_burst
#                   Sets the number of packets each port transmits in a single
#                   burst. Possible values are 1 - 16777215. The default is 1.
#                   You must specify a value equal to 1 for continuous mode
#                   and greater than 1 for continous_burst mode. You
#                   can only use this argument with Gigabit and higher Ethernet
#                   speeds in half-duplex mode.
#
#    -port_handle
#                   Specifies the handle for the port to be configured. The
#                   port_handle value uniquely identifies a port on a chassis.
#                   The port_handle value is obtained when you connect to the
#                   chassis (see the description of the connect function).
#                   Spirent HLTAPI will use this port to transmit
#                   traffic. This argument is mandatory for the
#                   sth::traffic_config function.
#
#    -port_handle2
#                   Specifies the handle for the second port for bidirectional
#                   traffic. This port is the source of the reverse stream of
#                   traffic. Use this argument only when bidirectional traffic
#                   is enabled. (See the description of the -bidirectional
#                   argument.)
#
#    -ppp_link
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables or disables PPPoX dynamic traffic. Valid values are
#                   1 and 0. Specify the value 1 to enable dynamic binding from
#                   the bound PPPoX sessions. Specify the value 0 to disable
#                   PPPoX dynamic traffic. The default is 0. The -l2_encap
#                   argument must be set to ethernet_ii_pppoe,
#                   ethernet_ii_vlan_pppoe, or ethernet_ii_qinq_pppoe.
#
#                   Note: For both PPPoX and DHCP bound traffic, for subsequent
#                   connects and disconnect you do not have to delete and re-
#                   create traffic when adding new sessions. To disconnect and
#                   re-connect multiple PPPoX or DHCP sessions, you must stop
#                   and then restart traffic AFTER all new sessions have
#                   connected so the traffic configuration can get the newly
#                   updated session information. If you do not stop traffic, the
#                   old session information will not be replaced by the new one.
#
#    -ppp_link_traffic_src_list
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the PPPoX session block handle from which to
#                   retrieve source IP addresses and creates dynamic upstream
#                   traffic. The sth::pppox_config function returns this
#                   handle in the keyed list. If you use this option, you must
#                   set -ppp_link to 1.
#
#    -ppp_session_id
#                   Specifies the PPPoE session ID. This argument requires
#                   the -l2_encap argument to be set to ethernet_ii_pppoe,
#                   ethernet_ii_vlan_pppoe, or ethernet_ii_qinq_pppoe. Possible
#                   values range from 0 to 65535. If you specify a PPPoE session
#                   ID, do not use the -ppp_link or -ppp_link_traffic_src_list
#                   arguments.
#
#    -rate_bps
#                   The traffic transmission rate in bits per second.
#
#    -rate_percent
#                   The traffic transmission rate specified as a percent of the
#                   line rate for the specified stream. Possible values are
#                   between 0.00 and 100.00, inclusive. The default is 100.00.
#
#    -rate_pps
#                   The traffic transmission rate in packets per second. This
#                   value refers to the packet rate of a given packet size that
#                   will load up an interface to 100%.
#
#    -stream_id
#                   A handle that identifies a stream. Use this argument to
#                   modify or remove an existing stream. Spirent HLTAPI
#                   creates and returns a stream ID when you configure traffic
#                   (sth::traffic_config -mode create). If you create
#                   bidirectional traffic, Spirent HLTAPI creates and
#                   returns two stream IDs. (Each direction of the stream must
#                   have a unique ID.)
#
#    -tcp_ack_flag
#                   Indicates whether the data identified by the sequence number
#                   has been received. Possible values are 0 and 1. The default
#                   is 0. You must specify TCP in the -l4_protocol argument.
#
#    -tcp_ack_num
#                   Identifies the next expected TCP octet. Possible values are
#                   1 to 2147483647. The default is 1. You must specify TCP in
#                   the -l4_protocol argument.
#
#    -tcp_dst_port
#                   Specifies the port on the receiving TCP module. Possible
#                   values range from 0 to 65535. The default is 80. You must
#                   specify TCP in the -l4_protocol argument.
#
#    -tcp_fin_flag
#                   Indicates whether a connection is terminated. Possible
#                   values are 0 and 1. The default is 0. Once the data transfer
#                   is complete, the host sends a packet with the FIN and ACK
#                   flags set. The FIN flag is then set to 1, while the ACK flag
#                   is set to 0. You must specify TCP in the -l4_protocol
#                   argument.
#
#    -tcp_psh_flag
#                   Indicates whether to ensure that the data is given the
#                   appropriate priority and is processed at the sending or
#                   receiving end. Possible values are 0 and 1. The default is
#                   0. You must specify TCP in the -l4_protocol argument.
#
#    -tcp_reserved
#                   Reserves TCP bits. The default is 0. You must specify TCP in
#                   the -l4_protocol argument.
#
#    -tcp_rst_flag
#                   Resets the connection when a segment arrives that is not
#                   intended for the current connection. Possible values are 0
#                   and 1. The default is 0. You must specify TCP in the
#                   -l4_protocol argument.
#
#    -tcp_seq_num
#                   Identifies the position of the data within the data stream.
#                   Possible values are 1 to 2147483647. The default is 1. You
#                   must specify TCP in the -l4_protocol argument.
#
#    -tcp_src_port
#                   Specifies the port on the sending TCP module. Possible
#                   values range from 0 to 65535. The default is 1024. You must
#                   specify TCP in the -l4_protocol argument.
#
#    -tcp_syn_flag
#                   Indicates whether the port is open for connection. Possible
#                   values are 0 and 1. A value of 1 indicates the port has
#                   established a connection. The default is 0. You must specify
#                   TCP in the -l4_protocol argument.
#
#    -tcp_urg_flag
#                   Identifies the incoming data as "urgent," giving it priority
#                   over the other segments. Possible values are 0 and 1. The
#                   default is 0. You must specify TCP in the -l4_protocol
#                   argument.
#
#    -tcp_urgent_ptr
#                   Specifies the position in the segment where urgent data
#                   ends. Possible values range from 0 to 65535. The default is
#                   0.
#
#    -tcp_window
#                   Specifies the number of bytes that can be sent
#                   simultaneously (within the window). In the TCP header, this
#                   field is used by the receiver to indicate to the sender the
#                   amount of data that it is able to accept. Possible values
#                   are 0 to 65535. The default is 4069.
#
#    -transmit_mode
#                   Defines the mode of transmission of the packets (as a part
#                   of the stream). Possible values are continuous,
#                   continuous_burst, multi_burst, single_burst, and single_pkt.
#                   The default is continuous. When calling this argument in
#                   either mode, the following arguments are mandatory:
#
#                   1. -rate_bps, -rate_pps, or -rate_percent (if you do not
#                       specify one of these arguments, Spirent HLTAPI uses
#                       the Spirent HLTAPI default (10% line rate)
#                   2. -length_mode
#                   3. -l3_length or l3_length_min and l3_length_max
#                   4. -pks_per_burst
#
#                   Note: The -pkts_per_burst argument must be equal to 1
#                   for continuous mode and greater than or equal to 1 for
#                   continuous_burst mode. For multi_burst mode, the
#                   -burst_loop_count argument is mandatory. If you do not
#                   specify it, Spirent HLTAPI will use the default value
#                   which is 30. For single_burst mode, the -burst_loop_count
#                   argument always defaults to 1. For single_pkt mode,
#                   both the -burst_loop_count and -pkts_per_burst arguments
#                   always default to 1.
#
#    -udp_checksum
#                   Verifies that packets are not corrupted. Possible values are
#                   0 (not corrupted) and 1 (corrupted). The default is 0.
#                   You must specify UDP in the -l4_protocol argument.
#
#    -udp_dst_port
#                   Defines the destination TCP port number. Possible values
#                   range from 0 to 65535. The default is 80. You must specify
#                   UDP in the -l4_protocol argument.
#
#    -udp_src_port
#                   Defines the source UDP port number. Possible values range
#                   from 0 to 65535. The default is 1024. You must specify UDP
#                   in the -l4_protocol argument.
#
#    -vlan_cfi
#                   Specifies whether the canonical format indicator (cfi) value
#                   is set for the VLAN header. Possible values are 0 or
#                   1. You must set the -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_outer_cfi
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies whether the canonical format indicator (cfi) value
#                   is set for the VLAN outer header. Possible values are 0 or
#                   1. You must set the -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id
#                   Specifies the VLAN ID for a particular stream. Possible
#                   values range from 0 to 4094. You must set the
#                   -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id_count
#                   Specifies the number of VLAN tags to generate for the
#                   stream. Possible values range from 1 to 65535. The
#                   default is 1. You must set the -vlan_id_mode argument to
#                   increment and the -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id_mode
#                   Specifies how Spirent Test Center will assign VLAN tags to
#                   packets in a particular stream. Possible values are:
#
#                   fixed - The VLAN ID is the same for all packets.
#
#                   increment - For all packets, the VLAN tag ID increments by
#                        the step specified in the -vlan_id_step argument.
#
#                   decrement - For all packets, the VLAN tag ID decrements by
#                        the step specified in the -vlan_id_step argument.
#
#                   You must set the -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id_step
#                   The amount by which to increment the specified VLAN ID
#                   (-vlan_id) for subsequent packets. The step must be equal to
#                   a value of 2 for the step to increment or decrement
#                   properly. Possible values range from 1 to 255 (see below).
#                   The default is 0. You must set the -l2_encap argument to
#                   ethernet_ii_vlan.
#
#                   2(1) = 2
#                   2(2) = 4
#                   2(4) = 16
#                   2(8) = 256
#                   2(16) = 65,536
#                   2(32) = 4,294,967,296
#                   2(64) = 18,446,744,073,709,551,616
#                   2(128) = 340,282,366,920,938,463,463,374,607,431,768,211,456
#                   2(256) = 115,792,089,237,316,195,423,570,985,008,687,907,
#                            853,269, 984,665,640,564,039, 457,584,007,913,129,
#                            639,936
#
#  -vlan_id_repeat
#               Specifies the number of times the value will be repeated
#
#    -vlan_id_outer
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the VLAN ID for a particular outer header.
#                   Possible values range from 0 to 4094. You must set the
#                   -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id_outer_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the number of VLAN tags to generate for the
#                   outer header. Possible values range from 1 to 65535.
#                   The default is 1. You must set the -vlan_id_outer_mode
#                   argument to increment and the -l2_encap argument to
#                   ethernet_ii_vlan.
#
#    -vlan_id_outer_mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies how Spirent Test Center will assign VLAN tags to
#                   packets in the specified outer header. Possible values are:
#
#                   fixed - The outer VLAN ID is the same for all packets.
#
#                   increment - For all packets, the outer VLAN tag ID
#                        increments by the step specified in the
#                        -vlan_id_outer_step argument.
#
#                   decrement - For all packets, the outer VLAN tag ID
#                        decrements by the step specified in the
#                        -vlan_id_outer_step argument.
#
#                   You must set the -l2_encap argument to ethernet_ii_vlan.
#
#    -vlan_id_outer_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The amount by which to increment the specified outer VLAN ID
#                   (-vlan_id_outer) for subsequent packets. The step must be
#                   equal to a value of 2 for the step to increment or decrement
#                   properly. Possible values range from 1 to 255 (see below).
#                   The default is 0. You must set the -l2_encap argument to
#                   ethernet_ii_vlan.
#
#                   2(1) = 2
#                   2(2) = 4
#                   2(4) = 16
#                   2(8) = 256
#                   2(16) = 65,536
#                   2(32) = 4,294,967,296
#                   2(64) = 18,446,744,073,709,551,616
#                   2(128) = 340,282,366,920,938,463,463,374,607,431,768,211,456
#                   2(256) = 115,792,089,237,316,195,423,570,985,008,687,907,
#                            853,269, 984,665,640,564,039, 457,584,007,913,129,
#                            639,936
#
#  -vlan_id_outer_repeat
#               Specifies the number of times the value will be repeated
#
#    -vlan_outer_user_priority
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the VLAN priority to assign to the outer header.
#                   Possible values range from 0 to 7. The default is 0.
#
#    -vlan_user_priority
#                   Specifies the VLAN priority to assign to the specified port,
#                   Possible values range from 0 to 7. The default is 1. You
#                   must set the -l2_encap argument to ethernet_ii_vlan.
#
#     -enable_stream_only_gen
#                  Specifies to use streams or VFDs (Variable Field Definitions)
#                  to generate traffic between end points. 0 or 1, default value
#                  is 1.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -arp_src_hw_addr  
#    -arp_src_hw_count  
#    -arp_src_hw_mode 
#    -arp_dst_hw_addr 
#    -arp_dst_hw_mode 
#    -arp_dst_hw_count 
#    -arp_operation 
#    -fcs
#    -icmp_checksum
#    -icmp_code
#    -icmp_id
#    -icmp_seq
#    -icmp_type
#    -igmp_group_addr
#    -igmp_group_count
#    -igmp_group_mode
#    -igmp_group_step
#    -igmp_max_response_time
#    -igmp_msg_type
#    -igmp_multicast_src
#    -igmp_qqic
#    -igmp_qrv
#    -igmp_record_type
#    -igmp_s_flag
#    -igmp_type
#    -igmp_version
#    -inter_burst_gap
#    -inter_stream_gap
#    -ip_cu
#    -ip_dst_skip_broadcast
#    -ip_dst_skip_multicast
#    -ip_fragment_last
#    -ip_mbz
#    -ip_src_skip_broadcast
#    -ip_src_skip_multicast
#    -ipv6_checksum
#    -ipv6_frag_id
#    -ipv6_frag_more_flag
#    -ipv6_frag_next_header
#    -ipv6_frag_offset
#    -l3_gaus1_avg
#    -l3_gaus2_avg
#    -l3_gaus3_avg
#    -l3_gaus4_avg
#    -l3_gaus1_halfbw
#    -l3_gaus1_weight
#    -l3_gaus2_halfbw
#    -l3_gaus2_weight
#    -l3_gaus3_halfbw
#    -l3_gaus3_weight
#    -l3_gaus4_halfbw
#    -l3_gaus4_weight
#    -l3_imix1_ratio
#    -l3_imix1_size
#    -l3_imix2_ratio
#    -l3_imix2_size
#    -l3_imix3_ratio
#    -l3_imix3_size
#    -l3_imix4_ratio
#    -l3_imix4_size
#    -vci
#    -vci_count
#    -vci_step
#    -vpi
#    -vpi_count
#    -vpi_step
#    -ssrc
#    -rtp_csrc_count
#    -rtp_payload_type
#    -csrc_list
#    -timestamp_initial_value
#    -timestamp_increment
#
# Return Values:
#    The sth::traffic_config function returns a keyed list using the
#    following keys (with corresponding data):
#
#    stream_id
#                   The handle that identifies the traffic stream created by the
#                   sth::traffic_config function.
#
#    stream_id.$port_handle
#                   The stream identifier for traffic associated with
#                   $port_handle. This ID is returned only if you generated
#                   bidirectional traffic.
#
#    stream_id.$port_handle2
#                   The stream identifier for traffic associated with
#                   $port_handle2. This ID is returned only if you generated
#                   bidirectional traffic.
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Description:
#    The sth::traffic_config function sets up a traffic stream block on a
#    Spirent HLTAPI port. Use this function to create new stream blocks,
#    modify existing stream blocks, remove or disable stream blocks, or reset
#    traffic stream blocks. (Use the -mode argument to specify the type of
#    operation, and see the Notes for this section for more information.)
#
#    When you create a stream block on a port, the Spirent HLTAPI generator
#    uses that port to transmit traffic stream blocks. You can also use a single
#    call to the sth::traffic_config function to configure bidirectional
#    traffic between two ports. (See the description of the -bidirectional
#    argument.)
#
#    To configure traffic, use the arguments of the sth::traffic_config
#    function to specify values for fields of an IP datagram. When you start
#    traffic during the test, Spirent HLTAPI generates packets containing
#    protocol headers based on the argument values. The arguments provide
#    information such as source address, destination address, ToS, Layer3
#    protocol, Layer4 protocol, IP bit flags, and other datagram values.
#
#    For each traffic header:
#
#    -    You specify a source and destination. For Ethernet headers, you supply
#         a MAC address; for IP protocols, you specify IPv4 or IPv6 addresses;
#         for TCP and UDP headers, you supply port numbers.
#
#    -    You can specify a count and an increment to use a range of addresses
#         or port numbers for sources and destinations. When you use ranges,
#         Spirent HLTAPI generates packets based on permutations of the
#         address and port number sets. You are limited in the number of ranges
#         that you can specify.
#
#    Spirent HLTAPI supports up to a maximum of 2000 streamBlocks. There is
#    one stream under each streamBlock. Each stream has an adjustable frame
#    length distribution and transmit rate setting.
#
#    HLTAPI version 2.00 introduced the capability of stacking L3 headers in the
#    stream block definition (-mode create). Currently, the HLTAPI supports two
#    levels of stacking for L3:  1) the "inner" type, which is defined by the L3
#    protocol (see -l3_protocol and the arguments that apply to it), and 2) the
#    "outer" type, which is defined by the L3 outer protocol (see
#    -l3_outer_protocol and the arguments that apply to it). The outer header
#    definition is created from the arguments containing "outer" in their names.
#
#    Here is an example showing how to stack headers in a stream
#    definition (-mode create) using both an inner and outer header:
#
#         sth::traffic_config
#                   -mode create \
#                   -port_handle $port1 \
#                   -enable_stacking true \
#                   -length_mode fixed \
#                   -l3_length 256 \
#                   # general switches end here
#                   -l2_encap Ethernet_ii \
#                   .
#                   ..
#                   -l3_protocol ipv4 \
#                   -ip_src_addr 1.1.1.1 \
#                   -ip_dst_addr 3.3.3.3 \
#                   -l3_outer_protocol ipv4 \
#                   -ip_dst_outer_addr "2.2.2.2" \
#                   -ip_outer_protocol 10 \
#                   -ip_hdr_outer_length 3 \
#                   -ip_outer_id 0 \
#                   -ip_outer_checksum 100 \
#                   -ip_outer_ttl 16 \
#                   -ip_fragment_outer_offset 12
#                   ...
#                   -l2_encap Ethernet_ii \
#                   ...
#
#    The example above creates two L3 headers under the stream block .
#
#    To modify attributes in a header (-mode modify), you must identify the
#    specific attribute of the specific header that you added to the traffic
#    stream during -mode create. Use the dot (".") notation to identify the
#    attribute and header using one of the following two methods:
#
#         1) Append the dot to the attribute name to identify the header to
#            modify. For example, to modify the second Layer 2 header, you can
#            identify it as "l2_encap.2". Likewise, to modify the third Layer 3
#            header, you can identify it as "l3_protocol.3". Here is an
#            example:
#
#         sth::traffic_config
#                   -mode modify \
#                   -stream_id 50 \
#                   -l2_encap.2 ethernet_ii \
#                   -src_mac_addr aa.bb.cc.dd.ee.ff \ # the new value of
#                      # src_mac_addr
#                   .
#                   -l3_protocol.3 ipv4 \
#                   -src_ip_addr 10.10.1.1 \
#                   .
#
#         2) Append the dot to the value of the attribute to identify the header
#            to modify. For example, to modify the second Layer 2 header, you
#            can identify it as "Ethernet_ii.2". Likewise, to modify the third
#            Layer 3 header, you can identify it as "ipv4.3". Here is an
#            example:
#
#         sth::traffic_config
#                   -mode modify \
#                   -stream_id 50 \
#                   -l2_encap ethernet_ii.2 \
#                   -src_mac_addr aa.bb.cc.dd.ee.ff \ # the new value of
#                        #src_mac_addr
#                   .
#                   -l3_protocol  ipv4.3 \
#                   -src_ip_addr 10.10.1.1 \
#                   .
#         For both PPPoX and DHCP bound traffic, for subsequent
#         connects and disconnect you do not have to delete and re-
#         create traffic when adding new sessions. To disconnect and
#         re-connect multiple PPPoX or DHCP sessions, you must stop
#         and then restart traffic AFTER all new sessions have
#         connected so the traffic configuration can get the newly
#         updated session information. If you do not stop traffic, the
#         old session information will not be replaced by the new one.
#
# Examples:
#    The following code fragment configures Ethernet traffic for a single
#    port and checks the returned key list to determine the status. The call to
#    traffic_config uses create mode to set up an Ethernet II header, supply
#    source and destination MAC addresses, and generate a range of addresses for
#    stream packets. The L2 encapsulation mode is ethernet_ii. Increment mode is
#    used with a step value of 2, and a count of 3 to generate a stream
#    containing packets with three unique source MAC addresses (0.0.0.0.0.1,
#    0.0.0.0.0.3, and 0.0.0.0.0.5).
#
#    set returnKlist [sth::traffic_config -mode create \
#              -port_handle $p0 \
#              -l2_encap ethernet_ii \
#              -mac_src 0.0.0.0.0.1 \
#              -mac_dst 0.0.0.0.0.3 \
#              -mac_src_mode increment \
#              -mac_src_step 2 \
#              -mac_src_count 3];
#
#    keylget returnKlist status iStatus;
#    if {$iStatus == 0} {
#         keylget returnKlist log result;
#         puts $result;
#    } else {
#         keylget returnKlist stream_id streamID;
#         puts "stream handle 1 = $streamID";
#    }
#
#    On success:
#    {stream_id 108} {status 1} {log {}}
#
#    On failure:
#    {status 0} {log {<errorMsg>}}
#
#   The following example configures PPPoE traffic.
#
#   ##
#   # Access PPPoE traffic example
#   ##
#
#   # Configure PPPoX which will return the handle that will be used later to
#   # configure resolved traffic both destined for and generated from the PPPoX
#   #clients created below.
#
#   set pppox_rL [sth::pppox_config \
#                   -mode create
#                   -port_handle        port1 \
#                   -encap              ethernet_ii \
#                   -protocol           pppoe \
#                   -num_sessions       1 \
#                   -auth_mode          chap \
#                   -mac_addr           00:10:94:01:00:01 \
#                   -username           cisco \
#                   -password           cisco \
#                   ]
#   {status 1} {port_handle port1} {handles host2} {pppoe_port
#   pppoxportconfig1} {pppoe_session pppoeclientblockconfig1} {procName
#   sth::pppox_config}
#
#   # Configure traffic generated from IP address 22.23.0.100, destined for all
#   # connected PPPoX clients associated with the handle returned in "pppox_rL".
#   # The following example assumes that the handle passed into
#   # -downstream_traffic_src_list was retrieved from a successful call to
#   # sth::pppox_config and that all PPPoE sessions are currently connected.
#   # Note: Access traffic requires that -ppp_link be set to 1 in order to use
#   #       -downstream_traffic_src_list. The parameter -mac_dst is a mandatory
#   #       parameter for Access traffic from a static port running no PPPoE
#   #       emulation and that will terminate at the PPPoX client.
#
#   set traffic_config_rL [sth::traffic_config \
#                 -mode                           create \
#                 -port_handle                    port2 \
#                 -l2_encap                       ethernet_ii \
#                 -mac_src                        00:03:a0:10:92:AA \
#                 -mac_dst                        00:03:a0:10:92:78 \
#                 -rate_pps                       50 \
#                 -ppp_link                       1 \
#                 -downstream_traffic_src_list    [keylget pppox_rL handles] \
#                 -l3_protocol                    ipv4 \
#                 -l3_length                      256 \
#                 -length_mode                    fixed \
#                 -ip_src_addr                    22.23.0.100 \
#                 ]
#   {status 1} {stream_id streamblock1}
#
#   # Configure traffic generated from all connected PPPoX clients associated
#   with the handle returned in "pppox_rL" and terminating at the IP address
#   22.23.0.100.
#   # The following example assumes that the handle passed into
#   # -ppp_link_traffic_src_list was retrieved from a successful call to
#   # sth::pppox_config and that all PPPoE sessions are currently connected.
#   # Note: Access traffic requires that -ppp_link be set to 1 in order to use
#   #       -ppp_link_traffic_src_list.
#   set traffic_config_rL [sth::traffic_config \
#                 -mode                           create \
#                 -port_handle                    port1 \
#                 -rate_pps                       1 \
#                 -l2_encap                       ethernet_ii_pppoe \
#                 -ppp_link                       1 \
#                 -ppp_link_traffic_src_list      [keylget pppox_rL handles] \
#                 -l3_protocol                    ipv4 \
#                 -l3_length                      256 \
#                 -length_mode                    fixed \
#                 -ip_dst_addr                    22.23.0.100 \
#                 -ip_dst_mode                    fixed \
#   ]
#  {status 1} {stream_id streamblock2}
#
# Sample Input: See Examples.
#
# Sample Output:See Examples.
#
# Notes:
#    1)   Before you modify traffic streams, you must use the traffic_control
#         function to stop generating traffic. Failure to stop traffic may
#         produce unpredictable results. (See the description of the
#         traffic_control function for information about stopping traffic.)
#
#    2)   When you set the mode to remove, the mandatory argument -stream_id
#         <integer> specifies the stream id to remove from the traffic
#         generator, existing streams are left intact.
#
#    3)   In reset mode, if you specify the -stream_id argument, Spirent
#         HLTAPI removes the existing stream for the specified port. If you
#         do not specify -stream_id, all streams are removed from the device
#         corresponding to the port_handle argument.
#
#    4)   For functions that use the control plane to resolve data plane packet
#         block information, it is assumed that the control plane has been
#         successfully established prior to issuing the sth::traffic_config
#         function.
#
# End of Procedure Header
#
proc ::sth::traffic_config_wrap {args} {
    ::sth::sthCore::Tracker ::sth::traffic_config_wrap $args
 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set returnKeyedList ""

    set cmdName "::sth::Traffic::traffic_config_imp $args"
    if {[catch {set returnKeyedList [eval $cmdName]} errMsg]} {
        if {[string length $errMsg] == 0} {
            set errMsg "exception with emptry error message is raised."
            ::sth::sthCore::log error $errMsg
        }
        ::sth::sthCore::processError returnKeyedList "error in $cmdName -->$errMsg";    
    } else {
        if {[string length $returnKeyedList] == 0} {
            ::sth::sthCore::processError returnKeyedList "error in $cmdName --> empty keyed list returned"
        }
    }
    return $returnKeyedList
}

proc ::sth::traffic_config {args} {
    # TODO:
    # 1.    The mode validation to be performed by commandInit (as a part of choices).
    #       To be added by Davison. 

    ::sth::sthCore::Tracker ::sth::traffic_config $args
    set mns "sth::Traffic";
    set cmdName "traffic_config";
    
    set trafficKeyedList "";
    array set userArgsArray {};
    set prioritisedAttributeList {};
    set errMsg "";
    
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    
    if {[lsearch -exact $args "-l3_protocol"] != -1} {
        set idx [lsearch -exact $args "-l3_protocol"];
        set arg [lindex $args [expr $idx+1]];
        set arg_new [string tolower $arg];
        set args [lreplace $args [expr $idx+1] [expr $idx+1] "$arg_new"];
    }
    
    if {[lsearch -exact $args "-l3_outer_protocol"] != -1} {
        set idx [lsearch -exact $args "-l3_outer_protocol"];
        set arg [lindex $args [expr $idx+1]];
        set arg_new [string tolower $arg];
        set args [lreplace $args [expr $idx+1] [expr $idx+1] "$arg_new"];
    }
    
    if {[lsearch -exact $args "-l4_protocol"] != -1} {
        set idx [lsearch -exact $args "-l4_protocol"];
        set arg [lindex $args [expr $idx+1]];
        set arg_new [string tolower $arg];
        set args [lreplace $args [expr $idx+1] [expr $idx+1] "$arg_new"];
    }
    
    if {[lsearch -exact $args "-igmp_version"] != -1} {
        set idx [lsearch -exact $args "-igmp_version"];
        set igmp_ver [lindex $args [expr $idx+1]];
        if {($igmp_ver!=3) && (([lsearch -exact $args "-igmp_qqic"] != -1) || \
            ([lsearch -exact $args "-igmp_qrv"] != -1) || ([lsearch -exact $args "-igmp_s_flag"] != -1)) } {
            ::sth::sthCore::processError trafficKeyedList "igmp_qqic/igmp_qrv/igmp_s_flag not support under igmp$igmp_ver" {}
            return $trafficKeyedList;
        }
        if {($igmp_ver==1) && ([lsearch -exact $args "-igmp_max_response_time"] != -1)} {
            ::sth::sthCore::processError trafficKeyedList "igmp_max_response_time not support under igmp1" {}
            return $trafficKeyedList;
        }
        
    }
    
    if {[catch {::sth::sthCore::commandInit  ::sth::Traffic::trafficConfigTable \
                                        $args \
                                        ::$mns\:: \
                                        $cmdName \
                                        userArgsArray \
                                        prioritisedAttributeList} errMsg]} {
        ::sth::sthCore::processError trafficKeyedList "\[Traffic\] commandInit FAILED. $errMsg" {}
        return $trafficKeyedList;
    }
    
    # If we get here, that means commandInit went fine.
    set ::sth::Traffic::modeOfOperation $userArgsArray(mode);
    
    #-l2_encap's default value should not be used for modify mode
    if { $::sth::Traffic::modeOfOperation == "modify" } {
        
        # DE17295 Failed to modify Frame threshold values
        # get frame threshold attributes, and remove them from prioritisedAttributeList
        set attributeList [::sth::Traffic::processThresholdAttributeList $prioritisedAttributeList]
        set prioritisedAttributeList [lindex $attributeList 0]
        set thresholdAttributes [lindex $attributeList 1]

        if {[llength $thresholdAttributes] > 0} {
            if {[info exists userArgsArray(port_handle)]} {
                # process frame threshold arguments
                foreach elem $thresholdAttributes {
                    ::sth::Traffic::processThresholdSwitches $elem
                }
                # config Frame threshold values
                ::sth::Traffic::configFrameThreshold
                if {![info exists userArgsArray(stream_id)]} {
                    keylset trafficKeyedList status $::sth::sthCore::SUCCESS
                    return $trafficKeyedList
                }
            } else {
                set errMsg "Missing mandatory arguments for config Frame threshold.. Expected: port_handle"
                ::sth::sthCore::log debug "$cmdName: $errMsg "
                return -code 1 -errorcode -1 $errMsg
            }
        }

        set streamHandle_list [split $userArgsArray(stream_id) " "]
            
        foreach streamHandle $streamHandle_list {
            if {$::sth::Session::xmlFlag != 1 \
                && $::sth::Session::fillTraffic ne "set" \
                && [lsearch -exact $args "-l2_encap"] == -1} {
                set userArgsArray(l2_encap) [set ::$mns\::strHandlel2EncapMap($streamHandle)];
            }
            set l3_protocol ""
            if {[lsearch -exact $args "-l3_protocol"] == -1} {
                   
                set ip_handle1 [::sth::sthCore::invoke ::stc::get $streamHandle -children-ipv4:IPv4]
                set ip_handle2 [::sth::sthCore::invoke ::stc::get $streamHandle -children-ipv6:IPv6]
                set ip_handle3 [::sth::sthCore::invoke ::stc::get $streamHandle -children-arp:ARP]
                if {($ip_handle1 ne "") && ($ip_handle2 eq "") && ($ip_handle3 eq "")} {
                    set l3_protocol "ipv4"
                } elseif {($ip_handle1 eq "") && ($ip_handle2 ne "") && ($ip_handle3 eq "")} {
                    set l3_protocol "ipv6"
                } elseif {($ip_handle1 eq "") && ($ip_handle2 eq "") && ($ip_handle3 ne "")} {
                    set l3_protocol "arp"
                }
                if {$l3_protocol ne ""} {
                    set userArgsArray(l3_protocol) $l3_protocol
                }
            }
           
            if {[info exists userArgsArray(l3_protocol)] && ($userArgsArray(l3_protocol) ne "")} {
                set ::sth::Traffic::l3Protocol $userArgsArray(l3_protocol);
            }
            if {[info exists userArgsArray(ip_checksum)]} {
                if {$userArgsArray(ip_checksum) == 1} {
                    set userArgsArray(ip_checksum) 65535  
                }
            }
    
    
                #error value is 65535 (0xffff)
            if {[info exists userArgsArray(ip_outer_checksum)]} {
                if {$userArgsArray(ip_outer_checksum) == 1} {
                    set userArgsArray(ip_outer_checksum) 65535
                }
            }
            set userArgsArray(stream_id) $streamHandle
            set funcToCall $::sth::Traffic::arrayModeFunctionMap($userArgsArray(mode));
    
            if {[catch {::sth::Traffic::$funcToCall} procStatus]} {
                ::sth::sthCore::log debug "\[Traffic\] internal operation failed $procStatus";
                set errMsg "_none_";
                keylget trafficKeyedList log errMsg;
                if {$errMsg == "_none_"} {
                    ::sth::sthCore::processError trafficKeyedList "internal operation failed. $procStatus" {}
                }
                #return $trafficKeyedList;
            }  
        }       
    } else {         
	#if loop is just for the support to generate streamblock from pcap in HLTAPI
        #and in which the streamblock and generatorconfig objects configuration is only supported.
        if {[lsearch -exact $args "-pcap_file"] != -1 && [lsearch -exact $args "-port_handle"]!= -1 } {
            set streamHandles_old [::sth::sthCore::invoke ::stc::get $userArgsArray(port_handle) -children-StreamBlock]
            ::sth::sthCore::invoke ::stc::perform GenerateStreamBlockFromPcap -PcapFileName $userArgsArray(pcap_file) -port $userArgsArray(port_handle)
            set streamHandles [::sth::sthCore::invoke ::stc::get $userArgsArray(port_handle) -children-StreamBlock]
            if {[llength $streamHandles_old]} {
                foreach stream $streamHandles_old {
                    set index0 [lsearch $streamHandles $stream]
                    set streamHandles [lreplace $streamHandles $index0 $index0]
                }
            }
            set funcTableName1 "::$mns\::traffic_config_procfunc";
            set funcTableName2 ""
            foreach element $prioritisedAttributeList {
                foreach {prio sName} $element {                   
                    set funcTableName2 "::$mns\::traffic_config_$sName\_mode";                  
                    if {[info exists $funcTableName2\(create)]} {
                        set funcName [set $funcTableName2\(create)];
                    } else {
                        set funcName [set $funcTableName1\($sName)];
                    }
                    
                    if {$funcName != "_none_"&& $sName!="port_handle"} {
                        if {[catch {::sth::Traffic::$funcName $sName} errMsg]} {
                            ::sth::sthCore::log debug "$funcName FAILED. $errMsg";
                            ::sth::sthCore::processError trafficKeyedList $errMsg;
                            return -code 1 -errorcode -1 $errMsg;
                        } else {
                            ::sth::sthCore::log info "$funcName for $sName \t PASSED."
                        }
                    }
                }
            }
            foreach stream $streamHandles {
                if {[catch {::sth::sthCore::invoke ::stc::config $stream [set ::$mns\::listProcessedList]} procStatus]} {
                    ::sth::sthCore::processError trafficKeyedList $procStatus {}
                    return -code 1 -errorcode -1 $procStatus;
                }
            }
            keylset trafficKeyedList stream_id $streamHandles
            keylset trafficKeyedList status $::sth::sthCore::SUCCESS
            return $trafficKeyedList
        }  
        if {[info exists userArgsArray(l3_protocol)] && ($userArgsArray(l3_protocol) ne "")} {
            set ::sth::Traffic::l3Protocol $userArgsArray(l3_protocol);
        }
	
	#error value is 65535 (0xffff)
        if {[info exists userArgsArray(ip_checksum)]} {
            if {$userArgsArray(ip_checksum) == 1} {
                set userArgsArray(ip_checksum) 65535  
            }
        }
    
    #error value is 65535 (0xffff)
        if {[info exists userArgsArray(ip_outer_checksum)]} {
            if {$userArgsArray(ip_outer_checksum) == 1} {
                set userArgsArray(ip_outer_checksum) 65535
            }
        }
	
        set funcToCall $::sth::Traffic::arrayModeFunctionMap($userArgsArray(mode));
    
        if {[catch {::sth::Traffic::$funcToCall} procStatus]} {
            ::sth::sthCore::log debug "\[Traffic\] internal operation failed $procStatus";
            set errMsg "_none_";
            keylget trafficKeyedList log errMsg;
            if {$errMsg == "_none_"} {
                ::sth::sthCore::processError trafficKeyedList "internal operation failed. $procStatus" {}
            }
            #return $trafficKeyedList;
        }
    }
    #if the mac_dst_mode is discovery, the Destination MAC will match the MAC address received from the ARP request.
    #although in stc gui, we can't see the mac_dst_addr changes, the captured packets will have the resolved mac_dst_addr
    #Do ARP here and set the variable ::sth::Session::PORTLEVELARPDONE($porthnd) as 1
    if {([string equal -nocase "create" $::sth::Traffic::modeOfOperation]||[string equal -nocase "modify" $::sth::Traffic::modeOfOperation]) \
        && [info exist userArgsArray(mac_dst_mode)] && [string equal -nocase "discovery" $userArgsArray(mac_dst_mode)]} {
        set porthdl_list ""
        if {[info exist userArgsArray(port_handle)]} {
            lappend porthdl_list $userArgsArray(port_handle)
        }
        set strblk_hdl ""
        if {[info exist userArgsArray(stream_id)]} {
            set strblk_hdl $userArgsArray(stream_id)
        } else {
            if {[info exist userArgsArray(port_handle2)] && [info exist userArgsArray(bidirectional)] && (1 == $userArgsArray(bidirectional))} {
                set strblk_hdl "[keylget trafficKeyedList stream_id.$userArgsArray(port_handle)] [keylget trafficKeyedList stream_id.$userArgsArray(port_handle2)]"
                lappend porthdl_list $userArgsArray(port_handle2)
            } else {
                set strblk_hdl [keylget trafficKeyedList stream_id]
            }
        }
        if {$strblk_hdl != ""} {
            set arped_strblk $strblk_hdl
            #check if the arpcache has stored the updated mac address
            ####do interface arp
            set host_arp ""
            set all_ports [::sth::sthCore::invoke stc::get project1 -children-port]
            foreach portindex $all_ports {
                set hostList [::sth::sthCore::invoke stc::get $portindex -affiliationport-Sources]
                foreach hostinde $hostList {
                    if {[::sth::sthCore::invoke stc::get $hostinde -name] eq "port_address"} {
                        lappend host_arp $hostinde
                    }
                }
            }
            if {$host_arp ne ""} {
                ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList "$host_arp"
            }
            foreach strblk $strblk_hdl {
                foreach porthandle $porthdl_list {
                    ::sth::sthCore::invoke stc::perform ArpNdUpdateArpCache -handlelist $porthandle
                    set arpcache [::sth::sthCore::invoke stc::get $porthandle -children-arpcache]
                    set arpinfo_list [::sth::sthCore::invoke stc::get $arpcache -arpcachedata]
                    set ipheader [::sth::sthCore::invoke stc::get $strblk -children-$userArgsArray(l3_protocol):$userArgsArray(l3_protocol)]
                    if {$ipheader != ""} {
                        set strblk_gw [::sth::sthCore::invoke stc::get $ipheader -gateway]
                        foreach arpinfo $arpinfo_list {
                            set len [llength $arpinfo]
                            set gw [lindex $arpinfo [expr $len - 2]]
                            if {$gw == $strblk_gw} {
                                set mac [lindex $arpinfo [expr $len - 1]]
                                if {[regsub -all -- {[.|\-|:]} $mac {}] != "000000000000"} {
                                    set ether [::sth::sthCore::invoke stc::get $strblk -children-ethernet:ethernetii]
                                    ::sth::sthCore::invoke stc::config $ether -dstmac $mac
                                    regsub "$strblk" $arped_strblk "" arped_strblk
                                    break
                                }
                            }
                        }
                    }
                }
            }

            if {$arped_strblk != ""} {
                ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $arped_strblk
            }
            
            ##disable Arp since already does here, or else, will do arp again in traffic_control
            foreach porthdl $porthdl_list {
                set ::sth::Session::PORTLEVELARPDONE($porthdl) 1
            }
        }
    }
    #keylset trafficKeyedList stream_id [set ::$mns\::handleTxStream];
    
    if {[catch {::sth::Traffic::_traffic_config $userArgsArray(mode)} retHandle]} {
        ::sth::sthCore::processError trafficKeyedList "_traffic_config failed. $retHandle" {}
    }
    
    if {[catch {::sth::sthCore::doStcApply } retHandle]} {
            ::sth::sthCore::processError trafficKeyedList "Apply failed. $retHandle" {}
    }
    # Apply the configuration to the card.
    ::sth::Traffic::processClearDataStructures;
    
    return $trafficKeyedList;
    
}

proc ::sth::imix_config { args } {
    ::sth::sthCore::Tracker ::sth::imix_config $args
    variable ::sth::Traffic::sortedSwitchPriorityList
    variable ::sth::Traffic::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Traffic::trafficConfigTable $args \
                                                    ::sth::Traffic:: \
                                                    imix_config \
                                                    ::sth::Traffic::userArgsArray \
                                                    ::sth::Traffic::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    
    set mode $::sth::Traffic::userArgsArray(mode)
    
    if {[catch {::sth::Traffic::imix_config_$mode returnKeyedList} eMsg]} {
            ::sth::sthCore::log error "Stack trace:\n$::errorInfo"
            ::sth::sthCore::processError returnKeyedList $eMsg
    }
    
    return $returnKeyedList	
}
