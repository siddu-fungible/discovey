namespace eval ::sth:: {

}

namespace eval ::sth::openflow:: {
}

proc ::sth::emulation_openflow_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_openflow_config" $args
    
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    
    set _hltCmdName "emulation_openflow_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_config \
                                                            ::sth::openflow::userArgsArray \
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::openflow::emulation_openflow_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing openflow protocol : $err"
        return $returnKeyedList
    }
    
	keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::openflow::emulation_openflow_config_imp {returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
    set mode $::sth::openflow::userArgsArray(mode)
	
    if {$mode eq "add"} {
        set mode enable
        set ::sth::openflow::userArgsArray(mode) enable
    }
    
    ::sth::openflow::emulation_openflow_config_$mode myreturnKeyedList
}

proc ::sth::emulation_openflow_control {args} {
	::sth::sthCore::Tracker "::sth::emulation_openflow_control" $args
    
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    
    set _hltCmdName "emulation_openflow_control"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_control \
                                                            ::sth::openflow::userArgsArray \
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::openflow::emulation_openflow_control_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing openflow protocol : $err"
        return $returnKeyedList
    }
    
	keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}


proc ::sth::openflow::emulation_openflow_control_imp {returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
    set action $::sth::openflow::userArgsArray(action)
	
    ::sth::openflow::emulation_openflow_control_$action myreturnKeyedList
}


proc ::sth::emulation_openflow_stats {args} {
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    
    set _hltCmdName "emulation_openflow_stats"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_stats \
                                                            ::sth::openflow::userArgsArray \
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::openflow::emulation_openflow_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get openflow stats : $err"
    }
    return $returnKeyedList
}
####################### support openflow switch in hltapi ####################
# US35019 support openflow switch in HLTAPI

proc ::sth::emulation_openflow_switch_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_openflow_switch_config" $args
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    set _hltCmdName "emulation_openflow_switch_config"
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_switch_config \
                                                            ::sth::openflow::userArgsArray\
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::openflow::emulation_openflow_switch_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing openflow switch protocol : $err"
        return $returnKeyedList
    }
	keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::openflow::emulation_openflow_switch_config_imp {returnKeyedList} {
	upvar $returnKeyedList myreturnKeyedList
    set mode $::sth::openflow::userArgsArray(mode)
    ::sth::openflow::emulation_openflow_switch_config_$mode myreturnKeyedList
}



proc ::sth::emulation_openflow_switch_control {args} {
    ::sth::sthCore::Tracker "::sth::emulation_openflow_control" $args
    
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    
    set _hltCmdName "emulation_openflow_switch_control"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_switch_control \
                                                            ::sth::openflow::userArgsArray \
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::openflow::emulation_openflow_switch_control_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing openflow protocol : $err"
        return $returnKeyedList
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}


proc ::sth::openflow::emulation_openflow_switch_control_imp {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    set action $::sth::openflow::userArgsArray(action)
    
    ::sth::openflow::emulation_openflow_switch_control_$action myreturnKeyedList
}

proc ::sth::emulation_openflow_switch_stats {args} {
    variable ::sth::openflow::userArgsArray
    variable ::sth::openflow::sortedSwitchPriorityList
    array unset ::sth::openflow::userArgsArray
    array set ::sth::openflow::userArgsArray {}
    
    set _hltCmdName "emulation_openflow_switch_stats"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    if {[catch {::sth::sthCore::commandInit ::sth::openflow::openflowTable $args \
                                                            ::sth::openflow:: \
                                                            emulation_openflow_switch_stats \
                                                            ::sth::openflow::userArgsArray \
                                                            ::sth::openflow::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
        
    if {[catch {::sth::openflow::emulation_openflow_switch_stats_func returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in get openflow switch stats : $err"
    }
    return $returnKeyedList
}