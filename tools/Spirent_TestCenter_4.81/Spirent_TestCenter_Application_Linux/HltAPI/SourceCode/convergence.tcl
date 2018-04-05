namespace eval ::sth:: {

}

proc ::sth::emulation_convergence_config { args } {    
    ::sth::sthCore::Tracker "::sth::emulation_convergence_config" $args
    
    variable ::sth::convergence::userArgsArray
    variable ::sth::convergence::sortedSwitchPriorityList
    array unset ::sth::convergence::userArgsArray
    array set ::sth::convergence::userArgsArray {}
    
    set _hltCmdName "emulation_convergence_config"
    
    set returnKeyedList ""
    
    if {[catch {::sth::sthCore::commandInit ::sth::convergence::convergenceTable $args \
                                                            ::sth::convergence:: \
                                                            emulation_convergence_config \
                                                            ::sth::convergence::userArgsArray \
                                                            ::sth::convergence::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

        
    set mode $::sth::convergence::userArgsArray(mode)   
    if {[catch {::sth::convergence::emulation_convergence_config_$mode returnKeyedList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
        return $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::emulation_convergence_control {args} {
    ::sth::sthCore::Tracker "::sth::emulation_convergence_control" $args 

    variable ::sth::convergence::sortedSwitchPriorityList
    variable ::sth::convergence::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set _hltCmdName "emulation_convergence_control"
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::convergence::convergenceTable $args \
                                                    ::sth::convergence:: \
                                                    emulation_convergence_control \
                                                    ::sth::convergence::userArgsArray \
                                                    ::sth::convergence::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    if {[catch {::sth::convergence::emulation_convergence_control returnKeyedList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
    }

    return $returnKeyedList
}

proc ::sth::emulation_convergence_info {args} {
    ::sth::sthCore::Tracker ::sth::emulation_convergence_info $args 

    variable ::sth::convergence::sortedSwitchPriorityList
    variable ::sth::convergence::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::convergence::convergenceTable $args \
                                                    ::sth::convergence:: \
                                                    emulation_convergence_info \
                                                    ::sth::convergence::userArgsArray \
                                                    ::sth::convergence::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }

    if {[catch {::sth::convergence::emulation_convergence_info returnKeyedList} eMsg]} { 
            ::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
    }

    return $returnKeyedList
}