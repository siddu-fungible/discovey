# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

###/*! \ingroup ldphelperfuncs
###\fn createConfigLdpRouter (str args, KeyedListRef returnStringName)
###\brief Create, Config and Start Ldp Router
###
###This procedure create a Ldp router, configure it with the users input and finally starts it.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return FAILURE or SUCCESS
###
###*/
###
###createConfigLdpRouter (str args, KeyedListRef returnStringName);
###


namespace eval ::sth::Ldp {
	set createResultQuery 0
    variable startTimeArray
    variable stopTimeArray
    set TRUE 1
    set FALSE 0
    set FALSE_MINUS_ONE -1
}



###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_config_enable (str args)
###\brief Process \em -mode switch with value \em enable for emulation_ldp_config cmd
###
###This procedure execute the emulation_ldp_config command when the mode is enable. It will create ldp sessions based on the \em -count switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with ldp handles
###
###
###*/
###
###emulation_ldp_config_create (str args);
###

proc ::sth::Ldp::emulation_ldp_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_create"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	set stepError $::sth::Ldp::FALSE
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"


	if {[::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(port_handle)]} {
		set portHandle $::sth::Ldp::emulation_ldp_config_user_input_args_array(port_handle)
        
		if {![::sth::sthCore::IsPortValid $portHandle msg]} {
		    ::sth::sthCore::log debug "Invalid Value of port_handle"
		    ::sth::sthCore::sthError -errno 23 -argslist "$portHandle -port_handle" -keyedlistvar returnKeyedList
		    set cmdState $FAILURE
		    return $returnKeyedList
		}
	    
		#setup global address/step/id params, put return value in 'device'
		if {[catch {set ret [set device [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-deviceaddroptions]]} error]} {
		    ::sth::sthCore::processError returnKeyedList "stc::get Failed: $error" {}
		    return $returnKeyedList 
		}
		#setup ethernet mac address start
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(mac_address_init)]} { 
		    set deviceSettings "-NextMac $::sth::Ldp::emulation_ldp_config_user_input_args_array(mac_address_init)" 
			::sth::sthCore::invoke stc::config $device $deviceSettings
		}
		
		if {![::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(count)]} {
		    set ::sth::Ldp::emulation_ldp_config\_user_input_args_array(count) 1
		} else {
		    set IpStepSwitchList {intf_ip_addr_step intf_ip_addr remote_ip_addr_step remote_ip_addr gateway_ip_addr_step gateway_ip_addr loopback_ip_addr_step loopback_ip_addr lsr_id_step lsr_id\
			intf_ipv6_addr_step intf_ipv6_addr  link_local_ipv6_addr_step link_local_ipv6_addr  gateway_ipv6_addr_step gateway_ipv6_addr  ipv6_router_id_step ipv6_router_id  remote_ipv6_addr_step remote_ipv6_addr}
		}
        
		for {set i 0} {$i < $::sth::Ldp::emulation_ldp_config_user_input_args_array(count)} {incr i} {
		    #process the user input and set the value of switches accordingly.
		    if {$i > 0} {
			::sth::sthCore::log debug "Updating values of switches, if required, based on the step input to create LDP router number:$i."
			::sth::sthCore::log debug "Updating local and remote address for ipVersion:4 for LDP router number:$i."
		
			foreach {stepVal addr} $IpStepSwitchList {
				set version 4
				if {[regexp -nocase "v6" $addr]} {
					set version 6
				}
				if {[::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($stepVal)] && [::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($addr)]} {
				    if {![::sth::sthCore::isValidIpStepValue $version $::sth::Ldp::emulation_ldp_config_user_input_args_array($stepVal)]} {
					::sth::sthCore::processError returnKeyedList "Error with invalid IP step, when executing -$stepVal" {}
					set stepError $::sth::Ldp::TRUE
					break
				    }
				    set newIpAddress [::sth::sthCore::updateIpAddress $version $::sth::Ldp::emulation_ldp_config_user_input_args_array($addr) $::sth::Ldp::emulation_ldp_config_user_input_args_array($stepVal) 1]
				    ::sth::sthCore::log debug "LDP router:$i The new Ipv$version Value for $addr is $newIpAddress."
				    set ::sth::Ldp::emulation_ldp_config_user_input_args_array($addr) $newIpAddress
				} else {
				    ::sth::sthCore::log warn "$addr and $stepVal should be present to use step functionality"
				}
			}
		
			::sth::sthCore::log debug "LDP router:$i Check the status of other step switches."
			foreach {stepMode switchToBeStepped stepSwitch} {vlan_id_mode vlan_id vlan_id_step  vlan_outer_id_mode vlan_outer_id vlan_outer_id_step} {
			    ::sth::sthCore::log debug "LDP router:$i Checking switch $stepMode : $switchToBeStepped : $stepSwitch."
			    if {[::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($stepMode)]} {
				::sth::sthCore::log debug "LDP router:$i Switch found in user input. Now checking the value:$::sth::Ldp::emulation_ldp_config_user_input_args_array($stepMode) against increment"
				if {[string equal $::sth::Ldp::emulation_ldp_config_user_input_args_array($stepMode) "increment"]} {
				    if {[::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($stepSwitch)]} {
					#update the value fo the switch with the specified stepValue
					set newSwitchToBeSteppedValue ""
					if {![::sth::sthCore::stepSwitchValue $::sth::Ldp::emulation_ldp_config_user_input_args_array($switchToBeStepped) $::sth::Ldp::emulation_ldp_config_user_input_args_array($stepSwitch) 1 newSwitchToBeSteppedValue]} {
					    ::sth::sthCore::log debug "Error occured while stepping the value of switch:$switchToBeStepped"
					}
					::sth::sthCore::log debug "LDP router:$i The new Value for $switchToBeStepped is $newSwitchToBeSteppedValue."
					set ::sth::Ldp::emulation_ldp_config_user_input_args_array($switchToBeStepped) $newSwitchToBeSteppedValue
				    } else {
					::sth::sthCore::log warn "No Step Value detected for switch:$switchToBeStepped"
				    }
				}
			    }
			}
		
		    }
		
		    if {$stepError} {
			set cmdState $FAILURE
			return $returnKeyedList
		    }
			     
		    #Execute the createConfigStartLdpRouter cmd and check result
		    set cmdFailed $::sth::Ldp::TRUE
		    ::sth::Ldp::createConfigLdpRouter $userInput returnKeyedList cmdFailed $i
		    if {$cmdFailed} {
			::sth::sthCore::log error "Error occured while creating/configuring the LDP router number $i"
			set cmdState $FAILURE
		    } else {
			::sth::sthCore::log debug "Successfully created/configured the LDP router number {$i} $returnKeyedList "
		    }
		}
	} elseif {[::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)]} {
		#RXu: Enable LDP under an existing device
		#puts "Pleasse be noted LDP protocol will be enable in the Device $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)"
        
		#Execute the createConfigStartLdpRouter cmd and check result
		set cmdFailed $::sth::Ldp::TRUE
		::sth::Ldp::createConfigLdpRouter $userInput returnKeyedList cmdFailed 0
		if {$cmdFailed} {
		    ::sth::sthCore::log error "Error occured while creating/configuring the LDP router number"
		    set cmdState $FAILURE
		} else {
		    ::sth::sthCore::log debug "Successfully created/configured the LDP under $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)] $returnKeyedList "
		}
	} else {
		::sth::sthCore::log error "port_handle / handle needed when creating Ldp router"
		set cmdState $FAILURE
		return $returnKeyedList
	}
	#RXu: Enable LDP under an existing device end    
	if {$cmdFailed > $::sth::Ldp::FALSE} {
		set cmdError $::sth::Ldp::TRUE
		set cmdState $FAILURE
		if {[catch {set handleList [keylget returnKeyedList handle]}]} {
			#do nothing
		}
		foreach deleteHandle $handleList {
			if {[catch {::sth::sthCore::invoke stc::delete $deleteHandle} deleteStatus]} {
				::sth::sthCore::log error "Error when trying to delete the handles $handleList"
			}
		}
		if {[catch {keyldel returnKeyedList handle}]} {
			# do nothing
		}
	}
	if {$cmdFailed > $::sth::Ldp::FALSE} {
		set cmdState $FAILURE
		return $returnKeyedList
	} else {
		set cmdState $SUCCESS
		return $returnKeyedList
	}
}


###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_config_modify (str args)
###\brief Process \em -mode switch with value \em enable for emulation_ldp_config cmd
###
###This procedure executes the emulation_ldp_config command when the mode is modify. It will modify ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_config_modify (str args);
###

proc ::sth::Ldp::emulation_ldp_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE



	
	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_modify"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandle $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)
		::sth::sthCore::log debug "__VALIDATE__: Validate value of ldp router handle"
		if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
			::sth::sthCore::log debug "Invalid Value of handle"
			#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
			set cmdState $FAILURE
			return $returnKeyedList 			
		}
	}

	#Configure the created LDP router with user input
    ::sth::sthCore::log debug "Processing the switches for command:$_hltCmdName"
    
    set objList {LdpRouterConfig Ipv4If Ipv6If Router VlanIf VlanIf_Outer Aal5If}
	array set cmdArray {
    	LdpRouterConfig ""
    	Ipv4If ""
    	Ipv6If ""
	Ipv6If_Link_Local ""
    	Router ""
    	VlanIf ""
	VlanIf_Outer ""
	Aal5If ""
    }
	array set hdlArray {
    	ldpRouterConfig ""
    	Ipv4If ""
    	Ipv6If ""
	Ipv6If_Link_Local ""
    	Router ""
    	VlanIf ""
	VlanIf_Outer ""
	Aal5If ""
    }
    
     #add for gre. get the greipif
     set topIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -TopLevelIf-targets]
     set checkIf [::sth::sthCore::invoke stc::get [lindex $topIf 0] -StackedOnEndpoint-targets]
     if {[string compare -nocase -length 5 $checkIf "greif"] == 0} {
	set greIpIf $checkIf
     }
     
    if {[catch {set hdlArray(LdpRouterConfig) [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-LdpRouterConfig]} getStatus]} {
		::sth::sthCore::log error "Unable to fetch LdpRouterConfig Handle. Error: $getStatus"
	} else {
		::sth::sthCore::log debug "Ipv4If handle to be configured:$hdlArray(LdpRouterConfig)"	
	}
		
    if {[catch {set hdlArray(Ipv4If) [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		::sth::sthCore::log error "Unable to fetch Ipv4If Handle. Error: $getStatus"
	} else {
		#add for gre case. delete the greipif from the list
		if {[info exists greIpif] } {
			set ix [lsearch -exact $hdlArray(Ipv4If) $greIpif]
			if {$ix >=0 } {
				set hdlArray(Ipv4If) [lreplace $hdlArray(Ipv4If) $ix $ix]
			}
		}
		::sth::sthCore::log debug "Ipv4If handle to be configured:$hdlArray(Ipv4If)"	
	}
	if {[catch {set hdlArray(Ipv6If) [lindex [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv6If] 0]
		set hdlArray(Ipv6If_Link_Local) [lindex [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv6If] 1]} getStatus]} {
		::sth::sthCore::log error "Unable to fetch Ipv6If Handle. Error: $getStatus"
	} else {
		#add for gre case. delete the greipif from the list
		if {[info exists greIpif] } {
			set ix [lsearch -exact $hdlArray(Ipv6If) $greIpif]
			if {$ix >=0 } {
				set hdlArray(Ipv4If) [lreplace $hdlArray(Ipv6If) $ix $ix]
			}
		}
		::sth::sthCore::log debug "Ipv6If handle to be configured:$hdlArray(Ipv6If)"	
	}		
	
	if {[catch {set hdlArray(Aal5If) [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Aal5If]} getStatus]} {
		::sth::sthCore::log error "Unable to fetch Aal5If Handle. Error: $getStatus"
	} else {
		::sth::sthCore::log debug "Aal5If handle to be configured:$hdlArray(Aal5If)"	
	}
	
	set hdlArray(Router) $ldpRouterHandle
	
    if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-VlanIf]} getStatus]} {
		::sth::sthCore::log error "Unable to fetch VlanIf Handle. Error: $getStatus"
	} else {
		::sth::sthCore::log debug "VlanIf handle to be configured:$hdlArray(VlanIf)"	
	}
	
	if {[llength $VlanIfHandle] == 2} {
	    lappend hdlArray(VlanIf_Outer) [lindex $VlanIfHandle 0]
	    lappend hdlArray(VlanIf) [lindex $VlanIfHandle 1]
	} else {
	    lappend hdlArray(VlanIf) $VlanIfHandle
	}
	
	#Configure the created Ldp router with user input (options)
	::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
	set userInputList $::sth::Ldp::emulation_ldp_config_user_input_args_array(optional_args)
	#remove the dash before the switch name in optional_args
	for {set i 0} {$i < [expr {[llength $userInputList]/2}]} {incr i} {
		set index [expr {$i*2}]
		set nameNoDash [string range [lindex $userInputList $index] 1 end]
		lset userInputList $index $nameNoDash
	}

	#remove those input switches without processing functions
	set switchWithoutFunc {count handle intf_ip_addr_step gateway_ip_addr_step label_step lsr_id_step mode port_handle remote_ip_addr_step vlan_id_mode vlan_outer_id_mode mandatory_args optional_args\
			ip_version intf_ipv6_addr_step link_local_ipv6_addr_step gateway_ipv6_addr_step ipv6_router_id_step remote_ipv6_addr_step hello_type use_gateway_as_dut_ip_addr use_gateway_as_dut_ipv6_addr authentication_mode password md5_key_id expand}
	foreach switchName $switchWithoutFunc {
		set switchIndex [lsearch $userInputList $switchName]
		if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
			set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
		}
	}

	foreach {switchName switchValue} $userInputList {
		::sth::sthCore::log debug "Trying to process the switch $switchName"
		set switchProcFunc [::sth::sthCore::getModeFunc2 ::sth::Ldp:: emulation_ldp_config $switchName $::sth::Ldp::emulation_ldp_config_user_input_args_array(mode)]
		#if { $switchProcFunc== ""} {
		#	set switchProcFunc "unknownSwitchProcessingInfo"
		#}
		
		#@TODO Change this to pass the value of the handle itself
		set handleSwitchName $ldpRouterHandle
		
		#if processing function is processConfigCmd, append the attribute/value pair to 
		#corresponding array element for processing later
		if {[string equal $switchProcFunc "processConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_config $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_config $switchName stcattr]
			if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_config $switchName $switchValue]} getStatus]} {
				append cmdArray($stcObjName) " -$stcAttrName $attrValue"
			} else {
				append cmdArray($stcObjName) " -$stcAttrName $switchValue"
			}
#			puts "cmdArray=$cmdArray($stcObjName)"
			 
		} else {
			set cmd "::sth::Ldp::$switchProcFunc {$switchValue} returnKeyedList $_hltCmdName $switchName switchToOutput $handleSwitchName"
			::sth::sthCore::log debug "CMD to Process: $cmd "
			set cmdResult [eval $cmd]
			::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
			if {$cmdResult == $::sth::sthCore::FAILURE} {
				set cmdFailed $::sth::Ldp::TRUE
				set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch $switchName with Value $switchValue"
				::sth::sthCore::log error "$logStatus"
				break
			}
		}
	}

	#process all switches handled by processConfigCmd
	#set cmdResult [eval ::sth::sthCore::genericConfig hdlArray cmdArray]
	foreach objName $objList {
#		puts "objName=$objName handle=$hdlArray($objName) cmd=$cmdArray($objName)"
		if {($cmdArray($objName) != "") & ([string length $hdlArray($objName)] > 3)} {
			set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
			#puts $cmd
			if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
			    ::sth::sthCore::log debug "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus"
			    set cmdFailed $::sth::Ldp::TRUE
			    set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
				::sth::sthCore::log error "$logStatus"
			} else {
		    	::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
			}
		}
	}
	
	 ###add for gre. config the gre objects here
	if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(tunnel_handle)] != 0} {
               set cmdPass [::sth::configGreStack $::sth::Ldp::emulation_ldp_config_user_input_args_array(tunnel_handle) $ldpRouterHandle]
        }
        
        #enable/disable BFD
        if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(bfd_registration)]} {
                configBfdRegistration $ldpRouterHandle $::sth::Ldp::emulation_ldp_config_user_input_args_array(mode) ::sth::Ldp::emulation_ldp_config_user_input_args_array
        }

	if {[::info exists cmdError]} {
		set cmdState $FAILURE
		return $returnKeyedList
	} else {
		set cmdState $SUCCESS
		return $returnKeyedList
	}		
}



#Rxu: enable LDP after disable it
proc ::sth::Ldp::emulation_ldp_config_active { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_active "
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	set ldpRouterHandles $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)
	set lspHandles ""
	foreach ldpRouterHandle $ldpRouterHandles {
		if {[catch {set lspHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-LdpRouterConfig]} err]} {
			::sth::sthCore::processError returnKeyedList "The router handle $ldpRouterHandle is invalid for LDP : $err" {}
			return $::sth::sthCore::FAILURE
		}
		
		if {[catch {::sth::sthCore::invoke stc::config $lspHandle "-Active TRUE -LocalActive TRUE"} err]} {
			::sth::sthCore::processError returnKeyedList "Failed to active  LDP protocol: $err" {}
			return $::sth::sthCore::FAILURE
		}
		lappend lspHandles $lspHandle
	}
	
	keylset returnKeyedList lsp_handle $lspHandle
	keylset returnKeyedList handle $ldpRouterHandle
	keylset returnKeyedList handles $ldpRouterHandle
	set errOccured $::sth::Ldp::FALSE
	set cmdState $::sth::sthCore::SUCCESS
	return $returnKeyedList
}


#Rxu: disable LDP instead of deleting it
proc ::sth::Ldp::emulation_ldp_config_inactive { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_inactive"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	set ldpRouterHandles $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)
	
	set lspHandles ""
	foreach ldpRouterHandle $ldpRouterHandles {
		if {[catch {set lspHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-LdpRouterConfig]} err]} {
			::sth::sthCore::processError returnKeyedList "The router handle $ldpRouterHandle is invalid for LDP : $err" {}
			return $::sth::sthCore::FAILURE
		}
	    
		if {[catch {::sth::sthCore::invoke stc::config $lspHandle "-Active FALSE -LocalActive FALSE"} err]} {
			::sth::sthCore::processError returnKeyedList "Failed to inactive LDP protocol: $err" {}
			return $::sth::sthCore::FAILURE
		}
		lappend lspHandles $lspHandle
	}
	
	keylset returnKeyedList lsp_handle $lspHandles
	keylset returnKeyedList handle $ldpRouterHandles
	keylset returnKeyedList handles $ldpRouterHandles
	set errOccured $::sth::Ldp::FALSE
	set cmdState $::sth::sthCore::SUCCESS
	return $returnKeyedList
}




###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_config_delete (str args)
###\brief Process \em -mode switch with value \em delete for emulation_ldp_config cmd
###
###This procedure executes the emulation_ldp_config command when the mode is delete. It will delete ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_config_delete (str args);
###

proc ::sth::Ldp::emulation_ldp_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE



	
	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_delete"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandleList $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)
		::sth::sthCore::log debug "__VALIDATE__: Validate value of ldp router handle"
		foreach ldpRouterHandle $ldpRouterHandleList {
		if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
			::sth::sthCore::log debug "Invalid Value of handle:$ldpRouterHandle"
			#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
			set cmdState $FAILURE
			return $returnKeyedList 			
		}
		}
	}
	
	#call delete on ldp router handle
	foreach ldpRouterHandle $ldpRouterHandleList {
	if {[catch {::sth::sthCore::invoke stc::delete $ldpRouterHandle} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting LDP router $ldpRouterHandle. Error: $eMsg" {}       
		set cmdState $FAILURE
		return $returnKeyedList		
	}
	}
	set cmdState $SUCCESS
	return $returnKeyedList
}

proc ::sth::Ldp::emulation_ldp_config_activate {userInput returnKeyedListVarName cmdStatusVarName} {
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    array set mainDefaultAry {}
    set opList "bfd_registration hello_type hello_version adjacency_version graceful_restart egress_label_mode label_adv label_start transport_tlv_mode use_gateway_as_dut_ip_addr use_gateway_as_dut_ipv6_addr remote_ip_addr remote_ip_addr_step remote_ipv6_addr remote_ipv6_addr_step"
    foreach key $opList {
        if {[info exists ::sth::Ldp::emulation_ldp_config_default($key)]} {
            set value $::sth::Ldp::emulation_ldp_config_default($key)
            set mainDefaultAry($key) $value
        }
    }
    
    if {[::sth::sthCore::IsInputOpt remote_ip_addr ] || [::sth::sthCore::IsInputOpt remote_ip_addr_step]} {
	    set mainDefaultAry(use_gateway_as_dut_ip_addr) "true"
    }
    
    if {[::sth::sthCore::IsInputOpt remote_ipv6_addr ] || [::sth::sthCore::IsInputOpt remote_ipv6_addr_step]} {
	    set mainDefaultAry(use_gateway_as_dut_ipv6_addr) "true"
    }

    set opList "authentication_mode password md5_key_id"
    foreach key $opList {
        if {[info exists ::sth::Ldp::emulation_ldp_config_default($key)]} {
            set value [set ::sth::Ldp::emulation_ldp_config_default($key)]
            set authDefaultAry($key) $value
        }
    }

    set mOptionList ""
    foreach idx [array names mainDefaultAry] {
        if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($idx)]} {
            if {[info exists ::sth::Ldp::emulation_ldp_config_$idx\_fwdmap($::sth::Ldp::emulation_ldp_config_user_input_args_array($idx))]} {
                set value [set ::sth::Ldp::emulation_ldp_config_$idx\_fwdmap($::sth::Ldp::emulation_ldp_config_user_input_args_array($idx))]
                set ::sth::Ldp::emulation_ldp_config_user_input_args_array($idx) $value
            }
            set mainDefaultAry($idx) $::sth::Ldp::emulation_ldp_config_user_input_args_array($idx)
        }
        if {[string equal $mainDefaultAry($idx) "_none_"]} { continue }
        regsub -all {[.]} [set ::sth::Ldp::emulation_ldp_config_stcattr($idx)] "" stcAttr
		#special handling for remote_as remote_as_step
		if {[string equal $stcAttr DutAsNum] ||
			[string equal $stcAttr DutAsNumStep]} {
			regsub -all {DutAsNum} $stcAttr "DutAs" stcAttr
		}
		
        append mOptionList " -$stcAttr $mainDefaultAry($idx)"
    }

    set authOptionList ""
    foreach idx [array names authDefaultAry] {
        if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($idx)]} {
            set authDefaultAry($idx) $::sth::Ldp::emulation_ldp_config_user_input_args_array($idx)
        }
        if {[string equal $authDefaultAry($idx) "_none_"]} { continue }
        append authOptionList " -$::sth::Ldp::emulation_ldp_config_stcattr($idx) $authDefaultAry($idx)"
    }
    
    if {![info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the activate mode of emulation_ldp_config" {}
	keylset returnKeyedList status $::sth::sthCore::FAILURE
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    } else {
		set ldpGenHnd [::sth::sthCore::invoke stc::create LdpDeviceGenProtocolParams -under $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle) $mOptionList]
	
		set authHnd [::sth::sthCore::invoke stc::get $ldpGenHnd -children-LdpAuthenticationParams]
		if {$authHnd == ""} {
			set authHnd [::sth::sthCore::invoke stc::create LdpAuthenticationParams -under $ldpGenHnd]
		}
		if { $authOptionList != "" } {
			::sth::sthCore::invoke stc::config $authHnd $authOptionList
		}
		
		if {[::sth::sthCore::IsInputOpt expand] && $::sth::Ldp::emulation_ldp_config_user_input_args_array(expand) == "false"} {
			keylset returnKeyedList handle_list ""
			keylset returnKeyedList handle ""
			keylset returnKeyedList handles ""
		} else {
			array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)]
			keylset returnKeyedList handle $return(-ReturnList)
			keylset returnKeyedList handles $return(-ReturnList)
			keylset returnKeyedList handle_list $return(-ReturnList)
		}
    }

    keylset returnKeyedList status $::sth::sthCore::SUCCESS
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_control_start (str args)
###\brief Process \em -mode switch with value \em start for emulation_ldp_control cmd
###
###This procedure executes the emulation_ldp_control command when the mode is start. It will start ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_control_start (str args);
###
proc ::sth::Ldp::emulation_ldp_control_start { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
    variable startTimeArray

	
	set _OrigHltCmdName "emulation_ldp_control"
	set _hltCmdName "emulation_ldp_control_start"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	##judge port_handle and get the ldprouter handle
	if {[::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)]} {
		set portlist $::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)
		set routerlist ""
		foreach port $portlist {
			set routers [stc::get $port -affiliationport-Sources]
			foreach router $routers {
				if {$router ne ""} {
					set ldprouterconfig [stc::get $router -children-ldprouterconfig]
					if {$ldprouterconfig ne ""} {
						set routerlist [concat $routerlist $router]
					}
				}
			}
		}
		if {$routerlist ne ""} {
			set ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle) $routerlist
		}
	}
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandleList $::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)
		::sth::sthCore::log debug "__VALIDATE__: Validate value of ldp router handle"
		
		foreach ldpRouterHandle $ldpRouterHandleList {
			if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
				::sth::sthCore::log debug "Invalid Value of handle"
				#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
				set cmdState $FAILURE
				return $returnKeyedList 			
			}
		}
	}
	
	# subscribe resultdataset
	if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Ldp:: LdpRouterConfig LdpRouterResults returnKeyedList]} {
		::sth::sthCore::processError returnKeyedList "Error subscribing the Ldp router result data set"
		return $returnKeyedList
	}
    
    set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
    ::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId LdpRouterConfig -ResultClassId LdpLspResults]
    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
	
	#call start on Ldp router handle
	foreach ldpRouterHandle $ldpRouterHandleList {
		if {[catch {array set ret [::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $ldpRouterHandle]} eMsg]} {
			::sth::sthCore::processError returnKeyedList "Internal Command Error while starting LDP router $ldpRouterHandle. Error: $eMsg" {}       
			set cmdState $FAILURE
			return $returnKeyedList 
		}
        set startTimeArray($ldpRouterHandle) $ret(-StartTime)	
	}
	set cmdState $SUCCESS  
	return $returnKeyedList	
}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_control_stop (str args)
###\brief Process \em -mode switch with value \em stop for emulation_ldp_control cmd
###
###This procedure executes the emulation_ldp_control command when the mode is stop. It will stop ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_control_stop (str args);
###

proc ::sth::Ldp::emulation_ldp_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
    variable stopTimeArray

	set _OrigHltCmdName "emulation_ldp_control"
	set _hltCmdName "emulation_ldp_control_stop"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	##judge port_handle and get the ldprouter handle
	if {[::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)]} {
		set portlist $::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)
		set routerlist ""
		foreach port $portlist {
			set routers [stc::get $port -affiliationport-Sources]
			foreach router $routers {
				if {$router ne ""} {
					set ldprouterconfig [stc::get $router -children-ldprouterconfig]
					if {$ldprouterconfig ne ""} {
						set routerlist [concat $routerlist $router]
					}
				}
			}
		}
		if {$routerlist ne ""} {
			set ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle) $routerlist
		}
	}
	
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandleList $::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)
		::sth::sthCore::log debug "__VALIDATE__: Validate value of ldp router handle"
		
		foreach ldpRouterHandle $ldpRouterHandleList {
			if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
				::sth::sthCore::log debug "Invalid Value of handle"
				#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
				set cmdState $FAILURE
				return $returnKeyedList 			
			}
		}
	}
	
	#call start on Ldp router handle
	foreach ldpRouterHandle $ldpRouterHandleList {
		if {[catch {array set ret [::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $ldpRouterHandle]} eMsg]} {
			::sth::sthCore::processError returnKeyedList "Internal Command Error while stopping LDP router $ldpRouterHandle. Error: $eMsg" {}      
			set cmdState $FAILURE
			return $returnKeyedList 
		}
        set stopTimeArray($ldpRouterHandle) $ret(-EndTime) 	
	}
	set cmdState $SUCCESS  
	return $returnKeyedList	
}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_control_restart (str args)
###\brief Process \em -mode switch with value \em restart for emulation_ldp_control cmd
###
###This procedure executes the emulation_ldp_control command when the mode is restart. It will restart ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_control_restart (str args);
###

proc ::sth::Ldp::emulation_ldp_control_restart { userInput returnKeyedListVarName cmdStatusVarName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set _OrigHltCmdName "emulation_ldp_control"
	set _hltCmdName "emulation_ldp_control_restart"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	##judge port_handle and get the ldprouter handle
	if {[::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)]} {
		set portlist $::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)
		set routerlist ""
		foreach port $portlist {
			set routers [stc::get $port -affiliationport-Sources]
			foreach router $routers {
				if {$router ne ""} {
					set ldprouterconfig [stc::get $router -children-ldprouterconfig]
					if {$ldprouterconfig ne ""} {
						set routerlist [concat $routerlist $router]
					}
				}
			}
		}
		if {$routerlist ne ""} {
			set ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle) $routerlist
		}
	}
	
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandleList $::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)
		::sth::sthCore::log debug "_VALIDATE__: Validate value of ldp router handle"
		
		foreach ldpRouterHandle $ldpRouterHandleList {
			if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
				::sth::sthCore::log debug "Invalid Value of handle"
				#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
				set cmdState $FAILURE
				return $returnKeyedList 			
			}
		}
	}
	# subscribe resultdataset
	if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Ldp:: LdpRouterConfig LdpRouterResults returnKeyedList]} {
		::sth::sthCore::processError returnKeyedList "Error subscribing the LDP result data set"
		return $returnKeyedList
	}


	#call start on Ldp router handle
	foreach ldpRouterHandle $ldpRouterHandleList {
        if {[catch {set ldprouterconfig [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldprouterconfig]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch ldprouterconfig Handle. Error: $getStatus"
        } 
        if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $ldprouterconfig -EnableGracefulRestart]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch ldprouterconfig Handle. Error: $getStatus"
        }
        if {$gracefulRestart} {
            if {[catch {::sth::sthCore::invoke stc::perform LdpRestartRouter -RouterList $ldprouterconfig} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Command Error while restarting LDP router $ldpRouterHandle. Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
        } else {
            #call stop on Ldp router handle
            if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $ldpRouterHandle} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting LDP router $ldpRouterHandle. Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            #call sleep for 5 seconds
            if {[catch {::sth::sthCore::invoke "stc::sleep 5"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while sleeping for 5 sec. Error: $eMsg" {}          
                set cmdState $FAILURE
                return $returnKeyedList
            }	
            #then start the router
            if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $ldpRouterHandle} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting LDP router $ldpRouterHandle. Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
        }
	}
		
	set cmdState $SUCCESS  
	return $returnKeyedList	
}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_control_graceful_restart (str args)
###\brief Process \em -mode switch with value \em graceful_restart for emulation_ldp_control cmd
###
###This procedure executes the emulation_ldp_control command when the mode is graceful_restart. It will gracefully restart ldp session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###*/
###
###emulation_ldp_control_graceful_restart (str args);
###

#by yulin chen 27/03/08
proc ::sth::Ldp::emulation_ldp_control_graceful_restart { userInput returnKeyedListVarName cmdStatusVarName } {

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
       
	set _OrigHltCmdName "emulation_ldp_control"
	set _hltCmdName "emulation_ldp_control_graceful_restart"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
        
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
        
        set args $userInput
        ##judge port_handle and get the ldprouter handle
	if {[::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)]} {
		set portlist $::sth::Ldp::emulation_ldp_control_user_input_args_array(port_handle)
		set routerlist ""
		foreach port $portlist {
			set routers [stc::get $port -affiliationport-Sources]
			foreach router $routers {
				if {$router ne ""} {
					set ldprouterconfig [stc::get $router -children-ldprouterconfig]
					if {$ldprouterconfig ne ""} {
						set routerlist [concat $routerlist $router]
					}
				}
			}
		}
		if {$routerlist ne ""} {
			set ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle) $routerlist
		}
	}
	
	#Check if ldp router handle is valid
	if {![::info exists ::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)]} {
		::sth::sthCore::processError returnKeyedList "handle switch with valid value is not provided." {}
		set cmdState $FAILURE
		return $returnKeyedList       
	} else {
		set ldpRouterHandleList $::sth::Ldp::emulation_ldp_control_user_input_args_array(handle)
		::sth::sthCore::log debug "_VALIDATE__: Validate value of ldp router handle"
		
		foreach ldpRouterHandle $ldpRouterHandleList {
			if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
				::sth::sthCore::processError returnKeyedList "Invalid Value of handle" {} 
				#::sth::sthCore::sthError -errno 23 -argslist "$ldpHandle -handle" -keyedlistvar returnKeyedList
				set cmdState $FAILURE
				return $returnKeyedList 			
			}
		}
	}
        
        #chenck if Ldp Router can be graceful restart
        foreach ldpRouterHandle $ldpRouterHandleList {
                if {[catch {set ldprouterconfig [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldprouterconfig]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch ldprouterconfig Handle. Error: $getStatus"
                    set cmdState $FAILURE
                    return $returnKeyedList
                } 
                if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $ldprouterconfig -EnableGracefulRestart]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch ldprouterconfig Handle. Error: $getStatus"
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                #call graceful start on Ldp router handle
                if {$gracefulRestart} {
                        if {[catch {::sth::sthCore::invoke stc::perform LdpRestartRouter -RouterList $ldprouterconfig} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Command Error while graceful restarting LDP router $ldpRouterHandle. Error: $eMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        }                           
                } else {
                        ::sth::sthCore::processError returnKeyedList "Ldp Router $ldpRouterHandle havenot been enable to graceful restart,cannot graceful restart"
                        set cmdState $FAILURE
                        return $returnKeyedList     
                }
        }
        
	# subscribe resultdataset
	if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Ldp:: LdpRouterConfig LdpRouterResults returnKeyedList]} {
		::sth::sthCore::processError returnKeyedList "Error subscribing the LDP result data set"
                set cmdState $FAILURE
		return $returnKeyedList
	}
		
	set cmdState $SUCCESS  
	return $returnKeyedList	
}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_info_Generic (str args)
###\brief Process \em -mode switch with value \em stats,settings for emulation_ldp_info cmd
###
###This procedure execute the emulation_ldp_info command when the mode is stats or settings. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/
###
###emulation_ldp_info_Generic (str args);
###
#by yulin chen 28/04/08
proc ::sth::Ldp::emulation_ldp_info_Generic { userInput returnKeyedListVarName cmdStatusVarName modeVal } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
  
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    #for -mode stats, switch -elapsed_time
    variable startTimeArray
    variable stopTimeArray

    set _OrigHltCmdName "emulation_ldp_info"
    set _hltCmdName "emulation_ldp_info_$modeVal"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
        
    set returnKeyName ""
    array set array_hLdpResult ""
	
    #check the validation of the ldp session handle
    if {[::info exists ::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)]} {
	set ldpRouterHandle $::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)
	    if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
		::sth::sthCore::processError returnKeyedList "Error: invalid LDP router handle $ldpRouterHandle" {}
		set cmdState $FAILURE
		return $returnKeyedList
	    }	
    } else {
	set cmdState $FAILURE
	return $returnKeyedList
    }
        
    #get result data handle
    if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldpRouterConfig]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterConfig handle from $ldpRouterHandle. Error: $getStatus" {}
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	if {[catch {set ldpRouterResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpRouterResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}
	if {[catch {set ldpLspResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpLspResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpLspResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}	
    }
    
    if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4If from $ldpRouterHandle. Error: $getStatus" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }

    #get num_lsp_setup for -mode stats  
    if {$modeVal == "stats"} {
        if {[catch {set lsp_pool_handle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-ipv4prefixlsp]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4PrefixLsp handle from $ldpRouterConfigHandle, $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
	if {[catch {set vc_lsp_pool_handle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-vclsp]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4PrefixLsp handle from $ldpRouterConfigHandle, $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
        set num_lsp_setup 0
        set lsp_pool_handle [concat $lsp_pool_handle $vc_lsp_pool_handle]
        foreach prefixlsp $lsp_pool_handle  {
            if {[string match "*prefixlsp*" $prefixlsp]} {
                if {[catch {set ipv4networkblock [::sth::sthCore::invoke stc::get $prefixlsp -children-ipv4networkblock]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Error while fetching ipv4networkblock handle from $prefixlsp, $getStatus" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                if {[catch {set net_count [::sth::sthCore::invoke stc::get $ipv4networkblock -NetworkCount]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Error while fetching NetworkCount handle from $ipv4networkblock, $getStatus" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            } elseif {[string match "vclsp*" $prefixlsp]} {
                if {[catch {set net_count [::sth::sthCore::invoke stc::get $prefixlsp -VcIdCount]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Error while fetching VcIdCount handle from $prefixlsp, $getStatus" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
            }
            set num_lsp_setup [expr $num_lsp_setup + $net_count]
        #end of foreach
        }
    #end of if {$modeValue == "stats"}  
    }
    
    set array_hLdpResult(LdpRouterResults) $ldpRouterResultsHandle
    set array_hLdpResult(LdpLspResults) $ldpLspResultsHandle
    set array_hLdpResult(LdpRouterConfig) $ldpRouterConfigHandle
    set array_hLdpResult(Ipv4If) $ipv4ResultIf
        
    #get all func switches
    set all_switch [array names ::sth::Ldp::emulation_ldp_info_mode]
    
    #choose the switches be returned in current mode
    foreach one_switch $all_switch {
        if {[info exist ::sth::Ldp::emulation_ldp_info_mode($one_switch)]} {
            if {[expr [lsearch $::sth::Ldp::emulation_ldp_info_mode($one_switch) "$modeVal"] > -1]} {
                lappend returnKeyName $one_switch
            }       
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    #loop for get switch's mapping stcattr value
    array set returnKL_temp ""
    array set hLdpResult ""
    set switchVal_temp ""
    foreach one_switch $returnKeyName {
        set stcobj $::sth::Ldp::emulation_ldp_info_stcobj($one_switch)
        set stcattr $::sth::Ldp::emulation_ldp_info_stcattr($one_switch)
        #if {[info exists array_hLdpResult($stcobj)]} {
        #    lappend hLdpResult($stcobj) $array_hLdpResult($stcobj)
        #}
        if {[string equal $stcobj "_none_"]} {
                #do nothing                   
        } else {
                #loop for more than one Result handle
                foreach obj_handle $array_hLdpResult($stcobj) {
                        if {[catch {set switchVal [::sth::sthCore::invoke stc::get $obj_handle -$stcattr]} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $$obj_handle, $eMsg"
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                lappend switchVal_temp $switchVal
                        }                    
                }
                #end of foreach obj_handle
        }
        #end of if {[string equal $stcobj "_none_"]} {} else {}
        
        set returnKL_temp($one_switch) $switchVal_temp
        set switchVal_temp ""
    }
    #end of foreach one_switch

    if {$modeVal == "state"} {
        if {$returnKL_temp(session_state) != ""} {
                set a_session_state_temp ""
                foreach session_state_temp $returnKL_temp(session_state) {
                        lappend a_session_state \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info session_state $session_state_temp]
                }
                set returnKL_temp(session_state) $a_session_state
        }
        if {$returnKL_temp(type) != ""} {
                set a_type_temp ""
                foreach type_temp $returnKL_temp(type) {
                        lappend a_type_temp \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info type $type_temp]
                }
                set returnKL_temp(type) $a_type_temp
        }
    } elseif {$modeVal == "settings"} {
        if {$returnKL_temp(label_adv) != ""} {
                set a_label_adv_temp ""
                foreach label_adv_temp $returnKL_temp(label_adv) {
                        lappend a_label_adv_temp \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info label_adv $label_adv_temp]
                }
                set returnKL_temp(label_adv) $a_label_adv_temp
        }
        if {[catch {set helloInterval [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -HelloInterval]} getStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Error while fetching HelloInterval from $ldpRouterConfigHandle, $getStatus" {}
		    set cmdState $FAILURE
		    return $returnKeyedList
	    }
        if {[catch {set keepAliveInterval [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -KeepAliveInterval]} getStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Error while fetching KeepAliveInterval from $ldpRouterConfigHandle, $getStatus" {}
		    set cmdState $FAILURE
		    return $returnKeyedList
	    }
        set returnKL_temp(keepalive_holdtime) [expr 3 * $keepAliveInterval]
        set returnKL_temp(hello_hold_time) [expr 3 * $helloInterval]
    } elseif {$modeVal == "stats"} {
        #return key elapsed_time num_lsps_setup
        #elapsed_time stats does not have stc attributes map to it
        if {[info exists stopTimeArray(-EndTime)] == 0} {
            #if stop command is not called, use current time. 
            set elapsed_time [expr [clock seconds] - $startTimeArray($ldpRouterHandle)]
        } else {
            if {[info exists startTimeArray(-EndTime)] == 0} {
                set elapsed_time 0
            } else {
                #if stop command is not call at all.
                set elapsed_time [expr $stopTimeArray($ldpRouterHandle) - $startTimeArray($ldpRouterHandle)]
            }
        }
        set returnKL_temp(elapsed_time) $elapsed_time
        set returnKL_temp(num_lsps_setup) $num_lsp_setup
    } elseif {$modeVal =="lsp_labels"} {
       if {[info exist returnKL_temp(fec_type)]} {
                if {$returnKL_temp(fec_type) != ""} {
			set temp ""
			foreach val $returnKL_temp(fec_type) {
				lappend temp [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info fec_type $val]				
			}
			set returnKL_temp(fec_type) $temp
                }
        }
        if {[info exist returnKL_temp(prefix)]} {
                if {$returnKL_temp(prefix) != "" } {
			set temp ""
			foreach val $returnKL_temp(prefix) {
				lappend temp [lindex [split $val /] 0]
			}
			set returnKL_temp(prefix) $temp
                }
        }
        if {[info exist returnKL_temp(prefix_length)]} {
                if {$returnKL_temp(prefix_length) != ""} {
			set temp ""
			foreach val $returnKL_temp(prefix_length) {
				lappend temp [lindex [split $val /] 1]				
			}
			set returnKL_temp(prefix_length) $temp
                }
        }
    }

    
    set cmd "keylset returnKeyedList [array get returnKL_temp]"
    if {[catch {eval $cmd} eMsg]} {
    if {$configReturnKeyList == ""} {
	::sth::sthCore::processError returnKeyedList "No results to be configured for returnKeyedList" {}
    } else {
	::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. Error: $eMsg" {}
    }
	return $returnKeyedList
    }
	
    set cmdState $SUCCESS
    return $returnKeyedList

}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_info_settings (str args)
###\brief Process \em -mode switch with value \em settings for emulation_ldp_info cmd
###
###This procedure execute the emulation_ldp_info command when the mode is settings. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/
###
###emulation_ldp_info_lsp_labels (str args);
###
#by yulin chen 27/03/08
proc ::sth::Ldp::emulation_ldp_info_settings { userInput returnKeyedListVarName cmdStatusVarName modeVal } {
   
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
  
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set args $userInput

    set _OrigHltCmdName "emulation_ldp_info"
    set _hltCmdName "emulation_ldp_info_$modeVal"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
        
    set returnKeyName ""
    array set array_hLdpResult ""
	
    #check the validation of the ldp session handle
    if {[::info exists ::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)]} {
	set ldpRouterHandle $::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)
	    if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
		::sth::sthCore::processError returnKeyedList "Error: invalid LDP router handle $ldpRouterHandle" {}
		set cmdState $FAILURE
		return $returnKeyedList
	    }	
    } else {
	set cmdState $FAILURE
	return $returnKeyedList
    }
        
    #get result data handle
    if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldpRouterConfig]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterConfig handle from $ldpRouterHandle. Error: $getStatus" {}
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	if {[catch {set ldpRouterResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpRouterResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}
	if {[catch {set ldpLspResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpLspResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpLspResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}	
    }
    
    	if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4If from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
    set array_hLdpResult(LdpRouterResults) $ldpRouterResultsHandle
    set array_hLdpResult(LdpLspResults) $ldpLspResultsHandle
    set array_hLdpResult(LdpRouterConfig) $ldpRouterConfigHandle
    set array_hLdpResult(Ipv4If) $ipv4ResultIf
        
    #get all func switches
    set all_switch [array names ::sth::Ldp::emulation_ldp_info_mode]
    
    #choose the switches be returned in current mode
    foreach one_switch $all_switch {
        if {[info exist ::sth::Ldp::emulation_ldp_info_mode($one_switch)]} {
            if {[expr [lsearch $::sth::Ldp::emulation_ldp_info_mode($one_switch) "$modeVal"] > -1]} {
                lappend returnKeyName $one_switch
            }       
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    #loop for get switch's mapping stcattr value
    array set returnKL_temp ""
    array set hLdpResult ""
    set switchVal_temp ""
    foreach one_switch $returnKeyName {
        set stcobj $::sth::Ldp::emulation_ldp_info_stcobj($one_switch)
        set stcattr $::sth::Ldp::emulation_ldp_info_stcattr($one_switch)
        #if {[info exists array_hLdpResult($stcobj)]} {
        #    lappend hLdpResult($stcobj) $array_hLdpResult($stcobj)
        #}
        if {[string equal $stcobj "_none_"]} {
        #do nothing         
        } else {
                #loop for more than one Result handle
                foreach obj_handle $array_hLdpResult($stcobj) {                
                        if {[catch {set switchVal [::sth::sthCore::invoke stc::get $obj_handle -$stcattr]} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $$obj_handle, $eMsg"
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                lappend switchVal_temp $switchVal
                        }                    
                }
            #end of foreach obj_handle
        }
        #end of if {[string equal $stcobj "_none_"]} {} else {}
        set returnKL_temp($one_switch) $switchVal_temp
        set  switchVal_temp ""
    }
    #end of foreach one_switch
    
    #return key keepalive_holdtime hello_hold_time
    if {$modeVal == "settings"} {
        if {$returnKL_temp(label_adv) != ""} {
                set a_label_adv_temp ""
                foreach label_adv_temp $returnKL_temp(label_adv) {
                        lappend a_label_adv_temp \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info label_adv $label_adv_temp]
                }
                set returnKL_temp(label_adv) $a_label_adv_temp
        }
        if {[catch {set helloInterval [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -HelloInterval]} getStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Error while fetching HelloInterval from $ldpRouterConfigHandle, $getStatus" {}
		    set cmdState $FAILURE
		    return $returnKeyedList
	    }
        if {[catch {set keepAliveInterval [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -KeepAliveInterval]} getStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Error while fetching KeepAliveInterval from $ldpRouterConfigHandle, $getStatus" {}
		    set cmdState $FAILURE
		    return $returnKeyedList
	    }
        set returnKL_temp(keepalive_holdtime) [expr 3 * $keepAliveInterval]
        set returnKL_temp(hello_hold_time) [expr 3 * $helloInterval]
    }
    
    set cmd "keylset returnKeyedList [array get returnKL_temp]"
    if {[catch {eval $cmd} eMsg]} {
    if {$configReturnKeyList == ""} {
	::sth::sthCore::processError returnKeyedList "No results to be configured for returnKeyedList" {}
    } else {
	::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. Error: $eMsg" {}
    }
	return $returnKeyedList
    }
	
    set cmdState $SUCCESS
    return $returnKeyedList

}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_info_state(str args)
###\brief Process \em -mode switch with value \em state for emulation_ldp_info cmd
###
###This procedure execute the emulation_ldp_info command when the mode is state. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/
###
###emulation_ldp_info_lsp_labels (str args);
###
#by yulin chen 27/03/08
proc ::sth::Ldp::emulation_ldp_info_state { userInput returnKeyedListVarName cmdStatusVarName modeVal } {
   
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
  
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set args $userInput

    set _OrigHltCmdName "emulation_ldp_info"
    set _hltCmdName "emulation_ldp_info_$modeVal"
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
        
    set returnKeyName ""
    array set array_hLdpResult ""
	
    #check the validation of the ldp session handle
    if {[::info exists ::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)]} {
	set ldpRouterHandle $::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)
	    if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
		::sth::sthCore::processError returnKeyedList "Error: invalid LDP router handle $ldpRouterHandle" {}
		set cmdState $FAILURE
		return $returnKeyedList
	    }	
    } else {
	set cmdState $FAILURE
	return $returnKeyedList
    }
        
    #get result data handle
    if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldpRouterConfig]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterConfig handle from $ldpRouterHandle. Error: $getStatus" {}
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	if {[catch {set ldpRouterResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpRouterResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}
	if {[catch {set ldpLspResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpLspResults]} getStatus]} {
	    ::sth::sthCore::processError returnKeyedList "Error while fetching LdpLspResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
	    set cmdState $FAILURE
	    return $returnKeyedList
	}	
    }
    	if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4If from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
    set array_hLdpResult(LdpRouterResults) $ldpRouterResultsHandle
    set array_hLdpResult(LdpLspResults) $ldpLspResultsHandle
    set array_hLdpResult(LdpRouterConfig) $ldpRouterConfigHandle
    set array_hLdpResult(Ipv4If) $ipv4ResultIf
        
    #get all func switches
    set all_switch [array names ::sth::Ldp::emulation_ldp_info_mode]
    
    #choose the switches be returned in current mode
    foreach one_switch $all_switch {
        if {[info exist ::sth::Ldp::emulation_ldp_info_mode($one_switch)]} {
            if {[expr [lsearch $::sth::Ldp::emulation_ldp_info_mode($one_switch) "$modeVal"] > -1]} {
                lappend returnKeyName $one_switch
            }       
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    #loop for get switch's mapping stcattr value
    array set returnKL_temp ""
    array set hLdpResult ""
    set switchVal_temp ""
    foreach one_switch $returnKeyName {
        set stcobj $::sth::Ldp::emulation_ldp_info_stcobj($one_switch)
        set stcattr $::sth::Ldp::emulation_ldp_info_stcattr($one_switch)
        #if {[info exists array_hLdpResult($stcobj)]} {
        #    lappend hLdpResult($stcobj) $array_hLdpResult($stcobj)
        #}
        if {[string equal $stcobj "_none_"]} {
                #do nothing                   
        } else {
                #loop for more than one Result handle
                foreach obj_handle $array_hLdpResult($stcobj) {
                        if {[catch {set switchVal [::sth::sthCore::invoke stc::get $obj_handle -$stcattr]} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $$obj_handle, $eMsg"
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                lappend switchVal_temp $switchVal
                        }                    
                }
                #end of foreach obj_handle
        }
        #end of if {[string equal $stcobj "_none_"]} {} else {}
        
        set returnKL_temp($one_switch) $switchVal_temp
        set switchVal_temp ""
    }
    #end of foreach one_switch

    if {$modeVal == "state"} {
        if {$returnKL_temp(session_state) != ""} {
                set a_session_state_temp ""
                foreach session_state_temp $returnKL_temp(session_state) {
                        lappend a_session_state \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info session_state $session_state_temp]
                }
                set returnKL_temp(session_state) $a_session_state
        }
        if {$returnKL_temp(type) != ""} {
                set a_type_temp ""
                foreach type_temp $returnKL_temp(type) {
                        lappend a_type_temp \
                                [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info type $type_temp]
                }
                set returnKL_temp(type) $a_type_temp
        }
    }

    
    set cmd "keylset returnKeyedList [array get returnKL_temp]"
    if {[catch {eval $cmd} eMsg]} {
    if {$configReturnKeyList == ""} {
	::sth::sthCore::processError returnKeyedList "No results to be configured for returnKeyedList" {}
    } else {
	::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. Error: $eMsg" {}
    }
	return $returnKeyedList
    }
	
    set cmdState $SUCCESS
    return $returnKeyedList

}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_info_stats (str args)
###\brief Process \em -mode switch with value \em stats for emulation_ldp_info cmd
###
###This procedure execute the emulation_ldp_info command when the mode is stats. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/
###
###emulation_ldp_info_lsp_labels (str args);
###
#by yulin chen 27/03/08
proc ::sth::Ldp::emulation_ldp_info_stats { userInput returnKeyedListVarName cmdStatusVarName modeVal } {
        variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState    

	set _OrigHltCmdName "emulation_ldp_info"
	set _hltCmdName "emulation_ldp_info_$modeVal"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

        variable startTimeArray
        variable stopTimeArray

        set returnKeyName ""
        array set array_hLdpResult ""
        
        #check the validation of the ldp session handle
	if {[::info exists ::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)]} {
		set ldpRouterHandle $::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)
		if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
			::sth::sthCore::processError returnKeyedList "Error: invalid LDP router handle $ldpRouterHandle" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}	
	} else {
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
        #get result data handle
	if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldpRouterConfig]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterConfig handle from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	} else {
		if {[catch {set ldpRouterResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpRouterResults]} getStatus]} {
			::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}
		if {[catch {set ldpLspResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpLspResults]} getStatus]} {
			::sth::sthCore::processError returnKeyedList "Error while fetching LdpLspResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}	
	}
        
        if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4If from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
        if {[catch {set lsp_pool_handle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-ipv4prefixlsp]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4PrefixLsp handle from $ldpRouterConfigHandle, $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
	if {[catch {set vc_lsp_pool_handle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-vclsp]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4PrefixLsp handle from $ldpRouterConfigHandle, $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}

    #get num_lsp_setup for -mode stats
    set num_lsp_setup 0
    set lsp_pool_handle [concat $lsp_pool_handle $vc_lsp_pool_handle]
    foreach prefixlsp $lsp_pool_handle  {
        if {[string match "*prefixlsp*" $prefixlsp]} {
            if {[catch {set ipv4networkblock [::sth::sthCore::invoke stc::get $prefixlsp -children-ipv4networkblock]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Error while fetching ipv4networkblock handle from $prefixlsp, $getStatus" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {[catch {set net_count [::sth::sthCore::invoke stc::get $ipv4networkblock -NetworkCount]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Error while fetching NetworkCount handle from $ipv4networkblock, $getStatus" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } elseif {[string match "vclsp*" $prefixlsp]} {
            if {[catch {set net_count [::sth::sthCore::invoke stc::get $prefixlsp -VcIdCount]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Error while fetching VcIdCount handle from $prefixlsp, $getStatus" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
        set num_lsp_setup [expr $num_lsp_setup + $net_count] 
    }
    
	set array_hLdpResult(LdpRouterResults) $ldpRouterResultsHandle
	set array_hLdpResult(LdpLspResults) $ldpLspResultsHandle
	set array_hLdpResult(LdpRouterConfig) $ldpRouterConfigHandle
	set array_hLdpResult(Ipv4If) $ipv4ResultIf
        
    #get all func switches
    set all_switch [array names ::sth::Ldp::emulation_ldp_info_mode]

    #choose the switches be returned in current mode
    foreach one_switch $all_switch {
        if {[info exist ::sth::Ldp::emulation_ldp_info_mode($one_switch)]} {
            if {[expr [lsearch $::sth::Ldp::emulation_ldp_info_mode($one_switch) "$modeVal"] > -1]} {
                lappend returnKeyName $one_switch
            }       
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    #loop for get switch's mapping stcattr value
    array set returnKL_temp ""
    array set hLdpResult ""
    set switchVal_temp ""
    foreach one_switch $returnKeyName {
        set stcobj $::sth::Ldp::emulation_ldp_info_stcobj($one_switch)
        set stcattr $::sth::Ldp::emulation_ldp_info_stcattr($one_switch)
        #if {[info exists array_hLdpResult($stcobj)]} {
        #    lappend hLdpResult($stcobj) $array_hLdpResult($stcobj)
        #}
        if {[string equal $stcobj "_none_"]} {
                #do nothing                   
        } else {
                #loop for more than one Result handle
                foreach obj_handle $array_hLdpResult($stcobj) {
                        if {[catch {set switchVal [::sth::sthCore::invoke stc::get $obj_handle -$stcattr]} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $$obj_handle, $eMsg"
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                lappend switchVal_temp $switchVal
                        }                    
                }
                #end of foreach obj_handle
        }
        #end of if {[string equal $stcobj "_none_"]} {} else {}
        
        set returnKL_temp($one_switch) $switchVal_temp
        set switchVal_temp ""
    }
    #end of foreach one_switch
    
    #return key elapsed_time num_lsps_setup
    if {$modeVal == "stats"} {
        #elapsed_time stats does not have stc attributes map to it
        if {[info exists stopTimeArray(-EndTime)] == 0} {
            #if stop command is not called, use current time. 
            set elapsed_time [expr [clock seconds] - $startTimeArray($ldpRouterHandle)]
        } else {
            if {[info exists startTimeArray(-EndTime)] == 0} {
                set elapsed_time 0
            } else {
                #if stop command is not call at all.
                set elapsed_time [expr $stopTimeArray($ldpRouterHandle) - $startTimeArray($ldpRouterHandle)]
            }
        }
        set returnKL_temp(elapsed_time) $elapsed_time
        set returnKL_temp(num_lsps_setup) $num_lsp_setup
    }
    
        set cmd "keylset returnKeyedList [array get returnKL_temp]"
	if {[catch {eval $cmd} eMsg]} {
        if {$configReturnKeyList == ""} {
		    ::sth::sthCore::processError returnKeyedList "No results to be configured for returnKeyedList" {}
        } else {
		    ::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. Error: $eMsg" {}
        }
		return $returnKeyedList
	}
	
	set cmdState $SUCCESS
	return $returnKeyedList
    
}

###/*! \ingroup ldpswitchprocfuncs
###\fn emulation_ldp_info_lsp_labels (str args)
###\brief Process \em -mode switch with value \em lsp_labels for emulation_ldp_info cmd
###
###This procedure execute the emulation_ldp_info command when the mode is lsp_labels. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###*/
###
###emulation_ldp_info_lsp_labels (str args);
###
#by yulin chen 27/03/08
proc ::sth::Ldp::emulation_ldp_info_lsp_labels { userInput returnKeyedListVarName cmdStatusVarName modeVal } {
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE

	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	set _OrigHltCmdName "emulation_ldp_info"
	set _hltCmdName "emulation_ldp_info_$modeVal"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

        set returnKeyName ""
        array set array_hLdpResult ""
	
        #check the validation of the ldp session handle
	if {[::info exists ::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)]} {
		set ldpRouterHandle $::sth::Ldp::emulation_ldp_info_user_input_args_array(handle)
		if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle msg]} {
			::sth::sthCore::processError returnKeyedList "Error: invalid LDP router handle $ldpRouterHandle" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}	
	} else {
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
        #get result data handle
	if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ldpRouterConfig]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterConfig handle from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	} else {
		if {[catch {set ldpRouterResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpRouterResults]} getStatus]} {
			::sth::sthCore::processError returnKeyedList "Error while fetching LdpRouterResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}
		if {[catch {set ldpLspResultsHandle [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-LdpLspResults]} getStatus]} {
			::sth::sthCore::processError returnKeyedList "Error while fetching LdpLspResults handle from $ldpRouterConfigHandle. Error: $getStatus" {}
			set cmdState $FAILURE
			return $returnKeyedList
		}	
	}
        
	if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		::sth::sthCore::processError returnKeyedList "Error while fetching Ipv4If from $ldpRouterHandle. Error: $getStatus" {}
		set cmdState $FAILURE
		return $returnKeyedList
	}
        
	set array_hLdpResult(LdpRouterResults) $ldpRouterResultsHandle
	set array_hLdpResult(LdpLspResults) $ldpLspResultsHandle
	set array_hLdpResult(LdpRouterConfig) $ldpRouterConfigHandle
	set array_hLdpResult(Ipv4If) $ipv4ResultIf
        
    #get all func switches
    set all_switch [array names ::sth::Ldp::emulation_ldp_info_mode]
    
    #choose the switches be returned in current mode
    foreach one_switch $all_switch {
        if {[info exist ::sth::Ldp::emulation_ldp_info_mode($one_switch)]} {
            if {[expr [lsearch $::sth::Ldp::emulation_ldp_info_mode($one_switch) "$modeVal"] > -1]} {
                lappend returnKeyName $one_switch
            }       
        } else {
            ::sth::sthCore::processError returnKeyedList "Error occured for: $_OrigHltCmdName $_hltCmdName $userInput" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    #loop for get switch's mapping stcattr value
    array set returnKL_temp ""
    array set hLdpResult ""
    set switchVal_temp ""
    foreach one_switch $returnKeyName {
        set stcobj $::sth::Ldp::emulation_ldp_info_stcobj($one_switch)
        set stcattr $::sth::Ldp::emulation_ldp_info_stcattr($one_switch)
        #if {[info exists array_hLdpResult($stcobj)]} {
        #    lappend hLdpResult($stcobj) $array_hLdpResult($stcobj)
        #}
        if {[string equal $stcobj "_none_"]} {
                #do nothing
        } else {
                #loop for more than one Result handle
                foreach obj_handle $array_hLdpResult($stcobj) {                
                        if {[catch {set switchVal [::sth::sthCore::invoke stc::get $obj_handle -$stcattr]} eMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error stc::get -$stcattr $$obj_handle, $eMsg"
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                if {[string equal $one_switch "fec_type"]} {
                                        lappend switchVal_temp [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_info fec_type $switchVal]
                                } elseif {[string equal $one_switch "prefix"]} {
                                        #LdpLspResult -LspFecInfo  --> string of lsp prefix and prefix_length(or vc id)
                                        lappend switchVal_temp [lindex [split $switchVal /] 0]
                                } elseif {[string equal $one_switch "prefix_length"] } {
                                        lappend switchVal_temp [lindex [split $switchVal /] 1]
                                } else {
                                        lappend switchVal_temp $switchVal
                                }
                                #end of if -elseif
                        }                    
                }
                #end of foreach obj_handle
        }
        #end of if {[string equal $stcobj "_none_"]} {} else {}
        
        set returnKL_temp($one_switch) $switchVal_temp
        set switchVal_temp ""
    }
    #end of foreach one_switch
    
        set cmd "keylset returnKeyedList [array get returnKL_temp]"
	if {[catch {eval $cmd} eMsg]} {
        if {$configReturnKeyList == ""} {
		    ::sth::sthCore::processError returnKeyedList "No results to be configured for returnKeyedList" {}
        } else {
		    ::sth::sthCore::processError returnKeyedList "Cannot update the returnKeyedList. Error: $eMsg" {}
        }
		return $returnKeyedList
	}
	
	set cmdState $SUCCESS
	return $returnKeyedList
    
}		

###/*! \ingroup ldp_route_config
###\fn emulation_ldp_route_config_create {str args}
###\brief Processes -mode create switch for emulation_ldp_route_config command
###
###This procedure processes the -mode create switch for emulation_ldp_route_config
###command.
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###\warning None
###*/
###
###emulation_ldp_route_config_create { args };
###

proc ::sth::Ldp::emulation_ldp_route_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set _OrigHltCmdName "emulation_ldp_route_config"
	set _hltCmdName "emulation_ldp_route_config_create"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	#check for the valid LDP router handle
	if {[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(handle)]} {
		set ldpRouterHandle $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(handle)
		#check if the ldp router handle is valid
		if {![::sth::Ldp::IsLdpRouterHandleValid $ldpRouterHandle errMsg]} {
			::sth::sthCore::log debug "Invalid Value of handle"
			#::sth::sthCore::sthError -errno 23 -argslist "$sessionHandle -handle" -keyedlistVar ldpRouteKeyedList
			return $returnKeyedList
		}
	} else {
        ::sth::sthCore::log error "To create a LDP route, valid LDP router handle, \"handle\" switch, is required"	
        return $FAILURE
	}

	set objList {ipv4networkblock Ipv4PrefixLsp VcLsp MacBlock Ipv6PrefixLsp Ipv4IngressPrefixLsp Ipv6IngressPrefixLsp ipv6networkblock GeneralizedPwidLsp P2mpLsp LdpMldpCustomOpaque}
	array set cmdArray {
		ipv4networkblock ""
		Ipv4PrefixLsp ""
		VcLsp ""
		MacBlock ""
        Ipv6PrefixLsp ""
        Ipv4IngressPrefixLsp  ""
        Ipv6IngressPrefixLsp  ""
        ipv6networkblock ""
        GeneralizedPwidLsp  ""
        P2mpLsp ""
        LdpMldpCustomOpaque ""
	}
	array set hdlArray {
		ipv4networkblock ""
		Ipv4PrefixLsp ""
		VcLsp ""
		MacBlock ""
        Ipv6PrefixLsp ""
        Ipv4IngressPrefixLsp  ""
        Ipv6IngressPrefixLsp  ""
        ipv6networkblock ""
        GeneralizedPwidLsp  ""
        P2mpLsp ""
        LdpMldpCustomOpaque ""
	}	
	
	# start - call doStcCreate to create lsp
	set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-LdpRouterConfig]
	
	if {![::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_type)]} {
        ::sth::sthCore::log error "To create a LDP route, lsp_type is required"	
        return $FAILURE	
	}
    set lspObj ""
    set ipObj ""
    switch -exact -- $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_type) \
        ipv4_egress {
                set lspObj  "Ipv4PrefixLsp"
                set ipObj "ipv4networkblock"
        }\
        ipv4_ingress {
                set lspObj "Ipv4IngressPrefixLsp"
                set ipObj "ipv4networkblock"
        }\
        ipv6_egress {
                set lspObj  "Ipv6PrefixLsp"
                set ipObj "ipv6networkblock"
        }\
        ipv6_ingress {
                set lspObj "Ipv6IngressPrefixLsp"
                set ipObj "ipv6networkblock"
        }\
        pwid {
                set lspObj "VcLsp"
        }\
        generalized_pwid {
                set lspObj "GeneralizedPwidLsp"
        }\
        p2mp {
                set lspObj "P2mpLsp"
        }\
        default {
        }
    if {[catch {set lspHandle [::sth::sthCore::invoke stc::create $lspObj -under $ldpRouterConfigHandle]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "stc::create FAILED: errMsg = $createStatus" {}
            return $FAILURE
    } else {
            set hdlArray($lspObj) $lspHandle
            if {[regexp -nocase "ipv4|ipv6" $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_type)]} {
                    set switchName fec_type
                    set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_route_config $switchName stcattr]
                    if {[catch {set ipNetworkBlockHandle [::sth::sthCore::invoke stc::get $lspHandle -children-$ipObj]} getStatus]} {
                            ::sth::sthCore::processError returnKeyedList "Cannot fetch $ipObj from $lspObj: $lspHandle. Error: $getStatus" {}
                            return $FAILURE
                    }
                    set hdlArray($ipObj) $ipNetworkBlockHandle      
                    set switchValue $::sth::Ldp::emulation_ldp_route_config_user_input_args_array($switchName)
                    if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_route_config $switchName $switchValue]} getStatus]} {
                            append cmdArray($lspObj) " -$stcAttrName $attrValue"
                    } else {
                            append cmdArray($lspObj) " -$stcAttrName $switchValue"
                    }
            } elseif {[regexp -nocase "p2mp" $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_type)]} {
                
                set opaqueTypeSelector $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(opaque_type_selector)
                if {[regexp -nocase "type3_s_g" $opaqueTypeSelector] || 
                    [regexp -nocase "type250_s_g_rd" $opaqueTypeSelector]} {
                    if {[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(multicast_group_handle)]} {
                        set multicastHnd $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(multicast_group_handle)
                        ::sth::sthCore::invoke stc::config $lspHandle -P2mpMemberGroup-targets $multicastHnd
                    }
                }
                if {[regexp -nocase "custom" $opaqueTypeSelector]} {
					if {[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(custom_opaque_type)] ||
						[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(enable_extended_type)] ||
						[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(extended_opaque_type)] ||
						[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(custom_opaque_value)]} {	
						set cusOpqHandle [::sth::sthCore::invoke stc::create LdpMldpCustomOpaque -under $lspHandle]
	                    set hdlArray(LdpMldpCustomOpaque) $cusOpqHandle
					}
                }
            } else {
                    if {[catch {set MacBlockHandle [::sth::sthCore::invoke stc::get $lspHandle -children-MacBlock]} getStatus]} {
                            ::sth::sthCore::processError returnKeyedList "Cannot fetch MacBlock from VcLsp: $lspHandle. Error: $getStatus" {}
                            return $FAILURE
                    }
                    set hdlArray(MacBlock) $MacBlockHandle	
            } 
    }

	#Configure the created lsp with user input (options)
	::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
	set userInputList [array get ::sth::Ldp::emulation_ldp_route_config\_user_input_args_array]
	#remove those input switches without processing functions
	#set switchWithoutFunc {fec_type handle label_msg_type lsp_handle mode num_lsps mandatory_args optional_args}
	set switchWithoutFunc {lsp_type fec_type handle label_msg_type lsp_handle mode mandatory_args optional_args multicast_group_handle}
	foreach switchName $switchWithoutFunc {
		set switchIndex [lsearch $userInputList $switchName]
		if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
			set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
		}
	}
	
	foreach {switchName switchValue} $userInputList {
		::sth::sthCore::log debug "Trying to process the switch $switchName $switchValue"
		set switchProcFunc [::sth::sthCore::getModeFunc2 ::sth::Ldp:: emulation_ldp_route_config $switchName $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(mode)]

		#@TODO Change this to pass the value of the handle itself
		set handleSwitchName $ldpRouterHandle
		
		#if processing function is processConfigCmd, append the attribute/value pair to corresponding array element for processing later
		if {[string equal $switchProcFunc "processConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_route_config $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_route_config $switchName stcattr]
                    
            #here need to change the stc obj name for different type of prefix lsp
            if {[regexp -nocase "ipv4networkblock" $stcObjName]} {
                    set stcObjName $ipObj
            } elseif {[regexp -nocase "Ipv4PrefixLsp" $stcObjName]} {
                    set stcObjName $lspObj
            }
                        
			if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_route_config $switchName $switchValue]} getStatus]} {
				append cmdArray($stcObjName) " -$stcAttrName $attrValue"
			} else {
				append cmdArray($stcObjName) " -$stcAttrName $switchValue"
			}
			 
		} else {
			set cmd "::sth::Ldp::$switchProcFunc {$switchValue} returnKeyedList $_hltCmdName $switchName switchToOutput $handleSwitchName"
			::sth::sthCore::log debug "CMD to Process: $cmd "
			set cmdResult [eval $cmd]
			::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
			if {$cmdResult == $::sth::sthCore::FAILURE} {
				set cmdFailed $::sth::Ldp::TRUE
				set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch $switchName with Value $switchValue"
				::sth::sthCore::log error "$logStatus"
				break
			}
		}
	}

	#process all switches handled by processConfigCmd
	#set cmdResult [eval ::sth::sthCore::genericConfig hdlArray cmdArray]
	foreach objName $objList {
		if {$cmdArray($objName) != "" && $hdlArray($objName) != ""} {
			set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
			if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
			    ::sth::sthCore::log debug "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus"
			    set cmdFailed $::sth::Ldp::TRUE
			    set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
				::sth::sthCore::log error "$logStatus"
			} else {
		    	::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
			}
		}
	}
	
	if {[::info exists cmdFailed]} {
		::sth::sthCore::log error "Error Occured configuring LDP route: $returnKeyedList"
                #Delete the lsp Object
                if {[catch {::sth::sthCore::invoke stc::delete $lspHandle} eMsg ]} {
                    ::sth::sthCore::log error "Error deleting previously created LSP:$lspHandle Msg: $eMsg"
                }
                set errOccured $::sth::Ldp::TRUE
                return $FAILURE
        } else {			
                if {[catch {::sth::sthCore::doStcApply} msg]} {
                    ::sth::sthCore::log error "Error applying LSP configuration: $msg"
                }
		keylset returnKeyedList lsp_handle $lspHandle
		set errOccured $::sth::Ldp::FALSE
		set cmdState $SUCCESS
		return $returnKeyedList
	}	
}

###/*! \ingroup ldp_route_config
###\fn emulation_ldp_route_config_modify {str args}
###\brief Processes -mode modify switch for emulation_ldp_route_config command
###
###This procedure processes the -mode modify switch for emulation_ldp_route_config
###command.
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###\warning None
###*/
###
###emulation_ldp_route_config_modify { args };
###

proc ::sth::Ldp::emulation_ldp_route_config_modify { userInput returnKeyedListVarName cmdStatusVarName } {
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE


	
	set _OrigHltCmdName "emulation_ldp_route_config"
	set _hltCmdName "emulation_ldp_route_config_modify"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	#check for the valid lsp handle
	if {[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_handle)]} {
		set lspHandle $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_handle)
		#check if the ldp router handle is valid
		if {![::sth::Ldp::IsLspHandleValid $lspHandle errMsg]} {
			::sth::sthCore::log debug "Invalid Value of lsp handle"
			return $returnKeyedList			
		}
	} else {
                ::sth::sthCore::log error "To modify a LDP route, valid lsp handle, \"lsp_handle\" switch, is required"	
                return $FAILURE
	}
	set objList {ipv4networkblock Ipv4PrefixLsp VcLsp MacBlock Ipv6PrefixLsp Ipv4IngressPrefixLsp Ipv6IngressPrefixLsp ipv6networkblock GeneralizedPwidLsp P2mpLsp LdpMldpCustomOpaque}
	array set cmdArray {
		ipv4networkblock ""
		Ipv4PrefixLsp ""
		VcLsp ""
		MacBlock ""
        Ipv6PrefixLsp ""
        Ipv4IngressPrefixLsp  ""
        Ipv6IngressPrefixLsp  ""
        ipv6networkblock ""
        GeneralizedPwidLsp ""
        P2mpLsp ""
		LdpMldpCustomOpaque ""
	}
	array set hdlArray {
		ipv4networkblock ""
		Ipv4PrefixLsp ""
		VcLsp ""
		MacBlock ""
        Ipv6PrefixLsp ""
        Ipv4IngressPrefixLsp  ""
        Ipv6IngressPrefixLsp  ""
        ipv6networkblock ""
        GeneralizedPwidLsp ""
        P2mpLsp ""
		LdpMldpCustomOpaque ""
	}	

	set lspObj ""
	set ipObj ""
	foreach obj $objList {
		if {[regexp -nocase $obj $lspHandle]} {
			  set lspObj   $obj
			  break
		}
	}
	set hdlArray($lspObj) $lspHandle

	if {[regexp -nocase "ipv4" $lspHandle]} {
		set ipNetworkBlockHandle [::sth::sthCore::invoke stc::get $lspHandle -children-ipv4networkblock]
		set hdlArray(ipv4networkblock) $ipNetworkBlockHandle
		set ipObj "ipv4networkblock"
	} elseif {[regexp -nocase "ipv6" $lspHandle]} {
		set ipNetworkBlockHandle [::sth::sthCore::invoke stc::get $lspHandle -children-ipv6networkblock]
		set hdlArray(ipv6networkblock) $ipNetworkBlockHandle
		set ipObj "ipv6networkblock"
	} elseif {[regexp -nocase "vclsp" $lspHandle]} {
		set MacBlockHandle [::sth::sthCore::invoke stc::get $lspHandle -children-MacBlock]
		set hdlArray(MacBlock) $MacBlockHandle
	} elseif {[regexp -nocase "p2mp" $lspHandle]} {
		set LdpMldpCustomOpaqueHandle [::sth::sthCore::invoke stc::get $lspHandle -children-LdpMldpCustomOpaque]
		set hdlArray(LdpMldpCustomOpaque) $LdpMldpCustomOpaqueHandle
	}

	::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
	set userInputList $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(optional_args)
	#remove the dash before the switch name in optional_args
	for {set i 0} {$i < [expr {[llength $userInputList]/2}]} {incr i} {
		set index [expr {$i*2}]
		set nameNoDash [string range [lindex $userInputList $index] 1 end]
		lset userInputList $index $nameNoDash
	}
        
	#remove those input switches without processing functions
	set switchWithoutFunc {lsp_type handle label_msg_type lsp_handle mode mandatory_args optional_args}
	foreach switchName $switchWithoutFunc {
		set switchIndex [lsearch $userInputList $switchName]
		if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
			set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
		}
	}
	
	foreach {switchName switchValue} $userInputList {
		::sth::sthCore::log debug "Trying to process the switch $switchName"
		set switchProcFunc [::sth::sthCore::getModeFunc2 ::sth::Ldp:: emulation_ldp_route_config $switchName $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(mode)]

		#@TODO Change this to pass the value of the handle itself
		set handleSwitchName $lspHandle
		
		#if processing function is processConfigCmd, append the attribute/value pair to 
		#corresponding array element for processing later
		if {[string equal $switchProcFunc "processConfigCmd"]} {
			set stcObjName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_route_config $switchName stcobj]
			set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_route_config $switchName stcattr]
			#special handling: when in vc mode, the num_lsps attribute is mapped to VcIdCount of vcLsp object
			if {[regexp -nocase "vclsp" $lspObj] && $stcAttrName == "NetworkCount"} {
				set stcObjName VcLsp
				set stcAttrName  VcIdCount
			} else {
				#here need to change the stc obj name for different type of prefix lsp
				if {[regexp -nocase "ipv4networkblock" $stcObjName]} {
						set stcObjName $ipObj
				} elseif {[regexp -nocase "Ipv4PrefixLsp" $stcObjName]} {
						set stcObjName $lspObj
				}
			}
			if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_route_config $switchName $switchValue]} getStatus]} {
				append cmdArray($stcObjName) " -$stcAttrName $attrValue"
			} else {
				append cmdArray($stcObjName) " -$stcAttrName $switchValue"
			}
                        
		} else {
			set cmd "::sth::Ldp::$switchProcFunc {$switchValue} returnKeyedList $_hltCmdName $switchName switchToOutput $handleSwitchName"
			::sth::sthCore::log debug "CMD to Process: $cmd "
			set cmdResult [eval $cmd]
			::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
			if {$cmdResult == $::sth::sthCore::FAILURE} {
				set cmdFailed $::sth::Ldp::TRUE
				set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch $switchName with Value $switchValue"
				::sth::sthCore::log error "$logStatus"
				break
			}
		}
	}

	#process all switches handled by processConfigCmd
	#set cmdResult [eval ::sth::sthCore::genericConfig hdlArray cmdArray]
	foreach objName $objList {
		if {$cmdArray($objName) != "" && $hdlArray($objName) != ""} {
			set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
			#puts $cmd
			if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
			    ::sth::sthCore::log debug "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus"
			    set cmdFailed $::sth::Ldp::TRUE
			    set errOccured $::sth::Ldp::TRUE
				set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
				::sth::sthCore::log error "$logStatus"
			} else {
		    	::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
			}
		}
	}
	
	if {[::info exists cmdFailed]} {
		::sth::sthCore::log error "Error Occured configuring LDP route: $returnKeyedList"
        #Delete the lspr Object
	    if {[catch {::sth::sthCore::invoke stc::delete $lspHandle} eMsg ]} {
	        ::sth::sthCore::log error "Error deleting previously created LSP:$lspHandle Msg: $eMsg"
	    }
	    set errOccured $::sth::Ldp::TRUE
	    return $FAILURE
   } else {	
   		#puts "ok"		
	#	set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList handle $lspHandle]
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::log error "Error applying LSP configuration: $msg"
        }
		keylset returnKeyedList lsp_handle $lspHandle
		set errOccured $::sth::Ldp::FALSE
		set cmdState $SUCCESS
		return $returnKeyedList
	}	
}	

###/*! \ingroup ldp_route_config
###\fn emulation_ldp_route_config_delete {str args}
###\brief Processes -mode delete switch for emulation_ldp_route_config command
###
###This procedure processes the -mode delete switch for emulation_ldp_route_config
###command.
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###\warning None
###*/
###
###emulation_ldp_route_config_delete { args };
###

proc ::sth::Ldp::emulation_ldp_route_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE


	
	set _OrigHltCmdName "emulation_ldp_route_config"
	set _hltCmdName "emulation_ldp_route_config_delete"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
	upvar 1 $cmdStatusVarName cmdState
	
	set args $userInput
	
	#check for the valid lsp handle
	if {[::info exists ::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_handle)]} {
		set lspHandle $::sth::Ldp::emulation_ldp_route_config_user_input_args_array(lsp_handle)
		#check if the ldp router handle is valid
		if {![::sth::Ldp::IsLspHandleValid $lspHandle errMsg]} {
			::sth::sthCore::log debug "Invalid Value of lsp handle"
			#::sth::sthCore::sthError -errno 23 -argslist "$sessionHandle -handle" -keyedlistVar ldpRouteKeyedList
			return $returnKeyedList			
		}
	} else {
        ::sth::sthCore::log error "To delete a LDP route, valid lsp handle, \"lsp_handle\" switch, is required"	
        return $FAILURE
	}

	#call dostcdelete on the lsp handle
	if {[catch {::sth::sthCore::invoke stc::delete $lspHandle} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting LDP lsp $lspHandle. Error: $eMsg" {}     
		set cmdState $FAILURE
		return $returnKeyedList  		
	}
	
	if {[::info exists cmdError]} {
		set cmdState $FAILURE
		return $returnKeyedList
	} else {
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::log error "Error applying LSP configuration: $msg"
        }
		set cmdState $SUCCESS
		return $returnKeyedList		
	}
}

proc ::sth::Ldp::createConfigLdpRouter {args returnStringName cmdStateVarName rtID} {
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	variable ::sth::Ldp::createResultQuery
		
	set _OrigHltCmdName "emulation_ldp_config"
	set _hltCmdName "emulation_ldp_config_create"
	
	
	upvar 1 $returnStringName returnKeyedList
	upvar 1 $cmdStateVarName errOccured
	
	::sth::sthCore::log debug "Value of args before cmdInit:$args"
	if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(port_handle)]} { 
		#Create the Ldp router under the port and then configure the other parameters.
		set ip_version "ipv4"
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(ip_version)]} {
			set ip_version $::sth::Ldp::emulation_ldp_config_user_input_args_array(ip_version)
		}
		set IpIfStack ""
		set IpIfCOunt ""

		if {[regexp -nocase "6" $ip_version]} {
			set IpIfStack "$IpIfStack Ipv6If"
			set IpIfCOunt "$IpIfCOunt 1"
		}
		if {[regexp -nocase "4" $ip_version]} {
			set IpIfStack "$IpIfStack Ipv4If"
			set IpIfCOunt "$IpIfCOunt 1"
		}
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vci)] || [info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vpi)]} {
			set IfStack "$IpIfStack Aal5If"
			set IfCount "$IpIfCOunt 1"
		} elseif {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_id)] && [info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_outer_id)]} {
		    #There is S-Vlan and C-vlan
		    set IfStack "$IpIfStack VlanIf VlanIf EthIIIf"
		    set IfCount "$IpIfCOunt 1 1 1"
		} elseif {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_id)] && ![info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_outer_id)]} {
		    # There is vlan
		    set IfStack "$IpIfStack VlanIf EthIIIf"
		    set IfCount "$IpIfCOunt 1 1"
		} else {
		    # There is no vlan
		    set IfStack "$IpIfStack EthIIIf"
		    set IfCount "$IpIfCOunt 1"
		}
		
		if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $::sth::GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $::sth::Ldp::emulation_ldp_config_user_input_args_array(port_handle)]
				    set ldpRouterHandle $DeviceCreateOutput(-ReturnList)} createStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Interal command error while creating LDP router. Error: $createStatus" {}
		    set errOccured $::sth::Ldp::TRUE
		    return $FAILURE
		} else {
		    ::sth::sthCore::log debug "The LDP Router:$ldpRouterHandle was successfully created \
			under project $::sth::GBLHNDMAP(project) affiliated with \
			port:$::sth::Ldp::emulation_ldp_config_user_input_args_array(port_handle)"
		}
		set lowerIf ""
		if {[regexp -nocase "vlanif" $IfStack]} {
			set lowerIf [lindex [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-VlanIf] 0]
		} else {
			set lowerIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-EthIIIf]
		}
		set topLevelIf ""
		if {[regexp "6" $ip_version]} {
			set ipv6If [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-ipv6if]
			::sth::sthCore::invoke stc::config $ldpRouterHandle "-primaryif-targets $ipv6If"
			# create new ipv6if
			::sth::sthCore::invoke stc::config $ipv6If -StackedOnEndpoint-targets $lowerIf
			set linkLocalIf [::sth::sthCore::invoke stc::create ipv6if -under $ldpRouterHandle -StackedOnEndpoint-targets $lowerIf]
			set topLevelIf [concat $topLevelIf $ipv6If $linkLocalIf]
		}
		
		if {[regexp "v4" $ip_version]} {
			set ipv4If [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]
			set topLevelIf [concat $ipv4If $topLevelIf]
		}
		::sth::sthCore::invoke stc::config $ldpRouterHandle "-TopLevelIf-targets \"$topLevelIf\""
		
		#Creat LdpRouterConfig under router
		if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $ldpRouterHandle  -CreateClassId [string tolower LdpRouterConfig]]
				      set ldpRouterConfigHandle $ProtocolCreateOutput(-ReturnList)} createStatus]} {
		    ::sth::sthCore::processError returnKeyedList "Interal command error while creating LDPRouterConfig. Error: $createStatus" {}
		    set errOccured $::sth::Ldp::TRUE
		    return $FAILURE
		} else {
		    ::sth::sthCore::log debug "The LDPRouterConfig:$ldpRouterConfigHandle was successfully created under Router:$ldpRouterHandle)"
		}
		###add for gre
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(tunnel_handle)]} {
		    set greTopIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -TopLevelIf-targets]
		    set nextIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
		    if {[regexp -nocase -- $nextIf "mplsif"]} {
			set mplsIf $nextIf
			set greLowerIf [::sth::sthCore::invoke stc::get $mplsIf -StackedOnEndpoint-targets]
		    } else {
			set greLowerIf $nextIf
		    }
		    
		    #in STC 3.00, the stack relation is like this:
		    #without gre:
		    #ethif<-mplsif<-ipif
		    #with gre:
		    #ethif<-greipv4if<-greif<-ipif
		    #                    ^
		    #                    |--mplsif
		    #but in the early version, the mplsif didn't have any relationship with other ifs
		    
		    ###create the gre stack and setup the relation
		    if {[catch {::sth::createGreStack $::sth::Ldp::emulation_ldp_config_user_input_args_array(tunnel_handle) $ldpRouterHandle $greLowerIf $rtID} greIf]} {
			::sth::sthCore::processError returnKeyedList "::sth::createGreStack Failed: $greIf" {}
			return $::sth::sthCore::FAILURE
		    }
		    
		    #stack the top ipif and the mplsif on greif
		    ::sth::sthCore::invoke stc::config $greTopIf "-StackedOnEndpoint-targets $greIf"
		    if {[info exists mplsIf]} {
			::sth::sthCore::invoke stc::config $mplsIf "-StackedOnEndpoint-targets $greIf"
		    }
		    set greIpif [::sth::sthCore::invoke stc::get $greIf -StackedOnEndpoint-targets]
		}
			
		    #enable/disable BFD
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(bfd_registration)]} {
			
		    configBfdRegistration $ldpRouterHandle ::sth::Ldp::emulation_ldp_config_user_input_args_array(mode) ::sth::Ldp::emulation_ldp_config_user_input_args_array
			
		    #bfd relation
		    set bfdRtrCfg [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-bfdrouterconfig]
		    if {[llength $bfdRtrCfg] != 0} {
			    #Rxu: once hltapi support dual stack, the following should be changed accordingly
			    set ipResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -TopLevelIf-Targets]
			    ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets \"$ipResultIf\""
		    }
		}
	    
		#Configure the created LDP router with user input
		::sth::sthCore::log debug "Processing the switches for command:$_hltCmdName"
        
		set objList {LdpRouterConfig Ipv4If Ipv6If Ipv6If_Link_Local Router VlanIf VlanIf_Outer Aal5If}
		array set cmdArray {
			LdpRouterConfig ""
			Ipv4If ""
			Ipv6If ""
			Ipv6If_Link_Local ""
			Router ""
			VlanIf ""
			VlanIf_Outer ""
			Aal5If ""
		}
		array set hdlArray {
			ldpRouterConfig ""
			Ipv4If ""
			Ipv6If ""
			Ipv6If_Link_Local ""
			Router ""
			VlanIf ""
			VlanIf_Outer ""
			Aal5If ""
		}
	    
		set hdlArray(LdpRouterConfig) $ldpRouterConfigHandle
		if {[catch {set hdlArray(Ipv4If) [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv4If]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch Ipv4If Handle. Error: $getStatus"
		} else {
		    #add for gre case. delete the greipif from the list
		    if {[info exists greIpif] } {
			set ix [lsearch -exact $hdlArray(Ipv4If) $greIpif]
			if {$ix >=0 } {
			    set hdlArray(Ipv4If) [lreplace $hdlArray(Ipv4If) $ix $ix]
			}
		    }
		    ::sth::sthCore::log debug "Ipv4If handle to be configured:$hdlArray(Ipv4If)"
		}
	    
	       
		
		if {[catch {set hdlArray(Ipv6If) [lindex [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv6If] 0]
				set hdlArray(Ipv6If_Link_Local) [lindex [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Ipv6If] 1]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch Ipv6If Handle. Error: $getStatus"
		} else {
		    #add for gre case. delete the greipif from the list
		    if {[info exists greIpif] } {
			set ix [lsearch -exact $hdlArray(Ipv6If) $greIpif]
			if {$ix >=0 } {
			    set hdlArray(Ipv6If) [lreplace $hdlArray(Ipv6If) $ix $ix]
			}
		    }
		    ::sth::sthCore::log debug "Ipv6If handle to be configured:$hdlArray(Ipv6If)"
		}		
		
		set hdlArray(Router) $ldpRouterHandle	
		
		if {[catch {set hdlArray(Aal5If) [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-Aal5If]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch Aal5If Handle. Error: $getStatus"
		} else {
		    ::sth::sthCore::log debug "Aal5If handle to be configured:$hdlArray(Aal5If)"
		}
		
		if {[catch {set VlanIfHandle [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-VlanIf]} getStatus]} {
		    ::sth::sthCore::log error "Unable to fetch VlanIf Handle. Error: $getStatus"
		} else {
		    ::sth::sthCore::log debug "VlanIf handle to be configured:$VlanIfHandle"	
		}
		if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_id)] && [info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_outer_id)]} {
			#There is S-Vlan and C-vlan
			lappend hdlArray(VlanIf_Outer) [lindex $VlanIfHandle 1]
			lappend hdlArray(VlanIf) [lindex $VlanIfHandle 0]
		} elseif {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_id)] && ![info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(vlan_outer_id)]} {
			lappend hdlArray(VlanIf) $VlanIfHandle
		}
		
		#Configure the created Ldp router with user input (options)
		::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
		set userInputList [array get ::sth::Ldp::emulation_ldp_config\_user_input_args_array]
		#remove those input switches without processing functions
		set switchWithoutFunc {count handle intf_ip_addr_step gateway_ip_addr_step loopback_ip_addr_step label_step lsr_id_step mode port_handle remote_ip_addr_step vlan_id_mode vlan_outer_id_mode mandatory_args optional_args \
					ip_version intf_ipv6_addr_step link_local_ipv6_addr_step gateway_ipv6_addr_step ipv6_router_id_step remote_ipv6_addr_step hello_type use_gateway_as_dut_ip_addr use_gateway_as_dut_ipv6_addr authentication_mode password md5_key_id expand}
		foreach switchName $switchWithoutFunc {
		    set switchIndex [lsearch $userInputList $switchName]
		    if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
			set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
		    }
		}
		
		foreach {switchName switchValue} $userInputList {
		    ::sth::sthCore::log debug "Trying to process the switch $switchName"
		    if {$switchName == "tunnel_handle"} {
		       continue
		    }
		    set switchProcFunc [::sth::sthCore::getModeFunc2 ::sth::Ldp:: emulation_ldp_config $switchName $::sth::Ldp::emulation_ldp_config_user_input_args_array(mode)]
		    
		    #@TODO Change this to pass the value of the handle itself
		    set handleSwitchName $ldpRouterHandle
		    
		    #if processing function is processConfigCmd, append the attribute/value pair to 
		    #corresponding array element for processing later
		    if {[string equal $switchProcFunc "processConfigCmd"]} {
				set stcObjName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_config $switchName stcobj]
				set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_ldp_config $switchName stcattr]
				if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_config $switchName $switchValue]} getStatus]} {
					append cmdArray($stcObjName) " -$stcAttrName $attrValue"
				} else {
					append cmdArray($stcObjName) " -$stcAttrName $switchValue"
				}
				if {$stcAttrName == "AffiliatedRouter-targets"} {
					set mac_addr ""
					set aff_router_handle $::sth::Ldp::emulation_ldp_config_user_input_args_array(affiliated_router_target)
					if {[catch {set mac_addr [::sth::sthCore::invoke stc::get $aff_router_handle -SourceMac]} getStatus]} {
					::sth::sthCore::log error "Unable to fetch SourceMac form $aff_router_handle. Error: $getStatus"
					}
					append cmdArray($stcObjName) $mac_addr
				}
			
				#puts "\tcmdArray($stcObjName)=$cmdArray($stcObjName)"
				 
		    } else {
				set cmd "::sth::Ldp::$switchProcFunc {$switchValue} returnKeyedList $_hltCmdName $switchName switchToOutput $handleSwitchName"
				::sth::sthCore::log debug "CMD to Process: $cmd "
				set cmdResult [eval $cmd]
				::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
				if {$cmdResult == $::sth::sthCore::FAILURE} {
					set cmdFailed $::sth::Ldp::TRUE
					set errOccured $::sth::Ldp::TRUE
					set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch $switchName with Value $switchValue"
					::sth::sthCore::log error "$logStatus"
					break
				}
		    }
		}
		set cmds [array get cmdArray]
        
		#process all switches handled by processConfigCmd
		foreach objName $objList {
		    if {($cmdArray($objName) != "") & ([string length $hdlArray($objName)] > 3)} {
			set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
			if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
			    ::sth::sthCore::log debug "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus"
			    set cmdFailed $::sth::Ldp::TRUE
			    set errOccured $::sth::Ldp::TRUE
			    set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
			    ::sth::sthCore::log error "$logStatus"
			} else {
				::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
			}
		    }
		}
	    
		if {[::info exists cmdFailed]} {
		    ::sth::sthCore::log error "Error Occured configuring LDP router: $returnKeyedList"
		    #Delete the LDP router Object
		    if {[catch {::sth::sthCore::invoke stc::delete $ldpRouterHandle} eMsg ]} {
			::sth::sthCore::log error "Error deleting previously created LDP router:$ldpRouterHandle Msg: $eMsg"
		    }
		    set errOccured $::sth::Ldp::TRUE
		    return $FAILURE
		} else {
		    set tmpHandleList {}
		    catch {set tmpHandleList [keylget returnKeyedList handle]}
		    lappend tmpHandleList $ldpRouterHandle
		    keylset returnKeyedList handle $tmpHandleList
		    keylset returnKeyedList handles $tmpHandleList
		    set errOccured $::sth::Ldp::FALSE
		    return $SUCCESS
		}
	} else {
		#RXu: Enable LDP under an existing device
		 set ldpRouterHandles $::sth::Ldp::emulation_ldp_config_user_input_args_array(handle)
		 unset ::sth::Ldp::emulation_ldp_config_user_input_args_array(optional_args)
		 unset ::sth::Ldp::emulation_ldp_config_user_input_args_array(mandatory_args)
		 foreach hname {loopback_ip_addr vpi_step  vpi vci_step vci tunnel_handle vlan_outer_user_priority vlan_outer_id_step vlan_outer_id vlan_user_priority vlan_id_step vlan_id \
					vlan_cfi  cfi lsr_id  intf_prefix_length  gateway_ip_addr intf_ip_addr mac_address_init  affiliated_router_target  ip_version intf_ipv6_addr_step link_local_ipv6_addr_step \
                                        gateway_ipv6_addr_step ipv6_router_id_step remote_ipv6_addr_step remote_ip_addr_step} {
			if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array($hname)]} {
				unset ::sth::Ldp::emulation_ldp_config_user_input_args_array($hname)
			}
		 }
		 foreach ldpRouterHandle $ldpRouterHandles {
			if {[::sth::sthCore::invoke stc::get $ldpRouterHandle -children-LdpRouterConfig] != ""} {
				::sth::sthCore::processError returnKeyedList "$ldpRouterHandle already has LDP enable" {}
				set errOccured $::sth::Ldp::TRUE
				return $::sth::sthCore::FAILURE
			}
			#Creat LdpRouterConfig under router
		       if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $ldpRouterHandle  -CreateClassId [string tolower LdpRouterConfig]]
				      set ldpRouterConfigHandle $ProtocolCreateOutput(-ReturnList)} createStatus]} {
			   ::sth::sthCore::processError returnKeyedList "Interal command error while creating LDPRouterConfig. Error: $createStatus" {}
			   set errOccured $::sth::Ldp::TRUE
			   return $FAILURE
		       } 
		       #enable/disable BFD
		       if {[info exists ::sth::Ldp::emulation_ldp_config_user_input_args_array(bfd_registration)]} {
			       configBfdRegistration $ldpRouterHandle ::sth::Ldp::emulation_ldp_config_user_input_args_array(mode) ::sth::Ldp::emulation_ldp_config_user_input_args_array
			       #bfd relation
			       set bfdRtrCfg [::sth::sthCore::invoke stc::get $ldpRouterHandle -children-bfdrouterconfig]
			       if {[llength $bfdRtrCfg] != 0} {
					   set ipResultIf [::sth::sthCore::invoke stc::get $ldpRouterHandle -PrimaryIf-Targets]
				       ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets \"$ipResultIf\""
			       }
			   }
		       set ldpRouterConfig_List ""
		       
		       foreach hname [array names ::sth::Ldp::emulation_ldp_config_user_input_args_array] {
			       set stcobj      [::sth::sthCore::getswitchprop ::sth::Ldp::  emulation_ldp_config $hname stcobj]
			       if {![regexp -nocase $stcobj $ldpRouterConfigHandle]} {continue}
			#       if {[regexp -nocase "$hname\\s" "egress_label_mode label_adv peer_discovery "]} {
			#	       set stcvalue  [::sth::sthCore::getFwdmap      ::sth::Ldp::  emulation_ldp_config  $hname  $::sth::Ldp::emulation_ldp_config_user_input_args_array($hname)]
			#       } else {
			#	       set stcvalue  $::sth::Ldp::emulation_ldp_config_user_input_args_array($hname)
			#       }
				set switchValue $::sth::Ldp::emulation_ldp_config_user_input_args_array($hname)
				if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_ldp_config $hname $switchValue]} getStatus]} {
					set stcvalue $attrValue
				} else {
					set stcvalue $switchValue
				}
			       set stcattr     [::sth::sthCore::getswitchprop  ::sth::Ldp::  emulation_ldp_config $hname stcattr]
                               if {![regexp -nocase "^_none_$" $stcattr]} {
                                        lappend  ldpRouterConfig_List -$stcattr $stcvalue
                                }
			       
		       }
		       if {$ldpRouterConfig_List  != ""} {
			       ::sth::sthCore::invoke stc::config $ldpRouterConfigHandle $ldpRouterConfig_List
		       }
		}
		keylset returnKeyedList handle  $ldpRouterHandles
		keylset returnKeyedList handles $ldpRouterHandles
		set errOccured $::sth::Ldp::FALSE
		return $SUCCESS
		#RXu: Enable LDP under an existing device
	}
}

proc ::sth::Ldp::configBfdRegistration {rtrHandle mode switchArgs} {
        upvar $switchArgs userArgsArray
   
    if {[catch {set ldpRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-ldprouterconfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::getNew Failed: $err" {}
        return -code error $returnKeyedList          
    }
    
    if {$userArgsArray(bfd_registration) == "1"} {
        #create new bfdrouterconfig if no exiting bfd found
        set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
        if {[llength $bfdrtrcfg] == 0} {
            if {[catch {set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::create Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        if {[catch {::sth::sthCore::invoke stc::config $ldpRtrHandle "-EnableBfd true"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    } else {
        if {[catch {::sth::sthCore::invoke stc::config $ldpRtrHandle "-EnableBfd false"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    }
}    



###/*! \ingroup ldphelperfuncs
### \fn IsLdpRouterHandleValid (str handle, varRef msgName)
###\brief Validates value against ldp_handle
###
###This procedure checks if the value is valid ldp router Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###*/
###
### IsLdpRouterHandleValid (str handle, varRef msgName);
###

proc ::sth::Ldp::IsLdpRouterHandleValid { handle msgName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set cmdStatus $::sth::Ldp::FALSE
	
	upvar 1 $msgName errorMsg

	if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} getStatus]} {
		::sth::sthCore::log error "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"
		return $FAILURE
	} else {
		foreach routerHandle $routerHandleList {
			if {[string equal $routerHandle $handle]} {
				set cmdStatus $::sth::Ldp::TRUE
				break
			}
		}
		
		if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $routerHandle -children-LdpRouterConfig]} getStatus]} {
			set cmdStatus $::sth::Ldp::FALSE
		}

		if {$cmdStatus == $::sth::Ldp::TRUE} {

			return $SUCCESS
		} else {
			set errorMsg "Value ($handle) is not a valid Ldp router handle"
			return $FAILURE		
		}		
	}
}

###/*! \ingroup ldphelperfuncs
### \fn IsLspHandleValid (str handle, varRef msgName)
###\brief Validates value against lsp handle
###
###This procedure checks if the value is valid lsp Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###*/
###
### IsLspHandleValid (str handle, varRef msgName);
###

proc ::sth::Ldp::IsLspHandleValid { lspHandle msgName } {

	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	
	set cmdStatus $::sth::Ldp::FALSE
	
	upvar 1 $msgName errorMsg

	if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-emulateddevice]} getStatus]} {
		::sth::sthCore::log error "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"
		return $FAILURE
	} else {
		foreach routerHandle $routerHandleList {
			if {![catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $routerHandle -children-LdpRouterConfig]} getStatus]} {
				foreach lspObj {Ipv4PrefixLsp Ipv6PrefixLsp Ipv4IngressPrefixLsp Ipv6IngressPrefixLsp VcLsp GeneralizedPwidLsp P2mpLsp} {
                                        if {![catch {set prefixLspHandleList [::sth::sthCore::invoke stc::get $ldpRouterConfigHandle -children-$lspObj]} getStatus]} {
                                                if {[::info exists prefixLspHandleList]} {
                                                        foreach prefixLspHandle $prefixLspHandleList {
                                                                if {[string equal $lspHandle $prefixLspHandle]} {
                                                                        set cmdStatus $::sth::Ldp::TRUE
                                                                        break
                                                                }
                                                        }	
                                                }
                                        }
                                }
			
                                
			}
			if {$cmdStatus == $::sth::Ldp::TRUE} {
				break
			}	
		}
		
		#puts "cmdStatus = $cmdStatus"
		if {$cmdStatus == $::sth::Ldp::TRUE} {
			return $SUCCESS
		} else {
			set errorMsg "Value ($lspHandle) is not a valid lsp handle"
			return $FAILURE		
		}		
	}
}


proc ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_create { userInput returnKeyedListVarName} {
        
	set _OrigHltCmdName "emulation_lsp_switching_point_tlvs_config"
	set _hltCmdName "emulation_lsp_switching_point_tlvs_config_create"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	
	
	upvar 1 $returnKeyedListVarName returnKeyedList
        
        #check for the valid LDP lsp handle
        if {[::info exists ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(lsp_handle)]} {
                set lspHandle $::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(lsp_handle)
                #check if the lsp handle is valid
                if {![regexp -nocase "vclsp" $lspHandle] && 
                    ![regexp -nocase "GeneralizedPwidLsp" $lspHandle] &&
                    ![regexp -nocase "P2mpLsp" $lspHandle]} {
                        ::sth::sthCore::log error "Invalid Value of lsp_handle"
                        return -code 1 -errorcode -1  "Invalid Value of lsp_handle"
                }
        } else {
                ::sth::sthCore::log error "To create a switching piont tlvs, valid lsp handle, \"lsp_handle\" switch, is required"
                return -code 1 -errorcode -1 "To create a switching piont tlvs, valid lsp handle, \"lsp_handle\" switch, is required"
        }
        set tlv_handle [::sth::sthCore::invoke stc::create PseudoWireSwitchingPointTlv -under $lspHandle]
        config_switching_point_tlvs $tlv_handle
        keylset returnKeyedList tlv_handle $tlv_handle
}

proc ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_modify { userInput returnKeyedListVarName} {
 
	
	set _OrigHltCmdName "emulation_lsp_switching_point_tlvs_config"
	set _hltCmdName "emulation_lsp_switching_point_tlvs_config_modify"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

        if {[::info exists ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(tlv_handle)]} {
		set tlvHandle $::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(tlv_handle)
		#check if the lsp handle is valid
		if {![regexp -nocase "PseudoWireSwitchingPointTlv" $tlvHandle]} {
			::sth::sthCore::log debug "Invalid Value of tlv_handle"
                        return -code 1 -errorcode -1 "Invalid Value of tlv_handle"
		}
	} else {
                ::sth::sthCore::log error "To modify a switching piont tlvs, valid tlv handle, \"tlv_handle\" switch, is required"
                return -code 1 -errorcode -1  "To modify a switching piont tlvs, valid tlv handle, \"tlv_handle\" switch, is required"        
	}
        config_switching_point_tlvs $tlvHandle
}

proc ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_delete { userInput returnKeyedListVarName} {

	set _OrigHltCmdName "emulation_lsp_switching_point_tlvs_config"
	set _hltCmdName "emulation_lsp_switching_point_tlvs_config_delete"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	    
        if {[::info exists ::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(tlv_handle)]} {
                set tlvHandle $::sth::Ldp::emulation_lsp_switching_point_tlvs_config_user_input_args_array(tlv_handle)
                #check if the lsp handle is valid
                if {![regexp -nocase "PseudoWireSwitchingPointTlv" $tlvHandle]} {
                        ::sth::sthCore::log debug "Invalid Value of tlv_handle"
                        return -code 1 -errorcode -1 "Invalid Value of tlv_handle"	
                }
        } else {
                ::sth::sthCore::log error "To delete a switching piont tlvs, valid tlv handle, \"tlv_handle\" switch, is required"
                return -code 1 -errorcode -1  "To delete a switching piont tlvs, valid tlv handle, \"tlv_handle\" switch, is required"
        }
        ::sth::sthCore::invoke stc::delete $tlvHandle

}


proc ::sth::Ldp::config_switching_point_tlvs {tlv_handle} {
        set userInputList [array get ::sth::Ldp::emulation_lsp_switching_point_tlvs_config\_user_input_args_array]
        set switchWithoutFunc {tlv_handle lsp_handle mode mandatory_args optional_args}
	foreach switchName $switchWithoutFunc {
		set switchIndex [lsearch $userInputList $switchName]
		if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
			set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
		}
	}
	set configList ""
        array set userInputArray $userInputList
	foreach {switchName switchValue} $userInputList {
		::sth::sthCore::log debug "Trying to process the switch $switchName $switchValue"
                #check dependency
                set dependency [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_lsp_switching_point_tlvs_config $switchName dependency]
                if {![regexp -nocase "_none_" $dependency]} {
                        set dependencyAttr [lindex $dependency 0]
                        set dependencyValue [lindex $dependency 1]
                        if {![info exists userInputArray($dependencyAttr)]} {
                                continue
                        } elseif {$userInputArray($dependencyAttr) != $dependencyValue} {
                                continue
                        }
                }
                set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: emulation_lsp_switching_point_tlvs_config $switchName stcattr]
		if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: emulation_lsp_switching_point_tlvs_config $switchName $switchValue]} getStatus]} {
                        append configList " -$stcAttrName $attrValue"
                } else {
                        append configList " -$stcAttrName $switchValue"
                }
        }
        
        ::sth::sthCore::invoke stc::config $tlv_handle $configList
}


proc ::sth::Ldp::emulation_ldp_route_element_config_create { userInput returnKeyedListVarName} {
        
	set _OrigHltCmdName "emulation_ldp_route_element_config"
	set _hltCmdName "emulation_ldp_route_element_config_create"
	::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

	upvar 1 $returnKeyedListVarName returnKeyedList

    #check for the valid LDP lsp handle
    if {[::info exists ::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(lsp_handle)]} {
        set lspHandle $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(lsp_handle)
        #check if the lsp handle is valid
        if {![regexp -nocase "vclsp" $lspHandle] && 
            ![regexp -nocase "GeneralizedPwidLsp" $lspHandle] &&
            ![regexp -nocase "P2mpLsp" $lspHandle]} {
                ::sth::sthCore::log error "Invalid Value of lsp_handle"
                return -code 1 -errorcode -1  "Invalid Value of lsp_handle"
        }
    } else {
        ::sth::sthCore::log error "To create a switching piont tlvs, valid lsp handle, \"lsp_handle\" switch, is required"
        return -code 1 -errorcode -1 "To create a switching piont tlvs, valid lsp handle, \"lsp_handle\" switch, is required"
    }
    
    
    switch -exact -- $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_type) \
        p2mp_custom_element {
            set element_handle [::sth::sthCore::invoke stc::create LdpMldpCustomOpaque -under $lspHandle]
            config_ldp_route_elements $element_handle emulation_ldp_route_element_config
        }\
        generalized_pwid_switch_tlv {
            set element_handle [::sth::sthCore::invoke stc::create PseudoWireSwitchingPointTlv -under $lspHandle]
            config_lsp_route_elements $element_handle emulation_lsp_switching_point_tlvs_config
        }\
        default {
        }

    keylset returnKeyedList element_handle $element_handle
}

 proc ::sth::Ldp::emulation_ldp_route_element_config_modify { userInput returnKeyedListVarName} {

	 set _OrigHltCmdName "emulation_ldp_route_element_config"
	 set _hltCmdName "emulation_ldp_route_element_config_modify"
	 ::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

	if {[::info exists ::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_handle)]} {
		set eleHandle $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_handle)
		#check if the lsp handle is valid
		
		if {![regexp -nocase "PseudoWireSwitchingPointTlv" $eleHandle] &&
		    ![regexp -nocase "LdpMldpCustomOpaque" $eleHandle]} {
			::sth::sthCore::log debug "Invalid Value of element_handle"
			return -code 1 -errorcode -1 "Invalid Value of element_handle"
		}
	} else {
		::sth::sthCore::log error "To modify LDP route elements, valid handle, \"element_handle\" switch, is required"
		return -code 1 -errorcode -1  "To modify LDP route elements, valid handle, \"element_handle\" switch, is required"        
	}
    
    switch -exact -- $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_type) \
        p2mp_custom_element {
            config_ldp_route_elements $eleHandle emulation_ldp_route_element_config
        }\
        generalized_pwid_switch_tlv {
            config_lsp_route_elements $eleHandle emulation_lsp_switching_point_tlvs_config
        }\
        default {
        }

    keylset returnKeyedList element_handle $eleHandle
 }

 proc ::sth::Ldp::emulation_ldp_route_element_config_delete { userInput returnKeyedListVarName} {

	 set _OrigHltCmdName "emulation_ldp_route_element_config"
	 set _hltCmdName "emulation_ldp_route_element_config_delete"
	 ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
	    
         if {[::info exists ::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_handle)]} {
                 set eleHandle $::sth::Ldp::emulation_ldp_route_element_config_user_input_args_array(element_handle)
                 #check if the lsp handle is valid
                 if {![regexp -nocase "PseudoWireSwitchingPointTlv" $eleHandle] &&
					 ![regexp -nocase "LdpMldpCustomOpaque" $eleHandle]} {
						::sth::sthCore::log debug "Invalid Value of element_handle"
						return -code 1 -errorcode -1 "Invalid Value of element_handle"	
                 }
         } else {
                 ::sth::sthCore::log error "To delete valid element handle, \"element_handle\" switch, is required"
                 return -code 1 -errorcode -1  "To delete valid element handle, \"element_handle\" switch, is required"
         }
         ::sth::sthCore::invoke stc::delete $eleHandle

 }

proc ::sth::Ldp::config_ldp_route_elements {element_handle cmdName} {
    set userInputList [array get ::sth::Ldp::$cmdName\_user_input_args_array]
    set switchWithoutFunc {element_handle lsp_handle mode mandatory_args optional_args}
    
    foreach switchName $switchWithoutFunc {
        set switchIndex [lsearch $userInputList $switchName]
        if {$switchIndex > $::sth::Ldp::FALSE_MINUS_ONE} {
            set userInputList [lreplace $userInputList $switchIndex [expr "$switchIndex+1"]]
        }
    }
    set configList ""
    array set userInputArray $userInputList
    foreach {switchName switchValue} $userInputList {
        ::sth::sthCore::log debug "Trying to process the switch $switchName $switchValue"
        #check dependency
        set dependency [::sth::sthCore::getswitchprop ::sth::Ldp:: $cmdName $switchName dependency]
        if {![regexp -nocase "_none_" $dependency]} {
            set dependencyAttr [lindex $dependency 0]
            set dependencyValue [lindex $dependency 1]
            if {![info exists userInputArray($dependencyAttr)]} {
                continue
            } elseif {$userInputArray($dependencyAttr) != $dependencyValue} {
                continue
            }
        }
		set stcAttrName [::sth::sthCore::getswitchprop ::sth::Ldp:: $cmdName $switchName stcattr]
		if {[regexp -nocase "_none_" $stcAttrName]} {
			continue
		}
        if {![catch {set attrValue [::sth::sthCore::getFwdmap ::sth::Ldp:: $cmdName $switchName $switchValue]} getStatus]} {
            append configList " -$stcAttrName $attrValue"
        } else {
            append configList " -$stcAttrName $switchValue"
        }
    }

    ::sth::sthCore::invoke stc::config $element_handle $configList
}
