from lib.system.fun_test import *
from scripts.networking.tcp import helper
from collections import OrderedDict
from prettytable import PrettyTable
import re


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
                                               output_file=mpstat_output_file, bg=True, count=duration+5)
            fun_test.log('mpstat cmd process id: %s' % mp_out)
            fun_test.add_checkpoint("Started mpstat command in {}".format(h))
        elif when == 'after':
            # Scp mpstat json to LOGS dir
            fun_test.log_module_filter("random_module")
            helper.populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=linux_obj,
                                               dump_filename=mpstat_temp_filename)
            fun_test.log_module_filter_disable()


def collect_dpc_stats(network_controller_objs, fpg_interfaces, version, when='before'):

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

    fpg_stats = {}
    for nc_obj in network_controller_objs:
        f1 = 'F1_{}'.format(network_controller_objs.index(nc_obj))
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