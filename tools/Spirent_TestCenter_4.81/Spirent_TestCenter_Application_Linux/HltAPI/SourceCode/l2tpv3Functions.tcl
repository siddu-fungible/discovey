namespace eval ::sth::l2tpv3:: {
   
    proc ::sth::l2tpv3::l2tpConfigPortSessionBlock_create { returnStringName } {
       
        variable userArgsArray
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        upvar 1 $returnStringName returnKeyedList
        
        foreach param {l2_encap mode l2tp_node_type l2tpv3_src_count l2tpv3_dst_count l2tpv3_src_addr l2tpv3_dst_addr l2tpv3_dst_step l2tpv3_src_step  
                       l2tpv3_mac_addr l2tpv3_mac_step qinq_incr_mode vlan_id_outer vlan_count_outer vlan_id_step_outer vlan_user_priority_outer vlan_id vlan_id_step 
                       vlan_count vlan_user_priority num_tunnels sessions_per_tunnel } {
            set $param $userArgsArray($param)
        }

        set argumentList_port {}
       
        set argumentList_l2tpblock {}
        set argumentList_sessionblock {}
        
        
        foreach switchName [array names userArgsArray ] {
            if {($switchName eq "use_gateway_as_remote_ipv6addr") && ($userArgsArray(ip_encap) eq "IPV4") } {
                continue
            } elseif {($userArgsArray(ip_encap) eq "IPV6") && (($switchName eq "use_gateway_as_remote_ipv4addr") ||  ($switchName eq "ipv4_tos"))} {
                continue
            }
            set procFunc [::sth::sthCore::getModeFunc  ::sth::l2tpv3:: l2tpv3_config $switchName creat]
            set stcObj     [::sth::sthCore::getswitchprop ::sth::l2tpv3:: l2tpv3_config $switchName stcobj]
            set stcAttr     [::sth::sthCore::getswitchprop ::sth::l2tpv3:: l2tpv3_config $switchName stcattr]
            
            if {[regexp -nocase  "L2tpPortConfig"  $stcObj ] } {
                if {$procFunc == ""} {
                    lappend argumentList_port -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_port $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }                
            }  elseif {[regexp -nocase  "L2tpv3BlockConfig"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_l2tpblock -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_l2tpblock $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "L2tpv3SessionBlockParams"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_sessionblock  -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_sessionblock  $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } 
        }
        # Handle the wildcards
        
        if {[info exists userArgsArray(secret_wc)] || [info exists userArgsArray(hostname_wc)]} {
            if {[catch {::sth::l2tpv3::processConfigCmd_wildcard argumentList_l2tpblock returnKeyedList} err]} {
                #puts "8 processConfigCmd_wildcard  Failed: $err"
                ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::processConfigCmd_wildcard  Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
       
       
        set l2tpPort [::sth::sthCore::invoke stc::get  $userArgsArray(port_handle) -children-L2tpPortConfig]
        ::sth::sthCore::invoke stc::config $l2tpPort "$argumentList_port"
        if {[regexp -nocase  $l2_encap "ethernet_ii"] } {
            set IfStack "L2tpv3If Ipv4If EthIIIf"
            set IfCount "1 1 1"
        } elseif {[regexp -nocase  $l2_encap "ethernet_ii_vlan"] } {
            set IfStack "L2tpv3If Ipv4If VlanIf EthIIIf"
            set IfCount "1 1 1 1"
        } elseif {[regexp -nocase  $l2_encap "ethernet_ii_qinq"] } {
            set IfStack "L2tpv3If Ipv4If VlanIf VlanIf EthIIIf"
            set IfCount "1 1 1 1 1"
        }
      
        array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle)]
        set createdHost $DeviceCreateOutput(-ReturnList)
        set createdIpIf [::sth::sthCore::invoke stc::get $createdHost "-children-ipv4if"]
        set createdL2tpIf [::sth::sthCore::invoke stc::get $createdHost "-children-l2tpv3if"]
        set createdL2tpv3BlockConfig [::sth::sthCore::invoke stc::create L2tpv3BlockConfig -under $createdHost]
        ::sth::sthCore::invoke stc::config $createdL2tpv3BlockConfig "$argumentList_l2tpblock "
        ::sth::sthCore::invoke stc::config $createdIpIf "-toplevelif-Sources $createdHost -usesif-Sources $createdL2tpv3BlockConfig"
        set L2tpv3SessionBlockParams [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-L2tpv3SessionBlockParams]
        if {$L2tpv3SessionBlockParams eq ""} {
            set L2tpv3SessionBlockParams [::sth::sthCore::invoke stc::create L2tpv3SessionBlockParams -under $createdL2tpv3BlockConfig ]
        }
        ::sth::sthCore::invoke stc::config $L2tpv3SessionBlockParams "$argumentList_sessionblock "
        set Ipv4NetworkBlock [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-Ipv4NetworkBlock]
        set Ipv6NetworkBlock [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-Ipv6NetworkBlock]
       
        if {[regexp -nocase "lac" $l2tp_node_type]} {
            set deviceCount $l2tpv3_src_count
            ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr $l2tpv3_dst_addr  -RemoteIpv4AddrStep $l2tpv3_dst_step"
            ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Address $l2tpv3_src_addr   -AddrStep $l2tpv3_src_step -Gateway  $l2tpv3_dst_addr  -GatewayStep $l2tpv3_dst_step"
            if {[info exists userArgsArray(use_gateway_as_remote_ipv4addr)] && ($userArgsArray(use_gateway_as_remote_ipv4addr)==0 || $userArgsArray(use_gateway_as_remote_ipv4addr) eq "FALSE")} {
                if {[info exists userArgsArray(remote_ipv4addr)]} {
                    ::sth::sthCore::invoke stc::config $Ipv4NetworkBlock "-StartIpList $userArgsArray(remote_ipv4addr)"
                } 
            } elseif {[info exists userArgsArray(use_gateway_as_remote_ipv6addr)] && ($userArgsArray(use_gateway_as_remote_ipv6addr)==0 || $userArgsArray(use_gateway_as_remote_ipv6addr) eq "FALSE")} {
                if {[info exists userArgsArray(remote_ipv6addr)] } {
                    ::sth::sthCore::invoke stc::config $Ipv6NetworkBlock "-StartIpList $userArgsArray(remote_ipv6addr)"
                } 
            }
        } else {
            set deviceCount $l2tpv3_dst_count
            ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr  $l2tpv3_src_addr  -RemoteIpv4AddrStep  $l2tpv3_src_step"
            ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Address $l2tpv3_dst_addr  -AddrStep $l2tpv3_dst_step  -Gateway $l2tpv3_src_addr   -GatewayStep  $l2tpv3_src_step"
 
        }
        
        set createdVlanIf [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
        set createdEthIIIf [::sth::sthCore::invoke stc::get  $createdHost "-children-EthIIIf"]
        if {$l2tpv3_mac_addr  eq "00:10:94:00:00:02" } { 
            ::sth::sthCore::invoke stc::config $createdEthIIIf "-SrcMacStep $l2tpv3_mac_step"
        } else {
            ::sth::sthCore::invoke stc::config $createdEthIIIf "-SourceMac $l2tpv3_mac_addr  -SrcMacStep $l2tpv3_mac_step"
        }
        if {[regexp -nocase  "ethernet_ii_vlan"  $l2_encap] } {
            ::sth::sthCore::invoke stc::config $createdVlanIf "-VlanId $vlan_id   -IdStep $vlan_id_step  -IdRepeatCount [expr $deviceCount/$vlan_count  - 1]  -Priority $vlan_user_priority"
        } elseif {[regexp -nocase  "ethernet_ii_qinq"  $userArgsArray(l2_encap)] } {
            switch -exact -- $qinq_incr_mode {
                "both" {
                    if { $deviceCount % $vlan_count != 0 || $deviceCount % $vlan_count_outer != 0} {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vlan_count and vlan_count_outer when qinq_incr_mode is \"both\""}
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 0] "-VlanId $vlan_id   -IdStep $vlan_id_step  -IfRecycleCount $vlan_count  -Priority $vlan_user_priority"
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 1] "-VlanId $vlan_id_outer -IdStep $vlan_id_step_outer -IfRecycleCount $vlan_count_outer  -Priority $vlan_user_priority_outer"
                }
            
                "inner" {
                    if { $deviceCount % ($vlan_count * $vlan_count_outer) != 0} {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vlan_count * vlan_count_outer when qinq_incr_mode is \"inner\""}
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 0] "-VlanId $vlan_id   -IdStep $vlan_id_step  -IfRecycleCount $vlan_count  -Priority $vlan_user_priority"
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 1] "-VlanId $vlan_id_outer -IdStep $vlan_id_step_outer -IdRepeatCount [expr $vlan_count - 1] -IfRecycleCount $vlan_count_outer -Priority $vlan_user_priority_outer"
                }
                "outer" {
                    if { $deviceCount % ($vlan_count * $vlan_count_outer) != 0} {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vlan_count * vlan_count_outer when qinq_incr_mode is \"outer\""}
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 0] "-VlanId $vlan_id   -IdStep $vlan_id_step  -IdRepeatCount  [expr $vlan_count_outer - 1]  -IfRecycleCount $vlan_count -Priority $vlan_user_priority"
                    ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 1] "-VlanId $vlan_id_outer -IdStep $vlan_id_step_outer -IfRecycleCount $vlan_count_outer -Priority $vlan_user_priority_outer"
                }
            }
            
        }
        
        keylset returnKeyedList handles $createdHost
        keylset returnKeyedList handle $createdHost
       
    }
   
    proc ::sth::l2tpv3::l2tpConfigPortSessionBlock_modify { userInput rklName } {
        ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::l2tpv3::l2tpConfigPortSessionBlock_modify $rklName"
	variable userArgsArray
	upvar 1 $rklName returnKeyedList
       
        set userInputList ""
        for {set i 0} { $i < [expr [llength $userInput] / 2]} { incr i} {
            set index [expr {$i*2}]
            set nameNoDash [string range [lindex $userInput $index] 1 end]
            lappend userInputList $nameNoDash
        }
        #puts $userInputList
        foreach switchName [array names userArgsArray] {
            if { [lsearch $userInputList $switchName] == -1} {
                unset userArgsArray($switchName)
            }
        }
        if {[info exists userArgsArray(tun_auth)] && ![info exists userArgsArray(secret)]} {
            set userArgsArray(secret)  "spirent"
        }
        
	if {![info exists ::sth::l2tpv3::userArgsArray(handle)]} {
		return -code error "the switch \"-handle\" is mandatory in modify mode"
	} else {
	    set rtrHandle $::sth::l2tpv3::userArgsArray(handle)
            foreach Handle $rtrHandle {
                if {[catch {::sth::sthCore::invoke stc::get $Handle -children-l2tpv3blockconfig} l2tpv3blockconfigHandle]} {
	  	    return -code error "Invalid l2tpv3 host handle $rtrHandle"  
	        }
            }
	   
	}
        set createdHost $userArgsArray(handle)
        set porthandle [::sth::sthCore::invoke stc::get $createdHost -affiliationport-targets]
        set l2tpPort [::sth::sthCore::invoke stc::get  $porthandle -children-L2tpPortConfig]
        set l2tp_node_type [::sth::sthCore::invoke stc::get  $l2tpPort -L2tpNodeType]
        set userArgsArray(l2tp_node_type) $l2tp_node_type
	set argumentList_port {}
        set argumentList_l2tpblock {}
        set argumentList_vlanif {}
        set argumentList_vlanif_outer {}
        set argumentList_ethernet {}
        set argumentList_sessionblock {}
        foreach switchName [array names userArgsArray ] {
            set procFunc [::sth::sthCore::getModeFunc  ::sth::l2tpv3:: l2tpv3_config $switchName modify]
            set stcObj     [::sth::sthCore::getswitchprop ::sth::l2tpv3:: l2tpv3_config $switchName stcobj]
            set stcAttr     [::sth::sthCore::getswitchprop ::sth::l2tpv3:: l2tpv3_config $switchName stcattr]
            
            if {[regexp -nocase  "L2tpPortConfig"  $stcObj ] } {
                if {$procFunc == ""} {
                    lappend argumentList_port -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_port $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }                
            }  elseif {[regexp -nocase  "L2tpv3BlockConfig"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_l2tpblock -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_l2tpblock $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "L2tpv3SessionBlockParams"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_sessionblock  -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_sessionblock  $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "VlanIf"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_vlanif -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_vlanif $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "VlanIf_Outer"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_vlanif_outer -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_vlanif_outer $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "EthIIIf"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_ethernet -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tpv3::$procFunc argumentList_ethernet $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            }
        }
        # Handle the wildcards
        
        if {[info exists userArgsArray(secret_wc)] || [info exists userArgsArray(hostname_wc)]} {
            if {[catch {::sth::l2tpv3::processConfigCmd_wildcard argumentList_l2tpblock returnKeyedList} err]} {
                #puts "8 processConfigCmd_wildcard  Failed: $err"
                ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::processConfigCmd_wildcard  Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        
        if {$argumentList_port ne ""} {
            ::sth::sthCore::invoke stc::config $l2tpPort "$argumentList_port"
        }
        
        set createdL2tpv3BlockConfig [::sth::sthCore::invoke stc::get $createdHost "-children-L2tpv3BlockConfig"]
        set Ipv4NetworkBlock [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-Ipv4NetworkBlock]
        set Ipv6NetworkBlock [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-Ipv6NetworkBlock]
        if {$argumentList_l2tpblock ne "" } {
            ::sth::sthCore::invoke stc::config $createdL2tpv3BlockConfig "$argumentList_l2tpblock"
        }
        set L2tpv3SessionBlockParams [::sth::sthCore::invoke stc::get $createdL2tpv3BlockConfig -children-L2tpv3SessionBlockParams] 
        if {$argumentList_sessionblock ne ""} {
            ::sth::sthCore::invoke stc::config $L2tpv3SessionBlockParams "$argumentList_sessionblock"
        
        }
        set createdEthIIIf [::sth::sthCore::invoke stc::get  $createdHost "-children-EthIIIf"]
        if {$argumentList_ethernet ne "" } {
            ::sth::sthCore::invoke stc::config $createdEthIIIf "$argumentList_ethernet"
        }
        set createdVlanIf [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
        if {$argumentList_vlanif ne ""} {
            ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 0] "$argumentList_vlanif"
            ::sth::sthCore::invoke stc::config [lindex $createdVlanIf 1] "$argumentList_vlanif"
        }
        if {($argumentList_vlanif ne "" ) && ($argumentList_vlanif_outer eq "")}  {
            ::sth::sthCore::invoke stc::config $createdVlanIf "$argumentList_vlanif"
        }
        set createdIpIf [::sth::sthCore::invoke stc::get $createdHost "-children-ipv4if"]
        set createdL2tpIf [::sth::sthCore::invoke stc::get $createdHost "-children-l2tpv3if"]
        
        
       
        if {[regexp -nocase "lac" $l2tp_node_type]} {
            if {[info exists userArgsArray(l2tpv3_src_count)]} {
                set deviceCount $l2tpv3_src_count
                ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            }
            if {[info exists userArgsArray(l2tpv3_dst_addr)]} {
                ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr $l2tpv3_dst_addr"
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Gateway  $l2tpv3_dst_addr"
            }
            if {[info exists userArgsArray(l2tpv3_dst_step)]} {
                ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4AddrStep $l2tpv3_dst_step"
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-GatewayStep $l2tpv3_dst_step"
            }
            if {[info exists userArgsArray(l2tpv3_src_addr)]} {
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Address $l2tpv3_src_addr"
            }
            if {[info exists userArgsArray(l2tpv3_src_step)]} {
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-AddrStep $l2tpv3_src_step"
            }
            if {[info exists userArgsArray(use_gateway_as_remote_ipv4addr)] && $userArgsArray(use_gateway_as_remote_ipv4addr)==0} {
                if {[info exists userArgsArray(remote_ipv4addr)]} {
                    ::sth::sthCore::invoke stc::config $Ipv4NetworkBlock "-StartIpList $userArgsArray(remote_ipv4addr)"
                } 
            }
            if {[info exists userArgsArray(use_gateway_as_remote_ipv6addr)] && $userArgsArray(use_gateway_as_remote_ipv6addr)==0} {
                if {[info exists userArgsArray(remote_ipv6addr)] } {
                    ::sth::sthCore::invoke stc::config $Ipv6NetworkBlock "-StartIpList $userArgsArray(remote_ipv6addr)"
                } 
            }
        } else {
            if {[info exists userArgsArray(l2tpv3_dst_count)]} {
                set deviceCount $l2tpv3_dst_count
                ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            }
             if {[info exists userArgsArray(l2tpv3_src_addr)]} {
                ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr $l2tpv3_src_addr"
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Gateway $l2tpv3_src_addr"
            }
            if {[info exists userArgsArray(l2tpv3_src_step)]} {
                ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4AddrStep $l2tpv3_src_step"
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-GatewayStep  $l2tpv3_src_step"
            }
            if {[info exists userArgsArray(l2tpv3_dst_addr)]} {
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Address $l2tpv3_dst_addr"
            }
            if {[info exists userArgsArray(l2tpv3_dst_step)]} {
                ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-AddrStep $l2tpv3_dst_step"
            }
            
        }
        
        keylset returnKeyedList handles $createdHost
        keylset returnKeyedList handle $createdHost
       
    }
    proc ::sth::l2tpv3::l2tpConfigPortSessionBlock_delete { rklName } {
        ::sth::sthCore::log hltcall "Internal HLTAPI call executed ::sth::l2tpv3::l2tpConfigPortSessionBlock_delete $rklName"
	
	upvar 1 $rklName returnKeyedList
        set l2tpv3Routers {}
        # user can specify port_handle, which will remove all ancp routers under it. Or specify specific router handles
	if {[info exists ::sth::l2tpv3::userArgsArray(port_handle)]} {
            set portHandle $::sth::l2tpv3::::userArgsArray(port_handle)
    	    set affRouters [::sth::sthCore::invoke stc::get $portHandle -affiliationport-sources]
    	    # verify which of these routers are l2tpv3 routers
    	    
    	    foreach Handle $affRouters {
                set l2tpv3blockconfigHandle [::sth::sthCore::invoke stc::get $Handle -children-l2tpv3blockconfig]
	  	if ($l2tpv3blockconfigHandle ne "" ) {
                    lappend l2tpv3Routers $l2tpv3blockconfigHandle
                }
    	    }
	} elseif {[info exists ::sth::l2tpv3::userArgsArray(handle)]} {
	    set affRouters $::sth::l2tpv3::userArgsArray(handle)
	    foreach Handle $affRouters {
                set l2tpv3blockconfigHandle [::sth::sthCore::invoke stc::get $Handle -children-l2tpv3blockconfig]
	  	if ($l2tpv3blockconfigHandle ne "" ) {
                    lappend l2tpv3Routers $l2tpv3blockconfigHandle
                }
    	    }
	} else {
	    return -code error "must specify either \"-port_handle\" or \"-handle\"."
	}
	
	foreach l2tpv3Rtr $l2tpv3Routers {
	    ::sth::sthCore::invoke stc::delete $l2tpv3Rtr
	}
        
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList
    }
      
	
  
    proc ::sth::l2tpv3::processConfigCmd_usersetting { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        set _OrigHltCmdName "l2tpv3_config"
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        set val $switchValue
        
        if {[info exists ::sth::l2tpv3::[set _OrigHltCmdName]_[set switchName]_fwdmap]} {
            set val [set ::sth::l2tpv3::[set _OrigHltCmdName]_[set switchName]_fwdmap([set switchValue])]
        }
        #if { [regexp -nocase "lns" $userArgsArray(l2tp_node_type)] && ( [regexp -nocase "AutoRetryCount" $switchName ] ||  [regexp -nocase "EnableAutoRetry" $switchName] ) } {
        #    return $returnKeyedList
        #} 
        lappend configList -$switchName $val

        return $returnKeyedList
    }
    
    
    
    proc ::sth::l2tpv3::processConfigCmd_wildcard { configListName returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray  
        set _OrigHltCmdName "l2tpv3_config"
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        # Calculate the start/end  4 marker characters
        foreach marker {question pound bang dollar} {
            set ${marker}_start 1
            set ${marker}_count 1
            set ${marker}_step 1
            set ${marker}_fill 0
            set ${marker}_repeat 0
            set ${marker}_end 1
            
            foreach type {start fill end} {
                if {[info exists userArgsArray(wildcard_[set marker]_[set type])]} {
                    set ${marker}_${type} $userArgsArray(wildcard_[set marker]_[set type])
                }
            }
            if {[set [set marker]_end] < [set [set marker]_start]} {
                #puts "36 wildcard_${marker}_end ([set [set marker]_end]) must not be less than wildcard_${marker}_start ([set [set marker]_start])"
                ::sth::sthCore::processError returnKeyedList "wildcard_${marker}_end ([set [set marker]_end]) must not be less than wildcard_${marker}_start ([set [set marker]_start])"
                return -code error $returnKeyedList 
            }
            set ${marker}_count [expr "([set [set marker]_end] - [set [set marker]_start]) + 1"]
            set ${marker}_string "@x([set [set marker]_start],[set [set marker]_count],[set [set marker]_step],[set [set marker]_fill],[set [set marker]_repeat])"
            #puts "DEBUG:${marker}_string=[set [set marker]_string]"
        }
        set attr_list "{hostname anonymous} {secret pass}"
        
        foreach attr $attr_list {
            foreach {attrName attrDefault} $attr {}
            if {[info exists userArgsArray(${attrName}_wc)]} {
                set $attrName $attrDefault
                if {[info exists userArgsArray($attrName)]} {
                    set $attrName $userArgsArray($attrName)
                }
                foreach pair {{# pound} {? question} {! bang} {$ dollar}} {
                    foreach {symbol marker} $pair {};
                    regsub -all \\$symbol [set [set attrName]] [set [set marker]_string] $attrName
                }
                lappend configList -$attrName [set [set attrName]]
            }
        }

        return $returnKeyedList
    }
    
   
    
    proc ::sth::l2tpv3::processConfigCmd_secret { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray    
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        lappend configList -EnableDutAuthentication $userArgsArray(tun_auth)  -RxTunnelPassword $userArgsArray(secret) -TxTunnelPassword $userArgsArray(secret)
        return $returnKeyedList
    }
  
    proc ::sth::l2tpv3::processl2tpv3GetCmd_state { attr returnInfoVarName keyName handle } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
    
        upvar 1 $returnInfoVarName returnKeyedList
        
        
        set portHandle [::sth::sthCore::invoke stc::get $handle -parent]
    
        set stateVal [::sth::sthCore::invoke stc::get $handle -portState]
    
        set connecting 0
        set connected 0
        set disconnecting 0
        set idle 0
         
        switch -glob -- $stateVal {
            "CONNECTING*" {
                set connecting 1
            }
            "CONNECTED*" {
                set connected 1
            }
            "DISCONNECTING*" {
                set disconnecting 1
            }
            "TERMINATING*" {
                #do nothing 
            }
            "IDLE*" {
                set idle 1
            }
            "NONE" {
                # Do nothing - No host blocks are configured for L2TP
            }
            default {
                #puts "42 processL2TPGetCmd_state: Could not resolve state: $stateVal: $err"
                ::sth::sthCore::processError returnKeyedList "::sth::l2tpv3::processl2tpv3GetCmd_state Could not resolve state: $stateVal: $err"
                return -code error $returnKeyedList 
            }
        }

         
        keylset returnKeyedList ${keyName}.connecting $connecting
        keylset returnKeyedList ${keyName}.connected $connected
        keylset returnKeyedList ${keyName}.disconnecting $disconnecting
        keylset returnKeyedList ${keyName}.idle $idle
         
        
        return $::sth::sthCore::SUCCESS
    }
    
    
    
    
    
    proc ::sth::l2tpv3::processl2tpv3GetCmd { attr returnInfoVarName keyName handle } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tpv3::l2tpv3_stats_${keyName}_stcattr($attr)]
    
        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]
    
        #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.$attr $val
    
        return $::sth::sthCore::SUCCESS
    }
    
    
    proc ::sth::l2tpv3::processl2tpv3TunnelGetCmd { attr returnInfoVarName keyName L2TPTunnelId handle } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tpv3::l2tpv3_stats_${keyName}_stcattr($attr)]

        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]

    #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.${L2TPTunnelId}.$attr $val
        

        return $::sth::sthCore::SUCCESS     
    }
    
    
    
    
    
    
    proc ::sth::l2tpv3::processl2tpv3SessionGetCmd { attr returnInfoVarName keyName L2TPTunnelId L2TPSessionId handle } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tpv3::l2tpv3_stats_${keyName}_stcattr($attr)]

        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]

    #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.${L2TPTunnelId}.${L2TPSessionId}.$attr $val

        return $::sth::sthCore::SUCCESS     
    }
    
 
    
   
}
