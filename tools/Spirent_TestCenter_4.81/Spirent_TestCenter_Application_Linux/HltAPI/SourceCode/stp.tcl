# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/stp.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Stp:: {

}

proc ::sth::emulation_stp_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_stp_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_stp_config"
    
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Stp::userArgsArray
    array set ::sth::Stp::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Stp::stpTable \
                                            $args \
                                            ::sth::Stp:: \
                                            $hltCmdName \
                                            ::sth::Stp::userArgsArray \
                                            ::sth::Stp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Stp::userArgsArray(handle)] || [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Stp::userArgsArray(handle)] && [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Stp::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }
    
    set cmd "::sth::Stp::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    keylget returnKeyedList status status
    if {!$::sth::sthCore::optimization && $status} {
        if {[info exists userArgsArray(stp_type)] && $userArgsArray(stp_type) != "mstp" && $::sth::Stp::applyFlag == 1} {
            # for mstp type, need to apply after creating mstp region
            ::sth::sthCore::doStcApply
        }
    }

    return $returnKeyedList
}

proc ::sth::emulation_mstp_region_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_mstp_region_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mstp_region_config"
    
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Stp::userArgsArray
    array set ::sth::Stp::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Stp::stpTable \
                                            $args \
                                            ::sth::Stp:: \
                                            $hltCmdName \
                                            ::sth::Stp::userArgsArray \
                                            ::sth::Stp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::Stp::userArgsArray(handle)] || [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::Stp::userArgsArray(handle)] && [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::Stp::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }
    
    set cmd "::sth::Stp::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    keylget returnKeyedList status status
    if {!$::sth::sthCore::optimization && $status} {
        ::sth::sthCore::doStcApply
    }

    return $returnKeyedList
}


proc ::sth::emulation_msti_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_msti_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_msti_config"
    
    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::Stp::userArgsArray
    array set ::sth::Stp::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Stp::stpTable \
                                            $args \
                                            ::sth::Stp:: \
                                            $hltCmdName \
                                            ::sth::Stp::userArgsArray \
                                            ::sth::Stp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }

    
    set cmd "::sth::Stp::${hltCmdName}"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    keylget returnKeyedList status status
    if {!$::sth::sthCore::optimization && $status} {
        ::sth::sthCore::doStcApply
    }

    return $returnKeyedList
}


proc ::sth::emulation_stp_control { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_stp_control" $args
        
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    array unset ::sth::Stp::userArgsArray
    array set ::sth::Stp::userArgsArray {}

    set hltCmdName "emulation_stp_control"
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Stp::stpTable \
                                            $args \
                                            ::sth::Stp:: \
                                            $hltCmdName \
                                            ::sth::Stp::userArgsArray \
                                            ::sth::Stp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList  
    }
    
    

    if {!([info exists ::sth::Stp::userArgsArray(handle)] || [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }
    if {([info exists ::sth::Stp::userArgsArray(handle)] && [info exists ::sth::Stp::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    if {[info exists ::sth::Stp::userArgsArray(action)]} {
        set actionVal $userArgsArray(action)
    } else {
        ::sth::sthCore::processError returnKeyedList "Error: The command $hltCmdName requires mandatroy argument -action." {}
        return -code error $returnKeyedList 
    }
    
    set cmd "::sth::Stp::${hltCmdName}"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_stp_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Stp::sortedSwitchPriorityList
    variable ::sth::Stp::userArgsArray
    array unset ::sth::Stp::userArgsArray
    array set ::sth::Stp::userArgsArray {}

    set hltCmdName "emulation_stp_stats"

    ::sth::sthCore::Tracker "::sth::emulation_stp_stats" $args

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::Stp::stpTable \
                                            $args \
                                            ::sth::Stp:: \
                                            $hltCmdName \
                                            ::sth::Stp::userArgsArray \
                                            ::sth::Stp::sortedSwitchPriorityList} err]} {
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

    # get STP stats
    if {[catch {::sth::Stp::emulation_stp_stats returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

