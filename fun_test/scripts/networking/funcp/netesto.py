#!/usr/bin/python
import sys
sys.path.append('/workspace/Integration/fun_test')
from lib.system.fun_test import *
from lib.host.linux import Linux
import pandas as pd
from StringIO import StringIO
import random


 
def get_netesto_script(no_of_streams=1, no_of_nobuff_streams=0, no_of_rr=1, local_buff=9000, remote_buff=9000):
    ali_script = '''
    #
    # Sample script for netesto
    #

    # Set default host suffix
    HOST_SUFFIX localadmin

    # Set hosts for 1, 2, 3 or 4 client host experiments
    # replace with appropriate hostnames
    SET clients1=cab02-qa-05
    SET clients2=cab02-qa-05,cab02-qa-07
    SET clients3=cab02-qa-05,cab02-qa-07,cab02-qa-06

    SET client1=cab02-qa-05
    SET client2=cab02-qa-07
    SET client3=cab02-qa-06
    SET server1=cab02-qa-03
    SET server2=cab02-qa-01
    SET server3=cab02-qa-02
    # Set hosts for 1 or 2 server host experiments
    # replace with appropriate hostnames
    SET servers1=cab02-qa-01
    SET servers_t1=cab02-qa-03t
    SET servers_t2=cab02-qa-01t
    SET servers_t3=cab02-qa-02t
    SET servers2=cab02-qa-03,cab02-qa-01
    SET servers3=cab02-qa-03,cab02-qa-01,cab02-qa-02

    # Set congestion control variants to run
    #SET ca=reno,cubic,nv,dctcp
    SET ca=cubic
    # Load library with macros
    SOURCE inlib

    SET instances=1				# how many flow instances per host
    SET dur=60						# duration of each run in seconds
    SET tcpDump=10000
    # specify descripiton of experiments
    #DESC ECN_Experiment

    # set default reply size of RPCs
    SET reply=1						# use RPC reply size of 1 byte

    #END # remove after fixing variables above

    #
    # Define commands to run before each test
    #
    # On Server(s)
    #
    BEGIN preServer
    # set large receive buffers in server
    #SET_SYSCTL host=$host net.ipv4.tcp_rmem=10000,262144,20971520
    # set large receive buffers in server
    SET_SYSCTL host=$host net.core.rmem_max=67108864
    SET_SYSCTL host=$host net.ipv4.tcp_rmem=10000,262144,33554432
    END preServer
    #
    # On Client(s)
    #
    BEGIN preClient
    # set large send buffers in client
    SET_SYSCTL host=$host net.core.wmem_max=67108864
    SET_SYSCTL host=$host net.ipv4.tcp_wmem=10000,262144,33554432
    END preClient
    #
    # On Client(s)
    #
    #BEGIN preClient
    # set large send buffers in client
    #SET_SYSCTL host=$host net.ipv4.tcp_wmem=10000,262144,20971520
    #END preClient

    # Experiments -----------------------------
    #
    # By default all will execute. You can disable individually by replacing
    #   "IF 1:" by "IF 0:" or "IF $varnanme" where varname is defined as an integer

    # burst - No: of sends or transactions
    # Interval - in milliseconds
    # For RR tests
    # reqs_in_bits = reqs * 8
    # transactions_per_sec = burst * (1/interval)
    # Throughput (Mbps) = reqs_in_bits * transactions_per_sec


    # 1 server, 1 client, 1M
    #SET reqs=1000B
    #SET reply=1
    #SET interval=200
    #SET burst=10
    #SET loops=1
    #SET instances=1
    #IF 1: RUN MServerRR servers=\$servers1 loops=$loops servers_t=$servers_t1 clients=$clients1 expName=1s1c1fr ca=$ca dur=$dur delay=0 instances=$instances reqs=$reqs reply=$reply interval=$interval burst=$burst

    #SET reqs=250K
    #SET reply=1
    #SET burst=10
    #SET interval=200
    #IF 1: RUN MServerStreamFunAlibaba  servers=$servers1  servers_t=$servers_t1 clients=$clients1 client1=$client1 instance1=1 expName=EACHSTREAM100Mbps ca=$ca dur=$dur  reqs=$reqs reply=$reply interval=$interval burst=$burst

    #SET burst=500
    #SET interval=100
    SET burst=0
    SET interval=0
    SET burst2=0
    SET interval2=0
    SET reqs=1B
    SET reply=1
    #SET tcpDump=25000
    SET instancestream=%s
    SET nobuffstreams=%s
    SET instancerr=%s
    SET localbuffer=%s
    SET remotebuffer=%s
    SET dur=60
    IF 1: RUN MServerStreamFunAlibaba  servers=$servers3  servers_t=$servers_t1 servers2_t=$servers_t2 servers3_t=$servers_t3 clients=$clients3 client1=$client1 client2=$client2 client3=$client3 nobuffclient1=$client1 nobuffclient3=$client3 instancenobuff1=$nobuffstreams localbuf1=$localbuffer remotebuf1=$remotebuffer instance1=$instancestream instance2=$instancerr reqs=$reqs reply=$reply burst2=$burst2 interval2=$interval2 expName=AlibabaSTREAM2RR1 ca=$ca dur=$dur interval=$interval burst=$burst


    SET burst=0
    SET interval=0
    SET burst2=0
    SET interval2=0
    SET reqs=1B
    SET reply=1
    #SET tcpDump=2500000
    SET instancestream=1
    SET instancerr=1
    IF 0: RUN MServerStreamFunAlibaba  servers=$servers3  servers_t=$servers_t1 servers2_t=$servers_t2 servers3_t=$servers_t1 clients=$clients3 client1=$client1 client2=$client2 client3=$client3 instance1=$instancestream instance2=$instancerr reqs=$reqs reply=$reply burst2=$burst2 interval2=$interval2 expName=AlibabaSTREAM2RR1Congestion ca=$ca dur=$dur interval=$interval burst=$burst

    SET burst=1000
    SET interval=200
    IF 0: RUN MServerStreamFunAlibaba  servers=$servers1  servers_t=$servers_t1 clients=$clients1 client1=$client1 instance1=1 expName=EACHSTREAM10Gbps ca=$ca dur=$dur interval=$interval burst=$burst

        ''' % (no_of_streams, no_of_nobuff_streams, no_of_rr, local_buff, remote_buff)
    return ali_script


def netesto_client(host, ssh_username="localadmin", ssh_password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=ssh_username, ssh_password=ssh_password)
    linux_obj.sudo_command(command="killall netserver; killall netperf; killall netesto.py; killall tcpdump")
    # linux_obj.sudo_command(command="sudo ufw disable;iptables -X;iptables -t nat -F;iptables -t nat -X;iptables -t mangle -F;iptables -t mangle -X;iptables -P INPUT ACCEPT;iptables -P OUTPUT ACCEPT;iptables -P FORWARD ACCEPT;iptables -F;iptables -L")
    # linux_obj.sudo_command(command="sysctl -w net.core.rmem_max=4194304;sysctl -w net.core.wmem_max=4194304;sysctl -w net.core.rmem_default=4194304;sysctl -w net.core.wmem_default=4194304;sysctl -w net.core.optmem_max=4194304")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem=\"4096 87380 4194304\";sysctl -w net.ipv4.tcp_wmem=\"4096 65536 4194304\";sysctl -w net.ipv4.tcp_timestamps=0;sysctl -w net.ipv4.tcp_sack=1;sysctl -w net.core.netdev_max_backlog=250000;sysctl -w net.ipv4.tcp_low_latency=1;sysctl -w net.ipv4.tcp_adv_win_scale=1;sysctl -w net.ipv4.route.flush=1")
    # linux_obj.sudo_command(command="echo 5 > /proc/sys/net/ipv4/tcp_fin_timeout")
    # 4096 65536 4194304
    # linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle")
    # linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_wmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem='10000 262144 33554432'")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_wmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w sysctl -w net.ipv4.tcp_mem '33554432 33554432 33554432'")
    # linux_obj.sudo_command(command="sysctl -w fs.file-max=10000000")
    # linux_obj.sudo_command(command="sysctl -w net.core.netdev_max_backlog=250000;sysctl -w net.ipv4.tcp_low_latency=1;")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.route.flush=1")
    # fun_test.sleep(message="start tcpdump now", seconds=10)
    take_tcpdump = False
    if take_tcpdump:
        if host == "cab02-qa-05":
            linux_obj.start_bg_process("sudo tcpdump -i hu2-f0 tcp -w netesto_%s.pcap" % random.randint(1, 90000))
            linux_obj.start_bg_process("sudo tcpdump \"tcp[tcpflags] & (tcp-syn) != 0\" -w netesto_syn_%s.pcap" % random.randint(1, 90000))
    linux_obj.command("cd ~/netesto/netesto/remote")
    # linux_obj.sudo_command("./numa_script.py")

    netesto_id = linux_obj.start_bg_process(command="taskset -c 0,1,2,3,4,5,6,7 ./netesto.py -d -s")
    check_netesto = linux_obj.process_exists(process_id=netesto_id)
    fun_test.test_assert(expression=check_netesto, message="Make sure netesto is running on %s" % linux_obj)
    netstat(linux_obj)
    # TODO : include netstat -st command output before nad after the runs on cliens/servers


def netstat(linux):
    fun_test.log("======================================")
    fun_test.log("netstat output for  %s" % linux)
    fun_test.log("======================================")
    linux.command(command="netstat -st")

def run_netesto(no_of_streams, no_of_nobuff_streams, no_of_rr, local_buff, remote_buff, total_calls):
    if total_calls == 0:
        st = inspect.stack()
        script_file_name = st[1][1]
        fun_test._initialize(script_file_name)

    #directory = '/Users/yajat/Documents/Fungible/WORKSPACE/Integration/fun_test/scripts/networking/funcp/'
    directory = '/workspace/Integration/fun_test/scripts/networking/funcp/'
    self_linux = Linux(host_ip='127.0.0.1', ssh_username='netesto', ssh_password='netesto')
    #self_linux = Linux(host_ip='127.0.0.1', ssh_username='yajat', ssh_password='messi3006')
    self_linux.command('cd %s' % directory)
    self_linux.command('rm -rf netesto_execute_script')
    file = open(directory+'/netesto_execute_script', 'w+')
    file.write(get_netesto_script(no_of_streams=no_of_streams, no_of_nobuff_streams=no_of_nobuff_streams, no_of_rr=no_of_rr, local_buff=local_buff,
                                  remote_buff=remote_buff))
    netesto_controller = Linux(host_ip="cab03-qa-03", ssh_username="localadmin", ssh_password="Precious1*")
    netesto_controller.command("cd ~/netesto_controller/netesto/local/fun_scripts")
    netesto_controller.command("rm netesto_execute_script")
    self_linux.scp(source_file_path=directory+"netesto_execute_script", target_ip="cab03-qa-03",
                   target_file_path="~/netesto_controller/netesto/local/fun_scripts", target_username="localadmin",
                   target_password="Precious1*")
    self_linux.disconnect()


    netesto_controller.command("cd ~/netesto_controller/netesto/local")

    netesto_process_before_test = netesto_controller.command("cat counter; echo").strip()

    # fun_test.sleep(message="Sleep before tests start", seconds=10)

    netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/netesto_execute_script", timeout=600)

    # netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/script.alibaba_3servers", timeout=600)

    netesto_process = netesto_controller.command("cat counter; echo").strip()
    if netesto_process != "" and netesto_process_before_test != netesto_process:
        netesto_controller.command("cd ~/netesto_controller/netesto/local/fun_plots")
        netesto_controller.sudo_command(command="./aggregate.py %s" % netesto_process, timeout=150)
        csv_results = netesto_controller.command("cat aggregate.csv")
        print csv_results
        data = StringIO(csv_results)
        df = pd.read_csv(data)
        print df
        fun_test.critical(message="No of incomplete streams = %s" % df[df['Duration'] < 60].count(1).count())
        x = Linux(host_ip='cab02-qa-05', ssh_username='localadmin', ssh_password='Precious1*')
        x.sudo_command("killall tcpdump")
        netesto_controller.sudo_command("cp -r ~/netesto_controller/netesto/local/%s /var/www/html/" % netesto_process)
        netesto_controller.command("cd /var/www/html/Chart.js/fun_plots")
        netesto_controller.sudo_command("./webplot_latency.py %s" % netesto_process)
        netesto_controller.sudo_command("./webplot_tp.py %s" % netesto_process)
        netesto_controller.sudo_command("mv netesto.html netesto_tp_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv netesto1.html netesto_latency_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv ~/netesto_controller/netesto/local/fun_plots/aggregate.csv "
                                        "/var/www/html/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        netesto_controller.disconnect()
        fun_test.log("\n======================================")
        fun_test.log("Link for throughput and Latency graphs")
        fun_test.log("======================================\n")
        fun_test.log("Throughput :  http://10.1.105.194/Chart.js/fun_plots/netesto_tp_%s.html" % netesto_process)
        fun_test.log("Latency :  http://10.1.105.194/Chart.js/fun_plots/netesto_latency_%s.html" % netesto_process)
        fun_test.log("Aggregate :  http://10.1.105.194/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        fun_test.log(message="No of incomplete streams = %s" % df[df['Duration'] < 57].count(1).count())

        total_throughput = df.loc[df.shape[0]-1].at['Throughput(Mbps)']
        row = 0
        for flow in df['FlowId']:
            if flow.startswith('cab02-qa-07'):
                print flow
                break
            row += 1
        rr_latency_min = df.loc[row].at['Latency_Min']
        rr_latency_p50 = df.loc[row].at['Latency_p50']
        rr_latency_p90 = df.loc[row].at['Latency_p90']
        rr_latency_p99 = df.loc[row].at['Latency_p99']
        no_of_nobuff_streams = str(no_of_nobuff_streams)
        name = str(no_of_streams) + "streams_" + str(local_buff) + "buff_" + str(no_of_nobuff_streams) + "nobuff"

        result = {'no_of_streams': no_of_streams, 'no_of_rr': no_of_rr,
                                                           'local_buff': local_buff, 'remote_buff': remote_buff,
                                                           'total_throughput': total_throughput,
                                                           'rr_latency_min': rr_latency_min,
                                                           'rr_latency_p50': rr_latency_p50,
                                                           'rr_latency_p90':rr_latency_p90,
                                                           'rr_latency_p99': rr_latency_p99,
                                                           'netesto_folder': netesto_process,
                                                           'aggregate': "http://10.1.105.194/Chart.js/"
                                                                        "fun_plots/aggregate_%s.csv" % netesto_process}
        result['no_of_nobuff_streams'] = str(no_of_nobuff_streams)
        print {name: result}
        fun_test.shared_variables['result'][name] = result
        fun_test.shared_variables['result']['script_names'].append(name)
        print fun_test.shared_variables['result']


if __name__ == '__main__':
    fun_test.shared_variables['result'] = {}
    fun_test.shared_variables['result']['script_names'] = []
    total_calls = 0
    #streams_list = [4, 8, 16, 32]
    arg_buffs = []
    streams_list = []
    print "Len of argv %s" %str(len(sys.argv))
    if len(sys.argv) > 1:
        streams_list.append(int(sys.argv[1]))
        arg_buffs.append(sys.argv[2])
        print "Streams list is %s , arg_buffs is %s" %(str(streams_list),str(arg_buffs))
    else:
        streams_list = [0,4,8,16,32]
    streams_4_buffs = ['18000', '42000', '72000', '128000', '300000']
    #streams_4_buffs = ['18000', '42000', '72000', '128000', '300000', '30000:4', '30000:8']
    #streams_4_buffs = [18000]
    for streams in streams_list:
        hosts = ['cab02-qa-06', 'cab02-qa-02', 'cab02-qa-03', 'cab02-qa-05', 'cab02-qa-01', 'cab02-qa-07']
        threads_list = []
        for host in hosts:
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=netesto_client, host=host)
            threads_list.append(thread_id)

        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
        buffs = []
        if streams == 4:
            if arg_buffs:
                buffs = arg_buffs
            else:
                buffs = ['18000', '42000', '72000', '128000', '300000'] 
        elif streams == 8:
            if arg_buffs:
                buffs = arg_buffs
            else:
                buffs = ['12000', '23000', '38000', '54000', '78000', '128000']
        elif streams == 0:
            #nobuff_streams = 8
            if arg_buffs:
                buffs = arg_buffs
            else:    
                buffs = ['0:4', '0:8', '0:16', '0:32', '0:64', '0:128', '0:256', '0:512', '0:1024']
        elif streams == 16:
            if arg_buffs:
                buffs = arg_buffs
            else:
                buffs = ['9000', '15000', '22000', '30000', '43000', '58000']
            #buffs = [58000]
        elif streams == 32:
            if arg_buffs:
                buffs = arg_buffs
            else:
                buffs = ['9000', '15000', '23000', '30000', '43000', '60000', '78000', '128000']
            #buffs = [8400]
            #nobuff_streams = 4
        for buff_value in buffs:
            if ':' in buff_value:
                nobuff_streams = int(buff_value.split(':')[1])
                buff_value = int(buff_value.split(':')[0])
            else:
                nobuff_streams = 0
                buff_value = int(buff_value)
            print "Running test for %s streams %s buffer size" %(str(streams),str(buff_value)) 
            run_netesto(no_of_streams=streams, no_of_nobuff_streams=nobuff_streams, no_of_rr=1, local_buff=buff_value, remote_buff=buff_value,
                        total_calls=total_calls)
            total_calls += 1
    print fun_test.shared_variables['result']
    directory = '/workspace/Integration/fun_test/scripts/networking/funcp/'
    fw = open(directory+'/netesto_results.csv', 'w')
    fw.write("Stream Name,no_of_streams,no_of_rr,no_of_nobuff_streams,rr_latency_min,rr_latency_p50,rr_latency_p90,rr_latency_p99,total_throughput,local_buff,remote_buff,netesto_folder,aggregate file link\n")
    for res1 in fun_test.shared_variables['result']['script_names']:
        res = fun_test.shared_variables['result'][res1]
        print("Res is " + str(res))
        line = []
        line_val = ''
        line.append(res1)
        line.append(str(res['no_of_streams']))
        line.append(str(res['no_of_rr']))
        line.append(str(res['no_of_nobuff_streams']))
        line.append(str(res['rr_latency_min']))
        line.append(str(res['rr_latency_p50']))
        line.append(str(res['rr_latency_p90']))
        line.append(str(res['rr_latency_p99']))
        line.append(str(res['total_throughput']))
        line.append(str(res['local_buff']))
        line.append(str(res['remote_buff']))
        line.append(str(res['netesto_folder']))
        line.append(str(res['aggregate']))
        print "Line is " + str(line)
        line_val = ','.join(line)
        fw.writelines(','.join(line) + '\n')
        #fw.write('\n')        
    fw.close()    
