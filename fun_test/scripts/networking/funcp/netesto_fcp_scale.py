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
from netesto_traffic_profiles import *



test_var = {}
test_var['pwd'] = '/workspace/Integration/fun_test/scripts/networking/funcp/'
test_var['local_user'] = 'netesto'
test_var['local_pass'] = 'netesto'
test_var['netesto_script_dir'] = '~/netesto_git/local/fun_scripts'
test_var['netesto_local_dir'] = '~/netesto_git/local/'
test_var['netesto_fun_plots'] = '~/netesto_git/local/fun_plots'






# Pre requisites - Create a user netesto/netesto in local host
 
def get_netesto_script(test_type='basic'):
    global test_var

    ali_script = ''
    flow_list = traffic_profile[test_type]['total_flows'].split(" ")
    doclient_cmd = []
    all_servers = []
    all_clients = []
    for fl in flow_list:
        flow = traffic_profile[test_type][fl]
        doclient_args = []
        for c in flow['clients'].split(","):
            if c not in all_clients:
                all_clients.append(c)
        for s in flow['servers'].split(","):
            if s not in all_servers:
                all_servers.append(s)

        if 'test' in flow:
            test = flow['test']
            if flow['test'] == "TCP_RR":
                if 'rr_size' in flow:
                    req, reply = flow['rr_size'].split(',')
                    doclient_args.append("req={REQ} reply={REPLY}".format(REQ=req, REPLY=reply))
                else:
                    doclient_args.append("req=1M reply=1")

        else:
            test = 'TCP_STREAM'

        inter_instance_delay = '0'
        if 'instances' in flow:
            if 'delay_between_instances' in flow:
                instance_delay_lst = [flow['delay_between_instances']] * int(flow['instances'])
                inter_instance_delay = ','.join(instance_delay_lst)
                doclient_args.append("instances=1")
            else:
                doclient_args.append("instances=" + flow['instances'])
        else:
            doclient_args.append("instances=1")

        if 'duration' in flow:
            doclient_args.append("dur=" + flow['duration'])
        else:
            doclient_args.append("dur=60")

        #if 'delay' in flow:
        #    doclient_args.append("delay=" + flow['delay'])
        #else:
        #    doclient_args.append("delay=0")
        if 'delay' in flow:
            delay = flow['delay']
        else:
            delay = '0'

        if 'repeat_interval' in flow:
            if 'repeat_max' in flow:
                repeat_max = flow['repeat_max']
            else:
                repeat_max = '1'
            repeat_flow_lst = [flow['repeat_interval']] * int(repeat_max)
            flow_repeat = ','.join(repeat_flow_lst)
            # insert first iteration
            flow_repeat = '0,' + str(flow_repeat)
        else:
            flow_repeat = '0'


        if 'ca' in flow:
            doclient_args.append("ca=" + flow['ca'])
        else:
            doclient_args.append("ca=cubic")

        if 'burst' in flow:
            doclient_args.append("burst=" + flow['burst'])

        if 'interval' in flow:
            doclient_args.append("interval=" + flow['interval'])

        if 'tos' in flow:
            doclient_args.append("tos=" + flow['tos'])

        if 'localbuffer' in flow:
            doclient_args.append("localBuffer=" + flow['localbuffer'])

        if 'remotebuffer' in flow:
            doclient_args.append("remoteBuffer=" + flow['remotebuffer'])

        port_incr_lst = [] 
        if 'port' in flow:
            print "Reached here port "
            doclient_args.append("port=" + flow['port']) 
        doclient_args.append("stats=1")

        doclient_args = " ".join(doclient_args)

        doclient_cmd.append('''
        FOR c IN {CLIENTS} DO
            IF_DEF preClient: RUN preClient host=$c
            FOR s IN {SERVERS_T} DO
                IF $tcpDump: DO_TCPDUMP host=$c server=$s packets=$tcpDump
                FOR t IN {TEST} DO
                    SET delay={DELAY}
                    FOR j IN {FLOW_REPEAT} DO
                        SET_EXP delay=$delay+$j
                        FOR i IN {INTER_INSTANCE_DELAY} DO
                            SET_EXP delay=$delay+$i
                            DO_CLIENT host=$c server=$s test=$t delay=$delay {DO_CLIENT_ARGS}
                            RAND_WAIT $randDelay
                        DONE
                    DONE        
                DONE
            DONE
        DONE
        '''.format(CLIENTS=flow['clients'], SERVERS_T=flow['servers_t'], TEST=test, INTER_INSTANCE_DELAY=inter_instance_delay, DELAY=delay, FLOW_REPEAT=flow_repeat, DO_CLIENT_ARGS=doclient_args))

    doclient_cmds = "\n".join(doclient_cmd)

    all_clients = ','.join(all_clients)
    all_servers = ','.join(all_servers)

    total_duration = traffic_profile[test_type]['total_duration']

    ali_script = '''

    ##################
    # Default values
    SET randDelay=0.1

    SET burst=0
    SET interval=0
    HOST_SUFFIX localadmin


    BEGIN FunFcpTests
    SET exp=COUNTER
    SET expName=TestRun
    SET tcpDump=0
    # servers
    FOR s IN {ALL_SERVERS} DO
      IF_DEF preServer: RUN preServer host=$s
      DO_SERVER exp=$exp host=$s order=0 expName=$expName start=1
      SET exp=PREV
      IF $tcpDump: DO_TCPDUMP host=$s server=$s packets=$tcpDump
    DONE
    WAIT 5

    {DO_CLIENT_CMDS}


    # wait and then get the results
    WAIT {TOTAL_DURATION}
    WAIT 10
    FOR s IN {ALL_SERVERS} DO
      DO_SERVER host=$s order=1
    DONE
    WAIT 5
    FOR s IN {ALL_SERVERS} DO
      GET_DATA host=$s
    DONE
    FOR c IN {ALL_CLIENTS} DO
      GET_DATA host=$c

    DONE
    WAIT 10
    PROCESS_EXP
    WAIT 15
    END FunFcpTests

    RUN FunFcpTests
    '''.format(DO_CLIENT_CMDS=doclient_cmds, ALL_SERVERS=all_servers, ALL_CLIENTS=all_clients, TOTAL_DURATION=total_duration)
    print "Ali_script is " + str(ali_script)

    return ali_script


def netesto_client(host, ssh_username="localadmin", ssh_password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=ssh_username, ssh_password=ssh_password)
    linux_obj.sudo_command(command="killall doClient.sh; killall ping; killall sleep; killall iostat; killall doServer.sh; killall netserver; killall netperf; killall netesto.py; killall tcpdump")
    time.sleep(10)
    linux_obj.sudo_command(command="echo 5 > /proc/sys/net/ipv4/tcp_fin_timeout")
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle")
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
    linux_obj.sudo_command(command="/etc/init.d/irqbalance stop")
    interface = {
        'mpoc-server30': 'hu3-f0',
        'mpoc-server31': 'hu1-f0',
        'mpoc-server32': 'hu0-f0',
        'mpoc-server33': 'hu1-f0',
        'mpoc-server34': 'hu2-f0',
        'mpoc-server40': 'hu3-f0',
        'mpoc-server41': 'hu1-f0',
        'mpoc-server42': 'hu0-f0',
        'mpoc-server43': 'hu1-f0',
        'mpoc-server44': 'hu2-f0',
        'mpoc-server45': 'hu3-f0',
        'mpoc-server46': 'hu1-f0',
        'mpoc-server47': 'hu1-f0',
        'mpoc-server48': 'hu2-f0',
        'mpoc-server01' : 'enp216s0',
        'mpoc-server02' : 'enp216s0',
        'mpoc-server03' : 'enp216s0',
        'mpoc-server04' : 'enp216s0',
        'mpoc-server05' : 'enp216s0',
        'mpoc-server06' : 'enp216s0',
        'mpoc-server19' : 'enp175s0',
        'mpoc-server20' : 'enp175s0',
        'mpoc-server21' : 'enp175s0',
        'mpoc-server22' : 'enp175s0',
        'mpoc-server23' : 'enp175s0',
    }

    #if host == "mpoc-server42" or host == "mpoc-server46" or host == "mpoc-server-33":
    #    linux_obj.sudo_command(command="ethtool --coalesce {INTF} rx-usecs 0 tx-usecs 0 rx-frames 1 tx-frames 1 adaptive-rx off".format(INTF=interface[host]))
    #else:
    #    linux_obj.sudo_command(
    #        command="sudo ethtool --coalesce {INTF} rx-usecs 8 tx-usecs 16 rx-frames 64 tx-frames 32 adaptive-rx on".format(
    #            INTF=interface[host]))

    linux_obj.sudo_command(command="sudo ethtool --coalesce {INTF} rx-usecs 8 tx-usecs 16 rx-frames 64 tx-frames 32 adaptive-rx on".format(INTF=interface[host]))



    #take_tcpdump = False
    #if take_tcpdump:
    #    if host == "cab02-qa-05":
    #        linux_obj.start_bg_process("sudo tcpdump -i hu2-f0 tcp -w netesto_%s.pcap" % random.randint(1, 90000))
    #        linux_obj.start_bg_process("sudo tcpdump \"tcp[tcpflags] & (tcp-syn) != 0\" -w netesto_syn_%s.pcap" % random.randint(1, 90000))
    linux_obj.command("cd ~/netesto_git/remote")
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

def run_netesto(test_type, total_calls=0):
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
        file.write(get_netesto_script(test_type=test_type))
    netesto_controller = Linux(host_ip=test_var['nh'], ssh_username="localadmin", ssh_password="Precious1*")
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

    netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/netesto_execute_script", timeout=1200)

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
        netesto_controller.sudo_command("./webplot_retrans.py %s" % netesto_process)
        netesto_controller.sudo_command("mv netesto.html netesto_tp_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv netesto1.html netesto_latency_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv netesto_retrans.html netesto_retrans_%s.html" % netesto_process)
        netesto_controller.sudo_command("mv ~/netesto_git/local/fun_plots/aggregate.csv "
                                        "/var/www/html/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        netesto_controller.disconnect()
        fun_test.log("\n======================================")
        fun_test.log("Link for throughput and Latency graphs")
        fun_test.log("======================================\n")
        fun_test.log("Throughput :  http://10.80.2.101/Chart.js/fun_plots/netesto_tp_%s.html" % netesto_process)
        fun_test.log("Latency :  http://10.80.2.101/Chart.js/fun_plots/netesto_latency_%s.html" % netesto_process)
        fun_test.log("Retransmissions :  http://10.80.2.101/Chart.js/fun_plots/netesto_retrans_%s.html" % netesto_process)
        fun_test.log("Aggregate :  http://10.80.2.101/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        fun_test.log(message="No of incomplete streams = %s" % df[df['Duration'] < 57].count(1).count())

        total_throughput = df.loc[df.shape[0]-1].at['Throughput(Mbps)']
        row = 0
        row_lst = []
        for flow in df['FlowId']:
            if test_type == 'tp_tcp_rr':
                if flow.startswith(tuple(test_var['nc'].split(','))):
                    print flow
                    row_lst.append(row)
                row += 1

        if test_type == 'tp_tcp_rr':
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
            row_lst = []
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
            if row_lst: 
                rr_1B_latency_min = int(rr_1B_latency_min) / len(row_lst)
                rr_1B_latency_p50 = int(rr_1B_latency_p50) / len(row_lst)
                rr_1B_latency_p90 = int(rr_1B_latency_p90) / len(row_lst)
                rr_1B_latency_p99 = int(rr_1B_latency_p99) / len(row_lst)

                rr_1B_latency = str(rr_1B_latency_min) + ':' + str(rr_1B_latency_p50) + ':' + str(rr_1B_latency_p90) + ':' + str(rr_1B_latency_p99)
            else:
                rr_1B_latency = 'na'
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
            if row_lst:
                rr_latency_min = int(rr_latency_min) / len(row_lst)
                rr_latency_p50 = int(rr_latency_p50) / len(row_lst)
                rr_latency_p90 = int(rr_latency_p90) / len(row_lst)
                rr_latency_p99 = int(rr_latency_p99) / len(row_lst)
                rr_1B_latency = 'na'
            else:
                rr_latency_min = 'na' 
                rr_latency_p50 = 'na'
                rr_latency_p90 = 'na'
                rr_latency_p99 = 'na'
                rr_1B_latency = 'na'

        instances = traffic_profile[test_type]['flow1']['instances']
        test = traffic_profile[test_type]['flow1']['test']
        if 'template' in test_type:
            local_buff = traffic_profile[test_type]['flow1']['localbuffer']
            remote_buff = traffic_profile[test_type]['flow1']['remotebuffer']

            name = str(test) + '_ins_' + str(instances) + '_lbuf_' + str(local_buff) + '_rbuf_' + str(remote_buff)
        else:
             name = str(test) + '_ins_' + str(instances)
             if 'localbuffer' in traffic_profile[test_type]['flow1']:
                 local_buff = traffic_profile[test_type]['flow1']['localbuffer']
                 remote_buff = traffic_profile[test_type]['flow1']['remotebuffer']
             else:
                 local_buff = '0'
                 remote_buff = '0'

        result = {'no_of_streams': str(instances),
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
    parser.add_option('-n', '--instances', action="store", dest="instances", default='1', help="No of instances" )
    parser.add_option('-s', '--rr_size', action="store", dest="rr_size", default='1M,1',
                      help="request,response ( applicable for tp_tcp_rr ")
    parser.add_option('--nh', action="store", dest="netesto_controller", default='mpoc-server01', help='netesto_controller' )
    parser.add_option('--nc', action="store", dest="netesto_clients", default='dummy',
                      help='netesto_clients')
    parser.add_option('--ns', action="store", dest="netesto_servers", default='dummy',
                      help='netesto_servers')
    parser.add_option('--buff', action="store", dest="buffer_size", default='0,0',
                      help='netesto_rr_clients')
    parser.add_option('-d', '--duration', action="store", dest="duration", default="60",
                      help='test duration')
    parser.add_option('--tos', action="store", dest="tos", default="0",
                      help='tos vaue')
    parser.add_option('-u', '--usage',
                      action="store_true", dest="usage",
                      help="README text", default=False)
    parser.add_option('-c', '--cmd',
                      action="store_true", dest="cmd_line",
                      help="command line option", default=False)


    options, args = parser.parse_args()
    if options.usage:
        print '''README:
    		'-t', '--test' default="tp_tcp_rr"
                '-d', '--duration' default=60
    		'-n', '--instances' default='1', help="No of instances "
    		'-s', '--rr_size' default='1M,1' help="request,response
    		'--nh', default='mpoc-server01', help='netesto_controller'
    		'--nc', default='dummy' , help='netesto_clients'
    		'--ns', default='dummy' , help='netesto_servers'
    		'--tos', default='0'
    		'--buff', default=0,0 , help=local_buff,remote_buff'
    		-u : This help
    		'''
        exit()



    test_type = options.test_type

    if options.cmd_line:
        if test_type == 'tp_tcp_stream_bi_dir':
            test = 'TCP_STREAM,TCP_MAERTS'
        elif test_type == 'tp_tcp_rr' or test_type == 'tp_tcp_rr_buff_limit' or test_type == 'tp_tcp_rr_buff_limit_template':
            test = 'TCP_RR'
        elif test_type == 'tp_tcp_crr':
            test = 'TCP_CRR'
        else:
            test = 'TCP_STREAM'

        servers_t = []
        for st in options.netesto_servers.split(','):
            servers_t.append(st + 't')
        servers_t = ','.join(servers_t)

        traffic_profile = {}
        traffic_profile[test_type] = {"total_flows" : "flow1", "total_duration" : options.duration, "netesto_controller": options.netesto_controller}
        traffic_profile[test_type]['flow1'] = {
                                                "test" : test,
                                                "clients" : options.netesto_clients,
                                                "servers" : options.netesto_servers,
                                                "servers_t" : servers_t,
                                                "duration"  : str(options.duration),
                                                "delay"     : "0",
                                                "instances" : options.instances,
                                              }
        if 'TCP_RR' in test or 'TCP_CRR' in test:
            traffic_profile[test_type]['flow1']['rr_size'] = options.rr_size

        if options.buffer_size != '0,0':
            if ',' in options.buffer_size:
                local_buff = options.buffer_size.split(',')[0]
                remote_buff = options.buffer_size.split(',')[1]
            else:
                local_buff = options.buffer_size
                remote_buff = options.buffer_size

            traffic_profile[test_type]['flow1']['localbuffer'] = str(local_buff)
            traffic_profile[test_type]['flow1']['remotebuffer'] = str(remote_buff)

        if options.tos != "0":
            traffic_profile[test_type]['flow1']['tos'] = str(options.tos)


    test_var['nc_rr'] = 'dummy'
    test_var['ns_rr'] = 'dummy'
    test_var['nc'] = []
    test_var['ns'] = []
    test_var['nh'] = options.netesto_controller
    flow_list = traffic_profile[test_type]['total_flows'].split(" ")
    for fl in flow_list:
        flow = traffic_profile[test_type][fl]
        for c in flow['clients'].split(","):
            if c not in test_var['nc']:
                test_var['nc'].append(c)
        for s in flow['servers'].split(","):
            if s not in test_var['ns']:
                test_var['ns'].append(s)

    test_var['nc'] = ','.join(test_var['nc'])
    test_var['ns'] = ','.join(test_var['ns'])

    hosts = test_var['nc'] + ',' + test_var['ns']

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

    if test_type ==  "tp_tcp_stream_buff_limit_template" or test_type ==  "tp_tcp_rr_buff_limit_template":

        stream_template = { '1' : ['18000', '42000', '72000', '128000', '300000'],
                            '4' : ['18000', '42000', '72000', '128000', '300000'],
                            '8' : ['12000', '23000', '38000', '54000', '78000', '128000'],
                            '16' : ['9000', '15000', '22000', '30000', '43000', '58000'],
                            '32' : ['9000', '15000', '23000', '30000', '43000', '60000', '78000', '128000']
                            }
        #stream_template = {'32' : ['18000', '42000', '72000', '128000', '300000']}
        #stream_template = {'32' : ['350000', '400000', '600000', '800000', '50000', '16000', '8000', '10000']}
        #stream_template = {'32' : ['620000', '650000', '700000', '750000', '600000', '800000']}
        #stream_template = {'64' : ['600000', '800000', '1000000', '128000', '64000', '1200000', '32000', '16000']}
        stream_template = {'128' : ['600000', '800000', '1000000', '128000', '64000', '1200000', '32000', '16000', '8000']}
        for stream_count in stream_template.keys():
            server_count = len(test_var['ns'].split(','))
            print "Server count is " + str(server_count)

            for buffer_size in stream_template[stream_count]:
                if ',' in buffer_size:
                    local_buff = buffer_size.split(',')[0]
                    remote_buff = buffer_size.split(',')[1]
                else:
                    local_buff = buffer_size
                    remote_buff = buffer_size

                local_buff = int(local_buff)/server_count
                remote_buff = int(remote_buff)/server_count

                traffic_profile[test_type]['flow1']['instances'] = str(stream_count)
                traffic_profile[test_type]['flow1']['localbuffer'] = str(local_buff)
                traffic_profile[test_type]['flow1']['remotebuffer'] = str(remote_buff)

                run_netesto(test_type=test_type, total_calls=total_calls)
                total_calls += 1

    else:
        run_netesto(test_type=test_type, total_calls=total_calls)


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


