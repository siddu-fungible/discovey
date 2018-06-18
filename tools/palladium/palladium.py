#! /usr/bin/python

from lib.system.fun_test import *
from lib.host.network_controller import NetworkController
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD, FUN_TEST_DIR
import re, os, json
from os.path import expanduser

class DpcshProxy(object):

    def __init__(self, ip='server120', port=40221, usb='ttyUSB6', dpc_bin_path='image',
                 user=REGRESSION_USER, password=REGRESSION_USER_PASSWORD):

        self.ip = ip
        self.port = port
        self.usb = usb
        self.dpc_bin_path = dpc_bin_path
        self.linux = Linux(host_ip=ip,
                      ssh_username=user,
                      ssh_password=password)

    def start(self):
        result = False
        env_cmd = 'setenv LD_LIBRARY_PATH "/project/tools/glibc-2.14/lib"'
        run_cmd = 'nohup ./dpcsh  -D /dev/{} --tcp_proxy {} &'.format(self.usb, self.port)
        try:
            self.linux.command(env_cmd)
            self.pid = self.linux.command(run_cmd).strip().split(' ')[-1]
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def stop(self):
        result = False
        cmd = 'pkill dpcsh'
        try:
            self.linux.command(cmd)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


class Palladium(object):

    BOARDS = {
        'Networking1': 4,
        'Networking2': 6,
    }

    TPODS = ['T4', 'T10', 'T11']

    def __init__(self, ip='server101', image_dir='/image', rdp_dir='/rdp',
                 odp_dir='/odp', model='Networking1', design='rel_052518_svn61241',
                 user=REGRESSION_USER, password=REGRESSION_USER_PASSWORD):

        self.ip = ip
        self.image_dir = expanduser("~")+image_dir
        self.rdp_dir = expanduser("~")+rdp_dir
        self.odp_dir = expanduser("~")+odp_dir
        self.model = model
        self.design = design
        self.reservation_key = ''
        self.linux = Linux(host_ip=ip,
                      ssh_username=user,
                      ssh_password=password)

    def _is_available(self):
        result = False
        boards_available = False
        tpods_available = False

        self.server_info = {'free_boards': 0,
                            'free_tpods': False,
                            'reservation_key': ""
                            }
        cmd = 'test_server -json'
        try:
            output = self.linux.command(cmd, timeout=120)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            cluster_info = json.loads(output)
        except ValueError:
            fun_test.critical('JSON decode Failed')

        cluster_3 = cluster_info['Clusters'][2]
        cluster_4 = cluster_info['Clusters'][3]
        rack_1_tpods = cluster_info['AvailableTpods'][1]["Targets"]

        for cluster in [cluster_3, cluster_4]:
            for slot in cluster['LogicDrawer']:
                if slot['Domains'][0]['Owner'] == 'NONE':
                    self.server_info['free_boards'] += 1

        if self.server_info['free_boards'] >= self.BOARDS[self.model]:
            boards_available = True

        if set(self.TPODS).issubset(set(rack_1_tpods)):
            tpods_available = True

        return result and boards_available and tpods_available

    def boot(self):
        result = False

        cmd = 'nohup runZ1 -d {} -rdp {} -odp {} -m {} -rev {} -ue &'.format\
            (self.image_dir, self.rdp_dir, self.odp_dir, self.model, self.design)
        try:
            self.pid = self.linux.command(cmd).strip().split(' ')[-1]
        except Exception as ex:
            fun_test.critical(str(ex))

        timer = FunTimer(max_time=3600)
        while not timer.is_expired():
            self.reservation_key = self._get_reservation_key()
            if self.reservation_key:
                break
            else:
                fun_test.sleep("Waiting for Boards to be free...sleeping 60 secs", seconds=60)

        if self.reservation_key:
            fun_test.log("Successfully reserved Boards. Booting FunOS....")
            if self._is_booted():
                fun_test.log("Successfully booted Palladium with FunOS")
                result = True
            else:
                self._release_reservation()
                result = False
                fun_test.critical("Failed to boot Palladium with FunOS...Exiting")
        else:
            result = False
            fun_test.critical("Failed to reserve Palladium boards/tpod...Exiting")

        return result

    def _is_booted(self):
        timer = FunTimer(max_time=600)
        design_loaded = False
        search_str = 'source init.qel'
        cmd = "grep --text '{}' {}/{}/emu.log".format(search_str, self.rdp_dir, self.model, include_last_line=True)
        while not timer.is_expired():
            output = self.linux.command(cmd)
            if re.search('XErun', output):
                design_loaded = True
                break
            fun_test.sleep("Waiting for design to load...sleeping 30 secs", seconds=30)
        return design_loaded

    def _get_reservation_key(self):

        cmd = 'test_server -json'
        try:
            output = self.linux.command(cmd, timeout=120)
        except Exception as ex:
            fun_test.critical(str(ex))

        for i,v in enumerate(output.split('\n')):
            if v.strip() == '{':
                break
        output = '\n'.join(output.split('\n')[i:])
        try:
            cluster_info = json.loads(output)
        except ValueError:
            fun_test.critical('JSON decode Failed')

        cluster_3 = cluster_info['Clusters'][2]
        cluster_4 = cluster_info['Clusters'][3]

        for cluster in [cluster_3, cluster_4]:
            for slot in cluster['LogicDrawer']:
                if slot['Domains'][0]['Owner'] == 'regression' and \
                                slot['Domains'][0]['Design'] == 'RESERVED*':
                    return slot['Domains'][0]['ReservedKey']
        return None 

    def _release_reservation(self):
        cmd = 'test_server -rmkey {}'.format(self.reservation_key)
        try:
            output = self.linux.command(cmd)
        except Exception as ex:
            fun_test.critical(str(ex))

    def cleanup_job(self):

        cmd1 = 'pkill perl'
        cmd2 = 'pkill startup1'
        cmd3 = 'pkill xeDebug'
        cmd4 = 'pkill ncsim'
        cmd5 = 'pkill DBEngine_rpcbin'

        self.linux.command(cmd1)
        self.linux.command(cmd2)
        self.linux.command(cmd3)
        self.linux.command(cmd4)
        self.linux.command(cmd5)


def main():
    palladium_obj = Palladium()
    if not palladium_obj.boot():
        palladium_obj.cleanup_job()
    else:
        dpcsh_obj = DpcshProxy()
        dpcsh_obj.start()
        network_controller_obj = NetworkController(dpc_server_ip='server120', dpc_server_port=40221)
        time.sleep(180)
        try:
            output = network_controller_obj._echo_hello()
        except Exception as ex:
            fun_test.critical(str(ex))

        time.sleep(180)
        try:
            output = network_controller_obj._echo_hello()
        except Exception as ex:
            fun_test.critical(str(ex))

        print output

        try:
            output = network_controller_obj._echo_hello()
        except Exception as ex:
            fun_test.critical(str(ex))

        print output

if __name__ == '__main__':
    main()

