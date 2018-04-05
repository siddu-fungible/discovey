namespace eval ::sth::microBfd:: {

}

proc ::sth::emulation_micro_bfd_config { args } {
    
    ::sth::sthCore::Tracker "::sth::microBfd::emulation_micro_bfd_config" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_micro_bfd_config"
    
    variable ::sth::microBfd::sortedSwitchPriorityList
    variable ::sth::microBfd::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::microBfd::userArgsArray
    array set ::sth::microBfd::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::microBfd::microBfdTable \
                                            $args \
                                            ::sth::microBfd:: \
                                            emulation_micro_bfd_config \
                                            ::sth::microBfd::userArgsArray \
                                            ::sth::microBfd::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {!([info exists ::sth::microBfd::userArgsArray(handle)] || [info exists ::sth::microBfd::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
        return -code error $returnKeyedList   
    }

    if {([info exists ::sth::microBfd::userArgsArray(handle)] && [info exists ::sth::microBfd::userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
        return -code error $returnKeyedList   
    }
    
    set modeVal create
    if {[info exists ::sth::microBfd::userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }

    set cmd "::sth::microBfd::${hltCmdName}\_$modeVal"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
    
    return $returnKeyedList
}

proc ::sth::emulation_micro_bfd_control { args  } {
    
    ::sth::sthCore::Tracker "::sth::emulation_micro_bfd_control" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_micro_bfd_control"
    
    variable ::sth::microBfd::sortedSwitchPriorityList
    variable ::sth::microBfd::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::microBfd::userArgsArray
    array set ::sth::microBfd::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::microBfd::microBfdTable \
                                            $args \
                                            ::sth::microBfd:: \
                                            emulation_micro_bfd_control \
                                            ::sth::microBfd::userArgsArray \
                                            ::sth::microBfd::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {(![info exists ::sth::microBfd::userArgsArray(port_handle)])
            && (![info exists ::sth::microBfd::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 

    if {[info exists userArgsArray(action)]} {        
    set cmd "::sth::microBfd::${hltCmdName}\_action"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::emulation_micro_bfd_info {args} {
    variable ::sth::microBfd::userArgsArray
    variable ::sth::microBfd::sortedSwitchPriorityList
    array unset ::sth::microBfd::userArgsArray
    array set ::sth::microBfd::userArgsArray {}
    
    ::sth::sthCore::Tracker "::sth::microBfd::emulation_micro_bfd_info" $args
    set _hltCmdName "emulation_micro_bfd_info"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::microBfd::microBfdTable $args \
                                                            ::sth::microBfd:: \
                                                            emulation_micro_bfd_info \
                                                            ::sth::microBfd::userArgsArray \
                                                            ::sth::microBfd::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {(![info exists ::sth::microBfd::userArgsArray(port_handle)])
            && (![info exists ::sth::microBfd::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: In the command $_hltCmdName Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 
        
    if {[catch {::sth::microBfd::emulation_micro_bfd_info_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get stats : $err"
    }
    return $returnKeyedList
}

