from lib.system.fun_test import *
import os
import sys
from time import asctime


class Funeth:
    """Funeth driver class"""

    def __init__(self, linux_obj, funos_branch=None, fundrv_branch=None, funsdk_branch=None, ws='/mnt/workspace'):
        self.linux_obj = linux_obj
        self.funos_branch = funos_branch
        self.fundrv_branch = fundrv_branch
        self.funsdk_branch = funsdk_branch
        self.ws = ws
        self.pf_intf = None
        self.vf_intf = None

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
                self.linux_obj.command('cd {1}; git checkout {0}'.format(branch, ws))

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

        self.linux_obj.command('cd {0}; scripts/bob --sdkup -C {1}/FunSDK-cache'.format(sdkdir, self.ws))

        return True

    def build(self):
        """Build driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        funsdkdir = os.path.join(self.ws, 'FunSDK')

        if self.funos_branch:
            self.linux_obj.command('cd {}; scripts/bob --build hci'.format(funsdkdir))

        self.linux_obj.command('cd {}; make clean; make PALLADIUM=yes'.format(drvdir))

        return True

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

        fun_test.sleep('Sleep for a while to wait for funeth driver loaded', 10)

        if cc:
            self.pf_intf = 'fpg0'
        else:
            self.pf_intf = 'hu3-f0'
        self.vf_intf = 'hu3-f8'

        if sriov > 0:
            sriov_en = '/sys/class/net/{0}/device'.format(self.pf_intf)
            self.linux_obj.command('echo "{0}" | sudo tee {1}/sriov_numvfs'.format(sriov, sriov_en), timeout=300)
            fun_test.sleep('Sleep for a while to wait for sriov enabled', 10)
            self.linux_obj.command('ifconfig -a')
            # vfs start from fnid 8
            #_ports.extend(range(8, 8 + sriov))

        return True

    def configure_intfs(self):
        """Configure interface."""

        # Configure PF interface IP/MAC/arp/route
        # TODO: Pass IP/MAC/arp/route/etc. as args
        cmds = (
            'sudo ifconfig {} hw ether 00:de:ad:be:ef:11'.format(self.pf_intf),
            'sudo ifconfig {} 53.1.1.5 netmask 255.255.255.0'.format(self.pf_intf),
            'sudo arp -s 53.1.1.1 00:de:ad:be:ef:00',
            'sudo ip route add 53.1.9.0/24 via 53.1.1.1',
        )
        for cmd in cmds:
            self.linux_obj.command(cmd)

        # Configure VF interface hu3-f8 namespace/IP/MAC/arp/route
        cmds = (
            'sudo ip netns add n8',
            'sudo ip link set {} netns n8'.format(self.vf_intf),
            'sudo ip netns exec n8 ifconfig {} hw ether 00:de:ad:be:ef:51'.format(self.vf_intf),
            'sudo ip netns exec n8 ifconfig {} 53.1.9.5/24 up'.format(self.vf_intf),
            'sudo ip netns exec n8 arp -s 53.1.9.1 00:de:ad:be:ef:00',
            'sudo ip netns exec n8 ip route add 53.1.1.0/24 via 53.1.9.1',
        )
        for cmd in cmds:
            self.linux_obj.command(cmd)

        return True

    def loopback_test(self, ip_addr='53.1.9.5', packet_count=100):
        """Do loopback test between PF and VF via NU."""

        return self.linux_obj.command('sudo ping -c {} -i 0.1 {}'.format(packet_count, ip_addr))

    def configure_ip_route(self, ip_prefix='19.1.1.0/24', next_hop='53.1.1.1'):
        """Configure IP routes to NU."""

        self.linux_obj.command('sudo ip route add {} via {}'.format(ip_prefix, next_hop))

        return True

    def unload(self):
        """Unload driver."""
        self.linux_obj.command('sudo rmmod funeth')

    def ifdown(self, intf):
        """Shut down interface."""
        self.linux_obj.command('sudo ip link set {} down'.format(intf))

    def ifup(self, intf):
        """No shut interface."""
        self.linux_obj.command('sudo ip link set {} up'.format(intf))
