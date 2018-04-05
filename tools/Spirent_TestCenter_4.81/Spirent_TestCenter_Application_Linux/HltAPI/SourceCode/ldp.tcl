# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth:: {
}

##Procedure Header
#
# Name:
#    sth::emulation_ldp_config
#
# Purpose:
#    Creates, enables, disables, modifies, or deletes an emulated Label Switched
#    Router (LSR) on a Spirent HLTAPI chassis.
#
#    LDP (Label Distribution Protocol) is a protocol that defines a set of
#    procedures and messages by which one LSR informs another of the label
#    bindings it has made. LDP enables LSRs to find each other and establish
#    communication.
#
# Synopsis:
#    sth::emulation_ldp_config
#         -mode   { create | enable | disable | modify | delete }
#              -port_handle   <port_handle>
#         -handle   { ldp_session_handle }
#         [-affiliated_router_target <router_session_handle>]
#         [-count <integer>]
#         [-graceful_restart {0|1}
#               -reconnect_time <0-4294967>
#               -recovery_time <0-4294967> ]
#         [-gateway_ip_addr <a.b.c.d> ]
#              [-gateway_ip_addr_step <a.b.c.d> ]
#         [-hello_interval   <1-21845> ]
#         [-intf_ip_addr  <a.b.c.d> ]
#              [-intf_ip_addr_step  <a.b.c.d>]
#              [-intf_prefix_length <1-32> ]
#         [-keepalive_interval <1-21845> ]
#         [-label_adv   {unsolicited|on_demand} ]
#         [-label_start  <0-1046400> ]
#         [-label_step <integer> ]
#         [-lsr_id   <a.b.c.d> ]
#              [-lsr_id_step <a.b.c.d>]
#         [-mac_address_init <aa:bb:cc:dd:ee>]
#         [-peer_discovery   {link|targeted} ]
#         [-remote_ip_addr   <a.b.c.d> ]
#              [-remote_ip_addr_step <a.b.c.d>]
#         [-vlan_id  <0-4095> ]
#              [-vlan_cfi {0|1} ]
#              [-vlan_id_mode {fixed|increment} ]
#              [-vlan_id_step  <1-4094> ]
#              [-vlan_user_priority <0-7> ]
#         [-vci <0-65535> ]
#              [-vci_step <0-65535> ]
#         [-vpi <0-4095> ]
#              [-vpi_step <0-4095> ]
#
# Arguments:
#
#    -affiliated_router_target
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the router to which the indirectly connected
#                   router will be connected. The value for the router session
#                   handle is alphanumeric. This option is used to support LDP
#                   testing with peer_discovery in targeted mode. For example,
#                   you could create an OSPF router to advertise IP routes. From
#                   this router, you could then create an indirectly connected
#                   router to run LDP.
#
#                   set retKeyList [::sth::emulation_ldp_config -mode create \
#                                 -port_handle $p0 \
#                                 -peer_discovery targeted \
#                                 -affiliated_router_target $ospf_router_handle\
#                                 -count 1 \
#
#                   The value of "mac_address_init <mac_addr>" will be ignored
#                   when you pass in a value for the -affiliated_router_target
#                   attribute. Spirent HLTAPI fills in the MAC address of
#                   the indirectly connected router using the MAC address
#                   obtained from the router pointed to by the
#                   affiliated_router_target handle. Note that there is no
#                   support for the retrieval of the MAC address for a
#                   router in the HLTAPI framework.
#
#    -count         Defines the number of sessions to create on the interface by
#                   incrementing the interface IP address (-intf_ip_addr), Label
#                   Switched Router ID (-lsr_id), and  remote IP address
#                   (-remote_ip_addr). Possible values are 0 to <max_int>. The
#                   default is 1. If you specify a count greater than 1, then
#                   the -intf_ip_addr_step, -gateway_ip_addr_step, -lsr_id_step,
#                   and -remote_ip_addr_step arguments are required.
#
#    -gateway_ip_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address of the label
#                   switched router.
#
#    -gateway_ip_addr_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address for multiple routers.
#                   This argument is used with the -gateway_ip_addr argument.
#
#    -graceful_restart
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies if LDP graceful restart is enabled on the
#                   emulated router. Possible values are 1 (enable Graceful
#                   Restart) or 0 (disable Graceful Restart). The default is 0.
#                   To use -graceful_restart in LDP, you must also specify
#                   values for the -reconnect_time and -recovery_time arguments.
#
#                   Example usage:
#
#                   sth::emulation_ldp_config -mode create \
#                        -port_handle $p0 \
#                        -graceful_restart <0|1>
#                        -reconnect_time <0-4294967>
#                        -recovery_time <0-4294967>
#
#    -handle
#                   Specifies the LDP handle for the port to be configured. The
#                   value for the handle is alphanumeric. This argument is
#                   required for the modify, delete, enable, and disable modes
#                   (see -mode).
#
#    -hello_interval
#                   Specifies the amount of time, in seconds, between HELLO
#                   messages. Possible values range from 1 to 21845. The default
#                   is 5.
#
#    -intf_ip_addr  Specifies the IP address of the interface for the LSR that
#                   will establish an adjacency with the DUT. The default for
#                   IPv4 is 192.85.1.3.
#
#    -intf_ip_addr_step
#                   Defines the interface IP addresses of consecutive routers
#                   when multiple routers are created. The default is 0.0.0.0.
#
#    -intf_prefix_length
#                   Specifies the prefix length on the emulated router, Possible
#                   values for IPv4 addresses range from 1 to 32; the default is
#                   24.
#
#    -keepalive_interval
#                   Specifies the amount of time, in seconds, between KEEPALIVE
#                   messages. Possible values range from 1 to 21845. The default
#                   is 60.
#
#    -label_adv
#                   Specifies the label advertisement mode for the router,
#                   the mode by which the emulated router advertises its FEC
#                   ranges. Possible values are:
#
#                   unsolicited - The router distributes FEC ranges whenever it
#                        has a new one. This is the default value.
#
#                   on_demand - The router only distributes FEC ranges when
#                        requested by a peer.
#
#                   The default is unsolicited.
#
#    -label_start
#                   Specifies the starting value for the first label of the
#                   route. Possible values range from 0 to 1046400. The default
#                   is 16.
#
#    -label_step
#                   Specifies how to increment the next label.The default is 1.
#
#    -lsr_id
#                   Specifies the router ID of the Label Switched Router (LSR)
#                   to be emulated by the Spirent HLTAPI port. The LSR ID is a
#                   32-bit value represented in dot notation. The default is
#                   192.85.1.3.
#
#    -lsr_id_step
#                   Defines the router ID of consecutive routers when multiple
#                   routers are created. You must specify a step value when the
#                   -count value is greater than 1. The default is 0.0.0.0.
#
#    -mac_address_init
#                   Specifies the MAC address to use for the first session. When
#                   -count is greater than 1, the MAC address is automatically
#                   incremented by one on the last octet
#
#    -mode
#                   Specifies the action to perform. Possible values are create,
#                   enable, disable, modify, or delete. This argument is
#                   required. The modes are described below:
#
#                   create - Creates one or more emulated label switched
#                        routers, and then starts all of the routers under the
#                        specified port. You must specify the -port_handle
#                        argument. Specify additional arguments to supply
#                        address information for the emulated routers.
#
#                   enable - Same as "create".
#
#                   disable - Same as "delete".
#
#                   modify - Changes the configuration for the LSR identified by
#                        the -handle argument.
#
#                   delete - Deletes the LSR specified in the -handle argument.
#
#    -peer_discovery
#                   Specifies whether the emulated router sends a link or a
#                   targeted hello. Possible values are:
#
#                   link - A Basic Discovery mechanism used to locate directly-
#                        connected neighbors. "Link" is the default.
#
#                   targeted - An Extended Discovery mechanism used to locate
#                        neighbors not directly connected.
#
#    -port_handle
#                   Specifies the handle of the port on which to create the
#                   label switched router (LSR). This argument is required only
#                   for create and enable modes.
#
#    -reconnect_time
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the amount of time, in seconds, it takes Spirent
#                   HLTAPI to reconnect after a graceful restart. To use
#                   this option, you must also enable -graceful_restart and
#                   specify a value for the -recovery_time argument. Possible
#                   values are 0 to 4294967. The default is 60.
#
#    -recovery_time
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the amount of time, in seconds, it takes Spirent
#                   HLTAPI to recover after a graceful restart. To use
#                   this option, you must also enable -graceful restart and
#                   specify a value for the -reconnect_time argument. Possible
#                   values are 0 to 4294967. The default is 140.
#
#    -remote_ip_addr
#                   Specifies either the IPv4 address of the DUT interface that
#                   is connected to the Spirent HLTAPI port for the emulated
#                   LSR or the DUT router ID. The default is 192.85.1.1.
#
#    -remote_ip_addr_step
#                   Configures either the IPv4 address of the DUT interface for
#                   multiple routers or the DUT router ID. You must specify the
#                   -remote_ip_address_step when the -count argument is greater
#                   than 1. The format of the remote_ip_addr_step value is an IP
#                   address, for example, 0.0.0.1.
#
#    -vlan_cfi
#                   Sets the canonical format indicator field in VLAN for the
#                   emulated router node. Possible values are 0 (Ethernet) and 1
#                   (Token Ring). If set to 0, it indicates the network is
#                   Ethernet. If set to 1, it indicates that Token Ring and
#                   packets are dropped by Ethernet ports.
#
#    -vlan_id
#                   The VLAN ID of the first VLAN sub-interface. Possible values
#                   range from 0 to 4095. When the mode is either "create" or
#                   "enable", Spirent HLTAPI checks for a vlan object on the
#                   port with the given vlan ID. If no vlan object with that ID
#                   exists, Spirent HLTAPI creates a vlan object with the
#                   specified vlan ID.
#
#    -vlan_id_mode
#                   If you configure more than one interface on Spirent
#                   HLTAPI with VLAN, you can choose to either automatically
#                   increment the VLAN tag (mode "increment") or leave it idle
#                   for each interface (mode "fixed"). If you set this argument
#                   to "increment", then you must also specify the -vlan_id_step
#                   argument to indicate the step size. The default is
#                   increment.
#
#    -vlan_id_step
#                   The step size by which the VLAN value is incremented when
#                   you set -vlan_id_mode to "increment". Possible values range
#                   from 1 to 4094. You must specify the step when the -count
#                   argument is greater than 1. The default is 1.
#
#    -vlan_user_priority
#                   VLAN priority for the VLANs on this port. Possible values
#                   range from 0 to 7. The default is 0.
#
#    -vci           Set the VCI for emulated router node. Possible values
#                   range from 0 to 65535. The default value is 32.
#
#    -vci_step      Set the step value to apply to VCI field when multiple
#                   emulated routers are created. The default is 1.
#
#    -vpi           Set the VPI for emulated router node. Possible values
#                   range from 0 to 4095. the default value is 0.
#
#    -vpi_step      Set the step value to apply to VCI field when multiple
#                   emulated routers are created. The default is 1.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -atm_merge_cap
#    -atm_range_max_vci
#    -atm_range_max_vpi
#    -atm_range_min_vci
#    -atm_range_min_vpi
#    -atm_vc_dir
#    -cfi
#    -config_seq_no
#    -discard_self_adv_fecs
#    -egress_label_mode
#    -hello_hold_time
#    -keepalive_holdtime
#    -label_space
#    -label_type
#    -loop_detection
#    -max_lsps
#    -max_pdu_length
#    -max_peers
#    -message_aggregation
#    -mtu
#    -path_vector_limit
#    -timeout
#    -transport_ip_addr
#    -user_priofity
#
# Return Values:
#    The sth::emulation_ldp_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handle         The handle that identifies the LDP router created by the
#                   sth::emulation_ldp_config function.
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Description:
#    The sth::emulation_ldp_config function creates, enables,
#    disables, modifies, or deletes the specified LSR. Use the -mode argument to
#    specify the action to perform. (See the -mode argument description for
#    information about the actions.)
#
#    To create an LSR, use the create or enable modes with the
#    sth::emulation_ldp_config function along with the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated LSR will use. (The port
#    handle value is contained in the keyed list returned by the connect
#    function.)
#
#    In addition to specifying the port, you must also provide one or more of
#    the following pieces of information when you create an LSR:
#
#    - The port handle (-port_handle argument)
#
#    - The IP address for the router (the -intf_ip_addr argument)
#
#    - The IP address for the router (DUT) to communicate with (the
#      -gateway_ip_add and -remote_ip_addr arguments)
#
#    For Spirent HLTAPI to start the router communication, use the
#    sth::emulation_ldp_control mode "start" to start either an individual
#    router or all emulated routers.
#
#    Two LSRs (Label Switched Routers) which use LDP to exchange label mapping
#    information are known as LDP peers and they have an LDP session between
#    them. In a session, each peer learns about the other's label mappings.
#
#    LDP has four types of LDP messages: discovery (HELL0), adjacency
#    (KEEPALIVE), label advertisement, and notification (error messages).
#
#    LSRs announce their presence in the network by sending HELLO messages at
#    specified intervals. HELLO messages are transmitted as UDP packets. All
#    other messages are sent over TCP.
#
#    Once you start an LDP session, Spirent HLTAPI handles all of the
#    messages for the emulated routers. During the test, use the
#    sth::emulation_ldp_control function to stop and re-start individual
#    routers. To delete all of the routers associated with a particular
#    port, use the disable or delete modes with the sth::emulation_ldp_config
#    function. After you have created the routers for your test, use the
#    sth::emulation_ldp_route_config function to set up routes.
#
# Examples: The following example creates and starts an LSR on an LDP port:
#
#    sth::emulation_ldp_config \
#                   -mode create \
#                   -count 5 \
#                   -hello_interval 15 \
#                   -intf_ip_addr 192.168.1.11 \
#                   -intf_ip_addr_step 0.0.1.0 \
#                   -intf_prefix_length 24 \
#                   -keepalive_interval 70 \
#                   -label_adv on_demand\
#                   -label_start 7 \
#                   -label_step 7 \
#                   -lsr_id 12.1.1.1 \
#                   -lsr_id_step 0.0.0.1 \
#                   -peer_discovery link \
#                   -port_handle $port_handle1 \
#                   -gateway_ip_addr 192.168.1.1 \
#                   -gateway_ip_addr_step 0.0.1.0 \
#                   -remote_ip_addr 1.1.1.4 \
#                   -remote_ip_addr_step 0.0.0.0 \
#                   -vlan_cfi 0 \
#                   -vlan_id 7 \
#                   -vlan_id_mode increment \
#                   -vlan_id_step 7 \
#                   -vlan_user_priority 7
#
# Modify the created LDP router:
#
#    sth::emulation_ldp_config -handle $ldpRouterHandle \
#                            -hello_interval 5 \
#                            -mode modify
#
# Delete the created LDP router:
#
#     sth::emulation_ldp_config -handle $ldpRouterHandle \
#                         -mode delete
#
#    Output:    {handle router1} {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#
# End of Procedure Heade
proc ::sth::emulation_ldp_config { args } {
        ::sth::sthCore::Tracker ::emulation_ldp_config $args
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
      
        variable ::sth::Ldp::emulation_ldp_config\_user_input_args_array
        array unset ::sth::Ldp::emulation_ldp_config\_user_input_args_array
        array set ::sth::Ldp::emulation_ldp_config\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_ldp_config\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_ldp_config"
        
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_ldp_config \
                                                        ::sth::Ldp::emulation_ldp_config\_user_input_args_array \
                                                        ::sth::Ldp::emulation_ldp_config\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_ldp_config_user_input_args_array(mode)
        switch -exact $modeValue {
                create -
                enable {
                        set modeValue "create"
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                modify {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                delete -
                disable {
                        set modeValue "delete"
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                inactive {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                active {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                }
                activate {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                }
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        }
        
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying LDP configuration: $msg"
        return $returnKeyedList 
    }
    
        if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
                return $returnKeyedList
        } else {
                keylset returnKeyedList status $::sth::sthCore::SUCCESS
                return $returnKeyedList                        
        }
}                                                                                                                
##Procedure Header
#
# Name:
#    sth::emulation_ldp_control
#
# Purpose:
#    Starts, stops, or restarts an LSR.
#
# Synopsis:
#    sth::emulation_ldp_control
#         -handle <LDP_session_handle>
#         -mode {stop | start | restart }
#         [-port_handle <port_handle> ]
#
# Arguments:
#
#    -handle
#                   Identifies the router handle, returned from the
#                   emulation_ldp_config function when creating an LSR. This
#                   argument is required. The router handle value is
#                   alphanumeric.
#
#    -port_handle
#                   Identifies the port on which to stop, start, or restart the
#                   routers.
#
#    -mode
#                   Specifies the action to be taken. Possible values are
#                   stop, start, or restart the LSR, This argument is required.
#
#                   stop - Stops the router with the specified handle.
#
#                   start - Starts the router with the specified handle.
#
#                   restart - Stops the router with the specified handle
#                       and then starts it again. If graceful restart is
#                       enabled (sth::emulation_ldp_config -graceful_restart 1),
#                       the restart mode restarts the router without stopping
#                       the router first.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -advertise
#    -flap_count
#    -flap_down_time
#    -flap_interval_time
#    -flap_router
#    -withdraw
#
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status    Success (1) or failure (0) of the operation.
#         log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_ldp_control function controls the starting and
#    stopping of LSRs as well as deleting them.
#
# Examples:
#    To start an LSR:
#
#         sth::emulation_ldp_control -mode start -handle $ldpRouterHandle
#
#    To stop an LSR:
#
#         sth::emulation_ldp_control -mode stop -handle $ldpRouterHandle
#
#    To restart an LSR:
#
#         sth::emulation_ldp_control -mode restart -handle $ldpRouterHandle
#
# Sample Input: See Examples.
#
# Sample Output:  {status 1}
#
# Notes: None
#
# End of Procedure Header
proc ::sth::emulation_ldp_control { args } {
        ::sth::sthCore::Tracker ::emulation_ldp_control $args
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable ::sth::Ldp::emulation_ldp_control\_user_input_args_array
        array unset ::sth::Ldp::emulation_ldp_control\_user_input_args_array
        array set ::sth::Ldp::emulation_ldp_control\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_ldp_control\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_ldp_control"
        
                
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_ldp_control \
                                                        ::sth::Ldp::emulation_ldp_control\_user_input_args_array \
                                                        ::sth::Ldp::emulation_ldp_control\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_ldp_control_user_input_args_array(mode)
        switch -exact $modeValue {
                start {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                stop {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                restart {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                }
                graceful_restart {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "                        
                }
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying LDP configuration: $msg"
        return $returnKeyedList 
    }
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        }
        if {!$cmdStatus} {
                return $returnKeyedList
        } else {
                keylset returnKeyedList status $::sth::sthCore::SUCCESS
                return $returnKeyedList                        
        }
}                                                                                                                
##Procedure Header
#
# Name:
#    sth::emulation_ldp_info
#
# Purpose:
#    Returns information about the LDP session.
#
# Synopsis:
#    sth::emulation_ldp_info
#         -handle <ldp_handle>
#         -mode   {state|stats|settings|lsp_labels}
#
# Arguments:
#    -handle
#                   The handle of the LDP session for which you want
#                   information.
#
#    -mode
#                   Specifies the kind of information you want to see.
#                   Possible values are state, stats, settings, and lsp_labels.
#                   You must specify a mode; there is no default.
#
# Return Values:
#         The sth::emulation_ldp_info function returns a keyed list using
#         the following keys (with corresponding data):
#
#         state
#                   Returns the state of an LSR and a summary of LSPs configured
#                   on each LSR (see list below). This is a Spirent-added key.
#
#         stats
#                   Retrieves the IP address of the specified port and the
#                   number of messages transmitted and received (see list
#                   below).
#
#         settings
#                   Retrieves the IP address of the specified port and the
#                   configuration settings for the LDP session (see list
#                   below).
#
#         lsp_labels
#                   Retrieves the list of LSP labels, information about
#                   them, and their FEC type (see list below).
#
#         status    Retrieves a value indicating the success (1) or failure
#                   (0) of the operation.
#
#         log       Retrieves a message describing the last error that
#                   occurred during the operation. If the operation was
#                   successful - {status 1} - the log value is null
#
#
#    The following keys are returned when you specify "-mode state":
#
#         session_state
#                        State of the LDP router:
#
#                        LDP_SESSION_STATE_NO_ STATE ------ >nonexist
#                        LDP_SESSION_STATE_DOWN  -----> init
#                        LDP_SESSION_STATE_UP -----> operational
#                        LDP_SESSION_STATE_FAILED -----> disabled
#                        LDP_SESSION_STATE_OPEN ------> opensent
#                        LDP_SESSION_STATE_CONNECT -----> openrec
#
#         num_incoming_ingress_lsps
#                        Specifies number of opened ingress LSPs.
#
#         num_incoming_egress_lsps
#                        Specifies number of opened egress LSPs.
#
#         lsp_pool_handle
#                        Specifies LSP handles.
#
#         type
#                        Type of LSP: egress or ingress.
#
#         num_opened_lsps
#                        Specifies number of opened LSPs.
#
#    The following keys are returned when you specify "-mode stats":
#
#         routing_protocol    Not supported in Spirent HLTAPI.
#
#         elapsed_time        Time in seconds measured when the router
#                             session is started until the time the
#                             statistics are retrieved or when the router
#                             session has stopped.
#
#         ip_address          IP address of the port on the interface card.
#
#         linked_hellos_tx    Number of direct HELLO messages sent.
#
#         linked_hellos_RX    Number of direct HELLO messages received.
#
#         targeted_hellos_tx  Number of targeted HELLO messages sent.
#
#         targeted_hellos_RX  Number of targeted HELLO messages received.
#
#         total_setup_time    Not supported in Spirent HLTAPI.
#
#         min_setup_time      Not supported in Spirent HLTAPI.
#
#         max_setup_time      Not supported in Spirent HLTAPI.
#
#         num_lsps_setup      Number of LSPs configured on the LDP session.
#
#         req_rx              Number of label requests received.
#
#         req_tx              Number of label requests sent.
#
#         map_rx              Number of label mappings sent.
#
#         map_tx              Number of label mappings received.
#
#         release_rx          Number of label release received.
#
#         release_tx          Number of label release sent.
#
#         withdraw_rx         Number of label withdraws received.
#
#         withdraw_tx         Number of label withdraws sent.
#
#         abort_rx            Number of label aborts received.
#
#         abort_tx            Number of label aborts sent.
#
#         notif_rx            Number of notifications received.
#
#         notif_tx            Number of notifications sent.
#
#
#    The following keys are returned when you specify "-mode settings":
#
#         intf_ip_address
#                             IP address of the port on the interface card:
#                             a.b.c.d.
#
#         label_type
#                             Not supported in Spirent HLTAPI.
#
#         transport_address
#                             Not supported in Spirent HLTAPI.
#
#         targeted_hello
#                             Not supported in Spirent HLTAPI.
#
#         label_adv
#                             Specified type of label advertisement.
#                             Spirent HLTAPI always runs in unsolicited mode
#
#         loop_detection
#                             Not supported in Spirent HLTAPI.
#
#         hello_hold_time
#                             Not supported in Spirent HLTAPI.
#
#         hello_interval
#                             Number of seconds between HELLO messages.
#
#         keepalive_interval
#                             Number of seconds between KEEPALIVE messages.
#
#         keepalive_holdtime
#                             Not supported in Spirent HLTAPI.
#
#         path_vector_limit
#                             Not supported in Spirent HLTAPI.
#
#         max_pdu_length
#                             Not supported in Spirent HLTAPI.
#
#         label_space
#                             Not supported in Spirent HLTAPI.
#
#         vpi
#                             Not supported in Spirent HLTAPI.
#         vci
#                             Not supported in Spirent HLTAPI.
#
#         vc_direction
#                             Not supported in Spirent HLTAPI.
#
#         atm_merge_capability
#                             Not supported in Spirent HLTAPI.
#
#         fr_merge_capability
#                             Not supported in Spirent HLTAPI.
#
#         atm_range_min_vci
#                             Not supported in Spirent HLTAPI.
#
#         atm_range_max_vci
#                             Not supported in Spirent HLTAPI.
#
#         atm_range_min_vpi
#                             Not supported in Spirent HLTAPI.
#
#         atm_range_max_vpi
#                             Not supported in Spirent HLTAPI.
#
#    The following keys are returned when you specify "-mode lsp_labels":
#
#
#         source
#                             The list of LSP pool handles.
#
#         fec_type
#                             The list of FEC types belonging to each source.
#                             (The FEC type specified in the -fec_type
#                             argument for the sth::emulation_ldp_route_config
#                             function.)
#
#         prefix
#                             The list of prefixes belonging to each source.
#
#         prefix_length
#                             The list of prefix lengths belonging to each
#                             source
#
#         label
#                             The list of MPLS labels belonging to each source.
#
#
# Description:
#    The sth::emulation_ldp_info function provides information about
#    either the state of the LDP session, the settings specified for the LDP
#    configuration, the statistics returned by it, or the list of LSP labels.
#
#    This function returns the requested data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message. Function return values are formatted as a keyed list
#    (supported by the Tcl extension software - TclX). Use the TclX function
#    keylget to retrieve data from the keyed list. (See Return Values for a
#    description of each key.)
#
# Examples:
#
# Assume we already have the LDP router handle ldpSessionHnd
#         sth::emulation_ldp_info  \
#                   -mode stats  \
#                   -handle $ldpSessionHnd
#
#    Output:
#         {ip_address 41.1.0.2} {abort_rx 0.000000} {map_tx 5.000000} {abort_tx
#         0.000000}
#         {withdraw_rx 0.000000} {withdraw_tx 0.000000} {linked_hellos_rx
#         27.000000}
#         {targeted_hellos_rx 0.000000} {linked_hellos_tx 24.000000} {notif_rx
#         0.000000}
#         {targeted_hellos_tx 0.000000} {req_rx 0.000000} {release_rx 0.000000}
#         {notif_tx 0.000000} {req_tx 0.000000} {release_tx 0.000000} {map_rx
#         1774.000000} {elapsed_time 123.418951035} {num_lsps_setup 5} {status
#         1}
#
# Assume we already have the LDP router handle ldpSessionHnd
#    sth::emulation_ldp_info -mode state  -handle $ldpSessionHnd
#
#    Output:
#         {type egress} {session_state operational} {lsp_pool_handle
#         ipv4prefixlsp1} {num_incoming_ingress_lsps 0.000000} {num_opened_lsps
#         5.000000} {num_incoming_egress_lsps 5.000000} {status 1}
#
# Assume we already have the LDP router handle ldpSessionHnd
#    sth::emulation_ldp_info -mode lsp_labels -handle $ldpSessionHnd
#
#    Output:
#         {source {ldplspresults1 ldplspresults2 ldplspresults3 ldplspresults4
#         ldplspresults5}} {label {50 51 52 53 54}} {prefix_length {24 24 24 24
#         24}}  {prefix {10.0.0.0 10.0.1.0 10.0.2.0 10.0.3.0 10.0.4.0}}
#         {fec_type {ipv4_prefix ipv4_prefix ipv4_prefix ipv4_prefix
#         ipv4_prefix}} {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes: None
#
# End of Procedure Header
proc ::sth::emulation_ldp_info { args } {
        ::sth::sthCore::Tracker ::emulation_ldp_info $args
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable ::sth::Ldp::emulation_ldp_info\_user_input_args_array
        array unset ::sth::Ldp::emulation_ldp_info\_user_input_args_array
        array set ::sth::Ldp::emulation_ldp_info\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_ldp_info\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_ldp_info"
        
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"        
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_ldp_info \
                                                        ::sth::Ldp::emulation_ldp_info\_user_input_args_array \
                                                        ::sth::Ldp::emulation_ldp_info\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_ldp_info_user_input_args_array(mode)
        
        #Check if the value of ldp handle is valid
        ::sth::sthCore::log hltcall "__VALIDATE__: Validate value of handle"
        set msg ""
        
        switch -exact $modeValue {
                stats {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore\Generic {$args} returnKeyedList cmdStatus $modeValue"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                settings {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore\Generic {$args} returnKeyedList cmdStatus $modeValue"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                clear_stats {
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList
                } 
                state {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore\Generic {$args} returnKeyedList cmdStatus $modeValue"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                lsp_labels {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore\Generic {$args} returnKeyedList cmdStatus $modeValue"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        }
        if {!$cmdStatus} {
                return $returnKeyedList
        } else {
                keylset returnKeyedList status $::sth::sthCore::SUCCESS
                return $returnKeyedList                        
        }
}                                                        
##Procedure Header
#
# Name:
#    sth::emulation_ldp_route_config
#
# Purpose:
#    Creates, modifies, or deletes Link State Path (LSP) pools or Forwarding
#    Equivalent Class (FEC) ranges on an emulated Label Switched Router
#    (LSR) on a Spirent HLTAPI chassis.
#
# Synopsis:
#    sth::emulation_ldp_route_config
#         { [-mode create -handle <ldp_handle>] |
#           [-mode [modify|delete]
#                  -lsp_handle <lsp_handle> ] }
#         [-num_lsps <integer>]
#         [-label_msg_type {mapping|request}]
#         { [-fec_type ipv4_prefix
#                   -fec_ip_prefix_length <1-32>
#                   -fec_ip_prefix_start <a.b.c.d.>
#                   -fec_ip_prefix_step <integer>]  |
#            [-fec_type host_addr
#                   -fec_host_addr <a.b.c.d>
#                   -fec_host_step <integer> ] |
#            [-fec_type vc
#                   -fec_vc_cbit {0|1}
#                   -fec_vc_group_id <0 to 0xFFFFFFFFF>
#                   -fec_vc_id_start <0 to 0xFFFFFFFFF>
#                   -fec_vc_id_step <integer>
#                   -fec_vc_intf_mtu <integer>
#            ]
#          }
#
# Arguments:
#
#    -fec_host_addr
#                   The first host address to be advertised. You must specify
#                   -fec_type with this argument. The default is 192.0.1.0.
#
#    -fec_host_step
#                   The amount by which the host address to be advertised should
#                   be increased. The default is 1. You must specify -fec_type
#                   host_addr with this argument. When -num_lsps is greater than
#                   1, you must also specify this argument.
#
#    -fec_ip_prefix_length
#                   The prefix length for the IPv4-prefix FEC range to be
#                   advertised. Possible values are from 1 to 32. The default is
#                   24. You must specify -fec_type ipv4_prefix with this
#                   argument.
#
#    -fec_ip_prefix_start
#                   The first prefix to be advertised in the IPv4-prefix FEC
#                   range. The default is 192.0.1.0. You must specify -fec_type
#                   ipv4_prefix with this argument.
#
#    -fec_ip_prefix_step
#                   The amount by which the prefix to be advertised should
#                   be increased. The default is 1. You must specify -fec_type
#                   ipv4_prefix with this argument. When -num_lsps is greater 
#                   than 1, you must also specify this argument.
#
#    -fec_type
#                   The type of FEC element to use. Valid types are:
#
#                   ipv4_prefix -  Configure FECs to be advertised by the
#                                  emulated LSR. This is the default value.
#
#                   host_addr -    Configure FECs to be advertised by a single
#                                  host
#
#                   vc             Indicates a virtual circuit ID with a label
#                                  assigned to it. You cannot modify this option
#                                  with -mode modify.
#
#    -fec_vc_cbit   Enables the generation of a control bit in the VC. Possible
#                   values are 0 (disable) and 1 (enable). The default is 0
#                   (disabled). You must specify -fec_type vc with this
#                   argument.
#
#    -fec_vc_group_id
#                   The group ID associated with all VC FEC elements for this
#                   interface. Possible values range from 0 to 0xFFFFFFFFF. The
#                   default is 0. You must specify -fec_type vc with this
#                   argument.
#
#    -fec_vc_id_start
#                   The virtual circuit ID, together with the value of the
#                   fec_vc_type option, identifies a unique VC.Possible values
#                   range from 0 to 0xFFFFFFFFF. The default is 1. You must
#                   specify -fec_type vc with this argument.
#
#    -fec_vc_id_step
#                   The step value applied between uses of VC ID. The default is
#                   1. You must specify -fec_type vc with this argument.
#
#    -fec_vc_intf_mtu
#                   The size of the interface MTU (maximum transmission unit),
#                   in bytes, for the vc. The default is 1500. You must specify
#                   "-fec_type vc" with this argument.
#
#    -fec_vc_intf_mtu_enable
#                    Not supported in Spirent HLTAPI. VC Fec mtu are always 
#                    supported in Spirent HLTAPI
#
#    -fec_vc_type   The type of virtual circuit used. Valid values are:
#
#                   none - Do not use a virtual circuit
#                   fr_dlci - Frame Relay DLCI
#                   eth_vlan - Ethernet VLAN (This is the default value.)
#                   eth  - Ethernet
#                   hdlc - HDLC
#                   ppp  - PPP
#                   cem  - CEM
#                   eth_vpls - Ethernet VPLS
#
#    -handle        Identifies the router on which to create, modify, or
#                   delete LSP (FEC) pools or FEC ranges. This argument is
#                   required. The value is alphanumeric.
#
#    -label_msg_type
#                   Type of label messages to send. Valid values are:
#
#                   mapping - Use message to advertise egress bindings to UUT.
#                        This is the default value.
#
#                   request - Use message to request ingress label bindings from
#                        UUT for an on_demand mode. You cannot modify this
#                        option with -mode modify.
#
#    -lsp_handle    Specifies the LSP for which to configure the LSP pools and
#                   FEC range options. This argument is required for modify
#                   and delete modes, but not for create mode. When you use
#                   -mode create, Spirent HLTAPI will return a handle for
#                   the newly created LSP.
#
#    -mode
#                   Specifies whether to create, modify, or delete LSPs
#                   from the emulated router's LSR database. Possible values
#                   are:
#
#                   create - Creates a new LSP for the LDP session. The handle
#                        for the LSP is returned in the lsp_handle key (see
#                        Return Values).
#
#                   modify - Modifies the setup for the LSP specified in the
#                        -lsp_handle argument.
#
#                   delete - Removes the LSP specified in the -lsp_handle
#                        argument.
#
#    -num_lsps      The number of label bindings to be advertised. The default
#                   is 1. When -num_lsps is greater than 1, you must also
#                   specify the -fec_host_step, and  -fec_ip_prefix_step 
#                   arguments.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -egress_label_mode
#    -fec_vc_intf_desc
#    -fec_vc_intf_mtu_enable
#    -hop_count_tlv_enable
#    -hop_count_value
#    -path_vector_tlv
#    -path_vector_tlv_lsr
#
# Return Values:
#    The function returns a keyed list using the following keys:
#    (with corresponding data):
#
#    lsp_handle
#              The handle that identifies the LSP created by the
#              sth::emulation_ldp_route_config function.
#
#    status
#              Success (1) or failure (0) of the operation.
#
#    log
#              An error message (if the operation failed).
#
# Description:
#    The sth::emulation_ldp_route_config function creates and
#    configures LSPs. Use the -lsp_handle argument to identify the router
#    for which to create, modify, or delete an LSP. (The router handle value is
#    contained in the keyed list returned by the sth::emulation_ldp_config
#    function.) Use the -mode argument to specify the action to perform. See the
#    -mode argument for a description of the actions.
#
#    FEC is a group of IP packets which are forwarded in the same way, over the
#    same path, and with the same forwarding treatment. An FEC (Forwarding
#    Equivalence Class) is associated with each LSP created. The FEC specifies
#    which packets are mapped to that LSP.
#
# Examples:
#
# Assume we already have the LDP router handle ldpRouterHandle
#    sth::emulation_ldp_route_config -mode create \
#                                    -handle $ldpRouterHandle \
#                                    -fec_type vc \
#                                    -fec_vc_cbit 1 \
#                                    -fec_vc_group_id 77 \
#                                    -fec_vc_id_start 7 \
#                                    -fec_vc_id_step 7 \
#                                    -fec_vc_intf_mtu 1200 \
#                                    -fec_vc_type eth_vlan \
#                                    -label_msg_type request \
#                                    -num_lsps 2
#
#
#    The following example creates an LSP pool with two LSPs in it on the
#    LDP router (ldpRouterHandle) on port1:
#
#   sth::emulation_ldp_route_config -mode create \
#                                   -handle $ldpRouterHandle \
#                                   -num_lsps 2  \
#                                   -fec_type ipv4_prefix  \
#                                   -fec_ip_prefix_step 1 \
#                                   -fec_ip_prefix_length 24 \
#                                   -fec_ip_prefix_start 32.25.0.0
#
#    Output:    {lsp_handle ipv4prefixlsp1} {status 1}
#
# Sample Input:
#
# Sample Output:
#
# Notes: None
#
# End of Procedure Header
proc ::sth::emulation_ldp_route_config { args } {
        ::sth::sthCore::Tracker ::emulation_ldp_route_config $args

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable ::sth::Ldp::emulation_ldp_route_config\_user_input_args_array
        array unset ::sth::Ldp::emulation_ldp_route_config\_user_input_args_array
        array set ::sth::Ldp::emulation_ldp_route_config\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_ldp_route_config\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_ldp_route_config"
          
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"
        #::sth::sthCore::log hltcall "Excuting command: {$_hltCmdName $args}"
        #eval ::Bgp::emulation_bgp_config_ParseArguments {$args}
        #fec_host_addr, fec_host_step, fec_host_prefix_length are not suggest to use,, will map these to fec_ip_prefix_start, fec_ip_prefix_step, fec_ip_prefix_length
        set switchIndex [lsearch $args "-fec_host_addr"]
        if {$switchIndex > -1 } {
            set args [lreplace $args $switchIndex $switchIndex "-fec_ip_prefix_start"]
        }
        set switchIndex [lsearch $args "-fec_host_step"]
        if {$switchIndex > -1 } {
            set args [lreplace $args $switchIndex $switchIndex "-fec_ip_prefix_step"]
        }
        set switchIndex [lsearch $args "-fec_host_prefix_length"]
        if {$switchIndex > -1 } {
            set args [lreplace $args $switchIndex $switchIndex "-fec_ip_prefix_length"]
        }
        #when lsp_type is pwid, "num_lsps" should be mapped to fec_vc_id_count if there is no fec_vc_id_count
        set switchIndex [lsearch $args "-lsp_type"]
        if {$switchIndex > -1 } {
            set lsp_type [lindex $args [expr $switchIndex + 1]]
            if {$lsp_type == "pwid"} {
                set num_lsps_index [lsearch $args "-num_lsps"]
                set fec_vc_id_count_index [lsearch $args "-fec_vc_id_count"]
                if {$num_lsps_index > -1} {
                    if {$fec_vc_id_count_index == -1} {
                        set args [lreplace $args $num_lsps_index $num_lsps_index "-fec_vc_id_count"]
                    } else {
                        set args [lreplace $args $num_lsps_index [expr $num_lsps_index + 1] ""]
                    }
                }
            }
        }
        set num_lsps_index [lsearch $args "-num_lsps"]
        set num_routes_index [lsearch $args "-num_routes"]
        if {$num_lsps_index > -1} {
            if {$num_routes_index == -1} {
                set args [lreplace $args $num_lsps_index $num_lsps_index "-num_routes"]
            } else {
                set args [lreplace $args $num_lsps_index [expr $num_lsps_index + 1]]
            }
        }
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_ldp_route_config \
                                                        ::sth::Ldp::emulation_ldp_route_config\_user_input_args_array \
                                                        ::sth::Ldp::emulation_ldp_route_config\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(mode)
        
        switch -exact $modeValue {
                create {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                modify {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                delete {
                        set cmdStatus 0
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList cmdStatus"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        }
        if {!$cmdStatus} {
                return $returnKeyedList
        } else {
                keylset returnKeyedList status $::sth::sthCore::SUCCESS
                return $returnKeyedList                        
        }
}


proc ::sth::emulation_lsp_switching_point_tlvs_config { args } {
        ::sth::sthCore::Tracker ::emulation_lsp_switching_point_tlvs_config $args

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_user_input_args_array
        array unset ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_user_input_args_array
        array set ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_lsp_switching_point_tlvs_config"
          
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_lsp_switching_point_tlvs_config \
                                                        ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_user_input_args_array \
                                                        ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(mode)
        
        switch -exact $modeValue {
                create {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                modify {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                delete {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        } else {
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return $returnKeyedList
        }

}

proc ::sth::emulation_ldp_route_element_config { args } {
        ::sth::sthCore::Tracker ::emulation_ldp_route_element_config $args

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable ::sth::Ldp::emulation_ldp_route_element_config\_user_input_args_array
        array unset ::sth::Ldp::emulation_ldp_route_element_config\_user_input_args_array
        array set ::sth::Ldp::emulation_ldp_route_element_config\_user_input_args_array {}
        
        variable ::sth::Ldp::emulation_ldp_route_element_config\_sortedSwitchPriorityList
        
        set _hltCmdName "emulation_ldp_route_element_config"
          
        set returnKeyedList ""
        set underScore "_"
        
        ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"
        
        ::sth::sthCore::commandInit ::sth::Ldp::LdpTable $args \
                                                        ::sth::Ldp:: \
                                                        emulation_ldp_route_element_config \
                                                        ::sth::Ldp::emulation_ldp_route_element_config\_user_input_args_array \
                                                        ::sth::Ldp::emulation_ldp_route_element_config\_sortedSwitchPriorityList
                                                        
        #switch to call processing functions for the mode of emulation_bgp_config        
        set modeValue $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(mode)
        
        switch -exact $modeValue {
                create {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                modify {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                delete {
                        set cmd "::sth::Ldp::$_hltCmdName$underScore$modeValue {$args} returnKeyedList"
                        ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
                } 
                default {
                        #Unknown value for switch Mode.
                        ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
                        return $returnKeyedList                 
                }
        }
        ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
        if {[catch {set procResult [eval $cmd]} eMsg]} { 
                ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
                return $returnKeyedList
        } else {
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return $returnKeyedList
        }

}

