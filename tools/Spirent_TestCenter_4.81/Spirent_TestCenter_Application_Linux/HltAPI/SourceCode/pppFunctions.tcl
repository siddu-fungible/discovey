namespace eval ::sth::ppp {
    variable ppp_subscription_state 0
}

proc ::sth::ppp::ppp_config_config { returnKeyedListVarName } {
    
    upvar $returnKeyedListVarName returnKeyedList
    variable userArgsArray
    variable ppp_subscription_state
    
    if {![info exists userArgsArray(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
        return -code error $returnKeyedList
    }
    
    if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
        return -code error $returnKeyedList
    }
    
    set retVal [catch {
        
        set mode "create"
        
        # set default values for non-user defined switches
	foreach key [array names ::sth::ppp::ppp_config_default] {
	    if {![info exists ::sth::ppp::userArgsArray($key)]} {
	        set defaultValue [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $key default]
	        if {![string match -nocase $defaultValue "_none_"]} {
	            set ::sth::ppp::userArgsArray($key) $defaultValue
	        }
	    }
	}
        
        if {$userArgsArray(ipv6_cp) == 0} {
            if {![info exists userArgsArray(local_addr)]} {
                set userArgsArray(local_addr) "0.0.0.0"
                set priority [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config local_addr priority]
                keylset ::sth::ppp::sortedSwitchPriorityList $priority local_addr
            }
            if {![info exists userArgsArray(peer_addr)]} {
                set userArgsArray(peer_addr) "0.0.0.0"
                set priority [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config peer_addr priority]
                keylset ::sth::ppp::sortedSwitchPriorityList $priority peer_addr
            }   
        } else {
            if {![info exists userArgsArray(local_intf_id)]} {
                set userArgsArray(local_intf_id) "0:0:0:0"
                set priority [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config local_intf_id priority]
                keylset ::sth::ppp::sortedSwitchPriorityList $priority local_intf_id
            }
            if {![info exists userArgsArray(peer_intf_id)]} {
                set userArgsArray(peer_intf_id) "0:0:0:0"
                set priority [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config peer_intf_id priority]
                keylset ::sth::ppp::sortedSwitchPriorityList $priority peer_intf_id
            }
        }
        
        # get the automatically-created host 
        set host [lindex [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-host] 0]
        
        # get ip stack, and create new one if not exist
            #Tcl: command substitution using []; "" can run substitution, while {} can't run, both mark a arry to be a argument of a command.
        set ipv6cp 0
        # enable ipv4cp by default
        if {([info exist userArgsArray(ipv6_cp)] && ($userArgsArray(ipv6_cp) == 0)) || (![info exist userArgsArray(ipv6_cp)])} {
            set ipv4If [::sth::sthCore::invoke stc::get $host -children-ipv4if]
            if {[string length $ipv4If] == 0} {
                set ipv4If [::sth::sthCore::invoke stc::create "Ipv4If" -under $host]
            }
                      
            configHostEncap $ipv4If $mode
        } elseif {$userArgsArray(ipv6_cp) == 1} {
            # create Ipv6If (Ipv6If count should be 2)
            set ipv6cp 1
            set ipv6 [::sth::sthCore::invoke stc::get $host -children-ipv6if]
            set ipv6If1 [lindex $ipv6 0]
            set ipv6If2 [lindex $ipv6 1]
            
            if {[string length $ipv6If1] == 0} {
                set ipv6If1 [::sth::sthCore::invoke stc::create "Ipv6If" -under $host]
            }
            
            # configure ipv6 link_local address on the second ipv6if, only local link address begin with "fe80::" can be set.
            if {[string length $ipv6If2] == 0} {
                set ipv6If2 [::sth::sthCore::invoke stc::create "Ipv6If" -under $host]
            }
            configHostEncap $ipv6If2 $mode 
        }
        
        # get POSPhy and create new if not exist
        set posphy [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-POSPhy]
        if {[string length $posphy] == 0} {
            set posphy [::sth::sthCore::invoke stc::create "POSPhy" -under $userArgsArray(port_handle)]   
        }
       
        # get SonetConfig, and create new if not exist
        set sonetCfg [::sth::sthCore::invoke stc::get $posphy -children-SonetConfig]
        if {[string length $sonetCfg] == 0} {
            set sonetCfg [::sth::sthCore::invoke stc::create "SonetConfig" -under $posphy]
        }
        
        configSonetConfig $sonetCfg $mode
        
        # get pppIf and create new if not exist
        set ppp [::sth::sthCore::invoke stc::get $host -children-PppIf]
        if {$ipv6cp == 0} {
            set pppIf1 [lindex $ppp 0]
            if {[string length $pppIf1] == 0} {
                set pppIf1 [::sth::sthCore::invoke stc::create "PppIf" -under $host "-ProtocolId PPP_PROTOCOL_ID_IPV4"]
            }
        } else {
            set pppIf2 [lindex $ppp 1]
            if {[string length $pppIf2] == 0} {
                set pppIf2 [::sth::sthCore::invoke stc::create "PppIf" -under $host "-ProtocolId PPP_PROTOCOL_ID_IPV6"]
            }
        }
        
        # get PppProtocolConfig
        set pppCfg [::sth::sthCore::invoke stc::get $userArgsArray(port_handle) -children-PppProtocolConfig]
        
        configPPPProtocolConfig $pppCfg $mode
        
        #setup relations for PPP Protocl
        lappend cmd_list [list ::sth::sthCore::invoke stc::config $userArgsArray(port_handle) "-ActivePhy-targets $posphy"]
        if {$ipv6cp == 0} {
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $host "-TopLevelIf-targets $ipv4If"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $host "-PrimaryIf-targets $ipv4If"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipv4If "-StackedOnEndpoint-targets $pppIf1"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $pppCfg "-UsesIf-targets $ipv4If"]
        } else {
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $host "-TopLevelIf-targets \"$ipv6If1 $ipv6If2\""]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $host "-PrimaryIf-targets \"$ipv6If1 $ipv6If2\""]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipv6If1 "-StackedOnEndpoint-targets $pppIf2"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipv6If2 "-StackedOnEndpoint-targets $pppIf2"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $pppCfg "-UsesIf-targets $ipv6If2"]
        }
        
     
        foreach cmd $cmd_list {
            if {[catch {eval $cmd} err]} {
                ::sth::sthCore::processError returnKeyedList "$cmd Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        
        if {$ppp_subscription_state == 0} {
             # Create the PPP result dataset
            set pppResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set pppResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $pppResultDataSet "-ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId PppProtocolConfig -ResultClassId PppProtocolResults"]
        }
        
        #apply all configurations
        if {!$::sth::sthCore::optimization} {
            ::sth::sthCore::doStcApply
        }
        
        if {$ppp_subscription_state == 0} {
        # Subscribe to the datasets
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $pppResultDataSet
            set ppp_subscription_state 1
        }
        
        keylset returnKeyedList handles $host
        
    } returnedString ]
    
    return -code $retVal $returnedString
}

proc ::sth::ppp::ppp_config_modify { returnKeyedListVarName } {
    
    upvar $returnKeyedListVarName returnKeyedList
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return -code error $returnKeyedList 
    }
    
	set retVal [catch {
        set unsupportedModifyOptions {port_handle}
        set mode "modify"
        set hostHandle $userArgsArray(handle)
        set host ""
                    
        #check if the handle is a valid PPP handle or not
        if {![IsPPPHandleValid $hostHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid PPP host handle." {}
            return -code error $returnKeyedList 
        }
        # get the automatically-created host and ipcp type
        set ipcp [getIPCPType $hostHandle host]
        
        set ip ""
        if {([info exists userArgsArray(ipv6_cp)] && $userArgsArray(ipv6_cp) == 0)
            || [info exists userArgsArray(local_addr)] || [info exists userArgsArray(peer_addr)]} {
            set ip "IPV4"
        } elseif {([info exists userArgsArray(ipv6_cp)] && $userArgsArray(ipv6_cp) == 1)
            || [info exists userArgsArray(local_intf_id)] || [info exists userArgsArray(peer_intf_id)]} {
            set ip "IPV6"
        }
        
        if {![string match -nocase $ip $ipcp]} {
            ::sth::sthCore::processError returnKeyedList "Error: The IP version of $hostHandle is $ipcp." {}
            return -code error $returnKeyedList  
        }
            
        set functionsToRun {}
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                # make sure the option is supported
                if {![::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $switchname supported]} {
                    ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                    return -code error $returnKeyedList 
                }
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
					::sth::sthCore::processError returnKeyedList "unable to modify the \"-$switchname\" in modify mode" {}
					return -code error $returnKeyedList 
				}
            
                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $switchname mode] "_none_"]} {
					continue 
				}
                set func [::sth::sthCore::getModeFunc ::sth::ppp:: ppp_config $switchname modify]
                if {[lsearch $functionsToRun $func] == -1} {
                    lappend functionsToRun $func
                }
            }
        }
        
        foreach func $functionsToRun {
            switch -- $func {
                configHostEncap {
                    if {[string match -nocase "IPV4" $ipcp ]} {
                        set ipIf [::sth::sthCore::invoke stc::get $hostHandle -children-ipv4if]
                    } elseif {[string match -nocase "IPV6" $ipcp]} {
                        set ipv6 [::sth::sthCore::invoke stc::get $hostHandle -children-ipv6if]
                        set ipIf [lindex $ipv6 1]
                    }
                    configHostEncap $ipIf $mode
                }
                configSonetConfig {
                    # get Port handle
                    set port [::sth::sthCore::invoke stc::get $hostHandle -parent]
                    # get POSPhy
                    set posphy [::sth::sthCore::invoke stc::get $port -children-POSPhy]
                     # get SonetConfig
                    set sonetCfg [::sth::sthCore::invoke stc::get $posphy -children-SonetConfig]
                    
                    configSonetConfig $sonetCfg $mode
                }
                configPPPProtocolConfig {
                    # get port handle
                    set port [::sth::sthCore::invoke stc::get $hostHandle -parent]
                    
                    # get PPPProtocolConfig
                    set pppCfg [::sth::sthCore::invoke stc::get $port -children-PppProtocolConfig]
                    configPPPProtocolConfig $pppCfg $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        #apply all configurations
        if {!$::sth::sthCore::optimization} {
            ::sth::sthCore::doStcApply
        }
        
        keylset returnKeyedList handles $userArgsArray(handle) 
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::ppp::ppp_config_up { returnKeyedListVarName } {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set retVal [catch {
        
        if {(![info exists ::sth::ppp::userArgsArray(port_handle)])
            && (![info exists ::sth::ppp::userArgsArray(handle)])} {
                ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
                return -code error $returnKeyedList
        } 
        
        if {([info exists ::sth::ppp::userArgsArray(port_handle)])
            && ([info exists ::sth::ppp::userArgsArray(handle)])} {
                ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle or -handle are mutually exclusive." {}
                return -code error $returnKeyedList
        }
   
        if {([info exists ::sth::ppp::userArgsArray(handle)])
            && (![info exists ::sth::ppp::userArgsArray(port_handle)])} {
            
            if {![::sth::ppp::IsPPPHandleValid $::sth::ppp::userArgsArray(handle)]} {
                ::sth::sthCore::processError returnKeyedList "Error: $::sth::ppp::userArgsArray(handle) is not a valid PPP host handle" {}
                return -code error $returnKeyedList
            }
            set port [::sth::sthCore::invoke stc::get $::sth::ppp::userArgsArray(handle) -parent]

        } elseif {([info exists ::sth::ppp::userArgsArray(port_handle)])
                && (![info exists ::sth::ppp::userArgsArray(handle)])} {
            if {![::sth::sthCore::IsPortValid $::sth::ppp::userArgsArray(port_handle) err]} {
                ::sth::sthCore::processError returnKeyedList "Error: $::sth::ppp::userArgsArray(port_handle) is not a valid port handle" {}
                return -code error $returnKeyedList
            }
            set port $sth::ppp::userArgsArray(port_handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::ppp::userArgsArray(port_handle)" {}
            return -code error $returnKeyedList
        }
        
    
        # get PPPProtocolConfig
        set pppCfg [::sth::sthCore::invoke stc::get $port -children-PppProtocolConfig]
    
        ::sth::sthCore::invoke stc::perform PppConnect -BlockList $pppCfg -ControlType Connect
    
    } returnedString ]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
	return -code error $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
    
}

proc ::sth::ppp::ppp_config_down { returnKeyedListVarName } {
    
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    set retVal [catch {
        
    if {(![info exists ::sth::ppp::userArgsArray(port_handle)])
        && (![info exists ::sth::ppp::userArgsArray(handle)])} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing mandatory attribute, either -port_handle or -handle." {}
            return -code error $returnKeyedList
    } 
        
    if {([info exists ::sth::ppp::userArgsArray(port_handle)])
        && ([info exists ::sth::ppp::userArgsArray(handle)])} {
            ::sth::sthCore::processError returnKeyedList "Error: The options -port_handle or -handle are mutually exclusive." {}
            return -code error $returnKeyedList
    }
    
    set handleList ""
    if {([info exists ::sth::ppp::userArgsArray(handle)])
        && (![info exists ::sth::ppp::userArgsArray(port_handle)])} {
            
        if {![::sth::ppp::IsPPPHandleValid $::sth::ppp::userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: $::sth::ppp::userArgsArray(handle) is not a valid PPP host handle" {}
            return -code error $returnKeyedList
        }
        
        set handleList $::sth::ppp::userArgsArray(handle) 
    } elseif {([info exists ::sth::ppp::userArgsArray(port_handle)])
            && (![info exists ::sth::ppp::userArgsArray(handle)])} {
            
        if {[::sth::sthCore::IsPortValid $::sth::ppp::userArgsArray(port_handle) err]} {
            set handleList [::sth::sthCore::invoke stc::get $::sth::ppp::userArgsArray(port_handle) -affiliationport-sources]
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $::sth::ppp::userArgsArray(port_handle)" {}
        return -code error $returnKeyedList
    }
    
    ::sth::sthCore::invoke stc::perform PppDisconnect -BlockList $handleList -ControlType Disconnect
    
    } returnedString ]
    
    if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString {}
	return -code error $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

proc ::sth::ppp::ppp_stats_collect {returnKeyedListVarName} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        set portHandle $userArgsArray(port_handle)
        if {![::sth::sthCore::IsPortValid $portHandle eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
            return $returnKeyedList
        }
        
        # get required handles
        set pppCfg [::sth::sthCore::invoke stc::get $portHandle -children-PppProtocolConfig]
        
        set pppResults [::sth::sthCore::invoke stc::get $pppCfg -children-PppProtocolResults]
        
        set hdlArray(PppProtocolResults) $pppResults
              
        foreach key [array names ::sth::ppp::ppp_stats_mode] {
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_stats $key supported] "false"]} {
                continue
            }
            if {[string match [set stcObj [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_stats $key stcobj]] "_none_"]} {
                continue
            }
            if {$stcObj == "PppProtocolResults"} {
                if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_stats $key stcattr]] "_none_"]} {
                    continue
                }
				set val [::sth::sthCore::invoke stc::get $hdlArray($stcObj) -$stcAttr]
                keylset returnKeyedList $key $val
            }
        } 
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::ppp::ppp_stats_clear {returnKeyedListVarName} {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {      
        # Clear ALL stats
        if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAllProtocol} err ]} {
            ::sth::sthCore::processError returnKeyedList "Internal error occured: $err"
            return -code error $returnKeyedList 
        } 
    } returnedString]
    
    return -code $retVal $returnedString  
}

proc ::sth::ppp::configHostEncap { handle mode } {
    variable userArgsArray
    
    if {[string match -nocase "ipv4if*" $handle]} {
        
        set optionValueList [getStcOptionValueList ppp_config configHostEncap $mode $handle]
        set optionValueList "$optionValueList -AddrResolver PppProtocol"
        
        if {[llength $optionValueList]} {
            if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                return -code error $returnKeyedList
            }
        }
    } elseif {[string match -nocase "ipv6if*" $handle]} {
        
        set optionValueList [getStcOptionValueList ppp_config configHostEncap $mode $handle]
        set optionValueList "$optionValueList -AddrResolver PppProtocol"
        
        if {[llength $optionValueList]} {
            if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                return -code error $returnKeyedList
            }
        }
    }
    
}

proc ::sth::ppp::configSonetConfig { handle mode } {
    set optionValueList [getStcOptionValueList ppp_config configSonetConfig $mode $handle]
    # config Sonet Mode to be "PPP" automatically
    set optionValueList "$optionValueList -HdlcEnable DISABLE"

    if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
        return -code error $returnKeyedList
    }
}


proc ::sth::ppp::configPPPProtocolConfig { handle mode } {
    set optionValueList [getStcOptionValueList ppp_config configPPPProtocolConfig $mode $handle]
    # config protocol type to "PPPOPOS" automatically
    set optionValueList "$optionValueList -Protocol PPPOPOS"
    
    if {[catch {::sth::sthCore::invoke stc::config $handle $optionValueList} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
        return -code error $returnKeyedList
    }
}


proc ::sth::ppp::process_ppp_config_fcsSize {handle myswitch value} {
    
    set fcssize ""
    if {$value == "16"} {
        set fcssize "FCS16"
    } elseif {$value == "32"} {
        set fcssize "FCS16"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
  
    return "-$stcattr $fcssize"
}

###
# process_ppp_config_remoteAddrOverride
#
# Notes:
# 1) If -peer_addr_given is 1, -peer_addr can be confiugred when IPv4CP is enabled (-ipv6_cp is 0);
#   on the contrary, -peer_intf_id can be configured when IPv6CP is enabled (-ipv6_cp is 1).
# 
# 2) If -peer_addr_given is 0, you can not configure -peer_addr or -peer_intf_id.
#
# 3) If -peer_addr_override(optional) is 1, which allows the peer to override the local setting for the peer,
#    set -peer_addr to 0.0.0.0 or -peer_intf_id to 0:0:0:0:0:0:0:0 automatically. If -peer_addr_override is 0,
#    the value of -peer_addr set by user can be negonicated by transmitting Configuration-Request packets.
#
# 4) If -peer_addr is 0.0.0.0, -peer_addr_override is automatically set to 1.
###
proc ::sth::ppp::process_ppp_config_remoteAddrSetting {handle myswitch value} {
    variable userArgsArray
        
    set ipcp ""
    set peerAddr ""

    if {$myswitch == "peer_addr"} {
        #if {[string match -nocase "ipv6if*" $handle]} {
        #    ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv4CP is disabled." {}
        #    return -code error $returnKeyedList 
        #}
        if {[info exist userArgsArray(ipv6_cp)] && ($userArgsArray(ipv6_cp) == 1)} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv4CP is disabled." {}
            return -code error $returnKeyedList 
        }
        set ipcp "-IpcpEncap IPV4"
        
        if {$userArgsArray(peer_addr_given) == 0} {     
            set userArgsArray(peer_addr) "0.0.0.0"
        }  
        
        if {[info exists userArgsArray(peer_addr_override)] && $userArgsArray(peer_addr_override) == 1} {
            set peerAddr "0.0.0.0"
            set userArgsArray(peer_addr) $peerAddr
        } elseif {$userArgsArray(peer_addr_override) == 0} {
            set peerAddr $userArgsArray(peer_addr)
            # If -peer_addr is 0.0.0.0, -peer_addr_override is automatically set to 1.
            if {$peerAddr == "0.0.0.0"} {
                set userArgsArray(peer_addr_override) 1
            }
        }
        
    } elseif {$myswitch == "peer_intf_id"} {
        #if {[string match -nocase "ipv4if*" $handle]} {
        #    ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv6CP is disabled" {}
        #    return -code error $returnKeyedList 
        #}
        if {([info exist userArgsArray(ipv6_cp)] && $userArgsArray(ipv6_cp) == 0) || (![info exists userArgsArray(ipv6_cp)])} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv6CP is disabled" {}
            return -code error $returnKeyedList 
        }
        set ipcp "-IpcpEncap IPV6"
        
        if {$userArgsArray(peer_addr_given) == 0} {     
            set userArgsArray(peer_intf_id) "0:0:0:0"
        } 
        
        
        if {[info exists userArgsArray(peer_addr_override)] && $userArgsArray(peer_addr_override) == 1} {
            set userArgsArray(peer_intf_id) "0:0:0:0"
        } elseif {$userArgsArray(peer_addr_override) == 0} {
            # If -peer_addr is 0.0.0.0, -peer_addr_override is automatically set to 1.
            if {$userArgsArray(peer_intf_id) == "0:0:0:0"} {
                set userArgsArray(peer_addr_override) 1
            }
        }
        
        set peerAddr "fe80::$userArgsArray(peer_intf_id)"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
 
    return "-$stcattr $peerAddr $ipcp"
}

###
# process_ppp_config_localAddrSetting
#
# Notes:
# 1) If -local_addr_given is 1, local address specified by -local_addr can be negotiated by transmitting 
#    Configuration-Request packets when IPv4CP is enabled (-ipv6_cp is 0);
#    similarly, -local_intf_id can be configured when IPv6CP is enabled (-ipv6_cp is 1).
# 
# 2) If -local_addr_given is 0, the specified local address will not be negotiated, the remote end sets the local setting
#    for the local end (by setting -local_addr to 0.0.0.0 or -local_intf_id to 0:0:0:0 automatically).
#
# 3) If -local_addr_override is 1, it allows the remote end to override the local setting for the local end compulsively,
#    (by setting -local_addr to 0.0.0.0 or -local_intf_id to 0:0:0:0 automatically).
#
# 4) If -local_addr is 0.0.0.0, -local_addr_override is automatically set to 1.
###
proc ::sth::ppp::process_ppp_config_localAddrSetting {handle myswitch value} {
    
    variable userArgsArray
    set localAddr ""
    
    if {$myswitch == "local_addr"} {
        if {[string match -nocase "ipv6if*" $handle]} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv4CP is disabled." {}
            return -code error $returnKeyedList 
        }
        if {[info exist userArgsArray(ipv6_cp)] && ($userArgsArray(ipv6_cp) == 1)} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv4CP is disabled." {}
            return -code error $returnKeyedList 
        }
        #
        # case 1: local_addr_given is 0, requiring its peer to set its local address
        #
        if {$userArgsArray(local_addr_given) == 0} {     
            set userArgsArray(local_addr) "0.0.0.0"
        }  
        #  
        # case 2: local_addr_override is 1, its peer overrides its local address compulsively
        #
        if {[info exists userArgsArray(local_addr_override)] && $userArgsArray(local_addr_override) == 1} {
            set localAddr "0.0.0.0"
            set userArgsArray(local_addr) $localAddr
        } elseif {$userArgsArray(local_addr_override) == 0} {
        #
        # case 3: local_addr_given is 1 && local_addr_given is 0, negotiating the specified local address
        #
            set localAddr $userArgsArray(local_addr)
            # If -local_addr is 0.0.0.0, -local_addr_override is automatically set to 1.
            if {$localAddr == "0.0.0.0"} {
                set userArgsArray(local_addr_override) 1
            }
        }
    } elseif {$myswitch == "local_intf_id"} {
        if {[string match -nocase "ipv4if*" $handle]} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv6CP is disabled" {}
            return -code error $returnKeyedList 
        }
        if {([info exist userArgsArray(ipv6_cp)] && $userArgsArray(ipv6_cp) == 0) || (![info exists userArgsArray(ipv6_cp)])} {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be configured when IPv6CP is disabled" {}
            return -code error $returnKeyedList 
        }
        
        if {$userArgsArray(local_addr_given) == 0} {     
            set userArgsArray(local_intf_id) "0:0:0:0"
        } 
        
        if {[info exists userArgsArray(local_addr_override)] && $userArgsArray(local_addr_override) == 1} {
            ##
            # config the IPv6CP local interface identifier (latter 64-bit), IPv6CP begins with "fe80::"
            #
            ##
            set userArgsArray(local_intf_id) "0:0:0:0"
        } elseif {$userArgsArray(local_addr_override) == 0} {
            # If -local_intf_id is 0:0:0:0, -local_addr_override is automatically set to 1.
            if {$userArgsArray(local_intf_id) == "0:0:0:0"} {
                set userArgsArray(local_addr_override) 1
            }
        }
        set localAddr "fe80::$userArgsArray(local_intf_id)"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
 
    return "-$stcattr $localAddr"
}


proc ::sth::ppp::process_ppp_config_authentication {handle myswitch value} {
    #checkDependency "ppp_config" $myswitch "chap pap"
    variable userArgsArray
    set authConfig ""
    if {$myswitch == "local_auth_mode"} {
        if {$value == "none"} {
            set auth "NONE"
        } elseif {$value == "pap"} {
            set auth "PAP"
            #set default password and username: spirent spirent
            if {![info exists userArgsArray(password)]} {
                set userArgsArray(password) "spirent"
            }
            if {![info exists userArgsArray(username)]} {
                set userArgsArray(username) "spirent"
            }
        } elseif {$value == "chap"} {
            set auth "CHAP_MD5"
            if {![info exists userArgsArray(password)]} {
                set userArgsArray(password) "spirent"
            }
            if {![info exists userArgsArray(username)]} {
                set userArgsArray(username) "spirent"
            }
        }
        set authConfig $auth
    } elseif {$myswitch == "password"} {
        if {(![info exist userArgsArray(local_auth_mode)]) || ($userArgsArray(local_auth_mode) == "none") } {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be set, please configure -local_auth_mode to be chap or pap" {}
            return -code error $returnKeyedList 
        }
        set authConfig $value    
    } elseif {$myswitch == "username"} {
        if {(![info exist userArgsArray(local_auth_mode)]) || ($userArgsArray(local_auth_mode) == "none") } {
            ::sth::sthCore::processError returnKeyedList "switch -$myswitch can not be set, please configure -local_auth_mode to be chap or pap" {}
            return -code error $returnKeyedList 
        }
        set authConfig $value
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr $authConfig"
    
}

proc ::sth::ppp::process_ppp_config_lcpAchoInterval {handle myswitch value} {
    
    set config ""
    if {$myswitch == "lcp_echo_interval"} {
        set config "-EnableEchoRequest TRUE"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr $value $config"
    
}

proc ::sth::ppp::process_ppp_config_mru {handle myswitch value} {
    variable userArgsArray
    
    if {$myswitch == "lcp_local_mru"} {
        if {$userArgsArray(local_mru) == 1} {
            if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::ppp:: ppp_config $myswitch stcattr]} err]} {
                ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
                return -code error $returnKeyedList 
            }
            return "-$stcattr $value"
        } else {
            ::sth::sthCore::processError returnKeyedList "-$myswitch can not be configured when mru negotiation is disabled" {}
            return -code error $returnKeyedList 
        }
    }
}


# hostHandle - the created ppp host
proc ::sth::ppp::getIPCPType {hostHandle autoHost} {
    
    upvar $autoHost host
    
    if {![IsPPPHandleValid $hostHandle]} {
        ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid PPP host handle" {}
        return -code error $returnKeyedList 
    }
    
    # get Port handle
    set port [::sth::sthCore::invoke stc::get $hostHandle -parent]
        
    # get PPPProtocolConfig
    set pppCfg [::sth::sthCore::invoke stc::get $port -children-PppProtocolConfig]
        
    # get the IPCP type
    set ipcp [::sth::sthCore::invoke stc::get $pppCfg -IpcpEncap]
    
    return $ipcp
}


#to check if the handle is valid PPP host Handle or not
proc ::sth::ppp::IsPPPHandleValid { handle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
	
    set cmdStatus 1
        
    if {[catch {set pppIfHandle [::sth::sthCore::invoke stc::get $handle -children-PppIf]} err]} {
	set cmdStatus 0
    }
    if {[llength $pppIfHandle] == 0} {
        set cmdStatus 0
    }

    if {$cmdStatus == 1} {
	return $SUCCESS
    } else {
	::sth::sthCore::log error "Value ($handle) is not a valid PPP host handle"
	return $FAILURE		
    }		
}

proc ::sth::ppp::checkDependency {cmdType myswitch dependentValue} {  
    # check for any dependencies in config commands
    if {[catch {::sth::sthCore::getswitchprop ::sth::ppp:: $cmdType $myswitch dependency} dependency]} { return }
    if {![string match -nocase $dependency "_none_"]} {
        if {![info exists ::sth::ppp::userArgsArray($dependency)]} {
            return -code error "\"-$myswitch\" is dependent upon the existence of \"-$dependency\"."
        } elseif {[lsearch $dependentValue $::sth::ppp::userArgsArray($dependency)] < 0} {
            return -code error "\"-$myswitch\" is dependent upon the value of \"-$dependency\" to be $dependentValue"
        }
    }
}

proc ::sth::ppp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in pppTable.tcl
    foreach item $::sth::ppp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::ppp:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::ppp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::ppp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::ppp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::ppp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::ppp:: $cmdType $opt $::sth::ppp::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::ppp::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::ppp::userArgsArray($opt)]
                }
            }
        }
    }
    return $optionValueList
}
