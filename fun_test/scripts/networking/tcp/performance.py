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
nu_lab_json = "nu_lab_info.json"
nu_lab_info_file = SCRIPTS_DIR + "/networking/tcp/configs/" + nu_lab_json
setup_fpg1_file = "setup_fpg1.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
TIMESTAMP = None
filename = "tcp_performance.json"
use_mpstat = False


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
        1. Setup fpg on nu-lab-04
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global nu_lab_obj, network_controller_obj, nu_lab_ip, nu_lab_username, nu_lab_password, nu_lab_obj2, \
            mpstat_obj, mpstat_obj2, mode

        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get()
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        nu_config_obj = NuConfigManager()
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
        #fun_test.simple_assert(exec_app, "Execute %s on dpcsh" % app)

        # Setup fpg1
        file_json = fun_test.parse_file_to_json(nu_lab_info_file)
        nu_lab_username = file_json['username']
        nu_lab_ip = file_json['ip']
        nu_lab_password = file_json['password']
        nu_lab_obj = Linux(host_ip=nu_lab_ip, ssh_username=nu_lab_username,
                           ssh_password=nu_lab_password)

        nu_lab_obj2 = copy.deepcopy(nu_lab_obj)
        mpstat_obj = copy.deepcopy(nu_lab_obj)
        mpstat_obj2 = copy.deepcopy(nu_lab_obj)

    def cleanup(self):
        pass


class TcpPerformance_1_Conn(FunTestCase):
    default_frame_size = 1500
    perf_filename = "perf_1_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    test_run_time = 30
    num_flows = 1
    output_file = None
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance for 1 connection for 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              2. Run netperf file with 1 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """)

    def setup(self):
        self.netperf_remote_port = get_port_from_file(self.perf_filepath)
        fun_test.simple_assert(self.netperf_remote_port, "Value of server port is %s" % self.netperf_remote_port)

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=nu_lab_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)
        '''
        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))
        
        fun_test.sleep("Letting file be copied", seconds=1)

        # Execute sh file
        fun_test.log("Creating interface and applying routes")
        output = execute_shell_file(linux_obj=nu_lab_obj, target_file=target_file_path)
        fun_test.simple_assert(output['output'], "Ensure file %s is executed" % target_file_path)
        '''
        fun_test.log("Display applied routes")
        nu_lab_obj.get_ip_route()

    def run(self):

        TIMESTAMP = get_current_time()

        fun_test.log("SCP file %s to %s" % (self.perf_filename, nu_lab_obj.host_ip))

        target_file_path = "/tmp/" + self.perf_filename
        file_transfer = fun_test.scp(source_file_path=self.perf_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))

        fun_test.sleep("Letting file be copied", seconds=1)

        fun_test.log("Capture netstat before traffic")
        netstat_1 = get_netstat_output(linux_obj=nu_lab_obj)

        # Start mpstat
        if use_mpstat:
            version = fun_test.get_version()
            mpstat_temp_filename = str(version) + "_" +str(self.num_flows) + '_mpstat.json'
            mpstat_output_file = fun_test.get_temp_file_path(file_name=mpstat_temp_filename)

            fun_test.log("Starting to run mpstat command")
            mp_out = run_mpstat_command(linux_obj=mpstat_obj, interval=self.test_run_time, json_output=True,
                                        output_file=mpstat_output_file, bg=True)
            fun_test.add_checkpoint("Started mpstat command")
        
        # Execute sh file
        temp_filename = fun_test.get_temp_file_name() + '.txt'
        output_file = fun_test.get_temp_file_path(file_name=temp_filename)
        
        fun_test.log("Starting netperf test")
        output = execute_shell_file(linux_obj=nu_lab_obj2, target_file=target_file_path, output_file=output_file)
        fun_test.simple_assert(output['result'], "Ensure file %s is executed" % target_file_path)

        fun_test.sleep("Letting traffic be run", seconds=self.test_run_time + 10)

        netperf_output = nu_lab_obj.command("cat %s" % output_file)
        fun_test.test_assert(netperf_output, "Ensure throughput value is seen")

        output = get_total_throughput(output=netperf_output, num_conns=self.num_flows)
        #fun_test.test_assert(output['connections'], "Ensure throughput value is greater than 0")
        total_throughput = output['throughput']
        fun_test.log("Total throughput seen is %s" % total_throughput)
        fun_test.test_assert(total_throughput > 0.0, "Ensure some throughput is seen. Actual %s" % total_throughput)

        pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=self.default_frame_size)
        fun_test.log("PPS value is %s" % pps)

        # Parse output to get json
        output = populate_performance_json_file(mode=mode, flow_type="FunTCP_Server_Throughput", frame_size=self.default_frame_size,
                                                num_flows=self.num_flows,
                                                throughput_n2t=total_throughput, pps_n2t=pps, timestamp=TIMESTAMP,
                                                filename=filename)
        fun_test.test_assert(output, "JSON file populated")

        fun_test.sleep("Letting files be generated", seconds=2)

        # Scp mpstat json to LOGS dir
        if use_mpstat:
            mpstat_dump_filename = LOGS_DIR + "/%s" % mpstat_temp_filename
            fun_test.scp(source_file_path=mpstat_output_file, source_ip=nu_lab_ip, source_username=nu_lab_username,
                         source_password=nu_lab_password, target_file_path=mpstat_dump_filename, timeout=180)

        fun_test.sleep("Letting file to be scp", seconds=2)

        # Trim contents of file
        #trim = trim_json_contents(filepath=mpstat_dump_filename)
        #fun_test.simple_assert(trim, "Reduce json contents")

        fun_test.log("Capture netstat after traffic")
        netstat_2 = get_netstat_output(linux_obj=nu_lab_obj)

        # Get diff stats
        netstat_temp_filename = str(version) + "_" + str(self.num_flows) + '_netstat.json'
        populate = populate_netstat_json_file(old_stats=netstat_1, new_stats=netstat_2, filename=netstat_temp_filename)
        fun_test.test_assert(populate, "Populate netstat into json file")

        output = network_controller_obj.get_flow_list()
        fun_test.log("Log flow list")

    def cleanup(self):
        if self.output_file:
            nu_lab_obj.remove_file(self.output_file)

        # Check stale socket connections
        stale_connections = get_stale_socket_connections(linux_obj=nu_lab_obj, port_value=self.netperf_remote_port)
        fun_test.log("Number of orphaned connections seen are %s" % stale_connections)


class TcpPerformance_2_Conn(TcpPerformance_1_Conn):
    num_flows = 2
    perf_filename = "perf_2_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test Tcp performance for 2 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              2. Run netperf file with 2 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """)

class TcpPerformance_4_Conn(TcpPerformance_1_Conn):
    num_flows = 4
    perf_filename = "perf_4_tcp_connection.sh"
    perf_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + perf_filename
    netperf_remote_port = None

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Tcp performance for 4 connections 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              2. Run netperf file with 4 connection
                              3. Update tcp_performance.json file with throughput and pps
                              """)


if __name__ == '__main__':
    ts = TcpPerformance()

    ts.add_test_case(TcpPerformance_1_Conn())
    #ts.add_test_case(TcpPerformance_2_Conn())
    #ts.add_test_case(TcpPerformance_4_Conn())
    ts.run()