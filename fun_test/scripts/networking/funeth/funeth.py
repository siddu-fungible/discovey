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

    def update_src(self):
        """Update driver source."""

        def update_mirror(ws, repo, **kwargs):
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            _ghbase = 'git@github.com:fungible-inc'
            _cmd = 'git clone --mirror'

            sys.stderr.write('+ [{0}] Update mirror: {1}\n'.format(asctime(), repo))

            if not os.path.exists(mirror):
                os.makedirs(mirror)

            os.chdir(mirror)
            if os.path.exists(repo):
                os.chdir(repo)
                self.linux_obj.command('git remote update')
            else:
                self.linux_obj.command('{0} {1}/{2}.git {2}'.format(_cmd, _ghbase, repo))
            os.chdir(ws)

        def local_checkout(ws, repo, **kwargs):
            subdir = kwargs.get('subdir', repo)
            branch = kwargs.get('branch', None)
            mirror = kwargs.get('mirror', '/mnt/github-mirror')

            self.linux_obj.command('git clone {0}/{1} {2}'.format(mirror, repo, subdir))
            if branch:
                os.chdir(subdir)
                self.linux_obj.command('git checkout {0}'.format(branch))
            os.chdir(ws)

        sdkdir = os.path.join(self.ws, 'FunSDK')
        self.linux_obj.command('sudo rm -rf {}'.format(self.ws))
        os.makedirs(self.ws)
        os.chdir(self.ws)

        update_mirror(self.ws, 'fungible-host-drivers')
        update_mirror(self.ws, 'FunSDK-small')
        if self.funos_branch:
            update_mirror(self.ws, 'FunOS')

        # clone FunSDK, host-drivers, FunOS
        local_checkout(self.ws, 'fungible-host-drivers', branch=self.fundrv_branch)
        local_checkout(self.ws, 'FunSDK-small', subdir='FunSDK', branch=self.funsdk_branch)
        if self.funos_branch:
            local_checkout(self.ws, 'FunOS', branch=self.funos_branch)

        os.chdir(sdkdir)
        self.linux_obj.command('scripts/bob --sdkup -C {}/FunSDK-cache'.format(self.ws))
        os.chdir(self.ws)

        return True

    def build(self):
        """Build driver."""
        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        funsdkdir = os.path.join(self.ws, 'FunSDK')

        if self.funos_branch:
            os.chdir(funsdkdir)
            self.linux_obj.command('scripts/bob --build hci')

        os.chdir(drvdir)
        self.linux_obj.command('make clean')
        self.linux_obj.command('make PALLADIUM=yes')
        os.chdir(self.ws)

        return True

    def load(self, sriov=0, cc=False, debug=False):
        """Load driver."""

        drvdir = os.path.join(self.ws, 'fungible-host-drivers', 'linux', 'kernel')
        os.chdir(drvdir)

        _ports = range(0, 1)
        _modparams = []

        if debug:
            _modparams.append('dyndbg=+p')

        if sriov > 0:
            _modparams.append('sriov_test=yes')

        self.linux_obj.command('sudo insmod funeth.ko {}'.format(" ".join(_modparams)))

        fun_test.sleep('Sleep for a while to wait for funeth driver loaded', 30)

        if cc:
            self.pf_intf = 'fpg0'
        else:
            self.pf_intf = 'hu3-f0'
        self.vf_intf = 'hu3-f8'

        if sriov > 0:
            sriov_en = '/sys/class/net/{0}/device'.format(self.pf_intf)
            self.linux_obj.command('echo "{0}" | sudo tee {1}/sriov_numvfs'.format(sriov, sriov_en))
            fun_test.sleep('Sleep for a while to wait for sriov enabled', 30)
            self.linux_obj.command('ifconfig -a')
            # vfs start from fnid 8
            _ports.extend(range(8, 8 + sriov))
        
        return True

    def configure_intfs(self):
        """Configure interface."""

        # TODO: Pass IP/MAC/arp/route/etc. as args

        # Configure PF interface IP/MAC/arp/route
        self.linux_obj.command('sudo ifconfig {} hw ether 00:de:ad:be:ef:11'.format(self.pf_intf))
        self.linux_obj.command('sudo ifconfig {} 53.1.1.5 netmask 255.255.255.0'.format(self.pf_intf))
        self.linux_obj.command('sudo arp -s 53.1.1.1 00:de:ad:be:ef:00')
        self.linux_obj.command('sudo ip route add 53.1.9.0/24 via 53.1.1.1')

        # Configure VF interface hu3-f8 namespace/IP/MAC/arp/route
        self.linux_obj.command('sudo ip netns add n8')
        self.linux_obj.command('sudo ip link set {} netns n8'.format(self.vf_intf))
        self.linux_obj.command('sudo ip netns exec n8 ifconfig {} hw ether 00:de:ad:be:ef:51'.format(self.vf_intf))
        self.linux_obj.command('sudo ip netns exec n8 ifconfig {} 53.1.9.5/24 up'.format(self.vf_intf))
        self.linux_obj.command('sudo ip netns exec n8 arp -s 53.1.9.1 00:de:ad:be:ef:00')
        self.linux_obj.command('sudo ip netns exec n8 ip route add 53.1.1.0/24 via 53.1.9.1')

        packet_count = 100
        self.linux_obj.command('sudo ping -c {} -i 0.1 53.1.9.5'.format(packet_count))

        os.chdir(self.ws)
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
