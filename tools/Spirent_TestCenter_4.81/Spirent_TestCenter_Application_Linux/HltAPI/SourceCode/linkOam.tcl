namespace eval ::sth {}

##Procedure Header
#
# Name:
#    sth::emulation_efm_config
#
# Purpose:
#    Configures EFM emulation for a given port. Also,has the ability to
#    toggle certain EFM (OAM 802.3ah) link events. Note, when toggling
#    the link events the EFM session should remain in the ?UP? state.
#
# Synopsis:
#    sth::emulation_efm_config
#         -port_handle <port_handle>
#		  [-mode {create|modify|destroy|reset}]
#         [-mac_local <aa:bb:cc:dd:ee:ff>]
#		  [-oui_value <6 HEX chars>]
#		  [-vsi_value <8 HEX chars>]
#		  [-unidirectional {0|1}]
#         [-error_symbol_period_window <1-65535>]
#         [-error_symbol_period_threshold <0-65535 >]
#		  [-error_frame_window <10-600>]
#		  [-error_frame_threshold <0-65535 >]
#         [-error_frame_period_window <1-65535>]
#         [-error_frame_period_threshold <0-65535 >]
#         [-error_frame_summary_window <100-9000>]
#         [-error_frame_summary_threshold <0-65535>]
#		  [-oam_mode {active|passive}]
#         [-remote_loopback {0|1}]
#		  [-link_events {0|1}]
#		  [-variable_retrieval {0|1}]
#		  [-critical_event {0|1}]
#         [-dying_gasp {0|1}]
#
# Arguments:
#
#    -mac_local
#		Defines the mac address of the emulated device(s).
#
#    -oui_value
#		Defines the Organizational Unique Identifier value.
#		Input format should be 6 HEX chars. The default is 000000.
#					
#    -vsi_value
#		Defines the Vendor-Specific Identifier value. 
#		Input format should be 8 HEX chars. The default is 00000000.
# 					
#    -unidirectional
#               Specifies that EFM should run in UniDirectional mode. 
#		Possible values are 0 and 1. The default is 0.
#
#    -mode
#               Specifies the action to perform on the specified test port.
#               The modes are described below:
#
#                   create - Creates one EFM router on the port
#                        specified with the -port_handle argument. You must
#                        specify the -port_handle argument.
#
#                   modify - Changes the configuration for the EFM router
#                        identified by the -port_handle argument. You must
#                        specify the -port_handle argument.
#
#                   destroy - Deletes all of the EFM routers specified in the
#                        -port_handle argument. You must specify the -port_handle 
#                        argument.
#
#		    reset - Same as destroy mode.
#
#    -port_handle
#                 Specifies the port handle, a string value, to use when
#                 mode is set to "create", "modify", "destroy", or "reset".
#		  This argument is mandatory only for every mode 
#              
#    -error_symbol_period_window
#
#		  Defines the window for Errored Symbol Period Events. 
#		  Possible values range from 1 to 65535. The default is 500.
#				
#    -error_symbol_period_threshold
#
#     		  Defines the threshold for Errored Symbol Period Events.
#		  Possible values range from 0 to 65535. The default is 50.
#
#    -error_frame_window
#
#  		  Defines the window for Errored Frame Events.
#		  Possible values range from 10 to 600. The default is 400.
#					
#    -error_frame_threshold
#
#		  Defines the threshold for Errored Frame Events.
#		  Possible values range from 0 to 65535. The default is 40.
#
#    -error_frame_period_window
#
#		  Defines the window for Errored Frame Period Events.
#		  Possible values range from 1 to 65535.The default is 300.
#
#    -error_frame_period_threshold
#
#		  Defines the threshold for Errored Frame Period Events.
#		  Possible values range from 0 to 65535.The default is 30.
#
#    -error_frame_summary_window
#
#		  Defines the window for Errored Frame Second Summary Events.
#		  Possible values range from 100 to 9000.The default is 200.
#
#    -error_frame_summary_threshold
#
#		  Defines the threshold for Errored Frame Second Summary Events
#		  Possible values range from 0 to 65535. The default is 20.
#
#    -oam_mode
#		  Defines the Link OAM mode to use.Possible values are Active and Passive.
#		  The default is Active.
#
#    -remote_loopback
#		  Specifies that TGEN EFM emulation should attempt to put it's
#		  peer into Remoteloopback mode. Possible values are 0 and 1. 
#		  The default is 0.
#
#    -link_events
#		  Specifies that TGEN EFM emulation should have link-events enabled.
#		  Possible values are 0 and 1. The default is 0.
#
#    -variable_retrieval
#		  Specifies that TGEN EFM emulation should have variable retrieval
#		  enabled. Possible values are 0 and 1.
#
#    -critical_event
#		  Send Critical Event message to EFM peer.Possible values are 0 and 1. 
#		  The default is 0.
#
#    -dying_gasp
#		  Send Dying Gasp message to EFM peer.Possible values are 0 and 1.
#		  The default is 0.       
#
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.xx.
#
#       -size
#	-passive_peer_only
#	-link_fault
#		
#
# Return Values:
#    The sth::emulation_efm_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handles   A list of handles that identify the routers created by the
#              sth::emulation_efm_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_efm_config function creates, modifies, 
#    destroys, or resets an emulated EFM router. Use the -mode
#    argument to specify the action to perform. (See the -mode argument
#    description for information about the actions.)
#
#    After you create a router, use the "emulation_efm_control -mode start"
#    command for Spirent HLTAPI to start the router communication.
#
#    Once you start sessions, Spirent HLTAPI handles all of the message
#    traffic for the emulated routers. During the test, use the
#    sth::emulation_efm_control function to stop and re-start individual
#    routers. 
#
# Examples: The following example creates a EFM router:
#
#    sth::emulation_efm_config 
#          -port_handle $hltSourcePort \
#          -mode create \
#          -mac_local 00:10:94:00:00:01 \
#          -oui_value 094567 \
#          -vsi_value 943b3412 \
#          -error_symbol_period_window 100 \
#          -error_symbol_period_threshold 10 \
#          -error_frame_window 200 \
#          -error_frame_threshold 20 \
#          -error_frame_period_window 500 \
#          -error_frame_period_threshold 50 \
#	   -error_frame_summary_window 600 \
#	   -error_frame_summary_threshold 60 \
#	   -oam_mode active \
#	   -remote_loopback 1 \
#          -link_events 1 \
#          -variable_retrieval 1 \
#          -critical_event 0 \
#          -dying_gasp 0
#
#
# Sample output for example shown above:     
#       {handle router1} {handles router1} {status 1} 	
#
# The following example modifies the created EFM router:
#
#    sth::emulation_efm_config \
#         -mode modify \
#         -handle efmRtrHandle1 \
#         -oam_mode passive
#
# Sample output for example shown above:  
#       {handle router1} {handles router1} {status 1}
#
# The following example deletes the specified EFM router:
#
#    sth::emulation_efm_config \
#         -mode delete \
#         -handle efmRtrHandle
#
#  or sth::emulation_efm_config \
#	    -mode reset \
#	    -handle efmRtrHandle
#
# Sample output for example shown above:     {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_efm_config { args } {

    variable ::sth::LinkOam::sortedSwitchPriorityList
    array unset ::sth::LinkOam::userArgsArray
    array set ::sth::LinkOam::userArgsArray ""
    
    set sortedSwitchPriorityList ""
    set returnKeyedList ""
    
    ::sth::sthCore::Tracker emulation_efm_config $args
    if {[catch {::sth::sthCore::commandInit \
                        ::sth::LinkOam::LinkOamTable \
                        $args \
                        ::sth::LinkOam:: \
                        emulation_efm_config \
                        ::sth::LinkOam::userArgsArray \
                        ::sth::LinkOam::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err"  {}
        return $returnKeyedList
    }
    
    # remap "reset" mode to "destroy"
    set mode [string map -nocase {reset destroy} $::sth::LinkOam::userArgsArray(mode)]
    if {[catch {::sth::LinkOam::emulation_efm_config_$mode returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Failed in $mode\ing Ethernet EFM router:$err" {}
        return $returnKeyedList
    }  
    
    return $returnKeyedList
}
##Procedure Header
#
# Name:
#    sth::emulation_efm_control
#
# Purpose:
#    Starts or stops a EFM router from routing traffic for the specified port.
#
# Synopsis:
#    sth::emulation_efm_control
#       [-port_handle <port_handle>]
#       [-action {start|stop}]
#       
#    -port_handle
#               Identifies the port handleon which to stop or start the router.
#		This argument is mandatory.
#
#    -mode
#               Specifies the action to be taken on the specified port handle.
#               Possible values are start or stop. This argument is mandatory.
#
#                   stop - Stops the router for the specified port.
#
#                   start - Starts the router for the specified port.
#
#
# Cisco-specific Arguments:
#   none
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status    Success (1) or failure (0) of the operation.
#         log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_efm_control function controls the routing of
#    traffic through the specified ports. You can use the function to perform
#    several actions: starting routers and stopping routers.
#
#
# Examples:
#  To start all EFM routers on the specified port:
#       sth::emulation_efm_control -mode start -port_handle $portHandle
#
#   To stop all EFM routers on the specified port:
#       sth::emulation_efm_control -mode stop -port_handle $portHandle]
#
# Sample Input: See Examples.
#
# Sample Output: {status 1}
#
# Notes: 
#       None
#
# End of Procedure Header

proc ::sth::emulation_efm_control {args} {
    variable ::sth::LinkOam::sortedSwitchPriorityList
    variable ::sth::LinkOam::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
    
    ::sth::sthCore::Tracker emulation_efm_control $args
    if {[catch {::sth::sthCore::commandInit ::sth::LinkOam::LinkOamTable $args \
                                                    ::sth::LinkOam:: \
                                                    emulation_efm_control \
						    ::sth::LinkOam::userArgsArray \
						    ::sth::LinkOam::sortedSwitchPriorityList} eMsg]} {
	    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $eMsg"
	    return $returnKeyedList
    }
    
    if {[info exists userArgsArray(port_handle)]} {
        set portHandle $userArgsArray(port_handle)
        foreach userArgsArray(port_handle) $portHandle {
			if {![::sth::sthCore::IsPortValid $userArgsArray(port_handle) err]} {
				::sth::sthCore::processError returnKeyedList "$userArgsArray(port_handle) is not a valid port handle" {}
				return $returnKeyedList 
			}
		
		
			set action "start"
			if {[info exist userArgsArray(action)]} {
				set action $userArgsArray(action)
				if {$userArgsArray(action) == "start_loopback" || $userArgsArray(action) == "start_variable_request" || $userArgsArray(action) == "start_organization_specific_event" ||
					$userArgsArray(action) == "start_event_notification" || $userArgsArray(action) == "resume"} {
					set action "start_send_pdu"
				}
				 if {$userArgsArray(action) == "stop_loopback" || $userArgsArray(action) == "stop_variable_request" ||
					$userArgsArray(action) == "stop_organization_specific_event" || $userArgsArray(action) == "stop_event_notification"} {
					set action "stop_send_pdu"
				}
			}
			if {[catch {::sth::LinkOam::emulation_efm_control_$action returnKeyedList} err]} {
			::sth::sthCore::processError returnKeyedList "Failed in $::sth::LinkOam::userArgsArray(action)\ing Ethernet EFM router:$err" {}
				return $returnKeyedList
			}
			
			if {[catch {::sth::sthCore::doStcApply} err]} {
				::sth::sthCore::processError returnKeyedList "Error applying Link OAM configuration: $err"
				return $returnKeyedList
			}
		}
		set userArgsArray(port_handle) $portHandle
	} else {
        ::sth::sthCore::processError returnKeyedList "missing a mandatory argument: port_handle" {}
        return$returnKeyedList
    }
        
    return $returnKeyedList
}
##Procedure Header
#
# Name:
#    sth::emulation_efm_stat
#
# Purpose:
#    Get EFM port statistics.
#
# Synopsis:
#    sth::emulation_efm_stat
#         -port_handle <port_handle>
#         -action   {get|reset}
#         
# Arguments:
#    -mode
#               Specifies the action to do with the EFM stats for the port.
#               Possible values are get and reset.
#
#                   get  - gets all EFM statistics for each port.
#
#                   reset - resets all EFM statistics for each port.
#
#    -port_handle
#                Specifies the ports from which to extract EFM session data.
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null.
#
#         port_handle    Retrieves the specified port handle.
#
#	  statistics     Retrieves the EFM port statistics including:
#               mac_remote
#		        oam_mode
#			unidir_enabled
#			remote_loopback_enabled
#			link_events_enabled
#			variable_retrieval_enabled
#			oampdu_size
#			oampdu_count
#			oui_value
#			vsi_value
# 		alarms
#			errored_symbol_period_events
#			errored_frame_events
#			errored_frame_period_events
#			errored_frame_seconds_summary_events
##
# Description:
#    The sth::emulation_efm_stat function provides information about the
#    ports specified for the EFM configuration.
#
#    This function returns the requested data and a status value (1 for
#    success). If there is an error, the function returns the status value (0)
#    and an error message. Function return values are formatted as a keyed list
#    (supported by the Tcl extension software - TclX). Use the TclX function
#    keylget to retrieve data from the keyed list. (See Return Values for a
#    description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input:
#               sth::emulation_efm_stat
#                    -action get \
#                    -port_handle $portHandle
#
# Sample Output: 
#  {port_handle port1} {statistics {
#  {mac_remote {{variable_retrieval_enabled TRUE} {remote_loopback_enabled TRUE}
#  {oam_mode PASSIVE} {link_events_enabled TRUE} {unidir_enabled TRUE} 
#  {vsi_value {0000 0000}} {oampdu_count 0}}} 
#  {alarms {{errored_symbol_period_events 0} {errored_frame_events 0} 
#  {errored_frame_period_events 0} {errored_frame_seconds_summary_events 0}}}}}
#  {status 1}
#
# Notes: 
#       The only statistics keys supported are:
#
#           statistics
#               mac_remote
#		        oam_mode
# 			unidir_enabled
#			remote_loopback_enabled
#			link_events_enabled
#			variable_retrieval_enabled
#			oampdu_count
#			oui_value
#			vsi_value
#	        alarms
#			errored_symbol_period_events
#			errored_frame_events
#			errored_frame_period_events
#			errored_frame_seconds_summary_events
#
# End of Procedure Header

proc ::sth::emulation_efm_stat {args} {
    ::sth::sthCore::Tracker ::sth::emulation_efm_stat $args 

    variable ::sth::LinkOam::sortedSwitchPriorityList
    variable ::sth::LinkOam::userArgsArray
    array unset userArgsArray
    array set userArgsArray {}
    
    set returnKeyedList ""
	if {[catch {::sth::sthCore::commandInit ::sth::LinkOam::LinkOamTable $args \
							::sth::LinkOam:: \
							emulation_efm_stat \
							::sth::LinkOam::userArgsArray \
							::sth::LinkOam::sortedSwitchPriorityList} err]} {
		::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit error. Error: $err"
		return $returnKeyedList
	}
        set action $::sth::LinkOam::userArgsArray(action)
	if {[catch {::sth::LinkOam::emulation_efm_stat_$action returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "$err" {}
		return $returnKeyedList
	}

	return $returnKeyedList
}