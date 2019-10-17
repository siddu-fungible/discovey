#!/usr/bin/python
import sys
import optparse
import os
sys.path.append('/workspace/Integration/fun_test')
from lib.system.fun_test import *
from lib.host.linux import Linux
import pandas as pd
from StringIO import StringIO
import random



test_var = {}
test_var['pwd'] = '/workspace/Integration/fun_test/scripts/networking/funcp/'
test_var['local_user'] = 'netesto'
test_var['local_pass'] = 'netesto'
test_var['netesto_script_dir'] = '~/netesto_git/local/fun_scripts'
test_var['netesto_local_dir'] = '~/netesto_git/local/'
test_var['netesto_fun_plots'] = '~/netesto_git/local/fun_plots'



# Pre requisites - Create a user netesto/netesto in local host
 
def get_netesto_script(test_type='basic', no_of_streams=1, no_of_nobuff_streams=0, no_of_rr=1, rr_size='1B,1', local_buff=9000, remote_buff=9000):
    global test_var
    ali_script = []
    test_duration = 5000
    rr_req_size = rr_size.split(',')[0]
    rr_reply_size = rr_size.split(',')[1]
    if test_type == 'tp_tcp_stream_bi_dir':
        test = 'TCP_STREAM,TCP_MAERTS'
    elif test_type == 'tp_tcp_rr':
        test = 'TCP_RR'
    else:
        test = 'TCP_STREAM'



    nc_list = test_var['nc'].split(',')
    ns_list = test_var['ns'].split(',')
    servers3 = test_var['ns'] + ',' + test_var['ns_rr']
    clients3 = test_var['nc'] + ',' + test_var['nc_rr']
    servers_count = len(ns_list[0:-1])
    servers_t1_count = servers_count / 2
    clients_t1_count = len(nc_list[0:-1]) /2
    servers_t1 = []
    servers_t2 = []
    for st in test_var['ns'].split(','):
        servers_t1.append(st + 't')
    servers_t1 = ','.join(servers_t1)
    for st in test_var['ns_rr'].split(','):
        servers_t2.append(st + 't')
    servers_t2 = ','.join(servers_t2)
    #servers_t3 = ','.join(ns_list[servers_t1_count +1:-1])
    client1 = test_var['nc']
    #client3 = ','.join(nc_list[clients_t1_count + 1: -1])
    client2 = test_var['nc_rr']
    servers_t3 = 'dummy'
    client3 = 'dummy'

    ali_script.append('''
    #
    # Sample script for netesto
    #

    # Set default host suffix
    HOST_SUFFIX localadmin

    # Set hosts for 1, 2, 3 or 4 client host experiments
    # replace with appropriate hostnames
    SET clients1=cab02-qa-05
    SET clients2=cab02-qa-05,cab02-qa-07
    SET clients3={CLIENTS3}

    SET client1={CLIENT1}
    SET client2={CLIENT2}
    SET client3={CLIENT3}
    SET server1=cab02-qa-03
    SET server2=cab02-qa-01
    SET server3=cab02-qa-02
    # Set hosts for 1 or 2 server host experiments
    # replace with appropriate hostnames
    SET servers1=cab02-qa-01
    SET servers_t1={SERVERS_T1}
    SET servers_t2={SERVERS_T2}
    SET servers_t3={SERVERS_T3}
    SET servers2=cab02-qa-03,cab02-qa-01
    SET servers3={SERVERS3}

    # Set congestion control variants to run
    #SET ca=reno,cubic,nv,dctcp
    SET ca=cubic
    # Load library with macros
    SOURCE inlib

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
    '''.format(CLIENT1=client1,CLIENT2=client2,CLIENT3=client3,CLIENTS3=clients3,SERVERS3=servers3,SERVERS_T2=servers_t2,SERVERS_T1=servers_t1,SERVERS_T3=servers_t3))

    if test_type == 'tcp_rr_only_test':
        local_buff = 0
        remote_buff = 0
        ali_script.append('''


        SET burst=0
        SET interval=0
        SET burst2=0
        SET interval2=0
        SET reqs={RR_SIZE}
        SET reply={REPLY_SIZE}
        SET reqs1=1B
        SET reply1=1
        #SET tcpDump=25000
        SET instancestream={BUFF_STREAMS}
        SET nobuffstreams={NO_BUFF_STREAMS}
        SET instancerr={RR}
        SET localbuffer={LOCAL_BUFF}
        SET remotebuffer={REMOTE_BUFF}
        SET dur={DURATION}
        IF 1: RUN MServerStreamFunAlibaba  test=TCP_RR reqs1=$reqs1 reply1=$reply1 servers=$servers3  servers_t=$servers_t1 servers2_t=$servers_t2 servers3_t=$servers_t3 clients=$clients3 client1=$client1 client2=$client2 client3=$client3 nobuffclient1=$client1 nobuffclient3=$client3 instancenobuff1=$nobuffstreams localbuf1=$localbuffer remotebuf1=$remotebuffer instance1=$instancestream instance2=$instancerr reqs=$reqs reply=$reply burst2=$burst2 interval2=$interval2 expName=AlibabaSTREAM2RR1 ca=$ca dur=$dur interval=$interval burst=$burst
            '''.format(BUFF_STREAMS=no_of_streams, NO_BUFF_STREAMS=no_of_nobuff_streams, RR=no_of_rr, RR_SIZE=rr_req_size, REPLY_SIZE=rr_reply_size,
                       LOCAL_BUFF=local_buff, REMOTE_BUFF=remote_buff, DURATION=test_duration))
    else:

        ali_script.append('''
    
    
       SET burst=0
        SET interval=0
        SET burst2=0
        SET interval2=0
        SET reqs={RR_SIZE}
        SET reply={REPLY_SIZE}
        SET reqs1=1B
        SET reply1=1
        #SET tcpDump=25000
        SET instancestream={BUFF_STREAMS}
        SET nobuffstreams={NO_BUFF_STREAMS}
        SET instancerr={RR}
        SET localbuffer={LOCAL_BUFF}
        SET remotebuffer={REMOTE_BUFF}
        SET dur={DURATION}
        SET test={TEST}
        IF 1: RUN MServerStreamFunAlibaba  test=$test reqs1=$reqs1 reply1=$reply1 servers=$servers3  servers_t=$servers_t1 servers2_t=$servers_t2 servers3_t=$servers_t3 clients=$clients3 client1=$client1 client2=$client2 client3=$client3 nobuffclient1=$client1 nobuffclient3=$client3 instancenobuff1=$nobuffstreams localbuf1=$localbuffer remotebuf1=$remotebuffer instance1=$instancestream instance2=$instancerr reqs=$reqs reply=$reply burst2=$burst2 interval2=$interval2 expName=AlibabaSTREAM2RR1 ca=$ca dur=$dur interval=$interval burst=$burst
            '''.format(BUFF_STREAMS=no_of_streams, NO_BUFF_STREAMS=no_of_nobuff_streams, RR=no_of_rr, RR_SIZE=rr_req_size, REPLY_SIZE=rr_reply_size,
                       LOCAL_BUFF=local_buff, REMOTE_BUFF=remote_buff, DURATION=test_duration, TEST=test))

    ali_script = '\n'.join(ali_script)
    return ali_script


def netesto_client(host, ssh_username="localadmin", ssh_password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=ssh_username, ssh_password=ssh_password)
    linux_obj.sudo_command(command="killall netserver; killall netperf; killall netesto.py; killall tcpdump")
    time.sleep(10)
    # linux_obj.sudo_command(command="sudo ufw disable;iptables -X;iptables -t nat -F;iptables -t nat -X;iptables -t mangle -F;iptables -t mangle -X;iptables -P INPUT ACCEPT;iptables -P OUTPUT ACCEPT;iptables -P FORWARD ACCEPT;iptables -F;iptables -L")
    # linux_obj.sudo_command(command="sysctl -w net.core.rmem_max=4194304;sysctl -w net.core.wmem_max=4194304;sysctl -w net.core.rmem_default=4194304;sysctl -w net.core.wmem_default=4194304;sysctl -w net.core.optmem_max=4194304")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem=\"4096 87380 4194304\";sysctl -w net.ipv4.tcp_wmem=\"4096 65536 4194304\";sysctl -w net.ipv4.tcp_timestamps=0;sysctl -w net.ipv4.tcp_sack=1;sysctl -w net.core.netdev_max_backlog=250000;sysctl -w net.ipv4.tcp_low_latency=1;sysctl -w net.ipv4.tcp_adv_win_scale=1;sysctl -w net.ipv4.route.flush=1")
    linux_obj.sudo_command(command="echo 5 > /proc/sys/net/ipv4/tcp_fin_timeout")
    # 4096 65536 4194304
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle")
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
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
    linux_obj.command("cd ~/netesto_git/remote")
    # linux_obj.sudo_command("./numa_script.py")

    #netesto_id = linux_obj.start_bg_process(command="taskset -c 0,1,2,3,4,5,6,7 ./netesto.py -d -s")
    netesto_id = linux_obj.start_bg_process(command="./netesto.py -d -s")
    check_netesto = linux_obj.process_exists(process_id=netesto_id)
    fun_test.test_assert(expression=check_netesto, message="Make sure netesto is running on %s" % linux_obj)
    netstat(linux_obj)
    # TODO : include netstat -st command output before nad after the runs on cliens/servers


def netstat(linux):
    fun_test.log("======================================")
    fun_test.log("netstat output for  %s" % linux)
    fun_test.log("======================================")
    linux.command(command="netstat -st")

def run_netesto(test_type, no_of_streams=0, no_of_nobuff_streams=0, no_of_rr=1, rr_size='1B,1', local_buff=0, remote_buff=0, total_calls=0):
    global test_var
    if total_calls == 0:
        st = inspect.stack()
        script_file_name = st[1][1]
        fun_test._initialize(script_file_name)

    directory = test_var['pwd']
    self_linux = Linux(host_ip='127.0.0.1', ssh_username=test_var['local_user'], ssh_password=test_var['local_pass'])

    self_linux.command('cd %s' % directory)

    with open(directory+'/netesto_execute_script', 'w+') as file:
        os.chmod(directory+'/netesto_execute_script', 0o777)
        file.write(get_netesto_script(test_type=test_type,no_of_streams=no_of_streams, no_of_nobuff_streams=no_of_nobuff_streams, no_of_rr=no_of_rr, rr_size=rr_size, local_buff=local_buff,
                                  remote_buff=remote_buff))
    netesto_controller = Linux(host_ip="mpoc-server01", ssh_username="localadmin", ssh_password="Precious1*")
    netesto_controller.command("cd " + test_var['netesto_script_dir'])
    netesto_controller.command("rm netesto_execute_script")
    self_linux.scp(source_file_path=directory+"netesto_execute_script", target_ip=test_var['nh'],
                   target_file_path=test_var['netesto_script_dir'], target_username="localadmin",
                   target_password="Precious1*")
    time.sleep(2)
    self_linux.disconnect()


    netesto_controller.command("cd " + test_var['netesto_local_dir'] )

    netesto_process_before_test = netesto_controller.command("cat counter; echo").strip()

    # fun_test.sleep(message="Sleep before tests start", seconds=10)

    netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/netesto_execute_script", timeout=600)

    netesto_process = netesto_controller.command("cat counter; echo").strip()
    if netesto_process != "" and netesto_process_before_test != netesto_process:
        netesto_controller.command("cd " + test_var['netesto_fun_plots'])
        netesto_controller.sudo_command(command="./aggregate.py %s" % netesto_process, timeout=150)
        csv_results = netesto_controller.command("cat aggregate.csv")
        print csv_results
        data = StringIO(csv_results)
        df = pd.read_csv(data)
        print df
        fun_test.critical(message="No of incomplete streams = %s" % df[df['Duration'] < 60].count(1).count())
        x = Linux(host_ip='cab02-qa-05', ssh_username='localadmin', ssh_password='Precious1*')
        x.sudo_command("killall tcpdump")
        netesto_controller.sudo_command("cp -r ~/netesto_git/local/%s /var/www/html/" % netesto_process)
        netesto_controller.command("cd /var/www/html/Chart.js/fun_plots")
        netesto_controller.sudo_command("./webplot_latency.py %s" % netesto_process)
        netesto_controller.sudo_command("./webplot_tp.py %s" % netesto_process)
        netesto_controller.sudo_command("mv netesto.html netesto_tp_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv netesto1.html netesto_latency_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv ~/netesto_git/local/fun_plots/aggregate.csv "
                                        "/var/www/html/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        netesto_controller.disconnect()
        fun_test.log("\n======================================")
        fun_test.log("Link for throughput and Latency graphs")
        fun_test.log("======================================\n")
        fun_test.log("Throughput :  http://10.80.2.101/Chart.js/fun_plots/netesto_tp_%s.html" % netesto_process)
        fun_test.log("Latency :  http://10.80.2.101/Chart.js/fun_plots/netesto_latency_%s.html" % netesto_process)
        fun_test.log("Aggregate :  http://10.80.2.101/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        fun_test.log(message="No of incomplete streams = %s" % df[df['Duration'] < 57].count(1).count())

        total_throughput = df.loc[df.shape[0]-1].at['Throughput(Mbps)']
        row = 0
        row_lst = []
        for flow in df['FlowId']:
            if test_type == 'tcp_rr_only_test':
                if flow.startswith(tuple(test_var['nc'].split(','))):
                    print flow
                    row_lst.append(row)
                row += 1

        if test_type == 'tcp_rr_only_test':
            rr_latency_min = 0
            rr_latency_p50 = 0
            rr_latency_p90 = 0
            rr_latency_p99 = 0
            for i in row_lst:
                rr_latency_min = int(rr_latency_min) + int(df.loc[i].at['Latency_Min'])
                rr_latency_p50 = int(rr_latency_p50) + int(df.loc[i].at['Latency_p50'])
                rr_latency_p90 = int(rr_latency_p90) + int(df.loc[i].at['Latency_p90'])
                rr_latency_p99 = int(rr_latency_p99) + int(df.loc[i].at['Latency_p99'])

            rr_latency_min = int(rr_latency_min) / len(row_lst)
            rr_latency_p50 = int(rr_latency_p50) / len(row_lst)
            rr_latency_p90 = int(rr_latency_p90) / len(row_lst)
            rr_latency_p99 = int(rr_latency_p99) / len(row_lst)

            row = 0 
            for flow in df['FlowId']:
                if flow.startswith(tuple(test_var['nc_rr'].split(','))):
                    print flow
                    row_lst.append(row)
                row += 1

            rr_1B_latency_min = 0
            rr_1B_latency_p50 = 0
            rr_1B_latency_p90 = 0
            rr_1B_latency_p99 = 0
            for i in row_lst:
                rr_1B_latency_min = int(rr_1B_latency_min) + int(df.loc[i].at['Latency_Min'])
                rr_1B_latency_p50 = int(rr_1B_latency_p50) + int(df.loc[i].at['Latency_p50'])
                rr_1B_latency_p90 = int(rr_1B_latency_p90) + int(df.loc[i].at['Latency_p90'])
                rr_1B_latency_p99 = int(rr_1B_latency_p99) + int(df.loc[i].at['Latency_p99'])

            rr_1B_latency_min = int(rr_1B_latency_min) / len(row_lst)
            rr_1B_latency_p50 = int(rr_1B_latency_p50) / len(row_lst)
            rr_1B_latency_p90 = int(rr_1B_latency_p90) / len(row_lst)
            rr_1B_latency_p99 = int(rr_1B_latency_p99) / len(row_lst)

            rr_1B_latency = str(rr_1B_latency_min) + ':' + str(rr_1B_latency_p50) + ':' + str(rr_1B_latency_p90) + ':' + str(rr_1B_latency_p99)
        else:
            for flow in df['FlowId']:
                if flow.startswith(tuple(test_var['nc_rr'].split(','))):
                    print flow
                    row_lst.append(row)
                row += 1
            rr_latency_min = 0
            rr_latency_p50 = 0
            rr_latency_p90 = 0
            rr_latency_p99 = 0
            for i in row_lst:
                rr_latency_min = int(rr_latency_min) + int(df.loc[i].at['Latency_Min'])
                rr_latency_p50 = int(rr_latency_p50) + int(df.loc[i].at['Latency_p50'])
                rr_latency_p90 = int(rr_latency_p90) + int(df.loc[i].at['Latency_p90'])
                rr_latency_p99 = int(rr_latency_p99) + int(df.loc[i].at['Latency_p99'])

            rr_latency_min = int(rr_latency_min) / len(row_lst)
            rr_latency_p50 = int(rr_latency_p50) / len(row_lst)
            rr_latency_p90 = int(rr_latency_p90) / len(row_lst)
            rr_latency_p99 = int(rr_latency_p99) / len(row_lst)
            rr_1B_latency = 'na'
        no_of_nobuff_streams = str(no_of_nobuff_streams)
        if test_type == 'tcp_rr_only_test':
            name = str(no_of_streams) + "streams_" + str(local_buff) + "buff_" + str(no_of_nobuff_streams) + "nobuff_" + str(rr_size) + "_rr_size"
        else:    
            name = str(no_of_streams) + "streams_" + str(local_buff) + "buff_" + str(no_of_nobuff_streams) + "nobuff"

        result = {'no_of_streams': no_of_streams, 'no_of_rr': no_of_rr,
                                                           'local_buff': local_buff, 'remote_buff': remote_buff,
                                                           'total_throughput': total_throughput,
                                                           'rr_latency_min': rr_latency_min,
                                                           'rr_latency_p50': rr_latency_p50,
                                                           'rr_latency_p90':rr_latency_p90,
                                                           'rr_latency_p99': rr_latency_p99,
                                                           'rr_1B_latency': rr_1B_latency,
                                                           'netesto_folder': netesto_process,
                                                           'aggregate': "http://10.80.2.101/Chart.js/"
                                                                        "fun_plots/aggregate_%s.csv" % netesto_process}
        result['no_of_nobuff_streams'] = str(no_of_nobuff_streams)
        print {name: result}
        fun_test.shared_variables['result'][name] = result
        fun_test.shared_variables['result']['script_names'].append(name)
        print fun_test.shared_variables['result']


if __name__ == '__main__':

    parser = optparse.OptionParser()

    parser.add_option('-t', '--test',
                      action="store", dest="test_type",
                      help="Options: tp_tcp_rr - All streams are TCP_RR, \n \
                           tp_tcp_stream - All streams are TCP_STREAM with one additional RR stream - no buffer limits \n, \
                           tp_tcp_stream_buff_limit - Predefined stream test with buffer limitations \n tp_tcp_stream_bi_dir - TCP bi dir", default="tp_tcp_rr")
    parser.add_option('-n', '--rr_stream_count', action="store", dest="nobuff_streams", default='1', help="No of TCP_streams " )
    parser.add_option('-s', '--rr_size', action="store", dest="rr_size", default='1M,1',
                      help="request,response ( applicable for tp_tcp_rr ")
    parser.add_option('--nh', action="store", dest="netesto_controller", default='mpoc-server01', help='netesto_controller' )
    parser.add_option('--nc', action="store", dest="netesto_clients", default='mpoc-server30,mpoc-server31,mpoc-server32,mpoc-server33,mpoc-server45,mpoc-server46,mpoc-server34',
                      help='netesto_clients')
    parser.add_option('--ns', action="store", dest="netesto_servers", default='mpoc-server40,mpoc-server41,mpoc-server42,mpoc-server43,mpoc-server47,mpoc-server48,mpoc-server44',
                      help='netesto_servers')
    parser.add_option('--ns_rr', action="store", dest="netesto_rr_servers", default='mpoc-server42,mpoc-server46,mpoc-server-33',
                      help='netesto_rr_servers')
    parser.add_option('--nc_rr', action="store", dest="netesto_rr_clients", default='mpoc-server42,mpoc-server46,mpoc-server-33',
                      help='netesto_rr_clients')
    parser.add_option('--buff', action="store", dest="buffer_size", default='0,0',
                      help='netesto_rr_clients')
    parser.add_option('-u', '--usage',
                      action="store_true", dest="usage",
                      help="README text", default=False)


    options, args = parser.parse_args()
    if options.usage:
        print '''README:
    		'-t', '--test' default="tp_tcp_rr"
    		'-n', '--rr_stream_count' default='1', help="No of TCP_RR streams ( applicable for tp_tcp_rr "
    		'-s', '--rr_size' default='1M,1' help="request,response
    		'--nh', default='mpoc-server01', help='netesto_controller'
    		'--nc', default='mpoc-server30,mpoc-server31,mpoc-server32,mpoc-server45,mpoc-server34' , help='netesto_clients'
    		'--ns', default='mpoc-server40,mpoc-server41,mpoc-server43,mpoc-server47,mpoc-server48,mpoc-server44' , help='netesto_servers'
    		'--ns_rr', default='mpoc-server42','mpoc-server46','mpoc-server-33'
    		'--nc_rr', default='mpoc-server42','mpoc-server46','mpoc-server-33'
    		'--buff', default=0,0 , help=local_buff,remote_buff'
    		-u : This help
    		'''
        exit()

    test_type = options.test_type
    nobuff_streams = options.nobuff_streams
    rr_size = options.rr_size
    buffer_size = options.buffer_size
    netesto_controller = options.netesto_controller
    test_var['nh'] = netesto_controller
    netesto_clients = options.netesto_clients
    test_var['nc'] = netesto_clients
    netesto_servers = options.netesto_servers
    test_var['ns'] = netesto_servers
    test_var['nc_rr'] = options.netesto_rr_clients
    test_var['ns_rr'] = options.netesto_rr_servers
    default_streams_list = [0,4,8,16,32]

    #hosts = netesto_controller + ',' + netesto_clients + ',' + netesto_servers
    hosts = test_var['nc'] + ',' + test_var['ns'] + ',' + test_var['nc_rr'] + ',' + test_var['ns_rr']
    hosts = hosts.split(',')
    fun_test.shared_variables['result'] = {}
    fun_test.shared_variables['result']['script_names'] = []
    total_calls = 0
    print "Hosts are " + str(hosts)
    threads_list = []
    for host in hosts:
        thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=netesto_client, host=host)
        threads_list.append(thread_id)

    for thread_id in threads_list:
        fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

    if test_type == "tp_tcp_rr" or test_type == "tp_tcp_stream" or test_type == "tp_tcp_stream_bi_dir":

        run_netesto(test_type=test_type, no_of_nobuff_streams=nobuff_streams,  rr_size=rr_size, total_calls=total_calls)
    elif test_type == "tp_tcp_stream_buff_limit":
        if ',' in buffer_size:
            local_buff = buffer_size.split(',')[0]
            remote_buff = buffer_size.split(',')[1]
        else:
            local_buff = buffer_size
            remote_buff = buffer_size

        run_netesto(test_type=test_type, no_of_streams=nobuff_streams, local_buff=local_buff, remote_buff=remote_buff, total_calls=total_calls)

        total_calls += 1


    print fun_test.shared_variables['result']
    directory = test_var['pwd']
    fw = open(directory+'/netesto_results.csv', 'w')
    fw.write("Stream Name,no_of_streams,no_of_rr,no_of_nobuff_streams,rr_latency_min,rr_latency_p50,rr_latency_p90,rr_latency_p99,rr_1B_latency,total_throughput,local_buff,remote_buff,netesto_folder,aggregate file link\n")
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
        line.append(str(res['rr_1B_latency']))
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


