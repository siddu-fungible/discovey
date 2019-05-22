from lib.system.fun_test import *
from fun_global import get_current_time
from fun_settings import FUN_TEST_DIR
from lib.host import netperf_manager as nm
from lib.host.network_controller import NetworkController
from scripts.networking.tcp import helper
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funeth import funeth, sanity
from collections import OrderedDict
import json
import pprint
import re


TB = sanity.TB
inputs = fun_test.get_job_inputs()
if inputs and inputs.get('debug', 0):
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data2.json'
else:
    RESULT_FILE = FUN_TEST_DIR + '/web/static/logs/hu_funeth_performance_data.json'
TIMESTAMP = get_current_time()
FLOW_TYPES_DICT = OrderedDict([  # TODO: add FCP
    ('HU_NU_NFCP', 'HU -> NU non-FCP'), # test case id: 1xxxx
    ('NU_HU_NFCP', 'NU -> HU non-FCP'), # test case id: 2xxxx
    ('HU_HU_NFCP', 'HU -> HU non-FCP'), # test case id: 3xxxx
#    ('HU_HU_FCP', 'HU -> HU FCP'),      # test case id: 4xxxx
#    ('NU2HU_NFCP', 'NU <-> HU non-FCP'),  # TODO: enable it
])
TOOLS = ('netperf',)
PROTOCOLS = ('tcp', )  # TODO: add UDP
FRAME_SIZES = (1500,)  # It's actually IP packet size in bytes
NUM_FLOWS = (1, 8,)  # TODO: May add more
NUM_HOSTS = (1, 2,)  # Number of PCIe hosts, TODO: may keep 2 hosts only in the future
FPG_MTU_DEFAULT = 1518
PERF_RESULT_KEYS = (nm.THROUGHPUT,
                    nm.PPS,
                    nm.LATENCY_MIN,
                    nm.LATENCY_AVG,
                    nm.LATENCY_MAX,
                    nm.LATENCY_P50,
                    nm.LATENCY_P90,
                    nm.LATENCY_P99,
                    )
FPG_INTERFACES = (0, 4,)


class FunethPerformance(sanity.FunethSanity):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. In NU and HU hosts, run netserver
        2. In NU and HU host, do throughput/latency test with 64B/800B/1500B frame sizes - a. NU->HU,  b. HU->NU, c. HU->HU
        """)

    def setup(self):
        super(FunethPerformance, self).setup()

        tb_config_obj = tb_configs.TBConfigs(TB)
        funeth_obj = funeth.Funeth(tb_config_obj)
        linux_objs = funeth_obj.linux_obj_dict.values()

        fun_test.log("Configure irq affinity")
        for hu in funeth_obj.hu_hosts:
            funeth_obj.configure_irq_affinity(hu, tx_or_rx='tx')
            # TODO: Configure irq affinity for rx

        self.netperf_manager_obj = nm.NetperfManager(linux_objs)
        fun_test.test_assert(self.netperf_manager_obj.setup(), 'Set up for throughput/latency test')

        network_controller_objs = []
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT, verbose=True))
        network_controller_objs.append(NetworkController(dpc_server_ip=sanity.DPC_PROXY_IP,
                                                         dpc_server_port=sanity.DPC_PROXY_PORT2, verbose=True))
        # Configure small DF/Non-FCP thr to workaround SWOS-4771
        for nc_obj in network_controller_objs:
            buffer_pool_set = nc_obj.set_qos_egress_buffer_pool(df_thr=256,
                                                                nonfcp_thr=256,
                                                                nonfcp_xoff_thr=128,
                                                                mode='nu')
            fun_test.test_assert(buffer_pool_set, 'Configure QoS egress buffer pool')

        fun_test.shared_variables['funeth_obj'] = funeth_obj
        fun_test.shared_variables['network_controller_objs'] = network_controller_objs
        fun_test.shared_variables['netperf_manager_obj'] = self.netperf_manager_obj

    def cleanup(self):
        super(FunethPerformance, self).cleanup()
        #fun_test.test_assert(self.iperf_manager_obj.cleanup(), 'Clean up')
        fun_test.test_assert(self.netperf_manager_obj.cleanup(), 'Clean up')


netstats_dict = {}
mpstat_dict = {}


def collect_stats(fpg_interfaces, linux_objs, version, when='before', duration=0):

    tc_id = fun_test.current_test_case_id
    network_controller_objs = fun_test.shared_variables['network_controller_objs']

    # funeth interface interrupts
    funeth_obj = fun_test.shared_variables['funeth_obj']
    for hu in funeth_obj.hu_hosts:
        funeth_obj.get_interrupts(hu)

    ## netstat
    #fun_test.log("Capture netstat {} test".format(when))
    #netstats_dict[when] = {}
    #for linux_obj in linux_objs:
    #    netstats_dict[when].update(
    #        {linux_obj.host_ip: helper.get_netstat_output(linux_obj=linux_obj)}
    #    )

    # It generates too much log, in a loop? Disable it before it's fixed.
    ## peek resource/pc/[1], and peek resource/pc/[1]
    #for nc_obj in network_controller_objs:
    #    for pc_id in (1, 2):
    #        checkpoint = "Peek stats resource pc {} {} test".format(pc_id, when)
    #        resource_pc_temp_filename = '{}_F1_{}_resource_pc_{}_{}.txt'.format(str(version),
    #                                                                            network_controller_objs.index(nc_obj),
    #                                                                            pc_id, when)
    #        fun_test.simple_assert(helper.populate_pc_resource_output_file(network_controller_obj=nc_obj,
    #                                                                       filename=resource_pc_temp_filename,
    #                                                                       pc_id=pc_id, display_output=False),
    #                               checkpoint)

    ## flow list TODO: Enable flow list for specific type after SWOS-4849 is resolved
    #checkpoint = "Get Flow list {} test".format(when)
    #network_controller_objs = fun_test.shared_variables['network_controller_objs']
    #for nc_obj in network_controller_objs:
    #    fun_test.log_module_filter("random_module")
    #    output = nc_obj.get_flow_list()
    #    fun_test.sleep("Waiting for flow list cmd dump to complete", seconds=2)
    #    fun_test.log_module_filter_disable()
    #    flowlist_temp_filename = '{}_F1_{}_flowlist_{}.txt'.format(str(version), network_controller_objs.index(nc_obj),
    #                                                               when)
    #    fun_test.simple_assert(
    #        helper.populate_flow_list_output_file(result=output['data'], filename=flowlist_temp_filename),
    #        checkpoint)

    ## mpstat
    #for linux_obj in linux_objs:
    #    h = linux_obj.host_ip
    #    mpstat_temp_filename = '{}_{}_mpstat_{}.txt'.format(str(version), tc_id, str(h))
    #    mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)
    #    if when == 'before':
    #        fun_test.log("Starting to run mpstat command")
    #        mp_out = helper.run_mpstat_command(linux_obj=linux_obj, interval=2,
    #                                           output_file=mpstat_output_file, bg=True, count=duration+5)
    #        fun_test.log('mpstat cmd process id: %s' % mp_out)
    #        fun_test.add_checkpoint("Started mpstat command in {}".format(h))
    #    elif when == 'after':
    #        # Scp mpstat json to LOGS dir
    #        fun_test.log_module_filter("random_module")
    #        helper.populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=linux_obj,
    #                                           dump_filename=mpstat_temp_filename)
    #        fun_test.log_module_filter_disable()
    #
    #if when == 'after':
    #    # Get diff netstat
    #    for h in netstats_dict['after']:
    #        diff_netstat = helper.get_diff_stats(old_stats=netstats_dict['before'][h],
    #                                             new_stats=netstats_dict['after'][h])
    #        netstat_temp_filename = '{}_{}_netstat_{}.txt'.format(str(version), tc_id, str(h))
    #        populate = helper.populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
    #        fun_test.test_assert(populate, "Populate {} netstat into txt file".format(h))
    #
    fpg_stats = {}
    for nc_obj in network_controller_objs:
        f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
        fun_test.log('{} dpc: echo hello'.format(f1))
        nc_obj.echo_hello()
        if not fpg_stats:
            for i in fpg_interfaces:
                fun_test.log('{} dpc: Get FPG stats'.format(f1))
                r = nc_obj.peek_fpg_port_stats(port_num=i)
                # TODO: handle None
                #if not r:
                #    r = [{}]
                fpg_stats.update(
                    {i: r}
                )

        # Check parser stuck
        fun_test.log('{} dpc: Get parser stats'.format(f1))
        output = nc_obj.peek_parser_stats().get('global')
        for blk in output:
            eop_cnt = output[blk].get('eop_cnt')
            prv_sent = output[blk].get('prv_sent')
            if eop_cnt != prv_sent:
                fun_test.test_assert(False, '{} parser is stuck'.format(blk))

        fun_test.log('{} dpc: Get PSW stats'.format(f1))
        nc_obj.peek_psw_global_stats()
        fun_test.log('{} dpc: Get FCB stats'.format(f1))
        nc_obj.peek_fcp_global_stats()
        fun_test.log('{} dpc: Get VP pkts stats'.format(f1))
        nc_obj.peek_vp_packets()

        # Check VP stuck
        is_vp_stuck = False
        for pc_id in (1, 2):
            fun_test.log('{} dpc: Get resource PC {} stats'.format(f1, pc_id))
            output = nc_obj.peek_resource_pc_stats(pc_id=pc_id)
            for core_str, val_dict in output.items():
                if any(val_dict.values()) != 0:  # VP stuck
                    core, vp = [int(i) for i in re.match(r'CORE:(\d+) VP:(\d+)', core_str).groups()]
                    vp_no = pc_id * 24 + core * 4 + vp
                    nc_obj.debug_vp_state(vp_no=vp_no)
                    nc_obj.debug_backtrace(vp_no=vp_no)
                    is_vp_stuck = True
        if is_vp_stuck:
            fun_test.test_assert(False, 'VP is stuck')
        #nc_obj.peek_per_vp_stats()
        fun_test.log('{} dpc: Get resource BAM stats'.format(f1))
        nc_obj.peek_resource_bam_stats()
        fun_test.log('{} dpc: Get EQM stats'.format(f1))
        nc_obj.peek_eqm_stats()
        fun_test.log('{} dpc: Get resource nux stats'.format(f1))
        nc_obj.peek_resource_nux_stats()
    fpg_rx_bytes = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_OctetsReceivedOK'.format(i), 0) for i in fpg_interfaces]
    )
    fpg_rx_pkts = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_aFramesReceivedOK'.format(i), 0) for i in fpg_interfaces]
    )
    fpg_tx_bytes = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_OctetsTransmittedOK'.format(i), 0) for i in fpg_interfaces]
    )
    fpg_tx_pkts = sum(
        [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_aFramesTransmittedOK'.format(i), 0) for i in fpg_interfaces]
    )
    return fpg_tx_pkts, fpg_tx_bytes, fpg_rx_pkts, fpg_rx_bytes


class FunethPerformanceBase(FunTestCase):
    def describe(self):
        pass

    def setup(self):
        pass

    def cleanup(self):
        if TB == 'SN2':
            interval = 60
        else:
            interval = 5
        fun_test.sleep("Waiting for buffer drain to run next test case", seconds=interval)

    def _run(self, flow_type, tool='netperf', protocol='tcp', num_flows=1, num_hosts=1, frame_size=1500, duration=30):
        funeth_obj = fun_test.shared_variables['funeth_obj']
        perf_manager_obj = fun_test.shared_variables['netperf_manager_obj']

        host_pairs = []
        bi_dir = False
        if flow_type.startswith('HU_HU'):  # HU --> HU
            # TODO: handle exception if hu_hosts len is 1
            num_hu_hosts = len(funeth_obj.hu_hosts)
            if flow_type == 'HU_HU_NFCP':
                for i in range(0, num_hu_hosts, 2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i+1]])
            elif flow_type == 'HU_HU_FCP':
                for i in range(0, num_hu_hosts/2):
                    host_pairs.append([funeth_obj.hu_hosts[i], funeth_obj.hu_hosts[i + 2]])
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
        for shost, dhost in host_pairs:
            linux_obj_src = funeth_obj.linux_obj_dict[shost]
            linux_obj_dst = funeth_obj.linux_obj_dict[dhost]
            dip = funeth_obj.tb_config_obj.get_interface_ipv4_addr(dhost,
                                                                   funeth_obj.tb_config_obj.get_an_interface(dhost))

            # Check dip pingable - IP header 20B, ICMP header 8B
            ping_result = linux_obj_src.ping(dip, count=5, max_percentage_loss=20, size=frame_size-20-8)

            fun_test.test_assert(ping_result, '{} ping {} with packet size {}'.format(
                linux_obj_src.host_ip, dip, frame_size))

            suffix = '{}2{}'.format(shost[0], dhost[0])
            arg_dicts.append(
                {'linux_obj': linux_obj_src,
                 'linux_obj_dst': linux_obj_dst,
                 'dip': dip,
                 'tool': tool,
                 'protocol': protocol,
                 'num_flows': num_flows/len(host_pairs) if not bi_dir else num_flows/(len(host_pairs)/2),
                 'duration': duration,
                 'frame_size': frame_size + 18,  # Pass Ethernet frame size
                 'suffix': suffix,
                 }
            )

        #linux_objs = [arg_dict.get('linux_obj') for arg_dict in arg_dicts] + [arg_dict.get('linux_obj_dst') for arg_dict in arg_dicts]
        #linux_objs = funeth_obj.linux_obj_dict.values()
        #perf_manager_obj = NetperfManager(linux_objs)

        # Collect stats before and after test run
        version = fun_test.get_version()
        fun_test.log('Collect stats before test')
        fpg_tx_pkts1, _, fpg_rx_pkts1, _ = collect_stats(FPG_INTERFACES[:num_hosts],
                                                         funeth_obj.linux_obj_dict.values(),
                                                         version,
                                                         when='before',
                                                         duration=duration)
        result = perf_manager_obj.run(*arg_dicts)
        fun_test.log('Collect stats after test')
        fpg_tx_pkts2, _, fpg_rx_pkts2, _ = collect_stats(FPG_INTERFACES[:num_hosts],
                                                         funeth_obj.linux_obj_dict.values(),
                                                         version,
                                                         when='after')
        if result:  # Only if perf_manager has valid result, we update pps; otherwise, it's meaningless
            if flow_type.startswith('NU_HU') and result.get('{}_n2h'.format(nm.THROUGHPUT)) != nm.NA:
                result.update(
                    {'{}_n2h'.format(nm.PPS): (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
                )
            elif flow_type.startswith('NU2HU'):
                if result.get('{}_n2h'.format(nm.THROUGHPUT)) != nm.NA:
                    result.update(
                        {'{}_n2h'.format(nm.PPS): (fpg_rx_pkts2 - fpg_rx_pkts1) / duration}
                    )
                if result.get('{}_h2n'.format(nm.THROUGHPUT)) != nm.NA:
                    result.update(
                        {'{}_h2n'.format(nm.PPS): (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
                    )
            elif flow_type.startswith('HU_NU') and result.get('{}_h2n'.format(nm.THROUGHPUT)) != nm.NA:
                result.update(
                    {'{}_h2n'.format(nm.PPS): (fpg_tx_pkts2 - fpg_tx_pkts1) / duration}
                )
            elif flow_type.startswith('HU_HU') and result.get('{}_h2h'.format(nm.THROUGHPUT)) != nm.NA:
                # HU -> HU via local F1, no FPG stats
                # HU -> HU via FCP, don't check FPG stats as it includes FCP request/grant pkts
                result.update(
                    {'{}_h2h'.format(nm.PPS): nm.calculate_pps(protocol, frame_size, result['throughput_h2h'])}
                )

        # Check test passed or failed
        fun_test.log('NetperfManager Results:\n{}'.format(pprint.pformat(result)))
        if not result:
            passed = False
        elif any(v == nm.NA for v in result.values()):
            passed = False
        else:
            passed = True

        # Set N/A for untested direction
        for suffix in suffixes:
            for k in PERF_RESULT_KEYS:
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
             'timestamp': '%s' % TIMESTAMP,  # Use same timestamp for all the results of same run, per John/Ashwin
             'version': version,
             }
        )
        fun_test.log('Final Results:\n{}'.format(pprint.pformat(result)))

        # Update file with result
        with open(RESULT_FILE) as f:
            r = json.load(f)
            r.append(result)

        with open(RESULT_FILE, 'w') as f:
            json.dump(r, f, indent=4, separators=(',', ': '), sort_keys=True)

        fun_test.test_assert(passed, 'Get throughput/pps/latency test result')


def create_testcases(id, summary, steps, flow_type, tool, protocol, num_flows, num_hosts, frame_size):

    class TmpClass(FunethPerformanceBase):

        def describe(self):
            self.set_test_details(id=id, summary=summary, steps=steps)

        def run(self):
            FunethPerformanceBase._run(self, flow_type, tool, protocol, num_flows, num_hosts, frame_size)

    return type('FunethPerformance_{}_{}B_{}_{}_{}flows'.format(flow_type.upper(),
                                                                frame_size,
                                                                protocol.upper(),
                                                                tool.upper(),
                                                                num_flows,
                                                                num_hosts),
                (TmpClass,), {})


if __name__ == "__main__":
    ts = FunethPerformance()
    tcs = []
    id = 1000  # x... - flow_type, .x.. - protocol, ..x. - frame size, ...x - num of flows
    for flow_type in FLOW_TYPES_DICT:
        for tool in TOOLS:
            sub_id_protocol = id
            for protocol in PROTOCOLS:
                sub_id_frame_size = sub_id_protocol
                for frame_size in FRAME_SIZES:
                    sub_id_num_flows = sub_id_frame_size
                    for num_flows in NUM_FLOWS:
                        for num_hosts in NUM_HOSTS:
                            summary = "{}: performance test by {}, with {}, {}-byte packets and {} flows in {} PCIe hosts".format(
                                FLOW_TYPES_DICT.get(flow_type), tool, protocol, frame_size, num_flows, num_hosts
                            )
                            steps = summary
                            #print sub_id_num_flows, summary
                            tcs.append(create_testcases(
                                sub_id_num_flows, summary, steps, flow_type, tool, protocol, num_flows, num_hosts, frame_size)
                            )
                            sub_id_num_flows += 1
                            if num_flows == 1 or flow_type == 'HU_HU_NFCP':
                                break
                    sub_id_frame_size += 10
                sub_id_protocol += 100
        id += 1000

    for tc in tcs:
        ts.add_test_case(tc())
    ts.run()

    with open(RESULT_FILE) as f:
        r = json.load(f)
        fun_test.log('Performance results:\n{}'.format(pprint.pformat(r)))
