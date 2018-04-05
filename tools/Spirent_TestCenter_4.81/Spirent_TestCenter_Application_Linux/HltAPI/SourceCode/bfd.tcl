namespace eval ::sth {

}
#
##Procedure Header
#
# Name:
#    sth::emulation_bfd_config
#
# Purpose:
#    Creates, enables, modifies, disables,or deletes an emulated Bidirectional Forwarding
#    Detection  (BFD) router on a Spirent TestCenter chassis.
#
#   BFD is a fast hello protocol which can be used by any protocol needing a faster method
#   of detecting link failures.BFD can be used by any routing protocol to detect loss of
#   connectivity with a neighbor that has gone done.BFD can also be used to detect data
#   plane failure in tunnel based protocols which traverse multiple hops.
#
#    Spirent TestCenter supports BFD router dependent form routing protocol (dymantic BFD)
#    or BFD router independent form routing protocol (static BFD)
#
# Synopsis:
#    sth::emulation_bfd_config
#         { [-mode create -port_handle <port_handle> |
#            -mode {enable|modify|disable|delete}
#                  -handle <BFD_handle> ] }
#         [-count <integer>]
#         [-ip_version {IPv4|IPv6}]
#         [-local_mac_addr <aa:bb:cc:dd:ee:ff>]
#               [-local_mac_addr_step <aa:bb:cc:dd:ee:ff>]
#         [-intf_ip_addr <a.b.c.d>]
#               [-intf_ip_addr_step <a.b.c.d>]
#         [-intf_ipv6_addr <a:b:c:d:e:f:g:h>]
#               [-intf_ipv6_addr_step <a:b:c:d:e:f:g:h>]
#         [-gateway_ip_addr <a.b.c.d>]
#               [-gateway_ip_addr_step {<a.b.c.d>]
#         [-gateway_ipv6_addr <a:b:c:d:e:f:g:h>]
#               [-gateway_ipv6_addr_step <a:b:c:d:e:f:g:h>]
#         [-vlan_id1 <0-4096>]
#               [-vlan_id_mode1 {fixed|increment}]
#               [-vlan_id_step1 <0-4096>]
#         [-vlan_id2 <0-4096>]
#               [-vlan_id_mode2 {fixed|increment}]
#               [-vlan_id_step2 <0-4096>]
#         [-vci <0-65535>]
#               [-vci_step <0-65535>]
#         [-vpi <0-255>]
#               [-vpi_step <0-255>]
#         [-session_discriminator <integer>]
#               [-session_discriminator_step <integer>]
#         [-detect_multiplier <2-100>]
#         [-echo_rx_interval <0-10000>]
#         [-active_mode {active|passive}]
#
# Arguments:
#     -mode
#                      Specifies the action to be performed. Possible values
#                      are create, enable, modify, disable and delete. The modes
#                      are described below:
#
#                      create - Creates one or more emulated BFD router. Use
#                           the -port_handle argument specify and additional
#                           arguments to supply address information for
#                           the emulated routers.
#
#                      modify - Changes the configuration for the BFD router
#                          specified in the -handle argument.
#
#                      enable - Same as description for "create"
#
#                      delete - Deletes the BFD router specified in the -handle
#                          argument.
#
#                      diable - Same as description for "delete"
#
#    -port_handle
#                      Specifies the port on which to create the BFD router. This
#                      argument is mandatory for create mode (-mode create).
#
#    -handle
#                      Specifies the BFD handle(s) to use when mode is set to
#                      modify, delete, or disable. This argument is not
#                      valid for create or enable mode. Instead, use -port_handle.
#
#    -count
#                      Defines the number of BFD routers to create on the
#                      interface. The default is 1.
#
#    -ip_version
#                      Specifies the IP version of the BFD emulated router.
#                      Possible values are IPv4 and IPv4. The default value
#                      is IPv4
#
#    -local_mac_addr
#                      Defines local MAC address.
#
#    -local_mac_addr_step
#                      Defines local MAC address step. You must specify
#                      the mac address step when the -count argument
#                      is greater than 1.
#
#    -intf_ip_addr
#                      Defines the tester IP address for BFD IPv4 session pool.
#                      The value should be in IPv4 format.
#
#    -intf_ip_addr_step
#                      Defines the step size in which the tester IP address
#                      is incremented.You must specify the ipv4 address
#                      step when the -count argument is greater than 1.
#                      The value should be in IPv4 format.
#
#    -intf_ipv6_addr
#                      Defines the tester IP address for BFD IPv6 session pool.
#                      The value should be in IPv6 format.
#
#    -intf_ipv6_addr_step
#                      Defines the step size in which the tester IP address
#                      is incremented.You must specify the ipv6 address
#                      step when the -count argument is greater than 1.
#                      The value should be in IPv6 format.
#
#    -gateway_ip_addr
#                      Defines the gateway IP address for BFD IPv4 session pool. The
#                      default is 192.85.1.1.
#
#    -gateway_ip_addr_step
#                      Defines the step size in which the gateway IP address
#                      is incremented.You must specify the gateway address
#                      step when the -count argument is greater than 1.
#                      The value should be in IPv4 format.
#
#    -gateway_ipv6_addr
#                      Defines the gateway IP address for BFD IPv6 session pool.
#                      The default is 2000::1.
#
#    -gateway_ipv6_addr_step
#                      Defines the step size in which the tester IP address
#                      is incremented.You must specify the gateway address
#                      step when the -count argument is greater than 1.
#                      The value should be in IPv6 format.
#
#    -vlan_id1
#                      The VLAN ID of the first VLAN sub-interface. Possible values
#                   range from 0 to 4096. The default is 1.
#
#    -vlan_id_mode1
#                      Defines mode of Inner Vlan Id.Possible values are fixed and increment.
#                      If you set this argument to "increment," then you must also
#                      specify the -vlan_id_step argument to indicate the step size.
#                      The default is "fixed".
#
#    -vlan_id_step1
#                      Defines step to increment Inner Vlan Id.Possible values range
#                      from 0 to 4096.You should specify inner vlan id step if "vlan_id_mode1"
#                      argument is set to "increment".
#    -vlan_id2
#                      The VLAN ID of the second VLAN sub-interface. Possible
#                      values range from 0 to 4096. The default is 1.
#
#    -vlan_id_mode2
#                      Defines mode of Outer Vlan Id.Possible values are fixed and increment.
#                      If you set this argument to "increment," then you must also
#                      specify the -vlan_id_step argument to indicate the step size.
#                      The default is "fixed".
#
#    -vlan_id_step2
#                      Defines step to increment Outer Vlan Id.Possible values range
#                      from 0 to 4096.You should specify inner vlan id step if "vlan_id_mode2"
#                      argument is set to "increment".
#
#    -vci
#                      Defines the VCI of the first ATM PVC pool.Possible values range
#                      from 0 to 65535.
#
#    -vci_step
#                      Defines the step size in which the VCI value is incremented.
#                      Possible values range from 0 to 65535.
#
#    -vpi
#                      Defines the VPI of the first ATM PVC pool. Possible values
#                      range from 0 to 255.
#
#    -vpi_step
#                      Defines the step size in which the VPI value is incremented.
#                      Possible values range from 0 to 255.
#
#    -session_discriminator
#                      Defines BFD session discriminator value.
#
#    -session_discriminator_step
#                     Defines BFD session discriminator step value.You must specify
#                     the session discriminator step when the -count argument
#                     is greater than 1.
#
#    -detect_multiplier
#                     Defines the value by which the negotiated transmit interval
#                     multiplied to give the detection time for this session.Possible
#                     values range from 2-100.Default value is 2.
#
#    -echo_rx_interval
#                     Defines the minimum interval, in microseconds, between received
#                     BFD Echo packets that this system is capable of supporting.
#                     If this value is zero, the transmitting system does not support
#                     the receipt of BFD Echo packets.Possible values range from 0 to 10000.
#                     The default value is 0.
#
#    -active_mode
#                     Defines whether or not this BFD session should actively attempt to
#                     establish a connection.Possible values are active and passive.
#                     The modes are described below:
#
#                     active - send BFD Control packets for BFD session, regardless of whether
#                         it has received any BFD packets.
#                     passive - must not begin sending BFD paceket for BFD session until it has
#                         received a BFD packet.
#                     The default value is active.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent TestCenter 2.30.
#
#    -control_interval
#    -pkts_per_control_interval
#    -hop_mode
#    -poll_interval
#    -reset
#    -encap_type
#    -vlan_ether_type1
#    -vlan_ether_type2
#    -remote_mac_addr
#    -remote_mac_addr_step
#    -dlci
#    -remote_ip_addr
#    -remote_ip_addr_step
#    -remote_ipv6_addr
#    -remote_ipv6_addr_step
#    -remote_discriminator
#    -remote_discriminator_step
#    -echo_bit
#    -echo_timeout
#    -echo_tx_interval
#    -flap_tx_interval
#    -performance_mode
#
#
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#   handle
#                   The handle(s) of the BFD router returned by the
#                   sth::emulation_bfd_config function when you use -mode
#                   create to create a new BFD router. When you want to modify
#                   or delete the BFD router, you specify the handle as the
#                   value to the -handle argument.
#   status
#                   Success (1) or failure (0) of the operation.
#   log
#                   An error message (if the operation failed).
#
#
# Description:
#    The sth::emulation_bfd_config function creates, enables,
#    modifies, deletes, or disables an emuloated BFD router. Use the -mode
#    argument to specify the action to perform. (See the -mode argument
#    description for information about the actions.)
#
#    When you create an BFD emulated router, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated router will use for
#    BFD communication. (The port handle value is contained in the keyed list
#    returned by the connect function.)
#
#    In addition to specifying the port handle (-port_handle), you must also
#    provide the following arguments when you create a BFD router:
#
#    -mode create
#
#    -intf_ip_addr
#
#    -gate_way_addr
#
#    -local_mac_addr
#
#    When you create a BFD router, Spirent HLTAPI creates the router in
#    memory and downloads the configuration to the card. To start the router,
#    use the sth::emulation_bfd_control function with -mode start.
#
#    Once you start sessions, Spirent HLTAPI handles all of the message
#    traffic for the emulated routers. During the test, use the
#    sth::emulation_bfd_control function to stop,suspend,resume and flap
#    routers.
#
# Examples:
#    The following example creates a BFD router on the specified port:
#
#       sth::emulation_bfd_config -port_handle $hltSourcePort \
#                               -mode create \
#                               -count 1 \
#                               -local_mac_addr 00:10:94:00:00:05 \
#                               -local_mac_addr_step 00:00:00:00:00:01 \
#                               -intf_ip_addr 23.24.3.3 \
#                               -intf_ip_addr_step 0.0.0.3 \
#                               -gateway_ip_addr 23.24.3.1 \
#                               -gateway_ip_addr_step 0.0.0.1 \
#                               -vlan_id1 100 \
#                               -vlan_id_mode1 fixed \
#                               -vlan_id2 120 \
#                               -vlan_id_mode2 fixed \
#                               -detect_multiplier 3 \
#                               -echo_rx_interval 10 \
#                               -active_mode active \
#                               -session_discriminator 80 \
#                               -session_discriminator_step 10]
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
proc ::sth::emulation_bfd_config {args} {

    variable ::sth::bfd::sortedSwitchPriorityList
    array unset ::sth::bfd::userArgsArray
    array set ::sth::bfd::userArgsArray {}

    set returnKeyedList ""

    set retVal [catch {
        ::sth::sthCore::Tracker emulation_bfd_config $args
        if {[catch {::sth::sthCore::commandInit \
            ::sth::bfd::bfdTable \
            $args \
            ::sth::bfd:: \
            emulation_bfd_config \
            ::sth::bfd::userArgsArray \
            sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
                return $returnKeyedList        }

        switch -exact -- $::sth::bfd::userArgsArray(mode) {
            "create" -
            "enable" {
                ::sth::bfd::emulation_bfd_config_create returnKeyedList
            }
            "modify" {
                ::sth::bfd::emulation_bfd_config_modify returnKeyedList
            }
            "delete" -
            "disable" {
                ::sth::bfd::emulation_bfd_config_delete returnKeyedList
            }
            default {
               # Unsupported mode
                ::sth::sthCore::processError returnKeyedList "Error: Unsupported -mode value $::sth::bfd::userArgsArray(mode)" {}
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
#    sth::emulation_bfd_control
#
# Purpose:
#    Starts, stops, suspends ,resumes or flap BFD routers.
#
# Synopsis:
#    sth::emulation_bfd_control
#         -handle <bfd_router_handle>
#         -mode {stop | start | suspend | resume | flap}
#         -port_handle <port_handle>
#         -flap_count <integer>
#         -flap_interval <integer>
#
# Arguments:
#
#    -handle
#                   Identifies the router handle, returned from the
#                   emulation_bfd_config function when creating a BFD router.
#                   The router handle value is alphanumeric.
#                   One of the two parameters is required: port_handle/handle.
#
#
#    -port_handle
#                   Identifies the port on which to stop, start, suspend or resume the
#                   routers.One of the two parameters is required: port_handle/handle.
#
#    -mode
#                   Specifies the action to be taken. Possible values are
#                   stop, start, suspend or resume , This argument is required.
#
#                   stop - Stops the router with the specified handle.
#
#                   start - Starts the router with the specified handle.
#
#                   flap - Stops sending/responding for the specific flap_interval
#
#                   suspend - Suspends the routers with the specified handle.
#
#                   resume - Resume the router with the specified handle.
#
#                   Note: The "no_shut" and "shut" options are not
#                   supported.
#
#    -flap_count    Specifies the number of flaps, each flap includes
#                   one suspend and one resume.You should and can only specify
#                   "flap_count" when mode is "flap".
#
#    -flap_interval  Specifies the BFD flap interval time.
#                    You should ans can only specify "flap_count" when mode is "flap".
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.30.
#
#    -mode {no_shut | shut}
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
#    The sth::emulation_bfd_control function controls the starting,
#    stopping , suspending and resuming of BFD routers.
#
# Examples:
#    To start a BFD router:
#
#         sth::emulation_bfd_control -mode start -handle $bfdRouterHandle
#
#   To start all routers on the specified port:
#
#         sth::emulation_bfd_control -mode start -port_handle $port1
#
#    To stop a BFD router:
#
#         sth::emulation_bfd_control -mode stop -handle $bfdRouterHandle
#
#    To flap a BFD router:
#
#        sth::emulation_bfd_control -mode flap -handle $bfdRouterHandle
#
#    To suspend a BFD router:
#
#         sth::emulation_bfd_control -mode suspend -handle $bfdRouterHandle
#
#    To resume a BFD router:
#
#         sth::emulation_bfd_control -mode resume -handle $bfdRouterHandle
#
# Sample Input: See Examples.
#
# Sample Output:  {status 1}
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bfd_control {args} {
    variable ::sth::bfd::sortedSwitchPriorityList
    array unset ::sth::bfd::userArgsArray
    array set ::sth::bfd::userArgsArray {}
    set returnKeyedList ""

    set retVal [catch {
        ::sth::sthCore::Tracker emulation_bfd_control $args
        if {[catch {::sth::sthCore::commandInit \
            ::sth::bfd::bfdTable \
            $args \
            ::sth::bfd:: \
            emulation_bfd_control \
            ::sth::bfd::userArgsArray \
            sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError trafficStatsKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
                return $trafficStatsKeyedList
            }

        if {(![info exists ::sth::bfd::userArgsArray(port_handle)])
            && (![info exists ::sth::bfd::userArgsArray(handle)])} {
                ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
                return -code error $returnKeyedList
            }

        if {([info exists ::sth::bfd::userArgsArray(port_handle)])
            && ([info exists ::sth::bfd::userArgsArray(handle)])} {
                ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle or -handle are mutually exclusive." {}
                return -code error $returnKeyedList
            }


        set rtrHandleList ""
        if {([info exists ::sth::bfd::userArgsArray(handle)])
            && (![info exists ::sth::bfd::userArgsArray(port_handle)])} {
            foreach handle $::sth::bfd::userArgsArray(handle) {
                if {![::sth::bfd::IsBfdRouterHandleValid $handle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $handle is not a valid BFD router handle" {}
                    return -code error $returnKeyedList
                }
            }
            set rtrHandleList $::sth::bfd::userArgsArray(handle)
        } elseif {([info exists ::sth::bfd::userArgsArray(port_handle)])
            && (![info exists ::sth::bfd::userArgsArray(handle)])} {

            if {[::sth::sthCore::IsPortValid $::sth::bfd::userArgsArray(port_handle) err]} {
                 set rtrHandleList [::sth::sthCore::invoke stc::get $::sth::bfd::userArgsArray(port_handle) -affiliationport-sources]
            } else {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::bfd::userArgsArray(port_handle)" {}
                return -code error $returnKeyedList
            }
        }

        switch -exact -- $::sth::bfd::userArgsArray(mode) {
            "start" {
                ::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $rtrHandleList
            }
            "stop" {
                ::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $rtrHandleList
            }
            "flap" {
                ::sth::bfd::emulation_bfd_flap returnKeyedList $rtrHandleList
            }
            "stop_pdus" -
            "resume_pdus" -
            "admin_up" -
            "admin_down" -
            "enable_demand" -
            "disable_demand" -
            "initiate_poll" {
                ::sth::bfd::emulation_bfd_common_control returnKeyedList $rtrHandleList
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error:  Unsupported BFD control mode $::sth::bfd::userArgsArray(mode)." {}
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
#    sth::emulation_bfd_info
#
# Purpose:
#    Returns information about the BFD configuration.
#
# Synopsis:
#    sth::emulation_bfd_info
#         -handle <bfd_router_handle>
#         -mode   {aggregate_stats| learned_info}
#         -port_handle <port_handle>
#
# Arguments:
#      -handle
#                   The BFD router for which you want information.
#                   One of the two parameters is required: port_handle/handle.
#
#      -mode
#                   Specifies the kind of information you want to see. Possible
#                   values are stats and settings.
#
#                   aggregate_stats  - returns stats aggregated per port
#
#                   learned_info - returns learned information by the BFD protocol
#
#                   Note: The "clear_stats" options are not supported.
#
#    -port_handle
#                    The port for which you want information.
#                   One of the two parameters is required: port_handle/handle.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.30.
#
#    -mode   {clear_stats}
#
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         learned_info   Retrieves learned information by the BFD protocol (see list below).
#
#         aggregate_stats   Retrieves stats aggregated per port (see list below).
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null
#
#    The following keys are returned when you specify -mode learned_info:
#
#      -packet_tx
#                   Retrieves BFD packets transmitted.
#
#      -packet_rx
#                   Retrieves BFD packets received.
#
#      -min_intr_arriv
#                   Retrieves Minimum inter-arrival time of received BFD packets.
#                   This value is not updated when session is not in Up state.
#
#      -to_down_state
#                   State changes to Down state.
#
#      -to_up_state
#                   State changes to Up state.
#
#         Note: The following keys are not supported when you specify -mode learned_info:
#               packet_dr
#               pool_rx
#               final_rx
#               echo_rx
#               avg_intr_arriv
#               max_intr_arriv
#               pool_tx
#               final_tx
#               echo_tx
#               avg_intr_dept
#               min_intr_dept
#               max_intr_dept
#               to_admin_down_state
#               to_init_state
#
#    The following keys are returned when you specify -mode aggregate_stats:
#
#
#
#       Note: The following keys are not supported when you specify -mode aggregate_stats:
#               routers_configured
#               routers_running
#               control_pkts_tx
#               control_pkts_tx
#               echo_self_pkts_tx
#               echo_self_pkts_rx
#               echo_dut_pkts_tx
#               echo_dut_pkts_rx
#               sessions_configured
#               sessions_auto_created
#               sessions_configured_up
#               sessions_auto_created_up
#
# Description:
#    The sth::emulation_bfd_info function provides information about
#    the settings specified for the BFD configuration, the statistics
#    returned by it
#
#    This function returns the requested data (learned_info, aggregate_stats)
#    and a status value (1 for success). If there is an error, the
#    function returns the status value (0) and an error message. Function return
#    values are formatted as a keyed list (supported by the Tcl extension
#    software - TclX). Use the TclX function keylget to retrieve data from the
#    keyed list. (See Return Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input: sth::emulation_bfd_info -mode learned_info -handle router1
#
# Sample Output: {bfd_session_state DOWN} {packet_rx 0} {to_down_state 1} {packet_tx 21} {min_intr_arriv 30} {to_up_state 0} {status 1}
#
# Notes: None
#
# End of Procedure Header

proc ::sth::emulation_bfd_info {args} {
    variable ::sth::bfd::sortedSwitchPriorityList
    array unset ::sth::bfd::userArgsArray
    array set ::sth::bfd::userArgsArray {}
    set returnKeyedList ""

    set retVal [catch {
        ::sth::sthCore::Tracker emulation_bfd_info $args
        ::sth::sthCore::commandInit \
            ::sth::bfd::bfdTable \
            $args \
            ::sth::bfd:: \
            emulation_bfd_info \
            ::sth::bfd::userArgsArray \
            sortedSwitchPriorityList

        #validate BFD handle, either -handle or -port_handle is mandatory
        if {![info exists ::sth::bfd::userArgsArray(handle)] && ![info exist ::sth::bfd::userArgsArray(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute -handle or -port_handle." {}
            return -code error $returnKeyedList
        }

        if {[info exists ::sth::bfd::userArgsArray(handle)] && [info exist ::sth::bfd::userArgsArray(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: -handle and -port_handle are exclusive ." {}
            return -code error $returnKeyedList
        }
        if {[info exists ::sth::bfd::userArgsArray(handle)] && ![info exists ::sth::bfd::userArgsArray(port_handle)]} {
            set routers $::sth::bfd::userArgsArray(handle)
            set portHandle [::sth::sthCore::invoke stc::get $routers -AffiliationPort-targets]
        }

        if {![info exists ::sth::bfd::userArgsArray(handle)] && [info exists ::sth::bfd::userArgsArray(port_handle)]} {
            set portHandle $::sth::bfd::userArgsArray(port_handle)
            set routers [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
        }

        if {($::sth::bfd::userArgsArray(mode) eq "bfd_stats")} {
            set bfdRouterConfigHanList ""
            foreach routerHandle $routers {
                if {![::sth::bfd::IsBfdRouterHandleValid $routerHandle]} {
                    ::sth::sthCore::log warning  "Warn: $routerHandle is not a valid BFD router handle."
                } else {
                    # get required handles
                    lappend bfdRouterConfigHanList [::sth::sthCore::invoke stc::get $routerHandle -children-BfdRouterConfig]
                }
            }
            set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set resultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId BfdRouterConfig -ResultClassId BfdRouterResults"]
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            ::sth::sthCore::invoke stc::sleep 3
            foreach bfdRouterConfigHandle $bfdRouterConfigHanList {
                set deviceHnd [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -parent]
                set bfdRouterResultsHandle [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -children-BfdRouterResults]
                array set bfdResults [::sth::sthCore::invoke stc::get $bfdRouterResultsHandle]
                set switchNameList [array names ::sth::bfd::emulation_bfd_info_bfd_stats_mode]
                set retVal {}
                foreach switchName $switchNameList {
                    set obj [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info_bfd_stats $switchName stcobj]
                    set attr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info_bfd_stats $switchName stcattr]
                    if { "BfdRouterResults" eq $obj} {
                        set val $bfdResults(-$attr)
                    } else {
                        set val [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -$attr]
                    }
                    keylset retVal $switchName $val
                }
                keylset returnKeyedList $deviceHnd $retVal
            }
            ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
            ::sth::sthCore::invoke stc::perform delete -ConfigList $resultDataSet
        } elseif {($::sth::bfd::userArgsArray(mode) eq "mpls_stats")} {
            set bfdRouterConfigHanList ""
            foreach routerHandle $routers {
                if {![::sth::bfd::IsBfdRouterHandleValid $routerHandle]} {
                    ::sth::sthCore::log warning  "Warn: $routerHandle is not a valid BFD router handle."
                } else {
                    # get required handles
                    lappend bfdRouterConfigHanList [::sth::sthCore::invoke stc::get $routerHandle -children-BfdRouterConfig]
                }
            }
            set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set resultQuery1 [::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId BfdRouterConfig -ResultClassId BfdMplsSessionResults"]
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
            ::sth::sthCore::invoke stc::sleep 3
            foreach bfdRouterConfigHandle $bfdRouterConfigHanList {
                set deviceHnd [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -parent]
                set bfdMplsSessionHndList [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -children-BfdMplsSessionResults]
                set sessionIndex 0
                foreach bfdMplsSessionHnd $bfdMplsSessionHndList {
                    array set bfdResults [::sth::sthCore::invoke stc::get $bfdMplsSessionHnd]
                    set switchNameList [array names ::sth::bfd::emulation_bfd_info_mpls_stats_mode]
                    set retVal {}
                    foreach switchName $switchNameList {
                        set attr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info_mpls_stats $switchName stcattr]
                        set val $bfdResults(-$attr)
                        keylset retVal $switchName $val
                    }
                    keylset returnKeyedList $deviceHnd.$sessionIndex $retVal
                    incr sessionIndex
                }
            }
            ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
            ::sth::sthCore::invoke stc::perform delete -ConfigList $resultDataSet
        } else {
            foreach routerHandle $routers {
                if {![::sth::bfd::IsBfdRouterHandleValid $routerHandle]} {
                    ::sth::sthCore::log warning  "Warn: $routerHandle is not a valid BFD router handle."
                } else {
                    # get required handles
                    set bfdRouterConfigHandle [::sth::sthCore::invoke stc::get $routerHandle -children-BfdRouterConfig]
                    set bfdRtrChild [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -children]
                }
            }
            foreach bfdCpiResultsHandle $bfdRtrChild {
                if {[regexp -nocase "ipv4" $bfdCpiResultsHandle]} {
                    set ipVersion IPv4
                }
                if {[regexp -nocase "ipv6" $bfdCpiResultsHandle]} {
                    set ipVersion IPv6
                }
                if {[string match -nocase "bfdipv4sessionresults*" $bfdCpiResultsHandle]} {
                    set hdlArray(BfdIpv4SessionResults) $bfdCpiResultsHandle
                } elseif {[string match -nocase "bfdipv6sessionresults*" $bfdCpiResultsHandle]} {
                    set hdlArray(BfdIpv6SessionResults) $bfdCpiResultsHandle
                }
            }
    
            # fix CR 224356047, there should be an error in BLL: firstly create a ospf router with BFD enabled on each port(router1, router2),
            # then create a static BFD router over each port step by step (router3, router4),
            # the second created/subscribed BfdIpv4SessionResults on router4
            # will make the first subscribed BfdIpv4SessionResults on router3 disappear
            if {(![info exists hdlArray(BfdIpv4SessionResults)] && $ipVersion == "IPv4") ||
                (![info exists hdlArray(BfdIpv6SessionResults)] && $ipVersion == "IPv6")} {
                set bfdResultDataSet [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]
                if {$ipVersion == "IPv4"} {
                    foreach resDataSet $bfdResultDataSet {
                        ::sth::sthCore::invoke stc::create "ResultQuery" -under $resDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId BfdIpv4SessionResults"}
                    } elseif {$ipVersion == "IPv6"} {
                        foreach resDataSet $bfdResultDataSet {
                            ::sth::sthCore::invoke stc::create "ResultQuery" -under $resDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId BfdIpv6SessionResults"
                        }
                    }
                if {[catch {::sth::sthCore::doStcApply} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error applying BFD configuration: $err"
                    return $returnKeyedList
                }
                ::sth::sthCore::invoke stc::sleep 1
                foreach resDataSet $bfdResultDataSet {
                    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resDataSet
                    ::sth::sthCore::invoke stc::sleep 2
                }
    
                set bfdRtrChild [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -children]
                foreach bfdCpiResultsHandle $bfdRtrChild {
                    if {[string match -nocase "bfdipv4sessionresults*" $bfdCpiResultsHandle]} {
                        set hdlArray(BfdIpv4SessionResults) $bfdCpiResultsHandle
                    } elseif {[string match -nocase "bfdipv6sessionresults*" $bfdCpiResultsHandle]} {
                        set hdlArray(BfdIpv6SessionResults) $bfdCpiResultsHandle
                    }
                }
            }
            
            # create a list of key-value pairs based on the mode -- key to mode mapping defined in bfdTable.tcl
            set mode $::sth::bfd::userArgsArray(mode)
            if {[info exists hdlArray(BfdIpv4SessionResults)]} {
                set sessionResultsHdl $hdlArray(BfdIpv4SessionResults)
            } elseif {[info exists hdlArray(BfdIpv6SessionResults)]} {
                set sessionResultsHdl $hdlArray(BfdIpv6SessionResults)
            }  else {
                continue
            }
            set bfdsessionstate [::sth::sthCore::invoke stc::get $sessionResultsHdl -BfdSessionState]
            keylset returnKeyedList bfd_session_state $bfdsessionstate
                
            #get BfdRouterResults handle
            set bfdRouterResultsHandle [::sth::sthCore::invoke stc::get $bfdRouterConfigHandle -children-BfdRouterResults]
    
            #create an array mapping between stcObj and stcHandle
            set hdlArray(BfdRouterResults) $bfdRouterResultsHandle
            set hdlArray(BfdRouterConfig) $bfdRouterConfigHandle
    
            foreach key [array names ::sth::bfd::emulation_bfd_info_mode] {
                foreach {tblMode tblProc} $::sth::bfd::emulation_bfd_info_mode($key) {
                    if {[string match $tblMode $mode]} {
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set Obj [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info $key stcobj]] "_none_"]} {
                            continue
                        } else {
                            set stcObj [::sth::bfd::getAssociatedItem $ipVersion $Obj]
                        }
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::bfd:: emulation_bfd_info $key stcattr]] "_none_"]} {
                            continue
                        }
                        set val [::sth::sthCore::invoke stc::get $hdlArray($stcObj) -$stcAttr]
    
                        #BFD 2.40 enhancement 12-17-09
                        #return statistics info per session basis
                        #example: learned_info.<handle>.statistics   <port_handle>.aggregate.statistics
                        if {$tblMode == "learned_info"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "learned_info.$routerHandle.$key" $val]
                        } elseif {$tblMode == "aggregate_stats"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "portHandle.aggregate.$key" $val]
                        }
                    }
                }
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


proc ::sth::emulation_bfd_session_config {args} {

    variable ::sth::bfd::sortedSwitchPriorityList
    array unset ::sth::bfd::userArgsArray
    array set ::sth::bfd::userArgsArray {}

    set returnKeyedList ""

    set retVal [catch {
        ::sth::sthCore::Tracker emulation_bfd_session_config $args
        if {[catch {::sth::sthCore::commandInit \
            ::sth::bfd::bfdTable \
            $args \
            ::sth::bfd:: \
            emulation_bfd_session_config \
            ::sth::bfd::userArgsArray \
            sortedSwitchPriorityList} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg" {}
                return $returnKeyedList        }

        switch -exact -- $::sth::bfd::userArgsArray(mode) {
            "create" {
                ::sth::bfd::emulation_bfd_session_config_create returnKeyedList
            }
            "modify" {
                ::sth::bfd::emulation_bfd_session_config_modify returnKeyedList
            }
            "delete" {
                ::sth::bfd::emulation_bfd_session_config_delete returnKeyedList
            }
            default {
               # Unsupported mode
                ::sth::sthCore::processError returnKeyedList "Error: Unsupported -mode value $::sth::bfd::userArgsArray(mode)" {}
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
