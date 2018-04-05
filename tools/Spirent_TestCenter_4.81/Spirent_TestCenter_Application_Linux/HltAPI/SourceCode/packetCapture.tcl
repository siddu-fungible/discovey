# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx

namespace eval ::sth:: {
}


##Procedure Header
#
# Name:
#    sth::packet_config_buffers
#
# Purpose:
#    Defines how Spirent HLTAPI will manage the buffers for packet
#    capturing.
#
# Synopsis:
#    sth::packet_config_buffers
#            -port_handle <handle>
#            -action {wrap|stop}
#
# Arguments:
#
#    -port_handle
#                   Specifies the handle of the port on which buffers will be
#                   managed. This argument is required. To apply the
#                   sth::packet_config_buffers function to all ports, specify
#                   "all" instead of a handle (for example, -port_handle all).
#
#    -action        Specifies the action to perform when the buffer is full.
#                   The only possible value for the HLTAPI for Spirent
#                   TestCenter 2.0 is "wrap", which is also the default.
#
# Return Values:
#    The sth::packet_config_buffers function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::packet_config_buffers function configures how Spirent HLTAPI
#    manages buffers on the specified port. You determine what happens when the
#    packet capture buffer becomes full. Use the -action argument to specify
#    whether to stop packet capture or to allow packet capture to continue even
#    after the buffer is full. The default and only option at this time is
#    "wrap." The -action wrap argument discards the first packets and replaces
#    them by the last captured packets until packet capturing stops.
#
# Examples:
#
#    sth::packet_config_buffers -port_handle port1 -action wrap
#
#    sth::packet_config_buffers -port_handle all -action wrap
#
#
# Sample output:
#
#    {status 1}
#
# Notes:
#    Spirent HLTAPI 2.00 does not yet support the "-action stop" option.
#
# End of Procedure Header
###
#  Name:    sth::packet_config_buffers
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description: hltapi command packet_config_buffers - change the buffer management between
#           wrap (earlier packets are overwritten when the buffer fills up) and stop (packet
#           capturing stops when the buffer is full).
#  Notes:   STC only supports wrap at this time.
###
proc ::sth::packet_config_buffers { args } {
    ::sth::sthCore::Tracker ::sth::packet_config_buffers $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
 
    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List - default status to FAILURE until command passes.
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_config_buffers $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_config_buffers \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }

    set cmdStatus $FAILURE
    set cmd "::sth::packetCapture::packet_config_buffers {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {set procResult [eval $cmd]} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }
    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_config_buffers ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::packet_control
#
# Purpose:
#    Starts or stops packet capturing.
#
# Synopsis:
#    sth::packet_control
#         -port_handle <handle>
#         -action {start|stop}
#
# Arguments:
#
#    -port_handle
#                   Identifies the handle of the port on which to start or stop
#                   capturing data packets. This argument is required. You can
#                   specify "all" to apply this function to all ports (for
#                   example, -port_handle all).
#
#    -action
#                   Specifies the action to perform. Possible values are start
#                   and stop, This argument is required. The actions are
#                   described below:
#
#                   start - Start capturing packets.
#
#                   stop - Stop capturing packets.
#
# Return Values:
#    The sth::packet_control function returns a keyed list using the
#    following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::packet_control function controls when Spirent HLTAPI starts
#    and when it stops capturing data packets.
#
#    The type of data captured is provided by the sth::packet_config_buffers,
#    sth::packet_config_triggers, and sth::packet_config_filter functions.
#    If these functions have not been defined correctly, Spirent HLTAPI
#    cannot start packet capturing and will return an error message.
#
#
# Examples:
#
#    To start data capturing on all ports:
#
#    sth::packet_control -port_handle all -action start
#
#    To start data capturing on port 1:
#
#    sth::packet_control -port_handle port1 -action start
#
#    To stop data capturing on port 1:
#
#    sth::packet_control -port_handle port1 -action stop
#
#
# Sample output:
#
#    {status 1}
#
# Notes:
#    None.
#
# End of Procedure Header
###
#  Name:    sth::packet_control
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description: hltapi command packet_control - start and stop capture.
###
proc ::sth::packet_control { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_control $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList


    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_control $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_control \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0
    set cmd "::sth::packetCapture::packet_control {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {set procResult [eval $cmd]} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }
    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_control ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::packet_stats
#
# Purpose:
#    Returns statistical information about each packet associated with the
#    specified port(s). Each captured packet is timestamped and saved to a pcap
#    file. Statistics include the connection status and number and type of
#    messages sent and received from the specified port.
#
# Synopsis:
#    sth::packet_stats
#         -port_handle <handle>
#         -action filtered
#         [-stop {0|1}]
#         [-format pcap ]
#         [-filename <filename>]
#
# Arguments:
#
#    -port_handle
#                   The handle of the port on which to return packet capture
#                   information. This argument is required. You can specify
#                   "all" to apply this function to all ports (for example,
#                   -port_handle all).
#
#    -action
#                   Specifies the action to perform. The only option suppported 
#                   in this release is "filtered". This argument is required
#                   and returns all filtered information, based on the
#                   filters specified with the sth::packet_config_filter 
#                   function.
#
#    -stop
#                   Either stops capturing data or does not stop capturing data
#                   while packets are being saved to a file. This argument
#                   is equivalent to "sth::packet_control -action stop" except
#                   incorporated into the info command to reduce the amount of
#                   commands issued. Valid values are 0 and 1. If you specify 0,
#                   nothing happens. Use 0 when you do not want to remove this
#                   option but want to test returning the information without
#                   stopping. If you specify 1, Spirent HLTAPI stops
#                   capturing data and returns the information requested with
#                   the -action argument. The default is 1.
#
#                   You must stop data capturing on the port before packets can
#                   be saved. Otherwise, packets being received while other
#                   packets are being saved will be lost. Data capture
#                   automatically restarts once the save-to-file command
#                   finishes.
#
#    -format
#                   Specifies the format in which data is returned. The default
#                   and only option supported in this release is pcap, which
#                   returns the data in ethereal format.
#
#    -filename
#                   Provide a file name to which to save the captured packets.
#                   Specify the file format with the -format argument (for
#                   example, "-format pcap"). The default file name and format 
#                   is Spirent_TestCenter-<timestamp>-<port_handle>.pcap 
#                   (for example, Spirent_TestCenter-1179466942-port1.pcap).
#
# Return Values:
#    The sth::packet_stats function returns a keyed list using the
#    following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
#    result    Information about the captured packet. This key is not supported 
#              in Spirent HLTAPI.
#
# Description:
#    The sth::packet_stats function saves the timestamped data packets to a
#    pcap file. If the data capture is not set to "stop" (that is, -stop is set
#    to 0) while captured packets are being saved from the hardware device, the
#    data capture procedure will restart once the save-to-file command finishes.
#    This method is not recommended because you may lose packets being received
#    at the same time the captured packets are being saved. We recommend that
#    you stop the data capture process on the port before saving packets.
#
#
# Examples:
#    The following example returns statistical information for all ports:
#
#    sth::packet_stats \
#         -port_handle all \
#         -stop 1
#         -action all \
#         -format pcap \
#         -filename spirent-2305062301-104.pcap
#
#
# Sample output:
#
#
# Notes:
#    None.
#
# End of Procedure Header
###
#  Name:    sth::packet_stats
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description:  Save the captured packets to a file (or someplace else later when STC supports this feature).
###
proc ::sth::packet_stats { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_stats $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList
    
    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_stats $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_stats \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0

    set cmd "::sth::packetCapture::packet_stats {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {::sth::packetCapture::packet_stats {$args} returnKeyedList cmdStatus} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }

    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_stats ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::packet_config_filter
#
# Purpose:
#    Defines how Spirent HLTAPI will filter the captured data. If you do not
#    define any filters, Spirent HLTAPI captures all data.
#
# Synopsis:
#    sth::packet_config_filter
#            -port_handle <handle>
#            [-mode {add|remove}]
#            [-filter {signature|jumbo|oversize|undersize|invalidfcs|ipchksum|
#              oos|length <0-4294967295>|prbs|pattern <pattern_sequence>}]
#
# Arguments:
#
#    -port_handle
#                   The handle of the port on which the data will be filtered.
#                   This argument is required. You can specify "all" to apply
#                   this function to all ports (for example, -port_handle all).
#
#    -mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Adds or removes all filters specified with the -filter
#                   argument. Possible values are add and remove. The default
#                   value is add. The modes are described below:
#
#                   add - Adds the specified filters.
#
#                   remove - Removes the specified filters.
#
#                   Note: You can remove filters that you had not previously
#                   added without causing an error. For example, you can specify
#                   "-mode remove" to clear all filters from the capture. Also,
#                   when removing either the "length" or "pattern" filter, you
#                   do not have to specify the value of the length nor pattern
#                   as you do when defining that filter. For example, you can
#                   use "-mode remove -filter length" instead of "-mode remove 
#                   -filter length 24".
#
#    -filter
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Defines the type of packet that will be captured. Only
#                   packets matching the filter will be captured. This argument
#                   is optional. If you do not define a filter, Spirent
#                   TestCenter captures all data. You cannot specify more than
#                   one filter at a time. That is, you can only specify one
#                   filter in each sth::packet_config_filter function call.
#                   The filters you can define are described below:
#
#                   signature - frames with a signature tag
#
#                   oversize - oversize frames
#
#                   jumbo - jumbo frames
#
#                   undersize - undersize frames
#
#                   invalidfcs - frames with invalid FCS
#
#                   ipchksum - IP header checksum error
#
#                   oos - Out of sequence error (requires signature support)
#
#                   length <length> - frames matching a specified length, where
#                        <length> is a value from 0 to 4294967295.
#
#                   prbs - frame with PRBS (pseudorandom bit sequence) errors
#
#                   pattern <pattern_sequence> - frames matching a given 
#                        pattern. A pattern_sequence is a list of patterns that 
#                        are linked together by logical operators (AND | OR). A
#                        pattern is a list of the following:
#
#                        -frameconfig - a list of protocol data units (PDUs)
#                             linked by colons (for example, ethernetii:ipv4).
#
#                        -pdu <pdu>:[index] - a PDU such as ipv4 or arp (address 
#                             resolution protocol). In addition to taking a PDU 
#                             as a value, the -pdu option can also take an 
#                             index. Index starts from 1 and increases the 
#                             further inside the packet the PDU appears.
#
#                             Note: If you do not include an index value, 
#                             Spirent HLTAPI filters on the first PDU of the 
#                             given type regardless of how many PDUs of that 
#                             type appear in the packet.
#
#                        -value - value that is to be filtered on (ie 192.1.1.1)
#
#                        -field - field in the specified PDU that the value
#                             exists in (ie senderpaddr in arp PDU)
#
#                        The following pattern sequence can be used to filter
#                        out ARP requests from client 192.1.1.2 to the target
#                        192.1.1.1:
#
#                        {{-frameconfig ethernetii:arp -pdu arp -field
#                        senderpaddr -value 192.1.1.1} AND {-frameconfig
#                        ethernetii:arp -pdu arp -field targetpaddr -value
#                        192.1.1.1}}
#
#                        If you are filtering on an inner VLAN, you must use an 
#                        index to specify which VLAN to filter on (inner or 
#                        outer), as in the following example:
#
#                        sth::packet_config_filter -port_handle port1 -pattern \
#                        {filter {{-frameconfig "ethernetii:vlan:vlan:ipv4" \
#                        -pdu "vlan:2" -value 1000 -field "id"}}}
#
#
#                        If you are filtering on an outer VLAN, you can use 
#                        either one of the following examples:
#
#                        sth::packet_config_filter -port_handle port1 -pattern \
#                        {filter {{-frameconfig "ethernetii:vlan:vlan:ipv4"
#                        -pdu "vlan" -value 500 -field "id"}}}
#
#                        sth::packet_config_filter -port_handle port1 -pattern \
#                        {filter {{-frameconfig "ethernetii:vlan:vlan:ipv4"
#                        -pdu "vlan:1" -value 500 -field "id"}}}
#
#
#                   Note: The PDUs specified in the -frameconfig and -pdu 
#                   arguments must be standard PDU names given in the Notes 
#                   section below. (Spirent HLTAPI only recognizes the PDUs 
#                   listed.) Likewise, the -field argument must be a valid 
#                   string recognized by Spirent HLTAPI.
#
# Return Values:
#    The sth::packet_config_filter function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::packet_config_filter function limits the type of data packets that
#    are captured. Use the -filter argument to specify the type of data to
#    include from the capture. The filter compares the network traffic to the
#    specified criteria and copies data packets that meet the criteria to the
#    buffer on the hardware until the sth::packet_stats function is called.
#    Then the data is copied to the file specified in the sth::packet_stats
#    function.
#
#    You can specify only one filter from the list of available filters to
#    determine which data packets you want to include in the capture. If you
#    do not specify a filter, Spirent HLTAPI includes all data packets in
#    the capture.
#
#    A pattern filter is defined as follows:
#
#    -filter {pattern {<pattern1>} <logical_operator1> {<pattern2>} \
#         <logical_operator2>... <logical_operatorN-1> {<patternN>}
#
#    <patternX> is defined as list of attributes: {-frameconfig <pdu_list> \
#         -pdu <pdu> -field <field_name> -value <field_value>}
#
#    Attribute      Description                             Example
#
#    frameconfig    A list of colon separated PDUs*,        -frameconfig
#                   <pdu1>:<pdu2>:...<pduN>                 "ethernetii:ipv4"
#
#    pdu            The PDU in which the value to           -pdu "ipv4"
#                   filter on appears.
#
#    field          The name of the field on which to       -field sourceaddr
#                   filter.
#
#    value          The value to filter on for the given     -value 192.1.1.2
#                   field in the given PDU. The valid values
#                   here will depend on what the field is and
#                   in which PDU it is in.
#
#    *List of valid PDUs and fields appear in the Notes section for this
#    function. Refer to the Spirent TestCenter Automation Object Reference
#    guide's "Protocol Data Unit Objects Index" section for more information,
#    such as valid values for the given fields.
#
#    <logical_operator> is either "AND" or "OR".
#
#    The pattern must be defined as a list containing the keyword "filter" and
#    another list containing the pattern sequence itself. This pattern sequence
#    list must contain at least one pattern (also in a list) and possibly others
#    linked by either AND or OR.  Even if only one pattern is defined, the
#    pattern must be contained in a list within the pattern sequence.
#
#    For example, to capture packets with source IP 192.1.1.2, the pattern would
#    look as follows:
#
#    {-frameconfig "ethernetii:ipv4" -pdu "ipv4" -field "sourceaddr"
#         -value 192.1.1.2}
#
#    The HLTAPI command would look as follows:
#
#    sth::packet_config_filter -port_handle $port_handle -mode "add" -filter
#    {pattern {{-frameconfig "ethernetii:ipv4" -pdu "ipv4" -field "sourceaddr"
#    -value 192.1.1.2}}}
#
#    Note the extra set of braces around the pattern. As another example, say we
#    want to capture ARP packets where the sender’s IP is 192.1.1.2, the target
#    IP is 192.1.1.1, and the sender’s MAC address is 1A:1A:1A:12:12:12. The
#    HLT command would look as follows:
#
#    sth::packet_config_filter -port_handle $port_handle -filter {pattern {{-
#    frameconfig "ethernetii:arp" -pdu "arp" -field "senderpaddr" -value
#    192.1.1.2} AND {-frameconfig "ethernetii:arp" -pdu "arp" -field
#    "targetpaddr" -value 192.1.1.1} AND {-frameconfig "ethernetii:arp" -pdu
#    "arp" -field "senderhwaddr" -value 1A:1A:1A:12:12:12}}}
#
#    If the pattern filter is sent down to a port multiple times, each
#    successive command overwrites the previous pattern.
#
# Examples:
#
#    To capture only data packets with a signature tag:
#
#    sth::packet_config_filter -port_handle $portHandle \
#         -mode add
#         -filter signature
#
#    To capture only data packets with specific IP, MAC, Int, and Hex values in
#    ARP PDU:
#
#    sth::packet_config_filter -port_handle $portHandle \
#        -filter {pattern {  \
#             {-frameconfig ethernetii:arp -pdu arp -field protocol \
#              -value ABCD} AND \
#             {-frameconfig ethernetii:arp -pdu arp -field operation \
#              -value 4} AND \
#             {-frameconfig ethernetii:arp -pdu arp -field senderpaddr \
#              -value 192.1.1.2} AND \
#             {-frameconfig ethernetii:arp -pdu arp -field senderhwaddr \
#              -value AB:CD:EF:12:34:56}}}
#
#    To remove a specified pattern filter:
#
#    sth::packet_config_filter -port_handle $portHandle \
#         -filter pattern -mode remove
#
# Sample output:
#
#    {status 1}
#         
# Notes:
#    PDUs and Fields
#
#    PDU                      FIELD                        TYPE
#
#    accookietag              value                         none
#                             length                        none
#                             type                          none
#
#    acnametag                value                         none
#                             length                        none
#                             type                          none
#
#    acsystemerrortag         value                         none
#                             length                        none
#                             type                          none
#
#    arp                      senderhwaddr                  mac
#                             ipaddr                        int
#                             senderpaddr                   ip
#                             hardware                      hex
#                             protocol                      hex
#                             ihaddr                        int
#                             operation                     int
#                             targethwaddr                  mac
#                             targetpaddr                   ip
#
#    atm                      clp                           none
#                             vpi                           none
#                             vci                           none
#
#
#    ciscohdlc                protocoltype                  none
#                             control                       none
#                             address                       none
#
#    controlflags             reserved                      none
#                             dfbit                         none
#                             mfbit                         none
#
#    custom                   pattern                       none
#
#    dhcpclientidhwtag        clienthwa                     none
#                             idtype                        none
#                             optionlength                  none
#                             type                          none
#
#    dhcpclientidnonhwtag     idtype                        none
#                             optionlength                  none
#                             value                         none
#                             type                          none
#
#    dhcpclientmsg            clienthwpad                   none
#                             bootfilename                  none
#                             xid                           none
#                             serverhostname                none
#                             messagetype                   none
#                             clientmac                     none
#                             hardwaretype                  none
#                             nextservaddr                  none
#                             haddrlen                      none
#                             hops                          none
#                             magiccookie                   none
#                             elapsed                       none
#                             relayagentaddr                none
#                             bootpflags                    none
#                             clientaddr                    none
#                             youraddr                      none
#
#    dhcpcustomoptiontag      value                         none
#                             length                        none
#                             type                          none
#
#    dhcphostnametag          value                         none
#                             length                        none
#                             type                          none
#
#    dhcpleasetimetag         leasetime                     none
#                             length                        none
#                             type                          none
#
#    dhcpmessagesizetag       value                         none
#                             length                        none
#                             type                          none
#
#    dhcpmessagetag           value                         none
#                             length                        none
#                             type                          none
#
#    dhcpmessagetypetag       code                          none
#                             length                        none
#                             type                          none
#
#    dhcpoptoverloadtag       overload                      none
#                             length                        none
#                             type                          none
#
#    dhcpreqaddrtag           reqaddr                       none
#                             length                        none
#                             type                          none
#
#    dhcpreqparamtag          value                         none
#                             length                        none
#                             type                          none
#
#    dhcpserveridtag          reqaddr                       none
#                             length                        none
#                             type                          none
#
#    dhcpservermsg            clienthwpad                   none
#                             bootfilename                  none
#                             xid                           none
#                             serverhostname                none
#                             messagetype                   none
#                             clientmac                     none
#                             hardwaretype                  none
#                             nextservaddr                  none
#                             haddrlen                      none
#                             hops                          none
#                             magiccookie                   none
#                             elapsed                       none
#                             relayagentaddr                none
#                             bootpflags                    none
#                             clientaddr                    none
#                             youraddr                      none
#
#    diffservbyte             reserved                      none
#                             dscplow                       none
#                             dscphigh                      none
#
#    encodedgroupipv4address  masklen                       none
#                             reserved                      none
#                             zbit                          none
#                             bbit                          none
#                             encodingtype                  none
#                             addrfamily                    none
#                             address                       none
#
#   encodedgroupipv6address   masklen                       none
#                             reserved                      none
#                             zbit                          none
#                             bbit                          none
#                             encodingtype                  none
#                             addrfamily                    none
#                             address                       none
#
#    encodedsourceipv4address encoding-type                 none
#                             wbit                          none
#                             address                       none
#                             rbit                          none
#                             masklen                       none
#                             addrfamily                    none
#                             reserved                      none
#                             sbit                          none
#
#    encodedsourceipv6address encoding-type                 none
#                             wbit                          none
#                             address                       none
#                             rbit                          none
#                             masklen                       none
#                             addrfamily                    none
#                             reserved                      none
#                             sbit                          none
#
#   encodedunicastipv4address encodingtype                  none
#                             addrfamily                    none
#                             address                       none
#
#   encodedunicastipv6address encodingtype                  none
#                             addrfamily                    none
#                             address                       none
#
#   endoflisttag              length                        none
#                             type                          none
#
#   endofoptionstag           type                          none
#
#   ethernet8022              dstmac                        none
#                             preamble                      none
#                             srcmac                        none
#                             length                        none
#
#   ethernet8023raw           dstmac                        none
#                             preamble                      none
#                             srcmac                        none
#                             length                        none
#
#    ethernetii               dstmac                        none
#                             preamble                      none
#                             srcmac                        none
#                             ethertype                     none
#
#    ethernetsnap             dstmac                        none
#                             preamble                      none
#                             srcmac                        none
#                             length                        none
#
#    genericerrortag          value                         none
#                             length                        none
#                             type                          none
#
#    gre                      version                       none
#                             ckpresent                     none
#                             reserved0                     none
#                             routingpresent                none
#                             seqnumpresent                 none
#                             endpointv4                    none
#                             protocoltype                  none
#                             endpointv6                    none
#                             keypresent                    none
#
#    grechecksum              reserved                      none
#                             value                         none
#
#    grekey                   value                         none
#
#    greseqnum                value                         none
#
#    grouprecord              mcastaddr                     none
#                             auxdatalen                    none
#                             numsource                     none
#                             recordtype                    none
#
#    hdrauthselectcrypto      authvalue1                    none
#                             authtype                      none
#                             authvalue2                    none
#
#    hdrauthselectnone        authvalue1                    none
#                             authtype                      none
#                             authvalue2                    none
#
#    hdrauthselectpassword    authvalue1                    none
#                             authtype                      none
#                             authvalue2                    none
#
#    hdrauthselectuserdef     authvalue1                    none
#                             authtype                      none
#                             authvalue2                    none
#
#    hostuniqtag              value                         none
#                             length                        none
#                             type                          none
#
#    icmpdestunreach          checksum                      none
#                             code                          none
#                             unused                        none
#                             type                          none
#
#    icmpechoreply            identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             data                          none
#                             type                          none
#
#    icmpechorequest          identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             data                          none
#                             type                          none
#
#    icmpinforeply            identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             type                          none
#
#    icmpinforequest          identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             type                          none
#
#    icmpipdata               data                          none
#
#    icmpparameterproblem     checksum                      none
#                             code                          none
#                             unused                        none
#                             pointer                       none
#                             type                          none
#
#    icmpredirect             checksum                      none
#                             code                          none
#                             gateway                       none
#                             type                          none
#
#    icmpsourcequench         checksum                      none
#                             code                          none
#                             unused                        none
#                             type                          none
#
#    icmptimeexceeded         checksum                      none
#                             code                          none
#                             unused                        none
#                             type                          none
#
#    icmptimestampreply       code                          none
#                             checksum                      none
#                             transmit                      none
#                             identifier                    none
#                             receive                       none
#                             seqnum                        none
#                             type                          none
#                             originate                     none
#
#    icmptimestamprequest     code                          none
#                             checksum                      none
#                             transmit                      none
#                             identifier                    none
#                             receive                       none
#                             seqnum                        none
#                             type                          none
#                             originate                     none
#
#    icmpv6destunreach        checksum                      none
#                             code                          none
#                             unused                        none
#                             type                          none
#
#
#    icmpv6echoreply          identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             data                          none
#                             type                          none
#
#    icmpv6echorequest        identifier                    none
#                             checksum                      none
#                             code                          none
#                             seqnum                        none
#                             data                          none
#                             type                          none
#
#    icmpv6ipdata             data                          none
#
#    icmpv6packettoobig       checksum                      none
#                             code                          none
#                             mtu                           none
#                             type                          none
#
#    icmpv6parameterproblem   checksum                      none
#                             code                          none
#                             pointer                       none
#                             type                          none
#
#    icmpv6timeexceeded       checksum                      none
#                             code                          none
#                             unused                        none
#                             type                          none
#
#    igmpv1                   groupaddress                  none
#                             checksum                      none
#                             unused                        none
#                             type                          none
#                             version                       none
#
#    igmpv2                   groupaddress                  none
#                             checksum                      none
#                             maxresptime                   none
#                             type                          none
#
#    igmpv3query              checksum                      none
#                             resv                          none
#                             numsource                     none
#                             groupaddress                  none
#                             sflag                         none
#                             qqic                          none
#                             maxresptime                   none
#                             qrv                           none
#                             type                          none
#
#    igmpv3report             numgrprecords                 none
#                             checksum                      none
#                             reserved                      none
#                             reserved2                     none
#                             type                          none
#
#    ip                       v6llprefixlength              none
#                             v6sourceaddr                  none
#                             v6trafficclass                none
#                             v6llhoplimit                  none
#                             ttl                           none
#                             sourceaddr                    none
#                             v6prefixlength                none
#                             v6gateway                     none
#                             v6llsourceaddr                none
#                             prefixlength                  none
#                             v6lltrafficclass              none
#                             gateway                       none
#                             v6hoplimit                    none
#
#    ipv4                     checksum                      none
#                             ihl                           none
#                             version                       none
#                             destprefixlength              none
#                             identification                none
#                             protocol                      none
#                             destaddr                      none
#                             ttl                           none
#                             sourceaddr                    none
#                             totallength                   none
#                             fragoffset                    none
#                             prefixlength                  none
#                             gateway                       none
#
#    ipv4addr                 value                         none
#
#
#  ipv4optionaddressextension dest7thbyte                   none
#                             sourceipv7                    none
#                             source7thbyte                 none
#                             destipv7                      none
#                             length                        none
#                             type                          none
#
#    ipv4optionendofoptions   type                          none
#
# ipv4optionextendedsecurity  addsecinfo                    none
#                             formatcode                    none
#                             length                        none
#                             type                          none
#
# ipv4optionloosesourceroute  pointer                       none
#                             length                        none
#                             type                          none
#
#    ipv4optionmtuprobe       mtu                           none
#                             length                        none
#                             type                          none
#
#    ipv4optionmtureply       mtu                           none
#                             length                        none
#                             type                          none
#
#    ipv4optionnop            type                          none
#
#    ipv4optionrecordroute    pointer                       none
#                             length                        none
#                             type                          none
#
#
#    ipv4optionrouteralert    routeralert                   none
#                             length                        none
#                             type                          none
#
#    ipv4optionsecurity       txcontrolcode                 none
#                             security                      none
#                             compartments                  none
#                             handlingrestrictions          none
#                             length                        none
#                             type                          none
#
# ipv4optionselectivebroadcastmode
#                             length                        none
#                             type                          none
#
# ipv4optionstreamidentifier  streamid                      none
#                             length                        none
#                             type                          none
#
# ipv4optionstrictsourceroute pointer                       none
#                             length                        none
#                             type                          none
#
#    ipv4optiontimestamp      timestamp                     none
#                             overflow                      none
#                             pointer                       none
#                             flag                          none
#                             length                        none
#                             type                          none
#
#    ipv4optiontraceroute     originatorip                  none
#                             returnhopcnt                  none
#                             outboundhopcnt                none
#                             idnumber                      none
#                             length                        none
#                             type                          none
#
#    ipv6                     payloadlength                 none
#                             version                       none
#                             hoplimit                      none
#                             destprefixlength              none
#                             flowlabel                     none
#                             nextheader                    none
#                             destaddr                      none
#                             sourceaddr                    none
#                             trafficclass                  none
#                             prefixlength                  none
#                             gateway                       none
#
#    ipv6addr                 value                         none
#
#    ipv6authenticationheader authdata                      none
#                             spi                           none
#                             reserved                      none
#                             nxthdr                        none
#                             seqnum                        none
#                             length                        none
#
#    ipv6customoption         data                          none
#                             type                          none
#
#    ipv6destinationheader    nxthdr                        none
#                             length                        none
#
#    ipv6encapsulationheader  paddata                       none
#                             authdata                      none
#                             nxthdr                        none
#                             payloaddata                   none
#                             spi                           none
#                             seqnum                        none
#                             length                        none
#
#    ipv6fragmentheader       fragoffset                    none
#                             ident                         none
#                             reserved                      none
#                             nxthdr                        none
#                             m_flag                        none
#                             length                        none
#
#    ipv6hopbyhopheader       nxthdr                        none
#                             length                        none
#
#    ipv6jumbopayloadoption   data                          none
#                             length                        none
#                             type                          none
#
#    ipv6pad1option           pad1                          none
#
#    ipv6padnoption           padding                       none
#                             padn                          none
#                             length                        none
#
#    ipv6routeralertoption    value                         none
#                             routeralert                   none
#                             length                        none
#
#    ipv6routingheader        reserved                      none
#                             nxthdr                        none
#                             segleft                       none
#                             routingtype                   none
#                             length                        none
#
#    joinprunev4grouprecord   numjoin                       none
#                             numprune                      none
#
#    joinprunev6grouprecord   numjoin                       none
#                             numprune                      none
#
#    lacp                     partnerportpriority           none
#                             actorsystemid                 none
#                             collectormaxdelay             none
#                             partnerreserved               none
#                             collectorinformation          none
#                             partnersystemid               none
#                             version                       none
#                             actorport                     none
#                             collectorreserved             none
#                             collectorinformationlength    none
#                             actorsystempriority           none
#                             partnerport                   none
#                             partnerinformation            none
#                             terminatorinformation         none
#                             partnersystempriority         none
#                             partnerinformationlength      none
#                             subtype                       none
#                             terminatorreserved            none
#                             terminatorinformationlength   none
#                             partnerstate                  none
#                             partnerkey                    none
#                             actorinformation              none
#                             actorportpriority             none
#                             actorreserved                 none
#                             actorinformationlength        none
#                             actorstate                    none
#                             actorkey                      none
#
#    mldv1                    mcastaddr                     none
#                             maxrespdelay                  none
#                             checksum                      none
#                             code                          none
#                             reserved                      none
#                             type                          none
#
#    mldv2grouprecord         mcastaddr                     none
#                             auxdatalen                    none
#                             numsource                     none
#                             recordtype                    none
#
#    mldv2query               code                          none
#                             checksum                      none
#                             resv                          none
#                             numsource                     none
#                             maxrespcode                   none
#                             groupaddress                  none
#                             sflag                         none
#                             qqic                          none
#                             reserved                      none
#                             qrv                           none
#                             type                          none
#
#    mldv2report              numgrprecords                 none
#                             checksum                      none
#                             unused                        none
#                             reserved2                     none
#                             type                          none
#
#    mpls                     dstmac                        none
#                             ttl                           none
#                             label                         none
#                             cos                           none
#                             sbit                          none
#
#    mtu                      reserved                      none
#                             mtu                           none
#                             length                        none
#                             type                          none
#
#    neighboradvertisement    code                          none
#                             checksum                      none
#                             oflag                         none
#                             rflag                         none
#                             sflag                         none
#                             targetaddress                 none
#                             reserved                      none
#                             type                          none
#
#    neighborsolicitation     checksum                      none
#                             code                          none
#                             reserved                      none
#                             targetaddress                 none
#                             type                          none
#
#    ospfv2asexternallsa      forwardingaddress             none
#                             externalroutetag              none
#                             externalroutemetric           none
#                             networkmask                   none
#
#    ospfv2attachedrouter     routerid                      none
#
#    ospfv2dd                 interfacemtu                  none
#                             sequencenumber                none
#
#    ospfv2ddoptions          msbit                         none
#                             ibit                          none
#                             reserved3                     none
#                             reserved4                     none
#                             mbit                          none
#                             reserved5                     none
#                             reserved6                     none
#                             reserved7                     none
#
#    ospfv2externallsaoptions reserved                      none
#                             ebit                          none
#
# ospfv2externallsatosmetric  externallsaroutetos           none
#                             ebit                          none
#                             forwardingaddress             none
#                             externallsaroutemetrics       none
#
#    ospfv2header             checksum                      none
#                             areaid                        none
#                             routerid                      none
#                             packetlength                  none
#                             type                          none
#                             version                       none
#
#    ospfv2hello         backupdesignatedrouter             none
#                             routerpriority                none
#                             routerdeadinterval            none
#                             designatedrouter              none
#                             hellointerval                 none
#                             networkmask                   none
#
#    ospfv2lsaheader          linkstateid                   none
#                             lssequencenumber              none
#                             advertisingrouter             none
#                             lstype                        none
#                             lsaage                        none
#                             lsalength                     none
#                             lschecksum                    none
#
#    ospfv2lsu                numberoflsas                  none
#
#    ospfv2neighbor           neighborid                    none
#
#    ospfv2networklsa         networkmask                   none
#
#    ospfv2options            ebit                          none
#                             mcbit                         none
#                             reserved0                     none
#                             eabit                         none
#                             npbit                         none
#                             reserved6                     none
#                             dcbit                         none
#                             reserved7                     none
#
#    ospfv2requestedlsa       linkstateid                   none
#                             advertisingrouter             none
#                             lstypewide                    none
#
#    ospfv2routerlsa          numberoflinks                 none
#                             routerlsareserved1            none
#
#    ospfv2routerlsalink      linkid                        none
#                             linkdata                      none
#                             routerlsalinktype             none
#                             routerlinkmetrics             none
#                             numrouterlsatosmetrics        none
#
#    ospfv2routerlsaoptions   ebit                          none
#                             bbit                          none
#                             reserved3                     none
#                             reserved4                     none
#                             reserved5                     none
#                             vbit                          none
#                             reserved6                     none
#                             reserved7                     none
#
#    ospfv2routerlsatosmetric routertoslinkmetrics          none
#                             routerlsametricreserved       none
#                             routerlsalinktype             none
#
#    ospfv2summaryasbrlsa     summarylsareserved1           none
#                             summarylsametric              none
#                             networkmask                   none
#
#    ospfv2summarylsa         summarylsareserved1           none
#                             summarylsametric              none
#                             networkmask                   none
#
# ospfv2summarylsatosmetric   routertoslinkmetrics          none
#                             summarylsametricreserved      none
#
#    pimhellodrpriority       value                         none
#                             length                        none
#                             type                          none
#
#    pimhellogenerationid     value                         none
#                             length                        none
#                             type                          none
#
#    pimhelloholdtime         value                         none
#                             length                        none
#                             type                          none
#
#    pimhellolanprunedelay    tbit                          none
#                             overrideintervalvalue         none
#                             prunedelayvalue               none
#                             length                        none
#                             type                          none
#
#    pimv4assert              metric                        none
#                             metricpref                    none
#                             rbit                          none
#
#    pimv4header              checksum                      none
#                             reserved                      none
#                             type                          none
#                             version                       none
#
#    pimv4helloaddresslist    length                        none
#                             type                          none
#
#    pimv4joinprune           numgroups                     none
#                             reserved                      none
#                             holdtime                      none
#
#    pimv4register            reserved                      none
#                             borderbit                     none
#                             multicastpacket               none
#                             nullbit                       none
#
#    pimv6assert              metric                        none
#                             metricpref                    none
#                             rbit                          none
#
#    pimv6header              checksum                      none
#                             reserved                      none
#                             type                          none
#                             version                       none
#
#    pimv6helloaddresslist    length                        none
#                             type                          none
#
#    pimv6joinprune           numgroups                     none
#                             reserved                      none
#                             holdtime                      none
#
#    pimv6register            reserved                      none
#                             borderbit                     none
#                             multicastpacket               none
#                             nullbit                       none
#
#    pos                      protocoltype                  none
#                             control                       none
#                             address                       none
#
#    ppp                      protocoltype                  none
#
#    pppoediscovery           code                          none
#                             sessionid                     none
#                             length                        none
#                             type                          none
#                             version                       none
#
#    pppoesession             code                          none
#                             sessionid                     none
#                             length                        none
#                             type                          none
#                             version                       none
#
#    prefixinformation        lbit                          none
#                             preferredlifetime             none
#                             reserved1                     none
#                             reserved2                     none
#                             prefixlen                     none
#                             prefix                        none
#                             validlifetime                 none
#                             abit                          none
#                             type                          none
#                             length                        none
#
#    rarp                     enderhwaddr                   none
#                             ipaddr                        none
#                             senderpaddr                   none
#                             hardware                      none
#                             protocol                      none
#                             ihaddr                        none
#                             operation                     none
#                             targethwaddr                  none
#                             targetpaddr                   none
#
#    redirect                 checksum                      none
#                             code                          none
#                             reserved                      none
#                             targetaddress                 none
#                             destaddress                   none
#                             type                          none
#
#    redirectedheader         reserved1                     none
#                             reserved2                     none
#                             length                        none
#                             type                          none
#
#    relaysessionidtag        value                         none
#                             length                        none
#                             type                          none
#
#    rip1entry                metric                        none
#                             ipaddr                        none
#                             reserved                      none
#                             afi                           none
#                             reserved1                     none
#                             reserved2                     none
#
#    rip2entry                routetag                      none
#                             metric                        none
#                             ipaddr                        none
#                             afi                           none
#                             subnetmask                    none
#                             nexthop                       none
#
#    ripng                    command                       none
#                             reserved                      none
#                             version                       none
#
#    ripngentry               routetag                      none
#                             metric                        none
#                             ipaddr                        none
#                             prefixlen                     none
#
#    ripv1                    command                       none
#                             reserved                      none
#                             version                       none
#
#    ripv2                    command                       none
#                             reserved                      none
#                             version                       none
#
#    routeradvertisement      code                          none
#                             checksum                      none
#                             retranstime                   none
#                             routerlifetime                none
#                             reserved2                     none
#                             mbit                          none
#                             obit                          none
#                             reachabletime                 none
#                             curhoplimit                   none
#                             type                          none
#
#    routersolicitation       checksum                      none
#                             code                          none
#                             reserved                      none
#                             type                          none
#
#    servicenameerrortag      value                         none
#                             length                        none
#                             type                          none
#
#    servicenametag           value                         none
#                             length                        none
#                             type                          none
#
#    snap                     rgcode                        none
#                             ethernettype                  none
#
#    tcp                      checksum                      none
#                             finbit                        none
#                             ecnbit                        none
#                             urgbit                        none
#                             ackbit                        none
#                             acknum                        none
#                             offset                        none
#                             window                        none
#                             synbit                        none
#                             urgentptr                     none
#                             cwrbit                        none
#                             destport                      none
#                             sourceport                    none
#                             rstbit                        none
#                             reserved                      none
#                             seqnum                        none
#                             pshbit                        none
#
#    tosbyte                  tbit                          none
#                             dbit                          none
#                             reserved                      none
#                             rbit                          none
#                             precedence                    none
#
#    udp                      checksum                      none
#                             destport                      none
#                             length                        none
#                             sourceport                    none
#
#    vendorspecifictag        value                         none
#                             length                        none
#                             type                          none
#
#    vlan                     pri                           none
#                             id                            none
#                             cfi                           none
#                             type                          none
#
#
# End of Procedure Header
###
#  Name:    sth::packet_config_filter
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description:  Configure the capture buffer filters.
###
proc ::sth::packet_config_filter { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_config_filter $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList

    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_config_filter $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_config_filter \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0

    set cmd "::sth::packetCapture::packet_config_filter {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {::sth::packetCapture::packet_config_filter {$args} returnKeyedList cmdStatus} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }

    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_config_filter ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

proc ::sth::packet_config_pattern { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_config_pattern $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList

    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_config_pattern $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_config_pattern \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0

    set cmd "::sth::packetCapture::packet_config_pattern {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {::sth::packetCapture::packet_config_pattern {$args} returnKeyedList cmdStatus} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }

    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_config_pattern ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::packet_config_triggers
#
# Purpose:
#    Defines the condition (trigger) that will start or stop packet capturing.
#    By default, Spirent HLTAPI captures all data and control plane packets
#    that it sends and all data plane packets that it receives.
#
# Synopsis:
#    sth::packet_config_triggers
#            -exec {start|stop}
#            -port_handle <handle>
#            [-mode {add|remove}]
#            [-trigger {signature|jumbo|oversize|undersize|invalidfcs|ipchksum|
#              oos|length <0-4294967295>|prbs}]
#            [-action {counter|event}]
#
# Arguments:
#
#    -action
#                   Specifies the condition under which Spirent HLTAPI will
#                   start or stop capturing packets. "Event" is the only 
#                   option supported in this release. Event starts or stops 
#                   capturing packets after a specified set of event details 
#                   takes place.
#
#                   This argument starts or stops the data capture based on the
#                   value provided for the -exec argument. For example, if you
#                   specified "-exec stop", Spirent HLTAPI stops capturing
#                   packets when the specified event occurs.
#
#    -exec
#                   Starts or stops packet capturing based on the condition
#                   provided in the -trigger argument. Possible values are start
#                   and stop, This argument is required. The modes are
#                   described below:
#
#                   start - Starts capturing packets when the specified
#                        condition is met..
#
#                   stop - Stops capturing packets when the specified
#                        condition is met.
#
#    -mode
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Adds or removes all triggers specified with the -trigger
#                   argument. Possible values are "add" and "remove", The 
#                   default is "add". The modes are described below:
#
#                   add - Adds the specified triggers.
#
#                   remove - Removes the specified triggers.
#
#                   Note: Using the sth::packet_config_triggers function 
#                   multiple times with "-mode add" adds all specified triggers 
#                   to the capture. Calling this function with "-mode remove" 
#                   clears all previously added triggers. Also, when removing 
#                   the "length" trigger, you do not have to specify the value 
#                   of the length as you do when defining that trigger. For 
#                   example, you can use "-mode remove -trigger length" instead 
#                   of "-mode remove -trigger {length 24}".
#
#    -port_handle
#                   The handle of the port on which triggers will be configured.
#                   This argument is required. You can specify "all" to apply
#                   this function to all ports (for example, -port_handle all).
#
#    -trigger
#                   Specifies the type of packets that will cause Spirent
#                   TestCenter to either start or stop capturing data plane and
#                   control plane packets. If you do not specify a trigger,
#                   Spirent HLTAPI captures all data packets. You cannot
#                   specify more than one trigger at a time. That is, you can
#                   only specify one trigger in each
#                   sth::packet_config_triggers function call. The triggers
#                   are described below:
#
#                   signature - frames with a signature tag
#
#                   oversize - oversize frames
#
#                   jumbo - jumbo frames
#
#                   undersize - undersize frames
#
#                   invalidfcs - frames with invalid FCS
#
#                   ipchksum - IP header checksum error
#
#                   oos - Out of sequence error (requires signature support)
#
#                   length <length> - frames matching a specified length, where
#                        <length> is a value from 0 to 4294967295.
#
#                   prbs - frame with PRBS (pseudorandom bit sequence) errors
#
#                   Note: To add multiple triggers, call this function multiple
#                   times. For example, to capture both oversize and undersize
#                   packets, call the sth::packet_config_triggers function
#                   twice as in the following example:
#
#                   sth::packet_config_triggers -port_handle $portHandle \
#                        -exec start \
#                        -trigger oversize
#
#                   sth::packet_config_triggers -port_handle $portHandle \
#                        -exec start \
#                        -trigger undersize
#
# Return Values:
#    The sth::packet_config_triggers function returns a keyed list
#    using the following keys (with corresponding data):
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::packet_config_triggers function configures which triggers will
#    cause Spirent HLTAPI to start or stop capturing packets. During the
#    data capturing process, a capture trigger monitors the traffic data for one
#    or more of the specified trigger events, such as an oversized packet. You
#    must use the -exec argument to specify whether to start or stop capturing
#    data packets based on the triggers you specify.
#
#    Optionally, you can use the -mode argument to specify whether to add or
#    remove the specified triggers. (See the -mode argument description for
#    information about the modes.)
#
#    You can use the -trigger argument to specify which trigger events to
#    monitor (See the -trigger argument description for information about each
#    trigger.) If you do not specify any triggers, Spirent HLTAPI will
#    capture all data plane and control plane packets received. To specify more
#    than one trigger, call this function for each trigger.
#
#    Use the -action argument to specify the conditions under which Spirent
#    TestCenter will stop capturing packets. (See the -action argument
#    description for information about the actions.)
#
#    Note: Background traffic analysis with IGMP is unavailable with calculate
#    latency enabled. Also, the HLTAPI cannot capture IGMP control plane packets
#    when calculate latency is enabled (that is, the command
#    "sth::emulation_igmp_control -calculate_latency" is enabled during an IGMP
#    Join. Likewise, the HLTAPI cannot capture MLD control plane packets if its
#    -calculate_latency option is enabled during an MLD Join.
#
#
# Examples:
#
#    To stop data capturing when Spirent HLTAPI encounters a packet with a
#    signature tag:
#
#    sth::packet_config_triggers -port_handle $portHandle \
#         -exec stop \
#         -trigger signature
#
#    To start data capturing when Spirent HLTAPI encounters a packet with a
#    length of 128 bytes:
#
#    sth::packet_config_triggers -port_handle $portHandle \
#         -exec start  \
#         -trigger {length 128}
#
# Sample output for example shown above:
#
#    {status 1}
#
# Notes:
#    It is not possible to define a pattern as a trigger in Spirent HLTAPI.
#
# End of Procedure Header
###
#  Name:    sth::packet_config_triggers
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description:  Configure the capture buffer triggers.
###
proc ::sth::packet_config_triggers { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_config_triggers $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList

    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_config_triggers $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_config_triggers \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0

    set cmd "::sth::packetCapture::packet_config_triggers {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {::sth::packetCapture::packet_config_triggers {$args} returnKeyedList cmdStatus} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }

    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_config_triggers ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}

##Procedure Header
#
# Name:
#    sth::packet_info
#
# Purpose:
#    Returns information about the status of the packet capture.
#
# Synopsis:
#    sth::packet_info
#         -port_handle <handle>
#         -action status
#
# Arguments:
#
#    -port_handle
#                   The handle of the port(s) for which you want information.
#                   This argument is required.
#
#    -action
#                   Specifies the kind of information you want to receive. This
#                   argument is required. The only possible value at this time
#                   is status, which returns a value of "stopped 1" if packet
#                   capturing has stopped or "stopped 0" if it has not.
#
# Return Values:
#    The sth::packet_info function returns a keyed list using the
#    following keys (with corresponding data):
#
#    stopped   Packet capturing has stopped (1) or packet capturing has not
#              stopped (0)
#
#    status    Success (1) or failure (0) of the operation.
#
#    log       An error message (if the operation failed).
#
# Description:
#    The sth::packet_info function queries the device for the status of the
#    packet capture. You must specify both the -port_handle and the -action to
#    be taken.
#
# Examples:
#
#    To retrieve statistical information about all ports:
#
#    sth::packet_info -port_handle all -action status
#
#    To retrieve statistical information about a specific port:
#
#    sth::packet_info -port_handle $portHandle -action status
#
# Sample output:
#
#    {status 1}  {stopped 1}
#
# Notes:
#    None.
#
# End of Procedure Header
###
#  Name:    sth::packet_info
#  Inputs:  args - arguments into this command
#  Globals: 
#  Outputs: 
#  Description:  Get packet capture info.  So far, the only supported stat is "stopped"
###
proc ::sth::packet_info { args } {
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    ::sth::sthCore::Tracker ::sth::packet_info $args
    variable ::sth::packetCapture::packetCapture_userArgs
    variable ::sth::packetCapture::packetCapture_switchPriorityList
    
    # Array to store the input args
    array unset ::sth::packetCapture::packetCapture_userArgs
    array set ::sth::packetCapture::packetCapture_userArgs {}

    # Return Keyed List
    set returnKeyedList ""
    keylset returnKeyedList status $::sth::sthCore::FAILURE

    ::sth::sthCore::log debug "Executing command: packet_info $args"

    # Parse and verify the input arguments
    if {[catch {::sth::sthCore::commandInit ::sth::packetCapture::PacketCaptureTable $args \
                    ::sth::packetCapture:: \
                    packet_info \
                    ::sth::packetCapture::packetCapture_userArgs \
                    ::sth::packetCapture::packetCapture_switchPriorityList} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList \
            "ERROR: Failed to parse and verify input arguments: $errorMsg"
        return $returnKeyedList
    }
    set cmdStatus 0

    set cmd "::sth::packetCapture::packet_info {$args} returnKeyedList cmdStatus"
    ::sth::sthCore::log debug "CMD: $cmd "

    if {[catch {::sth::packetCapture::packet_info {$args} returnKeyedList cmdStatus} errorMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd.  Error: $errorMsg"
        return $returnKeyedList
    }
    ::sth::sthCore::log debug "SUBCOMMAND RESULT for command: packet_info ||$returnKeyedList||"

    if {!$cmdStatus} {
        return $returnKeyedList
    }
    keylset returnKeyedList status $SUCCESS
    return $returnKeyedList
}




