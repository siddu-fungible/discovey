from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp import alibaba_fcp_setup
from scripts.networking.funeth import funeth, sanity, perf_utils, performance
from lib.host import netperf_manager as nm
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from web.fun_test.analytics_models_helper import get_data_collection_time
import json
import pprint


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

            for port_num in FunPerformance.FPG_INTERFACES:
                port_buffer_set = nc_obj.set_qos_egress_port_buffer(port_num, min_threshold=6000, shared_threshold=16383)
                fun_test.test_assert(port_buffer_set, '{}: Configure QoS egress port {} buffer'.format(f1, port_num))
                nc_obj.get_qos_egress_port_buffer(port_num)

            fpg_mtu = 9000
            for p in FunPerformance.FPG_INTERFACES:
                port_mtu_set = nc_obj.set_port_mtu(p, fpg_mtu)
                fun_test.test_assert(port_mtu_set, '{}: Configure FPG{} mtu {}'.format(f1, p, fpg_mtu))

            results = []
            fun_test.shared_variables['results'] = results

    def cleanup(self):
        super(SetupBringup, self).cleanup()


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


class FunPerformance(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        pass

    inputs = fun_test.get_job_inputs()
    if inputs:
        debug_mode = (inputs.get('debug', 0) == 1)
    else:
        debug_mode = False

    if debug_mode:
        RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
    else:
        RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'

    FPG_INTERFACES = (0, 4, 8, 20)
    FPG_FABRIC_DICT = {
        'F1_0': (8,),
        'F1_1': (20,),
    }
    PERF_RESULT_KEYS = (nm.THROUGHPUT,
                        nm.PPS,
                        nm.LATENCY_MIN,
                        nm.LATENCY_AVG,
                        nm.LATENCY_MAX,
                        nm.LATENCY_P50,
                        nm.LATENCY_P90,
                        nm.LATENCY_P99,
                        nm.LATENCY_MIN_ULOAD,
                        nm.LATENCY_AVG_ULOAD,
                        nm.LATENCY_MAX_ULOAD,
                        nm.LATENCY_P50_ULOAD,
                        nm.LATENCY_P90_ULOAD,
                        nm.LATENCY_P99_ULOAD,
                        )

    TIMESTAMP = get_data_collection_time()

    FLOW_TYPES_DICT = OrderedDict([
        ('HU_NU_NFCP', 'HU -> NU non-FCP'),
        ('NU_HU_NFCP', 'NU -> HU non-FCP'),
        ('HU_HU_NFCP', 'HU -> HU non-FCP under 1 F1'),
        ('HU_HU_FCP', 'HU -> HU FCP under 2 F1s'),
        ('HU_HU_NFCP_2F1', 'HU -> HU non-FCP under 2 F1s'),
        ('HU_NU_NFCP_UL_VM', 'HU -> NU non-FCP'),
        ('NU_HU_NFCP_UL_VM', 'NU -> HU non-FCP'),
        ('HU_HU_NFCP_UL_VM', 'HU -> HU non-FCP under 1 F1'),
        ('HU_HU_FCP_UL_VM', 'HU -> HU Underlay FCP under 2 F1s'),
        ('HU_HU_NFCP_2F1_UL_VM', 'HU -> HU Underlay non-FCP under 2 F1s'),
        ('HU_HU_FCP_OL_VM', 'HU -> HU Overlay FCP under 2 F1s'),
        ('HU_HU_NFCP_OL_VM', 'HU -> HU Overlay non-FCP under 2 F1s'),
        # TODO: Enable bi-direction
    ])
    TOOLS = ('netperf',)
    PROTOCOLS = ('tcp',)  # TODO: add UDP

    def redis_del_fcp_ftep(self, linux_obj):
        """In redis, delete FCP FTEP to tear down FCP tunnel."""
        # TODO: make it setup independent
        contents = ""
        if linux_obj.host_ip == 'fs60-come':
            ftep_dict = {
                'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'7.7.7.7\']"
            }
            contents = "SELECT 1 \nDEL \"openconfig-fcp:fcp-tunnel[ftep='7.7.7.7']\""
        elif linux_obj.host_ip == 'fs48-come':
            ftep_dict = {
                'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'9.9.9.9\']"
            }
            contents = "SELECT 1 \nDEL \"openconfig-fcp:fcp-tunnel[ftep='9.9.9.9']\""
        else:
            ftep_dict = {
                'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'9.9.9.9\']",
                'F1-1': r"openconfig-fcp:fcp-tunnel[ftep=\'7.7.7.7\']"
            }
        for k in ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(k)
            cmd_op = 'DEL "{}"'.format(ftep_dict[k])
            cmd_chk = 'KEYS *fcp-tunnel*'
            chk_file = 'check_{}'.format(k)
            del_file = 'del_{}'.format(k)

            # check
            cmds = ['SELECT 1', cmd_chk]
            linux_obj.command('{0} "rm {1}; touch {1}"'.format(cmd_prefix, chk_file))
            for cmd in cmds:
                linux_obj.command('{} \"echo {} >> {}\"'.format(cmd_prefix, cmd, chk_file))
            linux_obj.command('{} "cat {}"'.format(cmd_prefix, chk_file))

            # del
            lin = FunCpDockerContainer(host_ip=linux_obj.host_ip, ssh_username="fun", ssh_password="123", name=k)
            lin.create_file(del_file, contents=contents)
            fun_test.log("Check and delete FCP FTEP to tear down FCP tunnel in {}".format(k))
            linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, chk_file))
            linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, del_file))
            linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, chk_file))

    def _run(self, tool='netperf', protocol='tcp', flow_type="HU_HU_FCP", num_flows=8, num_hosts=4, frame_size=1500, duration=30):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        cpu_list_client = funeth.CPU_LIST_HOST
        cpu_list_server = funeth.CPU_LIST_HOST
        # TODO: Add new way of taking NFCP path
        if flow_type.startswith('HU_HU_NFCP_2F1'):
            ftep_dict = {
                'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'9.9.9.9\']"
            }
            self.redis_del_fcp_ftep(Linux(host_ip="fs48-come", ssh_password="123", ssh_username="fun"))
            ftep_dict = {
                'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'7.7.7.7\']"
            }
            self.redis_del_fcp_ftep(Linux(host_ip="fs60-come", ssh_password="123", ssh_username="fun"))
        perf_manager_obj = fun_test.shared_variables['netperf_manager_obj']
        host_pairs = []
        bi_dir = False  # TODO: enable bi-direction
        if flow_type.startswith('HU_HU'):  # HU --> HU
            # TODO: handle exception if hu_hosts len is 1
            num_hu_hosts = len(funeth_obj.hu_hosts)
            flow_types_2f1 = ('HU_HU_NFCP_2F1', 'HU_HU_NFCP_OL', 'HU_HU_FCP')
            if any(flow_type.startswith(f) for f in flow_types_2f1):  # Under 2 F1s
                for i in range(0, num_hu_hosts / 2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i + 2]])
                    if num_flows == 1:
                        break
                    elif len(host_pairs) == num_hosts:
                        break
            elif flow_type.startswith('HU_HU_NFCP'):  # Under 1 F1
                for i in range(0, num_hu_hosts, 2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i + 1]])
                    if num_flows == 1:
                        break
                    elif len(host_pairs) == num_hosts:
                        break
        else:
            for nu, hu in zip(funeth_obj.nu_hosts, funeth_obj.hu_hosts):
                if flow_type.startswith('NU_HU'):  # NU --> HU
                    host_pairs.append([nu, hu])
                elif flow_type.startswith('HU_NU'):  # HU --> NU
                    host_pairs.append([hu, nu])
                elif flow_type.startswith('NU2HU'):  # NU <-> HU
                    host_pairs.append([nu, hu])
                    host_pairs.append([hu, nu])
                    bi_dir = True
                if num_flows == 1:
                    break
                elif len(host_pairs) == num_hosts:
                    break
        suffixes = ('n2h', 'h2n', 'h2h')
        arg_dicts = []
        pingable = True
        linux_obj_src = None
        dip = None
        for shost, dhost in host_pairs:
            linux_obj_src = funeth_obj.linux_obj_dict[shost]
            linux_obj_dst = funeth_obj.linux_obj_dict[dhost]
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr(dhost,
                                                                   funeth_obj.tb_config_obj.get_an_interface(dhost))
            if not 'OL_VM' in flow_type.upper():  # TODO: Remove after overlay support ping flow
                pingable &= linux_obj_src.ping(dip, count=5, max_percentage_loss=40, size=frame_size-20-8)

                if pingable:
                    fun_test.test_assert(pingable, '{} ping {} with packet size {}'.format(
                        linux_obj_src.host_ip, dip, frame_size))
                else:
                    break

            suffix = '{}2{}'.format(shost[0], dhost[0])
            arg_dicts.append(
                {'linux_obj': linux_obj_src,
                 'linux_obj_dst': linux_obj_dst,
                 'dip': dip,
                 'tool': tool,
                 'protocol': protocol,
                 #'num_flows': num_flows/len(host_pairs) if not bi_dir else num_flows/(len(host_pairs)/2),
                 'num_flows': num_flows,
                 'duration': duration,
                 'frame_size': frame_size + 18,  # Pass Ethernet frame size
                 'suffix': suffix,
                 'cpu_list_server': cpu_list_server,
                 'cpu_list_client': cpu_list_client,
                 #'fixed_netperf_port': True if 'OL_VM' in flow_type.upper() else False,  # TODO: Remove after SWOS-5645
                 }
            )

        # Collect stats before and after test run
        network_controller_objs = fun_test.shared_variables['network_controller_objs']
        fpg_interfaces = self.FPG_INTERFACES[:num_hosts]
        fpg_intf_dict = self.FPG_FABRIC_DICT
        version = fun_test.get_version()
        fun_test.log('Collect stats before test')
        sth_stuck_before = True
        sth_stuck_after = True

        if len(network_controller_objs) == 4:
            network_controller_objs_fs1 = network_controller_objs[:len(network_controller_objs) // 2]
            network_controller_objs_fs2 = network_controller_objs[:len(network_controller_objs) // 2:]
            sth_stuck_before &= perf_utils.collect_dpc_stats(network_controller_objs_fs1,
                                                             fpg_interfaces,
                                                             fpg_intf_dict,
                                                             version,
                                                             when='before')
            sth_stuck_before &= perf_utils.collect_dpc_stats(network_controller_objs_fs2,
                                                             fpg_interfaces,
                                                             fpg_intf_dict,
                                                             version,
                                                             when='before')
        elif len(network_controller_objs) == 2:

            sth_stuck_before &= perf_utils.collect_dpc_stats(network_controller_objs,
                                                             fpg_interfaces,
                                                             fpg_intf_dict,
                                                             version,
                                                             when='before')

        if pingable and not sth_stuck_before:

            # TODO: calculate dpc stats collection duration and add it to test duration*2
            perf_utils.collect_host_stats(funeth_obj, version, when='before', duration=duration*5)

            result = perf_manager_obj.run(*arg_dicts)

            fun_test.log('Collect stats after test')

            if len(network_controller_objs) == 4:
                network_controller_objs_fs1 = network_controller_objs[:len(network_controller_objs) // 2]
                network_controller_objs_fs2 = network_controller_objs[:len(network_controller_objs) // 2:]
                sth_stuck_after &= perf_utils.collect_dpc_stats(network_controller_objs_fs1,
                                                                 fpg_interfaces,
                                                                 fpg_intf_dict,
                                                                 version,
                                                                 when='after')
                sth_stuck_after &= perf_utils.collect_dpc_stats(network_controller_objs_fs2,
                                                                 fpg_interfaces,
                                                                 fpg_intf_dict,
                                                                 version,
                                                                 when='after')
            elif len(network_controller_objs) == 2:

                sth_stuck_after &= perf_utils.collect_dpc_stats(network_controller_objs,
                                                                 fpg_interfaces,
                                                                 fpg_intf_dict,
                                                                 version,
                                                                 when='after')
            # Collect host stats after dpc stats to give enough time for mpstat collection
            perf_utils.collect_host_stats(funeth_obj, version, when='after')
            if sth_stuck_after:
                result = {}
        else:
            result = {}

        fun_test.log('NetperfManager Results:\n{}'.format(pprint.pformat(result)))
        if not result:
            passed = False
        elif any(v == nm.NA for v in result.values()):
            passed = False
        else:
            passed = True

        # Set N/A for untested direction
        for suffix in suffixes:
            for k in self.PERF_RESULT_KEYS:
                k_suffix = '{}_{}'.format(k, suffix)
                if k_suffix not in result:
                    result.update(
                        {k_suffix: nm.NA}
                    )

        # Update result dict
        result.update(
            {'flow_type': flow_type,
             'frame_size': frame_size,
             'protocol': protocol.upper(),
             'offloads': sanity.enable_tso,
             'num_flows': num_flows,
             'num_hosts': num_hosts,
             'timestamp': '%s' % self.TIMESTAMP,  # Use same timestamp for all the results of same run, per John/Ashwin
             'version': version,
             }
        )
        fun_test.log('Final Results:\n{}'.format(pprint.pformat(result)))

        # Update file with result
        with open(self.RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(self.RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.shared_variables['results'].append(result)
        fun_test.simple_assert(pingable, '{} ping {} with packet size {}'.format(
            linux_obj_src.host_ip, dip, frame_size))
        fun_test.simple_assert(not sth_stuck_before, 'Something is stuck before test')
        fun_test.test_assert(passed, 'Get throughput/pps/latency test result')
        fun_test.simple_assert(not sth_stuck_after, 'Something is stuck after test')
        fun_test.test_assert(expression=result, message="Results")
        fun_test.log('Final Results:\n{}'.format(pprint.pformat(result)))


class HuHuFCP(FunPerformance):
    def describe(self):
        self.set_test_details(id=1, summary="HU HU FCP perf",
                              steps="""

                                      """)

    def setup(self):
        pass

    def run(self):
        FunPerformance._run(self, flow_type="HU_HU_FCP", num_flows=8, num_hosts=4, frame_size=1500, duration=30)

    def cleanup(self):
        pass


class HuNu(FunPerformance):
    def describe(self):
        self.set_test_details(id=3, summary="HU NU perf",
                              steps="""

                                      """)

    def setup(self):
        pass

    def run(self):
        FunPerformance._run(self, flow_type="HU_NU_NFCP", num_flows=8, num_hosts=2, frame_size=1500, duration=30)

    def cleanup(self):
        pass


class NuHu(FunPerformance):
    def describe(self):
        self.set_test_details(id=4, summary="NU HU perf",
                              steps="""

                                      """)

    def setup(self):
        pass

    def run(self):
        FunPerformance._run(self, flow_type="NU_HU_NFCP", num_flows=8, num_hosts=2, frame_size=1500, duration=30)

    def cleanup(self):
        pass


class HuHuNonFCP(FunPerformance):
    def describe(self):
        self.set_test_details(id=2, summary="HU HU Non FCP perf",
                              steps="""

                                      """)

    def setup(self):
        pass

    def run(self):
        FunPerformance._run(self, flow_type="HU_HU_NFCP_2F1", num_flows=8, num_hosts=4, frame_size=1500, duration=30)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = SetupBringup()

    ts.add_test_case(HuHuFCP())
    ts.add_test_case(HuHuNonFCP())
    ts.add_test_case(HuNu())
    ts.add_test_case(NuHu())

    ts.run()
