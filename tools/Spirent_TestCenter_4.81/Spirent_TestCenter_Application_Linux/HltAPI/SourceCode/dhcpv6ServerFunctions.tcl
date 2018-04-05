
# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dhcpv6Server {
    # a global variable indicating whether to subscribe dot1x result objects
    set dhcpv6_server_subscription_state 0
}


proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_config_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable dhcpv6_server_subscription_state
    variable ::sth::Dhcpv6Server::userArgsArray
    set serverEmulationMode  $userArgsArray(server_emulation_mode)

    set retVal [catch {  
    
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
                ::sth::sthCore::processError returnKeyedList "Invalid value of \"-port_handle\" $portHandle"
                return $returnKeyedList
            }
        }  elseif {[info exists userArgsArray(handle)]} {
            set handle $userArgsArray(handle)
            set portHandle [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
        }

        set mode "create"
        
        if {$userArgsArray(mode) == "create"} {
            set ifStack ""
            set ifCount ""
            set lowerIf ""
            switch -exact -- $userArgsArray(encapsulation) {
                "ethernet_ii" {
                    set ifStack "Ipv6If EthIIIf "
                    set ifCount "1 1"
                }
                "ethernet_ii_vlan" {
                    set ifStack "Ipv6If VlanIf EthIIIf"
                    set ifCount "1 1 1"
                }
                "ethernet_ii_qinq" {
                    set ifStack "Ipv6If VlanIf VlanIf EthIIIf"
                    set ifCount "1 1 1 1"
                }
                default {    
                    ::sth::sthCore::processError returnKeyedList "Error: Unknown encapsulation $userArgsArray(encapsulation)"
                    return -code error $returnKeyedList 
                }
            }
            
            array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::sthCore::GBLHNDMAP(project) -DeviceType Host -IfStack $ifStack -IfCount $ifCount -Port $portHandle]
            set dhcpv6DeviceHandle $DeviceCreateOutput(-ReturnList)
            
            set ipv6If [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
            if {[catch {set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::get Failed $err" {}
                return -code error $returnKeyedList 
            }
    
            # create new ipv6if
            set cfglist "-Address fe80::2 -AddrStep ::1 -PrefixLength 64"
            if {[catch {
                set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $dhcpv6DeviceHandle "$cfglist -toplevelIf-sources $dhcpv6DeviceHandle -StackedOnEndpoint-targets $lowerIf"]
                ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
            } err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::create Failed $err" {}
                return -code error $returnKeyedList 
            }
    
            if {[catch {::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle "-primaryif-targets $linkLocalIf"} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: stc::config Failed $err" {}
                return -code error $returnKeyedList 
            }            
        } else {
            set dhcpv6DeviceHandle $handle
            
            if {$userArgsArray(mode) == "enable"} {
                set ipv6If [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
                if {[llength $ipv6If] == 0} {
                    set ipv6If [::sth::sthCore::invoke stc::create ipv6if -under  $dhcpv6DeviceHandle]
                    set primaryifTargets [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -primaryif-Targets]
                    set toplevelifTargets [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -toplevelif-Targets]
                    
                    set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $dhcpv6DeviceHandle -Address fe80::2 -AddrStep ::1 -PrefixLength 64]
                    ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                    set lowif [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ethiiif]
		    set vlanif [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-vlanif]
                    if {$vlanif != ""} {
                        set lowif [lindex $vlanif 0]
                    }
                    ::sth::sthCore::invoke stc::config $ipv6If "-stackedonendpoint-targets $lowif"
                    ::sth::sthCore::invoke stc::config $linkLocalIf "-stackedonendpoint-targets $lowif"
                    lappend primaryifTargets $ipv6If $linkLocalIf
                    lappend toplevelifTargets $ipv6If $linkLocalIf
                    ::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle -primaryif-Targets $primaryifTargets -toplevelif-Targets $toplevelifTargets
                    
                }
            } else {            
                set ipv6If [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
            }
        }
        # will not set DeviceCount when not specifying -count in enable mode
        if {$userArgsArray(mode) != "enable" || $::sth::Dhcpv6Server::dhcpv6SetCountArg} {
            set configList "-DeviceCount $userArgsArray(count)"
            ::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle $configList
        }
        
        #### ipv6 encap stack map ####
        #
        #            'toplevelIf'           UsesIf
        #         emulateddevice1 -----> ipv6if1  <------- $createdHost
        #              |                    |
        # 'toplevelIf' |                    |
        # 'PrimaryIf'  |                    |
        #              |                    |
        #   ipv6if2(linklocal)--------> vlanIf1 ---> vlanIf2 ---> ethIIIf1
        #
        #
        ####
        #  link local ipv6 interface faces to the DUT
        #  global ipv6 interface faces to Dhcpv6PortConfig
        ####

        
        if {[llength $ipv6If] > 1} {
            #get the ipv6 interface address
            foreach ipv6if $ipv6If {
                #get the address of ipv6if
                set ipv6IfAddr [::sth::sthCore::invoke stc::get $ipv6if -Address]
                if {![regexp -nocase "fe80" $ipv6IfAddr]} {
                    set ipv6If $ipv6if
                    break
                }
            }
        }
        #create Dhcpv6ServerConfig under host
        set dhcpv6ServerConfigHandle [::sth::sthCore::invoke stc::create Dhcpv6ServerConfig -under $dhcpv6DeviceHandle "-UsesIf-targets $ipv6If"]
            
        set dhcpv6ServerPrefixPoolConfig [::sth::sthCore::invoke stc::get $dhcpv6ServerConfigHandle -children-Dhcpv6ServerDefaultPrefixPoolConfig]
        
        # Added below code for check server_emulation_mode.
        # If server_emulation_mode is DHCPV6, create Dhcpv6ServerDefaultAddrPoolConfig object.
        if {[info exists userArgsArray(server_emulation_mode)] && $userArgsArray(server_emulation_mode) eq "DHCPV6"} {
            set dhcpv6ServerAddrPoolConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerDefaultAddrPoolConfig -under $dhcpv6ServerConfigHandle]
        }
        #config Dhcpv6ServerConfig
        processConfigSwitches $dhcpv6DeviceHandle $mode returnKeyedList

        if {$dhcpv6_server_subscription_state == 0} {
            # Create the DHCP server result dataset
            set dhcpv6ServerResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set dhcpv6ServerResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $dhcpv6ServerResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dhcpv6ServerConfig -ResultClassId Dhcpv6ServerResults"]
        }

        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying Dhcpv6 Server configuration: $err"
            return $returnKeyedList
        }
        
        if {$dhcpv6_server_subscription_state == 0} {
            # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $dhcpv6ServerResultDataSet
            set dhcpv6_server_subscription_state 1
        }
        
    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.port_handle" $portHandle]
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.dhcpv6_handle" $dhcpv6DeviceHandle]
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}


proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_config_modify"
    
    variable ::sth::Dhcpv6Server::userArgsArray
    variable ::sth::Dhcpv6Server::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            foreach hostHandle $hostHandleList {
                if {![IsDhcpv6ServerHandleValid $hostHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid DHCPv6/PD handle" {}
                    return -code error $returnKeyedList 
                }
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        set unsupportedModifyOptions {port_handle encapsulation count}

        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        # modify input arguments           
        ::sth::Dhcpv6Server::processConfigSwitches $hostHandle modify returnKeyedList
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.dhcpv6_handle" $hostHandleList]
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_config_reset { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_config_reset"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6Server::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }
        
        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![IsDhcpv6ServerHandleValid $deviceHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid DHCPv6 Server handle" {}
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

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_control_action"
	
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6Server::userArgsArray
    
    set retVal [catch {
        set hostHandleList ""
        if {([info exists ::sth::Dhcpv6Server::userArgsArray(dhcp_handle)])
                && (![info exists ::sth::Dhcpv6Server::userArgsArray(port_handle)])} {
				
			foreach deviceHandleList $::sth::Dhcpv6Server::userArgsArray(dhcp_handle) {
				if {![::sth::Dhcpv6Server::IsDhcpv6ServerHandleValid $deviceHandleList]} {
					::sth::sthCore::processError returnKeyedList "Error: $::sth::Dhcpv6Server::userArgsArray(dhcp_handle) is not a valid DHCPv6 Server handle" {}
					return -code error $returnKeyedList
				}
            }
			set hostHandleList $::sth::Dhcpv6Server::userArgsArray(dhcp_handle)      
			
        } elseif {([info exists ::sth::Dhcpv6Server::userArgsArray(port_handle)])
                && (![info exists ::sth::Dhcpv6Server::userArgsArray(dhcp_handle)])} {
			
			set portList $::sth::Dhcpv6Server::userArgsArray(port_handle)
			foreach ::sth::Dhcpv6Server::userArgsArray(port_handle) $portList {
				if {[::sth::sthCore::IsPortValid $::sth::Dhcpv6Server::userArgsArray(port_handle) err]} {
					set hostHandle [::sth::sthCore::invoke stc::get $::sth::Dhcpv6Server::userArgsArray(port_handle) -affiliationport-sources]
				} else {
					::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::Dhcpv6Server::userArgsArray(port_handle)" {}
					return -code error $returnKeyedList
				}
				foreach host $hostHandle {
					if {![::sth::Dhcpv6Server::IsDhcpv6ServerHandleValid $host]} {
						continue
					}
					lappend hostHandleList $host
				}
				set ::sth::Dhcpv6Server::userArgsArray(port_handle) $portList
			}
        }
        
		set hostHandles $hostHandleList
		foreach hostHandleList $hostHandles {
			switch -exact -- $::sth::Dhcpv6Server::userArgsArray(action) {
				"renew" -
				"connect" {
					::sth::sthCore::invoke stc::perform Dhcpv6StartServerCommand -Handle $hostHandleList
				}
				"reset" {
					::sth::sthCore::invoke stc::perform Dhcpv6StopServerCommand -Handle $hostHandleList
				}
				default {
					::sth::sthCore::processError returnKeyedList "Error:  Unsupported DHCPv6/PD Server control mode $::sth::Dhcpv6Server::userArgsArray(mode)." {}
					return -code error $returnKeyedList
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

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_collect { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_stats_action"
    variable ::sth::Dhcpv6Server::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {!([info exists userArgsArray(dhcp_handle)] || [info exists userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: -port_handle or -dhcp_handle."
        return $returnKeyedList
    }
    
    if {[info exists userArgsArray(dhcp_handle)] && [info exists userArgsArray(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The options -port_handle or -dhcp_handle are mutually exclusive."
        return $returnKeyedList
    }
    
    set hostHandleList ""
    #port_aggr_stat 1 - collect statistics on port_handle, 0 - collect statistics on specified dhcp_handle
    set port_aggr_stat 0
    if {([info exists userArgsArray(dhcp_handle)]) && (![info exists userArgsArray(port_handle)])} {
        if {![IsDhcpv6ServerHandleValid $userArgsArray(dhcp_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: $userArgsArray(dhcp_handle) is not a valid DHCP Server handle" {}
            return -code error $returnKeyedList
        }
        set handleList $userArgsArray(dhcp_handle)         
                
    } elseif {([info exists userArgsArray(port_handle)]) && (![info exists userArgsArray(dhcp_handle)])} {         
        if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) err]} {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
            return -code error $returnKeyedList
        }
        set port_aggr_stat 1
        set handleList $userArgsArray(port_handle)
    }

    processStatisticsServerResults $handleList $port_aggr_stat returnKeyedList
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_clear { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_server_stats"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::userArgsArray

    set retVal [catch {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            set dchpv6Handle [::sth::sthCore::invoke stc::get $portHandle -affiliationport-sources]
        } elseif {[info exists userArgsArray(handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![::sth::Dhcpv6Server::isDHCPv6DeviceHandleValid $handle]} { 
                   ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid Dhcpv6 Server handle"
                   return -code error $returnKeyedList
                }
            }
        }
            
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

proc ::sth::Dhcpv6Server::processConfigSwitches {handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Dhcpv6Server::sortedSwitchPriorityList
    variable ::sth::Dhcpv6Server::userArgsArray
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: emulation_dhcpv6_server_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: emulation_dhcpv6_server_config $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dhcpv6Server:: emulation_dhcpv6_server_config $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }

    set objArray(configDhcpv6DelayedAuthKey) Dhcpv6DelayedAuthKey
    set objArray(configDhcpv6ServerCustomOption) Dhcpv6ServerCustomMsgOption
    set objArray(configDhcpv6PrefixPoolCustomOption) Dhcpv6ServerPrefixPoolCustomMsgOption
    set objArray(configDhcpv6AddrPoolCustomOption) Dhcpv6ServerAddrPoolCustomMsgOption
    #Additional Address Pool Config
    set objArray(configDhcpv6ServerAddrPoolConfig) Dhcpv6ServerAddrPoolConfig
    set objArray(configDhcpv6ServerPrefixPoolConfig) Dhcpv6ServerPrefixPoolConfig
    
    foreach deviceHandle $handleList {
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
                            set ipv6If [lindex $ipv6If 0] 
                        }
                        configIpv6Intf $ipv6If $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: EthIIIf object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }

                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] > 1} {
                            set vlanIf [lindex $vlanIf 0]
                        }
                        configVlanIfInner $vlanIf $mode
                    }
                }

                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}            
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $vlanIf $mode
                    }
                }
                
                configDhcpv6ServerConfig {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    if {[llength $dhcpv6ServerCfg] != 0} {
                        configDhcpv6ServerConfig $dhcpv6ServerCfg $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Dhcpv6ServerConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                
                configDhcpv6ServerDefaultPrefixPoolConfig {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]
                    set dhcpv6ServerPrefixPoolConfig [::sth::sthCore::invoke stc::get $dhcpv6ServerCfg -children-Dhcpv6ServerDefaultPrefixPoolConfig]
                    if {[llength $dhcpv6ServerPrefixPoolConfig] != 0} {
                        configDhcpv6ServerDefaultPrefixPoolConfig $dhcpv6ServerPrefixPoolConfig $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Dhcpv6ServerDefaultPrefixPoolConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                
                configDhcpv6ServerDefaultAddrPoolConfig {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]
                    set dhcpv6ServerAddrPoolConfig [::sth::sthCore::invoke stc::get $dhcpv6ServerCfg -children-Dhcpv6ServerDefaultAddrPoolConfig]
                    if {[llength $dhcpv6ServerAddrPoolConfig] != 0} {
                        configDhcpv6ServerDefaultAddrPoolConfig $dhcpv6ServerAddrPoolConfig $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Dhcpv6ServerDefaultAddrPoolConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                
                configDhcpv6DelayedAuthKey {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerDelayedAuthKeyNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerDelayedAuthKeyIndex 0} {$dhcpv6ServerDelayedAuthKeyIndex < $dhcpv6ServerDelayedAuthKeyNum} {incr dhcpv6ServerDelayedAuthKeyIndex} {
                        set dhcpv6ServerdelayedAuthConfig [::sth::sthCore::invoke stc::create $objArray($func) -under $dhcpv6ServerCfg]
                        configDhcpv6DelayedAuthKey $dhcpv6ServerdelayedAuthConfig $mode $dhcpv6ServerDelayedAuthKeyIndex
                    }
                }
                
                configDhcpv6ServerCustomOption {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerMsgOptionNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerMsgOptionIndex 0} {$dhcpv6ServerMsgOptionIndex < $dhcpv6ServerMsgOptionNum} {incr dhcpv6ServerMsgOptionIndex} {
                        set dhcpv6ServerMsgOptionConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerMsgOption -under $dhcpv6ServerCfg]
                        configDhcpv6ServerCustomOption $dhcpv6ServerMsgOptionConfig $mode $dhcpv6ServerMsgOptionIndex
                    }
                }
                
                configDhcpv6PrefixPoolCustomOption {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerPrefixPoolConfig [::sth::sthCore::invoke stc::get $dhcpv6ServerCfg -children-Dhcpv6ServerDefaultPrefixPoolConfig]

                    set dhcpv6ServerMsgOptionNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerMsgOptionIndex 0} {$dhcpv6ServerMsgOptionIndex < $dhcpv6ServerMsgOptionNum} {incr dhcpv6ServerMsgOptionIndex} {
                        set dhcpv6PrefixPoolServerMsgOptionConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerMsgOption -under $dhcpv6ServerPrefixPoolConfig]
                        configDhcpv6PrefixPoolCustomOption $dhcpv6PrefixPoolServerMsgOptionConfig $mode $dhcpv6ServerMsgOptionIndex
                    }
                }

                configDhcpv6AddrPoolCustomOption {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerAddrPoolConfig [::sth::sthCore::invoke stc::get $dhcpv6ServerCfg -children-Dhcpv6ServerDefaultAddrPoolConfig]

                    set dhcpv6ServerMsgOptionNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerMsgOptionIndex 0} {$dhcpv6ServerMsgOptionIndex < $dhcpv6ServerMsgOptionNum} {incr dhcpv6ServerMsgOptionIndex} {
                        set dhcpv6AddrPoolServerMsgOptionConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerMsgOption -under $dhcpv6ServerAddrPoolConfig]
                        configDhcpv6AddrPoolCustomOption $dhcpv6AddrPoolServerMsgOptionConfig $mode $dhcpv6ServerMsgOptionIndex
                    }
                }

                configDhcpv6ServerAddrPoolConfig {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerAddrPoolNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerAddrPoolIndex 0} {$dhcpv6ServerAddrPoolIndex < $dhcpv6ServerAddrPoolNum} {incr dhcpv6ServerAddrPoolIndex} {
                        set dhcpv6ServerAddrPoolConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerAddrPoolConfig -under $dhcpv6ServerCfg]
                        configDhcpv6ServerAddrPoolConfig $dhcpv6ServerAddrPoolConfig $mode $dhcpv6ServerAddrPoolIndex
                    }
                }

                configDhcpv6ServerPrefixPoolConfig {
                    set dhcpv6ServerCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6ServerConfig]

                    set dhcpv6ServerPrefixPoolNum [inputListLength $objArray($func)]
                    for {set dhcpv6ServerPrefixPoolIndex 0} {$dhcpv6ServerPrefixPoolIndex < $dhcpv6ServerPrefixPoolNum} {incr dhcpv6ServerPrefixPoolIndex} {
                        set dhcpv6ServerAddrPoolConfig [::sth::sthCore::invoke stc::create Dhcpv6ServerPrefixPoolConfig -under $dhcpv6ServerCfg]
                        configDhcpv6ServerPrefixPoolConfig $dhcpv6ServerAddrPoolConfig $mode $dhcpv6ServerPrefixPoolIndex
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

proc ::sth::Dhcpv6Server::configEthIIIntf { ethHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configEthIIIntf $mode $ethHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configVlanIfInner { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $deviceHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configVlanIfInner $mode $deviceHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configVlanIfOuter { vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $vlanHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configVlanIfOuter $mode $deviceHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configIpv6Intf { ipv6ifHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configIpv6Intf $mode $ipv6ifHandle 0]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6ifHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerConfig { dhcpv6ServerHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerConfig $mode $dhcpv6ServerHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6ServerHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6DelayedAuthKey { dhcpv6delayedAuthConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6DelayedAuthKey $mode $dhcpv6delayedAuthConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6delayedAuthConfig $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerCustomOption { dhcpv6MsgOptionConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerCustomOption $mode $dhcpv6MsgOptionConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6MsgOptionConfig $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerDefaultAddrPoolConfig { dhcpv6ServerAddrPoolHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerDefaultAddrPoolConfig $mode $dhcpv6ServerAddrPoolHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6ServerAddrPoolHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6AddrPoolCustomOption { dhcpv6MsgOptionConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6AddrPoolCustomOption $mode $dhcpv6MsgOptionConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6MsgOptionConfig $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerDefaultPrefixPoolConfig { dhcpv6ServerPrefixPoolHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerDefaultPrefixPoolConfig $mode $dhcpv6ServerPrefixPoolHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6ServerPrefixPoolHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6PrefixPoolCustomOption { dhcpv6MsgOptionConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6PrefixPoolCustomOption $mode $dhcpv6MsgOptionConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6MsgOptionConfig $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerAddrPoolConfig { dhcpv6ServerAddrPoolHandle mode configIndex} {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerAddrPoolConfig $mode $dhcpv6ServerAddrPoolHandle $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6ServerAddrPoolHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::configDhcpv6ServerPrefixPoolConfig { dhcpv6ServerPrefixPoolHandle mode configIndex} {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_server_config configDhcpv6ServerPrefixPoolConfig $mode $dhcpv6ServerPrefixPoolHandle $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6ServerPrefixPoolHandle $optionValueList
    }
}

proc ::sth::Dhcpv6Server::processConfigCmd_vlanId { myswitch value } {
    variable userArgsArray
    
    set qinqIncrMode "inner"
    if {[info exists userArgsArray(qinq_incr_mode)]} {
        set qinqIncrMode $userArgsArray(qinq_incr_mode)
    }
    
    foreach item {{vlan_id_step 0} {vlan_id_count 1} {vlan_id_mode increment} {vlan_id_outer_step 0} {vlan_id_outer_count 1} {vlan_id_outer_mode increment}} {
        foreach {opt default} $item {}
        if {![info exists userArgsArray($opt)]} {
            set userArgsArray($opt) $default
        }
        set [string trim $opt "vlan_id_"] $userArgsArray($opt)
    }
    
    if {$myswitch == "vlan_id"} {
        if {$userArgsArray(encapsulation) == "ethernet_ii_qinq"} {
            switch -exact -- $qinqIncrMode {
                "inner" {
                    lappend vlanCfg -IfRecycleCount $count
                }
                "outer" {
                    if {[expr $outer_count-1] > 0} {
                        lappend vlanCfg -IdRepeatCount [expr $outer_count-1] -IfRecycleCount $count
                    } else {
                        lappend vlanCfg -IdRepeatCount $outer_count -IfRecycleCount $count
                    }
                }
                "both" {
                    lappend vlanCfg -IfRecycleCount $count
                }
            }
        } elseif {$userArgsArray(encapsulation) == "ethernet_ii_vlan"} {
            lappend vlanCfg -IfRecycleCount $count
        }
        if {$mode == "increment"} {
            lappend vlanCfg -IdStep $step
        } elseif {$mode == "fixed"} {
            lappend vlanCfg -IdStep 0
        }
        
        lappend vlanCfg -VlanId $value
        
    } elseif {$myswitch == "vlan_id_outer"} {
        
        if {$userArgsArray(encapsulation) != "ethernet_ii_qinq"} { return }
        
        switch -exact -- $qinqIncrMode {
            "inner" {
                if {[expr $count-1] > 0} {
                    lappend vlanCfg -IdRepeatCount [expr $count-1] -IfRecycleCount $outer_count
                } else {
                    lappend vlanCfg -IdRepeatCount $count -IfRecycleCount $outer_count
                } 
            }
            "outer" {
               lappend vlanCfg -IfRecycleCount $outer_count
            }
            "both" {
                lappend vlanCfg -IfRecycleCount $outer_count
            }
        }
        if {$mode == "increment"} {
            lappend vlanCfg -IdStep $outer_step
        } elseif {$mode == "fixed"} {
            lappend vlanCfg -IdStep 0
        }
        lappend vlanCfg -VlanId $value
    }

    return $vlanCfg
}

proc ::sth::Dhcpv6Server::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    
    set optionValueList {}
    
    foreach item $::sth::Dhcpv6Server::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dhcpv6Server:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Dhcpv6Server::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Dhcpv6Server::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Dhcpv6Server:: $cmdType $opt $::sth::Dhcpv6Server::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::Dhcpv6Server::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::Dhcpv6Server::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $opt $value]
                }
            }
    }
    return $optionValueList
}

proc ::sth::Dhcpv6Server::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Dhcpv6Server:: $cmdType $switchName dependency]] "_none_"]} {
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

proc ::sth::Dhcpv6Server::IsDhcpv6ServerHandleValid { handle } {
    
    set cmdStatus 1
    if {[catch {set hostHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {        ::sth::sthCore::processError returnKeyedList "No host exists under Project Handle:$::sth::GBLHNDMAP(project)"	return -code error $returnKeyedList     } else {
	foreach hostHandle $hostHandleList {
	    if {[string equal $hostHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}
	if {[catch {set dhcpServerHandle [::sth::sthCore::invoke stc::get $handle -children-Dhcpv6ServerConfig]} err]} {	    set cmdStatus 0
	}
        if {[string length $dhcpServerHandle] == 0} {
            set cmdStatus 0
        }
	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    #::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid Dhcp Server handle"
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::Dhcpv6Server::processStatisticsServerResults { handle statType returnKeyedListName } {
    variable userArgsArray
    upvar $returnKeyedListName dhcpv6ServerStatsKeyedList
    set port_aggr_stat $statType
        
    if {$port_aggr_stat == 1 && [string match "port*" $handle]} {
        set hostHandleList [::sth::sthCore::invoke stc::get $handle -affiliationport-sources]
    } elseif {$port_aggr_stat == 0 && ([string match "host*" $handle] || [string match "emulateddevice*" $handle])} {
        set hostHandleList $handle
    } else {
        ::sth::sthCore::processError returnKeyedList "$handle and $statType are not match" {}
        return -code error $returnKeyedList 
    }
    
    foreach host $hostHandleList {
        if {![IsDhcpv6ServerHandleValid $host]} {
            continue
        }
        set dhcpv6ServerConfigHandle [::sth::sthCore::invoke stc::get $host -children-Dhcpv6ServerConfig]
        set dhcpv6ServerResultsHandle [::sth::sthCore::invoke stc::get $dhcpv6ServerConfigHandle -children-Dhcpv6ServerResults]
        
        #Server State
        set dhcpv6ServersState [::sth::sthCore::invoke stc::get $dhcpv6ServerConfigHandle -ServerState]
        keylset dhcpv6ServerStatsKeyedList dhcp_server_state $dhcpv6ServersState
        
        set tableName ::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_stcattr
        set aggregateList [array names $tableName]
        if {![string length $dhcpv6ServerResultsHandle]} {
            foreach hltName $aggregateList {
                set stcName $::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                if {$port_aggr_stat == 1} {
                    set dhcpv6ServerStatsKeyedList [::sth::sthCore::updateReturnInfo $dhcpv6ServerStatsKeyedList "ipv6.aggregate.$handle.$hltName" "0"]  
                } else {
                    set dhcpv6ServerStatsKeyedList [::sth::sthCore::updateReturnInfo $dhcpv6ServerStatsKeyedList "ipv6.dhcp_handle.$host.$hltName" "0"] 
                }     
            }
        } else {
            foreach hltName $aggregateList {
                set stcName $::sth::Dhcpv6Server::emulation_dhcpv6_server_stats_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                set stcValue [::sth::sthCore::invoke stc::get $dhcpv6ServerResultsHandle -$stcName]
                if {$port_aggr_stat == 1} {
                    set dhcpv6ServerStatsKeyedList [::sth::sthCore::updateReturnInfo $dhcpv6ServerStatsKeyedList "ipv6.aggregate.$handle.$hltName" $stcValue]
                } else {
                    set dhcpv6ServerStatsKeyedList [::sth::sthCore::updateReturnInfo $dhcpv6ServerStatsKeyedList "ipv6.dhcp_handle.$host.$hltName" $stcValue]
                }    
            }
        }
    }  
}

proc ::sth::Dhcpv6Server::inputListLength {optionObject} {
    variable len
    variable userArgsArray
    variable sortedSwitchPriorityList
    set len -1
    switch -- $optionObject {
        Dhcpv6DelayedAuthKey {
            set optionList {dhcp6_delayed_auth_key_id dhcp6_delayed_auth_key_value}
        }
        Dhcpv6ServerCustomMsgOption {
            set optionList {server_custom_option_value server_custom_option_payload server_custom_enable_wildcards server_custom_string_as_hex_value server_custom_include_in_message}
        }
        Dhcpv6ServerPrefixPoolCustomMsgOption {
            set optionList {prefix_pool_custom_option_value prefix_pool_custom_option_payload prefix_pool_custom_enable_wildcards prefix_pool_custom_string_as_hex_value prefix_pool_custom_include_in_message}
        }
        Dhcpv6ServerAddrPoolCustomMsgOption {
            set optionList {addr_pool_custom_option_value addr_pool_custom_option_payload addr_pool_custom_enable_wildcards addr_pool_custom_string_as_hex_value addr_pool_custom_include_in_message}
        }
        Dhcpv6ServerAddrPoolConfig {
            set optionList {add_addr_pool_step_per_server  add_addr_pool_host_step  add_addr_pool_addresses_per_server  add_addr_pool_prefix_length add_addr_pool_start_addr}
        }
        Dhcpv6ServerPrefixPoolConfig {
            set optionList {add_prefix_pool_step_per_server add_prefix_pool_per_server  add_prefix_pool_prefix_length  add_prefix_pool_step add_prefix_pool_start_addr}
        }
        default {
            ::sth::sthCore::processError returnKeyedList "$optionObject should be Dhcpv6DelayedAuthKey " {}
            return -code error $returnKeyedList 
        }
    }
    foreach switchname $optionList {
        if {![info exists userArgsArray($switchname)]} {
            ::sth::sthCore::processError returnKeyedList "Should input $switchname in sth::emulation_dhcp_server_config" {}
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


