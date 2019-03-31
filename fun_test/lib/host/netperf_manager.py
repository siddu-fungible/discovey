from lib.system.fun_test import fun_test
from lib.system.utils import MultiProcessingTasks
import pprint
import re


class NetperfManager:
    """Use netperf to measure throughput and latency between host pairs.
    """

    def __init__(self, linux_objs):
        self.linux_objs = linux_objs

    def setup(self):
        self.cleanup()
        result = True
        for linux_obj in self.linux_objs:

            # CPU governor
            cmd = 'cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
            linux_obj.sudo_command(cmd)
            for i in range(0, 32):  # TODO: Use actual CPU number
                linux_obj.sudo_command(
                    'echo performance > /sys/devices/system/cpu/cpu{}/cpufreq/scaling_governor'.format(i))
            linux_obj.sudo_command(cmd)

            # Tune TCP buffer
            cmds = (
                'sysctl -w net.core.rmem_max=2147483647',
                'sysctl -w net.core.wmem_max=2147483647',
                'sysctl -w net.ipv4.tcp_rmem="4096 87380 2147483647"',
                'sysctl -w net.ipv4.tcp_wmem="4096 87380 2147483647"',
                'sysctl -w net.ipv4.route.flush=1',
            )
            for cmd in cmds:
                linux_obj.sudo_command(cmd)

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

            # Install Netperf
            for pkg in ('netperf',):
                if not linux_obj.check_package(pkg):
                    cmds = (
                        'wget http://archive.ubuntu.com/ubuntu/pool/multiverse/n/netperf/netperf_2.6.0-2.1_amd64.deb',
                        'apt install ./netperf_2.6.0-2.1_amd64.deb',
                    )
                    linux_obj.sudo_command(';'.join(cmds))
                    result &= linux_obj.check_package(pkg)
                    if not result:
                        break

            # Start netserver
            if linux_obj.get_process_id_by_pattern('netserveer') is None:
                cmd = '/usr/bin/netserver'
                linux_obj.sudo_command(cmd)
                for ns in linux_obj.get_namespaces():
                    linux_obj.sudo_command('ip netns exec {} {}'.format(ns, cmd))
                result &= linux_obj.get_process_id_by_pattern('netserver') is not None
                if not result:
                    break

        #fun_test.sleep("Waiting for PTP clock sync", seconds=10)

        return result

    def cleanup(self):
        result = True
        for linux_obj in self.linux_objs:
            for process in ('ptp4l', 'phc2sys', 'netserver'):
                linux_obj.pkill(process)
                result &= linux_obj.get_process_id_by_pattern(process) is None

        return result

    def run(self, *arg_dicts):
        result = {}
        parallel = arg_dicts[0].get('parallel', 1)
        for arg_dict in arg_dicts:
            linux_obj = arg_dict.get('linux_obj')
            dip = arg_dict.get('dip')
            protocol = arg_dict.get('protocol', 'tcp')
            duration = arg_dict.get('duration', 30)
            frame_size = arg_dict.get('frame_size', 800)
            sip = arg_dict.get('sip', None)
            ns = arg_dict.get('ns', None)

        if parallel > 1:
            mp_task_obj = MultiProcessingTasks()
            rlist = []
            for i in range(1, parallel):
                # parallel-1 tasks to measure throughput
                measure_latency = False
                mp_task_obj.add_task(
                    func=do_test,
                    func_args=(linux_obj, dip, protocol, duration, frame_size, i, measure_latency, sip, ns),
                    task_key=i)
            # One task to measure latency
            measure_latency = True
            mp_task_obj.add_task(
                func=do_test,
                func_args=(linux_obj, dip, protocol, duration, frame_size, parallel, measure_latency, sip, ns),
                task_key=parallel)
            mp_task_obj.run(max_parallel_processes=parallel)
            for i in range(1, parallel+1):
                rlist.append(mp_task_obj.get_result(i))

            throughput = sum(r.get('throughput') for r in rlist)
            latency_min = rlist[parallel-1].get('latency_min')
            latency_avg = rlist[parallel-1].get('latency_avg')
            latency_max = rlist[parallel-1].get('latency_max')
            latency_P50 = rlist[parallel-1].get('latency_P50')
            latency_P90 = rlist[parallel-1].get('latency_P90')
            latency_P99 = rlist[parallel-1].get('latency_P99')

            result = {
                'throughput': round(throughput, 3),
                'latency_min': round(latency_min, 1),
                'latency_avg': round(latency_avg, 1),
                'latency_max': round(latency_max, 1),
                'latency_P50': round(latency_P50, 1),
                'latency_P90': round(latency_P90, 1),
                'latency_P99': round(latency_P99, 1),
            }

        else:
            result = do_test(linux_obj, dip=dip, protocol=protocol, duration=duration, frame_size=frame_size, ns=ns)

        throughput = result.get('throughput')
        send_size = get_send_size(protocol, frame_size)
        result.update(
            {'throughput': round(throughput / (float(send_size) / frame_size), 3),
             'pps': round(throughput * 1000000 / 8 / send_size, 2),
             }
        )

        return result


def get_send_size(protocol, frame_size):
    """Get Netperf send_size"""
    if protocol.lower() == 'udp':
        t = 'UDP_STREAM'
        send_size = frame_size-18-20-8
    elif protocol.lower() == 'tcp':
        t = 'TCP_STREAM'
        send_size = frame_size-18-20-20
    return send_size


def do_test(linux_obj, dip, protocol='tcp', duration=30, frame_size=800, cpu=None, measure_latency=False, sip=None,
            ns=None):
    """Use Netperf measure TCP throughput (Mbps) and latency (us).


    fun@FunServer04:~$ netperf -t TCP_STREAM -H 21.1.1.1 -v 2 -l 5 -f m -j -- -k "THROUGHPUT" -m 742
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 21.1.1.1 () port 0 AF_INET : demo
    THROUGHPUT=3180.24

    fun@FunServer04:~$ netperf -t TCP_RR -H 21.1.1.1 -v 2 -l 5 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT,MEAN_LATENCY" -r 742,1
    MIGRATED TCP REQUEST/RESPONSE TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 21.1.1.1 () port 0 AF_INET : demo : first burst 0
    MIN_LATENCY=49
    P50_LATENCY=77
    P90_LATENCY=108
    P99_LATENCY=123
    MAX_LATENCY=263
    THROUGHPUT=75.78
    MEAN_LATENCY=78.26
    """

    interface = linux_obj.get_interface_to_route(dip)
    mtu = linux_obj.get_mtu(interface)
    if frame_size > mtu + 18:
        fun_test.log('Frame size {} is larger than interface {} mtu {}'.format(frame_size, interface, mtu))
        return None

    # Turn off offload
    #linux_obj.sudo_command('ethtool --offload {} rx off tx off sg off tso off gso off gro off'.format(interface))

    result = {}
    throughput = latency_min = latency_avg = latency_max = latency_P50 = latency_P90 = latency_P99 = float('nan')
    if protocol.lower() == 'udp':
        t = 'UDP_STREAM'
    elif protocol.lower() == 'tcp':
        if measure_latency:
            t = 'TCP_RR'
        else:
            t = 'TCP_STREAM'
    send_size = get_send_size(protocol, frame_size)
    if not measure_latency:
        #cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
        cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "THROUGHPUT"'.format(t, dip, duration)
        pat = r'THROUGHPUT=(\d+)'
    else:
        #cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
        cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "MIN_LATENCY,MEAN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT"'.format(t, dip, duration)
        pat = r'MIN_LATENCY=(\d+).*?MEAN_LATENCY=(\d+).*?P50_LATENCY=(\d+).*?P90_LATENCY=(\d+).*?P99_LATENCY=(\d+).*?MAX_LATENCY=(\d+).*?THROUGHPUT=(\d+)'
    if sip:
        cmd = '{} -L {}'.format(cmd, sip)
    if ns:
        cmd = 'sudo ip netns exec {} {}'.format(ns, cmd)
    if cpu:
        cmd = 'taskset -c {} {}'.format(cpu, cmd)
    # TODO: use numactl if necessary
    output = linux_obj.command(cmd, timeout=duration+30)
    match = re.search(pat, output, re.DOTALL)
    if match:
        if not measure_latency:
            throughput = float(match.group(1))  # TCP/UDP throughput
            result.update(
                {'throughput': round(throughput, 3)}
            )
        else:
            latency_min = float(match.group(1))
            latency_avg = float(match.group(2))
            latency_P50 = float(match.group(3))
            latency_P90 = float(match.group(4))
            latency_P99 = float(match.group(5))
            latency_max = float(match.group(6))
            throughput = float(match.group(7))  # TCP/UDP throughput

            result.update(
                {'latency_min': round(latency_min, 1),
                 'latency_avg': round(latency_avg, 1),
                 'latency_max': round(latency_max, 1),
                 'latency_P50': round(latency_P50, 1),
                 'latency_P90': round(latency_P90, 1),
                 'latency_P99': round(latency_P99, 1),
                 'throughput': round(throughput, 3),
                 }
            )

    fun_test.log('\n{}'.format(pprint.pformat(result)))
    return result

