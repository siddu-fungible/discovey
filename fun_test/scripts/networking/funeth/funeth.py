from lib.system.fun_test import *
from lib.host.linux import Linux
from lib.system.utils import MultiProcessingTasks
import re
import os
import sys
from time import asctime


CPU_LIST = range(8, 16)


class Funeth:
    """Funeth driver class"""

    def __init__(self, tb_config_obj, funos_branch=None, fundrv_branch=None, funsdk_branch=None, ws='/mnt/ws'):
        self.tb_config_obj = tb_config_obj
        self.linux_obj_dict = {}
        self.nu_hosts = sorted([host for host in tb_config_obj.configs.keys() if host.startswith('nu')])
        self.hu_hosts = sorted([host for host in tb_config_obj.configs.keys() if host.startswith('hu')])
        for nu_or_hu in self.nu_hosts + self.hu_hosts:
            self.linux_obj_dict.update(
                {nu_or_hu: Linux(host_ip=tb_config_obj.get_hostname(nu_or_hu),
                                 ssh_username=tb_config_obj.get_username(nu_or_hu),
                                 ssh_password=tb_config_obj.get_password(nu_or_hu))
                 }
            )
        self.funos_branch = funos_branch
        self.fundrv_branch = fundrv_branch
        self.funsdk_branch = funsdk_branch
        self.ws = ws
        self.pf_intf = self.tb_config_obj.get_hu_pf_interface()
        self.vf_intf = self.tb_config_obj.get_hu_vf_interface()

    def lspci(self, check_pcie_width=True):
        """Do lspci to check funeth controller."""
        result = True
        for hu in self.hu_hosts:
            output = self.linux_obj_dict[hu].command('lspci -d 1dad:')
            result &= re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output) is not None

            if check_pcie_width:
                output = self.linux_obj_dict[hu].sudo_command('lspci -d 1dad: -vv | grep LnkSta')
                result &= re.findall(r'Width x(\d+)', output) == ['{}'.format(self.tb_config_obj.get_hu_pcie_width(hu))]*4

        return result

    def setup_workspace(self):
        """Set env WORKSPACE, which is used in fungible-host-driver compilation."""
        for hu in self.hu_hosts:
            self.linux_obj_dict[hu].command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % self.ws)

    def cleanup_workspace(self):
        """Restore old WORKSPACE if exists."""
        for hu in self.hu_hosts:
            self.linux_obj_dict[hu].command('export WORKSPACE=$WSTMP')

    def update_src(self, parallel=False):
        """Update driver source."""

        def update_mirror(ws, repo, hu, **kwargs):
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            _ghbase = 'git@github.com:fungible-inc'
            _cmd = 'git clone --mirror'

            sys.stderr.write('+ [{0}] Update mirror: {1}\n'.format(asctime(), repo))

            if not self.linux_obj_dict[hu].check_file_directory_exists(mirror):
                self.linux_obj_dict[hu].create_directory(mirror, sudo=False)

            if self.linux_obj_dict[hu].check_file_directory_exists(mirror + '/' + repo):
                self.linux_obj_dict[hu].command('cd {}; git remote update'.format(mirror + '/' + repo))
            else:
                self.linux_obj_dict[hu].command('cd {3}; {0} {1}/{2}.git {2}'.format(_cmd, _ghbase, repo, mirror))

        def local_checkout(ws, repo, **kwargs):
            subdir = kwargs.get('subdir', repo)
            branch = kwargs.get('branch', None)
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            self.linux_obj_dict[hu].command('cd {3}; git clone {0}/{1} {2}'.format(mirror, repo, subdir, ws))
            if branch:
                self.linux_obj_dict[hu].command('cd {0}/{1}; git checkout {2}'.format(ws, repo, branch))

        def _update_src(linux_obj):
            sdkdir = os.path.join(self.ws, 'FunSDK')
            linux_obj.sudo_command('rm -rf {}'.format(self.ws))
            linux_obj.create_directory(self.ws, sudo=False)

            update_mirror(self.ws, 'fungible-host-drivers', hu)
            update_mirror(self.ws, 'FunSDK-small',hu)
            if self.funos_branch:
                update_mirror(self.ws, 'FunOS', hu)

            # clone FunSDK, host-drivers, FunOS
            local_checkout(self.ws, 'fungible-host-drivers', branch=self.fundrv_branch)
            local_checkout(self.ws, 'FunSDK-small', subdir='FunSDK', branch=self.funsdk_branch)
            if self.funos_branch:
                local_checkout(self.ws, 'FunOS', branch=self.funos_branch)

            output = linux_obj.command(
                'cd {0}; scripts/bob --sdkup -C {1}/FunSDK-cache'.format(sdkdir, self.ws), timeout=300)
            return re.search(r'Updating working projectdb.*Updating current build number', output, re.DOTALL) is not None

        def _update_src2(linux_obj):
            sdkdir = os.path.join(self.ws, 'FunSDK')
            drvdir = os.path.join(self.ws, 'fungible-host-drivers')
            linux_obj.sudo_command('rm -rf {}'.format(self.ws))
            linux_obj.create_directory(self.ws, sudo=False)

            # clone FunSDK, host-drivers, FunOS
            linux_obj.command('cd {}; git clone git@github.com:fungible-inc/fungible-host-drivers.git'.format(self.ws),
                              timeout=300)
            linux_obj.command('cd {}; git clone git@github.com:fungible-inc/FunSDK-small.git FunSDK'.format(self.ws),
                              timeout=300)

            output = linux_obj.command(
                'cd {0}; scripts/bob --sdkup -C {1}/FunSDK-cache'.format(sdkdir, self.ws), timeout=600)
            if re.search(r'Updating working projectdb.*Updating current build number', output, re.DOTALL):

                # Get FunSdK bld
                fun_test.log('Get FunSDK build info')
                output = linux_obj.command('cd {}; cat build_info.txt'.format(sdkdir))
                match = re.search(r'(\d+)', output)
                if match:
                    sdk_bld = match.group(1)
                else:
                    sdk_bld = None

                # Get driver bld
                fun_test.log('Get driver build/commit info')
                output = linux_obj.command('cd {}; git log | head -n 5'.format(drvdir))
                match = re.search(r'commit (\w+).* tag: (bld_\d+)', output)
                if match:
                    drv_commit = match.group(1)
                    drv_bld = match.group(2)
                else:
                    match = re.search(r'commit (\w+).*', output)
                    drv_commit = match.group(1)
                    drv_bld = None

                return sdk_bld, drv_bld, drv_commit

        bld_list = []

        if parallel:
            mp_task_obj = MultiProcessingTasks()
            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                mp_task_obj.add_task(
                    func=_update_src2,
                    func_args=(linux_obj,),
                    task_key='{}'.format(linux_obj.host_ip))

            mp_task_obj.run(max_parallel_processes=len(self.hu_hosts))

            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                bld_list.append(mp_task_obj.get_result('{}'.format(linux_obj.host_ip)))

        else:
            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                bld_list.append(_update_src2(linux_obj))

        if len(set(bld_list)) != 1:
            fun_test.critical('Different FunSDK/Driver bld in hosts')
            return False

        else:
            return bld_list[0]  # sdkdir, drv_bld, drv_commit

    def build(self, parallel=False):
        """Build driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        funsdkdir = os.path.join(self.ws, 'FunSDK')

        def _build(linux_obj):
            if self.funos_branch:
                linux_obj.command('cd {}; scripts/bob --build hci'.format(funsdkdir))

            output = linux_obj.command(
                'export WORKSPACE={}; cd {}; git log | head -n 5; make clean; make PALLADIUM=yes'.format(
                    self.ws, drvdir), timeout=600)
            return re.search(r'fail|error|abort|assert', output, re.IGNORECASE) is None

        result = True

        if parallel:
            mp_task_obj = MultiProcessingTasks()
            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                mp_task_obj.add_task(
                    func=_build,
                    func_args=(linux_obj,),
                    task_key='{}'.format(linux_obj.host_ip))

            mp_task_obj.run(max_parallel_processes=len(self.hu_hosts))

            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                result &= mp_task_obj.get_result('{}'.format(linux_obj.host_ip))

        else:
            for hu in self.hu_hosts:
                linux_obj = self.linux_obj_dict[hu]
                result &= _build(linux_obj)

        return result

    def load(self, sriov=0, cc=False, debug=False):
        """Load driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        _modparams = []

        if debug:
            _modparams.append('dyndbg=+p')

        if sriov > 0:
            _modparams.append('sriov_test=yes')

        result = True
        for hu in self.hu_hosts:
            self.linux_obj_dict[hu].command('cd {0}; sudo insmod funeth.ko {1} num_queues=2'.format(drvdir, " ".join(_modparams)),
                                            timeout=300)

            #fun_test.sleep('Sleep for a while to wait for funeth driver loaded', 5)

            if cc:
                pf_intf = 'fpg0'
            else:
                pf_intf = self.tb_config_obj.get_hu_pf_interface(hu)

            if sriov > 0:
                sriov_en = '/sys/class/net/{0}/device'.format(pf_intf)
                self.linux_obj_dict[hu].command('echo "{0}" | sudo tee {1}/sriov_numvfs'.format(sriov, sriov_en),
                                                timeout=300)
                #fun_test.sleep('Sleep for a while to wait for sriov enabled', 5)
                self.linux_obj_dict[hu].command('ifconfig -a')

            output1 = self.linux_obj_dict[hu].command('lsmod | grep funeth')
            output2 = self.linux_obj_dict[hu].command('ifconfig %s' % pf_intf)
            result &= re.search(r'funeth', output1) is not None and re.search(
                r'Device not found', output2, re.IGNORECASE) is None

        return result

    def configure_namespace_interfaces(self, nu_or_hu, ns):
        """Configure interfaces in a namespace."""
        result = True
        for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
            cmds = []
            mac_addr = self.tb_config_obj.get_interface_mac_addr(nu_or_hu, intf)
            ipv4_addr = self.tb_config_obj.get_interface_ipv4_addr(nu_or_hu, intf)
            ipv4_netmask = self.tb_config_obj.get_interface_ipv4_netmask(nu_or_hu, intf)
            mtu = self.tb_config_obj.get_interface_mtu(nu_or_hu, intf)

            # macvlan interface, e.g. fpg1.1
            if self.tb_config_obj.is_macvlan(nu_or_hu, intf):
                cmds.extend(
                    ['sudo ip link delete {}'.format(intf),
                     'sudo ip link add link {} address {} {} type macvlan'.format(intf.split('.')[0], mac_addr, intf),
                    ]
                )

            # ip alias, e.g. hu3-f0:1, has no mac/mtu config
            if not self.tb_config_obj.is_alias(nu_or_hu, intf):
                cmds.extend(
                    ['ifconfig {} hw ether {}'.format(intf, mac_addr),
                     'ifconfig {} mtu {}'.format(intf, mtu),
                    ]
                )

            cmds.extend(
                ['ifconfig {} {} netmask {}'.format(intf, ipv4_addr, ipv4_netmask),
                 'ifconfig {} up'.format(intf),
                 'ifconfig {}'.format(intf),
                ]
            )
            if ns:
                cmds = ['ip netns add {}'.format(ns), 'ip link set {} netns {}'.format(intf, ns)] + cmds
            for cmd in cmds:
                if ns is None or 'netns' in cmd:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo {}'.format(cmd))
                else:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo ip netns exec {} {}'.format(ns, cmd))
            # Ubuntu 16.04
            if self.tb_config_obj.is_alias(nu_or_hu, intf):
                match = re.search(r'UP.*RUNNING.*inet addr:{}.*Mask:{}'.format(ipv4_addr, ipv4_netmask), output, re.DOTALL)
            else:
                match = re.search(r'UP.*RUNNING.*HWaddr {}.*inet addr:{}.*Mask:{}'.format(mac_addr, ipv4_addr, ipv4_netmask),
                                  output, re.DOTALL)
            if not match:
                # Ubuntu 18.04
                if self.tb_config_obj.is_alias(nu_or_hu, intf):
                    match = re.search(r'UP.*RUNNING.*inet {}\s+netmask {}'.format(ipv4_addr, ipv4_netmask), output, re.DOTALL)
                else:
                    match = re.search(r'UP.*RUNNING.*inet {}\s+netmask {}.*ether {}'.format(ipv4_addr, ipv4_netmask, mac_addr),
                                      output, re.DOTALL)
            result &= match is not None

        return result

    def configure_interfaces(self, nu_or_hu):
        """Configure all the interfaces."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.configure_namespace_interfaces(nu_or_hu, ns)

        return result

    def enable_namespace_interfaces_tso(self, nu_or_hu, ns=None, disable=False):
        """Enable interfaces TSO in a namespace."""
        result = True
        op = 'off' if disable else 'on'
        for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
            cmd = 'ethtool -K {} tso {}'.format(intf, op)
            cmd_chk = 'ethtool -k {}'.format(intf)
            if ns is None or 'netns' in cmd:
                cmds = ['sudo {}; {}'.format(cmd, cmd_chk)]
            else:
                cmds = ['sudo ip netns exec {} {}; sudo ip netns exec {}'.format(ns, cmd, cmd_chk)]
            output = self.linux_obj_dict[nu_or_hu].command(';'.join(cmds))

            match = re.search(r'tcp-segmentation-offload: {}'.format(op), output)
            result &= match is not None

        return result

    def enable_tso(self, nu_or_hu, disable=False):
        """Enable TSO to the interfaces."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.enable_namespace_interfaces_tso(nu_or_hu, ns, disable=disable)

        return result

    def enable_namespace_interfaces_multi_txq(self, nu_or_hu, num_queues=8, ns=None, xps_cpus=True):
        """Enable interfaces multi tx queue in a namespace."""
        result = True
        for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
            cmd = 'ethtool -L {} tx {}'.format(intf, num_queues)
            cmd_chk = 'ethtool -l {}'.format(intf)
            if ns is None or 'netns' in cmd:
                cmds = ['sudo {}; {}'.format(cmd, cmd_chk)]
            else:
                cmds = ['sudo ip netns exec {} {}; sudo ip netns exec {}'.format(ns, cmd, cmd_chk)]
            output = self.linux_obj_dict[nu_or_hu].command(';'.join(cmds))

            match = re.search(r'Current hardware settings:.*RX:\s+\d+.*TX:\s+{}'.format(num_queues), output, re.DOTALL)
            result &= match is not None

            # Configure XPS CPU mapping to have CPU-Txq one to one mapping
            if xps_cpus:
                cmds = []
                for i in range(num_queues):
                    cpu_id = (1 << CPU_LIST[i%len(CPU_LIST)])
                    cmds.append('echo {:04x} > /sys/class/net/{}/queues/tx-{}/xps_cpus'.format(cpu_id, intf, i))
                self.linux_obj_dict[nu_or_hu].sudo_command(';'.join(cmds))
                self.linux_obj_dict[nu_or_hu].command(
                    "for i in {0..%d}; do cat /sys/class/net/%s/queues/tx-$i/xps_cpus; done" % (num_queues-1, intf))

        return result

    def enable_multi_txq(self, nu_or_hu, num_queues=8, xps_cpus=True):
        """Enable multi tx queue to the interfaces."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.enable_namespace_interfaces_multi_txq(nu_or_hu, num_queues, ns, xps_cpus=xps_cpus)

        return result

    def loopback_test(self, packet_count=100, hu='hu'):
        """Do loopback test between PF and VF via NU."""
        ip_addr = self.tb_config_obj.get_interface_ipv4_addr('hu', self.vf_intf)
        return self.linux_obj_dict[hu].ping(ip_addr, count=packet_count, max_percentage_loss=0, interval=0.1, sudo=True)

    def configure_namespace_ipv4_routes(self, nu_or_hu, ns):
        """Configure a namespace's IP routes to NU."""
        result = True
        for route in self.tb_config_obj.get_ipv4_routes(nu_or_hu, ns):
            prefix = route['prefix']
            nexthop = route['nexthop']

            # Route
            cmds = (
                'ip route delete {}'.format(prefix),
                'ip route add {} via {}'.format(prefix, nexthop),
                'ip route',
            )
            for cmd in cmds:
                if ns is None:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo {}'.format(cmd))
                else:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo ip netns exec {} {}'.format(ns, cmd))
            if prefix.endswith('/32'):
                p = prefix.rstrip('/32')
            else:
                p = prefix
            result &= re.search(r'{} via {}'.format(p, nexthop), output) is not None

            # ARP
            router_mac = self.tb_config_obj.get_router_mac()
            cmds = (
                'arp -s {} {}'.format(nexthop, router_mac),
                'arp -na',
            )
            for cmd in cmds:
                if ns is None:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo {}'.format(cmd))
                else:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo ip netns exec {} {}'.format(ns, cmd))
            result &= re.search(r'\({}\) at {} \[ether\] PERM'.format(nexthop, router_mac), output) is not None

        return result

    def configure_ipv4_routes(self, nu_or_hu):
        """Configure IP routes to NU."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.configure_namespace_ipv4_routes(nu_or_hu, ns)

        return result

    def configure_namespace_arps(self, nu_or_hu, ns):
        """Configure a namespace's ARP entries."""
        result = True
        for arp in self.tb_config_obj.get_arps(nu_or_hu, ns):
            ipv4_addr = arp['ipv4_addr']
            mac_addr = arp['mac_addr']

            cmds = (
                'arp -s {} {}'.format(ipv4_addr, mac_addr),
                'arp -na',
            )
            for cmd in cmds:
                if ns is None:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo {}'.format(cmd))
                else:
                    output = self.linux_obj_dict[nu_or_hu].command('sudo ip netns exec {} {}'.format(ns, cmd))
            result &= re.search(r'\({}\) at {} \[ether\] PERM'.format(ipv4_addr, mac_addr), output) is not None

        return result

    def configure_arps(self, nu_or_hu):
        """Configure ARP entries."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.configure_namespace_arps(nu_or_hu, ns)

        return result

    def unload(self):
        """Unload driver."""
        result = True
        for hu in self.hu_hosts:
            linux_obj = self.linux_obj_dict[hu]
            fun_test.log('Unload funeth driver in {}'.format(linux_obj.host_ip))
            linux_obj.command('sudo rmmod funeth')
            output = linux_obj.command('lsmod | grep funeth')
            result &= re.search(r'funeth', output) is None

        return result

    def ifdown(self, intf, hu='hu'):
        """Shut down interface."""
        self.linux_obj_dict[hu].command('sudo ip link set {} down'.format(intf))

    def ifup(self, intf, hu='hu'):
        """No shut interface."""
        self.linux_obj_dict[hu].command('sudo ip link set {} up'.format(intf))

    def get_interrupts(self, nu_or_hu):
        """Get HU host funeth interface interrupts."""
        output_dict = {}
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
                cmd = 'cat /proc/interrupts | grep {}'.format(intf)
                if ns is None or 'netns' in cmd:
                    cmds = ['sudo {}'.format(cmd), ]
                else:
                    cmds = ['sudo ip netns exec {} {}'.format(ns, cmd), ]
                output = self.linux_obj_dict[nu_or_hu].command(';'.join(cmds))
                output_dict.update({intf: output})
        return output_dict

    def get_ethtool_stats(self, nu_or_hu):
        """Get HU host funeth interface ethtool stats."""
        output_dict = {}
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
                cmd = 'ethtool -S {}'.format(intf)
                if ns is None or 'netns' in cmd:
                    cmds = ['sudo {}'.format(cmd), ]
                else:
                    cmds = ['sudo ip netns exec {} {}'.format(ns, cmd), ]
                output = self.linux_obj_dict[nu_or_hu].command(';'.join(cmds))
                output_dict.update({intf: output})
        return output_dict

    def configure_irq_affinity(self, nu_or_hu, tx_or_rx='tx'):
        """Configure irq affinity."""
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
                cmd = 'cat /proc/interrupts | grep {}'.format(intf)
                if ns is None or 'netns' in cmd:
                    cmds = ['sudo {}'.format(cmd), ]
                else:
                    cmds = ['sudo ip netns exec {} {}'.format(ns, cmd), ]
                output = self.linux_obj_dict[nu_or_hu].command(';'.join(cmds))
                irq_list = re.findall(r'(\d+):.*{}-{}'.format(intf, tx_or_rx), output)

                # cat irq affinity
                cmds_cat = []
                for i in irq_list:
                    cmds_cat.append('cat /proc/irq/{}/smp_affinity'.format(i))
                self.linux_obj_dict[nu_or_hu].command(';'.join(cmds_cat))

                # Change irq affinity
                cmds_chg = []
                for irq in irq_list:
                    i = irq_list.index(irq)
                    cpu_id = (1 << CPU_LIST[i % len(CPU_LIST)])
                    cmds_chg.append('echo {:04x} > /proc/irq/{}/smp_affinity'.format(cpu_id, irq))
                self.linux_obj_dict[nu_or_hu].sudo_command(';'.join(cmds_chg))
                self.linux_obj_dict[nu_or_hu].command(';'.join(cmds_cat))

    def collect_syslog(self):
        """Collect all HU hosts' syslog file and copy to job's Log directory."""
        for hu in self.hu_hosts:
            linux_obj = self.linux_obj_dict[hu]
            for log_file in ('syslog',):
                artifact_file_name = fun_test.get_test_case_artifact_file_name(
                    post_fix_name='{}_{}.txt'.format(log_file, linux_obj.host_ip))
                fun_test.scp(source_ip=linux_obj.host_ip,
                             source_file_path="/var/log/{}".format(log_file),
                             source_username=linux_obj.ssh_username,
                             source_password=linux_obj.ssh_password,
                             target_file_path=artifact_file_name)
                fun_test.add_auxillary_file(description="{} Log".format(log_file.split('.')[0]),
                                            filename=artifact_file_name)

    def collect_dmesg(self):
        """Collect all HU hosts' dmesg and copy to job's Log directory."""
        for hu in self.hu_hosts:
            linux_obj = self.linux_obj_dict[hu]
            for log_file in ('dmesg',):
                linux_obj.command('dmesg > /tmp/dmesg')
                artifact_file_name = fun_test.get_test_case_artifact_file_name(
                    post_fix_name='{}_{}.txt'.format(log_file, linux_obj.host_ip))
                fun_test.scp(source_ip=linux_obj.host_ip,
                             source_file_path="/tmp/{}".format(log_file),
                             source_username=linux_obj.ssh_username,
                             source_password=linux_obj.ssh_password,
                             target_file_path=artifact_file_name)
                fun_test.add_auxillary_file(description="{} Log".format(log_file.split('.')[0]),
                                            filename=artifact_file_name)