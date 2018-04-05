# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2013 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::synce:: {
    set subscribed 0
}

proc ::sth::emulation_synce_config { args } {
    
    ::sth::sthCore::Tracker "::sth::synce::emulation_synce_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_synce_config"
    
    variable ::sth::synce::sortedSwitchPriorityList
    variable ::sth::synce::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::synce::userArgsArray
    array set ::sth::synce::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::synce::synceTable \
                                            $args \
                                            ::sth::synce:: \
                                            emulation_synce_config \
                                            ::sth::synce::userArgsArray \
                                            ::sth::synce::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::synce::userArgsArray(handle)] || [info exists ::sth::synce::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::synce::userArgsArray(handle)] && [info exists ::sth::synce::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::synce::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }

    set cmd "::sth::synce::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    return $returnKeyedList
}

proc ::sth::emulation_synce_control { args  } {
    
    ::sth::sthCore::Tracker "::sth::emulation_synce_control" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_synce_control"
    
    variable ::sth::synce::sortedSwitchPriorityList
    variable ::sth::synce::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::synce::userArgsArray
    array set ::sth::synce::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::synce::synceTable \
                                            $args \
                                            ::sth::synce:: \
                                            emulation_synce_control \
                                            ::sth::synce::userArgsArray \
                                            ::sth::synce::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {(![info exists ::sth::synce::userArgsArray(port_handle)])
            && (![info exists ::sth::synce::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 

    if {[info exists userArgsArray(action)]} {        
	set cmd "::sth::synce::${hltCmdName}\_action"
	if {[catch {eval $cmd returnKeyedList} err]} {
	    ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
	    return -code error $returnKeyedList  
	}
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::emulation_synce_stats {args} {
    variable ::sth::synce::userArgsArray
    variable ::sth::synce::sortedSwitchPriorityList
    array unset ::sth::synce::userArgsArray
    array set ::sth::synce::userArgsArray {}
	
    ::sth::sthCore::Tracker "::sth::synce::emulation_synce_stats" $args
    set _hltCmdName "emulation_synce_stats"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::synce::synceTable $args \
                                                            ::sth::synce:: \
                                                            emulation_synce_stats \
                                                            ::sth::synce::userArgsArray \
                                                            ::sth::synce::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
    }
        
    if {(![info exists ::sth::synce::userArgsArray(port_handle)])
            && (![info exists ::sth::synce::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: In the command $_hltCmdName Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 
		
    if {[catch {::sth::synce::emulation_synce_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get synce stats : $err"
    }
    return $returnKeyedList
}

