from lib.system.fun_test import *
from lib.utilities.setup_nmtf import *


class SnapshotHelper():

    def __init__(self, dpc_proxy_ip, dpc_proxy_port=42221):
        self.dpc_client_obj = None
        self.snapshot_obj = None
        self.dpc_proxy_ip = dpc_proxy_ip
        self.dpc_proxy_port = dpc_proxy_port
        self.ws = fun_test.get_environment_variable(variable='WORKSPACE')
        if not self.ws:
            os.environ['WORKSPACE'] = SYSTEM_TMP_DIR

    def setup_snapshot(self, smac=None, psw_stream=None, stream=None, unit=None, instance=None):
        result = False
        try:
            from dpcsh.dpcsh_client import DpcshClient
            from dpcsh.snapshot import Snapshot

            if not self.dpc_client_obj:
                self.dpc_client_obj = DpcshClient(target_ip=self.dpc_proxy_ip, target_port=self.dpc_proxy_port,
                                                  verbose=False)
            if not self.snapshot_obj:
                self.snapshot_obj = Snapshot(self.dpc_client_obj)

            self.snapshot_obj.do_filter_reset()
            if smac is not None:
                self.snapshot_obj.do_smac(smac)
            if psw_stream is not None:
                self.snapshot_obj.do_psw_stream(psw_stream)
            if stream is not None:
                self.snapshot_obj.do_stream(stream)
            if unit is not None:
                self.snapshot_obj.do_unit(unit)
            if instance is not None:
                self.snapshot_obj.do_instance(instance=instance)
            fun_test.log("Captured Filter: %s" % self.snapshot_obj.capture_filter)
            fun_test.log("Captured Filter ERP: %s" % self.snapshot_obj.capture_filter_erp)
            self.snapshot_obj.do_capture()
            result = True
        except ImportError as ex:
            fun_test.log("Exception: %s" % str(ex))
            fun_test.log("Installing nmtf....")
            fun_test.simple_assert(setup_nmtf(), "Setup nmtf")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def run_snapshot(self):
        if self.snapshot_obj:
            return self.snapshot_obj.do_analyze(return_dict=True)
        else:
            return None

    def exit_snapshot(self):
        if self.snapshot_obj:
            return self.snapshot_obj.do_exit()
        else:
            return None

    def get_snapshot_main_sfg(self, snapshot_output, prv=False, md=False, frv=False, psw_ctl=False):
        result = {}
        flag = False
        if prv:
            result['PRV'] = snapshot_output['Main SFG']['PRV']
            flag = True
        if md:
            result['MD'] = snapshot_output['Main SFG']['MD']
            flag = True
        if frv:
            result['FRV'] = snapshot_output['Main SFG']['FRV']
            flag = True
        if psw_ctl:
            result['PSW_CTL'] = snapshot_output['Main SFG']['PSW_CTL']
            flag = True
        if not flag:
            result = snapshot_output['Main SFG']
        return result

    def get_snapshot_meter_id(self, snapshot_output, egress=False, erp=False):
        result = None
        try:
            if erp:
                if egress:
                    result = snapshot_output['ERP SFG']['MD']['meter1']
                else:
                    result = snapshot_output['ERP SFG']['MD']['meter0']
            else:
                if egress:
                    result = snapshot_output['Main SFG']['MD']['meter1']
                else:
                    result = snapshot_output['Main SFG']['MD']['meter0']
        except Exception as ex:
            fun_test.critical("Exception : %s" % ex)
        return result

    def get_pkt_color_from_snapshot(self, snapshot_output, erp=False):
        result = None
        try:
            if erp:
                result = snapshot_output['ERP SFG']['MD']['pkt_color']
            else:
                result = snapshot_output['Main SFG']['MD']['pkt_color']
        except Exception as ex:
            fun_test.critical("Exception : %s" % ex)
        return result

    def get_log_from_snapshot(self, snapshot_output, erp=False):
        result = None
        try:
            if erp:
                result = snapshot_output['Main SFG']['MD']['acl_log']
            else:
                result = snapshot_output['Main SFG']['MD']['acl_log']
        except Exception as ex:
            fun_test.critical("Exception : %s" % ex)
        return result

    def get_snapshot_acl_label(self, snapshot_output, erp=False):
        result = None
        try:
            if erp:
                result = snapshot_output['ERP SFG']['MD']['port_acl_label']
            else:
                result = snapshot_output['Main SFG']['MD']['port_acl_label']
        except Exception as ex:
            fun_test.critical("Exception : %s" % ex)
        return result
