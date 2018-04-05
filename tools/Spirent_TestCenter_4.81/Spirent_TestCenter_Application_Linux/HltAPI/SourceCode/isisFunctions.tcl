# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

###/*! \file IsIsFunctions.tcl
###    \brief Procedure for ISIS Api
###    
###    This file contains the helper utilities and the special switch processing functions for the ISIS Api.
###*/
### namespace IsIs {

package require Tclx
###/*! \file IsIs.tcl
###    \brief Sub Commands for ISIS
###    
###    This file contains the sub commands for IsIs Api which will execute the isis commands. This sub commands will be directly at the next level of the main command.
###*/


###/*! \namespace IsIs
###\brief IsIs Api
###
###This namespace contains the implementation for the IsIs Api

###*/
### namespace IsIs {

namespace eval ::sth::IsIs:: {
### Initialize boolean used for result subscription
        set createResultQuery 0

### store the handler for IsisLspGenParams
        set IsisLspGenParams_Handler 0

### Also, we need an array to keep the ip version for each LSP.
        array set ISISLSPIPVER {}
        
        
### This array stores the handle value used only in our Tcl code,
### which is the handle value of IsisIPRoute (for stub or external
### in the emulation_isis_topology_router_config). Since it can be 
### either IPv4, IPv6 or IPv4_6 (which is not supported in stc), we 
### create an array to store it. In this array, we have:

### Handle: I would define it as IsIsIpRoute***. It accumulates 
### each time a new handle is created.
### Parent LSP: The handle of its parent LSP
### IP version: the IP version of the route
### IPv4 route handle: the handle of object Ipv4IsisRoutesConfig
### Ipv6 route handle: the handle of object Ipv6IsisRoutesConfig

        array set ISISROUTEHNDLIST {}

### And another array which holds the values of switches to be set
        array set userArgsArray {}    


### Add this array to save much time: an array that keeps all the 
### neighbor LSPs of each LSP

        array set ISISLSPNEIGHBORLIST {}
### Unfortunately I found that it is impossible to get the largest 
### number from an array directly, therefore, this global variable 
### is to store the latest isisroutehandle number.
        set ISISROUTECOUNT 0
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_create (str args)
###\brief Process \em -mode switch with value \em enable for emulation_isis_config cmd
###
###This procedure execute the emulation_isis_config command when the mode is create. It will create isis sessions based on the \em -count switch.
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\return updatedKeyedList with isis handles
###
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
###emulation_isis_config_create (str args);
###

proc ::sth::IsIs::emulation_isis_config_create { returnKeyedListVarName cmdStatusVarName } {
        ::sth::sthCore::log debug "Excuting Internal Sub command for: emulation_isis_config {emulation_isis_config_create}"
        
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable ::sth::IsIs::userArgsArray
        variable ::sth::IsIs::useDefaultSystemId
        variable ::sth::sthCore::bfd_available_ipaddr
        
        upvar 1 $returnKeyedListVarName returnKeyedList
        upvar 1 $cmdStatusVarName cmdState

        # check if the port_handle value is valid
        if {[info exists userArgsArray(port_handle)]} {
                # validate the port_handle
                set portHandle $userArgsArray(port_handle)
                set msg ""
                if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                        ::sth::sthCore::processError returnKeyedList "The port_handle $portHandle is invalid." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                }
                
                ## Initiate default value
                if {![info exists userArgsArray(te_router_id)]} { set userArgsArray(te_router_id) 192.0.0.1}
                if {![info exists userArgsArray(router_id)]} { set userArgsArray(router_id) 192.0.0.1}
                #if {![info exists userArgsArray(mac_address_start)]} { set userArgsArray(mac_address_start) 00:10:94:00:00:02}
                ##auto aggsin the unique mac addr               
                if {![info exists userArgsArray(mac_address_start)]} {
                    set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
                    set userArgsArray(mac_address_start) [::sth::sthCore::invoke stc::get $addrOption -NextMac]
                }
                if {![info exists userArgsArray(gateway_ipv6_addr)]} { set userArgsArray(gateway_ipv6_addr) 2000::1}
                if {![info exists userArgsArray(intf_ipv6_addr)]} { set userArgsArray(intf_ipv6_addr) 2000::2}
                if {![info exists userArgsArray(gateway_ip_addr)]} { set userArgsArray(gateway_ip_addr) 192.85.1.1}
                if {![info exists userArgsArray(intf_ip_addr)]} { set userArgsArray(intf_ip_addr) 192.85.1.2}
                
                #If "vlan" is not explicitly set, enable "vlan" if any vlan arguments configured
                set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
                if {![info exists userArgsArray(vlan)]} {
                        if {$vlanOptFound} {
                                set userArgsArray(vlan) 1
                        } else {
                                set userArgsArray(vlan) 0
                        }
                }

                #If "atm_encapsulation" is not explicitly set, enable "atm_encapsulation" if any atm arguments configured 
                if {![info exists userArgsArray(atm_encapsulation)]} {
                    if {[info exists userArgsArray(vci)] || [info exist userArgsArray(vpi)]} { set userArgsArray(atm_encapsulation) 1}
                } else {
                    if {![info exist userArgsArray(vci)]} {set userArgsArray(vci) 100}
                    if {![info exist userArgsArray(vpi)]} {set userArgsArray(vpi) 100}
                }
                ## end 
                
                set rtrHdlList {}
                set lspHdlList {}
                #Process and create the ISISSessions for number of counts specified by user.
                for {set i 0} {$i < $userArgsArray(count)} {incr i} {
                    ::sth::sthCore::log info "Creating and configuring ISISSession number:$i."         
                    #process the user input and set the value of switches accordingly.        
                        if {$i > 0} {
                                ::sth::sthCore::log info "Updating values of switches, if required, based on the step input to create ISISSession number:$i."
                                
                                # update mac address
                                set ipVersion $userArgsArray(ip_version)    
                                switch -exact -- $ipVersion {
                                        4 {
                                                set ipAttrList {intf_ip_addr_step intf_ip_addr 4 gateway_ip_addr_step gateway_ip_addr 4}
                                        }
                                        6 {
                                                set ipAttrList {intf_ipv6_addr_step intf_ipv6_addr 6 gateway_ipv6_addr_step gateway_ipv6_addr 6}
                                        }
                                        4_6 {
                                                set ipAttrList {intf_ip_addr_step intf_ip_addr 4 intf_ipv6_addr_step intf_ipv6_addr 6 gateway_ip_addr_step gateway_ip_addr 4 gateway_ipv6_addr_step gateway_ipv6_addr 6}
                                        }
                                }
                                foreach {stepVal addr ipver} $ipAttrList {
                                        ::sth::sthCore::log info "Updating interface address for ipVersion:$ipver for ISISSession number:$i."
                                        set newIpAddress [::sth::sthCore::updateIpAddress $ipver $::sth::IsIs::userArgsArray($addr) $::sth::IsIs::userArgsArray($stepVal) 1]
                                        ::sth::sthCore::log info "ISISSession:$i The new Ipv$ipver Value for $addr is $newIpAddress."
                                        set userArgsArray($addr) $newIpAddress
                                }
                
                                # update mac address
                                ::sth::sthCore::log info "Updating the mac address for ISISSession number: $i"
                                set srcMac [::sth::sthCore::macStep $userArgsArray(mac_address_start) 00:00:00:00:00:01 1]
                                ::sth::sthCore::log info "ISISSession:$i The new value of mac_address_start is $srcMac."
                                ##auto aggsin the unique mac addr
                                if {$i == [expr $userArgsArray(count) -1]} {
                                     set nextMac [::sth::sthCore::macStep $srcMac "00:00:00:00:00:01" 1]
                                     set addrOption [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-DeviceAddrOptions]
                                     ::sth::sthCore::invoke stc::config $addrOption "-NextMac $nextMac"
                                }
                                set userArgsArray(mac_address_start) $srcMac
                                
                                #update router id
                                ::sth::sthCore::log info "Updating the router id for ISISSession number: $i"
                                set newRouterId [::sth::sthCore::updateIpAddress 4 $userArgsArray(router_id) $userArgsArray(router_id_step) 1]
                                ::sth::sthCore::log info "ISISSession:$i The new value of $addr is $newRouterId."
                                set userArgsArray(router_id) $newRouterId
                                
                                #update system id
                                set step [format "%012x" $userArgsArray(system_id_step)]
                                set newSystemId [::sth::IsIs::stepHexValue $userArgsArray(system_id) $step 1]
                                ::sth::sthCore::log info "ISISSession:$i The new value of System ID is $newSystemId."
                                set userArgsArray(system_id) $newSystemId
                                
                                #update the vlan_id and vlan_outer_id
                                if {$userArgsArray(vlan) == 1} {
                                        if {[info exists userArgsArray(vlan_id)]} {
                                                if {[string equal $userArgsArray(vlan_id_mode) "increment"]} {
                                                        set userArgsArray(vlan_id) [expr $userArgsArray(vlan_id)  + $userArgsArray(vlan_id_step) ]
                                                }
                                        }
                                        if {[info exists userArgsArray(vlan_outer_id)]} {
                                                if {[string equal $userArgsArray(vlan_outer_id_mode) "increment"]} {
                                                        set userArgsArray(vlan_outer_id) [expr $userArgsArray(vlan_outer_id)  + $userArgsArray(vlan_outer_id_step) ]
                                                } 
                                        }
                                }
                    
                                #add for ATM. update the vpi and vci
                                if {[info exist userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} { 
                                        set userArgsArray(vpi) [expr {$userArgsArray(vpi)+ $userArgsArray(vpi_step)}]
                                        set userArgsArray(vci) [expr {$userArgsArray(vci)+ $userArgsArray(vci_step)}]
                                }
                 
                                #update te router id
                                set newTeRouterId [::sth::sthCore::updateIpAddress 4 $userArgsArray(te_router_id) $userArgsArray(te_router_id_step) 1]
                                set userArgsArray(te_router_id) $newTeRouterId
                        }
            
                        #Execute the createConfigStartIsIsSession cmd and check result.
                        set cmdFailed 1
                        set sessInfo [::sth::IsIs::createConfigStartIsIsSession returnKeyedList cmdFailed $i]
                        foreach {rtrHdl lspHdl} $sessInfo {
                                lappend rtrHdlList $rtrHdl
                                if {[llength $lspHdl]} {
                                lappend lspHdlList $lspHdl
                                }
                        }
                        if {$cmdFailed} {
                                ::sth::sthCore::processError returnKeyedList "Error occured while creating/configuring the ISISSession number $i : $returnKeyedList" {}
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                ::sth::sthCore::log info "Successfully created/configured/started the ISISSession number {$i} $returnKeyedList "
                        }
                }
        } elseif {[info exists userArgsArray(handle)]} {
                set rtrHdlList $userArgsArray(handle)
                set lspHdlList {}
                #puts "Please be noted ISIS will be created in $userArgsArray(handle)"
                foreach hname {intf_ip_addr intf_ip_prefix_length gateway_ip_addr intf_ipv6_addr gateway_ipv6_addr intf_ipv6_prefix_length mac_address_start router_id \
                                                vci vpi vlan_cfi vlan_id  vlan_user_priority tunnel_handle atm_encapsulation  vlan_outer_id vlan_outer_user_priority} {
                        if {[info exists userArgsArray($hname)]} {
                                unset userArgsArray($hname)
                        }
                }
                #Execute the createConfigStartIsIsSession cmd and check result.
                set rtrHandles $userArgsArray(handle)
                set idx 0
                foreach rtrHandle $rtrHandles {
                        if {[::sth::sthCore::invoke stc::get $rtrHandle -children-IsIsRouterConfig] != ""} {
                                ::sth::sthCore::processError returnKeyedList "$rtrHandle already has IS-IS enable" {}
                                return $::sth::sthCore::FAILURE
                        }
                        set userArgsArray(handle) $rtrHandle
                        if {[set ipv6If [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-ipv6if]] != ""} {
                                set userArgsArray(ip_version) 6
                                if {[set ipv6If [::sth::sthCore::invoke stc::get $userArgsArray(handle) -children-ipv4if]] != ""} {
                                        set userArgsArray(ip_version) 4_6
                                }
                        } else {
                                set userArgsArray(ip_version) 4
                        }
                        set cmdFailed 1
                        set sessInfo [::sth::IsIs::createConfigStartIsIsSession returnKeyedList cmdFailed $idx]
                        if {$cmdFailed} {
                                ::sth::sthCore::processError returnKeyedList "Error occured while creating/configuring the ISISSession in $userArgsArray(handle): $returnKeyedList" {}
                                set cmdState $FAILURE
                                return $returnKeyedList 
                        } else {
                                ::sth::sthCore::log info "Successfully created/configured/started the ISISSession in $userArgsArray(handle) $returnKeyedList "
                        }
                        
                        foreach {rtrHdl lspHdl} $sessInfo {
                                if {[llength $lspHdl]} {
                                lappend lspHdlList $lspHdl
                                }
                        }
                        #update system id
                        set step [format "%012x" $userArgsArray(system_id_step)]
                        set newSystemId [::sth::IsIs::stepHexValue $userArgsArray(system_id) $step 1]
                        set userArgsArray(system_id) $newSystemId
                        incr idx
                }
        } else {
                ::sth::sthCore::processError returnKeyedList "please at least specify port_handle or handle" {}
                set cmdState $FAILURE
                return $returnKeyedList 
        }
    
        if {[::info exists cmdError]} {
                set cmdState $FAILURE
                return $returnKeyedList
        } else {
                    # apply config            
                if {[catch {::sth::sthCore::doStcApply} applyError]} {
                # if apply fails, delete any routers we may have created
                        foreach rtr $rtrHdlList {
                                if {[catch {::sth::sthCore::invoke stc::delete $rtr} err]} {
                                        return -code error "$err"   
                                }
                        }
                        return -code error $applyError
                }
        # subscribe to the resultdataset
        #if {![::sth::sthCore::ResultDataSetSubscribe ::sth::IsIs:: IsisRouterConfig IsisRouterResults returnKeyedList]} {
        #    return -code error "Error subscribing to the ISIS result data set"
        #}
                keylset returnKeyedList handle $rtrHdlList
                keylset returnKeyedList handles $rtrHdlList
                keylset returnKeyedList session_router $lspHdlList
                set cmdState $SUCCESS
                return $returnKeyedList
        }
}




###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_modify (str args)
###\brief Process \em -mode switch with value \em modify for emulation_isis_config cmd
###
###This procedure executes the emulation_isis_config command when the mode is modify. It will stop all isis sessions based on the port_handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang),  modified by Tong Zhou for P2
###*/
###
###emulation_isis_config_modify (str args);
###

proc ::sth::IsIs::emulation_isis_config_modify { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::emulation_isis_config_procfunc
    variable ::sth::IsIs::emulation_isis_configFunctionPriority

    set _OrigHltCmdName "emulation_isis_config"
    set _hltCmdName "emulation_isis_config_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    #Configure the modify IsIsSession with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
        
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the modify mode of emulation_isis_config" {}
        return $FAILURE
    } else {
        set isisRouterHandle $userArgsArray(handle)
        if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "The router handle $isisRouterHandle is invalid for ISIS" {}
            return $FAILURE
        } else {
            if {[catch {set isisLspHandleList [::sth::sthCore::invoke stc::get $isisSessionHandle -children-IsisLspConfig]}]} {
                ::sth::sthCore::processError returnKeyedList "The session handle $isisSessionHandle is invalid for isis" {}
                return $FAILURE
            }
        }
    }
    
    # If "vlan" is not explicitly set, enable "vlan" flag if any vlan arguments configured 
    set vlanOptFound [regexp -- {vlan} $userArgsArray(optional_args)]
    if {![info exists userArgsArray(vlan)] && $vlanOptFound} { set userArgsArray(vlan) 1 }
    
    #If "atm_encapsulation" is not explicitly set, enable "atm_encapsulation" if any atm arguments configured 
    if {![info exists userArgsArray(atm_encapsulation)]} {
        if {[info exists userArgsArray(vci)] || [info exist userArgsArray(vpi)]} { set userArgsArray(atm_encapsulation) 1}
    } else {
        if {![info exist userArgsArray(vci)]} {set userArgsArray(vci) 100}
        if {![info exist userArgsArray(vpi)]} {set userArgsArray(vpi) 100}
    }
    
    set cmdPass 1
    set priorityList [::sth::IsIs::processSwitches emulation_isis_config ::sth::IsIs:: returnKeyedList modify funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
#        puts $functionName
        set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_isis_config $funcSwitchArray($functionName) $isisRouterHandle $isisSessionHandle $isisLspHandleList]
        if {$cmdPass <= 0} {
            break
        }
    }
    #enable/disable BFD
        if {[info exists userArgsArray(bfd_registration)]} {
                configBfdRegistration $isisRouterHandle $userArgsArray(mode) 
        }
        
    #modify the gre
        if {[info exists userArgsArray(tunnel_handle)] == 1} {
            set cmdPass [::sth::configGreStack $userArgsArray(tunnel_handle) $isisRouterHandle]
        }
    
    # Apply the modifications to IL
    if {[catch {::sth::sthCore::doStcApply } err]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while applying config. Error: $err" {}    
        set cmdState $FAILURE
        return $returnKeyedList
    }
        
    if {$cmdPass <= 0} { 
        set cmdState $FAILURE
        return $returnKeyedList 
    } else {
                keylset returnKeyedList handle $isisRouterHandle
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}



###RXu: To enable the protocol after you disable it
proc ::sth::IsIs::emulation_isis_config_active { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::emulation_isis_config_procfunc
    variable ::sth::IsIs::emulation_isis_configFunctionPriority

    set _OrigHltCmdName "emulation_isis_config"
    set _hltCmdName "emulation_isis_config_active"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    #Configure the modify IsIsSession with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
        
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the active mode of emulation_isis_config" {}
            return $FAILURE
        } else {
            set isisRouterHandles $userArgsArray(handle)
            foreach isisRouterHandle $isisRouterHandles {
                if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The router handle $isisRouterHandle is invalid for ISIS" {}
                    return $FAILURE
                }
                if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle "-Active TRUE -LocalActive TRUE"} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Failed to active ISIS protocol for $userArgsArray(handle)" {}
                    return $FAILURE
                }
            }
        }
        keylset returnKeyedList handle $isisRouterHandles
        set cmdState $SUCCESS
        return $returnKeyedList
}


proc ::sth::IsIs::emulation_isis_config_activate { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::emulation_isis_config_procfunc
    variable ::sth::IsIs::emulation_isis_configFunctionPriority

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState


    array set mainDefaultAry {}
    set opList "hello_padding ip_version routing_level system_id system_id_step graceful_restart wide_metrics bfd_registration intf_type"
    foreach key $opList {
        if {[info exists ::sth::IsIs::emulation_isis_config_default($key)]} {
            set value [set ::sth::IsIs::emulation_isis_config_default($key)]
            set mainDefaultAry($key) $value
        }
    }
    set opList "authentication_mode password md5_key_id"
    foreach key $opList {
        if {[info exists ::sth::IsIs::emulation_isis_config_default($key)]} {
            set value [set ::sth::IsIs::emulation_isis_config_default($key)]
            set authDefaultAry($key) $value
        }
    }

    set mOptionList ""
    set authOptionList ""
    foreach idx [array names mainDefaultAry] {
        if {[info exists userArgsArray($idx)]} {
            if {[info exists ::sth::IsIs::emulation_isis_config_$idx\_fwdmap($userArgsArray($idx))]} {
                set value [set ::sth::IsIs::emulation_isis_config_$idx\_fwdmap($userArgsArray($idx))]
                set userArgsArray($idx) $value
            }
            set mainDefaultAry($idx) $userArgsArray($idx)
        }
        if {[string equal $mainDefaultAry($idx) "_none_"]} { continue }
        regsub -all {[.]} $::sth::IsIs::emulation_isis_config_stcattr($idx) "" stcAttr
        append mOptionList " -$stcAttr $mainDefaultAry($idx)"
    }
    if {[info exists userArgsArray(area_id)]} {
        append mOptionList " -Area $userArgsArray(area_id)"
    }
    
    foreach idx [array names authDefaultAry] {
        if {[info exists userArgsArray($idx)]} {
            set authDefaultAry($idx) $userArgsArray($idx)
        }
        if {[string equal $authDefaultAry($idx) "_none_"]} { continue }
        append authOptionList " -$::sth::IsIs::emulation_isis_config_stcattr($idx) $authDefaultAry($idx)"
    }
        
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the activate mode of emulation_isis_config" {}
        return $FAILURE
    } else {
        set isisGenHnd [::sth::sthCore::invoke stc::create IsisDeviceGenProtocolParams -under $userArgsArray(handle)]
        if { $mOptionList != "" } {
            ::sth::sthCore::invoke stc::config $isisGenHnd $mOptionList
        }
        set authHnd [::sth::sthCore::invoke stc::get $isisGenHnd -children-IsisAuthenticationParams]
        if { $authOptionList != "" } {
            ::sth::sthCore::invoke stc::config $authHnd $authOptionList
        }
        
        if {[info exists userArgsArray(expand)] &&
            $userArgsArray(expand) == "false"} {
            keylset returnKeyedList handle_list ""
        } else {
            array set return [::sth::sthCore::invoke stc::perform devicegenconfigexpand -deleteexisting no -genparams $userArgsArray(handle)]
            keylset returnKeyedList handle_list $return(-ReturnList)
        }
    }

    keylset returnKeyedList handle ""
    set cmdState $SUCCESS
    return $returnKeyedList
}


###RXu: To disable the protocol instead of removing it
proc ::sth::IsIs::emulation_isis_config_inactive { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::emulation_isis_config_procfunc
    variable ::sth::IsIs::emulation_isis_configFunctionPriority

    set _OrigHltCmdName "emulation_isis_config"
    set _hltCmdName "emulation_isis_config_inactive"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    #Configure the modify IsIsSession with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
        
        if {![info exists userArgsArray(handle)]} {
            ::sth::sthCore::processError returnKeyedList "Switch -handle is required in the inactive mode of emulation_isis_config" {}
            return $FAILURE
        } else {
            set isisRouterHandles $userArgsArray(handle)
            foreach isisRouterHandle $isisRouterHandles {
                if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "The router handle $isisRouterHandle is invalid for ISIS" {}
                    return $FAILURE
                }
                if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle "-Active FALSE -LocalActive FALSE"} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Failed to inactive ISIS protocol for $userArgsArray(handle)" {}
                    return $FAILURE
                }
            }
        }
        keylset returnKeyedList handle $isisRouterHandles
        set cmdState $SUCCESS
        return $returnKeyedList
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_delete (str args)
###\brief Process \em -mode switch with value \em delete for emulation_isis_config cmd
###
###This procedure execute the emulation_isis_config command when the mode is delete. It will delete all isis sessions based on the port_handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_config_delete (str args);
###

proc ::sth::IsIs::emulation_isis_config_delete { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcatt
    variable ::sth::IsIs::emulation_isis_config_procfunc
    variable ::sth::IsIs::emulation_isis_configFunctionPriority

    set _OrigHltCmdName "emulation_isis_config"
    set _hltCmdName "emulation_isis_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {(![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)] )} {
         ::sth::sthCore::processError returnKeyedList "At least one of the switches -handle and -port_handle is required for mode delete." {}
        set cmdState $FAILURE
        return $returnKeyedList          
    } else {
        if {[info exists userArgsArray(handle)]} {
            set isisHandle $userArgsArray(handle)
            #Validate the isis_handle, this is the handle of router
            ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::IsIs::IsIsIsSessionHandleValid $isisHandle msg]} {
                 ::sth::sthCore::processError returnKeyedList "The value $isisHandle is not valid for the switch -handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }          
        }
        
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            } 
        }
    }
    
    if {[info exists userArgsArray(port_handle)]} {    
        if {([info exists isisHandle] && $isisHandle != "")} {
            # if there is a router handle, delete this router handle
            #Call delete on all routers and also unset all routeblk and n/w blks info
            if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Error resetting router for ISISSession:$isisHandle Msg: $eMsg" {}    
            }
        } else {
            #delete all the routers under the port
            if {![::sth::IsIs::IsIsIsPortValid $portHandle routerHandleList]} {    
                ::sth::sthCore::processError returnKeyedList "No ISISSessions exists associated with Port Handle:$portHandle" {}    
                set cmdState $FAILURE
                return $returnKeyedList
            } else {
                ::sth::sthCore::log info "List of ISISSessions to be deleted:{$routerHandleList}"  
            }
            
            set isisSessionList [list]
            
            foreach routerHandle $routerHandleList {
                #Call delete on all routers (Their children, such as Ipv4If, Ipv6If, VlanIf and LSP will be deleted) and also unset all routeblk and n/w blks info
                if {[catch {::sth::sthCore::invoke stc::delete $routerHandle} eMsg ]} {
                    set cmdError 1
                    ::sth::sthCore::processError returnKeyedList "Error occured while deleting ISISSession:$isisSessionHandle" {}    
                }
            }
        }
    } else {
        #delete isis session indicate in the session handle
        #find corresponding $portHandle
        if {![::sth::IsIs::getIsIsPort $isisHandle portHandle]} {
             ::sth::sthCore::processError returnKeyedList "The value $isisHandle is not valid for the switch -handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList            
        } else {
            #Call delete on all routers and also unset all routeblk and n/w blks info
            if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg ]} {
                set cmdError 1
                ::sth::sthCore::processError returnKeyedList "Error occured while deleting ISISSession:$isisSessionHandle" {}    
            }
        }
    }
    if {[::info exists cmdError]} {
        set cmdState $FAILURE
        return $returnKeyedList
    } else {    
        set cmdState $SUCCESS
        return $returnKeyedList 
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_control_start (str args)
###\brief Process \em -mode switch with value \em start for emulation_isis_control cmd
###
###This procedure execute the emulation_isis_control command when the mode is \em start. It will start isis session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
###emulation_isis_control_start (str args);
###

proc ::sth::IsIs::emulation_isis_control_start { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_control_stcobj
    variable ::sth::IsIs::emulation_isis_control_stcattr
    variable ::sth::IsIs::emulation_isis_control_procfunc
    variable ::sth::IsIs::emulation_isis_controlFunctionPriority

    set _OrigHltCmdName "emulation_isis_control"
    set _hltCmdName "emulation_isis_control_start"
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"

    if {(![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)] )} {
        ::sth::sthCore::processError returnKeyedList "At least one of the switches -handle and -port_handle is required." {}
        set cmdState $FAILURE
        return $returnKeyedList          
    } else {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            } 
            set isisHandle $portHandle
        }

        if {[info exists userArgsArray(handle)]} {
            set isisRouterHandle $userArgsArray(handle)
            #Validate the isis_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::IsIs::IsIsIsSessionHandleValid $isisRouterHandle isisProtocolHandle]} {
                ::sth::sthCore::processError returnKeyedList "The value $isisRouterHandle is not valid for the switch -handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }          
        }
    }

    #initializing the cmd specific data, validating switches and user input for each switch
#    ::sth::sthCore::cmdInit
    
    #Configure the start isis router with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    
    # fetch the value of switches and the corresponding function, run the function according to the their priority
    set cmdPassed 1
    set priorityList [::sth::IsIs::processSwitches emulation_isis_control ::sth::IsIs:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        if {[string equal $functionName "emulation_isis_control_flap"]} {
            ::sth::sthCore::log debug "Warning: the flap parameters are only used in flap mode, ignored in start mode"
        } else {
            set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName)]
        }
        if {$cmdPassed <= 0} {
            break
        }
    }


    if {$cmdPassed <= 0} {
        ::sth::sthCore::processError returnKeyedList "Failed executing the command $_hltCmdName" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {([info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) != "")} {
        #start all the router under the port
        set portHandle $userArgsArray(port_handle)
        if {![::sth::IsIs::IsIsIsPortValid $portHandle routerList]} {
            ::sth::sthCore::processError returnKeyedList "No ISISSessions exists associated with port handle:$portHandle" {}        
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            ::sth::sthCore::log info "List of ISIS routers to be started:{$routerList}"  
        }
        
        if {[llength $routerList] > 0} {
            set tmpCount -1
            foreach router $routerList {
                incr tmpCount
                if {[catch {set isisProtocolHandle [::sth::sthCore::invoke stc::get $router -children-isisRouterConfig]}]} {
                    set routerList [lreplace $routerList $tmpCount $tmpCount]
                    set tmpCount [expr $tmpCount-1]
                } else {
                    lappend protocolList $isisProtocolHandle
                }
            }
            if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList \{$routerList\}"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting routers: $routerList, Error: $eMsg" {}    
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList \{$protocolList\}"} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting protocols: $protocolList, Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
        }
    } else {
        #Call start on isisSession Handle
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStart -DeviceList $isisRouterHandle"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting router: $isisRouterHandle, Error: $eMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStart -ProtocolList $isisProtocolHandle"} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while starting protocols: $isisProtocolHandle, Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList 
        }
    }
    set cmdState $SUCCESS  
    return $returnKeyedList
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_control_stop (str args)
###\brief Process \em -mode switch with value \em stop for emulation_isis_control cmd
###
###This procedure execute the emulation_isis_control command when the mode is \em stop. It will start isis session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_control_stop (str args);
###

proc ::sth::IsIs::emulation_isis_control_stop { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_control_stcobj
    variable ::sth::IsIs::emulation_isis_control_stcattr
    variable ::sth::IsIs::emulation_isis_control_procfunc
    variable ::sth::IsIs::emulation_isis_controlFunctionPriority

    set _OrigHltCmdName "emulation_isis_control"
    set _hltCmdName "emulation_isis_control_stop"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {(![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)] )} {
        ::sth::sthCore::processError returnKeyedList "At least one of the switches -handle and -port_handle is required." {}
        set cmdState $FAILURE
        return $returnKeyedList          
    } else {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            } 
            set isisHandle $portHandle
        }

        if {[info exists userArgsArray(handle)]} {
            set isisRouterHandle $userArgsArray(handle)
            #Validate the isis_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::IsIs::IsIsIsSessionHandleValid $isisRouterHandle isisProtocolHandle]} {
                ::sth::sthCore::processError returnKeyedList "The value $isisRouterHandle is not valid for the switch -handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }          
        }
    }

    #initializing the cmd specific data, validating switches and user input for each switch
#    ::sth::sthCore::cmdInit
    
    #Configure the start isis router with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    
    # fetch the value of switches and the corresponding function, run the function according to the their priority
    set cmdPassed 1
    set priorityList [::sth::IsIs::processSwitches emulation_isis_control ::sth::IsIs:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        if {[string equal $functionName "emulation_isis_control_flap"]} {
            ::sth::sthCore::log debug "Warning: the flap parameters are only used in flap mode, ignored in start mode"
        } else {
            set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName)]
        }
        if {$cmdPassed <= 0} {
            break
        }
    }


    if {$cmdPassed <= 0} {
        ::sth::sthCore::processError returnKeyedList "Failed executing the command $_hltCmdName" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {([info exists userArgsArray(port_handle)] && $userArgsArray(port_handle) != "")} {
        #start all the router under the port
        set portHandle $userArgsArray(port_handle)
        if {![::sth::IsIs::IsIsIsPortValid $portHandle routerList]} {
            ::sth::sthCore::processError returnKeyedList "No ISISSessions exists associated with port handle:$portHandle" {}        
            set cmdState $FAILURE
            return $returnKeyedList
        } else {
            ::sth::sthCore::log info "List of ISIS routers to be started:{$routerList}"  
        }
        
        if {[llength $routerList] > 0} {
            set tmpCount -1
            foreach router $routerList {
                incr tmpCount
                if {[catch {set isisProtocolHandle [::sth::sthCore::invoke stc::get $router -children-isisRouterConfig]}]} {
                    set routerList [lreplace $routerList $tmpCount $tmpCount]
                    set tmpCount [expr $tmpCount-1]
                } else {
                    lappend protocolList $isisProtocolHandle
                }
            }
            if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList \{$protocolList\}"} eMsg]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while stopping protocols: $protocolList, Error: $eMsg" {}
                set cmdState $FAILURE
                return $returnKeyedList 
            }
            if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList \{$routerList\}"} eMsg ]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while stopping routers: $routerList, Error: $eMsg" {}    
                set cmdState $FAILURE
                return $returnKeyedList 
            }
        }
    } else {
        #Call stop on isisSession Handle
        if {[catch {::sth::sthCore::invoke stc::perform "ProtocolStop -ProtocolList $isisProtocolHandle"} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while stopping protocols: $isisProtocolHandle, Error: $eMsg" {}        
            set cmdState $FAILURE
            return $returnKeyedList 
        }
        if {[catch {::sth::sthCore::invoke stc::perform "DeviceStop -DeviceList $isisRouterHandle"} eMsg ]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while stopping router: $isisRouterHandle, Error: $eMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList 
        }
    }
    set cmdState $SUCCESS  
    return $returnKeyedList
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_control_restart (str args)
###\brief Process \em -mode switch with value \em restart for emulation_isis_control cmd
###
###This procedure execute the emulation_isis_control command when the mode is \em restart. It will re-start isis session based on the handle switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_control_restart (str args);
###

proc ::sth::IsIs::emulation_isis_control_restart { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray

    set _OrigHltCmdName "emulation_isis_control"
    set _hltCmdName "emulation_isis_control_restart"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    if {(![info exists userArgsArray(port_handle)] && ![info exists userArgsArray(handle)] )} {
        ::sth::sthCore::processError returnKeyedList "At least one of the switches -handle and -port_handle is required." {}
        set cmdState $FAILURE
        return $returnKeyedList          
    } else {
        if {[info exists userArgsArray(port_handle)]} {
            set portHandle $userArgsArray(port_handle)
            #Validate the port_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of port_handle"
            set msg ""
            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }
            # get all routers under the port
            if {[catch {::sth::sthCore::invoke stc::get $portHandle -affiliationport-Sources} routeruserArgsArray]} {
                ::sth::sthCore::processError returnKeyedList "Error fetching routers under $portHandle." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } elseif {[info exists userArgsArray(handle)]} {
            set routeruserArgsArray $userArgsArray(handle)
            #Validate the isis_handle
            ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
            set msg ""
            foreach isisRouterHandle $routeruserArgsArray {
                if {![::sth::IsIs::IsIsIsSessionHandleValid $isisRouterHandle msg]} {
                    ::sth::sthCore::processError returnKeyedList "The value $isisRouterHandle is not valid for the switch -handle ." {}
                    set cmdState $FAILURE
                    return $returnKeyedList        
                }
            }
        }
    }
    
    set isisRtrConfigList {}
    foreach rtr $routeruserArgsArray {
        if {[catch {::sth::sthCore::invoke stc::get $rtr -children-isisrouterconfig} isisRtrConfigHandle]} {
            return -code error "Error fetching isisRouterConfig objects"   
        }
        
        # verify that the router has graceful restart enabled
        if {[catch {::sth::sthCore::invoke stc::get $isisRtrConfigHandle -EnableGracefulRestart} gracefulRestartEnabled]} {
            return -code error "Error fetching -EnableGracefulRestart property"
        }
        if {!$gracefulRestartEnabled} {
            return -code error "\"-graceful_restart\" not enabled on $rtr."
        }
        lappend isisRtrConfigList $isisRtrConfigHandle
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform IsisRestartIsisRouter -RouterList $isisRtrConfigList} eMsg]} {
        return -code error "Error restarting ISIS router: $isisRtrConfigHandle Msg: $eMsg"
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_control_flap (str args)
###\brief Process \em -mode switch with value \em flap for emulation_isis_control cmd
###
###This procedure execute the emulation_isis_control command when the mode is \em flap. It will flap routes based on the flap_routes switch value.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList 
###
###
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_control_flap (str args);
###

proc ::sth::IsIs::emulation_isis_control_flap { returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::ISISROUTEHNDLIST

    ::sth::sthCore::log debug "Executing Internal Sub command for: emulation_isis_control {emulation_isis_control_flap}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

#    if {(![info exists userArgsArray(port_handle)]  && ![info exists userArgsArray(handle)]) } {
#        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
#        set cmdState $FAILURE
#        return $returnKeyedList          
#    } else {
#        if {[info exists userArgsArray(port_handle)]} {
#            set portHandle $userArgsArray(port_handle)
#            #Validate the port_handle
#            ::sth::sthCore::log info "__VALIDATE__: Validate value of port_handle"
#            set msg ""
#            if {![::sth::sthCore::IsPortValid $portHandle msg]} {
#                if {[string equal $portHandle SHA_NO_USER_INPUT] == 1} {
#                    set portHandle "{{}}"
#                }
#                ::sth::sthCore::processError returnKeyedList "The value $portHandle is not valid for the switch -port_handle ." {}
#                set cmdState $FAILURE
#                return $returnKeyedList        
#            }
#        }
#    }
    
    # validate mandatory args
    set reqdArgs {}
    foreach requiredArg {handle flap_count flap_down_time flap_interval_time flap_routes} {
        if {![info exists userArgsArray($requiredArg)]} {
            lappend reqdArgs "\"-$requiredArg\""
        }
    }
    if {[llength $reqdArgs]} {
        return -code error "The following mandatory argument(s) are missing: [join $reqdArgs {, }]"
    }
    # validate ISIS handle
    set isisRouterHandle $userArgsArray(handle)
    set msg ""
    if {![::sth::IsIs::IsIsIsSessionHandleValid $isisRouterHandle msg]} {
        return -code error "The value $isisRouterHandle is not valid for the switch -handle."    
    }
    
    ###
    # Sequence of commands
    #    1. IsisWithdrawIpRoutesCommand
    #    2. WaitCommand (-flap_down_time)
    #    3. IsisReadvertiseLspsCommand
    #    4. WaitCommand (-flap_interval_time) ** applies when flap_count > 1
    ###
    
    # create the commands
    set seqHandle $::sth::sthCore::GBLHNDMAP(sequencer)
    set sysHandle $::sth::sthCore::GBLHNDMAP(system)
    
    # create a loop command that will contain all the ISIS commands
    set options [list -IterationCount $userArgsArray(flap_count) -ExecutionMode "BACKGROUND" -GroupCategory "REGULAR_COMMAND" -ContinuousMode "FALSE" -ExecuteSynchronous "FALSE"]
    if {[catch {::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under $seqHandle $options} seqLoopCmdHdl]} {
        return -code error "Error creating SequencerLoopCommand"
    }
    
    # build up the sequence list
    set sequenceList {}
    if {[catch {::sth::sthCore::invoke stc::create "IsisWithdrawIpRoutesCommand" -under $seqLoopCmdHdl} isisWithdrawCmdHdl]} {
        return -code error "Error creating IsisWithdrawIpRoutesCommand"
    }
    lappend sequenceList $isisWithdrawCmdHdl
    
    set options [list -WaitTime $userArgsArray(flap_down_time)]
    if {[catch {::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmdHdl $options} dwnTimeCmdHdl]} {
        return -code error "Error creating WaitCommand for flap_down_time"
    }
    lappend sequenceList $dwnTimeCmdHdl
    
    if {[catch {::sth::sthCore::invoke stc::create "IsisReadvertiseLspsCommand" -under $seqLoopCmdHdl} isisReadvertiseCmdHdl]} {
        return -code error "Error creating IsisReadvertiseLspsCommand"
    }
    lappend sequenceList $isisReadvertiseCmdHdl
    
    if {$userArgsArray(flap_count) > 1} {
        set options [list -WaitTime $userArgsArray(flap_interval_time)]
        if {[catch {::sth::sthCore::invoke stc::create "WaitCommand" -under $seqLoopCmdHdl $options} intervalTimeCmdHdl]} {
            return -code error "Error creating WaitCommand for flap_interval_time"
        }
        lappend sequenceList $intervalTimeCmdHdl
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $seqLoopCmdHdl [list -CommandList $sequenceList]} err]} {
        return -code error "Error configuring sequencer for ISIS route flapping."
    }

    # config the isis events
    set routeHandles {}
    foreach routeHdl $userArgsArray(flap_routes) {
        if {![info exists ISISROUTEHNDLIST($routeHdl)]} {
            append routeHandles "$routeHdl "
        } else {
                # get the list index of the appropriate isisRouteHandle
                set ipVer [lindex $ISISROUTEHNDLIST($routeHdl) 1]
                switch -- $ipVer {
                    4 {
                        set routeHandles [concat $routeHandles [lindex $ISISROUTEHNDLIST($routeHdl) 2]]
                    }
                    6 {
                        set routeHandles [concat $routeHandles [lindex $ISISROUTEHNDLIST($routeHdl) 3]]
                    }
                    4_6 {
                        set routeHandles [concat $routeHandles [lindex $ISISROUTEHNDLIST($routeHdl) 2]]
                        set routeHandles [concat $routeHandles [lindex $ISISROUTEHNDLIST($routeHdl) 3]]
                    }   
                }
        }
    }

    if {[catch {::sth::sthCore::invoke stc::config $isisWithdrawCmdHdl "-IsisIpRouteList [list $routeHandles]"} err]} {
        return -code error "Error configuring $isisWithdrawCmdHdl."
    }
    if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-isisrouterconfig} isisConfigHdl]} {
        return -code error "Error getting isisrouterconfig handle."
    }
    if {[catch {::sth::sthCore::invoke stc::config $isisReadvertiseCmdHdl "-RouterList [list $isisConfigHdl]"} err]} {
        return -code error "Error configuring $isisReadvertiseCmdHdl."
    }
    
    # insert the loop command into the sequencer
    if {[catch {::sth::sthCore::invoke stc::config $seqHandle "-CommandList $seqLoopCmdHdl"} err]} {
        return -code error "Error configuring sequencer for ISIS route flapping."
    }
    
    # Start the sequencer
    ::sth::sthCore::invoke stc::perform sequencerStart
    ::sth::sthCore::invoke stc::delete $isisWithdrawCmdHdl
    ::sth::sthCore::invoke stc::delete $dwnTimeCmdHdl
    ::sth::sthCore::invoke stc::delete $isisReadvertiseCmdHdl
    if {[info exists intervalTimeCmdHdl]} {
        ::sth::sthCore::invoke stc::delete $intervalTimeCmdHdl
    }
    
    set cmdState $SUCCESS  
    return $returnKeyedList
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_create (str args)
###\brief Process \em -mode switch with value \em create for emulation_isis_topology_route_config cmd
###
###This procedure execute the emulation_isis_topology_route_config command when the mode is create. It will create routeBlks or LSP based on the \em -type switch.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList with isis route blk handles
    ###
###
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_topology_route_config_create (str args);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_create { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_procfunc
    variable ::sth::IsIs::emulation_isis_topology_route_configFunctionPriority
    variable ::sth::IsIs::emulation_isis_topology_route_config_router_routing_level_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    variable ::sth::IsIs::ISISROUTECOUNT

    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_create"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #Validate the value of isis handle
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set isisRouterHandle $userArgsArray(handle)
        ::sth::sthCore::log info "__VALIDATE__: Validate value of handle $isisRouterHandle"
        set msg ""
        if {![::sth::IsIs::IsIsIsSessionHandleValid $isisRouterHandle msg]} {
            ::sth::sthCore::processError returnKeyedList "The value $isisRouterHandle is not valid for the switch -handle ." {}
            set cmdState $FAILURE
            return $returnKeyedList        
        } else {
            set isisSessionHandle $msg
        }
    }

    # Verify the IP version of isis route
    if {[catch {set ip_version [::sth::sthCore::invoke stc::get $isisSessionHandle -IpVersion]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the IP version from object $isisRouterhandle" {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        if {[info exists userArgsArray(ip_version)]} {
            set ipVersionSwitch $userArgsArray(ip_version)
            if {![::sth::IsIs::IpVersionCompatible $ip_version $ipVersionSwitch]} {
                ::sth::sthCore::processError returnKeyedList "Cannot have ip version $ipVersionSwitch under router with ip version $ip_version" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        } else {
            switch $ip_version {
                IPV4 {
                    set userArgsArray(ip_version) 4
                }
                IPV6 {
                    set userArgsArray(ip_version) 6
                }
                IPV4_AND_IPV6 {
                    set userArgsArray(ip_version) 4_6
                }
            }
        }
    }
    
    #get the type for configuration
    if {![info exists userArgsArray(type)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -type is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set topologyType $userArgsArray(type)
    }
    
    #get the router_system_id    
    if {![info exists userArgsArray(router_system_id)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -router_system_id is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set routerSystemId $userArgsArray(router_system_id)
        set routerSystemId [::sth::IsIs::convertSystemId $routerSystemId]
    }
    
    #get the router_routing_level
    if {![info exists userArgsArray(router_routing_level)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -router_routing_level is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set routerLevel $userArgsArray(router_routing_level)
        set routerLevel $emulation_isis_topology_route_config_router_routing_level_fwdmap($routerLevel)
    }
    if {[catch {::sth::sthCore::invoke stc::get $isisSessionHandle -Level} isisRtrLevel]} {
        ::sth::sthCore::processError returnKeyedList "Unable to get $isisSessionHandle Level" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    # make sure router_routing_level matches the ISIS session's level
    if {![string match -nocase "LEVEL1_AND_2" $isisRtrLevel] && ![string match -nocase $routerLevel $isisRtrLevel]} {
        ::sth::sthCore::processError returnKeyedList "The \"router_routing_level\" must match the ISIS session's level ($isisRtrLevel)" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

    set isisNbrHandle "-1"
    set isisLspHandle {}
    switch -exact $topologyType {
        router {
            if {[info exists userArgsArray(router_connect)]} {    
                #Validate the handle
                set routerConnectHandle $userArgsArray(router_connect)
                ::sth::sthCore::log info "__VALIDATE__: Validate value of handle $routerConnectHandle"
                set msg ""
                if {![::sth::IsIs::IsIsIsLspHandleValid $routerConnectHandle msg]} {
                    ::sth::sthCore::processError returnKeyedList "The value $routerConnectHandle is not valid for the switch -router_connect ." {}
                    set cmdState $FAILURE
                    return $returnKeyedList        
                }
            }
            
            # Search for existing ISIS session router's LSP. Otherwise create one.
            if {[catch {::sth::sthCore::invoke stc::get $isisSessionHandle -SystemId} isisRtrSystemId]} {
                ::sth::sthCore::processError returnKeyedList "Unable to get $isisSessionHandle System ID" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if {![::sth::IsIs::getLspHandleOnSysId $isisRouterHandle $isisRtrSystemId $routerLevel isisLspHandle]} {
                # need to create an LSP for the ISIS router specified in <handle>
                set isisRtrLevel {}
                if {[string match -nocase "LEVEL1_AND_2" $routerLevel]} {
                    # determine how many LSPs to create and what levels should be assigned
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel [list LEVEL1 LEVEL2]
                    } else {
                        foreach lspHandle $isisLspHandle {
                            if {[catch {::sth::sthCore::invoke stc::get $lspHandle -Level} level]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while fetching IsisLSP object, Error: $lspHandle" {}
                                set cmdState $FAILURE
                                return $FAILURE
                            }
                            if {[string match -nocase "LEVEL1" $level]} {
                                set isisRtrLevel LEVEL2 ;# need to create a Level2 LSP
                                break
                            } else {
                                set isisRtrLevel LEVEL1 ;# need to create a Level1 LSP
                                break
                            }
                        }
                    }
                    
                } else {
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel $routerLevel
                    }
                }
                foreach rtrLevel $isisRtrLevel {
                    if {[catch {::sth::sthCore::invoke stc::create IsisLSPConfig -under $isisSessionHandle "-Level $rtrLevel -SystemId $isisRtrSystemId"} lspHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisLSP object, Error: $lspHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                    lappend isisLspHandle $lspHandle
                }
            }

            # Note: isisLspHandle can potentially have two lsp handles (one LEVEL1 and one LEVEL2)
            set isisHandle {}
            set isisNbrHandle {}
            foreach lspHandle $isisLspHandle {
                set ISISLSPNEIGHBORLIST($lspHandle) [list]
                
                #Create the IsisNeighbor under the ISIS session's LSP and then configure the other parameters.
                if {[catch {::sth::sthCore::invoke stc::create IsisLspNeighborConfig -under $lspHandle "-NeighborSystemId $routerSystemId"} nbrHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisNeighbor under ISIS Lsp handle $lspHandle. Error: $nbrHandle" {}
                    set cmdState $FAILURE
                    return $FAILURE
                }
                
                #Create the ISIS session's neighbor LSP and then configure the other parameters.
                if {[catch {::sth::sthCore::invoke stc::create IsisLSPConfig -under $isisSessionHandle} nbrIsisLspHandle]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating neighbor IsisLSP object, Error: $nbrIsisLspHandle" {}
                    set cmdState $FAILURE
                    return $FAILURE
                } else {
                    if {[info exists userArgsArray(ip_version)]} {
                        set ::sth::IsIs::ISISLSPIPVER($nbrIsisLspHandle) $::sth::IsIs::userArgsArray(ip_version)
                    }
                    ::sth::sthCore::log info "The IsisLSP:$nbrIsisLspHandle was successfully created under isisRouter:$isisSessionHandle"
                    lappend ISISLSPNEIGHBORLIST($lspHandle) $nbrIsisLspHandle
                }
                
                if {[info exists userArgsArray(router_connect)]} {
                    #Create the IsisNeighbor under the isisLSP and then configure the other parameters.
                    if {[catch {::sth::sthCore::invoke stc::create IsisLspNeighborConfig -under $nbrIsisLspHandle "-NeighborSystemId $routerSystemId"} nbrHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisNeighbor under ISIS Lsp handle $nbrIsisLspHandle. Error: $nbrHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                    lappend isisNbrHandle $nbrHandle
                    lappend ISISLSPNEIGHBORLIST($nbrIsisLspHandle) $userArgsArray(router_connect)
                }
                lappend isisHandle $nbrIsisLspHandle
            }
        }
        stub {
            # Search for existing ISIS session router's LSP. Otherwise create one.
            if {[catch {::sth::sthCore::invoke stc::get $isisSessionHandle -SystemId} isisRtrSystemId]} {
                ::sth::sthCore::processError returnKeyedList "Unable to get $isisSessionHandle System ID" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            # Search for existing LSP based on specified "router_system_id" and "router_routing_level"
            if {![::sth::IsIs::getLspHandleOnSysId $isisRouterHandle $routerSystemId $routerLevel isisLspHandle]} {
                # need to create an LSP for the ISIS router specified in <handle>
                set isisRtrLevel {}
                if {[string match -nocase "LEVEL1_AND_2" $routerLevel]} {
                    # determine how many LSPs to create and what levels should be assigned
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel [list LEVEL1 LEVEL2]
                    } else {
                        foreach lspHandle $isisLspHandle {
                            if {[catch {::sth::sthCore::invoke stc::get $lspHandle -Level} level]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while fetching IsisLSP object, Error: $lspHandle" {}
                                set cmdState $FAILURE
                                return $FAILURE
                            }
                            if {[string match -nocase "LEVEL1" $level]} {
                                set isisRtrLevel LEVEL2 ;# need to create a Level2 LSP
                                break
                            } else {
                                set isisRtrLevel LEVEL1 ;# need to create a Level1 LSP
                                break
                            }
                        }
                    }
                    
                } else {
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel $routerLevel
                    }
                }
                foreach rtrLevel $isisRtrLevel {
                    if {[catch {::sth::sthCore::invoke stc::create IsisLSPConfig -under $isisSessionHandle "-Level $rtrLevel -SystemId $isisRtrSystemId"} lspHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisLSP object, Error: $lspHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                    lappend isisLspHandle $lspHandle
                }
            }
            
            # validate LSP handle exist
            if {($isisLspHandle < 0 ) } {
                ::sth::sthCore::processError returnKeyedList "Router with system_id $routerSystemId, router_routing_level $routerLevel, and router_pseudonode_num 0 does not exist for desire network advertisement" {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }
            set m_isisLspHandle $isisLspHandle
            
            set isisHandle {}
            foreach isisLspHandle $m_isisLspHandle {
                #Create the IsisIpRoute under the isisLSP and then configure the other parameters.
                if {[info exists userArgsArray(ip_version)]} {
                    set ipVersion $::sth::IsIs::userArgsArray(ip_version)
                } else {
                    if {[catch {set ip_version [::sth::sthCore::invoke stc::get $isisSessionHandle -IpVersion]} getStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Cannot get the IP version from the protocol $isisSessionHandle" {}
                        return $returnKeyedList
                    } else {
                        switch -exact ip_version {
                            IPV4 {
                                set ipVersion 4
                            }
                            IPV6 {
                                set ipVersion 6
                            }
                            default {
                                set ipVersion 4_6
                            }
                        }
                    }
                }
                
                set IsisIpv4RouteHandle ""
                set IsisIpv6RouteHandle ""
                
                if {([string equal $ipVersion 4] || [string equal $ipVersion 4_6])} {
                    if {[catch {set IsisIpv4RouteHandle [::sth::sthCore::invoke stc::create Ipv4IsisRoutesConfig -under $isisLspHandle]} createStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisIpRoute. Error: $createStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    } else {
                        ::sth::sthCore::log info "The IsisIpRoute:$IsisIpv4RouteHandle was successfully created under isisLSP:$isisLspHandle"
                    } 
                    
                    if {[catch {::sth::sthCore::invoke stc::config $IsisIpv4RouteHandle "-ipv4networkblock.NetworkCount 1"} configStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while setting networkBlockHandle: $networkBlockHandle. Error: $configStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                }
                
                if {([string equal $ipVersion 6] || [string equal $ipVersion 4_6])} {
                    if {[catch {set IsisIpv6RouteHandle [::sth::sthCore::invoke stc::create Ipv6IsisRoutesConfig -under $isisLspHandle]} createStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisIpRoute. Error: $createStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    } else {
                        ::sth::sthCore::log info "The IsisIpRoute:$IsisIpv6RouteHandle was successfully created under isisLSP:$isisLspHandle"
                    }
                    
                    if {[catch {::sth::sthCore::invoke stc::config $IsisIpv6RouteHandle "-ipv6networkblock.NetworkCount 1"} configStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while setting networkBlockHandle: $networkBlockHandle. Error: $configStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                }
                
                set m_lspHandle "isisRouteHandle$ISISROUTECOUNT"
                lappend isisHandle $m_lspHandle
                incr ISISROUTECOUNT
                set ISISROUTEHNDLIST($m_lspHandle) [list $isisLspHandle $ipVersion $IsisIpv4RouteHandle $IsisIpv6RouteHandle]
                
                set returnKey "network_stub"
            }
        }
        external {
            # Search for existing ISIS session router's LSP. Otherwise create one.
            if {[catch {::sth::sthCore::invoke stc::get $isisSessionHandle -SystemId} isisRtrSystemId]} {
                ::sth::sthCore::processError returnKeyedList "Unable to get $isisSessionHandle System ID" {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            # Search for existing LSP based on specified "router_system_id" and "router_routing_level"
            if {![::sth::IsIs::getLspHandleOnSysId $isisRouterHandle $routerSystemId $routerLevel isisLspHandle]} {
                # need to create an LSP for the ISIS router specified in <handle>
                set isisRtrLevel {}
                if {[string match -nocase "LEVEL1_AND_2" $routerLevel]} {
                    # determine how many LSPs to create and what levels should be assigned
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel [list LEVEL1 LEVEL2]
                    } else {
                        foreach lspHandle $isisLspHandle {
                            if {[catch {::sth::sthCore::invoke stc::get $lspHandle -Level} level]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while fetching IsisLSP object, Error: $lspHandle" {}
                                set cmdState $FAILURE
                                return $FAILURE
                            }
                            if {[string match -nocase "LEVEL1" $level]} {
                                set isisRtrLevel LEVEL2 ;# need to create a Level2 LSP
                                break
                            } else {
                                set isisRtrLevel LEVEL1 ;# need to create a Level1 LSP
                                break
                            }
                        }
                    }
                    
                } else {
                    if {[llength $isisLspHandle] == 0} {
                        set isisRtrLevel $routerLevel
                    }
                }
                foreach rtrLevel $isisRtrLevel {
                    if {[catch {::sth::sthCore::invoke stc::create IsisLSPConfig -under $isisSessionHandle "-Level $rtrLevel -SystemId $isisRtrSystemId"} lspHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisLSP object, Error: $lspHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                    lappend isisLspHandle $lspHandle
                }
            }
            
            # validate LSP handle exist
            if {($isisLspHandle < 0 ) } {
                ::sth::sthCore::processError returnKeyedList "Router with system_id $routerSystemId, router_routing_level $routerLevel, and router_pseudonode_num 0 does not exist" {}
                set cmdState $FAILURE
                return $returnKeyedList        
            }
            set m_isisLspHandle $isisLspHandle
            set isisHandle {}
            foreach isisLspHandle $m_isisLspHandle {
                #Create the IsisIpRoute under the isisLSP and then configure the other parameters.
                if {[info exists userArgsArray(ip_version)]} {
                    set ipVersion $::sth::IsIs::userArgsArray(ip_version)
                } else {
                    if {[catch {set ip_version [::sth::sthCore::invoke stc::get $isisSessionHandle -IpVersion]} getStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Cannot get the IP version from the protocol $isisSessionHandle" {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    } else {
                        switch -exact ip_version {
                            IPV4 {
                                set ipVersion 4
                            }
                            IPV6 {
                                set ipVersion 6
                            }
                            default {
                                set ipVersion 4_6
                            }
                        }
                    }
                }
                
                set IsisIpv4RouteHandle ""
                set IsisIpv6RouteHandle ""
                
                if {([string equal $ipVersion 4] || [string equal $ipVersion 4_6])} {
                    if {[catch {::sth::sthCore::invoke stc::create Ipv4IsisRoutesConfig -under $isisLspHandle} IsisIpv4RouteHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisIpRoute. Error: $IsisIpv4RouteHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    } else {
                        ::sth::sthCore::log info "The IsisIpRoute:$IsisIpv4RouteHandle was successfully created under isisLSP:$isisLspHandle"
                    } 
                    
                    if {[catch {::sth::sthCore::invoke stc::config $IsisIpv4RouteHandle "-ipv4networkblock.NetworkCount 1"} configStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while setting Ipv4Route: $IsIsIpv4RouteHandle. Error: $configStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                }
                
                if {([string equal $ipVersion 6] || [string equal $ipVersion 4_6])} {
                    if {[catch {::sth::sthCore::invoke stc::create Ipv6IsisRoutesConfig -under $isisLspHandle "-RouteType EXTERNAL"} IsisIpv6RouteHandle]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisIpRoute. Error: $IsisIpv6RouteHandle" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    } else {
                        ::sth::sthCore::log info "The IsisIpRoute:$IsisIpv6RouteHandle was successfully created under isisLSP:$isisLspHandle"
                    }
                    
                    if {[catch {::sth::sthCore::invoke stc::config $IsisIpv6RouteHandle "-ipv6networkblock.NetworkCount 1"} configStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while setting Ipv6Route: $IsisIpv6RouteHandle. Error: $configStatus" {}
                        set cmdState $FAILURE
                        return $FAILURE
                    }
                }
                
                set m_lspHandle "isisRouteHandle$ISISROUTECOUNT"
                lappend isisHandle $m_lspHandle
                incr ISISROUTECOUNT
                
                set ISISROUTEHNDLIST($m_lspHandle) [list $isisLspHandle $ipVersion $IsisIpv4RouteHandle $IsisIpv6RouteHandle]
                
                set returnKey "external"        
            }
        }
        default {
             ::sth::sthCore::processError returnKeyedList "The value $topologyType is not supported for switch -type ." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }    
    }

    #initializing the cmd specific data, validating switches and user input for each switch
    # ::sth::sthCore::cmdInit
    
    #Configure the start isis router with user input (options)
    ::sth::sthCore::log info "Processing the switches in priority order for command:$_hltCmdName"

    set cmdPassed 1
    set priorityList [::sth::IsIs::processSwitches emulation_isis_topology_route_config ::sth::IsIs:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $isisHandle $isisNbrHandle $topologyType]
            
        if {$cmdPassed <= 0} {
            break
        }
    }

    #update the returnKeyedList with the IsIs Handle.
    # get the ip version.
    if {$cmdPassed <= 0} {
        if {[string equal $topologyType "router"]} {
            # directly delete the lsp handle
            foreach isisHdl $isisHandle {
                if {[catch {::sth::sthCore::invoke stc::delete $isisHdl} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error deleting previously created IsisLspConfig as a router:$isisHdl Msg: $eMsg" {}
                }
            }
        } else {
            # troublesome...delete the isisroute handle and then unset the array
            foreach isisHdl $isisHandle {
                set isisHandleList $ISISROUTEHNDLIST($isisHdl)
                set ipv4Handle [lindex $isisHandleList 2]
                set ipv6Handle [lindex $isisHandleList 3]
                if {$ipv4Handle != ""} {
                    if {[catch {::sth::sthCore::invoke stc::delete $ipv4Handle} eMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error deleting previously created Ipv4IsIsRoute:$ipv4Handle Msg: $eMsg" {}
                    }
                }
                if {$ipv6Handle != ""} {
                    if {[catch {::sth::sthCore::invoke stc::delete $ipv6Handle} eMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Error deleting previously created Ipv6IsIsRoute:$ipv6Handle Msg: $eMsg" {}
                    }
                }
                catch {unset ISISROUTEHNDLIST($isisHdl)}
            }
        }
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        # Apply the modifications to IL
        if {[catch {::sth::sthCore::doStcApply } err]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while applying config. Error: $err" {}    
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        set ipVersion $userArgsArray(ip_version)
        
        keylset returnKeyedList elem_handle $isisHandle version $ipVersion
        if {![string equal $topologyType router]} {
            # This is the handle of IP route (stub or external)
            if {[string equal $returnKey "external"]} { 
                # external
                set networkCount $userArgsArray(external_count)
            } else {
                # stub
                set networkCount $userArgsArray(stub_count)
            }
    #        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList $returnKey "num_networks $networkCount"]
            keylset returnKeyedList $returnKey "num_networks $networkCount"
        } else {
            # This is the handle of LSP (router)
            if {![info exists ::sth::IsIs::userArgsArray(router_connect)]} {
                if {[info exists isisLspHandle]} {
                    set ::sth::IsIs::userArgsArray(router_connect) $isisLspHandle
                } else {
                    set ::sth::IsIs::userArgsArray(router_connect) {}
                }
            }
            keylset returnKeyedList router "connected_handles $::sth::IsIs::userArgsArray(router_connect)"
        }
        
        set cmdState $SUCCESS
        return $returnKeyedList
    }    
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_modify (str args)
###\brief Process \em -mode switch with value \em modify for emulation_isis_topology_route_config cmd
###
###This procedure execute the emulation_isis_topology_route_config command when the mode is mofity.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList with isis route blk handles
###
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
###emulation_isis_topology_route_config_modify (str args);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_modify { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray

    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_procfunc
    variable ::sth::IsIs::emulation_isis_topology_route_configFunctionPriority
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST

    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #Validate if the value of isis handle is valid
    if {![info exists userArgsArray(elem_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        #Validate the handle
        set isisHandles $userArgsArray(elem_handle)
        foreach isisHandle $isisHandles {
            ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
            set msg ""
            if {![::sth::IsIs::IsIsIsLspHandleValid  $isisHandle msg]} {
                # may be a route handle
                if {![info exists ISISROUTEHNDLIST($isisHandle)]} {
                    ::sth::sthCore::processError returnKeyedList "The value $isisHandle is not valid for the switch -elem_handle ." {}
                    set cmdState $FAILURE
                    return $returnKeyedList             
                } else {
                    #get route type
                    set ipVersion [lindex $ISISROUTEHNDLIST($isisHandle) 1]
                    set isisRouteHandleList {}
                    if {[string equal $ipVersion "6"]} {
                        set isisRouteHandleList [lindex $ISISROUTEHNDLIST($isisHandle) 3]
                    } elseif {[string equal $ipVersion "4"]} {
                        set isisRouteHandleList [lindex $ISISROUTEHNDLIST($isisHandle) 2]
                    } elseif {[string equal $ipVersion "4_6"]} {
                        set isisRouteHandleList [list [lindex $ISISROUTEHNDLIST($isisHandle) 2] [lindex $ISISROUTEHNDLIST($isisHandle) 3]]
                    }
                    
                    foreach isisRouteHandle $isisRouteHandleList {
                        if { [catch {set routeType [::sth::sthCore::invoke stc::get $isisRouteHandle -routeType]} getStatus ] } {
                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while modifying topology element:$isisHandle. Error: $getStatus" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        break
                    }
                
                    if {[string equal $routeType INTERNAL]} {
                        set origTopologyType "stub"
                    } elseif {[string equal $routeType EXTERNAL]} {
                        set origTopologyType "external"
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Unsupported route_type: $routeType" {}
                        set cmdState $FAILURE
                        return $returnKeyedList                        
                    }
                }
            } else {
                set origTopologyType "router"
            }
        }
    }
    
    if {(![info exists userArgsArray(type)] || $userArgsArray(type) == "")} {
        set newTopologyType $origTopologyType
    } else {
        set newTopologyType $userArgsArray(type)
    }
    
    #validate type modification is allowed or not.
    if {[string equal $origTopologyType "router"] && ([string equal $newTopologyType "stub"] || [string equal $newTopologyType "external"])} {
        ::sth::sthCore::processError returnKeyedList "Modifying type from $origTopologyType to $newTopologyType is not permitted" {}
        set cmdState $FAILURE  
        return $returnKeyedList  
    } elseif {([string equal $origTopologyType "stub"] || [string equal $origTopologyType "external"]) && ([string equal $newTopologyType "router"]) } {
        ::sth::sthCore::processError returnKeyedList "Modifying type from $origTopologyType to $newTopologyType is not permitted" {}
        set cmdState $FAILURE  
        return $returnKeyedList  
    }
    
    set isisNbrHandles {}
    set isisNbrHandle "-1"
    set newNeighbor "0"
    set topologyType $newTopologyType
    switch -exact $newTopologyType {    
        router {
            if {([info exists userArgsArray(router_disconnect)] && $userArgsArray(router_disconnect)!= "")} {
                #process router_disconnect 
                set disconnectHandle $userArgsArray(router_disconnect)
                foreach isisHandle $isisHandles {
                    set cmdFailed 1
                    ::sth::IsIs::deleteIsIsNeighborInfo $isisHandle $disconnectHandle returnKeyedList cmdFailed
                    if {$cmdFailed} {
                        ::sth::sthCore::processError returnKeyedList "Error occured while deleting neighbor information" {}
                        set cmdState $FAILURE
                        return $returnKeyedList 
                    }
                }
            }
            if {([info exists userArgsArray(router_connect)] && $userArgsArray(router_connect) != "")} {    
                #Validate the LSP handle to be connected
                set routerConnectHandle $userArgsArray(router_connect)
                ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
                set msg ""
                if {![::sth::IsIs::IsIsIsLspHandleValid $routerConnectHandle msg]} {
                    ::sth::sthCore::processError returnKeyedList "The value $routerConnectHandle is not valid for the switch -router_connect ." {}
                    set cmdState $FAILURE
                    return $returnKeyedList        
                }  

                # Create the neighbor; if it already exists, do nothing.
                foreach isisHandle $isisHandles {
                    if {![::sth::IsIs::getIsIsNeighborHandle $isisHandle $userArgsArray(router_connect) isisNbrHandle]} {
                        #Create the IsisNeighbor under the isisLSP and then configure the other parameters.
                        if {[catch {set isisNbrHandle [::sth::sthCore::invoke stc::create IsisLspNeighborConfig -under $isisHandle]} createStatus]} {
                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating IsisLspNeighborConfig. Error: $createStatus" {}
                            set cmdState $FAILURE
                            return $FAILURE
                        }
                        set newNeighbor 1
                        lappend ISISLSPNEIGHBORLIST($isisHandle) $userArgsArray(router_connect)
                    }
                    lappend isisNbrHandles $isisNbrHandle
                }
            }
        }
        stub {
            set returnKey "network_stub"
        }
        external {
            set returnKey "external"        
        }
        default {
            ::sth::sthCore::processError returnKeyedList "The value $newTopologyType is not supported for switch -type ." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    #initializing the cmd specific data, validating switches and user input for each switch
    set cmdPassed 1
    ::sth::sthCore::log info "Processing the switches in priority order for command:$_hltCmdName"
        
    set priorityList [::sth::IsIs::processSwitches emulation_isis_topology_route_config ::sth::IsIs:: returnKeyedList modify funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $isisHandles $isisNbrHandles $topologyType]
        
        if {$cmdPassed <= 0} {
            break
        }
    }

    # Apply the modifications to IL
    if {[catch {::sth::sthCore::doStcApply } err]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while applying config. Error: $err" {}    
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #update the returnKeyledList with the IsIs Handle.
    if {![string equal $newTopologyType router]} {    
        set totalNetworkCount 0
        if {[string equal $ipVersion "6"] || [string equal $ipVersion "4_6"]} {
            foreach isisHandle $isisHandles {
                if {[catch {set networkCount [::sth::sthCore::invoke stc::get [lindex $ISISROUTEHNDLIST($isisHandle) 3] -ipv6networkblock.NetworkCount]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while obtaining the network block count from the route handle. Error: $getStatus" {}    
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                set totalNetworkCount [expr {$networkCount + $totalNetworkCount}]
            }
        }
        if {[string equal $ipVersion "4"] || [string equal $ipVersion "4_6"]} {
            foreach isisHandle $isisHandles {
                if {[catch {set networkCount [::sth::sthCore::invoke stc::get [lindex $ISISROUTEHNDLIST($isisHandle) 2] -ipv4networkblock.NetworkCount]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while obtaining the network block count from the route handle. Error: $getStatus" {}    
                    set cmdState $FAILURE
                    return $returnKeyedList
                }
                set totalNetworkCount [expr {$networkCount + $totalNetworkCount}]
            }
        }
        keylset returnKeyedList version $ipVersion $returnKey "num_networks $totalNetworkCount"
        set cmdState $SUCCESS
        return $returnKeyedList
    } else {
          set ipVersion $ISISLSPIPVER([lindex $isisHandles 0])
          set connectedHandles {}
          foreach isisHandle $isisHandles {
              set connectedHandles [concat $connectedHandles $ISISLSPNEIGHBORLIST($isisHandle)]
          }
        keylset returnKeyedList version $ipVersion router "connected_handles $connectedHandles"
        set cmdState $SUCCESS
        return $returnKeyedList
    }
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_delete (str args)
###\brief Process \em -mode switch with value \em delete for emulation_isis_topology_route_config cmd
###
###This procedure execute the emulation_isis_topology_route_config command when the mode is delete.
###
###\param[in] args This is the list of user configuration input.
###\return updatedKeyedList with isis route blk handles
###
###
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_topology_route_config_delete (str args);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_delete { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray

    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_procfunc
    variable ::sth::IsIs::emulation_isis_topology_route_configFunctionPriority
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    #Validate if the value of isis handle is valid
    if {(![info exists userArgsArray(elem_handle)] || $userArgsArray(elem_handle) == "")} {
          ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        #Validate the handle
        ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
        set msg ""
        set isisHandles $userArgsArray(elem_handle)
        foreach isisHandle $isisHandles {
            if {![::sth::IsIs::IsIsIsLspHandleValid $isisHandle msg]} {
                if {![::sth::IsIs::IsIsIsSessionRtBlkHandleValid $isisHandle msg]} {
                    if {[string equal $isisHandle SHA_NO_USER_INPUT] == 1} {
                        set isisHandle "{{}}"
                    }
                    ::sth::sthCore::processError returnKeyedList "The value $isisHandle is not valid for the switch -elem_handle ." {}
                    set cmdState $FAILURE
                    return $returnKeyedList             
                } else {
                    #get route type
                    set ipVersion [lindex $ISISROUTEHNDLIST($isisHandle) 1]
                    set isisRouteHandleList {}
                    if {[string equal $ipVersion "6"]} {
                        set isisRouteHandleList [lindex $ISISROUTEHNDLIST($isisHandle) 3]
                    } elseif {[string equal $ipVersion "4"]} {
                        set isisRouteHandleList [lindex $ISISROUTEHNDLIST($isisHandle) 2]
                    } elseif {[string equal $ipVersion "4_6"]} {
                        set isisRouteHandleList [list [lindex $ISISROUTEHNDLIST($isisHandle) 2] [lindex $ISISROUTEHNDLIST($isisHandle) 3]]
                    }
                    
                    foreach isisRouteHandle $isisRouteHandleList {
                        if { [catch {set routeType [::sth::sthCore::invoke stc::get $isisRouteHandle -routeType]} getStatus ] } {
                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting topology element:$isisHandle. Error: $getStatus" {}
                            set cmdState $FAILURE
                            return $returnKeyedList
                        }
                        break
                    }
                    
                    if {[string equal $routeType INTERNAL]} {
                        set origTopologyType "stub"
                    } elseif {[string equal $routeType EXTERNAL]} {
                        set origTopologyType "external"
                    } else {
                        ::sth::sthCore::processError returnKeyedList "Unsupported route_type: $routeType" {}
                        set cmdState $FAILURE
                        return $returnKeyedList                        
                    }
                }
            } else {
                set origTopologyType "router"    
            }
        }
    }
    
    switch -exact $origTopologyType {    
        router {
            #process router_delete 
            foreach isisHandle $isisHandles {
                if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting router $isisHandle. Error: $eMsg" {}
                    set cmdState $FAILURE
                    return $returnKeyedList
                } else {
                    catch {unset ISISROUTEHNDLIST($isisHandle)}
                    catch {unset ISISLSPNEIGHBORLIST($isisHandle)}
                    set tmpList [array get ISISLSPNEIGHBORLIST]
                    foreach {lspHandle lspNeighborList} $tmpList {
                        set currLspIndex [lsearch $lspNeighborList $isisHandle]
                        if {$currLspIndex >= 0} {
                            set lspNeighborList [lreplace $lspNeighborList $currLspIndex $currLspIndex]
                            set ISISLSPNEIGHBORLIST($lspHandle) $lspNeighborList
                        }
                    }
                }
            }
        }
        stub {
            #process router_delete 
            foreach isisHandle $isisHandles {
                set cmdFailed 1
                ::sth::IsIs::deleteIsIsIpRoute $isisHandle returnKeyedList cmdFailed
                if {$cmdFailed} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while deleting stub network $isisHandle" {}
                    set cmdState $FAILURE
                    return $returnKeyedList 
                } else {
                    ::sth::sthCore::log info "Successfully deleting stub network $isisHandle"
                    set returnKeyedList 
                }
            }
        }
        external {
            #process router_delete
            foreach isisHandle $isisHandles {
                set cmdFailed 1
                ::sth::IsIs::deleteIsIsIpRoute $isisHandle returnKeyedList cmdFailed
                if {$cmdFailed} {
                    ::sth::sthCore::processError returnKeyedList "Error occured while deleting external network $isisHandle" {}
                    set cmdState $FAILURE
                return $returnKeyedList 
                } else {
                    ::sth::sthCore::log info "Successfully deleting external network $isisHandle"
                }
            }
        }
        default {
            ::sth::sthCore::processError returnKeyedList "Unable to retrieve original type information: Unsupported Type $origTopologyType" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
 
    set cmdState $SUCCESS
    return $returnKeyedList
}
###}; //ending for namespace comment for doc


proc ::sth::IsIs::emulation_isis_lsp_generator_create { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr
    variable ::sth::IsIs::emulation_isis_lsp_generator_procfunc
    variable ::sth::IsIs::emulation_isis_lsp_generatorFunctionPriority
    variable ::sth::IsIs::emulation_isis_lsp_generator_router_routing_level_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    variable ::sth::IsIs::ISISROUTECOUNT
    variable ::sth::IsIs::IsisLspGenParams_Handler

    set _OrigHltCmdName "emulation_isis_lsp_generator"
    set _hltCmdName "emulation_isis_lsp_generator_create"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    #Validate the value of isis handle
    if {![info exists userArgsArray(handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set isisRouterHandle $userArgsArray(handle)
    }

    #check the internal_prefix_length_dist
    if {"CUSTOM" == $userArgsArray(internal_prefix_length_dist_type)} {
        set distList [split $userArgsArray(internal_prefix_length_dist) " "]
        if {[llength $distList] > 32} {
                ::sth::sthCore::processError returnKeyedList "Invalid internal_prefix_length_dist: no more than 32 numbers" {}
                set cmdState $FAILURE
                return $returnKeyedList 
        }
        set distSum 0
        foreach dist $distList {
                set  distSum [expr {$distSum +  $dist}]       
        }
        if {$distSum != 100} {
                ::sth::sthCore::processError returnKeyedList "Invalid internal_prefix_length_dist: the summary should be 100" {}
                set cmdState $FAILURE
                return $returnKeyedList         
        }
    }
    if {"CUSTOM" == $userArgsArray(external_prefix_length_dist_type)} {
        set distList [split $userArgsArray(external_prefix_length_dist) " "]
        if {[llength $distList] > 32} {
                ::sth::sthCore::processError returnKeyedList "Invalid external_prefix_length_dist: no more than 32 numbers" {}
                set cmdState $FAILURE
                return $returnKeyedList 
        }
        set distSum 0
        foreach dist $distList {
                set  distSum [expr {$distSum +  $dist}]       
        }
        if {$distSum != 100} {
                ::sth::sthCore::processError returnKeyedList "Invalid external_prefix_length_dist: the summary should be 100" {}
                set cmdState $FAILURE
                return $returnKeyedList         
        }
    }
    #get the type for configuration
    if {![info exists userArgsArray(type)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -type is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set topologyType $userArgsArray(type)
    }
    
    #get IP version for this router
    set ipVersion 4
    if {[catch {set childrenIpInfo [::sth::sthCore::invoke stc::get [lindex $isisRouterHandle 0] -children]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisRouterHandle" {}
        set cmdState $FAILURE
        return $returnKeyedList
    } else {
        if {[regexp -nocase {ipv6} $childrenIpInfo]} {
            set ipVersion 6
            if {[regexp -nocase {ipv4} $childrenIpInfo]} {
                set ipVersion "4_6"        
            }
        }
    }

    #here need each procfunc to process and config relative parameters
    
    set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedList create funcSwitchList]
    array set funcSwitchArray $funcSwitchList
    foreach functionPriority $priorityList {
        set functionName [lindex $functionPriority 0]
        set cmdPassed [$functionName $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $isisRouterHandle $ipVersion $topologyType]
            
        if {$cmdPassed == $FAILURE} {
            break
        }
    }

    if {[catch {::sth::sthCore::invoke stc::perform RouteGenApply -GenParams $IsisLspGenParams_Handler} status]} {
        ::sth::sthCore::processError returnKeyedList "Internal command error while adding the LSP. Error: $status" {}
        set cmdState $FAILURE
        return $returnKeyedList
    }

    if ([info exists cmdPassed]) {
        set cmdState $cmdPassed
    } else {
        set cmdState $SUCCESS    
    }
   
    # fix DE15223 Unable to perform periodic ISIS route flapping for the routes generated using sth::emulation_isis_lsp_generator.
    # Update array ISISROUTEHNDLIST , emulation_isis_control_flap will get IsisIpv4RouteHandle and IsisIpv6RouteHandle in this array.
    set IsisIpv4RouteHandle ""
    set IsisIpv6RouteHandle ""
    set IsisLspHnd ""

    if {([string equal $ipVersion 4] || [string equal $ipVersion "4_6"])} {
        set  ISISROUTEHNDLIST_tmp [::sth::IsIs::emulation_isis_lsp_generator_update_routehndlst "4" $IsisLspGenParams_Handler]
        set isislspconfigHnd [lindex $ISISROUTEHNDLIST_tmp 0]
        set IsisIpv4RouteHandle [lindex $ISISROUTEHNDLIST_tmp 1]
    }
    if {([string equal $ipVersion 6] || [string equal $ipVersion "4_6"])} {
        set  ISISROUTEHNDLIST_tmp [::sth::IsIs::emulation_isis_lsp_generator_update_routehndlst "6" $IsisLspGenParams_Handler]
        set isislspconfigHnd [lindex $ISISROUTEHNDLIST_tmp 0]
        set IsisIpv6RouteHandle [lindex $ISISROUTEHNDLIST_tmp 1]
    }
            
set ISISROUTEHNDLIST($IsisLspGenParams_Handler) [list $isislspconfigHnd $ipVersion $IsisIpv4RouteHandle $IsisIpv6RouteHandle]   

    # return all Ipv4NetworkBlock and Ipv6NetworkBlock

    if { $userArgsArray(get_return_handles) == "true" } {
        set lsp_handle {}
        set ipv4_lsp_handle {}
        set ipv6_lsp_handle {}
        foreach ipVer $ipVersion {   
            set sub_object_iproute ""
            set sub_object_block ""
            append  sub_object_iproute  "Ipv" "$ipVer" "IsisRoutesConfig"
            append  sub_object_block  "Ipv" "$ipVer" "NetworkBlock"
            
            if {[llength $isisRouterHandle] == 1} {
                if {[catch {set IsisRouterConfigString [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisRouterHandle $getStatus" {}
                    return $FAILURE
                }
    
                set IsisRouterConfigList [split $IsisRouterConfigString " "]
                foreach IsisRouterConfigHandle $IsisRouterConfigList {
                    if {[catch {set IsisLspConfigString [::sth::sthCore::invoke stc::get $IsisRouterConfigHandle -children-IsisLspConfig]} getStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisRouterConfigHandle $getStatus" {}
                        return $FAILURE
                    }
                    set IsisLspConfigList [split $IsisLspConfigString " "]
                    foreach IsisLspConfigHandle $IsisLspConfigList {
                        if {[catch {set IsisLspConfigChilrenString [::sth::sthCore::invoke stc::get $IsisLspConfigHandle -children]} getStatus]} {
                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisLspConfigHandle $getStatus" {}
                            return $FAILURE
                        }
                        if {[regexp  {ipv[4|6]isisroutesconfig} $IsisLspConfigChilrenString]} {
                            if {[catch {set IsisIpRoutesString [::sth::sthCore::invoke stc::get $IsisLspConfigHandle -children-$sub_object_iproute]} getStatus]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisLspConfigHandle $getStatus" {}
                                return $FAILURE
                            }
                            set IsisIpRoutesList [split $IsisIpRoutesString " "]
                            foreach IsisIpRoutesHandle $IsisIpRoutesList {
                                if {[catch {set IsisblockHandle [::sth::sthCore::invoke stc::get $IsisIpRoutesHandle -children-$sub_object_block]} getStatus]} {
                                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisIpRoutesHandle $getStatus" {}
                                    return $FAILURE
                                }
                                lappend  lsp_handle  $IsisblockHandle
                                if {[string equal $ipVer "4"]} {
                                    lappend  ipv4_lsp_handle  $IsisblockHandle
                                } elseif {[string equal $ipVer "6"]} {
                                    lappend  ipv6_lsp_handle  $IsisblockHandle
                                }
                            }
                        }
                    }
                }
            } else {
                if {[string equal $ipVer "4"]} {
                    array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv4NetworkBlock -rootlist $isisRouterHandle]
                    set ipv4_lsp_handle $rtn(-ObjectList)
                } elseif {[string equal $ipVer "6"]} {
                    array set rtn [::sth::sthCore::invoke stc::perform GetObjectsCommand -className Ipv6NetworkBlock -rootlist $isisRouterHandle]
                    set ipv6_lsp_handle $rtn(-ObjectList)
                }
                lappend  lsp_handle $rtn(-ObjectList)
            }
            if {[string equal $ipVer "4"]} {
                keylset returnKeyedList ipv4_lsp_handle $ipv4_lsp_handle
            } elseif {[string equal $ipVer "6"]} {
                keylset returnKeyedList ipv6_lsp_handle $ipv6_lsp_handle
            }
        }

        keylset returnKeyedList lsp_handle $lsp_handle
    }
    
    return $returnKeyedList       
}
# add this function for update ISISROUTEHNDLIST 
proc ::sth::IsIs::emulation_isis_lsp_generator_update_routehndlst {ipversion IsisLspGenParams_Handler} {
    set IsisIpRouteHandle {}
    set IsisLspHnd {}
    set returnVlaue {}
    set RouteHandles [::sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -selectedrouterrelation-targets]
    foreach RouteHandle $RouteHandles {
        set isisrouterHndList [::sth::sthCore::invoke stc::get $RouteHandle -children-isisrouterconfig]
        foreach isisrouteconfigHnd $isisrouterHndList {
            set isislspconfigHnds [::sth::sthCore::invoke stc::get $isisrouteconfigHnd -children-isislspconfig]
                foreach isislspconfigHnd $isislspconfigHnds {
                    set IsisLspHnd [concat $IsisLspHnd $isislspconfigHnd]
                    if {[string equal $ipversion "4"]} {
                        set IsisIpRouteHandle [concat $IsisIpRouteHandle [::sth::sthCore::invoke stc::get $isislspconfigHnd -children-ipv4isisroutesconfig ]]
                   } elseif {[string equal $ipversion "6"]} {
                       set IsisIpRouteHandle [concat $IsisIpRouteHandle [::sth::sthCore::invoke stc::get $isislspconfigHnd -children-ipv6isisroutesconfig ]]
                   }
                }
        }
    }
    lappend returnVlaue $IsisLspHnd
    lappend returnVlaue $IsisIpRouteHandle
    return $returnVlaue
}


proc ::sth::IsIs::emulation_isis_lsp_generator_modify { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr
    variable ::sth::IsIs::emulation_isis_lsp_generator_procfunc
    variable ::sth::IsIs::emulation_isis_lsp_generatorFunctionPriority
    variable ::sth::IsIs::emulation_isis_lsp_generator_router_routing_level_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    variable ::sth::IsIs::ISISROUTECOUNT
    variable ::sth::IsIs::IsisLspGenParams_Handler

    set _OrigHltCmdName "emulation_isis_lsp_generator"
    set _hltCmdName "emulation_isis_lsp_generator_modify"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    #get the type for configuration
    set topologyType none
    #get IP version for this router
    set ipVersion 4

    #Validate the value of isis handle
    if {![info exists userArgsArray(elem_handle)]} {
        ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set isisLspHandle $userArgsArray(elem_handle)
    }

    if {[regexp -nocase {ipv4networkblock|ipv6networkblock} $isisLspHandle]} {
        if {[regexp -nocase {ipv6} $isisLspHandle]} {
                set ipVersion 6
                if {[regexp -nocase {ipv4} $isisLspHandle]} {
                        set ipVersion "4_6"
                }
        }
        #here need each procfunc to process and config relative parameters
        set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedList modify funcSwitchList]
        array set funcSwitchArray $funcSwitchList
        foreach functionPriority $priorityList {
            set functionName [lindex $functionPriority 0]
            set functionName_modify $functionName
            append functionName_modify "_modify"
            set cmdPassed [$functionName_modify $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $isisLspHandle $ipVersion $topologyType]
            if {$cmdPassed == $FAILURE} {
                break
            }
        }
    } else {
        if {[catch {set isisRouterHandle [::sth::sthCore::invoke stc::get $isisLspHandle -selectedrouterrelation-Targets]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisLspHandle" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        foreach isisRouterHandle $isisRouterHandle {
            if {[catch {set childrenIpInfo [::sth::sthCore::invoke stc::get $isisRouterHandle -children]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisRouterHandle" {}
                set cmdState $FAILURE
                return $returnKeyedList
            } else {
                if {[regexp -nocase {ipv6} $childrenIpInfo]} {
                    set ipVersion 6        
                }
            }
        }
    
        #here need each procfunc to process and config relative parameters
        set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedList modify funcSwitchList]
        array set funcSwitchArray $funcSwitchList
        foreach functionPriority $priorityList {
            set functionName [lindex $functionPriority 0]
            set functionName_modify $functionName
            append functionName_modify "_modify"
            set cmdPassed [$functionName_modify $funcSwitchArray($functionName) returnKeyedList $_hltCmdName $funcSwitchArray($functionName) $isisLspHandle $ipVersion $topologyType]
                
            if {$cmdPassed == $FAILURE} {
                break
            }
        }
        if {[catch {::sth::sthCore::invoke stc::perform RouteGenApply -GenParams $IsisLspGenParams_Handler} status]} {
            ::sth::sthCore::processError returnKeyedList "Internal command error while adding the LSP. Error: $status" {}
            set cmdState $FAILURE
            return $returnKeyedList
            }
        if ([info exists cmdPassed]) {
            set cmdState $cmdPassed
        } else {
            set cmdState $SUCCESS    
        }
        
        # return all Ipv4NetworkBlock
            
        set lsp_handle {}
        set sub_object_iproute ""
        set sub_object_block ""
        append  sub_object_iproute  "Ipv" "$ipVersion" "IsisRoutesConfig"
        append  sub_object_block  "Ipv" "$ipVersion" "NetworkBlock"
        if {[catch {set IsisRouterConfigString [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisRouterHandle $getStatus" {}
            return $FAILURE
        }
        
        set IsisRouterConfigList [split $IsisRouterConfigString " "]
        foreach IsisRouterConfigHandle $IsisRouterConfigList {
            if {[catch {set IsisLspConfigString [::sth::sthCore::invoke stc::get $IsisRouterConfigHandle -children-IsisLspConfig]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisRouterConfigHandle $getStatus" {}
                    return $FAILURE
            }
            set IsisLspConfigList [split $IsisLspConfigString " "]
            foreach IsisLspConfigHandle $IsisLspConfigList {
                    if {[catch {set IsisLspConfigChilrenString [::sth::sthCore::invoke stc::get $IsisLspConfigHandle -children]} getStatus]} {
                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisLspConfigHandle $getStatus" {}
                            return $FAILURE
                    }
                    if {[regexp  {ipv[4|6]isisroutesconfig} $IsisLspConfigChilrenString]} {
                            if {[catch {set IsisIpRoutesString [::sth::sthCore::invoke stc::get $IsisLspConfigHandle -children-$sub_object_iproute]} getStatus]} {
                                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisLspConfigHandle $getStatus" {}
                                    return $FAILURE
                            }
                            set IsisIpRoutesList [split $IsisIpRoutesString " "]
                            foreach IsisIpRoutesHandle $IsisIpRoutesList {
                                    if {[catch {set IsisblockHandle [::sth::sthCore::invoke stc::get $IsisIpRoutesHandle -children-$sub_object_block]} getStatus]} {
                                            ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisIpRoutesHandle $getStatus" {}
                                            return $FAILURE
                                    }
                                    lappend  lsp_handle  $IsisblockHandle
                            }
                    }
                    
            }                
        }
        keylset returnKeyedList lsp_handle $lsp_handle
    }

    # Update array ISISROUTEHNDLIST for modify, emulation_isis_control_flap will get IsisIpv4RouteHandle and IsisIpv6RouteHandle in this array.
    if {[keylget returnKeyedList status] == 1} {
    set IsisIpv4RouteHandle ""
    set IsisIpv6RouteHandle ""
    set IsisLspHnd ""
    if {[info exist ISISROUTEHNDLIST($IsisLspGenParams_Handler) ]} {
        unset ISISROUTEHNDLIST($IsisLspGenParams_Handler)  
    }
    if {([string equal $ipVersion 4] || [string equal $ipVersion "4_6"])} {
        set  ISISROUTEHNDLIST_tmp [::sth::IsIs::emulation_isis_lsp_generator_update_routehndlst "4" $IsisLspGenParams_Handler]
        set isislspconfigHnd [lindex $ISISROUTEHNDLIST_tmp 0]
        set IsisIpv4RouteHandle [lindex $ISISROUTEHNDLIST_tmp 1]
    }
    if {([string equal $ipVersion 6] || [string equal $ipVersion "4_6"])} {
        set  ISISROUTEHNDLIST_tmp [::sth::IsIs::emulation_isis_lsp_generator_update_routehndlst "6" $IsisLspGenParams_Handler]
        set isislspconfigHnd [lindex $ISISROUTEHNDLIST_tmp 0]
        set IsisIpv6RouteHandle [lindex $ISISROUTEHNDLIST_tmp 1]
    }
  
    set ISISROUTEHNDLIST($IsisLspGenParams_Handler) [list $isislspconfigHnd $ipVersion $IsisIpv4RouteHandle $IsisIpv6RouteHandle]
    }  
    return $returnKeyedList
}



proc ::sth::IsIs::DeleteNeighborLsp {isisRouterHandle} {
        
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    if {[catch {set IsisRouterConfigString [::sth::sthCore::invoke stc::get $isisRouterHandle -children-IsisRouterConfig]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisRouterHandle $getStatus" {}
        return $FAILURE
    }
    
    set IsisRouterConfigList [split $IsisRouterConfigString " "]
    foreach IsisRouterConfigHandle $IsisRouterConfigList {
        if {[catch {set IsisLspConfigString [::sth::sthCore::invoke stc::get $IsisRouterConfigHandle -children-IsisLspConfig]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $IsisRouterConfigHandle $getStatus" {}
                return $FAILURE
        }
        set IsisLspConfigList [split $IsisLspConfigString " "]
        foreach IsisLspConfigHandle $IsisLspConfigList {
                if {[catch {::sth::sthCore::invoke stc::delete $IsisLspConfigHandle} eMsg ]} {
                        ::sth::sthCore::processError returnKeyedList "delete $IsisLspConfigHandle failed: $eMsg" {}
                        return $FAILURE
                }
        }                
    }
    return $SUCCESS
}

proc ::sth::IsIs::emulation_isis_lsp_generator_delete { returnKeyedListVarName cmdStatusVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::userArgsArray

    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr
    variable ::sth::IsIs::emulation_isis_lsp_generator_procfunc
    variable ::sth::IsIs::emulation_isis_lsp_generatorFunctionPriority
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _OrigHltCmdName "emulation_isis_lsp_generator"
    set _hltCmdName "emulation_isis_lsp_generator_delete"

    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName {$_hltCmdName}"
    
    if {(![info exists userArgsArray(elem_handle)] || $userArgsArray(elem_handle) == "")} {
          ::sth::sthCore::processError returnKeyedList "The switch -elem_handle is a mandatory switch." {}
        set cmdState $FAILURE
        return $returnKeyedList        
    } else {
        set msg ""
        set isisLspHandles $userArgsArray(elem_handle)
        if {[regexp -nocase {IsisLspConfig\d+} $isisLspHandles]} {
                foreach isisHandle $isisLspHandles {
                        if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg ]} {
                                ::sth::sthCore::processError returnKeyedList "delete $isisHandle failed: $eMsg" {}
                                return $FAILURE
                        }
                }
        } else {
                foreach isisHandle $isisLspHandles {
                        if {[catch {set IsisrouterHandle [::sth::sthCore::invoke stc::get $isisHandle -selectedrouterrelation-Targets]} getStatus]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the children from object $isisHandle $getStatus" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                        }
                        ::sth::IsIs::DeleteNeighborLsp $IsisrouterHandle
                        
                        if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg ]} {
                                ::sth::sthCore::processError returnKeyedList "delete $isisHandle failed: $eMsg" {}
                                set cmdState $FAILURE
                                return $returnKeyedList
                        }
                        # update array ISISROUTEHNDLIST for lsp_generator_delete
                        if {[info exist ISISROUTEHNDLIST($isisHandle) ]} {
                            unset ISISROUTEHNDLIST($isisHandle)
                        }
                }
        }
    }
    set cmdState $SUCCESS
    return $returnKeyedList
}
###}; //ending for namespace comment for doc



##########################################################
#ISIS switch helper functions
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
proc ::sth::IsIs::processSwitches {hltapiCommand myNameSpace returnKeyValue mode switchArrayList} {
    
    upvar $returnKeyValue returnKeyedList
    upvar $switchArrayList functionswitcharrayList
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    array set userArgsArray [array get $myNameSpace\userArgsArray]
    array set procfuncarray [array get $myNameSpace$hltapiCommand\_procfunc]
    array set priorityarray [array get $myNameSpace$hltapiCommand\_priority]
    if {[string equal $mode create]} {
        catch {unset userArgsArray(mandatory_args)}
        catch {unset userArgsArray(optional_args)}
        set switchNameList [array names userArgsArray]
    } elseif {[string equal $mode modify]} {
        set tmpList $userArgsArray(optional_args)
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
#         puts "$switchName: $functionName"
        if {($functionName != "" && ![string equal $functionName "_none_"])} {
            if {$userArgsArray($switchName)!=""} {
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

###/*! \ingroup isishelperfuncs
###\fn createConfigStartIsIsSession (str args, KeyedListRef returnStringName)
###\brief Create, Config and Start IsIs Sesssion
###
###This procedure create a ISIS Session, configure it with the users input and finally starts it. 
###
###\param[in] args This is the list of user configuration input excluding the step related switches.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2, in fact we don't start the session
### anymore.
###*/
###
###createConfigStartIsIsSession (str args, KeyedListRef returnStringName);
###

proc ::sth::IsIs::createConfigStartIsIsSession { returnStringName cmdStateVarName rtID} {

        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        
        variable userArgsArray
        variable ::sth::IsIs::ISISLSPIPVER
        variable emulation_isis_config_stcobj
        variable emulation_isis_config_stcattr
        variable emulation_isis_config_procfunc
        variable emulation_isis_configFunctionPriority
        variable ::sth::IsIs::useDefaultSystemId
        variable ::sth::GBLHNDMAP

        ::sth::sthCore::log debug "Executing CreateConfigStartIsIsSession command for: emulation_isis_config {emulation_isis_config_create}"

        upvar 1 $returnStringName returnKeyedList
        upvar 1 $cmdStateVarName errOccured
        
        if {[info exists userArgsArray(port_handle)]} {
                if {[info exists userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} {
                        set baseIf "Aal5If"
                } else {
                        set baseIf "EthIIIf"    
                }
                if {[string equal $userArgsArray(ip_version) 4]} {
                        set topIf "Ipv4If"
                } else {
                        set topIf "Ipv6If"
                }
                
                set IfStack "$topIf $baseIf"
                set IfCount "1 1"
                
                if {$baseIf == "EthIIIf"} {
                        if {$userArgsArray(vlan) == 1} {
                                # there is vlan
                                if {[info exists userArgsArray(vlan_id)]} {
                                        set IfStack "$topIf VlanIf $baseIf"
                                         set IfCount "1 1 1"
                                        if {[info exists userArgsArray(vlan_outer_id)]} {
                                                set IfStack "$topIf VlanIf VlanIf $baseIf"
                                                set IfCount "1 1 1 1"
                                        }
                                }
                        }
                }
                # create the router and interface stack
                if {[catch {array set DeviceCreateOutput [::sth::sthCore::invoke stc::perform DeviceCreate -ParentList $GBLHNDMAP(project) -DeviceType Router -IfStack $IfStack -IfCount $IfCount -Port $userArgsArray(port_handle)]
                            set isisRouterHandle $DeviceCreateOutput(-ReturnList)} createStatus]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Isis Router. Error: $createStatus" {}
                    set errOccured 1
                    return
                }
        
                if {[string match *6 $userArgsArray(ip_version)]} {
                        if {[catch {set ipv6ResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-Ipv6If]} getStatus]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting ipv6if handle from Isis Router. Error: $getStatus" {}
                                set errOccured 1
                                return
                        }
                        # create link-local interface
                        if {[catch {set AttachToIf [::sth::sthCore::invoke stc::get $ipv6ResultIf -stackedonendpoint-Targets]} getStatus]} {
                                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting ipv6if attach stack from Isis Router. Error: $getStatus" {}
                                set errOccured 1
                                return
                        }
                        if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $isisRouterHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $AttachToIf} status]} {
                                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while adding the IPV6 interface. Error: $status" {}
                                set cmdFailed 1
                                return
                        }
                        if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
                                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV6 interface. Error: $getStatus" {}
                                set cmdFailed 1
                                return
                        }
                        set ipv6ifLocal [lindex $ipv6ifList 1]
#                        set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                        set linkLocalIp "FE80:0:0:0"
#                        foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                                append linkLocalIp ":$num1$num2$num3$num4"
#                        }
                        if {[catch {
                            ::sth::sthCore::invoke stc::config $ipv6ifLocal -Address FE80::2
                            ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                        } configStatus]} {
                                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while configuring the IPV6 link local address. Error: $configStatus" {}
                                set cmdFailed 1
                                return
                        }
                }
        } else {
                set isisRouterHandle $userArgsArray(handle)
        }
        # Create the ISIS router configuration under the router and then configure the other parameters.
        if {[catch {array set ProtocolCreateOutput [::sth::sthCore::invoke stc::perform ProtocolCreate -ParentList $isisRouterHandle  -CreateClassId [string tolower IsisRouterConfig]]
                              set isisSessionHandle $ProtocolCreateOutput(-ReturnList)} createStatus]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Isis Protocol. Error: $createStatus" {}
            set errOccured 1
            return
        }
        ::sth::sthCore::log info "The IsisRouter:$isisSessionHandle was successfully created"
        
        #Create the IsisLSP under the isissession
        set isisLspHandle ""
        if {[info exists userArgsArray(enable_isis_lsp)]&& $userArgsArray(enable_isis_lsp) == 1} {
                if {[catch {set isisLspHandle [::sth::sthCore::invoke stc::create IsisLspConfig -under $isisSessionHandle]} createStatus]} {
                        ::sth::sthCore::processError returnKeyedList "Internal Command Error while creating Isis Lsp. Error: $createStatus" {}
                        set errOccured 1
                        return
                }
                set ISISLSPIPVER($isisLspHandle) $userArgsArray(ip_version)
                ::sth::sthCore::log info "The IsisRouter:$isisLspHandle was successfully created under isisRouter:$isisSessionHandle"
        }
        ###add for gre
        if {[info exists userArgsArray(tunnel_handle)]} {
               set greTopIf [::sth::sthCore::invoke stc::get $isisRouterHandle -TopLevelIf-targets]
               set greLowerIf [::sth::sthCore::invoke stc::get $greTopIf -StackedOnEndpoint-targets]
               
           ###create the gre stack and setup the relation
               if {[catch {::sth::createGreStack $userArgsArray(tunnel_handle) $isisRouterHandle $greLowerIf $rtID} greIf]} {
                       ::sth::sthCore::processError returnKeyedList "::sth::sthCore::createGreStack Failed: $greIf" {}
                       return $::sth::sthCore::FAILURE
               }
       
        #stack the top ipif on greif
               ::sth::sthCore::invoke stc::config $greTopIf "-StackedOnEndpoint-targets $greIf"
        }
        # Configure default system id
        #   If system id is not specified, or is empty string, or is zero, set system id based to 0x0200<intf_ip_address>
        if {(![info exists userArgsArray(system_id)] || $userArgsArray(system_id) == "" || $userArgsArray(system_id) == 0)} {
           updateDefaultSystemId $isisRouterHandle
        }
   
        #Configure the created IsisRouter with user input (options)
        ::sth::sthCore::log info "Processing the switches in priority order for command: emulation_isis_config_create"
        # First of all, create the lists which holds the switchs that can be configured using the same function, call each function only once.
        set cmdPass 1
        set priorityList [::sth::IsIs::processSwitches emulation_isis_config ::sth::IsIs:: returnKeyedList create funcSwitchList]
        array set funcSwitchArray $funcSwitchList
        foreach functionPriority $priorityList {
           set functionName [lindex $functionPriority 0]
           if {[string equal $isisLspHandle ""]&&[string match {*metric} $functionName]} {
                set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_isis_config $funcSwitchArray($functionName) $isisRouterHandle $isisSessionHandle $isisSessionHandle]
                } elseif {[string equal $isisLspHandle ""]&&[string match {*lsp} $functionName]} {
                        continue
                } else {
                set cmdPass [$functionName $funcSwitchArray($functionName) returnKeyedList emulation_isis_config $funcSwitchArray($functionName) $isisRouterHandle $isisSessionHandle $isisLspHandle]
                }          
                      
           if {$cmdPass <= 0} {
               #break
               set errOccured 1
               return
            }
        }
        
        #enable/disable BFD
        if {[info exists userArgsArray(bfd_registration)]} {
                configBfdRegistration $isisRouterHandle $userArgsArray(mode)
                #bfd relation
                set bfdRtrCfg [::sth::sthCore::invoke stc::get $isisRouterHandle -children-bfdrouterconfig]
                if {[llength $bfdRtrCfg] != 0} {
                        if {[string equal $userArgsArray(ip_version) 4]} {
                                set ipResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv4if]
                        } else {
                                #For Ipv6, get the global link IPv6if
                                set ipResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]
                                set ipResultIf [lindex $ipResultIf 0]
                        }
                        ::sth::sthCore::invoke stc::config $bfdRtrCfg "-UsesIf-targets $ipResultIf"      
                }
        }
        

        set errOccured 0
        return [list $isisRouterHandle $isisLspHandle]
}
###/*! \ingroup isishelperfuncs
###\fn deleteIsIsNeighborInfo (str handleVar, str neighborHandleVar, KeyedListRef returnStringName)
###\brief delete Isis neighbor info
###
###This procedure delete Isis neighbor information of the correspond lsp. 
###
###\param[in] args Hanlde of IsisLsp object which need for the deletion of its neighbor.
###\param[in] args Hanlde of IsisLsp object which is to be deleted neighbor.
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###deleteIsIsNeighborInfo (str handleVar, str neighborHandleVar, KeyedListRef returnStringName);
###

proc ::sth::IsIs::deleteIsIsNeighborInfo { handleVar neighborHandleVar returnStringName cmdStateVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST

    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_modify"

    ::sth::sthCore::log debug "Excuting deleteIsIsNeighborInfo command for: $_OrigHltCmdName {$_hltCmdName}"

    upvar 1 $returnStringName returnKeyedList
    upvar 1 $cmdStateVarName errOccured

    #Validate the handle 
    if {![::sth::IsIs::IsIsIsLspHandleValid $neighborHandleVar msg]} {
         ::sth::sthCore::processError returnKeyedList "The value $neighborHandleVar is not a valid value for switch -router_disconnect ." {}
        set errOccured 1
        return $returnKeyedList  
    }        
    #get nbrHandle
    if {![::sth::IsIs::getIsIsNeighborHandle $handleVar $neighborHandleVar nbrHandle]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while process router_diconnect $neighborHandleVar:  Can not find corresponding neighbor information from element $handleVar" {}
        set errOccured 1
        return $FAILURE         
    }
    
    #Delete the IsisNeighbor Object
    if {[catch {::sth::sthCore::invoke stc::delete $nbrHandle} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while process router_diconnect $nbrHandle. Error: $eMsg" {}
        set errOccured 1
        return $FAILURE
    } else {
        set currNeighborList $ISISLSPNEIGHBORLIST($handleVar)
        set neighborIndex [lsearch $currNeighborList $neighborHandleVar]
        if {$neighborIndex >= 0} {
            set ISISLSPNEIGHBORLIST($handleVar) [lreplace $currNeighborList $neighborIndex $neighborIndex]
        }
    }

    set errOccured 0
    return $SUCCESS
}



###/*! \ingroup isishelperfuncs
###\fn deleteIsIsRouter (str handleVar, KeyedListRef returnStringName)
###\brief delete ISIS router
###
###This procedure delete isisLSP.  It will remove all other LSP neighbor information which connect to it. 
###
###\param[in] args Hanlde of IsisLsp object which will be delete
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
###deleteIsIsRouter (str handleVar, KeyedListRef returnStringName);
###

proc ::sth::IsIs::deleteIsIsRouter { handleVar returnStringName cmdStateVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_delete"

    ::sth::sthCore::log debug "Excuting deleteIsIsRouter command for: $_OrigHltCmdName {$_hltCmdName}"

    upvar 1 $returnStringName returnKeyedList
    upvar 1 $cmdStateVarName errOccured

    set isisHandle $handleVar

    #Delete the isisLSP Object
    if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} eMsg ]} {
     ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting router $isisHandle. Error: $eMsg" {}
     set errOccured 1
     return $FAILURE
    }

    set errOccured 0
    return $SUCCESS
}

###/*! \ingroup isishelperfuncs
###\fn deleteIsIsIpRoute (str handleVar, KeyedListRef returnStringName)
###\brief delete ISIS route
###
###This procedure delete isisIpRoute. 
###
###\param[in] args Hanlde of IsisIpRoute object which will be delete
###\param[in,out] returnStringName This is the reference to the keyedklist which will be returned to the user.
###
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
###deleteIsIsIpRoute (str handleVar, KeyedListRef returnStringName);
###

proc ::sth::IsIs::deleteIsIsIpRoute { handleVar returnStringName cmdStateVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::ISISROUTEHNDLIST

    set _OrigHltCmdName "emulation_isis_topology_route_config"
    set _hltCmdName "emulation_isis_topology_route_config_delete"

    ::sth::sthCore::log debug "Excuting deleteIsIsIpRoute command for: $_OrigHltCmdName {$_hltCmdName}"

    upvar 1 $returnStringName returnKeyedList
    upvar 1 $cmdStateVarName errOccured

    set isisHandle $handleVar
    
    set isisRouteHandleInfo $ISISROUTEHNDLIST($isisHandle)
    
    set ipv4Handle [lindex $isisRouteHandleInfo 2]
    set ipv6Handle [lindex $isisRouteHandleInfo 3]

    #Delete the isisLSP Object
    
    if {$ipv4Handle != ""} {
        if {[catch {::sth::sthCore::invoke stc::delete $ipv4Handle} eMsg ]} {
         ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting network topology element $isisHandle. Error: $eMsg" {}
         set errOccured 1
         return $FAILURE
        } else {
            set ISISROUTEHNDLIST($isisHandle) [lreplace $ISISROUTEHNDLIST($isisHandle) 2 2 ""]
        }
    }
    
    if {$ipv6Handle != ""} {
        if {[catch {::sth::sthCore::invoke stc::delete $ipv6Handle} eMsg ]} {
         ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting network topology element $isisHandle. Error: $eMsg" {}
         set errOccured 1
         return $FAILURE
        } else {
#             puts "list=$ISISROUTEHNDLIST($isisHandle)"
            set ISISROUTEHNDLIST($isisHandle) [lreplace $ISISROUTEHNDLIST($isisHandle) 3 3 ""]
        }
    }
    
    # Unset the isis route handle array
    if {[catch {unset ISISROUTEHNDLIST($isisHandle)} eMsg]} {
         ::sth::sthCore::processError returnKeyedList "Internal Command Error while deleting network topology element $isisHandle. Error: $eMsg" {}
        set errOccured 1
        return $FAILURE
    }
    set errOccured 0
    return $SUCCESS
}
###/*! \ingroup isishelperfuncs
### \fn IsIsIsSessionHandleValid (str handle, varRef msgName)
###\brief Validates value against isis_handle
###
###This procedure checks if the value is valid router handle, furthermore,
### whether this router handle has IsisRouterConfig child.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
### IsIsIsSessionHandleValid (str handle, varRef msgName);
###

proc ::sth::IsIs::IsIsIsSessionHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg        
    
    if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $handle -children-IsisRouterConfig]} errorMsg]} {
        return $FAILURE
    } else {
        if {[llength $isisSessionHandle] <= 0} {
            set errorMsg -1
            return $FAILURE
        } else {
            set errorMsg $isisSessionHandle
            return $SUCCESS
        }
    }
}

###/*! \ingroup isishelperfuncs
### \fn IsIsIsSessionHandleValid (str handle, varRef msgName)
###\brief Validates value against isis_handle
###
### This procedure checks if the port affiliates to 
### a router which runs IsIs protocol, if yes, output 
### the handle of the router
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
### IsIsIsPortValid (str handle, varRef msgName);
###

proc ::sth::IsIs::IsIsIsPortValid { handle RouterHandleList } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $RouterHandleList routerHandleList 
    
    set routerHandle -1
    set routerHandleList [list]
    if {[catch {set routerList [::sth::sthCore::invoke stc::get $handle -affiliationport-Sources]} errorMsg]} {
        set errorMsg "Port handle $handle not valid"
        return $FAILURE
    } else {
        if {[llength $routerList] <= 0} {
            set errorMsg "There is no router affiliated to the port $handle"
            return $FAILURE
        } else {
            foreach routerHandle $routerList {
                if {[catch {set isiuserArgsArray [::sth::sthCore::invoke stc::get $routerHandle -children-IsisRouterConfig]} errorMsg]} {
                } else {
                    if {[string first isisrouterconfig $isiuserArgsArray] >= 0} {
                        lappend routerHandleList $routerHandle
                    }
                }
            }
        }
    }
    if {[llength $routerHandleList] > 0} {
        return $SUCCESS
    } else {
        set errorMsg "There is no ISIS router affiliated to the port $handle"
        return $FAILURE
    }
}

proc ::sth::IsIs::IpVersionCompatible {parentIpVersion childIpVersion} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    switch -exact $parentIpVersion {
        IPV4 {
            if {[string equal $childIpVersion "4"]} {
                return $SUCCESS
            } else {
                return $FAILURE
            }
        }
        IPV6 {
            if {[string equal $childIpVersion "6"]} {
                return $SUCCESS
            } else {
                return $FAILURE
            }
        }
        IPV4_AND_IPV6 {
            return $SUCCESS
        }
    }
}


###/*! \ingroup isishelperfuncs
### \fn IsIsIsLspHandleValid (str handle, varRef msgName)
###\brief Validates value against isis_handle
###
###This procedure checks if the value is valid IsisLspConfig Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2
###*/
###
### IsIsIsLspHandleValid (str handle, varRef msgName);
###

proc ::sth::IsIs::IsIsIsLspHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg
    
    if {[string first isislspconfig $handle]<0} {
        set errorMsg "The handle $handle is not a valid lsp handle."
        return $FAILURE
    }
    
    if {[catch {set isisrouterConfigHandle [::sth::sthCore::invoke stc::get $handle -parent]} errorMsg]} {
        set errorMsg "The handle $handle is not a valid lsp handle."
        return $FAILURE
    } else {
        if {[string first isisrouterconfig $isisrouterConfigHandle] >= 0} {
            set errorMsg $isisrouterConfigHandle
            return $SUCCESS
        } else {
            set errorMsg "The lsp object has no isisrouterconfig parent."
            return $FAILURE
        }
    }
}


###/*! \ingroup isishelperfuncs
### \fn IsIsIsSessionRtBlkHandleValid (str handle, varRef msgName)
###\brief Validates value against Ipv4(6)IsisRoutesConfig
###
###This procedure checks if the value is valid Ipv4(6)IsisRoutesConfig Handle or not.
###
###\param[in] handle The value of route handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang)
###*/
###
### IsIsIsSessionRtBlkHandleValid (str handle, varRef msgName);
###

proc ::sth::IsIs::IsIsIsSessionRtBlkHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::IsIs::ISISROUTEHNDLIST
    
    upvar 1 $msgName errorMsg
    
    if {[info exists ISISROUTEHNDLIST($handle)]} {
        return $SUCCESS
    } else {
        set errorMsg "IsIs route handle $handle does not exist"
        return $FAILURE
    }
}

###/*! \ingroup isishelperfuncs
### \fn IsIsIsNeighborHandleValid (str handle, varRef msgName)
###\brief Validates value against isis_handle
###
###This procedure checks if the value is valid IsisLspNeighborConfig Handle or not.
###
###\param[in] handle The value of handle
###\param[out] msgName Error Msg
###\return FAILURE or SUCCESS
###
###\attention This procedure might require change based on other team needs.
###\author Jeremy Chang (jchang)
###*/
###
### IsIsIsNeighborHandleValid (str handle, varRef msgName);
###

proc ::sth::IsIs::IsIsIsNeighborHandleValid { handle msgName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $msgName errorMsg
    
    if {[string first isislspneighborconfig $handle] < 0} {
        set errorMsg "The handle $handle is not a valid isis neighbor handle"
        return $FAILURE
    }
    
    if {[catch {set isisLspHandle [::sth::sthCore::invoke stc::get $handle -parent]} errorMsg]} {
        set errorMsg "The handle $handle is not a valid isis neighbor handle"
        return $FAILURE
    } else {
        if {[string first isislspconfig $isisLspHandle]>=0} {
            return $SUCCESS
        } else {
            set errorMsg "The handle $handle has not a valid parent"
            return $FAILURE
        }
    }
}

proc ::sth::IsIs::IpToBin {ip} {
    if {[catch {::ip::normalize $ip} ip]} {
        return -code error $ip   
    }
    
    set binStr {}
    if {[::ip::is 4 $ip]} {
        foreach byte [split $ip .] {
            binary scan [binary format i $byte] B8 result
            append binStr $result
        }
    } else {
        foreach byte [split $ip :] {
            binary scan [binary format H* $byte] B16 result
            append binStr $result
        }
    }
    return $binStr
}

proc ::sth::IsIs::convertIpStepToInt {step prefix} {
    # convert step to binary
    set binStep [IpToBin $step]
    set targetBinStep [string range $binStep 0 [expr {$prefix - 1}]]
    # convert binary step to integer
    return [::sth::sthCore::binToInt $targetBinStep]
}

proc ::sth::IsIs::convertIptoNum {ipAddr ipVer convertVal} {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar $convertVal value
    
    switch -exact -- $ipVer {
        4 {
            set octets [split $ipAddr .]
            if {[llength $octets] != 4} {
                 set octets [lrange [concat $octets 0 0 0] 0 3]
            }
            set binipAddr ""
            foreach oct $octets {
                binary scan [binary format c $oct] B* bin
                set binipAddr "$binipAddr$bin"
            }
            binary scan [binary format B32 [format %032s $binipAddr]] I value
            return 1
        }
        6 {
            set normaizedIpAddressValue [::sth::sthCore::normalizeIPv6Addr $ipAddr];
            if {$normaizedIpAddressValue == 0} {
                return 0;
            } else {
                set ipAddr $normaizedIpAddressValue
            }
            set octets [split $ipAddr :]
            set binIpAddress ""
            foreach oct $octets {
                binary scan [binary format H4 $oct] B* bin
                set binIpAddress "$binIpAddress$bin"
            }
            set binIpAddress [string range $binIpAddress [expr [string length $binIpAddress]-32] end]
            binary scan [binary format B* $binIpAddress] I value
            return 1
        }
        default {
            ::sth::sthCore::log error "Unrecognized IP version"
            set value -1
            return 0
        }
    }
}


proc ::sth::IsIs::stepHexValue { hex stepVal stepCnt} {
     
     variable ::sth::sthCore::SUCCESS
     variable ::sth::sthCore::FAILURE

     set hexLen [string len $hex]
     set stepValLen [string len $stepVal]
     
     if {($hexLen % 2) || ($stepValLen % 2)} {
          ::sth::sthCore::log error "hex string does not have even number of hex digits."
         return $::sth::sthCore::FAILURE
     }
     
     if {$hexLen > $stepValLen} {
         set length  $hexLen
         for {set i 0} {$i < $hexLen- $stepValLen} {incr i} {
             set stepVal "0$stepVal"      
         }
     } else {
         set length  $stepValLen
         for {set i 0} {$i < $stepValLen - $hexLen} {incr i} {
             set hex "0$hex"      
         }
     }
     set binHexString ""          
     for {set i 0} {$i < $length} {incr i 2} {
         binary scan [binary format H2 [string range $hex $i [expr $i+ 1]]] B* bin
         set binHexString "$binHexString$bin"
     }
     set binStepVal ""          
     for {set i 0} {$i < $length} {incr i 2} {
         binary scan [binary format H2 [string range $stepVal $i [expr $i+ 1]]] B* bin
         set binStepVal "$binStepVal$bin"
     }
     
     set newBinHexString $binHexString
     for {set i 0} {$i < $stepCnt} {incr i} {
        if {![::sth::sthCore::binaryAddition $newBinHexString $binStepVal newBinHexString]} {
            ::sth::sthCore:: log error "Internal Error: binaryAddition - error occurs while adding two hex string."
            return ::sth::sthCore::FAILURE
        }
     }    
     
     set newHex ""
     for {set x 0; set y 7} {$y < [expr $hexLen * 4]} {} {
        set oct [string range $newBinHexString $x $y]
        binary scan [binary format B8 $oct] H* i
        set newHex "$newHex$i"
        set x [expr {$x+8}]
        set y [expr {$y+8}]
     }
     return $newHex
}

###/*! \ingroup isishelperfuncs
### \fn ipToHexFormat (str ip)
###\brief Convert ipv4 address to  hex format
###
###This procedure convert ipv4 address to hex digit format.
###\param[in] hexvalue
###
###\return hex format of ip address
###
###
###\author Jeremy Chang (jchang)
###
###*/
###
###ipToHexFormat (str ip str );
###

proc ::sth::IsIs::ipToHexFormat { ip } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
  
    set octets [split $ip .]
    if {[llength $octets] != 4} {
        set octets [lrange [concat $octets 0 0 0] 0 3]
    }
    set returnVal ""
    foreach oct $octets {
        set returnVal "$returnVal[format %0.2x $oct]"
    }
    return $returnVal
}


###/*! \ingroup isishelperfuncs
### \fn getIsIsPort (str handle, varRef returnVarName)
###\brief get isis port handle base on the session handle
###
###This procedure get isis port handle base on the session handle
###
###\param[in] handle The value of handle
###\param[out] returnVarName hold the return variable name
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang)
###*/
###
### getIsIsPort (str handle, varRef msgName);
###

proc ::sth::IsIs::getIsIsPort { handle returnVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnVarName returnVal  
    
    if {[catch {set portHandleList [::sth::sthCore::invoke stc::get $handle -affiliationport-Targets]} eMsg]} {
        return $FAILURE
    } else {
        set returnVarName [lindex $portHandleList 0]
        return $SUCCESS
    }
}


###/*! \ingroup isishelperfuncs
### \fn getIsIsSessionHandle (str handle, varRef returnVarName)
###\brief get isis session handle base on the Lsp handle
###
###This procedure get isis session handle base on the lsp handle
###
###\param[in] handle The value of handle
###\param[out] returnVarName hold the return variable name
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang)
###*/
###
### getIsIsSessionHandle (str handle, varRef msgName);
###

proc ::sth::IsIs::getIsIsSessionHandle { handle returnVarName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnVarName returnVal  
    
    set flag 0
    
    if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $handle -parent]} errorMsg]} {
        return $FAILURE
    } else {
        if {[string first "isisrouterconfig" [string tolower $isisSessionHandle]]<0} {
            return $FAILURE
        } else {
            set returnVal $isisSessionHandle
            return $SUCCESS
        }
    }
    set errorMsg "IsIs router handle does not exist"
    set returnVal ""
    return $FAILURE
}


###/*! \ingroup isishelperfuncs
### \fn getIsIsNeighborHandle (str lspHandle, str neighborLspHandle, varRef returnVarName)
###\brief get isis neighbor handle base on the neighbor Lsp handle
###
###This procedure get isisNeighbor Handle base on the neighbor Lsp Handle 
###
###\param[in] lsphandle The value of lsp handle
###\param[in] lsphandle The value of neighbor lsp handle
###\param[out] returnVarName hold the return variable name
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang), modified by Tong Zhou for stc P2
###*/
###
### getIsIsNeighborHandle (str lspHandle, str neighborLspHandle, varRef returnVarName);
###

proc ::sth::IsIs::getIsIsNeighborHandle { lspHandle neighborLspHandle returnVarName} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnVarName returnVal 
    
    if {[catch {set neighborNeighborPseudonodeId [::sth::sthCore::invoke stc::get $neighborLspHandle -NeighborPseudonodeId]}]} {
        set returnVal 0
        return $FAILURE
    }
    set NeighborPseudonodeId ""
    if {[catch {set neighborList [::sth::sthCore::invoke stc::get $lspHandle -children-IsisLspNeighborConfig]}]} {
        set returnVal 0
        return $FAILURE
    } else {
        foreach neighbor $neighborList {
            catch {set NeighborPseudonodeId [::sth::sthCore::invoke stc::get $neighbor -NeighborPseudonodeId]}
            if {[string compare $NeighborPseudonodeId $neighborNeighborPseudonodeId]==0} {
                set returnVal $neighbor
                return $SUCCESS
            }
        }
    }
    set returnVal 0
    return $FAILURE
}

###/*! \ingroup isishelperfuncs
### \fn getIsIsNeighborList (str lspHandle, varRef returnVarName)
###\brief get isisLsp List which connect to the lspHandle
###
###This procedure get list of isisLsp which has lspHandle as neighbor 
###
###\param[in] lsphandle The value of lsp handle
###\param[out] returnVarName hold the return variable name
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang)
###*/
###
### getIsIsNeighborList (str lspHandle, varRef returnVarName), modified by Tong Zhou for P2
###

proc ::sth::IsIs::getIsIsNeighborList { lspHandle returnVarName } { 
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::GBLHNDMAP

    upvar 1 $returnVarName returnVal  
    set returnVal {} 
    set nbrList {}    
    
    set projectHandle $GBLHNDMAP(project)
    
    set routerList [list]
    set isisRouterList [list]
    set isisLspList [list]
    set neighborList [list]

    if {[catch {set neighborNeighborPseudonodeId [::sth::sthCore::invoke stc::get $neighborLspHandle NeighborPseudonodeId]}]} {
        set returnVal 0
        return $FAILURE
    }
    
    set NeighborPseudonodeId ""
    if {[catch {::sth::sthCore::stcGetChildren router $projectHandle routerList} eMsg]} {
        set returnVal [list]
        return $FAILURE
    } else {
        foreach router $routerList {
            catch {set isisRouterList [::sth::sthCore::invoke stc::get $router -children-isisrouterconfig]}
            foreach isisRouter $isisRouterList {
                catch {set isisLspList [::sth::sthCore::invoke stc::get $isisRouter -children-isislspconfig]}
                foreach isisLsp $isisLspList {
                    catch {set neighborList [::sth::sthCore::invoke stc::get $isisLsp -children-IsisLspNeighborConfig]}
                    foreach neighbor $neighborList {
                        catch {set NeighborPseudonodeId [::sth::sthCore::invoke stc::get $neighbor -NeighborPseudonodeId]}
                        if {[string compare $pseunodeId $neighborNeighborPseudonodeId] == 0} {
                            lappend returnVal $isisLsp
                            break
                        }
                    }
                }
            }
        }
    }
    return $SUCCESS
}

###/*! \ingroup isishelperfuncs
### \fn getLspHandleOnSysId (str handleValue, str systemId, str level, varRef returnHandleName)
###\brief return IsisLSP handle base on handleValue, systemId and routing_level and pseduonode 0
###
###This procedure search IsisLSP object which is defined under the handleValue and matched to systemId, routing_level, and pseduonode 0     .    
###
###\param[in] handle The value of handle
###\param[in] systemId system id of isis router
###\param[out] returnHandleName The name hold the matching IsisLSP handle
###\return FAILURE or SUCCESS
###
###\author Jeremy Chang (jchang)
###*/
###
### getLspHandleOnSysId (str handleValue, str systemId, str level, varRef returnHandleName);
###

proc ::sth::IsIs::getLspHandleOnSysId { handleValue systemId routing_level returnHandleName } {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::GBLHNDMAP
    
    upvar 1 $returnHandleName returnHandle  
    
    set attrList {-SystemId -Level -NeighborPseudonodeId}
    
    if {[catch {set isisRouterList [::sth::sthCore::invoke stc::get $handleValue -children-isisrouterconfig]} eMsg]} {
        set returnHandle -1
        return $FAILURE
    } else {
        set isisRouterHandle [lindex $isisRouterList 0]
        if {[catch {set isisLspList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-isislspconfig]} eMsg]} {
            set returnHandle -1
            return $FAILURE
        }
        puts $isisLspList
        foreach isisLsp $isisLspList {
            catch {set attrValList [::sth::sthCore::invoke stc::get $isisLsp $attrList]}
            set sysid [lindex $attrValList 1]
            set lsplevel [lindex $attrValList 3]
            set NeighborPseudonodeId [lindex $attrValList 5]
                 # puts "sysid = $sysid, lsplevel = $lsplevel, NeighborPseudonodeId = $NeighborPseudonodeId"
                # puts "systemId = $systemId, routing_level = $routing_level"
            if {([string equal $systemId $sysid] && ([string equal $routing_level $lsplevel] || [string match -nocase "LEVEL1_AND_2" $routing_level]) && $NeighborPseudonodeId == 0)} {
                lappend returnHandle $isisLsp
            }
        }
        
        # puts [list length = [llength $returnHandle]]
        if { ( [string match -nocase "LEVEL1_AND_2" $routing_level] && [llength $returnHandle] == 2 ) || \
             (![string match -nocase "LEVEL1_AND_2" $routing_level] && [llength $returnHandle] == 1 )} {
            return $SUCCESS
        }
    }
    return $FAILURE
}


### convert the system_id format from hltapi (xxxxxxxxxxxx) to stc format
### (xx-xx-xx-xx-xx-xx)
proc ::sth::IsIs::convertSystemId {systemId} {
    # add padding if system id is too short
    set sysIdLen [string length $systemId]
    set padding [expr {12 - $sysIdLen}]
    if {$padding > 0} {
        set systemId [join [list [string repeat 0 $padding] $systemId] ""]
    }
    
    set retval {}
    for {set i 0} {$i < 12} {incr i 2} {
        lappend retval [string range $systemId $i [expr {$i+1}]]
    }
    return [join $retval -]
}


###/*! \ingroup isisswitchprocfuncs
###\fn processConfigCmd(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the direct-mapping.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
### param[in] isisSessionHandle is the handle of stc router, which is used as the handle in the return keyed list

proc ::sth::IsIs::processConfigCmd {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_wide_metrics_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchValueList [list]
    
    set wide_metrics_index [lsearch $switchList wide_metrics]
    
    if {$wide_metrics_index >= 0} {
        set switchAttr $emulation_isis_config_stcattr(wide_metrics)
        set switchValue $userArgsArray(wide_metrics)
        set switchValue $emulation_isis_config_wide_metrics_fwdmap($switchValue)
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
        set switchList [lreplace $switchList $wide_metrics_index $wide_metrics_index]
    }
    
    foreach switchName $switchList {
        set tmpAttrName $emulation_isis_config_stcattr($switchName)
        set tmpObjName $emulation_isis_config_stcobj($switchName)
        set tmpValue $userArgsArray($switchName)
        set attrValue $tmpValue
        
        if {[string compare $tmpObjName "IsisRouterConfig"]==0} {
            lappend switchValueList "-$tmpAttrName"
            lappend switchValueList $attrValue
        }
        
        if {$switchName == "area_id" && [string length $tmpValue] > 26} {
            ::sth::sthCore::processError returnKeyedList "The value of area_id should be of 2-26 hexadecimal characters" {}
            return $FAILURE      
        }
    }
    # tk_messageBox -message "::sth::sthCore::invoke stc::config $isisSessionHandle $switchValueList"
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $switchValueList} msg]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while setting handle: $isisSessionHandle; Error: $msg" {}
        return $FAILURE
    } else {
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_graceful_restart_time(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the graceful restart timer.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure implements the graceful_restart_restart_time. Thanks to the confliction between attribute config constraints of stc and the parse_dashed_args required by Cisco. The only purpose of this function is to determine whether the graceful_restart is allowed. We set the switch value only if graceful_restart is allowed. This is to prevent the case that the restart is automatically set to its default value even if the graceful_restart is not even enabled.

proc ::sth::IsIs::emulation_isis_config_graceful_restart_time {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {
    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList

    set switchName [lindex $switchList 0]
    
    if {[catch {set gracefulRestart [::sth::sthCore::invoke stc::get $isisSessionHandle -EnableGracefulRestart]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while processing $switchName, Error: $getStatus" {}
        return $FAILURE
    }
    
    if {$gracefulRestart} {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_config_stcattr($switchName)
        if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle "-$switchAttr $switchValue"} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while processing $switchName, Error: $getStatus" {}
            return $FAILURE
        } else {
            ::sth::sthCore::log debug "Successfully set value for $switchName."
            return $SUCCESS
        }
    } else {
        ::sth::sthCore::log debug "The graceful restart mode is not enabled, the switch $switchName is skipped."
        return $SUCCESS
    }
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_holding_time(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the holding time
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure implements the holding time switche. Note: since the hold time in STC domain can only be muliple of hello interval, the multiplier will be the ceiling of the holding time desired/hello interval.
###


proc ::sth::IsIs::emulation_isis_config_holding_time {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchName [lindex $switchList 0]
    set holdingTime $::sth::IsIs::userArgsArray($switchName)
    set switchValue $holdingTime
    
    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $isisSessionHandle -HelloInterval]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while processing $switchName. Error: $getStatus" {}
        return $FAILURE
    } else {
        set HelloInterval $getValueVar
    }
    
    
    set helloMultiplier [expr int(ceil(double($holdingTime)/double($HelloInterval)))]
    set cmdFailed 0
    if {[expr $holdingTime % $HelloInterval]} {    
        ::sth::sthCore::log warn "holding time is not multiple of hello interval value.  Setting holding time to [expr $helloMultiplier * $HelloInterval]"
        
    }
    set configList [list -HelloMultiplier $helloMultiplier]
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch:$switchName. Error: $configStatus" {}
        set cmdFailed 1
    } else {
            ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
    }
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log info "Value: $switchValue set for switch:$switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchName"
        return $SUCCESS
    }  
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_intf_ip_addr(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the IP addresses in the Ipv4If object
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure configures the parameters Address and PrefixLength under Ipv4If.
###


proc ::sth::IsIs::emulation_isis_config_intf_ip_addr {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    if {[info exists userArgsArray(ip_version)]} {
        set ipVersion $userArgsArray(ip_version)
    } else {
        if {[catch {set ipVersion [::sth::sthCore::invoke stc::get $isisSessionHandle -ipVersion]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ip version. Error: $getStatus" {}
            return $FAILURE
        }
    }
     
    if {([string equal $ipVersion "6"] || [string equal $ipVersion "IPV6"])} {
        ::sth::sthCore::log warning "Currently runnign IPV6, the configuration of IPV4 interface is ignored."
        return $SUCCESS
    }
    
    #it seems will have problem if there are two ipv4if. comment off by cf
    #set switchValueList [list]
    #foreach switchName $switchList {
    #    set switchAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
    #    set switchValue $::sth::IsIs::userArgsArray($switchName)
    #    lappend switchValueList "-Ipv4If.$switchAttr" $switchValue
    #}
    
    #if {[catch {::sth::sthCore::invoke stc::config $isisRouterHandle $switchValueList} msg]} {
    #    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $isisRouterHandle. Error: $msg" {}
    #    return $FAILURE
    #} else {
    #    return $SUCCESS
    #}
    
    ##rewrote for gre case. delete the gre ip header from the list
        set ipv4List [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv4if]
    set ipv4Handle [::sth::deleteGreIP $ipv4List $isisRouterHandle]
    
    set configList ""
    set switchValueList [list]
    foreach switchName $switchList {
        set switchAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        set switchValue $::sth::IsIs::userArgsArray($switchName)
        lappend configList -$switchAttr
        lappend configList $switchValue
    }

    foreach ipv4HandleTemp $ipv4Handle { 
    if {[catch {::sth::sthCore::invoke stc::config $ipv4HandleTemp $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "Internal Command Error while configuring value of switch. Error: $configStatus" {}
        return $FAILURE
    }
    }
    return $SUCCESS
}

###/*! \ingroup isisswitchprocfuncs(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the IP address in the Ipv6If object.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure configures the parameters Address and PrefixLength under Ipv6If.
###


proc ::sth::IsIs::emulation_isis_config_intf_ipv6_addr {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    if {[info exists userArgsArray(ip_version)]} {
        set ipVersion $userArgsArray(ip_version)
    } else {
        if {[catch {set ipVersion [::sth::sthCore::invoke stc::get $isisSessionHandle -ipVersion]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting IP version. Error: $getStatus" {}
            return $FAILURE
        }
    }
     
    if {([string equal $ipVersion "4"] || [string equal $ipVersion "IPV4"])} {
        ::sth::sthCore::log warning "Currently runnign IPV4, the configuration of IPV6 interface is ignored."
        return $SUCCESS
    }
    
    if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring : Cannot get Ipv6 interface handle. Error: $getStatus" {}
        return $FAILURE
    } else {
        if {[llength $ipv6ifList]!=2} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Something is wrong with the Ipv6If handle $ipv6ifList" {}
            return $FAILURE
        } else {
            set ipv6Global [lindex $ipv6ifList 0]
        }
    }
    
    set switchValueList [list]
    foreach switchName $switchList {
        set switchAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        set switchValue $::sth::IsIs::userArgsArray($switchName)
        lappend switchValueList "-$switchAttr" $switchValue
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $ipv6Global $switchValueList} msg]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $isisSessionHandle. Error: $msg" {}
        return $FAILURE
    } else {
        return $SUCCESS
    }
}


proc ::sth::IsIs::emulation_isis_config_link_local_ipv6_addr {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    if {[info exists userArgsArray(ip_version)]} {
        set ipVersion $userArgsArray(ip_version)
    } else {
        if {[catch {set ipVersion [::sth::sthCore::invoke stc::get $isisSessionHandle -ipVersion]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting IP version. Error: $getStatus" {}
            return $FAILURE
        }
    }
     
    if {([string equal $ipVersion "4"] || [string equal $ipVersion "IPV4"])} {
        ::sth::sthCore::log warning "Currently runnign IPV4, the configuration of IPV6 interface is ignored."
        return $SUCCESS
    }
    
    if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring : Cannot get Ipv6 interface handle. Error: $getStatus" {}
        return $FAILURE
    } else {
        if {[llength $ipv6ifList]!=2} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Something is wrong with the Ipv6If handle $ipv6ifList" {}
            return $FAILURE
        } else {
            set ipv6LinkLocal [lindex $ipv6ifList 1]
        }
    }
    
    set switchValueList [list]
    foreach switchName $switchList {
        set switchAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        set switchValue $::sth::IsIs::userArgsArray($switchName)
        lappend switchValueList "-$switchAttr" $switchValue
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $ipv6LinkLocal $switchValueList} msg]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $isisSessionHandle. Error: $msg" {}
        return $FAILURE
    } else {
        return $SUCCESS
    }
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_lsp_level(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the lsp level.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure processes lsp_life_time and lsp_level switches. 
###

proc ::sth::IsIs::emulation_isis_config_lsp {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_lsp_level_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchNameList [list]
    foreach switchName $switchList {
        set switchAttr $emulation_isis_config_stcattr($switchName)
        set switchValue $userArgsArray($switchName)
        if {[string equal $switchName lsp_level]} {
            set attrValue $emulation_isis_config_lsp_level_fwdmap($switchValue)
            if {[string match -nocase LEVEL1_AND_2 $attrValue]} {
                set attrValue LEVEL2 ;# LSP only supports LEVEL1 or LEVEL2   
            }
        } else {
            set attrValue $switchValue
        }
        lappend switchNameList "-$switchAttr"
        lappend switchNameList $attrValue
    }

    foreach lspHandle $isisLspHandle {
        if {[catch {::sth::sthCore::invoke stc::config $lspHandle $switchNameList} msg]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $lspHandle. Error: $msg" {}
            return $FAILURE
        }
    }
    return $SUCCESS
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_mac_address(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the MAC addresses in the EthiiIf object
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure configures the parameters SourceMac under EthiiIf.
###


proc ::sth::IsIs::emulation_isis_config_mac_address {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    # mac address is not allowed to be configured in ATM encapsulation
    if {[info exists userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} {
        return $SUCCESS
    }
    
    set switchValueList [list]
    foreach switchName $switchList {
        set switchAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        set switchValue $::sth::IsIs::userArgsArray($switchName)
        lappend switchValueList "-$switchAttr" $switchValue
    }
    
    if {[catch {set ethIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ethiiif]} err]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $isisRouterHandle. Error: $err" {}
        return $FAILURE
    }
    if {[llength $ethIf] == 0} {
        ::sth::sthCore::processError returnKeyedList "The lower layer stack of $isisRouterHandle is not Ethernet encapsulationon."
        return $FAILURE
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $ethIf $switchValueList} err]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $isisRouterHandle. Error: $err" {}
        return $FAILURE
    } else {
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_intf_metric(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the metrics.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure implements the intf_metric switche.
###


proc ::sth::IsIs::emulation_isis_config_intf_metric {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList

    
    set switchName [lindex $switchList 0]
    set switchValue $userArgsArray($switchName)
    
    set cmdFailed 0
    
    set isisLevel ""
    foreach lsphnd $isisLspHandle {
        # retreive isis level.  Note isis level and wide_metrics has higher priority, so it will be processed first.
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $lsphnd -Level]} getStatus ]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $lsphnd. Error: $getStatus" {}
            return $FAILURE
        } else {
            if {$isisLevel eq ""} {
                set isisLevel $getValueVar
            } elseif {$isisLevel ne $getValueVar} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $lsphnd. Error: cannot set intf_metric for different level in $isisLspHandle." {}
                return $FAILURE
            }
        }
    }


    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $isisSessionHandle -MetricMode]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while fetching -MetricMode from $isisSessionHandle. Error: $getStatus" {}
        return $FAILURE 
    } else {
        set isisMetMode $getValueVar
    }
    
    ::sth::sthCore::log info "Configuring the switch:$switchList to value:$switchValue"
    
    
    if {!([string equal $isisLevel LEVEL1] || 
        [string equal $isisLevel LEVEL2] ||        
        [string equal $isisLevel LEVEL1_AND_2])} {

        ::sth::sthCore::processError returnKeyedList "$_switchName* Unknown Value for the isis level Value:$isisLevel" {}
        return $FAILURE         
    }

    if {!([string equal $isisMetMode NARROW] || 
        [string equal $isisMetMode WIDE] ||        
        [string equal $isisMetMode NARROW_AND_WIDE])} {

        ::sth::sthCore::processError returnKeyedList "$_switchName* Unknown Value for the isis metric mode Value:$isisMetMode" {}
        return $FAILURE         
    }

        
    if {[string equal $isisLevel LEVEL1] || [string equal $isisLevel LEVEL1_AND_2]} {
        
        if {[string equal $isisMetMode NARROW] || [string equal $isisMetMode NARROW_AND_WIDE]} {
            set configList [list -L1Metric $switchValue]
        #    tk_messageBox -message "doStcConfig $isisSessionHandle $configList"
            if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                set cmdFailed 1
            } else {
                ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
            }        
        }
        
        if {[string equal $isisMetMode WIDE] || [string equal $isisMetMode NARROW_AND_WIDE]} {
            set configList [list -L1WideMetric $switchValue]
        #    tk_messageBox -message "doStcConfig $isisSessionHandle $configList"
            if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                set cmdFailed 1
            } else {
                ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
            }
        }        
    }
    
    if {[string equal $isisLevel LEVEL2] || [string equal $isisLevel LEVEL1_AND_2]} {
        
        if {[string equal $isisMetMode NARROW] || [string equal $isisMetMode NARROW_AND_WIDE]} {
            set configList [list -L2Metric $switchValue]
        #    tk_messageBox -message "doStcConfig $isisSessionHandle $configList"
            if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                set cmdFailed 1
            } else {
                ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
            }        
        }
        
        if {[string equal $isisMetMode WIDE] || [string equal $isisMetMode NARROW_AND_WIDE]} {
            set configList [list -L2WideMetric $switchValue]
        #    tk_messageBox -message "doStcConfig $isisSessionHandle $configList"
            if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                set cmdFailed 1
            } else {
                ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
            }
        }        
    }
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log info "Value: $switchValue set for switch:$switchName"
        ::sth::sthCore::log debug "Successfully completed processing switch: $switchName"
        return $SUCCESS
    }  
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_ip_version(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the IP version.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure implements ip version switche. 
###
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou
###*/
###
###emulation_isis_config_ip_version (str isisRouterHandle, str isisLspHandle, list switchList, list retKeyList);
###

proc ::sth::IsIs::emulation_isis_config_ip_version {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_ip_version_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList

    set cmdFailed 0
    
    set switchName [lindex $switchList 0]
    set switchValue $userArgsArray($switchName)
    set switchAttr $emulation_isis_config_stcattr($switchName)
    set attrValue $emulation_isis_config_ip_version_fwdmap($switchValue)
    
    set switchValueList [list "-$switchAttr" $attrValue]
    
    if {[catch {set isisHandleList [::sth::sthCore::invoke stc::get $isisRouterHandle "-children-isisrouterconfig -children-ipv4if -children-ipv6if -children-vlanif -children-ethiiif -children-Aal5If"]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting ISIS protocol, IPv4 interface, IPv6 interface and vlan interface from handle $isisRouterHandle. Error: $getStatus" {}
        set cmdFailed 1
        return $FAILURE
    } else {
        set isisSessionHandle [lindex $isisHandleList 1]
        set ipv4ResultIf [lindex $isisHandleList 3]
        set ipv6ResultIf [lindex $isisHandleList 5]
        set vlanResultIf [lindex $isisHandleList 7]
        set ethiiResultIf [lindex $isisHandleList 9]
        set atmResultIf [lindex $isisHandleList 11]
    }
        
        #delete the greipif from the list if exist
        set ipv4ResultIf [::sth::deleteGreIP $ipv4ResultIf $isisRouterHandle]
        set ipv6ResultIf [::sth::deleteGreIP $ipv6ResultIf $isisRouterHandle]
        
    
    if {[string first vlanif $vlanResultIf] >= 0} {
        set attachToHandle $vlanResultIf
    } elseif {[string first aal5if $atmResultIf] >= 0 } {
        set attachToHandle $atmResultIf
    } else {
        set attachToHandle $ethiiResultIf
    }
    
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
        set cmdFailed 1
        return $FAILURE
    } else {
        ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
    }
    
#    tk_messageBox -message "doStcConfig $isisSessionHandle $switchValueList"
    set haveIpv4 0
    set haveIpv6 0
    if {[string first ipv4if $ipv4ResultIf]>=0} {set haveIpv4 1}
    if {[string first ipv6if $ipv6ResultIf]>=0} {set haveIpv6 1}
    
    if {!$haveIpv6 && ([string first 6 $switchValue]>=0)} {
        if {!([info exists userArgsArray(intf_ipv6_addr)] && [info exists userArgsArray(intf_ipv6_prefix_length)])} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Cannot change IP version to $switchValue without specifying intf_ipv6_addr and intf_ipv6_prefix_length" {}
            return $FAILURE
        }
    }
    
    if {!$haveIpv4 && ([string first 4 $switchValue]>=0)} {
        if {!([info exists userArgsArray(intf_ip_addr)] && [info exists userArgsArray(intf_ip_prefix_length)])} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Cannot change IP version to $switchValue without specifying intf_ip_addr and intf_ip_prefix_length" {}
            return $FAILURE
        }
    }
    if {[string equal $switchValue "4"]} {
        if {!$haveIpv4} {
            foreach attHandle $attachToHandle { 
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $isisRouterHandle -IfStack "Ipv4If" -IfCount "1" -AttachToIf $attHandle} status]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while adding the IPV4 interface. Error: $status" {}
                set cmdFailed 1
                return $FAILURE
            }
            }
        }
        if {$haveIpv6} {
            foreach ipv6If $ipv6ResultIf {
                if {[catch {::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $isisRouterHandle -TopIf $ipv6If} status]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while removing the old IPV6 interface. Error: $status" {}
                    set cmdFailed 1
                    return $FAILURE
                }
            }
            # remove any existing IPv6 ISIS routes
            removeStaleIsisRoutes $isisSessionHandle
        }
        if {[catch {set ipv4ResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv4if]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV4 interface. Error: $getStatus" {}
                set cmdFailed 1
                return $FAILURE
        } else {
                        set ipv4ResultIf [::sth::deleteGreIP $ipv4ResultIf $isisRouterHandle]
            if {[catch {::sth::sthCore::invoke stc::perform "ProtocolAttach -ProtocolList $isisSessionHandle -UsesIfList $ipv4ResultIf"} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while associating the ISIS protocol to IPV4 interface. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
    } elseif {[string equal $switchValue "6"]} {
        if {!$haveIpv6} {
            foreach attHandle $attachToHandle {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $isisRouterHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $attHandle} status]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while adding the IPV6 interface. Error: $status" {}
                set cmdFailed 1
                return $FAILURE
            }
            }

            if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV6 interface. Error: $getStatus" {}
                set cmdFailed 1
                return $FAILURE
            } else {
                set ipv6ifList [::sth::deleteGreIP $ipv6ifList $isisRouterHandle]
                set ipv6ifLocal [lindex $ipv6ifList 1]
#                set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                set linkLocalIp "FE80:0:0:0"
#                foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                    append linkLocalIp ":$num1$num2$num3$num4"
#                }
                if {[catch {
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -Address FE80::2
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                } configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while configuring the IPV6 link local address. Error: $configStatus" {}
                    return $FAILURE
                }
            }
        }
        if {$haveIpv4} {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackRemove -DeviceList $isisRouterHandle -TopIf $ipv4ResultIf} status]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while removing the old IPV4 interface. Error: $status" {}
                set cmdFailed 1
                return $FAILURE
            }
            # remove any existing IPv4 ISIS routes
            removeStaleIsisRoutes $isisSessionHandle
        }
        
        if {[catch {set ipv6ResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV6 interface. Error: $getStatus" {}
            set cmdFailed 1
            return $FAILURE
        } else {
                        set ipv6ResultIf [::sth::deleteGreIP $ipv6ResultIf $isisRouterHandle]
            set ipv6ResultIf [lindex $ipv6ResultIf 0]
             if {[catch {::sth::sthCore::invoke stc::perform "ProtocolAttach -ProtocolList $isisSessionHandle -UsesIfList $ipv6ResultIf"} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while associating the ISIS protocol to the IPV6 interface. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
    } elseif {[string equal $switchValue "4_6"]} {
        if {!$haveIpv4} {
            foreach attHandle $attachToHandle {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $isisRouterHandle -IfStack "Ipv4If" -IfCount "1" -AttachToIf $attHandle} status]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while adding the IPV4 interface. Error: $status" {}
                set cmdFailed 1
                return $FAILURE
            }
            }
        }
        if {!$haveIpv6} {
            foreach attHandle $attachToHandle {
            if {[catch {::sth::sthCore::invoke stc::perform IfStackAttach -DeviceList $isisRouterHandle -IfStack "Ipv6If" -IfCount "1" -AttachToIf $attHandle} status]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while adding the IPV6 interface. Error: $status" {}
                set cmdFailed 1
                return $FAILURE
            }
            }
            if {[catch {set ipv6ifList [::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv6if]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV6 interface. Error: $getStatus" {}
                set cmdFailed 1
                return $FAILURE
            } else {
                set ipv6ifList [::sth::deleteGreIP $ipv6ifList $isisRouterHandle]
                set ipv6ifLocal [lindex $ipv6ifList 1]
#                set link64BitAddr [::sth::sthCore::getNext64BitNumber]
#                set linkLocalIp "FE80:0:0:0"
#                foreach {num1 num2 num3 num4} [split $link64BitAddr {}] {
#                    append linkLocalIp ":$num1$num2$num3$num4"
#                }
                if {[catch {
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -Address FE80::2
                    ::sth::sthCore::invoke stc::config $ipv6ifLocal -AllocateEui64LinkLocalAddress true
                } configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while configuring the IPV6 link local address. Error: $configStatus" {}
                    return $FAILURE
                }
            }
        }
        if {[catch {set ipv4_6ResultIf [::sth::sthCore::invoke stc::get $isisRouterHandle "-children-ipv4if -children-ipv6if"]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while getting the IPV4 and IPV6 interfaces. Error: $getStatus" {}
            set cmdFailed 1
            return $FAILURE
        } else {
            set ipv4ResultIfList [lindex $ipv4_6ResultIf 1]
            set ipv4ResultIf [lindex $ipv4ResultIfList 0]
            set ipv6ResultIfList [lindex $ipv4_6ResultIf 3]
            set ipv6ResultIf [lindex $ipv6ResultIfList 0]
                         #delete the greipif from the list if exist
                        set ipv4ResultIf [::sth::deleteGreIP $ipv4ResultIf $isisRouterHandle]
                        set ipv6ResultIf [::sth::deleteGreIP $ipv6ResultIf $isisRouterHandle]
                
            set ipv4_6handleList [list $ipv4ResultIf $ipv6ResultIf]

            foreach ipHandle $ipv4_6handleList {
                if {[catch {::sth::sthCore::invoke stc::perform "ProtocolAttach -ProtocolList $isisSessionHandle -UsesIfList $ipHandle"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal command error while associating the ISIS protocol to IPV4 and IPV6 interfaces. Error: $configStatus" {}
                    set cmdFailed 1
                    return $FAILURE
                }
            }
        }
        if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle {-MetricMode NARROW_AND_WIDE}} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the metric_mode. Error: $configStatus" {}
            set cmdFailed 1
        } else {
            ::sth::sthCore::log info "The switch:MetricMode was successfully set to NARROW_AND_WIDE"
        }
    }
    # FIXME: delete stale routes. If switching from IPv6 to IPv4, delete any existing IPv6 ISIS routes.
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Failed to set the switch:$switchName to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully set the switch:$switchName to $switchValue"
        return $SUCCESS
    }
}

proc ::sth::IsIs::removeStaleIsisRoutes {isisRtrCfgHdl} {
    if {[catch {::sth::sthCore::invoke stc::get $isisRtrCfgHdl -IpVersion} ipVersion]} {
        return -code error "Failed to get the IP version of the ISIS router config."
    }
    if {[string match -nocase IPV4 $ipVersion]} {
        set staleRouteType ipv6isisroutesconfig
    } else {
        set staleRouteType ipv4isisroutesconfig
    }
    if {[catch {::sth::sthCore::invoke stc::get $isisRtrCfgHdl -children-isislspconfig} isisLspConfigList]} {
        return -code error "Failed to get ISIS LSP configs."
    }
    foreach lspConfig $isisLspConfigList {
        if {[catch {::sth::sthCore::invoke stc::get $lspConfig "-children-$staleRouteType"} isisRoutesConfigList]} {
            return -code error "Failed to get ISIS routes."
        }
        foreach routesConfig $isisRoutesConfigList {
            if {[catch {::sth::sthCore::invoke stc::delete $routesConfig} err]} {
                return -code error "Failed to delete $routesConfig. $err"
            }
        }
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_router_id(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process configure the RouterId under router.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###\brief Processes routing_level switches. Basically, it sets the IsisRouterLevel under IsisRouterConfig and IsisLspLevel under IsisLspConfig
### to the value of routing_level. If routing level is L1_L2, then the IsisLspLevel is set to L2
###


proc ::sth::IsIs::emulation_isis_config_router_id {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_routing_level_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_isis_config_stcattr($switchName)
    set switchValue $userArgsArray($switchName)
    
    if {[catch {::sth::sthCore::invoke stc::config $isisRouterHandle "-$switchAttr $switchValue"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully configured $switchName to $switchValue"
        return $SUCCESS
    }
}

proc ::sth::IsIs::emulation_isis_config_ipv6_router_id {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_routing_level_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_isis_config_stcattr($switchName)
    set switchValue $userArgsArray($switchName)
    
    if {[catch {::sth::sthCore::invoke stc::config $isisRouterHandle "-$switchAttr $switchValue"} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully configured $switchName to $switchValue"
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_routing_level(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the routing level: 1 or 2.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###\brief Processes routing_level switches. Basically, it sets the IsisRouterLevel under IsisRouterConfig and IsisLspLevel under IsisLspConfig
### to the value of routing_level. If routing level is L1_L2, then the IsisLspLevel is set to L2
###This procedure implements routing_level switche. 
###


proc ::sth::IsIs::emulation_isis_config_routing_level {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_config_routing_level_fwdmap
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    set switchName [lindex $switchList 0]
    set switchValue $userArgsArray($switchName)
    set attrName $emulation_isis_config_stcattr($switchName)
    set attrValue $emulation_isis_config_routing_level_fwdmap($switchValue)
    
    # Configure the new routing level
    set switchValueList [list -$attrName $attrValue]
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName Internal Command Error while configuring $isisSessionHandle. Error: $configStatus" {}
        set cmdFailed 1
    }
    if {![string equal $switchValue "L1L2"] && ![info exists userArgsArray(lsp_level)]} {
        # get current routing level and set lsps to the same level
        foreach lspHandle $isisLspHandle {
        set switchValueList [list -Level $attrValue]
        if {[catch {::sth::sthCore::invoke stc::config $lspHandle $switchValueList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName Internal Command Error while configuring $lspHandle. Error: $configStatus" {}
            set cmdFailed 1
        }
        }
    }
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchName"
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_system_id(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the system id.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###This procedure implements system_id switche. Similar to the emulation_isis_config_routing_level, this function configures the system id of both
### IsisRouterConfig and IsisLspConfig
###

proc ::sth::IsIs::emulation_isis_config_system_id {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set switchName [lindex $switchList 0]
    set switchValue [convertSystemId $userArgsArray($switchName)]
        
    set attrName $emulation_isis_config_stcattr($switchName)
    set cmdFailed 0
    
    # Set the IsisRouterConfig
    set configList [list "-$attrName" $switchValue]
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    }
    
    # Set the IsisLspConfig
    set configList [list -SystemId $switchValue]
    foreach lspHandle $isisLspHandle {
        if {[catch {::sth::sthCore::invoke stc::config $lspHandle $configList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring $lspHandle. Error $configStatus" {}
            set cmdFailed 1
        }
    }

    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchName"
        return $SUCCESS
    }
}
###this fucntion is used to decide the TLV value of TeParams
proc ::sth::IsIs::calc_te_subtlv {switchList} {
        variable ::sth::IsIs::userArgsArray
        set SubTlv "NONE"
        foreach switchName $switchList {
                switch -- $switchName {
                        link_te_remote_ip_addr -
                        traffic_engineered_remote_ip_addr {
                                set SubTlv "$SubTlv|REMOTE_IP"       
                        }
                        link_ip_addr -
                        traffic_engineered_ip_addr {
                                set SubTlv "$SubTlv|LOCAL_IP"       
                        }
                        traffic_engineered_group -
                        te_admin_group -
                        link_te_admin_group {
                                set SubTlv "$SubTlv|GROUP"       
                        }
                        te_max_bw -
                        link_te_max_bw -
                        traffic_engineered_max_bw {
                                set SubTlv "$SubTlv|MAX_BW"       
                        }
                        te_max_resv_bw -
                        link_te_max_resv_bw -
                        traffic_engineered_max_resv_bw {
                                set SubTlv "$SubTlv|MAX_RSV_BW"       
                        }
                        
                        default {
                                if {([regexp -nocase {bw_priority} $switchName])&&(![regexp -nocase {UNRESERVED} $SubTlv])} {
                                        set SubTlv "$SubTlv|UNRESERVED"
                                }
                        }
                }   
        }
        return $SubTlv
}
###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_te_info(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling most of the switches related to TE.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###
###This procedure implements the configuration of te related switche for emulation_isis_config.
###
###

proc ::sth::IsIs::emulation_isis_config_te_info {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    
    # retrieve the router level
    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $isisSessionHandle -Level]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting routing_level. Error: $getStatus" {}
        return $FAILURE
    } else {
        set routerLevel $getValueVar
    }
    
    # puts "routerLevel = $routerLevel"
    
    set switchValueList1 [list]
    set switchValueList2 [list]
    
    if {([string equal $routerLevel LEVEL1] || [string equal $routerLevel LEVEL1_AND_2])} {
        foreach switchName $switchList {
            set switchAttr $emulation_isis_config_stcattr($switchName)
            set switchValue $userArgsArray($switchName)
            if {[string equal $switchName te_enable]} {
                continue
            }
            lappend switchValueList1 "-$switchAttr"
            lappend switchValueList1 $switchValue
        }
        lappend switchValueList1 "-SubTlv"
        lappend switchValueList1 [calc_te_subtlv $switchList]
        if {[llength $switchValueList1] > 0} {
            if {[catch {set isislevel1teparamsHandle [::sth::sthCore::invoke stc::get $isisSessionHandle -children-isislevel1teparams]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting level 1 TE params handle. Error: $getStatus" {}
                return $FAILURE
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $isislevel1teparamsHandle $switchValueList1} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring level 1 TE params handle. Error: $configStatus" {}
                    return $FAILURE
                } else {
                    ::sth::sthCore::log info "The Level 1 TeParams under handle $isisSessionHandle was successfully configured"
                }
            }
        }
    }
    
    if {([string equal $routerLevel LEVEL2] || [string equal $routerLevel LEVEL1_AND_2])} {
        foreach switchName $switchList {
            set switchAttr $emulation_isis_config_stcattr($switchName)
            set switchValue $userArgsArray($switchName)
            if {[string equal $switchName te_enable]} {
                continue
            } else {
                set attrValue $switchValue
            }
            lappend switchValueList2 "-$switchAttr"
            lappend switchValueList2 $attrValue
        }
        lappend switchValueList2 "-SubTlv"
        lappend switchValueList2 [calc_te_subtlv $switchList]
        if {[llength $switchValueList2] > 0} {
            if {[catch {set isislevel2teparamsHandle [::sth::sthCore::invoke stc::get $isisSessionHandle -children-isislevel2teparams]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while getting level 2 TE params handle. Error: $getStatus" {}
                return $FAILURE
            } else {
                if {[catch {::sth::sthCore::invoke stc::config $isislevel2teparamsHandle $switchValueList2} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring level 2 TE params handle. Error: $configStatus" {}
                    return $FAILURE
                } else {
                    ::sth::sthCore::log info "The Level 2 TeParams under handle $isisSessionHandle was successfully configured"
                }
            }
        }
    }

    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing TeParams"
        return $SUCCESS
    }  
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_te_router_id(str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###\brief Processes te_router_id switches.
###
### This procedure implements te_router_id switche. Similar to system id & router level, the te router id needs to be configured on
### both IsisRouterConfig and IsisLspConfig
###
###

proc ::sth::IsIs::emulation_isis_config_te_router_id {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    
    set switchName [lindex $switchList 0]
    set switchValue $::sth::IsIs::userArgsArray($switchName)
    set stcAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
    
    # Configure the IsisRouterConfig
    set configList [list "-$stcAttr" $switchValue]
    if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
        set cmdFailed 1
    } else {
        ::sth::sthCore::log info "The switch:$switchName was successfully set to $switchValue"
    }
    
    # Configure the IsisLspConfig
    set configList [list -TERouterID $switchValue]
    foreach lspHandle $isisLspHandle {
        if {[catch {::sth::sthCore::invoke stc::config $lspHandle $configList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
            set cmdFailed 1
        }
    }


    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchName"
        return $SUCCESS
    }
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_config_vlan (str switchList, str returnKeyedList, str HltCmdName, str switchName, str isisSessionHandle);
### The process handling the vlan-related switches.
### All the functions in this set, which are called for mapping in emulation_isis_config, will have the same list of arguments.
### param[in] switchList is the list of switches that to be configured.
### param[in][out] returnKeyedList, update the returnKeyedList: in most cases, this only happens when something goes wrong.
### param[in] HltCmdName, Basically this is used for debugging purpose.
###
###This procedure implements the vlan related switches. This command is used by all the switches with one on one mapping with the STC attributes.
### Configuring VlanIf is much simpler in P2.
###


proc ::sth::IsIs::emulation_isis_config_vlan {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    
    #ISIS 3.00 enhancement 08-10-09
    # avoid configuring vlan inner arguments in ATM encapsulation
    if {[info exists userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} {
        return $SUCCESS
    }
    
    # avoid configuring vlan inner args when "vlan" is disabled
    if {$userArgsArray(vlan) == 0} {
        return $SUCCESS
    }
        
    if {(![info exists ::sth::IsIs::userArgsArray(vlan_id)]) || $userArgsArray(vlan_id) == ""} {
        if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-vlanif} vlanHandles]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error: $vlanHandles"
            return $FAILURE
        }
        if {[llength $vlanHandles] == 0} {
            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $isisRouterHandle. To enable VLAN, specify \"-vlan_id <0-4095>\"."
            return $FAILURE
        }
        if {[llength $vlanHandles] > 1} {
            set vlanHandles [lindex $vlanHandles 0]
        } 
        if {[catch {set vlanID [::sth::sthCore::invoke stc::get $vlanHandles "-$emulation_isis_config_stcattr(vlan_id)"]} msg]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while obtaining value of switches of vlan. Error: $msg" {}
            return $FAILURE
        }
    }

    set configList [list]
    
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set stcAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        lappend configList "-$stcAttr"
        lappend configList $switchValue
    }
    
    if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-vlanif} vlanHandles]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error: $vlanHandles"
        return $FAILURE
    }
    
    if {[llength $vlanHandles] != 0} {
        if {[llength $vlanHandles] > 1} {
            set vlanHandles [lindex $vlanHandles 0]
        }
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandles $configList} configStatus]} {
            set cmdFailed 1
            ::sth::sthCore::processError returnKeyedList "$switchList* Internal Command Error while configuring value of switches of vlan. Error: $configStatus" {}
        }        
    }
        
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Vlan Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchList"
        return $SUCCESS
    }
}


#add QinQ 
proc ::sth::IsIs::emulation_isis_config_vlan_outer {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    
    # avoid configuring vlan out arguments in ATM encapsulation
    if {[info exists userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} {
        return $SUCCESS
    }
    # avoid configuring vlan inner args when "vlan" is disabled    
    if {$userArgsArray(vlan) == 0} {
        return $SUCCESS
    }
        
    if {(![info exists ::sth::IsIs::userArgsArray(vlan_outer_id)]) || $userArgsArray(vlan_outer_id) == ""} {
        if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-vlanif} vlanHandles]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error: $vlanHandles"
            return $FAILURE
        }
        if {[llength $vlanHandles] == 0} {
            ::sth::sthCore::processError returnKeyedList "VLAN not enabled on $isisRouterHandle. To enable VLAN, specify \"-vlan_id <0-4095>\"."
            return $FAILURE
        }
        if {[llength $vlanHandles] < 2} {
            ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $isisRouterHandle. To enable VLAN QinQ, specify \"-vlan_outer_id <0-4095>\"."
            return $FAILURE
        }
        
        set vlanHandles [lindex $vlanHandles 1]
                
        if {[catch {set vlanID [::sth::sthCore::invoke stc::get $vlanHandles "-$emulation_isis_config_stcattr(vlan_outer_id)"]} msg]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while obtaining value of switches of vlan. Error: $msg" {}
            return $FAILURE
        }
    }

    set configList [list]
    
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set stcAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        lappend configList "-$stcAttr"
        lappend configList $switchValue
    }
    
    if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-vlanif} vlanHandles]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error: $vlanHandles"
        return $FAILURE
    }
    if {[llength $vlanHandles] != 0} {
        if {[llength $vlanHandles] < 2} {
            ::sth::sthCore::processError returnKeyedList "VLAN QinQ not enabled on $isisRouterHandle."
            return $FAILURE
        }
        set vlanHandles [lindex $vlanHandles 1]
                        
        if {[catch {::sth::sthCore::invoke stc::config $vlanHandles $configList} configStatus]} {
            set cmdFailed 1
            ::sth::sthCore::processError returnKeyedList "$switchList* Internal Command Error while configuring value of switches of vlan. Error: $configStatus" {}
        }        
    }
        
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Vlan Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchList"
        return $SUCCESS
    }
}

proc ::sth::IsIs::emulation_isis_config_ATM {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {

    variable ::sth::IsIs::emulation_isis_config_stcobj
    variable ::sth::IsIs::emulation_isis_config_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $returnInfoVarName returnKeyedList
    
    set cmdFailed 0
    
    #ISIS 3.00 enhancement 08-10-09
    #add "-atm_encapsulation" to enable or disable ATM
    if {[info exists userArgsArray(atm_encapsulation)] && $userArgsArray(atm_encapsulation) == 1} {
        if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-aal5if} atmHandles]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error: $atmHandles"
            return $FAILURE
        }
        if {[llength $atmHandles] == 0} {
            ::sth::sthCore::processError returnKeyedList "ATM encapsulation is not enabled on $isisRouterHandle."
            return $FAILURE
        }
    } else {
        return $SUCCESS   
    }

    set configList [list]
    
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set stcAttr $::sth::IsIs::emulation_isis_config_stcattr($switchName)
        lappend configList "-Aal5If.$stcAttr"
        lappend configList $switchValue
    }
        
    #vc_mux is not allowed on the ISIS router. 
    lappend configList "-Aal5If.VcEncapsulation"
    lappend configList "LLC_ENCAPSULATED"

    if {[catch {::sth::sthCore::invoke stc::config $isisRouterHandle $configList} configStatus]} {
        set cmdFailed 1
        ::sth::sthCore::processError returnKeyedList "$switchList* Internal Command Error while configuring value of switches of ATM. Error: $configStatus" {}
    }
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "ATM Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$switchList"
        return $SUCCESS
    }
}


#ISIS 3.00 enhancement 08-10-09
# configure isis tpye to be broadcast or p2p
proc ::sth::IsIs::emulation_isis_config_intf_type {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {
        
        variable ::sth::IsIs::emulation_isis_config_stcobj
        variable ::sth::IsIs::emulation_isis_config_stcattr 
        variable ::sth::IsIs::userArgsArray
        variable ::sth::sthCore::FAILURE
        variable ::sth::sthCore::SUCCESS
        
        upvar $returnInfoVarName returnKeyedList
        
        set cmdFailed 0
        set configList 0
        if {[info exists userArgsArray(intf_type)]} {
                if {[string match "broadcast" $userArgsArray(intf_type)]} {
                        set intfType "BROADCAST"
                } elseif {[string match "ptop" $userArgsArray(intf_type)]} {
                        set intfType "P2P"
                }         
        }

        set stcAttr $::sth::IsIs::emulation_isis_config_stcattr($switchList)
        set configList "$stcAttr $intfType"
        
        if {[catch {::sth::sthCore::invoke stc::config $isisSessionHandle $configList} configStatus]} {
                set cmdFailed 1
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while configuring $isisSessionHandleS. Error: $configStatus" {}
        }
    
        if {$cmdFailed > 0} {
                ::sth::sthCore::log debug "Interface Type **NOT** set"
                return $FAILURE
        } else {
                ::sth::sthCore::log debug "Successfully completed processing switch:$switchList"
                return $SUCCESS
        }
              
}
#end of ISIS 3.00 enhancement


#neighbor authentication
proc ::sth::IsIs::emulation_isis_config_authentication {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle isisSessionHandle isisLspHandle} {
        
        variable ::sth::IsIs::userArgsArray
        
        upvar $returnInfoVarName returnKeyedList
                
        set configList ""
        
        switch -exact -- $userArgsArray($_switchName) {
             "none" {
                set configList "-Authentication NONE"
             }
             "simple" {
                # 1-253 alphanumeric characters for password in SIMPLE mode
                if {![info exists userArgsArray(password)]} {
                    set userArgsArray(password) Spirent
                } elseif {[string length $userArgsArray(password)] > 253} {
                    ::sth::sthCore::processError returnKeyedList "The value length of password is range from 1 to 253 characters in simple authentication mode." {}
                    return -code error $returnKeyedList 
                }
                
                set configList "-Authentication SIMPLE -Password $userArgsArray(password)"
             }
             "md5" {
                # 1-16 alphanumeric characters for password in MD5 mode
                if {![info exists userArgsArray(password)]} {
                    set userArgsArray(password) Spirent
                } elseif {[string length $userArgsArray(password)] > 16} {
                   ::sth::sthCore::processError returnKeyedList "The value length of password is range from 1 to 16 characters in md5 authentication mode." {}
                   return -code error $returnKeyedList      
                }
                
                if {![info exists userArgsArray(md5_key_id)]} {
                    set userArgsArray(md5_key_id) 1    
                }
                
                set configList "-Authentication MD5 -Password $userArgsArray(password) -Md5KeyId $userArgsArray(md5_key_id)"
             }
             default {
                ::sth::sthCore::processError returnKeyedList "unknown vlaue for password: $userArgsArray(password)." {}
                return -code error $returnKeyedList         
            }     
        }
            
        if {[catch {set isisAuthentication [lindex [::sth::sthCore::invoke stc::get $isisSessionHandle -children-IsisAuthenticationParams] 0]} err]} {
            ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
            return -code error $returnKeyedList 
        }
        
        if {[catch {::sth::sthCore::invoke stc::config $isisAuthentication $configList} err]} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while configuring $isisSessionHandleS. Error: $err" {}
            return -code error $returnKeyedList 
        }
        
        return $::sth::sthCore::SUCCESS
   
}

##########################################################
#Process functions for emulation_isis_control
#########################################################

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_control_withdraw(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName)
###\brief Processes withdraw switches.
###
###This procedure implements withdraw switche. 
###
###\param[in] switchName Contains the switch
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switch being processed.
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang)
###*/
###
###emulation_isis_control_withdraw(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName);
###

proc ::sth::IsIs::emulation_isis_control_withdraw {switchName retKeyList _hltCmdName _switchName} {

    variable ::sth::IsIs::emulation_isis_control_stcobj
    variable ::sth::IsIs::emulation_isis_control_stcattr
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::sthCore::FAILURE
    variable ::sth::sthCore::SUCCESS
    
    upvar $retKeyList returnKeyedList
    
    set cmdFailed 0
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    #Validate the each route_handle
    set elemhandleList $userArgsArray($switchName)
    ::sth::sthCore::log info "__VALIDATE__: Validate value of route_handle"
    foreach isisHandle $elemhandleList {
        #Validate the handle
        ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
        set msg ""
        if {![::sth::IsIs::IsIsIsLspHandleValid  $isisHandle msg]} {
            # This might be a route handle
            if {[info exists ISISROUTEHNDLIST($isisHandle)]} {
                set isisRouteInfo $ISISROUTEHNDLIST($isisHandle)
                set ipVersion [lindex $isisRouteInfo 1]
                # puts "ipVersion = $ipVersion"
                if {[string equal $ipVersion "6"]} {
                    set isisIpRouteHandle [lindex $isisRouteInfo 3]
                    set routeTypeName RouteType
                } elseif {[string equal $ipVersion "4"]} {
                    set isisIpRouteHandle [lindex $isisRouteInfo 2]
                    set routeTypeName RouteType
                }
                if {[catch {set routeType [::sth::sthCore::invoke stc::get $isisIpRouteHandle -$routeTypeName]} getStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: $getStatus" {}
                    return $FAILURE
                } else {
                    if {[string equal $routeType "INTERNAL"]} {
                        set origTopologyType "stub"
                    } elseif {[string equal $routeType "EXTERNAL"]} {
                        set origTopologyType "external"
                    } else {
                        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: Unknown topology type $routeType of route $isisIpRouteHandle." {}
                        return $FAILURE
                    }
                }
                
                if {[string equal $ipVersion "4_6"]} {
                    lappend isisIpRouteHandle [lindex $isisRouteInfo 3]
                }
            } else {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: The -handle $isisHandle is not valid" {}
                return $FAILURE
            }
        } else {
            set origTopologyType "router"    
        } 
        
        set cmdFailed 0
        switch -exact $origTopologyType {    
            router {    
                set answer y            
                if {$answer == "y"} {
                    if {[catch {::sth::sthCore::invoke stc::delete $isisHandle} msg]} {
                        set cmdFailed 1
                        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: $msg" {}
                    } else {
                        ::sth::sthCore::log info "Successfully deleting router $isisHandle"
                    }
                        
                    if {$cmdFailed} {
                        ::sth::sthCore::log Error "Error occured while deleting stub network $isisHandle"
                        return $FAILURE 
                    } else {
                        ::sth::sthCore::log info "Successfully deleting stub network $isisHandle"
                    }
                } else {
                    ::sth::sthCore::log debug "User cancelled withdrawing the router $isisHandle"
                }
            }
            stub {
                
                if {[catch {::sth::sthCore::invoke stc::perform "IsisWithdrawIpRoutes -IsisIpRouteList $isisIpRouteHandle"} msg]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: $msg" {}
                } else {
                    ::sth::sthCore::log info "Successfully withdrawn router $isisHandle"
                }
                    
                if {$cmdFailed} {
                    ::sth::sthCore::log Error "Error occured while withdrawing stub network $isisHandle"
                    return $FAILURE 
                } else {
                    ::sth::sthCore::log info "Successfully withdrawn stub network $isisHandle"
                }            
            }
            external {
                if {[catch {::sth::sthCore::invoke stc::perform "IsisWithdrawIpRoutes -IsisIpRouteList $isisIpRouteHandle"} msg]} {
                    set cmdFailed 1
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: $msg" {}
                } else {
                    ::sth::sthCore::log info "Successfully withdrawn router $isisHandle"
                }
                    
                if {$cmdFailed} {
                    ::sth::sthCore::log Error "Error occured while withdrawing external network $isisHandle"
                    return $FAILURE 
                } else {
                    ::sth::sthCore::log info "Successfully withdrawn external network $isisHandle"
                }              
            }
            default {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while withdrawing the routes. Error: Unsupported topology type $origTopologyType" {}
                set cmdState $FAILURE
                return $FAILURE
            }    
        }        
    }

 
    if {$cmdFailed} {
        ::sth::sthCore::log debug "Routes are **NOT** withdrawed: $elemhandleList"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }  
}

# The follownig two functions are currently not supported. I am not sure whether they are going to be supported in future.
# ###/*! \ingroup isisswitchprocfuncs
# ###\fn emulation_isis_control_advertise(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName)
# ###\brief Processes withdraw switches.
# ###
# ###This procedure implements advertise switche. 
# ###
# ###\param[in] switchName Contains the switch
# ###\param[in,out] returnInfoVarName Variable which contains the return Info
# ###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
# ###\param[in] _switchName Name of the switch being processed.
# ###\return FAILURE or SUCCESS
# ###
# ###\warning None
# ###\author Jeremy Chang (jchang)
# ###*/
# ###
# ###emulation_isis_control_advertise(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName);
# ###

# proc ::sth::IsIs::emulation_isis_control_advertise {switchName retKeyList _hltCmdName _switchName} {

#     variable ::sth::IsIs::emulation_isis_control_stcobj
#     variable ::sth::IsIs::emulation_isis_control_stcattr
#     variable ::sth::IsIs::userArgsArray
#     variable ::sth::IsIs::ISISROUTEHNDLIST
#     variable ::sth::sthCore::FAILURE
#     variable ::sth::sthCore::SUCCESS
#     
#     
#     upvar $retKeyList returnKeyedList
#     

#     
#     set cmdFailed 0

#     upvar 1 $retKeyList returnKeyedList
#     
#     ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

#     #Validate the each route_handle
#     
#     set elemhandleList $::sth::IsIs::userArgsArray($switchName)
#     ::sth::sthCore::log info "__VALIDATE__: Validate value of route_handle"
#     foreach isisHandle $elemhandleList {
#         #Validate the handle
#         ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
#         set msg ""
#         if {![::sth::IsIs::IsIsIsLspHandleValid $isisHandle msg]} {
#             # This might be a route handle
#             if {[info exists ISISROUTEHNDLIST($isisHandle)]} {
#                 set isisRouteInfo $ISISROUTEHNDLIST($isisHandle)
#                 set ipVersion [lindex $isisRouteInfo 1]
#                 if {[string equal $ipVersion "6"]} {
#                     set isisIpRouteHandle [lindex $isisRouteInfo 3]
#                     set routeTypeName RouteType
#                 } else {
#                     set isisIpRouteHandle [lindex $isisRouteInfo 2]
#                     set routeTypeName RouteType
#                 }
#                 if {[catch {set routeType [::sth::sthCore::invoke stc::get $isisIpRouteHandle -$routeTypeName]} getStatus]} {
#                     ::sth::sthCore::log info "Internal error when getting route type from route handle $isisIpRouteHandle."
#                     set retInfo [::sth::sthCore::updateReturnInfo $returnInfo log "Internal error when getting route type from route handle $isisIpRouteHandle."]
#                     return $FAILURE
#                 } else {
#                     if {[string equal $routeType "INTERNAL"]} {
#                         set origTopologyType "stub"
#                     } elseif {[string equal $routeType "external"]} {
#                         set origTopologyType "external"
#                     } else {
#                         ::sth::sthCore::log info "Unknown topology type $routeType of route $isisIpRouteHandle."
#                         set retInfo [::sth::sthCore::updateReturnInfo $returnInfo log "Unknown topology type $routeType of route $isisIpRouteHandle."]
#                         return $FAILURE
#                     }
#                 }
#                 
#                 if {[string equal $ipVersion "4_6"]} {
#                     lappend isisIpRouteHandle [lindex $isisRouteInfo 3]
#                 }
#             } else {
#                 ::sth::sthCore::log debug "The handle $isisHandle is not valid"
#                 set retInfo [::sth::sthCore::updateReturnInfo $returnInfo log "The handle $isisHandle is not valid"]
#                 return $FAILURE
#             }
#         } else {
#             set origTopologyType "router"    
#         }
#         set cmdFailed 0
#         switch -exact $origTopologyType {    
#             router {
#                 # Once a LSP is created, it is automatically advertised. Therefore advertise of router is not supported.
#             }
#             stub {
#                 #advertise ip routes
#                 if {[catch {::sth::sthCore::invoke stc::perform "IsisEstablishIpRoutes -IsisIpRouteList $isisIpRouteHandle"} msg]} {
#                     set cmdFailed 1
#                     set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while advertising topology element:$isisHandle"]
#                 } else {
#                     ::sth::sthCore::log info "Successfully advertised router $isisHandle"
#                 }
#                     
#                 if {$cmdFailed} {
#                     ::sth::sthCore::log Error "Error occured while advertising stub network $isisHandle"
#                     return $FAILURE 
#                 } else {
#                     ::sth::sthCore::log info "Successfully advertised stub network $isisHandle"
#                 }            
#             }
#             external {
#                 #process router_delete 
#                 if {[catch {::sth::sthCore::invoke stc::perform "IsisEstablishIpRoutes -IsisIpRouteList $isisIpRouteHandle"} msg]} {
#                     set cmdFailed 1
#                     set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while advertising topology element:$isisHandle"]
#                 } else {
#                     ::sth::sthCore::log info "Successfully advertised router $isisHandle"
#                 }
#                     
#                 if {$cmdFailed} {
#                     ::sth::sthCore::log Error "Error occured while advertising external network $isisHandle"
#                     return $FAILURE 
#                 } else {
#                     ::sth::sthCore::log info "Successfully advertised external network $isisHandle"
#                 }              
#             }
#             default {
#                 ::sth::sthCore::log info "Unable to retrieve original type information: Unknown Type $origTopologyType"
#                 set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while deleting topology element:$isisHandle"]
#                 set cmdState $FAILURE
#                 return $FAILURE
#             }    
#         }        
#     }

#  
#     if {$cmdFailed} {
#         ::sth::sthCore::log debug "Routes are **NOT** advertised: $elemhandleList"
#         return $FAILURE
#     } else {
#         ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
#         return $SUCCESS
#     }  
#     
# }


# ###/*! \ingroup isisswitchprocfuncs
# ###\fn emulation_isis_control_flap(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName)
# ###\brief Processes withdraw switches.
# ###
# ###This procedure implements withdraw switche. 
# ###
# ###\param[in] switchName Contains the switch
# ###\param[in,out] returnInfoVarName Variable which contains the return Info
# ###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
# ###\param[in] _switchName Name of the switch being processed.
# ###\return FAILURE or SUCCESS
# ###
# ###
# ###emulation_isis_control_flapFunc(str switchValue, keyedListRef returnInfoVarName, str _hltCmdName, str _switchName);
# ###

# proc ::sth::IsIs::emulation_isis_control_flapFunc {switchName retKeyList _hltCmdName _switchName} {

#     variable ::sth::IsIs::emulation_isis_control_stcobj
#     variable ::sth::IsIs::emulation_isis_control_stcattr
#     variable ::sth::IsIs::userArgsArray
#     variable ::sth::IsIs::ISISROUTEHNDLIST
#     variable ::sth::sthCore::FAILURE
#     variable ::sth::sthCore::SUCCESS
#     
#     
#     upvar $retKeyList returnKeyedList
#     

#     
#     set cmdFailed 0
#     
#     ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
#     
#     if {([info exists userArgsArray(flap_routes)] && [info exists userArgsArray(flap_count)] && [info exists userArgsArray(flap_down_time)] && [info exists userArgsArray(flap_interval_time)])} {
#         set elemHandleList $userArgsArray(flap_routes)
#         set flapCount $userArgsArray(flap_count)
#         set flapDowntime $::sth::IsIs::userArgsArray(flap_down_time)
#         set flapIntervaltime $::sth::IsIs::userArgsArray(flap_interval_time)    
#     } else {
#         ::sth::sthCore::log Error "Parameters flap_routes, flap_count, flap_down_time and flap_interval_time are needed"
#         set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Error: One or more of the parameters flap_routes, flap_count, flap_down_time and flap_interval_time are needed are missing."]
#         return $FAILURE
#     }
#     
#     #Validate the each route_handle
#     ::sth::sthCore::log info "__VALIDATE__: Validate value of route_handle"
#     set flapHandleList [list]
#     set flapRouterList [list]
#     foreach isisHandle $elemhandleList {
#         #Validate the handle
#         ::sth::sthCore::log info "__VALIDATE__: Validate value of handle"
#         set msg ""
#         if {![::sth::IsIs::IsIsIsLspHandleValid $isisHandle msg]} {
#             # This might be a route handle
#             if {[info exists ISISROUTEHNDLIST($isisHandle)]} {
#                 set isisRouteInfo ISISROUTEHNDLIST($isisHandle)
#                 set ipVersion [lindex $isisRouteInfo 1]
#                 if {[string equal $ipVersion "6"]} {
#                     set isisIpRouteHandle [lindex $isisRouteInfo 3]
#                     set routeTypeName RouteType
#                 } else {
#                     set isisIpRouteHandle [lindex $isisRouteInfo 2]
#                     set routeTypeName RouteType
#                 }
#                 if {[catch {set routeType [::sth::sthCore::invoke stc::get $isisIpRouteHandle -$routeTypeName]} getStatus]} {
#                     ::sth::sthCore::log info "Internal error when getting route type from route handle $isisIpRouteHandle."
#                     return $FAILURE
#                 } else {
#                     if {[string equal $routeType "INTERNAL"]} {
#                         set origTopologyType "stub"
#                         lappend flapHandleList $isisIpRouteHandle
#                     } elseif {[string equal $routeType "EXTERNAL"]} {
#                         set origTopologyType "external"
#                         lappend flapHandleList $isisIpRouteHandle
#                     } else {
#                         ::sth::sthCore::log info "Unknown topology type $routeType of route $isisIpRouteHandle."
#                         return $FAILURE
#                     }
#                 }
#                 
#                 if {[string equal $ipVersion "4_6"]} {
#                     lappend isisIpRouteHandle [lindex $isisRouteInfo 3]
#                     lappend flapHandleList [lindex $isisRouteInfo 3]
#                 }
#             } else {
#                 ::sth::sthCore::log debug "The handle $isisHandle is not valid"
#                 return $FAILURE
#             }
#         } else {
#             set origTopologyType "router"    
#         }
#     }
#         
#     # one flap = withdraw -> sleep for flap_down_time -> advertise -> sleep for flap_interval_time
#     for {set i 0} {$i < $flapCount} {incr i} {
#         if {[catch {::sth::sthCore::invoke stc::perform IsisWithdrawIpRoutes -IsisIpRouteList $flapHandleList} msg]} {
#             ::sth::sthCore::log Error "Unable to flap. Error: $msg"
#             set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while withdrawing topology element during flapping :$flapHandleList"]
#             set cmdFailed 1
#             break
#         }
#         
#         if {[catch {::sth::sthCore::invoke stc::sleep $flapDowntime} msg]} {
#             ::sth::sthCore::log Error "Unable to flap. Error: $msg"
#             set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while in down time of flapping :$flapHandleList"]
#             set cmdFailed 1
#             break
#         }
#         
#         if {[catch {::sth::sthCore::invoke stc::perform IsisEstablishIpRoutes -IsisIpRouteList $flapHandleList} msg]} {
#             ::sth::sthCore::log Error "Unable to flap. Error: $msg"
#             set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while advertising topology element during flapping :$flapHandleList"]
#             set cmdFailed 1
#             break
#         }
#         
#         if {[catch {::sth::sthCore::invoke stc::sleep $flapIntervaltime} msg]} {
#             ::sth::sthCore::log Error "Unable to flap. Error: $msg"
#             set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList log "Internal Command Error while in up time of flapping :$flapHandleList"]
#             set cmdFailed 1
#             break
#         }
#     }
#  
#     if {$cmdFailed} {
#         ::sth::sthCore::log debug "Routes are **NOT** flapped: $flapHandleList"
#         return $FAILURE
#     } else {
#         ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
#         return $SUCCESS
#     }  
#     
# }





##########################################################
#Process functions for emulation_isis_topology_route_config
#########################################################


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_NetworkBlock_external(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType)
###\brief Processes external related switch which need to access NetworkBlock
###
###This procedure implements the configuration on NetworkBlock for all external related switches.
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_NetworkBlock_external (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_NetworkBlock_external {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    #Validate the switch is applicable for the type 
    if {![string equal $topologyType "external"]} {
        #ignore the config, since the type is not external 
         ::sth::sthCore::log debug "$_switchName is ignored.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    #variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set handleValues $handleVar
    
    # retrieve the ip version & NetworkBlock Handle.
    foreach handleValue $handleValues {
        set routeInfoList $ISISROUTEHNDLIST($handleValue)
        set ipVersion [lindex $routeInfoList 1]
        
        set ipv6List ""
        set ipv4RouteHandle ""
        set ipv6RouteHandle ""
        set ipv4networkblockHandle ""
        set ipv6networkblockHandle ""
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            set ipv4RouteHandle [lindex $routeInfoList 2]
            if {[catch {set ipv4networkblockHandle [::sth::sthCore::invoke stc::get $ipv4RouteHandle -children-ipv4networkblock]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the route handle. Error: $getStatus" {}
                return $FAILURE
            }
            set optValList {}
            foreach switchName {external_count external_ip_pfx_len external_ip_start external_ip_step} {
                if {[lsearch $switchList $switchName] == -1} { continue }
                set switchValue $userArgsArray($switchName)
                set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
                if {[string match $switchName external_ip_step] && [llength [split [::ip::normalize $switchValue] .]] == 4} {
                    set switchValue [convertIpStepToInt $switchValue $userArgsArray(external_ip_pfx_len)]
                }
                lappend optValList -$switchAttr $switchValue
            }
            if {[llength $optValList]} {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4networkblockHandle $optValList} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while configuring $optValList   Error: $eMsg" {}
                    set cmdFailed 1
                    return $FAILURE
                }
            }
        }
        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            set ipv6RouteHandle [lindex $routeInfoList 3]
            if {[catch {set ipv6networkblockHandle [::sth::sthCore::invoke stc::get $ipv6RouteHandle -children-ipv6networkblock]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "Internal Command Error while getting the route handle. Error: $getStatus" {}
                return $FAILURE
            }
            set optValList {}
            foreach switchName {external_count external_ipv6_pfx_len external_ipv6_start external_ipv6_step} {
                if {[lsearch $switchList $switchName] == -1} { continue }
                set switchValue $userArgsArray($switchName)
                set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
                if {[string match $switchName external_ipv6_step] && [llength [split [::ip::normalize $switchValue] :]] == 8} {
                    set switchValue [convertIpStepToInt $switchValue $userArgsArray(external_ipv6_pfx_len)]
                }
                lappend optValList -$switchAttr $switchValue
            }
            if {[llength $optValList]} {
                if {[catch {::sth::sthCore::invoke stc::config $ipv6networkblockHandle $optValList} eMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Internal Command Error while configuring $optValList   Error: $eMsg" {}
                    set cmdFailed 1
                    return $FAILURE
                }
            }
        }
    }
    
    ::sth::sthCore::log debug "Successfully completed processing switch: for HltCmd:$_hltCmdName"
    return $SUCCESS
}

    
###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_external_metric(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType)
###\brief Processes external related switch which need to access NetworkBlock
###
###This procedure implements the configuration on metric
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_external_metric (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_external_metric {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST

    #Validate the switch is applicable for the type 
    if {!( [string equal $topologyType "external"])} {
        #ignore the config, since the type is not external 
         ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }
    
    set handleValues $handleVar
    foreach handleValue $handleValues {
        if {[string equal $userArgsArray(mode) "create"]} {
            set isisRouterHandle $userArgsArray(handle)
            if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $isisRouterHandle -children-isisrouterconfig]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the route. Error: $getStatus" {}
                return $FAILURE
            }
            set ipVersion $userArgsArray(ip_version)
            set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
            set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        } else {
            #get lsp handle
            set isisLspHandle [lindex $ISISROUTEHNDLIST($handleValue) 0]
            set ipVersion [lindex $ISISROUTEHNDLIST($handleValue) 1]
            set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
            set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        
            #get session handle 
            if {![::sth::IsIs::getIsIsSessionHandle $isisLspHandle isisSessionHandle]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the route. Error: Cannot LSP handle from the router handle." {}    
                return $FAILURE
            }
        }

        #retreive metric type from isisSession
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $isisSessionHandle -MetricMode]} getStatus ]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring the route. Error: $getStatus" {}
            return $FAILURE
        } else {
            set metMode $getValueVar
        }
    
        set metricValue $userArgsArray(external_metric)
    
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            # Configure ipv4IsisRouteHandle
            if {[string equal $metMode NARROW] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle "-Metric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch:$_switchName. Error:$configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }
            }    
            if {[string equal $metMode WIDE] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle "-WideMetric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch:$_switchName. Error $configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }    
            }
        } 

        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            # Configure ipv6IsisRouteHandle, narrow metric mode is not supported in ipv6
            if {[string equal $metMode WIDE] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv6IsisRouteHandle "-WideMetric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch:$_switchName. Error: $configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }    
            } else {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch:$_switchName: Unsupported metric mode $metMode under ip version $ipVersion" {}
                set cmdFailed 1
            }
        }
    }

    if {[::info exists cmdFailed]} {
    ::sth::sthCore::log debug "$_hltCmdName: $_switchName Value **NOT** set"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_external(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType)
###\brief Processes external related switch which need to access Ipv4/6IsisRouteConfig
###
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_external (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_external {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_external_metric_type_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"
    
    #Validate the switch is applicable for the type 
    if {![string equal $topologyType "external"]} {
        #ignore the config, since the type is not external 
        ::sth::sthCore::log debug "$_switchName is ignored.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }
    
    set handleValues $handleVar
    foreach handleValue $handleValues {
        set ipVersion [lindex $ISISROUTEHNDLIST($handleValue) 1]
        set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
        set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        
        set ipv4ConfigList {}
        set ipv6ConfigList {}
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
            if {[string equal $switchName external_metric_type]} {
                # configure external_metric_type (IPv4 routes only)
                if {[string match 4* $ipVersion]} {
                    set switchAttr "MetricType"
                    set switchValue $emulation_isis_topology_route_config_external_metric_type_fwdmap($switchValue)
                    lappend ipv4ConfigList -$switchAttr $switchValue
                }
            } else {
                lappend ipv4ConfigList -$switchAttr $switchValue
                lappend ipv6ConfigList -$switchAttr $switchValue
            }
        }
     
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle $ipv4ConfigList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv6IsisRouteHandle $ipv6ConfigList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
    }
    
    ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
    return $SUCCESS
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_te_info(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType)
###\brief Processes external related switch which need to access TEParams under IsisLspNeighborConfig
###
###This procedure implements the configuration on TEParams under IsisLspNeighborConfig
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_external (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);

proc ::sth::IsIs::emulation_isis_topology_route_config_te_info {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_link_te_fwdmap    
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    #Validate the switch is applicable for the type 
    if {!([string equal $topologyType "router"])} {
        #ignore the config, since the type is not router
        ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
        return $SUCCESS
    }
    
    #Validate the neighbor info
    if {$nbrHandleVar == -1 } {
        ::sth::sthCore::processError returnKeyedList "Dependent switches -router_connect for switch -$_switchName is/are not specified correctly or missing." {}
        return $FAILURE
    }
    
    foreach nbrHandleValue $nbrHandleVar {
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $nbrHandleValue -children-TeParams]} getStatus ]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while processing switch. Error: $getStatus" {}
            return $FAILURE
        } else {
            set teParamsHandle $getValueVar
        }
    
        set switchValueList [list -BandwidthUnit BYTES_PER_SEC] ;# bandwidths must always be specified in bytes/sec
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
            if {[string equal $switchName link_te]} {
                continue
            }
            lappend switchValueList -$switchAttr
            lappend switchValueList $switchValue
        }
        lappend switchValueList "-SubTlv"
        lappend switchValueList [calc_te_subtlv $switchList]
        if {[catch {::sth::sthCore::invoke stc::config $teParamsHandle $switchValueList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
            set cmdFailed 1
            break
        }
    }

    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_lsp_generator_te_info(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisRouterHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to access TEParams under IsisLspGenPramas
###
###This procedure implements the configuration on TEParams under IsisLspGenPramas
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of router created before. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_lsp_generator_te_info {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

proc ::sth::IsIs::emulation_isis_lsp_generator_te_info {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedList modify funcSwitchList]

    if {[regexp {emulation_isis_lsp_generator_te_info} $funcSwitchList]} {
        if {!($userArgsArray(traffic_engineered_enabled))} {
            ::sth::sthCore::processError returnKeyedList "make sure traffic_engineered_enabled is true when configure TE parameter" {}
            keylset returnKeyedList status $FAILURE
            return $FAILURE
        }
    }
    if {[catch {::sth::sthCore::invoke stc::create TeParams -under $IsisLspGenParams_Handler} TeParamsHandle]} {
        ::sth::sthCore::processError returnKeyedList "create TeParams failed: $TeParamsHandle" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    lappend switchValueList "-SubTlv"
    lappend switchValueList [calc_te_subtlv $switchList]
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $TeParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
    }
    }

    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }
}


proc ::sth::IsIs::emulation_isis_topology_ipv4_internal {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with 'internal_'
    if {[regexp -nocase {\-internal_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv4_internal_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }
    if {[emulation_isis_iproute_dependency "emulation_isis_topology_ipv4_internal" returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(ipv4_internal_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(ipv4_internal_emulated_routers) "ALL"
    }

    set ipv4RouteHandle ""
    set ipv4RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv4RouteGenParams]
    if {$ipv4RouteHandleList != ""} {
        foreach ipv4RouteHnd $ipv4RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv4RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "INTERNAL" $routeType]} {
                set ipv4RouteHandle $ipv4RouteHnd
                break
            }
        }
    }

    if {$ipv4RouteHandle == ""} {
        set ipv4RouteHandle [sth::sthCore::invoke stc::create Ipv4RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv4RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType INTERNAL
    }
    
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4RouteHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_topology_ipv4_internal_routegen {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-internal_'
    if {[regexp -nocase {\-internal_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv4_internal_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }

    set isisLspHandle ""
    set ipv4RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv4RouteGenParams]
    if {$ipv4RouteHandleList != ""} {
        foreach ipv4RouteHnd $ipv4RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv4RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "INTERNAL" $routeType]} {
                set isisLspHandle $isisLspHandle
                break
            }
        }
    }

    if {$isisLspHandle == ""} {
        set ipv4RouteHandle [sth::sthCore::invoke stc::create Ipv4RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv4RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType INTERNAL
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $isisLspHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}


proc ::sth::IsIs::emulation_isis_topology_ipv4_external {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-external_'
    if {[regexp -nocase {\-external_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv4_external_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }
    if {[emulation_isis_iproute_dependency "emulation_isis_topology_ipv4_external" returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(ipv4_external_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(ipv4_external_emulated_routers) "ALL"
    }

    set ipv4RouteHandle ""
    set ipv4RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv4RouteGenParams]
    if {$ipv4RouteHandleList != ""} {
        foreach ipv4RouteHnd $ipv4RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv4RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "EXTERNAL" $routeType]} {
                set ipv4RouteHandle $ipv4RouteHnd
                break
            }
        }
    } 

    if {$ipv4RouteHandle == ""} {
        set ipv4RouteHandle [sth::sthCore::invoke stc::create Ipv4RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv4RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType EXTERNAL
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $ipv4RouteHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_topology_ipv4_external_routegen {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-external_'
    if {[regexp -nocase {\-external_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv4_external_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }

    set isisLspHandle ""
    set ipv4RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv4RouteGenParams]
    if {$ipv4RouteHandleList != ""} {
        foreach ipv4RouteHnd $ipv4RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv4RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "EXTERNAL" $routeType]} {
                set isisLspHandle $isisLspHandle
                break
            }
        }
    }

    if {$isisLspHandle == ""} {
        set ipv4RouteHandle [sth::sthCore::invoke stc::create Ipv4RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv4RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType EXTERNAL
    }

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $isisLspHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_topology_ipv6_internal {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-internal_'
    if {[regexp -nocase {\-internal_} $userArgsArray(optional_args)] ||
        ![regexp -nocase {\-ipv6_internal_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }
    if {[emulation_isis_iproute_dependency "emulation_isis_topology_ipv6_internal" returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(ipv6_internal_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(ipv6_internal_emulated_routers) "ALL"
    }

    set ipv6RouteHandle ""
    set ipv6RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv6RouteGenParams]
    if {$ipv6RouteHandleList != ""} {
        foreach ipv6RouteHnd $ipv6RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv6RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "INTERNAL" $routeType]} {
                set ipv6RouteHandle $ipv6RouteHnd
                break
            }
        }
    }

    if {$ipv6RouteHandle == ""} {
        set ipv6RouteHandle [sth::sthCore::invoke stc::create Ipv6RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv6RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType INTERNAL
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6RouteHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_topology_ipv6_internal_routegen {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-internal_'
    if {[regexp -nocase {\-internal_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv6_internal_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }

    set isisLspHandle ""
    set ipv6RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv6RouteGenParams]
    if {$ipv6RouteHandleList != ""} {
        foreach ipv6RouteHnd $ipv6RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv6RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "INTERNAL" $routeType]} {
                set isisLspHandle $isisLspHandle
                break
            }
        }
    }

    if {$isisLspHandle == ""} {
        set ipv6RouteHandle [sth::sthCore::invoke stc::create Ipv6RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv6RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType INTERNAL
    }

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $isisLspHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}


proc ::sth::IsIs::emulation_isis_topology_ipv6_external {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-external_'
    if {[regexp -nocase {\-external_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv6_external_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }
    if {[emulation_isis_iproute_dependency "emulation_isis_topology_ipv6_external" returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(ipv6_external_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(ipv6_external_emulated_routers) "ALL"
    }

    set ipv6RouteHandle ""
    set ipv6RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv6RouteGenParams]
    if {$ipv6RouteHandleList != ""} {
        foreach ipv6RouteHnd $ipv6RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv6RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "EXTERNAL" $routeType]} {
                set ipv6RouteHandle $ipv6RouteHnd
                break
            }
        }
    }

    if {$ipv6RouteHandle == ""} {
        set ipv6RouteHandle [sth::sthCore::invoke stc::create Ipv6RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv6RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType EXTERNAL
    }

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $ipv6RouteHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_topology_ipv6_external_routegen {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    #Do not process for old similar options starting with '-external_'
    if {[regexp -nocase {\-external_} $userArgsArray(optional_args)]||
        ![regexp -nocase {\-ipv6_external_} $userArgsArray(optional_args)]} {
        return $SUCCESS;
    }

    set isisLspHandle ""
    set ipv6RouteHandleList [sth::sthCore::invoke stc::get $IsisLspGenParams_Handler -children-Ipv6RouteGenParams]
    if {$ipv6RouteHandleList != ""} {
        foreach ipv6RouteHnd $ipv6RouteHandleList {
            set isisLspHandle [sth::sthCore::invoke stc::get $ipv6RouteHnd -children-IsisLspGenRouteAttrParams]
            set routeType [sth::sthCore::invoke stc::get $isisLspHandle -RouteType]
            if {[string match -nocase "EXTERNAL" $routeType]} {
                set isisLspHandle $isisLspHandle
                break
            }
        }
    }

    if {$isisLspHandle == ""} {
        set ipv6RouteHandle [sth::sthCore::invoke stc::create Ipv6RouteGenParams -under $IsisLspGenParams_Handler]
        set isisLspHandle [sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $ipv6RouteHandle]
        sth::sthCore::invoke stc::config $isisLspHandle -RouteType EXTERNAL
    }

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $isisLspHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}

proc ::sth::IsIs::emulation_isis_lsp_generator_sr_info {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler

    set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedList modify funcSwitchList]

    if {[regexp {emulation_isis_lsp_generator_sr_info} $funcSwitchList]} {
        if {!($userArgsArray(segment_routing_enabled))} {
            ::sth::sthCore::processError returnKeyedList "make sure segment_routing_enabled is true when configure segment routing" {}
            keylset returnKeyedList status $FAILURE
            return $FAILURE
        }
    }
    
    set SRParamsHandle [sth::sthCore::invoke stc::create IsisSegmentRoutingParams -under $IsisLspGenParams_Handler]

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }

    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $SRParamsHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS

}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_type_lsp_gen_params(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisRouterHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to access xxxxTopologyGenParams under IsisLspGenParams
###
###This procedure implements the configuration on xxxxTopologyGenParams under IsisLspGenParams
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of router created before. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_type_lsp_gen_params {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_type_lsp_gen_params {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler
    
    set _hltCmdName "emulation_isis_topology_type_lsp_gen_params"
    
    if {[emulation_isis_iproute_dependency $_hltCmdName returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    
    switch  -exact -- $topologyType {
        tree {
              set  sub_project TreeTopologyGenParams
        }
        fullmesh {
              set  sub_project FullMeshTopologyGenParams 
        }
        grid {
              set  sub_project GridTopologyGenParams 
        }
        hubspoke {
              set  sub_project HubSpokeTopologyGenParams 
        }
        ring {
              set  sub_project RingTopologyGenParams 
        }
        none {
              ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName (topology_type : none)"
              keylset returnKeyedList status $SUCCESS
              return $SUCCESS
        }
        }
    
    if {[catch {::sth::sthCore::invoke stc::create $sub_project -under $IsisLspGenParams_Handler} TopologyGenParamsHandle]} {
        ::sth::sthCore::processError returnKeyedList "create $sub_project failed:$TopologyGenParamsHandle" {}
        keylset returnKeyedList status  $FAILURE
        return $FAILURE
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        switch  -exact -- $switchName {
                hubspoke_num_routers -
                hubspoke_emulated_router_pos {
                        if {$topologyType != "hubspoke"} {
                                continue        
                        }        
                }

                fullmesh_num_routers -
                fullmesh_emulated_router_pos {
                        if {$topologyType != "fullmesh"} {
                                continue        
                        }        
                }

                ring_num_routers -
                ring_emulated_router_pos {
                        if {$topologyType != "ring"} {
                                continue        
                        }
                }

                tree_if_type -
                tree_max_if_per_router -
                tree_max_routers_per_transit_network -
                tree_num_simulated_routers {
                        if {$topologyType != "tree"} {
                                continue        
                        }
                }

                grid_attach_column_index -
                grid_attach_row_index -
                grid_columns -
                grid_rows -
                grid_emulated_router_pos {
                        if {$topologyType != "grid"} {
                                continue        
                        }
                }

        }

        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $TopologyGenParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }

    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }

}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_lsp_gen_params(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisRouterHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to access IsisLspGenPramas under project1
###
###This procedure implements the configuration on TEPaIsisLspGenPramas under project1
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of router created before. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_lsp_gen_params {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_lsp_gen_params {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler
    
    variable ::sth::GBLHNDMAP
    if {[catch {::sth::sthCore::invoke stc::create IsisLspGenParams -under $GBLHNDMAP(project) "-SelectedRouterRelation-targets \"$isisRouterHandle\""} IsisLspGenParamsHandle]} {
        ::sth::sthCore::processError returnKeyedList "create IsisLspGenParams failed" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    
    #store the IsisLspGenParams handler
    set IsisLspGenParams_Handler $IsisLspGenParamsHandle
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        if {[string equal $switchName system_id_start]} {
                set switchValue [::sth::IsIs::convertSystemId $switchValue]
        }
        if {[string equal $switchName system_id_step]} {
                set switchValue [::sth::IsIs::convertSystemId $switchValue]
        }
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $IsisLspGenParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }
    keylset returnKeyedList elem_handle   $IsisLspGenParamsHandle
    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_iproute_gen_params(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisRouterHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to access IpvxRouteGenParams under IsisLspGenPramas
###
###This procedure implements the configuration on IpvxRouteGenParams under IsisLspGenPramas
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of router created before. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_iproute_gen_params {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_iproute_external {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {
    upvar 1 $returnInfoVarName returnKeyedListTmp
    set _hltCmdName "emulation_isis_topology_iproute_external"
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::SUCCESS

    #Do not process for new similar options starting with '-ipv4_external_'
    if {[regexp -- {\-ipv4_external_} $userArgsArray(optional_args)] ||
        ![regexp -- {\-external_} $userArgsArray(optional_args)]} {
        return $SUCCESS
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(external_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(external_emulated_routers) "ALL"
    }
    return [emulation_isis_topology_iproute $switchList returnKeyedListTmp $_hltCmdName $_switchName $isisRouterHandle $ipVersion $topologyType]
}

proc ::sth::IsIs::emulation_isis_topology_iproute_internal {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {
    upvar 1 $returnInfoVarName returnKeyedListTmp
    set _hltCmdName "emulation_isis_topology_iproute_internal"
    variable ::sth::IsIs::userArgsArray
    variable ::sth::sthCore::SUCCESS

    #Do not process for new similar options starting with '-ipv4_internal_'
    if {[regexp -- {\-ipv4_internal_} $userArgsArray(optional_args)] ||
        ![regexp -- {\-internal_} $userArgsArray(optional_args)]} {
        return $SUCCESS
    }
    #As per native STC, For NONE topo type, the default values of simulated and emulated routers is different
    if {[string match -nocase "NONE" $::sth::IsIs::userArgsArray(type)]} {
        set ::sth::IsIs::userArgsArray(internal_simulated_routers) "NONE"
        set ::sth::IsIs::userArgsArray(internal_emulated_routers) "ALL"
    }
    return [emulation_isis_topology_iproute $switchList returnKeyedListTmp $_hltCmdName $_switchName $isisRouterHandle $ipVersion $topologyType]
}


proc ::sth::IsIs::emulation_isis_iproute_dependency {functionName returnKeyedList} {
        variable ::sth::sthCore::SUCCESS
        variable ::sth::sthCore::FAILURE
        variable ::sth::IsIs::userArgsArray
        upvar 1 $returnKeyedList returnKeyedListDependency
        set priorityList [::sth::IsIs::processSwitches emulation_isis_lsp_generator ::sth::IsIs:: returnKeyedListDependency modify funcSwitchList]
        array set funcSwitchArray $funcSwitchList
        if {[info exists funcSwitchArray($functionName)]} {
                set switchList $funcSwitchArray($functionName)
        } else {
                return $SUCCESS 
        }
        
        foreach switchName $switchList {
                switch -exact -- $switchName {
                        tree_max_routers_per_transit_network {
                                if {$userArgsArray(tree_if_type) == "POINT_TO_POINT"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "tree_max_routers_per_transit_network is unavailable when tree_if_type is POINT_TO_POINT" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE      
                                }        
                        }
                        internal_iproute_ipv6_addr_end -
                        internal_iproute_ipv6_addr_start -
                        internal_iproute_ip_addr_end -
                        internal_iproute_ip_addr_start {
                                if {$userArgsArray(internal_enable_ip_addr_override) == "false"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "internal_enable_ip_addr_override:true is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        internal_prefix_length_end -
                        internal_prefix_v6_length_end {
                                if {$userArgsArray(internal_prefix_length_dist_type) == "FIXED" || \
                                        $userArgsArray(internal_prefix_length_dist_type) == "CUSTOM" ||\
                                        $userArgsArray(internal_prefix_length_dist_type) == "INTERNET"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "internal_prefix_length_dist_type:LINEAR or EXPONENTIAL is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        internal_prefix_length_start -
                        internal_prefix_v6_length_start {
                                if {$userArgsArray(internal_prefix_length_dist_type) == "CUSTOM" ||\
                                        $userArgsArray(internal_prefix_length_dist_type) == "INTERNET"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "internal_prefix_length_dist_type:LINEAR or EXPONENTIAL or FIXED is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                                if {$userArgsArray(internal_prefix_length_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                        external_iproute_ipv6_addr_end -
                        external_iproute_ipv6_addr_start -
                        external_iproute_ip_addr_end -
                        external_iproute_ip_addr_start {
                                if {$userArgsArray(external_enable_ip_addr_override) == "false"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "external_enable_ip_addr_override:true is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        external_prefix_length_end -
                        external_prefix_v6_length_end {
                                if {$userArgsArray(external_prefix_length_dist_type) == "FIXED" || \
                                        $userArgsArray(external_prefix_length_dist_type) == "CUSTOM" ||\
                                        $userArgsArray(external_prefix_length_dist_type) == "INTERNET"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "external_prefix_length_dist_type:LINEAR or EXPONENTIAL is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        external_prefix_length_start -
                        external_prefix_v6_length_start {
                                if {$userArgsArray(external_prefix_length_dist_type) == "CUSTOM" ||\
                                        $userArgsArray(external_prefix_length_dist_type) == "INTERNET"} {
                                        ::sth::sthCore::processError returnKeyedListDependency "external_prefix_length_dist_type:LINEAR or EXPONENTIAL or FIXED is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                                if {$userArgsArray(external_prefix_length_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                        internal_prefix_length_dist {
                                if {$userArgsArray(external_prefix_length_dist_type) != "CUSTOM" } {
                                        ::sth::sthCore::processError returnKeyedListDependency "internal_prefix_length_dist_type:CUSTOM is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        external_prefix_length_dist {
                                if {$userArgsArray(external_prefix_length_dist_type) != "CUSTOM" } {
                                        ::sth::sthCore::processError returnKeyedListDependency "external_prefix_length_dist_type:CUSTOM is a must for $switchName" {}
                                        keylset returnKeyedListDependency status $FAILURE
                                        return $FAILURE
                                }
                        }
                        ipv4_internal_prefix_len_start {
                                if {$userArgsArray(ipv4_internal_prefix_len_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                        ipv6_internal_prefix_len_start {
                                if {$userArgsArray(ipv6_internal_prefix_len_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                        ipv4_external_prefix_len_start {
                                if {$userArgsArray(ipv4_external_prefix_len_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                        ipv6_external_prefix_len_start {
                                if {$userArgsArray(ipv6_external_prefix_len_dist_type) == "FIXED"} {
                                       set userArgsArray([regsub {start$} $switchName {end}]) $userArgsArray($switchName)
                                }
                        }
                }
        }
        if {$userArgsArray(internal_prefix_length_start) > $userArgsArray(internal_prefix_length_end)} {
                ::sth::sthCore::processError returnKeyedListDependency "internal_prefix_length_start must be less than internal_prefix_length_end" {}
                keylset returnKeyedListDependency status $FAILURE
                return $FAILURE
        }
        if {$userArgsArray(external_prefix_length_start) > $userArgsArray(external_prefix_length_end)} {
                ::sth::sthCore::processError returnKeyedListDependency "external_prefix_length_start must be less than external_prefix_length_end" {}
                keylset returnKeyedListDependency status $FAILURE
                return $FAILURE
        }
        if {$userArgsArray(internal_prefix_v6_length_start) > $userArgsArray(internal_prefix_v6_length_end)} {
                ::sth::sthCore::processError returnKeyedListDependency "internal_prefix_v6_length_start must be less than internal_prefix_v6_length_end" {}
                keylset returnKeyedListDependency status $FAILURE
                return $FAILURE
        }
        if {$userArgsArray(external_prefix_v6_length_start) > $userArgsArray(external_prefix_v6_length_end)} {
                ::sth::sthCore::processError returnKeyedListDependency "external_prefix_v6_length_start must be less than external_prefix_v6_length_end" {}
                keylset returnKeyedListDependency status $FAILURE
                return $FAILURE
        }
        return $SUCCESS

}
proc ::sth::IsIs::emulation_isis_topology_iproute {switchList returnInfoVarName _hltCmdName _switchName isisRouterHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler
    
    append sub_project "Ipv" "$ipVersion" "RouteGenParams"
    if {$_hltCmdName == "emulation_isis_lsp_generator_create"} {
        set _hltCmdName "emulation_isis_topology_iproute_internal"
    }
    if {[emulation_isis_iproute_dependency $_hltCmdName returnKeyedList] == $FAILURE} {
        return $FAILURE
    }
    if {[catch {::sth::sthCore::invoke stc::create $sub_project -under $IsisLspGenParams_Handler} IpRouteGenParamsHandle]} {
        ::sth::sthCore::processError returnKeyedList "create $sub_project failed:$IpRouteGenParamsHandle" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        
        if {$ipVersion == 4} {
                switch -exact -- $switchName {
                        internal_iproute_ipv6_addr_end -
                        internal_iproute_ipv6_addr_start -
                        internal_prefix_v6_length_end -
                        internal_prefix_v6_length_start -
                        external_iproute_ipv6_addr_end -
                        external_iproute_ipv6_addr_start -
                        external_prefix_v6_length_end -
                        external_prefix_v6_length_start {
                                continue
                                }
                        }
        } else {
                switch -exact -- $switchName {
                        internal_iproute_ip_addr_end -
                        internal_iproute_ip_addr_start -
                        internal_prefix_length_end -
                        internal_prefix_length_start -
                        external_iproute_ip_addr_end -
                        external_iproute_ip_addr_start -
                        external_prefix_length_end -
                        external_prefix_length_start {
                                continue
                                }
                        }        
        }
        if {    $emulation_isis_lsp_generator_stcobj($switchName) == "IsisLspGenRouteAttrParams"} {
                set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
                lappend switchValueListAttr -$switchAttr
                lappend switchValueListAttr $switchValue
        } else {
                set emulation_isis_lsp_generator_stcobj($switchName) $sub_project
                set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
                lappend switchValueList -$switchAttr
                lappend switchValueList $switchValue
        }
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $IpRouteGenParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }
    if {[catch {::sth::sthCore::invoke stc::create IsisLspGenRouteAttrParams -under $IpRouteGenParamsHandle} IsisLspGenRouteAttrParamsHandler]} {
        ::sth::sthCore::processError returnKeyedList "create IsisLspGenRouteAttrParams failed:$IsisLspGenRouteAttrParamsHandler" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    if {[info exists switchValueListAttr]} {
    if {[catch {::sth::sthCore::invoke stc::config $IsisLspGenRouteAttrParamsHandler $switchValueListAttr} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }
    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }

}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_lsp_generator_te_info_modify(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisLspHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to modify TEParams under IsisLspGenPramas
###
###This procedure modifies the configuration on TEParams under IsisLspGenPramas
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisLspHandle The handle of LSP Generator. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_lsp_generator_te_info_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_lsp_generator_te_info_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    
    if {[catch {set teEnabled [::sth::sthCore::invoke stc::get $isisLspHandle -TeEnabled]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "interal cmd error to get -TeEnabled from object $isisLspHandle :$getStatus" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    if {!($teEnabled)} {
        ::sth::sthCore::processError returnKeyedList "There is no configure about TE parameter. You have to create at first" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
        }
        
    if {[catch {set TeParamsHandle [::sth::sthCore::invoke stc::get $isisLspHandle -children-TeParams]} getStatus]} {
        ::sth::sthCore::processError returnKeyedList "interal cmd error to get -children-TeParams from object $isisLspHandle :$getStatus" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $TeParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }

    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }
}

proc ::sth::IsIs::emulation_isis_prefix_sid_tlv_flags_ipv4_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    
    if {[regexp -nocase {6} $isisLspHandle]} {
        ::sth::sthCore::processError returnKeyedList "ipv4_isis_prefix_sid_tlv_flags not supported for ipv6"
        return $FAILURE
    }

    set ipv4IsisRoutesConfigHandle [::sth::sthCore::invoke stc::get $isisLspHandle -parent]
    set isisPrefixSidSubTlvHandleList [::sth::sthCore::invoke stc::get $ipv4IsisRoutesConfigHandle -children-IsisPrefixSidSubTlv]
    set IsisPrefixSidSubTlvHandle [lindex $isisPrefixSidSubTlvHandleList 0]

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $IsisPrefixSidSubTlvHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS
}


proc ::sth::IsIs::emulation_isis_prefix_sid_tlv_flags_ipv6_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    
    if {[regexp -nocase {4} $isisLspHandle]} {
        ::sth::sthCore::processError returnKeyedList "ipv6_isis_prefix_sid_tlv_flags_ipv6 not supported for ipv4"
        return $FAILURE
    }

    set ipv6IsisRoutesConfigHandle [::sth::sthCore::invoke stc::get $isisLspHandle -parent]
    set isisPrefixSidSubTlvHandleList [::sth::sthCore::invoke stc::get $ipv6IsisRoutesConfigHandle -children-IsisPrefixSidSubTlv]
    set IsisPrefixSidSubTlvHandle [lindex $isisPrefixSidSubTlvHandleList 0]


    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $IsisPrefixSidSubTlvHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS
}


proc ::sth::IsIs::emulation_isis_lsp_generator_sr_info_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    
    set srEnabled [::sth::sthCore::invoke stc::get $isisLspHandle -SREnabled]

    if {!($srEnabled)} {
        ::sth::sthCore::processError returnKeyedList "There is no configure about Segment Routing parameter. You have to create at first" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }

    set srParamsHandle [::sth::sthCore::invoke stc::get $isisLspHandle -children-IsisSegmentRoutingParams]

    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
        ::sth::sthCore::invoke stc::config $srParamsHandle $switchValueList
    }

    keylset returnKeyedList status $SUCCESS
    return $SUCCESS
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_type_lsp_gen_params_modify(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisLspHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to modify xxxxTopologyGenParams under IsisLspGenPramas
###
###This procedure modifies the configuration on xxxxTopologyGenParams under IsisLspGenPramas
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of LSP Generator. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_type_lsp_gen_params_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_type_lsp_gen_params_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::processError returnKeyedList "topology_type modify is not supported for HltCmd:$_hltCmdName" {}
    keylset returnKeyedList status $FAILURE
    return $FAILURE
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_lsp_gen_params_modify(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisLspHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to modify IsisLspGenPramas under project1
###
###This procedure modifies the configuration on IsisLspGenPramas under project1
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of LSP Generator. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_lsp_gen_params_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_lsp_gen_params_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    

 
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        if {[string equal $switchName system_id_start]} {
                set switchValue [::sth::IsIs::convertSystemId $switchValue]
        }
        if {[string equal $switchName system_id_step]} {
                set switchValue [::sth::IsIs::convertSystemId $switchValue]
        }
        set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
        lappend switchValueList -$switchAttr
        lappend switchValueList $switchValue
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $isisLspHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }
    keylset returnKeyedList elem_handle   $isisLspHandle
    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }
}

###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_iproute_gen_params_modify(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str isisLspHandle, str ip_version, str topologyType)
###\brief Processes external related switch which need to modify IpvxRouteGenParams under IsisLspGenPramas
###
###This procedure modifies the configuration on IpvxRouteGenParams under IsisLspGenPramas
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] isisRouterHandle The handle of LSP Generator. 
###\param[in] ip_version The ip version info of isisRouterHandle (4|6). 
###\param[in] topology_type topology configuration type (fullmesh|grid|hubspoke|ring|tree|none). 
###\return keyedListRef
###
###\warning None
###\author WestWang.
###*/
###
###emulation_isis_topology_iproute_gen_params_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {
proc ::sth::IsIs::emulation_isis_topology_iproute_external_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {
        upvar 1 $returnInfoVarName returnKeyedListTmp
        return [emulation_isis_topology_iproute_internal_modify $switchList returnKeyedListTmp $_hltCmdName $_switchName $isisLspHandle $ipVersion $topologyType]
}
proc ::sth::IsIs::emulation_isis_topology_iproute_internal_modify {switchList returnInfoVarName _hltCmdName _switchName isisLspHandle ipVersion topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcobj
    variable ::sth::IsIs::emulation_isis_lsp_generator_stcattr    
    variable ::sth::IsIs::IsisLspGenParams_Handler
    
    append sub_project "Ipv" "$ipVersion" "RouteGenParams"
    
 
    if {[catch {set IpRouteGenParamsHandle [::sth::sthCore::invoke stc::get $isisLspHandle -children-$sub_project]} getStatus]}  {
        ::sth::sthCore::processError returnKeyedList "get $sub_project failed:$getStatus" {}
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    }
    
    #config all parameters
    foreach switchName $switchList {
        set switchValue $userArgsArray($switchName)
        if {[regexp -nocase {internal} $switchName]} {
                set route_type "INTERNAL"        
        } else {
                set route_type "EXTERNAL"
        }
        if {$ipVersion == 4} {
                switch -exact -- $switchName {
                        internal_iproute_ipv6_addr_end -
                        internal_iproute_ipv6_addr_start -
                        internal_prefix_v6_length_end -
                        internal_prefix_v6_length_start -
                        external_iproute_ipv6_addr_end -
                        external_iproute_ipv6_addr_start -
                        external_prefix_v6_length_end -
                        external_prefix_v6_length_start {
                                continue
                                }
                        }
        } else {
                switch -exact -- $switchName {
                        internal_iproute_ip_addr_end -
                        internal_iproute_ip_addr_start -
                        internal_prefix_length_end -
                        internal_prefix_length_start -
                        external_iproute_ip_addr_end -
                        external_iproute_ip_addr_start -
                        external_prefix_length_end -
                        external_prefix_length_start {
                                continue
                                }
                        }        
        }
        
        if {    $emulation_isis_lsp_generator_stcobj($switchName) == "IsisLspGenRouteAttrParams"} {
                set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
                lappend switchValueListAttr -$switchAttr
                lappend switchValueListAttr $switchValue
        } else {
                set emulation_isis_lsp_generator_stcobj($switchName) $sub_project
                set switchAttr $emulation_isis_lsp_generator_stcattr($switchName)
        
                lappend switchValueList -$switchAttr
                lappend switchValueList $switchValue
        }
    }
    foreach ipRoute [split $IpRouteGenParamsHandle " "] {
        if {[catch {set IsisLspGenRouteAttrParamsHandle [::sth::sthCore::invoke stc::get $ipRoute -children-IsisLspGenRouteAttrParams]} getStatus]}  {
                ::sth::sthCore::processError returnKeyedList "get IsisLspGenRouteAttrParams failed:$getStatus" {}
                keylset returnKeyedList status $FAILURE
                return $FAILURE
        }
        if {[catch {set IsisLspGenRouteType [::sth::sthCore::invoke stc::get $IsisLspGenRouteAttrParamsHandle -RouteType]} getStatus]}  {
                ::sth::sthCore::processError returnKeyedList "get RouteType failed:$getStatus" {}
                keylset returnKeyedList status $FAILURE
                return $FAILURE
        }
        if {$IsisLspGenRouteType == $route_type} {
                set IpRouteGenParamsHandle $ipRoute
                break
        }
    }
    if {[info exists switchValueList]} {
    if {[catch {::sth::sthCore::invoke stc::config $IpRouteGenParamsHandle $switchValueList} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }

    if {[info exists switchValueListAttr]} {
    if {[catch {::sth::sthCore::invoke stc::config $IsisLspGenRouteAttrParamsHandle $switchValueListAttr} configStatus]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
        set cmdFailed 1
        
    }
    }
    if {[info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        keylset returnKeyedList status $FAILURE
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        keylset returnKeyedList status $SUCCESS
        return $SUCCESS
    }

}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_neighbor(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes switch relate to neighbor parameters 
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###
###emulation_isis_topology_route_config_neighbor (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_neighbor {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    #Validate the switch is applicable for the type 
    if {!([string equal $topologyType "router"])} {
        #ignore the config, since the type is not router
        ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }
    
    #Validate the neighbor info
    if {$nbrHandleVar == -1 } {
        ::sth::sthCore::processError returnKeyedList "Dependent switches -router_connect for switch -$_switchName is/are not specified correctly or missing." {}
        return $FAILURE     
    }
    
    set switchName [lindex $switchList 0]
    set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
    set switchValue $userArgsArray($switchName)

    set configList [list -$switchAttr $switchValue]
    foreach nbrHandleValue $nbrHandleVar {
        if {[catch {::sth::sthCore::invoke stc::config $nbrHandleValue $configList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
            set cmdFailed 1
        }
    }

    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_lsp(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes switch relate to emulated router parameters 
###
###This procedure implements the configuration on IsisLsp for all the te related switches
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###
###emulation_isis_topology_route_config_lsp (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_lsp {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_router_routing_level_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    # Validate the switch is applicable for the type 
    if {!([string equal $topologyType "router"])} {
        ::sth::sthCore::log debug "$_switchName is being ignored. Type must be \"router\"."
        return $SUCCESS
    }
    
    set levelIndex 1 ;# used for creating LEVEL1 and LEVEL2 LSPs
    
    foreach handleValue $handleVar {
        set switchValueList {}
        foreach switchName $switchList {
            set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
            set switchValue $userArgsArray($switchName)
            if {[string equal $switchName router_routing_level]} {
                set switchValue $emulation_isis_topology_route_config_router_routing_level_fwdmap($switchValue)
                if {[string match -nocase "LEVEL1_AND_2" $switchValue]} {
                    # Create LEVEL1 and LEVEL2 LSPs
                    set switchValue LEVEL$levelIndex
                    incr levelIndex
                }
            } elseif {[string equal $switchName router_te]} {
                if {$switchValue == 0} {
                    #set switchValue "0.0.0.0"
                    set switchValue null
                } else {
                    continue
                }
            } elseif {[string equal $switchName router_system_id]} {
                set switchValue [::sth::IsIs::convertSystemId $switchValue]
            } elseif {[string match $switchName router_id]} {
                if {[info exists userArgsArray(router_te)] && $userArgsArray(router_te) == 0} {
                    continue
                }
            }
            lappend switchValueList -$switchAttr $switchValue
        }
            
        if {[catch {::sth::sthCore::invoke stc::config $handleValue $switchValueList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
            set cmdFailed 1
        }
    }

    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_router_connect(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes router_connect switch 
###
###This procedure implements the configuration 
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_router_connect (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_router_connect {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList

    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    set nbrHandleValue $nbrHandleVar

    set switchName [lindex $switchList 0]
    set switchValue $userArgsArray($switchName)
    set cmdFailed 0
    #Validate the switch is applicable for the type 
    if {!([string equal $topologyType "router"]) } {
        #ignore the config, since the type is not router
         ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }

    #Validate the neighbor info
    if {$nbrHandleValue == -1 } {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: isisNeighbor handle is not created ." {}
        return $FAILURE     
    }

    #Validate the handle 
    if {![::sth::IsIs::IsIsIsLspHandleValid $switchValue msg]} {
        ::sth::sthCore::processError returnKeyedList "The value $switchValue is not a valid value for switch -router_connect ." {}
        return $returnInfo  
    } 
    
    #Validate the handle
    set handleValues $handleVar
    foreach handleValue $handleValues {
        if {$handleValue == $switchValue} {
            ::sth::sthCore::processError returnKeyedList "Internal Command Error while processing $_switchName: Can not connect router to itself" {}
            return $returnInfo  
        }
    }
    
    # get information for neighbor from connect isisLsp
    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $switchValue -Lifetime]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
        return $FAILURE
    } else {
        set lifeTime [lindex $getValueVar 0]
    }        

    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $switchValue -NeighborPseudonodeId]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
        return $FAILURE
    } else {
        set NeighborPseudonodeId [lindex $getValueVar 0]
    }  

    if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $switchValue -SystemId]} getStatus ]} {
        ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
        return $FAILURE
    } else {
        set sysId [lindex $getValueVar 0]
    }  
    # configure the neighbor
    
    set configList [list -NeighborSystemId $sysId -NeighborPseudonodeId $NeighborPseudonodeId]
    foreach nbrHandle $nbrHandleValue {
        if {[catch {::sth::sthCore::invoke stc::config $nbrHandle $configList} configStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
            set cmdFailed 1
            break
        }
    }
    
    if {$cmdFailed > 0} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}




###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_NetworkBlock_stub(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes stub related switch which need to access NetworkBlock
###
###This procedure implements the configuration on NetworkBlock for all stub related switch except those have common mapping for IPv4 and IPv6.
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_NetworkBlock_stub ((str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_NetworkBlock_stub {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    #Validate the switch is applicable for the type 
    if {!( [string equal $topologyType "stub"])} {
        #ignore the config, since the type is not external 
         ::sth::sthCore::log debug "$_switchName is ignored.  Possible not applicable with type $topologyType"
        return $SUCCESS     
    }
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    # set handleValue $handleVar
    foreach handleValue $handleVar {
        # retrieve the ip version & NetworkBlock Handle.
        set routeInfoList $ISISROUTEHNDLIST($handleValue)
        set ipVersion [lindex $routeInfoList 1]
        
        set ipv4RouteHandle ""
        set ipv6RouteHandle ""
        set ipv4networkblockHandle ""
        set ipv6networkblockHandle ""
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            set ipv4RouteHandle [lindex $routeInfoList 2]
            if {[catch {set ipv4networkblockHandle [::sth::sthCore::invoke stc::get $ipv4RouteHandle -children-ipv4networkblock]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
                return $FAILURE
            }
        }
        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            set ipv4RouteHandle [lindex $routeInfoList 3]
            if {[catch {set ipv6networkblockHandle [::sth::sthCore::invoke stc::get $ipv4RouteHandle -children-ipv6networkblock]} getStatus]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
                return $FAILURE
            }
        }
        
        set ipv4List [list stub_count stub_ip_pfx_len stub_ip_start stub_ip_step]
        set ipv6List [list stub_count stub_ipv6_pfx_len stub_ipv6_start stub_ipv6_step]
        set ipv4SwitchValueList [list]
        set ipv6SwitchValueList [list]
        foreach switchName $switchList {
            if {[lsearch $ipv4List $switchName]>=0} {
                set switchValue $userArgsArray($switchName)
                set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
                if {[string match $switchName stub_ip_step] && [llength [split [::ip::normalize $switchValue] .]] == 4} {
                    set switchValue [convertIpStepToInt $switchValue $userArgsArray(stub_ip_pfx_len)]
                }
                lappend ipv4SwitchValueList -$switchAttr
                lappend ipv4SwitchValueList $switchValue
            }
            if {[lsearch $ipv6List $switchName]>=0} {
                set switchValue $userArgsArray($switchName)
                set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
                if {[string match $switchName stub_ipv6_step] && [llength [split [::ip::normalize $switchValue] :]] == 8} {
                    set switchValue [convertIpStepToInt $switchValue $userArgsArray(stub_ipv6_pfx_len)]
                }
                lappend ipv6SwitchValueList -$switchAttr
                lappend ipv6SwitchValueList $switchValue
            }
        }

        if {$ipv4networkblockHandle != ""} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv4networkblockHandle $ipv4SwitchValueList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $eMsg" {}
                set cmdFailed 1
                return $FAILURE
            }
        }

        if {$ipv6networkblockHandle != ""} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv6networkblockHandle $ipv6SwitchValueList} eMsg]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $eMsg" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
    }

    ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
    return $SUCCESS
}



###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_stub_metric(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes stub_metric switch 
###
###This procedure implements the configuration on IsisIPRoute for stub_metric switch 
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_stub_metric (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_stub_metric {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    # set handleValue $handleVar    
    foreach handleValue $handleVar {
        #Validate the switch is applicable for the type 
        if {!( [string equal $topologyType "stub"])} {
            #ignore the config, since the type is not external 
             ::sth::sthCore::log debug "$_switchName is ignored.  Possible not applicable with type $topologyType"
            return $SUCCESS     
        }

        if {[string equal $userArgsArray(mode) "create"]} {
            set isisRouterHandle $userArgsArray(handle)
            if {[catch {set isisSessionHandle [::sth::sthCore::invoke stc::get $isisRouterHandle -children-isisrouterconfig]} getStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}    
                return $FAILURE
            }
            set ipVersion $userArgsArray(ip_version)
            set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
            set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        } else {
            #get lsp handle
            set isisLspHandle [lindex $ISISROUTEHNDLIST($handleValue) 0]
            set ipVersion [lindex $ISISROUTEHNDLIST($handleValue) 1]
            set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
            set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        
            #get session handle 
            if {![::sth::IsIs::getIsIsSessionHandle $isisLspHandle isisSessionHandle]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $unable to fetch IsisRouter from IsisLsp handle: isisLspHandle" {}        
                return $FAILURE
            }
        }
        
        #retreive metric type from isisSession
        if {[catch {set getValueVar [::sth::sthCore::invoke stc::get $isisSessionHandle -MetricMode]} getStatus ]} {
            ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $getStatus" {}
            return $FAILURE
        } else {
            set metMode $getValueVar
        }

        set metricValue $userArgsArray(stub_metric)
        
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            # Configure ipv4IsisRouteHandle
            if {[string equal $metMode NARROW] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle "-Metric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }
            }    
            if {[string equal $metMode WIDE] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle "-WideMetric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }    
            }
        } 

        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            # Configure ipv4IsisRouteHandle, narrow metric mode is not supported in ipv6
            if {[string equal $metMode WIDE] || [string equal $metMode NARROW_AND_WIDE] } {
                if {[catch {::sth::sthCore::invoke stc::config $ipv6IsisRouteHandle "-WideMetric $metricValue"} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring switch. Error: $configStatus" {}
                    set cmdFailed 1
                } else {
                    ::sth::sthCore::log info "The switch:$_switchName was/were successfully configured"
                }    
            }
        } 
    }
    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}


###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_stub(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes stub related switch which need to access IsisIpRoute 
###
###This procedure implements the configuration on IsisIPRoute for stub related switch 
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_stub (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_stub {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    # set handleValue $handleVar    
    foreach handleValue $handleVar {
        #Validate the switch is applicable for the type 
        if {!( [string equal $topologyType "stub"])} {
            #ignore the config, since the type is not external 
            ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
            return $SUCCESS
        }
        
        set ipVersion [lindex $ISISROUTEHNDLIST($handleValue) 1]
        set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
        set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]
        
        set configList [list]
        foreach switchName $switchList {
            set switchValue $userArgsArray($switchName)
            set switchAttr $emulation_isis_topology_route_config_stcattr($switchName)
            lappend configList -$switchAttr
            lappend configList $switchValue
        }
        
    #     puts "configList = $configList"
        
        if {([string equal $ipVersion "4"] || [string equal $ipVersion "4_6"])} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
        if {([string equal $ipVersion "6"] || [string equal $ipVersion "4_6"])} {
            if {[catch {::sth::sthCore::invoke stc::config $ipv6IsisRouteHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                set cmdFailed 1
                return $FAILURE
            }
        }
    }
    ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
    return $SUCCESS
}




###/*! \ingroup isisswitchprocfuncs
###\fn emulation_isis_topology_route_config_type(str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###\brief Processes type switch in emulation_isis_topology_route_config 
###
###This procedure implements the configuration for type switch of emulation_isis_topology_route_config 
###
###\param[in] switchList Contains the all the switches related to this function
###\param[in,out] returnInfoVarName Variable which contains the return Info
###\param[in] _hltCmdName Name of the hlt command name withoug namespace.
###\param[in] _switchName Name of the switches being processed, currently same as switchList
###\param[in] handleVar The handle of LSP or IpRoute object which config needs to be done. 
###\param[in] nbrHandleVar The handle of neigbor object. 
###\param[in] topologyType topology configuration type (router|stub|external). 
###\return FAILURE or SUCCESS
###
###\warning None
###\author Jeremy Chang (jchang), modified by Tong Zhou for P2.
###*/
###
###emulation_isis_topology_route_config_type (str switchList, keyedListRef returnInfoVarName, str _hltCmdName, str switchName, str handleVar, str nbrHandleVar, str topologyType);
###

proc ::sth::IsIs::emulation_isis_topology_route_config_type {switchList returnInfoVarName _hltCmdName _switchName handleVar nbrHandleVar topologyType} {

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE

    upvar 1 $returnInfoVarName returnKeyedList
    
    variable ::sth::IsIs::userArgsArray
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcobj
    variable ::sth::IsIs::emulation_isis_topology_route_config_stcattr
    variable ::sth::IsIs::emulation_isis_topology_route_config_type_fwdmap
    variable ::sth::IsIs::ISISLSPIPVER
    variable ::sth::IsIs::ISISROUTEHNDLIST
    variable ::sth::IsIs::ISISLSPNEIGHBORLIST
    set route_type ""
    ::sth::sthCore::log debug "Processing switch: -$_switchName for Command: $_hltCmdName"

    # set handleValue $handleVar    
    foreach handleValue $handleVar {
        #Validate the switch is applicable for the type 
        if {!([string equal $topologyType "stub"] || [string equal $topologyType "external"])} {
            #ignore the config, since the type is not external or stub
            ::sth::sthCore::log debug "$_switchName is ignore.  Possible not applicable with type $topologyType"
            return $SUCCESS     
        }
        puts $handleValue
        set ipVersion [lindex $ISISROUTEHNDLIST($handleValue) 1]
        set ipv4IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 2]
        set ipv6IsisRouteHandle [lindex $ISISROUTEHNDLIST($handleValue) 3]

        set switchName [lindex $switchList 0]
        set switchValue $userArgsArray($switchName)
        
        if {[string equal $switchValue "external"] && [regexp "modify" $_hltCmdName]} {
             if {[string equal $ipVersion "4"] || [string equal $ipVersion "4_6"]} {
                set route_type [stc::get $ipv4IsisRouteHandle -RouteType]
             } elseif {[string equal $ipVersion "6"] || [string equal $ipVersion "4_6"]} {
                set route_type [stc::get $ipv6IsisRouteHandle -RouteType]
             }
         }
        
        if {[string equal $switchValue "external"]} {
            set routeType EXTERNAL
        } else {
            set routeType INTERNAL
        }
        

        set configList [list -RouteType $routeType]
        if {[string equal $ipVersion "4"] || [string equal $ipVersion "4_6"]} {
            if {$route_type eq " " } {
            if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                set cmdFailed 1
            }
            }
            if {[string equal $switchValue stub]} {
                if {[catch {::sth::sthCore::invoke stc::config $ipv4IsisRouteHandle {-MetricType INTERNAL}} configStatus]} {
                    ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch. Error: $configStatus" {}
                    set cmdFailed 1
                  }
            }
        }
        if {[string equal $ipVersion "6"] || [string equal $ipVersion "4_6"]} {
            if {$route_type eq " " } {
            if {[catch {::sth::sthCore::invoke stc::config $ipv6IsisRouteHandle $configList} configStatus]} {
                ::sth::sthCore::processError returnKeyedList "$_switchName* Internal Command Error while configuring value of switch: Error: $configStatus" {}
                set cmdFailed 1
            }
            }
        }
    }

    if {[::info exists cmdFailed]} {
        ::sth::sthCore::log debug "Value **NOT** set to $switchValue"
        return $FAILURE
    } else {
        ::sth::sthCore::log debug "Successfully completed processing switch:$_switchName for HltCmd:$_hltCmdName"
        return $SUCCESS
    }
}

proc ::sth::IsIs::configBfdRegistration {rtrHandle mode} {
    variable ::sth::IsIs::userArgsArray
    
    if {[catch {set IsIsRtrHandle [::sth::sthCore::invoke stc::get $rtrHandle -children-isisrouterconfig]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList          
    }
    if {[catch {set ipVersion [::sth::sthCore::invoke stc::get $IsIsRtrHandle -IpVersion]} err]} {
        ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
        return -code error $returnKeyedList          
    }
    
    if {[regexp -nocase "ipv4_and_ipv6" $ipVersion]} {
        set ipVersion {ipv4 ipv6}
    }
    foreach ip $ipVersion {
        if {[catch {set ipIfHandle [ ::sth::sthCore::invoke stc::get $rtrHandle -children-$ip\if ]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList          
        }
        #For Ipv6, there are two Ipv6Ifs under the router, get the global link one
        set ipIfHandle [lindex $ipIfHandle 0]
        
        
        if {[catch {set ipaddr [::sth::sthCore::invoke stc::get $ipIfHandle -Address]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::get Failed: $err" {}
                return -code error $returnKeyedList  
        }  
    }
    
    if {$userArgsArray(bfd_registration) == "1"} {
        
        #create bfdrouterconfig
        set bfdrtrcfg [::sth::sthCore::invoke stc::get $rtrHandle -children-bfdrouterconfig]
        if {[llength $bfdrtrcfg] == 0} {
            if {[catch {set bfdrtrcfg [::sth::sthCore::invoke stc::create "BfdRouterConfig" -under $rtrHandle]} err]} {
                ::sth::sthCore::processError returnKeyedList "stc::create  Failed: $err" {}
                return -code error $returnKeyedList 
            }
        }
        if {[catch {::sth::sthCore::invoke stc::config $IsIsRtrHandle "-EnableBfd true"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    } elseif {$userArgsArray(bfd_registration) == "0"} {
        if {[catch {::sth::sthCore::invoke stc::config $IsIsRtrHandle "-EnableBfd false"} error]} {
            ::sth::sthCore::processError returnKeyedList "stc::config Failed: $error" {}
            return -code error $returnKeyedList 
        }
    }
}  

proc ::sth::IsIs::updateDefaultSystemId {isisRouterHandle} {
    variable userArgsArray
    
    if {![info exists userArgsArray(intf_ip_addr)]} {
        # get the default interface address
        if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -children-ipv4If} ipv4IfHdl]} {
            return -code error "Internal Command Error while fetching IPv4If. Error: $ipv4IfHdl"
        }
        if {[llength $ipv4IfHdl] == 1} {
            set ipAddr [::sth::sthCore::invoke stc::get $ipv4IfHdl -Address]
            set userArgsArray(system_id) "0200[::sth::IsIs::ipToHexFormat $ipAddr]"
        } else {
            # in the case of IPv6 only ISIS routers, use the router id
            if {[catch {::sth::sthCore::invoke stc::get $isisRouterHandle -RouterId} rtrId]} {
                return -code error "Internal Command Error while fetching RouterId. Error: $rtrId"
            }
            set userArgsArray(system_id) "0200[::sth::IsIs::ipToHexFormat $rtrId]"
        }
    } else {
        set ipAddr $userArgsArray(intf_ip_addr)
        set userArgsArray(system_id) "0200[::sth::IsIs::ipToHexFormat $ipAddr]"
    }
    return $userArgsArray(system_id)
}


### ending for namespace comment for doc
