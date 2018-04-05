# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::rip {
    variable sessionType
    variable rip_subscription_state 0
    variable ipv4Version 4
}
proc ::sth::rip::emulation_rip_config_create {returnKeyedListVarName {level 1}} {
        variable userArgsArray
        variable sessionType
        variable rip_subscription_state
        variable ipv4Version
        
        upvar $level $returnKeyedListVarName returnKeyedList
        
        set routerList [list]
        if {[info exists userArgsArray(port_handle)]} {
            switch -exact -- $userArgsArray(session_type) {
                "ripv1" -
                "ripv2" { set ipVersion 4 }
                "ripng" { set ipVersion 6 }
                default {
                    ::sth::sthCore::processError returnKeyedList \
                        [concat "Error:  Unknown session_type $userArgsArray(session_type)."]
                    return $returnKeyedList
                }
            }
    
            set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
            set vlanOuter [regexp -- {vlan_outer} $userArgsArray(optional_args)]
    
            #setup global address/step/id params, put return value in 'device'
            set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]
            #call to setup routerid and routeridstep
            set deviceSettings [GetDeviceAddrSettings $ipVersion]
            ::sth::sthCore::invoke stc::config $device $deviceSettings

            array unset router
            if {![info exists userArgsArray(count)]} {
                set userArgsArray(count) 1
            }
            for {set i 1} {$i <= $userArgsArray(count)} {incr i} {
                if {[catch {
                    # create the router
                    set router($i) [::sth::sthCore::invoke stc::create Router -under $::sth::GBLHNDMAP(project)]
                    #store the information for later use
                    set sessionType($router($i)) $userArgsArray(session_type)
    
                    # configure the router id
                    if {[info exists userArgsArray(router_id)] == 1} {
                        if {[info exists userArgsArray(router_id_step)] == 0} {
                            set newrouterid [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) 0.0.0.0 [expr $i-1]]
                        } else {
                            set newrouterid \
                                [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) $userArgsArray(router_id_step) [expr $i-1]]
                        }
                        set routerSettings "-RouterId $newrouterid"
                        ::sth::sthCore::invoke stc::config $router($i) $routerSettings
                    }
                    # create the ethernet stack for RIP router, the mac use in setup in device setttings
                    #add for ATM. if ATM option is provided, don't need to create ethiiif
                    if {[info exists userArgsArray(vpi)] ==1 || [info exists userArgsArray(vci)] ==1} {
                        set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $router($i)]
                        set atmSettings [getAtmSettings [expr $i-1]]
                        ::sth::sthCore::invoke stc::config $atmResultIf $atmSettings
                    } else {
                        set ethResultIf [::sth::sthCore::invoke stc::create EthIIIf -under $router($i)]
                        
                        ##auto aggsin the unique mac addr
                        if {[info exists userArgsArray(mac_address_start)]} {
                            set value $userArgsArray(mac_address_start)
                        } else {
                            set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
                            set value [::sth::sthCore::invoke stc::get $addrOption -NextMac]
                        }
                           
                        set srcMac [::sth::sthCore::macStep $value "00:00:00:00:00:01" [expr $i -1]]
        
                        set optionValueList "-SourceMac $srcMac"
        
                        if {$i == $userArgsArray(count)} {
                            set nextMac [::sth::sthCore::macStep $srcMac "00:00:00:00:00:01" 1]                        
                            set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
                            ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
                        }
                        ::sth::sthCore::invoke stc::config $ethResultIf $optionValueList
                    }
    
                    # configure vlan if option is provided
                    if {$vlanOptFound} {
                        set vlan userArgsArray(vlan_id)
                        set vlanResultIf [::sth::sthCore::invoke stc::create VlanIf -under $router($i)]
                        set vlanIfSettings [GetVlanIntfSetup $vlanResultIf [expr {$i-1}]]
                        ::sth::sthCore::invoke stc::config $vlanResultIf $vlanIfSettings
                        #add QinQ
                        if {$vlanOuter == 1} {
                            set vlanOuterIf [::sth::sthCore::invoke stc::create VlanIf -under $router($i)]
                            set vlanOuterSettings [GetVlanOuterSetup $vlanOuterIf [expr {$i-1}]]
                   
                            ::sth::sthCore::invoke stc::config $vlanOuterIf $vlanOuterSettings
                        }
                    }
                
                    if {![info exists userArgsArray(vlan_id)] && $vlanOuter == 1} {
                        ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $hostHandle. To enable VLAN, specify -vlan_id"
                        return $returnKeyedList
                    }
                
                    # configure the ip stack for RIP router
                    set ipResultIf [::sth::sthCore::invoke stc::create Ipv[string trim $ipVersion]If -under $router($i)]
    
                    set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(intf_ip_addr_step)]
                    set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(intf_ip_addr) $ipstep [expr $i-1]]
                    set ipifSettings [GetIPIntfSetup $ipResultIf $newipaddr]
                    ::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
    
                    #configure gateway ip for router
                    if {[info exists userArgsArray(gateway_ip_addr)] == 1} {
                        if {[info exists userArgsArray(gateway_ip_addr_step)] == 0} {
                            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(gateway_ip_addr) 0.0.0.0 0]
                        } else {
                            set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(gateway_ip_addr_step)]
                            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(gateway_ip_addr) $ipstep [expr $i-1]]
                        }
                        set ipifSettings "-Gateway $newipaddr"
                        ::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
                    }
    
                    #configure a link local stack in case of ipv6
                    if {$ipVersion == 6} {
                        set linkLocalHandle [::sth::sthCore::invoke stc::create Ipv[string trim $ipVersion]If -under $router($i)]
                        set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(link_local_intf_ip_addr_step)]
                        set ipaddr [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(link_local_intf_ip_addr)]
                        set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $ipaddr $ipstep [expr $i-1]]
                        set linkLocalSettings [GetLinkLocalIntfSetup $linkLocalHandle $newipaddr]
                        ::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
                    }
                                                         
		            set ripRtrCfg [::sth::sthCore::invoke "stc::create RipRouterConfig -under $router($i) -ripVersion V2"]

                    set rip_router_settings [GetRipRouterConfigSettings $ripRtrCfg]
                    ::sth::sthCore::invoke stc::config $ripRtrCfg $rip_router_settings
                    
                    if {[info exists userArgsArray(neighbor_intf_ip_addr_step)] && [info exists userArgsArray(neighbor_intf_ip_addr)]} {
                        set userArgsArray(neighbor_intf_ip_addr) [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(neighbor_intf_ip_addr) $userArgsArray(neighbor_intf_ip_addr_step) 1]
                    }
                    # setup authentication
                    set ripauthenticationparams [::sth::sthCore::invoke stc::get $ripRtrCfg -children-ripauthenticationparams]
                    set authen_settings [GetAuthenSettings $ripRtrCfg]
                    ::sth::sthCore::invoke stc::config $ripauthenticationparams $authen_settings
                                                         
                    #enable/disable BFD
                    if {[info exists ::sth::rip::userArgsArray(bfd_registration)]} {
                    
                        configBfdRegistration $router($i) $userArgsArray(mode)
                    }
                
                    # setup relations
                    ::sth::sthCore::invoke stc::config $router($i) "-AffiliationPort-targets $userArgsArray(port_handle)"
                
                    #adjust the stack for vlan relation. If there is atmif, VLANif is not allowed.
                    if { [info exists atmResultIf] } {
                        set lowerIf $atmResultIf
                        set baseIf $atmResultIf
                    } else {
                        set lowerIf $ethResultIf
                        set baseIf $ethResultIf
                    }
                
                    #add QinQ
                    if {$vlanOptFound && ![info exists atmResultIf] } {
                        if {$vlanOuter} {
                            ::sth::sthCore::invoke stc::config $vlanOuterIf "-StackedOnEndpoint-targets $lowerIf"
                            ::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $vlanOuterIf"
                            set lowerIf $vlanResultIf
                        } else {
                            ::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $lowerIf"
                            set lowerIf $vlanResultIf
                        }
                    }
                
                
                    ###adjust the stack for gre relation&& 
                    if {[info exists userArgsArray(tunnel_handle)] != 0} {
                       if {[catch {::sth::createGreStack $userArgsArray(tunnel_handle) $router($i) $lowerIf $i } returnIf]} {
                          return -code error "Internal error: failed to create Gre Stack"
                        } else {
                            set lowerIf $returnIf
                        }
                    }
                    
                    ::sth::sthCore::invoke stc::config $ipResultIf "-StackedOnEndpoint-targets $lowerIf"
                
                
                    #adjust the stack for link local stack relation
                    if {$ipVersion == 6} {
                        set ipstacking "$ipResultIf $linkLocalHandle"
                    } else {
                        set ipstacking "$ipResultIf"
                    }
                    ::sth::sthCore::invoke stc::config $router($i) -TopLevelIf-targets "$ipstacking"
                    ::sth::sthCore::invoke stc::config $router($i) -PrimaryIf-targets "$ipstacking"
                    if {$ipVersion == 6} {
                        ::sth::sthCore::invoke stc::config $linkLocalHandle "-StackedOnEndpoint-targets $lowerIf"
                    }
                    ::sth::sthCore::invoke stc::config $ripRtrCfg "-UsesIf-targets $ipResultIf"
                    #BFD relation
                    set bfdRtrCfg [::sth::sthCore::invoke stc::get $router($i) -children-bfdrouterconfig]
                    if {[llength $bfdRtrCfg] != 0} {
                        ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
                    }
            
                } routerConfigErr]} {
                    ::sth::sthCore::invoke stc::delete $router($i)
                return -code error $routerConfigErr
                }
                
                lappend routerList $router($i)
            }
    
     
        } elseif {[info exists userArgsArray(handle)]} {
    
            set ripRouters $userArgsArray(handle)
            set routerList $ripRouters
            
            foreach ripRouter $ripRouters {
                if {[set ipv6If [::sth::sthCore::invoke stc::get $ripRouter -children-ipv6if]] != ""} {
                    set ipv4Version 6
                } else {
                    set ipv4Version 4
                }

                #store the information for later use
                set sessionType($ripRouter) $userArgsArray(session_type)

                if {[::sth::sthCore::invoke stc::get $ripRouter -children-RipRouterConfig] != ""} {
                    ::sth::sthCore::processError returnKeyedList "$ripRouter already has RIP enable" {}
                    return -code error "$ripRouter already has RIP enable"
                }
                #puts "pleas be noted RIP will be enable in the Device $ripRouter"
                array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $ripRouter  -CreateClassId [string tolower RipRouterConfig]]
                set ripRtrCfg $ProtocolCreateOutput(-ReturnList)
                set rip_router_settings [GetRipRouterConfigSettings $ripRtrCfg]
                ::sth::sthCore::invoke stc::config $ripRtrCfg $rip_router_settings
                
                # setup authentication
                set ripauthenticationparams [::sth::sthCore::invoke stc::get $ripRtrCfg -children-ripauthenticationparams]
                set authen_settings [GetAuthenSettings $ripRtrCfg]
                ::sth::sthCore::invoke stc::config $ripauthenticationparams $authen_settings
                
                #enable/disable BFD
                if {[info exists ::sth::rip::userArgsArray(bfd_registration)]} {
                    configBfdRegistration $ripRouter $userArgsArray(mode)
                }
                set ipResultIf [::sth::sthCore::invoke stc::get $ripRouter  -PrimaryIf-Targets]
                if {$ipv4Version== 6} {
                    foreach ipif $ipResultIf {
                        set addr [::sth::sthCore::invoke stc::get  $ipif -Address]
                            if {![regexp -nocase "FE80" $addr] } {
                                set ipResultIf $ipif
                                break
                            }
                    }
                }
                set bfdRtrCfg [::sth::sthCore::invoke stc::get $ripRouter -children-bfdrouterconfig]
                if {[llength $bfdRtrCfg] != 0} {
                    ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
                }
                if {[info exists userArgsArray(neighbor_intf_ip_addr_step)] && [info exists userArgsArray(neighbor_intf_ip_addr]} {set userArgsArray(neighbor_intf_ip_addr) [::sth::sthCore::updateIpAddress $ipv4Version $userArgsArray(neighbor_intf_ip_addr)  $userArgsArray(neighbor_intf_ip_addr_step) 1]}
            }
        } else {
            return -code error "Error: Please at least specify -port_handle or -handle."
        } 
    
        if {$rip_subscription_state == 0} {
            # Create the RIP result dataset
            set ripResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set ripResultQuery [::sth::sthCore::invoke stc::create "ResultQuery" \
                           -under $ripResultDataSet \
                           -ResultRootList $::sth::GBLHNDMAP(project) \
                           -ConfigClassId RipRouterConfig \
                           -ResultClassId RipRouterResults]
            # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $ripResultDataSet
            set rip_subscription_state 1
        }
        keylset returnKeyedList handle $routerList
        keylset returnKeyedList handles $routerList

        return $::sth::sthCore::SUCCESS
}

proc ::sth::rip::emulation_rip_config_inactive {returnKeyedListVarName {level 1}} {
        variable userArgsArray
        
        if {[info exists userArgsArray(handle)]==0} {
            return -code error "Error: Missing a mandatory attribute -handle for inactive mode."
        }
        upvar $level $returnKeyedListVarName returnKeyedList
        set  ripRouters $userArgsArray(handle)

        foreach ripRouter $ripRouters {
            set ripRtrCfg [::sth::sthCore::invoke stc::get $ripRouter "-children-RipRouterConfig"]
            ::sth::sthCore::invoke stc::config $ripRtrCfg "-Active FALSE -LocalActive FALSE"
        }
        keylset returnKeyedList handle   $ripRouters
        keylset returnKeyedList handles $ripRouters
        return $::sth::sthCore::SUCCESS
}

proc ::sth::rip::emulation_rip_config_active {returnKeyedListVarName {level 1}} {
        variable userArgsArray
        
        if {[info exists userArgsArray(handle)]==0} {
            return -code error "Error: Missing a mandatory attribute -handle for active mode."
        }
        upvar $level $returnKeyedListVarName returnKeyedList
        set  ripRouters $userArgsArray(handle)
        
        foreach ripRouter $ripRouters {
            set ripRtrCfg [::sth::sthCore::invoke stc::get $ripRouter "-children-RipRouterConfig"]
            ::sth::sthCore::invoke stc::config $ripRtrCfg "-Active TRUE -LocalActive TRUE "
        }
        
        keylset returnKeyedList handle   $ripRouters
        keylset returnKeyedList handles $ripRouters
        return $::sth::sthCore::SUCCESS
}


proc ::sth::rip::emulation_rip_config_modify {returnKeyedListVarName {level 1}} {
  variable userArgsArray
  variable sessionType
  variable ipv4Version
  variable sortedSwitchPriorityList
  
  if {[info exists userArgsArray(handle)]==0} {
     return -code error "Error: Missing a mandatory attribute -handle."
  }
  upvar $level $returnKeyedListVarName returnKeyedList
  if {[info exists userArgsArray(session_type)]==0} {
      return -code error "Error: Missing a mandatory attribute -session_type."
  }
  
  if {[info exists userArgsArray(count)]} {
      return -code error "Error: Attribute -count is not valid in modify mode."
  }
  set unsupportedModifyOptions {port_handle count}

  #the count option has default value, always exist. comment by cf
  #if {[info exists userArgsArray(count)]} {
  #    return -code error "Error: Attribute -count is not valid in modify mode."
  #}
  set retVal [catch {
    foreach item $::sth::rip::sortedSwitchPriorityList {
        foreach {priority switchName} $item {
            if {[lsearch $unsupportedModifyOptions $switchName] > -1} {
                ::sth::sthCore::processError returnKeyedList "Error: unable to modify the \"-$switchName\" in modify mode." {}
                return -code error $returnKeyedList
            }
        }
    }
    
     switch -exact -- $userArgsArray(session_type) {
        "ripv1" -
        "ripv2" { set ipVersion 4 }
        "ripng" { set ipVersion 6 }
        default {
           ::sth::sthCore::processError returnKeyedList [concat "Error:  Unknown session_type $userArgsArray(session_type)."]
           return $returnKeyedList
        }
     }
    set router $userArgsArray(handle)

    set ethiiIf [::sth::sthCore::invoke stc::get $router -children-ethiiIf]
    #add for ATM. in ATM case, there will be no ethiiIf
    if { $ethiiIf != ""} {
        if {[info exists userArgsArray(mac_address_start)]} {
            set ethifSettings "-SourceMac $userArgsArray(mac_address_start)"
            ::sth::sthCore::invoke stc::config $ethiiIf $ethifSettings
        }
    }
    
    #add for ATM. config the aal5if
    set atmIf [::sth::sthCore::invoke stc::get $router -children-aal5If]
    if { $atmIf != ""} {
       set atmSettings [getAtmSettings 0]
       ::sth::sthCore::invoke stc::config $atmIf $atmSettings
    }

    set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
    set vlanOuter [regexp -- {vlan_outer} $userArgsArray(optional_args)]

    if {[info exists userArgsArray(router_id)]} {
        sth::sthCore::invoke stc::config $router "-routerId $userArgsArray(router_id)"
    }
    #if there is aal5if, vlan is not allowed
    if {$vlanOptFound && ($atmIf == "")} {
        set vlanInnerIf ""
        set vlanOuterIf ""
        set vlanIfObjHandle [::sth::sthCore::invoke stc::get $router -children-vlanif]
        if {[llength $vlanIfObjHandle] == 0} {
            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $router."
	    return $::sth::sthCore::FAILURE
        }
        set vlanInnerIf $vlanIfObjHandle
        if {[llength $vlanIfObjHandle] > 1} {
            set vlanInnerIf [lindex $vlanIfObjHandle 0]
        }
        set vlanIfSettings [GetVlanIntfSetup $vlanInnerIf 0]
        ::sth::sthCore::invoke stc::config $vlanInnerIf $vlanIfSettings
        #add QinQ
        if {$vlanOuter} {
            if {[llength $vlanIfObjHandle] < 2} {
                ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $hostHandle."
		return $::sth::sthCore::FAILURE
            }
            set vlanOuterIf [lindex $vlanIfObjHandle 1]
            
            set vlanOuterSettings [GetVlanOuterSetup $vlanOuterIf 0]
            
            ::sth::sthCore::invoke stc::config $vlanOuterIf $vlanOuterSettings
        }
    }
    
    ###rewrote for gre case
    set ipResultIf [::sth::sthCore::invoke stc::get $router -TopLevelIf-targets]
    array unset v6temp 
    foreach ipif $ipResultIf {
        array set v6temp [::sth::sthCore::invoke stc::get $ipif]
        if {![string match -nocase "*fe80*" $v6temp(-Address)]} { 
            set ipResultIf $ipif
        } else {
            set linklocalstack $ipif
        }
    }
    if {[info exists userArgsArray(intf_ip_addr)] == 1} {
        if {[info exists userArgsArray(intf_ip_addr_step)] == 0} {
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(intf_ip_addr) 0.0.0.0 0]
        } else { 
            set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(intf_ip_addr_step)]
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(intf_ip_addr) $ipstep 0]
        }
       
        set ipifSettings [GetIPIntfSetup $ipResultIf $newipaddr]
        ::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
    }
    #configure gateway ip for router
    if {[info exists userArgsArray(gateway_ip_addr)] == 1} {
        if {[info exists userArgsArray(gateway_ip_addr_step)] == 0} {
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(gateway_ip_addr) 0.0.0.0 0]
        } else {
            set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(gateway_ip_addr_step)]
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $userArgsArray(gateway_ip_addr) $ipstep 0]
        }
        set ipifSettings "-Gateway $newipaddr"
        ::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
    }

    set ipResultIf [::sth::sthCore::invoke stc::get $router -children-ipv[string trim $ipVersion]if]
    #when ipv6 is supported, two ip interfaces is return where the second is the link local stack.
    if {$ipVersion == 6} {
        array set v6temp [::sth::sthCore::invoke stc::get $linklocalstack]
        if {[string match -nocase "*fe80*" $v6temp(-Address)]} { 
            set linkLocalHandle $ipif 
            set ipstep [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(link_local_intf_ip_addr_step)]
            set ipaddr [GetAssociatedItem $userArgsArray(session_type) $userArgsArray(link_local_intf_ip_addr)]
            set newipaddr [::sth::sthCore::updateIpAddress $ipVersion $ipaddr $ipstep 0]
            set linkLocalSettings [GetLinkLocalIntfSetup $linkLocalHandle $newipaddr]
            ::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
        } else {
            set ipResultIf $ipif
        }
        array unset v6temp 
    }
    
    ### add for gre. Modify the gre
    if {[info exists userArgsArray(tunnel_handle)] != 0} {
        if {[catch {::sth::configGreStack  $userArgsArray(tunnel_handle) $router} err]} {
            		return -code error "unable to config gre stack"
            	}
    }

    #enable/disable BFD
    if {[info exists userArgsArray(bfd_registration)]} {
        configBfdRegistration $router $userArgsArray(mode)
    }
    
    set ripRtrCfg [::sth::sthCore::invoke stc::get $router -children-riprouterconfig]

    set rip_router_settings [GetRipRouterConfigSettings $ripRtrCfg]
    ::sth::sthCore::invoke stc::config $ripRtrCfg $rip_router_settings
    
     keylset returnKeyedList handle $userArgsArray(handle)
     keylset returnKeyedList handles $userArgsArray(handle)
  } returnedString]

  return -code $retVal $returnedString
}

proc ::sth::rip::configBfdRegistration {rtrHandle mode} {
    variable userArgsArray
   
    set ripRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-riprouterconfig]
    
    if {$userArgsArray(bfd_registration) == "1"} {
        #create new bfdrouterconfig if no exiting bfd found
        set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
        if {[llength $bfdrtrcfg] == 0} {
            set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]
        }
        ::sth::sthCore::invoke stc::config $ripRtrHandle "-EnableBfd true"
    } else {
        ::sth::sthCore::invoke stc::config $ripRtrHandle "-EnableBfd false"
    }
}  


proc ::sth::rip::GetAssociatedItem {session_type attribute} {
    #return value assocated to the atrribute based on desired sesssion (version) type.
    foreach {key keyVal} $attribute {
        if {$key == $session_type} {
            return $keyVal
        }
    } 
    return $attribute
}

proc ::sth::rip::GetRipRouterConfigSettings {ripRouteConfig} {
    variable userArgsArray
    variable sessionType
    set RipRouterConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            session_type {
                if {$val == "ripng"} {
                    lappend RipRouterConfig "-RipVersion" "NG"
                } elseif {$val == "ripv1"} {
                    lappend RipRouterConfig "-RipVersion" "V1"
                } else {
                    lappend RipRouterConfig "-RipVersion" "V2"
                }
            }
            send_type { 
                #handle outside of this proc.
                #DutIpv4Addr, DutIpv6Addr
                set sendtype [GetAssociatedItem $userArgsArray(session_type) $val]
                lappend RipRouterConfig "-UpdateType" "$sendtype"
                if {$val == "unicast"} {
                    if {$userArgsArray(session_type) == "ripng"} {
                        lappend RipRouterConfig "-DutIpv6Addr" "$userArgsArray(neighbor_intf_ip_addr)"
                    } else {
                        lappend RipRouterConfig "-DutIpv4Addr" "$userArgsArray(neighbor_intf_ip_addr)"
                    }
                }
                if {$val == "multicast"} {
                    if {$userArgsArray(session_type) == "ripv1"} {
                        return -code error "Error: RIP version 1 does not support -send_type multicast."
                    }
                    if {$userArgsArray(session_type) == "ripng"} {
                        lappend RipRouterConfig "-DutIpv6Addr" "ff02::9"
                    } else {
                        lappend RipRouterConfig "-DutIpv4Addr" "224.0.0.9"
                    }
                }
            } 
            update_interval         { lappend RipRouterConfig "-UpdateInterval" "$val" }
            update_interval_offset  { lappend RipRouterConfig "-UpdateJitter" "$val" }
            num_routes_per_period   { lappend RipRouterConfig "-MaxRoutePerUpdate" "$val" }
            time_period             { lappend RipRouterConfig "-InterUpdateDelay" "$val" }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetRipRouterConfigSettings: $RipRouterConfig"
    return $RipRouterConfig
}

proc ::sth::rip::GetAuthenSettings {ripRouteConfig} {
    variable userArgsArray
    variable sessionType
    set AuthenConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            authentication_mode {
                if {[string match -nocase $val "null"]} {
                    lappend AuthenConfig "-Authentication" "None" 
                } elseif {[string match -nocase $val "text"]} {
                    lappend AuthenConfig "-Authentication" "Simple"
                } else {
                    lappend AuthenConfig "-Authentication" $val
                }
            }
            md5_key -
            password {
                if {[regexp "Password" $AuthenConfig] && [regexp "^Spirent$" $val]} {
                    # md5_key and passward are all for the "-Passward".
                } else {
                    lappend AuthenConfig "-Password" $val
                }
            }
            md5_key_id          { lappend AuthenConfig "-Md5KeyId" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetAuthenSettings: $AuthenConfig"
    return $AuthenConfig
}
proc ::sth::rip::GetDeviceAddrSettings {version} {
    variable userArgsArray
    variable sessionType

    set RouterConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        set val [GetAssociatedItem $userArgsArray(session_type) $val]
        
        switch -- [string tolower $attr] {
            intf_ip_addr            {
                lappend RouterConfig "-NextIpv[string trim $version]" $val
            }
            intf_ip_addr_step       {
                foreach {key keyVal} $val {
                    if {$key == $userArgsArray(session_type)} {
                        lappend ripRouteSettings "-Ipv[string trim $version]Increment" $keyVal
                        break
                    }
                } 
            }
            intf_ip_prefix_len      {
                lappend RouterConfig "-DefaultIpv[string trim $version]Prefix" $val
            }
            router_id               { lappend RouterConfig "-NextRouterId" $val } 
            router_id_step          { lappend RouterConfig "-RouterIdIncrement" $val }
            mac_address_start       { lappend RouterConfig "-NextMac" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetDeviceAddrSettings: $RouterConfig"
    return $RouterConfig
}

proc ::sth::rip::GetIPIntfSetup {rtrHanlde addr} {
    variable userArgsArray
    set IPConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        set val [GetAssociatedItem $userArgsArray(session_type) $val]
        
        switch -- [string tolower $attr] {
            intf_ip_addr                { lappend IPConfig "-Address" $addr }
            intf_ip_addr_step           {
                if {[string match "rip*" $val] == 0} {
                    lappend ripRouteSettings "-AddrStep" $val
                } else {
                    set ipstep [GetAssociatedItem $userArgsArray(session_type) $val]
                    lappend IPConfig "-AddrStep" $ipstep
                }
            }
            neighbor_intf_ip_addr       { 
                lappend IPConfig "-Gateway" $val
            } 
            neighbor_intf_ip_addr_step  {
                #step is not use for this purpose
            }
            intf_prefix_length          { lappend IPConfig "-PrefixLength" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetIPIntfSetup: $IPConfig"
    return $IPConfig
}

#add for atm
proc ::sth::rip::getAtmSettings {rtrId} {
   variable userArgsArray
    set atmConfig [list]
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            vpi             {
                if { [info exists userArgsArray(vpi_step)] } {
                    lappend atmConfig "-vpi" [expr $val + ($userArgsArray(vpi_step) * $rtrId)]
                } else {
                    lappend atmConfig "-vpi" $val
                }
               
            }
            vci             {
                if { [info exists userArgsArray(vpi_step)] } {
                    lappend atmConfig "-vci" [expr $val + ($userArgsArray(vci_step) * $rtrId)]
                } else {
                    lappend atmConfig "-vci" $val
                }
            }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "getAtmSettings: $atmConfig"
    return $atmConfig
}

proc ::sth::rip::GetVlanIntfSetup {rtrHanlde rtrId} {
    variable userArgsArray
    set VlanConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            vlan_id             {
                if {$userArgsArray(vlan_id_mode) == "fixed"} {
                    lappend VlanConfig "-VlanId" $val
                } elseif {$userArgsArray(vlan_id_mode) == "increment"} {
                    if {$rtrId == 0} {
                        lappend VlanConfig "-VlanId" $val
                    } else {
                        lappend VlanConfig "-VlanId" [expr {$val + ($userArgsArray(vlan_id_step) * $rtrId)}]
                    }
                }
            }
            vlan_user_priority  { lappend VlanConfig "-Priority" $val }
            vlan_cfi            { lappend VlanConfig "-Cfi" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $VlanConfig"
    return $VlanConfig
}

proc ::sth::rip::GetVlanOuterSetup {rtrHanlde rtrId} {
    variable userArgsArray
    set VlanConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            vlan_outer_id  {
                if {$userArgsArray(vlan_outer_id_mode) == "fixed"} {
                    lappend VlanConfig "-VlanId" $val
                } elseif {$userArgsArray(vlan_outer_id_mode) == "increment"} {
                    if {$rtrId == 0} {
                        lappend VlanConfig "-VlanId" $val
                    } else {
                        lappend VlanConfig "-VlanId" [expr {$val + ($userArgsArray(vlan_outer_id_step) * $rtrId)}]
                    }
                }
            }
            vlan_outer_user_priority  { lappend VlanConfig "-Priority" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $VlanConfig"
    return $VlanConfig
}

proc ::sth::rip::GetLinkLocalIntfSetup {intfHandle ipaddr} {
    variable userArgsArray
    set LinkLocalConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            link_local_intf_ip_addr        { lappend LinkLocalConfig "-Address" $ipaddr }
            link_local_intf_ip_addr_step   {
                #lappend LinkLocalConfig "-AddrStep" $val
                if {[string match "rip*" $val] == 0} {
                    lappend LinkLocalConfig "-AddrStep" $val
                } else {
                    set ipstep [GetAssociatedItem $userArgsArray(session_type) $val]
                    lappend LinkLocalConfig "-AddrStep" $ipstep
                }
            }
            link_local_intf_prefix_len     {
                #lappend LinkLocalConfig "-PrefixLength" $val
                if {[string match "rip*" $val] == 0} {
                    lappend LinkLocalConfig "-PrefixLength" $val
                } else {
                    set ipstep [GetAssociatedItem $userArgsArray(session_type) $val]
                    lappend LinkLocalConfig "-PrefixLength" $ipstep
                }
            }
            gateway_ip_addr        { lappend LinkLocalConfig "-Gateway" $val }
            default {}
        }
    }
    ::sth::sthCore::log debug "GetLinkLocalIntfSetup: $LinkLocalConfig"
    return $LinkLocalConfig
}
proc ::sth::rip::GetRipRouteSettings {routeHandle} {
    variable userArgsArray
    variable sessionType

    set router [::sth::sthCore::invoke stc::get $routeHandle -parent]
    set ripRouteSettings [list] 

    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            metric          { lappend ripRouteSettings "-Metric" $val }
            next_hop        {
                if {[string match "rip*" $val] == 0} {
                    lappend ripRouteSettings "-NextHop" $val
                } else {
                    set ipstep [GetAssociatedItem $sessionType($router) $val]
                    lappend ripRouteSettings "-NextHop" $ipstep
                }
            }
            route_tag       { lappend ripRouteSettings "-RouteTag" $val }
            default {}
        }
    }
    ::sth::sthCore::log debug "GetRipRouteSettings: $ripRouteSettings"
    return $ripRouteSettings
}
proc ::sth::rip::GetRipNetworkBlockSettings {routeHandle} {
    variable userArgsArray
    variable sessionType
    set router [::sth::sthCore::invoke stc::get $routeHandle -parent]
    set ripNetworkBlockSettings [list] 

    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            num_prefixes    { lappend ripNetworkBlockSettings "-NetworkCount" $val }
            prefix_length   {
                if {[string match "rip*" $val] == 0} {
                    lappend ripNetworkBlockSettings "-PrefixLength" $val
                } else {
                    set len [GetAssociatedItem $sessionType($router) $val]
                    lappend ripNetworkBlockSettings "-PrefixLength" $len
                }
            }
            prefix_start    {
                if {[string match "rip*" $val] == 0} {
                    lappend ripNetworkBlockSettings "-StartIpList" $val
                } else {
                    set pstart [GetAssociatedItem $sessionType($router) $val]
                    lappend ripNetworkBlockSettings "-StartIpList" $pstart
                }
            }
            prefix_step     {
                if {[string match "rip*" $val] == 0} {
                    lappend ripNetworkBlockSettings "-AddrIncrement" $val
                } else {
                    set pstep [GetAssociatedItem $sessionType($router) $val]
                    lappend ripNetworkBlockSettings "-AddrIncrement" $pstep
                }
            }
            default {}
        }
    }
    ::sth::sthCore::log debug "GetRipNetworkBlockSettings: $ripNetworkBlockSettings"
    return $ripNetworkBlockSettings
}

proc ::sth::rip::emulation_rip_config_delete {returnKeyedListVarName {level 1}} {
    variable userArgsArray
    variable ripSessionConfig
    if {[info exists userArgsArray(handle)] == 0} {
        return -code error "Error: Missing a mandatory attribute -handle."
    }

    upvar $level $returnKeyedListVarName returnKeyedList
    set retVal [catch {

        foreach rtr $userArgsArray(handle) {
            ::sth::sthCore::invoke stc::delete $rtr
        }

    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::rip::retrieve_default_value {Key String} {
    upvar $Key myKey
    upvar $String myString
    set idKey -1
    if {[lsearch -exact $myString $myKey] != -1} {
        set idKey [expr [lsearch -exact $myString $myKey] + 1]
        set myString [lindex $myString $idKey]
    }
}

proc ::sth::rip::emulation_rip_route_config_create {returnKeyedListVarName {level 1}} {
    variable userArgsArray
    variable sessionType
    upvar $level $returnKeyedListVarName returnKeyedList
    
    if {[info exists userArgsArray(prefix_length)] && [regexp -- {[a-zA-Z]+} $userArgsArray(prefix_length)]} {
        ::sth::rip::retrieve_default_value sessionType($userArgsArray(handle)) userArgsArray(prefix_length)
    }
    if {[info exists userArgsArray(prefix_start)] && [regexp -- {[a-zA-Z]+} $userArgsArray(prefix_start)]} {
        ::sth::rip::retrieve_default_value sessionType($userArgsArray(handle)) userArgsArray(prefix_start)
    }
    if {[info exists userArgsArray(prefix_step)] && [regexp -- {[a-zA-Z]+} $userArgsArray(prefix_step)]} {
        ::sth::rip::retrieve_default_value sessionType($userArgsArray(handle)) userArgsArray(prefix_step)
    }
    if {[info exists userArgsArray(next_hop)] && [regexp -- {[a-zA-Z]+} $userArgsArray(next_hop)]} {
        ::sth::rip::retrieve_default_value sessionType($userArgsArray(handle)) userArgsArray(next_hop)
    }
    
    set retVal [catch {
        if {([info exists userArgsArray(prefix_length)] && $userArgsArray(prefix_length) > 32) &&
            (! [info exists sessionType($userArgsArray(handle))] || \
            ([info exists sessionType($userArgsArray(handle))] && \
            $sessionType($userArgsArray(handle)) != "ripng"))} {
                return [concat "Error: -prefix_length values greater than 32 are only allowed for -session_type ripng."]
        }
        if {[info exists userArgsArray(handle)]==0} {
            return -code error "Error: Missing a mandatory attribute -handle."
        } else {
            set ripRouter [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-riprouterconfig]
            if {$ripRouter == ""} {
                return -code error "Error: Invalid router handle, $userArgsArray(handle), is passed in."
            }
        }
        #if {[string match "*prefix_start*" $userArgsArray(optional_args)] == 0} {
        #    return -code error "Error: Missing a mandatory attribute -prefix_start."
        #}
         switch $sessionType($userArgsArray(handle)) {
            "ripv1" -
            "ripv2" {
               set ripRouteParams "Ripv4RouteParams"
               set ipNetworkBlock "Ipv4NetworkBlock"
            }
            "ripng" {
               set ripRouteParams "RipngRouteParams"
               set ipNetworkBlock "Ipv6NetworkBlock"
            }
            default {
               ::sth::sthCore::processError returnKeyedList [concat "Error:  Unknown session_type $sessionType($userArgsArray(handle))."]
               return $returnKeyedList
            }
         }

        set ripRouterConfig [::sth::sthCore::invoke stc::get $userArgsArray(handle) "-children-riprouterconfig"]
        #create ripv4routeparams1 etc.
        set route_settings [GetRipRouteSettings  $ripRouterConfig]
	    set ripRouteObj [::sth::sthCore::invoke stc::create $ripRouteParams -under $ripRouterConfig $route_settings]

        set networkblock_settings [GetRipNetworkBlockSettings $ripRouterConfig]
        set networkblock [::sth::sthCore::invoke stc::get $ripRouteObj -children-${ipNetworkBlock}]
        ::sth::sthCore::invoke stc::config $networkblock $networkblock_settings

        ::sth::sthCore::doStcApply
        keylset returnKeyedList route_handle $ripRouteObj
    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::rip::emulation_rip_route_config_modify {returnKeyedListVarName {level 1}} {
    variable userArgsArray
    variable sessionType
    upvar $level $returnKeyedListVarName returnKeyedList
    if {[info exists userArgsArray(route_handle)]==0} {
        return -code error "Error: Missing a mandatory attribute -route_handle."
    }
    if {[string match "*prefix_start*" $userArgsArray(optional_args)] == 0} {
        return -code error "Error: Missing a mandatory attribute -prefix_start."
    }
    set ripRouterConfig [::sth::sthCore::invoke stc::get $userArgsArray(route_handle) "-parent"]
    set router [::sth::sthCore::invoke stc::get $ripRouterConfig "-parent"]

    set retVal [catch {
        switch $sessionType($router) {
            "ripv1" -
            "ripv2" { set ipNetworkBlock "Ipv4NetworkBlock" }
            "ripng" { set ipNetworkBlock "Ipv6NetworkBlock" }
            default { }
         }

        #create ripv4routeparams1 etc.
        set route_settings [GetRipRouteSettings  $ripRouterConfig]
        
        ::sth::sthCore::invoke stc::config $userArgsArray(route_handle) $route_settings
        set networkblock_settings [GetRipNetworkBlockSettings $ripRouterConfig]
        set networkblock [::sth::sthCore::invoke stc::get $userArgsArray(route_handle) -children-$ipNetworkBlock]
        ::sth::sthCore::invoke stc::config $networkblock $networkblock_settings
        ::sth::sthCore::doStcApply

        keylset returnKeyedList route_handle $userArgsArray(route_handle)
    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::rip::emulation_rip_route_config_delete {returnKeyedListVarName {level 1}} {
    variable userArgsArray
    upvar $level $returnKeyedListVarName returnKeyedList

    if {[info exists userArgsArray(route_handle)] == 0} {
        return -code error "Error: Missing a mandatory attribute -route_handle."
    }

    set retVal [catch {
        foreach rt $userArgsArray(route_handle) {
            ::sth::sthCore::invoke stc::delete $rt
        }

        ::sth::sthCore::doStcApply
    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::rip::emulation_rip_flap {returnKeyedListVarName rtrList {level 1}} {
    variable userArgsArray
    upvar $level $returnKeyedListVarName returnKeyedList
    if {[info exists userArgsArray(handle)] == 0} {
        return -code error "Error: Missing a mandatory attribute -handle."
    }

    if {![info exists userArgsArray(flap_routes)]} {
        set userArgsArray(flap_routes) $rtrList
    }
    set retVal [catch {
        for {set i 1} {$i <= $userArgsArray(flap_count)} {incr i} {
            after [expr 1000 * $userArgsArray(flap_interval_time)]
        
            ::sth::sthCore::invoke stc::perform "ripWithdrawRoute"  "-routeList" $userArgsArray(flap_routes)

            after [expr 1000 * $userArgsArray(flap_down_time)]

            ::sth::sthCore::invoke stc::perform "ripReadvertiseRoute" "-routerList" [::sth::sthCore::invoke stc::get $userArgsArray(flap_routes) -parent]
        }
    } returnedString]
    return -code $retVal $returnedString
}

