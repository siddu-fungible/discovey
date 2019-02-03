from lib.system.fun_test import *
from lib.host.linux import Linux
import os
import sys
from time import asctime


class Funeth:
    """Funeth driver class"""

    def __init__(self, tb_config_obj, funos_branch=None, fundrv_branch=None, funsdk_branch=None, ws='/mnt/workspace'):
        self.tb_config_obj = tb_config_obj
        self.linux_obj = Linux(host_ip=tb_config_obj.get_hostname('hu'),
                               ssh_username=tb_config_obj.get_username('hu'),
                               ssh_password=tb_config_obj.get_password('hu'))
        self.funos_branch = funos_branch
        self.fundrv_branch = fundrv_branch
        self.funsdk_branch = funsdk_branch
        self.ws = ws
        self.pf_intf = self.tb_config_obj.get_hu_pf_interface()
        self.vf_intf = self.tb_config_obj.get_hu_vf_interface()

    def lspci(self):
        """Do lspci to check funeth controller."""
        return self.linux_obj.command('lspci -d 1dad:')

    def update_src(self):
        """Update driver source."""

        def update_mirror(ws, repo, **kwargs):
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            _ghbase = 'git@github.com:fungible-inc'
            _cmd = 'git clone --mirror'

            sys.stderr.write('+ [{0}] Update mirror: {1}\n'.format(asctime(), repo))

            if not self.linux_obj.check_file_directory_exists(mirror):
                self.linux_obj.create_directory(mirror, sudo=False)

            if self.linux_obj.check_file_directory_exists(mirror + '/' + repo):
                self.linux_obj.command('cd {}; git remote update'.format(mirror + '/' + repo))
            else:
                self.linux_obj.command('cd {3}; {0} {1}/{2}.git {2}'.format(_cmd, _ghbase, repo, mirror))

        def local_checkout(ws, repo, **kwargs):
            subdir = kwargs.get('subdir', repo)
            branch = kwargs.get('branch', None)
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            self.linux_obj.command('cd {3}; git clone {0}/{1} {2}'.format(mirror, repo, subdir, ws))
            if branch:
                self.linux_obj.command('cd {0}/{1}; git checkout {2}'.format(ws, repo, branch))

        sdkdir = os.path.join(self.ws, 'FunSDK')
        self.linux_obj.command('sudo rm -rf {}'.format(self.ws))
        self.linux_obj.create_directory(self.ws, sudo=False)

        update_mirror(self.ws, 'fungible-host-drivers')
        update_mirror(self.ws, 'FunSDK-small')
        if self.funos_branch:
            update_mirror(self.ws, 'FunOS')

        # clone FunSDK, host-drivers, FunOS
        local_checkout(self.ws, 'fungible-host-drivers', branch=self.fundrv_branch)
        local_checkout(self.ws, 'FunSDK-small', subdir='FunSDK', branch=self.funsdk_branch)
        if self.funos_branch:
            local_checkout(self.ws, 'FunOS', branch=self.funos_branch)

        return self.linux_obj.command('cd {0}; scripts/bob --sdkup -C {1}/FunSDK-cache'.format(sdkdir, self.ws))

    def build(self):
        """Build driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        funsdkdir = os.path.join(self.ws, 'FunSDK')

        if self.funos_branch:
            self.linux_obj.command('cd {}; scripts/bob --build hci'.format(funsdkdir))

        return self.linux_obj.command('cd {}; make clean; make PALLADIUM=yes'.format(drvdir))

    def load(self, sriov=0, cc=False, debug=False):
        """Load driver."""

        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')

        #_ports = range(0, 1)
        _modparams = []

        if debug:
            _modparams.append('dyndbg=+p')

        if sriov > 0:
            _modparams.append('sriov_test=yes')

        self.linux_obj.command('cd {0}; sudo insmod funeth.ko {1}'.format(drvdir, " ".join(_modparams)), timeout=300)

        fun_test.sleep('Sleep for a while to wait for funeth driver loaded', 5)

        if cc:
            self.pf_intf = 'fpg0'

        if sriov > 0:
            sriov_en = '/sys/class/net/{0}/device'.format(self.pf_intf)
            self.linux_obj.command('echo "{0}" | sudo tee {1}/sriov_numvfs'.format(sriov, sriov_en), timeout=300)
            fun_test.sleep('Sleep for a while to wait for sriov enabled', 5)
            self.linux_obj.command('ifconfig -a')

        return self.linux_obj.command('ifconfig %s' % self.pf_intf)

    def configure_intfs(self, nu_or_hu):
        """Configure interface."""

        for ns in self.tb_config_obj.get_namespaces(nu_or_hu):
            for intf in self.tb_config_obj.get_interfaces(nu_or_hu, ns):
                mac_addr = self.tb_config_obj.get_interface_mac_addr(nu_or_hu, intf)
                ipv4_addr = self.tb_config_obj.get_interface_ipv4_addr(nu_or_hu, intf)
                ipv4_netmask = self.tb_config_obj.get_interface_ipv4_netmask(nu_or_hu, intf)
                if ns == 'default':
                    cmds = (
                        'sudo ifconfig {} hw ether {}'.format(intf, mac_addr),
                        'sudo ifconfig {} {} netmask {}'.format(intf, ipv4_addr, ipv4_netmask),
                        'sudo ifconfig {} up'.format(intf),
                    )
                    return_intf = intf
                else:
                    cmds = (
                        'sudo ip netns add {}'.format(ns),
                        'sudo ip link set {} netns {}'.format(intf, ns),
                        'sudo ip netns exec {} ifconfig {} hw ether {}'.format(ns, intf, mac_addr),
                        'sudo ip netns exec {} ifconfig {} {} netmask {}'.format(ns, intf, ipv4_addr, ipv4_netmask),
                        'sudo ip netns exec {} ifconfig {} up'.format(ns, intf),
                    )
                for cmd in cmds:
                    self.linux_obj.command(cmd)

        return self.linux_obj.command('ifconfig %s' % return_intf)

    def loopback_test(self, packet_count=100):
        """Do loopback test between PF and VF via NU."""

        ip_addr = self.tb_config_obj.get_interface_ipv4_addr('hu', self.vf_intf)

        return self.linux_obj.command('sudo ping -c {} -i 0.1 {}'.format(packet_count, ip_addr))

    def configure_ipv4_route(self, nu_or_hu):
        """Configure IP routes to NU."""

        for route in self.tb_config_obj.get_ipv4_routes(nu_or_hu):
            prefix = route['prefix']
            nexthop = route['nexthop']
            cmds = (
                'sudo ip route delete {}'.format(prefix),
                'sudo ip route add {} via {}'.format(prefix, nexthop),
                'sudo arp -s {} {}'.format(nexthop, self.tb_config_obj.get_router_mac()),
            )
            for cmd in cmds:
                self.linux_obj.command(cmd)

        return self.linux_obj.command('ip route')

    def unload(self):
        """Unload driver."""

        self.linux_obj.command('sudo rmmod funeth')

    def ifdown(self, intf):
        """Shut down interface."""

        self.linux_obj.command('sudo ip link set {} down'.format(intf))

    def ifup(self, intf):
        """No shut interface."""

        self.linux_obj.command('sudo ip link set {} up'.format(intf))
