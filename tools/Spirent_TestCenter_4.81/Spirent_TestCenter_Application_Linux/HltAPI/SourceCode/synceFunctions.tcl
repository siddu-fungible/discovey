
# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
#  any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::synce {
    # a global variable indicating whether to subscribe ipv6 Auto config result objects
    variable synce_subscription_state 0
}

proc ::sth::synce::emulation_synce_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_synce_config_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::synce::userArgsArray

    set retVal [catch {
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: The -port_handle is required when \"-mode create\" is used."
            return $returnKeyedList
        }

        set ipVersion $userArgsArray(ip_version)
        # create encapsulation stack by -protocol and -encap 
		if {![string compare $ipVersion "4"]} {
            set topif "Ipv4If"
            set ifCount "1"
        } elseif {![string compare $ipVersion "6"]} {
            set topif "Ipv6If"
            set ifCount "1"
        } elseif {![string compare $ipVersion "4_6"]} {
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
						-DeviceType EmulatedDevice \
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

		if {![string compare $ipVersion "6"] ||
			![string compare $ipVersion "4_6"]} {

			set ipv6If [::sth::sthCore::invoke stc::get $createdHost -children-ipv6if]
			::sth::sthCore::invoke stc::config $ipv6If "-StackedOnEndpoint-targets $lowerIf"
			lappend ipIf $ipv6If

			if {![string compare $ipVersion "4_6"]} {
				set ipv4If [::sth::sthCore::invoke stc::get $createdHost -children-ipv4if]
				::sth::sthCore::invoke stc::config $ipv4If "-StackedOnEndpoint-targets $lowerIf"
				lappend ipIf $ipv4If
			}
		
			# create new ipv6if
			set cfglist "-Address $userArgsArray(link_local_ipv6_addr) -AddrStep $userArgsArray(link_local_ipv6_addr_step) -PrefixLength $userArgsArray(link_local_ipv6_prefix_len)"
			set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $createdHost "$cfglist -toplevelIf-sources $createdHost -StackedOnEndpoint-targets $lowerIf"]
			
			::sth::sthCore::invoke stc::config $createdHost "-primaryif-targets $linkLocalIf"
			::sth::sthCore::invoke stc::config $createdHost "-TopLevelIf-targets \"$linkLocalIf $ipIf\""
		}
		
		set topif [lindex $topif 0]
		set ipStack [::sth::sthCore::invoke stc::get $createdHost -children-$topif]
        
        #set ipStack [lindex $ipStack 0]
		set syncEthPortConfigHnd [::sth::sthCore::invoke stc::get $portHandle -children-SyncEthPortConfig]
		if {![string compare $syncEthPortConfigHnd ""]} {
			::sth::sthCore::invoke stc::create SyncEthPortConfig -under $portHandle
		}
        set syncEthDeviceConfigHnd [::sth::sthCore::invoke stc::create SyncEthDeviceConfig -under $createdHost "-UsesIf-targets \"$ipStack\""]
		
        #### Config input switches ####
        ::sth::synce::processConfigSwitches emulation_synce_config $createdHost create returnKeyedList

        #apply all configurations
        ::sth::sthCore::doStcApply

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
		keylset returnKeyedList synce_device_handle $syncEthDeviceConfigHnd
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::synce::emulation_synce_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_synce_config_modify"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::synce::userArgsArray
    variable ::sth::synce::sortedSwitchPriorityList

    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            foreach hostHandle $hostHandleList {
                if {![isSynceHandleValid $hostHandle]} {
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
			
			if {[regexp -nocase "link_local_" $sortedSwitchPriorityList]} {
				set linkLocalIf [::sth::sthCore::invoke stc::get $hostHandle -primaryif-Targets]
				set cfglist ""
				if {[info exists userArgsArray(link_local_ipv6_addr)]} {
					append cfglist " -Address $userArgsArray(link_local_ipv6_addr)"
				}
				if {[info exists userArgsArray(link_local_ipv6_addr_step)]} {
					append cfglist " -AddrStep $userArgsArray(link_local_ipv6_addr_step)"
				}
				if {[info exists userArgsArray(link_local_ipv6_prefix_len)]} {
					append cfglist " -PrefixLength $userArgsArray(link_local_ipv6_prefix_len)"
				}
				::sth::sthCore::invoke stc::config $linkLocalIf $cfglist
			}
            ::sth::synce::processConfigSwitches emulation_synce_config $hostHandle modify returnKeyedList  
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

proc ::sth::synce::emulation_synce_config_reset { returnKeyedListVarName } {

    variable ::sth::synce::userArgsArray
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
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::synce::emulation_synce_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_synce_control_action"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::synce::userArgsArray
    
    set synceHandleList ""
    if {[info exists ::sth::synce::userArgsArray(handle)]} {
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className SyncEthDeviceConfig -rootlist $::sth::synce::userArgsArray(handle)]
		set synceHandleList $rtn(-ObjectList)
    } elseif {[info exists ::sth::synce::userArgsArray(port_handle)]} {
		set port_list $::sth::synce::userArgsArray(port_handle)
		foreach port $port_list {
			if {[::sth::sthCore::IsPortValid $port err]} {
				set deviceHdl [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
				array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className SyncEthDeviceConfig -rootlist $deviceHdl]
				append synceHandleList " $rtn(-ObjectList)"
			} else {
				::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $port" {}
				return -code error $returnKeyedList
			}
		}
    }

    switch -exact -- $::sth::synce::userArgsArray(action) {
        "start" {
            ::sth::sthCore::invoke stc::perform ProtocolStartCommand -ProtocolList $synceHandleList
        }
        "stop" {
            ::sth::sthCore::invoke stc::perform ProtocolStopCommand -ProtocolList $synceHandleList
        }
        "delete" {
            ::sth::sthCore::invoke stc::perform DeleteCommand -ConfigList $synceHandleList
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unknown action $::sth::synce::userArgsArray(action)."
            return -code error $returnKeyedList
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS

    return $returnKeyedList
}

proc ::sth::synce::emulation_synce_stats_func {returnKeyedList} {
    upvar $returnKeyedList myreturnKeyedList
    variable ::sth::synce::userArgsArray
	
	set port_list ""
	set handle_list ""
	if {[info exists ::sth::synce::userArgsArray(handle)]} {
		set handle_list $::sth::synce::userArgsArray(handle)
		foreach hnd $handle_list {
			lappend port_list [::sth::sthCore::invoke stc::get $hnd -AffiliationPort-targets]
		}
	} else {
		set port_list $::sth::synce::userArgsArray(port_handle)
	}
	
	set num 1
	set mymode $::sth::synce::userArgsArray(mode)
	
	if {[regexp -nocase "port" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType SyncEthPortConfig -resulttype SyncEthPortResults]
		incr num
	}
	if {[regexp -nocase "device" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
						 -ConfigType SyncEthDeviceConfig -resulttype SyncEthDeviceResults]
		incr num
	}
	
	if {[regexp -nocase "option1" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType SyncEthDeviceConfig -resulttype SyncEthOption1Results]
		incr num
	}

	if {[regexp -nocase "option2" $mymode]} {
		set resultDataSet$num [::sth::sthCore::invoke stc::subscribe -parent project1 \
							 -ConfigType SyncEthDeviceConfig -resulttype SyncEthOption2Results]
		incr num
	}
    
	::sth::sthCore::invoke stc::sleep 3
	
	foreach port $port_list {
	
		if {[regexp -nocase "port" $mymode]} {
			array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className SyncEthPortConfig -rootlist $port]
			set syncEthPortConfigHnd $rtn(-ObjectList)
		
			set port_result [::sth::sthCore::invoke stc::get $syncEthPortConfigHnd -children-SyncEthPortResults]
			if {$port_result ne ""} {
				set switchNameList [array names ::sth::synce::emulation_synce_stats_port_mode]
				set retVal {}
				foreach switchName $switchNameList {
					set attr [::sth::sthCore::getswitchprop ::sth::synce:: emulation_synce_stats_port $switchName stcattr]
					set val [::sth::sthCore::invoke stc::get $port_result -$attr]
					keylset retVal $switchName $val
				}
				keylset myreturnKeyedList $port.port_result $retVal
			}
		}
		
		if {[regexp -nocase "device" $mymode]} {
			set device_list [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $device_list {
				if {[llength $handle_list] > 0} {
					if {![regexp -nocase $device $handle_list]} {
						continue
					}
				}
				set synceDevice [::sth::sthCore::invoke stc::get $device -children-SyncEthDeviceConfig]
				if {$synceDevice ne ""} {
					set device_result [::sth::sthCore::invoke stc::get $synceDevice -children-SyncEthDeviceResults]
					if {$device_result ne ""} {
						set switchNameList [array names ::sth::synce::emulation_synce_stats_device_mode]
						set retVal {}
						foreach switchName $switchNameList {
							set attr [::sth::sthCore::getswitchprop ::sth::synce:: emulation_synce_stats_device $switchName stcattr]
							set val [::sth::sthCore::invoke stc::get $device_result -$attr]
							keylset retVal $switchName $val
						}
						set val [::sth::sthCore::invoke stc::get $synceDevice -ClockState]
						keylset retVal clock_state $val
						keylset myreturnKeyedList $device.device_result $retVal
					}
				}
			}
		}
		
		if {[regexp -nocase "option1" $mymode]} {
			set device_list [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $device_list {
				set synceDevice [::sth::sthCore::invoke stc::get $device -children-SyncEthDeviceConfig]
				if {$synceDevice ne ""} {
					set option1_result [::sth::sthCore::invoke stc::get $synceDevice -children-SyncEthOption1Results]
					if {$option1_result ne ""} {
						set switchNameList [array names ::sth::synce::emulation_synce_stats_option1_mode]
						set retVal {}
						foreach switchName $switchNameList {
							set attr [::sth::sthCore::getswitchprop ::sth::synce:: emulation_synce_stats_option1 $switchName stcattr]
							set val [::sth::sthCore::invoke stc::get $option1_result -$attr]
							keylset retVal $switchName $val
						}
						keylset myreturnKeyedList $device.option1_result $retVal
					}
				}
			}
		}
		
		
		if {[regexp -nocase "option2" $mymode]} {
			set device_list [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources]
			foreach device $device_list {
				set synceDevice [::sth::sthCore::invoke stc::get $device -children-SyncEthDeviceConfig]
				if {$synceDevice ne ""} {
					set option2_result [::sth::sthCore::invoke stc::get $synceDevice -children-SyncEthOption2Results]
					if {$option2_result ne ""} {
						set switchNameList [array names ::sth::synce::emulation_synce_stats_option2_mode]
						set retVal {}
						foreach switchName $switchNameList {
							set attr [::sth::sthCore::getswitchprop ::sth::synce:: emulation_synce_stats_option2 $switchName stcattr]
							set val [::sth::sthCore::invoke stc::get $option2_result -$attr]
							keylset retVal $switchName $val
						}
						keylset myreturnKeyedList $device.option2_result $retVal
					}
				}
			}
		}
		
	}
	
	
	for {set i 1} {$i < $num} {incr i} {
		::sth::sthCore::invoke stc::unsubscribe [set resultDataSet$i]
		::sth::sthCore::invoke stc::delete [set resultDataSet$i]
	}
}

proc ::sth::synce::processConfigSwitches {userfunName handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::synce::sortedSwitchPriorityList
    variable ::sth::synce::userArgsArray
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::synce:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::synce:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::synce:: $userfunName $switchname $mode]
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
		        configSyncEthDeviceConfig {
                    set SyncEthDeviceConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-SyncEthDeviceConfig]

                    if {[llength $SyncEthDeviceConfigHnd] != 0} {
                        configSyncEthDeviceConfig $SyncEthDeviceConfigHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: SyncEthDeviceConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
		        configSyncEthPortConfig {
					set portHandle [::sth::sthCore::invoke stc::get $deviceHandle -affiliationport-Targets]
				    set SyncEthPortConfigHnd [::sth::sthCore::invoke stc::get $portHandle -children-SyncEthPortConfig]

                    if {[llength $SyncEthPortConfigHnd] != 0} {
                        configSyncEthPortConfig $SyncEthPortConfigHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: SyncEthPortConfig object missing" {}
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


proc ::sth::synce::configSyncEthPortConfig { syncEthPortConfigHnd mode } {

    set optionValueList [getStcOptionValueList emulation_synce_config configSyncEthPortConfig $mode $syncEthPortConfigHnd 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $syncEthPortConfigHnd $optionValueList
    }
}

proc ::sth::synce::configSyncEthDeviceConfig { syncEthDeviceConfigHnd mode } {

    set optionValueList [getStcOptionValueList emulation_synce_config configSyncEthDeviceConfig $mode $syncEthDeviceConfigHnd 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $syncEthDeviceConfigHnd $optionValueList
    }
}

proc ::sth::synce::configEthIIIntf { ethHandle mode } {

    set optionValueList [getStcOptionValueList emulation_synce_config configEthIIIntf $mode $ethHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::synce::configIpv6Intf { ipv6ifHandle mode } {

    set optionValueList [getStcOptionValueList emulation_synce_config configIpv6Intf $mode $ipv6ifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6ifHandle $optionValueList
    }
}

proc ::sth::synce::configIpv4Intf { ipv4ifHandle mode } {

    set optionValueList [getStcOptionValueList emulation_synce_config configIpv4Intf $mode $ipv4ifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4ifHandle $optionValueList
    }
}

proc ::sth::synce::configVlanIntf { vlanifHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_synce_config configVlanIntf $mode $vlanifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanifHandle $optionValueList
    }
}

proc ::sth::synce::configVlanOuterIntf { vlanifHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_synce_config configVlanOuterIntf $mode $vlanifHandle 0]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanifHandle $optionValueList
    }
}

proc ::sth::synce::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    
    set optionValueList {}
    
    foreach item $::sth::synce::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::synce:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }

            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::synce:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::synce:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::synce::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::synce::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::synce:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::synce:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::synce:: $cmdType $opt $::sth::synce::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::synce::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::synce::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $opt $value]
                }
            }
    }
    return $optionValueList
}

proc ::sth::synce::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::synce:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            # unlock the specified dependency relation when modify 
            # if {[string match "modify" $mode]} {
                # if {[lsearch -exact "transport_type device_type" $dependSwitch] >= 0} {
                    # set validFlag 1
                    # break
                # }
            # }
            
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

proc ::sth::synce::isSynceHandleValid { handle } {

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
		if {[catch {set syncEthDeviceConfigHnd [::sth::sthCore::invoke stc::get $handle -children-SyncEthDeviceConfig]} err]} {
			set cmdStatus 0
		}
        if {[string length $syncEthDeviceConfigHnd] == 0} {
            set cmdStatus 0
        }
		if {$cmdStatus == 1} {
			return $::sth::sthCore::SUCCESS
		} else {
			return $::sth::sthCore::FAILURE		
		}		
    }
}
