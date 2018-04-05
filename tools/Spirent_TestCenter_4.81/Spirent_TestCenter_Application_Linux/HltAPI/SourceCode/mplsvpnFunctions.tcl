# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth::Mplsvpn {
    array set VpnHandleList {}
    set createResultQuery 0
}

proc ::sth::Mplsvpn::emulation_mpls_l2vpn_pe_config_enable { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "emulation_mpls_l2vpn_pe_config_enable"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "port_handle needed when configuring PE of MPLS L2VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #prepare switches
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(vpn_type)]} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_type) ldp_vpls
    }
    if { [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)] == "martini_pwe"} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_type) ldp_vpls
    }
    set vpnType [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)]
    
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]} {
        puts "INFO: -tunnel_handle is input, MPLS over GRE will be enable. P router is forced to be disable, -mpls_session_handle will be ignored."
        set $_hltSpaceCmdName\_user_input_args_array(enable_p_router) $FAILURE
    }
    if { [set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
        puts "INFO: -enable_p_router is enabled, Input Igp session and MPLS session will emulate P router."
    }
    
    set peRtrHdlList ""
    if { [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)] == "ldp_vpls"} {
        if { ![info exists $_hltSpaceCmdName\_user_input_args_array(targeted_ldp_session_handle)]} {
            ::sth::sthCore::processError returnKeyedList "-targeted_ldp_session_handle needed when configuring PE of LDP VC L2VPN." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        set peRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(targeted_ldp_session_handle)]
    } elseif { [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)] == "bgp_vpls"} {
        if { ![info exists $_hltSpaceCmdName\_user_input_args_array(vpls_bgp_session_handle)]} {
            ::sth::sthCore::processError returnKeyedList "-vpls_bgp_session_handle needed when configuring PE of BGP VPLS." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        set peRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(vpls_bgp_session_handle)]
    } else {
        ::sth::sthCore::processError returnKeyedList "Wrong VPN type value." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set igpRtrHdlList ""
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(igp_session_handle)]} {
        ::sth::sthCore::processError returnKeyedList "igp_session_handle needed when configuring PE of MPLS L2vpn." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set igpRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(igp_session_handle)]
    
    set mplsRtrHdlList ""
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(mpls_session_handle)]} {
        set mplsRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(mpls_session_handle)]
    }
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(pe_count)]} {
        set peCount 1
    } else {
        set peCount [set $_hltSpaceCmdName\_user_input_args_array(pe_count)]
    }
    
    if { [llength $peRtrHdlList] != $peCount} {
        ::sth::sthCore::processError returnKeyedList "Input targeted ldp sesion handle number do not equal to -pe_count value." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { ![set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
        if { [llength $igpRtrHdlList] != $peCount} {
            ::sth::sthCore::processError returnKeyedList "Error: Input igp sesion handles number do not equal to -pe_count value, when P router is disabled." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { ($mplsRtrHdlList != "") && ([llength $mplsRtrHdlList] != $peCount)} {
            ::sth::sthCore::processError returnKeyedList "Error: Input mpls sesion handles number do not equal to -pe_count value, when P router is disabled." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    #configure PEs
    set rtnPeHdlList ""
    set routerIndex 1 
    for { set i 0} {$i < $peCount} {incr i} {
        set peRouterHandle [lindex $peRtrHdlList $i]
        set igpRouterHandle ""
        set mplsRouterHandle ""
        if { ![set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
            set igpRouterHandle [lindex $igpRtrHdlList $i]
            if { $mplsRtrHdlList != ""} {
                set mplsRouterHandle [lindex $mplsRtrHdlList $i]
            }
        } else {
            set igpRouterHandle [lindex $igpRtrHdlList 0]
            if { $mplsRtrHdlList != ""} {
                set mplsRouterHandle [lindex $mplsRtrHdlList 0]
            }
        }
        switch -regexp $peRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $peRouterHandle
                
                if {[catch {set peRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        switch -regexp $igpRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $igpRouterHandle
                
                if {[catch {set igpRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        switch -regexp $mplsRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $mplsRouterHandle
                
                if {[catch {set mplsRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]} {
            if { $peRouterHandle != $igpRouterHandle} {
                ::sth::sthCore::processError returnKeyedList "Error: input Targeted LDP session and IGP session pair are not on same emulated device when configuring MPLS over GRE." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {set ethIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-EthIIIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-EthIIIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {set vlanIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-VlanIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-VlanIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {set greIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-GreIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-GreIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            #configure switches
            #configure GRE interface
            set tunnelCfgList [set $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]
            if { $greIfHandle == ""} {
                if { $vlanIfHandle != ""} {
                    set lowerIf $vlanIfHandle
                } else {
                    set lowerIf $ethIfHandle
                }
                if {[catch {set tempIfHdl [::sth::sthCore::invoke stc::get $lowerIf -StackedOnEndpoint-Sources]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -StackedOnEndpoint-Sources from $lowerIf, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {set ipv4IfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-Ipv4If]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-Ipv4If from $peRouterHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {set greIfHandle [::sth::createGreStack $tunnelCfgList $peRouterHandle $lowerIf $routerIndex]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $tempIfHdl "-StackedOnEndpoint-Targets $greIfHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while config -StackedOnEndpoint-Targets $greIfHandle to $tempIfHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IfHandle "-StackedOnEndpoint-Targets $greIfHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while config -StackedOnEndpoint-Targets $greIfHandle to $ipv4IfHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            } else {
                if {[ catch {::sth::configGreStack $tunnelCfgList $peRouterHandle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            incr routerIndex
            
        } else {
            if { ![set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)] && ($peRouterHandle == $igpRouterHandle)} {
                lappend rtnPeHdlList $peRouterHandle
                continue
            }
            if { $mplsRtrHdlList != ""} {
                set providerRouter $mplsRouterHandle

            } else {
                set providerRouter $igpRouterHandle
            }
         
			::sth::sthCore::invoke stc::perform LinkCreateCommand -LinkType {VRF Provider Link} -SrcDev $peRouterHandle -DstDev $providerRouter
        }
        lappend rtnPeHdlList $peRouterHandle
    }
    
    keylset returnKeyedList handle $rtnPeHdlList
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l2vpn_pe_config_disable { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "emulation_mpls_l2vpn_pe_config_disable"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when disable PE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
    set peRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    foreach peRouterHandle $peRtrHdlList {
        set linkTypeList "L3ForwardingLink VrfProviderLink IpForwardingLink MplsHierarchicalLink MplsL2VpnPeToPLink MplsForwardingLink"
            if {[catch {set linkHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-VrfProviderLink]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -VrfProviderLink from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $linkHandle != ""} {
                if {[catch {::sth::sthCore::invoke stc::perform LinkDeleteCommand -Link $linkHandle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while running stc::perform LinkDeleteCommand -Link $linkHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
    }
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l2vpn_site_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l2vpn_site_config"    
    set _hltCmdName "emulation_mpls_l2vpn_site_config_create"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "port_handle needed when creating vpn site of MPLS L2VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(pe_handle)]} {
        puts "INFO: PE handle is input, configured VPN sites will be treated as on provider-side test port (behind emulated PE-router)."
        set portType "provider"
        set peHandleList [set $_hltSpaceCmdName\_user_input_args_array(pe_handle)]
    } else {
        puts "INFO: PE handle is not input, configured VPN sites will be treated as on customer-side test port (directly connected to SUT)."
        set portType "customer"
    }
    
    #prepare switches
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(vpn_type)]} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_type) ldp_vpls
    }
    if { [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)] == "martini_pwe"} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_type) ldp_vpls
    }
    set vpnType [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)]
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(site_count)]} {
        set siteCount 1
    } else {
        set siteCount [set $_hltSpaceCmdName\_user_input_args_array(site_count)]
    }
    
    if { $portType == "provider"} {
        if {[llength $peHandleList] != $siteCount} {
            ::sth::sthCore::processError returnKeyedList  "Error: Number of input pe handle is not equal to site count while creating site in a provider port." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    set siteHdlList ""
    #create and configure each site
    for {set i 1} {$i <= $siteCount} {incr i} {
        
        set hostCfgList ""
        set vpnCfgList ""
        #step VPN ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id)]} {
            set vpnId [set $_hltSpaceCmdName\_user_input_args_array(vpn_id)]
        } else {
            set vpnId 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]} {
            set $_hltSpaceCmdName\_user_input_args_array(vpn_id) [expr $vpnId + [set $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]]
        }
        lappend vpnCfgList vpn_id $vpnId
        
        #step VLAN ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id)]} {
            set vlanId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]
                set $_hltSpaceCmdName\_user_input_args_array(vlan_id) [expr $vlanId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)] * $count]
            } else {
                set step 0
            }
            
            lappend hostCfgList vlan_id $vlanId vlan_id_step $step vlan_id_count $count
        }
        
        #step VLAN outer ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer)]} {
            set vlanOuterId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)]
                set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer) [expr $vlanOuterId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)] * $count]
            } else {
                set step 0
            }
            
            lappend hostCfgList vlan_id_outer $vlanOuterId vlan_id_outer_step $step vlan_id_outer_count $count
        }
        
        #step MAC address
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr)]} {
            set macAddr [set $_hltSpaceCmdName\_user_input_args_array(mac_addr)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]
                set $_hltSpaceCmdName\_user_input_args_array(mac_addr) [::sth::sthCore::macStep $macAddr $step $count]
            } else {
                set step 00:00:00:00:00:00
            }
            
            lappend hostCfgList mac_addr $macAddr mac_addr_step $step mac_addr_count $count
        }
        
        #step VPN site Info
        if { $vpnType == "bgp_vpls"} {
            #step VE ID
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(ve_id)]} {
                
                set veId [set $_hltSpaceCmdName\_user_input_args_array(ve_id)]
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
                    set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
                } else {
                    set count 1
                }
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(ve_id_step)]} {
                    set step [set $_hltSpaceCmdName\_user_input_args_array(ve_id_step)]
                    set $_hltSpaceCmdName\_user_input_args_array(ve_id) [expr $veId + [set $_hltSpaceCmdName\_user_input_args_array(ve_id_step)] * $count]
                } else {
                    set step 1
                }
                
                lappend vpnCfgList ve_id $veId ve_id_step $step
            }
            
            #step route distinguisher
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_start)]} {
                
                set rd [set $_hltSpaceCmdName\_user_input_args_array(rd_start)]
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
                    set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
                } else {
                    set count 1
                }
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_step)]} {
                    set step [set $_hltSpaceCmdName\_user_input_args_array(rd_step)]
                    set $_hltSpaceCmdName\_user_input_args_array(rd_start) [::sth::Mplsvpn::rd_rt_step $rd [set $_hltSpaceCmdName\_user_input_args_array(rd_step)] $count]
                } else {
                    set step 0:0
                }
                
                lappend vpnCfgList rd_start $rd rd_step $step
            }
            
            #prepare other swithes
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
                lappend vpnCfgList vpn_block_count $count
            }
        } else {
            #step VC ID
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id)]} {
                set vcId [set $_hltSpaceCmdName\_user_input_args_array(vc_id)]
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id_count)]} {
                    set count [set $_hltSpaceCmdName\_user_input_args_array(vc_id_count)]
                } else {
                    set count 1
                }
                if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id_step)]} {
                    set step [set $_hltSpaceCmdName\_user_input_args_array(vc_id_step)]
                    set $_hltSpaceCmdName\_user_input_args_array(vc_id) [expr $vcId + [set $_hltSpaceCmdName\_user_input_args_array(vc_id_step)] * $count]
                }
                
                lappend vpnCfgList vc_id $vcId vc_id_step $step vc_id_count $count
            }
        }
        
        #process pe handle
        if { $portType == "provider"} {
            set peHandle [lindex $peHandleList [expr $i-1]]
            switch -regexp $peHandle {
                routerconfig {
                    if {[catch {set peHandle [::sth::sthCore::invoke stc::get $peHandle -Parents]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $peHandle, errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
                emulateddevice -
                router {}
            }
            
            if { ![info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
                if {[catch {set peIp [::sth::sthCore::invoke stc::get $peHandle -RouterId]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $peHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr) $peIp
            }
        }
        
        #process pe_loopback_ip_addr and pe_loopback_ip_prefix
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
            set peIp [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]
            lappend vpnCfgList pe_loopback_ip_addr $peIp
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_step)]
                set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr) [::sth::sthCore::updateIpAddress 4 $peIp $step 1]
            }
        }
        
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]} {
            lappend vpnCfgList pe_loopback_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]
        }
        
        #create site host
        if {[catch {set hostHdl [::sth::Mplsvpn::createOneSiteHost $_OrigHltCmdName $hostCfgList $portHandle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::createOneSiteHost failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #configure site host
        if {[catch {set hostHdl [::sth::Mplsvpn::configOneSiteHost $_OrigHltCmdName $hostHdl $hostCfgList]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::configOneSiteHost failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #configure vrf customer link if on provider side
        if { $portType == "provider" } {
            set peHandle
            
			::sth::sthCore::invoke stc::perform LinkCreateCommand -LinkType {VRF Customer Link} -SrcDev $hostHdl -DstDev $peHandle
        }
        
        #create vpn site information object
        if {[catch {set VpnSiteInfoHandle [::sth::Mplsvpn::createVpnSiteInfo $_OrigHltCmdName $vpnType $vpnCfgList $hostHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::createVpnSiteInfo failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #configure vpn site information
        if {[catch {::sth::Mplsvpn::configureVpnSiteInfo $_OrigHltCmdName $vpnType $VpnSiteInfoHandle $vpnCfgList $hostHdl} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::configureVpnSiteInfo failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        lappend siteHdlList $hostHdl
    }
    
    keylset returnKeyedList handle $siteHdlList
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l2vpn_site_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l2vpn_site_config"    
    set _hltCmdName "emulation_mpls_l2vpn_site_config_modify"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when modifying vpn site of MPLS L2VPN over GRE." {}
        set cmdState $FAILURE
    return $returnKeyedList
    } else {
    set hostHandle [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    #prepare switches
    
    #delete switches which has default value but hasn't been input
    set userInputList ""
    for {set i 0} { $i < [expr [llength $userInput] / 2]} { incr i} {
        set index [expr {$i*2}]
        set nameNoDash [string range [lindex $userInput $index] 1 end]
        lappend userInputList $nameNoDash
    }
    foreach switchName [array names $_hltSpaceCmdName\_user_input_args_array] {
        if { [lsearch $userInputList $switchName] == -1} {
            unset $_hltSpaceCmdName\_user_input_args_array($switchName)
        }
    }
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(vpn_type)]} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_type) ldp_vpls
    }
    set vpnType [set $_hltSpaceCmdName\_user_input_args_array(vpn_type)]
    
    set siteHdlList ""
    #create and configure each site
    set hostCfgList ""
    set vpnCfgList ""
    #step VPN ID
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id)]} {
        set vpnId [set $_hltSpaceCmdName\_user_input_args_array(vpn_id)]
    } else {
        set vpnId 1
    }
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_id) [expr $vpnId + [set $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]]
    }
    lappend vpnCfgList vpn_id $vpnId
    
    #step VLAN ID
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id)]} {
        set vlanId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id)]
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_count)]} {
            set count [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_count)]
        } else {
            set count 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]
            set $_hltSpaceCmdName\_user_input_args_array(vlan_id) [expr $vlanId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)] * $count]
        } else {
            set step 0
        }
        
        lappend hostCfgList vlan_id $vlanId vlan_id_step $step vlan_id_count $count
    }
    
    #step VLAN outer ID
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer)]} {
        set vlanOuterId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer)]
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_count)]} {
            set count [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_count)]
        } else {
            set count 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)]
            set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer) [expr $vlanOuterId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_outer_step)] * $count]
        } else {
            set step 0
        }
        
        lappend hostCfgList vlan_id_outer $vlanOuterId vlan_id_outer_step $step vlan_id_outer_count $count
    }
    
    #step MAC address
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr)]} {
        set macAddr [set $_hltSpaceCmdName\_user_input_args_array(mac_addr)]
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]} {
            set count [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]
        } else {
            set count 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]
            set $_hltSpaceCmdName\_user_input_args_array(mac_addr) [::sth::sthCore::macStep $macAddr $step $count]
        } else {
            set step 00:00:00:00:00:00
        }
        
        lappend hostCfgList mac_addr $macAddr mac_addr_step $step mac_addr_count $count
    }
    
    #step VPN site Info
    if { $vpnType == "bgp_vpls"} {
        #step VE ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(ve_id)]} {
            
            set veId [set $_hltSpaceCmdName\_user_input_args_array(ve_id)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(ve_id_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(ve_id_step)]
                set $_hltSpaceCmdName\_user_input_args_array(ve_id) [expr $veId + [set $_hltSpaceCmdName\_user_input_args_array(ve_id_step)] * $count]
            } else {
                set step 1
            }
            
            lappend vpnCfgList ve_id $veId ve_id_step $step
        }
        
        #step route distinguisher
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_start)]} {
            
            set rd [set $_hltSpaceCmdName\_user_input_args_array(rd_start)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(rd_step)]
                set $_hltSpaceCmdName\_user_input_args_array(rd_start) [::sth::Mplsvpn::rd_rt_step $rd [set $_hltSpaceCmdName\_user_input_args_array(rd_step)] $count]
            } else {
                set step 0:0
            }
            
            lappend vpnCfgList rd_start $rd rd_step $step
        }
        
        #prepare other swithes
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]} {
            set count [set $_hltSpaceCmdName\_user_input_args_array(vpn_block_count)]
            lappend vpnCfgList vpn_block_count $count
        }
    } else {
        #step VC ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id)]} {
            set vcId [set $_hltSpaceCmdName\_user_input_args_array(vc_id)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(vc_id_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vc_id_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(vc_id_step)]
                set $_hltSpaceCmdName\_user_input_args_array(vc_id) [expr $vcId + [set $_hltSpaceCmdName\_user_input_args_array(vc_id_step)] * $count]
            }
            
            lappend vpnCfgList vc_id $vcId vc_id_step $step vc_id_count $count
        }
    }
    
    #process pe_loopback_ip_addr and pe_loopback_ip_prefix
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
        lappend vpnCfgList pe_loopback_ip_addr [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]
    }
    
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]} {
        lappend vpnCfgList pe_loopback_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]
    }
    
    #configure site host
    if {[catch {set hostHdl [::sth::Mplsvpn::configOneSiteHost $_OrigHltCmdName $hostHandle $hostCfgList]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::configOneSiteHost failed. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #get vpn site information object
    if {[catch {set VpnSiteInfoHandle [::sth::sthCore::invoke stc::get $hostHandle -MemberOfVpnSite-Targets]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Error occured while getting -MemberOfVpnSite-Targets from $hostHandle. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #configure vpn site information
    if {[catch {::sth::Mplsvpn::configureVpnSiteInfo $_OrigHltCmdName $vpnType $VpnSiteInfoHandle $vpnCfgList $hostHdl} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::configureVpnSiteInfo failed. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    lappend siteHdlList $hostHdl
    
    keylset returnKeyedList handle $siteHdlList
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l2vpn_site_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l2vpn_site_config"    
    set _hltCmdName "emulation_mpls_l2vpn_site_config_delete"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when modifying vpn site of MPLS L2VPN over GRE." {}
        set cmdState $FAILURE
    return $returnKeyedList
    } else {
    set hostHdlList [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    foreach hostHandle $hostHdlList {
        #get vpn site information object
        if {[catch {set VpnSiteInfoHandle [::sth::sthCore::invoke stc::get $hostHandle -MemberOfVpnSite-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Error occured while getting -MemberOfVpnSite-Targets from $hostHandle. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::delete $VpnSiteInfoHandle } errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting $VpnSiteInfoHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::delete $hostHandle } errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting $hostHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    set cmdState $SUCCESS
    return $SUCCESS
}
proc ::sth::Mplsvpn::createOneSiteHost {tableName cfgList portHandle} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    #set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "createOneSiteHost"
    set _hltNameSpace "::sth::Mplsvpn::"

    #upvar 1 $returnKeyedListVarName returnKeyedList
    #upvar 1 $cmdStatusVarName cmdState

    #set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    if { [info exists cfgAttrArr(vlan_id)] && [info exists cfgAttrArr(vlan_id_outer)]} {
        set ifList "VlanIf VlanIf EthIIIf" 
        set ifCount "1 1 1"
    } elseif { [info exists cfgAttrArr(vlan_id)] || [info exists cfgAttrArr(vlan_id_outer)]} {
        set ifList "VlanIf EthIIIf"
        set ifCount "1 1"
    } else {
        set ifList "EthIIIf"
        set ifCount "1"
    }
    
    set deviceCount 1
    if { [info exists cfgAttrArr(mac_addr_count)]} {
        set deviceCount [expr $deviceCount * $cfgAttrArr(mac_addr_count)]
    }
    if { [info exists cfgAttrArr(vlan_id_count)]} {
        set deviceCount [expr $deviceCount * $cfgAttrArr(vlan_id_count)]
    }
    if { [info exists cfgAttrArr(vlan_id_outer_count)]} {
        set deviceCount [expr $deviceCount * $cfgAttrArr(vlan_id_outer_count)]
    }
    
    if {[catch {::sth::sthCore::createStcHost $portHandle \
                                                $::sth::GBLHNDMAP(project) \
                                                hostObjHdl \
                                                $ifList \
                                                $ifCount \
                                                $deviceCount} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "createStcHost command FAILED. $errMsg";
        return $returnKeyedList
    }
    
    return $hostObjHdl
}

proc ::sth::Mplsvpn::configOneSiteHost {tableName hostObjHdl cfgList} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
     
    set _hltCmdName "configOneSiteHost"
    set _hltNameSpace "::sth::Mplsvpn::"

    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    array set cfgObjArr {}
	set cfgObjArr(EthIIIf) [::sth::sthCore::invoke stc::get $hostObjHdl -Children-EthIIIf]
	set VlanHdl [::sth::sthCore::invoke stc::get $hostObjHdl -Children-VlanIf]
    
    if {[llength $VlanHdl] == 2} {
        set cfgObjArr("VlanIf") [lindex $VlanHdl 0]
        set cfgObjArr(VlanIf_Outer) [lindex $VlanHdl 1]
    } elseif {[llength $VlanHdl] == 1} {
        if {[info exists cfgAttrArr(vlan_id)]} {
            set cfgObjArr(VlanIf) $VlanHdl
        } else {
            set cfgObjArr(VlanIf_Outer) $VlanHdl
        }
    }
    
    array set cfgStr {}
    foreach attrName [array names cfgAttrArr] {
        set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $tableName $attrName stcobj]
        set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $tableName $attrName stcattr]
        append cfgStr($stcObjName) " -$stcAttrName $cfgAttrArr($attrName)"
    }
    foreach obj [array names cfgObjArr] {
        if {![info exists cfgStr($obj)]} {
            continue
        }
		::sth::sthCore::invoke stc::config $cfgObjArr($obj) $cfgStr($obj)
    }
    
    return $hostObjHdl
}

proc ::sth::Mplsvpn::createVpnSiteInfo {tableName vpnType cfgList site } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
   
    set _hltCmdName "createVpnSiteInfo"
    set _hltNameSpace "::sth::Mplsvpn::"
    
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    #create VpnSiteInfoVplsXX
    if { $vpnType == "ldp_vpls"} {
        set cmd "set VpnSiteInfoHandle [::sth::sthCore::invoke stc::create VpnSiteInfoVplsLdp -under $::sth::GBLHNDMAP(project) ]"
        if {[catch {eval $cmd} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not create VpnSiteInfoVplsLdp object \
                -under $::sth::GBLHNDMAP(project), $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList         
        }
    } elseif { $vpnType == "bgp_vpls"} {
        set cmd "set VpnSiteInfoHandle [::sth::sthCore::invoke stc::create VpnSiteInfoVplsBgp -under $::sth::GBLHNDMAP(project) ]"
        if {[catch {eval $cmd} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not create VpnSiteInfoVplsBgp object \
                -under $::sth::GBLHNDMAP(project), $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList         
        }
    } elseif { $vpnType == "l3vpn"} {
        set cmd "set VpnSiteInfoHandle [::sth::sthCore::invoke stc::create VpnSiteInfoRfc2547 -under $::sth::GBLHNDMAP(project) ]"
        if {[catch {eval $cmd} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not create VpnSiteInfoRfc2547 object \
                -under $::sth::GBLHNDMAP(project), $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList         
        }
    } else {
            ::sth::sthCore::processError returnKeyedList "Error: wrong vpn type value."
            set cmdState $FAILURE
            return $returnKeyedList
    }
    
    return $VpnSiteInfoHandle
}
proc ::sth::Mplsvpn::configureVpnSiteInfo {tableName vpnType VpnSiteInfoHandle cfgList site } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    #set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "configureVpnSiteInfo"
    set _hltNameSpace "::sth::Mplsvpn::"
    
    #upvar 1 $returnKeyedListVarName returnKeyedList
    #upvar 1 $cmdStatusVarName cmdState
    
    #set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    if {[info exists cfgAttrArr(vpn_id)]} {
        set VpnId $cfgAttrArr(vpn_id)
        unset cfgAttrArr(vpn_id)
    } else {
        set VpnId 1
    }
    
    set cfgStr ""
    foreach attrName [array names cfgAttrArr] {
        set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $tableName $attrName stcattr]
        set switchValue $cfgAttrArr($attrName)
        if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $tableName $attrName $switchValue]} getStatus]} {
            append cfgStr " -$stcAttrName $attrValue"
        } else {
            append cfgStr " -$stcAttrName $switchValue"
        }
    }
    ::sth::sthCore::invoke stc::config $VpnSiteInfoHandle $cfgStr
    
    #create VpnIdGroup
    set vpnSiteHandleList ""
    if {[info exists ${_hltNameSpace}VpnHandleList($VpnId)]} {
        set VpnIdGroupHandle [set ${_hltNameSpace}VpnHandleList($VpnId)]
        #get the vpls sites handle which already bind in VpnIdGroup
		set vpnSiteHandleList [::sth::sthCore::invoke stc::get $VpnIdGroupHandle -MemberOfVpnIdGroup-targets]
    } else {
        set cmd "set VpnIdGroupHandle [::sth::sthCore::invoke stc::create VpnIdGroup -under $::sth::GBLHNDMAP(project)]"
		eval $cmd
		#add new VPN ID Group to grobal array 
        set ${_hltNameSpace}VpnHandleList($VpnId) $VpnIdGroupHandle
    }
    
    #save the old VpnSiteInfo object handle
    lappend vpnSiteHandleList $VpnSiteInfoHandle

    set cmd "::sth::sthCore::invoke stc::config $VpnIdGroupHandle {-MemberOfVpnIdGroup-targets {$vpnSiteHandleList}}"
	eval $cmd

    #Binding site VpnSiteInfoVplsLdp
    set cmd "::sth::sthCore::invoke stc::config $site {-MemberOfVpnSite-targets $VpnSiteInfoHandle}"
	eval $cmd

    return $SUCCESS
}

proc ::sth::Mplsvpn::rd_rt_step {startValue stepValue {stepCount 1}} {
    set startFirstValue [lindex [split $startValue ":"] 0]
    set startLastValue [lindex [split $startValue ":"] 1]
    
    set stepFirstValue [lindex [split $stepValue :] 0]
    set stepLastValue [lindex [split $stepValue :] 1]
    
    return [join [list [expr $startFirstValue + $stepFirstValue * $stepCount] [expr $startLastValue + $stepLastValue * $stepCount]] :]
}

proc ::sth::sthCore::createStcHost {portHandle parentHandle handleName ifStack ifCount deviceCount} {
	# Currently, a router is created directly under a project, and affiliates with a port.
	
	upvar 1 $handleName returnHandle
	set stcCmd {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate \
					  -ParentList $parentHandle \
                    -DeviceType "Host" \
                    -DeviceCount $deviceCount \
					  -IfStack $ifStack \
					  -IfCount $ifCount \
					  -Port $portHandle]}
	
	########### log stccall ###########
	::sth::sthCore::log stccall $stcCmd;

	if {[catch {eval $stcCmd} createStatus ]} {
		::sth::sthCore::log debug "\[createStcHost\] $stcCmd FAILED. $createStatus";
		return -code 1 -errorcode -1 $createStatus;
	} else {
		::sth::sthCore::log info "\[createStcHost\] $stcCmd PASSED. $createStatus";
		set returnHandle $DeviceCreateOutput(-ReturnList);
		return $::sth::sthCore::SUCCESS;
	}
	
}

proc ::sth::Mplsvpn::emulation_mpls_l3vpn_pe_config_enable { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS 
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l3vpn_pe_config"    
    set _hltCmdName "emulation_mpls_l3vpn_pe_config_enable"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "port_handle needed when configuring PE router." {}
        set cmdState $FAILURE
    return $returnKeyedList
    } else {
    set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
    ::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
    set cmdState $FAILURE
    return $returnKeyedList
    }
    
    #prepare switches
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]} {
        puts "INFO: -tunnel_handle is input, MPLS over GRE will be enable. P router is forced to be disable, IGP session, MPLS session (if exists) and BGP session of a PE router must be created on same emulated device."
        set $_hltSpaceCmdName\_user_input_args_array(enable_p_router) $FAILURE
    }
    if { [set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
        puts "INFO: -enable_p_router is enable, Input IGP session and MPLS session will emulate P router."
    }
    
    set bgpRtrHdlList ""
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(bgp_session_handle)]} {
        ::sth::sthCore::processError returnKeyedList "bgp_session_handle needed when configuring PE router ." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set bgpRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(bgp_session_handle)]
    
    set mplsRtrHdlList ""
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(mpls_session_handle)]} {
        set mplsRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(mpls_session_handle)]
    }
    
    set igpRtrHdlList ""
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(igp_session_handle)]} {
        ::sth::sthCore::processError returnKeyedList "igp_session_handle needed when configuring PE router ." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    set igpRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(igp_session_handle)]
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(pe_count)]} {
        set peCount 1
    } else {
        set peCount [set $_hltSpaceCmdName\_user_input_args_array(pe_count)]
    }
    
    if { [llength $bgpRtrHdlList] != $peCount} {
        ::sth::sthCore::processError returnKeyedList "Input BGP sesion handle number do not equal to -pe_count value." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { ![set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
        if { $mplsRtrHdlList != ""} {
            if { [llength $mplsRtrHdlList] != $peCount} {
                ::sth::sthCore::processError returnKeyedList "Input MPLS sesion handle number do not equal to -pe_count value, when P router is disabled." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    
        
        if { [llength $igpRtrHdlList] != $peCount} {
            ::sth::sthCore::processError returnKeyedList "Input IGP sesion handle number do not equal to -pe_count value, when P router is disabled." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    
    #configure PEs
    set rtnPeHdlList ""
    #routerIndex is used for GRE interface configuring
    set routerIndex 1
    set mplsRouterHandle ""
    for { set i 0} { $i < $peCount} {incr i} {
        set peRouterHandle [lindex $bgpRtrHdlList $i]
        if { [set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)]} {
            set igpRouterHandle [lindex $igpRtrHdlList 0]
            set mplsRouterHandle [lindex $mplsRtrHdlList 0]
        } else {
            set igpRouterHandle [lindex $igpRtrHdlList $i]
            if { $mplsRtrHdlList != ""} {
                set mplsRouterHandle [lindex $mplsRtrHdlList $i]
            }
            
        }
        
        switch -regexp $peRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $peRouterHandle
                
                if {[catch {set peRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        switch -regexp $igpRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $igpRouterHandle
                
                if {[catch {set igpRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        switch -regexp $mplsRouterHandle {
            routerconfig {
                set protoRtrCfgHdl $mplsRouterHandle
                
                if {[catch {set mplsRouterHandle [::sth::sthCore::invoke stc::get $protoRtrCfgHdl -Parents]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $protoRtrCfgHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            default {}
        }
        
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]} {
            if { $peRouterHandle != $igpRouterHandle} {
                ::sth::sthCore::processError returnKeyedList "Error: input BGP and IGP session pair ($peRouterHandle $igpRouterHandle) are not on same emulated device when configuring MPLS over GRE." {}
                set cmdState $FAILURE
                return $returnKeyedList
            } elseif { $mplsRouterHandle != ""} {
                if { $peRouterHandle != $mplsRouterHandle} {
                    ::sth::sthCore::processError returnKeyedList "Error: input BGP and MPLS session pair ($peRouterHandle $igpRouterHandle) are not on same emulated device when configuring MPLS over GRE." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            
            if {[catch {set ethIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-EthIIIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-EthIIIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {set vlanIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-VlanIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-VlanIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {set greIfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-GreIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-GreIf from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            #configure switches
            #configure GRE interface
            set tunnelCfgList [set $_hltSpaceCmdName\_user_input_args_array(tunnel_handle)]
            if { $greIfHandle == ""} {
                if { $vlanIfHandle != ""} {
                    set lowerIf $vlanIfHandle
                } else {
                    set lowerIf $ethIfHandle
                }
                if {[catch {set tempIfHdl [::sth::sthCore::invoke stc::get $lowerIf -StackedOnEndpoint-Sources]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -StackedOnEndpoint-Sources from $lowerIf, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {set ipv4IfHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-Ipv4If]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-Ipv4If from $peRouterHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {set greIfHandle [::sth::createGreStack $tunnelCfgList $peRouterHandle $lowerIf $routerIndex]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $tempIfHdl "-StackedOnEndpoint-Targets $greIfHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while config -StackedOnEndpoint-Targets $greIfHandle to $tempIfHdl, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IfHandle "-StackedOnEndpoint-Targets $greIfHandle"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while config -StackedOnEndpoint-Targets $greIfHandle to $ipv4IfHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            } else {
                if {[ catch {::sth::configGreStack $tunnelCfgList $peRouterHandle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList $errMsg {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            incr routerIndex
            
        } else {
            if { ![set $_hltSpaceCmdName\_user_input_args_array(enable_p_router)] && ($peRouterHandle == $igpRouterHandle)} {
                lappend rtnPeHdlList $peRouterHandle
                continue
            }
            if { $mplsRtrHdlList != ""} {
                set providerRouter $mplsRouterHandle
            } else {
                set providerRouter $igpRouterHandle
            }
			::sth::sthCore::invoke stc::perform LinkCreateCommand -LinkType {VRF Provider Link} -SrcDev $peRouterHandle -DstDev $providerRouter
        }
        
        lappend rtnPeHdlList $peRouterHandle
    }
    #returned PE handle list
    
    keylset returnKeyedList handle $rtnPeHdlList
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l3vpn_pe_config_disable { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l3vpn_pe_config"    
    set _hltCmdName "emulation_mpls_l3vpn_pe_config_disable"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when deleting PE of MPLS L3VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
    set peRtrHdlList [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    foreach peRouterHandle $peRtrHdlList {
        set linkTypeList "L3ForwardingLink VrfProviderLink IpForwardingLink MplsHierarchicalLink MplsL3VpnPeToPLink MplsForwardingLink"
        
            if {[catch {set linkHandle [::sth::sthCore::invoke stc::get $peRouterHandle -Children-VrfProviderLink]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -VrfProviderLink from $peRouterHandle, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $linkHandle != ""} {
                if {[catch {::sth::sthCore::invoke stc::perform LinkDeleteCommand -Link $linkHandle} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while running stc::perform LinkDeleteCommand -Link $linkHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
    }
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l3vpn_site_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l3vpn_site_config"    
    set _hltCmdName "emulation_mpls_l3vpn_site_config_create"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "port_handle needed when creating vpn site." {}
        set cmdState $FAILURE
    return $returnKeyedList
    } else {
    set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(pe_handle)]} {
        puts "INFO: PE handle is input, configured VPN sites will be treated as on provider-side test port (behind emulated PE-router)."
        set portType "provider"
        set peHandleList [set $_hltSpaceCmdName\_user_input_args_array(pe_handle)]
    } else {
        puts "INFO: PE handle is not input, configured VPN sites will be treated as on customer-side test port (directly connected to SUT)."
        set portType "customer"
    }
    
    #prepare switches
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(site_count)]} {
        set siteCount 1
    } else {
        set siteCount [set $_hltSpaceCmdName\_user_input_args_array(site_count)]
    }
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(device_count)]} {
        set deviceCount 1
    } else {
        set deviceCount [set $_hltSpaceCmdName\_user_input_args_array(device_count)]
    }
    
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(ce_session_handle)]} {
        set ceHdlList [set $_hltSpaceCmdName\_user_input_args_array(ce_session_handle)]
        if { [llength $ceHdlList] != $siteCount} {
            ::sth::sthCore::processError returnKeyedList "Input CE sesion handle number do not equal to -site_count value." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if { $portType == "provider"} {
        if {[llength $peHandleList] != $siteCount} {
            ::sth::sthCore::processError returnKeyedList "Error: Number of input pe handle is not equal to site count while creating site in a provider port."  {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    set siteHdlList ""
    #create and configure each site
    for {set i 1} {$i <= $siteCount} {incr i} {
        
        set routerCfgList ""
        set vpnCfgList ""
        
        lappend routerCfgList device_count $deviceCount
        
        #step VPN ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id)]} {
            set vpnId [set $_hltSpaceCmdName\_user_input_args_array(vpn_id)]
        } else {
            set vpnId 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]} {
            set $_hltSpaceCmdName\_user_input_args_array(vpn_id) [expr $vpnId + [set $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]]
        }
        lappend vpnCfgList vpn_id $vpnId
        
        #step IP address
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr)]} {
            set ipAddr [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr)]
            
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_step)]
                set $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr) [::sth::sthCore::updateIpAddress 4 $ipAddr $step $deviceCount]
            } else {
                set step 0.0.0.0
            }
            
            lappend routerCfgList interface_ip_addr $ipAddr interface_ip_step $step
        }
        
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_prefix)]} {
            lappend routerCfgList interface_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_prefix)]
        }
        
        #step VLAN ID
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id)]} {
            set vlanId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id)]
            
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]
                set $_hltSpaceCmdName\_user_input_args_array(vlan_id) [expr $vlanId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)] * $deviceCount]
            } else {
                set step 0
            }
            
            lappend routerCfgList vlan_id $vlanId vlan_id_step $step
        }
        
        #step MAC address
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr)]} {
            set macAddr [set $_hltSpaceCmdName\_user_input_args_array(mac_addr)]
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]} {
                set count [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]
            } else {
                set count 1
            }
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]
                set $_hltSpaceCmdName\_user_input_args_array(mac_addr) [::sth::sthCore::macStep $macAddr $step $deviceCount]
            } else {
                set step 00:00:00:00:00:00
            }
            
            lappend routerCfgList mac_addr $macAddr mac_addr_step $step
        }
        
        #step VPN site Info
        #step route distinguisher
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_start)]} {
            
            set rd [set $_hltSpaceCmdName\_user_input_args_array(rd_start)]
            
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(rd_step)]
                set $_hltSpaceCmdName\_user_input_args_array(rd_start) [::sth::Mplsvpn::rd_rt_step $rd [set $_hltSpaceCmdName\_user_input_args_array(rd_step)] 1]
            } else {
                set step 0:0
            }
            
            lappend vpnCfgList rd_start $rd 
        }
            
        #prepare other swithes for VPN site Info
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(enable_inter_as_option)]} {
            lappend vpnCfgList enable_inter_as_option [set $_hltSpaceCmdName\_user_input_args_array(enable_inter_as_option)]
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip)]} {
            lappend vpnCfgList loacal_asbr_ip [set $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip)]
        }
        
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip_prefix)]} {
            lappend vpnCfgList loacal_asbr_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip_prefix)]
        }
        
        #process pe handle
        if { $portType == "provider"} {
            set peHandle [lindex $peHandleList [expr $i - 1]]
            switch -regexp $peHandle {
                routerconfig {
                    if {[catch {set peHandle [::sth::sthCore::invoke stc::get $peHandle -Parents]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $peHandle, errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
                emulateddevice -
                router {}
            }
            
            if { ![info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
                if {[catch {set peIp [::sth::sthCore::invoke stc::get $peHandle -RouterId]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Parents from $peHandle, errMsg: $errMsg." {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr) $peIp
            }
        }
        
        #process pe_loopback_ip_addr and pe_loopback_ip_prefix
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
            set peIp [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]
            lappend vpnCfgList pe_loopback_ip_addr $peIp
            if {[info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_step)]} {
                set step [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_step)]
                set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr) [::sth::sthCore::updateIpAddress 4 $peIp $step 1]
            }
        }
        
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]} {
            lappend vpnCfgList pe_loopback_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]
        }
        
        #create site router
        if {[catch {set routerHdl [::sth::Mplsvpn::createOneSiteIpv4Host $_OrigHltCmdName $routerCfgList $portHandle $deviceCount]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::createOneSiteIpv4Host failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #configure site router
        if {[catch {::sth::Mplsvpn::configOneSiteIpv4Host $_OrigHltCmdName $routerHdl $routerCfgList} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::configOneSiteHost failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #config relation with bgp session
        if { [info exists $_hltSpaceCmdName\_user_input_args_array(ce_session_handle)]} {
            set ceHdl [lindex $ceHdlList [expr $i - 1]]
            
            switch -regexp $ceHdl {
                emulateddevice -
                router { }
                routerconfig {
                    if {[catch {set ceHdl [::sth::sthCore::invoke stc::get $ceHdl -Parents]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error occured, errMsg: $errMsg." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
            }
            
			::sth::sthCore::invoke stc::perform LinkCreateCommand -LinkType {L3 Forwarding Link} -SrcDev $routerHdl -DstDev $ceHdl
        }
        
        #configure vrf customer link if on provider side
        if { $portType == "provider" } {
            ::sth::sthCore::invoke stc::perform LinkCreateCommand -LinkType {VRF Customer Link} -SrcDev $routerHdl -DstDev $peHandle
        }
        
        #create vpn site information object
        if {[catch {set VpnSiteInfoHandle [::sth::Mplsvpn::createVpnSiteInfo $_OrigHltCmdName "l3vpn" $vpnCfgList $routerHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::createVpnSiteInfo failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        #configure vpn site information
        if {[catch {::sth::Mplsvpn::configureVpnSiteInfo $_OrigHltCmdName "l3vpn" $VpnSiteInfoHandle $vpnCfgList $routerHdl} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::configureVpnSiteInfo failed. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        lappend siteHdlList $routerHdl
    }
    
    keylset returnKeyedList handle $siteHdlList
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l3vpn_site_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l3vpn_site_config"    
    set _hltCmdName "emulation_mpls_l3vpn_site_config_modify"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when modifying vpn site of MPLS L3VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
    set siteHandle [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    if { ![info exists $_hltSpaceCmdName\_user_input_args_array(device_count)]} {
        set deviceCount 1
    } else {
        set deviceCount [set $_hltSpaceCmdName\_user_input_args_array(device_count)]
    }
    
    #prepare switches
    
    #delete switches which has default value but hasn't been input
    set userInputList ""
    for {set i 0} { $i < [expr [llength $userInput] / 2]} { incr i} {
        set index [expr {$i*2}]
        set nameNoDash [string range [lindex $userInput $index] 1 end]
        lappend userInputList $nameNoDash
    }
    puts $userInputList
    foreach switchName [array names $_hltSpaceCmdName\_user_input_args_array] {
        if { [lsearch $userInputList $switchName] == -1} {
            unset $_hltSpaceCmdName\_user_input_args_array($switchName)
        }
    }
    
    #configure site
        
    set routerCfgList ""
    set vpnCfgList ""
    
    lappend routerCfgList device_count $deviceCount
    
    #step VPN ID
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id)]} {
        set vpnId [set $_hltSpaceCmdName\_user_input_args_array(vpn_id)]
    } else {
        set vpnId 1
    }
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]} {
        set $_hltSpaceCmdName\_user_input_args_array(vpn_id) [expr $vpnId + [set $_hltSpaceCmdName\_user_input_args_array(vpn_id_step)]]
    }
    lappend vpnCfgList vpn_id $vpnId
    
    #step IP address
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr)]} {
        set ipAddr [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr)]
        
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_step)]
            set $_hltSpaceCmdName\_user_input_args_array(interface_ip_addr) [::sth::sthCore::updateIpAddress 4 $ipAddr $step $deviceCount]
        } else {
            set step 0.0.0.0
        }
        
        lappend routerCfgList interface_ip_addr $ipAddr interface_ip_step $step
    }
    
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(interface_ip_prefix)]} {
        lappend routerCfgList interface_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(interface_ip_prefix)]
    }
    
    #step VLAN ID
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id)]} {
        set vlanId [set $_hltSpaceCmdName\_user_input_args_array(vlan_id)]
        
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)]
            set $_hltSpaceCmdName\_user_input_args_array(vlan_id) [expr $vlanId + [set $_hltSpaceCmdName\_user_input_args_array(vlan_id_step)] * $deviceCount]
        } else {
            set step 0
        }
        
        lappend routerCfgList vlan_id $vlanId vlan_id_step $step
    }
    
    #step MAC address
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr)]} {
        set macAddr [set $_hltSpaceCmdName\_user_input_args_array(mac_addr)]
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]} {
            set count [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_count)]
        } else {
            set count 1
        }
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(mac_addr_step)]
            set $_hltSpaceCmdName\_user_input_args_array(mac_addr) [::sth::sthCore::macStep $macAddr $step $deviceCount]
        } else {
            set step 00:00:00:00:00:00
        }
        
        lappend routerCfgList mac_addr $macAddr mac_addr_step $step
    }
    
    #step VPN site Info
    #step route distinguisher
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_start)]} {
        
        set rd [set $_hltSpaceCmdName\_user_input_args_array(rd_start)]
        
        if {[info exists $_hltSpaceCmdName\_user_input_args_array(rd_step)]} {
            set step [set $_hltSpaceCmdName\_user_input_args_array(rd_step)]
            set $_hltSpaceCmdName\_user_input_args_array(rd_start) [::sth::Mplsvpn::rd_rt_step $rd [set $_hltSpaceCmdName\_user_input_args_array(rd_step)] 1]
        } else {
            set step 0:0
        }
        
        lappend vpnCfgList rd_start $rd 
    }
        
    #prepare other swithes for VPN site Info
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(enable_inter_as_option)]} {
        lappend vpnCfgList enable_inter_as_option [set $_hltSpaceCmdName\_user_input_args_array(enable_inter_as_option)]
    }
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip)]} {
        lappend vpnCfgList loacal_asbr_ip [set $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip)]
    }
    
    if {[info exists $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip_prefix)]} {
        lappend vpnCfgList loacal_asbr_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(loacal_asbr_ip_prefix)]
    }
    
    #process pe_loopback_ip_addr and pe_loopback_ip_prefix
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]} {
        lappend vpnCfgList pe_loopback_ip_addr [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_addr)]
    }
    
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]} {
        lappend vpnCfgList pe_loopback_ip_prefix [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]
    }
    
    if { [info exists $_hltSpaceCmdName\_user_input_args_array(device_count)]} {
        lappend routerCfgList device_count [set $_hltSpaceCmdName\_user_input_args_array(pe_loopback_ip_prefix)]
    }
    
    #configure site router
    if {[catch {::sth::Mplsvpn::configOneSiteIpv4Host $_OrigHltCmdName $siteHandle $routerCfgList} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Commond ::sth::Mplsvpn::configOneSiteHost failed. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #configure vpn site information
    if {[catch {set VpnSiteInfoHandle [::sth::sthCore::invoke stc::get $siteHandle -MemberOfVpnSite-targets]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while getting -MemberOfVpnSite-targets from $siteHandle : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    if {[catch {::sth::Mplsvpn::configureVpnSiteInfo $_OrigHltCmdName "l3vpn" $VpnSiteInfoHandle $vpnCfgList $siteHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Command ::sth::Mplsvpn::configureVpnSiteInfo failed. $errMsg." {} 
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    keylset returnKeyedList handle $siteHandle
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_l3vpn_site_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_l3vpn_site_config"    
    set _hltCmdName "emulation_mpls_l3vpn_site_config_delete"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when modifying vpn site of MPLS L3VPN over GRE." {}
        set cmdState $FAILURE
    return $returnKeyedList
    } else {
    set routerHdlList [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    foreach routerHandle $routerHdlList {
        #get vpn site information object
        if {[catch {set VpnSiteInfoHandle [::sth::sthCore::invoke stc::get $routerHandle -MemberOfVpnSite-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Error occured while getting -MemberOfVpnSite-Targets from $hostHandle. $errMsg." {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::delete $VpnSiteInfoHandle } errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting $VpnSiteInfoHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::delete $routerHandle } errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting $routerHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Mplsvpn::emulation_mpls_control_start { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_control"    
    set _hltCmdName "emulation_mpls_control_start"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when starting vpn site of MPLS VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
    set deviceHandle [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $deviceHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Unable to start devices $deviceHandle. ErrMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mplsvpn::emulation_mpls_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mpls_control"    
    set _hltCmdName "emulation_mpls_control_stop"
    set _hltNameSpace "::sth::Mplsvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if the handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "-handle needed when stopping vpn site of MPLS VPN over GRE." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
    set deviceHandle [set $_hltSpaceCmdName\_user_input_args_array(handle)]
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $deviceHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Unable to start devices $deviceHandle. ErrMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mplsvpn::createOneSiteIpv4Host {tableName cfgList portHandle deviceCount} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    #set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "createOneSiteIpv4Host"
    set _hltNameSpace "::sth::Mplsvpn::"

    #upvar 1 $returnKeyedListVarName returnKeyedList
    #upvar 1 $cmdStatusVarName cmdState

    #set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    if { [info exists cfgAttrArr(vlan_id)]} {
        set ifList "Ipv4If VlanIf EthIIIf"
        set ifCount "1 1 1"
    } else {
        set ifList "Ipv4If EthIIIf"
        set ifCount "1 1"
    }
    
    if {[catch {::sth::sthCore::createStcHost $portHandle \
                                                $::sth::GBLHNDMAP(project) \
                                                routerObjHdl \
                                                $ifList \
                                                $ifCount \
                                                $deviceCount} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "createStcHost command FAILED. $errMsg";
        return $returnKeyedList
    }
    
    return $routerObjHdl
}

proc ::sth::Mplsvpn::configOneSiteIpv4Host {tableName routerObjHdl cfgList} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    #set _OrigHltCmdName "emulation_mpls_l2vpn_pe_config"    
    set _hltCmdName "configOneSiteIpv4Host"
    set _hltNameSpace "::sth::Mplsvpn::"

    #upvar 1 $returnKeyedListVarName returnKeyedList
    #upvar 1 $cmdStatusVarName cmdState

    #set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_hltCmdName "
    
    array set cfgAttrArr $cfgList
    
    array set cfgObjArr {}
	set cfgObjArr(EthIIIf) [::sth::sthCore::invoke stc::get $routerObjHdl -Children-EthIIIf]
    set cfgObjArr(Ipv4If) [::sth::sthCore::invoke stc::get $routerObjHdl -Children-Ipv4If]
    
    if {[info exists cfgAttrArr(vlan_id)]} {
		set VlanHdl [::sth::sthCore::invoke stc::get $routerObjHdl -Children-VlanIf]
        
        if { $VlanHdl == ""} {
			set VlanHdl [::sth::sthCore::invoke stc::create VlanIf -under $routerObjHdl "-StackedOnEndpoint-Targets $cfgObjArr(EthIIIf)"]

            if {[catch {::sth::sthCore::invoke stc::config $Ipv4If "-StackedOnEndpoint-Targets $VlanHdl"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while config \"-StackedOnEndpoint-Targets $VlanHdl\" to $Ipv4If, errMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        set cfgObjArr(VlanIf) $VlanHdl
    }

    
    array set cfgStr {}
    foreach attrName [array names cfgAttrArr] {
        set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $tableName $attrName stcobj]
        set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $tableName $attrName stcattr]
        append cfgStr($stcObjName) " -$stcAttrName $cfgAttrArr($attrName)"
    }
    foreach obj [array names cfgObjArr] {
        if {![info exists cfgStr($obj)]} {
            continue
        }
		::sth::sthCore::invoke stc::config $cfgObjArr($obj) $cfgStr($obj)
    }
    
    return $SUCCESS
}

#end of script
