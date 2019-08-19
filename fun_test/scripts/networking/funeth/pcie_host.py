from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs


fs_with_pcie_host = ('fs-11', 'fs-45', 'fs-66', 'fs-60', 'fs-48', 'fs-20', 'fs-31',)


class PcieHost(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Check PCIe host can see F1 with expected LnkSta
        """)

    def setup(self):

        fs = fun_test.get_job_environment_variable('test_bed_type')
        if fs and fs not in fs_with_pcie_host:
            fun_test.test_assert(False, "Please use {}.".format(','.join(fs_with_pcie_host)))

        # Boot up FS1600
        topology_helper = TopologyHelper()
        if fs == 'fs-11':
            boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=boot_args)
        elif fs == 'fs-45':
            f1_0_boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
            f1_1_boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})
        elif fs == 'fs-66':
            f1_0_boot_args = "app=hw_hsu_test retimer=0 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
            f1_1_boot_args = "app=hw_hsu_test retimer=0 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})
        elif fs == 'fs-60':
            f1_0_boot_args = "app=hw_hsu_test cc_huid=3 --all_100g --dpc-server --dpc-uart retimer=0,1,2 --disable-wu-watchdog"
            f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --all_100g --dpc-server --dpc-uart retimer=0 --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})
        elif fs == 'fs-48':
            f1_0_boot_args = "app=hw_hsu_test cc_huid=3 --all_100g --dpc-server --dpc-uart retimer=0,1,2 --disable-wu-watchdog"
            f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --all_100g --dpc-server --dpc-uart retimer=0 --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})

        elif fs == 'fs-20':
            f1_0_boot_args = "app=hw_hsu_test cc_huid=3 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog"
            f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --all_100g --dpc-server --dpc-uart retimer=0 --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})
        elif fs == 'fs-31':
            f1_0_boot_args = "app=hw_hsu_test cc_huid=3 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog retimer=0"
            f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog"
            topology_helper.set_dut_parameters(dut_index=0,
                                               f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}})

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fun_test.shared_variables["topology"] = topology

        TB = ''.join(fs.split('-')).upper()
        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj

    def cleanup(self):
        fs = fun_test.get_job_environment_variable('test_bed_type')
        if fs and fs in fs_with_pcie_host:
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
