# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth {
    variable isis_subscription_state 0
}
namespace eval ::sth::IsIs {
}

##Procedure Header
#
# Name: ::sth::emulation_isis_config
#
# Purpose:
#        Creates, enables, disables, modifies, or deletes an emulated IS-IS router
#        on a Spirent TestCenter chassis. You can create one or more IS-IS  routers.
#        Each IS-IS-enabled Spirent TestCenter port can emulate different types of
#        routers: Level 1 (intra-area), Level 2 (interarea), or Level 1-2 (both).
#
#        The Integrated Intermediate System to Intermediate System (IS-IS) protocol
#        is a link state, Interior Gateway Protocol (IGP) for IP and Connectionless
#        Network Protocol (CLNP). Routers (Intermediate Systems) use IS-IS to
#        exchange routes within a single network (routing domain). Based on the Open
#        System Interconnection (OSI) architecture, IS-IS functionality is similar
#        to that of IP-based OSPF. The topology information is flooded throughout
#        the AS, so that every router within the AS has a complete picture of the
#        topology of the AS. Packets or datagrams are forwarded based on the best
#        topological path through the network to the destination.
#
# Synopsis:
#        sth::emulation_isis_config
#                { [-mode create -port_handle <port_handle> |
#                   -mode {modify|delete|disable|enable}
#                                -handle <ISIS_handle>]}
#                [-area_id <string>]
#                [-count <integer>]
#                [-csnp_interval   <1-65535> ]
#                [-discard_lsp {0|1} ]
#                [-handle   { isis_session_handle } ]
#                [-hello_interval   <1-65535> ]
#                [-holding_time         <1-65535> ]
#                [-intf_ip_addr         <a.b.c.d> ]
#                [-intf_ip_addr_step  <integer> ]
#                [-intf_prefix_length <1-32> ]
#                [-intf_ipv6_addr   <0:0:0:0:0:0:0:0> ]
#                [-intf_ipv6_addr_step  <integer> ]
#                [-intf_ipv6_prefix_length <1-128> ]
#                [-intf_metric   <0-16777215> ]
#                [-ip_version   {4|6|4_6}  ]
#                [-l1_router_priority  <0-255>  ]
#                [-l2_router_priority  <0-255>  ]
#                [-lsp_level {L1|L2} ]
#                [-lsp_refresh_interval <1-65535>  ]
#                [-psnp_interval   <1-65535> ]
#                [-router_id_step  <integer> ]
#                [-routing_level   {L1|L2|L1L2}]
#                [-system_id   {000000000000 - FFFFFFFFFFFF}
#                [-te_admin_group  <1-4294967295> ]
#                [-te_enable   {0|1} ]
#                [-te_max_bw  <0 - 2147483647> ]
#                [-te_max_resv_bw <0 - 2147483647> ]
#                [-te_router_id   <a.b.c.d>  ]
#                [-te_unresv_bw_priority0 <0 - 2147483647> ]
#                [-te_unresv_bw_priority1 <0 - 2147483647> ]
#                [-te_unresv_bw_priority2 <0 - 2147483647> ]
#                [-te_unresv_bw_priority3 <0 - 2147483647> ]
#                [-te_unresv_bw_priority4 <0 - 2147483647> ]
#                [-te_unresv_bw_priority5 <0 - 2147483647> ]
#                [-te_unresv_bw_priority6 <0 - 2147483647> ]
#                [-te_unresv_bw_priority7 <0 - 2147483647> ]
#                [-vlan_id  <0-4095> ]
#                [-vlan_id_mode {fixed|increment} ]
#                [-vlan_id_step  <1-4094> ]
#                [-vlan_user_priority <0-7> ]
#                [-wide_metrics {0|1} ]
#
# Arguments:
#
#        -area_id                Identifies the area address to use for the IS-IS  router.
#                                Because IS-IS  can reside in more than one area, an ID can
#                                be up to 13-octets long (1 to 13), so you specify each ID as
#                                a string of 2 to 26 hexadecimal characters. (There must be
#                                an even number of hex characters.) The default area ID is
#                                000001.
#
#        -count                The number of routers to create on the interface. Possible
#                                values are 0 to <max_int>. The default is 1.
#
#        -csnp_interval        The maximum number of seconds between sending Complete
#                                Sequence Number PDUs over the interface when the session
#                                router is the designated router. Possible values range from
#                                1 to 65535. The default is 10.
#
#        -discard_lsp         Enables or disables whether to discard all LSPs coming from
#                                the neighbor. Possible values are 1 (enable) and 0 (disable)
#                                If enabled (1), Spirent TestCenter saves the routes. If
#                                disabled (0), Spirent TestCenter does not save the routes.
#
#        -handle                Specifies the handle for the port on which the IS-IS  router
#                                is to be configured. This argument is required for modify,
#                                delete, enable, and disable modes (see -mode).
#
#        -hello_interval
#                                Specifies the amount of time, in seconds, between Layer 1
#                                and Layer 2 protocol data units (PDUs). Possible values
#                                range from 1 to 65535. The default is 3.
#
#        -holding_time        Specifies the maximum amount of time, in seconds, between
#                                receipt of Hello PDUs before the link is pronounced down.
#                                Possible values range from 1 to 65535. The default is 10.
#
#        -intf_ip_addr        Specifies the IPv4 address of the interface for the IS-IS
#                                emulated router that will establish an adjacency with the
#                                DUT. The default is 0.0.0.0. Note that both the IPv4 and
#                                IPv6 addresses can be configured on the interface for ip
#                                version 4_6.
#
#        -intf_ip_addr_step
#                                Defines the increment used to generate IP addresses for
#                                emulated routers. Spirent TestCenter increments the
#                                -intf_ip_addr value. You must specify the interface
#                                IP address step when the -count argument is greater than 1.
#                                The range of possible values is 0 to <max_int>. The default
#                                is 0.
#
#        -intf_prefix_length
#                                Specifies the prefix length on the emulated router, Possible
#                                values for IPv4 addresses range from 1 to 32; the default is
#                                24,
#
#        -intf_ipv6_addr
#                                Specifies the IPv6 address of the interface for the IS-IS
#                                emulated router that will establish an adjacency with the
#                                DUT. The default is 0:0:0:0:0:0:0:0.
#
#        -intf_ipv6_addr_step
#                                Defines the increment used to generate IP addresses for
#                                emulated routers. Spirent TestCenter increments the
#                                -intf_ipv6_addr value. You must specify the interface
#                                IP address step when the -count argument is greater than 1.
#                                The range of possible values is 0 to <max_int>. The default
#                                is 0.
#
#        -intf_ipv6_prefix_length
#                                Specifies the prefix length on the emulated router, Possible
#                                values for IPv6 addresses range from 1 to 128; the default
#                                is 64,
#
#        -intf_metric        The cost metric associated with the route. Possible values
#                                range from 0 to 16777215. The default is 0.
#
#        -ip_version        Specifies the IP version of the IS-IS emulated router.
#                                Possible values are 4 (for IPv4 address format), 6 (for
#                                IPv6 address format), or 4_6 for both IPv4 and IPv6
#                                address formats. The default is 4. If you specify 4_6, wide
#                                metrics (see -wide_metrics argument) are automatically
#                                enabled.
#
#        -l1_router_priority
#                                Specifies the level 1 (L1) router priority for the IS-IS
#                                session. Possible values range from 0 to 255. The default is
#                                0.
#
#        -l2_router_priority
#                                Specifies the level 2 (L2) router priority for the IS-IS
#                                session. Possible values range from 0 to 255. The default is
#                                0.
#
#        -lsp_refresh_interval
#                                Specifies the rate, in seconds, at which LSPs are re-sent.
#                                Possible values range from 1 to 65535. The default is 900.
#
#        -mode                Specifies the action to perform. Possible values are create,
#                                enable, disable, modify, or delete. The default is disable.
#                                The modes are described below:
#
#                                create - Creates and starts one or more IS-IS  router on the
#                                        port        specified with the -port_handle argument. You must
#                                        specify the -port_handle argument.
#
#                                enable - Creates and starts one or more IS-IS  router on the
#                                        port        specified with the -port_handle argument. You must
#                                        specify the -port_handle argument.
#
#                                disable - Deletes all of the IS-IS  routers from the port
#                                        specified in the -handle argument. You must
#                                        specify the -handle argument.
#
#                                modify - Changes the configuration for the IS-IS  router
#                                        identified by the -handle argument. You must
#                                        specify the -handle argument.
#
#                                delete - Deletes all of the IS-IS  routers from the port
#                                        specified in the -handle argument. You must specify
#                                        the -handle argument.
#
#        -port_handle        Specifies the handle of the port on which to create the
#                                IS-IS  router. This argument is required.
#
#        -psnp_interval
#                                Specifies the minimum period between sending Partial
#                                Sequence Number PDUs over the interface when the session
#                                router is the DR. Possible values are 1 to 20. The default
#                                is 10.
#
#        -router_id_step
#                                Specifies the difference between router IDs of consecutive
#                                routers when multiple IS-IS  routers are created with the
#                                -count argument. Possible values are 0 to max_int. The
#                                default is 1.
#
#        -routing_level        Specifies the supported routing level: L1 only, L2 only, or
#                                both L1 and L2. Routing information is exchanged between
#                                Level 1 routers and other Level 1 routers. Level 2 routers
#                                only exchange information with other Level 2 routers. Level
#                                1-2 routers exchange information with both levels and are
#                                used to connect the interarea routers with the intra area
#                                routers. Possible values are L1, L2, or L1L2. The default is
#                                L1L2. Use this argument to specify the level to use to
#                                create the adjacency.
#
#        -system_id        Specifies the unique system ID. A system ID is typically
#                                six-octet long; therefore, you specify each system ID as a
#                                string of 12 hexadecimal characters. Possible values range
#                                from 000000000000 to FFFFFFFFFFFF. The default is
#                                0x0200+intf_ip in hex.
#
#        -te_admin_group
#                                Specifies the administrative group of the traffic
#                                engineering link. Possible values range from 1 to
#                                4294967295. The default is 1.
#
#        -te_enable        Enables or disables traffic engineering (TE) on all links.
#                                Possible values are 0 and 1. The default is 0 (disable).
#
#        -te_max_bw        Specifies the maximum bandwidth that can be
#                                used on the traffic engineering link. Possible values, in
#                                bytes per second, are 0 to 2147483647. The default is
#                                100000 bytes per second.
#
#        -te_max_resv_bw
#                                Specifies the maximum bandwidth that can be reserved traffic
#                                engineering link from the emulated router. Possible values,
#                                in bytes per second, are 0 to 2147483647. The default is
#                                100000 bytes per second.
#
#        -te_router_id        Specifies the TE router ID. The default is 0.0.0.0.
#
#        -te_unresv_bw_priority0
#                                Specifies the amount of bandwidth not yet
#                                reserved at priority level 0. The values corresponds to the
#                                bandwidth that can be reserved with a setup priority of 0
#                                through 7. Arranged in ascending order, priority 0 occurs at
#                                the start of the sub-TLV and priority 7 at the end. The
#                                initial values, before any bandwidth is reserved, are all
#                                set to the value specified for the maximum reservable
#                                bandwidth (-te_max_resv_bw). Each value will be less than or
#                                equal to the maximum reservable bandwidth. Possible values,
#                                in bytes per second, are 0 to 2147483647. The default is
#                                100000 bytes per second.
#
#        -te_unresv_bw_priority1
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 1. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority2
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 2. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority3
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 3. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority4
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 4. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority5
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 5. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority6
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 6. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -te_unresv_bw_priority7
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 7. Possible values, in bytes per second, are
#                                0 to 2147483647. The default is 100000 bytes per second.
#
#        -vlan_id                The VLAN ID of the first VLAN sub-interface. Possible values
#                                range from 0 to 4095. The default is 1. When the mode is
#                                either "create" or "enable", Spirent TestCenter checks for a
#                                vlan object on the port with the given vlan ID. If no vlan
#                                object with that ID exists, Spirent TestCenter creates a
#                                vlan object with the specified vlan ID.
#
#        -vlan_id_mode
#                                If you configure more than one interface on Spirent
#                                TestCenter with VLAN, you can choose to either automatically
#                                increment the VLAN tag (mode "increment") or leave it idle
#                                for each interface (mode "fixed"). If you set this argument
#                                to "increment", then you must also specify the -vlan_id_step
#                                argument to indicate the step size. The default is
#                                increment.
#
#         -vlan_id_step
#                                The step size by which the VLAN value is incremented when
#                                you set -vlan_id_mode to "increment". Possible values range
#                                from 1 to 4094. You must specify the step when the -count
#                                argument is greater than 1. The default is 1.
#
#        -vlan_user_priority
#                                VLAN priority for the VLANs on this port. Possible values
#                                range from 0 to 7. The default is 0.
#
#        -wide_metrics        Enables for disables wide style metrics. Possible values are
#                                1 (enable) and 0 (disable). If set to 1, enables both narrow
#                                and wide style metrics. If set to 0, then Spirent TestCenter
#                                uses only narrow metrics. The default is 0. Spirent
#                                TestCenter needs to use wide metrics for newer features such
#                                as IPv6 and TE.
#
# Spirent-specific Arguments:
#
#        -lsp_level        Specifies the level supported by the LSP: Level 1 or Level
#                                2. Possible values are L1 or L2. The default is L2. Use
#                                this argument to specify the level to use to create the
#                                links.
#
# Return Values: The sth::emulation_isis_config function returns a keyed list
#        using the following keys (with corresponding data):
#
#        handle                The handle that identifies the IS-IS  router created by the
#                                sth::emulation_isis_config function when you use "-mode
#                                create" or "-mode enable" to create a new IS-IS  router.
#                                When you want to modify, disable, or delete an IS-IS
#                                router, you specify the handle as the value to the -handle
#                                argument.
#
#        area_id                The area to which the router belongs.
#
#        system_id                The unique ID number of the system to which the router
#                                belongs
#
#        pseudonode_num        Thr unique ID number of the virtual router.
#
#        intf_ip_addr         The IPv4 address of the interface for the IS-IS
#                                emulated router.
#
#        intf_ipv6_addr        The IPv6 address of the interface for the IS-IS
#                                emulated router.
#
#        session_router        The handle of the router used in this IS-IS session.
#
#        status                Success (1) or failure (0) of the operation.
#        log                        An error message (if the operation failed).
#
# Description:        The sth::emulation_isis_config function creates, enables,
#        disables, modifies, or deletes IS-IS  routers from the specified port. Use
#        the -mode argument to specify the action to perform. (See the -mode
#        argument description for information about the actions.)
#
#        When you create an IS-IS  router, use the -port_handle argument to specify
#        the Spirent TestCenter port that the emulated router will use. (The port
#        handle value is contained in the keyed list returned by the connect
#        function.)
#
#        In addition to specifying the port (-port_handle), you must also provide
#        the following arguments when you create an IS-IS  router:
#
#        -mode create
#
#        -intf_ip_addr
#
#        -router_id
#
#        -area_id
#
#        -system_id
#
#        When you create a router, Spirent TestCenter automatically starts the
#        router communication.
#
#        Each emulated router establishes adjacency with the neighboring SUT.
#        Spirent TestCenter uses the Hello protocol to discover neighbors and, on
#        broadcast links, to elect a designated router, according to IS-IS
#        specifications.
#
#        Each Spirent TestCenter test module hosts an IS-IS stack capable of
#        emulating multiple IS-IS routers per port.
#
#        Once you start an IS-IS  session by creating routers, Spirent TestCenter
#        handles all of the messages for the emulated routers. During the test, you
#        can use the sth::emulation_isis_control function to stop and re-start
#        individual routers. To stop and start all of the routers associated with a
#        particular port, use the disable and enable modes with the
#        sth::emulation_isis_config function. After you have created the routers for
#        your test, use the sth::emulation_isis_topology_route_config function to
#        set up routes.
#
# Examples: The following example creates and starts an IS-IS IPv4
#        configuration:
#
#        ::sth::emulation_isis_config -port_handle $hPort($i)  \
#                                        -mode create  \
#                                        -ip_version 4_6 -system_id [expr 504030201000+$i] \
#                                        -area_id 000000000001 \
#                                        -count 1 \
#                                        -hello_interval 11 \
#                                        -holding_time 40
#                                        -intf_ip_addr [lindex $router1IpList $i] \
#                                        -intf_ip_addr_step 0.0.0.1 \
#                                        -intf_ip_prefix_length 16 \
#                                        -intf_metric 10 \
#                                        -l1_router_priority 0 \
#                                        -lsp_refresh_interval 3 \
#                                        -csnp_interval 30 \
#                                        -psnp_interval 3 \
#                                        -routing_level L1 \
#                                        -intf_ipv6_addr [lindex $router1Ipv6List $i]
#
#        Output:          {{status                                                  $SUCCESS | $FAILURE}
#                                {handle                                                  <ISIS_session_handle>}
#                                { session_router                                  <session_router_handle>}}
#
#        The following example stops and deletes the routers from the specified
#        port:
#
#        sth::emulation_isis_config -mode delete -port_handle $hPort($i)
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#
# End of Procedure Header


proc ::sth::emulation_isis_config { args } {
        ::sth::sthCore::Tracker ::emulation_isis_config $args 

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE

        variable ::sth::IsIs::isisTable
        variable ::sth::IsIs::userArgsArray
        array unset ::sth::IsIs::userArgsArray
        array set ::sth::IsIs::userArgsArray ""
        

        set _hltCmdName "emulation_isis_config"
        set myNameSpace "::sth::IsIs::"
        
        ::sth::sthCore::log hltapicall {Excuting command: {$_hltCmdName $args}}
        
        set returnKeyedList ""
        catch {unset sortedSwitchPriorityList} err
        if {[catch {::sth::sthCore::commandInit ::sth::IsIs::isisTable $args $myNameSpace $_hltCmdName userArgsArray sortedSwitchPriorityList} eMsg]} {  
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $eMsg" {}
                return $returnKeyedList  
        }
        
        set modeValue $userArgsArray(mode)
        
        if  {$modeValue == "enable"} {set modeValue  "create"}
        if  {$modeValue == "disable"} {set modeValue  "delete"}
        switch -exact $modeValue { 
                create -
                active -
                modify -
                inactive -
                activate -
                delete {
                        set cmdStatus 0
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "$_hltCmdName: unsupported mode $modeValue"
                        return $returnKeyedList 
                }
        }
        if {[catch {set procResult [eval $cmd]} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        } else {
                ::sth::sthCore::log stccall {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}                                   
                if {!$cmdStatus} {
                        return $returnKeyedList
                } else {
                        keylset returnKeyedList status $::sth::sthCore::SUCCESS
                        return $returnKeyedList
                }
        }
}


##Procedure Header
#
# Name: ::sth::emulation_isis_control
#
# Purpose:
#        Starts or stops an IS-IS  router. You can also use this function to
#        advertise LSPs or delete an LSP.
#
# Synopsis: emulation_isis_control
#                -handle   {LSP_session_handle}
#                -mode {stop | start | restart}
#                [-port_handle {port_handle} ]
#                [-advertise {list of topology_elem_handles} ]
#                [-withdraw {list of topology_elem_handles} ]
#
# Arguments:
#
#        -advertise        Advertises LSPs for topology elements.
#
#        -handle                Identifies the router to start or stop. This argument is
#                                required.
#
#        -port_handle        Identifies the port on which to stop or start the router.
#
#        -mode                Specifies the action to be taken. Possible values are stop,
#                                start, or restart the router, This argument is required.
#
#                                stop - Stops the router with the specified handle.
#
#                                start - Starts the router with the specified handle.
#
#                                restart - Stops the router with the specified handle
#                                        and then starts it again.
#
#        -withdraw                Specifies the LSPs to delete.
#
#
# Return Values: The function returns a keyed list using the following keys
#                        (with corresponding data):
#
#                status         Success (1) or failure (0) of the operation.
#                log                An error message (if the operation failed).
#
# Description: The emulation_isis_control function controls the starting and
#        stopping of routers as well as deleting them. At the same time you can
#        advertise or delete LSPs.
#
# Examples:
#        To start an IS-IS  router:
#
#        ::sth::emulation_isis_control
#                        -mode start -handle [lindex $hSession1($i) 0] \
#                        -advertise $hElementExternal1($i) \
#                                $hElementStub1($i)$hElementRouter1($i)
#
#        To stop and delete the routers:
#
#                 ::sth::emulation_isis_control -mode stop -handle 174
#
#         To restart a router:
#
#                 ::sth::emulation_isis_control -mode restart -handle 174
#
# Sample Input: See Examples.
#
# Sample Output:  {status 1}
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_isis_control { args } {
        ::sth::sthCore::Tracker ::emulation_isis_control $args 

    variable isis_subscription_state
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE

        variable ::sth::IsIs::isisTable
        variable ::sth::IsIs::userArgsArray
        array unset ::sth::IsIs::userArgsArray
        array set ::sth::IsIs::userArgsArray ""

        set _hltCmdName "emulation_isis_control"
        
        set myNameSpace "::sth::IsIs::"

        ::sth::sthCore::log hltapicall {Excuting command: {$_hltCmdName $args}}
        
        set returnKeyedList ""
        
        if {[catch {::sth::sthCore::commandInit ::sth::IsIs::isisTable $args $myNameSpace $_hltCmdName userArgsArray sortedSwitchPriorityList} eMsg]} {  
                ::sth::sthCore::processError returnKeyedList $eMsg {}
                return $returnKeyedList  
        }
        
        set modeValue $userArgsArray(mode)

    if {$isis_subscription_state == 0} {
        # subscribe to the resultdataset
        if {![::sth::sthCore::ResultDataSetSubscribe ::sth::IsIs:: IsisRouterConfig IsisRouterResults returnKeyedList]} {
                ::sth::sthCore::processError returnKeyedList "Error subscribing to the ISIS result data set" {}
                return $returnKeyedList  
        }
        set isis_subscription_state 1
    }

        switch -exact $modeValue {
        start {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
        stop {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
        restart {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
        flap {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
        default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "$_hltCmdName: Unsupported mode value $modeValue"
                        return $returnKeyedList
                }
        }
        #list of isis handles or single handle
		if {[info exists userArgsArray(handle)]} {
                    if {$userArgsArray(handle) ne "all" } {
                        set handlesList $userArgsArray(handle)       
                    } else {
                     set handlesList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-EmulatedDevice]
                    }
			foreach userArgsArray(handle) $handlesList {
				if {[catch {set procResult [eval $cmd]} eMsg]} {
					::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
					return $returnKeyedList
				} else {
					::sth::sthCore::log stccall {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}
					if {!$cmdStatus} {
						::sth::sthCore::log debug "Warning: Filed for the port: the flap parameters are only used in flap mode, ignored in start mode"
						set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList warning "$userArgsArray(handle) mode:  $modeValue Failed"]
						#setting back the list of handles 
						set userArgsArray(handle) $handlesList
						return $returnKeyedList
					} 
				}
			}
			# setting back list of the handles to userArgsArray if isis control is succedded
			set userArgsArray(handle) $handlesList
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
				
		#list of port handles or single port handle
		if {[info exists userArgsArray(port_handle)] || ![info exists userArgsArray(port_handle)]} {
                    if {[info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) ne "all"} {
			set isisPortList $userArgsArray(port_handle)
                    } else {
                        set isisPortList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Port]  
                      }
			foreach userArgsArray(port_handle) $isisPortList {
				if {[catch {set procResult [eval $cmd]} eMsg]} {
					::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
					return $returnKeyedList
				} else {
					::sth::sthCore::log stccall {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}                                   
					if {!$cmdStatus} {
						::sth::sthCore::log debug "Warning: Filed for the port: the flap parameters are only used in flap mode, ignored in start mode"
						set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList warning "$userArgsArray(port_handle) mode:  $modeValue Failed"]
						#setting back the list of handles 
						set userArgsArray(port_handle) $isisPortList
						return $returnKeyedList
					} 
				}
			}
			# setting back the handles list to userArgsArray if isis control is succedded
			set userArgsArray(port_handle) $isisPortList
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
}



##Procedure Header
#
# Name: ::sth::emulation_isis_topology_route_config
#
# Purpose:
#        Creates or modifies routes on or deletes routes from an emulated IS-IS
#        router on a Spirent TestCenter chassis. This function also configures the
#        properties of the IS-IS routes.
#
#        When you add a route (see description for -mode), Spirent TestCenter
#        returns the route handle in a keyed list with "connected_handles" as the 
#        key.
#
# Synopsis:
#        sth::emulation_isis_topology_route_config
#                { [-mode create -handle <isis_session_handle>] |
#                  [-mode [modify|delete]
#                                -elem_handle <lsp_handle> ] }
#                [-external_count <1-4294967295>  ]
#                [-external_ip_pfx_len  <1-32>  ]
#                [-external_ip_start   <a.b.c.d>   ]
#                [-external_ip_step  <1-255>  ]
#                [-external_ipv6_pfx_len  <1-128>  ]
#                [-external_ipv6_start  <0:0:0:0:0:0:0:0> ]
#                [-external_ipv6_step <1-255>  ]
#                [-external_metric  <0-65535> ]
#                [-external_metric_type   {internal|external}  ]
#                [-ip_version   {4|6|4_6}  ]
#                [-link_ip_addr   <a.b.c.d> ]
#                [-link_narrow_metric   <0-63>  ]
#                [-link_te   {0|1}  ]
#                [-link_te_admin_group   <1-4294967295>  ]
#                [-link_te_max_bw  <0 - 2147483647>  ]
#                [-link_te_max_resv_bw   <0 - 4294967295> ]
#                [-link_te_remote_ip_addr  <a.b.c.d>  ]
#                [-link_te_unresv_bw_priority0 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority1 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority2 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority3 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority4 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority5 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority6 <0 - 4294967295> ]
#                [-link_te_unresv_bw_priority7 <0 - 4294967295> ]
#                [-router_attached_bit   {0|1}  ]
#                [-router_connect   { another_elem_handle }  ]
#                [-router_disconnect   { another_elem_handle }  ]
#                [-router_id   <a.b.c.d>  ]
#                [-router_overload_bit   {0|1} ]
#                [-router_pseudonode_num  <0-255>  ]
#                [-router_routing_level   {L1|L2|L1L2}  ]
#                [-router_system_id <000000000000-FFFFFFFFFFFF> ]
#                [-router_te   {0|1} ]
#                [-stub_count <1-4294967295> ]
#                [-stub_ip_pfx_len   <1-32>  ]
#                [-stub_ip_start  <a.b.c.d> ]
#                [-stub_ip_step  <a.b.c.d> ]
#                [-stub_ipv6_pfx_len   <1-128>  ]
#                [-stub_ipv6_start   <0:0:0:0:0:0:0:0>  ]
#                [-stub_ipv6_step  <1-255> ]
#                [-stub_metric <0-65535> ]
#                [-stub_up_down_bit   {0|1}  ]
#                [-type   {internal | external}  ]
#
# Arguments:
#
#        -elem_handle        Specifies which topology element to modify or delete. You
#                                must specify this argument if the mode is modify or delete
#                                (see description for -mode),
#
#        -external_count
#                                Specifies the number of prefixes to be advertised for an
#                                external network. Possible values range from 1 to
#                                4294967295. The default is 1. Use this argument to configure
#                                a consecutive set of network prefixes
#
#        -external_ip_pfx_len
#                                The prefix length for the IPv4 external prefix. The IPv4
#                                external prefixes are advertised by TLV 130 for narrow
#                                style, and TLV 135 for wide style. Possible values range
#                                from 1 to 32. The default is 24.
#
#        -external_ip_start
#                                The first prefix to be advertised in the external network.
#                                The default is 0.0.0.0. You must specify a prefix length
#                                (-external_ip_pfx_le) with this argument,
#
#        -external_ip_step
#                                The amount by which the prefix to be advertised should
#                                be increased. Possible values are 1 to 255. The default is
#                                1. You must specify the -external_ip_start argument.

#        -external_ipv6_pfx_len
#                                The prefix length for the IPv6 external prefix. The IPv6
#                                external prefixes are advertised by TLV 236. Possible values
#                                range from 1 to 128. The default is 64.
#
#        -external_ipv6_start
#                                The first prefix to be advertised in the external network.
#                                The default is 0:0:0:0:0:0:0:0. You must specify a prefix
#                                length (-external_ipv6_pfx_le) with this argument,
#
#        -external_ipv6_step
#                                The amount by which the prefix to be advertised should
#                                be increased. Possible values are 1 to 255. The default is
#                                1. You must specify -external_ipv6_start argument.
#
#        -external_metric
#                                Specifies the metric value for external links. The range for
#                                wide style is different from narrow style. Possible values
#                                range from 0 to 65535.
#
#        -external_metric_type
#                                The type of metric element to configure for TLV 130.
#                                Possible values are 1 (internal) and 2 (external). The
#                                default is 1.
#
#                                1 - internal -  Configure internal metrics.
#
#                                2 - external -  Configure external metrics.
#
#        -handle                Identifies the router on which to create, modify, or
#                                delete a topology element. This argument is required.'
#
#        -ip_version        The IP version of the topology element. Possible values are 
#                                4, 6, or 4_6. The default value is 4_6. Note that you cannot 
#                                change the IP version for the TE topology elements after you 
#                                create them because Spirent TestCenter only supports Ipv4.
#
#        -link_ip_addr         Specifies the local interface IP address sub-TLV (type 3).
#                                The default for IPv4 is 0.0.0.0.
#
#        -link_narrow_metric
#                                Indicates whether to use a narrow metric. Possible values
#                                range from 0 to 63. The default is 1.
#
#        -link_te                Indicates whether to enable traffic engineering on the link.
#                                Possible values are 1 (enable) and 0 (disable). The default
#                                is 0.
#
#        -link_te_admin_group
#                                Specifies the link's administrative group membership,
#                                expressed as the decimal equivalent of a 32-bit bit mask.
#                                Each set bit corresponds to one administrative group
#                                assigned to the interface. A link can belong to multiple
#                                groups. By convention, the least significant bit is referred
#                                to as "group 0", and the most significant bit is referred to
#                                as "group 31". Possible values range from 1 to 4294967295.
#                                The default is 1. The Administrative Group sub-TLV is TLV
#                                type 9.
#
#        link_te_max_bw Specifies the maximum bandwidth that can be
#                                used on this traffic engineering link in this direction
#                                (from the originating router to its neighbor). The default
#                                is 100000 bytes per second.
#
#        link_te_max_resv_bw        teRsvrBandwidth
#                                Specifies the maximum reservable bandwidth sub-TLV (type 7),
#                                in bytes per second, that you can reserve on this link in
#                                this direction. The default is 100000 bytes per second.
#
#        link_te_remote_ip_addr
#                                The remote interface IP address sub-TLV (type 4). The
#                                default is 0.0.0.0.
#
#        link_te_unresv_bw_priority0
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 0. The values corresponds to the bandwidth
#                                that can be reserved with a setup priority of 0 through 7.
#                                Arranged in ascending order, priority 0 occurs at the start
#                                of the sub-TLV and priority 7 at the end. The initial
#                                values, before any bandwidth is reserved, are all set to the
#                                value specified for the maximum reservable bandwidth
#                                (-link_te_max_resv_bw). Each value will be less than or
#                                equal to the maximum reservable bandwidth. Possible values,
#                                in bytes per second, are 0 to 4294967295. The default is
#                                100000 bytes per second.
#
#        link_te_unresv_bw_priority1   teUnRsvrBandwidth1
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 1. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority2
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 2. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority3
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 3. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority4
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 4. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority5
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 5. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority6
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 6. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        link_te_unresv_bw_priority7
#                                Specifies the amount of bandwidth not yet reserved at
#                                priority level 7. Possible values, in bytes per second, are
#                                0 to 4294967295. The default is 100000 bytes per second.
#
#        -mode                Specifies whether to create, modify, or delete LSPs from the
#                                emulated router's LSR database. Possible values are:
#
#                                create - Creates a new LSP for the IS-IS session. The handle
#                                        for the LSP is returned in the lsp_handle key (see
#                                        Return Values).
#
#                                modify - Modifies the setup for the LSP specified in the
#                                        -lsp_handle argument.
#
#                                delete - Removes the LSP specified in the -lsp_handle
#                                        argument.
#
#        -router_attached_bit
#                                Specifies whether to set the 0th LSP's attached bit.
#                                Possible values are 1 (true) and 0 (false). The default
#                                is 0. The attached bit enables an L1 router to figure out
#                                who its closest L2 router is. You should set this bit if you
#                                are connected to either 1) other areas, or 2) other domains.
#
#        -router_connect
#                                Specifies the handle of the IS-IS router to which you 
#                                want to connect the current session router.
#
#        -router_disconnect
#                                Specifies the handle of the IS-IS router from which you 
#                                want to disconnect the current session router.
#
#        -router_id         Specifies the TE router ID. The default is 0.0.0.0.
#
#        -router_overload_bit
#                                Specifies whether to enable the LSP's overload bit on the
#                                router to add or modify. If enabled (1), sets the 0th LSP's
#                                overload bit. The default is 0
#
#        -router_pseudonode_num
#                                Specifies the ID of the virtual router to add or modify.
#                                Possible values range from 0 to 255. The default is 0. A
#                                pseudonode is not a real router. It's an extra LSP in the
#                                LSP database that is created by the designated router.
#
#        -router_routing_level
#                                Specifies the supported routing level: L1 or L2. IS-IS has
#                                two layers of hierarchy: the backbone is called "level-2,
#                                and the areas are called level-1. The default is L2.
#
#        -router_system_id
#                                Specifies the system ID of the router to add or modify. A
#                                system ID is typically 6-octet long thus each ID is
#                                specified as a string of 12 hex characters. Possible values
#                                range from 000000000000 to FFFFFFFFFFFF. The default is
#                                00-00-01-00-00-03.
#
#        -router_te
#                                Specifies whether the TE router ID is set. Possible values
#                                are 1 (true) and 0 (false). The default is 0.
#
#        -stub_count
#                                Configures a consecutive set of network prefixes when adding
#                                or modifying internal (stub) networks behind a session 
#                                router. The IPv4 stub networks are advertised by TLV 128 for 
#                                narrow metric style and TLV 135 for wide metric style. The 
#                                IPv6 stub networks are advertised by TLV 236. Possible 
#                                values range from 1 to 4294967295. The default is 1.
#
#        -stub_ip_pfx_len
#                                Specifies the prefix length of the stub network. Possible
#                                values for IPv4 addresses range from 1 to 32; the default is
#                                24,
#
#        -stub_ip_start        The first prefix to be advertised in the IPv4 network.
#                                The default is 0.0.0.0. You must specify a prefix
#                                length (-stub_ip_pfx_le) with this argument,
#
#        -stub_ip_step        The amount by which the prefix to be advertised should
#                                be increased. Possible values are 1 to 255. The default is
#                                1. You must specify the -stub_ip_start argument.
#
#        -stub_ipv6_start
#                                The first prefix to be advertised in the IPv6 network.
#                                The default is 0:0:0:0:0:0:0:0. You must specify a prefix
#                                length (-stub_ipv6_pfx_le) with this argument,
#
#        -stub_ipv6_step
#                                The amount by which the prefix to be advertised should
#                                be increased. Possible values are 1 to 255. The default is
#                                1. You must specify the -stub_ipv6_start argument.
#
#        -stub_ipv6_pfx_len
#                                Specifies the prefix length of the stub network. Possible
#                                values for IPv6 addresses range from 1 to 128; the default
#                                is 64,
#
#        -stub_metric        Specifies the metric value for stub links. The range for
#                                wide style is different from narrow style. Possible values
#                                range from 0 to 65535.
#
#        -stub_up_down_bit upDown
#                                Specifies whether the route is advertised from Level 2 to
#                                Level 1. Possible value are 1 (true) and 0 (false). The
#                                default is 0. If this argument is set to 1, the route is 
#                                advertised from Level 2 to Level 1. If this argument is set 
#                                to 0, the route is not advertised from Level 2 to Level 1.
#
#        -type                Specifies the type of topology element to be created. 
#                                Possible values are "internal" or "external". 
#                                
#                                - internal: stub network with a number of reachable network 
#                                  prefixes
#                                - external: external network with a number of reachable
#                                  network prefixes
#
# Return Values: The function returns a keyed list using the following keys:
#                        (with corresponding data):
#
#        elem_handle 
#                        The handle that identifies the router created by the
#                        sth::emulation_isis_topology_route_config function.
#
#        version        The IP version of the IS-IS emulated router: IPv4, IPv6, or 
#                        IPv4/6.
#
#        router
#                connected_handles <connected_elem_handles>
#                        The number of elements to which the router is connected.
#
#        network stub
#                num_networks                 <num_networkstub_prefixes>
#                        The number of internal (stub) network prefixes advertised.
#        external
#                num_networks                 <num_external_prefixes>
#                        The number of external network prefixes advertised.
#
#        status        Success (1) or failure (0) of the operation.
#
#        log                An error message (if the operation failed).
#
# Description: Each emulated IS-IS router simulates a topology of inter-
#        connected routers behind itself. It accomplishes this by advertising Link
#        State Protocol Data Units (LSPs), with the IS Neighbors TLV
#        (Type/Length/Value) or the Extended Reachability TLV, to the SUT.
#
#        The sth::emulation_isis_topology_route_config function creates and 
#        configures IP routes for the IS-IS protocol. Use the -elem_handle argument 
#        to identify the router for which to create, modify, or delete a route. (The 
#        router handle value is contained in the keyed list returned by the 
#        emulation_isis_config function.) Use the -mode argument to specify the 
#        action to perform. See the -mode argument for a description of the actions.
#
# Examples: The following example creates a route for each IS-IS  router on
#        port1:
#
# ::sth::emulation_isis_topology_route_config -mode create \
#                                                                -handle [lindex $hSession1($i) 0]
#                                                                -ip_version 4 \
#                                                                -type external \
#                                                                -external_count 10 \
#                                                                -external_ip_pfx_len 16 \
#                                                                -external_ip_start 21.$i.0.0 \
#                                                                -external_ip_step 10 \
#                                                                -external_metric 10 \
#                                                                -external_metric_type internal \
#                                                                -router_system_id [expr 504030201000+$i]
#
#        Output:
#
# Sample Input:
#
# Sample Output:
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_isis_topology_route_config { args } {
        ::sth::sthCore::Tracker ::emulation_isis_topology_route_config $args 

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE

        variable ::sth::IsIs::isisTable
    
        variable ::sth::IsIs::userArgsArray
        array unset ::sth::IsIs::userArgsArray
        array set ::sth::IsIs::userArgsArray ""


        set _hltCmdName "emulation_isis_topology_route_config"        
        set myNameSpace "::sth::IsIs::"

        ::sth::sthCore::log hltapicall {Excuting command: {$_hltCmdName $args}}
        
        set returnKeyedList ""
        if {[catch {::sth::sthCore::commandInit ::sth::IsIs::isisTable $args $myNameSpace $_hltCmdName userArgsArray sortedSwitchPriorityList} eMsg]} {  
                ::sth::sthCore::processError returnKeyedList $eMsg {}
                return $returnKeyedList  
        }
        set modeValue $userArgsArray(mode)

        switch -exact $modeValue {
        create {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                modify {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                delete {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "$_hltCmdName: Unsupported mode value $modeValue"
                        return $returnKeyedList
                }
        }
        if {[catch {set procResult [eval $cmd]} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        } else {
                ::sth::sthCore::log stccall {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}                                   
                if {!$cmdStatus} {
                        return $returnKeyedList
                } else {
                        keylset returnKeyedList status $::sth::sthCore::SUCCESS
                        return $returnKeyedList
                }
        }
}

##Procedure Header
#
# Name: ::sth::emulation_isis_lsp_generator
# detail info pls refer user Doc.
proc ::sth::emulation_isis_lsp_generator { args } {
        ::sth::sthCore::Tracker ::emulation_isis_lsp_generator $args 

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE

        variable ::sth::IsIs::isisTable
    
        variable ::sth::IsIs::userArgsArray
        array unset ::sth::IsIs::userArgsArray
        array set ::sth::IsIs::userArgsArray ""


        set _hltCmdName "emulation_isis_lsp_generator"        
        set myNameSpace "::sth::IsIs::"

        ::sth::sthCore::log hltapicall {Excuting command: {$_hltCmdName $args}}
        
        set returnKeyedList ""
        if {[catch {::sth::sthCore::commandInit ::sth::IsIs::isisTable $args $myNameSpace $_hltCmdName userArgsArray sortedSwitchPriorityList} eMsg]} {  
                ::sth::sthCore::processError returnKeyedList $eMsg {}
                return $returnKeyedList  
        }
        set modeValue $userArgsArray(mode)

        switch -exact $modeValue {
        create {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                modify {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                delete {
                        set cmdStatus 0
                        
                        set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltapicall {CMD which will process for mode($modeValue): $cmd }
                }
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "$_hltCmdName: Unsupported mode value $modeValue"
                        return $returnKeyedList
                }
        }
        if {[catch {set procResult [eval $cmd]} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        } else {
                ::sth::sthCore::log stccall {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}
                if {!$cmdStatus} {
                        return $returnKeyedList
                } else {
                        keylset returnKeyedList status $::sth::sthCore::SUCCESS
                        return $returnKeyedList
                }
        }
}


#MRQ24517: HLTAPI ISIS info support
#Author: RXu
proc ::sth::emulation_isis_info { args } {
set procName [lindex [info level [info level]] 0]

    variable ::sth::IsIs::sortedSwitchPriorityList
    variable ::sth::IsIs::userArgsArray
    array unset ::sth::IsIs::userArgsArray
    array set ::sth::IsIs::userArgsArray {}

    set _hltCmdName "emulation_isis_info"

    ::sth::sthCore::Tracker "::sth::emulation_isis_info" $args

    set underScore "_"

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::IsIs::isisTable $args ::sth::IsIs:: $_hltCmdName ::sth::IsIs::userArgsArray ::sth::IsIs::sortedSwitchPriorityList} err]} {
        puts "1 $procName commandInit Failed: $err"
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore $procName commandInit Failed: $err"
        return $returnKeyedList 
    }

     
     set modeVal $userArgsArray(mode)
     if {[info exists userArgsArray(handle)] && $userArgsArray(handle) ne "all"} {
         set handle $userArgsArray(handle)
     } else {
        set handle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-EmulatedDevice]
     }
     set msg ""
    foreach isisDev $handle {
    switch -exact -- $modeVal {
        stats {
                set isis_router_config [::sth::sthCore::invoke stc::get $isisDev -children-IsisRouterConfig]
                set isis_router_result [::sth::sthCore::invoke stc::get $isis_router_config -children-IsisRouterResults]
                foreach attr [array names ::sth::IsIs::emulation_isis_info_stcattr] {
                        set stcAttrName [set ::sth::IsIs::emulation_isis_info_stcattr($attr)]
                        if {$stcAttrName == "_none_"} { continue }
                        if {[catch {set val [::sth::sthCore::invoke stc::get $isis_router_result -$stcAttrName]} err ]} {
                                puts "3 processL2TPSessionGetCmd stc::get Failed: $err"
                                ::sth::sthCore::processError returnKeyedList "::sth::l2tp::processL2TPSessionGetCmd stc::get Failed: $err"
                                return $returnKeyedList
                        }
                        keylset tempKeyedList $attr $val
                }
        }
        clear_stats {
                if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -Project $::sth::GBLHNDMAP(project)} err ] } {
                        ::sth::sthCore::processError returnKeyedList "stc::Perform ResultsClearAll -Project $::sth::GBLHNDMAP(project) Failed: $err"
                        return $returnKeyedList
                }
        }
        SHA_NO_USER_INPUT {
            #puts "31 $procName: No Value for the switch: mode Value:$modeVal."
            ::sth::sthCore::processError returnKeyedList "$procName: No Value for the switch: mode Value:$modeVal."
            return $returnKeyedList 
        }
        SHA_UNKNWN_SWITCH -
        default {
            #puts "32 $procName: Unable to process -mode value: $modeVal."
            ::sth::sthCore::processError returnKeyedList "$procName: Unable to process -mode value: $modeVal."
            return $returnKeyedList 
        }
    }
    if {[info exists tempKeyedList] && $tempKeyedList ne ""} {
        keylset returnKeyedList $isisDev $tempKeyedList
    }
    if {[llength $handle] == 1 && $modeVal ne "clear_stats"} {
        set KeyVal [keylget returnKeyedList $isisDev]
        foreach key $KeyVal {
           keylset returnKeyedList [lindex $key 0] [lindex $key 1]  
        }
    }
}
    keylset returnKeyedList procName $procName
    if {[info exists userArgsArray(handle)]} {
       keylset returnKeyedList handles $userArgsArray(handle)
    } else {
      keylset returnKeyedList handles $handle  
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList procName "emulation_isis_info"

    return $returnKeyedList
}
#MRQ24517 end


proc ::sth::IsIs::emulation_isis_config_stak { args } {
    package require xtapi
    ::sth::sthCore::Tracker "::sth::IsIs::emulation_isis_config_stak" $args
       
    set _hltCmdName "::sth::IsIs::emulation_isis_config_stak"
    if {[catch {
	    set ::sth::IsIs::returnKeyedList [eval ::xtapi::scriptrun_stak $_hltCmdName $args]} err]} {
		::sth::sthCore::processError ::sth::IsIs::returnKeyedList "Error in processing isis protocol : $err"
	    return $::sth::IsIs::returnKeyedList
    }
    keylset ::sth::IsIs::returnKeyedList status $::sth::sthCore::SUCCESS 
    return $::sth::IsIs::returnKeyedList
}
