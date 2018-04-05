namespace eval ::sth::convergence {
    
}

###
#  Name:    emulation_convergence_config_create
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: create convergence.
###
proc ::sth::convergence::emulation_convergence_config_create { rklName } {
    
    upvar 1 $rklName returnKeyedList
    variable ::sth::convergence::userArgsArray


    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::convergence::emulation_convergence_config_create $rklName"
    
    # configure convergenceConfig
    set convergenceconfighandle [::sth::sthCore::invoke stc::create convergenceconfig -under $::sth::GBLHNDMAP(project)]
    set convergenceProto $userArgsArray(convergence_proto)
    set optionValueList [getStcOptionValueList emulation_convergence_config configconvergence create $convergenceconfighandle 0]
    if {[info exists userArgsArray(primary_router)]} {
	foreach prihandle $userArgsArray(primary_router) {
	    if {[regexp -nocase "BfdRouterConfig|BgpRouterConfig|Ospfv2RouterConfig|Ospfv3RouterConfig|IsisRouterConfig" $prihandle]} {	    
		set priRouteHandle $prihandle
	    } else {
		set priRouteHandle [::sth::sthCore::invoke stc::get $prihandle -children-[set convergenceProto]routerconfig]
	    }
	    lappend priRouteHandleList $priRouteHandle
	}
	lappend optionValueList -PrimaryPathProtocolConfig-targets $priRouteHandleList
    }
    if {[info exists userArgsArray(backup_router)]} {
	foreach bkhandle $userArgsArray(backup_router) {
	    if {[regexp -nocase "BfdRouterConfig|BgpRouterConfig|Ospfv2RouterConfig|Ospfv3RouterConfig|IsisRouterConfig" $bkhandle]} {	    
		set backupRouteHandle $bkhandle
	    } else {
		set backupRouteHandle [::sth::sthCore::invoke stc::get $bkhandle -children-[set convergenceProto]routerconfig]
	    }
	    lappend backupRouteHandleList $backupRouteHandle
	}
        lappend optionValueList -SecondaryPathProtocolConfig-targets $backupRouteHandleList
    }
    
    if {[llength $optionValueList]} {
	::sth::sthCore::invoke stc::config $convergenceconfighandle $optionValueList
    }
    set convergencepathHandle ""
    if {[info exists userArgsArray(selected_stream_block)]} {
        foreach streamHandle $userArgsArray(selected_stream_block) {
            lappend convergencepathHandle [::sth::sthCore::invoke stc::create convergencepathconfig -under $convergenceconfighandle -StreamHandle $streamHandle]         
        }
    }   

    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}   
        }
    }

    # prepare the keyed list to be returned to HLTAPI layer
    keylset returnKeyedList handle $convergenceconfighandle
    keylset returnKeyedList handles $convergencepathHandle 
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

###
#  Name:    emulation_convergence_config_modify
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Modify convergence.
###
proc ::sth::convergence::emulation_convergence_config_modify { rklName } {

    upvar 1 $rklName returnKeyedList
    variable ::sth::convergence::userArgsArray
    
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::convergence::emulation_convergence_config_modify $rklName"
      
    if {![info exists ::sth::convergence::userArgsArray(handle)]} {
            return -code error "the switch \"-handle\" is mandatory in modify mode"
    } else {
        set rtrHandle $::sth::convergence::userArgsArray(handle)
        if {[string first convergenceconfig $rtrHandle] < 0} {
                return -code error "Invalid convergence handle $rtrHandle"
        }
    }
    
    set optionValueList [getStcOptionValueList emulation_convergence_config configconvergence modify $rtrHandle 0]
    set convergenceProto $userArgsArray(convergence_proto)
    if {[info exists userArgsArray(primary_router)]} {
	foreach prihandle $userArgsArray(primary_router) {
	    if {[regexp -nocase "BfdRouterConfig|BgpRouterConfig|Ospfv2RouterConfig|Ospfv3RouterConfig|IsisRouterConfig" $prihandle]} {	    
		set priRouteHandle $prihandle
	    } else {
		set priRouteHandle [::sth::sthCore::invoke stc::get $prihandle -children-[set convergenceProto]routerconfig]
	    }
	    lappend priRouteHandleList $priRouteHandle
	}
	lappend optionValueList -PrimaryPathProtocolConfig-targets $priRouteHandleList
    }
    if {[info exists userArgsArray(backup_router)]} {
	foreach bkhandle $userArgsArray(backup_router) {
	    if {[regexp -nocase "BfdRouterConfig|BgpRouterConfig|Ospfv2RouterConfig|Ospfv3RouterConfig|IsisRouterConfig" $bkhandle]} {	    
		set backupRouteHandle $bkhandle
	    } else {
		set backupRouteHandle [::sth::sthCore::invoke stc::get $bkhandle -children-[set convergenceProto]routerconfig]
	    }
	    lappend backupRouteHandleList $backupRouteHandle
	}
        lappend optionValueList -SecondaryPathProtocolConfig-targets $backupRouteHandleList
    }
    
    if {[llength $optionValueList]} {
	::sth::sthCore::invoke stc::config $rtrHandle $optionValueList
    }
    set convergencepathHandle ""
    if {[info exists userArgsArray(selected_stream_block)]} {
        set convergencepathTmpHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-convergencepathconfig]
        if {$convergencepathTmpHandle != ""} {
            ::sth::sthCore::invoke stc::perform deletecommand -configlist $convergencepathTmpHandle
        }
        
        foreach streamHandle $userArgsArray(selected_stream_block) {
            lappend convergencepathHandle [::sth::sthCore::invoke stc::create convergencepathconfig -under $rtrHandle -StreamHandle $streamHandle]         
        }
    }   

    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} applyStatus]} {
                ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: Error while applying configuration: $applyStatus" {}   
        }
    }

    keylset returnKeyedList handles $convergencepathHandle
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::convergence::emulation_convergence_config_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::convergence::emulation_convergence_config_delete $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    if {![info exists ::sth::convergence::userArgsArray(handle)]} {
        return -code error "the switch \"-handle\" is mandatory in delete mode"
    } else {
        set handleList $::sth::convergence::userArgsArray(handle)
        foreach handle $handleList {
            if {![regexp -nocase {convergenceconfig|convergencepathconfig} $handle]} {
                return -code error "Invalid convergence handle $handle"
            }
        }
                
        ::sth::sthCore::invoke stc::perform deletecommand -configlist "$handleList"
            
    }
	
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply } err]} {
            return -code error "Error applying config: $err"
        }
    }
	
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::convergence::emulation_convergence_control { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::convergence::emulation_convergence_control $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    if {![info exists ::sth::convergence::userArgsArray(handle)]} {
        return -code error "the switch \"-handle\" is mandatory in control mode"
    } else {
        set handleList $::sth::convergence::userArgsArray(handle)
        foreach handle $handleList {
            if {![regexp -nocase {convergenceconfig|convergencepathconfig} $handle]} {
                return -code error "Invalid convergence handle $handle"
            }
        }
    }
    if {[info exists ::sth::convergence::userArgsArray(mode)]} {
        set mode $::sth::convergence::userArgsArray(mode)
    }
  
    if {[info exists ::sth::convergence::userArgsArray(test_type)]} {
        set testtype $::sth::convergence::userArgsArray(test_type)
    } else {
        set testtype "convergence"
    }
    if {[info exists ::sth::convergence::userArgsArray(timeout)]} {
        set timeout $::sth::convergence::userArgsArray(timeout)
    }
    if {[info exists ::sth::convergence::userArgsArray(mismatch_warning)]} {
        set mismatchwarning $::sth::convergence::userArgsArray(mismatch_warning)
    } else {
        set mismatchwarning "true"
    }
    
    switch -- $::sth::convergence::userArgsArray(mode) {
        setup {
            if {[info exists timeout]} {
                ::sth::sthCore::invoke stc::perform ConvergenceSetupCommand -ConfigList $handleList -TestType $testtype -Timeout $timeout
            } else {
                ::sth::sthCore::invoke stc::perform ConvergenceSetupCommand -ConfigList $handleList -TestType $testtype  
            }
	}
        collector {
            if {[info exists timeout]} {
                ::sth::sthCore::invoke stc::perform ConvergenceCollectorCommand -ConfigList $handleList -MismatchWarning $mismatchwarning -TestType $testtype -Timeout $timeout
            } else {
                ::sth::sthCore::invoke stc::perform ConvergenceCollectorCommand -ConfigList $handleList -MismatchWarning $mismatchwarning -TestType $testtype
            }
	}
        reset {
            ::sth::sthCore::invoke stc::perform ConvergenceResetCommand
        }
    }

    # prepare the keyed list to be returned to HLTAPI layer
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::convergence::emulation_convergence_info { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::convergence::emulation_convergence_info $rklName"
    
    upvar 1 $rklName returnKeyedList
	
    # validate convergenceconfig handle
    if {![info exists ::sth::convergence::userArgsArray(handle)]} {
            return -code error "the switch \"-handle\" is mandatory in emulation_convergence_info API"
    } else {
        set rtrHandle $::sth::convergence::userArgsArray(handle)
        if {[string first convergenceconfig $rtrHandle] < 0} {
                return -code error "Invalid convergence handle $rtrHandle"
        }
    }
       
    # get required result handle
    set convergenceResultHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-EventConfigResult]
    set hdlArray(EventConfigResult) $convergenceResultHandle
    
    # create a list of key-value pairs based on the mode -- key to mode mapping defined in convergenceTable.tcl
    set mode $::sth::convergence::userArgsArray(mode)
    set retVal {}

    foreach key [array names ::sth::convergence::emulation_convergence_info_mode] {
        set stcObj [::sth::sthCore::getswitchprop ::sth::convergence:: emulation_convergence_info $key stcobj]
        set stcAttr [::sth::sthCore::getswitchprop ::sth::convergence:: emulation_convergence_info $key stcattr]

        if {![info exists hdlArray($stcObj)]} {
            continue
        }
        set val [::sth::sthCore::invoke stc::get $hdlArray($stcObj) -$stcAttr]
        if {$mode == "stats"} {
            lappend retVal $key $val
        }
    }
    
    # prepare the keyed list to be returned to HLTAPI layer
    if {[llength $retVal]} {
	if {[catch { eval keylset returnKeyedList $retVal }]} {
		return -code error "Cannot update the returnKeyedList"
	}
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::convergence::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in convergenceTable.tcl
    foreach item $::sth::convergence::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::convergence:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::convergence:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::convergence:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::convergence:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::convergence:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::convergence:: $cmdType $opt $::sth::convergence::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::convergence::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::convergence::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}