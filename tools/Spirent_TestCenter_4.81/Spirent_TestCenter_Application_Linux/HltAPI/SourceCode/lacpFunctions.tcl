# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth::Lacp:: {
    set createResultQuery 0
    array set protocolStartFlag {}
}
proc ::sth::Lacp::emulation_lag_config_create { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lag_config"
    set _hltCmdName "emulation_lag_config_enable"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
     
    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    # detach ports before config lag port 
    set port_list ""
    if { [info exists switchToValue(port_handle)]} {
        set port_list $switchToValue(port_handle)
        ::sth::sthCore::invoke stc::perform detachports -portlist $port_list
    }

    ##lag info
    if {[info exists switchToValue(aggregatorresult)]} {
       set portoptions  [::sth::sthCore::invoke stc::get project1 -children-portoptions]
       ::sth::sthCore::invoke stc::config $portoptions -AggregatorResult $switchToValue(aggregatorresult)
    } 
    set attrList ""
    set port_name ""
    if {[info exists switchToValue(lag_name)]} {
       append attrList " -name $switchToValue(lag_name)"
       set port_name $switchToValue(lag_name)
    } 
    if {[info exists switchToValue(transmit_algorithm)]} {
       append attrList " -TransmitAlgorithm $switchToValue(transmit_algorithm)"
    } 
    if {[info exists switchToValue(l2_hash_option)]} {
       append attrList " -L2HashOption $switchToValue(l2_hash_option)"
    }
    if {[info exists switchToValue(l3_hash_option)]} {
       append attrList " -L3HashOption $switchToValue(l3_hash_option)"
    }

    if {[catch {set lagPort [::sth::sthCore::invoke stc::create Port -under project1]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not create lagPort, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
    }
    if {$port_name ne ""} {
        if {[catch {::sth::sthCore::invoke stc::config $lagPort -name $port_name} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lag, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
        }
    }
    if {[catch {set lag [::sth::sthCore::invoke stc::create lag -under $lagPort]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not create lag on the port:lagPort, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
    }
    if {[catch {::sth::sthCore::invoke stc::config $lag $attrList} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lag, errMsg:$errMsg" {}
        set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
        return $returnKeyedList
    }

    if {[llength $port_list] > 0 } {
        foreach port_handle $port_list {
            if { ![::sth::sthCore::IsPortValid $port_handle errMsg]} {
                ::sth::sthCore::processError returnKeyedList $errMsg {}
                set cmdState $FAILURE
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
                return $returnKeyedList
            }
        }
    }
    if {[info exists switchToValue(protocol)] && [string equal -nocase $switchToValue(protocol)  "Lacp"]} {
        set attrList ""
        if {[info exists switchToValue(actor_system_priority)]} {
            append attrList " -ActorSystemPriority  $switchToValue(actor_system_priority)"
        } 
        if {[info exists switchToValue(actor_system_id)]} {
            append attrList " -ActorSystemId $switchToValue(actor_system_id)"        
        }
        if {[catch {set lacpGroup [::sth::sthCore::invoke stc::create LacpGroupConfig -under $lag]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not create LacpGroupConfig on lag:$lag, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $lacpGroup $attrList} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lacpConfigHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
        }
        
        set attrList ""
        if {[info exists switchToValue(port_handle)]} {
            append attrList " -portlist \"$switchToValue(port_handle)\""
        }
        if {[info exists switchToValue(lacp_actor_key)]} {
            append attrList " -ActorKey $switchToValue(lacp_actor_key)"
        }
        if {[info exists switchToValue(lacp_actor_key_step)]} {
            append attrList " -ActorKeyStep $switchToValue(lacp_actor_key_step)"
        }
        if {[info exists switchToValue(lacp_actor_port_number)]} {
            append attrList " -ActorPort $switchToValue(lacp_actor_port_number)"
        }
        if {[info exists switchToValue(lacp_actor_port_priority)]} {
            append attrList " -ActorPortPriority $switchToValue(lacp_actor_port_priority)"
        }
        if {[info exists switchToValue(lacp_actor_port_priority_step)]} {
            append attrList " -ActorPortPriorityStep $switchToValue(lacp_actor_port_priority_step)"
        }
        if {[info exists switchToValue(lacp_actor_port_step)]} {
            append attrList " -ActorPortStep $switchToValue(lacp_actor_port_step)"
        }
        if {[info exists switchToValue(lacp_activity)]} {
            append attrList " -LacpActivity $switchToValue(lacp_activity)"
        }
        if {[info exists switchToValue(lacp_timeout)]} {
            append attrList " -LacpTimeout $switchToValue(lacp_timeout)"
        }
        if {[info exists switchToValue(lacp_port_mac_addr)]} {
            append attrList " -PortMacAddress $switchToValue(lacp_port_mac_addr)"
        }
        if {[info exists switchToValue(lacp_port_mac_addr_step)]} {
            append attrList " -PortMacAddressStep $switchToValue(lacp_port_mac_addr_step)"
        }
        set attrList "LacpCreateLagCommand $attrList"
        if {[catch {::sth::sthCore::invoke stc::perform [set attrList]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform $attrList to LacpCreateLagCommand, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
            return $returnKeyedList
        }
        foreach port_handle $port_list {
            set lacpportconfig [::sth::sthCore::invoke stc::get $port_handle  -children-lacpportconfig]
            ::sth::sthCore::invoke stc::config $lacpportconfig -memberoflag-Targets $lacpGroup
            
        }
        # subscribe resultdataset
        if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Lacp:: LacpPortConfig LacpPortResults returnKeyedList]} {
	    ::sth::sthCore::processError returnKeyedList "Error subscribing the LACP result data set"
            set cmdState $FAILURE
            if {[llength $port_list] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
            }
	        return $returnKeyedList
        }
    }
    if {$port_list ne ""} {

        ::sth::sthCore::invoke stc::config $lag -PortSetMember-targets $port_list

      
    }
    set ::sth::Session::PORTHNDLIST($lagPort) [stc::get $lagPort -location]
    set ::sth::Session::PERPORTSTREAMCOUNTTOBEARPED($lagPort) 0
    set ::sth::Session::PORTLEVELARPSENDREQUEST($lagPort) 1
    set ::sth::Session::PORTLEVELARPDONE($lagPort) 0
    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    keylset returnKeyedList lag_handle $lagPort

    # attach ports after config lag port 
    if {[llength $port_list] > 0} {
        ::sth::sthCore::invoke stc::perform attachports -portlist $port_list -autoconnect true
    }
    return $returnKeyedList
    
    
}

proc ::sth::Lacp::emulation_lag_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lag_config"
    set _hltCmdName "emulation_lag_config_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    # detach ports before config lag port
    set memberPorts ""
    if {[info exists switchToValue(lag_handle)]} {
        set lagPortList $switchToValue(lag_handle)
        foreach eachLagPort $lagPortList {
            set lagInfo [::sth::sthCore::invoke stc::get $eachLagPort -children-lag]
            set memberPorts [::sth::sthCore::invoke stc::get $lagInfo -PortSetMember-Targets]
            }
     } elseif {[info exists switchToValue{port_handle}]} {
            set memberPorts $switchToValue(port_handle)
        }

    if {[llength $memberPorts] > 0 } {

        ::sth::sthCore::invoke stc::perform detachports -portlist $memberPorts
    }
    #delete switches which has default value but hasn't been input
    set userInputList ""
    for {set i 0} { $i < [expr [llength $userInput] / 2]} { incr i} {
        set index [expr {$i*2}]
        set nameNoDash [string range [lindex $userInput $index] 1 end]
        lappend userInputList $nameNoDash
    }
    #puts $userInputList
    foreach switchName [array names switchToValue] {
        if { [lsearch $userInputList $switchName] == -1} {
            unset switchToValue($switchName)
        }
    }
    if {[info exists switchToValue(aggregatorresult)]} {
       set portoptions  [::sth::sthCore::invoke stc::get project1 -children-portoptions]
       ::sth::sthCore::invoke stc::config $portoptions -AggregatorResult $switchToValue(aggregatorresult)
    } 
    if {![info exists switchToValue(lag_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -lag_handle is a mandatory switch." {}
        set cmdState $FAILURE
        if {[llength $memberPorts] > 0} {
            ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
        }
        return $returnKeyedList	
    }
    set port_lag_handle $switchToValue(lag_handle)
    if {[catch {set lag [::sth::sthCore::invoke stc::get $port_lag_handle -children-lag]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get lag from $port_lag_handle." {}
        set cmdState $FAILURE
        if {[llength $memberPorts] > 0} {
            ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
        }
        return $returnKeyedList
    }
    
    
    set attrList ""
    set port_name ""
    if {[info exists switchToValue(lag_name)]} {
       append attrList " -name $switchToValue(lag_name)"
       set port_name $switchToValue(lag_name)
    } 
    if {[info exists switchToValue(transmit_algorithm)]} {
       append attrList " -TransmitAlgorithm $switchToValue(transmit_algorithm)"
    } 
    if {[info exists switchToValue(l2_hash_option)]} {
       append attrList " -L2HashOption $switchToValue(l2_hash_option)"
    }
    if {[info exists switchToValue(l3_hash_option)]} {
       append attrList " -L3HashOption $switchToValue(l3_hash_option)"
    }
    if {$port_name ne ""} {
        if {[catch {::sth::sthCore::invoke stc::config $port_lag_handle -name $port_name} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lag, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $memberPorts] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
            }  
            return $returnKeyedList
        }
    }
    if {$attrList != "" } { 
        if {[catch {::sth::sthCore::invoke stc::config $lag $attrList} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lag, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $memberPorts] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
            }
            return $returnKeyedList
        }
    }
    set attrList ""
    if {[info exists switchToValue(actor_system_priority)]} {
        append attrList " -ActorSystemPriority  $switchToValue(actor_system_priority)"
    } 
    if {[info exists switchToValue(actor_system_id)]} {
        append attrList " -ActorSystemId $switchToValue(actor_system_id)"        
    }
    if {[catch {set lacpgroupConfigHandle [::sth::sthCore::invoke stc::get $lag -children-lacpgroupconfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -children-lacpgroupconfig from lag:$lag." {}
        set cmdState $FAILURE
        if {[llength $memberPorts] > 0} {
            ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
        }
        return $returnKeyedList
    }
    if { $lacpgroupConfigHandle == ""} {
        ::sth::sthCore::log debug " There is no LACP protocol on the lag , if want to configure the LACP protocol should give the protocol parameter."
        if {[info exists switchToValue(protocol)] && [string equal -nocase $switchToValue(protocol)  "Lacp"]} {
            if {[catch {set lacpgroupConfigHandle [::sth::sthCore::invoke stc::create LacpGroupConfig -under $lag]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not create LacpGroupConfig on lag:$lag, errMsg:$errMsg" {}
                set cmdState $FAILURE
                if {[llength $memberPorts] > 0} {
                    ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
                }
                return $returnKeyedList
            }
        }
    }
    
    if {$attrList != ""  && $lacpgroupConfigHandle != ""} { 
        if {[catch {::sth::sthCore::invoke stc::config $lacpgroupConfigHandle $attrList} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lag, errMsg:$errMsg" {}
            set cmdState $FAILURE
            if {[llength $memberPorts] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
            }
            return $returnKeyedList
        }
    }

    set attrList ""
    if {[info exists switchToValue(lacp_actor_key)]} {
        append attrList " -ActorKey $switchToValue(lacp_actor_key)"
    }
    if {[info exists switchToValue(lacp_actor_key_step)]} {
        append attrList " -ActorKeyStep $switchToValue(lacp_actor_key_step)"
    }
    if {[info exists switchToValue(lacp_actor_port_number)]} {
        append attrList " -ActorPort $switchToValue(lacp_actor_port_number)"
    }
    if {[info exists switchToValue(lacp_actor_port_priority)]} {
        append attrList " -ActorPortPriority $switchToValue(lacp_actor_port_priority)"
    }
    if {[info exists switchToValue(lacp_actor_port_priority_step)]} {
        append attrList " -ActorPortPriorityStep $switchToValue(lacp_actor_port_priority_step)"
    }
    if {[info exists switchToValue(lacp_actor_port_step)]} {
        append attrList " -ActorPortStep $switchToValue(lacp_actor_port_step)"
    }
    if {[info exists switchToValue(lacp_activity)]} {
        append attrList " -LacpActivity $switchToValue(lacp_activity)"
    }
    if {[info exists switchToValue(lacp_timeout)]} {
        append attrList " -LacpTimeout $switchToValue(lacp_timeout)"
    }
        
    if {[info exists switchToValue(lacp_port_mac_addr)]} {
        append attrList " -PortMacAddress $switchToValue(lacp_port_mac_addr)"
    }
    if {[info exists switchToValue(lacp_port_mac_addr_step)]} {
        append attrList " -PortMacAddressStep $switchToValue(lacp_port_mac_addr_step)"
    }

    if {[catch {set port_handle [::sth::sthCore::invoke stc::get $lag -PortSetMember-targets]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -PortSetMember-targets from lag:$lag_handle." {}
        set cmdState $FAILURE
        if {[llength $memberPorts] > 0} {
            ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
        }
        return $returnKeyedList
    }
    if { $port_handle != "" && $attrList != "" } {
       if {![info exists switchToValue(port_handle)]} {
            ## mean all ports that attach the lag hanlde will be modify
            set attrList "LacpCreateLagCommand -portlist \"$port_handle\" $attrList"
            if {[catch {::sth::sthCore::invoke stc::perform [set attrList]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not perform $attrList to LacpCreateLagCommand, errMsg:$errMsg" {}
                set cmdState $FAILURE
                if {[llength $memberPorts] > 0} {
                    ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
                }
                return $returnKeyedList
            }
        } else {
            foreach port $port_handle {
                if {[regexp -nocase $port $switchToValue(port_handle)]} {
                    set lacpportattr "LacpCreateLagCommand -portlist \"$port\" $attrList"
                    if {[catch {::sth::sthCore::invoke stc::perform [set lacpportattr]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Can not perform $attrList to LacpCreateLagCommand, errMsg:$errMsg" {}
                        set cmdState $FAILURE
                        if {[llength $memberPorts] > 0} {
                            ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
                        }
                        return $returnKeyedList
                    }
                }
            }
        }
    } else {
        if {$attrList != "" && [info exists switchToValue(port_handle)]} {
            set attrList "LacpCreateLagCommand -portlist \"$switchToValue(port_handle)\" $attrList"
            if {[catch {::sth::sthCore::invoke stc::perform LacpCreateLagCommand $attrList} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not perform $attrList to LacpCreateLagCommand, errMsg:$errMsg" {}
                set cmdState $FAILURE
                if {[llength $memberPorts] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
                }
                return $returnKeyedList
            }
            set port_list $switchToValue(port_handle)
            foreach port_handle $port_list {
                set lacpportconfig [::sth::sthCore::invoke stc::get $port_handle  -children-lacpportconfig]
                ::sth::sthCore::invoke stc::config $lacpportconfig -memberoflag-Targets $lacpgroupConfigHandle
            }
            # subscribe resultdataset
            if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Lacp:: LacpPortConfig LacpPortResults returnKeyedList]} {
	        ::sth::sthCore::processError returnKeyedList "Error subscribing the LACP result data set"
                set cmdState $FAILURE
                if {[llength $memberPorts] > 0} {
                ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
                }
	            return $returnKeyedList
            }
            ::sth::sthCore::invoke stc::config $lag -PortSetMember-targets $port_list
        } 

    }

    set cmdState $SUCCESS
    # attach  ports after config lag port 
    if {[llength $memberPorts] > 0} {
        ::sth::sthCore::invoke stc::perform attachports -portlist $memberPorts -autoconnect true
    }
    return $SUCCESS    
}

proc ::sth::Lacp::emulation_lag_config_enable { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lag_config"
    set _hltCmdName "emulation_lag_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(lag_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -lag_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    set port_lag_handle $switchToValue(lag_handle)
    if {[catch {set lag_handle [::sth::sthCore::invoke stc::get $port_lag_handle -children-lag]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get lag from $port_lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
     
    if {[catch {::sth::sthCore::invoke stc::config $lag_handle -active  true} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not enable $lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }	
    
    set cmdState $SUCCESS
    return $SUCCESS  
}

proc ::sth::Lacp::emulation_lag_config_disable { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lag_config"
    set _hltCmdName "emulation_lag_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(lag_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -lag_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    set port_lag_handle $switchToValue(lag_handle)
    if {[catch {set lag_handle [::sth::sthCore::invoke stc::get $port_lag_handle -children-lag]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get lag from $port_lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
     
    if {[catch {::sth::sthCore::invoke stc::config $lag_handle -active  false} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not disable $lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }	
    
    set cmdState $SUCCESS
    return $SUCCESS  
}




proc ::sth::Lacp::emulation_lag_config_delete { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lag_config"
    set _hltCmdName "emulation_lag_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(lag_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -lag_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    set port_lag_handle $switchToValue(lag_handle)
    if {[catch {set lag_handle [::sth::sthCore::invoke stc::get $port_lag_handle -children-lag]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get lag from $port_lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if {[catch {set lacpgroupConfigHandle [::sth::sthCore::invoke stc::get $lag_handle -children-lacpgroupconfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -children-lacpgroupconfig from lag:$lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpgroupConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on lag:$lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if {[catch {set port_handle [::sth::sthCore::invoke stc::get $lag_handle -PortSetMember-targets]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -PortSetMember-targets from lag:$lag_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $port_handle != ""} {
        foreach port $port_handle {
           set lacpportconfig [::sth::sthCore::invoke stc::get $port -children-lacpportconfig]
           if { $lacpportconfig != ""} {
                if {[catch {::sth::sthCore::invoke stc::delete $lacpportconfig } errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Can not delete $lacpportconfig , errMsg:$errMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
        
    }
    if { $lacpgroupConfigHandle != ""} {
        if {[catch {::sth::sthCore::invoke stc::delete $lacpgroupConfigHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not delete $lacpgroupConfigHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $port_lag_handle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not delete $port_lag_handle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $port_handle != ""} {
        ::sth::sthCore::invoke stc::perform  AttachPortsCommand  -PortList  $port_handle
        ::sth::sthCore::invoke stc::sleep 5
    }
    set cmdState $SUCCESS
    return $SUCCESS  
}




proc ::sth::Lacp::emulation_lacp_config_enable { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_config"
    set _hltCmdName "emulation_lacp_config_enable"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[info exists switchToValue(local_mac_addr)]} {
        if {[catch {set hostHdl [::sth::sthCore::invoke stc::get $port_handle -Children-Host]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-Host from port:$port_handle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {set ethiiIfHdl [::sth::sthCore::invoke stc::get $hostHdl -Children-EthIIIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-EthiiIf from $hostHdl, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $ethiiIfHdl "-SourceMac $switchToValue(local_mac_addr)"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config -SourceMac to $ethiiIfHdl, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::create LacpPortConfig -under $port_handle]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not create LacpPortConfig on port:$port_handle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
    }

    set attrList ""
    if {[info exists switchToValue(act_port_key)]} {
        append attrList " -ActorKey $switchToValue(act_port_key)"
    }
    if {[info exists switchToValue(act_lacp_port_priority)]} {
        append attrList " -ActorPortPriority $switchToValue(act_lacp_port_priority)"
    }
    if {[info exists switchToValue(act_port_number)]} {
        append attrList " -ActorPort $switchToValue(act_port_number)"
    }
    if {[info exists switchToValue(act_lacp_timeout)]} {
        append attrList " -LacpTimeout $switchToValue(act_lacp_timeout)"
    }
    if {[info exists switchToValue(lacp_activity)]} {
        append attrList " -LacpActivity $switchToValue(lacp_activity)"
    }
    if {[catch {::sth::sthCore::invoke stc::config $lacpConfigHandle $attrList} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lacpConfigHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }    
    
    set attrList ""
    if {[info exists switchToValue(act_system_priority)]} {
        append attrList " -ActorSystemPriority $switchToValue(act_system_priority)"
    }
    if {[info exists switchToValue(act_system_id)]} {
        append attrList " -ActorSystemId $switchToValue(act_system_id)"        
    }
    if { $attrList != ""} {
        if {[catch {set lacpGroupHandle [::sth::sthCore::invoke stc::create LacpGroupConfig -under $GBLHNDMAP(project) $attrList]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config create LacpGroupConfig on $GBLHNDMAP(project), errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $lacpConfigHandle "-MemberOfLag-Targets $lacpGroupHandle"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config -MemberOfLag-Targets to $lacpConfigHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    # subscribe resultdataset
    if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Lacp:: LacpPortConfig LacpPortResults returnKeyedList]} {
	    ::sth::sthCore::processError returnKeyedList "Error subscribing the LACP result data set"
            set cmdState $FAILURE
	    return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $SUCCESS
}




proc ::sth::Lacp::emulation_lacp_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_config"
    set _hltCmdName "emulation_lacp_config_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)

    #delete switches which has default value but hasn't been input
    set userInputList ""
    for {set i 0} { $i < [expr [llength $userInput] / 2]} { incr i} {
        set index [expr {$i*2}]
        set nameNoDash [string range [lindex $userInput $index] 1 end]
        lappend userInputList $nameNoDash
    }
    puts $userInputList
    foreach switchName [array names switchToValue] {
        if { [lsearch $userInputList $switchName] == -1} {
            unset switchToValue($switchName)
        }
    }

    if {[info exists switchToValue(local_mac_addr)]} {
        if {[catch {set hostHdl [::sth::sthCore::invoke stc::get $port_handle -Children-Host]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-Host from port:$port_handle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {set ethiiIfHdl [::sth::sthCore::invoke stc::get $hostHdl -Children-EthIIIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -Children-EthiiIf from $hostHdl, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $ethiiIfHdl "-SourceMac $switchToValue(local_mac_addr)"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not config -SourceMac to $ethiiIfHdl, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get enable -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set attrList ""
    if {[info exists switchToValue(act_port_key)]} {
        append attrList " -ActorKey $switchToValue(act_port_key)"
    }
    if {[info exists switchToValue(act_lacp_port_priority)]} {
        append attrList " -ActorPortPriority $switchToValue(act_lacp_port_priority)"
    }
    if {[info exists switchToValue(act_port_number)]} {
        append attrList " -ActorPort $switchToValue(act_port_number)"
    }
    if {[info exists switchToValue(act_lacp_timeout)]} {
        append attrList " -LacpTimeout $switchToValue(act_lacp_timeout)"
    }
    if {[info exists switchToValue(lacp_activity)]} {
        append attrList " -LacpActivity $switchToValue(lacp_activity)"
    }
    if {[catch {::sth::sthCore::invoke stc::config $lacpConfigHandle $attrList} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lacpConfigHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }    

    set attrList ""
    if {[info exists switchToValue(act_system_priority)]} {
        append attrList " -ActorSystemPriority $switchToValue(act_system_priority)"
    }
    if {[info exists switchToValue(act_system_id)]} {
        append attrList " -ActorSystemId $switchToValue(act_system_id)"        
    }
    if { $attrList != ""} {
        if {[catch {set lacpGroupHandle [::sth::sthCore::invoke stc::get $lacpConfigHandle -MemberOfLag-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not get -MemberOfLag-Targets from $lacpConfigHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $lacpGroupHandle == ""} {
            if {[catch {set lacpGroupHandle [::sth::sthCore::invoke stc::create LacpGroupConfig -under $GBLHNDMAP(project)]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config create LacpGroupConfig on $GBLHNDMAP(project), errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if {[catch {::sth::sthCore::invoke stc::config $lacpConfigHandle "-MemberOfLag-Targets $lacpGroupHandle"} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config -MemberOfLag-Targets to $lacpConfigHandle, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $lacpGroupHandle $attrList} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Can not config $attrList to $lacpGroupHandle, errMsg:$errMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList
        }
    }
    
    set cmdState $SUCCESS
    return $SUCCESS    
}

proc ::sth::Lacp::emulation_lacp_config_disable { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_config"
    set _hltCmdName "emulation_lacp_config_disable"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set lacpGroupHandle [::sth::sthCore::invoke stc::get $lacpConfigHandle -MemberOfLag-Targets]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -MemberOfLag-Targets from $lacpConfigHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { $lacpGroupHandle != ""} {
        if {[catch {::sth::sthCore::invoke stc::delete $lacpGroupHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not delete $lacpGroupHandle, errMsg:$errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $lacpConfigHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not delete $lacpConfigHandle, errMsg:$errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $SUCCESS  
}

proc ::sth::Lacp::emulation_lacp_control_start { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_control"
    set _hltCmdName "emulation_lacp_control_start"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

        if {[catch {::sth::sthCore::invoke stc::perform ProtocolStart -ProtocolList $lacpConfigHandle} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Can not perform ProtocolStart on $lacpConfigHandle, errMsg: $errMsg." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    
    set cmdState $SUCCESS
    return $SUCCESS     
}

proc ::sth::Lacp::emulation_lacp_control_stop { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_control"
    set _hltCmdName "emulation_lacp_control_stop"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform ProtocolStop -ProtocolList $lacpConfigHandle} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not perform ProtocolStop on $lacpConfigHandle, errMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $SUCCESS     
}

proc ::sth::Lacp::emulation_lacp_info_collect { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_info"
    set _hltCmdName "emulation_lacp_info_collect"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

    if {[catch {array set lacpPortConfigAttr [::sth::sthCore::invoke stc::get $lacpConfigHandle]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -ResultChild-Targets from LacpPortConfig:$lacpConfigHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set lacpPortResultsHdl $lacpPortConfigAttr(-children)
    
    if { $lacpPortResultsHdl == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP results has not been subscribed on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {array set lacpPortResultsAttr [::sth::sthCore::invoke stc::get $lacpPortResultsHdl]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $lacpPortResultsHdl, $eMsg"
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set modeValue ""
    if {[info exists switchToValue(mode)]} {
        set modeValue $switchToValue(mode)
    } else {
        set modeValue "aggregate"
    }

    set switchList [array names ::sth::Lacp::emulation_lacp_info_mode]
    set returnKeyName ""
    foreach switchName $switchList {
        if { $switchName == "port_handle" || $switchName == "mode" || $switchName == "action"} {
            continue
        }
        if { $modeValue != "aggregate"} {
            if {[info exist ::sth::Lacp::emulation_lacp_info_mode($switchName)]} {
                if {[expr [lsearch $::sth::Lacp::emulation_lacp_info_mode($switchName) "$modeValue"] > -1]} {
                    lappend returnKeyName $switchName
                }       
            } else {
                ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } else {
            lappend returnKeyName $switchName
        }

    }

    foreach returnKey $returnKeyName {
        set stcobj $::sth::Lacp::emulation_lacp_info_stcobj($returnKey)
        set stcattr $::sth::Lacp::emulation_lacp_info_stcattr($returnKey)
        
        if {[string equal $stcobj "_none_"]} {
                #do nothing, present for further update
        } else {
            if { [string equal $stcobj "LacpPortResults"]} {
                keylset returnKeyedList $returnKey $lacpPortResultsAttr(-$stcattr)
            } elseif { [string equal $stcobj "LacpPortConfig"]} {
                keylset returnKeyedList $returnKey $lacpPortConfigAttr(-$stcattr)
            } else {
                #do nothing, present for further update
            }
        }
    }
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Lacp::emulation_lacp_info_clear { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Lacp::switchToValue
    variable ::sth::GBLHNDMAP

    set _OrigHltCmdName "emulation_lacp_info"
    set _hltCmdName "emulation_lacp_info_clear"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    set errMsg ""
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    if { ![info exists switchToValue(port_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList	
    }
    
    if { ![::sth::sthCore::IsPortValid $switchToValue(port_handle) errMsg]} {
        ::sth::sthCore::processError returnKeyedList $errMsg {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set port_handle $switchToValue(port_handle)
    
    if {[catch {set lacpConfigHandle [::sth::sthCore::invoke stc::get $port_handle -Children-LacpPortConfig]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortConfig from port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if { $lacpConfigHandle == ""} {
        ::sth::sthCore::processError returnKeyedList "LACP was not enable on port:$port_handle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set lacpPortResultsHdl [::sth::sthCore::invoke stc::get $lacpConfigHandle -Children-LacpPortResults]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not get -Children-LacpPortResults from LacpPortConfig:$lacpConfigHandle." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform ResultsClearView -ResultList $lacpPortResultsHdl} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Can not perform ResultsClearView on $lacpPortResultsHdl." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set cmdState $SUCCESS
    return $SUCCESS
}
