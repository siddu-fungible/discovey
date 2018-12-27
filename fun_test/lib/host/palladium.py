#! /usr/bin/python

from lib.system.fun_test import *
from lib.host.network_controller import NetworkController
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import re, os, json
from os.path import expanduser

HOME_DIR = "/home/{}".format(REGRESSION_USER)


class DpcshProxy(object):

    def __init__(self, ip='server120', dpcsh_port=40221, usb='ttyUSB6', dpc_bin_path='image',
                 user=REGRESSION_USER, password=REGRESSION_USER_PASSWORD):

        self.ip = ip
        self.dpcsh_port = dpcsh_port
        self.usb = usb
        self.dpc_bin_path = dpc_bin_path
        self.pid = None
        self.linux = Linux(host_ip=ip,
                           ssh_username=user,
                           ssh_password=password)
        self.network_controller_obj = NetworkController(dpc_server_ip=self.ip, dpc_server_port=self.dpcsh_port)

    def start(self):
        result = False
        env_cmd = 'setenv LD_LIBRARY_PATH "/project/tools/glibc-2.14/lib"'
        run_cmd = 'nohup ./dpcsh  -D /dev/{} --tcp_proxy={} > /tmp/start_dpc.out & '.format(self.usb, self.dpcsh_port)
        try:
            self.linux.command(env_cmd)
            self.pid = self.linux.command(run_cmd).strip().split(' ')[-1]
            result = True
        except Exception as ex:
            if re.search(r'Timeout\s+exceeded.*', str(ex), re.IGNORECASE):
                result = True
            else:
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

    def ensure_started(self, max_time=900, interval=30):
        result = False
        try:
            timer = FunTimer(max_time=max_time)
            while not timer.is_expired():
                fun_test.sleep("DPCsh to come up", seconds=interval)
                output = self.network_controller_obj.echo_hello()
                if output:
                    fun_test.log("Successfully started dpcsh echoed hello output: %s" % output)
                    result = True
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def run_dpc_shutdown(self):
        result = False
        try:
            result = self.network_controller_obj.dpc_shutdown()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    @fun_test.safe
    def stop_dpcsh_proxy(self, dpcsh_proxy_name="dpcsh", dpcsh_proxy_port=40221, dpcsh_proxy_tty="ttyUSB8"):
        process_pat = dpcsh_proxy_name + '.*' + dpcsh_proxy_tty
        current_dpcsh_proxy_pid = self.linux.get_process_id_by_pattern(process_pat)
        if current_dpcsh_proxy_pid:
            self.linux.kill_process(process_id=current_dpcsh_proxy_pid, sudo=False)
            self.linux.command("\n")
            current_dpcsh_proxy_pid = self.linux.get_process_id_by_pattern(process_pat)
            if current_dpcsh_proxy_pid:
                fun_test.critical("Unable to kill the existing dpcsh proxy process")
                return False
        else:
            fun_test.log("No dpcsh proxy listening in port {}".format(dpcsh_proxy_port))
        return True

    @fun_test.safe
    def start_dpcsh_proxy(self, dpcsh_env="/project/tools/glibc-2.14/lib",
                          dpcsh_proxy_path="/home/gliang/ws/FunSDK/bin", dpcsh_proxy_name="dpcsh",
                          dpcsh_proxy_port=40221, dpcsh_proxy_tty="/dev/ttyUSB8",
                          dpcsh_proxy_log="/tmp/dpcsh_proxy_log"):
        # Killling any existing dpcsh TCP proxy server running outside the qemu host
        status = self.stop_dpcsh_proxy(dpcsh_proxy_name, dpcsh_proxy_port, dpcsh_proxy_tty)
        if not status:
            return False

        dpcsh_proxy_cmd = "env LD_LIBRARY_PATH={} {}/{} -D {} --tcp_proxy={}".format(dpcsh_env, dpcsh_proxy_path,
                                                                                     dpcsh_proxy_name, dpcsh_proxy_tty,
                                                                                     dpcsh_proxy_port)
        dpcsh_proxy_process_id = self.linux.start_bg_process(command=dpcsh_proxy_cmd, output_file=dpcsh_proxy_log)
        # Checking whether the dpcsh proxy is started properly
        if dpcsh_proxy_process_id:
            self.linux.command("\n")
            process_pat = dpcsh_proxy_name + '.*' + dpcsh_proxy_tty
            current_dpcsh_proxy_process_id = self.linux.get_process_id_by_pattern(process_pat)
            if not current_dpcsh_proxy_process_id:
                return False
        else:
            return False
        return True

    @fun_test.safe
    def ipmi_power_off(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN"):
        return self.linux.ipmi_power_off(host=host, interface=interface, user=user, passwd=passwd)

    @fun_test.safe
    def ipmi_power_on(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN"):
        return self.linux.ipmi_power_on(host=host, interface=interface, user=user, passwd=passwd)

    @fun_test.safe
    def ipmi_power_cycle(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN", interval=30):
        return self.linux.ipmi_power_cycle(host=host, interface=interface, user=user, passwd=passwd, interval=interval)


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
        self.image_dir = HOME_DIR + image_dir
        self.rdp_dir = HOME_DIR + rdp_dir
        self.odp_dir = HOME_DIR + odp_dir
        self.model = model
        self.design = design
        self.reservation_key = ''
        self.pid = None
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
       
        self._cleanup_run_dir()
 
        try:
            timer = FunTimer(max_time=3600)
            while not timer.is_expired():
                if self._is_available():
                    break
                else:
                    fun_test.sleep("Waiting for Boards/TPOD to be free...sleeping 60 secs", seconds=60)
            try:
                self.pid = self.linux.command(cmd).strip().split(' ')[-1]
            except Exception as ex:
                if re.search(r'Timeout\s+exceeded.*', str(ex), re.IGNORECASE):
                    pass
                else:
                    raise ex
                    # a Real error occurred
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

        except Exception as ex:
            fun_test.critical(str(ex))

        return result

    def _is_booted(self):
        timer = FunTimer(max_time=1800)
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

        # Fake a reservation key to workaround Cadence bug
        return 99999 
        cmd = 'test_server -json'
        try:
            output = self.linux.command(cmd, timeout=180)
            
            for i, v in enumerate(output.split('\n')):
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
        except Exception as ex:
            fun_test.critical(str(ex))
        return None 

    def _release_reservation(self):
        
        # Fake release of reservation key to workaround Cadence bug
        return
        cmd = 'test_server -rmkey {}'.format(self.reservation_key)
        try:
            output = self.linux.command(cmd)
        except Exception as ex:
            fun_test.critical(str(ex))

    def ensure_boards_released(self):
        result = True
        cmd = "test_server -json"
        try:
            output = self.linux.command(cmd, timeout=180)
            json_output = None
            for i, v in enumerate(output.split('\n')):
                if v.strip() == '{':
                    json_output = '\n'.join(output.split('\n')[i:])
                    break
            cluster_info = json.loads(json_output)

            cluster_3 = cluster_info['Clusters'][2]
            cluster_4 = cluster_info['Clusters'][3]

            for cluster in [cluster_3, cluster_4]:
                for slot in cluster['LogicDrawer']:
                    if slot['Domains'][0]['Owner'] == 'regression' and slot['Domains'][0]['Design'] == 'RESERVED':
                        fun_test.log("Boards are not released by user %s" % REGRESSION_USER)
                        result = False
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _cleanup_run_dir(self):
        
        cmd_list = ['rm -rf {}/*'.format(self.rdp_dir), 'rm -rf {}/*'.format(self.odp_dir)]
        for cmd in cmd_list:
            self.linux.command(cmd)

    def cleanup_job(self):
        result = False
        cmd_list = ['pkill perl', 'pkill startup1', 'pkill xeDebug', 'pkill ncsim', 'pkill DBEngine_rpcbin']
        try:
            for cmd in cmd_list:
                self.linux.command(cmd)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


def main():
    try:
        config = parse_file_to_json(ASSET_DIR + "/palladium_hosts.json")[0]
        fun_test.log(config)
        
        palladium_obj = Palladium(ip=config['boot_up_server_ip'], model=config['model'], 
                                  design=config['design'])
        
        if not palladium_obj.boot():
            palladium_obj.cleanup_job()
        else:
            dpcsh_obj = DpcshProxy(ip=config['dpcsh_tcp_proxy_ip'], dpcsh_port=config['dpcsh_tcp_proxy_port'],
                                   usb=config['dpcsh_usb'])
            if dpcsh_obj.start():
                print dpcsh_obj.ensure_started()
            else:
                raise Exception("Failed to start dpcsh on %s port %d" % (config['dpcsh_tcp_proxy_ip'],
                                                                         config['dpcsh_tcp_proxy_port']))               
    except Exception as ex:
        fun_test.critical(str(ex))


if __name__ == '__main__':
    main()

