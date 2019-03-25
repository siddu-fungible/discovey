from lib.system.fun_test import *
from lib.templates.security.openssl_template import OpenSslTemplate
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

base_file_name = "/tmp/input"
vector_path = "/test_vectors"

sha_path_list=["/sha1.txt", "/sha224.txt", "/sha256.txt", "/sha384.txt", "/sha512.txt"]
hmac_path_list=["/hmac_sha1.txt", "/hmac_sha224.txt"]
plain_path = "/plain_16.txt"

class OpenSslScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and Allocate a QEMU instance
        2. Make the QEMU instance available for the testcase
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        openssl_template = OpenSslTemplate(host)
        openssl_template.setup()
        fun_test.shared_variables["host"] = host
        fun_test.shared_variables["openssl_template"] = openssl_template

    def compute_digests(self, host, openssl_template, path, algorithm):
        # parse the input vectors file
        file_path = fun_test.get_script_parent_directory() + vector_path + path
        digest_dict = openssl_template.parse_input(file_path)
        input_list = digest_dict.keys()

        # compute and compare digests
        for index, digest_input in enumerate(input_list):
            host.create_file("{}{}.bin".format(base_file_name, index), contents=digest_input)
            digest_output = openssl_template.compute_digest(algorithm, "{}{}.bin".format(base_file_name, index))
            fun_test.simple_assert((digest_output == digest_dict[digest_input]), "Digests match")

        return True

    def compute_hmacs(self, host, openssl_template, path, algorithm):
        # parse the input vectors file
        file_path = fun_test.get_script_parent_directory() + vector_path + path
        hmac_dict = openssl_template.parse_input_hmac(file_path)
        input_list = hmac_dict.keys()
        print input_list

        # compute and compare digests
        for index, hmac_input in enumerate(input_list):
            host.create_file("{}{}.bin".format(base_file_name, index), contents=(hmac_dict[hmac_input].values())[0])
            digest_output = openssl_template.compute_hmac(algorithm, "{}{}.bin".format(base_file_name, index), key=(hmac_dict[hmac_input].keys())[0])
            print digest_output
            fun_test.simple_assert((digest_output == hmac_input), "hmacs match")

        return True

    def cleanup(self):
        if self.topology:
            TopologyHelper(spec=self.topology).cleanup()
        return True


class OpenSslTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Check the OpenSSL SHA-1 digests generated",
                              steps="""
        1. Parse input file
        2. Run OpenSSL sha1 digest commands
        3. Compare with precomputed digests
        
                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def run(self):
        openssl_template = fun_test.shared_variables["openssl_template"]
        host = fun_test.shared_variables["host"]
        fun_test.test_assert((openssl_script.compute_digests(host, openssl_template, sha_path_list[0], openssl_template.SHA1)), "sha1 digests match")


class OpenSslTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Check the OpenSSL SHA-2 digests generated",
                              steps="""
        1. Parse input file
        2. Run OpenSSL sha1 digest commands
        3. Compare with precomputed digests

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def run(self):
        openssl_template = fun_test.shared_variables["openssl_template"]
        host = fun_test.shared_variables["host"]
        fun_test.test_assert((openssl_script.compute_digests(host, openssl_template, sha_path_list[1], openssl_template.SHA224)), "sha224 digests match")
        fun_test.test_assert((openssl_script.compute_digests(host, openssl_template, sha_path_list[2], openssl_template.SHA256)), "sha256 digests match")
        fun_test.test_assert((openssl_script.compute_digests(host, openssl_template, sha_path_list[3], openssl_template.SHA384)), "sha384 digests match")
        fun_test.test_assert((openssl_script.compute_digests(host, openssl_template, sha_path_list[4], openssl_template.SHA512)), "sha512 digests match")


class OpenSslTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Check the OpenSSL SHA-1 hmacs generated",
                              steps="""
        1. Parse input file
        2. Run OpenSSL sha1 hmac commands
        3. Compare with precomputed digests

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def run(self):
        openssl_template = fun_test.shared_variables["openssl_template"]
        host = fun_test.shared_variables["host"]
        fun_test.test_assert((openssl_script.compute_hmacs(host, openssl_template, hmac_path_list[0], openssl_template.SHA1)),
                             "sha1 hmacs match")

class OpenSslTestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Check the OpenSSL SHA-2 hmacs generated",
                              steps="""
        1. Parse input file
        2. Run OpenSSL sha2 hmac commands
        3. Compare with precomputed digests

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def run(self):
        openssl_template = fun_test.shared_variables["openssl_template"]
        host = fun_test.shared_variables["host"]
        fun_test.test_assert((openssl_script.compute_hmacs(host, openssl_template, hmac_path_list[1], openssl_template.SHA224)),
                             "sha224 hmacs match")


class OpenSslTestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Check the aes(cbc)128 encryption/decryption",
                              steps="""
        1. scp the input file
        2. Run encrypt and decrypt commands with aes(cbc)128
        3. generate md5 digests of input and decrypted files
        4. compare the digests

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def run(self):
        openssl_template = fun_test.shared_variables["openssl_template"]
        host = fun_test.shared_variables["host"]
        in_file_path = "/tmp/plain.txt"
        fun_test.scp(source_file_path=fun_test.get_script_parent_directory() + vector_path + plain_path, target_ip=host.host_ip,
                     target_port=host.ssh_port, target_username=host.ssh_username,
                     target_password=host.ssh_password,
                     target_file_path=in_file_path)
        out_enc_path = "/tmp/enc.txt"
        out_dec_path = "/tmp/dec.txt"
        plain_mds5 = openssl_template.compute_md5(in_file_path)
        fun_test.test_assert(openssl_template.encrypt(OpenSslTemplate.AESCBC128, in_file_path, out_enc_path, "key"), "encrypt successful")
        fun_test.test_assert(openssl_template.decrypt(OpenSslTemplate.AESCBC128, out_enc_path, out_dec_path, "key"), "decrypt successful")
        dec_md5 = openssl_template.compute_md5(out_dec_path)
        fun_test.test_assert((plain_mds5 == dec_md5), "aes(cbc)128 successful")


if __name__ == "__main__":
    openssl_script = OpenSslScript()
    openssl_script.add_test_case(OpenSslTestCase1())
    openssl_script.add_test_case(OpenSslTestCase2())
    openssl_script.add_test_case(OpenSslTestCase3())
    openssl_script.add_test_case(OpenSslTestCase4())
    openssl_script.add_test_case(OpenSslTestCase5())

    openssl_script.run()
