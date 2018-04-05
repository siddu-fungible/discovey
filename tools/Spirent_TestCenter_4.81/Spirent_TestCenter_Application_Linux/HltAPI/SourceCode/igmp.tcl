# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

##Procedure Header
#
# Name:
#    sth::emulation_igmp_config
#
# Purpose:
#    Creates, modifies, or deletes Internet Group Management Protocol (IGMP)
#    host(s) for the specified Spirent TestCenter port or handle.
#
#    The Internet Group Management Protocol (IGMP) is a communications protocol
#    that manages the membership of Internet Protocol multicast groups.
#
#    Use IGMP to dynamically register individual hosts in a multicast group on a
#    particular LAN. Hosts identify which multicast groups they belong to by
#    sending IGMP messages to their local router. Under IGMP, routers listen to
#    IGMP messages and send out queries to discover which groups are active on a
#    particular subnet. When all hosts leave a group, the router no longer
#    forwards packets for that group.
#
# Synopsis:
#    sth::emulation_igmp_config
#         {-mode create -port_handle <handle> |
#            -mode {modify|delete}
#            -handle <igmp_session_handle> }
#         [-count <1-65535> ]
#         [-filter_mode {include | exclude}]
#         [-filter_ip_addr {192.0.1.0}]
#         [-general_query 1]
#         [-group_query 1]
#         [-igmp_version {v1|v2|v3}]
#         [-intf_ip_addr <a.b.c.d>]
#         [-intf_ip_addr_step <a.b.c.d>]
#         [-intf_prefix_len <1-32>]
#         [-ip_router_alert {0|1}]
#         [-msg_interval <0-4294967295>]
#         [-neighbor_intf_ip_addr <a.b.c.d>]
#         [-neighbor_intf_ip_addr_step <a.b.c.d>]
#         [-older_version_timeout <0-4294967295>]
#         [-pppox_handle <handle>]
#         [-robustness <2-255>]
#         [-suppress_report 1]
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
#                   Defines the number of IGMP hosts to create on the
#                   interface. Possible values are 1 to 65535. The default
#                   is 1.
#
#    -filter_mode
#                   Specifies an explicit set of sources from which the
#                   multicast group is interested in receiving data (configures
#                   IGMPv3 Include Filter mode). Possible values are include and
#                   exclude. The default is "include".
#
#                   include - Data from the specified sources are filtered and
#                        forwarded to the hosts by the multicast router.
#
#                   exclude - Data from the specified sources are filtered and
#                        not forwarded to the hosts by the multicast router.
#
#    -filter_ip_addr
#                   Configure the filtered IP address
#
#    -general_query
#                   Always enabled. Valid values are 0 (false) and 1 (true).
#                   When -general_query is set to 1, Spirent TestCenter responds
#                   to only general queries received on the interface.
#
#    -group_query
#                   Always enabled. Valid values are 0 (false) and 1 (true).
#                   When -group_query is set to 1, Spirent TestCenter responds
#                   to only group-specific (and source/group) queries received
#                   on the interface.
#
#    -handle
#                   The handle of the IGMP host configured on the port to
#                   use when -mode is set to either "modify" or "delete".
#                   This argument is required when you specify any mode except
#                  "create."
#
#                   You can use -handle when -mode is set to "create" for
#                   IGMPoPPPoX. When specifying a PPPoX handle, the PPPoX
#                   options specified in the sth::pppox_config function are
#                   used instead of the following sth::emulation_igmp_config
#                   arguments:
#
#                    -intf_ip_addr
#                    -intf_ip_addr_step
#                    -intf_prefix_len
#                    -neighbor_intf_ip_addr
#                    -neighbor_intf_ip_addr_step
#                    -vlan_cfi
#                    -vlan_id
#                    -vlan_id_mode
#                    -vlan_id_step
#                    -vlan_user_priority
#
#                   The following example specifies a PPPoX handle:
#
#                   sth::emulation_igmp_config \
#                           -mode create  \
#                           -handle $pppoxHandle \
#                           -older_version_timeout 400 \
#                           -robustness 2 \
#                           -unsolicited_report_interval 100
#
#    -igmp_version
#                   Specifies the multicasting protocol used to manage multicast
#                   group memberships. Possible values are:
#
#                        v1 - The second version of IGMP (supercedes IGMPv0),
#                             specified in RFC 1112.
#
#                        v2 - IGMP version specified in RFC 2236. Improved IGMP
#                             version that adds "leave" messages, shortening the
#                             amount of time required for a router to determine
#                             that no stations are in a particular group. This
#                             version includes the ability for the receivers to
#                             gracefully exit from a multicast group.
#
#                        v3 - Specified in RFC 3376, this major revision of the
#                             IGMP protocol adds the ability to specify the
#                             source(s) to which a receiver is willing to
#                             listen. Sources can be stipulated with "include"
#                             filters in the "join" and "report" messages, or
#                             sources can be specifically rejected with
#                             "exclude" filters.
#
#    -intf_ip_addr  Specifies the first IPv4 address in the group. The default
#                   for IPv4 is 192.85.1.3.
#
#    -intf_ip_addr_step
#                   Specifies the difference between interface IP addresses of
#                   consecutive hosts when multiple IGMP hosts are created.
#                   The default increment is 1 (for example, 0.0.0.1). This
#                   argument is only applicable in create mode.
#
#    -intf_prefix_length
#                   Specifies the address prefix length on the emulated host,
#                   Possible values for IPv4 addresses range from 1 to 32; the
#                   default is 24,
#
#    -ip_router_alert
#                   Alerts transit routers to examine the contents of an IP
#                   packet more closely. When -ip_router_alert is set to 1,
#                   Spirent TestCenter enables the IP router alert option. This
#                   argument is always enabled (1 or true) in Spirent TestCenter
#                   whenever hosts send to routers. The IP router alert option
#                   is useful for new protocols that are addressed to a
#                   destination but require relatively complex processing in
#                   routers along the path. (See RFC 2113 for more information.)
#
#    -mode          Specifies the action to perform. Possible values are create,
#                   modify, and delete, This argument is required. The modes are
#                   described below:
#
#                   create - Starts emulating IGMP hosts on the specified port
#                        or handle.
#
#                   modify - Changes the configuration parameters for the IGMP
#                        hosts identified by either the -port or -handle
#                        argument.
#
#                   delete - Stops the IGMP emulation locally without attempting
#                        to clear the bound addresses from the IGMP server. In
#                        addition, all IGMP group sessions information on the
#                        port is cleared and the connection is restarted.
#
#    -msg_interval
#                   Maximum output rate of IGMP message packets generated per
#                   millisecond. Set this value to 0 to send messages as fast
#                   as possible. Possible values range from 0 to 4294967295. The
#                   default is 0.
#
#    -neighbor_intf_ip_addr
#                   Specifies the IP address of the interface for the IGMP
#                   neighbor (next hop) that will establish an adjacency with
#                   the DUT. The default for IPv4 is 192.85.1.1.
#
#    -neighbor_intf_ip_addr_step
#                   Specifies the difference between the IGMP neighbor's
#                   interface IP addresses when multiple IGMP hosts are created.
#                   The default is 0.0.0.0 (that is, the same address).
#
#    -older_version_timeout
#                   The amount of time (in 1/10 seconds) a host must wait after
#                   hearing a Version 1 Query before it may send any IGMPv2
#                   messages. Not used for IGMPv3. Possible values are 0 to
#                   4294967295. The default is 4000
#                   milliseconds.
#
#    -port_handle
#                   The handle of the port on which to create the emulated IGMP
#                   session. This argument is required.
#
#    -pppox_handle
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the handle to use when configuring IGMP over
#                   PPPoX.
#
#                   Note: The following arguments are ignored when configuring
#                   IGMP over PPPoX: -intf_ip_addr, -intf_ip_addr_step,
#                   -intf_prefix_len, -neighbor_intf_ip_addr,
#                   -neighbor_intf_ip_addr_step, -vlan_cfi, -vlan_id,
#                   -vlan_id_mode, -vlan_id_step, and -vlan_user_priority.
#
#    -robustness
#                   IGMPv3 only. Specifies the number of times to send a State
#                   Change Report. This number is used in the calculation of
#                   default values for various timers and counters. Possible
#                   values are 2 to 255. The default value is 2.
#
#    -suppress_report
#                   Always enabled. Valid values are 0 (false) and 1 (true).
#                   When -suppress_report is set to 1, Spirent TestCenter
#                   suppresses the transmission of a listener report that
#                   duplicates one received on the interface. Multicast hosts
#                   can suppress the transmission of reports to reduce the
#                   amount of multicast communication.
#
#    -vlan_cfi
#                   Sets the canonical format indicator field in VLAN for the
#                   emulated router node. Possible values are 0 (Ethernet) and 1
#                   (Token Ring). The default is 1. If set to 0, it indicates
#                   Token Ring and packets are dropped by Ethernet ports. If set
#                   to 0, it indicates the network is Ethernet.
#
#    -vlan_outer_cfi
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies whether the canonical format indicator (cfi) value
#                   is set for the VLAN outer header. Possible values are 0 or
#                   1.
#
#    -vlan_id
#                   Defines the VLAN ID of the first VLAN sub-interface.
#                   Possible values range from 0 to 4095. The default is 1. When
#                   the mode is either "create" or "enable", Spirent TestCenter
#                   checks for a vlan object on the port with the given vlan ID.
#                   If no vlan object with that ID exists, Spirent TestCenter
#                   creates a vlan object with the specified vlan ID.
#
#    -vlan_id_count
#                   Specifies the number of inner VLAN tags to generate for the
#                   stream. Possible values range from 1 to 4096. The default
#                   is 1.
#
#    -vlan_id_mode
#                   If you configure more than one interface on Spirent
#                   TestCenter with VLAN, you can choose to either automatically
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
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the VLAN ID for a particular outer header.
#                   Possible values range from 0 to 4095.
#
#    -vlan_id_outer_count
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the number of VLAN tags to generate for the
#                   outer header. Possible values range from 1 to 4096.
#                   The default is 1. You must set the -vlan_id_outer_mode
#                   argument to increment.
#
#    -vlan_id_outer_mode
#                   Spirent Extension (for Spirent TestCenter only).
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
#                   Spirent Extension (for Spirent TestCenter only).
#                   The amount by which to increment the specified outer VLAN ID
#                   (-vlan_id_outer) for subsequent packets. Possible values
#                   range from 0 to 32767. The default is 0.
#
#    -vlan_outer_user_priority
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the VLAN priority to assign to the outer header.
#                   Possible values range from 0 to 7. The default is 0.
#
#    -vlan_user_priority
#                   Defines the VLAN priority for the VLANs on this port.
#                   Possible values range from 0 to 7. The default is 0.
#
# Return Values:
#    The sth::emulation_igmp_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::emulation_igmp_config function creates, modifies, or deletes one
#    or more emulated IGMP hosts. Use the -mode argument to specify the action
#    to perform. (See the -mode argument description for information about the
#    actions.)
#
#    When you create an IGMP host, use the -port_handle argument to
#    specify the Spirent TestCenter port that the emulated IGMP host will
#    use for IGMP communication. (The port handle value is contained in the
#    keyed list returned by the  sth::connect function.)
#
#    Before you configure IGMP on a port, you must create the port, and use the
#    returned port handle in the call to the sth::emulation_igmp_config
#    function. The first time you call sth::emulation_igmp_config for a
#    particular port, you must specify "-mode create".
#
#    Spirent TestCenter supports the use of IGMP versions 1, 2, or 3 for
#    multicast group membership. To test IPv4 traffic with one of the Internet
#    Group Management Protocols, you use the Spirent TestCenter HLT API for:
#
#    - Generating multicast traffic
#    - Receiving multicast traffic
#    - Retrieving multicast results
#
#    IGMPv3 provides support for secure communication. Hosts can use Include
#    filters in the Join and Report messages to identify valid sources, or they
#    can use Exclude filters to reject sources. Routers will keep track of the
#    valid sources for every multicast group.
#
#    Note when using IGMP over PPPoX: Modifying any option during a PPPoE
#    session which currently is a member of a multicast group will sever the
#    PPPoE session, IGMP host, and multicast group relationship. Therefore, do
#    not use sth::pppox_config if the PPPoX engine is not idle. To see if the
#    PPoX engine is not idle, look at the aggregate.idle flag returned by
#    "sth::pppox_stats -mode aggregate". If aggregate.idle is "0", then do not
#    send sth::pppox_config. If the PPPoX engine is aborted, you will need to
#    reconfigure the PPPoX session. If using IGMP over PPPoX, you will also need
#    to reconfigure the IGMP session. (See Examples below).
#
#    For more information about the IGMP protocol, see RFC 1112 (IGMPv1), 2236
#    (IGMPv2), and 3376 (IGMPv3).
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent TestCenter 2.00.
#
#    -max_groups_per_pkts
#    -max_response_control
#    -max_response_time
#    -unsolicitied_report_interval
#
# Examples:
#    To create an IGMP session:
#
#    sth::emulation_igmp_config \
#         -port_handle $port_handle1 \
#         -mode create \
#         -igmp_version v3 \
#         -intf_ip_addr 10.41.1.2 \
#         -neighbor_intf_ip_addr 10.41.1.1
#
#    Output: {handles $port_handle1} {status 1}
#
#    To create an IGMP over PPPoE session:
#
#    set pppox_rL [sth::pppox_config -mode create -port_handle port1 ... ]
#
#    # Connect PPPoX
#    sth::pppox_control -action connect -handle [keylget pppox_rL handles]
#
#    #After all PPPoX sessions have finished connecting, create IGMP clients.
#    set igmp_rL [sth::emulation_igmp_config -handle [keylget pppox_rL handles]\
#         -mode create ...]
#
#    To modify an IGMP over PPPoE session:
#
#         Note: If you must modify the PPPoX configuration, modify
#         "sth::emulation_igmp_config" using the handle returned from
#         "sth::pppox_config -mode modify." Otherwise, the IGMP configuration
#         cannot be updated for the modified PPPoX configuration.
#
#    set pppox_rL [sth::pppox_config -handle host2 -mode modify... ]
#
#    # Connect PPPoX
#    sth::pppox_control -action connect -handle [keylget pppox_rL handles]
#
#    # After all PPPoX sessions have finished connecting, update IGMP using the
#    # handle from "sth::pppox_config -mode modify"
#    set igmp_rL [sth::emulation_igmp_config -handle [keylget pppox_rL handles]\
#         -mode modify ...]
#
#    To create an IGMP over DHCP session:
#
#    # Create DHCP port:
#    set dhcpport_rL [sth::emulation_dhcp_config -mode create -port_handle
#         port1 ...]
#    keylget rL handles dhcpport1
#
#    # Create the DHCP group
#    set dhcpgrp_rL [sth::emulation_dhcp_group_config -handle $dhcpport1 \
#         -mode create ...]
#    keylget rL handles dhcpgrp1
#
#    # Bind DHCP sessions
#    sth::emulation_dhcp_control -handle $dhcpgrp1 -action bind
#
#    # After all DHCP sessions have finished binding, create IGMP clients.
#    set igmp_rL [sth::emulation_igmp_config -handle $dhcpgrp1 -mode create ...]
#
#    To modify an IGMP over DHCP session:
#
#    # Modify the DHCP group
#    set dhcpgrp_rL [sth::emulation_dhcp_group_config -handle $dhcpgrp1  \
#         -mode modify ...]
#
#    # Bind DHCP sessions
#    sth::emulation_dhcp_control -handle $dhcpgrp1 -action bind
#
#    # After all DHCP sessions have finished binding, create IGMP clients.
#    set igmp_rL [sth::emulation_igmp_config -handle $dhcpgrp1 -mode modify ...]
#
# Sample Input:
#    See Examples.
#
# Sample output:
#    See Examples.
#
# Notes:
#    None.
#
# End of Procedure Header
#
#
#
#
##Procedure Header
#
# Name:
#    sth::emulation_igmp_control
#
# Purpose:
#    Start, stop, or restart the IGMP host on the
#    specified port. Leaves and joins group pools.
#
# Synopsis:
#    sth::emulation_igmp_control
#         -port_handle <handle>
#         -mode {restart|join|leave}
#         [-handle <IGMP_session_handle>]
#         [-leave_join_delay <0-4294967295>]
#         [-data_duration <0-4294967295>]
#         [-calculate_latency {0|1} ]
#
# Arguments:
#
#    -handle        Identifies the groups to stop, start, restart, join, or
#                   leave. This value is returned by the
#                   sth::emulation_igmp_group_config function. If you do not
#                   specify a group, the specified action is applied to all
#                   groups configured on the port specified by -port_handle.
#                   This value appears in the keyed list returned by the
#                   sth::emulation_igmp_group_config function. This argument is
#                   required when -port_handle is not used.
#
#    -mode          Specifies the action to perform on the specified handle. If
#                   you provide a handle (-handle), this argument performs the
#                   specified action on all groups on this session. If you do 
#                   not provide a handle, this argument performs the specified
#                   action on all groups on all sessions. Possible values are
#                   start, restart, join, and leave. You must specify one of
#                   these values. The modes are described below:
#
#                   restart - Stops and then restarts the groups specified by
#                        -handle on the specified port. If you do not provide 
#                        a handle, this action stops and restarts all groups
#                        on all ports.
#
#                   join - Joins all groups specified by -handle. If you
#                        do not provide a handle, this action joins all groups
#                        on all ports.  
#
#                   leave - Leave all groups specified by -handle. If you
#                        do not provide a handle, this action leaves all groups
#                        on all ports.  
#
#                        Note: You must send the "leave" actions before
#                        disconnecting PPPoX sessions. Otherwise, if you
#                        disconnect a PPPoX session before sending "leaves",
#                        HLTAPI will not automatically send the "leaves".
#
#    -calculate_latency
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies whether to calculate latencies when joining  or 
#                   leaving multicast groups. Possible values are 0 (do not 
#                   calculate latency) and 1 (calculate latency). If set to 1
#                   during an IGMP Join, HLTAPI cannot capture the IGMP
#                   dataplane packets because the analyzer stops to collect
#                   packets so it can calculate latency.
#
#    -leave_join_delay
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the amount of time, in seconds, between joins and
#                   leaves. The default is 0.
#
#    -data_duration
#                   Spirent Extension (for Spirent TestCenter only).
#                   Specifies the amount of time, in seconds, to wait after 
#                   sending joins or leaves before latencies are calculated. The 
#                   default is 10.
#
#    -port_handle
#                   Identifies the handle of the port on which to take the
#                   action. This is the port on which IGMP emulation
#                   has been configured. This value is returned by the
#                   sth::emulation_igmp_config function. This argument is
#                   required when -handle is not used.
#
# Cisco-specific Arguments:
#    The -group_member_handle argument is specific to the Cisco HLTAPI but is
#    not supported by Spirent TestCenter 2.00.
#
# Return Values:
#     The function returns a keyed list using the following keys (with
#     corresponding data):
#
#     status     Success (1) or failure (0) of the operation.
#     log        An error message (if the operation failed).
#
# Description:
#    The sth::emulation_igmp_control function stops, starts, or restarts the
#    IGMP protocol on the hosts on the specified port. You can also use this
#    function to send a Join or Leave message from the host to inform a router
#    that the host is either joining the multicast group specified by handle or
#    port_handle or terminating its membership in the specified multicast group,
#
#    When you call the sth::emulation_igmp_control function, you
#    specify a port handle. Spirent TestCenter applies the specified action to
#    all of the emulated IGMP hosts associated with the specified port.
#
#    IPv4 multicast traffic is based on group membership established and
#    maintained with IGMP. Hosts and adjacent routers exchange IGMP messages to
#    establish multicast group membership.
#
#    When a host wants to participate in a multicast group, it sends an
#    IGMP "join" message to its local router. After a router receives one or
#    more "joins" for a specific group, it forwards any packets destined for
#    that particular group to the appropriate interface(s). The router regularly
#    verifies that the hosts want to continue to participate in the
#    multicast groups by sending periodic "queries" to the receivers.
#
#    When a host is no longer interested in multicast group participation, it
#    sends a "leave" message to the router (IGMPv2 and IGMPv3 only).
#
# Examples:
#    The following example joins all groups specified by -handle:
#
#    sth::emulation_igmp_control
#         -mode join
#         -handle $IGMPSessionHandle
#
#    The following example removes the groups specified by -handle
#    from the hosts on the specified port:
#
#    sth::emulation_igmp_control
#         -mode leave
#         -handle $IGMPSessionHandle
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
#
#
##Procedure Header
#
# Name:
#    sth::emulation_igmp_group_config
#
# Purpose:
#    Creates group pools and source pools, and modifies and deletes group and
#    source pools from IGMP hosts. This function configures multicast group
#    ranges for an emulated IGMP host.You must use the common
#    sth::multicast_group_config and sth::multicast_source_config functions with
#    this function.
#
# Synopsis:
#    sth::emulation_igmp_group_config
#         { [-mode create -port_handle <port_handle> |
#            -mode {create|modify|delete|clear_all}
#           -handle <IGMP_group_config_handle>} ]
#         }
#         [-group_pool_handle <multicast_group_pool_handle>]
#         [-session_handle <igmp_session_handle>]
#         [-source_pool_handle <multicast_source_pool_handle>]
#
# Arguments:
#
#    -group_pool_handle
#                   Specifies the name of the group (that is, the list of
#                   multicast IP addresses) to link to the IGMP host during
#                   create mode. Before specifying the group pool handle, use
#                   the sth::emulation_multicast_group_config function to add
#                   the group pool. See "Multicast APIs" in this documentation
#                   set for information about the
#                   sth::emulation_multicast_group_config and
#                   sth::emulation_multicast_source_config functions.
#
#    -handle
#                   Sets group membership handle that associates group pools
#                   with an IGMP host. In modify mode, membership handle must be
#                   used in conjunction with the session handle to identify the
#                   multicast group pools.
#
#                   For "-mode create", the handle is returned by the
#                   sth::emulation_igmp_config function. Mode "modify" returns
#                   the same handle passed in.
#
#                   Note:  The IGMP hosts, specified by -handle, join the
#                   multicast groups, specified by the -group_pool_handle. So,
#                   both arguments are required for "-mode create", but
#                   -group_pool_handle is optional for "-mode modify".
#
#    -mode          Specifies the action to perform. Possible values are create,
#                   modify, and reset. There is no default; you must specify a
#                   mode. The modes are described below:
#
#                   create - Starts emulation on the port specified with
#                        -handle and associates an existing multicast group
#                        pool (-group_pool_handle) with the specified IGMP host
#                        (that is,joins the membership).
#
#                   modify - Changes the configuration identified by the -handle
#                        argument by applying the parameters specified in
#                        subsequent arguments.
#
#                   delete - Remove one group of pools from this session.
#
#                   clear_all - Remove all group pools from this session.
#
#    -session_handle
#                   Specifies the handle of the IGMP host on which to configure
#                   the IGMP group ranges.
#
#    -source_pool_handle
#                   Specifies the name of the source pool (that is, the list of
#                   non-multicast source IP addresses) to associate with the
#                   groups during create mode. Each multicast group may contain
#                   0 or more of these source IP addresses. Use this argument if
#                   the host only wants specific information within the
#                   specified multicast group (-group_pool_handle). Specifying
#                   the source pool handle along with the group pool handle in
#                   the sth::emulation_igmp_group_config function adds the
#                   range of source IP addresses to each multicast group.
#
#                   Before specifying the source pool handle, use the
#                   sth::emulation_multicast_source_config function to add
#                   the source pools. See "Multicast APIs" in this documentation
#                   set for information about the
#                   sth::emulation_multicast_source_config and
#                   sth::emulation_multicast_group_config functions.
#
# Return Values:
#    The sth::emulation_igmp_group_config function returns a keyed
#    list using the following keys (with corresponding data):
#
#    handle
#              Identifies the handle of the group (IGMP_group_config_handle) 
#              created by the sth::emulation_igmp_group_config function.
#
#    group_pool_handle
#              Identifies the group pool handle used by the
#              sth::emulation_igmp_group_config function to configure or modify
#              the group member.
#
#    source_pool_handle
#              Identifies the source pool handle used by the
#              sth::emulation_igmp_group_config function to configure or modify
#              the group member.
#
#    status
#              Success (1) or failure (0) of the operation.
#
#    log
#              An error message (if the operation failed).
#
# Description:
#    The sth::emulation_igmp_group_config function configures or
#    modifies a group of IGMP hosts where each group share a
#    set of common characteristics. Use the -mode argument to specify
#    the action to perform. (See the -mode argument description for information
#    about the actions.)
#
#    Before using this function, you must specify "-mode create" when
#    configuring IGMP host emulation on a port and initialize the port handle
#    argument (using the sth::emulation_igmp_config function).
#
#    You can link groups of multicast IP addresses to any interested host or
#    just a subset of IP addresses within each group.
#
#    Each multicast IP address directs the information it represents to any host
#    interested in subscribing to it. In the following example, the object
#    represented by MGroupHandle contains 229.0.0.1 & 229.0.0.2.  The host
#    handle "hostHandle" has the IP address 3.0.0.1.
#
#    sth::emulation_igmp_group_config \
#          -mode create \
#          -group_pool_handle $MGroupHandle \
#          -session_handle $hostHandle
#
#    The following illustration shows that host 3.0.0.1 subscribes to both
#    multicast group 229.0.0.1 and 229.0.0.2.
#
#         Host 3.0.0.1
#               *
#         *****************
#         *               *
#    *************   *************
#    *  MGroup1  *   *  MGroup2  *
#    * 229.0.0.1 *   * 229.0.0.2 *
#    *************   *************
#
#    To subscribe to only one or more particular IP addresses that exist within
#    a multicast group, you must use the -source_pool_handle as well. Specifying
#    the source_pool_handle along with the group_pool_handle in the
#    sth::emulation_igmp_group_config function, adds the range of source IP
#    addresses to each multicast group. Adding the source_pool_handle
#    SGroupHandle (which contains source IP addresses 1.1.1.1 and 1.1.1.2)
#    option to the above example results in:
#
#    sth::emulation_igmp_group_config \
#          -mode create \
#          -group_pool_handle $MGroupHandle \
#          -session_handle $hostHandle \
#          -source_pool_handle $SGroupHandle
#
#    The following illustration shows that host 3.0.0.1 subscribes to source
#    1.1.1.1 and 1.1.1.2 which exist in both multicast groups 229.0.0.1 and
#    229.0.0.2..
#
#         Host 3.0.0.1
#               *
#         *****************
#         *               *
#    *************   *************
#    *  MGroup1  *   *  MGroup2  *
#    * 229.0.0.1 *   * 229.0.0.2 *
#    *************   *************
#    *************   *************
#    *  Source1  *   *  Source1  *
#    *  1.1.1.1  *   *  1.1.1.1  *
#    *  Source2  *   *  Source2  *
#    *  1.1.1.2  *   *  1.1.1.2  *
#    *************   *************
#
#
# Examples:
#    The following example configures the hosts, represented by
#    "igmpSessionHandle", to subscribe to the multicast group(s) represented by
#    "multicastGroupPoolHandle(1)":
#
#     sth::emulation_igmp_group_config \
#         -mode create \
#         -group_pool_handle $multicastGroupPoolHandle(1) \
#         -session_handle $igmpSessionHandle
#
#
#    The following example causes all hosts on the port, represented by the port
#    handle "portHandle", to send "leave" messages to the multicast groups to
#    which they are currently subscribed. These multicast groups were set using
#    the sth::emulation_igmp_group_config function:
#
#     sth::emulation_igmp_group_config \
#         -mode clear_all \
#         -handle $IGMPgroupconfighandle
#
# Sample Input:
#    See Examples.
#
# Sample output for example 1 shown above:
#    {status 1} {handle igmphostconfig1}
#
# Notes:
#     None
#
# End of Procedure Header
#
#
##Procedure Header
#
# Name:
#    sth::emulation_igmp_info
#
# Purpose:
#    Returns statistics about the IGMP group activity on the specified handle.
#    Statistics include the connection status and number and type of messages
#    sent and received from the specified port.
#
# Synopsis:
#    sth::emulation_igmp_info
#         [-handle <igmp_session_handle>]
#
# Arguments:
#
#    -handle   Specifies the IGMP session handle upon which host emulation is
#              configured. This argument is required. This value is returned by
#              the sth::emulation_igmp_config function.
#
# Return Values:
#    The sth::emulation_igmp_info function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
#    invalid_pkts
#                   Number of invalid IGMP packets received. Invalid
#                   IGMP packets include:
#                        invalid IGMP checksum
#                        invalid packet length
#                        invalid IGMP types
#
#    dropped_pkts
#                   Will always return 0 because Spirent TestCenter currently
#                   does not drop valid IGMP packets.
#
#    host_addr
#                   IP address of host whose group membership stats are being
#                   displayed.
#
#    group_addr
#                   Group membership IP address of host whose group membership
#                   stats are being displayed.
#
#    group_membership_stats
#                   List of group membership statistics.
#
#    state          State of group membership of host whose group membership
#                   stats are being displayed. Possible returned values
#                   are:
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
#                   RETRYING_MEMBER - This state applies to IGMPv1/IGMPv2 hosts
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
#                   The time, in milliseconds, between sending the IGMP join and
#                   receiving the multicast data for the channel specified in
#                   the join message. This value is valid only when 
#                   "sth::emulation_igmp_control -calculate_latency" is set to 
#                   1.
#
#    leave_latency
#                   The time, in milliseconds, between sending the IGMP leave
#                   for a channel and when multicast data has stopped being
#                   received. This value is valid only when 
#                   "sth::emulation_igmp_control -calculate_latency" is set to 
#                   1.
#
#    The following IGMP port statistics are also returned:
#
#    igmpv1_queries_rx        IGMPv1 Host membership query messages are sent to
#                             discover which group have members.
#
#                             Note: Group- and source-specific queries are sent
#                             by a multicast router whenever a host leave a
#                             specific source of a group. This is to make sure
#                             that there are no other hosts of that source and
#                             group.
#
#    igmpv1_mem_reports_tx    IGMPv1 reports are sent to multicast routers to
#                             indicate that hosts have listeners interested in
#                             joining multicast groups whose multicast address
#                             is listed in the router's list.
#
#    igmpv1_mem_reports_rx    IGMPv1 reports are sent to multicast routers to
#                             indicate that hosts have listeners interested in
#                             joining multicast groups whose multicast address
#                             is listed in the router's list.
#
#    igmpv2_queries_rx        Routers use Multicast Listener Query messages to
#                             query a subnet for multicast listeners.
#
#    igmpv2_group_queries_rx  This statistic might be included in the
#                             RxGroupAndSourceSpecificQueryCount port results
#                             attributes, but it is not returned as an
#                             individual statistic. Also, see "Note" for
#                             "igmpv1_group_queries_rx" above.
#
#    igmpv2_mem_reports_tx    Similar to IGMPv1 reports, IGMPv2 reports are sent
#                             by IGMPv2 hosts if they detect an IGMPv2 router.
#
#    igmpv2_mem_reports_rx    Similar to IGMPv1 reports, IGMPv2 reports are sent
#                             by IGMPv2 hosts if they detect an IGMPv2 router.
#
#    igmpv2_leave_tx          This statistic is included in the
#                             TxLeaveGroupCount port results attributes, but it
#                             is not returned as an
#
#    igmpv3_queries_rx        IGMPv3 Membership Queries are sent by IP multicast
#                             routers to query the multicast reception state of
#                             neighboring interfaces.
#
#    igmpv3_group_queries_rx  This statistic might be included in the
#                             RxGroupAndSourceSpecificQueryCount port results
#                             attributes, but it is not returned as an
#                             individual statistic. Also, see "Note" for
#                             "igmpv1_group_queries_rx" above.
#
#    igmpv3_group_src_queries_rx
#                             This statistic might be included in the
#                             RxGroupAndSourceSpecificQueryCount port results
#                             attributes, but it is not returned as an
#                             individual statistic. Also, see "Note" for
#                             "igmpv1_group_queries_rx" above.
#
#    igmpv3_mem_reports_tx    While functionally similar to IGMPv2 reports,
#                             IGMPv3 reports add support for source filtering.
#                             This means a host may report interest in receiving
#                             packets only from specific addresses. Or, from all
#                             but specific addresses sent to a multicast
#                             address. This information may be used to avoid
#                             delivering multicast packets from specific sources
#                             to networks where there are no interested hosts.
#
#    igmpv3_mem_reports_rx    While functionally similar to IGMPv2 reports,
#                             IGMPv3 reports add support for source filtering.
#                             This means a host may report interest in receiving
#                             packets only from specific addresses. Or, from all
#                             but specific addresses sent to a multicast
#                             address. This information may be used to avoid
#                             delivering multicast packets from specific sources
#                             to networks where there are no interested hosts.
#
#    The following session statistics are returned:
#
#    session                  Session statistics for all multicast groups.
#
#    session.<IGMP session handle>
#                             Displays all session statistics for the specified
#                             session handle.
#
#    session.<IGMP session handle>.max_join_latency
#                             Maximum join latency for the specified session
#                             handle.
#
#    session.<IGMP session handle>.min_join_latency
#                             Minimum join latency for the specified session
#                             handle.
#
#    session.<IGMP session handle>.avg_join_latency
#                             Average join latency for the specified session
#                             handle.
#
#    session.<IGMP session handle>.min_leave_latency
#                             Minimum leave latency for the specified session
#                             handle.
#
#    session.<IGMP session handle>.max_leave_latency
#                             Maximum leave latency for the specified session
#                             handle.
#
#    session.<IGMP session handle>.avg_leave_latency
#                             Average leave latency for the specified session
#                             handle.
#
# Description:
#    The sth::emulation_igmp_info function retrieves statistics about the
#    number of invalid and dropped packets on the specified host as well as
#    several port and session statistics.
#
# Examples:
#    When you call sth::emulation_igmp_info, the contents of the returned keyed
#    list depends on the status of the call. For example:
#
#    sth::emulation_igmp_info -handle $handle1
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
#    {group_membership_stats {{{host_addr 44.1.0.2} {group_addr 239.0.0.1}
#    {state IDLE_MEMBER} {join_latency 0.000000} {leave_latency 0.000000}}
#    {{host_addr 44.1.0.2} {group_addr 239.0.0.2} {state IDLE_MEMBER}
#    {join_latency 0.000000} {leave_latency 0.000000}} {{host_addr 44.1.0.2}
#    {group_addr 239.0.0.3} {state IDLE_MEMBER} {join_latency 0.000000}
#    {leave_latency 0.000000}} {{host_addr 44.1.0.2} {group_addr 239.0.0.4}
#    {state DELAYING_MEMBER} {join_latency 0.000000} {leave_latency 0.000000}}}}
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

namespace eval ::sth {
   proc emulation_igmp_config {args} {
      variable ::sth::igmp::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::igmp::userArgsArray
      array set ::sth::igmp::userArgsArray {}

      set returnKeyedList ""

      set retVal [catch {
         ::sth::sthCore::Tracker emulation_igmp_config $args
         if {[catch {::sth::sthCore::commandInit \
               ::sth::igmp::igmpTable \
               $args \
               ::sth::igmp:: \
               emulation_igmp_config \
               ::sth::igmp::userArgsArray \
               sortedSwitchPriorityList \
            } err]} {
            ::sth::sthCore::processError returnKeyedList $err {}
            return $returnKeyedList
         }

         set mode $::sth::igmp::userArgsArray(mode)

         switch -exact $mode {
            create {
               ::sth::igmp::emulation_igmp_config_create returnKeyedList
            }

            modify {
               ::sth::igmp::emulation_igmp_config_modify returnKeyedList
            }

            delete {
               ::sth::igmp::emulation_igmp_config_delete returnKeyedList
            }

            enable -
            enable_all {
               ::sth::igmp::emulation_igmp_config_enable_all returnKeyedList
            }

            disable -
            disable_all {
               ::sth::igmp::emulation_igmp_config_disable_all returnKeyedList
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

   proc emulation_igmp_control {args} {

      variable ::sth::igmp::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::igmp::userArgsArray
      array set ::sth::igmp::userArgsArray {}

      set returnKeyedList ""

      ::sth::sthCore::Tracker emulation_igmp_control $args
      if {[catch {::sth::sthCore::commandInit \
            ::sth::igmp::igmpTable \
            $args \
            ::sth::igmp:: \
            emulation_igmp_control \
            ::sth::igmp::userArgsArray \
            sortedSwitchPriorityList \
         } err]} {
	::sth::sthCore::processError returnKeyedList $err {}
         return $returnKeyedList
      }

      set retVal [catch {
         set deviceList ""

         if {[info exists ::sth::igmp::userArgsArray(handle)]} {
            set userArgsArray(handle) [::sth::igmp::emulation_igmp_config_getIgmpHostCfgList $userArgsArray(handle)]
            set deviceList $::sth::igmp::userArgsArray(handle)
         } elseif {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            foreach port $::sth::igmp::userArgsArray(port_handle) {
                foreach host [::sth::sthCore::invoke stc::get $port -affiliationport-Sources] {
                   append deviceList " [::sth::sthCore::invoke stc::get $host -children-igmpHostConfig]"
                }
            }
         }

         switch $::sth::igmp::userArgsArray(mode) {
            join  { set deviceCmd "IgmpMldJoinGroupsCommand" }
            leave { set deviceCmd "IgmpMldLeaveGroupsCommand" }
            restart {
               ::sth::sthCore::invoke stc::perform IgmpMldLeaveGroups -blockList $deviceList
               ::sth::sthCore::invoke stc::perform ResultsClearAll -Project $::sth::GBLHNDMAP(project)
               set deviceCmd "IgmpMldJoinGroupsCommand"
            }
            default {
               return -code error [concat "Error:  Unsupported IGMP " \
                     "control mode \"$::sth::igmp::userArgsArray(mode)\".  "]
            }
         }

         if {[llength $deviceList] > 0} {
            if {$::sth::igmp::userArgsArray(calculate_latency)} {
               set calcLatency "TRUE"
            } else {
               set calcLatency "FALSE"
            }

            #Get sequencer handle before config
            set seqHandle [::sth::sthCore::invoke  "stc::get system1 -children-Sequencer"]
          
            ::sth::sthCore::invoke stc::config $seqHandle [list -CommandList ""]
            set seqLoopCmd [::sth::sthCore::invoke stc::create "SequencerLoopCommand" -under [::sth::sthCore::invoke stc::get $seqHandle -Parent] [list -IterationCount "1" -ExecutionMode "BACKGROUND" -GroupCategory "CLEANUP_COMMAND" -ContinuousMode "FALSE" -AutoDestroy "FALSE" -ExecuteSynchronous "FALSE"]]
            #set WaitForTxReports to "FALSE". The command may hang otherwise.
            set igmpMldCmd [::sth::sthCore::invoke stc::create $deviceCmd -under $seqHandle [list -calculateLatency $calcLatency -blockList $deviceList -WaitForTxReports "FALSE" -RxDataDuration $::sth::igmp::userArgsArray(data_duration) -JoinLeaveDelay $::sth::igmp::userArgsArray(leave_join_delay)]]
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

   proc emulation_igmp_group_config {args} {
      variable ::sth::igmp::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::igmp::userArgsArray
      array set ::sth::igmp::userArgsArray {}

      set returnKeyedList ""

      ::sth::sthCore::Tracker emulation_igmp_group_config $args
      if {[catch {::sth::sthCore::commandInit \
            ::sth::igmp::igmpTable \
            $args \
            ::sth::igmp:: \
            emulation_igmp_group_config \
            ::sth::igmp::userArgsArray \
            sortedSwitchPriorityList \
         } err]} {
         ::sth::sthCore::processError returnKeyedList $err {}
         return $returnKeyedList
      }

      set mode $::sth::igmp::userArgsArray(mode)

      set retVal [catch {
         switch -exact $mode {
            create {
               ::sth::igmp::emulation_igmp_group_config_create returnKeyedList
            }

            modify {
               ::sth::igmp::emulation_igmp_group_config_modify returnKeyedList
            }

            delete {
               ::sth::igmp::emulation_igmp_group_config_delete returnKeyedList
            }

            clear_all {
               ::sth::igmp::emulation_igmp_group_config_clear_all \
                     returnKeyedList
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

   proc emulation_igmp_info {args} {
      variable ::sth::igmp::userArgsArray
      variable sortedSwitchPriorityList

      array unset ::sth::igmp::userArgsArray
      array set ::sth::igmp::userArgsArray {}

      set returnKeyedList ""

      ::sth::sthCore::Tracker emulation_igmp_info $args
    if {[catch {::sth::sthCore::commandInit \
          ::sth::igmp::igmpTable \
          $args \
          ::sth::igmp:: \
          emulation_igmp_info \
          ::sth::igmp::userArgsArray \
          sortedSwitchPriorityList \
       } err]} {
       ::sth::sthCore::processError returnKeyedList $err {}
       return $returnKeyedList
    }
    
    if {[string equal $::sth::igmp::userArgsArray(mode) "clear_stats"]} {
        if {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            set portList $::sth::igmp::userArgsArray(port_handle)
        } elseif {[info exists ::sth::igmp::userArgsArray(handle)]} {
            set userArgsArray(handle) [::sth::igmp::emulation_igmp_config_getIgmpHostCfgList $userArgsArray(handle)]
            set portList [::sth::sthCore::invoke stc::get [::sth::sthCore::invoke stc::get $::sth::igmp::userArgsArray(handle) -parent] -AffiliationPort-Targets]
        } else {
            ::sth::sthCore::processError returnKeyedList "Either -port_handle or handle should be provided"
            return $returnKeyedList
        }
        if {[catch {::sth::sthCore::invoke stc::perform ResultsClearAll -PortList $portList} err ] } {
                        ::sth::sthCore::processError returnKeyedList "stc::perform ResultsClearAll -Project $::sth::GBLHNDMAP(project) Failed: $err"
                        return $returnKeyedList
            }
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
        return $returnKeyedList
    }
    
    set retVal [catch {
      if {$::sth::igmp::igmp_subscription_state == 0} {
          # Create an IGMP port dataset
          set portResultDataSet \
          [::sth::igmp::emulation_igmp_config_create_resultDataset \
              "IgmpPortConfig" \
              "IgmpPortResults" \
              [list \
                  "multicastportresults.txgroupandsourcespecificquerycount" \
                  "multicastportresults.rxgroupandsourcespecificquerycount" \
                  "multicastportresults.rxv1querycount" \
                  "multicastportresults.txv1reportcount" \
                  "multicastportresults.rxv1reportcount" \
                  "multicastportresults.rxv2querycount" \
                  "multicastportresults.txv2reportcount" \
                  "multicastportresults.rxv2reportcount" \
                  "igmpportresults.txleavegroupcount" \
                  "igmpportresults.rxv3querycount" \
                  "igmpportresults.txv3reportcount" \
                  "igmpportresults.rxv3reportcount" \
                  "multicastportresults.rxunknowntypecount" \
                  "igmpportresults.rxigmpchecksumerrorcount" \
                  "igmpportresults.rxigmplengtherrorcount"] \
          ]
          # Create an IGMP group membership dataset
          set igmpGroupMembershipResultDataSet \
              [::sth::igmp::emulation_igmp_config_create_resultDataset \
                  "IgmpGroupMembership" \
                  "IgmpGroupMembershipResults" \
                      [list "igmpgroupmembershipresults.hostaddr" \
                          "igmpgroupmembershipresults.groupaddr" \
                          "multicastgroupmembershipresults.state" \
                          "multicastgroupmembershipresults.joinlatency" \
                          "multicastgroupmembershipresults.leavelatency"] \
              ]
      
          set igmpResultsDataSet \
              [::sth::igmp::emulation_igmp_config_create_resultDataset \
                  "IgmpHostConfig" \
                  "IgmpHostResults" \
                  [list "igmphostresults.minjoinlatency" \
                      "igmphostresults.maxjoinlatency" \
                      "igmphostresults.avgjoinlatency" \
                      "igmphostresults.minleavelatency" \
                      "igmphostresults.maxleavelatency" \
                      "igmphostresults.avgleavelatency"] \
              ]


          # Subscribe to the datasets
          ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $portResultDataSet
          ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $igmpGroupMembershipResultDataSet
          ::sth::sthCore::invoke stc::perform ResultDataSetSubscribe -ResultDataSet $igmpResultsDataSet
          
          set ::sth::igmp::igmp_subscription_state 1
          ::sth::sthCore::invoke stc::sleep 3
      }
      if {![info exists igmpGroupMembershipResultDataSet] } {
          # if the value of ::sth::igmp::igmp_subscription_state is 1, need to get the resultdataset handle
          set resultDataSets [::sth::sthCore::invoke stc::get $::sth::GBLHNDMAP(project) -children-resultdataset]
          foreach resultDataSet $resultDataSets {
              set configClassID [::sth::sthCore::invoke stc::get $resultDataSet.resultquery -configclassid]
              switch -exact $configClassID {
                  "igmpgroupmembership" {
                      set igmpGroupMembershipResultDataSet $resultDataSet
                  }
                  "igmphostconfig" {
                      set igmpResultsDataSet $resultDataSet 
                  }
                  default {
                      continue
                  }
              }
          }
      }
      set igmpPortList ""
      set groupMembershipStats ""
      array unset groupAddrStats
      set igmpGroupMemberShips ""
      if {[info exists ::sth::igmp::userArgsArray(handle)]} {
         set userArgsArray(handle) [::sth::igmp::emulation_igmp_config_getIgmpHostCfgList $userArgsArray(handle)]
         set igmpHostConfigs $::sth::igmp::userArgsArray(handle)
         foreach igmpHostConfig $igmpHostConfigs {
            set igmpGroupMemberShips [concat $igmpGroupMemberShips [::sth::sthCore::invoke stc::get $igmpHostConfig -children-igmpgroupmembership]]
         }
         # Group membership statistics
         # US42078 result subscription from multiple pages is not supported in emulation_igmp_info API
         # process pageNum for igmpGroupMembershipResultDataset
         set groupPageCount [::sth::sthCore::invoke stc::get $igmpGroupMembershipResultDataSet -totalPageCount]
         for {set groupPageNum 1} {$groupPageNum <= $groupPageCount} {incr groupPageNum} {
             if {$groupPageNum > 1} {
                 ::sth::sthCore::invoke stc::config $igmpGroupMembershipResultDataSet -pageNumber $groupPageNum
                 ::sth::sthCore::invoke stc::apply
             }
             foreach groupMembershipResult [::sth::sthCore::invoke stc::get $igmpGroupMembershipResultDataSet -resultHandleList] {
                 set groupStats [::sth::sthCore::invoke stc::get $groupMembershipResult]
                 array set groupStatsArray $groupStats
                 if {[lsearch $igmpGroupMemberShips $groupStatsArray(-parent)] > -1} {
                     set iHostStat [join \
                         [list \
                             "group_addr" $groupStatsArray(-GroupAddr) "host_addr"  $groupStatsArray(-HostAddr)] "."]
                     #return the value of join_timestamp,leave_timestamp,join_failure,duplicate_join and state_change_timestamp
                     keylset groupMembershipStats "$iHostStat.state" $groupStatsArray(-State)
                     keylset groupMembershipStats "$iHostStat.state_change_timestamp" $groupStatsArray(-StateChangeTimestamp)
                     keylset groupMembershipStats "$iHostStat.join_timestamp" $groupStatsArray(-JoinTimestamp)
                     keylset groupMembershipStats "$iHostStat.leave_timestamp" $groupStatsArray(-LeaveTimestamp)
                     keylset groupMembershipStats "$iHostStat.join_latency" $groupStatsArray(-JoinLatency)
                     keylset groupMembershipStats "$iHostStat.leave_latency" $groupStatsArray(-LeaveLatency)
                     keylset groupMembershipStats "$iHostStat.join_failure" $groupStatsArray(-JoinFail)
                     keylset groupMembershipStats "$iHostStat.duplicate_join" $groupStatsArray(-DuplicateJoin)
                     array unset groupStatsArray
                     set groupStats ""
                 }
             }
         }
         # US42078 result subscription from multiple pages is not supported in emulation_igmp_info API
         # process pageNum for igmpResultsDataSet
         set igmpPageCount [::sth::sthCore::invoke stc::get $igmpResultsDataSet -totalPageCount]
         for {set igmpPageNum 1} {$igmpPageNum <= $igmpPageCount} {incr igmpPageNum} {
             if {$igmpPageNum > 1} {
                 ::sth::sthCore::invoke stc::config $igmpResultsDataSet -pageNumber $igmpPageNum
                 ::sth::sthCore::invoke stc::apply
             }
             # IGMP session statistics
             #set sessionResults [::sth::sthCore::invoke stc::get $igmpHostConfig -resultchild-Targets]
             foreach sessionResult [::sth::sthCore::invoke stc::get $igmpResultsDataSet -resultHandleList] {
                 set sessionStats [::sth::sthCore::invoke stc::get $sessionResult]
                 array set sessionStatsArray $sessionStats
                 if {[lsearch $igmpHostConfigs $sessionStatsArray(-parent)] >-1} {
                     keylset igmpSessionStats "$sessionStatsArray(-parent).min_join_latency" $sessionStatsArray(-MinJoinLatency)
                     keylset igmpSessionStats "$sessionStatsArray(-parent).max_join_latency" $sessionStatsArray(-MaxJoinLatency)
                     keylset igmpSessionStats "$sessionStatsArray(-parent).avg_join_latency" $sessionStatsArray(-AvgJoinLatency)
                     keylset igmpSessionStats "$sessionStatsArray(-parent).min_leave_latency" $sessionStatsArray(-MinLeaveLatency)
                     keylset igmpSessionStats "$sessionStatsArray(-parent).max_leave_latency" $sessionStatsArray(-MaxLeaveLatency)
                     keylset igmpSessionStats "$sessionStatsArray(-parent).avg_leave_latency" $sessionStatsArray(-AvgLeaveLatency)
                     array unset sessionStatsArray
                     set sessionStats ""
                 }
             }
         }
         # set pageNumber as 1
         ::sth::sthCore::invoke stc::config $igmpGroupMembershipResultDataSet -pageNumber 1
         ::sth::sthCore::invoke stc::config $igmpResultsDataSet -pageNumber 1
         ::sth::sthCore::invoke stc::apply
      }
         # Port statistics
        if {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            array unset stats
            set stats(igmpv1_queries_rx) 0
            #set stats(igmpv1_group_queries_rx) 0
            set stats(igmpv1_mem_reports_tx) 0
            set stats(igmpv1_mem_reports_rx) 0
            set stats(igmpv2_queries_rx) 0
            set stats(igmpv2_group_queries_rx) 0
            set stats(igmpv2_mem_reports_tx) 0
            set stats(igmpv2_mem_reports_rx) 0
            set stats(igmpv2_leave_tx) 0
            set stats(igmpv3_queries_rx) 0
            set stats(igmpv3_group_queries_rx) 0
            set stats(igmpv3_group_src_queries_rx) 0
            set stats(igmpv3_mem_reports_tx) 0
            set stats(igmpv3_mem_reports_rx) 0
            set stats_invalid_pkts 0

            foreach igmpPort $::sth::igmp::userArgsArray(port_handle) {
               set igmpPortConfig [::sth::sthCore::invoke stc::get $igmpPort -children-igmpPortConfig]
               set igmpPortResults [::sth::sthCore::invoke stc::get $igmpPortConfig -children-igmpPortResults]

               foreach stat [array names stats] {
                  set s [::sth::sthCore::getswitchprop ::sth::igmp:: \
                        emulation_igmp_info $stat stcattr]
                  incr stats($stat) [::sth::sthCore::invoke stc::get $igmpPortResults "-$s"]
               }

               foreach invalid_pkt_stat [::sth::sthCore::getswitchprop \
                     ::sth::igmp:: emulation_igmp_info invalid_pkts stcattr] {
                  incr stats_invalid_pkts [::sth::sthCore::invoke stc::get $igmpPortResults "-$s"]
               }

               # Spirent TestCenter 2.0 does not drop valid IGMP packets.  So
               # always set this statistic to 0.
               set stats(dropped_pkts) 0
               keylset portStats \
                     ${::sth::igmp::userArgsArray(port_handle)}.-.invalid_pkts \
                     $stats_invalid_pkts
            }

            foreach stat [array names stats] {
                
                if {![string compare -length 6 $stat "igmpv1"]} {
                    keylset portStats  ${::sth::igmp::userArgsArray(port_handle)}.V1.$stat  $stats($stat)
                } elseif {![string compare -length 6 $stat "igmpv2"]} {
                    keylset portStats  ${::sth::igmp::userArgsArray(port_handle)}.V2.$stat  $stats($stat)
                } elseif {![string compare -length 6  $stat "igmpv3"]} {
                    keylset portStats  ${::sth::igmp::userArgsArray(port_handle)}.V3.$stat $stats($stat)
                } else {
                    keylset portStats  ${::sth::igmp::userArgsArray(port_handle)}.-.$stat $stats($stat)
                }
            }
        }
    } returnedString]

      if {$retVal} {
         ::sth::sthCore::processError returnKeyedList $returnedString
      } else {
         if {[info exists ::sth::igmp::userArgsArray(handle)]} {
            keylset returnKeyedList group_membership_stats \
                  $groupMembershipStats
            keylset returnKeyedList session \
                  $igmpSessionStats
         }
         if {[info exists ::sth::igmp::userArgsArray(port_handle)]} {
            keylset returnKeyedList port_stats $portStats
         }

         keylset returnKeyedList status $::sth::sthCore::SUCCESS
      }

      return $returnKeyedList
   }
}
