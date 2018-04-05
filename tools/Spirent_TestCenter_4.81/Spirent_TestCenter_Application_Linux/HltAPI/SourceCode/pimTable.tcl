# This file contains confidential and / or privileged information belonging to Spirent Communications plc,
# its affiliates and / or subsidiaries.

namespace eval ::sth {
    set pimTable { ::sth::
        { emulation_pim_config
            { hname                         stcobj              stcattr                     type                                    priority                default         range   supported   dependency      mandatory procfunc      mode    constants }
            { bidir_capable 	        PimRouterConfig	        BiDirOptionSet	            {CHOICES 0 1}	                    100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { bs_period 	        PimRouterConfig	        BootstrapMessageInterval    NUMERIC	                            100	                    60	            1-3600	true	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_addr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_adv 	            _none_	        _none_	                    {CHOICES 0 1}	                    100	                    1	            _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_group_addr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_bsr_group_admin 	    _none_	        _none_	                    {CHOICES 0 1}	                    100	                    _none_	    _none_	false	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_bsr_group_bidir 	    _none_	        _none_	                    {CHOICES 0 1}	                    100	                    _none_	    _none_	false	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_bsr_group_prefix_len 	    _none_	        _none_	                    NUMERIC	                            100	                    _none_	    1-128	false	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_priority 	            PimRouterConfig	BsrPriority	            NUMERIC	                            100	                    192	            0-255	true	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_rp_addr 	            PimRpMap	        RpIpAddr	            IP	                                    100	                    _none_	    _none_	true	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_bsr_rp_handle 	            _none_	        _none_	                    ALPHANUM	                            100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_rp_holdtime 	    PimRpMap	        RpHoldTime	            NUMERIC	                            100	                    _none_	    _none_	true	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_bsr_rp_mode 	            _none_	        _none_	        {CHOICES create delete modify}	                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_bsr_rp_priority 	    PimRpMap	        RpPriority	            NUMERIC	                            100	                    _none_	    0-255	true	c_bsr_rp_handle	false	<procName>	_none_	_none_ }
            { c_rp_addr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_adv 	                    _none_	        _none_	                    {CHOICES 0 1}	                    100	                    1	            _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_adv_holdtime 	    _none_	        _none_	                    NUMERIC	                            100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_adv_interval 	    _none_	        _none_	                    NUMERIC	                            100	                    60	            1-3600	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_bsr_addr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_group_addr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	c_rp_group_mode	false	<procName>	_none_	_none_ }
            { c_rp_group_admin	            _none_	        _none_	                    NUMERIC	                            100	                    _none_	    _none_	false	c_rp_group_mode	false	<procName>	_none_	_none_ }
            { c_rp_group_bidir 	            _none_	        _none_	                    NUMERIC	                            100	                    _none_	    _none_	false	c_rp_group_mode	false	<procName>	_none_	_none_ }
            { c_rp_group_handle 	    _none_	        _none_	                    ALPHANUM	                            100	                    _none_	    _none_	false	c_rp_group_mode	false	<procName>	_none_	_none_ }
            { c_rp_group_mode 	            _none_	        _none_	        {CHOICES  create delete modify}	                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { c_rp_group_prefix_len 	    _none_	        _none_	                    NUMERIC	                            2	                    _none_	    1-128	false	c_rp_group_mode	false	<procName>	_none_	_none_ }
            { c_rp_priority 	            _none_	        _none_                      NUMERIC	                            100	                    192             0-255	false	_none_	        false	<procName>	_none_	_none_ }
            { count 	                Emulateddevice|Router	count	                    NUMERIC	                            100	                    1	            1-65535	true	_none_	        false	<procName>	_none_	_none_ }
            { dr_priority 	            PimRouterConfig	DrPriority	            NUMERIC	                            100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { handle 	                    _none_	        _none_	                    ALPHANUM	                            1	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { hello_holdtime 	            PimRouterConfig	HelloHoldtime	            NUMERIC	                            100	                    105	            1-65535	true	hello_interval	false	<procName>	_none_	_none_ }
            { hello_interval 	            PimRouterConfig	HelloInterval	            NUMERIC	                            100	                    30	            1-65535	true	_none_	        false	<procName>	_none_	_none_ }
            { hello_max_delay 	            PimGlobalConfig	TriggerHelloDelay	    NUMERIC	                            100	                    5	            1-65535	true	_none_	        false	<procName>	_none_	_none_ }
            { intf_ip_addr 	            Ipv4If	        Address	                    IP	                                    100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { intf_ip_addr_step 	    Ipv4If	        Address.step	            IP	                                    100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { intf_ip_prefix_len 	    Ipv4If	        PrefixLength	            NUMERIC	                            100	                    24	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            {link_local_intf_ip_addr        Ipv6If_Link_Local   Address                     IPV6                                    14                      FE80::0         _none_      TRUE    _none_          FALSE   <procName>      _none_  _none_}
            {link_local_intf_ip_addr_step   Ipv6If_Link_Local   Address.step                IPV6                                    15                      ::1             _none_      TRUE    _none_          FALSE   _none_          _none_  _none_}
            {link_local_intf_prefix_len     Ipv6If_Link_Local   PrefixLength                NUMERIC                                 16                      128             1-128       TRUE    _none_          FALSE   <procName>      _none_  _none_}
            { ip_version 	            PimRouterConfig	IpVersion	            {CHOICES 4 6}	                    100                     _none_	    _none_	true	_none_	        false	<procName>	_none_	{4 V4 6 V6} }
            { join_prune_holdtime 	    PimRouterConfig	JoinPruneHoldtime	    NUMERIC	                            100	                    180	            1-65535	true join_prune_interval false	<procName>	_none_	_none_ }
            { join_prune_interval 	    PimRouterConfig	JoinPruneInterval	    NUMERIC	                            100	                    60	            1-65535	true	_none_	        false	<procName>	_none_	_none_ }
            { keepalive_period 	            _none_	        _none_	                    NUMERIC	                            100	                    210	            _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { mode	                    _none_  _none_  {CHOICES create modify delete disable enable enable_all disable_all active inactive}    1	    _none_	    _none_	true	_none_	        true	<procName>	_none_	_none_ }
            { neighbor_intf_ip_addr 	    Ipv4If	        Gateway	                    IP	                                    100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { mac_address_start 	    EthiiIf	        SourceMac	            ANY	                                    100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { override_interval 	    PimGlobalConfig	OverrideInterval	    NUMERIC	                            100                     2500	    100-32767	true	_none_	        false	<procName>	_none_	_none_ }
            { port_handle 	            _none_	        _none_	                    ALPHANUM	                            100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { prune_delay 	            PimGlobalConfig	LanPruneDelay	            NUMERIC	                            100	                    500	            100-32767	true	_none_	        false	<procName>	_none_	_none_ }
            { prune_delay_enable 	    PimGlobalConfig	EnablingPruningDelayOption  {CHOICES 0 1}	                    100	                    0	            _none_	true	_none_	        false	<procName>	_none_	{0 false 0 FALSE 1 true 1 TRUE} }
            { register_probe_time 	    _none_	        _none_	                    NUMERIC	                            100	                    5	            1-30	false	_none_	        _none_	<procName>	_none_	_none_ }
            { register_suppression_time     _none_	        _none_	                    NUMERIC	                            100	                    60	            1-3600	false	_none_	        _none_	<procName>	_none_	_none_ }
            { router_id 	        Emulateddevice|Router	RouterId	            IP	                                    100	                    _none_	    _none_	true	_none_	        false	emulation_pim_config_router_id	_none_	_none_ }
            { router_id_step 	        Emulateddevice|Router	RouterId.step	            IP	                                    100	                    0.0.0.1	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { type	                    PimRouterConfig	EnableBsr	            {CHOICES remote_rp c_bsr}	                    100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	{remote_rp false c_bsr true} }
            { vlan_cfi 	                    VlanIf	        cfi	                    {CHOICES 0 1}	                    1	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_id 	                    VlanIf	        VlanId	                    NUMERIC	                            1	                    _none_	    0-4095	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_id_mode 	            VlanIf	        vlanid.mode	        {CHOICES fixed increment}	                    1	                    fixed	    _none_	true	_none_	        false	<procName>	_none_	{fixed fixed increment increment} }
            { vlan_id_step 	            VlanIf	        vlanid.step	            NUMERIC	                            1	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_user_priority 	    VlanIf	        Priority	            NUMERIC	                            1	                    _none_	    0-7	        true	_none_	        false	doGenericConfig	_none_	_none_ }
            { vlan_outer_cfi 	            VlanIf_Outer	cfi	                    {CHOICES 0 1}	                    1	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_outer_id 	            VlanIf_Outer	VlanId	                    NUMERIC	                            1	                    _none_	    0-4095	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_outer_id_mode 	    VlanIf_Outer	vlanid.mode	        {CHOICES fixed increment}	                    1	                    fixed	    _none_	true	_none_	        false	<procName>	_none_	{fixed fixed increment increment} }
            { vlan_outer_id_step 	    VlanIf_Outer	vlanid.step	            NUMERIC	                            1	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { vlan_outer_user_priority 	    VlanIf_Outer	Priority	            NUMERIC	                            1	                    _none_	    0-7	        true	_none_	        false	doGenericConfig	_none_	_none_ }
            { pim_mode 	                    PimRouterConfig	PimMode	                    {CHOICES sm ssm}	                    100	                    sm	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { mvpn_enable 	            _none_	        _none_	                    {CHOICES 0 1}	                    100	                    0	            _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { mvpn_pe_count 	            _none_	        _none_	                    NUMERIC	                            100	                    1	            _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { mvpn_pe_ip 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { mvpn_pe_ip_incr 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { mvrf_count 	            _none_	        _none_	                    NUMERIC	                            100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { default_mdt_ip 	            _none_	        _none_	                    IP	                                    100	                    _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { default_mdt_ip_incr 	    _none_	        _none_	                    IP	                                    100                     _none_	    _none_	false	_none_	        false	<procName>	_none_	_none_ }
            { gre_checksum_enable 	    _none_	        _none_	                    {CHOICES 0 1}	                    100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { gre_key_enable 	            _none_	        _none_	                    NUMERIC	                            100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { gre_key_in 	            _none_	        _none_	                    NUMERIC	                            100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { gre_key_out	            _none_	        _none_	                    NUMERIC	                            100	                    0	            _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { tunnel_handle	            _none_	        _none_	                    ANY                                     100	                    _none_	    _none_	true	_none_	        false	<procName>	_none_	_none_ }
            { vci                           Aal5If              vci                         NUMERIC                                 100                     _none_          0-65535     false   _none_          false   <procName>     _none_    _none_}
            { vci_step                      _none_              _none_                      NUMERIC                                 100                     _none_          0-65535     false   _none_          false   <procName>     _none_    _none_}
            { vpi                           Aal5If              vpi                         NUMERIC                                 100                     _none_          0-255       false   _none_          false   <procName>     _none_    _none_}
            { vpi_step                      _none_              _none                       NUMERIC                                 100                     _none_          0-255       false   _none_          false   <procName>     _none_    _none_} 
        }
        { emulation_pim_control
            { hname                      stcobj              stcattr                 type                        priority    default     range   supported   dependency  mandatory      procfunc        mode    constants }
            { group_member_handle 	GroupList	PimGroupCommand	            ALPHANUM	                    100	    _none_	_none_	    true	_none_	    false	<procName>	_none_	_none_ }
            { handle 	                _none_	            _none_	            ALPHANUM	                    100	    _none_	_none_	    true	_none_	    false	<procName>	_none_	_none_ }
            { mode	                _none_	            _none_  {CHOICES start stop restart join prune}	    100	    _none_	_none_	    true	_none_	    true	<procName>	_none_	_none_ }
            { port_handle 	        _none_	            _none_	            ALPHANUM	                    100	    _none_	_none_	    true	_none_	    false	<procName>	_none_	_none_ }
        }
        { emulation_pim_group_config
            { hname                             stcobj          stcattr     type                                        priority    default     range   supported   dependency  mandatory   procfunc    mode    constants }
            { border_bit 	                _none_	        _none_	    {CHOICES 0 1}	                        100	    0	        _none_	false	    _none_	false	_none_	_none_	_none_ }
            { group_pool_handle 	        _none_	        _none_	    ALPHANUM	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { group_pool_mode 	                _none_	        _none_	    {CHOICES send receive register}	        100	    send	_none_	false	    _none_	false	_none_	_none_	_none_ }
            { handle 	                        _none_	        _none_	    ALPHANUM	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { interval 	                        PimGlobalConfig	MsgInterval NUMERIC	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { join_prune_aggregation_factor 	_none_	        _none_	    NUMERIC	                                100	    0	        0-9999	false	    _none_	false	_none_	_none_	_none_ }
            { join_prune_per_interval 	        PimGlobalConfig	MsgRate	    NUMERIC	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { mode	                        _none_	        _none_	    {CHOICES create modify delete}	1	    _none_	none	true	    _none_	true	_none_	_none_	_none_ }
            { rate_control	                PimGlobalConfig	EnableMsgRate	{CHOICES 0 1}	                        100	    _none_	0-1	true	    _none_	false	_none_	_none_	{0 false 0 FALSE 1 true 1 TRUE} }
            { register_per_interval 	        PimGlobalConfig	MsgRate	    NUMERIC	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { register_stop_per_interval 	PimGlobalConfig	MsgRate	    NUMERIC	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { rp_ip_addr 	                PimGroupBlk 	RpIpAddr    IP	                                        100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { s_g_rpt_group 	                _none_	        _none_	    NUMERIC	                                100	    0	        0-1	false	    _none_	false	_none_	_none_	_none_ }
            { session_handle	                _none_	        _none_	    ALPHANUM	                                100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { source_pool_handle 	        _none_	        _none_	    ANY	                                        100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { source_group_mapping 	        _none_	        {CHOICES fully_meshed one_to_one}	    ANY	            100	    _none_	_none_	true	    _none_	false	_none_	_none_	_none_ }
            { wildcard_group	                _none_	        _none_	    {CHOICES 0 1}	                        100	    0	        _none_	true	    _none_	false	_none_	_none_	_none_ }
        }
        { emulation_pim_info 
            { hname stcobj  stcattr  type   priority    default     range   supported   dependency  mandatory   procfunc    mode    constants }
            { handle	_none_	_none_	ALPHANUM	101	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { duration  _none_  _none_  ANY 102 _none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { hello_tx	PimRouterResults	TxHelloCount	ANY	103	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { hello_rx	PimRouterResults	RxHelloCount	ANY	104	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { group_join_tx	PimRouterResults	TxGroupStargCount	ANY	105	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { group_join_rx	PimRouterResults	RxGroupStargCount	ANY	106	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { group_prune_tx	_none_	_none_	ANY	107	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { group_prune_rx	_none_	_none_	ANY	108	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { s_g_join_tx	PimRouterResults	TxGroupSgCount	ANY	109	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { s_g_join_rx	PimRouterResults    RxGroupSgCount	ANY	110	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { s_g_prune_tx	_none_	_none_	ANY	111	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { s_g_prune_rx	_none_	_none_	ANY	112	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { group_assert_tx	PimRouterResults	TxAssertCount	ANY	113	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { group_assert_rx	PimRouterResults	RxAssertCount	ANY	114	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { s_g_assert_tx	_none_	_none_	ANY	115	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { s_g_assert_rx	_none_	_none_	ANY	116	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { reg_tx	PimRouterResults	TxRegisterCount	ANY	117	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { reg_rx	PimRouterResults	RxRegisterCount	ANY	118	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { reg_stop_tx	PimRouterResults	TxRegisterStopCount	ANY	119	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { reg_stop_rx	PimRouterResults	RxRegisterStopCount	ANY	120	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { null_reg_tx	_none_	_none_	ANY	121	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { null_reg_rx	_none_	_none_	ANY	122	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { j_p_pdu_tx	PimRouterResults    TxJoinPruneCount	ANY	123	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { j_p_pdu_rx    PimRouterResults    RxJoinPruneCount	ANY 124	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { crp_tx	PimRouterResults    TxCandRpAdvertCount	ANY	125	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { crp_rx	PimRouterResults    RxCandRpAdvertCount	ANY	126	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { bsm_tx	PimRouterResults    TxBootstrapCount	ANY	127	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { bsm_rx    PimRouterResults    RxBootstrapCount	ANY	128	_none_	_none_	true	_none_	false	<procName>	_none_	_none_ }
            { bsm_rp_tx	_none_	_none_	ANY	129	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { bsm_rp_rx	_none_	_none_	ANY	130	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { bsm_group_tx	_none_	_none_	ANY	131	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { bsm_group_rx	_none_	_none_	ANY	132	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { graft_tx	_none_	_none_	ANY	133	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { graft_rx	_none_	_none_	ANY	134	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { graft_ack_tx	_none_	_none_	ANY	135	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
            { graft_ack_rx	_none_	_none_	ANY	136	_none_	_none_	false	_none_	false	<procName>	_none_	_none_ }
        }
    }
}
