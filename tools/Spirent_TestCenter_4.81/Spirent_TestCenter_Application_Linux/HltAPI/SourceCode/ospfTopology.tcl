# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::ospfTopology:: {
    variable returnKeyedList
}

#
##Procedure Header
#
# Name:
#    sth::emulation_ospf_topology_route_config
#
# Purpose:
#    Creates, modifies, or deletes a set of OSPFv2 and/or OSPFv3 routers or a 
#    single routers behind an OSPF router. You can attach routes to or delete 
#    routes from different kinds of routers, such as Summary, External, and 
#    NSSA.
#
# Synopsis:
#     sth::emulation_ospf_topology_route_config
#          -mode {create|modify|delete}
#              -handle <ospf_session_handle>
#              -elem_handle <topology_elem_handle>
#          -type {router|grid|network|summary_routes|ext_routes|nssa_routes}
#         [-external_connect <1-65535> <1-65535>]
#         [-external_number_of_prefix <1-65535> ]
#         [-external_prefix_forward_addr {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-external_prefix_length {<1-32> |<1-128>}]
#         [-external_prefix_metric <1-16777215>]
#         [-external_prefix_start {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-external_prefix_step <0-65535>]
#         [-external_prefix_type {{1|2} | {0|1} }]
#         [-grid_col <1-65535>]
#         [-grid_connect <1-65535> <1-65535>]
#         [-grid_connect_session <ospf_session_handle>]
#         [-grid_disconnect <ospf_session_handle>]
#         [-grid_link_type {ptop_numbered|ptop_unnumbered}]
#         [-grid_prefix_length {<1-32> |<1-128>}]
#         [-grid_prefix_start {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-grid_prefix_step]
#              ospfv2 a.b.c.d ospfv3 1-65535}
#         [-grid_router_id <a.b.c.d>]
#         [-grid_router_id_step <a.b.c.d>]
#         [-grid_row <1-65535>]
#         [-grid_stub_per_router <0-65535>]
#         [-link_enable {0|1}]
#         [-link_intf_addr <a.b.c.d>]
#         [-net_count <1-65535>]
#         [-net_dr <ospf_lsa_handle>]
#         [-net_ip {a.b.c.d}]
#         [-net_ip_step {a.b.c.d}]
#         [-net_prefix {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-net_prefix_length {<1-32> |<1-128>}]
#         [-nssa_connect <1-65535> <1-65535>]
#         [-nssa_number_of_prefix {<1-32> |<1-128>}]
#         [-nssa_prefix_forward_addr {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-nssa_prefix_length {<1-32> |<1-128>}]
#         [-nssa_prefix_metric <1-16777215>]
#         [-nssa_prefix_start {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-nssa_prefix_step {1-65535}]
#         [-nssa_prefix_type {{1|2} | {0|1} }]
#         [-router_abr <0|1>]
#         [-router_asbr <0|1>]
#         [-router_connect <ospf_lsa_handle>]
#         [-router_disconnect <ospf_lsa_handle>]
#         [-router_id <a.b.c.d>]
#         [-summary_connect <1-65535> <1-65535>]
#         [-summary_number_of_prefix <1-65535>]
#         [-summary_prefix_length {<1-32> |<1-128>}]
#         [-summary_prefix_metric <1-16777215>]
#         [-summary_prefix_start {<a.b.c.d> |
#                 <a:b:c:d:e:f:g:h>}]
#         [-summary_prefix_step {1-65535]
#
# Arguments:
#
#    -elem_handle
#                   Specifies the topology element to modify or delete. Returns
#                   the topology element type that you specified with the -type
#                   argument. This argument is mandatory for modify and delete 
#                   modes.
#
#    -external_connect
#                   Specifies the position (row and column) of the router in the
#                   router grid associated with the OSPF session to which an
#                   OSPF external route pool will be connected. The default
#                   position is "1 1".
#
#    -external_number_of_prefix
#                   Specifies the number of routes in an OSPF external route
#                   pool element. Possible values range from 1 to 66535. The
#                   default is 24. 
#
#    -external_prefix_forward_addr
#                   Specifies the forwarding IP address for an OSPF external
#                   route pool element. The default for OSPFv2 (IPv4) is
#                   0.0.0.0, and the default for OSPFv3 (IPv6) is
#                   0:0:0:0:0:0:0:0.  
#
#    -external_prefix_length
#                   Specifies the prefix length for an OSPF external route pool
#                   element. For IPv4, possible values range from 0 to 32, and
#                   the default is 24. For IPv6, possible values range from 1 to
#                   128. The default is 64,  
#
#    -external_prefix_metric
#                   Specifies a metric value for an OSPF external route pool 
#                   element. Possible values range from 1 to 16777215. The 
#                   default is 1.
#
#    -external_prefix_start
#                   Specifies the first of a sequence of IP addresses belonging
#                   to the same OSPF external route pool element. The default 
#                   for OSPFv2 (IPv4) is 0.0.0.0, and the default for OSPFv3 
#                   (IPv6) is 0:0:0:0:0:0:0:0. .
#
#    -external_prefix_step
#                   Specifies the modifier by which to increment the network
#                   part of the first IP address, to generate subsequent IP
#                   addresses belonging to different routes for an OSPF external
#                   route pool element. Possible values range from 0 to 66535.
#                   The default is 1.
#
#    -external_prefix_type
#                   Specifies the type of metric to use for an OSPF external
#                   route pool. Possible values are 1 or 2. Specify 1 
#                   for type 1 (internal cost is added to external cost) or 2 
#                   for type 2 (external cost only). The default is 1. 
#
#    -grid_col
#                   Defines the number of columns in a grid. Use this argument
#                   to add a grid of routers behind an emulated router. You must
#                   also specify "-grid_row" to configure the size of the grid.
#                   Possible values range from 0 to 65535. The default is
#                   1.
#
#    -grid_connect
#                   Connects a router in the grid, as specified by the row and 
#                   column, to the emulated router of the specified OSPF session 
#                   handle (-handle). By default, the first row and first column 
#                   router is connected to the emulated router. Spirent 
#                   TestCenter allows you to connect only one grid of routers to 
#                   one emulated router. Use this argument to add a grid of 
#                   routers behind an emulated router: 
#
#    -grid_connect_session
#                   Use this argument to reconnect a grid of routers to an
#                   emulated router after the grid has been disconnected by
#                   "-grid_disconnect". To reconnect a grid of routers to an
#                   emulated router, use "-grid_connect_session" with "-mode
#                   modify", "-type grid", "-elem_handle <grid_handle>", and
#                   "-grid_connect <row col>",
#
#                   Note: You can retrieve the "connected_session" handle after
#                   the grid of routers has been created.
#
#    -grid_disconnect
#                   Use this argument to disconnect a grid of routers from an
#                   emulated router. To disconnect a grid of routers from an
#                   emulated router, use "-grid_disconnect" with "-mode
#                   modify", "-type grid", "-elem_handle <grid_handle>", and
#                   "-grid_connect <row  col>",
#
#                   Note: You can retrieve the "connected_session" handle after
#                   the grid of routers has been created.
#
#    -grid_link_type
#                   Specifies the type of link that connects the routers in a
#                   grid. This argument is available only for OSPFv2. Possible
#                   values are ptop_numbered and ptop_unnumbered. The default is
#                   "ptop_unnumbered". A point-to-point (ptop) link is a 
#                   physical or logical serial link between two routers. The
#                   link can be numbered (IP address is configured on the link) 
#                   or unnumbered. 
#
#    -grid_prefix_length
#                   Specifies the prefix length of a ptop_numbered link on an
#                   OSPFv2 grid and on a stub network if you also used the
#                   "-grid_stub_per_network" argument. The default for OSPFv2 is
#                   24, and the default for OSPFv3 is 64.
#
#    -grid_prefix_start
#                   Defines the first prefix used in a grid. Use this argument
#                   only if "-grid_link_type" is set to "ptop_numbered" on
#                   an OSPFv2 grid or if you also used "-grid_stub_per_router".
#                   The default for OSPFv2 (IPv4) is 0.0.0.0, and the default
#                   for OSPFv3 (IPv6) is 0:0:0:0:0:0:0:0.
#
#    -grid_prefix_step
#                   Increments network prefixes in a grid. The value rounds to
#                   the prefix length..Use this argument if either
#                   "-grid_link_type" is set to "ptop_numbered" or if you also
#                   set "-grid_stub_per_router". Possible values range from 1 to
#                   32 for OSPFv2 and 1 to 128 for OSPFv3.
#
#    -grid_router_id
#                   Sets the first router ID in an OSPF router grid.
#
#    -grid_router_id_step
#                   Sets the step value for incrementing subsequent router IDs
#                   in an OSPF router grid
#
#    -grid_row
#                   Defines the number of rows in a grid. Use this argument
#                   to add a grid of routers behind an emulated router. You must
#                   also specify "-grid_col" to configure the size of the grid.
#                   Possible values range from 0 to 65535. The default is
#                   1.
#
#    -grid_stub_per_router
#                   Defines the number of stub networks per router in a grid.
#                   Use this argument to add a grid of routers behind a grid
#                   router.
#
#    -handle
#                   Identifies the OSPF router on which to create the OSPF
#                   element. This argument is mandatory.
#
#    -link_enable
#                   Enables a link to another element. Use this argument to add
#                   a single router behind a session router: If true (1),
#                   enables link to another element. The default is 1.
#
#    -link_intf_addr
#                   Sets the link interface address. Use this argument to add a
#                   single router behind a session router:
#
#    -mode
#                   Specifies the action to be performed. Possible values
#                   are create, modify, and delete. This argument is mandatory.
#                   The modes are described below:
#
#                   create - Creates a topology element. You must use the
#                        -handle argument to identify the associated element and 
#                        the -type argument to specify the type of topology 
#                        element to create. Both the -handle and -type arguments 
#                        are mandatory with "-mode create".
#
#                   modify - Changes the configuration for the topology
#                        specified in the -handle argument. The -handle, -type,
#                        and -elem_handle arguments are mandatory  with "-mode
#                        modify".
#
#                   delete - Deletes the element specified in the -handle
#                        argument. The -handle, -type, and -elem_handle
#                        arguments are mandatory with "-mode delete".
#
#    -net_count
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the number of routers per transit network.
#                   Possible values range from 1 to 65535. The default is 1.
#
#    -net_dr
#                   Sets the designated router of an OSPF network element.
#
#    -net_ip
#                   Sets the IP address of an OSPF network element.
#
#    -net_prefix
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Use this argument to add a network (transit link) behind a
#                   session router: The default for OSPFv2 (IPv4) is 0.0.0.0,
#                   and the default for OSPFv3 (IPv6) is 0:0:0:0:0:0:0:0.
#
#    -net_prefix_length
#                   Specifies the prefix length on the network interface.
#                   Possible values for OSPFv2 range from 1 to 32; the default
#                   is 24. Possible values for OSPFv3 range from 1 to 128; the
#                   default is 64.
#
#    -net_ip_step
#                   Spirent Extension (for Spirent HLTAPI only).
#                   Specifies the step value for incrementing subsequent IP
#                   addresses of an OSPF network element on the same transit
#                   network
#
#    -nssa_number_of_prefix
#                   Specifies the number of NSSA routes added to a grid
#                   router.
#
#    -nssa_prefix_forward_addr
#                   Specifies the forwarding address for an OSPF NSSA route
#                   pool. The default for OSPFv2 (IPv4) is 0.0.0.0, and the
#                   default for OSPFv3 (IPv6) is 0:0:0:0:0:0:0:0.
#
#    -nssa_prefix_length
#                   Specifies the prefix length for an OSPF NSSA route
#                   pool. Possible values for OSPFv2 range from 1 to 32; the
#                   default is 32. Possible values for OSPFv3 range from 1 to
#                   128; the default is 64.
#
#    -nssa_prefix_metric
#                   Specifies a metric value for an OSPF NSSA route pool 
#                   element. Use this argument when adding nssa routes (that is, 
#                   you specified "-type as nssa_routes"). Possible values 
#                   range from 1 to 16777215. The default is 1. 
#
#    -nssa_prefix_start
#                   Specifies the first IP network prefix in an OSPF NSSA route 
#                   pool element. The default for OSPFv2 (IPv4) is 0.0.0.0, and 
#                   the default for OSPFv3 (IPv6) is 0:0:0:0:0:0:0:0.
#
#    -nssa_prefix_step            
#                   Specifies the amount by which to increment the network part
#                   of the first IP address to generate subsequent IP addresses
#                   belonging to different routes for an OSPF NSSA route pool 
#                   element. Possible values range from 1 to 65535,
#
#    -nssa_prefix_type
#                   Specifies the type of metric to use for an OSPF NSSA route 
#                   pool. Possible values are 1 and 2. Specify 1 for type 1 
#                   (when calculating the cost of the path to an NSSA route, the 
#                   costs of the internal links are included) or 2 for type 2 
#                   (costs of internal links are not included in the total cost 
#                   calculation. Type 2 routes have a lower priority and are 
#                   considered in the path selection after type 1 costs have 
#                   been evaluated. The default is 1.  
#
#    -router_abr
#                   Specifies whether the emulated router is an area border
#                   router. This argument is equivalent to "Router Type" in the
#                   Spirent TestCenter GUI, with a choice of ABR, ASBR, or
#                   Virtual Link. Possible values are 0 (false) or 1 (true). If
#                   set to 1, the emulated router is an area border router (that 
#                   is, it corresponds to the B (Border) bit in a router LSA). 
#                   If set to 0, it is not.
#
#    -router_asbr
#                   Specifies whether the emulated router is an AS border
#                   router. This argument is equivalent to "Router Type" in the
#                   Spirent TestCenter GUI, with a choice of ABR, ASBR, or
#                   Virtual Link. Possible values are 0 (false) or 1 (true). If
#                   set to 1, the emulated router is an AS border router (that 
#                   is, it corresponds to the E (External) bit in a router 
#                   LSA).. If set to 0, it is not.
#
#    -router_connect
#                   Connects a single router behind a session 
#                   router: connects to an emulated router or a router 
#                   grid. If you do not specify "-router_connect", a router is 
#                   automatically connected to an emulated router by default. 
#                   To connect a router, use "-router_connect with "-mode
#                   create", and "-type router", 
#
#    -router_disconnect
#                   Disconnects the router from a session router. To disconnect
#                   a router, use "-router_disconnect with "-mode modify", 
#                   "-type router", and "-elem_handle <topology_elem_handle>".
# 
#    -router_id
#                   Sets the router ID for the OSPF router element. 
#
#    -summary_connect
#                   Specifies the position (row and column) of the router in the
#                   router grid associated with the OSPF session to which an
#                   OSPF summary route pool will be connected. The default
#                   position is "1 1".
#
#    -summary_number_of_prefix
#                   Specifies the number of summary routes added to a grid 
#                   router. Possible values range from 1 to 66535. The
#                   default is 1. 
#
#    -summary_prefix_length
#                   Specifies the prefix length for an OSPF summary route pool
#                   element. For IPv4, possible values range from 0 to 32, and
#                   the default is 24. For IPv6, possible values range from 1 to
#                   128. The default is 64,  
#
#    -summary_prefix_metric
#                   Specifies a metric value for an OSPF summary route pool 
#                   element. Use this argument when adding summary routes (that 
#                   is, you specified "-type summary_routes"). Possible values 
#                   range from 1 to 16777215. The default is 1. 
#
#    -summary_prefix_start
#                   Specifies the first of a sequence of IP addresses belonging
#                   to the same OSPF summary route pool element. The default 
#                   for OSPFv2 (IPv4) is 0.0.0.0, and the default for OSPFv3 
#                   (IPv6) is 0:0:0:0:0:0:0:0. Use this argument only if you 
#                   specified "-type ext_pool".
#
#                   The default for OSPFv2 (IPv4) is
#                   0.0.0.0, and the default for OSPFv3 (IPv6) is
#                   0:0:0:0:0:0:0:0.
#
#    -summary_prefix_step
#                   Specifies the modifier by which to increment the network
#                   part of the first IP address, to generate subsequent IP
#                   addresses belonging to different routes for an OSPF summary
#                   route pool element. Possible values range from 0 to 66535.
#                   The default is 1.
#
#    -type
#                   Specifies the type of topology element to create:
#
#                   - router: an individual OSPF router
#                   - grid: a rectangular grid of routers
#                   - network: a subnet/link behind the selected session router
#                   - summary_routes: a pool of summary route addresses
#                   - ext_routes: a pool of external route addresses
#                   - nssa_routes: a pool of NSSA route addresses
#
#                   This argument is mandatory.
#
# Cisco-specific Arguments:
#    The following arguments are specific to the Cisco HLTAPI but are not
#    supported by Spirent HLTAPI 2.00.
#
#    -grid_start_gmpls_link_id
#    -grid_start_te_ip
#    -grid_te
#    -link_metric
#    -link_te
#    -link_te_instance
#    -link_te_link_id
#    -link_te_local_ip_addr
#    -link_te_max_bw
#    -link_te_max_resv_bw
#    -link_te_metric
#    -link_te_remote_ip_addr
#    -link_te_type
#    -link_te_unresv_bw_priority0
#    -link_te_unresv_bw_priority1
#    -link_te_unresv_bw_priority2
#    -link_te_unresv_bw_priority3
#    -link_te_unresv_bw_priority4
#    -link_te_unresv_bw_priority5
#    -link_te_unresv_bw_priority6
#    -link_te_unresv_bw_priority7
#    -nssa_connect
#    -router_te
#    -router_virtual_link_endpt
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status         Success (1) or failure (0) of the operation.
#
#         log            An error message (if the operation failed).
#
#         elem_handle    A different element handle is returned based on 
#                        the user configuration
#
#         router (elem_handle - router_lsa_handle)
#
#              version             - ospfv2 or ospfv3
#
#              connected_handles   - router_lsa_handle that is connected
#                                    to the created router
#
#              router_lsa          - router_lsa_handle (same as elem_handle)
#
#         grid (elem_handle - grid_handle)
#              
#         connected_session.$session.row <row>.col <col>
#                                  - $session is router_lsa_handle
#                                    <row> is the row that 
#                                    the router connects to
#                                    the grid.
#                                    <col> is the column that 
#                                    the router connects to 
#                                    the grid.
#         router                   - the router_lsa_handle of each router 
#                                    on the grid
#
#    network (elem_handle - network_blk_handle)
#         
#         network_lsa         - network_blk_handle
#         connected_routers   - a list of router lsa handles
#         version             - ospfv2 or ospfv3
#
#    summary (elem_handle - summary_blk_handle)
#              
#         summary_lsas        - summary_blk_handle
#         connected_routers   - a list of router lsa handles
#         version             - ospfv2 or ospfv3       
#
#    external (elem_handle - external_blk_handle)
#
#         external_lsas       - summary_blk_handle
#         connected_routers   - a list of router lsa handles
#         version             - ospfv2 or ospfv3
#
#    nssa (elem_handle - nssa_blk_handle)
#              
#         nssa_lsas           - nssa_blk_handle
#         connected_routers   - a list of router lsa handles
#         version             - ospfv2 or ospfv3 
#
#    Examples:
#
#    To get the router_lsa handle of the created router, specify one of the 
#    following:
#
#    set router_lsa [keylget cmdReturn elem_handle]  
#    
#    set router_lsa [keylget cmdReturn router.router_lsa]
#
#    To get the router_lsa handle of the router that it is connected with, 
#    specify the following:
#    
#    set connected_router [keylget cmdReturn router. connected_handles]
#
#    To get the grid_handle:
#
#    set grid_handle [keylget cmdReturn elem_handle]
#
#    To get the connected_session handle
#    set connected_sesion [keylkeys cmdReturn grid.connected_session]
#    
#    To get the router_lsa of a grid router at row 2, col 2:
#
#    set router_lsa [keylget cmdReturn grid.router.2.2]
#
# Description:
#    The sth::emulation_ospf_topology_route_config function creates, enables, 
#    disables, modifies, or deletes a set of OSPFv2 and/or OSPFv3 routers or a 
#    single routers behind an OSPF router. Use this function to attach routes to 
#    or delete routes from Summary, External, and NSSA routers. 
#
#    To configure the OSPF topology, you create emulated routers and links 
#    associated with the routers. To define the routers and links, use a 
#    combination of router, LSA, and link elements,
#
#    Use the -mode argument to specify the operation to perform. When you create 
#    a topology element, the function returns a handle to the newly created 
#    element. Use this handle as input for modify and delete mode operations.
#
#    The mode that you use determines the set of arguments that you use to
#    configure the OSPF topology elements. When you specify -mode create, you 
#    must also use the -handle argument to identify the OSPF session on which to 
#    create the OSPF element and the -type argument to specify the type of 
#    topology element to create.
#
#  Examples:
#    The following example creates an OSPF router behind an emulated 
#    router:
#
#         [sth::emulation_ospf_topology_config -mode create \
#              -handle $router \
#              -type router \
#              -router_id 1.0.0.1]
#
#         router_handle [keylget cmdReturn elem_handle]
#
#    Output for above example:
#
#    {status 1} {elem_handle routerlsa2} {router {{connected_handles routerlsa1} 
#    {router_lsa routerlsa2} {link_lsa routerlsalink1}}}
#
#    The following example creates an OSPF router behind a grid
#    router:
#
#         [sth::emulation_ospf_topology_config -mode create \
#              -handle $router \
#              -type  router \
#              -router_id  1.0.0.1 \
#              -router_connect $lsa_handle]
#
#         router_handle [keylget cmdReturn elem_handle]
#
#    Output for above example:
#
#    {status 1} {elem_handle routerlsa6} {router {{connected_handles routerlsa1} 
#    {router_lsa routerlsa6} {link_lsa routerlsalink11}}}
#    
#    Note: The lsa_handle is retrieved once the grid router has been created.
#
#    The following example creates an OSPF grid:
#
#         [sth::emulation_ospf_topology_config -mode create \
#              -handle $router \
#              -type grid \
#              -grid_connect  "2 5" \
#              -grid_col 5 \
#              -grid_row  5 \
#              -grid_link_type ptop_unnumberd \
#              -grid_router_id 1.0.0.1 \
#              -grid_router_id_step  0.0.0.1]
#
#         grid_handle [keylget cmdReturn elem_handle]
#         connected_handle [keylkeys cmdReturn grid.connected_session]
#
#    Output for above example:
#
#    {status 1} {elem_handle ospfGrid1} {grid {{connected_session {{routerlsa5 
#    {{row 1} {col 1}}}}} {router {{1 {{1 routerlsa1} {2 routerlsa2}}} {2 {{1 
#    routerlsa3} {2 routerlsa4}}}}}}}
#
#    The following example disconnects an OSPF grid from emulated router:
#
#         [sth::emulation_ospf_topology_config -mode modify \
#              -handle  $router \
#              -type  grid \
#              -elem_handle $grid_handle \
#              -grid_disconnect $connected_handle]
#
#         grid_handle [keylget cmdReturn elem_handle]
#
#    Output for above example:
#
#    {status 1} {elem_handle ospfGrid1} {grid {{router {{1 {{1 routerlsa1}
#    {2 routerlsa2}}} {2 {{1 routerlsa3} {2 routerlsa4}}}}}}}
#
#    The following example creates an OSPF summary:
#
#         [sth::emulation_ospf_topology_config -mode create \
#              -handle $router \
#              -type  summary_routes \
#              -summary_connect "1 1" \
#              -summary_prefix_start  91.0.1.0 \ 
#              -summary_prefix_step  2 \
#              -summary_number_of_prefix  5 \
#              -summary_prefix_length  27 \
#              -summary_prefix_metric  10]
#
#         summary_handle [keylget cmdReturn elem_handle]
#
#    Output for above example:
#
#    {summary {{summary_lsas summarylsablock1} {version ospfv2} 
#    {connected_routers routerlsa1}}} {status 1} {elem_handle summarylsablock1}
#
#    The following example modifies an OSPF summary:
#
#         [sth::emulation_ospf_topology_config -mode modify \
#              -handle  $router \
#              -type  summary_routes \
#              -elem_handle $summary_handle \
#              -summary_prefix_start 191.0.1.0 \ 
#              -summary_prefix_step  4 \
#              -summary_number_of_prefix  2 \
#              -summary_prefix_length  24]
#
#         summary_handle [keylget cmdReturn elem_handle]
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#           1) The Cisco HLTAPI specification documentation states that to
#              use the emulation_ospf_topology_config function, you must use 
#              session_router that is returned from the emulation_ospf_config 
#              function: [keylget cmdReturn session_router]. However, the 
#              current implementation of the Spirent HLTAPI for 
#              sth::emulation_ospf_config is as follows:
#
#              [keylget cmdReturn handle]  -> return session_router handle
#              [keylget cmdReturn session_router] -> return router handle
#
#              To ensure that these handles do not cause other functions to work 
#              improperly, the Spirent HLTAPI uses the handle that is returned 
#              from [keylget cmdReturn handle] to create objects in 
#              sth::emulation_ospf_topology_config. You MUST use the handle that
#              is returned from emulation_ospf_config [keylget cmdReturn handle] 
#              when configuring topology elements with 
#              sth::emulation_ospf_topology_config. 
#
# End of Procedure Header
#
#
namespace eval ::sth {
    proc emulation_ospf_topology_route_config {args} {
	::sth::sthCore::Tracker ::emulation_ospf_topology_route_config $args
    
	::sth::ospfTopology::Reset
	::sth::sthCore::log hltcall "User executed ::sth::emulation_ospf_topology_route_config $args"
	set ::sth::ospfTopology::returnedKeyList ""
	
	set retVal [catch {
		#added to change input Router object handle to OspfRouterConfig object handle
		if {[set handle_idx [lsearch $args -handle]] < 0} {
			return -code error "Error: Required switch -handle not provided by user for mode $mode"
		}
		set routerHandle [lindex $args [expr {$handle_idx + 1}]]
		
		set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv2RouterConfig]
		if { $ospfHandle == "" } {
			set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv3RouterConfig]                 
		} 
		if { $ospfHandle == "" } {
			return -code error "Error: Provided router handle $routerHandle does not have a OspfvRouterConfig "
		}
    
		set args [lreplace $args [expr {$handle_idx + 1}] [expr {$handle_idx + 1}] $ospfHandle]
		#end--added to change input Router object handle to OspfRouterConfig object handle
    
		if {[catch {::sth::sthCore::commandInit ::sth::ospfTopology::ospfTopologyTable \
												$args \
												::sth::ospfTopology:: \
												emulation_ospf_topology_route_config \
												::sth::ospfTopology::userArgsArray \
												sortedSwitchPriorityList} err]} {
			return -code error "::sth::sthCore::commandInit Failed: $err"
		}
		
		set projectHandle [::sth::sthCore::invoke stc::get $::sth::ospfTopology::userArgsArray(handle) -parent]
		
		set ::sth::ospfTopology::topologyType $::sth::ospfTopology::userArgsArray(type)
    
		if {[string tolower $::sth::ospfTopology::userArgsArray(mode)] == $::sth::ospfTopology::MODE_CREATE} {
			::sth::ospfTopology::Emulation_ospf_Topology_config_create
		} elseif {[string tolower $::sth::ospfTopology::userArgsArray(mode)] == $::sth::ospfTopology::MODE_MODIFY} {
			::sth::ospfTopology::Emulation_ospf_Topology_config_modify
		} elseif {[string tolower $::sth::ospfTopology::userArgsArray(mode)] == $::sth::ospfTopology::MODE_DELETE} {
			::sth::ospfTopology::Emulation_ospf_Topology_config_delete
		}
	} returnedString]
    
	if {$retVal} {
	    if {$returnedString ne ""} {
		::sth::sthCore::processError ::sth::ospfTopology::returnedKeyList $returnedString {}
	    }
	} else {
	    keylset ::sth::ospfTopology::returnedKeyList status $::sth::sthCore::SUCCESS
	}
	return $::sth::ospfTopology::returnedKeyList
    }
}





