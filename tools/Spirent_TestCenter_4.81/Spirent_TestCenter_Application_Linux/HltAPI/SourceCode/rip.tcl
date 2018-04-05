# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.
#Changed by RXu

namespace eval ::sth {

}

#
##Procedure Header
#
# Name:
#    sth::emulation_rip_config
#
# Purpose:
#    Creates, enables, modifies, or deletes an emulated Routing Information
#    Protocol (RIP) router on a Spirent TestCenter chassis.
#
#    RIP is a protocol for managing routing information within a small
#    homogeneous network such as a corporate local area network (LAN) or an
#    interconnected group of such LANs.
#
#    Spirent TestCenter supports the three RIP versions: RIP-1 (RFC 1058), RIP-2
#    (RFC 1723), and RIPng (RFC 2080). All three are distance-vector protocols,
#    have a maximum hop count of 15, and trigger full routing updates to
#    neighbor routers every 30 seconds. Enhancements added by RIP-2 include
#    support of classless routing (prefix routing that includes the subnet mask
#    with the address) and authentication of routing updates (authenticates the
#    originator of the response message). RIPng substitutes IPv6 support for
#    IPv4 support.
#
# Synopsis:
#    sth::emulation_rip_config
#         { [-mode create -port_handle <port_handle> |
#            -mode {modify|delete}
#                  -handle <RIP_handle>} ]
#         { [-authentication_mode text -password <string> |
#            -authentication_mode {null | MD5} ] }
#         [-count <1-1000> ]
#         [-intf_ip_addr {<a.b.c.d> | <a:b:c:d:e:f:g:h>}]
#              [-intf_ip_addr_step {<a.b.c.d> | <a:b:c:d:e:f:g:h>}]
#              [-intf_prefix_length <1-128>]
#         [-gateway_ip_addr <a.b.c.d> ]
#              [-gateway_ip_addr_step <a.b.c.d>]
#         [-mac_address_start <aa:bb:cc:dd:ee:ff>]
#         [-md5_key_id <1-255>]
#         [-neighbor_intf_ip_addr {<a.b.c.d> | <a:b:c:d:e:f:g:h>} ]
#         [-neighbor_intf_ip_addr_step {<a.b.c.d> | <a:b:c:d:e:f:g:h>} ]
#         [-num_routes_per_period <1-70>]
#         [-router_id <a.b.c.d> ]
#         [-router_id_step <integer>]
#         [-send_type {multicast|broadcast}]
#         [-session_type {ripv1|ripv2|ripvng}]
#         [-time_period <0-5000>]
#         [-update_interval <0-10000>]
#         [-update_interval_offset <0-5>]
#         [-vlan_cfi {0|1} ]
#         [-vlan_id <0-4095>]
#         [-vlan_id_mode {fixed|increment}]
#         [-vlan_id_step <1-4094>]
#         [-vlan_user_priority <0-7>]
#
# Arguments:
#
#    -authentication_mode
#                   Specifies the authentication method to use. Spirent
#                   TestCenter supports MD5 Authentication for emulated RIPv2,
#                   and for RIPv1-compatible RIPv2 routers. A RIPv1-compatible
#                   is a RIPv2 router that broadcasts route updates. Possible
#                   values are null, text, and MD5.
#
#                   null - No authentication.
#
#                   text - The RIP-2 packet is authenticated by the receiving
#                        router if the password matches the authentication key
#                        that is included in the packet. This method provides
#                        little security because the authentication key can be
#                        learned by watching the RIP packets.
#
#                   MD5 - The RIP-2 packet contains a cryptographic checksum,
#                        but not the authentication key itself. The receiving
#                        router performs a calculation based on the MD5
#                        algorithm and an authentication key ID. The packet is
#                        authenticated if the calculated checksum matches. This
#                        method provides a stronger assurance that routing data
#                        originated from a router with a valid authentication
#                        key.
#
#    -count
#                   Defines the number of RIP routers to create on the
#                   interface. Possible values are 1 to 1000. The default is 1.
#
#    -gateway_ip_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address of the router.
#
#    -gateway_ip_addr_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address for multiple routers.
#                   This argument is used with the -gateway_ip_addr argument.
#    -handle
#                   Specifies the RIP handle(s) to use when mode is set to
#                   modify, delete, enable, or disable. This argument is not
#                   valid for create mode. Instead, use -port_handle.
#
#    -intf_ip_addr
#                   Specifies the IP address of the interface for the RIP
#                   emulated router that will establish an adjacency with the
#                   DUT. The default for IPv4 (RIPv1 and RIPv2) is 192.85.1.3.
#                   The default for IPv6 (RIPng) is 2000:0:0:0:0:0:0:2. The
#                   -intf_ip_addr argument is mandatory for "-mode create".
#
#    -intf_ip_addr_step
#                   Specifies the difference between interface IP addresses of
#                   consecutive routers when multiple RIP routers are created.
#                   Possible values range from 0 - 4294967295. The default for
#                   IPv4 (RIPv1 and RIPv2) is 0.0.0.1. The default for IPv6
#                   (RIPng) is 0:0:0:0:0:0:0:1.
#
#    -intf_prefix_length
#                   Specifies the prefix length on the emulated router, Possible
#                   values for IPv4 (RIPv1 and RIPv2) addresses range from 1 to
#                   31; the default is 24, Possible values for IPv6 addresses
#                   range from 1 to 128; the default is 64 for IPv6 (RIPng),
#
#    -mac_address_start
#                   Specifies the MAC address for the first session created for
#                   the RIP configuration. 
#
#    -md5_key
#                   For RIPv2 only, specifies the MD5 password to use for
#                   authentication of RIPv2 messages. This is used as a password
#                   string for text authentication, or as a key string for
#                   MD5. If the SUT is configured to authenticate messages, this
#                   password must match the SUT password in order for the SUT to
#                   accept RIP packets. Using -md5_key is the same as using
#                   -password. The default is "Spirent".
#
#    -md5_key_id
#                   Specifies the key ID for MD5 authentication. To use this
#                   argument, you must specify -authentication_mode MD5. MD5
#                   verifies the integrity of the communication, authenticates
#                   the origin, and checks for timeliness. This is an integer ID
#                   for the specified MD5 password. Possible values range from 0
#                   to 255. The default is 1.
#
#    -mode
#                   Specifies the action to be performed. Possible values
#                   are create, modify, and delete. The modes are described
#                   below:
#
#                   create - Creates an emulated router. Use the -port_handle
#                        argument to specify the associated port.
#
#                   modify - Changes the configuration for the RIP router
#                        specified in the -handle argument.
#
#                   delete - Deletes the RIP router specified in the -handle
#                        argument.
#
#    -neighbor_intf_ip_addr
#                   Specifies the neighbors (SUT) interface IP address for
#                   sending unicast packets. The default for IPv4 is 192.85.1.1.
#                   The default for Ipv6 is 2000:0:0:0:0:0:0:1. The
#                   -neighbor_intf_ip_addr argument is mandatory for "-mode
#                   create".
#
#    -neighbor_intf_ip_addr_step
#                   Specifies the difference between the RIP neighbor's
#                   interface IP addresses when multiple RIP hosts are created.
#                   For Spirent TestCenter 2.x, this value is always 0.0.0.0 or
#                   0:0:0:0:0:0:0:0 (that is, the same address).
#
#    -num_routes_per_period
#                   Specifies the number of routes to transmit every time 
#                   period. Possible values range from 1 to 70. The
#                   default is 25. A value of 0 disables this feature and
#                   transmits all routes immediately for all updates.
#
#    -password
#                   For RIPv2 only, specifies the MD5 password to use for
#                   authentication of RIPv2 messages. This is used as a password
#                   string for text authentication, or as a key string for
#                   MD5. If the SUT is configured to authenticate messages, this
#                   password must match the SUT password in order for the SUT to
#                   accept RIP packets. Using -password is the same as using
#                   -md5_key. The default is "Spirent".
#    -port_handle
#                   Specifies the port on which to create the RIP router. This
#                   argument is mandatory for create mode (-mode create).
#
#    -router_id
#                   Identifies the router ID of RIP session router. The router
#                   ID is a 32-bit value, represented in dot notation. Possible
#                   values range from 0.0.0.0 to 255.255.255.255. The default
#                   address is the IP address for -intf_ip_address. The
#                   -router_id argument is mandatory for "-mode create".
#
#    -router_id_step
#                   The step size is the increment used to define router IDs for
#                   multiple sessions. Use the -router_id_step argument along
#                   with the -router_id and -count arguments to create routers
#                   on the interface. You must specify a step value when the
#                   -count value is greater than 1. Possible values range from
#                   0.0.0.1 to 255.255.255.255.The default is 0.0.0.1.
#
#    -send_type
#                   Specifies which version of RIP to use for outgoing RIP
#                   packets. Possible values are multicast and broadcast. The
#                   default for RIPv1 is broadcast. The default for RIPv2 and
#                   RIPng is multicast.
#
#                   - broadcast: You can use broadcast addresses only for RIPv1.
#
#                   - multicast: You can use multicast addresses for both RIPv2
#                                and RIPng.
#
#    -session_type
#                   Specifies the RIP version to be used for each emulated
#                   router. Possible values are ripv1, ripv2, or ripng. The
#                   default is ripv2.
#
#    -time_period
#                   The interval, in milliseconds, between successive RIP
#                   packets. Possible values range from 0 to 5000. The default
#                   is 0. A value of 0 disables this feature and transmits all
#                   routes immediately for all updates.
#
#    -update_interval
#                   The time, in seconds, between transmitted update messages.
#                   Possible values range from 1 to 10000. The default is 30.
#
#    -update_interval_offset
#                   The maximum update-interval variance, in seconds, between
#                   transmitted update messages.That is, the maximum of a random
#                   time interval used to add or subtract from the time at
#                   which updates are sent. Possible values range from 0 to 5.
#                   The default is 0.
#    -vlan_cfi
#                   Sets the canonical format indicator field in VLAN for the
#                   emulated router node. Possible values are 0 (Ethernet) and 1
#                   (Token Ring). The default is 0. If set to 0, it indicates
#                   the network is Ethernet. If set to 1, it indicates that
#                   Token Ring and packets are dropped by Ethernet ports.
#
#    -vlan_id
#                   The VLAN ID of the first VLAN sub-interface. Possible values
#                   range from 0 to 4095. The default is 100.
#
#    -vlan_id_mode
#                   For multiple neighbor configurations, configures the VLAN ID
#                   mode to "fixed" or "increment." If you set this argument to
#                   "increment," then you must also specify the -vlan_id_step
#                   argument to indicate the step size. The default is "fixed".
#
#    -vlan_id_step
#                   The step size by which the VLAN value is incremented when
#                   you set -vlan_id_mode to "increment." Possible values range
#                   from 0 to 4095. The default is 1. You must specify the step
#                   when the -count argument is greater than 1.
#
#    -vlan_user_priority
#                   VLAN priority for the VLANs on this port. Possible values
#                   range from 0 to 7. The default is 7.
#
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent TestCenter 2.00.
#
#    -expiration_interval
#    -garbage_interval
#    -interface_metric
#    -receive_type
#    -triggered_interval
#    -update_mode
#    -vci
#    -vci_step
#    -vpi
#    -vpi_step
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#    handle
#                   The handle(s) of the RIP router returned by the
#                   sth::emulation_rip_config function when you use -mode
#                   create to create a new RIP router. When you want to modify
#                   or delete the RIP router, you specify the handle as the
#                   value to the -handle argument.
#
#    status
#                   Success (1) or failure (0) of the operation.
#
#    log
#                   An error message (if the operation failed).
#
# Description:
#    The sth::emulation_rip_config function creates, enables,
#    modifies, deletes, or disables an emulated RIP router. Use the -mode
#    argument to specify the action to perform. (See the -mode argument
#    description for information about the actions.)
#
#    Using RIP, a gateway host (with a router) sends its entire routing table
#    (which lists all the other hosts it knows about) to its closest neighbor
#    host every 30 seconds. The neighbor host in turn will pass the information
#    on to its next neighbor and so on until all hosts within the network have
#    the same knowledge of routing paths, a state known as network convergence.
#
#    RIP uses a hop count as a way to determine network distance. (Other
#    protocols use more sophisticated algorithms that include timing as well.)
#    Each host with a router in the network uses the routing table information
#    to determine the next host to route a packet to for a specified
#    destination.
#
#    When you create an RIP emulated router, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated router will use for
#    RIP communication. (The port handle value is contained in the keyed list
#    returned by the connect function.)
#
#    In addition to specifying the port handle (-port_handle), you must also
#    provide the following arguments when you create a RIP router:
#
#    -intf_ip_addr
#
#    -gateway_ip_addr
#
#    -mode create
#
#    -router_id
#
#    When you create a RIP router, Spirent HLTAPI creates the router in
#    memory and downloads the configuration to the card. To start the router,
#    use the sth::emulation_rip_control function with -mode start.
#
#    Once you start sessions, Spirent HLTAPI handles all of the message
#    traffic for the emulated routers. During the test, use the
#    sth::emulation_rip_control function to stop and re-start individual
#    routers. After you have created the routers for your test, use the
#    sth::emulation_rip_route_config function to set up the routes.
#
# Examples:
#    The following example creates a RIP router on the specified port:
#
#    sth::emulation_rip_config \
#                  -port_handle $port1 \
#                  -mode create \
#                  -count 1 \
#                  -authentication_mode "text" \
#                  -password "pass" \
#                  -send_type unicast \
#                  -mac_address_start 00:10:94:00:00:05 \
#                  -intf_ip_addr 23.24.0.2 \
#                  -neighbor_intf_ip_addr 23.24.0.1 \
#                  -neighbor_intf_ip_addr_step 0.1.0.0 \
#                  -gateway_ip_addr 23.24.0.1 \
#                  -gateway_ip_addr_step 0.0.0.1 \
#                  -intf_prefix_length 16 \
#                  -router_id 23.24.0.2 \
#                  -update_interval 30 \
#                  -update_interval_offset 30\
#                  -num_routes_per_period 30 \
#                  -time_period 30
#
#    The above example produced the following output:
#
#    {handle router1} {handles router1} {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#    None.
#
# End of Procedure Header
#
#
proc ::sth::emulation_rip_config {args} {
    variable sortedSwitchPriorityList
    array unset ::sth::rip::userArgsArray
    array set ::sth::rip::userArgsArray {}

    set returnKeyedList ""

    set retVal [catch {
        ::sth::sthCore::Tracker emulation_rip_config $args
        ::sth::sthCore::commandInit \
        ::sth::rip::ripTable \
            $args \
            ::sth::rip:: \
            emulation_rip_config \
            ::sth::rip::userArgsArray \
            ::sth::rip::sortedSwitchPriorityList

        switch -exact $::sth::rip::userArgsArray(mode) {
            "create" -
            "enable" {
                ::sth::rip::emulation_rip_config_create returnKeyedList
            }
            "modify" {
                ::sth::rip::emulation_rip_config_modify returnKeyedList
            }
            "delete" -
            "disable " {
                ::sth::rip::emulation_rip_config_delete returnKeyedList
            }
            "active" {
                ::sth::rip::emulation_rip_config_active returnKeyedList
            }
            "inactive" {
                ::sth::rip::emulation_rip_config_inactive returnKeyedList
            }
            default {
               # Unsupported mode
               return -code error "Error:  Unsupported -mode value $mode.  "
            }
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    # apply config
    if {!$::sth::sthCore::optimization} {
        if {[catch {set ret [::sth::sthCore::doStcApply]} err] } {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err" {}
                return -code error $returnKeyedList
        }
    }
    return $returnKeyedList
}

#
##Procedure Header
#
# Name:
#    sth::emulation_rip_control
#
# Purpose:
#    Starts or stops a RIP router. You can also use this function to
#    delete a route and to control route flapping.
#
# Synopsis:
#     sth::emulation_rip_control
#         {-mode {start|stop|restart}
#              {-handle <rip_session_handle>|-port_handle <port_handle>}
#         |
#          -mode flap
#              {-handle <rip_session_handle>|-port_handle <port_handle>}
#              [-advertise <list of route handles>]
#              [-withdraw <list of route handles> ]
#              [-flap_count <1-4294967295>]
#              [-flap_down_time <0-4294967295>]
#              [-flap_interval_time <0-4294967295>]
#              [-flap_routes <list of route handles>]
#         }
#
# Arguments:
#
#    -advertise
#                   Re-advertises routes in a route pool. This list should only
#                   be passed in the return from the 
#                   sth::emulation_rip_route_config function. Use this optional
#                   argument only in start mode. For example:
#
#                   sth::emulation_rip_control -mode start \
#                        -handle router1 -advertise ripv4routeparams1
#
#    -flap_count
#                   Specifies the number of flaps for each handle specified
#                   (-handle or -port_handle). Each flap includes one advertise
#                   and one withdraw. Possible values range from 1 to
#                   4294967295. This argument is mandatory for flap mode
#                   (-mode flap).
#
#    -flap_down_time
#                   During a flapping operation, specifies the period (in
#                   seconds) during which the routes are withdrawn from their
#                   neighbors. Possible values range from 0 to 4294967295. The
#                   default is 0. This argument is mandatory for flap mode
#                   (-mode flap).
#
#    -flap_interval_time
#                   During a flapping operation, the time (in seconds) between
#                   flap cycles. Possible values range from 0 to 4294967295. The
#                   default is 0. This argument is mandatory for flap mode
#                   (-mode flap).
#
#    -flap_routes
#                   Perform periodic route flapping on the specified routes. You
#                   must specify one or more route handles.
#
#    -handle
#                   Identifies the session router on which to take the RIP
#                   action. The handle (or list of handles) is returned from the
#                   sth::emulation_rip_config function when creating a RIP
#                   router. You must specify either -handle or -port_handle but
#                   not both.
#
#    -mode
#                   Specifies the action to be taken. Possible values are start,
#                   stop, or restart either the RIP router or route flapping,
#                   This argument is mandatory.
#
#                   start - Starts either the RIP router with the specified
#                        handle (-handle) or route flapping, or starts all of
#                        the RIP routers associated with the port specified with
#                        -port_handle.
#
#                        Note: Start mode automatically sends out the advertise
#                        for any routes associated with the RIP router. Also,
#                        when any subsequent sth::emulation_rip_router_config
#                        function is called to create a new route after the
#                        router has been started, the newly-created route is
#                        automatically advertised as well.
#
#                   stop - Stops either the RIP router with the specified handle
#                        (-handle) or route flapping, or stops all of the RIP
#                        routers associated with the port specified with
#                        -port_handle.
#
#                   restart - Stops either the RIP router with the specified
#                        handle (-handle) or route flapping and then starts it
#                        again, or stops all RIP routers associated with the
#                        port specified with -port_handle. This is not a
#                        graceful restart.
#
#                   flap - Enables flapping for each route handle specified in
#                        the -flap_routes argument.
#
#    -port_handle
#                   Specifies the handle for the port to be controlled. That is,
#                   the port on which all RIP routers or route flapping should
#                   be started, stopped, or restarted. You must specify either
#                   -handle or -port_handle but not both.
#
#    -withdraw
#                   Specifies the list of route handles to remove (withdraw)
#                   from the route pool. This list should only be passed in the
#                   return from the sth::emulation_rip_route_config function. 
#                   Use this optional argument only in start mode. For example:
#
#                   sth::emulation_rip_control -mode start \
#                        -handle router1 -withdraw ripv4routeparams1
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status    Success (1) or failure (0) of the operation.
#         log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_rip_control function controls the starting and
#    stopping of RIP routers as well as deleting routes from the route pool.
#
# Examples:
#    To start a RIP router:
#
#         sth::emulation_rip_control -mode start \
#                                    -handle router1
#
#    To stop a RIP router:
#
#         sth::emulation_rip_control -mode stop \
#                                    -handle router1
#
#    To restart a RIP router:
#
#         sth::emulation_rip_control -mode restart \
#                                    -handle router1
#
# Sample Input:
#    sth::emulation_rip_control  \
#         -mode start \
#         -handle router1
#
# Sample Output:
#         {status 1}
#
# Notes:
#          None.
#
# End of Procedure Header
#
proc ::sth::emulation_rip_control {args} {
    array unset ::sth::rip::userArgsArray
    array set ::sth::rip::userArgsArray {}
    set returnKeyedList ""
    set retVal [catch {
        ::sth::sthCore::Tracker emulation_rip_control $args
        ::sth::sthCore::commandInit \
            ::sth::rip::ripTable \
            $args \
            ::sth::rip:: \
            emulation_rip_control \
            ::sth::rip::userArgsArray \
            sortedSwitchPriorityList
        if {[info exists ::sth::rip::userArgsArray(port_handle)] == 0} {
            if {[info exists ::sth::rip::userArgsArray(handle)] == 0} {
                return -code error "Error: Missing mandatory attribute, either -port_handle or -handle."
            }
        }

        #handle the case of -advertise and -withdraw are passed in
        set advertise 0
        set withdraw 0
        set adv_withdraw_list ""

        if {[lsearch -exact $::sth::rip::userArgsArray(optional_args) "-advertise"] > -1} {
            foreach routeobj $::sth::rip::userArgsArray(advertise) {
                set riprtrcfg 0
                #check if route params is of riprouterconfig type
                set riprtrcfg [::sth::sthCore::invoke stc::get $routeobj -parent]
                if {![string match -nocase "*routerconfig*" $riprtrcfg]} {
                    return -code error [concat "Error:  Invalid advertise route handle(s) used."]
                }
                #check if adv route params is from the same riprouter passed in via -handle
                set riprtr [::sth::sthCore::invoke stc::get $riprtrcfg -parent]
                if {$::sth::rip::userArgsArray(handle) != $riprtr} {
                    return -code error [concat "Error:  -advertise attribute is not of $::sth::rip::userArgsArray(handle)."]
                }
                lappend adv_withdraw_list $riprtrcfg
            }
            set advertise 1
        }
        if {[lsearch -exact $::sth::rip::userArgsArray(optional_args) "-withdraw"] > -1} {
            foreach routeobj $::sth::rip::userArgsArray(withdraw) {
                set riprtrcfg 0
                #check if withdraw route params is of riprouterconfig type
                set riprtrcfg [::sth::sthCore::invoke stc::get $routeobj -parent]
                if {![string match -nocase "*routerconfig*" $riprtrcfg]} {
                    return -code error [concat "Error:  Invalid withdraw route handle(s) used."]
                }
                #check if withdraw route params is from the same riprouter passed in via -handle
                set riprtr [::sth::sthCore::invoke stc::get $riprtrcfg -parent]
                if {$::sth::rip::userArgsArray(handle) != $riprtr} {
                    return -code error [concat "Error:  -withdraw attribute is not of $::sth::rip::userArgsArray(handle)."]
                }
                lappend adv_withdraw_list $routeobj
            }
            set withdraw 1
        }
		
        set protocolList ""
        if {[info exists ::sth::rip::userArgsArray(handle)] && ([info exists ::sth::rip::userArgsArray(port_handle)]==0)} {
            set protocolList $::sth::rip::userArgsArray(handle)
        } elseif {[info exists ::sth::rip::userArgsArray(port_handle)]} {
			set handleList "$::sth::rip::userArgsArray(port_handle)"
			set handles ""
			foreach handles $handleList {
				append protocolList "[::sth::sthCore::invoke stc::get $handles -affiliationport-Sources] "
			}
        }
        if {!([llength $protocolList] > 0)} {
            return -code error [concat "Error:  Unable to execute mode " \
              "\"$::sth::rip::userArgsArray(mode)\".  No specified " \
              "RIP router session can be found.  "]
        }
        switch $::sth::rip::userArgsArray(mode) {
            "start" {
                if {$withdraw == 1 && $advertise == 1} {
                    return -code error [concat "Error:  Both -advertise and -withdraw attributes are provided; \
                            -advertise and -withdraw must not used be at the same time."]
                }
                if {$withdraw} {
                    ::sth::sthCore::invoke stc::perform "RipWithdrawRoute" "-routeList" $adv_withdraw_list
                }
                if {$advertise} {
                    ::sth::sthCore::invoke stc::perform "RipReadvertiseRoute" "-routerList" $adv_withdraw_list
                }
                if {$withdraw == 0 && $advertise == 0} {
                    ::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $protocolList
                }
            }
            "stop" { 
                if {$advertise} {
                    return -code error [concat "Error:  -advertise attribute cannot be use with stop mode."]
                }
                if {$withdraw} {
                    return -code error [concat "Error:  -withdraw attribute cannot be use with stop mode."]
                }
                ::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $protocolList
            }
            "restart" {
                ::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $protocolList
                ::sth::sthCore::invoke stc::perform "resultsClearRouting" "-protocolList" "RIP"
                ::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $protocolList
            }
            "flap" {
                ::sth::rip::emulation_rip_flap returnKeyedList $protocolList
            }
            default {
                return -code error [concat "Error:  Unsupported RIP control mode $::sth::rip::userArgsArray(mode)."]
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

#
##Procedure Header
#
# Name:
#    sth::emulation_rip_route_config
#
# Purpose:
#    Creates routes for or deletes routes from a RIP router. It
#    also defines the characteristics of the routes that will be advertised at
#    the beginning of the session.
#
#    When you add a route (see description for -mode), Spirent HLTAPI
#    returns the route handle in a keyed list with "handles" as the key.
#
# Synopsis:
#    sth::emulation_rip_route_config
#         { [-mode create
#              -handle <rip_session_handle> |
#            -mode {modify|delete}
#              -route_handle <rip_route_pool_handle>]
#         }
#         [-metric <1-16>]
#         [-next_hop <a.b.c.d | a:b:c:d:e:f:g:h>]
#         [-num_prefixes <1 - 1000000>]
#              [-prefix_start <a.b.c.d | a:b:c:d:e:f:g:h>]
#              [-prefix_step <1-128>]
#              [-prefix_length <1-128>]
#         [-route_tag <0 - 65535>]
#
# Arguments:
#
#    -handle
#                   Identifies the session router on which to create router
#                   pools or route ranges. This argument is mandatory when -mode
#                   is set to "create".
#
#    -metric
#                   Indicates the cost to the destination network and is
#                   the hop count needed to reach the destination network.
#                   Possible values range from 1 to 16. The default is 1.
#
#    -mode          Specifies the action to take. Possible values are
#                   create, modify, and delete.
#
#                   create - Creates a new route pool or range on the port
#                        specified in the -handle argument, and then starts all
#                        of the routers under that port. You must specify the
#                        -handle argument.
#
#                   modify - Modifies the route specified in the -route_handle
#                        argument.
#
#                   delete - Removes the route from the RIP pool specified in
#                        the -route_handle argument.
#
#    -next_hop
#                   Defines the IP address of the adjacent router to which the
#                   packet should be sent next. A value of 0.0.0.0 or
#                   0:0:0:0:0:0:0:0 indicates that the next hop is the
#                   advertising router. This value applies only to RIP v2 and
#                   RIPng. The default is 0.0.0.0 for RIPv2 and
#                   0:0:0:0:0:0:0:0 for RIPng.
#
#    -num_prefixes
#                   Specifies the number of routes to advertise in update
#                   messages. Possible values range from 1 to 1000000. The
#                   default is 1.
#
#    -prefix_length
#                   Set the width of the network mask. Possible values
#                   range from 1 to 128. The default is 24 for RIPv1 and RIPv2
#                   and 64 for RIPng.
#
#    -prefix_start
#                   Specifies the IP address of the first route in the range to
#                   be advertised or removed by the emulated RIP router.
#
#    -prefix_step
#                   Defines the step interval for the next incremented route
#                   if -num_prefixes is set to greater than 1. Possible values
#                   range from 1 to 128. The default depends on the width of the
#                   network mask (see -prefix_length): 24 for RIPv1 and RIPv2
#                   and 64 for RIPng.
#
#    -route_handle
#                   Specifies the handle of the RIP route to be modified or
#                   removed. This argument is mandatory when -mode is set to
#                   either "modify" or "delete".
#
#    -route_tag
#                   An arbitrary value associated with the routes in this range.
#                   Used by RIPv2 & RIPng to distinguish internal routes
#                   (learned from other protocols, such as BGP or OSPF)
#                   from external routes. This value causes the emulated RIP
#                   router to act as a router that runs RIP together with other
#                   protocols (such as BGP, OSPF).Possible values range from 0
#                   to 65535. The default is 0.
#
# Return Values:
#    The function returns a keyed list using the following keys:
#    (with corresponding data):
#
#    router_handle   
#              A handle that identifies the routes created by the
#              sth::emulation_rip_route_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_rip_route_config function creates and
#    configures the routes. Use the -route_handle argument to identify
#    the router for which to remove routes. (The router handle value is
#    contained in the keyed list returned by the sth::emulation_rip_config
#    function.) Use the -mode argument to specify the action to perform. See the
#    -mode argument for a description of the actions.
#
#    RIP uses a single routing metric (hop count) to measure the distance
#    between the source and a destination network. Each hop in a path from
#    source to destination is assigned a hop-count value, which is typically 1.
#    When a router receives a routing update that contains a new or changed
#    destination-network entry, the router adds one to the metric value
#    indicated in the update and enters the network in the routing table. The IP
#    address of the sender is used as the next hop.
#
#    To create RIP routes, you supply the total number of routes, starting IP
#    address, prefix length, and increment value:
#
#    -num_prefixes - the number of routes in the range
#    -prefix_start - the starting IP address for the first route in the range
#    -prefix_step - the increment used to generate IP addresses for each route
#         in the range
#    -prefix_length - the width of the network mask
#    -next_hop - the IP address increment used to generate IP
#         addresses for each route in the range
#    -metric - the hop count needed to reach the destination network
#
# Examples:
#    The following example adds a route block to the routing table for
#    the specified router:
#
#    sth::emulation_rip_route_config  \
#         -mode create  -handle router1 \
#         -num_prefixes 2 \
#         -prefix_start 12.12.13.12 \
#         -prefix_step 1 \
#         -prefix_length 32
#
#    The above example produced the following output:
#
#    {route_handle ripv4routeparams1} {status 1}
#
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#    None.
#
# End of Procedure Header
#
proc ::sth::emulation_rip_route_config {args} {
    variable sortedSwitchPriorityList
    array unset ::sth::rip::userArgsArray
    array set ::sth::rip::userArgsArray {}

    set returnKeyedList ""
    set retVal [catch {
        ::sth::sthCore::Tracker emulation_rip_route_config $args
        ::sth::sthCore::commandInit \
            ::sth::rip::ripTable \
            $args \
            ::sth::rip:: \
            emulation_rip_route_config \
            ::sth::rip::userArgsArray \
            sortedSwitchPriorityList

        switch -exact $::sth::rip::userArgsArray(mode) {
            create {
               ::sth::rip::emulation_rip_route_config_create returnKeyedList
            }
            modify {
               ::sth::rip::emulation_rip_route_config_modify returnKeyedList
            }
            delete {
               ::sth::rip::emulation_rip_route_config_delete returnKeyedList
            }
            default {
               # Unsupported mode
               return -code error "Error:  Unsupported -mode value $mode"
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

#
##Procedure Header
#
# Name:
#    sth::emulation_rip_info
#
# Purpose:
#    Spirent Extension (for Spirent HLTAPI only).
#    Returns statistics about the RIP configuration settings, routing 
#    setup, and emulation for the specified RIP router.
#
# Synopsis:
#    sth::emulation_rip_info
#         -handle <rip_handle>
#
# Arguments:
#
#    -handle
#                   Specifies the router for which you want information.
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#    status         Retrieves a value indicating the success (1) or failure
#                   (0) of the operation.
#
#    log            Retrieves a message describing the last error that
#                   occurred during the operation. If the operation was
#                   successful - {status 1} - the log value is null.
#
#    router_state             
#                             The state of the emulated RIP router on the 
#                             current port: 
#
#                             NONE      No state.
#                             CLOSED    The emulated router has been created but 
#                                       not yet started.
#                             OPEN      The emulated router has been created and 
#                                       started.
#
#    update_interval_offset   
#                             Maximum update-interval variance, in seconds, 
#                             between transmitted update messages.
#
#    session_type
#                             The RIP version used for the router:
#                             ripv1, ripv2, or ripng.
#
#    neighbor_intf_ip_addr
#                             The difference between the RIP neighbor's
#                             interface IP addresses when multiple RIP hosts are 
#                             created.
#
#    intf_ip_address          
#                             IP address of the port on the interface card:
#                             a.b.c.d.
#
#    gateway_ip_addr
#                             IPv4 gateway address of the router.
#
#    router_id 
#                             The router ID of the RIP session router. 
#
#    intf_prefix_length 
#                             The prefix length on the emulated router.
#
#    mac_address_start        
#                             Starting MAC address
#
#    time_period
#                             The interval, in milliseconds, between successive 
#                             RIP packets.
#
#    send_type
#                             Version of RIP to use for outgoing RIP packets.
#
#    num_routes_per_period
#                             Number of routes to transmit every time period.
#
#    update_interval
#                             Number of seconds between transmitted update 
#                             messages.
#
#    password
#                             (For RIPv2 only) The MD5 password used to
#                             authenticate RIPv2 messages
#
#    md5_key
#                             Key ID for MD5 authentication.
#
#    authentication_mode
#                             Authentication method used: none, text, or MD5.
#
#    route_tag
#                             Value used by RIPv2 & RIPng to distinguish 
#                             internal routes from external routes.
#                             
#    metric
#                             Value indicating the cost to the destination 
#                             network. Also, the hop count needed to reach the 
#                             destination network.
#
#    next_hop
#                             IP address of the adjacent router to which the
#                             packet should be sent next.
#
#    num_prefixes
#                             Number of routes to advertise in update messages.
#    
#    prefix_start
#                             Starting IP address for the first route in the 
#                             range.
#
#    prefix_step
#                             Increment used to generate IP addresses for each 
#                             route in the range.
#
#    prefix_length
#                             Width of the network mask
#
#    tx_advertised_update_count
#                             Number of advertised routes sent by the emulated 
#                             router.
#
#    rx_withdrawn_update_count
#                             Number of unreachable (metric 16) routes received 
#                             by the emulated router.
#
#    rx_advertised_update_count
#                             Number of advertised routes received by the 
#                             emulated router.
#
# Description:
#    This function returns the requested data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message. Function return values are formatted as a keyed list
#    (supported by the Tcl extension software - TclX). Use the TclX function
#    keylget to retrieve data from the keyed list. (See Return Values for a
#    description of each key.)
#
# Examples:
#    See Sample Input and Sample Output below.
#
# Sample Input:
#
#    sth::emulation_rip_info -handle router1
#
# Sample Output:
#
#    {router_state open} {update_interval_offset 12} {session_type ripv2}
#    {neighbor_intf_ip_addr 23.24.0.1} {time_period 10} {send_type unicast}
#    {num_routes_per_period 11} {update_interval 13} {password pass} {md5_key 
#    20} {authentication_mode MD5} {route_tag 0} {metric 1} {next_hop null} 
#    {num_prefixes 2} {prefix_start 12.12.13.12} {prefix_step 1} {prefix_length 
#    32} {tx_advertised_update_count 10.000000} {rx_withdrawn_update_count 
#    0.000000} {rx_advertised_update_count 0.000000} {status 1}
#
# Notes:
#    None
#
# End of Procedure Header
#
proc ::sth::emulation_rip_info {args} {
    ::sth::sthCore::Tracker :: "::sth::emulation_rip_info" $args
    variable sortedSwitchPriorityList
    array unset ::sth::rip::userArgsArray
    array set ::sth::rip::userArgsArray $args
    set returnKeyedList ""

	set retVal [catch {
		if {[info exists ::sth::rip::userArgsArray(-handle)] == 0} {
			return -code error "Error: Missing mandatory attribute -handle."
		}

		set ripRouterConfig [::sth::sthCore::invoke stc::get $::sth::rip::userArgsArray(-handle) -children-riprouterconfig]
		set router_state [::sth::sthCore::invoke stc::get $ripRouterConfig -RouterState]
		keylset returnKeyedList router_state $router_state
        # report state of setup
        array set rip_state [::sth::sthCore::invoke stc::get $ripRouterConfig]
        foreach {attr val} [array get rip_state] {
            switch -- $attr {
                -DutIpv4Addr -
                -DutIpv6Addr { 
                    keylset returnKeyedList session_type [string tolower rip$rip_state(-RipVersion)]
                    if {$rip_state(-RipVersion) == "V1" || $rip_state(-RipVersion) == "V2"} {
                        set ipversion "4"
                        set ripversion "v4"
                        keylset returnKeyedList neighbor_intf_ip_addr $rip_state(-DutIpv4Addr)
                        set IpConfig [::sth::sthCore::invoke stc::get $::sth::rip::userArgsArray(-handle) -children-ipv4if]
                    } else {
                        set ipversion "6"
                        set ripversion "ng"
                        keylset returnKeyedList neighbor_intf_ip_addr $rip_state(-DutIpv6Addr)
                        set IpConfig [::sth::sthCore::invoke stc::get $::sth::rip::userArgsArray(-handle) -children-ipv6if]
                        if {[llength $IpConfig] > 1} {
                            set IpConfig [lindex $IpConfig 0]
                        }
                    }
                    array set ripRouterIpConfig [::sth::sthCore::invoke stc::get $IpConfig]
                    set EtherConfig [::sth::sthCore::invoke stc::get $::sth::rip::userArgsArray(-handle) -children-ethiiif]
                    array set ripRouterEtherConfig [::sth::sthCore::invoke stc::get $EtherConfig]
                    keylset returnKeyedList intf_ip_addr $ripRouterIpConfig(-Address)
                    keylset returnKeyedList gateway_ip_addr $ripRouterIpConfig(-Gateway)
                    keylset returnKeyedList router_id [::sth::sthCore::invoke stc::get $::sth::rip::userArgsArray(-handle) -RouterId]
                    keylset returnKeyedList intf_prefix_length $ripRouterIpConfig(-PrefixLength)

                    keylset returnKeyedList mac_address_start $ripRouterEtherConfig(-SourceMac)
                }
                -UpdateType { keylset returnKeyedList send_type [string tolower $val] }
                -UpdateInterval { keylset returnKeyedList update_interval $val }
                -UpdateJitter { keylset returnKeyedList update_interval_offset $val }
                -MaxRoutePerUpdate { keylset returnKeyedList num_routes_per_period $val }
                -InterUpdateDelay { keylset returnKeyedList time_period $val }
                -RouterState { keylset returnKeyedList router_state [string tolower $val] }
                -EnableBfd {keylset returnKeyedList bfd_registration [string tolower $val]}
            }
        }
        #report state of authentication settups
        set ripauthenticationparams [::sth::sthCore::invoke stc::get $ripRouterConfig -children-ripauthenticationparams]
        array set ripauthen_state [::sth::sthCore::invoke stc::get $ripauthenticationparams]
        foreach {attr val} [array get ripauthen_state] {
            switch -- $attr {
                -Authentication {
                    if {$val == "NONE"} {
                        keylset returnKeyedList authentication_mode "null"
                    } else {
                        keylset returnKeyedList authentication_mode $val
                    }
                }
                -Password { keylset returnKeyedList password $val }
                -Md5KeyId { keylset returnKeyedList md5_key $val }
            }
        }

        #report state of route settups
        set ripRouteParamsList [::sth::sthCore::invoke stc::get $ripRouterConfig -children-rip[string trim $ripversion]routeparams]
        foreach ripRouteParams $ripRouteParamsList {
            if {[info exists rip_routeparams]} {
                set attrlist [array names rip_routeparams]
                foreach attr $attrlist {
                    set value "$rip_routeparams($attr) [::sth::sthCore::invoke stc::get $ripRouteParams $attr]"
                    array set rip_routeparams "$attr \"$value\""
                }
            } else {
                array set rip_routeparams [::sth::sthCore::invoke stc::get $ripRouteParams]
            }
            
            set ripNetworkBlock [::sth::sthCore::invoke stc::get $ripRouteParams -children-ipv[string trim $ipversion]networkblock]
            if {[info exists rip_neworkarams]} {
                set attrlist [array names rip_neworkarams]
                foreach attr $attrlist {
                    set value "$rip_neworkarams($attr) [::sth::sthCore::invoke stc::get $ripNetworkBlock $attr]"
                    array set rip_neworkarams "$attr \"$value\""
                }
            }  else {
                array set rip_neworkarams [::sth::sthCore::invoke stc::get $ripNetworkBlock]
            }
        }
        foreach {attr val} [array get rip_routeparams] {
            switch -- $attr {
                -NextHop { keylset returnKeyedList next_hop $val }
                -Metric { keylset returnKeyedList metric $val }
                -RouteTag { keylset returnKeyedList route_tag $val }
            }
        }

        foreach {attr val} [array get rip_neworkarams] {
            switch -- $attr {
                -StartIpList { keylset returnKeyedList prefix_start $val }
                -PrefixLength { keylset returnKeyedList prefix_length $val }
                -NetworkCount { keylset returnKeyedList num_prefixes $val }
                -AddrIncrement { keylset returnKeyedList prefix_step $val }
            }
        }
        
        #report results
        set ripRouterResults [::sth::sthCore::invoke stc::get $ripRouterConfig -children-riprouterresults]
        array set rip_stats [::sth::sthCore::invoke stc::get $ripRouterResults]
        foreach {attr val} [array get rip_stats] {
            switch -- $attr {
                -RxAdvertisedUpdateCount { keylset returnKeyedList rx_advertised_update_count $val }
                -TxAdvertisedUpdateCount { keylset returnKeyedList tx_advertised_update_count $val }
                -RxWithdrawnUpdateCount { keylset returnKeyedList rx_withdrawn_update_count $val }
                -TxWithdrawnUpdateCount { keylset returnKeyedList rx_withdrawn_update_count $val }
            }
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }

    return $returnKeyedList
}
