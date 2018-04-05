# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

###/*! \file RsvpFunctions.tcl
###    \brief Procedure for RSVP Api
###    
###    This file contains the helper utilities and the special switch processing functions for the RSVP Api.
###*/
### namespace Rsvp {
###/*! \file Rsvp.tcl
###    \brief Sub Commands for RSVP
###    
###    This file contains the sub commands for Rsvp Api which will execute the rsvp commands. This sub commands will be directly at the next level of the main command.
###*/
package require Tclx

###/*! \namespace Rsvp
###\brief Rsvp Api
###
###This namespace contains the implementation for the Rsvp Api

###*/
### namespace Rsvp {

namespace eval ::sth::Rsvp:: {

###/*! \var RSVPSESSIONSFORPORT
### \brief Global Array for portHandles and RSVPRouters
###
###This array holds the handles for the RSVPRouter for a particular port
###
###Example
###\li \c 58 : \a 60 84 96
### 58 = Port
### 50, 84, 96 = RSVPRouterHandles
###
###*/
###array RSVPSESSIONSFORPORT;

#         array set RSVPSESSIONSFORPORT {}
#         
# ###/*! \var RSVPSESSIONHNDLIST
# ### \brief Global Array for RSVPRouters and RsvpTunnelHandle
# ###
# ###This array holds the RSVPSessionHandle and corresponding RsvpTunnelHandle
# ###There RSVPRouterHandle and RsvpTunnelHandle should have one to one mapping.
# ###Example
# ###\li \c 60 : \a 84     
# ### 60 = RSVPRouterHandle
# ### 84 = RsvpTunnelHandle
# ###
# ###*/
# ###array RSVPSESSIONHNDLIST;
#         array set RSVPSESSIONHNDLIST {}

        set createResultQuery 0
     
        array set EnableRecordRoute {}
                
                set greIpHeader ""
                variable ipv4Version 4
                set atmEncap 0
				set ::sth::Rsvp::rsvp_subscription_state 0
}



###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_create (str args)
###\brief Process \em -mode switch with value \em enable for emulation_rsvp_config cmd
###
###This procedure execute the emulation_rsvp_config command when the mode is create. It will create rsvp sessions based on the \em -count switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with rsvp handles
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_config_create (str args);
###

proc ::sth::Rsvp::emulation_rsvp_config_inactive { returnKeyedListVarName cmdStatusVarName } {
    
        ::sth::sthCore::log debug "Excuting Internal Sub command for: emulation_rsvp_config_inactive"
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable ::sth::Rsvp::switchToValue
        upvar 1 $returnKeyedListVarName returnKeyedList
        upvar 1 $cmdStatusVarName cmdState
        
        if {[info exists switchToValue(handle)]==0} {
            ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle for inactive mode." {}
            set cmdState $FAILURE
            return $returnKeyedList        
        }
        
        set  revpRouters $switchToValue(handle)

    foreach revpRouter $revpRouters {
        if {[catch {set rsvpRtrCfg [::sth::sthCore::invoke stc::get $revpRouter "-children-RsvpRouterConfig"]} error]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while geting RSVP Protocol handle. Error: $error" {}
                set cmdState $FAILURE
                return $returnKeyedList        
        }
        if {[catch {::sth::sthCore::invoke stc::config $rsvpRtrCfg "-Active FALSE -LocalActive FALSE"} error]} {
            ::sth::sthCore::processError returnKeyedList "Failed to inactive RSVP protocol: $error. Error: $error" {}
                set cmdState $FAILURE
                return $returnKeyedList        
        }
    }
        
    keylset returnKeyedList handle   $revpRouters
    keylset returnKeyedList handles $revpRouters
        set cmdState $SUCCESS
    set errOccured 0
    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvp_config_active { returnKeyedListVarName cmdStatusVarName } {
    
	::sth::sthCore::log debug "Excuting Internal Sub command for: emulation_rsvp_config_active "
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	variable ::sth::Rsvp::switchToValue
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	if {[info exists switchToValue(handle)]==0} {
	    ::sth::sthCore::processError returnKeyedList "Error: Missing a mandatory attribute -handle for active mode." {}
	    set cmdState $FAILURE
	    return $returnKeyedList        
	}
	
	set  revpRouters $switchToValue(handle)

    foreach revpRouter $revpRouters {
        if {[catch {set rsvpRtrCfg [::sth::sthCore::invoke stc::get $revpRouter "-children-RsvpRouterConfig"]} error]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while geting RSVP Protocol handle. Error: $error" {}
                set cmdState $FAILURE
                return $returnKeyedList        
        }
        if {[catch {::sth::sthCore::invoke stc::config $rsvpRtrCfg "-Active TRUE -LocalActive TRUE"} error]} {
            ::sth::sthCore::processError returnKeyedList "Failed to active RSVP protocol: $error. Error: $error" {}
                set cmdState $FAILURE
                return $returnKeyedList        
        }
    }
        
    keylset returnKeyedList handle   $revpRouters
    keylset returnKeyedList handles $revpRouters
        set cmdState $SUCCESS
    set errOccured 0
    return $SUCCESS
}


proc ::sth::Rsvp::emulation_rsvp_config_create { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_config_strattr
    variable ::sth::Rsvp::switchToValue
    variable ::sth::GBLHNDMAP
    variable ::sth::Rsvp::createResultQuery
        variable atmEncap

    set _OrigHltCmdName "emulation_rsvp_config"
    set _hltCmdName "emulation_rsvp_config_create"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    

    #Validate if the value of port_handle is valid
    if {[info exists switchToValue(port_handle)]} {
        #Validate the port_handle
        set portHandle $switchToValue(port_handle)
        set msg ""
        if {![::sth::sthCore::IsPortValid $portHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList        
        }
        
        if {[info exist switchToValue(vci)] || [info exist switchToValue(vpi)]} {
            set atmEncap 1
        } else {
            set atmEncap 0
        }
    
        if {(![info exists switchToValue(count)] || $switchToValue(count)== "")} {
            set rsvpSessionCnt 1
        } else {
            #@TODO: Have to add the vlanId Stuff
            set rsvpSessionCnt $switchToValue(count)
            array set defaulValueToStep {}
            set stepSwitchListPair {intf_ip_addr_step intf_ip_addr \
                                    neighbor_intf_ip_addr_step neighbor_intf_ip_addr \
                                    gateway_ip_addr_step gateway_ip_addr \
                                    }
            set defaulValueToStep(intf_ip_addr) "192.85.1.3"
            set defaulValueToStep(neighbor_intf_ip_addr) "192.85.1.3"
            set defaulValueToStep(gateway_intf_ip_addr) "192.85.1.3"
            
            set stepSwitchListPairWithMode {
                                vlan_id_mode vlan_id_step vlan_id vlan_outer_id_mode vlan_outer_id_step vlan_outer_id\
                                             }
            set defaulValueToStep(neighbor_intf_ip_addr) "1"
                    set stepAtmListPair {vci_step vci vpi_step vpi}
        }
     
        if {[info exists switchToValue(refresh_reduction)]} {
            if {!$switchToValue(refresh_reduction)} {
                set switchToValue(summary_refresh) 0
                set switchToValue(bundle_msgs) 0
            }
        }
       
        #setup global address/step/id params, put return value in 'device'
        if {[catch {set ret [set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]]} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
            return $returnKeyedList 
        }
        #setup ethernet mac address start
        if {[info exists ::sth::Rsvp::switchToValue(mac_address_start)]} { 
            set deviceSettings "-NextMac $::sth::Rsvp::switchToValue(mac_address_start)" 
            ::sth::sthCore::invoke stc::config $device $deviceSettings
        }
       
        #Process and create the RSVPSessions for number of counts specified by user.
        for {set i 0} {$i < $rsvpSessionCnt} {incr i} {
            ::sth::sthCore::log debug "Creating,Configuring and Starting RSVPSession number:$i (total count $rsvpSessionCnt)." 
            #process the user input and set the value of switches accordingly.        
            if {$i > 0} {
                ::sth::sthCore::log debug "Updating values of switches, if required, based on the step input to create RSVPSession number:$i."
                ::sth::sthCore::log debug "Updating intface address for ipVersion:4 for RSVPSession number:$i."
                foreach {stepVal addr} $stepSwitchListPair {
                    if {[::info exists switchToValue($stepVal)]} {
                        if {[::info exists switchToValue($addr)]} {
                            set newIpAddress [::sth::sthCore::updateIpAddress 4 $switchToValue($addr) $switchToValue($stepVal) 1]
                            ::sth::sthCore::log Internalcall "RSVPSession:$i The new Ipv4 Value for $addr is $newIpAddress."
                            set switchToValue($addr) $newIpAddress
                            if {$switchToValue($addr)==""} {
                                sth::sthCore::log warn "WARN: Could not succesfully update the $addr switch."
                            }
                        } else {
                            set newIpAddress [::sth::sthCore::updateIpAddress 4 $defaulValueToStep($addr) $switchToValue($stepVal) 1]
                            ::sth::sthCore::log Internalcall "RSVPSession:$i The new Ipv4 Value for $addr is $newIpAddress."
                            if {![::sth::sthCore::updateUserInput "userInput" 1 "-$addr" $newIpAddress]} {
                                sth::sthCore::log warn "_INT_WARN: Could not succesfully update the $addr switch."
                            }
                        }
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Dependent switches -$stepVal for switch -$addr is/are not specified correctly or missing." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                }
                ::sth::sthCore::log Internalcall "RSVPSession:$i Check the status of other step switches."
                foreach {stepMode switchToBeStepped stepSwitch} $stepSwitchListPairWithMode {
                    ::sth::sthCore::log Internalcall "RSVPSession:$i Checking switch $stepMode : $switchToBeStepped : $stepSwitch."
                    if {[::info exists switchToValue($stepMode)]} {
                        ::sth::sthCore::log Internalcall "RSVPSession:$i Switch found in user input. Now checking the value:$switchToValue($stepMode) against increment"
                        if {[string equal $switchToValue($stepMode) "increment"]} {
                            if {[::info exists switchToValue($stepSwitch)]} {
                                if {[::info exists switchToValue($switchToBeStepped)]} {
                                    #update the value fo the switch with the specified stepValue
                                    set newSwitchToBeSteppedValue ""
                                    if {![::sth::Rsvp::stepSwitchValue $switchToValue($switchToBeStepped) $switchToValue($stepSwitch) 1 newSwitchToBeSteppedValue]} {
                                        ::sth::sthCore::log error "Error occured while stepping the value of switch:$switchToBeStepped"
                                    }
                                    #    tk_messageBox -message "$stepSwitch = $newSwitchToBeSteppedValue"
                                    ::sth::sthCore::log Internalcall "RSVPSession:$i The new Value for $switchToBeStepped is $newSwitchToBeSteppedValue."
                                    set switchToValue($stepSwitch) $newSwitchToBeSteppedValue
                                    if {$switchToValue($switchToBeStepped)==""} {
                                        ::sth::sthCore::log error "_INT_ERROR: Could not succesfully update the $switchToBeStepped switch."
                                    }
                                } else {
                                    #update the value fo the switch with the specified stepValue
                                    set newSwitchToBeSteppedValue ""
                                    if {![::sth::Rsvp::stepSwitchValue $defaulValueToStep($switchToBeStepped) $switchToValue($stepSwitch) $i newSwitchToBeSteppedValue]} {
                                        ::sth::sthCore::log error "Error occured while stepping the value of switch:$switchToBeStepped"
                                    }
                                    ::sth::sthCore::log Internalcall "RSVPSession:$i The new Value for $switchToBeStepped is $newSwitchToBeSteppedValue."
                                    set switchToValue($stepSwitch) $newSwitchToBeSteppedValue
                                    if {$switchToValue($switchToBeStepped)==""} {
                                        ::sth::sthCore::log error "_INT_ERROR: Could not succesfully update the $switchToBeStepped switch."
                                    }
                                }
                            } else {
                                ::sth::sthCore::processError returnKeyedList "Dependent switches -$stepSwitch for switch -$switchToBeStepped is/are not specified correctly or missing." {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                            }
                        }
                    }
                } ;#end foreach
                                
                if {$atmEncap == 1} {
                    foreach {stepVal atmAttr} $stepAtmListPair {
                        if {[info exist switchToValue($atmAttr)]} {
                            if {[info exist switchToValue($stepVal)]} {
                                set newValue [expr {$switchToValue($atmAttr) + $switchToValue($stepVal)}]
                                set switchToValue($atmAttr) $newValue
                            }
                        }
                    }
                }
            } ;#end if
            
            #Execute the createConfigStartRsvpSession cmd and check result.
            set cmdFailed 1
            ::sth::Rsvp::createConfigStartRsvpSession returnKeyedList cmdFailed $i
            if {$cmdFailed} {
                ::sth::sthCore::log error "Error occured while creating/configuring the RSVPSession number $i "
                set cmdState $FAILURE
            } else {
                ::sth::sthCore::log Internalcall "Successfully created/configured/started the RSVPSession number {$i} $returnKeyedList "
            }
        } ;#end foreach
    } elseif {[info exists switchToValue(handle)]} {
     foreach hname {vlan_cfi  cfi intf_ip_addr gateway_ip_addr intf_prefix_length user_priority vci vlan_id vpi vlan_id_mode  vlan_user_priority vlan_outer_id vlan_outer_id_mode vlan_outer_user_priority} {
            if {[info exists switchToValue($hname)]} {
                unset switchToValue($hname)
            }
        }
        #puts "Please be noted RSVP will be enable in the Device $switchToValue(handle)"
        if {[info exists switchToValue(refresh_reduction)]} {
            if {!$switchToValue(refresh_reduction)} {
                set switchToValue(summary_refresh) 0
                set switchToValue(bundle_msgs) 0
            }
        }
        #Execute the createConfigStartRsvpSession cmd and check result.
        set cmdFailed 1
    set idx 0
    set rtrHandles $switchToValue(handle)
    foreach rtrHandle $rtrHandles {
        set switchToValue(handle) $rtrHandle
        if {[::sth::sthCore::invoke stc::get $rtrHandle -children-RsvpRouterConfig] != ""} {
            ::sth::sthCore::processError returnKeyedList "$rtrHandle already has RSVP enable" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Rsvp::createConfigStartRsvpSession returnKeyedList cmdFailed $idx
        incr idx
        if {[info exists switchToValue(neighbor_intf_ip_addr_step)]} {set switchToValue(neighbor_intf_ip_addr) [::sth::sthCore::updateIpAddress 4 $switchToValue(neighbor_intf_ip_addr)  $switchToValue(neighbor_intf_ip_addr_step) 1]}
            
    }
        if {$cmdFailed} {
            ::sth::sthCore::log error "Error occured while creating/configuring the RSVPSession"
            set cmdState $FAILURE
        } else {
            ::sth::sthCore::log Internalcall "Successfully created/configured/started the RSVPSession $returnKeyedList "
        }
    } else {
        ::sth::sthCore::processError returnKeyedList "The switch -port_handle or handle is needed when mode is create." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    if {$cmdFailed > 0} {

    } else {    
        set cmdState $SUCCESS
        return $returnKeyedList
    }

}


proc ::sth::Rsvp::emulation_rsvp_config_activate {returnKeyedListVarName cmdStatusVarName} {

    upvar returnKeyedList returnKeyedList
    upvar cmdStatusVarName cmdState

    array set mainDefaultAry {}
    set opList "bfd_registration min_label_value max_label_value egress_label_mode dut_ip_addr dut_ip_addr_step use_gateway_as_dut_ip_addr"
    foreach key $opList {
        if {[info exists ::sth::Rsvp::emulation_rsvp_config_default($key)]} {
            set value $::sth::Rsvp::emulation_rsvp_config_default($key)
            set mainDefaultAry($key) $value
        }
    }
    
    if {[::sth::sthCore::IsInputOpt dut_ip_addr_step ] || [::sth::sthCore::IsInputOpt dut_ip_addr]} {
        set mainDefaultAry(use_gateway_as_dut_ip_addr) "true"
    }

    set mOptionList ""
    foreach idx [array names mainDefaultAry] {
        if {[info exists ::sth::Rsvp::switchToValue($idx)]} {
            if {[info exists ::sth::Rsvp::emulation_rsvp_config_$idx\_fwdmap($::sth::Rsvp::switchToValue($idx))]} {
                set value [set ::sth::Rsvp::emulation_rsvp_config_$idx\_fwdmap($::sth::Rsvp::switchToValue($idx))]
                set ::sth::Rsvp::switchToValue($idx) $value
            }
            set mainDefaultAry($idx) $::sth::Rsvp::switchToValue($idx)
        }
        if {[string equal $mainDefaultAry($idx) "_none_"]} { continue }
        regsub -all {[.]} [set ::sth::Rsvp::emulation_rsvp_config_stcattr($idx)] "" stcAttr
		#special handling for remote_as remote_as_step
		if {[string equal $stcAttr DutAsNum] ||
			[string equal $stcAttr DutAsNumStep]} {
			regsub -all {DutAsNum} $stcAttr "DutAs" stcAttr
		}
		
        append mOptionList " -$stcAttr $mainDefaultAry($idx)"
    }
        
    if {![info exists ::sth::Rsvp::switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the activate mode of emulation_rsvp_config" {}
	    keylset returnKeyedList status $::sth::sthCore::FAILURE
	    set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    } else {
	    set RsvpenHnd [::sth::sthCore::invoke stc::create RsvpDeviceGenProtocolParams -under $::sth::Rsvp::switchToValue(handle) $mOptionList]

        if {[::sth::sthCore::IsInputOpt expand] && $::sth::Rsvp::switchToValue(expand) == "false"} {
            keylset returnKeyedList handle_list ""
	        keylset returnKeyedList handle ""
	        keylset returnKeyedList handles ""
        } else {
            array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $::sth::Rsvp::switchToValue(handle)]
	        keylset returnKeyedList handle $return(-ReturnList)
	        keylset returnKeyedList handles $return(-ReturnList)
	        keylset returnKeyedList handle_list $return(-ReturnList)
                
            foreach hnd $return(-ReturnList) {
                set ::sth::Rsvp::EnableRecordRoute($hnd) $::sth::Rsvp::switchToValue(record_route)
                if {$mainDefaultAry(use_gateway_as_dut_ip_addr) == "true"} {
                        set rsvpHnd [::sth::sthCore::invoke stc::get $hnd -children-rsvprouterconfig]
                        set ipv4Hnd [::sth::sthCore::invoke stc::get $hnd -children-ipv4if]
                        ::sth::sthCore::invoke stc::config $rsvpHnd -dutipaddr [::sth::sthCore::invoke stc::get $ipv4Hnd -gateway]
                }
            }
        }
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}



###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_modify (str args)
###\brief Process \em -mode switch with value \em modify for emulation_rsvp_config cmd
###
###This procedure executes the emulation_rsvp_config command when the mode is modify.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for p2
###*/
###
###emulation_rsvp_config_modify (str args);
###

proc ::sth::Rsvp::emulation_rsvp_config_modify { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_config_procfunc
    variable ::sth::Rsvp::emulation_rsvp_configFunctionPriority
    variable ::sth::Rsvp::switchToValue
        variable atmEncap
    set _OrigHltCmdName "emulation_rsvp_config"
    set _hltCmdName "emulation_rsvp_config_modify"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    #Validate if the value of rsvp_handle is valid
    
    if {(![info exists switchToValue(handle)] || $switchToValue(handle) == "")} {
        ::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set rsvpRouterHandle $switchToValue(handle)
        #Validate the rsvp_handle
        ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
        set msg ""
        if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle msg]} {
             ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList         
        } else {
            set rsvpSessionHandle $msg
        }
    }
    if {[info exists switchToValue(refresh_reduction)]} {
        if {!$switchToValue(refresh_reduction)} {
            set switchToValue(summary_refresh) 0
            set switchToValue(bundle_msgs) 0
        }
    }
    #initializing the cmd specific data, validating switches and user input for each switch
    # ::sth::sthCore::cmdInit

        #get the lower layer stack, ethernet or ATM, which are exclusive.
        #modified by xiaozhi, 5/13/09
        
        if {$atmEncap == 0} { 
            #Modify the mac addr in the ethernet stack
            if {[catch {set ret [set ethernetstack [::sth::sthCore::invoke stc::get $rsvpRouterHandle -children-ethiiif]]} error]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
                return -code error $returnKeyedList
            }
            if {[info exists switchToValue(mac_address_start)] == 1} {
                set ethifSettings "-SourceMac $switchToValue(mac_address_start)"
                ::sth::sthCore::invoke stc::config $ethernetstack $ethifSettings
            }
        } else {
            #argments that can not modified under ATM encapsulation
            set atmUnsupportedModifyOptions {mac_address_start vlan_id vlan_outer_id tunnel_handle}
            foreach opt $atmUnsupportedModifyOptions {
                if {[info exist switchToValue($opt)]} {
                    ::sth::sthCore::processError returnKeyedList "-$opt can not modifed in ATM encapsulation." {}
                    return -code error $returnKeyedList 
                }
            }
        }
        
    #Configure the modify RsvpSession with user input (options)
    sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
        
    set cmdPass 1
    set priorityList [::sth::Rsvp::processSwitches emulation_rsvp_config ::sth::Rsvp:: returnKeyedList modify funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        if {[string equal $functionName "processConfigCmd"]} {
            set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_config $funcSwitchArray($functionName) $rsvpSessionHandle]
        } else {
            set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_config $funcSwitchArray($functionName) $rsvpRouterHandle]
        }
        if {$cmdPass <= 0} {
            break
        }
    }
    if {$atmEncap == 0} { 
            #modify the gre
            if {[info exists switchToValue(tunnel_handle)] == 1} {
                set cmdPass [::sth::configGreStack $switchToValue(tunnel_handle) $rsvpRouterHandle]
            }
        }
        
        #enable/disable BFD
        if {[info exists switchToValue(bfd_registration)]} {
            configBfdRegistration $rsvpRouterHandle $switchToValue(mode)
        }
        
    if {$cmdPass <= 0} {
        ::sth::sthCore::log error "Error configuring RSVPSession:$rsvpHandle "
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while modifying RsvpSession:$rsvpHandle" {}
        set cmdState $FAILURE
        return $returnKeyedList 
    } else {
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_delete (str args)
###\brief Process \em -mode switch with value \em delete for emulation_rsvp_config cmd
###
###This procedure execute the emulation_rsvp_config command when the mode is delete. It will delete all rsvp sessions based on the port_handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_config_delete (str args);
###

proc ::sth::Rsvp::emulation_rsvp_config_delete { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_config_procfunc
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_config"
    set _hltCmdName "emulation_rsvp_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set cmdFailed 0
    if {!([info exist switchToValue(port_handle)] || [info exist switchToValue(handle)])} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList            
    } else {
         if {[set portHandleExist [info exist switchToValue(port_handle)]]} {
                set portHandle $switchToValue(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
             return $returnKeyedList         
            } 
         } elseif {[info exist switchToValue(handle)]} {
            set rsvpRouterHandle $switchToValue(handle)
            #Validate the rsvp_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle msg]} {
              ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -handle ." {}
             set cmdState $FAILURE
             return $returnKeyedList         
            }            
         }
    }
    
    if ($portHandleExist) {    
        if {[catch {set routerList [::sth::sthCore::invoke stc::get $portHandle -affiliationport-Sources]} getStatus]} {
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while getting routers under port $portHandle. Error: $getStatus" {}
        } else {
            set rsvpRoutersList [list]
            set rsvpSessionList [list]
            #tk_messageBox -message $routerList
            foreach router $routerList {
                if {[::sth::Rsvp::IsRsvpSessionHandleValid $router eMsg]} {
                    lappend rsvpRoutersList $router
                    lappend rsvpSessionList $eMsg
                }
            }
            #tk_messageBox -message $rsvpRoutersList
            foreach rsvpSessionHandle $rsvpSessionList {
                #Call delete on all routers
                if {[catch {::sth::sthCore::invoke stc::delete $rsvpSessionHandle} eMsg ]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting RSVP router $rsvpRouterHandle. Error: $eMsg" {}        
                }
            }
            foreach rsvpRouterHandle $rsvpRoutersList {
                #Call delete on all routers
                if {[catch {::sth::sthCore::invoke stc::delete $rsvpRouterHandle} eMsg ]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
                }
            }
        }
    } else {
        #delete rsvp session indicate in the session handle
        #find corresponding $portHandle
        if {![::sth::Rsvp::getRsvpPort $rsvpRouterHandle portHandle]} {
              ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -handle ." {}
             set cmdState $FAILURE
             return $returnKeyedList
        } else {
            if {[::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle eMsg]} {
                set rsvpSessionHandle $eMsg
                #Call delete on all routers and also unset all routeblk and n/w blks info
                if {[catch {::sth::sthCore::invoke stc::delete $rsvpSessionHandle} eMsg ]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting RSVP router $rsvpRouterHandle. Error: $eMsg" {}    
                }
                if {[catch {::sth::sthCore::invoke stc::delete $rsvpRouterHandle} eMsg ]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
                }
            }
        }
    }
    if {$cmdFailed > 0} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {    
        set cmdState $SUCCESS
        return $returnKeyedList 
    }
}
    
###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_control_start (str args)
###\brief Process \em -mode switch with value \em start for emulation_rsvp_control cmd
###
###This procedure execute the emulation_rsvp_control command when the mode is \em start. It will start rsvp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_control_start (str args);
###

proc ::sth::Rsvp::emulation_rsvp_control_start { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::rsvp_subscription_state
    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_start"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

#    set args $userInput
    #initializing the cmd specific data, validating switches and user input for each switch
#    ::sth::sthCore::cmdInit

    if {!([info exist switchToValue(port_handle)] || [info exist switchToValue(handle)])} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList            
    } else {
        if {[set portHandleExist [info exist switchToValue(port_handle)]]} {
            set portHandle $switchToValue(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            } 
            set rsvpHandle portHandle
         }
			
        if {[info exist switchToValue(handle)]} {
            set rsvpRouterHandle $switchToValue(handle)
            #Validate the rsvp_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
            set msg ""
                        set rsvpProtocolHandle ""
                        foreach rsvpRouterHdl $rsvpRouterHandle {
                                if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHdl rsvpProtocolHdl]} {
                                        ::sth::sthCore::processError returnKeyedList "The value $rsvpRouterHdl is not valid for the switch -handle ." {}
                                        set cmdState $FAILURE
                                        return $returnKeyedList         
                                }
                                set rsvpProtocolHandle [concat $rsvpProtocolHandle $rsvpProtocolHdl]
                        }
         }

    }
	
	if {$::sth::Rsvp::rsvp_subscription_state == 0} {
    # subscribe dataset
		if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Rsvp:: RsvpRouterConfig RsvpRouterResults returnKeyedList]} {
			::sth::sthCore::processError returnKeyedList "Error subscribing the Rsvp result data set"
			return $returnKeyedList
		}
		set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
		::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId RsvpRouterConfig -ResultClassId RsvpLspResults]
		::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
		#set ::sth::Rsvp::createResultQuery 1
		set ::sth::Rsvp::rsvp_subscription_state 1
    }
	
        #before start the protocol and device, restore the tunnels
    if {[info exists switchToValue(restore)]} {
            foreach tunnelHandle $switchToValue(restore) {
                set errMsg ""
                if {![::sth::Rsvp::ProcessTunnelRestore $tunnelHandle errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "the rsvp tunnel $tunnelHandle can not be Restore errMsg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList    
                }
            }
        }

    if ($portHandleExist) {
        if {[catch {set rsvpRouterList [::sth::sthCore::invoke stc::get $portHandle -affiliationport-Sources]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                Internal Command Error while getting routers from the port $portHandle. Error: $getStatus" {}
            return $FAILURE
        }
        
        set rsvpProtocolList [list]
        set tmpCount -1
        foreach rsvpRouterHandle $rsvpRouterList {
            incr tmpCount
            if {[::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
                lappend rsvpProtocolList $rsvpProtocolHandle
            } else {
                set rsvpRouterList [lreplace $rsvpRouterList $tmpCount $tmpCount]
                set tmpCount [expr $tmpCount-1]
            }
        }
        
        if {$tmpCount < 0} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* There are no RSVP routers under the port handle $portHandle" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList {$rsvpRouterList}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while starting RSVP routers $rsvpRouterList. Error: $eMsg" {}    
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList {$rsvpProtocolList}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while starting RSVP routers $rsvpRouterList. Error: $eMsg" {}            
            set cmdState $FAILURE
            return $returnKeyedList
        }
    } else {
        #Call start on rsvpSession Handle
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList {$rsvpRouterHandle}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while starting RSVP router $rsvpRouterHandle. Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList {$rsvpProtocolHandle}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while starting RSVP router $rsvpRouterHandle. Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
	set cmdState $SUCCESS    
    return $returnKeyedList


}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_control_stop (str args)
###\brief Process \em -mode switch with value \em stop for emulation_rsvp_control cmd
###
###This procedure execute the emulation_rsvp_control command when the mode is \em stop. It will start rsvp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_control_stop (str args);
###

proc ::sth::Rsvp::emulation_rsvp_control_stop { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_stop"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState


    # initializing the cmd specific data, validating switches and user input for each switch
    # ::sth::sthCore::cmdInit

    if {!([info exist switchToValue(port_handle)] || [info exist switchToValue(handle)])} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList            
    } else {
         if {[set portHandleExist [info exist switchToValue(port_handle)]]} {
                set portHandle $switchToValue(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            } 
            set rsvpHandle portHandle
         }

         if {[info exist switchToValue(handle)]} {
            set rsvpRouterHandle $switchToValue(handle)
            #Validate the rsvp_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
                ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            }            
         }

    }
    

    
    #Configure the start rsvp router with user input (options)
    sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"

        #before stop the protocol and device, tear down the tunnels
    if {[info exists switchToValue(teardown)]} {
            foreach tunnelHandle $switchToValue(teardown) {
                set errMsg ""
                if {![::sth::Rsvp::ProcessTunnelTearDown $tunnelHandle errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "the rsvp tunnel $tunnelHandle can not be teardown errMsg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList    
                }
            }
        }    
    
    if ($portHandleExist) {
        #stop all the router under the port
        if {[catch {set rsvpRouterList [::sth::sthCore::invoke stc::get $portHandle -affiliationport-Sources]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while getting routers from the port $portHandle. Error: $getStatus" {}
            return $FAILURE
        }
        
        set rsvpProtocolList [list]
        set tmpCount -1
        foreach rsvpRouterHandle $rsvpRouterList {
            incr tmpCount
            if {[::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
                lappend rsvpProtocolList $rsvpProtocolHandle
            } else {
                set rsvpRouterList [lreplace $rsvpRouterList $tmpCount $tmpCount]
                set tmpCount [expr $tmpCount-1]
            }
        }
        if {$tmpCount < 0} {
            ::sth::sthCore::processError returnKeyedList "There are no RSVP routers under the port handle $portHandle" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList {$rsvpProtocolList}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while stopping RSVP routers $rsvpRouterList. Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList {$rsvpRouterList}"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while stopping RSVP routers $rsvpRouterList. Error: $eMsg" {}            
            set cmdState $FAILURE
            return $returnKeyedList 
        }
    } else {
        #Call stop on rsvpSession Handle
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList $rsvpProtocolHandle"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while stopping RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList $rsvpRouterHandle"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while stopping RSVP router $rsvpRouterHandle. Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList 
        }
    }
    set cmdState $SUCCESS    
    return $returnKeyedList


}

##################################
#resume_hellos
##################################
proc ::sth::Rsvp::emulation_rsvp_control_resume_hellos { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_resume_hellos"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set rsvpRouterHandle $switchToValue(handle)
    }
     
    if {[catch {::sth::sthCore::invoke stc::perform RsvpResumeHellos -RouterList " $rsvpRouterHandle "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpResumeHellos RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS    
    return $returnKeyedList
}
##################################
#stop_hellos 
##################################
proc ::sth::Rsvp::emulation_rsvp_control_stop_hellos { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_stop_hellos"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set rsvpRouterHandle $switchToValue(handle)
    }
     
    if {[catch {::sth::sthCore::invoke stc::perform RsvpStopHellos -RouterList " $rsvpRouterHandle "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpStopHellos RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS    
    return $returnKeyedList
}


##################################
#restart_router  
##################################
proc ::sth::Rsvp::emulation_rsvp_control_restart_router { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_restart_router"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set rsvpRouterHandle $switchToValue(handle)
    }
      
    if {[catch {::sth::sthCore::invoke stc::perform RsvpRestartRouter -RouterList " $rsvpRouterHandle "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpStopHellos RSVP router $rsvpRouterHandle. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    set cmdState $SUCCESS    
    return $returnKeyedList
}

##################################
#initiate_make_before_break   
##################################
proc ::sth::Rsvp::emulation_rsvp_control_initiate_make_before_break { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_initiate_make_before_break"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set rsvpRouterHandle $switchToValue(handle)
    }
    
    set ingressTunnelHandles [::sth::sthCore::invoke stc::get $rsvpRouterHandle -children-RsvpIngressTunnelParams]
    if { $ingressTunnelHandles != "" } { 
        if {[catch {::sth::sthCore::invoke stc::perform RsvpInitiateMakeBeforeBreak -IngressTunnelList " $ingressTunnelHandles "} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpInitiateMakeBeforeBreak command. Error: $eMsg" {}            
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    set cmdState $SUCCESS    
    return $returnKeyedList
}


##################################
#graft_ingress   
##################################
proc ::sth::Rsvp::emulation_rsvp_control_graft_ingress { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_graft_ingress"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set subLspList $switchToValue(handle)
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform RsvpP2mPGraftIngressSubLsp -SubLspList " $subLspList "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpP2mPGraftIngressSubLsp command. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set cmdState $SUCCESS    
    return $returnKeyedList
}

##################################
#graft_egress    
##################################
proc ::sth::Rsvp::emulation_rsvp_control_graft_egress { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_graft_egress"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set subLspList $switchToValue(handle)
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform RsvpP2mPGraftEgressSubLsp -SubLspList " $subLspList "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpP2mPGraftEgressSubLsp command. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set cmdState $SUCCESS    
    return $returnKeyedList
}

##################################
#prune_ingress    
##################################
proc ::sth::Rsvp::emulation_rsvp_control_prune_ingress { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_prune_ingress"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set subLspList $switchToValue(handle)
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform RsvpP2mPPruneIngressSubLsp -SubLspList " $subLspList "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpP2mPPruneIngressSubLsp command. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set cmdState $SUCCESS    
    return $returnKeyedList
}

##################################
#prune_egress     
##################################
proc ::sth::Rsvp::emulation_rsvp_control_prune_egress { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_prune_egress"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exist switchToValue(handle)]} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set subLspList $switchToValue(handle)
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform RsvpP2mPPruneEgressSubLsp -SubLspList " $subLspList "} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while RsvpP2mPPruneEgressSubLsp command. Error: $eMsg" {}            
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set cmdState $SUCCESS    
    return $returnKeyedList
}




###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_control_restart (str args)
###\brief Process \em -mode switch with value \em restart for emulation_rsvp_control cmd
###
###This procedure execute the emulation_rsvp_control command when the mode is \em restart. It will re-start rsvp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_control_restart (str args);
###

proc ::sth::Rsvp::emulation_rsvp_control_restart { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::rsvp_subscription_state
    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvp_control_restart"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState


    #initializing the cmd specific data, validating switches and user input for each switch
    # ::sth::sthCore::cmdInit

    if {!([info exist switchToValue(port_handle)] || [info exist switchToValue(handle)])} {
         ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList            
    } else {
        if {[set portHandleExist [info exist switchToValue(port_handle)]]} {
            set portHandle $switchToValue(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            } 
            set rsvpHandle portHandle
        }
    
         if {[info exist switchToValue(handle)]} {
            set rsvpRouterHandle $switchToValue(handle)
            #Validate the rsvp_handle
            ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
                ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList         
            }            
        }

    }
    sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
	if {$::sth::Rsvp::rsvp_subscription_state == 0} {
		# subscribe resultdataset
		if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Rsvp:: RsvpRouterConfig RsvpRouterResults returnKeyedList]} {
			::sth::sthCore::processError returnKeyedList "Error subscribing the Rsvp result data set"
			return $returnKeyedList
		}

		set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
		::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId RsvpRouterConfig -ResultClassId RsvpLspResults]
		::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
		set ::sth::Rsvp::rsvp_subscription_state 1
	}

        #before start the protocol and device, restore the tunnels
    if {[info exists switchToValue(restore)]} {
            foreach tunnelHandle $switchToValue(restore) {
                set errMsg ""
                if {![::sth::Rsvp::ProcessTunnelRestore $tunnelHandle errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "the rsvp tunnel $tunnelHandle can not be Restore errMsg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList    
                }
            }
        }

    # restart the routers
    if ($portHandleExist) {
        if {[catch {set rsvpRouterList [::sth::sthCore::invoke stc::get $portHandle -affiliationport-Sources]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName * \
                Internal Command Error while getting routers from the port_handle $portHandle. Error: $getStatus" {}
            return $FAILURE
        }
        
        set rsvpProtocolList [list]
        set tmpCount -1
        foreach rsvpRouterHandle $rsvpRouterList {
            incr tmpCount
            if {[::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
                lappend rsvpProtocolList $rsvpProtocolHandle
            } else {
                set rsvpRouterList [lreplace $rsvpRouterList $tmpCount $tmpCount]
                set tmpCount [expr $tmpCount-1]
            }
        }
        if {$tmpCount < 0} {
            ::sth::sthCore::processError returnKeyedList "There are no RSVP routers under the port_handle $portHandle" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        foreach router $rsvpRouterList {
            if {[catch {set rsvprouterconfig [::sth::sthCore::invoke stc::get $router -children-rsvprouterconfig]} getStatus]} {
                ::sth::sthCore::log error "Unable to fetch rsvprouter Handle. Error: $getStatus"
            } 
            if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $rsvprouterconfig -EnableGracefulRestart]} getStatus]} {
                ::sth::sthCore::log error "Unable to fetch rsvprouterconfig Handle. Error: $getStatus"
            }
            if {$gracefulRestart} {
                if {[catch {::sth::sthCore::invoke stc::perform RsvpRestartRouter -RouterList $rsvprouterconfig} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Command Error while restarting RSVP router $rsvprouterconfig. Error: $eMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList 
                }
            } else {
                if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList {$router}"} eMsg ]} {
                    ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                        Internal Command Error while stopping RSVP handles: $router. Error: $eMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList 
                }
                if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList {$rsvpProtocolList}"} eMsg ]} {
                    ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                        Internal Command Error while stopping RSVP handles: $router. Error: $eMsg" {}        
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                if {[catch {::sth::sthCore::invoke "stc::sleep 5"} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                        Internal Command Error while sleeping for 5 sec. Error: $eMsg" {}
                    set cmdState $FAILURE
                }
                if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList {$router}"} eMsg ]} {
                    ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                        Internal Command Error while starting RSVP handles: $router. Error: $eMsg" {}        
                    set cmdState $FAILURE
                    return $returnKeyedList 
                }
                if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList {$rsvpProtocolList}"} eMsg ]} {
                    ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                        Internal Command Error while starting RSVP handles: $router. Error: $eMsg" {}        
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
        }
    } else {
        if {[catch {set rsvprouterconfig [::sth::sthCore::invoke stc::get $rsvpRouterHandle -children-rsvprouterconfig]} getStatus]} {
            ::sth::sthCore::log error "Unable to fetch rsvprouter Handle. Error: $getStatus"
        } 
        if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $rsvprouterconfig -EnableGracefulRestart]} getStatus]} {
            ::sth::sthCore::log error "Unable to fetch rsvprouterconfig Handle. Error: $getStatus"
        }
        if {$gracefulRestart} {
            if {[catch {::sth::sthCore::invoke stc::perform RsvpRestartRouter -RouterList $rsvprouterconfig} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Command Error while restarting RSVP router $rsvprouterconfig. Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
        } else {
            #Call start on rsvpSession Handle
            if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList $rsvpRouterHandle"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                    Internal Command Error while stopping RSVP handle: $rsvpRouterHandle. Error: $eMsg" {}        
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList $rsvpProtocolHandle"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                    Internal Command Error while stopping RSVP handle: $rsvpRouterHandle. Error: $eMsg" {}                
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {::sth::sthCore::invoke "stc::sleep 5"} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                    Internal Command Error while sleeping for 5 sec. Error: $eMsg" {}
                set cmdState $FAILURE
            }
            if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList $rsvpRouterHandle"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                    Internal Command Error while starting RSVP handle: $rsvpRouterHandle. Error: $eMsg" {}            
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList $rsvpProtocolHandle"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName* \
                    Internal Command Error while starting RSVP handle: $rsvpRouterHandle. Error: $eMsg" {}                
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    set cmdState $SUCCESS    
    return $returnKeyedList


}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_info_Generic (str args)
###\brief Process \em -mode switch with value \em stats,settings for emulation_rsvp_info cmd
###
###This procedure execute the emulation_rsvp_info command when the mode is stats or settings. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###
###\author Jeremy Chang (jchnag)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_info_Generic (str args);
###

proc ::sth::Rsvp::emulation_rsvp_info_Generic { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_info_stcattr
    variable ::sth::Rsvp::emulation_rsvp_info_procfunc
    variable ::sth::Rsvp::emulation_rsvp_info_mode
    variable ::sth::Rsvp::switchToValue
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set mode $switchToValue(mode)

    set _OrigHltCmdName "emulation_rsvp_info"
    set _hltCmdName "emulation_rsvp_info_$mode"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    if {[info exists switchToValue(handle)]} {
        set rsvpRouterHandle $switchToValue(handle)
        if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "The handle $rsvpRouterHandle is not a valid handle of RSVP router" {}
            return $returnKeyedList
        } else {
            set rsvpProtocolHandle $msg
            if {[catch {set rsvpResultsHandle [::sth::sthCore::invoke stc::get $rsvpProtocolHandle -children-RsvpRouterResults]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Cannot get the rsvpResultsHandle from the rsvp protocol handle $rsvpProtocolHandle" {}
                return $returnKeyedList
            }
        }
    } else {
        return $returnKeyedList
    }
    
    set functionList [list]
    
    foreach returnKey [array names emulation_rsvp_info_mode] {
        if {[string equal [lindex $emulation_rsvp_info_mode($returnKey) 0] $mode]} {
            set functionName $emulation_rsvp_info_procfunc($returnKey)
            if {($functionName != "" && ![string equal $functionName "_none_"])} {
                lappend listof$functionName $returnKey
                if {[llength [expr "\$listof$functionName"]] == 1} {
                    lappend functionList $functionName
                }
            }
        }
    }
    # tk_messageBox -message $functionList
    set cmdPass 1
    foreach functionName $functionList {
        set cmdPass [::sth::Rsvp::$functionName [expr "\$listof$functionName"] returnKeyedList $_hltCmdName [expr "\$listof$functionName"] $rsvpRouterHandle $rsvpProtocolHandle $rsvpResultsHandle]
        if {$cmdPass <= 0} {
            break
        }
    }
    
    #return key msg_tx and msg_rx in mode "stats", by Yulin Chen 27/03/08
    set rx_msg_count 0
    set tx_msg_count 0
    if {$cmdPass<=0} {
        break
    } else {
        if {[info exists switchToValue(mode)]} {
            set mode $switchToValue(mode)
            if {[string equal $mode "stats"]} {
                set rx_msg_type_list "RxPath RxReservation RxPathError RxReservationError RxReservationConfirmation RxReservationTeardown RxPathTeardown RxHello RxPathRecovery"
                set rx_msg_type_switch_list "egress_path_rx ingress_resv_rx egress_patherr_rx ingress_resverr_rx egress_resvconf_rx ingress_resvtear_rx egress_pathtear_rx hellos_rx"
                foreach rx_msg_type_switch $rx_msg_type_switch_list {
                    #set rx_msg_type_count [keylget $returnKeyedList $rx_msg_type_switch]
                    if {![keylget returnKeyedList $rx_msg_type_switch rx_msg_type_count]} {
                        ::sth::sthCore::processError returnKeyedList "Cannot get the value of $rx_msg_type_switch " {}
                        return $returnKeyedList
                    }
                    set rx_msg_count [expr $rx_msg_count + $rx_msg_type_count]
                }
                keylset returnKeyedList "msg_rx" $rx_msg_count
                
                set tx_msg_type_list "TxPath TxReservation TxPathError TxReservationError TxReservationConfirmation TxReservationTeardown TxPathTeardown TxHello TxPathRecovery"
                set tx_msg_type_switch_list "ingress_path_tx egress_resv_tx ingress_patherr_tx egress_resverr_tx ingress_resvconf_tx egress_resvtear_tx ingress_pathtear_tx hellos_tx"
                foreach tx_msg_type_switch $tx_msg_type_switch_list {
                    #set tx_msg_type_count [keylget $returnKeyedList $tx_msg_type_switch]
                    if {![keylget returnKeyedList $tx_msg_type_switch tx_msg_type_count]} {
                        ::sth::sthCore::processError returnKeyedList "Cannot get the value of $tx_msg_type_switch " {}
                        return $returnKeyedList
                    }
                    set tx_msg_count [expr  $tx_msg_count + $tx_msg_type_count]
                }
                keylset returnKeyedList "msg_tx" $tx_msg_count
                
            }
        }
    }

    if {$cmdPass <= 0} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::Rsvp::emulation_rsvp_tunnel_info_Generic { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_info_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_info_procfunc
    variable ::sth::Rsvp::emulation_rsvp_tunnel_info_mode
    variable ::sth::Rsvp::switchToValue
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _OrigHltCmdName "emulation_rsvp_tunnel_info"
    set _hltCmdName "emulation_rsvp_info_Generic"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"

    if {[info exists switchToValue(handle)]} {
        set rsvpRouterHandle $switchToValue(handle)
        if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpRouterConfig]} {
            ::sth::sthCore::processError returnKeyedList "The handle $rsvpRouterHandle is not a valid handle of RSVP router" {}
            set cmdPass 0
            return $returnKeyedList
        } 
    }

    set cmdPass 1
    set total_lsp_count 0 
    set inbound_lsp_count 0
    set outbound_lsp_count 0
    set outbound_up_count 0
    set outbound_down_count 0
    set outbound_connect_count 0
    set outbound_lsps "N/A" 

    set ingress_ip_collections ""
    set egress_ip_collections ""
    set source_collections ""
    set direction_collections ""
    set tunnel_id_collections ""
    set lsp_id_collections ""
    set label_collections ""

    #retrieve ingress tunnel
    if {[catch {set rsvpingresstunnelparams [::sth::sthCore::invoke stc::get $rsvpRouterConfig -children-rsvpingresstunnelparams]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error fetching rsvpingresstunnelparams from $rsvpRouterConfig." {}
        set cmdPass 0
        return $returnKeyedList
    }

    #retrieve egress tunnel
    if {[catch {set rsvpegresstunnelparams [::sth::sthCore::invoke stc::get $rsvpRouterConfig -children-rsvpegresstunnelparams]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error fetching rsvpegresstunnelparams from $rsvpRouterConfig." {}
        set cmdPass 0
        return $returnKeyedList
    }

    #retrieve router's tunnel results
    if {[catch {set rsvprouterresults [::sth::sthCore::invoke stc::get $rsvpRouterConfig -children-rsvprouterresults]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error fetching rsvprouterresults from $rsvpRouterConfig." {}
        set cmdPass 0
        return $returnKeyedList
    }
    ##getting outbound_down_count
    #if {[catch {stc::get -LspDownCount $rsvprouterresults outbound_down_count} getStatus]} {
    #    ::sth::sthCore::processError returnKeyedList "Error fetching LspDownCount from $rsvprouterresults." {}
    #    set cmdPass 0
    #    return $returnKeyedList
    #}
    ##getting outbound_up_count
    #if {[catch {stc::get -LspUpCount $rsvprouterresults outbound_up_count} getStatus]} {
    #    ::sth::sthCore::processError returnKeyedList "Error fetching LspUpCount from $rsvprouterresults." {}
    #    set cmdPass 0
    #    return $returnKeyedList
    #}
    ##getting outbound_connect_count
    #if {[catch {stc::get -LspConnectingCount $rsvprouterresults outbound_connect_count} getStatus]} {
    #    ::sth::sthCore::processError returnKeyedList "Error fetching LspConnectingCount from $rsvprouterresults." {}
    #    set cmdPass 0
    #    return $returnKeyedList
    #}
    
    if {[catch {set tempStr [::sth::sthCore::invoke stc::get $rsvprouterresults]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error fetching attributes from rsvprouterresults handle: $getStatus" {}
        set cmdPass 0
        return $returnKeyedList
    }
    
    array set routerResultArr $tempStr
    
    #getting outbound_down_count outbound_up_count outbound_connect_count
    set outbound_down_count $routerResultArr(-LspDownCount)
    set outbound_up_count $routerResultArr(-LspUpCount)
    set outbound_connect_count $routerResultArr(-LspConnectingCount)
    
    #summarize total lspCount from ingress tunnels
    foreach rsvptunnel $rsvpingresstunnelparams {
        if {[catch {set lspCount [::sth::sthCore::invoke stc::get $rsvptunnel -LspCount]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Error fetching LspCount from $rsvptunnel." {}
            set cmdPass 0
            return $returnKeyedList
        }
        set outbound_lsp_count [expr $outbound_lsp_count + $lspCount]
    }
    #summarize total lspCount from egress tunnels
    #foreach rsvptunnel $rsvpegresstunnelparams {
    #    if {[catch {stc::get -LspCount $rsvptunnel lspCount} getStatus]} {
    #        ::sth::sthCore::processError returnKeyedList "Error fetching LspCount from $rsvptunnel." {}
    #        set cmdPass 0
    #        return $returnKeyedList
    #    }
    #    set inbound_lsp_count [expr $inbound_lsp_count + $lspCount]
    #}
    #stc now can only supply upped Egress lsp count
    set inbound_lsp_count $routerResultArr(-EgressLspUpCount)
        
    #add up total_lsp_count from ingress+egress tunnels
    set total_lsp_count [expr $inbound_lsp_count + $outbound_lsp_count]

    if {[catch {set rsvpLspResultList [::sth::sthCore::invoke stc::get $rsvpRouterConfig -children-rsvplspresults]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error fetching rsvplspresults from $rsvpRouterConfig." {}
        set cmdPass 0
        return $returnKeyedList
    }
    foreach rsvplspresult $rsvpLspResultList {

        set ingress_ip [::sth::sthCore::invoke stc::get $rsvplspresult -SrcIpAddr]
        lappend ingress_ip_collections $ingress_ip

        set egress_ip [::sth::sthCore::invoke stc::get $rsvplspresult -DstIpAddr]
        lappend egress_ip_collections $egress_ip

        set source [::sth::sthCore::invoke stc::get $rsvplspresult -SrcIpAddr]
        lappend source_collections $source

        set direction [::sth::sthCore::invoke stc::get $rsvplspresult -Direction]
        if {$direction == "RSVP_TUNNEL_INGRESS"} {
            lappend direction_collections "outbound" 
        } elseif {$direction == "RSVP_TUNNEL_EGRESS"} {
            lappend direction_collections "inbound" 
        }

        set tunnel_id [::sth::sthCore::invoke stc::get $rsvplspresult -TunnelId]
        lappend tunnel_id_collections $tunnel_id

        set lsp_id [::sth::sthCore::invoke stc::get $rsvplspresult -LspId]
        lappend lsp_id_collections $lsp_id

        set label [::sth::sthCore::invoke stc::get $rsvplspresult -Label]
        lappend label_collections $label

    }

    keylset returnKeyedList total_lsp_count [format "%d" $total_lsp_count]
    keylset returnKeyedList inbound_lsp_count [format "%d" $inbound_lsp_count]
    keylset returnKeyedList outbound_lsp_count [format "%d" $outbound_lsp_count]
    keylset returnKeyedList outbound_up_count $outbound_up_count
    keylset returnKeyedList outbound_down_count $outbound_down_count
    keylset returnKeyedList outbound_connect_count [format "%d" $outbound_connect_count]
    keylset returnKeyedList outbound_lsps $outbound_lsps

    keylset returnKeyedList ingress_ip $ingress_ip_collections
    keylset returnKeyedList egress_ip $egress_ip_collections
    keylset returnKeyedList source $source_collections
    keylset returnKeyedList direction $direction_collections
    keylset returnKeyedList tunnel_id $tunnel_id_collections
    keylset returnKeyedList lsp_id $lsp_id_collections
    keylset returnKeyedList label $label_collections

    if {$cmdPass <= 0} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}



###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_create (str args)
###\brief Process \em -mode switch with value \em enable for emulation_rsvp_tunnel_config cmd
###
###This procedure execute the emulation_rsvp_tunnel_config command when the mode is create. It will create rsvp sessions based on the \em -count switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with rsvp handles
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_tunnel_config_create (str args);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_create { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue


    set _OrigHltCmdName "emulation_rsvp_tunnel_config"
    set _hltCmdName "emulation_rsvp_tunnel_config_create"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState


    if {[info exists switchToValue(element_handle)]} {
        ::sth::Rsvp::configTunnelSubElements returnKeyedList cmdState
        return $returnKeyedList
    }

    #Validate if the value of session_handle is valid
    if {(![info exists switchToValue(handle)] || $switchToValue(handle)=="")} {
        ::sth::sthCore::processError returnKeyedList "$_OrigHltCmdName: The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList         
    } else {
        set rsvpRouterHandle $switchToValue(handle)
        #Validate the session_handle
        set msg ""
        if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
             ::sth::sthCore::processError returnKeyedList "$_OrigHltCmdName: \
                The value $rsvpRouterHandle is not valid for the switch -handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList        
        }
    }

    #make the value of "direction" switches same to "rsvp_behavior"
    if {[info exists switchToValue(rsvp_behavior)]} {
        if {[string equal $switchToValue(rsvp_behavior) "rsvpEgress"]} {
            set switchToValue(direction) "egress"
        } elseif {[string equal $switchToValue(rsvp_behavior) "rsvpIngress"]} {
            set switchToValue(direction) "ingress"
        } else {
    ::sth::sthCore::processError returnKeyedList "$_OrigHltCmdName: \
                The value of switch rsvp_behavior should be rsvpEgress or rsvpIngress." {}
        set cmdState $FAILURE
        return $returnKeyedList
        }
    }

# compare the value of -count and -tunnel_count, set the tunnel count as the lagrest number.
    set rsvpTunnelCnt "1" 
    if {[info exists switchToValue(count)] && $switchToValue(count) != ""} {
        set rsvpTunnelCnt $switchToValue(count)
    }
    if {[info exists switchToValue(tunnel_count)] && $switchToValue(tunnel_count) != "" } {
        if {$rsvpTunnelCnt > $switchToValue(tunnel_count) } {
            set switchToValue(tunnel_count) $rsvpTunnelCnt
        }
    } else {
        set switchToValue(tunnel_count) $rsvpTunnelCnt
    }
    
    #set stepSwitchList {egress_ip_step ingress_ip_step tunnel_id_step}
    #
    #if {(![info exists switchToValue(count)] || $switchToValue(count)=="")} {
    #    set rsvpTunnelCnt 1
    #} else {
        #@TODO: Have to add the vlanId Stuff
    #    set rsvpTunnelCnt $switchToValue(count)
        #array set defaulValueToStep {}
        #set stepIpSwitchListPair {egress_ip_step egress_ip_addr \
                                ingress_ip_step ingress_ip_addr \
                                }
        
        #set stepIntSwitchListPair {tunnel_id_step tunnel_id_start
        #                        } 
    #}

    # if the tunnel is egress, only the switches direction, handle, egress_ip_addr, egress_ip_step, ingress_ip_addr, ingress_ip_step,
    # tunnel_id_start, tunnel_id_step are kept.
    #fix a bug, set the egress source ip address as the value of -ingress_ip_addr.
    # remove -ingress_ip_addr from the egress switch list, and set the egress source ip address as the value of -egress_src_ip_addr.
    if {[string equal $switchToValue(direction) egress]} {
        set tmpList [list direction $switchToValue(direction) egress_ip_addr $switchToValue(egress_ip_addr) tunnel_id_start $switchToValue(tunnel_id_start) handle $switchToValue(handle)]
                #tunnel tail-end rsvp attributes
        set switchToValue(optional_args) [list \
                        -direction $switchToValue(direction) \
                        -egress_ip_addr $switchToValue(egress_ip_addr) \
                        -tunnel_id_start $switchToValue(tunnel_id_start) \
                        -handle $switchToValue(handle)]
        set rro_attribute_list [list rro rro_list_ipv4 rro_list_label rro_frr_merge_point rro_list_pfxlen rro_list_type]
        foreach item $rro_attribute_list {
                if {[info exists switchToValue($item)]} {
                        if {$switchToValue(rro) == 1 && $switchToValue(rro_list_type) == "ipv4"} {
                                switch -- $item {
                                        rro { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                        rro_list_ipv4 { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                        rro_list_label { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                        rro_list_pfxlen { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                        rro_frr_merge_point { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                        rro_list_type { lappend switchToValue(optional_args) -$item $switchToValue($item) } \
                                }
                        }
                }
        }
        # added tunnel_id_step and tunnel_count in egress switch list.
        set egressParams "egress_ip_step  tunnel_id_step tunnel_count \
                        egress_accept_any_tunnel_id egress_enable_notify_request egress_enable_point_to_multi_point egress_src_ip_addr egress_src_ip_addr_step \
                        gmpls_acceptable_label_set gmpls_acceptable_label_set_type gmpls_label gmpls_interface_id  gmpls_resv_src_ip_addr  gmpls_suggested_label gmpls_te_router_id  gmpls_use_upstream_label \
                        egress_resv_custom_object_list egress_resv_tear_custom_object_list"

        foreach tmpSwitchName $egressParams {
            if {[info exists switchToValue($tmpSwitchName)]} {
                lappend tmpList $tmpSwitchName $switchToValue($tmpSwitchName)
                lappend switchToValue(optional_args) -$tmpSwitchName $switchToValue($tmpSwitchName)
            }
        }

        lappend tmpList optional_args $switchToValue(optional_args) mandatory_args $switchToValue(mandatory_args)
        unset switchToValue
        array set switchToValue $tmpList
    }

    # 
    #Process and create the RSVP tunnels for number of counts specified by user.

    set rsvpIngressTunnelParamsList ""
    # fix US36836  config mulit tunnels as a tunnel block .
    #for {set i 0} {$i < $rsvpTunnelCnt} {incr i} {
    #    ::sth::sthCore::log Internalcall "Creating,Configuring and Starting RSVPSession number:$i." 
    #    #process the user input and set the value of switches accordingly.        
    #    if {$i > 0} {
    #        ::sth::sthCore::log Internalcall "Updating values of switches, if required, \
    #                            based on the step input to create RSVPSession number:$i."
    #        ::sth::sthCore::log Internalcall "Updating intface address for ipVersion:4 for RSVPSession number:$i."
    #        foreach {stepVal addr} $stepIpSwitchListPair {
    #            if {[::info exists switchToValue($stepVal)]} {
    #                set newIpAddress [::sth::sthCore::updateIpAddress 4 $switchToValue($addr) $switchToValue($stepVal) 1]
    #                ::sth::sthCore::log Internalcall "RSVPSession:$i The new Ipv4 Value for $addr is $newIpAddress."
    #                set switchToValue($addr) $newIpAddress
    #            } else {
    #                ::sth::sthCore::processError returnKeyedList "Dependent switches -$stepVal \
    #                                            for switch -$addr is/are not specified correctly or missing." {}
    #                set cmdState $FAILURE
    #               return $returnKeyedList
    #           }
    #        }
    #       foreach {stepVal switchVal} $stepIntSwitchListPair {
    #            if {[info exists switchToValue($stepVal)]} {
    #                set newSwitchVal [expr $switchToValue($switchVal) + ($switchToValue($stepVal) * 1)]
    #                ::sth::sthCore::log Internalcall "RSVPSession:$i The new value for $switchVal is $newSwitchVal."
    #                set switchToValue($switchVal) $newSwitchVal
    #            } else {
    #                ::sth::sthCore::processError returnKeyedList "Dependent switches -$stepVal for switch -$switchVal is/are not specified correctly or missing." {}
    #                set cmdState $FAILURE
    #                return $returnKeyedList        
    #            }
    #        }
    #    }
    #
    #    #Execute the createConfigStartRsvpTunnel cmd and check result.
    #    set cmdFailed 1
    #    ::sth::Rsvp::createConfigStartRsvpTunnel rsvpingresstunnelparams cmdFailed
    #    if {$cmdFailed} {
    #        ::sth::sthCore::log error "Error occured while creating/configuring the RSVPTunnel number $i "
    #        set cmdState $FAILURE
    #        return $returnKeyedList 
    #    } else {
    #        set rsvpIngressTunnelParamsList [concat $rsvpIngressTunnelParamsList [keylget rsvpingresstunnelparams tunnel_handle]]
    #        ::sth::sthCore::log Internalcall "Successfully created/configured the RSVPTunnel number {$i} $returnKeyedList "
    #    }
    # }

        set cmdFailed 1
        ::sth::Rsvp::createConfigStartRsvpTunnel rsvpingresstunnelparams cmdFailed
        if {$cmdFailed} {
            ::sth::sthCore::log error "Error occured while creating/configuring the RSVPTunnel number $i "
            set cmdState $FAILURE
            return $returnKeyedList 
        } else {
            set rsvpIngressTunnelParamsList [concat $rsvpIngressTunnelParamsList [keylget rsvpingresstunnelparams tunnel_handle]]
            ::sth::sthCore::log Internalcall "Successfully created/configured the RSVPTunnel ! "
        }
    
    if {[::info exists cmdError]} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {    
        set cmdState $SUCCESS
        keylset returnKeyedList tunnel_handle $rsvpIngressTunnelParamsList
        return $returnKeyedList
    }

}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_modify (str args)
###\brief Process \em -mode switch with value \em modify for emulation_rsvp_tunnel_config_modify cmd
###
###This procedure executes the emulation_rsvp_config command when the mode is modify.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_tunnel_config_modify (str args);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_modify { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::emulation_rsvp_tunnel_configFunctionPriority
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_tunnel_config"
    set _hltCmdName "emulation_rsvp_tunnel_config_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {[info exists switchToValue(element_handle)]} {
        ::sth::Rsvp::configTunnelSubElements returnKeyedList cmdState
        return $returnKeyedList
    }

    #Validate if the value of rsvp_handle is valid
    if {![info exists switchToValue(tunnel_pool_handle)]} {
        ::sth::sthCore::processError returnKeyedList "tunnel_pool_handle switch with valid value is not provided." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } 
    
    set rsvpHandleList $switchToValue(tunnel_pool_handle)
    
    set egressTunnelHandle [list]
    set ingressTunnelHandle [list]
    foreach rsvpHandle $rsvpHandleList {
        #Validate the rsvp_handle
        ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
        set msg ""
        if {![::sth::Rsvp::IsRsvpTunnelHandleValid $rsvpHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -tunnel_pool_handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList         
        }
        if {[string first "egress" [string tolower $rsvpHandle]] >= 0} {
            lappend egressTunnelHandle $rsvpHandle
        } else {
            lappend ingressTunnelHandle $rsvpHandle
        }
    }
    
    #initializing the cmd specific data, validating switches and user input for each switch
    # ::sth::sthCore::cmdInit
    #Configure the modify RsvpTunnel with user input (options)
    sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
        
    set cmdPass 1
    set priorityList [::sth::Rsvp::processSwitches emulation_rsvp_tunnel_config ::sth::Rsvp:: returnKeyedList modify funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    
    foreach rsvpHandle $ingressTunnelHandle {
        foreach functionPriority $priorityList {
            set functionName [lindex $functionPriority 0]
            set cmdPass [::sth::Rsvp::$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_tunnel_config $funcSwitchArray($functionName) $rsvpHandle]
            if {$cmdPass <= 0} {
                break
            }
        }
        if {$cmdPass <= 0} {
            break
        }
    }
    # add those five arguments for modify , tunnel_count ingress_dst_ip_addr ingress_dst_ip_addr_step egress_src_ip_addr egress_src_ip_addr_step
    set egressAcceptedSwitchList {tunnel_pool_handle egress_ip_addr ingress_ip_addr tunnel_id_start egress_ip_step ingress_ip_step tunnel_id_step tunnel_count ingress_dst_ip_addr ingress_dst_ip_addr_step egress_src_ip_addr egress_src_ip_addr_step}
    foreach rsvpHandle $egressTunnelHandle {
        foreach functionPriority $priorityList {
            set functionName [lindex $functionPriority 0]
            set functionSwitchList $funcSwitchArray($functionName)
            set tmpList [list]
            foreach switchName $functionSwitchList {
                set switchIndex [lsearch -exact $egressAcceptedSwitchList $switchName]
                if {$switchIndex >= 0} {
                    lappend tmpList $switchName
                }
            }
            set functionSwitchList $tmpList
            set cmdPass [::sth::Rsvp::$functionName $functionSwitchList returnKeyedList emulation_rsvp_tunnel_config $functionSwitchList $rsvpHandle]
            if {$cmdPass <= 0} {
                break
            }
        }
        if {$cmdPass <= 0} {
            break
        }
    }    
    
    if {$cmdPass <= 0} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_delete (str args)
###\brief Process \em -mode switch with value \em delete for emulation_rsvp_tunnel_config cmd
###
###This procedure execute the emulation_rsvp_tunnel_config command when the mode is delete. It will delete all rsvp tunnles based on the tunnel_pool_handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_tunnel_config_delete (str args);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_delete { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::emulation_rsvp_tunnel_configFunctionPriority
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_tunnel_config"
    set _hltCmdName "emulation_rsvp_tunnel_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {[info exists switchToValue(element_handle)]} {
        ::sth::Rsvp::configTunnelSubElements returnKeyedList cmdState
        return $returnKeyedList
    }

    if {!([info exist switchToValue(tunnel_pool_handle)])} {
        ::sth::sthCore::processError returnKeyedList "The switch -tunnel_pool_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList
    } 
    set rsvpHandleList $switchToValue(tunnel_pool_handle)
            
    set cmdError 0
    foreach rsvpHandle $rsvpHandleList {    
        #Validate the rsvp_handle
        ::sth::sthCore::log Internalcall "__VALIDATE__: Validate value of handle"
        set msg ""
        if {![::sth::Rsvp::IsRsvpTunnelHandleValid $rsvpHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "The value $rsvpHandle is not valid for the switch -tunnel_pool_handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList         
        }
        #delete rsvp tunnel indicate in the tunnel_pool_handle
        #find corresponding $sessionHandle
        #Call delete tunnel
        if {[catch {::sth::sthCore::invoke stc::delete $rsvpHandle} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting RSVPTunnel:$rsvpHandle" {}    
        }

        if {$cmdError > 0} {
            set cmdState $FAILURE
            return $returnKeyedList
        }    
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList 
}




##########################################################
#RSVP switch helper functions
#########################################################

#########################################################

### /*! \ingroup isishelperfuncs
###\fn processSwitches (str hltapiCommand, str myNameSpace, KeyedListRef returnStringName, str mode, list switchArrayList)
###\brief process all the switches
###
### This procedure goes through all the switches in the user input arguments,
### make a list of switches for each switch-processing function, and call each
### function only once. The priority of each function depends on the priority of 
### the switches. This is based on the assumption that switches processed by
### one function will have same priority, which is correct in most cases. For
### those switches who have different priorities, their priority will be taken
### care of in each switch-processing function.
###
###\param[in] hltapiCommand This is the hltapi command
###\param[in] myNameSpace This is the namespace of current protocol
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###\param[in] mode Create or Modify, this is to specify whether the default value of switches should be taken into account.
###\param[out] switchArrayList This list contains the switch lists for each processing function
###
###\returns the function list with priority.
###
###\author Tong Zhou
###
###processSwitches (str hltapiCommand, str myNameSpace, KeyedListRef returnStringName, str mode, list switchArrayList);
###
proc ::sth::Rsvp::processSwitches {hltapiCommand myNameSpace returnKeyValue mode switchArrayList} {
    upvar $returnKeyValue returnKeyedList
    upvar $switchArrayList functionswitcharrayList
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    array set switchToValue [array get $myNameSpace\switchToValue]
    array set procfuncarray [array get $myNameSpace$hltapiCommand\_procfunc]
    array set priorityarray [array get $myNameSpace$hltapiCommand\_priority]
    if {[string equal $mode create]} {
        catch {unset switchToValue(mandatory_args)}
        catch {unset switchToValue(optional_args)}
        set switchNameList [array names switchToValue]
    } elseif {[string equal $mode modify]} {
        set tmpList $switchToValue(optional_args)
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
            if {$switchToValue($switchName)!=""} {
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



###/*! \ingroup rsvphelperfuncs
###\fn createConfigStartRsvpSession (str args, KeyedListRef returnStringName)
###\brief Create, Config and Start Rsvp Router
###
###This procedure create a RSVP Router, configure it with the users input and finally starts it. 
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###createConfigStartRsvpSession (str args, KeyedListRef returnStringName);
###

proc ::sth::Rsvp::createConfigStartRsvpSession { returnStringName cmdStateVarName rtID} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_config_procfunc
    variable ::sth::Rsvp::emulation_rsvp_configFunctionPriority
    variable ::sth::GBLHNDMAP
    variable ::sth::Rsvp::switchToValue
        variable ipv4Version
        variable atmEncap

    set _OrigHltCmdName "emulation_rsvp_config"
    set _hltCmdName "emulation_rsvp_config_create"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"



    upvar 1 $returnStringName returnKeyedList
    upvar 1 $cmdStateVarName errOccured
    
    #Create the RsvpRouter under the port or existing device and then configure the other parameters.    
    if {[info exists switchToValue(port_handle)]} {
            # If ATM option is provided, configure ATM stack, otherwise, configure ethernet stack.
        # xiaozhi 5/13/09
        if {$atmEncap == 1} {
            set IfStack "Ipv4If Aal5If"
            set IfCount "1 1"
        } else {
            if {[info exists switchToValue(vlan_id)] && [info exists switchToValue(vlan_outer_id)]} {
                #There is S-Vlan and C-vlan
                set IfStack "Ipv4If VlanIf VlanIf EthIIIf"
                set IfCount "1 1 1 1"
            } elseif {[info exists switchToValue(vlan_id)] && ![info exists switchToValue(vlan_outer_id)]} {
                # There is vlan configuration
                set IfStack "Ipv4If VlanIf EthIIIf"
                set IfCount "1 1 1"
            } else {
                # No vlan configuration
                set IfStack "Ipv4If EthIIIf"
                set IfCount "1 1"
            }
        }
        
        if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $switchToValue(port_handle)]
                            set rsvpRouterHandle $DeviceCreateOutput(-ReturnList)} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating RsvpRouter. Error: $createStatus" {}
            set errOccured 1
            return $FAILURE
        } else {
            ::sth::sthCore::log Internalcall "The RsvpRouter:$rsvpRouterHandle was successfully created under port:$switchToValue(port_handle)"
            if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $rsvpRouterHandle  -CreateClassId [string tolower RsvpRouterConfig]]
                              set rsvpSessionHandle $ProtocolCreateOutput(-ReturnList)} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating RsvpProtocol. Error: $createStatus" {}
                set errOccured 1
                return $FAILURE
            }
        }
            
        ###add for gre
        #GRE is not supported in ATM encapsulation,   modifid by xiaozhi 5/13/09
        if {$atmEncap == 0} {
            if {[info exists switchToValue(tunnel_handle)]} {
                set greTopIf [::sth::sthCore::invoke stc::get $rsvpRouterHandle -TopLevelIf-targets]
                set greLowerIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
                    
                ###create the gre stack and setup the relation
                if {[catch {::sth::createGreStack $switchToValue(tunnel_handle) $rsvpRouterHandle $greLowerIf $rtID} greIf]} {
                    ::sth::sthCore::processError returnKeyedList "sth::createGreStack Failed: $greIf" {}
                    return $::sth::sthCore::FAILURE
                }
            
                #stack the top ipif on greif
                ::sth::sthCore::invoke stc::config $greTopIf "-StackedOnEndpoint-targets $greIf"
            }
        }
        
    } elseif {[info exists switchToValue(handle)]} {
        set rsvpRouterHandle $switchToValue(handle)
        if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $rsvpRouterHandle  -CreateClassId [string tolower RsvpRouterConfig]]
                              set rsvpSessionHandle $ProtocolCreateOutput(-ReturnList)} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating RsvpProtocol. Error: $createStatus" {}
            set errOccured 1
            return $FAILURE
        }
    }
    
    
        #To set -HelloCustomObject-targets,-PathErrorCustomObject-targets and -ReservationErrorCustomObject-targets
        #support for list of customobjects
        if {[info exists switchToValue(hello_custom_handle)]} {
                set rsvpRouterConfHandle [stc::get $rsvpRouterHandle -children-RsvpRouterConfig]
                foreach Hellohandle $switchToValue(hello_custom_handle) {
                    stc::config $Hellohandle -HelloCustomObject-targets " $rsvpRouterConfHandle "
                }
        }
        if {[info exists switchToValue(path_err_custom_handle)]} {
                set rsvpRouterConfHandle [stc::get $rsvpRouterHandle -children-RsvpRouterConfig]
                foreach Pathhandle $switchToValue(path_err_custom_handle) {
                    stc::config $Pathhandle -PathErrorCustomObject-targets " $rsvpRouterConfHandle "
                }
        }
        if {[info exists switchToValue(reser_err_custom_handle)]} {
                set rsvpRouterConfHandle [stc::get $rsvpRouterHandle -children-RsvpRouterConfig]
                foreach Resvhandle $switchToValue(reser_err_custom_handle) {
                    stc::config $Resvhandle -ReservationErrorCustomObject-targets " $rsvpRouterConfHandle "
                }
        }
           
    
    #enable/disable BFD
    if {[info exists switchToValue(bfd_registration)]} {
        configBfdRegistration $rsvpRouterHandle $switchToValue(mode) 
        #bfd relation
        set bfdRtrCfg [::sth::sthCore::invoke stc::get $rsvpRouterHandle -children-bfdrouterconfig]
        if {[llength $bfdRtrCfg] != 0} {
            ##
            ##TBC:support IPV4 session type temporarily (IPV6 is not available)
            ##
            set ipResultIf [::sth::sthCore::invoke stc::get $rsvpRouterHandle -PrimaryIf-Targets]
            ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"
        }
    }

    #Configure the created RsvpRouter with user input (options)
    ::sth::sthCore::log Internalcall "Processing the switches in priority order for command:$_hltCmdName"

    
    set cmdPass 1
    set priorityList [::sth::Rsvp::processSwitches emulation_rsvp_config ::sth::Rsvp:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
    #    tk_messageBox -message $functionName
        if {[string equal $functionName "processConfigCmd"]} {
            set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_config $funcSwitchArray($functionName) $rsvpSessionHandle]
        } else {
            set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_config $funcSwitchArray($functionName) $rsvpRouterHandle]
        }
        if {$cmdPass <= 0} {
            break
        }
    }
    if {$cmdPass <= 0} {
        ::sth::sthCore::log error "Error Occured configuring RsvpRouter: $returnKeyedList"
        #Delete the RsvpRouter Object
#        if {[catch {::sth::sthCore::invoke stc::delete $rsvpRouterHandle} eMsg ]} {
#            ::sth::sthCore::log error "Error deleting previously created RsvpRouter:$rsvpRouterHandle Msg: $eMsg"
#        }
        set errOccured 1
        return $FAILURE
    } else {
        set tmpHandles {}
        catch {set tmpHandles [keylget returnKeyedList handles]}
        lappend tmpHandles $rsvpRouterHandle
        keylset returnKeyedList handle $tmpHandles
        keylset returnKeyedList handles $tmpHandles
        set errOccured 0
        return $SUCCESS
    }

}

###/*! \ingroup rsvphelperfuncs
###\fn createConfigStartRsvpTunnel (str args, KeyedListRef returnStringName)
###\brief Create and Config Rsvp Tunnel
###
###This procedure create a RSVP Tunnel and configure it with the users input. 
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###createConfigStartRsvpTunnel (str args, KeyedListRef returnStringName);
###

proc ::sth::Rsvp::createConfigStartRsvpTunnel { returnStringName cmdStateVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_strattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::emulation_rsvp_tunnel_configFunctionPriority
    variable ::sth::Rsvp::switchToValue
    

    set _OrigHltCmdName "emulation_rsvp_tunnel_config"
    set _hltCmdName "emulation_rsvp_tunnel_config_create"
    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"



    upvar 1 $returnStringName returnKeyedList
    upvar 1 $cmdStateVarName errOccured
     
 
    if {![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is mandatory." {}
        set errOccured 1
        return $FAILURE
    } else {
        set RsvpRouterHandle $switchToValue(handle)
        if {![::sth::Rsvp::IsRsvpSessionHandleValid $RsvpRouterHandle rsvpRouterConfigHandle] } {
            ::sth::sthCore::processError returnKeyedList "The -handle $RsvpRouterHandle is not a valid rsvp router." {}
            set errOccured 1
            return $FAILURE
        } else {
#            tk_messageBox -message "1::sth::sthCore::invoke stc::create RsvpTunnelParams -under $rsvpRouterConfigHandle rsvpTunnelHandle"
        }
    }

    # Egress tunnel or Ingress tunnel?
    if {[string equal $switchToValue(direction) egress]} {
        set createTunnelType RsvpEgressTunnelParams
    } else {
        set createTunnelType RsvpIngressTunnelParams
    }
    
#    tk_messageBox -message "::sth::sthCore::invoke stc::create RsvpTunnelParams -under $rsvpRouterConfigHandle rsvpTunnelHandle"
    #Create the RsvpRouter under the port and then configure the other parameters.
    if {[catch {set rsvpTunnelHandle [::sth::sthCore::invoke stc::create $createTunnelType -under $rsvpRouterConfigHandle]} createStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating RsvpTunnel. Error: $createStatus" {}
        set errOccured 1
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "The RsvpTunnel:$rsvpTunnelHandle was successfully created under port:$switchToValue(handle)"
    }
    
    #Configure the created RsvpTunnel with user input (options)
    ::sth::sthCore::log Internalcall "Processing the switches in priority order for command:$_hltCmdName"

    set cmdPass 1
    set priorityList [::sth::Rsvp::processSwitches emulation_rsvp_tunnel_config ::sth::Rsvp:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_rsvp_tunnel_config $funcSwitchArray($functionName) $rsvpTunnelHandle]
        if {$cmdPass <= 0} {
            break
        }
    }
    # Configure the record_route. It is not included in the function switch list, therefore we need to do it manually
    if {$cmdPass > 0} {
        set cmdPass [::sth::Rsvp::emulation_rsvp_tunnel_config_record_route record_route returnKeyedList emulation_rsvp_tunnel_config record_route $rsvpTunnelHandle]
    }

    if {$cmdPass <= 0} {
        ::sth::sthCore::log error "Error Occured configuring RsvpTunnel: $returnKeyedList"
        #Delete the RsvpTunnel Object
        if {[catch {::sth::sthCore::invoke stc::delete $rsvpTunnelHandle} eMsg ]} {
            ::sth::sthCore::log error "Error deleting previously created RsvpTunnel:$rsvpTunnelHandle Msg: $eMsg"
        }
        set errOccured 1
        return $FAILURE
    } else {
        #update the returnKeyledList with the Rsvp Handle.
        keylset returnKeyedList tunnel_handle $rsvpTunnelHandle
        set errOccured 0
        return $SUCCESS
    }

}



###/*! \ingroup rsvphelperfuncs
### \fn IsRsvpSessionHandleValid (str handle, varRef msgName)
###\brief Validates value against rsvp_handle
###
###This procedure checks if the value is valid rsvpSession Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang)
###*/
###
### IsRsvpSessionHandleValid (str handle, varRef msgName);
###

proc ::sth::Rsvp::IsRsvpSessionHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg        

    if {[catch {set protocolHandle [::sth::sthCore::invoke stc::get $handle -children-rsvprouterconfig]} getStatus]} {
        set errorMsg $getStatus
        return $FAILURE
    } else {
        if {[llength $protocolHandle] <= 0} {
            set errorMsg "The router is not running rsvp protocol."
            return $FAILURE
        } else {
            set errorMsg $protocolHandle
            return $SUCCESS
        }
    }

}


###/*! \ingroup rsvphelperfuncs
### \fn IsRsvpTunnelHandleValid (str handle, varRef msgName)
###\brief Validates value against Rsvp Tunnel Handle
###
###This procedure checks if the value is valid rsvp tunnel Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang)
###*/
###
### IsRsvpTunnelHandleValid (str handle, varRef msgName);
###

proc ::sth::Rsvp::IsRsvpTunnelHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg        

    if {[catch {set ParentList [::sth::sthCore::invoke stc::get $handle -parent]} getStatus]} {
        set errorMsg $getStatus
        return $FAILURE
    } else {
        set parentFound 0
        foreach parentHandle $ParentList {
            if {[string first "rsvprouterconfig" $parentHandle] >= 0} {
                set parentFound 1
                set errorMsg $parentHandle
                break
            }
        }
        if {$parentFound > 0} {
            return $SUCCESS
        } else {
            set errorMsg "Not a RSVP tunnel handle"
            return $FAILURE
        }
    }
}


proc ::sth::Rsvp::configBfdRegistration {rtrHandle mode} {
   variable ::sth::Rsvp::switchToValue
   
    if {[catch {set rsvpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-rsvprouterconfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::getNew Failed: $err" {}
        return -code error $returnKeyedList          
    } 
    
    if {$switchToValue(bfd_registration) == "1"} {
        #create new bfdrouterconfig if no exiting bfd found
        set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
        if {[llength $bfdrtrcfg] == 0} {
            if {[catch {set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        if {[catch {::sth::sthCore::invoke stc::config $rsvpRtrHandle "-EnableBfd true"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $rsvpRtrHandle "-EnableBfd false"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    }
}  

###/*! \ingroup rsvphelperfuncs
### \fn getRsvpPort (str handle, varRef returnVarName)
###\brief get rsvp port handle base on the session handle
###
###This procedure get rsvp port handle base on the session handle
###
###\param[in] handle The value of handle
###\param[out] returnVarName hold the return variable name
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\author Jeremy Chang (jchang)
###*/
###
### getRsvpPort (str handle, varRef msgName);
###

proc ::sth::Rsvp::getRsvpPort { handle returnVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnVarName returnVal  
    
    if {[catch {set portHandle [::sth::sthCore::invoke stc::get $handle -affiliationport-Targets]} getStatus]} {
        set returnVal 0
        return $FAILURE
    } else {
        if {$portHandle == ""} {
            set returnVal 0
            return $FAILURE
        } else {
            set returnVal $portHandle
            return $SUCCESS
        }
    }
}



proc ::sth::Rsvp::stepSwitchValue {switchCurrentValue stepValue stepCnt newStepSwitchValueVarName} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    
    upvar 1 $newStepSwitchValueVarName newStepValue

    set incrValue [expr {$stepValue * $stepCnt}]
    if {$incrValue != 0} {
        set newStepValue [expr {$switchCurrentValue + $incrValue}]
    } else {
        set newStepValue $switchCurrentValue
    }
    
    return $SUCCESS
    

}


##########################################################
#RSVP switch Process functions
#########################################################

##########################################################
#Process functions for emulation_rsvp_config
#########################################################

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_hello_interval(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes hello interval switch.
###
###This procedure implements the hello interval switche.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed, currently modified to a list of switches
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2 API
###*/
###
###emulation_rsvp_config_hello_interval ((str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_config_hello_interval {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr

    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    

    set switchName [lindex $switchList 0]
    set switchValue $switchToValue($switchName)
    set stcAttr $emulation_rsvp_config_stcattr($switchName)
    
    set cmdFailed 0
    set HelloInterval [expr int(ceil(double($switchValue)/1000.00))] 
    
    if {![expr $switchValue % 1000]} {
        ::sth::sthCore::log warn "hello interval time can not converted to unit of second.  Setting hello interval time to $HelloInterval second"
    }

    # fetch the rsvpRouterConfig handle
    if {[catch {set rsvpSessionHandle [::sth::sthCore::invoke stc::get $handleValue -children-rsvprouterconfig]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $getStatus" {}
        set cmdFailed 1
        return $FAILURE
    }
    
#    #Fetch the switch/stc mapping information from the Data Structures.
#    This step is currently done before calling this procedure. This can alternatively be done here.
#    set switch2StcMapInfo [::sth::sthCore::GetMapPropertyInfoFromTable $_hltCmdName $_switchName $switchValue]
        
    if {[catch {::sth::sthCore::invoke stc::config $rsvpSessionHandle "-$stcAttr $HelloInterval"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
            ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }  
    
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_vlan (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements the vlan related switches. This command is used to process the vlan-related switches.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2 API
###*/
###
###emulation_rsvp_config_vlan (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar));
###

proc ::sth::Rsvp::emulation_rsvp_config_vlan_info {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
        variable atmEncap

    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
        
        if {$atmEncap == 1} {
            return $SUCCESS
        }

    set handleValue $handleVar    
 
    set cmdFailed 0

    if {[catch {set vlanHandle [::sth::sthCore::invoke stc::get $handleValue -children-VlanIf]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting the vlan interface handle. Error: $getStatus" {}
        return $FAILURE
    }
        
        if {[llength $vlanHandle] == 2} {
            set vlanHandle [lindex $vlanHandle 0]
        }

    if {(![info exists switchToValue(vlan_id)] || $switchToValue(vlan_id)=="")} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Vlan_id not present" {}
        return $FAILURE         
    } else {
        set vlan_id_value $switchToValue(vlan_id)
    }
    
    set configList ""
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        set switchAttr $emulation_rsvp_config_stcattr($switchName)
        if {![string equal $switchAttr _none_]} {
            lappend configList -$switchAttr
            lappend configList $switchValue
        }
    }
#    tk_messageBox -message "::sth::sthCore::invoke stc::config $vlanHandle $configList"
    if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
            ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    } 

}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_vlan_outer_info (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlan outer id switches.
###
###This procedure implements the vlan outer related switches. This command is used to process the vlan-outer-related switches.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2 API
###*/
###
###emulation_rsvp_config_vlan_outer_info (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar));
###

proc ::sth::Rsvp::emulation_rsvp_config_vlan_outer_info {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
        variable atmEncap 
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

        if {$atmEncap == 1} {
            return $SUCCESS
        }
        
    set handleValue $handleVar    
 
    set cmdFailed 0

    if {[catch {set vlanHandle [::sth::sthCore::invoke stc::get $handleValue -children-VlanIf]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting the vlan interface handle. Error: $getStatus" {}
        return $FAILURE
    }
        
        if {[llength $vlanHandle] == 2} {
            set vlanHandle [lindex $vlanHandle 1]
        } else {
            ::sth::sthCore::processError returnKeyedList "do not have two vlan interfaces." {}
            return $FAILURE
        }

    if {(![info exists switchToValue(vlan_outer_id)] || $switchToValue(vlan_outer_id)=="")} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Vlan_outer_id not present" {}
        return $FAILURE         
    } else {
        set vlan_id_value $switchToValue(vlan_outer_id)
    }
    
    set configList ""
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        set switchAttr $emulation_rsvp_config_stcattr($switchName)
        if {![string equal $switchAttr _none_]} {
            lappend configList -$switchAttr
            lappend configList $switchValue
        }
    }
#    tk_messageBox -message "::sth::sthCore::invoke stc::config $vlanHandle $configList"
    if {[catch {::sth::sthCore::invoke stc::config $vlanHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
            ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    } 

}

# config ATM settings, added by xiaozhi
proc ::sth::Rsvp::emulation_rsvp_config_atm_setting {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
        variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
        variable atmEncap
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
        if {$atmEncap == 0} {
            return $SUCCESS
        }
        
    set handleValue $handleVar    
     set cmdFailed 0
    
        if {[catch {set atmIf [::sth::sthCore::invoke stc::get $handleValue "-children-aal5if"]} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
            return -code error $returnKeyedList 
        }
    
    set configList ""
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        set switchAttr $emulation_rsvp_config_stcattr($switchName)
        lappend configList -$switchAttr
        lappend configList $switchValue
    }

        
    if {[catch {::sth::sthCore::invoke stc::config $atmIf $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
    
}


# a temp processConfigCmd function. Later on it might be changed to another name under ::sth::Rsvp:: namespace
proc ::sth::Rsvp::processConfigCmd {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_config_egress_label_mode_fwdmap
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar
    set cmdFailed 0
    
    set configList ""
    
    set egress_label_mode_index [lsearch $switchList egress_label_mode]
    if {$egress_label_mode_index >= 0} {
        set switchName egress_label_mode
        set switchAttr $emulation_rsvp_config_stcattr($switchName)
        set switchValue $switchToValue($switchName)
        set switchValue $emulation_rsvp_config_egress_label_mode_fwdmap($switchValue)
        lappend configList $switchAttr
        lappend configList $switchValue
        set switchList [lreplace $switchList $egress_label_mode_index $egress_label_mode_index]
    }
    set changeFlag 0
    set fastrouterParameters 0
    set switchValueFastRouter NONE
    foreach switchName $switchList {
        set tmpcmd "set switchAttr \$$_hltCmdName\_stcattr($switchName)"
        eval $tmpcmd
        # set switchAttr $emulation_rsvp_config_stcattr($switchName)
        set switchValue $switchToValue($switchName)
        if {$switchName == "facility_backup"} {
            if {$switchValue == 1} {
                if {$switchValueFastRouter == "ONE_TO_ONE_BACKUP"} {
                   ::sth::sthCore::processError returnKeyedList "$_switchName* facility_backup and one_to_one_backup cannot be 1 at same time" {}
                   return -code error $returnKeyedList 
                }
                set switchValueFastRouter "FACILITY_BACKUP"
            } 
            set changeFlag 1
            continue
        }
        if {$switchName == "one_to_one_backup"} {
            if {$switchValue == 1} {
                if {$switchValueFastRouter == "FACILITY_BACKUP"} {
                   ::sth::sthCore::processError returnKeyedList "$_switchName* facility_backup and one_to_one_backup cannot be 1 at same time" {}
                   return -code error $returnKeyedList 
                }
                set switchValueFastRouter "ONE_TO_ONE_BACKUP"
            } 
            set changeFlag 1
            continue
        }
        lappend configList -$switchAttr
        if {![catch {::sth::sthCore::getFwdmap ::sth::Rsvp:: $_hltCmdName $switchName $switchValue} value]} {
                lappend configList $value
        } else {
                lappend configList $switchValue
        }
    }
    
    if {$_hltCmdName == "emulation_rsvp_tunnel_config"} {
        set priorityList1 [::sth::Rsvp::processSwitches emulation_rsvp_tunnel_config ::sth::Rsvp:: returnKeyedList1 modify funcSwitchList1]
        array set funcSwitchArray1 $funcSwitchList1
        foreach functionPriority1 $priorityList1 {
                set functionName1 [lindex $functionPriority1 0]
                if {$functionName1 == "processConfigCmd"} {
                    set switchList1 $funcSwitchArray1($functionName1)
                    foreach switchName1 $switchList1 {
                            switch -- $switchName1 {
                                    "fast_reroute_exclude_any" -
                                    "fast_reroute_holding_priority" -
                                    "fast_reroute_hop_limit" -
                                    "fast_reroute_include_all" -
                                    "fast_reroute_include_any" -
                                    "fast_reroute_setup_priority" -
                                    "fast_reroute_bandwidth" {
                                            set fastrouterParameters 1
                                            break
                                    }       
                            }        
                    }
                    break
                }
        }
    }
    if {$changeFlag == 1} {
        lappend configList "-FastRerouteObject"
        lappend configList $switchValueFastRouter
    }
    if {($switchValueFastRouter == "NONE")&&($fastrouterParameters == 1)} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* fast_reroute_exclude_any/holding_priority/hop_limit/include_all/include_any/setup_priority/bandwidth can't be set when not specify fast reroute object" {}
        return -code error $returnKeyedList        
    }
    if {[catch {::sth::sthCore::invoke stc::config $handleValue $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_intf_ip (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements the IP interface related switches. This command is used to process the switches of IP interface.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_intf_ip (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
###
proc ::sth::Rsvp::emulation_rsvp_config_intf_ip {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    
     set cmdFailed 0
    
    #get port handle
    if {[string equal $switchToValue(mode) "enable"] || [string equal $switchToValue(mode) "create"]} {
        if {![info exists switchToValue(port_handle)]} {
             ::sth::sthCore::processError returnKeyedList "$_switchName* Valid value for the port_handle not entered." {}
            return $FAILURE         
        } else {
            set portHandle $switchToValue(port_handle)        
        }
    }
    ##will have problem if there are two ipv4if. Rewrote by cf
    #if {[catch {stc::get -children-ipv4if $handleValue ipv4Handle} getStatus]} {
    #    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting the IPv4 interface handle. Error: $getStatus" {}
    #    return $FAILURE
    #}
        
        ##rewrote for gre case
        if {[catch {set ipv4Handle [::sth::sthCore::invoke stc::get $handleValue -TopLevelIf-targets]} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
            return -code error $returnKeyedList 
        }
    
    set configList ""
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        set switchAttr $emulation_rsvp_config_stcattr($switchName)
        lappend configList -$switchAttr
        lappend configList $switchValue
    }

        
    if {[catch {::sth::sthCore::invoke stc::config $ipv4Handle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    } 

}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_graceful_restart (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements the graceful restart related switches. This command is used to process the graceful restart-related switches
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_graceful_restart (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
proc ::sth::Rsvp::emulation_rsvp_config_graceful_restart {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr

    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    
     set cmdFailed 0
     
     set rsvpRouterHandle $handleValue
     
     if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
         ::sth::sthCore::processError returnKeyedList "The -handle $rsvpRouterHandle is not the handle of a RSVP router" {}
         return $FAILURE
    }
     
     if {![info exists switchToValue(graceful_restart)]} {
         if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $rsvpProtocolHandle -EnableGracefulRestart]} getStatus]} {
             ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting the old graceful_restart value. Error: $getStatus" {}
             return $FAILURE
         }
     } else {
         set gracefulRestart $switchToValue(graceful_restart)
     }
     
#     if {!$gracefulRestart} {
#         # Graceful restart is not enabled, skip configuring
#         ::sth::sthCore::log warn "graceful restart is not enabled, thus all the switches related to graceful restart are skipped."
#         return $SUCCESS
#     } else {         
         set configList ""
         foreach switchName $switchList {
             set switchAttr $emulation_rsvp_config_stcattr($switchName)
             set switchValue $switchToValue($switchName)
             lappend configList -$switchAttr
             lappend configList $switchValue
         }
        if {$gracefulRestart} {
                if {[lsearch $configList "-EnableHello"] == -1} {
                    set configList [concat $configList "-EnableHello 1"]
                }
                if {[lsearch $configList "-HelloInterval"] == -1} {
                    set configList [concat $configList "-HelloInterval 5000"]
                }
        }
         if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle $configList} configStatus]} {
             ::sth::sthCore::processError returnKeyedList "$_switchName * Internal Command Error while configuring the switch. Error: $configStatus" {}
             return $FAILURE
         } else {
             return $SUCCESS
         }
     #}
}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_bundle_interval (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements process the switches bundle_interval and bundle_msgs, both of them are mapped to the nullable attribute 
###RsvpRotuerConfig.RefreshReductionBundleInterval - when it is null, bundle_msgs is false, bundle_interval has no value; when it has value,
###bundle_msgs is true, bundle_interval has value.
###
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_bundle_interval (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
proc ::sth::Rsvp::emulation_rsvp_config_bundle_interval {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    
     set cmdFailed 0
     
     set rsvpRouterHandle $handleValue
     
     if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
         ::sth::sthCore::processError returnKeyedList "The -handle $rsvpRouterHandle is not the handle of a RSVP router" {}
         return $FAILURE
    }

    if {![info exists switchToValue(bundle_msgs)]} {
        set switchToValue(bundle_msgs) 1
    }
    
    if {$switchToValue(bundle_msgs)} {
        if {![info exists switchToValue(bundle_interval)]} {
            ::sth::sthCore::processError returnKeyedList "If bundle_msgs is set 1, the value of bundle_interval must be included." {}
            return $FAILURE
        } else {
            if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle "-RefreshReductionBundleInterval $switchToValue(bundle_interval)"} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
                return $FAILURE
            }
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle "-RefreshReductionBundleInterval null"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
            return $FAILURE
        }
    }
    return $SUCCESS
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_srefresh (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements process the switches srefresh_interval and summary_refresh, both of them are mapped to the nullable attribute 
###RsvpRotuerConfig.RefreshReductionSummaryRefreshInterval - when it is null, summary_refresh is false, bundle_interval has no value; when
###it has value, summary_refresh is true, srefresh_interval has value.
###
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_srefresh (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
proc ::sth::Rsvp::emulation_rsvp_config_srefresh {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    
     set cmdFailed 0
     
     set rsvpRouterHandle $handleValue
     
     if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
         ::sth::sthCore::processError returnKeyedList "The -handle $rsvpRouterHandle is not the handle of a RSVP router" {}
         return $FAILURE
    }

    if {![info exists switchToValue(summary_refresh)]} {
        set switchToValue(summary_refresh) 1
    }
    
    if {$switchToValue(summary_refresh)} {
        if {![info exists switchToValue(srefresh_interval)]} {
            ::sth::sthCore::processError returnKeyedList "If summary_refresh is set 1, the value of srefresh_interval must be included." {}
            return $FAILURE
        } else {
            if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle "-RefreshReductionSummaryRefreshInterval $switchToValue(srefresh_interval)"} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                return $FAILURE
            }
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle "-RefreshReductionSummaryRefreshInterval null"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
            return $FAILURE
        }
    }
    return $SUCCESS
}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_record_route (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes vlanid switches.
###
###This procedure implements process the switch record_route, which is currently mapped to RsvpIngressTunnelParams.EnableRecordRoute. However,
###the RsvpTunnelParams can only be created in the command emulation_rsvp_tunnel_config, therefore, if RsvpTunnelParams is not created yet, we 
###only want to store its value into ::sth::Rsvp:: namespace, and process it later on when emulation_rsvp_tunnel_config is called. If RsvpTunnelParams
###is already created and this function is called under modify mode, we go to RsvpTunnelParams to modify it.
###
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_record_route (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
proc ::sth::Rsvp::emulation_rsvp_config_record_route {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    variable ::sth::Rsvp::EnableRecordRoute
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    
     set cmdFailed 0
     
     set rsvpRouterHandle $handleValue
     
     if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
         ::sth::sthCore::processError returnKeyedList "The -handle $rsvpRouterHandle is not the handle of a RSVP router" {}
         return $FAILURE
    } else {
        set EnableRecordRoute($rsvpRouterHandle) $switchToValue(record_route)
    }
    
    if {[catch {set rsvpTunnelHandleList [::sth::sthCore::invoke stc::get $rsvpProtocolHandle -children-RsvpTunnelParams]} getStatus]} {
        return $SUCCESS
    } else {
        foreach rsvpTunnelHandle $rsvpTunnelHandleList {
            if {[catch {::sth::sthCore::invoke stc::config $rsvpTunnelHandle "-EnableRecordRoute $EnableRecordRoute($rsvpRouterHandle)"} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
                return $FAILURE
            }
        }
        return $SUCCESS
    }
}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_config_transit(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar)
###\brief Processes transit switch. Note: there is only one ACCEPT_ALL router allowed per port.
###
###This procedure implements the transit switch.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed, currently modified to a list of switches
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return sth::sthCore::FAILURE or sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_config_transit ((str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_config_transit {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    

    set switchName [lindex $switchList 0]
    set switchValue $switchToValue($switchName)
    set stcAttr $emulation_rsvp_config_stcattr($switchName)
    
    set cmdFailed 0     
    set rsvpRouterHandle $handleValue
 
     if {![::sth::Rsvp::IsRsvpSessionHandleValid $rsvpRouterHandle rsvpProtocolHandle]} {
         ::sth::sthCore::processError returnKeyedList "The -handle $rsvpRouterHandle is not the handle of a RSVP router" {}
         return $FAILURE
    }
    
    if {![::sth::Rsvp::getRsvpPort $rsvpRouterHandle rsvpPort]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while getting the port of -handle $rsvpRouterHandle" {}
        return $FAILURE
    } 
    
    if {[string equal $switchValue RSVP_TRANSIT_ACCEPT_ALL]} {
        #Check if this is the only one ACCEPT_ALL router in the current port
        set foundAcceptAll 0
        if {[catch {set routerList [::sth::sthCore::invoke stc::get $rsvpPort -affiliationport-Sources]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while getting routers from the port $rsvpPort. Error: $getStatus" {}
            return $FAILURE
        }
        foreach routerHandle $routerList {
            if { $routerHandle != $rsvpRouterHandle && [::sth::Rsvp::IsRsvpSessionHandleValid $routerHandle tmpRsvpProtocolHandle]} {
                if {![catch {set tmpTransit [::sth::sthCore::invoke stc::get $tmpRsvpProtocolHandle -Transit]} getStatus]} {
                    if {[string equal $tmpTransit RSVP_TRANSIT_ACCEPT_ALL]} {
                        set foundAcceptAll 1
                        break
                    }
                }
            }
        }
        
        if {$foundAcceptAll > 0} {
            ::sth::sthCore::processError returnKeyedList "$_hltCmdName* There is already an TRANSIT_ACCEPT_ALL router under the same port. Only one such router is allowed per port." {}
            return $FAILURE
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $rsvpProtocolHandle "-Transit $switchValue"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_hltCmdName* Internal Command Error while configuring the switch. Error: $configStatus" {}
        return $FAILURE
    } else {
        return $SUCCESS
    }
}

##########################################################
#Process functions for emulation_rsvp_info
#########################################################

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_get (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic RSVP Get Processor
###
###This procedure implements the generic get command for RSVP. This command is used by all the keys with one on one mapping with the STC attributes. In the args, wherever it says switch, it is supposed to mean key
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for stc P2
###*/
###
###emulation_rsvp_get (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_get { switchList returnInfoVarName _hltCmdName _switchName rsvpRouterHandle rsvpProtocolHandle rsvpResultsHandle } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_info_stcattr


    upvar 1 $returnInfoVarName returnKeyedList
    set getValueVar ""

    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
    set getList ""
    foreach switchName $switchList {
        lappend getList -$emulation_rsvp_info_stcattr($switchName)
    }
    
    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $rsvpResultsHandle $getList]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while fetching value of switches. Error: $getStatus" {}
        return $FAILURE
    } else {
        set i 0
        set configReturnKeyedList {}
        foreach {attr attrValue} $getValueVar {
            set switchName [lindex $switchList $i]
            incr i
            lappend configReturnKeyedList $switchName $attrValue
        }
        set cmd "keylset returnKeyedList $configReturnKeyedList"
        if {[catch {eval $cmd}]} {
            ::sth::sthCore::processError returnKeyedList "Cannot set returnKeyedList" {}
        }
        return $SUCCESS
    }
}





###/*! \ingroup rsvpswitchprocfuncs
###\fn ::sth::sthCore::emulation_rsvp_info_lsp_count(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes RouteTarget related switches.
###
###This procedure implements the target, target_type and targer_assign switches. This command is used by all the switches with one on one mapping with the STC attributes.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Saumil Mehta (smehta), modified by Tong Zhou for stc P2
###*/
###
###::sth::sthCore::emulation_rsvp_info_lsp_count (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_lsp_count {switchList returnInfoVarName _hltCmdName _switchName rsvpRouterHandle rsvpProtocolHandle rsvpResultsHandle} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_info_stcattr


    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Fetching key: -$_switchName for Command: $_hltCmdName"

    
    ::sth::sthCore::log Internalcall "Fetching the key:$_switchName "

    set grpName ""
    set result  "0"
        
    
    set returnValueList "-LspConnectingCount -LspDownCount -LspUpCount"
    if {[catch {set lspNumbers [::sth::sthCore::invoke stc::get $rsvpResultsHandle $returnValueList]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while fetching LSP return value from $handleValue. Error: $getStatus" {}
        set cmdFailed 1
        return $FAILURE
    } else {
        set result "[lindex $lspNumbers 1]+[lindex $lspNumbers 3]+[lindex $lspNumbers 5]"
    }
    
    
    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** fetched"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
    
        set keyVal [expr "$result"]
        #to handle lsp_count and num_lsps_setup switch
        foreach switchName $_switchName {
            keylset returnKeyedList $switchName $keyVal
        }
        return $SUCCESS
    }
}

### ::sth::Rsvp::emulation_rsvp_get_intfip (string switchList, keyedList returnInfoVarName, string _hltCmdName, string _switchName, router_handle handleVar)
### This function is used to get the IP address of the RSVP router.

proc ::sth::Rsvp::emulation_rsvp_get_intfip {switchList returnInfoVarName _hltCmdName _switchName rsvpRouterHandle rsvpProtocolHandle rsvpResultsHandle} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_info_stcattr


    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Fetching key: -$_switchName for Command: $_hltCmdName"
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_rsvp_info_stcattr($switchName)
    
    if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $rsvpRouterHandle -children-ipv4if]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting $switchName. Error: $getStatus" {}
        return $FAILURE
    }
    
    if {[catch {set returnValue [::sth::sthCore::invoke stc::get $ipv4ResultIf -Address]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ip_addr. Error: $getStatus" {}
        return $FAILURE
    } else {
        keylset returnKeyedList $switchName $returnValue
        return $SUCCESS
    }
}

### proc ::sth::Rsvp::emulation_rsvp_get_neighborip (string switchList, keyedList returnInfoVarName, string _hltCmdName, string _switchName, router_handle handleVar)
### This function is used to get the IP address of the neighboring RSVP router.

proc ::sth::Rsvp::emulation_rsvp_get_neighborip {switchList returnInfoVarName _hltCmdName _switchName rsvpRouterHandle rsvpProtocolHandle rsvpResultsHandle} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_info_stcobj
    variable ::sth::Rsvp::emulation_rsvp_info_stcattr

    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Fetching key: -$_switchName for Command: $_hltCmdName"
    
    ::sth::sthCore::log Internalcall "Fetching the key:$_switchName "
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_rsvp_info_stcattr($switchName)
    
    if {[catch {set attrValue [::sth::sthCore::invoke stc::get $rsvpProtocolHandle -$switchAttr]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while fetching RSVP protocol handle from $handleVar. Error: $getStatus" {}
        return $FAILURE
    } else {
        keylset returnKeyedList $switchName $attrValue
        return $SUCCESS
    }
    
}


##########################################################
#Process functions for emulation_rsvp_tunnel_config
#########################################################

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_flag(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes session attribute flag related switch.
###
###This procedure implements the session attribute flag related switch.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_tunnel_config_flag (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_flag {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    


    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $handleVar -flag]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while fetching value of session attribute flags. Error: $getStatus" {}
        return $FAILURE
    }  
    ::sth::sthCore::log Internalcall "Originial Attribute flag value $getValueVar"
    
    set flagList [string map {"|" " "} $getValueVar]
    set flag 0
    foreach flagEnum $flagList {
        switch -exact -- $flagEnum {
            NONE -
            RSVP_FLAG_LOCAL_PROTECTION_DESIRED {set flag [expr $flag | 0x01]}
            RSVP_FLAG_MERGING_PERMITTED {set flag [expr $flag | 0x02]}
            RSVP_FLAG_INGRESS_NODE_MAY_REROUTE {set flag [expr $flag | 0x04]}
            RSVP_FLAG_BANDWIDTH_PROTECTION_DESIRED {set flag [expr $flag | 0x08]}
            RSVP_FLAG_NODE_PROTECTION_DESIRED {set flag [expr $flag | 0x10]}
        }
    }
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        if {[string equal $switchName "session_attr_flags"]} {
            set flag $switchValue
            break
        } else {
            if {$switchValue} {
                switch $switchName {
                    session_attr_local_protect {
                            set flag [expr $flag | 0x01] 
                        }
                    session_attr_label_record {
                        set flag [expr $flag | 0x02] 
                    }
                    session_attr_se_style {
                         set flag [expr $flag | 0x04]
                    }
                    session_attr_bw_protect {
                        set flag [expr $flag | 0x08]
                         } 
                    session_attr_node_protect {
                        set flag [expr $flag | 0x10]            
                    }
                    default {            
                    }
                }
            } elseif {!$switchValue} {
                switch -exact -- $_switchName {
                    session_attr_local_protect {
                        set flag [expr $flag & 0xFE] 
                    }
                    session_attr_label_record {
                        set flag [expr $flag & 0xFD] 
                    }
                    session_attr_se_style {
                        set flag [expr $flag & 0xFB] 
                    }
                    session_attr_bw_protect {
                        set flag [expr $flag & 0xF7]            
                    } 
                    session_attr_node_protect {
                        set flag [expr $flag & 0xEF]            
                    } 
                     default {
                    }
                }
            }
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $handleValue "-flag $flag"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $flag"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $flag set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }  
    
}


###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_ero_list_ipv4(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes ero_list_ipv4 ero_list_loose ero_list_pfxlen switch.
###
###This procedure implements the ero_list_ipv4 ero_list_loose ero_list_pfxlen switche.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang)
### Modified by Tong Zhou for P2
###*/
###
###emulation_rsvp_tunnel_config_ero_list_ipv4 (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_list_ipv4 {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_list_loose_fwdmap
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValue $handleVar    

    set cmdFailed 0
    
    if {![info exist switchToValue(ero_list_loose)] } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_loose for switch \
            -ero_list_ipv4 is/are not specified correctly or missing." {}
        return $FAILURE            
         
    }     
    if {![info exist switchToValue(ero_list_pfxlen)] } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_pfxlen for switch \
            -ero_list_ipv4 is/are not specified correctly or missing." {}
        return $FAILURE            
         
    }         
    if {![info exist switchToValue(ero_list_ipv4)] } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_ipv4 for switch \
            -ero_list_ipv4 is/are not specified correctly or missing." {}
        return $FAILURE            
         
    } 

    set addrList $switchToValue(ero_list_ipv4)
    set typeList $switchToValue(ero_list_loose) 
    set prefixList $switchToValue(ero_list_pfxlen) 
    
    if {([llength $addrList] != [llength $typeList]) || ([llength $typeList] != [llength $prefixList])} {
        ::sth::sthCore::processError returnKeyedList "The number of -ero_list_loose,\
            -ero_list_pfxlen and -ero_list_ipv4 list should be same." {}
        return $FAILURE         
    
    }
    if {[llength $addrList] == 0} {
        #ignore if empty list
        ::sth::sthCore::log warn "empty ero list is input it.  Ignoring the switch command"
        return $SUCCESS             
    }

    if {([string first "ero_mode" $switchToValue(optional_args)]< 0) && ([string first "ero_dut_pfxlen" $switchToValue(optional_args)]<0)} {
        if {[catch {set eroObjectHandles [::sth::sthCore::invoke stc::get $handleValue -children-RsvpIpv4EroObject]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ERO Ojbect. Error: $getStatus" {}
            return $FAILURE
        }
        
        if {[llength $eroObjectHandles]>0} {
            foreach eroObjectHandle $eroObjectHandles {
                if {[catch {::sth::sthCore::invoke stc::delete $eroObjectHandle} deleteStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while \
                        deleting previous explicit route. Error: $deleteStatus" {}
                    return $FAILURE
                }
            }
        }
        
        if {[catch {set eroObjectHandle [::sth::sthCore::invoke stc::create RsvpIpv4EroObject -under $handleValue]} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route object. Error: $createStatus" {}
                return $FAILURE
        }
    } else {
        if {[catch {set eroObjectHandles [::sth::sthCore::invoke stc::get $handleValue -children-RsvpIpv4EroObject]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ERO Ojbect. Error: $getStatus" {}
            return $FAILURE
        }
        
        set eroObjectHandle [lindex $eroObjectHandles 0]
    }
    if { $switchToValue(ero) == 1 } {
    set i 0
    foreach addr $addrList {
        set type [lindex $typeList $i]
        set prefix [lindex $prefixList $i]
        incr i
        
        set type $emulation_rsvp_tunnel_config_ero_list_loose_fwdmap($type)
        
        set configList "-RouteType $type"
        if {[catch {set explicitRouteHandle [::sth::sthCore::invoke stc::create RsvpIpv4ExplicitRouteParams -under $eroObjectHandle $configList]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route. Error: $createStatus" {}
            return $FAILURE
        }
        set configList "-StartIpList $addr -PrefixLength $prefix"
        if {[catch {set NetworkBlockHandle [::sth::sthCore::invoke stc::get $explicitRouteHandle -children-ipv4networkblock]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
                the network block handle from explicit route. Error: $getStatus" {}
            return $FAILURE            
        } else {
            if {[catch {::sth::sthCore::invoke stc::config $NetworkBlockHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
                return $FAILURE    
            }
        }
    }
    }
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE    
    } else {
        ::sth::sthCore::log Internalcall "Value set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }  
    
}
###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_ero_list_dut(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes ero_mode ero_dut_pfxlen switch.
###
###This procedure implements the ero_list_ipv4 ero_list_loose ero_list_pfxlen switche.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Yulin Chen (ychen)
###*/
###
###emulation_rsvp_tunnel_config_ero_list_dut (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###
proc ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_list_dut {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
        variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_mode_fwdmap
        variable ::sth::Rsvp::emulation_rsvp_tunnel_config_handle
        
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
        
    set handleValue $handleVar    

    set cmdFailed 0
    
    if {![info exist switchToValue(ero_mode)] } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_mode for switch \
             is/are not specified correctly or missing." {}
        return $FAILURE            
         
    }
        
    if {![info exist switchToValue(ero_dut_pfxlen)] } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_dut_pfxlen for switch \
             is/are not specified correctly or missing." {}
        return $FAILURE            
         
    }
        
    set type $switchToValue(ero_mode) 
    set prefix $switchToValue(ero_dut_pfxlen)
        
        if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $handleValue -Parent]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting router handle. Error: $getStatus" {}
        return $FAILURE
        }
        if {[catch {set addr [::sth::sthCore::invoke stc::get $routerHandle -DutIpAddr]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting router dut ip addr. Error: $getStatus" {}
        return $FAILURE
        }
        
    #if {[catch {stc::get -children-RsvpIpv4ExplicitRouteParams $handleValue previousRouteHandles} getStatus]} {
    #    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting explicit route. Error: $getStatus" {}
    #    return $FAILURE
    #}

#    if {[catch {stc::get -children-RsvpIpv4ExplicitRouteParams $handleValue previousRouteHandles} getStatus]} {
#        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting explicit route. Error: $getStatus" {}
#        return $FAILURE
#    } else {
#        foreach routeHandle $previousRouteHandles {
#            
#            if {[catch {stc::get -Children-ipv4networkblock $routeHandle routeIpNetwork} Status]} {
#                            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
#                            the network block handle from explicit route. Error: $Status" {}
#                            return $FAILURE
#            }
#                        if {[catch {stc::get -StartIpList $routeIpNetwork routeAddr} errMsg]} {
#                            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
#                            the Ip address from network block. Error: $errMsg" {}
#                            return $FAILURE
#                        }
#                        if {$routeAddr == $addr} {
#                            if {[catch {::sth::sthCore::invoke stc::delete $routeHandle} deleteStatus]} {
#                                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while \
#                                    deleting previous explicit route. Error: $deleteStatus" {}
#                                    return $FAILURE
#                            }
#                            break
#                        }
#        }
#    }

    if {[catch {set eroObjectHandles [::sth::sthCore::invoke stc::get $handleValue -children-RsvpIpv4EroObject]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ERO Ojbect. Error: $getStatus" {}
        return $FAILURE
    }
    
    if {[llength $eroObjectHandles]>0} {
        foreach eroObjectHandle $eroObjectHandles {
            if {[catch {::sth::sthCore::invoke stc::delete $eroObjectHandle} deleteStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while \
                    deleting previous explicit route. Error: $deleteStatus" {}
                return $FAILURE
            }
        }
    }
        
    if {![string equal -nocase $type "none"]} {
        if {[catch {set eroObjectHandle [::sth::sthCore::invoke stc::create RsvpIpv4EroObject -under $handleValue]} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route object. Error: $createStatus" {}
                return $FAILURE
        }
        
        set type $emulation_rsvp_tunnel_config_ero_mode_fwdmap($type)
        
        set configList "-RouteType $type"
        if {[catch {set explicitRouteHandle [::sth::sthCore::invoke stc::create RsvpIpv4ExplicitRouteParams -under $eroObjectHandle $configList]} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route. Error: $createStatus" {}
                return $FAILURE
        }
        set configList "-StartIpList $addr -PrefixLength $prefix"
        if {[catch {set NetworkBlockHandle [::sth::sthCore::invoke stc::get $explicitRouteHandle -children-ipv4networkblock]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
        the network block handle from explicit route. Error: $getStatus" {}
                return $FAILURE            
        } else {
                if {[catch {::sth::sthCore::invoke stc::config $NetworkBlockHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
                        return $FAILURE    
                }
        }
    }
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE    
    } else {
        ::sth::sthCore::log Internalcall "Value set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}
###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_ero(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes ero_list_ipv4 ero_list_loose ero_list_pfxlen ero_mode ero_dut_pfxlen switch.
###
###This procedure implements the ero_list_ipv4 ero_list_loose ero_list_pfxlen ero_mode ero_dut_pfxlen switche.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Yulin Chen (ychen)
###*/
###
###emulation_rsvp_tunnel_config_ero (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###
proc ::sth::Rsvp::emulation_rsvp_tunnel_config_ero {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    #variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_list_loose_fwdmap
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_mode_fwdmap
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_handle
    upvar 1 $returnInfoVarName returnKeyedList
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    set handleValue $handleVar    
    set cmdFailed 0

    # Delete previous ERO configuration and create new
    if {[catch {set eroObjectHandles [::sth::sthCore::invoke stc::get $handleValue -children-RsvpIpv4EroObject]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ERO Ojbect. Error: $getStatus" {}
        return $FAILURE
    }
    if {[llength $eroObjectHandles]>0} {
        foreach eroObjectHandle $eroObjectHandles {
            if {[catch {::sth::sthCore::invoke stc::delete $eroObjectHandle} deleteStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while \
                    deleting previous explicit route. Error: $deleteStatus" {}
                return $FAILURE
            }
        }
    }
    if { $switchToValue(ero) == 1 } {
        if {[catch {set eroObjectHandle [::sth::sthCore::invoke stc::create RsvpIpv4EroObject -under $handleValue]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route object. Error: $createStatus" {}
            return $FAILURE
        }
        if {[info exist switchToValue(ero_mode)] && ![string equal -nocase $switchToValue(ero_mode) "none"]} {
            #if {![info exist switchToValue(ero_mode)] } {
            #        ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_mode for switch \
            #                is/are not specified correctly or missing." {}
            #        return $FAILURE
            #}
            if {![info exist switchToValue(ero_dut_pfxlen)] } {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_dut_pfxlen for switch \
                    is/are not specified correctly or missing." {}
                return $FAILURE            
            }
            set type $switchToValue(ero_mode) 
            set prefix $switchToValue(ero_dut_pfxlen)
            if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $handleValue -Parent]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting router handle. Error: $getStatus" {}
                return $FAILURE
            }
            if {[catch {set addr [::sth::sthCore::invoke stc::get $routerHandle -DutIpAddr]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting router dut ip addr. Error: $getStatus" {}
                return $FAILURE
            }
            set type $emulation_rsvp_tunnel_config_ero_mode_fwdmap($type)
            set configList "-RouteType $type"
            if {[catch {set explicitRouteHandle [::sth::sthCore::invoke stc::create RsvpIpv4ExplicitRouteParams -under $eroObjectHandle $configList]} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route. Error: $createStatus" {}
                return $FAILURE
            }
            set configList "-StartIpList $addr -PrefixLength $prefix"
            if {[catch {set NetworkBlockHandle [::sth::sthCore::invoke stc::get $explicitRouteHandle -children-ipv4networkblock]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
                    the network block handle from explicit route. Error: $getStatus" {}
                return $FAILURE            
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $NetworkBlockHandle $configList} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
                    return $FAILURE    
                }
            }
        }
    } else {
        ::sth::sthCore::log debug "You can specify argument $_switchName only when -ero is set to 1."
        keylset returnKeyedList status $SUCCESS
        return $returnKeyedList
    }
    ############################################################################################################################
    #comment out the ero config for the ero_list_ipv4, this should be done in the emulation_rsvp_tunnel_config_ero_list_ipv4
    #if here process the ero_list_ipv4 and create the ero based on this ipv4 addr, then it will duplicated with what will be
    #done in the emulation_rsvp_tunnel_config_ero_list_ipv4 function.
    #since not very confident about this, so just comment it, and keep the code here
    ############################################################################################################################
    #if {[info exist switchToValue(ero_list_ipv4)]} {
    #        if {![info exist switchToValue(ero_list_loose)] } {
    #                ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_loose for switch \
    #                        -ero_list_ipv4 is/are not specified correctly or missing." {}
    #                return $FAILURE
    #        }
    #        if {![info exist switchToValue(ero_list_pfxlen)] } {
    #                ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_pfxlen for switch \
    #                        -ero_list_ipv4 is/are not specified correctly or missing." {}
    #                return $FAILURE
    #        }
    #        if {![info exist switchToValue(ero_list_ipv4)] } {
    #                ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_ipv4 for switch \
    #                        -ero_list_ipv4 is/are not specified correctly or missing." {}
    #                return $FAILURE
    #        }
    #        set addrList $switchToValue(ero_list_ipv4)
    #        set typeList $switchToValue(ero_list_loose)
    #        set prefixList $switchToValue(ero_list_pfxlen)
    #        if {([llength $addrList] != [llength $typeList]) || ([llength $typeList] != [llength $prefixList])} {
    #                ::sth::sthCore::processError returnKeyedList "$_switchName* Dependent switches -ero_list_loose,\
    #                        -ero_list_pfxlen for switch -ero_list_ipv4 is/are not specified correctly or missing." {}
    #                return $FAILURE
    #        }
    #        if {[llength $addrList] == 0} {
    #            #ignore if empty list
    #                ::sth::sthCore::log warn "empty ero list is input it.  Ignoring the switch command"
    #                return $SUCCESS
    #        }
    #        set i 0
    #        foreach addr $addrList {
    #                set type [lindex $typeList $i]
    #                set prefix [lindex $prefixList $i]
    #                incr i
    #                set type $emulation_rsvp_tunnel_config_ero_list_loose_fwdmap($type)
    #                set configList "-RouteType $type"
    #                if {[catch {set explicitRouteHandle [::sth::sthCore::invoke stc::create RsvpIpv4ExplicitRouteParams -under $eroObjectHandle $configList]} createStatus]} {
    #                        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while creating explicit route. Error: $createStatus" {}
    #                        return $FAILURE
    #                }
    #                set configList "-StartIpList $addr -PrefixLength $prefix"
    #                if {[catch {set NetworkBlockHandle [::sth::sthCore::invoke stc::get $explicitRouteHandle -children-ipv4networkblock]} getStatus]} {
    #                        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting \
    #                                the network block handle from explicit route. Error: $getStatus" {}
    #                        return $FAILURE
    #                } else {
    #                        if {[catch {::sth::sthCore::invoke stc::config $NetworkBlockHandle $configList} configStatus]} {
    #                                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the switch. Error: $configStatus" {}
    #                                return $FAILURE
    #                        }
    #                }
    #        }
    #}
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE    
    } else {
        ::sth::sthCore::log Internalcall "Value set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}

###/*! \ingroup rsvpswitchprocfuncs
###\fn emulation_rsvp_tunnel_config_ingress_ip_addr(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes session attribute ingress_ip_addr switch.
###
###This procedure implements the session attribute ingress_ip_addr switch.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang)
###*/
###
###emulation_rsvp_tunnel_config_ingress_ip_addr (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_ip_addr {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_list_loose_fwdmap
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName "

    set handleValue $handleVar    


#    #Fetch the switch/stc mapping information from the Data Structures.
#    This step is currently done before calling this procedure. This can alternatively be done here.
#    set switch2StcMapInfo [::sth::sthCore::GetMapPropertyInfoFromTable $_hltCmdName $_switchName $switchValue]

    
    ::sth::sthCore::log Internalcall "Configuring the switch:$_switchName"
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_rsvp_tunnel_config_stcattr($switchName)
    set switchValue $switchToValue($switchName) 
            
    if {[catch {::sth::sthCore::invoke stc::config $handleValue "-$switchAttr $switchValue"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
    } 
    #if extended_tunnel_id is not input, then configure it to be the value of ingress_ip_addr.
    if {[string first "ingress" [string tolower $handleValue]] >= 0} {
                if {![info exists switchToValue(extended_tunnel_id)]} {
                        if {[catch {::sth::sthCore::invoke stc::config $handleValue "-extendedTunnelId $switchValue"} configStatus]} {
                                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                                set cmdFailed 1
                        } else {
                                ::sth::sthCore::log Internalcall "The switch:$_switchName was successfully set to $switchValue"
                        }   
                }
        
    }
    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log Internalcall "Value: $switchValue set for switch:$_switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }  
    
}


##########################################################################
# The matching function of emulation_rsvp_config_record_route
##########################################################################
###\fn emulation_rsvp_tunnel_config_record_route(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes session attribute ingress_ip_addr switch.
###
###This procedure configures the attribute record_route under the command emulation_rsvp_config
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Tong Zhou
###*/
###
###emulation_rsvp_tunnel_config_record_route (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###
proc ::sth::Rsvp::emulation_rsvp_tunnel_config_record_route {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::EnableRecordRoute
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    set parentHandle $switchToValue(handle)
    set switchValue $EnableRecordRoute($parentHandle)
       if {[string first "ingress" [string tolower $handleVar]] >= 0} {
        if {[catch {::sth::sthCore::invoke stc::config $handleVar "-EnableRecordRoute $switchValue"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
            return $FAILURE
        }
    } elseif {[string first "egress" [string tolower $handleVar]] >= 0} {
                set rro_state 0
                foreach {item value} $::sth::Rsvp::switchToValue(optional_args) {
                        switch -- $item {
                                -rro_list_ipv4 { set rro_list_ipv4 $value } \
                                -rro_list_label { set rro_list_label $value } \
                                -rro_frr_merge_point { set rro_frr_merge_point $value } \
                                -rro_list_pfxlen { set rro_list_pfxlen $value } \
                                -rro { set rro_state $value }
                        }
                }
                #configure this value only when rro is set to 1.
                if {$rro_state == 1} {
                        if {[llength $rro_list_ipv4] != [llength $rro_list_label] || \
                                [llength $rro_list_ipv4] != [llength $rro_list_pfxlen] || \
                                [llength $rro_list_ipv4] != [llength $rro_frr_merge_point] || \
                                [llength $rro_list_ipv4] != [llength $rro_list_pfxlen]} {
                                set errorText "Internal Command Error \
                                        while configuring emulation_rsvp_tunnel_config_record_route. List of \
                                        rro_list_ipv4, rro_list_label, rro_frr_merge_point, and rro_list_pfxlen must be of equal size."
                                ::sth::sthCore::processError returnKeyedList $errorText 
                                return -code error "Error: $errorText" 
                        }
                        set index 0
                        for {set index 0} {$index < [llength $rro_list_ipv4]} {incr index} {
                                if {[catch {set RsvpIpv4LsrParams($index) [::sth::sthCore::invoke stc::create RsvpIpv4LsrParams -under $handleVar "-Label [lindex $rro_list_label $index] -FrrMergePoint [lindex $rro_frr_merge_point $index]"]} createStatus]} {
                                        set errorText "Command Error while creating RsvpIpv4LsrParams. Error: $createStatus"
                                        ::sth::sthCore::processError returnKeyedList $errorText 
                                        return -code error "Error: $errorText" 
                                }
                                if {[catch {set Ipv4NetworkBlock($index) [::sth::sthCore::invoke stc::get $RsvpIpv4LsrParams($index) -children-Ipv4NetworkBlock]} getStatus]} {
                                        set errorText "Command Error while getting the network block from $RsvpIpv4LsrParams($index). Error: $getStatus"
                                        ::sth::sthCore::processError returnKeyedList $errorText 
                                        return -code error "Error: $errorText"        
                                } 
                                if {[catch {::sth::sthCore::invoke stc::config $Ipv4NetworkBlock($index) "-StartIpList [lindex $rro_list_ipv4 $index] -PrefixLength [lindex $rro_list_pfxlen $index]"} configStatus]} {
                                        set errorText "Command Error while configuring $Ipv4NetworkBlock($index). Error: $configStatus"
                                        ::sth::sthCore::processError returnKeyedList $errorText 
                                        return -code error "Error: $errorText" 
                                }
                        } 
                }
        }
    return $::sth::sthCore::SUCCESS
}

###/*! \ingroup rsvphelperfuncs
### \fn ProcessTunnelTearDown (str handle, varRef msgName)
###\brief Validates value against Rsvp Tunnel Handle
###
###This procedure tear down a rsvp tunnel in emulation_rsvp_control -mode stop.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Yulin Chen (Ychen)
###*/
###
### ProcessTunnelTearDown (str handle, varRef msgName);
###
proc ::sth::Rsvp::ProcessTunnelTearDown { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg        

    if {[catch {set TunnelInfo [::sth::sthCore::invoke stc::get $handle Name]} getStatus]} {
        set errorMsg $getStatus
        return $FAILURE
    } else {
        if {[llength $TunnelInfo] <= 0} {
            set errorMsg "The tunnel handle is not available rsvp tunnel."
            return $FAILURE
                }
                if {[catch {::sth::sthCore::invoke stc::config $handle "-active FALSE"} getStatus]} {
                    set errorMsg $getStatus
                    return $FAILURE
                }
    }
        return $SUCCESS
}

###/*! \ingroup rsvphelperfuncs
### \fn ProcessTunnelRestore (str handle, varRef msgName)
###\brief Validates value against Rsvp Tunnel Handle
###
###This procedure restore a rsvp tunnel in emulation_rsvp_control -mode start.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Yulin Chen (Ychen)
###*/
###
### ProcessTunnelRestore (str handle, varRef msgName);
###
proc ::sth::Rsvp::ProcessTunnelRestore { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg        

    if {[catch {set TunnelInfo [::sth::sthCore::invoke stc::get $handle Name]} getStatus]} {
        set errorMsg $getStatus
        return $FAILURE
    } else {
        if {[llength $TunnelInfo] <= 0} {
            set errorMsg "The tunnel handle is not available rsvp tunnel."
            return $FAILURE
                }
                if {[catch {::sth::sthCore::invoke stc::config $handle "-active TRUE"} getStatus]} {
                    set errorMsg $getStatus
                    return $FAILURE
                }
    }
        return $SUCCESS
}

###\fn emulation_rsvp_tunnel_config_detour(str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Processes send_detour plr_id avoid_node_id switch.
###
###This procedure implements the send_detour plr_id avoid_node_id switches.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return ::sth::sthCore::FAILURE or ::sth::sthCore::SUCCESS
###
###\warning None
###\author Yulin Chen (ychen)
###*/
###
###emulation_rsvp_tunnel_config_detour (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###
proc ::sth::Rsvp::emulation_rsvp_tunnel_config_detour {switchList returnInfoVarName _hltCmdName _switchName handleVar} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_procfunc
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_ero_mode_fwdmap
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_handle
        
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
        
    set handleValue $handleVar

    if {![info exist switchToValue(send_detour)] } {
        ::sth::sthCore::processError returnKeyedList " Dependent switches -send_detour for switch \
             is/are not specified correctly or missing." {}
        return $FAILURE
    }
        
    if {!$switchToValue(send_detour)} {
        return $SUCCESS
    }
    
    #delete old detour object
    if {[catch {set detourObjectList [::sth::sthCore::invoke stc::get $handleValue -Children-RsvpDetourSubObject]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList " Internal Command Error while getting RsvpDetourSubObject . Error: $errMsg." {}
        return $FAILURE
    } else {
        if { $detourObjectList != ""} {
            foreach detourObject $detourObjectList {
                if {[catch {::sth::sthCore::invoke stc::delete $detourObject}]} {
                    ::sth::sthCore::processError returnKeyedList " Internal Command Error while deleting RsvpDetourSubObject . Error: $errMsg." {}
                    return $FAILURE
                }
            }
        }
    }
    
    #create detour object
    if {[catch {set detourObjectHandle [::sth::sthCore::invoke stc::create RsvpDetourSubObject -under $handleValue]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList " Internal Command Error while creating RsvpDetourSubObject . Error: $errMsg" {}
        return $FAILURE
    }
    
    #config detour object
    if {[info exists switchToValue(plr_id)]} {
        set plrId $switchToValue(plr_id)
        if {[catch {::sth::sthCore::invoke stc::config $detourObjectHandle "-PlrId $plrId"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList " Internal Command Error while config RsvpDetourSubObject . Error: $errMsg" {}
            return $FAILURE
        }
    }
    
    if {[info exists switchToValue(avoid_node_id)]} {
        set avoidNodeId $switchToValue(avoid_node_id)
        if {[catch {::sth::sthCore::invoke stc::config $detourObjectHandle "-AvoidNodeId $avoidNodeId"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList " Internal Command Error while config RsvpDetourSubObject . Error: $errMsg" {}
            return $FAILURE
        }
    }
    
    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvpte_tunnel_control_connect { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvpte_tunnel_control_connect"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
        
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList    
    } else {
        set handlelist $switchToValue(handle)
    }
    
    set errMsg ""
    foreach handle $handlelist {
        if { ![IsRsvpTunnelHandleValid $handle errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Input -handle error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList    
        }
        
        if { ![ProcessTunnelRestore $handle errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList    
        }
    }
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvpte_tunnel_control_tear_down_outbound { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvpte_tunnel_control_tear_down_outbound"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
        
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList    
    } else {
        set handle $switchToValue(handle)
    }
    
    set errMsg ""
    if { ![IsRsvpTunnelHandleValid $handle errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Input -handle error: $errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList    
    }
    if { ![regexp "ingress" [string tolower $handle]]} {
        ::sth::sthCore::processError returnKeyedList "Input -handle is not a outbound RSVP tunnel." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { ![ProcessTunnelTearDown $handle errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: $errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList    
    }
    
    set cmdState $SUCCESS
    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvpte_tunnel_control_tear_down_inbound { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    set _OrigHltCmdName "emulation_rsvp_control"
    set _hltCmdName "emulation_rsvpte_tunnel_control_tear_down_inbound"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName [array names switchToValue]"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
        
    if { ![info exists switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList    
    } else {
        set handle $switchToValue(handle)
    }
    
    set errMsg ""
    if { ![IsRsvpTunnelHandleValid $handle errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Input -handle error: $errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList    
    }
    if { ![regexp "egress" [string tolower $handle]]} {
        ::sth::sthCore::processError returnKeyedList "Input -handle is not a inbound RSVP tunnel." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if { ![ProcessTunnelTearDown $handle errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: $errMsg" {}
        set cmdState $FAILURE
        return $returnKeyedList    
    }
    
    set cmdState $SUCCESS
    return $SUCCESS
}


####################################################
#emulation_rsvp_custom_object_config
####################################################
proc ::sth::Rsvp::emulation_rsvp_custom_object_config_create { returnKeyedListVarName cmdStatusVarName} {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState  

    set RsvpCustomObjectHdl [::sth::sthCore::invoke stc::create RsvpCustomObject -under $::sth::GBLHNDMAP(project)]
    
    set optionValueList [getStcOptionValueList emulation_rsvp_custom_object_config configCustomObject create $RsvpCustomObjectHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpCustomObjectHdl $optionValueList
    }
    
    set cmdState $SUCCESS
    keylset returnKeyedList handle $RsvpCustomObjectHdl   
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Rsvp::emulation_rsvp_custom_object_config_modify { returnKeyedListVarName cmdStatusVarName} {
    variable ::sth::Rsvp::switchToValue
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exists ::sth::Rsvp::switchToValue(handle)]} {
        set result "The -handle is required when \"-mode modify\" is used."
        return $::sth::sthCore::FAILURE
    } else {
        set RsvpCustomObjectHdl $::sth::Rsvp::switchToValue(handle)
    }
    
    set optionValueList [getStcOptionValueList emulation_rsvp_custom_object_config configCustomObject modify $RsvpCustomObjectHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpCustomObjectHdl $optionValueList
    }

    set cmdState $SUCCESS
    return $::sth::sthCore::SUCCESS
}


proc ::sth::Rsvp::emulation_rsvp_custom_object_config_delete { returnKeyedListVarName cmdStatusVarName} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {![info exists ::sth::Rsvp::switchToValue(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        return $returnKeyedList        
    } else {
        set customObjHdl $::sth::Rsvp::switchToValue(handle)
    }
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$customObjHdl"
  
    set cmdState $SUCCESS
    return $returnKeyedList
}
    


proc ::sth::Rsvp::getStcOptionValueList {cmdType modeFunc mode procFuncHandle index} {
    set optionValueList {}
    # extract the stc attribute-value pairs related to the modeFunc as defined in the mode column in rsvpTable.tcl
    foreach item $::sth::Rsvp::sortedSwitchPriorityList {
        foreach {priority opt} $item {
            # make sure the option is supported
            if {![::sth::sthCore::getswitchprop ::sth::Rsvp:: $cmdType $opt supported]} {
                return -code error "\"-$opt\" is not supported"
            }
            if {[string match -nocase [::sth::sthCore::getswitchprop ::sth::Rsvp:: $cmdType $opt mode] "_none_"]} { continue }
            set func [::sth::sthCore::getModeFunc ::sth::Rsvp:: $cmdType $opt $mode]
            # only process options that have <modeFunc> as their mode function
            if {[string match -nocase $func $modeFunc]} {
                # some values need to be processed (or converted) to be stc friendly
                set processFunc [::sth::sthCore::getswitchprop ::sth::Rsvp:: $cmdType $opt procfunc]
                if {[string match -nocase $processFunc "_none_"]} {
                    set stcAttr [::sth::sthCore::getswitchprop ::sth::Rsvp:: $cmdType $opt stcattr]
                    if {[string match -nocase $stcAttr "_none_"]} { continue }
                    if {![catch {::sth::sthCore::getFwdmap ::sth::Rsvp:: $cmdType $opt $::sth::Rsvp::switchToValue($opt)} value]} {
                        lappend optionValueList -$stcAttr $value
                    } else {
                        lappend optionValueList -$stcAttr $::sth::Rsvp::switchToValue($opt)
                    }
                } else {
                    eval lappend optionValueList [$processFunc $procFuncHandle $opt $::sth::Rsvp::switchToValue($opt) $index]
                }
            }
        }
    }
    return $optionValueList
}


proc ::sth::Rsvp::emulation_rsvp_tunnel_config_custom_object {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
   
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
    if {[info exists ::sth::Rsvp::switchToValue(ingress_path_custom_object_list)]} {
        set customObjList $switchToValue(ingress_path_custom_object_list)
        foreach customObj $customObjList {
            stc::config $customObj -PathCustomObject-targets $handleVar
        }
    }
    
    if {[info exists ::sth::Rsvp::switchToValue(ingress_path_tear_custom_object_list)]} {
        set customObjList $switchToValue(ingress_path_tear_custom_object_list)
        foreach customObj $customObjList {
            stc::config $customObj -PathTearCustomObject-targets $handleVar
        }
    }

    if {[info exists ::sth::Rsvp::switchToValue(egress_resv_custom_object_list)]} {
        set customObjList $switchToValue(egress_resv_custom_object_list)
        foreach customObj $customObjList {
            stc::config $customObj -ReservationCustomObject-targets $handleVar
        }
    }

    if {[info exists ::sth::Rsvp::switchToValue(egress_resv_tear_custom_object_list)]} {
    set customObjList $switchToValue(egress_resv_tear_custom_object_list)
        foreach customObj $customObjList {
            stc::config $customObj -ReservationTearCustomObject-targets $handleVar
        }
    }

    return $SUCCESS
}


proc ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_ip_multicast_group {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
   
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
    set mcastGroup $switchToValue(ingress_ip_multicast_group)
    ::sth::sthCore::invoke stc::config $handleVar MemberGroup-targets $mcastGroup

    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_tunnel_params {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
    
    if {[regexp "rsvpegresstunnelparams" [string tolower $handleVar]]} {
        set configList ""
        foreach switchName $switchList {
            set switchValue $switchToValue($switchName)
            set switchAttr $emulation_rsvp_tunnel_config_stcattr($switchName)
            lappend configList -$switchAttr
            lappend configList $switchValue
        }
        ::sth::sthCore::invoke stc::config $handleVar $configList
    }

    return $SUCCESS
}

proc ::sth::Rsvp::emulation_rsvp_tunnel_config_gmpls_params {switchList returnInfoVarName _hltCmdName _switchName handleVar} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcobj
    variable ::sth::Rsvp::emulation_rsvp_tunnel_config_stcattr
    
    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set gmplsHnd [::sth::sthCore::invoke stc::get $handleVar -children-RsvpGmplsParams]
    if {$gmplsHnd == ""} {
        set gmplsHnd [::sth::sthCore::invoke stc::create RsvpGmplsParams -under $handleVar]
    }
    
    set configList ""
    foreach switchName $switchList {
        set switchValue $switchToValue($switchName)
        set switchAttr $emulation_rsvp_tunnel_config_stcattr($switchName)
        if { [regexp "RsvpGmplsParams" $emulation_rsvp_tunnel_config_stcobj($switchName)] } {
            lappend configList -$switchAttr
            if {![catch {::sth::sthCore::getFwdmap ::sth::Rsvp:: $_hltCmdName $switchName $switchValue} value]} {
                lappend configList $value
            } else {
                lappend configList $switchValue
            }
        }
    }
    ::sth::sthCore::invoke stc::config $gmplsHnd $configList

    return $SUCCESS
}


proc  ::sth::Rsvp::configTunnelSubElements { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList
    upvar 1 $cmdState cmdStatus

    set cmdStatus $SUCCESS
    set _hltCmdName "emulation_rsvp_tunnel_config"
    set myNameSpace "::sth::Rsvp::"
    
    #element_type option mandatory warning message
    if {![info exists switchToValue(element_type)]} {
        ::sth::sthCore::processError returnKeyedList "element_type option missing" {}
        set cmdStatus $FAILURE
        return $returnKeyedList
    }
    
    set elementType $::sth::Rsvp::switchToValue(element_type)
    set mode $::sth::Rsvp::switchToValue(mode)
    set cmd "$myNameSpace$_hltCmdName\_$elementType\_$mode returnKeyedValueList cmdState"

    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedValueList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedValueList
    }

    keylset returnKeyedValueList status $SUCCESS
    return $returnKeyedValueList
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set RsvpSubLspHdl [::sth::sthCore::invoke stc::create RsvpEgressS2lSubLspParams -under $handle]
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_egress_sub_lsp create $RsvpSubLspHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpSubLspHdl $optionValueList
    }
    
    keylset returnKeyedValueList handle $RsvpSubLspHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set RsvpSubLspHdl $::sth::Rsvp::switchToValue(element_handle)
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_egress_sub_lsp modify $RsvpSubLspHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpSubLspHdl $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}

# Egress: Create/modify/delete for egress_sub_lsp_rro
proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_rro_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set RsvpIpLsrHdl [::sth::sthCore::invoke stc::create RsvpIpv4LsrParams -under $handle]
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_egress_sub_lsp_rro create $RsvpIpLsrHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpIpLsrHdl $optionValueList
    }
    
    keylset returnKeyedValueList handle $RsvpIpLsrHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_rro_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set RsvpIpLsrHdl $::sth::Rsvp::switchToValue(element_handle)
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_egress_sub_lsp_rro modify $RsvpIpLsrHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpIpLsrHdl $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_egress_sub_lsp_rro_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}


# Ingress: Create/modify/delete for ingress_p2mp_sub_group
proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_p2mp_sub_group_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set RsvpP2mpSubHdl [::sth::sthCore::invoke stc::create RsvpP2MpSubGroupParams -under $handle]
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_p2mp_sub_group create $RsvpP2mpSubHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpP2mpSubHdl $optionValueList
    }
    
    keylset returnKeyedValueList handle $RsvpP2mpSubHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_p2mp_sub_group_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set RsvpP2mpSubHdl $::sth::Rsvp::switchToValue(element_handle)
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_p2mp_sub_group modify $RsvpP2mpSubHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpP2mpSubHdl $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_p2mp_sub_group_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}


# Ingress: Create/modify/delete for ingress_sub_lsp
proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set RsvpSubLspHdl [::sth::sthCore::invoke stc::create RsvpIngressS2lSubLspParams -under $handle]
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp create $RsvpSubLspHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpSubLspHdl $optionValueList
    }
    
    keylset returnKeyedValueList handle $RsvpSubLspHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set RsvpSubLspHdl $::sth::Rsvp::switchToValue(element_handle)
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp modify $RsvpSubLspHdl 0]
    
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpSubLspHdl $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}


# Ingress ingress_sub_lsp_ero : Create/modify/delete for ingress_sub_lsp_ero
proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set RsvpEroObjHdl [::sth::sthCore::invoke stc::create RsvpIpv4EroObject -under $handle]
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero create $RsvpEroObjHdl 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpEroObjHdl $optionValueList
    }
    
    keylset returnKeyedValueList handle $RsvpEroObjHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set RsvpEroObjHdl $::sth::Rsvp::switchToValue(element_handle)
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero modify $RsvpEroObjHdl 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $RsvpEroObjHdl $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}


# Ingress ingress_sub_lsp_ero_sub_obj : Create/modify/delete for ingress_sub_lsp_ero_sub_obj
proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_sub_obj_create { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set handle $::sth::Rsvp::switchToValue(element_handle)
    
    set exRouteParamHdl [::sth::sthCore::invoke stc::create RsvpIpv4ExplicitRouteParams -under $handle]
    set ipv4Hnd [::sth::sthCore::invoke stc::get $exRouteParamHdl -children-Ipv4NetworkBlock]

    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero_sub_obj create $exRouteParamHdl 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $exRouteParamHdl $optionValueList
    }
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero_sub_obj_ipv4 create $ipv4Hnd 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4Hnd $optionValueList
    }
    
    keylset returnKeyedValueList handle $exRouteParamHdl   
    return $::sth::sthCore::SUCCESS
}


proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_sub_obj_modify { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set exRouteParamHdl $::sth::Rsvp::switchToValue(element_handle)
    set ipv4Hnd [::sth::sthCore::invoke stc::get $exRouteParamHdl -children-Ipv4NetworkBlock]

    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero_sub_obj modify $exRouteParamHdl 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $exRouteParamHdl $optionValueList
    }
    
    set optionValueList [getStcOptionValueList emulation_rsvp_tunnel_config config_ingress_sub_lsp_ero_sub_obj_ipv4 modify $ipv4Hnd 0]
    if {[llength $optionValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4Hnd $optionValueList
    }
    
    return $::sth::sthCore::SUCCESS   
}

proc  ::sth::Rsvp::emulation_rsvp_tunnel_config_ingress_sub_lsp_ero_sub_obj_delete { returnKeyedList cmdState } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Rsvp::switchToValue

    upvar 1 $returnKeyedList returnKeyedValueList 
    
    set elementHandle $::sth::Rsvp::switchToValue(element_handle)
    
    ::sth::sthCore::invoke stc::perform delete -ConfigList "$elementHandle"
  
    return $::sth::sthCore::SUCCESS  
}

###}; //ending for namespace comment for doc
