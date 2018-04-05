# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Ancp {
    set createResultQuery 0
    variable ancp_subscribe_state 0
    # bool variable ether_encap indicates whether the ANCP host is over EthernetII encapsulation
    array set ether_encap ""
}


proc ::sth::Ancp::emulation_ancp_config_create { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_config_create $rklName"
	
	upvar 1 $rklName returnKeyedList
	variable ipv4Version
	variable ipv6Version
	
	# check if the port_handle value is valid
	if {[info exists ::sth::Ancp::userArgsArray(port_handle)]} {
		set portHandle $::sth::Ancp::userArgsArray(port_handle)
		if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
		    return -code error "Invalid value of \"-port_handle\" $portHandle"
	    }
	} else {
		return -code error "\"-port_handle\" is mandatory in enable mode"
	}
	
	# set default values for non-user defined switches
	foreach key [array names ::sth::Ancp::emulation_ancp_config_default] {
	    if {![info exists ::sth::Ancp::userArgsArray($key)]} {
	        set defaultValue [::sth::sthCore::getswitchprop ::sth::Ancp:: emulation_ancp_config $key default]
	        if {![string match $defaultValue "_none_"]} {
	            set ::sth::Ancp::userArgsArray($key) $defaultValue
	        }
	    }
	}
        
        set deviceCount $::sth::Ancp::userArgsArray(device_count)
        
        set macAddr $::sth::Ancp::userArgsArray(local_mac_addr)
        set macStep $::sth::Ancp::userArgsArray(local_mac_step)
        
        if {[info exists ::sth::Ancp::userArgsArray(vlan_id)]} {
            set vlanId $::sth::Ancp::userArgsArray(vlan_id)
            if {[llength $vlanId] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(vlan_id_count)]} {
                   set vlanRepeat [expr $deviceCount/$::sth::Ancp::userArgsArray(vlan_id_count)]
                    if {[expr $deviceCount%$::sth::Ancp::userArgsArray(vlan_id_count)] != 0} {
                       incr vlanRepeat
                    }
                } elseif {[info exists ::sth::Ancp::userArgsArray(vlan_id_repeat)]} {
                   set vlanRepeat $::sth::Ancp::userArgsArray(vlan_id_repeat)
                } 
                set vlanStep 0
                if {[info exists ::sth::Ancp::userArgsArray(vlan_id_step)]} {
                   set vlanStep $::sth::Ancp::userArgsArray(vlan_id_step)
                } elseif {[info exists vlanRepeatCount]} {
                   set vlanStep 1
                }
                if {![info exists vlanRepeat]} {
                    set vlanRepeat $deviceCount
                }
                set vlanRepeatCount $vlanRepeat 
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(vlan_id_inner)]} {
            set vlanInnerId $::sth::Ancp::userArgsArray(vlan_id_inner)
            if {[llength $vlanInnerId] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(vlan_id_count_inner)]} {
                   set vlanInnerRepeat [expr $deviceCount/$::sth::Ancp::userArgsArray(vlan_id_count_inner)]
                   if {[expr $deviceCount%$::sth::Ancp::userArgsArray(vlan_id_count_inner)]} {
                       incr vlanInnerRepeat
                   }
                } elseif {[info exists ::sth::Ancp::userArgsArray(vlan_id_repeat_inner)]} {
                   set vlanInnerRepeat $::sth::Ancp::userArgsArray(vlan_id_repeat_inner)
                } 
                set vlanInnerStep 0
                if {[info exists ::sth::Ancp::userArgsArray(vlan_id_step_inner)]} {
                   set vlanInnerStep $::sth::Ancp::userArgsArray(vlan_id_step_inner)
                } elseif {[info exists vlanRepeatCount]} {
                   set vlanInnerStep 1
                }
                if {![info exists vlanInnerRepeat]} {
                    set vlanInnerRepeat $deviceCount
                }
                set vlanInnerRepeatCount $vlanInnerRepeat
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(local_mac_addr)]} {
            set macAddr $::sth::Ancp::userArgsArray(local_mac_addr)
            if {[llength $macAddr] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(local_mac_repeat)]} {
                   set macAddrRepeat $::sth::Ancp::userArgsArray(local_mac_repeat)
                }
                set macStep 0
                if {[info exists ::sth::Ancp::userArgsArray(local_mac_step)]} {
                   set macStep $::sth::Ancp::userArgsArray(local_mac_step)
                } elseif {[info exists macAddrRepeat]} {
                   set macStep "00:00:00:00:00:01"
                }
                if {![info exists macAddrRepeat]} {
                    set macAddrRepeat 1
                }
                set macAddrRepeatCount $macAddrRepeat
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(intf_ip_addr)]} {
            set ipAddr $::sth::Ancp::userArgsArray(intf_ip_addr)
            if {[llength $ipAddr] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(intf_ip_repeat)]} {
                   set ipAddrRepeat $::sth::Ancp::userArgsArray(intf_ip_repeat)
                }
                set ipAddrStep 0
                if {[info exists ::sth::Ancp::userArgsArray(intf_ip_step)]} {
                   set ipAddrStep $::sth::Ancp::userArgsArray(intf_ip_step)
                } elseif {[info exists ipAddrRepeat]} {
                   set ipAddrStep 0.0.0.1
                }
                if {![info exists ipAddrRepeat]} {
                    set ipAddrRepeat 1
                }
                set ipAddrRepeatCount $ipAddrRepeat
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(gateway_ip_addr)]} {
            set gwAddr $::sth::Ancp::userArgsArray(gateway_ip_addr)
            if {[llength $gwAddr] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(gateway_ip_repeat)]} {
                   set gwRepeat $::sth::Ancp::userArgsArray(gateway_ip_repeat)
                }
                set gwStep 0
                if {[info exists ::sth::Ancp::userArgsArray(gateway_ip_step)]} {
                   set gwStep $::sth::Ancp::userArgsArray(gateway_ip_step)
                } elseif {[info exists gwRepeat]} {
                   set gwStep 0.0.0.1
                }
                if {![info exists gwRepeat]} {
                    set gwRepeat $deviceCount
                }
                set gwRepeatCount $gwRepeat
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(sut_ip_addr)]} {
            set sutAddr $::sth::Ancp::userArgsArray(sut_ip_addr)
            if {[llength $sutAddr] == 1} {
                if {[info exists ::sth::Ancp::userArgsArray(sut_ip_repeat)]} {
                   set sutRepeat $::sth::Ancp::userArgsArray(sut_ip_repeat)
                }
                set sutStep 0
                if {[info exists ::sth::Ancp::userArgsArray(sut_ip_step)]} {
                   set sutStep $::sth::Ancp::userArgsArray(sut_ip_step)
                } elseif {[info exists sutRepeat]} {
                   set sutStep 0.0.0.1
                }
                if {![info exists sutRepeat]} {
                    set sutRepeat $deviceCount
                }
                set sutRepeatCount $sutRepeat
            }
        }
        
        for {set i 0} {$i < $deviceCount} {incr i} {
            
            #set ipAddr $::sth::Ancp::userArgsArray(intf_ip_addr) 
            #set ipStep $::sth::Ancp::userArgsArray(intf_ip_step)
            #if {[llength $ipAddr] > 1} {
            #    set ipAddrConfig [lindex $ipAddr $i]
            #} else {
            #    set ipAddrConfig [::sth::sthCore::updateIpAddress 4 $ipAddr $ipStep $i]
            #}
            
            #create ipif
            if {[llength $ipAddr] > 1} {
                set ipAddrConfig [lindex $ipAddr $i]
            } else {
                if {$i == 0} {
                    set ipAddrConfig $ipAddr
                }
                if {$ipAddrRepeatCount == 0} {
                       set ipAddrConfig [::sth::sthCore::updateIpAddress 4 $ipAddrConfig $ipAddrStep 1]
                       set ipAddrRepeatCount $ipAddrRepeat
                }
                incr ipAddrRepeatCount -1
            }
            
            set rtrHandle [::sth::sthCore::invoke stc::create Router -under $::sth::GBLHNDMAP(project) "-RouterId $ipAddrConfig"]
            
            
            
            #create MAC
            #set macAddr $::sth::Ancp::userArgsArray(local_mac_addr)
            #set macStep $::sth::Ancp::userArgsArray(local_mac_step)
            #if {[llength $macAddr] > 1} {
            #    set macAddrConfig [lindex $macAddr $i]
            #} else {
            #    set macAddrConfig [::sth::sthCore::macStep $macAddr $macStep $i]
            #}
            
	    # add ATM and ATM_EthernetII (EthernetII over ATM) encapsulation
	    # by xiaozhi, 6/3/2009
	    
	    switch -- $::sth::Ancp::userArgsArray(encap_type) {
		ETHERNETII {
		    if {[llength $macAddr] > 1} {
			set macAddrConfig [lindex $macAddr $i]
		    } else {
			if {$i == 0} {
			    set macAddrConfig $macAddr
			}
			if {$macAddrRepeatCount == 0} {
			       set macAddrConfig [::sth::sthCore::macStep $macAddr $macStep $i]
			       set macAddrRepeatCount $macAddrRepeat
			}
			incr macAddrRepeatCount -1
		    }
		    set macHandle [::sth::sthCore::invoke stc::create EthIIIf -under $rtrHandle "-SourceMac $macAddrConfig"]
		    set lowerIf $macHandle
		    set ::sth::Ancp::ether_encap($rtrHandle) 1
		}
		LLC_SNAP {
		    set atmConfig [configAtmSettings $i]
                    
                    set atmHandle [::sth::sthCore::invoke stc::create Aal5If -under $rtrHandle "-VcEncapsulation LLC_ENCAPSULATED $atmConfig"]
                    
		    set lowerIf $atmHandle
                    set ::sth::Ancp::ether_encap($rtrHandle) 0 
		}
		VC_MUX {
                    set atmConfig [configAtmSettings $i]
                    
		    set atmHandle [::sth::sthCore::invoke stc::create Aal5If -under $rtrHandle "-VcEncapsulation VC_MULTIPLEXED $atmConfig"]
		    set lowerIf $atmHandle
                    set ::sth::Ancp::ether_encap($rtrHandle) 0
		}
		ATM_LLC_SNAP_ETHERNETII {          
                    if {[llength $macAddr] > 1} {
			set macAddrConfig [lindex $macAddr $i]
		    } else {
			if {$i == 0} {
			    set macAddrConfig $macAddr
			}
			if {$macAddrRepeatCount == 0} {
			       set macAddrConfig [::sth::sthCore::macStep $macAddr $macStep $i]
			       set macRepeatCount $macAddrRepeat
			}
			incr macAddrRepeatCount -1
		    }
		    set macHandle [::sth::sthCore::invoke stc::create EthIIIf -under $rtrHandle "-SourceMac $macAddrConfig"]
                    
                    set atmConfig [configAtmSettings $i]
                    
		    set atmHandle [::sth::sthCore::invoke stc::create Aal5If -under $rtrHandle "-VcEncapsulation LLC_ENCAPSULATED $atmConfig"]
                    ::sth::sthCore::invoke stc::config $macHandle "-StackedOnEndpoint-targets $atmHandle"
                    set lowerIf $macHandle
                    set ::sth::Ancp::ether_encap($rtrHandle) 1
		}
		ATM_VC_MUX_ETHERNETII {
                    if {[llength $macAddr] > 1} {
			set macAddrConfig [lindex $macAddr $i]
		    } else {
			if {$i == 0} {
			    set macAddrConfig $macAddr
			}
			if {$macAddrRepeatCount == 0} {
			       set macAddrConfig [::sth::sthCore::macStep $macAddr $macStep $i]
			       set macRepeatCount $macAddrRepeat
			}
			incr macAddrRepeatCount -1
		    }
		    set macHandle [::sth::sthCore::invoke stc::create EthIIIf -under $rtrHandle "-SourceMac $macAddrConfig"]
                    
                    set atmConfig [configAtmSettings $i]
                    
		    set atmHandle [::sth::sthCore::invoke stc::create Aal5If -under $rtrHandle "-VcEncapsulation LLC_ENCAPSULATED"]
                    ::sth::sthCore::invoke stc::config $macHandle "-StackedOnEndpoint-targets $atmHandle"
                    set lowerIf $macHandle
                    set ::sth::Ancp::ether_encap($rtrHandle) 1
		}
	    }
	    
            #creat outer vlan
            if {$::sth::Ancp::ether_encap($rtrHandle) == 1} {
                if {[info exists vlanId]} {
                    if {[llength $vlanId] > 1} {
                       set vlanIdConfig [lindex $vlanId $i]
                    } else {
                        if {$i == 0} {
                           set vlanIdConfig $vlanId
                        }
                        if {$vlanRepeatCount == 0} {
                           set vlanIdConfig [expr $vlanIdConfig + $vlanStep]
                           set vlanRepeatCount $vlanRepeat
                        }
                       incr vlanRepeatCount -1
                    }
                    set vlanHandle [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle "-VlanId $vlanIdConfig"]
                    ::sth::sthCore::invoke stc::config $vlanHandle "-StackedOnEndpoint-targets $lowerIf"
                    set lowerIf $vlanHandle
                }
            }
            
            #create inner vlan
            if {$::sth::Ancp::ether_encap($rtrHandle) == 1} { 
                if {[info exists vlanInnerId]} {
                    if {[llength $vlanInnerId] > 1} {
                       set vlanInnerIdConfig [lindex $vlanInnerId]
                    } else {
                        if {$i == 0} {
                           set vlanInnerIdConfig $vlanInnerId
                        }
                        if {$vlanInnerRepeatCount == 0} {
                           set vlanInnerIdConfig [expr $vlanInnerIdConfig + $vlanInnerStep]
                           set vlanInnerRepeatCount $vlanInnerRepeat
                       }
                       incr vlanInnerRepeatCount -1
                    }
                    set vlanInnerHandle [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle "-VlanId $vlanInnerIdConfig"]
                    ::sth::sthCore::invoke stc::config $vlanInnerHandle "-StackedOnEndpoint-targets $lowerIf"
                    set lowerIf $vlanInnerHandle
                }
            }
            
            #create ipif
            if {[llength $gwAddr] > 1} {
                set gwAddrConfig [lindex $gwAddr $i]
            } else {
                if {$i == 0} {
                    set gwAddrConfig $gwAddr
                }
                if {$gwRepeatCount == 0} {
                       set gwAddrConfig [::sth::sthCore::updateIpAddress 4 $gwAddrConfig $gwStep 1]
                       set gwRepeatCount $gwRepeat
                }
                incr gwRepeatCount -1
            }
            set prefixLen $::sth::Ancp::userArgsArray(intf_ip_prefix_len)
            set ipHandle [::sth::sthCore::invoke stc::create Ipv4If -under $rtrHandle "-Address $ipAddrConfig -Gateway $gwAddrConfig -prefixLength $prefixLen"]
            
            ::sth::sthCore::invoke stc::config $ipHandle "-StackedOnEndpoint-targets $lowerIf"
            ::sth::sthCore::invoke stc::config $rtrHandle "-TopLevelIf-targets $ipHandle"
            ::sth::sthCore::invoke stc::config $rtrHandle "-PrimaryIf-targets $ipHandle"
            
            
            set options ""
            # not support
            if {[info exists sutAddr]} {
                if {[llength $sutAddr] > 1} {
                    set sutAddrConfig [lindex $sutAddr $i]
                } else {
                    if {$i == 0} {
                        set sutAddrConfig $sutAddr
                    }
                    if {$sutRepeatCount == 0} {
                       set sutAddrConfig [::sth::sthCore::updateIpAddress 4 $sutAddrConfig $sutStep 1]
                       set sutRepeatCount $sutRepeat
                    }
                    incr sutRepeatCount -1
                }
               
            }
            if {[info exists ::sth::Ancp::userArgsArray(ancp_standard)]} {
                if {$::sth::Ancp::userArgsArray(ancp_standard) == "ietf-ancp-protocol2"} {
                    lappend options "-AncpVersion" "ANCP_DRAFT_02"
                } elseif {$::sth::Ancp::userArgsArray(ancp_standard) == "gsmp-l2control-config2"} {
                    lappend options "-AncpVersion" "L2CP_DRAFT_00"
                } else {
                    lappend options "-AncpVersion" "RFC_6320"
                    if {[info exists ::sth::Ancp::userArgsArray(partition_type)]} {
                        lappend options "-PartitionType" $::sth::Ancp::userArgsArray(partition_type)
                    }
                    if {[info exists ::sth::Ancp::userArgsArray(partition_flag)]} {
                        lappend options "-PartitionFlag" $::sth::Ancp::userArgsArray(partition_flag)
                    }
                    if {[info exists ::sth::Ancp::userArgsArray(partition_id)]} {
                        lappend options "-PartitionId" $::sth::Ancp::userArgsArray(partition_id)
                    }
                    if {[info exists ::sth::Ancp::userArgsArray(code)]} {
                        lappend options "-Code" $::sth::Ancp::userArgsArray(code)
                    }
                }
            }
	    if {[info exists ::sth::Ancp::userArgsArray(topology_discovery)]} {
	        lappend options "-EnableDynamicTopologyDiscovery" $::sth::Ancp::userArgsArray(topology_discovery) 
	    }
            if {[info exists ::sth::Ancp::userArgsArray(bulk_transaction)]} {
	        lappend options "-EnableBulkTransaction" $::sth::Ancp::userArgsArray(bulk_transaction) 
	    }
            if {[info exists ::sth::Ancp::userArgsArray(tcp_port)]} {
	        lappend options "-TcpPort" $::sth::Ancp::userArgsArray(tcp_port) 
	    }
            if {[info exists ::sth::Ancp::userArgsArray(keep_alive)]} {
	        lappend options "-AncpKeepAliveTimeout" $::sth::Ancp::userArgsArray(keep_alive) 
	    }
            #create ancp
            set ancpHandle [::sth::sthCore::invoke stc::create AncpAccessNodeConfig -under $rtrHandle $options]
            
            set accessLoopBlockHandle [::sth::sthCore::invoke stc::create AncpAccessLoopBlockConfig -under $ancpHandle]
set AncpLoopTlvConfig [::sth::sthCore::invoke stc::create AncpTlvConfig -under $accessLoopBlockHandle]
            
            #configure the peer address
            set ipv4NetworkBlock [::sth::sthCore::invoke stc::get $ancpHandle -children-ipv4networkblock]
            ::sth::sthCore::invoke stc::config $ipv4NetworkBlock "-StartIpList $sutAddrConfig"
            set prefixLen $::sth::Ancp::userArgsArray(sut_ip_prefix_len)
            ::sth::sthCore::invoke stc::config $ipv4NetworkBlock "-PrefixLength $prefixLen"
           
            ::sth::sthCore::invoke stc::config $rtrHandle "-AffiliationPort-targets $portHandle"
            lappend routers $rtrHandle 
        }
	
    # apply config
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        # if apply fails, delete any routers we may have created
        foreach rtr $routers {
            ::sth::sthCore::invoke stc::delete $rtr
        }
        return -code error $applyError
    }
    
    
    # prepare the keyed list to be returned to HLTAPI layer
    if {[catch { keylset returnKeyedList handle $routers } err]} {
	::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. $err"
    }	

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    return $returnKeyedList
}

###
#  Name:    emulation_ancp_config_modify
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Modify ancp router.
###
proc ::sth::Ancp::emulation_ancp_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_config_modify $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	if {![info exists ::sth::Ancp::userArgsArray(handle)]} {
		return -code error "the switch \"-handle\" is mandatory in modify mode"
	} else {
	    set rtrHandle $::sth::Ancp::userArgsArray(handle)
		if {![::sth::Ancp::isAncpRouterHandleValid $rtrHandle]} {
			return -code error "Invalid ancp router handle $rtrHandle"
		}
	}
	

    # Modify the Ethiiif if needed
    
    # add ATM and ATM_EthernetII (EthernetII over ATM) encapsulation
    # by xiaozhi, 6/3/2009
    if {$::sth::Ancp::ether_encap($rtrHandle) == 1} {
        if {[info exists ::sth::Ancp::userArgsArray(local_mac_addr)]} {
            set ethHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
            ::sth::sthCore::invoke stc::config $ethHandle "-SourceMac $::sth::Ancp::userArgsArray(local_mac_addr)"
        }
    
        # if input is inner_vlan, but there are only single vlan, create qinq here.
        if {[info exists ::sth::Ancp::userArgsArray(vlan_id_inner)] || [info exists ::sth::Ancp::userArgsArray(vlan_id)]} {
            set vlanHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif]
            if {[llength $vlanHandle] == 1} {
                set outerVlan $vlanHandle
                if {[info exists ::sth::Ancp::userArgsArray(vlan_id_inner)]} {
                    set innerVlan [::sth::sthCore::invoke stc::create vlanif -under $rtrHandle "-VlanId $::sth::Ancp::userArgsArray(vlan_id_inner)"]
                    #modify the stack relation
                    set ipHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv4if]
                    ::sth::sthCore::invoke stc::config $innerVlan "-StackedOnEndpoint-targets $outerVlan"
                    ::sth::sthCore::invoke stc::config $ipHandle "-StackedOnEndpoint-targets $innerVlan"
                }
            } elseif {[llength $vlanHandle] == 0} {
                set innerVlan [::sth::sthCore::invoke stc::create vlanif -under $rtrHandle]
                set outerVlan [::sth::sthCore::invoke stc::create vlanif -under $rtrHandle]
                set ipHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv4if]
                set ethHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                ::sth::sthCore::invoke stc::config $innerVlan "-StackedOnEndpoint-targets $outerVlan"
                ::sth::sthCore::invoke stc::config $ipHandle "-StackedOnEndpoint-targets $innerVlan"
                ::sth::sthCore::invoke stc::config $outerVlan "-StackedOnEndpoint-targets $ethHandle"
            
            } else {
                set outerVlan [lindex $vlanHandle 0]
                set innerVlan [lindex $vlanHandle 1]
            }
            if {[info exists ::sth::Ancp::userArgsArray(vlan_id_inner)]} {
                ::sth::sthCore::invoke stc::config $innerVlan "-VlanId $::sth::Ancp::userArgsArray(vlan_id_inner)"
            }
            if {[info exists ::sth::Ancp::userArgsArray(vlan_id)]} {
                ::sth::sthCore::invoke stc::config $outerVlan "-VlanId $::sth::Ancp::userArgsArray(vlan_id)"
            }
        }
        
        #modify vci or vpi under ATM_EthernetII encapsulation
        set atmHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-aal5if]
        
        if {[string length $atmHandle] != 0} {
            if {[info exists ::sth::Ancp::userArgsArray(vci)] || [info exists ::sth::Ancp::userArgsArray(vpi)]} {
                
                set vci ""
                set vpi ""
                if {[info exists ::sth::Ancp::userArgsArray(vci)]} {
                    set vci $::sth::Ancp::userArgsArray(vci)
                }
                if {[info exists ::sth::Ancp::userArgsArray(vpi)]} {
                    set vpi $::sth::Ancp::userArgsArray(vpi)
                }
                set atmSettings "-vci $vci -vpi $vpi"
                
                ::sth::sthCore::invoke stc::config $atmHandle $atmSettings
            }
        } else {
            # restrict modifing vci and vpi over EthernetII encapsulation
            foreach attr {vci vci_step vpi vpi_step} {
                if {[info exists ::sth::Ancp::userArgsArray($attr)]} {
                    ::sth::sthCore::processError returnKeyedList "switch -$attr can not be modified over EthernetII encapsulation."
                    return $returnKeyedList
                }
            }
        }         
    } else {
        # restrict modifing mac and vlan arguments over ATM encapsulations
        foreach attr {local_mac_addr local_mac_step local_mac_repeat remote_mac_addr remote_mac_step remote_mac_repeat \
                vlan_id_inner vlan_id_count_inner vlan_id_repeat_inner vlan_id_step_inner vlan_id vlan_id_count vlan_id_repeat vlan_id_step} {
            if {[info exists ::sth::Ancp::userArgsArray($attr)]} {
                ::sth::sthCore::processError returnKeyedList "switch -$attr can not be modified over ATM encapsulation."
                return $returnKeyedList
            }
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(vci)] || [info exists ::sth::Ancp::userArgsArray(vpi)]} {
            
            set vci ""
            set vpi ""
            if {[info exists ::sth::Ancp::userArgsArray(vci)]} {
                set vci $::sth::Ancp::userArgsArray(vci)
            }
            if {[info exists ::sth::Ancp::userArgsArray(vpi)]} {
                set vpi $::sth::Ancp::userArgsArray(vpi)
            }
            set atmSettings "-vci $vci -vpi $vpi"
            
            set atmHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-Aal5If]
            ::sth::sthCore::invoke stc::config $atmHandle $atmSettings
        }
    }
    
    set ipHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv4if]
    
    if {[info exists ::sth::Ancp::userArgsArray(intf_ip_addr)]} {
        ::sth::sthCore::invoke stc::config $ipHandle "-Address $::sth::Ancp::userArgsArray(intf_ip_addr)"
    }
    
    if {[info exists ::sth::Ancp::userArgsArray(gateway_ip_addr)]} {
        ::sth::sthCore::invoke stc::config $ipHandle "-Gateway $::sth::Ancp::userArgsArray(gateway_ip_addr)"
    }
    
    set ancpHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ancpaccessnodeconfig]
    if {[info exists ::sth::Ancp::userArgsArray(sut_ip_addr)]} {
        set ipv4NetworkBlock [::sth::sthCore::invoke stc::get $ancpHandle -children-ipv4networkblock]
        ::sth::sthCore::invoke stc::config $ipv4NetworkBlock "-StartIpList $::sth::Ancp::userArgsArray(sut_ip_addr)"
        set prefixLen $::sth::Ancp::userArgsArray(sut_ip_prefix_len)
        ::sth::sthCore::invoke stc::config $ipv4NetworkBlock "-PrefixLength $prefixLen"
    }
    if {[info exists ::sth::Ancp::userArgsArray(ancp_standard)]} {
        if {$::sth::Ancp::userArgsArray(ancp_standard) == "ietf-ancp-protocol2"} {
            set ancpVersion "ANCP_DRAFT_02"
        } elseif {$::sth::Ancp::userArgsArray(ancp_standard) == "gsmp-l2control-config2"} {
            set ancpVersion "L2CP_DRAFT_00"
        } else {
            set ancpVersion "RFC_6320"
        }
        ::sth::sthCore::invoke stc::config $ancpHandle "-AncpVersion $ancpVersion"
        if {$ancpVersion == "RFC_6320"} {
            if {[info exists ::sth::Ancp::userArgsArray(partition_type)]} {
                ::sth::sthCore::invoke stc::config $ancpHandle "-PartitionType $::sth::Ancp::userArgsArray(partition_type)"
            }
            if {[info exists ::sth::Ancp::userArgsArray(partition_flag)]} {
                ::sth::sthCore::invoke stc::config $ancpHandle "-PartitionFlag $::sth::Ancp::userArgsArray(partition_flag)"
            }
            if {[info exists ::sth::Ancp::userArgsArray(partition_id)]} {
                ::sth::sthCore::invoke stc::config $ancpHandle "-PartitionId $::sth::Ancp::userArgsArray(partition_id)"
            }
            if {[info exists ::sth::Ancp::userArgsArray(code)]} {
                ::sth::sthCore::invoke stc::config $ancpHandle "-Code $::sth::Ancp::userArgsArray(code)"
            }
        }
    }
    if {[info exists ::sth::Ancp::userArgsArray(topology_discovery)]} {
        ::sth::sthCore::invoke stc::config $ancpHandle "-EnableDynamicTopologyDiscovery $::sth::Ancp::userArgsArray(topology_discovery)"
    }
    if {[info exists ::sth::Ancp::userArgsArray(keep_alive)]} {
         ::sth::sthCore::invoke stc::config $ancpHandle "-AncpKeepAliveTimeout $::sth::Ancp::userArgsArray(keep_alive)"
    }
    if {[info exists ::sth::Ancp::userArgsArray(tcp_port)]} {
         ::sth::sthCore::invoke stc::config $ancpHandle "-TcpPort $::sth::Ancp::userArgsArray(tcp_port)"
    }
    if {[info exists ::sth::Ancp::userArgsArray(bulk_transaction)]} {
	::sth::sthCore::invoke stc::config $ancpHandle "-EnableBulkTransaction $::sth::Ancp::userArgsArray(bulk_transaction)"
    }
    
    if {[catch {::sth::sthCore::doStcApply } err]} {
        return -code error "Error applying config: $err"
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::Ancp::emulation_ancp_config_delete { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_config_disable $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	# user can specify port_handle, which will remove all ancp routers under it. Or specify specific router handles
	if {[info exists ::sth::Ancp::userArgsArray(port_handle)]} {
            set portHandle $::sth::Ancp::userArgsArray(port_handle)
    	    if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
    		return -code error "Invalid \"-port_handle\" value $portHandle"
    	    }
    	    set affRouters [::sth::sthCore::invoke stc::get $portHandle -affiliationport-sources]
    	    # verify which of these routers are ANCP routers
    	    set ancpRouters {}
    	    foreach rtr $affRouters {
    	        if {[isAncpRouterHandleValid $rtr]} {
		    lappend ancpRouters $rtr
	        }
    	    }
	} elseif {[info exists ::sth::Ancp::userArgsArray(handle)]} {
	    set ancpRouters $::sth::Ancp::userArgsArray(handle)
	    foreach rtr $ancpRouters {
	        if {![isAncpRouterHandleValid $rtr]} {
	            return -code error "$rtr is not a valid ANCP router."   
	        }
	    }
	} else {
	    return -code error "must specify either \"-port_handle\" or \"-handle\"."
	}
	
	foreach ancpRtr $ancpRouters {
		::sth::sthCore::invoke stc::delete $ancpRtr
	}
        
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}


proc ::sth::Ancp::emulation_ancp_control {handle rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_control $rklName"
    variable ancp_subscribe_state
    upvar 1 $rklName returnKeyedList
    
    if {$ancp_subscribe_state == 0} {
        set portList {}
        if {$handle == "all"} {
            set portList [::sth::sthCore::invoke stc::get [lindex [stc::get system1 -children-Project] 0] -children-port]
        } else {
            foreach rt $handle {
                set port [::sth::sthCore::invoke stc::get $rt -affiliationport-Targets]
                if {[lsearch $portList $port] == -1} {
                    lappend portList $port
                }
            }
        }
        #puts "Subscribing ANCP Port Results..."
        set Subscriptions(AncpPortResults) [::sth::sthCore::invoke stc::subscribe \
            -Parent $::sth::GBLHNDMAP(project) \
            -ResultParent $portList  \
            -ConfigType AncpPortConfig \
            -ResultType AncpPortResults \
            -interval 1]
            
        #puts "Subscribing ANCP Access Node Results..."
        set Subscriptions(AncpAccessNodeResults) [::sth::sthCore::invoke stc::subscribe \
            -Parent $::sth::GBLHNDMAP(project) \
            -ResultParent $portList \
            -ConfigType AncpAccessNodeConfig \
            -ResultType AncpAccessNodeResults \
            -interval 1]
        
        set ancp_subscribe_state 1
    }
    
    if {$handle == "all"} {
        set accessNodeList [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
        set objhandle [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
    } else {
        foreach rtHandle $handle {
            lappend accessNodeList [::sth::sthCore::invoke stc::get $rtHandle -children-AncpAccessNodeConfig]
        }
        set objhandle $handle
    }
    
   # stc::perform  AncpInitiateAdjacency -BlockList  [lindex [stc::get system1 -children-Project] 0] 
   # stc::perform  AncpInitiateAdjacencyWait -WaitTime 60 -ObjectList [lindex [stc::get system1 -children-Project] 0] 
   # stc::perform  AncpPortUp -BlockList [lindex [stc::get system1 -children-Project] 0] 
   # stc::perform  AncpPortUpWait -WaitTime 60 -ObjectList [lindex [stc::get system1 -children-Project] 0] 
   # stc::perform  PppoxConnect -BlockList [lindex [stc::get system1 -children-Project] 0] 
   #stc::perform  PppoxConnectWait -WaitTime 60 -ObjectList [lindex [stc::get system1 -children-Project] 0] 


    
    switch -- $::sth::Ancp::userArgsArray(action_control) {
	start {
            if {$::sth::Ancp::userArgsArray(action) == "initiate"} {
                puts "Initiate Ancp Adjacency..."
                if {[catch {::sth::sthCore::invoke stc::perform AncpInitiateAdjacency -BlockList $accessNodeList} eMsg]} {
        	    puts "Fail to Initiate Adjacency for Ancp router"
                }
                if {[catch {::sth::sthCore::invoke stc::perform AncpInitiateAdjacencyWait -ObjectList $objhandle -AdjacencyBlockState ESTABLISHED -WaitTime 50} eMsg]} {
        	    puts "Fail to bring up the Adjacency state to ESTABLISHED"
                }
            }
            if {$::sth::Ancp::userArgsArray(action) == "send"} {
                puts "Bring port up..."
                if {[catch {::sth::sthCore::invoke stc::perform AncpPortUp -BlockList $accessNodeList} eMsg]} {
        	    puts "Fail to bring port up"
                }
                if {[catch {::sth::sthCore::invoke stc::perform AncpPortUpWait -ObjectList $objhandle -SubscriberBlockState ESTABLISHED -WaitTime 30} eMsg]} {
        	    puts "Fail to bring up the Ancp Port"
                }
            }
            
            ##do the ARP
            ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $objhandle -WaitForArpToFinish false
            
        }
	stop {
            if {$::sth::Ancp::userArgsArray(action) == "send"} {
                puts "Bring port down..."
                if {[catch {::sth::sthCore::invoke stc::perform AncpPortDown -BlockList $accessNodeList} eMsg]} {
        	    puts "Fail to bring ANCP port down"
                }
                if {[catch {::sth::sthCore::invoke stc::perform AncpPortDownWait -ObjectList $objhandle -AdjacencyBlockState IDLE -WaitTime 30} eMsg]} {
        	    puts "Fail to bring down the Port state to IDLE"
                }
            }
            
            if {$::sth::Ancp::userArgsArray(action) == "initiate"} {
                puts "Terminate Ancp Adjacency..."
                if {[catch {::sth::sthCore::invoke stc::perform AncpTerminateAdjacency -BlockList $accessNodeList} eMsg]} {
        	    puts "Error Terminate Adjacency for Ancp router"
                }
                if {[catch {::sth::sthCore::invoke stc::perform AncpTerminateAdjacencyWait -ObjectList $objhandle -AdjacencyBlockState IDLE -WaitTime 30} eMsg]} {
        	     puts "Fail to terminate Adjacency for Ancp router"
                }
            }
        }
    }

    # prepare the keyed list to be returned to HLTAPI layer
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

proc ::sth::Ancp::emulation_ancp_subscriber_control {handle rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_control $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    set dhcpBlockList ""
    set pppBlockList ""
    set protocol ""
    if {$handle == "all"} {
	if {$::sth::Ancp::subscriber_type == ""} {
	    ##project is loaded from the config file
	    set hosts [::sth::sthCore::invoke stc::get project1 -children-host]
	    foreach host $hosts {
	        if {[::sth::sthCore::invoke stc::get $host -children-PppoeClientBlockConfig] != ""} {
		    set ::sth::Ancp::subscriber_type ppp
		    break
		}
		if {[::sth::sthCore::invoke stc::get $host -children-dhcpv4blockconfig] != ""} {
		    set ::sth::Ancp::subscriber_type dhcp
		    break
		}
		
	    }
	  
	}
        if {$::sth::Ancp::subscriber_type == "ppp"} {
            set pppBlockList [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
	    set objhandle [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
	    set protocol "ppp"
	}
	if {$::sth::Ancp::subscriber_type == "dhcp"} {
	    set dhcpBlockList [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
	    set objhandle [lindex [::sth::sthCore::invoke stc::get system1 -children-Project] 0]
	    set protocol "dhcp"
	}
	
    } else {
        foreach hostHandle $handle {
	    set dhcpblock [::sth::sthCore::invoke stc::get $hostHandle -children-dhcpv4blockconfig]
	    if {$dhcpblock != ""} {
	        set protocol "dhcp"
	        lappend dhcpBlockList $dhcpblock
	    } else {
	       set pppblock [::sth::sthCore::invoke stc::get $hostHandle -children-PppoeClientBlockConfig]
	       if {$pppblock != ""} {
	            set protocol "ppp"
	            lappend pppBlockList $pppblock
	       }
	   }
        }
        set objhandle $handle
    }
    
    switch -- $::sth::Ancp::userArgsArray(action_control) {
	start {
            if {$::sth::Ancp::userArgsArray(action) == "connect"} {
                if {[llength $dhcpBlockList] != 0} {
                    puts "Bind the subscribers..."
                    if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4Bind -BlockList $dhcpBlockList} eMsg]} {
        	         puts "unable to bind the dhcp host"
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4BindWait -ObjectList $objhandle} eMsg]} {
        	        puts "unable to bind the dhcp host"
                    }
                }
            
                if {[llength $pppBlockList] != 0} {
                    puts "connect the subscribers..."
                    if {[catch {::sth::sthCore::invoke stc::perform PppoxConnect -BlockList $pppBlockList} eMsg]} {
        	        puts "unable to connect the ppp client"
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform PppoxConnectWait -ObjectList $objhandle} eMsg]} {
        	        puts "unable to connect the ppp client"
                    }
                }
            
                ##do the ARP
                ::sth::sthCore::invoke stc::perform ArpNdStart -HandleList $objhandle -WaitForArpToFinish false
            }
            if {$::sth::Ancp::userArgsArray(action) == "flap"} {
               
                set mode "iteration"
                
                if {$protocol == "dhcp"} {       
                    createDhcpSequencerLoop $objhandle $mode $dhcpBlockList
                }
                if {$protocol == "ppp"} {
                    createPppSequencerLoop $objhandle $mode $pppBlockList
                }
           
                ::sth::sthCore::invoke stc::perform SequencerStart
            
                ::sth::sthCore::invoke ::stc::waituntilcomplete
            }
            if {$::sth::Ancp::userArgsArray(action) == "flap_start"} {
                if {$protocol == "dhcp"} {       
                    createDhcpSequencerLoop $objhandle "continue" $dhcpBlockList
                }
                if {$protocol == "ppp"} { 
                    createPppSequencerLoop $objhandle "continue" $pppBlockList
                }
                ::sth::sthCore::invoke stc::perform SequencerStart
            }
            if {$::sth::Ancp::userArgsArray(action) == "flap_stop"} {
                ::sth::sthCore::invoke stc::perform SequencerStop
                ::sth::sthCore::invoke stc::sleep 10
            }
        
        }
	stop {
            if {$::sth::Ancp::userArgsArray(action) == "connect"} {
                if {[llength $dhcpBlockList] != 0} {
                    puts "Release the subscribers..."
                    if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4Release -BlockList $dhcpBlockList} eMsg]} {
        	        puts "unable to release the dhcp host"
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4ReleaseWait -ObjectList $dhcpBlockList} eMsg]} {
        	        puts "unable to release the dhcp host"
                    }
                }
            
                if {[llength $pppBlockList] != 0} {
                    puts "Disconnect the subscribers..."
                    if {[catch {::sth::sthCore::invoke stc::perform PppoxDisConnect -BlockList $pppBlockList} eMsg]} {
        	        puts "unable to disconnect the ppp client"
                    }
                    if {[catch {::sth::sthCore::invoke stc::perform PppoxDisConnectWait -ObjectList $pppBlockList} eMsg]} {
        	        puts "unable to disconnect the ppp client"
                    }
                }
            }
            if {[regexp "flap" $::sth::Ancp::userArgsArray(action)]} {
                ::sth::sthCore::invoke stc::perform SequencerStop
                ::sth::sthCore::invoke stc::sleep 10
            }
        }
    }

    # prepare the keyed list to be returned to HLTAPI layer
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}


proc ::sth::Ancp::emulation_ancp_stats { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_info $rklName"
	
    upvar 1 $rklName returnKeyedList
    set rtHandle $::sth::Ancp::userArgsArray(handle)
    
    set ana [::sth::sthCore::invoke stc::get $rtHandle -children-Analyzer]
    if {$ana != ""} {
       #it's a port handle
       set ancpCfg [::sth::sthCore::invoke stc::get $rtHandle -children-AncpPortConfig]
       set results [::sth::sthCore::invoke stc::get $ancpCfg -children-AncpPortResults]
        set ret [::sth::sthCore::invoke stc::get $results]
        
    } else {
        set accessNode [::sth::sthCore::invoke stc::get $rtHandle -children-AncpAccessNodeConfig]
        if {$accessNode == ""} {
            return -code error "Invalid input handle"
        }
        set results [::sth::sthCore::invoke stc::get $accessNode -children-AncpAccessNodeResults]
    
       if {[info exists ::sth::Ancp::userArgsArray(reset)] && $::sth::Ancp::userArgsArray(reset) == 1} {
            ::sth::sthCore::invoke stc::perform ResultsClearAllProtocol
        }
        
        set accessNode [::sth::sthCore::invoke stc::get $rtHandle -children-AncpAccessNodeConfig]
        set results [::sth::sthCore::invoke stc::get $accessNode -children-AncpAccessNodeResults]
    
         set ret [::sth::sthCore::invoke stc::get $results]
    }
    
    #-parent ancpaccessnodeconfig1 -resultchild-Sources {ancpaccessnodeconfig1 ancpaccessnodeconfig1 resultdataset2} -Name {} -TxPortUpCount 0 -TxPortDownCount 0 -RxManagementCount 0 -TxSynCount 0 -RxSynCount 0 -TxSynackCount 0 -RxSynackCount 0 -TxAckCount 0 -RxAckCount 0 -TxRstackCount 0 -RxRstackCount 0 -KeepAliveEnabled true -TxKeepAliveCount 0 -RxKeepAliveCount 0 -KeepAliveTimeoutCount 0 -RxTcpResetCount 1 -SubscribersUp 0 -SubscribersDown 100 -DynamicTopologyDiscoverySupported UNSUPPORTED -LineConfigSupported UNSUPPORTED -TransactionalMulticastSupported UNSUPPORTED -OamSupported UNSUPPORTED -BulkTransactionSupported UNSUPPORTED -Active true
   
    set retVal {}
    foreach key [array names ::sth::Ancp::emulation_ancp_stats_mode] {
	if {$::sth::Ancp::emulation_ancp_stats_mode($key) == "stats \"\""} {   
	    set stcObj [::sth::sthCore::getswitchprop ::sth::Ancp:: emulation_ancp_stats $key stcobj]
	    set stcAttr [::sth::sthCore::getswitchprop ::sth::Ancp:: emulation_ancp_stats $key stcattr]
	    set val [::sth::sthCore::invoke stc::get $results -$stcAttr]
            lappend retVal $key $val
        }
    }
	       

    # prepare the keyed list to be returned to HLTAPI layer
    if {[catch { eval keylset returnKeyedList $retVal }]} {
	return -code error "Cannot update the returnKeyedList"
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    return $returnKeyedList
}


proc ::sth::Ancp::emulation_ancp_subscriber_lines_config_create { rklName } {
    
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_subscriber_lines_config $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    set routerHandle $::sth::Ancp::userArgsArray(ancp_client_handle)
    set portHandle [::sth::sthCore::invoke stc::get $routerHandle -affiliationport-Targets]
    set accessNodeHandle [::sth::sthCore::invoke stc::get $routerHandle -children-ancpaccessnodeconfig]
    
    set accessLoopHanlde [::sth::Ancp::createAccessLoop $accessNodeHandle create]
   
    set ancpVersion [::sth::sthCore::invoke stc::get $accessNodeHandle -AncpVersion]
    
    set hostHandle [::sth::Ancp::createHost $accessLoopHanlde $portHandle $routerHandle create]
    
    set dslProfileHanldeList [::sth::Ancp::createDslProfiles $ancpVersion $accessLoopHanlde create]
    
    ::sth::sthCore::invoke stc::config $accessLoopHanlde "-AffiliatedAncpDslLineProfile-targets {$dslProfileHanldeList}"
    
     # prepare the keyed list to be returned to HLTAPI layer
    if {[catch { keylset returnKeyedList handle $hostHandle } err]} {
	::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. $err"
    }	

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    return $returnKeyedList
}

proc ::sth::Ancp::emulation_ancp_subscriber_lines_config_modify { rklName } {
    
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_subscriber_lines_config $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    if {![info exists ::sth::Ancp::userArgsArray(handle)] || ![info exists ::sth::Ancp::userArgsArray(ancp_client_handle)]} {
        return -code error "the switch \"-handle\" and \"-ancp_client_handle\" are mandatory in modify mode"
    }

    set routerHandle $::sth::Ancp::userArgsArray(ancp_client_handle)
    set accessNodeHandle [::sth::sthCore::invoke stc::get $routerHandle -children-AncpAccessNodeConfig]
    set portHandle [::sth::sthCore::invoke stc::get $routerHandle -affiliationport-Targets]
    
    set accessLoopHanlde [::sth::Ancp::createAccessLoop $accessNodeHandle modify]
   
    set ancpVersion [::sth::sthCore::invoke stc::get $accessNodeHandle -AncpVersion]
    
    set hostHandle [::sth::Ancp::createHost $accessLoopHanlde $portHandle $routerHandle modify]
    
    set dslProfileHanldeList [::sth::Ancp::createDslProfiles $ancpVersion $accessLoopHanlde modify]
    
    ::sth::sthCore::invoke stc::config $accessLoopHanlde "-AffiliatedAncpDslLineProfile-targets {$dslProfileHanldeList}"
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    
    return $returnKeyedList
}

proc ::sth::Ancp::emulation_ancp_subscriber_lines_config_delete { rklName } {
    
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Ancp::emulation_ancp_subscriber_lines_config $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    checkDependency "emulation_ancp_subscriber_lines_config" "handle" "delete"
    
    set ancpHosts $::sth::Ancp::userArgsArray(handle)
    
    foreach ancpHost $ancpHosts {
		::sth::sthCore::invoke stc::delete $ancpHost
	}
        
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Ancp::configAtmSettings {rtrId} {
    variable userArgsArray
    
    set atmConfig ""
    
    if {![info exists userArgsArray(pvc_incr_mode)]} { set userArgsArray(pvc_incr_mode) "vci" }
    if {![info exists userArgsArray(vci)]} { set userArgsArray(vci) 100 }
    if {![info exists userArgsArray(vpi)]} { set userArgsArray(vpi) 100 }
    if {![info exist userArgsArray(vci_step)]} { set userArgsArray(vci_step) 1 }
    if {![info exists userArgsArray(vci_count)]} { set userArgsArray(vci_count) 1 }   
    if {![info exist userArgsArray(vpi_step)]} { set userArgsArray(vpi_step) 1 }
    if {![info exists userArgsArray(vpi_count)]} { set userArgsArray(vpi_count) 1 }
    
    switch -- $userArgsArray(pvc_incr_mode) {
        "vci" {
            while {$rtrId >= $userArgsArray(vci_count)*$userArgsArray(vpi_count)} {
                set rtrId [expr $rtrId - $userArgsArray(vci_count)*$userArgsArray(vpi_count)]
            }
            
            set multi  [expr $rtrId/$userArgsArray(vci_count)]
            set remain [expr $rtrId%$userArgsArray(vci_count)]
            
            set vci [expr {$userArgsArray(vci) + $userArgsArray(vci_step)*$remain}]
            set vpi [expr {$userArgsArray(vpi) + $userArgsArray(vpi_step)*$multi}]
            
            set atmConfig "-Vci $vci -Vpi $vpi"
        }
        "vpi" {
            while {$rtrId >= $userArgsArray(vci_count)*$userArgsArray(vpi_count)} {
                set rtrId [expr $rtrId - $userArgsArray(vci_count)*$userArgsArray(vpi_count)]
            }
            
            set multi  [expr $rtrId/$userArgsArray(vpi_count)]
            set remain [expr $rtrId%$userArgsArray(vpi_count)]
            
            set vpi [expr {$userArgsArray(vpi) + $userArgsArray(vpi_step)*$remain}]
            set vci [expr {$userArgsArray(vci) + $userArgsArray(vci_step)*$multi}]
            
            set atmConfig "-Vci $vci -Vpi $vpi"
        }
        "both" {
            set vciRemain [expr $rtrId%$userArgsArray(vci_count)]
            set vpiRemain [expr $rtrId%$userArgsArray(vpi_count)]
            
            set vpi [expr {$userArgsArray(vpi) + $userArgsArray(vpi_step)*$vpiRemain}]
            set vci [expr {$userArgsArray(vci) + $userArgsArray(vci_step)*$vciRemain}]
            
            set atmConfig "-Vci $vci -Vpi $vpi"
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Error: Unknown pvc_incr_mode $userArgsArray(pvc_incr_mode)." {}
            return $returnKeyedList
        }
    }
    
    return $atmConfig
}

proc ::sth::Ancp::createAccessLoop {accessNodeHandle mode} {
    
    set ancpVersion [::sth::sthCore::invoke stc::get $accessNodeHandle -AncpVersion]
    if {$ancpVersion == "ANCP_DRAFT_02"} {
        set versionTag "ancp_draft2"
    } elseif {$ancpVersion == "L2CP_DRAFT_00"} {
        set versionTag "ancp_draft0"
    } else {
        set versionTag "ancp_rfc6320"
    }
    
    set accessLoopBlockHandle [::sth::sthCore::invoke stc::get $accessNodeHandle -children-AncpAccessLoopBlockConfig]
    set AncpLoopTlvConfig [::sth::sthCore::invoke stc::get $accessLoopBlockHandle -children-AncpTlvConfig]
    set AncpLoopTlvConfigFrameCfg [::sth::sthCore::invoke stc::get $AncpLoopTlvConfig -FrameConfig]
    set frameConfig "<frame ><config><pdus>"
    if {[info exists ::sth::Ancp::userArgsArray(remote_id)] || [regexp AccessLoopRemoteIdTlv $AncpLoopTlvConfigFrameCfg]} {
        set current_remoteId ""
        regexp {.*:AccessLoopRemoteIdTlv"><Length>.*</Length><ID>(.*)</ID>.*} $AncpLoopTlvConfigFrameCfg mat current_remoteId
        if {[info exists ::sth::Ancp::userArgsArray(remote_id)]} {
            set remoteId $::sth::Ancp::userArgsArray(remote_id)
        } elseif { $current_remoteId != "" } {
            # when "mode" is modify, remain existing remoteId 
            set remoteId $current_remoteId
        }
        append frameConfig "<pdu name=\"AccessLoopRemoteIdTlv_1\" pdu=\"$versionTag:AccessLoopRemoteIdTlv\"><Length>0</Length><ID>$remoteId</ID></pdu>"
    }
    if {[info exists ::sth::Ancp::userArgsArray(tlv_customer_vlan_id)] || [info exists ::sth::Ancp::userArgsArray(tlv_service_vlan_id)]} {
        set current_service_vlan ""
        set current_customer_vlan ""
        regexp {.*<Vlan1>([0-9]+)</Vlan1><Vlan2>([0-9]+)</Vlan2>.*} $AncpLoopTlvConfigFrameCfg mat current_service_vlan current_customer_vlan
        if {[info exists ::sth::Ancp::userArgsArray(tlv_customer_vlan_id)]} {
            set tlvCustomerVlan $::sth::Ancp::userArgsArray(tlv_customer_vlan_id)
        } elseif { $current_customer_vlan != "" } {
            # when "mode" is modify, remain existing customer_vlan 
            set tlvCustomerVlan $current_customer_vlan
        } else {
            set tlvCustomerVlan 0
        }
        if {[info exists ::sth::Ancp::userArgsArray(tlv_service_vlan_id)]} {
            set tlvServiceVlan $::sth::Ancp::userArgsArray(tlv_service_vlan_id)
        } elseif { $current_service_vlan != "" } {
            # when "mode" is modify, remain existing service_vlan 
            set tlvServiceVlan $current_service_vlan
        } else {
            set tlvServiceVlan 0
        }
        append frameConfig "<pdu name=\"AccessAggregationCircuitIdBinaryVlanTlv_1\" pdu=\"$versionTag:AccessAggregationCircuitIdBinaryVlanTlv\"><Length>8</Length><Vlan1>$tlvServiceVlan</Vlan1><Vlan2>$tlvCustomerVlan</Vlan2></pdu>"
    }
    if {[info exists ::sth::Ancp::userArgsArray(circuit_id)] || [regexp AccessLoopCircuitIdTlv $AncpLoopTlvConfigFrameCfg]} {
        set current_circuitId ""
        regexp {.*:AccessLoopCircuitIdTlv"><Length>.*</Length><ID>(.*)</ID>.*} $AncpLoopTlvConfigFrameCfg mat current_circuitId
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id)]} {
            set circuitId $::sth::Ancp::userArgsArray(circuit_id)
        } elseif { $current_circuitId != "" } {
            # when "mode" is modify, remain existing circuitId 
            set circuitId $current_circuitId
        } else {
            set circuitId "Access-Node-Identifier"
        }
    }
    append frameConfig "<pdu name=\"proto1\" pdu=\"$versionTag:AccessLoopCircuitIdTlv\"><Length>0</Length><ID>$circuitId</ID></pdu>";
    append frameConfig "</pdus></config></frame>"
    
    ::sth::sthCore::invoke stc::config $AncpLoopTlvConfig "-FrameConfig {$frameConfig}"

    set tlv_service_vlan_id_errorMsg "Please provide valid -tlv_service_vlan_id start with '@' when you try to enable wildcard."
    set tlv_customer_vlan_id_errorMsg "Please provide valid -tlv_customer_vlan_id start with '@' when you try to enable wildcard."
    
    if {$mode == "create"} {
        # create AncpWildcardModifier under ancptlvconfig
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix)] || [info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_step)] || [info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_repeat)]} {
            if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix)]} {
                set suffix $::sth::Ancp::userArgsArray(circuit_id_suffix)
            } else {
                set suffix 0
            }
            if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_step)]} {
                set suffixStep $::sth::Ancp::userArgsArray(circuit_id_suffix_step)
            } else {
                set suffixStep 1
            }
            if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_repeat)]} {
                set suffixRepeat $::sth::Ancp::userArgsArray(circuit_id_suffix_repeat)
            } else {
                set suffixRepeat 0
            }
            if {$suffixRepeat > 0} {
                set suffixRepeat [expr $suffixRepeat - 1]
            }
            set circuitId "$circuitId@x($suffix,0,$suffixStep,0,$suffixRepeat)"
            set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {proto1.ID} -Data {$circuitId}"]
        }
        if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix)] || [info exists ::sth::Ancp::userArgsArray(remote_id_suffix_step)] || [info exists ::sth::Ancp::userArgsArray(remote_id_suffix_repeat)]} {
            if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix)]} {
                set suffix $::sth::Ancp::userArgsArray(remote_id_suffix)
            } else {
                set suffix 0
            }
            if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix_step)]} {
                set suffixStep $::sth::Ancp::userArgsArray(remote_id_suffix_step)
            } else {
                set suffixStep 1
            }
            if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix_repeat)]} {
                set suffixRepeat $::sth::Ancp::userArgsArray(remote_id_suffix_repeat)
            } else {
                set suffixRepeat 0
            }
            if {$suffixRepeat > 0} {
                set suffixRepeat [expr $suffixRepeat - 1]
            }
            if {[info exists ::sth::Ancp::userArgsArray(remote_id)]} {
                set remoteId "$remoteId@x($suffix,0,$suffixStep,0,$suffixRepeat)"
            } else {
                set errorMsg "please provide remote id when you try to create it."
            }
            set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessLoopRemoteIdTlv_1.ID} -Data {$remoteId}"]
        }
        if { [info exists ::sth::Ancp::userArgsArray(tlv_service_vlan_id_wildcard)] && $::sth::Ancp::userArgsArray(tlv_service_vlan_id_wildcard) == 1 } {
            set dataValue ""
            if [ regexp {^@} $tlvServiceVlan ] {
                set dataValue $tlvServiceVlan
            } else {
                set errorMsg $tlv_service_vlan_id_errorMsg
                ::sth::sthCore::log error $errorMsg
                ::sth::sthCore::processError returnKeyedList $errorMsg
            }
            set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan1} -Data {$dataValue}"]
        }
        if { [info exists ::sth::Ancp::userArgsArray(tlv_customer_vlan_id_wildcard)] && $::sth::Ancp::userArgsArray(tlv_customer_vlan_id_wildcard) == 1 } {
            set dataValue ""
            if [ regexp {^@} $tlvCustomerVlan ] {
                set dataValue $tlvCustomerVlan
            } else {
                set errorMsg $tlv_customer_vlan_id_errorMsg
                ::sth::sthCore::log error $errorMsg
                ::sth::sthCore::processError returnKeyedList $errorMsg
            }
            set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan2} -Data {$dataValue}"]
        }
        if {[info exists ::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)]} {
            set deviceCount $::sth::Ancp::userArgsArray(subscriber_lines_per_access_node) 
        } else {
            set deviceCount 1;
        }
     } else {
        set flag 0
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id)]} {
            set circuitId $::sth::Ancp::userArgsArray(circuit_id) 
            incr flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix)]} {
            set suffix $::sth::Ancp::userArgsArray(circuit_id_suffix) 
            incr flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_step)]} {
            set suffixStep $::sth::Ancp::userArgsArray(circuit_id_suffix_step) 
            incr flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(circuit_id_suffix_repeat)]} {
            set suffixRepeat [expr $::sth::Ancp::userArgsArray(circuit_id_suffix_repeat) - 1]
            incr flag
        }
        if {[info exists circuitId] && [info exists suffix] && [info exists suffixStep] && [info exists suffixRepeat]} {
            set circuitId "$circuitId@\x($suffix,0,$suffixStep,1,$suffixRepeat)"
            set wildcardList [::sth::sthCore::invoke stc::get $AncpLoopTlvConfig -children-AncpWildcardModifier]
            if {$wildcardList == ""} {
                set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {proto1.ID} -Data {$circuitId}"]
            } else {
                # find out which AncpWildcardModifier was setting for circuitId
                set mat ""
                foreach wildcard $wildcardList {
                    set offsetReference [::sth::sthCore::invoke stc::get $wildcard -OffsetReference]
                    if { $offsetReference != ""} {
                        if { [regexp {proto[0-9]+\.ID} $offsetReference mat] } {
                            break
                        }
                    } else {
                        continue
                    }
                }
                if { $mat != "" } {
                    ::sth::sthCore::invoke stc::config $wildcard "-OffsetReference {$mat} -Data {$circuitId}"
                } else {
                    set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {proto1.ID} -Data {$circuitId}"]
                }
            }
        } else {
            if {$flag != 4} {
                set errorMsg "please provide cicuit id, suffix, step and repeat all these four options when you try to modifiy them"
            }
        }
        
        set remote_flag 0
        if {[info exists ::sth::Ancp::userArgsArray(remote_id)]} {
            set remoteId $::sth::Ancp::userArgsArray(remote_id) 
            incr remote_flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix)]} {
            set remote_suffix $::sth::Ancp::userArgsArray(remote_id_suffix) 
            incr remote_flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix_step)]} {
            set remote_suffixStep $::sth::Ancp::userArgsArray(remote_id_suffix_step) 
            incr remote_flag
        }
        if {[info exists ::sth::Ancp::userArgsArray(remote_id_suffix_repeat)]} {
            set remote_suffixRepeat [expr $::sth::Ancp::userArgsArray(remote_id_suffix_repeat) - 1]
            incr remote_flag
        }
        if {[info exists remoteId] && [info exists remote_suffix] && [info exists remote_suffixStep] && [info exists remote_suffixRepeat]} {
            set remoteId "$remoteId@\x($remote_suffix,0,$remote_suffixStep,1,$remote_suffixRepeat)"
            set wildcardList [::sth::sthCore::invoke stc::get $AncpLoopTlvConfig -children-AncpWildcardModifier]
            if {$wildcardList == ""} {
                set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessLoopRemoteIdTlv_1.ID} -Data {$remoteId}"]
            } else {
                # find out which AncpWildcardModifier was setting for remoteId
                set mat ""
                foreach wildcard $wildcardList {
                    set offsetReference [::sth::sthCore::invoke stc::get $wildcard -OffsetReference]
                    if { $offsetReference != ""} {
                        if { [regexp {AccessLoopRemoteIdTlv_[0-9]+\.ID} $offsetReference mat] } {
                            break
                        }
                    } else {
                        continue
                    }
                }
                if { $mat != "" } {
                    ::sth::sthCore::invoke stc::config $wildcard "-OffsetReference {$mat} -Data {$remoteId}"
                } else {
                    set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessLoopRemoteIdTlv_1.ID} -Data {$remoteId}"]
                }
            }
        } else {
            if {$remote_flag != 4} {
                set errorMsg "please provide remote id, suffix, step and repeat all these four options when you try to modifiy them"
            }
        }

        if {[info exists ::sth::Ancp::userArgsArray(tlv_service_vlan_id_wildcard)]} {
            set tlvServiceVlanWildcard $::sth::Ancp::userArgsArray(tlv_service_vlan_id_wildcard)
            set wildcardList [::sth::sthCore::invoke stc::get $AncpLoopTlvConfig -children-AncpWildcardModifier]
            set dataValue ""
            if [ regexp {^@} $tlvServiceVlan ] {
                set dataValue $tlvServiceVlan
            } elseif { $::sth::Ancp::userArgsArray(tlv_service_vlan_id_wildcard) == 1 } {
                set errorMsg $tlv_service_vlan_id_errorMsg
                ::sth::sthCore::log error $errorMsg
                ::sth::sthCore::processError returnKeyedList $errorMsg
            }
            if {$wildcardList == ""} {
                set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan1} -Data {$dataValue}"]
            } else {
                # find out which AncpWildcardModifier was setting for tlv_service_vlan_id
                set mat ""
                foreach wildcard $wildcardList {
                    set offsetReference [::sth::sthCore::invoke stc::get $wildcard -OffsetReference]
                    if { $offsetReference != ""} {
                        if { [regexp {AccessAggregationCircuitIdBinaryVlanTlv_[0-9]+.Vlan1} $offsetReference mat] } {
                            break
                        }
                    } else {
                        continue
                    }
                }
                if { $mat != "" } {
                    if { $tlvServiceVlanWildcard == 1 } {
                        ::sth::sthCore::invoke stc::config $wildcard "-OffsetReference {$mat} -Data {$dataValue}"
                    } elseif { $tlvServiceVlanWildcard == 0 } {
                        ::sth::sthCore::invoke stc::delete $wildcard
                    }
                } else {
                    if { $tlvServiceVlanWildcard == 1 } {
                        set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan1} -Data {$dataValue}"]
                    }
                }
            }
        }
        if {[info exists ::sth::Ancp::userArgsArray(tlv_customer_vlan_id_wildcard)]} {
            set tlvCustomerVlanWildcard $::sth::Ancp::userArgsArray(tlv_customer_vlan_id_wildcard)
            set wildcardList [::sth::sthCore::invoke stc::get $AncpLoopTlvConfig -children-AncpWildcardModifier]
            set dataValue ""
            if [ regexp {^@} $tlvCustomerVlan ] {
                set dataValue $tlvCustomerVlan
            } elseif { $::sth::Ancp::userArgsArray(tlv_customer_vlan_id_wildcard) == 1 } {
                set errorMsg $tlv_customer_vlan_id_errorMsg
                ::sth::sthCore::log error $errorMsg
                ::sth::sthCore::processError returnKeyedList $errorMsg
            }
            if {$wildcardList == ""} {
                set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan2} -Data {$dataValue}"]
            } else {
                # find out which AncpWildcardModifier was setting for tlv_customer_vlan_id
                set mat ""
                foreach wildcard $wildcardList {
                    set offsetReference [::sth::sthCore::invoke stc::get $wildcard -OffsetReference]
                    if { $offsetReference != ""} {
                        if { [regexp {AccessAggregationCircuitIdBinaryVlanTlv_[0-9]+.Vlan2} $offsetReference mat] } {
                            break
                        }
                    } else {
                        continue
                    }
                }
                if { $mat != "" } {
                    if { $tlvCustomerVlanWildcard == 1 } {
                        ::sth::sthCore::invoke stc::config $wildcard "-OffsetReference {$mat} -Data {$dataValue}"
                    } elseif { $tlvCustomerVlanWildcard == 0 } {
                        ::sth::sthCore::invoke stc::delete $wildcard
                    }
                } else {
                    if { $tlvCustomerVlanWildcard == 1 } {
                        set wildcard [::sth::sthCore::invoke stc::create AncpWildcardModifier -under $AncpLoopTlvConfig "-OffsetReference {AccessAggregationCircuitIdBinaryVlanTlv_1.Vlan2} -Data {$dataValue}"]
                    }
                }
            }
        }
    }
    
    return $accessLoopBlockHandle
}

proc ::sth::Ancp::createHost {accessLoopBlockHandle portHandle routerHandle mode} {

    if {$mode == "create"} {
        if {[info exists ::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)]} {
           set deviceCount $::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)
        } else {
           set deviceCount 1
        }
	
        #create host. we just create one hostblock here
        set hostHandle $::sth::Ancp::userArgsArray(handle)
        if {[regexp "dhcp" $hostHandle]} {
            set hostHandle [::sth::sthCore::invoke stc::get $hostHandle -parent]
        }
        
        ::sth::sthCore::invoke stc::config $hostHandle "-DeviceCount $deviceCount"
        
        # in case the l2 is atm
        set ethiiif [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif]
        if {$ethiiif == ""} {
            set atmif [::sth::sthCore::invoke stc::get $hostHandle -children-aal5if]
            set lowerif $atmif
        } else {
           set lowerif $ethiiif
        }
        
        set upifs [::sth::sthCore::invoke stc::get $lowerif -StackedOnEndpoint-sources]
        #if the host has vlan or qinq, we need to delete the vlans
        #if the host has already create vlan, delete it, since in this function will create the new vlan
        if {[regexp "vlan" $upifs]} {
            set upifs1 $upifs
            set upifs2 [::sth::sthCore::invoke stc::get $upifs1 -StackedOnEndpoint-sources]
            if {[regexp "vlan" $upifs2]} {
                set upifs [::sth::sthCore::invoke stc::get $upifs2 -StackedOnEndpoint-sources]
                ::sth::sthCore::invoke stc::delete $upifs2
            } else {
               set upifs $upifs2
            }
            ::sth::sthCore::invoke stc::delete $upifs1
        }

        #now the question is how to handle Vlan options. we don't support create qinq on the host. qinq means use
        #the AN's vlan as the outer vlan. so we don't care the service_vlan_id option here.

        if {[info exists ::sth::Ancp::userArgsArray(vlan_allocation_model)] && $::sth::Ancp::userArgsArray(vlan_allocation_model) == "1_1"} {
            if {[info exists ::sth::Ancp::userArgsArray(enable_c_vlan)] && $::sth::Ancp::userArgsArray(enable_c_vlan) == "1"} {
                set vlanid $::sth::Ancp::userArgsArray(customer_vlan_id)
                if {[llength $vlanid] != 1} {
                    set vlanif [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle "-IsRange FALSE -IdList $vlanid"]
                } else {
                    set options [list -VlanId $vlanid]
                    lappend options "-IdStep" $::sth::Ancp::userArgsArray(customer_vlan_id_step)
                    lappend options "-IdRepeatCount" [expr $::sth::Ancp::userArgsArray(customer_vlan_id_repeat) -1 ]
                    set vlanif [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle $options]
                }
        
                set flag 1
                if {[catch {::sth::sthCore::invoke stc::get $routerHandle -children-vlanif} targetVlanIf]} {
                   set eMsg "ANCP router don't configure Vlan"
                   set flag 0
                }
                if {[regexp "^$" $targetVlanIf]} {
                    set eMsg "ANCP router don't configure Vlan"
                    set flag 0
                }
                if {[llength $targetVlanIf] > 1} {
                   set eMsg "ANCP router has dual vlan stack"
                   set flag 0
                }
                if {$flag} {
                    set vlanLink [::sth::sthCore::invoke stc::create VlanSwitchLink -under $hostHandle "-CreateVlanIfOnDst FALSE -Active TRUE -LocalActive TRUE"]
                    set ancpCpeToDslamLink [::sth::sthCore::invoke stc::create AncpCpeToDslamLink -under $hostHandle "-Active TRUE -LocalActive TRUE"]
            
                    ::sth::sthCore::invoke stc::config $vlanLink "-LinkDstDevice-targets $routerHandle"
                    ::sth::sthCore::invoke stc::config $vlanLink "-LinkSrc-targets $ethiiif"
                    ::sth::sthCore::invoke stc::config $vlanLink "-LinkDst-targets $targetVlanIf"
                    ::sth::sthCore::invoke stc::config $ancpCpeToDslamLink "-LinkDstDevice-targets $routerHandle"
                    ::sth::sthCore::invoke stc::config $ancpCpeToDslamLink "-ContainedLink-targets $vlanLink"
                    ::sth::sthCore::invoke stc::config $hostHandle "-ContainedLink-targets $ancpCpeToDslamLink"
                }
            }
            ::sth::sthCore::invoke stc::config $vlanif "-StackedOnEndpoint-targets $lowerif"
            set lowerif $vlanif
        }
       
        foreach upif $upifs {
            ::sth::sthCore::invoke stc::config $upif "-StackedOnEndpoint-targets $lowerif"
        }

        set sessionBlockHandle [::sth::sthCore::invoke stc::get $hostHandle -children-dhcpv4blockconfig]
        if {$sessionBlockHandle == ""} {
            set sessionBlockHandle [::sth::sthCore::invoke stc::get $hostHandle -children-PppoeClientBlockConfig]
            if {$sessionBlockHandle != ""} {
            set ::sth::Ancp::subscriber_type "ppp"
            }
        } else {
            set ::sth::Ancp::subscriber_type "dhcp"
        }
        ::sth::sthCore::invoke stc::config $accessLoopBlockHandle "-L2NetworkIf $lowerif"
        if {$sessionBlockHandle != ""} {
            ::sth::sthCore::invoke stc::config $accessLoopBlockHandle  "-SessionBlock $sessionBlockHandle"
        }
        ::sth::sthCore::invoke stc::config $hostHandle "-AffiliationPort-targets $portHandle"
    } else {
        set l2If [::sth::sthCore::invoke stc::get $accessLoopBlockHandle -L2NetworkIf]
        
        set sessionBlock [::sth::sthCore::invoke stc::get $accessLoopBlockHandle -SessionBlock]
        
        set hostHandle [::sth::sthCore::invoke stc::get $sessionBlock -parent]
        
        if {[info exists ::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)]} {
           ::sth::sthCore::invoke stc::config $hostHandle "-DeviceCount $::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)"
        }
        
        #in case the L2 is atm
        set ethiiif [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif]
        if {$ethiiif == ""} {
            set atmif [::sth::sthCore::invoke stc::get $hostHandle -children-aal5if]
            set lowerif $atmif
        } else {
           set lowerif $ethiiif
        }
    
        if {[info exists ::sth::Ancp::userArgsArray(vlan_allocation_model)] && $::sth::Ancp::userArgsArray(vlan_allocation_model) == "1_1"} {
            if {[info exists ::sth::Ancp::userArgsArray(enable_c_vlan)] && $::sth::Ancp::userArgsArray(enable_c_vlan) == "1"} {
                if {[regexp "vlan" $l2If]} {
                    set vlanIf $l2If
                    set lowerif $vlanIf
                } else {
                    set vlanIf [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle]
                    ::sth::sthCore::invoke stc::config $vlanIf "-StackedOnEndpoint-targets $lowerif"
                    set lowerif $vlanIf
                    
                    set vlanLink [::sth::sthCore::invoke stc::create VlanSwitchLink -under $hostHandle "-CreateVlanIfOnDst FALSE -Active TRUE -LocalActive TRUE"]
                    set ancpCpeToDslamLink [::sth::sthCore::invoke stc::create AncpCpeToDslamLink -under $hostHandle "-Active TRUE -LocalActive TRUE"]
                    set targetVlanIf [::sth::sthCore::invoke stc::get $routerHandle -children-vlanif]
            
                    ::sth::sthCore::invoke stc::config $vlanLink -LinkDstDevice-targets $routerHandle
                    ::sth::sthCore::invoke stc::config $vlanLink "-LinkSrc-targets $ethiiif"
                    ::sth::sthCore::invoke stc::config $vlanLink "-LinkDst-targets $targetVlanIf"
                    ::sth::sthCore::invoke stc::config $ancpCpeToDslamLink "-LinkDstDevice-targets $routerHandle"
                    ::sth::sthCore::invoke stc::config $ancpCpeToDslamLink "-ContainedLink-targets $vlanLink"
                    ::sth::sthCore::invoke stc::config $hostHandle "-ContainedLink-targets $ancpCpeToDslamLink"
                }
                set vlanid $::sth::Ancp::userArgsArray(customer_vlan_id)
                if {[llength $vlanid] != 1} {
                    ::sth::sthCore::invoke stc::config $vlanIf "-IsRange FALSE -IdList $vlanid"
                } else {
                   set options [list -VlanId $vlanid]
                   lappend options "-IdStep" $::sth::Ancp::userArgsArray(customer_vlan_id_step)
                   lappend options "-IdRepeatCount" [expr $::sth::Ancp::userArgsArray(customer_vlan_id_repeat) -1 ]
                   ::sth::sthCore::invoke stc::config $vlanIf "$options"
                }
            }
        }
        set pppoeif [::sth::sthCore::invoke stc::get $hostHandle -children-pppoeif]
        if {$pppoeif != ""} {
            ::sth::sthCore::invoke stc::config $pppoeif "-StackedOnEndpoint-targets $lowerif"
            set lowerif [::sth::sthCore::invoke stc::get $hostHandle -children-pppif]
        }
        
        set ipv4if [::sth::sthCore::invoke stc::get $hostHandle -children-ipv4if]
        ::sth::sthCore::invoke stc::config $ipv4if "-StackedOnEndpoint-targets $lowerif"
        
        if {[info exists ::sth::Ancp::userArgsArray(subscriber_protocol)]} {
            set protocol $::sth::Ancp::userArgsArray(subscriber_protocol)
            if {![regexp -- $protocol $sessionBlock]} {
                ::sth::sthCore::invoke stc::delete $sessionBlock
                if {$protocol == "dhcp"} {
                    set sessionBlockHandle [::sth::sthCore::invoke stc::create dhcpv4blockconfig -under $hostHandle "-usesif-targets $ipv4if"]
                } elseif {$protocol == "ppp"} {
                    set sessionBlockHandle [::sth::sthCore::invoke stc::create PppoeClientBlockConfig -under $hostHandle "-usesif-targets $ipv4if"]
                }
                ::sth::sthCore::invoke stc::config $accessLoopBlockHandle  "-SessionBlock $sessionBlockHandle"
            }
        }
        ::sth::sthCore::invoke stc::config $accessLoopBlockHandle "-L2NetworkIf $lowerif"
    }
    return $hostHandle
}

proc ::sth::Ancp::createDslProfiles {ancpVersion accessLoopHanlde mode} {
        
        set encapTlv ""
        set dslTypeTlv ""
        set upRateTlv ""
        set downRateTlv ""
        set downMinRateTlv ""
        set downMaxRateTlv ""
        set downAttainRateTlv ""
        set downPowerRateTlv ""
        set downMaxILDelayTlv ""
        set downActILDelayTlv ""
        set upMinRateTlv ""
        set upMaxRateTlv ""
        set upAttainRateTlv ""
        set upPowerRateTlv ""
        set upMaxILDelayTlv ""
        set upActILDelayTlv ""
        
        if {$mode == "modify"} {
            set dslHandles  [::sth::sthCore::invoke stc::get $accessLoopHanlde -affiliatedancpdsllineprofile-Targets]
            set dslHandle1 [lindex $dslHandles 0]
           
            set tlvConfig [::sth::sthCore::invoke stc::get $dslHandle1 -children-AncpTlvConfig]
            set frameConfig [::sth::sthCore::invoke stc::get $tlvConfig -FrameConfig]
            regexp {<pdu name="AccessLoopEncapsulationTlv.*?</pdu>} $frameConfig encapTlv
            regexp {<pdu name="proto1.*?</pdu>} $frameConfig dslTypeTlv
            regexp {<pdu name="proto2.*?</pdu>} $frameConfig upRateTlv
            regexp {<pdu name="proto3.*?</pdu>} $frameConfig downRateTlv
            regexp {<pdu name="MinimumNetDataRateDownstreamTlv.*?</pdu>} $frameConfig downMinRateTlv
            regexp {<pdu name=\"MaximumNetDataRateDownstreamTlv.*?</pdu>} $frameConfig downMaxRateTlv
            regexp {<pdu name=\"AttainableNetDataRateDownstreamTlv.*?</pdu>} $frameConfig downAttainRateTlv
            regexp {<pdu name=\"MinimumNetLowPowerDataRateDownstreamTlv.*?</pdu>} $frameConfig downPowerRateTlv
            regexp {<pdu name=\"MaximumInterleavingDelayDownstreamTlv.*?</pdu>} $frameConfig downMaxILDelayTlv
            regexp {<pdu name=\"ActualInterleavingDelayDownstreamTlv.*?</pdu>} $frameConfig downActILDelayTlv
            regexp {<pdu name=\"MinimumNetDataRateUpstreamTlv.*?</pdu>} $frameConfig upMinRateTlv
            regexp {<pdu name=\"MaximumNetDataRateUpstreamTlv.*?</pdu>} $frameConfig upMaxRateTlv
            regexp {<pdu name=\"AttainableNetDataRateUpstreamTlv.*?</pdu>} $frameConfig upAttainRateTlv
            regexp {<pdu name=\"MinimumNetLowPowerDataRateUpstreamTlv.*?</pdu>} $frameConfig upPowerRateTlv
            regexp {<pdu name=\"MaximumInterleavingDelayUpstreamTlv.*?</pdu>} $frameConfig upMaxILDelayTlv
            regexp {<pdu name=\"ActualInterleavingDelayUpstreamTlv.*?</pdu>} $frameConfig upActILDelayTlv
            
            foreach dslHandle $dslHandles {
                ::sth::sthCore::invoke stc::delete $dslHandle
            }
            
        }
        
        set dslHandle1 [::sth::sthCore::invoke stc::create AncpDslLineProfile -under $::sth::GBLHNDMAP(project) "-AncpVersion $ancpVersion"]
        
        lappend dslHandleList $dslHandle1
        
        if {$ancpVersion == "ANCP_DRAFT_02"} {
            set versionTag "ancp_draft2"
        } elseif {$ancpVersion == "L2CP_DRAFT_00"} {
            set versionTag "ancp_draft0"
        } else {
            set versionTag "ancp_rfc6320"
        }
       
        
        set tlvHeader "<frame ><config><pdus>"
        
         #set tlvConfig "<frame ><config><pdus>"
        
        if {[info exists ::sth::Ancp::userArgsArray(include_encap)]} {
            set datalink "01"
            if {[info exists ::sth::Ancp::userArgsArray(data_link)]} {
                if {$::sth::Ancp::userArgsArray(data_link) == "atm_aal5"} {
                    set datalink "00"
                }
            }
            set encaps1 "00"
            if {[info exists ::sth::Ancp::userArgsArray(encap1)]} {
                switch -- [string tolower $::sth::Ancp::userArgsArray(encap1)] {
                      untagged_ethernet {
                         set encaps1 "01"
                      }
                      single_tagged_ethernet {
                        set encaps1 "02"
                      }
                      default {
                      }
                }
            }
            set encaps2 "00"
             if {[info exists ::sth::Ancp::userArgsArray(encap2)]} {
                switch -- [string tolower $::sth::Ancp::userArgsArray(encap2)] {
                       pppoa_llc {
                         set encaps2 "01"
                      }
                       pppoa_null {
                        set encaps2 "02"
                      }
                       ipoa_llc {
                        set encaps2 "03"
                      }
                        ipoa_null {
                        set encaps2 "04"
                      }
                      aal5_llc_w_fcs {
                        set encaps2 "05"
                      }
                       aal5_llc_wo_fcs {
                        set encaps2 "06"
                      }
                        aal5_null_w_fcs  {
                        set encaps2 "07"
                      }
                        aal5_null_wo_fcs {
                        set encaps2 "08"
                      }
                      default {
                        set encaps2 "00"
                      }
                      
                }
            }
            set encapTlv "<pdu name=\"AccessLoopEncapsulationTlv_1\" pdu=\"ancp_draft2:AccessLoopEncapsulationTlv\"><Length>3</Length><DataLink>$datalink</DataLink><Encaps1>$encaps1</Encaps1><Encaps2>$encaps2</Encaps2></pdu>"
            #append tlvConfig "<pdu name=\"AccessLoopEncapsulationTlv_1\" pdu=\"ancp_draft2:AccessLoopEncapsulationTlv\"><Length>3</Length><DataLink>$datalink</DataLink><Encaps1>$encaps1</Encaps1><Encaps2>$encaps2</Encaps2></pdu>"
        }
        
        set dsltype "01"
        if {[info exists ::sth::Ancp::userArgsArray(dsl_type)]} {
            switch -- [string tolower $::sth::Ancp::userArgsArray(dsl_type)] {
                adsl1 {
                    set dsltype "01"    
                }
                adsl2 {
                    set dsltype "02"    
                }
                adsl2_plus {
                    set dsltype "03"    
                }
                vdsl1 {
                    set dsltype "04"    
                }
                vdsl2 {
                    set dsltype "05"    
                }
                 sdsl {
                    set dsltype "06"    
                }
                "unknown" {
                   set dsltype "07"    
                }
                default {
                  set dsltype "01"   
                }
            }
        }
        set dslTypeTlv "<pdu name=\"proto1\" pdu=\"$versionTag:DslTypeTlv\"><Length>4</Length><DslType>$dsltype</DslType></pdu>"
        
        if {[info exists ::sth::Ancp::userArgsArray(actual_rate_upstream)]} {
            set rateUpstream $::sth::Ancp::userArgsArray(actual_rate_upstream)
            set upRateTlv "<pdu name=\"proto2\" pdu=\"$versionTag:ActualNetDataRateUpstreamTlv\"><Length>4</Length><Rate>$rateUpstream</Rate></pdu>"
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(actual_rate_downstream)]} {
            set rateDownstream $::sth::Ancp::userArgsArray(actual_rate_downstream)
            set downRateTlv "<pdu name=\"proto3\" pdu=\"$versionTag:ActualNetDataRateDownstreamTlv\"><Length>4</Length><Rate>$rateDownstream</Rate></pdu>"
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(downstream_min_rate)]} {
            set downMinRateTlv "<pdu name=\"MinimumNetDataRateDownstreamTlv_1\" pdu=\"$versionTag:MinimumNetDataRateDownstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(downstream_min_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(downstream_max_rate)]} {
            set downMaxRateTlv "<pdu name=\"MaximumNetDataRateDownstreamTlv_1\" pdu=\"$versionTag:MaximumNetDataRateDownstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(downstream_max_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(downstream_attainable_rate)]} {
            set downAttainRateTlv "<pdu name=\"AttainableNetDataRateDownstreamTlv_1\" pdu=\"$versionTag:AttainableNetDataRateDownstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(downstream_attainable_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(downstream_min_low_power_rate)]} {
            set downPowerRateTlv "<pdu name=\"MinimumNetLowPowerDataRateDownstreamTlv_1\" pdu=\"$versionTag:MinimumNetLowPowerDataRateDownstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(downstream_min_low_power_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(downstream_max_interleaving_delay)]} {
            set downMaxILDelayTlv "<pdu name=\"MaximumInterleavingDelayDownstreamTlv_1\" pdu=\"$versionTag:MaximumInterleavingDelayDownstreamTlv\"><Length>4</Length><Time>$::sth::Ancp::userArgsArray(downstream_max_interleaving_delay)</Time></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(downstream_act_interleaving_delay)]} {
            set downActILDelayTlv "<pdu name=\"ActualInterleavingDelayDownstreamTlv_1\" pdu=\"$versionTag:ActualInterleavingDelayDownstreamTlv\"><Length>4</Length><Time>$::sth::Ancp::userArgsArray(downstream_act_interleaving_delay)</Time></pdu>"
        }
        
        if {[info exists ::sth::Ancp::userArgsArray(upstream_min_rate)]} {
            set upMinRateTlv "<pdu name=\"MinimumNetDataRateUpstreamTlv_1\" pdu=\"$versionTag:MinimumNetDataRateUpstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(upstream_min_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(upstream_max_rate)]} {
            set upMaxRateTlv "<pdu name=\"MaximumNetDataRateUpstreamTlv_1\" pdu=\"$versionTag:MaximumNetDataRateUpstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(upstream_max_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(upstream_attainable_rate)]} {
            set upAttainRateTlv "<pdu name=\"AttainableNetDataRateUpstreamTlv_1\" pdu=\"$versionTag:AttainableNetDataRateUpstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(upstream_attainable_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(upstream_min_low_power_rate)]} {
            set upPowerRateTlv "<pdu name=\"MinimumNetLowPowerDataRateUpstreamTlv_1\" pdu=\"$versionTag:MinimumNetLowPowerDataRateUpstreamTlv\"><Length>4</Length><Rate>$::sth::Ancp::userArgsArray(upstream_min_low_power_rate)</Rate></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(upstream_max_interleaving_delay)]} {
            set upMaxILDelayTlv "<pdu name=\"MaximumInterleavingDelayUpstreamTlv_1\" pdu=\"$versionTag:MaximumInterleavingDelayUpstreamTlv\"><Length>4</Length><Time>$::sth::Ancp::userArgsArray(upstream_max_interleaving_delay)</Time></pdu>"
        }
        if {[info exists ::sth::Ancp::userArgsArray(upstream_act_interleaving_delay)]} {
            set upActILDelayTlv "<pdu name=\"ActualInterleavingDelayUpstreamTlv_1\" pdu=\"$versionTag:ActualInterleavingDelayUpstreamTlv\"><Length>4</Length><Time>$::sth::Ancp::userArgsArray(upstream_act_interleaving_delay)</Time></pdu>"
        }
        
        set tlvTail "</pdus></config></frame>"
        
        #set tlvConfig $tlvHeader$encapTlv$dslTypeTlv$upRateTlv$downRateTlv$downMinRateTlv$downMaxRateTlv$downAttainRateTlv$downPowerRateTlv$downMaxILDelayTlv$downActILDelayTlv$upMinRateTlv$upMaxRateTlv$upAttainRateTlv$upPowerRateTlv$upMaxILDelayTlv$upActILDelayTlv$tlvTail
        set cmdName {set tlvConfig $tlvHeader$encapTlv$dslTypeTlv$upRateTlv$downRateTlv$downMinRateTlv$downMaxRateTlv$downAttainRateTlv$downPowerRateTlv$downMaxILDelayTlv$downActILDelayTlv$upMinRateTlv$upMaxRateTlv$upAttainRateTlv$upPowerRateTlv$upMaxILDelayTlv$upActILDelayTlv$tlvTail}
        eval $cmdName
        
        set dslTlvHandle1 [::sth::sthCore::invoke stc::create AncpTlvConfig -under $dslHandle1 "-FrameConfig {$tlvConfig}"]
        
        set subscount $::sth::Ancp::userArgsArray(subscriber_lines_per_access_node)
        
        set repeatcount $subscount
        
        if {[info exists ::sth::Ancp::userArgsArray(actual_rate_upstream_repeat)]} {
            set repeatcount $::sth::Ancp::userArgsArray(actual_rate_upstream_repeat)
        } elseif {[info exists ::sth::Ancp::userArgsArray(actual_rate_upstream_repeat)]} {
            set repeatcount $::sth::Ancp::userArgsArray(actual_rate_downstream_repeat)
        }
            
        
        set count [expr $subscount/$repeatcount]
            
        if {[expr $subscount%$repeatcount] != 0} {
            incr count
        }
            
        set hostRangeStep [expr $subscount/$count]
            
        set AncpSubscriberMap1 [::sth::sthCore::invoke stc::create "AncpSubscriberMap" \
              -under $accessLoopHanlde \
             -SubscriberStartEndList "1 $hostRangeStep" \
              -Active "TRUE" \
              -LocalActive "TRUE"  ]
        ::sth::sthCore::invoke stc::config $AncpSubscriberMap1 -AffiliatedSubscriberDslLineProfile-targets $dslHandle1
            
        set upstep $::sth::Ancp::userArgsArray(actual_rate_upstream_step)
        set downstep $::sth::Ancp::userArgsArray(actual_rate_downstream_step)
            
        for {set i 2} {$i <=$count } {incr i} {
            set rateUpstream [expr $rateUpstream + $upstep]
            set rateDownstream [expr $rateDownstream + $upstep]
                
            set upRateTlv "<pdu name=\"proto2\" pdu=\"$versionTag:ActualNetDataRateUpstreamTlv\"><Length>4</Length><Rate>$rateUpstream</Rate></pdu>"
            set downRateTlv "<pdu name=\"proto3\" pdu=\"$versionTag:ActualNetDataRateDownstreamTlv\"><Length>4</Length><Rate>$rateDownstream</Rate></pdu>"
                
            eval $cmdName
                
            set dslHandle$i [::sth::sthCore::invoke stc::create AncpDslLineProfile -under $::sth::GBLHNDMAP(project) "-AncpVersion $ancpVersion"]
            set dslHandle [set dslHandle$i]
            #set dslhandle $dslhanlde
            set dslTlvHandle$i [::sth::sthCore::invoke stc::create AncpTlvConfig -under $dslHandle "-FrameConfig {$tlvConfig}"]
                
            set startHost [expr $hostRangeStep*($i-1) + 1]
            if {$i < $count} {
                set endHost [expr $startHost + $hostRangeStep -1]
            } else {
                set endHost $subscount
            }
                
            set AncpSubscriberMap$i [::sth::sthCore::invoke stc::create "AncpSubscriberMap" \
                    -under $accessLoopHanlde \
                    -SubscriberStartEndList "$startHost $endHost" \
                    -Active "TRUE" \
                    -LocalActive "TRUE"  ]
        set AncpSubscriberMap [set AncpSubscriberMap$i]
        ::sth::sthCore::invoke stc::config $AncpSubscriberMap -AffiliatedSubscriberDslLineProfile-targets $dslHandle
        
        lappend dslHandleList $dslHandle
        }
            
        return $dslHandleList
}


proc ::sth::Ancp::isAncpRouterHandleValid { handle } {
   # do preliminary search on the router handle since it must exist under the project
    if {[catch {::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router} allRouters]} {
		return 0
	}
        #the code is wrong here, $handle may be a list. Modify by cf
	#if {[lsearch $allRouters $handle] < 0} {
	#    return 0
	#}
        foreach router $handle {
           if {[lsearch $allRouters $router] < 0} {
	          return 0
	   }
           # verify that ancp exists on the router
           if {[catch {::sth::sthCore::invoke stc::get $router -children-ancpaccessnodeconfig} ancpConfigHandle]} {
	  			return 0
	       }
        }
    
	return 1
}

proc ::sth::Ancp::createDhcpSequencerLoop {hostHandle mode blockList} {

    set sequencer $::sth::sthCore::GBLHNDMAP(sequencer)
    
    set oldLoopCmd [::sth::sthCore::invoke stc::get $sequencer -children-SequencerLoopCommand]

    foreach cmd $oldLoopCmd {
           ::sth::sthCore::invoke stc::delete $cmd
    }

set sequencerLoopCommand [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $sequencer "-ContinuousMode TRUE"]

    if {$mode == "iteration"} {
        if {[info exists ::sth::Ancp::userArgsArray(flap_count)]} {
            set count $::sth::Ancp::userArgsArray(flap_count)
        } else {
            set count 1
    }
        ::sth::sthCore::invoke stc::config $sequencerLoopCommand "-ContinuousMode false -IterationCount $count"
    }
set dhcpv4ReleaseCommand [::sth::sthCore::invoke stc::create "Dhcpv4ReleaseCommand" -under $sequencerLoopCommand]

set dhcpv4ReleaseWaitCommand [::sth::sthCore::invoke stc::create "Dhcpv4ReleaseWaitCommand" -under $sequencerLoopCommand]

    if {[info exists ::sth::Ancp::userArgsArray(subscriber_line_down_time)]} {
        set waitTime $::sth::Ancp::userArgsArray(subscriber_line_down_time)
    } else {
        set waitTime 10
    }

set waitCommand1 [::sth::sthCore::invoke stc::create "WaitCommand" -under $sequencerLoopCommand "-waitTime $waitTime"]
      
set dhcpv4BindCommand [::sth::sthCore::invoke stc::create "Dhcpv4BindCommand" -under $sequencerLoopCommand]
        
set dhcpv4BindWaitCommand [::sth::sthCore::invoke stc::create "Dhcpv4BindWaitCommand" -under $sequencerLoopCommand]
    
    if {[info exists ::sth::Ancp::userArgsArray(subscriber_line_up_time)]} {
        set waitTime $::sth::Ancp::userArgsArray(subscriber_line_up_time)
    } else {
        set waitTime 10
    }
    
set waitCommand2 [::sth::sthCore::invoke stc::create "WaitCommand" -under $sequencerLoopCommand "-waitTime $waitTime"]
    
    ::sth::sthCore::invoke stc::config $dhcpv4BindWaitCommand "-ObjectList {$hostHandle}"
    ::sth::sthCore::invoke stc::config $dhcpv4BindCommand "-BlockList {$blockList}"
    ::sth::sthCore::invoke stc::config $dhcpv4ReleaseWaitCommand "-ObjectList {$hostHandle}"
    ::sth::sthCore::invoke stc::config $dhcpv4ReleaseCommand "-BlockList {$blockList}"
    ::sth::sthCore::invoke stc::config  $sequencerLoopCommand "-CommandList \"$dhcpv4ReleaseCommand $dhcpv4ReleaseWaitCommand $waitCommand1 $dhcpv4BindCommand $dhcpv4BindWaitCommand $waitCommand2\""
    ::sth::sthCore::invoke stc::config  $sequencer "-CommandList $sequencerLoopCommand"
}

proc ::sth::Ancp::createPppSequencerLoop {hostHandle mode blockList} {

    set sequencer $::sth::sthCore::GBLHNDMAP(sequencer)
    
    set oldLoopCmd [::sth::sthCore::invoke stc::get $sequencer -children-SequencerLoopCommand]

    foreach cmd $oldLoopCmd {
           ::sth::sthCore::invoke stc::delete $cmd
    }

set sequencerLoopCommand [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $sequencer "-ContinuousMode TRUE"]

    if {$mode == "iteration"} {
        if {[info exists ::sth::Ancp::userArgsArray(flap_count)]} {
            set count $::sth::Ancp::userArgsArray(flap_count)
        } else {
            set count 1
    }
        ::sth::sthCore::invoke stc::config $sequencerLoopCommand "-ContinuousMode false -IterationCount $count"
    }
    
set pppReleaseCommand [::sth::sthCore::invoke stc::create "PppoxDisconnectCommand" -under $sequencerLoopCommand]

set pppReleaseWaitCommand [::sth::sthCore::invoke stc::create "PppoxDisconnectWaitCommand" -under $sequencerLoopCommand]

    if {[info exists ::sth::Ancp::userArgsArray(flap_interval)]} {
        set waitTime $::sth::Ancp::userArgsArray(flap_interval)
    } else {
        set waitTime 10
    }

set waitCommand1 [::sth::sthCore::invoke stc::create "WaitCommand" -under $sequencerLoopCommand "-waitTime $waitTime"]
      
set pppBindCommand [::sth::sthCore::invoke stc::create "PppoxConnectCommand" -under $sequencerLoopCommand]
        
set pppBindWaitCommand [::sth::sthCore::invoke stc::create "PppoxConnectWaitCommand" -under $sequencerLoopCommand]

set waitCommand2 [::sth::sthCore::invoke stc::create "WaitCommand" -under $sequencerLoopCommand "-waitTime $waitTime"]
    
    
    ::sth::sthCore::invoke stc::config $pppBindWaitCommand "-ObjectList {$hostHandle}"
    ::sth::sthCore::invoke stc::config $pppBindCommand "-BlockList {$blockList}"
    ::sth::sthCore::invoke stc::config $pppReleaseWaitCommand "-ObjectList {$hostHandle}"
    ::sth::sthCore::invoke stc::config $pppReleaseCommand "-BlockList {$blockList}"
    ::sth::sthCore::invoke stc::config  $sequencerLoopCommand "-CommandList \"$pppReleaseCommand $pppReleaseWaitCommand $waitCommand1 $pppBindCommand $pppBindWaitCommand $waitCommand2\""
    ::sth::sthCore::invoke stc::config  $sequencer "-CommandList $sequencerLoopCommand"
}

proc ::sth::Ancp::checkDependency {cmdType option dependentValue} {  
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $option dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::Ancp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $::sth::Ancp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::Ancp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in ancpTable.tcl
    foreach item $::sth::Ancp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Ancp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Ancp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Ancp:: $cmdType $opt $::sth::Ancp::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::Ancp::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Ancp::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}
