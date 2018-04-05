namespace eval ::sth::http {

}

proc ::sth::emulation_http_profile_config {args} {
    ::sth::sthCore::Tracker ::emulation_http_profile_config $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_http_profile_config $args"

    variable returnKeyedList ""
    array unset ::sth::http::userArgsArray
    array set ::sth::http::userArgsArray {}
    variable ::sth::http::sortedSwitchPriorityList
    set _hltCmdName emulation_http_profile_config

    if {[catch {
        ::sth::sthCore::commandInit ::sth::http::httpTable $args ::sth::http:: $_hltCmdName ::sth::http::userArgsArray sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }

    if {![string equal create $::sth::http::userArgsArray(mode)]} {
        if {![info exists ::sth::http::userArgsArray(profile_handle)]} {
		    ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Need to provide -profile_handle value" {}
            return $returnKeyedList
        }
    } else {
        if {![info exists ::sth::http::userArgsArray(profile_type)]} {
		    ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Need to provide -profile_type value" {}
            return $returnKeyedList
        }
    }
  
    set cmd "sth::http::emulation_http_profile_config_$::sth::http::userArgsArray(mode) returnKeyedList"
    if {[catch {
        set tempResult [eval $cmd]
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $errMsg" {}
        return $returnKeyedList
    }
	
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::emulation_http_phase_config {args} {
    ::sth::sthCore::Tracker ::emulation_http_phase_config $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_http_phase_config $args"

    variable returnKeyedList ""
    array unset ::sth::http::userArgsArray
    array set ::sth::http::userArgsArray {}
    variable ::sth::http::sortedSwitchPriorityList
    set _hltCmdName emulation_http_phase_config

    if {[catch {
        ::sth::sthCore::commandInit ::sth::http::httpTable $args ::sth::http:: $_hltCmdName ::sth::http::userArgsArray  sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }

    if {![string equal create $::sth::http::userArgsArray(mode)]} {
	if {![info exists ::sth::http::userArgsArray(phase_handle)] || [string equal "" $::sth::http::userArgsArray(phase_handle)]} {
		    ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Need to provide -phase_handle value" {}
            return $returnKeyedList
        }
	
    } elseif {[string equal create $::sth::http::userArgsArray(mode)]} {
        if {![info exists ::sth::http::userArgsArray(profile_handle)] || [string equal "" $::sth::http::userArgsArray(profile_handle)]} {
		    ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_profile_config Failed: Need to provide -profile_handle value" {}
            return $returnKeyedList
        }
    }
    if {![info exists ::sth::http::userArgsArray(load_pattern)] && ([string equal create $::sth::http::userArgsArray(mode)])} {
        set ::sth::http::userArgsArray(load_pattern) stair
    }

    set cmd "sth::http::emulation_http_phase_config_$::sth::http::userArgsArray(mode) returnKeyedList "
    if {[catch {
        set tempResult [eval $cmd]
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $errMsg" {}
        return $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::emulation_http_config {args} {
    ::sth::sthCore::Tracker ::emulation_http_config $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_http_config $args"
    
    variable returnKeyedList ""
    array unset ::sth::http::userArgsArray
    array set ::sth::http::userArgsArray {}
    variable ::sth::http::sortedSwitchPriorityList

    set _hltCmdName emulation_http_config

    if {[catch {
        ::sth::sthCore::commandInit ::sth::http::httpTable $args ::sth::http:: $_hltCmdName ::sth::http::userArgsArray  sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_config Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }
    if {![info exists ::sth::http::userArgsArray(device_handle)] || [string equal "" ::sth::http::userArgsArray(device_handle)]} {
        if {[string equal create $::sth::http::userArgsArray(mode)]} {
            if {![info exists ::sth::http::userArgsArray(port_handle)] || [string equal "" $::sth::http::userArgsArray(port_handle)]} {
                ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_config Failed: Need to provide -device_handle value or -port_handle vlaue" {}
                return $returnKeyedList
            } else {
                set tempResult ""
                set tempDeviceHandle ""
                set tempResult [sth::emulation_device_config -mode create -port_handle $::sth::http::userArgsArray(port_handle)]
                set tempDeviceHandle [keylget tempResult handle]
                set ::sth::http::userArgsArray(device_handle) $tempDeviceHandle
                keylset returnKeyedList device_handle $tempDeviceHandle
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_config Failed: Need to provide -device_handle value" {}
            return $returnKeyedList
        }
    }

    set cmd "sth::http::emulation_http_config_$::sth::http::userArgsArray(mode) returnKeyedList"
    if {[catch {
        set tempResult [eval $cmd]
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $errMsg" {}
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::emulation_http_control {args} {
    ::sth::sthCore::Tracker ::emulation_http_control $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_http_control $args"

    variable returnKeyedList ""
    variable userArgsArray
    variable sortedSwitchPriorityList
    set _hltCmdName emulation_http_control

    array set argArray {}
    set args [string tolower $args]
    ::sth::http::listToArray $args argArray

    if {[catch {
        ::sth::sthCore::commandInit ::sth::http::httpTable $args ::sth::http:: $_hltCmdName userArgsArray sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_control Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }

    set cmd "::sth::http::emulation_http_control_$argArray(-mode) $args"
    if {[catch {
        set tempResult [eval $cmd]
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $errMsg" {}
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}

proc ::sth::emulation_http_stats {args} {
    ::sth::sthCore::Tracker ::emulation_http_stats $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_http_stats $args"

    variable returnKeyedList ""
    variable userArgsArray
    variable sortedSwitchPriorityList
    set _hltCmdName emulation_http_stats

    array set argArray {}
    set args [string tolower $args]
    ::sth::http::listToArray $args argArray

    if {[catch {
        ::sth::sthCore::commandInit ::sth::http::httpTable $args ::sth::http:: $_hltCmdName userArgsArray sortedSwitchPriorityList
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_stats Failed: Command init error: $errMsg" {}
        return $returnKeyedList
    }

    if {[catch {
        if {[regexp -- httpclientprotocolconfig $argArray(-handle)]} {
            set tempClientResult ""
            set tempClientResult [sth::sthCore::invoke stc::get $argArray(-handle) -children]
            if {[string equal "" $tempClientResult]} {
        
                sth::sthCore::invoke stc::subscribe \
                                            -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                            -ResultType httpclientresults \
                                            -ConfigType httpclientprotocolconfig \
                                            -ResultParent $argArray(-handle)
        
                set tempClientResult [sth::sthCore::invoke stc::get $argArray(-handle) -children]
                ##need some time to get results from hard device
                ::sth::sthCore::invoke stc::sleep 3
            }
        
            ##get return item name from httpTable
            foreach tempName [array names ::sth::http::emulation_http_stats_client_results_stcattr] {
                keylset returnKeyedList $tempName [stc::get $tempClientResult -$::sth::http::emulation_http_stats_client_results_stcattr($tempName)]
            }
        } elseif {[regexp -- httpserverprotocolconfig $argArray(-handle)]} {
            set tempServerResult ""
            set tempServerResult [sth::sthCore::invoke stc::get $argArray(-handle) -children]
            if {[string equal "" $tempServerResult]} {
        
                sth::sthCore::invoke stc::subscribe \
                                            -Parent $::sth::sthCore::GBLHNDMAP(project) \
                                            -ResultType httpserverresults \
                                            -ConfigType httpserverprotocolconfig \
                                            -ResultParent $argArray(-handle)
                
                set tempServerResult [sth::sthCore::invoke stc::get $argArray(-handle) -children]
                ##need some time to get results from hard device
                ::sth::sthCore::invoke stc::sleep 3
            }
        
            ##get return item name from httpTable
            foreach tempName [array names ::sth::http::emulation_http_stats_server_results_stcattr] {
                keylset returnKeyedList $tempName [stc::get $tempServerResult -$::sth::http::emulation_http_stats_server_results_stcattr($tempName)]
            }
        } else {
            return "Wrong handle $argArray(-handle)"
        }
    } errMsg]} {
        ::sth::sthCore::processError returnKeyedList "::sth::emulation_http_stats Failed: $errMsg" {}
        return $returnKeyedList
    }
    keylset returnKeyedList status 1
    return $returnKeyedList
}
