# $Id: //TestCenter/4.81_rel/content/HltAPI/SourceCode/pppox.tcl#1 $
# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

# Copyright (c) 2005 - 2007 Spirent Communications
#
# All rights are reserved. Reproduction or transmission in whole or in part, in
# any form or by any means, electronic, mechanical or otherwise, is prohibited
# without the prior written consent of the copyright owner.
#

#source sthCore.tcl
#source pppoxTable.tcl
#source parse_dashed_args.tcl
#source pppoxFunctions.tcl
#source sthutils.tcl

#::sth::sthCore::sthCoreInit
#set ::sth::sthCore::enableInternallog true

namespace eval ::sth::Pppox:: {

}

##Procedure Header
#
# Name:
#    sth::pppox_config
#
# Purpose:
#    Configures PPPoE sessions for the specified Spirent HLTAPI port.
#
#    The Point-to-Point Protocol (PPP) provides a method of transporting
#    datagrams over point-to-point links between hosts, switches, and routers.
#    Spirent HLTAPI supports Point-to-Point Protocol over Ethernet (PPPoE).
#
# Synopsis:
#    sth::pppox_config
#         -num_sessions <1-65535>
#         { [-mode {create|reset} -port_handle <handle> |
#            -mode modify -handle <session_block_handle>]
#         }
#         [-encap {ethernet_ii|ethernet_ii_vlan|ethernet_ii_qinq}]
#         [-protocol pppoe ]
#         [-ac_select_mode <service_name>]
#         [-agent_circuit_id <circuit_id> ]
#         [-agent_mac_addr <aa:bb:cc:dd:ee:ff> ]
#         [-agent_remote_id <remote_id>
#         [-agent_session_id <session_id>]
#         [-agent_type {2516 | dsl} ]
#         [-attempt_rate <1-1000>]
#         [-auth_mode {none|pap|chap|pap_or_chap}]
#              [-username <username>]
#                   [-username_wildcard {0|1}]
#                        [-wildcard_pound_start<0-65535>]
#                             [-wildcard_pound_fill <0-9> ]
#                             [-wildcard_pound_end<0-65535>]
#                        [-wildcard_question_start <0-65535>]
#                             [-wildcard_question_fill <0-9> ]
#                             [-wildcard_question_end <0-65535>]
#              [-password <password>]
#                   [-password_wildcard {0|1}]
#                        [-wildcard_pound_start<0-65535>]
#                             [-wildcard_pound_fill <0-9> ]
#                             [-wildcard_pound_end<0-65535>]
#                        [-wildcard_question_start <0-65535>]
#                             [-wildcard_question_fill <0-9> ]
#                             [-wildcard_question_end <0-65535>]
#              [-auth_req_timeout <1-65535>]
#         [-auto_retry {0|1}]#
#         [-chap_ack_timeout <1-65535> ]
#         [-config_req_timeout <1-65535>]
#              [-max_configure_req <1-65535>]
#              [-max_outstanding <2-65535>]
#              [-max_terminate_req <1-65535>]
#         [-disconnect_rate <1-1000>]
#         [-dut_assigned_src_addr 1]
#         [-echo_req 0]
#         [-echo_req_interval <0-65535>]
#         [-fsm_max_naks <1-65535> ]
#         [-include_id {0|1}]
#         [-intermediate_agent {0|1}]
#         [-ip_cp {ipv4_cp|ipv4v6_cp}]
#              [-ipcp_req_timeout <1-65535>]
#         [-lcp_mru <128-65535>]
#         [-local_magic {0|1}]
#         [-mac_addr <aa:bb:cc:dd:ee:ff>]
#              [-mac_addr_step <aa:bb:cc:dd:ee:ff>]
#              [-mac_addr_stutter <0xFFFFFFFF>]
#         [-max_auth_req <1-65535> ]
#         [-max_auto_retry_count <1-65535> ]
#         [-max_configure_req <1-65535> ]
#         [-max_echo_acks <0-65535> ]
#         [-max_ipcp_req <1-65535> ]
#         [-max_padi_req <1-65535> ]
#         [-max_padr_req <1-65535> ]
#         [-mru_neg_enable {0|1}]
#         [-padi_include_tag {0|1}]
#         [-padi_req_timeout <1-65535>]
#         [-padr_include_tag {0|1}]
#         [-padr_req_timeout <1-65535>]
#         [-qinq_incr_mode {inner|outer|both}]
#         [-service_name <name>]
#         [-term_req_timeout <1-65535>]
#         [-vlan_id <0-4095>]
#              [-vlan_id_count <1-4095>]
#              [-vlan_id_step <1-4095>]
#              [-vlan_user_priority <0-7>]
#         [-vlan_id_outer <0-4095>]
#              [-vlan_id_outer_count <1-4096>]
#              [-vlan_id_outer_step <1-4095>]
#              [-vlan_outer_tpid 0x8100 ]
#
# Arguments:
#
#    -ac_select_list
#                   Use this option with -ac_select_mode only when the specified
#                   type of service is either ac_mac or ac_name. This option
#                   specifies the ac mac address and percentage pair as either
#                   00:11:00:00:00:11|50 or 00:11:00:00:00:12|50 or the ac name
#                   and percentage pair as either ciscoAC|60 or ciscoAC2|40.
#
#    -ac_select_mode
#                   Specifies the type of service (ISP name, claxs or QoS)
#                   requested. If blank, (not specified or empty
#                   string specified), any service is acceptable.
#                   There are various ways the AC can be selected based on
#                   the PADO received from AC. The default is an empty
#                   string.
#
#    -agent_circuit_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enabled for DSL-type relay agents only. You can use the
#                   circuit ID to encode a local identifier for the circuit that
#                   received a PPP packet from a client, destined for the access
#                   concentrator. Use wildcard characters to make each circuit
#                   ID unique:
#
#                   @s - Session index associated with the PPPoX client.
#                   @b - Block (host/router) index
#                   @p - Port name
#                   @m - MAC address of the PPPoX client
#
#                   You can also include the following customizable substitution
#                   options:
#
#                   @x - Custom step setup in
#                        (start,count,step,zeropadding,stutter) format
#                   start - starting value
#                   count - number of values to generate
#                   step - amount to increment the start value when the start
#                        value must be stepped
#                   zeropadding - length the value should be padded to by
#                        prepending 0's
#                   stutter - number of times a value should be repeated before
#                        applying the step
#
#                   To include the "@" symbol in a relay agent option, use it
#                   twice:
#
#                   @@ - This must be used to include the textual "@" symbol in
#                        the string, use @@
#
#                   The default is "circuit @s".
#
#    -agent_mac_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enabled for RFC 2516-type relay agents only. The Relay Agent
#                   MAC address is the MAC address of the next hop from the
#                   subscriber client group to the access concentrator. Its
#                   format is aa:bb:cc:dd:ee:ff. The default is  "" (empty
#                   String).
#
#    -agent_remote_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the remote ID of the DSL-type relay agent (see
#                   -agent_type). Use wildcard characters to make each ID
#                   unique:
#
#                   @s - Session index associated with the PPPoX client.
#                   @b - Block (host/router) index
#                   @p - Port name
#                   @m - MAC address of the PPPoX client
#
#                   You can also include the following customizable substitution
#                   options:
#
#                   @x - Custom step setup in
#                        (start,count,step,zeropadding,stutter) format
#                   start - starting value
#                   count - number of values to generate
#                   step - amount to increment the start value when the start
#                        value must be stepped
#                   zeropadding - length the value should be padded to by
#                        prepending 0's
#                   stutter - number of times a value should be repeated before
#                        applying the step
#
#                   To include the "@" symbol in a relay agent option, use it
#                   twice:
#
#                   @@ - This must be used to include the textual "@" symbol in
#                        the string
#
#                   The default is "remote @m-@p-@g".
#
#                   Note:  The relay remote ID (-agent_remote_id) and relay
#                   session ID (-agent_session_id) parameters are mutually
#                   exclusive.
#
#    -agent_session_id
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the session ID of the RFC2516-type relay agent
#                   (see -agent_type). Use wildcard characters to make each ID
#                   unique:
#
#                   @s - Session index associated with the PPPoX client.
#                   @b - Block (host/router) index
#                   @p - Port name
#                   @m - MAC address of the PPPoX client
#
#                   You can also include the following customizable substitution
#                   options:
#
#                   @x - Custom step setup in
#                        (start,count,step,zeropadding,stutter) format
#                   start - starting value
#                   count - number of values to generate
#                   step - amount to increment the start value when the start
#                        value must be stepped
#                   zeropadding - length the value should be padded to by
#                        prepending 0's
#                   stutter - number of times a value should be repeated before
#                        applying the step
#
#                   To include the "@" symbol in a relay agent option, use it
#                   twice:
#
#                   @@ - This must be used to include the textual "@" symbol in
#                        the string
#
#                   The default is "remote @m-@p-@g".
#
#                   Note:  The relay remote ID (-agent_remote_id) and relay
#                   session ID (-agent_session_id) parameters are mutually
#                   exclusive.
#
#    -agent_type
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the type of relay agent to use. Possible values
#                   are 2516 (for the RFC 2516-type of relay agent) and dsl (for
#                   the DSL-type of relay agent). The default is 2516.
#
#    -attempt_rate
#                   Specifies the PPP attempt rate, in seconds, for all PPP
#                   session blocks on this port. Possible values range from 1 to
#                   1000. The default is 100. This is a port-wide option. Any
#                   subsequent use of this option on a port after the initial
#                   "-mode create" will overwrite any previous setting.
#
#    -auth_mode
#                   Specifies the authentication mode. During the Link Control
#                   Protocol (LCP) phase, one peer may send an authentication
#                   challenge to the other. LCP supports two authentication
#                   protocols:
#
#                   -    Password Authentication Protocol (PAP). PAP is a simple
#                        authentication protocol in which a peer sends a
#                        password in response to the challenge.
#
#                   -    Challenge Handshake Authentication Protocol (CHAP).
#                        CHAP is based on the message digest concept in which
#                        the PPPoE peers share a secret password value but do
#                        not send that value across the connection. A peer sends
#                        a challenge (containing a random number value), the
#                        challenged peer uses the challenge value together with
#                        the password to calculate a message digest value. The
#                        challenged peer returns a response containing the
#                        message digest. If the transmitted message digest
#                        matches the same calculation performed by the
#                        challenging peer, the connection setup can continue.
#
#                   Possible values are none, pap, chap, and pap_or_chap.
#
#                   none - No authentication.
#                   pap  - PAP
#                   chap - CHAP MD5
#                   pap_or_chap - Automatically negotiated; accepts both PAP and
#                        CHAP offered by the DUT.
#
#                   The default is none.
#
#    -auth_req_timeout
#                   Specifies the timeout wait period for the server to either
#                   send a CHAP challenge or time between the re-transmission of
#                   a PAP request. Possible values range from 1 to 65525
#                   seconds. The default is 3 seconds.
#
#    -auto_retry
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables or disables an automatic retry to connect failed PPP
#                   sessions. Possible values are 0 (disable) and 1 (enable).
#                   The default value is 0.
#
#    -chap_ack_timeout
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the timeout wait period for the server to send an
#                   ACK to a challenge response. Possible values range from 1 to
#                   65525 seconds. The default is 3 seconds.
#
#    -config_req_timeout
#                   Specifies the configuration timeout value in seconds. When
#                   this expires, another PPP Configure-Request packet will be
#                   sent, until the value defined for the -max_configure_req
#                   argument is reached. After that, the session is terminated.
#                   This is a port-wide option. Any subsequent use of this
#                   option on a port after the initial "-mode create" will
#                   overwrite any previous setting. Possible values range from 1
#                   to 65535. The default is 3. See also -max_configure_req.
#
#    -disconnect_rate
#                   Specifies the PPP disconnect rate for all PPP session blocks
#                   on this port. Possible values range from 1 to 1000. The
#                   default is 1000. This is a port-wide option. Any subsequent
#                   use of this option on a port after the initial
#                   "-mode create" will overwrite any previous setting.
#
#    -dut_assigned_src_addr
#                   The DUT assigned source address, which is always set to 1.
#                   The IP address is always assigned by the DUT.
#
#    -echo_req
#                   Enables or disables echo requests. The default is 0
#                   (disables). Spirent HLTAPI does not allow you to change
#                   this value.
#
#    -echo_req_interval
#                   Specifies the interval (in seconds) between sending out
#                   consecutive echo requests. Possible values range from 0 to
#                   65525 seconds.
#                   The default is 10 seconds.
#
#    -encap
#                   Identifies the type of Layer2 encapsulation to use to define
#                   source and destination MAC addresses for a stream. Possible
#                   values are ethernet_ii, ethernet_ii_vlan, and
#                   ethernet_ii_qinq. Ethernet_ii_vlan supports VLAN tagging on
#                   Ethernet networks; ethernet_ii does not. If you use the
#                   -vlan_* arguments to define a VLAN interface, you must set
#                   the L2 encapsulation type to ethernet_ii_vlan.
#
#                   Note: If you modify the encapsulation value from encap
#                   ethernet_ii or ethernet_ii_vlan to ethernet_ii_qinq or vice
#                   versa (using "-mode modify"), you must resend all
#                   parameters. Otherwise, the parameters use their default
#                   values.
#
#                   The following example configures PPPoE for QinQ:
#
#                   sth::pppox_config   -port_handle port1 \
#                           -mode create \
#                           -protocol pppoe \
#                           -encap ethernet_ii_qinq \
#                           -auth_mode pap \
#                           -include_id 1 \
#                           -num_sessions 15000 \
#                           -mac_addr 00.00.12.00.00.02 \
#                           -mac_addr_step 00.00.00.00.00.01 \
#                           -username spirent \
#                           -password spirent \
#                           -vlan_id 1 \
#                           -vlan_id_outer 10 \
#                           -vlan_id_count 3000 \
#                           -vlan_id_outer_count 5 \
#                           -vlan_id_step 1 \
#                           -vlan_id_outer_step 1 \
#                           -qinq_incr_mode inner \
#
#    -fsm_max_naks
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the maximum number of Negative-Acknowlegments
#                   allowed during LCP and NCP configuration/negotiation.
#                   Possible values range from 1 to 65535. The default is 5.
#
#    -handle
#                   Specifies the handle of the PPPoE session group to use when
#                   -mode is set to "modify" or "reset." This argument is
#                   required for modify mode only. The handle is returned by the
#                   sth::pppox_config function.
#
#                   NOTE:In version 1.24, -handle was passed as a string value.
#                   In version 1.30, -handle was passed as an integer. In
#                   version 2.x, -handle is passed as an ALPHANUMERIC value.
#
#    -include_id
#                   Specifies whether to include the CHAP ID in challenge
#                   messages. Possible values are:
#                        1 - The CHAP ID is included in challenge messages.
#                        0 - The CHAP ID is not included.
#                   The default is 0.
#
#    -intermediate_agent
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables or disables the relay agent. Possible value are 0
#                   (disable the relay agent) or 1 (enable the relay agent).
#                   The default is 0.
#
#    -ip_cp
#                   The IP Control Protocol (IPCP) version to enable. Possible
#                   values are ipv4_cp and ipv4v6_cp. The default is
#                   ipv4_cp.
#
#                   ipv4_cp - Enables IPv4 addressing
#
#                   ipv4v6_cp - Enables both IPv4 and IPv6 addressing on the
#                   same PPP link. This option requires that both IPv4 and IPv6
#                   negotiate with the DUT for the session to be successful.
#                   Both (ipv6 and IPv4v6) are used for negative testing only;
#                   the session will not establish.
#
#    -ipcp_req_timeout
#                   Specifies the timeout value (in seconds) for acknowledgment
#                   of an NCP Configure-Request. Possible values range from 1 to
#                   65535 seconds. The default value is 3 seconds.
#
#    -lcp_mru
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the local maximum receive unit (MRU) size in
#                   bytes. Possible values range from 128 to 65535. For PPPoE,
#                   the MRU size cannot exceed 65535. The default is 1492. This
#                   is a port-wide option. Any subsequent use of this option on
#                   a port after the initial "-mode create" will overwrite any
#                   previous setting.
#
#    -local_magic
#                   Enables or disables the use of the magic number for
#                   detection of data link layer errors. This argument is used
#                   for loop back detection. Possible values are 0 (disable
#                   magic number) and 1 (enable magic number). The default is 1.
#                   This is a port-wide option. Any subsequent use of this
#                   option on a port after the initial "-mode create" will
#                   overwrite any previous setting.
#
#    -mac_addr
#                   Specifies the starting value for the MAC address. The
#                   default is 00-10-94-01-00-01.
#
#    -mac_addr_step
#                   Specifies the step value applied to the base MAC address.
#                   The default is 00:00:00:00:00:01
#
#    -max_auth_req
#                   Specifies the maximum number of authentication requests that
#                   can be sent without getting an authentication response from
#                   the DUT. Possible values range from 1 to 65535. The default
#                   is 5.
#
#    -max_auto_retry_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the maximum number of automatic retry attempts.
#                   Possible values range from 1 to 65535. The default is 65535.
#
#    -max_configure_req
#                   Specifies the maximum number of times a PPP Configure-
#                   Request packet can be sent without a response before a
#                   session fails. Possible values range from 1 to 65535. The
#                   default is 5. See also -config_req_timeout, This is a
#                   port-wide option. Any subsequent use of this option on a
#                   port after the initial "-mode create" will overwrite
#                   any previous setting.
#
#    -max_echo_acks
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the maximum number of consecutive, unanswered echo
#                   request to send before failing the subscriber session.
#                   Possible values range from 0 to 65535. The default is 3. If
#                   you specify 0 for this argument, echo requests are disabled.
#                   Specifying any other number enables echo requests on the
#                   port; this is the same as setting -echo_req to 1. See also
#                   -echo_req and -term_req_timeout.
#
#    -max_ipcp_req
#                   Specifies the maximum number of NCP Configure-Requests that
#                   can be sent without acknowledgement before a session fails.
#                   Possible values range from 1 to 65535. The default is 10.
#                   See also -term_req_timeout.
#
#    -max_outstanding
#                   Specifies the maximum number of sessions that can be
#                   connecting or disconnecting at one time for all PPP session
#                   blocks on this port. Possible values range from 2 to 1000.
#                   The default is 100. This is a port-wide option. Any
#                   subsequent use of this option on a port after the initial
#                   "-mode create" will overwrite any previous setting.
#
#    -max_padi_req
#                   Specifies the maximum number of PADI packets that can be
#                   sent without acknowledgment before a session fails. Possible
#                   values range from 1 to 65535. The default is 5.
#
#    -max_padr_req
#                   Specifies the maximum number of PADR packets that can be
#                   sent without acknowledgment before a session fails. Possible
#                   values range from 1 to 65535. The default is 5.
#
#    -max_terminate_req
#                   Specifies the maximum number of times a PPP Terminate-
#                   Request packet can be sent before a session fails. Possible
#                   values range from 1 to 65535. The default is 10. See also
#                   -term_req_timeout.
#
#    -mode
#                   Specifies the action to perform. Possible values are create,
#                   modify, and reset. This argument is required. The modes are
#                   described below:
#
#                   create - Configures the PPPoE sessions on the port specified
#                        with the -port_handle argument. The first "-mode
#                        create" argument also creates the PPPoE port object.
#
#                   modify - Changes the configuration for the PPPoE port and
#                        session block identified by the -handle argument.
#
#                        You must use the new handle returned by
#                        "sth::pppox_config -mode modify" in all subsequent
#                        sth::pppox_stats and sth::pppox_control functions
#                        because the old handle is no longer valid. This
#                        new handle replaces the handle returned by
#                        "sth::pppox_config -mode create -handle <handle>".
#                        Example:
#
#                        sth::pppox_config -mode modify -handle host2
#                        -username spirent -password spirent
#
#                        {status 1} {handles host3} {port_handle port1}
#                        {pppoe_port pppoxportconfig1} {pppoe_session
#                        pppoeclientblockconfig2} {procName sth::pppox_config}
#
#                        If you have configured either IGMP over PPPoX and
#                        modify sth::pppox_config, you must also modify the IGMP
#                        handle to accept the new handle as well. (See the usage
#                        examples provided for sth::emulation_igmp_config.)
#
#                        Note: When modifying PPPoX sessions, only modify
#                        sth::pppox_config when the aggregate.idle flag
#                        returned by sth::pppox_stats is 1 and no sessions are
#                        connected.
#
#                   reset - Deletes the session block associated with the handle
#                        name. To re-connect and re-start, you must reconfigure
#                        your settings.
#
#                        IMPORTANT:
#                        Before using "sth::pppox_config -mode reset", you must
#                        first delete all traffic streams with the
#                        "sth::traffic_config -mode reset" command. Traffic
#                        streams must be reset before PPPoX can be reset.
#
#    -mru_neg_enable
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Enables or disables MRU negotiation. Possible value are 0
#                   (disable) or 1 (enable).  The default is 1.
#
#    -num_sessions
#                   The number of PPPoE clients to emulate. Possible values
#                   range from 1 to 65535. This argument is required.
#
#                   Note: If the value of -encap is set to "ethernet_ii_vlan",
#                   then the value of -num_sessions must be equal to the value
#                   of -vlan_id_count. Likewise, if the value of -encap is set
#                   to "ethernet_ii_qinq", then the value of -num_sessions must
#                   be equal to (vlan_id_count * vlan_id_outer_count).
#
#    -padi_include_tag
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies whether to include the relay agent tags in
#                   transmitted PADI messages. Possible values are 0 (do not
#                   include relay agent tags in PADI messages) or 1 (include
#                   relay agent tags in PADI messages). The default is 1.
#
#    -padi_req_timeout
#                   Specifies the timeout value (in seconds) for acknowledgment
#                   of a PADI packet. Possible values range from 1 to 65535. The
#                   default is 3.
#
#    -padr_include_tag
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies whether to include the relay agent tags in
#                   transmitted PADR messages. Possible values are 0 (do not
#                   include relay agent tags in PADR messages) or 1 (include
#                   relay agent tags in PADR messages). The default is 1.
#
#    -padr_req_timeout
#                   Specifies the timeout value (in seconds) for acknowledgment
#                   of a PADR packet. Possible values range from 1 to 65535. The
#                   default is 3.
#
#    -password
#                   Specifies the string base from which the passwords are
#                   generated (for example, Password#) when the authentication
#                   mode is pap, chap, or pap_or_chap (see -auth_mode). The
#                   default is "pass". See Notes for information about using
#                   wildcards in passwords.
#
#    -password_wildcard
#                   Enables wildcard substitution in the -password argument.
#                   Possible values are 0 (false) and 1 (true). If the value is
#                   set to 1, any wildcards used in -password are replaced with
#                   the corresponding values for -wildcard_pound_start,
#                   wildcard_pound_end, wildcard_question_start and
#                   -wildcard_question_end. If the value is 0, wildcards are not
#                   replaced in the specified password. The default is 0.
#
#    -port_handle
#                   Specifies the handle of the port on which to create the
#                   PPPoE port and session block when -mode is set to "create".
#                   This argument is required for create mode only. Specifies
#                   the port handle is returned by the sth::interface_config
#                   function.
#
#    -protocol
#                   Specifies the type of protocol to use. Currently, Spirent
#                   HLTAPI supports only pppoe.
#
#    -qinq_incr_mode
#                   Determines which VLAN ID to increment first. Possible values
#                   are:
#                   inner - increment the inner VLAN ID before the outer VLAN ID
#                   outer - increment the outer VLAN ID before the inner VLAN ID
#                   both - increment both the inner and outer VLAN ID at the
#                   same time
#
#                   The default is outer.
#
#                   Note: For version 2.00, qinq can only be incremented on a
#                   per host basis.
#
#    -service_name
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Indicates the service (ISP name, class, or QoS) requested.
#                   If you do not specify a service name or specify an empty
#                   string, Spirent HLTAPI will accept any service.
#
#    -term_req_timeout
#                   The maximum amount of time (in seconds) that the
#                   termination process can take before another PPP Terminate-
#                   Request packet is sent. If there is no response, another
#                   packet is sent until the value defined for the
#                   -max_terminate_req argument is reached, and then the session
#                   is terminated. Possible values range from 1 to 65535.
#                   The default is 10.  See also -max_terminate_req.
#
#    -username
#                   The string base from which the usernames are generated
#                   (for example, User#) when the authentication mode is
#                   pap, chap, or pap_or_chap (see -auth_mode). The default is
#                   "anonymous". See Notes for information about using wildcards
#                   in passwords.
#
#    -username_wildcard
#                   Enables wildcard substitution in the -username argument.
#                   Possible values are 0 (false) and 1 (true). If the value
#                   is set to 1, any wildcards used in -username are replaced
#                   with the corresponding values according to
#                   -willcard_pound_start, -wildcard_pound_end,
#                   -wildcard_question_start and -wilcard_question_end. If the
#                   value is 0, wildcards are not replaced. The default is 0.
#
#    -vlan_id
#                   The first inner VLAN ID to use when generating PPPoE
#                   clients. Possible values range from 0 to 4095. The default
#                   is 1.
#
#    -vlan_id_count
#                   The number of inner VLAN IDs to use when generating PPPoE
#                   clients. Spirent HLTAPI assigns VLAN membership in
#                   round-robin fashion. If the value of -encap is set to
#                   "ethernet_ii_vlan", then the value of -num_sessions must
#                   be equal to the value of -vlan_id_count. Possible values
#                   range from 1 to 4096. The default is 1.
#
#    -vlan_id_outer
#                   The first outer VLAN ID to use when generating PPPoE
#                   clients. This ID only applies to PPPoE w/Stacked VLAN.
#                   Possible values range from 0 to 4095. The default is 1.
#
#    -vlan_id_outer_count
#                   The number of outer VLAN IDs to use when generating PPPoE
#                   clients. Spirent HLTAPI assigns VLAN membership in
#                   round-robin fashion. The VLAN count must divide evenly into
#                   the number of sessions. The VLAN count cannot be greater
#                   than the session count. Possible values range from 1 to
#                   4096. The default is 1.
#
#    -vlan_id_outer_step
#                   The value that Spirent HLTAPI uses to increment the
#                   outer VLAN ID. Possible step values range from 1 to 4095.
#                   The default is 1.
#
#    -vlan_id_step
#                   The value that Spirent HLTAPI uses to increment the
#                   inner VLAN ID. Possible step values range from 1 to 4095.
#                   The default is 1.
#
#    -vlan_user_priority
#                   Specifies the inner VLAN priority to assign to the specified
#                   port. Possible values range from 0 to 7. The default is 0.
#
#    -vlan_outer_user_priority
#                   Specifies the outer VLAN priority to assign to the specified
#                   port. Possible values range from 0 to 7. The default is 0.
#
#    -vlan_outer_tpid
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Sets the value of the outer VLAN Tag Protocol Identifier
#                   (TPID) to hex (0x8100), identifying the frame as an
#                   802.1Q frame. This value is part of the outer VLAN tag
#                   header in the packet.
#
#    -wildcard_pound_fill
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Wildcard fill character for -wildcard_pound_start
#                   and -wildcard_pound_end. If 0, the numbers are replaced
#                   without leading zeroes. Otherwise, leading zeroes are added
#                   to ensure that the number is at least the specified number
#                   of digits wide. Possible values range from 0 to 9. The
#                   default is 0. See Notes for more about using wildcards.
#
#    -wildcard_question_fill
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Wildcard fill character for -wildcard_question_start and
#                   -wildcard_question_end. If 0, the numbers are replaced
#                   without leading zeroes. Otherwise, leading zeroes are added
#                   to ensure that the number is at least the specified number
#                   of digits wide. Possible values range from 0 to 9. The
#                   default is 0. See Notes for more about using wildcards.
#
#    -wildcard_pound_start
#                   Starting numerical value to replace the wildcard pound (#)
#                   character in user names and passwords, such as user# or
#                   pwd#. Possible values range from 0 to 65535. The default is
#                   1. See Notes for more about using wildcards.
#
#    -wildcard_pound_end
#                   Final numerical value to replace the wildcard pound (#)
#                   character in user names and passwords, such as user# or
#                   pwd#. Possible values range from 0 to 65535. The default is
#                   1. See Notes for more about using wildcards.
#
#    -wildcard_question_start
#                   Starting numerical value to replace the wildcard question
#                   mark character in user names and passwords. Possible values
#                   range from 0 to 65535. The default is 1. See Notes for more
#                   about using wildcards.
#
#    -wildcard_question_end
#                   Final numerical value to replace the wildcard question
#                   mark character in user names and passwords. Possible values
#                   range from 0 to 65535. The default is 1. See Notes for more
#                   about using wildcards.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -echo_rsp
#    -pvc_incr_mode
#    -sessions_per_vc
#    -vci
#    -vci_count
#    -vci_step
#    -vlan_user_priority_count
#    -vlan_user_priority_step
#    -vpi
#    -vpi_count
#    -vpi_step
#
# Return Values:
#    The sth::pppox_config function returns a keyed list using the following
#    keys (with corresponding data):
#
#    handles   Identifies the PPPoE session block handle (or group) returned
#              by the "sth::pppox_config -mode create" function.
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::pppox_config function creates or modifies an emulated PPPoE
#    session block. Use the -mode argument to specify the action to perform.
#    (See the -mode argument description for information about the actions.)
#
#    Note: Modifying any option during a PPPoE session which currently is a
#    member of a multicast group will sever the PPPoE session, IGMP host, and
#    multicast group relationship. Therefore, do not use sth::pppox_config while
#    sessions are connected to prevent aborting the PPPoX engine. To see if
#    sessions are connected, look at the aggregate.idle flag returned by
#    "sth::pppox_stats -mode aggregate". If aggregate.idle is "0", then do not
#    send sth::pppox_config. If the PPPoX engine is aborted, you will need to
#    reconfigure the PPPoX session. If using IGMP over PPPoX, you will also need
#    to reconfigure the IGMP session.
#
#    When you create a PPPoE session block, you must use the -port_handle
#    argument to specify the Spirent HLTAPI port that the emulated PPPoE
#    session block will use for PPPoE communication. (The port handle value is
#    contained in the keyed list returned by the sth::connect function.)
#
#    Use the -mode create argument to define the characteristics of a PPPoE
#    session block. You can use a single session block to emulate multiple PPPoE
#    clients.
#
#    In addition to specifying the port handle (-port_handle), you must also
#    provide one or more of the following arguments when you create a PPPoE
#    session block, or use their default values:
#
#    -num_sessions (the number of PPPoE clients to emulate)
#
#    -mac_addr (starting value for the MAC address)
#
#    -mac_addr_step (increment used to generate additional MAC addresses for
#         multiple clients)
#
#    -auth_mode  (authentication style)
#
#    -include_id (include or exclude the CHAP ID in challenge messages)
#
#    -username  (if specifying an authentication style)
#
#    -password  (if specifying an authentication style)
#
#    NOTES:
#         1)   In version 1.24, -handle was passed as a string value.
#              In version 1.30, -handle was passed as an integer.  In version
#              2.x, -handle is passed as an ALPHANUMERIC value.
#
#    For a detailed description of PPPoE encapsulation, see "RFC 2516
#    - A Method for Transmitting PPP Over Ethernet (PPPoE)".
#
#    For an example of how to configure PPPoE traffic, see the documentation for
#    sth::traffic_config.
#
# Examples:
#    The following example configures a PPPoE session:
#
#    sth::pppox_config -port_handle $p0  \
#         -mode create \
#         -protocol pppoe \
#         -encap ethernet_ii \
#         -local_magic         1 \
#         -max_configure_req   5 \
#         -max_terminate_req   10 \
#         -attempt_rate        100 \
#         -disconnect_rate     100 \
#         -max_outstanding     100 \
#         -num_sessions        1 \
#         -mac_addr            $mac_addr \
#         -username            $username \
#         -password            $password
#
#    Output for example shown above:
#
#    {status 1} {port_handle port1} {handles host2} {pppoe_port \
#         pppoeportconfig1}\
#    {pppoe_host host2}{pppoe_session pppoeclientblkconfig1} {procName \
#    sth::pppox_config}
#
#    The following example configures multiple PPPoE sessions:
#
#    set pppHandles ""
#    for {set i 1} {$i <= $num_blocks} {incr i} {
#         set rL [sth::pppox_config   -port_handle port1 \
#                                     -mode create \
#                                     -protocol pppoe \
#                                     -encap ethernet_ii \
#                                     -num_sessions $num_sessions \
#         ]
#
#         #Create a list of PPPoX handles
#         keylget rL handles pppHandle
#         lappend pppHandles $pppHandle
#   }
#
#   # Connect all PPPoX handles in list
#   set rL [sth::pppox_control -handle $pppHandles -action connect]
#
# Sample output: See Examples above.
#
# Notes:
#    You can generate outgoing usernames and passwords based on wildcard
#    replacements. The following example generates 50 user names and passwords:
#
#    sth::pppox_config -port_handle $p0  \
#     -mode create -protocol pppoe -encap ethernet_ii \
#     -num_sessions $num_sessions \
#     -username User# \
#     -password Pass? \
#     -wildcard_pound_start 1  \
#     -wildcard_pound_end 50  \
#     -wildcard_question_start 1  \
#     -wildcard_question_end 50  \
#
#    The # character represents a counter. For example, define a counter to
#    start at 1 (-wildcard_pound_start 1), run to 50 (-wildcard_pound_end), and
#    increment by 1. Then, in the -username argument, specify user#, which would
#    be replaced with User1, User2,and so on, when authentication begins.
#
#    The # wildcard is replaced with a counter, starting at 1. For example,
#    User# becomes User1, User2, and so on. If you do not specify #, then
#    no substitution will take place.
#
# End of Procedure Header

proc ::sth::pppox_config { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Pppox::sortedSwitchPriorityList
    variable ::sth::Pppox::userArgsArray
    array unset ::sth::Pppox::userArgsArray
    array set ::sth::Pppox::userArgsArray {}

    set _hltCmdName "pppox_config"
    ::sth::sthCore::Tracker "::sth::pppox_config" $args

    set underScore "_"
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::Pppox::pppoxTable $args ::sth::Pppox:: $_hltCmdName ::sth::Pppox::userArgsArray ::sth::Pppox::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err"
        return $returnKeyedList
    }

    # Error checking
	set retVal [catch {
		if {!([info exists ::sth::Pppox::userArgsArray(handle)] ||
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: The command $_hltCmdName requires -port_handle or -handle."
			return $returnKeyedList
		}

		if {([info exists ::sth::Pppox::userArgsArray(handle)] &&
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
			return $returnKeyedList
		}

		# Check the port handle exists on STC
		set portHandleList ""
		if {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
			if {[catch {::sth::sthCore::invoke stc::get $userArgsArray(port_handle)} err]} {
				::sth::sthCore::processError returnKeyedList "Error in $procName: -port_handle $userArgsArray(port_handle) does not exist."
				return $returnKeyedList
			}
			lappend portHandleList $userArgsArray(port_handle) 
		}
		# Check the handle exists on STC
		if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
			foreach handle $userArgsArray(handle) {
				if {[catch {::sth::sthCore::invoke stc::get $handle} err]} {
					::sth::sthCore::processError returnKeyedList "Error in $procName: -handle $handle does not exist."
					return $returnKeyedList
				}
				lappend portHandleList [::sth::sthCore::invoke stc::get $handle -affiliationPORT-Targets]
			}
		}

		# 4/20/07 - We will have to do this until CR 103885701 can be fixed. This value is currently not exposed to us in the lower layer.
		# Error checking for TPID
		if {[info exists ::sth::Pppox::userArgsArray(vlan_outer_tpid)] && $userArgsArray(vlan_outer_tpid) != 0x8100} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid value for -vlan_outer_tpid $userArgsArray(vlan_outer_tpid). The only value accepted at this time is 0x8100. Please change this value to 0x8100."
			return $returnKeyedList
		}

		# Check that PPPoX is idle (not busy) until CR 116178231 can be fixed 
		# Modifying/configuring while session is connected will terminate the
		# engine
		set none 0; set idle 0; set connecting 0; set disconnecting 0; set connected 0; set terminating 0;
		foreach curPort $portHandleList {
			foreach pppoxportconfig [::sth::sthCore::invoke stc::get $curPort -children-PPPoxportconfig] { set port_state [string tolower [stc::get $pppoxportconfig -portstate]] ; incr $port_state }
		}
		if {$connecting || $connected || $disconnecting || $terminating} {
			set result "Error in $_hltCmdName: This command should not be sent until engine is idle state. Please check \"sth::pppox_stats -mode aggregate\" to see that aggregate.idle is 1 before sending again. "
			::sth::sthCore::processError returnKeyedList $result
			return $returnKeyedList
		}

		set modeVal create
		if {[info exists ::sth::Pppox::userArgsArray(mode)]} {
			set modeVal $userArgsArray(mode)
		}

		# Mandatory parameters -- not so much encap protocol (but they will be later when we add OEOA and OA
		if {! ( $modeVal == "reset" || $modeVal == "modify")} {
			foreach param_name [list num_sessions encap protocol] { 
				if {! [info exists ::sth::Pppox::userArgsArray($param_name)]} {
					set result "Error in $_hltCmdName: Missing mandatory arguments num_sessions encap protocol"
					#puts "DEBUG:$result"
					::sth::sthCore::processError returnKeyedList $result
					return $returnKeyedList
				}
			}
		}
		foreach hname {"ip_cp" "auth_mode" "agent_type"} {
			if {[info exist userArgsArray($hname)]} {
				set stcvalue  [::sth::sthCore::getFwdmap      ::sth::Pppox::  pppox_config  $hname $userArgsArray($hname)]
				set userArgsArray($hname)  $stcvalue
			}
		}
		
		switch -exact -- $modeVal {
			create -
			modify -
			reset {
				set cmdStatus 0
				if {[catch {::sth::Pppox::${_hltCmdName}${underScore}${modeVal} returnKeyedList} err]} {
					::sth::sthCore::processError returnKeyedList $err
					keylset returnKeyedList procName $procName
					return $returnKeyedList
				}
				::sth::sthCore::doStcApply
				keylset returnKeyedList procName $procName
				keylset returnKeyedList status $::sth::sthCore::SUCCESS
			}
			SHA_NO_USER_INPUT {
				::sth::sthCore::processError returnKeyedList "No value for -mode: $modeVal."
				return $returnKeyedList
			}
			SHA_UNKNWN_SWITCH -
			default {
				::sth::sthCore::processError returnKeyedList "Unknown value for the -mode: $modeVal."
				return $returnKeyedList
			}
		}
	} returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList   
}

##Procedure Header
#
# Name:
#       sth::pppox_control
#
# Purpose:
#    Connects, disconnects, pauses, resumes, retries, or resets the PPPoE
#    sessions for the specified session block.
#
# Synopsis:
#    sth::pppox_control
#         -action {connect|disconnect|retry|reset|pause|resume|clear}
#         -handle <handle>
#
# Arguments:
#
#    -action        Specifies the action to perform. Possible values are
#                   connect, disconnect, reset, retry, pause, resume, and clear.
#                   You must specify one of these values. The modes are
#                   described below:
#
#                   connect - Establishes all PPPoX sessions on the specified
#                        session block.
#
#                   disconnect - Disconnects all established PPPoX sessions from
#                        the specified session block.
#
#                   retry - Attempts to connect failed PPPoX sessions on the
#                        port. You can only use the retry command after the
#                        sessions have finished attempting to connect (that is,
#                        the stats show that either aggregate.idle or
#                        aggregate.connected is 1).
#
#                   reset - Terminates the port. This action does not reset the
#                        defaults nor does it attempt to re-connect. To re-
#                        connect to the port, you must reconfigure the session
#                        block.
#
#                   pause - Pause all PPPoX sessions that are connecting or
#                        disconnecting.
#
#                   resume - Resume PPPoX sessions that were paused with
#                        "-action pause" while connecting or disconnecting.
#
#                   clear - Clears the PPPoX statistics for the port. You can
#                           only use this command after the sessions have been
#                           disconnected (that is, aggregate.idle is 1). You
#                           cannot clear the PPPoX port statistics while
#                           sessions are currently connected (that is,
#                           aggregate.connected is 1).
#
#                   Note: Use "sth::pppox_control -action clear" and
#                   "sth::pppox_control -action retry" only while sessions are
#                   in the idle state. To see if the PPPoX engine is in the idle
#                   state, look at the aggregate.idle flag returned by
#                   "sth::pppox_stats -mode aggregate".  If aggregate.idle is
#                   "0", then do not send this command.
#
#    -handle        Identifies the session block on which to connect,
#                   disconnect, reset, retry, pause, resume, or clear the PPPoX
#                   sessions.
#
# Return Values:
#    The function returns a keyed list using the following keys (with
#    corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#    log       An error message (if the operation failed).
#
# Description:
#    The pppox_control function stops or starts PPPoE session blocks.
#    You can use the function to perform the following actions: connecting,
#    disconnecting, resetting, retrying, pausing, resuming, or clearing PPPoE
#    sessions. When you call the pppox_control function, you specify a handle.
#
#    You can check the aggregate.idle and aggregate.connected fields returned
#    by "sth::pppox_stats -mode aggregate" to see when all sessions have
#    finished connecting or disconnecting. If the aggregate.idle or
#    aggregate.connected values are equal to 1, then you can send the
#    sth::pppox_control connect, retry, disconnect, pause, or resume actions
#    again. When the aggregate.connected value is 1, you can disconnect the
#    PPPoX sessions with "sth::pppox_control -handle <handle> -action
#    disconnect". If configuring and connecting multiple PPPoX handles,
#    configure all the handles before connecting PPPoE. Do not call
#    sth::pppox_config while aggregate.connecting, aggregate.connected, or
#    aggregate.disconnecting are equal to 1.
#
#         Example usage:
#
#         # Connect PPPoX sessions
#         set rL [sth::pppox_control -action connect -handle $pppHandles]
#
#         # Wait until aggregate.connected is 1
#         for {set i 0} {$i < $max} {incr i} {
#              after 10000
#              set rL [sth::pppox_stats -mode aggregate -handle $pppHandles]
#              keylget rL aggregate.connected connected
#              if {$connected == 1} {
#                   break
#              }
#         }
#
#         # You can now call connect, retry, disconnect, pause, or resume
#         # actions again.
#
#         set rL [sth::pppox_control -action disconnect -handle $pppHandles]
#
#    While in either the aggregate.connecting, aggregate.connected, or
#    aggregate.disconnecting state, the PPPoE engine cannot accept newly
#    configured PPPoE session blocks. Therefore, if you plan to configure and
#    bring up multiple PPPoX groups, configure all the PPPoE session blocks
#    before connecting PPPoE sessions.
#
#    NOTE:In version 1.24, -handle was passed as a string value.
#    In version 1.30, -handle was passed as an integer. In
#    version 2.x, -handle is passed as an ALPHANUMERIC value.
#
# Examples:
#  To connect a PPPoE session:
#
#    sth::pppox_control -handle host2 -action connect
#
#  Output for above example:
#    {status 1} {procName sth::pppox_control} {handles host2}
#
#  To connect multiple PPPoX handles:
#
#    set rL [sth::pppox_control -handle $pppHandles -action connect]
#
#  To disconnect a PPPoE session:
#
#    sth::pppox_control -handle host2 -action disconnect
#
#  Output for above example:
#    {status 1} {procName sth::pppox_control} {handles host2}
#
# Sample Input:
#    See Examples.
#
# Sample Output:
#    See Examples.
#
# Notes:
#    None
#
# End of Procedure Header

proc ::sth::pppox_control { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Pppox::sortedSwitchPriorityList
    variable ::sth::Pppox::userArgsArray
    array unset ::sth::Pppox::userArgsArray
    array set ::sth::Pppox::userArgsArray {}

    set _hltCmdName "pppox_control"

    ::sth::sthCore::Tracker "::sth::pppox_control" $args

    set underScore "_"

    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    if {[catch {::sth::sthCore::commandInit ::sth::Pppox::pppoxTable $args ::sth::Pppox:: $_hltCmdName ::sth::Pppox::userArgsArray ::sth::Pppox::sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error trying to initialize PPPoX command: $err"
        return $returnKeyedList
    }

    # Error checking
	set retVal [catch {
		if {!([info exists ::sth::Pppox::userArgsArray(handle)] ||
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "The command $_hltCmdName requires -port_handle or -handle."
			return $returnKeyedList
		}
		if {([info exists ::sth::Pppox::userArgsArray(handle)] &&
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
			return $returnKeyedList
		}

		set dhcpv6handleList  ""
		set dhcpv6resultList  ""
		set pppoxresultList ""
		set hostList ""

		if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
			set hostList $::sth::Pppox::userArgsArray(handle)
		} else {
			foreach port $::sth::Pppox::userArgsArray(port_handle) {
				foreach host [::sth::sthCore::invoke stc::get $port -AffiliationPort-sources] {
					if {![regexp -nocase "port_address" [::sth::sthCore::invoke stc::get $host -name]]} {
						lappend hostList $host
					}
				}
			}
		}
		
		foreach host $hostList {
			# Check how many handles are in the list -- will need to verify each one	
			#####
			#RXu: workaroud for PPPOX over IPV6 traffic error, MUST be removed once 3.40 STC itself fixs this
			if {[::sth::sthCore::invoke stc::get $host -children-ipv6if] == ""} {
				set version "ipv4"
			} else {
				set version "ipv6"
				set num_sessions [::sth::sthCore::invoke stc::get $host -DeviceCount]
				if {[info exists userArgsArray(use_internal_dhcpv6)] && $userArgsArray(use_internal_dhcpv6) == 1} {
					lappend dhcpv6handleList [::sth::sthCore::invoke stc::get $host -children-Dhcpv6PdBlockConfig]
					lappend dhcpv6resultList [::sth::sthCore::invoke stc::get [stc::get $host -children-Dhcpv6PdBlockConfig] -children-Dhcpv6BlockResults ]
				}
			}
			#RXu: End
			#####
			
			set port  [::sth::sthCore::invoke stc::get $host "-AffiliationPort-Targets"]
            # for cases such as load_xml()
             if {![info exists ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]} {
                set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port) ""
                regexp {(pppo.)clientblockconfig[0-9]*} [::sth::sthCore::invoke stc::get $host -children] "" ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)
            }
			set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockConfig
			set PppoxClientBlokcResults [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockResults
			
            if {"" == $::sth::Pppox::PPPOXCLIENTROBJTYPE($port) || [catch { lappend handleList [::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] } err]} {
				::sth::sthCore::processError returnKeyedList "Error in $procName: Invalid handle ($host) passed in. No $PppoxClientBlockConfig exists under -handle $userArgsArray(handle): $err."
				return $returnKeyedList
			}
			if {[::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] != ""} {
				lappend pppoxresultList [::sth::sthCore::invoke stc::get [stc::get $host -children-$PppoxClientBlockConfig] -children-$PppoxClientBlokcResults]
			}
			lappend portHandleList [::sth::sthCore::invoke stc::get $host -affiliationPORT-Targets]
		}

		# Action is mandatory
		if {! [info exists ::sth::Pppox::userArgsArray(action)]} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: -action is required."
			return $returnKeyedList
		}

		set actionValue $userArgsArray(action)
		# it complete successfully (GK 11/1/06)
		# 11/02/06 -- This fails periodically, according to KeithAbe MikeCruz, 
		# this error can be ignored and the test will still continue. Not 
		# sure what the repercussions are if this fails however.
		# For some reason, there needs to be a timer before this is called to help
		#after 3000
		# /11/06/06 -- Have to comment this out. Its causing errors during functional testing
		#if {$actionValue == "connect" && [catch { ::sth::sthCore::invoke stc::perform setupPortMappings } err]} {
		#    #set result "Error: Could not perform setupPortMappings. Msg: $err"
		#    #puts "DEBUG:$result"
		#    keylset returnKeyedList log $result
		#    keylset returnKeyedList status $::sth::sthCore::FAILURE
		#    return $returnKeyedList
		#}

		# Check that PPPoX is idle (not busy) until CR 116178231 can be fixed 
		# Modifying/configuring while session is connected will terminate the
		# engine
		if {[regexp clear $actionValue]} {
			set none 0; set idle 0; set connecting 0; set disconnecting 0; set connected 0; set terminating 0;
			foreach curPort $portHandleList {
				foreach pppoxportconfig [::sth::sthCore::invoke stc::get $curPort -children-pppoxPORTconfig] { set port_state [string tolower [stc::get $pppoxportconfig -portstate]] ; incr $port_state }
			}
			if {$connecting || $connected || $disconnecting || $terminating} {
				set result "Error in $_hltCmdName: The clear command should not be sent until engine is idle. Please check \"sth::pppox_stats -mode aggregate\" to see that value of aggregate.idle  is 1 before sending again. "
				::sth::sthCore::processError returnKeyedList $result
				return $returnKeyedList
			}
		}
		if {[regexp retry $actionValue]} {
			set none 0; set idle 0; set connecting 0; set disconnecting 0; set connected 0; set terminating 0;
			foreach curPort $portHandleList {
				foreach pppoxportconfig [::sth::sthCore::invoke stc::get $curPort -children-pppoxPORTconfig] { set port_state [string tolower [stc::get $pppoxportconfig -portstate]] ; incr $port_state }
			}
			if {$connecting || $disconnecting || $terminating} {
				set result "Error in $_hltCmdName: The retry command should not be sent until engine is idle or connected. Please check \"sth::pppox_stats -mode aggregate\" to see that value of aggregate.idle or aggregate.connected are 1 before sending again. "
				::sth::sthCore::processError returnKeyedList $result
				return $returnKeyedList
			}
		}

		if {[catch {::sth::sthCore::doStcApply} err]} {
			set result "Error: Could not perform the apply. Msg: $err"
			::sth::sthCore::processError returnKeyedList $result
			return $returnKeyedList
		}


		########## Greg Debug ############
		set gSystem system1
		set gProject [::sth::sthCore::invoke stc::get $gSystem -children-project]
		set gPortList [::sth::sthCore::invoke stc::get $gProject -children-port]

		::sth::sthCore::invoke stc::perform ArpNdStartOnAllDevices -portlist $gPortList
		####################################

		if {($version == "ipv6" ) && [info exists userArgsArray(use_internal_dhcpv6)] && $userArgsArray(use_internal_dhcpv6) == 1} {
			switch -exact -- $actionValue {
				connect {
					::sth::sthCore::invoke stc::perform PppoxConnect         -BlockList $handleList
					::sth::sthCore::invoke stc::perform PppoxConnectWait -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_sessions*240]
					::sth::sthCore::invoke stc::perform Dhcpv6Bind             -BlockList $dhcpv6handleList
					::sth::sthCore::invoke stc::perform Dhcpv6BindWait    -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_sessions*240]
				}
				disconnect {
					::sth::sthCore::invoke stc::perform Dhcpv6Release             -BlockList $dhcpv6handleList
					::sth::sthCore::invoke stc::perform Dhcpv6ReleaseWait    -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_sessions*240]
					::sth::sthCore::invoke stc::perform PppoxDisconnect     -BlockList $handleList
				}
				abort -
				reset {
					::sth::sthCore::invoke stc::perform PppoxAbort     -BlockList $handleList
				}
				resume {
					::sth::sthCore::invoke stc::perform PppoxResume     -BlockList $handleList
					::sth::sthCore::invoke stc::perform PppoxConnectWait -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_sessions*240]
					::sth::sthCore::invoke stc::perform Dhcpv6Rebind           -BlockList $dhcpv6handleList
					::sth::sthCore::invoke stc::perform Dhcpv6BindWait    -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_sessions*240]
				}
				pause {
					::sth::sthCore::invoke stc::perform PppoxPause     -BlockList $handleList
				}
				clear {
					::sth::sthCore::invoke stc::perform PppoxClearStats     -BlockList $handleList
				}
				retry {
					::sth::sthCore::invoke stc::perform PppoxRetry             -BlockList $handleList
					::sth::sthCore::invoke stc::perform PppoxRetryWait    -ObjectList $::sth::Pppox::userArgsArray(handle)  -WaitTime [expr $num_session*240]
					::sth::sthCore::invoke stc::perform Dhcpv6Bind             -BlockList $dhcpv6handleList
					::sth::sthCore::invoke stc::perform Dhcpv6BindWait      -ObjectList $::sth::Pppox::userArgsArray(handle) -WaitTime [expr $num_session*240]
				}
				SHA_NO_USER_INPUT {
					::sth::sthCore::processError returnKeyedList "No Value for -action Value:$actionValue."
					return $returnKeyedList
				}
				SHA_UNKNWN_SWITCH -
				default {
					::sth::sthCore::processError returnKeyedList "Unknown Value for -action Value:$actionValue."
					return $returnKeyedList
				}
			}
		} else {
			switch -exact -- $actionValue {
				connect -
				disconnect -
				reset -
				pause -
				resume -
				clear -
				retry {
					::sth::sthCore::invoke stc::perform [set ::sth::Pppox::${_hltCmdName}_action_fwdmap($actionValue)] -BlockList $handleList
				}
				abort {
					#set actionValue reset
					::sth::sthCore::invoke stc::perform [set ::sth::Pppox::${_hltCmdName}_action_fwdmap(reset)] -BlockList $handleList
				}
				SHA_NO_USER_INPUT {
					::sth::sthCore::processError returnKeyedList "No Value for -action Value:$actionValue."
					return $returnKeyedList
				}
				SHA_UNKNWN_SWITCH -
				default {
					::sth::sthCore::processError returnKeyedList "Unknown Value for -action Value:$actionValue."
					return $returnKeyedList
				}
			}
		} 
		if {$actionValue == "clear"} {
			# Delay to allow time for stats to clear
			# May need to make value dependent on number of hosts, sessions, etc.
			after 5000
		}
		if {$actionValue == "reset"} {
			# Must delete all stale objects, the lower layer does not take care of this
			if {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
				foreach handle $userArgsArray(port_handle) {
					foreach host [::sth::sthCore::invoke stc::get $handle -affiliationport-sources] {
						foreach pppoeclientblockconfig [::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] {
							if {[catch {::sth::sthCore::invoke stc::delete $host} err ]} {
								# Error but continue on
								#keylset returnKeyedList log "Error trying to delete $host."
								#keylset returnKeyedList status $::sth::sthCore::FAILURE
								#return $returnKeyedList
								::sth::sthCore::log error "Error deleting previously created Host:$host: $err"
							}
						}
					}
				}
			}
			if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
				foreach host $userArgsArray(handle) {
					foreach handle [::sth::sthCore::invoke stc::get $host -affiliationport-targets] {
						foreach host [::sth::sthCore::invoke stc::get $handle -affiliationport-sources] {
							foreach pppoeclientblockconfig [::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] {
								if {[catch {::sth::sthCore::invoke stc::delete $host} err ]} {
									# Error but continue on
									#keylset returnKeyedList log "Error trying to delete $host."
									#keylset returnKeyedList status $::sth::sthCore::FAILURE
									#return $returnKeyedList
									::sth::sthCore::log error "Error deleting previously created Host:$host: $err"
								}
							}
						}
					}
				}
			}
		}

		keylset returnKeyedList procName $procName

		if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
			keylset returnKeyedList handles $userArgsArray(handle)
		} elseif {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
			keylset returnKeyedList port_handle $userArgsArray(port_handle)
		}
	} returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}
    return $returnKeyedList  
}

##Procedure Header
#
# Name:
#       sth::pppox_stats
#
# Purpose:
#    Returns PPPoE port statistics associated with the specified port.
#    Statistics include the connection status and number and type of messages
#    sent and received from the specified port.
#
# Synopsis:
#    sth::pppox_stats
#         -handle <PPPoE_session_block_handle>
#         -mode {aggregate | session}
#
# Arguments:
#
#    -handle
#              Specifies the handle of the PPPoE session block for which you
#              want to retrieve PPPoE port statistics. The -handle argument is
#              required.
#
#    -mode
#              Specifies the type of statistics to return in the keyed list. The
#              -mode argument is required. Possible values are aggregate or
#              session:
#
#              aggregate - retrieves transmitted and received statistics for all
#                   PPPoE sessions associated with the specified port and a
#                   status value (1 for success).
#
#              session - retrieves transmitted and received statistics for only
#                   the PPPoE sessions specified with -handle.
#
#              Note: Session statistics are only valid after the PPPoE sessions\
#              are established. They will not be returned nor accessible until
#              you are connected.
#
# Cisco-specific Arguments:
#    Although the -retry option is supported by Spirent HLTAPI 2.00, we
#    strongly recommend that you use "sth::pppox_control -action retry" instead.
#
# Return Values:
#    The function returns a keyed list using the following keys (with
#    corresponding data):
#
#    Following is a keyed list showing the types of keys returned based on the
#    mode you specified.
#
#    TclX keyed list
#    key                             value
#    ---                             -----
#    status                          1 | 0
#    log                             Error message if command returns {status 0}
#    *** Aggregate stats ***
#    aggregate.atm_mode              Specifies whether the port is in ATM mode
#                                    (currently not supported)
#    aggregate.avg_setup_time........Average time required to bring a session up
#    aggregate.chap_auth_rsp_tx......Number of CHAP messages sent
#    aggregate.chap_auth_chal_rx.....The number of CHAP messages received*
#    aggregate.chap_auth_succ_rx     The number of CHAP messages received*
#    aggregate.chap_auth_fail_rx     The number of CHAP messages received*
#
#    aggregate.connecting............PPPoE clients that are connecting. If
#                                    aggregate.connecting is 1, then there are
#                                    sessions connecting on the port.
#
#    aggregate.connected.............All sessions that have finished with NCP
#                                    negotiation. If aggregate.connected is 1,
#                                    then PPPoX has finished attempting all
#                                    configured PPPoX sessions.
#
#    aggregate.idle..................The sessions have been disconnected or
#                                    terminated. If aggregate.idle is 1, then
#                                    the port state is idle.
#
#    aggregate.disconnecting.........If aggregate.disconnecting is 1, then PPPoX
#                                    sessions are disconnecting.
#
#    aggregate.connect_attempts......Number of sessions attempted
#    aggregate.connect_success.......Number of sessions that connected
#                                    successfully
#    aggregate.disconnect_failed.....Number of sessions that failed to
#                                    disconnect
#    aggregate.disconnect_success....Number of sessions that disconnected
#                                    successfully
#    aggregate.echo_req_rx...........Number of Echo Requests received
#    aggregate.echo_rsp_tx...........Number of Echo Replies sent
#
#    aggregate.ipcp_cfg_ack_rx.......Total number of IPCP messages received*
#    aggregate.ipcp_cfg_ack_tx.......Total number of IPCP messages sent*
#    aggregate.ipcp_cfg_nak_rx.......Total number of IPCP messages received*
#    aggregate.ipcp_cfg_nak_tx.......Total number of IPCP messages sent*
#    aggregate.ipcp_cfg_rej_rx.......Total number of IPCP messages received*
#    aggregate.ipcp_cfg_rej_tx.......Total number of IPCP messages sent*
#    aggregate.ipcp_cfg_req_rx.......Total number of IPCP messages received*
#    aggregate.lcp_cfg_req_rx........Number of LCP Configure-Request messages
#                                    received
#    aggregate.lcp_cfg_req_tx........Number of LCP Configure-Request messages
#                                    sent
#    aggregate.lcp_cfg_rej_rx........Number of LCP Configure-Reject messages
#                                    received
#    aggregate.lcp_cfg_rej_tx........Number of LCP Configure-Reject messages
#                                    sent
#    aggregate.lcp_cfg_ack_rx........Number of LCP Configure-ACK messages
#                                    received
#    aggregate.lcp_cfg_ack_tx........Number of LCP Configure-ACK messages
#                                    sent
#    aggregate.lcp_cfg_nak_rx........Number of LCP Configure-NAK messages
#                                    received
#    aggregate.lcp_cfg_nak_tx........Number of LCP Configure-NAK messages sent
#    aggregate.max_setup_time........Maximum time required to bring a session up
#    aggregate.min_setup_time........Minimum time required to bring a session up
#    aggregate.num_sessions..........Number of sessions configured
#    aggregate.padi_rx...............Number of PADI messages received
#    aggregate.padi_tx...............Number of PADI messages sent
#    aggregate.pado_rx...............Number of PADO messages received
#    aggregate.padr_tx...............Number of PADR messages sent
#    aggregate.pads_rx...............Number of PADS messages received
#    aggregate.padt_tx...............Number of PADT messages sent
#    aggregate.padt_rx...............Number of PADT messages received
#    aggregate.pap_auth_ack_rx.......Number of PAP ACK messages received
#    aggregate.pap_auth_nak_rx.......Number of PAP NAK messages received
#    aggregate.pap_auth_req_tx.......Number of PAP Request messages sent
#    aggregate.retry_count...........Number of sessions that have been retried
#                                    using the Retry function
#    aggregate.sessions_up...........Number of sessions currently active
#    aggregate.sessions_down.........Number of sessions that failed to connect
#    aggregate.success_setup_rate....Number of sessions per second that have
#                                    been established
#    aggregate.term_ack_rx...........Number of LCP Terminate-ACK messages
#                                    received
#    aggregate.term_ack_tx...........Number of LCP Terminate-ACK messages
#                                    sent
#    aggregate.term_req_rx...........Number of LCP Terminate-Request messages
#                                    received
#    aggregate.term_req_tx...........Number of LCP Terminate-Request messages
#                                    sent
#
#
#    *** Session stats ***
#
#    session.<session ID>.attempted
#                                    Number of times this session was attempted
#    session.<session ID>.chap_auth_chal_rx
#                                    Total number of CHAP responses received*
#    session.<session ID>.chap_auth_fail_rx
#                                    Total number of CHAP responses received *
#    session.<session ID>.chap_auth_rsp_tx
#                                    Total number of CHAP responses sent*
#    session.<session ID>.chap_auth_succ_rx
#                                    Total number of CHAP responses received *
#    session.<session ID>.completed
#                                    Number of times this session was
#                                    successfully connected and disconnected
#    session.<session ID>.connect_success
#                                    Number of times this session was
#                                    successfully connected and disconnected
#    session.<session ID>.echo_req_rx
#                                    Total number of Echo-Request packets
#                                    received
#    session.<session ID>.echo_rsp_tx
#                                    Total number of Echo-Reply packets sent
#
#    session.<session ID>.failed_connect
#                                    Number of times this session failed to
#                                    connect
#    session.<session ID>.failed_disconnect
#                                    Number of times this session failed to
#                                    disconnect
#    session.<session ID>.ip_addr
#                                    IP address assigned by the DUT to the
#                                    subscriber
#    session.<session ID>.ipcp_cfg_ack_rx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_ack_tx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_nak_rx
#                                    Total number of IPCP responses receive
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_nak_tx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_rej_rx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_rej_tx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_req_rx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.ipcp_cfg_req_tx
#                                    Total number of IPCP responses received
#                                    (IPv4)*
#    session.<session ID>.lcp_cfg_ack_rx
#                                    Total number of Configure-Acknowledge
#                                    packets received
#    session.<session ID>.lcp_cfg_ack_tx
#                                    Total number of Configure-Acknowledge
#                                    packets sent
#    session.<session ID>.lcp_cfg_nak_rx
#                                    Total number of Configure-Negative-
#                                    Acknowledge packets received
#    session.<session ID>.lcp_cfg_nak_tx
#                                    Total number of Configure-Negative-
#                                    Acknowledge packets sent
#    session.<session ID>.lcp_cfg_rej_rx
#                                    Total number of Configure-Reject packets
#                                    received
#    session.<session ID>.lcp_cfg_rej_tx
#                                    Total number of Configure-Reject packets
#                                    sent
#    session.<session ID>.lcp_cfg_req_rx
#                                    Total number of Configure-Request packets
#                                    received
#    session.<session ID>.lcp_cfg_req_tx
#                                    Total number of Configure-Request packets
#                                    sent
#    session.<session ID>.padi_rx
#                                    Total number of PPPoE Active Discovery
#                                    Initialized packets received
#    session.<session ID>.padi_tx
#                                    Total number of PPPoE Active Discovery
#                                    Initialized packets sent
#    session.<session ID>.pado_rx
#                                    Total number of PPPoE Active Discovery
#                                    Offer packets received
#    session.<session ID>.pado_tx
#                                    Total number of PPPoE Active Discovery
#                                    Offer packets sent
#    session.<session ID>.padr_rx
#                                    Total number of PPPoE Active Discovery
#                                    Request packets received
#    session.<session ID>.padr_tx
#                                    Total number of PPPoE Active Discovery
#                                    Request packets sent
#    session.<session ID>.pads_rx
#                                    Total number of PPPoE Active Discovery
#                                    Session-confirmation packets received
#    session.<session ID>.pads_tx
#                                    Total number of PPPoE Active Discovery
#                                    Session-confirmation packets sent
#    session.<session ID>.padt_rx
#                                    Total number of PPPoE Active Discovery
#                                    Terminate packets received
#    session.<session ID>.padt_tx
#                                    Total number of PPPoE Active Discovery
#                                    Terminate packets sent
#    session.<session ID>.pap_auth_ack_rx
#                                    Total number of PAP responses received*
#    session.<session ID>.pap_auth_nak_rx
#                                    Total number of PAP responses sent*
#    session.<session ID>.pap_auth_req_tx
#                                    Total number of PAP responses received*
#    session.<session ID>.setup_time
#                                    Amount of time taken to bring up the
#                                    session
#    session.<session ID>.term_ack_rx
#                                    Total number of Terminate-Acknowledge
#                                    packets received
#    session.<session ID>.term_ack_tx
#                                    Total number of Terminate-Acknowledge
#                                    packets sent
#    session.<session ID>.term_req_rx
#                                    Total number of Terminate-Request packets
#                                    received
#    session.<session ID>.term_req_tx
#                                    Total number of Terminate-Request packets
#                                    sent
#
#  * indicates the statistic is not fully supported and only gives the aggregate
#    count
#
# Description:
#    The sth::pppox_stats function retrieves a list of aggregate
#    statistics for the PPPoE session configured on the specified port.
#
#    NOTE:In version 1.24, -handle was passed as a string value. In version
#         1.30, -handle was passed as an integer. In version 2.x, -handle is
#         passed as an ALPHANUMERIC value.
#
# Examples:
#    When you call sth::pppox_stats, the contents of the returned keyed list
#    depends on the status of the call. For example:
#
#    sth::pppox_stats -handle host1
#
#    Returns a list that contains one of the following:
#
#    a)   If the call is successful, the list contains aggregate stats and
#         command execution status (in this case, a 1 indicating success).
#
#    b)   If the call fails, the list contains error log and command
#         execution status (in this case, a 0 indicating failure).
#
# Sample Input:
#    sth::pppox_stats -handle host2 -mode aggregate
#
# Sample Output:
#  {status 1} {aggregate {{term_req_rx 0} {term_ack_tx 0} {ipcp_cfg_rej_tx 6}a
#  {padr_rx 0} {lcp_cfg_rej_tx 0} {padt_tx 1} {pap_auth_ack_rx 0} {term_req_tx
#  1} {ipcp_cfg_ack_rx 6} {connect_success 2} {lcp_cfg_ack_rx 2} {num_sessions
#  1} {echo_req_rx 0} {chap_auth_fail_rx 0} {padr_tx 2} {max_setup_time 156}
#  {disconnect_success 1} {chap_auth_chal_rx 0} {echo_rsp_tx 0}
#  {pads_rx 2} {chap_auth_succ_rx 0} {ipcp_cfg_req_rx 6} {sessions_up 1}
#  {pap_auth_nak_rx 0} {ipcp_cfg_ack_tx 6} {ipcp_cfg_nak_rx 6}
#  {disconnect_failed 0} {lcp_cfg_req_rx 2} {padi_rx 0} #{lcp_cfg_ack_tx 2}
#  {lcp_cfg_nak_rx 0} {min_setup_time 149} {success_setup_rate 6}
#  {chap_auth_rsp_tx 0} {term_ack_rx 0} {pads_tx 0} {pap_auth_req_tx 0}
#  {ipcp_cfg_rej_rx 6} {ipcp_cfg_req_tx 6} {sessions_down 0} {lcp_cfg_rej_rx 0}
#  {ipcp_cfg_nak_tx 6} {lcp_cfg_req_tx 2} {padi_tx 2} {padt_rx 0}
#  {lcp_cfg_nak_tx 0} {connect_attempts 2} {avg_setup_time 152} {pado_rx 2}
#  {connecting 0} {connected 1} {disconnecting 0} {idle 0} {atm_mode
#  0}}} {procName sth::pppox_stats} {handles host2}
#
#  If there is an error, you will see: {status 0} {log {Error message }}
#
# Notes:
#    None
#
# End of Procedure Header

proc ::sth::pppox_stats { args } {
    set procName [lindex [info level [info level]] 0]

    variable ::sth::Pppox::sortedSwitchPriorityList
    variable ::sth::Pppox::userArgsArray
    array unset ::sth::Pppox::userArgsArray
    array set ::sth::Pppox::userArgsArray {}

    set _hltCmdName "pppox_stats"

    ::sth::sthCore::Tracker "::sth::pppox_stats" $args
    set sessionStartIndex 0
    set underScore "_"
    set modeVal aggregate; #default
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

	set retVal [catch {
		if {[catch {::sth::sthCore::commandInit ::sth::Pppox::pppoxTable $args ::sth::Pppox:: $_hltCmdName ::sth::Pppox::userArgsArray ::sth::Pppox::sortedSwitchPriorityList} err]} {
			::sth::sthCore::processError returnKeyedList "Error in $procName: $err"
			return $returnKeyedList
		}

		if {!([info exists ::sth::Pppox::userArgsArray(handle)] ||
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "ERROR in $procName: The command $_hltCmdName requires -port_handle or -handle."
			return $returnKeyedList
		}
		if {([info exists ::sth::Pppox::userArgsArray(handle)] &&
			  [info exists ::sth::Pppox::userArgsArray(port_handle)])} {
			::sth::sthCore::processError returnKeyedList "The options -port_handle or -handle are mutually exclusive."
			return $returnKeyedList
		}

		# Old retry option (relic of AX) -- retry is located in the pppox control command
		if {[info exists ::sth::Pppox::userArgsArray(retry)]} {

			# Check that PPPoX is idle (not busy) until CR 116178231 can be fixed 
			# Modifying/configuring while session is connected will terminate the
			# engine
			set portHandleList ""
			set err 1
			if {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
				foreach handle $userArgsArray(port_handle) {
					if {! [catch {::sth::sthCore::invoke stc::get $handle} err]} {
						lappend portHandleList $handle
					}
				}
				set err 0
			}
			if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
				foreach host $userArgsArray(handle) {
					set port  [::sth::sthCore::invoke stc::get $host "-AffiliationPort-Targets"]
					set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockConfig
					if {! [catch { lappend handleList [::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] } err]} {
						lappend portHandleList [::sth::sthCore::invoke stc::get $host -affiliationPORT-Targets]
					}
				}
				set err 0
			}
			if {! $err} {
				set none 0; set idle 0; set connecting 0; set disconnecting 0; set connected 0; set terminating 0;
				foreach curPort $portHandleList {
					foreach pppoxportconfig [::sth::sthCore::invoke stc::get $curPort -children-pppoxportCONFIG] { set port_state [string tolower [stc::get $pppoxportconfig -portstate]] ; incr $port_state }
				}
				if {$connecting || $connected || $disconnecting || $terminating} {
					set result "Error in $_hltCmdName: This command should not be sent until engine is idle state. Please check \"sth::pppox_stats -mode aggregate\" to see that aggregate.idle is 1 before sending again. "
					::sth::sthCore::processError returnKeyedList $result
					return $returnKeyedList
				}
			}

			if {$userArgsArray(retry) == "false" || $userArgsArray(retry) == "0"} {
				return $returnKeyedList
			}

			if {! [info exists ::sth::Pppox::userArgsArray(handle)]} {
				::sth::sthCore::processError returnKeyedList "The -retry option requires -handle to be specified."
				return $returnKeyedList
			}
			foreach host $userArgsArray(handle) {
				set port  [::sth::sthCore::invoke stc::get $host "-AffiliationPort-Targets"]
				set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockConfig
				if {[catch { lappend handleList [::sth::sthCore::invoke stc::get $host -children-$PppoxClientBlockConfig] } err]} {
					::sth::sthCore::processError returnKeyedList "Error in $procName: PPPoX should be configured under the handle ($host) when retrying sessions. Please check the handle."
					return $returnKeyedList
				}
			}
			if {[catch {::sth::sthCore::invoke stc::perform PppoxRetry -BlockList $handleList} err]} {
				::sth::sthCore::processError returnKeyedList "Error: $err"
				return $returnKeyedList
			}
			# Give the PPPoX engine time to kick off the retry before requesting stats
			after 5000
		}

		if {[info exists ::sth::Pppox::userArgsArray(mode)]} {
			set modeVal $userArgsArray(mode)
		}
		if {$modeVal == "session" && [info exists ::sth::Pppox::userArgsArray(port_handle)]} {
			::sth::sthCore::processError returnKeyedList "Error: Session stats requires -handle, not -port_handle."
			return $returnKeyedList
		}

		set handle ""
		#Validate if the value of port_handle is valid
		set result_handle_list ""
		set sessionblock_handle_list ""
		if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
			foreach handle $userArgsArray(handle) {
				set port  [::sth::sthCore::invoke stc::get $handle "-AffiliationPort-Targets"]
				set PppoxClientBlockConfig [set ::sth::Pppox::PPPOXCLIENTROBJTYPE($port)]ClientBlockConfig
				lappend sessionblock_handle_list [::sth::sthCore::invoke stc::get $handle -children-$PppoxClientBlockConfig]
			}
			if {$modeVal == "session"} {
	#            foreach handle_element $sessionblock_handle_list {
	#                if {[catch {set devCount [stc::get [stc::get $handle_element -parent] -deviceCount]} err]} {
	#                    set result "Count not retrieve deviceCount under host $host"
	#                    #puts "DEBUG:$result"
	#                    keylset returnKeyedList log $result
	#                    keylset returnKeyedList status $::sth::sthCore::FAILURE
	#                    return $returnKeyedList
	#                }
	#                if {[catch { set diff [stc::get $handle_element -children-pppoesessionresults] } err]} {
	#                    set result "$err"
	#                    #puts "DEBUG:$result"
	#                    keylset returnKeyedList log $result
	#                    keylset returnKeyedList status $::sth::sthCore::FAILURE
	#                    return $returnKeyedList
	#                }
	#                set devCount [expr "$devCount - [llength $diff]"]
	#                for {set devIdx 0} {$devIdx < $devCount} {incr devIdx} {
	#                    if {[catch { set createdPppoeSessionResults [::sth::sthCore::invoke stc::create PppoeSessionResults -under $handle_element] } err]} {
	#                        set result "Error in $procName while trying to create a PPPoE session results object to retrieve stats for. Msg: $err"
	#                        #puts "DEBUG:$result"
	#                        keylset returnKeyedList log $result
	#                        keylset returnKeyedList status $::sth::sthCore::FAILURE
	#                        return $returnKeyedList
	#                    }
	#                }
	#                lappend result_handle_list [stc::get $handle_element -children-pppoesessionresults]
	#            }
			} else {
				# Grab the port from the session
				# If this is stacked VLAN, just grab the first
				foreach handle_element $sessionblock_handle_list {
					lappend result_handle_list [::sth::sthCore::invoke stc::get [stc::get [stc::get [stc::get $handle_element -parent] -affiliationport-targets] -children-PppoxPortConfig] -children-pppoeportresults]
					break;
				}
			}
		} elseif {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
			lappend result_handle_list [::sth::sthCore::invoke stc::get [stc::get $userArgsArray(port_handle) -children-PppoxPortConfig] -children-pppoeportresults]
		}
	#    regsub -all {\{|\}} $result_handle_list "" result_handle_list

		set msg ""

		switch -exact -- $modeVal {
			aggregate {
				foreach result_handle $result_handle_list {
					foreach name [array names ::sth::Pppox::pppox_stats_${modeVal}_stcattr] {
						set procFunc [set ::sth::Pppox::pppox_stats_${modeVal}_procfunc($name)]
						if {$procFunc == "_none_"} {continue}
						#if {[catch {$procFunc $name returnKeyedList ${modeVal} $result_handle} err]} {}
						if {[catch {::sth::Pppox::$procFunc $name returnKeyedList ${modeVal} $result_handle} err]} {
							set cmdFailed 1
							#puts "DEBUG:$err"
							::sth::sthCore::processError returnKeyedList $err
							break
						}
					}
				}
				# Set the port state
				if {[catch { ::sth::Pppox::processPPPOXGetCmd_state $name returnKeyedList ${modeVal} [::sth::sthCore::invoke stc::get $result_handle -parent] } err]} {
					#puts "DEBUG:$err"
					::sth::sthCore::processError returnKeyedList $err
				}
				keylset returnKeyedList ${modeVal}.atm_mode "0"
			}
			session {
				# According to GK, this should create the sessionresults, doesn't seem to do so in the case of no apply or no connect being done prior to calling
				if {[catch {::sth::sthCore::invoke stc::perform PppoxSessionInfo -BlockList $sessionblock_handle_list -saveToFile FALSE} err]} {
					set result "$err"
					#puts "DEBUG:$result" 
					::sth::sthCore::processError returnKeyedList $result
					return $returnKeyedList
				}
				foreach handle_element $sessionblock_handle_list {
					if {[catch { lappend result_handle_list [::sth::sthCore::invoke stc::get $handle_element -children-pppoesessionresults] } err]} {
						set result "$err"
						#puts "DEBUG:$result"
						::sth::sthCore::processError returnKeyedList $result
						return $returnKeyedList
					}
				}
				regsub -all {\{|\}} $result_handle_list "" result_handle_list
                                set sessionStartIndex [::sth::sthCore::invoke stc::get [lindex $result_handle_list 0] -pppoeSessionId]
                                set curPppoeSessionId 1
				foreach result_handle $result_handle_list {
                                        
					foreach name [array names ::sth::Pppox::pppox_stats_${modeVal}_stcattr] {
						#if {[catch { set curPppoeSessionId [::sth::sthCore::invoke stc::get $result_handle -pppoeSessionId] } err]} {
						#	set result "Could not retrieve PPPoE session ID for session stats:$err"
						#	#puts "DEBUG:$result" 
						#	::sth::sthCore::processError returnKeyedList $result
						#	return $returnKeyedList
						#}
                                                
						set procFunc [set ::sth::Pppox::pppox_stats_${modeVal}_procfunc($name)]
						if {$procFunc == "_none_"} {continue}
						#if {[catch {$procFunc $name returnKeyedList ${modeVal} $result_handle} err]} {}
                                                
						if {[catch {::sth::Pppox::$procFunc $name returnKeyedList ${modeVal} $curPppoeSessionId $result_handle} err]} {
							
                                                        set cmdFailed 1
							#puts "DEBUG:$err"
							::sth::sthCore::processError returnKeyedList $err
							break
						}
                                           
					}
                               incr curPppoeSessionId
				}
			}
			SHA_NO_USER_INPUT {
				::sth::sthCore::processError returnKeyedList "No Value for the switch: mode Value:$modeVal."
				return $returnKeyedList
			}
			SHA_UNKNWN_SWITCH -
			default {
				::sth::sthCore::processError returnKeyedList "Unable to process -mode value: $modeVal"
				return $returnKeyedList
			}
		}

		keylset returnKeyedList procName $procName
		if {[info exists ::sth::Pppox::userArgsArray(port_handle)]} {
			keylset returnKeyedList port_handle $userArgsArray(port_handle)
		}
		if {[info exists ::sth::Pppox::userArgsArray(handle)]} {
			keylset returnKeyedList handles $userArgsArray(handle)
		}
	}  returnedString]
	
	if {$retVal} {
        ::sth::sthCore::processError returnKeyedList $returnedString
    } else {
	    keylset returnKeyedList status $::sth::sthCore::SUCCESS
	}

    if { $modeVal eq "session"} {
       
      set total_sessions [keylget returnKeyedList session]
      set no_of_total_sessions [llength "$total_sessions"]
      foreach name [array names ::sth::Pppox::pppox_stats_${modeVal}_stcattr] {
          set final 0
          set final_ips ""
          for {set each_sess 1} {$each_sess <= $no_of_total_sessions} {incr each_sess} {
              if {[keylget returnKeyedList session.$each_sess sessExists]} {
                  set temp [keylget returnKeyedList session.$each_sess.$name]
                  if {$name ne "ipv6_global_addr" && $name ne "ip_addr" && $name ne "ipv6_addr"} {
                      set final [expr {$final +$temp}]
                  } else {
                      lappend final_ips $temp
                  }
               }

          }
         
         if {$name eq "ipv6_global_addr" || $name eq "ip_addr" || $name eq "ipv6_addr"} { 
            keylset returnKeyedList agg.$name $final_ips
         } else {
             keylset returnKeyedList agg.$name $final
           }
         
       }
      
      return $returnKeyedList

    } else {
    
    return $returnKeyedList
    }
    
}
