from lib.system.fun_test import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs


def setup_hu_host(funeth_obj):
    linux_obj = funeth_obj.linux_obj_dict['hu']
    linux_obj.command('hostname')

    # Install packages
    for pkg in ('make', 'python', 'python-pip', 'libelf-dev',):  # TODO: add iperf3 3.6
        result = linux_obj.install_package(pkg)
        fun_test.test_assert(result, 'Install package {}'.format(pkg))

    for python_pkg in ('pyyaml', 'jinja2'):
        linux_obj.sudo_command('pip install {}'.format(python_pkg))

    # Set up workspace
    linux_obj.sudo_command('chmod -R 777 /mnt')
    for f, d in zip(('71-fundev-net.rules', 'ws.tar.gz', 'compliance_test.sh'), ('/etc/udev/rules.d/', '/mnt/', '/home/fun')):
        if f == '71-fundev-net.rules':
            sudo = True
        else:
            sudo = False
        result = linux_obj.scp(source_ip='qa-ubuntu-02',
                               source_username='auto_admin',
                               source_password='fun123',
                               source_file_path='/project/users/gliang/shared/system_test/{}'.format(f),
                               target_file_path=d,
                               timeout=60,
                               sudo=sudo),
        fun_test.test_assert(result, 'scp file {} to {}'.format(f, d))
    linux_obj.sudo_command('cd /mnt; rm -fr ws; tar xzvf ws.tar.gz', timeout=180)


    # Build driver, copy driver out and remove workspace!!
    funeth_obj.setup_workspace()
    fun_test.test_assert(funeth_obj.build(), 'Build funeth driver.')
    fun_test.test_assert(funeth_obj.copy_driver(to_path='/mnt'), 'Copy driver.')
    linux_obj.sudo_command('rm -fr /mnt/ws.tar.gz', timeout=180)
    fun_test.test_assert(not linux_obj.check_file_directory_exists('/mnt/ws.tar.gz'), 'Removed ws.tar.gz.')
    linux_obj.sudo_command('rm -fr /mnt/ws', timeout=180)
    fun_test.test_assert(not linux_obj.check_file_directory_exists('/mnt/ws'), 'Removed workspace.')

    #fun_test.test_assert(funeth_obj.load(sriov=4), 'Load funeth driver.')
    #fun_test.test_assert(funeth_obj.configure_interfaces('hu'), 'Configure funeth interfaces.')
    #fun_test.test_assert(funeth_obj.configure_ipv4_routes('hu'), 'Configure IPv4 routes.')


class SnakeTest(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Snake test
        """)

    def setup(self):

        tb_config_obj = tb_configs.TBConfigs('snake')
        tb_config_obj.configs['hu']['hostname'] = target_ip
        tb_config_obj.configs['hu']['username'] = username
        tb_config_obj.configs['hu']['password'] = password
        funeth_obj = Funeth(tb_config_obj, ws='/mnt/ws')
        fun_test.shared_variables['funeth_obj'] = funeth_obj

        # HU host
        setup_hu_host(funeth_obj)

    def cleanup(self):
        # TODO: Uncomment below to clean up workspace after test
        #fun_test.shared_variables['funeth_obj'].cleanup_workspace()
        pass


def verify_snake_datapath(funeth_obj, packet_count=1000, packet_size=114):
    linux_obj = funeth_obj.linux_obj_dict['hu']

    for f1, dip in zip(('F1_0', 'F1_1'), ('9.1.2.1', '9.2.2.1')):
        result = linux_obj.ping(dip, count=packet_count, max_percentage_loss=0, interval=0.01,
                                size=packet_size-20-8,  # IP header 20B, ICMP header 8B
                                sudo=True)
        fun_test.test_assert(
            result,
            '{}: Snake ping {} packets and packet size {}B'.format(f1, packet_count, packet_size))


class SnakePing(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Snake test ping",
                              steps="""
        1. Snake test ping
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        #verify_snake_datapath(funeth_obj=fun_test.shared_variables['funeth_obj'])
        pass


if __name__ == "__main__":
    try:
        inputs = fun_test.inputs
        input_dict = {}
        for i in inputs.split(','):
            input_dict.update({i.split('=')[0]: i.split('=')[1]})
        target_ip = input_dict['COMe_ip']
        username = input_dict.get('username', 'fun')
        password = input_dict.get('password', '123')
    except:
        fun_test.test_assert(False, 'Provide COMe ip address to ssh, e.g. --inputs "COMe_ip=192.168.0.1"')

    ts = SnakeTest()
    for tc in (
            SnakePing,
    ):
        ts.add_test_case(tc())
    ts.run()
