# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/dhcpv6.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dhcpv6:: {
    variable dhcpv6Pd ""
}

proc ::sth::Dhcpv6::emulation_dhcpv6_config { returnKeyedListVarName args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcpv6_config" $args
    upvar 1 $args dhcpv6Args
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6::userArgsArray
    array set ::sth::Dhcpv6::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_config"

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6::dhcpv6Table \
                                            $dhcpv6Args \
                                            ::sth::Dhcpv6:: \
                                            emulation_dhcpv6_config \
                                            ::sth::Dhcpv6::userArgsArray \
                                            ::sth::Dhcpv6::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Dhcpv6::userArgsArray(handle)] || [info exists ::sth::Dhcpv6::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Dhcpv6::userArgsArray(handle)] && [info exists ::sth::Dhcpv6::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Dhcpv6::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
        if {$modeVal=="enable"} {
            set modeVal "create"
        }
    }
   

    set cmd "::sth::Dhcpv6::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_group_config { returnKeyedListVarName args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcpv6_group_config" $args
    upvar 1 $args dhcpv6Args
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6::userArgsArray
    array set ::sth::Dhcpv6::userArgsArray {}
    array set usrArray {};
    array set usrArray $dhcpv6Args
    set hltCmdName "emulation_dhcpv6_group_config"
    set returnKeyedList ""
    set dhcp6ClientModeTableName  "emulation_dhcpv6pd_group_config"
    set ::sth::Dhcpv6::dhcpv6Pd 1

    if {[info exists usrArray(-dhcp6_client_mode)]} {
        set dhcpv6ClientMode $usrArray(-dhcp6_client_mode)
        if { [string match -nocase $dhcpv6ClientMode "DHCPV6"] ||
             [string match -nocase $dhcpv6ClientMode "DHCPV6ANDPD"]} {
            set dhcp6ClientModeTableName "emulation_dhcpv6_group_config"
            set ::sth::Dhcpv6::dhcpv6Pd 0
        }
    } else {
        set ::sth::Dhcpv6::dhcpv6Pd 0
    }
    
    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6::dhcpv6Table \
                                            $dhcpv6Args \
                                            ::sth::Dhcpv6:: \
                                            $dhcp6ClientModeTableName \
                                            ::sth::Dhcpv6::userArgsArray \
                                            ::sth::Dhcpv6::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    set modeVal create
    if {[info exists ::sth::Dhcpv6::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
        if {$modeVal=="enable"} {
            set modeVal "create"
        }
    }

    set cmd "::sth::Dhcpv6::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_control { returnKeyedListVarName args  } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcpv6_control" $args
    upvar 1 $args dhcpv6Args
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6::userArgsArray
    array set ::sth::Dhcpv6::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_control"

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6::dhcpv6Table \
                                            $dhcpv6Args \
                                            ::sth::Dhcpv6:: \
                                            emulation_dhcpv6_control \
                                            ::sth::Dhcpv6::userArgsArray \
                                            ::sth::Dhcpv6::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    if {(![info exists ::sth::Dhcpv6::userArgsArray(port_handle)])
            && (![info exists ::sth::Dhcpv6::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 

    if {[info exists userArgsArray(action)]} {        
	set cmd "::sth::Dhcpv6::${hltCmdName}\_action"
	if {[catch {eval $cmd returnKeyedList} err]} {
	    ::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: $err." {}
	    return -code error $returnKeyedList  
	}
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_stats { returnKeyedListVarName args } {

    ::sth::sthCore::Tracker "::sth::emulation_dhcpv6_stats" $args

    upvar 1 $args dhcpv6Args
    upvar $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dhcpv6::userArgsArray
    array set ::sth::Dhcpv6::userArgsArray {}
    set hltCmdName "emulation_dhcpv6_stats"


    if {[catch {::sth::sthCore::commandInit ::sth::Dhcpv6::dhcpv6Table \
                                            $dhcpv6Args \
                                            ::sth::Dhcpv6:: \
                                            emulation_dhcpv6_stats \
                                            ::sth::Dhcpv6::userArgsArray \
                                            ::sth::Dhcpv6::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    if {[catch {::sth::Dhcpv6::emulation_dhcpv6_get_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}