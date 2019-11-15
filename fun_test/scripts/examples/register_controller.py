from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
import time

hsu_pwp_core0_csr_test_outl_dict = {"LTSSM state": [96, 100], "Data link layer": [101], "TLP transmission": [102],
                     "DLLP Transmission": [103], "Low-Power state": [104, 107]}

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


    def __init__(self, dpc_server_ip, dpc_server_port=42221, verbose=True):
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

    def form_args(self, register_name, rinst, ring="hsu", field=None, inst=None, index=None):
        args = "{name: %s,ring:%s, rinst:%s" % (register_name, ring, rinst)
        if field is not None:
            args = args + ", field:%s" % field
        if inst is not None:
            args = args + ", inst:%s" % inst
        if index is not None:
            args = args + ", index:%s" % index
        args = args + "}"
        return args

    def peek_register(self, register_name, rinst, ring="hsu", field=None, inst=None, index=None):
        args = self.form_args(register_name, rinst, ring, field, inst, index)
        fun_test.log("\n############################")
        output = self.peek_csr(args)
        if field:
            fun_test.log("Output seen for register '%s' with field '%s' is '%s'" % (register_name, field, output['data']))
        else:
            fun_test.log("Output seen for register '%s' is '%s'" % (register_name, output['data']))
        if register_name == self.hsu_pwp_core0_csr_test_outl and rinst == 0 and field == "csr_test_outl":
            self.print_simplified_data(register_name, output['data'][2], hsu_pwp_core0_csr_test_outl_dict)
        if register_name == self.hsu_pwp_core0_csr_apb and (inst is not None) and (index is not None) and (int(output['data'][0]) != 0):
            self.print_hsu_pwp_core0_csr_apb_byte0(output['data'][0], rinst, inst, index)

    def findTwoscomplement(self,stri):
        n = len(stri)
        i = n - 1
        while (i >= 0):
            if (stri[i] == '1'):
                break
            i -= 1
        if (i == -1):
            return '1' + stri
        k = i - 1
        while (k >= 0):
            if (stri[k] == '1'):
                stri = list(stri)
                stri[k] = '0'
                stri = ''.join(stri)
            else:
                stri = list(stri)
                stri[k] = '1'
                stri = ''.join(stri)
            k -= 1
        return stri



    def _convert_decimal_to_binary(self, decimal, zfill_val):
        result = None
        try:
            if decimal<0:
                decimal = -decimal
                bin_d = bin(decimal)
                stri = str(bin_d)
                binary = self.findTwoscomplement(stri)
                binary = '0b'+binary
            else:
                binary = bin(decimal)

            to_add = zfill_val - len(binary)
            to_prepend = to_add + 2
            zeros = '0' * to_prepend
            result = binary.replace('0b', zeros)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def extract_value(self, output, start_index, end_index=None):
        if end_index:
            return output[start_index:end_index]
        else:
            return output[start_index]

    def print_simplified_data(self, register_name, decimal_data, display_bits_dict):
        if register_name == self.hsu_pwp_core0_csr_test_outl:
            zfill_val = 64
            binary_output = self._convert_decimal_to_binary(decimal_data, zfill_val=zfill_val)
            binary_output = binary_output[::-1]
            for key, val in display_bits_dict.iteritems():
                start_index = val[0] - zfill_val
                end_index = None
                if len(val) == 2:
                    start_index = val[0] - zfill_val
                    end_index = val[1] - zfill_val + 1
                binary_bits = self.extract_value(binary_output, start_index,end_index)
                fun_test.log("Output for %s in range %s in binary bits is %s" % (key, val[::-1], binary_bits[::-1]))

    def print_hsu_pwp_core0_csr_apb_byte0(self, decimal_data, rinst, inst, index):
        zfill_val = 64
        binary_output = self._convert_decimal_to_binary(decimal_data, zfill_val)
        byte0 = binary_output[56:]
        fun_test.log("Byte0 info for hsu_pwp_core0_csr_apb register with "
                     "rinst '%s' and inst '%s' and index '%s' is [7:0] '%s'" % (rinst, inst, index,
                                                                                byte0))
        fun_test.log("Value of D3 on state is '%s'" % byte0[6:])
