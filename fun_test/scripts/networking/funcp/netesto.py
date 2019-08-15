from lib.system.fun_test import *
from lib.host.linux import Linux
import pandas as pd
from StringIO import StringIO


def netesto_client(host, ssh_username="localadmin", ssh_password="Precious1*"):
    linux_obj = Linux(host_ip=host, ssh_username=ssh_username, ssh_password=ssh_password)
    linux_obj.sudo_command(command="killall netserver; killall netesto.py; killall tcpdump")
    linux_obj.sudo_command(command="echo 5 > /proc/sys/net/ipv4/tcp_fin_timeout")
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_recycle")
    linux_obj.sudo_command(command="echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse")
    linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_rmem='10000 262144 33554432'")
    linux_obj.sudo_command(command="sysctl -w net.ipv4.tcp_wmem='10000 262144 33554432'")
    # linux_obj.sudo_command(command="sysctl -w fs.file-max=10000000")
    # fun_test.sleep(message="Waiting for process kills", seconds=10)
    linux_obj.command("cd ~/netesto/netesto/remote")
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

    netesto_process = netesto_controller.command("cat counter; echo").strip()
    if netesto_process != "":
        netesto_controller.command("cd ~/netesto_controller/netesto/local/fun_plots")
        netesto_controller.sudo_command(command="./aggregate.py %s" % netesto_process, timeout=150)
        csv_results = netesto_controller.command("cat aggregate.csv")
        # print csv_results
        data = StringIO(csv_results)
        df = pd.read_csv(data)
        print df
        fun_test.critical(message="No of incomplete streams = %s" % df[df['Duration'] < 60].count(1).count())

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
