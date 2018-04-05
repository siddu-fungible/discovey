namespace eval ::sth::LinkOam {
    variable efm_subscription_state 0
    #defines the first time to start EFM after created
    array set firstStartFlag {}
}

proc ::sth::LinkOam::emulation_efm_config_create { rklName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    upvar $rklName returnKeyedList
    variable efm_subscription_state
    variable firstStartFlag
    
    if {[info exists userArgsArray(port_handle)]} {
        if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) err]} {
           ::sth::sthCore::processError returnKeyedList "$userArgsArray(port_handle) is not a valid port handle" {}
            return -code error $returnKeyedList 
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
        return -code error $returnKeyedList
    }
    
    set retVal [catch {
            # set default values for non-user defined switches
            foreach key [array names ::sth::LinkOam::emulation_efm_config_default] {
                if {[lsearch -exact $sortedSwitchPriorityList $key] < 0} {
                    set defaultValue [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $key default]
                    if {![string match $defaultValue "_none_"]} {
                        lappend sortedSwitchPriorityList "$defaultValue $key"
                    }
                }
            }
            
            set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
            set vlanOuter    [regexp -- {vlan_outer} $userArgsArray(optional_args)]
            
            if {$vlanOptFound} {
                if {$vlanOuter} {
                    set ifStack "Ipv4If VlanIf VlanIf EthIIIf"
                    set ifCount "1 1 1 1"
                } else {
                    set ifStack "Ipv4If VlanIf EthIIIf"
                    set ifCount "1 1 1"
                }
            } else {
                set ifStack "Ipv4If EthIIIf"
                set ifCount "1 1"
            }
            
            # create the router and interface stack
            if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $ifStack -IfCount $ifCount -Port $userArgsArray(port_handle)]
                            set router $DeviceCreateOutput(-ReturnList)} err]} {
		::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Link OAM Router. Error: $err" {}
		return -code error $returnKeyedList
            }
            
            set firstStartFlag($router) 1
            
            if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::create LinkOamRouterConfig -under $router]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                return -code error $returnKeyedList
            }
            set functionsToRun {}
            foreach item $sortedSwitchPriorityList {
                foreach {priority switchname} $item {
                    # make sure the option is supported
                    if {![::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $switchname supported]} {
                        ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                        return -code error $returnKeyedList 
                    }
                    if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $switchname mode] "_none_"]} { continue }
                    set func [::sth::sthCore::getModeFunc ::sth::LinkOam:: emulation_efm_config $switchname create]
                    if {[lsearch $functionsToRun $func] == -1} {
                        lappend functionsToRun $func
                    }
                }
            }
            set objArray(configLinkOamEventNotification) linkoameventnotificationconfig
            set objArray(configLinkOamTimers) LinkOamTimersConfig
            set objArray(configLinkOamOrgSpecific) LinkOamOrgSpecificConfig
            set objArray(configLinkOamVariableResponse) LinkOamVariableResponseConfig
            set objArray(configLinkOamVariableRequest) LinkOamVariableRequestConfig
            set objArray(configLinkOamOrgSpecificInfo) LinkOamOrgSpecificInfoConfig
            
            foreach func $functionsToRun {
                switch -- $func {
                    configEthIf {
                        #configure ethernet stack 
                        if {[catch {set ethIf [::sth::sthCore::invoke stc::get $router -children-EthIIIf]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        configEthIf $ethIf $userArgsArray(mode)
                    }
                    configVlanIfInner {
                        if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $router -children-vlanif]} err]} {
                           ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                           return -code error $returnKeyedList
                        }
                        if {[llength $vlanIf] == 0} {
                            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $router."
                            return $FAILURE
                        }
                        if {[llength $vlanIf] > 1} {
                            set vlanInner [lindex $vlanIf 0]
                        } else {
                            set vlanInner $vlanIf
                        }
                        configVlanIfInner $vlanInner $userArgsArray(mode)
                        
                    }
                    configVlanIfOuter {
                        if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $router -children-vlanif]} err]} {
                           ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                           return -code error $returnKeyedList
                        }
                        if {[llength $vlanIf] < 2} {
                            ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $router."
                            return $FAILURE
                        }
                        set vlanOuter [lindex $vlanIf 1]
                        configVlanIfOuter $vlanOuter $userArgsArray(mode)
                    }
                    configLinkOamRouter {
                        #configure LinkOamRouterConfig options
                        configLinkOamRouter $linkOamRtrCfg $userArgsArray(mode)
                    }
                    configLinkOamEventNotification -
                    configLinkOamTimers -
                    configLinkOamOrgSpecific {
                        ##configure LinkOamOrgSpecificConfig options
                        if {[catch {set linkOamObjCfg [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-$objArray($func)]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        $func $linkOamObjCfg $userArgsArray(mode)
                    }
                    configLinkOamVariableResponse -
                    configLinkOamVariableRequest -
                    configLinkOamOrgSpecificInfo {
                        set linkOamObjConfigNum [inputListLength $objArray($func)]
                        for {set linkOamObjConfigIndex 0} {$linkOamObjConfigIndex < $linkOamObjConfigNum} {incr linkOamObjConfigIndex} {
                            if {[catch {set linkOamObjCfg [::sth::sthCore::invoke stc::create $objArray($func) -under $linkOamRtrCfg]} err]} {
                                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            $func $linkOamObjCfg $userArgsArray(mode) $linkOamObjConfigIndex
                        }
                    }
                }
            }
            if {$efm_subscription_state == 0} {
                # Create the EFM result dataset
                if {[catch {set efmResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
            } else {
                if {[catch {set efmResultDataSet [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-ResultDataSet]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
            }
            if {$efm_subscription_state == 0} {
                if {[catch {set efmResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $efmResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId linkoamrouterconfig -ResultClassId linkoamstateresults"]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
                
                if {[catch {set efmResultQuery(2) [::sth::sthCore::invoke stc::create "ResultQuery" -under $efmResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId linkoamrouterconfig -ResultClassId linkoamcounterresults"]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
                if {[catch {set efmResultQuery(3) [::sth::sthCore::invoke stc::create "ResultQuery" -under $efmResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId linkoamrouterconfig -ResultClassId linkoameventcounterresults"]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
                
                if {[catch {set efmResultQuery(4) [::sth::sthCore::invoke stc::create "ResultQuery" -under $efmResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId linkoamrouterconfig -ResultClassId linkoamremoteinforesults"]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
                }
                
            }
                        
            #apply  all configurations
            if {[catch {::sth::sthCore::doStcApply} err]} {
                ::sth::sthCore::processError returnKeyedList "Error applying Link OAM configuration: $err"
                return $returnKeyedList
            }


            if {$efm_subscription_state == 0} {
                # Subscribe to the datasets
                ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $efmResultDataSet
                set efm_subscription_state 1
            }
            keylset returnKeyedList handle $router
        } returnedString]    
        
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return $returnKeyedList
}

proc ::sth::LinkOam::emulation_efm_config_modify { rklName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    upvar $rklName returnKeyedList
    variable firstStartFlag
    
    if {[info exists userArgsArray(port_handle)]} {
        if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) err]} {
           ::sth::sthCore::processError returnKeyedList "$userArgsArray(port_handle) is not a valid port handle" {}
            return -code error $returnKeyedList 
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
        return -code error $returnKeyedList
    }
    
    set portHandle $userArgsArray(port_handle)
    
    set retVal [catch {
        if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList
        }
        set linkOamRouter {}
        foreach router $routerHandle {
            if {![IsLinkOamRouterHandleValid $router]} {
                continue
            }
            if {![string match $portHandle [::sth::sthCore::invoke stc::get $router -AffiliationPort-targets]]} {
                continue
            }
            lappend linkOamRouter $router
            set firstStartFlag($router) 0
        }
        
        foreach linkOamRouterHandle $linkOamRouter {
            
            set functionsToRun {}
            foreach item $sortedSwitchPriorityList {
                foreach {priority switchname} $item {
                    # make sure the option is supported
                    if {![::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $switchname supported]} {
                        ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                        return -code error $returnKeyedList 
                    }
                    if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $switchname mode] "_none_"]} { continue }
                    set func [::sth::sthCore::getModeFunc ::sth::LinkOam:: emulation_efm_config $switchname modify]
                    if {[lsearch $functionsToRun $func] == -1} {
                        lappend functionsToRun $func
                    }
                }
            }
            if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::get $linkOamRouterHandle -children-LinkOamRouterConfig]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList 
            }
            set objArray(configLinkOamEventNotification) linkoameventnotificationconfig
            set objArray(configLinkOamTimers) LinkOamTimersConfig
            set objArray(configLinkOamOrgSpecific) LinkOamOrgSpecificConfig
            set objArray(configLinkOamVariableResponse) LinkOamVariableResponseConfig
            set objArray(configLinkOamVariableRequest) LinkOamVariableRequestConfig
            set objArray(configLinkOamOrgSpecificInfo) LinkOamOrgSpecificInfoConfig
            
            foreach func $functionsToRun {
                switch -- $func {
                    configEthIf {
                        if {[catch {set ethiiIf [::sth::sthCore::invoke stc::get $linkOamRouterHandle -children-ethiiif]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList 
                        }
                        configEthIf $ethiiIf $userArgsArray(mode)
                    }
                    configVlanIfInner {
                        if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $linkOamRouterHandle -children-vlanIf]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList 
                        }
                        if {[llength $vlanIf] == 0} {
                            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $linkOamRouterHandle."
                            return -code error $returnKeyedList 
                            #return $::sth::sthCore::FAILURE
                        }
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0]
                        }
                        configVlanIfInner $vlanIf $userArgsArray(mode)
                    }
                    configVlanIfOuter {
                        if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $linkOamRouterHandle -children-vlanIf]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList 
                        }
                        if {[llength $vlanIf] < 2} {
                            ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $linkOamRouterHandle."
                            return -code error $returnKeyedList 
                        }
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $vlanIf $userArgsArray(mode)
                    }
                    configLinkOamRouter {
                        configLinkOamRouter $linkOamRtrCfg $userArgsArray(mode)
                        
                        #start or stop sending remote_loop and link_events OAMPDU should on "COMPLETED" status when modifing the two paramters,
                        #otherwise, send the corresponding OAMPDU when starting EFM router
                        if {[catch {set linkOamStateResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoamstateresults]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        
                        #if {[string length $linkOamStateResults] != 0} {
                        #    
                        #    if {[catch {set localstate [stc::get $linkOamStateResults -LocalState]} err]} {
                        #        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                        #        return -code error $returnKeyedList
                        #    }
                        #    if {$localstate == "COMPLETED"} {
                        #        #Active mode EFM is allowed to send Remote Loopback OAMPDUs, Passive mode EFM is not permitted.
                        #        if {[info exist userArgsArray(remote_loopback)] && $userArgsArray(oam_mode) == "active"} {
                        #            if {$userArgsArray(remote_loopback) == 1} {
                        #                if {[catch {::sth::sthCore::invoke stc::perform  LinkOamStartLoopbackRequest -LinkOamRouterList $linkOamRtrCfg} err]} {
                        #                    ::sth::sthCore::processError returnKeyedList "Error starting loopback OAMPDUs for EFM router: $linkOamRouterHandle Msg: $err" {}
                        #                    return -code error $returnKeyedList
                        #                }
                        #            } else {
                        #                if {[catch {::sth::sthCore::invoke stc::perform  LinkOamStopLoopbackRequest -LinkOamRouterList $linkOamRtrCfg} err]} {
                        #                    ::sth::sthCore::processError returnKeyedList "Error starting loopback OAMPDUs for EFM router: $linkOamRouterHandle Msg: $err" {}
                        #                    return -code error $returnKeyedList
                        #                }
                        #            }  
                        #        }
                        #        #Active and Passive EFM both can send Link Event Notification OAMPDUs
                        #        if {[info exist userArgsArray(link_events)]} {
                        #            if {$userArgsArray(link_events) == 1} {
                        #                if {[catch {::sth::sthCore::invoke stc::perform  LinkOamStartEventNotification -LinkOamRouterList $linkOamRtrCfg \
                        #                           -SendErroredSymbolPeriodEvent true -SendErroredFrameEvent true -SendErroredFramePeriodEvent true \
                        #                           -SendErroredFrameSecondsSummaryEvent true -TxType SINGLE_MSG -Period 1} err]} {
                        #                    ::sth::sthCore::processError returnKeyedList "Error starting loopback OAMPDUs for EFM router: $linkOamRouterHandle Msg: $err" {}
                        #                    return -code error $returnKeyedList
                        #                } 
                        #            } else {
                        #                if {[catch {::sth::sthCore::invoke stc::perform  LinkOamStopEventNotification -LinkOamRouterList $linkOamRtrCfg} err]} {
                        #                    ::sth::sthCore::processError returnKeyedList "Error starting loopback OAMPDUs for EFM router: $linkOamRouterHandle Msg: $err" {}
                        #                    return -code error $returnKeyedList
                        #                }  
                        #            }   
                        #        }
                        #    }
                        #}
                    }
                    configLinkOamEventNotification -
                    configLinkOamTimers -
                    configLinkOamOrgSpecific {
                        if {[catch {set linkOamObjCfg [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-$objArray($func)]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        $func $linkOamObjCfg $userArgsArray(mode)
                    }
                    configLinkOamVariableResponse -
                    configLinkOamVariableRequest -
	            configLinkOamOrgSpecificInfo {
                        set linkOamObjConfigNum [inputListLength $objArray($func)]
                        if {[catch {set linkOamObjCfgList [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-$objArray($func)]} err]} {
                            ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        foreach linkOamObjToDelete $linkOamObjCfgList {
                            if {[catch {::sth::sthCore::invoke stc::delete $linkOamObjToDelete}]} {
                                ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                        }
                        for {set linkOamObjConfigIndex 0} {$linkOamObjConfigIndex < $linkOamObjConfigNum} {incr linkOamObjConfigIndex} {
                            if {[catch {set linkOamObjCfg [::sth::sthCore::invoke stc::create $objArray($func) -under $linkOamRtrCfg]} err]} {
                               ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                             $func $linkOamObjCfg $userArgsArray(mode) $linkOamObjConfigIndex
                        }
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                        return -code error $returnKeyedList 
                    }
                }
            }
        }
        
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying Link OAM configuration: $err"
            return $returnKeyedList
        }
        
        keylset returnKeyedList handle $linkOamRouterHandle
        
    } returnedString]
    
    
        if {$retVal} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        } else {
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
        }
        
    return $returnKeyedList
}



proc ::sth::LinkOam::emulation_efm_config_destroy { rklName } {
    upvar 1 $rklName returnKeyedList
    variable userArgsArray    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $::sth::LinkOam::userArgsArray(port_handle)
        if {![::sth::sthCore::IsPortValid $portHandle err]} {
            ::sth::sthCore::processError returnKeyedList "$portHandle is not a valid port handle" {}
            return -code error $returnKeyedList 
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
        return -code error $returnKeyedList
    }
       
    set retVal [catch {
        if {[catch {set routerHanle [::sth::sthCore::invoke stc::get $portHandle -affiliationport-sources]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error retrieving routers under $portHandle :$err" {}
            return -code error $returnKeyedList
        }
        
    	# verify which of these routers are Link OAM routers
    	set linkOamRouters {}
    	foreach rtr $routerHanle {
    	    if {[IsLinkOamRouterHandleValid $rtr]} {
		    lappend linkOamRouters $rtr
	    } 
        }
	foreach linkOamRtr $linkOamRouters {
		if {[catch {::sth::sthCore::invoke stc::delete $linkOamRtr} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error deleting Link Oam router. $err" {}
                    return -code error $returnKeyedList
		}
	}
        
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying Link OAM configuration: $err"
            return $returnKeyedList
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
	return $returnKeyedList
}

proc ::sth::LinkOam::emulation_efm_control_start { rklName } {
        variable userArgsArray
        variable firstStartFlag 
        upvar $rklName returnKeyedList
        
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $userArgsArray(port_handle)} err]} {
            ::sth::sthCore::processError returnKeyedList "Error starting router for EFM router: $userArgsArray(port_handle) Msg: $err" {}
            return -code error $returnKeyedList
        }
               
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList      
}

proc ::sth::LinkOam::emulation_efm_control_stop { rklName } {
        variable userArgsArray
        upvar $rklName returnKeyedList
    
        if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $userArgsArray(port_handle)} err]} {
        	::sth::sthCore::processError returnKeyedList "Error stopping router for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
        }
        
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList      
}

proc ::sth::LinkOam::emulation_efm_control_start_send_pdu { rklName } {
    variable userArgsArray
    upvar $rklName returnKeyedList
    set pdu_packing $userArgsArray(pdu_packing)
    set period $userArgsArray(period)
    set tx_type $userArgsArray(tx_type)
    set pause_at $userArgsArray(pause_at)
    if {[catch {set routerlist [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -AffiliationPort-Sources]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList
    }
    set linkoamrouterlist "";
    foreach router $routerlist {
        if {![IsLinkOamRouterHandleValid $router]} {
            continue
        } else {
           lappend linkoamrouterlist $router
        }
    }
    if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::get $router -children-LinkOamRouterConfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList 
    }
    switch -- $userArgsArray(action) {
        "start_loopback" {
            if {[catch {::sth::sthCore::invoke stc::perform LinkOamStartLoopbackRequest -LinkOamRouterList $linkOamRtrCfg} err]} {
                ::sth::sthCore::processError returnKeyedList "Error starting loopback for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
            }
        }
        "start_variable_request" {
             if {[catch {::sth::sthCore::invoke stc::perform LinkOamStartVariableRequest -LinkOamRouterList $linkOamRtrCfg -PduPackingOption $pdu_packing -Period $period -TxType $tx_type} err]} {
                ::sth::sthCore::processError returnKeyedList "Error starting Variable Request for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
            }
        }
        "start_organization_specific_event" {
            if {[catch {::sth::sthCore::invoke stc::perform LinkOamStartOrgSpecific -LinkOamRouterList $linkOamRtrCfg -Period $period -TxType $tx_type} err]} {
                ::sth::sthCore::processError returnKeyedList "Error starting Organazition Specific PDU for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
            }
        }
        "start_event_notification" {
            set error_frame_event_enable $userArgsArray(error_frame_event_enable)
            set error_frame_period_event_enable $userArgsArray(error_frame_period_event_enable)
            set error_frame_seconds_summary_event_enable $userArgsArray(error_frame_seconds_summary_event_enable)
            set error_symbol_period_event_enable $userArgsArray(error_symbol_period_event_enable)
            set organization_specific_event_enable $userArgsArray(organization_specific_event_enable)
            if {[catch {::sth::sthCore::invoke stc::perform LinkOamStartEventNotification -LinkOamRouterList $linkOamRtrCfg -PduPackingOption $pdu_packing-Period $period -SendErroredFrameEvent $error_frame_event_enable -SendErroredFramePeriodEvent $error_frame_period_event_enable -SendErroredFrameSecondsSummaryEvent $error_frame_seconds_summary_event_enable -SendOrgSpecificEvent $organization_specific_event_enable -SendErroredSymbolPeriodEvent $error_symbol_period_event_enable} err]} {
                ::sth::sthCore::processError returnKeyedList "Error starting Event Notifiaction for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
            }
        }
        "resume" {
            if {[catch {::sth::sthCore::invoke stc::perform LinkOamResume -LinkOamRouterList $linkOamRtrCfg -PauseAtState $pause_at} err]} {
                ::sth::sthCore::processError returnKeyedList "Error starting resume for EFM router: $userArgsArray(port_handle) Msg: $err" {}
                return -code error $returnKeyedList
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "unknown action: $userArgsArray(action)" {}
            return -code error $returnKeyedList 
        }
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList 
}
proc ::sth::LinkOam::emulation_efm_control_stop_send_pdu { rklName } {
    variable userArgsArray
    upvar $rklName returnKeyedList
    
    if {[catch {set routerlist [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -AffiliationPort-Sources]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList
    }
    
    foreach router $routerlist {
        if {![IsLinkOamRouterHandleValid $router]} {
            continue
        } else {
           lappend linkoamrouterlist $router
        }
    }
    if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::get $router -children-LinkOamRouterConfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList 
    }
    switch -- $userArgsArray(action) {
        "stop_loopback" {
            set cmdObject LinkOamStopLoopbackRequest
        }
        "stop_variable_request" {
            set cmdObject LinkOamStopVariableRequest
        }
        "stop_organization_specific_event" {
            set cmdObject LinkOamStopOrgSpecific
        }
        "stop_event_notification" {
            set cmdObject LinkOamStopEventNotification
        }
        default {
            ::sth::sthCore::processError returnKeyedList "unknown action: $userArgsArray(action)" {}
            return -code error $returnKeyedList
        }
    }
    if {[catch {::sth::sthCore::invoke stc::perform $cmdObject -LinkOamRouterList $linkOamRtrCfg} err]} {
        ::sth::sthCore::processError returnKeyedList "Error $userArgsArray(action) for EFM router: $userArgsArray(port_handle) Msg: $err" {}
        return -code error $returnKeyedList
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::LinkOam::emulation_efm_stat_get { rklName } {
    variable userArgsArray
    upvar $rklName returnKeyedList
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
        if {![::sth::sthCore::IsPortValid $portHandle err]} {
            ::sth::sthCore::processError returnKeyedList "$portHandle is not a valid port handle" {}
            return -code error $returnKeyedList 
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
        return -code error $returnKeyedList
    }
    
    set retVal [catch {
        # get required handles
        if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList
        }
        set LinkOamRouter {}
        foreach router $routerHandle {
            if {![IsLinkOamRouterHandleValid $router]} {
                continue
            }
            if {![string match $portHandle [::sth::sthCore::invoke stc::get $router -AffiliationPort-targets]]} {
                continue
            }
            lappend LinkOamRouter $router
        }         
           
        foreach LinkOamRouterHandle $LinkOamRouter {
            
            # get required handles
            if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::get $LinkOamRouterHandle -children-LinkOamRouterConfig]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
			
            # get the linkoamstateresults results
            if {[catch {set linkOamStateResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoamstateresults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
			
			if { $linkOamStateResults == "" } {
				if {[catch {set linkOamStateResults [::sth::sthCore::invoke stc::create linkoamstateresults -under $linkOamRtrCfg]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                    return -code error $returnKeyedList 
				}
				if {[catch {set linkOamStateResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resultparent $linkOamRtrCfg -resulttype LinkOamStateResults -configtype LinkOamRouterConfig ]} err]} {
					::sth::sthCore::processError returnKeyedList "Err: $err"
					return $returnKeyedList
				}
				::sth::sthCore::invoke stc::sleep 3;
			}
            
            # get the linkoamcounterresults results 
            if {[catch {set linkOamCouterResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoamcounterresults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            
            # get the linkoameventcounterresults results 
            if {[catch {set linkOamEventCouterResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoameventcounterresults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            
            # get the linkoamremoteinforesults results  
            if {[catch {set linkOamRemoteInfoResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoamremoteinforesults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            
            #subscribe the linkOamEventNotificationResults and get the linkoameventnotificationresults results
            # to make sure all the linkOamEventNotificationResults can be returned, we get linkOamEventNotificationResults again after wait a second.
            if {[catch {::sth::sthCore::invoke stc::perform LinkOamEventLogCommand -LinkOamRouter $linkOamRtrCfg} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::perform Failed: $err" {}
                return -code error $returnKeyedList
            }
            if {[catch {set linkOamEventNotificationResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoameventnotificationresults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            ::sth::sthCore::invoke stc::sleep 1;
            if {[catch {set linkOamEventNotificationResults [::sth::sthCore::invoke stc::get $linkOamRtrCfg -children-linkoameventnotificationresults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            
            # create an array mapping between stcObj and stcHandle
            set hdlArray(LinkOamRouterConfig) $linkOamRtrCfg
            set hdlArray(LinkOamStateResults) $linkOamStateResults
            set hdlArray(LinkOamCounterResults) $linkOamCouterResults
            set hdlArray(LinkOamEventCounterResults) $linkOamEventCouterResults
            set hdlArray(LinkOamRemoteInfoResults) $linkOamRemoteInfoResults
            set hdlArray(LinkOamEventNotificationResults) $linkOamEventNotificationResults
            
            
            keylset returnKeyedList port_handle $userArgsArray(port_handle)
            #local state
            if {[catch {set localstate [::sth::sthCore::invoke stc::get $linkOamStateResults -LocalState]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            keylset returnKeyedList local_state $localstate
            #get the results accroding to the option in the table
            foreach key [array names ::sth::LinkOam::emulation_efm_stat_mode] {
                foreach {tblMode tblProc} $::sth::LinkOam::emulation_efm_stat_mode($key) {
                   
                    if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_stat $key supported] "false"]} {
                        continue
                    }
                    if {[string match [set Obj [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_stat $key stcobj]] "_none_"]} {
                        continue
                    } 
                    if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_stat $key stcattr]] "_none_"]} {
                        continue
                    }
                    if {[regexp "LinkOamEventNotificationResults" $Obj]} {
                        set linkOamEventNotificationResultIndex 1
                        foreach linkOamEventNotificationResult $hdlArray($Obj) {
                            if {[catch {::sth::sthCore::invoke stc::get $linkOamEventNotificationResult -$stcAttr} val]} {
                                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                                return -code error $returnKeyedList
                            }
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "event_notification.$linkOamEventNotificationResultIndex.$key" $val]
                            incr linkOamEventNotificationResultIndex
                        }
                    } else {
                        if {[catch {::sth::sthCore::invoke stc::get $hdlArray($Obj) -$stcAttr} val]} {
                            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                            return -code error $returnKeyedList
                        }
                        # updated for cisco spec 5.4.1, TBC
                        if {$tblMode == "statistics"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "statistics.$key" $val]
                        } elseif {$tblMode == "mac_remote"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "mac_remote.$key" $val]
                        } elseif {$tblMode == "alarms"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "alarms.$key" $val]
                        }
                    }
                }
            }
            # oampdu_count is an aggregated count of all the oam Rx pdus
            if {[catch {set counterResultsInfo [::sth::sthCore::invoke stc::get $linkOamCouterResults]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList
            }
            set oampducount 0
            foreach results $counterResultsInfo {
                if {![regexp -- {RxCount} $results]} { continue }
                if {[catch {set value [::sth::sthCore::invoke stc::get $linkOamCouterResults $results]} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                    return -code error $returnKeyedList
                }
                set oampducount [expr {$oampducount+$value}]
            }
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "mac_remote.oampdu_count" $oampducount]
        }        
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return $returnKeyedList  
}


proc ::sth::LinkOam::emulation_efm_stat_reset { rklName } {  
    variable userArgsArray
    upvar $rklName returnKeyedList
       
    set retVal [catch {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            if {![::sth::sthCore::IsPortValid $portHandle err]} {
                ::sth::sthCore::processError returnKeyedList "$portHandle is not a valid port handle" {}
                return -code error $returnKeyedList 
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
            return -code error $returnKeyedList
        }
    
        # Clear ALL stats
        if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAllProtocol} err ]} {
            ::sth::sthCore::processError returnKeyedList "Internal error occured: $err"
            return $returnKeyedList
        }
     
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    
    return $returnKeyedList 
}

proc ::sth::LinkOam::configEthIf {ethIfHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configEthIf $mode $ethIfHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}
proc ::sth::LinkOam::configVlanIfInner {vlanHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configVlanIfInner $mode $vlanHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}
proc ::sth::LinkOam::configVlanIfOuter {vlanHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configVlanIfOuter $mode $vlanHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}
proc ::sth::LinkOam::configLinkOamRouter {linkOamRtrHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamRouter $mode $linkOamRtrHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamRtrHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamEventNotification {linkOamEventNHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamEventNotification $mode $linkOamEventNHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamEventNHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamTimers {linkOamTimerHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamTimers $mode $linkOamTimerHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamTimerHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamVariableResponse {linkOamVarResCfgHandle mode variableResponseConfigIndex} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamVariableResponse $mode $linkOamVarResCfgHandle $variableResponseConfigIndex]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamVarResCfgHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamVariableRequest {linkOamVarReqCfgHandle mode variableRequestConfigIndex} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamVariableRequest $mode $linkOamVarReqCfgHandle $variableRequestConfigIndex]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamVarReqCfgHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamOrgSpecificInfo {linkOamOrgSpecicInfoCfgHandle mode OrgSpecificInfoConfigIndex} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamOrgSpecificInfo $mode $linkOamOrgSpecicInfoCfgHandle $OrgSpecificInfoConfigIndex]
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamOrgSpecicInfoCfgHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::configLinkOamOrgSpecific {linkOamOrgSpecicCfgHandle mode} {
    set optionValueList [getStcOptionValueList emulation_efm_config configLinkOamOrgSpecific $mode $linkOamOrgSpecicCfgHandle 0]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $linkOamOrgSpecicCfgHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
	    return -code error $returnKeyedList
        }
    }
}

proc ::sth::LinkOam::processEmulation_efm_configOui {rtrHandle myswitch value} {
    if {[string length $value] != 6} {
        ::sth::sthCore::processError returnKeyedList "wrong Oui value for argument -$myswitch" {}
	return -code error $returnKeyedList
    }
    #change Oui format: xxxxxx to xx-xx-xx
    for {set x 0; set y 1} {$y < 6} {} {
        set val [string range $value $x $y]
        lappend oui $val 
        set x [expr {$x+2}]
	set y [expr {$y+2}]
    }
    set ouiValue [join $oui "-"]
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr $ouiValue"
}

proc ::sth::LinkOam::processEmulation_efm_configVsi {rtrHandle myswitch value} {
    if {[string length $value] != 8} {
        ::sth::sthCore::processError returnKeyedList "wrong Vsi value for argument -$myswitch" {}
	return -code error $returnKeyedList
    }
    #change Vsi value format: xxxxxxxx to xxxx xxxx
    for {set x 0; set y 3} {$y < 8} {} {
        set val [string range $value $x $y]
        lappend vsi $val 
        set x [expr {$x+4}]
	set y [expr {$y+4}]
    }
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr {$vsi}" 
    
}

proc ::sth::LinkOam::processEmulation_efm_vlanIdInner {rtrHandle myswitch value} {
    variable userArgsArray
    
    if {![info exists userArgsArray(vlan_id)]} {
        if {[catch {::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif} vlanHandles]} {
	    ::sth::sthCore::processError returnKeyedList "Internal Command Error: $vlanHandles"
            return $FAILURE
	}
        if {[llength $vlanHandles] == 0} {
            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $rtrHandle. To enable VLAN, specify \"-vlan_id <0-4095>\"."
	    return $FAILURE
	}
    }

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    set vlanConfig ""
    
    switch -- [string tolower $myswitch] {
        vlan_id {
            if {[info exists userArgsArray(vlan_id_mode)] && \
                    [string match -nocase $userArgsArray(vlan_id_mode) "increment"]} {
                if {![info exists userArgsArray(vlan_id_step)]} {
                    ::sth::sthCore::processError returnKeyedList "switch -vlan_id_step is required for -$myswitch." {}
                    return -code error $returnKeyedList
                }
                
                set newvlanId ""
                #in fact,vlan_id_step is useless as only one LinkOAM router can be created on a port.
                if {![::sth::sthCore::stepSwitchValue $userArgsArray($myswitch) $userArgsArray(vlan_id_step) 0 newvlanId]} {
                    ::sth::sthCore::log Error "Error occured while stepping the value of switch: $myswitch."
                }
                
                set vlanConfig "-$stcattr $newvlanId"     
            } elseif {[string match -nocase $userArgsArray(vlan_id_mode) "fixed"]} {
                if {![info exists userArgsArray(vlan_id_step)]} {
                    set vlanConfig "-$stcattr $value -IdStep 0"
                } else {
                    set vlanConfig "-$stcattr $value"
                }
            }  else {
                set vlanConfig "-$stcattr $value"
            }
        }
        vlan_user_priority { set vlanConfig "-$stcattr $value" }
        vlan_id_step {
            if {![info exists userArgsArray(vlan_id_mode)]} {
                ::sth::sthCore::processError returnKeyedList "switch -vlan_id_mode is required for -$myswitch." {}
                return -code error $returnKeyedList
            }
            if {[string match -nocase $userArgsArray(vlan_id_mode) "increment"]} {
                set vlanConfig "-$stcattr $value"
            } elseif {[string match -nocase $userArgsArray(vlan_id_mode) "fixed"]} {
                set vlanConfig "-$stcattr 0"
            }
        }  
    }
    
    return $vlanConfig
}

proc ::sth::LinkOam::processEmulation_efm_vlanIdOuter {rtrHandle myswitch value} {
    variable userArgsArray
    
    if {![info exists userArgsArray(vlan_outer_id)]} {
        if {[catch {::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif} vlanHandles]} {
	    ::sth::sthCore::processError returnKeyedList "Internal Command Error: $vlanHandles"
            return $FAILURE
	}
        if {[llength $vlanHandles] == 0} {
            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $rtrHandle. To enable VLAN, specify \"-vlan_id <0-4095>\"."
	    return $FAILURE
	}
    }

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    set vlanConfig ""
    
    switch -- [string tolower $myswitch] {
        vlan_outer_id {
            if {[info exists userArgsArray(vlan_outer_id_mode)] && \
                    [string match -nocase $userArgsArray(vlan_outer_id_mode) "increment"]} {
                if {![info exists userArgsArray(vlan_outer_id_step)]} {
                    ::sth::sthCore::processError returnKeyedList "switch -vlan_outer_id_step is required for -$myswitch." {}
                    return -code error $returnKeyedList
                }
                
                set newvlanId ""
                #in fact,vlan_id_step is useless as only one LinkOAM router can be created on a port.
                if {![::sth::sthCore::stepSwitchValue $userArgsArray($myswitch) $userArgsArray(vlan_outer_id_step) 0 newvlanId]} {
                    ::sth::sthCore::log Error "Error occured while stepping the value of switch: $myswitch."
                }
                
                set vlanConfig "-$stcattr $newvlanId"     
            } elseif {[string match -nocase $userArgsArray(vlan_outer_id_mode) "fixed"]} {
                if {![info exists userArgsArray(vlan_outer_id_step)]} {
                    set vlanConfig "-$stcattr $value -IdStep 0"
                } else {
                    set vlanConfig "-$stcattr $value"
                }
            }  else {
                set vlanConfig "-$stcattr $value"
            }
        }
        vlan_outer_user_priority { set vlanConfig "-$stcattr $value" }
        vlan_outer_id_step {
            if {![info exists userArgsArray(vlan_outer_id_mode)]} {
                ::sth::sthCore::processError returnKeyedList "switch -vlan_outer_id_mode is required for -$myswitch." {}
                return -code error $returnKeyedList
            }
            if {[string match -nocase $userArgsArray(vlan_outer_id_mode) "increment"]} {
                set vlanConfig "-$stcattr $value"
            } elseif {[string match -nocase $userArgsArray(vlan_outer_id_mode) "fixed"]} {
                set vlanConfig "-$stcattr 0"
            }
        }  
    }
    
    return $vlanConfig
}
proc ::sth::LinkOam::processEmulation_efm_datavalue {rtrHandle myswitch value} {
    variable userArgsArray
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::LinkOam:: emulation_efm_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    set ValueLen [string length $value]
    if {[expr $ValueLen%2]} {
        ::sth::sthCore::processError returnKeyedList "wrong input value os $myswitch" {}
        return -code error $returnKeyedList 
    } elseif {[expr $ValueLen == 2]} {
        set datavalueConfig "-$stcattr $value"
    } else {
        set valueWithSpace [string range $value 0 1]
        for {set i 2} {$i<$ValueLen} {incr i 2}  {
            #insert space
            lappend valueWithSpace
            lappend valueWithSpace [string range $value $i [expr $i+1]]
        }
        set datavalueConfig "-$stcattr \"$valueWithSpace\""
    }
    return $datavalueConfig
}
proc ::sth::LinkOam::IsLinkOamRouterHandleValid { handle } {
    	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set cmdStatus 0
        
	if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]} err]} {
                ::sth::sthCore::log error "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"
		return $FAILURE
	} else {
		foreach routerHandle $routerHandleList {
			if {[string equal $routerHandle $handle]} {
				set cmdStatus 1
				break
			}
		}
		
		if {[catch {set linkOamRtrCfg [::sth::sthCore::invoke stc::get $routerHandle -children-LinkOamRouterConfig]} err]} {
			set cmdStatus 0
		}

		if {$cmdStatus == 1} {

			return $SUCCESS
		} else {
			set errorMsg "Value ($handle) is not a valid Link OAM router handle"
			return $FAILURE		
		}		
	}
}

proc ::sth::LinkOam::checkDependency {cmdType myswitch dependentValue} {
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::LinkOam:: $cmdType $myswitch dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::LinkOam::userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $::sth::LinkOam::userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::LinkOam::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    variable sortedSwitchPriorityList
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in LinkOamTable.tcl
    foreach item $::sth::LinkOam::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::LinkOam:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::LinkOam:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::LinkOam:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::LinkOam:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::LinkOam:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::LinkOam:: $cmdType $opt $::sth::LinkOam::userArgsArray($opt)} value]} {
        		    lappend optionValueList -$stcAttr $value
        	    } else {
        		lappend optionValueList -$stcAttr [lindex $::sth::LinkOam::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::LinkOam::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $value]
                }
            }
        }
    }
    return $optionValueList
}
proc ::sth::LinkOam::inputListLength {optionObject} {
    variable len
    variable userArgsArray
    variable sortedSwitchPriorityList
    set len -1
    switch -- $optionObject {
        LinkOamVariableResponseConfig {
            set optionList {variable_response_branch variable_response_leaf variable_response_width variable_response_indication variable_response_data}
        }
        LinkOamVariableRequestConfig {
            set optionList {variable_request_branch variable_request_leaf}
        }
        LinkOamOrgSpecificInfoConfig {
            set optionList {osi_enable osi_value osi_oui}
        }
        default {
            ::sth::sthCore::processError returnKeyedList "$optionObject should be LinkOamVariableResponseConfig/LinkOamVariableRequestConfig/LinkOamOrgSpecificInfoConfig in emulation_efm_config_create" {}
            return -code error $returnKeyedList 
        }
    }
    foreach switchname $optionList {
        if {![info exists userArgsArray($switchname)]} {
            ::sth::sthCore::processError returnKeyedList "Should input $switchname in sth::emulation_efm_config" {}
            return -code error $returnKeyedList 
        } else {
            set currentSwitchLen [llength $userArgsArray($switchname)]
            if {$len == -1} {
                set len $currentSwitchLen
            } else {
                if {$len != $currentSwitchLen} {
                    ::sth::sthCore::processError returnKeyedList "the value of $switchname is wrong." {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
    return $len
}
