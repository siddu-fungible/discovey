namespace eval ::sth::l2tp:: {
   
    proc ::sth::l2tp::l2tpConfigPortSessionBlock { returnStringName } {
       
        variable userArgsArray
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        upvar 1 $returnStringName returnKeyedList
        
        foreach param {vci vpi  vci_step vpi_step vci_count vpi_count l2_encap mode l2tp_src_count l2tp_dst_count l2tp_src_addr l2tp_dst_addr l2tp_dst_step l2tp_src_step ppp_server_ip ppp_client_ip 
                                ppp_server_step ppp_client_step l2tp_mac_addr l2tp_mac_step qinq_incr_mode vlan_id_outer vlan_count_outer vlan_id_step_outer vlan_user_priority_outer vlan_id vlan_id_step 
                                vlan_count vlan_user_priority num_tunnels sessions_per_tunnel pvc_incr_mode   } {
           set $param $userArgsArray($param)
        }

        set argumentList_port {}
        set argumentList_ppp_port {}
        set argumentList_l2tpblock {}
        set argumentList_pppol2tpv2 {}
        set argumentList_pppseverippool {}
        
        
        foreach switchName [array names userArgsArray ] {
            set procFunc [::sth::sthCore::getModeFunc  ::sth::l2tp:: l2tp_config $switchName creat]
            set stcObj     [::sth::sthCore::getswitchprop ::sth::l2tp:: l2tp_config $switchName stcobj]
            set stcAttr     [::sth::sthCore::getswitchprop ::sth::l2tp:: l2tp_config $switchName stcattr]
            
            if {[regexp -nocase  "L2tpPortConfig"  $stcObj ] } {
                if {$procFunc == ""} {
                    lappend argumentList_port -$stcAttr $userArgsArray($switchName)
                } else {
                    if { [regexp -nocase "attempt_rate" $switchName]} {
                        lappend argumentList_ppp_port -ConnectRate $userArgsArray($switchName)
                    }
                    if {[catch {::sth::l2tp::$procFunc argumentList_port $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tp::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }                
            } elseif {[regexp -nocase  "PppoxPortConfig"  $stcObj ] } {
                if { [regexp -nocase "attempt_rate" $switchName]} {
                    lappend argumentList_ppp_port -ConnectRate $userArgsArray($switchName)
                } elseif {$procFunc == ""} {
                    lappend argumentList_ppp_port -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tp::$procFunc argumentList_ppp_port $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tp::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }                
            } elseif {[regexp -nocase  "L2tpv2BlockConfig"  $stcObj ]} {
                if {$procFunc == ""} {
                    lappend argumentList_l2tpblock -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tp::$procFunc argumentList_l2tpblock $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tp::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    }
                }
            } elseif {[regexp -nocase  "PppoL2tpBlockConfig"  $stcObj ] } {
                if {$procFunc == ""} {
                    lappend argumentList_pppol2tpv2 -$stcAttr $userArgsArray($switchName)
                } else {
                    if {[catch {::sth::l2tp::$procFunc argumentList_pppol2tpv2 $stcAttr $userArgsArray($switchName) returnKeyedList} err]} {
                        #puts "3 $procFunc Failed: $err"
                        ::sth::sthCore::processError returnKeyedList "::sth::l2tp::$procFunc Failed: $err" {}
                        return -code error $returnKeyedList 
                    } 
                }
            } elseif {[regexp -nocase  "PppoxServerIpv4PeerPool"  $stcObj ] } {
                lappend argumentList_pppseverippool -$stcAttr $userArgsArray($switchName) 
            }
        }
       
        set l2tpPort [::sth::sthCore::invoke stc::get  $userArgsArray(port_handle) -children-L2tpPortConfig]
        set pppoxPort [::sth::sthCore::invoke stc::get  $userArgsArray(port_handle) -children-PppoxPortConfig]
        ::sth::sthCore::invoke stc::config $pppoxPort "$argumentList_ppp_port -EmulationType PPPOL2TP"
        ::sth::sthCore::invoke stc::config $l2tpPort "$argumentList_port"
        
        # Handle the wildcards
        if {[info exists userArgsArray(username_wc)] || [info exists userArgsArray(password_wc)] } {
            if {[catch {::sth::l2tp::processConfigCmd_wildcard argumentList_pppol2tpv2 returnKeyedList} err]} {
                #puts "7 processConfigCmd_wildcard  Failed: $err"
                ::sth::sthCore::processError returnKeyedList "processConfigCmd_wildcard  Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        if {[info exists userArgsArray(secret_wc)] || [info exists userArgsArray(hostname_wc)]} {
            if {[catch {::sth::l2tp::processConfigCmd_wildcard argumentList_l2tpblock returnKeyedList} err]} {
                #puts "8 processConfigCmd_wildcard  Failed: $err"
                ::sth::sthCore::processError returnKeyedList "::sth::l2tp::processConfigCmd_wildcard  Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
     
        
        # Create the l2tp Client Blk and config the value
        
        if {[regexp -nocase  "atm"  $l2_encap] } {
            set IfStack "Ipv4If PppIf L2tpv2If Ipv4If Aal5If"
            set IfCount "1 1 1 1 1"
        } elseif {[regexp -nocase  $l2_encap "ethernet_ii"] } {
            set IfStack "Ipv4If PppIf L2tpv2If Ipv4If EthIIIf"
            set IfCount "1 1 1 1 1"
        } elseif {[regexp -nocase  $l2_encap "ethernet_ii_vlan"] } {
            set IfStack "Ipv4If PppIf L2tpv2If Ipv4If VlanIf EthIIIf"
            set IfCount "1 1 1 1 1 1"
        } elseif {[regexp -nocase  $l2_encap "ethernet_ii_qinq"] } {
            set IfStack "Ipv4If PppIf L2tpv2If Ipv4If VlanIf VlanIf EthIIIf"
            set IfCount "1 1 1 1 1 1 1"
        }
      
array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Host -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle)]
                            set createdHost $DeviceCreateOutput(-ReturnList)

        
        set createdIpIf [::sth::sthCore::invoke stc::get $createdHost "-children-ipv4if"]
        set createdL2tpIf [::sth::sthCore::invoke stc::get $createdHost "-children-l2tpv2if"]
set createdL2tpv2BlockConfig [::sth::sthCore::invoke stc::create L2tpv2BlockConfig -under $createdHost]
        ::sth::sthCore::invoke stc::config $createdL2tpv2BlockConfig "$argumentList_l2tpblock -UsesIf-targets $createdL2tpIf"
        if {[regexp -nocase "lac" $mode]} {
            set deviceCount $l2tp_src_count
            ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr $l2tp_dst_addr  -RemoteIpv4AddrStep $l2tp_dst_step"
            ::sth::sthCore::invoke stc::config [lindex $createdIpIf 1] "-Address $l2tp_src_addr   -AddrStep $l2tp_src_step -Gateway  $l2tp_dst_addr  -GatewayStep $l2tp_dst_step"
set createdPppoL2tpConfig [::sth::sthCore::invoke stc::create PppoL2tpv2ClientBlockConfig -under $createdHost]
            ::sth::sthCore::invoke stc::config $createdPppoL2tpConfig "$argumentList_pppol2tpv2 -UsesIf-targets [lindex $createdIpIf 0]"
            #Config PppoL2tpv2ClientBlockConfig/Ipv4Network Block
            set createdIpv4NetworkBlock [::sth::sthCore::invoke stc::get $createdPppoL2tpConfig -children-Ipv4NetworkBlock ]
            ::sth::sthCore::invoke stc::config $createdIpv4NetworkBlock "-StartIpList $l2tp_dst_step "
            #Config L2tpv2BlockConfig/Ipv4NetworkBlock
            set createdIpv4NetworkBlock2 [::sth::sthCore::invoke stc::get  $createdL2tpv2BlockConfig -children-Ipv4NetworkBlock ]
            ::sth::sthCore::invoke stc::config $createdIpv4NetworkBlock2 "-StartIpList $l2tp_dst_addr "
        } else {
            set deviceCount $l2tp_dst_count
            ::sth::sthCore::invoke stc::config $createdHost "-DeviceCount $deviceCount"
            ::sth::sthCore::invoke stc::config $createdL2tpIf "-RemoteIpv4Addr  $l2tp_src_addr  -RemoteIpv4AddrStep  $l2tp_src_step"
            ::sth::sthCore::invoke stc::config [lindex $createdIpIf 1] "-Address $l2tp_dst_addr  -AddrStep $l2tp_dst_step  -Gateway $l2tp_src_addr   -GatewayStep  $l2tp_src_step"
            # Config Ipv4 Top If
            ::sth::sthCore::invoke stc::config [lindex $createdIpIf 0] "-Address $ppp_server_ip -AddrStep $ppp_server_step"
            # Config PppoL2tpv2ServerBlockConfig
set createdPppoL2tpConfig [::sth::sthCore::invoke stc::create PppoL2tpv2ServerBlockConfig -under $createdHost ]
            ::sth::sthCore::invoke stc::config $createdPppoL2tpConfig "$argumentList_pppol2tpv2 -UsesIf-targets [lindex $createdIpIf 0]"
            #Config PppoL2tpv2ServerBlockConfig/PppoxServerIpv4PeerPool
            set createdPppoxServerIpv4PeerPool [::sth::sthCore::invoke stc::get  $createdPppoL2tpConfig -children-PppoxServerIpv4PeerPool ]
            regexp {(\d+?).(\d+?).(\d+?).(\d+?)} $ppp_client_step b a1 a2 a3 a4
            set add_increment [expr {$a1*512+$a2*256+$a3*128+$a4} ]
            if {[::sth::sthCore::invoke stc::get system1 -version] >= 3.40} {
                ::sth::sthCore::invoke stc::config $createdPppoxServerIpv4PeerPool "-Ipv4PeerPoolAddr $ppp_client_ip -StartIpList $ppp_client_ip -NetworkCount $l2tp_dst_count  -AddrIncrement $add_increment"
            } else {
                ::sth::sthCore::invoke stc::config $createdPppoxServerIpv4PeerPool "-StartIpList $ppp_client_ip -NetworkCount $l2tp_dst_count  -AddrIncrement $add_increment"
            }
            
        }
        
        if {[regexp -nocase  "atm"  $l2_encap] } {
            if {[regexp -nocase  "atm_vc_mux"  $l2_encap] } {
                set vc_encap "VC_MULTIPLEXED"
            } else {
                set vc_encap "LLC_ENCAPSULATED"
            }
            switch -exact -- $pvc_incr_mode {
                "both" {
                    if { $deviceCount % $vci_count != 0 || $deviceCount % $vpi_count != 0 } {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vci_count and vpi_count when pvc_incr_mode is \"both\""}
                    set  argumentList_aal5if    "-Vci $vci -VciStep $vci_step -VciRecycleCount $vci_count -Vpi $vpi -VpiStep $vpi_step -IfRecycleCount $vpi_count -VcEncapsulation $vc_encap"
                }
                "vci" {
                    if { $deviceCount % ($vci_count * $vpi_count) != 0 } {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vci_count * vpi_count when pvc_incr_mode is \"vci\""}
                    set  argumentList_aal5if "-Vci $vci -VciStep $vci_step -VciRecycleCount $vci_count -Vpi $vpi  -VpiStep $vpi_step  -VpiRepeatCount [expr $vci_count -1] -IfRecycleCount $vpi_count  -VcEncapsulation $vc_encap"
                }
                "vpi" {
                    if { $deviceCount % ($vci_count * $vpi_count) != 0 } {return -code 1 -errorcode -1 "deviceCount ($deviceCount) should be divided evenly by vci_count * vpi_count when pvc_incr_mode is \"vpi\""}
                    set  argumentList_aal5if "-Vci $vci -VciStep $vci_step -VciRepeatCount [expr $vpi_count -1] -VciRecycleCount $vci_count -Vpi $vpi  -VpiStep $vpi_step -IfRecycleCount $vpi_count  -VcEncapsulation $vc_encap"
                }
            }
            set createdAal5If [::sth::sthCore::invoke stc::get  $createdHost "-children-Aal5If"]
            ::sth::sthCore::invoke stc::config $createdAal5If $argumentList_aal5if
        } else {
            set createdVlanIf [::sth::sthCore::invoke stc::get $createdHost "-children-vlanif"]
            set createdEthIIIf [::sth::sthCore::invoke stc::get  $createdHost "-children-EthIIIf"]
            ::sth::sthCore::invoke stc::config $createdEthIIIf "-SourceMac $l2tp_mac_addr  -SrcMacStep $l2tp_mac_step"
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
        }
        
        keylset returnKeyedList handles $createdHost
        keylset returnKeyedList handle $createdHost
    }
   
   
    proc ::sth::l2tp::processConfigCmd_usersetting { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
        set _OrigHltCmdName "l2tp_config"
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        set val $switchValue
        if {[regexp -nocase "chap" $val ]} {
            set val "CHAP_MD5"
        } elseif {[regexp -nocase "pap_or_chap" $val ]} {
            set val "AUTO"
        }
        if {[info exists ::sth::l2tp::[set _OrigHltCmdName]_[set switchName]_fwdmap]} {
            set val [set ::sth::l2tp::[set _OrigHltCmdName]_[set switchName]_fwdmap([set switchValue])]
        }
        if { [regexp -nocase "lns" $userArgsArray(mode)] && ( [regexp -nocase "AutoRetryCount" $switchName ] ||  [regexp -nocase "EnableAutoRetry" $switchName] ) } {
            return $returnKeyedList
        } 
        lappend configList -$switchName $val

        return $returnKeyedList
    }
    
    
    
    
    
    
    proc ::sth::l2tp::processConfigCmd_wildcard { configListName returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray  
        set _OrigHltCmdName "l2tp_config"
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
        # Reconfigure the actual username and/or password for wildcards
        if {[regexp "pppol2tpv2" $configListName]} {
            set attr_list "{username anonymous} {password pass}"
        } else {
            set attr_list "{hostname anonymous} {secret pass}"
        }
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
    
    
    
    

    proc ::sth::l2tp::processConfigCmd_EchoReq { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray 
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        if {$userArgsArray($switchName) < 1} {
            lappend configList -MaxEchoRequestAttempts 0
        } else {
            lappend configList -MaxEchoRequestAttempts 3
        }
        return $returnKeyedList
    }
    

    
    proc ::sth::l2tp::processConfigCmd_secret { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray    
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
        
        lappend configList -EnableDutAuthentication $userArgsArray(tun_auth)  -RxTunnelPassword $userArgsArray(secret) -TxTunnelPassword $userArgsArray(secret)
        return $returnKeyedList
    }
    
    
    
    proc ::sth::l2tp::processConfigCmd_PapChap { configListName switchName switchValue returnKeyedListVarName } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
    
        upvar 1 $configListName configList
        upvar 1 $returnKeyedListVarName returnKeyedList
    
        if {! [info exists userArgsArray(auth_mode)]} {
            # Do nothing
            return $returnKeyedList
        }
    
        set val $switchValue
        switch -- ${userArgsArray(auth_mode)},${switchName} {
            pap,auth_req_timeout {
                if { [info exists userArgsArray(mode)] && [regexp -nocase "lns" $userArgsArray(mode)] } {
                } else { lappend configList -PapRequestTimeout $val }
            }
            chap,auth_req_timeout {
                lappend configList -ChapChalRequestTimeout $val
            }
            pap_or_chap,auth_req_timeout {
                lappend configList -PapRequestTimeout $val -ChapChalRequestTimeout $val
            }
            pap,max_auth_req {
                if { [info exists userArgsArray(mode)] && [regexp -nocase "lns" $userArgsArray(mode)] } {
                } else {lappend configList -MaxPapRequestAttempts $val }
            }
            chap,max_auth_req {
                lappend configList -MaxChapRequestReplyAttempts $val
            }
            pap_or_chap,max_auth_req {
                lappend configList -MaxPapRequestAttempts $val -MaxChapRequestReplyAttempts $val
            }
        }
        return $returnKeyedList
    }
    
    
    
    
    
    proc ::sth::l2tp::processL2TPGetCmd_state { attr returnInfoVarName keyName handle } {
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
                ::sth::sthCore::processError returnKeyedList "::sth::l2tp::processL2TPGetCmd_state Could not resolve state: $stateVal: $err"
                return -code error $returnKeyedList 
            }
        }

         
        keylset returnKeyedList ${keyName}.connecting $connecting
        keylset returnKeyedList ${keyName}.connected $connected
        keylset returnKeyedList ${keyName}.disconnecting $disconnecting
        keylset returnKeyedList ${keyName}.idle $idle
         
        
        return $::sth::sthCore::SUCCESS
    }
    
    
    
    
    
    proc ::sth::l2tp::processL2TPGetCmd { attr returnInfoVarName keyName handle } {
        set procName [lindex [info level [info level]] 0]
        variable userArgsArray
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tp::l2tp_stats_${keyName}_stcattr($attr)]
    
        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]
    
        #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.$attr $val
    
        return $::sth::sthCore::SUCCESS
    }
    
    
    proc ::sth::l2tp::processL2TPTunnelGetCmd { attr returnInfoVarName keyName L2TPTunnelId handle } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tp::l2tp_stats_${keyName}_stcattr($attr)]

        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]

    #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.${L2TPTunnelId}.$attr $val
        

        return $::sth::sthCore::SUCCESS     
    }
    
    
    
    
    
    
    proc ::sth::l2tp::processL2TPSessionGetCmd { attr returnInfoVarName keyName L2TPTunnelId L2TPSessionId handle } {
        set procName [lindex [info level [info level]] 0]
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
    
        upvar 1 $returnInfoVarName returnKeyedList
    
        set getValueVar ""
        set stcAttrName [set ::sth::l2tp::l2tp_stats_${keyName}_stcattr($attr)]

        set val [::sth::sthCore::invoke stc::get $handle -$stcAttrName]

    #@TODO: Add the general encoding function as per requirement
        keylset returnKeyedList ${keyName}.${L2TPTunnelId}.${L2TPSessionId}.$attr $val

        return $::sth::sthCore::SUCCESS     
    }
    
 
    
   
}
