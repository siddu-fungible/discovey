# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::ospfTopology:: {
	set topologyType ""
	set TYPE_GRID	"grid"
	set TYPE_ROUTER	"router"
	set TYPE_NETWORK	"network"
	set TYPE_SUMROUTES "summary_routes"
	set TYPE_EXTROUTES "ext_routes"
	set TYPE_NSSAROUTES "nssa_routes"
	set MODE_CREATE 	"create"
	set MODE_MODIFY	"modify"
	set MODE_DELETE	"delete"
	set CURRENTLINKDATA_STR "currentID"
	set OSPFV3_STR "ospfv3"
	set OSPFV2_STR "ospfv2"	
	set GRIDID_STR "ospfGrid"
	set TRUE 1
	set FALSE 0
	array set userArgsArray ""
	array set topologyHndMap ""
	array set gridLsaInfoMap ""
	array set topologyV3HndLsaMap ""
	array set routerGridHndMap ""
	array set routerDefaultLSAMap ""
	array set extRouteHndLocationMap ""
	array set sumRouteHndLocationMap ""
	array set nssaRouteHndLocationMap ""
	array set networkLinkMap ""
	array set routerConnectInfoMap ""
	array set gridLinkPairMap ""
	array set gridInfoMap ""
	array set lsaGridLinkMap ""
	array set routerLSAInfoMap ""
	array set networkLSAInfoMap ""
	array set ospfNetworkInfoMap ""
	set currentX 0
	set currentY 0
	set numberOfSimRouters 0
	set iniRouterID 0.0.0.1
	set routerStep 0.0.0.1
	set grid_connect "1 1"
	set isGridCreate $::sth::ospfTopology::FALSE
	set returnedKeyList ""
	set currentOSPFVersion ""
	set currentGridID 1
	set isOspfv3 ""
	
}

set ::sth::ospfTopology::ospfTopologyTable {
    ::sth::ospfTopology::
    {
    	emulation_ospf_topology_route_config
    	{	hname						stcobj						stcattr						type										priority	default				range			supported	dependency	mandatory	procfunc						mode																			constants	}
    	{	elem_handle					_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{modify ""}									_none_ }
    	{	external_connect			_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create "" modify ""}						_none_ }
    	{	mode						_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		true		_none_							{create ""}									_none_ }
    	{	handle						_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		true		_none_							{create "" modify "" delete ""}				_none_ }
		{	type						_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		true		_none_							{create ""}									_none_ }
		{	router_abr					RouterLsa					Abr							ALPHANUM										0		_none_				0-1				true		_none_		false		_none_							{create ""}									_none_ }
		{	router_asbr					RouterLsa					Asbr						ALPHANUM										0		_none_				0-1				true		_none_		false		_none_							{create ""}									_none_ }
		{	router_connect				_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }
		{	router_disconnect			_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }
		{	router_id					RouterLsa					AdvertisingRouterId			IPV4											0		_none_				_none_			true		_none_		false		_none_							{create "" modify ""} 						_none_ }
		{ 	router_te					_none_						_none_						ALPHANUM										0		_none_				0-1				true		_none_		false		_none_							{create ""}									_none_ }
		{	router_virtual_link_endpt	_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_col					_none_						_none_						NUMERIC											0		_none_				0-65535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_connect				_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_connect_session		_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_disconnect				_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_link_type				_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_prefix_length			_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_prefix_start			_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_prefix_step			_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_router_id				_none_						_none_						IPV4											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_router_id_step			_none_						_none_						IPV4											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_row					_none_						_none_						NUMERIC											0		_none_				0-65535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_start_gmpls_link_id	_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_start_te_ip			_none_						_none_						ALPHANUM										0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_stub_per_router		_none_						_none_						ALPHANUM										0		_none_				0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	grid_te						_none_						_none_						ALPHANUM										0		0					0-1				false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_intf_addr				_none_						_none_						IPV4											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_connect				_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_number_of_prefix	_none_						_none_						NUMERIC											0		1					0-14294967295		true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_prefix_length		_none_						_none_						NUMERIC											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_prefix_metric		_none_						_none_						NUMERIC											0		100					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_prefix_start		_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	summary_prefix_step			_none_						_none_						NUMERIC											0		1					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_number_of_prefix	_none_						_none_						NUMERIC											0		1					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_forward_addr	_none_					_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_length		_none_						_none_						NUMERIC											0		32					_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_metric		_none_						_none_						NUMERIC											0		_none_				1-16777215		true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_start		_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_step		_none_						_none_						NUMERIC											0		1					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_prefix_type		_none_						_none_						NUMERIC											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	external_connect			_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_number_of_prefix		_none_						_none_						NUMERIC											0		1					_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_forward_addr	_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_length			_none_						_none_						NUMERIC											0		32					_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_metric			_none_						_none_						NUMERIC											0		1					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_start			_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_step			_none_						_none_						NUMERIC											0		1					0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_prefix_type			_none_						_none_						NUMERIC											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	nssa_connect				_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_dr						_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_ip						_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_prefix_length			_none_						_none_						NUMERIC											0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_count					_none_						_none_						NUMERIC											0		_none_				0-66535			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_prefix					_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	net_ip_step					_none_						_none_						ANY												0		_none_				_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	link_enable					_none_						_none_						NUMERIC											0		1					_none_			true		_none_		false		_none_							{create ""}									_none_ }										
		{	link_metric					_none_						_none_						NUMERIC											0		1					1-65535			true		_none_		false		_none_							{create ""}									_none_ }
		{	link_te						_none_						_none_						NUMERIC											0		0					_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_admin_group			_none_						_none_						ANY												0		1					_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_instance			_none_						_none_						NUMERIC											0		0					_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_link_id				_none_						_none_						IPV4											0		0.0.0.0				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_local_ip_addr		_none_						_none_						IPV4											0		0.0.0.0				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_max_bw				_none_						_none_						NUMERIC											0		100000				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_max_resv_bw			_none_						_none_						NUMERIC											0		100000				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_metric				_none_						_none_						NUMERIC											0		1					_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_remote_ip_addr		_none_						_none_						IPV4											0		0.0.0.0				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_type				_none_						_none_						ANY												0		ptop				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority0	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority1	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority2	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority3	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority4	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority5	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority6	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
		{	link_te_unresv_bw_priority7	_none_						_none_						NUMERIC											0		_none_				_none_			false		_none_		false		_none_							{create ""}									_none_ }										
	}
}