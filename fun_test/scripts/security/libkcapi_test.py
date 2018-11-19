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
                   "type": DutInterface.INTERFACE_TYPE_PCIE,
                   "vm_host_os": "fungible_yocto"
               }
           },
           "start_mode": F1.START_MODE_NORMAL
       }

   }
}

libkcapi_template = ""

vector_path = ""

cbc_vector_path = ["/test_vectors/nist/cbc/cbcvectors_1.txt", "/test_vectors/nist/cbc/cbcvectors_2.txt",
                   "/test_vectors/nist/cbc/cbcvectors_3.txt", "/test_vectors/nist/cbc/cbcvectors_4.txt",
                   "/test_vectors/nist/cbc/cbcvectors_5.txt", "/test_vectors/nist/cbc/cbcvectors_6.txt",
                   "/test_vectors/nist/cbc/cbcvectors_7.txt"]

ecb_vector_path = ["/test_vectors/nist/ecb/ecbvectors_1.txt", "/test_vectors/nist/ecb/ecbvectors_2.txt",
                   "/test_vectors/nist/ecb/ecbvectors_3.txt", "/test_vectors/nist/ecb/ecbvectors_4.txt",
                   "/test_vectors/nist/ecb/ecbvectors_5.txt", "/test_vectors/nist/ecb/ecbvectors_6.txt"]

xts_vector_path = ["/test_vectors/nist/xts/xtsvectors_128.txt", "/test_vectors/nist/xts/xtsvectors_256.txt"]


gcm_vector_path = ["/test_vectors/nist/gcm/gcmdecrypt128.txt", "/test_vectors/nist/gcm/gcmdecrypt192.txt",
                   "/test_vectors/nist/gcm/gcmdecrypt256.txt", "/test_vectors/nist/gcm/gcmencryptextiv128",
                   "/test_vectors/nist/gcm/gcmencryptextiv192", "/test_vectors/nist/gcm/gcmencryptextiv256"]

ccm_vector_path = ["/test_vectors/nist/ccm/ccm_vadt128.txt", "/test_vectors/nist/ccm/ccm_vadt192.txt",
                   "/test_vectors/nist/ccm/ccm_vadt256.txt", "/test_vectors/nist/ccm/ccm_dvpt128.txt",
                   "/test_vectors/nist/ccm/ccm_dvpt192.txt", "/test_vectors/nist/ccm/ccm_dvpt256.txt",
                   "/test_vectors/nist/ccm/ccm_vnt128.txt", "/test_vectors/nist/ccm/ccm_vnt192.txt",
                   "/test_vectors/nist/ccm/ccm_vnt256.txt", "/test_vectors/nist/ccm/ccm_vpt128.txt",
                   "/test_vectors/nist/ccm/ccm_vpt192.txt", "/test_vectors/nist/ccm/ccm_vpt256.txt",
                   "/test_vectors/nist/ccm/ccm_vtt128.txt", "/test_vectors/nist/ccm/ccm_vtt192.txt",
                   "/test_vectors/nist/ccm/ccm_vtt256.txt"]

sha1_vector_path = "/test_vectors/nist/dgst/sha1.txt"
sha224_vector_path = "/test_vectors/nist/dgst/sha224.txt"
sha256_vector_path = "/test_vectors/nist/dgst/sha256.txt"
sha384_vector_path = "/test_vectors/nist/dgst/sha384.txt"
sha512_vector_path = "/test_vectors/nist/dgst/sha512.txt"
sha512_224_vector_path = "/test_vectors/nist/dgst/sha512_224.txt"
sha512_256_vector_path = "/test_vectors/nist/dgst/sha512_256.txt"
sha3_224_vector_path = "/test_vectors/nist/dgst/sha3_224.txt"
sha3_256_vector_path = "/test_vectors/nist/dgst/sha3_256.txt"
sha3_384_vector_path = "/test_vectors/nist/dgst/sha3_384.txt"
sha3_512_vector_path = "/test_vectors/nist/dgst/sha3_512.txt"


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
        libkcapi_template.setup()
        fun_test.shared_variables["host"] = host
        fun_test.shared_variables["libkcapi_template"] = libkcapi_template
        # setup_path = fun_test.get_script_parent_directory()+ "/lib_crypto/libkcapi"
        # fun_test.test_assert(libkcapi_template.setup(setup_path), "libkcapi Setup complete")

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class TestGcm(FunTestCase):
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
        for file_paths in gcm_vector_path:
            vect_path = fun_test.get_script_parent_directory() + file_paths
            input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
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
                # Compare result or tag, coz if input is null only tag is computed.
                fun_test.simple_assert((enc_output == enc_dict['result'] or
                                        (enc_output in enc_dict['tag'])), "encryption verified")
            fun_test.test_assert(True, "gcm(aes) encryption verified")

            for dec_dict in dec_dicts:
                dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.GCM_AES, dec_dict['cipher_type'],
                                                           dec_dict['key'], encrypt=False,
                                                           cipher_text=dec_dict['cipher_text'],
                                                           iv=dec_dict['iv'], assoc_data=dec_dict['assosc_data'],
                                                           tag=dec_dict['tag'])).strip()
                print "expected :", dec_dict['result']
                print "current :", dec_output
                # Below method of check was done for nist vectors. Need to find a better way to handle it.
                fun_test.simple_assert((dec_output == dec_dict['result']) or
                                       (dec_output in "Received data length 0 does not match expected length 1") or
                                       (dec_output in "EBADMSG"), "decryption verified")
            fun_test.test_assert(True, "gcm(aes) decryption verified")


class TestCcm(FunTestCase):
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
        for file_paths in ccm_vector_path:
            vect_path = fun_test.get_script_parent_directory() + file_paths
            input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
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
                                                           tag_len=enc_dict['tag_len'])).strip()
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


class TestCtr(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Run ctr(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt ctr(aes) with a sample plain text using kcapi command 
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


class TestEcb(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Run ecb(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt ecb(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        for file_paths in ecb_vector_path:
            vect_path = fun_test.get_script_parent_directory() + file_paths
            input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
            enc_dicts = []
            dec_dicts = []
            for dict in input_dict:
                if dict == "enc_ecb(aes)":
                    enc_dicts = input_dict[dict]
                elif dict == "dec_ecb(aes)":
                    dec_dicts = input_dict[dict]

            for enc_dict in enc_dicts:
                enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.ECB_AES, enc_dict['cipher_type'],
                                                           enc_dict['key'],
                                                           plain_text=enc_dict['plain_text'])).strip()
                fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
            fun_test.test_assert(True, "ecb(aes) encryption verified")

            for dec_dict in dec_dicts:
                dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.ECB_AES, dec_dict['cipher_type'],
                                                           dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                           encrypt=False)).strip()
                fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
            fun_test.test_assert(True, "ecb(aes) decryption verified")


class TestXts(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Run xts(aes) with libkcapi",
                              steps="""
        1. Encrypt and decrypt xts(aes) with a sample plain text using kcapi command 
        2. Compare with the known output and ensure they are equal

                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        for file_paths in xts_vector_path:
            vect_path = fun_test.get_script_parent_directory() + file_paths
            input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
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


class TestAuthenc(FunTestCase):
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
        dec_dicts = []
        for dict in input_dict:
            if dict == "auth_enc":
                enc_dicts = input_dict[dict]
            elif dict == "auth_dec":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.AUTH_ENC, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'], assoc_data=enc_dict['assosc_data'],
                                                       tag_len=enc_dict['tag_len'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
            fun_test.test_assert(True, "auth encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.AUTH_ENC, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       iv=dec_dict['iv'], assoc_data=dec_dict['assosc_data'],
                                                       encrypt=False,
                                                       tag=dec_dict['tag'])).strip()

            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "auth decryption verified")


class TestCbc(FunTestCase):
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
        for file_paths in cbc_vector_path:
            vect_path = fun_test.get_script_parent_directory() + file_paths
            input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
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


class TestRfc3686(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Run rfc3686 with libkcapi",
                              steps="""
        1. Encrypt and decrypt rfc3686 with a sample plain text using kcapi command 
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
            if dict == "enc_rfc3686":
                enc_dicts = input_dict[dict]
            elif dict == "dec_rfc3686":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC3686, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "RFC3686 encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC3686, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "RFC3686 decryption verified")


class TestRfc4106(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Run rfc4106 with libkcapi",
                              steps="""
        1. Encrypt and decrypt rfc4106 with a sample plain text using kcapi command 
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
            if dict == "enc_rfc4106":
                enc_dicts = input_dict[dict]
            elif dict == "dec_rfc4106":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC4106, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       assoc_data=enc_dict['assosc_data'],
                                                       tag_len=enc_dict['tag_len'], iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "RFC4106 encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC4106, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, tag=dec_dict['tag'],
                                                       assoc_data=dec_dict['assosc_data'], iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "RFC4106 decryption verified")


class TestRfc4309(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Run rfc4309 with libkcapi",
                              steps="""
        1. Encrypt and decrypt rfc4309 with a sample plain text using kcapi command 
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
            if dict == "enc_rfc4309":
                enc_dicts = input_dict[dict]
            elif dict == "dec_rfc4309":
                dec_dicts = input_dict[dict]

        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC4309, enc_dict['cipher_type'],
                                                       enc_dict['key'], plain_text=enc_dict['plain_text'],
                                                       assoc_data=enc_dict['assosc_data'],
                                                       tag_len=enc_dict['tag_len'], iv=enc_dict['iv'])).strip()
            fun_test.simple_assert((enc_output == enc_dict['result']), "encryption verified")
        fun_test.test_assert(True, "RFC4309 encryption verified")

        for dec_dict in dec_dicts:
            dec_output = (libkcapi_template.kcapi_cmnd(LibkcapiTemplate.RFC4309, dec_dict['cipher_type'],
                                                       dec_dict['key'], cipher_text=dec_dict['cipher_text'],
                                                       encrypt=False, tag=dec_dict['tag'],
                                                       assoc_data=dec_dict['assosc_data'], iv=dec_dict['iv'])).strip()
            fun_test.simple_assert((dec_output == dec_dict['result']), "decryption verified")
        fun_test.test_assert(True, "RFC4309 decryption verified")


class TestSha1(FunTestCase):
    def describe(self):
        self.set_test_details(id=11,
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
        vect_path = fun_test.get_script_parent_directory() + sha1_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha1":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA1, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA1 verified")


class TestSha224(FunTestCase):
    def describe(self):
        self.set_test_details(id=12,
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
        vect_path = fun_test.get_script_parent_directory() + sha224_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha224":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA224, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA224 verified")


class TestSha256(FunTestCase):
    def describe(self):
        self.set_test_details(id=13,
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
        vect_path = fun_test.get_script_parent_directory() + sha256_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha256":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA256, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA256 verified")


class TestSha384(FunTestCase):
    def describe(self):
        self.set_test_details(id=14,
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
        vect_path = fun_test.get_script_parent_directory() + sha384_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha384":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA384, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA384 verified")


class TestSha512(FunTestCase):
    def describe(self):
        self.set_test_details(id=15,
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
        vect_path = fun_test.get_script_parent_directory() + sha512_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha512":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA512, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA512 verified")


class TestSha512224(FunTestCase):
    def describe(self):
        self.set_test_details(id=16,
                              summary="Run SHA512_224 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha512_224_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha512_224":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA512_224, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA512_224 verified")


class TestSha512256(FunTestCase):
    def describe(self):
        self.set_test_details(id=17,
                              summary="Run SHA512_256 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha512_256_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha512_256":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA512_256, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA512_256 verified")


class TestSha3224(FunTestCase):
    def describe(self):
        self.set_test_details(id=18,
                              summary="Run SHA3_224 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha3_224_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha3_224":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA3_224, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA3_224 verified")


class TestSha3256(FunTestCase):
    def describe(self):
        self.set_test_details(id=19,
                              summary="Run SHA3_256 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha3_256_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha3_256":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA3_256, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA3_256 verified")


class TestSha3384(FunTestCase):
    def describe(self):
        self.set_test_details(id=20,
                              summary="Run SHA3_384 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha3_384_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha3_384":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA3_384, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA3_384 verified")


class TestSha3512(FunTestCase):
    def describe(self):
        self.set_test_details(id=21,
                              summary="Run SHA3_512 with libkcapi",
                              steps="""
        1. Compute digest for input.
        2. Compare with result file.
                             """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        vect_path = fun_test.get_script_parent_directory() + sha3_512_vector_path
        libkcapi_template = fun_test.shared_variables["libkcapi_template"]
        input_dict = libkcapi_template.parse_input_libkcapi(vect_path)
        enc_dicts = []
        for dict in input_dict:
            if dict == "dgst_sha3_512":
                enc_dicts = input_dict[dict]
        for enc_dict in enc_dicts:
            enc_output = (libkcapi_template.kcapi_dgst(LibkcapiTemplate.SHA3_512, enc_dict['cipher_type'],
                                                       msg=enc_dict['MSG'])).strip()

            fun_test.simple_assert((enc_output == enc_dict['MD']), "encryption verified")
        fun_test.test_assert(True, "SHA3_512 verified")


if __name__ == "__main__":
    libkcapi_script = LibkcapiScript()

    libkcapi_script.add_test_case(TestGcm())
    libkcapi_script.add_test_case(TestCcm())
    libkcapi_script.add_test_case(TestCtr())
    libkcapi_script.add_test_case(TestEcb())
    libkcapi_script.add_test_case(TestXts())
    # libkcapi_script.add_test_case(TestAuthenc())
    libkcapi_script.add_test_case(TestCbc())
    # libkcapi_script.add_test_case(TestRfc3686())
    # libkcapi_script.add_test_case(TestRfc4106())
    # libkcapi_script.add_test_case(TestRfc4309())
    libkcapi_script.add_test_case(TestSha1())
    libkcapi_script.add_test_case(TestSha224())
    libkcapi_script.add_test_case(TestSha256())
    libkcapi_script.add_test_case(TestSha384())
    libkcapi_script.add_test_case(TestSha512())
    # libkcapi_script.add_test_case(TestSha512224())
    # libkcapi_script.add_test_case(TestSha512256())
    # libkcapi_script.add_test_case(TestSha3224())
    # libkcapi_script.add_test_case(TestSha3256())
    # libkcapi_script.add_test_case(TestSha3384())
    # libkcapi_script.add_test_case(TestSha3512())

    libkcapi_script.run()
