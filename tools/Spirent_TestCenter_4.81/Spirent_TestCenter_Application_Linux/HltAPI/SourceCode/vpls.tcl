# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

package require Tclx
namespace eval ::sth:: {
}

##Procedure Header
#
# Name:
#    sth::emulation_l2vpn_pe_config
#
# Purpose:
#    Creates emulated VPLS l2VPN PE Routers on a Spirent HLTAPI chassis.
#    Retrun status and PE handle list
#
#
# Synopsis:
#   sth::emulation_l2vpn_pe_config
#           -port_handle <port_handle>
#           [-pe_remote_ip_addr <a.b.c.d>]
#           [-pe_ip_addr_start <a.b.c.d>]
#               [-pe_ip_addr_step <a.b.c.d>]
#           [-pe_ip_addr_count  <1 - >]
#           [-pe_ip_addr_prefix_length <1 - 32>]
#           [-pe_gateway_ip_addr <a.b.c.d>]
#               [-pe_gateway_ip_addr_step <a.b.c.d> ]
#           [-traffic_engineering <FLAG>]
#
# Arguments:
#
#       -port_handle
#                   Specifies the handle of the port on which to create PE router on
#
#       -pe_remote_ip_addr
#                   Specifies either the IPv4 address of the DUT interface that
#                   is connected to the Spirent HLTAPI port for the emulated
#                   PE peer or the DUT router ID. The default is 192.1.0.1.
#
#       -pe_ip_addr_start
#                   Specifies the IP address of the interface for the PE that
#                   will establish an adjacency with the PE peer of the DUT. The
#                   default is 192.85.1.1.
#
#       -pe_ip_addr_step
#                   Defines the interface IP addresses of consecutive routers
#                   when multiple PE routers are created. 
#                   
#
#       -pe_ip_addr_count
#                   Defines the number of PE to create on the interface by
#                   incrementing the interface IP address. The default is 1.
#
#       _pe_ip_addr_prefix_length
#                   specify the prefix length of PE IP address.
#
#       -pe_gateway_ip_addr
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address of the PE router. The
#                   default is 192.85.1.1.
#
#       -pe_gateway_ip_addr_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Configures the IPv4 gateway address for multiple PE routers.
#                   This argument is used with the -gateway_ip_addr argument.
#                   
#
#       -traffic_engineering
#                   To be defined. Not supported now
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.30.
#       -traffic_engineering
#
#Decription:
#   
#
# Return Values:
#    The sth::emulation_l2vpn_pe_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handle         The handle that identifies the PE created by the
#                   sth::emulation_l2vpn_pe_config function.
#    status         Success (1) or failure (0) of the operation.
#
#Examples:
#   sth::emulation_l2vpn_pe_config -port_handle $p1 \
#                                  -pe_remote_ip_addr 10.1.1.1 \
#                                  -pe_ip_addr_start 192.168.0.1 \
#                                  -pe_ip_addr_step 0.0.0.1 \
#                                  -pe_ip_addr_count 1 \
#                                  -pe_gateway_ip_addr 192.168.0.3 \
#                                  -pe_gateway_ip_addr_step 0.0.0.1 \
#                                  -pe_ip_addr_prefix_length 24
#
#
# Notes:
#
# End of Procedure Heade
proc ::sth::emulation_l2vpn_pe_config { args } {
    ::sth::sthCore::Tracker ::emulation_l2vpn_pe_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
    
    set _hltCmdName "emulation_l2vpn_pe_config"
    set _hltNameSpace "::sth::Vpls::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}
    
    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}
    
    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
  
    set returnKeyedList ""
    set underScore "_"
    

    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

    if {[catch {::sth::sthCore::commandInit ::sth::Vpls::VplsTable $args \
                                                       $_hltNameSpace \
                                                       $_hltCmdName \
                                                       ${_hltSpaceCmdName}\_user_input_args_array \
                                                       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::$_hltCmdName commandInit error. Error: $err" {}
        return $returnKeyedList  
    }

    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    set cmdStatus $::sth::sthCore::FAILURE
    
    #Executing the ::sth::emulation_l2vpn_pe_config_Generic funcition
    set cmd "${_hltSpaceCmdName}\_Generic {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        return $returnKeyedList
    }  
    
    #apply the stc configuration
    ::sth::sthCore::doStcApply
    
    #return 
    if {!$cmdStatus} {
            keylset returnKeyedList status $::sth::sthCore::FAILURE
            return $returnKeyedList
    } else {
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return $returnKeyedList			
    }    
}

##Procedure Header
#
# Name:emulation_vpls_site_config
#
# Purpose:
#    Creates emulated VPLS site on a Spirent HLTAPI chassis.
#    Retrun status and VPLS site handle list
#
# Synopsis:
#	sth::emulation_vpls_site_config
#		-port_handle <port_handle>
#		-pe_handle <pe_handle>
#		[-set_count <1-200>]
#		[-vc_type { 4 | 5 | B | vlan_mapped |port_mapped }]
#		[-vpn_id <0 - 65535>]
#		[-vpn_id_step <1 - 65535>]
#		[-vc_id <0 - 65535>]
#		[-vc_id_step <1 - 65535>]
#		[-vlan <0-4095>]
#		[-vlan_id_step <1-4095>]
#		[-mtu <1 - 65535>]
#		[-control_word <FLAG>]
#		[-traffic_engineering <FLAG>]
#		[-te_label <FLAG>]
#		[-mac_addr <aa:bb:cc:dd:ee>]
#		[-mac_addr_step <aa:bb:cc:dd:ee>]
#		[-mac_count <1 - >]
#		[-vlan_id <0 - 4095>]
#		[-vlan_step <1 - 4095>]
#		[-vlan_count <1 - 4095>]
#
# Arguments:
#	-port_handle	specify the port handle to create VPLS on. The
#                   	value for the handle is alphanumeric.
#
#	-pe_handle	specify the PE handle to create VPLS sites on. The
#                   	value for the handle is alphanumeric.
#
#	-site_count	specify the number of VPLS sites to create on the PE.
#			The value for the handle is alphanumeric. The default
#			value is 1.
#
#	-vc_type	specify the encapsulation type for the VC on PE used by
#			the VPLS site. Three types are supported, including
#			Ethernet VLAN VC, Ethernet VC, and Ethernet VPLS VC.
#                       The default value is 4, Ethernet VLAN VC. 
#			
#	-vpn_id		specify the VPN ID of the emulated VPN site. 
#
#	-vpn_id_step	define the VPN ID of consecutive VPLS sites when multiple
#			sites are created. The default value is 1.
#
#	-vc_id		specify the VC ID of the VC which the created VPLS site
#			uses when multiple VPLS sites are created.
#
#	-vc_id_step	define the VC ID of the consecutive VC which the created 
#			VPLS site uses when multiple VPLS sites are created.
#			The default value is 1.
#
#	-vlan		The VLAN ID of the VLAN sub-interface of the first created 
#			VPLS site. The Possible values range from 0 to 4095. Set
#                       up the vpls site vlan configuration.
#
#	-vlan_step	define the VLAN ID of the consecutive VLAN sub-interface
#			when multiple VPLS sites are created. The default value
#			is 1.
#
#	-mtu		Maximum Transmission Unit, excluding encapsulation 
#			overhead, for the egress packet interface transmitting 
#			the de-capsulated PDU.
#
#	-control_word	enable VCs to encapsulate using the L2oMPLS control word.
#                       Not supported. 
#
#	-traffic_engineering
#			enalbe the use of RSVP tunnels. To be defined.
#
#	-te_label	label or RSVP tunnel. To be defined
#
#	-mac_addr	specify First MAC address in address pool of VPLS site.
#                       The default value is 00:00:00:00:00:01.
#
#	-mac_addr_step	define MAC address step size when consecutive multiple
#			MAC addresses are created in address pool. The default
#			value is 00:00:00:00:00:01.
#
#	-mac_count	specify the number of MAC addresses in the address pool.
#			The number of MAC addresses determines the number of
#			stations within the VPLS site. If you enable VLAN addresses,
#			type  the number of addresses per VLAN ID in the address
#			pool. The default value is 1.
#
#	-vlan_id 	specify the starting VLAN ID for a range of customer VLANs.
#                       setup the PE vlan configuration.
#
#	-vlan_id_step	define VLAN ID of consecutive VLAN sub-interfaces for a
#			range of customer VLANs.
#
#	-vlan_count	specify the number of VLAN IDs in the address pool.
#
#
#
# Return Values:
#    The sth::emulation_vpls_site_config function returns a keyed list
#    using the following keys (with corresponding data):
#
#    handle         The handle that identifies the VPLS site created by the
#                   sth::emulation_vpls_site_config function.
#    status         Success (1) or failure (0) of the operation.
#
#Examples:
#   sth::emulation_vpls_site_config -port_handle $p1 \
#                                       -pe_handle $peHandle \
#                                       -site_count 2 \
#                                       -vc_type 5 \
#                                       -vpn_id 10 \
#                                       -vpn_id_step 11\
#                                       -vc_id 20 \
#                                       -vc_id_step 22\
#                                       -vlan 100 \
#                                       -vlan_step 5 \
#                                       -vlan_count 4 \
#                                       -mtu 2000 \
#                                       -traffic_engineering \
#                                       -mac_addr 00:00:11:00:00:01 \
#                                       -mac_addr_step 00:00:00:00:00:01 \
#                                       -mac_count 3 \
#                                       -vlan_id 200 \
#                                       -vlan_id_step 7
#
#
# Notes:
#
# End of Procedure Heade
proc ::sth::emulation_vpls_site_config {args} {
    ::sth::sthCore::Tracker ::emulation_vpls_site_config $args
    
    variable ::sth::sthCore::SUCCESS
    variable ::sth::sthCore::FAILURE
  
    set _hltCmdName "emulation_vpls_site_config"
    set _hltNameSpace "::sth::Vpls::"
    set _hltSpaceCmdName ${_hltNameSpace}${_hltCmdName}

    variable ${_hltSpaceCmdName}\_user_input_args_array
    array unset ${_hltSpaceCmdName}\_user_input_args_array
    array set ${_hltSpaceCmdName}\_user_input_args_array {}

    variable ${_hltSpaceCmdName}\_sortedSwitchPriorityList
    
    set returnKeyedList ""
    set underScore "_"

    ::sth::sthCore::log hltcall "Excuting command: $_hltCmdName $args"

    #command init
    if {[catch {::sth::sthCore::commandInit ::sth::Vpls::VplsTable $args \
                                                       $_hltNameSpace \
						       $_hltCmdName \
						       ${_hltSpaceCmdName}\_user_input_args_array \
						       ${_hltSpaceCmdName}\_sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "::sth::sthCore::$_hltCmdName commandInit error. Error: $err" {}
        return $returnKeyedList  
    }
    ::sth::sthCore::log hltcall "SUBCOMMAND RESULT for command: $_hltCmdName ||$returnKeyedList||"
    
    #executing the ::sth::emulation_vpls_site_config_Generic function
    set cmdStatus $::sth::sthCore::FAILURE
    set cmd "${_hltSpaceCmdName}\_Generic {$args} returnKeyedList cmdStatus"
    if {[catch {eval $cmd} errMsg]} {
        ::sth::sthCore::processError returnKeyedList "Error while running $cmd : $errMsg"
        return $returnKeyedList
    }
    
    #apply the stc configuration
    ::sth::sthCore::doStcApply
    
    #return 
    if {!$cmdStatus} {
        keylset returnKeyedList status $::sth::sthCore::FAILURE
	return $returnKeyedList
    } else {
	keylset returnKeyedList status $::sth::sthCore::SUCCESS
	return $returnKeyedList			
    }    

}