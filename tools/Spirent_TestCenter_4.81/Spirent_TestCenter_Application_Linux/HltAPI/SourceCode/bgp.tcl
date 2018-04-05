# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth:: {
}

##Procedure Header
#
# Name:
#    sth::emulation_bgp_config
#
# Purpose:
#    Creates, enables, modifies, or deletes an emulated Border Gateway Protocol
#    (BGP) router on a Spirent HLTAPI chassis. BGP is a protocol for
#    exchanging routing information between border gateway routers in a network
#    of autonomous systems.
#
# Synopsis:
#    sth::emulation_bgp_config
#         -mode {enable|disable|modify|reset}
#         [-active_connect_enable {1|0}]
#         [-count <integer>]
#         [-graceful_restart_enable {1|0}]
#              [-restart_time <0-10000000> ]
#         [-handle <router_handle>]
#         [-hold_time <3-65535>]
#         [-ip_version {4|6}]
#         [-ipv4_mpls_nlri {1|0}]
#         [-ipv4_mpls_vpn_nlri {1|0}]
#         [-ipv4_multicast_nlri {1|0}]
#         [-ipv4_unicast_nlri {1|0}]
#         [-ipv6_mpls_nlri {1|0}]
#         [-ipv6_mpls_vpn_nlri {1|0}]
#         [-ipv6_multicast_nlri {1|0}]
#         [-ipv6_unicast_nlri {1|0}]
#         [-local_as_mode {fixed|increment}]
#              [-local_as <0-65535> ]
#              [-local_as mode {fixed|increment}]
#              [-local_as_step <integer>]
#         [-local_addr_step {<a.b.c.d> |
#              <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}]
#         [-local_ip_addr <a.b.c.d>]
#         [-local_ipv6_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-local_router_id <a.b.c.d.>]
#         [-mac_address_start <aa:bb:cc:dd:ee:ff>]
#         [-md5_enable {1|0}]
#         [-netmask   <1-128> ]
#         [-next_hop_ip {<a.b.c.d> |
#              <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}]
#         [-port_handle <port_handle>]
#         [-remote_addr_step {<a.b.c.d> |
#              <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}]
#         [-remote_as <0-65535>]
#         [-remote_ip_addr <a.b.c.d>]
#         [-remote_ipv6_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-retries <0-65535>]
#         [-retry_time <10-300>]
#         [-routes_per_msg <0-10000>]
#         [-staggered_start_enable {0|1}]
#         [-staggered_start_time <0-10000>]
#         [-update_interval <0-10000>]
#         [-vlan_cfi {1|0}]
#         [-vlan_id <0-4095>]
#         [-vlan_id_mode {fixed|increment}]
#         [-vlan_id_step <1-4094>]
#         [-vlan_user_priority <0-7>]
#         [-vlan_outer_id <0-4095>]
#         [-vlan_outer_id_mode {fixed|increment}]
#         [-vlan_outer_id_step <1-4094>]
#         [-vlan_outer_user_priority <0-7>]
#
# Arguments:
#    -active_connect_enable
#                   Indicates whether or not the emulated router will initiate
#                   the session. Possible values are 0 and 1. The default is 0
#                   (disabled). If enabled, the emulated router will send an
#                   OPEN message without waiting for the device under test to
#                   send its OPEN message.
#
#    -count         Defines the number of BGP routers to create. Possible values
#                   are 0 to <max_int>. The default is 1.
#
#    -graceful_restart_enable
#                   Enables a graceful restart operation on an emulated router
#                   within a specified amount of time or "grace period."
#                   Graceful restart allows a router undergoing a restart to
#                   inform its adjacent neighbors and peers of its condition and
#                   to preserve its forwarding table during a BGP restart
#                   operation. Possible values are 0 and 1. The default is 0.
#
#                   If you enable this option, you must also use the
#                   -restart_time argument to specify the time allowed for the
#                   restart operation.
#
#                   There are two modes of graceful restart for BGP: restart
#                   speaker and receiving speaker. When the receiving speaker
#                   (which may be the emulated router or the DUT) receives a
#                   graceful restart capability in the BGP OPEN message, it will
#                   keep the routers advertised by the restart router before the
#                   restart time expires for forwarding traffic. When the
#                   restart speaker does not come up within the restart_time,
#                   the receiving speaker will delete the routes and stop using
#                   them to forward traffic. In general, restart time (see
#                   -restart_time) should not be greater than hold time (see
#                   -hold_time).
#
#    -handle        Specifies the BGP handle, a string value, to use when mode
#                   is set to "modify." This argument is required only for
#                   modify mode.
#
#    -hold_time
#                   Defines the session expiration interval in seconds. The
#                   expiration interval determines how long to wait for a
#                   KEEPALIVE message before ending a BGP session for an
#                   emulated router. Spirent HLTAPI also uses the -hold_time
#                   value to determine the interval between transmitted
#                   KEEPALIVE messages. The transmission interval is one-third
#                   of the session expiration interval. Possible -hold_time
#                   values range from 3 to 65535. The default is 90. (Therefore,
#                   using the default value, Spirent HLTAPI will transmit
#                   KEEPALIVE messages every 30 seconds.)
#
#    -ip_version
#                   Specifies the IP version of the BGP emulated router.
#                   Possible values are 4 (for IPv4 address format) or 6 (for
#                   IPv6 address format).
#
#    -ipv4_mpls_nlri
#                   Enables or disables support for IPv4 multiprotocol label
#                   switching (MPLS) in the Capabilities Optional Parameter and
#                   Multiprotocol Extensions parameter of the OPEN message.
#                   Possible values are 0 and 1. If you set this value to 1,
#                   support for IPv4 MPLS is advertised in the Capabilities
#                   Optional Parameter/Multiprotocol Extensions parameter of the
#                   OPEN message.
#
#    -ipv4_mpls_vpn_nlri
#                   Enables or disables support for IPv4 MPLS VPN. Possible
#                   values are 0 and 1. If you set this value to 1, support for
#                   IPv4 MPLS VPN is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -ipv4_multicast_nlri
#                   Enables or disables support for IPv4 multicast. Possible
#                   values are 0 and 1. If you set this value to 1, support for
#                   IPv4 multicast is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -ipv4_unicast_nlri
#                   Enable or disable support for IPv4 Unicast. Possible values
#                   are 0 and 1. If you set this value to 1, support for IPv4
#                   unicast is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -ipv6_mpls_nlri
#                   Enable or disable support for IPv6 multiprotocol label
#                   switching (MPLS) in the Capabilities Optional Parameter and
#                   Multiprotocol Extensions parameter of the OPEN message.
#                   Possible values are 0 and 1. If you set this value to 1,
#                   support for IPv6 MPLS is advertised in the Capabilities
#                   Optional Parameter/Multiprotocol Extensions parameter of the
#                   OPEN message.
#
#    -ipv6_mpls_vpn_nlri
#                   Enable or disable support for IPv6 MPLS VPN. Possible values
#                   are 0 and 1. If you set this value to 1, support for IPv6
#                   MPLS VPN is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -ipv6_multicast_nlri
#                   Enable or disable support for IPv6 Multicast. Possible
#                   values are 0 and 1. If you set this value to 1, support for
#                   IPv6 multicast is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -ipv6_unicast_nlri
#                   Enable or disable support for IPv6 Unicast. Possible values
#                   are 0 and 1. If you set this value to 1, support for IPv6
#                   unicast is advertised in the Capabilities Optional
#                   Parameter/Multiprotocol Extensions parameter of the OPEN
#                   message.
#
#    -local_addr_step
#                   Defines the increment used to generate IP addresses for
#                   emulated routers. Spirent HLTAPI increments the
#                   -local_ip_addr value or the -local_ipv6_addr, depending on
#                   the IP version you are using. You must specify the local
#                   address step when the -count argument is greater than 1.
#                   The value can be in either IPv4 or IPv6 format, depending on
#                   the value of the IP version specified in -ip_version..
#    -local_as
#                   The Autonomous System number of the emulated BGP router.
#                   Possible values range from 1 to 65535. The default is 1.
#
#    -local_as mode 
#                   When configuring multiple BGP4 neighbors, sets the 
#                   -local_as for multiple neighbors. Possible values are fixed 
#                   or increment. The default is fixed.
#
#    -local_as_step
#                   When configuring multiple BGP4 neighbors, defines the step
#                   of the increment for the -local_as.
#
#    -local_ip_addr
#                   Specifies the IPv4 address of the emulated router. The
#                   default is 192.85.1.3.
#
#    -local_ipv6_addr
#                   Specifies the IPv6 address of the emulated router. The
#                   default is 2000::2.
#
#    -local_router_id
#                   Identifies the router from which a packet originated. The
#                   router identifier is the IP address of the emulated router.
#                   The default is 192.0.0.1.
#
#    -mac_address_start
#                   Initial MAC address of the interfaces created for the BGP
#                   neighbor configuration. 
#
#    -md5_enable
#                   Enables or disables MD5 authentication for the emulated BGP
#                   node. Possible values are 0 (disable) and 1 (enable). The 
#                   default is 0.
#
#    -mode
#                   Specifies the action to perform on the specified test port. 
#                   Possible values are enable, disable, modify, or reset. The 
#                   modes are described below:
#
#                   enable - Creates one or more emulated routers. To create
#                        routers, specify the -port_handle argument and
#                        additional arguments to supply address information for
#                        the emulated routers.
#
#                   disable - Same as description for "reset".
#
#                   modify - Changes the configuration for the emulated router
#                        identified by the -handle argument.
#
#                   reset - Deletes all BGP routers associated with the
#                        specified port. 
#
#    -netmask
#                   The prefix length of the BGP router's IP address (v4 or v6),
#                   in number of bits. For IPv4 addresses, the netmask range is
#                   from 1 to 32, and the default is 24. For IPv6 addresses, the
#                   netmask range is 1 to 128, and its default is 64.
#
#    -next_hop_ip
#                   Configures the IP address of the next hop in IP traffic.
#                   The hop address is the IP address STC uses to reach the
#                   advertising router. The "next hop" is the next router to
#                   forward a packet to its final destination.
#
#    -port_handle
#                   The port on which to create the emulated router. This handle
#                   is returned by the sth::connect function.
#
#    -remote_addr_step
#                   Defines the increment used to generate remote IP addresses
#                   for emulated routers. Spirent HLTAPI increments either 
#                   the -remote_ip_addr value or the -remote_ipv6_addr, 
#                   depending on the IP version you are using. You must specify 
#                   the remote address step when the -count argument is greater 
#                   than 1. The value can be in either IPv4 or IPv6 format, 
#                   depending on the IP version specified in -ip_version..
#
#    -remote_as
#                   The Autonomous System number of the DUT. Possible values
#                   range from 0 to 65535. The default is 1001.
#
#    -remote_ip_addr
#                   IPv4 address of the DUT interface that is connected to the
#                   Spirent HLTAPI port for the emulated router. The default
#                   is 192.85.1.1.
#
#    -remote_ipv6_addr
#                   IPv6 address of the DUT interface that is connected to the
#                   Spirent HLTAPI port for the emulated router. The default
#                   is 2000::1.
#
#    -restart_time
#                   Specifies the maximum number of seconds allowed to re-
#                   establish a BGP session between the emulated router and the
#                   DUT (peer router) following a restart operation. When the
#                   router restarts its BGP process, the DUT marks all routes as
#                   "stale," but continues to use them to forward packets based
#                   on the expectation that the restarting router will re-
#                   establish the BGP session shortly. If the time expires
#                   before the router restarts, then the DUT will start sending
#                   the routing information, which will cause problems for the
#                   restart router. Therefore, be sure to allow enough time.
#                   Possible values range from 1 to 255. The default is 90
#                   seconds. Specify the restart time only if
#                   -enable_graceful_restart is enabled.
#
#    -retries
#                   Specifies the number of times that Spirent HLTAPI will
#                   attempt to establish a connection with the DUT router(s).
#                   Possible values range from 0 to 65535. The default is 100.
#
#    -retry_time
#                   Specifies the time in seconds between attempts to establish
#                   a connection for the session. Possible values range from 10
#                   to 300. The default is 30.
#
#    -routes_per_msg
#                   The maximum number of prefixes to encode in an UPDATE
#                   message. Possible values range from 0 to 10000. The default
#                   is 2000.
#
#    -staggered_start_enable
#                   Determines whether emulated routers advertise their routes
#                   sequentially across ports. If enabled, Spirent HLTAPI
#                   sends BGP OPEN messages for each session in a staggered
#                   fashion. The interval between each OPEN message is defined
#                   in the -staggered_start_time argument. Possible values are
#                   0 and 1. The default is 0.
#
#    -staggered_start_time
#                   Specifies the staggered start interval between OPEN
#                   messages, in milliseconds. Possible values range from 0 to
#                   10000. The default is 100.
#
#    -vlan_cfi
#                   Sets the canonical format indicator field in VLAN for the
#                   emulated router node. Possible values are 0 (Ethernet) and 1
#                   (Token Ring). The default is 1. If set to 0, it indicates
#                   the network is Ethernet. If set to 1, it indicates that
#                   Token Ring and packets are dropped by Ethernet ports.
#
#    -update_interval
#                   The time, in milliseconds, to wait before sending the next
#                   UPDATE message to the DUT. Possible values range from 0 to
#                   10000. The default is 30.
#
#    -vlan_id
#                   The VLAN ID of the first VLAN sub-interface. Possible values
#                   range from 0 to 4095. The default is 1.
#
#    -vlan_id_mode
#                   Specifies VLAN ID assignment for multiple router
#                   configurations when -count is greater than 1. Valid values
#                   are "fixed" or "increment". If you specify "fixed", all of
#                   the routers will be assigned the same VLAN ID (the value of
#                   the -vlan_id argument). If you specify "increment", then
#                   Spirent HLTAPI assigns unique VLAN IDs. When you use
#                   increment mode, you must also specify the -vlan_id_step
#                   argument to define the increment value.
#
#    -vlan_id_step
#                   The value that Spirent HLTAPI uses to increment the VLAN
#                   ID. You must specify this step when you use specify
#                   "increment" for the -vlan_id_mode argument and the router
#                   count (-count) is greater than 1. Possible step values range
#                   from 1 to 4094.
#
#    -vlan_user_priority
#                   VLAN priority for the VLANs on this port. Possible values
#                   range from 0 to 7. The default is 0.
#
#    -vlan_outer_id
#                   The OUTER VLAN ID of VLAN sub-interface. Possible values
#                   range from 0 to 4095. The default is 1.
#
#    -vlan_id_mode
#                   Specifies OUTER VLAN ID assignment for multiple router
#                   configurations when -count is greater than 1. Valid values
#                   are "fixed" or "increment". If you specify "fixed", all of
#                   the routers will be assigned the same VLAN ID (the value of
#                   the -vlan_id argument). If you specify "increment", then
#                   Spirent HLTAPI assigns unique VLAN IDs. When you use
#                   increment mode, you must also specify the -vlan_id_step
#                   argument to define the increment value.
#
#    -vlan_id_step
#                   The value that Spirent HLTAPI uses to increment the OUTER VLAN
#                   ID. You must specify this step when you use specify
#                   "increment" for the -vlan_id_mode argument and the router
#                   count (-count) is greater than 1. Possible step values range
#                   from 1 to 4094.
#
#    -vlan_user_priority
#                   VLAN priority for the OUTER VLANs on this port. Possible values
#                   range from 0 to 7. The default is 0.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -advertise_host_route
#    -local_router_id_enable
#    -modify_outgoing_as_path
#    -neighbor_type
#    -next_hop_enable
#    -next_hop_mode
#    -next_hop_ip_version
#    -remote_confederation_member
#    -reset
#    -route_refresh
#    -stale_time
#    -suppress_notify
#    -tcp_window_size
#    -timeout
#    -update_interval
#    -update_msg_size
#    -vci
#    -vci_step
#    -vpi
#    -vpi_step
#
#
# Return Values:
#    The sth::emulation_bgp_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handles   A list of handles that identify the routers created by the
#              sth::emulation_bgp_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description: 
#    The sth::emulation_bgp_config function creates, enables,
#    modifies, or deletes an emulated BGP router. Use the -mode argument to
#    specify the action to perform. (See the -mode argument description for
#    information about the actions.)
#
#    When you create an emulated router, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated router will use for
#    BGP communication. (The port handle value is contained in the keyed list
#    returned by the connect function.)
#
#    In addition to specifying the port, you must also provide one or more of
#    the following pieces of information when you create a router:
#
#    - The IP address for the emulated router (the -local_router_id or
#      -local_ipv6_addr argument)
#
#    - The IP address for the BGP router (DUT) to communicate with (the
#      -remote_ip_addr or -remote_ipv6_addr argument)
#
#    - The autonomous systems for the emulated router and its BGP router for the
#      session (the -local_as or -remote_as argument)
#
#    - The hold time value the emulated router will use (the -hold_time
#      argument)
#
#    - The amount of time between UPDATE messages (the -update_interval
#      argument)
#
#    - VLAN membership information (the -vland_id, vlan_id_mode, and/or
#      vlan_id_step arguments)
#
#    After you create a router, use the "emulation_bgp_control -mode start"
#    command for Spirent HLTAPI to start the router communication.
#    A BGP session is a periodic stream of BGP messages sent between BGP peers
#    - an OPEN message followed by a series of UPDATE and KEEPALIVE messages.
#    OPEN messages establish the session. BGP routers use KEEPALIVE messages
#    to maintain sessions, and UPDATE messages to exchange routing table data.
#    Session termination is indicated by a NOTIFICATION message.
#
#    Once you start sessions, Spirent HLTAPI handles all of the message
#    traffic for the emulated routers. During the test, use the
#    sth::emulation_bgp_control function to stop and re-start individual
#    routers. To stop and start all of the routers associated with a particular
#    port, use the restart mode with the sth::emulation_bgp_control
#    function. After you have created the routers for your test, use the
#    sth::emulation_bgp_route_config function to set up routes.
#
# Examples: The following example creates a BGP router:
#
#    sth::emulation_bgp_config
#                   -active_connect_enable 0 \
#                   -mode enable \
#                   -count 1 \
#                   -graceful_restart_enable 0 \
#                   -hold_time 50 \
#                   -ip_version 4 \
#                   -ipv4_mpls_nlri 0 \
#                   -ipv4_mpls_vpn_nlri 0 \
#                   -ipv4_multicast_nlri 0 \
#                   -ipv4_unicast_nlri 0 \
#                   -local_addr_step 0.0.2.0 \
#                   -local_as 5 \
#                   -local_as_step 1 \
#                   -local_ip_addr 192.168.1.6 \
#                   -local_router_id 192.168.1.6 \
#                   -mode enable \
#                   -netmask 24 \
#                   -next_hop_ip 192.168.1.1 \
#                   -port_handle $port_handle1 \
#                   -remote_addr_step 0.0.1.0 \
#                   -remote_as 6 \
#                   -remote_ip_addr 192.168.2.1 \
#                   -restart_time 50 \
#                   -retries 5 \
#                   -retry_time 50 \
#                   -routes_per_msg 5 \
#                   -staggered_start_time 30 \
#                   -update_interval 50 \
#                   -vlan_cfi 0 \
#                   -vlan_id 5 \
#                   -valn_id_mode increment \
#                   -vlan_id_step 1 \
#                   -vlan_user_priority 1
#
# Sample output for example shown above:     {handles router1} {status 1}
#
# The following example stops all routers on the specified port:
#
#    sth::emulation_bgp_config -mode disable -port_handle port1
#
# Sample output for example shown above:     {status 1}
#
# The following example modifies handle router1:
#
#    sth::emulation_bgp_config \
#         -mode modify \
#         -handle router1 \
#         -active_connect_enable 1 \
#         -remote_as 123
#
# Sample output for example shown above:     {status 1}
#
# The following example creates five BGP routers:
#
# sth::emulation_bgp_config -mode enable \
#    -port_handle port1 \
#    -count 5 \
#    -active_connect_enable 1 \
#    -ip_version 4 \
#    -local_ip_addr 61.25.0.11 \
#    -remote_ip_addr 61.25.0.1 \
#    -next_hop_ip 61.25.0.1 \
#    -local_as 123 \
#    -local_router_id 61.25.0.11 \
#    -remote_as 123 -vlan_id 101 \
#    -vlan_id_mode increment \
#    -vlan_id_step 1  \
#    -local_addr_step 0.0.1.0 \
#    -remote_addr_step 0.0.0.1 \
#    -retry_time 30 \
#    -retries 10 \
#    -routes_per_msg 20 \
#    -hold_time 180 \
#    -update_interval 45 \
#    -ipv4_unicast_nlri 1
#
# Sample output for example shown above:
#    {handles router1 router2 router3 router4 router5} {status 1}
#
# The following example deletes all BGP routers on the specified port:
#
# sth::emulation_bgp_config -mode reset \
#    -port_handle port1
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

proc ::sth::emulation_bgp_config { args } {
    ::sth::sthCore::Tracker ::sth::emulation_bgp_config $args

    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_config \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	# remap "reset" mode to "disable"
    set mode [string map -nocase {reset disable} $::sth::Bgp::userArgsArray(mode)]
    
	if {[catch {::sth::Bgp::emulation_bgp_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}
        
        #add by Fei Cheng. 2008-7-7
        if {!$::sth::sthCore::optimization} {
            if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}

	    }
        }

	return $returnKeyedList	
}

##Procedure Header
#
# Name:
#    sth::emulation_bgp_control
#
# Purpose:
#    Starts or stops a BGP router from routing traffic for the specified
#    port.
#
# Synopsis:
#    sth::emulation_bgp_control
#         { [-mode stop -handle <port_handle> |
#            -mode {start|restart|link_flap|full_route_flap} 
#          -handle <port_handle>]
#         }
#         [-link_flap_down_time <0-10000000>]
#         [-link_flap_up_time <0-10000000>]
#         [-route_flap_down_time <integer>]
#         [-route_flap_up_time <integer>]
#         [-route_handle <BGP_route_handle>]
#
# Arguments:
#
#    -handle
#                   Identifies the port on which to stop or start the router.
#                   This argument is required. If link flapping is enabled,
#                   specifies on which BGP neighbor the action will be taken.
#                   If route flapping is enabled, specifies on which BGP route
#                   range the action will be taken..
#
#    -link_flap_down_time
#                   Specifies the amount of time, in seconds, that the link is
#                   disconnected. This argument is valid only when -mode is set 
#                   to "link_flap".
#
#    -link_flap_up_time
#                   Specifies the amount of time, in seconds, that the link is
#                   connected. This argument is valid only when -mode is set to 
#                   "link_flap".
#
#    -mode
#                   Specifies the action to be taken. Possible values are stop,
#                   start, or restart the BGP router. This argument is required.
#
#                   stop - Stops the router for the specified port.
#
#                   start - Starts the router for the specified port.
#
#                   restart - Stops and then starts the router for the
#                        specified port.
#
#                   link_flap - Disconnects and then reconnects the link to the
#                        router based on the settings for -link_flap_up_time 
#                        and -link_flap_down_time.
#
#                   full_route_flap - Enables flapping functions on the 
#                        route handle (-route_handle) based on the settings for 
#                        -route_flap_up_time and -route_flap_down_time.
#
#                   Note: The "partial_route_flap option is not supported.
#
#    -route_flap_down_time
#                   During a flapping operation, specifies the period of time, 
#                   in seconds, during which the route will be withdrawn from 
#                   its neighbors. This argument is valid only when -mode is set 
#                   to "full_route_flap". 
#
#    -route_flap_up_time
#                   During a flapping operation, specifies the time, in seconds,
#                   between flap cycles. This argument is valid only when -mode 
#                   is set to "full_route_flap". 
#
#    -route_handle
#                   Specifies the handles of the BGP routes on which to enable 
#                   flapping. Use this argument when the mode is set to 
#                   "full_route_flap".
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -route_index_from
#    -route_index_to
# 
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         stopped   Stopped (1) or Running (0)
#         status    Success (1) or failure (0) of the operation.
#         log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_bgp_control function controls the routing of
#    traffic through the specified ports. You can use the function to perform
#    several actions: starting routers, stopping routers, restarting routers, 
#    and controlling route flapping. 
#
#    In normal network operation, routers advertise changes to routes. 
#    In response to these changes, routers recalculate the routes and update 
#    routing tables. A network may become unstable; for example, routers may go 
#    down, there may problems with connections, or there may be some other type 
#    of problem with the network. When the network topology changes rapidly, the 
#    repeated advertising and withdrawal of routing information is called "route 
#    flapping". When route flapping occurs, the network performance degrades due 
#    to the increased routing communication and to the time it takes for routers 
#    to reconfigure the routing table. 
#
#    Spirent HLTAPI enables you to use flapping in your network environment. 
#    You can use flapping to control various kind of events in your test 
#    environment, including routing. When you use the sth::emulation_bgp_control 
#    function to define flapping for your test:
#
#    - Define the flapping mode with "-mode full_route_flap". 
#    - Set -route_flap_down_time and -route_flap_up_time to define the flapping 
#      cycle.
#    - Specify the route to flap using -route_handle.
#
#    Note: The sth:emulation_bgp_control function does not include a flapping 
#    count argument because it only does one flap (for example, -flap_count is
#    always equal to 1). 
#
#    When you call the sth::emulation_bgp_control function, you specify a port
#    handle. Spirent HLTAPI applies the specified action to all of the
#    emulated BGP routers associated with the specified port.
#
#    - When you stop a router, Spirent HLTAPI sends a NOTIFICATION message
#      to terminate the session and shut down the connection.
#
#    - When you start a router, Spirent HLTAPI sends an OPEN message to
#      start the BGP message exchange and re-establish the session.
#
#    - When you restart a router, Spirent HLTAPI sends a NOTIFICATION
#      message, followed by an OPEN message.
#
# Examples:
#    To start the BGP router on the specified port:
#
#         sth::emulation_bgp_control -mode start -handle router1
#
#    To stop the BGP router on the specified port:
#
#         sth::emulation_bgp_control -mode stop -handle router1
#
#    To restart the BGP router on the specified port:
#
#         sth::emulation_bgp_control -mode restart -handle router1
#
#    To control route flapping, 
#
#    sth::emulation_bgp_control -mode full_route_flap \
#         -handle router1 -route_handle bgpipv4routeconfig1 \
#         -route_flap_up_time 10 \
#         -route_flap_down_time 10
#
#    To control link flapping, 
#
#    sth::emulation_bgp_control -mode link_flap \
#         -handle router1  \
#         -link_flap_up_time 30 \
#         -link_flap_down_time 30
#
# Sample Input: See Examples.
#
# Sample Output: {handle router1} {status 1}
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bgp_control {args} {
    ::sth::sthCore::Tracker ::sth::emulation_bgp_control $args 

    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_control \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::Bgp::emulation_bgp_control returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_bgp_info
#
# Purpose:
#    Returns information about the BGP configuration.
#
# Synopsis:
#    sth::emulation_bgp_info
#         -handle <port_handle>
#         -mode   {stats|settings|neighbors}
#
# Arguments:
#    -handle
#                   The port for which you want information.
#
#    -mode
#                   Specifies the kind of information you want to see. Possible
#                   values are stats and settings. The default is stats.
#
#                   stats  - returns transmitted and received statistics for
#                        different BGP messages.
#
#                   settings - returns the address and AS number of the
#                        specified handle.
#
#                   neighbors - returns the list of BGP peers.
#
#                   Note: The "labels" and "clear_stats" options are not 
#                   supported.
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         stats          Retrieves the IP address of the specified port and the
#                        number of OPEN, UPDATE, NOTIFICATION, and KEEPALIVE
#                        messages transmitted and received (see list below).
#
#         settings       Retrieves the IP address of the specified port and the
#                        number of the Autonomous System for the emulated router
#                        and its BGP router (see list below).
#
#         neighbors      Retrieves the IP addresses of the BGP session's peers.
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null
#
#    The following keys are returned when you specify -mode stats:
#
#         ip_address     IP address of the port on the interface card: a.b.c.d.
#
#         asn            The number of the Autonomous System for the emulated
#                        router and its BGP peer.
#
#         peers          List of BGP peer IP addresses.
#
#         update_tx      Number of BGP UPDATE messages successfully transmitted.
#
#         update_rx      Number of BGP UPDATE messages received.
#
#         keepalive_tx   Number of BGP KEEPALIVE messages successfully
#                        transmitted.
#
#         keepalive_rx   Number of BGP KEEPALIVE messages received.
#
#         open_tx        Number of BGP OPEN messages successfully transmitted.
#
#         open_rx        Number of BGP OPEN messages received.
#
#         notify_tx      Number of BGP NOTIFICATION messages successfully
#                        transmitted.
#
#         notify_rx      Number of BGP NOTIFICATION messages received.
#
#         Note: duration, routing_protocol, and num_node_routes are not 
#               supported.
#
#    The following keys are returned when you specify -mode settings:
#
#         ip_address     IP address of the port on the interface card: a.b.c.d.
#
#         asn            The number of the Autonomous System for the emulated
#                        router and its BGP peer.
#
#    The following keys are returned when you specify -mode neighbors:
#
#         peers          List of BGP peer IP addresses.
#
#
#
# Description:
#    The sth::emulation_bgp_info function provides information about either
#    the settings specified for the BGP configuration, the statistics
#    returned by it, or its neighbors.
#
#    This function returns the requested data (statistics, settings, or neighbor
#    information) and a status value (1 for success). If there is an error, the
#    function returns the status value (0) and an error message. Function return
#    values are formatted as a keyed list (supported by the Tcl extension
#    software - TclX). Use the TclX function keylget to retrieve data from the
#    keyed list. (See Return Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input: sth::emulation_bgp_info -mode settings -handle router1
#
# Sample Output: {ip_address 90.0.0.3} {asn 3} {status 1}
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bgp_info {args} {
    ::sth::sthCore::Tracker ::sth::emulation_bgp_info $args 

    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_info \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::Bgp::emulation_bgp_info returnKeyedList} eMsg]} { 
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_bgp_route_config
#
# Purpose:
#    Creates routes for or deletes routes from a BGP router. It
#    also defines the characteristics of the routes that will be advertised at
#    the beginning of the session.
#
#    When you add a route (see description for -mode), Spirent HLTAPI
#    returns the route handle in a keyed list with "handles" as the key.
#
# Synopsis:
#    sth::emulation_bgp_route_config
#         -mode {add|remove}
#         [-aggregator { asn:ipv4}]
#         [-as_path { <as path type>:<comma separated segment list>}]
#         [-atomic_aggregate {0|1}]
#         [-cluster_list {0|1}]
#         [-cluster_list_enable {0|1}]
#         [-communities {as_id:<asn>,<user data>}]
#         [-communities_enable {0|1}]
#         [-handle <router_handle>]
#         [-ip_version   {4|6}]
#         [-ipv6_prefix_length <0-128>]
#         [-label_incr_mode {fixed|prefix}]
#         [-local_pref <0-4294927695>]
#         [-max_route_ranges <integer>]
#         [-multi_exit_disc <<0-4294927695>]
#         [-netmask {255.255.255.255}]
#         [-next_hop_set_mode  {same|manual}]
#              [-next_hop <ip address>]
#              [-next_hop_ip_version {4|6}]
#         [-num_routes <integer>]
#              [-prefix {<ip address>}]
#              [-prefix_step {<integer>}]
#         [-origin  {igp|egp|incomplete} ]
#         [-originator_id  <ipv4 address>]
#         [-originator_id_enable  {0|1}]
#         [-rd_type {0|1}]
#              [-rd_admin_step {<integer> | <ipv4 address>}]
#              [-rd_admin_value {<AS number> | <ipv4 address>}]
#              [-rd_assign_step <ipv4 address>]
#              [-rd_assign_value {<AS number> | <ipv4 address>}]
#         [-route_handle <route_handle>]
#         [-route_ip_addr_step <ip address>]
#         [-target_type {as|ip}]
#              [-target {<AS number> | <ipv4 address>}]
#              [-target_assign <integer>]
#
# Arguments:
#
#    -aggregator
#                   Specifies the last AS number that formed the aggregate
#                   route, followed by the IP address of the BGP speaker that
#                   formed the aggregate route format. In the following example,
#                   173 is the aggregator AS number and 192.1.1.1 is the IP
#                   address of the BGP speaker:
#
#                   173:192.1.1.1.
#
#                   You must specify the -mode argument.
#
#    -as_path
#                   Specifies a list of the Autonomous Systems (AS) numbers that
#                   a route passes through to reach the destination. As the
#                   update passes through an AS, the AS number is inserted at
#                   the beginning of the list. This argument is composed of a
#                   sequence of AS path segments in the following format:
#                   {<as path type>:<comma separated segment list>}. For
#                   example, as_set:1,2,3,4. You must specify one of the
#                   following path types:
#
#                   as_set - Specifies an unordered set of Autonomous Systems
#                   through which a route in the UPDATE message has traversed.
#
#                   as_seq - Specifies an ordered set of Autonomous Systems
#                   through which a route in the UDPATE message has traversed.
#
#                   as_confed_set - Specifies an unordered set of autonomous
#                   systems in the local confederation that the UPDATE message
#                   has traversed.
#
#                   as_confed_seq - Specifies an ordered set of autonomous
#                   systems in the local confederation that the UPDATE message
#                   has traversed.
#
#                   You must specify the add mode argument (-mode add).
#
#    -atomic_aggregate
#                   Enables or disables atomic aggregation. Possible values are
#                   0 and 1. When set to 1, a BGP speaker uses this attribute to
#                   inform other BGP speakers that the local system selected a
#                   less specific route without selecting a more specific route
#                   included in it.
#    -cluster_list
#                   Specifies a sequence of cluster ID values representing the
#                   reflection path through which the route has passed. This is
#                   a string value. The default is "" (empty string).
#
#    -cluster_list_enable
#                   Enables or disables a cluster list in the BGP route range.
#                   Possible values are 0 (disable) and 1 (enable). The default
#                   is 0.
#
#    -communities
#                   Specifies the community to which the routes belong. This
#                   argument provides a way to group destinations, called
#                   communities, to which routing decisions can be applied.
#                   Routing decisions include which routing information a BGP
#                   speaker accepts, prefers, or distributes to other neighbors.
#
#                   All routes with this argument belong to the communities
#                   listed in the argument. Possible values are as follows:
#
#                   as_id:<asn>,<user data> - Creates a value composed of an AS
#                        number and user data. The semantics of the user data
#                        may be defined by the AS.
#
#    -communities_enable
#                   Enables or disables the -community argument. Possible values
#                   are 0 (disable) and 1 (enable). The default is 0.
#
#    -handle
#                   Identifies the router for which to add or remove routes.
#                   This argument is required when -mode is set to "add".
#
#    -ip_version
#                   Specify the IP version of the BGP route to be created. Valid
#                   Possible values are 4 (for IPv4 address format) and 6 (for
#                   IPv6 address format). The default is 4.
#
#    -ipv6_prefix_length
#                   Specifies the IPv6 mask for the IPv6 routes advertised.
#                   Possible values range from 1 to 128. The default is 64.
#
#    -label_incr_mode
#                   Specifies the method in which the MPLS label of an IPv4
#                   MPLS-VPN route is incremented. Currently, Spirent HLTAPI
#                   only supports fixed and prefix mode. The default is
#                   "fixed".
#
#                   fixed - Fixed MPLS label for all route distinguishers (RDs)
#                   prefix - Increment label per prefix advertised
#
#    -local_pref
#                   Defines the preferred exit point from the local autonomous
#                   system (AS) for a specific route. A BGP speaker uses this
#                   argument to inform other BGP speakers in its own AS of the
#                   originating speaker's degree of preference for an advertised
#                   route. Possible values range from 0 to 4294927695. The
#                   default is 10.
#
#    -max_route_ranges
#                   Specifies the number of route ranges to create under the
#                   emulated router, which is specified in the -handle argument.
#
#    -mode          Specifies whether to add or remove routes from the
#                   emulated router's BGP route table. Possible values are add
#                   and remove.
#
#                   add - Adds all routes (defined in the function call) to the
#                        routing table for the specified router. The handles for
#                        these routes are returned in the handles key (see
#                        Return Values).
#
#                   remove - Removes routes from the router specified in the
#                        -route_handle argument.
#
#    -multi_exit_disc
#                   Specifies the multi-exit discriminator (MED), which
#                   indicates the preferred path into an autonomous
#                   system (AS) to external neighbors when multiple paths exist.
#                   The value of this attribute may be used by a BGP speaker to
#                   discriminate among multiple exit points to a neighboring AS.
#                   Possible values range from 0 to 4294927695. The default is
#                   0.
#
#    -netmask
#                   Specifies the netmask of the advertised routes. Enter a
#                   valid IPv4 mask. Use -ipv6_prefix_length for IPv6 addresses.
#                   Possible values for IPv4 addresses range from 0.0.0.0 to
#                   255.255.255.255. The default is 255.255.255.0.
#
#    -next_hop
#                   Defines the IP address of the border router to use as the
#                   next hop to the destinations listed in the Network Layer
#                   Reachability field of the UPDATE message. The default is
#                   192.85.1.3.
#
#    -next_hop_ip_version
#                   The type of IP address that was defined for -next_hop. 
#                   Possible values are 4 and 6. The default is 4.
#
#    -next_hop_set_mode
#                   Indicates how to set the next hop IP address. Possible
#                   values are same and manual:
#
#                   same - Sets the value as the local IP address.
#                   manual - Reads the value given in the -next_hop argument.
#
#    -num_routes
#                   Specifies the number of routes to advertise, using the
#                   prefix as the starting prefix and incrementing based on
#                   either the -step and -netmask arguments or the
#                   -ipv6_prefix_length argument.
#
#    -origin
#                   Indicates how BGP learned about a particular route. Possible
#                   values are:
#
#                   igp - the route is internal to the AS
#
#                   egp - the route is learned via the Exterior Border Gateway
#                        Protocol (EBGP)
#
#                   incomplete - the origin of the route is unknown or learned
#                        by some other means
#
#                   The default is igp.
#
#                   Note: Specifying a path attribute forces the advertised
#                   route to be a node route as opposed to a global route).
#
#    -originator_id
#                   A four-byte BGP attribute created by the route reflector and
#                   carries the router ID of the originator of the route in the
#                   local Autonomous System. The default is 0.0.0.0.
#
#    -originator_id_enable
#                   Enables or disables the originator ID in the BGP route
#                   range. Possible values are 0 and 1. The default is 0.
#
#    -prefix
#                   Specifies the IP address of the first route in the range to
#                   be advertised or removed by the emulated BGP router. Specify
#                   either the IP address or "all." Specify "all" to generate
#                   all route blocks for all prefixes. You must specify the
#                   -mode argument.
#
#    -prefix_step
#                   Defines the step interval for the next incremented prefix
#                   if -num_routes is set to greater than 1. The value must be a
#                   power of two - 1, 2, 4, 8...). The default is 1.
#
#    -rd_admin_step
#                   Defines increment value to step the base route distinguisher
#                   administrator field. If -rd_type is set to 0, the value is
#                   an integer. If -rd_type is set to 1, the value is in dotted
#                   decimal format (for example, 0.0.1.0).
#
#    -rd_admin_value
#                   Specifies the starting value of the administrator field of
#                   the route distinguisher. If -rd_type is set to 0, the value
#                   is an AS number. If -rd_type is set to 1, the value is a
#                   dotted decimal IPv4 address. The default is 100:1.
#
#    -rd_assign_step
#                   Specifies the increment value to step the base route
#                   distinguisher assigned number field. The default is 1.
#
#    -rd_assign_value
#                   Specifies the starting value of the assigned field of the
#                   route distinguisher. If -rd_type is set to 0, the value is
#                   an AS number. If -rd_type is set to 1, the value is a dotted
#                   decimal IPv4 address. The default is 100:1.
#
#    -rd_type
#                   Specifies the route distinguisher type. Possible values are
#                   0 and 1. If -rd_type is set to 0, the administrator field is
#                   an AS number. If it is set to 1, the administrator field is
#                   a global IPv4 address.
#
#    -route_handle
#                   Specifies the handle of the BGP route to be removed. This
#                   argument is required when -mode is set to "remove".
#
#    -route_ip_addr_step
#                   Defines the increment used to generate IP addresses for a
#                   range of routes created under the emulated router, based on
#                   the value specified for the -max_route_ranges argument.
#
#    -target
#                   Specifies the AS number or IP address list  The default is
#                   100:1.
#
#    -target_assign
#                   Specifies the assigned number subfield of the value field of
#                   the target. It is a number from a numbering space which is
#                   maintained by the enterprise administers for a given IP
#                   address or ASN space. It is the local part of the target.
#
#    -target_type
#                   Specifies the route target type. Possible values are 0 and
#                   1. If this argument is set to 0, the target field is an
#                   AS number. If it is set to 1, the target field is a global
#                   IPv4 address.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -ext_communities
#    -import_target
#    -import_target_assign
#    -import_target_type
#    -ipv4_mpls_nlri
#    -ipv4_mpls_vpn_nlri
#    -ipv4_multicast_nlri
#    -ipv4_unicast_nlri
#    -ipv6_mpls_nlri
#    -ipv6_mpls_vpn_nlri
#    -ipv6_multicast_nlri
#    -ipv6_unicast_nlri
#    -l3_site_handle
#    -label_step
#    -label_value
#    -next_hop_enable
#    -num_sites
#    -origin_route_enable
#    -packing_from
#    -default_mdt_ip
#    -default_mdt_ip_incr
#
#
# Return Values:
#    The function returns a keyed list using the following keys:
#    (with corresponding data):
#
#    handles   A list of handles that identify the routes created by the
#              sth::emulation_bgp_route_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description: The sth::emulation_bgp_route_config function creates and
#    configures the routes. Use the -route_handle argument to identify
#    the router for which to remove routes. (The router handle value is
#    contained in the keyed list returned by the sth::emulation_bgp_config
#    function.) Use the -mode argument to specify the action to perform. See the
#    -mode argument for a description of the actions.
#
#    BGP peers exchange routing information about network reachability and AS
#    paths. For a particular route, this information includes a destination
#    address and a list of AS addresses that describes a path to the
#    destination. Based on the exchange of information, the BGP speakers build
#    and maintain routing tables that contain a representation of large portions
#    of the network topology.
#
#    To create BGP routes, you supply address and AS path information. To define
#    the addresses of the routes, use the following arguments:
#
#    -prefix - the starting IP address for the first route in the range
#
#    -netmask IP - the netmask of the advertised routes
#
#    -num_routes - the number of routes in the range
#
#    -prefix_step - the increment used to generate additional addresses
#
#    -max_route_ranges - the maximum number of routes in the range
#
#    -route_ip_addr_step - the IP address increment used to generate IP
#         addresses for each route in the range
#
#    For example, setting the following arguments to the given values will
#    generate five route ranges (shown after the arguments:
#
#    -prefix 1.1.1.0  \
#    -netmask 255.255.255.0 \
#    -num_routes 10 \
#    -prefix_step 1 \
#    -max_route_ranges 5 \
#    -route_ip_addr_step 0.1.0.0
#
#    The above code generates five route ranges as follows:
#
#                   1.1.1.0 - 1.1.10.0
#                   1.2.1.0 - 1.2.10.0
#                   1.3.1.0 - 1.3.10.0
#                   1.4.1.0 - 1.4.10.0
#                   1.5.1.0 - 1.5.10.0
#
# Examples:
#    The following example adds a route block to the routing table for
#    the specified router:
#
# sth::emulation_bgp_route_config -mode add \
#    -handle router1 \
#    -prefix 160.0.0.0 \
#    -num_routes 10 \
#    -prefix_step 1 \
#    -netmask 255.255.255.0 \
#    -ip_version 4 \
#    -as_path as_seq:123 \
#    -next_hop_ip_version 4 \
#    -next_hop 61.25.0.11 \
#    -local_pref 0 \
#    -next_hop_set_mode same
#
# Sample output for example shown above:{handles bgpipv4routeconfig1} {status 1}
#
# The following example adds five route blocks, as specified in the
# -max_route_ranges argument; therefore, five route blocks are advertised:
#
# sth::emulation_bgp_route_config \
#    -mode add -handle router2 \
#    -prefix 161.0.0.0 \
#    -num_routes 10 \
#    -prefix_step 1 \
#    -netmask 255.255.255.0 \
#    -ip_version 4 \
#    -as_path as_seq:123 \
#    -next_hop_ip_version 4 \
#    -next_hop 61.26.0.11 \
#    -local_pref 0 \
#    -next_hop_set_mode same \
#    -max_route_ranges 5 \
#    -route_ip_addr_step 0.1.0.0 \
#
# Sample output for example shown above:
#    {handles bgpipv4routeconfig2 bgpipv4routeconfig3 bgpipv4routeconfig4
#         bgpipv4routeconfig5 bgpipv4routeconfig6} {status 1}
#
# The following example deletes the first BGP router:
#
# sth::emulation_bgp_route_config \
#    -mode remove -route_handle bgpipv4routeconfig1
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bgp_route_config {args} {
	::sth::sthCore::Tracker ::sth::emulation_bgp_route_config $args
	
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}	
	
	set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_route_config \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $userArgsArray(mode)
	
	if {[catch {::sth::Bgp::emulation_bgp_route_config_$mode returnKeyedList} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Stack trace:\n$::errorInfo,$eMsg"
	}
	
	return $returnKeyedList
}



proc ::sth::emulation_bgp_route_generator {args} {
	::sth::sthCore::Tracker ::sth::emulation_bgp_route_generator $args
	
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}	
	
	set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_route_generator \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $userArgsArray(mode)
	
	if {[catch {::sth::Bgp::emulation_bgp_route_generator_$mode returnKeyedList} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Stack trace:\n$::errorInfo,$eMsg"
	}
	
	return $returnKeyedList
}

proc ::sth::emulation_bgp_custom_attribute_config {args} {
	::sth::sthCore::Tracker ::sth::emulation_bgp_custom_attribute_config $args
	
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}	
	
	set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_custom_attribute_config \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $userArgsArray(mode)
	
	if {[catch {::sth::Bgp::emulation_bgp_custom_attribute_config_$mode returnKeyedList} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Stack trace:\n$::errorInfo,$eMsg"
	}
	
	return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_bgp_route_info
#
# Purpose:
#    Returns information on advertised and received BGP routes for the specified
#    emulated node.
#
# Synopsis:
#    sth::emulation_bgp_route_info
#         -handle <BGP_session_handle>
#         -mode   {advertised|received}
#
# Arguments:
#    -handle
#                   The BGP session for which you want information.
#
#    -mode
#                   Specifies the kind of information you want to see. Possible
#                   values are advertised and received.
#
#                   advertised  - returns transmitted count and route statistics
#
#                   received - returns the received count and route statistics
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null
#
#    The following keys are returned when you specify -mode advertised or
#    received:
#
#         ipv4_count     Number of BGP IPv4 routes advertised or received.
#
#         ipv6_count     Number of BGP IPv6 routes advertised or received.
#
#    The following keys are not supported but still returned:
#
#         ipv4_routes           List of BGP IPv4 route prefix and prefix length
#                               advertised or received. Returns "{}".
#
#         ipv6_routes           List of BGP IPv6 route prefix and prefix length
#                               advertised or received. Returns "{}".
#
#         ipv4_mpls_vpn_count   Number of BGP MPLS IPv4 routes advertised or
#                               received. Returns 0.
#
#         ipv4_mpls_vpn_routes  List of BGP IPv4 route prefix, admin, assigned,
#                               and label advertised or received. Returns "{}".
#
#         ipv6_mpls_vpn_count   Number of BGP MPLS IPv6 routes advertised or
#                               received. Returns 0.
#
#         ipv6_mpls_vpn_routes  List of BGP IPv6 route prefix, admin, assigned,
#                               and label advertised or received. Returns "{}".
#
# Description:
#    The sth::emulation_bgp_route_info function provides information about
#    either the advertised or received BGP routes.
#
#    This function returns the requested data (advertised or received
#    information) and a status value (1 for success). If there is an error, the
#    function returns the status value (0) and an error message. Function return
#    values are formatted as a keyed list (supported by the Tcl extension
#    software - TclX). Use the TclX function keylget to retrieve data from the
#    keyed list. (See Return Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input: ::sth::emulation_bgp_route_info -mode advertised -handle router1
#
# Sample Output: {ipv4_count 100} {ipv4_routes {}} {ipv6_count 0} {ipv6_routes
#                {}} {ipv4_mpls_vpn_count 0} {ipv4_mpls_vpn_routes {}}
#                {ipv6_mpls_vpn_count 0} {ipv6_mpls_vpn_routes {}} {status 1}
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bgp_route_info { args } {
	::sth::sthCore::Tracker ::sth::emulation_bgp_route_info $args  
	
	variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_route_info \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::Bgp::emulation_bgp_route_info returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:\n$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}

###################################
#Function:sth::emulation_bgp_route_element_config
###################################
proc ::sth::emulation_bgp_route_element_config {args} {
	::sth::sthCore::Tracker ::sth::emulation_bgp_route_element_config $args
	
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}	
	
	set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Bgp::bgpTable $args \
							::sth::Bgp:: \
							emulation_bgp_route_element_config \
							::sth::Bgp::userArgsArray \
							::sth::Bgp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $userArgsArray(mode)
	
	if {[catch {::sth::Bgp::emulation_bgp_route_element_config_$mode returnKeyedList} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Stack trace:\n$::errorInfo,$eMsg"
	}
	
	return $returnKeyedList
}