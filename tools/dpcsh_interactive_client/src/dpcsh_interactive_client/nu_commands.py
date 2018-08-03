from prettytable import PrettyTable, FRAME
from datetime import datetime
from collections import OrderedDict
import re
import time

TIME_INTERVAL = 5

class PortCommands(object):
    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def port_mtu(self, port_num, shape, mtu=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if mtu is not None:
                mtu_dict = {"mtu": mtu}
                arg_list = ["mtuset", cmd_arg_dict, mtu_dict]
            else:
                arg_list = ["mtuget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_port(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["enable", cmd_arg_dict]
            else:
                arg_list = ["disable", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_link_pause(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["lpena", cmd_arg_dict]
            else:
                arg_list = ["lpdis", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_tx_link_pause(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["lptxon", cmd_arg_dict]
            else:
                arg_list = ["lptxoff", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def port_pause_quanta(self, port_num, shape, quanta=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if quanta is not None:
                arg_dict = {"quanta": quanta}
                arg_list = ["lpqset", cmd_arg_dict, arg_dict]
            else:
                arg_list = ["lpqget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def port_pause_threshold(self, port_num, shape, threshold=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if threshold is not None:
                arg_dict = {"threshold": threshold}
                arg_list = ["lptset", cmd_arg_dict, arg_dict]
            else:
                arg_list = ["lptget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_pfc(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["pfcena", cmd_arg_dict]
            else:
                arg_list = ["pfcdis", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_tx_pfc(self, port_num, shape, class_num, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["pfctxon", cmd_arg_dict, {'class': class_num}]
            else:
                arg_list = ["pfctxoff", cmd_arg_dict, {'class': class_num}]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def port_pfc_quanta(self, port_num, shape, class_num=None, quanta=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if quanta is not None:
                arg_dict = {"class": class_num, "quanta": quanta}
                arg_list = ["pfcqset", cmd_arg_dict, arg_dict]
            else:
                arg_list = ["pfcqget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def port_pfc_threshold(self, port_num, shape, class_num=None, threshold=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if threshold is not None:
                arg_dict = {"class": class_num, "threshold": threshold}
                arg_list = ["pfctset", cmd_arg_dict, arg_dict]
            else:
                arg_list = ["pfctget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_ptp_peer_delay(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["ptppeerdelayena", cmd_arg_dict]
            else:
                arg_list = ["ptppeerdelaydis", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ptp_peer_delay(self, port_num, shape, delay=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if delay is not None:
                arg_dict = {"delay": delay}
                arg_list = ["ptppeerdelayset", cmd_arg_dict, arg_dict]
            else:
                arg_list = ["ptppeerdelayget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def get_ptp_tx_ts(self, port_num, shape):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb="port", arg_list=["ptptxtsget", cmd_arg_dict])
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def enable_disable_ptp_1step(self, port_num, shape, enable=True):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if enable:
                arg_list = ["ptp1stepena", cmd_arg_dict]
            else:
                arg_list = ["ptp1stepdis", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def set_runt_filter(self, port_num, shape, buffer, runt_err_en, en_delete):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            runt_dict = {"buffer_64": buffer, "runt_err_en": runt_err_en, "en_delete": en_delete}
            result = self.dpc_client.execute(verb='port', arg_list=["runtfilterset", cmd_arg_dict, runt_dict])
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def dump_runt_filter(self, port_num, shape):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb='port', arg_list=["runtfilterdump", cmd_arg_dict])
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)


class SystemCommands(object):
    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def time_interval(self, time_interval=None):
        global TIME_INTERVAL
        if time_interval:
            TIME_INTERVAL = time_interval
            print "Time interval between stats iteration set to %d secs" % TIME_INTERVAL
        else:
            print TIME_INTERVAL

    def system_syslog_level(self, level_val=None):
        try:
            if level_val:
                result = self.dpc_client.execute(verb="poke", arg_list=["params/syslog/level", level_val])
                print result
            else:
                cmd = "params/syslog/level"
                result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)


class QosCommands(object):
    SCHEDULER_TYPE_DWRR = 'dwrr'
    SCHEDULER_TYPE_SHAPER = 'shaper'
    SCHEDULER_TYPE_STRICT = 'strict_priority'

    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def egress_buffer_pool(self, sf_thr=None, sx_thr=None, df_thr=None, dx_thr=None, fcp_thr=None, nonfcp_thr=None,
                           sample_copy_thr=None, sf_xoff_thr=None, fcp_xoff_thr=None, nonfcp_xoff_thr=None,
                           update_config=True):
        try:
            get_cmd_arg_list = ['get', 'egress_buffer_pool']
            buffer_config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_arg_list)
            if update_config:
                if sf_thr is not None:
                    buffer_config['sf_thr'] = sf_thr
                if sx_thr is not None:
                    buffer_config['sx_thr'] = sx_thr
                if df_thr is not None:
                    buffer_config['df_thr'] = df_thr
                if dx_thr is not None:
                    buffer_config['dx_thr'] = dx_thr
                if fcp_thr is not None:
                    buffer_config['fcp_thr'] = fcp_thr
                if nonfcp_thr is not None:
                    buffer_config['nonfcp_thr'] = nonfcp_thr
                if sample_copy_thr is not None:
                    buffer_config['sample_copy_thr'] = sample_copy_thr
                if sf_xoff_thr is not None:
                    buffer_config['sf_xoff_thr'] = sf_xoff_thr
                if fcp_xoff_thr is not None:
                    buffer_config['fcp_xoff_thr'] = fcp_xoff_thr
                if nonfcp_xoff_thr is not None:
                    buffer_config['nonfcp_xoff_thr'] = nonfcp_xoff_thr

                set_cmd_arg_list = ['set', 'egress_buffer_pool', buffer_config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_arg_list)
                print result
            else:
                self._display_qos_config(config_dict=buffer_config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def _display_qos_config(self, config_dict, column_list=['Field Name', 'Value']):
        try:
            table_obj = PrettyTable(column_list)
            table_obj.align = "l"
            for key in sorted(config_dict):
                table_obj.add_row([key, config_dict[key]])
            print table_obj
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def egress_port_buffer(self, port_num, min_thr=None, shared_thr=None, update_config=True):
        try:
            get_cmd_arg_list = ['get', 'egress_port_buffer', {"port": port_num}]
            buffer_config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_arg_list)
            buffer_config['port'] = port_num
            if update_config:
                if min_thr is not None:
                    buffer_config['min_thr'] = min_thr
                if shared_thr is not None:
                    buffer_config['shared_thr'] = shared_thr

                set_cmd_arg_list = ['set', 'egress_port_buffer', buffer_config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_arg_list)
                print result
            else:
                self._display_qos_config(config_dict=buffer_config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def egress_queue_buffer(self, port_num, queue, min_thr=None, static_shared_thr_green=None, dynamic_enable=None,
                            shared_thr_alpha=None, shared_thr_offset_yellow=None, shared_thr_offset_red=None,
                            update_config=True):
        try:
            get_cmd_arg_list = ['get', 'egress_queue_buffer', {"port": port_num, "queue": queue}]
            buffer_config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_arg_list)
            buffer_config['port'] = port_num
            buffer_config['queue'] = queue
            if update_config:
                if min_thr is not None:
                    buffer_config['min_thr'] = min_thr
                if static_shared_thr_green is not None:
                    buffer_config['static_shared_thr_green'] = static_shared_thr_green
                if dynamic_enable is not None:
                    buffer_config['dynamic_enable'] = dynamic_enable
                if shared_thr_alpha is not None:
                    buffer_config['shared_thr_alpha'] = shared_thr_alpha
                if shared_thr_offset_yellow is not None:
                    buffer_config['shared_thr_offset_yellow'] = shared_thr_offset_yellow
                if shared_thr_offset_red is not None:
                    buffer_config['shared_thr_offset_red'] = shared_thr_offset_red

                set_cmd_arg_list = ['set', 'egress_queue_buffer', buffer_config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_arg_list)
                print result
            else:
                self._display_qos_config(config_dict=buffer_config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def egress_queue_to_priority_map(self, port_num, map_list=None, update=True):
        try:
            get_cmd_args = ['get', 'queue_to_priority_map', {"port": port_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            if update:
                if map_list:
                    config["map"] = [int(x) for x in map_list] 
                set_cmd_args = ['set', 'queue_to_priority_map', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_glb_sh_threshold(self, en=None, green=None, red=None, yellow=None, update=True):
        try:
            get_cmd_args = ['get', 'ecn_glb_sh_thresh']
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if update:
                if en is not None:
                    config['en'] = en
                if green is not None:
                    config['green'] = green
                if red is not None:
                    config['red'] = red
                if yellow is not None:
                    config['yellow'] = yellow

                set_cmd_args = ['set', 'ecn_glb_sh_thresh', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_profile(self, prof_num, min_thr=None, max_thr=None, ecn_prob_index=None, update=True):
        try:
            get_cmd_args = ['get', 'ecn_profile', {'prof_num': prof_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prof_num'] = prof_num
            if update:
                if min_thr is not None:
                    config['min_thr'] = min_thr
                if max_thr is not None:
                    config['max_thr'] = max_thr
                if ecn_prob_index is not None:
                    config['ecn_prob_index'] = ecn_prob_index

                set_cmd_args = ['set', 'ecn_profile', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_prob(self, prob_idx, prob=None, update=True):
        try:
            get_cmd_args = ['get', 'ecn_prob', {'prob_idx': prob_idx}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prob_idx'] = prob_idx
            if update:
                if prob is not None:
                    config['prob'] = prob
                set_cmd_args = ['set', 'ecn_prob', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_profile(self, prof_num, min_thr=None, max_thr=None, wred_prob_index=None, update=True):
        try:
            get_cmd_args = ['get', 'wred_profile', {'prof_num': prof_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prof_num'] = prof_num
            if update:
                if min_thr is not None:
                    config['min_thr'] = min_thr
                if max_thr is not None:
                    config['max_thr'] = max_thr
                if wred_prob_index is not None:
                    config['wred_prob_index'] = wred_prob_index

                set_cmd_args = ['set', 'wred_profile', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_prob(self, prob_idx, prob=None, update=True):
        try:
            get_cmd_args = ['get', 'wred_prob', {'prob_idx': prob_idx}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prob_idx'] = prob_idx
            if update:
                if prob is not None:
                    config['prob'] = prob
                set_cmd_args = ['set', 'wred_prob', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_queue_config(self, port_num, queue_num, wred_en=None, wred_weight=None, wred_prof_num=None, ecn_en=None,
                          ecn_prof_num=None, update=True):
        try:
            get_cmd_args = ['get', 'wred_queue_config', {'port': port_num, "queue": queue_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            config['queue'] = queue_num
            if update:
                if wred_en is not None:
                    config['wred_en'] = wred_en
                if wred_weight is not None:
                    config['wred_weight'] = wred_weight
                if wred_prof_num is not None:
                    config['wred_prof_num'] = wred_prof_num
                if ecn_en is not None:
                    config['ecn_en'] = ecn_en
                if ecn_prof_num is not None:
                    config['ecn_prof_num'] = ecn_prof_num

                set_cmd_args = ['set', 'wred_queue_config', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_avg_q_config(self, q_avg_en=None, cap_avg_sz=None, avg_period=None, update=True):
        try:
            get_cmd_args = ['get', 'wred_avg_q_config']
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if update:
                if q_avg_en is not None:
                    config["avg_en"] = q_avg_en
                    # del config['avg_en']
                if cap_avg_sz is not None:
                    config['cap_avg_sz'] = cap_avg_sz
                if avg_period is not None:
                    config['avg_period'] = avg_period
                set_cmd_args = ['set', 'wred_avg_q_config', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def get_scheduler_config(self, port_num, queue_num, scheduler_type=None):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            result = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if scheduler_type == self.SCHEDULER_TYPE_DWRR:
                config = result['dwrr']
                config['port_num'] = port_num
                config['queue'] = queue_num
                self._display_qos_config(config_dict=config, column_list=['Scheduler %s' %
                                                                          self.SCHEDULER_TYPE_DWRR, 'Config'])
            elif scheduler_type == self.SCHEDULER_TYPE_SHAPER:
                config = result['shaper']
                config['port_num'] = port_num
                config['queue'] = queue_num
                self._display_qos_config(config_dict=config,
                                         column_list=['Scheduler %s' % self.SCHEDULER_TYPE_SHAPER, 'Config'])
            elif scheduler_type == self.SCHEDULER_TYPE_STRICT:
                config = result['strict_priority']
                config['port_num'] = port_num
                config['queue'] = queue_num
                self._display_qos_config(config_dict=config,
                                         column_list=['Scheduler %s' % self.SCHEDULER_TYPE_STRICT, 'Config'])
            else:
                table_obj = PrettyTable(["Scheduler Type", "Config"])
                for key in result:
                    inner_table_obj = PrettyTable(['Config', 'Value'])
                    inner_table_obj.align = 'l'
                    config = result[key]
                    config['port_num'] = port_num
                    config['queue'] = queue_num
                    for _key in sorted(config):
                        inner_table_obj.add_row([_key, config[_key]])
                    table_obj.add_row([key, inner_table_obj])
                print table_obj
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def scheduler_config_dwrr(self, port_num, queue_num, weight):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            result = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            dwrr_config = result['dwrr']
            dwrr_config['weight'] = weight
            dwrr_config['port'] = port_num
            dwrr_config['queue'] = queue_num
            set_cmd_args = ['set', 'scheduler_config', 'dwrr', dwrr_config]
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def scheduler_config_shaper(self, port_num, queue_num, shaper_enable=None, shaper_type=0, shaper_rate=None, shaper_threshold=None):
        try:
            shaper_config = {}
            shaper_config['port'] = port_num
            shaper_config['queue'] = queue_num
            shaper_config['type'] = shaper_type
            if shaper_enable is not None:
                shaper_config['en'] = shaper_enable
            if shaper_rate is not None:
                shaper_config['rate'] = shaper_rate
            if shaper_threshold is not None:
                shaper_config['thresh'] = shaper_threshold
            set_cmd_args = ['set', 'scheduler_config', 'shaper', shaper_config]
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def scheduler_config_strict_priority(self, port_num, queue_num, strict_priority_enable=None, extra_bandwidth=None):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            result = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            strict_priority_config = result['strict_priority']
            strict_priority_config['port'] = port_num
            strict_priority_config['queue'] = queue_num
            if strict_priority_enable is not None:
                strict_priority_config['strict_priority_enable'] = strict_priority_enable
            if extra_bandwidth is not None:
                strict_priority_config['extra_bandwidth'] = extra_bandwidth
            set_cmd_args = ['set', 'scheduler_config', 'shaper', strict_priority_config]
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ingress_priority_group(self, port_num, pg_num, min_thr=None, shared_thr=None, headroom_thr=None,
                               xoff_enable=None, shared_xon_thr=None, update=True):
        try:
            get_cmd_args = ['get', 'ingress_priority_group', {"port": port_num, "pg": pg_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            config['pg'] = pg_num
            if update:
                if min_thr is not None:
                    config["min_thr"] = min_thr
                if shared_thr is not None:
                    config['shared_thr'] = shared_thr
                if headroom_thr is not None:
                    config['headroom_thr'] = headroom_thr
                if xoff_enable is not None:
                    config['xoff_enable'] = xoff_enable
                if shared_xon_thr is not None:
                    config['shared_xon_thr'] = shared_xon_thr
                set_cmd_args = ['set', 'ingress_priority_group', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ingress_priority_to_pg_map(self, port_num, map_list=None, update=True):
        try:
            get_cmd_args = ['get', 'priority_to_pg_map', {"port": port_num}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            if update:
                if map_list is not None:
                    config["map"] = [int(x) for x in map_list]
                set_cmd_args = ['set', 'priority_to_pg_map', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def pfc(self, enable=None, update=True, disable=None):
        try:
            if update:
                config = {}
                if enable is not None:
                    config["enable"] = 1
                elif disable is not None:
                    config['enable'] = 0
                set_cmd_args = ['set', 'pfc', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                get_cmd_args = ['get', 'pfc']
                config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def arb_cfg(self, en=None, update=True):
        try:
            get_cmd_args = ['get', 'arb_cfg']
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if update:
                if en is not None:
                    config["en"] = en
                set_cmd_args = ['set', 'arb_cfg', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def xoff_status(self, port_num, pg, status=None, update=True):
        try:
            get_cmd_args = ['get', 'xoff_status', {'port': port_num, 'pg': pg}]
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            config['pg'] = pg
            if update:
                if status is not None:
                    config["status"] = status
                set_cmd_args = ['set', 'xoff_status', config]
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

class NuClearCommands(object):

    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def clear_nu_port_stats(self, port_num, shape):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            result = self.dpc_client.execute(verb="port", arg_list=["clearstats", cmd_arg_dict])
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def clear_nu_fwd_stats(self):
        try:
            cmd = ["clear", "fwd"] 
            result = self.dpc_client.execute(verb="nu", arg_list=cmd)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def clear_nu_erp_stats(self):
        try:
            cmd = ["clear", "erp"]
            result = self.dpc_client.execute(verb="nu", arg_list=cmd)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def clear_nu_parser_stats(self):
        try:
            cmd = ["clear", "prsr"]
            result = self.dpc_client.execute(verb="nu", arg_list=cmd)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def clear_nu_all_stats(self):
        try:
            cmd = ["clear"]
            result = self.dpc_client.execute(verb="nu", arg_list=cmd)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)


class PeekCommands(object):

    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def _get_timestamp(self):
        ts = time.time()
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    def _get_difference(self, result, prev_result):
        """
        :param result: Should be dict or dict of dict
        :param prev_result: Should be dict or dict of dict
        :return: dict or dict of dict
        """
        diff_result = {}
        for key in result:
            if type(result[key]) == dict:
                diff_result[key] = {}
                for _key in result[key]:
                    if key in prev_result and _key in prev_result[key]:
                        if type(result[key][_key]) == dict:
                            diff_result[key][_key] = {}
                            for inner_key in result[key][_key]:
                                if inner_key in prev_result[key][_key]:
                                    diff_value = result[key][_key][inner_key] - prev_result[key][_key][inner_key]
                                    diff_result[key][_key][inner_key] = diff_value
                                else:
                                    diff_result[key][_key][inner_key] = 0
                        else:
                            diff_value = result[key][_key] - prev_result[key][_key]
                            diff_result[key][_key] = diff_value
                    else:
                        diff_result[key][_key] = 0
            else:
                if key in prev_result:
                    if type(result[key]) == list:
                        diff_result[key] = result[key]
                        continue
                    diff_value = result[key] - prev_result[key]
                    diff_result[key] = diff_value
                else:
                    diff_result[key] = 0

        return diff_result

    def _sort_bam_keys(self, result):
        pool_map = {}
        sorted_dict = OrderedDict()
        for key in result:
            if re.search(r'AU.*', key):
                k = key.split()[4]
                pool_map[key] = int(k)
            else:
                pool_map[key] = result[key]
        sorted_keys = sorted(result, key=pool_map.__getitem__)
        for key in sorted_keys:
            sorted_dict[key] = result[key]
        return sorted_dict

    def peek_fpg_stats(self, port_num, grep_regex=None, mode='nu'):
        prev_result = {}
        result = None
        while True:
            try:
                master_table_obj = PrettyTable()
                master_table_obj.border = False
                master_table_obj.align = 'l'
                master_table_obj.header = False
                cmd = "stats/fpg/%s/port[%d]" % (mode, port_num)
                result_list = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                if result_list:
                    result = result_list[0]
                    if prev_result:
                        diff_result = self._get_difference(result=result, prev_result=prev_result)
                        tx_table_obj = PrettyTable(['Port %d Tx Stats' % port_num, 'Counter', 'Counter diff'])
                        rx_table_obj = PrettyTable(['Port %d Rx Stats' % port_num, 'Counter', 'Counter diff'])
                        tx_table_obj.align = 'l'
                        tx_table_obj.sortby = "Port %d Tx Stats" % port_num
                        rx_table_obj.align = 'l'
                        rx_table_obj.sortby = "Port %d Rx Stats" % port_num
                        for key in result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    if re.search(r'.*tx.*', key, re.IGNORECASE):
                                        tx_table_obj.add_row([key, result[key], diff_result[key]])
                                    else:
                                        rx_table_obj.add_row([key, result[key], diff_result[key]])
                            else:
                                if re.search(r'.*tx.*', key, re.IGNORECASE):
                                    tx_table_obj.add_row([key, result[key], diff_result[key]])
                                else:
                                    rx_table_obj.add_row([key, result[key], diff_result[key]])
                        prev_result = result
                        if tx_table_obj.rowcount > 1:
                            master_table_obj.add_column('Tx Stats', [tx_table_obj])
                        if rx_table_obj.rowcount > 1:
                            master_table_obj.add_column('Rx Stats', [rx_table_obj])
                    else:
                        tx_table_obj = PrettyTable(['Port %d Tx Stats' % port_num, 'Counter'])
                        rx_table_obj = PrettyTable(['Port %d Rx Stats' % port_num, 'Counter'])
                        tx_table_obj.align = 'l'
                        tx_table_obj.sortby = "Port %d Tx Stats" % port_num
                        rx_table_obj.align = 'l'
                        rx_table_obj.sortby = "Port %d Rx Stats" % port_num
                        for key in result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    if re.search(r'.*tx.*', key, re.IGNORECASE):
                                        tx_table_obj.add_row([key, result[key]])
                                    else:
                                        rx_table_obj.add_row([key, result[key]])
                            else:
                                if re.search(r'.*tx.*', key, re.IGNORECASE):
                                    tx_table_obj.add_row([key, result[key]])
                                else:
                                    rx_table_obj.add_row([key, result[key]])
                        prev_result = result
                        if tx_table_obj.rowcount > 1:
                            master_table_obj.add_column('Tx Stats', [tx_table_obj])
                        if rx_table_obj.rowcount > 1:
                            master_table_obj.add_column('Rx Stats', [rx_table_obj])
                print master_table_obj
                print "\n########################  %s ########################\n" % str(self._get_timestamp())
                time.sleep(TIME_INTERVAL)
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
                break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()

    def peek_meter_stats(self, bank, index, grep_regex=None, erp=False):
        prev_result = {}
        while True:
            try:
                if erp:
                    cmd = "stats/meter/erp/bank/%d/meter[%d]" % (bank, index)
                else:
                    cmd = "stats/meter/nu/bank/%d/meter[%d]" % (bank, index)
                result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                print "--------------> Meter %d  <--------------" % index
                table_obj = None
                if result:
                    if prev_result:
                        diff_result = self._get_difference(result=result, prev_result=prev_result)
                        table_obj = PrettyTable(['Color', 'Bytes', 'Bytes Diff', 'Packet', 'Packet Diff'])
                        for key in sorted(result):
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    table_obj.add_row([key, result[key]['bytes'],
                                                       diff_result[key]['bytes'],
                                                       result[key]['pkts'],
                                                       diff_result[key]['pkts']])
                            else:
                                table_obj.add_row([key, result[key]['bytes'],
                                                   diff_result[key]['bytes'],
                                                   result[key]['pkts'],
                                                   diff_result[key]['pkts']])
                    else:
                        table_obj = PrettyTable(['Color', 'Bytes', 'Packet'])
                        for key in sorted(result):
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    table_obj.add_row([key, result[key]['bytes'], result[key]['pkts']])
                            else:
                                table_obj.add_row([key, result[key]['bytes'], result[key]['pkts']])
                prev_result = result
                print table_obj
                print "\n########################  %s ########################\n" % str(self._get_timestamp())
                time.sleep(TIME_INTERVAL)
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
                break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()
                break
                
    def peek_psw_stats(self, mode='nu', port_num=None, queue_list=None, grep_regex=None):
        prev_result = None
        while True:
            try:
                is_global = False
                if port_num is None:
                    is_global = True
                    cmd = "stats/psw/%s/global" % mode
                else:
                    cmd = "stats/psw/%s/port/[%d]" % (mode, port_num)
                master_table_obj = PrettyTable()
                master_table_obj.header = False
                master_table_obj.border = False
                master_table_obj.align = 'l'
                result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                if is_global:
                    if prev_result:
                        diff_result = self._get_difference(result=result, prev_result=prev_result)
                        for key in sorted(result):
                            table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            for _key in result[key]:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                else:
                                    if type(result[key][_key]) == dict:
                                        inner_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                                        inner_table_obj.align = 'l'
                                        inner_table_obj.sortby = 'Field Name'
                                        for inner_key in result[key][_key]:
                                            inner_table_obj.add_row([inner_key, result[key][_key][inner_key],
                                                                     diff_result[key][_key][inner_key]])
                                        table_obj.add_row([_key, inner_table_obj, ""])
                                    else:
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                            if table_obj.rowcount > 0:
                                master_table_obj.add_row([key, table_obj])
                    else:
                        for key in sorted(result):
                            table_obj = PrettyTable(['Field Name', 'Counters'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            for _key in result[key]:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([_key, result[key][_key]])
                                else:
                                    if type(result[key][_key]) == dict:
                                        inner_table_obj = PrettyTable(['Field Name', 'Counters'])
                                        inner_table_obj.align = 'l'
                                        inner_table_obj.sortby = 'Field Name'
                                        for inner_key in result[key][_key]:
                                            inner_table_obj.add_row([inner_key, result[key][_key][inner_key]])
                                        table_obj.add_row([_key, inner_table_obj])
                                    else:
                                        table_obj.add_row([_key, result[key][_key]])
                            if table_obj.rowcount > 0:
                                master_table_obj.add_row([key, table_obj])
                else:
                    print "--------------> Port %d  <--------------" % port_num
                    if prev_result:
                        for queue in result:
                            count_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Bytes Diff', 'Packets',
                                                           'Packets Diff'])
                            drops_table_obj = PrettyTable(['Drops Type', 'Count', 'Drop Count Diff'])

                            m = re.search(r'q_\d+', queue)
                            if not m:
                                diff = result[queue] - prev_result[queue]
                                master_table_obj.add_row(['Orm Port Shared Drops', result[queue], diff])
                                continue
                            queue_result = result[queue]
                            count_result = queue_result['count']
                            drop_result = queue_result['drops']

                            diff_count_result = self._get_difference(result=count_result,
                                                                     prev_result=prev_result[queue]['count'])
                            diff_drop_result = self._get_difference(result=drop_result,
                                                                    prev_result=prev_result[queue]['drops'])
                            for key in count_result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        count_table_obj.add_row([key, count_result[key]['bytes'],
                                                                 diff_count_result[key]['bytes'],
                                                                 count_result[key]['pkts'],
                                                                 diff_count_result[key]['pkts']])
                                else:
                                    count_table_obj.add_row([key, count_result[key]['bytes'],
                                                             diff_count_result[key]['bytes'],
                                                             count_result[key]['pkts'],
                                                             diff_count_result[key]['pkts']])

                            for key in drop_result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        drops_table_obj.add_row([key, drop_result[key], diff_drop_result[key]])
                                else:
                                    drops_table_obj.add_row([key, drop_result[key], diff_drop_result[key]])

                            if queue_list:
                                if queue in queue_list:
                                    master_table_obj.add_row([queue, count_table_obj, drops_table_obj])

                            else:
                                master_table_obj.add_row([queue, count_table_obj, drops_table_obj])
                    else:
                        for queue in result:
                            count_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Packets'])
                            drops_table_obj = PrettyTable(['Drops Type', 'Count'])

                            m = re.search(r'q_\d+', queue)
                            if not m:
                                master_table_obj.add_row(['Orm Port Shared Drops', result[queue], None])
                                continue
                            queue_result = result[queue]
                            count_result = queue_result['count']
                            drop_result = queue_result['drops']

                            for key in count_result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        count_table_obj.add_row([key, count_result[key]['bytes'],
                                                                 count_result[key]['pkts']])
                                else:
                                    count_table_obj.add_row([key, count_result[key]['bytes'],
                                                            count_result[key]['pkts']])
                            for key in drop_result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        drops_table_obj.add_row([key, drop_result[key]])
                                else:
                                    drops_table_obj.add_row([key, drop_result[key]])
                            if queue_list:
                                if queue in queue_list:
                                    master_table_obj.add_row([queue, count_table_obj, drops_table_obj])

                            else:
                                master_table_obj.add_row([queue, count_table_obj, drops_table_obj])
                    master_table_obj.border = True
                    master_table_obj.sortby = 'Field 1'
                    master_table_obj.header = False
                    master_table_obj.hrules = FRAME

                prev_result = result
                print master_table_obj
                print "\n########################  %s ########################\n" % str(self._get_timestamp())
                time.sleep(TIME_INTERVAL)
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
                break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()
                break
     
    def _display_stats(self, cmd, grep_regex, prev_result=None, verb="peek"):
        try:
            while True:
                try:
                    if type(cmd) == list:
                        result = self.dpc_client.execute(verb=verb, arg_list=cmd)
                    else:
                        result = self.dpc_client.execute(verb=verb, arg_list=[cmd])
                    if 'bam' in cmd:
                        result = self._sort_bam_keys(result=result)
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            table_obj = PrettyTable(['Field Name', 'Counters', 'Diff Counters'])
                            table_obj.align = 'l'
                            if 'bam' not in cmd:
                                table_obj.sortby = 'Field Name'
                            for key in result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result[key], diff_result[key]])
                                else:
                                    table_obj.add_row([key, result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counters'])
                            table_obj.align = 'l'
                            if 'bam' not in cmd:
                                table_obj.sortby = 'Field Name'
                            for key in result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result[key]])
                                else:
                                    table_obj.add_row([key, result[key]])

                        prev_result = result
                        print table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _display_all_erp_stats(self, grep_regex, global_prev_result=None, nu_prev_result=None, hnu_prev_result=None,
                               nuflex_prev_result=None):
        try:
            while True:
                try:
                    result = self.dpc_client.execute(verb='peek', arg_list=['stats/erp'])
                    if result:
                        global_result = result['global']
                        hnu_result = result['hnu']
                        nu_result = result['nu']
                        # Assuming NU Flex result has list of only single dict in it
                        if result['nuflex']:
                            nuflex_result = result['nuflex'][0]
                        else:
                            nuflex_result = {}
                    master_table_obj = PrettyTable()
                    master_table_obj.border = False
                    master_table_obj.align = 'l'

                    if global_prev_result or nu_prev_result or hnu_prev_result or nuflex_prev_result:
                        global_diff_result = self._get_difference(result=global_result,
                                                                  prev_result=global_prev_result)
                        nu_diff_result = self._get_difference(result=nu_result, prev_result=nu_prev_result)
                        hnu_diff_result = self._get_difference(result=hnu_result, prev_result=hnu_prev_result)
                        nuflex_diff_result = self._get_difference(result=nuflex_result,
                                                                  prev_result=nuflex_prev_result)

                        global_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                        global_table_obj.align = 'l'
                        nu_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                        nu_table_obj.align = 'l'
                        hnu_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                        hnu_table_obj.align = 'l'
                        nuflex_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                        nuflex_table_obj.align = 'l'
                        for key in global_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    global_table_obj.add_row([key, global_result[key], global_diff_result[key]])
                            else:
                                global_table_obj.add_row([key, global_result[key], global_diff_result[key]])
                        if global_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP Global Result', [global_table_obj])

                        for key in nu_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    nu_table_obj.add_row([key, nu_result[key], nu_diff_result[key]])
                            else:
                                nu_table_obj.add_row([key, nu_result[key], nu_diff_result[key]])
                        if nu_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP NU Result', [nu_table_obj])

                        for key in hnu_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    hnu_table_obj.add_row([key, hnu_result[key], hnu_diff_result[key]])
                            else:
                                hnu_table_obj.add_row([key, hnu_result[key], hnu_diff_result[key]])
                        if hnu_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP HNU Result', [hnu_table_obj])

                        for key in nuflex_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    nuflex_table_obj.add_row([key, nuflex_result[key], nuflex_diff_result[key]])
                            else:
                                nuflex_table_obj.add_row([key, nuflex_result[key], nuflex_diff_result[key]])
                        if nuflex_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP NU Flex Result', [nuflex_table_obj])
                    else:
                        global_table_obj = PrettyTable(['Field Name', 'Counters'])
                        global_table_obj.align = 'l'
                        nu_table_obj = PrettyTable(['Field Name', 'Counters'])
                        nu_table_obj.align = 'l'
                        hnu_table_obj = PrettyTable(['Field Name', 'Counters'])
                        hnu_table_obj.align = 'l'
                        nuflex_table_obj = PrettyTable(['Field Name', 'Counters'])
                        nuflex_table_obj.align = 'l'
                        for key in global_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    global_table_obj.add_row([key, global_result[key]])
                            else:
                                global_table_obj.add_row([key, global_result[key]])
                        if global_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP Global Result', [global_table_obj])

                        for key in nu_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    nu_table_obj.add_row([key, nu_result[key]])
                            else:
                                nu_table_obj.add_row([key, nu_result[key]])
                        if nu_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP NU Result', [nu_table_obj])

                        for key in hnu_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    hnu_table_obj.add_row([key, hnu_result[key]])
                            else:
                                hnu_table_obj.add_row([key, hnu_result[key]])
                        if hnu_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP HNU Result', [hnu_table_obj])

                        for key in nuflex_result:
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    nuflex_table_obj.add_row([key, nuflex_result[key]])
                            else:
                                nuflex_table_obj.add_row([key, nuflex_result[key]])
                        if nuflex_table_obj.rowcount > 0:
                            master_table_obj.add_column('ERP NU Flex Result', [nuflex_table_obj])

                    global_prev_result = global_result
                    nu_prev_result = nu_result
                    hnu_prev_result = hnu_result
                    nuflex_prev_result = nuflex_result
                    print master_table_obj
                    print "\n########################  %s ########################\n" % str(self._get_timestamp())
                    time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_vp_stats(self, grep_regex=None):
        cmd = "stats/vppkts"
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_fcp_stats(self, tunnel_id=None, grep_regex=None):
        cmd = "stats/fcp/global"
        if tunnel_id:
            cmd = "stats/fcp/tunnel[%d]" % tunnel_id
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_wro_stats(self, cmd_type, tunnel_id=None, grep_regex=None):
        if tunnel_id:
            cmd = "stats/wro/%s/tunnel[%d]" % (cmd_type, tunnel_id)
        else:
            cmd = "stats/wro/%s/global" % cmd_type
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_bam_stats(self, grep_regex=None):
        cmd = "stats/bam"
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_fwd_stats(self, grep_regex=None):
        cmd = "stats/fwd/flex"
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_erp_stats(self, cmd_type, grep_regex=None):
        if cmd_type == "hnu":
            cmd = "stats/erp/hnu/global"
            self._display_stats(cmd=cmd, grep_regex=grep_regex)
        elif cmd_type == 'nu':
            cmd = "stats/erp/nu/global"
            self._display_stats(cmd=cmd, grep_regex=grep_regex)
        else:
            try:
                prev_result_list = None
                while True:
                    try:
                        cmd = "stats/erp/flex"
                        result_list = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                        if result_list:
                            if prev_result_list:
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for result in sorted(result_list):
                                    diff_result = self._get_difference(result=result,
                                                                       prev_result=prev_result_list[0])
                                    for key in sorted(result):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([key, result[key], diff_result[key]])
                                        else:
                                            table_obj.add_row([key, result[key], diff_result[key]])
                            else:
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for result in sorted(result_list):
                                    for key in sorted(result):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([key, result[key]])
                                        else:
                                            table_obj.add_row([key, result[key]])
                            prev_result_list = result_list
                            print table_obj
                            print "\n########################  %s ########################\n" % \
                                  str(self._get_timestamp())
                            time.sleep(TIME_INTERVAL)
                        else:
                            print "Empty Result"
                    except KeyboardInterrupt:
                        self.dpc_client.disconnect()
                        break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()

    def peek_parser_nu_stats(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/prsr/nu"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False
                    global_result = result['global']
                    if global_result:
                        if prev_result:
                            diff_result = self._get_difference(result=global_result, prev_result=prev_result)
                            for key in sorted(global_result):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(global_result[key]):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, global_result[key][_key], diff_result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, global_result[key][_key], diff_result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(global_result):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(global_result[key]):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, global_result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, global_result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                    else:
                        print "Empty Result"

                    prev_result = global_result
                    print master_table_obj
                    print "\n########################  %s ########################\n" % str(self._get_timestamp())
                    time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_parser_hnu_stats(self, grep_regex=None):
        # TODO: Currently this cmd is crashing on palladium. Implement it later
        pass

    def peek_wred_ecn_stats(self, port_num, queue_num, grep_regex=None):
        cmd = ["get", "wred_ecn_stats", {"port": port_num, "queue": queue_num}]
        self._display_stats(cmd=cmd, verb='qos', grep_regex=grep_regex)

    def peek_sfg_stats(self, stats_type, grep_regex=None):
        if stats_type == "nu":
            cmd = "stats/sfg/nu"
            self._display_stats(cmd=cmd, grep_regex=grep_regex)
        elif stats_type == "hnu":
            cmd = "stats/sfg/hnu"
            self._display_stats(cmd=cmd, grep_regex=grep_regex)
        else:
            try:
                prev_result = None
                while True:
                    try:
                        cmd = "stats/sfg"
                        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                        master_table_obj = PrettyTable()
                        master_table_obj.align = 'l'
                        master_table_obj.border = False
                        master_table_obj.header = True
                        if result:
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, _key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    master_table_obj.add_column(key, [table_obj])
                            else:
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, _key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key]])

                                    master_table_obj.add_column(key, [table_obj])
                            prev_result = result
                            print master_table_obj
                            print "\n########################  %s ########################\n" % \
                                  str(self._get_timestamp())
                            time.sleep(TIME_INTERVAL)
                    except KeyboardInterrupt:
                        self.dpc_client.disconnect()
                        break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()

    def _get_vp_number_key(self, output_dict, vp_number):
        result = None
        try:
            dict_keys = output_dict.keys()
            for key in dict_keys:
                if int(key.split(":")[1]) == int(vp_number):
                    result = key
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return result

    def peek_stats_per_vp(self, vp_number=None, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/per_vp"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False
                    if result:
                        if vp_number:
                            vp_key = self._get_vp_number_key(output_dict=result, vp_number=vp_number)
                            result = result[vp_key]
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(result):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[_key], diff_result[_key]])
                                    else:
                                        table_obj.add_row([_key, result[_key], diff_result[_key]])
                                master_table_obj.add_row([table_obj])
                            else:
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(result):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[_key]])
                                    else:
                                        table_obj.add_row([_key, result[_key]])
                                master_table_obj.add_row([table_obj])
                        else:
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                            else:
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    table_obj.align = 'l'
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_nwqm_stats(self, grep_regex=None):
        try:
            prev_results = None
            while True:
                try:
                    cmd = "stats/nwqm"
                    results = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    result = results[""]
                    if result:
                        if prev_results:
                            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            table_obj.align = 'l'
                            diff_result = self._get_difference(result=result, prev_result=prev_results)
                            for key in sorted(result):
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result[key], diff_result[key]])
                                else:
                                    table_obj.add_row([key, result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counter'])
                            table_obj.align = 'l'
                            for key in sorted(result):
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result[key]])
                                else:
                                    table_obj.add_row([key, result[key]])
                        prev_results = result
                        print table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_mpg_stats(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    master_table_obj = PrettyTable()
                    master_table_obj.border = False
                    master_table_obj.align = 'l'
                    master_table_obj.header = False
                    cmd = "stats/mpg"
                    result_list = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result_list:
                        result = result_list['port'][0]
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            tx_table_obj = PrettyTable(['Tx Stats', 'Counter', 'Counter diff'])
                            rx_table_obj = PrettyTable(['Rx Stats', 'Counter', 'Counter diff'])
                            tx_table_obj.align = 'l'
                            tx_table_obj.sortby = "Tx Stats"
                            rx_table_obj.align = 'l'
                            rx_table_obj.sortby = "Rx Stats"
                            for key in result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        if re.search(r'.*tx.*', key, re.IGNORECASE):
                                            tx_table_obj.add_row([key, result[key], diff_result[key]])
                                        else:
                                            rx_table_obj.add_row([key, result[key], diff_result[key]])
                                else:
                                    if re.search(r'.*tx.*', key, re.IGNORECASE):
                                        tx_table_obj.add_row([key, result[key], diff_result[key]])
                                    else:
                                        rx_table_obj.add_row([key, result[key], diff_result[key]])
                            prev_result = result
                            if tx_table_obj.rowcount > 1:
                                master_table_obj.add_column('Tx Stats', [tx_table_obj])
                            if rx_table_obj.rowcount > 1:
                                master_table_obj.add_column('Rx Stats', [rx_table_obj])
                        else:
                            tx_table_obj = PrettyTable(['Tx Stats', 'Counter'])
                            rx_table_obj = PrettyTable(['Rx Stats', 'Counter'])
                            tx_table_obj.align = 'l'
                            tx_table_obj.sortby = "Tx Stats"
                            rx_table_obj.align = 'l'
                            rx_table_obj.sortby = "Rx Stats"
                            for key in result:
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        if re.search(r'.*tx.*', key, re.IGNORECASE):
                                            tx_table_obj.add_row([key, result[key]])
                                        else:
                                            rx_table_obj.add_row([key, result[key]])
                                else:
                                    if re.search(r'.*tx.*', key, re.IGNORECASE):
                                        tx_table_obj.add_row([key, result[key]])
                                    else:
                                        rx_table_obj.add_row([key, result[key]])
                            prev_result = result
                            if tx_table_obj.rowcount > 1:
                                master_table_obj.add_column('Tx Stats', [tx_table_obj])
                            if rx_table_obj.rowcount > 1:
                                master_table_obj.add_column('Rx Stats', [rx_table_obj])
                    print master_table_obj
                    print "\n########################  %s ########################\n" % str(self._get_timestamp())
                    time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_pervppkts_stats(self, vp_number=None, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/pervppkts"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False
                    if result:
                        if vp_number:
                            vp_key = self._get_vp_number_key(output_dict=result, vp_number=vp_number)
                            result = result[vp_key]
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(result):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[_key], diff_result[_key]])
                                    else:
                                        table_obj.add_row([_key, result[_key], diff_result[_key]])
                                master_table_obj.add_row([table_obj])
                            else:
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(result):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[_key]])
                                    else:
                                        table_obj.add_row([_key, result[_key]])
                                master_table_obj.add_row([table_obj])

                        else:
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                            else:
                                for key in sorted(result):
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    table_obj.align = 'l'
                                    for _key in sorted(result[key]):
                                        if grep_regex:
                                            if re.search(grep_regex, key, re.IGNORECASE):
                                                table_obj.add_row([_key, result[key][_key]])
                                        else:
                                            table_obj.add_row([_key, result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()












