*** Settings ***
Documentation     Resource file containing keywords for Spirent High Level Test Api(HLTAPI) libarary. 
Library           BuiltIn
Library           Collections
Library           sth.py

*** Variables ***

*** Keywords ***
emulation http control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_http_control  &{request_params}

emulation oam config msg
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_oam_config_msg  &{request_params}

emulation pcep stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pcep_stats  &{request_params}

emulation rsvp tunnel config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_tunnel_config  &{request_params}

emulation lacp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lacp_config  &{request_params}

emulation lldp dcbx tlv config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lldp_dcbx_tlv_config  &{request_params}

l2tpv3 stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tpv3_stats  &{request_params}

emulation http config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_http_config  &{request_params}

emulation sip stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_sip_stats  &{request_params}

pcs error config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pcs_error_config  &{request_params}

fc config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fc_config  &{request_params}

emulation efm config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_efm_config  &{request_params}

emulation ldp route element config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ldp_route_element_config  &{request_params}

emulation ldp route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ldp_route_config  &{request_params}

l2tp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tp_control  &{request_params}

emulation vxlan config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vxlan_config  &{request_params}

emulation twamp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_twamp_stats  &{request_params}

emulation igmp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_info  &{request_params}

emulation bgp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_config  &{request_params}

emulation igmp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_config  &{request_params}

emulation dhcp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_control  &{request_params}

emulation ancp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ancp_control  &{request_params}

emulation igmp querier control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_querier_control  &{request_params}

emulation mpls vpn control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_vpn_control  &{request_params}

l2tpv3 config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tpv3_config  &{request_params}

interface stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.interface_stats  &{request_params}

emulation mpls tp port config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_tp_port_config  &{request_params}

link config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.link_config  &{request_params}

emulation ipv6 autoconfig control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ipv6_autoconfig_control  &{request_params}

fip traffic config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fip_traffic_config  &{request_params}

emulation openflow control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_openflow_control  &{request_params}

emulation multicast group config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_multicast_group_config  &{request_params}

emulation dhcp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_config  &{request_params}

invoke
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.invoke  &{request_params}

emulation bgp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_control  &{request_params}

emulation bgp route info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_route_info  &{request_params}

emulation rsvp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_control  &{request_params}

fcoe control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fcoe_control  &{request_params}

emulation ospf topology route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_topology_route_config  &{request_params}

random error control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.random_error_control  &{request_params}

packet control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_control  &{request_params}

traffic stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.traffic_stats  &{request_params}

emulation ospfv3 info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospfv3_info  &{request_params}

pppox control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_control  &{request_params}

emulation convergence config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_convergence_config  &{request_params}

emulation oam config ma meg
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_oam_config_ma_meg  &{request_params}

pppox config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_config  &{request_params}

emulation mld info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mld_info  &{request_params}

emulation bfd config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bfd_config  &{request_params}

emulation oam control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_oam_control  &{request_params}

emulation msti config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_msti_config  &{request_params}

get handles
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.get_handles  &{request_params}

test rfc2544 config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc2544_config  &{request_params}

interface control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.interface_control  &{request_params}

emulation ospfv2 info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospfv2_info  &{request_params}

emulation nonvxlan port config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_nonvxlan_port_config  &{request_params}

emulation dot1x config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dot1x_config  &{request_params}

emulation dhcp group config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_group_config  &{request_params}

fcoe config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fcoe_config  &{request_params}

emulation bfd session config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bfd_session_config  &{request_params}

emulation ptp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ptp_control  &{request_params}

test rfc3918 control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc3918_control  &{request_params}

emulation rsvp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_info  &{request_params}

test rfc2889 config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc2889_config  &{request_params}

arp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.arp_control  &{request_params}

emulation lldp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lldp_control  &{request_params}

pcs error control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pcs_error_control  &{request_params}

emulation vpls site config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vpls_site_config  &{request_params}

emulation pim group config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pim_group_config  &{request_params}

connect
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.connect  &{request_params}

close
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.close  &{request_params}

emulation mpls tp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_tp_config  &{request_params}

emulation igmp querier info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_querier_info  &{request_params}

emulation dot1x control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dot1x_control  &{request_params}

emulation twamp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_twamp_config  &{request_params}

create csv file
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.create_csv_file  &{request_params}

emulation ldp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ldp_info  &{request_params}

emulation bgp route generator
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_route_generator  &{request_params}

emulation lldp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lldp_info  &{request_params}

emulation ospf lsa generator
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_lsa_generator  &{request_params}

test config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_config  &{request_params}

emulation stp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_stp_stats  &{request_params}

alarms control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.alarms_control  &{request_params}

emulation mvpn customer port config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_customer_port_config  &{request_params}

emulation bgp custom attribute config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_custom_attribute_config  &{request_params}

random error config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.random_error_config  &{request_params}

emulation isis lsp generator
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_isis_lsp_generator  &{request_params}

fill global variables
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fill_global_variables  &{request_params}

emulation mpls l3vpn pe config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_l3vpn_pe_config  &{request_params}

emulation openflow config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_openflow_config  &{request_params}

emulation ospf tlv config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_tlv_config  &{request_params}

emulation ldp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ldp_control  &{request_params}

emulation bgp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_info  &{request_params}

emulation mpls l2vpn site config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_l2vpn_site_config  &{request_params}

emulation rsvp custom object config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_custom_object_config  &{request_params}

sequencer control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.sequencer_control  &{request_params}
    
sequencer config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${tcl_str} =  Pop From Dictionary  ${request_params}  tcl_str
    ${return_params}    sth.hltpy_sequencer_config_wrapper  ${tcl_str}  &{request_params}

emulation pcep control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pcep_control  &{request_params}

traffic config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.traffic_config  &{request_params}

emulation rip config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rip_config  &{request_params}

test rfc3918 config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc3918_config  &{request_params}

emulation twamp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_twamp_control  &{request_params}

packet config buffers
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_config_buffers  &{request_params}

emulation twamp session config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_twamp_session_config  &{request_params}

emulation efm control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_efm_control  &{request_params}

drv stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.drv_stats  &{request_params}

emulation device config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_device_config  &{request_params}

emulation stp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_stp_control  &{request_params}

pppox server control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_server_control  &{request_params}

l2tpv3 control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tpv3_control  &{request_params}

emulation oam config topology
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_oam_config_topology  &{request_params}

emulation dhcp server control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_server_control  &{request_params}

pppox stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_stats  &{request_params}

pppox server config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_server_config  &{request_params}

pppox server stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.pppox_server_stats  &{request_params}

emulation iptv channel viewing profile config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_channel_viewing_profile_config  &{request_params}

interface config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.interface_config  &{request_params}

emulation oam info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_oam_info  &{request_params}

forty hundred gig l1 results
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.forty_hundred_gig_l1_results  &{request_params}

emulation vxlan control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vxlan_control  &{request_params}

packet config filter
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_config_filter  &{request_params}

emulation mstp region config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mstp_region_config  &{request_params}

emulation iptv control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_control  &{request_params}

emulation iptv config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_config  &{request_params}

ppp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.ppp_config  &{request_params}

emulation mvpn control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_control  &{request_params}

emulation gre config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_gre_config  &{request_params}

fcoe stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fcoe_stats  &{request_params}

emulation ptp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ptp_stats  &{request_params}

start devices
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.start_devices  &{request_params}

emulation ping
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ping  &{request_params}

emulation openflow stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_openflow_stats  &{request_params}

traffic config ospf
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.traffic_config_ospf  &{request_params}

traffic control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.traffic_control  &{request_params}

load xml
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.load_xml  &{request_params}

emulation mpls l2vpn pe config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_l2vpn_pe_config  &{request_params}

emulation vxlan stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vxlan_stats  &{request_params}

arp nd config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.arp_nd_config  &{request_params}

device info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.device_info  &{request_params}

emulation stp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_stp_config  &{request_params}

emulation mvpn config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_config  &{request_params}

emulation http phase config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_http_phase_config  &{request_params}

packet stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_stats  &{request_params}

emulation convergence info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_convergence_info  &{request_params}

fc stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fc_stats  &{request_params}

emulation bfd control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bfd_control  &{request_params}

packet config pattern
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_config_pattern  &{request_params}

emulation pcep config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pcep_config  &{request_params}

emulation rip control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rip_control  &{request_params}

emulation mvpn info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_info  &{request_params}

emulation pim control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pim_control  &{request_params}

emulation isis info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_isis_info  &{request_params}

emulation vxlan port config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vxlan_port_config  &{request_params}

emulation ldp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ldp_config  &{request_params}

emulation ospf control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_control  &{request_params}

test rfc2544 info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc2544_info  &{request_params}

emulation dhcp server stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_server_stats  &{request_params}

emulation rip route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rip_route_config  &{request_params}

emulation rsvpte tunnel control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvpte_tunnel_control  &{request_params}

fc control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fc_control  &{request_params}

emulation efm stat
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_efm_stat  &{request_params}

emulation vxlan wizard config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_vxlan_wizard_config  &{request_params}

emulation rip info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rip_info  &{request_params}

emulation dhcp server config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_server_config  &{request_params}

emulation bfd info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bfd_info  &{request_params}

emulation ipv6 autoconfig
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ipv6_autoconfig  &{request_params}

emulation iptv stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_stats  &{request_params}

emulation ancp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ancp_config  &{request_params}

emulation mpls l3vpn site config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_l3vpn_site_config  &{request_params}

emulation sip control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_sip_control  &{request_params}

emulation multicast source config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_multicast_source_config  &{request_params}

fcoe traffic config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.fcoe_traffic_config  &{request_params}

emulation ipv6 autoconfig stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ipv6_autoconfig_stats  &{request_params}

test control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_control  &{request_params}

imix config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.imix_config  &{request_params}

emulation http stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_http_stats  &{request_params}

l2tp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tp_stats  &{request_params}

emulation bgp route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_route_config  &{request_params}

packet config triggers
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_config_triggers  &{request_params}

emulation isis topology route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_isis_topology_route_config  &{request_params}

emulation dhcp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_stats  &{request_params}

emulation mvpn vrf route config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_vrf_route_config  &{request_params}

emulation dot1x stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dot1x_stats  &{request_params}

test rfc2544 control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc2544_control  &{request_params}

emulation lacp info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lacp_info  &{request_params}

emulation iptv channel block config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_channel_block_config  &{request_params}

labserver disconnect
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.labserver_disconnect  &{request_params}

emulation ospf lsa config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_lsa_config  &{request_params}

l2tp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.l2tp_config  &{request_params}

packet info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_info  &{request_params}

stop devices
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.stop_devices  &{request_params}

emulation lag config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lag_config  &{request_params}

emulation mpls tp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mpls_tp_control  &{request_params}

emulation igmp querier config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_querier_config  &{request_params}

emulation isis control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_isis_control  &{request_params}

emulation convergence control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_convergence_control  &{request_params}

cleanup session
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.cleanup_session  &{request_params}

emulation bgp route element config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_bgp_route_element_config  &{request_params}

emulation lsp switching point tlvs config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lsp_switching_point_tlvs_config  &{request_params}

emulation ospf config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_config  &{request_params}

emulation ptp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ptp_config  &{request_params}

emulation mld config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mld_config  &{request_params}

emulation mvpn vrf config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_vrf_config  &{request_params}

ppp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.ppp_stats  &{request_params}

packet decode
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.packet_decode  &{request_params}

emulation mvpn vrf traffic config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_vrf_traffic_config  &{request_params}

test rfc3918 info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.test_rfc3918_info  &{request_params}

labserver connect
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.labserver_connect  &{request_params}

emulation http profile config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_http_profile_config  &{request_params}

emulation dhcp server relay agent config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_dhcp_server_relay_agent_config  &{request_params}

emulation ancp subscriber lines config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ancp_subscriber_lines_config  &{request_params}

emulation sip config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_sip_config  &{request_params}

emulation mld group config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mld_group_config  &{request_params}

alarms stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.alarms_stats  &{request_params}

emulation mld control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mld_control  &{request_params}

emulation pim info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pim_info  &{request_params}

emulation lsp ping info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lsp_ping_info  &{request_params}

emulation mvpn provider port config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_mvpn_provider_port_config  &{request_params}

emulation pim config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_pim_config  &{request_params}

emulation ospf route info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ospf_route_info  &{request_params}

emulation rsvp tunnel info
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_tunnel_info  &{request_params}

emulation l2vpn pe config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_l2vpn_pe_config  &{request_params}

emulation lldp optional tlv config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lldp_optional_tlv_config  &{request_params}

emulation isis config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_isis_config  &{request_params}

emulation rsvp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_rsvp_config  &{request_params}

emulation igmp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_control  &{request_params}

emulation ancp stats
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_ancp_stats  &{request_params}

emulation igmp group config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_igmp_group_config  &{request_params}

emulation lacp control
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lacp_control  &{request_params}

emulation iptv viewing behavior profile config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_iptv_viewing_behavior_profile_config  &{request_params}

emulation lldp config
    [Arguments]    &{request_params}
    [return]       ${return_params}
    [Documentation]
    ${return_params}    sth.emulation_lldp_config  &{request_params}

