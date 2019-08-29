from lib.system.fun_test import fun_test
from lib.system.utils import MultiProcessingTasks
import pprint
import re


NETSERVER_PORT = 12865
NETSERVER_FIXED_PORT_CONTROL_BASE = 30000
NETSERVER_FIXED_PORT_DATA_BASE = 40000
THROUGHPUT = 'throughput'
LATENCY = 'latency'
PPS = 'pps'
LATENCY_MIN = 'latency_min'
LATENCY_AVG = 'latency_avg'
LATENCY_P50 = 'latency_P50'
LATENCY_P90 = 'latency_P90'
LATENCY_P99 = 'latency_P99'
LATENCY_MAX = 'latency_max'
LATENCY_MIN_ULOAD = 'latency_min_uload'
LATENCY_AVG_ULOAD = 'latency_avg_uload'
LATENCY_P50_ULOAD = 'latency_P50_uload'
LATENCY_P90_ULOAD = 'latency_P90_uload'
LATENCY_P99_ULOAD = 'latency_P99_uload'
LATENCY_MAX_ULOAD = 'latency_max_uload'
NA = -1

# Server has 2 socket, each CPU (Silver 4110) has 8 cores, NUMA 0: 0-7, NUMA 1: 8-15
# scaling_governor is set to performance mode.
# If locked, CPU frequency is 2.4GHz; if turbo boost, it can go up to 3.0GHz.


class PerformanceTuning:
    def __init__(self, linux_obj):
        self.linux_obj = linux_obj
        self.num_cpus = linux_obj.get_number_cpus()

    def cpu_governor(self, lock_freq=False):
        cmds = ['cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_driver',
                'for i in {0..%d}; do echo performance > /sys/devices/system/cpu/cpu$i/cpufreq/scaling_governor; done' % (self.num_cpus-1),
                'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor',
                ]
        if lock_freq:
            cmds.extend([
                #'cpupower frequency-set -f {}'.format(CPU_FREQ),
                'cpupower idle-set -e 0',
                'cpupower idle-set -d 1',
                'cpupower idle-set -d 2',
                'cpupower idle-set -d 3',
                'cpupower idle-set -d 4',
            ])
        else:
            cmds.extend([
                'cpupower idle-set -E',
            ])
        cmds.extend([
            'cpupower monitor',
            'cat /proc/cpuinfo | grep MHz',
        ])
        self.linux_obj.sudo_command(';'.join(cmds))

    def tcp(self):
        cmds = (
            'sysctl -w net.core.rmem_max=4194304',
            'sysctl -w net.core.wmem_max=4194304',
            'sysctl -w net.core.rmem_default=4194304',
            'sysctl -w net.core.wmem_default=4194304',
            'sysctl -w net.core.optmem_max=4194304',
            'sysctl -w net.ipv4.tcp_rmem="4096 87380 4194304"',
            'sysctl -w net.ipv4.tcp_wmem="4096 65536 4194304"',
            'sysctl -w net.ipv4.tcp_timestamps=0',
            'sysctl -w net.ipv4.tcp_sack=1',
            'sysctl -w net.core.netdev_max_backlog=250000',
            'sysctl -w net.ipv4.tcp_low_latency=1',
            'sysctl -w net.ipv4.tcp_adv_win_scale=1',
            'sysctl -w net.ipv4.route.flush=1',
        )
        self.linux_obj.sudo_command(';'.join(cmds))

    def iptables(self):
        cmds = (
            'sudo ufw disable',
            'iptables -X',
            'iptables -t nat -F',
            'iptables -t nat -X',
            'iptables -t mangle -F',
            'iptables -t mangle -X',
            'iptables -P INPUT ACCEPT',
            'iptables -P OUTPUT ACCEPT',
            'iptables -P FORWARD ACCEPT',
            'iptables -F',
            'iptables -L',
        )
        self.linux_obj.sudo_command(';'.join(cmds))

    def mlnx_tune(self, profile='HIGH_THROUGHPUT'):
        """profile: HIGH_THROUGHPUT, or LOW_LATENCY_VMA"""
        cmds = (
            'mlnx_tune -p {}'.format(profile),
        )
        self.linux_obj.sudo_command(';'.join(cmds))

    def interrupt_coalesce(self, interfaces, disable=True):
        for interface in interfaces:
            if disable:
                cmds = (
                    'ethtool --coalesce {} rx-usecs 0 tx-usecs 0 rx-frames 1 tx-frames 1 adaptive-rx off'.format(
                        interface),
                )
            else:
                cmds = (
                    'ethtool --coalesce {} rx-usecs 8 tx-usecs 16 rx-frames 128 tx-frames 32 adaptive-rx on'.format(
                        interface),
                )
        self.linux_obj.sudo_command(';'.join(cmds))

    def irq_affinity(self):
        # Set in performance.py
        pass


class NetperfManager:
    """Use netperf to measure throughput and latency between host pairs.
    """

    def __init__(self, linux_objs):
        self.linux_objs = linux_objs
        self.perf_tuning_objs = [PerformanceTuning(linux_obj) for linux_obj in linux_objs]

    def setup(self):
        self.cleanup()
        result = True

        for perf_tuning_obj in self.perf_tuning_objs:
            #perf_tuning_obj.cpu_governor(lock_freq=False)  # This is done in self.run()
            perf_tuning_obj.tcp()
            perf_tuning_obj.iptables()

        for linux_obj in self.linux_objs:
            linux_obj.sudo_command('sysctl net.ipv6.conf.all.disable_ipv6=1')

            # All the required packages are manually installed, so no need to do it in script
            ## Install linuxptp package
            #for pkg in ('linuxptp',):
            #    result &= linux_obj.install_package(pkg)
            #    if not result:
            #        break
            #
            ## Start ptp4l for PTP clock, and phy2c for sync system clock to PTP clock
            #if (linux_obj.get_process_id_by_pattern('ptp4l') is None or
            #            linux_obj.get_process_id_by_pattern('phc2sys') is None):
            #    cmds = (
            #        'ptp4l -i {} -2 &'.format(linux_obj.get_mgmt_interface()),
            #        'phc2sys -a -rr &',
            #    )
            #    for cmd in cmds:
            #        linux_obj.sudo_command(cmd)
            #    result &= (linux_obj.get_process_id_by_pattern('ptp4l') is not None) & (
            #        linux_obj.get_process_id_by_pattern('phc2sys') is not None)
            #    if not result:
            #        break

            ## Install Netperf
            #for pkg in ('netperf',):
            #    if not linux_obj.check_package(pkg):
            #        cmds = (
            #            'wget http://archive.ubuntu.com/ubuntu/pool/multiverse/n/netperf/netperf_2.6.0-2.1_amd64.deb',
            #            'apt install ./netperf_2.6.0-2.1_amd64.deb',
            #        )
            #        linux_obj.sudo_command(';'.join(cmds))
            #        result &= linux_obj.check_package(pkg)
            #        if not result:
            #            break
            #
            ## Start netserver
            #if linux_obj.get_process_id_by_pattern('netserveer') is None:
            #    #cmd = 'taskset -c 8-15 /usr/bin/netserver'  # NU server NIC and F1 are both in NUA 1
            #    cmd = '/usr/bin/netserver'  # NU server NIC and F1 are both in NUA 1
            #    linux_obj.sudo_command(cmd)
            #    for ns in linux_obj.get_namespaces():
            #        linux_obj.sudo_command('ip netns exec {} {}'.format(ns, cmd))
            #    result &= linux_obj.get_process_id_by_pattern('netserver') is not None
            #    if not result:
            #        break

        #fun_test.sleep("Waiting for PTP clock sync", seconds=10)

        return result

    def start_netserver(self, linux_obj, cpu_list=None, fixed_netperf_port=False):
        linux_obj.pkill('netserver')
        if fixed_netperf_port:
            if cpu_list:
                cmds = []
                for c in cpu_list:
                    cmds.append('taskset -c {} netserver -p {}'.format(c, c+NETSERVER_FIXED_PORT_CONTROL_BASE))  # Netperf control ports
                cmds.append('taskset -c {} netserver -p {}'.format(c, c-1+NETSERVER_FIXED_PORT_CONTROL_BASE))  # for TCP_RR
                cmd = ';'.join(cmds)
        else:
            if cpu_list:
                cmd = 'taskset -c {} netserver'.format(','.join([str(c) for c in cpu_list]))
            else:
                cmd = 'netserver'
        linux_obj.sudo_command(cmd)
        return linux_obj.get_process_id_by_pattern('netserver') is not None

    def cleanup(self):
        result = True
        for linux_obj in self.linux_objs:
            #for process in ('ptp4l', 'phc2sys', 'netserver'):
            for process in ('netserver',):
                linux_obj.pkill(process)
                result &= linux_obj.get_process_id_by_pattern(process) is None

        return result

    def run(self, *arg_dicts):
        result = {}

        # Do throughput test first, and latency test last
        #for measure_latency in (False, True):
        # Test - 1: throughput only, 2: latency only, 3: latency under throughput load
        #for test in (1, 2, 3, ):
        for test in (2, 3, ):
            if test == 2:
                for perf_tuning_obj in self.perf_tuning_objs:
                    perf_tuning_obj.cpu_governor(lock_freq=True)
                    perf_tuning_obj.mlnx_tune(profile='LOW_LATENCY_VMA')
                    perf_tuning_obj.interrupt_coalesce(['fpg0',], disable=True)  # TODO: pass interface in a nice way
            else:
                for perf_tuning_obj in self.perf_tuning_objs:
                    perf_tuning_obj.cpu_governor(lock_freq=False)
                    perf_tuning_obj.mlnx_tune(profile='HIGH_THROUGHPUT')
                    perf_tuning_obj.interrupt_coalesce(['fpg0',], disable=False)

            mp_task_obj = MultiProcessingTasks()

            direction_list = []
            dip_list = []
            for arg_dict in arg_dicts:
                num_flows = arg_dict.get('num_flows', 1)
                linux_obj = arg_dict.get('linux_obj')
                linux_obj_dst = arg_dict.get('linux_obj_dst')
                direction = arg_dict.get('suffix')
                direction_list.append(direction)
                dip = arg_dict.get('dip')
                dip_list.append(dip)
                protocol = arg_dict.get('protocol', 'tcp')
                duration = arg_dict.get('duration', 30)
                frame_size = arg_dict.get('frame_size', 800)
                sip = arg_dict.get('sip', None)
                ns = arg_dict.get('ns', None)
                cpu_list_server = sorted(arg_dict.get('cpu_list_server'))[::-1]  # reversed order
                cpu_list_client = sorted(arg_dict.get('cpu_list_client'))[::-1]  # reversed order
                fixed_netperf_port = arg_dict.get('fixed_netperf_port', False)
                csi_perf_obj = arg_dict.get('csi_perf_obj', None)

                if test == 2:
                    num_processes = 1
                    measure_latency = True
                else:
                    num_processes = num_flows
                    measure_latency = False
                netserver_cpu_list = []
                for i in range(0, num_processes):
                    #cpu = 15 - i  # TODO: assume host has 2 CPUs, each has 8 cores, and NIC NUMA is 1
                    cpu = cpu_list_client[i % len(cpu_list_client)]
                    netserver_cpu = cpu_list_server[i % len(cpu_list_server)]
                    netserver_cpu_list.append(netserver_cpu)
                    mp_task_obj.add_task(
                        func=do_test,
                        func_args=(linux_obj, dip, protocol, duration, frame_size, cpu, measure_latency, sip, ns, fixed_netperf_port),
                        task_key='{}_{}_{}'.format(direction, dip, i))
                if test == 3:
                    #if num_flows == 1:
                    #    cpu -= 1
                    #    cpu_list.append(cpu)
                    measure_latency = True
                    mp_task_obj.add_task(
                        func=do_test,
                        func_args=(linux_obj, dip, protocol, duration, frame_size, cpu, measure_latency, sip, ns, fixed_netperf_port),
                        task_key='{}_{}_{}_latency'.format(direction, dip, i))

                # Start netserver
                if not self.start_netserver(linux_obj_dst, cpu_list=netserver_cpu_list, fixed_netperf_port=fixed_netperf_port):
                    fun_test.critical('Failed to start netserver!')
                    netserver_ready = False
                    break
                else:
                    netserver_ready = True

            if not netserver_ready:
                break

            if test == 3:  # +1 for latency under load
                # Get perf for throughput test, no need to latency only test
                if csi_perf_obj:
                    csi_perf_obj.start(f1_index=0)
                mp_task_obj.run(max_parallel_processes=(num_processes+1)*len(direction_list), threading=True)
                if csi_perf_obj:
                    csi_perf_obj.stop(f1_index=0)
            else:
                mp_task_obj.run(max_parallel_processes=num_processes*len(direction_list), threading=True)

            rdict = {}
            for direction in direction_list:
                if direction not in result:
                    result.update(
                        {direction: {}}
                    )
                rdict.update(
                    {direction: []}
                )
                for dip in dip_list:
                    for i in range(0, num_processes):
                        rdict[direction].append(mp_task_obj.get_result('{}_{}_{}'.format(direction, dip, i)))
                    if test == 3:
                        rdict[direction].append(mp_task_obj.get_result('{}_{}_{}_latency'.format(direction, dip, i)))
                fun_test.log('NetperfManager aggregated netperf result of {}\n{}'.format(direction, rdict[direction]))

                if test == 2:
                    lat_dict = rdict[direction][-1]  # latency result is the last element
                    for k, v in lat_dict.items():
                        result[direction].update(
                            {k: round(v, 1) if v != NA else v}
                        )
                    fun_test.log('NetperfManager latency result\n{}'.format(result))

                elif test == 1:
                    throughput = sum(r.get(THROUGHPUT) for r in rdict[direction] if r.get(THROUGHPUT) != NA)
                    if not throughput:
                        result[direction].update(
                            {THROUGHPUT: NA}
                        )
                    else:
                        result[direction].update(
                            {THROUGHPUT: calculate_ethernet_throughput(protocol, frame_size, round(throughput, 3)),
                             PPS: calculate_pps(protocol, frame_size, throughput),
                            }
                        )
                    fun_test.log('NetperfManager throughput result\n{}'.format(result))

                elif test == 3:
                    # throughput
                    throughput = sum(r.get(THROUGHPUT) for r in rdict[direction] if r.get(THROUGHPUT, NA) != NA)
                    if not throughput:
                        result[direction].update(
                            {THROUGHPUT: NA}
                        )
                    else:
                        result[direction].update(
                            {THROUGHPUT: calculate_ethernet_throughput(protocol, frame_size, round(throughput, 3)),
                             PPS: calculate_pps(protocol, frame_size, throughput),
                            }
                        )
                    fun_test.log('NetperfManager throughput result\n{}'.format(result))
                    # latency
                    lat_dict = rdict[direction][-1]  # latency result is the last element
                    for k, v in lat_dict.items():
                        result[direction].update(
                            {'{}_uload'.format(k): round(v, 1) if v != NA else v}
                        )
                    fun_test.log('NetperfManager latency under load result\n{}'.format(result))

            if fixed_netperf_port:
                fun_test.sleep("Sleeping for 60 sec waiting for TCP TIME_WAIT to CLOSE", seconds=60)

        result_cooked = {}
        for direction in result:
            for k, v in result[direction].items():
                result_cooked.update(
                    {'{}_{}'.format(k, direction): v}
                )

        return result_cooked


def get_send_size(protocol, frame_size):
    """Get Netperf send_size"""
    if protocol.lower() == 'udp':
        send_size = frame_size-18-20-8
    elif protocol.lower() == 'tcp':
        send_size = frame_size-18-20-20
    return send_size


def calculate_ethernet_throughput(protocol, frame_size, payload_throughput):
    send_size = get_send_size(protocol, frame_size)
    return round(payload_throughput / (float(send_size) / (frame_size+20)), 3)  # IPG 20B


def calculate_pps(protocol, frame_size, throughput):
    send_size = get_send_size(protocol, frame_size)
    return round(throughput * 1000000 / 8 / send_size, 2)


def do_test(linux_obj, dip, protocol='tcp', duration=30, frame_size=800, cpu=None, measure_latency=False, sip=None,
            ns=None, fixed_netperf_port=False):
    """Use Netperf measure TCP throughput (Mbps) and latency (us).


    fun@FunServer04:~$ netperf -t TCP_STREAM -H 21.1.1.1 -v 2 -l 5 -f m -j -- -k "THROUGHPUT" -m 742
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 21.1.1.1 () port 0 AF_INET : demo
    THROUGHPUT=3180.24

    fun@FunServer04:~$ netperf -t TCP_RR -H 21.1.1.1 -v 2 -l 5 -w 100 -b 1 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT,MEAN_LATENCY" -r 742,1
    MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 21.1.1.1 () port 0 AF_INET : demo : first burst 0
    MIN_LATENCY=49
    P50_LATENCY=77
    P90_LATENCY=108
    P99_LATENCY=123
    MAX_LATENCY=263
    THROUGHPUT=75.78
    MEAN_LATENCY=78.26
    """

    #interface = linux_obj.get_interface_to_route(dip)
    #mtu = linux_obj.get_mtu(interface)
    #if frame_size > mtu + 18:
    #    fun_test.log('Frame size {} is larger than interface {} mtu {}'.format(frame_size, interface, mtu))
    #    return None

    # Turn off offload
    #linux_obj.sudo_command('ethtool --offload {} rx off tx off sg off tso off gso off gro off'.format(interface))

    try:
        fun_test.log("1.Spawn PID: {}".format(linux_obj.spawn_pid))
    except Exception as ex:
        fun_test.critical(ex)

    if measure_latency:
        result = {
            LATENCY_MIN: NA,
            LATENCY_AVG: NA,
            LATENCY_MAX: NA,
            LATENCY_P50: NA,
            LATENCY_P90: NA,
            LATENCY_P99: NA,
        }
    else:
        result = {
            THROUGHPUT: NA,
        }

    if protocol.lower() == 'udp':
        t = 'UDP_STREAM'
    elif protocol.lower() == 'tcp':
        if measure_latency:
            t = 'TCP_RR'
        else:
            t = 'TCP_STREAM'
    send_size = get_send_size(protocol, frame_size)
    if fixed_netperf_port:
        if not measure_latency:
            # cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
            # for TCP_RR, make port NETSERVER_FIXED_PORT_CONTROL_BASE+cpu-1 to avoid conflict with TCP_STREAM
            cmd = 'netperf -t {0} -H {1} -v 2 -l {2} -f m -j -p {3},{3} -- -k "THROUGHPUT" -P {4}'.format(
                t, dip, duration, NETSERVER_FIXED_PORT_CONTROL_BASE+cpu-1, NETSERVER_FIXED_PORT_DATA_BASE+cpu-1)
            pat = r'THROUGHPUT=(\d+)'
            pat = r'THROUGHPUT=(\d+\.\d+|\d+)'
        else:
            # cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
            # 1 request per 100 msec
            cmd = 'netperf -t {0} -H {1} -v 2 -l {2} -w 10 -b 100 -f m -j -p {3},{3} -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY" -r1,1 -P {4}'.format(
                t, dip, duration, NETSERVER_FIXED_PORT_CONTROL_BASE+cpu, NETSERVER_FIXED_PORT_DATA_BASE+cpu)
            pat = r'MIN_LATENCY=(\d+\.\d+|\d+).*?MEAN_LATENCY=(\d+\.\d+|\d+).*?P50_LATENCY=(\d+\.\d+|\d+).*?P90_LATENCY=(\d+\.\d+|\d+).*?P99_LATENCY=(\d+\.\d+|\d+).*?MAX_LATENCY=(\d+\.\d+|\d+)'
    else:
        if not measure_latency:
            #cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
            cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "THROUGHPUT"'.format(t, dip, duration)
            pat = r'THROUGHPUT=(\d+)'
            pat = r'THROUGHPUT=(\d+\.\d+|\d+)'
        else:
            #cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
            # 1 request per 100 msec
            cmd = 'netperf -t {} -H {} -v 2 -l {} -w 10 -b 100 -f m -j -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY" -r1,1'.format(t, dip, duration)
            pat = r'MIN_LATENCY=(\d+\.\d+|\d+).*?MEAN_LATENCY=(\d+\.\d+|\d+).*?P50_LATENCY=(\d+\.\d+|\d+).*?P90_LATENCY=(\d+\.\d+|\d+).*?P99_LATENCY=(\d+\.\d+|\d+).*?MAX_LATENCY=(\d+\.\d+|\d+)'
    if sip:
        cmd = '{} -L {}'.format(cmd, sip)
    if ns:
        cmd = 'sudo ip netns exec {} {}'.format(ns, cmd)
    if cpu:
        cmd = 'taskset -c {} {}'.format(cpu, cmd)
    # TODO: use numactl if necessary
    try:
        output = linux_obj.command(cmd, timeout=duration+30)
        match = re.search(pat, output, re.DOTALL)
        if match:
            if not measure_latency:
                throughput = float(match.group(1))  # TCP/UDP throughput
                result.update(
                    {THROUGHPUT: round(throughput, 3)}
                )
            else:
                latency_min = float(match.group(1))
                latency_avg = float(match.group(2))
                latency_P50 = float(match.group(3))
                latency_P90 = float(match.group(4))
                latency_P99 = float(match.group(5))
                latency_max = float(match.group(6))

                result.update(
                    {LATENCY_MIN: round(latency_min, 1),
                     LATENCY_AVG: round(latency_avg, 1),
                     LATENCY_MAX: round(latency_max, 1),
                     LATENCY_P50: round(latency_P50, 1),
                     LATENCY_P90: round(latency_P90, 1),
                     LATENCY_P99: round(latency_P99, 1),
                     }
                )
    except:
        pass

    fun_test.log('netperf {} result\n{}'.format(LATENCY if measure_latency else THROUGHPUT, pprint.pformat(result)))
    return result

