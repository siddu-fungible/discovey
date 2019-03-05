from dpcsh.dpcsh_client import DpcshClient
from dpcsh.snapshot import Snapshot
from lib.system.fun_test import *


def setup_snapshot(smac=None, psw_stream=None, stream=None, unit=None, dpc_tcp_proxy_ip='127.0.0.1', dpc_tcp_proxy_port=40221):
    global dpc_client_obj
    global snapshot_obj
    dpc_client_obj = None
    snapshot_obj = None

    if dpc_client_obj is None:
        dpc_client_obj = DpcshClient(target_ip=dpc_tcp_proxy_ip, target_port=dpc_tcp_proxy_port,
                                     verbose=False)
    if snapshot_obj is None:
        snapshot_obj = Snapshot(dpc_client_obj)

    snapshot_obj.do_filter_reset()
    if smac is not None:
        snapshot_obj.do_smac(smac)
    if psw_stream is not None:
        snapshot_obj.do_psw_stream(psw_stream)
    if stream is not None:
        snapshot_obj.do_stream(stream)
    if unit is not None:
        snapshot_obj.do_unit(unit)
    snapshot_obj.do_capture()
    return


def run_snapshot():
    global snapshot_obj
    if snapshot_obj:
        return snapshot_obj.do_analyze(return_dict=True)
    else:
        return None


def get_snapshot_main_sfg(snapshot_output, prv=False, md=False, frv=False, psw_ctl=False):
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


def get_snapshot_meter_id(snapshot_output, egress=False, erp=False):
    result = 0
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


def get_snapshot_acl_label(snapshot_output, erp=False):
    result = 0
    try:
        if erp:
            result = snapshot_output['ERP SFG']['MD']['port_acl_label']
        else:
            result = snapshot_output['Main SFG']['MD']['port_acl_label']
    except Exception as ex:
        fun_test.critical("Exception : %s" % ex)
    return result
