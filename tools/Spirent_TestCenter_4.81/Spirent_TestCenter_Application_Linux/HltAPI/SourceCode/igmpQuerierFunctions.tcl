namespace eval ::sth::igmp {

}

proc ::sth::igmp::emulation_igmp_querier_config_create {returnKeyedListVarName} {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_igmp_querier_config_create"
    variable switchValues
    variable ::sth::igmp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
    set retVal [catch {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
                ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHandle"
                return $returnKeyedList
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set handle $userArgsArray(handle)
        }
        
        if {[info exists userArgsArray(port_handle)]} {
            #determine the stack on the router ethiff ipv4, ethiff vlan ipv4, ethiff vlan1 vlan2 ipv4
            if {[info exists switchValues(qinq_incr_mode)] || [info exists switchValues(vlan_id_outer)]} {
                set IfStack "Ipv4If VlanIf VlanIf EthIIIf"
                set IfCount "1 1 1 1"
            } elseif {[info exists switchValues(vlan_id)]} {
                set IfStack "Ipv4If VlanIf EthIIIf"
                set IfCount "1 1 1"
            } else {
                set IfStack "Ipv4If EthIIIf"
                set IfCount "1 1"
            }
            
            array set deviceList [::sth::sthCore::invoke stc::perform deviceCreate "-parentList" $::sth::GBLHNDMAP(project) "-ifStack"  $IfStack "-ifCount" $IfCount "-port" $userArgsArray(port_handle) "-deviceType" "Router" "-deviceCount" 1 "-createCount" $userArgsArray(count)]
            set igmpQuerierDeviceList $deviceList(-ReturnList)
        } else {
            set igmpQuerierDeviceList $handle
            foreach hname {intf_ip_addr intf_ip_addr_step intf_prefix_len source_mac source_mac_step neighbor_intf_ip_addr neighbor_intf_ip_addr_step vlan_cfi\ 
                            vlan_id vlan_id_mode vlan_id_step vlan_id_count vlan_user_priority vlan_outer_cfi vlan_id_outer vlan_id_outer_mode vlan_id_outer_step\ 
                            vlan_id_outer_count qinq_incr_mode vlan_outer_user_priority} {
                if {[info exists userArgsArray($hname)]} {
                        unset userArgsArray($hname)
                }
            }
        }
        foreach igmpQuerierDevice $igmpQuerierDeviceList {
            set ipv4if [::sth::sthCore::invoke stc::get $igmpQuerierDevice -children-Ipv4If]
            ::sth::sthCore::invoke stc::create IgmpRouterConfig -under $igmpQuerierDevice "-usesif-Targets $ipv4if"
        }
        #in the hlapiGen, the table is changed, these related args need to be change back
        # source_mac_step, neighbor_intf_ip_addr_step, vlan_id_mode, vlan_id_step, vlan_id_outer_mode, vlan_id_outer_step
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(source_mac_step) "SrcMacStep"
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(neighbor_intf_ip_addr_step) "GatewayStep"
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(vlan_id_mode) "_none_"
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(vlan_id_outer_mode) "_none_"
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(vlan_id_step) "IdStep"
        set ::sth::igmp::emulation_igmp_querier_config_stcattr(vlan_id_outer_step) "IdStep"
        #### Config input switches ####
        ::sth::igmp::processConfigSwitches $igmpQuerierDeviceList create returnKeyedList
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any device created if error occurs
        if {[info exists igmpQuerierDeviceList]} {
            foreach device $igmpQuerierDeviceList {
                if {[catch {::sth::sthCore::invoke stc::delete $device} err]} {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::delete Failed $err" {}
                    return -code error $returnKeyedList   
                }
            }
        }
    } else {
        keylset returnKeyedList handle $igmpQuerierDeviceList 
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::igmp::emulation_igmp_querier_config_modify {returnKeyedListVarName} {
    
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_igmp_querier_config_modify"
    variable switchValues
    variable ::sth::igmp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    ::sth::sthCore::parseInputArgs switches switchValues $userArgsArray(optional_args)
    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        #for the modify mode the handle can not be a device list
        set igmpQuerierDeviceHandle $userArgsArray(handle)
        if {![IsIgmpQuerierHandleValid $igmpQuerierDeviceHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $igmpQuerierDeviceHandle is not valid Igmp Querier handle" {}
            return -code error $returnKeyedList 
        }
        #### Config input switches ####
        ::sth::igmp::processConfigSwitches $igmpQuerierDeviceHandle create returnKeyedList
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $igmpQuerierDeviceHandle
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
}

proc ::sth::igmp::emulation_igmp_querier_config_delete {returnKeyedListVarName} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        
        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![IsIgmpQuerierHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid Igmp Querier handle" {}
                return -code error $returnKeyedList 
            }
            
            if {[catch {::sth::sthCore::invoke stc::delete $deviceHandle} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::delete Failed: $err" {}
                return -code error $returnKeyedList 
            }  
        }
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}


proc ::sth::igmp::processConfigSwitches {handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::igmp::sortedSwitchPriorityList
    variable ::sth::igmp::userArgsArray
    variable switchValues
    
    upvar $returnList returnKeyedList
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            if {![info exists userArgsArray($switchname)]} {
                continue
            }
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::igmp:: emulation_igmp_querier_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::igmp:: emulation_igmp_querier_config $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::igmp:: emulation_igmp_querier_config $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    if {[lsearch $functionsToRun "configVlanIfInner"] == -1 && [lsearch $functionsToRun "configVlanIfOuter"] == -1} {
    } else {
        getVlanIdList innerVlanIdList outerVlanIdList innerVlanRepeatCount outerVlanRepeatCount 
    }
    set i 0
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethIntfOption ""
                    if {[catch {set ethiiIf [::sth::sthCore::invoke stc::get $deviceHandle -children-EthIIIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[string length $ethiiIf] != 0} {
                        if {[llength $ethiiIf] > 1} {
                            set ethiiIf [lindex $ethiiIf 0] 
                        }
                        lappend ethIntfOption \
                            "-SourceMac" [::sth::sthCore::macStep \
                                $userArgsArray(source_mac) \
                                $userArgsArray(source_mac_step) $i] \
                            "-SrcMacStep" $userArgsArray(source_mac_step)
                        ::sth::sthCore::invoke stc::config $ethiiIf $ethIntfOption
                        #configEthIIIntf $ethiiIf $mode
                    }
                }
                configVlanIfInner {
                    if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0]
                        }
                        configVlanIfInner $vlanIf $mode $i $innerVlanIdList $innerVlanRepeatCount
                    }
                }
                configVlanIfOuter { 
                    if {[catch {set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $vlanIf $mode $i $outerVlanIdList $outerVlanRepeatCount
                    }
                }
                configIpIntf {
                    set ipIntfOption ""
                    if {[catch {set ipIf [::sth::sthCore::invoke stc::get $deviceHandle -children-Ipv4if]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    if {[llength $ipIf] != 0} {
                        if {[llength $ipIf] > 1} {
                            set ipIf [lindex $ipIf 0] 
                        }
                        lappend ipIntfOption \
                            "-address" [::sth::sthCore::updateIpAddress \
                                4 $userArgsArray(intf_ip_addr) \
                                $userArgsArray(intf_ip_addr_step) $i] \
                            "-gateway" [::sth::sthCore::updateIpAddress \
                                4 $userArgsArray(neighbor_intf_ip_addr) \
                                $userArgsArray(neighbor_intf_ip_addr_step) $i]\
                            "-gatewaystep" $userArgsArray(neighbor_intf_ip_addr_step) \
                            "-tostype" $userArgsArray(tos_type)
                        ::sth::sthCore::invoke stc::config $ipIf $ipIntfOption
                        #configIpIntf $ipIf $mode
                    }
                }
                configIgmpRouterConfig {
                    if {[catch {set igmpRouterCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-IgmpRouterConfig]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                    configIgmpRouterConfig $igmpRouterCfg $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        incr i
    }
}

proc ::sth::igmp::processConfigCmd_qinqIncrMode { handle myswitch value } {
    variable sortedSwitchPriorityList
    variable userArgsArray
    variable switchValues
    
    # inner vlan
    if {![info exists switchValues(vlan_id)]} {
        if {[catch {set vlanIf [lindex [::sth::sthCore::invoke stc::get $handle -children-vlanif] 0]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
            return -code error $returnKeyedList   
        }
        if {[catch {set vlan_id [::sth::sthCore::invoke stc::get $vlanIf -vlanId]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
            return -code error $returnKeyedList   
        }
        set vlanInnerCfg [processConfigCmd_vlanId $handle vlan_id $vlan_id]
        if {[catch {::sth::sthCore::invoke stc::config $vlanIf "$vlanInnerCfg"} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
    if {![info exists switchValues(vlan_id_outer)]} {
        # outer vlan
        if {[catch {set outerVlanIf [lindex [::sth::sthCore::invoke stc::get $handle -children-vlanif] 1]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
            return -code error $returnKeyedList   
        }
        if {[catch {set outer_vlan_id [::sth::sthCore::invoke stc::get $outerVlanIf -vlanId]} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed: $err" {}
            return -code error $returnKeyedList   
        }
        set vlanOuterCfg [processConfigCmd_vlanId $handle vlan_id_outer $outer_vlan_id]
        if {[catch {::sth::sthCore::invoke stc::config $outerVlanIf "$vlanOuterCfg"} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::igmp::processConfigCmd_vlanId {handle myswitch value } {
    variable userArgsArray
    variable VLANS
    variable switchValues
    
    foreach opt {vlan_id_step vlan_id_count vlan_id_outer_count vlan_id_outer_step} {
        if {![info exists VLANS($opt)] && [info exists userArgsArray($opt)] } {
            set VLANS($opt) $userArgsArray($opt)
        } 
    }
    
    if {$myswitch == "vlan_id"} {
        lappend vlanCfg -IfRecycleCount $VLANS(vlan_id_count) -VlanId $value
        
    } elseif {$myswitch == "vlan_id_outer"} {
        lappend vlanCfg -IfRecycleCount $VLANS(vlan_id_outer_count) -VlanId $value
    }

    return $vlanCfg
}

proc ::sth::igmp::IsIgmpQuerierHandleValid { handle } {
    set cmdStatus 0
    if {[catch {set port [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error: stc::get Failed: $err" {}
        return -code error $returnKeyedList 
    }
    
    if {[catch {set deviceHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-EmulatedDevice]} err]} {
        ::sth::sthCore::processError returnKeyedList "No device exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach deviceHandle $deviceHandleList {
	    if {[string equal $deviceHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}

	if {[catch {set igmpQuerierConfig [::sth::sthCore::invoke stc::get $handle -children-IgmpRouterConfig]} err]} {
	    set cmdStatus 0
	}
        if {[string length $igmpQuerierConfig] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid IGMP Querier handle"
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::igmp::configEthIIIntf { ethHandle mode } {

    set optionValueList [getStcOptionValueList emulation_igmp_querier_config configEthIIIntf $mode $ethHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $ethHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::igmp::configVlanIfInner { vlanHandle mode i innerVlanIdList innerVlanRepeatCount} {
    
    if {[catch {set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error: stc::get Failed $err" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_igmp_querier_config configVlanIfInner $mode $deviceHandle]
    
    set vlanId [lindex $innerVlanIdList $i]
    set optionValueList [regsub {VlanId .* -} $optionValueList "VlanId $vlanId -"]

    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}

proc ::sth::igmp::configVlanIfOuter { vlanHandle mode i outerVlanIdList outerVlanRepeatCount} {
        
    if {[catch {set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error: stc::get Failed $err" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_igmp_querier_config configVlanIfOuter $mode $deviceHandle]
    
    set vlanId [lindex $outerVlanIdList $i]
    set optionValueList [regsub {VlanId .* -} $optionValueList "VlanId $vlanId -"]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
}


proc ::sth::igmp::configIgmpRouterConfig {igmpRouterCfgHandle mode} {
    
    set optionValueList [getStcOptionValueList emulation_igmp_querier_config configIgmpRouterConfig $mode $igmpRouterCfgHandle]
    
    if {[llength $optionValueList]} {
        if {[catch {::sth::sthCore::invoke stc::config $igmpRouterCfgHandle $optionValueList} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
            return -code error $returnKeyedList
        }
    }
    
}

proc ::sth::igmp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    set optionValueList {}
    foreach item $::sth::igmp::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::igmp:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::igmp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::igmp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                ##check dependency
                #::sth::igmp::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::igmp::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::igmp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::igmp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::igmp:: $cmdType $opt $::sth::igmp::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr $::sth::igmp::userArgsArray($opt)
        	    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::igmp::userArgsArray($opt)]
                }
            }
    }
    return $optionValueList
}

proc ::sth::igmp::getVlanIdList {innerVlanIdList outerVlanIdList innerVlanRepeatCount outerVlanRepeatCount} {
    
    variable userArgsArray
    variable switchValues
    upvar innerVlanIdList myinnerVlanIdList
    upvar outerVlanIdList myouterVlanIdList
    upvar innerVlanRepeatCount myinnerVlanRepeatCount
    upvar outerVlanRepeatCount myouterVlanRepeatCount
    set myinnerVlanRepeatCount 0
    set myouterVlanRepeatCount 0
    
    if {[info exists switchValues(qinq_incr_mode)] || [info exists switchValues(vlan_id_outer)]} {
        #have outer vlanid

        set count $userArgsArray(count)
        set outerVlanId $userArgsArray(vlan_id_outer)
        set innerVlanId $userArgsArray(vlan_id)
        if {[info exists switchValues(vlan_id_count)]} {
            set innerVlanIdCount $switchValues(vlan_id_count)
        } else {
            set innerVlanIdCount $count
        }
        if {[info exists switchValues(vlan_id_outer_count)]} {
            set outerVlanIdCount $switchValues(vlan_id_outer_count)
        } else {
            set outerVlanIdCount $count  
        }

        switch -exact -- [string tolower $userArgsArray(vlan_id_mode)] {
            "fixed" {
               set innerVlanIdStep 0
            }
            "increment" {
               set innerVlanIdStep $userArgsArray(vlan_id_step)
            }
            default {
               return -code error "the vlan_id_mode should be 'fixed' or 'increment'"
            }
        }
        
        switch -exact -- [string tolower $userArgsArray(vlan_id_outer_mode)] {
            "fixed" {
               set outerVlanIdStep 0
            }
            "increment" {
               set outerVlanIdStep $userArgsArray(vlan_id_outer_step)
            }
            default {
               return -code error "the vlan_id_outer_mode should be 'fixed' or 'increment'"
            }
        }
        
        switch -- $userArgsArray(qinq_incr_mode) {
            "inner" {
                set myouterVlanRepeatCount $innerVlanIdCount
                for {set n 0} {$n < $count} {} {
                    for {set o 0} {($n < $count) && ($o < $outerVlanIdCount)} {incr o} {
                        for {set i 0} {($n < $count) && ($i < $innerVlanIdCount)} {incr i} {
                            lappend myinnerVlanIdList $innerVlanId
                            lappend myouterVlanIdList $outerVlanId
                            incr n
                            incr innerVlanId $innerVlanIdStep
                        }
                        incr outerVlanId $outerVlanIdStep
                    }
                }
            }
            "outer" {
                set myinnerVlanRepeatCount $outerVlanIdCount
                for {set n 0} {$n < $count} {} {
                    for {set i 0} {($n < $count) && ($i < $innerVlanIdCount)} {incr i} {
                        for {set o 0} {($n < $count) && ($o < $outerVlanIdCount)} {incr o} {
                            lappend myinnerVlanIdList $innerVlanId
                            lappend myouterVlanIdList $outerVlanId
                            incr n
                            incr outerVlanId $outerVlanIdStep
                            
                        }
                        incr innerVlanId $innerVlanIdStep
                    }
                }
            }
            "both" {
                set i $innerVlanId
                set iNum 0
                set o $outerVlanId
                set oNum 0
                for {set n 0} {$n < $count} {incr n} {
                    lappend myinnerVlanIdList $i
                    lappend myouterVlanIdList $o
                    incr i $innerVlanIdStep
                    incr iNum
                    if {!($iNum < $innerVlanIdCount)} {
                        set i $innerVlanId
                        set iNum 0
                    }
                    incr o $outerVlanIdStep
                    incr oNum
                    if {!($oNum < $outerVlanIdCount)} {
                        set o $outerVlanId
                        set oNum 0
                    }
                }
                
            }
        }
    } else {
        #only have the inner vlan id
        set count $userArgsArray(count)
        set innerVlanId $userArgsArray(vlan_id)
        #set count $switchValues(count)
        #set innerVlanId $switchValues(vlan_id)
        if {[info exists switchValues(vlan_id_count)]} {
            set innerVlanIdCount $switchValues(vlan_id_count)
        } else {
            set innerVlanIdCount $count
        }
        #set innerVlanIdCount $switchValues(vlan_id_count)
        switch -exact -- [string tolower $userArgsArray(vlan_id_mode)] {
            "fixed" {
               set innerVlanIdStep 0
            }
            "increment" {
               set innerVlanIdStep $userArgsArray(vlan_id_step)
            }
            default {
               return -code error "the vlan_id_mode should be 'fixed' or 'increment'"
            }
        }
        set i $innerVlanId
        set iNum 0
        for {set n 0} {$n < $count} {incr n} {
            lappend myinnerVlanIdList $i
            incr i $innerVlanIdStep
            incr iNum
            if {!($iNum < $innerVlanIdCount)} {
                set i $innerVlanId
                set iNum 0
            }
        }  
    }
}
