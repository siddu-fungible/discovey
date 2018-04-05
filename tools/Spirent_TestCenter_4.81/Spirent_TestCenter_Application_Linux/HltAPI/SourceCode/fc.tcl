namespace eval ::sth::fc:: {
    array set arrayHostCurrentIfStack {}
	set autoCreateTraffic 0
}

proc ::sth::fc_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fc::sortedSwitchPriorityList
    variable ::sth::fc::userArgsArray
    array unset ::sth::fc::userArgsArray
    array set ::sth::fc::userArgsArray {}

    set _hltCmdName "fc_config"

    ::sth::sthCore::Tracker "::sth::fc_config" $args

    set returnKeyedList ""
    if {[catch {::sth::sthCore::commandInit ::sth::fc::fcTable $args ::sth::fc:: $_hltCmdName userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err"
        return $returnKeyedList
    }
    
    # Error checking
    if {![info exists userArgsArray(mode)] } {
        ::sth::sthCore::processError returnKeyedList "Error in fc_config: requires -mode"
        return $returnKeyedList 
    }
    
    foreach priPair $::sth::fc::sortedSwitchPriorityList  {
        foreach [list switchPriority switchName] $priPair {};
        # Check if this is supported or not
        if {[::sth::sthCore::getswitchprop ::sth::fc:: fc_config $switchName supported] != "TRUE"} {
            ::sth::sthCore::processError returnKeyedList "Error in fc_config: -$switchName is not a supported option"
            return $returnKeyedList 
        }
    }
   
    set mode $userArgsArray(mode)
    
    if {[catch {::sth::fc::${_hltCmdName}_${mode} returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} err ]} {
        ::sth::sthCore::processError returnKeyedList "$procName Error: $err"
        return $returnKeyedList
    }
  
    keylset returnKeyedList procName $_hltCmdName
    keylget returnKeyedList status value
    if {![info exists value]} {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::fc_control { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fc::userArgsArray
    array unset ::sth::fc::userArgsArray
    array set ::sth::fc::userArgsArray {}
    set _hltCmdName "fc_control"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    
    ::sth::sthCore::Tracker "::sth::fc_control" $args

    if {[catch {::sth::sthCore::commandInit ::sth::fc::fcTable $args ::sth::fc:: $_hltCmdName ::sth::fc::userArgsArray ::sth::fc::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error trying to initialize fc command: $err"
        return $returnKeyedList
    }

	set retVal [catch {
		# Error checking
		if {!([info exists ::sth::fc::userArgsArray(handle)] || [info exists ::sth::fc::userArgsArray(action)])} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -handle or -action."
			return $returnKeyedList
		}

		set hostList ""
		foreach host $userArgsArray(handle) {
            set hostConfig [::sth::sthCore::invoke stc::get $host "-children-fcHostConfig"]
            if {$hostConfig ne ""} {
                lappend hostList $hostConfig
            }
		}

        set fportList ""
		foreach host $userArgsArray(handle) {
            set portConfig [::sth::sthCore::invoke stc::get $host "-children-fcFPortConfig"]
            if {$portConfig ne ""} {
                lappend fportList $portConfig
            }
		}
        
		set action $userArgsArray(action) 
		switch -exact -- $action {
			login -
			logout {
				::sth::sthCore::invoke stc::perform [set ::sth::fc::${_hltCmdName}_action_fwdmap($action)] -HostList $hostList
			}
            delete {
                foreach hnd $hostList {
                    ::sth::sthCore::invoke stc::delete $hnd
                }
                foreach hnd $fportList {
                    ::sth::sthCore::invoke stc::delete $hnd
                }
            }
            start {
                ::sth::sthCore::invoke stc::perform ProtocolStartCommand -protocolList $fportList
            }
            stop {
                ::sth::sthCore::invoke stc::perform ProtocolStopCommand -protocolList $fportList
            }
		} 
		
		keylset returnKeyedList handle $userArgsArray(handle)
		keylset returnKeyedList procName fc_control
	}  returnedString]
	 
    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }

    return $returnKeyedList
}

proc ::sth::fc_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fc::userArgsArray
    array unset ::sth::fc::userArgsArray
    array set ::sth::fc::userArgsArray {}
    set _hltCmdName "fc_stats"
    
    ::sth::sthCore::Tracker "::sth::fc_stats" $args
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    

    if {[catch {::sth::sthCore::commandInit ::sth::fc::fcTable $args ::sth::fc:: $_hltCmdName ::sth::fc::userArgsArray ::sth::fc::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error trying to initialize fc command: $err"
        return $returnKeyedList
    }

	set retVal [catch {
		if {!([info exists ::sth::fc::userArgsArray(handle)] )} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -handle."
			return $returnKeyedList
		}
		foreach handle $userArgsArray(handle) {
			set fchostconfig [::sth::sthCore::invoke stc::get $handle "-children-fcHostConfig"]
            set fcfportconfig [::sth::sthCore::invoke stc::get $handle "-children-fcfPortConfig"]
			if {[regexp -nocase {all|summary} $userArgsArray(mode)] && $fchostconfig ne ""} {
				if {[catch {set fcSummaryResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fchostconfig -resulttype FcSummaryResults -configtype FcHostConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}
				after 2000
				if {[set fcSummaryResults [::sth::sthCore::invoke stc::get $fchostconfig "-children-fcSummaryResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcSummaryResults generated"
					return $returnKeyedList
				}
				foreach hname [array names ::sth::fc::fc_stats_summary_stcattr] {
					set stcattr  [set ::sth::fc::fc_stats_summary_stcattr($hname)]
					if {[catch {set val [::sth::sthCore::invoke stc::get $fcSummaryResults -$stcattr]} err]} {
						::sth::sthCore::processError returnKeyedList "Error: $err"
						return $returnKeyedList
					}
					keylset returnKeyedList $hname $val
				}
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcSummaryResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}
			}
            if {[regexp -nocase {all|discovery} $userArgsArray(mode)] && $fchostconfig ne ""} {
				if {[catch {set fcDiscoveryResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fchostconfig -resulttype FcRemoteDiscoveryResults -configtype FcHostConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}
				after 2000
				if {[set fcDiscoveryResults [::sth::sthCore::invoke stc::get $fchostconfig "-children-fcRemoteDiscoveryResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcRemoteDiscoveryResults generated"
					return $returnKeyedList
				}
                set id 0
                foreach fcDiscoveryResult [split $fcDiscoveryResults] {
                    foreach hname [array names ::sth::fc::fc_stats_discovery_stcattr] {
                        set stcattr  [set ::sth::fc::fc_stats_discovery_stcattr($hname)]
                        if {[catch {set val [::sth::sthCore::invoke stc::get $fcDiscoveryResult -$stcattr]} err]} {
                            ::sth::sthCore::processError returnKeyedList "Error: $err"
                            return $returnKeyedList
                        }
                        keylset result $hname $val
                    }
                    keylset returnKeyedList remoteDiscovery$id $result
					unset result
					incr id
                }
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcDiscoveryResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}
			}
			if {[regexp -nocase {all|nport} $userArgsArray(mode)] && $fchostconfig ne ""} {
				if {[catch {set fcnPortResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fchostconfig -resulttype FcnPortResults -configtype FcHostConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList  
				}
				after 2000
				if {[set fcnPortResults [::sth::sthCore::invoke stc::get $fchostconfig "-children-fcnPortResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcnPortResults generated"
					return $returnKeyedList  
				}
				set id 0
				foreach fcnPortResult [split $fcnPortResults] {
					foreach hname [array names ::sth::fc::fc_stats_nport_stcattr] {
						set stcattr  [set ::sth::fc::fc_stats_nport_stcattr($hname)]
						if {[catch {set val [::sth::sthCore::invoke stc::get $fcnPortResult -$stcattr]} err]} {
							::sth::sthCore::processError returnKeyedList "Error: $err"
							return $returnKeyedList
						}
						if {$hname == "fcid"} {
							set val [format %x $val]
						}
						keylset result $hname $val
					}
					keylset returnKeyedList nport$id $result
					unset result
					incr id
				}
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcnPortResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}
			}
            if {[regexp -nocase {all|^fport$} $userArgsArray(mode)] && $fcfportconfig ne ""} {
				if {[catch {set fcfPortResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fcfportconfig -resulttype FcFPortResults -configtype FcFPortConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList  
				}
				after 2000
				if {[set fcfPortResults [::sth::sthCore::invoke stc::get $fcfportconfig "-children-fcFPortResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcfPortResults generated"
					return $returnKeyedList  
				}
				set id 0
				foreach fcfPortResult [split $fcfPortResults] {
					foreach hname [array names ::sth::fc::fc_stats_fport_stcattr] {
						set stcattr  [set ::sth::fc::fc_stats_fport_stcattr($hname)]
						if {[catch {set val [::sth::sthCore::invoke stc::get $fcfPortResult -$stcattr]} err]} {
							::sth::sthCore::processError returnKeyedList "Error: $err"
							return $returnKeyedList
						}
						if {$hname == "fcid"} {
							set val [format %x $val]
						}
						keylset result $hname $val
					}
					keylset returnKeyedList fport$id $result
					unset result
					incr id
				}
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcfPortResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}                
            }
            if {[regexp -nocase {all|fportneighbor} $userArgsArray(mode)] && $fcfportconfig ne ""} {
                if {[catch {set resultDataSetHandle [::sth::sthCore::invoke stc::create ResultDataSet -under $::sth::GBLHNDMAP(project)]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::create ResultDataSet $::sth::GBLHNDMAP(project)\", errMsg: $errMsg."
                    return $returnKeyedList                 
                }
                if {[catch {set resultQueryHandle [::sth::sthCore::invoke stc::create ResultQuery -under $resultDataSetHandle "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId FcFPortConfig -ResultClassId FcFPortNeighborResults"]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::create ResultQuery $resultDataSetHandle \"-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId FcFPortConfig -ResultClassId FcFPortNeighborResults\"\", errMsg: $errMsg."
                    return $returnKeyedList                 
                }
                if {[catch {::sth::sthCore::invoke stc::perform "ResultDataSetSubscribe -ResultDataSet $resultDataSetHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while excuting \"stc::perform \"ResultDataSetSubscribe -ResultDataSet $resultDataSetHandle\"\", errMsg: $errMsg."
                    return $returnKeyedList                
                }
        
				after 1000
				if {[set fcfPortNeighborResults [::sth::sthCore::invoke stc::get $fcfportconfig "-children-FcFPortNeighborResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcfPortNeighborResults generated"
					return $returnKeyedList  
				}
				set id 0
				foreach fcfPortNResult [split $fcfPortNeighborResults] {
					foreach hname [array names ::sth::fc::fc_stats_fportneighbor_stcattr] {
						set stcattr  [set ::sth::fc::fc_stats_fportneighbor_stcattr($hname)]
						if {[catch {set val [::sth::sthCore::invoke stc::get $fcfPortNResult -$stcattr]} err]} {
							::sth::sthCore::processError returnKeyedList "Error: $err"
							return $returnKeyedList
						}
						if {$hname == "fcid"} {
							set val [format %x $val]
						}
						keylset result $hname $val
					}
					keylset returnKeyedList fport$id $result
					unset result
					incr id
				}
				if {[catch {::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSetHandle} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err"
					return $returnKeyedList
				}      
            }
			keylset returnKeyedList handle $handle
		}
		keylset returnKeyedList procName fc_stats
	} returnedString]
	
    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }

    return $returnKeyedList
}

