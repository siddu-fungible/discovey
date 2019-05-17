from lib.system.fun_test import *
from lib.host.linux import *
from prettytable import PrettyTable
import yaml


TREX_BINARY_PATH = "~/trex-core/scripts"
TREX_BINARY = "./t-rex-64"
TREX_CONFIG_FILE = "/etc/trex_cfg.yaml"


class TrexManager(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password):
        Linux.__init__(self, host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)

    def execute_trex_command(self, cmd, timeout=60):
        result = None
        try:
            change_dir_command = "cd %s" % TREX_BINARY_PATH
            if self.check_file_directory_exists(path=TREX_BINARY_PATH):
                self.command(change_dir_command)
            else:
                raise Exception('TRex binary %s dir not found. or Ensure TRex is installed on host' % TREX_BINARY_PATH)
            result = self.sudo_command(command=cmd, timeout=timeout + 10)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_trex_cmd(self, astf_profile, cps_rate=30, duration=30, cpu=1, astf=True, output_file=None, bg=False,
                     latency=True, warmup_time=5, latency_packet_rate=100):
        cmd = None
        try:
            cmd = "%s -f %s -m %d -d %d -c %d " % (TREX_BINARY, astf_profile, cps_rate, duration, cpu)
            if latency:
                cmd += "-k %d -l %d " % (warmup_time, latency_packet_rate)
            if astf:
                cmd += "--astf"
            if bg:
                cmd = 'nohup ' + cmd
                cmd += r' > ' + output_file + " 2>&1 &"
            fun_test.log("TRex cmd formed: %s" % cmd)
        except Exception as ex:
            fun_test.critical(str(ex))
        return cmd

    def read_trex_output_summary(self, file_path):
        summary_contents = None
        try:
            contents = self.read_file(file_name=file_path)
            m = re.search(r'(summary\s+stats.*)', contents, re.DOTALL | re.IGNORECASE)
            if m:
                summary_contents = m.group(0)
        except Exception as ex:
            fun_test.critical(str(ex))
        return summary_contents

    def ensure_trex_config_correct(self, port_info):
        result = False
        try:
            if self.check_file_directory_exists(path=TREX_CONFIG_FILE):
                contents = self.read_file(file_name=TREX_CONFIG_FILE)
                yaml_data = yaml.load(contents)

                data = yaml_data[0]['port_info']
                for index in range(0, len(data)):
                    fun_test.test_assert_expected(expected=port_info[index]['dest_mac'],
                                                  actual=data[index]['dest_mac'],
                                                  message="Ensure dest mac is correct", ignore_on_success=True)

                    fun_test.test_assert_expected(expected=port_info[index]['src_mac'],
                                                  actual=data[index]['src_mac'],
                                                  message="Ensure dest mac is correct", ignore_on_success=True)
            else:
                fun_test.log('Warning: %s config file not present' % TREX_CONFIG_FILE)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def poll_for_trex_process(self, max_time=30):
        result = False
        try:
            timer = FunTimer(max_time=max_time)
            while not timer.is_expired():
                process_id = self.get_process_id_by_pattern(process_pat='t-rex')
                if not process_id:
                    result = True
                    break
                fun_test.sleep("TRex process running... process id: %s" % process_id, seconds=10)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_trex_summary_stats(self, summary_contents):
        summary_dict = {'client': {}, 'server': {}}
        try:
            total_pkt_drop = re.search(r'Total-pkt-drop\s+:\s+(\d+)', summary_contents, re.IGNORECASE)
            total_tx_bytes = re.search(r'Total-tx-bytes\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_tx_sw_bytes = re.search(r'Total-tx-sw-bytes\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_rx_bytes = re.search(r'Total-rx-bytes\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_tx_pkt = re.search(r'Total-tx-pkt\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_rx_pkt = re.search(r'Total-rx-pkt\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_sw_tx_pkt = re.search(r'Total-sw-tx-pkt\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_sw_err = re.search(r'Total-sw-err\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_arp_sent = re.search(r'Total\sarp\ssent\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            total_arp_recv = re.search(r'Total\sarp\sreceived\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            max_latency = re.search(r'maximum-latency\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)
            avg_latency = re.search(r'average-latency\s+:\s+(\d+)', summary_contents, re.DOTALL | re.IGNORECASE)

            # Client/Server stats
            m_active_flows = re.search(r'm_active_flows\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            m_est_flows = re.search(r'm_est_flows\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            m_tx_bw_l7_r = re.search(r'm_tx_bw_l7_r.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_rx_bw_l7_r = re.search(r'm_rx_bw_l7_r.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_tx_bw_l7_total_r = re.search(r'm_tx_bw_l7_total_r.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_tx_pps_r = re.search(r'm_tx_pps_r.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_rx_pps_r = re.search(r'm_rx_pps_r.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_avg_size = re.search(r'm_avg_size.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            m_tx_ratio = re.search(r'm_tx_ratio.*.(\d+.\d+).*.(\d+.\d)', summary_contents)
            tcps_conn_attempt = re.search(r'tcps_connattempt\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_connects = re.search(r'tcps_connects\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_closed = re.search(r'tcps_closed\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_segstimed = re.search(r'tcps_segstimed\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_rtt_updated = re.search(r'tcps_rttupdated\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_total_sent = re.search(r'tcps_sndtotal\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_ctrl_sent = re.search(r'tcps_sndctrl\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_acks_sent = re.search(r'tcps_sndacks\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_drops = re.search(r'tcps_drops\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            embryonic_tcp_conn_drops = re.search(r'tcps_conndrops\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_retransmit_syn_timeouts = re.search(r'tcps_rexmttimeo_syn\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_keepalive_timeouts = re.search(r'tcps_keeptimeo\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)
            tcps_conn_keepalive_drops = re.search(r'tcps_keepdrops\s+\|\s+(\d+)\s+\|\s+(\d+)', summary_contents)

            if total_pkt_drop:
                summary_dict['total_pkt_drop'] = int(total_pkt_drop.group(1))

            if total_tx_bytes:
                summary_dict['total_tx_bytes'] = int(total_tx_bytes.group(1))

            if total_tx_sw_bytes:
                summary_dict['total_tx_sw_bytes'] = int(total_tx_sw_bytes.group(1))

            if total_rx_bytes:
                summary_dict['total_rx_bytes'] = int(total_rx_bytes.group(1))

            if total_tx_pkt:
                summary_dict['total_tx_pkt'] = int(total_tx_pkt.group(1))

            if total_rx_pkt:
                summary_dict['total_rx_pkt'] = int(total_rx_pkt.group(1))

            if total_sw_tx_pkt:
                summary_dict['total_sw_tx_pkt'] = int(total_sw_tx_pkt.group(1))

            if total_sw_err:
                summary_dict['total_sw_err'] = int(total_sw_err.group(1))

            if total_arp_sent:
                summary_dict['total_arp_sent'] = int(total_arp_sent.group(1))

            if total_arp_recv:
                summary_dict['total_arp_recv'] = int(total_arp_recv.group(1))

            if max_latency:
                summary_dict['max_latency'] = int(max_latency.group(1))

            if avg_latency:
                summary_dict['avg_latency'] = int(avg_latency.group(1))

            # Client/Server stats
            if m_active_flows:
                summary_dict['client']['m_active_flows'] = int(m_active_flows.group(1))
                summary_dict['server']['m_active_flows'] = int(m_active_flows.group(2))

            if m_est_flows:
                summary_dict['client']['m_est_flows'] = int(m_est_flows.group(1))
                summary_dict['server']['m_est_flows'] = int(m_est_flows.group(2))

            if m_tx_bw_l7_r:
                summary_dict['client']['m_tx_bw_l7_r'] = float(m_tx_bw_l7_r.group(1))
                summary_dict['server']['m_tx_bw_l7_r'] = float(m_tx_bw_l7_r.group(2))

            if m_rx_bw_l7_r:
                summary_dict['client']['m_rx_bw_l7_r'] = float(m_rx_bw_l7_r.group(1))
                summary_dict['server']['m_rx_bw_l7_r'] = float(m_rx_bw_l7_r.group(2))

            if m_tx_bw_l7_total_r:
                summary_dict['client']['m_tx_bw_l7_total_r'] = float(m_tx_bw_l7_total_r.group(1))
                summary_dict['server']['m_tx_bw_l7_total_r'] = float(m_tx_bw_l7_total_r.group(2))

            if m_tx_pps_r:
                summary_dict['client']['m_tx_pps_r'] = float(m_tx_pps_r.group(1))
                summary_dict['server']['m_tx_pps_r'] = float(m_tx_pps_r.group(2))

            if m_rx_pps_r:
                summary_dict['client']['m_rx_pps_r'] = float(m_rx_pps_r.group(1))
                summary_dict['server']['m_rx_pps_r'] = float(m_rx_pps_r.group(2))

            if m_avg_size:
                summary_dict['client']['m_avg_size'] = float(m_avg_size.group(1))
                summary_dict['server']['m_avg_size'] = float(m_avg_size.group(2))

            if m_tx_ratio:
                summary_dict['client']['m_tx_ratio'] = float(m_tx_ratio.group(1))
                summary_dict['server']['m_tx_ratio'] = float(m_tx_ratio.group(2))

            if tcps_conn_attempt:
                summary_dict['client']['tcps_conn_attempt'] = int(tcps_conn_attempt.group(1))
                summary_dict['server']['tcps_conn_attempt'] = int(tcps_conn_attempt.group(2))

            if tcps_connects:
                summary_dict['client']['tcps_connects'] = int(tcps_connects.group(1))
                summary_dict['server']['tcps_connects'] = int(tcps_connects.group(2))

            if tcps_segstimed:
                summary_dict['client']['tcps_segstimed'] = int(tcps_segstimed.group(1))
                summary_dict['server']['tcps_segstimed'] = int(tcps_segstimed.group(2))

            if tcps_rtt_updated:
                summary_dict['client']['tcps_rtt_updated'] = int(tcps_rtt_updated.group(1))
                summary_dict['server']['tcps_rtt_updated'] = int(tcps_rtt_updated.group(2))

            if tcps_total_sent:
                summary_dict['client']['tcps_total_sent'] = int(tcps_total_sent.group(1))
                summary_dict['server']['tcps_total_sent'] = int(tcps_total_sent.group(2))

            if tcps_ctrl_sent:
                summary_dict['client']['tcps_ctrl_sent'] = int(tcps_ctrl_sent.group(1))
                summary_dict['server']['tcps_ctrl_sent'] = int(tcps_ctrl_sent.group(2))

            if tcps_acks_sent:
                summary_dict['client']['tcps_acks_sent'] = int(tcps_acks_sent.group(1))
                summary_dict['server']['tcps_acks_sent'] = int(tcps_acks_sent.group(2))

            if tcps_drops:
                summary_dict['client']['tcps_drops'] = int(tcps_drops.group(1))
                summary_dict['server']['tcps_drops'] = int(tcps_drops.group(2))

            if tcps_closed:
                summary_dict['client']['tcps_closed'] = int(tcps_closed.group(1))
                summary_dict['server']['tcps_closed'] = int(tcps_closed.group(2))

            if embryonic_tcp_conn_drops:
                summary_dict['client']['embryonic_tcp_conn_drops'] = int(embryonic_tcp_conn_drops.group(1))
                summary_dict['server']['embryonic_tcp_conn_drops'] = int(embryonic_tcp_conn_drops.group(2))

            if tcps_retransmit_syn_timeouts:
                summary_dict['client']['tcps_retransmit_syn_timeouts'] = int(tcps_retransmit_syn_timeouts.group(1))
                summary_dict['server']['tcps_retransmit_syn_timeouts'] = int(tcps_retransmit_syn_timeouts.group(2))

            if tcps_keepalive_timeouts:
                summary_dict['client']['tcps_keepalive_timeouts'] = int(tcps_keepalive_timeouts.group(1))
                summary_dict['server']['tcps_keepalive_timeouts'] = int(tcps_keepalive_timeouts.group(2))

            if tcps_conn_keepalive_drops:
                summary_dict['client']['tcps_conn_keepalive_drops'] = int(tcps_conn_keepalive_drops.group(1))
                summary_dict['server']['tcps_conn_keepalive_drops'] = int(tcps_conn_keepalive_drops.group(2))
        except Exception as ex:
            fun_test.critical(str(ex))
        return summary_dict

    def pretty_print_summary_dict(self, summary_dict, table_header=None):
        try:
            if table_header:
                fun_test.log("\n<==========>  %s <==========>\n" % table_header)

            fun_test.log_disable_timestamps()
            table_obj = PrettyTable(['Field Name', 'Counter'])
            for key in summary_dict:
                inner_table = None
                if type(summary_dict[key]) == dict:
                    inner_table = PrettyTable(['Field Name', 'Counter'])
                    inner_table.align = 'l'
                    for _key in summary_dict[key]:
                        inner_table.add_row([_key, summary_dict[key][_key]])

                if inner_table:
                    table_obj.add_row([key, inner_table])
                else:
                    table_obj.add_row([key, summary_dict[key]])

            print table_obj
            fun_test.log_enable_timestamps()
        except Exception as ex:
            fun_test.critical(str(ex))
