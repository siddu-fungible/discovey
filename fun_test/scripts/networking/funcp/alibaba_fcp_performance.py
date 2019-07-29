from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp import alibaba_fcp_setup
from scripts.networking.funeth import funeth, sanity, perf_utils, performance
from lib.host import netperf_manager as nm
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *

FPG_INTERFACES = (0, 4, 8, 20)
FPG_FABRIC_DICT = {
    'F1_0': (16, 12),
    'F1_1': (12, 20),
}

class SetupBringup(alibaba_fcp_setup.ScriptSetup):

    def describe(self):
        self.set_test_details(steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):
        super(SetupBringup, self).setup()
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        tb_config_obj = tb_configs.TBConfigs(str(fs_name))
        funeth_obj = funeth.Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        linux_objs = funeth_obj.linux_obj_dict.values()

        fun_test.log("Configure irq affinity")
        for hu in funeth_obj.hu_hosts:
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='tx', cpu_list=funeth.CPU_LIST_HOST)
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='rx', cpu_list=funeth.CPU_LIST_HOST)

        for nu in funeth_obj.nu_hosts:
            linux_obj = funeth_obj.linux_obj_dict[nu]
            perf_utils.mlx5_irq_affinity(linux_obj)

        netperf_manager_obj = nm.NetperfManager(linux_objs)
        fun_test.shared_variables['netperf_manager_obj'] = netperf_manager_obj
        fun_test.test_assert(netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        topology = fun_test.shared_variables["topology"]
        network_controller_objs = []
        for i in range(0, 2):
            fs = topology.get_dut_instance(index=i)

            come_obj = fs.get_come()
            fun_test.shared_variables['come_linux_obj'] = come_obj

            for port in come_obj.DEFAULT_DPC_PORT:
                network_controller_objs.append(NetworkController(dpc_server_ip=come_obj.host_ip,
                                                                 dpc_server_port=port, verbose=True))
        fun_test.shared_variables['network_controller_objs'] = network_controller_objs
        for nc_obj in network_controller_objs:
            f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
            buffer_pool_set = nc_obj.set_qos_egress_buffer_pool(sf_thr=11000,
                                                                sf_xoff_thr=10000,
                                                                nonfcp_thr=11000,
                                                                nonfcp_xoff_thr=10000,
                                                                mode='nu')
            fun_test.test_assert(buffer_pool_set, '{}: Configure QoS egress buffer pool'.format(f1))
            nc_obj.get_qos_egress_buffer_pool()

            for port_num in FPG_INTERFACES:
                port_buffer_set = nc_obj.set_qos_egress_port_buffer(port_num, min_threshold=6000, shared_threshold=16383)
                fun_test.test_assert(port_buffer_set, '{}: Configure QoS egress port {} buffer'.format(f1, port_num))
                nc_obj.get_qos_egress_port_buffer(port_num)

            if sanity.control_plane:
                fpg_mtu = 9000
                for p in FPG_INTERFACES:
                    port_mtu_set = nc_obj.set_port_mtu(p, fpg_mtu)
                    fun_test.test_assert(port_mtu_set, '{}: Configure FPG{} mtu {}'.format(f1, p, fpg_mtu))


    def cleanup(self):
        super(SetupBringup, self).cleanup()


class HuHuNonFCP(performance.FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=1, summary="HU HU perf",
                              steps="""
                                      
                                      """)

    def setup(self):
        pass

    def run(self):
        topology = fun_test.shared_variables["topology"]
        for i in range(0, 2):
            fs = topology.get_dut_instance(index=i)

            come_obj = fs.get_come()
            # Delete FCP FTEP for 1st host
            if i == 0:
                perf_utils.redis_del_fcp_ftep(come_obj)
            else:
                fun_test.shared_variables['come_linux_obj'] = come_obj

        performance.FunethPerformanceBase._run(self, flow_type="HU_HU_NFCP_2F1", num_flows=8, num_hosts=4, frame_size=1500,
                                               duration=30)

    def cleanup(self):
        pass


class HuHuFCP(performance.FunethPerformanceBase):
    def describe(self):
        self.set_test_details(id=1, summary="HU HU perf",
                              steps="""

                                      """)

    def setup(self):
        pass

    def run(self):

        performance.FunethPerformanceBase._run(self, flow_type="HU_HU_FCP", num_flows=8, num_hosts=4, frame_size=1500,
                                               duration=30)

    def cleanup(self):
        pass


class ScriptSetup2(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                                  1. BringUP both F1s
                                  2. Bringup FunCP
                                  3. Create MPG Interfaces and assign static IPs
                                  """)

    def setup(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')
        fs_name = fun_test.get_job_environment_variable('test_bed_type')


    def cleanup(self):
        fun_test.log("Cleanup")
        # fun_test.shared_variables["topology"].cleanup()


if __name__ == '__main__':
    ts = SetupBringup()
    ts.add_test_case(HuHuFCP())
    # ts.add_test_case(HuHuNonFCP())
    ts.run()
