from lib.system.fun_test import *
from lib.templates.security.openssl_template import OpenSslTemplate
from lib.templates.security.crypto_template import CryptoTemplate
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
vector_path = "/test_vectors/sha1.txt"


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
        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        if self.topology:
            TopologyHelper(spec=self.topology).cleanup()
        return True


class OpenSslTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Check the OpenSSL sha1 digests generated",
                              steps="""
        1. Parse input file
        2. Run OpenSSL sha1 digest commands
        3. Compare with precomputed digests
        
                              """)

    def setup(self):
        return True

    def cleanup(self):
        return True

    def compute_sha1_digests(self, host, openssl_template):
        # parse the input vectors file
        file_path = fun_test.get_script_parent_directory() + vector_path
        digest_dict = openssl_template.parse_input(file_path)
        input_list = digest_dict.keys()

        # compute and compare digests
        for index, digest_input in enumerate(input_list):
            host.create_file("{}{}.txt".format(base_file_name, index), contents=digest_input, newline=False)
            digest_output = openssl_template.compute_digest(CryptoTemplate.DGST, CryptoTemplate.SHA1,
                                                            "{}{}.txt".format(base_file_name, index))
            fun_test.simple_assert((digest_output == digest_dict[digest_input]), "Digests match")

        return True

    def run(self):
        topology = fun_test.shared_variables["topology"]

        host = topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        openssl_template = OpenSslTemplate(host)
        openssl_template.setup()
        fun_test.test_assert((self.compute_sha1_digests(host, openssl_template)), "sha1 digests match")


if __name__ == "__main__":
    openssl_script = OpenSslScript()
    openssl_script.add_test_case(OpenSslTestCase1())
    openssl_script.run()
