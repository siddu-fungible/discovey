# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

###/*! \file DhcpFunctions.tcl
###    \brief Procedure for Dhcp Api
###    
###    This file contains the helper utilities and the special switch processing functions for the Dhcp Api.
###*/
namespace eval ::sth::Dhcp:: {

###/*! \var DHCPHOSTENCAP
### \brief Global Array for encap types and Hosts
###
###This array holds the encap type (e.g. ethernet_ii_vlan) for a particular Host
###
###*/
###array DHCPHOSTENCAP;
        array set DHCPHOSTENCAP {}
 
###/*! \var DHCPHOSTS
### \brief Global Array for Hosts and Dhcpv4PortConfigs
###
###This array holds the Host handles under a particular Dhcpv4PortConfig
###
###*/
###array DHCPHOSTS;       
        array set DHCPHOSTS {}

###/*! \var DHCPHOSTNUMSESS
### \brief Global Array for number of sessions and Dhcpv4PortConfigs
###
###This array holds the number of sessions for a particular Host
###
###*/
###array DHCPHOSTNUMSESS;           
        array set DHCPHOSTNUMSESS {}

###/*! \var DHCPHOSTINNERVLANCOUNT
### \brief Global Array for the number of inner Vlan Ids and Hosts
###
###This array holds the number of inner Vlan Ids for a particular Host
###
###*/
###array DHCPHOSTINNERVLANCOUNT;           
        array set DHCPHOSTINNERVLANCOUNT {}

###/*! \var DHCPHOSTOUTERVLANCOUNT
### \brief Global Array for the number of outer Vlan Ids and Hosts
###
###This array holds the number of outer Vlan Ids for a particular Host
###
###*/
###array DHCPHOSTOUTERVLANCOUNT;          
        array set DHCPHOSTOUTERVLANCOUNT {}

###/*! \var DHCPHOSTINNERVLANID
### \brief Global Array for the starting inner Vlan Ids and Hosts
###
###This array holds the starting inner Vlan Id for a particular Host
###
###*/
###array DHCPHOSTINNERVLANID;          
        array set DHCPHOSTINNERVLANID {}

###/*! \var DHCPHOSTOUTERVLANID
### \brief Global Array for the starting outer Vlan Ids and Hosts
###
###This array holds the starting outer Vlan Id for a particular Host
###
###*/
###array DHCPHOSTOUTERVLANID;          
        array set DHCPHOSTOUTERVLANID {}

###/*! \var DHCPHOSTINNERVLANSTEP
### \brief Global Array for the inner Vlan Id steps and Hosts
###
###This array holds the inner Vlan Id step for a particular Host
###
###*/
###array DHCPHOSTINNERVLANSTEP;          
        array set DHCPHOSTINNERVLANSTEP {}

###/*! \var DHCPHOSTOUTERVLANSTEP
### \brief Global Array for the outer Vlan Id steps and Hosts
###
###This array holds the outer Vlan Id step for a particular Host
###
###*/
###array DHCPHOSTOUTERVLANSTEP;         
        array set DHCPHOSTOUTERVLANSTEP {}
        
        # array to store vlan priority
        array set DHCPHOSTINNERVLANPRI {}
        array set DHCPHOSTOUTERVLANPRI {}

###/*! \var DHCPHOSTQINQINCRMODE
### \brief Global Array for the Qinq increment modes and Hosts
###
###This array holds the Qinq increment mode for a particular Host
###
###*/
###array DHCPHOSTQINQINCRMODE;         
        array set DHCPHOSTQINQINCRMODE {}

###/*! \var DHCPHOSTINNERVLANIF
### \brief Global Array for the inner Vlan interaces and Hosts
###
###This array holds the inner Vlan interface handle for a particular Host
###
###*/
###array DHCPHOSTINNERVLANIF;         
        array set DHCPHOSTINNERVLANIF {}

###/*! \var DHCPHOSTOUTERVLANIF
### \brief Global Array for the outer Vlan interaces and Hosts
###
###This array holds the outer Vlan interface handle for a particular Host
###
###*/
###array DHCPHOSTOUTERVLANIF;           
        array set DHCPHOSTOUTERVLANIF {}

###/*! \var DHCPHOSTQINQSUBHOSTS
### \brief Global Array for the Qinq subHost handles and Hosts
###
###This array holds the Host handles for a particular Host with encap ethernet_ii_qinq
###
###*/
###array DHCPHOSTQINQSUBHOSTS;           
        array set DHCPHOSTQINQSUBHOSTS {}
        
        
        #DHCP 3.00 enhancement xiaozhi
        set dhcpBlockInputArgsList ""
        array set dhcpBlockInputArgs {}
        array set processFlag {}
        set relay_agent_flag 0
        #qinqOneblock is a flag indicating whether or not a single DHCPv4 host handle will be returned in QinQ mode
        array set qinqOneblock {}
        # This array holds the protocol type for a particular host
        array set DHCPHOSTPROTOCOL {}
        set session_index 0
        
        ###array DHCPHOSTOUTERVLANREPEATCOUNT;          
        array set DHCPHOSTOUTERVLANREPEATCOUNT {}
        ###array DHCPHOSTINNERVLANREPEATCOUNT;          
        array set DHCPHOSTINNERVLANREPEATCOUNT {}

}

###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_config_create (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em create for emulation_dhcp_config cmd
###
###This procedure execute the emulation_dhcp_config command when the mode is create. It will create and config a Dhcpv4portconfig.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with dhcp handles
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_config_create (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName;
###

proc ::sth::Dhcp::emulation_dhcp_config_create { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_config"
    set _hltCmdName "emulation_dhcp_config_create"
    variable dhcpBlockInputArgs

	#::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    set validateStep 1
    set stepError 0
    
    #Get port handle from port_handle or handle
    if {[info exists userInputArgs(port_handle)]} {
        set hltPort $userInputArgs(port_handle)
    } elseif {$userInputArgs(mode) == "create" && [info exists userInputArgs(handle)]} {
        #Get Dhcpv4portconfig handle from handle switch
        set handleVar [::sth::Dhcp::getDHCPHandle handle port userInputArgs returnKeyedList cmdState]
        if {!$cmdState} {
            return $returnKeyedList
        }
        
        #Get port handle from Dhcpv4portconfig handle
        if {![::sth::Dhcp::getPort $handleVar hltPort]} {
            ::sth::sthCore::processError returnKeyedList "The value $handleVar is not valid for the switch -handle"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList             
        }
    } elseif {$userInputArgs(mode) == "enable" && [info exists userInputArgs(handle)]} {
        #Get Dhcpv4portconfig handle from handle switch
        set handle $userInputArgs(handle)
        set hltPort [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
        
    } else {
        ::sth::sthCore::processError returnKeyedList "The switch -port_handle is a mandatory switch"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList  
    }
    
    #Validate the port_handle
    set msg ""
    if {![::sth::sthCore::IsPortValid $hltPort msg]} {
        if {[string equal $hltPort SHA_NO_USER_INPUT] == 1} {
            set hltPort "{{}}"
        }
        ::sth::sthCore::processError returnKeyedList "The value $hltPort is not valid for the switch -port_handle"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList        
    }
    
    #Execute the createConfigDhcpPort cmd and check result.
    set cmdFailed 1
    if {[catch {::sth::Dhcp::createConfigDhcpPort userInputArgs sortedPriorityList returnKeyedList cmdFailed} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp port: $eMsg"
        set cmdFailed 1
    }
    
    if {$cmdFailed} {
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList 
    } else {
        #::sth::sthCore::log debug "Successfully created/configured Dhcpv4portconfig $returnKeyedList"
    }
    
    if {[::info exists cmdError]} {
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList
    } else {    
        set cmdState $::sth::sthCore::SUCCESS
    	return $returnKeyedList
    }

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_config_modify (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em modify for emulation_dhcp_config cmd
###
###This procedure executes the emulation_dhcp_config command when the mode is modify. It will modify the specified Dhcpv4portconfig based on switch values.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_config_modify (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_config_modify { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_config"
    set _hltCmdName "emulation_dhcp_config_modify"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
   
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    #Validate if handle is valid
    set dhcpHandle [::sth::Dhcp::getDHCPHandle handle port userInputArgs returnKeyedList cmdState]
    if {!$cmdState} {
        return $returnKeyedList
    }
    
    #Configure the created Dhcpv4portconfig with user input (options)
    #::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName userInputArgs sortedPriorityList \
                   $dhcpHandle returnKeyedList]
    
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList 
    } 
    
    set cmdResult [::sth::Dhcp::modifyDhcpBlockConfigArgs ::sth::Dhcp:: $_OrigHltCmdName userInputArgs sortedPriorityList \
                   $dhcpHandle returnKeyedList]
    
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList 
    } 
    
    #apply  all configurations
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
            return $returnKeyedList
        }
    }

    keylset returnKeyedList handle.[::sth::sthCore::invoke stc::get $dhcpHandle -parent] $dhcpHandle
    keylset returnKeyedList handles $dhcpHandle
 
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_config_reset (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em reset for emulation_dhcp_config cmd
###
###This procedure execute the emulation_dhcp_config command when the mode is reset. It will perform abort and delete on the Dhcpv4portconfig.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_config_reset (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_config_reset { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_config"
    set _hltCmdName "emulation_dhcp_config_reset"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    #Validate if handle is valid
    set dhcpHandle [::sth::Dhcp::getDHCPHandle handle port userInputArgs returnKeyedList cmdState]
    if {!$cmdState} {
        return $returnKeyedList
    }
    
    if {[info exists ::sth::Dhcp::DHCPHOSTS($dhcpHandle)]} {
        #Call abort on Dhcp hosts
        if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4Abort -BlockList $::sth::Dhcp::DHCPHOSTS($dhcpHandle)} eMsg]} {
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp port: $eMsg"        
        }

        #Call delete on all Dhcp hosts
        foreach hostHandle $::sth::Dhcp::DHCPHOSTS($dhcpHandle) {
            #Call abort/delete on additional QinQ hosts
            if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]} { 
                catch {unset ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)}
            
            #Otherwise just delete the single host
            }
            
            if {![::sth::Dhcp::deleteDhcpHost $hostHandle returnKeyedList]} {
                set cmdError 1
                ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp port"        
            }    
        }

        catch {unset ::sth::Dhcp::DHCPHOSTS($dhcpHandle)}
    }
    
    
    #apply  all configurations
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
            return $returnKeyedList
        }
    }

    if {[::info exists cmdError]} {
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList
    } else {    
        set cmdState $::sth::sthCore::SUCCESS
    	return $returnKeyedList
    }

}

###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_group_config_create (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em create for emulation_dhcp_group_config cmd
###
###This procedure execute the emulation_dhcp_group_config command when the mode is create. It will create sessions based on the \em -num_sessions switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with bgp handles
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_create (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_create { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_group_config"
    set _hltCmdName "emulation_dhcp_group_config_create"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    #set args $userInput
    set validateStep 1
    set stepError 0
    set maxNumOfGroups 10
    
    if {$userInputArgs(mode) == "create"} {
        #Validate if the DhcpPort handle is valid
        set dhcpHandle [::sth::Dhcp::getDHCPHandle handle port userInputArgs returnKeyedList cmdState]
        if {!$cmdState} {
            return $returnKeyedList
        }
    
        #Check encap switch
        if {![info exists userInputArgs(encap)]} {
            ::sth::sthCore::processError returnKeyedList "The switch -encap is a mandatory switch"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
    }
    
    #TODO: find P2 MAX
    #Check if max number of groups has been reached and if so quit
    #set numOfGroups [llength $::sth::Dhcp::DHCPSESSIONS($dhcpHandle)]
    #if {$numOfGroups >= $maxNumOfGroups} {
    #    keylset returnKeyedList log "Cannot create group: maximum number ($maxNumOfGroups) of groups exceeded" 
    #    set cmdState $::sth::sthCore::FAILURE
    #    return $returnKeyedList 
    #}

    #Execute the createConfigDhcpSessionBlock cmd and check result.
    set cmdFailed 1
    if {[catch {::sth::Dhcp::createConfigDhcpSessionBlock userInputArgs sortedPriorityList returnKeyedList cmdFailed} eMsg]} {
        set cmdFailed 1
    }
    
    if {$cmdFailed} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList 
    } else {
        #::sth::sthCore::log debug "Successfully created/configured DhcpSessionBlock $returnKeyedList"
    }
    
    if {[::info exists cmdError]} {
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList
    } else {
        set cmdState $::sth::sthCore::SUCCESS
    	return $returnKeyedList
    }

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_group_config_modify (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em modify for emulation_dhcp_group_config cmd
###
###This procedure executes the emulation_dhcp_group_config command when the mode is modify. It will modify the DhcpSessionBlock based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_modify (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_modify { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_group_config"
    set _hltCmdName "emulation_dhcp_group_config_modify"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"

    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    #Get DhcpSessionBlock handle
    set dhcpHandle [::sth::Dhcp::getDHCPHandle handle group userInputArgs returnKeyedList cmdState]
    if {!$cmdState} {
        return $returnKeyedList
    }
    
    if {![::sth::Dhcp::getDhcpPort $dhcpHandle dhcpPort]} {
        ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
        return $::sth::sthCore::FAILURE           
    }
    #Get port handle from DhcpPort handle
    if {![::sth::Dhcp::getPort $dhcpPort hltPort]} {
        ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
        return $::sth::sthCore::FAILURE           
    }
    
    
    #Get host handle from Dhcpv4BlockConfig handle
    if {![::sth::Dhcp::getHostHandle $dhcpHandle hostHandle]} {
        ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList             
    }
    
    array set hostAttrs "
        _outervlan          ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)
        _innervlan          ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)
        _hostnum            ::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle)
    "
    ::sth::Session::getHostAttrToArray $hostHandle hostAttrs
    
    #Modify Host object
    #If the object created using "enable" mode, the "encap" needs to be added in modify mode.
    if {[info exists userInputArgs(encap)]} {
        set encap $userInputArgs(encap)
    } elseif {[info exists ::sth::Dhcp::DHCPHOSTENCAP($hostHandle)]} {
        set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)
    } else {
        ::sth::sthCore::processError returnKeyedList "The switch -encap is necessary if the dhcp object is created in enable mode"
        return $::sth::sthCore::FAILURE
    }
    
    if {[info exists userInputArgs(protocol)]} {
        set protocol $userInputArgs(protocol)
    } else {
        set protocol $::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle)
    }
    if {[catch {set status [::sth::Dhcp::emulation_dhcp_group_config_encap $encap $protocol "" \
                            hostHandle returnKeyedList errOccured dhcpHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnKeyedList "Internal error creating Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #Configure the created DhcpSessionBlock with user input (options)
    #::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName userInputArgs sortedPriorityList \
                   $dhcpHandle returnKeyedList]
      
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList 
    }

    #Create additional hosts for ethernet_ii_qinq    
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        #
        if {[info exists ::sth::Dhcp::qinqOneblock($hostHandle)]} {
            if {$::sth::Dhcp::qinqOneblock($hostHandle) == 0} {
                set userInputArgs(qinq_oneblock) 0
            } else {
                set userInputArgs(qinq_oneblock) 1
            }
        }
        set cmdResult [::sth::Dhcp::createQinQHosts $hostHandle $hltPort userInputArgs sortedPriorityList returnKeyedList]
        if {$cmdResult == $::sth::sthCore::FAILURE} {
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }
    }
    
    #Configure host and vlan interfaces
    set cmdResult [::sth::Dhcp::configVlan $dhcpHandle "" returnKeyedList]
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdState $::sth::sthCore::FAILURE
        set cmdFailed 1
    }

    #apply  all configurations
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
            return $returnKeyedList
        }
    }
   
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList

}

###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_group_config_reset (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em reset for emulation_dhcp_group_config cmd
###
###This procedure execute the emulation_dhcp_group_config command when the mode is reset. It will perform abort on the DhcpSessionBlock.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_reset (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_reset { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {

    set _OrigHltCmdName "emulation_dhcp_group_config"
    set _hltCmdName "emulation_dhcp_group_config_reset"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    #Get the DhcpSessionBlock handle
    set dhcpHandle [::sth::Dhcp::getDHCPHandle handle group userInputArgs returnKeyedList cmdState]
    if {!$cmdState} {
        return $returnKeyedList
    }

    #Get host handle from Dhcpv4BlockConfig handle
    if {![::sth::Dhcp::getHostHandle $dhcpHandle hostHandle]} {
        ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList             
    }

    if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]} {
        #Abort host
        if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4Abort -BlockList $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)} eMsg]} {
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp group $dhcpHandle: $eMsg"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }

        foreach subhostHandle $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) {
            #Delete host
            if {![::sth::Dhcp::deleteDhcpHost $subhostHandle returnKeyedList]} {
                set cmdError 1
                ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp group:$dhcpHandle"
                set cmdState $::sth::sthCore::FAILURE
                return $returnKeyedList 
            }


            #Remove dhcpHandle from DHCPHOSTS($dhcpPort)
            if {[catch {::sth::Dhcp::deleteHandleInHandleList $subhostHandle ::sth::Dhcp::DHCPHOSTS eMsg} eMsg ]} {	   
                set cmdError 1
                ::sth::sthCore::processError returnKeyedList "Error occured while deleting Dhcp group $dhcpHandle: $eMsg"
                set cmdState $::sth::sthCore::FAILURE
                return $returnKeyedList 
            }
        }
        
        catch {unset ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)}
        
    } else {
        #Abort host
        if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4Abort -BlockList $hostHandle} eMsg]} {
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp group:$dhcpHandle"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }
    
        #Delete host
        if {![::sth::Dhcp::deleteDhcpHost $hostHandle returnKeyedList]} {
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp group:$dhcpHandle"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }

        
        #Remove dhcpHandle from DHCPHOSTS($dhcpPort)
        if {[catch {::sth::Dhcp::deleteHandleInHandleList $hostHandle ::sth::Dhcp::DHCPHOSTS eMsg} eMsg ]} {	   
            set cmdError 1
            ::sth::sthCore::processError returnKeyedList "Error occured while deleting Dhcp group $dhcpHandle: $eMsg"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }
    }
    
    #apply  all configurations
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
            return $returnKeyedList
        }
    }

    if {[::info exists cmdError]} {
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList
    } else {    
        set cmdState $::sth::sthCore::SUCCESS
    	return $returnKeyedList
    }

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_control_action (str action, arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em action for emulation_dhcp_control cmd
###
###It will perform the specified action: either bind, release, or renew.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_control_reset (str action, arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###
proc ::sth::Dhcp::emulation_dhcp_control_action { action switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName } {
    
    set _OrigHltCmdName "emulation_dhcp_control"
    set _hltCmdName "emulation_dhcp_control_$action"

    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState
    
    switch -- $action {
        bind {
            set perform "Dhcpv4Bind"
        }
        release {
            set perform "Dhcpv4Release"
        }
        renew {
            set perform "Dhcpv4Renew"
        }
        rebind {
            set perform "Dhcpv4Rebind"
        }
        abort {
            set perform "Dhcpv4Abort"
        }
        default {
            ::sth::sthCore::processError returnKeyedList "The value $action is not valid for the switch -action"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
    }

    #Get Dhcpv4portconfig or Dhcpv4BlockConfig handle
    if {!([info exist userInputArgs(port_handle)] || [info exist userInputArgs(handle)])} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList          
    } else {
        if {[info exist userInputArgs(port_handle)]} {
				#Validate the DhcpPort handle
				if {[info exist userInputArgs(handle)]} {
					set userInputArgs(handle) ""
				}
				set portList $userInputArgs(port_handle)
				foreach userInputArgs(port_handle) $portList {
					if {[regexp -nocase "dhcp" $userInputArgs(port_handle)]} {
						set dhcpHandle [::sth::Dhcp::getDHCPHandle port_handle port userInputArgs returnKeyedList cmdState]
						if {!$cmdState} {
							return $returnKeyedList
						}
						#Check if there are any Dhcpv4BlockConfigs associated with Dhcpv4portconfig. If not, don't continue.
						append portHandleList " $::sth::Dhcp::DHCPHOSTS($dhcpHandle)"
						if {[llength $portHandleList] < 1} {
							::sth::sthCore::processError returnKeyedList "Must configure at least one group first" 
							set cmdState $::sth::sthCore::FAILURE
							return $returnKeyedList 
						}
					} else {
						set hostlist [::sth::sthCore::invoke stc::get $userInputArgs(port_handle) -affiliationport-sources]
						foreach host $hostlist {
							set dhcpHandle [stc::get $host -children-Dhcpv4BlockConfig]
							if {$dhcpHandle ne ""} {
								lappend userInputArgs(handle) $dhcpHandle
							}
						}
						if {0 == [llength $userInputArgs(handle)]} {
							::sth::sthCore::processError returnKeyedList "invalid port_handle input"
							set cmdState $::sth::sthCore::FAILURE
							return $returnKeyedList
						}
					}
		    }
			set userInputArgs(port_handle) $portList
        }
        
       if {[set handleExist [info exist userInputArgs(handle)]]} {       
            #Validate the Dhcpv4BlockConfig handle
            set dhcpHandles [::sth::Dhcp::getDHCPHandle handle mix userInputArgs returnKeyedList cmdState]
            if {!$cmdState} {
                return $returnKeyedList
            }
            
            set hostList ""
            
            foreach dhcpHandle $dhcpHandles {
                #Get host handle from Dhcpv4BlockConfig handle
                if {![::sth::Dhcp::getHostHandle $dhcpHandle hostHandle]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList             
                }
                
                #Check if there are other hosts tied to hostHandle for QinQ
                if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]} {
                    set hostList [concat $hostList $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]
                } else {
                    set hostList [concat $hostList $hostHandle]
                }
            }
        }
    }

    #apply  all configurations
    if {!$::sth::sthCore::optimization} {
        if {[catch {::sth::sthCore::doStcApply} err]} {
            ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
            return $returnKeyedList
        }
    }

    if ($handleExist) {
        #Perform action on Dhcpv4BlockConfig's host
        if {[catch {::sth::sthCore::invoke stc::perform $perform -BlockList $hostList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while performing $action on Dhcp group $dhcpHandle: $eMsg"        
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }
    } else {
        #Perform action on Dhcpv4portconfig's hosts
        if {[catch {::sth::sthCore::invoke stc::perform $perform -BlockList $portHandleList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while performing $action on Dhcp port $dhcpHandle: $eMsg"       
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList 
        }
    }
	
    set cmdState $::sth::sthCore::SUCCESS  
    return $returnKeyedList

}

# For debug use: saves .csv of sessions info
proc ::sth::Dhcp::session_info { handle filename } {
    
    #Get host handle from Dhcpv4BlockConfig handle
    if {![::sth::Dhcp::getHostHandle $handle hostHandle]} {
        return $::sth::sthCore::FAILURE            
    }
            
    #Check if there are other hosts tied to hostHandle for QinQ
    if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]} {
        set hostList $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)
    } else {
        set hostList $hostHandle
    }

    #Perform action on Dhcpv4BlockConfig's host
    if {[catch {::sth::sthCore::invoke stc::perform Dhcpv4SessionInfo -BlockList $hostList -filename $filename} eMsg]} {
        return $::sth::sthCore::FAILURE
    }

    return $::sth::sthCore::SUCCESS  

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_stats_collect (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process emulation_dhcp_stats cmd with no \em -mode switch
###
###This procedure execute the emulation_dhcp_stats command with default mode. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_stats_collect (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_stats_collect { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName modeVal } {
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState

    set _OrigHltCmdName "emulation_dhcp_stats"
    set _hltCmdName "emulation_dhcp_stats"
    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"

    if {[info exist userInputArgs(mode)]} {
        set modeVal $userInputArgs(mode)
    } else {
        set modeVal session
    }
    
    #Get Dhcpv4portconfig or Dhcpv4BlockConfig handle
    if {!([info exist userInputArgs(port_handle)] || [info exist userInputArgs(handle)])} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList          
    } else {
        if {[set portHandleExist [info exist userInputArgs(port_handle)]]} {
            #Validate the Dhcpv4portconfig handle
            if {[regexp -nocase "dhcp" $userInputArgs(port_handle)]} {
                set dhcpHandle [::sth::Dhcp::getDHCPHandle port_handle port userInputArgs returnKeyedList cmdState]
                if {!$cmdState} {
                    return $returnKeyedList
                }
                
                #Add Dhcpv4portresults handle to list of handles to pull stats from
                if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpHandle -children-dhcpv4portresults]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -port_handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
                lappend handleList [list $dhcpResultsHandle aggregate]
                
                #Add all associated Dhcpv4BlockConfig handles to list
                foreach hostHandle $::sth::Dhcp::DHCPHOSTS($dhcpHandle) {
                    #Check if Dhcpv4BlockConfig exists
                    if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $hostHandle -children-Dhcpv4BlockConfig]} getStatus]} {
                        continue
                    }
                    #Check if Dhcpv4BlockResults exists
                    if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -children-Dhcpv4BlockResults]} getStatus]} {
                        continue
                    }
                    #Add Dhcpv4BlockResults to list
                    lappend handleList [list $dhcpResultsHandle group]
                    
                    if {[string equal $modeVal "detailed_session"]} {
                        set ::sth::Dhcp::session_index 0
                        ::sth::sthCore::invoke stc::perform Dhcpv4ShowSessionInfoCommand -blocklist $dhcpBlkHandle
                        set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -children-Dhcpv4SessionResults]
                        
                        foreach handle $dhcpResultsHandle {
                            lappend handleList [list $handle detailed_session]
                        }
                    }
                }
            } else { 
                set hostlist [::sth::sthCore::invoke stc::get $userInputArgs(port_handle) -affiliationport-sources]
                foreach host $hostlist {
                    set dhcpHandle [stc::get $host -children-Dhcpv4BlockConfig]
                    if {$dhcpHandle ne ""} {
                        set userInputArgs(handle) $dhcpHandle
                        break
                    }
                }
                if {$dhcpHandle eq ""} {
                    ::sth::sthCore::processError returnKeyedList "invalid port_handle input"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList
                }
                # for cases such as load_xml()
                set portConfig [::sth::sthCore::invoke stc::get $userInputArgs(port_handle) -children-dhcpv4portconfig]                
                if { ![info exists ::sth::Dhcp::DHCPHOSTS($portConfig)]} {
                    set ::sth::Dhcp::DHCPHOSTS($portConfig) $hostlist
                }
            }
       }
       if {[info exist userInputArgs(handle)]} {
            #Validate the Dhcpv4BlockConfig handle
            set dhcpHandle [::sth::Dhcp::getDHCPHandle handle group userInputArgs returnKeyedList cmdState]
            if {!$cmdState} {
                return $returnKeyedList
            }
            
            if {[string equal $modeVal "aggregate"]} {
                #Get Dhcpv4BlockConfig's associated Dhcpv4portconfig handle
                if {![::sth::Dhcp::getDhcpPort $dhcpHandle dhcpPort]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    return $::sth::sthCore::FAILURE           
                }
                #Get Dhcpv4portconfig's results handle
                if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpPort -children-dhcpv4portresults]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
                set handleList [list [list $dhcpResultsHandle aggregate]]
            } elseif {[string equal $modeVal "detailed_session"]} {
                
                #Add Dhcpv4BlockResults handle to list of handles to pull stats from
                if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpHandle -children-Dhcpv4BlockResults]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
                set handleList [list [list $dhcpResultsHandle group]]
                
                #Add Dhcpv4SessionResults handle to list of handles to pull stats from                
                set ::sth::Dhcp::session_index 0
                ::sth::sthCore::invoke stc::perform Dhcpv4ShowSessionInfoCommand -blocklist $dhcpHandle
                if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpHandle -children-Dhcpv4SessionResults]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
                
                foreach handle $dhcpResultsHandle {
                    lappend handleList [list $handle detailed_session]
                }
            } else {
                #Add Dhcpv4BlockResults handle to list of handles to pull stats from
                if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpHandle -children-Dhcpv4BlockResults]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
                set handleList [list [list $dhcpResultsHandle group]]
            }
        }
    }
    
    foreach handle $handleList {
        set dhcpHandle [lindex $handle 0]
        set handleType [lindex $handle 1]
        
        if {[regexp -nocase "dhcpv4sessionresults" $dhcpHandle]} {
            incr ::sth::Dhcp::session_index
        } 
        if {[catch {set returnKeys [array names ::sth::Dhcp::emulation_dhcp_stats_procfunc]} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error occured while determining stats key list"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList
        }
    
        #Get stats
        foreach keyName $returnKeys {
            set objType [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $keyName stcobj]
            #Don't process aggregate stat if handle is for a blk
            if {($objType == "Dhcpv4PortResults" && $handleType == "group") || ($objType == "Dhcpv4PortResults" && $handleType == "detailed_session")} {
                continue
            }
            #Don't process group stat if handle is for a port
            if {($objType == "Dhcpv4BlockResults" && $handleType == "aggregate") || ($objType == "Dhcpv4BlockResults" && $handleType == "detailed_session")} {
                continue
            }
            #Don't process group stat if handle is for a port
            if {($objType == "Dhcpv4SessionResults" && $handleType == "aggregate") || ($objType == "Dhcpv4SessionResults" && $handleType == "group")} {
                continue
            }
            
            # Fetch the processing function and generate the cmd
            set keyProcFunc [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $keyName procfunc]
            #"Procfunc for $keyName is $keyProcFunc"
            if {$keyProcFunc == "_none_"} {
                continue
            }
                
            set cmd "::sth::Dhcp::$keyProcFunc returnKeyedList $_hltCmdName $keyName $dhcpHandle"
            set cmdResult [eval $cmd]
            if {$cmdResult == $::sth::sthCore::FAILURE} {
                set cmdFailed 1
                ::sth::sthCore::processError returnKeyedList "$_hltCmdName: Error occured while fetching key:$keyName"
                break
            }
        }
    }

    if {[::info exists cmdFailed]} {
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList
    } else {
        set cmdState $::sth::sthCore::SUCCESS
    	return $returnKeyedList
    }

}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_stats_clear (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName)
###\brief Process \em -mode switch with value \em clear for emulation_dhcp_stats cmd
###
###This procedure execute the emulation_dhcp_stats command when the mode is clear. 
###
###\param[in] args This is the list of user configuration input.
###\return KeyedList with keyed based on mode switch value
###
###
###\author Mark Menor
###*/
###
###emulation_dhcp_stats_clear (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnKeyedListVarName, varRef cmdStatusVarName);
###

proc ::sth::Dhcp::emulation_dhcp_stats_clear { switchArgs mySortedPriorityList returnKeyedListVarName cmdStatusVarName modeVal } {

    set _OrigHltCmdName "emulation_dhcp_stats"
    set _hltCmdName "emulation_dhcp_stats_clear"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnKeyedListVarName returnKeyedList
    upvar $cmdStatusVarName cmdState
    
    #::sth::sthCore::log debug "Executing Internal Sub command for: $_OrigHltCmdName {$_hltCmdName $args}"
    
    set grpName $modeVal
    
    #Get Dhcpv4portconfig or Dhcpv4BlockConfig handle
    if {!([info exist userInputArgs(port_handle)] || [info exist userInputArgs(handle)])} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
        set cmdState $::sth::sthCore::FAILURE
    	return $returnKeyedList          
    }
    
    if {[info exist userInputArgs(port_handle)]} {
        #Validate the Dhcpv4portconfig handle
        set dhcpHandle [::sth::Dhcp::getDHCPHandle port_handle port userInputArgs returnKeyedList cmdState]
        if {!$cmdState} {
            return $returnKeyedList
        }
    }
    
    if {[info exist userInputArgs(handle)]} {
        #Validate the Dhcpv4BlockConfig handle
        set dhcpHandle [::sth::Dhcp::getDHCPHandle handle group userInputArgs returnKeyedList cmdState]
        if {!$cmdState} {
            return $returnKeyedList
        }
    }
    
    # Clear ALL stats
    if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAllProtocol} eMsg]} {
        set cmdState $::sth::sthCore::FAILURE
        ::sth::sthCore::processError returnKeyedList "Internal error occured: $eMsg"
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
    
    #Get Dhcpv4portconfig or Dhcpv4BlockConfig handle
    #if {!([info exist userInputArgs(port_handle)] || [info exist userInputArgs(handle)])} {
    #    ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch"
    #    set cmdState $::sth::sthCore::FAILURE
    # 	 return $returnKeyedList          
    #} else {
    #    if {[set portHandleExist [info exist userInputArgs(port_handle)]]} {
    #        #Validate the Dhcpv4portconfig handle
    #        set dhcpHandle [::sth::Dhcp::getDHCPHandle port_handle port userInputArgs returnKeyedList cmdState]
    #        if {!$cmdState} {
    #            return $returnKeyedList
    #        }
            
    #        #List of DhcpPort attributes to clear
    #        set grpName DhcpPort
    #        set cntList { avgSetupTime \
    #                    attemptRate \
    #                    bindRate \
    #                    currBound \
    #                    currIdle \
    #                    maxSetupTime \
    #                    minSetupTime \
    #                    outAttempt \
    #                    outBound \
    #                    outFail \
    #                    outRetryTotal \
    #                    rxAck \
    #                    rxNak \
    #                    rxOffer \
    #                    successPct \
    #                    txDiscover \
    #                    txRelease \
    #                    txReq \
    #        }
    #    }

    #   if {[info exist userInputArgs(handle)]} {
    #        #Validate the DhcpSessionBlock handle
    #        set dhcpHandle [::sth::Dhcp::getDHCPHandle handle group userInputArgs returnKeyedList cmdState]
    #        if {!$cmdState} {
    #            return $returnKeyedList
    #        }
            
    #        #List of DhcpSessionBlock attributes to clear
    #        set grpName DhcpSessionBlock
    #        set cntList { attemptRate \
    #                    bindRate \
    #                    currAttempt \
    #                    currBound \
    #                    currIdle \
    #                    elapsed \
    #                    outAttempt \
    #                    outBound \
    #                    outFail \
    #                    outRetryTotal \
    #                    rxAck \
    #                    rxNak \
    #                    rxOffer \
    #                    txDiscover \
    #                    txRelease \
    #                    txReq \
    #        }
    #    }
    #}
    
    #Clear stats for object -- Currently does not work --
    #if {[catch {::sth::sthCore::invoke stc::clear $dhcpHandle $cntList} clearStatus ]} {
    #    eval "$::sth::_SHA_DEBUG(error) {Unable to Clear Stats. Error: $clearStatus}"
    #    keylset returnKeyedList log "Internal Command Error while clearing Stats"
    #    set cmdState 0
    #    set cmdFailed 1
    #} else {
    #    eval "$::sth::_SHA_DEBUG(level1) {Successfully Cleared Stats.}"
    #}
    
    #Temporary clear proc: Clear ALL Dhcp stats under project
    #Set clearAllStats to FALSE
    #if {[catch {::sth::sthCore::invoke stc::config $::sth::GBLHNDMAP(project) "-clearAllStats FALSE"} configStats ] } {
    #    ::sth::sthCore::processError returnKeyedList "Internal Command Error while clearing Stats"
    #    set cmdState 0
    #    set cmdFailed 1
    #} else {
    #    #::sth::sthCore::log debug "Successfully set Project clearAllStats to FALSE."
    #}
    
    #Clear all Dhcp stats under project
    #if {[catch {::sth::sthCore::invoke stc::clear $::sth::GBLHNDMAP(project) clearDhcpStats} configStats ] } {
    #    ::sth::sthCore::processError returnKeyedList "Internal Command Error while clearing Stats"
    #    set cmdState 0
    #    set cmdFailed 1
    #} else {
    #    #::sth::sthCore::log debug "Successfully peformed Clear_Stats on Project."
    #}


    #if {[::info exists cmdFailed]} {
    #    set cmdState 0
    #	return $returnKeyedList
    #} else {
    #    set cmdState 1
    #	return $returnKeyedList
    #}

}


###/*! \ingroup dhcphelperfuncs
###\fn macToBinary ( string mac )
###\brief Convert mac address to binary number
###
###This procedure returns a string of the binary form of the mac address
###
###\param[in] mac The mac address to be converted
###\return String of the binary form of the mac address
###
###
###\author Mark Menor
###*/
###
###macToBinary ( string mac )
###

proc ::sth::Dhcp::macToBinary { mac } {
	set octets [split $mac .]
	set len [llength $octets]
	if {$len != 6} {
		#"invalid address: this is not an MAC address"
		return 0
	}
	set result ""
	for {set n 0} {$n < $len} {incr n} {
		set octet [lindex $octets $n]
		set octet [binary format H2 $octet]
		append result $octet
	}
	
    #convert to binary character string
    binary scan $result B48 binMac
    return $binMac
}


###/*! \ingroup dhcphelperfuncs
###\fn addMacAddr ( string macAddr1, string macAddr2 )
###\brief Return the sum of two mac addresses
###
###This procedure returns a string of sum of two mac address. NOTE: assumes no overflow
###
###\param[in] macAddr1 First mac address to be summed
###\param[in] macAddr2 Second mac address to be summed
###\return String of the mac address sum of macAddr1 and macAddr2
###
###
###\author Mark Menor
###*/
###
###addMacAddr ( string macAddr1, string macAddr2 )
###

proc ::sth::Dhcp::addMacAddr { macAddr1 macAddr2 } {
    
    set binMac1 [::sth::Dhcp::macToBinary $macAddr1]
    set binMac2 [::sth::Dhcp::macToBinary $macAddr2]
    
    set newBinMac ""
    set iStatus [::sth::sthCore::binaryAddition $binMac1 $binMac2 newBinMac];
	if {$iStatus != 1} {
		return 0;
	}
    
    set len [string length $newBinMac]
	set r ""
	
    #convert binary character string to binary
    set m [binary format B48 $newBinMac]
    #convert binary to hex
	binary scan $m H12 hex
    #add MAC formatting
	for {set n 0} {$n < 12} {incr n} {
		append r [string range $hex $n [incr n 1]].
	}
	return [string trimright $r .]
}


###/*! \ingroup dhcphelperfuncs
### \fn getPort (str handle, varRef returnVarName)
###\brief get port handle based on the DhcpPort handle
###
###This procedure gets port handle based on the Dhcpv4PortConfig handle
###
###\param[in] handle The Dhcpv4PortConfig handle
###\param[out] returnVarName hold the return variable name
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### getPort(str handle, varRef msgName);
###

proc ::sth::Dhcp::getPort { handle returnVarName } {

    upvar $returnVarName returnVal
    
    if {[catch {set returnVal [::sth::sthCore::invoke stc::get $handle -parent]} errorMsg]} {
        set returnVal 0
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS

}


###/*! \ingroup dhcphelperfuncs
### \fn getHostHandle (str handle, varRef returnVarName)
###\brief get Host handle based on the Dhcpv4BlockConfig handle
###
###This procedure gets Host handle based on the Dhcpv4BlockConfig handle
###
###\param[in] handle The Dhcpv4BlockConfig handle
###\param[out] returnVarName hold the return variable name
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### getHostHandle(str handle, varRef msgName);
###

proc ::sth::Dhcp::getHostHandle { handle returnVarName } {

    upvar $returnVarName returnVal
    
    if {[catch {set returnVal [::sth::sthCore::invoke stc::get $handle -parent]} errorMsg]} {
        set returnVal 0
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS

}


###/*! \ingroup dhcphelperfuncs
### \fn getDhcpPort (str handle, varRef returnVarName)
###\brief get Dhcpv4PortConfig handle from Dhcpv4BlockConfig handle
###
###This procedure gets the Dhcpv4Portconfig handle based on the Dhcpv4BlockConfig handle
###
###\param[in] handle The Dhcpv4BlockConfig handle
###\param[out] returnVarName hold the return variable name
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### getDhcpPort(str handle, varRef msgName);
###

proc ::sth::Dhcp::getDhcpPort { handle returnVarName } {

    upvar $returnVarName returnVal
    
    if {![::sth::Dhcp::getHostHandle $handle hostHandle]} {
        set returnVal 0
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set hltPort [::sth::sthCore::invoke stc::get $hostHandle -AffiliationPort-targets]} errorMsg]} {
        set returnVal 0
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set returnVal [::sth::sthCore::invoke stc::get $hltPort -children-dhcpv4portconfig]} errorMsg]} {
        set returnVal 0
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcphelperfuncs
### \fn IsDhcpPortValid (str handle, varRef msgName)
###\brief Validates Dhcpv4PortConfig handle
###
###This procedure checks if the value is a valid Dhcpv4PortConfig handle or not.
###
###\param[in] handle The Dhcpv4PortConfig handle
###\param[out] msgName Error Msg
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### IsDhcpPortValid (str handle, varRef msgName);
###

proc ::sth::Dhcp::IsDhcpPortValid { handle msgName } {
    
    upvar $msgName errorMsg
    # for dhcpv4portconfig handles
    if {[regexp -nocase "^Dhcpv4PortConfig" $handle]} {
        return $::sth::sthCore::SUCCESS
    }
    # for port handles
    if {[catch {set objname [::sth::sthCore::invoke stc::get $handle -children-Dhcpv4PortConfig]} errorMsg]} {
        return $::sth::sthCore::FAILURE
    }
    if {$objname != ""} {
        return $::sth::sthCore::SUCCESS
    } else {
        set errorMsg "Value ($handle) is not a valid DhcpPort handle"
        return $::sth::sthCore::FAILURE
    }
}


###/*! \ingroup dhcphelperfuncs
### \fn IsDhcpSessionBlockHandleValid (str handle, varRef msgName)
###\brief Validates Dhcpv4BlockConfig handle
###
###This procedure checks if the value is a valid Dhcpv4BlockConfig handle or not.
###
###\param[in] handle The Dhcpv4BlockConfig handle
###\param[out] msgName Error Msg
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### IsDhcpSessionBlockHandleValid (str handle, varRef msgName);
###

proc ::sth::Dhcp::IsDhcpSessionBlockHandleValid { handles msgName } {

    upvar $msgName errorMsg       
    
    foreach handle $handles {
        if {[catch {::sth::sthCore::invoke stc::get $handle} errorMsg]} {
            return $::sth::sthCore::FAILURE
        }
        if {![string match -nocase dhcpv4blockconfig* $handle]} {
            set errorMsg "Value ($handle) is not a valid DhcpBlk handle"
            return $::sth::sthCore::FAILURE
        }
    }

    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcphelperfuncs
### \fn deleteHandleInHandleList (str handleValue, varRef handleListName, varRef errMsgName)
###\brief delete handle in the handle list
###
###This procedure deletes the handle if found in the handle list
###
###\param[in] handle The value of handle
###\param[in out] handleListName The name of handle list
###\param[out] errMsgName hold the error message
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
### deleteHandleInHandleList (str handleValue, varRef handleListName, varRef errMsgName);
###

proc ::sth::Dhcp::deleteHandleInHandleList { handle handleListName errMsgName } {
    
    upvar $handleListName handleList  
    upvar $errMsgName errMsg
    
    foreach index [array name handleList] {
        if {[set i [lsearch $handleList($index) $handle]] != -1} {
           set handleList($index) [lreplace $handleList($index) $i $i]
           return $::sth::sthCore::SUCCESS
        }
    }
    set errMsg "Value ($handle) is not found in the handlelist $handleListName"
    return $::sth::sthCore::FAILURE

}

###/*! \ingroup dhcphelperfuncs
### \fn getDHCPHandle (str param, str handleType, arrayRef switchArgs, keyedListRef returnStringName, varRef cmdStateVarName)
###\brief Gets and validates DHCP handle from user input found in array switchArgs
###
###This procedure get and validate handle of type $handleType (port, group, mix) specified in switch $param (handle, port_handle).
###
###\author Mark Menor
###*/
###
### getDHCPHandle (str param, str handleType, arrayRef switchArgs, keyedListRef returnStringName, varRef cmdStateVarName);
###

proc ::sth::Dhcp::getDHCPHandle { param handleType switchArgs returnStringName cmdStateVarName } {
    
    upvar $switchArgs userInputArgs
    upvar $returnStringName returnKeyedList
    upvar $cmdStateVarName cmdState
    
    if {![info exists userInputArgs($param)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -$param is a mandatory switch"
        set cmdState $::sth::sthCore::FAILURE
    	return $::sth::sthCore::FAILURE   
    }
    
    set msg ""
    set dhcpHandle $userInputArgs($param)
    
    if {$handleType == "port"} {
        set proc "::sth::Dhcp::IsDhcpPortValid"
    } elseif {$handleType == "group" || $handleType == "mix"} {
        set proc "::sth::Dhcp::IsDhcpSessionBlockHandleValid"
    } else {
        ::sth::sthCore::processError returnKeyedList "Internal error validating -$param switch"
        set cmdState $::sth::sthCore::FAILURE
    	return $::sth::sthCore::FAILURE 
    }
    
    set cmd "$proc {$dhcpHandle} msg"
    set cmdResult [eval $cmd]
	
	if {!$cmdResult && $handleType == "mix"} {
        set dhcpBlockHandles ""
		#Try to get children of type Dhcpv4BlockConfig
        foreach host $dhcpHandle {
            set dhcpBlockHandle [::sth::sthCore::invoke stc::get $host -children-Dhcpv4BlockConfig]
            if {$dhcpBlockHandle eq ""} {
                ::sth::sthCore::processError returnKeyedList "Cannot get valid children of type Dhcpv4BlockConfig"
                set cmdState $::sth::sthCore::FAILURE
                return $::sth::sthCore::FAILURE 
            }
            ::sth::sthCore::log debug "Got children of type Dhcpv4BlockConfig: $dhcpBlockHandle"
            lappend dhcpBlockHandles $dhcpBlockHandle
        }
        set dhcpHandle $dhcpBlockHandles
        set msg ""
        set cmd "$proc {$dhcpHandle} msg"
        set cmdResult [eval $cmd]
	}
    
    if {!$cmdResult} {
        if {[string equal $dhcpHandle SHA_NO_USER_INPUT] == 1} {
            set dhcpHandle "{{}}"
        }
        ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -$param"
        set cmdState $::sth::sthCore::FAILURE
        return $::sth::sthCore::FAILURE
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $dhcpHandle

}

###/*! \ingroup dhcphelperfuncs
### \fn callStcApply (keyedListRef returnStringName, varRef cmdStateVarName)
###\brief Calls doStcApply with exception handling.
###
###\author Mark Menor
###*/
###
### callStcApply (keyedListRef returnStringName, varRef cmdStateVarName);
###

proc ::sth::Dhcp::callStcApply { returnStringName cmdStateVarName } {
    
    upvar $returnStringName returnKeyedList
    upvar $cmdStateVarName cmdState
    
    #::sth::sthCore::log debug "Applying configuration"
    if {[catch {set iStatus [::sth::sthCore::doStcApply] } eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while applying: $eMsg" 
        return $::sth::sthCore::FAILURE
    }
    if {$iStatus != $::sth::sthCore::SUCCESS } {
        ::sth::sthCore::processError returnKeyedList "$iStatus"
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcphelperfuncs
### \fn deleteDhcpHost (str hostHandle, keyedListRef returnStringName)
###\brief Deletes Host and corresponding internal array data
###
###\author Mark Menor
###*/
###
### deleteDhcpHost (str hostHandle, keyedListRef returnStringName);
###

proc ::sth::Dhcp::deleteDhcpHost { hostHandle returnKeyedListVarName } {
    
    upvar $returnKeyedListVarName returnKeyedList
    
    if {[catch {::sth::sthCore::invoke stc::delete $hostHandle} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured while reseting Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #Unset host config settings
    catch {unset ::sth::Dhcp::DHCPHOSTENCAP($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANID($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANSTEP($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANPRI($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle)}
    catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle)} 
    
    return $::sth::sthCore::SUCCESS
    
}


###/*! \ingroup dhcphelperfuncs
###\fn createConfigDhcpPort (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName, varRef cmdStateVarName)
###\brief Create and config  DhcpPort
###
###This procedure creates a DhcpPort, configures it with the users input 
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
###createConfigDhcpPort (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName, varRef cmdStateVarName);
###

proc ::sth::Dhcp::createConfigDhcpPort { switchArgs mySortedPriorityList returnStringName cmdStateVarName } {

    set _OrigHltCmdName "emulation_dhcp_config"
    set _hltCmdName "emulation_dhcp_config_create"

    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnStringName returnKeyedList
    upvar $cmdStateVarName errOccured

    #Get port handle from port_handle or handle: at least one must exist
    if {![info exists userInputArgs(port_handle)] } {
        set handleVar $userInputArgs(handle)
        #Get port handle from Dhcpv4portconfig handle
        if {$userInputArgs(mode) == "create"} {
            if {![::sth::Dhcp::getPort $handleVar hltPort]} {
                ::sth::sthCore::processError returnKeyedList "The value $handleVar is not valid for the switch -handle"
                set cmdState $::sth::sthCore::FAILURE
                return $returnKeyedList             
            }
        } else {
            set handle $userInputArgs(handle)
            set hltPort [::sth::sthCore::invoke stc::get $handle -AffiliationPort-targets]
        }
    } else {
        set hltPort $userInputArgs(port_handle)
    }
    
    # Check if Dhcpv4portconfig already exists, if not make one
    if {[catch {set dhcpPort [::sth::sthCore::invoke stc::get $hltPort -children-dhcpv4portconfig]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Dhcp port: $getStatus"
        set errOccured 1
        return $::sth::sthCore::FAILURE
    }
    if {$dhcpPort == ""} {
        if {[catch {set dhcpPort [::sth::sthCore::invoke stc::create dhcpv4portconfig -under $hltPort ""]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Dhcp port: $getStatus"
            set errOccured 1
            return $::sth::sthCore::FAILURE
        }
    }
    
    #Configure the created Dhcpv4portconfig with user input (options)
    #::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"    
    set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName userInputArgs sortedPriorityList \
                   $dhcpPort returnKeyedList]
    
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdFailed 1
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    }
    
    #Configure HLTAPI defaults for switches user did not specifically set
    #::sth::sthCore::log debug "Processing the default switches for command:$_hltCmdName" 
    array set defaultArray [list lease_time 86400 \
                        max_dhcp_msg_size 576 \
                        msg_timeout 15000 \
                        release_rate 500 \
                        request_rate 500 \
                        retry_count 3 \
                        outstanding_session_count 100 \
                    ]
    
    set cmdResult [::sth::Dhcp::processConfigDefaults ::sth::Dhcp:: $_OrigHltCmdName defaultArray userInputArgs \
                   $dhcpPort returnKeyedList]
    
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdFailed 1
        keylset returnKeyedList status $::sth::sthCore::FAILURE
    }
    
    if {[::info exists cmdFailed]} {
        #Delete the Dhcpv4portconfig Object
        if {[catch {::sth::sthCore::invoke stc::delete $dhcpPort} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error deleting previously created Dhcpv4portconfig:$dhcpPort Msg: $eMsg"
        }
        set errOccured 1
        return $::sth::sthCore::FAILURE
    } else {
        #apply  all configurations
        if {!$::sth::sthCore::optimization} {
            if {[catch {::sth::sthCore::doStcApply} err]} {
                ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
                return $returnKeyedList
            }
        }
        
        #Update arrays and the returnKeyedList
        #::sth::sthCore::log debug "New Dhcpv4portconfig $dhcpPort created"
        keylset returnKeyedList handle.$hltPort $dhcpPort
        keylset returnKeyedList handles $dhcpPort
        set errOccured 0
        return $::sth::sthCore::SUCCESS    
    }

}


###/*! \ingroup dhcphelperfuncs
###\fn processConfigSwitches (str mynamespace, str mycmd, arrayRef switchArgs, listRef mySortedPriorityList, str switchHandle, keyedListRef returnStringName)
###\brief Process config switchs on object $switchHandle
###
###\author Mark Menor
###*/
###
###processConfigSwitches (str mynamespace, str mycmd, arrayRef switchArgs, listRef mySortedPriorityList, str switchHandle, keyedListRef returnStringName);
###

proc ::sth::Dhcp::processConfigSwitches { mynamespace mycmd switchArgs mySortedPriorityList switchHandle returnStringName } {

    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnStringName returnKeyedList
    
    set doStcConfigCmd "::sth::sthCore::invoke stc::config $switchHandle \""
    foreach {switch} $sortedPriorityList {
        set switchName [lindex $switch 1]
        #return if the switch value has been unset
        if {![info exists userInputArgs($switchName)]} {
            continue
        }
        set switchValue $userInputArgs($switchName)
        if {[::sth::sthCore::getswitchprop $mynamespace $mycmd $switchName supported]} {
            set switchProcFunc [::sth::sthCore::getswitchprop $mynamespace $mycmd $switchName procfunc]
            if {$switchProcFunc != "_none_"} {
                set cmd "$mynamespace$switchProcFunc {$switchValue} returnKeyedList $mycmd $switchName $switchHandle doStcConfigCmd"

                set cmdResult [eval $cmd]
                #::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
                if {$cmdResult == $::sth::sthCore::FAILURE} {
                    set logStatus "$mycmd: Error occured while configuring switch $switchName with Value $switchValue"
                    return $::sth::sthCore::FAILURE
                }
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "-$switchName is not a supported switch"
            return $::sth::sthCore::FAILURE
        }
        
    }
    
    set doStcConfigCmd "$doStcConfigCmd\""
    
    if {[catch {eval $doStcConfigCmd} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error configuring $switchHandle: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    return $::sth::sthCore::SUCCESS 
}


###/*! \ingroup dhcphelperfuncs
###\fn processConfigSwitches (str mynamespace, str mycmd, arrayRef switchArgs, listRef mySortedPriorityList, str switchHandle, keyedListRef returnStringName)
###\brief Process config switchs on object $switchHandle with default values if user did not specify them
###
###\author Mark Menor
###*/
###
###processConfigSwitches (str mynamespace, str mycmd, arrayRef switchArgs, listRef mySortedPriorityList, str switchHandle, keyedListRef returnStringName);
###

proc ::sth::Dhcp::processConfigDefaults { mynamespace mycmd defaultArrayName switchArgs  switchHandle returnStringName } {

    upvar $switchArgs userInputArgs
    upvar $defaultArrayName defaultArray
    upvar $returnStringName returnKeyedList
    
    set doStcConfigCmd "::sth::sthCore::invoke stc::config $switchHandle \""
    foreach switchName [array names defaultArray] {
        if {![info exists userInputArgs($switchName)]} {
            set switchValue $defaultArray($switchName)
            if {[::sth::sthCore::getswitchprop $mynamespace $mycmd $switchName supported]} {
                set switchProcFunc [::sth::sthCore::getswitchprop $mynamespace $mycmd $switchName procfunc]
                if {$switchProcFunc != "_none_"} {
                    set cmd "::sth::Dhcp::$switchProcFunc {$switchValue} returnKeyedList $mycmd $switchName $switchHandle doStcConfigCmd"

                    set cmdResult [eval $cmd]
                    ::sth::sthCore::log debug "SWITCH RESULT for switch $switchName: $cmdResult"
                    if {$cmdResult == $::sth::sthCore::FAILURE} {
                        set cmdFailed 1
                        set errOccured 1
                        set logStatus "$mycmd: $cmdFailed Error occured while configuring switch $switchName with Value $switchValue"
                        ::sth::sthCore::processError returnKeyedList "$logStatus" {}
                        break
                    }
                }
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: -$switchName is not a supported switch"
                return $::sth::sthCore::FAILURE
            }
        }
    }
    
    set doStcConfigCmd "$doStcConfigCmd\""

    
    if {[catch {eval $doStcConfigCmd} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error configuring $switchHandle"
        return $::sth::sthCore::FAILURE
    }

}


###/*! \ingroup dhcphelperfuncs
###\fn createConfigDhcpSessionBlock (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName, varRef cmdStateVarName)
###\brief Create and config DhcpSessionBlock
###
###This procedure create a DhcpSessionBlock, configures it with the users input 
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\author Mark Menor
###*/
###
###createConfigDhcpSessionBlock (arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName, varRef cmdStateVarName);
###

proc ::sth::Dhcp::createConfigDhcpSessionBlock { switchArgs mySortedPriorityList returnStringName cmdStateVarName } {

    set _OrigHltCmdName "emulation_dhcp_group_config"
    set _hltCmdName "emulation_dhcp_group_config_create"

    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnStringName returnKeyedList
    upvar $cmdStateVarName errOccured

    if {$userInputArgs(mode) == "create"} {
        #Get port handle from DhcpPort handle
        set dhcpHandle $userInputArgs(handle)
    
        if {![::sth::Dhcp::getPort $dhcpHandle hltPort]} {
            ::sth::sthCore::processError returnKeyedList "The value $dhcpHandle is not valid for the switch -handle"
            set cmdState $::sth::sthCore::FAILURE
            return $returnKeyedList             
        }
        
        #Create Host and Dhcpv4BlockConfig objects
        set hostHandle ""
        if {[catch {set status [::sth::Dhcp::emulation_dhcp_group_config_encap $userInputArgs(encap) $userInputArgs(protocol) \
                             $hltPort hostHandle returnKeyedList errOccured dhcpSessionBlockHandle]} eMsg] || !$status} {
            return $::sth::sthCore::FAILURE
        }
    } else {
        #enable dhcp under an existing device
        set hostHandle $userInputArgs(handle)
        #get the dhcpv4 port handle
        set hltPort [::sth::sthCore::invoke stc::get $hostHandle -AffiliationPort-targets]
        set dhcpHandle [::sth::sthCore::invoke stc::get $hltPort -children-Dhcpv4PortConfig]
        if {$userInputArgs(mode) == "enable"} {
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
                #::sth::sthCore::invoke stc::config $hostHandle -primaryif-Targets $primaryifTargets -toplevelif-Targets $toplevelifTargets
                ::sth::sthCore::invoke stc::config $ipv4ifhandle -primaryif-Sources $hostHandle -toplevelif-Sources $hostHandle     
            }
        }
        #set the DHCPHOSTPROTOCOL to use in modify mode
        set ::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle) $userInputArgs(protocol)
        if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-Ipv4If]} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        #Create new DHCP block
        if {[catch {set dhcpSessionBlockHandle [::sth::sthCore::invoke stc::create Dhcpv4BlockConfig -under $hostHandle "-UsesIf-targets [lindex $ipv4ResultIf 0]"]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal error creating DHCP group: $createStatus"
            set errOccured 1
            return $::sth::sthCore::FAILURE
        }
        
        
        #unset unnecessary config
        foreach hname {mac_addr mac_addr_step vlan_id vlan_id_outer vlan_id_step vlan_id_outer_step vlan_id_count \
                       vlan_id_outer_count vlan_user_priority vlan_outer_user_priority qinq_incr_mode qinq_oneblock\
                       gateway_addresses ipv4_gateway_address vci vpi vci_count vci_step vpi_count vpi_step pvc_incr_mode} {
            
            if {[info exists userInputArgs($hname)]} {
                    unset userInputArgs($hname)
            }
        } 
    }

    set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName userInputArgs \
                   sortedPriorityList $dhcpSessionBlockHandle returnKeyedList] 
    if {$cmdResult == $::sth::sthCore::FAILURE} {
        set cmdState $::sth::sthCore::FAILURE
        set cmdFailed 1
    }
    
    if {![::info exists cmdFailed]} {
        #Configure HLTAPI defaults for switches user did not specifically set
        
        #array set defaultArray [list num_sessions 4096 \
        #                             relay_mac_dst ff.ff.ff.ff.ff.ff \
        #                            ]
        array set defaultArray [list num_sessions 4096 ]
        if {$userInputArgs(mode) == "create"} {
        set cmdResult [::sth::Dhcp::processConfigDefaults ::sth::Dhcp:: $_OrigHltCmdName defaultArray userInputArgs \
                       $dhcpSessionBlockHandle returnKeyedList]
        if {$cmdResult == $::sth::sthCore::FAILURE} {
            set cmdState $::sth::sthCore::FAILURE
            set cmdFailed 1
        }
        }
    }
    if {$userInputArgs(mode) == "create"} {
        if {![::info exists cmdFailed]} {
            #Create/config additional groups for ethernet_ii_qinq
            if {$userInputArgs(encap) == "ethernet_ii_qinq" || $userInputArgs(encap) == "ethernet_ii_mvlan"} {
                set cmdResult [::sth::Dhcp::createQinQHosts $hostHandle $hltPort userInputArgs sortedPriorityList returnKeyedList]
                if {$cmdResult == $::sth::sthCore::FAILURE} {
                    set cmdState $::sth::sthCore::FAILURE
                    return $returnKeyedList 
                }
            }
        }
        
        if {![::info exists cmdFailed]} {
            set cmdResult [::sth::Dhcp::configVlan $dhcpSessionBlockHandle $hltPort returnKeyedList]
            if {$cmdResult == $::sth::sthCore::FAILURE} {
                set cmdState $::sth::sthCore::FAILURE
                set cmdFailed 1
            }
        }
    }

    if {[::info exists cmdFailed]} {    
        #Delete the DhcpSessionBlock Object
        if {![::sth::Dhcp::deleteDhcpHost $hostHandle returnKeyedList]} {
            ::sth::sthCore::processError returnKeyedList "createConfigDhcpSessionBlock: Error deleting previously created Dhcp Host:$hostHandle" {}
        }
        set errOccured 1
        return $::sth::sthCore::FAILURE
    } else {
        #apply  all configurations
        if {!$::sth::sthCore::optimization} {
            if {[catch {::sth::sthCore::doStcApply} err]} {
                ## if apply fails, delete any host we may have created
                #if {[catch {::sth::sthCore::invoke stc::delete $hostHandle} err]} {
                #    return -code error "$err"   
                #}
                ::sth::sthCore::processError returnKeyedList "Error applying DHCP configuration: $err"
                return $returnKeyedList
            }
        }
        #Update arrays and the returnKeyedList    
        lappend ::sth::Dhcp::DHCPHOSTS($dhcpHandle) $hostHandle
        keylset returnKeyedList handles $dhcpSessionBlockHandle
        #add "dhcp host" handle as output value (xiaozhi, 6/22/09)
        keylset returnKeyedList handle $hostHandle
        set errOccured 0
        return $::sth::sthCore::SUCCESS    
    }

}


###/*! \ingroup dhcphelperfuncs
###\fn createQinQHosts (str hostHandle, str hltPort, arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName)
###\brief Create additional Hosts for encap ethernet_ii_qinq
###
###\author Mark Menor
###*/
###
###createQinQHosts (str hostHandle, str hltPort, arrayRef switchArgs, listRef mySortedPriorityList, keyedListRef returnStringName);
###

proc ::sth::Dhcp::createQinQHosts { hostHandle hltPort switchArgs mySortedPriorityList returnStringName } {
    
    set _OrigHltCmdName "emulation_dhcp_group_config"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnStringName returnInfo
    
    array set defaultArray [list num_sessions 4096 ]
    
    #Get number of sessions
    if {[catch {set numSessions $::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #Get Dhcpv4portconfig handle
    if {[catch {set dhcpPort [::sth::sthCore::invoke stc::get $hltPort -children-Dhcpv4PortConfig]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    if {![info exists userInputArgs(qinq_oneblock)] || $userInputArgs(qinq_oneblock) == 0} {
        
        set ::sth::Dhcp::qinqOneblock($hostHandle) 0
        if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)]} {
            set outerVlanCount 1
        } else {
            set outerVlanCount $::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)
        }
        
        
        # #STC limitation: outerVlanCount must divide numSessions
        # if {[expr $numSessions % $outerVlanCount != 0]} {
            # ::sth::sthCore::processError returnInfo "The value $outerVlanCount is not valid for switch vlan_id_count or vlan_id_outer_count: It does not divide $numSessions"
            # return $::sth::sthCore::FAILURE
        # }
        
        if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)]} {
            set innerVlanCount 1
        } else {
            set innerVlanCount $::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)
        }
        
        #for DHCPHOSTOUTERVLANREPEATCOUNT
        if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle)]} {
            set outerVlanRepeatCount 0
        } else {
            set outerVlanRepeatCount $::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle)
        }
        
        #for DHCPHOSTINNERVLANREPEATCOUNT
        if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle)]} {
            set innerVlanRepeatCount 0
        } else {
            set innerVlanRepeatCount $::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle)
        }
      
        if {![info exists ::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle)]} {
            set qinqMode inner
        } else {
            set qinqMode $::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle)
        }
        
        # #STC limitation: innerVlanCount must divide numSessions
        # if {[expr $numSessions % $innerVlanCount != 0]} {
            # ::sth::sthCore::processError returnInfo "The value $innerVlanCount is not valid for switch vlan_id_count: It does not divide $numSessions"
            # return $::sth::sthCore::FAILURE
        # }
        
        #Calculate how many groups to create
        if {($numSessions == $outerVlanCount) || ($numSessions == $innerVlanCount) || ($innerVlanCount == 1)
            || ($outerVlanCount == 1)} {
            set numGroups 1
        } else {
            if { $innerVlanRepeatCount != 0 || $outerVlanRepeatCount !=0 } {
                set numGroups 1
            } else {
                
                if {$numSessions != [expr $outerVlanCount * $innerVlanCount]} {
                    ::sth::sthCore::processError returnInfo "The value $innerVlanCount is not valid for switch vlan_id_count: num_sessions must equal vlan_id_count * vlan_id_outer_count"
                    return $::sth::sthCore::FAILURE
                }
            
                if {$qinqMode == "outer"} {
                    set numGroups [expr $numSessions / $outerVlanCount]
                } else {
                    set numGroups [expr $numSessions / $innerVlanCount]
                }
            
                if {$numGroups > 1024} {
                    ::sth::sthCore::processError returnInfo "The combined values of num_sessions, vlan_id_count, and vlan_id_outer are not supported"
                    return $::sth::sthCore::FAILURE
                }
            }
        }
         
        set ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) $hostHandle
        
        for {set idx 1} {$idx < $numGroups} {incr idx} {        
            #Create Host and Dhcpv4BlockConfig objects
            set newHostHandle ""
            if {[catch {set status [::sth::Dhcp::emulation_dhcp_group_config_encap $userInputArgs(encap) $userInputArgs(protocol) $hltPort \
                                    newHostHandle returnInfo errOccured newDhcpHandle]} eMsg] || !$status} {
                ::sth::sthCore::processError returnKeyedList "Internal error creating Dhcp group: $eMsg"
                return $::sth::sthCore::FAILURE
            }

            set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName userInputArgs \
                            sortedPriorityList $newDhcpHandle returnInfo] 
            if {$cmdResult == $::sth::sthCore::FAILURE} {
                set cmdState $::sth::sthCore::FAILURE
                set cmdFailed 1
                break
            }
            
            set cmdResult [::sth::Dhcp::processConfigDefaults ::sth::Dhcp:: $_OrigHltCmdName defaultArray userInputArgs \
                   $newDhcpHandle returnInfo]
            if {$cmdResult == $::sth::sthCore::FAILURE} {
                set cmdState $::sth::sthCore::FAILURE
                set cmdFailed 1
                break
            }
            
            lappend ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) $newHostHandle
            lappend ::sth::Dhcp::DHCPHOSTS($dhcpPort) $newHostHandle
        }
    } else {
        
        if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)]} {
            set outerVlanCount 1
        } else {
            set outerVlanCount $::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)
        }
        # #STC limitation: outerVlanCount must divide numSessions
        # if {[expr $numSessions % $outerVlanCount != 0]} {
            # ::sth::sthCore::processError returnInfo "The value $outerVlanCount is not valid for switch vlan_id_count or vlan_id_outer_count: It does not divide $numSessions"
            # return $::sth::sthCore::FAILURE
        # }
        
        if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)]} {
            set innerVlanCount 1
        } else {
            set innerVlanCount $::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)
        }
        
        #STC limitation: innerVlanCount must divide numSessions
        # if {[expr $numSessions % $innerVlanCount != 0]} {
            # ::sth::sthCore::processError returnInfo "The value $innerVlanCount is not valid for switch vlan_id_count: It does not divide $numSessions"
            # return $::sth::sthCore::FAILURE
        # }
        
        set ::sth::Dhcp::qinqOneblock($hostHandle) 1
        
        lappend ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) $hostHandle
    }
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcphelperfuncs
###\fn configVlan (str handle, str hltPort, keyedListRef returnStringName)
###\brief Configure Host and Vlan interfaces
###
###\author Mark Menor
###*/
###
###configVlan (str handle, str hltPort, keyedListRef returnStringName);
###

proc ::sth::Dhcp::configVlan { handle hltPort returnInfoVarName } {
    variable ::sth::Dhcp::userArgsArray
    upvar $returnInfoVarName returnInfo
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "::sth::Dhcp::configVlan: Not able to get host handle from $handle" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Get encap type of host
    if {[catch {set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #if {$::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle) == "dhcpoa"} {
    #    return $::sth::sthCore::SUCCESS
    #}
    
    #Check if supported encap
    switch -- $encap {
        ethernet_ii -
        ethernet_ii_vlan -
        ethernet_ii_qinq -
        ethernet_ii_mvlan {
        }
        vc_mux -
        llcsnap {
            return $::sth::sthCore::SUCCESS
        }
        default {
            ::sth::sthCore::processError returnInfo "The value $encap is not valid for the switch -encap"
            return $::sth::sthCore::FAILURE
        }
    }
    
    #Get number of sessions and set device count
    if {[catch {set numSessions $::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    if {$encap == "ethernet_ii" || $encap == "ethernet_ii_vlan"} {
        if {$::sth::Dhcp::relay_agent_flag == 0} {
            if {[catch {::sth::sthCore::invoke stc::config $hostHandle "-DeviceCount $numSessions"} eMsg]} {
                ::sth::sthCore::processError returnInfo "The value $numSessions is not valid for switch -num_sessions: $eMsg"
                return $::sth::sthCore::FAILURE
            }
        } else {
            if {[catch {set ipIf [::sth::sthCore::invoke stc::get $hostHandle "-children-ipv4if"]} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
                return $::sth::sthCore::FAILURE
            }
            if {[catch {::sth::sthCore::invoke stc::config [lindex $ipIf 0] "-IfCountPerLowerIf $numSessions"} eMsg]} {
                ::sth::sthCore::processError returnInfo "The value $numSessions is not valid for switch -num_sessions: $eMsg"
                return $::sth::sthCore::FAILURE
            }
        }
    }
    
    #Done if configuring encap ethernet_ii
    if {$encap == "ethernet_ii"} {
        return $::sth::sthCore::SUCCESS
    }
    
    #Grab outer VlanIf handle and outer vlan id count
    if {[catch {set outerVlanHandle $::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)]} {
        set outerVlanCount 1
    } else {
        set outerVlanCount $::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle)
    }
    if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle)]} {
        set outerVlanId 1
    } else {
        set outerVlanId $::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle)
    }
    if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle)]} {
        set outerVlanStep 1
    } else {
        set outerVlanStep $::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle)
    }
    if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle)]} {
        set outerVlanPri 0
    } else {
        set outerVlanPri $::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle)
    }
    
    #for DHCPHOSTOUTERVLANREPEATCOUNT
    if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle)]} {
        set outerVlanRepeatCount 0
    } else {
        set outerVlanRepeatCount $::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle)
    }
    
    # #STC limitation: outerVlanCount must divide numSessions
    # if {[expr $numSessions % $outerVlanCount != 0]} {
        # ::sth::sthCore::processError returnInfo "The value $outerVlanCount is not valid for switch vlan_id_count or vlan_id_outer_count: It does not divide $numSessions"
        # return $::sth::sthCore::FAILURE
    # }
    set tpid $::sth::Dhcp::userArgsArray(vlan_ether_type)
    if {$encap == "ethernet_ii_vlan"} {
        if {[info exists ::sth::Dhcp::userArgsArray(qinq_oneblock)] && $::sth::Dhcp::userArgsArray(qinq_oneblock) == 0} {
            #Set outer vlan if's IdRepeatCount (repeat)
            set count [expr ($numSessions / $outerVlanCount) - 1]
            if {[catch {::sth::sthCore::invoke stc::config $outerVlanHandle "-VlanId $outerVlanId -IdStep $outerVlanStep -IdRepeatCount $count -Priority $outerVlanPri -Tpid $tpid"} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
                return $::sth::sthCore::FAILURE
            }
        } else {
            set tpid $::sth::Dhcp::userArgsArray(vlan_outer_ether_type)
            if {[catch {::sth::sthCore::invoke stc::config $outerVlanHandle "-VlanId $outerVlanId -IdStep $outerVlanStep -IfRecycleCount $outerVlanCount -IdRepeatCount 0 -Priority $outerVlanPri -Tpid $tpid"} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
                return $::sth::sthCore::FAILURE
            }
        }
    }
    
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)]} {
            set innerVlanCount 1
        } else {
            set innerVlanCount $::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle)
        }
        
        if {![info exists ::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle)]} {
            set qinqMode inner
        } else {
            set qinqMode $::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle)
        }
        
        #for DHCPHOSTINNERVLANREPEATCOUNT
        if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle)]} {
            set innerVlanRepeatCount 0
        } else {
            set innerVlanRepeatCount $::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle)
        }
      
        
        set cmdResult [::sth::Dhcp::configQinq $hostHandle $numSessions $innerVlanCount $outerVlanCount $innerVlanRepeatCount $outerVlanRepeatCount $qinqMode returnInfo]
        if {$cmdResult == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: QinQ hosts"
            return $::sth::sthCore::FAILURE
        }
    }
    
    if {$encap == "ethernet_ii_mvlan"} {
        set cmdResult [::sth::Dhcp::configMVlan $hostHandle $numSessions returnInfo]
        if {$cmdResult == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: multiple Vlan hosts"
            return $::sth::sthCore::FAILURE
        }
    }

    return $::sth::sthCore::SUCCESS   
}


proc ::sth::Dhcp::configMVlan {hostHandle numSessions returnInfoVarName} {
    variable ::sth::Dhcp::userArgsArray
    upvar $returnInfoVarName returnInfo
    
    if {[info exists ::sth::Dhcp::userArgsArray(vlan_id_list)]} {   
        set vlanid_list $::sth::Dhcp::userArgsArray(vlan_id_list)
        set tpid_list $::sth::Dhcp::userArgsArray(vlan_ether_type_list)
        set idcount_list $::sth::Dhcp::userArgsArray(vlan_id_count_list)
        set userprio_list $::sth::Dhcp::userArgsArray(vlan_user_priority_list)
        set idstep_list $::sth::Dhcp::userArgsArray(vlan_id_step_list)
        set repeatcount_list $::sth::Dhcp::userArgsArray(vlan_id_repeat_count_list)
        
        foreach host $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) {
            #Get vlan interface handles
            if {[info exists ::sth::Dhcp::DHCPHOSTINNERVLANIF($host)]} {
                set vlanHandle $::sth::Dhcp::DHCPHOSTINNERVLANIF($host)
            } else {
                set vlanHandle $::sth::Dhcp::DHCPHOSTOUTERVLANIF($host)
            }

            set stackedHandle [::sth::sthCore::invoke stc::get $vlanHandle "-stackedonendpoint-Sources"]
            set stack_src [regsub -all {vlanif\d+} $stackedHandle ""]
            if {[regexp -all {vlanif\d+} $stackedHandle matchHandle]} {
                foreach hnd $matchHandle {
                    set thnd_list ""
                    set target [::sth::sthCore::invoke stc::get $hnd "-stackedonendpoint-Sources"]
                    while {$target != ""} {
                        append thnd_list "$target "
                        set target [::sth::sthCore::invoke stc::get $target "-stackedonendpoint-Sources"]
                    }
                    foreach thnd $thnd_list {
                       ::sth::sthCore::invoke stc::delete $thnd 
                    }
                    ::sth::sthCore::invoke stc::delete $hnd
                }
            }
    
            set i 0
            foreach vlanid $vlanid_list {
                set myvlanid $vlanid 
                set stackedHandle [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle "-StackedOnEndpoint-targets $vlanHandle"]
                
                set tpid [lindex $tpid_list $i]
                if {$tpid == ""} {
                    set tpid $::sth::Dhcp::emulation_dhcp_group_config_default(vlan_ether_type_list)
                }
                set idcount [lindex $idcount_list $i]
                if {$idcount == ""} {
                    set idcount $::sth::Dhcp::emulation_dhcp_group_config_default(vlan_id_count_list)
                }
                set usrprio [lindex $userprio_list $i]
                if {$usrprio == ""} {
                    set usrprio $::sth::Dhcp::emulation_dhcp_group_config_default(vlan_user_priority_list)
                }
                set idstep [lindex $idstep_list $i]
                if {$idstep == ""} {
                    set idstep $::sth::Dhcp::emulation_dhcp_group_config_default(vlan_id_step_list)
                }
                set repeatcount [lindex $repeatcount_list $i]
                if {$repeatcount == ""} {
                    set repeatcount $::sth::Dhcp::emulation_dhcp_group_config_default(vlan_id_repeat_count_list)
                }
                
                if {[catch {::sth::sthCore::invoke stc::config $stackedHandle "-VlanId $myvlanid -IdStep $idstep -IdRepeatCount $repeatcount -IfRecycleCount $idcount -Priority $usrprio -Tpid $tpid"} eMsg]} {
                    ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
                    return $::sth::sthCore::FAILURE
                }

                set vlanHandle $stackedHandle
                incr i
            }
            
            ::sth::sthCore::invoke stc::config $stack_src "-stackedonendpoint-Targets $vlanHandle"
        }
    }
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcphelperfuncs
###\fn configQinq (str hostHandle, str numSessions, str innerVlanCount, str outerVlanCount, str qinqMode, keyedListRef returnStringName)
###\brief Configure Host and Vlan interfaces for Qinq Hosts
###
###\author Mark Menor
###*/
###
###configQinq (str hostHandle, str numSessions, str innerVlanCount, str outerVlanCount, str qinqMode, keyedListRef returnStringName);
###

proc ::sth::Dhcp::configQinq { hostHandle numSessions innerVlanCount outerVlanCount innerVlanRepeatCount outerVlanRepeatCount qinqMode returnInfoVarName } {
    upvar $returnInfoVarName returnInfo
    
    set numGroups [llength $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]
    set numSessPerGroup [expr $numSessions / $numGroups]
    #"Debug $numGroups groups with $numSessPerGroup sess/each"
    
    #Get vlan interface handles
    if {[catch {set innerVlanHandle $::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set outerVlanHandle $::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #Get inner and outer vlan ids, steps
    if {[catch {set innerVlanIdStart $::sth::Dhcp::DHCPHOSTINNERVLANID($hostHandle)} eMsg]} {
        #::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        #return $::sth::sthCore::FAILURE
        set innerVlanIdStart 1
    }
    if {[catch {set innerVlanIdStep $::sth::Dhcp::DHCPHOSTINNERVLANSTEP($hostHandle)} eMsg]} {
        #::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        #return $::sth::sthCore::FAILURE
        set innerVlanIdStep 1
    }
    if {[catch {set outerVlanIdStart $::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle)} eMsg]} {
        #::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        #return $::sth::sthCore::FAILURE
        set outerVlanIdStart 1
    }
    if {[catch {set outerVlanIdStep $::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle)} eMsg]} {
        #::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
        #return $::sth::sthCore::FAILURE
        set outerVlanIdStep 1
    }
    if {[catch {set innerVlanPri $::sth::Dhcp::DHCPHOSTINNERVLANPRI($hostHandle)} eMsg]} {
        set innerVlanPri 0
    }
    if {[catch {set outerVlanPri $::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle)} eMsg]} {
        set outerVlanPri 0
    }
    
    #Get hostHandle's EthIIIf and sourcemac and srcmacstep
    if {[catch {set ethiiResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-EthIIIf]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set sourceMac [::sth::sthCore::invoke stc::get $ethiiResultIf -SourceMac]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set srcMacStep [::sth::sthCore::invoke stc::get $ethiiResultIf -SrcMacStep]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
        return $::sth::sthCore::FAILURE
    }

    #configure subhosts
    set vlanIdCount 0
    set nextMacAddr $sourceMac
    foreach host $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) {
        #Set host device count to numSessPerGroup
        if {[catch {::sth::sthCore::invoke stc::config $host "-DeviceCount $numSessPerGroup"} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring -encap ethernet_ii_qinq: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        
        if {[catch {set ethiiResultIf [::sth::sthCore::invoke stc::get $host -children-EthIIIf]} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }

        #Get vlan interface handles
        if {[catch {set innerVlanHandle $::sth::Dhcp::DHCPHOSTINNERVLANIF($host)} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        if {[catch {set outerVlanHandle $::sth::Dhcp::DHCPHOSTOUTERVLANIF($host)} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        
        if {$::sth::Dhcp::qinqOneblock($hostHandle) == 0} {
            #TODO: this probably is incorrect for some cases...
            #Calculate and set IdRepeatCount, mac addresses, start vlan ids
            
            if {$outerVlanRepeatCount != 0 || $innerVlanRepeatCount != 0} {
                set innerVlanRepeat $innerVlanRepeatCount
                set outerVlanRepeat $outerVlanRepeatCount
                set outerVlanId $outerVlanIdStart
                set innerVlanId $innerVlanIdStart
                set outerVlanRecycle $outerVlanCount
                set innerVlanRecycle $innerVlanCount
            } elseif {$numSessPerGroup == $numSessions} {
                set outerVlanRepeat [expr ($numSessions / $outerVlanCount) - 1]
                set innerVlanRepeat [expr ($numSessions / $innerVlanCount) - 1]
                set outerVlanId $outerVlanIdStart
                set innerVlanId $innerVlanIdStart
                set outerVlanRecycle 0
                set innerVlanRecycle 0
            } elseif {$qinqMode == "outer"} {
                set outerVlanRepeat 0
                set innerVlanRepeat [expr $outerVlanCount -1]
                set outerVlanId $outerVlanIdStart
                set innerVlanId [expr $innerVlanIdStart + ($vlanIdCount * $innerVlanIdStep)]
                incr vlanIdCount
                if {$vlanIdCount >= $innerVlanCount} {
                    set vlanIdCount 0
                }
                set outerVlanRecycle 0
                set innerVlanRecycle 0
            } else {
                set innerVlanRepeat 0
                set outerVlanRepeat [expr $innerVlanCount - 1]
                set innerVlanId $innerVlanIdStart
                set outerVlanId [expr $outerVlanIdStart + ($vlanIdCount * $outerVlanIdStep)]
                incr vlanIdCount
                if {$vlanIdCount >= $outerVlanCount} {
                    set vlanIdCount 0
                }
                set outerVlanRecycle 0
                set innerVlanRecycle 0
            }
        } else {
            #add by xiaozhi
            if {$qinqMode == "inner"} {
                set innerVlanRepeat 0
                set outerVlanRepeat [expr $innerVlanCount - 1]
                set innerVlanId $innerVlanIdStart
                set outerVlanId $outerVlanIdStart
                set innerVlanRecycle $innerVlanCount
                set outerVlanRecycle $outerVlanCount
            } elseif {$qinqMode == "outer"} {
                set innerVlanRepeat [expr $outerVlanCount - 1]
                set outerVlanRepeat 0
                set innerVlanId $innerVlanIdStart
                set outerVlanId $outerVlanIdStart
                set innerVlanRecycle $innerVlanCount
                set outerVlanRecycle $outerVlanCount
            } 
        }

        set tpid $::sth::Dhcp::userArgsArray(vlan_ether_type)
        set tpid_outer $::sth::Dhcp::userArgsArray(vlan_outer_ether_type)
        #Configure VlanIfs, EthIIIF
        #Debug: setting up $innerVlanHandle with id $innerVlanId and repeat $innerVlanRepeat"
        if {[catch {::sth::sthCore::invoke stc::config $innerVlanHandle "-VlanId $innerVlanId -IdStep $innerVlanIdStep -IdRepeatCount $innerVlanRepeat -IfRecycleCount $innerVlanRecycle -Priority $innerVlanPri -Tpid $tpid"} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }

        if {[catch {::sth::sthCore::invoke stc::config $outerVlanHandle "-VlanId $outerVlanId -IdStep $outerVlanIdStep -IdRepeatCount $outerVlanRepeat -IfRecycleCount $outerVlanRecycle -Priority $outerVlanPri -Tpid $tpid_outer"} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $ethiiResultIf "-SourceMac $nextMacAddr -SrcMacStep $srcMacStep"} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }

        if {[catch {set nextMacAddr [::sth::Pppox::MACIncr $nextMacAddr $srcMacStep $numSessPerGroup]} err]} {
            ::sth::sthCore::processError returnInfo "Internal error configuring Dhcp group: $err"
            return $::sth::sthCore::FAILURE
        }
        
    }
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_num_sessions (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch num_sessions
###
###This procedure implements the config command for Dhcp group switch num_sessions.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_num_sessions (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_num_sessions { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_num_sessions: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    set ::sth::Dhcp::DHCPHOSTNUMSESS($hostHandle) $switchValue
    
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id
###
###This procedure implements the config command for Dhcp group switch vlan_id.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Check encap
    set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)

    #Config VlanIfs
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        set ::sth::Dhcp::DHCPHOSTINNERVLANID($hostHandle) $switchValue
    } else {
        set ::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle) $switchValue
    }
    
    return $::sth::sthCore::SUCCESS
    
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id_step (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id_step
###
###This procedure implements the config command for Dhcp group switch vlan_id_step.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id_step (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_step { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_step: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Check encap
    set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)
    
    #Config VlanIfs
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        set ::sth::Dhcp::DHCPHOSTINNERVLANSTEP($hostHandle) $switchValue
    } else {
        set ::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle) $switchValue
    }
    
    return $::sth::sthCore::SUCCESS
    
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id_outer (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id_outer
###
###This procedure implements the config command for Dhcp group switch vlan_id_outer.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id_outer (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_outer { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_outer: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Config VlanIfs
    set ::sth::Dhcp::DHCPHOSTOUTERVLANID($hostHandle) $switchValue
    
    return $::sth::sthCore::SUCCESS
    
}

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_priority { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
    	return $::sth::sthCore::FAILURE
    }
    
    #Check encap
    set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)
    
    #Config VlanIfs
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        set ::sth::Dhcp::DHCPHOSTINNERVLANPRI($hostHandle) $switchValue
    } else {
        set ::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle) $switchValue
    }
    
    return $::sth::sthCore::SUCCESS
    
}

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_outer_priority { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
    	return $::sth::sthCore::FAILURE
    }
    
    #Config VlanIfs
    set ::sth::Dhcp::DHCPHOSTOUTERVLANPRI($hostHandle) $switchValue
    
    return $::sth::sthCore::SUCCESS
    
}

###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id_outer_step (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id_outer_step
###
###This procedure implements the config command for Dhcp group switch vlan_id_outer_step.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id_outer_step (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_outer_step { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_outer_step: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Config VlanIfs
    set ::sth::Dhcp::DHCPHOSTOUTERVLANSTEP($hostHandle) $switchValue
    
    return $::sth::sthCore::SUCCESS
    
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id_count(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id_count
###
###This procedure implements the config command for Dhcp group switch vlan_id_count.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id_count (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_count { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_count: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Check encap
    set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)
    
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        set ::sth::Dhcp::DHCPHOSTINNERVLANCOUNT($hostHandle) $switchValue
    } else {
        set ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle) $switchValue
    }
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_vlan_id_outer_count (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch vlan_id_outer_count
###
###This procedure implements the config command for Dhcp group switch vlan_id_outer_count.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_vlan_id_outer_count (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_outer_count { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_outer_count: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    set ::sth::Dhcp::DHCPHOSTOUTERVLANCOUNT($hostHandle) $switchValue
    return $::sth::sthCore::SUCCESS
}


#for vlan_id_outer_repeat
proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_outer_repeat_count { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_outer_repeat: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    set ::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle) $switchValue
    return $::sth::sthCore::SUCCESS
}


#for vlan_id_repeat_count
proc ::sth::Dhcp::emulation_dhcp_group_config_vlan_id_repeat_count { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_vlan_id_repeat_count: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    #Check encap
    set encap $::sth::Dhcp::DHCPHOSTENCAP($hostHandle)
    
    if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan"} {
        set ::sth::Dhcp::DHCPHOSTINNERVLANREPEATCOUNT($hostHandle) $switchValue
    } else {
        set ::sth::Dhcp::DHCPHOSTOUTERVLANREPEATCOUNT($hostHandle) $switchValue
    }
    return $::sth::sthCore::SUCCESS
}




###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_qinq_incr_mode(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch qinq_incr_mode
###
###This procedure implements the config command for Dhcp group switch qinq_incr_mode.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_qinq_incr_mode(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_qinq_incr_mode { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {

    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "emulation_dhcp_group_config_qinq_incr_mode: Not able to get host handle from $handle: $eMsg" {}
    	return $::sth::sthCore::FAILURE
    }
    
    set ::sth::Dhcp::DHCPHOSTQINQINCRMODE($hostHandle) $switchValue
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_group_config_mac_addr (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar)
###\brief Config Processor for Dhcp group switch mac_addr
###
###This procedure implements the config command for Dhcp group switch mac_addr.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_mac_addr (str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, str handle, varRef cmdVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_mac_addr { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName  with value: $switchValue"
    
    #Fetch the switch/stc mapping information from the Data Structures.    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $_switchName stcattr]
    
	#Fetching the forward map
	#::sth::sthCore::log debug "Fetching the STC equivalent value for userinput:$switchValue if any"
    if {[catch {set stcAttrValue [::sth::sthCore::getFwdmap ::sth::Dhcp:: $_hltCmdName $_switchName $switchValue]} getStatus]} {
        set stcAttrValue $switchValue
    }
    
    #Get host handle
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "Internal error configuring $_switchName for $handle: $eMsg"
    	return $::sth::sthCore::FAILURE
    }
    
    # ignore ethernet configuration in ATM encapsulation
    #if {$::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle) == "dhcpoa"} {
    #    return $::sth::sthCore::SUCCESS
    #}
    
    #Get EthIIIf handle
    if {[catch {set ethHandle [::sth::sthCore::invoke stc::get $hostHandle -children-ethiiif]} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring $_switchName for $handle: $eMsg"
    	return $::sth::sthCore::FAILURE
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $ethHandle "-$stcAttr $switchValue"} eMsg]} {
        ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for switch -$_switchName: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn emulation_dhcp_group_config_encap (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar, str hltPortVar)
###\brief Process encap switch.
###
###This procedure implements processing of the encap switch.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The DhcpSessionBlock handle on which config needs to be done.
###\param[in] portHandleVar The DhcpPort handle which DhcpSessionBlock is associated with.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_group_config_encap (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar, str hltPortVar);
###

proc ::sth::Dhcp::emulation_dhcp_group_config_encap { encap protocol hltPort hostHandleVarName returnStringName cmdStateVarName returnHandleVarName } {

    upvar $hostHandleVarName hostHandle
    upvar $returnStringName returnKeyedList
    upvar $cmdStateVarName errOccured
    upvar $returnHandleVarName returnHandle
    
    set ethII_encap ""
    set atm_encap ""
    switch -exact -- $protocol {
        "dhcpoe" {
            set ethII_encap 1
            set atm_encap 0
        }
        "dhcpoeoa" {
            set ethII_encap 1
            set atm_encap 1
        }
        default {
            ::sth::sthCore::processError returnInfo "The value $protocol is not valid for the switch -protocol"
            return $::sth::sthCore::FAILURE
        }   
    }
        # TBC: dhcpoa is not supported by stc 3.30
        #"dhcpoa" {
        #    set ethII_encap 0
        #    set atm_encap 1
        #}
        
    switch -- $encap {
        ethernet_ii -
        ethernet_ii_vlan -
        ethernet_ii_qinq -
        ethernet_ii_mvlan {
            # dhcpoa does not support "ethernet_ii"
            if {$ethII_encap == 0} {
                ::sth::sthCore::processError returnInfo "The value $encap is not supported in encapsulation $protocol"
                return $::sth::sthCore::FAILURE
            }
        }
        vc_mux -
        llcsnap {
            # dhcpoe does not support "vc_mux" or "llcsnap"
            if {$atm_encap == 0} {
                ::sth::sthCore::processError returnInfo "The value $encap is not supported in encapsulation $protocol"
                return $::sth::sthCore::FAILURE
            }
        }
        SHA_NO_USER_INPUT {
            ::sth::sthCore::processError returnInfo "No value specified for the switch -encap"
            return $::sth::sthCore::FAILURE               
        }
        default {
            ::sth::sthCore::processError returnInfo "The value $encap is not valid for the switch -encap"
            return $::sth::sthCore::FAILURE
        }
    }

    set createNew 0
    if {$hostHandle == ""} {
        set createNew 1
    }
    
    #Create new Host, EthIIIF, Ipv4If under project if Host handle not given
    #Otherwise, we'll just modify existing host
    if {$createNew} {
        if {[catch {set hostHandle [::sth::sthCore::invoke stc::create Host -under $::sth::sthCore::GBLHNDMAP(project) ""]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating DHCP group: $createStatus"
            set errOccured 1
            return $::sth::sthCore::FAILURE
        }
        
        #Create new Ethernet II interface
        if {$ethII_encap} { 
            if {[catch {set ethiiResultIf [::sth::sthCore::invoke stc::create EthIIIf -under $hostHandle ""]} createStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating DHCP group: $createStatus"
                set errOccured 1
                return $::sth::sthCore::FAILURE
            }
        }
        #Create new ATM stack
            #add DHCPv4oEoA support , xiaozhi, 6/15/09
        if {$atm_encap} {
            if {$encap == "vc_mux"} {
                set atmCfg "-VcEncapsulation VC_MULTIPLEXED"
            } elseif {$encap == "llcsnap"} {
                set atmCfg "-VcEncapsulation LLC_ENCAPSULATED"
            } else {
                set atmCfg "-VcEncapsulation VC_MULTIPLEXED"
            }
            ::sth::sthCore::invoke stc::config $hostHandle "-devicecount $::sth::userArgsArray(num_sessions)"
            set atmResultIf [::sth::sthCore::invoke stc::create Aal5If -under $hostHandle $atmCfg]
            if {$protocol == "dhcpoeoa"} {
                if {[catch {::sth::sthCore::invoke stc::config $ethiiResultIf "-StackedOnEndpoint-targets $atmResultIf"} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "stc::config Failed: $eMsg"
                    return $::sth::sthCore::FAILURE
                }
            }
        }
    } else {
        #Get EthIIIf
        if {$ethII_encap} {
            if {[catch {set ethiiResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-EthIIIf]} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                return $::sth::sthCore::FAILURE
            }
            
           
        }
        #Get Aal5If
        if {$atm_encap} {
            set atmResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-aal5if]
        }
        #Get Ipv4If
        if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $hostHandle -children-Ipv4If]} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
            return $::sth::sthCore::FAILURE
        }
    }
    
    if {$ethII_encap} {
        #Create or get handle of outer VlanIf
        if {$encap == "ethernet_ii_vlan" || $encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan" } {
            if {![info exists ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)]} {
                if {[catch {set outerVlanHandle [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle "-StackedOnEndpoint-targets $ethiiResultIf"]} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                    return $::sth::sthCore::FAILURE
                }
                set ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle) $outerVlanHandle
            } else {
                set outerVlanHandle $::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)
            }
        }
        
        #Create or get handle of inner VlanIf
        if {$encap == "ethernet_ii_qinq" || $encap == "ethernet_ii_mvlan" } {
            if {![info exists ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)]} {
                if {[catch {set innerVlanHandle [::sth::sthCore::invoke stc::create VlanIf -under $hostHandle "-StackedOnEndpoint-targets $outerVlanHandle"]} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                    return $::sth::sthCore::FAILURE
                }
                set ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle) $innerVlanHandle
            } else {
                set innerVlanHandle $::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)
            }
        }
    }
    
    #Delete old VlanIfs (occurs when changing encap type)
    if {!$createNew} {
        if {$encap == "ethernet_ii"} {
            if {[info exists ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)]} {
                if {[catch {::sth::sthCore::invoke stc::delete $::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                    return $::sth::sthCore::FAILURE
                }
                catch {unset ::sth::Dhcp::DHCPHOSTOUTERVLANIF($hostHandle)}
            }
        }
        
        if {$encap == "ethernet_ii" || $encap == "ethernet_ii_vlan"} {
            if {[info exists ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)]} {
                if {[catch {::sth::sthCore::invoke stc::delete $::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                    return $::sth::sthCore::FAILURE
                }
                catch {unset ::sth::Dhcp::DHCPHOSTINNERVLANIF($hostHandle)}
            }
        }
            
            #Delete all extra qinq hosts
            if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]} {
                foreach handle $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) {
                    if {$handle != $hostHandle } {
                        if {[catch {::sth::Dhcp::deleteDhcpHost $handle returnKeyedList} eMsg]} {
                           ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $eMsg"
                           return $::sth::sthCore::FAILURE
                        }
                        
                        if {[catch {::sth::Dhcp::deleteHandleInHandleList $handle ::sth::Dhcp::DHCPHOSTS eMsg} eMsg ]} {	   
                            ::sth::sthCore::processError returnKeyedList "Error occured while deleting Dhcp group: $eMsg"
                            return $::sth::sthCore::FAILURE
                        }
                    }
                }
                catch {unset ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)}
            }
        
    }
    
    switch -- $encap {
        ethernet_ii {
            set stackedHandle $ethiiResultIf
        }
        ethernet_ii_vlan {
            set stackedHandle $outerVlanHandle
        }
        ethernet_ii_qinq {
            set stackedHandle $innerVlanHandle
        }
        ethernet_ii_mvlan {
            set stackedHandle $innerVlanHandle
        }
        vc_mux -
        llcsnap {
            if {$ethII_encap} {
                set stackedHandle $ethiiResultIf
            }
            # TBC: dhcpoa is not supported by stc 3.30
            #if {$protocol == "dhcpoa"} {
            #    set stackedHandle $atmResultIf
            #}
        }
    }
    
    if {$createNew} {
        #Create new IPv4 interface
        # We need to set the Gateway IP here (from the IPv4 interface that just so happens to be living
        # under the project (if it exists of course).
        set defaultIpv4 [lindex [::sth::sthCore::invoke stc::get $hltPort -children-ipv4if] 0]
        set gatewayIp "192.85.2.1"
        if {$defaultIpv4 != ""} {
            set gatewayIp [::sth::sthCore::invoke stc::get $defaultIpv4 -gateway]
        }
        if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::create Ipv4If -under $hostHandle "-StackedOnEndpoint-targets $stackedHandle -gateway $gatewayIp"]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $createStatus"
            set errOccured 1
            return $::sth::sthCore::FAILURE
        }
        
        #Config host
        if {[catch {::sth::sthCore::invoke stc::config $hostHandle "-AffiliationPort-targets $hltPort -TopLevelIf-targets $ipv4ResultIf -PrimaryIf-targets $ipv4ResultIf"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $configStatus"
            set errOccured 1
        } 
        
        #Create new DHCP block
        if {[catch {set returnHandle [::sth::sthCore::invoke stc::create Dhcpv4BlockConfig -under $hostHandle "-UsesIf-targets $ipv4ResultIf"]} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal error creating DHCP group: $createStatus"
            set errOccured 1
            return $::sth::sthCore::FAILURE
        }
        
    } else {
        #Modify Ipv4If
        if {[catch {::sth::sthCore::invoke stc::config [lindex $ipv4ResultIf 0] "-StackedOnEndpoint-targets $stackedHandle"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal error configuring Dhcp group: $configStatus"
            set errOccured 1
        }
    }
    
    set ::sth::Dhcp::DHCPHOSTENCAP($hostHandle) $encap
    set ::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle) $protocol
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processDhcpConfigCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic Dhcp Config Processor
###
###This procedure implements the generic config command. This command is used by all the switches with one on one mapping with the STC attributes.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###processDhcpConfigCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###
#{$switchValue} returnKeyedList $_hltCmdName $switchName $switchHandle

proc ::sth::Dhcp::processDhcpConfigCmd { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
          
    #This check will be done before this function is called. Thus this can be removed.
    if {[string equal $switchValue "SHA_NO_USER_INPUT"]} {
    	::sth::sthCore::processError returnInfo "No value specified for the switch -$switchName "
    	return $::sth::sthCore::FAILURE
    }

    #Fetch the switch/stc mapping information from the Data Structures.    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $switchName stcattr]
    
    #Fetching the forward map
    if {[catch {set stcAttrValue [::sth::sthCore::getFwdmap ::sth::Dhcp:: $_hltCmdName $switchName $switchValue]} getStatus]} {
        set stcAttrValue $switchValue
    }     
    #if {[catch {set iStatus [::sth::sthCore::invoke stc::config $handle -$stcAttr $stcAttrValue] } errMsg ]} {
	#    set cmdFailed 1  
	#} else {
    #    if {$iStatus != $::sth::sthCore::SUCCESS } {
    #        ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for the switch -$_switchName"
    #        set cmdFailed 1  
    #    } else {
    #        #::sth::sthCore::log debug "The switch:$_switchName was successfully set to $switchValue"
    #    }
    #}

    #Append attribute pair to doStcConfig cmd
    set cmd "${cmd} -$stcAttr $stcAttrValue"
    return $::sth::sthCore::SUCCESS

}


#DHCP 3.00 enhancement xiaozhi,liu
proc ::sth::Dhcp::processDhcpBlockInputArgs { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    
    variable processFlag
     
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd

    set stcAttrValue ""
    if {$processFlag($switchName) == "true"} {
        set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $switchName stcattr]
        if {[catch {set stcAttrValue [::sth::sthCore::getFwdmap ::sth::Dhcp:: $_hltCmdName $switchName $switchValue]} getStatus]} {
            set stcAttrValue $switchValue
        } 
        set cmd "${cmd} -$stcAttr $stcAttrValue"
        set processFlag($switchName) false
    }
    
    return $::sth::sthCore::SUCCESS
}

#DHCP 3.00 enhancement xiaozhi,liu
proc ::sth::Dhcp::modifyDhcpBlockConfigArgs { mynamespace mycmd switchArgs mySortedPriorityList dhcpHandle returnStringName } {
    
    set _OrigHltCmdName "emulation_dhcp_config"
    
    upvar $switchArgs userInputArgs
    upvar $mySortedPriorityList sortedPriorityList
    upvar $returnStringName returnKeyedList
    
    variable ::sth::Dhcp::dhcpBlockInputArgsList
    variable ::sth::Dhcp::dhcpBlockInputArgs
    variable ::sth::Dhcp::processFlag
    
    set dhcpSession ""
    
    set portHandle [::sth::sthCore::invoke stc::get $dhcpHandle -parent]
        
    set handle [::sth::sthCore::invoke stc::get $portHandle -AffiliationPort-sources]
        
    foreach hdl $handle {
        if {[string match -nocase "host*" $hdl]} {
            set dhcpBlockCfg [::sth::sthCore::invoke stc::get $hdl -children-Dhcpv4BlockConfig]
            
            if {[llength $dhcpBlockCfg] != 0} {
            
                set argname [array names processFlag]
                foreach name $argname {
                    set processFlag($name) true
                    keylset dhcpSession $name $name
                }
            
                set cmdResult [::sth::Dhcp::processConfigSwitches ::sth::Dhcp:: $_OrigHltCmdName dhcpBlockInputArgs \
                    dhcpSession $dhcpBlockCfg returnKeyedList] 
            }
        }
    }
        
}
###
#DHCP 3.00 enhancement
#
#Notes:
# 1) relay_agent_flag is required to be 1 when configuring circuit id;
# 2) parameter -circuit_id_suffix_count specifies the total count of circuit ids to generate,
#regardless of the setting of the -circuit_id_suffix_repeat.
# 3) using DHCP custom options to map circuit_id, notice that all other wildcards other than @$ are actually strings.
#     @$(n1,n2,n3,n4, n5),
#       $  - used as a variable-width arbitrary value : 
#       n1 - a variable-length hexadecimal value          
#       n2 - number of values, zero meaning limit is 32-bits
#       n3 - hexadecimal step value (default 1)
#       n4 - endianness, 0 = little endian, 1 = big endian, 2 = hexadecimal;
#       n5 - repeat count (default 0)
#
#Example:
#circuit_id_suffix = 0,circuit_id_suffix_count = 5  circuit_id_suffix_repeat = 1, circuit_id_suffix_step = 1
#This will generate the circuit_id sequence 0, 1, 2, 3, 4, 0, 1, 2, 3, 4
#
#Calling emulation_dhcp_group_config two times for the port above:
#First group:  dhcp_group_config -num_sessions is 2, then the 2 sessions will use the first two values (0,1) for the circuit id in first group. 
#Second group: dhcp_group_config -num_sessions is 8, then the 8 sessions will use the first five values and repeat three values
#              (0, 1, 2, 3, 4, 0, 1, 2) for the circuit id in the second group. 
#
#Author: xiaozhi,liu
###
proc ::sth::Dhcp::emulation_dhcp_config_circuit_id { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    variable processFlag
    variable dhcpBlockInputArgs
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    
    if {$switchName == "circuit_id"} {
        if {$processFlag($switchName) == "true"} {

            set suffixStart 0
            set suffixStep 1
            set suffixRepeat 0
            set suffixCount 1
            if {![info exists dhcpBlockInputArgs(circuit_id_suffix)] && ![info exists dhcpBlockInputArgs(circuit_id_suffix_step)] && ![info exists dhcpBlockInputArgs(circuit_id_suffix_count)]} {
                set circuitId $switchValue
            } else {
                if {[info exists dhcpBlockInputArgs(circuit_id_suffix)]} {
                    set suffixStart $dhcpBlockInputArgs(circuit_id_suffix)
                    
                    #if {[info exists dhcpBlockInputArgs(circuit_id_suffix_repeat)]} {
                    #    if {$dhcpBlockInputArgs(circuit_id_suffix_repeat) >= 1} {
                    #        set suffixRepeat [expr {$dhcpBlockInputArgs(circuit_id_suffix_repeat)-1}]  
                    #    }  
                    #}
                    if {[info exists dhcpBlockInputArgs(circuit_id_suffix_step)]} {
                        set suffixStep $dhcpBlockInputArgs(circuit_id_suffix_step)
                    }
                    if {[info exists dhcpBlockInputArgs(circuit_id_suffix_count)]} {
                        set suffixCount $dhcpBlockInputArgs(circuit_id_suffix_count)
                    }
                    set hexsuffixStart [format "%x" $suffixStart]
                    set circuitId "@\\\$($switchValue$hexsuffixStart,$suffixCount, $suffixStep,1,0)"
                    
                } else {
                    set circuitId "@\\\$($switchValue,$suffixCount,$suffixStep,1,0)"
                }
            }
            set cmd "${cmd} -EnableCircuitId true -CircuitId {$circuitId}"
            set processFlag($switchName) false
        } 
    }
    
    return $::sth::sthCore::SUCCESS
}

###
#DHCP 3.00 enhancement
#
#Notes:
#   1) relay_agent_flag is required to be 1 when configuring remote id;
#   2) The way to generate remeote id is similar to circuit id. See emulation_dhcp_config_circuit_id for reference.
#
#Author: xiaozhi,liu
###
proc ::sth::Dhcp::emulation_dhcp_config_remote_id { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    variable processFlag
    variable dhcpBlockInputArgs
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    if {$switchName == "remote_id"} {
        if {$processFlag($switchName) == "true"} {
            
            set suffixStart 0
            set suffixStep 1
            set suffixRepeat 0
            set suffixCount 1
            if {![info exists dhcpBlockInputArgs(remote_id_suffix)] && ![info exists dhcpBlockInputArgs(remote_id_suffix_step)] && ![info exists dhcpBlockInputArgs(remote_id_suffix_count)]} {
                set remoteId $switchValue
            } else {
                if {[info exists dhcpBlockInputArgs(remote_id_suffix)]} {
                    set suffixStart $dhcpBlockInputArgs(remote_id_suffix)
                    #if {[info exists dhcpBlockInputArgs(remote_id_suffix_repeat)]} {
                    #    if {$dhcpBlockInputArgs(remote_id_suffix_repeat) >= 1} {
                    #        set suffixRepeat [expr {$dhcpBlockInputArgs(remote_id_suffix_repeat)-1}]
                    #    }
                    #}
                    if {[info exists dhcpBlockInputArgs(remote_id_suffix_step)]} {
                        set suffixStep $dhcpBlockInputArgs(remote_id_suffix_step)
                    }
                    if {[info exists dhcpBlockInputArgs(remote_id_suffix_count)]} {
                        set suffixCount $dhcpBlockInputArgs(remote_id_suffix_count)
                    }
                    set hexsuffixStart [format "%x" $suffixStart]
                    set remoteId "@\\\$($switchValue$hexsuffixStart,$suffixCount,$suffixStep,1,0)"  
                } else {
                    set remoteId "@\\\$($switchValue,$suffixCount,$suffixStep,1,0)"
                }
            }
            set cmd "${cmd} -EnableRemoteId true -RemoteId {$remoteId}"
            set processFlag($switchName) false
        }

    }
    
    return $::sth::sthCore::SUCCESS
}

###
#DHCP 3.00 enhancement
#
#Notes:
#   1) Client id(option 61) is used by DHCP clients to specify their unique identifier.
#   DHCP servers use this value to index their database of address bindings.  
#   This value is expected to be unique for all clients in an administrative domain.
#   2) client_id_type is mandatory when configuring client_id.
#   3) The way to generate client id is similar to circuit id. See emulation_dhcp_config_circuit_id for reference.
#
#Author: xiaozhi,liu
###
proc ::sth::Dhcp::emulation_dhcp_config_client_id { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    variable processFlag
    variable dhcpBlockInputArgs
    
    upvar $returnInfoVarName returnKeyedList
    upvar $cmdVar cmd
    
    if {$switchName == "client_id"} {
        if {$processFlag($switchName) == "true"} {
            set suffixStart 0
            set suffixStep 1
            set suffixCount 1
            
            if {![info exists dhcpBlockInputArgs(client_id_type)]} {
                ::sth::sthCore::processError returnKeyedList "-client_id_type is mandatory when configuring -client_id" {}
                return -code error $returnKeyedList
            }
            set clientType $dhcpBlockInputArgs(client_id_type)
            # "0" specifies that the number should be padded on the left with zeroes instead of spaces.
            set hexclientType [format "%02x" $clientType]
            if {![info exists dhcpBlockInputArgs(client_id_suffix)] && ![info exists dhcpBlockInputArgs(client_id_suffix_step)] && ![info exists dhcpBlockInputArgs(client_id_suffix_count)]} {
                set clientId $switchValue
            } else {
                if {[info exists dhcpBlockInputArgs(client_id_suffix)]} {
                    set suffixStart $dhcpBlockInputArgs(client_id_suffix)
                        
                    if {[info exists dhcpBlockInputArgs(client_id_suffix_step)]} {
                        set suffixStep $dhcpBlockInputArgs(client_id_suffix_step)
                    }
                    if {[info exists dhcpBlockInputArgs(client_id_suffix_count)]} {
                        set suffixCount $dhcpBlockInputArgs(client_id_suffix_count)
                    }
                    
                    set hexsuffixStart [format "%x" $suffixStart]
                    set clientId "@\$($hexclientType$switchValue$hexsuffixStart,$suffixCount,$suffixStep,1,0)"  
                } else {
                    set clientId "@\$($hexclientType$switchValue,$suffixCount,$suffixStep,1,0)"
                }
            }
            set optionvalue "-OptionType 61 -EnableWildcards TRUE -HexValue TRUE -Payload {$clientId}"
            #create Dhcpv4MsgOption under Dhcpv4BlockConfig 
            set msgOptHandle [::sth::sthCore::invoke stc::create Dhcpv4MsgOption -under $handle]
            ::sth::sthCore::invoke stc::config $msgOptHandle $optionvalue
            set processFlag($switchName) false     
        }
    }
    
    return $::sth::sthCore::SUCCESS
}


######configure the client_id circuit_id and the remote_id in the same fucntion instead of using
#emulation_dhcp_config_client_id, emulation_dhcp_config_remote_id, and emulation_dhcp_config_circuit_id

###
# According to the Documentation Spirent TestCenter Automation Object Reference :
# CircuitId and RemotedId Attributes of Dhcpv4BlockConfig Object,Custom step setup in " @x(Start ,Count ,Step ,ZeroPadding ,Stutter) " format.
# Acturally ,To use " @$(Start ,Count ,Step ,ZeroPadding ,Stutter)" format to setup the custom iterator. 
#
# In emulation_dhcp_config_wildcard function：
# (circuit/remote)_id configues the circuit/remote ID sub-option of relay agent option.            
# (circuit/remote)_id_suffix defines the suffix to append to the circuit/remote ID. It is Equivalent to Start.  
# (circuit/remote)_id_suffix_step defines the increment used to generate circuit/remote_id_suffixes for emulated clients.It is Equivalent to Step. 
# (circuit/remote)_id_suffix_count specifies the number of circuit/remote_id_suffixes . It is Equivalent to Count. 
# (circuit/remote)_id_suffix_repeat specifies the number of times a circuit/remote_id_suffix should be repeated. It is Equivalent to Stutter. 
#
#
# Payload Attribute of Dhcpv4MsgOption Object , Custom step setup in " @x(Start ,Count ,Step ,ZeroPadding ,stutter) " format.
# client_id configues the client ID .            
# client_id_suffix defines the suffix to append to the client ID. It is Equivalent to Start.  
# client_id_suffix_step defines the increment used to generate client_id_suffixes for emulated clients. It is Equivalent to Step. 
# client_id_suffix_count specifies the number of client_id_suffixes . It is Equivalent to Count. 
# client_id_suffix_repeat specifies the number of times a client_id_suffix should be repeated. It is Equivalent to Stutter. 
# 
#Example:
# setup these parameters, circuit_id 100 , circuit_id_suffix 1 , circuit_id_suffix_step 1 , circuit_id_suffix_count 10 , circuit_id_suffix_repeat 0.
#Packets:
# Agent Circuit ID : 1001 ~ 100a
#
# setup these parameters, client_id_type 60, client_id 100 , client_id_suffix 1 , client_id_suffix_step 10 , 
#                         client_id_suffix_count 10 , client_id_suffix_repeat 0 .
#Packets:
# Option :(60) vendor class identifier : 101 ~ 110
##

proc ::sth::Dhcp::emulation_dhcp_config_wildcard { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    variable processFlag
    variable dhcpBlockInputArgs
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    
    if {$processFlag($switchName) == "true"} {
        set suffixStart 0
        set suffixStep 1
        set suffixRepeat 0
        set suffixCount 1
        if {![info exists dhcpBlockInputArgs($switchName\_suffix)] && ![info exists dhcpBlockInputArgs($switchName\_suffix_step)] && ![info exists dhcpBlockInputArgs($switchName\_suffix_count)]} {
            set switchValue $switchValue
        } else {
            if {[info exists dhcpBlockInputArgs($switchName\_suffix)]} {
                set suffixStart $dhcpBlockInputArgs($switchName\_suffix)
                if {[info exists dhcpBlockInputArgs($switchName\_suffix_repeat)]} {
                    if {$dhcpBlockInputArgs($switchName\_suffix_repeat) >= 1} {
                        set suffixRepeat [expr {$dhcpBlockInputArgs($switchName\_suffix_repeat)-1}]
                    }
                }
                if {[info exists dhcpBlockInputArgs($switchName\_suffix_step)]} {
                    set suffixStep $dhcpBlockInputArgs($switchName\_suffix_step)
                }
                if {[info exists dhcpBlockInputArgs($switchName\_suffix_count)]} {
                    set suffixCount $dhcpBlockInputArgs($switchName\_suffix_count)
                }
                set hexsuffixStart [format "%x" $suffixStart]
				switch $switchName {
				    "remote_id" {
				        set switchValue "@\\\$($switchValue$hexsuffixStart,$suffixCount, $suffixStep,1,$suffixRepeat)"}
					"circuit_id" {
					    set switchValue "@\\\$($switchValue$hexsuffixStart,$suffixCount, $suffixStep,1,$suffixRepeat)"}
					"client_id" {
					    set switchValue "@x($switchValue$hexsuffixStart,$suffixCount, $suffixStep,1,$suffixRepeat)"}	
				}		
#                set switchValue "@\\\$($switchValue$hexsuffixStart,$suffixCount, $suffixStep,1,$suffixRepeat)"

            }
        }
        if {$switchName == "remote_id"} {
            set cmd "${cmd} -EnableRemoteId true -RemoteId {$switchValue}"
        } elseif {$switchName == "circuit_id"} {
            set cmd "${cmd} -EnableCircuitId true -CircuitId {$switchValue}"
        } else {
            #client_id
            if {![info exists dhcpBlockInputArgs(client_id_type)]} {
                ::sth::sthCore::processError returnKeyedList "-client_id_type is mandatory when configuring -client_id" {}
                return -code error $returnKeyedList
            }
            set clientType $dhcpBlockInputArgs(client_id_type)
            set optionvalue "-OptionType $clientType -EnableWildcards TRUE -HexValue TRUE -Payload {$switchValue}"
            #create Dhcpv4MsgOption under Dhcpv4BlockConfig 
            set msgOptHandle [::sth::sthCore::invoke stc::create Dhcpv4MsgOption -under $handle]
            ::sth::sthCore::invoke stc::config $msgOptHandle $optionvalue  
        }
        set processFlag($switchName) false
    }

    
    
    return $::sth::sthCore::SUCCESS
}

#This proc is to create/modify dhcpv4 custom options.
proc ::sth::Dhcp::emulation_dhcp_config_msgoption { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } { 
     
    variable processFlag
    variable dhcpBlockInputArgs
    variable ::sth::Dhcp::userArgsArray
    upvar $returnInfoVarName returnKeyedList
    upvar $cmdVar cmd
        
    if {[string equal $processFlag($switchName) true]} {
        #setting default values if not providing externally from execution script.
        if {![info exists dhcpBlockInputArgs(option_value)]} {
            ::sth::sthCore::processError returnKeyedList "-option_value is mandatory when configuring dhcpv4 custom options" {}
            return -code error $returnKeyedList
        }
        if {![info exists dhcpBlockInputArgs(enable_wildcards)]} {
            set dhcpBlockInputArgs(enable_wildcards) "false"  
        }
        if {![info exists dhcpBlockInputArgs(string_as_hex_value)]} {
            set dhcpBlockInputArgs(string_as_hex_value) "false"
        }
        if {![info exists dhcpBlockInputArgs(remove_option)]} {
            set dhcpBlockInputArgs(remove_option) "false"
        }
        if {![info exists dhcpBlockInputArgs(include_in_message)]} {
            set dhcpBlockInputArgs(include_in_message) "both"
        }

        set option_value $dhcpBlockInputArgs(option_value)
        set optionvalue "-OptionType $option_value -EnableWildcards $dhcpBlockInputArgs(enable_wildcards) \
                        -HexValue $dhcpBlockInputArgs(string_as_hex_value) -Payload \"$dhcpBlockInputArgs(option_payload)\" \
                        -MsgType $dhcpBlockInputArgs(include_in_message) -Remove $dhcpBlockInputArgs(remove_option)"
                        
        #create Dhcpv4MsgOption under Dhcpv4BlockConfig 
        if {[string equal $::sth::Dhcp::userArgsArray(mode) "create"]} { 
            set msgOptHandle [::sth::sthCore::invoke stc::create Dhcpv4MsgOption -under $handle]
            ::sth::sthCore::invoke stc::config $msgOptHandle $optionvalue
        }
        if {[string equal $::sth::Dhcp::userArgsArray(mode) "modify"]} {
             set dhcpMsgHandle [::sth::sthCore::invoke stc::get $handle -children-Dhcpv4MsgOption]
            ::sth::sthCore::invoke stc::config $dhcpMsgHandle $optionvalue            
        }
            
        set processFlag($switchName) false
    } else {
        ::sth::sthCore::processError returnKeyedList "::sth::Dhcp::emulation_dhcp_config_msgoption \
                        -option_value is mandatory when configuring dhcpv4 custom options" {}
        return $returnKeyedList
    }
    
    return $::sth::sthCore::SUCCESS
}

###
#3.30 enhancement (xiaozhi,liu)
#
#Supporting "-gateway_addresses" and "-ipv4_gateway_address"
###
proc ::sth::Dhcp::emulation_dhcp_group_config_gateway { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd

    if {[info exists ::sth::Dhcp::userArgsArray(gateway_addresses)] && $::sth::Dhcp::userArgsArray(gateway_addresses) == 1} {
        set host [::sth::sthCore::invoke stc::get $handle -parent]
    
        set ipIf [lindex [::sth::sthCore::invoke stc::get $host -children-ipv4if] 0]
    
        ::sth::sthCore::invoke stc::config $ipIf "-Gateway $switchValue"
    }
    
    return $::sth::sthCore::SUCCESS
}

#for gateway_ipv4_addr_step
proc ::sth::Dhcp::emulation_dhcp_group_config_gateway_ipv4_addr_step { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
      
    if {[info exists ::sth::userArgsArray(gateway_ipv4_addr_step)]} {
        set host [::sth::sthCore::invoke stc::get $handle -parent]
    
        set ipIf [lindex [::sth::sthCore::invoke stc::get $host -children-ipv4if] 0]
    
        ::sth::sthCore::invoke stc::config $ipIf "-GatewayStep $switchValue"
    }
    
    return $::sth::sthCore::SUCCESS
}

###
# emulation_dhcp_group_config_atm_settings
#   configure ATM settings in dhcpoeoa protocol
#
# Author: xiaozhi
###

proc ::sth::Dhcp::emulation_dhcp_group_config_atm_settings { switchValue returnInfoVarName _hltCmdName _switchName handle cmdVar} {
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #Get host handle
    if {[catch {set status [::sth::Dhcp::getHostHandle $handle hostHandle]} eMsg] || !$status} {
        ::sth::sthCore::processError returnInfo "Internal error configuring $_switchName for $handle: $eMsg"
    	return $::sth::sthCore::FAILURE
    }
    
    if {$::sth::Dhcp::DHCPHOSTPROTOCOL($hostHandle) == "dhcpoe"} {
        return $::sth::sthCore::SUCCESS
    }
    
    #Get atm handle
    if {[catch {set atmHandle [::sth::sthCore::invoke stc::get $hostHandle -children-aal5if]} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal error configuring $_switchName for $handle: $eMsg"
    	return $::sth::sthCore::FAILURE
    }
    
    #validate vci_count and vpi_count
    if {[expr $::sth::userArgsArray(num_sessions) % $::sth::userArgsArray(vci_count) != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $::sth::userArgsArray(vci_count) is not valid for switch vci_count: It does not divide $::sth::userArgsArray(num_sessions)."
        return -code error $returnKeyedList
    }
    
    if {[expr $::sth::userArgsArray(num_sessions) % $::sth::userArgsArray(vpi_count) != 0]} {
        ::sth::sthCore::processError returnKeyedList "The value $::sth::userArgsArray(vpi_count) is not valid for switch vpi_count: It does not divide $::sth::userArgsArray(num_sessions)."
        return -code error $returnKeyedList
    }
    
    set atmConfig ""
    if {![info exists ::sth::userArgsArray(pvc_incr_mode)]} { set ::sth::userArgsArray(pvc_incr_mode) "vci" }
    switch -- $::sth::userArgsArray(pvc_incr_mode) {
        "vci" {
            if {$_switchName == "vci_count"} {
                set atmConfig "-VciRecycleCount $switchValue"
            } elseif {$_switchName == "vpi_count"} {
                if {[expr $::sth::userArgsArray(vci_count)-1] >= 0} {
                    set vpiRepeat [expr $::sth::userArgsArray(vci_count)-1]
                } else {
                    set vpiRepeat 0
                }
                set atmConfig "-VpiRepeatCount $vpiRepeat -IfRecycleCount $::sth::userArgsArray(vpi_count)"
            } else {
                set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $_switchName stcattr]
                set atmConfig "-$stcAttr $switchValue"
            }
        }
        "vpi" {
            if {$_switchName == "vci_count"} {
                if {[expr $::sth::userArgsArray(vpi_count)-1] >= 0} {
                    set vciRepeat [expr $::sth::userArgsArray(vpi_count)-1]
                } else {
                    set vciRepeat 0
                }
                set atmConfig "-VciRepeatCount $vciRepeat -VciRecycleCount $::sth::userArgsArray(vci_count)"
            } elseif {$_switchName == "vpi_count"} {
                set atmConfig "-IfRecycleCount $::sth::userArgsArray(vpi_count)"
            } else {
                set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $_switchName stcattr]
                set atmConfig "-$stcAttr $switchValue"
            }
        }
        "both" {
            set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $_switchName stcattr]
            set atmConfig "-$stcAttr $switchValue"
        } 
        default {
            ::sth::sthCore::processError returnKeyedList "Error: Unknown pvc_incr_mode $userArgsArray(pvc_incr_mode)." {}
            return $returnKeyedList
        }
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $atmHandle "$atmConfig"} eMsg]} {
        ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for switch -$_switchName: $eMsg"
        return $::sth::sthCore::FAILURE
    }
     
    return $::sth::sthCore::SUCCESS
}

proc ::sth::Dhcp::emulation_dhcp_group_config_opt_list { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
    
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
    
    #::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName  with value: $switchValue"
      
    #This check will be done before this function is called. Thus this can be removed.
    if {[string equal $switchValue "SHA_NO_USER_INPUT"]} {
    	::sth::sthCore::processError returnInfo "No value specified for the switch -$switchName "
    	return $::sth::sthCore::FAILURE
    }

    #::sth::sthCore::log debug "Configuring the switch:$_switchName to value:$switchValue"

    #Fetch the switch/stc mapping information from the Data Structures.    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $_hltCmdName $switchName stcattr]
    
	#Fetching the forward map
	#::sth::sthCore::log debug "Fetching the STC equivalent value for userinput:$switchValue if any"
    if {[catch {set stcAttrValue [::sth::sthCore::getFwdmap ::sth::Dhcp:: $_hltCmdName $switchName $switchValue]} getStatus]} {
        set stcAttrValue $switchValue
    } 
	#::sth::sthCore::log debug "The STC equivalent value for userinput:$switchValue is $stcAttrValue"
    
    #if {[catch {set iStatus [::sth::sthCore::invoke stc::config $handle -$stcAttr $stcAttrValue] } errMsg ]} {
	#    set cmdFailed 1  
	#} else {
    #    if {$iStatus != $::sth::sthCore::SUCCESS } {
    #        ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for the switch -$_switchName"
    #        set cmdFailed 1  
    #    } else {
    #        #::sth::sthCore::log debug "The switch:$_switchName was successfully set to $switchValue"
    #    }
    #}
    
    if {[llength $stcAttrValue] == 1} {
        set stcAttrValue [lindex $stcAttrValue 0]
        set value_len [string length $stcAttrValue]
        if {$value_len > 2} {
            # Check if length is even
            if {[expr $value_len % 2] != 0} {
                ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for the switch -opt_list"
                return $::sth::sthCore::FAILURE
            }
            
            set substring [string range $stcAttrValue 0 1]
            if {![string compare $substring "0x"] || ![string compare $substring "0X"]} {
                set newValue ""
                for {set i 2} {$i < $value_len} {incr i 2} {
                    set substring [string range $stcAttrValue $i [expr $i + 1]]
                    if {[catch {lappend newValue [format "%u" "0x$substring"]} eMsg]} {
                        ::sth::sthCore::processError returnInfo "The value $switchValue is not valid for the switch -opt_list: $eMsg"
                        return $::sth::sthCore::FAILURE
                    }
                }
                set stcAttrValue $newValue
            }
        }
    }
    #check the option whether includes in [ 1 3 6 15 33 44 46 47 51 54 58 59]
    foreach optVal $stcAttrValue {
        switch -- $optVal {
            1 -
            3 -
            6 -
            15 -
            33 -
            44 -
            46 -
            47 -
            51 -
            54 -
            58 -
            59 {
                }
            default {
                ::sth::sthCore::processError returnInfo "The opt list value must be in 1|3|6|15|33|44|46|47|51|54|58|59"  
                return $::sth::sthCore::FAILURE
            }
        }
    }
    #Append attribute pair to doStcConfig cmd
    set cmd "${cmd} -$stcAttr \{$stcAttrValue\}";
    return $::sth::sthCore::SUCCESS

    #if {[::info exists cmdFailed]} {
    # 	return $::sth::sthCore::FAILURE
    #} else {
        #::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
    	#return $::sth::sthCore::SUCCESS
    #}

}


###/*! \ingroup switchprocfuncs
###\fn emulation_dhcp_config_msg_timeout (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Config Processor for Dhcp switch msg_timeout
###
###This procedure implements the config command for Dhcp switch msg_timeout.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the switch
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\warning None
###\author Mark Menor
###*/
###
###emulation_dhcp_config_msg_timeout (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::emulation_dhcp_config_msg_timeout { switchValue returnInfoVarName _hltCmdName switchName handle cmdVar } {
  
    upvar $returnInfoVarName returnInfo
    upvar $cmdVar cmd
  
    #Convert switchValue from ms to sec
    if {[expr $switchValue % 1000] != 0} {
    	::sth::sthCore::processError returnInfo "Invalid value was specified: value of switch -msg_timeout can not be converted to unit of second"
    	return $::sth::sthCore::FAILURE
    }
    set switchValue [expr $switchValue / 1000]
    
	set cmdResult [::sth::Dhcp::processDhcpConfigCmd $switchValue returnInfo $_hltCmdName $switchName $handle cmd]

    return $cmdResult
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processDHCPGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic DHCP Get Processor
###
###This procedure implements the generic get command for DHCP. This command is used by all the keys with one on one mapping with the STC attributes. In the args, wherever it says switch, it is supposed to mean key
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processDHCPGetCmd { returnInfoVarName hltCmdName keyName handle } {
    
    upvar $returnInfoVarName returnInfo
    set getValueVar ""

    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $hltCmdName $keyName stcattr]

    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $handle -$stcAttr]} getStatus]} {
        ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $getStatus"
        return $::sth::sthCore::FAILURE
    } else {
        #::sth::sthCore::log debug "Value of STC attribute:$stcAttr from handle:$handle successfully fetched"
        set mappedValue $getValueVar
        
        #::sth::sthCore::GetRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
        #::sth::sthCore::GetReturnKeyRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
        #::sth::sthCore::log debug "Converted value:$getValueVar to HLT equivalent:$mappedValue"
        #@TODO: Add the general encoding function as per requirement
        keylset returnInfo $keyName "$mappedValue"       
    	return $::sth::sthCore::SUCCESS
    }
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processUnsprtDHCPGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic DHCP Get Processor
###
###This procedure implements the generic get command for DHCP ports. This command is used by all the unsupported aggregate keys.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processUnsprtDHCPCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processUnsprtDHCPGetCmd { returnInfoVarName hltCmdName keyName handle } {
    
    upvar $returnInfoVarName returnInfo

    keylset returnInfo $keyName "-"        
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processDHCPGroupGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic DHCP Get Processor
###
###This procedure implements the generic get command for DHCP sessions/groups. This command is used by all the keys with one on one mapping with the STC attributes. In the args, wherever it says switch, it is supposed to mean key
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processDHCPGroupCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processDHCPGroupGetCmd { returnInfoVarName hltCmdName keyName handle } {

    upvar $returnInfoVarName returnInfo
    set getValueVar ""
    set resultType "Dhcpv4BlockResults"

    if {[regexp -nocase "dhcpv4sessionresults" $handle]} {
        set resultType "Dhcpv4SessionResults"
    } 
    
    #Get parent Dhcpv4BlockConfig handle, host handle
    if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $handle -parent]} getStatus]} {
        ::sth::sthCore::processError returnInfo "Internal error getting stats: $getStatus"
        return $::sth::sthCore::FAILURE
    }
    if {[catch {set hostHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -parent]} getStatus]} {
        ::sth::sthCore::processError returnInfo "Internal error getting stats: $getStatus"
        return $::sth::sthCore::FAILURE
    }
    
    set stcAttr [::sth::sthCore::getswitchprop ::sth::Dhcp:: $hltCmdName $keyName stcattr]
    
    #Get encap to determine if special QinQ processing is needed
    if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)] && ($keyName != "elapsed_time")} {
        set totalValue 0
        foreach subHostHandle $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle) {
            #Get Dhcpv4BlockConfig and results handles
            if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $subHostHandle -children-Dhcpv4BlockConfig]} getStatus]} {
                ::sth::sthCore::processError returnInfo "Internal error getting stats: $getStatus"
                return $::sth::sthCore::FAILURE
            }
            if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -children-$resultType]} getStatus]} {
                ::sth::sthCore::processError returnInfo "Internal error getting stats: $getStatus"
                return $::sth::sthCore::FAILURE
            }
            
            #Grab and sum values
            if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $dhcpResultsHandle -$stcAttr]} getStatus]} {
                ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $getStatus"
                return $::sth::sthCore::FAILURE
            } else {
                #::sth::sthCore::log debug "Value of STC attribute:$stcAttr from handle:$handle successfully fetched"
                set mappedValue $getValueVar
                
                #::sth::sthCore::GetRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
                #::sth::sthCore::GetReturnKeyRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
                #::sth::sthCore::log debug "Converted value:$getValueVar to HLT equivalent:$mappedValue"
                #@TODO: Add the general encoding function as per requirement
                
                #incr totalValue $mappedValue
                set totalValue [expr $totalValue + $mappedValue]
            }
        }
        
        #Take average value for these stats
        if {($keyName == "bind_rate") || ($keyName == "attempt_rate")} {
            set numGroups [llength $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($hostHandle)]
            set totalValue [expr $totalValue / $numGroups]
        }
        
        if {[regexp -nocase "dhcpv4sessionresults" $handle]} {
            keylset returnInfo group.$dhcpBlkHandle.$::sth::Dhcp::session_index.$keyName "$totalValue"
        } else {
            keylset returnInfo group.$dhcpBlkHandle.$keyName "$totalValue"
        }
        return $::sth::sthCore::SUCCESS
    
    } else {
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $handle -$stcAttr]} getStatus]} {
            ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $getStatus"
            return $::sth::sthCore::FAILURE
        } else {
            #::sth::sthCore::log debug "Value of STC attribute:$stcAttr from handle:$handle successfully fetched"
            set mappedValue $getValueVar
            
            #::sth::sthCore::GetRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
            #::sth::sthCore::GetReturnKeyRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
            #::sth::sthCore::log debug "Converted value:$getValueVar to HLT equivalent:$mappedValue"
            #@TODO: Add the general encoding function as per requirement
            if {[regexp -nocase "dhcpv4sessionresults" $handle]} {
                keylset returnInfo group.$dhcpBlkHandle.$::sth::Dhcp::session_index.$keyName "$mappedValue"
            } else {
                keylset returnInfo group.$dhcpBlkHandle.$keyName "$mappedValue"
            }
            return $::sth::sthCore::SUCCESS
        }
    }
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processUnsprtDHCPGroupGetCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief Generic DHCP Get Processor
###
###This procedure implements the generic get command for DHCP sessions/groups. This command is used by all the unsupported group keys.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processUnsprtDHCPGroupCmd (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processUnsprtDHCPGroupGetCmd { returnInfoVarName hltCmdName keyName handle } {

    upvar $returnInfoVarName returnInfo
    
    #Get parent Dhcpv4BlockConfig handle, host handle
    if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $handle -parent]} getStatus]} {
        ::sth::sthCore::processError returnInfo "Internal error getting stats: $getStatus"
        return $::sth::sthCore::FAILURE
    }

    keylset returnInfo group.$dhcpBlkHandle.$keyName "-"       
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processDHCPGetElapsedTime (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief DHCP Get Processor of elapsed_time
###
###This procedure implements the get command of elapsed_time for DHCP.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processDHCPGetElapsedTime (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processDHCPGetElapsedTime { returnInfoVarName hltCmdName keyName handle } {
    
    upvar $returnInfoVarName returnInfo
    set getValueVar ""

    if {[catch {set dhcpPort [::sth::sthCore::invoke stc::get $handle -parent]} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #set dhcpPort $handle

    set handleList $::sth::Dhcp::DHCPHOSTS($dhcpPort)
    set maxElapsedTime 0
    
    foreach handle $handleList {
        if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $handle -children-Dhcpv4BlockConfig]} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -children-Dhcpv4BlockResults]} eMsg]} {
            ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
            return $::sth::sthCore::FAILURE
        }
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $dhcpResultsHandle -ElapsedTime]} getStatus]} {
            ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $getStatus"
            return $::sth::sthCore::FAILURE
        }
        
        #::sth::sthCore::log debug "Value of STC attribute:$switch2StcMapInfo(stcattr) from handle:$handleVar successfully fetched"
        set mappedValue ""
        set mappedValue $getValueVar
        
        #::sth::sthCore::GetRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
        #::sth::sthCore::GetReturnKeyRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
        #::sth::sthCore::log debug "Converted value:$getValueVar to HLT equivalent:$mappedValue"
        if {$mappedValue > $maxElapsedTime} {
            set maxElapsedTime $mappedValue
        }
    }
    
    keylset returnInfo $keyName "$maxElapsedTime"        
    return $::sth::sthCore::SUCCESS
}


###/*! \ingroup dhcpswitchprocfuncs
###\fn processDHCPGetCurrentlyAttempting (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar)
###\brief DHCP Get Processor of elapsed_time
###
###This procedure implements the get command of currently_attempting for DHCP.
###
###\param[in] switchValue Contains the user input for this switch
###\param[in] sw2ValArrayName Array which contains the switch,value pairs.
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\param[in,out] sw2OutArrayName Contains the output for the previously processed switches.
###\param[in] switch2StcMapInfoName Contains the different attributes for the key
###\param[in] handleVar The handle on which config needs to be done. Currently this will be name of the switch whose input value is an handle.
###\return _INT_SHA_CMD_FAIL or _INT_SHA_CMD_PASS
###
###\todo Merge this with the generic get cmd.
###\warning None
###\author Mark Menor
###*/
###
###processDHCPGetCurrentlyAttempting (str switchValue, array sw2ValArrayName, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName, array sw2OutArrayName, array switch2StcMapInfoName, str handleVar);
###

proc ::sth::Dhcp::processDHCPGetCurrentlyAttempting { returnInfoVarName hltCmdName keyName handle } {
    
    upvar $returnInfoVarName returnInfo
    set getValueVar ""
    
    if {[catch {set dhcpPort [::sth::sthCore::invoke stc::get $handle -parent]} eMsg]} {
        ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
        return $::sth::sthCore::FAILURE
    }
    
    #set dhcpPort $handle

    set handleList $::sth::Dhcp::DHCPHOSTS($dhcpPort)
    set currAttempt 0
    
    foreach handle $handleList {
        if {[info exists ::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($handle)]} {
            set subHostHandleList $::sth::Dhcp::DHCPHOSTQINQSUBHOSTS($handle)
        } else {
            set subHostHandleList $handle
        }
        
        foreach subHostHandle $subHostHandleList {
            if {[catch {set dhcpBlkHandle [::sth::sthCore::invoke stc::get $subHostHandle -children-Dhcpv4BlockConfig]} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
                return $::sth::sthCore::FAILURE
            }
        if {[catch {set dhcpResultsHandle [::sth::sthCore::invoke stc::get $dhcpBlkHandle -children-Dhcpv4BlockResults]} eMsg]} {
                ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $eMsg"
                return $::sth::sthCore::FAILURE
            }
            if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $dhcpResultsHandle -CurrentAttemptCount]} getStatus]} {
                ::sth::sthCore::processError returnInfo "Internal Command Error while fetching value of $keyName: $getStatus"
                return $::sth::sthCore::FAILURE
            }
            
            #::sth::sthCore::log debug "Value of STC attribute:$switch2StcMapInfo(stcattr) from handle:$handleVar successfully fetched"
            set mappedValue ""
            set mappedValue $getValueVar
            
            #::sth::sthCore::GetRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
            #::sth::sthCore::GetReturnKeyRMapInfoFromTable $_hltCmdName $_switchName mappedValue $getValueVar
            #::sth::sthCore::log debug "Converted value:$getValueVar to HLT equivalent:$mappedValue"
            incr currAttempt $mappedValue
        }
    }
    
    keylset returnInfo $keyName "$currAttempt"      
    return $::sth::sthCore::SUCCESS
}



###}; //ending for namespace comment for doc
