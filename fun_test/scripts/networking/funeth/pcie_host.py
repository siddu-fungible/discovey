from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs


class PcieHost(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Check PCIe host can see F1 with expected LnkSta
        """)

    def setup(self):

        fs = fun_test.get_job_environment_variable('test_bed_type')
        if fs and fs != 'fs-11':
            fun_test.test_assert(False, "Please use FS-11.")

        # Boot up FS1600
        boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g"
        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=boot_args)

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fun_test.shared_variables["topology"] = topology

        tb_config_obj = tb_configs.TBConfigs('FS11')
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-11':
            fun_test.shared_variables["topology"].cleanup()
            fun_test.shared_variables['funeth_obj'].cleanup_workspace()


class PceiHostLnkSta(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Check PCIe host can see F1 with expected width in LnkSta",
                              steps="""
        1. Check PCIe host can see F1 with expected width in LnkSta
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        funeth_obj.setup_workspace()
        fun_test.test_assert(funeth_obj.lspci(), 'Fungible Ethernet controller is seen.')


if __name__ == "__main__":
    ts = PcieHost()
    for tc in (
            PceiHostLnkSta,
    ):
        ts.add_test_case(tc())
    ts.run()
