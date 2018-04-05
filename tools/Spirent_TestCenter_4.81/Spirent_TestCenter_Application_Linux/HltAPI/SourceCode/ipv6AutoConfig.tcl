# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2013 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Ipv6AutoConfig:: {
    set subscribed 0
}

proc ::sth::emulation_ipv6_autoconfig { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_ipv6_autoconfig" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig"
    
    variable ::sth::Ipv6AutoConfig::sortedSwitchPriorityList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Ipv6AutoConfig::userArgsArray
    array set ::sth::Ipv6AutoConfig::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Ipv6AutoConfig::ipv6AutoConfigTable \
                                            $args \
                                            ::sth::Ipv6AutoConfig:: \
                                            emulation_ipv6_autoconfig \
                                            ::sth::Ipv6AutoConfig::userArgsArray \
                                            ::sth::Ipv6AutoConfig::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Ipv6AutoConfig::userArgsArray(handle)] || [info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Ipv6AutoConfig::userArgsArray(handle)] && [info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Ipv6AutoConfig::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }

    set cmd "::sth::Ipv6AutoConfig::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    return $returnKeyedList
}

proc ::sth::emulation_ipv6_autoconfig_control { args  } {
    
    ::sth::sthCore::Tracker "::sth::emulation_ipv6_autoconfig_control" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_control"
    
    variable ::sth::Ipv6AutoConfig::sortedSwitchPriorityList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Ipv6AutoConfig::userArgsArray
    array set ::sth::Ipv6AutoConfig::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Ipv6AutoConfig::ipv6AutoConfigTable \
                                            $args \
                                            ::sth::Ipv6AutoConfig:: \
                                            emulation_ipv6_autoconfig_control \
                                            ::sth::Ipv6AutoConfig::userArgsArray \
                                            ::sth::Ipv6AutoConfig::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {(![info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)])
            && (![info exists ::sth::Ipv6AutoConfig::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 

    if {[info exists userArgsArray(action)]} {        
	set cmd "::sth::Ipv6AutoConfig::${hltCmdName}\_action"
	if {[catch {eval $cmd returnKeyedList} err]} {
	    ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
	    return -code error $returnKeyedList  
	}
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::emulation_ipv6_autoconfig_stats { args } {

    ::sth::sthCore::Tracker "::sth::emulation_ipv6_autoconfig_stats" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_stats"
    
    variable ::sth::Ipv6AutoConfig::sortedSwitchPriorityList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Ipv6AutoConfig::userArgsArray
    array set ::sth::Ipv6AutoConfig::userArgsArray {}

    set returnKeyedList ""


    if {[catch {::sth::sthCore::commandInit ::sth::Ipv6AutoConfig::ipv6AutoConfigTable \
                                            $args \
                                            ::sth::Ipv6AutoConfig:: \
                                            emulation_ipv6_autoconfig_stats \
                                            ::sth::Ipv6AutoConfig::userArgsArray \
                                            ::sth::Ipv6AutoConfig::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {[catch {::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_get_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}