namespace eval ::sth::twamp:: {
}
proc ::sth::twamp::emulation_twamp_config_create { returnKeyedListVarName } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        set result "The -handle is required when \"-mode create\" is used."
        return -code 1 -errorcode -1 $result
    }

    unset userArgsArray(optional_args)
    unset userArgsArray(mandatory_args)
    
    set host $userArgsArray(handle)
    set type $userArgsArray(type)
    if { $type == "client" } {
        set twampchild "TwampClientConfig"
        set procTwampName "configTwampClient"
    } else {
        set twampchild "TwampServerConfig"
        set procTwampName "configTwampServer"
    }
    set twampchildconfig [::sth::sthCore::invoke stc::create $twampchild -under $host]
    
    set ip_version $userArgsArray(ip_version)
    if {$ip_version == "ipv6"} {
        set ip6if [lindex [::sth::sthCore::invoke stc::get $host "-children-ipv6if"] 0]
        ::sth::sthCore::invoke stc::config $twampchildconfig -UsesIf-Targets $ip6if
    } else {
        set ip4if [lindex [::sth::sthCore::invoke stc::get $host "-children-ipv4if"] 0]
        ::sth::sthCore::invoke stc::config $twampchildconfig -UsesIf-Targets $ip4if 
    }
    $procTwampName $twampchildconfig create 0
    keylset returnKeyedList handle $twampchildconfig   
    return $::sth::sthCore::SUCCESS
}

proc ::sth::twamp::emulation_twamp_config_modify { returnKeyedListVarName } {
    variable userArgsArray
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        set result "The -handle is required when \"-mode modify\" is used."
        return $::sth::sthCore::FAILURE
    }
    set host $userArgsArray(handle)
    if {[set twampconfig [::sth::sthCore::invoke stc::get $host -children-TwampClientConfig ]] == ""} {  
        set twampconfig [::sth::sthCore::invoke stc::get $host -children-TwampServerConfig ]
        configTwampServer $twampconfig modify 0 
    } else {
        configTwampClient $twampconfig modify 0 
    }
    
    return $::sth::sthCore::SUCCESS
}


proc ::sth::twamp::emulation_twamp_config_delete { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::twamp::userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    
    if {(![info exists userArgsArray(handle)] || $userArgsArray(handle) == "")} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        return $returnKeyedList        
    } else {
        set host $userArgsArray(handle)
        if {[set twampconfig [::sth::sthCore::invoke stc::get $host -children-TwampClientConfig ]] == ""} {  
            set twampconfig [::sth::sthCore::invoke stc::get $host -children-TwampServerConfig ]
        }
        ::sth::sthCore::invoke stc::perform delete -ConfigList "$twampconfig"
    }
     
    keylset returnKeyedList status  $SUCCESS
    return $returnKeyedList

}
    
#################################################################
#emulation_twamp_session_config create modify and delete
#################################################################
proc ::sth::twamp::emulation_twamp_session_config_create { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        set result "The -handle is required when \"-mode create\" is used."
        return -code 1 -errorcode -1 $result
    }

    unset userArgsArray(optional_args)
    unset userArgsArray(mandatory_args)
    
    if {[info exists userArgsArray(handle)]} {
        set clientDeviceHandle $userArgsArray(handle)
        if {[set twampconfig [::sth::sthCore::invoke stc::get $clientDeviceHandle -children-TwampClientConfig ]] != ""} {  
            set TwampTestSessionHandle [::sth::sthCore::invoke stc::create TwampTestSession -under $twampconfig]
            configTwampSession $TwampTestSessionHandle create 0 
        } 
    }
    keylset returnKeyedList handle $TwampTestSessionHandle;  
    return $::sth::sthCore::SUCCESS
}

proc ::sth::twamp::emulation_twamp_session_config_modify { returnKeyedListVarName } {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        set result "The -handle is required when \"-mode modify\" is used."
        return $::sth::sthCore::FAILURE
    }
 
    configTwampSession $userArgsArray(handle) modify 0 

    keylset returnKeyedList handle $userArgsArray(handle)
    return $::sth::sthCore::SUCCESS
}


proc ::sth::twamp::emulation_twamp_session_config_delete { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    
    if {(![info exists userArgsArray(handle)] || $userArgsArray(handle) == "")} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        return $returnKeyedList        
    } else {
        foreach hdl $userArgsArray(handle) {
            ::sth::sthCore::invoke stc::perform delete -ConfigList $hdl
        }
    }
    keylset returnKeyedList status  $SUCCESS
    return $returnKeyedList

}
    

##################################################################
#Control API
#################################################################
proc ::sth::twamp::emulation_twamp_control { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    set twampconfigListServer ""
    set twampconfigList ""
    
    if {![info exists ::sth::twamp::userArgsArray(handle)] && ![info exists ::sth::twamp::userArgsArray(port_handle)]} {
        set result "The -handle or -port_handle is required for twamp control api"
        return -code 1 -errorcode -1 $result
    } 
    
    if {[info exists ::sth::twamp::userArgsArray(port_handle)]} {
        foreach port_handle $::sth::twamp::userArgsArray(port_handle) {
            set devices [::sth::sthCore::invoke stc::get $port_handle -affiliationport-Sources]
            foreach device $devices {
                if {[set twampconfig [::sth::sthCore::invoke stc::get $device -children-TwampClientConfig ]] == ""} {  
                    set twampconfig [::sth::sthCore::invoke stc::get $device -children-TwampServerConfig ]
                    append twampconfigListServer " " $twampconfig
                } else {
                    append twampconfigList " " $twampconfig
                } 
            }
        }
    } 
    
    if {[info exists ::sth::twamp::userArgsArray(handle)]} {
        set twampDeviceHandles $::sth::twamp::userArgsArray(handle)
        foreach twampHandle $twampDeviceHandles {
            if {[set twampconfig [::sth::sthCore::invoke stc::get $twampHandle -children-TwampClientConfig ]] == ""} {  
                set twampconfig [::sth::sthCore::invoke stc::get $twampHandle -children-TwampServerConfig ]
                append twampconfigListServer " " $twampconfig
            } else {
                append twampconfigList " " $twampconfig
            }    
        }
    }
	switch -- $::sth::twamp::userArgsArray(mode) {
	    start {
            if { $twampconfigListServer != "" } {
                append twampconfigList " " $twampconfigListServer
            }
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform ProtocolStartCommand -ProtocolList $twampconfigList
            }
        }
	    stop {
            if { $twampconfigListServer != "" } {
                append twampconfigList " " $twampconfigListServer
            }
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform ProtocolStopCommand -ProtocolList $twampconfigList
            }	
        }
        establish {
            if { $twampconfigListServer != "" } {
                append twampconfigList " " $twampconfigListServer
            }
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampStartHostsCommand -HandleList $twampconfigList
            }
        }
        request_twamp_sessions {
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampRequestSessionsCommand -HandleList $twampconfigList
            } 
        }
        start_twamp_sessions {
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampStartSessionsCommand -HandleList $twampconfigList -DelayTime $::sth::twamp::userArgsArray(delay_time)
            }
        }
        stop_twamp_sessions  {
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampStopSessionsCommand -HandleList $twampconfigList
            }
        }
        pause_twamp_session_traffic   {
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampPauseTestPacketsCommand -HandleList $twampconfigList
            } 
        }
        resume_twamp_session_traffic  {
            if { [ llength $twampconfigList] != 0 } {
                ::sth::sthCore::invoke stc::perform TwampResumeTestPacketsCommand -HandleList $twampconfigList
            }
        } 
       
    }
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

###############################################################
#Stats
###############################################################
proc ::sth::twamp::emulation_twamp_stats { returnKeyedListVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    
    upvar 1 $returnKeyedListVarName returnKeyedList
  
   
    switch -- $::sth::twamp::userArgsArray(mode) {
    state_summary {
            if {![info exists userArgsArray(port_handle)]} {
                set result "The -port_handle is required when \"-mode state_summary\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set port_handle $userArgsArray(port_handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType port -resulttype TwampStateSummary]
            ::sth::sthCore::invoke stc::sleep 3
            foreach portHandle $port_handle {
                set twampSummaryResults [stc::get $portHandle -children-TwampStateSummary]
                foreach hname [array names ::sth::twamp::twamp_stats_summary_stcattr] {
                set stcattr  [set ::sth::twamp::twamp_stats_summary_stcattr($hname)]
                if {[catch {set val [::sth::sthCore::invoke stc::get $twampSummaryResults -$stcattr]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $err"
                    return $returnKeyedList
                }
                keylset returnKeyedList $portHandle.$hname $val
                }
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    client {
            if {![info exists userArgsArray(handle)]} {
                set result "The -handle is required when \"-mode client\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set handles $userArgsArray(handle)
            }
            set resultDataSet [::sth::sthCore::invoke ::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType TwampClientConfig -resulttype TwampClientResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach handle $handles {
                set twampClientConfig [::sth::sthCore::invoke stc::get $handle -children-TwampClientConfig]
                set TwampClientResults [::sth::sthCore::invoke stc::get $twampClientConfig -children-TwampClientResults]
                set clientState [::sth::sthCore::invoke stc::get $twampClientConfig -state]
                keylset returnKeyedList $handle.state $clientState
                foreach hname [array names ::sth::twamp::twamp_stats_client_stcattr] {
                    set stcattr  [set ::sth::twamp::twamp_stats_client_stcattr($hname)]
                    if {[catch {set val [::sth::sthCore::invoke stc::get $TwampClientResults -$stcattr]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $returnKeyedList
                    }
                    keylset returnKeyedList $handle.$hname $val
                }
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    server {
            if {![info exists userArgsArray(handle)]} {
                set result "The -handle is required when \"-mode server\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set handles $userArgsArray(handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType TwampServerConfig -resulttype TwampServerResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach handle $handles {
                set TwampServerConfig [stc::get $handle -children-TwampServerConfig]
                set TwampServerResults [stc::get $TwampServerConfig -children-TwampServerResults]
                set serverState [stc::get $TwampServerConfig -state]
                keylset returnKeyedList $handle.state $serverState
                foreach hname [array names ::sth::twamp::twamp_stats_server_stcattr] {
                set stcattr  [set ::sth::twamp::twamp_stats_server_stcattr($hname)]
                if {[catch {set val [::sth::sthCore::invoke stc::get $TwampServerResults -$stcattr]} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $err"
                    return $returnKeyedList
                }
                keylset returnKeyedList $handle.$hname $val
                }
            }
            
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    test_session {
            if {![info exists userArgsArray(handle)]} {
                set result "The -handle is required when \"-mode test_session\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set handles $userArgsArray(handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType TwampTestSession -resulttype TwampTestSessionResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach handle $handles {
                set TwampClientConfig [::sth::sthCore::invoke stc::get $handle -children-TwampClientConfig]
                set TwampTestSession [::sth::sthCore::invoke stc::get $TwampClientConfig -children-TwampTestSession]
                set iteration 1
                foreach TwampTestSes $TwampTestSession {
                    set TwampTestSessionResults [::sth::sthCore::invoke stc::get $TwampTestSes -children-TwampTestSessionResults]
                    set sessionState [::sth::sthCore::invoke stc::get $TwampTestSes -SessionState]
                    keylset returnKeyedList $handle.$iteration.state $sessionState
                    keylset returnKeyedList $handle.$TwampTestSes.state $sessionState
                    foreach hname [array names ::sth::twamp::twamp_stats_testsession_stcattr] {
                        set stcattr  [set ::sth::twamp::twamp_stats_testsession_stcattr($hname)]
                        if {[catch {set val [::sth::sthCore::invoke stc::get $TwampTestSessionResults -$stcattr]} err]} {
                            ::sth::sthCore::processError returnKeyedList "Error: $err"
                            return $returnKeyedList
                        }
                        keylset returnKeyedList $handle.$iteration.$hname $val
                        keylset returnKeyedList $handle.$TwampTestSes.$hname $val
                    }
                    incr iteration
                }  
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    aggregated_client {
            if {![info exists userArgsArray(port_handle)]} {
                set result "The -port_handle is required when \"-mode aggregated_client\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set portHandles $userArgsArray(port_handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType port -resulttype TwampClientResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach port_handle $portHandles {
                set TwampClientResults [::sth::sthCore::invoke stc::get $port_handle -children-TwampClientResults]
                foreach TCRHandle $TwampClientResults {
                    foreach hname [array names ::sth::twamp::twamp_stats_client_stcattr] {
                        set stcattr  [set ::sth::twamp::twamp_stats_client_stcattr($hname)]
                        if {[catch {set val [::sth::sthCore::invoke stc::get $TCRHandle -$stcattr]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $returnKeyedList
                    }
                    keylset returnKeyedList $port_handle.$hname $val
                }
                }
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    aggregated_server {
            if {![info exists userArgsArray(port_handle)]} {
                set result "The -port_handle is required when \"-mode aggregated_server\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set portHandles $userArgsArray(port_handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType port -resulttype TwampServerResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach port_handle $portHandles {
                set TwampServerResults [stc::get $port_handle -children-TwampServerResults]
                foreach TCRHandle $TwampServerResults {
                    foreach hname [array names ::sth::twamp::twamp_stats_server_stcattr] {
                        set stcattr  [set ::sth::twamp::twamp_stats_server_stcattr($hname)]
                        if {[catch {set val [::sth::sthCore::invoke stc::get $TCRHandle -$stcattr]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $returnKeyedList
                    }
                    keylset returnKeyedList $port_handle.$hname $val
                }
                }
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    port_test_session {
            if {![info exists userArgsArray(port_handle)]} {
                set result "The -port_handle is required when \"-mode aggregated_server\" is used."
                return -code 1 -errorcode -1 $result
            } else {
                set portHandles $userArgsArray(port_handle)
            }
            set resultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -ConfigType Port  -resulttype TwampPortTestSessionResults]
            ::sth::sthCore::invoke stc::sleep 3
            foreach port_handle $portHandles {
                set TwampPortTestSessionResults [::sth::sthCore::invoke stc::get $port_handle -children-TwampPortTestSessionResults]
                foreach TPTSRHandle $TwampPortTestSessionResults {
                    foreach hname [array names ::sth::twamp::twamp_stats_porttestsession_stcattr] {
                        set stcattr  [set ::sth::twamp::twamp_stats_porttestsession_stcattr($hname)]
                        if {[catch {set val [::sth::sthCore::invoke stc::get $TPTSRHandle -$stcattr]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error: $err"
                        return $returnKeyedList
                    }
                    keylset returnKeyedList $port_handle.$hname $val
                }
                }
            }
            ::sth::sthCore::invoke stc::unsubscribe $resultDataSet
    }
    clear_stats {
            ::sth::sthCore::invoke stc::perform ResultsClearAllProtocol    
    }
    
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

##########################################################################
#Helper functions
##########################################################################
proc ::sth::twamp::configTwampServer {twampServerHandle mode routerIdx} {  
    set optionValueList [getStcOptionValueList emulation_twamp_config configTwampServer $mode $twampServerHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $twampServerHandle $optionValueList
    }
}

proc ::sth::twamp::configTwampClient {twampClientHandle mode routerIdx} {  
    set optionValueList [getStcOptionValueList emulation_twamp_config configTwampClient $mode $twampClientHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $twampClientHandle $optionValueList
    }
}

proc ::sth::twamp::configTwampSession {twampSessionHandle mode routerIdx} {  
    set optionValueList [getStcOptionValueList emulation_twamp_session_config configTwampSession $mode $twampSessionHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $twampSessionHandle $optionValueList
    }
}
proc ::sth::twamp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in twampTable.tcl
    foreach item $::sth::twamp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::twamp:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::twamp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::twamp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::twamp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::twamp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::twamp:: $cmdType $opt $::sth::twamp::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::twamp::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::twamp::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}


