# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.
package require Tclx

namespace eval ::sth {
}

proc ::sth::emulation_lag_config { args } {
    ::sth::sthCore::Tracker ::emulation_lag_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lacp::lacpTable

    set _hltCmdName "emulation_lag_config"
    set myNameSpace "::sth::Lacp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lacp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lacp::lacpTable $args $myNameSpace $_hltCmdName ::sth::Lacp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lacp::switchToValue(mode)
    
    switch -exact $modeValue {
        create {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        enable {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        disable {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        delete {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList
        }
    }
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Lag configuration in config: $msg"
        return $returnKeyedList 
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}


proc ::sth::emulation_lacp_config { args } {
    ::sth::sthCore::Tracker ::emulation_lacp_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lacp::lacpTable

    set _hltCmdName "emulation_lacp_config"
    set myNameSpace "::sth::Lacp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lacp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lacp::lacpTable $args $myNameSpace $_hltCmdName ::sth::Lacp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lacp::switchToValue(mode)
    
    switch -exact $modeValue {
        enable {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        modify {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue {$args} returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        disable {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -mode value $modeValue" {}
            return $returnKeyedList
        }
    }
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Lacp configuration in config: $msg"
        return $returnKeyedList 
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}

proc ::sth::emulation_lacp_control { args } {
    ::sth::sthCore::Tracker ::emulation_lacp_control $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lacp::lacpTable

    set _hltCmdName "emulation_lacp_control"
    set myNameSpace "::sth::Lacp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lacp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lacp::lacpTable $args $myNameSpace $_hltCmdName ::sth::Lacp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lacp::switchToValue(action)
    
    switch -exact $modeValue {
        start {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        stop {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -action value $modeValue" {}
            return $returnKeyedList
        }
    }
    
    if {[info exists ::sth::Lacp::switchToValue(port_handle)]} {
		set handlesList $::sth::Lacp::switchToValue(port_handle)
		foreach ::sth::Lacp::switchToValue(port_handle) $handlesList {
		
			if {[catch {set procResult [eval $cmd]} eMsg]} {
				::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
				return $returnKeyedList
			}
			
			if {[catch {::sth::sthCore::doStcApply} msg]} {
				::sth::sthCore::processError returnKeyedList "Error applying Lacp configuration in config: $msg"
				#setting back the list of handles 
				set sth::Lacp::switchToValue(port_handle) $handlesList
				set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList warning "$::sth::Lacp::switchToValue(port_handle) mode:  $modeValue Failed"]
				return $returnKeyedList 
			}
			
			::sth::sthCore::log stccall \
				"SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

			if {!$cmdStatus} {
				set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList warning "$::sth::Lacp::switchToValue(port_handle) mode:  $modeValue Failed"]
				return $returnKeyedList
			}
		}
	}
	# setting back list of the handles
	set sth::Lacp::switchToValue(port_handle) $handlesList
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
    return $returnKeyedList
}

proc ::sth::emulation_lacp_info { args } {
    ::sth::sthCore::Tracker ::emulation_lacp_info $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Lacp::lacpTable

    set _hltCmdName "emulation_lacp_info"
    set myNameSpace "::sth::Lacp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Lacp::switchToValue}
    
    if {[catch {::sth::sthCore::commandInit ::sth::Lacp::lacpTable $args $myNameSpace $_hltCmdName ::sth::Lacp::switchToValue slist} eMsg]} {  
            ::sth::sthCore::processError returnKeyedList $eMsg {}
            return $returnKeyedList  
    }
    
    set modeValue $::sth::Lacp::switchToValue(action)
    
    switch -exact $modeValue {
        collect {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        clear {
            set cmdStatus 0
            set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
            ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
        }
        default {
            #Unknown value for switch Mode.
            ::sth::sthCore::processError returnKeyedList "Unsupported -action value $modeValue" {}
            return $returnKeyedList
        }
    }
    
    if {[catch {set procResult [eval $cmd]} eMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
        return $returnKeyedList
    }
    
    if {[catch {::sth::sthCore::doStcApply} msg]} {
        ::sth::sthCore::processError returnKeyedList "Error applying Lacp configuration in config: $msg"
        return $returnKeyedList 
    }
    
    ::sth::sthCore::log stccall \
        "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:action, Value:$modeValue. ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}