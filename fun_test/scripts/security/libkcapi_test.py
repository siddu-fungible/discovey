from lib.system.fun_test import *
from lib.templates.security.libkcapi_template import LibkcapiTemplate
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1


topology_dict = {
    "name": "Basic Security",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 1,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_NORMAL
        }

    }
}

libkcapi_template = ""
vector_path = "/test_vectors/kcapi_vectors.txt"


class LibkcapiScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and Allocate a QEMU instance
        2. Make the QEMU instance available for the testcase
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = self.topology
        host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        libkcapi_template = LibkcapiTemplate(host)
        file_path = fun_test.get_script_parent_directory() + vector_path
        input_dict = libkcapi_template.parse_input_libkcapi(file_path)
        fun_test.shared_variables["host"] = host
        fun_test.shared_variables["libkcapi_template"] = libkcapi_template
        fun_test.shared_variables["input_dict"] = input_dict
        setup_path = fun_test.get_script_parent_directory()+ "/lib_crypto/libkcapi"
        fun_test.test_assert(libkcapi_template.setup(setup_path), "libkcapi Setup complete")



    def cleanup(self):
        if self.topology:
            TopologyHelper(spec=self.topology).cleanup()
        pass


class LibkcapiTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Run gcm(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt gcm(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal
        
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_gcm(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_gcm(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_gcm_aes(LibkcapiTemplate.GCM_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                      enc_dict['key'], enc_dict['iv'], enc_dict['assosc_data'],
                                      enc_dict['tag_len'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "gcm(aes) encryption verified ")

        for dec_dict in dec_dicts:

            dec_output = (libkcapi_template.dec_gcm_aes(LibkcapiTemplate.GCM_AES, dec_dict['cipher_type'], dec_dict['cipher_text'],
                                      dec_dict['key'], dec_dict['iv'], dec_dict['assosc_data'],
                                      dec_dict['tag'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "gcm(aes) decryption verified ")


class LibkcapiTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Run ccm(aes) with libkcapi",
                              steps="""
        1. Decrypt ccm(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts =[]
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_ccm(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_ccm(aes)":
                dec_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_ccm_aes(LibkcapiTemplate.CCM_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                      enc_dict['nonce'], enc_dict['key'], enc_dict['assosc_data'],
                                      enc_dict['tag'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "ccm(aes) encryption verified ")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.dec_ccm_aes(LibkcapiTemplate.CCM_AES, dec_dict['cipher_type'], dec_dict['cipher_text'],
                                      dec_dict['nonce'], dec_dict['key'], dec_dict['assosc_data'],
                                      dec_dict['tag'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "ccm(aes) decryption verified ")



class LibkcapiTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Run ctr(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt gcm(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_ctr(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_ctr(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_ctr_aes(LibkcapiTemplate.CTR_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                              enc_dict['key'], enc_dict['iv'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "ctr(aes) encryption verified ")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.dec_ctr_aes(LibkcapiTemplate.CTR_AES, dec_dict['cipher_type'],
                                                        dec_dict['cipher_text'],
                                                        dec_dict['key'], dec_dict['iv'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "ctr(aes) decryption verified ")



class LibkcapiTestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Run ecb(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt gcm(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_ecb(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_ecb(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_ecb_aes(LibkcapiTemplate.ECB_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                              enc_dict['key'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "ecb(aes) encryption verified ")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.dec_ecb_aes(LibkcapiTemplate.ECB_AES, dec_dict['cipher_type'],
                                                        dec_dict['cipher_text'],
                                                        dec_dict['key'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "ecb(aes) decryption verified ")


class LibkcapiTestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Run xts(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt gcm(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_xts(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_xts(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_xts_aes(LibkcapiTemplate.XTS_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                              enc_dict['key'], enc_dict['iv'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "xts(aes) encryption verified ")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.dec_xts_aes(LibkcapiTemplate.XTS_AES, dec_dict['cipher_type'],
                                                        dec_dict['cipher_text'],
                                                        dec_dict['key'], dec_dict['iv'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "xts(aes) decryption verified ")


class LibkcapiTestCase6(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Run authenc with libkcapi",
                              steps="""
        1. Compute authenc with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        for dict in input_dict:
            if dict == "auth_enc":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.auth_enc(LibkcapiTemplate.AUTH_ENC, enc_dict['cipher_type'], enc_dict['plain_text'],
                                          enc_dict['key'], enc_dict['iv'], enc_dict['assosc_data'],
                                          enc_dict['tag_len'])).strip()

            fun_test.test_assert((enc_output == enc_dict['result']), "authenc verified ")


class LibkcapiTestCase7(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Run cbc(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt cbc(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = fun_test.shared_variables["input_dict"]
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_cbc(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_cbc(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.enc_cbc_aes(LibkcapiTemplate.CBC_AES, enc_dict['cipher_type'], enc_dict['plain_text'],
                                              enc_dict['key'], enc_dict['iv'])).strip()
            fun_test.test_assert((enc_output == enc_dict['result']), "cbc(aes) encryption verified ")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.dec_cbc_aes(LibkcapiTemplate.CBC_AES, dec_dict['cipher_type'],
                                                        dec_dict['cipher_text'],
                                                        dec_dict['key'], enc_dict['iv'])).strip()
            fun_test.test_assert((dec_output == dec_dict['result']), "cbc(aes) decryption verified ")


if __name__ == "__main__":
    libkcapi_script = LibkcapiScript()

#    libkcapi_script.add_test_case(LibkcapiTestCase1())
#    libkcapi_script.add_test_case(LibkcapiTestCase2())
#    libkcapi_script.add_test_case(LibkcapiTestCase3())
#    libkcapi_script.add_test_case(LibkcapiTestCase4())
#    libkcapi_script.add_test_case(LibkcapiTestCase5())
#    libkcapi_script.add_test_case(LibkcapiTestCase6())
    libkcapi_script.add_test_case(LibkcapiTestCase7())

    libkcapi_script.run()
