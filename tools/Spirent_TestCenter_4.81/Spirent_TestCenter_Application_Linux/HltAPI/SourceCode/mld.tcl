# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::Mld:: {
    variable subscription_state 0
}

##Procedure Header
#
# Name:
#    sth::emulation_mld_config
#
# Purpose:
#    Creates, modifies, or deletes a Multicast Listener Discovery Protocol
#    (MLD) session on the specified Spirent HLTAPI port or handle.
#
#    MLD a communications protocol that manages IPv6 multicast groups. Use MLD
#    to track IPv6 multicast membership.
#
# Synopsis:
#    sth::emulation_mld_config
#         { [-mode create -port_handle <handle> |
#            -mode {modify|delete}
#            -handle <mld_session_handle>} ]
#         }
#         [-count <1-65535> ]
#         [-filter_mode {include | exclude}]
#        [-filter_ip_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-force_leave {0|1}]
#         [-force_robust_join {0|1}]
#         [-general_query 1]
#         [-group_query 1]
#         [-insert_checksum_errors {0|1}]
#         [-mld_version {v1|v2}]
#         -intf_ip_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>
#         [-intf_ip_addr_step <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-intf_prefix_len <1-128>]
#         [-insert_length_errors {0|1}]
#         [-ip_router_alert 1 ]
#         [-link_local_intf_ip_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-link_local_intf_prefix_len <1-128>]
#         [-max_response_control 0 ]
#         [-mld_version {v1|v2} ]
#         [-msg_interval <0-0xFFFFFFFF>]
#         -neighbor_intf_ip_addr <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-neighbor_intf_ip_addr_step
#              <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>]
#         [-robustness <2-255>]
#         [-suppress_report 1]
#         [-unsolicited_report_interval <0-4294967295>]
#         [-use_partial_block_state {0|1}]
#         [-vlan_cfi {0|1}]
#              [-vlan_outer_cfi {0 | 1}]
#         [-vlan_id  <0-4095> ]
#              [-vlan_id_count <1-4096>]
#              [-vlan_id_mode {fixed|increment}]
#              [-vlan_id_step <0-32767>]
#              [-vlan_user_priority <0-7>]
#         [-vlan_id_outer <0-4095>]
#              [-vlan_id_outer_mode {fixed|increment}]
#              [-vlan_id_outer_count <1-4096>]
#              [-vlan_id_outer_step <0-32767>]
#              [-vlan_outer_user_priority <0-7>]
#
# Arguments:
#
#    -count
#                   Defines the number of MLD sessions to create on the
#                   interface. Possible values are 1 to 65535. The default
#                   is 1. You can configure up to 8192 sessions per port.
#    -filter_mode
#                   Specifies an explicit set of sources from which the
#                   multicast group is interested in receiving data (configures
#                   MLDv2 Include Filter mode). Possible values are include and
#                   exclude. The default is "include".
#
#                   include - Data from the specified sources are filtered and
#                        forwarded to the hosts by the multicast router.
#
#                   exclude - Data from the specified sources are filtered and
#                        not forwarded to the hosts by the multicast router.
#   -filter_ip_addr
#                   Configure the filtered IP address. The default is "2008::8"
#                   Only work when version is mld_v2
#                   Dependencies: -filter_mode 
#    -force_leave
#                   Spirent-specific argument (for Spirent HLTAPI only).
#                   Controls whether all hosts are required to send leave
#                   reports when leaving the multicast group. Valid values are 0
#                   (false) and 1 (true). The default is 0. If set to 0, hosts
#                   are not required to send a Leave Group message when leaving
#                   a multicast group. If set to 1, hosts are required to send a
#                   Leave Group message when leaving a multicast group. This
#                   argument affects all hosts except the last one, which is
#                   always required to send an MLDv1 leave report. MLDv1 hosts
#                   leaving a multicast group may optionally send a leave report
#                   to the all-routers multicast group.
#
#    -force_robust_join
#                   Spirent-specific argument (for Spirent HLTAPI only).
#                   Controls whether a second unsolicited join report is
#                   transmitted by the MLDv1 host. Valid values are 0 (false)
#                   and 1 (true). The default is 0. If set to 0, MLDv1 hosts do
#                   not transmit a second join report. If set to 1, MLDv1
#                   hosts do transmit a second join report.
#
#                   When an MLDv1 host joins a multicast group, it immediately
#                   transmits an initial unsolicited membership report for that
#                   group, in case it is the first member of that group on the
#                   network. In case the initial report gets damaged or lost,
#                   it is recommended that you send a second unsolicited report.
#
#    -general_query
#                   Always enabled. When -general_query is set to 1, Spirent
#                   HLTAPI responds to only general queries received on the
#                   interface.
#
#    -group_query
#                   Always enabled. When -group_query is set to 1, Spirent
#                   HLTAPI responds to only group-specific (and source/group)
#                   queries received on the interface.
#
#    -handle
#                   The handle of the MLD host configured on the port to
#                   use when -mode is set to either "modify" or "delete".
#
#    -insert_checksum_errors
#                   Spirent-specific argument (for Spirent HLTAPI only).
#                   Controls the insertion of checksum errors into the MLD
#                   messages by the hardware. Valid values are 0 (false) and 1
#                   (true). The default is 0. If set to 0, the MLD checksum of
#                   the transmitted packet is not modified. If set to 1, the
#                   MLD checksum of the transmitted packet is flipped by the
#                   protocol stack (that is, the least significant bit is
#                   inverted.)
#
#    -insert_length_errors
#                   Spirent-specific argument (for Spirent HLTAPI only).
#                   Controls the insertion of message length errors into the MLD
#                   messages by the MLD stack. Valid values are 0 (false) and 1
#                   (true). The default is 0. If set to 1, every MLD packet
#                   transmitted by the host will be two bytes shorter than
#                   normal If set to 0, the MLD packet lengths will not be
#                   modified
#
#    -intf_ip_addr
#                   Specifies the first IPv6 address in the group. This argument
#                   is required.
#
#    -intf_ip_addr_step
#                   Specifies the difference between interface IP addresses of
#                   consecutive hosts when multiple MLD hosts are created.
#                   The default increment is 1. This argument is only applicable
#                   in create mode.
#
#    -intf_prefix_len
#                   Specifies the address prefix length on the emulated host,
#                   Possible values for IPv6 addresses range from 1 to 128; the
#                   default is 64,
#
#    -ip_router_alert
#                   Alerts transit routers to examine the contents of an IP
#                   packet more closely. When -ip_router_alert is set to 1,
#                   Spirent HLTAPI enables the IP router alert option. This
#                   argument is always enabled (1 or true) in Spirent HLTAPI
#                   whenever hosts send to routers. The IP router alert option
#                   is useful for new protocols that are addressed to a
#                   destination but require relatively complex processing in
#                   routers along the path. (See RFC 2113 for more information.)
#
#    -link_local_intf_ip_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the first link local IPv6 address in the group.
#
#    -link_local_intf_prefix_length
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the address prefix length on the emulated host,
#                   Possible values for link local IPv6 addresses range from 1
#                   to 128; the default is 128.
#
#    -max_response_control
#                   Always set to 0 (false).
#
#    -mld_version
#                   Specifies the multicasting protocol used to manage multicast
#                   group memberships. Possible values are:
#
#                        v1 - Initial multicasting protocol version for IPv6,
#                             similar to IGMPv2. It is specified in RFC 2710.
#
#                        v2 - Version of MLD, specified in draft-vida-mld-
#                             v2-08.txt, that adds the "include" and "exclude"
#                             filter functionality.
#
#    -mode          Specifies the action to perform. Possible values are create,
#                   modify, and delete. This argument is required. The modes are
#                   described below:
#
#                   create - Creates MLD hosts on the specified port or handle,
#                        but does not start them..
#
#                   modify - Changes the configuration parameters for the MLD
#                        hosts identified by the -handle argument.
#
#                   delete - Stops the MLD emulation locally without attempting
#                        to clear the bound addresses from the MLD server. In
#                        addition, all MLD group sessions information on the
#                        port is cleared and the connection is restarted.
#
#    -msg_interval
#                   Maximum output rate of MLD message packets generated per
#                   millisecond. Set this value to 0 to send messages as fast
#                   as possible. Possible values range from 0 to 0xFFFFFFFF. The
#                   default is 0.
#
#    -neighbor_intf_ip_addr
#                   Specifies the IP address of the interface for the MLD
#                   neighbor (next hop) that will establish an adjacency with
#                   the DUT. The default for IPv6 is 2000::1.
#
#    -neighbor_intf_ip_addr_step
#                   Specifies the difference between the MLD neighbor's
#                   interface IP addresses when multiple MLD hosts are created.
#                   The default is 0000:0000:0000:0000:0000:0000:0000:0000 (that
#                   is, the same address).
#
#    -port_handle
#                   The handle of the port on which to create the MLD session.
#
#    -robustness
#                   Specifies the number of times to send a State
#                   Change Report. This number is used in the calculation of
#                   default values for various timers and counters. Possible
#                   values are 2 to 255. The default value is 2. For MLDv1, you
#                   must set -force_robust_join to 1.
#
#    -suppress_report
#                   Suppresses the transmission of a listener report that
#                   duplicates one received on the interface. Multicast hosts
#                   can suppress the transmission of reports to reduce the
#                   amount of multicast communication. This argument is
#                   always enabled.
#
#    -unsolicited_report_interval
#                   Sets the interval (in 1/10 seconds) to wait before re-
#                   sending the host's initial report of membership in a group.
#                   Possible values are 0 to 0-0xFFFFFFFF. The default value is
#                   100 for MLDv1 and 10 for MLDv2. Set it to 0 if you do not
#                   want to send an unsolicited report.
#
#    -use_partial_block_state
#                   Spirent-specific argument (for Spirent HLTAPI only).
#                   Controls the use of a partial block state. Possible values
#                   are 1 (true) and 0 (false). When set to 1, this argument
#                   enables using a partial block state. When set to 0, it
#                   disables the use of a partial block state.
#
#    -vlan_cfi
#                   Sets the canonical format indicator field in VLAN for the
#                   emulated router node. Possible values are 0 (Ethernet) and 1
#                   (Token Ring). The default is 1. If set to 0, it indicates
#                   Token Ring and packets are dropped by Ethernet ports. If set
#                   to 0, it indicates the network is Ethernet.
#
#    -vlan_id
#                   Defines the VLAN ID of the first VLAN sub-interface.
#                   Possible values range from 0 to 4095. The default is 1. When
#                   the mode is either "create" or "enable", Spirent HLTAPI
#                   checks for a vlan object on the port with the given vlan ID.
#                   If no vlan object with that ID exists, Spirent HLTAPI
#                   creates a vlan object with the specified vlan ID.
#
#    -vlan_id_count
#                   Specifies the number of inner VLAN tags to generate for the
#                   stream. Possible values range from 1 to 4096. The default
#                   is 1.
#    -vlan_id_mode
#                   If you configure more than one interface on Spirent
#                   HLTAPI with VLAN, you can choose to either automatically
#                   increment the VLAN tag (mode "increment") or leave it idle
#                   for each interface (mode "fixed"), in which case the VLAN ID
#                   is the same for all packets. If you set this argument
#                   to "increment", then you must also specify the -vlan_id_step
#                   argument to indicate the step size. The default is
#                   increment.
#
#    -vlan_id_step
#                   Defines the step size by which the VLAN value is incremented
#                   when you set -vlan_id_mode to "increment". Possible values
#                   range from 0 to 32767. You must specify the step when the
#                   -count argument is greater than 1. The default is 1.
#
#    -vlan_id_outer
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the VLAN ID for a particular outer header.
#                   Possible values range from 0 to 4095.
#
#    -vlan_id_outer_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the number of VLAN tags to generate for the
#                   outer header. Possible values range from 1 to 4096.
#                   The default is 1. You must set the -vlan_id_outer_mode
#                   argument to increment.
#
#    -vlan_id_outer_mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies how Spirent Test Center will assign VLAN tags to
#                   packets in the specified outer header. Possible values are:
#
#                   fixed - The outer VLAN ID is the same for all packets.
#
#                   increment - For all packets, the outer VLAN tag ID
#                        increments by the step specified in the
#                        -vlan_id_outer_step argument.
#
#    -vlan_id_outer_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   The amount by which to increment the specified outer VLAN ID
#                   (-vlan_id_outer) for subsequent packets. Possible values
#                   range from 0 to 32767. The default is 0.
#
#    -vlan_outer_cfi
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies whether the canonical format indicator (cfi) value
#                   is set for the VLAN outer header. Possible values are 0 or
#                   1.
#
#    -vlan_outer_user_priority
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the VLAN priority to assign to the outer header.
#                   Possible values range from 0 to 7. The default is 0.
#
#    -vlan_user_priority
#                   Defines the VLAN priority for the VLANs on this port.
#                   Possible values range from 0 to 7. The default is 0.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -max_groups_per_pkts
#    -max_response_time
#
# Return Values:
#    The sth::emulation_mld_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handle    MLD session handle. A handle to the MLD host block is returned on
#              success.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_mld_config function creates, modifies, enables,
#    or deletes one or more emulated MLD hosts. Use the -mode argument
#    to specify the action to perform. (See the -mode argument description for
#    information about the actions.)
#
#    When you create an MLD host, use the -port_handle argument to
#    specify the Spirent HLTAPI port that the emulated MLD host will
#    use for MLD communication. (The port handle value is contained in the
#    keyed list returned by the  sth::connect function.)
#
#    Use the -mode create function to define the characteristics of an MLD
#    host.
#
#    Spirent HLTAPI supports the use of MLD versions 1 and 2 for
#    multicast group membership.
#
#    For more information about the MLD protocol, see RFC 2710 (MLDv1) and
#    draft-vida-mld-v2-08.txt (MLDv2).
#
# Examples:
#    The following example creates an MLD session:
#
#    sth::emulation_imld_config \
#         -port_handle $port_handle1 \
#         -mode create \
#         -mld_version v1 \
#         -intf_ip_addr 2001::3 \
#         -neighbor_intf_ip_addr 2001::1
#
# Sample output for example shown above:
#    {handle host1} {status 1}
#
# Notes:
#    When first configuring MLD emulation on a port, you must specify
#    "-mode create" and initialize the port handle before calling the
#    sth::emulation_mld_config function.
#
# End of Procedure Header

proc ::sth::emulation_mld_config {args} {
   variable ::Mld::userArgsArray
   variable ::Mld::sortedSwitchPriorityList
   
   array unset ::Mld::userArgsArray
   array set ::Mld::userArgsArray {}
   
   set returnKeyedList ""
      
   set retval [catch {
      ::sth::sthCore::Tracker emulation_mld_config $args

      if {[catch {::sth::sthCore::commandInit \
            ::Mld::mldTable \
            $args \
            ::Mld:: \
            emulation_mld_config \
            ::Mld::userArgsArray \
            ::Mld::sortedSwitchPriorityList \
         } err]} {
         keylset returnKeyedList log "$err"
         keylset returnKeyedList status $::sth::sthCore::FAILURE
         return $returnKeyedList
      }

      set mode $::Mld::userArgsArray(mode)
      
      switch -exact $mode {
         create {
            ::Mld::emulation_mld_config_create returnKeyedList
         }
         
         modify {
            ::Mld::emulation_mld_config_modify returnKeyedList
         }
         
         delete {
            ::Mld::emulation_mld_config_delete returnKeyedList
         }
         
         enable_all {
            ::Mld::emulation_mld_config_enable_all returnKeyedList
         }
         
         default {
            # Unsupported mode
            ::sth::sthCore::processError returnKeyedList \
                  "Error:  Unsupported -mode value $mode" {}
            return -code error $returnKeyedList
         }
      }
   } returnedString]
   
   return $returnedString
}
 
##Procedure Header
#
# Name:
#    sth::emulation_mld_control
#
# Purpose:
#    Start, stop, or restart the MLD host on the
#    specified port. Leaves and joins group pools.
#
# Synopsis:
#    sth::emulation_mld_control
#         -mode {join|leave}
#         -group_member_handle <handle>
#         -handle <MLD_session_handle>
#         [-delay <seconds>]
#         [-data_duration <seconds>]
#         [-calculate_latency {0|1} ]
#
# Arguments:
#
#    -calculate_latency
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies whether to calculate latencies when joining  or
#                   leaving multicast groups. Possible values are 0 (do not
#                   calculate latency) and 1 (calculate latency). If set to 1
#                   during an MLD Join, HLTAPI cannot capture the MLD
#                   control plane packets because the analyzer stops to collect
#                   packets so it can calculate latency.
#
#                   Note: Background traffic analysis with MLD is unavailable
#                   with calculate latency enabled. Also, if you are testing
#                   multiple joins and leaves with calculate latency enabled,
#                   you must add a delay (a few seconds) between subsequent
#                   joins and leaves (see example below):
#
#                   The following example does 100 iterations of join and leaves
#                   on 90 sessions. A 10-second delay is added after each join 
#                   and each leave (using the Tcl command "after"). The delay 
#                   duration to use depends on the number of iterations and 
#                   number of sessions.
#
#                   for {set joinleaveidx 0} {$joinleaveidx < 100} \
#                        {incr joinleaveidx} {
#
#                        # MLD join
#                        sth::emulation_mld_control \
#                             -mode join \
#                             -calculate_latency 1 \
#                             -handle $MLDSessionHandle
#
#                        # Adding a delay between join and leave.
#                        # This value is based on 90 sessions joining.
#                        # May need to be tweaked when scaling higher.
#
#                        after 10000
#
#                        # MLD leave
#                        sth::emulation_mld_control \
#                             -mode leave \
#                             -calculate_latency 1 \
#                             -handle $MLDSessionHandle
#
#                        # Adding a delay between the last leave and
#                        # the next join when this loops.
#                        # This value is based on 90 sessions leaving.
#                        # May need to be tweaked when scaling higher.
#
#                        after 10000
#
#                        }
#
#    -delay
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the amount of time, in seconds, between joins and
#                   leaves. The default is 0.
#
#    -data_duration
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the amount of time, in seconds, to wait before
#                   latencies are calculated. The default is 10.
#
#    -group_member_handle
#                   Identifies the MLD (one or more) group member handle.
#
#    -handle
#                   Identifies the groups to stop, start, restart, join, or
#                   leave. This value is returned by the
#                   sth::emulation_mld_group_config function. If you do not
#                   specify a group, the specified action is applied to all
#                   groups configured on the port specified by -port_handle.
#                   This value appears in the keyed list returned by the
#                   sth::emulation_mld_group_config function.
#
#
#    -mode
#                   Specifies the action to perform on the specified handle. If
#                   you provide a handle (-handle), this argument performs the
#                   specified action on all groups on this session. If you
#                   provide a group member handle (-group_member_handle), this
#                   argument performs the specified action on the specified
#                   group pool(s). If you do not provide either a handle or
#                   a group member handle, this argument performs the specified
#                   action on all groups on all sessions. Possible values are
#                   start, restart, join, and leave. You must specify one of
#                   these values. The modes are described below:
#
#                   join - Joins all groups specified by -handle or joins
#                        group pools specified by -group_member_handle. If you
#                        do not provide a handle, this action joins all groups
#                        on all ports. This action only affects the status of
#                        the groups, it will not start the MLD protocol.
#
#                   leave - Leave (or unjoin) all groups specified by -handle or
#                        group pools specified by -group_member_handle. If you
#                        do not provide a handle, this action leaves all groups
#                        on all ports. This action only affects the status of
#                        the groups, it will not start or stop the protocol..
#
# Cisco-specific Arguments:
#    The -port_handle argument is specific to the Cisco HLTAPI but is
#    not supported by Spirent HLTAPI 2.00.
#
#
# Return Values:
#     The function returns a keyed list using the following keys (with
#     corresponding data):
#
#     status     Success (1) or failure (0) of the operation.
#     log        An error message (if the operation failed).
#
# Description:
#    The sth::emulation_mld_control function sends a Join or Leave message from
#    the host to inform a router that the host is either joining the multicast
#    group specified by handle or group_member_handle or terminating its
#    membership in the specified multicast group.
#
#    When you call the sth::emulation_mld_control function, you
#    specify a handle. Spirent HLTAPI applies the specified action to
#    all of the emulated MLD hosts associated with the specified port.
#
#    When a host wants to participate in a multicast group, it sends a
#    "join" message to its local router. After a router receives one or
#    more "joins" for a specific group, it forwards any packets destined for
#    that particular group to the appropriate interface(s). The router regularly
#    verifies that the hosts want to continue to participate in the
#    multicast groups by sending periodic "queries" to the receivers.
#
#    When a host is no longer interested in multicast group participation, it
#    sends a "leave" message.
#
# Examples:
#    The following example joins all groups specified by -handle:
#
#    sth::emulation_mld_control
#         -mode join
#         -handle $MLDSessionHandle
#
#    The following example removes the groups specified by -handle
#    from the hosts on the specified port:
#
#    sth::emulation_mld_control
#         -mode leave
#         -handle $MLDSessionHandle
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
   
proc ::sth::emulation_mld_control {args} {
   variable ::Mld::userArgsArray
   variable ::Mld::sortedSwitchPriorityList
   
   array unset ::Mld::userArgsArray
   array set ::Mld::userArgsArray {}
   
   set returnKeyedList ""
   set calcLatency "FALSE"
   
   ::sth::sthCore::Tracker emulation_mld_control $args
   if {[catch {::sth::sthCore::commandInit \
         ::Mld::mldTable \
         $args \
         ::Mld:: \
         emulation_mld_control \
         ::Mld::userArgsArray \
         sortedSwitchPriorityList \
      } err]} {
      keylset returnKeyedList log "$err"
      keylset returnKeyedList status $::sth::sthCore::FAILURE
      return $returnKeyedList
   }
   
   set retVal [catch {
      set deviceList ""
      
      if {[info exists ::Mld::userArgsArray(handle)]} {
         set ::Mld::userArgsArray(handle) [::Mld::emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]
         set deviceList $::Mld::userArgsArray(handle)
      } elseif {[info exists ::Mld::userArgsArray(port_handle)]} {
		 set portHndList $userArgsArray(port_handle)
		 foreach ::Mld::userArgsArray(port_handle) $portHndList {
			 foreach host [::sth::sthCore::invoke stc::get $::Mld::userArgsArray(port_handle) -affiliationport-Sources] {
				append deviceList " [::sth::sthCore::invoke stc::get \
					  $host -children-mldHostConfig]"
			 }
		 }
		 set userArgsArray(port_handle) $portHndList
      }
      
      switch -- $::Mld::userArgsArray(mode) {
         join {set deviceCmd "IgmpMldJoinGroupsCommand"}
         leave {set deviceCmd "IgmpMldLeaveGroupsCommand"}
         leave_join {set deviceCmd  "IgmpMldRejoinGroupsCommand"}
         default {
            return -code error [concat "Error: Unsupported MLD " \
                  "control mode \"$::Mld::userArgsArray(mode)\".  "]
         }
      }

      if {[info exists ::Mld::userArgsArray(calculate_latency)] == 0} {
         set ::Mld::userArgsArray(calculate_latency) [::sth::sthCore::getswitchprop \
               ::Mld:: emulation_mld_control \
               calculate_latency default]
      }
      
      if {[llength $deviceList] > 0} {
         if {$::Mld::userArgsArray(calculate_latency)} {
            set calcLatency "TRUE"
         } else {
            set calcLatency "FALSE"
         }

        #Get sequencer handle before config
        set seqHandle [::sth::sthCore::invoke  "stc::get system1 -children-Sequencer"]

         ::sth::sthCore::invoke stc::config $seqHandle [list -CommandList ""]
         set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under [::sth::sthCore::invoke stc::get $seqHandle -Parent] [list -IterationCount "1" -ExecutionMode "BACKGROUND" -GroupCategory "CLEANUP_COMMAND" -ContinuousMode "FALSE" -AutoDestroy "FALSE" -ExecuteSynchronous "FALSE"]]

         # set WaitForTxReports to "FALSE". The command may hang otherwise.
         set igmpMldCmd [::sth::sthCore::invoke stc::create $deviceCmd -under $seqHandle [list -calculateLatency $calcLatency -blockList $deviceList -WaitForTxReports "FALSE" -RxDataDuration $::Mld::userArgsArray(data_duration) -JoinLeaveDelay $::Mld::userArgsArray(delay)]]
         
         ::sth::sthCore::invoke stc::config $seqHandle [list -CommandList $igmpMldCmd -SequencerFinalizeType-targets $seqLoopCmd -breakpointList "" -disabledCommandList "" -cleanupCommand $seqLoopCmd]
         ::sth::sthCore::doStcApply
         ::sth::sthCore::invoke stc::perform sequencerStart
         ::sth::sthCore::invoke ::stc::waituntilcomplete
         ::sth::sthCore::invoke stc::delete $igmpMldCmd
         ::sth::sthCore::invoke stc::delete $seqLoopCmd
      }
   } returnedString]
   
   if {$retVal} {
      ::sth::sthCore::processError returnKeyedList $returnedString {}
   } else {
      keylset returnKeyedList status $::sth::sthCore::SUCCESS
   }
   
   return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::emulation_mld_group_config
#
# Purpose:
#    Creates group pools and source pools and modifies group and
#    source pools from MLD hosts. This function configures multicast
#    group ranges for an emulated MLD host.You must use the common
#    sth::multicast_group_config and sth::multicast_source_config functions with
#    this function.
#
# Synopsis:
#    sth::emulation_mld_group_config
#         {-mode create -session_handle <mld_session_handle> |
#          -mode {modify|delete} -handle <group_member_handle>}
#         -group_pool_handle <multicast_group_pool_handle>
#         -source_pool_handle <multicast_source_pool_handle>
#
# Arguments:
#
#    -group_pool_handle
#                   Specifies the name of the group (that is, the list of
#                   multicast IP addresses) to link to the MLD host during
#                   create mode. Before specifying the group pool handle, use
#                   the sth::emulation_multicast_group_config function to add
#                   the group pool. See "Multicast APIs" in this documentation
#                   set for information about the
#                   sth::emulation_multicast_group_config and
#                   sth::emulation_multicast_source_config functions. This
#                   argument is required.
#
#    -handle
#                   Sets the group membership handle that associates group pools
#                   with an MLD host. In modify mode, the membership handle must
#                   be used in conjunction with the session handle to identify
#                   the multicast group pools. Mode "modify" returns the same
#                   handle passed in. This argument is required.
#
#    -mode          Specifies the action to perform. Possible values are create,
#                   modify, and delete. There is no default; you must specify a
#                   mode. The modes are described below:
#
#                   create - Starts emulation on the port specified with
#                        -session_handle and associates an existing multicast
#                        group pool (-group_pool_handle) with the specified MLD
#                        host (that is, joins the membership). You must specify
#                        a session handle with "-mode create".
#
#                   modify - Changes the configuration identified by the -handle
#                        argument by applying the parameters specified in
#                        subsequent arguments.
#
#                   delete - Remove one group of pools from this session.
#
#    -session_handle
#                   Specifies the handle of the MLD host on which to configure
#                   the MLD group ranges. This argument is required.
#
#    -source_pool_handle
#                   Specifies the name of the source pool (that is, the list of
#                   non-multicast source IP addresses) to associate with the
#                   groups during create mode. Each multicast group may contain
#                   0 or more of these source IP addresses. Use this argument if
#                   the host only wants specific information within the
#                   specified multicast group (-group_pool_handle). Specifying
#                   the source pool handle along with the group pool handle in
#                   the sth::emulation_mld_group_config function adds the
#                   range of source IP addresses to each multicast group. This
#                   argument is required.
#
#                   Before specifying the source pool handle, use the
#                   sth::emulation_multicast_source_config function to add
#                   the source pools. See "Multicast APIs" in this documentation
#                   set for information about the
#                   sth::emulation_multicast_source_config and
#                   sth::emulation_multicast_group_config functions.
#
# Return Values:
#    The sth::emulation_mld_group_config function returns a keyed
#    list using the following keys (with corresponding data):
#
#    handle
#              Identifies the handle of the group (group_member_handle) created
#              by the sth::emulation_mld_group_config function.
#
#    group_pool_handle
#              Identifies the group pool handle used by the
#              sth::emulation_mld_group_config function to configure or modify
#              the group member.
#
#    source_pool_handle
#              Identifies the source pool handle used by the
#              sth::emulation_mld_group_config function to configure or modify
#              the group member.
#
#    status
#              Success (1) or failure (0) of the operation.
#
#    log
#              An error message (if the operation failed).
#
# Description:
#    The sth::emulation_mld_group_config function configures or
#    modifies a group of MLD hosts where each group share a
#    set of common characteristics. Use the -mode argument to specify
#    the action to perform. (See the -mode argument description for information
#    about the actions.)
#
#    Before using this function, you must specify "-mode create" when
#    configuring MLD host emulation on a port and initialize the port handle
#    argument (using the sth::emulation_mld_config function).
#
#    When calling sth::emulation_mld_group_config using "-mode create",
#    this function will return the group member handle for use with the -handle
#    argument.
#
#    You can link groups of multicast IP addresses to any interested host or
#    just a subset of IP addresses within each group.
#
#    Each multicast IP address directs the information it represents to any host
#    interested in subscribing to it.
#
#    To subscribe to only one or more particular IP addresses that exist within
#    a multicast group, you must use the -source_pool_handle as well. Specifying
#    the source_pool_handle along with the group_pool_handle in the
#    sth::emulation_mld_group_config function, adds the range of source IP
#    addresses to each multicast group.
#
# Examples:
#    [[please provide an example]]
#
# Notes:
#     None
#
# End of Procedure Header
   
proc ::sth::emulation_mld_group_config {args} {
   variable ::Mld::userArgsArray
   variable ::Mld::sortedSwitchPriorityList
   
   array unset ::Mld::userArgsArray
   array set ::Mld::userArgsArray {}
   
   set returnKeyedList ""
   
   ::sth::sthCore::Tracker emulation_mld_group_config $args
   if {[catch {::sth::sthCore::commandInit \
         ::Mld::mldTable \
         $args \
         ::Mld:: \
         emulation_mld_group_config \
         ::Mld::userArgsArray \
         ::Mld::sortedSwitchPriorityList \
      } err]} {
      keylset returnKeyedList log "$err"
      keylset returnKeyedList status $::sth::sthCore::FAILURE
      return $returnKeyedList
   }
   
   set mode $::Mld::userArgsArray(mode)
   
   set retVal [catch {
      switch -exact $mode {
         create {
            ::Mld::emulation_mld_group_config_create returnKeyedList
         }
            
         modify {
            ::Mld::emulation_mld_group_config_modify returnKeyedList
         }
            
         delete {
            ::Mld::emulation_mld_group_config_delete returnKeyedList
         }
         
         clear_all {
            ::Mld::emulation_mld_group_config_clear_all returnKeyedList
         }
         
         default {
            # Unsupported mode
            ::sth::sthCore::processError returnKeyedList \
                  "Error:  Unsupported -mode value $mode" {}
            return $returnKeyedList
         }
      }
   } returnedString]
   
   return $returnedString
}

##Procedure Header
#
# Name:
#    sth::emulation_mld_info
#
# Purpose:
#    Returns statistics about the MLD group activity on the
#    specified handle. Statistics include the connection status and number and
#    type of messages sent and received from the specified port.
#
# Synopsis:
#    sth::emulation_mld_info
#         -handle <MLD_session_handle>
#
# Arguments:
#
#    -handle   Specifies the MLD session handle upon which host emulation is
#              configured. This argument is required. This value is returned by
#              the sth::emulation_mld_config function.
#
# Return Values:
#    The sth::emulation_mld_info function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
#    invalid_pkts
#                   Number of invalid MLD packets received. Invalid
#                   MLD packets include:
#                        invalid MLD checksum
#                        invalid packet length
#                        invalid MLD types
#
#    dropped_pkts
#                   Will always return 0 because Spirent HLTAPI currently
#                   does not drop valid MLD packets dropped.
#
#    host_addr
#                   IP address of host whose group membership stats are
#                   being displayed.
#
#    group_addr
#                   Group membership IP address of host whose group membership
#                   stats are being displayed.
#
#    group_membership_stats
#                   List of group membership statistics.
#
#    state          State of group membership of host whose group membership
#                   stats are being displayed. Possible returned values are:
#
#                   UNDEFINED - The state is not defined.
#
#                   NON_MEMBER - The host does not belong to the group on the
#                        interface. Non-member is the initial state for all
#                        memberships on all network interfaces.
#
#                   DELAYING_MEMBER - The host belongs to the group on the
#                        interface and has a report delay timer running for that
#                        membership.
#
#                   IDLE_MEMBER - The host belongs to the group on the interface
#                        and does not have a report delay timer running for that
#                        membership.
#
#                   RETRYING_MEMBER - This state applies to MLDv1 hosts
#                        when ForceRobustJoin is True. The host is
#                        retransmitting its initial "join" before transitioning
#                        from the NON_MEMBER state to the DELAYING_MEMBER or
#                        IDLE_MEMBER state.
#
#                   INCLUDE - Data from the specified sources are filtered and
#                        forwarded to the host by the multicast router.
#
#                   EXCLUDE - Data from the specified sources are filtered and
#                        not forwarded to the host by the multicast router.
#
#    join_latency
#                   The time, in milliseconds, between sending the MLD join and
#                   receiving the multicast data for the channel specified in
#                   the join message. This value is valid only when
#                   "sth::emulation_igmp_control -calculate_latency" is set to
#                   1.
#
#    leave_latency
#                   The time, in milliseconds, between sending the MLD leave
#                   for a channel and when multicast data has stopped being
#                   received. This value is valid only when
#                   "sth::emulation_igmp_control -calculate_latency" is set to
#                   1.
#
#    In addition, the following MLD port statistics are returned:
#
#    mldv1_queries_rx         Routers use Multicast Listener Query messages to
#                             query a subnet for multicast listeners.
#
#    mldv1_group_queries_rx   MLDv1 Group specific Queries received.
#
#    mldv1_queries_tx         MLDv1 Membership Queries are sent by IP multicast
#                             routers to query the multicast reception state of
#                             neighboring interfaces.
#
#    mldv1_mem_reports_tx     MLDv1 reports are sent to multicast routers to
#                             indicate that hosts have listeners interested in
#                             joining multicast groups whose multicast address
#                             is listed in the router's list.
#
#    mldv1_mem_reports_rx     MLDv1 reports are sent to multicast routers to
#                             indicate that hosts have listeners interested in
#                             joining multicast groups whose multicast address
#                             is listed in the router's list.
#
#    mldv1_leave_tx           MLDv1 Leaves transmitted.
#
#    mldv2_queries_rx         Routers use Multicast Listener Query messages to
#                             query a subnet for multicast listeners.
#
#    mldv2_group_queries_tx   This statistic is included in the
#                             TxV2QueryCount. MLDv2 Membership Queries are sent
#                             by IP multicast routers to query the multicast
#                             reception state of neighboring interfaces.
#
#    mldv2_group_src_queries_rx
#                             Routers use Multicast Listener Query messages to
#                             query a subnet for multicast listeners
#
#    mldv2_mem_reports_rx     MLDv2 are used to report interest in receiving
#                             multicast traffic for a specific multicast address
#                             or to respond to a Multicast Listener Query
#                             message.
#
#    mldv2_mem_reports_tx     MLDv2 reports are sent to multicast routers to
#                             indicate that hosts have listeners interested in
#                             joining multicast groups whose multicast address
#                             is listed in the router's list.
#
#    mld_frames_rx            Total number of MLD frames received.
#
#    mld_general_queries_rx
#                             Total number of multicast general queries
#                             received.
#
#    mld_group_src_queries_rx
#                             Group- and source-specific queries are sent by a
#                             multicast router whenever a host leave a specific
#                             source of a group. This is to make sure that there
#                             are no other hosts of that source and group.
#
#    mld_group_queries_rx
#                             The Group-Specific Query is used to learn if a
#                             particular group has any members on an attached
#                             network.
#
#    mld_checksum_errors_rx
#                             Total number of MLD messages received with
#                             checksum errors.
#
#    mld_length_errors_rx
#                             Total number of MLD messages received with length
#                             errors.
#
#    mld_unknown_rx
#                             Total number of MLD frames of unknown type
#                             received.
#
#    mld_timestamp
#                             Timestamp in seconds of last statistic update.
#
#    mld_frames_tx
#                             Total number of MLD frames transmitted.
#
#    mld_general_queries_tx
#                             General Queries are used to learn which multicast
#                             addresses have listeners on an attached link.
#
#    mld_group_src_queries_tx
#                             Group- and source-specific queries are sent by a
#                             multicast router whenever a host leave a specific
#                             source of a group. This is to make sure that there
#                             are no other hosts of that source and group.
#
#    mld_group_queries_tx
#                             The Group-Specific Query is used to learn if a
#                             particular group has any members on an attached
#                             network.
#
#    mldv2_allow_new_src_tx
#                             A Source-List-Change Record (SLCR) indicating the
#                             group's associated sources have changed such that
#                             data from a new set of sources are to be received
#
#    mldv2_block_old_src_tx
#                             A Source-List-Change Record (SLCR) indicating the
#                             group's associated sources have changed such that
#                             data from an existing set of sources are not
#                             required.
#
#    mldv2_filter_exclude_tx
#                             A Filter-Mode-Change Record (FMCR) indicating the
#                             filter-mode of the reception state has changed to
#                             exclude mode.
#
#    mldv2_filter_include_tx
#                             A Filter-Mode-Change Record (FMCR) indicating the
#                             filter-mode of the reception state has changed to
#                             include mode.
#
#    mldv2_exclude_tx
#                             A Current-State Record (CSR) indicating the
#                             current reception state with respect to 1
#                             multicast group at a given interface. The state
#                             contains the exclude filter mode.
#
#    mldv2_include_tx
#                             A Current-State Record (CSR) indicating the
#                             current reception state with respect to 1
#                             multicast group at a given interface. The state
#                             contains the include filter mode
#
# Description:
#    The sth::emulation_mld_info function retrieves statistics about the
#    number of invalid and dropped packets on the specified host as well as
#    several port statistics.
#
# Examples:
#    When you call sth::emulation_mld_info, the contents of the returned keyed
#    list depends on the status of the call. For example:
#
#    sth::emulation_mld_info -handle $handle1
#
#    Returns a list that contains one of the following:
#
#    a)   If the call is successful, the list contains stats and
#         command execution status (in this case, a 1 indicating success).
#
#    b)   If the call fails, the list contains error log and command
#         execution status (in this case, a 0 indicating failure).
#
# Sample Input:
#    See Examples.
#
# Sample Output:
#
#    {group_membership_stats {{group_addr {{ff1e::1 {{host_addr 
#    {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 0.000000} 
#    {leave_latency 0.000000}}}}}}} {ff1e::2 {{host_addr {{fe80:1:1:1:1:1:1:2 
#    {{state IDLE_MEMBER} {join_latency 0.000000} {leave_latency 0.000000}}}}}}} 
#    {ff1e::3 {{host_addr {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} 
#    {join_latency 0.000000} {leave_latency 0.000000}}}}}}} {ff1e::4
#    {{host_addr {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 
#    0.000000} {leave_latency 0.000000}}}}}}} {ff1e::5 {{host_addr 
#    {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 0.000000} 
#    {leave_latency 0.000000}}}}}}} {ff1e::6 {{host_addr {{fe80:1:1:1:1:1:1:2 
#    {{state IDLE_MEMBER} {join_latency 0.000000} {leave_latency 0.000000}}}}}}} 
#    {ff1e::7 {{host_addr {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} 
#    {join_latency 0.000000} {leave_latency 0.000000}}}}}}} {ff1e::8 
#    {{host_addr {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 
#    0.000000} {leave_latency 0.000000}}}}}}} {ff1e::9 {{host_addr 
#    {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 0.000000} 
#    {leave_latency 0.000000}}}}}}} {ff1e::a {{host_addr 
#     {{fe80:1:1:1:1:1:1:2 {{state IDLE_MEMBER} {join_latency 0.000000} 
#    {leave_latency 0.000000}}}}}}}}}}} {session {{mldhostconfig1 
#    {{min_join_latency 0.000000} {max_join_latency 0.000000} {avg_join_latency 
#    0.000000} {min_leave_latency 0.000000} {max_leave_latency 0.000000} 
#    {avg_leave_latency 0.000000}}}}} {status 1}
#
#    If there is an error, you will see: {status 0} {log {Error message }}
#
# Notes:
#    If you configure over 1000 host-group pairs, the lower layer only returns
#    avg/min/max latencies in the returned keyed list. If you configure 1000 or
#    less host-group pairs, the returned keyed list contains individual
#    latencies.
#
# End of Procedure Header
   
proc ::sth::emulation_mld_info {args} {
   variable ::Mld::userArgsArray
   variable ::Mld::sortedSwitchPriorityList
   
   array unset ::Mld::userArgsArray
   array set ::Mld::userArgsArray {}
   
   set returnKeyedList ""
   
   ::sth::sthCore::Tracker emulation_mld_info $args
   if {[catch {::sth::sthCore::commandInit \
         ::Mld::mldTable \
         $args \
         ::Mld:: \
         emulation_mld_info \
         ::Mld::userArgsArray \
         ::Mld::returnKeyedList \
      } err]} {
      keylset returnKeyedList log "$err"
      keylset returnKeyedList status $::sth::sthCore::FAILURE
      return $returnKeyedList
   }
   
   set mldPorthandles ""
   set groupMembershipStats ""
   array unset groupAddrStats
      
   set retVal [catch {
        #move the result subscriber from mld config to the emulation_mld_info, since if the result is subscibed, and then enable the iptv on it, it will get the demon died.
        #so in the hltapi script, need to make sure the emulation_iptv_config should not be called after the emulation_mld_info
        if {$::Mld::subscription_state == 0} {
         # Create an MLD port dataset
         set portResultDataSet \
               [::Mld::emulation_mld_config_create_resultDataset \
                     "MldPortConfig" \
                     "MldPortResults" \
                     [list \
                           "multicastportresults.txgroupandsourcespecificquerycount" \
                           "multicastportresults.rxgroupandsourcespecificquerycount" \
                           "multicastportresults.rxv1querycount" \
                           "multicastportresults.txv1reportcount" \
                           "multicastportresults.rxv1reportcount" \
                           "multicastportresults.rxv2querycount" \
                           "multicastportresults.txv2reportcount" \
                           "multicastportresults.rxv2reportcount" \
                           "multicastportresults.rxunknowntypecount" \
                           "mldportresults.rxmldchecksumerrorcount" \
                           "mldportresults.rxmldlengtherrorcount"] \
               ]
         # Create an MLD group membership dataset
         set mldGroupMembershipResultDataSet \
               [::Mld::emulation_mld_config_create_resultDataset \
                     "MldGroupMembership" \
                     "MldGroupMembershipResults" \
                     [list "Mldgroupmembershipresults.hostaddr" \
                           "Mldgroupmembershipresults.groupaddr" \
                           "multicastgroupmembershipresults.state" \
                           "multicastgroupmembershipresults.joinlatency" \
                           "multicastgroupmembershipresults.leavelatency"] \
               ]

         set mldResultsDataSet \
               [::Mld::emulation_mld_config_create_resultDataset \
                     "MldHostConfig" \
                     "MldHostResults" \
                     [list "mldhostresults.minjoinlatency" \
                           "mldhostresults.maxjoinlatency" \
                           "mldhostresults.avgjoinlatency" \
                           "mldhostresults.minleavelatency" \
                           "mldhostresults.maxleavelatency" \
                           "mldhostresults.avgleavelatency"] \
               ]

         ::sth::sthCore::doStcApply

         # Subscribe to the datasets
         ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $portResultDataSet
         ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldGroupMembershipResultDataSet
         ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $mldResultsDataSet
         set ::Mld::subscription_state 1
         ::sth::sthCore::invoke stc::sleep 3
        }
      # Group membership statistics
      if {[info exists ::Mld::userArgsArray(handle)]} {
         set ::Mld::userArgsArray(handle) [::Mld::emulation_mld_config_getMldHostCfgList $userArgsArray(handle)]
         foreach mldHostConfig $::Mld::userArgsArray(handle) {
            # Group membership statistics
            foreach mldGroupMembership [::sth::sthCore::invoke stc::get $mldHostConfig -children-mldGroupMembership] {
               foreach groupMembershipResult [::sth::sthCore::invoke stc::get $mldGroupMembership -children-mldGroupMembershipResults] {
                  set iHostStat [join \
                        [list \
                           "group_addr" \
                           [::sth::sthCore::invoke stc::get $groupMembershipResult -GroupAddr] \
							"host_addr" \
                           [::sth::sthCore::invoke stc::get $groupMembershipResult -HostAddr] \
                        ] \
                        "."]
                  keylset groupMembershipStats "$iHostStat.state" \
                        [::sth::sthCore::invoke stc::get $groupMembershipResult -State]
                  keylset groupMembershipStats "$iHostStat.join_latency" \
                         [::sth::sthCore::invoke stc::get $groupMembershipResult -JoinLatency]
                  keylset groupMembershipStats "$iHostStat.leave_latency" \
                         [::sth::sthCore::invoke stc::get $groupMembershipResult -LeaveLatency]
               }
            }
            
            # MLD session statistics
            set sessionResults [::sth::sthCore::invoke stc::get $mldHostConfig -resultchild-Targets]
            foreach sessionResult $sessionResults {
                keylset mldSessionStats "$mldHostConfig.min_join_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-minJoinLatency"]
                keylset mldSessionStats "$mldHostConfig.max_join_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-maxJoinLatency"]
                keylset mldSessionStats "$mldHostConfig.avg_join_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-avgJoinLatency"]
                keylset mldSessionStats "$mldHostConfig.min_leave_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-minLeaveLatency"]
                keylset mldSessionStats "$mldHostConfig.max_leave_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-maxLeaveLatency"]
                keylset mldSessionStats "$mldHostConfig.avg_leave_latency" \
                      [::sth::sthCore::invoke stc::get $sessionResult "-avgLeaveLatency"]
            }
         }
      }
      
      # Port statistics
      if {[info exists ::Mld::userArgsArray(port_handle)]} {

         array unset stats
         set stats(mldv1_queries_rx) 0
         set stats(mldv1_group_queries_rx) 0
         set stats(mldv1_queries_tx) 0
         set stats(mldv1_mem_reports_tx) 0
         set stats(mldv1_mem_reports_rx) 0
         set stats(mldv1_leave_tx) 0
         set stats(mldv2_queries_rx) 0
         set stats(mldv2_group_queries_tx) 0
         set stats(mldv2_group_src_queries_rx) 0
         set stats(mldv2_mem_reports_tx) 0
         set stats(mldv2_mem_reports_rx) 0
         set stats(mld_frames_rx) 0
         set stats(mld_general_queries_rx) 0
         set stats(mld_group_src_queries_rx) 0
         set stats(mld_group_queries_rx) 0
         set stats(mld_checksum_errors_rx) 0
         set stats(mld_length_errors_rx) 0
         set stats(mld_unknown_rx) 0
         set stats(mld_timestamp) 0
         set stats(mld_frames_tx) 0
         set stats(mld_general_queries_tx) 0
         set stats(mld_group_src_queries_tx) 0
         set stats(mld_group_queries_tx) 0
         set stats(mldv2_allow_new_src_tx) 0
         set stats(mldv2_block_old_src_tx) 0
         set stats(mldv2_filter_exclude_tx) 0
         set stats(mldv2_filter_include_tx) 0
         set stats(mldv2_exclude_tx) 0
         set stats(mldv2_include_tx) 0
         set stats_invalid_pkts 0
      
         foreach mldPort $::Mld::userArgsArray(port_handle) {
            set mldPortConfig [::sth::sthCore::invoke stc::get $mldPort -children-mldPortConfig]
            set mldPortResults [::sth::sthCore::invoke stc::get $mldPortConfig -children-mldPortResults]
            
            foreach stat [array names stats] {
               set s [::sth::sthCore::getswitchprop ::Mld:: \
                     emulation_mld_info $stat stcattr]

               set stats($stat) [expr $stats($stat) + \
                     [::sth::sthCore::invoke stc::get $mldPortResults "-$s"]]
            }
         
            foreach invalid_pkt_stat [::sth::sthCore::getswitchprop \
                  ::Mld:: emulation_mld_info invalid_pkts stcattr] {
               set stats_invalid_pkts [expr $stats_invalid_pkts + \
                     [::sth::sthCore::invoke stc::get $mldPortResults "-$invalid_pkt_stat"]]
            }
            
            # Spirent TestCenter 2.0 does not drop valid MLD packets. So
            # always set this statistic to 0
            set stats(dropped_pkts) 0
            keylset portStats \
                  ${::Mld::userArgsArray(port_handle)}.invalid_pkts \
                  $stats_invalid_pkts
         }
         
         foreach stat [array names stats] {
            keylset portStats \
               ${::Mld::userArgsArray(port_handle)}.$stat \
               $stats($stat)
         }
      }
   } returnedString]
   
   if {$retVal} {
      ::sth::sthCore::processError returnKeyedList $returnedString
   } else {
      if {[info exists ::Mld::userArgsArray(handle)]} {
         keylset returnKeyedList group_membership_stats \
            $groupMembershipStats
         keylset returnKeyedList session \
               $mldSessionStats
      }
      
      if {[info exists ::Mld::userArgsArray(port_handle)]} {
         keylset returnKeyedList port_stats $portStats
      }
      
      keylset returnKeyedList status $::sth::sthCore::SUCCESS
   }
   return $returnKeyedList
}
