from lib.system.fun_test import *
from lib.templates.security.sha3_template import Sha3Template
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

BASE_FILE_NAME = "/tmp/input"
VECTOR_PATH = "/test_vectors/"
sha3_digests_list = ["sha3_224.txt", "sha3_256.txt", "sha3_384.txt", "sha3_512.txt"]

class CryptoAcceleratorScript(FunTestScript):
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

    def cleanup(self):
        if self.topology:
            TopologyHelper(spec=self.topology).cleanup()
        return True

class Sha3TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Check the sha3 digests generated",
                              steps="""
        1. Parse input file
        2. Run sha3 digest commands using digest_hmac tool
        3. Compare with precomputed digests

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def compute_all_digests(self, host, sha3_template):
        for idx, digest_file_input in enumerate(sha3_digests_list):
            # parse the input vectors file
            file_path = fun_test.get_script_parent_directory() + VECTOR_PATH + sha3_digests_list[idx]
            digest_dict = sha3_template.parse_input_sha3(file_path)
            input_list = digest_dict.keys()

            # compute and compare digests
            for index, digest_input in enumerate(input_list):
                host.create_file("{}{}.txt".format(BASE_FILE_NAME, index), contents=digest_input)
                digest_output = sha3_template.compute_digest(Sha3Template.sha3_digests[idx],
                                                                         "{}{}.txt".format(BASE_FILE_NAME, index))
                # fun_test.test_assert_expected(expected=digest_dict[digest_input], actual=digest_output, message="match!!",
                #                              ignore_on_success=True)
                fun_test.simple_assert((digest_output == digest_dict[digest_input]), "Digests match?")

        return True

    def run(self):
        topology = fun_test.shared_variables["topology"]

        host = topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        sha3_template = Sha3Template(host)
        sha3_template.setup_verify()

        compute_digests_flag = self.compute_all_digests(host, sha3_template)
        fun_test.test_assert(compute_digests_flag, "Digests match?")


class Sha3TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Check the sha3 hmacs generated",
                              steps="""
        1. Parse input file
        2. Run sha3 hmac  commands using digest_hmac_sha3 tool
        3. Compare with precomputed hmacs

                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True


    def compute_all_hmacs(self, host, sha3_template):
        for idx, digest_file_input in enumerate(sha3_digests_list):
            if (idx < 2): # fix the tool and remove this check
                file_path = fun_test.get_script_parent_directory() + VECTOR_PATH + "hmac_" + sha3_digests_list[idx]
                hmac_list = sha3_template.parse_input_sha3(file_path)
                for index, hmac_input in enumerate(hmac_list):
                    host.create_file("{}{}.txt".format(BASE_FILE_NAME, index), contents=hmac_input[0])
                    hmac_output = sha3_template.compute_hmac(
                        "\"hmac(" + Sha3Template.sha3_digests[idx] + ")\"",
                                                                         "{}{}.txt".format(BASE_FILE_NAME, index),
                                                                        hmac_input[3],hmac_input[2])
                    fun_test.simple_assert((hmac_output == hmac_input[1]), "Digests match?")

        return True

    def run(self):
        topology = fun_test.shared_variables["topology"]

        host = topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        sha3_template = Sha3Template(host)
        sha3_template.setup_verify()

        compute_hmacs_flag = self.compute_all_hmacs(host, sha3_template)
        fun_test.test_assert(compute_hmacs_flag, "Digests match?")

if __name__ == "__main__":
    crypto_accelerator_script = CryptoAcceleratorScript()
    crypto_accelerator_script.add_test_case(Sha3TestCase1())
    crypto_accelerator_script.add_test_case(Sha3TestCase2())
    crypto_accelerator_script.run()

