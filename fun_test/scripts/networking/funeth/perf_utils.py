from fun_global import PerfUnit
from lib.system.fun_test import *
from scripts.networking.tcp import helper
from web.fun_test.analytics_models_helper import ModelHelper
from collections import OrderedDict
from prettytable import PrettyTable
import json
import re


NETWORK_PC_LIST = (1, 2)
HU_ID_LIST = (1, 2, 3)


def get_diff_stats(old_stats, new_stats):
    result = {}
    try:
        for key, val in new_stats.iteritems():
            if isinstance(val, dict):
                result[key] = get_diff_stats(old_stats=old_stats[key], new_stats=new_stats[key])
            elif key in old_stats:
                try:
                    result[key] = int(new_stats[key]) - int(old_stats[key])
                except TypeError:
                    result[key] = None
            else:
                try:
                    result[key] = int(new_stats[key])
                except TypeError:
                    result[key] = None
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def populate_diff_output_file(diff_stats, filename, desc='ethtool stats'):
    output = False
    try:
        out_table = PrettyTable(diff_stats.keys())
        rows = []
        for key in diff_stats:
            inner_table = PrettyTable(['Name', 'Value'])
            inner_table.align = 'l'
            inner_table.border = False
            inner_table.header = False
            for _key, _val in sorted(diff_stats[key].iteritems()):
                inner_table.add_row([_key, _val])
            rows.append(inner_table)
        out_table.add_row(rows)

        lines = ['<=======> {} diff <=======>\n'.format(desc), out_table.get_string()]

        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'w') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=filename, filename=file_path)

        fun_test.log_disable_timestamps()
        fun_test.log_section('{} diff output'.format(desc))
        for line in lines:
            fun_test.log(line)
        fun_test.log_enable_timestamps()

        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


netstats_dict = {}
ethtool_stats_dict = {}


def collect_host_stats(funeth_obj, version, when='before', duration=0):

    tc_id = fun_test.current_test_case_id
    linux_objs = funeth_obj.linux_obj_dict.values()

    # funeth interface interrupts
    for hu in funeth_obj.hu_hosts:
        funeth_obj.get_interrupts(hu)

    # ethtool -S
    fun_test.log("Collect ethtool stats {} test".format(when))
    ethtool_stats_dict[when] = {}
    for hu in funeth_obj.hu_hosts:
        output = funeth_obj.get_ethtool_stats(hu).values()[0]  # TODO: assume there is one funeth intf per host
        linux_obj = funeth_obj.linux_obj_dict[hu]
        ethtool_stats_dict[when].update(
            {linux_obj.host_ip: {'NIC statistics': dict(OrderedDict(re.findall(r'(\S+):\s+(\d+)', output)))}}
        )

    # netstat
    fun_test.log("Collect netstat {} test".format(when))
    netstats_dict[when] = {}
    for linux_obj in linux_objs:
        netstats_dict[when].update(
            {linux_obj.host_ip: helper.get_netstat_output(linux_obj=linux_obj)}
        )

    if when == 'after':
        # Get diff netstat
        for h in netstats_dict['after']:
            fun_test.log_module_filter("random_module")
            diff_netstat = helper.get_diff_stats(old_stats=netstats_dict['before'][h],
                                                 new_stats=netstats_dict['after'][h])
            netstat_temp_filename = '{}_{}_netstat_{}.txt'.format(str(version), tc_id, str(h))
            populate = helper.populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
            fun_test.log_module_filter_disable()
            fun_test.test_assert(populate, "Populate {} netstat into txt file".format(h))

        # Get diff ethtool stats
        for h in ethtool_stats_dict['after']:
            fun_test.log_module_filter("random_module")
            diff_ethtool_stats = helper.get_diff_stats(old_stats=ethtool_stats_dict['before'][h],
                                                       new_stats=ethtool_stats_dict['after'][h])
            ethtool_temp_filename = '{}_{}_ethtool_stats_{}.txt'.format(str(version), tc_id, str(h))
            populate = populate_diff_output_file(diff_stats=diff_ethtool_stats, filename=ethtool_temp_filename)
            fun_test.log_module_filter_disable()
            fun_test.test_assert(populate, "Populate {} ethtool stats into txt file".format(h))

    # mpstat
    for linux_obj in linux_objs:
        h = linux_obj.host_ip
        mpstat_temp_filename = '{}_{}_mpstat_{}.txt'.format(str(version), tc_id, str(h))
        mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)
        if when == 'before':
            fun_test.log("Starting to run mpstat command")
            mp_out = helper.run_mpstat_command(linux_obj=linux_obj, interval=2,
                                               output_file=mpstat_output_file, bg=True, count=duration/2)
            fun_test.log('mpstat cmd process id: %s' % mp_out)
            fun_test.add_checkpoint("Started mpstat command in {}".format(h))
        elif when == 'after':
            # Scp mpstat json to LOGS dir
            fun_test.log('Populating mpstat %s' % mpstat_output_file)
            fun_test.log_module_filter("random_module")
            helper.populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=linux_obj,
                                               dump_filename=mpstat_temp_filename)
            fun_test.log_module_filter_disable()


def collect_dpc_stats(network_controller_objs, fpg_interfaces, fpg_intf_dict,  version, when='before'):
    """Collect DPC stats and return if something is stuck."""

    tc_id = fun_test.current_test_case_id

    # peek resource/pc/[1], and peek resource/pc/[1]
    #for nc_obj in network_controller_objs:
    #    for pc_id in (1, 2):
    #        fun_test.log_module_filter("random_module")
    #        checkpoint = "Peek stats resource pc {} {} test".format(pc_id, when)
    #        resource_pc_temp_filename = '{}_F1_{}_resource_pc_{}_{}.txt'.format(str(version),
    #                                                                            network_controller_objs.index(nc_obj),
    #                                                                            pc_id, when)
    #        res_result = helper.populate_pc_resource_output_file(network_controller_obj=nc_obj,
    #                                                             filename=resource_pc_temp_filename,
    #                                                             pc_id=pc_id, display_output=False)
    #        fun_test.log_module_filter_disable()
    #        fun_test.simple_assert(res_result, checkpoint)

    # flow list TODO: Enable flow list for specific type after SWOS-4849 is resolved
    #checkpoint = "Get Flow list {} test".format(when)
    #for nc_obj in network_controller_objs:
    #    fun_test.log_module_filter("random_module")
    #    output = nc_obj.get_flow_list(timeout=180).get('data')
    #    fun_test.sleep("Waiting for flow list cmd dump to complete", seconds=10)
    #    fun_test.log_module_filter_disable()
    #    flowlist_temp_filename = '{}_{}_F1_{}_flowlist_{}.txt'.format(str(version), tc_id,
    #                                                                  network_controller_objs.index(nc_obj), when)
    #    file_path = fun_test.get_test_case_artifact_file_name(flowlist_temp_filename)
    #    with open(file_path, 'w') as f:
    #        json.dump(output, f, indent=4, separators=(',', ': '), sort_keys=True)
    #    fun_test.add_auxillary_file(description=flowlist_temp_filename, filename=file_path)
    #
    fpg_stats = {}
    is_vp_stuck = False
    is_parser_stuck = False
    is_etp_queue_stuck = False
    is_flow_blocked = False
    is_eqm_not_dequeued = False
    is_wropkt_timeout_skip = False
    for nc_obj in network_controller_objs:
        output_list = []
        f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
        if not fpg_stats:
            for i in fpg_interfaces:
                fun_test.log('{} dpc: Get FPG stats'.format(f1))
                r = nc_obj.peek_fpg_port_stats(port_num=i)
                output_list.append({'FPG{}'.format(i): r})
                # TODO: handle None
                #if not r:
                #    r = [{}]
                fpg_stats.update(
                    {i: r}
                )

        # Check FPG stats
        for i in fpg_intf_dict.get(f1):
            fun_test.log('{} dpc: Get FPG {} stats'.format(f1, i))
            output = nc_obj.peek_fpg_port_stats(port_num=i)
            output_list.append({'FPG{}'.format(i): output})

        # Check parser stuck
        fun_test.log('{} dpc: Get parser stats'.format(f1))
        output = nc_obj.peek_parser_stats().get('global')
        output_list.append({'Parser': output})
        for blk in output:
            eop_cnt = output[blk].get('eop_cnt')
            prv_sent = output[blk].get('prv_sent')
            if eop_cnt != prv_sent:
                is_parser_stuck = True

        # VP pkt stats
        fun_test.log('{} dpc: Get VP pkts stats'.format(f1))
        output = nc_obj.peek_vp_packets()
        output_list.append({'VP': output})

        # Per VP pkt stats
        for pc_id in NETWORK_PC_LIST:
            fun_test.log('{} dpc: Get per VP pkts stats from PC {}'.format(f1, pc_id))
            output = nc_obj.peek_per_vppkts_stats(pc_id)
            output_list.append({'Per VP for PC {}'.format(pc_id): output})

        # Per VP WU stats
        fun_test.log('{} dpc: Get per_vp WU stats from'.format(f1, pc_id))
        output = nc_obj.peek_per_vp_stats()
        output_list.append({'per_vp': output})

        # NWQM
        #fun_test.log('{} dpc: Get NWQM stats'.format(f1))
        #output = nc_obj.peek_nwqm_stats()
        #output_list.append({'WQM': output})

        # ETP
        fun_test.log('{} dpc: Get ETP stats'.format(f1))
        output = nc_obj.peek_etp_stats()
        output_list.append({'ETP': output})

        # FCB
        fun_test.log('{} dpc: Get FCB stats'.format(f1))
        output = nc_obj.peek_fcp_global_stats()
        output_list.append({'FCB': output})

        # FCP tunnel
        tunnel_id = 195
        fun_test.log('{} dpc: Get FCP tunnel {} stats'.format(f1, tunnel_id))
        output = nc_obj.peek_fcp_tunnel_stats(tunnel_id)
        output_list.append({'FCP tunnel {}'.format(tunnel_id): output})

        # PSW
        fun_test.log('{} dpc: Get PSW stats'.format(f1))
        output = nc_obj.peek_psw_global_stats()
        output_list.append({'PSW': output})

        # ERP
        fun_test.log('{} dpc: Get ERP stats'.format(f1))
        output = nc_obj.peek_erp_global_stats()
        output_list.append({'ERP': output})

        # WRO - Check WROPKT_TIMEOUT_SKIP
        fun_test.log('{} dpc: Get WRO stats'.format(f1))
        output = nc_obj.peek_wro_global_stats()
        output_list.append({'WRO': output})
        #if output['global'].get('WROPKT_TIMEOUT_SKIP'):
        #    is_wropkt_timeout_skip = True

        # WRO tunnel
        fun_test.log('{} dpc: Get WRO tunnel {} stats'.format(f1, tunnel_id))
        output = nc_obj.peek_wro_tunnel_stats(tunnel_id)
        output_list.append({'WRO tunnel {}'.format(tunnel_id): output})

        # BM
        #fun_test.log('{} dpc: Get resource BAM stats'.format(f1))
        #output = nc_obj.peek_resource_bam_stats()
        #output_list.append({'BM': output})

        # EQM
        fun_test.log('{} dpc: Get EQM stats'.format(f1))
        eqm_output = nc_obj.peek_eqm_stats()
        output_list.append({'EQM': eqm_output})

        # Check VP stuck
        for pc_id in NETWORK_PC_LIST:
            fun_test.log('{} dpc: Get resource PC {} stats'.format(f1, pc_id))
            output = nc_obj.peek_resource_pc_stats(pc_id=pc_id)
            output_list.append({'resource pc {}'.format(pc_id): output})
            for core_str, val_dict in output.items():
                if any(val_dict.values()) != 0:  # VP stuck
                    core, vp = [int(i) for i in re.match(r'CORE:(\d+) VP:(\d+)', core_str).groups()]
                    vp_no = pc_id * 24 + core * 4 + vp
                    nc_obj.debug_vp_state(vp_no=vp_no)
                    nc_obj.debug_backtrace(vp_no=vp_no)
                    is_vp_stuck = True

        # Check ETP queue stuck
        fun_test.log('{} dpc: Get resource nux stats'.format(f1))
        output = nc_obj.peek_resource_nux_stats()
        output_list.append({'resource nux': output})
        if output:
            is_etp_queue_stuck = True

        # Check flow blocked
        fun_test.log('{} dpc: flow blocked'.format(f1))
        output = nc_obj.flow_list(blocked_only=True)
        output_list.append({'flow blocked': output})
        if output:
            is_flow_blocked = True
            for hu_fn in output:
                for flow_t in output.get(hu_fn):
                    for blocked_dict in output.get(hu_fn).get(flow_t):
                        if 'callee_dest' in blocked_dict:
                            fun_test.log('{} dpc: flow blocked {} {} has callee_dest'.format(f1, hu_fn, flow_t))
                            fabric_addr = blocked_dict.get('callee_dest')
                            pc_id, vp = [int(i) for i in re.match(r'FA(\d+):(\d+):\d+', fabric_addr).groups()]
                            vp_no = pc_id * 24 + (vp - 8)
                            nc_obj.debug_vp_state(vp_no=vp_no)
                            nc_obj.debug_backtrace(vp_no=vp_no)
                        else:
                            fun_test.log('{} dpc: flow blocked {} {} has no callee_dest'.format(f1, hu_fn, flow_t))

        # Flow list
        for huid in HU_ID_LIST:
            output = nc_obj.flow_list(huid=huid)
            output_list.append({'flow list {}'.format(huid): output})

        # cdu stats
        fun_test.log('{} dpc: Get cdu stats'.format(f1))
        output = nc_obj.peek_cdu_stats()
        output_list.append({'cdu': output})

        # ca stats
        #fun_test.log('{} dpc: Get ca stats'.format(f1))
        #output = nc_obj.peek_ca_stats()
        #output_list.append({'ca': output})

        # Upload stats output file
        dpc_stats_filename = '{}_{}_{}_dpc_stats_{}.txt'.format(str(version), tc_id, f1, when)
        file_path = fun_test.get_test_case_artifact_file_name(dpc_stats_filename)
        with open(file_path, 'w') as f:
            json.dump(output_list, f, indent=4, separators=(',', ': '), sort_keys=True)
            fun_test.add_auxillary_file(description=dpc_stats_filename, filename=file_path)

    #fpg_rx_bytes = sum(
    #    [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_OctetsReceivedOK'.format(i), 0) for i in fpg_interfaces]
    #)
    #fpg_rx_pkts = sum(
    #    [fpg_stats[i][0].get('port_{}-PORT_MAC_RX_aFramesReceivedOK'.format(i), 0) for i in fpg_interfaces]
    #)
    #fpg_tx_bytes = sum(
    #    [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_OctetsTransmittedOK'.format(i), 0) for i in fpg_interfaces]
    #)
    #fpg_tx_pkts = sum(
    #    [fpg_stats[i][0].get('port_{}-PORT_MAC_TX_aFramesTransmittedOK'.format(i), 0) for i in fpg_interfaces]
    #)

    for nc_obj in network_controller_objs:
        nc_obj.disconnect()

    if is_vp_stuck or is_parser_stuck or is_etp_queue_stuck or is_flow_blocked or is_wropkt_timeout_skip:
        if eqm_output.get(
                "EFI->EQC Enqueue Interface valid", None) != eqm_output.get("EQC->EFI Dequeue Interface valid", None):
            is_eqm_not_dequeued = True
        messages = []
        if is_vp_stuck:
            messages.append('VP is stuck')
        if is_parser_stuck:
            messages.append('Parser is stuck')
        if is_etp_queue_stuck:
            messages.append('ETP queue is stuck')
        if is_flow_blocked:
            messages.append('Flow blocked')
        if is_eqm_not_dequeued:
            messages.append('EQM not dequeued')
        if is_wropkt_timeout_skip:
            messages.append('WROPKT_TIMEOUT_SKIP happened')
        fun_test.critical('; '.join(messages))

    return is_etp_queue_stuck, is_flow_blocked, is_parser_stuck, is_vp_stuck, is_wropkt_timeout_skip
    #return fpg_tx_pkts, fpg_tx_bytes, fpg_rx_pkts, fpg_rx_bytes


def populate_result_summary(tc_ids, results, funsdk_commit, funsdk_bld, driver_commit, driver_bld, filename):
    """Populate result summary file.

    :param tc_ids: list of test case id.
    :param results: list of dict. One element is like below.

        {
        "flow_type": "HU_HU_NFCP",
        "frame_size": 1500,
        "latency_P50_h2h": 34.0,
        "latency_P50_h2n": -1,
        "latency_P50_n2h": -1,
        "latency_P90_h2h": 35.0,
        "latency_P90_h2n": -1,
        "latency_P90_n2h": -1,
        "latency_P99_h2h": 36.0,
        "latency_P99_h2n": -1,
        "latency_P99_n2h": -1,
        "latency_avg_h2h": 34.2,
        "latency_avg_h2n": -1,
        "latency_avg_n2h": -1,
        "latency_max_h2h": 78.0,
        "latency_max_h2n": -1,
        "latency_max_n2h": -1,
        "latency_min_h2h": 32.0,
        "latency_min_h2n": -1,
        "latency_min_n2h": -1,
        "num_flows": 8,
        "num_hosts": 1,
        "offloads": true,
        "pps_h2h": 1046038.05,
        "pps_h2n": -1,
        "pps_n2h": -1,
        "protocol": "TCP",
        "throughput_h2h": 12067.095,
        "throughput_h2n": -1,
        "throughput_n2h": -1,
        "timestamp": "2019-05-26 12:37:54.859905-07:00",
        "version": "6617-6-g60146766df",
    }

    :return: Bool
    """
    output = False
    try:
        ptable = PrettyTable()
        ptable.align = 'r'

        # field name: tc_id
        field_names = ['tc_id', ]
        field_names.extend(tc_ids)
        ptable.field_names = field_names

        # rows: flow_type, protocol, frame_size, num_flows, num_hosts
        row_name_keys = ['flow_type', 'protocol', 'frame_size', 'num_flows', 'num_hosts', 'offloads', ]
        rows0 = []
        for k in row_name_keys:
            row = [k, ]
            for result in results:
                row.append(result.get(k))
            rows0.append(row)
        for row in rows0:
            ptable.add_row(row)

        # rows: latency, pps, throughput
        r0 = results[0]
        rows = []
        for k in r0:
            if k.startswith('latency') or k.startswith('pps') or k.startswith('throughput'):
                row = [k, ]
                for result in results:
                    v = result.get(k)
                    if v == -1:
                        v = '.'
                    row.append(v)
                rows.append(row)

        for row in sorted(rows, key=lambda elem: elem[0]):
            ptable.add_row(row)

        funos_bld = r0.get('version')
        lines = ['FunOS: {}'.format(funos_bld),
                 'FunSDK: {} {}'.format(funsdk_commit, funsdk_bld),
                 'Driver: {} {}'.format(driver_commit, driver_bld),
                 ptable.get_string(),
                 'Note:',
                 '_h2n: HU to NU (Host to Network)',
                 '_n2h: NU to HU (Network to Host)',
                 '_h2h: HU to HU (Host to Host)']
        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))

        fun_test.add_auxillary_file(description=filename, filename=file_path)

        fun_test.log_disable_timestamps()
        fun_test.log_section('Summary of results')
        for line in lines:
            fun_test.log(line)
        fun_test.log_enable_timestamps()

        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


unit = {
    "latency_P50_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P50_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P50_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_P50_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P50_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P50_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_P90_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P90_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P90_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_P90_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P90_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P90_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_P99_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P99_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P99_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_P99_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_P99_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_P99_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_avg_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_avg_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_avg_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_avg_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_avg_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_avg_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_max_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_max_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_max_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_max_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_max_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_max_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_min_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_min_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_min_n2h_unit": PerfUnit.UNIT_USECS,
    "latency_min_uload_h2h_unit": PerfUnit.UNIT_USECS,
    "latency_min_uload_h2n_unit": PerfUnit.UNIT_USECS,
    "latency_min_uload_n2h_unit": PerfUnit.UNIT_USECS,
    "pps_h2h_unit": PerfUnit.UNIT_PPS,
    "pps_h2n_unit": PerfUnit.UNIT_PPS,
    "pps_n2h_unit": PerfUnit.UNIT_PPS,
    "throughput_h2h_unit": PerfUnit.UNIT_MBITS_PER_SEC,
    "throughput_h2n_unit": PerfUnit.UNIT_MBITS_PER_SEC,
    "throughput_n2h_unit": PerfUnit.UNIT_MBITS_PER_SEC,
}


def db_helper(results):
    """Write results to DB.

    :param results: list of result dict.
    :return:
    """

    model_names = ["HuThroughputPerformance", "HuLatencyPerformance", "HuLatencyUnderLoadPerformance"]
    for line in results:
        status = fun_test.PASSED
        try:
            for model_name in model_names:
                generic_helper = ModelHelper(model_name=model_name)
                generic_helper.set_units(validate=False, **unit)
                generic_helper.add_entry(**line)
                generic_helper.set_status(status)
        except Exception as ex:
            fun_test.critical(str(ex))
        #print "used generic helper to add an entry"


def mlx5_irq_affinity(linux_obj):
    """Set Mellanox ConnectX-5 NIC irq affinity."""
    cmd = 'cat /proc/interrupts | grep "mlx5"'
    output = linux_obj.command(cmd)
    irq_list = re.findall(r'(\d+):.*mlx5_comp', output)

    # cat irq affinity
    cmds_cat = []
    for i in irq_list:
        cmds_cat.append('cat /proc/irq/{}/smp_affinity'.format(i))
    linux_obj.command(';'.join(cmds_cat))

    # set irq affinity
    # TODO: here its' hardcoded to exclude cpu 15, which single flow netperf will run on
    cmds_chg = []
    for i in irq_list:
        cmds_chg.append('echo 7f00 > /proc/irq/{}/smp_affinity'.format(i))
    linux_obj.sudo_command(';'.join(cmds_chg))
    linux_obj.command(';'.join(cmds_cat))


def redis_del_fcp_ftep(linux_obj, ws='/scratch/opt/fungible'):
    """In redis, delete FCP FTEP to tear down FCP tunnel."""
    # TODO: make it setup independent
    ftep_dict = {
        'F1-0': r"openconfig-fcp:fcp-tunnel[ftep=\'9.0.0.2\']",
        'F1-1': r"openconfig-fcp:fcp-tunnel[ftep=\'9.0.0.1\']",
    }
    for k in ftep_dict:
        cmd_prefix = 'docker exec {} bash -c'.format(k)
        chk_file = 'check_{}'.format(k)
        del_file = 'del_{}'.format(k)

        # check
        contents = "SELECT 1 \nKEYS *fcp-tunnel*"
        linux_obj.command('{0} "rm {1}"'.format(cmd_prefix, chk_file))
        linux_obj.create_file('{}/{}'.format(ws, chk_file), contents=contents)
        linux_obj.command('{} "cat {}"'.format(cmd_prefix, chk_file))

        # del
        contents = "SELECT 1 \nDEL \"{}\"".format(ftep_dict[k])
        linux_obj.command('{0} "rm {1}"'.format(cmd_prefix, del_file))
        linux_obj.create_file('{}/{}'.format(ws, del_file), contents=contents)
        linux_obj.command('{} "cat {}"'.format(cmd_prefix, del_file))

        fun_test.log("Check and delete FCP FTEP to tear down FCP tunnel in {}".format(k))
        linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, chk_file))
        linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, del_file))
        linux_obj.command('{} "redis-cli < {}"'.format(cmd_prefix, chk_file))


def collect_funcp_logs(linux_obj, path='/scratch/opt/fungible/logs'):
    """Populate the FunCP log files to job log dir"""
    output = linux_obj.command('cd {}; ls -l *.log'.format(path))
    log_files = re.findall(r'(\S+.log)', output)
    for log_file in log_files:
        artifact_file_name = fun_test.get_test_case_artifact_file_name(
            post_fix_name='{}_{}.txt'.format(linux_obj.host_ip, log_file))
        fun_test.scp(source_ip=linux_obj.host_ip,
                     source_file_path='{}/{}'.format(path, log_file),
                     source_username=linux_obj.ssh_username,
                     source_password=linux_obj.ssh_password,
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(log_file), filename=artifact_file_name)

    linux_obj.command('rm -rf /scratch/opt/fungible/logs/CC_openr*')
