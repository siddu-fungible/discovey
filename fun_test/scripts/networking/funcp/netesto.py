from lib.system.fun_test import *
from lib.host.linux import Linux
import pandas as pd
from StringIO import StringIO
import random


def netesto_client(host, ssh_username="localadmin", ssh_password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=ssh_username, ssh_password=ssh_password)
    linux_obj.sudo_command(command="killall netserver; killall netesto.py; killall tcpdump")
    # linux_obj.sudo_command(command="sudo ufw disable;iptables -X;iptables -t nat -F;iptables -t nat -X;iptables -t mangle -F;iptables -t mangle -X;iptables -P INPUT ACCEPT;iptables -P OUTPUT ACCEPT;iptables -P FORWARD ACCEPT;iptables -F;iptables -L")
    # linux_obj.sudo_command(command="sysctl -w net.core.rmem_max=4194304;sysctl -w net.core.wmem_max=4194304;sysctl -w net.core.rmem_default=4194304;sysctl -w net.core.wmem_default=4194304;sysctl -w net.core.optmem_max=4194304")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem=\"4096 87380 4194304\";sysctl -w net.ipv4.tcp_wmem=\"4096 65536 4194304\";sysctl -w net.ipv4.tcp_timestamps=0;sysctl -w net.ipv4.tcp_sack=1;sysctl -w net.core.netdev_max_backlog=250000;sysctl -w net.ipv4.tcp_low_latency=1;sysctl -w net.ipv4.tcp_adv_win_scale=1;sysctl -w net.ipv4.route.flush=1")
    #linux_obj.sudo_command(command="echo 5 > /proc/sys/net/ipv4/tcp_fin_timeout")

    #linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle")
    #linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_wmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_wmem='10000 262144 33554432'")
    #linux_obj.sudo_command(command="sysctl -w sysctl -w net.ipv4.tcp_mem '33554432 33554432 33554432'")
    # linux_obj.sudo_command(command="sysctl -w fs.file-max=10000000")
    # linux_obj.sudo_command(command="sysctl -w net.core.netdev_max_backlog=250000;sysctl -w net.ipv4.tcp_low_latency=1;")
    # linux_obj.sudo_command(command="sysctl -w net.ipv4.route.flush=1")
    fun_test.sleep(message="start tcpdump now", seconds=10)
    if host == "cab02-qa-05":
        linux_obj.start_bg_process("sudo tcpdump -i hu2-f0 tcp -w netesto_%s.pcap" % random.randint(1, 90000))
        linux_obj.start_bg_process("sudo tcpdump \"tcp[tcpflags] & (tcp-syn) != 0\" -w netesto_syn_%s.pcap" % random.randint(1, 90000))
    linux_obj.command("cd ~/netesto/netesto/remote")
    linux_obj.sudo_command("./numa_script.py")

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


if __name__ == '__main__':
    hosts = ['cab02-qa-06', 'cab02-qa-02', 'cab02-qa-03', 'cab02-qa-05', 'cab02-qa-01', 'cab02-qa-07']
    threads_list = []

    for host in hosts:
        thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=netesto_client, host=host)
        threads_list.append(thread_id)

    for thread_id in threads_list:
        fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

    netesto_controller = Linux(host_ip="cab03-qa-03", ssh_username="localadmin", ssh_password="Precious1*")
    netesto_controller.command("cd ~/netesto_controller/netesto/local")
    # fun_test.sleep(message="Sleep before tests start", seconds=10)
    netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/script.alibaba_hu-hu", timeout=600)

    # netesto_controller.sudo_command(command="./netesto.py -d < fun_scripts/script.alibaba_3servers", timeout=600)

    netesto_process = netesto_controller.command("cat counter; echo").strip()
    if netesto_process != "":
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

        fun_test.log("\n======================================")
        fun_test.log("Link for throughput and Latency graphs")
        fun_test.log("======================================\n")
        fun_test.log("Throughput :  http://10.1.105.194/Chart.js/fun_plots/netesto_tp_%s.html" % netesto_process)
        fun_test.log("Latency :  http://10.1.105.194/Chart.js/fun_plots/netesto_latency_%s.html" % netesto_process)
        fun_test.log("Aggregate :  http://10.1.105.194/Chart.js/fun_plots/aggregate_%s.csv" % netesto_process)
        fun_test.log(message="No of incomplete streams = %s" % df[df['Duration'] < 57].count(1).count())
