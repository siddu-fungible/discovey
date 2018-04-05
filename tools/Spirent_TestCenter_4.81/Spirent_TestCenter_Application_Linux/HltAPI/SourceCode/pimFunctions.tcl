# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::sthCore {
}
namespace eval ::sth {
    variable version 4 
    variable testType "remote_rp" 
    variable groupType "SG" 
    variable stopTimeArray
    variable startTimeArray
    variable ipv4Version 4
}

proc ::sth::emulation_pim_config_create {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_create"
    variable userArgsArray
    variable version
    variable testType
    variable ipv4Version
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set returnKeyedList ""
    set routerList ""

    set retVal [catch {
        if {[info exists userArgsArray(port_handle)] } {
            set version $userArgsArray(ip_version)
            if {[info exists userArgsArray(count)] == 0} {
                set userArgsArray(count) [::sth::sthCore::getswitchprop \
                      ::sth:: emulation_pim_config count default]
            }
            if {[info exists userArgsArray(neighbor_intf_ip_addr)] == 1} {
                if {[llength $userArgsArray(neighbor_intf_ip_addr)] != $userArgsArray(count)} {
                    return -code error [concat "Error:  Unable to create PIM session. \
                        The number of router(s) to be created and a list of -neighbor_intf_ip_addr mismatched. "]
                }
            }
            #setup global address/step/id params, put return value in 'device'
            set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]

            #call to setup routerid and routeridstep
            set deviceSettings [GetDeviceAddrSettings]
			::sth::sthCore::invoke stc::config $device $deviceSettings
            #set pim global setup here
			set pimGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PimGlobalConfig]

            set pimGlobalSettings [GetPimGlobalConfig]
			::sth::sthCore::invoke stc::config $pimGlobalConfig $pimGlobalSettings
            array unset router
            set routerList [list]
            for {set rtrId 1} {$rtrId <= $userArgsArray(count)} {incr rtrId} {
                #1. creating router block
                #use stc::perform DeviceCreate command instead of stc::create to create the router
                #when use stc::perform DeviceCreate, the mac and ip address can be globally assigned with the values configured in
                #$device->deviceaddroptions
                if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack "" -IfCount "" -Port $userArgsArray(port_handle)]
                            set router($rtrId) $DeviceCreateOutput(-ReturnList)} createStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Isis Router. Error: $createStatus" {}
                    return -code error $returnKeyedList
                }
                if {[info exists userArgsArray(router_id)] == 1} {
                    if {[info exists userArgsArray(router_id_step)] == 0} {
                        set newrouterid [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) 0.0.0.0 [expr $rtrId-1]]
                    } else {
                        set newrouterid \
                            [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) $userArgsArray(router_id_step) [expr $rtrId-1]]
                    }
                    set routerSettings [GetRouterSettings $newrouterid]
                    ::sth::sthCore::invoke stc::config $router($rtrId) $routerSettings
                }
                #2. configure the ethernet stack for PIM router
                    # If ATM option is provided, configure ATM stack for PIM router, otherwise, configure the ethernet stack.
                    # modifid by xiaozhi 5/13/09
                if {[info exists userArgsArray(vci)]||[info exists userArgsArray(vpi)]} {
                    if {[catch {set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $router($rtrId)]} err]} {
                        ::sth::sthCore::processError returnKeyedList "Internal error creating Aal5If: $err"
                        return -code error $returnKeyedList
                    }
                    set atmSettings [GetAtmSettings $atmResultIf [expr {$rtrId-1}]]
                    ::sth::sthCore::invoke stc::config $atmResultIf $atmSettings
                } else {
                    set ethResultIf [::sth::sthCore::invoke "stc::get $router($rtrId) -children-ethiiif"]
                    if {$ethResultIf == ""} {
                        if {[catch {set ethResultIf [::sth::sthCore::invoke stc::create EthIIIf -under $router($rtrId)]} error]} {
                            ::sth::sthCore::processError returnKeyedList "Internal error creating EthIIIf: $error"
                            return -code error $returnKeyedList 
                        }
                    }
                }
            
            #rxu: qinq support
                    #xiaozhi: if there is ATM encapsulation, vlan is not allowed
                if {[info exists userArgsArray(vlan_outer_id)] && ![info exists atmResultIf]} {
                    set vlan userArgsArray(vlan_outer_id)
                    if {[catch {set vlanOuterResultIf [::sth::sthCore::invoke stc::create VlanIf -under $router($rtrId)]} error]} {
                        ::sth::sthCore::processError returnKeyedList "Internal error creating VlanIf: $error"
                        return -code error $returnKeyedList 
                    }
                    set vlanOuterIfSettings [GetVlanOuterIntfSetup $vlanOuterResultIf [expr $rtrId-1]]
                    ::sth::sthCore::invoke stc::config $vlanOuterResultIf $vlanOuterIfSettings
                }
            #rxu: qinq support end
    
                #3. configure vlan if option is provided
                    #xiaozhi: if there is ATM encapsulation, vlan is not allowed
                if {[info exists userArgsArray(vlan_id)] && ![info exists atmResultIf]} {
                    set vlan userArgsArray(vlan_id)
                    set vlanResultIf [::sth::sthCore::invoke stc::create VlanIf -under $router($rtrId)]
                    set vlanIfSettings [GetVlanIntfSetup $vlanResultIf [expr $rtrId-1]]
                    ::sth::sthCore::invoke stc::config $vlanResultIf $vlanIfSettings
                }

                #4. configure the ip stack for PIM router
                set ipResultIf [::sth::sthCore::invoke "stc::get $router($rtrId) -children-Ipv[string trim $version]If"]
                if {$ipResultIf == ""} {
                    set ipResultIf [::sth::sthCore::invoke stc::create Ipv[string trim $version]If -under $router($rtrId)]
                }
                if {[info exists userArgsArray(intf_ip_addr)]} {
                    if {[info exists userArgsArray(intf_ip_addr_step)]} {
                        set newipaddr [::sth::sthCore::updateIpAddress $userArgsArray(ip_version) $userArgsArray(intf_ip_addr) \
                        $userArgsArray(intf_ip_addr_step) [expr $rtrId-1]]
                    } else {
                        set newipaddr $userArgsArray(intf_ip_addr)
                    }
                      
                    set ipifSettings [GetIPIntfSetup $ipResultIf $newipaddr [expr $rtrId-1]]
                    ::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
                }
                #configure a link local stack in case of ipv6
                if {$userArgsArray(ip_version) == 6} {
					set linkLocalHandle [::sth::sthCore::invoke stc::create Ipv[string trim $version]If -under $router($rtrId)]
                    #enable/disable the exposure of link local, the spec does not call for this. 
                    if {1} {
                        if {[info exists userArgsArray(link_local_intf_ip_addr_step)]} {
                        set newipaddr [::sth::sthCore::updateIpAddress $version $userArgsArray(link_local_intf_ip_addr) \
                            $userArgsArray(link_local_intf_ip_addr_step) [expr $rtrId-1]]
                        } else {
                        set newipaddr $userArgsArray(link_local_intf_ip_addr) 
                        }
                        
                        set linkLocalSettings [GetLinkLocalIntfSetup $linkLocalHandle $newipaddr]
						::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
                    } else {
                        set linkLocalSettings [GetDefaultLinkLocalIntfSetup $linkLocalHandle]
						::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
                    }
                }
                #5. configure router to run PIM
				set pimrtrHandle [::sth::sthCore::invoke stc::create PimRouterConfig -under $router($rtrId)]
                set pimSettings [GetPimRouterSetup $pimrtrHandle [expr $rtrId-1]]
				::sth::sthCore::invoke stc::config $pimrtrHandle $pimSettings
 
                #6. create rp mapping
                if {[string match -nocase $testType "c_bsr"]} {
                    #if rp priority and rp hold time is provided, setup the RP Maps.
                    if {[info exists userArgsArray(c_bsr_rp_priority)] || [info exists userArgsArray(c_bsr_rp_holdtime)]} {
						set pimRpMapBlkHandle [::sth::sthCore::invoke stc::create Pimv[string trim $version]RpMap -under $pimrtrHandle]
                        set pimMaps [GetPimRpMap $pimRpMapBlkHandle]
						::sth::sthCore::invoke stc::config $pimRpMapBlkHandle $pimMaps
                    }
                }
    
                #7. setup relations
				::sth::sthCore::invoke stc::config $router($rtrId) "-AffiliationPort-targets $userArgsArray(port_handle)"
                
                #adjust the stack for vlan relation
                #rxu: qinq support
                #xiaozhi: atm support
                if {[info exists atmResultIf]} {
                    set lowerIf $atmResultIf
                } else {
                    set lowerIf $ethResultIf
                    if {[info exists userArgsArray(vlan_outer_id)] != 0} {
						::sth::sthCore::invoke stc::config $vlanOuterResultIf "-StackedOnEndpoint-targets $lowerIf"
                        set lowerIf $vlanOuterResultIf   
                        if {[info exists userArgsArray(vlan_id)] != 0} {
							::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $lowerIf"
                        } else {
                            ::sth::sthCore::processError returnKeyedList "miss vlan_id value for QinQ"
                            puts "$returnKeyedList \n"    
                            return $returnKeyedList
                        }
                        set lowerIf $vlanResultIf
                        #rxu: qinq support end
                    } elseif {[info exists userArgsArray(vlan_id)] != 0} {
						::sth::sthCore::invoke stc::config $vlanResultIf "-StackedOnEndpoint-targets $lowerIf"
                        set lowerIf $vlanResultIf   
                    }
                }
                ### adjust the stack for gre relation
                if {[info exists userArgsArray(tunnel_handle)] && ![info exists atmResultIf]} {
                   if {[catch {::sth::createGreStack $userArgsArray(tunnel_handle) $router($rtrId) $lowerIf $rtrId } returnIf]} {
                      return -code error "Internal error: failed to create Gre Stack"
                    } else {
                        set lowerIf $returnIf
                    }
                }
                
                #stack the top ipif on lowerif
				::sth::sthCore::invoke stc::config $ipResultIf "-StackedOnEndpoint-targets $lowerIf"

                #adjust the stack for link local stack relation
                if {$userArgsArray(ip_version) == 6} {
                    set ipstacking "$ipResultIf $linkLocalHandle"
                } else {
                    set ipstacking "$ipResultIf"
                }
                ::sth::sthCore::invoke stc::config $router($rtrId) -TopLevelIf-targets "$ipstacking"
                ::sth::sthCore::invoke stc::config $router($rtrId) -PrimaryIf-targets "$ipstacking"
                if {$userArgsArray(ip_version) == 6} {
                    # Just stack the link-local interface object on top of the same object as the global interface object.
                    set endpoint [::sth::sthCore::invoke stc::get $ipResultIf -StackedOnEndpoint-targets]
                    ::sth::sthCore::invoke stc::config $linkLocalHandle "-StackedOnEndpoint-targets $endpoint"
                }
				::sth::sthCore::invoke stc::config $pimrtrHandle "-UsesIf-targets $ipResultIf"
                #build router handle into keyed list
                lappend routerList $router($rtrId)
            }
        } elseif {[info exists userArgsArray(handle)]} {
            #puts "Please be noted PIM will be created in Device $userArgsArray(handle)"
            set pimRouters $userArgsArray(handle)
            set routerList $pimRouters
            set idx 0
            foreach pimRouter $pimRouters {
                if {[::sth::sthCore::invoke stc::get $pimRouter -children-PimRouterConfig] != ""} {
                    ::sth::sthCore::processError returnKeyedList "$pimRouter already has PIM enable" {}
                    return -code error $returnKeyedList 
                }
                set version $userArgsArray(ip_version)
                #create pimconfig
				array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $pimRouter  -CreateClassId [string tolower PimRouterConfig]]
                set pimrtrHandle $ProtocolCreateOutput(-ReturnList)
                set pimSettings [GetPimRouterSetup $pimrtrHandle $idx]
				::sth::sthCore::invoke stc::config $pimrtrHandle $pimSettings
                #create rp mapping
                if {[string match -nocase $testType "c_bsr"]} {
                    #if rp priority and rp hold time is provided, setup the RP Maps.
                    if {[info exists userArgsArray(c_bsr_rp_priority)] || [info exists userArgsArray(c_bsr_rp_holdtime)]} {
                        set pimRpMapBlkHandle [::sth::sthCore::invoke stc::create Pimv[string trim $version]RpMap -under $pimrtrHandle]
                        set pimMaps [GetPimRpMap $pimRpMapBlkHandle]
                        ::sth::sthCore::invoke stc::config $pimRpMapBlkHandle $pimMaps
                    }
                }
                incr idx
            }
        } else {
            return -code error [concat "Error:  Unable to create PIM session. Need to specify -port_handle or -handle."]
        }
        keylset returnKeyedList handle $routerList 
        keylset returnKeyedList handles $routerList 
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::GetVlanIntfSetup {rtrHanlde rtrId} {
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
                        lappend VlanConfig "-VlanId" [expr $val + ($userArgsArray(vlan_id_step) * $rtrId)]
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

#rxu: qinq support
proc ::sth::GetVlanOuterIntfSetup {rtrHanlde rtrId} {
    variable userArgsArray
    set VlanOuterConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            vlan_outer_id             {
                if {$userArgsArray(vlan_outer_id_mode) == "fixed"} {
                    lappend VlanOuterConfig "-VlanId" $val
                } elseif {$userArgsArray(vlan_outer_id_mode) == "increment"} {
                    if {$rtrId == 0} {
                        lappend VlanOuterConfig "-VlanId" $val
                    } else {
                        lappend VlanOuterConfig "-VlanId" [expr $val + ($userArgsArray(vlan_outer_id_step) * $rtrId)]
                    }
                }
            }
            vlan_outer_user_priority  { lappend VlanOuterConfig "-Priority" $val }
            vlan_outer_cfi            { lappend VlanOuterConfig "-Cfi" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetVlanIntfSetup: $VlanOuterConfig"
    return $VlanOuterConfig
}
#rxu: qinq support end
proc ::sth::GetDefaultLinkLocalIntfSetup {intfHandle} {
    variable userArgsArray
    set intFromIntfHandle [string range $intfHandle 6 [string length $intfHandle]]
    set LinkLocalConfig [list "-Address" "fe80::$intFromIntfHandle:1"] 
    ::sth::sthCore::log debug "GetLinkLocalIntfSetup: $LinkLocalConfig"
    return $LinkLocalConfig
}

proc ::sth::GetLinkLocalIntfSetup {intfHandle ipaddr} {
    variable userArgsArray
    set LinkLocalConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            link_local_intf_ip_addr        { lappend LinkLocalConfig "-Address" $ipaddr }
            link_local_intf_ip_addr_step   { lappend LinkLocalConfig "-AddrStep" $val }
            link_local_intf_prefix_len     { lappend LinkLocalConfig "-PrefixLength" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetLinkLocalIntfSetup: $LinkLocalConfig"
    return $LinkLocalConfig
}
proc ::sth::GetIPIntfSetup {rtrHanlde addr rtrId} {
    variable userArgsArray
    set IPConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            intf_ip_addr              { lappend IPConfig "-Address" $addr }
            intf_ip_addr_step         { lappend IPConfig "-AddrStep" $val }
            AddrStepMask              { lappend IPConfig "-AddrStepMask" $val }
            neighbor_intf_ip_addr     { lappend IPConfig "-Gateway" [lindex $val $rtrId] }
            intf_ip_prefix_len        { lappend IPConfig "-PrefixLength" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetIPIntfSetup: $IPConfig"
    return $IPConfig
}

#this proc needs to be executed before you create the router
proc ::sth::GetDeviceAddrSettings {} {
    variable userArgsArray
    variable version

    set RouterConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            intf_ip_addr            {
                if {$version == 4} {
                    lappend RouterConfig "-NextIpv4" $val
                } else {
                    lappend RouterConfig "-NextIpv6" $val
                }
            }
            intf_ip_addr_step       {
                if {$version == 4} {
                    lappend RouterConfig "-Ipv4Increment" $val
                } else {
                    lappend RouterConfig "-Ipv6Increment" $val
                }
            }
            intf_ip_prefix_len      {
                if {$version == 4} {
                    lappend RouterConfig "-DefaultIpv4Prefix" $val
                } else {
                    lappend RouterConfig "-DefaultIpv6Prefix" $val
                }
            }
            router_id               { lappend RouterConfig "-NextRouterId" $val } 
            router_id_step          { lappend RouterConfig "-RouterIdIncrement" $val }
            mac_address_start       {
                #xiaozhi: mac address can not be set in ATM encapsulation
                if {![info exists userArgsArray(vci)] && ![info exists userArgsArray(vpi)]} {
                    lappend RouterConfig "-NextMac" $val
                }
            }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetDeviceAddrSettings: $RouterConfig"
    return $RouterConfig
}
proc ::sth::GetRouterSettings {addr} {
    variable userArgsArray
    set RouterConfig [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            router_id          { lappend RouterConfig "-RouterId" $addr }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetRouterSettings: $RouterConfig"
    return $RouterConfig
}
proc ::sth::GetPimRpMap {pimRpMapHandle} {
    variable userArgsArray
    set pimRpMap [list]
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            c_bsr_rp_addr              { lappend pimRpMap "-RpIpAddr" $val }
            c_bsr_rp_holdtime          { lappend pimRpMap "-RpHoldTime" $val }
            c_bsr_rp_priority          { lappend pimRpMap "-RpPriority" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetPimRpMap: $pimRpMap"
    return $pimRpMap
}
proc ::sth::GetPimRouterSetup {handle rtrId} {
    variable userArgsArray
    variable version
    variable testType 
    set intFromHandle [string range $handle 15 [string length $handle]]
    if {$version == 4} {
        if {[info exists userArgsArray(neighbor_intf_ip_addr)]} {
            #userArgsArray(neighbor_intf_ip_addr) is in forms of list. Assume they are inorder as we create pim routers
            set neighbor_intf_ip_addr [lindex $userArgsArray(neighbor_intf_ip_addr) $rtrId]
            set PimRouterConfig [list -UpstreamNeighborV4 $neighbor_intf_ip_addr]
        }
    } else {
        #set PimRouterConfig [list -UpstreamNeighborV6 fe80::$intFromHandle:1] 
        if {[info exists userArgsArray(neighbor_intf_ip_addr)]} {
            #userArgsArray(neighbor_intf_ip_addr) is in forms of list. Assume they are inorder as we create pim routers
            set neighbor_intf_ip_addr [lindex $userArgsArray(neighbor_intf_ip_addr) $rtrId]
            set PimRouterConfig [list -UpstreamNeighborV6 $neighbor_intf_ip_addr]
        }
    }
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            pim_mode                   { lappend PimRouterConfig "-PimMode" $val }
            type                       {
                if {[string match -nocase "remote_rp" $val]} {
                    set testType "remote_rp"
                    lappend PimRouterConfig "-EnableBsr" "FALSE" 
                } elseif {[string match "c_bsr" $val]} {
                    set testType "c_bsr"
                    lappend PimRouterConfig "-EnableBsr" "TRUE" 
                }
            }
            ip_version                 { lappend PimRouterConfig "-IpVersion" "V$val" }
            hello_holdtime             { lappend PimRouterConfig "-HelloHoldtime" $val }
            hello_interval             { lappend PimRouterConfig "-HelloInterval" $val }
            join_prune_holdtime        { lappend PimRouterConfig "-JoinPruneHoldtime" $val }
            join_prune_interval        { lappend PimRouterConfig "-JoinPruneInterval" $val }
            bidir_capable              { lappend PimRouterConfig "-BiDirOptionSet" $val }
            bs_period                  { lappend PimRouterConfig "-BootstrapMessageInterval" $val }
            dr_priority                { lappend PimRouterConfig "-DrPriority" $val }
            c_bsr_priority             { lappend PimRouterConfig "-BsrPriority" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetPimRouterSetup: $PimRouterConfig"
    return $PimRouterConfig
}

proc ::sth::UnknownConfigSettingWarning {key value} {
    ::sth::sthCore::log debug "::sth::UnknownConfigSettingWarning, $key, $value."
}

proc ::sth::GetPimGroupsSetup {rtrHanlde} {
    variable userArgsArray
    variable groupType
    set pimGroupMap [list] 
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            rp_ip_addr          { lappend pimGroupMap "-RpIpAddr" $val }
            wildcard_group     {
                if {[info exists userArgsArray(source_pool_handle)] == 0} {
                    set groupType "STARSTARRP"
                } else {
                    set groupType "SG"
                    if {$val == 1} {
                        set groupType "STARG" 
                    }
                }
                lappend pimGroupMap "-GroupType" $groupType
            }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetPimGroupsSetup: $pimGroupMap"
    return $pimGroupMap
}


proc ::sth::GetPimJoinPruneSrc {joinPruneSrc srcSettings} {
    variable userArgsArray
    variable groupType
    set pimJoinPruneSrc [list] 
    foreach {attr val} $srcSettings {
        switch -- [string tolower $attr] {
            -num_sources         { lappend pimJoinPruneSrc "-NetworkCount" $val }
            -ip_addr_start       { lappend pimJoinPruneSrc "-StartIpList" $val }
            -ip_addr_step        { lappend pimJoinPruneSrc "-AddrIncrement" $val }
            -ip_prefix_len       { lappend pimJoinPruneSrc "-PrefixLength" $val }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
     ::sth::sthCore::log debug "GetPimJoinPruneSrc: $pimJoinPruneSrc"
    return $pimJoinPruneSrc
}
#add ATM encapsulation  5/13/09 xiaozhi
proc ::sth::GetAtmSettings {rtrHanlde rtrId} {
    variable userArgsArray
    set atmList [list]
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            vci {
                if {[info exist userArgsArray(vci_step)]} {
                    set vci [expr {$val + ($userArgsArray(vci_step) * $rtrId)}]
                } else {
                    set vci $val
                } 
                lappend atmList "-vci" $vci
            }
            vpi {
                if {[info exist userArgsArray(vpi_step)]} {
                    set vpi [expr {$val + ($userArgsArray(vpi_step) * $rtrId)}]
                } else {
                    set vpi $val
                } 
                lappend atmList "-vpi" $vpi
            }
            default {
                #UnknownConfigSettingWarning $attr $val
            }
        }
    }
    ::sth::sthCore::log debug "GetAtmSettings: $atmList"
    return $atmList
}


proc ::sth::emulation_pim_config_inactive {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_inactive"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    set returnKeyedList "" 
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to inactive PIM " \
                  "session.  Missing mandatory argument \"-handle\".  "]
        }
        set  pimRouters $userArgsArray(handle)
        foreach pimRouter $pimRouters  {
            if {[catch {set pimRtrCfg [::sth::sthCore::invoke stc::get $pimRouter "-children-PimRouterConfig"]} error]} {
                ::sth::sthCore::processError returnKeyedList "Error while geting PIM Protocol handle. Error: $error" {}
                return -code error $returnKeyedList 	
            }
            if {[catch {::sth::sthCore::invoke stc::config $pimRtrCfg "-Active FALSE -LocalActive FALSE"} error]} {
                ::sth::sthCore::processError returnKeyedList "Failed to inactive PIM protocol: $error. Error: $error" {}
                            return $returnKeyedList		
            }
        }
        keylset returnKeyedList handle $pimRouters
        keylset returnKeyedList handles $pimRouters
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::emulation_pim_config_active {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_active"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    set returnKeyedList "" 
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to active PIM " \
                  "session.  Missing mandatory argument \"-handle\".  "]
        }
        set  pimRouters $userArgsArray(handle)
        foreach pimRouter $pimRouters {
            if {[catch {set pimRtrCfg [::sth::sthCore::invoke stc::get $pimRouter "-children-PimRouterConfig"]} error]} {
                ::sth::sthCore::processError returnKeyedList "Error while geting PIM Protocol handle. Error: $error" {}
                return -code error $returnKeyedList 	
            }
            if {[catch {::sth::sthCore::invoke stc::config $pimRtrCfg "-Active TRUE -LocalActive TRUE"} error]} {
                ::sth::sthCore::processError returnKeyedList "Failed to active PIM protocol: $error. Error: $error" {}
                            return $returnKeyedList		
            }
        }
        keylset returnKeyedList handle $pimRouters
        keylset returnKeyedList handles $pimRouters
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::emulation_pim_config_modify {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_modify"
    variable userArgsArray
    variable version
    variable testType
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set returnKeyedList "" 
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to modify PIM " \
                  "session.  Missing mandatory argument \"-handle\".  "]
        }
        #set pim global setup here
        set pimGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PimGlobalConfig]
        set pimGlobalSettings [GetPimGlobalConfig]
        ::sth::sthCore::invoke stc::config $pimGlobalConfig $pimGlobalSettings
        array unset router
        #1. get the router block and modify the router id
        set router $userArgsArray(handle)

        if {[info exists userArgsArray(router_id)] == 1} {
            if {[info exists userArgsArray(router_id_step)] == 0} {
                set newrouterid [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) 0.0.0.0 0]
            } else {
                set newrouterid [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) $userArgsArray(router_id_step) 0]
            }
            set routerSettings [GetRouterSettings $newrouterid]
            ::sth::sthCore::invoke stc::config $router $routerSettings
        }
        
        #2. modify the ip stack for PIM router. Rewrote by cf
        set ipResultIf [::sth::sthCore::invoke stc::get $router -TopLevelIf-targets]
        
        #when ipv6 is supported, two ip interfaces is return where the second is the link local stack.
        if {$version == 6} {
            array unset v6temp 
            foreach ipif $ipResultIf {
                array set v6temp [::sth::sthCore::invoke stc::get $ipif]
                if {[string match -nocase "*fe80*" $v6temp(-Address)]} { 
                    set linkLocalHandle $ipif 
                    #enable/disable the exposure of link local, the spec does not call for this. 
                    if {1} {
                        set newipaddr [::sth::sthCore::updateIpAddress $version $userArgsArray(link_local_intf_ip_addr) \
                            $userArgsArray(link_local_intf_ip_addr_step) 0]
                        set linkLocalSettings [GetLinkLocalIntfSetup $linkLocalHandle $newipaddr]
                        ::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
                    } else {
                        set linkLocalSettings [GetDefaultLinkLocalIntfSetup $linkLocalHandle]
                        ::sth::sthCore::invoke stc::config $linkLocalHandle $linkLocalSettings
                    }
                } else {
                    set ipResultIf $ipif
                }
                array unset v6temp 
            }
        }

        if {[info exists userArgsArray(intf_ip_addr)] == 1} {
            if {[info exists userArgsArray(intf_ip_addr_step)] == 0} {
                set newipaddr [::sth::sthCore::updateIpAddress $version $userArgsArray(intf_ip_addr) 0.0.0.0 0]
            } else {
                set newipaddr [::sth::sthCore::updateIpAddress $version $userArgsArray(intf_ip_addr) $userArgsArray(intf_ip_addr_step) 0]
            }
            set ipifSettings [GetIPIntfSetup $ipResultIf $newipaddr 0]
			::sth::sthCore::invoke stc::config $ipResultIf $ipifSettings
        }
        #get the lower layer stack, ethernet or ATM, which are exclusive.
        #modified by xiaozhi, 5/13/09
		set lowerIf [::sth::sthCore::invoke stc::get $ipResultIf -StackedOnEndpoint-targets]
        
        set atmResultIf ""
        set atmUnsupportedModifyOptions {mac_address_start vlan_id vlan_outer_id tunnel_handle}
        if {[string length $lowerIf] != 0} {
            if {[string match -nocase "aal5if*" $lowerIf]} {
                set atmResultIf $lowerIf
                if {[info exist userArgsArray(vci)] || [info exist userArgsArray(vpi)]} {
                    set atmSettings [GetAtmSettings $atmResultIf 0]
					::sth::sthCore::invoke stc::config $atmResultIf $atmSettings
                }
                #argments that can not modified under ATM encapsulation
                foreach opt $atmUnsupportedModifyOptions {
                    if {[info exist userArgsArray($opt)]} {
                        ::sth::sthCore::processError returnKeyedList "-$opt can not modifed in ATM encapsulation." {}
                        return -code error $returnKeyedList 
                    }
                }
            }
        }
        
        if {[string length $atmResultIf] == 0} {
            # modify the ethernet stack for PIM router
			set ethResultIf [::sth::sthCore::invoke stc::get $router -children-ethiiif]
            if {[info exists userArgsArray(mac_address_start)] == 1} {
                set ethifSettings "-SourceMac $userArgsArray(mac_address_start)"
				::sth::sthCore::invoke stc::config $ethResultIf $ethifSettings
            }

            # modify vlan if option is provided
            #rxu: qinq support
            if {[info exists userArgsArray(vlan_outer_id)] != 0} {
                set vlan_outer userArgsArray(vlan_outer_id)
                set eth [::sth::sthCore::invoke stc::get $router -children-EthIIIf ]
                set vlanOuterResultIf [::sth::sthCore::invoke stc::get $eth -StackedOnEndpoint-Sources]
                set vlanOuterIfSettings [GetVlanOuterIntfSetup $vlanOuterResultIf 0]
				::sth::sthCore::invoke stc::config $vlanOuterResultIf $vlanOuterIfSettings
            }
    
            if {[info exists userArgsArray(vlan_id)] != 0} {
                set vlan userArgsArray(vlan_id)
                set eth [::sth::sthCore::invoke stc::get $router -children-EthIIIf ]
                set vlanResultIf [::sth::sthCore::invoke stc::get $eth -StackedOnEndpoint-Sources]
                set vlanUpperIf [::sth::sthCore::invoke stc::get $vlanResultIf -StackedOnEndpoint-Sources]
                if {[regexp -nocase "vlanIf" $vlanUpperIf]} {
                    set vlanResultIf $vlanUpperIf
                }
                set vlanIfSettings [GetVlanIntfSetup $vlanResultIf 0]
				::sth::sthCore::invoke stc::config $vlanResultIf $vlanIfSettings
            }
            #rxu: qinq support end
            
            # add for gre. Config Gre stack if needed
            if {[info exists userArgsArray(tunnel_handle)] != 0} {
                if {[catch {::sth::configGreStack  $userArgsArray(tunnel_handle) $router} err]} {
                        return -code error "unable to config gre stack"
                    }
            }
        }
        #5. modify router to run PIM
		set pimrtrHandle [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
        set pimSettings [GetPimRouterSetup $pimrtrHandle 0]
	    ::sth::sthCore::invoke stc::config $pimrtrHandle $pimSettings

        #6. create rp mapping
        if {[string match -nocase $testType "c_bsr"]} {
            #if rp priority and rp hold time is provided, setup the RP Maps.
            if {[info exists userArgsArray(c_bsr_rp_priority)] || [info exists userArgsArray(c_bsr_rp_holdtime)]} {
				set pimRpMapBlkHandle [::sth::sthCore::invoke stc::get $pimrtrHandle -children-Pimv[string trim $version]RpMap]
                set pimMaps [GetPimRpMap $pimRpMapBlkHandle]
				::sth::sthCore::invoke stc::config $pimRpMapBlkHandle $pimMaps
            }
        }

        keylset returnKeyedList handle $router
        keylset returnKeyedList handles $router
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::emulation_pim_config_delete {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_delete"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error [concat "Error:  Unable to delete PIM " \
                  "session.  Missing mandatory argument \"-handle\".  "]
        }
        set  pimRouters $userArgsArray(handle)
        foreach pimRouter $pimRouters  {
            ::sth::sthCore::invoke stc::delete $pimRouter
        }
    } returnedString]
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while deleting PIM "\
                       "session \"$userArgsArray(handle)\".  \n"\
                       "Returned Error:  $returnedString"]
           keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList handle $userArgsArray(handle)
        keylset returnKeyedList handles $userArgsArray(handle)
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_config_enable_all {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_enable_all"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    set retVal [catch {
        set pimRtrConfig [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-pimrouterconfig]
        ::sth::sthCore::invoke stc::config $pimRtrConfig [list -Active true]
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while enabling PIM "\
                       "session \"$userArgsArray(handle)\".  \n"\
                       "Returned Error:  $returnedString"]
           keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList handle $userArgsArray(handle)
        keylset returnKeyedList handles $userArgsArray(handle)
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_config_disable_all {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_config_disable_all"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    set retVal [catch {
        set pimRtrConfig [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-pimrouterconfig]
        ::sth::sthCore::invoke stc::config $pimRtrConfig [list -Active false]
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList \
               [concat "Error:  Error encountered while disabling PIM "\
                       "session \"$userArgsArray(handle)\".  \n"\
                       "Returned Error:  $returnedString"]
           keylset returnKeyedList status $::sth::sthCore::FAILURE
    } else {
        keylset returnKeyedList handle $userArgsArray(handle)
        keylset returnKeyedList handles $userArgsArray(handle)
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_control_stop {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_control_stop"
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    variable stopTimeArray
    variable version
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set retVal [catch {
        if {[info exists userArgsArray(port_handle)] == 0} {
            return -code error [concat "Error:  Unable to stop PIM " \
                  "session.  Missing mandatory argument \"-port_handle\".  "]
        }

        if {[info exists userArgsArray(handle)] == 0} {
            #stop all pim router in a port
			set pimPortList ""
			foreach pimPortList $userArgsArray(port_handle) {
				foreach rtrList [::sth::sthCore::invoke stc::get $pimPortList -affiliationport-Sources] {
					foreach rtr $rtrList {
						set pimRtr [::sth::sthCore::invoke stc::get $rtr -children-pimrouterconfig]
						if {![regexp "^$" $pimRtr]} {
							lappend pimRtrList $pimRtr
						}
					}
				}
			}
        } else {
            #stop a signle pim router
           foreach router $userArgsArray(handle) {
                lappend pimRtrList [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
            }
        }
        #stop pim protocol.
        foreach pimrouter $pimRtrList {
            if { $pimrouter eq "" } { continue }
            if {[catch {array set ret [::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $pimrouter] } err ] } {
                ::sth::sthCore::processError returnKeyedList \
                    "::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $pimRtrList Failed: $err" {}
                return -code error $::sth::sthCore::FAILURE
            }
            set parent [::sth::sthCore::invoke stc::get $pimrouter -parent]
            lappend router_collections $parent
            set stopTimeArray($parent) $ret(-EndTime) 
        }

    } returnedString]
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $router_collections
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_control_start_resultDataset {configClass resultClass {level 1}} {
    set resultDataSet ""
    set retVal [catch {
        set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
        ::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId $configClass -ResultClassId $resultClass]
    } returnedString]
    return -code $retVal $resultDataSet
}

proc ::sth::emulation_pim_control_start {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_control_start"
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable userArgsArray
    variable startTimeArray
    variable version
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set retVal [catch {
        ::sth::sthCore::log debug "Subscribing to results"
        set pimResultDataSet [emulation_pim_control_start_resultDataset "PimRouterConfig" "PimRouterResults"]
        
        ::sth::sthCore::doStcApply  
        ::sth::sthCore::invoke stc::sleep 5 
        ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $pimResultDataSet

        if {[info exists userArgsArray(handle)]} {
            #restart specified  pim router
            foreach router $userArgsArray(handle) {
                lappend pimRtrList [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
            }
        } elseif {[info exists userArgsArray(port_handle)]} {
            #restart all pim router in a port
			set pimPortList ""
			foreach pimPortList $userArgsArray(port_handle) {
				foreach rtrList [::sth::sthCore::invoke stc::get $pimPortList -affiliationport-Sources] {
					foreach rtr $rtrList {
						set pimRtr [::sth::sthCore::invoke stc::get $rtr -children-pimrouterconfig]
						if {![regexp "^$" $pimRtr]} {
							lappend pimRtrList $pimRtr
						}
					}
				}
			}
        } else {
            ::sth::sthCore::processError returnKeyedList "Error:  Unable to start PIM session.  Either -port_handle or handle should be provided" {}
            return -code error $::sth::sthCore::FAILURE
        }

        #start pim protocol.
        foreach pimrouter $pimRtrList {
            if {[catch {array set ret [::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $pimrouter] } err ] } {
                ::sth::sthCore::processError returnKeyedList \
                    "::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $pimRtrList Failed: $err" {}
                return -code error $::sth::sthCore::FAILURE
            }
            set parent [::sth::sthCore::invoke stc::get $pimrouter -parent]
            lappend router_collections $parent
            set startTimeArray($parent) $ret(-StartTime) 
        }

    } returnedString]
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $router_collections
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_control_restart {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_control_restart"
    variable userArgsArray
    variable version
    variable startTimeArray
    variable stopTimeArray
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set pimgroupBlockList ""
    set retVal [catch {
        if {[info exists userArgsArray(handle)] } {
            #restart specified pim router
            foreach router $userArgsArray(handle) {
                set pimRtr [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
                lappend pimRtrList $pimRtr
                set pimgroupBlockList [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
            }
        } elseif {[info exists userArgsArray(port_handle)] } {
            #retart all pim router in a port
			set pimPortList ""
			foreach pimPortList $userArgsArray(port_handle) {
				foreach rtrList [::sth::sthCore::invoke stc::get $pimPortList -affiliationport-Sources] {
					foreach rtr $rtrList {
						set pimRtr [::sth::sthCore::invoke stc::get $rtr -children-pimrouterconfig]
						if {![regexp "^$" $pimRtr]} {
							lappend pimRtrList $pimRtr
						} else {
							continue	
						}
					}
				}
			}
			foreach pimRtr $pimRtrList {
                set pimgroupBlockList \
                [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error:  Unable to restart PIM session.  Either -port_handle or handle should be provided" {}
            return -code error $::sth::sthCore::FAILURE
        }
        ::sth::sthCore::doStcApply    
        ::sth::sthCore::invoke stc::sleep 5
        #send prunes, stop router, clear all results
        if {[catch {::sth::sthCore::invoke stc::perform PimSendPrunes -GroupList $pimgroupBlockList} err ] } {
            ::sth::sthCore::processError returnKeyedList \
                "::sth::sthCore::invoke stc::perform PimSendPrunes -GroupList $pimgroupBlockList Failed: $err" {}
            return -code error $::sth::sthCore::FAILURE
        }
        #now stop the protocol
        foreach pimrouter $pimRtrList {
            if { $pimrouter eq "" } { continue }
            if {[catch {array set ret [::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $pimrouter] } err ] } {
                ::sth::sthCore::processError returnKeyedList \
                    "::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $pimrouter Failed: $err" {}
                return -code error $::sth::sthCore::FAILURE
            }
            set parent [::sth::sthCore::invoke stc::get $pimrouter -parent]
            set stopTimeArray($parent) $ret(-EndTime) 
        }
        if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -Project $::sth::GBLHNDMAP(project)} err ] } {
            ::sth::sthCore::processError returnKeyedList \
                "::sth::sthCore::invoke stc::perform ResultsClearAll -Project $::sth::GBLHNDMAP(project) Failed: $err" {}
            return -code error $::sth::sthCore::FAILURE
        }
        #call sleep for 5 seconds
        ::sth::sthCore::invoke "stc::sleep 5"

        #now start the protocol again
        foreach pimrouter $pimRtrList {
            if {[catch {array set ret [::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $pimrouter] } err ] } {
                ::sth::sthCore::processError returnKeyedList \
                    "::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $pimrouter Failed: $err" {}
                return -code error $::sth::sthCore::FAILURE
            }
            set parent [::sth::sthCore::invoke stc::get $pimrouter -parent]
            lappend router_collections $parent
            set startTimeArray($parent) $ret(-StartTime) 
        }
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $router_collections
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_control_join {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_control_join"
    variable userArgsArray
    variable version
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set pimgroupBlockList ""
    set retVal [catch {
        #If no handle provided, join all the session groups on this port. 
        if {[info exists userArgsArray(handle)]} {
            #If session handle is provided, join all groups on this session. 
            #However, if group member handle is provided, join specified groups. 
            if {[info exists userArgsArray(group_member_handle)] == 1} {
                #group member handle is provided, join specified groups
                set pimgroupBlockList $userArgsArray(group_member_handle)
            } else {
                #session handle is provided, join all groups on this session
                foreach router $userArgsArray(handle) {
                    set pimRtr [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
                    lappend pimRtrList $pimRtr
                    set pimgroupBlockList [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
                }
            }
            keylset returnKeyedList handle $userArgsArray(handle)
            #send joins from all pim router in a port
        } elseif {[info exists userArgsArray(port_handle)]} {
			set pimPortList ""
			foreach pimPortList $userArgsArray(port_handle) {
				foreach rtrList [::sth::sthCore::invoke stc::get $pimPortList -affiliationport-Sources] {
					foreach rtr $rtrList {
						set pimRtr [::sth::sthCore::invoke stc::get $rtr -children-pimrouterconfig]
						if {![regexp "^$" $pimRtr]} {
							lappend pimRtrList $pimRtr
						} else {
							continue	
						}
						lappend router_collection $rtr
					}
				}
			}
			foreach pimRtr $pimRtrList {
                set pimgroupBlockList \
                [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
            }
            keylset returnKeyedList handle $router_collection
        } else {
            ::sth::sthCore::processError returnKeyedList "Error:  Unable to join PIM session.  Either -port_handle or handle should be provided" {}
            return -code error $::sth::sthCore::FAILURE
        }
        ::sth::sthCore::doStcApply       
        ::sth::sthCore::invoke stc::sleep 5      
        if {[catch {set ret [::sth::sthCore::invoke stc::perform PimSendJoins -GroupList $pimgroupBlockList] } err ] } {
            ::sth::sthCore::processError returnKeyedList \
                "::sth::sthCore::invoke stc::perform PimSendJoins -GroupList $pimgroupBlockList Failed: $err" {}
            return -code error $::sth::sthCore::FAILURE
        }
    } returnedString]
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_control_prune {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_control_prune"
    variable userArgsArray
    variable version
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set pimgroupBlockList ""
    set retVal [catch {
        #If no handle provided, prune all the session groups on this port. 
        if {[info exists userArgsArray(handle)]} {
            #If session handle is provided, prune all groups on this session. 
            #However, if group member handle is provided, prune specified groups. 
            if {[info exists userArgsArray(group_member_handle)] == 1} {
                #group member handle is provided, join specified groups
                set pimgroupBlockList $userArgsArray(group_member_handle)
            } else {
                #session handle is provided, join all groups on this session
                foreach router $userArgsArray(handle) {
                    set pimRtr [::sth::sthCore::invoke stc::get $router -children-pimrouterconfig]
                    lappend pimRtrList $pimRtr
                    set pimgroupBlockList [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
                }
            }
            keylset returnKeyedList handle $userArgsArray(handle)
        } elseif {[info exists userArgsArray(port_handle)]} {
            #send prune from all pim router in a port
			set pimPortList ""
			foreach pimPortList $userArgsArray(port_handle) {
				foreach rtrList [::sth::sthCore::invoke stc::get $pimPortList -affiliationport-Sources] {
					foreach rtr $rtrList {
						set pimRtr [::sth::sthCore::invoke stc::get $rtr -children-pimrouterconfig]
						if {![regexp "^$" $pimRtr]} {
							lappend pimRtrList $pimRtr
						} else {
							continue	
						}
						

						lappend router_collection $rtr
					}
				}
			}
			foreach pimRtr $pimRtrList {
	            set pimgroupBlockList \
                [concat $pimgroupBlockList [::sth::sthCore::invoke stc::get $pimRtr -children-pimv[string trim $version]groupblk]]
	        }
            keylset returnKeyedList handle $router_collection
        } else {
            ::sth::sthCore::processError returnKeyedList "Error:  Unable to prune PIM session.  Either -port_handle or handle should be provided" {}
            return -code error $::sth::sthCore::FAILURE
        }

        ::sth::sthCore::doStcApply
        ::sth::sthCore::invoke stc::sleep 5
        if {[catch {set ret [::sth::sthCore::invoke stc::perform PimSendPrunes -GroupList $pimgroupBlockList] } err ] } {
            ::sth::sthCore::processError returnKeyedList \
                "::sth::sthCore::invoke stc::perform PimSendPrunes -GroupList $pimgroupBlockList Failed: $err" {}
            return -code error $::sth::sthCore::FAILURE
        }
    } returnedString]
    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}
# this proc is to be call from pim_group_config
proc ::sth::GetPimGlobalConfig {} {
    variable userArgsArray
    set pimGlobalConfig [list]
    foreach {attr val} [array get userArgsArray] {
        switch -- [string tolower $attr] {
            prune_delay_enable {
                lappend pimGlobalConfig "-EnablingPruningDelayOption" $val
            }
            prune_delay {
                if {$userArgsArray(prune_delay_enable)} { lappend pimGlobalConfig "-LanPruneDelay" $val }
            }
            override_interval {
                if {$userArgsArray(prune_delay_enable)} { lappend pimGlobalConfig "-OverrideInterval" $val }
            }
            interval {
                if {$userArgsArray(rate_control)} { lappend pimGlobalConfig "-MsgInterval" $val }
            }
            join_prune_per_interval {
                if {$userArgsArray(rate_control)} { lappend pimGlobalConfig "-MsgRate" $val }
            }
            register_per_interval {
                if {$userArgsArray(rate_control)} { lappend pimGlobalConfig "-MsgRate" $val }
            }
            register_stop_per_interval {
                if {$userArgsArray(rate_control)} {
                    lappend pimGlobalConfig "-MsgRate" $val
                }
            }
            rate_control {
                if {$val == 0} {
                    set val "false"
                } else {
                    set val "true"
                }
                lappend pimGlobalConfig "-EnableMsgRate" $val
            }
            hello_max_delay {
                lappend pimGlobalConfig "-TriggerHelloDelay" $val
            }
        }
    }
    ::sth::sthCore::log debug "GetPimGlobalConfig: $pimGlobalConfig"
    return $pimGlobalConfig
}

proc ::sth::emulation_pim_group_config_create {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_group_config_create"
    variable userArgsArray
    variable version
    variable testType
    variable groupType
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set returnKeyedList ""
    set retVal [catch {
        if {[info exists userArgsArray(session_handle)] == 0} {
            return -code error "Error:  Unable to create PIM group configuration. Missing mandatory argument -session_handle"
        }
        if {[info exists userArgsArray(group_pool_handle)] == 0} {
            return -code error "Error:  Unable to create an PIM group membership. Missing mandatory argument -group_pool_handle"
        }

        #set pim global setup here
		set pimGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PimGlobalConfig]
        set pimGlobalSettings [GetPimGlobalConfig]
		::sth::sthCore::invoke stc::config $pimGlobalConfig $pimGlobalSettings

		if {[info exists userArgsArray(group_pool_mode)] && ($userArgsArray(group_pool_mode) eq "register")} {
			emulation_pim_register_group_config_create returnKeyedList
		} else {
		
			foreach router $userArgsArray(session_handle) {
				set pimRtrConfig [::sth::sthCore::invoke stc::get $router -children-PimRouterConfig]
	
				#Add PIM Groups for ipv4/6 
				#6. configure group mapping for PIM
				set pimGrpBlkHandle [::sth::sthCore::invoke stc::create Pimv[string trim $version]GroupBlk -under $pimRtrConfig]
	
				#Here is when we decide if test is for (S,G), (*,G), or (*,*,RP); groupType is being set in here.
				#For groupType "STARSTARRP", skip all in SG's and STARG's if/else block
				set pimGrps [GetPimGroupsSetup $pimGrpBlkHandle]
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle $pimGrps
	
				if {$groupType == "SG"} {
					#Only (S,G) can do join source, no enabling needed. It's an SG mode if source_pool_handle is passed and wildcard attr is 0.
					set pimJoinSrc [::sth::sthCore::invoke stc::get $pimGrpBlkHandle -children-pimv[string trim $version]joinsrc]
					array set joinSrcSettings [subst $[subst ::sth::multicast_group::${userArgsArray(source_pool_handle)}]]
					set pimJoinSrcSettings [GetPimJoinPruneSrc $pimJoinSrc $joinSrcSettings(optional_args)]
					::sth::sthCore::invoke stc::config $pimJoinSrc $pimJoinSrcSettings
					keylset returnKeyedList source_pool_handle $userArgsArray(source_pool_handle) 
				} elseif {$groupType == "STARG"} {
					#Only (*,G) can do prune source, after enable a pruning feature
					#The spec doesn't specify specific source pruning feature, so assume to prune all, which is same as STARSTARG.
					set enable_source_pruning 0 ;#if ever needed, this code makes specific pruning
					if {$enable_source_pruning} {
						set pimPruneSrc [::sth::sthCore::invoke stc::get $pimGrpBlkHandle -children-pimv[string trim $version]prunesrc]
						array set leaveSrcSettings [subst $[subst ::sth::multicast_group::${userArgsArray(source_pool_handle)}]]
						set pimPruneSrcSettings [GetPimJoinPruneSrc $pimPruneSrc $leaveSrcSettings(optional_args)]
						::sth::sthCore::invoke stc::config $pimPruneSrc $pimPruneSrcSettings
						keylset returnKeyedList source_pool_handle $userArgsArray(source_pool_handle) 
					}
				}
	
				#rp map is supported only if a bsr is enable.
				if {[string match -nocase $testType "c_bsr"]} {
					#setup relation to rpmap block. If block is found, configure. If not, ignore.
					set pimRpMapBlkHandle "unassigned"
					set pimRpMapBlkHandle [::sth::sthCore::invoke stc::get $pimRtrConfig -children-Pimv[string trim $version]RpMap]
					if {$pimRpMapBlkHandle != ""} {
						::sth::sthCore::invoke stc::config $pimRpMapBlkHandle "-JoinedGroup-targets $userArgsArray(group_pool_handle)"
					}
				}
	
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle "-JoinedGroup-targets $userArgsArray(group_pool_handle)"
				lappend pimGrpBlkHandle_collection $pimGrpBlkHandle
			}
			keylset returnKeyedList handle $pimGrpBlkHandle_collection ;#return pim group membership handle
			keylset returnKeyedList group_pool_handle $userArgsArray(group_pool_handle)
		}
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_group_config_modify {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_group_config_modify"
    variable userArgsArray
    variable version
    variable groupType
    variable testType
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set returnKeyedList ""
    set retVal [catch {
        if {[info exists userArgsArray(session_handle)] == 0} {
            return -code error "Error:  Unable to create PIM group configuration. Missing mandatory argument -session_handle"
        }
        if {[info exists userArgsArray(group_pool_handle)] == 0} {
            return -code error "Error:  Unable to create an PIM group membership. Missing mandatory argument -group_pool_handle"
        }

        #set pim global setup here
		set pimGlobalConfig [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-PimGlobalConfig]
        set pimGlobalSettings [GetPimGlobalConfig]
		::sth::sthCore::invoke stc::config $pimGlobalConfig $pimGlobalSettings
        set pimRtrConfig [::sth::sthCore::invoke stc::get $userArgsArray(session_handle) -children-PimRouterConfig]
		
        #Add PIM Groups for ipv4/6
        #6. configure pim group linking
	    set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $pimRtrConfig -children-Pimv[string trim $version]GroupBlk]

		if {$pimGrpBlkHandle eq ""} {
			emulation_pim_register_group_config_modify returnKeyedList
		} else {
			#Here is when we decide if test is for (S,G), (*,G), or (*,*,RP); groupType is being set in here.
			#For groupType "STARSTARRP", just omitt any thing in SG's and STARG's if/else block
			set pimGrps [GetPimGroupsSetup $pimGrpBlkHandle]
			::sth::sthCore::invoke stc::config $pimGrpBlkHandle $pimGrps
	
			if {$groupType == "SG"} {
				#Only (S,G) can do join source, no enabling needed. It's an SG mode if source_pool_handle is passed in.
				set pimJoinSrc [::sth::sthCore::invoke stc::get $pimGrpBlkHandle -children-pimv[string trim $version]joinsrc]
				array set joinSrcSettings [subst $[subst ::sth::multicast_group::${userArgsArray(source_pool_handle)}]]
				set pimJoinSrcSettings [GetPimJoinPruneSrc $pimJoinSrc $joinSrcSettings(optional_args)]
				::sth::sthCore::invoke stc::config $pimJoinSrc $pimJoinSrcSettings
				keylset returnKeyedList source_pool_handle $userArgsArray(source_pool_handle) 
			} elseif {$groupType == "STARG"} {
				#Only (*,G) can do prune source, after enable a pruning feature
				#The spec doesn't specify source pruning feature, so assume to prune all, which is same as STARSTARRP.
				set enable_source_pruning 0
				if {$enable_source_pruning} {
					set pimPruneSrc [::sth::sthCore::invoke stc::get $pimGrpBlkHandle -children-pimv[string trim $version]prunesrc]
					array set leaveSrcSettings [subst $[subst ::sth::multicast_group::${userArgsArray(source_pool_handle)}]]
					set pimPruneSrcSettings [GetPimJoinPruneSrc $pimPruneSrc $leaveSrcSettings(optional_args)]
					::sth::sthCore::invoke stc::config $pimPruneSrc $pimPruneSrcSettings
					keylset returnKeyedList source_pool_handle $userArgsArray(source_pool_handle) 
				}
			}
			#rp map is supported only if a bsr is enable.
			if {[string match -nocase $testType "c_bsr"]} {
				#setup relation to rpmap block. If block is found, configure. If not, ignore.
				set pimRpMapBlkHandle "unassigned"
				set pimRpMapBlkHandle [::sth::sthCore::invoke stc::get $pimRtrConfig $version]RpMap]
				if {$pimRpMapBlkHandle != ""} {
					::sth::sthCore::invoke stc::config $pimRpMapBlkHandle "-JoinedGroup-targets $userArgsArray(group_pool_handle)"
				}
			}
	
			::sth::sthCore::invoke stc::config $pimGrpBlkHandle "-JoinedGroup-targets $userArgsArray(group_pool_handle)"
			keylset returnKeyedList handle $pimGrpBlkHandle ;#return pim group membership handle
			keylset returnKeyedList group_pool_handle $userArgsArray(group_pool_handle)
		}
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_register_group_config_create {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_register_group_config_create"
    variable userArgsArray
    variable version
    upvar $level $keyedList returnKeyedList
    set returnKeyedList ""
    set retVal [catch {
        foreach router $userArgsArray(session_handle) {
            set pimRtrConfig [::sth::sthCore::invoke stc::get $router -children-PimRouterConfig]
			set pimGrpBlkHandle [::sth::sthCore::invoke stc::create Pimv[string trim $version]RegisterBlk -under $pimRtrConfig]
			
			if {[info exists userArgsArray(rp_ip_addr)]} {
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle -RpIpAddr  $userArgsArray(rp_ip_addr)
			}
			if {[info exists userArgsArray(group_pool_handle)]} {
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle -AssociatedMulticastGroup-targets  $userArgsArray(group_pool_handle)
			}
			if {[info exists userArgsArray(source_group_mapping)]} {
				switch -- $userArgsArray(source_group_mapping) {
					fully_meshed {
						# I'm hoping that BACKBONE and FULLY_MESHED are the same.
						set source_group_mapping "BACKBONE"
					}
					one_to_one {
						set source_group_mapping "PAIR"
					}
				}
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle -MulticastGroupToSourceDistribution  $source_group_mapping
			}
			if {[info exists userArgsArray(source_pool_handle)]} {
				array unset sourcearray
				::sth::multicast_group::emulation_multicast_group_getSrcPool $userArgsArray(source_pool_handle) sourcearray
	
				::sth::sthCore::invoke stc::config $pimGrpBlkHandle.Ipv4NetworkBlock \
					-StartIpList   $sourcearray(ip_addr_start) \
					-PrefixLength  $sourcearray(ip_prefix_len) \
					-NetworkCount  $sourcearray(num_sources)   \
					-AddrIncrement $sourcearray(ip_addr_step)
			}
			##config registerblk
            lappend pimGrpBlkHandle_collection $pimGrpBlkHandle
        }
        keylset returnKeyedList handle $pimGrpBlkHandle_collection ;#return pim group membership handle
        keylset returnKeyedList group_pool_handle $userArgsArray(group_pool_handle)
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}
proc ::sth::emulation_pim_register_group_config_modify {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_register_group_config_modify"
    variable userArgsArray
    variable version
    upvar $level $keyedList returnKeyedList
    set returnKeyedList ""
    set retVal [catch {
        
		set pimRtrConfig [::sth::sthCore::invoke stc::get $userArgsArray(session_handle) -children-PimRouterConfig]
		set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $pimRtrConfig -children-Pimv[string trim $version]RegisterBlk]
		
		if {[info exists userArgsArray(rp_ip_addr)]} {
			::sth::sthCore::invoke stc::config $pimGrpBlkHandle -RpIpAddr  $userArgsArray(rp_ip_addr)
		}
		if {[info exists userArgsArray(group_pool_handle)]} {
			::sth::sthCore::invoke stc::config $pimGrpBlkHandle -AssociatedMulticastGroup-targets  $userArgsArray(group_pool_handle)
		}
		if {[info exists userArgsArray(source_group_mapping)]} {
			switch -- $userArgsArray(source_group_mapping) {
				fully_meshed {
					# I'm hoping that BACKBONE and FULLY_MESHED are the same.
					set source_group_mapping "BACKBONE"
				}
				one_to_one {
					set source_group_mapping "PAIR"
				}
			}
			::sth::sthCore::invoke stc::config $pimGrpBlkHandle -MulticastGroupToSourceDistribution  $source_group_mapping
		}
		if {[info exists userArgsArray(source_pool_handle)]} {
			array unset sourcearray
			::sth::multicast_group::emulation_multicast_group_getSrcPool $userArgsArray(source_pool_handle) sourcearray

			::sth::sthCore::invoke stc::config $pimGrpBlkHandle.Ipv4NetworkBlock \
				-StartIpList   $sourcearray(ip_addr_start) \
				-PrefixLength  $sourcearray(ip_prefix_len) \
				-NetworkCount  $sourcearray(num_sources)   \
				-AddrIncrement $sourcearray(ip_addr_step)
		}

        keylset returnKeyedList handle $pimGrpBlkHandle ;#return pim group membership handle
        keylset returnKeyedList group_pool_handle [::sth::sthCore::invoke stc::get $pimGrpBlkHandle -AssociatedMulticastGroup-targets]
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_group_config_delete {keyedList {level 1}} {
    ::sth::sthCore::log debug "emulation_pim_group_config_delete"
    variable userArgsArray
    upvar $level $keyedList returnKeyedList
    array unset deviceList
    set returnKeyedList ""
    set retVal [catch {
        if {[info exists userArgsArray(handle)] == 0} {
            return -code error "Error:  Unable to clear PIM group configuration. Missing mandatory argument -handle"
        }

        foreach handle $userArgsArray(handle) {
            set pimGrpBlkHandleList ""
            array set objectTypeArray [::sth::sthCore::invoke stc::perform GetObjectInfo -Object $handle]
            switch -- [string tolower $objectTypeArray(-ObjectType)] {
                emulateddevice -
                router -
                host {
                    set routerConfig [::sth::sthCore::invoke stc::get $handle -children-PimRouterConfig]
                    if { $routerConfig ne "" } {
                        set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $routerConfig -children-Pimv4GroupBlk]
                        set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
						set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $routerConfig -children-Pimv6GroupBlk]
                        set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
						set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $routerConfig -children-Pimv4RegisterBlk]
                        set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
						set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $routerConfig -children-Pimv6RegisterBlk]
                        set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
                    }
                }
                pimrouterconfig {
                    set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $handle -children-Pimv4GroupBlk]
                    set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
					set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $handle -children-Pimv6GroupBlk]
                    set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
					set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $handle -children-Pimv4RegisterBlk]
                    set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
					set pimGrpBlkHandle [::sth::sthCore::invoke stc::get $handle -children-Pimv6RegisterBlk]
                    set pimGrpBlkHandleList [concat $pimGrpBlkHandleList $pimGrpBlkHandle]
                }
				pimv6groupblk -
                pimv4registerblk -
				pimv6registerblk -
                pimv4groupblk {
                    lappend pimGrpBlkHandleList $handle
                }
            }
            
            foreach pimGrpBlkHandle $pimGrpBlkHandleList {
                ::sth::sthCore::invoke stc::delete $pimGrpBlkHandle
                
            }
        }                
    } returnedString]

    if {$retVal} {
           ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        keylset returnKeyedList handle $userArgsArray(handle)
		if {[info exists userArgsArray(group_pool_handle)]} {
			keylset returnKeyedList group_pool_handle $userArgsArray(group_pool_handle)
		}
        keylset returnKeyedList source_pool_handle "need_to_add_this"     
    }
    return -code $retVal $returnKeyedList
}

proc ::sth::emulation_pim_config_getPimRouterConfigList { inputHdlList } {
    variable userArgsArray
    set pimRouterConfigList ""

    set retVal [catch {
        foreach inputHdl $inputHdlList {
            if {[string match "host*" $inputHdl] || [string match "router*" $inputHdl] || [string match "emulateddevice*" $inputHdl]} {
                set pimRouterConfig [::sth::sthCore::invoke "stc::get $inputHdl -children-PimRouterConfig"]
                lappend pimRouterConfigList $pimRouterConfig
            } else {
                #current input handle is PimRouterConfig handle, nothing needs to do
                lappend pimRouterConfigList $inputHdl
            }
        }
    } returnedString]

    if {$retVal} {
        return -code $retVal $returnedString
    } else {
        return $pimRouterConfigList
    }
}
