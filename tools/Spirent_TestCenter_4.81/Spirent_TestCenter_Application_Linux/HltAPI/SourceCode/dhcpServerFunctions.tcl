namespace eval ::sth::DhcpServer:: {
   
    ###global variable acksubopt82 stands for paylaod string of DHCP option 82 with a "ACK" message type,
    ###offersubopt82 stands for payload string of DHCP option 82 with a "OFFER" message type.
    set acksubopt82 ""
    set offersubopt82 ""
    set dhcp_server_subscription_state 0
    array set ENCAP ""
    array set DEVICECOUNT ""
   
    ###DHCPSERVEROPTIONSTYPE
    ###This array holds the code of DHCP options in a DHCP OFFER or ACK message,
    ###and the code uniquely idenfies the option.
    
    array set DHCPSERVEROPTIONSTYPE {
        dhcp_ack_time_offset                    2
        dhcp_ack_router_address                 3
        dhcp_ack_router_adddress                3
        dhcp_ack_time_server_address            4
        dhcp_ack_circuit_id                     82
        dhcp_ack_remote_id                      82
        dhcp_ack_link_selection                 82
        dhcp_ack_cisco_server_id_override       82
        dhcp_ack_server_id_override             82
        dhcp_offer_time_offset                  2
        dhcp_offer_router_address               3
        dhcp_offer_time_server_address          4
        dhcp_offer_circuit_id                   82
        dhcp_offer_remote_id                    82
        dhcp_offer_link_selection               82
        dhcp_offer_cisco_server_id_override     82
        dhcp_offer_server_id_override           82
    }
    
    ###DHCPSERVERSUBOPTIONS
    ###This array holds the suboption code of DHCP Option 82(relay agent), in hex
    ###
    
    array set DHCPSERVERSUBOPTIONS {
        dhcp_ack_circuit_id                     01
        dhcp_ack_remote_id                      02
        dhcp_ack_link_selection                 05
        dhcp_ack_cisco_server_id_override       98
        dhcp_ack_server_id_override             B6
        dhcp_offer_circuit_id                   01
        dhcp_offer_remote_id                    02
        dhcp_offer_link_selection               05
        dhcp_offer_cisco_server_id_override     98
        dhcp_offer_server_id_override           B6
    }
}

###
#  Name:    emulation_dhcp_server_config_create { str }
#  Inputs:  returnKeyedListVarName - returnKeyedList name
#  Outputs: 1|0 - pass|fail
#  Description:  This procedure executes the emulation_dhcp_server_config command when the mode is create.
#                It will create a hostblock with hosts based on the -count switch on the specified port.
###
proc ::sth::DhcpServer::emulation_dhcp_server_config_create { returnKeyedListVarName } {
    
    variable ::sth::DhcpServer::userArgsArray
    variable dhcp_server_subscription_state
    upvar 1 $returnKeyedListVarName returnKeyedList
    
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
        
        set modeType "create"
        set hltCmdName "emulation_dhcp_server_config"
        set vlanexist 0
        set count 1
        if {[info exists userArgsArray(count)]} {
            set count $userArgsArray(count)
        }
        if {[info exists userArgsArray(port_handle)]} {
            set vlanOuter 0
            
            #create new host
            set hostHandle [::sth::sthCore::invoke stc::create Host -under $::sth::sthCore::GBLHNDMAP(project)]
            
            set ::sth::DhcpServer::DEVICECOUNT($hostHandle) $count
            
            set baseIf "" 
            #add ATM support, xiaozhi, 6/5/09
            #STC does not support DHCPServer over ATM, but supports DHCPServer oEoA.
            switch -exact -- $userArgsArray(encapsulation) {
                "ETHERNET_II" -
                "ETHERNET_II_VLAN" {
                    #create EthernetII interface
                    set ethiiIf [::sth::sthCore::invoke stc::create EthIIIf -under $hostHandle]
                    configEthIIIntf $ethiiIf $modeType
                    set baseIf $ethiiIf
                }
                "ETHERNET_II_QINQ" {
                    set vlanOuter 1
                    #create EthernetII interface
                    set ethiiIf [::sth::sthCore::invoke stc::create EthIIIf -under $hostHandle]
                    configEthIIIntf $ethiiIf $modeType
                    set baseIf $ethiiIf
                }
                "ATM_LLC_SNAP_ETHERNET_II" {
                    set ethiiIf [::sth::sthCore::invoke stc::create EthIIIf -under $hostHandle]
                    configEthIIIntf $ethiiIf $modeType
                            
                    #create ATM stack
                    set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $hostHandle "-VcEncapsulation LLC_ENCAPSULATED"]
                    configAtmIf $atmResultIf $modeType
                    
                    ::sth::sthCore::invoke stc::config $ethiiIf "-StackedOnEndpoint-targets $atmResultIf"
                    set baseIf $ethiiIf
                }
                "ATM_VC_MUX_ETHERNET_II" {
                    set ethiiIf [::sth::sthCore::invoke stc::create EthIIIf -under $hostHandle]
                    configEthIIIntf $ethiiIf $modeType
                            
                    #create ATM stack
                    set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $hostHandle "-VcEncapsulation VC_MULTIPLEXED"]
                    configAtmIf $atmResultIf $modeType
                    
                    ::sth::sthCore::invoke stc::config $ethiiIf "-StackedOnEndpoint-targets $atmResultIf"
                    set baseIf $ethiiIf
                }
            }
        
            set ::sth::DhcpServer::ENCAP($hostHandle) "ethernet_ii"
                                      
            #create IPv4 interface
            set ipv4If [::sth::sthCore::invoke stc::create Ipv4If -under $hostHandle]
            configIpv4Intf $ipv4If $modeType
                      
            if {[info exists ethiiIf]} {
                #create vlan interface if any vlan related as input, it is optional
                if {[info exists userArgsArray(vlan_id)]} {
                    set vlanexist 1
                    set vlanInnerIf [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle]
                    
                    #add QinQ
                    if {$vlanOuter == 1} {
                        set vlanOuterIf [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle]
                        set ::sth::DhcpServer::ENCAP($hostHandle) "ethernet_ii_qinq"
                        configVlanIfOuter $vlanOuterIf $modeType
                        
                        ::sth::sthCore::invoke stc::config $vlanOuterIf "-StackedOnEndpoint-targets $ethiiIf"
                        ::sth::sthCore::invoke stc::config $vlanInnerIf "-StackedOnEndpoint-targets $vlanOuterIf"
                        set baseIf $vlanInnerIf
                    } else {
                        set ::sth::DhcpServer::ENCAP($hostHandle) "ethernet_ii_vlan"
                        ::sth::sthCore::invoke stc::config $vlanInnerIf "-StackedOnEndpoint-targets $ethiiIf"
                        set baseIf $vlanInnerIf
                    }
                    
                    configVlanIfInner $vlanInnerIf $modeType
                }
    
                if {![info exists userArgsArray(vlan_id)] && $vlanOuter == 1} {
                    ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $hostHandle. Specify -vlan_id to enable VLAN"
                    return $returnKeyedList
                }
            }
        } else {
            set hostHandle $userArgsArray(handle)
            set ::sth::DhcpServer::DEVICECOUNT($hostHandle) $count
            
            if {$userArgsArray(mode) == "enable"} {
                set ipv4If [::sth::sthCore::invoke stc::get $hostHandle -children-ipv4if]
                if {[llength $ipv4If] == 0} {
                    set ipv4ifhandle [::sth::sthCore::invoke stc::create ipv4if -under $hostHandle]
                    set primaryifTargets [::sth::sthCore::invoke stc::get $hostHandle -primaryif-Targets]
                    set toplevelifTargets [::sth::sthCore::invoke stc::get $hostHandle -toplevelif-Targets]
                    lappend primaryifTargets $ipv4ifhandle
                    lappend toplevelifTargets $ipv4ifhandle
                    set lowif [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif]
		    set vlanif [::sth::sthCore::invoke stc::get $hostHandle -children-vlanif]
                    if {$vlanif != ""} {
                       set lowif [lindex $vlanif 0]
                    }
                    ::sth::sthCore::invoke stc::config $ipv4ifhandle "-stackedonendpoint-targets $lowif"
                    ::sth::sthCore::invoke stc::config $hostHandle -primaryif-Targets $primaryifTargets -toplevelif-Targets $toplevelifTargets      
                }
            }   
        }
        # will not set DeviceCount when not specifying -count in enable mode
        if {$userArgsArray(mode) != "enable" || $::sth::DhcpServer::dhcpv4SetCountArg} {
            ::sth::sthCore::invoke stc::config $hostHandle "-DeviceCount $count"
        }
        #create Dhcpv4ServerConfig under host
        set dhcpServerConfigHandle [::sth::sthCore::invoke stc::create Dhcpv4ServerConfig -under $hostHandle ]
        configDhcpServerConfig $dhcpServerConfigHandle $modeType
            
        #get Dhcpv4ServerDefaultPoolConfig
        set dhcpServerPoolConfig [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -children-Dhcpv4ServerDefaultPoolConfig]
        configDhcpServerPoolConfig $dhcpServerPoolConfig $modeType $hltCmdName
            
        #create Dhcpv4ServerMsgOption under Dhcpv4ServerDefaultPoolConfig, it is optional
        if {$dhcpServerPoolConfig != ""} {
            if {[regexp -- {dhcp_ack} $userArgsArray(optional_args)] || [regexp -- {dhcp_offer} $userArgsArray(optional_args)]} {               
                configDhcpServerMsgOption $dhcpServerPoolConfig $modeType $hltCmdName
            }
        }
        
        if {[info exists userArgsArray(port_handle)]} {
            #config relation
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $hostHandle "-AffiliationPort-targets $portHandle"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipv4If "-StackedOnEndpoint-targets $baseIf" ]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $hostHandle "-TopLevelIf-targets $ipv4If"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $hostHandle "-PrimaryIf-targets $ipv4If"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $dhcpServerConfigHandle "-UsesIf-targets $ipv4If"]
                        
            foreach cmd $cmd_list {
                if {[catch {eval $cmd} err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::stc::config Failed: $err" {}
                    return -code error $returnKeyedList 
                }
            }
        }

        if {$dhcp_server_subscription_state == 0} {
            # Create the DHCP server result dataset
            set dhcpServerResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set dhcpServerResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $dhcpServerResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId Dhcpv4ServerConfig -ResultClassId Dhcpv4ServerResults"]
        }
    
        #apply all configurations
        if {[catch {::sth::sthCore::doStcApply} applyError]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $applyError" {}
            return -code error $returnKeyedList 
        }
        
        if {$dhcp_server_subscription_state == 0} {
            # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $dhcpServerResultDataSet
            set dhcp_server_subscription_state 1
        }
        
        #keylset returnKeyedList handle
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.port_handle" $portHandle]
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.dhcp_handle" $hostHandle]

    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
        # delete any host created if error occurs
        ::sth::sthCore::invoke stc::delete $hostHandle
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}
###
#  Name:    emulation_dhcp_server_config_modify 
#  Inputs:  returnKeyedListVarName - returnKeyedList name
#  Outputs: 1|0 - pass|fail
#  Description: This procedure executes the emulation_dhcp_server_config command when the mode is modify.
#               It will modify the exiting host(s) based on the -handle switch.
###

proc ::sth::DhcpServer::emulation_dhcp_server_config_modify { returnKeyedListVarName } {

    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {[info exists userArgsArray(handle)]} {
        set hostHandleList $userArgsArray(handle)
        if {![IsDhcpServerHandleValid $hostHandleList]} {
            ::sth::sthCore::processError returnKeyedList "Error: $hostHandleList is not a valid Dhcp Server handle" {}
            return -code error $returnKeyedList 
        }
    } else {
         ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return -code error $returnKeyedList 
    }

    set modeType "modify"
    set hltCmdName "emulation_dhcp_server_config"
    #unsupported switches in -mode modify
    set unsupportedModifyOptions {port_handle count}
    
    set functionsToRun {}
    foreach item $sortedSwitchPriorityList {
        foreach {priority switchname} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::DhcpServer:: $hltCmdName $switchname supported]} {
                ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                return -code error $returnKeyedList 
            }
            if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
        	::sth::sthCore::processError returnKeyedList "unable to modify the \"-$switchname\" in modify mode" {}
                return -code error $returnKeyedList 
            }
            
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $hltCmdName $switchname mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::DhcpServer:: $hltCmdName $switchname modify]
            if {[lsearch $functionsToRun $func] == -1} {
                lappend functionsToRun $func
            }
        }
    }
    
    foreach hostHandle $hostHandleList {
        foreach func $functionsToRun {
            switch -- $func {
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $hostHandle -children-EthIIIf]
                    if {[llength $ethiiIf] == 0} {
                        ::sth::sthCore::processError returnKeyedList "$hostHandle is not over EthernetII encapsulation." {}
                        return $returnKeyedList
                    }
                    configEthIIIntf $ethiiIf $modeType
                }
                configAtmIf {
                    set atmIf [::sth::sthCore::invoke stc::get $hostHandle -children-aal5if]
                    if {[llength $atmIf] == 0} {
                        ::sth::sthCore::processError returnKeyedList "$hostHandle is not over ATM encapsulation." {}
                        return $returnKeyedList
                    }
                    configAtmIf $atmIf $modeType
                }
                configIpv4Intf {
                    if {[catch {set ipv4If [::sth::sthCore::invoke stc::get $hostHandle -children-Ipv4If]} err]} {
                        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                        return $::sth::sthCore::FAILURE
                    }
                    foreach ipIf $ipv4If {
                        configIpv4Intf $ipIf $modeType
                    }
                }
                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-VlanIf]
                    
                    if {[llength $vlanIf] == 0} {
                        ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $hostHandle."
			return $::sth::sthCore::FAILURE
                    }
                    if {[llength $vlanIf] > 1} {
                        set vlanIf [lindex $vlanIf 0]
                    }
                    configVlanIfInner $vlanIf $modeType
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-VlanIf]
                    if {[llength $vlanIf] == 0} {
                        ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $hostHandle."
			return $::sth::sthCore::FAILURE
                    }
                    if {[llength $vlanIf] < 2} {
                        ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $hostHandle."
			return $::sth::sthCore::FAILURE
                    }
                    
                    set vlanIf [lindex $vlanIf 1]
                    configVlanIfOuter $vlanIf $modeType
                   
                }
                configDhcpServerConfig {
                    set dhcpServerConfigHandle [::sth::sthCore::invoke stc::get $hostHandle -children-Dhcpv4ServerConfig]
                    configDhcpServerConfig $dhcpServerConfigHandle $modeType
                }
                configDhcpServerPoolConfig {
                    set dhcpServerConfigHandle [::sth::sthCore::invoke stc::get $hostHandle -children-Dhcpv4ServerConfig]
                    set dhcpServerPoolConfig [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -children-Dhcpv4ServerDefaultPoolConfig]
                    configDhcpServerPoolConfig $dhcpServerPoolConfig $modeType $hltCmdName
                }
                configDhcpServerMsgOption {
                    set dhcpServerConfigHandle [::sth::sthCore::invoke stc::get $hostHandle -children-Dhcpv4ServerConfig]
                    set dhcpServerPoolConfig [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -children-Dhcpv4ServerDefaultPoolConfig]
                    
                    configDhcpServerMsgOption $dhcpServerPoolConfig $modeType $hltCmdName
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "handle.dhcp_handle" $hostHandle]
    }
    
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $applyError" {}
        return -code error $returnKeyedList 
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
###
#  Name:   emulation_dhcp_server_config_reset
#  Inputs:  returnKeyedListVarName - returnKeyedList name
#  Outputs: 1|0 - pass|fail
#  Description: This procedure execute the emulation_dhcp_server_config command when the mode is resst.
#               It will delete all DHCP server hosts based on the handle switch value.
###
proc ::sth::DhcpServer::emulation_dhcp_server_config_reset { returnKeyedListVarName } {
    
    variable ::sth::DhcpServer::userArgsArray
    variable ::sth::DhcpServer::sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
        return $returnKeyedList
    }
    
    set hostHandleList $userArgsArray(handle)
    
    foreach hostHandle $hostHandleList {
        if {![IsDhcpServerHandleValid $hostHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid DHCP Server host handle" {}
            return -code error $returnKeyedList 
        }
        
        ::sth::sthCore::invoke stc::delete $hostHandle
    }
    
    if {[catch {::sth::sthCore::doStcApply} applyError]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::doStcApply Failed: $applyError" {}
        return -code error $returnKeyedList 
    }
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
    
}



proc ::sth::DhcpServer::emulation_dhcp_server_relay_agent_config_create { returnKeyedListVarName } {
    
    variable ::sth::DhcpServer::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        set dhcpHandle $userArgsArray(handle)
        if {![IsDhcpServerHandleValid $dhcpHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $dhcpHandle is not a valid Dhcp Server handle" {}
            return -code error $returnKeyedList
        }
        
        set hltCmdName "emulation_dhcp_server_relay_agent_config"
        # get Dhcpv4ServerConfig
        set dhcpServerCfgHdl [::sth::sthCore::invoke stc::get $dhcpHandle -children-Dhcpv4ServerConfig]
        
        set dhcpServerPoolList ""
        if {[info exists userArgsArray(relay_agent_ipaddress_pool)]} {
        	set temp_relay_agent_ipaddress_pool $userArgsArray(relay_agent_ipaddress_pool)
        }
        for {set i 0} {$i < $userArgsArray(relay_agent_pool_count)} {incr i} {
            #create Dhcpv4ServerPoolConfig 
            set dhcpServerPoolHdl [::sth::sthCore::invoke stc::create Dhcpv4ServerPoolConfig -under $dhcpServerCfgHdl]

            if {[info exists userArgsArray(relay_agent_ipaddress_pool)]} {
                if {[info exists userArgsArray(relay_agent_pool_step)]} {
                    set userArgsArray(relay_agent_ipaddress_pool) [::sth::sthCore::updateIpAddress 4 $temp_relay_agent_ipaddress_pool \
                                                                   $userArgsArray(relay_agent_pool_step) $i]
                }
            }
            configDhcpServerPoolConfig $dhcpServerPoolHdl create $hltCmdName
            
            #create Dhcpv4ServerMsgOption under Dhcpv4ServerPoolConfig, it is optional
            if {$dhcpServerPoolHdl != ""} {
                if {[regexp -- {dhcp_ack} $userArgsArray(optional_args)] || [regexp -- {dhcp_offer} $userArgsArray(optional_args)]} {               
                    configDhcpServerMsgOption $dhcpServerPoolHdl create $hltCmdName
                }
            }
            
            lappend dhcpServerPoolList $dhcpServerPoolHdl
        }
        
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList pool_handles $dhcpServerPoolList
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}


proc ::sth::DhcpServer::emulation_dhcp_server_relay_agent_config_modify { returnKeyedListVarName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        set dhcpServerPoolHdl $userArgsArray(handle)
        
        foreach dhcpServerPool $dhcpServerPoolHdl { 
            if {![string match -nocase "dhcpv4serverpoolconfig*" $dhcpServerPool]} {
                ::sth::sthCore::processError returnKeyedList "Error: $dhcpServerPool is not a valid Dhcpv4ServerPoolConfig handle" {}
                return -code error $returnKeyedList
            }
        }
        set hltCmdName "emulation_dhcp_server_relay_agent_config"
        set functionsToRun {}
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                if {![::sth::sthCore::getswitchprop ::sth::DhcpServer:: $hltCmdName $switchname supported]} {
                    ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                    return -code error $returnKeyedList 
                }
                
                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $hltCmdName $switchname mode] "_none_"]} { continue }
                set func [::sth::sthCore::getModeFunc ::sth::DhcpServer:: $hltCmdName $switchname modify]
                if {[lsearch $functionsToRun $func] == -1} {
                    lappend functionsToRun $func
                }
            }
        }
        
        foreach dhcpServerPool $dhcpServerPoolHdl {
            foreach func $functionsToRun {
                switch -- $func {
                    configDhcpServerPoolConfig {
                        configDhcpServerPoolConfig $dhcpServerPool "modify" $hltCmdName
                    }
                    configDhcpServerMsgOption {
                        configDhcpServerMsgOption $dhcpServerPool "modify" $hltCmdName
                    }
                    default {
                        ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                        return -code error $returnKeyedList 
                    }
                }
            }
        }
    
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList pool_handles $dhcpServerPoolHdl
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
}


proc ::sth::DhcpServer::emulation_dhcp_server_relay_agent_config_delete { returnKeyedListVarName } {
    
    variable ::sth::DhcpServer::userArgsArray
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        set dhcpServerPoolHdl $userArgsArray(handle)
        
        foreach dhcpServerPool $dhcpServerPoolHdl {
            if {![string match -nocase "Dhcpv4ServerPoolConfig*" $dhcpServerPool]} {
                ::sth::sthCore::processError returnKeyedList "Error: $dhcpServerPool is not a valid Dhcpv4ServerPoolConfig handle" {}
                return -code error $returnKeyedList
            }
            
            ::sth::sthCore::invoke stc::delete $dhcpServerPool
        }
    
    } returnedString]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS 
    }
    
    return $returnKeyedList
    
}

###
#  Name:   emulation_dhcp_server_stats_collect
#  Inputs:  returnKeyedListVarName - returnKeyedList name
#  Outputs(example): {dhcp_server_state UP} {aggregate {{port1 {{tx {{nak 0} {offer 0} {ack 0}}}
#                   {rx {{decline 0} {release 0} {request 0} {inform 0} {discover 0}}}}}}} {status 1}
#  Description: This procedure execute the emulation_dhcp_server_stats command when the action is COLLECT.
#               It will collect the statistics for the specified ports or DHCP handles/servers.
###
proc ::sth::DhcpServer::emulation_dhcp_server_stats_collect { returnKeyedListVarName } {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    if {!([info exists userArgsArray(dhcp_handle)] || [info exists userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: -port_handle or -dhcp_handle."
        return $returnKeyedList
    }
    
    if {[info exists userArgsArray(dhcp_handle)] && [info exists userArgsArray(port_hanlde)]} {
        ::sth::sthCore::processError returnKeyedList "The options -port_handle or -dhcp_handle are mutually exclusive."
        return $returnKeyedList
    }
    
    set hostHandleList ""
    #port_aggr_stat 1 - collect statistics on port_handle, 0 - collect statistics on specified dhcp_handle
    set port_aggr_stat 0
    if {([info exists userArgsArray(dhcp_handle)]) && (![info exists userArgsArray(port_handle)])} {
        if {![IsDhcpServerHandleValid $userArgsArray(dhcp_handle)]} {
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
    
    processStatisticsTxResults $handleList $port_aggr_stat returnKeyedList
    processStatisticsRxResults $handleList $port_aggr_stat returnKeyedList
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList 
}

proc ::sth::DhcpServer::emulation_dhcp_server_stats_clear { returnKeyedListVarName } {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    if {!([info exists userArgsArray(dhcp_handle)] || [info exists userArgsArray(port_handle)])} {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: -port_handle or -dhcp_handle."
        return $returnKeyedList
    }
    
    if {[info exists userArgsArray(dhcp_handle)] && [info exists userArgsArray(port_hanlde)]} {
        ::sth::sthCore::processError returnKeyedList "The options -port_handle or -dhcp_handle are mutually exclusive."
        return $returnKeyedList
    }
    
    set hostHandleList ""
    if {([info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)])
            && (![info exists ::sth::DhcpServer::userArgsArray(port_handle)])} {
        if {![::sth::DhcpServer::IsDhcpServerHandleValid $::sth::DhcpServer::userArgsArray(dhcp_handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: $::sth::DhcpServer::userArgsArray(dhcp_handle) is not a valid DHCP Server handle" {}
            return -code error $returnKeyedList
        }
        set hostHandleList $::sth::DhcpServer::userArgsArray(dhcp_handle)         
                
    } elseif {([info exists ::sth::DhcpServer::userArgsArray(port_handle)])
            && (![info exists ::sth::DhcpServer::userArgsArray(dhcp_handle)])} {
                
        if {[::sth::sthCore::IsPortValid $::sth::DhcpServer::userArgsArray(port_handle) err]} {
            set hostHandleList [::sth::sthCore::invoke stc::get $::sth::DhcpServer::userArgsArray(port_handle) -affiliationport-sources]
        } else {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::DhcpServer::userArgsArray(port_handle)" {}
            return -code error $returnKeyedList
        }
    }
    
    #Clear all stats
    ::sth::sthCore::invoke stc::perform ResultsClearAllProtocol
    
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList 
}
###
#  Name:   processStatisticsTxResults
#  Inputs:  handle - port handle or dhcp server handle
#           statType - 1|0, 1 for port handle, 0 for dhcp server handle
#           returnKeyedListName - returnKeyedList name
#  Description: This procedure retrieves Dhcp Server state and TX statistics
#               for the specified ports or DHCP handles/servers.
#               
###
proc ::sth::DhcpServer::processStatisticsTxResults { handle statType returnKeyedListName } {
    
    variable userArgsArray
    upvar $returnKeyedListName dhcpServerStatsTxKeyedList
    set port_aggr_stat $statType
        
    if {$port_aggr_stat == 1 && [string match "port*" $handle]} {
        set hostHandleList [::sth::sthCore::invoke stc::get $handle -affiliationport-sources]
    } elseif {$port_aggr_stat == 0 && ([string match "host*" $handle] || [string match "router*" $handle] || [string match "emulateddevice*" $handle])} {
        set hostHandleList $handle
    } else {
        ::sth::sthCore::processError returnKeyedList "$handle and $statType are not match" {}
        return -code error $returnKeyedList 
    }
    
    foreach host $hostHandleList {
        if {![IsDhcpServerHandleValid $host]} {
            continue
        }
        set dhcpServerConfigHandle [::sth::sthCore::invoke stc::get $host -children-Dhcpv4ServerConfig]
        set dhcpServerResultsHandle [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -children-Dhcpv4ServerResults]
        
        #Server State
        set dhcpServersState [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -ServerState]
        keylset dhcpServerStatsTxKeyedList dhcp_server_state $dhcpServersState
        
        set tableName ::sth::DhcpServer::dhcp_server_stats_tx_results_stcattr
        set aggregateList [array names $tableName]
        if {![string length $dhcpServerResultsHandle]} {
            foreach hltName $aggregateList {
                set stcName $::sth::DhcpServer::dhcp_server_stats_tx_results_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                if {$port_aggr_stat == 1} {
                    set dhcpServerStatsTxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsTxKeyedList "aggregate.$handle.tx.$hltName" "0"]  
                } else {
                    set dhcpServerStatsTxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsTxKeyedList "dhcp_handle.$host.tx.$hltName" "0"] 
                }     
            }
        } else {
            foreach hltName $aggregateList {
                set stcName $::sth::DhcpServer::dhcp_server_stats_tx_results_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                set stcValue [::sth::sthCore::invoke stc::get $dhcpServerResultsHandle -$stcName]
                if {$port_aggr_stat == 1} {
                    set dhcpServerStatsTxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsTxKeyedList "aggregate.$handle.tx.$hltName" $stcValue]
                } else {
                    set dhcpServerStatsTxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsTxKeyedList "dhcp_handle.$host.tx.$hltName" $stcValue]
                }    
            }
        }
    }  
}
###
#  Name:   processStatisticsRxResults
#  Inputs:  handle - port handle or dhcp server handle
#           statType - 1|0, 1 for port handle, 0 for dhcp server handle
#           returnKeyedListName - returnKeyedList name
#  Description: This procedure retrieves RX statistics for the specified ports or DHCP handles/servers.              
###
proc ::sth::DhcpServer::processStatisticsRxResults { handle statType returnKeyedListName } {
    variable userArgsArray
    upvar $returnKeyedListName dhcpServerStatsRxKeyedList
    set port_aggr_stat $statType
        
    if {$port_aggr_stat == 1 && [string match "port*" $handle]} {
        set hostHandleList [::sth::sthCore::invoke stc::get $handle -affiliationport-sources]
    } elseif {$port_aggr_stat == 0 && ([string match "host*" $handle] || [string match "router*" $handle] || [string match "emulateddevice*" $handle])} {
        set hostHandleList $handle
    } else {
        ::sth::sthCore::processError returnKeyedList "$handle and $statType are not match" {}
        return -code error $returnKeyedList 
    }
    
    foreach host $hostHandleList {
        if {![IsDhcpServerHandleValid $host]} {
            continue
        }
        set dhcpServerConfigHandle [::sth::sthCore::invoke stc::get $host -children-Dhcpv4ServerConfig]
        set dhcpServerResultsHandle [::sth::sthCore::invoke stc::get $dhcpServerConfigHandle -children-Dhcpv4ServerResults]
        
        set tableName ::sth::DhcpServer::dhcp_server_stats_rx_results_stcattr
        set aggregateList [array names $tableName]
        if {![string length $dhcpServerResultsHandle]} {
            foreach hltName $aggregateList {
                set stcName $::sth::DhcpServer::dhcp_server_stats_rx_results_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                if {$port_aggr_stat == 1} {
                    set dhcpServerStatsRxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsRxKeyedList "aggregate.$handle.rx.$hltName" "0"]  
                } else {
                    set dhcpServerStatsRxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsRxKeyedList "aggregate.$host.rx.$hltName" "0"] 
                }     
            }
        } else {
            foreach hltName $aggregateList {
                set stcName $::sth::DhcpServer::dhcp_server_stats_rx_results_stcattr($hltName)
                if {$stcName == "_none_"} { continue }
                set stcValue [::sth::sthCore::invoke stc::get $dhcpServerResultsHandle -$stcName]
                if {$port_aggr_stat == 1} {
                    set dhcpServerStatsRxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsRxKeyedList "aggregate.$handle.rx.$hltName" $stcValue]
                } else {
                    set dhcpServerStatsRxKeyedList [::sth::sthCore::updateReturnInfo $dhcpServerStatsRxKeyedList "aggregate.$host.rx.$hltName" $stcValue]
                }    
            }
        }
    }  
}
###
#  Name:    configEthIIIntf 
#  Inputs:  ethIfHandle - EthIIIf handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description: This procedure configures EthIIIf with mac address
###
proc ::sth::DhcpServer::configEthIIIntf { ethIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configEthIIIntf $mode $ethIfHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ethIfHandle $optionValueList
    }
}

###
#  Name:    configAtmIf 
#  Inputs:  atmHandle - atm handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description: This procedure configures vci or vpi
###
proc ::sth::DhcpServer::configAtmIf { atmHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configAtmIf $mode $atmHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $atmHandle $optionValueList
    }
}

###
#  Name:    configIpv4Intf
#  Inputs:  ipIfHandle - IPv4If handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This prodecure configures IPv4If with ip address and gateway
###
proc ::sth::DhcpServer::configIpv4Intf { ipIfHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configIpv4Intf $mode $ipIfHandle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipIfHandle $optionValueList
    }
}
###
#  Name:    configVlanIfInner 
#  Inputs:  vlanIfHandle - VlanIf handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This procedure configures VlanIf with vlan_id and vlan_ethertype
###
proc ::sth::DhcpServer::configVlanIfInner { vlanIfHandle mode } {
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configVlanIfInner $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}


proc ::sth::DhcpServer::configVlanIfOuter {vlanIfHandle mode} {
    
    set deviceHandle [::sth::sthCore::invoke stc::get $vlanIfHandle -parent]
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configVlanIfOuter $mode $deviceHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $vlanIfHandle $optionValueList
    }
}
###
#  Name:    configDhcpServerConfig 
#  Inputs:  dhcpServerHandle - DhcpServerConfig handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This procedure configures DhcpServerConfig 
###
proc ::sth::DhcpServer::configDhcpServerConfig { dhcpServerHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_config configDhcpServerConfig $mode $dhcpServerHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpServerHandle $optionValueList
    }
}
###
#  Name:    configDhcpServerPoolConfig 
#  Inputs:  dhcpServerPoolHandle - Dhcpv4ServerDefaultPoolConfig handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This procedure configures Dhcpv4ServerDefaultPoolConfig with pool address 
###
proc ::sth::DhcpServer::configDhcpServerPoolConfig { dhcpServerPoolHandle mode cmdName } {
    
    set optionValueList [getStcOptionValueList $cmdName configDhcpServerPoolConfig $mode $dhcpServerPoolHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpServerPoolHandle $optionValueList
    }
}

proc ::sth::DhcpServer::configDhcpServerRelayAgentConfig { dhcpServerPoolHandle mode } {
    
    set optionValueList [getStcOptionValueList emulation_dhcp_server_relay_agent_config configDhcpServerRelayAgentConfig $mode $dhcpServerPoolHandle]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $dhcpServerPoolHandle $optionValueList
    }
}
###
#  Name:    configDhcpServerMsgOption 
#  Inputs:  dhcpServerPoolHandle - Dhcpv4ServerDefaultPoolConfig handle
#           mode - "-mode" switch value
#  Outputs: none
#  Description:  This procedure creates Dhcpv4ServerMsgOption per dhcp option except for option 82 by invoking 
#                procedure processEmulation_dhcp_server_config_dhcpAckOfferOptions through procedure getStcOptionValueList.
#                And it uses global variables "acksubopt82" and "offersubopt82" to aggregate all the option 82 ack and offer
#                payload string separately, and creates Dhcpv4ServerMsgOption if the payload string is not null.
###
proc ::sth::DhcpServer::configDhcpServerMsgOption { dhcpServerPoolHandle mode cmdName} {
    
    variable acksubopt82
    variable offersubopt82
    
    set value [getStcOptionValueList $cmdName configDhcpServerMsgOption $mode $dhcpServerPoolHandle]      
    
    if {[string length $acksubopt82]} {
        set msgtype "ACK"
        
        set dhcpServerMsg [getDhcpServerMsgOptionHandle $dhcpServerPoolHandle 82 $msgtype]
        
        set optionvalue "-OptionType 82 -MsgType $msgtype -EnableWildcards TRUE -Payload {$acksubopt82}"
        ::sth::sthCore::invoke stc::config $dhcpServerMsg $optionvalue
        set acksubopt82 ""
    }  
     
    if {[string length $offersubopt82]} {  
        set msgtype "OFFER"
        
        set dhcpServerMsg [getDhcpServerMsgOptionHandle $dhcpServerPoolHandle 82 $msgtype]
        
        set optionvalue "-OptionType 82 -MsgType $msgtype -EnableWildcards TRUE -Payload {$offersubopt82}"
        ::sth::sthCore::invoke stc::config $dhcpServerMsg $optionvalue
        set offersubopt82 ""
    }     
}

###
#  Name:    processEmulation_dhcp_server_config_ipPrefixstep
#  Inputs:  ipIfHandle - IPv4If handle
#           myswitch - "ip_prefix_step" switch
#           value - "ip_prefix_step" value <integer>
#  Outputs: "-AddrStep a.b.c.d"
#  Description: This procedure processes "-ip_prefix_step", mapping "-ip_prefix_step <integer>" and "-ip_prefix_length <integer>"
#               to relevant "ip_step <IPv4>" if "ip_step" is not specifed. It also can check the validity of "-ip_prefix_step"
#               and "-ip_prefix_length" if "ip_step" is being used. For example, "-ip_step" is "0.0.0.2","-ip_prefix_length" is 32,
#               "-ip_prefix_step" should be 2, otherwise it is a wrong value. Now it supports IPv4 only.
###
proc ::sth::DhcpServer::processEmulation_dhcp_server_config_ipPrefixstep { ipIfHandle myswitch value} {
    
    variable userArgsArray
   
    checkDependency "emulation_dhcp_server_config" $myswitch 1
    
    #If "ip_step" is not being used, convert "ip_prefix_step" and "ip_prefix_length", which are in dependence relation, to relavant "ip_step" in Ipv4 format.
    if {![info exists userArgsArray(ip_step)]} {
        if {[info exists userArgsArray(ip_prefix_step)] && [info exists userArgsArray(ip_prefix_length)]} {
            
            set ipprefixstep $userArgsArray(ip_prefix_step)
            set ipprefixlength $userArgsArray(ip_prefix_length)
            
            binary scan [binary format I* $ipprefixstep] B32 binpfxstep 
            set binpfxstep [string trimleft $binpfxstep 0 ]
            set length [string length $binpfxstep]
            binary scan [binary format I* 0] B32 ipstep
            #replace ip_prefix_length bit by ip_prefix_step in binary format
            set newbinpfxstep [string replace $ipstep [expr {$ipprefixlength-$length}] [expr {$ipprefixlength-1}] $binpfxstep]
            #convert to IPv4 format
            for {set x 0; set y 7} {$y < 32} {} {
                set oct [string range $newbinpfxstep $x $y]
                binary scan [binary format B32 $oct] i ip
                lappend newpfxstep $ip
                set x [expr {$x+8}]
                set y [expr {$y+8}]
            }
            set newipstep [join $newpfxstep .]
            
        } else {
            ::sth::sthCore::processError returnKeyedList "switches -ip_prefix_step and -ip_prefix_length are both required when \"-ip_step\" is not being used" {}
            return -code error $returnKeyedList 
        }
    } else {
        #if "ip_step" is being used, check the validity of "ip_prefix_step" and "ip_prefix_length".  
        if {[info exists userArgsArray(ip_prefix_step)] && [info exists userArgsArray(ip_prefix_length)]} {
            
            set ipprefixstep $userArgsArray(ip_prefix_step)
            set ipprefixlength $userArgsArray(ip_prefix_length)
            ###convert "ip_prefix_step" and "ip_prefix_length" to relevant ip step
            binary scan [binary format I* $ipprefixstep] B32 binpfxstep 
            set binpfxstep [string trimleft $binpfxstep 0 ]
            set length [string length $binpfxstep]
            binary scan [binary format I* 0] B32 ipstep
            #replace ip_prefix_length bit by ip_prefix_step in binary format
            set newbinpfxstep [string replace $ipstep [expr {$ipprefixlength-$length}] [expr {$ipprefixlength-1}] $binpfxstep]
            
            for {set x 0; set y 7} {$y < 32} {} {
                set oct [string range $newbinpfxstep $x $y]
                binary scan [binary format B32 $oct] i ip
                lappend newpfxstep $ip
                set x [expr {$x+8}]
                set y [expr {$y+8}]
            }
            set newipstep [join $newpfxstep .]
            ###end
            
            if {![string match $newipstep $userArgsArray(ip_step)]} {
                ::sth::sthCore::processError returnKeyedList "value of -ip_prefix_step or -ip_prefix_length is incorrect " {}
                return -code error $returnKeyedList 
            }    
        } 
    } 
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $newipstep"
}

###
#  Name:    processEmulation_dhcp_server_config_vlanEthertype
#  Inputs:  vlanIfHandle - VlanIf handle
#           myswitch - "vlan_ethertype" switch
#           value - "vlan_ethertype" value <HEX>
#  Outputs: "-Tpid value<decimal>"
#  Description: This procedure converts "-vlan_ethertype" from HEX to equivalent decimal value.
###

proc ::sth::DhcpServer::processEmulation_dhcp_server_config_vlanEthertype { vlanIfHandle myswitch value } {
    
    variable userArgsArray
    
    set decVlantype ""
    if {$myswitch == "vlan_ethertype"} {
        if {[info exists userArgsArray(vlan_id)]} {
            set vlantype $userArgsArray($myswitch)
            #convert HEX to decimal
            set decVlantype [format "%i" $vlantype]    
        } else {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_id is required when -$myswitch is used." {}
            return -code error $returnKeyedList 
        }
    } elseif {$myswitch == "vlan_outer_ethertype"} {
        if {[info exists userArgsArray(vlan_outer_id)]} {
            set vlantype $userArgsArray($myswitch) 
            set decVlantype [format "%i" $vlantype]    
        } else {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_outer_id is required when -$myswitch is used" {}
            return -code error $returnKeyedList 
        }
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $decVlantype"
}

proc ::sth::DhcpServer::processEmulation_dhcp_server_config_vlanStep { vlanIfHandle myswitch value } {
    
    variable userArgsArray
    
    set switchValue $userArgsArray($myswitch)
    set vlanStep ""
    set configCmd ""
    
    
    if {$myswitch == "vlan_id"} {
        
        # fix CR284626041, change the vlan_id_mode default to "increment"
        if {![info exists userArgsArray(vlan_id_mode)]} { set userArgsArray(vlan_id_mode) "increment" }
        if {![info exists userArgsArray(vlan_id_step)]} { set userArgsArray(vlan_id_step) 1 }
        
        if {$userArgsArray(vlan_id_mode) == "increment"} {
            set vlanStep "$userArgsArray(vlan_id_step)" 
        } elseif {$userArgsArray(vlan_id_mode) == "fixed"} {
            set vlanStep 0 
        }
        set configCmd "-IdStep $vlanStep"
        
    } elseif {$myswitch == "vlan_outer_id"} {
        # fix CR284626041, change the vlan_outer_id_mode default to "increment"
        if {![info exists userArgsArray(vlan_outer_id_mode)]} { set userArgsArray(vlan_outer_id_mode) "increment" }
        if {![info exists userArgsArray(vlan_outer_id_step)]} { set userArgsArray(vlan_outer_id_step) 1 }
        
        if {$userArgsArray(vlan_outer_id_mode) == "increment"} {
            set vlanStep "$userArgsArray(vlan_outer_id_step)" 
        } elseif {$userArgsArray(vlan_outer_id_mode) == "fixed"} {
            set vlanStep 0 
        }
        set configCmd "-IdStep $vlanStep"
        
    } 
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $switchValue $configCmd"
}


proc ::sth::DhcpServer::processEmulation_dhcp_server_config_vlanIdCount { handle myswitch value } {
    variable userArgsArray
    
    set encap $::sth::DhcpServer::ENCAP($handle)
    
    if {![info exist userArgsArray(qinq_incr_mode)]} { set userArgsArray(qinq_incr_mode) "inner" }
    set qinqMode $userArgsArray(qinq_incr_mode)
    
    if {$myswitch == "vlan_id_count"} {
        
        if {[expr $::sth::DhcpServer::DEVICECOUNT($handle)%$userArgsArray(vlan_id_count)] != 0} {
            ::sth::sthCore::processError returnKeyedList "The value of -count must be divisible by -$myswitch" {}
            return -code error $returnKeyedList 
        }
        if {$encap == "ethernet_ii_qinq"} {
            if {$qinqMode == "inner"} {
                set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_id_count)"   
            } elseif {$qinqMode == "outer"} {
                set repeatCount ""
                set repeatCount [expr $userArgsArray(vlan_outer_id_count)-1]
                set idCount "-IdRepeatCount $repeatCount -IfRecycleCount 0"
                
            } elseif {$qinqMode == "both"} {
                set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_id_count)"
            }
            
        } elseif {$encap == "ethernet_ii_vlan"} {
            set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_id_count)"
        }
        
    } elseif {$myswitch == "vlan_outer_id_count"} {
        
        if {[expr $::sth::DhcpServer::DEVICECOUNT($handle)%$userArgsArray(vlan_outer_id_count)] != 0} {
            ::sth::sthCore::processError returnKeyedList "The value of -count must be divisible by -$myswitch" {}
            return -code error $returnKeyedList 
        }
        if {$encap == "ethernet_ii_qinq"} {
            if {$qinqMode == "inner"} {
                set repeatCount ""
				set repeatCount [expr $userArgsArray(vlan_id_count)-1]
                set idCount "-IdRepeatCount $repeatCount -IfRecycleCount 0"
				
            } elseif {$qinqMode == "outer"} {
                set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_outer_id_count)"
            } elseif {$qinqMode == "both"} {
                set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_outer_id_count)"
            }
        } elseif {$encap == "ethernet_ii_vlan"} {
            set idCount "-IdRepeatCount 0 -IfRecycleCount $userArgsArray(vlan_outer_id_count)"
        }
    }

    return "$idCount"
}

proc ::sth::DhcpServer::processEmulation_dhcp_server_config_remoteMac { vlanIfHandle myswitch value } {
    variable userArgsArray
    checkDependency "emulation_dhcp_server_config" $myswitch 1
    
    set switchValue $userArgsArray($myswitch)
    
    set configCmd "-ResolveGatewayMac FALSE"
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
      
    return "-$stcattr $switchValue $configCmd"
}
###
#  Name:    processEmulation_dhcp_server_config_poolAddressCount
#  Inputs:  dhcpServerPoolHandle - Dhcpv4ServerDefaultPoolConfig handle
#           myswitch - "ipaddress_count" switch
#           value - "ipaddress_count" value 
#  Outputs: "-LimitHostAddrCount TRUE -HostAddrCount value<decimal>"
#  Description: This procedure sets stc arrribute "-LimitHostAddrCount" to be TRUE when configuring "-ipaddress_count".
###
proc ::sth::DhcpServer::processEmulation_dhcp_server_config_poolAddressCount { dhcpServerPoolHandle myswitch value } {
    
    variable userArgsArray
    checkDependency "emulation_dhcp_server_config" $myswitch 1 
    
    if {[info exists userArgsArray(ipaddress_count)]} {     
        set poolvar "-LimitHostAddrCount TRUE"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "$poolvar -$stcattr $value"
}

proc ::sth::DhcpServer::process_dhcp_server_relay_agent_poolAddressCount { dhcpServerPoolHandle myswitch value } {
    
    variable userArgsArray
    checkDependency "emulation_dhcp_server_relay_agent_config" $myswitch 1 
    
    if {[info exists userArgsArray(relay_agent_ipaddress_count)]} {     
        set poolvar "-LimitHostAddrCount TRUE"
    }
    
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_relay_agent_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "$poolvar -$stcattr $value"
}
###
#  Name:    processEmulation_dhcp_server_config_poolAddressIncrement
#  Inputs:  dhcpServerPoolHandle - Dhcpv4ServerDefaultPoolConfig handle
#           myswitch - "ipaddress_increment" switch
#           value - "ipaddress_increment" value <integer>
#  Outputs: "-HostAddrStep a.b.c.d"
#  Description: This procedure converts switch "-ipaddress_increment" from integer to IPv4 format.
###
proc ::sth::DhcpServer::processEmulation_dhcp_server_config_poolAddressIncrement { dhcpServerPoolHandle myswitch value } {
    
    variable userArgsArray
    checkDependency "emulation_dhcp_server_config" $myswitch 1 
    
    set newpoolstep ""
    #convert integer to IPv4
    binary scan [binary format I* $value] B32 poolstep
    for {set x 0; set y 7} {$y < 32} {} {
        set oct [string range $poolstep $x $y]
        binary scan [binary format B32 $oct] i ip
        lappend newpoolstep $ip
        set x [expr {$x+8}]
        set y [expr {$y+8}]
    }
    set newstep [join $newpoolstep .]
        
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: emulation_dhcp_server_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $newstep"
    
}

proc ::sth::DhcpServer::processEmulation_dhcp_server_config_atmSettings { atmHandle myswitch value } {
    variable userArgsArray
    
    if {![info exists userArgsArray(pvc_incr_mode)]} { set userArgsArray(pvc_incr_mode) "vci" }
    if {![info exists userArgsArray(vci)]} { set userArgsArray(vci) 100 }
    if {![info exists userArgsArray(vpi)]} { set userArgsArray(vpi) 100 }
    if {![info exist userArgsArray(vci_step)]} { set userArgsArray(vci_step) 1 }
    if {![info exists userArgsArray(vci_count)]} { set userArgsArray(vci_count) 1 }   
    if {![info exist userArgsArray(vpi_step)]} { set userArgsArray(vpi_step) 1 }
    if {![info exists userArgsArray(vpi_count)]} { set userArgsArray(vpi_count) 1 }
    
    
    set handle [::sth::sthCore::invoke stc::get $atmHandle -parent]
    
    #validate vci_count and vpi_count
    if {[expr $::sth::DhcpServer::DEVICECOUNT($handle) % $userArgsArray(vci_count) != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $userArgsArray(vci_count) is not valid for switch vci_count: It does not divide -count $::sth::DhcpServer::DEVICECOUNT($handle)."
        return -code error $returnKeyedList
    }
    
    if {[expr $::sth::DhcpServer::DEVICECOUNT($handle) % $userArgsArray(vpi_count) != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $userArgsArray(vpi_count) is not valid for switch vpi_count: It does not divide -count $::sth::DhcpServer::DEVICECOUNT($handle)."
        return -code error $returnKeyedList
    }
    
    set atmConfig ""
    switch -- $userArgsArray(pvc_incr_mode) {
        "vci" {
            if {$myswitch == "vci"} {
                set atmConfig "-Vci $value -VciStep $userArgsArray(vci_step) -VciRecycleCount $userArgsArray(vci_count)"   
            } elseif {$myswitch == "vpi"} {
                if {[expr $userArgsArray(vci_count)-1] >= 0} {
                    set vpiRepeat [expr $userArgsArray(vci_count)-1]
                } else {
                    set vpiRepeat 0
                }
                set atmConfig "-Vpi $value -VpiStep $userArgsArray(vpi_step) -VpiRepeatCount $vpiRepeat \
                                -IfRecycleCount $userArgsArray(vpi_count)"
            }
        }
        "vpi" {
            if {$myswitch == "vci"} {
                if {[expr $userArgsArray(vpi_count)-1] >= 0} {
                    set vciRepeat [expr $userArgsArray(vpi_count)-1]
                } else {
                    set vciRepeat 0
                }
                set atmConfig "-Vci $value -VciStep $userArgsArray(vci_step) -VciRepeatCount $vciRepeat \
                                -VciRecycleCount $userArgsArray(vci_count)"   
            } elseif {$myswitch == "vpi"} {
                set atmConfig "-Vpi $value -VpiStep $userArgsArray(vpi_step) -IfRecycleCount $userArgsArray(vpi_count)"
            }
        }
        "both" {
            if {$myswitch == "vci"} {
                set atmConfig "-Vci $value -VciStep $userArgsArray(vci_step) -VciRecycleCount $userArgsArray(vci_count)"                 
            } elseif {$myswitch == "vpi"} {
                set atmConfig "-Vpi $value -VpiStep $userArgsArray(vpi_step) -IfRecycleCount $userArgsArray(vpi_count)"              
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Error: Unknown pvc_incr_mode $userArgsArray(pvc_incr_mode)." {}
            return -code error $returnKeyedList
        }
    }
    
    return "$atmConfig"
}
###
#  Name:    processEmulation_dhcp_server_config_dhcpAckOfferOptions
#  Inputs:  dhcpServerPoolHandle - Dhcpv4ServerDefaultPoolConfig handle
#           myswitch - dhcp ack or offer options related switch
#           value - 
#  Outputs: 
#  Description: This procedure processes Dhcp options, and message type can be "ACK" or "OFFER", each dhcp option will 
#               create a Dhcpv4ServerMsgOption under input Dhcpv4ServerDefaultPoolConfig handle except for option 82.
#               It will be invoked by procedure "configDhcpServerMsgOption", which will processes option 82.
###
proc ::sth::DhcpServer::processEmulation_dhcp_server_config_dhcpAckOfferOptions { dhcpServerPoolHandle myswitch value } {
    
    variable userArgsArray
    checkDependency "emulation_dhcp_server_config" $myswitch 1
    
    set optionType ""
    if {[info exists ::sth::DhcpServer::DHCPSERVEROPTIONSTYPE($myswitch)]} {
        set optionType $::sth::DhcpServer::DHCPSERVEROPTIONSTYPE($myswitch)
    }
    #dhcp ack or offer options can be configured only when dhcp_ack_options or dhcp_offer_options is 1
    if {[string match -nocase "dhcp_ack*" $myswitch]} {
        set msgType "ACK"
        if {[info exists userArgsArray(dhcp_ack_options)] && $userArgsArray(dhcp_ack_options) == 1} {
            #invoke procedure "processOptions" to format the paylaod string of dhcp options correctly
            set optionvalue [processOptions $msgType $myswitch $value]
        
        } elseif {[info exists userArgsArray(dhcp_ack_options)] && $userArgsArray(dhcp_ack_options) == 0} {
            ::sth::sthCore::processError returnKeyedList "switch -dhcp_ack_options is required to be \"1\" when configuring dhcp ack options" {}
            return -code error $returnKeyedList 
        } else {
            ::sth::sthCore::processError returnKeyedList "switch -dhcp_ack_options is required when configuring dhcp ack options" {}
            return -code error $returnKeyedList 
        }  
        
    } elseif {[string match -nocase "dhcp_offer*" $myswitch]} {
        set msgType "OFFER"
        if {[info exists userArgsArray(dhcp_offer_options)] && $userArgsArray(dhcp_offer_options) == 1} {
            #invoke processOptions to format the paylaod string of dhcp options correctly
            set optionvalue [processOptions $msgType $myswitch $value]
        
        } elseif {[info exists userArgsArray(dhcp_offer_options)] && $userArgsArray(dhcp_offer_options) == 0} {
            ::sth::sthCore::processError returnKeyedList "switch -dhcp_offer_options is required to be \"1\" when configuring dhcp offer options" {}
            return -code error $returnKeyedList 
        } else {
            ::sth::sthCore::processError returnKeyedList "switch -dhcp_offer_options is required when configuring dhcp offer options" {}
            return -code error $returnKeyedList 
        }  
    } 
    
    #create Dhcpv4ServerMsgOption except for option 82
    if {[string length $optionType] && $optionType != "82"} {
        
        set dhcpServerMsg [getDhcpServerMsgOptionHandle $dhcpServerPoolHandle $optionType $msgType]
        
        if {[llength $optionvalue]} {
            ::sth::sthCore::invoke stc::config $dhcpServerMsg $optionvalue
        }
        set returnval $dhcpServerMsg
    } else {
        #option 82 returns null
        set returnval ""
    }
    
    return $returnval
}
###
#  Name:    processOptions
#  Inputs:  msgtype - dhcp message type: ACK or OFFER
#           myswitch - dhcp ack or offer options related switch
#           value - 
#  Outputs (example): -OptionType 2 -MsgType ACK -EnableWildcards TRUE -Payload  {@$(00001200, 0, 1, 1, 0)}
#  Description: This procedure formats payload string of DHCP options according RFC2132 correctly.And now it supports
#               DHCP ACK and OFFER message only.
###
proc ::sth::DhcpServer::processOptions { msgtype myswitch value } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    variable acksubopt82
    variable offersubopt82
    
    set msgType [string toupper $msgtype]
    if {[info exists ::sth::DhcpServer::DHCPSERVEROPTIONSTYPE($myswitch)]} {
        set optionType $::sth::DhcpServer::DHCPSERVEROPTIONSTYPE($myswitch)
    }
    set payload ""
    
    switch -regexp -- $myswitch {
        #subnet_mask {
        #    #Option code is 1 and its length is fixed, 4 octest in a DHCP message.
        #    #Ipv4 subnet mask should be converted to HEX first
        #    set hexvalue [ipv4addrtoHex $value]
        #    set payload "@\$($hexvalue, 0, 1, 1, 0)"
        #    set optionvalue "-OptionType $optionType -MsgType $msgType -EnableWildcards TRUE -Payload {$payload}"
        #}
        time_offset {
            #Option code is 2 and its length is fixed, 4 octets in a DHCP message
            #convert integer to 8 HEX
            binary scan [binary format I* $value] H8 hex
            set payload "@\$($hex, 0, 1, 1, 0)"
            set optionvalue "-OptionType $optionType -MsgType $msgType -EnableWildcards TRUE -Payload {$payload}"
        }
        router_address -
        router_adddress {
            #Option is 3 and the minium length is 4 octets, the length is variable and must always be a multiple of 4.
            #IPv4 router address(es) should be converted to HEX first
            foreach rtr $value {
                set hexvalue [ipv4addrtoHex $rtr]
                set payload "@\$($hexvalue, 0, 1, 1, 0)$payload"
            }
            set optionvalue "-OptionType $optionType -MsgType $msgType -EnableWildcards TRUE -Payload {$payload}"
        }
        time_server_address {
            #Option is 4, the minium length is 4 octets, the length is variable and must alway be a multiple of 4
            #IPv4 time server address(es) should be converted to HEX first
            foreach rtr $value {
                set hexvalue [ipv4addrtoHex $rtr]
                set payload "@\$($hexvalue, 0, 1, 1, 0)$payload"
            }
            set optionvalue "-OptionType $optionType -MsgType $msgType -EnableWildcards TRUE -Payload {$payload}"
        }
        circuit_id -
        remote_id {
            #suboptions of Option 82(relay agent), requires suboption number as first byte;
            #Hex format
            if {[info exists ::sth::DhcpServer::DHCPSERVERSUBOPTIONS($myswitch)]} {
                set subopt $::sth::DhcpServer::DHCPSERVERSUBOPTIONS($myswitch)
            }
            set val [join "$subopt 04" ""]
            set suboption "@\$($val, 0, 1, 1, 0)"
            if {$msgType == "ACK"} {
                set acksubopt82 "$suboption@\$($value, 0, 1, 1, 0)$acksubopt82"  
            } elseif {$msgType == "OFFER"} {
                set offersubopt82 "$suboption@\$($value, 0, 1, 1, 0)$offersubopt82"  
            }    
            set optionvalue ""
        }
        link_selection -
        cisco_server_id_override -
        server_id_override {
            #suboptions of Option 82(relay agent)
            #IPv4 address should converted to HEX
            if {[info exists ::sth::DhcpServer::DHCPSERVERSUBOPTIONS($myswitch)]} {
                set subopt $::sth::DhcpServer::DHCPSERVERSUBOPTIONS($myswitch)
            }
            set val [join "$subopt 04" ""]
            set suboption "@\$($val, 0, 1, 1, 0)"
            set hexvalue [ipv4addrtoHex $value]
            if {$msgType == "ACK"} {
                set acksubopt82 "$suboption@\$($hexvalue, 0, 1, 1, 0)$acksubopt82"  
            } elseif {$msgType == "OFFER"} {
                set offersubopt82 "$suboption@\$($hexvalue, 0, 1, 1, 0)$offersubopt82"  
            }  
            set optionvalue ""
        }
        default {
            set optionvalue ""
        }
    }
    return $optionvalue
}

proc ::sth::DhcpServer::getDhcpServerMsgOptionHandle { dhcpServerPoolHandle optionType msgType } {
    
    set curDhcpServerMsgHandle ""
    
    set dhcpServerMsg [::sth::sthCore::invoke stc::get $dhcpServerPoolHandle -children-Dhcpv4ServerMsgOption]
    if {[string length $dhcpServerMsg]} {
        foreach msg $dhcpServerMsg {
            set opt [::sth::sthCore::invoke stc::get $msg -OptionType]
            set msgtype [::sth::sthCore::invoke stc::get $msg -MsgType]
            if {[string match $opt $optionType] && [string match $msgtype $msgType]} {
                set curDhcpServerMsgHandle $msg
            }
        }
        if {![string length $curDhcpServerMsgHandle]} {
            set curDhcpServerMsgHandle [::sth::sthCore::invoke stc::create Dhcpv4ServerMsgOption -under $dhcpServerPoolHandle]
        }
    } else {
        set curDhcpServerMsgHandle [::sth::sthCore::invoke stc::create Dhcpv4ServerMsgOption -under $dhcpServerPoolHandle]
    }
    
    return $curDhcpServerMsgHandle
}

proc ::sth::DhcpServer::ipv4addrtoHex {ipaddr} {
    
    set octets [split $ipaddr .]
    if {[llength $octets] != 4} {
	set octets [lrange [concat 0 0 0 $octets] 0 3]
    }
    set hexIpaddr ""
    foreach oct $octets {
	binary scan [binary format c $oct] B* bin
        set hex [::sth::sthCore::binToHex $bin]
	set hexIpaddr "$hexIpaddr$hex"
    }
    return $hexIpaddr
}
###
#  Name:    IsDhcpServerHandleValid
#  Inputs:  handle - host handle or host handle list
#  Outputs: 0|1 - pass|fail
#  Description: This procedure checks if the host handle or handle list is valid DHCP server Handle.
###
proc ::sth::DhcpServer::IsDhcpServerHandleValid { handle } {
    
    set cmdStatus 1
    if {[catch {set hostHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-EmulatedDevice]} err]} {
        ::sth::sthCore::processError returnKeyedList "No host exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return -code error $returnKeyedList 
    } else {
	foreach hostHandle $hostHandleList {
	    if {[string equal $hostHandle $handle]} {
                set cmdStatus 1
		break
	    }
	}
	if {[catch {set dhcpServerHandle [::sth::sthCore::invoke stc::get $handle -children-Dhcpv4ServerConfig]} err]} {
	    set cmdStatus 0
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

proc ::sth::DhcpServer::checkDependency {cmdType myswitch dependentValue} {
    
    variable userArgsArray
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $myswitch dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the existence of \"-$dependency\"."
        } elseif {![string match -nocase $dependentValue $userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::DhcpServer::checkDependencyParams {cmdType switchName} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set validFlag 0
    # check the dependency, and unset the argument if the dependecny value is not the expected value
    if {![string match -nocase [set dependPair [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $switchName dependency]] "_none_"]} {
        ###array set dependArray $dependPair
        ## use "array set" will override the argument with the same name
        foreach opt $dependPair {
            set dependSwitch [lindex $opt 0]
            set dependValue [lindex $opt 1]
            
            if {[info exists userArgsArray($dependSwitch)] && [string match -nocase $dependValue $userArgsArray($dependSwitch)]} {
                set validFlag 1
                break
            }    
        }
        
        if {$validFlag == 0} { 
            if {[info exists userArgsArray($switchName)]} {
                ::sth::sthCore::processError returnKeyedList "\"-$switchName\" is supported if \"$dependPair\"."
                unset userArgsArray($switchName)
            }
        }
    }
}

proc ::sth::DhcpServer::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    
    variable sortedSwitchPriorityList
    variable userArgsArray
    
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in dhcpServerTable.tcl
    foreach item $sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::DhcpServer:: $cmdType $opt $mode]
            
            #check dependency
            if {![regexp -- {dhcp_ack|dhcp_offer} $opt]} {
                ::sth::DhcpServer::checkDependencyParams $cmdType $opt
                if {![info exists ::sth::DhcpServer::userArgsArray($opt)]} { continue }
            }

            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::DhcpServer:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::DhcpServer:: $cmdType $opt $userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $userArgsArray($opt)]
                }
            }
        }
    }
    return $optionValueList
}
