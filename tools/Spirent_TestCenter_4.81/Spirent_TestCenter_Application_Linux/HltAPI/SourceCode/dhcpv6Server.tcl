# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/dhcpv6Server.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dhcpv6Server:: {

}

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_config { returnKeyedListVarName args } {
    
    upvar 1 $args dhcpv6ServerArgs
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6Server::sortedSwitchPriorityList
    variable ::sth::Dhcpv6Server::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6Server::userArgsArray
    array set ::sth::Dhcpv6Server::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_server_config"

    ::sth::sthCore::Tracker "::sth::Dhcpv6Server::emulation_dhcpv6_server_config" $dhcpv6ServerArgs
    # check if user has specified device count
    variable ::sth::Dhcpv6Server::dhcpv6SetCountArg 0
    if {[lsearch $dhcpv6ServerArgs -count] > -1} {        
        set ::sth::Dhcpv6Server::dhcpv6SetCountArg 1
    }

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6Server::dhcpv6ServerTable \
                                            $dhcpv6ServerArgs \
                                            ::sth::Dhcpv6Server:: \
                                            emulation_dhcpv6_server_config \
                                            ::sth::Dhcpv6Server::userArgsArray \
                                            ::sth::Dhcpv6Server::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: commandInit FAILED. $err" {}
        return -code error "$err"
    }

    if {!([info exists ::sth::Dhcpv6Server::userArgsArray(handle)] || [info exists ::sth::Dhcpv6Server::userArgsArray(port_handle)])} {
	::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList    
    }

    if {([info exists ::sth::Dhcpv6Server::userArgsArray(handle)] && [info exists ::sth::Dhcpv6Server::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList
    }
    
    set modeVal create
    if {[info exists ::sth::Dhcpv6Server::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
        if {$modeVal=="enable"} {
            set modeVal "create"
        }
    }

    set cmd "::sth::Dhcpv6Server::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: $err." {}
        return -code error $returnKeyedList  
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_control { returnKeyedListVarName args } {
    
    upvar 1 $args dhcpv6ServerArgs
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6Server::sortedSwitchPriorityList
    variable ::sth::Dhcpv6Server::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6Server::userArgsArray
    array set ::sth::Dhcpv6Server::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_server_control"

    ::sth::sthCore::Tracker "::sth::Dhcpv6Server::emulation_dhcpv6_server_control" $dhcpv6ServerArgs

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6Server::dhcpv6ServerTable \
                                            $dhcpv6ServerArgs \
                                            ::sth::Dhcpv6Server:: \
                                            emulation_dhcpv6_server_control \
                                            ::sth::Dhcpv6Server::userArgsArray \
                                            ::sth::Dhcpv6Server::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: commandInit FAILED. $err" {}
        return -code error "$err"
    }
    
    if {(![info exists ::sth::Dhcpv6Server::userArgsArray(port_handle)])
            && (![info exists ::sth::Dhcpv6Server::userArgsArray(dhcp_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 
    
    set cmd "::sth::Dhcpv6Server::${hltCmdName}\_action"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: $err." {}
        return -code error $returnKeyedList  
    }

    return $returnKeyedList
}


proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_stats { returnKeyedListVarName args  } {

    upvar 1 $args dhcpv6ServerArgs
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6Server::sortedSwitchPriorityList
    variable ::sth::Dhcpv6Server::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6Server::userArgsArray
    array set ::sth::Dhcpv6Server::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_server_stats"

    ::sth::sthCore::Tracker "::sth::Dhcpv6Server::emulation_dhcpv6_server_stats" $dhcpv6ServerArgs

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6Server::dhcpv6ServerTable \
                                            $dhcpv6ServerArgs \
                                            ::sth::Dhcpv6Server:: \
                                            emulation_dhcpv6_server_stats \
                                            ::sth::Dhcpv6Server::userArgsArray \
                                            ::sth::Dhcpv6Server::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: commandInit FAILED. $err" {}
        return -code error "$err"
    }

    if {![info exists ::sth::Dhcpv6Server::userArgsArray(action)]} {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: -action" {}
        return -code error $returnKeyedList
    }
    set action [string tolower $::sth::Dhcpv6Server::userArgsArray(action)]
    
    if {[catch {::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_$action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
	return -code error $returnKeyedList
    }

    return $returnKeyedList
}