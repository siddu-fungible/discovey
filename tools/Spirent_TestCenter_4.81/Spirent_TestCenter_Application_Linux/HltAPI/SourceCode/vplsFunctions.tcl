# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Vpls {
    array set VpnHandleList {}
    #array set peHandleList {}
    set createResultQuery 0
}

###########################################################
#VPLS PE config
###########################################################
###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::emulation_vpls_l2vpn_pe_Generic { str switchArgs str mySortedPriorityList str procPrefix} {
###\breif Returns  $::sth::sthCore::SUCCESS or $::sth::sthCore::FAILURE
###
###This procedure is used to config Vpls PE based on the user input.
###
###\param[in] switchArgs contains the user input
###\param[in] mySortedPriorityList contains prioritized list of user input
###\param[in] procPrefix contains the subcommand table name and the version number of the session
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::emulation_vpls_l2vpn_pe_Generic {switchArgs mySortedPriorityList procPrefix}
proc ::sth::Vpls::emulation_l2vpn_pe_config_Generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_l2vpn_pe_config"    
    set _hltCmdName "emulation_vpls_l2vpn_pe_Generic"
    set _hltNameSpace "::sth::Vpls::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    #check if mandatory switches are all provided
    
    #foreach  man_switch [array get ${_hltNameSpace}${_OrigHltCmdName}] {}

    # subscribe resultdataset
    if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Vpls:: LdpRouterConfig LdpRouterResults returnKeyedList]} {
	    ::sth::sthCore::processError returnKeyedList "Error subscribing the Ldp router (PE) result data set"
            set cmdState $FAILURE
	    return $returnKeyedList
    }
    
    set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
    if {[catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
    					[list -ResultRootList $::sth::GBLHNDMAP(project) \
					-ConfigClassId LdpRouterConfig \
					-ResultClassId LdpLspResults]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Error create the Ldp router (PE) ResultQuery"
        set cmdState $FAILURE
	return $returnKeyedList        
    }
    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
    
    #Check if te port_handle is valid
    if {![::info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when creating vpls l2vpn pe"
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]
    }
	
    if {![::sth::sthCore::IsPortValid $portHandle msg]} {
	::sth::sthCore::log debug "Invalid Value of port_handle"
	set cmdState $FAILURE
	return $returnKeyedList
    }

    #get number of PE to create
    if {![::info exists ${_hltSpaceCmdName}\_user_input_args_array(pe_ip_addr_count)]} {
        set ${_hltSpaceCmdName}\_user_input_args_array(pe_ip_addr_count) 1
    } 
    set peCount [set ${_hltSpaceCmdName}\_user_input_args_array(pe_ip_addr_count)]

    #addressStepProcess
    array set IpAddressList {}
    set IpStepSwitchList {pe_ip_addr_step pe_ip_addr_start pe_gateway_ip_addr_step pe_gateway_ip_addr}
    
    #todo if peCount > 1, IpStepSwitchList will available
    foreach {IpStep IpAddrType} $IpStepSwitchList {
        if { $peCount == 1 } {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array($IpAddrType)]} {
                ::sth::sthCore::processError returnKeyedList "Error with invalid IP address, when executing -$IpAddrType" {}
		set cmdState $FAILURE
		return $returnKeyedList               
            }
            set IpAddressList($IpAddrType) [set ${_hltSpaceCmdName}\_user_input_args_array($IpAddrType)]
        } elseif { $peCount > 1 } {
            for {set i 0} {$i < $peCount} {incr i} {
                if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($IpStep)] && \
                    [info exists ${_hltSpaceCmdName}\_user_input_args_array($IpAddrType)]} {
                    set IpAddrStart [set ${_hltSpaceCmdName}\_user_input_args_array($IpAddrType)]
                    set IpAddrStepVal [set ${_hltSpaceCmdName}\_user_input_args_array($IpStep)]
                    if {![::sth::sthCore::isValidIpStepValue 4 $IpAddrStepVal]} {
                        ::sth::sthCore::processError returnKeyedList "Error with invalid IP step, when executing -$IpStep" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }  
                    lappend IpAddressList($IpAddrType) \
                        [::sth::sthCore::updateIpAddress 4 \
                                                         $IpAddrStart \
                                                         $IpAddrStepVal \
                                                         $i]                   
                } else {
                    ::sth::sthCore::processError returnKeyedList "If PE count more than 1,$IpAddrType and $IpStep should be present to use step functionality" 
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                ::sth::sthCore::log debug "pe config:$i The new $IpAddrType Value list is $IpAddressList($IpAddrType)."
            #end of for
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "PE count is not a correct Numeric."
            set cmdState $FAILURE
            return $returnKeyedList            
        }
    #end of foreach
    }
    #::sth::sthCore::updateIpAddress ipVersion ipAddressValue stepValue stepCnt    

    #create PE
    #if RSVP are turn on
    array set configUserSwitch {}
#    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(traffic_engineering)]} {
        #TODO finish up 
#    } else {
        #only LDP be used
        for { set i 0} { $i < $peCount } { incr i } {        
                foreach { _switch _switchVal} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
                    if {$_switch != "optional_args"} {
                        if {$_switch != "mandatory_args"} {
                            set configUserSwitch($_switch) $_switchVal
                        }
                    }
                }
                foreach IpAddrType [array names IpAddressList] {
                    set configUserSwitch($IpAddrType) [lindex $IpAddressList($IpAddrType) $i]
                }                
                
                set childCmdState $::sth::sthCore::SUCCESS
                #createLdpRouters(PE) : proc ::sth::sthCore::configureNextMacAddress { routerHandle }
                ::sth::sthCore::log debug "pe config: ProcessCreateOneLdpRouter configUserSwitch."
                set peHandle [${_hltNameSpace}ProcessCreateOneLdpRouter configUserSwitch returnKeyedList childCmdState]
                if { !$childCmdState } {
			::sth::sthCore::processError returnKeyedList "Error occured while creating/configuring the PE (LDP router) number $i"
			set cmdState $::sth::sthCore::FAILURE
                        #return returnKeyedList
		} else {
			::sth::sthCore::log debug "Successfully created/configured the PE (LDP router) number {$i} $returnKeyedList "                    
                }
                
                #set traffic_engineering "LDP"
                #if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(traffic_engineering)]} {
                #    set traffic_engineering "RSVP"
                #}
                #
                ##GetMPLSCoreRouter $portHandle $peHandle $traffic_engineering returnKeyedList childCmdState
                #if {!$childCmdState} {
                #    ::sth::sthCore::processError returnKeyedList "Error occured while linking the PE $i to relevant MPLS core session."
                #    set cmdState $::sth::sthCore::FAILURE                    
                #}
                
                #if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(traffic_engineering)]} {
                #    ${_hltNameSpace}ProcessCreateRsvpTunnel $peHandle returnKeyedList childCmdState
                #    if { !$childCmdState } {
                #        ::sth::sthCore::processError returnKeyedList "Error occured while creating/configuring the PE (LDP router) number $i"
                #        set cmdState $::sth::sthCore::FAILURE
                #        #return $returnKeyedList
                #    }
                #}
        }        
#    }
    
    #if PE creation progress failed, delete already created PE
    if {!$childCmdState} {
	set cmdState $::sth::sthCore::FAILURE
	
        catch {set handleList [keylget returnKeyedList handle]}
	
        foreach ldpHandle $handleList {
            set deleteHandle [::sth::sthCore::invoke stc::get $handle -parent]
	    if {[catch {::sth::sthCore::invoke stc::delete $deleteHandle} deleteStatus]} {
		::sth::sthCore::processError returnKeyedList "Error when trying to delete the handles $handleList"
	    }
	}
        
        catch {keyldel returnKeyedList handle}	
    }
    
    #return value process
    if {$childCmdState} {
	set cmdState $::sth::sthCore::SUCCESS
	return $returnKeyedList
    } else {
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }       
}


###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::ProcessCreateOneLdpRouter { str userInput str returnKeyedListVarName bool cmdStatusVarName} {
###\breif Returns  $returnKeyedList : success- key handle in $returnKeyedList, failure-error log in $returnKeyedList
###Returns: success-cmdStatusVarName $::sth::sthCore::SUCCESS, failure-cmdStatusVarName $::sth::sthCore::FAILURE
###
###This procedure is used to create an ldp router (PE) object based on the user input.
###
###\param[in] userInput contains the user input
###\param[in] returnKeyedListVarName contains prioritized list of user input
###\param[in] cmdStatusVarName contains the cmd executing status
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::ProcessCreateOneLdpRouter { userInput returnKeyedListVarName cmdStatusVarName }
proc ::sth::Vpls::ProcessCreateOneLdpRouter { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_l2vpn_pe_config"    
    set _hltCmdName "ProcessCreateOneLdpRouter"
    set _hltNameSpace "::sth::Vpls::"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    upvar 1 $userInput UserInputArray

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
       
    #Create the Ldp router under the port and then configure the other parameters.
    set port_handle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]

    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)]} {
	# There is vlan
	set IfStack "Ipv4If VlanIf EthIIIf"
	set IfCount "1 1 1"
    } else {
	# There is no vlan
	set IfStack "Ipv4If EthIIIf"
	set IfCount "1 1"
    }
    
    #create unque msc_addr for PE
    #TODO finish up

    array set DeviceCreateOutput [::sth::sthCore::invoke "stc::perform DeviceCreate\
    							 -ParentList $::sth::GBLHNDMAP(project)\
							 -DeviceType Router\
							 -IfStack \"$IfStack\"\
							 -IfCount \"$IfCount\"\
							 -Port $port_handle"]
    set pe_ldpRouterHandle $DeviceCreateOutput(-ReturnList)

    
    #Creat LdpRouterConfig under router
    array set ProtocolCreateOutput [::sth::sthCore::invoke "stc::perform ProtocolCreate\
    								-ParentList $pe_ldpRouterHandle\
								-CreateClassId [string tolower LdpRouterConfig]"]
    set pe_ldpRouterConfigHandle $ProtocolCreateOutput(-ReturnList)

    
    #Configure the created LDP router with user input
    ::sth::sthCore::log debug "Processing the switches for command:$_hltCmdName"
    
    set objList {LdpRouterConfig Ipv4If Router VlanIf}
    
    array set cmdArray {
    	LdpRouterConfig ""
    	Ipv4If ""
    	Router ""
    	VlanIf ""
    }
    array set hdlArray {
    	ldpRouterConfig ""
    	Ipv4If ""
    	Router ""
    	VlanIf ""
    }
    
    set hdlArray(LdpRouterConfig) $pe_ldpRouterConfigHandle
    
    if {[catch {set hdlArray(Ipv4If) [::sth::sthCore::invoke stc::get $pe_ldpRouterHandle -children-Ipv4If]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch Ipv4If Handle. Error: $getStatus"
    } else {
	::sth::sthCore::log debug "Ipv4If handle to be configured:$hdlArray(Ipv4If)"
    }
	
    set hdlArray(Router) $pe_ldpRouterHandle	
	
    if {[catch {set hdlArray(VlanIf) [::sth::sthCore::invoke stc::get $pe_ldpRouterHandle -children-VlanIf]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VlanIf Handle. Error: $getStatus"
    } else {
	::sth::sthCore::log debug "VlanIf handle to be configured:$hdlArray(VlanIf)"	
    }

    #Configure the created Ldp router with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    set userInputList [array get UserInputArray]
    foreach {switchName switchValue} $userInputList {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        
        set switchProcFunc [::sth::sthCore::getModeFunc $_hltNameSpace $_OrigHltCmdName $switchName create]
	
        #if processing function is processConfigCmd, append the attribute/value pair to 
		#corresponding array element for processing later        
        if {[string equal $switchProcFunc "processConfigCmd"]} {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
	    if {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
		append cmdArray($stcObjName) " -$stcAttrName $attrValue"
	    } else {
		append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            }    
        } else {
            #TODO finish up
        }  
    }
    #process all switches handled by processConfigCmd
    foreach objName $objList {
	if {($cmdArray($objName) != "") & ([string length $hdlArray($objName)] > 3)} {
            set cmd "::sth::sthCore::invoke stc::config $hdlArray($objName)$cmdArray($objName)"
            if {[catch {::sth::sthCore::invoke stc::config $hdlArray($objName) $cmdArray($objName)} configStatus]} {
                ::sth::sthCore::log debug "Unable to set switch/value pair:$cmdArray($objName) for object:$objName. Error: $configStatus"
		set cmdFailed $::sth::sthCore::SUCCESS
		set cmdState $::sth::sthCore::SUCCESS
		set logStatus "$_OrigHltCmdName: $cmdFailed Error occured while configuring switch/value pair:$cmdArray($objName) for object:$objName"
		::sth::sthCore::processError returnKeyedList "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::processError returnKeyedList "Error Occured configuring PE LDP router: $returnKeyedList"
        #Delete the LDP router Object
	if {[catch {::sth::sthCore::invoke stc::delete $pe_ldpRouterHandle} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created PE LDP router:$pe_ldpRouterHandle Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    #for new STC version 3.00, set the prefix length of PE router(simulated router) to 32
    if {[catch {::sth::sthCore::invoke stc::config $hdlArray(Ipv4If) "-PrefixLength 32"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: Unable to set switch/value pair:-PrefixLength 32 for object:Ipv4If. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList    
    }

    set cmdState [MPLS_Tunnel_Select $port_handle $pe_ldpRouterConfigHandle returnKeyedList]
    if { !$cmdState } {
        ::sth::sthCore::processError returnKeyedList "Error occured while linking the PE $i to relevant MPLS core session."
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    #call start on Ldp router handle
    if {[catch {array set ret [::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $pe_ldpRouterHandle]} eMsg]} {
	::sth::sthCore::processError returnKeyedList "Internal Command Error while starting LDP router (PE) $ldpRouterHandle. Error: $eMsg" {}       
	set cmdState $FAILURE
	return $returnKeyedList 
    }	
    
    #Return Handle
    set tmpHandleList {}
    catch {set tmpHandleList [keylget returnKeyedList handle]}
    lappend tmpHandleList $pe_ldpRouterConfigHandle
    keylset returnKeyedList handle $tmpHandleList
    set cmdState $::sth::sthCore::SUCCESS
    return $pe_ldpRouterConfigHandle   
}

proc ::sth::Vpls::ProcessCreateRsvpTunnel { InputPeHandle returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_l2vpn_pe_config"    
    set _hltCmdName "ProcessCreateRsvpTunnel"
    set _hltNameSpace "::sth::Vpls::"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
#    upvar 1 $userInput UserInputArray

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $InputPeHandle"
    
    set peHandle $InputPeHandle
    
    #get the parent router handle
    if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $peHandle -parent]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not get the parent router handle of peHandle $peHandle. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    if {[info exists ${_hltSpaceCmdName}_user_input_args_array(pe_remote_ip_addr)]} {
        set DutIpVal [set ${_hltSpaceCmdName}_user_input_args_array(pe_remote_ip_addr)]
    } else {
        set DutIpVal "192.85.1.1"
    }
    
    #create rsvpRouterConfig object
    if {[catch {set rsvpHandle [::sth::sthCore::invoke stc::create RsvpRouterConfig -under $routerHandle "-DutIpAddr $DutIpVal"]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not create the rsvpRouterConfig object under pe router $peHandle. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }

    if {[info exists ${_hltSpaceCmdName}_user_input_args_array(pe_ip_addr_start)]} {
        set SrcIpVal [set ${_hltSpaceCmdName}_user_input_args_array(pe_ip_addr_start)]
    } else {
        set SrcIpVal "192.85.1.1"
    }
    
    set DstIpVal $DutIpVal
    
    #create rsvp Tunnel (ingress, PATH message)
    if {[catch {set rsvpIngressTunnelHandle [::sth::sthCore::invoke stc::create RsvpIngressTunnelParams -under $rsvpHandle "-SrcIpAddr $SrcIpVal -DstIpAddr $DstIpVal"]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not create the rsvpRouterConfig object under pe router $peHandle. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }
    
    #create rsvp Tunnel (egress, Resv message)
    if {[catch {set rsvpEgressTunnelHandle [::sth::sthCore::invoke stc::create RsvpEgressTunnelParams -under $rsvpHandle "-SrcIpAddr $DstIpVal -DstIpAddr $SrcIpVal"]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not create the rsvpRouterConfig object under pe router $peHandle. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }
    
    # subscribe resultdataset
    if {![::sth::sthCore::ResultDataSetSubscribe ::sth::Vpls:: RsvpRouterConfig RsvpRouterResults returnKeyedList]} {
	    ::sth::sthCore::processError returnKeyedList "Error subscribing the Ldp router (PE) result data set"
            set cmdState $FAILURE
	    return $returnKeyedList
    }
    
    set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
    ::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet \
    					[list -ResultRootList $::sth::GBLHNDMAP(project) \
					-ConfigClassId RsvpRouterConfig \
					-ResultClassId RsvpLspResults]
    ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
	
    #call start on rsvp router handle
    if {[catch {array set ret [::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $routerHandle]} eMsg]} {
	::sth::sthCore::processError returnKeyedList "Internal Command Error while starting LDP router (PE) $ldpRouterHandle. Error: $eMsg" {}       
	set cmdState $FAILURE
	return $returnKeyedList 
    }	
    
    set cmdState $SUCCESS
    return $rsvpHandle
}

######################################
#vpls site config
#####################################
###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::emulation_vpls_site_config_Generic { str userInput str returnKeyedListVarName bool cmdStatusVarName} {
###\breif Returns  $returnKeyedList : success- key handle in $returnKeyedList, failure- error log in $returnKeyedList
###Returns: success-cmdStatusVarName $::sth::sthCore::SUCCESS, failure-cmdStatusVarName $::sth::sthCore::FAILURE
###
###This procedure is used to config VPLS site (host) object based on the user input.
###
###\param[in] userInput contains the user input
###\param[in] returnKeyedListVarName contains prioritized list of user input
###\param[in] cmdStatusVarName contains the cmd executing status
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::emulation_vpls_site_config_Generic { userInput returnKeyedListVarName cmdStatusVarName }
proc ::sth::Vpls::emulation_vpls_site_config_Generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_vpls_site_config"    
    set _hltCmdName "emulation_vpls_site_config_Generic"
    set _hltNameSpace "::sth::Vpls::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS

    #check if mandatory switches are all provided
    
    #Check if the port_handle is valid
    #check if the pe_handle is valid
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]} {
        if {![::info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
            ::sth::sthCore::processError returnKeyedList error "port_handle or pe_handle is needed when creating vpls site"
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "Invalid Value of port_handle"
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    } else {
	set peHandle [set ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]
        
        #peHandle can be router handle or ldpRouterConfig handle or maybe bgpRouterconfig handle in the future
        #now only support router/ldpRouterConfig
        switch -regexp [string tolower $peHandle] {
            emulateddevice -
            router {
                if {[catch {set ldpConfigHandle [::sth::sthCore::invoke stc::get $peHandle -Children-LdpRouterConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "can not get ldpRouterConfig from $pe_handle : $errMsg"
                    set cmdState $FAILURE
                    return $returnKeyedList                     
                }
                
                if {$ldpConfigHandle == ""} {
                    #TODO finish
                } else {
                    set peHandle $ldpConfigHandle
                }
            }
            
            ldprouterconfig {
                #TODO finish
            }
            
            bgprouterconfig -
            default {
                ::sth::sthCore::processError returnKeyedList "the input Value of pe_handle is not valid: $peHandle"
                set cmdState $FAILURE
                return $returnKeyedList                
            }            
        }
        if {![::sth::Vpls::IsPEHandleValid $peHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "Invalid Value of pe_handle : $peHandle"
            set cmdState $FAILURE
            return $returnKeyedList        
        }        
    }
    

    
    #get numeber of site to create
    if {![::info exists ${_hltSpaceCmdName}\_user_input_args_array(site_count)]} {
        set ${_hltSpaceCmdName}\_user_input_args_array(site_count) 1
    } 
    set siteCount [set ${_hltSpaceCmdName}\_user_input_args_array(site_count)]
    
    set stepSwitchList {vlan vlan_step vpn_id vpn_id_step mac_addr mac_addr_step vc_id vc_id_step vlan_id vlan_id_step}

    #step the switch values,  create the site, vpn, modify the PE   
    for {set i 0} {$i < $siteCount} {incr i} {
        #if $i >1, step values
        if {$i >= 1} {
            foreach {switchname switchstepval} $stepSwitchList {
                if {[info exists ${_hltSpaceCmdName}\_user_input_args_array($switchname)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array($switchstepval)]} {
                    if { $switchname == "mac_addr" } {
                        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]} {
                            set MacCount [set ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]
                        } else {
                            set MacCount 1
                        }
                        #TODO finish up
                        set startMac [set ${_hltSpaceCmdName}\_user_input_args_array(mac_addr)]
                        set stepMac [set ${_hltSpaceCmdName}\_user_input_args_array(mac_addr_step)]
                        
                        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)]} {
                            if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]} {
                                set VlanCount [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]
                            } else {
                                set VlanCount 1
                            }
                            if {[catch {set MacVal [::sth::sthCore::macStep $startMac $stepMac [expr $i * $MacCount * $VlanCount]]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error occur when step the vpls site mac address"
                                set cmdState $FAILURE
                                return $returnKeyedList                             
                            }                            
                        } else {
                            if {[catch {set MacVal [::sth::sthCore::macStep $startMac $stepMac [expr $i * $MacCount]]} errMsg]} {
                                ::sth::sthCore::processError returnKeyedList "Error occur when step the vpls site mac address"
                                set cmdState $FAILURE
                                return $returnKeyedList                             
                            }                             
                        }

                        set ${_hltSpaceCmdName}\_user_input_args_array(mac_addr) $MacVal
                    } else {
                        set switchCurrentValue [set ${_hltSpaceCmdName}\_user_input_args_array($switchname)]
                        set stepValue [set ${_hltSpaceCmdName}\_user_input_args_array($switchstepval)]
                        if {$switchname == "vlan"} {
                            if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]} {
                                set stepCount [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]
                            } else {
                                set stepCount 1
                            }
                        } else {
                            set stepCount 1                            
                        }
                        set newStepSwitchValueVarName ""
                        ::sth::sthCore::stepSwitchValue $switchCurrentValue $stepValue $stepCount newStepSwitchValueVarName
                        ::sth::sthCore::log debug "Vpls site:$i The new $switchname Value is $newStepSwitchValueVarName."
                        set ${_hltSpaceCmdName}\_user_input_args_array($switchname) $newStepSwitchValueVarName
                    }
                } else {
                    ::sth::sthCore::log warn "$switchname and $switchstepval should be present to use step functionality"
                }
            }
        }
        
        #create the site, host object
        set siteHandle [::sth::Vpls::ProcessCreateL2Host $userInput returnKeyedList cmdState]
        if {!$cmdState} {
            ::sth::sthCore::processError returnKeyedList "Error occur when Excuting Internal Sub command \
                ::sth::Vpls::ProcessCreateL2Host in $_OrigHltCmdName $_hltCmdName $userInput"
            set cmdState $FAILURE
            return $returnKeyedList               
        }
        
        #config PE with VC_lsp
        ::sth::Vpls::ProcessPeConfiguration $userInput returnKeyedList cmdState
        if {!$cmdState} {
            if {[catch {::sth::sthCore::invoke stc::delete $siteHandle} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error deleting previously created vpls site:$siteHandle Msg: $eMsg"
            }
            ::sth::sthCore::processError returnKeyedList "Error occur when Excuting Internal Sub command \
                ::sth::Vpls::ProcessPeConfiguration in $_OrigHltCmdName $_hltCmdName $userInput"
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        
        #create vpn, set up vpn
        ::sth::Vpls::ProcessVPNConfiguration $siteHandle $userInput returnKeyedList cmdState
        if {!$cmdState} {
            if {[catch {::sth::sthCore::invoke stc::delete $siteHandle} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error deleting previously created vpls site:$siteHandle Msg: $eMsg"
            }
            ::sth::sthCore::processError returnKeyedList "Error occur when Excuting Internal Sub command \
                ::sth::Vpls::ProcessVPNConfiguration in $_OrigHltCmdName $_hltCmdName $userInput"
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        
        
        #record pe list
        #set ::sth::Vpls::peHandleList($siteHandle) $peHandle
    }
    
    #return host block, site handle
    if {!$cmdState} {
        if {[catch {::sth::sthCore::invoke stc::delete $siteHandle} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error deleting previously created vpls site:$siteHandle Msg: $eMsg"
        }
        ::sth::sthCore::processError returnKeyedList "Error occur when Excuting Internal Sub command \
            ::sth::Vpls::ProcessVPNConfiguration in $_OrigHltCmdName $_hltCmdName $userInput"
        set cmdState $FAILURE
        return $returnKeyedList         
    } else {
        set cmdState $SUCCESS
        return $returnKeyedList
    }
    
}


###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::ProcessCreateL2Host { str userInput str returnKeyedListVarName bool cmdStatusVarName} {
###\breif Returns  $returnKeyedList : success- key handle in $returnKeyedList, failure- error log in $returnKeyedList
###Returns: success-cmdStatusVarName $::sth::sthCore::SUCCESS, failure-cmdStatusVarName $::sth::sthCore::FAILURE
###
###This procedure is used to create an VPLS site (host) object based on the user input.
###
###\param[in] userInput contains the user input
###\param[in] returnKeyedListVarName contains prioritized list of user input
###\param[in] cmdStatusVarName contains the cmd executing status
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::ProcessCreateL2Host { userInput returnKeyedListVarName cmdStatusVarName }
proc ::sth::Vpls::ProcessCreateL2Host { userInput returnKeyedListVarName cmdStatusVarName } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_vpls_site_config"    
    set _hltCmdName "ProcessCreateL2Host"
    set _hltNameSpace "::sth::Vpls::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    set TRUE 1
    set FALSE 0

    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]} {
        set peHandle [set ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]
        if {[catch {set routerhandle [::sth::sthCore::invoke stc::get $peHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get parent router object of $peHandle, $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList            
        }
        if {[catch {set portHandle [::sth::sthCore::invoke stc::get $routerhandle -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get parent router object of $peHandle, $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList             
        }
    } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]} {
        set portHandle [set ${_hltSpaceCmdName}\_user_input_args_array(port_handle)]
    } else {
            ::sth::sthCore::processError returnKeyedList "Error: do not provided port_handle or pe_handle"
            set cmdState $FAILURE
            return $returnKeyedList          
    }
    
    #If stack for host creation
    set IfStack ""
    set IfCount ""
    
    #vlanIf EthIIIf
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)] && [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)]} {
        set IfStack "VlanIf VlanIf EthIIIf"
        set IfCount "1 1 1"
    } elseif {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)] || [info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)]} {
        set IfStack "VlanIf EthIIIf"
        set IfCount "1 1"
    } else {
        set IfStack "EthIIIf"
        set IfCount "1"
    }

    #create host block object
    set stcCmd {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate \
                                                            -DeviceType Host \
                                                            -ParentList $::sth::GBLHNDMAP(project) \
                                                            -IfStack $IfStack \
                                                            -IfCount $IfCount \
                                                            -Port $portHandle]}

    if {[catch {eval $stcCmd} errMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not create site(host) object \
            -under $::sth::GBLHNDMAP(project), $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set siteHandle $DeviceCreateOutput(-ReturnList)

    #config ethiiIf
    if {[info exist ${_hltSpaceCmdName}\_user_input_args_array(mac_addr)]} {
        set MacAddr [set ${_hltSpaceCmdName}\_user_input_args_array(mac_addr)]
    } else {
        set MacAddr 00:10:94:00:00:01
    }
    
    if {[info exist ${_hltSpaceCmdName}\_user_input_args_array(mac_addr_step)]} {
        set MacAddrStep [set ${_hltSpaceCmdName}\_user_input_args_array(mac_addr_step)]
    } else {
        set MacAddrStep 00:00:00:00:00:01
    }
    
    if {[info exist ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]} {
        set MacCount [set ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]
    } else {
        set MacCount 1
    }
    
    #config EthiiIf
    if {[catch {set EthIIIfHandle [::sth::sthCore::invoke stc::get $siteHandle -children-EthIIIf]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch EthIIIf Handle. Error: $getStatus"
    } else {
	::sth::sthCore::log debug "EthIIIf handle to be configured:$EthIIIfHandle"
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $EthIIIfHandle "-SourceMac $MacAddr -SrcMacStep $MacAddrStep -IsRange $TRUE"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "Unable to config EthIIIf Handle. Error: $configStatus"
        set cmdState $FAILURE
        return $returnKeyedList     
    }
    
    #config vlanIf
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)]} {
        
        set vlanId [set ${_hltSpaceCmdName}\_user_input_args_array(vlan)]
        
        if {[catch {set vlanIfHandle [::sth::sthCore::invoke stc::get $siteHandle -children-VlanIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch vlanIf Handle. Error: $errMsg"
                    set cmdState $FAILURE
                    return $returnKeyedList           
        }
        if {[llength $vlanIfHandle] == 2} {
            set vlanIfHandle [lindex $vlanIfHandle 1]
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_step)]} {
            set vlanIdStep [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_step)]
        } else {
            
            set vlanIdStep 1
        } 
        
        if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]} {
            set  ${_hltSpaceCmdName}\_user_input_args_array(vlan_count) 1
        }
        set vlanCount [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]        
        
        if {[info exist ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]} {
            set vlanRepeatCount [expr [set ${_hltSpaceCmdName}\_user_input_args_array(mac_count)] - 1]
        } else {
            set vlanRepeatCount 0
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $vlanIfHandle "-VlanId $vlanId -IdRepeatCount $vlanRepeatCount -IdStep $vlanIdStep -IsRange $TRUE"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not config VlanIf -under $siteHandle. Msg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList             
        }
        
        #with vlan, host count of host block equals vlan_count * mac_count
        set HostCount [expr $vlanCount * $MacCount]
        if {[catch {::sth::sthCore::invoke stc::config $siteHandle "-DeviceCount $HostCount"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "Unable to config host count in host block $siteHandle. Error: $configStatus"
            set cmdState $FAILURE
            return $returnKeyedList 
        }        
    } else {
        #with no vlan encap, host count of host block equals the mac addr count
        if {[info exist ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]} {
            set HostCount [set ${_hltSpaceCmdName}\_user_input_args_array(mac_count)]
        } else {
            set HostCount 1
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $siteHandle "-DeviceCount $HostCount"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "Unable to config host count in host block $siteHandle. Error: $configStatus"
            set cmdState $FAILURE
            return $returnKeyedList 
        }        
    }
#    if {[catch {set siteHandle [::sth::sthCore::doCreateNew Host -under $::sth::GBLHNDMAP(project) $siteDashedAttribute]} errMsg]} {
#            ::sth::sthCore::processError returnKeyedList "Error: can not create site(host) object \
#                -under $::sth::GBLHNDMAP(project), $errMsg"
#            set cmdState $FAILURE
#            return $returnKeyedList         
#    }

    #config customer vlan
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)]} {
        if {[catch {set vlanIfHandle [::sth::sthCore::invoke stc::get $siteHandle -children-VlanIf]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch vlanIf Handle. Error: $errMsg"
                    set cmdState $FAILURE
                    return $returnKeyedList           
        }

        set vlanIfHandle [lindex $vlanIfHandle 0]
        
        set vlanId [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_id)]
        
        if {[catch {::sth::sthCore::invoke stc::config $vlanIfHandle "-VlanId $vlanId"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not config VlanIf -under $siteHandle. Msg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList             
        }
    }
    
    if {!$cmdState} {
	::sth::sthCore::processError returnKeyedList "Error Occured create vpls site (host): $returnKeyedList"
        #Delete the LDP router Object
	if {[catch {::sth::sthCore::invoke stc::delete $siteHandle} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created vpls site:$siteHandle Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    } else {
        set tmpHandleList {}
        catch {set tmpHandleList [keylget returnKeyedList handle]}
        lappend tmpHandleList $siteHandle
        keylset returnKeyedList handle $tmpHandleList
        set cmdState $::sth::sthCore::SUCCESS
        return $siteHandle
    }
}



###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::ProcessVPNConfiguration { str siteHandle str userInput str returnKeyedListVarName bool cmdStatusVarName} {
###\breif Returns  $returnKeyedList : success- key handle in $returnKeyedList, failure- error log in $returnKeyedList
###Returns: success-cmdStatusVarName $::sth::sthCore::SUCCESS, failure-cmdStatusVarName $::sth::sthCore::FAILURE
###
###This procedure is used to config the VPN setup in VPLS site (host) object based on the user input.
###
######\param[in] siteHandle contains the VPLS site handle to be set up VPN  
###\param[in] userInput contains the user input
###\param[in] returnKeyedListVarName contains prioritized list of user input
###\param[in] cmdStatusVarName contains the cmd executing status
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::ProcessVPNConfiguration { siteHandle userInput returnKeyedListVarName cmdStatusVarName }
proc ::sth::Vpls::ProcessVPNConfiguration { siteHandle userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    variable ::sth::Vpls::VpnHandleList

    set _OrigHltCmdName "emulation_vpls_site_config"    
    set _hltCmdName "ProcessVPNConfiguration"
    set _hltNameSpace "::sth::Vpls::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vc_id)]} {
        set VcId [set ${_hltSpaceCmdName}\_user_input_args_array(vc_id)]
    } else {
        set VcId 1
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vc_id_step)]} {
        set VcIdStep [set ${_hltSpaceCmdName}\_user_input_args_array(vc_id_step)]
    } else {
        set VcIdStep 1
    }
    
    #vc id count equals vlan count, or with no vlan equals 1
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)]} {
        if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]} {
            set  ${_hltSpaceCmdName}\_user_input_args_array(vlan_count) 1
        }
        set VcIdCount [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]            
    } else {
        set VcIdCount 1
    }    
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(site_count)]} {
        set VpnCount [set ${_hltSpaceCmdName}\_user_input_args_array(site_count)]
    } else {
        set VpnCount 1
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vpn_id)]} {
        set VpnId [set ${_hltSpaceCmdName}\_user_input_args_array(vpn_id)]
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vpn_id_step)]} {
        set VpnIdStep [set ${_hltSpaceCmdName}\_user_input_args_array(vpn_id_step)]
    }
    
    #if pe handle exist
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]} {

        set peHandle [set ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]
        
        if {[catch {set peRouterHandle [::sth::sthCore::invoke stc::get $peHandle -Parent]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get parent from $peHandle. Msg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList     
        }
        if {[catch {set PeIpAddr [::sth::sthCore::invoke stc::get $peRouterHandle -RouterId]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get DutIp from $peHandle. Msg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList        
        }
        
        #default value of PE ipaddr prefix length 
        set PeIpAddrPrefixLength 32    
        
        set AttrList "-PeIpv4Addr $PeIpAddr -PeIpv4PrefixLength $PeIpAddrPrefixLength -StartVcId $VcId -VcIdStep $VcIdStep -VcIdCount $VcIdCount"

    } else {
        set AttrList "-StartVcId $VcId -VcIdStep $VcIdStep -VcIdCount $VcIdCount"
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(attached_dut_ip_addr)]} {
            set PeIpAddr [set ${_hltSpaceCmdName}\_user_input_args_array(attached_dut_ip_addr)]
            append AttrList " -PeIpv4Addr $PeIpAddr"
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(attached_dut_ip_prefix)]} {
            set PeIpAddrPrefixLength [set ${_hltSpaceCmdName}\_user_input_args_array(attached_dut_ip_prefix)]
            append AttrList " -PeIpv4PrefixLength $PeIpAddrPrefixLength"
        }   
    }
    
    #create VpnSiteInfoVplsLdp
    set cmd "set VpnSiteInfoHandle [::sth::sthCore::invoke stc::create VpnSiteInfoVplsLdp -under $::sth::GBLHNDMAP(project) $AttrList]"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not create VpnSiteInfoVplsLdp object \
            -under $::sth::GBLHNDMAP(project), $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }

    #create VpnIdGroup
    set vpnSiteHandleList ""
    if {[info exists ${_hltNameSpace}VpnHandleList($VpnId)]} {
        set VpnIdGroupHandle [set ${_hltNameSpace}VpnHandleList($VpnId)]
        #get the vpls sites handle which already bind in VpnIdGroup
        if {[catch {set vpnSiteHandleList [::sth::sthCore::invoke stc::get $VpnIdGroupHandle -MemberOfVpnIdGroup-targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not get VpnSite $VpnSiteInfoHandle from \
                VpnIdGroup $VpnIdGroupHandle, $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList         
        }
    } else {
        set cmd "set VpnIdGroupHandle [::sth::sthCore::invoke stc::create VpnIdGroup -under $::sth::GBLHNDMAP(project)]"
        if {[catch {eval $cmd} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not create VpnIdGroup object \
                -under $::sth::GBLHNDMAP(project), $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList          
        } else {
            set ${_hltNameSpace}VpnHandleList($VpnId) $VpnIdGroupHandle
        }
    }    
    
    #Binding VpnIdGroup VpnSiteInfoVplsLdp
#   set AttrList "-MemberOfVpnIdGroup-targets $VpnSiteInfoHandle"
    #save the old VpnSiteInfo object handle
    lappend vpnSiteHandleList $VpnSiteInfoHandle

    set cmd "::sth::sthCore::invoke stc::config $VpnIdGroupHandle {-MemberOfVpnIdGroup-targets {$vpnSiteHandleList}}"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not set VpnSite $vpnSiteHandleList as \
            member of VpnIdGroup $VpnIdGroupHandle, $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }
    
    #Binding host VpnSiteInfoVplsLdp
    set cmd "::sth::sthCore::invoke stc::config $siteHandle {-MemberOfVpnSite-targets $VpnSiteInfoHandle}"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not set Vpls Site $siteHandle as \
            member of VpnSite $VpnSiteInfoHandle, $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList         
    }    
    #stc::config $Host(4) -MemberOfVpnSite-targets " $VpnSiteInfoVplsLdp(2) "
    
    set cmdState $SUCCESS
    return $returnKeyedList 
    
}

###/* \ingroup VplsFunctions
###\fn proc ::sth::Vpls::ProcessPeConfiguration { str siteHandle str userInput str returnKeyedListVarName bool cmdStatusVarName} {
###\breif Returns  $returnKeyedList : success- key handle in $returnKeyedList, failure- error log in $returnKeyedList
###Returns: success-cmdStatusVarName $::sth::sthCore::SUCCESS, failure-cmdStatusVarName $::sth::sthCore::FAILURE
###
###This procedure is used to config the VPLS PE (router) when configging the vpls site(host) object based on the user input.
### 
###\param[in] userInput contains the user input
###\param[in] returnKeyedListVarName contains prioritized list of user input
###\param[in] cmdStatusVarName contains the cmd executing status
###
###Author: Yulin Chen 
###
###*/
###::sth::Vpls::ProcessPeConfiguration { siteHandle userInput returnKeyedListVarName cmdStatusVarName }
proc ::sth::Vpls::ProcessPeConfiguration { userInput returnKeyedListVarName cmdStatusVarName } {
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_vpls_site_config"    
    set _hltCmdName "ProcessPeConfiguration"
    set _hltNameSpace "::sth::Vpls::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS    
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]} {
        return $SUCCESS         
    }
    
    set peHandle [set ${_hltSpaceCmdName}\_user_input_args_array(pe_handle)]
    
    if {[catch {set routerHandle [::sth::sthCore::invoke stc::get $peHandle -Parent]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: can not get parent router handle of pe_handle $peHandle"
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(site_count)]} {
        set count [set ${_hltSpaceCmdName}\_user_input_args_array(site_count)]
    } else {
        
        set count 1
    }
    
    ##vlanIf -under pe 
    #vc id\vc type\mtu\vlan
    
    #to set up a vc_lsp, need to modify pe ldp hello type to target hello type.
    if {[catch {::sth::sthCore::invoke stc::config $peHandle "-HelloType LDP_TARGETED_HELLO"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: \
            can not config PE $peHandle Hello type to LDP_TARGETED_HELLO. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList             
    }   
    
    #in type target hello, RouterId should be the same with ipaddr
    if {[catch {set Ipv4IfHandle [::sth::sthCore::invoke stc::get $routerHandle -Children-Ipv4If]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: \
            can not get Ipv4If handle of routerhandle $routerHandle :pe_handle $peHandle"
        set cmdState $FAILURE
        return $returnKeyedList        
    }
    
    if {[catch {set Ipv4AddrVal [::sth::sthCore::invoke stc::get $Ipv4IfHandle -Address]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: \
            can not get Ipv4 address of Ipv4If handle $Ipv4IfHandle :pe_handle $peHandle"
        set cmdState $FAILURE
        return $returnKeyedList        
    }

    if {[catch {::sth::sthCore::invoke stc::config $routerHandle "-RouterId $Ipv4AddrVal"} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error: \
            can not config PE $peHandle: routerhandle $routerHandle -RouterId to $Ipv4IfHandle. Msg: $errMsg"
        set cmdState $FAILURE
        return $returnKeyedList             
    }         
    
    #create vc_lsp -under pe
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vc_id)]} {
        set VcId [set ${_hltSpaceCmdName}\_user_input_args_array(vc_id)]
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vc_id_step)]} {
            set VcIdStep [set ${_hltSpaceCmdName}\_user_input_args_array(vc_id_step)]
        } else {
            set VcIdStep 1
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vc_type)]} {
            set VcType [set ${_hltSpaceCmdName}\_user_input_args_array(vc_type)]
            set VcType [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName vc_type $VcType]
        } else {
            #default value
            set VcType "LDP_LSP_ENCAP_ETHERNET_VLAN"
        }
        
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mtu)]} {
            set Mtu [set ${_hltSpaceCmdName}\_user_input_args_array(mtu)]
        } else {
            #default value
            set Mtu 1500
        }
        
        #vc id count equals vlan count, or with no vlan equals 1
        if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan)]} {
            if {![info exists ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]} {
                set  ${_hltSpaceCmdName}\_user_input_args_array(vlan_count) 1
            }
            set VcIdCount [set ${_hltSpaceCmdName}\_user_input_args_array(vlan_count)]            
        } else {
            set VcIdCount 1
        }
        
        if {[catch {::sth::sthCore::invoke stc::create VcLsp -under $peHandle \
		"-StartVcId $VcId -VcIdIncrement $VcIdStep -VcIdCount $VcIdCount -Encap $VcType -IfMtu $Mtu"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error: can not create VcLsp -under $peHandle. Msg: $errMsg"
            set cmdState $FAILURE
            return $returnKeyedList             
        }        
    }
    #config PE router
    
    set cmdState $SUCCESS
    return $returnKeyedList   
}


###/*! \ingroup VplsFunctions
### \fn IsPEHandleValid (str handle, varRef msgName)
###\brief Validates value 
###
###This procedure checks if the value is valid ldpRouterConfig (Pe) Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###*/
###
### IsPEHandleValid (str handle, varRef msgName);
###
proc ::sth::Vpls::IsPEHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable returnKeyedList

    set cmdStatus $::sth::sthCore::FAILURE

    upvar 1 $msgName errorMsg

    if {[catch {set routerHandleList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-Router]} getStatus]} {
	::sth::sthCore::processError returnKeyedList "No router exists under Project Handle:$::sth::GBLHNDMAP(project)"
	return $FAILURE
    } else {
	foreach routerHandle $routerHandleList {
            if {[catch {set ldpRouterConfigHandle [::sth::sthCore::invoke stc::get $routerHandle -children-LdpRouterConfig]} getStatus]} {
                set cmdStatus $::sth::sthCore::FAILURE
            }
            if {[string equal $handle $ldpRouterConfigHandle]} {
                set cmdStatus $::sth::sthCore::SUCCESS
                break
            }
	}
        
	if {$cmdStatus == $::sth::sthCore::SUCCESS} {
            return $SUCCESS
	} else {
	    set errorMsg "Value ($handle) is not a valid PE Ldp router handle"
	    return $FAILURE		
	}		
    }
}

###/*! \ingroup VplsFunctions
### \fn MPLS_Tunnel_Select (str handle, varRef msgName)
###\brief Validates value 
###
###This procedure select the Affiliated MPLS tunnel router for vpls session by
###router ID.
###
###\param[in] handle The value of handle
###\param[in] portHandle the value of port handle
###\param[in] interfaceAddrIP loopback interface ip addr(router ID)
###\param[in] returnKeyedListVarName the value of return key list handle
###\return FAILURE or SUCCESS
###
###*/
###
### MPLS_Tunnel_Select { str portHandle str handle str interfaceAddrIP } 
###
proc ::sth::Vpls::MPLS_Tunnel_Select { portHandle handle returnKeyedListVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_l2vpn_pe_config"    
    set _hltCmdName "MPLS_Tunnel_Select"
    set _hltNameSpace "::sth::Vpls::"
    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    
    if {![::sth::sthCore::IsPortValid $portHandle msg]} {
	::sth::sthCore::log debug "Invalid Value of port_handle"
	set cmdState $FAILURE
	return $FAILURE
    }
    
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(traffic_engineering)]} {
        set mplsRouterConfig RsvpRouterConfig
    } else {
        set mplsRouterConfig LdpRouterConfig
    }
    
    if {[catch {set routerList [sth::sthCore::invoke stc::get $portHandle -AffiliationPort-Sources]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Error occured while getting routers from AffiliationPort. errMsg: $errMsg."
	set cmdState $FAILURE
	return $FAILURE
    }
    
    foreach router $routerList {
        if {[catch {set RouterConfig [sth::sthCore::invoke stc::get $router -Children-$mplsRouterConfig]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while getting routerConfig from $router. errMsg: $errMsg."
            set cmdState $FAILURE
            return $FAILURE
        }
        
        if {$RouterConfig != ""} {
            if {[catch {set ethiiIfHdl [sth::sthCore::invoke stc::get $router -Children-EthIIIf]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-EthIIIf from $router. errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE
            }
            
            if {[catch {set MacAddr [sth::sthCore::invoke stc::get $ethiiIfHdl -SourceMac]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while getting -SourceMac from $ethiiIfHdl. errMsg: $errMsg."
                set cmdState $FAILURE
                return $FAILURE
            }
            
            #if {$LSRID == $interfaceAddrIP} {
                if {[catch {set routerHandle [sth::sthCore::invoke stc::get $handle -Parent]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting parent router from $router. errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE
                }
                
                if {[catch {sth::sthCore::invoke stc::config $routerHandle "-AffiliatedRouter-Targets $router"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while configuring AffiliatedRouter to $handle. errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE
                }
                
                if {[catch {set ethiiIfHdl [sth::sthCore::invoke stc::get $routerHandle -Children-EthIIIf]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while getting -Children-EthIIIf from $routerHandle. errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE
                }
                
                if {[catch {sth::sthCore::invoke stc::config $ethiiIfHdl "-SourceMac $MacAddr"} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while configuring -SourceMac to $ethiiIfHdl. errMsg: $errMsg."
                    set cmdState $FAILURE
                    return $FAILURE
                }
                
                return $SUCCESS
            #}
        }
    }
    
    ::sth::sthCore::processError returnKeyedList "No relevant MPLS tunnel session can be link to. Please check the configuration."
    return $FAILURE
}