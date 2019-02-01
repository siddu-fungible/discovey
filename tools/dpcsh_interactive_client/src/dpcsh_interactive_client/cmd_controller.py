from dpc_shell import DpcShell
from dpc_client import DpcClient
from cmd2 import Cmd, with_argparser
from nu_commands import *
from cmd_arg_parser import *
import sys

class CmdController(Cmd):

    def __init__(self, target_ip, target_port, verbose=False):
        Cmd.__init__(self)
        self.prompt = "(dpcsh) "
        self.dpc_client = DpcClient(target_ip=target_ip, target_port=target_port, verbose=verbose)
        self._port_cmd_obj = PortCommands(dpc_client=self.dpc_client)
        self._sys_cmd_obj = SystemCommands(dpc_client=self.dpc_client)
        self._qos_cmd_obj = QosCommands(dpc_client=self.dpc_client)
        self._peek_cmd_obj = PeekCommands(dpc_client=self.dpc_client)
        self._clear_cmd_obj = NuClearCommands(dpc_client=self.dpc_client)
        self._sample_cmd_obj = SampleCommands(dpc_client=self.dpc_client)
        self._show_cmd_obj = ShowCommands(dpc_client=self.dpc_client)

    def set_system_time_interval(self, args):
        time_interval = args.time
        self._sys_cmd_obj.time_interval(time_interval=time_interval)

    def get_system_time_interval(self, args):
        self._sys_cmd_obj.time_interval(time_interval=None)

    def set_port_mtu(self, args):
        port_num = args.port_num
        shape = args.shape
        mtu_value = args.mtu_value
        self._port_cmd_obj.port_mtu(port_num=port_num, shape=shape, mtu=mtu_value)

    def get_port_mtu(self, args):
        port_num = args.port_num
        shape = args.shape
        self._port_cmd_obj.port_mtu(port_num=port_num, shape=shape)

    def enable_port(self, args):
        self._port_cmd_obj.enable_disable_port(port_num=args.port_num, shape=args.shape)

    def disable_port(self, args):
        self._port_cmd_obj.enable_disable_port(port_num=args.port_num, shape=args.shape, enable=False)

    def enable_port_link_pause(self, args):
        self._port_cmd_obj.enable_disable_link_pause(port_num=args.port_num, shape=args.shape)

    def disable_port_link_pause(self, args):
        self._port_cmd_obj.enable_disable_link_pause(port_num=args.port_num, shape=args.shape, enable=False)

    def enable_port_tx_link_pause(self, args):
        self._port_cmd_obj.enable_disable_tx_link_pause(port_num=args.port_num, shape=args.shape)

    def disable_port_tx_link_pause(self, args):
        self._port_cmd_obj.enable_disable_tx_link_pause(port_num=args.port_num, shape=args.shape, enable=False)

    def set_port_pause_quanta(self, args):
        self._port_cmd_obj.port_pause_quanta(port_num=args.port_num, shape=args.shape, quanta=args.quanta)

    def get_port_pause_quanta(self, args):
        self._port_cmd_obj.port_pause_quanta(port_num=args.port_num, shape=args.shape)

    def set_port_pause_threshold(self, args):
        self._port_cmd_obj.port_pause_threshold(port_num=args.port_num, shape=args.shape, threshold=args.threshold)

    def get_port_pause_threshold(self, args):
        self._port_cmd_obj.port_pause_threshold(port_num=args.port_num, shape=args.shape)

    def enable_port_pfc(self, args):
        self._port_cmd_obj.enable_disable_pfc(port_num=args.port_num, shape=args.shape)

    def disable_port_pfc(self, args):
        self._port_cmd_obj.enable_disable_pfc(port_num=args.port_num, shape=args.shape, enable=False)

    def enable_port_tx_pfc(self, args):
        self._port_cmd_obj.enable_disable_tx_pfc(port_num=args.port_num, shape=args.shape, class_num=args.class_num)

    def disable_port_tx_pfc(self, args):
        self._port_cmd_obj.enable_disable_tx_pfc(port_num=args.port_num, shape=args.shape, enable=False,
                                                 class_num=args.class_num)

    def set_port_pfc_quanta(self, args):
        self._port_cmd_obj.port_pfc_quanta(port_num=args.port_num, shape=args.shape, quanta=args.quanta,
                                           class_num=args.class_num)

    def get_port_pfc_quanta(self, args):
        self._port_cmd_obj.port_pfc_quanta(port_num=args.port_num, shape=args.shape, class_num=args.class_num)

    def set_port_pfc_threshold(self, args):
        self._port_cmd_obj.port_pfc_threshold(port_num=args.port_num, shape=args.shape, threshold=args.threshold,
                                              class_num=args.class_num)

    def get_port_pfc_threshold(self, args):
        self._port_cmd_obj.port_pfc_threshold(port_num=args.port_num, shape=args.shape, class_num=args.class_num)

    def enable_port_ptp_peer_delay(self, args):
        self._port_cmd_obj.enable_disable_ptp_peer_delay(port_num=args.port_num, shape=args.shape)

    def disable_port_ptp_peer_delay(self, args):
        self._port_cmd_obj.enable_disable_ptp_peer_delay(port_num=args.port_num, shape=args.shape, enable=False)

    def set_port_ptp_peer_delay(self, args):
        self._port_cmd_obj.ptp_peer_delay(port_num=args.port_num, shape=args.shape, delay=args.delay)

    def get_port_ptp_peer_delay(self, args):
        self._port_cmd_obj.ptp_peer_delay(port_num=args.port_num, shape=args.shape)

    def get_port_ptp_tx_ts(self, args):
        self._port_cmd_obj.get_ptp_tx_ts(port_num=args.port_num, shape=args.shape)

    def enable_port_ptp_1step(self, args):
        self._port_cmd_obj.enable_disable_ptp_1step(port_num=args.port_num, shape=args.shape)

    def disable_port_ptp_1step(self, args):
        self._port_cmd_obj.enable_disable_ptp_1step(port_num=args.port_num, shape=args.shape, enable=False)

    def set_port_runt_filter(self, args):
        self._port_cmd_obj.set_runt_filter(port_num=args.port_num, shape=args.shape, buffer=args.buffer_64,
                                           runt_err_en=args.runt_err_en, en_delete=args.en_delete)

    def dump_port_runt_filter(self, args):
        self._port_cmd_obj.dump_runt_filter(port_num=args.port_num, shape=args.shape)

    def set_system_syslog_level(self, args):
        self._sys_cmd_obj.system_syslog_level(level_val=args.level_val)

    def get_system_syslog_level(self, args):
        self._sys_cmd_obj.system_syslog_level(level_val=None)

    def set_qos_egress_buffer_pool(self, args):
        sf_thr = args.sf_thr
        sx_thr = args.sx_thr
        df_thr = args.df_thr
        dx_thr = args.dx_thr
        fcp_thr = args.fcp_thr
        nonfcp_thr = args.nonfcp_thr
        sample_copy_thr = args.sample_copy_thr
        sf_xoff_thr = args.sf_xoff_thr
        fcp_xoff_thr = args.fcp_xoff_thr
        nonfcp_xoff_thr = args.nonfcp_xoff_thr
        self._qos_cmd_obj.egress_buffer_pool(sf_thr=sf_thr, sx_thr=sx_thr, df_thr=df_thr, dx_thr=dx_thr,
                                             fcp_thr=fcp_thr, nonfcp_xoff_thr=nonfcp_xoff_thr,
                                             sample_copy_thr=sample_copy_thr, nonfcp_thr=nonfcp_thr,
                                             fcp_xoff_thr=fcp_xoff_thr, sf_xoff_thr=sf_xoff_thr, update_config=True)

    def set_hnu_qos_egress_buffer_pool(self, args):
        sf_thr = args.sf_thr
        sx_thr = args.sx_thr
        df_thr = args.df_thr
        dx_thr = args.dx_thr
        fcp_thr = args.fcp_thr
        nonfcp_thr = args.nonfcp_thr
        sample_copy_thr = args.sample_copy_thr
        sf_xoff_thr = args.sf_xoff_thr
        fcp_xoff_thr = args.fcp_xoff_thr
        nonfcp_xoff_thr = args.nonfcp_xoff_thr
        self._qos_cmd_obj.egress_buffer_pool(sf_thr=sf_thr, sx_thr=sx_thr, df_thr=df_thr, dx_thr=dx_thr,
                                             fcp_thr=fcp_thr, nonfcp_xoff_thr=nonfcp_xoff_thr,
                                             sample_copy_thr=sample_copy_thr, nonfcp_thr=nonfcp_thr,
                                             fcp_xoff_thr=fcp_xoff_thr, sf_xoff_thr=sf_xoff_thr, update_config=True,
                                             mode='hnu')

    def get_qos_egress_buffer_pool(self, args):
        self._qos_cmd_obj.egress_buffer_pool(update_config=False)

    def get_hnu_qos_egress_buffer_pool(self, args):
        self._qos_cmd_obj.egress_buffer_pool(update_config=False, mode='hnu')

    def set_qos_egress_port_buffer(self, args):
        port_num = args.port_num
        min_thr = args.min_thr
        shared_thr = args.shared_thr
        self._qos_cmd_obj.egress_port_buffer(port_num=port_num, min_thr=min_thr, shared_thr=shared_thr)

    def set_hnu_qos_egress_port_buffer(self, args):
        port_num = args.port_num
        min_thr = args.min_thr
        shared_thr = args.shared_thr
        self._qos_cmd_obj.egress_port_buffer(port_num=port_num, min_thr=min_thr, shared_thr=shared_thr, mode='hnu')

    def get_qos_egress_port_buffer(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.egress_port_buffer(port_num=port_num, update_config=False)

    def get_hnu_qos_egress_port_buffer(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.egress_port_buffer(port_num=port_num, update_config=False, mode='hnu')

    def set_qos_egress_queue_buffer(self, args):
        port_num = args.port_num
        queue = args.queue
        min_thr = args.min_thr
        static_shared_thr_green = args.static_shared_thr_green
        dynamic_enable = args.dynamic_enable
        shared_thr_alpha = args.shared_thr_alpha
        shared_thr_offset_yellow = args.shared_thr_offset_yellow
        shared_thr_offset_red = args.shared_thr_offset_red
        self._qos_cmd_obj.egress_queue_buffer(port_num=port_num, queue=queue,
                                              min_thr=min_thr, static_shared_thr_green=static_shared_thr_green,
                                              shared_thr_alpha=shared_thr_alpha, dynamic_enable=dynamic_enable,
                                              shared_thr_offset_red=shared_thr_offset_red,
                                              shared_thr_offset_yellow=shared_thr_offset_yellow)

    def set_hnu_qos_egress_queue_buffer(self, args):
        port_num = args.port_num
        queue = args.queue
        min_thr = args.min_thr
        static_shared_thr_green = args.static_shared_thr_green
        dynamic_enable = args.dynamic_enable
        shared_thr_alpha = args.shared_thr_alpha
        shared_thr_offset_yellow = args.shared_thr_offset_yellow
        shared_thr_offset_red = args.shared_thr_offset_red
        self._qos_cmd_obj.egress_queue_buffer(port_num=port_num, queue=queue,
                                              min_thr=min_thr, static_shared_thr_green=static_shared_thr_green,
                                              shared_thr_alpha=shared_thr_alpha, dynamic_enable=dynamic_enable,
                                              shared_thr_offset_red=shared_thr_offset_red,
                                              shared_thr_offset_yellow=shared_thr_offset_yellow, mode='hnu')

    def get_qos_egress_queue_buffer(self, args):
        port_num = args.port_num
        queue = args.queue
        self._qos_cmd_obj.egress_queue_buffer(port_num=port_num, update_config=False, queue=queue)

    def get_hnu_qos_egress_queue_buffer(self, args):
        port_num = args.port_num
        queue = args.queue
        self._qos_cmd_obj.egress_queue_buffer(port_num=port_num, update_config=False, queue=queue, mode='hnu')

    def set_qos_egress_priority_map(self, args):
        port_num = args.port_num
        map_list = args.map_list
        self._qos_cmd_obj.egress_queue_to_priority_map(port_num=port_num, map_list=map_list, update=True)

    def set_hnu_qos_egress_priority_map(self, args):
        port_num = args.port_num
        map_list = args.map_list
        self._qos_cmd_obj.egress_queue_to_priority_map(port_num=port_num, map_list=map_list, update=True)

    def get_qos_egress_priority_map(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.egress_queue_to_priority_map(port_num=port_num, update=False)

    def get_hnu_qos_egress_priority_map(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.egress_queue_to_priority_map(port_num=port_num, update=False, mode='hnu')

    def set_qos_ecn_glb_sh_threshold(self, args):
        en = args.en
        green = args.green
        red = args.red
        yellow = args.yellow
        self._qos_cmd_obj.ecn_glb_sh_threshold(en=en, green=green, red=red, yellow=yellow, update=True)

    def set_hnu_qos_ecn_glb_sh_threshold(self, args):
        en = args.en
        green = args.green
        red = args.red
        yellow = args.yellow
        self._qos_cmd_obj.ecn_glb_sh_threshold(en=en, green=green, red=red, yellow=yellow, update=True, mode='hnu')

    def get_qos_ecn_glb_sh_threshold(self, args):
        self._qos_cmd_obj.ecn_glb_sh_threshold(update=False)

    def get_hnu_qos_ecn_glb_sh_threshold(self, args):
        self._qos_cmd_obj.ecn_glb_sh_threshold(update=False, mode='hnu')

    def set_qos_ecn_profile(self, args):
        prof_num = args.prof_num
        min_thr = args.min_thr
        max_thr = args.max_thr
        ecn_prob_index = args.ecn_prob_index
        self._qos_cmd_obj.ecn_profile(prof_num=prof_num, min_thr=min_thr, max_thr=max_thr,
                                      ecn_prob_index=ecn_prob_index, update=True)

    def set_hnu_qos_ecn_profile(self, args):
        prof_num = args.prof_num
        min_thr = args.min_thr
        max_thr = args.max_thr
        ecn_prob_index = args.ecn_prob_index
        self._qos_cmd_obj.ecn_profile(prof_num=prof_num, min_thr=min_thr, max_thr=max_thr,
                                      ecn_prob_index=ecn_prob_index, update=True, mode='hnu')

    def get_qos_ecn_profile(self, args):
        prof_num = args.prof_num
        self._qos_cmd_obj.ecn_profile(prof_num=prof_num, update=False)

    def get_hnu_qos_ecn_profile(self, args):
        prof_num = args.prof_num
        self._qos_cmd_obj.ecn_profile(prof_num=prof_num, update=False, mode='hnu')

    def set_qos_ecn_prob(self, args):
        prob_idx = args.prob_idx
        prob = args.prob
        self._qos_cmd_obj.ecn_prob(prob=prob, prob_idx=prob_idx, update=True)

    def set_hnu_qos_ecn_prob(self, args):
        prob_idx = args.prob_idx
        prob = args.prob
        self._qos_cmd_obj.ecn_prob(prob=prob, prob_idx=prob_idx, update=True, mode='hnu')

    def get_qos_ecn_prob(self, args):
        prob_idx = args.prob_idx
        self._qos_cmd_obj.ecn_prob(prob_idx=prob_idx, update=False)

    def get_hnu_qos_ecn_prob(self, args):
        prob_idx = args.prob_idx
        self._qos_cmd_obj.ecn_prob(prob_idx=prob_idx, update=False,mode='hnu')

    def set_qos_wred_profile(self, args):
        prof_num = args.prof_num
        min_thr = args.min_thr
        max_thr = args.max_thr
        wred_prob_index = args.wred_prob_index
        self._qos_cmd_obj.wred_profile(prof_num=prof_num, min_thr=min_thr, max_thr=max_thr,
                                       wred_prob_index=wred_prob_index, update=True)

    def set_hnu_qos_wred_profile(self, args):
        prof_num = args.prof_num
        min_thr = args.min_thr
        max_thr = args.max_thr
        wred_prob_index = args.wred_prob_index
        self._qos_cmd_obj.wred_profile(prof_num=prof_num, min_thr=min_thr, max_thr=max_thr,
                                       wred_prob_index=wred_prob_index, update=True, mode='hnu')

    def get_qos_wred_profile(self, args):
        prof_num = args.prof_num
        self._qos_cmd_obj.wred_profile(prof_num=prof_num, update=False)

    def get_hnu_qos_wred_profile(self, args):
        prof_num = args.prof_num
        self._qos_cmd_obj.wred_profile(prof_num=prof_num, update=False, mode='hnu')

    def set_qos_wred_prob(self, args):
        prob_idx = args.prob_idx
        prob = args.prob
        self._qos_cmd_obj.wred_prob(prob=prob, prob_idx=prob_idx, update=True)

    def set_hnu_qos_wred_prob(self, args):
        prob_idx = args.prob_idx
        prob = args.prob
        self._qos_cmd_obj.wred_prob(prob=prob, prob_idx=prob_idx, update=True, mode='hnu')

    def get_qos_wred_prob(self, args):
        prob_idx = args.prob_idx
        self._qos_cmd_obj.wred_prob(prob_idx=prob_idx, update=False)

    def get_hnu_qos_wred_prob(self, args):
        prob_idx = args.prob_idx
        self._qos_cmd_obj.wred_prob(prob_idx=prob_idx, update=False, mode='hnu')

    def set_qos_wred_queue_config(self, args):
        port_num = args.port_num
        queue_num = args.queue
        wred_en = args.wred_en
        wred_weight = args.wred_weight
        wred_prof_num = args.wred_prof_num
        ecn_en = args.ecn_en
        ecn_prof_num = args.ecn_prof_num
        self._qos_cmd_obj.wred_queue_config(port_num=port_num, queue_num=queue_num, wred_en=wred_en,
                                            wred_weight=wred_weight, wred_prof_num=wred_prof_num, ecn_en=ecn_en,
                                            ecn_prof_num=ecn_prof_num, update=True)

    def set_hnu_qos_wred_queue_config(self, args):
        port_num = args.port_num
        queue_num = args.queue
        wred_en = args.wred_en
        wred_weight = args.wred_weight
        wred_prof_num = args.wred_prof_num
        ecn_en = args.ecn_en
        ecn_prof_num = args.ecn_prof_num
        self._qos_cmd_obj.wred_queue_config(port_num=port_num, queue_num=queue_num, wred_en=wred_en,
                                            wred_weight=wred_weight, wred_prof_num=wred_prof_num, ecn_en=ecn_en,
                                            ecn_prof_num=ecn_prof_num, update=True, mode='hnu')

    def get_qos_wred_queue_config(self, args):
        port_num = args.port_num
        queue_num = args.queue
        self._qos_cmd_obj.wred_queue_config(port_num=port_num, queue_num=queue_num, update=False)

    def get_hnu_qos_wred_queue_config(self, args):
        port_num = args.port_num
        queue_num = args.queue
        self._qos_cmd_obj.wred_queue_config(port_num=port_num, queue_num=queue_num, update=False, mode='hnu')

    def set_qos_wred_avg_q_config(self, args):
        q_avg_en = args.q_avg_en
        cap_avg_sz = args.cap_avg_sz
        avg_period = args.avg_period
        self._qos_cmd_obj.wred_avg_q_config(q_avg_en=q_avg_en, cap_avg_sz=cap_avg_sz, avg_period=avg_period,
                                            update=True)

    def set_hnu_qos_wred_avg_q_config(self, args):
        q_avg_en = args.q_avg_en
        cap_avg_sz = args.cap_avg_sz
        avg_period = args.avg_period
        self._qos_cmd_obj.wred_avg_q_config(q_avg_en=q_avg_en, cap_avg_sz=cap_avg_sz, avg_period=avg_period,
                                            update=True, mode='hnu')

    def get_qos_wred_avg_q_config(self, args):
        self._qos_cmd_obj.wred_avg_q_config(update=False)

    def get_hnu_qos_wred_avg_q_config(self, args):
        self._qos_cmd_obj.wred_avg_q_config(update=False, mode='hnu')

    def get_qos_scheduler_config(self, args):
        port_num = args.port_num
        queue = args.queue
        self._qos_cmd_obj.get_scheduler_config(port_num=port_num, queue_num=queue)

    def get_hnu_qos_scheduler_config(self, args):
        port_num = args.port_num
        queue = args.queue
        self._qos_cmd_obj.get_scheduler_config(port_num=port_num, queue_num=queue, mode='hnu')

    def set_qos_scheduler_config_dwrr(self, args):
        port_num = args.port_num
        queue = args.queue
        weight = args.weight
        self._qos_cmd_obj.scheduler_config_dwrr(port_num=port_num, queue_num=queue, weight=weight)

    def set_hnu_qos_scheduler_config_dwrr(self, args):
        port_num = args.port_num
        queue = args.queue
        weight = args.weight
        self._qos_cmd_obj.scheduler_config_dwrr(port_num=port_num, queue_num=queue, weight=weight, mode='hnu')

    def set_qos_scheduler_config_shaper(self, args):
        port_num = args.port_num
        queue = args.queue
        shaper_enable = args.enable
        shaper_type = args.type
        shaper_rate = args.rate
        shaper_threshold = args.thresh
        self._qos_cmd_obj.scheduler_config_shaper(port_num=port_num, queue_num=queue,
                                                  shaper_enable=shaper_enable,
                                                  shaper_type=shaper_type,
                                                  shaper_rate=shaper_rate,
                                                  shaper_threshold=shaper_threshold)

    def set_hnu_qos_scheduler_config_shaper(self, args):
        port_num = args.port_num
        queue = args.queue
        shaper_enable = args.enable
        shaper_type = args.type
        shaper_rate = args.rate
        shaper_threshold = args.thresh
        self._qos_cmd_obj.scheduler_config_shaper(port_num=port_num, queue_num=queue,
                                                  shaper_enable=shaper_enable,
                                                  shaper_type=shaper_type,
                                                  shaper_rate=shaper_rate,
                                                  shaper_threshold=shaper_threshold, mode='hnu')

    def set_qos_scheduler_config_strict_priority(self, args):
        port_num = args.port_num
        queue = args.queue
        strict_priority_enable = args.strict_priority_enable
        extra_bandwidth = args.extra_bandwidth
        self._qos_cmd_obj.scheduler_config_strict_priority(port_num=port_num, queue_num=queue,
                                                           strict_priority_enable=strict_priority_enable,
                                                           extra_bandwidth=extra_bandwidth)

    def set_hnu_qos_scheduler_config_strict_priority(self, args):
        port_num = args.port_num
        queue = args.queue
        strict_priority_enable = args.strict_priority_enable
        extra_bandwidth = args.extra_bandwidth
        self._qos_cmd_obj.scheduler_config_strict_priority(port_num=port_num, queue_num=queue,
                                                           strict_priority_enable=strict_priority_enable,
                                                           extra_bandwidth=extra_bandwidth, mode='hnu')

    def set_qos_ingress_pg(self, args):
        port_num = args.port_num
        pg_num = args.pg
        min_thr = args.min_thr
        shared_thr = args.shared_thr
        headroom_thr = args.headroom_thr
        xoff_enable = args.xoff_enable
        shared_xon_thr = args.shared_xon_thr
        self._qos_cmd_obj.ingress_priority_group(port_num=port_num, pg_num=pg_num, min_thr=min_thr,
                                                 shared_thr=shared_thr, shared_xon_thr=shared_xon_thr,
                                                 headroom_thr=headroom_thr, xoff_enable=xoff_enable, update=True)

    def set_hnu_qos_ingress_pg(self, args):
        port_num = args.port_num
        pg_num = args.pg
        min_thr = args.min_thr
        shared_thr = args.shared_thr
        headroom_thr = args.headroom_thr
        xoff_enable = args.xoff_enable
        shared_xon_thr = args.shared_xon_thr
        self._qos_cmd_obj.ingress_priority_group(port_num=port_num, pg_num=pg_num, min_thr=min_thr,
                                                 shared_thr=shared_thr, shared_xon_thr=shared_xon_thr,
                                                 headroom_thr=headroom_thr, xoff_enable=xoff_enable, update=True, mode='hnu')

    def get_qos_ingress_pg(self, args):
        port_num = args.port_num
        pg_num = args.pg
        self._qos_cmd_obj.ingress_priority_group(port_num=port_num, pg_num=pg_num, update=False)

    def get_hnu_qos_ingress_pg(self, args):
        port_num = args.port_num
        pg_num = args.pg
        self._qos_cmd_obj.ingress_priority_group(port_num=port_num, pg_num=pg_num, update=False, mode='hnu')

    def set_qos_ingress_pg_map(self, args):
        port_num = args.port_num
        map_list = args.map_list
        self._qos_cmd_obj.ingress_priority_to_pg_map(port_num=port_num, map_list=map_list, update=True)

    def set_hnu_qos_ingress_pg_map(self, args):
        port_num = args.port_num
        map_list = args.map_list
        self._qos_cmd_obj.ingress_priority_to_pg_map(port_num=port_num, map_list=map_list, update=True, mode='hnu')

    def get_qos_ingress_pg_map(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.ingress_priority_to_pg_map(port_num=port_num, update=False)

    def get_hnu_qos_ingress_pg_map(self, args):
        port_num = args.port_num
        self._qos_cmd_obj.ingress_priority_to_pg_map(port_num=port_num, update=False, mode='hnu')

    def set_qos_pfc_enable(self, args):
        self._qos_cmd_obj.pfc(enable=True, update=True)

    def set_hnu_qos_pfc_enable(self, args):
        self._qos_cmd_obj.pfc(enable=True, update=True, mode='hnu')

    def set_qos_pfc_disable(self, args):
        self._qos_cmd_obj.pfc(update=True, disable=True)

    def set_hnu_qos_pfc_disable(self, args):
        self._qos_cmd_obj.pfc(update=True, disable=True, mode='hnu')

    def get_qos_pfc(self, args):
        self._qos_cmd_obj.pfc(update=False)

    def get_hnu_qos_pfc(self, args):
        self._qos_cmd_obj.pfc(update=False, mode='hnu')

    def set_qos_arb_cfg(self, args):
        enable = args.en
        self._qos_cmd_obj.arb_cfg(en=enable, update=True)

    def set_hnu_qos_arb_cfg(self, args):
        enable = args.en
        self._qos_cmd_obj.arb_cfg(en=enable, update=True, mode='hnu')

    def get_qos_arb_cfg(self, args):
        self._qos_cmd_obj.arb_cfg(update=False)

    def get_hnu_qos_arb_cfg(self, args):
        self._qos_cmd_obj.arb_cfg(update=False, mode='hnu')

    def set_qos_xoff_status(self, args):
        port_num = args.port_num
        pg = args.pg
        status = args.status
        self._qos_cmd_obj.xoff_status(port_num=port_num, pg=pg, status=status, update=True)

    def set_hnu_qos_xoff_status(self, args):
        port_num = args.port_num
        pg = args.pg
        status = args.status
        self._qos_cmd_obj.xoff_status(port_num=port_num, pg=pg, status=status, update=True, mode='hnu')

    def get_qos_xoff_status(self, args):
        port_num = args.port_num
        pg = args.pg
        self._qos_cmd_obj.xoff_status(port_num=port_num, pg=pg, update=False)

    def get_hnu_qos_xoff_status(self, args):
        port_num = args.port_num
        pg = args.pg
        self._qos_cmd_obj.xoff_status(port_num=port_num, pg=pg, update=False, mode='hnu')

    def peek_fpg_stats(self, args):
        port_num = args.port_num
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fpg_stats(port_num=port_num, grep_regex=grep_regex)

    def peek_hnu_fpg_stats(self, args):
        port_num = args.port_num
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fpg_stats(port_num=port_num, grep_regex=grep_regex, mode='hnu')

    def peek_psw_nu_stats(self, args):
        port_num = args.port_num
        queues = args.queues
        grep_regex = args.grep
        self._peek_cmd_obj.peek_psw_stats(mode='nu', port_num=port_num, queue_list=queues, grep_regex=grep_regex)

    def peek_psw_hnu_stats(self, args):
        port_num = args.port_num
        queues = args.queues
        grep_regex = args.grep
        self._peek_cmd_obj.peek_psw_stats(mode='hnu', port_num=port_num, queue_list=queues, grep_regex=grep_regex)

    def peek_meter_stats(self, args):
        bank = args.bank
        index = args.index
        grep_regex = args.grep
        self._peek_cmd_obj.peek_meter_stats(bank=bank, index=index, grep_regex=grep_regex)

    def peek_erp_meter_stats(self, args):
        bank = args.bank
        index = args.index
        grep_regex = args.grep
        self._peek_cmd_obj.peek_meter_stats(bank=bank, index=index, grep_regex=grep_regex, erp=True)

    def peek_vp_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_vp_stats(grep_regex=grep_regex)

    def peek_fcp_nu_stats(self, args):
        tunnel_id = args.tunnel
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fcp_stats(mode='nu', tunnel_id=tunnel_id, grep_regex=grep_regex)

    def peek_fcp_hnu_stats(self, args):
        tunnel_id = args.tunnel
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fcp_stats(mode='hnu', tunnel_id=tunnel_id, grep_regex=grep_regex)

    def peek_wro_nu_stats(self, args):
        tunnel_id = args.tunnel
        grep_regex = args.grep
        self._peek_cmd_obj.peek_wro_stats(mode='nu', tunnel_id=tunnel_id, grep_regex=grep_regex)

    def peek_wro_hnu_stats(self, args):
        tunnel_id = args.tunnel
        grep_regex = args.grep
        self._peek_cmd_obj.peek_wro_stats(mode='hnu', tunnel_id=tunnel_id, grep_regex=grep_regex)

    def peek_bam_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_bam_stats(grep_regex=grep_regex)

    def peek_fwd_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fwd_stats(grep_regex=grep_regex)

    def peek_erp_hnu_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_erp_stats(mode='hnu', grep_regex=grep_regex)

    def peek_erp_nu_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_erp_stats(mode='nu', grep_regex=grep_regex)

    def peek_etp_hnu_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_etp_stats(mode='hnu', grep_regex=grep_regex)

    def peek_etp_nu_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_etp_stats(mode='nu', grep_regex=grep_regex)

    def peek_erp_flex_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_erp_stats(mode='flex', grep_regex=grep_regex)

    def peek_nu_parser_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_parser_stats(mode='nu', grep_regex=grep_regex)

    def peek_hnu_parser_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_parser_stats(mode='hnu', grep_regex=grep_regex)

    def peek_nu_qos_wred_ecn_stats(self, args):
        port_num = args.port_num
        queue_num = args.queue_num
        grep_regex = args.grep
        self._peek_cmd_obj.peek_wred_ecn_stats(port_num=port_num, queue_num=queue_num, grep_regex=grep_regex)

    def peek_nu_sfg_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_sfg_stats(mode='nu', grep_regex=grep_regex)

    def peek_hnu_sfg_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_sfg_stats(mode='hnu', grep_regex=grep_regex)

    def peek_per_vp_stats(self, args):
        grep_regex = args.grep
        vp_num = args.vp_num
        self._peek_cmd_obj.peek_stats_per_vp(vp_number=vp_num, grep_regex=grep_regex)

    def peek_nwqm_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_nwqm_stats(grep_regex=grep_regex)

    def peek_nwqm_hnu_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_nwqm_stats(mode='hnu', grep_regex=grep_regex)

    def peek_fae_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_fae_stats(grep_regex=grep_regex)

    def peek_mpg_stats(self, args):
        self._peek_cmd_obj.peek_mpg_stats()

    def peek_pervppkts_stats(self, args):
        cluster_id = args.cluster_id
        grep_regex = args.grep
        vp_num = args.vp_num
        self._peek_cmd_obj.peek_pervppkts_stats(vp_number=vp_num, cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_stats_nhp(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_nhp_stats(grep_regex=grep_regex)

    def peek_stats_sse(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_sse_stats(grep_regex=grep_regex)

    def peek_pc_resource_stats(self, args):
        grep_regex = args.grep
        cluster_id = args.cluster_id
        self._peek_cmd_obj.peek_pc_resource_stats(cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_cc_resource_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_cc_resource_stats(grep_regex=grep_regex)

    def peek_dma_resource_stats(self, args):
        grep_regex = args.grep
        cluster_id = args.cluster_id
        self._peek_cmd_obj.peek_dma_resource_stats(cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_le_resource_stats(self, args):
        grep_regex = args.grep
        cluster_id = args.cluster_id
        self._peek_cmd_obj.peek_le_resource_stats(cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_zip_resource_stats(self, args):
        grep_regex = args.grep
        cluster_id = args.cluster_id
        self._peek_cmd_obj.peek_zip_resource_stats(cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_rgx_resource_stats(self, args):
        grep_regex = args.grep
        cluster_id = args.cluster_id
        self._peek_cmd_obj.peek_rgx_resource_stats(cluster_id=cluster_id, grep_regex=grep_regex)

    def peek_hnu_resource_stats(self, args):
        grep_regex = args.grep
        resource_id = args.resource_id
        self._peek_cmd_obj.peek_mode_resource_stats(mode='hnu', resource_id=resource_id, grep_regex=grep_regex)

    def peek_nu_resource_stats(self, args):
        grep_regex = args.grep
        resource_id = args.resource_id
        self._peek_cmd_obj.peek_mode_resource_stats(mode='nu', resource_id=resource_id, grep_regex=grep_regex)

    def peek_hu_resource_stats(self, args):
        id = args.id
        grep_regex = args.grep
        self._peek_cmd_obj.peek_hu_resource_stats(hu_id=id, grep_regex=grep_regex)

    def peek_hu_wqsi_resource_stats(self, args):
        id = args.id
        grep_regex = args.grep
        resource_id = args.rid
        self._peek_cmd_obj.peek_hu_resource_stats(hu_id=id, wqsi=True, resource_id=resource_id,
                                                  grep_regex=grep_regex)

    def peek_hu_wqse_resource_stats(self, args):
        id = args.id
        grep_regex = args.grep
        self._peek_cmd_obj.peek_hu_resource_stats(hu_id=id, wqse=True, grep_regex=grep_regex)

    def peek_dam_resource_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_dam_resource_stats(grep_regex=grep_regex)

    def peek_bam_resource_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_bam_resource_stats(grep_regex=grep_regex)

    def peek_eqm_stats(self, args):
        grep_regex = args.grep
        self._peek_cmd_obj.peek_eqm_stats(grep_regex=grep_regex)

    def clear_nu_port_stats(self, args):
        self._clear_cmd_obj.clear_nu_port_stats(port_num=args.port_num, shape=args.shape)

    def clear_nu_fwd_stats(self, args):
        self._clear_cmd_obj.clear_nu_fwd_stats()

    def clear_nu_erp_stats(self, args):
        self._clear_cmd_obj.clear_nu_erp_stats()

    def clear_nu_parser_stats(self, args):
        self._clear_cmd_obj.clear_nu_parser_stats()

    def clear_nu_nwqm_stats(self, args):
        self._clear_cmd_obj.clear_nu_nwqm_stats()

    def clear_nu_vppkts_stats(self, args):
        self._clear_cmd_obj.clear_nu_vppkts_stats()

    def clear_nu_all_stats(self, args):
        self._clear_cmd_obj.clear_nu_all_stats()

    def set_port_speed(self, args):
        port_num = args.port_num
        shape = args.shape
        brkmode = args.brkmode
        self._port_cmd_obj.port_speed(port_num=port_num, shape=shape, brkmode=brkmode)

    def get_port_speed(self, args):
        port_num = args.port_num
        shape = args.shape
        self._port_cmd_obj.port_speed(port_num=port_num, shape=shape)

    def set_sample(self, args, mode):
        id = args.id
        fpg = args.fpg
        dest = args.dest
        acl = args.acl
        flag_mask = args.flag_mask
        hu = args.hu
        psw_drop = args.psw_drop
        pps_en = args.pps_en
        pps_interval = args.pps_interval
        pps_burst = args.pps_burst
        pps_tick = args.pps_tick
        sampler_en = args.sampler_en
        sampler_rate = args.sampler_rate
        sampler_run_sz = args.sampler_run_sz
        first_cell_only = args.first_cell_only
        self._sample_cmd_obj.set_sample(id=id, fpg=fpg, dest=dest, acl=acl, flag_mask=flag_mask, hu=hu, psw_drop=psw_drop,
                                        pps_en=pps_en, pps_interval=pps_interval, pps_burst=pps_burst, pps_tick=pps_tick,
                                        sampler_en=sampler_en, sampler_rate=sampler_rate, sampler_run_sz=sampler_run_sz,
                                        first_cell_only=first_cell_only, mode=mode)

    def set_ingress_sample(self, args):
        self.set_sample(args=args, mode=0)

    def set_egress_sample(self, args):
        self.set_sample(args=args, mode=1)

    def disable_sample(self, args):
        self.set_sample(args=args, mode=2)

    def get_sample(self, args):
        self._sample_cmd_obj.get_sample()

    def show_tech_nu_stats(self, args):
        filename = args.filename
        portlist = args.portlist
        self._show_cmd_obj.show_stats(filename=filename, mode='nu', port_list=portlist)

    def show_tech_hnu_stats(self, args):
        filename = args.filename
        portlist = args.portlist
        self._show_cmd_obj.show_stats(filename=filename, mode='hnu', port_list=portlist)

    def show_tech_all_stats(self, args):
        filename = args.filename
        portlist = args.portlist
        self._show_cmd_obj.show_stats(filename=filename, mode='all', port_list=portlist)

    # Set handler functions for the sub commands

    # -------------- Port Command Handlers ----------------
    set_port_mtu_parser.set_defaults(func=set_port_mtu)
    get_port_mtu_parser.set_defaults(func=get_port_mtu)
    set_port_enable_parser.set_defaults(func=enable_port)
    set_port_disable_parser.set_defaults(func=disable_port)
    set_port_pause_enable_parser.set_defaults(func=enable_port_link_pause)
    set_port_pause_disable_parser.set_defaults(func=disable_port_link_pause)
    set_port_pause_tx_enable_parser.set_defaults(func=enable_port_tx_link_pause)
    set_port_pause_tx_disable_parser.set_defaults(func=disable_port_tx_link_pause)
    set_port_pause_quanta_parser.set_defaults(func=set_port_pause_quanta)
    get_port_pause_quanta_parser.set_defaults(func=get_port_pause_quanta)
    set_port_pause_threshold_parser.set_defaults(func=set_port_pause_threshold)
    get_port_pause_threshold_parser.set_defaults(func=get_port_pause_threshold)
    set_port_pfc_enable_parser.set_defaults(func=enable_port_pfc)
    set_port_pfc_disable_parser.set_defaults(func=disable_port_pfc)
    set_port_pfc_tx_enable_parser.set_defaults(func=enable_port_tx_pfc)
    set_port_pfc_tx_disable_parser.set_defaults(func=disable_port_tx_pfc)
    set_port_pfc_quanta_parser.set_defaults(func=set_port_pfc_quanta)
    get_port_pfc_quanta_parser.set_defaults(func=get_port_pfc_quanta)
    set_port_pfc_threshold_parser.set_defaults(func=set_port_pfc_threshold)
    get_port_pfc_threshold_parser.set_defaults(func=get_port_pfc_threshold)
    set_port_ptp_peer_delay_enable_parser.set_defaults(func=enable_port_ptp_peer_delay)
    set_port_ptp_peer_delay_disable_parser.set_defaults(func=disable_port_ptp_peer_delay)
    set_port_ptp_peer_delay_parser.set_defaults(func=set_port_ptp_peer_delay)
    get_port_ptp_peer_delay_parser.set_defaults(func=get_port_ptp_peer_delay)
    get_port_ptp_tx_ts_parser.set_defaults(func=get_port_ptp_tx_ts)
    set_port_ptp_1step_enable_parser.set_defaults(func=enable_port_ptp_1step)
    set_port_ptp_1step_disable_parser.set_defaults(func=disable_port_ptp_1step)
    set_port_runt_filter_parser.set_defaults(func=set_port_runt_filter)
    get_port_runt_filter_parser.set_defaults(func=dump_port_runt_filter)
    set_port_speed_parser.set_defaults(func=set_port_speed)
    get_port_speed_parser.set_defaults(func=get_port_speed)

    # -------------- System Command Handlers ----------------
    set_system_params_syslog_parser.set_defaults(func=set_system_syslog_level)
    set_system_time_interval_parser.set_defaults(func=set_system_time_interval)
    get_system_time_interval_parser.set_defaults(func=get_system_time_interval)
    get_system_params_syslog_parser.set_defaults(func=get_system_syslog_level)

    # --------------------Sample Commands Handlers -------------
    set_nu_sample_ingress_parser.set_defaults(func=set_ingress_sample)
    set_nu_sample_egress_parser.set_defaults(func=set_egress_sample)
    set_nu_sample_disable_parser.set_defaults(func=disable_sample)
    get_nu_sample_parser.set_defaults(func=get_sample)

    # -------------- QoS Command Handlers ----------------
    set_qos_egress_buffer_pool_parser.set_defaults(func=set_qos_egress_buffer_pool)
    get_qos_egress_buffer_pool_parser.set_defaults(func=get_qos_egress_buffer_pool)
    set_qos_egress_port_buffer_parser.set_defaults(func=set_qos_egress_port_buffer)
    get_qos_egress_port_buffer_parser.set_defaults(func=get_qos_egress_port_buffer)
    set_qos_egress_queue_buffer_parser.set_defaults(func=set_qos_egress_queue_buffer)
    get_qos_egress_queue_buffer_parser.set_defaults(func=get_qos_egress_queue_buffer)
    set_qos_egress_priority_map_parser.set_defaults(func=set_qos_egress_priority_map)
    get_qos_egress_priority_map_parser.set_defaults(func=get_qos_egress_priority_map)
    get_qos_ecn_glb_sh_thresh_parser.set_defaults(func=get_qos_ecn_glb_sh_threshold)
    set_qos_ecn_glb_sh_thresh_parser.set_defaults(func=set_qos_ecn_glb_sh_threshold)
    set_qos_ecn_profile_parser.set_defaults(func=set_qos_ecn_profile)
    get_qos_ecn_profile_parser.set_defaults(func=get_qos_ecn_profile)
    set_qos_ecn_prob_parser.set_defaults(func=set_qos_ecn_prob)
    get_qos_ecn_prob_parser.set_defaults(func=get_qos_ecn_prob)
    set_qos_wred_profile_parser.set_defaults(func=set_qos_wred_profile)
    get_qos_wred_profile_parser.set_defaults(func=get_qos_wred_profile)
    set_qos_wred_prob_parser.set_defaults(func=set_qos_wred_prob)
    get_qos_wred_prob_parser.set_defaults(func=get_qos_wred_prob)
    set_qos_wred_avg_queue_config_parser.set_defaults(func=set_qos_wred_avg_q_config)
    get_qos_wred_avg_queue_config_parser.set_defaults(func=get_qos_wred_avg_q_config)
    set_qos_wred_queue_config_parser.set_defaults(func=set_qos_wred_queue_config)
    get_qos_wred_queue_config_parser.set_defaults(func=get_qos_wred_queue_config)
    get_qos_scheduler_config_parser.set_defaults(func=get_qos_scheduler_config)
    set_qos_scheduler_dwrr_parser.set_defaults(func=set_qos_scheduler_config_dwrr)
    set_qos_scheduler_shaper_parser.set_defaults(func=set_qos_scheduler_config_shaper)
    set_qos_scheduler_strict_priority_parser.set_defaults(func=set_qos_scheduler_config_strict_priority)
    set_qos_ingress_pg_parser.set_defaults(func=set_qos_ingress_pg)
    get_qos_ingress_pg_parser.set_defaults(func=get_qos_ingress_pg)
    set_qos_ingress_pg_map_parser.set_defaults(func=set_qos_ingress_pg_map)
    get_qos_ingress_pg_map_parser.set_defaults(func=get_qos_ingress_pg_map)
    set_qos_pfc_enable_parser.set_defaults(func=set_qos_pfc_enable)
    set_qos_pfc_disable_parser.set_defaults(func=set_qos_pfc_disable)
    get_qos_pfc_parser.set_defaults(func=get_qos_pfc)
    set_qos_arb_cfg_parser.set_defaults(func=set_qos_arb_cfg)
    get_qos_arb_cfg_parser.set_defaults(func=get_qos_arb_cfg)
    set_qos_xoff_status_parser.set_defaults(func=set_qos_xoff_status)
    get_qos_xoff_status_parser.set_defaults(func=get_qos_xoff_status)

    # -------------- QoS Command Handlers ----------------
    set_hnu_qos_egress_buffer_pool_parser.set_defaults(func=set_hnu_qos_egress_buffer_pool)
    get_hnu_qos_egress_buffer_pool_parser.set_defaults(func=get_hnu_qos_egress_buffer_pool)
    set_hnu_qos_egress_port_buffer_parser.set_defaults(func=set_hnu_qos_egress_port_buffer)
    get_hnu_qos_egress_port_buffer_parser.set_defaults(func=get_hnu_qos_egress_port_buffer)
    set_hnu_qos_egress_queue_buffer_parser.set_defaults(func=set_hnu_qos_egress_queue_buffer)
    get_hnu_qos_egress_queue_buffer_parser.set_defaults(func=get_hnu_qos_egress_queue_buffer)
    set_hnu_qos_egress_priority_map_parser.set_defaults(func=set_hnu_qos_egress_priority_map)
    get_hnu_qos_egress_priority_map_parser.set_defaults(func=get_hnu_qos_egress_priority_map)
    get_hnu_qos_ecn_glb_sh_thresh_parser.set_defaults(func=get_hnu_qos_ecn_glb_sh_threshold)
    set_hnu_qos_ecn_glb_sh_thresh_parser.set_defaults(func=set_hnu_qos_ecn_glb_sh_threshold)
    set_hnu_qos_ecn_profile_parser.set_defaults(func=set_hnu_qos_ecn_profile)
    get_hnu_qos_ecn_profile_parser.set_defaults(func=get_hnu_qos_ecn_profile)
    set_hnu_qos_ecn_prob_parser.set_defaults(func=set_hnu_qos_ecn_prob)
    get_hnu_qos_ecn_prob_parser.set_defaults(func=get_hnu_qos_ecn_prob)
    set_hnu_qos_wred_profile_parser.set_defaults(func=set_hnu_qos_wred_profile)
    get_hnu_qos_wred_profile_parser.set_defaults(func=get_hnu_qos_wred_profile)
    set_hnu_qos_wred_prob_parser.set_defaults(func=set_hnu_qos_wred_prob)
    get_hnu_qos_wred_prob_parser.set_defaults(func=get_hnu_qos_wred_prob)
    set_hnu_qos_wred_avg_queue_config_parser.set_defaults(func=set_hnu_qos_wred_avg_q_config)
    get_hnu_qos_wred_avg_queue_config_parser.set_defaults(func=get_hnu_qos_wred_avg_q_config)
    set_hnu_qos_wred_queue_config_parser.set_defaults(func=set_hnu_qos_wred_queue_config)
    get_hnu_qos_wred_queue_config_parser.set_defaults(func=get_hnu_qos_wred_queue_config)
    get_hnu_qos_scheduler_config_parser.set_defaults(func=get_hnu_qos_scheduler_config)
    set_hnu_qos_scheduler_dwrr_parser.set_defaults(func=set_hnu_qos_scheduler_config_dwrr)
    set_hnu_qos_scheduler_shaper_parser.set_defaults(func=set_hnu_qos_scheduler_config_shaper)
    set_hnu_qos_scheduler_strict_priority_parser.set_defaults(func=set_hnu_qos_scheduler_config_strict_priority)
    set_hnu_qos_ingress_pg_parser.set_defaults(func=set_hnu_qos_ingress_pg)
    get_hnu_qos_ingress_pg_parser.set_defaults(func=get_hnu_qos_ingress_pg)
    set_hnu_qos_ingress_pg_map_parser.set_defaults(func=set_hnu_qos_ingress_pg_map)
    get_hnu_qos_ingress_pg_map_parser.set_defaults(func=get_hnu_qos_ingress_pg_map)
    set_hnu_qos_pfc_enable_parser.set_defaults(func=set_hnu_qos_pfc_enable)
    set_hnu_qos_pfc_disable_parser.set_defaults(func=set_hnu_qos_pfc_disable)
    get_hnu_qos_pfc_parser.set_defaults(func=get_hnu_qos_pfc)
    set_hnu_qos_arb_cfg_parser.set_defaults(func=set_hnu_qos_arb_cfg)
    get_hnu_qos_arb_cfg_parser.set_defaults(func=get_hnu_qos_arb_cfg)
    set_hnu_qos_xoff_status_parser.set_defaults(func=set_hnu_qos_xoff_status)
    get_hnu_qos_xoff_status_parser.set_defaults(func=get_hnu_qos_xoff_status)


    # -------------- Peek Command Handlers ----------------
    peek_fpg_stats_parser.set_defaults(func=peek_fpg_stats)
    peek_hnu_fpg_stats_parser.set_defaults(func=peek_hnu_fpg_stats)
    peek_psw_nu_stats_parser.set_defaults(func=peek_psw_nu_stats)
    peek_psw_hnu_stats_parser.set_defaults(func=peek_psw_hnu_stats)
    peek_meter_nu_stats_parser.set_defaults(func=peek_meter_stats)
    peek_meter_erp_stats_parser.set_defaults(func=peek_erp_meter_stats)
    peek_vp_stats_parser.set_defaults(func=peek_vp_stats)
    peek_fcp_nu_stats_parser.set_defaults(func=peek_fcp_nu_stats)
    peek_fcp_hnu_stats_parser.set_defaults(func=peek_fcp_hnu_stats)
    peek_wro_nu_stats_parser.set_defaults(func=peek_wro_nu_stats)
    peek_wro_hnu_stats_parser.set_defaults(func=peek_wro_hnu_stats)
    peek_bam_stats_parser.set_defaults(func=peek_bam_stats)
    peek_fwd_stats_parser.set_defaults(func=peek_fwd_stats)
    peek_erp_hnu_stats_parser.set_defaults(func=peek_erp_hnu_stats)
    peek_erp_nu_stats_parser.set_defaults(func=peek_erp_nu_stats)
    peek_erp_flex_stats_parser.set_defaults(func=peek_erp_flex_stats)
    peek_parser_nu_stats_parser.set_defaults(func=peek_nu_parser_stats)
    peek_parser_hnu_stats_parser.set_defaults(func=peek_hnu_parser_stats)
    peek_wred_ecn_stats_parser.set_defaults(func=peek_nu_qos_wred_ecn_stats)
    peek_nu_sfg_stats_parser.set_defaults(func=peek_nu_sfg_stats)
    peek_hnu_sfg_stats_parser.set_defaults(func=peek_hnu_sfg_stats)
    peek_per_vp_stats_parser.set_defaults(func=peek_per_vp_stats)
    peek_nwqm_stats_parser.set_defaults(func=peek_nwqm_stats)
    peek_nwqm_hnu_stats_parser.set_defaults(func=peek_nwqm_hnu_stats)
    peek_fae_stats_parser.set_defaults(func=peek_fae_stats)
    peek_mpg_stats_parser.set_defaults(func=peek_mpg_stats)
    peek_pervppkts_stats_parser.set_defaults(func=peek_pervppkts_stats)
    peek_nhp_stats_parser.set_defaults(func=peek_stats_nhp)
    peek_sse_stats_parser.set_defaults(func=peek_stats_sse)
    peek_pc_resource_stats_parser.set_defaults(func=peek_pc_resource_stats)
    peek_cc_resource_stats_parser.set_defaults(func=peek_cc_resource_stats)
    peek_dma_resource_stats_parser.set_defaults(func=peek_dma_resource_stats)
    peek_le_resource_stats_parser.set_defaults(func=peek_le_resource_stats)
    peek_zip_resource_stats_parser.set_defaults(func=peek_zip_resource_stats)
    peek_rgx_resource_stats_parser.set_defaults(func=peek_rgx_resource_stats)
    peek_hnu_resource_stats_parser.set_defaults(func=peek_hnu_resource_stats)
    peek_nu_resource_stats_parser.set_defaults(func=peek_nu_resource_stats)
    peek_hu_resource_stats_parser.set_defaults(func=peek_hu_resource_stats)
    peek_hu_wqsi_resource_stats_parser.set_defaults(func=peek_hu_wqsi_resource_stats)
    peek_hu_wqse_resource_stats_parser.set_defaults(func=peek_hu_wqse_resource_stats)
    peek_dam_resource_stats_parser.set_defaults(func=peek_dam_resource_stats)
    peek_bam_resource_stats_parser.set_defaults(func=peek_bam_resource_stats)
    peek_etp_hnu_stats_parser.set_defaults(func=peek_etp_hnu_stats)
    peek_etp_nu_stats_parser.set_defaults(func=peek_etp_nu_stats)
    peek_eqm_stats_parser.set_defaults(func=peek_eqm_stats)

    # -------------- Clear Command Handlers ----------------
    clear_nu_port_stats_parser.set_defaults(func=clear_nu_port_stats)
    clear_nu_fwd_stats_parser.set_defaults(func=clear_nu_fwd_stats)
    clear_nu_erp_stats_parser.set_defaults(func=clear_nu_erp_stats)
    clear_nu_parser_stats_parser.set_defaults(func=clear_nu_parser_stats)
    clear_nu_all_stats_parser.set_defaults(func=clear_nu_all_stats)
    clear_nu_nwqm_stats_parser.set_defaults(func=clear_nu_nwqm_stats)
    clear_nu_vppkts_stats_parser.set_defaults(func=clear_nu_vppkts_stats)

    # -------------- Clear Command Handlers ----------------
    show_tech_nu_parser.set_defaults(func=show_tech_nu_stats)
    show_tech_hnu_parser.set_defaults(func=show_tech_hnu_stats)
    show_tech_all_parser.set_defaults(func=show_tech_all_stats)

    @with_argparser(base_set_parser)
    def do_set(self, args):
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)
        else:
            self.do_help('set')

    @with_argparser(base_get_parser)
    def do_get(self, args):
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)
        else:
            self.do_help('get')

    @with_argparser(base_clear_parser)
    def do_clear(self, args):
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)
        else:
            self.do_help('clear')

    @with_argparser(base_peek_parser)
    def do_peek(self, args):
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)
        else:
            self.do_help('peek')

    @with_argparser(base_show_parser)
    def do_show(self, args):
        func = getattr(args, 'func', None)
        if func is not None:
            func(self, args)
        else:
            self.do_help('show')

    def __del__(self):
        self.dpc_client.disconnect()






if __name__ == '__main__':
    cmd_obj = CmdController(target_ip="10.1.21.120", target_port=40222, verbose=False)
    cmd_obj.cmdloop(intro="hello")




