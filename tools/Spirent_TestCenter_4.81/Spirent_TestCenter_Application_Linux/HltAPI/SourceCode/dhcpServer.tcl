namespace eval ::sth::DhcpServer:: {
}

##Procedure Header
#
# Name:
#    sth::emulation_dhcp_server_config
#
# Purpose:
#    Creates, modifies or resets an emulated Dynamic Host Configuration Protocol(DHCP)
#    server for the specified Spirent HLTAPI port or handle.
#
#    DHCP server can dynamically assign an IP address and deliver configuration parameters
#    to a DHCP client on a TCP/IP network. DHCP allows reuse of an address that is no
#    longer needed by the client to which it was assigned. 
#    
#
# Synopsis:
#    sth::emulation_dhcp_server_config
#         -handle <dhcp_server_handle>
#         -port_handle <port_handle>
#	  [-mode {create|modify|reset}]
#         [-count <1-100000>]
#         [-local_mac <aa:bb:cc:dd:ee:ff>]
#         [-vlan_id <0-4095>]
#         [-vlan_ethertype {0x8100|0x88A8|0x9100|0x9200}]
#	  [-ip_address <a.b.c.d>]
#         [-ip_step <a.b.c.d>]
#	  [-ip_prefix_step <integer>]
#	  [-ip_prefix_length <0-32>]
#	  [-ip_repeat <integer>]
#	  [-ip_gateway <a.b.c.d>]
#	  [-lease_time <10-4294967295>]
#	  [-ipaddress_pool <a.b.c.d>]
#	  [-ipaddress_count <integer>]
#	  [-ipaddress_increment <integer>]
#	  [-dhcp_ack_options {0|1}]
#	  [-dhcp_ack_time_offset <8 HEX chars>]
#	  [-dhcp_ack_router_address <a.b.c.d>]
#	  [-dhcp_ack_time_server_address <a.b.c.d>]
#	  [-dhcp_ack_circuit_id <8 HEX chars>]
#	  [-dhcp_ack_remote_id <8 HEX chars>]
#	  [-dhcp_ack_link_selection <a.b.c.d>]
#	  [-dhcp_ack_cisco_server_id_override <a.b.c.d>]
#	  [-dhcp_ack_server_id_override <a.b.c.d>]
#	  [-dhcp_offer_options {0|1}]
#	  [-dhcp_offer_time_offset <integer>]
#	  [-dhcp_offer_router_adddress <a.b.c.d>]
#	  [-dhcp_offer_time_server_address <a.b.c.d>]
#	  [-dhcp_offer_circuit_id <8 HEX chars>]
#	  [-dhcp_offer_remote_id <8 HEX chars>]
#	  [-dhcp_offer_link_selection <a.b.c.d>]
#	  [-dhcp_offer_cisco_server_id_override <a.b.c.d>]
#	  [-dhcp_offer_server_id_override <a.b.c.d>]
#
#
# Arguments:
#
#    -port_handle
#                   Specifies the port on which to create the DHCP server when
#                   -mode is set to "create". This argument is mandatory only for
#                   "create" mode.
# 
#    -mode
#		   Specifies the action to perform on the specified port or DHCP 
#                  server handle. The modes are described below:
#                   
#                     create - Creates a DHCP server on the port
#                          specified with the -port_handle argument. You must
#                          specify the -port_handle argument.
#
#		      modify - Changes the configuration for the DHCP server 
#                          identified by the -handle argument. You must specify
#                          the -handle argument.
#
#		     reset - Deletes the DHCP server identified by the -handle
#                          argument. You must specify the -handle argument.
#                        
#    -handle
#                  Specifies the DHCP server handle when -mode is set to
#                  "modify" or "reset". This argument is mandatory for -mode 
#                  modify and reset. See -port_handle.
#                   
#
#    -count
#                  Specifies the number of emulated DHCP server devices. 
#                  Possible values range form 1 to 100000. The default value is 1.
#
#    -local_mac
#		   Specifies the first mac address of the emulated DHCP server.
#
#    -vlan_id  
#		   Specifies the vlan id of the VLAN interface. Possible values
#                  range form 0 to 4095.
#
#    -vlan_ethertype
#		   Specifies the type of vlan tag protocol identifier(TPID). 
#                  It applies only to vlan_id option. Possible values are 
#                  0x8100, 0x88A8, 0x9100 and 0x9200. The default
#                  value is 0x8100.
#
#    -ip_address
#                  Specifies the first IPv4 address of the emulated DHCP server.
#                  The default value is 192.85.1.3.
#    -ip_step
#                  Specifies the step value for IPv4 addresses. The default
# 		   increment is 0.0.0.1. You can use -ip_prefix_step and
#                  -ip_prefix_length to replace -ip_step argument. If the 
#                  three arguments are specified, -ip_step must be equivalent
#                  with the step value figured out by -ip_prefix_step and 
#                  -ip_prefix_length.
#
#
#	 -ip_prefix_step
#                   Specifies the size of the step applied to the prefix length
#                   bit position. It can be used with -ip_prefix_length to increase
#                   IPv4 address when -ip_step is not being used. You must 
#                   specify -ip_prefix_length if -ip_prefix_step is used.  
#                                     
#    -ip_prefix_length
#                   Specifies the IPv4 address prefix length. It is the bit 
#                   position at which the -ip_prefix_step is applied. 
#                   It is mandatory when -ip_prefix_step is used. Possible values
#                   range form 0 to 32. The default value is 24. 
#                   
#    -ip_repeat
#                   Specifies the number of times to repeat the same IPv4 address 
#                   before incrementing. The default value is 1.
#
#    -ip_gateway
#                   Specifies the IPv4 gateway address of the emulated DHCP server.
#                   The default value is 192.85.1.1.
#
#    -lease_time
#		   Specifies the lease duration to offer the client, in seconds.
#                  Possible values range form 10 to 4294967295. The default value
#                  is 60.
#
#     -ipaddress_pool
#		   Specifies the first IPv4 address in the DHCP server address pool.
#
#     -ipaddress_count
#                  Specifies the number of IPv4 addresses in the DHCP server 
#                  address pool. The default value is 65536.
# 
#     -ipaddress_increment
#		   Specifies the amount to increase each IPv4 address in the
#                  DHCP server address pool. The default value is 1.
#
#     -dhcp_ack_options
#		   Enable or disable DHCP ACK Options of the emulated DHCP server. 
#                  Possible values are 0 and 1. The default value is 0(disabled).
#                  If enabled, you can specify DHCP ACK options which will be 
#                  encapsulated in DHCP ACK message sent to the client by DHCP server.
#         
#    -dhcp_ack_time_offset      
#                  Specifies DHCP ACK Option time offset(Option 2) in seconds. 
#                  Its value can be positive or negative. The default value is 0.
#                  -dhcp_ack_options must be 1 when -dhcp_ack_time_offset is used.
#                   
#    -dhcp_ack_router_address
#		   Specifies DHCP ACK Option router option(Option 3) IPv4 
#                  address. Multiple IPv4 addresses can be specified.
#                  The default value is  0.0.0.0. -dhcp_ack_options must 
#                  be 1 when -dhcp_ack_router_address is used.
#                  
#    -dhcp_ack_time_server_address    
#		   Specifies DHCP ACK Option timer server address(Option 4).
#        	   Multiple IPv4 addresses can be specified. The default 
#                  value is  0.0.0.0. -dhcp_ack_options must be 1 when
#                  -dhcp_ack_time_server_address is used.

#    -dhcp_ack_circuit_id
#                  Specifies the circuit ID sub-option(sub-option 1) of DHCP 
#                  ACK Option relay agent(Option 82). The length is fixed,
#                  8 HEX chars. -dhcp_ack_options must be 1 when
#                  -dhcp_ack_circuit_id is used.
#                  
#    -dhcp_ack_remote_id 
#		   Specifies the remote ID sub-option(sub-option 2) of DHCP 
#                  ACK Option relay agent(Option 82). The length is fixed,
#                  8 HEX chars. -dhcp_ack_options must be 1 when
#                  -dhcp_ack_remote_id is used.
#
#    -dhcp_ack_link_selection
#		   Specifies the link selection subnet IPv4 address(sub-option 5)
#                  of DHCP ACK Option relay agent(Option 82). The default value 
#                  is 0.0.0.0. -dhcp_ack_options must be 1 when
#                  -dhcp_ack_link_selection is used.
#              
#    -dhcp_ack_cisco_server_id_override
#   		   Specifies the Cisco server ID override IPv4 address
#                  (sub-option 152) of DHCP ACK Option relay agent(Option 82).
#		   The default value is 0.0.0.0. -dhcp_ack_options must be 1 
#                  when -dhcp_ack_cisco_server_id_override is used.
#                  
#	 -dhcp_ack_server_id_override
#		   Specifies the server ID override IPv4 address(sub-option 182)
#                  of DHCP ACK Option relay agent(Option 82). The default value
#                  is 0.0.0.0. -dhcp_ack_options must be 1 when
#                  -dhcp_ack_server_id_override is used.
#
#     -dhcp_offer_options
#		   Enable or disable DHCP OFFER Options of the emulated DHCP server. 
#                  Possible values are 0 and 1. The default value is 0(disabled).
#                  If enabled, you can specify DHCP OFFER options which will be 
#                  encapsulated in DHCP OFFER message sent to the client by DHCP server.
#         
#    -dhcp_offer_time_offset      
#                  Specifies DHCP OFFER Option time offset(Option 2) in seconds. 
#                  Its value can be positive or negative. The default value is 0.
#                  -dhcp_offer_options must be 1 when -dhcp_offer_time_offset is used.
#                   
#    -dhcp_offer_router_adddress
#		   Specifies DHCP OFFER Option router option(Option 3) IPv4 
#                  address. Multiple IPv4 addresses can be specified.
#                  The default value is  0.0.0.0. -dhcp_offer_options must 
#                  be 1 when -dhcp_offer_router_adddress is used.
#                  
#    -dhcp_offer_time_server_address    
#		   Specifies DHCP OFFER Option timer server address(Option 4).
#        	   Multiple IPv4 addresses can be specified. The default 
#                  value is  0.0.0.0. -dhcp_offer_options must be 1 when
#                  -dhcp_offer_time_server_address is used.

#    -dhcp_offer_circuit_id
#                  Specifies the circuit ID sub-option(sub-option 1) of DHCP 
#                  OFFER Option relay agent(Option 82). The length is fixed,
#                  8 HEX chars. -dhcp_offer_options must be 1 when
#                  -dhcp_offer_circuit_id is used.
#                  
#    -dhcp_offer_remote_id 
#		   Specifies the remote ID sub-option(sub-option 2) of DHCP 
#                  OFFER Option relay agent(Option 82). The length is fixed,
#                  8 HEX chars. -dhcp_offer_options must be 1 when
#                  -dhcp_offer_remote_id is used.
#
#    -dhcp_offer_link_selection
#		   Specifies the link selection subnet IPv4 address(sub-option 5)
#                  of DHCP OFFER Option relay agent(Option 82). The default value 
#                  is 0.0.0.0. -dhcp_offer_options must be 1 when
#                  -dhcp_offer_link_selection is used.
#              
#    -dhcp_offer_cisco_server_id_override
#   		   Specifies the Cisco server ID override IPv4 address
#                  (sub-option 152) of DHCP OFFER Option relay agent(Option 82).
#		   The default value is 0.0.0.0. -dhcp_offer_options must be 1 
#                  when -dhcp_offer_cisco_server_id_override is used.
#                  
#	 -dhcp_offer_server_id_override
#		   Specifies the server ID override IPv4 address(sub-option 182)
#                  of DHCP OFFER Option relay agent(Option 82). The default value
#                  is 0.0.0.0. -dhcp_offer_options must be 1 when
#                  -dhcp_offer_server_id_override is used.
#   
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.xx.
#
#    -ipv6_gateway
#    -encapsulation
#    -remote_mac
#    -ip_count
#    -spfc_mac_mask_pool
#    -spfc_mac_pattern_pool
#    -spfc_mac_ipaddress_pool
#    -spfc_mac_ipaddress_count
#    -spfc_mac_ipaddress_increment
#    -dhcp_ignore_mac
#    -dhcp_ignore_mac_mask
#    -dhcp_mac_nak
#    -dhcp_mac_nak_mask
#    -dhcp_ack_subnet_mask
#    -dhcp_offer_subnet_mask
#
#
# Return Values:
#    The sth::emulation_dhcp_server_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#     handle.port_handle  
#               The port handle on which DHCP server emulation was configured
#
#     handle.dhcp_handle
#	        The handle that identify the DHCP server emulation created by 
#               the sth::emulation_dhcp_server_config function
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_dhcp_server_config function creates, modifies, or
#    resets an emulated DHCP server. Use the -mode argument to specify the
#    action to perform. (See the -mode argument description for 
#    information about the actions.)
#   
#    Use create mode to create DHCP server on the specified port. The handle
#    of the created dhcp server host is returned. The dhcp server host can be 
#    further configured with modify mode, as well as reset mode. 
#
#    When you create an emulated DHCP server, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated DHCP server will use 
#    (The port handle value is contained in the keyed list returned by
#    the connect function.)
#
#    In addition to specifying the port, you must also provide one or more of
#    the following pieces of information when you create a DHCP server:
#
#    - The IPv4 address for the emulated DHCP server (the -ip_address argument)
#
#    - The IPv4 address for the DHCP server (DUT) to communicate with 
#       (the -ip_gateway argument)
#
#    - The first IPv4 address in the DHCP server address pool
#       (the -ipaddress_pool argument)
#
#    After you create a DHCP server, use the "emulation_dhcp_server_control 
#    -mode connect" command for Spirent HLTAPI to connect the server. 
#    To disconnect all of the DHCP server associated with a particular
#    port, use the disconnect mode with the sth::emulation_dhcp_server_control
#    function. 
#
# Examples: The following example creates a DHCP server on the specified port:
#
#    sth::emulation_dhcp_server_config \
#            -count 1 \
#            -port_handle port1 \
#            -local_mac 00:10:94:00:00:03 \
#            -ip_address 192.0.1.4 \
#            -ip_step 0.0.1.0 \
#            -ip_prefix_length 24 \
#            -ip_prefix_step 1 \
#            -ip_repeat 1 \
#            -ip_gateway 192.0.1.1 \
#            -ipaddress_pool 192.0.1.5 \
#            -ipaddress_increment 2 \
#            -ipaddress_count 30 \
#            -vlan_id 200 \
#            -vlan_ethertype 0x8100 \
#            -lease_time 20 \
#            -dhcp_ack_options 1 \
#            -dhcp_ack_time_offset 12 \
#            -dhcp_ack_router_address 10.0.0.1 \
#            -dhcp_ack_time_server_address 20.0.0.1 \
#            -dhcp_ack_circuit_id 12345678 \
#            -dhcp_ack_remote_id 87654321 \
#	     -dhcp_ack_link_selection 30.0.0.1 \
#  	     -dhcp_ack_cisco_server_id_override 40.0.0.1 \
#            -dhcp_ack_server_id_override 50.0.0.1 \
#            -dhcp_offer_options 1 \
#            -dhcp_offer_time_offset 25 \
#            -dhcp_offer_router_adddress 10.0.0.2 \
#	     -dhcp_offer_time_server_address 20.0.0.2 \			 
#            -dhcp_offer_circuit_id 22221111 \
#            -dhcp_offer_remote_id 11112222 \
#	     -dhcp_offer_link_selection 30.0.0.2 \
#  	     -dhcp_offer_cisco_server_id_override 40.0.0.2 \
#            -dhcp_offer_server_id_override 50.0.0.2 
#
#
# Sample output for example shown above:     
#       {handle {{port_handle port1} {dhcp_handle host1}}} {status 1}
#
# The following example modifies the created DHCP server:
#
#    sth::emulation_dhcp_server_config \
#           -mode modify \
#           -handle dhcpserverHandle1 \
#           -ip_address 192.0.1.6 \
#           -dhcp_ack_options 1 \
#           -dhcp_ack_time_offset 10 \
#           -dhcp_ack_circuit_id 87654321 
#
# Sample output for example shown above:  
#       {handle {dhcp_handle host1}}} {status 1}
#
#
# The following example resets the specified DHCP server:
#
#    sth::emulation_dhcp_server_config \
#           -mode reset \
#           -handle dhcpserverHandle1
#
# Sample output for example shown above:     {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_dhcp_server_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcp_server_config" $args
    
    variable ::sth::DhcpServer::userArgsArray
    variable ::sth::DhcpServer::sortedSwitchPriorityList
    array unset ::sth::DhcpServer::userArgsArray
    array set ::sth::DhcpServer::userArgsArray {}
    variable ::sth::DhcpServer::dhcpv4SetCountArg 0
    
    set _hltCmdName "emulation_dhcp_server_config"
    
    set returnKeyedList ""
    
    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6Server::emulation_dhcpv6_server_config returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName - emulation_dhcpv6_server_config: $err"
                return -code error $returnKeyedList  
            }
            return $returnKeyedList
        }
    }
    # check if user has specified device count    
    if {[lsearch $args -count] > -1} {        
        set ::sth::DhcpServer::dhcpv4SetCountArg 1
    } 
    
    if {[catch {::sth::sthCore::commandInit ::sth::DhcpServer::dhcpServerTable $args \
                                                            ::sth::DhcpServer:: \
                                                            emulation_dhcp_server_config \
                                                            ::sth::DhcpServer::userArgsArray \
                                                            ::sth::DhcpServer::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {!([info exists ::sth::DhcpServer::userArgsArray(handle)] || 
        [info exists ::sth::DhcpServer::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error : The command $_hltCmdName requires -port_handle or -handle."
        return $returnKeyedList
    }
        
    if {[info exists ::sth::DhcpServer::userArgsArray(handle)] &&
        [info exists ::sth::DhcpServer::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
            return $returnKeyedList
    }
        
    set mode create
    if {[info exists ::sth::DhcpServer::userArgsArray(mode)]} {
        set mode $userArgsArray(mode)
        if {$mode=="enable"} {
            set mode "create"
        }
    }
       
    if {[catch {::sth::DhcpServer::emulation_dhcp_server_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing DHCP Sever : $err"
        return $returnKeyedList
    }
    
    return $returnKeyedList
}

proc ::sth::emulation_dhcp_server_relay_agent_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcp_server_relay_agent_config" $args
    
    variable ::sth::DhcpServer::userArgsArray
    variable ::sth::DhcpServer::sortedSwitchPriorityList
    array unset ::sth::DhcpServer::userArgsArray
    array set ::sth::DhcpServer::userArgsArray {}
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::DhcpServer::dhcpServerTable $args \
                                                            ::sth::DhcpServer:: \
                                                            emulation_dhcp_server_relay_agent_config \
                                                            ::sth::DhcpServer::userArgsArray \
                                                            ::sth::DhcpServer::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    
    if {![info exists ::sth::DhcpServer::userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error : Missing the mandatory switch -handle ."
        return $returnKeyedList
    }
    
    set mode create
    if {[info exists ::sth::DhcpServer::userArgsArray(mode)]} {
        set mode $userArgsArray(mode)
        if {$mode=="enable"} {
            set mode "create"
        }
    }
    
    if {[catch {::sth::DhcpServer::emulation_dhcp_server_relay_agent_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $mode\ing DHCP Sever : $err"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $applyError" {}
        return -code error $returnKeyedList 
    }
    
    return $returnKeyedList
}
##Procedure Header
#
# Name:
#    sth::emulation_dhcp_server_control
#
# Purpose:
#    Connects, renews or resets DHCP server(s) on the specified ports or the 
#    dhcp handles/servers.
#
# Synopsis:
#    sth::emulation_dhcp_server_control
#       {[-action {connect|renew|reset} -port_handle <port_handle>] |
#        [-action {connect|renew|reset} -dhcp_handle <dhcp_server_handle>]}
#
# Arguments:
#
#    -dchp_handle
#                   Identifies the DHCP server handles on which to connect, renew or 
#                   disconnect the dhcp server. The -action specified will apply 
#                   only to the dhcp handles specified. It is mandatory that you 
#                   specify either -dhcp_handle or -port_handle but not both.
#                  
#    -action
#                   Specifies the action to be taken on the specified dhcp handles 
#                   specified by the dhcp_handle argument or on the port handle 
#                   specified by the port_handle argument. Possible values are
#                   connect, renew or disconnect. This argument is mandatory.
#
#                   connect  -   Connects the DHCP server on the specified port or
#                                 dhcp handle.
#
#                   renew    -   Reconnects the DHCP server on the specified port or
#                                 dhcp handle.
#
#                   reset    - Deletes the DHCP server on the specified port 
#                                   or dhcp handle.
#
#    -port_handle
#                   Specifies the port on which  DHCP server will connect, renew
#                   and disconnect. It is mandatory that you specify either
#                   -dhcp_handle or -port_handle but not both.
#                 
#
# Cisco-specific Arguments:
#     none
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status    Success (1) or failure (0) of the operation.
#         log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_dhcp_server_control function controls the DHCP server 
#    on the specified ports. You can use the function to perform several
#    actions: connecting dhcp server, renewing dhcp server, and disconnecting 
#    dhcp server.
#
#    When you call the sth::emulation_dhcp_server_control function, you specify 
#    a DHCP server handle or a port handle. Spirent HLTAPI applies the
#    specified action to the specified dhcp server or to all of the emulated
#    DCHP servers associated with the specified port.
#   
#
# Examples:
#  To connect the specified DHCP server:
#       sth::emulation_dhcp_server_control \
#                -action connect \
#                -dhcp_handle dhcpserverHandle 
#
#  To connect all DHCP server on the specified port:
#       sth::emulation_dhcp_server_control \
#                -action connect \
#                -port_handle port1
#
#  To renew the specified DHCP server:
#       sth::emulation_dhcp_server_control \
#                -action renew \
#                -dhcp_handle dhcpserverHandle 
#
#  To renew all DHCP server on the specified port:
#       sth::emulation_dhcp_server_control \
#                -action renew \
#                -port_handle port1
#
#   To reset the specified DHCP server:
#      sth::emulation_dhcp_server_control \
#                -action reset \
#                -dhcp_handle dhcpserverHandle 
#
#  To reset all DHCP server on the specified port:
#       sth::emulation_dhcp_server_control \
#                -action reset \
#                -port_handle port1
#
# Sample Input: See Examples.
#
# Sample Output: {status 1}
#
# Notes: 
#
# End of Procedure Header

proc ::sth::emulation_dhcp_server_control {args} {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::DhcpServer::sortedSwitchPriorityList
    variable ::sth::DhcpServer::userArgsArray
    array unset ::sth::DhcpServer::userArgsArray
    array set ::sth::DhcpServer::userArgsArray {}
    
    set _hltCmdName "emulation_dhcp_server_control"
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcp_server_control" $args

    set returnKeyedList ""
    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6Server::emulation_dhcpv6_server_control returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName - emulation_dhcpv6_server_control: $err"
                return -code error $returnKeyedList  
            }
            return $returnKeyedList
        }
    }

    set retVal [catch {
        if {[catch {::sth::sthCore::commandInit ::sth::DhcpServer::dhcpServerTable $args \
                                                            ::sth::DhcpServer:: \
                                                            emulation_dhcp_server_control \
                                                            ::sth::DhcpServer::userArgsArray \
                                                            ::sth::DhcpServer::sortedSwitchPriorityList} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
                    return $returnKeyedList
        }
    
        if {!([info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)] || 
            [info exists ::sth::DhcpServer::userArgsArray(port_handle)])} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $_hltCmdName requires -port_handle or -dhcp_handle."
            return $returnKeyedList
        }
        
        if {[info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)] &&
            [info exists ::sth::DhcpServer::userArgsArray(port_hanlde)]} {
            ::sth::sthCore::processError returnKeyedList "The options -port_handle or -dhcp_handle are mutually exclusive."
            return $returnKeyedList
        }
        
        set hostHandleList ""
        if {([info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)])
                && (![info exists ::sth::DhcpServer::userArgsArray(port_handle)])} {
			foreach deviceHandleList $::sth::DhcpServer::userArgsArray(dhcp_handle) {
				if {![::sth::DhcpServer::IsDhcpServerHandleValid $deviceHandleList]} {
					::sth::sthCore::processError returnKeyedList "Error: $::sth::DhcpServer::userArgsArray(dhcp_handle) is not a valid DHCP Server handle" {}
					return -code error $returnKeyedList
				}
			}
            set hostHandleList $::sth::DhcpServer::userArgsArray(dhcp_handle)
                    
        } elseif {([info exists ::sth::DhcpServer::userArgsArray(port_handle)])
                && (![info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)])} {
            
			set portList $::sth::DhcpServer::userArgsArray(port_handle)
			foreach ::sth::DhcpServer::userArgsArray(port_handle) $portList {
				if {[::sth::sthCore::IsPortValid $::sth::DhcpServer::userArgsArray(port_handle) err]} {
					set hostHandle [::sth::sthCore::invoke stc::get $::sth::DhcpServer::userArgsArray(port_handle) -affiliationport-sources]
				} else {
					::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::DhcpServer::userArgsArray(port_handle)" {}
					return -code error $returnKeyedList
				}
				foreach host $hostHandle {
					if {![::sth::DhcpServer::IsDhcpServerHandleValid $host]} {
						continue
					}
					lappend hostHandleList $host
				}
			}
			set ::sth::DhcpServer::userArgsArray(port_handle) $portList
        }
        
        switch -exact -- $::sth::DhcpServer::userArgsArray(action) {
            "renew" -
            "connect" {
                ::sth::sthCore::invoke stc::perform Dhcpv4StartServerCommand -ServerList $hostHandleList
            }
            "reset" {
                ::sth::sthCore::invoke stc::perform Dhcpv4StopServerCommand -ServerList $hostHandleList
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error:  Unsupported DHCP Server control mode $::sth::DhcpServer::userArgsArray(mode)." {}
                return -code error $returnKeyedList
            }
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList

}
##Procedure Header
#
# Name:
#    sth::emulation_dhcp_server_stats
#
# Purpose:
#    Returns statistics of the DHCP server.
#
# Synopsis:
#    sth::emulation_dhcp_server_stats
#         -dhcp_handle <dhcp_server_handle>
#         -action  {CLEAR|COLLECT}
#         -port_handle <port_handle>
#
# Arguments:
#    -dhcp_handle
#                   Specifies the dhcp server handle from which to extract DHCP 
#                   server statistics data. It is mandatory that either -dhcp_handle 
#                   or -port_handle, but not both, be specified
#
#    -action
#                   Specifies the action of the statistics for the specified port
#                   or DHCP server. Possible values are CONNECT and CLEAR.
#
#                   COLLECT  - collects the statistics for the specified port or 
#                                DHCP server 
#
#                   CLEAR    - clears the statistics for the specified port or 
#                                DHCP server 
#
#    -port_handle
#                   Specifies the ports from which to extract DHCP server
#                   statistics data.It is mandatory that either -dchp_handle 
#                   or -port_handle, but not both, be specified
#                  
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null
#
#         aggregate statistics
#						 Provided when -port_handle is used. Contains the
#                        aggregate statistics from all the DHCP handles/servers
#                        on the specified port_handle.
#     
#         server specific statistics
#						 Provided when -dhcp_server is used. Contains the statistics
#                        from the specified DHCP handle/server.
#
#    The following keys are returned when you specify -port_handle:
#
#    aggregate.<port_handle>.rx.discover 
#    aggregate.<port_handle>.rx.offer        (not supported)
#    aggregate.<port_handle>.rx.request
#    aggregate.<port_handle>.rx.decline
#    aggregate.<port_handle>.rx.ack           (not supported)
#    aggregate.<port_handle>.rx.nak           (not supported)
#    aggregate.<port_handle>.rx.release
#    aggregate.<port_handle>.rx.inform
#    aggregate.<port_handle>.rx.force_renew  (not supported)
#    aggregate.<port_handle>.rx.relay_agent  (not supported)
#    aggregate.<port_handle>.tx.discover      (not supported)
#    aggregate.<port_handle>.tx.offer
#    aggregate.<port_handle>.tx.request       (not supported)
#    aggregate.<port_handle>.tx.decline       (not supported)
#    aggregate.<port_handle>.tx.ack
#    aggregate.<port_handle>.tx.nak
#    aggregate.<port_handle>.tx.release        (not supported)
#    aggregate.<port_handle>.tx.inform         (not supported)
#    aggregate.<port_handle>.tx.force_renew   (not supported)
#    aggregate.<port_handle>.allocated.ip      (not supported)
#
#    The following keys are returned when you specify -dhcp_handle:
#
#     dhcp_handle.<dhcp_handle>.rx.discover
#     dhcp_handle.<dhcp_handle>.rx.offer        (not supported)
#     dhcp_handle.<dhcp_handle>.rx.request
#     dhcp_handle.<dhcp_handle>.rx.decline
#     dhcp_handle.<dhcp_handle>.rx.ack           (not supported)
#     dhcp_handle.<dhcp_handle>.rx.nak           (not supported)
#     dhcp_handle.<dhcp_handle>.rx.release
#     dhcp_handle.<dhcp_handle>.rx.inform
#     dhcp_handle.<dhcp_handle>.rx.force_renew   (not supported)
#     dhcp_handle.<dhcp_handle>.rx.relay_agent   (not supported)
#     dhcp_handle.<dhcp_handle>.tx.discover       (not supported)
#     dhcp_handle.<dhcp_handle>.tx.offer
#     dhcp_handle.<dhcp_handle>.tx.request        (not supported)
#     dhcp_handle.<dhcp_handle>.tx.decline        (not supported)
#     dhcp_handle.<dhcp_handle>.tx.ack
#     dhcp_handle.<dhcp_handle>.tx.nak
#     dhcp_handle.<dhcp_handle>.tx.release        (not supported)
#     dhcp_handle.<dhcp_handle>.tx.inform         (not supported)
#     dhcp_handle.<dhcp_handle>.tx.force_renew   (not supported)
#     dhcp_handle.<dhcp_handle>.allocated.ip      (not supported)
#
# Description:
#    The sth::emulation_dhcp_server_info function provides statistics datas for
#    DHCP server about either the DHCP server handles or ports specified.    
#
#    This function returns the requested data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message. Function return values are formatted as a keyed list
#    (supported by the Tcl extension software - TclX). Use the TclX function
#    keylget to retrieve data from the keyed list. (See Return Values for a
#    description of each key.)
#
# Examples:
#    The following example collects statistics on the specified port:
#      
#      ::sth::emulation_dhcp_server_stats
#                    -action COLLECT \
#                    -port_handle port1
#
#   Sample output for example shown above:   
#      {dhcp_server_state UP} {aggregate {{port1 {{tx {{nak 0}
#      {offer 0} {ack 0}}} {rx {{decline 0} {release 0}
#      {request 0} {inform 0} {discover 0}}}}}}} {status 1}
#
#	The following example collects statistics on the specified DCHP server:
#
#       ::sth::emulation_dhcp_server_stats
#                    -action COLLECT \
#                    -dhcp_handle host1
#
#   Sample output for example shown above:   
#      {dhcp_server_state UP} {dhcp_handle {{host1 {{tx {{nak 0}
#      {offer 0} {ack 0}}} {rx {{decline 0} {release 0}
#      {request 0} {inform 0} {discover 0}}}}}}} {status 1}
#
#   The following example clears statistics on the specified port:
#       ::sth::emulation_dhcp_server_stats
#                    -action CLEAR \
#                    -port_handle host1
#
#   Sample output for example shown above:  	{status 1}
#
#   The following example clears statistics on the specified DHCP server:
#       ::sth::emulation_dhcp_server_stats
#                    -action CLEAR \
#                    -dhcp_handle host1
#
#   Sample output for example shown above:  	{status 1}
#  
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes: 
#
# End of Procedure Header

proc ::sth::emulation_dhcp_server_stats {args} {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcp_server_stats" $args
    
    variable ::sth::DhcpServer::sortedSwitchPriorityList
    variable ::sth::DhcpServer::userArgsArray
    array unset ::sth::DhcpServer::userArgsArray
    array set ::sth::DhcpServer::userArgsArray {}
     
    set returnKeyedList ""
    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6Server::emulation_dhcpv6_server_stats returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName - emulation_dhcpv6_server_stats: $err"
                return -code error $returnKeyedList  
            }
            return $returnKeyedList
        }
    }

    if {[catch {::sth::sthCore::commandInit ::sth::DhcpServer::dhcpServerTable $args \
							::sth::DhcpServer:: \
							emulation_dhcp_server_stats \
							userArgsArray \
							sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
    }
    
    if {![info exists ::sth::DhcpServer::userArgsArray(action)]} {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: -action" {}
        return -code error $returnKeyedList
    }
    set action [string tolower $::sth::DhcpServer::userArgsArray(action)]
    
    if {[catch {::sth::DhcpServer::emulation_dhcp_server_stats_$action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
	return -code error $returnKeyedList
    }
    
    return $returnKeyedList  
}
