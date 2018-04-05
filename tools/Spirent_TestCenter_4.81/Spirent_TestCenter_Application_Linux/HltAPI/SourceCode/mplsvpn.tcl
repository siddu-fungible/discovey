# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth:: {
}

proc ::sth::emulation_mpls_l2vpn_pe_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_l2vpn_pe_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mpls_l2vpn_pe_config"
        set _hltNameSpace "::sth::Mplsvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mplsvpn::MplsvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    #Executing the ::sth::emulation_mvpn_provider_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying PE configuration: $msg"
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

proc ::sth::emulation_mpls_l2vpn_site_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_l2vpn_site_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mpls_l2vpn_site_config"
        set _hltNameSpace "::sth::Mplsvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mplsvpn::MplsvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    #Executing the ::sth::emulation_mvpn_provider_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  

    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying VPN site configuration: $msg"
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

proc ::sth::emulation_mpls_l3vpn_pe_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_l3vpn_pe_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mpls_l3vpn_pe_config"
        set _hltNameSpace "::sth::Mplsvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mplsvpn::MplsvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    #Executing the ::sth::emulation_mvpn_provider_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  

    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying PE configuration: $msg"
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

proc ::sth::emulation_mpls_l3vpn_site_config { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_l3vpn_site_config $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mpls_l3vpn_site_config"
        set _hltNameSpace "::sth::Mplsvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mplsvpn::MplsvpnTable $args \
                                                           $_hltNameSpace \
                                                           $_hltCmdName \
                                                           ${_hltSpaceCmdName}\_user_input_args_array \
                                                           ${_hltSpaceCmdName}\_sortedSwitchPriorityList

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdState $::sth::sthCore::FAILURE
    
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    #Executing the ::sth::emulation_mvpn_provider_port_config funcition
    set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }  
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying vpn site configuration: $msg"
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

proc ::sth::emulation_mpls_vpn_control { args } {
    ::sth::sthCore::Tracker ::emulation_mpls_vpn_control $args
    
	variable ::sth::sthCore::SUCCESS
	variable ::sth::sthCore::FAILURE
        
        set _hltCmdName "emulation_mpls_vpn_control"
        set _hltNameSpace "::sth::Mplsvpn::"
        set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
        
	variable ${_hltSpaceCmdName}\_user_input_args_array
	array unset ${_hltSpaceCmdName}\_user_input_args_array
	array set ${_hltSpaceCmdName}\_user_input_args_array {}
        
        variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
      
	set returnKeyedList ""
	set underScore "_"
        

	::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

        #command init
	::sth::sthCore::commandInit ::sth::Mplsvpn::MplsvpnTable $args \
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
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error when applying configuration: $msg"
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

