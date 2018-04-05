# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth {
}

#::sth::sthCore::sthCoreInit
#set ::sth::sthCore::enableHltcalllog TRUE
#set ::sth::sthCore::enableStccalllog TRUE
#set ::sth::sthCore::enableInternallog TRUE

proc ::sth::sthCore::getValueOfSwitch {args} {
	
	set inputArgs [lindex $args 0]
	set switchName [lindex $args 1]
	set switchValue [lindex $args 2]
	
	upvar 1 $switchValue value
	
	set switchIndex [string first $switchName $inputArgs]
	if {$switchIndex < 0} {
		return 0
	}
	set switchIndexAfter [expr $switchIndex+[string length $switchName]]
	
	set Args [string range $inputArgs $switchIndexAfter end]
	
	set value [ctoken Args " \t\n"]
	
	if {[string length $value] <= 0} {
		return 0
	} else {
		return 1
	}
}


##Procedure Header
#
# Name: ::sth::emulation_rsvp_config
#
# Purpose:
#	Creates, enables, modifies, or deletes an emulated resource reservation
#	setup protocol (RSVP) router on a Spirent TestCenter chassis. RSVP is not a
#	routing protocol; RSVP works in conjunction with routing protocols and
#	installs the equivalent of dynamic access lists along the routes that
#	routing protocols calculate.
#
#	RSVP is a resource reservation setup protocol that enables Internet
#	applications to obtain differing qualities of service (QoS) for their data
#	flows. RSVP is used by routers to request a specific quality of service
#	from the network for particular data flows. It is also used to establish
#	and maintain "resource reservations" across a network.
#
# Synopsis:
#	sth::emulation_rsvp_config
#		-port_handle   { port_handle }
#		-mode   {create|modify|delete|disable|enable }
#		[-handle <rsvp_session_handle>]
#		[-count  <integer> ]
#		[-egress_label_mode {nextlabel|imnull|exnull} ]
#		[-hello_interval  <1-65535> ]
#		[-hello_msgs   {1|0} ]
#		[-hello_retry_count  <1-255> ]
#		[-intf_ip_addr   { ip } ]
#		[-intf_ip_addr_step  <0-<max_int>> ]
#		[-intf_prefix_length <1-32> ]
#		[-max_label_value   <1-1048575> ]
#		[-min_label_value   <1-1048575> ]
#		[-neighbor_intf_ip_addr   { ip } ]
#		[-neighbor_intf_ip_addr_step <0-<max_int>>]
#		[-rapid_retx_delta  <1-65535> ]
#		[-rapid_retx_interval <integer>]
#		[-rapid_retx_limit  <1-255> ]
#		[-record_route   {1|0} ]
#		[-refresh_interval <1-4294967295> ]
#		[-refresh_reduction   {1|0} ]
#		[-reliable_delivery   {1|0} ]
#		[-resv_confirm   {1|0} ]
#		[-srefresh_interval <1-4294967295> ]
#		[-vlan_id  <0-4095> ]
#		[-vlan_id_mode {fixed|increment} ]
#		[-vlan_id_step  <1-4094> ]
#		[-vlan_user_priority <0-7> ]
#
# Arguments:
#
#	-count		Defines the number of RSVP routers to create on the
#				interface. Possible values are 0 to <max_int>. The default
#				is 1.
#
#	-egress_label_mode
#				Specifies the label advertisement for the egress of an LSP.
#				Possible values are nextlabel, exnull, and imnull. The 
#				default is nextlabel. These values are described below:
#
#				nextlabel - Advertise the next available label.
#				exnull - Advertise label 9, the explicit null label.
#				imnull - Advertise label 3, the implicit null label.
#
#	-handle		Specifies the RSVP handle to use when the -mode argument is
#				set to modify, delete, enable, or disable. This argument is
#				not valid for create mode. Instead, use -port_handle.
#
#	-hello_interval
#				Specifies the amount of time, in milliseconds, between HELLO
#				messages. Possible values range from 1 to 65535. The default
#				is 5000.
#
#	-hello_msgs
#				Enables or disables the creation of HELLO messages and
#				graceful restart capability. Possible values are 0 (disable)
#				and 1 (enable). The default is 0.
#
#	-intf_ip_addr	Specifies the IP address of the interface for the RSVP
#				emulated router that will establish an adjacency with the
#				DUT. The default for IPv4 is 192.85.1.3.
#
#	-intf_ip_addr_step
#				Specifies the difference between interface IP addresses of
#				consecutive routers when multiple RSVP routers are created.
#				The default increment is 1.
#
#	-intf_prefix_length
#				Specifies the prefix length on the emulated router, Possible
#				values for IPv4 addresses range from 1 to 32; the default is
#				24,
#
#	-max_label_value
#				Specifies the maximum LSP label value. Used to configure
#				refresh reduction capabilities per RFC2961, Possible values
#				range from 1 to 1048575. The default value is 65535.
#
#	-min_label_value
#				Specifies the minimum LSP label value. Used to configure
#				refresh reduction capabilities per RFC2961, Possible values
#				range from 16 to 1048575. The default value is 16.
#
#	-mode		Specifies the action to perform. Possible values are enable,
#				disable, modify, or reset. By default, RSPV is disabled so
#				that it is backward compatible with systems that do not
#				implement RSVP. The modes are described below:
#
#				create - Create and start the RSVP router.
#
#				enable - Create and start the RSVP router.
#
#				disable - Delete all the RSVP routers associated with the
#					specified port.
#
#				modify - Changes the configuration for the RSVP router
#					identified by the -handle argument.
#
#				delete - Deletes all the RSVP routers associated with the
#					specified port.
#
#	-neighbor_intf_ip_addr
#				Specifies the IP address of the interface for the RSVP
#				neighbor (next hop) that will establish an adjacency with
#				the DUT. The default for IPv4 is 192.85.1.3.
#
#	-neighbor_intf_ip_addr_step
#				Specifies the difference between interface IP addresses of
#				consecutive routers when multiple RSVP routers are created.
#				The default increment is 1.
#
#	-port_handle	The port on which to create the emulated router.
#
#	-rapid_retx_delta
#				Specifies the rapid retransmission delta, which is the speed
#				at which the retransmission interval is increased. The ratio
#				of two successive retransmission intervals is (1 + Delta).
#				Possible values range from 1 to 65535. The default is 1.
#
#	-rapid_retx_interval
#				Specifies, in millliseconds, the rapid retransmission
#				interval, which is the initial retransmission interval for
#				unacknowledged messages.  The default is 500.
#
#	-rapid_retx_limit
#				Specifies the rapid retransmission limit, which is the
#				maximum number of times a message can be transmitted without
#				being acknowledged. Possible values range from 1 to 255. The
#				default is 3.
#
#	-record_route	Enables or disables whether to include the RECORD_ROUTE
#				object in the Path message. Possible values are 0 (disable)
#				and 1 (enable). The default is 0.
#
#	-refresh_interval
#				Specifies the amount of time, in milliseconds, between
#				sending RSVP messages to refresh state. Possible values
#				range from 1 to 4294967295. The default is 30000 (30
#				seconds).
#
#	-refresh_reduction
#				Enables or disables refresh reduction. Possible values are 0
#				(disable)	and 1 (enable). The default is 0. The reliable
#				messages, bundle messages, and summary refresh messages are
#				only meaningful when refresh reduction is enabled.
#
#	-reliable_delivery
#				Enables or disables transmitting message IDs. Possible
#				values are 0 (disable)	and 1 (enable). The default is 0.
#				If set to 1, RSVP sends message IDs and acknowledgements for
#				each message received. If set to 0, it does not send message
#				IDs.
#
#	-resv_confirm	Enables or disables whether to require a reservation
#				confirmation message. Possible values are 0 (disable)	and 1
#				(enable). The default is 0. If set to 1, enables and
#				requires RESV confirmation with final parameters from the
#				egress router. If set to 0, does not require sending RESV
#				confirmation messages.
#
#	-srefresh_interval
#				Specifies the time interval, in milliseconds, to gather
#				refresh messages that would have been sent out individually.
#				Messages are sent out as a single refresh message upon
#				interval expiration or when the message size exceeds the
#				MTU. Possible values range from 1 to 4294967295. The default
#				is 30000 (30 seconds).
#
# 	-vlan_id		The VLAN ID of the first VLAN sub-interface. Used to
#				configure refresh reduction capabilities per RFC 2961.
#				Possible values range from 0 to 4095. The default is 1.
#
#	-vlan_id_mode
#				Specifies VLAN ID assignment for multiple router
#				configurations when -count is greater than 1. Valid values
#				are "fixed" or "increment." If you specify "fixed," all of
#				the routers will be assigned the same VLAN ID (the value of
#				the -vlan_id argument). If you specify "increment", then
#				Spirent TestCenter assigns unique VLAN IDs. When you use
#				increment mode, you must also specify the -vlan_id_step
#				argument to define the increment value.
#
# 	-vlan_id_step
#				The value that Spirent TestCenter uses to increment the VLAN
#				ID. You must specify this step when you use specify
#				"increment" for the -vlan_id_mode argument and the router
#				count (-count) is greater than 1. Possible step values range
#				from 1 to 4094.
#
# 	 -vlan_user_priority
#				VLAN user priority assigned to emulated router node.
#				Possible values range from 0 to 7. The default is 0.
#
#
# Return Values: The sth::emulation_rsvp_config function returns a keyed list
#	using the following keys (with corresponding data):
#
#	handles	A list of RSVP handles that identify the routers created by the
#			sth::emulation_rsvp_config function.
#
#	status	Success (1) or failure (0) of the operation.
#
#	log		An error message (if the operation failed).
#
# Description: The sth::emulation_rsvp_config function creates, enables,
#	disables, modifies, or deletes an emulated RSVP router. Use the -mode
#	argument to specify the action to perform. (See the -mode argument
#	description for information about the actions.)
#
#	RSVP has three basic functions: path setup and maintenance, path tear down,
#	and error signaling.
#
#	When you create an emulated router, use the -port_handle argument to
#	specify the Spirent TestCenter port that the emulated router will use for
#	RSVP communication. (The port handle value is contained in the keyed list
#	returned by the connect function.)
#
#	In addition to specifying the port, you must also provide one or more of
#	the following pieces of information when you create an RSVP router:
#
#	- The source IP address for the emulated router (the -intf_ip_addr
#	  argument)
#
#	- The destination IP address for the emulated router (the
#	  -neighbor_intf_ip_addr argument)
#
#	- The port on which to create the emulated router (the -port_handle
#	  argument)
#
#	An RSVP session is a data flow with a particular destination
#	and transport-layer protocol. When you create an RSVP router, Spirent
#	TestCenter starts the router communication. 
#
#	Refresh messages are sent to both synchronize state between RSVP neighbors
#	and to recover from lost RSVP messages.
#
#	There are several RSVP message types but the two most important are "path"
#	and "reservation" messages. Reservation messages are also referred to as
#	"RESV" messages. Path messages are used to set up and maintain (that is,
#	refresh) reservations. RESV messages are used to set up and maintain the
#	"resources requested" as well as "refresh" reservations. An RSVP router
#	sends a path message every 30 seconds (30 seconds is the default refresh
#	interval) to say "Maintain my reserved resources. I still need them." It
#	sends an RESV message every 30 seconds to say "I will hold this reservation
#	for you."
#
#	Once you start sessions by creating routers, Spirent TestCenter handles all
#	of the message traffic for the emulated RSVP routers. During the test, use
#	the sth::emulation_rsvp_control function to stop and re-start individual
#	RSPV routers. To stop and start all of the RSVP routers associated with a
#	particular port, use the disable and enable modes with the
#	sth::emulation_rsvp_config function.
#
# Examples: The following example creates an RSVP router:
#
#::sth::emulation_rsvp_config -mode enable \
#	-egress_label_mode nextlabel \
#	-hello_interval 5000 \
#	-hello_msgs 1 \
#	-intf_ip_addr 90.0.0.3 \
#	-intf_prefix_length 24 \
#	-max_label_value 1048575 \
#	-min_label_value   16 \
#	-neighbor_intf_ip_addr 90.0.0.4 \
#	-port_handle  $port_handle($device,$port1) \
#	-rapid_retx_delta 1 \
#	-rapid_retx_interval 500 \
#	-rapid_retx_limit 3 \
#	-record_route 0 \
#	-refresh_interval 30000 \
#	-refresh_reduction 1 \
#	-reliable_delivery  1 \
#	-resv_confirm 1 \
#	-srefresh_interval 30000
#
# Sample Input:
#
# Sample Output:
#
# Notes:
#		  1) RSVP needs to periodically refresh its reservations in the
#			network by re-signaling them.
#
#		  2)	With RSVP, a reservation goes away only if it is explicitly
#			removed from the network by RSVP or if the reservation "times
#			out".
#
#		  3)	RSVP does not have an explicit neighbor discovery mechanism like
#			LDP, which means that if RSVP is enabled on two different
#			routers, they will not see each other as RSVP neighbors until
#			they receive path and RESV messages from one another.
#
#		  4)	All path messages have a "Router Alert" bit that when set
#			instructs each router along the LSP to examine and process the
#			message.
#
# End of Procedure Header


proc ::sth::emulation_rsvp_config { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable

    set _hltCmdName "emulation_rsvp_config"
    set myNameSpace "::sth::Rsvp::"
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
    
    catch {unset ::sth::Rsvp::switchToValue}
    if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue slist} eMsg]} {  
	::sth::sthCore::processError returnKeyedList $eMsg {}
	return $returnKeyedList  
    }
    set modeValue $::sth::Rsvp::switchToValue(mode)

    switch -exact $modeValue {
    	    create  -
	    enable {
                set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_create returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            active {
                set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
	    activate {
                set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            modify {
                set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            inactive {
                set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            delete -
	    disable {
		set cmdStatus 0
        	set cmd "$myNameSpace$_hltCmdName\_delete returnKeyedList cmdStatus"
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
	} else {
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::processError returnKeyedList "Error applying RSVP configuration: $msg"
            return $returnKeyedList 
        }
		::sth::sthCore::log stccall \
            "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
	}
    if {!$cmdStatus} {
        return $returnKeyedList
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
}


##Procedure Header
#
# Name: ::sth::emulation_rsvp_control
#
# Purpose: Starts or stops RSVP routers.
#
# Synopsis:
#	sth::emulation_rsvp_control
#		-handle <integer>
#		-mode {stop|start|restart}
#		-port_handle <port_handle>
#		[-teardown {1|0} ]
#		[-restore {1|0} ]
#
# Arguments:
#	-handle		Identifies the port on which to stop or start the RSVP
#				router. This argument is required.
#
#	-mode		Specifies the action to be taken. Possible values are stop,
#				start, or restart the RSVP router. This argument is
#				required.
#
#				stop - Stops the router for the specified port.
#
#				start - Starts the router for the specified port.
#
#				restart - Stops and then starts the router for the
#				specified port.
#
#	-port_handle 	Specifies the handle for the port to be controlled.
#
#	-teardown		Enables or disables whether to tear down the LSP tunnels.
#				Possible values are 0 (disable) and 1 (enable). The default
#				is 1.
#
#	-restore		Enables or disables whether you can establish LSP tunnels.
#				Possible values are 0 (disable) and 1 (enable). The default
#				is 1.
#
# Return Values: The function returns a keyed list using the following keys
#			(with corresponding data):
#
#		status 	Success (1) or failure (0) of the operation.
#		log		An error message (if the operation failed).
#
# Description: The emulation_rsvp_control function controls the starting and
#	stopping of RSVP routers as well as the tearing down and restoring of LSP
#	tunnels. When you call the emulation_rsvp_control function, you specify a
#	port handle. Spirent TestCenter applies the specified action to all of the
#	emulated RSVP routers associated with the specified port.
#
# Examples:
#	To start the RSVP router on the specified port:
#
#		::sth::emulation_rsvp_control -mode start \
#			-handle $rsvp_handle(rsvp1) \
#			-teardown $tunnel1
#
# 	To stop the RSVP router on the specified port:
#
#		::sth::emulation_rsvp_control -mode stop \
#			-handle $rsvp_handle(rsvp1)
#
# 	To restart the RSVP router on the specified port:
#
# 		::sth::emulation_rsvp_control -mode restart\
#			-handle $rsvp_handle(rsvp1)
#
# Sample Input: See Examples.
#
# Sample Output: {handle 174} {status 1}
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_rsvp_control { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_control $args
    
    
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
    

    set _hltCmdName "emulation_rsvp_control"
    
    set myNameSpace "::sth::Rsvp::"


    
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""

    catch {unset ::sth::Rsvp::switchToValue}
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue slist} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}
	set modeValue $::sth::Rsvp::switchToValue(mode)
	
    switch -exact $modeValue {
            start {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            stop {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            restart {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			resume_hellos {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			stop_hellos {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			restart_router {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			initiate_make_before_break {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			graft_ingress {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			graft_egress {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			prune_ingress {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
			prune_egress {
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
	set cmdStatusAll 1
	if {[catch {
		if {[info exists ::sth::Rsvp::switchToValue(port_handle)]} {
			set portHndList $::sth::Rsvp::switchToValue(port_handle)
			foreach ::sth::Rsvp::switchToValue(port_handle) $portHndList {
				set returnKeyedList ""
				set procResult [eval $cmd]
				if {!$cmdStatus} {
					#checking status for each port and returning with updated msg and status 
					set cmdStatusAll "$cmdStatus"
					keylset returnKeyedList Errormsg "Failed for the port $::sth::Rsvp::switchToValue(port_handle)"
					append returnKeyedListAll "  $returnKeyedList"
				}
			}
			set ::sth::Rsvp::switchToValue(port_handle) $portHndList
		} elseif {[info exists ::sth::Rsvp::switchToValue(handle)]} {	
			set handleList $::sth::Rsvp::switchToValue(handle)
			foreach ::sth::Rsvp::switchToValue(handle) $handleList {
				set returnKeyedList ""
				set procResult [eval $cmd]
				if {!$cmdStatus} {
					#checking status for each port and returning with updated msg and status 
					set cmdStatusAll "$cmdStatus"
					keylset returnKeyedList Errormsg "Failed for the handle $::sth::Rsvp::switchToValue(handle)"
					append returnKeyedListAll "  $returnKeyedList"
				}
			}
			set ::sth::Rsvp::switchToValue(handle) $handleList
		}
	} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
		return $returnKeyedList
	} else {
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::processError returnKeyedList "Error applying RSVP configuration in control: $msg"
            return $returnKeyedList 
        }
		::sth::sthCore::log stccall \
            "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"
		if {!$cmdStatusAll} {
			return $returnKeyedListAll
		} elseif {!$cmdStatus} {
			return $returnKeyedList
		} else {
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
	}

}




##Procedure Header
#
# Name: ::sth::emulation_rsvp_info
#
# Purpose:
#	Returns information about the RSVP configuration.
#
# Synopsis:
#	sth::emulation_rsvp_info
#		-handle <rsvp_handle>
#		-mode   {stats|settings}
#
# Arguments:
#	-handle		The port for which you want information.
#
#	-mode		Specifies the kind of information you want to see. Possible
#				values are stats and settings. The default is stats.
#
#				stats  - returns transmitted and received statistics for
#					different RSVP messages.
#
#				settings - returns the IP address of the specified RSVP
#					handle.
#
# Return Values: The function returns a keyed list using the following keys
#			(with corresponding data):
#
#		stats		Retrieves the IP address of the specified handle,
#					the number of reserved and path messages sent and
#					received, and information about the LSPs (see list
#					below).
#
#		settings		Retrieves the IP address of the specified RSVP router
#					and of its neighbor that will establish an adjacency to
#					the DUT (see list below).
#
#		status		Retrieves a value indicating the success (1) or failure
#					(0) of the operation.
#
#		log			Retrieves a message describing the last error that
#					occurred during the operation. If the operation was
#					successful - {status 1} - the log value is null
#
#	The following keys are returned when you specify -mode stats:
#
#	ingress_resvconf_tx		Number of reserve confirmation messages sent.
#
#	ingress_patherr_tx		Number of path error messages sent.
#
#	ingress_resverr_rx		Number of reserve error messages received.
#
#	egress_resvconf_rx		Number of reserve confirmation messages received.
#
#	egress_patherr_rx		Number of path error messages received.
#
#	egress_resverr_tx		Number of reserve error messages sent.
#
#	lsp_count				Number of LSPs.
#
#	lsp_created			Number of LSPs up.
#
#	lsp_deleted			Number of LSPs down.
#
#	min_setup_time			Minimum LSP setup time.
#
#	max_setup_time			Maximum LSP setup time.
#
#	num_lsps_setup			Number of LSPs connecting.
#
#	ingress_path_tx		Number of path messages sent.
#
#	ingress_resv_rx		Number of reserve messages received.
#
#	egress_resv_tx			Number of reserve messages sent.
#
#	The following keys are returned when you specify -mode settings:
#
#	intf_ip_address 		IP address of the port on the interface card:
#						a.b.c.d.
#
#	neighbor_intf_ip_addr	IP address of the interface for the RSVP
#						neighbor (next hop) that will establish an
#						adjacency with the DUT: a.b.c.d.
#
# Description:  The emulation_rsvp_info function provides information about
#	either the settings specified for the RSVP configuration or the statistics
#	returned by it.
#
#	This function returns the requested data (statistics or settings
#	information) and a status value (1 for success). If there is an error, the
#	function returns the status value (0) and an error message. Function return
#	values are formatted as a keyed list (supported by the Tcl extension
#	software - TclX). Use the TclX function keylget to retrieve data from the
#	keyed list. (See Return Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input: ::sth::emulation_rsvp_info -mode settings -handle 174
#
# Sample Output: {ip_address 90.0.0.3} {status 1}
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_rsvp_info { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_info $args
    
    
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
    

    set _hltCmdName "emulation_rsvp_info"

    
    set underScore "_"
    
    set myNameSpace "::sth::Rsvp::"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""

    #Validate if the value of port_handle is valid
    catch {unset ::sth::Rsvp::switchToValue}
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue slist} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}
	set modeValue $::sth::Rsvp::switchToValue(mode)

    switch -exact $modeValue {
            stats {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_Generic returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            settings {
                set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_Generic returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            neighbors {
                set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_Generic returnKeyedList cmdStatus"
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
	} else {
		::sth::sthCore::log stccall "SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||"

		if {!$cmdStatus} {
			return $returnKeyedList
		} else {
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
	}

}

proc ::sth::emulation_rsvp_tunnel_info { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_tunnel_info $args

    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
    
    set _hltCmdName "emulation_rsvp_tunnel_info"

    set underScore "_"
    set myNameSpace "::sth::Rsvp::"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""

    #Validate if the value of port_handle is valid
    catch {unset ::sth::Rsvp::switchToValue}
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable \
            $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue slist} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}

    set cmdStatus 0
    set cmd "$myNameSpace$_hltCmdName\_Generic returnKeyedList cmdStatus"
    ::sth::sthCore::log hltcall "CMD which will process for ::sth::emulation_rsvp_tunnel_info: $cmd "
	if {[catch {set procResult [eval $cmd]} eMsg]} {
		::sth::sthCore::processError returnKeyedList "Error while running $cmd. Error: $eMsg"
		return $returnKeyedList
	} else {
		::sth::sthCore::log stccall "SUBCOMMAND RESULT for command: $_hltCmdName. ||$returnKeyedList||"

		if {!$cmdStatus} {
			return $returnKeyedList
		} else {
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
	}

}

##Procedure Header
#
# Name: ::sth::emulation_rsvp_tunnel_config
#
# Purpose:
#	Creates, modifies, or deletes LSP tunnels on the specified test port
#	running RSVP emulation. When you create LSP tunnels using RSVP as a
#	signaling protocol, these tunnels can be automatically or manually routed
#	away from network failures, congestion, and bottlenecks automatically.
#
# Synopsis:
#	sth::emulation_rsvp_tunnel_config
#		-mode {create|modify|delete}
#		-handle <integer>
#		[-count <0-max_int>]
#		[-egress_ip_addr <a.b.c.d> ]
#		[-egress_ip_step <integer> ]
#		[-ero_list_ipv4 {ipv4List} ]
#		[-ero_list_loose {0|1} ]
#		[-ero_list_pfxlen <1-128> ]
#		[-handle <rsvp_session_handle> ]
#		[-ingress_ip_addr  <a.b.c.d> ]
#		[-ingress_ip_step  <integer> ]
#		[-sender_tspec_max_pkt_size <1-4294967295> ]
#		[-sender_tspec_min_policed_size <1-4294967295> ]
#		[-sender_tspec_peak_data_rate <1-43980465111040>]
#		[-sender_tspec_token_bkt_rate <1-43980465111040>]
#		[-sender_tspec_token_bkt_size <1-4294967295> ]
#		[-session_attr {0|1} ]
#		[-session_attr_bw_protect {0|1} ]
#		[-session_attr_flags <0-255> ]
#		[-session_attr_hold_priority <0-7> ]
#		[-session_attr_label_record {0|1} ]
#		[-session_attr_local_protect {0|1} ]
#		[-session_attr_name   { any }  ]
#		[-session_attr_node_protect {0|1} ]
#		[-session_attr_ra_exclude_any   { 0-0xFFFFFFFF }  ]
#		[-session_attr_ra_include_all   { 0-0xFFFFFFFF }  ]
#		[-session_attr_ra_include_any   { 0-0xFFFFFFFF }  ]
#		[-session_attr_resource_affinities {0|1} ]
#		[-session_attr_se_style  {0|1} ]
#		[-session_attr_setup_priority  <0-7> ]
#		[-tunnel_id_start <0-65535> ]
#		[-tunnel_id_step  <integer> ]
#		[-tunnel_pool_handle <rsvpte_tunnel_pool_handle> ]
#
# Arguments:
#
#	-count		Defines the number of tunnels to create to the specified
#				egress point (that is, the tunnel end point). Possible
#				values are 0 to <max_int>. The default is 1.
#
#	-egress_ip_addr
#				Specifies the IP address of the tunnel's egress (end) point.
#				The default for IPv4 is 192.85.1.1.
#
#	-egress_ip_step
#				Specifies the difference between egress IP addresses when
#				multiple tunnels are created.
#
#	-ero_list_ipv4 Specifies the IPv4 prefixes (that is, subobjects), one for
#				each entry in a path message for ingress (incoming) tunnels.
#				Use this argument with the -ero_list_loose and
#				-ero_list_pfxlen arguments.
#
#	-ero_list_loose
#				Specifies the value of the L bit in the explicit route
#				object's subobject. Possible values are 1 (loose) and 0
#				(strict). If you specify 1 for the L bit, the subobject
#				represents a loose hop in the explicit route. If you specify
#				0 for the L bit, the subobject represents a strict hop in
#				the explicit route. The default is 0. Use this argument with
#				the -ero_list_ipv4 and -ero_list_pfxlen arguments.
#
#	-ero_list_pfxlen
#				Specifies the IPv4 prefix length. The default is 32. This
#				argument only applies to ingress (incoming) tunnels. Use
#				this argument with the -ero_list_ipv4 and -ero_list_loose
#				arguments.
#
#	-handle		Identifies the RSVP router for which to add or remove
#				tunnels. This argument is required.
#
#	-ingress_ip_addr
#				Specifies the IP address of the tunnel's ingress (start)
#				point. The default is 192.85.1.3
#
#	-ingress_ip_step
#				Specifies the increment for IP addresses for multiple
#				ingress tunnels. Possible values range from 0 to <max_int>. 
#				The default is 1.
#
#	-mode		Specifies the action to perform on tunnels for the RSVP
#				emulated router. Possible values are create, modify, and
#				delete:
#
#				create - Creates an RSVP tunnel for the RSVP emulated router
#					identified by the -handle argument.
#
#				modify - Changes the configuration for the tunnel
#					identified by the -tunnel_pool_handle argument.
#
#				delete - Deletes the tunnels identified by the
#					-tunnel_pool_handle argument.
#
#	-sender_tspec_max_pkt_size
#				Specifies the maximum packet size in bytes. The maximum
#				packet size is the biggest packet that will conform to the
#				traffic specifications. Packets larger than this size sent
#				into the network may not receive QoS-controlled service
#				because they do not meet the traffic specification. Possible
#				values are 1 to 4294967295. The default is 4096. This
#				argument only applies to ingress (incoming) tunnels.
#
#	-sender_tspec_min_policed_size
#				Specifies the minimum policed size in bytes. This size
#				includes the the application data and all protocol headers
#				at or above the IP level (IP, TCP, UDP, RTP, etc.). It does
#				not include the link-level header size, because these
#				headers will change in size as the packet crosses different
#				portions of the internetwork.Possible values are 1 to
#				4294967295. The default is 64. This argument only applies to
#				ingress (incoming) tunnels.
#
#	-sender_tspec_peak_data_rate
#				Specifies the peak data rate in bytes of IP datagrams per
#				second. Possible values range from 1 byte per second to 40
#				terabytes per second (43980465111040 bytes). The default is
#				512000. This argument only applies to ingress (incoming)
#				tunnels.
#
#	-sender_tspec_token_bkt_rate
#				Specifies the token bucket rate in bytes of IP datagrams per
#				second. Possible values range from 1 byte per second to 40
#				terabytes per second (43980465111040 bytes). The default is
#				128000. This argument only applies to ingress (incoming)
#				tunnels.
#
#	-sender_tspec_token_bkt_size
#				Specifies the token bucket size in bytes. Possible values
#				are 1 to 4294967295. The default is 256000. This argument
#				only applies to ingress (incoming) tunnels.
#
#	-session_attr	Enables or disables whether to include the SESSION_ATTRIBUTE
#				object in the Path message. Possible values are 0 (disable)
#				and 1 (enable). The default is 1. This argument only applies
#				to ingress (incoming) tunnels.
#
#	-session_attr_bw_protect
#				Indicates to the point of local repairs (PLRs) along the
#				protected LSP path whether a backup path with a bandwidth is
#				guaranteed. Possible values are 0 (disable) and 1
#				(enable). The default is 0. This argument only applies
#				to ingress (incoming) tunnels.
#
#	-session_attr_flags
#				Sets the following session attribute flags at the same time:
#				-session_attr_hold_priority  (bit 0)
#				-session_attr_label_record (bit 1)
#				-session_attr_se_style (bit 2)
#				-session_attr_bw_protect (bit 3)
#				-session_attr_node_protect (bit 4)
#
#				You can use this argument to set the session attribute flags
#				at one time instead of setting each flag individually for
#				those five arguments (listed above). Possible values are
#				from 0 to 255. The default is 0. For example, to enable the
#				first five flags, specify -session_attr_flags 31. The RSVP
#				protocol converts the binary setting (11111) to its decimal
#				equivalent (31). This argument only applies to ingress
#				(incoming) tunnels.
#
#	-session_attr_hold_priority
#				Specifies the priority at which resources assigned to this
#				session will be reserved. Possible values range from 0 to 7,
#				with 0 representing the highest priority. The default is 7.
#				RSVP-TE uses the holding priority to determine whether this
#				session can be preempted by another session. This argument
#				only applies to ingress (incoming) tunnels.
#
#	-session_attr_label_record {0|1} ]
#				Specifies whether to include label information when doing
#				a record route. Possible values are 0 (disable) and 1
#				(enable). The default is 0. There are two record_route
#				subobjects: IP addresses and labels. Either the Ip address
#				at each hop in the path is recorded or the label used at
#				every hop is recorded. This argument only applies to ingress
#				(incoming) tunnels.
#
#	-session_attr_local_protect {0|1} ]
#				Specifies whether transit routers are permitted to use a
#				local repair mechanism which may result in violation of the
#				explicit route object.  When a fault is detected on an
#				adjacent downstream link or node, a transit router can
#				reroute traffic for fast service restoration. Possible
#				values are 0 (disable) and 1 (enable). The default is 0.
#				This argument only applies to ingress (incoming) tunnels.
#
#	-session_attr_name
#				Specifies a name for the session. The default name is
#				Tunnel1. This argument only applies to ingress (incoming)
#				tunnels.
#
#	-session_attr_node_protect
#				Indicates to the point of local repairs (PLRs) along a
#				protected LSP path whether a backup path which bypasses at
#				least the next node of the protected LSP is desired
#				Possible values are 0 (disable) and 1 (enable). The default
#				is 0. This argument only applies to ingress (incoming)
#				tunnels.
#
#	-session_attr_ra_exclude_any
#				Sets the affinity bits in the session attribute object that
#				are excluded. Possible value are 0 to 0xFFFFFFFF. The 
#				default is 0. This argument only applies to ingress 
#				(incoming) tunnels.
#
#	-session_attr_ra_include_all
#				Set all the affinity bits in the session attribute object. 
#				Possible value are 0 to 0xFFFFFFFF. The default is 0. This 
#				argument only applies to ingress (incoming) tunnels.
#				 
#
#	-session_attr_ra_include_any
#				Sets the affinity bits in the session attribute object that
#				are included. Possible value are 0 to 0xFFFFFFFF. The 
#				default is 0. This argument only applies to ingress 
#				(incoming) tunnels.
#
#	-session_attr_resource_affinities
#				Specifies whether to enable resource affinities. Possible
#				values are 0 (disable) and 1 (enable). The default is 0. 
#				This argument only applies to ingress (incoming) tunnels.#
#
#	-session_attr_se_style
#				Indicates whether the tunnel ingress node will reroute
#				this tunnel without tearing it down. A tunnel egress node
#				should use the shared explicit (SE) reservation style when
#				responding with a Resv message. Possible values are 0
#				(disable) and 1 (enable). The default is 0. SE style
#				reservations allow an existing LSP tunnel to share bandwidth
#				with itself. This argument only applies to ingress 
#				(incoming) tunnels.
#
#	-session_attr_setup_priority
#				Specifies the priority for taking resources. Possible values
#				range from 0 to 7, with 0 representing the highest priority.
#				The default is 7. RSVP-TE uses the setup priority to
#				determine whether this session can preempt another session.
#				Note: The setup priority should never be higher than the
#				holding priority that you specified with the 
#				-session_attr_hold_priority argument) for a given session.
#
#	-tunnel_id_start
#				Specifies the starting tunnel ID used in the RSVP session.
#				Possible values range from 0 to 65535. The default is 1.
#
#	-tunnel_id_step
#				Specifies the increment to use to define the tunnel ID for
#				multiple tunnels. If 0, all the tunnels belong to the same
#				RSVP session. Possible values range from 0 to <max_int>. The
#				default is 1.
#
#	-tunnel_pool_handle
#				Specifies the RSVP handle(s) to use when mode is set to
#				modify or delete. This argument is not valid for create
#				mode. Instead, use -handle.
#
# Return Values: The function returns a keyed list using the following keys:
#			(with corresponding data):
#
#	tunnel_handles		A list of handles that identify the tunnels created by
#					the sth::emulation_rsvp_tunnel_config function.
#
#	status			Success (1) or failure (0) of the operation.
#
#	log				An error message (if the operation failed).
#
# Description: The sth::emulation_rsvp_tunnel_config function creates, modifies,
#	or deletes an LSP tunnel. Use the -mode argument to specify the action to
#	perform. (See the -mode argument description for information about the
#	actions.)
#
#	When you create an RSVP tunnel, use the -handle argument. When you modify
#	or delete a tunnel, use the -tunnel_pool_handle argument to specify which
#	tunnel to modify or delete.
#
#	In addition to specifying the port, you must also provide one or more of
#	the following pieces of information when you create an ingress tunnel:
#
#		- The source IP address for the tunnel's ingress (start) point (the 
#		  -ingress_ip_addr argument) 
#
#		- The destination IP address for the for the tunnel's egress (end) 
#		  point (the -egress_ip_addr argument)
#
#		- The port handle (the -handle argument) from which to add or remove 
#		  tunnels
#
#	During the test, use the sth::emulation_rsvp_tunnel_control function to
#	control individual LSP tunnels.
#
# Examples: The following example creates a tunnel for the specified RSVP
#	session on the reserved port:
#
# ::sth::emulation_rsvp_tunnel_config -mode create \
#			-egress_ip_addr 90.0.0.4 \
#			-handle  $rsvp_handle(rsvp1) \
#			-ingress_ip_addr 90.0.0.3 \
#			-sender_tspec_max_pkt_size 4096 \
#			-sender_tspec_min_policed_size 64 \
#			-sender_tspec_peak_data_rate 512000 \
#			-sender_tspec_token_bkt_rate 128000 \
#			-sender_tspec_token_bkt_size 256000 \
#			-session_attr 1 \
#			-session_attr_bw_protect 1 \
#			-session_attr_hold_priority 0 \
#			-session_attr_label_record 1 \
#			-session_attr_local_protect 1 \
#			-session_attr_name Tunnel1 \
#			-session_attr_node_protect 1 \
#			-session_attr_ra_exclude_any 0 \
#			-session_attr_ra_include_all 0 \
#			-session_attr_ra_include_any 0 \
#			-session_attr_resource_affinities 0 \
#			-session_attr_se_style 0 \
#			-session_attr_setup_priority 7 \
#			-tunnel_id_start 100 \
#			-tunnel_id_step 5
#
# Sample Input: See Examples.
#
# Sample Output: 
#
# Notes: None
#
# End of Procedure Header


proc ::sth::emulation_rsvp_tunnel_config { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_tunnel_config $args	

    
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
    

    set _hltCmdName "emulation_rsvp_tunnel_config"
    
    set myNameSpace "::sth::Rsvp::"

    
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
   
    catch {unset ::sth::Rsvp::switchToValue}
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue ::sth::Rsvp::sortedSwitchPriorityList} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}
	set modeValue $::sth::Rsvp::switchToValue(mode)
	
    switch -exact $modeValue {
    	    create {
                set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            modify {
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
	} else {
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::processError returnKeyedList "Error applying RSVP tunnel configuration: $msg"
            return $returnKeyedList 
        }
		::sth::sthCore::log stccall \
            {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}		   		
		if {!$cmdStatus} {
			return $returnKeyedList
		} else {
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
	}
}

proc ::sth::emulation_rsvpte_tunnel_control { args } {
    ::sth::sthCore::Tracker ::emulation_rsvpte_tunnel_control $args
    
    
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
    

    set _hltCmdName "emulation_rsvpte_tunnel_control"
    
    set myNameSpace "::sth::Rsvp::"


    
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""

    catch {unset ::sth::Rsvp::switchToValue}
    
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue slist} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}
	set modeValue $::sth::Rsvp::switchToValue(action)
	
    switch -exact $modeValue {
            connect {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
            }
            tear_down_outbound {
	            set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for action($modeValue): $cmd "
            }
            tear_down_inbound {
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
		    ::sth::sthCore::processError returnKeyedList "Error applying RSVP configuration in control: $msg"
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



proc ::sth::emulation_rsvp_custom_object_config { args } {
    ::sth::sthCore::Tracker ::emulation_rsvp_custom_object_config $args	
 
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable _SHA_DEBUG
    variable ::sth::Rsvp::rsvpTable
	variable ::sth::Rsvp::sortedSwitchPriorityList
    

    set _hltCmdName "emulation_rsvp_custom_object_config"
    
    set myNameSpace "::sth::Rsvp::"

    
    set underScore "_"
    
    ::sth::sthCore::log hltcall {Excuting command: {$_hltCmdName $args}}
    
    set returnKeyedList ""
   
    catch {unset ::sth::Rsvp::switchToValue}
	if {[catch {::sth::sthCore::commandInit ::sth::Rsvp::rsvpTable $args $myNameSpace $_hltCmdName ::sth::Rsvp::switchToValue ::sth::Rsvp::sortedSwitchPriorityList} eMsg]} {  
		::sth::sthCore::processError returnKeyedList $eMsg {}
		return $returnKeyedList  
	}
	set modeValue $::sth::Rsvp::switchToValue(mode)
	
    switch -exact $modeValue {
    	    create {
                set cmdStatus 0
        	    set cmd "$myNameSpace$_hltCmdName\_$modeValue returnKeyedList cmdStatus"
                ::sth::sthCore::log hltcall "CMD which will process for mode($modeValue): $cmd "
            }
            modify {
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
	} else {
        if {[catch {::sth::sthCore::doStcApply} msg]} {
            ::sth::sthCore::processError returnKeyedList "Error applying in emulation_rsvp_custom_object_config : $msg"
            return $returnKeyedList 
        }
		::sth::sthCore::log stccall \
            {SUBCOMMAND RESULT for command: $_hltCmdName based on switch:mode, Value:$modeValue. ||$returnKeyedList||}		   		
		if {!$cmdStatus} {
			return $returnKeyedList
		} else {
			keylset returnKeyedList status $::sth::sthCore::SUCCESS
			return $returnKeyedList
		}
	}
}


