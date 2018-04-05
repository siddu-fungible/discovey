namespace eval ::sth::igmp:: {

}
proc ::sth::emulation_igmp_querier_config {args} {
    ::sth::sthCore::Tracker "::sth::emulation_igmp_querier_config" $args 
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_igmp_querier_config"
    
    variable ::sth::igmp::sortedSwitchPriorityList
    variable ::sth::igmp::userArgsArray
    variable ::sth::igmp::switchValues
    # unset to load new switches for another config or reset
    array unset ::sth::igmp::userArgsArray
    array set ::sth::igmp::userArgsArray {}
    array unset ::sth::igmp::switchValues
    array set ::sth::igmp::switchValues {}

    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::igmp::igmpQuerierTable \
                                            $args \
                                            ::sth::igmp:: \
                                            emulation_igmp_querier_config \
                                            ::sth::igmp::userArgsArray \
                                            ::sth::igmp::sortedSwitchPriorityList} err]} {
        keylset returnKeyedList log "Error in $procName: $err"
        return -code error $returnKeyedList  
    }
    
	set retVal [catch {
		if {!([info exists ::sth::igmp::userArgsArray(handle)] || [info exists ::sth::igmp::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: The command $hltCmdName requires mandatroy argument -port_handle or -handle." {}
			return -code error $returnKeyedList   
		}

		if {([info exists ::sth::igmp::userArgsArray(handle)] && [info exists ::sth::igmp::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: The options -port_handle and -handle are mutually exclusive." {}
			return -code error $returnKeyedList   
		}
		
		set modeVal create
		if {[info exists ::sth::igmp::userArgsArray(mode)]} {
			set modeVal $userArgsArray(mode)
			if {$modeVal=="enable"} {
				set modeVal "create"
			}
		}
		
		set cmd "::sth::igmp::${hltCmdName}\_$modeVal"
		eval $cmd returnKeyedList
		
		keylget returnKeyedList status status
		if {!$::sth::sthCore::optimization && $status} {
			::sth::sthCore::doStcApply
		}
	} returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::emulation_igmp_querier_control {args} {

    variable ::sth::igmp::userArgsArray
    variable sortedSwitchPriorityList
    array unset ::sth::igmp::userArgsArray
    array set ::sth::igmp::userArgsArray {}

    set returnKeyedList ""

    ::sth::sthCore::Tracker emulation_igmp_querier_control $args
    if {[catch {::sth::sthCore::commandInit \
        ::sth::igmp::igmpQuerierTable \
        $args \
        ::sth::igmp:: \
        emulation_igmp_querier_control \
        ::sth::igmp::userArgsArray \
        sortedSwitchPriorityList \
    } err]} {
    keylset returnKeyedList log "$err"
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    return $returnKeyedList
    }

    set retVal [catch {
        set deviceList ""
        if {[info exists ::sth::igmp::userArgsArray(handle)]} {
            foreach router $::sth::igmp::userArgsArray(handle) {
                append deviceList " [::sth::sthCore::invoke stc::get $router -children-IgmpRouterConfig]"
            }
        } elseif {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            set port_list $::sth::igmp::userArgsArray(port_handle)
            foreach port $port_list {
                foreach router [::sth::sthCore::invoke stc::get $port -affiliationport-Sources] {
                   append deviceList " [::sth::sthCore::invoke stc::get $router -children-IgmpRouterConfig]"
                }
            }
        }
        switch $::sth::igmp::userArgsArray(mode) {
            start { set deviceCmd "IgmpMldStartQuerierCommand "}
            stop { set deviceCmd "IgmpMldStopQuerierCommand "}
            default {
                return -code error [concat "Error:  Unsupported IGMP " \
                     "control mode \"$::sth::igmp::userArgsArray(mode)\".  "]
            }
        }
        if {[llength $deviceList] > 0} {
           ::sth::sthCore::doStcApply
           ::sth::sthCore::invoke stc::perform $deviceCmd -blocklist $deviceList
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}
   
   
proc ::sth::emulation_igmp_querier_info {args} {

    variable ::sth::igmp::userArgsArray
    variable sortedSwitchPriorityList
    array unset ::sth::igmp::userArgsArray
    array set ::sth::igmp::userArgsArray {}

    set returnKeyedList ""

    ::sth::sthCore::Tracker emulation_igmp_querier_info $args
    if {[catch {::sth::sthCore::commandInit \
        ::sth::igmp::igmpQuerierTable \
        $args \
        ::sth::igmp:: \
        emulation_igmp_querier_info \
        ::sth::igmp::userArgsArray \
        sortedSwitchPriorityList \
    } err]} {
        keylset returnKeyedList log "$err"
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    }

    set retVal [catch {
        set deviceList ""
        if {[info exists ::sth::igmp::userArgsArray(handle)]} {
            foreach router $::sth::igmp::userArgsArray(handle) {
                append igmpRouterhandleList " [::sth::sthCore::invoke stc::get $router -children-IgmpRouterConfig]"
            }
        } elseif {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            foreach port $::sth::igmp::userArgsArray(port_handle) {
                foreach router [::sth::sthCore::invoke stc::get $port -affiliationport-Sources] {
                    append igmpRouterhandleList " [::sth::sthCore::invoke stc::get $router -children-IgmpRouterConfig]"
                }
            }
            
        }
        set resultDataSet [::sth::sthCore::invoke stc::subscribe -Parent project1 -ResultParent project1 -ResultType IgmpRouterResults -ConfigType IgmpRouterConfig]
        ::sth::sthCore::invoke stc::sleep 3
        foreach igmpRouterhandle $igmpRouterhandleList {
            set tmpResultsKeyedList ""
            set igmpRouter [::sth::sthCore::invoke stc::get $igmpRouterhandle -parent]
            set igmpRouterResultsObj [::sth::sthCore::invoke stc::get $igmpRouterhandle -children-IgmpRouterResults]
            
            if {[llength $igmpRouterResultsObj] != 0} {
                array set igmpRouterResults [::sth::sthCore::invoke stc::get $igmpRouterResultsObj]
                foreach optArg [array names userArgsArray] {
                    if {![string match "optional_args" $optArg] && ![string match "mandatory_args" $optArg]} {
                        set stcAttr [::sth::sthCore::getswitchprop ::sth::igmp:: emulation_igmp_querier_info $optArg stcattr]
                        if {![string match "_none_" $stcAttr]} {
                            keylset tmpResultsKeyedList $optArg $igmpRouterResults(-$stcAttr)
                        }
                    }
                }
            }
            keylset ResultsKeyedList $igmpRouter $tmpResultsKeyedList
        }
        if {![string match "" $resultDataSet]} {
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList results $ResultsKeyedList
    }
    return $returnKeyedList
}    
