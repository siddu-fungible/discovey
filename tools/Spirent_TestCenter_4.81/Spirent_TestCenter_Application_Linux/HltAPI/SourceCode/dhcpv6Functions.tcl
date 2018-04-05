
# Copyright (c) 2005 - 2012 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

namespace eval ::sth::Dhcpv6 {
    # a global variable indicating whether to subscribe dot1x result objects

}

proc ::sth::Dhcpv6::emulation_dhcpv6_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_config_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::userArgsArray

    set retVal [catch {
        # port_handle is mandatory for the -mode create
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
                ::sth::sthCore::processError returnKeyedList "Error: Invalid value of \"-port_handle\" $portHandle"
                return $returnKeyedList
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set handle $userArgsArray(handle)
            set portHandle [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
        }
        
        # get Dhcpv6PortConfig
        set dhcpv6PortHandle [::sth::sthCore::invoke stc::get $portHandle -children-Dhcpv6PortConfig]
        
        #### Config input switches ####
        configDhcpv6PortConfig $dhcpv6PortHandle create
        
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error in $procName: Error applying DHCPv6 configuration: $err"
            return $returnKeyedList
        }

    } returnedString]

    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handles $dhcpv6PortHandle
        keylset returnKeyedList handle $dhcpv6PortHandle
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}


proc ::sth::Dhcpv6::emulation_dhcpv6_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_config_modify"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::userArgsArray
    
    set retVal [catch { 
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
            return -code error $returnKeyedList  
        } else {
            if {[string match -nocase "port*" $userArgsArray(handle)]} {
                set portHandle $userArgsArray(handle)
                if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                    ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -handle"
                    return -code error $returnKeyedList         
                }
                # get Dhcpv6PortConfig
                set dhcpv6PortHandle [::sth::sthCore::invoke stc::get $portHandle -children-Dhcpv6PortConfig]
            } elseif {[string match -nocase "Dhcpv6PortConfig*" $userArgsArray(handle)]} {
                set dhcpv6PortHandle $userArgsArray(handle)
                
                set portHandle [::sth::sthCore::invoke stc::get $dhcpv6PortHandle -parent]
            } else {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -handle"
                return -code error $returnKeyedList  
            }
        }
        
        # modify DHCPv6/pd port level configurations 
        configDhcpv6PortConfig $dhcpv6PortHandle modify
        
        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList handles $dhcpv6PortHandle
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_config_reset { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_config_reset"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    variable ::sth::Dhcpv6::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList


    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
            return -code error $returnKeyedList  
        } else {
            if {[string match -nocase "port*" $userArgsArray(handle)]} {
                set portHandle $userArgsArray(handle)
                if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                    ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -handle"
                    return -code error $returnKeyedList         
                }
                # get Dhcpv6PortConfig
                set dhcpv6PortHandle [::sth::sthCore::invoke stc::get $portHandle -children-Dhcpv6PortConfig]
            } elseif {[string match -nocase "Dhcpv6PortConfig*" $userArgsArray(handle)]} {
                set dhcpv6PortHandle $userArgsArray(handle)
                
                set portHandle [::sth::sthCore::invoke stc::get $dhcpv6PortHandle -parent]
            } else {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -handle"
                return -code error $returnKeyedList  
            }
        }

        ::sth::sthCore::invoke stc::delete $portHandle
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_group_config_create { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_group_config_create"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd
    variable ::sth::Dhcpv6::userArgsArray

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Missing a mandatory switch -handle."
            return -code error $returnKeyedList   
        } elseif {$userArgsArray(mode) == "create"} {
            set dhcpv6Handle $userArgsArray(handle)
            
            if {[string match -nocase "dhcpv6portconfig*" $dhcpv6Handle]} {
                set portHandle [::sth::sthCore::invoke stc::get $dhcpv6Handle -parent]
            } else {
                ::sth::sthCore::processError returnKeyedList "The value $dhcpv6Handle is not valid for -handle."
                return -code error $returnKeyedList  
                
            }
        }
            
        set mode "create"
        
        if {$userArgsArray(mode) == "create"} {
            set ifStack ""
            set ifCount ""
            set lowerIf ""
            switch -exact -- $userArgsArray(encap) {
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

            # Create the dhcpv6/pd device and interface stack
            array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::sthCore::GBLHNDMAP(project) -DeviceType Host -IfStack $ifStack -IfCount $ifCount -Port $portHandle]
                            set dhcpv6DeviceHandle $DeviceCreateOutput(-ReturnList)
            
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
    
            set ipv6If [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
            set lowerIf [::sth::sthCore::invoke stc::get $ipv6If -StackedOnEndpoint-targets]
        
            # create new ipv6if
            set cfglist "-Address fe80::1 -AddrStep ::1 -PrefixLength 64"
            set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $dhcpv6DeviceHandle "$cfglist -toplevelIf-sources $dhcpv6DeviceHandle -StackedOnEndpoint-targets $lowerIf"]
            ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
            ::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle "-primaryif-targets $linkLocalIf"
        } else {
            set dhcpv6DeviceHandle $userArgsArray(handle)
            if {$userArgsArray(mode) == "enable"} {
                set ipv6If [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
                if {[llength $ipv6If] == 0} {
                    set ipv6ifhandle [::sth::sthCore::invoke stc::create ipv6if -under  $dhcpv6DeviceHandle]
                    set primaryifTargets [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -primaryif-Targets]
                    set toplevelifTargets [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -toplevelif-Targets]
                    
                    set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $dhcpv6DeviceHandle -Address fe80::1 -AddrStep ::1 -PrefixLength 64]
                    ::sth::sthCore::invoke stc::config $linkLocalIf -AllocateEui64LinkLocalAddress true
                    set lowif [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ethiiif]
		            set vlanif [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-vlanif]
                    if {$vlanif != ""} {
                        set lowif [lindex $vlanif 0]
                    }
                    ::sth::sthCore::invoke stc::config $ipv6ifhandle "-stackedonendpoint-targets $lowif"
                    ::sth::sthCore::invoke stc::config $linkLocalIf "-stackedonendpoint-targets $lowif"
                    lappend primaryifTargets $ipv6ifhandle $linkLocalIf
                    lappend toplevelifTargets $ipv6ifhandle $linkLocalIf
                    ::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle -primaryif-Targets $primaryifTargets -toplevelif-Targets $toplevelifTargets
                    
                }
            }
            if {![regexp -nocase "AffiliationPort" [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle]]} {
                set dhcpv6DeviceHandle [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -parent]
            }
            set portHandle [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -AffiliationPort-targets]
        }
        

        set configList ""
        if {[info exists userArgsArray(device_name)]} {
            set configList [concat $configList "-Name $userArgsArray(device_name)"]
        }
        if {[info exists userArgsArray(num_sessions)] && $userArgsArray(mode) == "create"} {
            set configList [concat $configList " -DeviceCount $userArgsArray(num_sessions)"]
        } elseif {[info exists userArgsArray(num_sessions)] && $userArgsArray(num_sessions) != 1 && $userArgsArray(mode) == "enable"} {
            set configList [concat $configList " -DeviceCount $userArgsArray(num_sessions)"]
        }
        if {$configList != ""} {
            ::sth::sthCore::invoke stc::config $dhcpv6DeviceHandle $configList
        }
        set dhcpv6GroupHnd ""
        # create Dhcpv6PdBlockConfig or Dhcpv6PdBlockConfig under dhcpv6 device
        if {$::sth::Dhcpv6::dhcpv6Pd == 1} {

            array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $dhcpv6DeviceHandle  -CreateClassId [string tolower Dhcpv6PdBlockConfig]]
                              set dhcpv6PdBlockHandle $ProtocolCreateOutput(-ReturnList)
            
            #create the default host and return the host handle when dhcpv6pd is configured
            if {[info exists userArgsArray(export_addr_to_clients)] && $userArgsArray(export_addr_to_clients) == 1} {
                ::sth::Dhcpv6::processCreateLinkedHost $portHandle $dhcpv6DeviceHandle returnKeyedList
            }

            # config Dhcpv6PdBlockConfig
            ::sth::Dhcpv6::processConfigSwitches emulation_dhcpv6pd_group_config $dhcpv6DeviceHandle create returnKeyedList
            
            set dhcpv6GroupHnd [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-Dhcpv6PdBlockConfig]
        } else {
            array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $dhcpv6DeviceHandle  -CreateClassId [string tolower Dhcpv6BlockConfig]]
                              set dhcpv6BlockHandle $ProtocolCreateOutput(-ReturnList)

            # config Dhcpv6BlockConfig
            ::sth::Dhcpv6::processConfigSwitches emulation_dhcpv6_group_config $dhcpv6DeviceHandle create returnKeyedList
            set dhcpv6GroupHnd [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-Dhcpv6BlockConfig]
        }

        keylset returnKeyedList port_handle $portHandle
        keylset returnKeyedList dhcpv6_handle $dhcpv6DeviceHandle
        keylset returnKeyedList handles $dhcpv6GroupHnd
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::processCreateLinkedHost {portHandle dhcpv6DeviceHandle returnList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    upvar $returnList returnKeyedList
    
    #get the ifstack of dhcpv6DeviceHandle
    set ipv6IfList [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -children-ipv6if]
    #get the global ipv6 and link locak ipv6
    foreach ipv6if $ipv6IfList {
        #get the address of ipv6if
        set ipv6IfAddr [::sth::sthCore::invoke stc::get $ipv6if -Address]
        if {[regexp -nocase "fe80" $ipv6IfAddr]} {
            set linkLocalIf $ipv6if
        } else {
            set ipv6If $ipv6if
        }
    }
    set deviceCount [::sth::sthCore::invoke stc::get $dhcpv6DeviceHandle -DeviceCount]
    
    # step2: create host interface stack (ipv6if ipv6if ethiiif)
    set ifStack "Ipv6If EthIIIf"
    set ifCount "1 1"
array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::sthCore::GBLHNDMAP(project) -DeviceType Host -IfStack $ifStack -IfCount $ifCount -Port $portHandle]
                            set linkedHost $DeviceCreateOutput(-ReturnList)

    
    # validate the client count
    if {![info exists userArgsArray(client_count)]} {
        set userArgsArray(client_count) $deviceCount   
    }
    if {$userArgsArray(client_count) != $deviceCount && $deviceCount != 1} {
        ::sth::sthCore::processError returnKeyedList "The client_count is incompatible with the device count of $dhcpv6DeviceHandle, must be the same as the device count $deviceCount."
        return -code error $returnKeyedList 
    }    
    ::sth::sthCore::invoke stc::config $linkedHost "-DeviceCount $userArgsArray(client_count)"
    
    # config mac address
    set ethIf [::sth::sthCore::invoke stc::get $linkedHost -children-ethiiif]
    if {![info exists userArgsArray(client_mac_addr)]} { set userArgsArray(client_mac_addr) "00:10:01:00:00:01"}
    if {![info exists userArgsArray(client_mac_addr_step)]} { set userArgsArray(client_mac_addr_step) "00:00:00:00:00:01"}
    if {![info exists userArgsArray(client_mac_addr_mask)]} { set userArgsArray(client_mac_addr_mask) "00:00:00:FF:FF:FF"}
    
    ::sth::sthCore::invoke stc::config $ethIf "-SourceMac $userArgsArray(client_mac_addr) -SrcMacStep $userArgsArray(client_mac_addr_step) -SrcMacStepMask $userArgsArray(client_mac_addr_mask) "
    
    set ipv6If2 [::sth::sthCore::invoke stc::get $linkedHost -children-ipv6if]
    
     
    #create the link local address
    set cfglist "-Address fe80:: -AddrStep ::1 -PrefixLength 128 -Gateway ::"
    set linkLocalIf2 [::sth::sthCore::invoke stc::create ipv6if -under $linkedHost "$cfglist -StackedOnEndpoint-targets $ethIf"]
    ::sth::sthCore::invoke stc::config $linkLocalIf2 -AllocateEui64LinkLocalAddress true
    ::sth::sthCore::invoke stc::config $linkedHost "-TopLevelIf-targets \"$ipv6If2 $linkLocalIf2\" -PrimaryIf-targets $linkLocalIf2"
    
    # step3 : config link relationship between CPE and Clients
    ::sth::sthCore::invoke stc::perform LinkCreate -DstDev $dhcpv6DeviceHandle -SrcDev $linkedHost -LinkType {Home Gateway Link}
    

    keylset returnKeyedList linked_host_handle $linkedHost
    
}


proc ::sth::Dhcpv6::emulation_dhcpv6_group_config_modify { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_group_config_modify"
    
    variable ::sth::Dhcpv6::userArgsArray
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd
    
    if {$::sth::Dhcpv6::dhcpv6Pd == 1} {
       set configBlockObject "Dhcpv6PdBlockConfig"
    } else {
       set configBlockObject "Dhcpv6BlockConfig"
    }

    set retVal [catch {
        if {[info exists userArgsArray(handle)]} {
            set hostHandleList $userArgsArray(handle)
            foreach hostHandle $hostHandleList {
                if {![isDHCPv6DeviceHandleValid $hostHandle $configBlockObject]} {
                    ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not valid DHCPv6/PD handle" {}
                    return -code error $returnKeyedList 
                }
            }
        } else {
             ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory argument -handle." {}
            return -code error $returnKeyedList 
        }
        
        # checking unsupported switches under "modify" mode
        #set unsupportedModifyOptions {port_handle encap count}
        set unsupportedModifyOptions {port_handle count}

        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
                    ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        # create Dhcpv6PdBlockConfig or Dhcpv6BlockConfig under dhcpv6 device
        if {$::sth::Dhcpv6::dhcpv6Pd == 1} {        
            ::sth::Dhcpv6::processConfigSwitches emulation_dhcpv6pd_group_config $hostHandle modify returnKeyedList
        } else {   
            ::sth::Dhcpv6::processConfigSwitches emulation_dhcpv6_group_config $hostHandle modify returnKeyedList
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "dhcpv6_handle" $hostHandleList]
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_group_config_reset { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_group_config_reset"
    variable ::sth::Dhcpv6::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd

    if {$::sth::Dhcpv6::dhcpv6Pd == 1} {
       set configBlockObject "Dhcpv6PdBlockConfig"
    } else {
       set configBlockObject "Dhcpv6BlockConfig"
    }

    set retVal [catch {
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
            return $returnKeyedList
        }

        set deviceHandleList $userArgsArray(handle)
        
        foreach deviceHandle $deviceHandleList {
            if {![isDHCPv6DeviceHandleValid $deviceHandle $configBlockObject]} {
                ::sth::sthCore::processError returnKeyedList "Error: $deviceHandle is not valid DHCPv6/PD handle" {}
                return -code error $returnKeyedList 
            }
            
            ::sth::sthCore::invoke stc::perform Dhcpv6Abort -BlockList $deviceHandle
            
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


proc ::sth::Dhcpv6::emulation_dhcpv6_control_action { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_control_action"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd
    variable ::sth::Dhcpv6::userArgsArray

    set dhcpv6HandleList ""
    if {[info exists ::sth::Dhcpv6::userArgsArray(handle)]} {  
        foreach host $::sth::Dhcpv6::userArgsArray(handle) {
            if {[regexp -nocase "Dhcpv6BlockConfig|Dhcpv6PdBlockConfig" [::sth::sthCore::invoke stc::get $host -children] configBlockObject]} {
                if {[::sth::Dhcpv6::isDHCPv6DeviceHandleValid $host $configBlockObject]} {
                    set dhcpv6Block [::sth::sthCore::invoke stc::get $host -children-$configBlockObject]
                    lappend dhcpv6HandleList $dhcpv6Block
                }
            }
        } 
    } elseif {[info exists ::sth::Dhcpv6::userArgsArray(port_handle)]} {
		set portList $::sth::Dhcpv6::userArgsArray(port_handle)
		foreach ::sth::Dhcpv6::userArgsArray(port_handle) $portList {
			if {[::sth::sthCore::IsPortValid $::sth::Dhcpv6::userArgsArray(port_handle) err]} {
				set dhcpv6Hdl [::sth::sthCore::invoke stc::get $::sth::Dhcpv6::userArgsArray(port_handle) -affiliationport-sources]
				foreach host $dhcpv6Hdl {
					if {[regexp -nocase "Dhcpv6BlockConfig|Dhcpv6PdBlockConfig" [::sth::sthCore::invoke stc::get $host -children] configBlockObject]} {
						if {[::sth::Dhcpv6::isDHCPv6DeviceHandleValid $host $configBlockObject]} {
							set dhcpv6Block [::sth::sthCore::invoke stc::get $host -children-$configBlockObject]
							lappend dhcpv6HandleList $dhcpv6Block
						}
					}
				} 
			} else {
				::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::Dhcpv6::userArgsArray(port_handle)" {}
				return -code error $returnKeyedList
			}
		}
		set ::sth::Dhcpv6::userArgsArray(port_handle) $portList
    }

    if {$dhcpv6HandleList != ""} {
        switch -exact -- $::sth::Dhcpv6::userArgsArray(action) {
            "bind" {
                ::sth::sthCore::invoke stc::perform Dhcpv6Bind -BlockList $dhcpv6HandleList
            }
            "release" {
                #Note: Need to check there is an -RelaseMode attribute
                ::sth::sthCore::invoke stc::perform Dhcpv6Release -BlockList $dhcpv6HandleList
            }
            "renew" {
                ::sth::sthCore::invoke stc::perform Dhcpv6Renew -BlockList $dhcpv6HandleList
            }
            "rebind" {
                ::sth::sthCore::invoke stc::perform Dhcpv6Rebind -BlockList $dhcpv6HandleList
            }
            "abort" {
                ::sth::sthCore::invoke stc::perform Dhcpv6Abort -BlockList $dhcpv6HandleList
            }
            "inforeq" {
                ::sth::sthCore::invoke stc::perform Dhcpv6InfoRequest -BlockList $dhcpv6HandleList
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Unknown action $::sth::Dhcpv6::userArgsArray(action)."
                return -code error $returnKeyedList
            }
        }
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
}

proc ::sth::Dhcpv6::emulation_dhcpv6_get_stats { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_stats"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd
    variable ::sth::Dhcpv6::userArgsArray

    if {(![info exists ::sth::Dhcpv6::userArgsArray(port_handle)]) && (![info exists ::sth::Dhcpv6::userArgsArray(handle)])} {
            ## get the DHCP-PD port handle if no handle is input
        set hosts [::sth::sthCore::invoke stc::get $::sth::sthCore::GBLHNDMAP(project) -children-emulateddevice]
        set portList ""
        foreach host $hosts {
            if {[regexp -nocase "Dhcpv6BlockConfig|Dhcpv6PdBlockConfig" [::sth::sthCore::invoke stc::get $host -children] configBlockObject]} {
                if {[::sth::Dhcpv6::isDHCPv6DeviceHandleValid $host $configBlockObject]} {
                    set portHandle [::sth::sthCore::invoke stc::get $host -affiliationport-targets]
                    if {[lsearch $portList $portHandle] < 0} {lappend portList $portHandle}
                }
            }
        }
        set ::sth::Dhcpv6::userArgsArray(port_handle) $portList
    }
 
    set action "collect"
    if {[info exists ::sth::Dhcpv6::userArgsArray(action)]} {
        set action $::sth::Dhcpv6::userArgsArray(action)
    }
    if {![info exists ::sth::Dhcpv6::userArgsArray(mode)]} {
        if {[info exists ::sth::Dhcpv6::userArgsArray(port_handle)]} {
            set ::sth::Dhcpv6::userArgsArray(mode) "aggregate session"
        } else {
            set ::sth::Dhcpv6::userArgsArray(mode) "session"
        }
    }
        
    if {[catch {::sth::Dhcpv6::emulation_dhcpv6_stats_$action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}

proc ::sth::Dhcpv6::emulation_dhcpv6_stats_collect { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_stats_collect"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::dhcpv6Pd
    variable ::sth::Dhcpv6::userArgsArray

    array set portAgg ""
    set dchpv6Handle ""
    
    set retVal [catch {      
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            foreach port $portHandle {
                set portAgg($port) 0
                set dchpv6Host [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
                set dchpv6Handle "$dchpv6Handle $dchpv6Host"
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set dchpv6Handle $userArgsArray(handle)
        }
        
        foreach mode $userArgsArray(mode) {
            foreach handle $dchpv6Handle {
                set index 0
                # Get the DHCP handle
                if {![regexp -nocase "Dhcpv6BlockConfig|Dhcpv6PdBlockConfig" [::sth::sthCore::invoke stc::get $handle -children] configBlockObject]} { continue }
                # validate the handle
                if {![::sth::Dhcpv6::isDHCPv6DeviceHandleValid $handle $configBlockObject]} { continue }
                # get required handles
                set portHdl [::sth::sthCore::invoke stc::get $handle -affiliationport-targets]
                set dhcpv6PortHdl [::sth::sthCore::invoke stc::get $portHdl -children-Dhcpv6PortConfig]
                # Dhcpv6PortResults is automatically created from Dhcpv6PortConfig
                set dhcpv6PortResult [::sth::sthCore::invoke stc::get $dhcpv6PortHdl -children-Dhcpv6PortResults]
                set dhcpv6BlockHdl [::sth::sthCore::invoke stc::get $handle -children-$configBlockObject]
                # Dhcpv6BlockResults is automatically created from Dhcpv6PdBlockConfig
                set dhcpv6BlockResult [::sth::sthCore::invoke stc::get $dhcpv6BlockHdl -children-Dhcpv6BlockResults]

                # create an array mapping between stcObj and stcHandle
                set hdlArray(Dhcpv6PortResults) $dhcpv6PortResult
                set hdlArray(Dhcpv6BlockResults) $dhcpv6BlockResult
                
                if {$mode == "aggregate"} {
                    if {[info exists portAgg($portHdl)] && $portAgg($portHdl) == 1} {
                        continue
                    } else {
                        set portAgg($portHdl) 1
                    }
                }
                
                if {$mode == "session"} {
                    set state [::sth::sthCore::invoke stc::get $dhcpv6BlockHdl -BlockState]
                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.aggregate.state" $state]
                } elseif {$mode == "aggregate"} {
                    set state [::sth::sthCore::invoke stc::get $dhcpv6PortHdl -PortState]
                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.$portHdl.aggregate.state" $state]
                } elseif {$mode == "detailed_session"} {
                    set state [::sth::sthCore::invoke stc::get $dhcpv6BlockHdl -BlockState]
                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.aggregate.state" $state]
                    
                    ::sth::sthCore::invoke stc::perform Dhcpv6SessionInfoCommand  -blocklist $dhcpv6BlockHdl -SaveToFile FALSE 
                    set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpv6BlockHdl -children-Dhcpv6SessionResults]
                    set hdlArray(Dhcpv6SessionResults) $dhcpResultsHandle
                }
                
                foreach key [array names ::sth::Dhcpv6::emulation_dhcpv6_stats_mode] {
                    foreach {tblMode tblProc} $::sth::Dhcpv6::emulation_dhcpv6_stats_mode($key) {
                        if { $mode != "detailed_session"} {
                            if {[string match $tblMode $mode]} {
                                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: emulation_dhcpv6_stats $key supported] "false"]} {
                                    continue
                                }
                                
                                if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: emulation_dhcpv6_stats $key stcattr]] "_none_"]} {
                                    continue
                                }
                                
                                if {$tblMode == "aggregate"} {
                                    set stcObj $hdlArray(Dhcpv6PortResults)
                                    
                                    set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]
                                    
                                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.$portHdl.aggregate.$key" $val]
                                } elseif {$tblMode == "session"} {
                                    set stcObj $hdlArray(Dhcpv6BlockResults)
                                    
                                    set val 0
                                    foreach handle $stcObj {
                                        set val [expr $val + [::sth::sthCore::invoke stc::get $handle -$stcAttr]]
                                    }
                                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.aggregate.$key" $val]
                                }
                            }
                        } elseif {$mode == "detailed_session"} {
                            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: emulation_dhcpv6_stats $key supported] "false"]} {
                                continue
                            }
                            
                            if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: emulation_dhcpv6_stats $key stcattr]] "_none_"]} {
                                continue
                            }
                            
                            if {$tblMode == "session"} {
                                set stcObj $hdlArray(Dhcpv6BlockResults)
                                set val [::sth::sthCore::invoke stc::get $stcObj -$stcAttr]
                                set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.aggregate.$key" $val]
                            } elseif {$tblMode == "detailed_session"} {
                                set stcObj $hdlArray(Dhcpv6SessionResults)
                                set index 0
                                foreach handle $stcObj {
                                    incr index
                                    set val [::sth::sthCore::invoke stc::get $handle -$stcAttr]
                                    set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "ipv6.$dhcpv6BlockHdl.$index.$key" $val]
                                }
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

proc ::sth::Dhcpv6::emulation_dhcpv6_stats_clear { returnKeyedListVarName } {
    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_dhcpv6_stats_clear"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    variable ::sth::Dhcpv6::userArgsArray

    set retVal [catch {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            set dchpv6Handle [::sth::sthCore::invoke stc::get $portHandle -affiliationport-sources]
        } elseif {[info exists userArgsArray(handle)]} {
            foreach handle $userArgsArray(handle) {
                if {![::sth::Dhcpv6::isDHCPv6DeviceHandleValid $handle]} { 
                   ::sth::sthCore::processError returnKeyedList "Value ($handle) is not a valid Dhcpv6 handle"
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

proc ::sth::Dhcpv6::processConfigSwitches {userfunName handleList mode returnList } {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Dhcpv6::sortedSwitchPriorityList
    variable ::sth::Dhcpv6::userArgsArray
    upvar $returnList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dhcpv6:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    set objArray(configDhcpv6DelayedAuthKey) Dhcpv6DelayedAuthKey
    set objArray(configDhcpv6MsgOption) Dhcpv6MsgOption
    
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $deviceHandle -children-EthIIIf]
                    if {[string length $ethiiIf] != 0} {
                        configEthIIIntf $userfunName $ethiiIf $mode
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
                        configIpv6Intf $userfunName $ipv6If $mode
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
                        configVlanIfInner $userfunName $vlanIf $mode
                    }
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $deviceHandle -children-VlanIf]
                    if {[llength $vlanIf] != 0} {
                        if {[llength $vlanIf] < 2} {continue}            
                        set vlanIf [lindex $vlanIf 1]
                        configVlanIfOuter $userfunName $vlanIf $mode
                    }
                }

                configDhcpv6PdBlockConfig {
                    set dhcpv6PdBlockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6PdBlockConfig]

                    if {[llength $dhcpv6PdBlockCfg] != 0} {
                        configDhcpv6PdBlockConfig $dhcpv6PdBlockCfg $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Dhcpv6PdBlockConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configDhcpv6BlockConfig {
                    set dhcpv6BlockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6BlockConfig]
                    
                    if {[llength $dhcpv6BlockCfg] != 0} {                    
                        configDhcpv6BlockConfig $dhcpv6BlockCfg $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: Dhcpv6BlockConfig object missing" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configDhcpv6DelayedAuthKey {
                    set dhcpv6BlockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6BlockConfig]

                    set dhcpv6DelayedAuthKeyNum [inputListLength $objArray($func)]
                    for {set dhcpv6DelayedAuthKeyIndex 0} {$dhcpv6DelayedAuthKeyIndex < $dhcpv6DelayedAuthKeyNum} {incr dhcpv6DelayedAuthKeyIndex} {
                        set dhcpv6delayedAuthConfig [::sth::sthCore::invoke stc::create $objArray($func) -under $dhcpv6BlockCfg]
                        configDhcpv6DelayedAuthKey $dhcpv6delayedAuthConfig $mode $dhcpv6DelayedAuthKeyIndex
                    }
                }

                configDhcpv6MsgOption {
                    set dhcpv6BlockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6BlockConfig]
                    if {$dhcpv6BlockCfg eq ""} {
                        set dhcpv6BlockCfg [::sth::sthCore::invoke stc::get $deviceHandle -children-Dhcpv6PDBlockConfig]
                        if {$dhcpv6BlockCfg eq ""} {
                            ::sth::sthCore::processError returnKeyedList "no Dhcpv6BlockConfig or Dhcpv6PDBlockConfig configured: $err" {}
                            return $returnKeyedList
                        }
                    }

                    set dhcpv6MsgOptionNum [inputListLength $objArray($func)]
                    for {set dhcpv6MsgOptionIndex 0} {$dhcpv6MsgOptionIndex < $dhcpv6MsgOptionNum} {incr dhcpv6MsgOptionIndex} {
                        set dhcpv6MsgOptionConfig [::sth::sthCore::invoke stc::create $objArray($func) -under $dhcpv6BlockCfg]
                        configDhcpv6MsgOption $userfunName $dhcpv6MsgOptionConfig $mode $dhcpv6MsgOptionIndex
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

proc ::sth::Dhcpv6::configDhcpv6PortConfig { dhcpv6PortCfg mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_config configDhcpv6PortConfig $mode $dhcpv6PortCfg 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6PortCfg $optionValueList
    }
}

proc ::sth::Dhcpv6::configDhcpv6PdBlockConfig { dhcpv6PdBlockHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6pd_group_config configDhcpv6PdBlockConfig $mode $dhcpv6PdBlockHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6PdBlockHandle $optionValueList
    }
}

proc ::sth::Dhcpv6::configDhcpv6BlockConfig { dhcpv6BlockHandle mode } {

    set optionValueList [getStcOptionValueList emulation_dhcpv6_group_config configDhcpv6BlockConfig $mode $dhcpv6BlockHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6BlockHandle $optionValueList
    }
}

proc ::sth::Dhcpv6::configDhcpv6DelayedAuthKey { dhcpv6delayedAuthConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList emulation_dhcpv6_group_config configDhcpv6DelayedAuthKey $mode $dhcpv6delayedAuthConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6delayedAuthConfig $optionValueList
    }
}

proc ::sth::Dhcpv6::configDhcpv6MsgOption { userfunName dhcpv6MsgOptionConfig mode configIndex} {
    
    set optionValueList [getStcOptionValueList $userfunName configDhcpv6MsgOption $mode $dhcpv6MsgOptionConfig $configIndex]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpv6MsgOptionConfig $optionValueList
    }
}

proc ::sth::Dhcpv6::configEthIIIntf { userfunName ethHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configEthIIIntf $mode $ethHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethHandle $optionValueList
    }
}

proc ::sth::Dhcpv6::configVlanIfInner { userfunName vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $deviceHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList $userfunName configVlanIfInner $mode $deviceHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dhcpv6::configVlanIfOuter { userfunName vlanHandle mode } {
    set procName [lindex [info level [info level]] 0]
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanHandle -parent]
    
    if {[string length $vlanHandle] == 0} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: empty object handle" {}
        return -code error $returnKeyedList 
    }
    set optionValueList [getStcOptionValueList $userfunName configVlanIfOuter $mode $deviceHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanHandle $optionValueList
    }
}

proc ::sth::Dhcpv6::configIpv6Intf { userfunName ipv6ifHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configIpv6Intf $mode $ipv6ifHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6ifHandle $optionValueList
    }
}
proc ::sth::Dhcpv6::processRemoteId { switchName switchValue } {
    variable userArgsArray
    
    set suffixStart 0
    set suffixStep 1
    set suffixRepeat 0
    set suffixCount 1        

    if {![info exists userArgsArray($switchName\_suffix)] && ![info exists userArgsArray($switchName\_suffix_step)] && ![info exists userArgsArray($switchName\_suffix_count)]} {
        set switchValue $switchValue
    } else {
        if {[info exists userArgsArray($switchName\_suffix)]} {
            set suffixStart $userArgsArray($switchName\_suffix)
            if {[info exists userArgsArray($switchName\_suffix_repeat)]} {
                if {$userArgsArray($switchName\_suffix_repeat) >= 1} {
                    set suffixRepeat [expr {$userArgsArray($switchName\_suffix_repeat)-1}]
                }
            }
            if {[info exists userArgsArray($switchName\_suffix_step)]} {
                set suffixStep $userArgsArray($switchName\_suffix_step)
            }
            if {[info exists userArgsArray($switchName\_suffix_count)]} {
                set suffixCount $userArgsArray($switchName\_suffix_count)
            }
            set hexsuffixStart [format "%x" $suffixStart]
            set switchValue "@\$($switchValue$hexsuffixStart,$suffixCount,$suffixStep,1,$suffixRepeat)"
        }
    }

    set remoteIdCfg "-RemoteId {$switchValue}"
    return $remoteIdCfg
}
proc ::sth::Dhcpv6::processConfigCmd_vlanId { myswitch value } {
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
        if {$userArgsArray(encap) == "ethernet_ii_qinq"} {
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
        } elseif {$userArgsArray(encap) == "ethernet_ii_vlan"} {
            lappend vlanCfg -IfRecycleCount $count
        }
        if {$mode == "increment"} {
            lappend vlanCfg -IdStep $step
        } elseif {$mode == "fixed"} {
            lappend vlanCfg -IdStep 0
        }
        
        lappend vlanCfg -VlanId $value
        
    } elseif {$myswitch == "vlan_id_outer"} {
        
        if {$userArgsArray(encap) != "ethernet_ii_qinq"} { return }
        
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

proc ::sth::Dhcpv6::getStcOptionValueList {cmdType modeFunc mode procFuncHandle confgIndex} {
    
    set optionValueList {}
    
    foreach item $::sth::Dhcpv6::sortedSwitchPriorityList {
        set opt [lindex $item 1]
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $cmdType $opt supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$opt\" is not supported."
                return -code error $returnKeyedList
            }

            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Dhcpv6:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                
                #check dependency
                ::sth::Dhcpv6::checkDependency $cmdType $opt $modeFunc $mode
                if {![info exists ::sth::Dhcpv6::userArgsArray($opt)]} { continue }
                
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Dhcpv6:: $cmdType $opt $::sth::Dhcpv6::userArgsArray($opt)} value]} {
        		lappend optionValueList -$stcAttr $value
        	    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::Dhcpv6::userArgsArray($opt) $confgIndex]
        	    }
                } else {
                    set value [lindex $::sth::Dhcpv6::userArgsArray($opt) $confgIndex]
                    eval lappend optionValueList [$processFunc $opt $value]
                }
            }
    }
    return $optionValueList
}

proc ::sth::Dhcpv6::checkDependency {cmdType switchName modeFunc mode} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::Dhcpv6:: $cmdType $switchName dependency]] "_none_"]} {
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

proc ::sth::Dhcpv6::isDHCPv6DeviceHandleValid { handle blockConfigObject} {
    
    set cmdStatus 1    
    if {[catch {set hostHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {
        ::sth::sthCore::log debug "No host exists under Project Handle:$::sth::GBLHNDMAP(project) $err"
	return $::sth::sthCore::FAILURE
    } else {
	foreach hostHandle $hostHandleList {
	    if {[string equal $hostHandle $handle]} {
		set cmdStatus 1
		break
	    }
	}

        if {[catch {set dhcpv6Handle [::sth::sthCore::invoke stc::get $handle -children-$blockConfigObject]} err]} {
	    set cmdStatus 0
	}
        
        if {[string length $dhcpv6Handle] == 0} {
            set cmdStatus 0
        }

	if {$cmdStatus == 1} {
	    return $::sth::sthCore::SUCCESS
	} else {
	    return $::sth::sthCore::FAILURE		
	}		
    }
}

proc ::sth::Dhcpv6::inputListLength {optionObject} {
    
    variable len
    variable userArgsArray
    variable sortedSwitchPriorityList
    set len -1
    switch -- $optionObject {
        Dhcpv6DelayedAuthKey {
            set optionList {dhcp6_delayed_auth_key_id dhcp6_delayed_auth_key_value}
        }
        Dhcpv6MsgOption {
            set optionList {option_value option_payload enable_wildcards string_as_hex_value include_in_message remove_option}
        }
        default {
            ::sth::sthCore::processError returnKeyedList "$optionObject should be Dhcpv6DelayedAuthKey/Dhcpv6MsgOption " {}
            return -code error $returnKeyedList 
        }
    }
    foreach switchname $optionList {
        if {![info exists userArgsArray($switchname)]} {
            ::sth::sthCore::processError returnKeyedList "Should input $switchname in sth::emulation_dhcpv6_group_config" {}
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