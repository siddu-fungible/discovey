# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth:: {
}

proc ::sth::rfc2544_asymmetric_config { args } {
    ::sth::sthCore::Tracker ::sth::rfc2544_asymmetric_config $args
    
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
   if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
                            ::sth::Rfctest:: \
                            rfc2544_asymmetric_config \
                            ::sth::Rfctest::userArgsArray \
                            ::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
    }

    set mode $::sth::Rfctest::userArgsArray(mode)
    
    if {[catch {::sth::Rfctest::rfc2544_asymmetric_config_$mode returnKeyedList} eMsg]} {
    ::sth::sthCore::log error "Stack trace:\n$::errorInfo"
    ::sth::sthCore::processError returnKeyedList $eMsg
     }
        
    return $returnKeyedList
}

proc ::sth::rfc2544_asymmetric_control { args } {
    ::sth::sthCore::Tracker ::sth::rfc2544_asymmetric_control $args
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
                            ::sth::Rfctest:: \
                            rfc2544_asymmetric_control \
                            ::sth::Rfctest::userArgsArray \
                            ::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
    }

    if {[catch {::sth::Rfctest::rfc2544_asymmetric_control returnKeyedList} eMsg]} {
        ::sth::sthCore::log error "Stack trace:\n$::errorInfo"
        ::sth::sthCore::processError returnKeyedList $eMsg
    }
        
    return $returnKeyedList
}

proc ::sth::rfc2544_asymmetric_stats { args } {
    ::sth::sthCore::Tracker ::sth::rfc2544_asymmetric_stats $args
   
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
   if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
                            ::sth::Rfctest:: \
                            rfc2544_asymmetric_stats \
                            ::sth::Rfctest::userArgsArray \
                            ::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
     }
    
    if {[catch {::sth::Rfctest::rfc2544_asymmetric_stats returnKeyedList} eMsg]} {
        ::sth::sthCore::log error "Stack trace:\n$::errorInfo"
        ::sth::sthCore::processError returnKeyedList $eMsg
    }
        
    return $returnKeyedList
}



proc ::sth::rfc2544_asymmetric_profile { args } {
    ::sth::sthCore::Tracker ::sth::rfc2544_asymmetric_profile $args
    
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
                             ::sth::Rfctest:: \
                             rfc2544_asymmetric_profile \
                             ::sth::Rfctest::userArgsArray \
                             ::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
        return $returnKeyedList
     }
     
    set mode $::sth::Rfctest::userArgsArray(mode)
    
    if {[catch {::sth::Rfctest::rfc2544_asymmetric_profile_$mode returnKeyedList} eMsg]} {
        ::sth::sthCore::log error "Stack trace:\n$::errorInfo"
        ::sth::sthCore::processError returnKeyedList $eMsg
    }
        
    return $returnKeyedList
}

proc ::sth::test_rfc2889_config { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc2889_config $args

    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Ancp:: \
							test_rfc2554_config \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode [$::sth::Rfctest::userArgsArray(mode)]
    
	if {[catch {::sth::Ancp::test_rfc2544_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc2544_config { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc2544_config $args

    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc2544_config \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $::sth::Rfctest::userArgsArray(mode)
    
	if {[catch {::sth::Rfctest::test_rfc2544_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc2544_control { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc2544_control $args

    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc2544_control \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
    
	if {[catch {::sth::Rfctest::test_rfc2544_control returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc2544_info { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc2544_info $args
   
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc2544_info \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
    
	if {[catch {::sth::Rfctest::test_rfc2544_info returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc3918_config { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc3918_config $args

    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc3918_config \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
	set mode $::sth::Rfctest::userArgsArray(mode)
    
	if {[catch {::sth::Rfctest::test_rfc3918_config_$mode returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc3918_control { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc3918_control $args

    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc3918_control \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
    
	if {[catch {::sth::Rfctest::test_rfc3918_control returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}

proc ::sth::test_rfc3918_info { args } {
    ::sth::sthCore::Tracker ::sth::test_rfc3918_info $args
   
    variable ::sth::Rfctest::sortedSwitchPriorityList
    variable ::sth::Rfctest::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::Rfctest::rfctestTable $args \
							::sth::Rfctest:: \
							test_rfc3918_info \
							::sth::Rfctest::userArgsArray \
							::sth::Rfctest::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
	}
	
    
	if {[catch {::sth::Rfctest::test_rfc3918_info returnKeyedList} eMsg]} {
		::sth::sthCore::log error "Stack trace:\n$::errorInfo"
		::sth::sthCore::processError returnKeyedList $eMsg
	}
        
	return $returnKeyedList	
}
