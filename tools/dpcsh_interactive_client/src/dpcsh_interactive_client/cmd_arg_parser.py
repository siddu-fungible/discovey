from argparse import ArgumentParser

# Set sub commands
base_set_parser = ArgumentParser(prog="set")
base_set_subparsers = base_set_parser.add_subparsers(title="subcommands", help="")
set_nu_parser = base_set_subparsers.add_parser('nu', help="Set NU config")
set_hnu_parser = base_set_subparsers.add_parser('hnu', help="Set HNU config")
set_system_parser = base_set_subparsers.add_parser('system', help="Set System Configs")

# Set NU sub commands
set_nu_subparsers = set_nu_parser.add_subparsers(title='subcommands', help="")
set_nu_port_parser = set_nu_subparsers.add_parser('port', help="NU Port commands")
set_nu_qos_parser = set_nu_subparsers.add_parser('qos', help="NU QoS commands")
set_nu_sample_parser = set_nu_subparsers.add_parser('sample', help="Sample commands")
set_nu_meter_parser = set_nu_subparsers.add_parser('meter', help="Meter commands")

set_hnu_subparsers = set_hnu_parser.add_subparsers(title='subcommands', help="")
set_hnu_qos_parser = set_hnu_subparsers.add_parser('qos', help="HNU QoS commands")
set_hnu_port_parser = set_hnu_subparsers.add_parser('port', help="HNU Port commands")

# -----------------------------------------------------------------------------------------------
# Set NU Port sub commands
set_nu_port_parsers = set_nu_port_parser.add_subparsers(title="subcommands", help="")
set_hnu_port_parsers = set_hnu_port_parser.add_subparsers(title="subcommands", help="")

# MTU
set_port_mtu_parser = set_nu_port_parsers.add_parser('mtu', help="Port MTU")
set_port_mtu_parser.add_argument('port_num', type=int, help="port num")
set_port_mtu_parser.add_argument('shape', type=int, help="shape")
set_port_mtu_parser.add_argument('mtu_value', type=int, help="MTU value")
# Enable Port
set_port_enable_parser = set_nu_port_parsers.add_parser('enable', help="Enable")
set_port_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_enable_parser.add_argument('shape', type=int, help="shape")
# Disable Port
set_port_disable_parser = set_nu_port_parsers.add_parser('disable', help="Disable")
set_port_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_disable_parser.add_argument('shape', type=int, help="shape")

# Set NU Port Pause sub commands
set_port_pause_parser = set_nu_port_parsers.add_parser('pause', help="NU Port Link pause")
set_port_pause_subparsers = set_port_pause_parser.add_subparsers(title="subcommands", help="")
# Enable Pause
set_port_pause_enable_parser = set_port_pause_subparsers.add_parser('enable', help="Enable Port Link Pause")
set_port_pause_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_enable_parser.add_argument('shape', type=int, help="shape")
# Disable Pause
set_port_pause_disable_parser = set_port_pause_subparsers.add_parser('disable', help="Disable Port Link Pause")
set_port_pause_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_disable_parser.add_argument('shape', type=int, help="shape")
# Enable Tx Pause
set_port_pause_tx_enable_parser = set_port_pause_subparsers.add_parser('tx_enable', help="Enable Port Tx Link Pause")
set_port_pause_tx_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_tx_enable_parser.add_argument('shape', type=int, help="shape")
# Disable Tx Pause
set_port_pause_tx_disable_parser = set_port_pause_subparsers.add_parser('tx_disable', help="Disable Port Tx Link Pause")
set_port_pause_tx_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_tx_disable_parser.add_argument('shape', type=int, help="shape")
# Set Port Pause Quanta
set_port_pause_quanta_parser = set_port_pause_subparsers.add_parser('quanta', help="Set Port Link Pause Quanta")
set_port_pause_quanta_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_quanta_parser.add_argument('shape', type=int, help="shape")
set_port_pause_quanta_parser.add_argument('quanta', type=int, help="Quanta")
# Set Port Pause threshold
set_port_pause_threshold_parser = set_port_pause_subparsers.add_parser('threshold', help="Set Port Link Pause threshold")
set_port_pause_threshold_parser.add_argument('port_num', type=int, help="port_num")
set_port_pause_threshold_parser.add_argument('shape', type=int, help="shape")
set_port_pause_threshold_parser.add_argument('threshold', type=int, help="threshold")


# Set NU Port PFC sub commands
set_port_pfc_parser = set_nu_port_parsers.add_parser('pfc', help="Port PFC")
set_port_pfc_subparsers = set_port_pfc_parser.add_subparsers(title="subcommands", help="")
# Enable pfc
set_port_pfc_enable_parser = set_port_pfc_subparsers.add_parser('enable', help="Enable Port pfc")
set_port_pfc_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_enable_parser.add_argument('shape', type=int, help="shape")
# Disable pfc
set_port_pfc_disable_parser = set_port_pfc_subparsers.add_parser('disable', help="Disable Port pfc")
set_port_pfc_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_disable_parser.add_argument('shape', type=int, help="shape")
# Enable Tx pfc
set_port_pfc_tx_enable_parser = set_port_pfc_subparsers.add_parser('tx_enable', help="Enable Port Tx pfc")
set_port_pfc_tx_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_tx_enable_parser.add_argument('shape', type=int, help="shape")
set_port_pfc_tx_enable_parser.add_argument('class_num', type=int, help="class")
# Disable Tx pfc
set_port_pfc_tx_disable_parser = set_port_pfc_subparsers.add_parser('tx_disable', help="Disable Port Tx pfc")
set_port_pfc_tx_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_tx_disable_parser.add_argument('shape', type=int, help="shape")
set_port_pfc_tx_disable_parser.add_argument('class_num', type=int, help="class")
# Set Port pfc Quanta
set_port_pfc_quanta_parser = set_port_pfc_subparsers.add_parser('quanta', help="Set Port pfc Quanta")
set_port_pfc_quanta_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_quanta_parser.add_argument('shape', type=int, help="shape")
set_port_pfc_quanta_parser.add_argument('class_num', type=int, help="class")
set_port_pfc_quanta_parser.add_argument('quanta', type=int, help="Quanta")
# Set Port pfc threshold
set_port_pfc_threshold_parser = set_port_pfc_subparsers.add_parser('threshold', help="Set Port pfc threshold")
set_port_pfc_threshold_parser.add_argument('port_num', type=int, help="port_num")
set_port_pfc_threshold_parser.add_argument('shape', type=int, help="shape")
set_port_pfc_threshold_parser.add_argument('class_num', type=int, help="class")
set_port_pfc_threshold_parser.add_argument('threshold', type=int, help="threshold")

# Set NU Port PTP sub commands
set_port_ptp_parser = set_nu_port_parsers.add_parser('ptp', help="Port PTP")
set_port_ptp_subparsers = set_port_ptp_parser.add_subparsers(title="subcommands", help="")
# Enable ptp
set_port_ptp_peer_delay_enable_parser = set_port_ptp_subparsers.add_parser('peer_delay_enable',
                                                                           help="Enable Port ptp peer delay")
set_port_ptp_peer_delay_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_ptp_peer_delay_enable_parser.add_argument('shape', type=int, help="shape")
# Disable ptp
set_port_ptp_peer_delay_disable_parser = set_port_ptp_subparsers.add_parser('peer_delay_disable',
                                                                            help="Disable Port ptp peer delay")
set_port_ptp_peer_delay_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_ptp_peer_delay_disable_parser.add_argument('shape', type=int, help="shape")
# Set ptp peer delay
set_port_ptp_peer_delay_parser = set_port_ptp_subparsers.add_parser('peer_delay', help="Set Port ptp peer delay")
set_port_ptp_peer_delay_parser.add_argument('port_num', type=int, help="port_num")
set_port_ptp_peer_delay_parser.add_argument('shape', type=int, help="shape")
set_port_ptp_peer_delay_parser.add_argument('delay', type=int, help="delay")
# Enable ptp 1 step
set_port_ptp_1step_enable_parser = set_port_ptp_subparsers.add_parser('1step_enable',
                                                                      help="Enable Port ptp peer delay")
set_port_ptp_1step_enable_parser.add_argument('port_num', type=int, help="port_num")
set_port_ptp_1step_enable_parser.add_argument('shape', type=int, help="shape")
# Disable ptp 1step
set_port_ptp_1step_disable_parser = set_port_ptp_subparsers.add_parser('1step_disable',
                                                                       help="Disable Port ptp peer delay")
set_port_ptp_1step_disable_parser.add_argument('port_num', type=int, help="port_num")
set_port_ptp_1step_disable_parser.add_argument('shape', type=int, help="shape")

# Set NU Port Runt sub commands
set_port_runt_parser = set_nu_port_parsers.add_parser('runt', help="Set Port Runt Config")
set_port_runt_sunbparsers = set_port_runt_parser.add_subparsers(title='subcommands', help="")
# Set Runt Filter
set_port_runt_filter_parser = set_port_runt_sunbparsers.add_parser('filter', help="Set Port Runt Filter")
set_port_runt_filter_parser.add_argument('port_num', type=int, help="port_num")
set_port_runt_filter_parser.add_argument('shape', type=int, help="shape")
set_port_runt_filter_parser.add_argument('buffer_64', type=int, help="Buffer")
set_port_runt_filter_parser.add_argument('runt_err_en', type=int, help="Runt Error Enable")
set_port_runt_filter_parser.add_argument('en_delete', type=int, help="Enable Delete")

# Set Port Speed
brkmode_list = ['no_brk_40g', 'no_brk_100g', 'brk_2x50g', 'brk_4x25g', 'brk_4x10g', 'brk_1x50g_2x25g',
                'brk_2x25g_1x50g']
set_port_speed_parser = set_nu_port_parsers.add_parser('speed', help="Set port speed")
set_port_speed_parser.add_argument('port_num', type=int, help="port_num")
set_port_speed_parser.add_argument('shape', type=int, help='shape')
set_port_speed_parser.add_argument('brkmode', type=str, help='Specify brkmode from %s' % brkmode_list)

# -----------------------------------------------------------------------------------------------
# Set NU QoS sub commands
set_nu_qos_parsers = set_nu_qos_parser.add_subparsers(title="subcommands", help="")
# QoS Egress sub commands
set_qos_egress_parser = set_nu_qos_parsers.add_parser('egress', help="QoS Egress Buffers")
set_qos_egress_parsers = set_qos_egress_parser.add_subparsers(title='subcommands', help="")

set_qos_egress_buffer_pool_parser = set_qos_egress_parsers.add_parser('buffer_pool', help="QoS Egress Buffer Pool")
set_qos_egress_buffer_pool_parser.add_argument('-sf_thr', type=int, help="Egress Buffer Pool sf_thr", default=None)
set_qos_egress_buffer_pool_parser.add_argument('-sx_thr', type=int, help="Egress Buffer Pool sx_thr", default=None)
set_qos_egress_buffer_pool_parser.add_argument('-df_thr', type=int, help="Egress Buffer Pool df_thr", default=None)
set_qos_egress_buffer_pool_parser.add_argument('-dx_thr', type=int, help="Egress Buffer Pool dx_thr", default=None)
set_qos_egress_buffer_pool_parser.add_argument('-fcp_thr', type=int, help="Egress Buffer Pool fcp_thr", default=None)
set_qos_egress_buffer_pool_parser.add_argument('-nonfcp_thr', type=int, help="Egress Buffer Pool nonfcp_thr")
set_qos_egress_buffer_pool_parser.add_argument('-sample_copy_thr', type=int, help="Egress Buffer Pool sample_copy_thr",
                                               default=None)
set_qos_egress_buffer_pool_parser.add_argument('-sf_xoff_thr', type=int, help="Egress Buffer Pool sf_xoff_thr",
                                               default=None)
set_qos_egress_buffer_pool_parser.add_argument('-fcp_xoff_thr', type=int, help="Egress Buffer Pool fcp_xoff_thr",
                                               default=None)
set_qos_egress_buffer_pool_parser.add_argument('-nonfcp_xoff_thr', type=int, help="Egress Buffer Pool nonfcp_xoff_thr",
                                               default=None)

set_qos_egress_port_buffer_parser = set_qos_egress_parsers.add_parser('port_buffer', help="QoS Egress Port Buffer")
set_qos_egress_port_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
set_qos_egress_port_buffer_parser.add_argument('-min_thr', type=int, help="Egress Port Buffer min_thr", default=None)
set_qos_egress_port_buffer_parser.add_argument('-shared_thr', type=int, help="Egress Port Buffer shared_thr",
                                               default=None)

set_qos_egress_queue_buffer_parser = set_qos_egress_parsers.add_parser('queue_buffer', help="QoS Egress Queue Buffer")
set_qos_egress_queue_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
set_qos_egress_queue_buffer_parser.add_argument('queue', type=int, help="Egress Queue num")
set_qos_egress_queue_buffer_parser.add_argument('-min_thr', type=int, help="Egress Queue Buffer min_thr",
                                                default=None)
set_qos_egress_queue_buffer_parser.add_argument('-static_shared_thr_green', type=int,
                                                help="Egress Queue Buffer static_shared_thr_green",
                                                default=None)
set_qos_egress_queue_buffer_parser.add_argument('-dynamic_enable', type=int, help="Egress Queue Buffer dynamic_enable",
                                                default=None)
set_qos_egress_queue_buffer_parser.add_argument('-shared_thr_alpha', type=int,
                                                help="Egress Queue Buffer shared_thr_alpha",
                                                default=None)
set_qos_egress_queue_buffer_parser.add_argument('-shared_thr_offset_yellow', type=int,
                                                help="Egress Queue Buffer shared_thr_offset_yellow",
                                                default=None)
set_qos_egress_queue_buffer_parser.add_argument('-shared_thr_offset_red', type=int,
                                                help="Egress Queue Buffer shared_thr_offset_red",
                                                default=None)

set_qos_egress_priority_map_parser = set_qos_egress_parsers.add_parser('queue_to_priority_map', help="QoS egress priority map")
set_qos_egress_priority_map_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_egress_priority_map_parser.add_argument('-map_list', nargs='+', help="QoS egress map list E.g [1, 2, 3....N] \n "
                                                                        "Where n is number of queues, n = 16 for "
                                                                        "FPG ports and n = 8 for EPG ports \n"
                                                                        "Please specify space separated list for E.g \n"
                                                                        "set nu qos egress queue_to_priority_map 6 -map-list 1 2 3 4 5 6 7 7",
                                           default=None)

# QoS ECN sub commands
set_qos_ecn_parser = set_nu_qos_parsers.add_parser('ecn', help="QoS ECN Config")
set_qos_ecn_parsers = set_qos_ecn_parser.add_subparsers(title='subcommands', help="")

set_qos_ecn_glb_sh_thresh_parser = set_qos_ecn_parsers.add_parser('glb_sh_thresh', help="QoS ECN glb sh threshold")
set_qos_ecn_glb_sh_thresh_parser.add_argument('-en', type=int, help="glb_sh_thresh en", default=None)
set_qos_ecn_glb_sh_thresh_parser.add_argument('-green', type=int, help="glb_sh_thresh green", default=None)
set_qos_ecn_glb_sh_thresh_parser.add_argument('-yellow', type=int, help="glb_sh_thresh yellow", default=None)
set_qos_ecn_glb_sh_thresh_parser.add_argument('-red', type=int, help="glb_sh_thresh red", default=None)

set_qos_ecn_profile_parser = set_qos_ecn_parsers.add_parser('profile', help="QoS ECN Profile")
set_qos_ecn_profile_parser.add_argument('prof_num', type=int, help="Profile num")
set_qos_ecn_profile_parser.add_argument('-min_thr', type=int, help="Profile min threshold", default=None)
set_qos_ecn_profile_parser.add_argument('-max_thr', type=int, help="Profile max threshold", default=None)
set_qos_ecn_profile_parser.add_argument('-ecn_prob_index', type=int, help="Profile ECN prob index", default=None)

set_qos_ecn_prob_parser = set_qos_ecn_parsers.add_parser('prob', help="QoS ECN Prob")
set_qos_ecn_prob_parser.add_argument('prob_idx', type=int, help="Prob index")
set_qos_ecn_prob_parser.add_argument('-prob', type=int, help="Prob", default=None)

# QoS WRED sub commands
set_qos_wred_parser = set_nu_qos_parsers.add_parser('wred', help="QoS WRED Config")
set_qos_wred_parsers = set_qos_wred_parser.add_subparsers(title='subcommands', help="")

set_qos_wred_profile_parser = set_qos_wred_parsers.add_parser('profile', help="QoS WRED Profile")
set_qos_wred_profile_parser.add_argument('prof_num', type=int, help="Profile num")
set_qos_wred_profile_parser.add_argument('-min_thr', type=int, help="Profile min threshold", default=None)
set_qos_wred_profile_parser.add_argument('-max_thr', type=int, help="Profile max threshold", default=None)
set_qos_wred_profile_parser.add_argument('-wred_prob_index', type=int, help="Profile WRED prob index", default=None)

set_qos_wred_prob_parser = set_qos_wred_parsers.add_parser('prob', help="QoS WRED Prob")
set_qos_wred_prob_parser.add_argument('prob_idx', type=int, help="Prob index")
set_qos_wred_prob_parser.add_argument('-prob', type=int, help="Prob", default=None)

set_qos_wred_queue_config_parser = set_qos_wred_parsers.add_parser('queue_config', help="QoS WRED Queue Config")
set_qos_wred_queue_config_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_wred_queue_config_parser.add_argument('queue', type=int, help="Queue Num")
set_qos_wred_queue_config_parser.add_argument('-wred_en', type=int, help="QoS WRED Queue Enable", default=None)
set_qos_wred_queue_config_parser.add_argument('-wred_weight', type=int, help="QoS WRED Queue weight", default=None)
set_qos_wred_queue_config_parser.add_argument('-wred_prof_num', type=int, help="QoS WRED Queue Profile Num",
                                              default=None)
set_qos_wred_queue_config_parser.add_argument('-ecn_en', type=int, help="QoS WRED Queue ECN enable", default=None)
set_qos_wred_queue_config_parser.add_argument('-ecn_prof_num', type=int, help="QoS WRED Queue ECN Prof num",
                                              default=None)

set_qos_wred_avg_queue_config_parser = set_qos_wred_parsers.add_parser('avg_q_config', help="QoS WRED Avg Queue Config")
set_qos_wred_avg_queue_config_parser.add_argument('-q_avg_en', type=int, help="QoS WRED Avg Queue Enable",
                                                  default=None)
set_qos_wred_avg_queue_config_parser.add_argument('-cap_avg_sz', type=int, help="QoS WRED Avg Queue cap_avg_sz",
                                                  default=None)
set_qos_wred_avg_queue_config_parser.add_argument('-avg_period', type=int, help="QoS WRED Avg Queue Period",
                                                  default=None)

# QoS Scheduler sub commands
set_qos_scheduler_parser = set_nu_qos_parsers.add_parser('scheduler', help="QoS Scheduler Config")
set_qos_scheduler_parsers = set_qos_scheduler_parser.add_subparsers(title='subcommands', help="")

# dwrr
set_qos_scheduler_dwrr_parser = set_qos_scheduler_parsers.add_parser('dwrr', help="QoS Scheduler dwrr Config")
set_qos_scheduler_dwrr_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_scheduler_dwrr_parser.add_argument('queue', type=int, help="Queue Num")
set_qos_scheduler_dwrr_parser.add_argument('weight', type=int, help="Weight")

# Shaper
set_qos_scheduler_shaper_parser = set_qos_scheduler_parsers.add_parser('shaper', help="QoS Scheduler Shaper Config")
set_qos_scheduler_shaper_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_scheduler_shaper_parser.add_argument('queue', type=int, help="Queue Num")
set_qos_scheduler_shaper_parser.add_argument('-enable', type=int, help="Shaper enable/disable")
set_qos_scheduler_shaper_parser.add_argument('-type', type=int, help="Shaper type. 0=min_rate, 1=max_rate")
set_qos_scheduler_shaper_parser.add_argument('-rate', type=int, help="Shaper rate in bits")
set_qos_scheduler_shaper_parser.add_argument('-thresh', type=int, help="Shaper Threshold")

# Strict priority
set_qos_scheduler_strict_priority_parser = set_qos_scheduler_parsers.add_parser('strict_priority',
                                                                                help="QoS Scheduler Strict "
                                                                                     "Priority Config")
set_qos_scheduler_strict_priority_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_scheduler_strict_priority_parser.add_argument('queue', type=int, help="Queue Num")
set_qos_scheduler_strict_priority_parser.add_argument('-strict_priority_enable', type=int, help="QoS Scheduler Strict "
                                                                                                "Priority enable",
                                                      default=None)
set_qos_scheduler_strict_priority_parser.add_argument('-extra_bandwidth', type=int, help="QoS Scheduler Strict Priority "
                                                                                         "Extra Bandawidth",
                                                      default=None)

# QoS Ingress sub commands
set_qos_ingress_parser = set_nu_qos_parsers.add_parser('ingress', help="QoS INgress Config")
set_qos_ingress_parsers = set_qos_ingress_parser.add_subparsers(title='subcommands', help="")

set_qos_ingress_pg_parser = set_qos_ingress_parsers.add_parser('pg', help="QoS ingress pg")
set_qos_ingress_pg_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_ingress_pg_parser.add_argument('pg', type=int, help="Pg Num")
set_qos_ingress_pg_parser.add_argument('-min_thr', type=int, help="QoS ingress min thr", default=None)
set_qos_ingress_pg_parser.add_argument('-shared_thr', type=int, help="QoS ingress shared thr", default=None)
set_qos_ingress_pg_parser.add_argument('-headroom_thr', type=int, help="QoS ingress headroom_thr", default=None)
set_qos_ingress_pg_parser.add_argument('-xoff_enable', type=int, help="QoS ingress xoff_enable", default=None)
set_qos_ingress_pg_parser.add_argument('-shared_xon_thr', type=int, help="QoS ingress shared_xon_thr", default=None)

set_qos_ingress_pg_map_parser = set_qos_ingress_parsers.add_parser('priority_to_pg_map', help="QoS ingress pg map")
set_qos_ingress_pg_map_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_ingress_pg_map_parser.add_argument('-map_list', nargs='+', help="QoS ingress map list E.g [1, 2, 3....N] \n "
                                                                        "Where n is number of priorities, n = 16 for "
                                                                        "FPG ports and n = 8 for EPG ports \n"
                                                                        "Please specify space separated list for E.g \n"
                                                                        "set nu qos ingress priority_to_pg_map 6 -map-list 1 2 3 4 5 6 7 7",
                                           default=None)
# QoS Pfc sub commands
set_qos_pfc_parser = set_nu_qos_parsers.add_parser('pfc', help="QoS PFC Config")
set_qos_pfc_parsers = set_qos_pfc_parser.add_subparsers(title="subcommands", help="")
set_qos_pfc_enable_parser = set_qos_pfc_parsers.add_parser('enable', help="QoS PFC Enable")
set_qos_pfc_disable_parser = set_qos_pfc_parsers.add_parser('disable', help="QoS PFC Disable")

# QoS arb cfg sub commands
set_qos_arb_cfg_parser = set_nu_qos_parsers.add_parser('arb_cfg', help="QoS arb cfg Config")
set_qos_arb_cfg_parser.add_argument('en', type=int, help="QoS arb cfg Enable")

# QoS xoff status
set_qos_xoff_status_parser = set_nu_qos_parsers.add_parser('xoff_status', help="QoS xoff status")
set_qos_xoff_status_parser.add_argument('port_num', type=int, help="Port Num")
set_qos_xoff_status_parser.add_argument('pg', type=int, help="PG Num")
set_qos_xoff_status_parser.add_argument('-status', type=int, help="QoS xoff_status", default=None)

# -----------------------------------------------------------------------------------------------
# Sample commands
set_nu_sample_parsers = set_nu_sample_parser.add_subparsers(title="subcommands", help="")
set_nu_sample_ingress_parser = set_nu_sample_parsers.add_parser('ingress', help="Sampler for ingress parser")
set_nu_sample_ingress_parser.add_argument("id", type=int, help="Sample id [0-63]")
set_nu_sample_ingress_parser.add_argument("dest", type=int, help="dest [0-1023]", default=None)
set_nu_sample_ingress_parser.add_argument("-fpg", type=int, help="Fpg [0-7]", default=None)
set_nu_sample_ingress_parser.add_argument("-acl", type=int, help="acl: [0-124]", default=None)
set_nu_sample_ingress_parser.add_argument("-flag_mask", type=int, help="Flag mask [0-63]", default=None)
set_nu_sample_ingress_parser.add_argument("-hu", type=int, help="HU [0-7]", default=None)
set_nu_sample_ingress_parser.add_argument("-psw_drop", type=int, help="PSW drop", default=None)
set_nu_sample_ingress_parser.add_argument("-pps_en", type=int, help="PPS en [0-1]", default=None)
set_nu_sample_ingress_parser.add_argument("-pps_interval", type=int, help="pps interval [1-0xffffff]", default=None)
set_nu_sample_ingress_parser.add_argument("-pps_burst", type=int, help="pps burst [0-127]", default=None)
set_nu_sample_ingress_parser.add_argument("-pps_tick", type=int, help="pps tick set clock frequency for e.g "
                                                                      "1000 KHz[1000]", default=None)
set_nu_sample_ingress_parser.add_argument("-sampler_en", type=int, help="sampler_en [0-1]", default=None)
set_nu_sample_ingress_parser.add_argument("-sampler_rate", type=int, help="sampler_rate [1-0x3fff]", default=None)
set_nu_sample_ingress_parser.add_argument("-sampler_run_sz", type=int, help="sampler run sz [1-15]", default=None)
set_nu_sample_ingress_parser.add_argument("-first_cell_only", type=int, help="first cell only [0-1]", default=None)

set_nu_sample_egress_parser = set_nu_sample_parsers.add_parser('egress', help="Sampler for egress parser")
set_nu_sample_egress_parser.add_argument("id", type=int, help="Sample id [0-63]")
set_nu_sample_egress_parser.add_argument("dest", type=int, help="dest [0-1023]")
set_nu_sample_egress_parser.add_argument("-fpg", type=int, help="Fpg [0-7]", default=None)
set_nu_sample_egress_parser.add_argument("-acl", type=int, help="acl: [0-124]", default=None)
set_nu_sample_egress_parser.add_argument("-flag_mask", type=int, help="Flag mask [0-63]", default=None)
set_nu_sample_egress_parser.add_argument("-hu", type=int, help="HU [0-7]", default=None)
set_nu_sample_egress_parser.add_argument("-psw_drop", type=int, help="PSW drop", default=None)
set_nu_sample_egress_parser.add_argument("-pps_en", type=int, help="PPS en [0-1]", default=None)
set_nu_sample_egress_parser.add_argument("-pps_interval", type=int, help="pps interval [1-0xffffff]", default=None)
set_nu_sample_egress_parser.add_argument("-pps_burst", type=int, help="pps burst [0-127]", default=None)
set_nu_sample_egress_parser.add_argument("-pps_tick", type=int, help="pps tick set clock frequency for e.g "
                                                                      "1000 KHz[1000]", default=None)
set_nu_sample_egress_parser.add_argument("-sampler_en", type=int, help="sampler_en [0-1]", default=None)
set_nu_sample_egress_parser.add_argument("-sampler_rate", type=str, help="sampler_rate [1-0x3fff]", default=None)
set_nu_sample_egress_parser.add_argument("-sampler_run_sz", type=int, help="sampler run sz [1-15]", default=None)
set_nu_sample_egress_parser.add_argument("-first_cell_only", type=int, help="first cell only [0-1]", default=None)

set_nu_sample_disable_parser = set_nu_sample_parsers.add_parser('disable', help="Sampler for disable parser")
set_nu_sample_disable_parser.add_argument("id", type=int, help="Sample id [0-63]")
set_nu_sample_disable_parser.add_argument("dest", type=int, help="dest [0-1023]")
set_nu_sample_disable_parser.add_argument("-fpg", type=int, help="Fpg [0-7]", default=None)
set_nu_sample_disable_parser.add_argument("-acl", type=int, help="acl: [0-124]", default=None)
set_nu_sample_disable_parser.add_argument("-flag_mask", type=int, help="Flag mask [0-63]", default=None)
set_nu_sample_disable_parser.add_argument("-hu", type=int, help="HU [0-7]", default=None)
set_nu_sample_disable_parser.add_argument("-psw_drop", type=int, help="PSW drop", default=None)
set_nu_sample_disable_parser.add_argument("-pps_en", type=int, help="PPS en [0-1]", default=None)
set_nu_sample_disable_parser.add_argument("-pps_interval", type=int, help="pps interval [1-0xffffff]", default=None)
set_nu_sample_disable_parser.add_argument("-pps_burst", type=int, help="pps burst [0-127]", default=None)
set_nu_sample_disable_parser.add_argument("-pps_tick", type=int, help="pps tick set clock frequency for e.g "
                                                                      "1000 KHz[1000]", default=None)
set_nu_sample_disable_parser.add_argument("-sampler_en", type=int, help="sampler_en [0-1]", default=None)
set_nu_sample_disable_parser.add_argument("-sampler_rate", type=str, help="sampler_rate [1-0x3fff]", default=None)
set_nu_sample_disable_parser.add_argument("-sampler_run_sz", type=int, help="sampler run sz [1-15]", default=None)
set_nu_sample_disable_parser.add_argument("-first_cell_only", type=int, help="first cell only [0-1]", default=None)

# -----------------------------------------------------------------------------------------------
# Meter commands
set_nu_meter_parser.add_argument('index', type=int, help="Meter ID")
set_nu_meter_parser.add_argument('interval', type=int, help="Meter Interval")
set_nu_meter_parser.add_argument('crd', type=int, help="Meter CRD")
set_nu_meter_parser.add_argument('commit_rate', type=int, help="Meter Commit Rate")
set_nu_meter_parser.add_argument('pps_mode', type=int, help="Meter PPS Mode")
set_nu_meter_parser.add_argument('-excess_rate', type=int, help="Meter Excess Rate", default=0)
set_nu_meter_parser.add_argument('-commit_burst', type=int, help="Meter Commit Burst", default=82)
set_nu_meter_parser.add_argument('-excess_burst', type=int, help="Meter Excess Burst", default=1)
set_nu_meter_parser.add_argument('-direction', type=int, help="Meter direction", default=0)
set_nu_meter_parser.add_argument('-len_mode', type=int, help="Meter Len Mode", default=1)
set_nu_meter_parser.add_argument('-rate_mode', type=int, help="Meter Rate Mode", default=0)
set_nu_meter_parser.add_argument('-color_aware', type=int, help="Meter Color Aware", default=0)
set_nu_meter_parser.add_argument('-unit', type=int, help="Meter Unit", default=0)
set_nu_meter_parser.add_argument('-rsvd', type=int, help="Meter RSVD", default=0)
set_nu_meter_parser.add_argument('-len8', type=int, help="Meter Len8", default=3)
set_nu_meter_parser.add_argument('-common', type=dict, help="Meter Common", default={})
set_nu_meter_parser.add_argument('-bank', type=int, help="Meter Bank", default=0)

# -----------------------------------------------------------------------------------------------
# Set NU system sub commands
set_system_parsers = set_system_parser.add_subparsers(title="subcommands", help="")
set_system_params_parser = set_system_parsers.add_parser('params', help="Set System Params")
set_system_time_interval_parser = set_system_parsers.add_parser('time_interval', help="Set Time interval between "
                                                                                      "stats iterations")
set_system_time_interval_parser.add_argument('time', type=int, help="Time interval in secs")

# Set Syslog Levels
set_system_params_subparsers = set_system_params_parser.add_subparsers(title="subcommands", help="")
set_system_params_syslog_parser = set_system_params_subparsers.add_parser('syslog', help="Set System Syslog Params")
set_system_params_syslog_parser.add_argument('level_val', type=int, help="Syslog Level Value")

# ============================================================================================================

# Get sub commands
base_get_parser = ArgumentParser(prog="get")
base_get_subparsers = base_get_parser.add_subparsers(title="subcommands", help="")
get_nu_parser = base_get_subparsers.add_parser('nu', help="Get NU config")
get_hnu_parser = base_get_subparsers.add_parser('hnu', help="Get HNU config")
get_system_parser = base_get_subparsers.add_parser('system', help="system log commands")
get_bam_parser = base_get_subparsers.add_parser('bam', help="get bam commands")

# Get NU sub commands
get_nu_subparsers = get_nu_parser.add_subparsers(title='subcommands', help="")
get_nu_port_parser = get_nu_subparsers.add_parser('port', help="NU Port commands")
get_nu_qos_parser = get_nu_subparsers.add_parser('qos', help="NU QoS commands")
get_nu_sample_parser = get_nu_subparsers.add_parser('sample', help="Sample commands")
get_nu_config_parser = get_nu_subparsers.add_parser("configs",help="Config commands")

get_hnu_subparsers = get_hnu_parser.add_subparsers(title='subcommands', help="")
get_hnu_qos_parser = get_hnu_subparsers.add_parser('qos', help="HNU QoS commands")

get_bam_parser.add_argument("configs")

#get_bam_parser.add_parser("usage", help="print bam usage", default=None)
#get_bam_parser.add_argument("pool_config", help="print bam pool config")

get_nu_config_parser.add_argument("config_type",
                                   help="Value for config_type can be: \n1. pool_config\n2. ncv_config\n3. per_pool_flow_control\n4. global_flow_control",
                                   default=None)
# -----------------------------------------------------------------------------------------------

# Get NU Port sub commands
get_nu_port_parsers = get_nu_port_parser.add_subparsers(title="subcommands", help="")
# MTU
get_port_mtu_parser = get_nu_port_parsers.add_parser('mtu', help="Port MTU")
get_port_mtu_parser.add_argument('port_num', type=int, help="port num")
get_port_mtu_parser.add_argument('shape', type=int, help="shape")

# Get NU Port Pause sub commands
get_port_pause_parser = get_nu_port_parsers.add_parser('pause', help="Port PFC")
get_port_pause_subparsers = get_port_pause_parser.add_subparsers(title="subcommands", help="")
# Get Port Pause Quanta
get_port_pause_quanta_parser = get_port_pause_subparsers.add_parser('quanta', help="Set Port Link Pause Quanta")
get_port_pause_quanta_parser.add_argument('port_num', type=int, help="port_num")
get_port_pause_quanta_parser.add_argument('shape', type=int, help="shape")
# Get Port Pause Threshold
get_port_pause_threshold_parser = get_port_pause_subparsers.add_parser('threshold', help="Set Port Link Pause threshold")
get_port_pause_threshold_parser.add_argument('port_num', type=int, help="port_num")
get_port_pause_threshold_parser.add_argument('shape', type=int, help="shape")

# Get NU Port pfc sub commands
get_port_pfc_parser = get_nu_port_parsers.add_parser('pfc', help="Port Link Pause")
get_port_pfc_subparsers = get_port_pfc_parser.add_subparsers(title="subcommands", help="")
# Get Port pfc Quanta
get_port_pfc_quanta_parser = get_port_pfc_subparsers.add_parser('quanta', help="Set Port pfc Quanta")
get_port_pfc_quanta_parser.add_argument('port_num', type=int, help="port_num")
get_port_pfc_quanta_parser.add_argument('shape', type=int, help="shape: {'NU': 0, 'HNU': 1}")
get_port_pfc_quanta_parser.add_argument('class_num', type=int, help="class: {'NU': 0, 'HNU': 1}")
# Get Port pfc Threshold
get_port_pfc_threshold_parser = get_port_pfc_subparsers.add_parser('threshold', help="Set Port pfc threshold")
get_port_pfc_threshold_parser.add_argument('port_num', type=int, help="port_num")
get_port_pfc_threshold_parser.add_argument('shape', type=int, help="shape: {'NU': 0, 'HNU': 1}")
get_port_pfc_threshold_parser.add_argument('class_num', type=int, help="class: {'NU': 0, 'HNU': 1}")

# Get Port PTP sub commands
get_port_ptp_parser = get_nu_port_parsers.add_parser('ptp', help="Port PTP")
get_port_ptp_subparsers = get_port_ptp_parser.add_subparsers(title="subcommands", help="")
# Get ptp peer delay
get_port_ptp_peer_delay_parser = get_port_ptp_subparsers.add_parser('peer_delay', help="Get Port ptp peer delay")
get_port_ptp_peer_delay_parser.add_argument('port_num', type=int, help="port_num")
get_port_ptp_peer_delay_parser.add_argument('shape', type=int, help="shape")
# Get ptp tx ts
get_port_ptp_tx_ts_parser = get_port_ptp_subparsers.add_parser('tx_ts', help="Get Port ptp peer delay")
get_port_ptp_tx_ts_parser.add_argument('port_num', type=int, help="port_num")
get_port_ptp_tx_ts_parser.add_argument('shape', type=int, help="shape")

# Get NU Port Runt sub commands
get_port_runt_parser = get_nu_port_parsers.add_parser('runt', help="Get Port Runt Config")
get_port_runt_sunbparsers = get_port_runt_parser.add_subparsers(title='subcommands', help="")
# Get Runt Filter
get_port_runt_filter_parser = get_port_runt_sunbparsers.add_parser('filter', help="Get Port Runt Filter")
get_port_runt_filter_parser.add_argument('port_num', type=int, help="port_num")
get_port_runt_filter_parser.add_argument('shape', type=int, help="shape")

# Get Port Linkstatus
get_port_link_status_parser = get_nu_port_parsers.add_parser('linkstatus', help="Get Port Link Status")
# -----------------------------------------------------------------------------------------------
# Get NU QoS sub commands
get_nu_qos_parsers = get_nu_qos_parser.add_subparsers(title="subcommands", help="")
# QoS Egress sub commands
get_qos_egress_parser = get_nu_qos_parsers.add_parser('egress', help="QoS Egress Buffers")
get_qos_egress_parsers = get_qos_egress_parser.add_subparsers(title='subcommands', help="")

get_qos_egress_buffer_pool_parser = get_qos_egress_parsers.add_parser('buffer_pool', help="QoS Egress Buffer Pool")

get_qos_egress_port_buffer_parser = get_qos_egress_parsers.add_parser('port_buffer', help="QoS Egress Port Buffer")
get_qos_egress_port_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")

get_qos_egress_queue_buffer_parser = get_qos_egress_parsers.add_parser('queue_buffer', help="QoS Egress Queue Buffer")
get_qos_egress_queue_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
get_qos_egress_queue_buffer_parser.add_argument('queue', type=int, help="Egress Queue Num")

get_qos_egress_priority_map_parser = get_qos_egress_parsers.add_parser('queue_to_priority_map', help="QoS egress queue map")
get_qos_egress_priority_map_parser.add_argument('port_num', type=int, help="Port Num")

# QoS ECN sub commands
get_qos_ecn_parser = get_nu_qos_parsers.add_parser('ecn', help="QoS ECN Config")
get_qos_ecn_parsers = get_qos_ecn_parser.add_subparsers(title='subcommands', help="")

get_qos_ecn_glb_sh_thresh_parser = get_qos_ecn_parsers.add_parser('glb_sh_thresh', help="QoS ECN glb sh threshold")

get_qos_ecn_profile_parser = get_qos_ecn_parsers.add_parser('profile', help="QoS ECN Profile")
get_qos_ecn_profile_parser.add_argument('prof_num', type=int, help="Profile num")

get_qos_ecn_prob_parser = get_qos_ecn_parsers.add_parser('prob', help="QoS ECN Prob")
get_qos_ecn_prob_parser.add_argument('prob_idx', type=int, help="Prob index")

# QoS WRED sub commands
get_qos_wred_parser = get_nu_qos_parsers.add_parser('wred', help="QoS WRED Config")
get_qos_wred_parsers = get_qos_wred_parser.add_subparsers(title='subcommands', help="")

get_qos_wred_profile_parser = get_qos_wred_parsers.add_parser('profile', help="QoS WRED Profile")
get_qos_wred_profile_parser.add_argument('prof_num', type=int, help="Profile num")

get_qos_wred_prob_parser = get_qos_wred_parsers.add_parser('prob', help="QoS WRED Prob")
get_qos_wred_prob_parser.add_argument('prob_idx', type=int, help="Prob index")

get_qos_wred_queue_config_parser = get_qos_wred_parsers.add_parser('queue_config', help="QoS WRED Queue Config")
get_qos_wred_queue_config_parser.add_argument('port_num', type=int, help="Port Num")
get_qos_wred_queue_config_parser.add_argument('queue', type=int, help="Queue Num")

get_qos_wred_avg_queue_config_parser = get_qos_wred_parsers.add_parser('avg_q_config', help="QoS WRED Avg Queue Config")

# QoS Scheduler sub commands
get_qos_scheduler_config_parser = get_nu_qos_parsers.add_parser('scheduler', help="QoS Scheduler Config")
get_qos_scheduler_config_parser.add_argument('port_num', type=int, help="Port Num")
get_qos_scheduler_config_parser.add_argument('queue', type=int, help="Queue Num")

# QoS Ingress sub commands
get_qos_ingress_parser = get_nu_qos_parsers.add_parser('ingress', help="QoS INgress Config")
get_qos_ingress_parsers = get_qos_ingress_parser.add_subparsers(title='subcommands', help="")

get_qos_ingress_pg_parser = get_qos_ingress_parsers.add_parser('pg', help="QoS ingress pg")
get_qos_ingress_pg_parser.add_argument('port_num', type=int, help="Port Num")
get_qos_ingress_pg_parser.add_argument('pg', type=int, help="Pg Num")

get_qos_ingress_pg_map_parser = get_qos_ingress_parsers.add_parser('priority_to_pg_map', help="QoS ingress pg map")
get_qos_ingress_pg_map_parser.add_argument('port_num', type=int, help="Port Num")

# QoS Pfc sub commands
get_qos_pfc_parser = get_nu_qos_parsers.add_parser('pfc', help="QoS PFC Config")

# QoS Pfc sub commands
get_qos_arb_cfg_parser = get_nu_qos_parsers.add_parser('arb-cfg', help="QoS PFC Config")

# QoS xoff status
get_qos_xoff_status_parser = get_nu_qos_parsers.add_parser('xoff_status', help="QoS xoff status")
get_qos_xoff_status_parser.add_argument('port_num', type=int, help="Port Num")
get_qos_xoff_status_parser.add_argument('pg', type=int, help="PG Num")

# ------------------------------------------------------------------------------------------------
# Get qos HNU parser
get_hnu_qos_parsers = get_hnu_qos_parser.add_subparsers(title="subcommands", help="")

get_hnu_qos_egress_parser = get_hnu_qos_parsers.add_parser('egress', help="QoS Egress Buffers")
get_hnu_qos_egress_parsers = get_hnu_qos_egress_parser.add_subparsers(title='subcommands', help="")

get_hnu_qos_egress_buffer_pool_parser = get_hnu_qos_egress_parsers.add_parser('buffer_pool', help="QoS Egress Buffer Pool")

get_hnu_qos_egress_port_buffer_parser = get_hnu_qos_egress_parsers.add_parser('port_buffer', help="QoS Egress Port Buffer")
get_hnu_qos_egress_port_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")

get_hnu_qos_egress_queue_buffer_parser = get_hnu_qos_egress_parsers.add_parser('queue_buffer', help="QoS Egress Queue Buffer")
get_hnu_qos_egress_queue_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
get_hnu_qos_egress_queue_buffer_parser.add_argument('queue', type=int, help="Egress Queue Num")

get_hnu_qos_egress_priority_map_parser = get_hnu_qos_egress_parsers.add_parser('queue_to_priority_map', help="QoS egress queue map")
get_hnu_qos_egress_priority_map_parser.add_argument('port_num', type=int, help="Port Num")

# QoS ECN sub commands
get_hnu_qos_ecn_parser = get_hnu_qos_parsers.add_parser('ecn', help="QoS ECN Config")
get_hnu_qos_ecn_parsers = get_hnu_qos_ecn_parser.add_subparsers(title='subcommands', help="")

get_hnu_qos_ecn_glb_sh_thresh_parser = get_hnu_qos_ecn_parsers.add_parser('glb_sh_thresh', help="QoS ECN glb sh threshold")

get_hnu_qos_ecn_profile_parser = get_hnu_qos_ecn_parsers.add_parser('profile', help="QoS ECN Profile")
get_hnu_qos_ecn_profile_parser.add_argument('prof_num', type=int, help="Profile num")

get_hnu_qos_ecn_prob_parser = get_hnu_qos_ecn_parsers.add_parser('prob', help="QoS ECN Prob")
get_hnu_qos_ecn_prob_parser.add_argument('prob_idx', type=int, help="Prob index")

# QoS WRED sub commands
get_hnu_qos_wred_parser = get_hnu_qos_parsers.add_parser('wred', help="QoS WRED Config")
get_hnu_qos_wred_parsers = get_hnu_qos_wred_parser.add_subparsers(title='subcommands', help="")

get_hnu_qos_wred_profile_parser = get_hnu_qos_wred_parsers.add_parser('profile', help="QoS WRED Profile")
get_hnu_qos_wred_profile_parser.add_argument('prof_num', type=int, help="Profile num")

get_hnu_qos_wred_prob_parser = get_hnu_qos_wred_parsers.add_parser('prob', help="QoS WRED Prob")
get_hnu_qos_wred_prob_parser.add_argument('prob_idx', type=int, help="Prob index")

get_hnu_qos_wred_queue_config_parser = get_hnu_qos_wred_parsers.add_parser('queue_config', help="QoS WRED Queue Config")
get_hnu_qos_wred_queue_config_parser.add_argument('port_num', type=int, help="Port Num")
get_hnu_qos_wred_queue_config_parser.add_argument('queue', type=int, help="Queue Num")

get_hnu_qos_wred_avg_queue_config_parser = get_hnu_qos_wred_parsers.add_parser('avg_q_config', help="QoS WRED Avg Queue Config")

# QoS Scheduler sub commands
get_hnu_qos_scheduler_config_parser = get_hnu_qos_parsers.add_parser('scheduler', help="QoS Scheduler Config")
get_hnu_qos_scheduler_config_parser.add_argument('port_num', type=int, help="Port Num")
get_hnu_qos_scheduler_config_parser.add_argument('queue', type=int, help="Queue Num")

# QoS Ingress sub commands
get_hnu_qos_ingress_parser = get_hnu_qos_parsers.add_parser('ingress', help="QoS INgress Config")
get_hnu_qos_ingress_parsers = get_hnu_qos_ingress_parser.add_subparsers(title='subcommands', help="")

get_hnu_qos_ingress_pg_parser = get_hnu_qos_ingress_parsers.add_parser('pg', help="QoS ingress pg")
get_hnu_qos_ingress_pg_parser.add_argument('port_num', type=int, help="Port Num")
get_hnu_qos_ingress_pg_parser.add_argument('pg', type=int, help="Pg Num")

get_hnu_qos_ingress_pg_map_parser = get_hnu_qos_ingress_parsers.add_parser('priority_to_pg_map', help="QoS ingress pg map")
get_hnu_qos_ingress_pg_map_parser.add_argument('port_num', type=int, help="Port Num")

# QoS Pfc sub commands
get_hnu_qos_pfc_parser = get_hnu_qos_parsers.add_parser('pfc', help="QoS PFC Config")

# QoS Pfc sub commands
get_hnu_qos_arb_cfg_parser = get_hnu_qos_parsers.add_parser('arb-cfg', help="QoS PFC Config")

# QoS xoff status
get_hnu_qos_xoff_status_parser = get_hnu_qos_parsers.add_parser('xoff_status', help="QoS xoff status")
get_hnu_qos_xoff_status_parser.add_argument('port_num', type=int, help="Port Num")
get_hnu_qos_xoff_status_parser.add_argument('pg', type=int, help="PG Num")

# -----------------------------------------------------------------------------------------------------
# Qos hnu set commands
set_hnu_qos_parsers = set_hnu_qos_parser.add_subparsers(title="subcommands", help="")

set_hnu_qos_egress_parser = set_hnu_qos_parsers.add_parser('egress', help="QoS Egress Buffers")
set_hnu_qos_egress_parsers = set_hnu_qos_egress_parser.add_subparsers(title='subcommands', help="")

set_hnu_qos_egress_buffer_pool_parser = set_hnu_qos_egress_parsers.add_parser('buffer_pool', help="QoS Egress Buffer Pool")
set_hnu_qos_egress_buffer_pool_parser.add_argument('-sf_thr', type=int, help="Egress Buffer Pool sf_thr", default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-sx_thr', type=int, help="Egress Buffer Pool sx_thr", default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-df_thr', type=int, help="Egress Buffer Pool df_thr", default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-dx_thr', type=int, help="Egress Buffer Pool dx_thr", default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-fcp_thr', type=int, help="Egress Buffer Pool fcp_thr", default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-nonfcp_thr', type=int, help="Egress Buffer Pool nonfcp_thr")
set_hnu_qos_egress_buffer_pool_parser.add_argument('-sample_copy_thr', type=int, help="Egress Buffer Pool sample_copy_thr",
                                               default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-sf_xoff_thr', type=int, help="Egress Buffer Pool sf_xoff_thr",
                                               default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-fcp_xoff_thr', type=int, help="Egress Buffer Pool fcp_xoff_thr",
                                               default=None)
set_hnu_qos_egress_buffer_pool_parser.add_argument('-nonfcp_xoff_thr', type=int, help="Egress Buffer Pool nonfcp_xoff_thr",
                                               default=None)

set_hnu_qos_egress_port_buffer_parser = set_hnu_qos_egress_parsers.add_parser('port_buffer', help="QoS Egress Port Buffer")
set_hnu_qos_egress_port_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
set_hnu_qos_egress_port_buffer_parser.add_argument('-min_thr', type=int, help="Egress Port Buffer min_thr", default=None)
set_hnu_qos_egress_port_buffer_parser.add_argument('-shared_thr', type=int, help="Egress Port Buffer shared_thr",
                                               default=None)

set_hnu_qos_egress_queue_buffer_parser = set_hnu_qos_egress_parsers.add_parser('queue_buffer', help="QoS Egress Queue Buffer")
set_hnu_qos_egress_queue_buffer_parser.add_argument('port_num', type=int, help="Egress Port Num")
set_hnu_qos_egress_queue_buffer_parser.add_argument('queue', type=int, help="Egress Queue num")
set_hnu_qos_egress_queue_buffer_parser.add_argument('-min_thr', type=int, help="Egress Queue Buffer min_thr",
                                                default=None)
set_hnu_qos_egress_queue_buffer_parser.add_argument('-static_shared_thr_green', type=int,
                                                help="Egress Queue Buffer static_shared_thr_green",
                                                default=None)
set_hnu_qos_egress_queue_buffer_parser.add_argument('-dynamic_enable', type=int, help="Egress Queue Buffer dynamic_enable",
                                                default=None)
set_hnu_qos_egress_queue_buffer_parser.add_argument('-shared_thr_alpha', type=int,
                                                help="Egress Queue Buffer shared_thr_alpha",
                                                default=None)
set_hnu_qos_egress_queue_buffer_parser.add_argument('-shared_thr_offset_yellow', type=int,
                                                help="Egress Queue Buffer shared_thr_offset_yellow",
                                                default=None)
set_hnu_qos_egress_queue_buffer_parser.add_argument('-shared_thr_offset_red', type=int,
                                                help="Egress Queue Buffer shared_thr_offset_red",
                                                default=None)

set_hnu_qos_egress_priority_map_parser = set_hnu_qos_egress_parsers.add_parser('queue_to_priority_map', help="QoS egress priority map")
set_hnu_qos_egress_priority_map_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_egress_priority_map_parser.add_argument('-map_list', nargs='+', help="QoS egress map list E.g [1, 2, 3....N] \n "
                                                                        "Where n is number of queues, n = 16 for "
                                                                        "FPG ports and n = 8 for EPG ports \n"
                                                                        "Please specify space separated list for E.g \n"
                                                                        "set nu qos egress queue_to_priority_map 6 -map-list 1 2 3 4 5 6 7 7",
                                           default=None)

# QoS ECN sub commands
set_hnu_qos_ecn_parser = set_hnu_qos_parsers.add_parser('ecn', help="QoS ECN Config")
set_hnu_qos_ecn_parsers = set_hnu_qos_ecn_parser.add_subparsers(title='subcommands', help="")

set_hnu_qos_ecn_glb_sh_thresh_parser = set_hnu_qos_ecn_parsers.add_parser('glb_sh_thresh', help="QoS ECN glb sh threshold")
set_hnu_qos_ecn_glb_sh_thresh_parser.add_argument('-en', type=int, help="glb_sh_thresh en", default=None)
set_hnu_qos_ecn_glb_sh_thresh_parser.add_argument('-green', type=int, help="glb_sh_thresh green", default=None)
set_hnu_qos_ecn_glb_sh_thresh_parser.add_argument('-yellow', type=int, help="glb_sh_thresh yellow", default=None)
set_hnu_qos_ecn_glb_sh_thresh_parser.add_argument('-red', type=int, help="glb_sh_thresh red", default=None)

set_hnu_qos_ecn_profile_parser = set_hnu_qos_ecn_parsers.add_parser('profile', help="QoS ECN Profile")
set_hnu_qos_ecn_profile_parser.add_argument('prof_num', type=int, help="Profile num")
set_hnu_qos_ecn_profile_parser.add_argument('-min_thr', type=int, help="Profile min threshold", default=None)
set_hnu_qos_ecn_profile_parser.add_argument('-max_thr', type=int, help="Profile max threshold", default=None)
set_hnu_qos_ecn_profile_parser.add_argument('-ecn_prob_index', type=int, help="Profile ECN prob index", default=None)

set_hnu_qos_ecn_prob_parser = set_hnu_qos_ecn_parsers.add_parser('prob', help="QoS ECN Prob")
set_hnu_qos_ecn_prob_parser.add_argument('prob_idx', type=int, help="Prob index")
set_hnu_qos_ecn_prob_parser.add_argument('-prob', type=int, help="Prob", default=None)

# QoS WRED sub commands
set_hnu_qos_wred_parser = set_hnu_qos_parsers.add_parser('wred', help="QoS WRED Config")
set_hnu_qos_wred_parsers = set_hnu_qos_wred_parser.add_subparsers(title='subcommands', help="")

set_hnu_qos_wred_profile_parser = set_hnu_qos_wred_parsers.add_parser('profile', help="QoS WRED Profile")
set_hnu_qos_wred_profile_parser.add_argument('prof_num', type=int, help="Profile num")
set_hnu_qos_wred_profile_parser.add_argument('-min_thr', type=int, help="Profile min threshold", default=None)
set_hnu_qos_wred_profile_parser.add_argument('-max_thr', type=int, help="Profile max threshold", default=None)
set_hnu_qos_wred_profile_parser.add_argument('-wred_prob_index', type=int, help="Profile WRED prob index", default=None)

set_hnu_qos_wred_prob_parser = set_hnu_qos_wred_parsers.add_parser('prob', help="QoS WRED Prob")
set_hnu_qos_wred_prob_parser.add_argument('prob_idx', type=int, help="Prob index")
set_hnu_qos_wred_prob_parser.add_argument('-prob', type=int, help="Prob", default=None)

set_hnu_qos_wred_queue_config_parser = set_hnu_qos_wred_parsers.add_parser('queue_config', help="QoS WRED Queue Config")
set_hnu_qos_wred_queue_config_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_wred_queue_config_parser.add_argument('queue', type=int, help="Queue Num")
set_hnu_qos_wred_queue_config_parser.add_argument('-wred_en', type=int, help="QoS WRED Queue Enable", default=None)
set_hnu_qos_wred_queue_config_parser.add_argument('-wred_weight', type=int, help="QoS WRED Queue weight", default=None)
set_hnu_qos_wred_queue_config_parser.add_argument('-wred_prof_num', type=int, help="QoS WRED Queue Profile Num",
                                              default=None)
set_hnu_qos_wred_queue_config_parser.add_argument('-ecn_en', type=int, help="QoS WRED Queue ECN enable", default=None)
set_hnu_qos_wred_queue_config_parser.add_argument('-ecn_prof_num', type=int, help="QoS WRED Queue ECN Prof num",
                                              default=None)

set_hnu_qos_wred_avg_queue_config_parser = set_hnu_qos_wred_parsers.add_parser('avg_q_config', help="QoS WRED Avg Queue Config")
set_hnu_qos_wred_avg_queue_config_parser.add_argument('-q_avg_en', type=int, help="QoS WRED Avg Queue Enable",
                                                  default=None)
set_hnu_qos_wred_avg_queue_config_parser.add_argument('-cap_avg_sz', type=int, help="QoS WRED Avg Queue cap_avg_sz",
                                                  default=None)
set_hnu_qos_wred_avg_queue_config_parser.add_argument('-avg_period', type=int, help="QoS WRED Avg Queue Period",
                                                  default=None)

# QoS Scheduler sub commands
set_hnu_qos_scheduler_parser = set_hnu_qos_parsers.add_parser('scheduler', help="QoS Scheduler Config")
set_hnu_qos_scheduler_parsers = set_hnu_qos_scheduler_parser.add_subparsers(title='subcommands', help="")

# dwrr
set_hnu_qos_scheduler_dwrr_parser = set_hnu_qos_scheduler_parsers.add_parser('dwrr', help="QoS Scheduler dwrr Config")
set_hnu_qos_scheduler_dwrr_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_scheduler_dwrr_parser.add_argument('queue', type=int, help="Queue Num")
set_hnu_qos_scheduler_dwrr_parser.add_argument('weight', type=int, help="Weight")

# Shaper
set_hnu_qos_scheduler_shaper_parser = set_hnu_qos_scheduler_parsers.add_parser('shaper', help="QoS Scheduler Shaper Config")
set_hnu_qos_scheduler_shaper_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_scheduler_shaper_parser.add_argument('queue', type=int, help="Queue Num")
set_hnu_qos_scheduler_shaper_parser.add_argument('-enable', type=int, help="Shaper enable/disable")
set_hnu_qos_scheduler_shaper_parser.add_argument('-type', type=int, help="Shaper type. 0=min_rate, 1=max_rate")
set_hnu_qos_scheduler_shaper_parser.add_argument('-rate', type=int, help="Shaper rate in bits")
set_hnu_qos_scheduler_shaper_parser.add_argument('-thresh', type=int, help="Shaper Threshold")

# Strict priority
set_hnu_qos_scheduler_strict_priority_parser = set_hnu_qos_scheduler_parsers.add_parser('strict_priority',
                                                                                help="QoS Scheduler Strict "
                                                                                     "Priority Config")
set_hnu_qos_scheduler_strict_priority_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_scheduler_strict_priority_parser.add_argument('queue', type=int, help="Queue Num")
set_hnu_qos_scheduler_strict_priority_parser.add_argument('-strict_priority_enable', type=int, help="QoS Scheduler Strict "
                                                                                                "Priority enable",
                                                      default=None)
set_hnu_qos_scheduler_strict_priority_parser.add_argument('-extra_bandwidth', type=int, help="QoS Scheduler Strict Priority "
                                                                                         "Extra Bandawidth",
                                                      default=None)

# QoS Ingress sub commands
set_hnu_qos_ingress_parser = set_hnu_qos_parsers.add_parser('ingress', help="QoS INgress Config")
set_hnu_qos_ingress_parsers = set_hnu_qos_ingress_parser.add_subparsers(title='subcommands', help="")

set_hnu_qos_ingress_pg_parser = set_hnu_qos_ingress_parsers.add_parser('pg', help="QoS ingress pg")
set_hnu_qos_ingress_pg_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_ingress_pg_parser.add_argument('pg', type=int, help="Pg Num")
set_hnu_qos_ingress_pg_parser.add_argument('-min_thr', type=int, help="QoS ingress min thr", default=None)
set_hnu_qos_ingress_pg_parser.add_argument('-shared_thr', type=int, help="QoS ingress shared thr", default=None)
set_hnu_qos_ingress_pg_parser.add_argument('-headroom_thr', type=int, help="QoS ingress headroom_thr", default=None)
set_hnu_qos_ingress_pg_parser.add_argument('-xoff_enable', type=int, help="QoS ingress xoff_enable", default=None)
set_hnu_qos_ingress_pg_parser.add_argument('-shared_xon_thr', type=int, help="QoS ingress shared_xon_thr", default=None)

set_hnu_qos_ingress_pg_map_parser = set_hnu_qos_ingress_parsers.add_parser('priority_to_pg_map', help="QoS ingress pg map")
set_hnu_qos_ingress_pg_map_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_ingress_pg_map_parser.add_argument('-map_list', nargs='+', help="QoS ingress map list E.g [1, 2, 3....N] \n "
                                                                        "Where n is number of priorities, n = 16 for "
                                                                        "FPG ports and n = 8 for EPG ports \n"
                                                                        "Please specify space separated list for E.g \n"
                                                                        "set nu qos ingress priority_to_pg_map 6 -map-list 1 2 3 4 5 6 7 7",
                                           default=None)
# QoS Pfc sub commands
set_hnu_qos_pfc_parser = set_hnu_qos_parsers.add_parser('pfc', help="QoS PFC Config")
set_hnu_qos_pfc_parsers = set_hnu_qos_pfc_parser.add_subparsers(title="subcommands", help="")
set_hnu_qos_pfc_enable_parser = set_hnu_qos_pfc_parsers.add_parser('enable', help="QoS PFC Enable")
set_hnu_qos_pfc_disable_parser = set_hnu_qos_pfc_parsers.add_parser('disable', help="QoS PFC Disable")

# QoS arb cfg sub commands
set_hnu_qos_arb_cfg_parser = set_hnu_qos_parsers.add_parser('arb_cfg', help="QoS arb cfg Config")
set_hnu_qos_arb_cfg_parser.add_argument('en', type=int, help="QoS arb cfg Enable")

# QoS xoff status
set_hnu_qos_xoff_status_parser = set_hnu_qos_parsers.add_parser('xoff_status', help="QoS xoff status")
set_hnu_qos_xoff_status_parser.add_argument('port_num', type=int, help="Port Num")
set_hnu_qos_xoff_status_parser.add_argument('pg', type=int, help="PG Num")
set_hnu_qos_xoff_status_parser.add_argument('-status', type=int, help="QoS xoff_status", default=None)

get_port_speed_parser = get_nu_port_parsers.add_parser('speed', help="Get port speed")
get_port_speed_parser.add_argument('port_num', type=int, help="port_num")
get_port_speed_parser.add_argument('shape', type=int, help='shape')
# -----------------------------------------------------------------------------------------------
# Get system sub commands
get_system_parsers = get_system_parser.add_subparsers(title="subcommands", help="")
get_system_params_parser = get_system_parsers.add_parser('params', help="Get System Params")
get_system_time_interval_parser = get_system_parsers.add_parser('time_interval', help="Get Time interval between "
                                                                                      "stats iterations")
# Get Syslog Levels
get_system_params_subparsers = get_system_params_parser.add_subparsers(title="subcommands", help="")
get_system_params_syslog_parser = get_system_params_subparsers.add_parser('syslog', help="Get System Syslog Params")

# ============================================================================================================

# Clear stats sub commands
base_clear_parser = ArgumentParser(prog="clear")
base_clear_subparsers = base_clear_parser.add_subparsers(title="subcommands", help="")
clear_stats_parser = base_clear_subparsers.add_parser('stats', help="Clear stats")

# Clear NU stats sub commands
clear_nu_subparsers = clear_stats_parser.add_subparsers(title='subcommands', help="")
clear_nu_stats_parser = clear_nu_subparsers.add_parser('nu', help="Clear NU stats")
clear_nu_stats_subparsers = clear_nu_stats_parser.add_subparsers(title='subcommands', help="")

# Clear Port Stats
clear_nu_port_stats_parser = clear_nu_stats_subparsers.add_parser('port', help="Clear Port Stats")
clear_nu_port_stats_parser.add_argument('port_num', type=int, help="port num")
clear_nu_port_stats_parser.add_argument('shape', type=int, help="shape")

# Clear FWD stats
clear_nu_fwd_stats_parser = clear_nu_stats_subparsers.add_parser('fwd', help="Clear FWD Stats")

# Clear ERP stats
clear_nu_erp_stats_parser = clear_nu_stats_subparsers.add_parser('erp', help="Clear ERP Stats")

# Clear Parser stats 
clear_nu_parser_stats_parser = clear_nu_stats_subparsers.add_parser('parser', help="Clear Parser Stats")

# Clear FWD stats
clear_nu_nwqm_stats_parser = clear_nu_stats_subparsers.add_parser('nwqm', help="Clear NWQM Stats")

# Clear ERP stats
clear_nu_vppkts_stats_parser = clear_nu_stats_subparsers.add_parser('vppkts', help="Clear VPPKTS Stats")

# Clear ALL NU stats
clear_nu_all_stats_parser = clear_nu_stats_subparsers.add_parser('all', help="Clear ALL Stats")

# ============================================================================================================

# peek stats sub commands
base_peek_parser = ArgumentParser(prog="peek")
base_peek_subparsers = base_peek_parser.add_subparsers(title="subcommands", help="")
peek_stats_parser = base_peek_subparsers.add_parser('stats', help="Peek stats")
peek_stats_parsers = peek_stats_parser.add_subparsers(title="subcommands", help="")

# Meter stats
peek_meter_stats_parser = peek_stats_parsers.add_parser('meter', help="NU Meter Stats")
peek_meter_stats_parsers = peek_meter_stats_parser.add_subparsers(title='subcommands', help="")
peek_meter_nu_stats_parser = peek_meter_stats_parsers.add_parser('nu', help='Peek meter erp stats')
peek_meter_nu_stats_parser.add_argument('-bank', type=int, help="Meter bank")
peek_meter_nu_stats_parser.add_argument('-index', type=int, help="Meter Index")
peek_meter_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)
# Erp meter stats
peek_meter_erp_stats_parser = peek_meter_stats_parsers.add_parser('erp', help='Peek meter erp stats')
peek_meter_erp_stats_parser.add_argument('-bank', type=int, help="Meter bank")
peek_meter_erp_stats_parser.add_argument('-index', type=int, help="Meter ID")
peek_meter_erp_stats_parser.add_argument('-grep', help="Grep regex", default=None)

# Fpg stats
peek_fpg_stats_parser = peek_stats_parsers.add_parser('fpg', help="NU Peek FPG Port stats")
peek_fpg_subparsers = peek_fpg_stats_parser.add_subparsers(title='subcommands', help="")
peek_nu_fpg_stats_parser = peek_fpg_subparsers.add_parser('nu', help="Peek NU FPG stats")
peek_nu_fpg_stats_parser.add_argument('port_num', type=int, help="FPG Port num")
peek_nu_fpg_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_hnu_fpg_stats_parser = peek_fpg_subparsers.add_parser('hnu', help="Peek HNU FPG stats")
peek_hnu_fpg_stats_parser.add_argument('port_num', type=int, help="FPG Port num")
peek_hnu_fpg_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)


# PSW Stats
peek_psw_stats_parser = peek_stats_parsers.add_parser('psw', help="NU Peek PSW Stats")
peek_psw_stats_parsers = peek_psw_stats_parser.add_subparsers(title='subcommands', help="")

peek_psw_nu_stats_parser = peek_psw_stats_parsers.add_parser('nu', help="NU Peek PSW Stats")
peek_psw_hnu_stats_parser = peek_psw_stats_parsers.add_parser('hnu', help="NU Peek PSW Stats")

peek_psw_nu_stats_parser.add_argument('-port_num', type=int, help="Port num", default=None)
peek_psw_nu_stats_parser.add_argument('-queues', nargs='+', help="Queue List", default=None)
peek_psw_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_psw_hnu_stats_parser.add_argument('-port_num', type=int, help="Port num", default=None)
peek_psw_hnu_stats_parser.add_argument('-queues', nargs='+', help="Queue List", default=None)
peek_psw_hnu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# VP Stats
peek_vp_stats_parser = peek_stats_parsers.add_parser('vppkts', help="NU Peek VP Stats")
peek_vp_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# FCP Stats
peek_fcp_stats_parser = peek_stats_parsers.add_parser('fcp', help="NU Peek FCP Stats")
peek_fcp_stats_parsers = peek_fcp_stats_parser.add_subparsers(title='subcommands', help="")
peek_fcp_nu_stats_parser = peek_fcp_stats_parsers.add_parser('nu', help="NU Peek FCP stats (Global)")
peek_fcp_nu_stats_parser.add_argument('-tunnel', type=int, help="Tunnel ID", default=None)
peek_fcp_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)


# WRO Stats
peek_wro_stats_parser = peek_stats_parsers.add_parser('wro', help="NU Peek WRO Stats")
peek_wro_stats_parsers = peek_wro_stats_parser.add_subparsers(title='subcommands', help="")

# WRO NU stats
peek_wro_nu_stats_parser = peek_wro_stats_parsers.add_parser('nu', help="Peek NU wro stats")
peek_wro_nu_stats_parser.add_argument('-tunnel', type=int, help="Tunnel ID", default=None)
peek_wro_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# WRO HNU stats
peek_wro_hnu_stats_parser = peek_wro_stats_parsers.add_parser('hnu', help="Peek HNU wro stats")
peek_wro_hnu_stats_parser.add_argument('-tunnel', type=int, help="Tunnel ID", default=None)
peek_wro_hnu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# fwd stats
peek_fwd_stats_parser = peek_stats_parsers.add_parser('fwd', help="NU Peek FWD Stats")
peek_fwd_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# erp stats
peek_erp_stats_parser = peek_stats_parsers.add_parser('erp', help="NU Peek Erp Stats")
peek_erp_stats_parsers = peek_erp_stats_parser.add_subparsers(title='subcommands', help="")

# Erp HNU stats
peek_erp_hnu_stats_parser = peek_erp_stats_parsers.add_parser('hnu', help="Peek HNU erp stats")
peek_erp_hnu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Erp NU stats
peek_erp_nu_stats_parser = peek_erp_stats_parsers.add_parser('nu', help="Peek HU erp stats")
peek_erp_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# erp stats
peek_etp_stats_parser = peek_stats_parsers.add_parser('etp', help="NU Peek Etp Stats")
peek_etp_stats_parsers = peek_etp_stats_parser.add_subparsers(title='subcommands', help="")

# Erp HNU stats
peek_etp_hnu_stats_parser = peek_etp_stats_parsers.add_parser('hnu', help="Peek HNU etp stats")
peek_etp_hnu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Erp NU stats
peek_etp_nu_stats_parser = peek_etp_stats_parsers.add_parser('nu', help="Peek HU etp stats")
peek_etp_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Erp NU Flex stats
peek_erp_flex_stats_parser = peek_erp_stats_parsers.add_parser('flex', help="Peek NU Flex erp stats")
peek_erp_flex_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Parser NU stats
peek_prp_stats_parser = peek_stats_parsers.add_parser('parser', help="NU Peek Parser Stats")
peek_prp_stats_parsers = peek_prp_stats_parser.add_subparsers(title='subcommands', help="")

peek_parser_nu_stats_parser = peek_prp_stats_parsers.add_parser('nu', help="Peek Parser NU Stats")
peek_parser_nu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_parser_hnu_stats_parser = peek_prp_stats_parsers.add_parser('hnu', help="Peek Parser HNU Stats")
peek_parser_hnu_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Peek WRED ECN stats
peek_wred_ecn_stats_parser = peek_stats_parsers.add_parser('wred_ecn', help="Peek QoS WRED ECN Stats")
peek_wred_ecn_stats_parser.add_argument('port_num', type=int, help="Port Num")
peek_wred_ecn_stats_parser.add_argument('queue_num', type=int, help="Queue Num")
peek_wred_ecn_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Peek NU SFG Stats
peek_sfg_stats_parser = peek_stats_parsers.add_parser('sfg', help="Peek SFG Stats")
peek_sfg_stats_parsers = peek_sfg_stats_parser.add_subparsers(title='subcommands', help="")

# Nu SFG stats
peek_nu_sfg_stats_parser = peek_sfg_stats_parsers.add_parser('nu', help="Peek NU SFG stats")
peek_nu_sfg_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Hnu SFG stats
peek_hnu_sfg_stats_parser = peek_sfg_stats_parsers.add_parser('hnu', help="Peek HNU SFG stats")
peek_hnu_sfg_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Per VP stats
peek_per_vp_stats_parser = peek_stats_parsers.add_parser('per_vp', help="Peek Per VP Stats")
peek_per_vp_stats_parser.add_argument('-cluster_id', type=int, help="Cluster_id 0..7", default=None)
peek_per_vp_stats_parser.add_argument('-core_id', type=int, help="Core_id 0..5", default=None)
peek_per_vp_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# New params
peek_per_vp_stats_parser.add_argument('-rx', type=bool, help="Print Wus received", default=False)
peek_per_vp_stats_parser.add_argument('-tx', type=bool, help="Print Wus sent", default=False)
peek_per_vp_stats_parser.add_argument('-q', type=bool, help="Print Wus q depth", default=False)
peek_per_vp_stats_parser.add_argument('-pp', type=bool, help="PrettyPrint tabular", default=False)

# nwqm stats
peek_nwqm_stats_parser = peek_stats_parsers.add_parser('nwqm', help="Peek nwqm stats")
peek_nwqm_stats_parser.add_argument('-grep', help="Grep Regex pattern", default=None)

# nwqm stats
peek_nwqm_hnu_stats_parser = peek_stats_parsers.add_parser('nwqm_hnu', help="Peek nwqm hnu stats")
peek_nwqm_hnu_stats_parser.add_argument('-grep', help="Grep Regex pattern", default=None)

# fae stats
peek_fae_stats_parser = peek_stats_parsers.add_parser('fae', help="Peek fae stats")
peek_fae_stats_parser.add_argument('-grep', help="Grep Regex pattern", default=None)

# hbm stats
peek_hbm_stats_parser = peek_stats_parsers.add_parser('hbm', help="Peek hbm stats")
peek_hbm_stats_parser.add_argument('-muh', help="muh id", default=None)
peek_hbm_stats_parser.add_argument('-grep', help="Grep Regex pattern", default=None)

# Nu mpg stats
peek_mpg_stats_parser = peek_stats_parsers.add_parser('mpg', help='Peek mpg stats')
peek_mpg_stats_parser.add_argument('-grep', help="Grep Regex pattern", default=None)

# Nu per vppkts
peek_pervppkts_stats_parser = peek_stats_parsers.add_parser('pervppkts', help='Peek per vppkts stats')
peek_pervppkts_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID")
peek_pervppkts_stats_parser.add_argument('-core_id', type=int, help="Core id", default=None)
#peek_pervppkts_stats_parser.add_argument('-vp_num', type=int, help="VP number", default=None)
peek_pervppkts_stats_parser.add_argument('-grep', help='Grep regex pattern', default=None)

# nhp stats
peek_nhp_stats_parser = peek_stats_parsers.add_parser('nhp', help="Peek nhp stats")
peek_nhp_stats_parser.add_argument('-grep', help='Grep regex pattern', default=None)

# sse stats
peek_sse_stats_parser = peek_stats_parsers.add_parser('sse', help='Peek sse stats')
peek_sse_stats_parser.add_argument('-grep', help='Grep regex pattern', default=None)

# Resource stats
peek_resource_stats_parser = peek_stats_parsers.add_parser('resource', help="Resource Stats")
peek_resource_stats_parsers = peek_resource_stats_parser.add_subparsers(title='subcommands', help="")
peek_pc_resource_stats_parser = peek_resource_stats_parsers.add_parser('pc', help='Peek pc resource stats')
peek_pc_resource_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID", default=None)
peek_pc_resource_stats_parser.add_argument('-core_id', type=int, help="Core ID", default=None)
peek_pc_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_cc_resource_stats_parser = peek_resource_stats_parsers.add_parser('cc', help='Peek cc resource stats')
peek_cc_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_dma_resource_stats_parser = peek_resource_stats_parsers.add_parser('dma', help='Peek dma resource stats')
peek_dma_resource_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID", default=None)

peek_le_resource_stats_parser = peek_resource_stats_parsers.add_parser('le', help='Peek le resource stats')
peek_le_resource_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID", default=None)

peek_zip_resource_stats_parser = peek_resource_stats_parsers.add_parser('zip', help='Peek zip resource stats')
peek_zip_resource_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID", default=None)

peek_rgx_resource_stats_parser = peek_resource_stats_parsers.add_parser('rgx', help='Peek rgx resource stats')
peek_rgx_resource_stats_parser.add_argument('cluster_id', type=int, help="Cluster ID", default=None)
peek_rgx_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_hnu_resource_stats_parser = peek_resource_stats_parsers.add_parser('hnu', help='Peek hnu resource stats')
peek_hnu_resource_stats_parser.add_argument('-resource_id', type=int, help="Resource id to be specified between 0 and "
                                                                          "191", default=None)
peek_hnu_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_nu_resource_stats_parser = peek_resource_stats_parsers.add_parser('nu', help='Peek nu resource stats')
peek_nu_resource_stats_parser.add_argument('-resource_id', type=int, help="Resource id", default=None)
peek_nu_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_hu_resource_stats_parser = peek_resource_stats_parsers.add_parser('hu', help='Peek hu resource stats')
peek_hu_resource_stats_parser.add_argument('id', type=int, help="id")
peek_hu_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_hu_wqsi_resource_stats_parser = peek_resource_stats_parsers.add_parser('hu_wqsi', help='Peek hu_wqsi resource stats')
peek_hu_wqsi_resource_stats_parser.add_argument('id', type=int, help="id")
peek_hu_wqsi_resource_stats_parser.add_argument('-rid', type=int, help="Resource id", default=None)
peek_hu_wqsi_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_hu_wqse_resource_stats_parser = peek_resource_stats_parsers.add_parser('hu_wqse', help='Peek hu_wqse resource stats')
peek_hu_wqse_resource_stats_parser.add_argument('id', type=int, help="id")
peek_hu_wqse_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_dam_resource_stats_parser = peek_resource_stats_parsers.add_parser('dam', help='Peek dam resource stats')
peek_dam_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_bam_resource_stats_parser = peek_resource_stats_parsers.add_parser('bam', help='Peek bam resource stats')
peek_bam_resource_stats_parser.add_argument('-cid', help="Specify the cluster id", default=None)
peek_bam_resource_stats_parser.add_argument('-diff', help="Show diff for percent and color", default=None)
peek_bam_resource_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Eqm stats
peek_eqm_stats_parser = peek_stats_parsers.add_parser('eqm', help="EQM stats")
peek_eqm_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# funtop stats
peek_funtop_stats_parser = peek_stats_parsers.add_parser('funtop', help="Funtop stats")

# wustacks stats
peek_wustacks_stats_parser = peek_stats_parsers.add_parser('wustacks', help="Peke wustacks stats")

# wustacks stats
peek_wus_stats_parser = peek_stats_parsers.add_parser('wus', help="Peke wus stats")

# HU stats
peek_hu_stats_parser = peek_stats_parsers.add_parser('hu', help="Peek HU stats")
peek_hu_stats_parser.add_argument('-grep', help="Grep regex pattern (Grep for HU Slice)", default=None)

# malloc agent stats
peek_malloc_agent_stats_parser = peek_stats_parsers.add_parser('malloc_agent', help="Peek Malloc Agent Stats")
peek_malloc_agent_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# malloc agent non coh stats
peek_malloc_agent_non_coh_stats_parser = peek_stats_parsers.add_parser('malloc_agent_non_coh',
                                                                       help="Peek Malloc Agent Non coh Stats")
peek_malloc_agent_non_coh_stats_parser.add_argument('-grep', help="Grep regex pattern", default=None)


# Storage Peek Commands
peek_storage_parser = base_peek_subparsers.add_parser('storage', help="Peek storage")
peek_storage_parsers = peek_storage_parser.add_subparsers(title="subcommands", help="")

peek_storage_vol_parser = peek_storage_parsers.add_parser('volumes', help="Shows volumes attached to DUT")
peek_storage_vol_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Peek Stats SSDs Connected
peek_stats_ssds_parser = peek_stats_parsers.add_parser('ssds', help="Shows the SSDs connected")
peek_stats_ssds_parser.add_argument('-ssd_ids', help="List of ssd ids. specify as follows: -ssd_ids 6 7 8", default=[], nargs='+')
peek_stats_ssds_parser.add_argument('-grep', help="Grep regex pattern (Grep for filter key)", default=None)

# Peek BLT volume stats
peek_stats_blt_vol_parser = peek_stats_parsers.add_parser('blt', help="Peek BLT volume stats")
peek_stats_blt_vol_parser.add_argument('vol_id', type=str, help="Volume ID (For e.g if vol id is 0000000000003001)")

# Peek RDS volume stats
peek_stats_rds_vol_parser = peek_stats_parsers.add_parser('rds', help="Peek RDS volume stats")
peek_stats_rds_vol_parser.add_argument('vol_id', type=str, help="Volume ID (For e.g if vol id is 0000000000003001)")

# Peek stats cdu
peek_stats_cdu_parser = peek_stats_parsers.add_parser('cdu', help="Peek cdu stats")
peek_stats_cdu_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Peek stats ca
peek_stats_ca_parser = peek_stats_parsers.add_parser('ca', help="Peek ca stats")
peek_stats_ca_parser.add_argument('-grep', help="Grep regex pattern", default=None)

# Peek stats ddr
peek_stats_ddr_parser = peek_stats_parsers.add_parser('ddr', help="Peek ddr stats")
peek_stats_ddr_parser.add_argument('-grep', help="Grep regex pattern", default=None)

peek_stats_rdma_parser = peek_stats_parsers.add_parser('rdma', help='peek rdma stats')
peek_stats_rdma_parser.add_argument("hu_id", help="Hu id to look for", type=str)
peek_stats_rdma_parser.add_argument("-qpn", help="Print data only for particular qpn", default=None)
peek_stats_rdma_parser.add_argument('-grep', help="Grep for specific flow", default=None)


# peek status
peek_status_parser = base_peek_subparsers.add_parser('status', help="Peek stats")
peek_status_subparsers = peek_status_parser.add_subparsers(title='subcommands', help="")

peek_status_nhp_parser = peek_status_subparsers.add_parser('nhp', help="NHP Status")
peek_status_nhp_parser.add_argument('-grep', help="Grep regex pattern", default=None)
# ---------------------------------------------------------------------------------------------------
# show commands

# Set sub commands
base_show_parser = ArgumentParser(prog="show")
base_show_subparsers = base_show_parser.add_subparsers(title="subcommands", help="")
show_tech_parser = base_show_subparsers.add_parser('tech', help="show tech commands")
show_tech_parsers = show_tech_parser.add_subparsers(title="subcommands", help="")

show_tech_nu_parser = show_tech_parsers.add_parser('nu', help="Capture nu stats")
show_tech_nu_parser.add_argument('-filename', help="Specify a filename to save/append the output stats. "
                                                   "If not provided it will create one. The entire filepath will be "
                                                   "provided on console once commands run successfully", default=None,
                                    type=str)
show_tech_nu_parser.add_argument('-portlist', help="List of port numbers. specify as follows: -portlist 6 7 8", default=[], nargs='+')
show_tech_nu_parser.add_argument('-fcp_tunnel_id', type=int, help="FCP tunnel ID", default=None)

show_tech_hnu_parser = show_tech_parsers.add_parser('hnu', help="Capture hnu stats")
show_tech_hnu_parser.add_argument('-filename', help="Specify a filename to save/append the output stats. "
                                                   "If not provided it will create one. The entire filepath will be "
                                                   "provided on console once commands run successfully")
show_tech_hnu_parser.add_argument('-portlist', help="List of port numbers. specify as follows: -portlist 6 7 8", default=[], nargs='+')
show_tech_hnu_parser.add_argument('-fcp_tunnel_id', type=int, help="FCP tunnel ID", default=None)

show_tech_all_parser = show_tech_parsers.add_parser('all', help="Capture all stats")
show_tech_all_parser.add_argument('-filename', help="Specify a filename to save/append the output stats. "
                                                   "If not provided it will create one. The entire filepath will be "
                                                   "provided on console once commands run successfully", default=None,
                                     type=str)
show_tech_all_parser.add_argument('-portlist', help="List of port numbers. specify as follows: -portlist 6 7 8", default=[], nargs='+')
show_tech_all_parser.add_argument('-fcp_tunnel_id', type=int, help="FCP tunnel ID", default=None)


# ---------------------------------------------------------------------------------------------------
# flow commands

# flow sub commands

base_flow_parser = ArgumentParser(prog="flow")
base_flow_subparsers = base_flow_parser.add_subparsers(title="subcommands", help="")

# Flow list
flow_list_parser = base_flow_subparsers.add_parser('list', help='List flows')
flow_list_parser.add_argument("-pp", help="Pretty Print output", default=False)
flow_list_parser.add_argument("-tx", help="Only prints tx data", default=None)
flow_list_parser.add_argument("-rx", help="Only prints rx data", default=None)
flow_list_parser.add_argument("-hu_id", help="hu_id in x format", type=str, default=None)
flow_list_parser.add_argument("-hcf_id", help="hu_id.ctrlr.fn_id in x.x.x format", type=str, default=None)
flow_list_parser.add_argument('-grep', help="Grep for specific flow", default=None)

flow_list_rdma_parser = base_flow_subparsers.add_parser('list_rdma', help='list rdma flows')
flow_list_rdma_parser.add_argument("hu_id", help="Hu id to look for", type=str)
flow_list_rdma_parser.add_argument("-qpn", help="Print data only for particular qpn", default=None)
flow_list_rdma_parser.add_argument('-grep', help="Grep for specific flow", default=None)

# Flow blocked
flow_blocked_parser = base_flow_subparsers.add_parser('blocked', help='blocked flows')
flow_blocked_parser.add_argument('-grep', help="Grep for specific flow", default=None)

# ==================================================================================================

base_debug_parser = ArgumentParser(prog="debug")
base_debug_subparsers = base_debug_parser.add_subparsers(title="subcommands", help="")

vp_util_parser = base_debug_subparsers.add_parser("vp_util", help="Display vp utilization")
vp_util_parser.add_argument("-cluster_id", help="Specify cluster id", type=int)
vp_util_parser.add_argument("-core_id", help="Specify core id", type=int)
vp_util_parser.add_argument("-pp", help="Pretty Print in tabular")
vp_util_parser.add_argument('-grep', help="Grep on particular field")