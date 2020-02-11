from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper

class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        already_deployed = False
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        self.topology.cleanup()


class QuickImagesVersionChecks(FunTestCase):
    topology = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="check the funsdk version on runing funos",
                              steps='''
                              1. Make sure FSox is up and running
                              2. validate the image versions
                              ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]

    def run(self):
        fs_obj = self.topology.get_dut_instance(index=0)
        bld_props = fs_obj.get_come().get_build_props()
        return_code = fs_obj.platform.validate_firmware(f1_index=0, bld_props=bld_props)
        fun_test.test_assert(expression=return_code, message="DPU#0 Bundle Flash results: {}"
            .format("Success" if return_code else "Failed"))
        return_code = fs_obj.platform.validate_firmware(f1_index=1, bld_props=bld_props)
        fun_test.test_assert(expression=return_code, message="DPU#1 Bundle Flash results: {}"
            .format("Success" if return_code else "Failed"))

    def cleanup(self):
        pass


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(QuickImagesVersionChecks())
    setup_bringup.run()
