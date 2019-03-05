import os
import re


class FunControlPlane:
    """FunControlPlane repository."""
    def __init__(self, linux_obj, ws='%s/tmp/' % os.getenv('HOME'), name='FunControlPlane'):
        self.linux_obj = linux_obj
        self.ws = ws
        self.name = name
        self.palladium_test_path = '%s/FunControlPlane/scripts/palladium_test' % self.ws
        self.linux_obj.command('rm -fr {0}/{1}; mkdir -p {0}/{1}'.format(self.ws, self.name))

    def clone(self, git_base='git@github.com:fungible-inc', repo_name='FunControlPlane'):
        """git clone."""
        output = self.linux_obj.command('cd %s; git clone %s/%s.git %s' % (self.ws, git_base, repo_name, self.name),
                                        timeout=300)
        done_list = re.findall(r'done', output)
        return done_list == ['done'] * 5 or done_list == ['done'] * 6

    def pull(self, branch='master'):
        """git pull."""
        output = self.linux_obj.command('cd %s/%s; git pull; git checkout %s' % (self.ws, self.name, branch),
                                        timeout=300)
        return re.search(r'Already up[-| ]to[-| ]date.', output) is not None

    def get_prebuilt(self):
        """Get prebuilt FunControlPlane, which has funnel_gen.py, needed to run test."""
        # TODO: Add platform check to use correct prebuilt functrlp file - functrlp_mips.tgz, or functrlp_palladium.tgz
        filename = 'functrlp_palladium.tgz'
        cmds = (
            'cd %s/%s' % (self.ws, self.name),
            'wget http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/%s' % filename,
            'tar xzvf %s' % filename,
        )
        output = self.linux_obj.command(';'.join(cmds), timeout=300)
        return re.search(r'funnel_gen.py', output, re.DOTALL) is not None

    def make_gen_files(self):
        cmds = (
            'cd %s/%s/networking/tools/dpcsh' % (self.ws, self.name),
            'python setup.py install',
            'cd ../nmtf',
            'sudo python setup.py install',
        )
        output = self.linux_obj.sudo_command(';'.join(cmds), timeout=120)
        return output

    def setup_traffic_server(self, server='nu'):
        """Set up PTF traffic server."""
        if server.lower() in ('nu', 'hu', 'sb'):
            return self.linux_obj.command('%s/setup_traffic_server %s' % (self.palladium_test_path, server), timeout=300)
        else:
            return 'error'

    def send_traffic(self, test, server, dpc_proxy_ip, dpc_proxy_port, timeout=60):
        """Run the given test by sending traffic."""
        return self.linux_obj.command('%s/send_traffic %s -dpc_proxy_ip %s -dpc_proxy_port %s %s' % (
            self.palladium_test_path, server, dpc_proxy_ip, dpc_proxy_port, test), timeout=timeout)

    def cleanup(self):
        """Remove worksapce."""
        return self.linux_obj.command('rm -fr {}/{}'.format(self.ws, self.name))


class FunSDK:
    """FunSDK repository."""
    def __init__(self, linux_obj, ws='%s/tmp/' % os.getenv('HOME'), name='FunSDK'):
        self.linux_obj = linux_obj
        self.ws = ws
        self.name = name
        self.linux_obj.command('rm -fr {0}/{1}; mkdir -p {0}/{1}'.format(self.ws, self.name))

    def clone(self, git_base='git@github.com:fungible-inc', repo_name='FunSDK-small'):
        """git clone."""
        output = self.linux_obj.command('cd %s; git clone %s/%s.git %s' % (self.ws, git_base, repo_name, self.name),
                                        timeout=300)
        done_list = re.findall(r'done', output)
        return done_list == ['done'] * 5 or done_list == ['done'] * 6

    def sdkup(self):
        """Update SDK."""
        output = self.linux_obj.command('cd %s/%s; ./scripts/bob --sdkup' % (self.ws, self.name), timeout=300)
        return re.search(r'Updating current build number', output) is not None
