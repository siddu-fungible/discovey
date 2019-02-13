from lib.host.linux import Linux
from lib.system.fun_test import fun_test
import re


class PerfManager:
    """The class uses iperf2/iperf3 to measure throughput and use owping to measure latency between host pairs."""

    def __init__(self, hosts):
        self.packet_count = 10
        self.linux_obj_dict = {}
        for host in hosts:
            self.linux_obj_dict.update(
                {host: Linux(host)}
            )

    def setup(self):
        result = True
        for linux_obj in self.linux_obj_dict.values():

            # Install linuxptp package
            for pkg in ('linuxptp',):
                if not linux_obj.check_package(pkg):
                    result &= linux_obj.install_package(pkg)

            # Start ptp4l for PTP clock, and phy2c for sync system clock to PTP clock
            if not linux_obj.get_process_id_by_pattern('ptp4l') or linux_obj.get_process_id_by_pattern('phc2sys'):
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
                if not linux_obj.get_process_id_by_pattern(pkg):
                    linux_obj.command('{} -sD'.format(pkg))
                    result &= linux_obj.get_process_id_by_pattern(pkg) is not None

            # Install owampd and owping
            if not linux_obj.command_exists('owampd') or not linux_obj.command_exists('owping'):
                cmds = (
                    'wget http://software.internet2.edu/sources/owamp/owamp-3.4-6.tar.gz',
                    'wget http://software.internet2.edu/sources/owamp/owamp-3.4-10.tar.gz',
                    'tar xzf owamp-3.4-6.tar.gz',
                    'mv owamp-3.4 owamp-3.4-6',
                    'tar xzf owamp-3.4-10.tar.gz',
                    'cd owamp-3.4',
                    'cp -r ../owamp-3.4-6/I2util .',  # 3.4-10 doesn't have I2util included
                    './configure',
                    'make',
                    'sudo make install',
                )
                for cmd in cmds:
                    linux_obj.command(cmd)
                result &= linux_obj.command_exists('owampd') & linux_obj.command_exists('owping')

            # Start owampd server
            if not linux_obj.get_process_id_by_pattern('owampd'):
                config_path = 'owamp-3.4/conf'
                cmds = (
                    'owampd -c {}'.format(config_path),
                )
                for cmd in cmds:
                    linux_obj.command(cmd)
                result &= linux_obj.get_process_id_by_pattern('owampd') is not None

        return result

    def cleanup(self):
        result = True
        for linux_obj in self.linux_obj_dict.values():
            for process in ('ptp4l', 'phc2sys', 'iperf', 'iperf3', 'owampd'):
                linux_obj.kill_process(linux_obj.get_process_id_by_pattern(process))
                result &= linux_obj.get_process_id_by_pattern(process) is None

        return result

    def do_throughput_test(self, linux_obj, dip, tool='iperf3', protocol='udp', parallel=1, duration=10,
                           frame_size=1518, bw='5m'):
        """iperf3 output example.

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
        """
        interface = linux_obj.get_interface_to_route(dip)
        mtu = linux_obj.get_mtu(interface)
        if frame_size > mtu + 18:
            fun_test.log('Frame size {} is larger than interface {} mtu {}'.format(frame_size, interface, mtu))
            return None

        result = None
        if protocol.lower() == 'udp':
            bw_unit = bw[:-1]
            if bw_unit.lower() == 'k':
                factor = float(1/1000)
            elif bw_unit.lower() == 'm':
                factor = 1.0
            elif bw_unit.lower() == 'g':
                factor = 1000.0
            bw_val = float(bw.rstrip('kmgKMG')) * factor  # Convert bandwidth to Mbps

            left, right = 0.0, bw_val
            target_bw_val = (left + right) / 2  # Start test from 1/2 of target bindwidth
            while (right - left) >= 0.01:
                target_bw = '{}{}'.format(target_bw_val, bw_unit)
                cmd = '{} -c {} -i 1 -P {} -u -t {} -l {} -b {}'.format(
                    tool, dip, parallel, duration, frame_size-18-20-8, target_bw)
                pat = re.compile(
                    r'Interval.*Bandwidth\s+Jitter\s+Lost/Total.*-(\S+)\s+sec.*(\S+ [K|M|G]bits/sec)\s+(\S+ [m|u|n]s).*(\d+)/(\d+)',
                    re.DOTALL)
                output = linux_obj.command(cmd, timeout=duration+30)
                match = re.match(pat, output)
                if match:
                    time = float(match.group(1))
                    #throughput = format_throughput(match.group(2))  # UDP throughput
                    jitter = format_latency(match.group(3))  # TODO: See if it's needed
                    lost = int(match.group(4))
                    total = int(match.group(5))

                    self.packet_count = total - lost
                    result = float(self.packet_count) * frame_size * 8 / 1000000 / time  # Ethernet throughput in Mbps
                    left = target_bw_val
                    target_bw_val = (left + right) / 2
                else:
                    right = target_bw_val
                    target_bw_val = (left + right) / 2
                fun_test.sleep("Waiting for buffer drain", seconds=60)

            return result

        elif protocol.lower() == 'tcp':  # TODO: frame_size is ignored?
            # Turn off offload
            linux_obj.sudo_command(
                'ethtool --offload {} rx off tx off sg off tso off gso off gro off'.format(interface))

            payload_size = frame_size-18-20-20
            cmd = '{} -c {} -i 1 -P {} -t {} -M {}'.format(tool, dip, parallel, duration, payload_size)
            pat = re.compile(r'Interval.*Bandwidth\s+Retr.*-(\S+)\s+sec.*(\S+ [K|M|G]bits/sec)\s+(\d+)\s+sender',
                             re.DOTALL)
            output = linux_obj.command(cmd, timeout=duration + 30)
            match = re.match(pat, output)
            if match:
                time = float(match.group(1))
                throughput_str = match.group(2)
                if throughput_str.endswith('Kbits/sec'):
                    factor = 1.0 / 1000
                elif throughput_str.endswith('Mbits/sec'):
                    factor = 1.0
                elif throughput_str.endswith('Gbits/sec'):
                    factor = 1.0 * 1000
                throughput = float(throughput_str.rstrip('KMGbps').strip()) * factor
                retry = int(match.group(3))

                result = (throughput * time - retry * payload_size * 8 / 1000000) / (float(payload_size) / frame_size)
                return result

        else:
            fun_test.log('Protocol {} is not supported.'.format(protocol))
            return None

    def do_latency_test(self, tool='owping', protocol='udp', parallel=1, duration=10, frame_size=1518, packet_count=10):

        def format_latency(s):
            """Return latency in us"""
            if s.endswith('ns'):
                factor = 1.0 / 1000
            elif s.endswith('us'):
                factor = 1.0
            elif s.endswith('ms'):
                factor = 1.0 * 1000
            return float(s.rstrip('nums').strip()) * factor

        pass


