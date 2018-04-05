# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth::ospf:: {

    set ospfv2Resultdataset ""
    set ospfv3Resultdataset ""

    #add for gre. store the gre delivery header handle
    set greIpHeader ""

    variable ipv4Version 4
    variable flag_option_bits 1
}

##Procedure Header
#
# Name: ::sth::emulation_ospf_lsa_config
#
# Purpose: Creates, modifies, or deletes a Link State Advertisement (LSA).
#    When you add a route (see description for -mode), Spirent TestCenter
#    returns the LSA handle in a keyed list with "lsa_handles" as the key.
#
# Synopsis:
#    sth::emulation_ospf_lsa_config
#        { [-mode {create|reset} -handle <router_handle> |
#           -mode {modify|delete} -lsa_handle <lsa_handle>]
#         }
#        [-adv_router_id <a.b.c.d>]
#        [-link_state_id <1-7> ]
#        [-lsa_age <0-3600> ]
#        [-ls_seq <0 - 0xffffffff>]
#        [-options <hexadecimal> ]
#        { [-type asbr_summary ] |
#          [-type ext_pool
#           -external_number_of_prefix <numeric>
#           -external_prefix_forward_addr <0-128>
#           -external_prefix_metric <1-16777215>
#           -external_prefix_start {<a.b.c.d> |
#                <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}
#           -external_prefix_step <integer>
#           -external_prefix_type {1|2} ] |
#          [-type network
#            -attached_router_id <a.b.c.d>
#            -net_attached_router {create|delete|reset}
#            -net_prefix_length <1-128>  |
#          [-type nsssa_ext_pool
#           -nssa_number_of_prefix <numeric>
#           -nssa_prefix_forward_addr {<a.b.c.d> }
#               <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}
#           -nssa_prefix_length  <1-128>
#           -nssa_prefix_metric  <1-16777215>
#           -nssa_prefix_start   {<a.b.c.d> |
#               <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}
#           -nssa_prefix_step    <numeric>
#           -nssa_prefix_type   {1|2} ]  |
#          [-type router
#           -router_abr {0|1}
#           -router_asbr {0|1}
#           -router_link_data <a.b.c.d>
#           -router_link_id  <a.b.c.d>
#           -router_link_idx  <numeric>
#           -router_link_metric  <1-65535>
#           -router_link_mode {create|delete|reset}
#           -router_link_type {ptop|transit|stub|virtual}
#           -router_virtual_link_endpt {0|1} ] |
#          [-type summary_pool
#           -summary_number_of_prefix <numeric>
#           -summary_prefix_length <1-128>
#           -summary_prefix_metric <1-65535>
#           -summary_prefix_start  {<a.b.c.d>|
#               <aaaa:bbbb:cccc:dddd:eeee:ffff:gggg:hhhh>}
#           -summary_prefix_step   <numeric>
#
# Arguments:
#
#    -adv_router_id
#                Specifies the OSPF router ID of the LSA's originator.
#                (the Advertising Router field in the LSA header). The
#                default is 0.0.0.0. For router LSAs, this value is identical
#                to the Link-state ID value. For network LSAs, this value is
#                originated by the designated router. For summary LSAs, this
#                value is originated by area border routers. For
#                external/NSSA LSAs, this value is originated by AS boundary
#                routers.
#
#    -attached_router_id
#                Adds to the list of attached routers on this network. You
#                must specify this argument for network LSAs. You can attach
#                a router ID only to network LSAs. The default is 0.0.0.0.
#                Use this argument with -net_attached_router.
#
#    -external_number_of_prefix
#                Specifies the number of external IP LSAs to generate. Use
#                this argument with -type ext_pool.
#
#    -external_prefix_forward_addr
#                Specifies the forwarding IP address for the external LSA
#                pool. The default for IPv4 is 0.0.0.0, and the default
#                for IPv6 is 0:0:0:0:0:0:0:0. Use this argument only if you
#                specified -type ext_pool.
#
#    -external_prefix_length
#                Specifies the number of leading bits that form the network
#                part of an IP address for the external LSA pool. For IPv4,
#                possible values range from 0 to 32, and the default is 24.
#                For IPv6, possible values range from 1 to 128. The default
#                is 64, Use this argument only if you specified
#                -type ext_pool.
#
#    -external_prefix_metric
#                Specifies a metric value for the external LSA pool. Possible
#                values range from 1 to 16777215. The default is 1. Use this
#                argument only if you specified -type ext_pool.
#
#    -external_prefix_start
#                Specifies the starting IP address for the external LSA
#                pool. The default for IPv4 is 0.0.0.0 and the default
#                for IPv6 is 0:0:0:0:0:0:0:0. Use this argument only if you
#                specified -type ext_pool.
#
#    -external_prefix_step
#                Specifies the amount by which to increment the network part
#                of the first IP address to generate subsequent IP addresses
#                belonging to different routes for the external LSA pool. Use
#                this argument only if you specified -type ext_pool.
#
#    -external_prefix_type
#                Specifies the type of external LSA pool metric by setting
#                the E bit in the LSA header. Possible values are 1 and 2.
#                Specify 1 for type 1 (internal cost is added to external
#                cost) or 2 for type 2 (external cost only). The default is
#                1. Use this argument only if you specified -type ext_pool.
#
#    -handle        Identifies the OSPF router under which the LSA is created.
#
#    -link_state_id    Identifies the part of the routing domain being described by
#                the LSA. Depending on the advertisement's LS type, the link
#                state ID takes on one of the following values:
#
#                Type 1 - The originating router’s Router ID.
#
#                Type 2 - The IP interface address of the network’s
#                    Designated Router.
#
#                Type 3 - The destination network’s IP address.
#
#                Type 4 - The Router ID of the described AS boundary router.
#
#                Type 5 - The destination network’s IP address.
#
#                Type 7 - The destination network’s IP address.
#
#                Note: Do not specify -link_state_id with Type 3
#                (summary_pool), Type 5 (ext_pool), or Type 7 (nssa_ext_pool)
#                LSAs.
#
#    -lsa_handle    Identifies the LSA handle to modify or delete. You obtain
#                the LSA handle from the emulation_ospf_lsa_config function
#                when you use -mode create.
#
#    -ls_age        Specifies the age of the LSA, in seconds. The LS Age field
#                is examined if a router receives two instances of an LSA
#                with identical LS sequence numbers and LS checksums.
#                Possible values range from 0 to 3600. The default is 0.
#
#    -ls_seq        Specifies the LS sequence number, which is used to detect
#                old and duplicate LSAs. The larger the sequence number, the
#                more recent the LSA. The sequence number is a two-byte
#                value. Possible values range from 0 to 0xffffffff. The
#                default is 0x80000001.
#
#    -mode        Specifies the action to perform. You can create, modify, or
#                delete an LSA, or delete all LSAs (reset). The modes are
#                described below:
#
#                create - Creates a new Link State Advertisement. See the
#                    description of the -type argument for a list of LSAs
#                    that you can create. Use the -handle argument to
#                    specify the router under which the LSA is created.
#
#                modify - Modifies a Link State Advertisement. Use the
#                    -lsa_handle argument to specify the LSA to modify.
#
#                delete - Deletes a Link State Advertisement. Use the
#                    -lsa_handle argument to specify the LSA to delete.
#
#                reset - Deletes all LSAs under the router specified in the
#                    -handle argument.
#
#    -net_attached_router
#                Specifies whether to add an attached router to the
#                network, delete an existing attached router from the
#                network, or reset all the attached routers of the
#                network. For create and delete mode, you must specify the
#                -attached_router_id argument. Possible values are create,
#                delete, and reset.
#
#                When you specify "-mode create", you must also specify
#                "create" for the -net_attached_router argument. However,
#                when you specify "-mode modify", -net_attached_router
#                can be either "delete" or "reset".
#
#    -net_prefix_length
#                Specifies the number of leading bits which form the network
#                part of an IP address. Possible values for IPv4 addresses
#                range from 1 to 32; the default is 24, Possible values for
#                IPv6 addresses range from 1 to 128;the default is 64,
#
#    -nssa_number_of_prefix
#                Specifies the number of routes in a Type 7 NSSA area
#                external pool LSA. Use this argument only if you specified
#                -type nssa_ext_pool.
#
#    -nssa_prefix_forward_addr
#                Specifies the forwarding IP address for a Type 7 NSSA
#                external pool LSA. Use this argument only if you specified
#                -type nssa_ext_pool. The default for IPv4 is 0.0.0.0
#                and the default for IPv6 is 0:0:0:0:0:0:0:0.
#
#    -nssa_prefix_length
#                Specifies the number of leading bits which form the network
#                part of an IP address for a Type 7 NSSA external pool LSA.
#                Use this argument only if you specified -type nssa_ext_pool.
#                Possible values for IPv4 addresses range from 1 to 32; the
#                default is 24, Possible values for IPv6 addresses range from
#                1 to 128;the default is 64,
#
#    -nssa_prefix_metric
#                Specifies a metric value for a Type 7 NSSA external pool
#                LSA. Use this argument only if you specified -type
#                nssa_ext_pool. Possible values range from 1 to 16777215.
#
#    -nssa_prefix_start
#                Specifies the starting IP address for a Type 7 NSSA external
#                pool LSA. Use this argument only if you specified
#                -type nssa_ext_pool. The default for IPv4 is 0.0.0.0
#                and the default for IPv6 is 0:0:0:0:0:0:0:0.
#
#    -nssa_prefix_step
#                Specifies the amount by which to increment the network part
#                of the first IP address to generate subsequent IP addresses
#                belonging to different routes for a Type 7 NSSA external
#                pool LSA. Use this argument only if you specified -type
#                nssa_ext_pool.
#
#    -nssa_prefix_type
#                Specifies the type of NSSA external pool LSA metric by
#                setting the E bit in the LSA header. Possible values are 1
#                and 2. Specify 1 for type 1 (internal cost is added to
#                external cost) or 2 for type 2 (external cost only). The
#                default is 1. Use this argument only if you specified
#                -type nssa_ext_pool.
#
#    -options        A bit mask that specifies the settings of the Options field
#                in the LSAs. The Options field describes the optional
#                OSPF capabilities of the router. Section A.2 in RFC 2328
#                describes the Options field for OSPFv2. Section A.2 in RFC
#                2740 describes the Options field for OSPFv3.
#
#                Use hexadecimal for this value. The default for OSPFv2,
#                0x02, sets the E-bit (binary 00000010). The default for
#                OSPFv3, 0x13, sets the R-bit, the E-bit, and the V6-bit
#                (binary 000...010011).
#
#                You can specify one of the following values for this
#                argument:
#
#                O: 0x40:     This bit describes the router's willingness to
#                        receive and forward Opaque LSAs.
#
#                DC: 0x20: This bit describes the router's handling of demand
#                        circuits.
#
#                EA: 0x10: This bit describes the router's willingness to
#                        receive and forward External-Attributes-LSAs.
#
#                NP: 0x08: This bit describes the handling of Type-7 LSAs.
#
#
#                MC: 0x04:    This bit describes whether IP multicast datagrams
#                        are forwarded.
#
#                E: 0x02:    This bit describes the way AS-external-LSAs are
#                        flooded.  When this bit is set, the area type is
#                        external_capable; when this bit is cleared, the
#                        area type is stub.
#
#                For OSPFv3, you can also specify one of the following values
#                for this argument.
#
#                R: 0x10:     This bit indicates if the originator is an active
#                        router. If this is clear, routes that transit the
#                        advertising node cannot be computed.
#
#                V6: 0x01:    If this bit is clear, the router/link should be
#                        excluded from IPv6 routing calculations.
#
#    -router_abr
#                Identifies the router as an area boundary router (ABR).
#                Corresponds to the E (external) bit in router LSA. Possible
#                values are 0 and 1. Specify 0 for false or 1 for true. The
#                default is 0 (false). Use this argument only if you
#                specified -type router.
#
#    -router_asbr
#                Identifies the router as an AS boundary router (ASBR).
#                Corresponds to the B (border) bit in router LSA. Possible
#                values are 0 and 1. Specify 0 for false or 1 for true. The
#                default is 0 (false). Use this argument only if you
#                specified -type router.
#
#    -router_link_data
#                Specifies the data (IP address) for a router link. The
#                default is 0.0.0.0. Use this argument only if you
#                specified -type router.
#
#    -router_link_id
#                Specifies the ID for a router link. The router link ID is a
#                32-bit value, represented in dot notation. (It is not an IP
#                address.) The default is 0.0.0.0. Use this argument only if
#                you specified -type router.
#
#    -router_link_idx
#                Specifies an index to an added router link. When a link is
#                removed, the remaining links are re-indexed. Use this
#                argument only if you specified -type router.
#
#    -router_link_metric
#                Defines the metric value for a router link. The metric value
#                contributes to the overall cost of a route to a destination.
#                (The metric is the cost associated with the output side of a
#                router interface; the lower the cost, the more likely a
#                router will be used to forward traffic.) Possible values
#                range from 1 to 65535. The default is 1. Use this argument
#                only if you specified -type router.
#
#    -router_link_mode
#                Specifies the action to be performed for a router LSA. Use
#                this argument only if you specified -type router. Possible
#                values are create, delete, or reset. The modes are described
#                below:
#
#                create - Creates a router link. When you specify -mode
#                    create, you must also specify create for the
#                    -router_link_mode argument. However, when you specify
#                    -mode modify, -router_link_mode can be create, delete
#                    or reset. Also, when you specify -router_link_mode
#                    create, you must also use the -router_link_id,
#                    -router_link_data, -router_link_type, and
#                    -router_link_metric arguments.
#
#                delete - Deletes a router link. When you specify delete
#                    mode, you must also specify the -router_link_id
#                    argument.
#
#                reset - Deletes all the links under the router LSA.
#
#    -router_link_type
#                Identifies the type of link. Possible values are ptop,
#                transit, stub, and virtual:
#
#                ptop - A ptop (point-to-point) link is a physical or logical
#                    serial link between two routers. The link can be
#                    numbered (IP address is configured on the link) or
#                    unnumbered.
#
#                transit - A transit network link connects a router to a
#                    transit network. A transit network has more than one
#                    router attached to it, and it is capable of carrying
#                    data traffic for which the source and destination are
#                    outside of the local area.
#
#                stub - A stub network link connects a router to a stub
#                    network (not the same as a Stub Area). A stub network,
#                    or stub segment, has one router attached to it. One
#                    router attached to an Ethernet or Token Ring network is
#                    considered a link to a stub network.
#
#                virtual - A virtual link is a logical link connecting areas
#                    with no physical connections to the backbone. Virtual
#                    links are treated as numbered point-to-point links.
#
#                Use this argument only if you specified -type router.
#
#    -router_virtual_link_endpt
#                Sets or unsets the router as a virtual link endpoint. A
#                virtual link is a logical link connecting areas with no
#                physical connections to the backbone. Virtual links are
#                treated as numbered point-to-point links. Possible values
#                are 0 and 1. The default is 0. Use this argument only if you
#                specified -type router.
#
#    -summary_number_of_prefix
#                Specifies the number of routes in the summary pool LSA. The
#                default is 0. Use this argument only if you specified
#                -type summary_pool.
#
#    -summary_prefix_length
#                Specifies the number of leading bits which form the network
#                part of an IP address for the summary pool LSA. Possible
#                values for IPv4 addresses range from 1 to 32; the default is
#                24, Possible values for IPv6 addresses range from 1 to 128;
#                the default is 64, Use this argument only if you specified
#                -type summary_pool.
#
#    -summary_prefix_metric
#                Defines the metric value for the summary pool LSA. The
#                metric value contributes to the overall cost of a route to a
#                destination. (The metric is the cost associated with the
#                output side of a router interface; the lower the cost, the
#                more likely a router will be used to forward traffic.)
#                Possible values range from 1 to 65535. The default is 1. Use
#                this argument only if you specified -type summary_pool.
#
#    -summary_prefix_start
#                Specifies the starting IP address for the summary pool LSA.
#                The default for IPv4 is 0.0.0.0. The default for IPv6
#                is 0:0:0:0:0:0:0:0. Use this argument only if you specified
#                -type summary_pool.
#
#    -summary_prefix_step
#                Specifies the increment to use to generate the network
#                part of the first IP address as well as to generate
#                subsequent IP addresses belonging to different routes for
#                the summary pool LSA. Use this argument only if you
#                specified -type summary_pool.
#
#    -type        Specifies the type of LSA to create. Possible values and
#                descriptions are as follows:
#
#                router - (Type 1) Describes the states and costs of the
#                    router’s interfaces. Indicates that the router is
#                    either an area border router (ABR) or an autonomous
#                    system boundary router (ASBR). The Options field is
#                    expanded to 24 bits for OSPFv3 LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id  3.3.3.3  \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle $hOspfv2RouterHandle \
#                    -mode create \
#                    -type router \
#                    -router_abr 1 \
#                    -router_asbr 1 \
#                    -router_link_data 5.5.5.5 \
#                    -router_link_id 4.4.4.4 \
#                    -router_link_idx 2 \
#                    -router_link_metric 300 \
#                    -router_link_mode create \
#                    -router_link_type stub \
#                    -router_virtual_link_endpt  1
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 (interface ID) \
#                    -link_state_id  3.3.3.3 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle $hOspfv3RouterHandle \
#                    -mode create \
#                    -type router \
#                    -router_abr 1 \
#                    -router_asbr 1 \
#                    -router_link_data 5.5.5.5 \
#                    -router_link_id 4.4.4.4 \
#                    -router_link_idx 2 \
#                    -router_link_metric 300 \
#                    -router_link_mode create \
#                    -router_link_type stub \
#                    -router_virtual_link_endpt  1
#
#                network - (Type 2) Originated by the link's designated
#                    router (DR) for every broadcast or non-broadcast multi-
#                    access (NBMA) link having two or more attached routers.
#                    Lists all routers attached to the link.
#
#                    OSPFv3 network LSAs have no address information and are
#                    network protocol independent. The Options field is
#                    expanded to 24 bits for OSPFv3 LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 1.1.1.1 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle $hOspfv2RouterHandle \
#                    -mode create \
#                    -type network \
#                    -attached_router_id 2.2.2.2 \
#                    -net_attached_router  create \
#                    -net_prefix_length 24
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 1.1.1.1 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle $hOspfv3RouterHandle \
#                    -mode create \
#                    -type network \
#                    -attached_router_id 2.2.2.2 \
#                    -net_attached_router  create \
#                    -net_prefix_length 24
#
#                summary_pool - (Type 3) Summary Pool (OSPFv2) and Inter-Area
#                    Prefix LSA (OSPFv3) describe routes to networks outside
#                    of the area. (In version 3, the Inter-Area (Prefix LSA
#                    replaces the Summary Pool LSA.) Originated by ABRs. Do
#                    not specify a link state ID for OSPFv2 summary pool
#                    LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -handle $hOspfv2RouterHandle \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -mode create \
#                    -type summary_pool \
#                    -summary_number_of_prefix 10 \
#                    -summary_prefix_length 16 \
#                    -summary_prefix_metric 5000 \
#                    -summary_prefix_start 10.10.10.10 \
#                    -summary_prefix_step 10
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -handle $hOspfv3RouterHandle \
#                    -link_state_id 64 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -mode create \
#                    -type summary_pool \
#                    -summary_number_of_prefix 10 \
#                    -summary_prefix_length 64 \
#                    -summary_prefix_metric 5000 \
#                    -summary_prefix_start CAFE::10 \
#                    -summary_prefix_step 10
#
#                asbr_summary - (Type 4)
#                    For OSPFv2, describes routes to autonomous system
#                    boundary routers outside of the area in which the LSA
#                    is transmitted (flooded). Originated by area border
#                    routers (ABRs).
#
#                    For OSPFv3, Inter-Area Router LSA, replaces the OSPFv2
#                    AS Boundary Router Summary LSA. The Options field is
#                    expanded to 24 bits for OSPFv3 LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 3.3.3.3  \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv2RouterHandle \
#                    -mode create \
#                    -type asbr_summary
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 3.3.3.3  \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv3RouterHandle \
#                    -mode create \
#                    -type asbr_summary
#
#                ext_pool - (Type 5) Describes routes to destinations
#                    external to the AS. A default route for the AS can also
#                    be described by this type of LSA. Originated by AS
#                    boundary routers (ASBRs). Do not specify a link state
#                    ID for OSPFv2 external pool LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv2RouterHandle \
#                    -mode create \
#                    -type ext_pool \
#                    -external_number_of_prefix 30 \
#                    -external_prefix_forward_addr   40.40.40.40 \
#                    -external_prefix_length   16 \
#                    -external_prefix_metric   3000 \
#                    -external_prefix_start  30.30.30.30 \
#                    -external_prefix_step  30 \
#                    -external_prefix_type   1
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 0.0.0.1 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv3RouterHandle \
#                    -mode create \
#                    -type ext_pool \
#                    -external_number_of_prefix 30 \
#                    -external_prefix_forward_addr   CFFF::40 \
#                    -external_prefix_length   64 \
#                    -external_prefix_metric   3000 \
#                    -external_prefix_start  FFEE::30 \
#                    -external_prefix_step  30 \
#                    -external_prefix_type   1
#
#                nssa_ext_pool - (Type 7) Describes routes to destinations
#                    external to the AS, usually from a different protocol.
#                    Originated by AS boundary routers (ASBRs). Do not
#                    specify a link state ID for OSPFv2 NSSA external pool
#                    LSAs.
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv2, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv2RouterHandle \
#                    -mode create \
#                    -type nssa_ext_pool \
#                    -nssa_number_of_prefix   100 \
#                    -nssa_prefix_forward_addr   40.40.40.40 \
#                    -nssa_prefix_length   24 \
#                    -nssa_prefix_metric  5000 \
#                    -nssa_prefix_start  20.20.20.20 \
#                    -nssa_prefix_step  20 \
#                    -nssa_prefix_type  1
#
#                    You must provide the following arguments for this type
#                    of LSA in OSPFv3, as shown in this sample code snippet:
#
#                    -adv_router_id 1.1.1.1 \
#                    -link_state_id 0.0.0.2 \
#                    -ls_age 300 \
#                    -ls_checksum 5000 \
#                    -ls_seq 7000 \
#                    -handle  $hOspfv3RouterHandle \
#                    -mode create \
#                    -type nssa_ext_pool \
#                    -nssa_number_of_prefix   100 \
#                    -nssa_prefix_forward_addr   CFE0::1 \
#                    -nssa_prefix_length   64 \
#                    -nssa_prefix_metric  5000 \
#                    -nssa_prefix_start  FFEE::20 \
#                    -nssa_prefix_step  20 \
#                    -nssa_prefix_type  1
#
# Return Values: The function returns a keyed list using the following keys
#            (with corresponding data):
#
#    lsa_handle    The handle returned by the function when you use -mode
#                create to create a new LSA. When you want to modify or
#                delete the LSA, you specify the handle as the value to the
#                -lsa_handle argument
#
#    adv_router_id    <a.b.c.d>
#    router        The keyword "router" returns a list of links for an LSA of
#                type "router".
#    links
#        0.id        <link ID a.b.c.d>
#        data        <link data a.b.c.d>
#        type        {ptop|transit|stub|virtual}
#        1.id        <link ID a.b.c.d>
#        data        <link data a.b.c.d>
#        type        {ptop|transit|stub|virtual}
#
#    <idx=n>.id    <link ID a.b.c.d>
#        data        <link data a.b.c.d>
#        type        {ptop|transit|stub|virtual}
#
#    network        The keyword "network" returns a list of attached router IDs
#                for a network LSA.
#
#    attached_router_ids        <list_of_a.b.c.d>
#
#    summary        The keyword "summary" returns a list of prefixes for a
#                summary LSA pool.
#    external        The keyword "external" returns a list of prefixes for an
#                external LSA pool.
#    nssa            The keyword "nssa" returns a list of prefixes for an NSSA
#                LSA pool
#        num_prefix    <number of prefixes>
#        prefix_start    <a.b.c.d>
#        prefix_length    <n>
#        prefix_step    <a.b.c.d>
#
#    status         Success (1) or failure (0) of the operation.
#    log            An error message (if the operation failed).
#
# Description: The sth::emulation_ospf_lsa_config function creates, modifies, or
#    deletes a Link State Advertisement (LSA). Use the -mode argument to specify
#    the operation to perform. When you create an LSA, the function returns a
#    handle to the newly created LSA. Use this handle as input for modify and
#    delete mode operations.
#
#    The mode that you use determines the set of arguments that you use to
#    configure the LSA.
#
#    - When you specify -mode create, you must also use the -type argument to
#      specify the type of LSA to create.
#    - To provide prefix information, use the set of arguments that correspond
#      to the type of LSA. For example, when you create an AS external LSA
#      (-type ext_pool), you also specify prefix information by using the
#      -external_prefix_length and -external_prefix_metric arguments. See the
#      examples in the type argument for the required arguments for each LSA
#      type. You specify the prefix information for the following types of LSAs:
#      summary_pool, ext_pool, and nssa_pool.
#
#    Every router sends a router LSA. Each router can only originate one router
#    LSA. If your create another router LSA for the same originating router, it
#    overwrites the previous one. That is how the stack works. If you create
#    multiple Router LSAs, the stack does not combine the router links for you
#    under the same originating router. However, you can create multiple router
#    LSA links for the same router LSA. Also you can create multiple router LSAs
#    for different originating routers. In this case, the advertising router's
#    ID must be different).
#
#    AS boundary routers send a single AS-external LSA for each AS external
#    destination. To define routers in external areas, you must specify
#    nssa_ext_pool or ext_pool in the -type argument.
#
#    Designated routers send network LSAs for any networks with which it is
#    associated. To identify the routers attached to a network link, you must
#    specify network in the -type argument.
#
#    Area border routers send a single summary LSA for each known inter-area
#    destination. To describe routes to networks outside of the local area. you
#    must specify summary_pool in the -type argument. To describe routes to AS
#    boundary routers outside the local area, you must specify asbr_summary in
#    the -type argument.
#
# Examples:
#    The following sample code snippet creates a router LSA:
#
#    ::sth::emulation_ospf_lsa_config \
#        -mode create \
#        -type router \
#        -adv_router_id [lindex $routerIpList $i] \
#        -handle $hRouter($i) \
#        -link_state_id [lindex $routerIpList $i] \
#        -ls_age 0 \
#        -ls_seq 80000001 \
#        -router_abr 1 \
#        -router_asbr 1 \
#        -router_link_data 255.255.255.255 \
#        -router_link_id [lindex $routerIpList $i] \
#        -router_link_idx 1 \
#        -router_link_metric 1 \
#        -router_link_mode create \
#        -router_link_type stub \
#        -router_virtual_link_endpt 0
#
#    Here is the output for the above example:
#    {status 1} {lsa_handle 362} {adv_router_id 18.18.18.18} {router {{links
#    {{{0 {{id 17.17.17.17}}} {data 16646656} {type stub}}}}}}
#
#    The following sample code snippet creates a router LSA link:
#
#    ::sth::emulation_ospf_lsa_config \
#        -mode modify \
#        -type router \
#        -adv_router_id [lindex $routerIpList $i]\
#        -lsa_handle $hLsaHandle($i)\
#        -link_state_id [lindex $routerIpList $i]\
#        -ls_age 0\
#        -ls_seq 80000001\
#        -router_abr 1\
#        -router_asbr 1\
#        -router_link_data 0.0.0.2\
#        -router_link_id 50.50.50.50\
#        -router_link_idx 2\
#        -router_link_metric 1\
#        -router_link_mode create\
#        -router_link_type ptop \
#        -router_virtual_link_endpt 0
#
#    The following sample code snippet creates a network LSA:
#
#    ::sth::emulation_ospf_lsa_config \
#        -adv_router_id 18.18.18.18 \
#        -handle 182 \
#        -link_state_id 64 \
#        -ls_age 300 \
#        -ls_checksum 5000 \
#        -ls_seq 7000 \
#        -mode create \
#        -type network \
#        -attached_router_id 17.17.17.17 \
#        -net_attached_router create \
#        -net_prefix_length 64
#
#    Here is the output for the above example:
#    {status 1} {lsa_handle 354} {adv_router_id 18.18.18.18} {network
#    {{attached_router_ids 17.17.17.17}}}
#
#    The following sample code snippet creates an external LSA pool:
#
#    ::sth::emulation_ospf_lsa_config \
#        -adv_router_id 1.1.1.1 \
#        -handle 182 \
#        -link_state_id 64 \
#        -ls_age 300 \
#        -ls_checksum 5000 \
#        -ls_seq 7000 \
#        -mode create \
#        -type ext_pool \
#        -external_number_of_prefix 30 \
#        -external_prefix_forward_addr  CAFF::40 \
#        -external_prefix_length   64 \
#        -external_prefix_metric   3000 \
#        -external_prefix_start  FFEE::30 \
#        -external_prefix_step  30 \
#        -external_prefix_type   1
#
#    Here is the output for the above example:
#    {status 1} {lsa_handle 324} {adv_router_id 1.1.1.1}
#    {external {{num_prefx 30} {prefix_length 64} {prefix_start 1.1.1.0}
#    {prefix_step 30}}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#           1) A metric is a number that is used to specify the cost of the
#            route, so that the best route (potentially among multiple
#            routes to the same destination) can be selected.
#
#
# End of Procedure Header
proc ::sth::emulation_ospf_lsa_config {args} {
    ::sth::sthCore::Tracker ::emulation_ospf_lsa_config $args

    ::sth::sthCore::log hltcall "User executed ::sth::emulation_ospf_lsa_config $args"

    variable returnKeyedList
    set returnKeyedList ""

    set retVal [catch {
        if {[set idx [lsearch $args -mode]] < 0} {
            ::sth::sthCore::processError returnKeyedList "Error: Required switch -mode not provided by user" {}
            return
        }

        set mode [lindex $args [expr {$idx + 1}]]

        if {[string equal -nocase $mode reset] || [string equal -nocase $mode create] || [string equal -nocase $mode enable]} {
            #added to change the input Router objecthandle to OspfRouterConfig object handle
            if {[set handle_idx [lsearch $args -handle]] < 0} {
                ::sth::sthCore::processError returnKeyedList "Error: Required switch -handle not provided by user for mode $mode" {}
                return
            }
            set routerHandle [lindex $args [expr {$handle_idx + 1}]]

            if {[set type_idx [lsearch $args -session_type]] >= 0} {
                set session_type [lindex $args [expr {$type_idx + 1}]]
            } else {
                set session_type ospfv2
            }

            set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-$session_type\RouterConfig]

            if { $ospfHandle == "" } {
                set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv3RouterConfig]
            }
            if { $ospfHandle == "" } {
                ::sth::sthCore::processError returnKeyedList "Error: Provided router handle $routerHandle does not have a \
                OspfvRouterConfig " {}
                return
            }

            set args [lreplace $args [expr {$handle_idx + 1}] [expr {$handle_idx + 1}] $ospfHandle]
            #end--added to change the input Router objecthandle to OspfRouterConfig object handle

            if {[string match -nocase "Ospfv2RouterConfig*" $ospfHandle]} {
                set procPrefix "emulation_ospfv2_lsa_config"
            } elseif {[string match -nocase "Ospfv3RouterConfig*" $ospfHandle]} {
                set procPrefix "emulation_ospfv3_lsa_config"
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: Provided handle $ospfHandle is not of type \
                    Ospfv2RouterConfig or Ospfv3RouterConfig. It is of type $ospfRouter" {}
                return
            }
        } elseif {[string equal -nocase $mode modify] || [string equal -nocase $mode delete]} {
            if {[set idx [lsearch $args -lsa_handle]] < 0} {
                ::sth::sthCore::processError returnKeyedList "Error: Required switch -lsa_handle not provided by user for mode $mode" {}
                return
            }

            set lsaHandle [lindex $args [expr {$idx + 1}]]

            set ret [set name [::sth::sthCore::invoke stc::get $lsaHandle Name]]

            set lsa [lindex $name 0]

            #assuming that OSPFv3 LSAs always have a "v3" occurance in their names.
            if {[string first "v3" $lsa ] >= 0 || [string first "V3" $lsa ] >= 0} {
                set procPrefix "emulation_ospfv3_lsa_config"
            } else {
                set procPrefix "emulation_ospfv2_lsa_config"
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: Provided mode value $mode is invalid" {}
            return
        }

        if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: $procPrefix userArgsArray sortedSwitchPriorityList} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
            return
        }

        #delete unecessary elements from the array
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)

        set cmd "::sth::ospf::emulation_ospf_lsa_config_$userArgsArray(mode) userArgsArray sortedSwitchPriorityList $procPrefix"

        switch $userArgsArray(mode) {
            create {
                if {![info exists userArgsArray(handle)]} {
                    ::sth::sthCore::processError returnKeyedList "Error: handle not provided by user for -mode create" {}
                    return
                }
                if {![info exists userArgsArray(type)]} {
                    ::sth::sthCore::processError returnKeyedList "Error: type not provided by user for -mode create" {}
                    return
                }

                if {[info exists userArgsArray(router_link_mode)]} {
                    set routerLinkMode $userArgsArray(router_link_mode)

                    if {$routerLinkMode == "create"} {
                        if {![info exists userArgsArray(router_link_id)] || ![info exists userArgsArray(router_link_data)]\
                        || ![info exists userArgsArray(router_link_type)] || ![info exists userArgsArray(router_link_metric)] } {
                            ::sth::sthCore::processError returnKeyedList "Error: router_link_id, router_link_data, router_link_type\
                             and router_link_metric must be provided  for -router_link_mode create" {}
                            return
                        }
                    } elseif {$routerLinkMode == "delete"} {
                        if {![info exists userArgsArray(router_link_id)]} {
                            ::sth::sthCore::processError returnKeyedList "Error: router_link_id must be provided for -router_link_mode delete" {}
                            return
                        }
                    }
                }

                if {[info exists userArgsArray(net_attached_router)]} {
                    set attachedRouterMode $userArgsArray(net_attached_router)

                    if {$attachedRouterMode == "delete" || $attachedRouterMode == "create"} {
                        if {![info exists userArgsArray(attached_router_id)]} {
                            ::sth::sthCore::processError returnKeyedList "Error: attached_router_id must be provided for -net_attached_router $attachedRouterMode" {}
                            return
                        }
                    }
                }
            }
            reset {
                if {![info exists userArgsArray(handle)]} {
                    ::sth::sthCore::processError returnKeyedList "Error: handle not provided by user for -mode reset" {}
                    return
                }
            }
            modify -
            delete {
                if {$userArgsArray(mode) == "modify"} {
                    if {[info exists userArgsArray(router_link_mode)]} {
                        set routerLinkMode $userArgsArray(router_link_mode)

                        if {$routerLinkMode == "create"} {
                            if {![info exists userArgsArray(router_link_id)] || ![info exists userArgsArray(router_link_data)]\
                            || ![info exists userArgsArray(router_link_type)] || ![info exists userArgsArray(router_link_metric)] } {
                                ::sth::sthCore::processError returnKeyedList "Error: router_link_id, router_link_data, router_link_type\
                                and router_link_metric must be provided  for -router_link_mode create" {}
                                return
                            }
                        } elseif {$routerLinkMode == "delete"} {
                            if {![info exists userArgsArray(router_link_id)]} {
                                ::sth::sthCore::processError returnKeyedList "Error: router_link_id -router_link_mode delete" {}
                                return
                            }
                        }
                    }

                    if {[info exists userArgsArray(net_attached_router)]} {
                        set attachedRouterMode $userArgsArray(net_attached_router)

                        if {$attachedRouterMode == "delete" || $attachedRouterMode == "create"} {
                            if {![info exists userArgsArray(attached_router_id)]} {
                                ::sth::sthCore::processError returnKeyedList "Error: attached_router_id must be provided for -net_attached_router $attachedRouterMode" {}
                                return
                            }
                        }
                    }
                }

                if {![info exists userArgsArray(lsa_handle)]} {
                    ::sth::sthCore::processError returnKeyedList "Error: lsa_handle not provided by user for -mode $userArgsArray(mode)" {}
                    return
                }
            }
        }

        if {[catch {set ret [eval $cmd]} err]} {
            ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
            return
        }

        if {$ret == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::log error "Evaluating $cmd Failed: $err"
            return
        }

        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status $::sth::sthCore::SUCCESS]
    } returnedString ]

    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        keylset returnKeyedList status $::sth::sthCore::SUCCESS
    }
    return $returnKeyedList
}


proc ::sth::emulation_ospf_tlv_config { args } {

    ::sth::sthCore::Tracker "::sth::emulation_ospf_tlv_config" $args

    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_tlv_config"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable\
                                                            $args\
                                                            ::sth::ospf::\
                                                            emulation_ospf_tlv_config\
                                                            userArgsArray\
                                                            sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList
    }

    unset userArgsArray(optional_args)
    unset userArgsArray(mandatory_args)

    set modeVal create
    if {[info exists userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }

    set cmd "::sth::ospf::${hltCmdName}\_$modeVal userArgsArray"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}



##Procedure Header
#
# Name: ::sth::emulation_ospf_config
#
# Purpose:
#    Creates, enables, disables, modifies, or deletes one or more emulated Open
#    Shortest Path First (OSPF) routers on the specified test port. OSPF is an
#    Interior Gateway Protocol (IGP) that is designed to manage communications
#    in large IP networks by dividing them into smaller networks called "areas."
#
#    An individual router maintains a local state that represents the router’s
#    interfaces and adjacent neighbors. OSPF routers use link state
#    advertisements (LSAs) to exchange the local state information. Within an
#    AS, the combined LSA data produces a link-state database. Routers maintain
#    a representation of the AS topology in a link-state database. Each router
#    has a separate link-state database for each area to which it is connected.
#    A router uses the topology information to create a shortest-path tree for
#    the routing table.
#
#    OSPFv2 is designed to work with IPv4. OSPFv3 uses IPv6. The two OSPF
#    protocols are based on the same concepts of LSA communication. In general,
#    OSPFv3 introduces new LSA types, and it modifies the packet format to
#    support IPv6 addresses, IPv6 authentication, and multiple instances per
#    link. (For detailed information about the differences between the
#    protocols, see RFC 2740, "OSPF for IPv6".)
#
# Synopsis:
#    sth::emulation_ospf_config
#        { [-mode create -port_handle <port_handle> |
#           -mode {modify|delete|disable|enable}
#                -handle <OSPF_handle>} ]
#        [-area_id <a.b.c.d>]
#            [-area_id_step <integer>]
#            [-area_type {external_capable | stub | nssa} ]
#        { [-authentication_mode simple -password <password> |
#           -authentication_mode {null | MD5} ] }
#        [-count <1-100> ]
#        [-dead_interval <1-65535>]
#        [-demand_circuit {1|0} ]
#        [-hello_interval <1-65535>]
#        [-instance_id <1-65535>]
#        [-instance_id_step <integer>]
#        [-interface_cost <1-65535>]
#        [-intf_ip_addr <a.b.c.d>]
#            [-intf_ip_addr_step <integer>]
#            [-intf_prefix_length <1-128>]
#        [-lsa_retransmit_delay <1-65535>]
#        [-md5_key_id <1-255>]
#        [-network_type {broadcast|ptop} ]
#        [-option_bits <hexadecimal>]
#        [-router_id <a.b.c.d> ]
#        [-router_id_step <integer>]
#        [-router_priority <0-255>]  for broadcast and nba networks only
#        [-session_type {ospfv2 | ospfv3}]
#        [-te_enable {1|0} ]
#        [-te_admin_group <1-4294967295>]
#        [-te_max_bw <0-MAX_DOUBLE>]
#        [-te_max_resv_bw <0-MAX_DOUBLE>]
#        [-te_max_metric <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority0 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority1 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority2 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority3 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority4 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority5 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority6 <0-MAX_DOUBLE>]
#        [-te_unresv_bw_priority7 <0-MAX_DOUBLE>]
#        [-vlan_id    <0-4095>]
#        [-vlan_id_mode {fixed|increment}]
#        [-vlan_id_step <1-4094>]
#        [-vlan_user_priority <0-7>]
#
# Arguments:
#
#    -area_id        Identifies the OSPF area to which the router belongs.
#                Areas are groups of contiguous networks and attached hosts.
#                A network belongs to only one area. Each area has an area
#                ID, designated as x.x.x.x. The area ID is NOT an IP address
#                although it looks like one. Areas should be kept to a
#                maximum of 100 routers. The default area ID is 0.0.0.0.
#
#    -area_id_step    The increment between consecutive area IDs when multiple
#                emulated OSPF routers are created. Possible values are 1 to
#                255. The default is 1.
#
#    -area_type    Specifies the type of area to which the OSPF router belongs
#                and sets two option bits: the E bit and the NP bit. If you
#                also specify the -option_bits argument, the -option_bit
#                setting overwrites any previous value (the -area_type
#                argument is processed before the -option_bit argument).
#                Possible values are external_capable, stub, and nssa. The
#                default is external_capable.
#
#                external_capable - An area in which non-AS boundary routers
#                    can handle routes to destinations outside of the
#                    autonomous system. In an external_capable area,
#                    boundary routers will flood the area with AS-external
#                    LSAs describing the external routes. Specifying
#                    -area_type external capable sets the E bit
#
#                stub - An area that does not handle external routes.  AS-
#                    external LSAs are not flooded into stub areas, so you
#                    cannot redistribute routing data from another protocol
#                    into a stub area. Specifying -area_type stub clears the
#                    E bit
#
#                nssa - (not so stubby area) An area that supports NSSA-
#                    encoded route information area. It allows external
#                    routes to be flooded within the area but does not allow
#                    external routes from other areas to enter it.
#                    Specifying -area_type nssa sets the NP bit.
#
#    -authentication_mode
#                (OSPFv2 only) Specifies the authentication mode for an
#                interface. Possible values are null, simple, and MD5.
#
#                null - No authentication
#
#                simple - Simple authentication uses a password (key) that is
#                    configured on each router and is included in plain text
#                    in each OSPF packet originated by that router
#
#                MD5 - MD5 authentication is based on shared secret keys that
#                    are configured in all routers in the area
#
#                All OSPF protocol exchanges are authenticated. The
#                authentication type is configurable on a per-area basis.
#
#    -count        Defines the number of OSPF routers to create on the
#                interface. Possible values are 1 to 100. The default is 1.
#
#    -dead_interval    Specifies the number of seconds after receiving the most
#                recent hello message, at which point neighboring routers
#                will declare the emulated router down. Possible values range
#                from 1 to 65535. The default is 40 on broadcast networks;
#                otherwise, it is 120.
#
#    -demand_circuit
#                Enables the demand circuit bit. Pertains to handling of
#                demand circuits (DCs) by the router. Possible values are 0
#                and 1. If true (1), sets the DC bit(0x20) in the Options
#                field of all LSAs generated.
#
#    -handle        Specifies the OSPF handle(s) to use when mode is set to
#                modify, delete, enable, or disable. This argument is not
#                valid for create mode. Instead, use -port_handle.
#
#    -hello_interval
#                Specifies the amount of time, in seconds, between Hello
#                messages. Possible values range from 1 to 65535. The default
#                is 10 on broadcast networks; otherwise, it is 30.
#
#    -instance_id    (OSPFv3 only) Defines the instance ID of the OSPFv3 process.
#                This ID allows multiple instances of the OSPFv3 protocol to
#                run simultaneously over the same link. Possible values range
#                from 0 to 65535. The default is 0.
#
#    -instance_id_step
#                (OSPFv3 only) Defines the amount by which the -instance_id
#                is incremented for multiple sessions. The default is 1.
#
#    -interface_cost
#                The metric associated with sending packets over the OSPF
#                interface. Possible values range from 1 to 65535. The
#                default is 1.
#
#    -intf_ip_addr    Specifies the IP address of the interface for the OSPF
#                emulated router that will establish an adjacency with the
#                DUT. The default for IPv4 is 192.85.1.3. The default for
#                IPv6 is 0:0:0:0:0:0:0:0.
#
#    -intf_ip_addr_step
#                Specifies the difference between interface IP addresses of
#                consecutive routers when multiple OSPF routers are created.
#                The default increment is 1.
#
#    -intf_prefix_length
#                Specifies the prefix length on the emulated router, Possible
#                values for IPv4 addresses range from 1 to 32; the default is
#                24, Possible values for IPv6 addresses range from 1 to 128;
#                the default is 64,
#
#    -lsa_retransmit_delay
#                Specifies the number of seconds between retransmission of
#                unacknowledged link state updates. Possible values range
#                from 1 to 65535. The default is 5.
#
#    -md5_key_id    (OSPFv2 only) Specifies the MD5 key ID to use for MD5
#                authentication mode. To use this argument, you must specify
#                -authentication_mode MD5. Possible values range from 1
#                to 255. The default is 1.
#
#    -mode        Specifies the action to be performed. Possible values are
#                create, modify, delete, disable, and enable. The modes are
#                described below:
#
#                create - Creates an emulated router. Use the -port_handle
#                    argument to specify the associated port.
#
#                modify - Changes the configuration for the OSPF router
#                    specified in the -handle argument.
#
#                delete - Deletes the OSPF router specified in the -handle
#                    argument.
#
#                disable - Stops the OSPF router specified in the -handle
#                    argument.
#
#                enable - Starts the OSPF router specified in the -handle.
#
#    -network_type    Indicates the type of network for the interface. Possible
#                values are:
#
#                broadcast - Indicates that the network is a broadcast
#                    network, as in an Ethernet connection. This is the
#                    default.
#
#                ptop - Point-to-point (PTOP). A network formed by a
#                    point-to-point link between two routers.
#
#    -option_bits    A bit mask that specifies the settings of the Options field
#                in Hello packets sent to the DUT. The Options field
#                describes the optional OSPF capabilities of the router.
#                Section A.2 in RFC 2328 describes the Options field for
#                OSPFv2; Section A.2 in RFC 2740 describes the Options field
#                for OSPFv3.
#
#                Use hexadecimal for this value. The default for OSPFv2 is
#                0x02, which sets the E-bit (binary 00000010). The default
#                for OSPFv3 is 0x13.
#
#                The value specified for this argument overwrites the initial
#                value specified by the -area_type and -demand_circuit
#                arguments:
#
#                V6: 0x01:    If this bit is clear, the router/link should be
#                        excluded from IPv6 routing calculations.
#
#                E: 0x02:    This bit describes whether or not AS-external-LSAs
#                        are flooded.  When this bit is set, the area type
#                        is external_capable; when this bit is cleared, the
#                        area type is stub.
#
#                MC: 0x04:    This bit describes whether IP multicast datagrams
#                        are forwarded.
#
#                NP: 0x08: This bit describes the handling of Type-7 LSAs.
#
#                EA: 0x10: This bit describes the router's willingness to
#                        receive and forward External-Attributes-LSAs. Used
#                         only for OSPFv2 sessions.
#
#                R: 0x10:     This bit indicates if the originator is an active
#                        router.
#
#                DC: 0x20: This bit describes the router's handling of demand
#                        circuits.
#
#                O: 0x40:     This bit describes the router's willingness to
#                        exchange Opaque LSAs. Used only for OSPFv2
#                        sessions.
#
#    -password        (OSPFv2 only) Assigns a password that is used by neighboring
#                OSPF routers on an area that is using OSPF's simple password
#                authentication. The default is "Spirent". To use this
#                argument, you must specify -authentication_mode simple.
#
#    -port_handle    Specifies the port on which to create the OSPF router.
#
#    -router_id    Identifies the emulated router. The router ID is a 32-bit
#                value, represented in dot notation. (It is not an IP
#                address.) The default is 192.85.1.3.
#
#    -router_id_step
#                The step size is the increment used to assign IDs to
#                routers. Use the -router_id_step argument along with the
#                -router_id and -count arguments to create routers on the
#                interface. You must specify a step value when the -count
#                value is greater than 1.
#
#    -router_priority
#                Sets the priority for the emulated router. OSPF routers use
#                the priority to elect the designated and back-up designated
#                routers. If you do not want the router to act as a
#                designated router, set this value to 0. The default is 0
#                for broadcast and NBMA networks. For other networks, this
#                argument is ignored. For OSPFv2 sessions, if designated
#                routers are not supported, this value is always 0. Possible
#                values are 0 to 255.
#
#    -session_type    Specifies the OSPF version to be emulated. Possible values
#                are ospfv2 or ospfv3. The default is ospfv2.
#
#    -te_admin_group
#                (OSPFv2 only) Specifies the administrative group of the
#                traffic engineering link. Possible values range from 1 to
#                4294967295. The default is 1.
#
#    -te_enable    (OSPFv2 only) Enables or disables traffic engineering (TE)
#                on all links. Possible values are 0 and 1. The default is 0
#                (disable). RFC 3630 defines the traffic engineering
#                extension for OSPF. It introduces the concept of the TE LSA
#                - an LSA that includes link resource information.
#
#                TE LSA information is confined to the description of a
#                single area. TE LSAs are originated when LSA contents
#                change, and during LSA refresh and other OSPF mandated
#                events. When a router receives a changed TE LSA or a changed
#                Network LSA, the router updates its traffic engineering
#                database.
#
#    -te_max_bw    (OSPFv2 only) Specifies the maximum bandwidth that can be
#                used on the traffic engineering link. Possible values
#                range from 0 to the maximum float number. The default is
#                100000 bytes per second.
#
#    -te_max_resv_bw
#                (OSPFv2 only) Specifies the maximum bandwidth that may be
#                reserved on the traffic engineering link. Possible values
#                range from 0 to the maximum float number. The default is
#                100000 bytes per second.
#
#    -te_metric    (OSPFv2 only) Specifies the link metric for traffic
#                engineering purposes. Possible values range from 0 to the
#                maximum float number. . The default is 1.
#
#    -te_unresv_bw_priority0
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 0. The values corresponds to the
#                bandwidth that can be reserved with a setup priority of 0
#                through 7. Arranged in ascending order, priority 0 occurs at
#                the start of the sub-TLV and priority 7 at the end. The
#                initial values, before any bandwidth is reserved, are all
#                set to the value specified for the maximum reservable
#                bandwidth (-te_max_resv_bw). Each value will be less than or
#                equal to the maximum reservable bandwidth. The default is
#                100000 bytes per second.
#
#    -te_unresv_bw_priority1
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 1. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority2
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 2. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority3
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 3. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority4
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 4. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority5
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 5. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority6
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 6. The default is 100000 bytes
#                per second.
#
#    -te_unresv_bw_priority7
#                (OSPFv2 only) Specifies the amount of bandwidth not yet
#                reserved at priority level 7. The default is 100000 bytes
#                per second.
#
#    -vlan_id        The VLAN ID of the first VLAN sub-interface. Possible values
#                range from 0 to 4095. The default is 1.
#
#    -vlan_id_mode
#                For multiple neighbor configurations, configures the VLAN ID
#                mode to "fixed" or "increment." If you set this argument to
#                "increment," then you must also specify the -vlan_id_step
#                argument to indicate the step size.
#
#     -vlan_id_step
#                The step size by which the VLAN value is incremented when
#                you set -vlan_id_mode to "increment." Possible values range
#                from 1 to 4094. You must specify the step when the -count
#                argument is greater than 1.
#
#    -vlan_user_priority
#                VLAN priority for the VLANs on this port. Possible values
#                range from 0 to 7. The default is 1.
#
#
# Return Values: The function returns a keyed list using the following keys
#            (with corresponding data):
#
#    handle        The handle(s) of the OSPF router returned by the
#                emulation_ospf_config function when you use -mode
#                create to create a new OSPF router. When you want to modify
#                or delete the OSPF router, you specify the handle as the
#                value to the -handle argument.
#
#    status         Success (1) or failure (0) of the operation.
#
#    log            An error message (if the operation failed).
#
# Description: The sth::emulation_ospf_config function creates, enables,
#    modifies, deletes, or disables an emulated OSPF router. Use the -mode
#    argument to specify the action to perform. (See the -mode argument
#    description for information about the actions.)
#
#    When you create an OSPF emulated router, use the -port_handle argument to
#    specify the Spirent TestCenter port that the emulated router will use for
#    OSPF communication. (The port handle value is contained in the keyed list
#    returned by the connect function.)
#
#    In addition to specifying the port handle (-port_handle), you must also
#    provide the following arguments when you create an OSPF router:
#
#    -intf_ip_addr
#
#    -mode create
#
#    -router_id
#
#    -area_type
#
#    -area_id
#
#    -network_type
#
#    When you create an OSPF router, Spirent TestCenter creates the router in
#    memory and downloads the configuration to the card. To start the router,
#    use the emulation_ospf_control function with -mode start. OSPF
#    communication begins with a discovery phase in which routers transmit Hello
#    packets to identify themselves. Through the reception of Hello packets from
#    other routers, a router discovers its neighbors. Two routers become
#    neighbors by agreeing on the following criteria:
#
#    - The connecting interfaces of the router are in the same area (Area ID)
#    - The routers use the same type of authentication
#    - How often they will exchange Hello packets to maintain the neighbor
#      relationship
#    - How long they will wait to hear from a neighbor before it is declared
#      dead
#    - The Stub Area Flag
#
#    On point-to-point and broadcast networks, the router discovers neighbors by
#    sending Hello packets to the IP multicast address 224.0.0.5. On broadcast
#    and non-broadcast, multi-access (NBMA) networks the Hello Protocol also
#    elects a Designated Router (DR).
#
#    Once you start sessions, Spirent TestCenter handles all of the message
#    traffic for the emulated routers. During the test, use the
#    sth::emulation_ospf_control function to stop and re-start individual
#    routers. After you have created the routers for your test, use the
#    sth::emulation_ospf_lsa_config function to set up link state
#    advertisements.
#
#
# Examples: The following example creates an OSPFv2 router on the
#    specified port:
#
#    ::sth::emulation_ospf_config  \
#        -port_handle 64 \
#        -area_id 113.1.1.1 \
#        -area_type stub \
#        -count 1 \
#        -dead_interval 200 \
#        -demand_circuit 1 \
#        -intf_ip_addr 111.100.0.1 \
#        -intf_ip_addr_step 1 \
#        -router_id 111.2.2.2 \
#        -router_id_step 10 \
#        -session_type ospfv2 \
#        -mode create
#
#    The above example produced the following output:
#
#    {handles 122} {keyedhandles {{111 {{100 {{0 {{1 122}}}}}}}}}
#    {status 1}
#
# The following example creates an OSPFv3 router on the specified
# port:
#
#    ::sth::emulation_ospf_config \
#        -port_handle 64 \
#        -area_id 113.1.1.1 \
#        -area_type stub \
#        -count 1 \
#        -dead_interval 200 \
#        -demand_circuit 1 \
#        -intf_ip_addr FE01::113 \
#        -intf_ip_addr_step 1 \
#        -router_id 113.2.2.2 \
#        -router_id_step 10 \
#        -session_type ospfv3 \
#        -mode create
#
#    The above example produced the following output:
#
#    {handles 182} {keyedhandles {{FE01::113 182}}} {status 1}
#
# Sample Input: See Examples.
#
# Sample Output: See Examples.
#
# Notes:
#          1) OSPFv3 interfaces are per link instead of per IPv6 subnet. Two
#            nodes can "talk OSPF" directly over a single link even if they do
#            not share a common IPv6 subnet.
#
#          2)    IPv6 addresses are not present in packets, except in prefix LSA
#            packets (Inter-Area Prefix LSAs and Intra-Area Prefix LSAs).
#
#          3)    In OSPFv3, neighboring routers are always identified by router
#            ID. In OSPFv2, neighbors on broadcast and NBMA networks are
#            identified by IPv4 addresses.
#
#          4)    In OSPFv3,router and network LSAs do not contain network
#            prefixes. New prefix LSAs have "referenced" fields that determine
#            which router or network LSA they are advertising prefixes on
#            behalf of.
#
#          5)    OSPFv3 is enabled at the port level.
#
#
# End of Procedure Header
proc ::sth::emulation_ospf_config {args} {
    ::sth::sthCore::Tracker ::emulation_ospf_config $args
    ::sth::sthCore::log hltcall "User executed ::sth::emulation_ospf_config $args"
    variable returnKeyedList
    set returnKeyedList ""
    set ospfHandlesList {}

    set retVal [catch {
        if {[set idx [lsearch $args -mode]] < 0} {
            ::sth::sthCore::processError returnKeyedList "Error: Required switch -mode not provided by user" {}
            return
        }
        set mode [lindex $args [expr {$idx + 1}]]
        if {[set idx [lsearch $args -session_type]] < 0} {
            set sessionType "ospfv2"
        } else {
            set sessionType [lindex $args [expr {$idx + 1}]]
        }
        if {[string equal -nocase $mode create] || [string equal -nocase $mode enable] || [string equal -nocase $mode activate]} {
            if {[string equal -nocase $sessionType ospfv2]} {
                set procPrefix "emulation_ospfv2_config"
            } elseif {[string equal -nocase $sessionType ospfv3]} {
                set procPrefix "emulation_ospfv3_config"
            } else {
               ::sth::sthCore::processError returnKeyedList \
                   [concat "Error: Unknown session type \"$sessionType\".  " \
                         "Should be \"ospfv2\" or \"ospfv3\".  "] {}
               return
            }
        } elseif {[string equal -nocase $mode modify] || [string equal -nocase $mode delete] || [string equal -nocase $mode disable] || [string equal -nocase $mode active] || [string equal -nocase $mode inactive]} {
            #added to change the input Router objecthandle to OspfRouterConfig object handle
            if {[set handle_idx [lsearch $args -handle]] < 0} {
                ::sth::sthCore::processError returnKeyedList "Error: Required switch -handle not provided by user for mode $mode" {}
                return
            }
            set routerHandle [lindex $args [expr {$handle_idx + 1}]]
            if {[set idx [lsearch $args -session_type]] >= 0} {
                if {[string equal -nocase $sessionType ospfv2]} {
                    set ospfRouterObj "Ospfv2RouterConfig"
                } elseif {[string equal -nocase $sessionType ospfv3]} {
                    set ospfRouterObj "Ospfv3RouterConfig"
                } else {
                   ::sth::sthCore::processError returnKeyedList \
                       [concat "Error: Unknown session type \"$sessionType\".  " \
                             "Should be \"ospfv2\" or \"ospfv3\".  "] {}
                   return
                }
                set ospfHandle [::sth::sthCore::invoke "stc::get $routerHandle -children-$ospfRouterObj"]
            } else {
                #keep the origin codes in case the customers doesn't input the session_type to distinguish the ospf version in their existing scripts
                set ospfHandle [::sth::sthCore::invoke "stc::get $routerHandle -children-Ospfv2RouterConfig"]
                if { $ospfHandle == "" } {
                    set ospfHandle [::sth::sthCore::invoke "stc::get $routerHandle -children-Ospfv3RouterConfig"]
                }
            }
            if { $ospfHandle == "" } {
                ::sth::sthCore::processError returnKeyedList "Error: Provided router handle $routerHandle does not have a \
                OspfvRouterConfig " {}
                return
            }
            set args [lreplace $args [expr {$handle_idx + 1}] [expr {$handle_idx + 1}] $ospfHandle]
            #end--added to change the input Router objecthandle to OspfRouterConfig object handle

            if {[string match -nocase "ospfv2routerconfig*" $ospfHandle ]} {
                set procPrefix "emulation_ospfv2_config"
            } elseif {[string match -nocase "ospfv3routerconfig*" $ospfHandle]} {
                set procPrefix "emulation_ospfv3_config"
            } else {
                ::sth::sthCore::processError returnKeyedList "Error: Provided handle $ospfHandle is not of type \
                    Ospfv2RouterConfig or Ospfv3RouterConfig. It is of type $ospfRouter" {}
                return
            }
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: Provided mode value $mode is invalid" {}
            return
        }

        if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: $procPrefix userArgsArray sortedSwitchPriorityList} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
            return
        }

        if {($mode != "create") && ($mode != "enable")} {

            foreach elem $sortedSwitchPriorityList {
                set switchName [lindex $elem 1]
                set newUserArgsArray($switchName) $userArgsArray($switchName)
            }

            unset userArgsArray
            array set userArgsArray [array get newUserArgsArray]
        } else {
            unset userArgsArray(optional_args)
            unset userArgsArray(mandatory_args)
        }


        switch $userArgsArray(mode) {
            create -
            enable {
                if {[info exists userArgsArray(port_handle)]} {
                    set userArgsArray(mode) create
                    if {![info exists userArgsArray(session_type)]} {
                       set userArgsArray(session_type) $sessionType
                       lappend userArgsArray(optional_args) "session_type" $sessionType
                    }
                    if {![info exists userArgsArray(intf_ip_addr)]} {
                       switch -exact -- $sessionType {
                          "ospfv2" {
                             set userArgsArray(intf_ip_addr) "192.85.1.3"
                          }
                          "ospfv3" {
                             set userArgsArray(intf_ip_addr) "0:0:0:0:0:0:0:0"
                          }
                       }
                    }
                } elseif {[info exists userArgsArray(handle)]} {
                    set userArgsArray(mode) create
                    #puts "Pleasse be noted OSPF protocol will be enable in the Device $userArgsArray(handle)"
                } else {
                    ::sth::sthCore::processError returnKeyedList "Error: port_handle or handle must be provided by user for -mode create" {}
                    return
                }
            }
			activate -
            modify -
            active -
            inactive {
            }
            delete -
            disable {
            # redirect to delete
                set userArgsArray(mode) delete
            }
            # this is not necessary since parse_dashed_args makes sure that the
            # correct switch values are provided by the user
            # keep it, it might be needed in the future
            default {
                ::sth::sthCore::processError returnKeyedList "Error: $userArgsArray(mode) is not a supported -mode value" {}
                return
            }
        }
        
        set cmd "::sth::ospf::emulation_ospf_config_$userArgsArray(mode) userArgsArray sortedSwitchPriorityList $procPrefix"

        if {[catch {set ret [eval $cmd]} err]} {
            ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
            return
        }

        if {$ret == $::sth::sthCore::FAILURE} {
            ::sth::sthCore::log error "Evaluating $cmd Failed: $err"
            return
        }

        if {![string equal -nocase $userArgsArray(mode) activate]} {
            keylset returnKeyedList session_router $ospfHandlesList
        }
        set RouterHandles ""
        foreach handle $ospfHandlesList {
           lappend RouterHandles [::sth::sthCore::invoke stc::get $handle -parent]
        }
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList handle $RouterHandles]
        set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList handles $RouterHandles]
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
# Name: ::sth::emulation_ospf_control
#
# Purpose: Starts or stops OSPF routers.
#
# Synopsis: emulation_ospf_control
#           [ -handle { ospf_handle } -mode {stop | start | restart } ] |
#           [ -withdraw_lsa { list of lsa_handles } ]
#
# Arguments:
#    -handle        Identifies the router handle, returned from the
#                emulation_ospf_config function when creating an OSPF
#                router.
#
#    -mode        Specifies the action to be taken. Possible values are stop,
#                start, or restart the OSPF router, This argument is
#                required.
#
#                stop - Stops the OSPF router with the specified handle.
#
#                start - Starts the OSPF router with the specified handle.
#
#                restart - Stops the OSPF router with the specified handle
#                    and then starts it again. This is not a graceful
#                    restart.
#
#    -withdraw_lsa    Specifies the list of LSA handles to delete.
#
# Return Values: The function returns a keyed list using the following keys
#            (with corresponding data):
#
#        status     Success (1) or failure (0) of the operation.
#        log        An error message (if the operation failed).
#
# Description: The emulation_ospf_control function controls the starting and
#    stopping of OSPF routers as well as deleting LSAs.
#
# Examples:
#    To start an OSPF router:
#
#        ::sth::emulation_ospf_control -mode start -handle 174
#
#    To stop an OSPF router:
#
#         ::sth::emulation_ospf_control -mode stop -handle 174
#
#     To restart an OSPF router:
#
#         ::sth::emulation_ospf_control -mode restart -handle 174
#
# Sample Input: See Examples.
#
# Sample Output:  {status 1}
#
# Notes:
#           1) Graceful restart is not available for this function.
#
#           2) You can specify either the -mode or -withdraw_lsa argument but
#            not both.
#
# End of Procedure Header
proc ::sth::emulation_ospf_control {args} {
    ::sth::sthCore::Tracker ::emulation_ospf_control $args

    ::sth::sthCore::log hltcall "User executed ::sth::emulation_ospf_control $args"

    variable returnKeyedList
    set returnKeyedList ""
    set ospfHandlesList {}

    set retVal [catch {
        ::sth::sthCore::Tracker ::sth::emulation_ospf_control $args
        #added to change iniput Router object handle to OspfRouterConfig object handle
        if {[set handle_idx [lsearch $args -handle]] > -1} {
            #check if there is a list input for -handle
            set handle_value_idx [expr $handle_idx + 1]
            set arg_value [lindex $args $handle_value_idx]
            set routerHandleList $arg_value
            set handle_next_idx [expr $handle_value_idx + 1]
            for {set i $handle_next_idx} {$i < [llength $args]} {incr i} {
                set arg_next [lindex $args $i]
                if {$arg_next!= "" && ![regexp ^- $arg_next]} {
                    lappend routerHandleList $arg_next
                } else {
                    break
                }
            }
            set index_end [expr $i - 1]
            set ospfHandleList ""
            foreach routerHandle $routerHandleList {
                #Get both the ospfv2 and ospfv3 when the two session are configured on the same device to make sure both the control command can perform on the two sassion.
                if {[catch {set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv2RouterConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv2routerconfig from router $routerHandle" {}
                    return
                }

                if {[catch {set ospfv3Handle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv3RouterConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv3routerconfig from router $routerHandle" {}
                    return
                }

                if { $ospfHandle == "" && $ospfv3Handle == ""} {
                    ::sth::sthCore::processError returnKeyedList "Error: Provided router handle $routerHandle does not have a \
                    OspfvRouterConfig object" {}
                    return
                }
                if { $ospfHandle != ""} {
                    lappend ospfHandleList $ospfHandle
                }
                if { $ospfv3Handle != ""} {
                    lappend ospfHandleList $ospfv3Handle
                }
            }
            set args [lreplace $args [expr {$handle_idx + 1}] $index_end $ospfHandleList]
            #end--added to change iniput Router object handle to OspfRouterConfig object handle
        }
        if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: emulation_ospfv2_control userArgsArray sortedSwitchPriorityList} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
            return
        }
        #delete unecessary elements from the array
        unset userArgsArray(optional_args)
        unset userArgsArray(mandatory_args)
        if {[info exists userArgsArray(withdraw_lsa)]} {
            set withdrawLsaValue $userArgsArray(withdraw_lsa)
            set cmd "::sth::ospf::emulation_ospf_control_withdraw_lsa userArgsArray"
            if {[catch {set ret [eval $cmd] } err] } {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
                return
            }
            if {$ret == $::sth::sthCore::FAILURE} {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err"
                return
            }
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return
        }
        if {[info exists userArgsArray(readvertise_lsa)]} {
            set cmd "::sth::ospf::emulation_ospf_control_readvertise_lsa userArgsArray"

            if {[catch {set ret [eval $cmd] } err] } {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
                return
            }
            if {$ret == $::sth::sthCore::FAILURE} {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err"
                return
            }
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return
        }
        if {[info exists userArgsArray(age_lsa)]} {
            set cmd "::sth::ospf::emulation_ospf_control_age_lsa userArgsArray"
            if {[catch {set ret [eval $cmd] } err] } {
                ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
                return
            }
            if {$ret == $::sth::sthCore::FAILURE} {
                ::sth::sthCore::log error "Evaluating $cmd Failed: $err"
                return
            }
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
            return
        }
        if {[info exists userArgsArray(mode)]} {
            set modeValue $userArgsArray(mode)
        } else {
            ::sth::sthCore::processError returnKeyedList "Error: Neither -mode nor -withdraw_lsa were provided by user" {}
            return
        }
        switch $modeValue {
            stop -
            start -
            restart {
                if { ![info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)] } {
                    ::sth::sthCore::processError returnKeyedList "Neither port_handle nor handle were provided by user" {}
                    return
                }
                set cmd "::sth::ospf::emulation_ospf_control_$modeValue userArgsArray"
            }
            stop_hellos -
            resume_hellos -
            restore -
            shutdown -
            advertise -
            establish {
                #raise an error if neither port_handle nor handle exist in the user arguments
                if { ![info exists userArgsArray(handle)] && ![info exists userArgsArray(port_handle)] } {
                    ::sth::sthCore::processError returnKeyedList "Neither port_handle nor handle were provided by user" {}
                    return
                }
                set cmd "::sth::ospf::emulation_ospf_control_common userArgsArray"
            }
            flap {
               if {![info exists userArgsArray(handle)] && \
                   ![info exists userArgsArray(port_handle)]} {
                  ::sth::sthCore::processError returnKeyedList \
                        [concat "Error:  Unable to execute flap command.  " \
                           "Neither \"port_handle\" nor \"handle\" were " \
                           "provided.  "] {}
                  return
                }
                if {![info exists userArgsArray(flap_lsa)] && \
                    ![info exists userArgsArray(flap_routes)]} {
                   ::sth::sthCore::processError returnKeyedList \
                        [concat "Error:  Unable to execute flap command.  " \
                           "Neither \"flap_lsa\" nor \"flap_routes\" were " \
                           "provided.  "] {}
                   return
                }
                if {[info exists userArgsArray(flap_lsa)]} {
                   set cmd [list ::sth::ospf::emulation_ospf_control_flap_lsa \
                         userArgsArray \
                         returnKeyedList]
                }
            }
            default {
                ::sth::sthCore::processError returnKeyedList "Error: $modeValue is not a valid -mode value" {}
                return
            }
        }
        if {[catch {set ret [eval $cmd]} err]} {
            ::sth::sthCore::processError returnKeyedList "Evaluating $cmd Failed: $err" {}
            return
        }
    } returnedString]

    if {$retVal} {
        if {$returnedString ne ""} {
            ::sth::sthCore::processError returnKeyedList $returnedString {}
        }
    } else {
        if {![keylget returnKeyedList status mystatus]} {
            keylset returnKeyedList status $::sth::sthCore::SUCCESS
        }
    }
    return $returnKeyedList
}

#
##Procedure Header
#
# Name:
#    sth::emulation_ospfv2_info
#
# Purpose:
#    This function is a Spirent Extension created to return statistical
#    information about the OSPFv2 configuration.
#
# Synopsis:
#    sth::emulation_ospfv2_info
#         -handle <port_handle>
#
# Arguments:
#    -handle
#                   Specifies one or more ports from which to gather transmitted
#                   (tx) and received (rx) statistics. This argument is
#                   mandatory.
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null.
#
#    The following keys are returned:
#
#         rx_ack
#                        Received Acks - Number of Link State Acknowledgment
#                        packets received by the emulated router
#
#         rx_router_asbr
#                        Received ASBR-Summary-LSAs - Number of ASBR-Summary-
#                        LSAs received by the emulated router
#
#         rx_asexternal_lsa
#                        Received External-LSAs - Number of External LSAs
#                        received by the emulated router
#
#         rx_dd
#                        Received DD - Number of Database Description packets
#                        (containing LSA headers) received by the emulated
#                        router
#
#         rx_hello
#                        Received Hellos - Number of Hello packets received by
#                        the emulated router
#
#         rx_network_lsa
#                        Received Network-LSAs - Number of Network LSAs received
#                        by the emulated router
#
#         rx_nssa_lsa
#                        Received NSSA-LSAs - Number of NSSA LSAs received by
#                        the emulated router
#
#         rx_request
#                        Received Requests - Number of LS Request packets
#                        received by the emulated router
#
#         rx_router_lsa
#                        Received Router-LSAs - Number of Router LSAs received
#                        by the emulated router
#
#         rx_summary_lsa
#                        Received Summary-LSAs - Number of Summary LSAs received
#                        by the emulated router
#
#         rx_te_lsa
#                        Received TE-LSAs - Number of TE-LSAs received by the
#                        emulated router
#
#         tx_ack
#                        Sent Acks - Number of Link State Acknowledgment packets
#                        sent by the emulated router
#
#         tx_asbr_summry_lsa
#                        Sent ASBR-Summary-LSAs - Number of ASBR-Summary LSAs
#                        sent by the emulated router
#
#         tx_as_external_lsa
#                        Sent External-LSAs - Number of External LSAs sent by
#                        the emulated router
#
#         tx_dd
#                        Sent DD - Number of Database Description packets sent
#                        by the emulated router
#
#         tx_hello
#                        Sent Hellos - Number of Hello packets sent by the
#                        emulated router
#
#         tx_network_lsa
#                        Sent Network-LSAs - Number of Network LSAs sent by the
#                        emulated router
#
#         tx_nssa_lsa
#                        Sent NSSA-LSAs - Number of NSSA LSAs sent by the
#                        emulated router
#
#         tx_request
#                        Sent Requests - Number of LS Request packets sent by
#                        the emulated router
#
#         tx_router_lsa
#                        Sent Router-LSAs - Number of Router LSAs sent by the
#                        emulated router
#
#         tx_summary_lsa
#                        Sent Summary-LSAs - Number of Summary LSAs sent by the
#                        emulated router
#
#         tx_te_lsa
#                        Sent TE-LSAs - Number of TE-LSAs sent by the emulated
#                        router
#
# Description:
#    The sth::emulation_ospfv2_info function provides information about the
#    statistics returned by the OSPFv2 configuration. The default return value
#    for each statistic is 0.
#
#    This function returns the statistics for the specified handle and a status
#    value (1 for success). If there is an error, the function returns the
#    status value (0) and an error message. Function return values are formatted
#    as a keyed list (supported by the Tcl extension software - TclX). Use the
#    TclX function keylget to retrieve data from the keyed list. (See Return
#    Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input:
#    ::sth::emulation_ospfv2_info -handle $ospfv2Router(1)
#
# Sample Output:
#    {tx_summary_lsa 2.000000}  {status 1}
#
# Notes:
#    None
#
# End of Procedure Header
#
#
proc ::sth::emulation_ospfv2_info { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ospfv2_info $args
    set returnKeyedList ""
    set retVal [catch {
        variable userArgsArray
        array set userArgsArray {};
        variable sortedSwitchPriorityList {};
        variable ::sth::sthCore\::SUCCESS
        variable ::sth::sthCore::FAILURE
        set cmdName "emulation_ospfv2_info"

        ::sth::sthCore::log debug "{Calling ::sth::emulation_ospfv2_info}"

        if {[set modeVal_idx [lsearch $args -mode]] < 0} {
            set modeVal "stats"
        } else {
            set modeVal [lindex $args [expr {$modeVal_idx + 1}]]
        }
        if { $modeVal == "clear_stats" } {
            if {[catch {::sth::sthCore::invoke stc::perform ResultsClearRouting -ProtocolList "Ospfv2"} err ] } {
                        ::sth::sthCore::processError returnKeyedList "stc::Perform ResultsClearRouting -ProtocolList Ospfv2 Failed: $err"
                        set cmdFailed 0
                }
        } else {
            ::sth::sthCore::log info "{Generating Ospfv2 stats table}"

            #added to change the input Router objecthandle to OspfRouterConfig object handle
            if {[set handle_idx [lsearch $args -handle]] < 0} {
                ::sth::sthCore::processError returnKeyedList "Error: Required switch -handle not provided by user for mode $mode" {}
                return
            }

            set routerHandles [lindex $args [expr {$handle_idx + 1}]]
            foreach routerHandle $routerHandles {
                if {[catch {set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv2RouterConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv2routerconfig from router $routerHandle" {}
                    return
                }

                if { $ospfHandle == "" } {
                    ::sth::sthCore::processError returnKeyedList "Error: Provided router handle $routerHandle does not have a \
                    OspfvRouterConfig object" {}
                    return
                }

                set args [lreplace $args [expr {$handle_idx + 1}] [expr {$handle_idx + 1}] $ospfHandle]
                #end--added to change the input Router objecthandle to OspfRouterConfig object handle

                if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: emulation_ospfv2_info userArgsArray sortedSwitchPriorityList} err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
                    return
                }

                if {[info exists userArgsArray(handle)]} {
                    set ospfv2RouterHandle $userArgsArray(handle)
                    if {![::sth::ospf::IsOspfRouterHandleValid $ospfv2RouterHandle msg]} {
                        ::sth::sthCore::processError returnKeyedList "The handle $ospfv2RouterHandle is not a valid handle of RSVP router" {}
                        return
                    } else {
                        set cmdResult [::sth::ospf::getOspfCounters $ospfv2RouterHandle "ospfv2RouterResults"]
                    }
                }

                if {$cmdResult == 0} {
                    set cmdFailed 0
                }
            }
        }
        if {[::info exists cmdFailed]} {
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 0]
            return
        } else {
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 1]
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

#
##Procedure Header
#
# Name:
#    sth::emulation_ospfv3_info
#
# Purpose:
#    This function is a Spirent Extension created to return statistical
#    information about the OSPFv3 configuration.
#
# Synopsis:
#    sth::emulation_ospfv3_info
#         -handle <port_handle>
#
# Arguments:
#    -handle
#                   Specifies one or more ports from which to gather transmitted
#                   (tx) and received (rx) statistics. This argument is
#                   mandatory..
#
# Return Values:
#    The function returns a keyed list using the following keys
#    (with corresponding data):
#
#         status         Retrieves a value indicating the success (1) or failure
#                        (0) of the operation.
#
#         log            Retrieves a message describing the last error that
#                        occurred during the operation. If the operation was
#                        successful - {status 1} - the log value is null.
#
#    The following keys are returned:
#
#         rx_ack
#                        Received acks - Number of Link State Acknowledgment
#                        packets received by the emulated router
#
#         rx_asexternal_lsa
#                        Received external-LSAs - Number of external LSAs
#                        received by the emulated router
#
#         rx_dd
#                        Received DD - Number of Database Description
#                        packets (containing LSA headers) received by the
#                        emulated router
#
#         rx_hello
#                        Received Hellos - Number of Hello packets received by
#                        the emulated router
#
#         rx_inter_area_prefix_lsa
#                        Received inter-area-prefix LSAs - Number of inter-
#                        area-prefix LSAs received by the emulated router
#
#         rx_inter_area_router_lsa
#                        Received inter-area-router LSAs - Number of inter-
#                        area-router LSAs received by the emulated router
#
#         rx_intra_area_prefix_lsa
#                        Received Intra-Area-Prefix-LSAs - Number of Intra-Area-
#                        Prefix LSAs received by the emulated router
#
#         rx_link_lsa
#                        Received link-LSAs - Number of Ilink LSAs received by
#                        the emulated router.
#
#         rx_network_lsa
#                        Received Network-LSAs - Number of Network LSAs received
#                        by the emulated router
#
#         rx_nssa_lsa
#                        Received Link-LSAs - Number of Link LSAs received by
#                        the emulated router
#
#         rx_router_lsa
#                        Received Router-LSAs - Number of Router LSAs received
#                        by the emulated router
#
#         tx_ack
#                        Sent acks - Number of Link State Acknowledgment
#                        packets sent by the emulated router
#
#         tx_as_external_lsa
#                        Sent external-LSAs - Number of external LSAs sent by
#                        the emulated router
#
#         tx_dd
#                        Sent DD - Number of Database Description packets sent
#                        by the emulated router
#
#         tx_hello
#                        Sent Hellos - Number of Hello packets sent by the
#                        emulated router
#
#         tx_inter_area_prefix_lsa
#                        Sent inter-area-prefix LSAs - Number of inter-area-
#                        prefix LSAs sent by the emulated router
#
#         tx_inter_area_prefix_lsa
#                        Sent inter-area-router LSAs - Number of inter-area-
#                        router LSAs sent by the emulated router
#
#         tx_intra_area_prefix_lsa
#                        Sent Intra-Area-Prefix-LSAs - Number of Intra-Area-
#                        Prefix LSAs sent by the emulated router
#
#         tx_link_lsa
#                        Sent link-LSAs - Number of link LSAs sent by the
#                        emulated router.
#
#         tx_network_lsa
#                        Sent Network-LSAs - Number of Network LSAs sent by the
#                        emulated router
#
#         tx_nssa_lsa
#                        Sent NSSA-LSAs - Number of NSSA LSAs sent by the
#                        emulated router
#
#         tx_request
#                        Sent requests - Number of LS request packets sent by
#                        the emulated router
#
#         tx_router_lsa
#                        Sent Router-LSAs - Number of Router LSAs sent by the
#                        emulated router
#
# Description:
#    The sth::emulation_ospfv3_info function provides information about the
#    statistics returned by the OSPFv3 configuration.
#
#    This function returns the statistics for the specified handle and a status
#    value (1 for success). If there is an error, the function returns the
#    status value (0) and an error message. Function return values are formatted
#    as a keyed list (supported by the Tcl extension software - TclX). Use the
#    TclX function keylget to retrieve data from the keyed list. (See Return
#    Values for a description of each key.)
#
# Examples: See Sample Input and Sample Output below.
#
# Sample Input:
#    ::sth::emulation_ospfv3_info -handle $ospfv3Router(1)
#
# Sample Output:
#     { tx_hello 59.000000}  {status 1}
#
# Notes:
#    None
#
# End of Procedure Header
#
#
proc ::sth::emulation_ospfv3_info { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ospfv3_info $args

    set returnKeyedList ""
    set retVal [catch {
        variable userArgsArray
        array set userArgsArray {};
        variable sortedSwitchPriorityList {};
        variable ::sth::sthCore\::SUCCESS
        variable ::sth::sthCore::FAILURE
        set cmdName "emulation_ospfv3_info"

        ::sth::sthCore::log debug "{Calling ::sth::emulation_ospfv3_info}"

        if {[set modeVal_idx [lsearch $args -mode]] < 0} {
            set modeVal "stats"
        } else {
            set modeVal [lindex $args [expr {$modeVal_idx + 1}]]
        }
        if { $modeVal == "clear_stats" } {
            if {[catch {::sth::sthCore::invoke stc::perform ResultsClearRouting -ProtocolList "Ospfv3"} err ] } {
                        ::sth::sthCore::processError returnKeyedList "stc::Perform ResultsClearRouting -ProtocolList Ospfv3 Failed: $err"
                        set cmdFailed 0
                }
        } else {
            ::sth::sthCore::log info "{Generating Ospfv3 stats table}"

            #added to change the input Router objecthandle to OspfRouterConfig object handle
            if {[set handle_idx [lsearch $args -handle]] < 0} {
                ::sth::sthCore::processError returnKeyedList "Error: Required switch -handle not provided by user for mode $mode" {}
                return
            }
            set routerHandles [lindex $args [expr {$handle_idx + 1}]]
            foreach routerHandle $routerHandles {
                if {[catch {set ospfHandle [::sth::sthCore::invoke stc::get $routerHandle -children-Ospfv3RouterConfig]} errMsg]} {
                    ::sth::sthCore::processError returnKeyedList "Error: can not get children object ospfv3routerconfig from router $routerHandle" {}
                    return
                }

                if { $ospfHandle == "" } {
                    ::sth::sthCore::processError returnKeyedList "Error: Provided router handle $routerHandle does not have a \
                    OspfvRouterConfig object" {}
                    return
                }

                set args [lreplace $args [expr {$handle_idx + 1}] [expr {$handle_idx + 1}] $ospfHandle]
                #end--added to change the input Router objecthandle to OspfRouterConfig object handle

                if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: emulation_ospfv3_info userArgsArray sortedSwitchPriorityList} err]} {
                    ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
                    return
                }

                if {[info exists userArgsArray(handle)]} {
                    set ospfv3RouterHandle $userArgsArray(handle)
                    if {![::sth::ospf::IsOspfRouterHandleValid $ospfv3RouterHandle msg]} {
                        ::sth::sthCore::processError returnKeyedList "The handle $ospfv3RouterHandle is not a valid handle of RSVP router" {}
                        return
                    } else {
                        set cmdResult [::sth::ospf::getOspfCounters $ospfv3RouterHandle "ospfv3RouterResults"]
                    }
                }

                if {$cmdResult == 0} {
                    set cmdFailed 0
                }
            }

        }
        if {[::info exists cmdFailed]} {
           set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 0]
            return
        } else {
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 1]
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

proc ::sth::emulation_ospf_route_info { args } {
    ::sth::sthCore::Tracker ::sth::emulation_ospf_route_info $args

    set returnKeyedList ""
    set retVal [catch {
        variable userArgsArray
        array set userArgsArray {};
        variable sortedSwitchPriorityList {};
        variable ::sth::sthCore\::SUCCESS
        variable ::sth::sthCore::FAILURE
        set cmdName "emulation_ospf_route_info"

        ::sth::sthCore::log debug "{Calling ::sth::emulation_ospf_route_info}"

        if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable $args ::sth::ospf:: emulation_ospf_route_info userArgsArray sortedSwitchPriorityList} err]} {
            ::sth::sthCore::processError returnKeyedList "::sth::sthCore::commandInit Failed: $err" {}
            return
        }

        if {[info exists userArgsArray(handle)]} {
            set ospfRouterHandles $userArgsArray(handle)
        } else {
            ::sth::sthCore::processError returnKeyedList "Missed mandatory switch -handle." {}
            return
        }
        foreach ospfRouterHandle $ospfRouterHandles {
            set cmdResult [::sth::ospf::emulation_ospf_route_info_generic $ospfRouterHandle returnKeyedList]
        }

        if { $cmdResult} {
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 1]
        } else {
            set returnKeyedList [::sth::sthCore::updateReturnInfo $returnKeyedList status 0]
            return
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


#emulation_ospf_lsa_generator (wizard implementation)
#supported modes are create and delete
proc ::sth::emulation_ospf_lsa_generator { args } {
    variable ::sth::ospf::sortedSwitchPriorityList
    ::sth::sthCore::Tracker "::sth::emulation_ospf_lsa_generator" $args
    variable ::sth::ospf::userArgsArray
    array unset ::sth::ospf::userArgsArray
    array set ::sth::ospf::userArgsArray {}

    set procName [lindex [info level [info level]] 0]
    set hltCmdName "emulation_ospf_lsa_generator"
    set returnKeyedList ""

    if {[catch {::sth::sthCore::commandInit ::sth::ospf::ospfTable\
                                                            $args\
                                                            ::sth::ospf::\
                                                            emulation_ospf_lsa_generator\
                                                            userArgsArray\
                                                            sortedSwitchPriorityList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err" {}
        return -code error $returnKeyedList
    }

    unset userArgsArray(optional_args)
    unset userArgsArray(mandatory_args)

    set modeVal create
    if {[info exists userArgsArray(mode)]} {
        set modeVal $userArgsArray(mode)
    }

    set cmd "::sth::ospf::${hltCmdName}\_$modeVal userArgsArray"
    if {[catch {eval $cmd returnKeyedList} err]} {
        ::sth::sthCore::processError returnKeyedList "Error in $procName: $err." {}
        return -code error $returnKeyedList
    }

    return $returnKeyedList
}
