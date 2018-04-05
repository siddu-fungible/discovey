namespace eval ::sth::fcoe:: {
    array set arrayHostCurrentIfStack {}
}

proc ::sth::fcoe_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fcoe::sortedSwitchPriorityList
    variable ::sth::fcoe::userArgsArray
    array unset ::sth::fcoe::userArgsArray
    array set ::sth::fcoe::userArgsArray {}

    set _hltCmdName "fcoe_config"

    ::sth::sthCore::Tracker "::sth::fcoe_config" $args

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::fcoe::fcoeTable $args ::sth::fcoe:: $_hltCmdName userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "$procName Error: $err" {}
        return $returnKeyedList
    }
    
	set retVal [catch {
		foreach priPair $::sth::fcoe::sortedSwitchPriorityList  {
			foreach [list switchPriority switchName] $priPair {};
			# Check if this is supported or not
			if {[::sth::sthCore::getswitchprop ::sth::fcoe:: fcoe_config $switchName supported] != "TRUE"} {
				::sth::sthCore::processError returnKeyedList "Error in fcoe_config: -$switchName is not a supported option"
				return $returnKeyedList 
			}
		}
	   
		set mode $userArgsArray(mode)
		
		#This is for back compatibility
		foreach {new old} {vlan_pri_outer vlan_user_priority_outer vlan_pri vlan_user_priority vnport_count device_count} {
			if {[info exists userArgsArray($old)]} {
				set userArgsArray($new) $userArgsArray($old)
				lappend ::sth::fcoe::sortedSwitchPriorityList [list 100 $new]
			}
		}
		
		if {[catch {::sth::fcoe::${_hltCmdName}_${mode} returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err" {}
			return $returnKeyedList
		}

		if {[catch {::sth::sthCore::doStcApply } err ]} {
			::sth::sthCore::processError returnKeyedList "$procName Error: $err" {}
			return $returnKeyedList
		}
		keylset returnKeyedList procName $_hltCmdName
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

proc ::sth::fcoe_control { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fcoe::userArgsArray
    array unset ::sth::fcoe::userArgsArray
    array set ::sth::fcoe::userArgsArray {}
    set _hltCmdName "fcoe_control"
    
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    
    ::sth::sthCore::Tracker "::sth::fcoe_control" $args

    if {[catch {::sth::sthCore::commandInit ::sth::fcoe::fcoeTable $args ::sth::fcoe:: $_hltCmdName ::sth::fcoe::userArgsArray ::sth::fcoe::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error trying to initialize fcoe command: $err" {}
        return $returnKeyedList
    }
    
	set retVal [catch {
		set handleList ""
		foreach host $userArgsArray(handle) {
			lappend handleList [::sth::sthCore::invoke stc::get $host "-children-FcoeHostConfig"]
		}

		set action $userArgsArray(action) 
		switch -exact -- $action {
			discovery -
			login -
			logout -
			start -
			stop {
				::sth::sthCore::invoke stc::perform [set ::sth::fcoe::${_hltCmdName}_action_fwdmap($action)] -HostList $handleList
			}
		}
		keylset returnKeyedList handle $userArgsArray(handle)
		keylset returnKeyedList procName fcoe_control
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

proc ::sth::fcoe_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::fcoe::userArgsArray
    array unset ::sth::fcoe::userArgsArray
    array set ::sth::fcoe::userArgsArray {}
    set _hltCmdName "fcoe_stats"
    
    ::sth::sthCore::Tracker "::sth::fcoe_stats" $args
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE
    

    if {[catch {::sth::sthCore::commandInit ::sth::fcoe::fcoeTable $args ::sth::fcoe:: $_hltCmdName ::sth::fcoe::userArgsArray ::sth::fcoe::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error trying to initialize fcoe command: $err" {}
        return $returnKeyedList
    }
    
	set retVal [catch {
		foreach handle $userArgsArray(handle) {
			set handlelist  ""
			set fcoehostconfig [::sth::sthCore::invoke stc::get $handle "-children-FcoeHostConfig"]
			if {[regexp -nocase {all|summary} $userArgsArray(mode)]} {
				if {[catch {set fcoeSummaryResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fcoehostconfig -resulttype FcoeSummaryResults  -configtype FcoeHostConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err" {}
					return $returnKeyedList
				}
				after 2000
				if {[set fcoeSummaryResults [::sth::sthCore::invoke stc::get $fcoehostconfig "-children-FcoeSummaryResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcoeSummaryResults generated" {}
					return $returnKeyedList
				}
				foreach hname [array names ::sth::fcoe::fcoe_stats_summary_stcattr] {
					set stcattr  [set ::sth::fcoe::fcoe_stats_summary_stcattr($hname)]
					if {[catch {set val [::sth::sthCore::invoke stc::get $fcoeSummaryResults -$stcattr]} err]} {
						::sth::sthCore::processError returnKeyedList "$procName Err: $err" {}
						return $returnKeyedList
					}
					keylset returnKeyedList $hname $val
				}
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcoeSummaryResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err" {}
					return $returnKeyedList
				}
			}
			if {[regexp -nocase {all|vnport} $userArgsArray(mode)]} {
				if {[catch {set fcoeVnPortResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $fcoehostconfig -resulttype FcoeVnPortResults  -configtype FcoeHostConfig]} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err" {}
					return $returnKeyedList  
				}
				after 2000
				if {[set fcoeVnPortResults [::sth::sthCore::invoke stc::get $fcoehostconfig "-children-FcoeVnPortResults"]] == ""} {
					::sth::sthCore::processError returnKeyedList "$procName Err: no fcoeVnPortResults generated" {}
					return $returnKeyedList  
				}
				set id 0
				foreach fcoeVnPortResult [split $fcoeVnPortResults] {
					foreach hname [array names ::sth::fcoe::fcoe_stats_vnport_stcattr] {
						set stcattr  [set ::sth::fcoe::fcoe_stats_vnport_stcattr($hname)]
						if {[catch {set val [::sth::sthCore::invoke stc::get $fcoeVnPortResult -$stcattr]} err]} {
							::sth::sthCore::processError returnKeyedList "Error: $err" {}
							return $returnKeyedList
						}
						if {$hname == "fcid"} {
							set val [format %x $val]
						}
						keylset result $hname $val
					}
					keylset returnKeyedList vnport$id $result
					unset result
					incr id
				}
				if {[catch {::sth::sthCore::invoke stc::unsubscribe $fcoeVnPortResultDataSet} err]} {
					::sth::sthCore::processError returnKeyedList "$procName Err: $err" {}
					return $returnKeyedList
				}
			}
			keylset returnKeyedList handle $handle
		}

		keylset returnKeyedList procName $procName
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

