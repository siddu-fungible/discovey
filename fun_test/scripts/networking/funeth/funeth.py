from lib.system.fun_test import *
from lib.host.linux import Linux
import re
import os
import sys
from time import asctime


class Funeth:
    """Funeth driver class"""

    def __init__(self, tb_config_obj, funos_branch=None, fundrv_branch=None, funsdk_branch=None, ws='/mnt/ws'):
        self.tb_config_obj = tb_config_obj
        self.linux_obj_dict = {}
        for nu_or_hu in ('nu', 'hu'):
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

    def lspci(self):
        """Do lspci to check funeth controller."""
        output = self.linux_obj_dict['hu'].command('lspci -d 1dad:')
        return re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output) is not None

    def setup_workspace(self):
        """Set env WORKSPACE, which is used in fungible-host-driver compilation."""
        self.linux_obj_dict['hu'].command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % self.ws)

    def cleanup_workspace(self):
        """Restore old WORKSPACE if exists."""
        self.linux_obj_dict['hu'].command('export WORKSPACE=$WSTMP')

    def update_src(self):
        """Update driver source."""

        def update_mirror(ws, repo, **kwargs):
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            _ghbase = 'git@github.com:fungible-inc'
            _cmd = 'git clone --mirror'

            sys.stderr.write('+ [{0}] Update mirror: {1}\n'.format(asctime(), repo))

            if not self.linux_obj_dict['hu'].check_file_directory_exists(mirror):
                self.linux_obj_dict['hu'].create_directory(mirror, sudo=False)

            if self.linux_obj_dict['hu'].check_file_directory_exists(mirror + '/' + repo):
                self.linux_obj_dict['hu'].command('cd {}; git remote update'.format(mirror + '/' + repo))
            else:
                self.linux_obj_dict['hu'].command('cd {3}; {0} {1}/{2}.git {2}'.format(_cmd, _ghbase, repo, mirror))

        def local_checkout(ws, repo, **kwargs):
            subdir = kwargs.get('subdir', repo)
            branch = kwargs.get('branch', None)
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            self.linux_obj_dict['hu'].command('cd {3}; git clone {0}/{1} {2}'.format(mirror, repo, subdir, ws))
            if branch:
                self.linux_obj_dict['hu'].command('cd {0}/{1}; git checkout {2}'.format(ws, repo, branch))

        sdkdir = os.path.join(self.ws, 'FunSDK')
        self.linux_obj_dict['hu'].command('sudo rm -rf {}'.format(self.ws))
        self.linux_obj_dict['hu'].create_directory(self.ws, sudo=False)

        update_mirror(self.ws, 'fungible-host-drivers')
        update_mirror(self.ws, 'FunSDK-small')
        if self.funos_branch:
            update_mirror(self.ws, 'FunOS')

        # clone FunSDK, host-drivers, FunOS
        local_checkout(self.ws, 'fungible-host-drivers', branch=self.fundrv_branch)
        local_checkout(self.ws, 'FunSDK-small', subdir='FunSDK', branch=self.funsdk_branch)
        if self.funos_branch:
            local_checkout(self.ws, 'FunOS', branch=self.funos_branch)

        output = self.linux_obj_dict['hu'].command(
            'cd {0}; scripts/bob --sdkup -C {1}/FunSDK-cache'.format(sdkdir, self.ws), timeout=300)
        return re.search(r'Updating working projectdb.*Updating current build number', output, re.DOTALL) is not None

    def build(self):
        """Build driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        funsdkdir = os.path.join(self.ws, 'FunSDK')

        if self.funos_branch:
            self.linux_obj_dict['hu'].command('cd {}; scripts/bob --build hci'.format(funsdkdir))

        output = self.linux_obj_dict['hu'].command('cd {}; make clean; make PALLADIUM=yes'.format(drvdir), timeout=600)
        return re.search(r'fail|error|abort|assert', output, re.IGNORECASE) is None

    def load(self, sriov=0, cc=False, debug=False):
        """Load driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        _modparams = []

        if debug:
            _modparams.append('dyndbg=+p')

        if sriov > 0:
            _modparams.append('sriov_test=yes')

        self.linux_obj_dict['hu'].command('cd {0}; sudo insmod funeth.ko {1}'.format(drvdir, " ".join(_modparams)),
                                          timeout=300)

        fun_test.sleep('Sleep for a while to wait for funeth driver loaded', 5)

        if cc:
            self.pf_intf = 'fpg0'

        if sriov > 0:
            sriov_en = '/sys/class/net/{0}/device'.format(self.pf_intf)
            self.linux_obj_dict['hu'].command('echo "{0}" | sudo tee {1}/sriov_numvfs'.format(sriov, sriov_en),
                                              timeout=300)
            fun_test.sleep('Sleep for a while to wait for sriov enabled', 5)
            self.linux_obj_dict['hu'].command('ifconfig -a')

        output1 = self.linux_obj_dict['hu'].command('lsmod')
        output2 = self.linux_obj_dict['hu'].command('ifconfig %s' % self.pf_intf)
        return re.search(r'funeth', output1) is not None and re.search(
            r'Device not found', output2, re.IGNORECASE) is None

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
                match = re.search(r'inet addr:{}.*Mask:{}'.format(ipv4_addr, ipv4_netmask), output, re.DOTALL)
            else:
                match = re.search(r'HWaddr {}.*inet addr:{}.*Mask:{}'.format(mac_addr, ipv4_addr, ipv4_netmask),
                                  output, re.DOTALL)
            if not match:
                # Ubuntu 18.04
                if self.tb_config_obj.is_alias(nu_or_hu, intf):
                    match = re.search(r'inet {}\s+netmask {}'.format(ipv4_addr, ipv4_netmask), output, re.DOTALL)
                else:
                    match = re.search(r'inet {}\s+netmask {}.*ether {}'.format(ipv4_addr, ipv4_netmask, mac_addr),
                                      output, re.DOTALL)
            result &= match is not None

        return result

    def configure_interfaces(self, nu_or_hu):
        """Configure all the interfaces."""
        result = True
        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            result &= self.configure_namespace_interfaces(nu_or_hu, ns)

        return result

    def loopback_test(self, packet_count=100):
        """Do loopback test between PF and VF via NU."""
        ip_addr = self.tb_config_obj.get_interface_ipv4_addr('hu', self.vf_intf)
        #output = self.linux_obj_dict['hu'].command('sudo ping -c {} -i 0.01 {}'.format(packet_count, ip_addr))
        #return re.search(r'{0} packets transmitted, {0} received, 0% packet loss'.format(packet_count),
        #                 output) is not None
        return self.linux_obj_dict['hu'].ping(ip_addr, count=packet_count, max_percentage_loss=0, interval=0.1,
                                              sudo=True)

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
            result &= re.search(r'{} via {}'.format(prefix, nexthop), output) is not None

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

    def unload(self):
        """Unload driver."""
        self.linux_obj_dict['hu'].command('sudo rmmod funeth; lsmod')
        output = self.linux_obj_dict['hu'].command('lsmod')
        return re.search(r'funeth', output) is None

    def ifdown(self, intf):
        """Shut down interface."""
        self.linux_obj_dict['hu'].command('sudo ip link set {} down'.format(intf))

    def ifup(self, intf):
        """No shut interface."""
        self.linux_obj_dict['hu'].command('sudo ip link set {} up'.format(intf))
