from lib.host.linux import Linux
import os


class FunControlPlane:
    """FunControlPlane repository."""
    def __init__(self, linux_obj, ws='%s/tmp/' % os.getenv('HOME'), name='FunControlPlane'):
        self.linux_obj = linux_obj
        self.ws = ws
        self.name = name
        self.palladium_test_path = '%s/FunControlPlane/scripts/palladium_test' % self.ws
        self.linux_obj.command('rm -fr {0}; mkdir {0}'.format(self.ws))

    def clone(self, git_base='git@github.com:fungible-inc', repo_name='FunControlPlane'):
        """git clone."""
        return self.linux_obj.command('cd %s; git clone %s/%s.git %s' % (self.ws, git_base, repo_name, self.name),
                                      timeout=120)

    def pull(self, branch='master'):
        """git pull."""
        return self.linux_obj.command('cd %s/%s; git pull; git checkout %s' % (self.ws, self.name, branch), timeout=120)

    def get_prebuilt(self):
        """Get prebuilt FunControlPlane, which has funnel_gen.py, needed to run test."""
        cmds = (
            'cd %s/%s' % (self.ws, self.name),
            'wget http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/functrlp.tgz',
            'tar xzvf functrlp.tgz',
        )
        return self.linux_obj.command(';'.join(cmds), timeout=120)

    def setup_traffic_server(self, server='nu'):
        """Set up PTF traffic server."""
        if server.lower() in ('nu', 'hu', 'sb'):
            return self.linux_obj.command('%s/setup_traffic_server %s' % (self.palladium_test_path, server))
        else:
            return 'error'

    def send_traffic(self, test, server='nu', timeout=60):
        """Run the given test by sending traffic."""
        return self.linux_obj.command('%s/send_traffic %s %s' % (self.palladium_test_path, server, test),
                                      timeout=timeout)

    def cleanup(self):
        """Remove worksapce."""
        return self.linux_obj.command('rm -fr {}'.format(self.ws))
