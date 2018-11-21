from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient


class NetworkController(DpcshClient):
    COMMAND_DURATION = 20
    VERB_TYPE_PORT = 'port'
    VERB_TYPE_QOS = 'qos'
    VERB_TYPE_PEEK = 'peek'
    VERB_TYPE_POKE = 'poke'
    SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN = "dwrr"
    SCHEDULER_TYPE_SHAPER = "shaper"
    SCHEDULER_TYPE_STRICT_PRIORITY = " strict_priority"

    def __init__(self, dpc_server_ip, dpc_server_port=40221, verbose=True):
        super(NetworkController, self).__init__(mode="network", target_ip=dpc_server_ip, target_port=dpc_server_port,
                                                verbose=verbose)
        self.server_ip = dpc_server_ip
        self.server_port = dpc_server_port
        self.verbose = verbose
        # self._echo_hello()

    def echo_hello(self):
        output = None
        try:
            cmd = "Hello"
            output = self.json_execute(verb="echo", data=[cmd])
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def dpc_shutdown(self):
        result = False
        try:
            cmd = "dpc_shutdown"
            # Sometimes dpc_shutdown cmd takes 2-3 min to execute
            output = self.json_execute(verb=cmd, command_duration=180)
            if output['status']:
                result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def enable_port(self, port_num, shape=0):
        port_enabled = False
        try:
            enable_port_args = ["enable", {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enabling port %d " % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=enable_port_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(result['status'], message="Enable port %d" % port_num)
            port_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return port_enabled

    def disable_port(self, port_num, shape=0):
        port_disabled = False
        try:
            disable_port_args = ['disable', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Disabling port %d " % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=disable_port_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(result['status'], message="Disable port %d" % port_num)
            port_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return port_disabled

    def clear_port_stats(self, port_num, shape=0):
        stats_cleared = False
        try:
            clear_stats_args = ['clearstats', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Clear Port stats: %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=clear_stats_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(result['status'], message="Clear port %d stats" % port_num)
            stats_cleared = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats_cleared

    def set_port_mtu(self, port_num, mtu_value, shape=0):
        result = False
        try:
            set_mtu_args = ['mtuset', {"portnum": port_num, "shape": shape}, {'mtu': mtu_value}]
            fun_test.debug("Set port %d mtu to %d" % (port_num, mtu_value))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=set_mtu_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(json_cmd_result['status'], message="Set port %d mtu to %d" % (port_num, mtu_value))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_port_mtu(self, port_num, shape=0):
        port_mtu = None
        try:
            get_mtu_args = ['mtuget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Get port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=get_mtu_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(json_cmd_result['status'], message="Get port %d" % port_num)
            fun_test.debug("Port %d MTU: %d" % (port_num, json_cmd_result['data']))
            port_mtu = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return port_mtu

    def set_fpg_speed(self, port_num, shape=0, brk_mode="brk_4x10g"):
        speed_changed = False
        try:
            speed_change_args = ["breakoutset", {'portnum': port_num, "shape": shape}, {"brkmode": brk_mode}]
            fun_test.debug("Set Port Speed %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=speed_change_args,
                                                command_duration=self.COMMAND_DURATION, tid=1)
            fun_test.simple_assert(json_cmd_result['status'], message="Set Port Speed %d" % port_num)
            speed_changed = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return speed_changed

    def enable_link_pause(self, port_num, shape=0):
        link_pause_enabled = False
        try:
            link_pause_enable_args = ['lpena', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enabling link pause on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_enable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Enable Link Pause on %d" % port_num)
            link_pause_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return link_pause_enabled

    def disable_link_pause(self, port_num, shape=0):
        link_pause_disabled = False
        try:
            link_pause_disable_args = ['lpdis', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Disabling link pause on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_disable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Disable Link Pause on %d" % port_num)
            link_pause_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return link_pause_disabled

    def enable_tx_link_pause(self, port_num, shape=0):
        link_pause_tx_enabled = False
        try:
            link_pause_tx_enable_args = ['lptxon', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enabling TX link pause on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_tx_enable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Enable TX Link Pause on %d" % port_num)
            link_pause_tx_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return link_pause_tx_enabled

    def disable_tx_link_pause(self, port_num, shape=0):
        link_pause_tx_disabled = False
        try:
            link_pause_tx_disable_args = ['lptxoff', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Disabling TX link pause on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_tx_disable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Disable TX Link Pause on %d" % port_num)
            link_pause_tx_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return link_pause_tx_disabled

    def set_link_pause_quanta(self, port_num, quanta, shape=0):
        result = False
        try:
            link_pause_quanta_args = ['lpqset', {"portnum": port_num, "shape": shape}, {'quanta': quanta}]
            fun_test.debug("Setting link pause quanta %d on port %d" % (quanta, port_num))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_quanta_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Set Link Pause quanta %d on port %d" % (quanta, port_num))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_link_pause_quanta(self, port_num, shape=0):
        quanta_value = None
        try:
            link_pause_quanta_args = ['lpqget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Getting link pause quanta on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_quanta_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Get Link Pause on port %d" % port_num)
            fun_test.debug("Link Pause Quanta on port %d: %d" % (port_num, json_cmd_result['data']))
            quanta_value = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return quanta_value

    def set_link_pause_threshold(self, port_num, threshold, shape=0):
        result = False
        try:
            link_pause_threshold_args = ['lptset', {"portnum": port_num, "shape": shape}, {'threshold': threshold}]
            fun_test.debug("Setting link pause threshold %d on port %d" % (threshold, port_num))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_threshold_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Set Link Pause threshold %d on port %d" % (threshold, port_num))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_link_pause_threshold(self, port_num, shape=0):
        threshold_value = None
        try:
            link_pause_threshold_args = ['lptget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Getting link pause threshold on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=link_pause_threshold_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Get Link Pause on port %d" % port_num)
            fun_test.debug("Link Pause threshold on port %d: %d" % (port_num, json_cmd_result['data']))
            threshold_value = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return threshold_value

    def enable_priority_flow_control(self, port_num, shape=0):
        pfc_enabled = False
        try:
            sleep_duration = 2
            if shape:
                sleep_duration = 30
            pfc_enable_args = ['pfcena', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enabling pfc on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=pfc_enable_args,
                                       command_duration=self.COMMAND_DURATION, sleep_duration=sleep_duration)
            fun_test.simple_assert(expression=result['status'], message="Enable pfc on %d" % port_num)
            pfc_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return pfc_enabled

    def disable_priority_flow_control(self, port_num, shape=0):
        pfc_disabled = False
        try:
            pfc_disable_args = ['pfcdis', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Disabling pfc on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=pfc_disable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Disable pfc on %d" % port_num)
            pfc_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return pfc_disabled

    def enable_tx_priority_flow_control(self, port_num, class_num, shape=0):
        priority_flow_control_tx_enabled = False
        try:
            priority_flow_control_tx_enable_args = ['pfctxon', {"portnum": port_num, "shape": shape},
                                                    {"class": class_num}]
            fun_test.debug("Enabling TX pfc on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_tx_enable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Enable TX pfc on %d" % port_num)
            priority_flow_control_tx_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return priority_flow_control_tx_enabled

    def disable_tx_priority_flow_control(self, port_num, class_num, shape=0):
        priority_flow_control_tx_disabled = False
        try:
            priority_flow_control_tx_disable_args = ['pfctxoff', {"portnum": port_num, "shape": shape},
                                                     {"class": class_num}]
            fun_test.debug("Disabling TX pfc on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_tx_disable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Disable TX pfc on %d" % port_num)
            priority_flow_control_tx_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return priority_flow_control_tx_disabled

    def set_priority_flow_control_quanta(self, port_num, quanta, class_num, shape=0):
        result = False
        try:
            priority_flow_control_quanta_args = ['pfcqset', {"portnum": port_num, "shape": shape},
                                                 {"quanta": quanta, "class": class_num}]
            fun_test.debug("Setting pfc quanta %d on port %d" % (quanta, port_num))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_quanta_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Set pfc quanta %d on port %d" % (quanta, port_num))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_priority_flow_control_quanta(self, port_num, shape=0):
        quanta_value = None
        try:
            priority_flow_control_quanta_args = ['pfcqget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Getting pfc quanta on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_quanta_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Get pfc on port %d" % port_num)
            fun_test.debug("pfc Quanta on port %d: %d" % (port_num, json_cmd_result['data']))
            quanta_value = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return quanta_value

    def set_priority_flow_control_threshold(self, port_num, threshold, class_num, shape=0):
        result = False
        try:
            priority_flow_control_threshold_args = ['pfctset', {"portnum": port_num, "shape": shape},
                                                    {'threshold': threshold, "class": class_num}]
            fun_test.debug("Setting pfc threshold %d on port %d" % (threshold, port_num))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_threshold_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Set pfc threshold %d on port %d" % (threshold, port_num))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_priority_flow_control_threshold(self, port_num, shape=0):
        threshold_value = None
        try:
            priority_flow_control_threshold_args = ['pfctget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Getting pfc threshold on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=priority_flow_control_threshold_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Get pfc on port %d" % port_num)
            fun_test.debug("Link Pause threshold on port %d: %d" % (port_num, json_cmd_result['data']))
            threshold_value = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return threshold_value

    def enable_ptp_peer_delay(self, port_num, shape=0):
        ptp_peer_delay_enabled = False
        try:
            ptp_peer_delay_enable_args = ['ptppeerdelayena', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enabling PTP peer delay on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_peer_delay_enable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Enable PTP peer delay on %d" % port_num)
            ptp_peer_delay_enabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return ptp_peer_delay_enabled

    def disable_ptp_peer_delay(self, port_num, shape=0):
        ptp_peer_delay_disabled = False
        try:
            ptp_peer_delay_disable_args = ['ptppeerdelaydis', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Disabling PTP peer delay on port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_peer_delay_disable_args,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Disable PTP peer delay on %d" % port_num)
            ptp_peer_delay_disabled = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return ptp_peer_delay_disabled

    def set_ptp_peer_delay(self, port_num, delay, shape=0):
        result = False
        try:
            ptp_peer_delay_args = ['ptppeerdelayset', {"portnum": port_num, "shape": shape}, {"delay": delay}]
            fun_test.debug("Setting PTP peer delay %d on port %d" % (delay, port_num))
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_peer_delay_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Set PTP peer delay %d on port %d" % (delay, port_num))
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_ptp_peer_delay(self, port_num, shape=0):
        delay_value = None
        try:
            ptp_peer_delay_args = ['ptppeerdelayget', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Getting PTP peer delay on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_peer_delay_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'],
                                   message="Get PTP peer delay on port %d" % port_num)
            fun_test.debug("PTP peer delay on port %d: %d" % (port_num, json_cmd_result['data']))
            delay_value = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return delay_value
    
    def set_filter_runt(self, port_num, buffer_64=0, runt_err_en=1, en_delete=0, shape=0):
        result = False
        try:
            filter_runt_args = ['runtfilterset', {"portnum": port_num, "shape": shape}, {"buffer_64": buffer_64,
                                                                                         "runt_err_en": runt_err_en,
                                                                                         "en_delete": en_delete}]
            fun_test.debug("Enable runt filter on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=filter_runt_args, 
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], 
                                   message="Enable runt filter on port %d" % port_num)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
    
    def enable_ptp_first_step(self, port_num, shape=0):
        result = False
        try:
            ptp_first_step_args = ['ptp1stepena', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Enable PTP 1 step on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_first_step_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], 
                                   message="Enable PTP 1 step on port %d" % port_num)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
    
    def disable_ptp_first_step(self, port_num, shape=0):
        result = False
        try:
            ptp_first_step_args = ['ptp1stepdis', {"portnum": port_num, "shape": shape}]
            fun_test.debug("disable PTP 1 step on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=ptp_first_step_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], 
                                   message="disable PTP 1 step on port %d" % port_num)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
    
    def dump_runt_filter(self, port_num, shape=0):
        result = None
        try:
            dump_runt_filter_args = ['runtfilterdump', {"portnum": port_num, "shape": shape}]
            fun_test.debug("Dump runt filter on port %d" % port_num)
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PORT, data=dump_runt_filter_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], 
                                   message="Dump runt filter on port %d" % port_num)
            # TODO: See the output of this cmd on palladium and modify the lib accordingly
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
    
    def set_qos_egress_buffer_pool(self, sf_thr=None, sx_thr=None, dx_thr=None, df_thr=None, fcp_thr=None,
                                   nonfcp_thr=None, sample_copy_thr=0, sf_xoff_thr=0, fcp_xoff_thr=0,
                                   nonfcp_xoff_thr=0, mode='nu'):
        result = False
        try:
            egress_buffer_pool = self.get_qos_egress_buffer_pool(mode=mode)
            fun_test.simple_assert(egress_buffer_pool, "Get Existing settings")
            if sf_thr:
                egress_buffer_pool["sf_thr"] = sf_thr
            if sx_thr:
                egress_buffer_pool["sx_thr"] = sx_thr
            if dx_thr:
                egress_buffer_pool["dx_thr"] = dx_thr
            if df_thr:
                egress_buffer_pool["df_thr"] = df_thr
            if fcp_thr:
                egress_buffer_pool["fcp_thr"] = fcp_thr
            if nonfcp_thr:
                egress_buffer_pool["nonfcp_thr"] = nonfcp_thr
            if sample_copy_thr:
                egress_buffer_pool["sample_copy_thr"] = sample_copy_thr
            if sf_xoff_thr:
                egress_buffer_pool["sf_xoff_thr"] = sf_xoff_thr
            if fcp_xoff_thr:
                egress_buffer_pool["fcp_xoff_thr"] = fcp_xoff_thr
            if nonfcp_xoff_thr:
                egress_buffer_pool["nonfcp_xoff_thr"] = nonfcp_xoff_thr
            egress_buffer_pool_args = ['set', 'egress_buffer_pool', egress_buffer_pool]
            if not mode == 'nu':
                egress_buffer_pool_args.insert(1, mode)
            fun_test.debug("Setting QOS egress buffer pool")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_buffer_pool_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS egress buffer pool")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_egress_buffer_pool(self, mode='nu'):
        egress_buffer_pool_dict = None
        try:
            egress_buffer_pool_args = ['get', 'egress_buffer_pool']
            if not mode == 'nu':
                egress_buffer_pool_args.insert(1, mode)
            fun_test.debug("Getting QOS egress buffer pool")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_buffer_pool_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS egress buffer pool")
            fun_test.debug(json_cmd_result['data'])
            egress_buffer_pool_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return egress_buffer_pool_dict

    def set_qos_egress_port_buffer(self, port_num, min_threshold=None, shared_threshold=None):
        result = False
        try:
            input_dict = {"port": port_num}
            if min_threshold:
                input_dict["min_thr"] = min_threshold
            if shared_threshold:
                input_dict["shared_thr"] = shared_threshold
            egress_port_bufffer_args = ['set', 'egress_port_buffer', input_dict]
            fun_test.debug("Setting QOS egress port buffer")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_port_bufffer_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS egress port buffer")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_egress_port_buffer(self, port_num):
        egress_port_buffer_dict = None
        try:
            egress_port_buffer_args = ['get', 'egress_port_buffer', {"port": port_num}]
            fun_test.debug("Getting QOS egress port buffer")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_port_buffer_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS egress port buffer")
            fun_test.debug(json_cmd_result['data'])
            egress_port_buffer_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return egress_port_buffer_dict

    def set_qos_egress_queue_buffer(self, port_num, queue_num, min_threshold=None, static_shared_threshold_green=None,
                                    dynamic_enable=None, shared_threshold_alpha=None,
                                    shared_threshold_offset_yellow=None, shared_threshold_offset_red=None):
        result = False
        try:
            input_dict = {"port": port_num, "queue": queue_num}
            if min_threshold:
                input_dict["min_thr"] = min_threshold
            if static_shared_threshold_green:
                input_dict["static_shared_thr_green"] = static_shared_threshold_green
            if dynamic_enable:
                input_dict["dynamic_enable"] = dynamic_enable
            if shared_threshold_alpha:
                input_dict["shared_thr_alpha"] = shared_threshold_alpha
            if shared_threshold_offset_yellow:
                input_dict["shared_thr_offset_yellow"] = shared_threshold_offset_yellow
            if shared_threshold_offset_red:
                input_dict["shared_threshold_offset_red"] = shared_threshold_offset_red

            egress_queue_buffer_args = ['set', 'egress_queue_buffer', input_dict]
            fun_test.debug("Setting QOS egress queue buffer")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_queue_buffer_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS egress queue buffer")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_egress_queue_buffer(self, port_num, queue_num):
        egress_queue_buffer_dict = None
        try:
            egress_queue_buffer_args = ['get', 'egress_queue_buffer', {"port": port_num, "queue": queue_num}]
            fun_test.debug("Getting QOS egress queue buffer")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=egress_queue_buffer_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS egress queue buffer")
            fun_test.debug(json_cmd_result['data'])
            egress_queue_buffer_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return egress_queue_buffer_dict

    def set_qos_ingress_priority_group(self, port_num, priority_group_num, min_threshold=None,
                                       shared_threshold=None, headroom_threshold=None, xoff_enable=None,
                                       shared_xon_threshold=None, hnu=False):
        result = False
        try:
            input_dict = {"port": port_num, "pg": priority_group_num}
            if min_threshold:
                input_dict["min_thr"] = min_threshold
            if shared_threshold:
                input_dict["shared_thr"] = shared_threshold
            if headroom_threshold:
                input_dict["headroom_thr"] = headroom_threshold
            if xoff_enable:
                input_dict["xoff_enable"] = xoff_enable
            if shared_xon_threshold:
                input_dict["shared_xon_threshold"] = shared_xon_threshold

            ingress_priority_group_args = ['set', 'ingress_priority_group', input_dict]
            if hnu:
                ingress_priority_group_args = ['set', 'hnu', 'ingress_priority_group', input_dict]
            fun_test.debug("Setting QOS ingress priority group")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ingress_priority_group_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set ingress priority group")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_ingress_priority_group(self, port_num, priority_group_num):
        ingress_priority_group_dict = None
        try:
            ingress_priority_group_args = ['get', 'ingress_priority_group',
                                           {"port": port_num, "pg": priority_group_num}]
            fun_test.debug("Getting QOS ingress priority group")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ingress_priority_group_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS ingress priority group")
            fun_test.debug(json_cmd_result['data'])
            ingress_priority_group_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return ingress_priority_group_dict

    def set_qos_priority_to_pg_map(self, port_num, map_list):
        """
        QOS priority to pg map
        :param port_num: FPG port num
        :param map_list: list of N values where N is the number of priorities N = 16 for FPG ports and N = 8 for EPG ports
        :return: bool
        """
        result = False
        try:
            priority_to_pg_map_args = ['set', 'priority_to_pg_map', {"port": port_num, "map": map_list}]
            fun_test.debug("Setting QOS priority to pg map")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=priority_to_pg_map_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set priority to pg map")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_priority_to_pg_map(self, port_num):
        priority_to_pg_map_dict = None
        try:
            priority_to_pg_map_args = ['get', 'priority_to_pg_map', {"port": port_num}]
            fun_test.debug("Getting QOS priority to pg map")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=priority_to_pg_map_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS priority to pg map")
            fun_test.debug(json_cmd_result['data'])
            priority_to_pg_map_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return priority_to_pg_map_dict

    def set_qos_queue_to_priority_map(self, port_num, map_list):
        """
        QOS queue to priority map
        :param port_num: FPG port num
        :param map_list: list of N values where N is the number of priorities N = 16 for FPG ports and N = 8 for EPG ports
        :return: bool
        """
        result = False
        try:
            priority_to_pg_map_args = ['set', 'queue_to_priority_map', {"port": port_num, "map": map_list}]
            fun_test.debug("Setting QOS priority to pg map")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=priority_to_pg_map_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set priority to pg map")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_queue_to_priority_map(self, port_num):
        priority_to_pg_map_dict = None
        try:
            priority_to_pg_map_args = ['get', 'queue_to_priority_map', {"port": port_num}]
            fun_test.debug("Getting QOS priority to pg map")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=priority_to_pg_map_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS priority to pg map")
            fun_test.debug(json_cmd_result['data'])
            priority_to_pg_map_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return priority_to_pg_map_dict

    def enable_qos_pfc(self, hnu=False):
        result = False
        try:
            enable_pfc_args = ['set', 'pfc', {"enable": 1}]
            if hnu:
                enable_pfc_args = ['set', 'hnu', 'pfc', {"enable": 1}]
            fun_test.debug("Enable QOS priority flow control")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=enable_pfc_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Enable QOS priority flow control")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disable_qos_pfc(self, hnu=False):
        result = False
        try:
            disable_pfc_args = ['set', 'pfc', {"enable": 0}]
            if hnu:
                disable_pfc_args = ['set', 'hnu', 'pfc', {"enable": 0}]
            fun_test.debug("Disable QOS priority flow control")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=disable_pfc_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Disable QOS priority flow control")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_pfc_status(self):
        status = None
        try:
            pfc_args = ['get', 'pfc']
            fun_test.debug("Getting QOS priority flow control status")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=pfc_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS priority flow control status")
            fun_test.debug(json_cmd_result['data'])
            result = json_cmd_result['data']
            if result['enable'] == 0:
                status = False
            else:
                status = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return status

    def set_qos_wred_queue_config(self, port_num, queue_num, wred_enable=None, wred_weight=None, wred_prof_num=None,
                                  enable_ecn=None, ecn_profile_num=None):
        result = False
        try:
            input_dict = {"port": port_num, "queue": queue_num}
            if wred_enable:
                input_dict["wred_en"] = wred_enable
            if wred_weight:
                input_dict["wred_weight"] = wred_weight
            if wred_prof_num:
                input_dict["wred_prof_num"] = wred_prof_num
            if enable_ecn:
                input_dict["ecn_en"] = enable_ecn
            if ecn_profile_num:
                input_dict["ecn_profile_num"] = ecn_profile_num

            wred_queue_config_args = ['set', 'wred_queue_config', input_dict]
            fun_test.debug("Setting QOS WRED queue config")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_queue_config_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS WRED queue config")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_wred_queue_config(self, port_num, queue_num):
        wred_queue_config_dict = None
        try:
            wred_queue_config_args = ['get', 'wred_queue_config', {"port": port_num, "queue": queue_num}]
            fun_test.debug("Getting QOS WRED queue config")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_queue_config_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS WRED queue config")
            fun_test.debug(json_cmd_result['data'])
            wred_queue_config_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return wred_queue_config_dict

    def set_qos_wred_profile(self, prof_num, min_threshold=None, max_threshold=None, wred_prob_index=None):
        result = False
        try:
            input_dict = {"prof_num": prof_num}
            if min_threshold:
                input_dict["min_thr"] = min_threshold
            if max_threshold:
                input_dict["max_thr"] = max_threshold
            if wred_prob_index:
                input_dict["wred_prob_index"] = wred_prob_index

            wred_profile_args = ['set', 'wred_profile', input_dict]
            fun_test.debug("Setting QOS WRED profile")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_profile_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS WRED profile")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_wred_profile(self, prof_num):
        wred_profile_dict = None
        try:
            wred_profile_args = ['get', 'wred_profile', {"prof_num": prof_num}]
            fun_test.debug("Getting QOS WRED profile")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_profile_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS WRED profile")
            fun_test.debug(json_cmd_result['data'])
            wred_profile_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return wred_profile_dict

    def set_qos_wred_probability(self, prob_index, probability):
        result = False
        try:
            wred_prob_args = ['set', 'wred_prob', {"prob_idx": prob_index, "prob": probability}]
            fun_test.debug("Setting QOS WRED probability")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_prob_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS WRED probability")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_wred_probability(self, prob_index):
        prob_value = None
        try:
            wred_prob_args = ['get', 'wred_prob', {"prob_idx": prob_index}]
            fun_test.debug("Getting QOS WRED probability")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=wred_prob_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS WRED probability")
            fun_test.debug(json_cmd_result['data'])
            prob_value = json_cmd_result['data']['prob']
        except Exception as ex:
            fun_test.critical(str(ex))
        return prob_value

    def set_qos_ecn_profile(self, prof_num, min_threshold=None, max_threshold=None, ecn_prob_index=None):
        result = False
        try:
            input_dict = {"prof_num": prof_num}
            if min_threshold:
                input_dict["min_thr"] = min_threshold
            if max_threshold:
                input_dict["max_thr"] = max_threshold
            if ecn_prob_index:
                input_dict["ecn_prob_index"] = ecn_prob_index

            ecn_profile_args = ['set', 'ecn_profile', input_dict]
            fun_test.debug("Setting QOS ECN profile")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ecn_profile_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS ECN profile")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_ecn_profile(self, prof_num):
        ecn_profile_dict = None
        try:
            ecn_profile_args = ['get', 'ecn_profile', {"prof_num": prof_num}]
            fun_test.debug("Getting QOS ECN profile")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ecn_profile_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS ECN profile")
            fun_test.debug(json_cmd_result['data'])
            ecn_profile_dict = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return ecn_profile_dict

    def set_qos_ecn_probability(self, prob_index, probability):
        result = False
        try:
            ecn_prob_args = ['set', 'ecn_prob', {"prob_idx": prob_index, "prob": probability}]
            fun_test.debug("Setting QOS ECN probability")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ecn_prob_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS ECN probability")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_ecn_probability(self, prob_index):
        prob_value = None
        try:
            ecn_prob_args = ['get', 'ecn_prob', {"prob_idx": prob_index}]
            fun_test.debug("Getting QOS ECN probability")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=ecn_prob_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS ECN probability")
            fun_test.debug(json_cmd_result['data'])
            prob_value = json_cmd_result['data']['prob']
        except Exception as ex:
            fun_test.critical(str(ex))
        return prob_value

    def set_qos_scheduler_config(self, port_num, queue_num, scheduler_type=SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                 weight=None, shaper_enable=None,
                                 min_rate=None, max_rate=None, strict_priority_enable=False, extra_bandwidth=None):
        result = False
        strict_priority_enable_value = 0
        if strict_priority_enable:
            strict_priority_enable_value = 1
        try:
            input_dict = {"port": port_num, "queue": queue_num}
            if scheduler_type == self.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN:
                if not weight:
                    raise FunTestLibException("Please provide weight for weighted round robin scheduler")
                input_dict["weight"] = weight
            elif scheduler_type == self.SCHEDULER_TYPE_SHAPER:
                input_dict["shaper_enable"] = shaper_enable
                input_dict["min_rate"] = min_rate
                input_dict["max_rate"] = max_rate
            elif scheduler_type == self.SCHEDULER_TYPE_STRICT_PRIORITY:
                input_dict["strict_priority_enable"] = strict_priority_enable_value
                input_dict["extra_bandwidth"] = extra_bandwidth

            scheduler_config_args = ['set', 'scheduler_config %s' % scheduler_type, input_dict]
            fun_test.debug("Setting QOS Scheduler Config")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=scheduler_config_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Set QOS Scheduler Config")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_qos_port_scheduler_config(self, port_num, queue_num):
        scheduler_config = None
        try:
            scheduler_config_args = ['get', 'scheduler_config', {"port": port_num, "queue": queue_num}]
            fun_test.debug("Getting QOS Scheduler Config")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_QOS, data=scheduler_config_args,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Get QOS Scheduler Config")
            fun_test.debug(json_cmd_result['data'])
            scheduler_config = json_cmd_result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return scheduler_config

    def peek_fpg_port_stats(self, port_num, hnu=False):
        stats = None
        try:
            type = 'nu'
            if hnu:
                type = 'hnu'
            stats_cmd = "stats/fpg/%s/port/[%d]" % (type, port_num)
            fun_test.debug("Getting FPG stats for port %d" % port_num)
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get FPG stats for port %d" % port_num)
            fun_test.debug("FPG port %d stats: %s" % (port_num, result['data']))
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_psw_port_stats(self, port_num, queue_num=None, hnu=False):
        stats = None
        try:
            max_retry = 3
            current_retry = 0
            sleep_duration = 2
            type = 'nu'
            if hnu:
                type = 'hnu'
                sleep_duration = 50
            if queue_num:
                stats_cmd = "stats/psw/%s/port/[%d]/q_%s" % (type, port_num, queue_num)
                fun_test.debug("Getting PSW stats for port %d for queue %s" % (port_num, queue_num))
            else:
                stats_cmd = "stats/psw/%s/port/[%d]" % (type, port_num)
                fun_test.debug("Getting PSW stats for port %d" % port_num)
            while current_retry < max_retry:
                result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION,
                                           sleep_duration=sleep_duration, chunk=8192)
                fun_test.simple_assert(expression=result['status'], message="Get PSW stats for port %d" %
                                                                            (port_num))
                fun_test.debug("PSW port %d stats: %s" % (port_num, result['data']))
                if isinstance(result['data'], dict):
                    break
                self.disconnect()
                fun_test.sleep("Before reconnecting", seconds=3)
                current_retry += 1
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_psw_global_stats(self, hnu=False):
        stats = None
        try:
            stats_cmd = "stats/psw/nu"
            if hnu:
                stats_cmd = "stats/psw/hnu"
            fun_test.debug("Getting PSW global stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get PSW global stats")
            fun_test.debug("PSW global stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_vp_packets(self):
        stats = None
        try:
            stats_cmd = "stats/vppkts"
            fun_test.debug("Getting VP packets stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get VP packets stats")
            fun_test.debug("VP packets stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_fcp_global_stats(self):
        stats = None
        try:
            stats_cmd = "stats/fcp/global"
            fun_test.debug("Getting FCP global stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get FCP global stats")
            fun_test.debug("FCP global stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_fcp_tunnel_stats(self, tunnel_id):
        stats = None
        try:
            stats_cmd = "stats/fcp/tunnel[%d]" % tunnel_id
            fun_test.debug("Getting FCP tunnel stats for tunnel %d" % tunnel_id)
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'],
                                   message="Get FCP tunnel stats for tunnel %d" % tunnel_id)
            fun_test.debug("FCP tunnel stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_wro_tunnel_stats(self, tunnel_id):
        stats = None
        try:
            stats_cmd = "stats/wro/tunnel[%d]" % tunnel_id
            fun_test.debug("Getting WRO tunnel stats for tunnel %d" % tunnel_id)
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'],
                                   message="Get WRO tunnel stats for tunnel %d" % tunnel_id)
            fun_test.debug("WRO tunnel stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_wro_global_stats(self):
        stats = None
        try:
            stats_cmd = "stats/wro/nu"
            fun_test.debug("Getting WRO global stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get WRO global stats")
            fun_test.debug("WRO global stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_erp_global_stats(self, hnu=False, flex=False):
        stats = None
        try:
            stats_cmd = "stats/erp/nu/global"
            if hnu:
                stats_cmd = "stats/erp/hnu/global"
            if flex:
                stats_cmd = "stats/erp/flex/global"
            fun_test.debug("Getting ERP global stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=stats_cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get ERP global stats")
            fun_test.debug("ERP global stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def configure_fcp_tunnel(self, q_id, secure_tunnel=None, remote_key_index=None, local_key_index=None, profile=None,
                             spray=None):
        result = False
        try:
            input_dict = {"qid": q_id}
            if secure_tunnel:
                input_dict["sec_tunnel"] = secure_tunnel
            if remote_key_index:
                input_dict["remote_key_index"] = remote_key_index
            if local_key_index:
                input_dict["local_key_index"] = local_key_index
            if profile:
                input_dict["profile"] = profile
            if spray:
                input_dict["spray"] = spray
            fcp_tunnel_cmd = "poke config/fcp/tunnel %s" % input_dict
            fun_test.debug("Configure FCP tunnel")
            json_cmd_result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=fcp_tunnel_cmd,
                                                command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=json_cmd_result['status'], message="Configure FCP tunnel")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def set_syslog_level(self, level=3):
        result = False
        try:
            cmd = ["params/syslog/level", level]
            fun_test.debug("Disabe syslogs on level %s" % level)
            result = self.json_execute(verb=self.VERB_TYPE_POKE, data=cmd,
                                       command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(result['status'], message="Disable syslog")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def peek_bam_stats(self):
        stats = None
        try:
            cmd = "stats/bam"
            fun_test.debug("Getting bam stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get bam stats")
            fun_test.debug("BAM stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_parser_stats(self, hnu=False):
        stats = None
        try:
            cmd = "stats/prsr/nu"
            if hnu:
                cmd = "stats/prsr/hnu"
            fun_test.debug("Getting parser stats")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get parser stats")
            fun_test.debug("parser stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_per_vppkts_stats(self):
        stats = None
        try:
            cmd = "stats/pervppkts"
            fun_test.debug("Getting vp per pkt")
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=cmd, command_duration=self.COMMAND_DURATION, sleep_duration=20)
            fun_test.simple_assert(expression=result['status'], message="Get vp per pkts stats")
            fun_test.debug("Per vppkts stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def peek_meter_stats_by_id(self, meter_id, bank=0, erp=False):
        stats = None
        try:
            if erp:
                cmd = "stats/meter/erp/bank/%d/meter[%d]" % (bank, meter_id)
            else:
                cmd = "stats/meter/nu/bank/%d/meter[%d]" % (bank, meter_id)
            fun_test.debug("Getting meter stats for id %d" % meter_id)
            result = self.json_execute(verb=self.VERB_TYPE_PEEK, data=cmd, command_duration=self.COMMAND_DURATION)
            fun_test.simple_assert(expression=result['status'], message="Get meter stats for meter id %d" % meter_id)
            fun_test.debug("meter stats: %s" % result['data'])
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats

    def set_nu_test_op(self, rule, lso):
        lso_set = False
        try:
            cmd = ["old", "add", "rule", rule, "lso", lso]
            fun_test.debug("Setting NU test op for rule %d with lso %d" % (rule, lso))
            result = self.json_execute(verb="nu_test_op", data=cmd)
            fun_test.simple_assert(expression=result['status'],
                                   message="Setting NU test op for rule %d with lso %d" % (rule, lso))
            lso_set = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return lso_set

    def delete_nu_test_op(self, rule):
        lso_set = False
        try:
            cmd = ["old", "delete", "rule", rule]
            fun_test.debug("Deleting nu test op rule %d" % rule)
            result = self.json_execute(verb="nu_test_op", data=cmd)
            fun_test.simple_assert(expression=result['status'],
                                   message="Deleting nu test op rule %d" % rule)
            lso_set = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return lso_set

    def _enable_sample_rule(self, *args):
        result = None
        try:
            result = self.json_execute(verb='sample', data=args[0])
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def add_ingress_sample_rule(self, id, fpg, dest, acl=None, flag_mask=None, hu=None, psw_drop=None, pps_en=None,
                                pps_interval=None, pps_burst=None, sampler_en=None, sampler_rate=None, sampler_run_sz=None,
                                first_cell_only=None):
        result = None
        try:
            cmd_arg_dict = {"id": id, "fpg": fpg, "mode": 0, "dest": dest}
            if acl:
                cmd_arg_dict['acl'] = acl
            if flag_mask:
                cmd_arg_dict['flag_mask'] = flag_mask
            if hu:
                cmd_arg_dict['hu'] = hu
            if psw_drop is not None:
                cmd_arg_dict['psw_drop'] = psw_drop
            if pps_en is not None:
                cmd_arg_dict['pps_interval'] = pps_interval
            if pps_burst:
                cmd_arg_dict['pps_burst'] = pps_burst
            if sampler_en is not None:
                cmd_arg_dict['sampler_en'] = sampler_en
            if sampler_rate:
                cmd_arg_dict['sampler_rate'] = sampler_rate
            if sampler_run_sz:
                cmd_arg_dict['sampler_run_sz'] = sampler_run_sz
            if first_cell_only is not None:
                cmd_arg_dict['first_cell_only'] = first_cell_only

            result = self._enable_sample_rule(cmd_arg_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def add_egress_sample_rule(self, id, fpg, dest, acl=None, flag_mask=None, hu=None, psw_drop=None, pps_en=None,
                               pps_interval=None, pps_burst=None, sampler_en=None, sampler_rate=None,
                               sampler_run_sz=None, first_cell_only=None):
        result = None
        try:
            cmd_arg_dict = {"id": id, "fpg": fpg, "mode": 1, "dest": dest}
            if acl:
                cmd_arg_dict['acl'] = acl
            if flag_mask:
                cmd_arg_dict['flag_mask'] = flag_mask
            if hu:
                cmd_arg_dict['hu'] = hu
            if psw_drop is not None:
                cmd_arg_dict['psw_drop'] = psw_drop
            if pps_en is not None:
                cmd_arg_dict['pps_interval'] = pps_interval
            if pps_burst:
                cmd_arg_dict['pps_burst'] = pps_burst
            if sampler_en is not None:
                cmd_arg_dict['sampler_en'] = sampler_en
            if sampler_rate:
                cmd_arg_dict['sampler_rate'] = sampler_rate
            if sampler_run_sz:
                cmd_arg_dict['sampler_run_sz'] = sampler_run_sz
            if first_cell_only is not None:
                cmd_arg_dict['first_cell_only'] = first_cell_only

            result = self._enable_sample_rule(cmd_arg_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def disable_sample_rule(self, id, fpg, dest, acl=None, flag_mask=None, hu=None, psw_drop=None, pps_en=None,
                            pps_interval=None, pps_burst=None, sampler_en=None, sampler_rate=None,
                            sampler_run_sz=None, first_cell_only=None):
        result = None
        try:
            cmd_arg_dict = {"id": id, "fpg": fpg, "mode": 2, "dest": dest}
            if acl:
                cmd_arg_dict['acl'] = acl
            if flag_mask:
                cmd_arg_dict['flag_mask'] = flag_mask
            if hu:
                cmd_arg_dict['hu'] = hu
            if psw_drop is not None:
                cmd_arg_dict['psw_drop'] = psw_drop
            if pps_en is not None:
                cmd_arg_dict['pps_interval'] = pps_interval
            if pps_burst:
                cmd_arg_dict['pps_burst'] = pps_burst
            if sampler_en is not None:
                cmd_arg_dict['sampler_en'] = sampler_en
            if sampler_rate:
                cmd_arg_dict['sampler_rate'] = sampler_rate
            if sampler_run_sz:
                cmd_arg_dict['sampler_run_sz'] = sampler_run_sz
            if first_cell_only is not None:
                cmd_arg_dict['first_cell_only'] = first_cell_only

            result = self._enable_sample_rule(cmd_arg_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def show_sample_stats(self):
        stats = None
        try:
            result = self.json_execute(verb='sample', data=['show'], command_duration=5)
            fun_test.simple_assert(result['status'], "Stats fetched")
            stats = result['data']
        except Exception as ex:
            fun_test.critical(str(ex))
        return stats
