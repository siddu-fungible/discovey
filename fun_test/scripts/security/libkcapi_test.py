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
vector_path = "/test_vectors/NIST/DGST/SHA1.txt"
cbc_vector_path = "/test_vectors/NIST/CBC/cbctest.txt"


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
        # setup_path = fun_test.get_script_parent_directory()+ "/lib_crypto/libkcapi"
        # fun_test.test_assert(libkcapi_template.setup(setup_path), "libkcapi Setup complete")

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
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.GCM_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'], assoc_data=enc_dict['assosc_data'],
                                                       tag_len=enc_dict['tag_len'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "gcm(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.GCM_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], encrypt=False,
                                                       cipher_text=dec_dict['cipher_text'],
                                                       iv=dec_dict['iv'], assoc_data=dec_dict['assosc_data'],
                                                       tag=dec_dict['tag'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "gcm(aes) decryption verified")


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
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_ccm(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_ccm(aes)":
                dec_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CCM_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       nonce=enc_dict['nonce'], assoc_data=enc_dict['assosc_data'],
                                                       tag=enc_dict['tag'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "ccm(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CCM_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, nonce=dec_dict['nonce'],
                                                       assoc_data=dec_dict['assosc_data'],
                                                       tag=dec_dict['tag'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "ccm(aes) decryption verified")


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
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CTR_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "ctr(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CTR_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "ctr(aes) decryption verified")


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
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.ECB_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "ecb(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.ECB_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False)).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "ecb(aes) decryption verified")


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
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.XTS_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "xts(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.XTS_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "xts(aes) decryption verified")


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
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.AUTH_ENC, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'], assoc_data=enc_dict['assosc_data'],
                                                       tag_len=enc_dict['tag_len'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "authenc verified")


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
        file_path = fun_test.get_script_parent_directory() + cbc_vector_path
        input_dict = libkcapi_template.parse_input_libkcapi(file_path)
        enc_dicts = []
        dec_dicts = []
        for dict in input_dict:
            if dict == "enc_cbc(aes)":
                enc_dicts = input_dict[dict]
            elif dict == "dec_cbc(aes)":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CBC_AES, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "cbc(aes) encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.CBC_AES, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "cbc(aes) decryption verified")


class LibkcapiTestCase8(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Run SHA1 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
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
            if dict == "dgst_sha1":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA1, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA1 verified")


class LibkcapiTestCase9(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Run SHA224 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
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
            if dict == "dgst_sha224":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA224, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA224 verified")


class LibkcapiTestCase10(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Run SHA256 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
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
            if dict == "dgst_sha256":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA256, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA256 verified")


class LibkcapiTestCase11(FunTestCase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="Run SHA384 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
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
            if dict == "dgst_sha384":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA384, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA384 verified")


class LibkcapiTestCase12(FunTestCase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="Run SHA512 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
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
            if dict == "dgst_sha512":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA512, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA512 verified")


if __name__ == "__main__":
    libkcapi_script = LibkcapiScript()

    libkcapi_script.add_test_case(LibkcapiTestCase1())
    libkcapi_script.add_test_case(LibkcapiTestCase2())
    libkcapi_script.add_test_case(LibkcapiTestCase3())
    libkcapi_script.add_test_case(LibkcapiTestCase4())
    libkcapi_script.add_test_case(LibkcapiTestCase5())
    libkcapi_script.add_test_case(LibkcapiTestCase6())
    libkcapi_script.add_test_case(LibkcapiTestCase7())
    libkcapi_script.add_test_case(LibkcapiTestCase8())
    libkcapi_script.add_test_case(LibkcapiTestCase9())
    libkcapi_script.add_test_case(LibkcapiTestCase10())
    libkcapi_script.add_test_case(LibkcapiTestCase11())
    libkcapi_script.add_test_case(LibkcapiTestCase12())

    libkcapi_script.run()
