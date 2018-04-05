namespace eval ::sth::sip {
    variable sip_subscription_state 0
}

proc ::sth::sip::emulation_sip_config_create {returnKeyedListVarName} {

    variable userArgsArray
    variable sip_subscription_state
    
    upvar $returnKeyedListVarName returnKeyedList
    set mode create
    
    set retVal [catch {
        #if -port_handle, create a new SIP host on port, otherwise, -handle will enable SIP on the input device handle
        if {![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle or -handle." {}
            return $returnKeyedList
        }
        
        # the priority of -port_handle is higher than -handle
        if {[info exists userArgsArray(port_handle)] && [info exist userArgsArray(handle)]} {
            unset userArgsArray(handle)
        }
        
        set createNewHost ""
        if {[info exists userArgsArray(port_handle)]} {
            if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
                return $returnKeyedList
            }
            set createNewHost 1
        } else {
            set createNewHost 0
            set device $userArgsArray(handle)
            emulation_create_sip_over_device $device returnKeyedList
        }
        
        if {$createNewHost} {
            # set default values for non-user defined switches
            foreach key [array names ::sth::sip::emulation_sip_config_default] {
                if {![info exists ::sth::sip::userArgsArray($key)]} {
                    set defaultValue [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $key default]
                    if {![string match -nocase $defaultValue "_none_"]} {
                        set ::sth::sip::userArgsArray($key) $defaultValue
                    }
                }
            }
            
            set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
            
            # 1 create the sip device
            set count $userArgsArray(count)
            set device [::sth::sthCore::invoke stc::create "Emulateddevice" -under $::sth::GBLHNDMAP(project) "-DeviceCount $count"]
            
            if {[info exists userArgsArray(router_id)]} {
                ::sth::sthCore::invoke stc::config $device -routerid $userArgsArray(router_id)
            }
            
            # 2 create the Ethernet stack
            #add "mac_address_start" as a spirent extension argument
            set ethiiIf [::sth::sthCore::invoke stc::create "EthIIIf" -under $device]
                
            configEthIIIntf $ethiiIf $mode 
        
            # 3 create & configure vlan if option is provided
            if {$vlanOptFound} {
                set ethernetii_vlan 0
                set ethernetii_qinq 0
                    
                if {[info exists userArgsArray(vlan_id1)]&&(![info exists userArgsArray(vlan_id2)])} {
                    set ethernetii_vlan 1
                }
                if {[info exists userArgsArray(vlan_id2)]} {
                    if {![info exists userArgsArray(vlan_id1)]} {
                        set uerArgsArray(vlan_id1) 100
                    }
                    set ethernetii_qinq 1
                }
                if {$ethernetii_vlan} {
                    set vlanIf [::sth::sthCore::invoke stc::create VlanIf -under $device]
                    configVlanIfInner $vlanIf $mode 
                }
                if {$ethernetii_qinq} {
                    #vlan_id_inner
                    set vlanIf_inner [::sth::sthCore::invoke stc::create VlanIf -under $device]
                    configVlanIfInner $vlanIf_inner $mode 
                    
                    #vlan_id_outer
                    set vlanIf_outer [::sth::sthCore::invoke stc::create VlanIf -under $device]
                    configVlanIfOuter $vlanIf_outer $mode
                }
            }
                 
            # 4 create ip stack, only IPV4 is supported now
            if {[info exists userArgsArray(ip_version)] && [regexp 6 $userArgsArray(ip_version)]} {
                #ipv6 or dual stack
                if {$userArgsArray(ip_version) == "4_6"} {
                    set ipv4If [::sth::sthCore::invoke stc::create "Ipv4If" -under $device]
                    configIpInterface $ipv4If $mode
                    lappend ipIfList $ipv4If
                }
                
                set ipv6If [::sth::sthCore::invoke stc::create "Ipv6If" -under $device]
                configIpv6Interface $ipv6If $mode
                set ipIfPrimary $ipv6If
                
                set ipv6ifLocal [::sth::sthCore::invoke stc::create "Ipv6If" -under $device]
                if {[info exists userArgsArray(local_ipv6_addr)]} {
                    set addr $userArgsArray(local_ipv6_addr)
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal "-Address $addr -Gateway ::"
                } else {
                    set addr "FE80::0"
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal "-Address $addr -Gateway ::"
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                }
                lappend ipIfList $ipv6If $ipv6ifLocal
            } else {
                set ipIf [::sth::sthCore::invoke stc::create "Ipv4If" -under $device]
                configIpInterface $ipIf $mode
                set ipIfPrimary $ipIf
                set ipIfList $ipIf
            }
                
            
            
            # 5 create SipUaProtocolConfig under sip device
            set sipUaCfg [::sth::sthCore::invoke stc::create "SipUaProtocolConfig" -under $device]
            
            configSipUaProtocolConfig $sipUaCfg $mode
            
            # 6 create sip client profile
            #"-ProfileName {SIP DefaultClientProfile}"
            set clientProfile [::sth::sthCore::invoke stc::create "ClientProfile" -under $::sth::GBLHNDMAP(project)]
            
            #It is better to configure ProfileName, or the "AffiliatedClientProfile" relation will not take effect.
            #"DefaultClientProfile" and "SIP DefaultClientProfile" profiles are automatically created by STC SIP.
            ::sth::sthCore::invoke stc::config $clientProfile "-ProfileName SIP$clientProfile"
            
            set sipUaProfile [::sth::sthCore::invoke stc::create "SipUaProtocolProfile" -under $clientProfile]
            
            configSipUaProtocolProfile $sipUaProfile $mode
            
            # 7 create sip load profile
            set loadProfile [::sth::sthCore::invoke stc::create "ClientLoadProfile" -under $::sth::GBLHNDMAP(project)]
            
            #"SIP DefaultLoadProfile" profile is automatically created by STC SIP.
            ::sth::sthCore::invoke stc::config $loadProfile "-ProfileName SIP$loadProfile"
            
            # set flat as default load pattern
            set loadPhase [::sth::sthCore::invoke stc::create "ClientLoadPhase" -under $loadProfile "-PhaseName {Delay} -LoadPattern FLAT"]
            
            #  set default flat pattern descriptor       
            set flatPatternDescriptor "-Height 300 -RampTime 20 -SteadyTime 40"
            set flat [::sth::sthCore::invoke stc::create "FlatPatternDescriptor" -under $loadPhase $flatPatternDescriptor]
            
            # connect the romete subscribers to establish a SIP call path
            connect_remote_subscribers $device
            
            # 8 setup relations
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $device "-AffiliationPort-targets $userArgsArray(port_handle)"]
    
            if {$vlanOptFound} {
                if {$ethernetii_vlan} {
                    foreach ipIf $ipIfList {
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $vlanIf"]
                    }
                    lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf "-StackedOnEndpoint-targets $ethiiIf"]
                }
                if {$ethernetii_qinq} {
                    foreach ipIf $ipIfList {
                        lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $vlanIf_inner"]
                    }
                    lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf_inner "-StackedOnEndpoint-targets $vlanIf_outer"]
                    lappend cmd_list [list ::sth::sthCore::invoke stc::config $vlanIf_outer "-StackedOnEndpoint-targets $ethiiIf"]
                }
            } else {
                foreach ipIf $ipIfList {
                    lappend cmd_list [list ::sth::sthCore::invoke stc::config $ipIf "-StackedOnEndpoint-targets $ethiiIf" ]
                }
            }
            
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $device "-TopLevelIf-targets \"$ipIfList\""]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $device "-PrimaryIf-targets \"$ipIfPrimary\""]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-UsesIf-targets \"$ipIfPrimary\""]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-AffiliatedClientProfile-targets $clientProfile"]
            lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-AffiliatedClientLoadProfile-targets $loadProfile"]
            
            foreach cmd $cmd_list {
                if {[catch {eval $cmd} err]} {
                    ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        #end of if {$createNewHost}
        
        # 9 Create the SIP result dataset
        if {$sip_subscription_state == 0} {
            
            set sipResultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
            set sipResultQuery(1) [::sth::sthCore::invoke stc::create "ResultQuery" -under $sipResultDataSet \
	    						"-ResultRootList $::sth::GBLHNDMAP(project) \
							-ConfigClassId SipUaProtocolConfig \
							-ResultClassId SipUaResults"]
        }
        
        # apply all configurations
        if {!$::sth::sthCore::optimization} {
            if {[catch {::sth::sthCore::doStcApply} applyError]} {
                if {$createNewHost} {
                    ::sth::sthCore::invoke stc::delete $device
                }
                ::sth::sthCore::processError returnKeyedList "Error applying sip configuration: $applyError"
                return $returnKeyedList
            }
        }
        
        # Subscribe to the datasets
        if {$sip_subscription_state == 0} {
            ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $sipResultDataSet
            set sip_subscription_state 1
        }
        
        keylset returnKeyedList handle $device
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_create_sip_over_device {handle returnKeyedListVarName} {
    upvar $returnKeyedListVarName returnKeyedList
    
    variable userArgsArray
    variable sip_subscription_state
    
    set mode "create"

    if {![string match -nocase "host*" $handle]} {
        ::sth::sthCore::processError returnKeyedList "Invalid host handle: $handle"
        return -code error $returnKeyedList 
    }
        
    # 1 create sipUaProtocolConfig under existing device if no sip found
    set sipUaCfg [::sth::sthCore::invoke stc::get $handle -children-SipUaProtocolConfig]
        
    if {[string length $sipUaCfg] == 0} {
        set sipUaCfg [::sth::sthCore::invoke stc::create "SipUaProtocolConfig" -under $handle]
        configSipUaProtocolConfig $sipUaCfg $mode
        
        # 2 create sip client profile
        set clientProfile [::sth::sthCore::invoke stc::create "ClientProfile" -under $::sth::GBLHNDMAP(project)]
            
        ::sth::sthCore::invoke stc::config $clientProfile "-ProfileName SIP$clientProfile"
        
        set sipUaProfile [::sth::sthCore::invoke stc::create "SipUaProtocolProfile" -under $clientProfile]
            
        configSipUaProtocolProfile $sipUaProfile $mode
            
        # 3 create sip load profile
        set loadProfile [::sth::sthCore::invoke stc::create "ClientLoadProfile" -under $::sth::GBLHNDMAP(project)]
            
        ::sth::sthCore::invoke stc::config $loadProfile "-ProfileName SIP$loadProfile"
            
        # set flat as default load pattern
        set loadPhase [::sth::sthCore::invoke stc::create "ClientLoadPhase" -under $loadProfile "-PhaseName {Delay} -LoadPattern FLAT"]
        
        #  set default flat pattern descriptor       
        set flatPatternDescriptor "-Height 300 -RampTime 20 -SteadyTime 40"
        set flat [::sth::sthCore::invoke stc::create "FlatPatternDescriptor" -under $loadPhase $flatPatternDescriptor]
        
        # connect the romete subscribers to establish a SIP call path
        connect_remote_subscribers $handle
            
        # set relation
	set hndIf [::sth::sthCore::invoke stc::get $handle "-TopLevelIf-targets"]    
        lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-UsesIf-targets $hndIf"]
        lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-AffiliatedClientProfile-targets $clientProfile"]
        lappend cmd_list [list ::sth::sthCore::invoke stc::config $sipUaCfg "-AffiliatedClientLoadProfile-targets $loadProfile"]
        foreach cmd $cmd_list {
            if {[catch {eval $cmd} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::config Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "Failed to create more sip on sip host: $handle" {}
        return -code error $returnKeyedList 
    }
}

proc ::sth::sip::emulation_sip_config_enable {returnKeyedListVarName} {
    variable userArgsArray
    
    upvar $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch { 
        foreach hostHandle $userArgsArray(handle) {
            
            #check if the handle is a valid sip handle
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip host handle" {}
                return -code error $returnKeyedList 
            }
        
            #get SipUaProtocolConfig
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
            #enable the SIP host specified by "-handle"
            ::sth::sthCore::invoke stc::config $sipUaCfg "-Active TRUE"
        
            keylset returnKeyedList handle $userArgsArray(handle)
        }
    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::sip::emulation_sip_config_disable {returnKeyedListVarName} {
    variable userArgsArray
    
    upvar $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch {
        foreach hostHandle $userArgsArray(handle) {
        
            #check if the handle is a valid sip handle
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip host handle" {}
                return -code error $returnKeyedList 
            }
        
            #get SipUaProtocolConfig
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
            #enable the SIP host specified by "-handle"
            ::sth::sthCore::invoke stc::config $sipUaCfg "-Active FALSE"
            keylset returnKeyedList handle $userArgsArray(handle)
        }
        
    } returnedString]
    
    return -code $retVal $returnedString
}


proc ::sth::sip::emulation_sip_config_enable_all {returnKeyedListVarName} {
    variable userArgsArray
    
    upvar $returnKeyedListVarName returnKeyedList
    
    if {[info exists userArgsArray(port_handle)]} {
        if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
            return $returnKeyedList
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
        return $returnKeyedList
    }
    
    set retVal [catch {
        set portHandle $userArgsArray(port_handle)
        
        set handleList [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
        
        foreach handle $handleList {
            if {![string match -nocase "host*" $handle]} {
                continue
            }
            if {[isSipHandleValid $handle]} {
                #get SipUaProtocolConfig
                set sipUaCfg [::sth::sthCore::invoke stc::get $handle -children-SipUaProtocolConfig ]
                #enable the SIP host
                ::sth::sthCore::invoke stc::config $sipUaCfg "-Active TRUE"
                lappend sipHandleList $handle
            }  
        }
        
        keylset returnKeyedList handle $sipHandleList
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_config_disable_all {returnKeyedListVarName} {
    variable userArgsArray
    
    upvar $returnKeyedListVarName returnKeyedList
    
    if {![info exists userArgsArray(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -port_handle." {}
        return $returnKeyedList
    }
    
    if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Invalid \"-port_handle\" value $userArgsArray(port_handle)" {}
        return $returnKeyedList
    }
    
    set retVal [catch {
        set portHandle $userArgsArray(port_handle)
        
        set handleList [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
        
        foreach handle $handleList {
            if {![string match -nocase "host*" $handle]} {
                continue
            }
            if {[isSipHandleValid $handle]} {
                #get SipUaProtocolConfig
                set sipUaCfg [::sth::sthCore::invoke stc::get $handle -children-SipUaProtocolConfig ]
                #enable the SIP host
                ::sth::sthCore::invoke stc::config $sipUaCfg "-Active FALSE"
                lappend sipHandleList $handle
            }  
        }
    
        keylset returnKeyedList handle $sipHandleList
        
    } returnedString]
    
    return -code $retVal $returnedString
}

# modify a SIP UA per time
proc ::sth::sip::emulation_sip_config_modify {returnKeyedListVarName} {
    variable userArgsArray
    variable sortedSwitchPriorityList
    set mode modify
    
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle." {}
        return -code error $returnKeyedList 
    }
    
    upvar $returnKeyedListVarName returnKeyedList
    
    set unsupportedModifyOptions {port_handle count}
    
    set retVal [catch {
        set hostHandle $userArgsArray(handle)
        
        #check if the handle is a valid sip handle or not
        if {![isSipHandleValid $hostHandle]} {
            ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip host handle" {}
            return -code error $returnKeyedList 
        }
        
        #modify the router id if it is input
        if {[info exists userArgsArray(router_id)]} {
                ::sth::sthCore::invoke stc::config $hostHandle -routerid $userArgsArray(router_id)
        }
        if {[info exists userArgsArray(local_ipv6_addr)]} {
            set addr $userArgsArray(local_ipv6_addr)
            set ipv6ResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-ipv6if ]
            foreach ipIf $ipv6ResultIf {
                set ipaddr [::sth::sthCore::invoke stc::get $ipIf -Address ]
                if {[regexp -nocase "FE80" $ipaddr] } {
                    ::sth::sthCore::invoke stc::config $ipIf "-Address $addr -Gateway ::"
                }
            }
        } 
         
        set functionsToRun {}
        foreach item $sortedSwitchPriorityList {
            foreach {priority switchname} $item {
                # make sure the option is supported
                if {![::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $switchname supported]} {
                    ::sth::sthCore::processError returnKeyedList "Error: \"-$switchname\" is not supported" {}
                    return -code error $returnKeyedList 
                }
                if {[lsearch $unsupportedModifyOptions $switchname] > -1} {
        	    ::sth::sthCore::processError returnKeyedList "unable to modify the \"-$switchname\" in modify mode" {}
                    return -code error $returnKeyedList 
        	}
            
                if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $switchname mode] "_none_"]} { continue }
                set func [::sth::sthCore::getModeFunc ::sth::sip:: emulation_sip_config $switchname modify]
                if {[lsearch $functionsToRun $func] == -1} {
                    lappend functionsToRun $func
                }
            }
        }
        
        foreach func $functionsToRun {
        # these functions are mapped to switches in sipTable.tcl
            switch -- $func {
                configVlanIfInner {
                    set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-vlanif ]
                    
                    if {[llength vlanIf] == 0} {
                            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $hostHandle."
                            return -code error $returnKeyedList
                    }
                    if {[llength $vlanIf] > 1} {
                        set vlanIf [lindex $vlanIf 0]
                    }
                    
                    configVlanIfInner $vlanIf $mode
                }
                configVlanIfOuter {
                    set vlanIf [::sth::sthCore::invoke stc::get $hostHandle -children-vlanif]
                    if {[llength $vlanIf] < 2} {
                        ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $hostHandle."
                        return -code error $returnKeyedList
                    }
                    set vlanIf [lindex $vlanIf 1]
                    configVlanIfOuter $vlanIf $mode
                    
                }
                configIpInterface {
                    set ipResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-ipv4if ]
                    foreach ipIf $ipResultIf {
                        configIpInterface $ipIf $mode
                    }
                }
                configIpv6Interface {
                    set ipv6ResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-ipv6if ]
                    foreach ipIf $ipv6ResultIf {
                        set ipaddr [::sth::sthCore::invoke stc::get $ipIf -Address ]
                        if {![regexp -nocase "FE80" $ipaddr] } {
                            configIpv6Interface $ipIf $mode
                        }
                    }
                }
                configEthIIIntf {
                    set ethiiIf [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiIf ]
                    configEthIIIntf $ethiiIf $mode 
                }
                configSipUaProtocolConfig {
                    set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
                    configSipUaProtocolConfig $sipUaCfg $mode
                }
                configSipUaProtocolProfile {
                    set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
                    
                    set clientProfile [::sth::sthCore::invoke stc::get $sipUaCfg "-AffiliatedClientProfile-targets"]
                    
                    set sipUaProfile [::sth::sthCore::invoke stc::get $clientProfile -children-SipUaProtocolProfile]
        
                    configSipUaProtocolProfile $sipUaProfile $mode
                }
                default {
                    ::sth::sthCore::processError returnKeyedList "unknown function: $func" {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
        keylset returnKeyedList handle $userArgsArray(handle)
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_config_delete {returnKeyedListVarName} {
    
    variable userArgsArray
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle."
        return $returnKeyedList
    }

    upvar $returnKeyedListVarName returnKeyedList
    set retVal [catch {
        
        #delete a list of SIP UAs
        foreach rtr $userArgsArray(handle) {
            if {![isSipHandleValid $rtr]} {
                ::sth::sthCore::processError returnKeyedList "Error: $rtr is not a valid sip host handle" {}
                return -code error $returnKeyedList 
            }
            
            # delete RTP_steamblock and RTCP_steambolock created after successfull sip call
            # fix CR 190905641
            
                #get ip stack
            set ipIf [::sth::sthCore::invoke stc::get $rtr -TopLevelIf-targets]
            #get all the streams under the affiliated port
            set portHandle [::sth::sthCore::invoke stc::get $rtr -AffiliationPort-targets]
            set streamHandle [::sth::sthCore::invoke stc::get $portHandle -children-streamblock]
            
            foreach stream $streamHandle {
                set ipList [::sth::sthCore::invoke stc::get $stream "-srcbinding-Targets -dstbinding-Targets"]
                # delete the assiciated streamblcok
                if {[lsearch $ipList $ipIf] >= 0} {
                    ::sth::sthCore::invoke stc::delete $stream
                }
            }
            
            ::sth::sthCore::invoke stc::delete $rtr
            
        }
        
    } returnedString]

    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_control_register {returnKeyedListVarName} {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList 
    
    set retVal [catch {
        #check the enable state before registering
        emulation_sip_config_enable returnKeyedList
        
        set sipUaList ""
        
        foreach hostHandle $userArgsArray(handle) {
        
            set actionFlag 0
            if {[info exists userArgsArray(action_control)] && $userArgsArray(action_control) == "start"} {
                set actionFlag 1
            }
    
            if {$actionFlag == 1} {
                processRegisterRate returnKeyedList $hostHandle
            }
            
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig]
            
            set clientProfile [::sth::sthCore::invoke stc::get $sipUaCfg -AffiliatedClientProfile-targets]
            
            set sipUaProfile [::sth::sthCore::invoke stc::get $clientProfile -children-SipUaProtocolProfile]
            
            set peerFlag [::sth::sthCore::invoke stc::get $sipUaProfile -UseUaToUaSignaling]
            
            #Under peer to peer situation, SIP UA does not need to register.
            if {$peerFlag == 1} {
                return
            }
        
            append sipUaList $sipUaCfg
        }
        
        ::sth::sthCore::invoke stc::perform SipRegister -UaProtocolList $hostHandle
 
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_control_deregister {returnKeyedListVarName} {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        
        set sipUaList ""
        foreach hostHandle $userArgsArray(handle) {
        
        set actionFlag 0
        if {[info exists userArgsArray(action_control)] && $userArgsArray(action_control) == "start"} {
            set actionFlag 1
        }
    
        if {$actionFlag == 1} {
            processRegisterRate returnKeyedList $hostHandle
        }
        
        set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
        set clientProfile [::sth::sthCore::invoke stc::get $sipUaCfg -AffiliatedClientProfile-targets]
            
        set sipUaProfile [::sth::sthCore::invoke stc::get $clientProfile -children-SipUaProtocolProfile]
        
        set peerFlag [::sth::sthCore::invoke stc::get $sipUaProfile -UseUaToUaSignaling]
            
        #Under peer to peer situation, SIP UA does not need unregistration process
        if {$peerFlag == 1} {
            return
        }
        
        append sipUaList $sipUaCfg      
    } 
        ::sth::sthCore::invoke stc::perform SipUnRegister -UaProtocolList $hostHandle
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_control_establish {returnKeyedListVarName} {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        
        set sipUaList ""
        foreach hostHandle $userArgsArray(handle) {
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip handle" {}
                return -code error $returnKeyedList 
            }
        
            # check the register state
        
            set actionFlag 0
            if {[info exists userArgsArray(action_control)] && $userArgsArray(action_control) == "start"} {
                set actionFlag 1
            }
            
            if {$actionFlag == 1} {
                processCallRate returnKeyedList $hostHandle
            }
            
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig]
            
            set dstHandle [::sth::sthCore::invoke stc::get $sipUaCfg -ConnectionDestination-targets]
            
            if {[llength $dstHandle] == 0} {
                ::sth::sthCore::processError returnKeyedList "Only the UACs are supposed to initiate the SIP call" {}
                return -code error $returnKeyedList
            }
            
            append sipUaList $sipUaCfg     
        }
        ::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $sipUaList
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_control_terminate {returnKeyedListVarName} {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        set sipUaList ""
        foreach hostHandle $userArgsArray(handle) {
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip handle" {}
                return -code error $returnKeyedList 
            }
        
            set actionFlag 0
            if {[info exists userArgsArray(action_control)] && $userArgsArray(action_control) == "start"} {
                set actionFlag 1
            }
        
            if {$actionFlag == 1} {
                processCallRate returnKeyedList $hostHandle
            }
            
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
            append sipUaList $sipUaCfg
        }
        ::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $sipUaList
        
    } returnedString]
    
    return -code $retVal $returnedString
}

proc ::sth::sip::emulation_sip_stats_collect {returnKeyedListVarName} {
    
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        foreach hostHandle $::sth::sip::userArgsArray(handle) {
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip handle" {}
                return -code error $returnKeyedList 
            }
            # get required handles
            set sipUaCfg [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig ]
            
            set sipUaResults [::sth::sthCore::invoke stc::get $sipUaCfg -children-sipuaresults ]
            
            # create an array mapping between stcObj and stcHandle
            set hdlArray(SipUaProtocolConfig) $sipUaCfg
            set hdlArray(SipUaResults) $sipUaResults

            set sipRegState [::sth::sthCore::invoke stc::get $hdlArray(SipUaProtocolConfig) -RegState]
            # Enum: NOT_REGISTERED|REGISTERING|REGISTRATION_SUCCEEDED|REGISTRATION_FAILED|REGISTRATION_CANCELED|UNREGISTERING
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "$hostHandle.registration_state" $sipRegState]

            
            set mode $::sth::sip::userArgsArray(mode)
            foreach key [array names ::sth::sip::emulation_sip_stats_mode] {
                foreach tblMode $::sth::sip::emulation_sip_stats_mode($key) {
                    if {[string match $tblMode $mode]} {
                        if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_stats $key supported] "false"]} {
                            continue
                        }
                        if {[string match [set stcObj [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_stats $key stcobj]] "_none_"]} {
                            continue
                        }
                        
                        if {[string match [set stcAttr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_stats $key stcattr]] "_none_"]} {
                            continue
                        }
                        set val [::sth::sthCore::invoke stc::get $hdlArray($stcObj) -$stcAttr]
                        #example: session.<handle>.statistics
                        if {$tblMode == "device"} {
                            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList "session.$hostHandle.$key" $val]
                        }
                    }
                }
            }
        }
    } returnedString]
    
    return -code $retVal $returnedString    
}

proc ::sth::sip::emulation_sip_stats_clear {returnKeyedListVarName} {
    variable userArgsArray
    upvar $returnKeyedListVarName returnKeyedList
    
    set retVal [catch {
        foreach hostHandle $::sth::sip::userArgsArray(handle) {
            if {![isSipHandleValid $hostHandle]} {
                ::sth::sthCore::processError returnKeyedList "Error: $hostHandle is not a valid sip handle" {}
                return -code error $returnKeyedList 
            }
                
            # Clear ALL stats
            ::sth::sthCore::invoke stc::perform ResultsClearAllProtocol
        }
    } returnedString]
    
    return -code $retVal $returnedString  
}

###
# processRegisterRate
#   
#
#
###
proc ::sth::sip::processRegisterRate {returnValue sipHandle} {
    
    variable userArgsArray
    upvar $returnValue returnKeyedList
     
    set batchRate 1
    if {[info exists userArgsArray(batch_rate)]} {
        set batchRate $userArgsArray(batch_rate)
    }
    set regsPerSec "-RegsPerSecond $batchRate"
        
    set clientProfile [::sth::sthCore::invoke stc::get $sipHandle "-AffiliatedClientProfile-targets"]
    if {[string length $clientProfile] == 0} { return }
        
    set sipUaProfile [::sth::sthCore::invoke stc::get $clientProfile -children-SipUaProtocolProfile]
        
    ::sth::sthCore::invoke stc::config $sipUaProfile $regsPerSec
}

proc ::sth::sip::processCallRate {returnValue sipHandle} {
    variable userArgsArray
    upvar $returnValue returnKeyedList
    
    set batchRate 1
    if {[info exists userArgsArray(batch_rate)]} {
        set batchRate $userArgsArray(batch_rate)
    }
    
    set count [::sth::sthCore::invoke stc::get $sipHandle "-DeviceCount"]
      
    set loadProfile [::sth::sthCore::invoke stc::get $sipHandle "-AffiliatedClientLoadProfile-targets"]
    if {[string length $loadProfile] == 0} { return }
        
    set loadPhase [::sth::sthCore::invoke stc::get $loadProfile "-children-ClientLoadPhase"]
    
    set flatDesp [::sth::sthCore::invoke stc::get $loadPhase "-children-FlatPatternDescriptor"]
    
    set rampTime [expr $count/$batchRate]
    set callPerSec "-Height $count -RampTime $rampTime -SteadyTime 0"
    
    ::sth::sthCore::invoke stc::config $flatDesp $callPerSec
    
}

proc ::sth::sip::configVlanIfInner { handle mode } {
    set optionValueList [getStcOptionValueList emulation_sip_config configVlanIfInner $mode $handle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configVlanIfOuter { handle mode } {
    set optionValueList [getStcOptionValueList emulation_sip_config configVlanIfOuter $mode $handle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configIpInterface { handle mode } {
    set optionValueList [getStcOptionValueList emulation_sip_config configIpInterface $mode $handle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configIpv6Interface { handle mode } {
    set optionValueList [getStcOptionValueList emulation_sip_config configIpv6Interface $mode $handle]

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configEthIIIntf { handle mode } {
    variable userArgsArray
    set optionValueList [getStcOptionValueList emulation_sip_config configEthIIIntf $mode $handle]
    set optionValueList "$optionValueList -SrcMacStep 00:00:00:00:00:01"
    if {![info exists userArgsArray(mac_address_start)]} {
        set mac "00:10:94:00:00:02"
        set optionValueList [concat $optionValueList "$optionValueList -SourceMac $mac"]
    }

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configSipUaProtocolConfig { handle mode } {
    variable userArgsArray
    set optionValueList [getStcOptionValueList emulation_sip_config configSipUaProtocolConfig $mode $handle]
    # set default local port 5060
    if {![info exists userArgsArray(local_port)]} {
        set optionValueList [concat $optionValueList "$optionValueList -LocalPort 5060"]
    }

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::configSipUaProtocolProfile { handle mode } {
    variable userArgsArray
    set optionValueList [getStcOptionValueList emulation_sip_config configSipUaProtocolProfile $mode $handle]
    #set default proxy server port 5060
    if {![info exists userArgsArray(proxy_server_port)]} {
        set optionValueList [concat $optionValueList "$optionValueList -ProxyPort 5060"]
    }

    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $handle $optionValueList
    }
}

proc ::sth::sip::processEmulation_sip_config_vlanId {vlanHandle myswitch value} {
    variable userArgsArray

    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    if {[string match -nocase $myswitch "vlan_id1"]} {
        if {[info exists userArgsArray(vlan_id_mode1)] && \
            [string match -nocase $userArgsArray(vlan_id_mode1) "increment"]} {
            if {![info exists userArgsArray(vlan_id_step1)]} {
                set userArgsArray(vlan_id_step1) 1
            }
            set idStep "-IdStep $userArgsArray(vlan_id_step1)"
        } else {
            set idStep "-IdStep 0"
        }      
    } elseif {[string match -nocase $myswitch "vlan_id2"]} {
        if {[info exists userArgsArray(vlan_id_mode2)] && \
            [string match -nocase $userArgsArray(vlan_id_mode2) "increment"]} {
            if {![info exists userArgsArray(vlan_id_step2)]} {     
               set userArgsArray(vlan_id_step2) 1
            }
            set idStep "-IdStep $userArgsArray(vlan_id_step2)"
        } else {
            set idStep "-IdStep 0"
        }  
    }
    return "-$stcattr $value $idStep"
}

proc ::sth::sip::processEmulation_sip_config_vlanType { vlanIfHandle myswitch value} {
    
    variable userArgsArray
    
    set vlantype ""  
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    if {[string match -nocase $myswitch "vlan_ether_type1"]} {
        if {![info exists userArgsArray(vlan_id1)]} {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_id1 is required when \"-vlan_ether_type1\" is used" {}
            return -code error $returnKeyedList 
        }
        set vlantype $value
        
        #convert HEX to decimal
        set decVlantype [format "%i" $vlantype]    
    } elseif {[string match -nocase $myswitch "vlan_ether_type2"]} {
        if {![info exists userArgsArray(vlan_id2)]} {
            ::sth::sthCore::processError returnKeyedList "switch -vlan_id2 is required when \"-vlan_ether_type2\" is used" {}
            return -code error $returnKeyedList 
        }
        set vlantype $value

        #convert HEX to decimal
        set decVlantype [format "%i" $vlantype]  
    }
    return "-$stcattr $decVlantype"
}

proc ::sth::sip::processEmulation_sip_config_local_username { sipUaCfgHandle myswitch value} {
    
    set uaNum ""
    if {$myswitch == "local_username_prefix"} {
        set uaNum "$value%u"
    }
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $uaNum"
}

###
#  Name:    processEmulation_sip_config_ipaddress_step
#  Inputs:  ipIfHandle - ipv4if handle
#           myswitch -"local_ip_addr_step" or "remote_ip_addr_step" switch
#           value - ip address step value <integer>
#  Outputs: "-AddrStep a.b.c.d" or "-GatewayStep a.b.c.d"
#  Description: This procedure converts "-local_ip_addr_step" or "-remote_ip_addr_step"from integer to IPv4 format.
###

proc ::sth::sip::processEmulation_sip_config_ip_addr_step { ipIfHandle myswitch value } {
    
    variable userArgsArray
    
    set newstep [::sth::sthCore::intToIpv4Address $value]
    
    #set newpoolstep ""
    ##convert integer to IPv4
    #binary scan [binary format I* $value] B32 poolstep
    #for {set x 0; set y 7} {$y < 32} {} {
    #    set oct [string range $poolstep $x $y]
    #    binary scan [binary format B32 $oct] i ip
    #    lappend newpoolstep $ip
    #    set x [expr {$x+8}]
    #    set y [expr {$y+8}]
    #}
    #set newstep [join $newpoolstep .]
        
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $newstep" 
}


proc ::sth::sip::processEmulation_sip_config_ip_addr_repeat { ipIfHandle myswitch value } {
    variable userArgsArray
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    if {$value > 0} {
        set addrRepeat [expr $value -1]
    } else {
        set addrRepeat 0
    }
    
    return "-$stcattr $addrRepeat" 
}
###
#  Name:    processEmulation_sip_config_registration
#  Description: Specifies whether to enable registration transaction,
#       "True" indicates calls will be established through SIP server. 
#       "False" indicates calls will be established directly between two UAs without SIP server,
#        no registration transaction. And the proxy will be disabled (0.0.0.0)
###

proc ::sth::sip::processEmulation_sip_config_registration { ipIfHandle myswitch value } {
    variable userArgsArray
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    set peer_to_peer_signal ""
    if {$myswitch == "registration_server_enable"} {
        if {$value == 0} {
            set peer_to_peer_signal "true"
            #disable the proxy server
            if {[info exist userArgsArray(registrar_address)]} {
                set userArgsArray(registrar_address) "0.0.0.0"
            }
        } else {
            set peer_to_peer_signal "false"
            #proxy address is required when two SIP UAs connect through a Server
            if {![info exists userArgsArray(registrar_address)]} {
                ::sth::sthCore::processError returnKeyedList "-registrar_address is required when when SIP UAs connect through a Server" {}
                return -code error $returnKeyedList 
            }
        }
    }
    
    return "-$stcattr $peer_to_peer_signal" 
}
###
#  Name:    processEmulation_sip_config_media_type
#  Description: Specifies SIP Audio Codec type: G_711|G_723_1|G_729
###
proc ::sth::sip::processEmulation_sip_config_media_type { sipUaPflHandle myswitch value } {
    variable userArgsArray
    
    set media_type ""
    set sipCallType ""
    if {![info exist userArgsArray(call_type)]} {
        set sipCallType "-CallType AUDIO_ONLY"
    } 

    if {[string match -nocase userArgsArray(call_type) "SIGNALING_ONLY"]} {
    #SIP Audio Codec will be configured under "AUDIO_ONLY" or "AUDIO_VIDEO" type
        return 
    }
    
    if {$value == "SIP_MEDIA_ITU_G711_64K_240BYTE" || $value == "SIP_MEDIA_ITU_G711_64K_160BYTE"} {
        set media_type "G_711"
    } elseif {$value == "SIP_MEDIA_ITU_G723_6K3_24BYTE" || $value == "SIP_MEDIA_ITU_G723_5K3_20BYTE"
    || $value == "SIP_MEDIA_ITU_G723_5K3_40BYTE"} {
        set media_type "G_723_1"
    } elseif {$value == "SIP_MEDIA_ITU_G729_8K_20BYTE" || $value == "SIP_MEDIA_ITU_G729_8K_40BYTE"} {
        set media_type "G_729"
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    return "-$stcattr $media_type $sipCallType" 
}

proc ::sth::sip::processEmulation_sip_config_vedio_type { ipIfHandle myswitch value } {
    variable userArgsArray
    
    #SIP Vedio Codec will be configured under "AUDIO_VIDEO" type
    if {![info exist userArgsArray(call_type)] || ![string match -nocase $userArgsArray(call_type) "AUDIO_VIDEO"]} {
        return
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr $value"
}

proc ::sth::sip::processEmulation_sip_config_ringTime { sipUaPflHandle myswitch value } {
    variable userArgsArray
    
    if {![info exist userArgsArray(call_accept_delay_enable)]} {
        set userArgsArray(call_accept_delay_enable) 1
    }
    
    if {$userArgsArray(call_accept_delay_enable) == 0} {
        return
    }
    
    if {[catch {set stcattr [::sth::sthCore::getswitchprop ::sth::sip:: emulation_sip_config $myswitch stcattr]} err]} {
        ::sth::sthCore::processError returnKeyedList "Error processing switch: -$myswitch $err" {}
        return -code error $returnKeyedList 
    }
    
    return "-$stcattr $value"
}
####
# connect_remote_subscribers
#   creat the relation between caller and callee.
#  
# 1, If SIP makes a call going through a Proxy server, only the user name of the callee is required (remote_username_prefix|remote_username_suffix).
# The proxy server will find the callee by name mapping.
# 2, When SIP makes a peer to peer call, the ip address of the remote subscriber is required
#(call_using_aor=1|remote_host|remote_host_step).
####

proc ::sth::sip::connect_remote_subscribers { sipHandle } {
    variable userArgsArray
    
    set calleeHandle ""
    #1 : under peer_to_peer situation
    if {$userArgsArray(registration_server_enable) == 0} {
        if {![info exists userArgsArray(call_using_aor)] || $userArgsArray(call_using_aor) == 0} {
            ::sth::sthCore::processError returnKeyedList "-call_using_aor should be set to 1 to enable remote subscribers
            when SIP call is established directly between two UAs without SIP server." {}
            return -code error $returnKeyedList
        } else {
            set calleeHandle [isRemoteHostMatched $sipHandle]
        }
    } else {
        #2 : using proxy server
        set calleeHandle [isRemoteUserNameMatched $sipHandle]
    }
    
    #find the callee handle and bind the call relation
    if {[llength $calleeHandle] != 0} {
        
        set sipLocalCfgHandle [::sth::sthCore::invoke stc::get $sipHandle -children-SipUaProtocolConfig]
        
        set sipRemoteCfgHandle [::sth::sthCore::invoke stc::get $calleeHandle -children-SipUaProtocolConfig]
        
        #connect relation
        ::sth::sthCore::invoke stc::config $sipLocalCfgHandle "-ConnectionDestination-targets $sipRemoteCfgHandle"
    }
}

proc ::sth::sip::isRemoteHostMatched {sipHandle} {
    variable userArgsArray
    
    if {[info exists userArgsArray(call_using_aor)] && $userArgsArray(call_using_aor) == 0} {
        return
    }
    
    set remoteHost ""
    set remoteStep 0.0.0.1
    set remoteRepeat 1
    
    #convert integer step to IPv4 address format
    if {[info exists userArgsArray(remote_host_step)]} {
        if {[info exists userArgsArray(ip_version)] && $userArgsArray(ip_version) == "6"} {
            #the step is ipv6 format if ip version is ipv6
            set remoteStep $userArgsArray(remote_host_step)
        } else {
            set remoteStep [::sth::sthCore::intToIpv4Address $userArgsArray(remote_host_step)]
        }
    }
    
    if {[info exists userArgsArray(remote_host)]} {
        set remoteHost $userArgsArray(remote_host)
    }
    
    if {[info exists userArgsArray(remote_host_repeat)]} {
        set remoteRepeat $userArgsArray(remote_host_repeat)
    }
    
    #get the existing SIP UAs
    set hostList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]
    
    set calleeHandle ""
    foreach host $hostList {
        if {![isSipHandleValid $host]} {
            continue
        }
        if {$sipHandle == $host} {
            continue
        }
        set count [::sth::sthCore::invoke stc::get $host -devicecount]
        if {$count != $userArgsArray(count)} {
            ::sth::sthCore::processError returnKeyedList "STC only supports one-to-one call" {}
            return -code error $returnKeyedList 
        }
        if {[info exists userArgsArray(ip_version)]  && $userArgsArray(ip_version) == "6"} {
            set ipv6If [::sth::sthCore::invoke stc::get $host -children-ipv6if]
            foreach ipIf $ipv6If {
                set ipaddr [::sth::sthCore::invoke stc::get $ipIf -Address]
                if {![regexp -nocase "FE80" $ipaddr]} {
                    break
                }
            }
        } else {
            set ipIf [::sth::sthCore::invoke stc::get $host -children-ipv4if]
        }
        
        array set ipOpt [::sth::sthCore::invoke stc::get $ipIf "-Address -AddrStep -AddrRepeatCount"]
        if {$remoteHost == $ipOpt(-address) && $remoteStep == $ipOpt(-addrstep) && $remoteRepeat == [expr {$ipOpt(-addrrepeatcount) + 1}]} {
            append calleeHandle $host
        }    
    }
    
    if {[llength $calleeHandle] > 1} {
        ::sth::sthCore::processError returnKeyedList "STC only supports one-to-one call" {}
        return -code error $returnKeyedList 
    }
    
    return $calleeHandle
}
    
proc ::sth::sip::isRemoteUserNameMatched {sipHandle} {
    variable userArgsArray
    
    set usernamePrefix "%u"
    set usernameSuffix 0
    set usernameStep 1
    
    if {![info exists userArgsArray(remote_username_prefix)]} {
        ::sth::sthCore::processError returnKeyedList "-remote_username_prefix should be set to enable remote subscribers
            when SIP call is established through SIP server." {}
        return -code error $returnKeyedList
    } else {
        set usernamePrefix "$userArgsArray(remote_username_prefix)$usernamePrefix"
    }
    
    if {[info exists userArgsArray(remote_username_suffix)]} {
        set usernameSuffix $userArgsArray(remote_username_suffix)
    }
    
    if {[info exists userArgsArray(remote_username_suffix_step)]} {
        set usernameStep $userArgsArray(remote_username_suffix_step)
    }
    
    #get the existing SIP UAs
    set hostList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]
    
    set calleeHandle ""
    foreach host $hostList {
        if {![isSipHandleValid $host]} {
            continue
        }
        if {$sipHandle == $host} {
            continue
        }
        set count [::sth::sthCore::invoke stc::get $host -devicecount]
        
        if {$count != $userArgsArray(count)} {
            ::sth::sthCore::processError returnKeyedList "STC only supports one-to-one call" {}
            return -code error $returnKeyedList 
        }
        
        set sipUaCfgHandle [::sth::sthCore::invoke stc::get $host -children-SipUaProtocolConfig]
        
        array set uaNumOpt [::sth::sthCore::invoke stc::get $sipUaCfgHandle "-UaNumFormat -UaNumStart -UaNumStep"]
        
        if {$usernamePrefix == $uaNumOpt(-uanumformat) && $usernameSuffix == $uaNumOpt(-uanumstart) \
                            && $usernameStep == $uaNumOpt(-uanumstep)} {
            append calleeHandle $host
        } 
    }
    
    if {[llength $calleeHandle] > 1} {
        ::sth::sthCore::processError returnKeyedList "STC only supports one-to-one call" {}
        return -code error $returnKeyedList 
    }
    
    return $calleeHandle
}

#to check if the handle is valid SIP host Handle or not
proc ::sth::sip::isSipHandleValid { handle } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
	
    set cmdStatus 0
        
    if {[catch {set hostHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} err]} {
        ::sth::sthCore::log error "No host exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return $FAILURE
    } else {
	foreach hostHandle $hostHandleList {
	    if {[string equal $hostHandle $handle]} {
		set cmdStatus 1
		break
	    }
	}
		
        if {[catch {set sipUaCfgHandle [::sth::sthCore::invoke stc::get $hostHandle -children-SipUaProtocolConfig]} err]} {
	    set cmdStatus 0
	}
        
        if {[string length $sipUaCfgHandle] == 0} {
            set cmdStatus 0
        }

	if {$cmdStatus == 1} {
	    return $SUCCESS
	} else {
	    set errorMsg "Value ($handle) is not a valid SIP host handle"
	    return $FAILURE		
	}		
    }
}


proc ::sth::sip::getStcOptionValueList {cmdType modeFunc mode procFuncHandle} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in sipTable.tcl
    foreach item $::sth::sip::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::sip:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::sip:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::sip:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::sip:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::sip:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::sip:: $cmdType $opt $::sth::sip::userArgsArray($opt)} value]} {
        				lappend optionValueList -$stcAttr $value
        			} else {
        			    lappend optionValueList -$stcAttr $::sth::sip::userArgsArray($opt)
        			}
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::sip::userArgsArray($opt)]
                }
            }
        }
    }
    return $optionValueList
}
