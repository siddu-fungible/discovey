namespace eval ::sth::microBfd {

}

proc ::sth::microBfd::emulation_micro_bfd_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_micro_bfd_config_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::microBfd::userArgsArray

    set retVal [catch {
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle is required when \"-mode create\" is used."
            return $returnKeyedList
        }

        set bfdHnd [::sth::sthCore::invoke stc::create LagBfdPortConfig -under $portHandle]
        set lagHnd [::sth::sthCore::invoke stc::get $portHandle -portsetmember-Sources]
        set grpHnd [::sth::sthCore::invoke stc::get $lagHnd -children-LagBfdGroupConfig]
        if {$grpHnd eq ""} {
            set grpHnd [::sth::sthCore::invoke stc::create LagBfdGroupConfig -under $lagHnd]
        }
        ::sth::sthCore::invoke stc::config $bfdHnd -MemberOfLag-targets $grpHnd
        set authHnd [::sth::sthCore::invoke stc::get $bfdHnd -children-BfdAuthenticationParams]

        #### Config input switches ####
        ::sth::microBfd::processConfigSwitches emulation_micro_bfd_config $bfdHnd create returnKeyedList
        
        #apply all configurations
        ::sth::sthCore::doStcApply

    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList handle $bfdHnd
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::microBfd::emulation_micro_bfd_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_micro_bfd_config_modify"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::microBfd::userArgsArray

    set retVal [catch {
       # handle is mandatory for the -mode modify
        if {[info exists userArgsArray(handle)]} {
            set handle $userArgsArray(handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -handle is required when \"-mode modify\" is used."
            return $returnKeyedList
        }

        #### Config input switches ####
        ::sth::microBfd::processConfigSwitches emulation_micro_bfd_config $handle modify returnKeyedList
        
    } returnedString]

    if {$retVal} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::microBfd::emulation_micro_bfd_config_reset { returnKeyedListVarName } {

    variable ::sth::microBfd::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }

        set deviceHandleList $userArgsArray(handle)
        ::sth::sthCore::invoke stc::perform delete -configList $deviceHandleList

    } returnedString]

    if {$retVal} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::microBfd::emulation_micro_bfd_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_micro_bfd_control_action"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::microBfd::userArgsArray
    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    set lagBfdHandleList ""
    if {[info exists ::sth::microBfd::userArgsArray(handle)]} {
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className LagBfdPortConfig -rootlist $::sth::microBfd::userArgsArray(handle)]
		set lagBfdHandleList $rtn(-ObjectList)
    } elseif {[info exists ::sth::microBfd::userArgsArray(port_handle)]} {
		set port_list $::sth::microBfd::userArgsArray(port_handle)
        array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className LagBfdPortConfig -rootlist $port_list]
        append lagBfdHandleList " $rtn(-ObjectList)"
    }

    switch -exact -- $::sth::microBfd::userArgsArray(action) {
        "start" {
            ::sth::sthCore::invoke stc::perform ProtocolStartCommand -ProtocolList $lagBfdHandleList
        }
        "stop" {
            ::sth::sthCore::invoke stc::perform ProtocolStopCommand -ProtocolList $lagBfdHandleList
        }
        "delete" {
            ::sth::sthCore::invoke stc::perform DeleteCommand -ConfigList $lagBfdHandleList
        }
        "admin_up" {
            ::sth::sthCore::invoke stc::perform BfdAdminUpCommand -ObjectList $lagBfdHandleList
        }
        "admin_down" {
            ::sth::sthCore::invoke stc::perform BfdAdminDownCommand -ObjectList $lagBfdHandleList
        }
        "initiate_poll" {
            ::sth::sthCore::invoke stc::perform BfdInitiatePollCommand -ObjectList $lagBfdHandleList
        }
        "resume_pdus" {
            ::sth::sthCore::invoke stc::perform BfdResumePdusCommand -ObjectList $lagBfdHandleList
        }
        "stop_pdus" {
            ::sth::sthCore::invoke stc::perform BfdStopPdusCommand -ObjectList $lagBfdHandleList
        }
        "set_diagnostic_state" {
            ::sth::sthCore::invoke stc::perform BfdSetDiagnosticStateCommand -ObjectList $lagBfdHandleList -BfdDiagnosticCode $::sth::microBfd::userArgsArray(bfd_diagnostic_code)
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown action $::sth::microBfd::userArgsArray(action)."
            return -code error $returnKeyedList
        }
    }
    
    return $returnKeyedList
}

proc ::sth::microBfd::emulation_micro_bfd_info_func {myreturnKeyedList} {
    upvar $myreturnKeyedList returnKeyedList
    variable ::sth::microBfd::userArgsArray

    set lagBfdHandleList ""
    if {[info exists ::sth::microBfd::userArgsArray(handle)]} {
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className LagBfdPortConfig -rootlist $::sth::microBfd::userArgsArray(handle)]
		set lagBfdHandleList $rtn(-ObjectList)
    } elseif {[info exists ::sth::microBfd::userArgsArray(port_handle)]} {
		set port_list $::sth::microBfd::userArgsArray(port_handle)
        array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className LagBfdPortConfig -rootlist $port_list]
        append lagBfdHandleList " $rtn(-ObjectList)"
    }

    #subscribe
    set resultDataSet [::sth::microBfd::subscribeObjects $::sth::microBfd::userArgsArray(mode) $lagBfdHandleList]
    
    #get results
    ::sth::microBfd::getResults $resultDataSet
    
    #unsubscribe    
    ::sth::sthCore::invoke stc::perform ResultDataSetUnSubscribe -ResultDataSet $resultDataSet
    ::sth::sthCore::invoke stc::perform delete -configlist $resultDataSet
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList

}

proc ::sth::microBfd::subscribeObjects {modeList configHnd} {
    upvar userArgsArray userArgsArray;

    #Create Single resultdatatset
    set resultDataSet [sth::sthCore::invoke stc::create ResultDataSet -under project1]

    #Create differet result queries based on different modes
    foreach mode [split $modeList |]  {
        set configResultClass [::sth::microBfd::getConfigResultClass $mode]
        sth::sthCore::invoke "stc::create ResultQuery -under $resultDataSet -ResultRootList \{$configHnd\} -ConfigClassId [lindex $configResultClass 0] -ResultClassId [lindex $configResultClass 1]"
    }

    sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    sth::sthCore::invoke stc::sleep 3

    return $resultDataSet
}

proc ::sth::microBfd::getConfigResultClass {mode} {
    set resultObj ""

    switch -exact $mode { 
        port {
            set resultObj "LagBfdPortConfig LagBfdPortResults"
        }
        session {
            set resultObj "LagBfdPortConfig LagBfdPortIpv4SessionResults"
        }
    }

    return $resultObj
}

proc ::sth::microBfd::getResults {resultDataSet} {
    upvar returnKeyedList returnKeyedList
    variable ::sth::sthCore::SUCCESS;
    variable ::sth::sthCore::FAILURE;
    set totalPage 1

    set totalPage [sth::sthCore::invoke stc::get $resultDataSet -TotalPageCount]
    
    #Getting mapping the native and hlt return keys/values
    for {set pageNumber 1} { $pageNumber <= $totalPage} {incr pageNumber} {
        
        if {$pageNumber > 1} {
            sth::sthCore::invoke stc::config $resultDataSet -pageNumber $pageNumber
            sth::sthCore::invoke stc::apply
            sth::sthCore::invoke stc::perform RefreshResultViewCommand -ResultDataSet $resultDataSet
            sth::sthCore::invoke stc::sleep 2
        }

        set resultHndLists [sth::sthCore::invoke stc::get $resultDataSet -ResultHandleList]

        foreach resultHnd $resultHndLists {
            array set hnd [sth::sthCore::invoke stc::get $resultHnd]
            if {[regexp -nocase "LagBfdPortResults" $resultHnd]} {
                ::sth::microBfd::updateLagBfdStats [array get hnd] $resultHnd "port"
            } elseif {[regexp -nocase "LagBfdPortIpv4SessionResults" $resultHnd]} {
                ::sth::microBfd::updateLagBfdStats [array get hnd] $resultHnd "session"
            }
        }
    }

    return $returnKeyedList
}

proc ::sth::microBfd::updateLagBfdStats {resultVal resultHnd type} {
    upvar userArgsArray userArgsArray;
    upvar returnKeyedList returnKeyedList
    
    array set hnd $resultVal
    set key "$type.$hnd(-parent)"

    #Getting mapping the native and hlt return keys/values
    set TableName ::sth::microBfd::emulation_micro_bfd_info_$type\_stcattr
    set hltOptionList [array names $TableName]

    foreach hltName $hltOptionList {
        set stcName ""
        set stcValue ""
        if {[info exists ::sth::microBfd::emulation_micro_bfd_info_$type\_stcattr($hltName)]} {
            set stcName [set ::sth::microBfd::emulation_micro_bfd_info_$type\_stcattr($hltName)]
            if {($hltName eq "sessions_down_count") || ($hltName eq "sessions_up_count")} {
                set stcValue [sth::sthCore::invoke stc::get $hnd(-parent) -$stcName]
            } else {
                set stcValue $hnd(-$stcName)
            }
            keylset returnKeyedList $key.$hltName $stcValue
        }
    }

    return $::sth::sthCore::SUCCESS
}


proc ::sth::microBfd::processConfigSwitches {userfunName handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::microBfd::sortedSwitchPriorityList
    variable ::sth::microBfd::userArgsArray
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::microBfd:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::microBfd:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::microBfd:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach lagBfdHnd $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configLagBfdport {
                    configLagBfdport $lagBfdHnd $mode
                }
                configBfdAuth {
                    set bfdAuthHnd [::sth::sthCore::invoke stc::get $lagBfdHnd -children-BfdAuthenticationParams]
                    if {$bfdAuthHnd ne ""} {
                        configBfdAuth $bfdAuthHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BfdAuthenticationParams object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
}

proc ::sth::microBfd::configLagBfdport { handle mode } {

    set optionValueList [getStcOptionValueList emulation_micro_bfd_config configLagBfdport $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::microBfd::configBfdAuth { handle mode } {

    set optionValueList [getStcOptionValueList emulation_micro_bfd_config configBfdAuth $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::microBfd::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    
    set optionValueList {}
    
    foreach item $::sth::microBfd::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::microBfd:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }

            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::microBfd:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::microBfd:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::microBfd::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::microBfd::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::microBfd:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::microBfd:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::microBfd:: $cmdType $opt $::sth::microBfd::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::microBfd::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::microBfd::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $opt $value]
                }
            }
    }
    return $optionValueList
}

proc ::sth::microBfd::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::microBfd:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            if {[info exists userArgsArray($dependSwitch)] && [string match -nocase $dependValue $userArgsArray($dependSwitch)]} {
                set validFlag 1
                break
            }    
        }
        
        if {$validFlag == 0} { 
            if {[info exists userArgsArray($switchName)]} {
                ::sth::sthCore::processError returnKeyedList "Warning: \"-$switchName\" is supported if \"-$dependSwitch $dependValue\"."
                unset userArgsArray($switchName)
            }
        }
    }
}
