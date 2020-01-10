from prettytable import PrettyTable, FRAME
from datetime import datetime
from collections import OrderedDict
import re
import time
import os
from uuid import uuid4
import json

TIME_INTERVAL = 1
TOTAL_CLUSTERS = 8
TOTAL_CORES_PER_CLUSTER = 6
TOTAL_VPS_PER_CORE = 4
START_VP_NUMBER = 8

def do_sleep_for_interval():
    time.sleep(TIME_INTERVAL)
    return True

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
                    diff_result[key] = result[key]

        return diff_result

    def _get_nested_dict_difference(self, result, prev_result):
        diff_result = {}
        for key in result:
            if type(result[key]) == dict:
                if key in prev_result:
                    diff_result[key] = self._get_nested_dict_difference(result[key], prev_result[key])
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
                    diff_result[key] = result[key]

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
                do_sleep_for_interval()
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
                do_sleep_for_interval()
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
                do_sleep_for_interval()
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
                        print "Empty result seen"
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
                        do_sleep_for_interval()
                    else:
                        if get_result_only:
                            return cmd, "Empty Result"
                        print "Empty Result"
                        do_sleep_for_interval()
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
                    do_sleep_for_interval()
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

    def peek_fcp_tunnel_stats(self, tunnel_id, mode='nu', grep_regex=None, get_result_only=False):
        if tunnel_id:
            cmd = "stats/fcp/tunnel[%d]" % tunnel_id
            if get_result_only:
                return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
            else:
                self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            cmd = "stats/fcp/%s" % mode
            prev_result = None
            while True:
                try:
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            diff_result = self._get_difference(result=result['global'],
                                                               prev_result=prev_result['global'])
                            table_obj = PrettyTable(['Field Name', 'Counters', 'Diff Counters'])
                            table_obj.align = 'l'
                            for key in sorted(result['global']):
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result['global'][key], diff_result[key]])
                                else:
                                    table_obj.add_row([key, result['global'][key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counters'])
                            table_obj.align = 'l'
                            for key in sorted(result['global']):
                                if grep_regex:
                                    if re.search(grep_regex, key, re.IGNORECASE):
                                        table_obj.add_row([key, result['global'][key]])
                                else:
                                    table_obj.add_row([key, result['global'][key]])
                        if get_result_only:
                            return cmd, table_obj
                        prev_result = result
                        print table_obj
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        do_sleep_for_interval()
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
                except Exception as ex:
                    print "ERROR: %s" % str(ex)
                    self.dpc_client.disconnect()
                    break

    def peek_wro_stats(self, mode='nu', tunnel_id=None, grep_regex=None, get_result_only=False):
        if tunnel_id:
            cmd = "stats/wro/%s/tunnel[%d]" % (mode, tunnel_id)
        else:
            cmd = "stats/wro/%s/global" % mode
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)

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
                            do_sleep_for_interval()
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
        # cmd = "stats/etp/" + mode
        # if get_result_only:
        #     return self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)
        # else:
        #     self._get_nested_dict_stats(cmd=cmd, grep_regex=grep_regex)
        prev_result = None
        while True:
            try:
                cmd = "stats/etp/%s" % mode
                result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                if prev_result:
                    master_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                    master_table_obj.align = 'l'
                    diff_result = self._get_difference(result=result, prev_result=prev_result)
                    for key in sorted(result):
                        if grep_regex:
                            if re.search(grep_regex, key, re.IGNORECASE):
                                master_table_obj.add_row([key, result[key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            if type(result[key]) == dict:
                                inner_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
                                inner_table_obj.align = 'l'
                                inner_table_obj.sortby = 'Field Name'
                                for inner_key in result[key]:
                                    inner_table_obj.add_row([inner_key, result[key][inner_key],
                                                             diff_result[key][inner_key]])
                                master_table_obj.add_row([key, inner_table_obj, ""])
                            else:
                                master_table_obj.add_row([key, result[key], diff_result[key]])
                else:
                    master_table_obj = PrettyTable(['Field Name', 'Counters'])
                    master_table_obj.align = 'l'
                    for key in sorted(result):
                        if grep_regex:
                            if re.search(grep_regex, key, re.IGNORECASE):
                                master_table_obj.add_row([key, result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counters'])
                            table_obj.align = 'l'
                            table_obj.sortby = 'Field Name'
                            if type(result[key]) == dict:
                                inner_table_obj = PrettyTable(['Field Name', 'Counters'])
                                inner_table_obj.align = 'l'
                                inner_table_obj.sortby = 'Field Name'
                                for inner_key in result[key]:
                                    inner_table_obj.add_row([inner_key, result[key][inner_key]])
                                master_table_obj.add_row([key, inner_table_obj])
                            else:
                                master_table_obj.add_row([key, result[key]])
                if get_result_only:
                    return cmd, master_table_obj
                prev_result = result
                print master_table_obj
                print "\n########################  %s ########################\n" % str(self._get_timestamp())
                do_sleep_for_interval()
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
                break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()
                break


    def get_singleton_table_obj(self, result, prev_result=None, grep=None):
        if prev_result:
            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
            table_obj.align = 'l'
            diff_result = self._get_difference(result=result, prev_result=prev_result)
            for key in sorted(result):
                if grep:
                    if re.search(grep, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key], diff_result[key]])
                else:
                    table_obj.add_row([key, result[key], diff_result[key]])
        else:
            table_obj = PrettyTable(['Field Name', 'Counter'])
            table_obj.align = 'l'
            for key in sorted(result):
                if grep:
                    if re.search(grep, key, re.IGNORECASE):
                        table_obj.add_row([key, result[key]])
                else:
                    table_obj.add_row([key, result[key]])
        return table_obj

    def peek_cdu_stats(self, grep=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/cdu"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                            table_obj.align = 'l'
                            diff_result = self._get_difference(result=result['cdu_cnts'], prev_result=prev_result)
                            for key in sorted(result['cdu_cnts']):
                                if grep:
                                    if re.search(grep, key, re.IGNORECASE):
                                        table_obj.add_row([key, result['cdu_cnts'][key], diff_result[key]])
                                else:
                                    table_obj.add_row([key, result['cdu_cnts'][key], diff_result[key]])
                        else:
                            table_obj = PrettyTable(['Field Name', 'Counter'])
                            table_obj.align = 'l'
                            for key in sorted(result['cdu_cnts']):
                                if grep:
                                    if re.search(grep, key, re.IGNORECASE):
                                        table_obj.add_row([key, result['cdu_cnts'][key]])
                                else:
                                    table_obj.add_row([key, result['cdu_cnts'][key]])
                        prev_result = result['cdu_cnts']
                        print table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_ddr_stats(self, grep=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/ddr"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = "l"
                    if result:
                        result = result['ddr_cnts']
                        for key in sorted(result):
                            prev_result_dict = prev_result
                            if prev_result:
                                prev_result_dict = prev_result[key]
                            result_dict = result[key]
                            table_obj = self.get_singleton_table_obj(result=result_dict, prev_result=prev_result_dict,
                                                                     grep=grep)
                            master_table_obj.add_row([key, table_obj])

                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_ca_stats(self, grep=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/ca"
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    if result:
                        if prev_result:
                            master_table_obj = PrettyTable()
                            master_table_obj.align = 'l'
                            master_table_obj.header = False
                            diff_result = self._get_difference(result=result['ca_cnts'], prev_result=prev_result)
                            for key in sorted(result['ca_cnts']):
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(result['ca_cnts'][key]):
                                    if grep:
                                        if re.search(grep, key, re.IGNORECASE):
                                            table_obj.add_row([_key, result['ca_cnts'][key][_key],
                                                               diff_result[key][_key]])
                                    else:
                                        table_obj.add_row([_key, result['ca_cnts'][key][_key],
                                                           diff_result[key][_key]])
                                if table_obj:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            master_table_obj = PrettyTable()
                            master_table_obj.align = 'l'
                            master_table_obj.header = False
                            for key in sorted(result['ca_cnts']):
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(result['ca_cnts'][key]):
                                    if grep:
                                        if re.search(grep, key, re.IGNORECASE):
                                            table_obj.add_row([_key, result['ca_cnts'][key][_key]])
                                    else:
                                        table_obj.add_row([_key, result['ca_cnts'][key][_key]])
                                if table_obj:
                                    master_table_obj.add_row([key, table_obj])
                        prev_result = result['ca_cnts']
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


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
                    do_sleep_for_interval()
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
                            do_sleep_for_interval()
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

    def _get_vp_numbers_from_core_id(self, core_id):
        result = []
        try:
            start_vp_num = START_VP_NUMBER
            if core_id != 0:
                start_vp_num = START_VP_NUMBER + TOTAL_VPS_PER_CORE * core_id
            end_vp_num = start_vp_num + TOTAL_VPS_PER_CORE
            result = range(start_vp_num, end_vp_num, 1)
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return result

    def _get_cluster_core_parsed_dict(self, output_dict, cluster_id, core_id=None, pc_resource=False):
        result = {}
        try:
            if pc_resource and (core_id is not None):
                core_id = '0' + str(core_id)
                dict_keys = output_dict.keys()
                for key in dict_keys:
                    if str(core_id) in key.split(":")[1]:
                        result[key] = output_dict[key]
            else:
                dict_keys = output_dict.keys()
                for key in dict_keys:
                    if str(cluster_id) in key.split(":")[0]:
                        if core_id is not None:
                            vp_num_list = self._get_vp_numbers_from_core_id(core_id=core_id)
                            if int(key.split(":")[1]) in vp_num_list:
                                result[key] = output_dict[key]
                        else:
                            result[key] = output_dict[key]
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return result

    def get_required_per_vp_result(self, output_result):
        result = {}
        for key, val in output_result.iteritems():
            if key.split(":")[2][0] == '0':
                result[key] = {}
                result[key]['low_q_depth'] = val['vp_wu_qdepth']
                new_key = key.replace(":1[VP]", ":0[VP]")
                result[key]['high_q_depth'] = output_result[new_key]['vp_wu_qdepth']
                for _key, _val in val.iteritems():
                    result[key][_key] = _val
                del result[key]['vp_wu_qdepth']
        return result

    def get_filtered_dict(self, output_dict, cluster_id=None, core_id=None, rx=True, tx=True, q=True):
        rx_key_name = 'wus_received'
        tx_key_name = 'wus_sent'
        low_q_key_name = 'low_q_depth'
        high_q_key_name = 'high_q_depth'
        current_result = {}
        dict_keys = output_dict.keys()
        for key in dict_keys:
            if (str(cluster_id) is not None) and (str(cluster_id) in key.split(":")[0]):
                if core_id is not None:
                    vp_num_list = self._get_vp_numbers_from_core_id(core_id=core_id)
                    if int(key.split(":")[1]) in vp_num_list:
                        current_result[key] = output_dict[key]
                else:
                    current_result[key] = output_dict[key]
            elif cluster_id is None:
                cc_cluster_id = '8'
                if cc_cluster_id not in key.split(":")[0]:
                    current_result[key] = output_dict[key]
        parsed_dict = {}
        for key, val in current_result.iteritems():
            parsed_dict[key] = {}
            for _key in val.keys():
                if _key == rx_key_name and rx:
                    parsed_dict[key][rx_key_name] = current_result[key][_key]
                if _key == tx_key_name and tx:
                    parsed_dict[key][tx_key_name] = current_result[key][_key]
                if _key == low_q_key_name and q:
                    parsed_dict[key][low_q_key_name] = current_result[key][_key]
                if _key == high_q_key_name and q:
                    parsed_dict[key][high_q_key_name] = current_result[key][_key]
        return parsed_dict

    def peek_stats_per_vp(self, cluster_id=None, core_id=None, grep_regex=None,
                          rx=False, tx=False, q=False, get_result_only=False):
        try:
            prev_result = None
            if rx == False and tx == False and q == False:
                rx = True
                tx = True
                q = True
            while True:
                try:
                    cmd = "stats/per_vp"
                    output_result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    result = self.get_required_per_vp_result(output_result)
                    #prev_result = prev_result_dict[key]
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False
                    if result:
                        '''
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
                        '''
                        # Print table for cluster id and core id given
                        if (cluster_id is not None) and (core_id is not None):
                            result = self._get_cluster_core_parsed_dict(output_dict=result, cluster_id=cluster_id,
                                                                        core_id=core_id)

                        # Print table for cluster id given
                        elif cluster_id is not None:
                            result = self._get_cluster_core_parsed_dict(output_dict=result, cluster_id=cluster_id)

                        # Print master table
                        result = self.get_filtered_dict(result, cluster_id=cluster_id, core_id=core_id, rx=rx, tx=tx,
                                                        q=q)
                        if prev_result:
                            prev_result = self.get_filtered_dict(prev_result, cluster_id=cluster_id, core_id=core_id, rx=rx,
                                                                 tx=tx, q=q)
                            self.print_diff_result_single_dict_table_obj(master_table_obj=master_table_obj,
                                                                         result=result, prev_result=prev_result,
                                                                         grep_regex=grep_regex)
                        else:
                            self.print_single_dict_table_obj(master_table_obj=master_table_obj, result=result,
                                                             grep_regex=grep_regex)

                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
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

    def peek_stats_per_vp_pp(self, cluster_id=None, core_id=None, rx=False, tx=False, q=False, grep_regex=None,
                          get_result_only=False):
        try:
            rx_key_name = 'wus_received'
            display_rx_key_name = 'rx'
            tx_key_name = 'wus_sent'
            display_tx_key_name = 'tx'
            lo_q_key_name = 'low_q_depth'
            display_lo_q_key_name = 'lo_q'
            hi_q_key_name = 'high_q_depth'
            display_hi_q_key_name = 'hi_q'
            prev_result = None
            if rx == False and tx == False and q == False:
                rx = True
                tx = True
                q = True
            while True:
                print "%s = %s" % (display_rx_key_name, rx_key_name)
                print "%s = %s" % (display_tx_key_name, tx_key_name)
                print "%s = %s" % (display_lo_q_key_name, lo_q_key_name)
                print "%s = %s" % (display_hi_q_key_name, hi_q_key_name)
                try:
                    cmd = "stats/per_vp"
                    output_result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    result = self.get_required_per_vp_result(output_result)
                    if result:
                        def get_sorted_dict(result):
                            sorted_dict = OrderedDict()
                            result_keys = sorted(result)
                            if len(result_keys) % (TOTAL_VPS_PER_CORE * TOTAL_CORES_PER_CLUSTER) == 0:
                                result_keys.insert(0, result_keys[-2])
                                result_keys.insert(1, result_keys[-1])
                                del result_keys[-1]
                                del result_keys[-1]
                            else:
                                insert_index = 0
                                del_index = 22
                                for x in range(0, TOTAL_CLUSTERS):
                                    second_insert_index = insert_index + 1
                                    second_del_index = del_index + 1

                                    result_keys.insert(insert_index, result_keys[del_index])
                                    del result_keys[del_index + 1]
                                    result_keys.insert(second_insert_index, result_keys[second_del_index])
                                    del result_keys[second_del_index + 1]

                                    insert_index = insert_index + 24
                                    del_index = del_index + 24
                            for key in result_keys:
                                sorted_dict[key] = result[key]
                            return sorted_dict

                        def get_complete_dict(result, tabular_list, prev_result=None):
                            complete_dict = OrderedDict()
                            added_cluster_list = []
                            for item in tabular_list:
                                complete_dict[item] = []
                            current_result = result
                            if prev_result:
                                current_result = prev_result
                            for key, val in current_result.iteritems():
                                cluster_val = key.split(":")[0][2]
                                vp_val = key.split(":")[1]
                                if not cluster_val in added_cluster_list:
                                    if core_id is not None:
                                        complete_dict[tabular_list[0]].append("%s/%s" % (cluster_val, core_id))
                                        added_cluster_list.append(cluster_val)
                                    else:
                                        for x in range(0, 6):
                                            complete_dict[tabular_list[0]].append("%s/%s" % (cluster_val, x))
                                        added_cluster_list.append(cluster_val)
                                for _key, _val in val.iteritems():
                                    for item in tabular_list[1:]:
                                        if (int(vp_val) % TOTAL_VPS_PER_CORE == int(item.split(":")[0][0])) and (not 'd_' in item) and (_key == item.split(":")[1]):
                                            complete_dict[item].append(_val)
                                            break
                            if prev_result:
                                diff_result = self._get_difference(result=result, prev_result=prev_result)
                                diff_result = get_sorted_dict(diff_result)
                                for key, val in diff_result.iteritems():
                                    cluster_val = key.split(":")[0][2]
                                    vp_val = key.split(":")[1]
                                    if not cluster_val in added_cluster_list:
                                        added_cluster_list.append(cluster_val)
                                        complete_dict[tabular_list[0]].append(cluster_val)
                                    for _key, _val in val.iteritems():
                                        for item in tabular_list[1:]:
                                            if (int(vp_val) % TOTAL_VPS_PER_CORE == int(item.split(":")[0][0])) and (
                                            'd_' in item) and ('d_' + _key == item.split(":")[1]):
                                                complete_dict[item].append(_val)
                                                break
                            return complete_dict

                        def get_tabular_list(table_list, print_key_list, diff=False):
                            tabular_list = []
                            for _key in table_list:
                                for key in print_key_list:
                                    if not 'Cls/Core' in str(_key):
                                        tabular_list.append(str(_key) + ":" + key)
                                        if diff:
                                            tabular_list.append(str(_key) + ":d_" + key)
                                    else:
                                        if not any('Cls/Core' in s for s in tabular_list):
                                            tabular_list.append(_key)
                            return tabular_list

                        def eliminate_zero_val_rows(print_keys, print_values):
                            diff_indexes = []

                            # Find all diff columns
                            for key in print_keys:
                                if 'd_' in key:
                                    diff_indexes.append(print_keys.index(key))
                            if diff_indexes:
                                del_indexes = []
                                # Check all lists simultaneously if their diff value is 0 and note its index
                                for i in range(len(print_values[0])):
                                    zero_val = []
                                    for index in diff_indexes:
                                        if print_values[index][i] == 0:
                                            zero_val.append(True)
                                        else:
                                            zero_val.append(False)
                                            break
                                    if len(set(zero_val)) == 1 and zero_val[0]:
                                        del_indexes.append(i)
                                # Check if del indexes and delete those from all lists
                                del_indexes.reverse()
                                for val_list in print_values:
                                    for del_index in del_indexes:
                                        del val_list[del_index]
                            return print_values

                        def eliminate_zero_val_cols(print_keys, print_values):
                            diff_indexes = []
                            del_indexes = []
                            # Find all diff columns
                            for key in print_keys:
                                # TODO: Not removing column for q depth
                                if 'd_' in key and not '_q' in key:
                                    diff_indexes.append(print_keys.index(key))
                            if diff_indexes:
                                # Compare index list and index - 1 list and see if all elements are 0.
                                # If so then delete those 2 columns from print_keys and print_values
                                for index in diff_indexes:
                                    diff_check_len = len(set(print_values[index]))
                                    diff_check_val = print_values[index][0]
                                    nor_check_len = len(set(print_values[index - 1]))
                                    nor_check_val = print_values[index - 1][0]
                                    if diff_check_len == 1 and diff_check_val == 0 and nor_check_len == 1 and nor_check_val == 0:
                                        del_indexes.append(index - 1)
                                        del_indexes.append(index)
                            if del_indexes:
                                del_indexes.reverse()
                                for del_col in del_indexes:
                                    del print_keys[del_col]
                                    del print_values[del_col]
                            return print_values

                        def get_per_vp_dict_table_obj(result, prev_result=None):
                            all_keys = result.keys()
                            cluster_core_key = "Cls/Core"
                            row_list = [cluster_core_key, "0", "1", "2", "3"]

                            print_key_list = []
                            if rx:
                                print_key_list.append(rx_key_name)
                            if tx:
                                print_key_list.append(tx_key_name)
                            if q:
                                print_key_list.append(lo_q_key_name)
                                print_key_list.append(hi_q_key_name)

                            diff = False
                            if prev_result:
                                diff = True

                            tabular_list = get_tabular_list(row_list, print_key_list, diff=diff)

                            master_table_obj = PrettyTable()
                            print_dict = get_complete_dict(result=result, tabular_list=tabular_list,
                                                           prev_result=prev_result)

                            print_keys = print_dict.keys()
                            print_keys = [print_key.replace(tx_key_name, display_tx_key_name) for print_key in print_keys]
                            print_keys = [print_key.replace(rx_key_name, display_rx_key_name) for print_key in
                                          print_keys]
                            print_keys = [print_key.replace(lo_q_key_name, display_lo_q_key_name) for print_key in
                                          print_keys]
                            print_keys = [print_key.replace(hi_q_key_name, display_hi_q_key_name) for print_key in
                                          print_keys]
                            print_values = print_dict.values()

                            print_values = eliminate_zero_val_rows(print_keys, print_values)
                            all_empty_list = True
                            for print_val_list in print_values:
                                if print_val_list:
                                    all_empty_list = False
                                    break
                            if not all_empty_list:
                                print_values = eliminate_zero_val_cols(print_keys, print_values)
                            for col_name, col_values in zip(print_keys, print_values):
                                master_table_obj.add_column(col_name, col_values)
                            return master_table_obj

                        result = self.get_filtered_dict(output_dict=result, cluster_id=cluster_id, core_id=core_id,
                                                        rx=rx, tx=tx, q=q)

                        if core_id is None:
                            result = get_sorted_dict(result)
                        if prev_result:
                            prev_result = get_sorted_dict(prev_result)

                        master_table_obj = get_per_vp_dict_table_obj(result=result, prev_result=prev_result)

                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
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
                    do_sleep_for_interval()
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def print_diff_result_single_dict_table_obj(self, master_table_obj, result, prev_result, grep_regex=None):
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

    def print_single_dict_table_obj(self, master_table_obj, result, grep_regex=None):
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

    def peek_pervppkts_stats(self, cluster_id, core_id=None, grep_regex=None, get_result_only=False):
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
                        '''
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
                        '''
                        if core_id is not None:
                            result = self._get_cluster_core_parsed_dict(output_dict=result, cluster_id=cluster_id,
                                                                        core_id=core_id)
                        if prev_result:
                            self.print_diff_result_single_dict_table_obj(master_table_obj=master_table_obj,
                                                                         result=result, prev_result=prev_result,
                                                                         grep_regex=grep_regex)
                        else:
                            self.print_single_dict_table_obj(master_table_obj=master_table_obj, result=result,
                                                             grep_regex=grep_regex)

                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
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
                                add_finally = False
                                table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                table_obj.align = 'l'
                                for _key in sorted(result[key]):
                                    add_finally = False
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
                                        add_finally = True
                                        table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
                                    if not add_finally:
                                        master_table_obj.add_row([key, table_obj])
                                if add_finally:
                                    master_table_obj.add_row([key, table_obj])
                        else:
                            for key in sorted(result):
                                add_finally = False
                                table_obj = PrettyTable(['Field Name', 'Counter'])
                                table_obj.align = 'l'
                                for _key in sorted(result[key]):
                                    add_finally = False
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
                                        add_finally = True
                                        table_obj.add_row([_key, result[key][_key]])
                                    if not add_finally:
                                        master_table_obj.add_row([key, table_obj])
                                if add_finally:
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
                    do_sleep_for_interval()
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
                    do_sleep_for_interval()
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

    def peek_pc_resource_stats(self, cluster_id, core_id=None, grep_regex=None, get_result_only=False):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "stats/resource/pc/[%s]" % cluster_id
                    result = self.dpc_client.execute(verb='peek', arg_list=[cmd])
                    master_table_obj = PrettyTable()
                    master_table_obj.align = 'l'
                    master_table_obj.border = False
                    master_table_obj.header = False

                    if result:
                        '''
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
                        '''
                        if core_id is not None:
                            result = self._get_cluster_core_parsed_dict(output_dict=result, cluster_id=cluster_id,
                                                                        core_id=core_id, pc_resource=True)
                        if prev_result:
                            self.print_diff_result_single_dict_table_obj(master_table_obj=master_table_obj,
                                                                         result=result, prev_result=prev_result,
                                                                         grep_regex=grep_regex)
                        else:
                            self.print_single_dict_table_obj(master_table_obj=master_table_obj, result=result,
                                                             grep_regex=grep_regex)

                        if get_result_only:
                            return cmd, master_table_obj
                        prev_result = result
                        print master_table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
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
                do_sleep_for_interval()
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
            cmd = "stats/resource/hux[%s]" % hu_id
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
        self._display_list_of_dict_stats(cmd=cmd, grep_regex=grep_regex)

    # def peek_bam_resource_stats(self, grep_regex=None, get_result_only=False):
    #     cmd = "stats/resource/bam"
    #     verb = "peek"
    #     tid = 0
    #     au_sort = False
    #     prev_result = None
    #     try:
    #         bam_pool_decode_dict ={
	# 	'pool0': 'BM_POOL_FUNOS',
	# 	'pool1': 'BM_POOL_NU_ETP_CMDLIST',
	# 	'pool2': 'BM_POOL_HU_REQ',
	# 	'pool3': 'BM_POOL_SW_PREFETCH',
	# 	'pool4': 'BM_POOL_NU_ERP_FCP',
	# 	'pool19': 'BM_POOL_NU_ERP_CC',
	# 	'pool20': 'BM_POOL_NU_ERP_SAMPLING',
	# 	'pool34': 'BM_POOL_REGEX',
	# 	'pool35': 'BM_POOL_REFBUF',
	# 	'pool49': 'BM_POOL_NU_ERP_NONFCP',
	# 	'pool50': 'BM_POOL_HNU_NONFCP',
	# 	'pool62': 'BM_POOL_HNU_PREFETCH',
	# 	'pool63': 'BM_POOL_NU_PREFETCH',}
    #
    #         while True:
    #             try:
    #                 if type(cmd) == list:
    #                     result = self.dpc_client.execute(verb=verb, arg_list=cmd, tid=tid)
    #                 else:
    #                     result = self.dpc_client.execute(verb=verb, arg_list=[cmd], tid=tid)
    #                 result = self._sort_bam_keys(result=result, au_sort=au_sort)
    #                 if result:
    #                     if prev_result:
    #                         diff_result = self._get_difference(result=result, prev_result=prev_result)
    #                         table_obj = PrettyTable(['Field Name', 'Counters', 'Diff Counters'])
    #                         table_obj.align = 'l'
    #                         for key in result:
    #                             decode_value = ''
    #                             pool_value = key.split(' ')[0]
    #                             if 'usage' in key:
    #                                 pool_value = key.split(' ')[1]
    #                             if pool_value in bam_pool_decode_dict:
    #                                 decode_value = bam_pool_decode_dict[pool_value]
    #                             if grep_regex:
    #                                 if re.search(grep_regex, decode_value, re.IGNORECASE):
    #                                     table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], diff_result[key]])
    #                             else:
    #                                 table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], diff_result[key]])
    #                     else:
    #                         table_obj = PrettyTable(['Field Name', 'Counters'])
    #                         table_obj.align = 'l'
    #                         for key in result:
    #                             decode_value = ''
    #                             pool_value = key.split(' ')[0]
    #                             if 'usage' in key:
    #                                 pool_value = key.split(' ')[1]
    #                             if pool_value in bam_pool_decode_dict:
    #                                 decode_value = bam_pool_decode_dict[pool_value]
    #                             if grep_regex:
    #                                 if re.search(grep_regex, decode_value, re.IGNORECASE):
    #                                     table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key]])
    #                             else:
    #                                 table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], ])
    #                     if get_result_only:
    #                         return cmd, table_obj
    #                     prev_result = result
    #                     print table_obj
    #                     print "\n########################  %s ########################\n" % str(self._get_timestamp())
    #                     do_sleep_for_interval()
    #                 else:
    #                     if get_result_only:
    #                         return cmd, "Empty Result"
    #                     print "Empty Result"
    #                     do_sleep_for_interval()
    #             except KeyboardInterrupt:
    #                 self.dpc_client.disconnect()
    #                 break
    #     except Exception as ex:
    #         print "ERROR: %s" % str(ex)
    #         self.dpc_client.disconnect()

    def _get_max_reference_keys(self, result, reference_cluster):
        reference_keys = reference_cluster.keys()
        num_keys = len(reference_keys)
        for key, val in result.iteritems():
            if len(val) > num_keys:
                reference_keys = val.keys()
        return reference_keys

    def _print_master_table_columns(self, print_keys, print_values):
        master_table_obj = PrettyTable()
        master_table_obj.header = True
        master_table_obj.border = True
        master_table_obj.align = 'l'
        for col_name, col_values in zip(print_keys, print_values):
            master_table_obj.add_column(col_name, col_values)
        print master_table_obj

    def get_bam_flow_control_configs(self, per_pool):
        try:
            print "bam flow_control configs"
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _invert_output_dict(self, output_dict):
        new_output = OrderedDict()
        temp_list = []
        for key, val in output_dict.iteritems():
            val.insert(0, key)
            temp_list.append(val)
        for key in temp_list[0]:
            new_output[key] = []
            index = temp_list[0].index(key)
            for item in temp_list[1:]:
                new_output[key].append(item[index])
        return new_output

    def get_bam_usage(self):
        cmd = "stats/resource/bam"
        row_list = ['key names']
        for x in range(9):
            row_list.append('C' + str(x) + ":" + 'size_AUs')
            row_list.append('C' + str(x) + ":" + 'size_KB')
        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
        result = result['bm_usage_per_cluster']
        reference_cluster = result['cluster_0']
        reference_keys = self._get_max_reference_keys(result, reference_cluster)
        output = OrderedDict()
        for col_name in row_list:
            output[col_name] = []
            if col_name == 'key names':
                output[col_name].extend(sorted(reference_keys))
            else:
                cname = col_name.replace('C', 'cluster_')
                cluster_name = cname.split(":")[0]
                key_name = 'pool_' + cname.split(":")[1]
                cls_output = result[cluster_name]
                for display_key in sorted(reference_keys):
                    if display_key in cls_output:
                        output[col_name].append(cls_output[display_key][key_name])
                    else:
                        output[col_name].append(0)
        print_keys = output.keys()
        print_values = output.values()
        self._print_master_table_columns(print_keys, print_values)

    def _get_bam_pool_config(self):
        cmd = "config/bam/pool_config"
        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])

        all_keys = sorted(result.keys())
        reference_pool = all_keys[0]
        reference_pool = result[reference_pool]
        reference_keys = self._get_max_reference_keys(result, reference_pool)
        row_list = ['key names']
        output = OrderedDict()
        output[row_list[0]] = all_keys
        for x in sorted(reference_keys):
            output[x] = []
            row_list.append(x)
        for key in all_keys:
            for _key in reference_keys:
                val = None
                if _key in result[key]:
                    val = result[key][_key]
                output[_key].append(val)
        print_keys = output.keys()
        print_values = output.values()
        self._print_master_table_columns(print_keys, print_values)

    def _get_bam_ncv_config(self):
        cmd = "config/bam/ncv_config"
        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
        pc_result = result['pc_count']
        print "pc_count:%s" % pc_result
        del result['pc_count']
        all_keys = sorted(result.keys())
        reference_pool = all_keys[0]
        reference_pool = result[reference_pool]
        reference_keys = self._get_max_reference_keys(result, reference_pool)
        row_list = ['key names']
        output = OrderedDict()
        output[row_list[0]] = all_keys
        for x in sorted(reference_keys):
            output[x] = []
            row_list.append(x)
        for key in all_keys:
            for _key in reference_keys:
                val = None
                if _key in result[key]:
                    val = result[key][_key]
                output[_key].append(val)
        output = self._invert_output_dict(output)
        print_keys = output.keys()
        print_values = output.values()
        self._print_master_table_columns(print_keys, print_values)

    def _get_bam_global_flow_control(self):
        cmd = "config/bam/global_flow_control"
        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
        print "Not implemented"

    def _get_bam_per_pool_flow_control(self):
        cmd = "config/bam/per_pool_flow_control"
        result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
        print "Not implemented"

    def get_nu_configs(self, config_type):
        try:
            if config_type == 'pool_config':
                self._get_bam_pool_config()
            elif config_type == 'ncv_config':
                self._get_bam_ncv_config()
            elif config_type == 'per_pool_flow_control':
                self._get_bam_per_pool_flow_control()
            elif config_type == 'global_flow_control':
                self._get_bam_global_flow_control()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _get_cid_bam_results(self, result, cid):
        for key in result.keys():
            if key == 'bm_usage_per_cluster':
                for _key in result[key].keys():
                    if not str(cid) == _key.split("_")[1]:
                        del result[key][_key]
        return result

    def peek_bam_resource_stats(self, cid=None, diff=None, grep_regex=None, get_result_only=False):
        prev_global_result = None
        prev_per_cluster_result = None
        while True:
            try:
                cmd = "stats/resource/bam"
                result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
                if not result:
                    break
                reference_keys = self._get_max_reference_keys(result['bm_usage_per_cluster'],
                                                              result['bm_usage_per_cluster']['cluster_0'])
                if cid:
                    result = self._get_cid_bam_results(result, cid)
                gloabl_result = result['bm_usage_global']
                per_cluster_result = result['bm_usage_per_cluster']
                if prev_global_result and diff:
                    diff_result = self._get_nested_dict_difference(result=gloabl_result, prev_result=prev_global_result)
                    global_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                    global_table_obj.align = 'l'
                    for key, val in gloabl_result.iteritems():
                        global_table_obj.add_row([key, val, diff_result[key]])
                if prev_per_cluster_result and diff:
                    row_list = ['key names']
                    for key in sorted(per_cluster_result.keys()):
                        row_list.append(key[0].upper() + key[-1] + ":" + "%")
                        row_list.append(key[0].upper() + key[-1] + ":" + "d_%")
                        row_list.append(key[0].upper() + key[-1] + ":" + "col")
                        row_list.append(key[0].upper() + key[-1] + ":" + "d_col")
                    per_cluster_table_obj = PrettyTable()

                    output = OrderedDict()
                    for col_name in row_list:
                        output[col_name] = []
                        if col_name == 'key names':
                            output[col_name].extend(sorted(reference_keys))
                        else:
                            cname = col_name.replace('C', 'cluster_')
                            cluster_name = cname.split(":")[0]
                            key_name = cname.split(":")[1]
                            if key_name == '%':
                                key_name = 'usage_percent'
                            elif key_name == 'col':
                                key_name = 'color'
                            cls_output = per_cluster_result[cluster_name]
                            if 'd_' in key_name:
                                cls_output = prev_per_cluster_result[cluster_name]
                            for display_key in sorted(reference_keys):
                                if display_key in cls_output:
                                    if key_name in cls_output[display_key]:
                                        output[col_name].append(cls_output[display_key][key_name])
                                    else:
                                        output[col_name].append(0)
                                else:
                                    output[col_name].append(0)
                else:
                    # Global table object
                    global_table_obj = PrettyTable(['Field Name', 'Counter'])
                    global_table_obj.align = 'l'
                    for key, val in gloabl_result.iteritems():
                        global_table_obj.add_row([key, val])

                    # Per cluster table
                    row_list = ['key names']
                    for key in sorted(per_cluster_result.keys()):
                        row_list.append(key[0].upper() + key[-1] + ":" + "%")
                        row_list.append(key[0].upper() + key[-1] + ":" + "col")
                    per_cluster_table_obj = PrettyTable()

                    output = OrderedDict()
                    for col_name in row_list:
                        output[col_name] = []
                        if col_name == 'key names':
                            output[col_name].extend(sorted(reference_keys))
                        else:
                            cname = col_name.replace('C', 'cluster_')
                            cluster_name = cname.split(":")[0]
                            key_name = cname.split(":")[1]
                            if key_name == '%':
                                key_name = 'usage_percent'
                            elif key_name == 'col':
                                key_name = 'color'
                            cls_output = per_cluster_result[cluster_name]
                            for display_key in sorted(reference_keys):
                                if display_key in cls_output:
                                    if key_name in cls_output[display_key]:
                                        output[col_name].append(cls_output[display_key][key_name])
                                    else:
                                        output[col_name].append(0)
                                else:
                                    output[col_name].append(0)
                print_keys = output.keys()
                print_values = output.values()
                for col_name, col_values in zip(print_keys, print_values):
                    per_cluster_table_obj.add_column(col_name, col_values)


                if get_result_only:
                    return cmd, global_table_obj, per_cluster_table_obj
                prev_global_result = gloabl_result
                prev_per_cluster_result = per_cluster_result
                print global_table_obj
                print per_cluster_table_obj
                print "\n########################  %s ########################\n" % str(self._get_timestamp())
                do_sleep_for_interval()
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
                break
            except Exception as ex:
                print "ERROR: %s" % str(ex)
                self.dpc_client.disconnect()
                break
    # def peek_bam_resource_stats(self, cid=None, grep_regex=None, get_result_only=False):
    #     prev_result = None
    #     while True:
    #         try:
    #             cmd = "stats/resource/bam"
    #             master_table_obj = PrettyTable()
    #             master_table_obj.header = False
    #             master_table_obj.border = False
    #             master_table_obj.align = 'l'
    #             result = self.dpc_client.execute(verb="peek", arg_list=[cmd])
    #             if cid:
    #                 result = self._get_cid_bam_results(result, cid)
    #             if prev_result:
    #                 diff_result = self._get_nested_dict_difference(result=result, prev_result=prev_result)
    #                 for key in sorted(result):
    #                     table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
    #                     table_obj.align = 'l'
    #                     table_obj.sortby = 'Field Name'
    #                     for _key in result[key]:
    #                         if grep_regex:
    #                             if re.search(grep_regex, key, re.IGNORECASE):
    #                                 table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
    #                         else:
    #                             if type(result[key][_key]) == dict:
    #                                 inner_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
    #                                 inner_table_obj.align = 'l'
    #                                 inner_table_obj.sortby = 'Field Name'
    #                                 for inner_key in result[key][_key]:
    #                                     if type(result[key][_key]) == dict:
    #                                         _inner_table_obj = PrettyTable(['Field Name', 'Counters', 'Counter Diff'])
    #                                         _inner_table_obj.align = 'l'
    #                                         _inner_table_obj.sortby = 'Field Name'
    #                                         for _inner_key in result[key][_key][inner_key]:
    #                                             _inner_table_obj.add_row([_inner_key, result[key][_key][inner_key][_inner_key],
    #                                                                       diff_result[key][_key][inner_key][_inner_key]])
    #                                         inner_table_obj.add_row([inner_key, _inner_table_obj, ""])
    #                                     else:
    #                                         inner_table_obj.add_row([inner_key, result[key][_key][inner_key],
    #                                                                  diff_result[key][_key][inner_key]])
    #                                 table_obj.add_row([_key, inner_table_obj, ""])
    #                             else:
    #                                 table_obj.add_row([_key, result[key][_key], diff_result[key][_key]])
    #                     if table_obj.rowcount > 0:
    #                         master_table_obj.add_row([key, table_obj])
    #             else:
    #                 for key in sorted(result):
    #                     table_obj = PrettyTable(['Field Name', 'Counters'])
    #                     table_obj.align = 'l'
    #                     table_obj.sortby = 'Field Name'
    #                     for _key in result[key]:
    #                         if grep_regex:
    #                             if re.search(grep_regex, key, re.IGNORECASE):
    #                                 table_obj.add_row([_key, result[key][_key]])
    #                         else:
    #                             if type(result[key][_key]) == dict:
    #                                 inner_table_obj = PrettyTable(['Field Name', 'Counters'])
    #                                 inner_table_obj.align = 'l'
    #                                 inner_table_obj.sortby = 'Field Name'
    #                                 for inner_key in result[key][_key]:
    #                                     if type(result[key][_key]) == dict:
    #                                         _inner_table_obj = PrettyTable(['Field Name', 'Counters'])
    #                                         _inner_table_obj.align = 'l'
    #                                         _inner_table_obj.sortby = 'Field Name'
    #                                         for _inner_key in result[key][_key][inner_key]:
    #                                             _inner_table_obj.add_row([_inner_key, result[key][_key][inner_key][_inner_key]])
    #                                         inner_table_obj.add_row([inner_key, _inner_table_obj])
    #                                     else:
    #                                         inner_table_obj.add_row([inner_key, result[key][_key][inner_key]])
    #                                 table_obj.add_row([_key, inner_table_obj])
    #                             else:
    #                                 table_obj.add_row([_key, result[key][_key]])
    #                     if table_obj.rowcount > 0:
    #                         master_table_obj.add_row([key, table_obj])
    #             if get_result_only:
    #                 return cmd, master_table_obj
    #             prev_result = result
    #             print master_table_obj
    #             print "\n########################  %s ########################\n" % str(self._get_timestamp())
    #             do_sleep_for_interval()
    #         except KeyboardInterrupt:
    #             self.dpc_client.disconnect()
    #             break
    #         except Exception as ex:
    #             print "ERROR: %s" % str(ex)
    #             self.dpc_client.disconnect()
    #             break
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
                        do_sleep_for_interval()
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

    def peek_hbm_stats(self, muh=None, grep_regex=None, get_result_only=False):
        cmd = "stats/hbm/hbm_cnts"
        if muh:
            cmd += "/muh_%s" % muh
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
                    result = result["eqm_stats"]
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
                        do_sleep_for_interval()
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
                        do_sleep_for_interval()
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
                        do_sleep_for_interval()
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
                        do_sleep_for_interval()
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
                            diff_result = self._get_nested_dict_difference(result=result, prev_result=prev_result)
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
                                        if type(result[key][_key][in_key]) == dict:
                                            nested_table_obj = PrettyTable(['Field Name', 'Counter', 'Counter Diff'])
                                            nested_table_obj.align = 'l'
                                            nested_table_obj.sortby = 'Field Name'
                                            for nested_in_key in sorted(result[key][_key][in_key]):
                                                nested_table_obj.add_row([nested_in_key, result[key][_key][in_key][nested_in_key],
                                                                         diff_result[key][_key][in_key][nested_in_key]])
                                            inner_table_obj.add_row([in_key, nested_table_obj, ""])
                                        else:
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
                                        if type(result[key][_key][in_key]) == dict:
                                            nested_table_obj = PrettyTable(['Field Name', 'Counter'])
                                            nested_table_obj.align = 'l'
                                            nested_table_obj.sortby = 'Field Name'
                                            for nested_in_key in sorted(result[key][_key][in_key]):
                                                nested_table_obj.add_row([nested_in_key, result[key][_key][in_key][nested_in_key]])
                                            inner_table_obj.add_row([in_key, nested_table_obj])
                                        else:
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
                        do_sleep_for_interval()
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
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


    def _get_all_rdma(self, output_dict, hu_id, qpn_number=None):
        result = {}
        result['rdma'] = {}
        for key, val in output_dict.iteritems():
            if key.split(".")[0] == str(hu_id) and 'rdma' in val.keys():
                if qpn_number:
                    for item in val['rdma']:
                        if str(qpn_number) == str(item['QPN']):
                            result['rdma'][key] = []
                            result['rdma'][key].append(item)
                            break
                else:
                    result['rdma'][key] = output_dict[key]['rdma']
        return result

    def peek_stats_rdma(self, hu_id, qpn_number=None, grep_regex=None):
        try:
            prev_result = None
            while True:
                try:
                    cmd = "list"
                    output = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                    result = self._get_all_rdma(output, hu_id, qpn_number)
                    if result['rdma']:
                        if prev_result:
                            result = result['rdma']
                            master_table_obj = PrettyTable(['id:qpn', 'values'])
                            master_table_obj.align = 'l'
                            for key, val in result.iteritems():
                                for item in val:
                                    table_obj = PrettyTable(['Field', 'Counter', "Counter_Diff"])
                                    table_obj.align = 'l'
                                    qpn_id = item['QPN']
                                    for new_item in prev_result[key]:
                                        if qpn_id == new_item['QPN']:
                                            diff_item = new_item
                                            break
                                    for _key in sorted(item):
                                        if isinstance(item[_key], dict):
                                            for inner_key, inner_val in item[_key].iteritems():
                                                if isinstance(inner_val, int):
                                                    table_obj.add_row([_key + ":" + inner_key, inner_val,
                                                                       int(inner_val) - int(diff_item[_key][inner_key])])
                                        else:
                                            if isinstance(item[_key], int):
                                                table_obj.add_row([_key, item[_key], int(item[_key]) - int(diff_item[_key])])
                                    master_table_obj.add_row([key + ":" + str(qpn_id), table_obj])
                        else:
                            result = result['rdma']
                            master_table_obj = PrettyTable(['id:qpn', 'values'])
                            master_table_obj.align = 'l'
                            for key, val in result.iteritems():
                                for item in val:
                                    table_obj = PrettyTable(['Field', 'Counter'])
                                    table_obj.align = 'l'
                                    qpn_id = item['QPN']
                                    for _key in sorted(item):
                                        if isinstance(item[_key], dict):
                                            for inner_key, inner_val in item[_key].iteritems():
                                                if isinstance(inner_val, int):
                                                    table_obj.add_row([_key + ":" + inner_key, inner_val])
                                        else:
                                            if isinstance(item[_key], int):
                                                table_obj.add_row([_key, item[_key]])
                                    master_table_obj.add_row([key + ":" + str(qpn_id), table_obj])
                        print master_table_obj
                        prev_result = result
                        print "\n########################  %s ########################\n" % str(self._get_timestamp())
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                        break
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def peek_nhp_status(self, grep_regex=None, get_result_only=False):
        cmd = "status/nhp"
        if get_result_only:
            return self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=True)
        else:
            self._display_stats(cmd=cmd, grep_regex=grep_regex, get_result_only=get_result_only)


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
            command_dict['per_vp stats'] = self.peek_stats_per_vp_pp(get_result_only=True)
            for i in range(9):
                command_dict['pervppkts stats'] = self.peek_pervppkts_stats(cluster_id=i, get_result_only=True)
            command_dict['nwqm stats'] = self.peek_nwqm_stats(get_result_only=True)
            command_dict['nhp stats'] = self.peek_nhp_stats(get_result_only=True)
            command_dict['sse stats'] = self.peek_sse_stats(get_result_only=True)
            command_dict['resource bam stats'] = self.peek_bam_resource_stats(get_result_only=True)
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

    def _get_core_id_vp_num(self, val):
        core_id = None
        vp_num = None
        try:
            vp_num = int(val) % TOTAL_VPS_PER_CORE
            core_id = (int(val)/TOTAL_VPS_PER_CORE) - 2
        except Exception as ex:
            print "ERROR: %s" % str(ex)
        return core_id, vp_num

    def _get_callee_list(self, result):
        callee_list = []
        for key, val in result.iteritems():
            if str(key) == '3.2.2':
                if isinstance(val, dict):
                    for _key, _val in val.iteritems():
                        if isinstance(_val, list):
                            for value in _val:
                                if 'callee' in value:
                                    callee_list.append(value['callee'])
                                break
        return callee_list


    def _get_info_for_id(self, queues, id, module_name):
        output = {}
        for queue in queues:
            if 'flow' in queue.keys():
                if queue['flow']['id'] == id:
                    if module_name == 'ethernet':
                        output['eth_vp'] = queue['flow']['dest']
                        output['eth_pkts'] = queue['packets']
                        output['eth_bytes'] = queue['bytes']
                        output['hw_blockedcnt'] = queue['flow']['hw_blockedcnt']
                        output['sw_blockedcnt'] = queue['flow']['sw_blockedcnt']
                    elif module_name == 'epcq':
                        output['epcq_vp'] = queue['flow']['dest']
                        output['cqe_count'] = queue['cqe_count']
                        output['hw_blockedcnt'] = queue['flow']['hw_blockedcnt']
                        output['sw_blockedcnt'] = queue['flow']['sw_blockedcnt']
                    elif module_name == 'virtual_interface':
                        output['vi_vp'] = queue['flow']['dest']
                        output['vi_pkts'] = queue['packets']
                        output['vi_bytes'] = queue['bytes']
                    break
        return output

    def get_queue_parsed_dict(self, result, queue):
        output = {}
        for key, val in result.iteritems():
            if isinstance(val, dict):
                # TODO: Remove ethernet and virtual interface in below condition if needed
                if 'epsq' in val.keys() and 'epcq' in val.keys() and 'ethernet' in val.keys() and 'virtual_interface' in val.keys():
                    output[key] = OrderedDict()
                    epsqs = val['epsq']
                    epcqs = val['epcq']
                    ethernets = val['ethernet']
                    vis = val['virtual_interface']
                    for epsq in epsqs:
                        for _key, _val in epsq.iteritems():
                            if 'callee' in str(_key) and _val['module'] in queue:
                                output[key][_val['id']] = OrderedDict()
                                output[key][_val['id']]['flow_id'] = epsq['flow']['id']
                                output[key][_val['id']]['epsq_vp'] = epsq['flow']['dest']
                                output[key][_val['id']]['epsq_dest_vp'] = epsq['callee']['dest']
                                output[key][_val['id']]['epsq_sqe_cnt'] = epsq['sqe_count']
                                output[key][_val['id']]['epsq_hw_bcnt'] = epsq['flow']['hw_blockedcnt']
                                output[key][_val['id']]['eqsq_sw_bcnt'] = epsq['flow']['sw_blockedcnt']
                                if queue == 'ethernet':
                                    ethernet = self._get_info_for_id(ethernets, _val['id'], module_name='ethernet')
                                    eth_vp = None
                                    eth_pkts = None
                                    eth_bytes = None
                                    eth_hw_blockedcnt = None
                                    eth_sw_blockedcnt = None
                                    if ethernet:
                                        eth_vp = ethernet['eth_vp']
                                        eth_pkts = ethernet['eth_pkts']
                                        eth_bytes = ethernet['eth_bytes']
                                        eth_hw_blockedcnt = ethernet['hw_blockedcnt']
                                        eth_sw_blockedcnt = ethernet['sw_blockedcnt']
                                    output[key][_val['id']]['eth_vp'] = eth_vp
                                    output[key][_val['id']]['eth_pkts'] = eth_pkts
                                    output[key][_val['id']]['eth_bytes'] = eth_bytes
                                    output[key][_val['id']]['eth_hw_bcnt'] = eth_hw_blockedcnt
                                    output[key][_val['id']]['eth_sw_bcnt'] = eth_sw_blockedcnt

                                    # Virtual Interface
                                    # TODO: Remove virtual interface for now
                                    '''
                                    vi = self._get_info_for_id(vis, _val['id'], module_name='virtual_interface')
                                    vi_vp = None
                                    vi_pkts = None
                                    vi_bytes = None
                                    if vi:
                                        vi_vp = vi['vi_vp']
                                        vi_pkts = vi['vi_pkts']
                                        vi_bytes = vi['vi_bytes']
                                    output[key][_val['id']]['vi_vp'] = vi_vp
                                    output[key][_val['id']]['vi_pkts'] = vi_pkts
                                    output[key][_val['id']]['vi_bytes'] = vi_bytes
                                    '''
                                elif queue == 'epcq':
                                    epcq = self._get_info_for_id(epcqs, _val['id'], module_name='epcq')
                                    output[key][_val['id']]['epcq_vp'] = epcq['epcq_vp']
                                    output[key][_val['id']]['epcq_cqe_cnt'] = epcq['cqe_count']
                                    output[key][_val['id']]['epcq_hw_bcnt'] = epcq['hw_blockedcnt']
                                    output[key][_val['id']]['epcq_sw_bcnt'] = epcq['sw_blockedcnt']
                                    '''
                                    vi = self._get_info_for_id(vis, _val['id'], module_name='virtual_interface')
                                    output[key][_val['id']]['vi_vp'] = vi['vi_vp']
                                    output[key][_val['id']]['vi_pkts'] = vi['vi_pkts']
                                    output[key][_val['id']]['vi_bytes'] = vi['vi_bytes']
                                    '''
        return output

    def _get_flow_list_diff_dict(self, parsed_result, prev_parsed_result):
        diff_dict = OrderedDict()
        for key, val in parsed_result.iteritems():
            if key not in diff_dict:
                diff_dict[key] = OrderedDict()
            for key1, val1 in val.iteritems():
                diff_dict[key][key1] = OrderedDict()
                current_id_key = val1['flow_id']
                prev_result_id_key = None
                if key1 in prev_parsed_result[key]:
                    prev_result_id_key = prev_parsed_result[key][key1]['flow_id']
                if current_id_key == prev_result_id_key:
                    for _key, _val in val1.iteritems():
                        diff_dict[key][key1][_key] = _val
                        if 'id' not in _key and isinstance(_val, int):
                            diff_dict[key][key1]['d_' + _key] = int(_val) - int(prev_parsed_result[key][key1][_key])
        return diff_dict

    def _print_flow_list_table(self, output_dict):
        tx_entry = output_dict.values()[0]
        first_entry = tx_entry.values()[0]
        col_names = first_entry.keys()
        col_names.insert(0, 'id')

        master_table_obj = PrettyTable(col_names)
        for key, val in output_dict.iteritems():
            for _key, _val in val.iteritems():
                all_vals = _val.values()
                all_vals.insert(0, key)
                master_table_obj.add_row(all_vals)
        print master_table_obj

    def get_flow_list_pp(self, hcf_id=None,hu_id=None, tx=None, rx=None, grep_regex=None):
        try:
            prev_tx_parsed_dict = None
            prev_rx_parsed_dict = None
            tx_parsed_dict = None
            rx_parsed_dict = None
            try:
                while True:
                    cmd = "list"
                    output = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                    if output:
                        result = output
                        if hu_id:
                            result = {}
                            key_list = []
                            for key in output.keys():
                                if hu_id == key.split(".")[0]:
                                    key_list.append(key)
                            if not key_list:
                                print "hu_id %s entry not found" % hu_id
                                return self.dpc_client.disconnect()
                            for id in key_list:
                                result[str(id)] = output[str(id)]
                        elif hcf_id:
                            result = {}
                            if not hcf_id in output.keys():
                                print "hcf_id %s entry not found" % hcf_id
                                return self.dpc_client.disconnect()
                            result[hcf_id] = output[hcf_id]
                        if tx:
                            print "\n********** Displaying tx table below **********\n"
                            tx_parsed_dict = self.get_queue_parsed_dict(result, queue='ethernet')
                            if prev_tx_parsed_dict:
                                self._print_flow_list_table(self._get_flow_list_diff_dict(tx_parsed_dict, prev_tx_parsed_dict))
                            elif tx_parsed_dict:
                                self._print_flow_list_table(tx_parsed_dict)
                            else:
                                print "No tx entries found"
                                self.dpc_client.disconnect()
                                break
                        if rx:
                            print "\n********** Displaying rx table below **********\n"
                            rx_parsed_dict = self.get_queue_parsed_dict(result, queue='epcq')
                            if prev_rx_parsed_dict:
                                self._print_flow_list_table(
                                    self._get_flow_list_diff_dict(rx_parsed_dict, prev_rx_parsed_dict))
                            elif rx_parsed_dict:
                                self._print_flow_list_table(rx_parsed_dict)
                            else:
                                print "No rx entries found"
                                self.dpc_client.disconnect()
                                break
                    print "\n########################  %s ########################\n" % str(self._get_timestamp())
                    prev_tx_parsed_dict = tx_parsed_dict
                    prev_rx_parsed_dict = rx_parsed_dict
                    do_sleep_for_interval()
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def get_flow_list(self, hcf_id=None,hu_id=None, grep_regex=None):
        try:
            prev_result = None
            while True:
                master_table_obj = PrettyTable()
                master_table_obj.align = 'l'
                master_table_obj.header = False
                try:
                    cmd = "list"
                    output = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                    if output:
                        result = output
                        if hu_id:
                            result = {}
                            key_list = []
                            for key in output.keys():
                                if hu_id == key.split(".")[0]:
                                    key_list.append(key)
                            if not key_list:
                                print "hu_id %s entry not found" % hu_id
                                return self.dpc_client.disconnect()
                            for id in key_list:
                                result[str(id)] = output[str(id)]
                        elif hcf_id:
                            result = {}
                            if not hcf_id in output.keys():
                                print "hcf_id %s entry not found" % hcf_id
                                return self.dpc_client.disconnect()
                            result[hcf_id] = output[hcf_id]
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
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def _get_all_rdma(self, output_dict, hu_id, qpn_number=None):
        result = {}
        result['rdma'] = {}
        for key, val in output_dict.iteritems():
            if key.split(".")[0] == str(hu_id) and 'rdma' in val.keys():
                if qpn_number:
                    for item in val['rdma']:
                        if str(qpn_number) == str(item['QPN']):
                            result['rdma'][key] = []
                            result['rdma'][key].append(item)
                            break
                else:
                    result['rdma'][key] = output_dict[key]['rdma']
        return result

    def get_flow_list_rdma(self, hu_id, qpn_number=None, grep_regex=None):
        try:
            try:
                cmd = "list"
                output = self.dpc_client.execute(verb='flow', arg_list=[cmd])
                result = self._get_all_rdma(output, hu_id, qpn_number)
                if result['rdma']:
                    result = result['rdma']
                    master_table_obj = PrettyTable(['id:qpn', 'values'])
                    master_table_obj.align = 'l'
                    for key, val in result.iteritems():
                        for item in val:
                            table_obj = PrettyTable(['Field', 'Counter'])
                            table_obj.align = 'l'
                            qpn_id = item['QPN']
                            for _key in sorted(item):
                                if isinstance(item[_key], dict):
                                    for inner_key, inner_val in item[_key].iteritems():
                                        table_obj.add_row([_key + ":" + inner_key, inner_val])
                                else:
                                    table_obj.add_row([_key, item[_key]])
                            master_table_obj.add_row([key + ":" + str(qpn_id), table_obj])
                    print master_table_obj
                else:
                    print "Empty Result"
            except KeyboardInterrupt:
                self.dpc_client.disconnect()
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
                        do_sleep_for_interval()
                    else:
                        print "Empty Result"
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()


class DebugCommands(PeekCommands):

    def get_filtered_dict(self, output_dict, cluster_id=None, core_id=None):
        result = OrderedDict()
        start_key_name = 'CCV'
        for key, val in output_dict.iteritems():
            if cluster_id is not None and core_id is not None:
                key_name = start_key_name + "%s.%s" % (cluster_id, core_id)
                if key_name in key:
                    result[key] = val
            elif cluster_id is not None:
                key_name = start_key_name + "%s" % (cluster_id)
                if key_name in key:
                    result[key] = val
            else:
                result = output_dict
                break
        return result

    def _print_val_red_color(self, val):
        val = "\033[91m " + val + " \033[0m"
        return val

    def _format_data_output(self, val):
        if val == "N/A":
            return val
        val = "{:.0f}".format(val * 100)
        if int(val) >= 90:
            val = self._print_val_red_color(val)
        return val


    def _format_non_zero_values(self, list_of_lists):
        index_list = []
        for cls, vp_0, vp_1, vp_2, vp_3 in zip(list_of_lists[0],list_of_lists[1],list_of_lists[2],list_of_lists[3],list_of_lists[4]):
            if (vp_0 == '0' and vp_1 == '0' and vp_2 == '0' and vp_3 == '0') or ((vp_0 == 'N/A' or vp_0 == '0') and (vp_1 == 'N/A' or vp_1 == '0') and vp_2 == 'N/A' and vp_3 == 'N/A'):
                index_list.append(list_of_lists[0].index(cls))
        for index in sorted(index_list, reverse=True):
            for list in list_of_lists:
                del list[index]
        return list_of_lists

    def get_vp_util_parsed_data_dict(self, result):
        complete_dict = OrderedDict()
        rows_list = ["Cls/Core", "0", "1", "2", "3"]
        for col_name in rows_list:
            complete_dict[col_name] = []
        for key, val in result.iteritems():
            val = self._format_data_output(val)
            cluster_id = key.split(".")[0][3]
            core_id = key.split(".")[1]
            vp_num = key.split(".")[2]
            for _key in rows_list:
                if _key == rows_list[0] and cluster_id + '/' + core_id not in complete_dict[_key]:
                    complete_dict[_key].append(cluster_id + '/' + core_id)
                else:
                    if _key == vp_num:
                        complete_dict[_key].append(val)
                        break
        return complete_dict

    def get_vp_util_table_obj(self, complete_dict):
        master_table_obj = PrettyTable()
        print_keys = complete_dict.keys()
        print_values = complete_dict.values()
        print_values = self._format_non_zero_values(print_values)
        for col_name, col_values in zip(print_keys, print_values):
            master_table_obj.add_column(col_name, col_values)
        return master_table_obj

    def get_normalized_data_vp_data(self, complete_dict):
        print_values = complete_dict.values()
        sum = 0
        counter = 0
        for item in print_values:
            if isinstance(item, list):
                for val in item:
                    if val.isdigit():
                        sum += int(val)
                        counter += 1
            else:
                if item.isdigit():
                    sum += int(item)
                    counter += 1
        if counter == 0:
            counter = 1
        return sum/counter

    def get_vp_util_histogram_table_obj(self, complete_dict):
        histo_table_obj = PrettyTable()
        histo_dict = {'1-10': 0, '11-20': 0, '21-30': 0, '31-40': 0, '41-50': 0, '51-60': 0, '61-70': 0,
                      '71-80': 0, '81-90': 0, '91-100': 0}
        final_list = []
        print_values = complete_dict.values()
        for inner_list in print_values:
            final_list.extend(inner_list)

        for val in final_list:
            if val.isdigit():
                val = int(val)
                if val in range(0,11):
                    if not val == 0:
                        histo_dict['1-10'] += 1
                elif val in range(11,21):
                    histo_dict['11-20'] += 1
                elif val in range(21,31):
                    histo_dict['21-30'] += 1
                elif val in range(31,41):
                    histo_dict['31-40'] += 1
                elif val in range(41,51):
                    histo_dict['41-50'] += 1
                elif val in range(51,61):
                    histo_dict['51-60'] += 1
                elif val in range(61,71):
                    histo_dict['61-70'] += 1
                elif val in range(71,81):
                    histo_dict['71-80'] += 1
                elif val in range(81,91):
                    histo_dict['81-90'] += 1
                else:
                    histo_dict['91-100'] += 1
        for key in sorted(histo_dict):
            val = []
            val.append(histo_dict[key])
            histo_table_obj.add_column(key, val)
        return histo_table_obj

    def debug_vp_util_pp(self, cluster_id=None, core_id=None, grep_regex=None):
        try:
            while True:
                try:
                    cmd = "vp_util"
                    output_dict = OrderedDict()
                    output = self.dpc_client.execute(verb='debug', arg_list=[cmd])
                    for key in sorted(output):
                        output_dict[key] = output[key]

                    if cluster_id is None and core_id is None:
                        for x in range(0, 6):
                            for y in range(2, 4):
                                if x > 3:
                                    z = 0
                                    key = 'CCV8.%s.%s' % (x, z)
                                    output_dict[key] = 'N/A'
                                    z = 1
                                    key = 'CCV8.%s.%s' % (x, z)
                                    output_dict[key] = 'N/A'
                                key = 'CCV8.%s.%s' % (x, y)
                                output_dict[key] = 'N/A'
                    result = self.get_filtered_dict(output_dict=output_dict, cluster_id=cluster_id, core_id=core_id)
                    complete_dict = self.get_vp_util_parsed_data_dict(result=result)

                    master_table_obj = self.get_vp_util_table_obj(complete_dict=complete_dict)

                    # print normalized data
                    normalized_value = self.get_normalized_data_vp_data(complete_dict=complete_dict)
                    print "Normalized VP Util: {}".format(normalized_value)

                    # print histogram
                    histogram_table_obj = self.get_vp_util_histogram_table_obj(complete_dict=complete_dict)
                    print "\nHistogram table: Num of VPs in util range"
                    print histogram_table_obj

                    print "\nVP util table"
                    print master_table_obj
                    print "\n########################  %s ########################\n" % \
                          str(self._get_timestamp())
                    do_sleep_for_interval()
                except KeyboardInterrupt:
                    self.dpc_client.disconnect()
                    break
        except Exception as ex:
            if str(ex) == 'Column length 0 does not match number of rows 4!':
                print "1st data set captured. Please re-run the command"
            else:
                print "ERROR: %s" % str(ex)
            self.dpc_client.disconnect()

    def debug_vp_util(self, cluster_id=None, core_id=None, grep_regex=None, get_result_only=False):
        try:
            while True:
                try:
                    cmd = "vp_util"
                    output_result = self.dpc_client.execute(verb='debug', arg_list=[cmd])
                    if output_result:
                        result = self.get_filtered_dict(output_dict=output_result, cluster_id=cluster_id, core_id=core_id)

                        table_obj = PrettyTable(['Field Name', 'Counters'])
                        table_obj.align = 'l'
                        table_obj.sortby = 'Field Name'
                        for key in sorted(result):
                            if grep_regex:
                                if re.search(grep_regex, key, re.IGNORECASE):
                                    table_obj.add_row([key, result[key]])
                            else:
                                table_obj.add_row([key, result[key]])
                        if get_result_only:
                            return cmd, table_obj
                        print table_obj
                        print "\n########################  %s ########################\n" % \
                              str(self._get_timestamp())
                        do_sleep_for_interval()
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


