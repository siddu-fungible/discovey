from lib.system.fun_test import fun_test
import math
import pprint
import re


class IPerfManager:
    """1. Use iperf2/iperf3 to measure throughput/jitter and use owping to measure latency/jitter between host pairs.
       2. Or, use netperf to measure throughput and latency between host pairs.
    """

    def __init__(self, linux_objs):
        self.linux_objs = linux_objs

    def setup(self):
        self.cleanup()
        result = True
        for linux_obj in self.linux_objs:

            # Install linuxptp package
            for pkg in ('linuxptp',):
                result &= linux_obj.install_package(pkg)
                if not result:
                    break

            # Start ptp4l for PTP clock, and phy2c for sync system clock to PTP clock
            if (linux_obj.get_process_id_by_pattern('ptp4l') is None or
                        linux_obj.get_process_id_by_pattern('phc2sys') is None):
                cmds = (
                    'ptp4l -i {} -2 &'.format(linux_obj.get_mgmt_interface()),
                    'phc2sys -a -rr &',
                )
                for cmd in cmds:
                    linux_obj.sudo_command(cmd)
                result &= (linux_obj.get_process_id_by_pattern('ptp4l') is not None) & (
                    linux_obj.get_process_id_by_pattern('phc2sys') is not None)
                if not result:
                    break

            ## Install iperf/iperf3 and start server mode
            #for pkg in ('iperf', 'iperf3'):
            #    result &= linux_obj.install_package(pkg)
            #    if not result:
            #        break
            #    if linux_obj.get_process_id_by_pattern(pkg) is None:
            #        linux_obj.command('{} -sD'.format(pkg))
            #        for ns in linux_obj.get_namespaces():
            #            linux_obj.sudo_command('ip netns exec {} {} -sD'.format(ns, pkg))
            #        result &= linux_obj.get_process_id_by_pattern(pkg) is not None
            #        if not result:
            #            break
            #
            ## Install perfsonar-tools for owampd and owping
            #for pkg in ('perfsonar-tools',):
            #    cmds = (
            #        'cd /etc/apt/sources.list.d/',
            #        'wget http://downloads.perfsonar.net/debian/perfsonar-release.list',
            #        'wget -qO - http://downloads.perfsonar.net/debian/perfsonar-debian-official.gpg.key | apt-key add -',
            #    )
            #    linux_obj.sudo_command(';'.join(cmds))
            #    result &= linux_obj.install_package(pkg)
            #    if not result:
            #        break
            #
            ## Start owampd server
            #if linux_obj.get_process_id_by_pattern('owampd') is None:
            #    cmd = '/usr/sbin/owampd -c /etc/owamp-server -R /var/run'
            #    linux_obj.sudo_command(cmd)
            #    for ns in linux_obj.get_namespaces():
            #        linux_obj.sudo_command('ip netns exec {} {}'.format(ns, cmd))
            #    result &= linux_obj.get_process_id_by_pattern('owampd') is not None
            #    if not result:
            #        break

            # Install netperf
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

        fun_test.sleep("Waiting for PTP clock sync", seconds=10)

        return result

    def cleanup(self):
        result = True
        for linux_obj in self.linux_objs:
            for process in ('ptp4l', 'phc2sys', 'iperf', 'iperf3', 'owampd', 'netserver'):
                linux_obj.pkill(process)
                result &= linux_obj.get_process_id_by_pattern(process) is None

        return result

    def run(self, *arg_dicts):
        result = {}
        concurrent = False  # TODO: pass this arg in func
        if concurrent:
            # TODO: run test concurrently
            pass
        else:
            for arg_dict in arg_dicts:
                linux_obj = arg_dict.get('linux_obj')
                dip = arg_dict.get('dip')
                tool = arg_dict.get('tool', 'iperf3')
                protocol = arg_dict.get('protocol', 'udp')
                parallel = arg_dict.get('parallel', 1)
                duration = arg_dict.get('duration', 10)
                frame_size = arg_dict.get('frame_size', 1518)
                bw = arg_dict.get('bw', '5m')
                result = do_test(linux_obj, dip=dip, tool=tool, protocol=protocol, parallel=parallel,
                                 duration=duration, frame_size=frame_size, bw=bw)
        return result


def do_test(linux_obj, dip, tool='iperf3', protocol='udp', parallel=1, duration=10, frame_size=1518, bw='10m'):
    """Use iperf2/iperf3 to measure TCP/UDP throughput, and use owping by sending UDP packets to measure latency.

    Here are iperf3, owping, and netperf output examples.

    localadmin@cadence-pc-5:~$ iperf3 -c 19.1.1.1 -u -l 1400 -b 0.1m
    Connecting to host 19.1.1.1, port 5201
    [  5] local 53.1.1.5 port 54203 connected to 19.1.1.1 port 5201
    [ ID] Interval           Transfer     Bitrate         Total Datagrams
    [  5]   0.00-1.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   1.00-2.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   2.00-3.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   3.00-4.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   4.00-5.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   5.00-6.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   6.00-7.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   7.00-8.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   8.00-9.00   sec  12.3 KBytes   101 Kbits/sec  9
    [  5]   9.00-10.00  sec  12.3 KBytes   101 Kbits/sec  9
    - - - - - - - - - - - - - - - - - - - - - - - - -
    [ ID] Interval           Transfer     Bitrate         Jitter    Lost/Total Datagrams
    [  5]   0.00-10.00  sec   123 KBytes   101 Kbits/sec  0.000 ms  0/90 (0%)  sender
    [  5]   0.00-10.59  sec   123 KBytes  95.2 Kbits/sec  3.844 ms  0/90 (0%)  receiver

    iperf Done.
    localadmin@cadence-pc-5:~$
    localadmin@cadence-pc-5:~$ iperf3 -c 19.1.1.1 -l 1400 -b 0.1m
    Connecting to host 19.1.1.1, port 5201
    [  5] local 53.1.1.5 port 46886 connected to 19.1.1.1 port 5201
    [ ID] Interval           Transfer     Bitrate         Retr  Cwnd
    [  5]   0.00-1.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   1.00-2.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   2.00-3.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   3.00-4.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   4.00-5.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   5.00-6.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   6.00-7.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   7.00-8.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   8.00-9.00   sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    [  5]   9.00-10.00  sec  12.3 KBytes   101 Kbits/sec    0   14.1 KBytes
    - - - - - - - - - - - - - - - - - - - - - - - - -
    [ ID] Interval           Transfer     Bitrate         Retr
    [  5]   0.00-10.00  sec   123 KBytes   101 Kbits/sec    0             sender
    [  5]   0.00-10.59  sec   122 KBytes  94.2 Kbits/sec                  receiver

    iperf Done.
    localadmin@cadence-pc-5:~$ iperf3 -v
    iperf 3.6 (cJSON 1.5.2)
    Linux cadence-pc-5 4.15.0-45-generic #48-Ubuntu SMP Tue Jan 29 16:28:13 UTC 2019 x86_64
    Optional features available: CPU affinity setting, IPv6 flow label, TCP congestion algorithm setting, sendfile / zerocopy, socket pacing


    localadmin@nu-lab-01:~$ owping -c 10 -s 4 -i 0.1 hu-lab-01 -a 98 -a 99
    Approximately 3.9 seconds until results available

    --- owping statistics from [nu-lab-01.fungible.local]:8915 to [hu-lab-01]:9270 ---
    SID:	0a012817e00ef46a64d737e862a44f3a
    first:	2019-02-13T11:54:19.387
    last:	2019-02-13T11:54:20.139
    10 sent, 0 lost (0.000%), 0 duplicates
    one-way delay min/median/max = -12.5/-12.5/-12.4 ms, (err=9.01 ms)
    one-way jitter = 0 ms (P95-P50)
    Percentiles:
    	99.0: -12.5 ms
    TTL not reported
    no reordering


    --- owping statistics from [hu-lab-01]:8848 to [nu-lab-01.fungible.local]:8920 ---
    SID:	0a012818e00ef46a68dfd8e9e4886fc9
    first:	2019-02-13T11:54:19.541
    last:	2019-02-13T11:54:20.178
    10 sent, 0 lost (0.000%), 0 duplicates
    one-way delay min/median/max = 12.8/12.9/12.8 ms, (err=9.01 ms)
    one-way jitter = 0 ms (P95-P50)
    Percentiles:
    	99.0: 12.9 ms
    TTL not reported
    no reordering

    localadmin@nu-lab-01:~$

    localadmin@nu-lab-01:~$ netperf -t UDP_STREAM -H hu-lab-01 -v 1 -l 1 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m 18
    MIGRATED UDP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to hu-lab-01.fungible.local () port 0 AF_INET : demo
    MIN_LATENCY=2
    P50_LATENCY=2
    P90_LATENCY=3
    P99_LATENCY=6
    MAX_LATENCY=71
    THROUGHPUT=55.07
    localadmin@nu-lab-01:~$
    localadmin@nu-lab-01:~$ netperf -t UDP_STREAM -H hu-lab-01 -v 1 -l 1 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m 1472
    MIGRATED UDP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to hu-lab-01.fungible.local () port 0 AF_INET : demo
    MIN_LATENCY=1
    P50_LATENCY=4
    P90_LATENCY=7
    P99_LATENCY=579
    MAX_LATENCY=854
    THROUGHPUT=936.77
    localadmin@nu-lab-01:~$
    localadmin@nu-lab-01:~$ netperf -t TCP_STREAM -H hu-lab-01 -v 1 -l 10 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m 6
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to hu-lab-01.fungible.local () port 0 AF_INET : demo
    MIN_LATENCY=0
    P50_LATENCY=1
    P90_LATENCY=1
    P99_LATENCY=6
    MAX_LATENCY=366
    THROUGHPUT=54.80
    localadmin@nu-lab-01:~$ netperf -t TCP_STREAM -H hu-lab-01 -v 1 -l 1 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m 6
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to hu-lab-01.fungible.local () port 0 AF_INET : demo
    MIN_LATENCY=0
    P50_LATENCY=1
    P90_LATENCY=1
    P99_LATENCY=5
    MAX_LATENCY=262
    THROUGHPUT=55.19
    localadmin@nu-lab-01:~$ netperf -t TCP_STREAM -H hu-lab-01 -v 1 -l 1 -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m 1460
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to hu-lab-01.fungible.local () port 0 AF_INET : demo
    MIN_LATENCY=1
    P50_LATENCY=2
    P90_LATENCY=3
    P99_LATENCY=6
    MAX_LATENCY=7762
    THROUGHPUT=916.25
    """

    interface = linux_obj.get_interface_to_route(dip)
    mtu = linux_obj.get_mtu(interface)
    if frame_size > mtu + 18:
        fun_test.log('Frame size {} is larger than interface {} mtu {}'.format(frame_size, interface, mtu))
        return None

    # Turn off offload
    linux_obj.sudo_command('ethtool --offload {} rx off tx off sg off tso off gso off gro off'.format(interface))

    result = {}

    if tool in ('iperf3', 'iperf'):

        def get_time_factor(unit):
            """Time in us."""
            if unit.lower() == 'ms':
                factor = 1000.0
            elif unit.lower() == 'us':
                factor = 1.0
            elif unit.lower() == 'ns':
                factor = 0.001
            return factor

        def get_rate_factor(unit):
            """Throughput in Mbps."""
            if unit.upper() == 'G':
                factor = 1000.0
            elif unit.upper() == 'M':
                factor = 1.0
            elif unit.upper() == 'K':
                factor = 0.001
            return factor

        if protocol.lower() not in ('tcp', 'udp'):
            fun_test.log('Protocol {} is not supported.'.format(protocol))
            return None

        deviation = 0.02  # 2%

        # Throughput Test

        throughput = pps = jitter = float('nan')
        max_data_throughput = 0.0
        bw_unit = bw[-1]
        factor = get_rate_factor(bw_unit)
        bw_val = float(bw.rstrip('kmgKMG')) * factor  # Convert bandwidth to Mbps

        left, right = 0.0, bw_val
        target_bw_val = (left + right) / 2  # Start test from 1/2 of target bindwidth
        while left <= right * (1 - deviation):
            target_bw = '{}{}'.format(target_bw_val, bw_unit)

            if protocol.lower() == 'udp':
                payload_size = frame_size-18-20-8
                cmd = '{} -c {} -i 1 -P {} -u -t {} -l {} -b {}'.format(tool, dip, parallel, duration, payload_size, target_bw)
                pat = r'sender.*?0.00-(\S+)\s+sec.*?(\S+) ([K|M|G])bits/sec\s+(\S+) ([m|u|n]s).*?(\d+)/(\d+).*?receiver'
            elif protocol.lower() == 'tcp':
                payload_size = frame_size-18-20-20
                cmd = '{} -c {} -i 1 -P {} -t {} -M {} -b {}'.format(tool, dip, parallel, duration, payload_size, target_bw)
                pat = r'sender.*?0.00-(\S+)\s+sec.*?(\S+) ([K|M|G])bits/sec\s+receiver'

            output = linux_obj.command(cmd, timeout=duration+30)
            match = re.search(pat, output, re.DOTALL)

            if match:
                if protocol.lower() == 'udp':
                    actual_duration = float(match.group(1))
                    rate_unit = match.group(3)
                    factor = get_rate_factor(rate_unit)
                    data_throughput = float(match.group(2)) * factor  # UDP throughput
                    jitter_unit = match.group(5)
                    factor = get_time_factor(jitter_unit)
                    jitter = float(match.group(4)) * factor
                    lost = int(match.group(6))
                    total = int(match.group(7))

                    if data_throughput > max_data_throughput:
                        max_data_throughput = data_throughput
                        packet_count = total - lost
                        throughput = float(packet_count) * frame_size * 8 / 1000000 / actual_duration  # Ethernet throughput in Mbps
                        pps = float(packet_count) / actual_duration

                elif protocol.lower() == 'tcp':
                    actual_duration = float(match.group(1))
                    rate_unit = match.group(3)
                    factor = get_rate_factor(rate_unit)
                    data_throughput = float(match.group(2)) * factor  # TCP throughput

                    if data_throughput > max_data_throughput:
                        max_data_throughput = data_throughput
                        throughput = data_throughput / (float(payload_size) / frame_size)  # Ethernet throughput in Mbps
                        pps = throughput * 1000000 / (frame_size * 8)

                fun_test.log('{} traffic duration: {} sec, throughput: {} Mbits/sec'.format(
                    protocol.upper(), actual_duration, data_throughput))
                fun_test.log('{} traffic pps: {}, Ethernet throughput: {} Mbits/sec'.format(
                    protocol.upper(), pps, throughput))

                if data_throughput < target_bw_val*(1-deviation):
                    break

                left = target_bw_val
                target_bw_val = (left + right) / 2
                fun_test.sleep("Waiting for buffer drain..", seconds=30)

            else:
                right = target_bw_val
                target_bw_val = (left + right) / 2
                fun_test.sleep("Waiting for buffer drain..", seconds=120)

        result.update(
            {'throughput': round(throughput, 3),
             'pps': round(pps, 2),
             'jitter': round(jitter, 1),
             }
        )

        fun_test.log('\n{}'.format(pprint.pformat(result)))

        # Latency test

        percentile = 99.0
        latency_min = latency_avg = latency_max = jitter = latency_percentile = float('nan')

        packet_count = int(pps*actual_duration)
        left, right = 0, packet_count
        target_packet_count = packet_count  # Start from most right instead of middle
        padding_size = frame_size-18-20-8-14
        while left <= right * (1 - deviation):
            interval = float(actual_duration) / float(target_packet_count)
            cmd = 'owping -c {} -s {} -i {} -a {} {}'.format(target_packet_count, padding_size, interval, percentile, dip)
            output = linux_obj.command(cmd, timeout=duration+30)
            pat = r'from.*?to.*?{}.*?{} sent, 0 lost.*?0 duplicates.*?min/median/max = (\S+)/(\S+)/(\S+) ([mun]s).*?jitter = (\S+) [mun]s.*?Percentiles.*?{}: (\S+) [mun]s.*?no reordering'.format(dip, target_packet_count, percentile)
            match = re.search(pat, output, re.DOTALL)
            if match:
                unit = match.group(4)
                factor = get_time_factor(unit)
                latency_min = float(match.group(1)) * factor
                latency_avg = float(match.group(2)) * factor
                latency_max = float(match.group(3)) * factor
                jitter = float(match.group(5)) * factor
                latency_percentile = float(match.group(6)) * factor

                left = target_packet_count
                target_packet_count = (left + right) / 2
                fun_test.sleep("Waiting for buffer drain..", seconds=30)

            elif not re.search(r'owping statistics from.*?to.*?{}'.format(dip), output):  # Error
                break
            else:
                right = target_packet_count
                target_packet_count = (left + right) / 2
                fun_test.sleep("Waiting for buffer drain..", seconds=120)

        result.update(
            {'latency_min': round(latency_min, 1),
             'latency_avg': round(latency_avg, 1),
             'latency_max': round(latency_max, 1),
             'latency_P{}'.format(percentile): round(latency_percentile, 1),
             }
        )

        if result.get('jitter', 0.0) == 0 or math.isnan(result.get('jitter', 0.0)):
            result.update(
                {'jitter': round(jitter, 1)}
            )

    elif tool == 'netperf':  # TODO: do multiple netperf sessions parallelly

        throughput = latency_min = latency_avg = latency_max = latency_P90 = latency_P99 = float('nan')
        if protocol.lower() == 'udp':
            t = 'UDP_STREAM'
            send_size = frame_size-18-20-8
        elif protocol.lower() == 'tcp':
            t = 'TCP_STREAM'
            send_size = frame_size-18-20-20
        cmd = 'netperf -t {} -H {} -v 2 -l {} -f m -j -- -k "MIN_LATENCY,P50_LATENCY,P90_LATENCY,P99_LATENCY,MAX_LATENCY,THROUGHPUT" -m {}'.format(t, dip, duration, send_size)
        output = linux_obj.command(cmd, timeout=duration+30)
        pat = r'MIN_LATENCY=(\d+).*?P50_LATENCY=(\d+).*?P90_LATENCY=(\d+).*?P99_LATENCY=(\d+).*?MAX_LATENCY=(\d+).*?THROUGHPUT=(\d+)'
        match = re.search(pat, output, re.DOTALL)
        if match:
            latency_min = float(match.group(1))
            latency_P50 = float(match.group(2))
            latency_P90 = float(match.group(3))
            latency_P99 = float(match.group(4))
            latency_max = float(match.group(5))
            data_throughput = float(match.group(6))  # TCP/UDP throughput

            throughput = data_throughput / (float(send_size) / frame_size)  # Ethernet throughput in Mbps
            pps = data_throughput * 1000000 /8 / send_size

        result.update(
            {'throughput':  round(throughput, 3),
             'pps': round(pps, 2),
             'latency_min': round(latency_min, 1),
             'latency_avg': round(latency_P50, 1),
             'latency_max': round(latency_max, 1),
             'latency_P99.0': round(latency_P99, 1),
             }
        )

    fun_test.log('\n{}'.format(pprint.pformat(result)))
    return result

