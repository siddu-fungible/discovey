# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Ancp {
    set subscriber_type ""
}

##Procedure Header
#
# Name:
#    sth::emulation_ancp_config
#
# Purpose:
#    Creates, modifies, or deletes an emulated ANCP
#    router on a Spirent HLTAPI chassis.
#
# Synopsis:
#::sth::emulation_ancp_config
#    -mode {create|modify|delete}
#    [-handle <ancp_handle>]
#    [-port_handle <port handle>]
#    [-device_count <NUMERIC>]
#    [-encap_type {ETHERNETII}]
#    [-vlan_id <NUMERIC>]
#    [-vlan_id_count <NUMERIC>]
#    [-vlan_id_repeat <NUMERIC>]
#    [-vlan_id_step <NUMERIC>]
#    [-vlan_id_inner <NUMERIC>]
#    [-vlan_id_count_inner <NUMERIC>]
#    [-vlan_id_repeat_inner <NUMERIC>]
#    [-vlan_id_step_inner <NUMERIC>]
#    [-local_mac_addr <ANY>]
#    [-local_mac_step <ANY>]
#    [-local_mac_repeat <NUMERIC>]
#    [-intf_ip_addr <IPv4>]
#    [-intf_ip_repeat <NUMERIC>]
#    [-intf_ip_step <IPv4>]
#    [-intf_ip_prefix_len <NUMERIC>]
#    [-intf_ip_prefix <NUMERIC>]
#    [-sut_ip_addr <IPV4>]
#    [-sut_ip_count <NUMERIC>]
#    [-sut_ip_repeat <NUMERIC>]
#    [-sut_ip_step <IPV4>]
#    [-sut_ip_prefix_len <NUMERIC>]
#    [-sut_ip_prefix <NUMERIC>]
#    [-gateway_ip_addr <IPV4>]
#    [-gateway_ip_repeat <NUMERIC>]
#    [-gateway_ip_step <IPV4>]
#    [-gateway_ip_prefix_len <NUMERIC>]
#    [-gateway_ip_prefix <NUMERIC>]
#    [-ancp_standard {ietf-ancp-protocol2|gsmp-l2control-config2|rfc_6320}]
#    [-keep_alive <RANGE 100 - 25500>]
#    [-topology_discovery {0|1}]
#    [-bulk_transaction {0|1}]
#
# Arguments:
#
#
# Return Values:
#    The sth::emulation_ancp_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handles   A list of handles that identify the routers created by the
#              sth::emulation_ancp_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# End of Procedure Header

proc ::sth::emulation_ancp_config { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ancp_config $args

    variable ::sth::Ancp::sortedSwitchPriorityList
    variable ::sth::Ancp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Ancp::ancpTable $args \
							::sth::Ancp:: \
							emulation_ancp_config \
							::sth::Ancp::userArgsArray \
							::sth::Ancp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	# remap "reset" mode to "disable"
    set mode [string map -nocase {reset disable} $::sth::Ancp::userArgsArray(mode)]
    
	if {[catch {::sth::Ancp::emulation_ancp_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}
        
        #add by Fei Cheng. 2008-7-7
#        if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
#                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}
#
#	}

	return $returnKeyedList	
}



proc ::sth::emulation_ancp_subscriber_lines_config { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ancp_subscriber_lines_config $args

    variable ::sth::Ancp::sortedSwitchPriorityList
    variable ::sth::Ancp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Ancp::ancpTable $args \
							::sth::Ancp:: \
							emulation_ancp_subscriber_lines_config \
							::sth::Ancp::userArgsArray \
							::sth::Ancp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	# remap "reset" mode to "disable"
        set mode [string map -nocase {reset disable} $::sth::Ancp::userArgsArray(mode)]
    
	if {[catch {::sth::Ancp::emulation_ancp_subscriber_lines_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}
        
        #add by Fei Cheng. 2008-7-7
#        if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
#                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}
#
#	}

	return $returnKeyedList	
}



proc ::sth::emulation_ancp_control {args} {
    ::sth::sthCore::Tracker ::sth::emulation_ancp_control $args 

    variable ::sth::Ancp::sortedSwitchPriorityList
    variable ::sth::Ancp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Ancp::ancpTable $args \
							::sth::Ancp:: \
							emulation_ancp_control \
							::sth::Ancp::userArgsArray \
							::sth::Ancp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
        
        if {$userArgsArray(action) == "initiate" || $userArgsArray(action) == "send"} {
            if {[info exists userArgsArray(ancp_handle)]} {
                set handle $::sth::Ancp::userArgsArray(ancp_handle)
                if {[catch {::sth::Ancp::emulation_ancp_control $handle returnKeyedList} eMsg]} {
		    ::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	        }    
            }
        } else {
            if {[info exists userArgsArray(ancp_subscriber)]} {
                set handle $::sth::Ancp::userArgsArray(ancp_subscriber)
                if {[catch {::sth::Ancp::emulation_ancp_subscriber_control $handle returnKeyedList} eMsg]} {
		    ::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	        }    
            }
        }
    
	return $returnKeyedList
}



proc ::sth::emulation_ancp_stats {args} {
    ::sth::sthCore::Tracker ::sth::emulation_ancp_stats $args 

    variable ::sth::Ancp::sortedSwitchPriorityList
    variable ::sth::Ancp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Ancp::ancpTable $args \
							::sth::Ancp:: \
							emulation_ancp_stats \
							::sth::Ancp::userArgsArray \
							::sth::Ancp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::Ancp::emulation_ancp_stats returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}
