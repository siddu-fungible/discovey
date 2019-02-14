from fun_global import get_current_time
from lib.system.fun_test import fun_test
import pprint
import re


class IPerfManager:
    """The class uses iperf2/iperf3 to measure throughput and use owping to measure latency between host pairs."""

    def __init__(self, linux_objs):
        self.linux_objs = linux_objs

    def setup(self):
        result = True
        for linux_obj in self.linux_objs:

            # Install linuxptp package
            for pkg in ('linuxptp',):
                if not linux_obj.check_package(pkg):
                    result &= linux_obj.install_package(pkg)

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

            # Install iperf/iperf3 and start server mode
            for pkg in ('iperf', 'iperf3'):
                if not linux_obj.check_package(pkg):
                    result &= linux_obj.install_package(pkg)
                if linux_obj.get_process_id_by_pattern(pkg) is None:
                    linux_obj.command('{} -sD'.format(pkg))
                    for ns in linux_obj.get_namespaces():
                        linux_obj.sudo_command('ip netns exec {} {} -sD'.format(ns, pkg))
                    result &= linux_obj.get_process_id_by_pattern(pkg) is not None

            # Install perfsonar-tools for owampd and owping
            for pkg in ('perfsonar-tools',):
                if not linux_obj.check_package(pkg):
                    cmds = (
                        'cd /etc/apt/sources.list.d/',
                        'wget http://downloads.perfsonar.net/debian/perfsonar-release.list',
                        'wget -qO - http://downloads.perfsonar.net/debian/perfsonar-debian-official.gpg.key | apt-key add -',
                    )
                    linux_obj.sudo_command(';'.join(cmds))
                    result &= linux_obj.install_package(pkg)

            # Start owampd server
            if linux_obj.get_process_id_by_pattern('owampd') is None:
                cmd = '/usr/sbin/owampd -c /etc/owamp-server -R /var/run'
                linux_obj.sudo_command(cmd)
                for ns in linux_obj.get_namespaces():
                    linux_obj.sudo_command('ip netns exec {} {}'.format(ns, cmd))
                result &= linux_obj.get_process_id_by_pattern('owampd') is not None

        fun_test.sleep("Waiting for PTP clock sync", seconds=10)

        return result

    def cleanup(self):
        result = True
        for linux_obj in self.linux_objs:
            for process in ('ptp4l', 'phc2sys', 'iperf', 'iperf3', 'owampd'):
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
                hostname = linux_obj.hostname()
                result.update({hostname: {}})
                dip = arg_dict.get('dip')
                tool = arg_dict.get('tool', 'iperf3')
                protocol = arg_dict.get('protocol', 'udp')
                parallel = arg_dict.get('parallel', 1)
                duration = arg_dict.get('duration', 10)
                frame_size = arg_dict.get('frame_size', 1518)
                bw = arg_dict.get('bw', '5m')
                result[hostname] = do_test(linux_obj, dip=dip, tool=tool, protocol=protocol, parallel=parallel,
                                           duration=duration, frame_size=frame_size, bw=bw)
        return result


def do_test(linux_obj, dip, tool='iperf3', protocol='udp', parallel=1, duration=10, frame_size=1518, bw='5m'):
    """Use iperf2/iperf3 to measure TCP/UDP throughput, and use owping by sending UDP packets to measure latency.

    Here are iperf3 and owping output examples.

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
    """

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

    # Throughput Test
    interface = linux_obj.get_interface_to_route(dip)
    mtu = linux_obj.get_mtu(interface)
    if frame_size > mtu + 18:
        fun_test.log('Frame size {} is larger than interface {} mtu {}'.format(frame_size, interface, mtu))
        return None

    result = {}
    throughput = pps = jitter = -1
    bw_unit = bw[-1]
    factor = get_rate_factor(bw_unit)
    bw_val = float(bw.rstrip('kmgKMG')) * factor  # Convert bandwidth to Mbps

    left, right = 0.0, bw_val
    target_bw_val = (left + right) / 2  # Start test from 1/2 of target bindwidth
    while (right - left) >= 0.01:
        target_bw = '{}{}'.format(target_bw_val, bw_unit)

        if protocol.lower() == 'udp':
            payload_size = frame_size-18-20-8
            cmd = '{} -c {} -i 1 -P {} -u -t {} -l {} -b {}'.format(tool, dip, parallel, duration, payload_size, target_bw)
            pat = r'Lost/Total.*?0.00-(\S+)\s+sec.*?(\S+ [K|M|G]bits/sec)\s+(\S+) ([m|u|n]s).*?(\d+)/(\d+).*?sender'
        elif protocol.lower() == 'tcp':
            payload_size = frame_size - 18 - 20 - 20
            cmd = '{} -c {} -i 1 -P {} -t {} -M {} -b {}'.format(tool, dip, parallel, duration, payload_size, target_bw)
            pat = r'0.00-(\S+)\s+sec.*?(\S+) ([K|M|G])bits/sec\s+(\d+)\s+sender'

        output = linux_obj.command(cmd, timeout=duration+30)
        match = re.search(pat, output, re.DOTALL)

        if match:
            if protocol.lower() == 'udp':
                time = float(match.group(1))
                #throughput = format_throughput(match.group(2))  # UDP throughput
                jitter_unit = match.group(4)
                factor = get_time_factor(jitter_unit)
                jitter = float(match.group(3)) * factor
                lost = int(match.group(5))
                total = int(match.group(6))

                packet_count = total - lost
                throughput = float(packet_count) * frame_size * 8 / 1000000 / time  # Ethernet throughput in Mbps
                pps = float(packet_count) / time

            elif protocol.lower() == 'tcp':
                time = float(match.group(1))
                rate_unit = match.group(3)
                factor = get_rate_factor(rate_unit)
                rate = float(match.group(2)) * factor  # TCP throughput
                retry = int(match.group(4))

                throughput = (rate * time - retry * payload_size * 8 / 1000000) / (float(payload_size) / frame_size)
                pps = throughput * 1000000 / (frame_size * 8)

            left = target_bw_val
            target_bw_val = (left + right) / 2

            # If tested throughput is less than targeted bw for more than 0.1Mbps, no need to try further
            if throughput < abs(target_bw_val - 0.1):
                fun_test.sleep("Waiting for buffer drain..", seconds=60)
                break
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
    latency_min = latency_median = latency_max = jitter = latency_percentile = -1

    cmd = 'owping -c {} -s {} -i {} -a {} {}'.format(int(pps*duration), frame_size-18-20-8-14, 1.0/pps, percentile, dip)
    output = linux_obj.command(cmd, timeout=duration+30)
    pat = r'from.*?to.*?{}.*?{} sent, (\d+) lost.*?(\d+) duplicates.*?min/median/max = (\S+)/(\S+)/(\S+) ([mun]s).*?jitter = (\S+) [mun]s.*?Percentiles.*?{}: (\S+) [mun]s.*?no reordering'.format(dip, packet_count, percentile)
    match = re.search(pat, output, re.DOTALL)
    if match:
        lost = int(match.group(1))  # TODO: Add check if needed
        duplicates = int(match.group(2))
        unit = match.group(6)
        factor = get_time_factor(unit)
        latency_min = float(match.group(3)) * factor
        latency_median = float(match.group(4)) * factor
        latency_max = float(match.group(5)) * factor
        jitter = float(match.group(7)) * factor
        latency_percentile = float(match.group(8)) * factor

    result.update(
        {'latency_min': round(latency_min, 1),
         'latency_median': round(latency_median, 1),
         'latency_max': round(latency_max, 1),
         'latency_{}_percentile'.format(percentile): round(latency_percentile, 1),
         }
    )

    if result.get('jitter', 0) == 0:
        result.update(
            {'jitter': round(jitter, 1)}
        )

    result.update(
        {'timestamp': '%s' % get_current_time(),
         'version': fun_test.get_version(),
        }
    )

    fun_test.log('\n{}'.format(pprint.pformat(result)))
    return result

