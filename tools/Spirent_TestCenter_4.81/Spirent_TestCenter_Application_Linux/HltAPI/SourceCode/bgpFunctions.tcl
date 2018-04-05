# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Bgp {
    set createResultQuery 0
    variable bgp_subscription_state 0
    variable ipv4Version 4
    variable ipv6Version 6
}

###
#  Name:    emulation_bgp_config_enable
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Create one or more bgp routers.
###
proc ::sth::Bgp::emulation_bgp_config_enable { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_enable $rklName"
	
	upvar 1 $rklName returnKeyedList
	variable ipv4Version
	variable ipv6Version
	
	# check if the port_handle/handle is provided value is valid
	if {[info exists ::sth::Bgp::userArgsArray(port_handle)]} {
		set portHandle $::sth::Bgp::userArgsArray(port_handle)
		if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
		    return -code error "Invalid value of \"-port_handle\" $portHandle"
	    }
	} elseif {[info exists ::sth::Bgp::userArgsArray(handle)]} {
	    #puts "Pleasse be noted BGP protocol will be enable in the Device $::sth::Bgp::userArgsArray(handle)"
    } else {
		return -code error "\"-port_handle\" or \"-handle\" is mandatory in enable mode"
	}
	
	# set default values for non-user defined switches
	foreach key [array names ::sth::Bgp::emulation_bgp_config_default] {
	    if {![info exists ::sth::Bgp::userArgsArray($key)]} {
	        set defaultValue [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $key default]
	        if {![string match $defaultValue "_none_"]} {
	            set ::sth::Bgp::userArgsArray($key) $defaultValue
	        }
	    }
	}
	
    # setup start/step values
    if {[info exists ::sth::Bgp::userArgsArray(ip_stack_version)]} {
	set version $::sth::Bgp::userArgsArray(ip_stack_version)
    } else {
	set version $::sth::Bgp::userArgsArray(ip_version)
	if {$::sth::Bgp::userArgsArray(ip_version) == 6} {
	    #earlier when there is no option netmask_ipv6 next_hop_ipv6 next_hop_ipv6_step
	    #customer will input netmask next_hop_ip next_hop_ip_step for the ipv5 usage,
	    #for backward compatible, we will change them to the ipv6 for internally
	    set ele_changed(netmask) netmask_ipv6
	    set ele_changed(next_hop_ip) next_hop_ipv6
	    set ele_changed(next_hop_ip_step) next_hop_ipv6_step
	    foreach element [array names ele_changed] {
		if {[info exists ::sth::Bgp::userArgsArray($element)]} {
		    set element_changed $ele_changed($element)
		    set ::sth::Bgp::userArgsArray($element_changed) $::sth::Bgp::userArgsArray($element)
		    unset ::sth::Bgp::userArgsArray($element)
		    set pri_ori [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $element priority]
		    set pri_changed [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $element_changed priority]
		    set indx [lsearch $::sth::Bgp::sortedSwitchPriorityList "$pri_ori $element"]
		    set ::sth::Bgp::sortedSwitchPriorityList [lreplace $::sth::Bgp::sortedSwitchPriorityList $indx $indx "$pri_changed $element_changed"]
		}
	    }
	}
    }
    
    set routerList {}
    set mode enable
	
    if {[info exists ::sth::Bgp::userArgsArray(port_handle)]} {
        for {set i 0} {$i < $::sth::Bgp::userArgsArray(count)} {incr i} {
            # create router
	    if {[info exists ipResultIf]} {
		unset ipResultIf
	    }
            set rtrHandle [::sth::sthCore::invoke stc::create EmulatedDevice -under $::sth::GBLHNDMAP(project)]
            if {[catch {
                # configure router level options
                configRouter $rtrHandle $mode $i
                
                # FIXME: check port to get layer 2 encapsulation...for now we're only supporting ethernet
                # configure the ethernet stack for BGP router
                #add for ATM. if ATM option is provided, don't need to create ethiiif
                if {[info exists ::sth::Bgp::userArgsArray(vpi)] ==1 || [info exists ::sth::Bgp::userArgsArray(vci)] ==1} {
                     set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $rtrHandle]
                    configAtmIf $atmResultIf $i
                } else {
                    set ethResultIf [::sth::sthCore::invoke stc::create EthIIIf -under $rtrHandle]
                    configEthIf $ethResultIf $mode $i
                } 
                
            # qinq support
                if {[info exists ::sth::Bgp::userArgsArray(vlan_outer_id)] && [info exists atmResultIf] == 0 } {
                    set vlanOuterResultIf [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle]
                    configOuterVlanIf $vlanOuterResultIf $mode $i  
                }
            
                # configure vlan if option is provided
                if {[info exists ::sth::Bgp::userArgsArray(vlan_id)] && [info exists atmResultIf] == 0 } {
                    set vlanResultIf [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle]
                    configVlanIf $vlanResultIf $mode $i  
                }
                
                # configure the ip stack for BGP router
                if {[string match $version "4_6"]} {
                    set ipv4ResultIf [::sth::sthCore::invoke stc::create Ipv4If -under $rtrHandle]
                    configIpInterface $ipv4ResultIf $mode $i
                    lappend ipResultIf $ipv4ResultIf
                    set ipv6ResultIf [::sth::sthCore::invoke stc::create Ipv6If -under $rtrHandle]
                    configIpv6Interface $ipv6ResultIf $mode $i
                    lappend ipResultIf $ipv6ResultIf
                } else {
                    set ipResultIf [::sth::sthCore::invoke stc::create Ipv${version}If -under $rtrHandle]
                    if {$version == 4} {
                        configIpInterface $ipResultIf $mode $i
                    } else {
                        configIpv6Interface $ipResultIf $mode $i
                    }
                }

                
                # configure a link local stack for ipv6
                if {$version == 6 || [string match $version "4_6"]} {
#                    set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                    set linkLocalIp "FE80:0:0:0"
#                    foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                        append linkLocalIp ":$num1$num2$num3$num4"
#                    }
                    set linkLocalHandle [::sth::sthCore::invoke stc::create Ipv6If -under $rtrHandle "-Address fe80::2 -PrefixLength 128"]
                    ::sth::sthCore::invoke stc::config $linkLocalHandle -AllocateEui64LinkLocalAddress true
                }
                
                # configure router to run BGP
                set bgpRtrHandle [::sth::sthCore::invoke stc::create BgpRouterConfig -under $rtrHandle]
                configBgpRouter $bgpRtrHandle $mode $i
                
                # configure authentication
                set bgpAuthHandle [::sth::sthCore::invoke stc::get $bgpRtrHandle -children-BgpAuthenticationParams]
                configBgpAuthentication $bgpAuthHandle $mode $i
		
		set projectHandle [::sth::sthCore::invoke stc::get $rtrHandle -parent]
	        set bgpGlobalHandle [::sth::sthCore::invoke stc::get $projectHandle -children-BgpGlobalConfig]
		configBgpGlobal $bgpGlobalHandle $mode $i
                                
                #enable/disable BFD
                if {[info exists ::sth::Bgp::userArgsArray(bfd_registration)]} {
                    if {$::sth::Bgp::userArgsArray(bfd_registration) == 1} {
                        configBfdRegistration $rtrHandle $mode $i
                    }
                }
                          
                # setup relations
                ::sth::sthCore::invoke stc::config $rtrHandle "-AffiliationPort-targets $::sth::Bgp::userArgsArray(port_handle)"
                
                # adjust the stack for vlan relation
                if { [info exists atmResultIf] } {
                   #set baseIf $atmResultIf
                   set lowerIf $atmResultIf
                } else {
                    #set baseIf $ethResultIf
                    set lowerIf $ethResultIf
                }
            
            #qinq support
                if {[info exists ::sth::Bgp::userArgsArray(vlan_outer_id)] && [info exists ethResultIf]} {
                    ::sth::sthCore::invoke stc::config $vlanOuterResultIf "-StackedOnEndpoint-targets $ethResultIf"
                    
                    if {![info exists ::sth::Bgp::userArgsArray(vlan_id)]} {
                         ::sth::sthCore::processError returnKeyedList "Error. Vlan_id option needed when outer vlan is configured"
                 return $returnKeyedList 
                    }
                
                    if {[info exists ::sth::Bgp::userArgsArray(vlan_id)] && [info exists ethResultIf]} {
                        ::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $vlanOuterResultIf"
                     set lowerIf $vlanResultIf   
                    }
                } elseif {[info exists ::sth::Bgp::userArgsArray(vlan_id)] && [info exists ethResultIf]} {
                    ::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $ethResultIf"
                    set lowerIf $vlanResultIf   
                }
                
                # adjust the stack for gre relation
                if {[info exists ::sth::Bgp::userArgsArray(tunnel_handle)] != 0} {
                   if {[catch {::sth::createGreStack $::sth::Bgp::userArgsArray(tunnel_handle) $rtrHandle $lowerIf [expr $i + 1] } returnIf]} {
                      return -code error "Internal error: failed to create Gre Stack"
                    } else {
                        set lowerIf $returnIf
                    }
                }
                #stack the top ipif on lowerif
                if {[llength $ipResultIf] == 1} {
                    ::sth::sthCore::invoke stc::config $ipResultIf "-StackedOnEndpoint-targets $lowerIf"
                } else {
                    #for dual stack
                    ::sth::sthCore::invoke stc::config $ipv4ResultIf "-StackedOnEndpoint-targets $lowerIf"
                    #set lowerIf $ipv4ResultIf
                    ::sth::sthCore::invoke stc::config $ipv6ResultIf "-StackedOnEndpoint-targets $lowerIf"
                }

                if {$version == $ipv6Version || [string match $version "4_6"]} {
                    ::sth::sthCore::invoke stc::config $linkLocalHandle "-StackedOnEndpoint-targets $lowerIf"
                }
            
            
                # adjust the stack for link local stack relation
                if {$version == 6 || [string match $version "4_6"]} {
                    set ipstacking "$ipResultIf $linkLocalHandle"
                } else {
                    set ipstacking "$ipResultIf"
                }
                ::sth::sthCore::invoke stc::config $rtrHandle "-TopLevelIf-targets {$ipstacking} -PrimaryIf-targets {$ipstacking}"
                # assign the UsesIf (for IPv6 assign to the global Ipv6If)
                if {[llength $ipResultIf] == 1} {
                    ::sth::sthCore::invoke stc::config $bgpRtrHandle "-UsesIf-targets $ipResultIf"
                } else {
                    #dual stack
                    ::sth::sthCore::invoke stc::config $bgpRtrHandle "-UsesIf-targets $ipv6ResultIf"
                }
                #bfd relation if need
                set bfdRtrCfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
    
                if {[llength $bfdRtrCfg] != 0} {
                    #for IPv6 assign to the global Ipv6If
                    if {[llength $ipResultIf] == 1} {
                        ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
                    } else {
                        #dual stack
                        ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipv6ResultIf"
                    }
                }
                # configure bgp custom pdus
				if {[info exists ::sth::Bgp::userArgsArray(custom_pdus)]} {
                    ::sth::sthCore::updateListToHex ::sth::Bgp::userArgsArray(custom_pdus)                    
                    # apply before creating custom pdus to avoid deletion failure
                    ::sth::sthCore::invoke stc::apply
                    foreach cuspdu $::sth::Bgp::userArgsArray(custom_pdus) {                        
                        ::sth::sthCore::invoke stc::create BgpCustomPdu -under $bgpRtrHandle -pdu $cuspdu                        
				    }
				}
            } routerConfigErr]} {
                # if an error occurs while configuring the router, we need to remove it
                ::sth::sthCore::invoke stc::delete $rtrHandle
                return -code error $routerConfigErr
            }
    
            lappend routerList $rtrHandle
        }
    } else {
        set rtrHandles $::sth::Bgp::userArgsArray(handle)
        set routerList $::sth::Bgp::userArgsArray(handle)
        
	set idx 0
	set bgpRtrHandle ""
	foreach rtrHandle $rtrHandles {
	    if {[::sth::sthCore::invoke stc::get $rtrHandle -children-BgpRouterConfig] != ""} {
		set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-BgpRouterConfig]
		#::sth::sthCore::processError returnKeyedList "$rtrHandle already has BGP enable" {}
                #return $::sth::sthCore::FAILURE
	    }
	    if {$bgpRtrHandle==""} {
	    # configure BgpRouterConfig
	        if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $rtrHandle  -CreateClassId [string tolower BgpRouterConfig]]
                              set bgpRtrHandle $ProtocolCreateOutput(-ReturnList)} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::perform ProtocolCreate $err" {}
                    return $::sth::sthCore::FAILURE
		}
            }
	    configBgpRouter $bgpRtrHandle $mode $idx
	    
	    # configure authentication
	    set bgpAuthHandle [::sth::sthCore::invoke stc::get $bgpRtrHandle -children-BgpAuthenticationParams]
	    configBgpAuthentication $bgpAuthHandle $mode $idx
	    
	    #enable/disable BFD
	    if {[info exists ::sth::Bgp::userArgsArray(bfd_registration)]} {
			if {$::sth::Bgp::userArgsArray(bfd_registration) == 1} {
				configBfdRegistration $rtrHandle $mode 0
				set bfdRtrCfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
				set ipResultIf [::sth::sthCore::invoke stc::get $rtrHandle -PrimaryIf-Targets]
				if {$version == 6} {
					foreach ipif $ipResultIf {
						set addr [::sth::sthCore::invoke stc::get  $ipif -Address]
						if {![regexp -nocase "FE80" $addr] } {
							set ipResultIf $ipif
							break
						}
					}
				}	
				::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
			}
	    }
        # configure bgp custom pdus
        if {[info exists ::sth::Bgp::userArgsArray(custom_pdus)]} {
            ::sth::sthCore::updateListToHex ::sth::Bgp::userArgsArray(custom_pdus)            
            # apply before creating custom pdus to avoid deletion failure
            ::sth::sthCore::invoke stc::apply
            foreach cuspdu $::sth::Bgp::userArgsArray(custom_pdus) {
                ::sth::sthCore::invoke stc::create BgpCustomPdu -under $bgpRtrHandle -pdu $cuspdu
            }
        }
	
	    set projectHandle [::sth::sthCore::invoke stc::get $rtrHandle -parent]
	    set bgpGlobalHandle [::sth::sthCore::invoke stc::get $projectHandle -children-BgpGlobalConfig]
	    configBgpGlobal $bgpGlobalHandle $mode $idx
	    incr idx
	}
    }
    # apply config
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} applyError]} {
            # if apply fails, delete any routers we may have created
            foreach rtr $routerList {
                ::sth::sthCore::invoke stc::delete $rtr
            }
            return -code error $applyError
        }
    }

	# subscribe to the resultdataset
    #if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Bgp:: BgpRouterConfig BgpRouterResults returnKeyedList]} {
    #    return -code error "Error subscribing to the Bgp result data set"
    #}
	
    # prepare the keyed list to be returned to HLTAPI layer
    keylset returnKeyedList handles $routerList 
    keylset returnKeyedList handle $routerList 
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

###
#  Name:    emulation_bgp_config_modify
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Modify bgp router.
###
proc ::sth::Bgp::emulation_bgp_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_modify $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	if {![info exists ::sth::Bgp::userArgsArray(handle)]} {
		return -code error "the switch \"-handle\" is mandatory in modify mode"
	} else {
	    set rtrHandle $::sth::Bgp::userArgsArray(handle)
		if {![::sth::Bgp::isBgpRouterHandleValid $rtrHandle]} {
			return -code error "Invalid bgp router handle $rtrHandle"
		}
	}
	
	# fixme: not sure if we'll support modifying port handles
	set unsupportedModifyOptions {port_handle count}

    # we don't want to execute unnessary config functions so we'll make a list of the
    # ones we need to run based off of the user's input
    set functionsToRun {}
    foreach item $::sth::Bgp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[lsearch $unsupportedModifyOptions $opt] > -1} {
        	    return -code error "unable to modify the \"-$opt\" in modify mode"
        	}
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: emulation_bgp_config $opt modify]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach func $functionsToRun {
        # these functions are mapped to switches in bgpTable.tcl
        switch -- $func {
            configEthIf {
                set ethiiIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                configEthIf $ethiiIfHandle modify 0
            }
	     configAtmIf {
                set atmIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-aal5if]
                if {$atmIfHandle != ""} {
                    configAtmIf $atmIfHandle 0
                }
            }
            configRouter {
                configRouter $rtrHandle modify 0
            }
            configIpInterface {
                set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
                set ipVersion [::sth::sthCore::invoke stc::get $bgpRtrHandle -IpVersion]
                set ipIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv4If]
                configIpInterface [lindex $ipIfHandle 0] modify 0
            }
            configIpv6Interface {
                set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
                set ipVersion [::sth::sthCore::invoke stc::get $bgpRtrHandle -IpVersion]
                set ipIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv6If]
                configIpv6Interface [lindex $ipIfHandle 0] modify 0
            }
            configOuterVlanIf {
                set vlanIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif]
                if {$vlanIfHandle eq ""} {
                    ::sth::sthCore::processError returnKeyedList "Error. Vlan_id option needed when outer vlan is configured"
                    return $returnKeyedList 
                    
                } elseif  {[llength $vlanIfHandle] == 1} {
                    set vlanouterIfHandle [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle]
                    configOuterVlanIf $vlanouterIfHandle enable 0
                    set ethiiIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                    ::sth::sthCore::invoke stc::config $vlanouterIfHandle "-StackedOnEndpoint-targets $ethiiIfHandle"
                    ::sth::sthCore::invoke stc::config $vlanIfHandle "-StackedOnEndpoint-targets $vlanouterIfHandle"
                    set lowerIf $vlanIfHandle   
                    set ipv4ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv4If]
                    set ipv6ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv6If]
                    if {$ipv4ResultIf ne  ""} {
                        ::sth::sthCore::invoke stc::config $ipv4ResultIf "-StackedOnEndpoint-targets $lowerIf"
                    } elseif {$ipv6ResultIf ne  ""} {
                        set  Ipv6Interface [lindex $ipv6ResultIf 0]
                        set  Ipv6linklock  [lindex $ipv6ResultIf 1]
                        ::sth::sthCore::invoke stc::config $Ipv6Interface "-StackedOnEndpoint-targets $lowerIf"
                        ::sth::sthCore::invoke stc::config $Ipv6linklock  "-StackedOnEndpoint-targets $lowerIf"
                    }
                    
                }  else {
                    if {[llength $vlanIfHandle] == 2} {
                        set vlanIfHandle [lindex $vlanIfHandle 0]
                    }
                
                    configOuterVlanIf $vlanIfHandle modify 0
                }
            }
            configVlanIf {
                set vlanIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif]
                if  {$vlanIfHandle eq ""} {
                    set vlanIfHandle [::sth::sthCore::invoke stc::create VlanIf -under $rtrHandle]
                    configVlanIf $vlanIfHandle enable 0
                    set ethiiIfHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                    ::sth::sthCore::invoke stc::config $vlanIfHandle "-StackedOnEndpoint-targets $ethiiIfHandle"
                    set lowerIf $vlanIfHandle   
                    set ipv4ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv4If]
                    set ipv6ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv6If]
                    if {$ipv4ResultIf ne  ""} {
                        ::sth::sthCore::invoke stc::config $ipv4ResultIf "-StackedOnEndpoint-targets $lowerIf"
                    } elseif {$ipv6ResultIf ne  ""} {
                        set  Ipv6Interface [lindex $ipv6ResultIf 0]
                        set  Ipv6linklock  [lindex $ipv6ResultIf 1]
                        ::sth::sthCore::invoke stc::config $Ipv6Interface "-StackedOnEndpoint-targets $lowerIf"
                        ::sth::sthCore::invoke stc::config $Ipv6linklock  "-StackedOnEndpoint-targets $lowerIf"
                    }
                    
                } else {
                    if {[llength $vlanIfHandle] == 2} {
                        set vlanIfHandle [lindex $vlanIfHandle 1]
                    }
                    configVlanIf $vlanIfHandle modify 0
                }
            }
            configBgpRouter {
                set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
            	configBgpRouter $bgpRtrHandle modify 0
            }
            configBgpGlobal {
                set bgpGlobalHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-bgpglobalconfig]
            	configBgpGlobal $bgpGlobalHandle modify 0
            }
            configBgpAuthentication {
                set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
            	set bgpAuthHandle [::sth::sthCore::invoke stc::get $bgpRtrHandle -children-BgpAuthenticationParams]
            	configBgpAuthentication $bgpAuthHandle modify 0
            }
	    configGreIf {
               if {[catch {::sth::configGreStack  $::sth::Bgp::userArgsArray(tunnel_handle) $rtrHandle} err]} {
            		return -code error "unable to config bgp gre stack"
            	}
            }
            configBfdRegistration {
                
                configBfdRegistration $rtrHandle modify 0
            }  
            configCustomPdus {
                # TODO: not tested
                ::sth::sthCore::updateListToHex ::sth::Bgp::userArgsArray(custom_pdus)
                set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
                set bgpCuspduHandle [::sth::sthCore::invoke stc::get $bgpRtrHandle -children-bgpcustompdu]
                foreach cuspdu $bgpCuspduHandle {
                    configCustomPdus $cuspdu modify 0
                }
			}
            default {
                return -code error "unknown function: $func"   
            }
        }
    }
    
    if {!$::sth::sthCore::optimization} {  
        if {[catch {::sth::sthCore::doStcApply } err]} {
            return -code error "Error applying config: $err"
        }
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

###
#  Name:    emulation_bgp_config_disable
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Disable (delete) bgp routers. It will delete all bgp routers based on the port_handle switch value.
###
proc ::sth::Bgp::emulation_bgp_config_disable { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_disable $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	# user can specify port_handle, which will remove all bgp routers under it. Or specify specific router handles
	if {[info exists ::sth::Bgp::userArgsArray(port_handle)]} {
        set portHandle $::sth::Bgp::userArgsArray(port_handle)
    	#if {![::sth::sthCore::IsPortValid $portHandle Msg]} {
    	#	return -code error "Invalid \"-port_handle\" value $portHandle"
    	#}
        set bgpRouters {}
        foreach port $portHandle {
    	set affRouters [::sth::sthCore::invoke stc::get $port -affiliationport-sources]
    	# verify which of these routers are BGP routers
    	foreach rtr $affRouters {
    	    if {[isBgpRouterHandleValid $rtr]} {
			    lappend bgpRouters $rtr
	        }
    	}
     }
	} elseif {[info exists ::sth::Bgp::userArgsArray(handle)]} {
	    set bgpRouters $::sth::Bgp::userArgsArray(handle)
	    foreach rtr $bgpRouters {
	        if {![isBgpRouterHandleValid $rtr]} {
	            return -code error "$rtr is not a valid BGP router."   
	        }
	    }
	} else {
	    return -code error "must specify either \"-port_handle\" or \"-handle\"."
	}
	
	foreach bgpRtr $bgpRouters {
		::sth::sthCore::invoke stc::delete $bgpRtr
	}
        
        # SPIRENT_MOD 08-08-12 Fei Cheng
        #after deleting routes, if the streamblock's src binding or dst binding is empty, delete it.
        foreach handle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port] {
            foreach streamblock [::sth::sthCore::invoke stc::get $handle -Children-StreamBlock ] {
                set sb_dstbding [::sth::sthCore::invoke stc::get $streamblock -DstBinding-targets]
                set sb_srcbding [::sth::sthCore::invoke stc::get $streamblock -SrcBinding-targets]
                if {($sb_dstbding == "" )|| ($sb_srcbding == "")} {
                    ::sth::sthCore::invoke stc::delete $streamblock
                }
            }
        }
        # SPIRENT_MOD end
        
        
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

proc ::sth::Bgp::emulation_bgp_config_inactive { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_inactive $rklName"

    upvar 1 $rklName returnKeyedList
    
    if {![info exists  ::sth::Bgp::userArgsArray(handle)]} {
        return -code error "Error: Missing a mandatory attribute -handle for inactive mode."
    }
    set  bgpRouters $::sth::Bgp::userArgsArray(handle)
    
    foreach bgpRouter $bgpRouters {
	set bgpRtrCfg [::sth::sthCore::invoke stc::get $bgpRouter "-children-BgpRouterConfig"]
	::sth::sthCore::invoke stc::config $bgpRtrCfg "-Active FALSE -LocalActive FALSE"
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Bgp::emulation_bgp_config_active { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_active $rklName"

    upvar 1 $rklName returnKeyedList
    
    if {![info exists  ::sth::Bgp::userArgsArray(handle)]} {
        return -code error "Error: Missing a mandatory attribute -handle for active mode."
    }
    set  bgpRouters $::sth::Bgp::userArgsArray(handle)
    
    foreach bgpRouter $bgpRouters {
	set bgpRtrCfg [::sth::sthCore::invoke stc::get $bgpRouter "-children-BgpRouterConfig"]
	::sth::sthCore::invoke stc::config $bgpRtrCfg "-Active TRUE -LocalActive TRUE"
    }
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::Bgp::emulation_bgp_config_readvertise { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_config_readvertise $rklName"
	
    upvar 1 $rklName returnKeyedList
    
    if {![info exists ::sth::Bgp::userArgsArray(handle)]} {
	    return -code error "the switch \"-handle\" is mandatory in readvertise mode"
    }
    
    set rtrHandle $::sth::Bgp::userArgsArray(handle)
    if {![::sth::Bgp::isBgpRouterHandleValid $rtrHandle]} {
	    return -code error "Invalid bgp router handle $rtrHandle"
    }

    ::sth::sthCore::invoke stc::perform BgpReadvertiseRoute -RouterList $rtrHandle

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::Bgp::emulation_bgp_config_activate { rklName } {

	upvar 1 $rklName returnKeyedList

    array set mainDefaultAry {}
    set opList "local_as local_as4 local_as4_step local_as_step remote_as4 remote_as4_step remote_ip_addr remote_ipv6_addr bfd_registration graceful_restart_enable ip_version \
	bgp_mode remote_ip_addr_step remote_ipv6_addr_step local_as4_enable remote_as4_enable use_gateway_remote_ip_addr remote_as remote_as_step"
    foreach key $opList {
        if {[info exists ::sth::Bgp::emulation_bgp_config_default($key)]} {
            set value $::sth::Bgp::emulation_bgp_config_default($key)
            set mainDefaultAry($key) $value
        }
    }
	
    set opList "md5_enable md5_key md5_key_id"
    foreach key $opList {
        if {[info exists ::sth::Bgp::emulation_bgp_config_default($key)]} {
            set value $::sth::Bgp::emulation_bgp_config_default($key)
            set authDefaultAry($key) $value
        }
    }

    set mOptionList ""
    set authOptionList ""
    foreach idx [array names mainDefaultAry] {
        if {[info exists ::sth::Bgp::userArgsArray($idx)]} {
            if {[info exists ::sth::Bgp::emulation_bgp_config_$idx\_fwdmap($::sth::Bgp::userArgsArray($idx))]} {
                set value [set ::sth::Bgp::emulation_bgp_config_$idx\_fwdmap($::sth::Bgp::userArgsArray($idx))]
                set ::sth::Bgp::userArgsArray($idx) $value
            }
            set mainDefaultAry($idx) $::sth::Bgp::userArgsArray($idx)
        }
        if {[string equal $mainDefaultAry($idx) "_none_"]} { continue }
        regsub -all {[.]} [set ::sth::Bgp::emulation_bgp_config_stcattr($idx)] "" stcAttr
		
		#special handling for remote_as remote_as_step
		if {[string equal $stcAttr DutAsNum] ||
			[string equal $stcAttr DutAsNumStep]} {
			regsub -all {DutAsNum} $stcAttr "DutAs" stcAttr
		}
		
        append mOptionList " -$stcAttr $mainDefaultAry($idx)"
    }

    foreach idx [array names authDefaultAry] {
        if {[info exists ::sth::Bgp::userArgsArray($idx)]} {
            set authDefaultAry($idx) $::sth::Bgp::userArgsArray($idx)
			if {[info exists ::sth::Bgp::emulation_bgp_config_$idx\_fwdmap($::sth::Bgp::userArgsArray($idx))]} {
				set authDefaultAry($idx) [set ::sth::Bgp::emulation_bgp_config_$idx\_fwdmap($::sth::Bgp::userArgsArray($idx))]
			}
        }
        if {[string equal $authDefaultAry($idx) "_none_"]} { continue }
        append authOptionList " -[set ::sth::Bgp::emulation_bgp_config_stcattr($idx)] $authDefaultAry($idx)"
    }
        
    if {![info exists ::sth::Bgp::userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the activate mode of emulation_bgp_config" {}
		keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    } else {
		set bgpGenHnd [::sth::sthCore::invoke stc::create BgpDeviceGenProtocolParams -under $::sth::Bgp::userArgsArray(handle) $mOptionList]
		if { $authOptionList != "" } {
			set authHnd [::sth::sthCore::invoke stc::get $bgpGenHnd -children-BgpAuthenticationParams]
			::sth::sthCore::invoke stc::config $authHnd $authOptionList
		}

        if {[info exists ::sth::Bgp::userArgsArray(expand)] &&
            $::sth::Bgp::userArgsArray(expand) == "false"} {
            keylset returnKeyedList handle_list ""
			keylset returnKeyedList handle ""
			keylset returnKeyedList handles ""
        } else {
            array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $::sth::Bgp::userArgsArray(handle)]
            keylset returnKeyedList handle_list $return(-ReturnList)
            array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className BgpRouterConfig -rootlist $return(-ReturnList)]
            keylset returnKeyedList bgp_handle_list $rtn(-ObjectList)
			keylset returnKeyedList handle ""
			keylset returnKeyedList handles $return(-ReturnList)
        }
    }

	keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



###
#  Name:    emulation_bgp_control
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Control bgp emulation based on the following modes: start, stop, or restart
#
#  TODO:
#        - Add support for the following modes and keys:
#            1. link_flap
#                 a. link_flap_down_time
#                 b. link_flap_up_time
#            2. full_route_flap
#            3. partial_route_flap
#                 a. route_flap_down_time
#                 b. route_flap_up_time
#                 c. route_handle
#                 d. route_index_from
#                 e. route_index_to
#                 
###
proc ::sth::Bgp::emulation_bgp_control { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_control $rklName"

    variable bgp_subscription_state
    upvar 1 $rklName returnKeyedList

    if {([info exists ::sth::Bgp::userArgsArray(port_handle)])
        && ([info exists ::sth::Bgp::userArgsArray(handle)])} {
            ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle or -handle are mutually exclusive." {}
            return -code error $returnKeyedList
        }

    set bgpRouterHandles ""
    if {([info exists ::sth::Bgp::userArgsArray(handle)] && $::sth::Bgp::userArgsArray(handle) ne "all" ) && (![info exists ::sth::Bgp::userArgsArray(port_handle)])} {
        foreach handle $::sth::Bgp::userArgsArray(handle) {
            if {![::sth::Bgp::isBgpRouterHandleValid $handle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $handle is not a valid Bgp router handle" {}
                return -code error $returnKeyedList
            }
        }
        set bgpRouterHandles $::sth::Bgp::userArgsArray(handle)
    } elseif {([info exists ::sth::Bgp::userArgsArray(port_handle)] && $::sth::Bgp::userArgsArray(port_handle) ne "all" ) && (![info exists ::sth::Bgp::userArgsArray(handle)])} {
        foreach port_handle $::sth::Bgp::userArgsArray(port_handle) {
            if {[::sth::sthCore::IsPortValid $port_handle err]} {
                set port_host [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]
                foreach host $port_host {
                    if {![::sth::Bgp::isBgpRouterHandleValid $host]} {
                        continue
                    }
                    lappend bgpRouterHandles $host
                }
            } else {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $port_handle" {}
                return -code error $returnKeyedList
            }
        }
    } else {
           set all_ports [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]
            foreach port_handle $all_ports {
               if {[::sth::sthCore::IsPortValid $port_handle err]} {
                   set port_host [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]
                   foreach host $port_host {
                      if {![::sth::Bgp::isBgpRouterHandleValid $host]} {
                          continue
                      }
                      lappend bgpRouterHandles $host
                   }
               } else {
                   ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $port_handle" {}
                   return -code error $returnKeyedList
                 }
            }
    }

    if {$bgp_subscription_state == 0} {
        # subscribe to the resultdataset
        if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Bgp:: BgpRouterConfig BgpRouterResults returnKeyedList]} {
            return -code error "Error subscribing to the Bgp result data set"
        }
        set bgp_subscription_state 1
    }

    switch -- $::sth::Bgp::userArgsArray(mode) {
        start {
            ::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $bgpRouterHandles
        }
        stop {
            ::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $bgpRouterHandles
        }
        restart {
            foreach bgpRouterHandle $bgpRouterHandles {
                set bgpRtrConfigHandle [::sth::sthCore::invoke stc::get $bgpRouterHandle -children-bgprouterconfig]
                # verify that the router has graceful restart enabled
                set gracefulRestartEnabled [::sth::sthCore::invoke stc::get $bgpRtrConfigHandle -GracefulRestart]
                if {!$gracefulRestartEnabled} {
                    return -code error "\"-graceful_restart_enable\" not enabled."
                }
                lappend bgpRtrConfigHandles $bgpRtrConfigHandle
            }
            
            ::sth::sthCore::invoke stc::perform BgpRestartRouter -RouterList $bgpRtrConfigHandles
        }
        link_flap {
            # validate mandatory args
            set reqdArgs {}
            foreach requiredArg {link_flap_down_time link_flap_up_time handle} {
                if {![info exists ::sth::Bgp::userArgsArray($requiredArg)]} {
                    lappend reqdArgs "\"-$requiredArg\""
                }
            }
            if {[llength $reqdArgs]} {
                return -code error "The following mandatory argument(s) are missing: [join $reqdArgs {, }]"
            }
            
            if {[info exists ::sth::Bgp::userArgsArray(flap_count)]} {
                set flapcount $::sth::Bgp::userArgsArray(flap_count)
            } else {
                set flapcount 1
            }
            
            
            
            ###
            # Sequence of commands
            #    1. BgpBreakTcpSessionCommand
            #    2. WaitCommand (-link_flap_down_time)
            #    3. BgpResumeTcpSessionCommand
            #    4. WaitCommand (-link_flap_up_time)
            ###
            
            # create the commands
            set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
            set sysHandle $::sth::sthCore::GBLHNDMAP(system)
            
            set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $seqHandle]
            
            set options [list -Code "6" -SubCode "0"]
            set bgpBreakCmdHdl [::sth::sthCore::invoke stc::create "BgpBreakTcpSessionCommand" -under $seqLoopCmd $options]
            
            set options [list -WaitTime $::sth::Bgp::userArgsArray(link_flap_down_time)]
            set dwnTimeCmdHdl [::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmd $options]
            
            set bgpResumeCmdHdl [::sth::sthCore::invoke stc::create "BgpResumeTcpSessionCommand" -under $seqLoopCmd]
            
            set options [list -WaitTime $::sth::Bgp::userArgsArray(link_flap_up_time)]
            set upTimeCmdHdl [::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmd $options]

            set sequenceList [list -CommandList "$bgpBreakCmdHdl $dwnTimeCmdHdl $bgpResumeCmdHdl $upTimeCmdHdl" -BreakpointList {} -DisabledCommandList {}]
            ::sth::sthCore::invoke stc::config $seqHandle $sequenceList
            
            ::sth::sthCore::invoke stc::config $seqLoopCmd [list "-IterationCount" $flapcount "-ExecutionMode" "BACKGROUND" "-GroupCategory" "REGULAR_COMMAND" "-ContinuousMode" FALSE "-ExecuteSynchronous" FALSE "-CommandList" "$bgpBreakCmdHdl $dwnTimeCmdHdl $bgpResumeCmdHdl $upTimeCmdHdl"]
            
            ::sth::sthCore::invoke stc::config  $seqHandle "-CommandList $seqLoopCmd"

            ## config the bgp events
            set routerlist $::sth::Bgp::userArgsArray(handle)
            ::sth::sthCore::invoke stc::config $bgpBreakCmdHdl "-RouterList {$routerlist}"
            ::sth::sthCore::invoke stc::config $bgpResumeCmdHdl "-RouterList {$routerlist}"
            
            # Start the sequencer
            ::sth::sthCore::invoke stc::perform sequencerStart
            ::sth::sthCore::invoke ::stc::waituntilcomplete
            ::sth::sthCore::invoke stc::delete $bgpBreakCmdHdl
            ::sth::sthCore::invoke stc::delete $dwnTimeCmdHdl
            ::sth::sthCore::invoke stc::delete $bgpResumeCmdHdl
            ::sth::sthCore::invoke stc::delete $upTimeCmdHdl
            ::sth::sthCore::invoke stc::delete $seqLoopCmd
        }
        full_route_flap {
            # validate mandatory args
            set reqdArgs {}
            foreach requiredArg {route_flap_down_time route_flap_up_time route_handle handle} {
                if {![info exists ::sth::Bgp::userArgsArray($requiredArg)]} {
                    lappend reqdArgs "\"-$requiredArg\""
                }
            }
            if {[llength $reqdArgs]} {
                return -code error "The following mandatory argument(s) are missing: [join $reqdArgs {, }]"
            }
            
            if {[info exists ::sth::Bgp::userArgsArray(flap_count)]} {
                set flapcount $::sth::Bgp::userArgsArray(flap_count)
            } else {
                set flapcount 1
            }
            
            set routelist $::sth::Bgp::userArgsArray(route_handle)
            set routerlist $::sth::Bgp::userArgsArray(handle)
            ###
            # Sequence of commands
            #    1. BgpWithdrawRouteCommand
            #    2. WaitCommand (-route_flap_down_time)
            #    3. BgpReadvertiseRouteCommand
            #    4. WaitCommand (-route_flap_up_time)
            ###
            
            # create the commands
            set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
            set sysHandle $::sth::sthCore::GBLHNDMAP(system)
            
            #add an option flap_count
            set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $seqHandle]
            
            set bgpWithdrawCmdHdl [::sth::sthCore::invoke stc::create "BgpWithdrawRouteCommand" -under $seqLoopCmd "-RouteList {$routelist}"]
            
            set options [list -WaitTime $::sth::Bgp::userArgsArray(route_flap_down_time)]
            set dwnTimeCmdHdl [::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmd $options]
            
            set bgpReadvertiseCmdHdl [::sth::sthCore::invoke stc::create "BgpReadvertiseRouteCommand" -under $seqLoopCmd "-RouterList {$routerlist}"]
            
            set options [list -WaitTime $::sth::Bgp::userArgsArray(route_flap_up_time)]
            set upTimeCmdHdl [::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmd $options]
            
            # Configure sequencer
            ::sth::sthCore::invoke stc::config $seqLoopCmd [list "-IterationCount" $flapcount "-ExecutionMode" "BACKGROUND" "-GroupCategory" "REGULAR_COMMAND" "-ContinuousMode" FALSE "-ExecuteSynchronous" FALSE "-CommandList" "$bgpWithdrawCmdHdl $dwnTimeCmdHdl $bgpReadvertiseCmdHdl $upTimeCmdHdl"]
            
            ::sth::sthCore::invoke stc::config  $seqHandle "-CommandList $seqLoopCmd"
            
            #####################
            
            # Start the sequencer
            ::sth::sthCore::invoke stc::perform sequencerStart
            ::sth::sthCore::invoke ::stc::waituntilcomplete
            ::sth::sthCore::invoke stc::delete $bgpWithdrawCmdHdl
            ::sth::sthCore::invoke stc::delete $dwnTimeCmdHdl
            ::sth::sthCore::invoke stc::delete $bgpReadvertiseCmdHdl
            ::sth::sthCore::invoke stc::delete $upTimeCmdHdl

            ::sth::sthCore::invoke stc::delete $seqLoopCmd
        }
        partial_route_flap {
            return -code error "\"-partial_route_flap\" mode is not supported"
        }
        advertise {
            # validate mandatory args
            set reqdArgs {}
            foreach requiredArg {route_handle route_type} {
                if {![info exists ::sth::Bgp::userArgsArray($requiredArg)]} {
                    lappend reqdArgs "\"-$requiredArg\""
                }
            }
            if {[llength $reqdArgs]} {
                return -code error "The following mandatory argument(s) are missing: [join $reqdArgs {, }]"
            }
            set routeType $::sth::Bgp::userArgsArray(route_type)
            set routeHandle $::sth::Bgp::userArgsArray(route_handle)
            
            switch -- $routeType {
                ip {
                   sth::sthCore::invoke stc::perform BgpAdvertiseRoute -RouteList $routeHandle
                }
                evpn_type1 {
                    sth::sthCore::invoke stc::perform BgpAdvertiseEvpnRouteCommand -RouteList $routeHandle -RouteType TYPE1
                }
                evpn_type2 {
                    sth::sthCore::invoke stc::perform BgpAdvertiseEvpnRouteCommand -RouteList $routeHandle -RouteType TYPE2
                }
                evpn_type3 {
                    sth::sthCore::invoke stc::perform BgpAdvertiseEvpnRouteCommand -RouteList $routeHandle -RouteType TYPE3
                }
                evpn_type4 {
                    sth::sthCore::invoke stc::perform BgpAdvertiseEvpnRouteCommand -RouteList $routeHandle -RouteType TYPE4
                }
                evpn_type5 {
                    sth::sthCore::invoke stc::perform BgpAdvertiseEvpnRouteCommand -RouteList $routeHandle -RouteType TYPE5
                }
                link_state {
                    sth::sthCore::invoke stc::perform BgpAdvertiseLinkState -RouteList $routeHandle
                }
                default {
                    return -code error "unsupported route_type: $routeType"	
                }
            }
        }
        withdraw {
            # validate mandatory args
            set reqdArgs {}
            foreach requiredArg {route_handle route_type} {
                if {![info exists ::sth::Bgp::userArgsArray($requiredArg)]} {
                    lappend reqdArgs "\"-$requiredArg\""
                }
            }
            if {[llength $reqdArgs]} {
                return -code error "The following mandatory argument(s) are missing: [join $reqdArgs {, }]"
            }
            set routeType $::sth::Bgp::userArgsArray(route_type)
            set routeHandle $::sth::Bgp::userArgsArray(route_handle)
            
            switch -- $routeType {
                ip {
                   sth::sthCore::invoke stc::perform BgpWithdrawRoute -RouteList $routeHandle
                }
                evpn_type1 {
                    sth::sthCore::invoke stc::perform BgpWithdrawEvpnRoute -RouteList $routeHandle -RouteType TYPE1
                }
                evpn_type2 {
                    sth::sthCore::invoke stc::perform BgpWithdrawEvpnRoute -RouteList $routeHandle -RouteType TYPE2
                }
                evpn_type3 {
                    sth::sthCore::invoke stc::perform BgpWithdrawEvpnRoute -RouteList $routeHandle -RouteType TYPE3
                }
                evpn_type4 {
                    sth::sthCore::invoke stc::perform BgpWithdrawEvpnRoute -RouteList $routeHandle -RouteType TYPE4
                }
                evpn_type5 {
                    sth::sthCore::invoke stc::perform BgpWithdrawEvpnRoute -RouteList $routeHandle -RouteType TYPE5
                }
                link_state {
                    sth::sthCore::invoke stc::perform BgpWithdrawLinkState -RouteList $routeHandle
                }
                default {
                    return -code error "unsupported route_type: $routeType"	
                }
            }
        }
        send_custom_pdu {
            # Sends BGP Custom PDU Command when the sessions are in the established state for the configured routers
            set routerState [::sth::sthCore::invoke stc::perform WaitForRouterState -ObjectList $bgpRouterHandles -WaitRouterState PROTOCOL_UP -WaitTime 30]
            if {![regexp {\-PassFailState PASSED} $routerState]} {
                return -code error "router not in ESTABLISHED state to send custom PDU: $routerState"
            }
            
            set bgpCustomPduHandles {}
            foreach bgpRouterHandle $bgpRouterHandles {
                set bgpRtrConfigHandle [::sth::sthCore::invoke stc::get $bgpRouterHandle -children-bgprouterconfig]
                set bgpCustomPduHandle [::sth::sthCore::invoke stc::get $bgpRtrConfigHandle -children-bgpcustompdu]                
                set bgpCustomPduHandles [concat $bgpCustomPduHandles $bgpCustomPduHandle]
            }
            ::sth::sthCore::invoke stc::perform BgpSendCustomPdu -CustomPduList $bgpCustomPduHandles
        }
    }

    # prepare the keyed list to be returned to HLTAPI layer
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

###
#  Name:    emulation_bgp_info
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Return bgp emulation info based on the following modes: stats, settings, or neighbors
#
#  TODO:
#        - Add support for "clear_stats" and "labels" modes
#        - Unsupported keys for "stats" mode:
#           1. duration
#           2. routing_protocol
#           3. num_nodes_routes
###
proc ::sth::Bgp::emulation_bgp_info { rklName } {
	::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_info $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	if {[info exist ::sth::Bgp::userArgsArray(handle)] && $::sth::Bgp::userArgsArray(handle) ne "all"} {
	   set bgpRouterHandle $::sth::Bgp::userArgsArray(handle)
	   if {![::sth::Bgp::isBgpRouterHandleValid $bgpRouterHandle]} {
	      return -code error "Error: the bgp router handle $bgpRouterHandle is not valid"
	   }
	} else {
	       set all_ports [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]
            foreach port_handle $all_ports {
               if {[::sth::sthCore::IsPortValid $port_handle err]} {
                   set port_host [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]
                   foreach host $port_host {
                      if {![::sth::Bgp::isBgpRouterHandleValid $host]} {
                          continue
                      }
                      lappend bgpRouterHandle $host
                   }
               } 
            }
	}
	foreach bgp_device $bgpRouterHandle {
	   # validate router handle
	   if {![::sth::Bgp::isBgpRouterHandleValid $bgpRouterHandle]} {
	    return -code error "Error: the bgp router handle $bgpRouterHandle is not valid"
	   }
        }
        foreach bgp_device $bgpRouterHandle {
            emulation_bgp_info_stats_calc returnKeyedList $bgp_device	     
        }
       
        if {[llength $bgpRouterHandle] == 1 && $returnKeyedList ne "" } {
	   set Temp_keyed_list [keylget returnKeyedList $bgp_device]
    	}
	if {[info exists Temp_keyed_list]} {
	  keylget Temp_keyed_list
	  foreach key $Temp_keyed_list {
	     keylset returnKeyedList [lindex $key 0] [lindex $key 1]
	  }
	}
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
  
}

proc ::sth::Bgp::emulation_bgp_info_stats_calc { rklName bgp_device } {

       upvar 1 $rklName returnKeyedList     
  
       
	set bgpRouterConfigHandle [::sth::sthCore::invoke stc::get $bgp_device -children-BgpRouterConfig]
	set bgpRouterResultsHandle [::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -children-BgpRouterResults]
	
	if {[catch {::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -IpVersion} bgpIpVerValue]} {
		return -code error "Internal Command Error while fetching IP version from $bgpRouterHandle"
	} else {
		switch -- [string tolower $bgpIpVerValue] {
			ipv4 {
			    # need to remap peers to the correct stc attribute
			    set ::sth::Bgp::emulation_bgp_info_stcattr(peers) DutIpv4Addr
				set ipIfHandle [::sth::sthCore::invoke stc::get $bgp_device -children-Ipv4If]
			}
			ipv6 {
			    # need to remap peers to the correct stc attribute
				set ::sth::Bgp::emulation_bgp_info_stcattr(peers) DutIpv6Addr
				if {[catch {::sth::sthCore::invoke stc::get $bgp_device -children-Ipv6If} ipIfHandle]} {
					return -code error "Internal Command Error while fetching IPv6 interface handle from $bgpRouterHandle"
				} else {
					set ipIfHandle [lindex $ipIfHandle 0] ;# fixme: should check to make sure we are returning the global address
				}
			}
			default {
				return -code error "Unsupported IP version $bgpIpVerValue"
			}
		}
	}
	
	# create an array mapping between stcObj and stcHandle
	set hdlArray(BgpRouterResults) $bgpRouterResultsHandle
	set hdlArray(BgpRouterConfig) $bgpRouterConfigHandle
	if {[llength $ipIfHandle] > 1} {
	    foreach iphandle $ipIfHandle {
		set lowerif [::sth::sthCore::invoke stc::get $iphandle -stackedonendpoint-Targets]
		if {[regexp {greif} $lowerif]} {
		    set hdlArray(IpIf) $iphandle
		    break
		}
	    } 
	} else {
	    set hdlArray(IpIf) $ipIfHandle
	}
		
    # create a list of key-value pairs based on the mode -- key to mode mapping defined in bgpTable.tcl
        set mode $::sth::Bgp::userArgsArray(mode)
        set retVal {}
        if {$mode != "ls_results"} {
            foreach key [array names ::sth::Bgp::emulation_bgp_info_mode] {
                foreach {tblMode tblProc} $::sth::Bgp::emulation_bgp_info_mode($key) {
                    if {[string match $tblMode $mode]} {
                        set stcObj [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_info $key stcobj]
                                set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_info $key stcattr]
    
                                    if {$hdlArray($stcObj) eq ""} {
                                            continue
                                    }
                        set val [::sth::sthCore::invoke stc::get $hdlArray($stcObj) -$stcAttr]
                        if {$tblMode == "stats"} {
                            # convert double to int
                            if {[string is double $val] && [scan $val %d intVal]} {
                                lappend retVal $key $intVal
                            } else {
                                if {$key == "sessions_established"} {
                                  if {$val == "ESTABLISHED"} {
                                     set val 1
                                  } else {
                                     set val 0
                                  }
                                  lappend retVal "sessions_configured" 1
                                }
                                lappend retVal $key $val
                            }
                        } else {
                            lappend retVal $key $val
                        }
                    }
                }
            }
        } else {
            if {[string length $::sth::sthCore::custom_path]} {
                set filename [file join $::sth::sthCore::custom_path routes.txt]
            } else {
                set filename [file join [pwd] routes.txt]
            }
            ::sth::sthCore::invoke stc::perform BgpViewRoutesCommand -routerList $bgpRouterConfigHandle -FileName $filename
            if {[file exists $filename]} {
                set fileHandle [open $filename "r"]
                set lsResults [split [read $fileHandle] \n]
                close $fileHandle
                file delete -force $filename
                foreach lstmp $lsResults {
                    set lskey [lindex $lstmp 0]
                    set lsvalue [lindex $lstmp 1]
                    switch -- $lskey {
                        TxAdvertisedLsLocalNodeDesc {lappend retVal tx_advertised_ls_local_node_desc $lsvalue}
                        RxAdvertisedLsLocalNodeDesc {lappend retVal rx_advertised_ls_local_node_desc $lsvalue}
                        TxWithdrawnLsLocalNodeDesc {lappend retVal tx_withdrawn_ls_local_node_desc $lsvalue}
                        RxWithdrawnLsLocalNodeDesc {lappend retVal rx_withdrawn_ls_local_node_desc $lsvalue}
                        TxAdvertisedLsRemoteNodeDesc {lappend retVal tx_advertised_ls_remote_node_desc $lsvalue}
                        RxAdvertisedLsRemoteNodeDesc {lappend retVal rx_advertised_ls_remote_node_desc $lsvalue}
                        TxWithdrawnLsRemoteNodeDesc {lappend retVal tx_withdrawn_ls_remote_node_desc $lsvalue}
                        RxWithdrawnLsRemoteNodeDesc {lappend retVal rx_withdrawn_ls_remote_node_desc $lsvalue}
                        TxAdvertisedLsLinkLocalRemoteId {lappend retVal tx_advertised_ls_link_local_remote_id $lsvalue}
                        RxAdvertisedLsLinkLocalRemoteId {lappend retVal rx_advertised_ls_link_local_remote_id $lsvalue}
                        TxWithdrawnLsLinkLocalRemoteId {lappend retVal tx_withdrawn_ls_link_local_remote_id $lsvalue}
                        RxWithdrawnLsLinkLocalRemoteId {lappend retVal rx_withdrawn_ls_link_local_remote_id $lsvalue}
                        TxAdvertisedLsIpv4InterfaceAddr {lappend retVal tx_advertised_ls_ipv4_intf_addr $lsvalue}
                        RxAdvertisedLsIpv4InterfaceAddr {lappend retVal rx_advertised_ls_ipv4_intf_addr $lsvalue}
                        TxWithdrawnLsIpv4InterfaceAddr {lappend retVal tx_withdrawn_ls_ipv4_intf_addr $lsvalue}
                        RxWithdrawnLsIpv4InterfaceAddr {lappend retVal rx_withdrawn_ls_ipv4_intf_addr $lsvalue}
                        TxAdvertisedLsIpv4NeighborAddr {lappend retVal tx_advertised_ls_ipv4_neighbor_addr $lsvalue}		
                        RxAdvertisedLsIpv4NeighborAddr {lappend retVal rx_advertised_ls_ipv4_neighbor_addr $lsvalue}		
                        TxWithdrawnLsIpv4NeighborAddr {lappend retVal tx_withdrawn_ls_ipv4_neighbor_addr $lsvalue}		
                        RxWithdrawnLsIpv4NeighborAddr {lappend retVal rx_withdrawn_ls_ipv4_neighbor_addr $lsvalue}		
                        TxAdvertisedLsMultiTopologyID {lappend retVal tx_advertised_ls_multitopo_id $lsvalue}
                        RxAdvertisedLsMultiTopologyID {lappend retVal rx_advertised_ls_multitopo_id $lsvalue}
                        TxWithdrawnLsMultiTopologyID {lappend retVal tx_withdrawn_ls_multitopo_id $lsvalue}
                        RxWithdrawnLsMultiTopologyID {lappend retVal rx_withdrawn_ls_multitopo_id $lsvalue}
                        TxAdvertisedLsIpReachInfo {lappend retVal tx_advertised_ls_ip_reach_info $lsvalue}
                        RxAdvertisedLsIpReachInfo {lappend retVal rx_advertised_ls_ip_reach_info $lsvalue}
                        TxWithdrawnLsIpReachInfo {lappend retVal tx_withdrawn_ls_ip_reach_info $lsvalue}
                        RxWithdrawnLsIpReachInfo {lappend retVal rx_withdrawn_ls_ip_reach_info $lsvalue}
                        TxAdvertisedLsAutonomousSys {lappend retVal tx_advertised_ls_as $lsvalue}
                        RxAdvertisedLsAutonomousSys {lappend retVal rx_advertised_ls_as $lsvalue}
                        TxWithdrawnLsAutonomousSys {lappend retVal tx_withdrawn_ls_as $lsvalue}
                        RxWithdrawnLsAutonomousSys {lappend retVal rx_withdrawn_ls_as $lsvalue}
                        TxAdvertisedLsLsId {lappend retVal tx_advertised_ls_ls_id $lsvalue}
                        RxAdvertisedLsLsId {lappend retVal rx_advertised_ls_ls_id $lsvalue}
                        TxWithdrawnLsLsId {lappend retVal tx_withdrawn_ls_ls_id $lsvalue}
                        RxWithdrawnLsLsId {lappend retVal rx_withdrawn_ls_ls_id $lsvalue}
                        TxAdvertisedLsOspfAreaId {lappend retVal tx_advertised_ls_ospf_area_id $lsvalue}
                        RxAdvertisedLsOspfAreaId {lappend retVal rx_advertised_ls_ospf_area_id $lsvalue}
                        TxWithdrawnLsOspfAreaId {lappend retVal tx_withdrawn_ls_ospf_area_id $lsvalue}
                        RxWithdrawnLsOspfAreaId {lappend retVal rx_withdrawn_ls_ospf_area_id $lsvalue}
                        TxAdvertisedLsIgpRouterId {lappend retVal tx_advertised_ls_igp_router_id $lsvalue}
                        RxAdvertisedLsIgpRouterId {lappend retVal rx_advertised_ls_igp_router_id $lsvalue}
                        TxWithdrawnLsIgpRouterId {lappend retVal tx_withdrawn_ls_igp_router_id $lsvalue}
                        RxWithdrawnLsIgpRouterId {lappend retVal rx_withdrawn_ls_igp_router_id $lsvalue}
                        TxLsAttributeMultiTopologyId {lappend retVal tx_ls_attribute_multitopo_id $lsvalue}
                        RxLsAttributeMultiTopologyId {lappend retVal rx_ls_attribute_multitop_id $lsvalue}
                        TxLsAttributeLinkLocalRemoteId {lappend retVal tx_ls_attribute_link_local_remote_id $lsvalue}
                        RxLsAttributeLinkLocalRemoteId {lappend retVal rx_ls_attribute_link_local_remote_id $lsvalue}
                        TxLsNodeFlagBits {lappend retVal tx_ls_node_flag_bits $lsvalue}
                        RxLsNodeFlagBits {lappend retVal rx_ls_node_flag_bits $lsvalue}
                        TxLsNodeName {lappend retVal tx_ls_node_name $lsvalue}
                        RxLsNodeName {lappend retVal rx_ls_node_name $lsvalue}
                        TxLsIsisAreaId {lappend retVal tx_ls_isis_area_id $lsvalue}
                        RxLsIsisAreaId {lappend retVal rx_ls_isis_area_id $lsvalue}
                        TxLsIpv4RouterIdLocalNode {lappend retVal tx_ls_ipv4_router_id_local_node $lsvalue}
                        RxLsIpv4RouterIdLocalNode {lappend retVal rx_ls_ipv4_router_id_local_node $lsvalue}
                        TxLsIpv4RouterIdRemoteNode {lappend retVal tx_ls_ipv4_router_id_remote_node $lsvalue}
                        RxLsIpv4RouterIdRemoteNode {lappend retVal rx_ls_ipv4_router_id_remote_node $lsvalue}
                        TxLsAdminGroup {lappend retVal tx_ls_admin_group $lsvalue}
                        RxLsAdminGroup {lappend retVal rx_ls_admin_group $lsvalue}
                        TxLsMaxLinkBw {lappend retVal tx_ls_max_link_bw $lsvalue}
                        RxLsMaxLinkBw {lappend retVal rx_ls_max_link_bw $lsvalue}
                        TxLsMaxReservableLinkBw {lappend retVal tx_ls_max_reservable_link_bw $lsvalue}
                        RxLsMaxReservableLinkBw {lappend retVal rx_ls_max_reservable_link_bw $lsvalue}
                        TxLsUnreservedBw {lappend retVal tx_ls_unreserved_bw $lsvalue}
                        RxLsUnreservedBw {lappend retVal rx_ls_unreserved_bw $lsvalue}
                        TxLsTeDefaultMetric {lappend retVal tx_ls_te_default_metric $lsvalue}
                        RxLsTeDefaultMetric {lappend retVal rx_ls_te_default_metric $lsvalue}
                        TxLsIgpMetric {lappend retVal tx_ls_igp_metric $lsvalue}
                        RxLsIgpMetric {lappend retVal rx_ls_igp_metric $lsvalue}
                        TxLsSharedRiskLinkGroup {lappend retVal tx_ls_shared_risk_link_group $lsvalue}
                        RxLsSharedRiskLinkGroup {lappend retVal rx_ls_shared_risk_link_group $lsvalue}
                        TxLsIgpFlags {lappend retVal tx_ls_igp_flags $lsvalue}
                        RxLsIgpFlags {lappend retVal rx_ls_igp_flags $lsvalue}
                        TxLsPrefixMetric {lappend retVal tx_ls_prefix_metric $lsvalue}
                        RxLsPrefixMetric {lappend retVal rx_ls_prefix_metric $lsvalue}
                    }
                }
	    }
	}
  
   
    # prepare the keyed list to be returned to HLTAPI layer
    if {[llength $retVal]} {
	if {[catch { eval keylset tempKeyedList $retVal }]} {
		return -code error "Cannot update the returnKeyedList"
	}
    }
	if {[info exists tempKeyedList] && $tempKeyedList ne ""} {
	   keylset returnKeyedList $bgp_device $tempKeyedList
	}
	return $returnKeyedList 


}



###
#  Name:    emulation_bgp_route_info
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Display information on advertised and received BGP routes.
###
proc ::sth::Bgp::emulation_bgp_route_info { rklName } {
	::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_info $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	# validate router handle
	if {[info exists ::sth::Bgp::userArgsArray(handle)] && $::sth::Bgp::userArgsArray(handle) ne "all"} {
	set bgpRouterHandle $::sth::Bgp::userArgsArray(handle)
	if {![::sth::Bgp::isBgpRouterHandleValid $bgpRouterHandle]} {
	    return -code error "Error: the bgp router handle $bgpRouterHandle is not valid"
	}
	} else {
	       set all_ports [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]
            foreach port_handle $all_ports {
               if {[::sth::sthCore::IsPortValid $port_handle err]} {
                   set port_host [::sth::sthCore::invoke stc::get $port_handle -affiliationport-sources]
                   foreach host $port_host {
                      if {![::sth::Bgp::isBgpRouterHandleValid $host]} {
                          continue
                      }
                      lappend bgpRouterHandle $host
                   }
               } 
            }
	    
	    
	}
	
	foreach bgp_device $bgpRouterHandle {
	# get required handles
	set bgpRouterConfigHandle [::sth::sthCore::invoke stc::get $bgp_device -children-BgpRouterConfig]
	set bgpRouterResultsHandle [::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -children-bgprouterresults]
	set bgpIpVerValue [::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -IpVersion]

    set unsupportedStats [list ipv4_routes ipv6_routes ipv4_mpls_vpn_count ipv4_mpls_vpn_routes ipv6_mpls_vpn_count ipv6_mpls_vpn_routes]
    
	set retVal {}
	foreach stat {ipv4_count ipv4_routes ipv6_count ipv6_routes ipv4_mpls_vpn_count ipv4_mpls_vpn_routes ipv6_mpls_vpn_count ipv6_mpls_vpn_routes} {
        set statIpVersion [lindex [split $stat _] 0] ;# ipv4 or ipv6
        set statType [lindex [split $stat _] end] ;# count or routes
        
        switch -- $statType {
            count {
                if {![string match -nocase $statIpVersion $bgpIpVerValue] || [lsearch $unsupportedStats $stat] > -1} {
                    set intVal 0
                } else {
                    set stcAttr [string map -nocase {advertised TxAdvertisedRouteCount received RxAdvertisedRouteCount} $::sth::Bgp::userArgsArray(mode)]
                    set intVal 0
                    foreach bgpResultHandle $bgpRouterResultsHandle {
                    	set statValue [::sth::sthCore::invoke stc::get $bgpResultHandle -$stcAttr]
                    	# convert from double to int
                    	if {[scan $statValue %d intVal] != 1} {
                    	    return -code error "Error converting $stcAttr value ($intVal) to an integer"
                    	}
                    }
                }
                lappend retVal $stat $intVal
            }
            routes {
                # not supported yet
                lappend retVal $stat {}
            }
        }
    }
    
	if {[catch { eval keylset tempKeyedList $retVal }]} {
		return -code error "Cannot update the returnKeyedList"
	}
	keylset returnKeyedList $bgp_device $tempKeyedList
	#closure of the new foreach
	}
	if {[llength $bgpRouterHandle] == 1 && $returnKeyedList ne ""} {
	    set Temp_keyed_list [keylget returnKeyedList $bgp_device]    
	}
	if {[info exists Temp_keyed_list]} {
	  keylget Temp_keyed_list
	  foreach key $Temp_keyed_list {
	     keylset returnKeyedList [lindex $key 0] [lindex $key 1]
	  }
	}
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

###
#  Name:    emulation_bgp_route_config_add
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Create one or more routes on the specified router.
###
proc ::sth::Bgp::emulation_bgp_route_config_add { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_config_add $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	# Check if bgp router handle is valid
	if {![info exists ::sth::Bgp::userArgsArray(handle)]} {
        if {![info exists ::sth::Bgp::userArgsArray(route_handle)]} {
        	return -code error "the switch \"-handle\" or \"-route_handle\" is mandatory in add mode"
        }
	} else {
	    set rtrHandle $::sth::Bgp::userArgsArray(handle)
		if {![::sth::Bgp::isBgpRouterHandleValid $rtrHandle]} {
			return -code error "Invalid bgp router handle $rtrHandle"
		}
        # get the bgp router config handle
        set bgpRouterHdl [::sth::sthCore::invoke stc::get $rtrHandle -children-BgpRouterConfig]
        
        # determine IP version of the routes
        set ipVersion $::sth::Bgp::userArgsArray(ip_version)
        # verify that the ip version of the route being added matches the ip version of the router
        set bgpIpVersion [::sth::sthCore::invoke stc::get $bgpRouterHdl -IpVersion]
        set bgpIpVersion [string index $bgpIpVersion end]
	}

    if {[info exists ::sth::Bgp::userArgsArray(route_type)]} {
        set routeType  $::sth::Bgp::userArgsArray(route_type)
    } else {
        set routeType ip
    }
    
    switch -- $routeType {
        ip {
            set stcRouteBlkObj "BgpIpv${ipVersion}RouteConfig"
        }
        vpn {
            set stcRouteBlkObj "BgpIpv${ipVersion}RouteConfig"
        }
        vpls {
            set stcRouteBlkObj "BgpIpv${ipVersion}VplsConfig"
        }
        vplsad {
            set stcRouteBlkObj "BgpVplsAdConfig"
        }
        link_state {
            set stcRouteBlkObj "BgpLsNodeConfig"
        }
        flow_spec {
            set stcRouteBlkObj "BgpFlowSpecConfig"
        }
        srte {
            set stcRouteBlkObj "BgpSrTePolicyConfig"
        }
        evpn_type1 {
            set stcRouteBlkObj "BgpEvpnAdRouteConfig"
        }
        evpn_type2 {
            set stcRouteBlkObj "BgpEvpnMacAdvRouteConfig"
        }
        evpn_type3 {
            set stcRouteBlkObj "BgpEvpnInclusiveMcastRouteConfig"
        }
        evpn_type4 {
            set stcRouteBlkObj "BgpEvpnEthernetSegmentRouteConfig"
        }
        evpn_type5 {
            set stcRouteBlkObj "BgpEvpnIpPrefixRouteConfig"
        }
        default {
            return -code error "unsupported route_type: $routeType"	
        }
    }
        
	if {[info exists ::sth::Bgp::userArgsArray(route_handle)]} {        
        set route_handle $::sth::Bgp::userArgsArray(route_handle)
        set linkHandleList {}
        if {$routeType == "link_state"} {
            processBgpLsConfigSwitches emulation_bgp_route_config $route_handle add returnKeyedList
        }
        if {$routeType == "flow_spec"} {
            processBgpFlowSpecConfigSwitches emulation_bgp_route_config $bgpRouteConfigHandle add returnKeyedList
        }
        if {$routeType == "srte"} {
            processBgpSrTePolicyConfig emulation_bgp_route_config $route_handle add returnKeyedList
        }
    } else {
        # create specified number of route blocks
        set routeHandleList {}
        for {set i 0} {$i < $::sth::Bgp::userArgsArray(max_route_ranges)} {incr i} {
            # create a route block
            set bgpRouteConfigHandle [::sth::sthCore::invoke stc::create $stcRouteBlkObj -under $bgpRouterHdl]
            # configure the route block
            if {[catch {
                # configure the route attributes
                configBgpRoute $bgpRouteConfigHandle $i $ipVersion
                
                # configure the network block attributes
                if {$routeType == "ip" || $routeType == "vpn"} {
                    configBgpRouteNetworkBlock $bgpRouteConfigHandle $i $ipVersion
                }
    
                # configure the vpn route attributes
                configBgpRouteVpn $bgpRouteConfigHandle $i $routeType
                    
                if {$routeType == "vpls"} {
                    configBgpRouteVpls $bgpRouteConfigHandle $i 
                }
                    
                if {$routeType == "vplsad"} {
                    configBgpRouteVplsad $bgpRouteConfigHandle $i
                }
                if {$routeType == "link_state"} {
                    processBgpLsConfigSwitches emulation_bgp_route_config $bgpRouteConfigHandle add returnKeyedList
                }
                if {$routeType == "flow_spec"} {
                    processBgpFlowSpecConfigSwitches emulation_bgp_route_config $bgpRouteConfigHandle add returnKeyedList
                }
                if {$routeType == "srte"} {
                    processBgpSrTePolicyConfig emulation_bgp_route_config $bgpRouteConfigHandle add returnKeyedList
                }
                if {[regexp -nocase "evpn" $routeType] } {
                    processBgpEvpnSwitches emulation_bgp_route_config $bgpRouteConfigHandle add returnKeyedList
                }
                    
            } routeConfigErr]} {
                # if an error occurs while configuring the route block, we need to remove it
                ::sth::sthCore::invoke stc::delete $bgpRouteConfigHandle
                return -code error $routeConfigErr
            }
            
            lappend routeHandleList $bgpRouteConfigHandle
        }
        
        ## begin kludge
        #
        # need to support "-packing_to" option which existed in P1.30. this option should probably not be
        # supported in the future since it is a global setting when it should be a route-based setting
        # according to the HLTAPI spec. we also do not support the "-packing_from" option.
        set bgpGlobalHandle [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-BgpGlobalConfig]
        set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpGlobal add $bgpGlobalHandle 0]
        
        if {[llength $optionValueList]} {
            ::sth::sthCore::invoke stc::config $bgpGlobalHandle $optionValueList
        }
        ## end kludge
        
        if {[catch { keylset returnKeyedList handles $routeHandleList } err]} {
            return -code error "Cannot update the returnKeyedList. $err"
        }
    }

    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply } err]} {
	    return -code error "Error applying config: $err"
        }
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::Bgp::emulation_bgp_route_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_config_modify $rklName"
	
	upvar 1 $rklName returnKeyedList
	set link_handle ""
    set route_handle ""
    
	if {[info exists ::sth::Bgp::userArgsArray(link_handle)] } {
        set link_handle $::sth::Bgp::userArgsArray(link_handle)
    } elseif {[info exists ::sth::Bgp::userArgsArray(route_handle)]} {
        set route_handle $::sth::Bgp::userArgsArray(route_handle)
	} else {
        return -code error "the switch \"-route_handle\" or \"-link_handle\" is mandatory in modify mode"
    }


    # determine IP version of the routes
    if {[info exists ::sth::Bgp::userArgsArray(ip_version)]} {
        set ipVersion  $::sth::Bgp::userArgsArray(ip_version)
    } else {
        set ipVersion 4
    }

    if {[info exists ::sth::Bgp::userArgsArray(route_type)]} {
        set routeType  $::sth::Bgp::userArgsArray(route_type)
    } else {
        set routeType ip
    }

	if {$link_handle != ""} {        
        if {$routeType == "link_state"} {
            processBgpLsConfigSwitches emulation_bgp_route_config $link_handle modify returnKeyedList
        }
    } else {
        # create specified number of route blocks
        set routeHandleList {}
        for {set i 0} {$i < $::sth::Bgp::userArgsArray(max_route_ranges)} {incr i} {
            # create a route block
            #set bgpRouteConfigHandle [::sth::sthCore::invoke stc::get $bgpRouterHdl -children-$stcRouteBlkObj]
            set bgpRouteConfigHandle $route_handle
            
            # configure the route block
            if {[catch {
                # configure the route attributes
                configBgpRoute $bgpRouteConfigHandle $i $ipVersion
                
                # configure the network block attributes
                if {$routeType == "ip" || $routeType == "vpn"} {
                    configBgpRouteNetworkBlock $bgpRouteConfigHandle $i $ipVersion
                }
    
                # configure the vpn route attributes
                configBgpRouteVpn $bgpRouteConfigHandle $i $routeType
                    
                if {$routeType == "vpls"} {
                    configBgpRouteVpls $bgpRouteConfigHandle $i 
                }
                    
                if {$routeType == "vplsad"} {
                    configBgpRouteVplsad $bgpRouteConfigHandle $i
                }
                if {$routeType == "link_state"} {
                    processBgpLsConfigSwitches emulation_bgp_route_config $bgpRouteConfigHandle modify returnKeyedList
                }
                if {$routeType == "flow_spec"} {
                    processBgpFlowSpecConfigSwitches emulation_bgp_route_config $bgpRouteConfigHandle modify returnKeyedList
                }
                if {$routeType == "srte"} {
                    processBgpSrTePolicyConfig emulation_bgp_route_config $bgpRouteConfigHandle modify returnKeyedList
                }                    
                if {[regexp -nocase "evpn" $routeType] } {
                    processBgpEvpnSwitches emulation_bgp_route_config $bgpRouteConfigHandle modify returnKeyedList
                }
            } routeConfigErr]} {
                # if an error occurs while configuring the route block, we need to remove it
                ::sth::sthCore::invoke stc::delete $bgpRouteConfigHandle
                return -code error $routeConfigErr
            }
            
            lappend routeHandleList $bgpRouteConfigHandle
        }
        
        if {[catch { keylset returnKeyedList handles $routeHandleList } err]} {
            return -code error "Cannot update the returnKeyedList. $err"
        }
    }

    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply } err]} {
    	    return -code error "Error applying config: $err"
        }
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


###
#  Name:    emulation_bgp_route_config_remove
#  Inputs:  rklName - returnKeyedList name
#  Globals: none
#  Outputs: 1 | 0 - pass | fail (yes, it is reversed)
#  Description: Deletes one or more routes on the specified router.
###
proc ::sth::Bgp::emulation_bgp_route_config_remove { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_config_remove $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	if {[info exists ::sth::Bgp::userArgsArray(route_handle)]} {
        set handleList $::sth::Bgp::userArgsArray(route_handle)
	} elseif {[info exists ::sth::Bgp::userArgsArray(handle)]} {
        lappend handleList $::sth::Bgp::userArgsArray(handle)
	} else {
        return -code error "the switch \"-route_handle\" or \"-handle\"is mandatory in remove mode"
    }
    
    ::sth::sthCore::invoke stc::perform deletecommand -configlist "$handleList"
                        
	#::sth::sthCore::invoke ::stc::sleep 15
	
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply } err]} {
            return -code error "Error applying config: $err"
        }
    }
	
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}

proc ::sth::Bgp::emulation_bgp_route_config_withdraw { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_config_withdraw  $rklName"
    
    upvar 1 $rklName returnKeyedList
    
    if {![info exists ::sth::Bgp::userArgsArray(route_handle)]} {
	return -code error "the switch \"-route_handle\" is mandatory in withdraw mode"
    }
    
    set rtrHandle $::sth::Bgp::userArgsArray(route_handle)
    ::sth::sthCore::invoke stc::perform  BgpWithdrawRoute -RouteList $rtrHandle
    
    if {!$::sth::sthCore::optimization} {
	if {[catch {::sth::sthCore::doStcApply } err]} {
	    return -code error "Error applying config: $err"
	}
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



proc ::sth::Bgp::emulation_bgp_route_generator_create { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Bgp::userArgsArray


    set _OrigHltCmdName "emulation_bgp_route_generator"
    set _hltCmdName "emulation_bgp_route_generator_create"

    ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    
    #Validate the value of bgp handle
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set bgpRouterHandle $userArgsArray(handle)
    }


	#get the type for configuration
	set routeType "ipv4"
	if {[info exists userArgsArray(route_type)]} {
		set routeType $userArgsArray(route_type)
	}

	if {[llength $bgpRouterHandle] == 1 } {		
		#get IP version for this router
		set ipVersion 4
		set childrenIpInfo [::sth::sthCore::invoke stc::get $bgpRouterHandle -children]
		if {[regexp -nocase {ipv6} $childrenIpInfo]} {
				set ipVersion 6        
		}
	}
 
    set bgpRouteGenParamsHandle [::sth::sthCore::invoke stc::create BgpRouteGenParams  -under project1 -SelectedRouterRelation-targets $bgpRouterHandle]

    set priorityList [::sth::Bgp::processSwitches emulation_bgp_route_generator ::sth::Bgp:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $bgpRouteGenParamsHandle $routeType]
            
        if {$cmdPassed == $FAILURE} {
            break
        }
    }

    ::sth::sthCore::invoke stc::perform RouteGenApply -GenParams $bgpRouteGenParamsHandle

	set ip_block_handle {}
	if {[llength $bgpRouterHandle] == 1 } {
		# return all Ipv4NetworkBlock
		set sub_object_iproute ""
		set sub_object_block ""
		append  sub_object_iproute  "BgpIpv" "$ipVersion" "RouteConfig"
		append  sub_object_block  "Ipv" "$ipVersion" "NetworkBlock"
		set BgpRouterConfigString [::sth::sthCore::invoke stc::get $bgpRouterHandle -children-BgpRouterConfig]
		
		set BgpRouterConfigList [split $BgpRouterConfigString " "]
		foreach BgpRouterConfigHandle $BgpRouterConfigList {
			set BgpIpRouteConfigChildrenString [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children]
			if {[regexp  {bgpipv[4|6]routeconfig} $BgpIpRouteConfigChildrenString]} {
				set BgpIpRoutesString [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children-$sub_object_iproute]
				set BgpIpRoutesList [split $BgpIpRoutesString " "]
				foreach BgpIpRoutesHandle $BgpIpRoutesList {
					set BgpblockHandle [::sth::sthCore::invoke stc::get $BgpIpRoutesHandle -children-$sub_object_block]
					lappend  ip_block_handle  $BgpblockHandle
				}
			}
		}
	} else {
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className BgpRouterConfig -rootlist $bgpRouterHandle]
		set bgpHndList $rtn(-ObjectList)
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className bgpipv4routeconfig -rootlist $bgpHndList]
		set bgpIpv4HndList $rtn(-ObjectList)
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className bgpipv6routeconfig -rootlist $bgpHndList]
		set bgpIpv6HndList $rtn(-ObjectList)
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv4NetworkBlock -rootlist $bgpIpv4HndList]
		set ipv4HndList $rtn(-ObjectList)
		array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $bgpIpv6HndList]
		set ipv6HndList $rtn(-ObjectList)
		if {[llength $ipv4HndList]} {
			lappend ip_block_handle $ipv4HndList
		}
		if {[llength $ipv6HndList]} {
			lappend ip_block_handle $ipv6HndList
		}
	}

    keylset returnKeyedList ip_block_handle  $ip_block_handle
    keylset returnKeyedList elem_handle  $bgpRouteGenParamsHandle
    keylset returnKeyedList status  $SUCCESS
    
    return $returnKeyedList       
}


proc ::sth::Bgp::emulation_bgp_route_generator_modify { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Bgp::userArgsArray


    set _OrigHltCmdName "emulation_bgp_route_generator"
    set _hltCmdName "emulation_bgp_route_generator_modify"
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    upvar 1 $returnKeyedListVarName returnKeyedList

    
    #Validate the value of bgp handle
    if {![info exists userArgsArray(elem_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set bgpRouteGenParamsHandle $userArgsArray(elem_handle)
    }

    #get the type for configuration
    set routeType "ipv4"
    if {[info exists userArgsArray(route_type)]} {
        set routeType $userArgsArray(route_type)
    }
 
    set bgpRouterHandle [::sth::sthCore::invoke stc::get $bgpRouteGenParamsHandle -selectedrouterrelation-Targets]
    #get IP version for this router
    set ipVersion 4
    set childrenIpInfo [::sth::sthCore::invoke stc::get $bgpRouterHandle -children]
    if {[regexp -nocase {ipv6} $childrenIpInfo]} {
        set ipVersion 6        
    }


    set priorityList [::sth::Bgp::processSwitches emulation_bgp_route_generator ::sth::Bgp:: returnKeyedList modify funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $bgpRouteGenParamsHandle $routeType]
            
        if {$cmdPassed == $FAILURE} {
            break
        }
    }

    ::sth::sthCore::invoke stc::perform RouteGenApply -GenParams $bgpRouteGenParamsHandle

    # return all Ipv4NetworkBlock
    set ip_block_handle {}
    set sub_object_iproute ""
    set sub_object_block ""
    append  sub_object_iproute  "BgpIpv" "$ipVersion" "RouteConfig"
    append  sub_object_block  "Ipv" "$ipVersion" "NetworkBlock"
    set BgpRouterConfigString [::sth::sthCore::invoke stc::get $bgpRouterHandle -children-BgpRouterConfig]
    
    set BgpRouterConfigList [split $BgpRouterConfigString " "]
    foreach BgpRouterConfigHandle $BgpRouterConfigList {
        set BgpIpRouteConfigChildrenString [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children]
        if {[regexp  {bgpipv[4|6]routeconfig} $BgpIpRouteConfigChildrenString]} {
            set BgpIpRoutesString [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children-$sub_object_iproute]
            set BgpIpRoutesList [split $BgpIpRoutesString " "]
            foreach BgpIpRoutesHandle $BgpIpRoutesList {
                set BgpblockHandle [::sth::sthCore::invoke stc::get $BgpIpRoutesHandle -children-$sub_object_block]
                lappend  ip_block_handle  $BgpblockHandle
            }
        }
    }

    keylset returnKeyedList ip_block_handle  $ip_block_handle
    keylset returnKeyedList elem_handle  $bgpRouteGenParamsHandle
    keylset returnKeyedList status  $SUCCESS
    
    return $returnKeyedList       
}


proc ::sth::Bgp::emulation_bgp_route_generator_delete { returnKeyedListVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Bgp::userArgsArray


    set _OrigHltCmdName "emulation_bgp_route_generator"
    set _hltCmdName "emulation_bgp_route_generator_delete"
    ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    upvar 1 $returnKeyedListVarName returnKeyedList

    set routeType "ipv4|ipv6|link_state"
    if {[info exists userArgsArray(route_type)]} {
        set routeType $userArgsArray(route_type)
    }

   if {(![info exists userArgsArray(elem_handle)] || $userArgsArray(elem_handle) == "")} {
          ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        return $returnKeyedList        
    } else {
        set msg ""
        set bgpRouteHandles $userArgsArray(elem_handle)
        foreach bgpHandle $bgpRouteHandles {
            set BgprouterHandle [::sth::sthCore::invoke stc::get $bgpHandle -selectedrouterrelation-Targets]
            
            set BgpRouterConfigString [::sth::sthCore::invoke stc::get $BgprouterHandle -children-BgpRouterConfig]
    
            set BgpRouterConfigList [split $BgpRouterConfigString " "]
            foreach BgpRouterConfigHandle $BgpRouterConfigList {
                if {[regexp -nocase {ipv4} $routeType]} {
                    set BgpIpRouteConfigList [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children-BgpIpv4RouteConfig]
                    if {$BgpIpRouteConfigList != ""} {
                        ::sth::sthCore::invoke stc::perform delete -ConfigList "$BgpIpRouteConfigList"
                    }
                }
                
                if {[regexp -nocase {ipv6} $routeType]} {
                    set BgpIpRouteConfigList [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children-BgpIpv6RouteConfig]
                    if {$BgpIpRouteConfigList != ""} {
                        ::sth::sthCore::invoke stc::perform delete -ConfigList "$BgpIpRouteConfigList"
                    }
                }
                
                if {[regexp -nocase {link_state} $routeType]} {
                    set BgpLsNodeConfigList [::sth::sthCore::invoke stc::get $BgpRouterConfigHandle -children-BgpLsNodeConfig]
                    if {$BgpLsNodeConfigList != ""} {
                        ::sth::sthCore::invoke stc::perform delete -ConfigList "$BgpLsNodeConfigList"
                    }
                }
                
            }
            ::sth::sthCore::invoke stc::delete $bgpHandle
        }
    }

    keylset returnKeyedList status  $SUCCESS
    return $returnKeyedList
    
}
proc ::sth::Bgp::emulation_bgp_custom_attribute_config_add { returnKeyedListVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::sortedSwitchPriorityList

    set _OrigHltCmdName "emulation_bgp_custom_attribute_config"
    set _hltCmdName "emulation_bgp_custom_attribute_config_add"

    ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList

    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set bgpRouterConfigHandle $userArgsArray(handle)
    }
    
    if {[info exists userArgsArray(type_selector)]} {
        set cstmAttrType  $userArgsArray(type_selector)
    } else {
        set cstmAttrType custom
    }
  
    set stcObjList ""
    set asPathSegmentObj ""
    set lsCustomTlvObj ""
    set mpNlriObj ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_custom_attribute_config $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            set stcObjtmp [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_custom_attribute_config $switchname stcobj]
            if {[string match -nocase $stcObjtmp "_none_"]} { continue }
            if {[lsearch $stcObjList $stcObjtmp] == -1} {
                lappend stcObjList $stcObjtmp
            }
            if {$stcObjtmp=="BgpAsPathSegment"} {
                lappend asPathSegmentObj $switchname
            }
            if {$stcObjtmp=="BgpLsCustomTlv"} {
                lappend lsCustomTlvObj $switchname
            }
            if {$stcObjtmp=="BgpMpNlri"} {
                lappend mpNlriObj $switchname
            }
        }
    }
            
    set bgpCustomAttributeHandle [::sth::sthCore::invoke stc::create BgpCustomAttribute -under $bgpRouterConfigHandle]
    set bgpMpReachUnReachAttrHandle [::sth::sthCore::invoke stc::get $bgpCustomAttributeHandle -children-BgpMpReachUnReachAttr]
    set optionValueList [getStcOptionValueList emulation_bgp_custom_attribute_config configBgpCstmAttr add $bgpCustomAttributeHandle 0]
    if {[llength $optionValueList]} {
	::sth::sthCore::invoke stc::config $bgpCustomAttributeHandle $optionValueList
    }
    keylset returnKeyedList handle $bgpCustomAttributeHandle
    keylset returnKeyedList BgpMpReachUnReach_Handle $bgpMpReachUnReachAttrHandle
    if {$cstmAttrType=="mp_reach_unreach_nlri"} {	
        set optionValueList [getStcOptionValueList emulation_bgp_custom_attribute_config configBgpMpReachUnReachAttr add $bgpMpReachUnReachAttrHandle 0]
        if {[llength $optionValueList]} {
            ::sth::sthCore::invoke stc::config $bgpMpReachUnReachAttrHandle $optionValueList
        }       
    }

    foreach stcObj $stcObjList {
	if {$stcObj=="BgpAsPathSegment"} {
	    processBgpCstmAttrSwitches emulation_bgp_custom_attribute_config $asPathSegmentObj BgpAsPathSegment $bgpCustomAttributeHandle add returnKeyedList
	}

	if {$stcObj=="BgpLsCustomTlv"} {
	    processBgpCstmAttrSwitches emulation_bgp_custom_attribute_config $lsCustomTlvObj BgpLsCustomTlv $bgpCustomAttributeHandle add returnKeyedList
	}
	if {$stcObj=="BgpMpNlri"} {
	    processBgpCstmAttrSwitches emulation_bgp_custom_attribute_config $mpNlriObj BgpMpNlri $bgpMpReachUnReachAttrHandle add returnKeyedList
	}	
    }
    if {!$::sth::sthCore::optimization} {
	if {[catch {::sth::sthCore::doStcApply } err]} {
	    return -code error "Error applying config: $err"
	}
    }

    keylset returnKeyedList status $SUCCESS   
    return $returnKeyedList       
}

proc ::sth::Bgp::emulation_bgp_custom_attribute_config_delete { returnKeyedListVarName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_custom_attribute_config_delete $returnKeyedListVarName"
	
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {[info exists ::sth::Bgp::userArgsArray(custom_handles)]} {
    set handleList $::sth::Bgp::userArgsArray(custom_handles)
    } else {
    return -code error "the switch \"-custom_handles\" is mandatory in delete mode"
    }
    
    ::sth::sthCore::invoke stc::perform deletecommand -configlist "$handleList"
	
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply } err]} {
            return -code error "Error applying config: $err"
        }
    }
	
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}
proc ::sth::Bgp::processBgpCstmAttrSwitches {userfunName objList objHandleName parentHandle mode returnKeyedListVarName} {
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList

    #set handle [regsub -all {\d+} $objHandleName ""]
    
    if {[llength $objList]} {
        set attrCount [llength $userArgsArray([lindex $objList 0])]
        foreach objTmp $objList {
            if {[llength $userArgsArray($objTmp)]==$attrCount} {
                continue
            } else {
               ::sth::sthCore::processError returnKeyedList "Error: Argument $objList count is different" {}
                return -code error $returnKeyedList
            }
        }
    }  
    set objHandleList ""
    for {set index 0} {$index < $attrCount} {incr index} {
        set optionValueList ""
        foreach item $::sth::Bgp::sortedSwitchPriorityList {
            foreach {priority opt} $item {
                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $opt mode] "_none_"]} { continue }
                set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $opt $mode]
                if {[string match -nocase $func config$objHandleName]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Bgp:: $userfunName $opt [lindex $::sth::Bgp::userArgsArray($opt) $index]} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr [lindex $::sth::Bgp::userArgsArray($opt) $index]
                    }                         
                }
            }
        }
        set objHandle [::sth::sthCore::invoke stc::create $objHandleName -under $parentHandle]
        if {[llength $optionValueList]} {
            ::sth::sthCore::invoke stc::config $objHandle $optionValueList
        }
        lappend objHandleList $objHandle
    }
    keylset returnKeyedList [set objHandleName]_Handles $objHandleList
    return $returnKeyedList
}

proc ::sth::Bgp::processSwitches {hltapiCommand myNameSpace returnKeyValue mode switchArrayList} {
    
    upvar $returnKeyValue returnKeyedList
    upvar $switchArrayList functionswitcharrayList
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    array set userArgsArray [array get $myNameSpace\userArgsArray]
    array set procfuncarray [array get $myNameSpace$hltapiCommand\_procfunc]
    array set priorityarray [array get $myNameSpace$hltapiCommand\_priority]
    if {[string equal $mode create]} {
        catch {unset userArgsArray(mandatory_args)}
        catch {unset userArgsArray(optional_args)}
        set switchNameList [array names userArgsArray]
    } elseif {[string equal $mode modify]} {
        set tmpList $userArgsArray(optional_args)
        set switchNameList [list]
        foreach {switchName switchValue} $tmpList {
            set switchName [string range $switchName 1 end]
            lappend switchNameList $switchName
        }
    } else {
        return $FAILURE
    }
    set priorityList [list]
    array set funcSwitchArray [list]
    foreach switchName $switchNameList {
        set functionName $procfuncarray($switchName)
        if {($functionName != "" && ![string equal $functionName "_none_"])} {
            if {$userArgsArray($switchName)!=""} {
                lappend funcSwitchArray($functionName) $switchName
                if {[llength $funcSwitchArray($functionName)] == 1} {
                    lappend priorityList [list $functionName $priorityarray($switchName)]
                }
            }
        }
    }
    
    set priorityList [lsort -integer -index 1 $priorityList]
    set functionswitcharrayList [array get funcSwitchArray]
    
    return $priorityList
}

proc ::sth::Bgp::emulation_bgp_route_gen_ip {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    set ipRouteGenParamsHnd ""
    

    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {ipv4} $routeType]} {
            set ipRouteGenParamsHnd [::sth::sthCore::invoke stc::create Ipv4RouteGenParams -under $bgpRouterGenHandle]
        } elseif {[regexp -nocase {ipv6} $routeType]} {
            set ipRouteGenParamsHnd [::sth::sthCore::invoke stc::create Ipv6RouteGenParams -under $bgpRouterGenHandle]
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {ipv4} $routeType]} {
            set ipRouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv4RouteGenParams]
        } elseif {[regexp -nocase {ipv6} $routeType]} {
            set ipRouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv6RouteGenParams]
        }
    }
      
    if {$ipRouteGenParamsHnd != ""} {
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $ipRouteGenParamsHnd $switchValueList
        }
    }
    
    return $SUCCESS
}


proc ::sth::Bgp::emulation_bgp_route_gen_attr {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    set bgpRouteGenHnd ""
    
    
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {ipv4} $routeType]} {
            set ipv4RouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv4RouteGenParams]
            set bgpRouteGenHnd [::sth::sthCore::invoke stc::create BgpRouteGenRouteAttrParams -under $ipv4RouteGenParamsHnd]
        } elseif {[regexp -nocase {ipv6} $routeType]} {
            set ipv6RouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv6RouteGenParams]
            set bgpRouteGenHnd [::sth::sthCore::invoke stc::create BgpRouteGenRouteAttrParams -under $ipv6RouteGenParamsHnd]
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {ipv4} $routeType]} {
            set ipv4RouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv4RouteGenParams]
            set bgpRouteGenHnd [::sth::sthCore::invoke stc::get $ipv4RouteGenParamsHnd -children-BgpRouteGenRouteAttrParams]
        } elseif {[regexp -nocase {ipv6} $routeType]} {
            set ipv6RouteGenParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-Ipv6RouteGenParams]
            set bgpRouteGenHnd [::sth::sthCore::invoke stc::get $ipv6RouteGenParamsHnd -children-BgpRouteGenRouteAttrParams]
        }
    }


    if {$bgpRouteGenHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $bgpRouteGenHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        ::sth::sthCore::invoke stc::config $bgpRouterGenHandle -EnableLinkState true
    }
    
    if {[regexp -nocase {link_state} $routeType]} {
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $bgpRouterGenHandle $switchValueList
        }
    }
    
    return $SUCCESS
}


proc ::sth::Bgp::emulation_bgp_route_gen_ls_b_full_mesh {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    set fullMeshHnd ""

    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set backboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsBackboneTopologyGenParams]
            if {$backboneTopoHnd == ""} {
                set backboneTopoHnd [::sth::sthCore::invoke stc::create BgpLsBackboneTopologyGenParams -under $bgpRouterGenHandle]
                set fullMeshHnd [::sth::sthCore::invoke stc::get $backboneTopoHnd -children-FullMeshTopologyGenParams]
                if {$fullMeshHnd == ""} {
                    set fullMeshHnd [::sth::sthCore::invoke stc::create FullMeshTopologyGenParams -under $backboneTopoHnd]
                }
                ::sth::sthCore::invoke stc::config $bgpRouterGenHandle -BackboneAreaTopologyGenParams-targets $fullMeshHnd
            }
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set backboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsBackboneTopologyGenParams]
            set fullMeshHnd [::sth::sthCore::invoke stc::get $backboneTopoHnd -children-FullMeshTopologyGenParams]
        }
    }

    if {$fullMeshHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $fullMeshHnd $switchValueList
        }
    }
    
    return $SUCCESS
}


proc ::sth::Bgp::emulation_bgp_route_gen_ls_nb_tree_topo {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    set treeTopoHnd ""
     
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set nonbackboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsNoneBackboneTopologyGenParams]
            if {$nonbackboneTopoHnd == ""} {
                set nonbackboneTopoHnd [::sth::sthCore::invoke stc::create BgpLsNoneBackboneTopologyGenParams -under $bgpRouterGenHandle]
                set treeTopoHnd [::sth::sthCore::invoke stc::get $nonbackboneTopoHnd -children-TreeTopologyGenParams]
                if {$treeTopoHnd == ""} {
                    set treeTopoHnd [::sth::sthCore::invoke stc::create TreeTopologyGenParams -under $nonbackboneTopoHnd]
                }
            }
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set nonbackboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsNoneBackboneTopologyGenParams]
            set treeTopoHnd [::sth::sthCore::invoke stc::get $nonbackboneTopoHnd -children-TreeTopologyGenParams]
        }
    }

    if {$treeTopoHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $treeTopoHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls_b_grid_topo {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    set treeTopoHnd ""
     
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set backboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsBackboneTopologyGenParams]
            if {$backboneTopoHnd == ""} {
                set backboneTopoHnd [::sth::sthCore::invoke stc::create BgpLsBackboneTopologyGenParams -under $bgpRouterGenHandle]
            }
            set treeTopoHnd [::sth::sthCore::invoke stc::create GridTopologyGenParams -under $backboneTopoHnd]
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set backboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsBackboneTopologyGenParams]
            set treeTopoHnd [::sth::sthCore::invoke stc::get $backboneTopoHnd -children-GridTopologyGenParams]
        }
    }

    if {$treeTopoHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $treeTopoHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls_nb_grid_topo {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    set treeTopoHnd ""
     
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set nonbackboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsNoneBackboneTopologyGenParams]
            if {$nonbackboneTopoHnd == ""} {
                set nonbackboneTopoHnd [::sth::sthCore::invoke stc::create BgpLsNoneBackboneTopologyGenParams -under $bgpRouterGenHandle]
            }
            set treeTopoHnd [::sth::sthCore::invoke stc::create GridTopologyGenParams -under $nonbackboneTopoHnd]
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set nonbackboneTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-BgpLsNoneBackboneTopologyGenParams]
            set treeTopoHnd [::sth::sthCore::invoke stc::get $nonbackboneTopoHnd -children-GridTopologyGenParams]
        }
    }

    if {$treeTopoHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $treeTopoHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls_full_mesh {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {
    #need to check the STC version, after STC 4.56, the STC will FullMeshTopologyGenParams under the  BgpRouteGenParams  will not be used, only the
    #FullMeshTopologyGenParams under  BgpLsBackboneTopologyGenParams which under BgpRouteGenParams will be used. so use the function 'emulation_bgp_route_gen_ls_b_full_mesh'
    set stc_version [stc::get system1 -version]
    if {$stc_version >= 4.56} {
        return [emulation_bgp_route_gen_ls_b_full_mesh $switchList $returnInfoVarName $_hltCmdName $_switchName $bgpRouterGenHandle $routeType]
    }
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    set fullMeshHnd ""

    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set fullMeshHnd [::sth::sthCore::invoke stc::create FullMeshTopologyGenParams -under $bgpRouterGenHandle]
            ::sth::sthCore::invoke stc::config $bgpRouterGenHandle -BackboneAreaTopologyGenParams-targets $fullMeshHnd
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set fullMeshHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-FullMeshTopologyGenParams]
        }
    }

    if {$fullMeshHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $fullMeshHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls_tree_topo {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    #need to check the STC version, after STC 4.56, the STC will TreeTopologyGenParams under the  BgpRouteGenParams  will not be used, only the
    #TreeTopologyGenParams under  BgpLsNonBackboneTopologyGenParams which under BgpRouteGenParams will be used. so use the function 'emulation_bgp_route_gen_ls_b_full_mesh'
    set stc_version [stc::get system1 -version]
    if {$stc_version >= 4.56} {
        return [emulation_bgp_route_gen_ls_nb_tree_topo $switchList $returnInfoVarName $_hltCmdName $_switchName $bgpRouterGenHandle $routeType]
    }

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    set treeTopoHnd ""
     
    if {[regexp -nocase {create} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set treeTopoHnd [::sth::sthCore::invoke stc::create TreeTopologyGenParams -under $bgpRouterGenHandle]
        }
    } elseif {[regexp -nocase {modify} $userArgsArray(mode)]} {
        if {[regexp -nocase {link_state} $routeType]} {
            set treeTopoHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-TreeTopologyGenParams]
        }
    }

    if {$treeTopoHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $treeTopoHnd $switchValueList
        }
    }
    
    return $SUCCESS
}

proc ::sth::Bgp::emulation_bgp_route_gen_ls_teparams {switchList returnInfoVarName _hltCmdName _switchName bgpRouterGenHandle routeType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::Bgp::userArgsArray
    variable ::sth::Bgp::emulation_bgp_route_generator_stcobj
    variable ::sth::Bgp::emulation_bgp_route_generator_stcattr    
    
    set teParamsHnd ""
     
    if {[regexp -nocase {link_state} $routeType]} {
        set teParamsHnd [::sth::sthCore::invoke stc::get $bgpRouterGenHandle -children-TeParams]
    } 

    if {$teParamsHnd != ""} {    
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_bgp_route_generator_stcattr($switchName)
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
    
        if {[info exists switchValueList]} {
            ::sth::sthCore::invoke stc::config $teParamsHnd $switchValueList
        }
    }

    return $SUCCESS
}



proc ::sth::Bgp::processBgpEvpnSwitches {userfunName handleList mode retKeyedList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $retKeyedList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configBgpEvpnType1 {
                   configBgpEvpnType1 $userfunName $deviceHandle $mode
                }
                configBgpEvpnType2 {
                   configBgpEvpnType2 $userfunName $deviceHandle $mode
                }
                configBgpEvpnType2MacAddr {
                    if {$mode == "add"} {
                        set macBlockHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-MacBlock]
                        if {[string length $macBlockHnd] == 0} {
                            set macBlockHnd [::sth::sthCore::invoke stc::create MacBlock -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set macBlockHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-MacBlock]
                    }
                    if {[string length $macBlockHnd] != 0} {
                        configBgpEvpnType2MacAddr $userfunName $macBlockHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No MacBlock object under BgpEvpnMacAdvRouteConfig(evpn_type2)" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpEvpnType3 {
                   configBgpEvpnType3 $userfunName $deviceHandle $mode
                }
                configBgpEvpnType4 {
                   configBgpEvpnType4 $userfunName $deviceHandle $mode
                }
                configBgpEvpnType5 {
                   configBgpEvpnType5 $userfunName $deviceHandle $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList
                }
            }
        }
    }
    keylset returnKeyedList handles $handleList
    return $returnKeyedList
}

proc ::sth::Bgp::processBgpLsConfigSwitches {userfunName handleList mode retKeyedList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $retKeyedList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configBgpLsNode {
                    configBgpLsNode $userfunName $deviceHandle $mode
                }
                configBgpLsLocalNodeDesc {
                    set bgpLsLocalNodeDescHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsLocalNodeDescriptor]
                    if {[string length $bgpLsLocalNodeDescHnd] != 0} {
                        configBgpLsLocalNodeDesc $userfunName $bgpLsLocalNodeDescHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsLocalNodeDescriptor object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsNodeAttr {
                    set bgpLsNodeAttrHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsNodeAttribute]
                    if {[string length $bgpLsNodeAttrHnd] != 0} {
                        configBgpLsNodeAttr $userfunName $bgpLsNodeAttrHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsNodeAttribute object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsRemoteNodeDesc {
                    if {$mode == "add"} {
                        set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsLinkConfig]
                        if {[string length $bgpLsLinkConfigHnd] == 0} {
                            set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::create BgpLsLinkConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsLinkConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList link_handle $bgpLsLinkConfigHnd
                    set bgpLsRemoteNodeDescHnd [::sth::sthCore::invoke stc::get $bgpLsLinkConfigHnd -children-BgpLsRemoteNodeDescriptor]
                    if {[string length $bgpLsRemoteNodeDescHnd] != 0} {
                        configBgpLsRemoteNodeDesc $userfunName $bgpLsRemoteNodeDescHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsRemoteNodeDescriptor object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsLinkAttr {
                    if {$mode == "add"} {
                        set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsLinkConfig]
                        if {[string length $bgpLsLinkConfigHnd] == 0} {
                            set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::create BgpLsLinkConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsLinkConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList link_handle $bgpLsLinkConfigHnd
                    set bgpLsLinkAttrHnd [::sth::sthCore::invoke stc::get $bgpLsLinkConfigHnd -children-BgpLsLinkAttribute]
                    if {[string length $bgpLsLinkAttrHnd] != 0} {
                        configBgpLsLinkAttr $userfunName $bgpLsLinkAttrHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsLinkAttribute object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsLinkAttrTeParams {
                    if {$mode == "add"} {
                        set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsLinkConfig]
                        if {[string length $bgpLsLinkConfigHnd] == 0} {
                            set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::create BgpLsLinkConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsLinkConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList link_handle $bgpLsLinkConfigHnd
                    set bgpLsLinkAttrHnd [::sth::sthCore::invoke stc::get $bgpLsLinkConfigHnd -children-BgpLsLinkAttribute]
                    set teParamsHnd [::sth::sthCore::invoke stc::get $bgpLsLinkAttrHnd -children-TeParams ]
                    if {[string length $teParamsHnd] != 0} {
                        configBgpLsLinkAttrTeParams $userfunName $teParamsHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No TeParams under BgpLsLinkAttribute object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsLinkDesc {
                    if {$mode == "add"} {
                        set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsLinkConfig]
                        if {[string length $bgpLsLinkConfigHnd] == 0} {
                            set bgpLsLinkConfigHnd [::sth::sthCore::invoke stc::create BgpLsLinkConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsLinkConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList link_handle $bgpLsLinkConfigHnd
                    set bgpLsLinkDescHnd [::sth::sthCore::invoke stc::get $bgpLsLinkConfigHnd -children-BgpLsLinkDescriptor]
                    if {[string length $bgpLsLinkDescHnd] != 0} {
                        configBgpLsLinkDesc $userfunName $bgpLsLinkDescHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsLinkDescriptor object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsPrefixAttr {
                    if {$mode == "add"} {
                        set bgpLsIpv4PrefixConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsIpv4PrefixConfig]
                        if {[string length $bgpLsIpv4PrefixConfigHnd] == 0} {
                            set bgpLsIpv4PrefixConfigHnd [::sth::sthCore::invoke stc::create BgpLsIpv4PrefixConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsIpv4PrefixConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList ipv4_prefix_handle $bgpLsIpv4PrefixConfigHnd
                    set bgpLsPrefixAttrHnd [::sth::sthCore::invoke stc::get $bgpLsIpv4PrefixConfigHnd -children-BgpLsPrefixAttribute]
                    if {[string length $bgpLsPrefixAttrHnd] != 0} {
                        configBgpLsPrefixAttr $userfunName $bgpLsPrefixAttrHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsPrefixAttribute object" {}
                        return -code error $returnKeyedList                        
                    }
                }
                configBgpLsPrefixDesc {
                    if {$mode == "add"} {
                        set bgpLsIpv4PrefixConfigHnd [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpLsIpv4PrefixConfig]
                        if {[string length $bgpLsIpv4PrefixConfigHnd] == 0} {
                            set bgpLsIpv4PrefixConfigHnd [::sth::sthCore::invoke stc::create BgpLsIpv4PrefixConfig -under $deviceHandle]
                        }
                    } elseif { $mode == "modify"} {
                        set bgpLsIpv4PrefixConfigHnd $deviceHandle
                    }
                    keylset returnKeyedList ipv4_prefix_handle $bgpLsIpv4PrefixConfigHnd
                    set bgpLsPrefixDescHnd [::sth::sthCore::invoke stc::get $bgpLsIpv4PrefixConfigHnd -children-BgpLsPrefixDescriptor]
                    if {[string length $bgpLsPrefixDescHnd] != 0} {
                        configBgpLsPrefixDesc $userfunName $bgpLsPrefixDescHnd $mode
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Error in $procName: No BgpLsPrefixDescriptor object" {}
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
    keylset returnKeyedList handles $handleList
    return $returnKeyedList
}



proc ::sth::Bgp::configBgpEvpnType1 { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType1 $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpEvpnType2 { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType2 $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpEvpnType2MacAddr { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType2MacAddr $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpEvpnType3 { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType3 $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpEvpnType4 { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType4 $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpEvpnType5 { userfunName bgpHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpEvpnType5 $mode $bgpHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsNode { userfunName bgpLsNodeHandle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsNode $mode $bgpLsNodeHandle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpLsNodeHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsLocalNodeDesc { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsLocalNodeDesc $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsRemoteNodeDesc { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsRemoteNodeDesc $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsNodeAttr { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsNodeAttr $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsLinkAttr { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsLinkAttr $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsLinkAttrTeParams { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsLinkAttrTeParams $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpLsLinkDesc { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsLinkDesc $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsPrefixAttr { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsPrefixAttr $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configBgpLsPrefixDesc { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpLsPrefixDesc $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}



proc ::sth::Bgp::configBgpRoute {bgpRouteConfigHandle routeIdx ipVersion} {    
    set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpRoute add $bgpRouteConfigHandle $routeIdx]
    
    ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle $optionValueList
}

proc ::sth::Bgp::configBgpRouteNetworkBlock {bgpRouteConfigHandle routeIdx ipVersion} {
    set networkBlkHandle [::sth::sthCore::invoke stc::get $bgpRouteConfigHandle -children-ipv${ipVersion}networkblock]

    # VALIDATION - make sure user specifies the correct option to configure the prefix length
    if {$ipVersion == 4 && [info exists ::sth::Bgp::userArgsArray(ipv6_prefix_length)] && ![info exists ::sth::Bgp::userArgsArray(netmask)]} {
        return -code error "unable to set \"-ipv6_prefix_length\" when configuring IPv4 routes. use \"-netmask\" to set IPv4 mask."   
    } elseif {$ipVersion == 6 && [info exists ::sth::Bgp::userArgsArray(netmask)] && ![info exists ::sth::Bgp::userArgsArray(ipv6_prefix_length)]} {
        return -code error "unable to set \"-netmask\" when configuring IPv6 routes. use \"-ipv6_prefix_length\" to set IPv6 mask."   
    }
    if {[info exists ::sth::Bgp::userArgsArray(route_ip_addr_step)]} {
        if {![::ip::is $ipVersion $::sth::Bgp::userArgsArray(route_ip_addr_step)]} {
            return -code error "\"-route_ip_addr_step\" must be a IPv$ipVersion address."
        }   
    }
    # According to the HLTAPIv5 spec, "prefix" is not mandatory but we still need to properly step the
    # starting route IP address if "max_route_ranges" > 1. If the user doesn't specify a prefix, we need 
    # to pretend that they actually did.
    if {![info exists ::sth::Bgp::userArgsArray(prefix)]} {
        set ::sth::Bgp::userArgsArray(prefix) [::sth::sthCore::invoke stc::get $networkBlkHandle -StartIpList]
        lappend ::sth::Bgp::sortedSwitchPriorityList [list 10 prefix]
    }

    set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpRouteNetworkBlock add $bgpRouteConfigHandle $routeIdx]
    
    ::sth::sthCore::invoke stc::config $networkBlkHandle $optionValueList
}


proc ::sth::Bgp::configBgpRouteVpn {bgpRouteConfigHandle routeIdx routeType} {
    
    if {$routeType == "ip" || $routeType == "vpn"} {
        set bgpVpnConfigHandle [::sth::sthCore::invoke stc::get $bgpRouteConfigHandle -children-bgpvpnrouteconfig]
	
	#configure the subafi as VPN since vpn related option is configured
	if {$routeType == "vpn"} {
	    ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle "-routesubafi VPN"
	}
	
	if {[info exists ::sth::Bgp::userArgsArray(vrf_count)]} {
            ::sth::sthCore::invoke stc::config $bgpVpnConfigHandle "-vrfcount $::sth::Bgp::userArgsArray(vrf_count)"
        }
	
    } else {
       set bgpVpnConfigHandle $bgpRouteConfigHandle
    }

    set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpRouteVpn add $bgpRouteConfigHandle $routeIdx]

    ::sth::sthCore::invoke stc::config $bgpVpnConfigHandle $optionValueList
}

proc ::sth::Bgp::configBgpRouteVpls {bgpRouteConfigHandle routeIdx} {
    
    set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpRouteVpls add $bgpRouteConfigHandle $routeIdx]

    ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle $optionValueList
    
    if {[info exists ::sth::Bgp::userArgsArray(vrf_count)]} {
        ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle "-vrfcount $::sth::Bgp::userArgsArray(vrf_count)"
    }
}

proc ::sth::Bgp::configBgpRouteVplsad {bgpRouteConfigHandle routeIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_route_config configBgpRouteVplsad add $bgpRouteConfigHandle $routeIdx]

    ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle $optionValueList
    
    if {[info exists ::sth::Bgp::userArgsArray(vrf_count)]} {
        ::sth::sthCore::invoke stc::config $bgpRouteConfigHandle "-vrfcount $::sth::Bgp::userArgsArray(vrf_count)"
    }
}

proc ::sth::Bgp::configRouter {rtrHandle mode routerIdx} {
	set optionValueList [getStcOptionValueList emulation_bgp_config configRouter $mode $rtrHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $rtrHandle $optionValueList
    }
}

proc ::sth::Bgp::configEthIf {ethIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configEthIf $mode $ethIfHandle $routerIdx]
    
    ##auto aggsin the unique mac addr
    if {![info exists ::sth::Bgp::userArgsArray(mac_address_start)]} {
        
        # indirectly connected routers will use the directly connected router's source mac
	if {[info exists ::sth::Bgp::userArgsArray(affiliated_router_target)]} {
	    set step "00:00:00:00:00:00"
	} else {
	    set step "00:00:00:00:00:01"
	}
	
	# mac step is not defined in HltApi spec so we'll just step by 1
        set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
        set value [::sth::sthCore::invoke stc::get $addrOption -NextMac]
        set srcMac [::sth::sthCore::macStep $value $step $routerIdx]
        
        lappend optionValueList -SourceMac $srcMac
        
        if {$routerIdx == [expr $::sth::Bgp::userArgsArray(count) -1]} {
            set nextMac [::sth::sthCore::macStep $srcMac "00:00:00:00:00:01" 1]
            ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
        }
        
    }
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList
    }
}

#qinq support
proc ::sth::Bgp::configOuterVlanIf {vlanIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configOuterVlanIf $mode $vlanIfHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}


proc ::sth::Bgp::configVlanIf {vlanIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configVlanIf $mode $vlanIfHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}

#add for atm
proc ::sth::Bgp::configAtmIf {atmIfHandle rtrId} {
    set atmConfig [list]
    foreach {attr val} [array get ::sth::Bgp::userArgsArray] {
        switch -- [string tolower $attr] {
            vpi             {
                if { [info exists ::sth::Bgp::userArgsArray(vpi_step)] } {
                    lappend atmConfig "-vpi" [expr $val + ($::sth::Bgp::userArgsArray(vpi_step) * $rtrId)]
                } else {
                    lappend atmConfig "-vpi" $val
                }
               
            }
            vci             {
                if { [info exists ::sth::Bgp::userArgsArray(vpi_step)] } {
                    lappend atmConfig "-vci" [expr $val + ($::sth::Bgp::userArgsArray(vci_step) * $rtrId)]
                } else {
                    lappend atmConfig "-vci" $val
                }
            }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    
    #not complete, need futher work
    
    
   ::sth::sthCore::invoke stc::config $atmIfHandle $atmConfig
}

proc ::sth::Bgp::configBgpRouter {bgpRtrHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configBgpRouter $mode $bgpRtrHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpRtrHandle $optionValueList
    }
}


proc ::sth::Bgp::configBfdRegistration {rtrHandle mode routerIdx} {
   
    set bgpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-bgprouterconfig]
    set ipVersion [::sth::sthCore::invoke stc::get $bgpRtrHandle -IpVersion]
    set ipIfHandle [ ::sth::sthCore::invoke stc::get $rtrHandle -children-$ipVersion\if ]
    #For Ipv6, there are two Ipv6Ifs under the router, get the global link one
    if {[string match -nocase "ipv6" $ipVersion]} {
            set ipIfHandle [lindex $ipIfHandle 0]
    }
    set ipaddr [::sth::sthCore::invoke stc::get $ipIfHandle -Address]
    
    #create new bfdrouterconfig if no exiting bfd found
    set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
    if {[llength $bfdrtrcfg] == 0} {
        set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]
    }
    
    #configure enableBFD
    set optionValueList [getStcOptionValueList emulation_bgp_config configBfdRegistration $mode $bgpRtrHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpRtrHandle $optionValueList
    }
}    


proc ::sth::Bgp::configBgpAuthentication {bgpAuthHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configBgpAuthentication $mode $bgpAuthHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpAuthHandle $optionValueList
    }
}

proc ::sth::Bgp::configBgpGlobal {bgpGlobalHandle mode routerIdx} {  
    set optionValueList [getStcOptionValueList emulation_bgp_config configBgpGlobal $mode $bgpGlobalHandle $routerIdx]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpGlobalHandle $optionValueList
    }
}

proc ::sth::Bgp::configIpInterface {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configIpInterface $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::Bgp::configIpv6Interface {ipIfHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configIpv6Interface $mode $ipIfHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}

proc ::sth::Bgp::configCustomPdus {bgpCuspduHandle mode routerIdx} {
    set optionValueList [getStcOptionValueList emulation_bgp_config configCustomPdus $mode $bgpCuspduHandle $routerIdx]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpCuspduHandle $optionValueList
    }
}

proc ::sth::Bgp::processEmulation_bgp_configIpNetmask {ipIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
	if {[string match -nocase "ipv6if*" $ipIfHandle]} {
	    set ipVersion 6
	    set ipMask [sth::sthCore::prefixLengthToIpMask $value $ipVersion]
	    set prefixLength $value
	} else {
	    set ipVersion 4
	    # allow user to specify netmask in IP notation (for backwards compatibility)
	    if {[llength [split $value .]] == 4 && [::ip::is $ipVersion $value]} {
	        set ipMask $value
	        set prefixLength [::ip::maskToLength $ipMask]
	    } else {
	        set ipMask [sth::sthCore::prefixLengthToIpMask $value $ipVersion]
	        set prefixLength $value
	    }
	}

    ::sth::sthCore::invoke stc::config $ipIfHandle [list -PrefixLength $prefixLength -AddrStepMask $ipMask]
}

#qinq support
proc ::sth::Bgp::processEmulation_bgp_configOuterVlanId {vlanIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {[info exists ::sth::Bgp::userArgsArray(vlan_outer_id_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(vlan_outer_id_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(vlan_outer_id_step)]} {
            return -code error "missing \"-vlan_outer_id_step\" switch"
        }
        set vlan [expr $value + ($routerIdx * $::sth::Bgp::userArgsArray(vlan_outer_id_step))]
    } else {
        set vlan $value
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $vlan"
}

proc ::sth::Bgp::processEmulation_bgp_configVlanId {vlanIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {[info exists ::sth::Bgp::userArgsArray(vlan_id_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(vlan_id_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(vlan_id_step)]} {
            return -code error "missing \"-vlan_id_step\" switch"
        }
        set vlan [expr $value + ($routerIdx * $::sth::Bgp::userArgsArray(vlan_id_step))]
    } else {
        set vlan $value
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $vlan"
}

proc ::sth::Bgp::processEmulation_bgp_configRouterId {rtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    if {[info exists ::sth::Bgp::userArgsArray(local_router_id_step)]} {
        set stepValue $::sth::Bgp::userArgsArray(local_router_id_step)
    } else {
         set stepValue "0.0.0.1"
    }
    set ip [::sth::sthCore::updateIpAddress 4 $value $stepValue $routerIdx]
    if {[info exists ::sth::Bgp::userArgsArray(local_router_id_enable)] && $::sth::Bgp::userArgsArray(local_router_id_enable) == "0"} {
         return ""
    } else {
        return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $ip"
    }
   
    
}

proc ::sth::Bgp::processEmulation_bgp_configAffRouter {rtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
    # verify affiliated router exists
    set allRouters [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router]
	if {[lsearch $allRouters $value] < 0} {
	    return -code error "Unable to create an affiliation to $value. Make sure a valid router handle is being used."
	}
	
	# force the bgp router's source mac to match the affiliated routers source mac
	set ethIf [::sth::sthCore::invoke stc::get $value -children-ethiiif]
	set affRtrSrcMac [::sth::sthCore::invoke stc::get $ethIf -SourceMac]
	# set or overwrite (if -mac_address_start is specified in bgp_config) the source mac 
	# for the indirectly connected bgp router
	set ::sth::Bgp::userArgsArray(mac_address_start) $affRtrSrcMac
	if {[lsearch $::sth::Bgp::sortedSwitchPriorityList {10 mac_address_start}] == -1} {
	    lappend ::sth::Bgp::sortedSwitchPriorityList [list 10 mac_address_start]
	}
	
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $value"
}

proc ::sth::Bgp::processEmulation_bgp_configSrcMacAddr {ethIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
	# indirectly connected routers will use the directly connected router's source mac
	if {[info exists ::sth::Bgp::userArgsArray(affiliated_router_target)]} {
	    set step "00:00:00:00:00:00"
	} else {
	    set step "00:00:00:00:00:01"
	}
	
	# mac step is not defined in HltApi spec so we'll just step by 1
        set srcMac [::sth::sthCore::macStep $value $step $routerIdx]
        
        if {$routerIdx == [expr $::sth::Bgp::userArgsArray(count) -1]} {
            set nextMac [::sth::sthCore::macStep $srcMac "00:00:00:00:00:01" 1]
            set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
            ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
        }
    
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $srcMac"
}

proc ::sth::Bgp::processEmulation_bgp_configIp {ipIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
	# check for any dependencies
	checkDependency "emulation_bgp_config" $option 1
	
	set ipVersion 4
	if {[string match -nocase "ipv6if*" $ipIfHandle]} {
	    set ipVersion 6
	}
	
    ##SPIRENT_MOD 8-11-08 Xiaozhi Liu
    ##Needed to change processing.Porcessing remote_addr_step is incorrect, add processEmulation_bgp_config_RemoteAddr
    ## to process remote_addr_step
    ##Replaced next block 
	## SPIRENT_MOD 08-08-05 Fei Cheng
	## Needed to change processing. Add support for remote_addr_step
	## Replaced next block 
	##if {[info exists ::sth::Bgp::userArgsArray(local_addr_step)]} {
	##    set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(local_addr_step) $routerIdx]
	##} else {
	##    set ip $value
	##}
	#set ip $value
	#if {[info exists ::sth::Bgp::userArgsArray(local_addr_step)] && ![regexp remote_ip $option]} {
	#    set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(local_addr_step) $routerIdx]
	#} 
	#if {[info exists ::sth::Bgp::userArgsArray(remote_addr_step)] && [regexp remote_ip $option]} {
	#    set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(remote_addr_step) $routerIdx]
	#}
	## SPIRENT_MOD end of change
	
	#need to take care of the backward compatible
	if {![info exists ::sth::Bgp::userArgsArray(ip_stack_version)]} {
	    if {[info exists ::sth::Bgp::userArgsArray(local_addr_step)]} {
		set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(local_addr_step) $routerIdx]
	    } else {
		set ip $value
	    }
	} else {
	    if {[string match $option "local_ip_addr"]} {
		if {[info exists ::sth::Bgp::userArgsArray(local_addr_step)]} {
		    set ip [::sth::sthCore::updateIpAddress 4 $value $::sth::Bgp::userArgsArray(local_addr_step) $routerIdx]
		} else {
		    set ip $value
		}
	    } else {
		if {[info exists ::sth::Bgp::userArgsArray(local_ipv6_addr_step)]} {
		    set ip [::sth::sthCore::updateIpAddress 6 $value $::sth::Bgp::userArgsArray(local_ipv6_addr_step) $routerIdx]
		} else {
		    set ip $value
		}
	    }
	}
	
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $ip"
}

proc ::sth::Bgp::processEmulation_bgp_config_RemoteAddr {BfdRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    # check for any dependencies
    checkDependency "emulation_bgp_config" $option 1
    
    set ipVer [::sth::sthCore::invoke stc::get $BfdRtrHandle -IpVersion]
	
    set ipVersion 4
    if {[string match -nocase "ipv6" $ipVer]} {
        set ipVersion 6
    }
    	
    if {[info exists ::sth::Bgp::userArgsArray(remote_addr_step)]} {
        set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(remote_addr_step) $routerIdx]
    } elseif {[info exists ::sth::Bgp::userArgsArray(remote_ipv6_addr_step)]} {
        set ip [::sth::sthCore::updateIpAddress $ipVersion $value $::sth::Bgp::userArgsArray(remote_ipv6_addr_step) $routerIdx]
    } else {
        set ip $value
    }
    
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $ip"
}

proc ::sth::Bgp::processEmulation_bgp_config_Nexthop {ipIfHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
    # check for any dependencies
    checkDependency "emulation_bgp_config" $option 1
    

    if {[string match $option "next_hop_ip"]} {	
        if {[info exists ::sth::Bgp::userArgsArray(next_hop_ip_step)]} {
            set ip [::sth::sthCore::updateIpAddress 4 $value $::sth::Bgp::userArgsArray(next_hop_ip_step) $routerIdx]
        } else {
            set ip $value
        }
    } elseif {[string match $option "next_hop_ipv6"]} {	
        if {[info exists ::sth::Bgp::userArgsArray(next_hop_ipv6_step)]} {
            set ip [::sth::sthCore::updateIpAddress 6 $value $::sth::Bgp::userArgsArray(next_hop_ipv6_step) $routerIdx]
        } else {
		if {[info exist ::sth::Bgp::userArgsArray(local_ipv6_addr)]} {
			#check if getway is in the same network with the ipv6 address, if it is in the same gateway no need to change the value.
			set prefix [::sth::sthCore::invoke stc::get $ipIfHandle -PrefixLength]
			set ipAddressValue [::sth::sthCore::normalizeIPv6Addr $::sth::Bgp::userArgsArray(local_ipv6_addr)]
			set gatewayAddressValue [::sth::sthCore::normalizeIPv6Addr $value]
			set binIpAddress ""
			set binGatewayAddress ""
			set ipOctets [split $ipAddressValue :]
			set gatewayOctets [split $gatewayAddressValue :]
			for {set i 0} {$i < 8} {incr i} {
			    set ipOctet [lindex $ipOctets $i]
			    binary scan [binary format H4 $ipOctet] B* binIp
			    set binIpAddress "$binIpAddress$binIp"

			    set gatewayOctet [lindex $gatewayOctets $i]
			    binary scan [binary format H4 $gatewayOctet] B* binGateway
			    set binGatewayAddress "$binGatewayAddress$binGateway"
			}
			set ipNetMask [string range $binIpAddress 0 [expr $prefix - 1]]
			set gatewayNetMask [string range $binGatewayAddress 0 [expr $prefix - 1]]
			if {$ipNetMask != $gatewayNetMask} {
			    set ip [::sth::ospf::calGateway v6 $::sth::Bgp::userArgsArray(local_ipv6_addr) $prefix]
			} else {
			    set ip $value
			}

		} else {
		    set ip $value
		}
        }
    } else {
    	if {[info exist ::sth::Bgp::userArgsArray(local_ipv6_addr)]} {
    		set prefix [::sth::sthCore::invoke stc::get $ipIfHandle -PrefixLength]
    		set ip [::sth::ospf::calGateway v6 $::sth::Bgp::userArgsArray(local_ipv6_addr) $prefix]
    	} else {
		if {[info exists ::sth::Bgp::userArgsArray(next_hop_ipv6_step)]} {
            		set ip [::sth::sthCore::updateIpAddress 6 $value $::sth::Bgp::userArgsArray(next_hop_ipv6_step) $routerIdx]
        	} else {
            		set ip $value
        	}
    	}
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $ip"
}


proc ::sth::Bgp::processEmulation_bgp_config_LocalAs {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {[info exists ::sth::Bgp::userArgsArray(local_as_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(local_as_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(local_as_step)]} {
            return -code error "missing \"-local_as_step\" switch"
        }
        set localAs [expr $value + ($routerIdx * $::sth::Bgp::userArgsArray(local_as_step))]
    } else {
        set localAs $value
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $localAs"
}

proc ::sth::Bgp::processEmulation_bgp_config_RemoteAs {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {[info exists ::sth::Bgp::userArgsArray(remote_as_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(remote_as_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(remote_as_step)]} {
            return -code error "missing \"-remote_as_step\" switch"
        }
        set remoteAs [expr $value + ($routerIdx * $::sth::Bgp::userArgsArray(remote_as_step))]
    } else {
        set remoteAs $value
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $remoteAs"
}

proc ::sth::Bgp::processEmulation_bgp_config_LocalAs4 {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
    ::sth::sthCore::invoke stc::config $bgpRtrHandle "-Enable4ByteAsNum TRUE"
    
    if {[info exists ::sth::Bgp::userArgsArray(local_as4_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(local_as4_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(local_as4_step)]} {
            return -code error "missing \"-local_as4_step\" switch"
        }
		set highValue [lindex [split $value :] 0]
		set lowValue [lindex [split $value :] 1]
		set highStepValue [lindex [split $::sth::Bgp::userArgsArray(local_as4_step) :] 0]
		set lowStepValue [lindex [split $::sth::Bgp::userArgsArray(local_as4_step) :] 1]
		set asHigh [expr $highValue + ($routerIdx * $highStepValue)]
		set aslow [expr $lowValue + ($routerIdx * $lowStepValue)]
		if {$aslow > 65535} {
		   set asHigh [expr $asHigh + [expr $aslow/65535]]
		   set aslow [expr $aslow%65535]
		}
		if {$asHigh > 65535} {
		   set asHigh 65535
		   ::sth::sthCore::log debug "the as4 number is stepping over the boundary"
		}
			
		set localAs $asHigh:$aslow
    } else {
        set localAs $value
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $localAs"
}

proc ::sth::Bgp::processEmulation_bgp_config_RemoteAs4 {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    ::sth::sthCore::invoke stc::config $bgpRtrHandle "-Enable4ByteDutAsNum TRUE"
	
    if {[info exists ::sth::Bgp::userArgsArray(remote_as4_mode)] && \
        [string match -nocase "increment" $::sth::Bgp::userArgsArray(remote_as4_mode)]} {
        if {![info exists ::sth::Bgp::userArgsArray(remote_as4_step)]} {
            return -code error "missing \"-remote_as4_step\" switch"
        }
		set highValue [lindex [split $value :] 0]
		set lowValue [lindex [split $value :] 1]
		set highStepValue [lindex [split $::sth::Bgp::userArgsArray(remote_as4_step) :] 0]
		set lowStepValue [lindex [split $::sth::Bgp::userArgsArray(remote_as4_step) :] 1]
		set asHigh [expr $highValue + ($routerIdx * $highStepValue)]
		set aslow [expr $lowValue + ($routerIdx * $lowStepValue)]
		if {$aslow > 65535} {
		   set asHigh [expr $asHigh + [expr $aslow/65535]]
		   set aslow [expr $aslow%65535]
		}
		if {$asHigh > 65535} {
		   set asHigh 65535
		   ::sth::sthCore::log debug "the as4 number is stepping over the boundary"
		}
			
		set remoteAs4 $asHigh:$aslow
    } else {
        set remoteAs4 $value
    }
	
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $remoteAs4"
}

proc ::sth::Bgp::processEmulation_bgp_config_IpVersion {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
    set rtrHandle [::sth::sthCore::invoke stc::get $bgpRtrHandle -parent]
	set newIpVersion $value
	set oldIpVersion [getIpVersionFromStack $rtrHandle]
        if {$oldIpVersion == "4and6"} {
            #this is dual stack device, so can configure both ipv6 or ipv4 bgp, no need to modify the ip stack
        } else {
            if {$oldIpVersion != $newIpVersion} {
                    #remove old IF stack
                    set hasVlan 0
                    if {[catch {::sth::sthCore::invoke stc::get $rtrHandle -children-VlanIf} vlanResultIf]} {
                            return -code error $vlanResultIf
                    } else {
                        if {[llength $vlanResultIf]} {
                            set hasVlan 1   
                        }
                            if {!$hasVlan} {
                                    # There is no vlan configuration
                                    switch -- $newIpVersion {
                                            4 {
                                                    set IfStack "Ipv4If EthIIIf"
                                            }
                                            6 {
                                                    set IfStack "Ipv6If EthIIIf"
                                            }
                                    }
                                    set IfCount "1 1"
                            } else {
                                    # There is vlan configuration
                                    switch -- $newIpVersion {
                                            4 {
                                                    set IfStack "Ipv4If VlanIf EthIIIf"
                                            }
                                            6 {
                                                    set IfStack "Ipv6If VlanIf EthIIIf"
                                            }
                                    }
                                    set IfCount "1 1 1"
                            }
                    }
                                    
                    switch -- $oldIpVersion {
                            4 {
                                    set ipv4ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv4If]
                                    if {[llength $ipv4ResultIf]} {
                                    set performStatus [::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $rtrHandle -TopIf $ipv4ResultIf]
                            }
                            }
                            6 {
                                    set ipv6ResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-Ipv6If]
                                foreach ipv6If $ipv6ResultIf {
                                set performStatus [::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $rtrHandle -TopIf $ipv6If]
                                }
                            }
                    }
                            
                    #add new IF stack
                    switch -- $newIpVersion {
                            4 {
                                    set performStatus [::sth::sthCore::invoke stc::perform IfStackAdd -DeviceList $rtrHandle -IfStack $IfStack -IfCount $IfCount]
                            }
                            6 {
                                    set performStatus [::sth::sthCore::invoke stc::perform IfStackAdd -DeviceList $rtrHandle -IfStack $IfStack -IfCount $IfCount]
                                    if {[catch {::sth::sthCore::invoke stc::get $rtrHandle -children-vlanif} vlanResultIf]} {
                                            return -code error $vlanResultIf
                                    } else {
                                            if {!$hasVlan} {
                                                    set ethiiResultIf [::sth::sthCore::invoke stc::get $rtrHandle -children-ethiiif]
                                                    set AttachToIf $ethiiResultIf
                                            } else {
                                                    set AttachToIf $vlanResultIf
                                            }
                                    }	
                                    set performStatus [::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $rtrHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $AttachToIf]
                                    set ipv6ResultIfList [::sth::sthCore::invoke stc::get $rtrHandle -children-ipv6if]
                                    set ipv6ifLocal [lindex $ipv6ResultIfList 1]
#                                    set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                                    set linkLocalIp "FE80:0:0:0"
#                                    foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                                            append linkLocalIp ":$num1$num2$num3$num4"
#                                    }
                                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -Address fe80::2
                                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                            }
                    }
            }
        }
			
	# config new bgp ip_version
	set newIpVersionValue [::sth::sthCore::getFwdmap ::sth::Bgp:: emulation_bgp_config ip_version $newIpVersion]
	set configStatus [::sth::sthCore::invoke stc::config $bgpRtrHandle [list -IpVersion $newIpVersionValue]]
}

proc ::sth::Bgp::processEmulation_bgp_configNlri {bgpRtrHandle option value routerIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"

    if {$value == 0} { return }    

	array set stcAttrMap {ipv4_unicast_nlri {afi 1 subAfi 1} \
			      ipv4_multicast_nlri {afi 1 subAfi 2} \
                              ipv4_unicast_multicast_nlri {afi 1 subAfi 3} \
			      ipv4_mpls_nlri {afi 1 subAfi 4} \
                              ipv4_multicast_vpn_nlri {afi 1 subAfi 5} \
			      ipv4_vpls_nlri {afi 1 subAfi 65} \
                              ipv4_mdt_nlri {afi 1 subAfi 66} \
                              ipv4_e_vpn_nlri {afi 1 subAfi 70} \
                              ipv4_ls_non_vpn_nlri {afi 1 subAfi 71} \
                              ipv4_mpls_vpn_nlri {afi 1 subAfi 128} \
                              ipv4_rt_constraint_nlri {afi 1 subAfi 132} \
                              ipv4_flow_spec_nlri {afi 1 subAfi 133} \
                              ipv4_flow_spec_vpn_nlri {afi 1 subAfi 134} \
			      ipv6_unicast_nlri {afi 2 subAfi 1} \
			      ipv6_multicast_nlri {afi 2 subAfi 2} \
                              ipv6_unicast_multicast_nlri {afi 2 subAfi 3} \
			      ipv6_mpls_nlri {afi 2 subAfi 4} \
                              ipv6_multicast_vpn_nlri {afi 2 subAfi 5} \
                              ipv6_vpls_nlri {afi 2 subAfi 65} \
                              ipv6_mdt_nlri {afi 2 subAfi 66} \
                              ipv6_e_vpn_nlri {afi 2 subAfi 70} \
                              ipv6_ls_non_vpn_nlri {afi 2 subAfi 71} \
                              ipv6_mpls_vpn_nlri {afi 2 subAfi 128} \
                              ipv6_rt_constraint_nlri {afi 2 subAfi 132} \
                              ipv6_flow_spec_nlri {afi 2 subAfi 133} \
                              ipv6_flow_spec_vpn_nlri {afi 2 subAfi 134} \
			      vpls_unicast_nlri {afi 25 subAfi 1} \
			      vpls_multicast_nlri {afi 25 subAfi 2} \
                              vpls_unicast_multicast_nlri {afi 65 subAfi 3} \
			      vpls_mpls_nlri {afi 25 subAfi 4} \
                              vpls_multicast_vpn_nlri {afi 25 subAfi 5} \
                              vpls_nlri {afi 25 subAfi 65} \
                              vpls_mdt_nlri {afi 25 subAfi 66} \
                              vpls_e_vpn_nlri {afi 25 subAfi 70} \
                              vpls_ls_non_vpn_nlri {afi 25 subAfi 71} \
                              vpls_mpls_vpn_nlri {afi 25 subAfi 128} \
                              vpls_rt_constraint_nlri {afi 25 subAfi 132} \
                              vpls_flow_spec_nlri {afi 25 subAfi 133} \
                              vpls_flow_spec_vpn_nlri {afi 25 subAfi 134} \
                              kompella_vpls_unicast_nlri {afi 196 subAfi 1} \
			      kompella_vpls_multicast_nlri {afi 196 subAfi 2} \
                              kompella_vpls_unicast_multicast_nlri {afi 196 subAfi 3} \
			      kompella_vpls_mpls_nlri {afi 196 subAfi 4} \
                              kompella_vpls_multicast_vpn_nlri {afi 196 subAfi 5} \
                              kompella_vpls_vpls_nlri {afi 196 subAfi 65} \
                              kompella_vpls_mdt_nlri {afi 196 subAfi 66} \
                              kompella_vpls_e_vpn_nlri {afi 196 subAfi 70} \
                              kompella_vpls_ls_non_vpn_nlri {afi 196 subAfi 71} \
                              kompella_vpls_mpls_vpn_nlri {afi 196 subAfi 128} \
                              kompella_vpls_rt_constraint_nlri {afi 196 subAfi 132} \
                              kompella_vpls_flow_spec_nlri {afi 196 subAfi 133} \
                              kompella_vpls_flow_spec_vpn_nlri {afi 196 subAfi 134} \
                              link_unicast_nlri {afi 16388 subAfi 1} \
			      link_multicast_nlri {afi 16388 subAfi 2} \
                              link_unicast_multicast_nlri {afi 16388 subAfi 3} \
			      link_mpls_nlri {afi 16388 subAfi 4} \
                              link_multicast_vpn_nlri {afi 16388 subAfi 5} \
                              link_vpls_nlri {afi 16388 subAfi 65} \
                              link_mdt_nlri {afi 16388 subAfi 66} \
                              link_e_vpn_nlri {afi 16388 subAfi 70} \
                              link_ls_non_vpn_nlri {afi 16388 subAfi 71} \
                              link_mpls_vpn_nlri {afi 16388 subAfi 128} \
                              link_rt_constraint_nlri {afi 16388 subAfi 132} \
                              link_flow_spec_nlri {afi 16388 subAfi 133} \
                              link_flow_spec_vpn_nlri {afi 16388 subAfi 134} \
                              }
	
	set afiVal 0
	set subafiVal 0
	if {[info exists stcAttrMap($option)]} {
    	set afiVal [lindex $stcAttrMap($option) 1]
    	set subafiVal [lindex $stcAttrMap($option) 3]
	}

#	if {([expr $subafiVal & 127] != 0)} {
#		if {([expr $subafiVal & 252] != 0)} {
#			return -code error "Conflicting configuration of NRLI attributes: Cannot be VPN and Uni/Multi at the same time."
#		} elseif {([expr $subafiVal & 251] != 0)} {
#			return -code error "Conflicting configuration of NRLI attributes: Cannot be VPN and Label at the same time."
#		}
#	} elseif {([expr $subafiVal & 252] != 0) & ([expr $subafiVal & 251] != 0)} {
#		return -code error "Conflicting configuration of NRLI attributes: Cannot be Uni/Multi and Label at the same time."
#	}
	set BgpCapabilityHdl [::sth::sthCore::invoke stc::create "BgpCapabilityConfig" -under $bgpRtrHandle [list -afi $afiVal -subafi $subafiVal]]
	return
}

proc ::sth::Bgp::processEmulation_bgp_configBfd {bgpRtrHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
    
    if {$value == "1"} {
        set bfdValue true
    } elseif {$value == "0"} {
        set bfdValue false
    }
        
    if {[catch {set attr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::getswitchprop Failed: $err" {}
        return -code error $returnKeyedList  
    }  
    return "-$attr $bfdValue"
}



proc ::sth::Bgp::getPrefixLength {ipVersion ipAddressValue} {
    switch -- $ipVersion {
	    4 {
		    set octets [split $ipAddressValue .]
		    if {[llength $octets] != 4} {
			    set octets [lrange [concat $octets 0 0 0] 0 3]
			}
		    set binIpAddress ""
		    foreach oct $octets {
			    binary scan [binary format c $oct] B* bin
			    set binIpAddress "$binIpAddress$bin"
			}

		    for {set x 0;set prefixLength 0} {$x < 32} {incr x} {
			    set oct [string range $binIpAddress $x $x]
			    if {$oct != 1} {
				    break
				} else {
				    incr prefixLength
				}
			}
		    return $prefixLength
		}
	    6 {
			return $ipAddressValue
		}
	    default {}
	}
}

proc ::sth::Bgp::processEmulation_bgp_config_enableStagger {bgpGlobalHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {$value == 1 && ![info exists ::sth::Bgp::userArgsArray(staggered_start_time)]} {
        return -code error "\"-staggered_start_time\" must be specified"
    } elseif {$value == 0} {
        # start all routers at the same time
        return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config staggered_start_time stcattr] 0"   	
    }
}

proc ::sth::Bgp::processEmulation_bgp_config_staggerStart {bgpGlobalHandle option value routerIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value $routerIdx"
	
    if {![info exists ::sth::Bgp::userArgsArray(staggered_start_enable)] || \
        $::sth::Bgp::userArgsArray(staggered_start_enable) == 0} {
        return -code error "\"-staggered_start_enable\" must be enabled"
    }
    return "-[::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_config $option stcattr] $value"    
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addGeneric {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	# check for any dependencies
	checkDependency "emulation_bgp_route_config" $option 1
	
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $option stcattr]
	return "-$stcAttr [list $value]"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addAggregator {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	set index [string last ":" $value]
	set aggregatorAs [string range $value 0 [expr $index-1]]
	set aggregatorIp [string range $value [expr $index+1] [string length $value]]

	if {[llength $aggregatorAs] == 0 || [llength $aggregatorIp] == 0} {
	    return -code error "invalid \"-$option\" value: $value. Format: <asn>:<x.x.x.x>"
	}
	
	return "-AggregatorAs $aggregatorAs -AggregatorIp $aggregatorIp"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addSubAfi {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	set ipVer $::sth::Bgp::userArgsArray(ip_version)
	switch -- [string tolower $option] {
            ipv4_mpls_nlri {
                if {$ipVer == 4 && $value} {
                    set subAfi "LABELED_IP"
                }
            }
            ipv4_mpls_vpn_nlri {
                if {$ipVer == 4 && $value} {
                    set subAfi "VPN"
                }
            }
            ipv4_multicast_nlri {
                if {$ipVer == 4 && $value} {
                    set subAfi "MULTICAST"
                }
            }
            ipv4_unicast_nlri {
                if {$ipVer == 4 && $value} {
                    set subAfi "UNICAST"
                }
            }
            ipv6_mpls_nlri {
                if {$ipVer == 6 && $value} {
                    set subAfi "LABELED_IP"
                }
            }
            ipv6_mpls_vpn_nlri {
                if {$ipVer == 6 && $value} {
                    set subAfi "VPN"
                }
            }
            ipv6_multicast_nlri {
                if {$ipVer == 6 && $value} {
                    set subAfi "MULTICAST"
                }
            }
            ipv6_unicast_nlri {
                if {$ipVer == 6 && $value} {
                    set subAfi "UNICAST"
                }
            }
        }
	
        if {[info exists subAfi]} {
            return "-RouteSubAfi $subAfi"
        }
	
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addLabelIncrMode {handle option value routeIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value"
    
    switch -- [string tolower $value] {
        fixed -
        prefix -
        none {
            set stcValue [::sth::sthCore::getFwdmap ::sth::Bgp:: emulation_bgp_route_config $option $::sth::Bgp::userArgsArray($option)]
        }
        rd {
            return -code error "rd mode is not supported at this time."   
        }
        default {
            return -code error "invalid mode \"-label_incr_mode\". must be fixed or prefix."
        }
    }
    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $option stcattr]
	return "-$stcAttr $stcValue"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addAs_path {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	regexp {(.*?):(.*)$} $value match asPathSegType asPathValue
	if {[llength $asPathSegType] == 0 || [llength $asPathValue] == 0} {
	    return -code error "invalid \"-$option\" value: $value. Format: <as_path_type>:<comma separated segment list>"
	}
	# convert as path type and value to stc format
	set stcAsPathSegType [string map -nocase {as_set SET as_seq SEQUENCE as_confed_set CONFED_SET as_confed_seq CONFED_SEQ} $asPathSegType]
	set asPathValue [split $asPathValue ,]
	
	return "-AsPathSegmentType $stcAsPathSegType -AsPath [list $asPathValue]"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addCommunity {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	# check for any dependencies
	checkDependency "emulation_bgp_route_config" $option 1
	
	foreach {commType commData} [split $value :] {break}
	if {[llength $commType] == 0 || [llength $commData] == 0} {
	    return -code error "invalid \"-$option\" value: $value. Format: <communities_type>:<data>"
	}
	# convert community type and value to stc format
	switch -- [string tolower $commType] {
	    as_id {
	        set stcValue $value
	    }
	    default {
	        return -code error "community type not supported. supported types are: as_id"   
	    }
	}
	set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $option stcattr]
	return "-$stcAttr $stcValue"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addNetmask {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	if {![::info exists ::sth::Bgp::userArgsArray(ip_version)]} {
		return -code error "\"-ip_version\" is required for configuring \"-netmask\"."
	}

	switch -- $::sth::Bgp::userArgsArray(ip_version) {
		4 {
			if {[regexp "\\." $value]} {
				set value [::sth::Bgp::getPrefixLength 4 $value]
			} 
			#else the input in the numberic
		}
		6 {
			return -code error "\"-netmask\" applies to IPv4 routes. Use \"-ipv6_prefix_length\" for IPv6 routes."
		}
	}

	set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $option stcattr]
	return "-$stcAttr $value"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addNext_hop {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	# check for any dependencies
	checkDependency "emulation_bgp_route_config" $option 1
	
	if {![::info exists ::sth::Bgp::userArgsArray(next_hop_set_mode)]} {
		return -code error "\"-next_hop_set_mode\" is required when \"-next_hop\" is specified."
	} else {
		switch -- [string tolower $::sth::Bgp::userArgsArray(next_hop_set_mode)] {
			same {
				#Fetch the value of the local ip address
				set bgpRouterConfigHandle [::sth::sthCore::invoke stc::get $handle -parent]
				set ipVer [::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -IpVersion]
				set bgpRouterHandle [::sth::sthCore::invoke stc::get $bgpRouterConfigHandle -parent]
				set ipResultIf [::sth::sthCore::invoke stc::get $bgpRouterHandle -children-${ipVer}if]
				set nextHopAddr [::sth::sthCore::invoke stc::get [lindex $ipResultIf 0] -Address]
				return "-NextHop $nextHopAddr"
			}
			manual {
			    if {[info exists ::sth::Bgp::userArgsArray(next_hop_ip_version)]} {
			        if {$sth::Bgp::userArgsArray(next_hop_ip_version) == "4" || $sth::Bgp::userArgsArray(next_hop_ip_version) == "6"} {
			            if {![::ip::is $sth::Bgp::userArgsArray(next_hop_ip_version) $value]} {
			                return -code error "\"-next_hop $value\" doesn't match configured \"-next_hop_ip_version\". must be of type IPv$sth::Bgp::userArgsArray(next_hop_ip_version)."
			            }
			            if {![::ip::is $sth::Bgp::userArgsArray(ip_version) $value]} {
			                return -code error "\"-next_hop $value\" must be an IPv$sth::Bgp::userArgsArray(ip_version) address."
			            }
			        } else {
			            return -code error "unknown \"-next_hop_ip_version\". must be 4 or 6."   
			        }
			    } else {
			        return -code error "\"-next_hop_ip_version\" is required when \"-next_hop\" is specified."   
			    }
			    return "-NextHop $value"
			}
			default {
				return -code error "Incorrect Next Hop Mode Value. Should be same or manual"	   
			}
		}
	}
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addRd_admin_value {handle option value routeIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value"
    
    # validate dependent options
    if {![::info exists ::sth::Bgp::userArgsArray(rd_admin_step)]} {
        #return -code error "\"-rd_admin_step\" is required"
        if {$value == 0} {
            set ::sth::Bgp::userArgsArray(rd_admin_step) 1
        } elseif  {$value == 1} {
            set ::sth::Bgp::userArgsArray(rd_admin_step) "0.0.0.1"
        } else {
            return -code error "invalid \"-rd_type\" specified. must be \"0 or 1\""
        }
    }
    if {![::info exists ::sth::Bgp::userArgsArray(rd_admin_value)]} {
        return -code error "\"-rd_admin_value\" is required"
    }
    if {![::info exists ::sth::Bgp::userArgsArray(rd_assign_step)]} {
        # return -code error "\"-rd_assign_step\" is required"
        set ::sth::Bgp::userArgsArray(rd_assign_step) 1
    }
    if {![::info exists ::sth::Bgp::userArgsArray(rd_assign_value)]} {
        return -code error "\"-rd_assign_value\" is required"
    }
	
    # validate rd values based on rd_type
    switch -- $value {
        0 {
            # administrator field is AS number
            foreach opt {rd_admin_value rd_admin_step} {
                if {![string is integer $::sth::Bgp::userArgsArray($opt)] || \
                    ($::sth::Bgp::userArgsArray($opt) < 0 || $::sth::Bgp::userArgsArray($opt) > 65535)} {
                        return -code error "\"-$opt\" must be an integer in the range 0-65535"
                }
            }
        
            set rdAdminVal [expr $::sth::Bgp::userArgsArray(rd_admin_value) + ($::sth::Bgp::userArgsArray(rd_admin_step) * $routeIdx)]
        }
        1 {
            # administrator field is global IPv4 address
            foreach opt {rd_admin_value rd_admin_step} {
                if {![::ip::is ipv4 $::sth::Bgp::userArgsArray($opt)]} {
                    return -code error "\"-$opt\" must be a valid IPv4 address"
                }
            }
            
            if {![::info exists ::sth::Bgp::userArgsArray(rd_admin_step)]} {
                set ::sth::Bgp::userArgsArray(rd_admin_step) "0.0.0.1"
            }
            
            set rdAdminVal [::sth::sthCore::updateIpAddress 4 $::sth::Bgp::userArgsArray(rd_admin_value) $::sth::Bgp::userArgsArray(rd_admin_step) $routeIdx]
        }
        default {
            return -code error "invalid \"-rd_type\" specified. must be \"0 or 1\""
        }
    }
    # validate the rd_assign_value and rd_assign_step (must be integers)
    foreach opt {rd_assign_value rd_assign_step} {
        if {![string is integer $::sth::Bgp::userArgsArray($opt)] || $::sth::Bgp::userArgsArray($opt) < 0} {
            return -code error "\"-$opt\" must be an integer"
        }
    }
    set rdAssignVal [expr $::sth::Bgp::userArgsArray(rd_assign_value) + ($::sth::Bgp::userArgsArray(rd_assign_step) * $routeIdx)]
    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config rd_admin_value stcattr]
    set stcValue [join [list $rdAdminVal $rdAssignVal] :]
    return "-$stcAttr $stcValue"	
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addTarget {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	if {![::info exists ::sth::Bgp::userArgsArray(target_assign)]} {
		return -code error "\"-target_assign\" is required"
	} elseif {![::info exists ::sth::Bgp::userArgsArray(target)]} {
		return -code error "\"-target\" is required"
	}
	
	# validate target based on target_type
	switch -- [string tolower $value] {
	    as {
	        if {![string is integer $::sth::Bgp::userArgsArray(target)] || \
	            ($::sth::Bgp::userArgsArray(target) < 0 || $::sth::Bgp::userArgsArray(target) > 65535)} {
	            return -code error "\"-target\" must be an integer in the range 0-65535"
	        }
	    }
	    ip {
	        if {![::ip::is ipv4 $::sth::Bgp::userArgsArray(target)]} {
	            return -code error "\"-target\" must be a valid IPv4 address"
	        }
	    }
	    default {
	        return -code error "invalid \"-target_type\" specified. must be \"as or ip\""
	    }
	}
	set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config target stcattr]
	set stcValue [join [list $::sth::Bgp::userArgsArray(target) $::sth::Bgp::userArgsArray(target_assign)] :]
        set stcAttrStep [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config target_step stcattr]
        set stcValueStep "0:1"
        if {[::info exists ::sth::Bgp::userArgsArray(target_step)] && [::info exists ::sth::Bgp::userArgsArray(target_assign_step)]} {
            set stcValueStep [join [list $::sth::Bgp::userArgsArray(target_step) $::sth::Bgp::userArgsArray(target_assign_step)] :]
        } elseif {[::info exists ::sth::Bgp::userArgsArray(target_step)]} {
            set stcValueStep [join [list $::sth::Bgp::userArgsArray(target_step) 1] :]
        } elseif {[::info exists ::sth::Bgp::userArgsArray(target_assign_step)]} {
            set stcValueStep [join [list 0 $::sth::Bgp::userArgsArray(target_assign_step)] :]
        }
        
	return "-$stcAttr $stcValue -$stcAttrStep $stcValueStep"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addTargetImport {handle option value routeIdx} {
	::sth::sthCore::log debug "Processing switch: -$option $value"
	
	if {![::info exists ::sth::Bgp::userArgsArray(import_target_assign)]} {
		return -code error "\"-import_target_assign\" is required"
	} elseif {![::info exists ::sth::Bgp::userArgsArray(import_target)]} {
		return -code error "\"-import_target\" is required"
	}
	
	# validate import_target based on import_target_type
	switch -- [string tolower $value] {
	    as {
	        if {![string is integer $::sth::Bgp::userArgsArray(import_target)] || \
	            ($::sth::Bgp::userArgsArray(import_target) < 0 || $::sth::Bgp::userArgsArray(import_target) > 65535)} {
	            return -code error "\"-import_target\" must be an integer in the range 0-65535"
	        }
	    }
	    ip {
	        if {![::ip::is ipv4 $::sth::Bgp::userArgsArray(import_target)]} {
	            return -code error "\"-import_target\" must be a valid IPv4 address"
	        }
	    }
	    default {
	        return -code error "invalid \"-import_target_type\" specified. must be \"as or ip\""
	    }
	}
	set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config import_target stcattr]
	set stcValue [join [list $::sth::Bgp::userArgsArray(import_target) $::sth::Bgp::userArgsArray(import_target_assign)] :]
        set stcAttrStep [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config import_target_step stcattr]
        set stcValueStep "0:1"
        if {[::info exists ::sth::Bgp::userArgsArray(import_target_step)] && [::info exists ::sth::Bgp::userArgsArray(import_target_assign_step)]} {
            set stcValueStep [join [list $::sth::Bgp::userArgsArray(import_target_step) $::sth::Bgp::userArgsArray(import_target_assign_step)] :]
        } elseif {[::info exists ::sth::Bgp::userArgsArray(import_target_step)]} {
            set stcValueStep [join [list $::sth::Bgp::userArgsArray(import_target_step) 1] :]
        } elseif {[::info exists ::sth::Bgp::userArgsArray(import_target_assign_step)]} {
            set stcValueStep [join [list 0 $::sth::Bgp::userArgsArray(import_target_assign_step)] :]
        }
        
	return "-$stcAttr $stcValue -$stcAttrStep $stcValueStep"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_addPrefix {handle option value routeIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value"
    
    set ipVersion $::sth::Bgp::userArgsArray(ip_version)
    if {$::sth::Bgp::userArgsArray(max_route_ranges) == 1} {
        set ipStep [string map -nocase {4 "0.0.0.0" 6 "::"} $ipVersion]
    } elseif {[info exists ::sth::Bgp::userArgsArray(route_ip_addr_step)]} {
        set ipStep $::sth::Bgp::userArgsArray(route_ip_addr_step)
    } else {
		return -code error "\"-route_ip_addr_step\" is required when \"max_route_ranges\" is greater than 1."
	}

    if {![::ip::is $ipVersion $value]} {
        return -code error "\"-prefix\" must be a valid IPv$ipVersion address"
    }
    
	set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $option stcattr]
	set stcValue [::sth::sthCore::updateIpAddress $ipVersion $value $ipStep $routeIdx]
	return "-$stcAttr $stcValue"
}

proc ::sth::Bgp::processEmulation_bgp_route_config_checkNullable {handle option value routeIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value"
    
    set optionBase [join [lrange [split $option _] 0 end-1] _]
    
    if {$value == 0} {
        set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $optionBase stcattr]
        return "-$stcAttr null"
    }
}

proc ::sth::Bgp::processEmulation_bgp_route_config_checkEmptyList {handle option value routeIdx} {
    ::sth::sthCore::log debug "Processing switch: -$option $value"
    
    set optionBase [join [lrange [split $option _] 0 end-1] _]
    
    if {$value == 0} {
        set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: emulation_bgp_route_config $optionBase stcattr]
        return "-$stcAttr {}"
    }
}

proc ::sth::Bgp::isBgpRouterHandleValid { handle } {
   # do preliminary search on the router handle since it must exist under the project
    if {[catch {::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-router} allRouters]} {
		return 0
	}
        #the code is wrong here, $handle may be a list. Modify by cf
	#if {[lsearch $allRouters $handle] < 0} {
	#    return 0
	#}
        foreach router $handle {
#           if {[lsearch $allRouters $router] < 0} {
#	          return 0
#	   }
           # verify that bgp exists on the router
            if {[catch {set bgpRouterConfigHandle [::sth::sthCore::invoke stc::get $router -children-BgpRouterConfig]} err]} {
				return 0
		    } elseif {$bgpRouterConfigHandle eq ""} {
				return 0
			}
        }
    
	return 1
}

proc ::sth::Bgp::isBgpRouteConfigHandleValid { routeConfigHandle } {
	if {([string first bgpipv4routeconfig $routeConfigHandle] < 0) && ([string first bgpipv6routeconfig $routeConfigHandle] < 0)} {
		return 0
	}
	if {[catch {::sth::sthCore::invoke stc::get $routeConfigHandle -parent} routerHandleList]} {
		return 0
	}
	if {[string first bgprouterconfig $routerHandleList] < 0} {
		return 0
	}
    return 1
}

# move this to sthutils.tcl
proc ::sth::Bgp::getIpVersionFromStack {deviceHandle} {
    set ipv4IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv4if]
	set ipv6IfHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-ipv6if]
	if {[llength $ipv4IfHandle] > 0 && [llength $ipv6IfHandle] == 0} {
	    return 4
	} elseif {[llength $ipv6IfHandle] > 0 && [llength $ipv4IfHandle] == 0} {
	    return 6
	} else {
	    return 4and6   
	}
}

proc ::sth::Bgp::checkDependency {cmdType option dependentValue} {  
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::Bgp:: $cmdType $option dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::Bgp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $::sth::Bgp::userArgsArray($dependency)]} {
            return -code error "\"-$option\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::Bgp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in bgpTable.tcl
    foreach item $::sth::Bgp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Bgp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Bgp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Bgp:: $cmdType $opt $::sth::Bgp::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::Bgp::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Bgp::userArgsArray($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}


#####################################################
#Supporting Functions for bgp flow spec
#####################################################
proc ::sth::Bgp::processBgpFlowSpecConfigSwitches {userfunName handleList mode retKeyedList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $retKeyedList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    
    foreach deviceHandle $handleList {
        foreach func $functionsToRun {
            switch -- $func {
                configBgpFlowSpecConfig {
                    configBgpFlowSpecConfig $userfunName $deviceHandle $mode
                }
                configBgpVpnRouteConfig {
                    set BgpVpnRouteConfigHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpVpnRouteConfig]
                    if {[string length $BgpVpnRouteConfigHdl] != 0} {
                        configBgpVpnRouteConfig $userfunName $BgpVpnRouteConfigHdl $mode
                    }
                }
                configBgpFsType1DestinationPrefix {
                    set BgpFsType1DestinationPrefixHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType1DestinationPrefix ]
                    if {[string length $BgpFsType1DestinationPrefixHdl] != 0} {
                        configBgpFsType1DestinationPrefix $userfunName $BgpFsType1DestinationPrefixHdl $mode
                    }
                }
                configBgpFsType2SourcePrefix {
                    set configBgpFsType2SourcePrefixHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType2SourcePrefix]
                    if {[string length $configBgpFsType2SourcePrefixHdl] != 0} {
                        configBgpFsType2SourcePrefix $userfunName $configBgpFsType2SourcePrefixHdl $mode
                    }
                }
                configBgpFsOperatorValuePairT4 {
                    set BgpFsType4PortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType4Port]
                    set configBgpFsOperatorValuePairT4Hdl [::sth::sthCore::invoke stc::get $BgpFsType4PortHdl -children-BgpFsOperatorValuePair]
                    if {[string length $configBgpFsOperatorValuePairT4Hdl] != 0} {
                        configBgpFsOperatorValuePairT4 $userfunName $configBgpFsOperatorValuePairT4Hdl $mode
                    }
                }
                configBgpFsOperatorValuePairT5 {
                    set BgpFsType5PortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType5DestinationPort]
                    set configBgpFsOperatorValuePairT5Hdl [::sth::sthCore::invoke stc::get $BgpFsType5PortHdl -children-BgpFsOperatorValuePair]
                    if {[string length $configBgpFsOperatorValuePairT5Hdl] != 0} {
                        configBgpFsOperatorValuePairT5 $userfunName $configBgpFsOperatorValuePairT5Hdl $mode
                    }
                }
                configBgpFsOperatorValuePairT6 {
                    set BgpFsType6PortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType6SourcePort]
                    set configBgpFsOperatorValuePairT6Hdl [::sth::sthCore::invoke stc::get $BgpFsType6PortHdl -children-BgpFsOperatorValuePair]
                    if {[string length $configBgpFsOperatorValuePairT6Hdl] != 0} {
                        configBgpFsOperatorValuePairT6 $userfunName $configBgpFsOperatorValuePairT6Hdl $mode
                    }
                }
                configBgpFsOperatorValuePairT10 {
                    set BgpFsType10PortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType10PacketLength]
                    set configBgpFsOperatorValuePairT10Hdl [::sth::sthCore::invoke stc::get $BgpFsType10PortHdl -children-BgpFsOperatorValuePair]
                    if {[string length $configBgpFsOperatorValuePairT10Hdl] != 0} {
                        configBgpFsOperatorValuePairT10 $userfunName $configBgpFsOperatorValuePairT10Hdl $mode
                    }
                }
                configBgpFsDscpOpValuePair {
                    set BgpFsType11DscpValueHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType11DscpValue]
                    set configBgpFsDscpOpValuePairHdl [::sth::sthCore::invoke stc::get $BgpFsType11DscpValueHdl -children-BgpFsDscpOpValuePair]
                    if {[string length $configBgpFsDscpOpValuePairHdl] != 0} {
                        configBgpFsDscpOpValuePair $userfunName $configBgpFsDscpOpValuePairHdl $mode
                    }
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
    keylset returnKeyedList handles $handleList
    return $returnKeyedList
}


proc ::sth::Bgp::configBgpFlowSpecConfig { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFlowSpecConfig $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpVpnRouteConfig { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpVpnRouteConfig $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsType1DestinationPrefix { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsType1DestinationPrefix $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsType2SourcePrefix { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsType2SourcePrefix $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsOperatorValuePairT4 { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsOperatorValuePairT4 $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsOperatorValuePairT5 { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsOperatorValuePairT5 $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsOperatorValuePairT6 { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsOperatorValuePairT6 $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsOperatorValuePairT10 { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsOperatorValuePairT10 $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}


proc ::sth::Bgp::configBgpFsDscpOpValuePair { userfunName handle mode } {

    set optionValueList [getStcOptionValueList $userfunName configBgpFsDscpOpValuePair $mode $handle 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}



###################################################################
#functions for emulation_bgp_route_element_config:add modify remove 
###################################################################

proc ::sth::Bgp::emulation_bgp_route_element_config_add { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_element_config_add $rklName"
	
	upvar 1 $rklName returnKeyedList
    set elementHandle 0
    set handle 0
	
	if {![info exists ::sth::Bgp::userArgsArray(handle)] && ![info exists ::sth::Bgp::userArgsArray(element_type)]} {
        return -code error "the \"-handle\" and \"-element_type\" are mandatory in add mode"
	} else {
		set handle  $::sth::Bgp::userArgsArray(handle)
		set elementType  $::sth::Bgp::userArgsArray(element_type)
	}
    
    #In future we can have switch
    #fs_type4 fs_type5 fs_type6 fs_type10 fs_type11
    if {[regexp -nocase "fs_" $elementType]} {
        processBgpFlowSpecElementConfigSwitches emulation_bgp_route_element_config $handle $elementHandle add returnKeyedList 
    }
   
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



proc ::sth::Bgp::emulation_bgp_route_element_config_modify { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_element_config_modify $rklName"
	
	upvar 1 $rklName returnKeyedList
    set elementHandle 0
    set handle 0
	
	if {![info exists ::sth::Bgp::userArgsArray(element_handle)] && ![info exists ::sth::Bgp::userArgsArray(element_type)]} {
        return -code error "the \"-element_handle\" and \"-element_type\" are mandatory in modify mode"
	} else {
		set elementHandle  $::sth::Bgp::userArgsArray(element_handle)
		set elementType  $::sth::Bgp::userArgsArray(element_type)
	}

    #In future we can have switch
    #fs_type4 fs_type5 fs_type6 fs_type10 fs_type11
    if {[regexp -nocase "fs_" $elementType]} {
        processBgpFlowSpecElementConfigSwitches emulation_bgp_route_element_config $handle $elementHandle modify returnKeyedList 
    }
   
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Bgp::emulation_bgp_route_element_config_remove { rklName } {
    ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::Bgp::emulation_bgp_route_element_config_remove $rklName"
	
	upvar 1 $rklName returnKeyedList
	
	if {[info exists ::sth::Bgp::userArgsArray(element_handle)]} {
        set handleList $::sth::Bgp::userArgsArray(element_handle)
	} else {
        return -code error "the switch \"-element_handle\" is mandatory in remove mode"
    }
	
    ::sth::sthCore::invoke stc::perform deletecommand -configlist "$handleList"
	
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
}


proc ::sth::Bgp::processBgpFlowSpecElementConfigSwitches {userfunName parHandle parelementHandle mode retKeyedList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $retKeyedList returnKeyedList
    
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    #parHandle is Fs handle
    foreach deviceHandle $parHandle {
        foreach func $functionsToRun {
            switch -- $func {
                configBgpFsOperatorValuePairT4 {
                    if {$mode == "add"} {
                        set BgpFsType4PortHdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType4Port]
                        set configBgpFsOperatorValuePairT4Hdl [::sth::sthCore::invoke stc::create BgpFsOperatorValuePair -under $BgpFsType4PortHdl]
                        configBgpFsOperatorValuePairT4 $userfunName $configBgpFsOperatorValuePairT4Hdl $mode
                        keylset returnKeyedList handles $configBgpFsOperatorValuePairT4Hdl
                    } elseif {$mode == "modify"} {
                        foreach eleHandle $parelementHandle {
                            set configBgpFsOperatorValuePairT4Hdl $eleHandle
                            configBgpFsOperatorValuePairT4 $userfunName $configBgpFsOperatorValuePairT4Hdl $mode
                            keylset returnKeyedList handles $configBgpFsOperatorValuePairT4Hdl
                        }
                    }
                }
                configBgpFsOperatorValuePairT5 {
                    if {$mode == "add"} {
                        set BgpFsType5Hdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType5DestinationPort]
                        set configBgpFsOperatorValuePairT5Hdl [::sth::sthCore::invoke stc::create BgpFsOperatorValuePair -under $BgpFsType5Hdl]
                        configBgpFsOperatorValuePairT5 $userfunName $configBgpFsOperatorValuePairT5Hdl $mode
                        keylset returnKeyedList handles $configBgpFsOperatorValuePairT5Hdl
                    } elseif {$mode == "modify"} {
                        foreach eleHandle $parelementHandle {
                            set configBgpFsOperatorValuePairT5Hdl $eleHandle
                            configBgpFsOperatorValuePairT5 $userfunName $configBgpFsOperatorValuePairT5Hdl $mode
                            keylset returnKeyedList handles $configBgpFsOperatorValuePairT5Hdl
                        }
                    } 
                }
                configBgpFsOperatorValuePairT6 {
                    if {$mode == "add"} {
                        set BgpFsType6Hdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType6SourcePort]
                        set configBgpFsOperatorValuePairT6Hdl [::sth::sthCore::invoke stc::create BgpFsOperatorValuePair -under $BgpFsType6Hdl]
                        configBgpFsOperatorValuePairT6 $userfunName $configBgpFsOperatorValuePairT6Hdl $mode
                        keylset returnKeyedList handles $configBgpFsOperatorValuePairT6Hdl
                    } elseif {$mode == "modify"} {
                        foreach eleHandle $parelementHandle {
                            set configBgpFsOperatorValuePairT6Hdl $eleHandle
                            configBgpFsOperatorValuePairT6 $userfunName $configBgpFsOperatorValuePairT6Hdl $mode
                            keylset returnKeyedList handles $configBgpFsOperatorValuePairT6Hdl
                        }
                    }
                }
                configBgpFsOperatorValuePairT10 {
                    if {$mode == "add"} {
                        set BgpFsType10Hdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType10PacketLength]
                        set configBgpFsOperatorValuePairT10Hdl [::sth::sthCore::invoke stc::create BgpFsOperatorValuePair -under $BgpFsType10Hdl]
                        configBgpFsOperatorValuePairT10 $userfunName $configBgpFsOperatorValuePairT10Hdl $mode
                        keylset returnKeyedList handles $configBgpFsOperatorValuePairT10Hdl
                    } elseif {$mode == "modify"} {
                        foreach eleHandle $parelementHandle {
                            set configBgpFsOperatorValuePairT10Hdl $eleHandle
                            configBgpFsOperatorValuePairT10 $userfunName $configBgpFsOperatorValuePairT10Hdl $mode
                            keylset returnKeyedList handles $configBgpFsOperatorValuePairT10Hdl
                        }
                    }
                }
                configBgpFsDscpOpValuePair {
                    if {$mode == "add"} {
                        set BgpFsType11Hdl [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpFsType11DscpValue]
                        set configBgpFsDscpOpValuePairT11Hdl [::sth::sthCore::invoke stc::create BgpFsDscpOpValuePair -under $BgpFsType11Hdl]
                        configBgpFsDscpOpValuePair $userfunName $configBgpFsDscpOpValuePairT11Hdl $mode
                        keylset returnKeyedList handles $configBgpFsDscpOpValuePairT11Hdl
                    } elseif {$mode == "modify"} {
                        foreach eleHandle $parelementHandle {
                            set configBgpFsDscpOpValuePairT11Hdl $eleHandle
                            configBgpFsDscpOpValuePair $userfunName $configBgpFsDscpOpValuePairT11Hdl $mode
                            keylset returnKeyedList handles $configBgpFsDscpOpValuePairT11Hdl
                        }
                    }
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
    }
    return $returnKeyedList
}

#####################################################
#Supporting Functions for bgp srte policy config
#####################################################
proc ::sth::Bgp::processBgpSrTePolicyConfig {userfunName handleList mode retKeyedList} {
    set procName [lindex [info level [info level]] 0]
    variable ::sth::Bgp::sortedSwitchPriorityList
    variable ::sth::Bgp::userArgsArray
    upvar 1 $retKeyedList returnKeyedList
    set functionsToRun ""
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: Argument \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            # lappend the function
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Bgp:: $userfunName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Bgp:: $userfunName $switchname $mode]
            if {[lsearch $functionsToRun $func] == -1} {
                if {[regexp -nocase "srte" $func]} {
                    lappend functionsToRun $func
                }
            }
        }
    }
	set funList "configSrTePolicy configSrTePolicyAttribute configSrTePolicyTlvTypeConfig configSrTePolicySgListAttribute \
			configSrTePolicySgListAttributeType1 configSrTePolicySgListAttributeType2 configSrTePolicySgListAttributeType3 configSrTePolicySgListAttributeType4 \
			configSrTePolicySgListAttributeType5 configSrTePolicySgListAttributeType6 configSrTePolicySgListAttributeType7 configSrTePolicySgListAttributeType8"
	foreach funListElement $funList {
		foreach functionRun $functionsToRun {
			if {$funListElement == "$functionRun"} {
				lappend newlistFunc $functionRun
			}
	}
	}
    foreach deviceHandle $handleList {
        set typeHadles ""
        foreach func $newlistFunc {
			if {$func == "configSrTePolicy"} {
                    configSrTePolicy $userfunName $deviceHandle $mode
            } elseif {$func == "configSrTePolicyAttribute"} {
            	       configSrTePolicyAttribute $userfunName $deviceHandle $mode
            } elseif {$func == "configSrTePolicyTlvTypeConfig"} {
            	    configSrTePolicyTlvTypeConfig $userfunName $deviceHandle $mode
            } elseif {$func == "configSrTePolicySgListAttribute"} {
                    if { [info exists ::sth::Bgp::userArgsArray(route_handle)] } {
                        if { $mode == "add"} {
                            #need to provicde bgpsrtehandle in route_handle to add segment PolicySgListAttribute..from second time it will have more than one handle ..so getting/appending the children handles
                            set bgpSrTePolicySgListAttributeHandle [::sth::sthCore::invoke stc::create BgpSrTePolicySgListAttribute -under $deviceHandle]
                            configSrTePolicySgListAttribute $userfunName $bgpSrTePolicySgListAttributeHandle $mode
							set deviceHandle $bgpSrTePolicySgListAttributeHandle
                        } elseif {$mode == "modify"} {
                            configSrTePolicySgListAttribute $userfunName $deviceHandle $mode
                        }
                    } else {
                        #First time by default it will have only one segment handle - getting automatically created children segment handle from bgpsrtehandle1
                        set bgpSrTePolicySgListAttributeHandle [::sth::sthCore::invoke stc::get $deviceHandle -children-BgpSrTePolicySgListAttribute]
                        configSrTePolicySgListAttribute $userfunName $bgpSrTePolicySgListAttributeHandle $mode
						set deviceHandle $bgpSrTePolicySgListAttributeHandle
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType1"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType1Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType1 -under $deviceHandle]
                        configSrTePolicySgListAttributeType1 $userfunName $BgpSrTePolicySegmentType1Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType1Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType1 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType3"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType3Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType3 -under $deviceHandle]
                        configSrTePolicySgListAttributeType3 $userfunName $BgpSrTePolicySegmentType3Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType3Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType3 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType5"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType5Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType5 -under $deviceHandle]
                        configSrTePolicySgListAttributeType5 $userfunName $BgpSrTePolicySegmentType5Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType5Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType5 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType6"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType6Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType6 -under $deviceHandle]
                        configSrTePolicySgListAttributeType6 $userfunName $BgpSrTePolicySegmentType6Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType6Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType6 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType2"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType2Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType2 -under $deviceHandle]
                        configSrTePolicySgListAttributeType2 $userfunName $BgpSrTePolicySegmentType2Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType2Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType2 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType4"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType4Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType4 -under $deviceHandle]
                        configSrTePolicySgListAttributeType4 $userfunName $BgpSrTePolicySegmentType4Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType4Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType4 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType7"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType7Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType7 -under $deviceHandle]
                        configSrTePolicySgListAttributeType7 $userfunName $BgpSrTePolicySegmentType7Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType7Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType7 $userfunName $deviceHandle $mode
                    }
            } elseif {$func == "configSrTePolicySgListAttributeType8"} {
                    if { $mode == "add"} {
                        set BgpSrTePolicySegmentType8Handle [::sth::sthCore::invoke stc::create BgpSrTePolicySegmentType8 -under $deviceHandle]
                        configSrTePolicySgListAttributeType8 $userfunName $BgpSrTePolicySegmentType8Handle $mode
                        lappend typeHadles $BgpSrTePolicySegmentType8Handle
                    } elseif {$mode == "modify"} {
                        configSrTePolicySgListAttributeType8 $userfunName $deviceHandle $mode
                    }
            } else {
                ::sth::sthCore::processError returnKeyedList "Error in $procName: unknown function: $func" {}
                return -code error $returnKeyedList 
            }
        }
        if {$mode == "add"} {
            if {$typeHadles != "" && [info exists bgpSrTePolicySgListAttributeHandle]} {
                #while creating subtlv under segment
                keylset returnKeyedList bgp_srte_segment_list_handles.$bgpSrTePolicySgListAttributeHandle "$typeHadles"
            } elseif {$typeHadles == "" && [info exists bgpSrTePolicySgListAttributeHandle]} {
                #while creating only segment list without subtlv
                keylset returnKeyedList bgp_srte_segment_list_handles    $bgpSrTePolicySgListAttributeHandle
            } elseif {$typeHadles != ""} {
                #while creating only subtlv under segment handle with out creating segment handle. By providing existing segment handle
                keylset returnKeyedList bgp_srte_segment_list_handles.$deviceHandle   $typeHadles 
            }
        }
    }
    keylset returnKeyedList handles $handleList
    return $returnKeyedList
}

proc ::sth::Bgp::configSrTePolicy {userfunName handle mode} {
   
    #configure SrTePolicy
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicy $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicyAttribute {userfunName handle mode} {
    
    set bgpSrTePolicyAttributeHandle [::sth::sthCore::invoke stc::get $handle -children-BgpSrTePolicyAttribute]
   
    #configure SrTePolicyAttribute
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicyAttribute $mode $bgpSrTePolicyAttributeHandle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpSrTePolicyAttributeHandle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttribute {userfunName segmentHandle mode} {

    #configure SrTePolicySgListAttribute - segment list handle
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttribute $mode $segmentHandle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $segmentHandle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicyTlvTypeConfig {userfunName handle mode} {
   
    set bgpSrTePolicyTlvTypeConfigHandle [::sth::sthCore::invoke stc::get $handle -children-BgpSrTePolicyTlvTypeConfig]
    
    #configure SrTePolicySgListAttribute
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicyTlvTypeConfig $mode $bgpSrTePolicyTlvTypeConfigHandle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $bgpSrTePolicyTlvTypeConfigHandle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType6 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType6
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType6 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType5 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType5
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType5 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType3 {userfunName handle mode} {
   
    #configure SrTePolicySgListAttributeType3
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType3 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType1 {userfunName handle mode} {
   
    #configure SrTePolicySgListAttributeType1
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType1 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType2 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType2
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType2 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType4 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType4
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType4 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType7 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType7
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType7 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::Bgp::configSrTePolicySgListAttributeType8 {userfunName handle mode} {
    
    #configure SrTePolicySgListAttributeType8
    set optionValueList [getStcOptionValueList $userfunName configSrTePolicySgListAttributeType8 $mode $handle 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}
