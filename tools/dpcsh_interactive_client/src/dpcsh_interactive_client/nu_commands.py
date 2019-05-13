from prettytable import PrettyTable, FRAME
from datetime import datetime
from collections import OrderedDict
import re
import time
import os
from uuid import uuid4
import json

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

    def _sort_key_by_int(self, result):
        sorted_keys = []
        for key in result:
            if key == 'LINK STATUS':
                continue
            sorted_keys.append(int(key.split('-')[1]))
        return sorted(sorted_keys)

    def port_link_status(self):
        try:
            arg_list = ["linkstatus"]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
            if result:
                table_obj = PrettyTable(['Port', 'Status'])
                table_obj.align = 'l'
                for key in sorted(result):
                    table_obj.add_row([key, result[key]])
                print table_obj
            else:
                print "Unable to get linkstatus: %s" % result
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
                arg_dict = {"class": class_num}
                arg_list = ["pfcqget", cmd_arg_dict, arg_dict]
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
                arg_dict = {"class": class_num}
                arg_list = ["pfctget", cmd_arg_dict, arg_dict]
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

    def port_speed(self, port_num, shape, brkmode=None):
        try:
            cmd_arg_dict = {"portnum": port_num, "shape": shape}
            if brkmode is not None:
                mtu_dict = {"brkmode": brkmode}
                arg_list = ["breakoutset", cmd_arg_dict, mtu_dict]
            else:
                arg_list = ["breakoutget", cmd_arg_dict]
            result = self.dpc_client.execute(verb="port", arg_list=arg_list)
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
                           update_config=True, mode='nu'):
        try:
            get_cmd_arg_list = ['get', 'egress_buffer_pool']
            if not mode == 'nu':
                get_cmd_arg_list.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_arg_list.insert(1, mode)
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

    def egress_port_buffer(self, port_num, min_thr=None, shared_thr=None, update_config=True, mode='nu'):
        try:
            get_cmd_arg_list = ['get', 'egress_port_buffer', {"port": port_num}]
            if not mode == 'nu':
                get_cmd_arg_list.insert(1, mode)
            buffer_config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_arg_list)
            buffer_config['port'] = port_num
            if update_config:
                if min_thr is not None:
                    buffer_config['min_thr'] = min_thr
                if shared_thr is not None:
                    buffer_config['shared_thr'] = shared_thr

                set_cmd_arg_list = ['set', 'egress_port_buffer', buffer_config]
                if not mode == 'nu':
                    set_cmd_arg_list.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_arg_list)
                print result
            else:
                self._display_qos_config(config_dict=buffer_config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def egress_queue_buffer(self, port_num, queue, min_thr=None, static_shared_thr_green=None, dynamic_enable=None,
                            shared_thr_alpha=None, shared_thr_offset_yellow=None, shared_thr_offset_red=None,
                            update_config=True, mode='nu'):
        try:
            get_cmd_arg_list = ['get', 'egress_queue_buffer', {"port": port_num, "queue": queue}]
            if not mode == 'nu':
                get_cmd_arg_list.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_arg_list.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_arg_list)
                print result
            else:
                self._display_qos_config(config_dict=buffer_config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def egress_queue_to_priority_map(self, port_num, map_list=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'queue_to_priority_map', {"port": port_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            if update:
                if map_list:
                    config["map"] = [int(x) for x in map_list] 
                set_cmd_args = ['set', 'queue_to_priority_map', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_glb_sh_threshold(self, en=None, green=None, red=None, yellow=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'ecn_glb_sh_thresh']
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_profile(self, prof_num, min_thr=None, max_thr=None, ecn_prob_index=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'ecn_profile', {'prof_num': prof_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ecn_prob(self, prob_idx, prob=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'ecn_prob', {'prob_idx': prob_idx}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prob_idx'] = prob_idx
            if update:
                if prob is not None:
                    config['prob'] = prob
                set_cmd_args = ['set', 'ecn_prob', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_profile(self, prof_num, min_thr=None, max_thr=None, wred_prob_index=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'wred_profile', {'prof_num': prof_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_prob(self, prob_idx, prob=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'wred_prob', {'prob_idx': prob_idx}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['prob_idx'] = prob_idx
            if update:
                if prob is not None:
                    config['prob'] = prob
                set_cmd_args = ['set', 'wred_prob', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_queue_config(self, port_num, queue_num, wred_en=None, wred_weight=None, wred_prof_num=None, ecn_en=None,
                          ecn_prof_num=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'wred_queue_config', {'port': port_num, "queue": queue_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def wred_avg_q_config(self, q_avg_en=None, cap_avg_sz=None, avg_period=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'wred_avg_q_config']
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if update:
                if q_avg_en is not None:
                    config["q_avg_en"] = q_avg_en
                    # del config['avg_en']
                if cap_avg_sz is not None:
                    config['cap_avg_sz'] = cap_avg_sz
                if avg_period is not None:
                    config['avg_period'] = avg_period
                set_cmd_args = ['set', 'wred_avg_q_config', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def get_scheduler_config(self, port_num, queue_num, scheduler_type=None, mode='nu'):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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

    def scheduler_config_dwrr(self, port_num, queue_num, weight, mode='nu'):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            result = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            dwrr_config = result['dwrr']
            dwrr_config['weight'] = weight
            dwrr_config['port'] = port_num
            dwrr_config['queue'] = queue_num
            set_cmd_args = ['set', 'scheduler_config', 'dwrr', dwrr_config]
            if not mode == 'nu':
                set_cmd_args.insert(1, mode)
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def scheduler_config_shaper(self, port_num, queue_num, shaper_enable=None, shaper_type=0, shaper_rate=None, shaper_threshold=None, mode='nu'):
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
            if not mode == 'nu':
                set_cmd_args.insert(1, mode)
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def scheduler_config_strict_priority(self, port_num, queue_num, strict_priority_enable=None, extra_bandwidth=None, mode='nu'):
        try:
            get_cmd_args = ['get', 'scheduler_config', {'port': port_num, 'queue': queue_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            result = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            strict_priority_config = result['strict_priority']
            strict_priority_config['port'] = port_num
            strict_priority_config['queue'] = queue_num
            if strict_priority_enable is not None:
                strict_priority_config['strict_priority_enable'] = strict_priority_enable
            if extra_bandwidth is not None:
                strict_priority_config['extra_bandwidth'] = extra_bandwidth
            set_cmd_args = ['set', 'scheduler_config', 'strict_priority', strict_priority_config]
            if not mode == 'nu':
                set_cmd_args.insert(1, mode)
            result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ingress_priority_group(self, port_num, pg_num, min_thr=None, shared_thr=None, headroom_thr=None,
                               xoff_enable=None, shared_xon_thr=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'ingress_priority_group', {"port": port_num, "pg": pg_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
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
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def ingress_priority_to_pg_map(self, port_num, map_list=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'priority_to_pg_map', {"port": port_num}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            if update:
                if map_list is not None:
                    config["map"] = [int(x) for x in map_list]
                set_cmd_args = ['set', 'priority_to_pg_map', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def pfc(self, enable=None, update=True, disable=None, mode='nu'):
        try:
            if update:
                config = {}
                if enable is not None:
                    config["enable"] = 1
                elif disable is not None:
                    config['enable'] = 0
                set_cmd_args = ['set', 'pfc', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                get_cmd_args = ['get', 'pfc']
                if not mode == 'nu':
                    get_cmd_args.insert(1, mode)
                config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def arb_cfg(self, en=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'arb_cfg']
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            if update:
                if en is not None:
                    config["en"] = en
                set_cmd_args = ['set', 'arb_cfg', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
                result = self.dpc_client.execute(verb='qos', arg_list=set_cmd_args)
                print result
            else:
                self._display_qos_config(config_dict=config)
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def xoff_status(self, port_num, pg, status=None, update=True, mode='nu'):
        try:
            get_cmd_args = ['get', 'xoff_status', {'port': port_num, 'pg': pg}]
            if not mode == 'nu':
                get_cmd_args.insert(1, mode)
            config = self.dpc_client.execute(verb='qos', arg_list=get_cmd_args)
            config['port'] = port_num
            config['pg'] = pg
            if update:
                if status is not None:
                    config["status"] = status
                set_cmd_args = ['set', 'xoff_status', config]
                if not mode == 'nu':
                    set_cmd_args.insert(1, mode)
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

    def clear_nu_nwqm_stats(self):
        try:
            cmd = ["clear", "nwqm"]
            result = self.dpc_client.execute(verb="nu", arg_list=cmd)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)

    def clear_nu_vppkts_stats(self):
        try:
            cmd = ["clear", "vppkts"]
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
            elif type(result[key]) == str:
                diff_result[key] = result[key]
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

    def _sort_bam_keys(self, result, au_sort=True):
        sorted_dict = OrderedDict()
        if not au_sort:
            new_usage_dict = {}
            new_color_dict = {}
            usage_dict = {}
            color_dict = {}
            for key in result:
                if re.search(r'usage', key):
                    new_usage_dict[key] = result[key]
                    pool_word = key.split(" ")[1]
                    usage_dict[key] = int(filter(str.isdigit, str(pool_word)))
                else:
                    new_color_dict[key] = result[key]
                    # pool_word = key.split(" ")[0]
                    # color_dict[key] = int(filter(str.isdigit, str(pool_word)))
            sorted_usage_keys = sorted(new_usage_dict, key=usage_dict.__getitem__)
            # sorted_color_keys = sorted(new_color_dict, key=color_dict.__getitem__)
            for key in sorted_usage_keys:
                sorted_dict[key] = result[key]
            for index in range(0, len(sorted(new_color_dict['pool_colors']))):
                key = 'pool%d color' % index
                sorted_dict[key] = new_color_dict['pool_colors'][index]
        else:
            pool_map = {}
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

    def _get_colmun_name_fpg(self, result, port_num):
        column_name = None
        for key in result:
            if re.search(r'.*_MAC_.*', key, re.IGNORECASE):
                column_name = "Port %d FPG stats" % port_num
                break
            elif re.search(r'.*misc.*', key, re.IGNORECASE):
                column_name = "Port %d MISC stats" % port_num
                break
        return column_name

    def peek_fpg_stats(self, port_num, grep_regex=None, mode='nu', get_result_only=False):
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
                index = 0
                for result in result_list:
                    if prev_result:
                        diff_result = self._get_difference(result=result, prev_result=prev_result[index])
                        column_name = self._get_colmun_name_fpg(result=result, port_num=port_num)
                        tx_table_obj = PrettyTable([column_name, 'Counter', 'Counter diff'])
                        rx_table_obj = PrettyTable([column_name, 'Counter', 'Counter diff'])
                        tx_table_obj.align = 'l'
                        tx_table_obj.sortby = column_name
                        rx_table_obj.align = 'l'
                        rx_table_obj.sortby = column_name
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
                        if tx_table_obj.rowcount > 1:
                            master_table_obj.add_row([tx_table_obj])
                        if rx_table_obj.rowcount > 1:
                            master_table_obj.add_row([rx_table_obj])
                        index += 1
                    else:
                        column_name = self._get_colmun_name_fpg(result=result, port_num=port_num)
                        tx_table_obj = PrettyTable([column_name, 'Counter'])
                        rx_table_obj = PrettyTable([column_name, 'Counter'])
                        tx_table_obj.align = 'l'
                        tx_table_obj.sortby = column_name
                        rx_table_obj.align = 'l'
                        rx_table_obj.sortby = column_name
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
                        if tx_table_obj.rowcount > 1:
                            master_table_obj.add_row([tx_table_obj])
                        if rx_table_obj.rowcount > 1:
                            master_table_obj.add_row([rx_table_obj])

                prev_result = result_list
                if get_result_only:
                    return cmd, master_table_obj
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
                
    def peek_psw_stats(self, mode='nu', port_num=None, queue_list=None, grep_regex=None, get_result_only=False):
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
                        for key in result:
                            count_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            drops_table_obj = PrettyTable(['Drops Type', 'Count', 'Drop Count Diff'])

                            m = re.search(r'q_\d+', key)
                            if not m:
                                diff = result[key] - prev_result[key]
                                master_table_obj.add_row([key, result[key], diff])
                                continue
                            queue_result = result[key]
                            count_result = queue_result['count']
                            drop_result = queue_result['drops']

                            diff_count_result = self._get_difference(result=count_result,
                                                                     prev_result=prev_result[key]['count'])
                            diff_drop_result = self._get_difference(result=drop_result,
                                                                    prev_result=prev_result[key]['drops'])

                            for _key in count_result:
                                inner_table_obj = None
                                if grep_regex:
                                    if type(count_result[_key]) == dict:
                                        inner_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Bytes Diff', 'Packets',
                                                                       'Packets Diff'])
                                        inner_table_obj.add_row([_key, count_result[_key]['bytes'],
                                                                 diff_count_result[_key]['bytes'],
                                                                 count_result[_key]['pkts'],
                                                                 diff_count_result[_key]['pkts']])
                                    else:
                                        count_table_obj.add_row([_key, count_result[_key], diff_count_result[_key]])
                                else:
                                    if type(count_result[_key]) == dict:
                                        inner_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Bytes Diff', 'Packets',
                                                                       'Packets Diff'])
                                        inner_table_obj.add_row([_key, count_result[_key]['bytes'],
                                                                 diff_count_result[_key]['bytes'],
                                                                 count_result[_key]['pkts'],
                                                                 diff_count_result[_key]['pkts']])
                                    else:
                                        count_table_obj.add_row([_key, count_result[_key], diff_count_result[_key]])
                                    if inner_table_obj:
                                        count_table_obj.add_row([_key, inner_table_obj, None])

                            for _key in drop_result:
                                if grep_regex:
                                    if re.search(grep_regex, _key, re.IGNORECASE):
                                        drops_table_obj.add_row([_key, drop_result[_key], diff_drop_result[_key]])
                                else:
                                    drops_table_obj.add_row([_key, drop_result[_key], diff_drop_result[_key]])

                            if queue_list:
                                if key in queue_list:
                                    master_table_obj.add_row([key, count_table_obj, drops_table_obj])

                            else:
                                master_table_obj.add_row([key, count_table_obj, drops_table_obj])
                    else:
                        for key in result:
                            count_table_obj = PrettyTable(['Field Name', 'Counter'])
                            drops_table_obj = PrettyTable(['Drops Type', 'Counter'])

                            m = re.search(r'q_\d+', key)
                            if not m:
                                master_table_obj.add_row([key, result[key], None])
                                continue
                            queue_result = result[key]
                            count_result = queue_result['count']
                            drop_result = queue_result['drops']

                            for _key in count_result:
                                inner_table_obj = None
                                if grep_regex:
                                    if re.search(grep_regex, _key, re.IGNORECASE):
                                        if type(count_result[_key]) == dict:
                                            inner_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Packets'])
                                            inner_table_obj.add_row([_key, count_result[_key]['bytes'],
                                                                     count_result[_key]['pkts']])
                                        else:
                                            count_table_obj.add_row([_key, count_result[_key]])
                                else:
                                    if type(count_result[_key]) == dict:
                                        inner_table_obj = PrettyTable(['Enq/Deq', 'Bytes', 'Packets'])
                                        inner_table_obj.add_row([_key, count_result[_key]['bytes'],
                                                                count_result[_key]['pkts']])
                                    else:
                                        count_table_obj.add_row([_key, count_result[_key]])
                                if inner_table_obj:
                                    count_table_obj.add_row([_key, inner_table_obj])

                            for _key in drop_result:
                                if grep_regex:
                                    if re.search(grep_regex, _key, re.IGNORECASE):
                                        drops_table_obj.add_row([_key, drop_result[_key]])
                                else:
                                    drops_table_obj.add_row([_key, drop_result[_key]])
                            if queue_list:
                                if key in queue_list:
                                    master_table_obj.add_row([key, count_table_obj, drops_table_obj])

                            else:
                                master_table_obj.add_row([key, count_table_obj, drops_table_obj])
                    master_table_obj.border = True
                    master_table_obj.sortby = 'Field 1'
                    master_table_obj.header = False
                    master_table_obj.hrules = FRAME
                if get_result_only:
                    return cmd, master_table_obj
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
     
    def _display_stats(self, cmd, grep_regex, prev_result=None, verb="peek", tid=0, au_sort=True, get_result_only=False):
        try:
            while True:
                try:
                    if type(cmd) == list:
                        result = self.dpc_client.execute(verb=verb, arg_list=cmd, tid=tid)
                    else:
                        result = self.dpc_client.execute(verb=verb, arg_list=[cmd], tid=tid)
                    if 'bam' in cmd:
                        result = self._sort_bam_keys(result=result, au_sort=au_sort)
                    if not isinstance(result, dict):
                        print "'%s' seen in output " % result
                        break
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
                        if get_result_only:
                            return cmd, table_obj
                        prev_result = result
                        print table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
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

    def peek_vp_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/vppkts"
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_fcp_tunnel_stats(self, tunnel_id, grep_regex=None, get_result_only=False):
        cmd = "stats/fcp/tunnel[%d]" % tunnel_id
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_wro_stats(self, mode='nu', tunnel_id=None, grep_regex=None, get_result_only=False):
        if tunnel_id:
            cmd = "stats/wro/%s/tunnel[%d]" % (mode, tunnel_id)
        else:
            cmd = "stats/wro/%s/global" % mode
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_bam_stats(self, grep_regex=None):
        cmd = "stats/bam"
        self._display_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_fwd_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/fwd/flex"
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_erp_stats(self, mode='nu', grep_regex=None, get_result_only=False):
        if mode == "hnu":
            cmd = "stats/erp/hnu/global"
            if get_result_only:
                return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
            else:
                self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        elif mode == 'nu':
            cmd = "stats/erp/nu/global"
            if get_result_only:
                return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
            else:
                self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
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
                            if get_result_only:
                                return cmd, table_obj
                            print table_obj
                            print "\n########################  %s ########################\n" % \
                                  str(self._get_timestamp())
                            time.sleep(TIME_INTERVAL)
                        else:
                            if get_result_only:
                                return cmd, "Empty Result"
                            print "Empty Result"
                    except KeyboardInterrupt:
                        self.dpc_client.disconnect()
                        break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()

    def peek_etp_stats(self, mode='nu', grep_regex=None, get_result_only=False):
        cmd = "stats/etp/" + mode
        if get_result_only:
            return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def _get_parser_stats(self, grep_regex=None, hnu=False, get_result_only=False):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/prsr/nu"
                    if hnu:
                        cmd = "stats/prsr/hnu"
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
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                    if get_result_only:
                        return cmd, master_table_obj
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

    def peek_parser_stats(self, mode='nu', grep_regex=None, get_result_only=False):
        hnu=False
        if mode == 'hnu':
            hnu=True
        if get_result_only:
            return self._get_parser_stats(hnu=hnu, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._get_parser_stats(hnu=hnu, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_wred_ecn_stats(self, port_num, queue_num, grep_regex=None):
        cmd = ["get", "wred_ecn_stats", {"port": port_num, "queue": queue_num}]
        self._display_stats(cmd=cmd, verb='qos', grep_regex=grep_regex)

    def peek_sfg_stats(self, mode='nu', grep_regex=None, get_result_only=False):
        if mode == "nu":
            cmd = "stats/sfg/nu"
            if get_result_only:
                return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
            else:
                self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        elif mode == "hnu":
            cmd = "stats/sfg/hnu"
            if get_result_only:
                return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
            else:
                self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
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
                            if get_result_only:
                                return cmd, master_table_obj
                            prev_result = result
                            print master_table_obj
                            print "\n########################  %s ########################\n" % \
                                  str(self._get_timestamp())
                            time.sleep(TIME_INTERVAL)
                        else:
                            if get_result_only:
                                return cmd, "Empty Result"
                            print "Empty Result"
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

    def peek_stats_per_vp(self, vp_number=None, grep_regex=None, get_result_only=False):
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
                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_mpg_stats(self, grep_regex=None, get_result_only=False):
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
                    else:
                        if get_result_only:
                            print cmd, "Empty Result"
                        print "Empty Result"
                    if get_result_only:
                        return cmd, master_table_obj
                    print master_table_obj
                    print "\n########################  %s ########################\n" % str(self._get_timestamp())
                    time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_pervppkts_stats(self, vp_number=None, cluster_id=0, grep_regex=None, get_result_only=False):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/pervppkts/[%d]" % cluster_id
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
                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _get_nested_dict_stats(self, cmd, stop_regex="does not exist", grep_regex=None, get_result_only=False):
        try:
            prev_result = None
            while True:
                try:
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False
                    if result:
                        if stop_regex in str(result):
                            raise Exception("'%s' seen in output" % result)
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(result[key]):
                                    if isinstance(result[key][_key], dict):
                                        table_obj = PrettyTable()
                                        table_obj.align = 'l'
                                        inner_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                        inner_table_obj.align = 'l'
                                        for _key1 in sorted(result[key][_key]):
                                            if grep_regex:
                                                if re.search(grep_regex, _key1, re.IGNORECASE):
                                                    inner_table_obj.add_row([_key1, result[key][_key][_key1], diff_result[key][_key][_key1]])
                                            else:
                                                inner_table_obj.add_row([_key1, result[key][_key][_key1], diff_result[key][_key][_key1]])
                                        table_obj.add_row([_key, inner_table_obj])
                                    elif grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(result[key]):
                                    if isinstance(result[key][_key], dict):
                                        table_obj = PrettyTable()
                                        table_obj.align = 'l'
                                        inner_table_obj = PrettyTable(['Field Name', 'Counter'])
                                        inner_table_obj.align = 'l'
                                        for _key1 in sorted(result[key][_key]):
                                            if grep_regex:
                                                if re.search(grep_regex, _key1, re.IGNORECASE):
                                                    inner_table_obj.add_row([_key1, result[key][_key][_key1]])
                                            else:
                                                inner_table_obj.add_row([_key1, result[key][_key][_key1]])
                                        table_obj.add_row([_key, inner_table_obj])
                                    elif grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, result[key][_key]])
                                master_table_obj.add_row([key, table_obj])
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                    if get_result_only:
                        return cmd, master_table_obj
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

    def _display_list_of_dict_stats(self, cmd, grep_regex=None):
        # Modified as per dam stats
        try:
            prev_result = None
            while True:
                try:
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            table_obj.align = 'l'
                            index = 0
                            for out in result:
                                for _key in sorted(out):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            diff_val = int(prev_result[index][_key]) - int(out[_key])
                                            table_obj.add_row([_key, out[_key], diff_val])
                                    else:
                                        diff_val = int(prev_result[index][_key]) - int(out[_key])
                                        table_obj.add_row([_key, out[_key], diff_val])
                                index += 1
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counter'])
                            table_obj.align = 'l'
                            for out in result:
                                for _key in sorted(out):
                                    if grep_regex:
                                        if re.search(grep_regex, _key, re.IGNORECASE):
                                            table_obj.add_row([_key, out[_key]])
                                    else:
                                        table_obj.add_row([_key, out[_key]])
                    else:
                        print "Empty Result"

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

    def peek_nhp_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/nhp"
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_sse_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/sse"
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_pc_resource_stats(self, cluster_id, grep_regex=None):
        cmd = "stats/resource/pc/[%s]" % cluster_id
        self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_cc_resource_stats(self, grep_regex=None):
        cmd = "stats/resource/cc"
        self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def _display_resource_color_qdepth(self, cmd, cluster_id):
        prev_result = {}
        while True:
            try:
                result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                table_obj = None
                if result:
                    if prev_result:
                        table_obj = PrettyTable(['color', 'color diff', 'qdepth', 'qdepth Diff'])
                        for index in range(0, len(sorted(result))):
                            diff_result = self._get_difference(result=result[index], prev_result=prev_result[index])
                            table_obj.add_row([result[index]['color'], diff_result['color'], result[index]['qdepth'],
                                               diff_result['qdepth']])
                    else:
                        table_obj = PrettyTable(['color', 'qdepth'])
                        for record in sorted(result):
                            table_obj.add_row(record.values())
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

    def peek_dma_resource_stats(self, cluster_id):
        cmd = "stats/resource/dma/[%s]" % cluster_id
        self._display_resource_color_qdepth(cmd=cmd, cluster_id=cluster_id)

    def peek_le_resource_stats(self, cluster_id):
        cmd = "stats/resource/le/[%s]" % cluster_id
        self._display_resource_color_qdepth(cmd=cmd, cluster_id=cluster_id)

    def peek_zip_resource_stats(self, cluster_id):
        cmd = "stats/resource/zip/[%s]" % cluster_id
        self._display_resource_color_qdepth(cmd=cmd, cluster_id=cluster_id)

    def peek_rgx_resource_stats(self, cluster_id, grep_regex=None):
        cmd = "stats/resource/rgx/[%s]" % cluster_id
        self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_mode_resource_stats(self, mode='nu', resource_id=None, grep_regex=None, get_result_only=False):
        if resource_id:
            cmd = "stats/resource/hnu/[%s]" % resource_id
            if mode == 'nu':
                cmd = "stats/resource/nu/[%s]" % resource_id
        else:
            cmd = "stats/resource/hnux"
            if mode == 'nu':
                cmd = "stats/resource/nux"
        if get_result_only:
            return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_hu_resource_stats(self, hu_id, wqsi=None, wqse=None, resource_id=None, grep_regex=None):
        try:
            cmd = "stats/resource/hu%s" % hu_id
            if wqsi:
                cmd = cmd + "/wqsi"
            elif wqse:
                cmd = cmd + "/wqse"
            if resource_id:
                if not ('wqsi' in cmd):
                    raise Exception("Resource id given, Please provide wqsi or wqse")
                cmd = cmd + "[%s]" % resource_id
            if wqsi or wqse:
                self._display_stats(cmd=cmd, grep_regex=grep_regex)
            else:
                self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, stop_regex="does not exist")
        except Exception as ex:
            print "ERROR:  %s" % str(ex)

    def peek_dam_resource_stats(self, grep_regex=None):
        cmd = "stats/resource/dam"
        self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_bam_resource_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/resource/bam"
        verb = "peek"
        tid = 0
        au_sort = False
        prev_result = None
        try:
            bam_pool_decode_dict ={
		'pool0': 'BM_POOL_FUNOS',
		'pool1': 'BM_POOL_NU_ETP_CMDLIST',
		'pool2': 'BM_POOL_HU_REQ',
		'pool3': 'BM_POOL_SW_PREFETCH',
		'pool4': 'BM_POOL_NU_ERP_FCP',
		'pool19': 'BM_POOL_NU_ERP_CC',
		'pool20': 'BM_POOL_NU_ERP_SAMPLING',
		'pool34': 'BM_POOL_REGEX',
		'pool35': 'BM_POOL_REFBUF',
		'pool49': 'BM_POOL_NU_ERP_NONFCP',
		'pool50': 'BM_POOL_HNU_NONFCP',
		'pool62': 'BM_POOL_HNU_PREFETCH',
		'pool63': 'BM_POOL_NU_PREFETCH',}

            while True:
                try:
                    if type(cmd) == list:
                        result = self.dpc_client.execute(verb=verb, arg_list=cmd, tid=tid)
                    else:
                        result = self.dpc_client.execute(verb=verb, arg_list=[cmd], tid=tid)
                    result = self._sort_bam_keys(result=result, au_sort=au_sort)
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            table_obj = PrettyTable(['Field Name', 'Counters', 'Diff Counters'])
                            table_obj.align = 'l'
                            for key in result:
                                decode_value = ''
                                pool_value = key.split(' ')[0]
                                if 'usage' in key:
                                    pool_value = key.split(' ')[1]
                                if pool_value in bam_pool_decode_dict:
                                    decode_value = bam_pool_decode_dict[pool_value]
                                if grep_regex:
                                    if re.search(grep_regex, decode_value, re.IGNORECASE):
                                        table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], diff_result[key]])
                                else:
                                    table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counters'])
                            table_obj.align = 'l'
                            for key in result:
                                decode_value = ''
                                pool_value = key.split(' ')[0]
                                if 'usage' in key:
                                    pool_value = key.split(' ')[1]
                                if pool_value in bam_pool_decode_dict:
                                    decode_value = bam_pool_decode_dict[pool_value]
                                if grep_regex:
                                    if re.search(grep_regex, decode_value, re.IGNORECASE):
                                        table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key]])
                                else:
                                    table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], ])
                        if get_result_only:
                            return cmd, table_obj
                        prev_result = result
                        print table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                        time.sleep(TIME_INTERVAL)
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()
    '''
    def peek_nwqm_stats(self, grep_regex=None):
        try:
            prev_results = None
            while True:
                try:
                    cmd = "stats/nwqm"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    #result = results[""]
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
    '''

    def peek_nwqm_stats(self, mode=None, grep_regex=None, get_result_only=False):
        cmd = "stats/nwqm"
        if mode:
            cmd = "stats/nwqm/%s" % mode
        if get_result_only:
            return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_fae_stats(self, grep_regex=None, get_result_only=False):
        cmd = "stats/fae"
        if get_result_only:
            return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

    def peek_eqm_stats(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/eqm"
                    result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                    if result:
                        if prev_result:
                            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result[key], diff_result[key]])
                                else:
                                    table_obj.add_row([key, result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counter'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            for key in sorted(result):
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
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_funtop_stats(self):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "stats/funtop"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        result = result['funtop']
                        if prev_result:
                            diff_result = self._get_difference(result=result,
                                                               prev_result=prev_result)
                            for key in sorted(result):
                                if type(result[key]) == dict:
                                    if key == 'cluster_usage':
                                        table_obj = PrettyTable(['Field Name', 'Counter'])
                                    else:
                                        table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in sorted(result[key]):
                                        if type(result[key][_key]) == dict:
                                            inner_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                            inner_table_obj.align = 'l'
                                            inner_table_obj.sortby = 'Field Name'
                                            for inner_key in sorted(result[key][_key]):
                                                inner_table_obj.add_row([inner_key, result[key][_key][inner_key],
                                                                         diff_result[key][_key][inner_key]])
                                            table_obj.add_row([_key, inner_table_obj])
                                        else:
                                            table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, result[key]])
                        else:
                            for key in sorted(result):
                                if type(result[key]) == dict:
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in sorted(result[key]):
                                        if type(result[key][_key]) == dict:
                                            inner_table_obj = PrettyTable(['Field Name', 'Counter'])
                                            inner_table_obj.align = 'l'
                                            inner_table_obj.sortby = 'Field Name'
                                            for inner_key in sorted(result[key][_key]):
                                                inner_table_obj.add_row([inner_key, result[key][_key][inner_key]])
                                            table_obj.add_row([_key, inner_table_obj])
                                        else:
                                            table_obj.add_row([_key, result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, result[key]])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print 'Empty Result'
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_malloc_agent_stats(self, grep_regex=None):
        cmd = "stats/malloc_agent"
        self._print_malloc_agent_stats(cmd=cmd, grep_regex=grep_regex)

    def peek_malloc_agent_non_coh_stats(self, grep_regex=None):
        cmd = "stats/malloc_agent_non_coh"
        self._print_malloc_agent_stats(cmd=cmd, grep_regex=grep_regex)

    def _print_malloc_agent_stats(self, cmd, grep_regex=None):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            for key in sorted(result):
                                if type(result[key]) == dict:
                                    diff_result = self._get_difference(result=result[key],
                                                                       prev_result=prev_result[key])
                                    table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in sorted(result[key]):
                                        table_obj.add_row([_key, result[key][_key], diff_result[_key]])
                                elif type(result[key]) == list:
                                    table_obj = PrettyTable()
                                    table_obj.align = 'l'
                                    table_obj.border = False
                                    table_obj.header = False
                                    index = 0
                                    for record in result[key]:
                                        diff_result = self._get_difference(result=record,
                                                                           prev_result=prev_result[key][index])
                                        in_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                        in_table_obj.align = 'l'
                                        in_table_obj.sortby = 'Field Name'
                                        for in_key in record:
                                            in_table_obj.add_row([in_key, record[in_key], diff_result[in_key]])
                                        table_obj.add_row([in_table_obj])
                                        index += 1
                                else:
                                    diff_result = self._get_difference(result=result,
                                                                       prev_result=prev_result)
                                    table_obj = PrettyTable(['Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    table_obj.add_row([result[key], diff_result[key]])

                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                if type(result[key]) == dict:
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in sorted(result[key]):
                                        table_obj.add_row([_key, result[key][_key]])
                                elif type(result[key]) == list:
                                    table_obj = PrettyTable()
                                    table_obj.align = 'l'
                                    table_obj.border = False
                                    table_obj.header = False
                                    for record in result[key]:
                                        in_table_obj = PrettyTable(['Field Name', 'Counter'])
                                        in_table_obj.align = 'l'
                                        in_table_obj.sortby = 'Field Name'
                                        for in_key in record:
                                            in_table_obj.add_row([in_key, record[in_key]])
                                        table_obj.add_row([in_table_obj])
                                else:
                                    table_obj = PrettyTable(['Counter'])
                                    table_obj.align = 'l'
                                    table_obj.add_row([result[key]])

                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print 'Empty Result'
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_stats_wustacks(self):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/wustacks"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            for key in result:
                                table_obj.add_row([key, result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counter'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            for key in result:
                                table_obj.add_row([key, result[key]])
                        print table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_stats_hu(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "stats/hu"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in sorted(result):
                                table_obj = PrettyTable()
                                table_obj.align = 'l'
                                table_obj.border = False
                                table_obj.header = False
                                for _key in sorted(result[key]):
                                    inner_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    inner_table_obj.align = 'l'
                                    inner_table_obj.sortby = 'Field Name'
                                    for in_key in sorted(result[key][_key]):
                                        if grep_regex:
                                            if re.search(grep_regex, _key, re.IGNORECASE):
                                                inner_table_obj.add_row([in_key, result[key][_key][in_key],
                                                                         diff_result[key][_key][in_key]])
                                        else:
                                            inner_table_obj.add_row([in_key, result[key][_key][in_key],
                                                                     diff_result[key][_key][in_key]])
                                    table_obj.add_row([_key, inner_table_obj])
                                master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = PrettyTable()
                                table_obj.align = 'l'
                                table_obj.border = False
                                table_obj.header = False
                                for _key in sorted(result[key]):
                                    inner_table_obj = PrettyTable(['Field Name', 'Counter'])
                                    inner_table_obj.align = 'l'
                                    inner_table_obj.sortby = 'Field Name'
                                    for in_key in sorted(result[key][_key]):
                                        if grep_regex:
                                            if re.search(grep_regex, _key, re.IGNORECASE):
                                                inner_table_obj.add_row([in_key, result[key][_key][in_key]])
                                        else:
                                            inner_table_obj.add_row([in_key, result[key][_key][in_key]])
                                    table_obj.add_row([_key, inner_table_obj])
                                master_table_obj.add_row([key, table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_stats_wus(self):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "stats/wus"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result, prev_result=prev_result)
                            for key in result:
                                if type(result[key]) == dict:
                                    table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in result[key]:
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in result:
                                if type(result[key]) == dict:
                                    table_obj = PrettyTable(['Field Name', 'Counter'])
                                    table_obj.align = 'l'
                                    table_obj.sortby = 'Field Name'
                                    for _key in result[key]:
                                        table_obj.add_row([_key, result[key][_key]])
                                    master_table_obj.add_row([key, table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


class SampleCommands(object):

    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def get_sample(self):
        try:
            result = self.dpc_client.execute(verb='sample', arg_list=['show'])
            if result:
                master_table_obj = PrettyTable(['Field Name', 'Counter'])
                master_table_obj.align = 'l'
                for key, val in sorted(result.iteritems()):
                    if isinstance(val, dict):
                        table_obj = PrettyTable(['Field Name', 'Counter'])
                        table_obj.align = 'l'
                        for _key in sorted(val):
                            table_obj.add_row([_key, val[_key]])
                        master_table_obj.add_row([key, table_obj])
                    else:
                        master_table_obj.add_row([key, val])
                print master_table_obj
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def set_sample(self, id, dest, fpg=None, acl=None, flag_mask=None, hu=None, psw_drop=None, pps_en=None,
                   pps_interval=None, pps_burst=None, sampler_en=None, sampler_rate=None, sampler_run_sz=None,
                   first_cell_only=None, mode=0, pps_tick=None):
        try:
            cmd_arg_dict = {"id": id, "mode": mode, "dest": dest}
            if fpg is not None:
                cmd_arg_dict['fpg'] = fpg
            if acl is not None:
                cmd_arg_dict['acl'] = acl
            if flag_mask:
                cmd_arg_dict['flag_mask'] = flag_mask
            if hu is not None:
                cmd_arg_dict['hu'] = hu
            if psw_drop is not None:
                cmd_arg_dict['psw_drop'] = psw_drop
            if pps_en is not None:
                cmd_arg_dict['pps_en'] = pps_en
            if pps_interval is not None:
                cmd_arg_dict['pps_interval'] = pps_interval
            if pps_burst is not None:
                cmd_arg_dict['pps_burst'] = pps_burst
            if pps_tick is not None:
                cmd_arg_dict['pps_tick'] = pps_tick
            if sampler_en is not None:
                cmd_arg_dict['sampler_en'] = sampler_en
            if sampler_rate:
                cmd_arg_dict['sampler_rate'] = sampler_rate
            if sampler_run_sz is not None:
                cmd_arg_dict['sampler_run_sz'] = sampler_run_sz
            if first_cell_only is not None:
                cmd_arg_dict['first_cell_only'] = first_cell_only

            result = self.dpc_client.execute(verb='sample', arg_list=cmd_arg_dict)
            if result:
                print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


class ShowCommands(PeekCommands):
    def do_write_on_file(self, filepath, command_dict):
        result = False
        try:
            with open(filepath, 'a') as f:
                f.write('\n######### Show start time %s #########\n' % self._get_timestamp())
                for command in command_dict.iterkeys():
                    cmd, result = command_dict[command]
                    f.write("Executed command: %s" % cmd)
                    f.write("\nOutput is:\n")
                    if isinstance(result, PrettyTable):
                        f.write(result.get_string())
                    else:
                        f.write(result)
                    f.write("\n")
                    f.write('\n===============================================================\n')
                result = True
        except Exception as ex:
            print "Error: %s" % str(ex)
        return result

    def append_mode_specific_commands(self, command_dict, port_list=[], mode='nu'):
        try:
            if not port_list is None:
                for port_num in port_list:
                    command_dict['%s fpg %s stats' % (mode, port_num)] = self.peek_fpg_stats(port_num=int(port_num),
                                                                                             get_result_only=True,
                                                                                             mode=mode)
            command_dict['%s psw stats' % mode] = self.peek_psw_stats(get_result_only=True, mode=mode)
            command_dict['%s wro stats' % mode] = self.peek_wro_stats(get_result_only=True, mode=mode)
            command_dict['%s erp stats' % mode] = self.peek_erp_stats(get_result_only=True, mode=mode)
            command_dict['%s sfg stats' % mode] = self.peek_sfg_stats(get_result_only=True, mode=mode)
            command_dict['%s parser stats' % mode] = self.peek_parser_stats(get_result_only=True, mode=mode)
            command_dict['%s etp stats' % mode] = self.peek_etp_stats(get_result_only=True, mode=mode)
            command_dict['%s resource stats' % mode] = self.peek_mode_resource_stats(get_result_only=True, mode=mode)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return command_dict

    def delete_filepath(self, filepath):
        if os.path.exists(filepath):
            os.remove(filepath)

    def show_stats(self, filename, mode='nu', port_list=[], fcp_tunnel_id=None):
        filepath = None
        command_dict = OrderedDict()
        try:
            tmp_path = '/tmp/'
            if not filename:
                filename = str(uuid4()) + '.txt'
            filepath = tmp_path + filename
            command_dict['fae stats'] = self.peek_fae_stats(get_result_only=True)
            command_dict['vppkts stats'] = self.peek_vp_stats(get_result_only=True)
            command_dict['per_vp stats'] = self.peek_stats_per_vp(get_result_only=True)
            command_dict['pervppkts stats'] = self.peek_pervppkts_stats(get_result_only=True)
            command_dict['nwqm stats'] = self.peek_nwqm_stats(get_result_only=True)
            command_dict['nhp stats'] = self.peek_nhp_stats(get_result_only=True)
            command_dict['sse stats'] = self.peek_sse_stats(get_result_only=True)
            command_dict['resource bam stats'] = self.peek_bam_resource_stats(get_result_only=True)
            if fcp_tunnel_id:
                command_dict['fcp stats'] = self.peek_fcp_tunnel_stats(get_result_only=True, tunnel_id=fcp_tunnel_id)
            if mode == 'nu' or mode == 'hnu':
                command_dict = self.append_mode_specific_commands(command_dict=command_dict, port_list=port_list,
                                                                  mode=mode)
            elif mode == 'all':
                command_dict = self.append_mode_specific_commands(command_dict=command_dict, port_list=port_list,
                                                                  mode='nu')
                command_dict = self.append_mode_specific_commands(command_dict=command_dict, port_list=port_list,
                                                                  mode='hnu')
            write_result = self.do_write_on_file(filepath=filepath, command_dict=command_dict)
            if write_result:
                print "Filepath is %s" % filepath
            else:
                print "Error in execution. Deleting file"
                self.delete_filepath(filepath)
            self.dpc_client.disconnect()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            print "Error in execution. Deleting file"
            if filepath:
                self.delete_filepath(filepath)
            self.dpc_client.disconnect()


class MeterCommands(object):

    def __init__(self, dpc_client):
        self.dpc_client = dpc_client

    def set_meter(self, index, interval, crd, commit_rate, pps_mode, excess_rate, commit_burst,
                  excess_burst, direction, len_mode, rate_mode, color_aware, unit, rsvd, len8, common, bank,
                  op="FUN_NU_OP_SFG_METER_CFG_W", erp=False):
        inst = 0
        if erp:
            inst = 1
        try:
            cmd_arg_dict = {"op": op, "len8": len8, "common": common, "inst": inst, "bank": bank, "index": index,
                            "interval": interval, "crd": crd, "commit_rate": commit_rate,
                            "excess_rate": excess_rate,
                            "commit_burst": commit_burst, "excess_burst": excess_burst, "dir": direction,
                            "len_mode": len_mode, "rate_mode": rate_mode, "pps_mode": pps_mode,
                            "color_aware": color_aware, "unit": unit, "rsvd": rsvd}

            result = self.dpc_client.execute(verb='req', arg_list=cmd_arg_dict)
            print result
        except Exception as ex:
            print "ERROR: %s" % str(ex)


class FlowCommands(object):

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
            elif type(result[key]) == str:
                diff_result[key] = result[key]
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

    def _inner_table_obj(self, result, prev_result=None):
        if prev_result:
            diff_result = self._get_difference(prev_result=prev_result, result=result)
            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
            table_obj.align = 'l'
            table_obj.sortby = 'Field Name'
            for key in sorted(result):
                if key == 'cookie':
                    table_obj.add_row([key, result[key], diff_result[key]])
                elif type(result[key]) == list:
                    for record in sorted(result[key]):
                        if type(record) == dict:
                            inner_table = PrettyTable()
                            inner_table.align = 'l'
                            for _key, val in record.iteritems():
                                if type(val) == dict:
                                    if 'packets' in val or 'bytes' in val:
                                        _table_obj = PrettyTable(['Field Name', 'Counter'])
                                        _table_obj.sortby = 'Field Name'
                                    else:
                                        _table_obj = PrettyTable()
                                    _table_obj.align = 'l'
                                    for inner_key in val:
                                        _table_obj.add_row([inner_key, val[inner_key]])
                                    inner_table.add_row([_key, _table_obj])
                                else:
                                    inner_table.add_row([_key, val])
                            table_obj.add_row([key, inner_table, None])
        else:
            table_obj = PrettyTable(['Field Name', 'Counter'])
            table_obj.align = 'l'
            table_obj.sortby = 'Field Name'
            for key in sorted(result):
                if key == 'cookie':
                    table_obj.add_row([key, result[key]])
                elif type(result[key]) == list:
                    for record in sorted(result[key]):
                        if type(record) == dict:
                            inner_table = PrettyTable()
                            inner_table.align = 'l'
                            for _key, val in record.iteritems():
                                if type(val) == dict:
                                    if 'packets' in val or 'bytes' in val:
                                        _table_obj = PrettyTable(['Field Name', 'Counter'])
                                        _table_obj.sortby = 'Field Name'
                                    else:
                                        _table_obj = PrettyTable()
                                    _table_obj.align = 'l'
                                    for inner_key in val:
                                        _table_obj.add_row([inner_key, val[inner_key]])
                                    inner_table.add_row([_key, _table_obj])
                                else:
                                    inner_table.add_row([_key, val])
                            table_obj.add_row([key, inner_table])

        return table_obj

    def get_flow_list(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "list"
                    result = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                    if result:
                        if prev_result:
                            for key in sorted(result):
                                table_obj = self._inner_table_obj(result=result[key],
                                                                  prev_result=prev_result[key])
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = self._inner_table_obj(result=result[key])
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def get_flow_blocked(self, grep_regex=None):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "blocked"
                    result = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                    if result:
                        if prev_result:
                            for key in sorted(result):
                                table_obj = self._inner_table_obj(result=result[key],
                                                                  prev_result=prev_result[key])
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                table_obj = self._inner_table_obj(result=result[key])
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        master_table_obj.add_row([key, table_obj])
                                else:
                                    master_table_obj.add_row([key, table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        time.sleep(TIME_INTERVAL)
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


