namespace eval ::sth::mplstpOam:: {

}


proc ::sth::emulation_mplstp_y1731_oam_control { args  } {
    
    ::sth::sthCore::Tracker "::sth::emulation_mplstp_y1731_oam_control" $args
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_mplstp_y1731_oam_control"
    
    variable ::sth::mplstpOam::sortedSwitchPriorityList
    variable ::sth::mplstpOam::userArgsArray
    # unset to load new switches for another config or reset
    array unset ::sth::mplstpOam::userArgsArray
    array set ::sth::mplstpOam::userArgsArray {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::mplstpOam::mplstpOamTable \
                                            $args \
                                            ::sth::mplstpOam:: \
                                            emulation_mplstp_y1731_oam_control \
                                            ::sth::mplstpOam::userArgsArray \
                                            ::sth::mplstpOam::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList  
    }

    if {(![info exists ::sth::mplstpOam::userArgsArray(port_handle)])
            && (![info exists ::sth::mplstpOam::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 

    if {[info exists userArgsArray(action)]} {        
    set cmd "::sth::mplstpOam::${hltCmdName}\_action"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList  
    }
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::emulation_mplstp_y1731_oam_stats {args} {
    variable ::sth::mplstpOam::userArgsArray
    variable ::sth::mplstpOam::sortedSwitchPriorityList
    array unset ::sth::mplstpOam::userArgsArray
    array set ::sth::mplstpOam::userArgsArray {}
    
    ::sth::sthCore::Tracker "::sth::mplstpOam::emulation_mplstp_y1731_oam_stats" $args
    set _hltCmdName "emulation_mplstp_y1731_oam_stats"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::mplstpOam::mplstpOamTable $args \
                                                            ::sth::mplstpOam:: \
                                                            emulation_mplstp_y1731_oam_stats \
                                                            ::sth::mplstpOam::userArgsArray \
                                                            ::sth::mplstpOam::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
    }
        
    if {(![info exists ::sth::mplstpOam::userArgsArray(port_handle)])
            && (![info exists ::sth::mplstpOam::userArgsArray(handle)])} {
        ::sth::sthCore::processError returnKeyedList "Error: In the command $_hltCmdName Missing mandatory attribute, either -port_handle or -handle." {}
        return -code error $returnKeyedList
    } 
        
    if {[catch {::sth::mplstpOam::emulation_mplstp_y1731_oam_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get mplstpOam stats : $err"
    }
    return $returnKeyedList
}

