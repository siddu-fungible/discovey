# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/ptp.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Ptp:: {

}

proc ::sth::emulation_ptp_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_ptp_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ptp_config"
    
    variable ::sth::Ptp::sortedSwitchPriorityList
    variable ::sth::Ptp::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Ptp::userArgsArray
    array set ::sth::Ptp::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Ptp::PtpTable \
                                            $args \
                                            ::sth::Ptp:: \
                                            emulation_ptp_config \
                                            ::sth::Ptp::userArgsArray \
                                            ::sth::Ptp::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Ptp::userArgsArray(handle)] || [info exists ::sth::Ptp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Ptp::userArgsArray(handle)] && [info exists ::sth::Ptp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Ptp::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }
    
    # check mandatory parameters for create mode
    if {$modeVal == "create"} {
        foreach param_name [list num_sessions count device_type transport_type ] { 
            if {! [info exists ::sth::Ptp::userArgsArray($param_name)]} {
                ::sth::sthCore::processError returnKeyedList "Error in $hltCmdName: Missing mandatory arguments $param_name." {}
                return -code error $returnKeyedList   
            }
        }
    }
    
    set cmd "::sth::Ptp::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error while applying configuration: $err" {}
            return -code error $returnKeyedList  
	}
    }

    return $returnKeyedList
}

proc ::sth::emulation_ptp_control { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_ptp_control" $args
        
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Ptp::sortedSwitchPriorityList
    variable ::sth::Ptp::userArgsArray
    array unset ::sth::Ptp::userArgsArray
    array set ::sth::Ptp::userArgsArray {}

    set hltCmdName "emulation_ptp_control"
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Ptp::PtpTable \
                                            $args \
                                            ::sth::Ptp:: \
                                            $hltCmdName \
                                            ::sth::Ptp::userArgsArray \
                                            ::sth::Ptp::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Ptp::userArgsArray(handle)] || [info exists ::sth::Ptp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }
    if {([info exists ::sth::Ptp::userArgsArray(handle)] && [info exists ::sth::Ptp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set handleList ""
    if {[info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)]} {
        foreach handle $userArgsArray(handle) {
            if {![::sth::Ptp::IsPtpHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $userArgsArray(handle) is not valid PTP handle" {}
                return -code error $returnKeyedList
            }
            lappend handleList $handle    
        }
                
    } elseif {[info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
        
        foreach port $userArgsArray(port_handle) {
            if {[::sth::sthCore::IsPortValid $port err]} {
                if {[catch {set deviceHandle [::sth::sthCore::invoke stc::get $port -affiliationport-sources]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                    return -code error $returnKeyedList   
                }
                foreach device $deviceHandle {
                    if {![::sth::Ptp::IsPtpHandleValid $device]} {
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
        ::sth::sthCore::processError returnKeyedList "Error: No valid PTP device handle specified" {}
        return -code error $returnKeyedList
    }

    # Action is mandatory
    if {![info exists userArgsArray(action_control)]} {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires argument -action_control." {}
        return -code error $returnKeyedList
    }

    set action [string tolower $userArgsArray(action_control)]

    switch -exact -- $action {
        start {
            if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $handleList} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Perform $action ptp Failed: $err" {}
                return -code error $returnKeyedList   
            }
        }
        stop {
            if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $handleList} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Perform $action ptp Failed: $err" {}
                return -code error $returnKeyedList   
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown Value for -action Value:$action." {}
            return -code error $returnKeyedList   
        }
    }

    if {[info exists userArgsArray(handle)]} {
        keylset returnKeyedList handle $userArgsArray(handle)
    } elseif {[info exists userArgsArray(port_handle)]} {
        keylset returnKeyedList port_handle $userArgsArray(port_handle)
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_ptp_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Ptp::sortedSwitchPriorityList
    variable ::sth::Ptp::userArgsArray
    array unset ::sth::Ptp::userArgsArray
    array set ::sth::Ptp::userArgsArray {}

    set hltCmdName "emulation_ptp_stats"

    ::sth::sthCore::Tracker "::sth::emulation_ptp_stats" $args

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Ptp::PtpTable \
                                            $args \
                                            ::sth::Ptp:: \
                                            $hltCmdName \
                                            ::sth::Ptp::userArgsArray \
                                            ::sth::Ptp::sortedSwitchPriorityList} err]} {
	::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
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
    
    # clear ptp stats
    if {[info exists userArgsArray(reset)]} {
        if {![info exists userArgsArray(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Missing mandatory argument port_handle." {}
            return -code error $returnKeyedList     
        }
        if {$userArgsArray(reset) == 1} {
            if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -PortList $userArgsArray(port_handle)} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: reset ptp stats failed $err" {}
                return -code error $returnKeyedList   
            }
        }
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList  
    }

    # collect ptp stats
    if {[catch {::sth::Ptp::emulation_ptp_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

