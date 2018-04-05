# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth:: {
}

proc ::sth::emulation_mvpn_provider_port_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_provider_port_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	array set UserArgs $args
        
    set _hltCmdName "emulation_mvpn_provider_port_config"
	if { [ info exists UserArgs(-mvpn_type) ] && ($UserArgs(-mvpn_type) == "nextgen") } {
	    set _hltCmdName "emulation_nextgen_mvpn_provider_port_config"
	}
	
    set _hltNameSpace "::sth::Mvpn::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(action)]
    
    #Executing the ::sth::emulation_mvpn_provider_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_provider_router_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	array set UserArgs $args
	  
    set _hltCmdName "emulation_mvpn_config"
	if { [ info exists UserArgs(-mvpn_type) ] && ($UserArgs(-mvpn_type) == "nextgen") } {
	    set _hltCmdName "emulation_nextgen_mvpn_config"
	}
    set _hltNameSpace "::sth::Mvpn::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    #Executing the ::sth::emulation_mvpn_provider_router_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying VPLS PE configuration: $msg"
        return $returnKeyedList 
    }
        
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_customer_port_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_customer_port_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
	array set UserArgs $args
        
    set _hltCmdName "emulation_mvpn_customer_port_config"
	if { [ info exists UserArgs(-mvpn_type) ] && ($UserArgs(-mvpn_type) == "nextgen") } {
	    set _hltCmdName "emulation_nextgen_mvpn_customer_port_config"
	}
      
    set _hltNameSpace "::sth::Mvpn::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(action)]
    
    #Executing the ::sth::emulation_mvpn_customer_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_vrf_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_vrf_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mvpn_vrf_config"
        set _hltNameSpace "::sth::Mvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    #Executing the ::sth::emulation_mvpn_vrf_config funcition
    set cmd "${_hltSpaceCmdName}\_generic {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_vrf_route_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_vrf_route_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mvpn_vrf_route_config"
        set _hltNameSpace "::sth::Mvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    #Executing the ::sth::emulation_mvpn_vrf_route_config funcition
    set cmd "${_hltSpaceCmdName}\_generic {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_vrf_traffic_config { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_vrf_traffic_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mvpn_vrf_traffic_config"
        set _hltNameSpace "::sth::Mvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    #Executing the ::sth::emulation_mvpn_vrf_traffic_config funcition
    set cmd "${_hltSpaceCmdName}\_generic {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}

proc ::sth::emulation_mvpn_control { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_control $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
      
    array set UserArgs $args   
        
    set _hltCmdName "emulation_mvpn_control"
    if { [ info exists UserArgs(-mvpn_type) ] && ($UserArgs(-mvpn_type) == "nextgen") } {
	    set _hltCmdName "emulation_nextgen_mvpn_control"
	}
    set _hltNameSpace "::sth::Mvpn::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(action)]
    
        #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying : $msg"
        return $returnKeyedList 
    }
    
    #Executing the ::sth::emulation_mvpn_control funcition
	set handleList [set ${_hltSpaceCmdName}\_user_input_args_array(handle)]
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
	foreach ::sth::Mvpn::emulation_mvpn_control_user_input_args_array(handle) $handleList {
		if {[catch {eval $cmd} errMsg]} {
			::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
			set cmdState $::sth::sthCore::FAILURE
			return $returnKeyedList
		}
		if {!$cmdStatus} {
            keylset returnKeyedList status $::sth::sthCore::FAILURE
			keylset returnKeyedList Errmsg "Failed for the handle $::sth::Mvpn::emulation_mvpn_control_user_input_args_array(handle)"
			return $returnKeyedList
		}
	}
	set ::sth::Mvpn::emulation_mvpn_control_user_input_args_array(handle) $handleList
    
    #return 
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList			
}

proc ::sth::emulation_mvpn_info { args } {
    ::sth::sthCore::Tracker ::emulation_mvpn_info $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mvpn_info"
        set _hltNameSpace "::sth::Mvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mvpn::MvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    #Executing the ::sth::emulation_mvpn_control funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #return 
	if {!$cmdStatus} {
                keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
	} else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
	}    
}
