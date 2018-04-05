namespace eval ::sth::l2tp:: {
}

proc ::sth::l2tp_config { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tp_config" $args
    set procName [lindex [info level [info level]] 0]
    
    variable ::sth::l2tp::sortedSwitchPriorityList
    variable ::sth::l2tp::userArgsArray
    array unset ::sth::l2tp::userArgsArray
    array set ::sth::l2tp::userArgsArray {}

    set returnKeyedList ""
    keylset returnKeyedList procName "l2tp_config"
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::l2tp::l2tpTable $args ::sth::l2tp:: l2tp_config ::sth::l2tp::userArgsArray ::sth::l2tp::sortedSwitchPriorityList} err]} {
        keylset returnKeyedList log "Error in $procName: $err"
        return $returnKeyedList
    }

    foreach priPair $::sth::l2tp::sortedSwitchPriorityList  {
        foreach [list switchPriority switchName] $priPair {};
        # Check if this is supported or not
        if {[::sth::sthCore::getswitchprop ::sth::l2tp:: l2tp_config $switchName supported] != "TRUE"} {
            ::sth::sthCore::processError returnKeyedList "Error in l2tp_config: -$switchName is not a supported option"
            return $returnKeyedList 
        }
    }
   
    if {[catch {::sth::l2tp::l2tpConfigPortSessionBlock returnKeyedList} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::l2tp::l2tpConfigPortSessionBlock Failed: $err"
            return $returnKeyedList 
    }

    if {[catch {::sth::sthCore::doStcApply } err ]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err"
            return $returnKeyedList 
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::l2tp_control { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tp_control" $args
    set procName [lindex [info level [info level]] 0]
     
    
    variable ::sth::l2tp::sortedSwitchPriorityList
    variable ::sth::l2tp::userArgsArray
    array unset ::sth::l2tp::userArgsArray
    array set ::sth::l2tp::userArgsArray {}

    set returnKeyedList ""
    keylset returnKeyedList procName "l2tp_control"
    keylset returnKeyedList status $::sth::sthCore::FAILURE
	
    if {[catch {::sth::sthCore::commandInit ::sth::l2tp::l2tpTable $args ::sth::l2tp:: l2tp_control ::sth::l2tp::userArgsArray ::sth::l2tp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore $procName commandInit Failed: $err"
        return $returnKeyedList 
    }

    set retVal [catch {
        set pppHandleList ""
        set l2tpHandleList ""
		set pppHandleListServer ""
		set pppHandleListClient ""
		
        foreach host $userArgsArray(handle) {
		
            set l2tpv2BlockConfig [::sth::sthCore::invoke stc::get $host -children-L2tpv2BlockConfig]
            set pppoL2tpv2BlockConfig [::sth::sthCore::invoke stc::get $host -children-PppoL2tpv2ServerBlockConfig]
            if {$pppoL2tpv2BlockConfig == ""} {
                set pppoL2tpv2BlockConfig [::sth::sthCore::invoke stc::get $host -children-PppoL2tpv2ClientBlockConfig]
            }
		
			if {$pppoL2tpv2BlockConfig != ""} { 
				if {[regexp -nocase "server" $pppoL2tpv2BlockConfig]} {
					lappend pppHandleListServer $pppoL2tpv2BlockConfig
				}
				if {[regexp -nocase "client" $pppoL2tpv2BlockConfig]} {
					lappend pppHandleListClient $pppoL2tpv2BlockConfig
				}	
			}
			if {$l2tpv2BlockConfig != ""} {
				lappend l2tpHandleList $l2tpv2BlockConfig
			}
		}

		#passing server handle as a first one; to start server then client.
		set pppHandleList "[concat $pppHandleListServer  $pppHandleListClient]"

        set action $userArgsArray(action)
        switch -exact -- $action {
            
            retry -
            connect {
                set gSystem system1
                set gProject [::sth::sthCore::invoke stc::get $gSystem -children-project]
                set gPortList [::sth::sthCore::invoke stc::get $gProject -children-port]
                
                set ret [::sth::sthCore::invoke stc::perform ArpNdStartOnAllDevices -portlist $gPortList]
                set command [::sth::sthCore::getModeFunc ::sth::l2tp:: l2tp_control action ${action}_pppox]
                set ret [::sth::sthCore::invoke stc::perform $command -BlockList $pppHandleList]
            }
            
            reset -
            abort -
            pause -
            resume -
            clear -
            disconnect {
                set command [::sth::sthCore::getModeFunc ::sth::l2tp:: l2tp_control action ${action}_pppox]
                set ret [::sth::sthCore::invoke stc::perform $command -BlockList $pppHandleList]
                
            }
            
            SHA_NO_USER_INPUT {
                ::sth::sthCore::processError returnKeyedList "$procName: No Value for -action Value: $action."
                return $returnKeyedList
            }
            SHA_UNKNWN_SWITCH -
            default {
                ::sth::sthCore::processError returnKeyedList "$procName: Unknown Value for -action Value: $action."
                return $returnKeyedList
            }
        }
    
        #if {$actionValue == "clear"} {
        #    # Delay to allow time for stats to clear
        #    # May need to make value dependent on number of hosts, sessions, etc.
        #    after 5000
        #}
        
        if {$action == "reset"} {
            foreach host $userArgsArray(handle) {
                set handle [::sth::sthCore::invoke stc::get $host -affiliationport-targets]
                set l2tpblockconfig [::sth::sthCore::invoke stc::get $host -children-l2tpv2blockconfig]
                ::sth::sthCore::invoke stc::delete $host
                foreach streamblock [::sth::sthCore::invoke stc::get $handle -Children-StreamBlock ] {
                    set sb_dstbding [::sth::sthCore::invoke stc::get $streamblock -DstBinding-targets]
                    set sb_srcbding [::sth::sthCore::invoke stc::get $streamblock -SrcBinding-targets]
                    if {($sb_dstbding == "" )|| ($sb_srcbding == "")} {
                        ::sth::sthCore::invoke stc::delete $streamblock
                    }
                }
            }
        }
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


proc ::sth::l2tp_stats { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tp_stats" $args
    set procName [lindex [info level [info level]] 0]

    variable ::sth::l2tp::sortedSwitchPriorityList
    variable ::sth::l2tp::userArgsArray
    array unset ::sth::l2tp::userArgsArray
    array set ::sth::l2tp::userArgsArray {}


    set returnKeyedList ""
    keylset returnKeyedList procName "l2tp_status"
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::l2tp::l2tpTable $args ::sth::l2tp:: l2tp_stats ::sth::l2tp::userArgsArray ::sth::l2tp::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore $procName commandInit Failed: $err"
        return $returnKeyedList 
    }

    set retVal [catch {
        set modeVal $userArgsArray(mode)
    
        foreach handle $userArgsArray(handle) {
            keylset returnKeyedList handles $userArgsArray(handle)
        
            set l2tpBlockConfig  [::sth::sthCore::invoke stc::get $handle -children-L2tpv2BlockConfig]
            set l2tpBlockResult [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv2BlockResults]
            
            set pppol2tpv2clientblockconfig [::sth::sthCore::invoke stc::get $handle -children-pppol2tpv2clientblockconfig]
            if {$pppol2tpv2clientblockconfig == ""} {
                set pppoxBlockResult [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $handle -children-pppol2tpv2serverblockconfig] -children-pppserverblockresults]
            } else {
                set pppoxBlockResult [::sth::sthCore::invoke stc::get $pppol2tpv2clientblockconfig -children-pppclientblockresults]
            }
            
            set l2tpPortConfig [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $handle -affiliationport-targets] -children-L2tpPortConfig]
            set l2tpPortResult [::sth::sthCore::invoke stc::get $l2tpPortConfig -children-L2tpPortResults]
            
            switch -exact -- $modeVal {
                aggregate {
                    foreach name [array names ::sth::l2tp::l2tp_stats_${modeVal}_stcattr] {
                        set procFunc [set ::sth::l2tp::l2tp_stats_${modeVal}_procfunc($name)]
                        set action [set ::sth::l2tp::l2tp_stats_${modeVal}_action($name)]
                        if {$procFunc == "_none_"} { continue }
                        if {$action == "PortResult"} {
                            set porcessHandle $l2tpPortResult
                        } elseif { $action == "L2tpResult"} {
                            set porcessHandle $l2tpBlockResult
                        } elseif { $action == "PppoxBlock"} {
                            set porcessHandle [::sth::sthCore::invoke stc::get $pppoxBlockResult -parent]
                        } elseif { $action == "PppoxResult" || ($action == "PppoxClientResult" && [regexp -nocase "client" $pppoxBlockResult ]) } {
                            set porcessHandle $pppoxBlockResult
                        } else {
                            continue
                        }
                        if {$porcessHandle != ""} { 
                            if {[catch {::sth::l2tp::$procFunc $name returnKeyedList ${modeVal} $porcessHandle} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return $returnKeyedList 
                            }
                        }
                    }
                    ###Set the port state
                    if {[catch { ::sth::l2tp::processL2TPGetCmd_state "" returnKeyedList ${modeVal} $l2tpPortConfig } err]} {
                        #puts "22 $procName fetching key(portState) Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "$procName fetching key(portState) Failed: $err"
                        return $returnKeyedList
                    }
                }
               
                session {
                    ::sth::sthCore::invoke stc::perform L2tpSessionInfo -BlockList $l2tpBlockConfig -saveToFile FALSE
                    set sessionResults [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv2SessionResults ]
                    foreach sessionResult $sessionResults {
                        if {[catch { set curL2tpTunnelId [::sth::sthCore::invoke stc::get $sessionResult -TunnelId ] } err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName Could not retrieve L2TP Tunnel ID for session stats: $err"
                                return -code error $returnKeyedList
                        }
                        set curL2tpSessionId [::sth::sthCore::invoke stc::get $sessionResult -SessionId]
                        
                        foreach name [array names ::sth::l2tp::l2tp_stats_${modeVal}_stcattr] {
                            
                            set procFunc [set ::sth::l2tp::l2tp_stats_${modeVal}_procfunc($name)]
                            if {$procFunc == "_none_"} {continue}
                             
                            if {[catch {::sth::l2tp::$procFunc $name returnKeyedList ${modeVal} $curL2tpTunnelId $curL2tpSessionId $sessionResult} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return -code error $returnKeyedList 
                            }
                        }
                    }
                }
                tunnel {
                    ::sth::sthCore::invoke stc::perform L2tpTunnelInfo -BlockList $l2tpBlockConfig -saveToFile FALSE
                    set tunnelResults [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv2TunnelResults  ]
                    foreach runnelResult $tunnelResults {
                        if {[catch { set curL2tpTunnelId [::sth::sthCore::invoke stc::get $runnelResult -TunnelId ] } err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName Could not retrieve L2TP Tunnel ID for session stats: $err"
                                return -code error $returnKeyedList
                        }
                        
                        foreach name [array names ::sth::l2tp::l2tp_stats_${modeVal}_stcattr] {        
                            set procFunc [set ::sth::l2tp::l2tp_stats_${modeVal}_procfunc($name)]
                            if {$procFunc == "_none_"} {continue}
                                 
                            if {[catch {::sth::l2tp::$procFunc $name returnKeyedList ${modeVal} $curL2tpTunnelId $runnelResult} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return  $returnKeyedList 
                            }
                        }
                    }
                }
                SHA_NO_USER_INPUT {
                    ::sth::sthCore::processError returnKeyedList "$procName: No Value for the switch: mode Value:$modeVal."
                    return  $returnKeyedList 
                }
                SHA_UNKNWN_SWITCH -
                default {
                    ::sth::sthCore::processError returnKeyedList "$procName: Unable to process -mode value: $modeVal."
                    return  $returnKeyedList 
                }
            }
        }
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
