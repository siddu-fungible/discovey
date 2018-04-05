# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/dot1x.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dot1x:: {

}

proc ::sth::emulation_dot1x_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dot1x_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dot1x_config"
    
    variable ::sth::Dot1x::sortedSwitchPriorityList
    variable ::sth::Dot1x::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Dot1x::userArgsArray
    array set ::sth::Dot1x::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Dot1x::Dot1xTable \
                                            $args \
                                            ::sth::Dot1x:: \
                                            emulation_dot1x_config \
                                            ::sth::Dot1x::userArgsArray \
                                            ::sth::Dot1x::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Dot1x::userArgsArray(handle)] || [info exists ::sth::Dot1x::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Dot1x::userArgsArray(handle)] && [info exists ::sth::Dot1x::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Dot1x::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }
    
    set cmd "::sth::Dot1x::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    keylget returnKeyedList status status
    if {!$::sth::sthCore::optimization && $status} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error while applying configuration: $err" {}
            return -code error $returnKeyedList  
        }
    }

    return $returnKeyedList
}

proc ::sth::emulation_dot1x_control { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dot1x_control" $args
        
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Dot1x::sortedSwitchPriorityList
    variable ::sth::Dot1x::userArgsArray
    array unset ::sth::Dot1x::userArgsArray
    array set ::sth::Dot1x::userArgsArray {}

    set hltCmdName "emulation_dot1x_control"
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Dot1x::Dot1xTable \
                                            $args \
                                            ::sth::Dot1x:: \
                                            $hltCmdName \
                                            ::sth::Dot1x::userArgsArray \
                                            ::sth::Dot1x::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }
        
    # download or delete certificates
    if {[info exists userArgsArray(action)]} {
        # port_handle is mandatory for -action download
        if {![info exists userArgsArray(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: The -action download requires mandatroy argument -port_handle." {}
            return -code error $returnKeyedList   
        }
	set action $userArgsArray(action)
	set cmd "::sth::Dot1x::${hltCmdName}\_$action"
	if {[catch {eval $cmd returnKeyedList} err]} {
	    ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
	    return -code error $returnKeyedList  
	}
        
        return $returnKeyedList
    }

    # start/stop authentication
    if {!([info exists ::sth::Dot1x::userArgsArray(handle)] || [info exists ::sth::Dot1x::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }
    if {([info exists ::sth::Dot1x::userArgsArray(handle)] && [info exists ::sth::Dot1x::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set handleList ""
    if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
        foreach handle $userArgsArray(handle) {
            if {![::sth::Dot1x::IsDot1xHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $userArgsArray(handle) is not valid Dot1x handle" {}
                return -code error $returnKeyedList
            }
            lappend handleList $handle    
        }
                
    } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
        
        foreach port $userArgsArray(port_handle) {
            if {[::sth::sthCore::IsPortValid $port err]} {
                set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                foreach device $deviceHandle {
                    if {![::sth::Dot1x::IsDot1xHandleValid $device]} {
                        continue
                    }
                    lappend handleList $device
                }
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                return -code error $returnKeyedList
            }
        }
    }
    
    if {[llength $handleList] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error: No valid Dot1x device handle specified" {}
        return -code error $returnKeyedList
    }

    set mode [string tolower $userArgsArray(mode)]

    switch -exact -- $mode {
        start {
            ::sth::sthCore::invoke stc::perform Dot1xStartAuth -ObjectList $handleList
        }
        stop {
            ::sth::sthCore::invoke stc::perform Dot1xAbortAuth -ObjectList $handleList
        }
        logout {
            ::sth::sthCore::invoke stc::perform Dot1xLogout -ObjectList $handleList
        }
        abort {
            ::sth::sthCore::invoke stc::perform Dot1xAbortAuth -ObjectList $handleList
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown Value for -action Value:$mode." {}
            return -code error $returnKeyedList   
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_dot1x_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Dot1x::sortedSwitchPriorityList
    variable ::sth::Dot1x::userArgsArray
    array unset ::sth::Dot1x::userArgsArray
    array set ::sth::Dot1x::userArgsArray {}

    set hltCmdName "emulation_dot1x_stats"

    ::sth::sthCore::Tracker "::sth::emulation_dot1x_stats" $args

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Dot1x::Dot1xTable \
                                            $args \
                                            ::sth::Dot1x:: \
                                            $hltCmdName \
                                            ::sth::Dot1x::userArgsArray \
                                            ::sth::Dot1x::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists userArgsArray(handle)] || [info exists userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }
    
    if {([info exists userArgsArray(handle)] && [info exists userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }

    # get 802.1x stats
    if {[catch {::sth::Dot1x::emulation_dot1x_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

