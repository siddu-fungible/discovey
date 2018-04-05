namespace eval ::sth::twamp:: {
}

proc ::sth::emulation_twamp_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::twamp::sortedSwitchPriorityList
    variable ::sth::twamp::userArgsArray
    array unset ::sth::twamp::userArgsArray
    array set ::sth::twamp::userArgsArray {}

    set _hltCmdName "emulation_twamp_config"

    ::sth::sthCore::Tracker "::sth::emulation_twamp_config" $args

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::twamp::twampTable $args ::sth::twamp:: $_hltCmdName userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err"
        return $returnKeyedList
    }
    
    set mode $userArgsArray(mode)
    
    if {[catch {::sth::twamp::${_hltCmdName}_${mode} returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
        return $returnKeyedList
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::emulation_twamp_session_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::twamp::sortedSwitchPriorityList
    variable ::sth::twamp::userArgsArray
    array unset ::sth::twamp::userArgsArray
    array set ::sth::twamp::userArgsArray {}

    set _hltCmdName "emulation_twamp_session_config"

    ::sth::sthCore::Tracker "::sth::emulation_twamp_session_config" $args

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::twamp::twampTable $args ::sth::twamp:: $_hltCmdName userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err"
        return $returnKeyedList
    }
    
    set mode $userArgsArray(mode)
    
    if {[catch {::sth::twamp::${_hltCmdName}_${mode} returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
        return $returnKeyedList
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_twamp_control {args} {
    ::sth::sthCore::Tracker ::sth::emulation_twamp_control $args 

    variable ::sth::twamp::sortedSwitchPriorityList
    variable ::sth::twamp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::twamp::twampTable $args \
							::sth::twamp:: \
							emulation_twamp_control \
							::sth::twamp::userArgsArray \
							::sth::twamp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::twamp::emulation_twamp_control returnKeyedList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}


proc ::sth::emulation_twamp_stats {args} {
    ::sth::sthCore::Tracker ::sth::emulation_twamp_stats $args 

    variable ::sth::twamp::sortedSwitchPriorityList
    variable ::sth::twamp::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::twamp::twampTable $args \
							::sth::twamp:: \
							emulation_twamp_stats \
							::sth::twamp::userArgsArray \
							::sth::twamp::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
    
	if {[catch {::sth::twamp::emulation_twamp_stats returnKeyedList} eMsg]} { 
		::sth::sthCore::processError returnKeyedList "Stack trace:$::errorInfo,$eMsg"
	}

	return $returnKeyedList
}
