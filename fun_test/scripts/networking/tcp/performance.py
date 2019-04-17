from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from scripts.networking.tcp.helper import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *


network_controller_obj = None
nu_lab_handle = None
app = "tcp_server"
nu_lab_json = "nu_lab_info.json"
nu_lab_info_file = SCRIPTS_DIR + "/networking/tcp/configs/" + nu_lab_json
setup_fpg1_file = "setup_fpg1.sh"
setup_fpg1_filepath = SCRIPTS_DIR + "/networking/tcp/configs/" + setup_fpg1_file
TIMESTAMP = None
filename = "tcp_performance.json"


class TcpPerformance(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Setup fpg on nu-lab-04
        2. set syslog 2
        3. Execute tcp_server in dpcsh""")

    def setup(self):
        global nu_lab_obj, network_controller_obj, nu_lab_ip, nu_lab_username, nu_lab_password

        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get()
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        nu_config_obj = NuConfigManager()
        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

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

    def cleanup(self):
        pass


class TcpPerformance_1500(FunTestCase):
    default_frame_size = 1500

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test Tcp performance for 1500B stream",
                              steps="""
                              1. Setup fpg1 on nu-lab-04
                              """)

    def setup(self):
        target_file_path = "/tmp/" + setup_fpg1_file
        file_transfer = fun_test.scp(source_file_path=setup_fpg1_filepath, target_file_path=target_file_path,
                                     target_ip=nu_lab_ip, target_username=nu_lab_username,
                                     target_password=nu_lab_password)
        fun_test.simple_assert(file_transfer, "Ensure %s is scp to %s" % (setup_fpg1_file, nu_lab_ip))

        # Apply routes
        cmd = "sh %s" % target_file_path
        nu_lab_obj.command(command=cmd)
        nu_lab_obj.get_ip_route()

    def run(self):

        TIMESTAMP = get_current_time()
        fun_test.log("Starting netperf test")
        cmd = "taskset -c 2 netperf -t TCP_STREAM -H 10.1.40.26 -l 30 -f m -j -N -P 0 -- -k \"THROUGHPUT\" -s 128K -P 3000,4555"
        #fun_test.log(cmd)
        import copy

        nu_lab2 = copy.deepcopy(nu_lab_obj)
        cmd_2 = "sh /local/localadmin/onkar_perf.sh > out1984.txt"
        output_1 = nu_lab2.command(command=cmd_2, timeout=40)
        fun_test.sleep("file update", seconds=40)
        output = nu_lab_obj.command("cat /local/localadmin/out1984.txt")
        fun_test.log(output)

        #output = nu_lab_obj.command(command=cmd)
        #output = """THROUGHPUT=935.87
        #THROUGHPUT=935.87
        #THROUGHPUT=935.87
        #THROUGHPUT=935.87"""
        #fun_test.log(output)

        throughput_out_lines = output.split("\n")
        total_throughput = 0.0
        for line in throughput_out_lines:
            throughput = float(line.split("=")[1])
            total_throughput += throughput

        fun_test.log("Throughput seen is %s" % total_throughput)
        pps = get_pps_from_mbps(mbps=total_throughput, byte_frame_size=default_frame_size)
        fun_test.log("PPS value is %s" % pps)

        # Parse output to get json
        output = populate_performance_json_file(flow_type="TCP_Server", frame_size=default_frame_size, num_flows=1,
                                                throughput_n2t=total_throughput, pps_n2t=pps, timestamp=TIMESTAMP,
                                                filename=filename)
        fun_test.test_assert(output, "JSON file populated")

    def cleanup(self):
        pass

if __name__ == '__main__':
    ts = TcpPerformance()

    # Multi flows
    ts.add_test_case(TcpPerformance_1500())
    ts.run()