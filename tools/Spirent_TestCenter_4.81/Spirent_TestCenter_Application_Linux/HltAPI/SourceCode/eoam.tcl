# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth {
}

proc ::sth::emulation_oam_config_msg { args } {
    ::sth::sthCore::Tracker ::emulation_oam_config_msg $args
	
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
        
    set _hltCmdName "emulation_oam_config_msg"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log debug "Executing command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Eoam::EoamTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList
    }
    
    #switch mode 
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    switch -exact $modeValue {
        create {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "            
            
        }
        reset {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
	    ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList 
        }
    }

    #executing the mode function
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
	return $returnKeyedList
    }

    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
   
    #return 
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
	return $returnKeyedList
    } else {
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList			
    }    
    
}


proc ::sth::emulation_oam_config_ma_meg { args } {
    ::sth::sthCore::Tracker ::emulation_oam_config_ma_meg $args
	
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
        
    set _hltCmdName "emulation_oam_config_ma_meg"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log debug "Executing command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Eoam::EoamTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList
    }
    
    #switch mode 
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]
    
    switch -exact $modeValue {
        add {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "            
            
        }
        delete {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
	    ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList 
        }
    }

    #executing the mode function
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
	return $returnKeyedList
    }

    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
   
    #return 
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
		return $returnKeyedList
    } else {
		keylset returnKeyedList status $::sth::sthCore::SUCCESS
		return $returnKeyedList			
    }    
    
}


proc ::sth::emulation_oam_config_topology { args } {
    ::sth::sthCore::Tracker ::emulation_oam_config_topology $args
	
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
        
    set _hltCmdName "emulation_oam_config_topology"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log debug "Excuting command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Eoam::EoamTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList
    }
    
    #switch mode 
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]

    switch -exact $modeValue {
        create {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "            
            
        }
        reset {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
	    ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList 
        }
    }

    #executing the mode function
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying EOAM topology configuration: $msg"
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
 
proc ::sth::emulation_oam_control { args } {
    ::sth::sthCore::Tracker ::emulation_oam_control $args
	
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
        
    set _hltCmdName "emulation_oam_control"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log debug "Excuting command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Eoam::EoamTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList
    }
    
    #switch mode 
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(action)]

    switch -exact $modeValue {
        start {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        stop {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "            
            
        }
        reset {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
	    ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList 
        }
    }

    #executing the mode function
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying EOAM topology configuration: $msg"
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

proc ::sth::emulation_oam_info { args } {
    ::sth::sthCore::Tracker ::emulation_oam_info $args
	
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
        
    set _hltCmdName "emulation_oam_info"
    set _hltNameSpace "::sth::Eoam::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"
    
    ::sth::sthCore::log debug "Excuting command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Eoam::EoamTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: ::sth::sthCore::commandInit $err" {}
        return -code error $returnKeyedList
    }
    
    #switch mode 
    set modeValue [set ${_hltSpaceCmdName}\_user_input_args_array(mode)]

    switch -exact $modeValue {
        aggregate {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "
        }
        session {
            set cmdStatus $::sth::sthCore::FAILURE
            set cmd "${_hltSpaceCmdName}\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log debug "CMD which will process for mode($modeValue): $cmd "            
            
        }
        default {
            #Unknown value for switch Mode.
	    ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList 
        }
    }

    #executing the mode function
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        set cmdState $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
        return $returnKeyedList
    }
    
    #apply the stc configuration
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying EOAM topology configuration: $msg"
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