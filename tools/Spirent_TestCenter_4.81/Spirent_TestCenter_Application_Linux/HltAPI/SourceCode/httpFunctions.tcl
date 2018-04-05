namespace eval ::sth::http:: {
}
#######################################################################
#Functions: emulation_http_phase_config_create
#           emulation_http_phase_config_modify
#           emulation_http_phase_config_delete
#######################################################################
proc ::sth::http::emulation_http_phase_config_create {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_phase_config_create "
    variable ::sth::http::userArgsArray
    upvar 1 $returnKeyedListarg returnKeyedList
    set cmdLine ""
    # set default values for non-user defined switches
    foreach key [array names ::sth::http::emulation_http_phase_config_default] {
	if {![info exists ::sth::http::userArgsArray($key)]} {
	    set defaultValue [::sth::sthCore::getswitchprop ::sth::http:: emulation_http_phase_config $key default]
	    if {![string match -nocase $defaultValue "_none_"]} {
	        set ::sth::http::argArray($key) $defaultValue
	    }
	}
    }
    if {[info exists ::sth::http::userArgsArray(profile_handle)]} {
        ::sth::http::load_phase_create returnKeyedList 
    } else {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -profile_handle." {}
        return -code error $returnKeyedList
    }
   
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_phase_config_modify {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_phase_config_modify "

    variable ::sth::http::userArgsArray
    upvar 1 $returnKeyedListarg returnKeyedList
    set cmdLine ""
    
    if {[info exists ::sth::http::userArgsArray(phase_handle)]} {
        set tempPatternType [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(phase_handle) -LoadPattern]
        if {![string equal -nocase $tempPatternType $::sth::http::userArgsArray(load_pattern)]} {
            set tempPatternHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(phase_handle) -children]
            ::sth::sthCore::invoke stc::delete $tempPatternHandle 
                #::sth::http::load_phase_create $args
            set cmdLine ""
            switch -exact $::sth::http::userArgsArray(load_pattern){
                    stair {
			set cmdLine [::sth::http::pattern_stair_config]
			::sth::sthCore::invoke stc::create StairPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    flat {
			set cmdLine [::sth::http::pattern_flat_config]
			::sth::sthCore::invoke stc::create FlatPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    burst {
			set cmdLine [::sth::http::pattern_burst_config]
			::sth::sthCore::invoke stc::create BurstPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    sinusoid {
			set cmdLine [::sth::http::pattern_sinusoid_config]
			::sth::sthCore::invoke stc::create SinusoidPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    random {
			set cmdLine [::sth::http::pattern_random_config]
			::sth::sthCore::invoke stc::create RandomPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    sawtooth {
			set cmdLine [::sth::http::pattern_sawTooth_config]
			::sth::sthCore::invoke stc::create SawToothPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                    default {
			set cmdLine [::sth::http::pattern_stair_config]
			::sth::sthCore::invoke stc::create StairPatternDescriptor -under $::sth::http::userArgsArray(phase_handle) $cmdLine
                    }
                }    
            } else {
                    ::sth::http::load_phase_modify 
            }
                    
            set cmdLine ""
            set cmdLine [::sth::http::load_phase_config modify]
            ::sth::sthCore::invoke stc::config $::sth::http::userArgsArray(phase_handle) $cmdLine
        }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_phase_config_delete {args} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_phase_config_delete "
    if {[info exists ::sth::http::userArgsArray(phase_handle) ]} {
        ::sth::sthCore::invoke stc::delete $::sth::http::userArgsArray(phase_handle)
    }
    return $::sth::sthCore::SUCCESS
}

#########################################################################
#Functions: emulation_http_profile_config_create
#           emulation_http_profile_config_modify
#           emulation_http_profile_config_delete
#########################################################################

proc ::sth::http::emulation_http_profile_config_create {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_profile_config_create "
    variable ::sth::http::userArgsArray
    upvar 1 $returnKeyedListarg returnKeyedList
    set cmdLine ""
    
    #set default values for non-user defined switches
    foreach key [array names ::sth::http::emulation_http_profile_config_default] {
	if {![info exists ::sth::http::userArgsArray($key)]} {
	    set defaultValue [::sth::sthCore::getswitchprop ::sth::http:: emulation_http_profile_config $key default]
	    if {![string match -nocase $defaultValue "_none_"]} {
	        set ::sth::http::argArray($key) $defaultValue
	    }
	}
    } 
    if {[string equal "load" $::sth::http::userArgsArray(profile_type)]} {

        if {[string match -nocase *-use_dynamic_load* $::sth::http::userArgsArray(optional_args)]} {
            if {![info exists ::sth::http::userArgsArray(load_type)] || ![string equal -nocase bandwidth $::sth::http::userArgsArray(load_type)]} {
                ::sth::sthCore::processError returnKeyedList "Error: Please set -load_type as bandwidth before configuring -use_dynamic_load" {}
            }
        }
        set cmdLine [::sth::http::load_profile_config "create" ]
        set tempLoadHandle [::sth::sthCore::invoke stc::create ClientLoadProfile -under $::sth::sthCore::GBLHNDMAP(project) $cmdLine]
        keylset returnKeyedList load_profile_handle $tempLoadHandle

        unset tempLoadHandle

    } elseif {[string equal "client" $::sth::http::userArgsArray(profile_type)]} {
        set cmdLine [::sth::http::client_server_profile_config "create"]
        set tempClientHandle [::sth::sthCore::invoke stc::create ClientProfile -under $::sth::sthCore::GBLHNDMAP(project) $cmdLine]

        ##create http client protocol profile
        set cmdLine [::sth::http::client_protocol_profile_config "create"]
        ::sth::sthCore::invoke stc::create HttpClientProtocolProfile -under $tempClientHandle $cmdLine

        keylset returnKeyedList client_profile_handle $tempClientHandle

    } elseif {[string equal "server" $::sth::http::userArgsArray(profile_type)]} {
        set cmdLine [::sth::http::client_server_profile_config "create"]
        set tempServerHandle [::sth::sthCore::invoke stc::create ServerProfile -under $::sth::sthCore::GBLHNDMAP(project) $cmdLine]

        ##create http server protocol profile
        set cmdLine [::sth::http::server_protocol_profile_config "create"]
        set tempServerProtocolProfile [::sth::sthCore::invoke stc::create HttpServerProtocolProfile -under $tempServerHandle $cmdLine]

        ##deal with server response configuration
        set cmdLine [::sth::http::server_response_config "create"]
        if {[llength $cmdLine]} {
            set tempServerResponse [::sth::sthCore::invoke stc::get $tempServerProtocolProfile -children-httpserverresponseconfig]
            ::sth::sthCore::invoke stc::config $tempServerResponse $cmdLine
        }
        keylset returnKeyedList server_profile_handle $tempServerHandle
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_profile_config_modify {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_profile_config_modify "
    set cmdLine ""
    upvar 1 $returnKeyedListarg returnKeyedList

    if {[regexp -- clientloadprofile $::sth::http::userArgsArray(profile_handle)]} {
        if {[string match -nocase *-use_dynamic_load* $::sth::http::userArgsArray(optional_args)]} {
            if {![info exists ::sth::http::userArgsArray(load_type)] || ![string equal -nocase bandwidth $::sth::http::userArgsArray(load_type)]} {
                ::sth::sthCore::processError returnKeyedList "Error: Please set -load_type as bandwidth before configuring -use_dynamic_load" {}
            }
        }
        set cmdLine [::sth::http::load_profile_config "modify"]
        if {[llength $cmdLine]} {
            ::sth::sthCore::invoke stc::config $::sth::http::userArgsArray(profile_handle) $cmdLine
        }
    } elseif {[regexp -- clientprofile $::sth::http::userArgsArray(profile_handle)]} {
        set cmdLine [::sth::http::client_server_profile_config "modify"]
        if {[llength $cmdLine]} {
            ::sth::sthCore::invoke stc::config $::sth::http::userArgsArray(profile_handle) $cmdLine
        }
        set cmdLine [::sth::http::client_protocol_profile_config "modify"]
        if {[llength $cmdLine]} {
            set tempClientProtocolProfile [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(profile_handle) -children]
            ::sth::sthCore::invoke stc::config $tempClientProtocolProfile $cmdLine
            unset tempClientProtocolProfile
        }
    } elseif {[regexp -- serverprofile $::sth::http::userArgsArray(profile_handle)]} {
        set cmdLine [::sth::http::client_server_profile_config "modify"]
        if {[llength $cmdLine]} {
            ::sth::sthCore::invoke stc::config $::sth::http::userArgsArray(profile_handle) $cmdLine
        }
        ##modify http server protocol profile
        set cmdLine [::sth::http::server_protocol_profile_config "modify"]
        if {[llength $cmdLine]} {
            set tempServerProtocolProfile [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(profile_handle) -children]
            ::sth::sthCore::invoke stc::config $tempServerProtocolProfile $cmdLine
        }

        ##modify http server response configuration
        set cmdLine [::sth::http::server_response_config "modify"]
        if {[llength $cmdLine]} {
            set tempServerProtocolProfile [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(profile_handle) -children]
            set tempServerResponse [::sth::sthCore::invoke stc::get $tempServerProtocolProfile -children-httpserverresponseconfig]
            ::sth::sthCore::invoke stc::config $tempServerResponse $cmdLine
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_profile_config_delete {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_profile_config_delete "
    upvar 1 $returnKeyedListarg returnKeyedList
    
    foreach tempHandle $::sth::http::userArgsArray(profile_handle) {
        ::sth::sthCore::invoke stc::delete $tempHandle
    }
    return $::sth::sthCore::SUCCESS
}
#################################################################################################
proc ::sth::http::emulation_http_config_create {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_config_create "
    set cmdLine ""
    upvar 1 $returnKeyedListarg returnKeyedList

    #set default values for non-user defined switches
    foreach key [array names ::sth::http::emulation_http_config_default] {
	if {![info exists ::sth::http::userArgsArray($key)]} {
	    set defaultValue [::sth::sthCore::getswitchprop ::sth::http:: emulation_http_config $key default]
	    if {![string match -nocase $defaultValue "_none_"]} {
	        set ::sth::http::argArray($key) $defaultValue
	    }
	}
    } 
    set tempClientHandle ""
    set tempServerHandle ""
    if {[regexp -- client $::sth::http::userArgsArray(http_type)]} {
        set tempClientHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(device_handle) -children-httpclientprotocolconfig]
        if {[llength $tempClientHandle]} {
            ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_create Failed: There is already a http client on $::sth::http::userArgsArray(device_handle)" {}
            return $::sth::sthCore::FAILURE
        }
        set tempClientHandle [::sth::sthCore::invoke stc::create HttpClientProtocolConfig -under $::sth::http::userArgsArray(device_handle)]
        keylset returnKeyedList client_handle $tempClientHandle
    } elseif {[regexp -- server $::sth::http::userArgsArray(http_type)]} {
        set tempServerHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(device_handle) -children-httpserverprotocolconfig]
        if {![string equal "" $tempServerHandle]} {
            ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_create Failed: There is already a http server on $::sth::http::userArgsArray(device_handle)" {}
            return $::sth::sthCore::FAILURE
        }
        set tempServerHandle [::sth::sthCore::invoke stc::create HttpServerProtocolConfig -under $::sth::http::userArgsArray(device_handle)]
        keylset returnKeyedList server_handle $tempServerHandle
    }

    ##config http client protocol config
    set cmdLine [::sth::http::http_client_config "create"]
    if {![string equal "" $cmdLine]} {
        ::sth::sthCore::invoke stc::config $tempClientHandle $cmdLine
    }
    ##config http server protocol config
    set cmdLine [::sth::http::http_server_config "create"]
    if {![string equal "" $cmdLine]} {
        ::sth::sthCore::invoke stc::config $tempServerHandle $cmdLine
    }
    ##-usesif-targets will added automaticly after stc::apply
    #::sth::sthCore::invoke stc::apply

    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_config_modify {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_config_modify "
    set cmdLine ""
    upvar 1 $returnKeyedListarg returnKeyedList

    set tempClientHandle ""
    set tempServerHandle ""
    if {[regexp -- client $::sth::http::userArgsArray(http_type)]} {
        set tempClientHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(device_handle) -children-httpclientprotocolconfig]
        if {[string equal "" $tempClientHandle]} {
            ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_modify Failed: There is no http client on $::sth::http::userArgsArray(device_handle)" {}
            return $::sth::sthCore::FAILURE
        }
        set cmdLine [::sth::http::http_client_config "modify"]
        if {[llength $cmdLine]} {
            ::sth::sthCore::invoke stc::config $tempClientHandle $cmdLine
        }
    } elseif {[regexp -- server $::sth::http::userArgsArray(http_type)]} {
        set tempServerHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(device_handle) -children-httpserverprotocolconfig]
        if {[string equal "" $tempServerHandle]} {
            ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_modify Failed: There is no http server on $::sth::http::userArgsArray(device_handle)" {}
            return $::sth::sthCore::FAILURE
        }
        set cmdLine [::sth::http::http_server_config "modify"]
        if {[llength $cmdLine]} {
            ::sth::sthCore::invoke stc::config $tempServerHandle $cmdLine
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_config_delete {returnKeyedListarg} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_config_delete "

    set cmdLine ""
    upvar 1 $returnKeyedListarg returnKeyedList

    set tempClientHandle ""
    set tempServerHandle ""

    foreach tempDeviceHandle $::sth::http::userArgsArray(device_handle) {
        if {[regexp -- client $::sth::http::userArgsArray(http_type)]} {
            set tempClientHandle [::sth::sthCore::invoke stc::get $tempDeviceHandle -children-httpclientprotocolconfig]
            if {[string equal "" $tempClientHandle]} {
                ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_delete Failed: there is no http client on $tempDeviceHandle" {}
                return $::sth::sthCore::FAILURE
            }
            ::sth::sthCore::invoke stc::delete $tempClientHandle
        } elseif {[regexp -- server $::sth::http::userArgsArray(http_type)]} {
            set tempServerHandle [::sth::sthCore::invoke stc::get $tempDeviceHandle -children-httpserverprotocolconfig]
            if {[string equal "" $tempServerHandle]} {
                ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_config_delete Failed: there is no http server on $tempDeviceHandle" {}
                return $::sth::sthCore::FAILURE
            }
            ::sth::sthCore::invoke stc::delete $tempServerHandle
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_control_start {args} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_control_start $args"

    upvar returnKeyedList returnKeyedList
    array set argArray {}
    ::sth::http::listToArray $args argArray

    ::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $argArray(-handle)

    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_control_stop {args} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_control_stop $args"

    upvar returnKeyedList returnKeyedList
    array set argArray {}
    ::sth::http::listToArray $args argArray

    ::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $argArray(-handle)

    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::emulation_http_control_clear_stats {args} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::emulation_http_control_clear_stats $args"

    upvar returnKeyedList returnKeyedList
    array set argArray {}
    ::sth::http::listToArray $args argArray

    foreach tempHandle $argArray(-handle) {
        set tempClientResult ""
        set tempClientResult [::sth::sthCore::invoke stc::get $tempHandle -children]
        if {![string equal "" $tempClientResult]} {
            set tempSources ""
            set tempResultSet ""
            set tempSources [::sth::sthCore::invoke stc::get $tempClientResult -resultchild-Sources]
            regexp -- {resultdataset\d+} $tempSources tempResultSet
            if {![string equal "" $tempResultSet]} {
                ::sth::sthCore::invoke stc::perform resultsclearviewcommand -resultdataset $tempResultSet
            } else {
                ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_control_clear_stats Failed: There is no result set." {}
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "::sth::http::emulation_http_control_clear_stats Failed: There is no result handle." {}
        }
    }
    return $::sth::sthCore::SUCCESS
}

proc ::sth::http::load_profile_config { mode } {
    return [getStcOptionValueList emulation_http_profile_config load_profile_config $mode ]
}


proc ::sth::http::load_phase_config {mode} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::load_phase_config "
    return [getStcOptionValueList emulation_http_phase_config load_phase_config $mode ] 
}

proc ::sth::http::load_phase_create {returnKeyedList} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::load_phase_create "
    variable ::sth::http::userArgsArray
    upvar 1 $returnKeyedList returnKeyedLst
    
    set cmdLine ""
    set cmdLine [::sth::http::load_phase_config "create"]
    
    if {[info exists ::sth::http::userArgsArray(profile_handle)]} {
        set tempLoadHandle $::sth::http::userArgsArray(profile_handle)
    }
    
    set tempPhaseHandle [::sth::sthCore::invoke stc::create ClientLoadPhase -under $tempLoadHandle $cmdLine]

    ##create load pattern
    set cmdLine ""
    switch -exact $::sth::http::userArgsArray(load_pattern) {
        stair {
            set cmdLine [::sth::http::pattern_stair_config ]
            ::sth::sthCore::invoke stc::create StairPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        flat {
            set cmdLine [::sth::http::pattern_flat_config ]
            ::sth::sthCore::invoke stc::create FlatPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        burst {
            set cmdLine [::sth::http::pattern_burst_config ]
            ::sth::sthCore::invoke stc::create BurstPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        sinusoid {
            set cmdLine [::sth::http::pattern_sinusoid_config ]
            ::sth::sthCore::invoke stc::create SinusoidPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        random {
            set cmdLine [::sth::http::pattern_random_config ]
            ::sth::sthCore::invoke stc::create RandomPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        sawtooth {
            set cmdLine [::sth::http::pattern_sawTooth_config ]
            ::sth::sthCore::invoke stc::create SawToothPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
        default {
            set cmdLine [::sth::http::pattern_stair_config ]
            ::sth::sthCore::invoke stc::create StairPatternDescriptor -under $tempPhaseHandle $cmdLine
        }
    }
    keylset returnKeyedLst load_phase_handle $tempPhaseHandle
    return $::sth::sthCore::SUCCESS
}


proc ::sth::http::load_phase_modify {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::load_phase_modify "

    upvar returnKeyedList returnKeyedList
    variable ::sth::http::userArgsArray
    set cmdLine ""

    if {[info exists ::sth::http::userArgsArray(profile_handle)]} {
        set tempLoadHandle ::sth::http::userArgsArray(profile_handle)
    }
    
    set tempPatternHandle [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(phase_handle) -children]
    set tempPatternType [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(phase_handle) -LoadPattern]
    set tempPatternType [string tolower $tempPatternType]
    switch -exact $tempPatternType {
    stair {
            set cmdLine [::sth::http::pattern_stair_config]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    flat {
            set cmdLine [::sth::http::pattern_flat_config ]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    burst {
            set cmdLine [::sth::http::pattern_burst_config ]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    sinusoid {
            set cmdLine [::sth::http::pattern_sinusoid_config ]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    random {
            set cmdLine [::sth::http::pattern_random_config ]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    sawtooth {
            set cmdLine [::sth::http::pattern_sawTooth_config ]
            ::sth::sthCore::invoke stc::config $tempPatternHandle $cmdLine
        }
    default {}
    }
    return $::sth::sthCore::SUCCESS
}



proc ::sth::http::pattern_stair_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::pattern_stair_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(repetitions)]} {
        append cmdLine " -Repetitions $::sth::http::userArgsArray(repetitions) "
    }
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -Height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(ramp_time)]} {
        append cmdLine " -RampTime $::sth::http::userArgsArray(ramp_time) "
    }
    if {[info exists ::sth::http::userArgsArray(steady_time)]} {
        append cmdLine " -SteadyTime $::sth::http::userArgsArray(steady_time) "
    }
    return $cmdLine
}

proc ::sth::http::pattern_flat_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::pattern_flat_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -Height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(ramp_time)]} {
        append cmdLine " -RampTime $::sth::http::userArgsArray(ramp_time) "
    }
    if {[info exists ::sth::http::userArgsArray(steady_time)]} {
        append cmdLine " -SteadyTime $::sth::http::userArgsArray(steady_time) "
    }
    return $cmdLine
}

proc ::sth::http::pattern_burst_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::pattern_burst_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(repetitions)]} {
        append cmdLine " -Repetitions $::sth::http::userArgsArray(repetitions) "
    }
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(burst_time)]} {
        append cmdLine " -BurstTime $::sth::http::userArgsArray(burst_time) "
    }
    if {[info exists ::sth::http::userArgsArray(pause_time)]} {
        append cmdLine " -PauseTime $::sth::http::userArgsArray(pause_time) "
    }
    return $cmdLine
}

proc ::sth::http::pattern_sinusoid_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::pattern_sinusoid_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(repetitions)]} {
        append cmdLine " -Repetitions $::sth::http::userArgsArray(repetitions) "
    }
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -Height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(period)]} {
        append cmdLine " -Period $::sth::http::userArgsArray(period) "
    }
    return $cmdLine
}

proc ::sth::http::pattern_random_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::pattern_random_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(repetitions) ]} {
        append cmdLine " -Repetitions $::sth::http::userArgsArray(repetitions) "
    }
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -Height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(ramp_time)]} {
        append cmdLine " -RampTime $::sth::http::userArgsArray(ramp_time) "
    }
    if {[info exists ::sth::http::userArgsArray(steady_time)]} {
        append cmdLine " -SteadyTime $::sth::http::userArgsArray(steady_time) "
    }
    return $cmdLine
}

proc ::sth::http::pattern_sawTooth_config {} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::pattern_sawTooth_config "

    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(repetitions)]} {
        append cmdLine " -Repetitions $::sth::http::userArgsArray(repetitions) "
    }
    if {[info exists ::sth::http::userArgsArray(height)]} {
        append cmdLine " -Height $::sth::http::userArgsArray(height) "
    }
    if {[info exists ::sth::http::userArgsArray(pause_time)]} {
        append cmdLine " -PauseTime $::sth::http::userArgsArray(pause_time) "
    }
    if {[info exists ::sth::http::userArgsArray(steady_time)]} {
        append cmdLine " -SteadyTime $::sth::http::userArgsArray(steady_time) "
    }
    return $cmdLine
}

proc ::sth::http::client_server_profile_config { mode } {
    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(profile_name)]} {
        append cmdLine " -ProfileName $::sth::http::userArgsArray(profile_name) "
    }
    append cmdLine [getStcOptionValueList emulation_http_profile_config client_server_profile_config $mode ]
    return $cmdLine
}

proc ::sth::http::client_protocol_profile_config { mode } {
    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(user_agent_header)]} {
        append cmdLine " -UserAgentHeader $::sth::http::userArgsArray(user_agent_header) "
    }
    append cmdLine [getStcOptionValueList emulation_http_profile_config client_protocol_profile_config $mode ]
    return $cmdLine
}
   
proc ::sth::http::server_protocol_profile_config {mode} {
    variable ::sth::http::userArgsArray
    
    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(http_version)]} {
        append cmdLine " -HttpVersion $::sth::http::userArgsArray(http_version) "
    }
    append cmdLine [getStcOptionValueList emulation_http_profile_config server_protocol_profile_config $mode ]
    return $cmdLine
}

proc ::sth::http::server_response_config {mode} {
    return [getStcOptionValueList emulation_http_profile_config server_response_config $mode ]
}
   
proc ::sth::http::http_client_config {mode} {
    ::sth::sthCore::log hltcall "User executed ::sth::http::http_client_config "
    
    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(load_profiles)]} {
        append cmdLine " -affiliatedclientloadprofile-Targets $::sth::http::userArgsArray(load_profiles) "
    }
    if {[info exists ::sth::http::userArgsArray(client_profiles)]} {
        append cmdLine " -affiliatedclientprofile-Targets $::sth::http::userArgsArray(client_profiles) "
    }
    if {[info exists ::sth::http::userArgsArray(connected_server)]} {
        set tempConnectedServer ""
        set tempConnectedServer [::sth::sthCore::invoke stc::get $::sth::http::userArgsArray(connected_server) -children-httpserverprotocolconfig]
        if {![llength $tempConnectedServer]} {
            ::sth::sthCore::processError returnKeyedList "There is no http server configuration on device $::sth::http::userArgsArray(connected_server)" {}
            return $::sth::sthCore::FAILURE
        } else {
            append cmdLine " -connectiondestination-Targets $tempConnectedServer "
        }
        ##-usesif-targets will added automaticly after stc::apply
    }
    append cmdLine [getStcOptionValueList emulation_http_config http_client_config $mode ]
    return $cmdLine
}

proc ::sth::http::http_server_config {mode} {
    set cmdLine ""
    if {[info exists ::sth::http::userArgsArray(server_profiles)]} {
        append cmdLine " -affiliatedserverprofile-Targets $::sth::http::userArgsArray(server_profiles) "
    }
    append cmdLine [getStcOptionValueList emulation_http_config http_server_config $mode ]
    return $cmdLine
}

proc ::sth::http::getStcOptionValueList {cmdType modeFunc mode} {
    
    set optionValueList {}
    
    foreach item $::sth::http::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::http:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::http:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::http:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                #::sth::http::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::http::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::http:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::http:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::http:: $cmdType $opt $::sth::http::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::http::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::http::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}
proc ::sth::http::listToArray {args aResultsName} {
    upvar $aResultsName aName

    set lstResponses [regexp -nocase -all -line -inline -- {(-[^[:space:]]*) ([^-]*)} [join $args]]
    foreach {szMatch szAttr szValue} $lstResponses {
        regsub -all {[\{\}]} $szValue {} szValue
        set aName($szAttr) [string trim $szValue]
    }
}