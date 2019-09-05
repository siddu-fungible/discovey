from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import copy
import re


network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
host_name1 = "nu-lab-06"
host_name2 = "nu-lab-04"
hosts_json_file = ASSET_DIR + "/hosts.json"
setup_fpg1_file = "setup_fpg12.sh"
setup_fpg0_file = "fpg0.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
setup_fpg0_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg0_file
TIMESTAMP = None
filename = "tcp_performance.json"
use_mpstat = True


def get_port_from_file(filepath):
    port_value = None
    try:
        read_op = fun_test.read_file(file_name=filepath)
        if read_op:
            read_op = read_op.split("\n")
            first_line = read_op[0]
            out = re.search(',[0-9]*', first_line)
            if out.group():
                port_value = int(out.group()[1:])
    except Exception as ex:
        fun_test.critical(str(ex))
    return port_value


class TcpPerformance(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup fpg on host
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global network_controller_obj, mode, TIMESTAMP

        TIMESTAMP = get_current_time()
        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(disable_f1_index=f1_index)
            fun_test.shared_variables['fs'] = fs
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')
        host_lists = ['nu-lab-04']
        for host in host_lists:
            linux_obj = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            linux_obj.reboot()

        for host in host_lists:
            linux_obj = Linux(host_ip=host, ssh_username="localadmin", ssh_password="Precious1*")
            count = 0
            while True:
                count += 1
                response = os.system("ping -c 1 " + host)
                if count > 10:
                    fun_test.test_assert(expression=False, message="Cannot reach host %s" % host)
                    break
                if response == 0:
                    if not linux_obj.check_ssh():
                        fun_test.sleep(message="Can ping host, but cannot SSH", seconds=15)
                        continue
                    else:
                        fun_test.log("Host %s reachable" % host)
                        break
                else:
                    fun_test.log("Cannot ping Host %s" % host)
                    fun_test.sleep(message="Cannot ping host", seconds=15)


        private_funos_branch = fun_test.get_build_parameter(parameter='BRANCH_FunOS')
        if private_funos_branch:
            fun_test.shared_variables['funos_branch'] = private_funos_branch

        speed = nu_config_obj.get_speed()
        mode = str(speed/1000) + "G"
        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        dut_config = nu_config_obj.read_dut_config()

        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=16383,
                                                                            nonfcp_xoff_thr=16383,
                                                                            df_thr=16383,
                                                                            dx_thr=16383,
                                                                            fcp_thr=12287,
                                                                            nonfcp_thr=256,
                                                                            sample_copy_thr=255,
                                                                            sf_thr=16383,
                                                                            sf_xoff_thr=4095,
                                                                            sx_thr=16383)
        fun_test.test_assert(buffer_pool_set, "Configure psw buffer")

        syslog = network_controller_obj.set_syslog_level(level=2)
        fun_test.simple_assert(syslog, "Set syslog level to 2")

        exec_app = network_controller_obj.execute_app(name=app)
        fun_test.test_assert(expression=exec_app['status'], message="Ensure TCP server App started")

        # Fetch hosts details
        host1_info = get_nu_lab_host(file_path=hosts_json_file, host_name=host_name1)
        fun_test.simple_assert(host1_info, 'Host info fetched')
        host1_username = host1_info['ssh_username']
        host1_ip = host1_info['host_ip']
        host1_password = host1_info['ssh_password']

        fun_test.shared_variables['host1_username'] = host1_username
        fun_test.shared_variables['host1_password'] = host1_password
        fun_test.shared_variables['host1_ip'] = host1_ip

        host2_info = get_nu_lab_host(file_path=hosts_json_file, host_name=host_name2)
        fun_test.simple_assert(host2_info, 'Host info fetched')
        host2_username = host2_info['ssh_username']
        host2_ip = host2_info['host_ip']
        host2_password = host2_info['ssh_password']

        fun_test.shared_variables['host2_username'] = host2_username
        fun_test.shared_variables['host2_password'] = host2_password
        fun_test.shared_variables['host2_ip'] = host2_ip

        fun_test.shared_variables['host1_obj'] = Linux(host_ip=host1_ip, ssh_username=host1_username,
                                                       ssh_password=host1_password)

        fun_test.shared_variables['host2_obj'] = Linux(host_ip=host2_ip, ssh_username=host2_username,
                                                       ssh_password=host2_password)

    def cleanup(self):
        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TcpPerformance1Conn(FunTestCase):
    default_frame_size = 1500
    test_run_time = 10
    duration = 60
    num_flows = 1
    netperf_remote_port = 4555

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance for 1 connection for 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 1 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name1)

    def setup(self):
        host1_ip = fun_test.shared_variables['host1_ip']
        host1_username = fun_test.shared_variables['host1_username']
        host1_password = fun_test.shared_variables['host1_password']
        host1_obj = fun_test.shared_variables['host1_obj']

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=host1_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)

        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=host1_ip, target_username=host1_username,
                                     target_password=host1_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, host1_ip))
        
        fun_test.sleep("Letting file be copied", seconds=1)

        # Execute sh file
        fun_test.log("Creating interface and applying routes")
        output = execute_shell_file(linux_obj=host1_obj, target_file=target_file_path)
        fun_test.simple_assert(output['result'], "Ensure file %s is executed" % target_file_path)

        fun_test.log("Display applied routes")
        host1_obj.get_ip_route()

    def run(self):
        host1_obj = fun_test.shared_variables['host1_obj']
        mpstat_obj = copy.deepcopy(host1_obj)

        test_parameters = {'dest_ip': '29.1.1.2', 'protocol': 'tcp', 'num_flows': self.num_flows,
                           'duration': self.duration, 'port1': 1000, 'port2': 4555, 'send_size': '128K'}

        branch_name = None
        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        version = fun_test.get_version()
        mpstat_temp_filename = str(version) + "_" + str(self.num_flows) + '_mpstat.txt'
        mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)

        tcpdump_temp_filename = str(version) + "_" + str(self.num_flows) + '_tcpdump.pcap'
        tcpdump_output_file = fun_test.get_temp_file_path(file_name=tcpdump_temp_filename)

        diff_netstat = None
        netstat_1 = None

        fun_test.log("Starting netperf test")
        cmd_list = get_netperf_cmd_list(dip=test_parameters['dest_ip'],
                                        duration=test_parameters['duration'],
                                        num_flows=test_parameters['num_flows'],
                                        send_size=test_parameters['send_size'])
        fun_test.simple_assert(cmd_list, 'Ensure netperf command formed')

        network_controller_obj.disconnect()
        cmd_dict = {host1_obj: cmd_list}
        throughput_list = []
        for iteration in range(0, 5):
            fun_test.add_checkpoint("<=====> Start iteration: %d  <=====>" % iteration)
            fun_test.log_section("Start iteration: %d" % iteration)
            collect_dpc_stats = False if iteration > 0 else True
            if iteration == 0:
                fun_test.add_checkpoint("Capture netstat before traffic for iteration %d" % iteration)
                netstat_1 = get_netstat_output(linux_obj=host1_obj)

                # Start mpstat
                if use_mpstat:
                    fun_test.log("Starting to run mpstat command")
                    mp_out = run_mpstat_command(linux_obj=mpstat_obj, interval=self.test_run_time,
                                                output_file=mpstat_output_file, bg=True, count=6)
                    fun_test.log('mpstat cmd process id: %s' % mp_out)
                    fun_test.add_checkpoint("Started mpstat command")

                checkpoint = "Start tcpdump capture in background before starting traffic"
                interface_name = get_interface_name(file_path=setup_fpg1_filepath)
                result = run_tcpdump_command(linux_obj=host1_obj, interface=interface_name,
                                             tcp_dump_file=tcpdump_output_file,
                                             count=100000, filecount=1)
                fun_test.simple_assert(result, checkpoint)
                fun_test.shared_variables['tcpdump_pid'] = result

            netperf_result = run_netperf_concurrently(cmd_dict=cmd_dict,
                                                      network_controller_obj=network_controller_obj,
                                                      display_output=False,
                                                      num_flows=self.num_flows, collect_dpc_stats=collect_dpc_stats)
            fun_test.simple_assert(netperf_result, 'Ensure result found')

            fun_test.sleep("Wait after traffic", seconds=self.test_run_time)

            if 'tcpdump_pid' in fun_test.shared_variables and iteration == 0:
                host1_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid']), sudo=True)

            if iteration == 0:
                fun_test.add_checkpoint("Capture netstat after traffic for iteration %d" % iteration)
                netstat_2 = get_netstat_output(linux_obj=host1_obj)
                diff_netstat = get_diff_stats(old_stats=netstat_1, new_stats=netstat_2)

            total_throughput = netperf_result['total_throughput']
            fun_test.add_checkpoint("ITERATION: %d Total throughput seen is %s" % (iteration, total_throughput))
            # TODO: We don't need to fail the case if total_throughput <= 0 instead put -1 in JSON and
            # TODO: Model so that it gets reflected on dashboard
            # fun_test.test_assert(total_throughput > 0.0, "Ensure some throughput is seen. Actual %s" %
            # total_throughput)

            throughput_list.append(total_throughput)

            pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
            fun_test.add_checkpoint("ITERATION: %d Total PPS value is %s" % (iteration, round(pps, 2)))

            fun_test.add_checkpoint("<=====> End iteration: %d  <=====>" % iteration)

        avg_throughput = sum(throughput_list) / len(throughput_list)
        avg_pps = get_pps_from_mbps(mbps=avg_throughput, byte_frame_size=self.default_frame_size)
        if avg_throughput <= 0.0 and avg_pps <= 0.0:
            avg_throughput = -1
            avg_pps = -1

        create_performance_table(total_throughput=avg_throughput, total_pps=round(avg_pps, 2),
                                 num_flows=self.num_flows)

        # Scp mpstat json to LOGS dir
        if use_mpstat:
            populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=mpstat_obj,
                                        dump_filename=mpstat_temp_filename)

        populate_tcpdump_redirect_file(dump_filename=tcpdump_temp_filename, version=version, num_flows=self.num_flows,
                                       host_name=host_name1, host_obj=host1_obj, source_file_path=tcpdump_output_file)

        # Get diff stats
        netstat_temp_filename = str(version) + "_" + str(self.num_flows) + '_netstat.txt'
        populate = populate_netstat_output_file(diff_stats=diff_netstat, filename=netstat_temp_filename)
        fun_test.test_assert(populate, "Populate netstat into txt file")

        # Parse output to get json
        if not branch_name:
            output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput",
                                                    frame_size=self.default_frame_size,
                                                    num_flows=self.num_flows,
                                                    throughput_n2t=avg_throughput, pps_n2t=avg_pps,
                                                    timestamp=TIMESTAMP,
                                                    filename=filename, model_name=TCP_PERFORMANCE_MODEL_NAME)
            fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        host1_obj = fun_test.shared_variables['host1_obj']

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=host1_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)

        if 'tcpdump_pid' in fun_test.shared_variables:
            host1_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid']), sudo=True)


class TcpPerformance4Conn(TcpPerformance1Conn):
    num_flows = 4
    perf_filename = "perf_4_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Tcp performance for 4 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 4 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name1)


class TcpPerformance8Conn(TcpPerformance1Conn):
    num_flows = 8

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Tcp performance for 8 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s
                              2. Run netperf file with 8 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """ % host_name1)


# 2 Hosts with 8 connections on each host
class TcpPerformance16Conn2Host(FunTestCase):
    default_frame_size = 1500
    test_run_time = 10
    duration = 60
    num_flows = 16
    netperf_remote_port = 4555

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test Tcp performance for 16 connection for 1500B stream",
                              steps="""
                              1. Setup fpg1 on %s and fpg0 on %s
                              2. Run netperf file with 8 connections on %s and 8 connections on %s
                              3. Update tcp_performance.json file with throughput and pps
                              """ % (host_name1, host_name2, host_name1, host_name2))

    def setup(self):
        host1_ip = fun_test.shared_variables['host1_ip']
        host1_username = fun_test.shared_variables['host1_username']
        host1_password = fun_test.shared_variables['host1_password']
        host1_obj = fun_test.shared_variables['host1_obj']

        host2_ip = fun_test.shared_variables['host2_ip']
        host2_username = fun_test.shared_variables['host2_username']
        host2_password = fun_test.shared_variables['host2_password']
        host2_obj = fun_test.shared_variables['host2_obj']

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=host1_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen on %s are %s" % (host_name1, stale_connections))

        stale_connections = get_stale_socket_connections(linux_obj=host2_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen on %s are %s" % (host_name2, stale_connections))

        checkpoint = "Copy setup file %s to %s" % (setup_fpg1_file, host_name1)
        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=host1_ip, target_username=host1_username,
                                     target_password=host1_password)
        fun_test.simple_assert(file_transfer, checkpoint)

        fun_test.sleep("Letting file be copied", seconds=1)

        checkpoint = "Execute setup file %s on %s" % (target_file_path, host_name1)
        output = execute_shell_file(linux_obj=host1_obj, target_file=target_file_path)
        fun_test.simple_assert(output['result'], checkpoint)

        checkpoint = "Copy setup file %s to %s" % (setup_fpg0_file, host_name2)
        target_file_path = "/tmp/" + setup_fpg0_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg0_filepath, target_file_path=target_file_path,
                                     target_ip=host2_ip, target_username=host2_username,
                                     target_password=host2_password)
        fun_test.simple_assert(file_transfer, checkpoint)

        fun_test.sleep("Letting file be copied", seconds=1)

        # Execute setup file on host2
        checkpoint = "Execute setup file %s on %s" % (target_file_path, host_name2)
        output = execute_shell_file(linux_obj=host2_obj, target_file=target_file_path, sudo=True)
        fun_test.simple_assert(output['result'], checkpoint)

        checkpoint = "Display applied routes on %s" % host_name1
        host1_obj.get_ip_route()
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Display applied routes on %s" % host_name2
        host2_obj.get_ip_route()
        fun_test.add_checkpoint(checkpoint)

    def run(self):
        host1_obj = fun_test.shared_variables['host1_obj']
        mpstat_host1_obj = copy.deepcopy(host1_obj)

        host2_obj = fun_test.shared_variables['host2_obj']

        test_parameters = {'dest_ip': '29.1.1.2', 'protocol': 'tcp', 'num_flows': self.num_flows,
                           'duration': self.duration, 'port1': 1000, 'port2': 4555, 'send_size': '128K'}

        branch_name = None
        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        # TODO: For now we capture mpstat only on poc-server-06 and not on nu-lab-04.
        version = fun_test.get_version()
        mpstat_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_mpstat.txt' % host_name1
        mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)

        # Captured tcpdump on Host 1
        tcpdump_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_tcpdump.pcap' % host_name1
        tcpdump_output_file1 = fun_test.get_temp_file_path(file_name=tcpdump_temp_filename)

        # Captured tcpdump on Host2
        tcpdump_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_tcpdump.pcap' % host_name2
        tcpdump_output_file2 = fun_test.get_temp_file_path(file_name=tcpdump_temp_filename)

        diff_netstat1 = None
        diff_netstat2 = None
        netstat_host1_before = None
        netstat_host2_before = None

        checkpoint = "Starting netperf test on %s and %s" % (host_name1, host_name2)
        host1_cmd_list = get_netperf_cmd_list(dip=test_parameters['dest_ip'],
                                              duration=test_parameters['duration'],
                                              num_flows=8,
                                              send_size=test_parameters['send_size'])
        fun_test.simple_assert(host1_cmd_list, 'Ensure netperf command formed')

        host2_cmd_list = get_netperf_cmd_list(dip=test_parameters['dest_ip'],
                                              duration=test_parameters['duration'],
                                              num_flows=8,
                                              start_core_id=8, end_core_id=15,
                                              send_size=test_parameters['send_size'])
        fun_test.simple_assert(host2_cmd_list, 'Ensure netperf command formed')

        network_controller_obj.disconnect()
        cmd_dict = {host1_obj: host1_cmd_list, host2_obj: host2_cmd_list}
        throughput_list = []
        for iteration in range(0, 5):
            fun_test.add_checkpoint("<=====> Start iteration: %d  <=====>" % iteration)
            fun_test.log_section("Start iteration: %d" % iteration)
            collect_dpc_stats = False if iteration > 0 else True
            if iteration == 0:
                checkpoint = "Capture netstat before traffic on %s" % host_name1
                netstat_host1_before = get_netstat_output(linux_obj=host1_obj)
                fun_test.add_checkpoint(checkpoint)

                checkpoint = "Capture netstat before traffic on %s" % host_name2
                netstat_host2_before = get_netstat_output(linux_obj=host2_obj)
                fun_test.add_checkpoint(checkpoint)

                # Start mpstat
                if use_mpstat:
                    fun_test.log("Starting to run mpstat command")
                    mp_out = run_mpstat_command(linux_obj=mpstat_host1_obj, interval=self.test_run_time,
                                                output_file=mpstat_output_file, bg=True, count=6)
                    fun_test.log('mpstat cmd process id: %s' % mp_out)
                    fun_test.add_checkpoint("Started mpstat command")

                checkpoint = "Start tcpdump capture in background before starting traffic on %s" % host_name1
                interface_name = get_interface_name(file_path=setup_fpg1_filepath)
                result = run_tcpdump_command(linux_obj=host1_obj, interface=interface_name,
                                             tcp_dump_file=tcpdump_output_file1,
                                             count=100000, filecount=1)
                fun_test.simple_assert(result, checkpoint)
                fun_test.shared_variables['tcpdump_pid1'] = result

                checkpoint = "Start tcpdump capture in background before starting traffic on %s" % host_name2
                interface_name = get_interface_name(file_path=setup_fpg0_filepath)
                result = run_tcpdump_command(linux_obj=host2_obj, interface=interface_name,
                                             tcp_dump_file=tcpdump_output_file2,
                                             count=100000, filecount=1, sudo=True)
                fun_test.simple_assert(result, checkpoint)
                fun_test.shared_variables['tcpdump_pid2'] = result

            netperf_result = run_netperf_concurrently(cmd_dict=cmd_dict,
                                                      network_controller_obj=network_controller_obj,
                                                      display_output=False, num_flows=self.num_flows,
                                                      collect_dpc_stats=collect_dpc_stats)
            fun_test.test_assert(netperf_result, checkpoint)

            fun_test.sleep("Wait after traffic", seconds=self.test_run_time)

            if iteration == 0:
                checkpoint = "Capture netstat after traffic on %s" % host_name1
                netstat_host1_after = get_netstat_output(linux_obj=host1_obj)
                fun_test.add_checkpoint(checkpoint)

                checkpoint = "Capture netstat after traffic on %s" % host_name2
                netstat_host2_after = get_netstat_output(linux_obj=host2_obj)
                fun_test.add_checkpoint(checkpoint)

                diff_netstat1 = get_diff_stats(old_stats=netstat_host1_before, new_stats=netstat_host1_after)
                diff_netstat2 = get_diff_stats(old_stats=netstat_host2_before, new_stats=netstat_host2_after)

            if 'tcpdump_pid1' in fun_test.shared_variables and 'tcpdump_pid2' in fun_test.shared_variables and \
                    iteration == 0:
                host1_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid1']), sudo=True)
                host2_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid2']), sudo=True)

            total_throughput = netperf_result['total_throughput']
            fun_test.add_checkpoint("ITERATION: %d Total throughput seen is %s" % (iteration, total_throughput))

            throughput_list.append(total_throughput)

            pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
            fun_test.add_checkpoint("ITERATION: %d Total PPS value is %s" % (iteration, round(pps, 2)))

            fun_test.add_checkpoint("<=====> End iteration: %d  <=====>" % iteration)

        avg_throughput = sum(throughput_list) / len(throughput_list)
        avg_pps = get_pps_from_mbps(mbps=avg_throughput, byte_frame_size=self.default_frame_size)
        if avg_throughput <= 0.0 and avg_pps <= 0.0:
            avg_throughput = -1
            avg_pps = -1

        create_performance_table(total_throughput=avg_throughput, total_pps=round(avg_pps, 2),
                                 num_flows=self.num_flows)

        # Scp mpstat json to LOGS dir
        if use_mpstat:
            populate_mpstat_output_file(output_file=mpstat_output_file, linux_obj=mpstat_host1_obj,
                                        dump_filename=mpstat_temp_filename)

        tcpdump_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_tcpdump.pcap' % host_name1
        populate_tcpdump_redirect_file(dump_filename=tcpdump_temp_filename, host_name=host_name1,
                                       source_file_path=tcpdump_output_file1, version=version,
                                       num_flows=self.num_flows, host_obj=host1_obj)

        tcpdump_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_tcpdump.pcap' % host_name2
        populate_tcpdump_redirect_file(dump_filename=tcpdump_temp_filename, host_name=host_name2,
                                       source_file_path=tcpdump_output_file2, version=version,
                                       num_flows=self.num_flows, host_obj=host2_obj)

        checkpoint = "Populate Netstat diff output file captured on %s" % host_name1
        netstat_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_netstat.txt' % host_name1
        populate = populate_netstat_output_file(diff_stats=diff_netstat1, filename=netstat_temp_filename)
        fun_test.test_assert(populate, checkpoint)

        checkpoint = "Populate Netstat diff output file captured on %s" % host_name2
        netstat_temp_filename = str(version) + "_" + str(self.num_flows) + '%s_netstat.txt' % host_name2
        populate = populate_netstat_output_file(diff_stats=diff_netstat2, filename=netstat_temp_filename)
        fun_test.test_assert(populate, checkpoint)

        # Parse output to get json
        if not branch_name:
            output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput",
                                                    frame_size=self.default_frame_size,
                                                    num_flows=self.num_flows,
                                                    throughput_n2t=avg_throughput, pps_n2t=avg_pps, timestamp=TIMESTAMP,
                                                    filename=filename, model_name=TCP_PERFORMANCE_MODEL_NAME)
            fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        host1_obj = fun_test.shared_variables['host1_obj']
        host2_obj = fun_test.shared_variables['host2_obj']

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=host1_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen on %s are %s" % (host_name1, stale_connections))

        stale_connections = get_stale_socket_connections(linux_obj=host2_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen on %s are %s" % (host_name2, stale_connections))

        if 'tcpdump_pid1' in fun_test.shared_variables and 'tcpdump_pid2' in fun_test.shared_variables:
            host1_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid1']), sudo=True)
            host2_obj.kill_process(process_id=int(fun_test.shared_variables['tcpdump_pid2']), sudo=True)


if __name__ == '__main__':
    ts = TcpPerformance()

    ts.add_test_case(TcpPerformance1Conn())
    ts.add_test_case(TcpPerformance4Conn())
    ts.add_test_case(TcpPerformance8Conn())
    ts.add_test_case(TcpPerformance16Conn2Host())

    ts.run()