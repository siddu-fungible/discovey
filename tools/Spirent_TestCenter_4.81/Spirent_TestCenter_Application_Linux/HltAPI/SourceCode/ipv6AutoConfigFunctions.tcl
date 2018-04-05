
# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
#  any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Ipv6AutoConfig {
    # a global variable indicating whether to subscribe ipv6 Auto config result objects
    variable ipv6AutoConfig_subscription_state 0
}

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray

    set retVal [catch {
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            #if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
            #    ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHandle"
            #   return $returnKeyedList
            #}
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle is required when \"-mode create\" is used."
            return $returnKeyedList
        }

        set ipVersion $userArgsArray(ip_version)
        # create encapsulation stack by -protocol and -encap 
        if {![string compare -length 1 $ipVersion "6"]} {
            set topif "Ipv6If"
            set ifCount "1"
        } elseif {![string compare -length 3 $ipVersion "4_6"]} {
            set topif "Ipv6If Ipv4If"
            set ifCount "1 1"
        } else {
            # the interface does not have the L3 layer encapsulation
            set ipVersion "none"
            set topif ""
            set ifCount ""
        }
        
        # create encapsulation stack by -encap 
        set encap $userArgsArray(encap)
        
        switch -- $encap {
            "ethernet_ii" {
                set IfStack "$topif EthIIIf"
                set IfCount "$ifCount 1"
            }
	    "ethernet_vlan" {
		set IfStack "$topif VlanIf EthIIIf"
                set IfCount "$ifCount 1 1"
	    }
            "ethernet_ii_qinq" {
		set IfStack "$topif VlanIf VlanIf EthIIIf"
                set IfCount "$ifCount 1 1 1"
	    }
            default {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid -encap $encap" {}
                return -code error $returnKeyedList  
            }
        }
        
        # create device
        set createdDeviceList ""
        
        set ipIf ""
        array set DeviceCreateOutput [::sth::sthCore::invoke "stc::perform DeviceCreate \
						-ParentList $::sth::GBLHNDMAP(project) \
						-DeviceType Host \
						-IfStack \"$IfStack\" \
						-IfCount \"$IfCount\" \
						-Port $portHandle"]
         set createdHost $DeviceCreateOutput(-ReturnList)

        # config device count
        set count $userArgsArray(count)
        ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $count"

        lappend createdDeviceList $createdHost
	if {$encap == "ethernet_ii"} {
	    set lowerIf [::sth::sthCore::invoke stc::get $createdHost -children-EthIIIf]
	} else {
            set lowerIf [lindex [::sth::sthCore::invoke stc::get $createdHost -children-VlanIf] 0]
	}

        set ipv6If [::sth::sthCore::invoke stc::get $createdHost -children-ipv6if]

        ::sth::sthCore::invoke stc::config $ipv6If "-StackedOnEndpoint-targets $lowerIf"

        lappend ipIf $ipv6If

        if {![string compare -length 3 $ipVersion "4_6"]} {
            set ipv4If [::sth::sthCore::invoke stc::get $createdHost -children-ipv4if]

            ::sth::sthCore::invoke stc::config $ipv4If "-StackedOnEndpoint-targets $lowerIf"
            lappend ipIf $ipv4If
        }
    
        # create new ipv6if
        set cfglist "-Address $userArgsArray(link_local_ipv6_addr) -AddrStep $userArgsArray(link_local_ipv6_addr_step) -PrefixLength $userArgsArray(link_local_ipv6_prefix_len)"
        set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $createdHost "$cfglist -toplevelIf-sources $createdHost -StackedOnEndpoint-targets $lowerIf"]
        
        ::sth::sthCore::invoke stc::config $createdHost "-primaryif-targets $linkLocalIf"

        ::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets \"$linkLocalIf $ipIf\""

        set topif [lindex $topif 0]
        set ipStack [::sth::sthCore::invoke stc::get $createdHost -children-$topif]
        
        #set ipStack [lindex $ipStack 0]
        # Create SaaDeviceConfig
        set saaDeviceConfig [::sth::sthCore::invoke stc::create SaaDeviceConfig -under $createdHost "-UsesIf-targets \"$ipStack\""]
        
        #### Config input switches ####
        ::sth::Ipv6AutoConfig::processConfigSwitches emulation_ipv6_autoconfig $createdHost create returnKeyedList
	#need to check if the SaaDeviceResults & SaaPortResults have been subscribed
	if {$::sth::Ipv6AutoConfig::subscribed == 0} {
	    if {[catch {set SaaDeviceResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resulttype SaaDeviceResults  -configtype SaaDeviceConfig]} err]} {
		keylset returnKeyedList log "$procName Err: $err"
		return $returnKeyedList  
	    }
	    if {[catch {set SaaPortResultDataSet [::sth::sthCore::invoke stc::subscribe -parent $::sth::GBLHNDMAP(project) -resulttype SaaPortResults  -configtype SaaPortConfig]} err]} {
		keylset returnKeyedList log "$procName Err: $err"
		return $returnKeyedList  
	    }
	    set ::sth::Ipv6AutoConfig::subscribed 1
	}
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying IPv6 auto configuration: $err"
            return $returnKeyedList
        }

    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        # delete any device created if error occurs
        if {[info exists createdDeviceList]} {
            foreach device $createdDeviceList {
                ::sth::sthCore::invoke stc::delete $device
            }
        }
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handle $createdDeviceList 
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}


proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_modify"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    variable ::sth::Ipv6AutoConfig::sortedSwitchPriorityList

    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            foreach hostHandle $hostHandleList {
                if {![isIpv6AutoConfigHandleValid $hostHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid IPv6 Autoconfig handle" {}
                    return -code error $returnKeyedList 
                }
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle encap count ip_version}

        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        # modify input arguments
        foreach hostHandle $hostHandleList {
			if {[info exists userArgsArray(link_local_ipv6_addr)] ||
				[info exists userArgsArray(link_local_ipv6_addr_step)] ||
				[info exists userArgsArray(link_local_ipv6_prefix_len)] } {
				set linkLocalIf [::sth::sthCore::invoke stc::get $hostHandle -primaryif-Targets]
				set cfglist "-Address $userArgsArray(link_local_ipv6_addr) -AddrStep $userArgsArray(link_local_ipv6_addr_step) -PrefixLength $userArgsArray(link_local_ipv6_prefix_len)"
				::sth::sthCore::invoke stc::config $linkLocalIf $cfglist
			}
            ::sth::Ipv6AutoConfig::processConfigSwitches emulation_ipv6_autoconfig $hostHandle modify returnKeyedList  
        }
        
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList handle $hostHandleList   
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_reset { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_reset"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    variable ::sth::Ipv6AutoConfig::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }

        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![isIpv6AutoConfigHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid IPv6 Autoconfig handle" {}
                return -code error $returnKeyedList 
            }

            ::sth::sthCore::invoke stc::delete $deviceHandle
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

# fix US36948 [CR22644][P0]Deactivate/Activete ipv6 autoconfiguration
proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_enable { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_enable"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    variable ::sth::Ipv6AutoConfig::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }

        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![isIpv6AutoConfigHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid IPv6 Autoconfig handle" {}
                return -code error $returnKeyedList 
            }

            ::sth::sthCore::invoke stc::config $deviceHandle.saadeviceconfig -Active true
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $deviceHandleList
    }

    return $returnKeyedList
}

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_disable { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_disable"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    variable ::sth::Ipv6AutoConfig::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }

        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![isIpv6AutoConfigHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid IPv6 Autoconfig handle" {}
                return -code error $returnKeyedList 
            }

            ::sth::sthCore::invoke stc::config $deviceHandle.saadeviceconfig -Active false
        }
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $deviceHandleList
    }

    return $returnKeyedList
}


proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_control_action"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    
    set ipv6AutoConfigHandleList ""
    if {[info exists ::sth::Ipv6AutoConfig::userArgsArray(handle)]} {  
        foreach host $::sth::Ipv6AutoConfig::userArgsArray(handle) {
            if {[::sth::Ipv6AutoConfig::isIpv6AutoConfigHandleValid $host]} {
                set saaDeviceConfig [::sth::sthCore::invoke stc::get $host -children-SaaDeviceConfig]
                lappend ipv6AutoConfigHandleList $saaDeviceConfig
            }
        } 
    } elseif {[info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)]} {
		set portHndList $::sth::Ipv6AutoConfig::userArgsArray(port_handle)
		foreach ::sth::Ipv6AutoConfig::userArgsArray(port_handle) $portHndList { 
			if {[::sth::sthCore::IsPortValid $::sth::Ipv6AutoConfig::userArgsArray(port_handle) err]} {
				set ipv6DeviceHdl [::sth::sthCore::invoke stc::get $::sth::Ipv6AutoConfig::userArgsArray(port_handle) -affiliationport-sources]
				foreach host $ipv6DeviceHdl {
					if {[::sth::Ipv6AutoConfig::isIpv6AutoConfigHandleValid $host]} {
						set saaDeviceConfig [::sth::sthCore::invoke stc::get $host -children-SaaDeviceConfig]
						lappend ipv6AutoConfigHandleList $saaDeviceConfig
					}
				} 
			} else {
				::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::Ipv6AutoConfig::userArgsArray(port_handle)" {}
				return -code error $returnKeyedList
			}
		}
		set ::sth::Ipv6AutoConfig::userArgsArray(port_handle) $portHndList
    }

    switch -exact -- $::sth::Ipv6AutoConfig::userArgsArray(action) {
        "start" {
            ::sth::sthCore::invoke stc::perform SaaStartCommand -BlockList $ipv6AutoConfigHandleList
        }
        "stop" {
            ::sth::sthCore::invoke stc::perform SaaStopCommand -BlockList $ipv6AutoConfigHandleList
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown action $::sth::Ipv6AutoConfig::userArgsArray(action)."
            return -code error $returnKeyedList
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_get_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_get_stats"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    
    if {(![info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)]) && (![info exists ::sth::Ipv6AutoConfig::userArgsArray(handle)])} {
            ## get the handle if no handle is input
        set hosts [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-host]
        set portList ""
        foreach host $hosts {
            if {[::sth::Ipv6AutoConfig::isIpv6AutoConfigHandleValid $host]} {
                set portHandle [::sth::sthCore::invoke stc::get $host -affiliationport-targets]
                if {[lsearch $portList $portHandle] < 0} {lappend portList $portHandle}
            }  
        }
        set ::sth::Ipv6AutoConfig::userArgsArray(port_handle) $portList
    }

    set action "collect"
    if {[info exists ::sth::Ipv6AutoConfig::userArgsArray(action)]} {
        set action $::sth::Ipv6AutoConfig::userArgsArray(action)
    }
    if {![info exists ::sth::Ipv6AutoConfig::userArgsArray(mode)]} {
        if {[info exists ::sth::Ipv6AutoConfig::userArgsArray(port_handle)]} {
            set ::sth::Ipv6AutoConfig::userArgsArray(mode) "aggregate session"
        } else {
            set ::sth::Ipv6AutoConfig::userArgsArray(mode) "session"
        }
    }
        
    if {[catch {::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_stats_$action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_stats_collect { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_stats_collect"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray

    array set portAgg ""
    set ipv6AutoConfigHandle ""

    set retVal [catch {      
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            foreach port $portHandle {
                set portAgg($port) 0
                set ipv6Host [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                set ipv6AutoConfigHandle "$ipv6AutoConfigHandle $ipv6Host"
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set ipv6AutoConfigHandle $userArgsArray(handle)
        }

        foreach mode $userArgsArray(mode) {
            foreach handle $ipv6AutoConfigHandle {
                # validate the handle
                if {![::sth::Ipv6AutoConfig::isIpv6AutoConfigHandleValid $handle]} { continue }
                # get required handles
                set portHdl [::sth::sthCore::invoke stc::get $handle -affiliationport-targets]
                
                set saaPortHdl [::sth::sthCore::invoke stc::get $portHdl -children-SaaPortConfig]
                
                set saaDeviceHdl [::sth::sthCore::invoke stc::get $handle -children-SaaDeviceConfig]

                # SaaPortResults is automatically created from SaaDeviceConfig
                set saaPortResults [::sth::sthCore::invoke stc::get $saaPortHdl -children-SaaPortResults]
                set saaDeviceResults [::sth::sthCore::invoke stc::get $saaDeviceHdl -children-SaaDeviceResults]
    
                # create an array mapping between stcObj and stcHandle
                set hdlArray(SaaPortResults) $saaPortResults
                set hdlArray(SaaDeviceResults) $saaDeviceResults
                
                if {$mode == "aggregate"} {
                    if {[info exists portAgg($portHdl)] && $portAgg($portHdl) == 1} {
                        continue
                    } else {
                        set portAgg($portHdl) 1
                    }
                }

                foreach key [array names ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_stats_mode] {
                    foreach {tblMode tblProc} $::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_stats_mode($key) {
                        if {[string match $tblMode $mode]} {
                            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: emulation_ipv6_autoconfig_stats $key supported] "false"]} {
                                continue
                            }
                            
                            if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: emulation_ipv6_autoconfig_stats $key stcattr]] "_none_"]} {
                                continue
                            }
                            
                            if {$tblMode == "aggregate"} {
                                set stcObj $hdlArray(SaaPortResults)
                                
                                set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]
                                
                                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$portHdl.$key" $val]
                            } elseif {$tblMode == "session"} {
                                set stcObj $hdlArray(SaaDeviceResults)
                                
                                set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]
                                
                                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$key" $val]
                            } 
                        }
                    }
                }
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

proc ::sth::Ipv6AutoConfig::emulation_ipv6_autoconfig_stats_clear { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ipv6_autoconfig_stats_clear"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Ipv6AutoConfig::userArgsArray

    set retVal [catch {
        #Clear all stats
        ::sth::sthCore::invoke stc::perform ResultsClearAllProtocol
        
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }

    return $returnKeyedList
}

proc ::sth::Ipv6AutoConfig::processConfigSwitches {userfunName handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Ipv6AutoConfig::sortedSwitchPriorityList
    variable ::sth::Ipv6AutoConfig::userArgsArray
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Ipv6AutoConfig:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach deviceHandle $handleList {
		set linkLocalIf [::sth::sthCore::invoke stc::get $deviceHandle -primaryif-Targets]
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $deviceHandle -children-EthIIIf]
                    if {[string length $ethiiIf] != 0} {
                        configEthIIIntf $ethiiIf $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No EthIIIf object" {}
                        return -code error $returnKeyedList                        
                    }
                }

                configIpv6Intf {
                    set ipv6If [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv6if]
                    if {[llength $ipv6If] != 0} {
                        if {[llength $ipv6If] > 1} {
                            # get global ipv6if
							if {$linkLocalIf != "" } {
								set ipv6If [string trim [regsub $linkLocalIf $ipv6If ""] " "]
							} else {
								set ipv6If [lindex $ipv6If 0] 
							}
                        }
                        configIpv6Intf $ipv6If $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: ipv6if object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }

                configIpv4Intf {
                    set ipv4If [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv4if]
                    if {[llength $ipv4If] != 0} {
                        if {[llength $ipv4If] > 1} {
                            # get global ipv6if 
                            set ipv4If [lindex $ipv4If 0] 
                        }
                        configIpv4Intf $ipv4If $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: ipv4if object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
		
		configVlanIntf {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-vlanif]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0] 
                        }
                        configVlanIntf $vlanIf $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: ipv4if object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configVlanOuterIntf {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-vlanif]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] == 2} {
                            set vlanIfOuter [lindex $vlanIf 1]
                        }
                        configVlanOuterIntf $vlanIfOuter $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: vlanif object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
		
                configSaaDeviceConfig {
                    set saaDeviceCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-SaaDeviceConfig]

                    if {[llength $saaDeviceCfg] != 0} {
                        configSaaDeviceConfig $saaDeviceCfg $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: SaaDeviceConfig object missing" {}
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


proc ::sth::Ipv6AutoConfig::configSaaDeviceConfig { saaDeviceHandle mode } {

    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configSaaDeviceConfig $mode $saaDeviceHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $saaDeviceHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::configEthIIIntf { ethHandle mode } {

    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configEthIIIntf $mode $ethHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::configIpv6Intf { ipv6ifHandle mode } {

    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configIpv6Intf $mode $ipv6ifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6ifHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::configIpv4Intf { ipv4ifHandle mode } {

    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configIpv4Intf $mode $ipv4ifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4ifHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::configVlanIntf { vlanifHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configVlanIntf $mode $vlanifHandle 0]
#    if {$::sth::Ipv6AutoConfig::userArgsArray(vlan_id_mode) == "fixed"} {
#	if {[lsearch $optionValueList "-IdStep"] > -1} {
#	    set optionValueList [lreplace $optionValueList [expr [lsearch $optionValueList "-IdStep"] + 1] [expr [lsearch $optionValueList "-IdStep"] + 1] 0]
#	}
#    }
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanifHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::configVlanOuterIntf { vlanifHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_ipv6_autoconfig configVlanOuterIntf $mode $vlanifHandle 0]
#    if {$::sth::Ipv6AutoConfig::userArgsArray(vlan_outer_id_mode) == "fixed"} {
#	if {[lsearch $optionValueList "-IdStep"] > -1} {
#	    set optionValueList [lreplace $optionValueList [expr [lsearch $optionValueList "-IdStep"] + 1] [expr [lsearch $optionValueList "-IdStep"] + 1] 0]
#	}
#    }
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanifHandle $optionValueList
    }
}

proc ::sth::Ipv6AutoConfig::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    
    set optionValueList {}
    
    foreach item $::sth::Ipv6AutoConfig::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }

            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Ipv6AutoConfig:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Ipv6AutoConfig::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Ipv6AutoConfig::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Ipv6AutoConfig:: $cmdType $opt $::sth::Ipv6AutoConfig::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::Ipv6AutoConfig::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::Ipv6AutoConfig::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $opt $value]
                }
            }
    }
    return $optionValueList
}

proc ::sth::Ipv6AutoConfig::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Ipv6AutoConfig:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            # unlock the specified dependency relation when modify 
            if {[string match "modify" $mode]} {
                if {[lsearch -exact "transport_type device_type" $dependSwitch] >= 0} {
                    set validFlag 1
                    break
                }
            }
            
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

proc ::sth::Ipv6AutoConfig::isIpv6AutoConfigHandleValid { handle } {

    set procName [lindex [info level [info level]] 0]
    set cmdStatus 0
    set port [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
    
    if {[catch {set deviceHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {
        ::sth::sthCore::processError returnKeyedList "No device exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach deviceHandle $deviceHandleList {
	    if {[string equal $deviceHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}
        if {$cmdStatus == 0} {
            return $::sth::sthCore::FAILURE
        }
	if {[catch {set saaDeviceConfig [::sth::sthCore::invoke stc::get $handle -children-SaaDeviceConfig]} err]} {
	    set cmdStatus 0
	}
        if {[string length $saaDeviceConfig] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    return $::sth::sthCore::FAILURE		
	}		
    }
}
