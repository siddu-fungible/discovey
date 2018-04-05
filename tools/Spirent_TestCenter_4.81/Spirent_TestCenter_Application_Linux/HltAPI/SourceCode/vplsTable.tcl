# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::Vpls:: {
}

set ::sth::Vpls::VplsTable {
    ::sth::Vpls::
    {   emulation_l2vpn_pe_config
        {hname   			stcobj  	stcattr		type    	priority    	default range   supported   	dependency  	mandatory   	procfunc    		mode    			constants}
        {port_handle    		_none_  	_none_  	ALPHANUM    	1   		_none_  _none_  true    	_none_  	true    	_none_  		{ create "" }  			_none_}
 	{pe_gateway_ip_addr		Ipv4If		Gateway		IP		10		_none_	_none_	true		_none_		false		processConfigCmd	{ create processConfigCmd }	_none_}
	{pe_gateway_ip_addr_step    	Ipv4If		_none_		IP		15		1	_none_	true		_none_		false		_none_			{ create "" }			_none_}
        {pe_remote_ip_addr 		LdpRouterConfig DutIp   	IP  		5  		_none_  _none_  true    	_none_  	false    	processConfigCmd  	{ create processConfigCmd }  	_none_}
        {pe_ip_addr_start 		Ipv4If  	Address   	IP  		10  		_none_  _none_  true    	_none_  	false    	processConfigCmd  	{ create processConfigCmd }  	_none_}
        {pe_ip_addr_step 		_none_  	_none_   	IP  		15  		_none_  _none_  true    	_none_  	false    	_none_  		{ create "" }  			_none_}
        {pe_ip_addr_count 		_none_  	_none_   	NUMERIC  	20  		1  	_none_  true    	_none_  	false    	_none_  		{ create "" }  			_none_}
        {pe_ip_addr_prefix_length 	Ipv4If  	PrefixLength   	NUMERIC  	11  		24  	1-128  	true    	_none_  	false    	processConfigCmd  	{ create processConfigCmd }  	_none_}
        {traffic_engineering 		_none_  	_none_   	FLAG  		50  		_none_  _none_  false    	_none_  	false    	_none_  		{ create "" }  			_none_}
    }
    {   emulation_vpls_site_config
        {hname   		stcobj  		stcattr				type    				priority    	default range   supported   dependency  mandatory   procfunc    mode    constants}
        {port_handle    	_none_  		_none_  			ALPHANUM    				1   		_none_  _none_  true    	_none_  true    _none_  { create "" }  _none_}
 	{attached_dut_ip_addr	VpnSiteInfoVplsLdp	PeIpv4Addr			IP    					3		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}        
 	{attached_dut_ip_prefix	VpnSiteInfoVplsLdp	PeIpv4PrefixLength		NUMERIC    				3		32	1-32	true		_none_	false	_none_	{ create "" }	_none_}
 	{pe_handle		_none_			_none_				ALPHANUM    				2		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{site_count		_none_			_none_				NUMERIC    				5		1	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vc_type		VcLsp 			Encap	    		{CHOICES 4 5 B vlan_mapped port_mapped}    	50		_none_	_none_	false		_none_	false	_none_	{ create "" }   { 4 LDP_LSP_ENCAP_ETHERNET_VLAN 5 LDP_LSP_ENCAP_ETHERNET B LDP_LSP_ENCAP_ETHERNET_VPLS }}
 	{vpn_id 		Project			VpnIdGroup  			NUMERIC    				30		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
  	{vpn_id_step 		_none_			_none_  			NUMERIC    				35		_none_	_none_	false		_none_	false	_none_	{ create "" }	_none_}
 	{vc_id 			VpnSiteInfoVplsLdp	StartVcId  			NUMERIC    				40		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vc_id_step 		VpnSiteInfoVplsLdp	_none_  			NUMERIC    				45		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vlan_id    		VlanIf			VlanId  			NUMERIC    				25		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vlan_id_step 		_none_			_none_  			NUMERIC    				50		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{mtu 			VcLsp 			IfMtu  				NUMERIC    			    	60		1500	1-65535	true		_none_	false	_none_	{ create "" }	_none_}
 	{control_word 		_none_			_none_  			FLAG    				70		_none_	_none_	false		_none_	false	_none_	{ create "" }	_none_}
 	{traffic_engineering 	_none_			_none_  			FLAG    				80		_none_	_none_	false		_none_	false	_none_	{ create "" }	_none_}
 	{te_label 		_none_			_none_  			NUMERIC    				90		_none_	_none_	false		_none_	false	_none_	{ create "" }	_none_}
 	{mac_addr 		EthIIIf   		SourceMac  			ANY    					10    		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{mac_addr_step 		_none_   		_none_  			ANY    					11    		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{mac_count 		_none_   		_none_  			NUMERIC    				15    		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vlan 			VlanIf_Outer		VlanId  			NUMERIC    				20		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vlan_step 		_none_			_none_  			NUMERIC    				55		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
 	{vlan_count 		_none_			_none_  			NUMERIC    				56		_none_	_none_	true		_none_	false	_none_	{ create "" }	_none_}
   }
}