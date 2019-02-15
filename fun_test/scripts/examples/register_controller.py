from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
import time

class RegisterController(DpcshClient):
    VERB_TYPE_PEEK = 'peek'
    VERB_TYPE_POKE = 'poke'
    VERB_TYPE_CSR = 'csr'
    hsu_pwp_core0_csr_test_in = "hsu_pwp_core0_csr_test_in"
    hsu_pwp_core0_csr_tl_pm_event0 = "hsu_pwp_core0_csr_tl_pm_event0"
    hsu_pwp_core0_csr_tl_pm_event1 = "hsu_pwp_core0_csr_tl_pm_event1"
    hsu_pwp_core0_csr_tl_pm_event2 = "hsu_pwp_core0_csr_tl_pm_event2"
    hsu_pwp_core0_csr_tl_pm_event3 = "hsu_pwp_core0_csr_tl_pm_event3"
    hsu_pwp_core0_csr_k_pexconf = "hsu_pwp_core0_csr_k_pexconf"
    hsu_pwp_core0_csr_apb = "hsu_pwp_core0_csr_apb"
    hsu_pwp_core0_csr_test_outl = "hsu_pwp_core0_csr_test_outl"


    def __init__(self, dpc_server_ip, dpc_server_port=40221, verbose=True):
        super(RegisterController, self).__init__(mode="register", target_ip=dpc_server_ip, target_port=dpc_server_port,
                                                verbose=verbose)
        self.server_ip = dpc_server_ip
        self.server_port = dpc_server_port
        self.verbose = verbose
        self.command(command="enable_counters", legacy=True)
        time.sleep(1)

    def peek_csr(self, args):
        result = None
        try:
            cmd = self.VERB_TYPE_CSR + ' ' + self.VERB_TYPE_PEEK
            cmd = cmd + " %s" % args
            fun_test.log("Command formed is %s" % cmd)
            result = self.command(cmd, legacy=True)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def form_args(self, register_name, rinst, ring="hsu", field=None):
        args = "{name: %s, ring:%s, rinst:%s," % (register_name, ring, rinst)
        if field:
            args = args + " field:%s" % field
        args = args + "}"
        return args

    def peek_register(self, register_name, rinst, ring="hsu", field=None):
        args = self.form_args(register_name,rinst,ring, field)
        fun_test.log("\n############################")
        output = self.peek_csr(args)
        if field:
            fun_test.log("Output seen for register '%s' with field '%s' is '%s'" % (register_name, field, output['data']))
        else:
            fun_test.log("Output seen for register '%s' is '%s'" % (register_name, output['data']))
