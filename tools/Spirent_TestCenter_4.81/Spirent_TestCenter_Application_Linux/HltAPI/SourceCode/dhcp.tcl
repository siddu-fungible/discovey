# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

#source sthCore.tcl
#source dhcpTable.tcl
#source parse_dashed_args.tcl    
#source dhcpFunctions.tcl
#source sthutils.tcl

#::sth::sthCore::sthCoreInit
#set ::sth::sthCore::enableInternallog true

namespace eval ::sth::Dhcp:: {
    variable userArgsArray
}

##Procedure Header
#
# Name:
#    sth::emulation_dhcp_config
#
# Purpose:
#    Creates, modifies, or resets Dynamic Host Configuration Protocol (DHCP)
#    clients for the specified Spirent HLTAPI port or handle.
#
#    DHCP uses a client-server model, in which DHCP servers provide network
#    addresses and configuration parameters to DHCP clients. You use Spirent
#    TestCenter to emulate a network containing DHCP clients.
#
# Synopsis:
#    sth::emulation_dhcp_config
#         { [-mode create -port_handle <Port(device.port)> |
#            -mode {modify|reset} -handle <dhcp_port>} ]
#         }
#         [-lease_time <10-2147483647 seconds> ]
#         [-max_dhcp_msg_size <264-1500 bytes> ]
#         [-msg_timeout <1000-99999000 milliseconds>]
#         [-outstanding_sessions_count <1-2048>]
#         [-release_rate <1-2000 seconds>]
#         [-request_rate <1-2000 seconds>]
#         [-retry_count <0-32>]
#
# Arguments:
#
#    -handle        
#                   Specifies the handle of the port upon which DHCP emulation 
#                   is configured. Use -handle when -mode is set to either 
#                   "modify" or "reset". This argument is required only for 
#                   modify and reset modes. The handle is returned by the
#                   sth::emulation_dhcp_config function.
#
#    -lease_time    
#                   Specifies a finite time period, in seconds, for use of the
#                   IP address offered by the DHCP server. The actual lease
#                   length that the DHCP sessions will receive depends on the
#                   lease time configured for the DUT. For example, if the 
#                   Cisco DUT sends a lease time of one day (its default), then 
#                   the IP address will only be good for one day, regardless of 
#                   the value set by Spirent HLTAPI. Possible values range 
#                   from 10 to 2147483647. The default is 86400.
#
#    -max_dhcp_msg_size
#                   Sets the maximum size of the DHCP message. Spirent
#                   TestCenter uses this value to negotiate the DHCP message
#                   size, in bytes. Possible values range from 264 to 1500. The
#                   default is 576.
#
#    -mode          
#                   Specifies the action to perform. Possible values are create,
#                   modify, and reset. This argument is required. The modes are
#                   described below:
#
#                   create - Starts emulating DHCP clients on the port specified
#                        by the -port_handle argument.
#
#                   modify - Changes the configuration parameters for the DHCP
#                        clients identified by the -handle argument.
#
#                   reset - Stops the DHCP emulation locally without attempting
#                        to clear the bound addresses from the DHCP server. In
#                        addition, all DHCP group sessions information on the
#                        port is cleared and the connection is restarted.
#                        Because -mode reset deletes the handle, do not use the
#                        handle following this action.
#
#                        IMPORTANT:
#                        Before using "sth::emulation_dhcp_config -mode reset",
#                        you must first delete all traffic streams with the
#                        "sth::traffic_config -mode reset" command. Traffic
#                        streams must be reset before DHCP can be reset.
#
#    -msg_timeout
#                   Sets the maximum time, in milliseconds, to wait for receipt
#                   of an offer or ack message after sending a corresponding
#                   discover or request message. Possible values range from 1000
#                   to 99999000. However, because Spirent HLTAPI accepts
#                   seconds, the timeout value must be evenly divisible by 1000.
#                   The default is 15000.
#
#                   Note: The -msg_timeout argument controls the determination
#                   of when a discover or request message is counted as
#                   unacknowledged.
#
#    -outstanding_sessions_count
#                   Specifies the maximum number of outstanding sessions that
#                   Spirent HLTAPI can resolve at one time. Possible values
#                   are 1 to 2048. The default is 100.
#
#    -port_handle   
#                   The handle of the port on which to configure DHCP emulation.
#                   The port handle is returned by the sth::interface_config
#                   function. This argument is required for create mode (see
#                   -mode).
#
#    -release_rate  
#                   The number of DHCP sessions that are released per second.
#                   This value applies to all sessions on the port. Possible
#                   values range from 1 to 2000. The default is 500.
#
#                   Note: DHCPv4 release messages are unacknowledged; therefore,
#                   the system may overwhelm the DHCP server.
#
#    -request_rate  
#                   The number of requests per second for DHCP client leases or
#                   lease renewals. This value applies to all sessions on the
#                   port. Possible values range from 1 to 2000. The default is
#                   500.
#
#    -retry_count   
#                   The maximum number of times that discover or request
#                   messages will be re-sent. This value limits the number of
#                   additional transmissions of either a discover or request
#                   message when no acknowledgement is received. Possible values
#                   range from 0 to 65535. The default is 0.
#
#                   Note: A session is considered failed once the -retry_count
#                   argument is exceeded.
#
# Return Values:
#    The sth::emulation_dhcp_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handles   Identifies the handle of the port on which the DHCP emulation
#              was configured by the sth::emulation_dhcp_config function. If you
#              reset the port (-mode reset), it returns a new handle.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_dhcp_config function creates, modifies,
#    or resets an emulated DHCP client. Use the -mode argument to specify the
#    action to perform. (See the -mode argument description for information
#    about the actions.)
#
#    When you create a DHCP client, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated DHCP session will
#    use for DHCP communication. (The port handle value is contained in the
#    keyed list returned by the  sth::connect function.)
#
#    Use the -mode create function to define the characteristics of a DHCP
#    session. You can use a single session to emulate multiple DHCP clients.
#
#    In addition to specifying the port handle (-port_handle), you must also
#    provide one or more of the following arguments when you create a DHCP
#    session, or use their default values:
#
#    -lease_time (the number of seconds you can use the IP address)
#
#    When you write an HLT API that uses Spirent HLTAPI Automation software
#    for DHCP tests, you create a test configuration to emulate DHCP clients.
#    During a DHCP test, Spirent HLTAPI sends DHCP messages to, and receives
#    messages from the DUT (configured as a DHCP server). In this context, you
#    can create test configurations in which Spirent HLTAPI DHCP clients act
#    as independent network hosts, communicating directly with a DHCP server.
#    Spirent HLTAPI DHCP clients are part of a VLAN. Spirent HLTAPI DHCP
#    clients communicate with a DHCP server through a Spirent HLTAPI
#    emulation of a relay server (agent).
#
#    NOTES:
#         1)   In version 1.24, -handle was passed as a string value.
#              In version 1.30, -handle was passed as an integer.  In version
#              2.x, -handle is passed as an alphanumeric value.
#
#    For information about the DHCP protocol, see RFC 2131, "Dynamic Host
#    Configuration Protocol".
#
#
# Examples:
#    The following example creates a DHCP emulation port:
#
#    sth::emulation_dhcp_config -port_handle $hPort($device.$port)
#         -mode create \
#         -lease_time 10400
#
#
# Sample output for example shown above:
#    {handles dhcpv4portconfig1} {status 1}
#
# Notes:
#    When first configuring DHCP emulation on a port, you must specify
#    "-mode create" and initialize the port handle argument before calling the
#    sth::emulation_dhcp_config function.
#
# End of Procedure Header


proc ::sth::emulation_dhcp_config { args } {
    
    ::sth::sthCore::Tracker "::sth::emulation_dhcp_config" $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    variable ::sth::Dhcp::dhcpBlockInputArgsList
    variable ::sth::Dhcp::dhcpBlockInputArgs
    variable ::sth::Dhcp::processFlag
    
    variable sortedSwitchPriorityList
    variable ::sth::Dhcp::userArgsArray
    array unset ::sth::Dhcp::userArgsArray
    array set ::sth::Dhcp::userArgsArray {}
    
    set _hltCmdName "emulation_dhcp_config"
    
    set underScore "_"
    
    set returnKeyedList ""

    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6::emulation_dhcpv6_config returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: FAILED. $err" {}
            }
            return $returnKeyedList
        }
    }

    if {[catch {::sth::sthCore::commandInit ::sth::Dhcp::dhcpTable $args ::sth::Dhcp:: $_hltCmdName ::sth::Dhcp::userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: commandInit FAILED. $err" {}
        return $returnKeyedList  
    }
    
    set retVal [catch {
	#DHCP 3.00 enhancement 
	#store the arguments table of DHCP session(Dhcpv4BlockConfig or Dhcpv4MsgOption)
	set keylist {stcobj stcattr type priority default range supported dependency mandatory procfunc mode}
	foreach switchName $sortedSwitchPriorityList {
		set switchName [lindex $switchName 1]
		set objType [::sth::sthCore::getswitchprop ::sth::Dhcp:: emulation_dhcp_config $switchName stcobj]
		if {$objType == "Dhcpv4BlockConfig" || $objType == "Dhcpv4MsgOption"} {
			set arglist [array names dhcpBlockInputArgs]
			if {[lsearch -exact $arglist $switchName] < 0} {
				foreach key $keylist {
					set type [::sth::sthCore::getswitchprop ::sth::Dhcp:: emulation_dhcp_config $switchName $key]
					set dhcpBlockInputArgsList [::sth::sthCore::updateReturnInfo $dhcpBlockInputArgsList "$switchName.$key" $type]
				} 
			}
		   
			set dhcpBlockInputArgs($switchName) $::sth::Dhcp::userArgsArray($switchName)
			set processFlag($switchName) false
		}
	}
	#end 
	
	set modeValue $::sth::Dhcp::userArgsArray(mode)

	switch -exact -- $modeValue \
            enable -\
            create {
                set cmdStatus 0
                set modeValue "create"
                set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName create mode: $cmd" {}
                    return $returnKeyedList
                } 
            }\
            modify {
                set cmdStatus 0
                set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName modify mode: $cmd" {}
                    return $returnKeyedList
                }
            }\
            reset {
                set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName reset mode: $cmd" {}
                    return $returnKeyedList
                }               
            }\
            SHA_UNKNWN_SWITCH {
                ::sth::sthCore::processError returnKeyedList "The switch -mode is a mandatory switch"
                return $returnKeyedList                   
            }\
            SHA_NO_USER_INPUT {
                ::sth::sthCore::processError returnKeyedList "The value {} is not valid for the switch -mode"
                return $returnKeyedList                
            }\
            default {
                #Unknown value for switch Mode.
                ::sth::sthCore::processError returnKeyedList "The value $modeValue is not valid for the switch -mode"
                return $returnKeyedList 
            }
    } returnedString]

    if {$retVal} {
		if {$returnedString ne ""} {
			::sth::sthCore::processError returnKeyedList $returnedString {}
		}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_dhcp_group_config
#
# Purpose:
#    Configures or modifies a specified number of DHCP client sessions which
#    belong to a subscriber group with specific Layer 2 network settings.  Once
#    the subscriber group has been configured, a handle is created, which can be
#    used to modify the parameters or reset the sessions for the subscriber
#    group or to control the binding, renewal, and release of the DHCP sessions.
#
# Synopsis:
#    sth::emulation_dhcp_group_config
#         -mode {create|modify|reset}
#         -handle <dhcpGroup_handle>
#         -num_sessions <1-65536>
#         [-host_name <host_name> ]
#    {
#         [{-encap ethernet_ii  |
#         -encap ethernet_ii_vlan
#            [-vlan_id <1-4095> ]
#            [-vlan_id_step <1-4095>  ]
#            [-vlan_id_count <1-4096> ]
#         ]  |
#         [-encap ethernet_ii_qinq
#            [-vlan_id_outer <0-4095>]
#            [-vlan_id_outer_step <0-4095> ]
#            [-vlan_id_outer_count <1-4096> ]
#            [-qinq_incr_mode {inner|outer}]
#         ]
#         [-mac_addr <aa.bb.cc.dd.ee.ff>]
#         [-mac_addr_step <aa.bb.cc.dd.ee.ff>]
#    }
#         [-opt_list <list of numbers> ]
#         [-relay_agent_enable {1|0} ]
#         [-relay_circuit_id <circuit ID> ]
#         [-relay_circuit_id_enable {1|0} ]
#         [-relay_local_ip <a.b.c.d.> ]
#         [-relay_mac_dst <aa:bb:cc:dd:ee:ff>]
#         [-relay_remote_id <remote ID> ]
#         [-relay_remote_id_enable {1|0} ]
#         [-relay_server_ip <a.b.c.d.> ]
#
# Arguments:
#
#    -encap         
#                   Specifies the type of Layer2 encapsulation to use to define
#                   source and destination MAC addresses for a stream. This
#                   argument is required. Possible values are:
#
#                   ethernet_ii      - Ethernet II
#                   ethernet_ii_vlan - Ethernet II with a single vlan tag
#                   ethernet_ii_qinq - Ethernet II with two vlan tags
#
#                   Ethernet_ii_vlan supports VLAN tagging on Ethernet networks;
#                   ethernet_ii does not. If you use the -vlan_* arguments to
#                   define a VLAN interface, you must set the L2 encapsulation
#                   type to ethernet_ii_vlan.
#
#                   Note: If you modify the encapsulation value from encap
#                   ethernet_ii or ethernet_ii_vlan to ethernet_ii_qinq or
#                   vice versa (using "-mode modify"), you must resend all
#                   parameters. Otherwise, the parameters use their default
#                   values.
#
#    -handle        
#                   Identifies the port and group upon which emulation is
#                   configured. This argument is required. When -mode is
#                   "modify" or "reset", this parameter also specifies the DHCP
#                   group number. For "-mode create", the handle is returned by
#                   the sth::emulation_dhcp_config function. For "-mode modify"
#                   or "-mode reset", the group handle is returned by the
#                   sth::emulation_dhcp_group_config function.
#
#    -host_name     
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the name of the host. You can use the following
#                   wildcards: @p = port, @b = session block, @s = session. The
#                   default is client_ @p-@b-@s.
#
#    -mac_addr      
#                   Specifies the first MAC address to use when emulating
#                   multiple clients. The default is 00:10:01:00:00:01.
#
#    -mac_addr_step 
#                   Specifies the increment to use to generate additional MAC 
#                   addresses for multiple clients. Possible values range from
#                   00.00.00.00.00.01 to 00.00.7f.ff.ff.ff. The default is
#                   00.00.00.00.00.01.
#
#    -mode          
#                   Specifies the action to perform. Possible values are create,
#                   modify, and reset. There is no default; you must specify a
#                   mode. The modes are described below:
#
#                   create - Starts emulation on the port specified with
#                        -handle.
#
#                   modify - Changes the configuration identified by the -handle
#                        argument by applying the parameters specified in
#                        subsequent arguments.
#
#                   reset - Stops the DHCP emulation locally without attempting
#                        to clear the bound addresses from the DHCP server. In
#                        addition, all DHCP group sessions information on the
#                        port is cleared.
#
#                   IMPORTANT:
#                   Before using "sth::emulation_dhcp_group_config -mode reset",
#                   you must first delete all traffic streams with the
#                   "sth::traffic_config -mode reset" command. Traffic
#                   streams must be reset before DHCP can be reset.
#
#    -num_sessions  
#                   Specifies the number of DHCP clients to emulate. Possible
#                   values range from 1 to 32767. The default is 4096.
#
#                   Note: For Outrigger2 platforms, the maximum value is 131070.
#                   For non-Outrigger2 platforms, the maximum is 4096.
#
#    -opt_list      
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Set up the Option 55 values for the DHCP request messages on
#                   each session block. You can select from the following list
#                   of options::
#
#                   Subnet Mask Option [1]
#                   Routers Option [3]
#                   Domain Name Servers Option [6]
#                   Domain Name Option [15]
#                   Static Routes Option [33]
#                   NetBIOS Name Servers Option [44]
#                   NetBIOS Node Type Option [46]
#                   NetBIOS Scope Option [47]
#                   IP Address Lease Time Option [51]
#                   Server Identifier Option [54]
#                   Renewal Time (T1) Option [58]
#                   Rebinding Time (T2) Option [59]
#
#                   The default is 1 6 15 33 44.
#
#                   Example usage:
#                   sth::emulation_dhcp_group_config -mode create \
#                                           -handle $dhcpport1 \
#                                           -encap ethernet_ii \
#                                           -num_sessions 30 \
#                                           -mac_addr 00.00.03.00.00.02 \
#                                           -mac_addr_step 00.00.00.00.00.02 \
#                                           -opt_list {1 6 15}
#
#                   Alternatively, you can use the hexadecimal input style used
#                   in version 1.30 but must prefix the input with "0x" or "0X"
#                   to indicate hexadecimal style. The following example uses
#                   the HLTAPI version 1.30 input style and is equivalent to the
#                   above example:
#
#                   sth::emulation_dhcp_group_config -mode create \
#                                           -handle $dhcpport1 \
#                                           -encap ethernet_ii \
#                                           -num_sessions 30 \
#                                           -mac_addr 00.00.03.00.00.02 \
#                                           -mac_addr_step 00.00.00.00.00.02 \
#                                           -opt_list 0x01060f
#
#    -qinq_incr_mode
#                   Specifies the increment mode for ethernet_ii_qinq
#                   encapsulation. Possible values are inner and outer.
#                   The default is inner.
#
#                   Note: Applies only to QnQ Ethernet interfaces. For the
#                   "inner" mode, when the number of sessions is greater than
#                   the inner VLAN count multiplied by the outer VLAN count, the
#                   inner VLAN ID is incremented first until the specified
#                   number of inner VLANs is exhausted; then, the outer vlan id
#                   is incremented. This continues in round-robin fashion until
#                   the number of sessions specified in -num_sessions.
#
#                   For the "outer" mode, when the number of sessions is greater
#                   than the inner VLAN count multiplied by the outer VLAN count
#                   outer VLAN count, the outer VLAN ID is incremented first
#                   until the specified number of outer VLANs is exhausted; then
#                   it increments the inner VLAN ID. This continues in round-
#                   robin fashion until the number of sessions specified
#                   in -num_sessions.
#
#    -relay_agent_enable
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables the use of a relay agent. Possible values are 1
#                   (true) and 0 (false). If the value is 1, all client bind
#                   requests are sent as if they were passing through a relay
#                   agent. If the value is set to 0, a relay agent is not used.
#                   The default is 0 (false).
#
#    -relay_circuit_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies what is in the Circuit ID field of the message
#                   sent by the relay agent. You can use the following
#                   wildcards: @p = port, @b = session block, @s = session
#                   You must set the -relay_circuit_id_enable argument to 1
#                   (true) for this argument to take effect. The default is
#                   circuitid_ @p.
#
#    -relay_circuit_id_enable
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enable the circuit ID sub-option in the DHCP messages that
#                   are sent from the emulated relay agent. Possible values are
#                   1 (true) and 0 (false). If the value is 1, the circuit ID
#                   sub-option is included. If the value is set to 0, the
#                   circuit ID sub-option is not included. The default is 0
#                   (false).
#
#    -relay_local_ip
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The source IP address of the relay agent message, and the
#                   "giaddr" field in the DHCP message. The default is 0.0.0.0.
#
#    -relay_mac_dst 
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The destination MAC field of the relay agent message. The
#                   default is FF-FF-FF-FF-FF-FF.
#
#    -relay_remote_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specify what is in the Remote ID field of the message
#                   sent by the relay agent. You can use the following
#                   wildcards: @p = port, @b = session block, @s = session
#                   The -relay_remote_id_enable argument must be set to 1 (true)
#                   for this to take effect. The default is remoteid_ @p-@b-@s.
#
#    -relay_remote_id_enable
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enable the remote ID sub-option in the DHCP messages that
#                   are sent from the emulated relay agent. The remote ID sub-
#                   option is described in RFC 3046. Possible values are 1
#                   (true) and 0 (false). If the value is 1, the remote ID sub-
#                   option is included. If the value is set to 0, the remote ID
#                   sub-option is not included. The default is 0 (false).
#
#    -relay_server_ip
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The destination IP address for the relay agent message. The
#                   default is 0.0.0.0.
#
#    -vlan_id       
#                   The starting VLAN ID to use when generating DHCP clients for
#                   ethernet_ii_vlan. Possible values range from 1 to 4095. This
#                   argument is required for ethernet_ii_vlan.
#
#    -vlan_id_count 
#                   The number of VLAN IDs to use when generating DHCP clients.
#                   Spirent HLTAPI assigns VLAN membership in round-robin
#                   fashion. The VLAN count must divide evenly into the number
#                   of sessions. The -vlan_id_count cannot be greater than the
#                   session count (-num_session). Possible values range from 1
#                   to 4096. The default is 1.
#
#    -vlan_id_outer
#                   Starting outer VLAN ID, applies to DHCP w/Stacked VLAN
#                   only. Possible values range from 0 to 4095. The default
#                   is 1.
#
#    -vlan_id_outer_step
#                   The value that Spirent HLTAPI uses to increment the
#                   outer VLAN ID. Possible step values range from 0 to 4095.
#                   The default is 1.
#
#    -vlan_id_outer_count
#                   The number of outer VLAN IDs to use when generating DHCP
#                   clients. Spirent HLTAPI assigns VLAN membership in
#                   round-robin fashion. The VLAN count must divide evenly into
#                   the number of sessions. The VLAN count cannot be greater
#                   than the session count. Possible values range from 1 to
#                   4096. The default is 1.
#
#    -vlan_id_step  
#                   The value that Spirent HLTAPI uses to increment the VLAN
#                   ID for ethernet_ii_vlan. Possible step values range
#                   from 1 to 4095. The default is 1.
#
# Return Values:
#    The sth::emulation_dhcp_group_config function returns a keyed
#    list using the following keys (with corresponding data):
#
#    handles   Identifies the handle of the group configured or modified by the
#              sth::emulation_dhcp_group_config function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
#
# Description:
#    The sth::emulation_dhcp_group_config function configures or
#    modifies a group of DHCP subscribers where each group share a
#    set of common characteristics. Use the -mode argument to specify
#    the action to perform. (See the -mode argument description for information
#    about the actions.)
#
#    Before using this function, you must specify "-mode create" when
#    configuring DHCP emulation on a port and initialize the port handle
#    argument (using the sth::emulation_dhcp_config function).
#
#    You can call this function multiple times to create multiple groups of
#    subscribers on a port with characteristics different from other groups or
#    for independent control purposes. This function enables you to configure a
#    specified number of DHCP client sessions which belong to a subscriber group
#    with specific Layer 2 network settings.
#
#    Once the subscriber group has been configured, a handle is created, which
#    can be used to modify the parameters or reset the sessions for the
#    subscriber group or to control the binding, renewal, and release of the
#    DHCP sessions.
#
#    In addition to specifying the handle (-handle), you must also provide the
#    following arguments:
#
#    -mode (create, modify, or reset)
#
#    -num_sessions (the number of DHCP clients to emulate)
#
#    -encap (type of Ethernet encapsulation)
#
#    -mac_addr      (starting value for the MAC address)
#
#    -mac_addr_step (increment used to generate additional MAC addresses for
#         multiple clients)
#
#    For information about the protocol, see RFC 2131, "Dynamic Host
#    Configuration Protocol".
#
# Examples:
#    The following example configures a group of DHCP subscribers on a
#    port:
#
#     sth::emulation_dhcp_group_config -handle $hDhcpGroup($port) \
#           -mode create -encap ethernet_ii_vlan \
#           -num_sessions 5 -mac_addr 00.10.95.11.12 -mac_addr_step \
#                 00.00.00.00.00.01 \
#           -vlan_id 10 -vlan_id_step 1 -vlan_id_count 1
#
# Sample output for example shown above:
#     {handles dhcpv4blockconfig1} {status 1}
#
# Notes:
#     None
#
# End of Procedure Header


proc ::sth::emulation_dhcp_group_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_dhcp_group_config" $args
    
    variable sortedSwitchPriorityList
    variable ::sth::Dhcp::userArgsArray
    array unset ::sth::Dhcp::userArgsArray
    array set ::sth::Dhcp::userArgsArray {}
    
    variable ::sth::Dhcp::dhcpBlockInputArgsList
    variable ::sth::Dhcp::dhcpBlockInputArgs
    variable ::sth::Dhcp::processFlag
    
    set _hltCmdName "emulation_dhcp_group_config"

    set underScore "_"
    
    set returnKeyedList ""
   
    if {[set idx [lsearch $args -dhcp_range_ip_type]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6::emulation_dhcpv6_group_config returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: FAILED. $err" {}
            }
            return $returnKeyedList
        }
    }
   
   
    if {[catch {::sth::sthCore::commandInit ::sth::Dhcp::dhcpTable $args ::sth::Dhcp:: $_hltCmdName ::sth::Dhcp::userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList $err
        return $returnKeyedList
    }
    
    set modeValue $::sth::Dhcp::userArgsArray(mode)
    
    #DHCP 3.00 enhancement
    #map the arguments list stored in dhcpBlockInputArgsList
    set retVal [catch {
                array unset dhcpBlockInputArgsOld
                array set dhcpBlockInputArgsOld {}
                array set dhcpBlockInputArgsOld [array get dhcpBlockInputArgs]
		set keylist {stcobj stcattr type priority default range supported dependency mandatory procfunc mode}
		if {[array size dhcpBlockInputArgs] != 0} {
			set argslist [array names dhcpBlockInputArgs]
			foreach temp $argslist {
				set value $dhcpBlockInputArgs($temp)
				foreach key $keylist {
					keylget dhcpBlockInputArgsList $temp.$key keyName
					set name "::sth::Dhcp::$_hltCmdName\_$key"
					set ${name}($temp) $keyName
				}
				
				set pri [::sth::sthCore::getswitchprop ::sth::Dhcp:: emulation_dhcp_config $temp priority]
                                if {[catch {keylget sortedSwitchPriorityList $pri} err]} {
                                    #if not configured in the dhcp_group_config, then add it to the userArgsArray and the sortedSwitchPriorityList
                                    set ::sth::Dhcp::userArgsArray($temp) $value
                                    keylset sortedSwitchPriorityList $pri $temp
                                }
				
				set processFlag($temp) true
			}
			if {[info exists ::sth::Dhcp::userArgsArray(relay_agent_flag)]} {
				set ::sth::Dhcp::relay_agent_flag $::sth::Dhcp::userArgsArray(relay_agent_flag)
			} 
		}
                foreach switchName $sortedSwitchPriorityList {
                    set switchName [lindex $switchName 1]
                    set objType [::sth::sthCore::getswitchprop ::sth::Dhcp:: emulation_dhcp_group_config $switchName stcobj]
                    if {$objType == "Dhcpv4BlockConfig" || $objType == "Dhcpv4MsgOption"} {
                        set dhcpBlockInputArgs($switchName) $::sth::Dhcp::userArgsArray($switchName)
                        set processFlag($switchName) true
                    }
                }
		#end

		switch -exact -- $modeValue \
				enable -\
				create {
					set modeValue "create"
					set cmdStatus 0
					set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
					set procResult [eval $cmd]
					if {!$cmdStatus} {
						::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName create mode: $cmd" {}
						return $returnKeyedList
					} 
				}\
				modify {
					set cmdStatus 0
					set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
					set procResult [eval $cmd]
					if {!$cmdStatus} {
						::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName modify mode: $cmd" {}
						return $returnKeyedList
					}
				}\
				reset {
					set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
					set procResult [eval $cmd]
					if {!$cmdStatus} {
						::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName reset mode: $cmd" {}
						return $returnKeyedList
					}               
				}\
				SHA_UNKNWN_SWITCH {
					::sth::sthCore::processError returnKeyedList "The switch -mode is a mandatory switch"
					return $returnKeyedList                   
				}\
				SHA_NO_USER_INPUT {
					::sth::sthCore::processError returnKeyedList "The value {} is not valid for the switch -mode"
					return $returnKeyedList                
				}\
				default {
					#Unknown value for switch Mode.
					::sth::sthCore::processError returnKeyedList "The value $modeValue is not valid for the switch -mode"
					return $returnKeyedList 
				}
            array unset  dhcpBlockInputArgs
            array set dhcpBlockInputArgs [array get dhcpBlockInputArgsOld]
        } returnedString]

    if {$retVal} {
		if {$returnedString ne ""} {
			::sth::sthCore::processError returnKeyedList $returnedString {}
		}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_dhcp_control
#
# Purpose:
#    Start, stop, or restart the DHCP subscriber group activity on the
#    specified port.
#
# Synopsis:
#    sth::emulation_dhcp_control -port_handle <port_handle>
#         -action {bind|release|renew}
#         [-handle <DHCP_group_handles>]
#
# Arguments:
#
#    -action        
#                   Specifies the action to perform on the port specified by the
#                   -port_handle argument. Possible values are bind, release,
#                   and renew. You must specify one of these values. The modes
#                   are described below:
#
#                   bind - Starts the Discover/Request message exchange between
#                        the emulated requesting router(s) and the delegating
#                        router(s) that is necessary to establish client
#                        bindings.
#
#                   release - Terminates bindings for all currently bound
#                        subscribers.
#
#                   renew - Renews the lease for all currently bound
#                        subscribers.
#
#                   rebind - Rebinds the DHCP Clients with DHCP Server.
#
#                   abort - Aborts the DHCP Client bindings and reset
#                           the DHCP Client state.
#
#    -handle        
#                   Identifies the groups or list of groups to bind, release, or
#                   renew (see Examples section). This value is returned from
#                   the sth::emulation_dhcp_group_config function. If you do not
#                   specify a group, the specified action is applied to all
#                   groups configured on the port specified by -port_handle.
#                   This value appears in the keyed list returned by the
#                   sth::emulation_dhcp_group_config function.
#
#    -port_handle   
#                   Identifies the handle of the port on which DHCP emulation
#                   has been configured. This value is returned by the
#                   sth::emulation_dhcp_config function.
#
# Return Values:
#     The function returns a keyed list using the following keys (with
#     corresponding data):
#
#     status     Success (1) or failure (0) of the operation.
#     log        An error message (if the operation failed).
#
# Description:
#    The sth::emulation_dhcp_control function starts or stops the message
#    exchange between the emulated requesting router(s) and the delegating
#    router(s). You use this function to bind, release, or renew subscribers.
#    When you call the sth::emulation_dhcp_control function, you specify a
#    port handle. Spirent HLTAPI applies the specified action to all of the
#    emulated DHCP clients associated with the specified port.
#
#    The basic DHCP operation is a co-operative exchange of messages between
#    client and server. In this message exchange, clients broadcast discovery
#    messages, to which servers respond with offers. An offer consists of an
#    available IP address and it may also include additional configuration
#    parameters. The client then accepts an offer. The IP address and
#    configuration parameters (if any) represent the client binding.
#
#    NOTE:In version 1.24, -handle was passed as a string value.
#    In version 1.30, -handle was passed as an integer. In
#    version 2.x, -handle is passed as an alphanumeric value.
#
# Examples:
#
#    The following example binds two DHCP groups with either a single command
#    using the DHCP port handle or using the list feature.
#
#    # Configure DHCP port
#    set rL [sth::emulation_dhcp_config -mode create -port_handle $p0]
#    keylget rL handles dhcpport1
#
#    # Configure two DHCP groups
#    set rL [sth::emulation_dhcp_group_config -mode create \
#                                -handle $dhcpport1 \
#                                -encap ethernet_ii_vlan \
#                                -num_sessions 30 \
#                                -vlan_id 10 \
#                                -vlan_id_count 30 \
#
#    ]
#
#    keylget rL handles dhcpHandles
#
#    set rL [sth::emulation_dhcp_group_config -mode create \
#                                -handle $dhcpport1 \
#                                -encap ethernet_ii_vlan \
#                                -num_sessions 30 \
#                                -vlan_id 100 \
#                                -vlan_id_count 30 \
#
#    ]
#
#    lappend dhcpHandles [keylget rL handles]
#
# Bind the two DHCP groups using a list of DHCP group handles
#    set rL [sth::emulation_dhcp_control -action bind -handle $handles]
#
# Or bind the two groups using the DHCP port handle
#    set rL [sth::emulation_dhcp_control -action bind -port_handle $dhcpport1]
#
# Sample Input:
#    See Examples.
#
# Sample Output:
#    {status 1} success or {status 0} fail
#
# Notes:
#    None
#
# End of Procedure Header


proc ::sth::emulation_dhcp_control { args } {

    ::sth::sthCore::Tracker "::sth::emulation_dhcp_control" $args

    variable sortedSwitchPriorityList
    variable ::sth::Dhcp::userArgsArray
    array unset ::sth::Dhcp::userArgsArray
    array set ::sth::Dhcp::userArgsArray {}

    set _hltCmdName "emulation_dhcp_control"
    
    set underScore "_"
    
    set returnKeyedList ""
    
    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6::emulation_dhcpv6_control returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: $err" {}
            }
            return $returnKeyedList
        }
    }
    
    if {[catch {::sth::sthCore::commandInit ::sth::Dhcp::dhcpTable $args ::sth::Dhcp:: $_hltCmdName ::sth::Dhcp::userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList $err
        return $returnKeyedList
    }
    
    set modeValue $::sth::Dhcp::userArgsArray(action)
    set retVal [catch {
		switch -exact -- $modeValue \
            bind {
                set cmdStatus 0
                set cmd "::sth::Dhcp::${_hltCmdName}_action $modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: $cmd" {}
                    return $returnKeyedList
                } else {
                    keylset returnKeyedList status $::sth::sthCore::SUCCESS
                }
            }\
            release {
                set cmdStatus 0
                set cmd "::sth::Dhcp::${_hltCmdName}_action $modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName release mode: $cmd" {}
                    return $returnKeyedList
                }
            }\
            renew {
                set cmd "::sth::Dhcp::${_hltCmdName}_action $modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName renew mode: $cmd" {}
                    return $returnKeyedList
                }               
            }\
            rebind {
                set cmd "::sth::Dhcp::${_hltCmdName}_action $modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName rebind mode: $cmd" {}
                    return $returnKeyedList
                }     
            }\
            abort {
                set cmd "::sth::Dhcp::${_hltCmdName}_action $modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName abort mode: $cmd" {}
                    return $returnKeyedList
                }     
            }\
            SHA_UNKNWN_SWITCH {
                ::sth::sthCore::processError returnKeyedList "The switch -action is a mandatory switch"
                return $returnKeyedList                   
            }\
            SHA_NO_USER_INPUT {
                ::sth::sthCore::processError returnKeyedList "The value {} is not valid for the switch -mode"
                return $returnKeyedList                
            }\
            default {
                #Unknown value for switch Mode.
                ::sth::sthCore::processError returnKeyedList "The value $modeValue is not valid for the switch -mode"
                return $returnKeyedList 
            }
    } returnedString]

    if {$retVal} {
		if {$returnedString ne ""} {
			::sth::sthCore::processError returnKeyedList $returnedString {}
		}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_dhcp_stats
#
# Purpose:
#    Returns statistics about the DHCP subscriber group activity on the
#    specified port. Statistics include the connection status and number and
#    type of messages sent and received from the specified port.
#
# Synopsis:
#    sth::emulation_dhcp_stats
#         -port_handle <dhcpPort_handle>
#         [-handle <dhcpGroup_handle>]
#         [-action clear]
#         [-mode {aggregate|session}]
#
# Arguments:
#
#    -action   
#              Resets the statistics for the specified port/subscriber group to
#              0. The default and only possible value is "clear". All statistics
#              including traffic statistics as well as statistics for other
#              protocols will be cleared from all ports in the project, For
#              example, if "-action clear" is executed on any port handle, and
#              there are multiple DHCP ports in the current project, then all
#              statistics will be cleared from all ports in that project, not
#              just the port specified in -port_handle.
#
#    -handle   
#              Specifies the groups whose statistics to return. If you do not
#              specify a handle, then the statistics for all groups configured
#              on the specified port will be returned. This value is returned by
#              the sth::emulation_dhcp_group_config function.
#
#    -mode     
#              Spirent Extension (for Spirent HLTAPI only).
#              Specifies the kind of information you want to see. If you do not
#              specify both -mode and -handle, then aggregate statistics and all
#              statistics of each group under the specified DHCP port
#              (-port_handle) are returned. If -handle is specified but -mode is
#              not, then only the statistics for the specified DHCP group
#              (-handle) are returned. Possible values are:
#
#              aggregate - Returns transmitted and received statistics for the
#                          specified DHCP port.
#
#              session   - If -handle is specified, returns transmitted and
#                          received statistics for the specified DHCP group. If
#                          -handle is not specified, then statistics for all
#                          groups under the specified DHCP port are returned.
#
#    -port_handle
#              Specifies the port upon which emulation is configured. This value
#              is returned by the sth::emulation_dhcp_config function.
#
# Return Values:
#    The sth::emulation_dhcp_stats function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Following is a keyed list showing the types of keys returned based on the mode
# you specified.
#
#    *** Aggregate statistics ***
#
#    aggregate.ack_rx_count
#    aggregate.attempted_rate
#    aggregate.average_setup_time
#    aggregate.bind_rate
#    aggregate.bound_renewed
#    aggregate.currently_attempting
#    aggregate.currently_bound
#    aggregate.currently_idle
#    aggregate.discover_tx_count
#    aggregate.elapsed_time
#    aggregate.maximum_setup_time
#    aggregate.minimum_setup_time
#    aggregate.nak_rx_count
#    aggregate.offer_rx_count
#    aggregate.release_tx_count
#    aggregate.request_tx_count
#    aggregate.success_percentage
#    aggregate.total_attempted
#    aggregate.total_bound
#    aggregate.total_failed
#    aggregate.total_retried
#
#    *** Subscriber Group statistics ***
#    group.<dhcpGroup_handle>.ack_rx_count
#    group.<dhcpGroup_handle>.attempt_rate
#    group.<dhcpGroup_handle>.bind_rate
#    group.<dhcpGroup_handle>.bound_renewed
#    group.<dhcpGroup_handle>.currently_attempting
#    group.<dhcpGroup_handle>.currently_bound
#    group.<dhcpGroup_handle>.currently_idle
#    group.<dhcpGroup_handle>.decline_tx_count
#    group.<dhcpGroup_handle>.discover_tx_count
#    group.<dhcpGroup_handle>.elapsed_time
#    group.<dhcpGroup_handle>.inform_tx_count
#    group.<dhcpGroup_handle>.nak_rx_count
#    group.<dhcpGroup_handle>.offer_rx_count
#    group.<dhcpGroup_handle>.release_tx_count
#    group.<dhcpGroup_handle>.request_tx_count
#    group.<dhcpGroup_handle>.total_attempted
#    group.<dhcpGroup_handle>.total_bound
#    group.<dhcpGroup_handle>.total_failed
#    group.<dhcpGroup_handle>.total_retried
#
#    NOTE: The following statistics are not supported; therefore, their values
#    are returned as "-":  group.<dhcpGroup_handle>.request_rate,
#    and group.<dhcpGroup_handle>.release_rate.
#
# Description:
#    The sth::emulation_dhcp_stats function retrieves a list of
#    aggregate statistics about the DHCP subscriber group activity on the
#    specified port.
#
#    NOTE:In version 1.24, -handle was passed as a string value.
#    In version 1.30, -handle was passed as an integer. In
#    version 2.x, -handle is passed as an alphanumeric value.
#
# Examples:
#    When you call sth::emulation_dhcp_stats, the contents of the returned keyed
#    list depends on the status of the call. For example:
#
#    sth::emulation_dhcp_stats -port_handle $dhcpport1 -mode aggregate
#
#    Returns a list that contains one of the following:
#
#    a)   If the call is successful, the list contains aggregate stats and
#         command execution status (in this case, a 1 indicating success).
#
#    b)   If the call fails, the list contains error log and command
#         execution status (in this case, a 0 indicating failure).
#
#    On success:
#
#    {{aggregate {{nak_rx_count 0} {attempted_rate 188.563907} {total_bound 72}
#    {release_tx_count 0} {maximum_setup_time 0.700688} {currently_idle 0}
#    {success_percentage 100.000000} {bind_rate 166.787465} {total_failed 0}
#    {average_setup_time 0.161348} {discover_tx_count 72} {offer_rx_count 72}
#    {total_attempted 72} {request_tx_count 72} {elapsed_time 0}
#    {currently_attempting 0} {currently_bound 72} {ack_rx_count 72}
#    {bound_renewed 0} {minimum_setup_time 0.002921} {total_retried 0}}}
#    {status 1}
#
#    sth::emulation_dhcp_stats -handle $dhcpgrp1 -mode session
#
#    On success:
#
#    {group {{dhcpv4blockconfig1 {{ack_rx_count 12} {bind_rate 454.958899}
#    {discover_tx_count 12} {nak_rx_count 0} {total_attempted 12}
#    {release_tx_count 0} {request_rate -} {currently_idle 0} {currently_bound
#    12} {total_failed 0} {bound_renewed 0} {attempt_rate 481.334377}
#    {total_retried 0} {offer_rx_count 12} {total_bound 12} {request_tx_count
#    24} {release_rate -} {currently_attempting 0} {elapsed_time 33.000000}}}}}
#    {status 1}
#
# Sample Input:
#    See Examples.
#
# Sample Output:
#    See Examples.
#
#    Note that the blank stats "-" are statistics that are not supported in this
#    release.
#
#    If there is an error, you will see: {status 0} {log {Error message }}
#
# Notes:
#    None
#
# End of Procedure Header


proc ::sth::emulation_dhcp_stats { args } {

    ::sth::sthCore::Tracker "::sth::emulation_dhcp_stats" $args

    variable sortedSwitchPriorityList
    variable ::sth::Dhcp::userArgsArray
    array unset ::sth::Dhcp::userArgsArray
    array set ::sth::Dhcp::userArgsArray {}

    set _hltCmdName "emulation_dhcp_stats"
    
    set underScore "_"
    
    set returnKeyedList ""
   
    if {[set idx [lsearch $args -ip_version]] > -1} {
        set ipVersion [lindex $args [expr {$idx + 1}]]
        if {$ipVersion == 6} {
            if {[catch {::sth::Dhcpv6::emulation_dhcpv6_stats returnKeyedList args} err]} {
                ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName: $err" {}
            }
            return $returnKeyedList
        }
    }
   
    if {[catch {::sth::sthCore::commandInit ::sth::Dhcp::dhcpTable $args ::sth::Dhcp:: $_hltCmdName ::sth::Dhcp::userArgsArray sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList $err
        return $returnKeyedList
    }
    
    set modeValue "collect"
    if {[info exists ::sth::Dhcp::userArgsArray(action)]} {
        set modeValue $::sth::Dhcp::userArgsArray(action)
    } 
    set retVal [catch {
		switch -exact -- $modeValue \
            clear {
                set cmdStatus 0
                set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus $modeValue"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName clear mode: $cmd" {}
                    return $returnKeyedList
                } 
            }\
            collect {
                set cmdStatus 0
                set cmd "::sth::Dhcp::$_hltCmdName$underScore$modeValue ::sth::Dhcp::userArgsArray sortedSwitchPriorityList returnKeyedList cmdStatus $modeValue"
                set procResult [eval $cmd]
                if {!$cmdStatus} {
                    ::sth::sthCore::processError returnKeyedList "Error in $_hltCmdName collect mode: $cmd" {}
                    return $returnKeyedList
                }                  
            }\
            SHA_NO_USER_INPUT {
                ::sth::sthCore::processError returnKeyedList "The value {} is not valid for the switch -mode"
                return $returnKeyedList                
            }\
            default {
                #Unknown value for switch Mode.
                ::sth::sthCore::processError returnKeyedList "The value $modeValue is not valid for the switch -mode"
                return $returnKeyedList 
            }
    } returnedString]

    if {$retVal} {
		if {$returnedString ne ""} {
			::sth::sthCore::processError returnKeyedList $returnedString {}
		}
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}
