namespace eval ::sth:: {
}

namespace eval ::sth::6pe6vpe:: {
}

proc ::sth::emulation_6pe_6vpe_provider_port_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_6pe_6vpe_provider_port_config" $args

    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::sortedSwitchPriorityList
    array unset ::sth::6pe6vpe::userArgsArray
    array set ::sth::6pe6vpe::userArgsArray {}

    set _hltCmdName "emulation_6pe_6vpe_provider_port_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::6pe6vpe::6pe6vpeTable $args \
                                                            ::sth::6pe6vpe:: \
                                                            emulation_6pe_6vpe_provider_port_config \
                                                            ::sth::6pe6vpe::userArgsArray \
                                                            ::sth::6pe6vpe::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::6pe6vpe::emulation_6pe_6vpe_provider_port_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing 6PE/6VPE provider side port config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_provider_port_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::6pe6vpe::userArgsArray(mode)
    
    ::sth::6pe6vpe::emulation_6pe_6vpe_provider_port_config_$mode myReturnKeyedList
}

proc ::sth::emulation_6pe_6vpe_cust_port_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_6pe_6vpe_cust_port_config" $args

    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::sortedSwitchPriorityList
    array unset ::sth::6pe6vpe::userArgsArray
    array set ::sth::6pe6vpe::userArgsArray {}

    set _hltCmdName "emulation_6pe_6vpe_cust_port_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::6pe6vpe::6pe6vpeTable $args \
                                                            ::sth::6pe6vpe:: \
                                                            emulation_6pe_6vpe_cust_port_config \
                                                            ::sth::6pe6vpe::userArgsArray \
                                                            ::sth::6pe6vpe::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::6pe6vpe::emulation_6pe_6vpe_cust_port_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing 6PE/6VPE customer side port config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_cust_port_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::6pe6vpe::userArgsArray(mode)
    
    ::sth::6pe6vpe::emulation_6pe_6vpe_cust_port_config_$mode myReturnKeyedList
}


proc ::sth::emulation_6pe_6vpe_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_6pe_6vpe_config" $args

    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::sortedSwitchPriorityList
    array unset ::sth::6pe6vpe::userArgsArray
    array set ::sth::6pe6vpe::userArgsArray {}

    set _hltCmdName "emulation_6pe_6vpe_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::6pe6vpe::6pe6vpeTable $args \
                                                            ::sth::6pe6vpe:: \
                                                            emulation_6pe_6vpe_config \
                                                            ::sth::6pe6vpe::userArgsArray \
                                                            ::sth::6pe6vpe::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::6pe6vpe::emulation_6pe_6vpe_config_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing 6PE/6VPE network config : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_config_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::6pe6vpe::userArgsArray(mode)
    
    ::sth::6pe6vpe::emulation_6pe_6vpe_config_$mode myReturnKeyedList
}

proc ::sth::emulation_6pe_6vpe_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_6pe_6vpe_control" $args

    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::sortedSwitchPriorityList
    array unset ::sth::6pe6vpe::userArgsArray
    array set ::sth::6pe6vpe::userArgsArray {}

    set _hltCmdName "emulation_6pe_6vpe_control"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::6pe6vpe::6pe6vpeTable $args \
                                                            ::sth::6pe6vpe:: \
                                                            emulation_6pe_6vpe_control \
                                                            ::sth::6pe6vpe::userArgsArray \
                                                            ::sth::6pe6vpe::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::6pe6vpe::emulation_6pe_6vpe_control_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing 6PE/6VPE network control : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_control_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set action $::sth::6pe6vpe::userArgsArray(action)
    
    if {![info exists ::sth::6pe6vpe::userArgsArray(handle)] && ![info exists ::sth::6pe6vpe::userArgsArray(port_handle)]} {
        return -code 1 -errorcode -1 "Either handle or port_handle need to be specified"
    }
    ::sth::6pe6vpe::emulation_6pe_6vpe_control_$action myReturnKeyedList
}

proc ::sth::emulation_6pe_6vpe_info { args } {

    ::sth::sthCore::Tracker "::sth::emulation_6pe_6vpe_info" $args

    variable ::sth::6pe6vpe::userArgsArray
    variable ::sth::6pe6vpe::sortedSwitchPriorityList
    array unset ::sth::6pe6vpe::userArgsArray
    array set ::sth::6pe6vpe::userArgsArray {}

    set _hltCmdName "emulation_6pe_6vpe_info"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::6pe6vpe::6pe6vpeTable $args \
                                                            ::sth::6pe6vpe:: \
                                                            emulation_6pe_6vpe_info \
                                                            ::sth::6pe6vpe::userArgsArray \
                                                            ::sth::6pe6vpe::sortedSwitchPriorityList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "In the command $_hltCmdName, ::sth::sthCore::commandInit error. Error: $eMsg"
            return $returnKeyedList
    }
    if {[catch {::sth::6pe6vpe::emulation_6pe_6vpe_info_imp returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in processing 6PE/6VPE info : $err"
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    return $returnKeyedList
}

proc ::sth::6pe6vpe::emulation_6pe_6vpe_info_imp {returnKeyedList} {
    
    upvar $returnKeyedList myReturnKeyedList
    set mode $::sth::6pe6vpe::userArgsArray(mode)

    ::sth::6pe6vpe::emulation_6pe_6vpe_info_$mode myReturnKeyedList
}
