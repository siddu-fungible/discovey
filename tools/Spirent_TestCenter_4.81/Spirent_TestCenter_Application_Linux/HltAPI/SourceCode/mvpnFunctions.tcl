# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.
package require Tclx
namespace eval ::sth::Mvpn {
    set createResultQuery 0
}

proc ::sth::Mvpn::emulation_mvpn_provider_port_config_add { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_provider_port_config"    
    set _hltCmdName "emulation_mvpn_provider_port_config_add"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set corePortParamsHdlList [::sth::sthCore::invoke stc::get $mvpnGenParamsHdl -Children-MvpnGenCorePortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenCorePortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set mvpnGenCorePortHdl ""
    foreach corePortParamsHdl $corePortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $corePortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $corePortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set mvpnGenCorePortHdl $corePortParamsHdl
        }
    }
    
    if { $mvpnGenCorePortHdl == ""} {
        if {[catch {set mvpnGenCorePortHdl [::sth::sthCore::invoke stc::create "MvpnGenCorePortParams" -under $mvpnGenParamsHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenCorePortParams under $mvpnGenParamsHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $mvpnGenCorePortHdl "-AffiliationPort-Targets $portHandle"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to config -AffiliationPort-Targets to $mvpnGenCorePortHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    set objList "MvpnGenCorePortParams"
    array set cmdArray {
        MvpnGenCorePortParams ""
    }
    array set hdlArray {
        MvpnGenCorePortParams ""
    }
    set hdlArray(MvpnGenCorePortParams) $mvpnGenCorePortHdl
    
    #Configure the created MvpnGenCorePortParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenCorePortParams: $returnKeyedList"
        #Delete the MvpnGenCorePortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenCorePortHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenCorePortParams:$mvpnGenCorePortHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_provider_port_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_provider_port_config"    
    set _hltCmdName "emulation_mvpn_provider_port_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    
    if { $mvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: No Mvpn has been configured. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {set corePortParamsHdlList [::sth::sthCore::invoke stc::get $mvpnGenParamsHdl -Children-MvpnGenCorePortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenCorePortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set mvpnGenCorePortHdl ""
    foreach corePortParamsHdl $corePortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $corePortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $corePortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set mvpnGenCorePortHdl $corePortParamsHdl
        }
    }
    
    if { $mvpnGenCorePortHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: Current Mvpn configuration doesn't include certain port:$portHandle. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenCorePortHdl} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenCorePortParams:$mvpnGenCorePortHdl Msg: $eMsg"
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_config"    
    set _hltCmdName "emulation_mvpn_config_create"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    set objList "MvpnGenParams VpnMplsRsvpSessionParams VpnMplsLdpSessionParams VpnIgpOspfv2SessionParams VpnIgpIsisSessionParams Ospfv2AuthenticationParams IsisAuthenticationParams"
    array set cmdArray {
        MvpnGenParams ""
        VpnMplsRsvpSessionParams ""
        VpnMplsLdpSessionParams ""
        VpnIgpOspfv2SessionParams ""
        VpnIgpIsisSessionParams ""
        Ospfv2AuthenticationParams ""
        IsisAuthenticationParams ""
    }
    array set hdlArray {
        MvpnGenParams ""
        VpnMplsRsvpSessionParams ""
        VpnMplsLdpSessionParams ""
        VpnIgpOspfv2SessionParams ""
        VpnIgpIsisSessionParams ""
        Ospfv2AuthenticationParams ""
        IsisAuthenticationParams ""
    }
    
    set hdlArray(MvpnGenParams) $mvpnGenParamsHdl
    
    set protocolList {VpnMplsRsvpSessionParams VpnMplsLdpSessionParams VpnIgpOspfv2SessionParams VpnIgpIsisSessionParams }
    
    foreach protocolSession $protocolList {
        if {[catch {set hdlArray($protocolSession) [::sth::sthCore::invoke stc::get $mvpnGenParamsHdl -Children-$protocolSession]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocolSession from $mvpnGenParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if { $hdlArray($protocolSession) == ""} {
            if {[catch {set hdlArray($protocolSession) [::sth::sthCore::invoke stc::create "$protocolSession" -under $mvpnGenParamsHdl]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList  "Unable to create $protocolSession under $mvpnGenParamsHdl. Error: $errMsg"  {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    if {[catch {set hdlArray(Ospfv2AuthenticationParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnIgpOspfv2SessionParams) -Children-Ospfv2AuthenticationParams ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Unable to fetch -Children-Ospfv2AuthenticationParams from $hdlArray(VpnIgpOspfv2SessionParams). Error: $errMsg"  {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set hdlArray(IsisAuthenticationParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnIgpIsisSessionParams) -Children-IsisAuthenticationParams ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Unable to fetch -Children-IsisAuthenticationParams from $hdlArray(VpnIgpIsisSessionParams). Error: $errMsg"  {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #Configure the created objects with user input (options)
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mpls_protocol)] &&
        [set ${_hltSpaceCmdName}\_user_input_args_array(mpls_protocol)] == "none"} {
        puts "INFO: switch -mpls_protocol has been set to \"none\". In this case, the unicast VPN traffic can not be sent, \
                switch -unicast_traffic_enable will be forced to 0 (false), and all unicast traffic relavant swtiches are unavailable."
        set ${_hltSpaceCmdName}\_user_input_args_array(unicast_traffic_enable) 0
    }
    
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
        #if processing function is processConfigCmd, append the attribute/value pair to 
	#corresponding array element for processing later        
        if {[string equal $switchProcFunc "processConfigCmd"]} {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            if { $stcAttrName == "VpnCustRouteStep"} {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(customer_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif { $stcAttrName == "VpnCoreRouteStep" } {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(provider_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }
    
    if {[info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenParams: $returnKeyedList"
        #Delete the MvpnGenCustPortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenParamsHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenParams:$mvpnGenParamsHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Error: No M-VPN has been configured." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set pre_streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set pre_streamList [concat $pre_streamList $stream]
        }
    }
    if {[catch {set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform VpnGenConfigExpand -clearportconfig no -genparams $mvpnGenParamsHdl}]} {
	::sth::sthCore::processError returnKeyedList "Unable to expand M-VPN configuration." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set streamList [concat $streamList $stream]
        }
    }
    if {[catch {set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    #get new created devices' handles within mvpn 
    foreach stream $pre_streamList {
        set x [lsearch $streamList $stream]
        if { $x > -1 } {
            set streamList [lreplace $streamList $x $x]
        }
    }
    
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    
    set vpnIdGroupHdl ""
    set emulatedDeviceHdl ""
    set ipv4GroupHdl ""
    set vpnSiteInfoHdl ""
    set hostHdl ""
    set ceRouter ""
    set peRouter ""
    set peVrfRouter ""
    set pRouter ""
    set rrRouter ""
    foreach child $childrenList {
        if { [string first "vpnidgroup" [string tolower $child]] > -1} {
            lappend vpnIdGroupHdl $child
        } elseif { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        } elseif { [string first "router" [string tolower $child]] > -1} { 
            lappend emulatedDeviceHdl $child
        } elseif { [string first "ipv4group" [string tolower $child]] > -1} {
            lappend ipv4GroupHdl $child
        } elseif { [string first "vpnsiteinforfc2547" [string tolower $child]] > -1} {
            lappend vpnSiteInfoHdl $child
        } elseif { [string first "host" [string tolower $child]] > -1} {
            lappend hostHdl $child
        }
    }
    
    foreach device $emulatedDeviceHdl {
        if {[catch {set deviceName [::sth::sthCore::invoke stc::get $device -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $device. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { [string first "CE Router" $deviceName] > -1 } {
            lappend ceRouter $device
        } elseif { [string first "PE Router" $deviceName] > -1 } {
            lappend peRouter $device
        } elseif { [string first "PE VRF Router" $deviceName] > -1 } {
            lappend peVrfRouter $device
        } elseif { [string first "P Router" $deviceName] > -1 } {
            lappend pRouter $device
        } elseif { [string first "RR Router" $deviceName] > -1 } {
            lappend rrRouter $device
         }
    }
    
    set i 0
    while { 1 } {
        if { ![info exists $_hltNameSpace\MvpnHdlArr$i]} {
            global array set $_hltNameSpace\MvpnHdlArr$i {}
            array set $_hltNameSpace\MvpnHdlArr$i [list \
                VpnIdGroup $vpnIdGroupHdl \
                Ipv4Group  $ipv4GroupHdl \
                VpnSiteInfoRfc2547 $vpnSiteInfoHdl \
                Host $hostHdl \
                CeRouter $ceRouter \
                PeRouter $peRouter \
                PeVrfRouter $peVrfRouter \
                PRouter $pRouter \
                RRRouter $rrRouter \
                StreamBlock $streamList \
            ]
            #puts [array get $_hltNameSpace\MvpnHdlArr$i]
            set mvpnHandle $_hltNameSpace\MvpnHdlArr$i
            ::sth::sthCore::log DEBUG "Mvpn handle : $mvpnHandle. [array get $_hltNameSpace\MvpnHdlArr$i]"
            break
        } else {
            incr i
        }
    }
    
    #subscribe results for all protocols
    if { !$::sth::Mvpn::createResultQuery} {
        set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
        set protocolList {bgp ospfv2 isis rip ldp rsvp pim bfd}
        foreach protocol $protocolList {
            if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId $protocol\RouterConfig -ResultClassId $protocol\RouterResults]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error create the $protocol ResultQuery"
            set cmdState $FAILURE
            return $returnKeyedList        
            }
        }
        if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId bfdipv4sessionresults]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error create the bfdipv4sessionresults ResultQuery"
        set cmdState $FAILURE
        return $returnKeyedList        
        }
        ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
        
    }
    
    keylset returnKeyedList handle $mvpnHandle
    keylset returnKeyedList traffic_handle $streamList
    
    if { [catch {::sth::sthCore::invoke stc::delete $mvpnGenParamsHdl} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured while deleting $mvpnGenParamsHdl. ErrMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
            
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_control"    
    set _hltCmdName "emulation_mvpn_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { ![info exists $mvpnHandle]} {
    	::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set objectType "StreamBlock"
    if {[info exist $mvpnHandle\($objectType)]} {
	foreach objectHandle [set $mvpnHandle\($objectType)] {
	    if { [catch {::sth::sthCore::invoke stc::delete $objectHandle} errMsg]} {
		::sth::sthCore::processError returnKeyedList "Error occured while deleting $objectHandle. ErrMsg: $errMsg." {}
		set cmdState $FAILURE
		return $returnKeyedList
	    }
	}
	set $mvpnHandle\($objectType) ""
    }
    
    foreach objectType [array names $mvpnHandle] {
        foreach objectHandle [set $mvpnHandle\($objectType)] {
            if { [catch {::sth::sthCore::invoke stc::delete $objectHandle} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while deleting $objectHandle. ErrMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    array unset $mvpnHandle
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_customer_port_config_add { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_customer_port_config"    
    set _hltCmdName "emulation_mvpn_customer_port_config_add"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set custPortParamsHdlList [::sth::sthCore::invoke stc::get $mvpnGenParamsHdl -Children-MvpnGenCustPortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenCorePortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set mvpnGenCustPortHdl ""
    foreach custPortParamsHdl $custPortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $custPortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $custPortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set mvpnGenCustPortHdl $custPortParamsHdl
        }
    }
    
    if { $mvpnGenCustPortHdl == ""} {
        if {[catch {set mvpnGenCustPortHdl [::sth::sthCore::invoke stc::create "MvpnGenCustPortParams" -under $mvpnGenParamsHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenCustPortParams under $mvpnGenParamsHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $mvpnGenCustPortHdl "-AffiliationPort-Targets $portHandle"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to config -AffiliationPort-Targets to $mvpnGenCustPortHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    set objList "MvpnGenCustPortParams"
    array set cmdArray {
        MvpnGenCustPortParams ""
    }
    array set hdlArray {
        MvpnGenCustPortParams ""
    }
    set hdlArray(MvpnGenCustPortParams) $mvpnGenCustPortHdl
    
    #Configure the created MvpnGenCorePortParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenCustPortParams: $returnKeyedList"
        #Delete the MvpnGenCustPortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenCustPortHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenCustPortParams:$mvpnGenCustPortHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_customer_port_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_customer_port_config"    
    set _hltCmdName "emulation_mvpn_customer_port_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    
    if { $mvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: No Mvpn has been configured. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {set custPortParamsHdlList [::sth::sthCore::invoke stc::get $mvpnGenParamsHdl -Children-MvpnGenCustPortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenCustPortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set mvpnGenCustPortHdl ""
    foreach custPortParamsHdl $custPortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $custPortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $custPortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set mvpnGenCustPortHdl $custPortParamsHdl
        }
    }
    
    if { $mvpnGenCustPortHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: Current Mvpn configuration doesn't include certain port:$portHandle. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenCustPortHdl} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenCustPortParams:$mvpnGenCustPortHdl Msg: $eMsg"
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_vrf_config_generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_vrf_config"    
    set _hltCmdName "emulation_mvpn_vrf_config_generic"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    set objList "MvpnGenParams"
    array set cmdArray {
        MvpnGenParams ""
    }
    array set hdlArray {
        MvpnGenParams ""
    }
    
    set hdlArray(MvpnGenParams) $mvpnGenParamsHdl
    
    #Configure the created MvpnGenParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }
    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenParams: $returnKeyedList"
        #Delete the MvpnGenParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenParamsHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenParams:$mvpnGenParamsHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_vrf_route_config_generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_vrf_route_config"    
    set _hltCmdName "emulation_mvpn_vrf_route_config_generic"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    set objList "MvpnGenParams"
    array set cmdArray {
        MvpnGenParams ""
    }
    array set hdlArray {
        MvpnGenParams ""
    }
    
    set hdlArray(MvpnGenParams) $mvpnGenParamsHdl
    
    #Configure the created MvpnGenParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
        #if processing function is processConfigCmd, append the attribute/value pair to 
	#corresponding array element for processing later        
        if {[string equal $switchProcFunc "processConfigCmd"]} {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            if { $stcAttrName == "VpnCustRouteStep"} {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(customer_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif { $stcAttrName == "VpnCoreRouteStep" } {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(provider_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }
    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenParams: $returnKeyedList"
        #Delete the MvpnGenParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenParamsHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenParams:$mvpnGenParamsHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_vrf_traffic_config_generic { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_vrf_traffic_config"    
    set _hltCmdName "emulation_mvpn_vrf_traffic_config_generic"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
    }
    if { $mvpnGenParamsHdl == ""} {
        if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::create "MvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create MvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    set objList "MvpnGenParams"
    array set cmdArray {
        MvpnGenParams ""
    }
    array set hdlArray {
        MvpnGenParams ""
    }
    
    set hdlArray(MvpnGenParams) $mvpnGenParamsHdl
    
    #Configure the created MvpnGenParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }
    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring MvpnGenParams: $returnKeyedList"
        #Delete the MvpnGenParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $mvpnGenParamsHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created MvpnGenParams:$mvpnGenParamsHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_control_validate { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_control"    
    set _hltCmdName "emulation_mvpn_control_validate"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

     
	if { [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
		if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
			::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
			set cmdState $FAILURE
			return $returnKeyedList
		} else {
			::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$mvpnGenParamsHdl"
		}
	} else {
		if {[catch {set mvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-MvpnGenParams]} errMsg]} {
			::sth::sthCore::processError returnKeyedList "Unable to fetch MvpnGenParams Handle. Error: $errMsg" {} 
			set cmdState $FAILURE
			return $returnKeyedList
		} else {
			::sth::sthCore::log debug "MvpnGenParams handle to be configured:$mvpnGenParamsHdl"
	    }
	}
    if { $mvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Error: No M-VPN has been configured." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set pre_streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set pre_streamList [concat $pre_streamList $stream]
        }
    }
    if {[catch {set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform VpnGenConfigExpand -clearportconfig no -genparams $mvpnGenParamsHdl}]} {
	::sth::sthCore::processError returnKeyedList "Unable to expand M-VPN configuration." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set streamList [concat $streamList $stream]
        }
    }
    if {[catch {set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    #get new created devices' handles within mvpn 
    foreach stream $pre_streamList {
        set x [lsearch $streamList $stream]
        if { $x > -1 } {
            set streamList [lreplace $streamList $x $x]
        }
    }
    
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    
    set vpnIdGroupHdl ""
    set emulatedDeviceHdl ""
    set ipv4GroupHdl ""
    set vpnSiteInfoHdl ""
    set hostHdl ""
    set ceRouter ""
    set peRouter ""
    set peVrfRouter ""
    set pRouter ""
    foreach child $childrenList {
        if { [string first "vpnidgroup" [string tolower $child]] > -1} {
            lappend vpnIdGroupHdl $child
        } elseif { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        } elseif { [string first "router" [string tolower $child]] > -1} { 
            lappend emulatedDeviceHdl $child
        } elseif { [string first "ipv4group" [string tolower $child]] > -1} {
            lappend ipv4GroupHdl $child
        } elseif { [string first "vpnsiteinforfc2547" [string tolower $child]] > -1} {
            lappend vpnSiteInfoHdl $child
        } elseif { [string first "host" [string tolower $child]] > -1} {
            lappend hostHdl $child
        }
    }
    
    foreach device $emulatedDeviceHdl {
        if {[catch {set deviceName [::sth::sthCore::invoke stc::get $device -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $device. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { [string first "CE Router" $deviceName] > -1 } {
            lappend ceRouter $device
        } elseif { [string first "PE Router" $deviceName] > -1 } {
            lappend peRouter $device
        } elseif { [string first "PE VRF Router" $deviceName] > -1 } {
            lappend peVrfRouter $device
        } elseif { [string first "P Router" $deviceName] > -1 } {
            lappend pRouter $device
        }
    }
    
    set i 0
    while { 1 } {
        if { ![info exists $_hltNameSpace\MvpnHdlArr$i]} {
            global array set $_hltNameSpace\MvpnHdlArr$i {}
            array set $_hltNameSpace\MvpnHdlArr$i [list \
                VpnIdGroup $vpnIdGroupHdl \
                Ipv4Group  $ipv4GroupHdl \
                VpnSiteInfoRfc2547 $vpnSiteInfoHdl \
                Host $hostHdl \
                CeRouter $ceRouter \
                PeRouter $peRouter \
                PeVrfRouter $peVrfRouter \
                PRouter $pRouter \
                StreamBlock $streamList \
            ]
            #puts [array get $_hltNameSpace\MvpnHdlArr$i]
            set mvpnHandle $_hltNameSpace\MvpnHdlArr$i
            ::sth::sthCore::log DEBUG "Mvpn handle : $mvpnHandle. [array get $_hltNameSpace\MvpnHdlArr$i]"
            break
        } else {
            incr i
        }
    }
    
    #subscribe results for all protocols
    if { !$::sth::Mvpn::createResultQuery} {
        set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
        set protocolList {bgp ospfv2 isis rip ldp rsvp pim bfd}
        foreach protocol $protocolList {
            if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId $protocol\RouterConfig -ResultClassId $protocol\RouterResults]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error create the $protocol ResultQuery"
            set cmdState $FAILURE
            return $returnKeyedList        
            }
        }
        if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId bfdipv4sessionresults]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error create the bfdipv4sessionresults ResultQuery"
        set cmdState $FAILURE
        return $returnKeyedList        
        }
        ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
        
    }
    
    keylset returnKeyedList handle $mvpnHandle
    keylset returnKeyedList traffic_handle $streamList
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_control_invalidate { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_control"    
    set _hltCmdName "emulation_mvpn_control_invalidate"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { ![info exists $mvpnHandle]} {
    	::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    foreach objectType [array names $mvpnHandle] {
        foreach objectHandle [set $mvpnHandle\($objectType)] {
            if { [catch {::sth::sthCore::invoke stc::delete $objectHandle} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while deleting $objectHandle. ErrMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    array unset $mvpnHandle
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_control_start { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_control"    
    set _hltCmdName "emulation_mvpn_control_start"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { ![info exists $mvpnHandle]} {
    	::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set deviceList ""
    
    set objectList "Host CeRouter PeRouter PeVrfRouter PRouter RRRouter"
    
    foreach objectType $objectList {
        append deviceList " " [set $mvpnHandle\($objectType)] 
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $deviceList} errMsg]} {
    	::sth::sthCore::processError returnKeyedList "Unable to start devices within mvpn configuration. ErrMsg: $errMsg." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_control"    
    set _hltCmdName "emulation_mvpn_control_stop"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { ![info exists $mvpnHandle]} {
    	::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set deviceList ""
    
    set objectList "Host CeRouter PeRouter PeVrfRouter PRouter RRRouter"
    
    foreach objectType $objectList {
        append deviceList " " [set $mvpnHandle\($objectType)] 
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $deviceList} errMsg]} {
    	::sth::sthCore::processError returnKeyedList "Unable to stop devices within mvpn configuration. ErrMsg: $errMsg." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_bgp { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_bgp"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    
     
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Bgp" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
    	    ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	    set cmdState $FAILURE
	        return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Bgp" $mvpnHandle returnKeyedList cmdState
    }
    return $returnKeyedList

    #set deviceList ""
    #set objectList "Host CeRouter PeRouter PeVrfRouter PRouter"
    #foreach objectType $objectList {
    #    foreach device [set $mvpnHandle\($objectType)] {
    #        if { [catch {set bgpConfigHdl [::sth::sthCore::invoke stc::get $device -Children-BgpRouterConfig ]} errMsg]} {
    #            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-BgpRouterConfig from $device." {}
    #            set cmdState $FAILURE
    #            return $returnKeyedList
    #        }
    #        
    #        if { $bgpConfigHdl == ""} {
    #            break
    #        }
    #        
    #        if { [catch {set bgpResultHdl [::sth::sthCore::invoke stc::get $bgpConfigHdl -Children-BgpRouterResults]} errMsg]} {
    #            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-BgpRouterResults from $bgpConfigHdl." {}
    #            set cmdState $FAILURE
    #            return $returnKeyedList
    #        }
    #        
    #        if { $bgpResultHdl == ""} {
    #            ::sth::sthCore::processError returnKeyedList "BGP Router results have not been subscribed correctly for $device." {}
    #            set cmdState $FAILURE
    #            return $returnKeyedList
    #        }
    #        
    #        if { [catch {set affPortHdl [::sth::sthCore::invoke stc::get $device -AffiliationPort-Targets]} errMsg]} {
    #            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $device." {}
    #            set cmdState $FAILURE
    #            return $returnKeyedList
    #        }
    #        if { [catch {set buff [keylget returnKeyedList port.$affPortHdl.device]}]} {
    #            keylset returnKeyedList port.$affPortHdl.device $device
    #        } elseif {
    #            keylset returnKeyedList port.$affPortHdl.device [concat $buff " " $device]
    #        }
    #        
    #        array set resultHdlArr [list
    #            BgpRouterConfig $bgpConfigHdl
    #            BgpRouterResults $bgpResultHdl
    #        ]
    #        foreach returnkeyName [array names $_hltNameSpace$_hltCmdName\_mode] {
    #            set supported [set $_hltNameSpace$_hltCmdName\_supported($returnKeyName)]
    #            if { $supported == "true"} {
    #                set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcobj]
    #                set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_hltCmdName $returnKeyName stcattr]
    #                
    #                if { [catch {set result [::sth::sthCore::invoke stc::get $resultHdlArr($stcObjName) -$stcAttrName]} errMsg]} {
    #                    ::sth::sthCore::processError returnKeyedList "Unable to fetch -$stcAttrName from $resultHdlArr($stcObjName)." {}
    #                    set cmdState $FAILURE
    #                    return $returnKeyedList
    #                }
    #                
    #                keylset returnKeyedList [regsub {yyy} [regsub {xxx} $returnkeyName $affPortHdl] $device] $result
    #            }
    #        }
    #    }
    #}
    #
    #
}

proc ::sth::Mvpn::emulation_mvpn_info_ospfv2 { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_ospfv2"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Ospfv2" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Ospfv2" $mvpnHandle returnKeyedList cmdState
    }
 
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_isis { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_isis"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Isis" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Isis" $mvpnHandle returnKeyedList cmdState
    }
    
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_rip { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_rip"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Rip" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
    	::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
    	set cmdState $FAILURE
        return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Rip" $mvpnHandle returnKeyedList cmdState
    }
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_ldp { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_ldp"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Ldp" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Ldp" $mvpnHandle returnKeyedList cmdState
    }
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_rsvp { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_rsvp"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Rsvp" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Rsvp" $mvpnHandle returnKeyedList cmdState
    }
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_pim { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_pim"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Pim" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Pim" $mvpnHandle returnKeyedList cmdState
    } 
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_bfd { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_bfd"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $_hltCmdName "Bfd" $mvpnHandle returnKeyedList cmdState
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        ::sth::Mvpn::get_return_key_results $_hltNameSpace $_hltCmdName "Bfd" $mvpnHandle returnKeyedList cmdState
    } 
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_mvpn_info_aggregate { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_mvpn_info"    
    set _hltCmdName "emulation_mvpn_info_aggregate"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set mvpnHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    
    if { [::info exists $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] && [string equal "nextgen" [set $_hltSpaceCmdName\_user_input_args_array(mvpn_type)] ] } {
        set protocolList {Bgp Ospfv2 Isis Rip Ldp Rsvp Pim Bfd}
        foreach protocol $protocolList {
            set subCmdName $_OrigHltCmdName\_[string tolower $protocol]
            ::sth::Mvpn::get_return_key_results_nextgen $_hltNameSpace $subCmdName $protocol $mvpnHandle returnKeyedList cmdState
        }
    } else {
        if { ![info exists $mvpnHandle]} {
            ::sth::sthCore::processError returnKeyedList "input mvpn handle is not valid." {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    
        set protocolList {Bgp Ospfv2 Isis Rip Ldp Rsvp Pim Bfd}
    
        foreach protocol $protocolList {
            set subCmdName $_OrigHltCmdName\_[string tolower $protocol]
            ::sth::Mvpn::get_return_key_results $_hltNameSpace $subCmdName $protocol $mvpnHandle returnKeyedList cmdState
        }
    }
    
    return $returnKeyedList
}

proc ::sth::Mvpn::get_return_key_results {_hltNameSpace subCmdName protocol mvpnHandle returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _hltSpaceCmdName ${_hltNameSpace}$subCmdName
    set deviceList ""
    set objectList "CeRouter PeRouter PeVrfRouter PRouter RRRouter"
    foreach objectType $objectList {
        foreach device [set $mvpnHandle\($objectType)] {
            if { [catch {set protocolConfigHdl [::sth::sthCore::invoke stc::get $device -Children-$protocol\RouterConfig ]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocol\RouterConfig from $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $protocolConfigHdl == ""} {
                continue
            }
            
            if { [catch {set protocolResultHdl [::sth::sthCore::invoke stc::get $protocolConfigHdl -Children-$protocol\RouterResults]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocol\RouterResults from $protocolConfigHdl." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $protocolResultHdl == ""} {
                ::sth::sthCore::processError returnKeyedList "$protocol Router results have not been subscribed correctly for $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { [catch {set affPortHdl [::sth::sthCore::invoke stc::get $device -AffiliationPort-Targets]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if { ![catch {set buff [keylget returnKeyedList port.$affPortHdl.devices]} errMsg]} {
                if { [lsearch $buff $device] == -1} {
                    keylset returnKeyedList port.$affPortHdl.devices [concat $buff $device]
                }
            } else {
                keylset returnKeyedList port.$affPortHdl.devices $device
            }
            
            array set resultHdlArr [list \
                $protocol\RouterConfig $protocolConfigHdl \
                $protocol\RouterResults $protocolResultHdl ]
            
            #puts [array names $_hltSpaceCmdName\_mode]
            foreach returnKeyName [array names $_hltSpaceCmdName\_mode] {
                set supported [set $_hltSpaceCmdName\_supported($returnKeyName)]
                if { $supported == "true"} {
                    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $subCmdName $returnKeyName stcobj]
                    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $subCmdName $returnKeyName stcattr]
                    
                    if { [catch {set result [::sth::sthCore::invoke stc::get $resultHdlArr($stcObjName) -$stcAttrName]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Unable to fetch -$stcAttrName from $resultHdlArr($stcObjName)." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    keylset returnKeyedList [regsub {yyy} [regsub {xxx} $returnKeyName $affPortHdl] $device] $result
                }
            }
        }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::get_return_key_results_nextgen {_hltNameSpace subCmdName protocol mvpnHandle returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState
    
    set _hltSpaceCmdName ${_hltNameSpace}$subCmdName
    set deviceList ""
   
        foreach device $mvpnHandle {
            if { [catch {set protocolConfigHdl [::sth::sthCore::invoke stc::get $device -Children-$protocol\RouterConfig ]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocol\RouterConfig from $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $protocolConfigHdl == ""} {
                continue
            }
            
            if { [catch {set protocolResultHdl [::sth::sthCore::invoke stc::get $protocolConfigHdl -Children-$protocol\RouterResults]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocol\RouterResults from $protocolConfigHdl." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { $protocolResultHdl == ""} {
                ::sth::sthCore::processError returnKeyedList "$protocol Router results have not been subscribed correctly for $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            
            if { [catch {set affPortHdl [::sth::sthCore::invoke stc::get $device -AffiliationPort-Targets]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $device." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
            if { ![catch {set buff [keylget returnKeyedList port.$affPortHdl.devices]} errMsg]} {
                if { [lsearch $buff $device] == -1} {
                    keylset returnKeyedList port.$affPortHdl.devices [concat $buff $device]
                }
            } else {
                keylset returnKeyedList port.$affPortHdl.devices $device
            }
            
            array set resultHdlArr [list \
                $protocol\RouterConfig $protocolConfigHdl \
                $protocol\RouterResults $protocolResultHdl ]
            
            foreach returnKeyName [array names $_hltSpaceCmdName\_mode] {
                set supported [set $_hltSpaceCmdName\_supported($returnKeyName)]
                if { $supported == "true"} {
                    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $subCmdName $returnKeyName stcobj]
                    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $subCmdName $returnKeyName stcattr]
                    
                    if { [catch {set result [::sth::sthCore::invoke stc::get $resultHdlArr($stcObjName) -$stcAttrName]} errMsg]} {
                        ::sth::sthCore::processError returnKeyedList "Unable to fetch -$stcAttrName from $resultHdlArr($stcObjName)." {}
                        set cmdState $FAILURE
                        return $returnKeyedList
                    }
                    
                    keylset returnKeyedList [regsub {yyy} [regsub {xxx} $returnKeyName $affPortHdl] $device] $result
                }
            }
        }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}



proc ::sth::Mvpn::ipv4_to_binary {ipVal} {
    set ipList [split $ipVal "."]
    set binIp ""
    foreach v $ipList {
        foreach c [split [format "%02x" $v] ""] {
            switch $c {
                0 { append binIp "0000"}
                1 { append binIp "0001"}
                2 { append binIp "0010"}
                3 { append binIp "0011"}
                4 { append binIp "0100"}
                5 { append binIp "0101"}
                6 { append binIp "0110"}
                7 { append binIp "0111"}
                8 { append binIp "1000"}
                9 { append binIp "1001"}
                a { append binIp "1010"}
                b { append binIp "1011"}
                c { append binIp "1100"}
                d { append binIp "1101"}
                e { append binIp "1110"}
                f { append binIp "1111"}
            }
        }
    }
    
    return $binIp
}

proc ::sth::Mvpn::ipv4_step_to_dec_step {ipVal prefix} {
    set bin_ip [::sth::Mvpn::ipv4_to_binary $ipVal]
    set step 0
    for {set i 1} {$i <= $prefix} {incr i} {
        set v [expr [string index $bin_ip [expr $i - 1]] * [expr { pow(2, [expr $prefix - $i]) }] ]
        set step [expr $step + $v]
    }
    return [format "%.0f" $step]
}

###############################################################
#For nextgen mvpn provider ADD and DELETE
###############################################################
proc ::sth::Mvpn::emulation_nextgen_mvpn_provider_port_config_add { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_provider_port_config"    
    set _hltCmdName "emulation_nextgen_mvpn_provider_port_config_add"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
   
    #Check if te port_handle is valid
    if { ![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }
	

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$nextgenmvpnGenParamsHdl"
    }
    if { $nextgenmvpnGenParamsHdl == ""} {
        if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::create "VpnNextGenMvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create VpnNextGenMvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set corePortParamsHdlList [::sth::sthCore::invoke stc::get $nextgenmvpnGenParamsHdl -Children-VpnNextGenMvpnGenCorePortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenCorePortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set nextgenmvpnGenCorePortHdl ""
    foreach corePortParamsHdl $corePortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $corePortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $corePortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set nextgenmvpnGenCorePortHdl $corePortParamsHdl
        }
    }
    
    if { $nextgenmvpnGenCorePortHdl == ""} {
        if {[catch {set nextgenmvpnGenCorePortHdl [::sth::sthCore::invoke stc::create "VpnNextGenMvpnGenCorePortParams" -under $nextgenmvpnGenParamsHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create VpnNextGenMvpnGenCorePortParams under $nextgenmvpnGenParamsHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $nextgenmvpnGenCorePortHdl "-AffiliationPort-Targets $portHandle"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to config -AffiliationPort-Targets to $nextgenmvpnGenCorePortHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    #To get RtgTestGenIpv4PortParams and RtgTestGenIpv6PortParams handles (automatic children of VpnNextGenMvpnGenCorePortParams)
	#Used to get DutIpv4Addr DutIpv4AddrStep Ipv4PrefixLength DutIpv6Addr DutIpv6AddrStep Ipv6PrefixLength 
	set RtgTestGenIpv4PortParamsHandle [stc::get $nextgenmvpnGenCorePortHdl -children-RtgTestGenIpv4PortParams]
	set RtgTestGenIpv6PortParamsHandle [stc::get $nextgenmvpnGenCorePortHdl -children-RtgTestGenIpv6PortParams]
	
    set objList "VpnNextGenMvpnGenCorePortParams RtgTestGenIpv4PortParams RtgTestGenIpv6PortParams"
    array set cmdArray {
        VpnNextGenMvpnGenCorePortParams ""
		RtgTestGenIpv6PortParams ""
		RtgTestGenIpv4PortParams ""
    }
    array set hdlArray {
        VpnNextGenMvpnGenCorePortParams ""
		RtgTestGenIpv6PortParams ""
		RtgTestGenIpv4PortParams ""
    }
    set hdlArray(VpnNextGenMvpnGenCorePortParams) $nextgenmvpnGenCorePortHdl
	set hdlArray(RtgTestGenIpv4PortParams) $RtgTestGenIpv4PortParamsHandle
	set hdlArray(RtgTestGenIpv6PortParams) $RtgTestGenIpv6PortParamsHandle
    
    #Configure the created VpnNextGenMvpnGenCorePortParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring VpnNextGenMvpnGenCorePortParams: $returnKeyedList"
    #Delete the VpnNextGenMvpnGenCorePortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $nextgenmvpnGenCorePortHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created VpnNextGenMvpnGenCorePortParams:$mvpnGenCorePortHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_nextgen_mvpn_provider_port_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_provider_port_config"    
    set _hltCmdName "emulation_nextgen_mvpn_provider_port_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists $_hltSpaceCmdName\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set $_hltSpaceCmdName\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$nextgenmvpnGenParamsHdl"
    }
    
    if { $nextgenmvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: No Mvpn has been configured. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {set corePortParamsHdlList [::sth::sthCore::invoke stc::get $nextgenmvpnGenParamsHdl -Children-VpnNextGenMvpnGenCorePortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch nextgenMvpnGenCorePortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set nextgenmvpnGenCorePortHdl ""
    foreach corePortParamsHdl $corePortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $corePortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $corePortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set nextgenmvpnGenCorePortHdl $corePortParamsHdl
        }
    }
    
    if { $nextgenmvpnGenCorePortHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: Current Mvpn configuration doesn't include certain port:$portHandle. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $nextgenmvpnGenCorePortHdl} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Error deleting previously created VpnNextGenMvpnGenCorePortParams :$nextgenmvpnGenCorePortHdl Msg: $eMsg"
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
###############################################################
#For nextgen mvpn customer ADD and DELETE
###############################################################
proc ::sth::Mvpn::emulation_nextgen_mvpn_customer_port_config_add { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_customer_port_config"    
    set _hltCmdName "emulation_nextgen_mvpn_customer_port_config_add"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$nextgenmvpnGenParamsHdl"
    }
    if { $nextgenmvpnGenParamsHdl == ""} {
        if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::create "VpnNextGenMvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create VpnNextGenMvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    
    if {[catch {set custPortParamsHdlList [::sth::sthCore::invoke stc::get $nextgenmvpnGenParamsHdl -Children-VpnNextGenMvpnGenCustPortParams ]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenCustPortParams  Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set nextgenmvpnGenCustPortHdl ""
    foreach custPortParamsHdl $custPortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $custPortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $custPortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set nextgenmvpnGenCustPortHdl $custPortParamsHdl
        }
    }
    
    if { $nextgenmvpnGenCustPortHdl == ""} {
        if {[catch {set nextgenmvpnGenCustPortHdl [::sth::sthCore::invoke stc::create "VpnNextGenMvpnGenCustPortParams" -under $nextgenmvpnGenParamsHdl]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create VpnNextGenMvpnGenCustPortParams  under $nextgenmvpnGenParamsHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::config $nextgenmvpnGenCustPortHdl "-AffiliationPort-Targets $portHandle"} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to config -AffiliationPort-Targets to $nextgenmvpnGenCustPortHdl. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }
    #To get RtgTestGenIpv4PortParams and RtgTestGenIpv6PortParams handles (automatic children of VpnNextGenMvpnGenCustPortParams)
	#Used to get DutIpv4Addr DutIpv4AddrStep Ipv4PrefixLength DutIpv6Addr DutIpv6AddrStep Ipv6PrefixLength 
	set RtgTestGenIpv4PortParamsHandle [stc::get $nextgenmvpnGenCustPortHdl -children-RtgTestGenIpv4PortParams]
	set RtgTestGenIpv6PortParamsHandle [stc::get $nextgenmvpnGenCustPortHdl -children-RtgTestGenIpv6PortParams]
	 
    set objList "VpnNextGenMvpnGenCustPortParams RtgTestGenIpv4PortParams RtgTestGenIpv6PortParams"

    array set cmdArray {
        VpnNextGenMvpnGenCustPortParams ""
		RtgTestGenIpv6PortParams ""
		RtgTestGenIpv4PortParams ""
    }
    array set hdlArray {
        VpnNextGenMvpnGenCustPortParams ""
		RtgTestGenIpv6PortParams ""
		RtgTestGenIpv4PortParams ""
    }
    set hdlArray(VpnNextGenMvpnGenCustPortParams) $nextgenmvpnGenCustPortHdl
	set hdlArray(RtgTestGenIpv4PortParams) $RtgTestGenIpv4PortParamsHandle
	set hdlArray(RtgTestGenIpv6PortParams) $RtgTestGenIpv6PortParamsHandle
    
    #Configure the created VpnNextGenMvpnGenCustPortParams with user input (options)
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }    
    if {[::info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring VpnNextGenMvpnGenCustPortParams: $returnKeyedList"
        #Delete the VpnNextGenMvpnGenCustPortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $nextgenmvpnGenCustPortHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created VpnNextGenMvpnGenCustPortParams:$nextgenmvpnGenCustPortHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}


proc ::sth::Mvpn::emulation_nextgen_mvpn_customer_port_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_customer_port_config"    
    set _hltCmdName "emulation_nextgen_mvpn_customer_port_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    #Check if te port_handle is valid
    if {![::info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]} {
    	::sth::sthCore::processError returnKeyedList "port_handle needed when adding port to mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	set portHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(port_handle)]
    }

    if {![::sth::sthCore::IsPortValid $portHandle errMsg]} {
	::sth::sthCore::processError returnKeyedList  "Invalid Value of port_handle. $errMsg." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {set nextgenmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$nextgenmvpnGenParamsHdl"
    }
    
    if { $nextgenmvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: No Mvpn has been configured. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {set custPortParamsHdlList [::sth::sthCore::invoke stc::get $nextgenmvpnGenParamsHdl -Children-VpnNextGenMvpnGenCustPortParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenCustPortParams Handle. Error: $errMsg" {}
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set nextgenmvpnGenCustPortHdl ""
    foreach custPortParamsHdl $custPortParamsHdlList {
        if {[catch {set port_handle [::sth::sthCore::invoke stc::get $custPortParamsHdl -AffiliationPort-Targets]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -AffiliationPort-Targets from $custPortParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $portHandle == $port_handle} {
            set nextgenmvpnGenCustPortHdl $custPortParamsHdl
        }
    }
    
    if { $nextgenmvpnGenCustPortHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Warning: Current Mvpn configuration doesn't include certain port:$portHandle. " {} 
	set cmdState $SUCCESS
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::delete $nextgenmvpnGenCustPortHdl} eMsg ]} {
        ::sth::sthCore::processError returnKeyedList "Error deleting previously created VpnNextGenMvpnGenCustPortParams:$nextgenmvpnGenCustPortHdl Msg: $eMsg"
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}
###############################################################
#For nextgen mvpn config CREATE and DELETE
###############################################################
proc ::sth::Mvpn::emulation_nextgen_mvpn_config_create { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_config"    
    set _hltCmdName "emulation_nextgen_mvpn_config_create"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"

    if {[catch {set ngmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$ngmvpnGenParamsHdl"
    }
    if { $ngmvpnGenParamsHdl == ""} {
        if {[catch {set ngmvpnGenParamsHdl [::sth::sthCore::invoke stc::create "VpnNextGenMvpnGenParams" -under $::sth::GBLHNDMAP(project)]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList  "Unable to create VpnNextGenMvpnGenParams Handle. Error: $errMsg"  {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
    }

    set objList "VpnNextGenMvpnGenParams VpnMplsRsvpSessionParams VpnMplsLdpSessionParams VpnIgpOspfv2SessionParams VpnIgpIsisSessionParams Ospfv2AuthenticationParams IsisAuthenticationParams"
    array set cmdArray {
        VpnNextGenMvpnGenParams ""
        VpnMplsRsvpSessionParams ""
        VpnMplsLdpSessionParams ""
        VpnIgpOspfv2SessionParams ""
        VpnIgpIsisSessionParams ""
        Ospfv2AuthenticationParams ""
        IsisAuthenticationParams ""
    }
    array set hdlArray {
        VpnNextGenMvpnGenParams ""
        VpnMplsRsvpSessionParams ""
        VpnMplsLdpSessionParams ""
        VpnIgpOspfv2SessionParams ""
        VpnIgpIsisSessionParams ""
        Ospfv2AuthenticationParams ""
        IsisAuthenticationParams ""
    }
    
    set hdlArray(VpnNextGenMvpnGenParams) $ngmvpnGenParamsHdl
    
    set protocolList {VpnMplsRsvpSessionParams VpnMplsLdpSessionParams VpnIgpOspfv2SessionParams VpnIgpIsisSessionParams }
    
    foreach protocolSession $protocolList {
        if {[catch {set hdlArray($protocolSession) [::sth::sthCore::invoke stc::get $ngmvpnGenParamsHdl -Children-$protocolSession]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-$protocolSession from $ngmvpnGenParamsHdl. Error: $errMsg" {}
            set cmdState $FAILURE
            return $returnKeyedList
        }
        
        if { $hdlArray($protocolSession) == ""} {
            if {[catch {set hdlArray($protocolSession) [::sth::sthCore::invoke stc::create "$protocolSession" -under $ngmvpnGenParamsHdl]} errMsg]} {
                ::sth::sthCore::processError returnKeyedList  "Unable to create $protocolSession under $ngmvpnGenParamsHdl. Error: $errMsg"  {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
        }
    }
    
    if {[catch {set hdlArray(Ospfv2AuthenticationParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnIgpOspfv2SessionParams) -Children-Ospfv2AuthenticationParams ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Unable to fetch -Children-Ospfv2AuthenticationParams from $hdlArray(VpnIgpOspfv2SessionParams). Error: $errMsg"  {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    if {[catch {set hdlArray(IsisAuthenticationParams) [::sth::sthCore::invoke stc::get $hdlArray(VpnIgpIsisSessionParams) -Children-IsisAuthenticationParams ]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList  "Unable to fetch -Children-IsisAuthenticationParams from $hdlArray(VpnIgpIsisSessionParams). Error: $errMsg"  {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
    
    #Configure the created objects with user input (options)
    if {[info exists ${_hltSpaceCmdName}\_user_input_args_array(mpls_protocol)] &&
        [set ${_hltSpaceCmdName}\_user_input_args_array(mpls_protocol)] == "none"} {
        puts "INFO: switch -mpls_protocol has been set to \"none\". In this case, the unicast VPN traffic can not be sent, \
                switch -unicast_traffic_enable will be forced to 0 (false), and all unicast traffic relavant swtiches are unavailable."
        set ${_hltSpaceCmdName}\_user_input_args_array(unicast_traffic_enable) 0
    }
    
    ::sth::sthCore::log debug "Processing the switches in priority order for command:$_hltCmdName"
    #set userInputList [split $userInput]
    foreach {switchName switchValue} [array get ${_hltSpaceCmdName}\_user_input_args_array] {
        ::sth::sthCore::log debug "Trying to process the switch $switchName"
        
        if { $switchName == "optional_args" || $switchName == "mandatory_args" } {
            continue
        }
        set switchProcFunc [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName procfunc]
	
        #if processing function is processConfigCmd, append the attribute/value pair to 
	#corresponding array element for processing later        
        if {[string equal $switchProcFunc "processConfigCmd"]} {
	    set stcObjName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcobj]
	    set stcAttrName [::sth::sthCore::getswitchprop $_hltNameSpace $_OrigHltCmdName $switchName stcattr]
            if { $stcAttrName == "VpnCustRouteStep"} {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(customer_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif { $stcAttrName == "VpnCoreRouteStep" } {
                set switchValue [::sth::Mvpn::ipv4_step_to_dec_step $switchValue [set ${_hltSpaceCmdName}\_user_input_args_array(provider_route_prefix_length)]]
                append cmdArray($stcObjName) " -$stcAttrName $switchValue"
            } elseif {![catch {set attrValue [::sth::sthCore::getFwdmap $_hltNameSpace $_OrigHltCmdName $switchName $switchValue]} getStatus]} {
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
		::sth::sthCore::log error "$logStatus"
	    } else {
		::sth::sthCore::log debug "Successfully set switch/value pair:$cmdArray($objName) for object:$objName."
	    }
	}
    }
    
    if {[info exists cmdFailed]} {
	::sth::sthCore::log error "Error Occured configuring VpnNextGenMvpnGenParams: $returnKeyedList"
        #Delete the MvpnGenCustPortParams Object
	if {[catch {::sth::sthCore::invoke stc::delete $ngmvpnGenParamsHdl} eMsg ]} {
	    ::sth::sthCore::processError returnKeyedList "Error deleting previously created VpnNextGenMvpnGenParams:$ngmvpnGenParamsHdl Msg: $eMsg"
        }
	set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
        if {[catch {set ngmvpnGenParamsHdl [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-VpnNextGenMvpnGenParams]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch VpnNextGenMvpnGenParams Handle. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    } else {
	::sth::sthCore::log debug "VpnNextGenMvpnGenParams handle to be configured:$ngmvpnGenParamsHdl"
    }
    if { $ngmvpnGenParamsHdl == ""} {
	::sth::sthCore::processError returnKeyedList "Error: No M-VPN has been configured." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set pre_streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set pre_streamList [concat $pre_streamList $stream]
        }
    }
    if {[catch {set pre_childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::invoke stc::perform VpnGenConfigExpand -clearportconfig no -genparams $ngmvpnGenParamsHdl}]} {
	::sth::sthCore::processError returnKeyedList "Unable to expand M-VPN configuration." {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set streamList ""
    if {[catch {set portList [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children-Port]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-Port from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    foreach port $portList {
        if {[catch {set stream [::sth::sthCore::invoke stc::get $port -Children-StreamBlock]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Children-StreamBlock from $port. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { $stream != "" } {
            set streamList [concat $streamList $stream]
        }
    }
    if {[catch {set childrenStr [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -Children]} errMsg]} {
	::sth::sthCore::processError returnKeyedList "Unable to fetch -Children from project. Error: $errMsg" {} 
	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    #get new created devices' handles within mvpn 
    foreach stream $pre_streamList {
        set x [lsearch $streamList $stream]
        if { $x > -1 } {
            set streamList [lreplace $streamList $x $x]
        }
    }
    
    set childrenList [split $childrenStr]
    foreach child $pre_childrenStr {
        set x [lsearch $childrenList $child]
        if { $x > -1 } {
            set childrenList [lreplace $childrenList $x $x]
        }
    }
    
    set vpnIdGroupHdl ""
    set emulatedDeviceHdl ""
    set ipv4GroupHdl ""
    set ipv6GroupHdl ""
    set vpnSiteInfoHdl ""
    set hostHdl ""
    set ceRouterV4 ""
    set ceRouterV6 ""
    set peRouter ""
    set peVrfRouter ""
    set pRouter ""
    set rrRouter ""
    foreach child $childrenList {
        if { [string first "vpnidgroup" [string tolower $child]] > -1} {
            lappend vpnIdGroupHdl $child
        } elseif { [string first "emulateddevice" [string tolower $child]] > -1} {
            lappend emulatedDeviceHdl $child
        } elseif { [string first "router" [string tolower $child]] > -1} { 
            lappend emulatedDeviceHdl $child
        } elseif { [string first "ipv4group" [string tolower $child]] > -1} {
            lappend ipv4GroupHdl $child
        } elseif { [string first "ipv6group" [string tolower $child]] > -1} {
            lappend ipv6GroupHdl $child
        } elseif { [string first "vpnsiteinforfc2547" [string tolower $child]] > -1} {
            lappend vpnSiteInfoHdl $child
        } elseif { [string first "host" [string tolower $child]] > -1} {
            lappend hostHdl $child
        }
    }
    
    foreach device $emulatedDeviceHdl {
        if {[catch {set deviceName [::sth::sthCore::invoke stc::get $device -Name]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Unable to fetch -Name from $device. Error: $errMsg" {} 
            set cmdState $FAILURE
            return $returnKeyedList
        }
        if { [string first "CE IPv4 Router" $deviceName] > -1 } {
            lappend ceRouterV4 $device
        } elseif { [string first "CE IPv6 Router" $deviceName] > -1 } {
            lappend ceRouterV6 $device
        } elseif { [string first "PE Router" $deviceName] > -1 } {
            lappend peRouter $device
        } elseif { [string first "PE VRF Router" $deviceName] > -1 } {
            lappend peVrfRouter $device
        } elseif { [string first "P Router" $deviceName] > -1 } {
            lappend pRouter $device
        } elseif { [string first "RR Router" $deviceName] > -1 } {
            lappend rrRouter $device
         }
    }
   
    set HandleKey [list VpnIdGroup Ipv4Group Ipv6Group VpnSiteInfoRfc2547 Host CeRouterV4 CeRouterV6 PeRouter PeVrfRouter PRouter RRRouter StreamBlock]
    set HandleValue [list vpnIdGroupHdl ipv4GroupHdl ipv6GroupHdl vpnSiteInfoHdl hostHdl ceRouterV4 ceRouterV6 peRouter peVrfRouter pRouter rrRouter streamList]
    for {set handleIdx 0} {$handleIdx < [llength $HandleKey] } {incr handleIdx} {
        keylset returnKeyedList handle.[lindex $HandleKey $handleIdx ]  [set [lindex $HandleValue $handleIdx ]]
    }
    
    #subscribe results for all protocols
    if { !$::sth::Mvpn::createResultQuery} {
        set resultDataSet [::sth::sthCore::invoke stc::create "ResultDataSet" -under $::sth::GBLHNDMAP(project)]
        set protocolList {bgp ospfv2 isis rip ldp rsvp pim bfd}
        foreach protocol $protocolList {
            if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId $protocol\RouterConfig -ResultClassId $protocol\RouterResults]} errMsg]} {
            ::sth::sthCore::processError returnKeyedList "Error create the $protocol ResultQuery"
            set cmdState $FAILURE
            return $returnKeyedList        
            }
        }
        if {[ catch {::sth::sthCore::invoke stc::create "ResultQuery" -under $resultDataSet [list -ResultRootList $::sth::GBLHNDMAP(project) -ConfigClassId bfdrouterconfig -ResultClassId bfdipv4sessionresults]} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error create the bfdipv4sessionresults ResultQuery"
        set cmdState $FAILURE
        return $returnKeyedList        
        }
        ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $resultDataSet
        
    }
    
   
    keylset returnKeyedList traffic_handle $streamList
    
    if { [catch {::sth::sthCore::invoke stc::delete $ngmvpnGenParamsHdl} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error occured while deleting $ngmvpnGenParamsHdl. ErrMsg: $errMsg." {}
        set cmdState $FAILURE
        return $returnKeyedList
    }
            
    set cmdState $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_nextgen_mvpn_config_delete { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_config"    
    set _hltCmdName "emulation_nextgen_mvpn_config_delete"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set DelHandle [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    
    foreach objectHandle $DelHandle {
            if { [catch {::sth::sthCore::invoke stc::delete $objectHandle} errMsg]} {
                ::sth::sthCore::processError returnKeyedList "Error occured while deleting $objectHandle. ErrMsg: $errMsg." {}
                set cmdState $FAILURE
                return $returnKeyedList
            }
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_nextgen_mvpn_control_start { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_control"    
    set _hltCmdName "emulation_nextgen_mvpn_control_start"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set deviceList [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStart -DeviceList $deviceList} errMsg]} {
    	::sth::sthCore::processError returnKeyedList "Unable to start devices within mvpn configuration. ErrMsg: $errMsg." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}

proc ::sth::Mvpn::emulation_nextgen_mvpn_control_stop { userInput returnKeyedListVarName cmdStatusVarName } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _OrigHltCmdName "emulation_nextgen_mvpn_control"    
    set _hltCmdName "emulation_nextgen_mvpn_control_stop"
    set _hltNameSpace "::sth::Mvpn::"

    upvar 1 $returnKeyedListVarName returnKeyedList
    upvar 1 $cmdStatusVarName cmdState

    set _hltSpaceCmdName ${_hltNameSpace}${_OrigHltCmdName}
    set cmdState $SUCCESS
    ::sth::sthCore::log debug "Excuting Internal Sub command for: $_OrigHltCmdName $_hltCmdName $userInput"
    
    if { ![info exists ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]} {
    	::sth::sthCore::processError returnKeyedList "handle needed when invalidating mvpn configuration." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    set deviceList [set ${_hltNameSpace}${_OrigHltCmdName}\_user_input_args_array(handle)]
    if {[catch {::sth::sthCore::invoke stc::perform DeviceStop -DeviceList $deviceList} errMsg]} {
    	::sth::sthCore::processError returnKeyedList "Unable to stop devices within mvpn configuration. ErrMsg: $errMsg." {}
    	set cmdState $FAILURE
	return $returnKeyedList
    }
    
    set cmdState $SUCCESS
    return $returnKeyedList
}
