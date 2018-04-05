namespace eval ::sth::l2tpv3:: {
}

proc ::sth::l2tpv3_config { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tpv3_config" $args
    set procName [lindex [info level [info level]] 0]
    
    variable ::sth::l2tpv3::sortedSwitchPriorityList
    variable ::sth::l2tpv3::userArgsArray
    array unset ::sth::l2tpv3::userArgsArray
    array set ::sth::l2tpv3::userArgsArray {}

    set returnKeyedList ""
    #keylset returnKeyedList procName "l2tp_config"
    #keylset returnKeyedList status $::sth::sthCore::FAILURE
    if {[catch {::sth::sthCore::commandInit ::sth::l2tpv3::l2tpv3Table $args \
							::sth::l2tpv3:: \
							l2tpv3_config \
							::sth::l2tpv3::userArgsArray \
							::sth::l2tpv3::sortedSwitchPriorityList} eMsg]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
		return $returnKeyedList
    }
    

    foreach priPair $::sth::l2tpv3::sortedSwitchPriorityList  {
        foreach [list switchPriority switchName] $priPair {};
        # Check if this is supported or not
        if {[::sth::sthCore::getswitchprop ::sth::l2tpv3:: l2tpv3_config $switchName supported] != "TRUE"} {
            ::sth::sthCore::processError returnKeyedList "Error in l2tpv3_config: -$switchName is not a supported option"
            return $returnKeyedList 
        }
    }
   
    set modeValue  $::sth::l2tpv3::userArgsArray(mode)
    
    switch -exact $modeValue {
        create {
            
            set cmd "::sth::l2tpv3::l2tpConfigPortSessionBlock\_$modeValue returnKeyedList"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
            
        modify {
            set cmd "::sth::l2tpv3::l2tpConfigPortSessionBlock\_$modeValue {$args} returnKeyedList"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        delete {
            set cmd "::sth::l2tpv3::l2tpConfigPortSessionBlock\_$modeValue returnKeyedList"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList
        }
    }
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    if {[catch {::sth::sthCore::doStcApply } err ]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $err"
            return $returnKeyedList 
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::l2tpv3_control { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tpv3_control" $args
    set procName [lindex [info level [info level]] 0]
     
    
    variable ::sth::l2tpv3::sortedSwitchPriorityList
    variable ::sth::l2tpv3::userArgsArray
    array unset ::sth::l2tpv3::userArgsArray
    array set ::sth::l2tpv3::userArgsArray {}

    set returnKeyedList ""
    keylset returnKeyedList procName "l2tpv3_control"
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::l2tpv3::l2tpv3Table $args ::sth::l2tpv3:: l2tpv3_control ::sth::l2tpv3::userArgsArray ::sth::l2tpv3::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore $procName commandInit Failed: $err"
        return $returnKeyedList 
    }

    set retVal [catch {
        set l2tpHandleList ""
    
        foreach host $userArgsArray(handle) {
            set l2tpv3BlockConfig [::sth::sthCore::invoke stc::get $host -children-L2tpv3BlockConfig]
            if {$l2tpv3BlockConfig != ""} { lappend l2tpHandleList $l2tpv3BlockConfig}
        }
        
        
    
        set action $userArgsArray(action)
        switch -exact -- $action {
            
            retry -
            connect {
                set gSystem system1
                set gProject [::sth::sthCore::invoke stc::get $gSystem -children-project]
                set gPortList [::sth::sthCore::invoke stc::get $gProject -children-port]
                
                set ret [::sth::sthCore::invoke stc::perform ArpNdStartOnAllDevices -portlist $gPortList]
                set ret [::sth::sthCore::invoke stc::perform L2tpConnectCommand -BlockList $l2tpHandleList]
                ::sth::sthCore::invoke stc::sleep 3
                set ret [::sth::sthCore::invoke stc::perform L2tpv3RetryCommand -BlockList $l2tpHandleList -ControlType $action ]
            }
            
            terminate -
            disconnect {
                set ret [::sth::sthCore::invoke stc::perform L2tpDisconnectCommand -BlockList $l2tpHandleList]
                ::sth::sthCore::invoke stc::sleep 3
                set ret [::sth::sthCore::invoke stc::perform L2tpv3RetryCommand -BlockList $l2tpHandleList -ControlType $action]
                
            }
            
            default {
                ::sth::sthCore::processError returnKeyedList "$procName: Unknown Value for -action Value: $action."
                return $returnKeyedList
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


proc ::sth::l2tpv3_stats { args } {
    ::sth::sthCore::Tracker :: "::sth::l2tpv3_stats" $args
    set procName [lindex [info level [info level]] 0]

    variable ::sth::l2tpv3::sortedSwitchPriorityList
    variable ::sth::l2tpv3::userArgsArray
    array unset ::sth::l2tpv3::userArgsArray
    array set ::sth::l2tpv3::userArgsArray {}


    set returnKeyedList ""
    keylset returnKeyedList procName "l2tpv3_stats"
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::l2tpv3::l2tpv3Table $args ::sth::l2tpv3:: l2tpv3_stats ::sth::l2tpv3::userArgsArray ::sth::l2tpv3::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore $procName commandInit Failed: $err"
        return $returnKeyedList 
    }

    set retVal [catch {
        set modeVal $userArgsArray(mode)
    
        foreach handle $userArgsArray(handle) {
            keylset returnKeyedList handles $userArgsArray(handle)
        
            set l2tpBlockConfig  [::sth::sthCore::invoke stc::get $handle -children-L2tpv3BlockConfig]
            set l2tpBlockResult [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv3BlockResults]
           
            
            set l2tpPortConfig [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $handle -affiliationport-targets] -children-L2tpPortConfig]
            set l2tpPortResult [::sth::sthCore::invoke stc::get $l2tpPortConfig -children-L2tpPortResults]
            
            switch -exact -- $modeVal {
                aggregate {
                    foreach name [array names ::sth::l2tpv3::l2tpv3_stats_${modeVal}_stcattr] {
                        set procFunc [set ::sth::l2tpv3::l2tpv3_stats_${modeVal}_procfunc($name)]
                        set action [set ::sth::l2tpv3::l2tpv3_stats_${modeVal}_action($name)]
                        if {$procFunc == "_none_"} { continue }
                        if {$action == "PortResult"} {
                            set porcessHandle $l2tpPortResult
                        } elseif { $action == "l2tpv3Result"} {
                            set porcessHandle $l2tpBlockResult
                        } else {
                            continue
                        }
                        if {$porcessHandle != ""} { 
                            if {[catch {::sth::l2tpv3::$procFunc $name returnKeyedList ${modeVal} $porcessHandle} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return $returnKeyedList 
                            }
                        }
                    }
                    ###Set the port state
                    if {[catch { ::sth::l2tpv3::processl2tpv3GetCmd_state "" returnKeyedList ${modeVal} $l2tpPortConfig } err]} {
                        #puts "22 $procName fetching key(portState) Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "$procName fetching key(portState) Failed: $err"
                        return $returnKeyedList
                    }
                }
               
                session {
                    ::sth::sthCore::invoke stc::perform L2tpSessionInfo -BlockList $l2tpBlockConfig -saveToFile FALSE
                    set sessionResults [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv3SessionResults ]
                    foreach sessionResult $sessionResults {
                        if {[catch { set curL2tpTunnelId [::sth::sthCore::invoke stc::get $sessionResult -TunnelId ] } err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName Could not retrieve L2TP Tunnel ID for session stats: $err"
                                return -code error $returnKeyedList
                        }
                        set curL2tpSessionId [::sth::sthCore::invoke stc::get $sessionResult -SessionId]
                        
                        foreach name [array names ::sth::l2tpv3::l2tpv3_stats_${modeVal}_stcattr] {
                            
                            set procFunc [set ::sth::l2tpv3::l2tpv3_stats_${modeVal}_procfunc($name)]
                            if {$procFunc == "_none_"} {continue}
                             
                            if {[catch {::sth::l2tpv3::$procFunc $name returnKeyedList ${modeVal} $curL2tpTunnelId $curL2tpSessionId $sessionResult} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return -code error $returnKeyedList 
                            }
                        }
                    }
                }
                tunnel {
                    ::sth::sthCore::invoke stc::perform L2tpTunnelInfo -BlockList $l2tpBlockConfig -saveToFile FALSE
                    set tunnelResults [::sth::sthCore::invoke stc::get $l2tpBlockConfig -children-L2tpv3TunnelResults  ]
                    foreach runnelResult $tunnelResults {
                        if {[catch { set curL2tpTunnelId [::sth::sthCore::invoke stc::get $runnelResult -TunnelId ] } err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName Could not retrieve L2TP Tunnel ID for session stats: $err"
                                return -code error $returnKeyedList
                        }
                        
                        foreach name [array names ::sth::l2tpv3::l2tpv3_stats_${modeVal}_stcattr] {        
                            set procFunc [set ::sth::l2tpv3::l2tpv3_stats_${modeVal}_procfunc($name)]
                            if {$procFunc == "_none_"} {continue}
                                 
                            if {[catch {::sth::l2tpv3::$procFunc $name returnKeyedList ${modeVal} $curL2tpTunnelId $runnelResult} err]} {
                                ::sth::sthCore::processError returnKeyedList "$procName $procFunc Failed: $err"
                                return  $returnKeyedList 
                            }
                        }
                    }
                }
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
