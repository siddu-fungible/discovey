from lib.system.fun_test import *
from lib.host.linux import Linux
from lib.system.utils import MultiProcessingTasks
from prettytable import PrettyTable
from collections import OrderedDict
from random import randint
import re

IB_WRITE_BANDWIDTH_TEST = "ib_write_bw"
IB_WRITE_LATENCY_TEST = "ib_write_lat"
LD_LIBRARY_PATH = "/mnt/ws/fungible-rdma-core/build/lib/"
PATH = "/home/localadmin/mks/workspace/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/"


class RdmaClient(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password, server_ip, rdma_port, client_id):
        super(RdmaClient, self).__init__(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        self.server_ip = server_ip
        self.rdma_port = rdma_port
        self.client_id = client_id
        self.add_path(additional_path=PATH)
        self.set_ld_library_path()

    def set_ld_library_path(self):
        self.command(command="export LD_LIBRARY_PATH=%s" % LD_LIBRARY_PATH)

    def __hash__(self):
        return self.client_id

    def __eq__(self, other):
        return self.client_id == other.client_id


class RdmaServer(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password, server_id, server_port=None, interface_ip=None):
        super(RdmaServer, self).__init__(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        self.rdma_process_id = None
        self.server_id = server_id
        self.rdma_server_port = server_port
        self.interface_ip = interface_ip
        self.add_path(additional_path=PATH)
        self.set_ld_library_path()

    def set_ld_library_path(self):
        self.command(command="export LD_LIBRARY_PATH=%s" % LD_LIBRARY_PATH)

    def __hash__(self):
        return self.server_id

    def __eq__(self, other):
        return self.server_id == other.server_id


class RdmaTemplate(object):
    CONNECTION_TYPE_RC = "RC"

    def __init__(self, client_server_objs, test_type, hosts, is_parallel=True,
                 connection_type=CONNECTION_TYPE_RC, size=100, inline_size=64, duration=10, iterations=100):
        """
        RDMA Template for Scale Tool

        :param client_server_objs: List of Clients/Server Map objects
        :param test_type: RDMA Test Type can be IB_WRITE_BANDWIDTH_TEST or IB_WRITE_LATENCY_TEST test
        :param hosts: List of all hosts objects
        :param is_parallel: True/False  True if run traffic in parallel from all clients
        :param connection_type: RDMA tool connection type RC
        :param size: size in bytes for test
        :param inline_size: Inline size for latency test in bytes
        :param duration: Test duration in secs
        :param iterations: No of iterations needed for Latency test
        """
        self.is_parallel = is_parallel
        self.test_type = test_type
        self.connection_type = connection_type
        self.size = size
        self.inline_size = inline_size
        self.duration = duration
        self.client_server_objs = client_server_objs
        self.hosts = hosts
        self.iterations = iterations

    def setup_test(self):
        result = False
        try:
            module_cmds = ['sudo insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko',
                           'sudo modprobe rdma_ucm']
            for host_obj in self.hosts:
                fun_test.log_section("Configure %s host load all modules and export necessary paths" %
                                     str(host_obj))
                for cmd in module_cmds:
                    host_obj.command(cmd, timeout=90)
            fun_test.add_checkpoint(checkpoint="Setup RDMA Test")
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_ibv_device(self, host_obj):
        ibv_device = {'name': None, 'node_guid': None}
        try:
            cmd = "ibv_devices"
            output = host_obj.command(cmd)
            m = re.search(r'--.*.(fun.*.)\s+(\w+)', output, re.DOTALL)
            if m:
                name = m.group(1).strip()
                guid = m.group(2).strip()
                ibv_device['name'] = name
                ibv_device['node_guid'] = guid
        except Exception as ex:
            fun_test.critical(str(ex))
        return ibv_device

    def create_rdma_cmd(self, ibv_device, port_num, client_cmd=False, server_ip=None, **kwargs):
        cmd = None
        try:
            if self.test_type == IB_WRITE_BANDWIDTH_TEST:
                if '-c' in kwargs:
                    self.connection_type = kwargs['-c']

                if '-D' in kwargs and client_cmd:
                    self.duration = kwargs['-D']

                if '-s' in kwargs:
                    self.size = kwargs['-s']

                cmd = "%s -c %s -R -d %s -p %d -F -s %d " % (self.test_type, self.connection_type, ibv_device,
                                                             port_num, self.size)
                for key, val in kwargs.items():
                    if type(val) == list:
                        for op in val:
                            if op not in cmd:
                                cmd += "%s" % op
                    else:
                        if key not in cmd:
                            cmd += "%s %s " % (key, val)
                if client_cmd:
                    cmd += "-D %d %s " % (self.duration, server_ip)
            elif self.test_type == IB_WRITE_LATENCY_TEST:
                if '-c' in kwargs:
                    self.connection_type = kwargs['-c']

                if '-s' in kwargs:
                    self.size = kwargs['-s']

                if '-I' in kwargs:
                    self.inline_size = kwargs['-I']

                if '-n' in kwargs and client_cmd:
                    self.iterations = kwargs['-n']

                cmd = "%s -c %s -R -d %s -p %d -F -I %d -s %d " % (self.test_type, self.connection_type, ibv_device,
                                                                   port_num, self.inline_size, self.size)
                for key, val in kwargs.items():
                    if type(val) == list:
                        for op in val:
                            if op not in cmd:
                                cmd += "%s" % op
                    else:
                        if key not in cmd:
                            cmd += "%s %s " % (key, val)
                if client_cmd:
                    cmd += "-n %d %s " % (self.iterations, server_ip)
            fun_test.log('Cmd Formed: %s' % cmd)
        except Exception as ex:
            fun_test.critical(str(ex))
        return cmd

    def _setup_server(self, server_obj, **kwargs):
        result = False
        try:
            fun_test.log_section("Setup %s server with RDMA port %d" % (str(server_obj),
                                                                        server_obj.rdma_server_port))
            ibv_device = self.get_ibv_device(host_obj=server_obj)
            cmd = self.create_rdma_cmd(ibv_device=ibv_device['name'], port_num=server_obj.rdma_server_port, client_cmd=False,
                                       **kwargs)
            tmp_output_file = "/tmp/%s_server_process_%d.log" % (
                self.test_type, server_obj.rdma_server_port)
            process_id = server_obj.start_bg_process(command=cmd, output_file=tmp_output_file)
            fun_test.log("Server Process Started: %s" % process_id)
            fun_test.simple_assert(process_id, "Rdma server process started")
            server_obj.rdma_process_id = process_id
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def setup_servers(self):
        result = False
        try:
            checkpoint = "Configure all servers and start the tool %s" % self.test_type
            for c_s_dict in self.client_server_objs:
                for client_obj, server_obj in c_s_dict.items():
                    if type(server_obj) == list:
                        for obj in server_obj:
                            result = self._setup_server(server_obj=obj)
                    else:
                        result = self._setup_server(server_obj=server_obj)
            fun_test.add_checkpoint(checkpoint)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_test(self, client_obj, server_obj, set_paths=False, cmd_args=None):
        result_dict = OrderedDict()
        try:
            fun_test.log_section("Run traffic from %s client -----> %s server" % (str(client_obj), str(server_obj)))
            result_dict['client'] = str(client_obj)
            result_dict['server'] = str(server_obj)
            port_no = RdmaHelper.generate_random_port_no()
            server_obj.rdma_server_port = port_no
            client_obj.rdma_port = port_no
            client_obj.server_ip = server_obj.interface_ip
            if set_paths:
                client_obj.add_path(additional_path=PATH)
                client_obj.set_ld_library_path()
                server_obj.add_path(additional_path=PATH)
                server_obj.set_ld_library_path()
            res = self._setup_server(server_obj=server_obj, **cmd_args)
            fun_test.simple_assert(res, "Ensure on %s server process started" % str(server_obj))
            ibv_device = self.get_ibv_device(host_obj=client_obj)
            cmd = self.create_rdma_cmd(ibv_device=ibv_device['name'], port_num=client_obj.rdma_port, client_cmd=True,
                                       server_ip=client_obj.server_ip, **cmd_args)
            output = client_obj.command(command=cmd, timeout=90)
            result_dict = self._parse_rdma_output(output=output)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_dict

    def run(self, **kwargs):
        result = []
        try:
            if self.is_parallel:
                multi_task_obj = MultiProcessingTasks()
                process_count = 0
                for c_s_dict in self.client_server_objs:
                    for client_obj, server_obj in c_s_dict.items():
                        if type(server_obj) == list:
                            for obj in server_obj:
                                multi_task_obj.add_task(func=self.start_test,
                                                        func_args=(client_obj, obj, True, kwargs),
                                                        task_key="process_%s" % process_count)
                                process_count += 1
                        else:
                            multi_task_obj.add_task(func=self.start_test,
                                                    func_args=(client_obj, server_obj, True, kwargs),
                                                    task_key="process_%s" % process_count)
                            process_count += 1
                run_started = multi_task_obj.run(max_parallel_processes=process_count, parallel=True)
                fun_test.simple_assert(run_started, "Ensure Clients initiated simultaneously")
                for index in range(process_count):
                    result_dict = multi_task_obj.get_result(task_key="process_%s" % index)
                    result.append(result_dict)
            else:
                for c_s_dict in self.client_server_objs:
                    for client_obj, server_obj in c_s_dict.items():
                        if type(server_obj) == list:
                            for obj in server_obj:
                                result_dict = self.start_test(client_obj=client_obj, server_obj=obj,
                                                              cmd_args=kwargs)
                                result.append(result_dict)
                        else:
                            result_dict = self.start_test(client_obj=client_obj, server_obj=server_obj,
                                                          cmd_args=kwargs)
                            result.append(result_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _parse_rdma_output(self, output):
        result = {}
        try:
            m = re.search(r'(#bytes.*)', output, re.DOTALL)
            if m:
                chunk = m.group(1).strip()
                keys = re.split(r'\s\s+', chunk.split('\n')[0].strip())
                for i in range(0, len(keys)):
                    if '#bytes #iterations' in keys[i]:
                        v = keys[i].split()
                        keys.pop(i)
                        keys.insert(i, v[0])
                        keys.insert(i + 1, v[1])
                values = list(map(float, re.split(r'\s+', chunk.split('\n')[1].strip())))
                result = OrderedDict(zip(keys, values))
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_table(self, records, scenario_type):
        try:
            columns = records[0].keys()
            table_obj = PrettyTable(columns)
            rows = []
            for record in records:
                table_obj.add_row(record.values())
                rows.append(record.values())
            fun_test.log_section("Result table for %s test Scenario: %s" % (self.test_type, scenario_type))
            fun_test.log_disable_timestamps()
            fun_test.log("\n")
            fun_test.log(table_obj)
            fun_test.log_enable_timestamps()

            headers = columns
            table_name = "Aggregate Result of %s test scenario %s" % (self.test_type, scenario_type)
            table_data = {'headers': headers, 'rows': rows}
            fun_test.add_table(panel_header='RDMA %s Test Result Table' % self.test_type,
                               table_name=table_name, table_data=table_data)
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def cleanup(self):
        try:
            for c_s_dict in self.client_server_objs:
                for client_obj, server_obj in c_s_dict.items():
                    client_obj.disconnect()
                    if type(server_obj) == list:
                        for obj in server_obj:
                            obj.disconnect()
                    else:
                        server_obj.disconnect()
        except Exception as ex:
            fun_test.critical(str(ex))


class RdmaHelper(object):
    SCENARIO_TYPE_1_1 = "1_1"
    SCENARIO_TYPE_N_1 = "N_1"
    SCENARIO_TYPE_N_N = "N_N"
    CONFIG_JSON = SCRIPTS_DIR + "/networking/rdma/config.json"
    HOSTS_ASSET = ASSET_DIR + "/hosts.json"

    def __init__(self, scenario_type):
        self.scenario_type = scenario_type
        self.config = fun_test.parse_file_to_json(file_name=self.CONFIG_JSON)
        self.hosts = fun_test.parse_file_to_json(file_name=self.HOSTS_ASSET)
        self.host_objs = []

    def get_list_of_servers(self):
        servers = []
        try:
            for key in self.config:
                if key == self.scenario_type:
                    servers = self.config[key]['servers']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return servers

    def get_list_of_clients(self):
        clients = []
        try:
            for key in self.config:
                if key == self.scenario_type:
                    clients = self.config[key]['clients']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return clients

    @staticmethod
    def generate_random_port_no():
        return randint(20000, 30000)

    def get_client_server_map(self):
        client_server_map = {}
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'client_server_map' in self.config[key]:
                        client_server_map = self.config[key]['client_server_map']
                        break
                    else:
                        clients = self.get_list_of_clients()
                        servers = self.get_list_of_servers()
                        for client in clients:
                            for server in servers:
                                client_server_map[client] = server
        except Exception as ex:
            fun_test.critical(str(ex))
        return client_server_map

    def is_parallel(self):
        result = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    result = self.config[key]['is_parallel']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_traffic_size_in_bytes(self):
        size = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    size = self.config[key]['size_in_bytes']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return size

    def get_traffic_duration_in_secs(self):
        duration_in_secs = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    duration_in_secs = self.config[key]['duration_in_secs']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return duration_in_secs

    def get_traffic_iterations(self):
        iterations = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    iterations = self.config[key]['iterations']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return iterations

    def get_inline_size(self):
        inline_size = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    inline_size = self.config[key]['inline_size']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return inline_size

    def _fetch_client_dict(self, client_name):
        result = None
        try:
            for host in self.hosts:
                if host == client_name:
                    result = self.hosts[host]
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _fetch_server_dict(self, server_name):
        result = None
        try:
            for host in self.hosts:
                if host == server_name:
                    result = self.hosts[host]
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_hu_interface_ip(self, server_name):
        hu_interface_ip = None
        try:
            for server in self.get_list_of_servers():
                if server['host_ip'] == server_name:
                    hu_interface_ip = server['hu_interface_ip']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return hu_interface_ip

    def _get_all_hosts_full_mesh(self):
        hosts = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    hosts = self.config[key]['hosts']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return hosts

    def create_client_server_map_full_mesh(self):
        result = []
        try:
            client_id = 1
            server_id = 1
            clients = []
            servers = []
            for host in self._get_all_hosts_full_mesh():
                host_dict = self._fetch_client_dict(client_name=host['host_ip'])
                hu_interface_ip = host['hu_interface_ip']
                fun_test.simple_assert(host_dict, "Unable to find host %s info in hosts.json under asset" %
                                       host['host_ip'])
                client_obj = RdmaClient(host_ip=host_dict['host_ip'], ssh_username=host_dict['ssh_username'],
                                        ssh_password=host_dict['ssh_password'], server_ip=None, rdma_port=None,
                                        client_id=client_id)
                server_obj = RdmaServer(host_ip=host_dict['host_ip'], ssh_username=host_dict['ssh_username'],
                                        ssh_password=host_dict['ssh_password'], server_id=server_id,
                                        interface_ip=hu_interface_ip, server_port=None)
                clients.append(client_obj)
                servers.append(server_obj)
                client_id += 1
                server_id += 1
            self.host_objs.extend(clients)
            for client_obj in clients:
                server_objs = []
                for server_obj in servers:
                    if client_obj.host_ip == server_obj.host_ip:
                        continue
                    server_objs.append(server_obj)
                result.append({client_obj: server_objs})
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_client_server_objects(self):
        result = []
        try:
            if self.scenario_type == self.SCENARIO_TYPE_N_N:
                result = self.create_client_server_map_full_mesh()
            else:
                client_id = 1
                server_id = 1
                client_server_map = self.get_client_server_map()
                for client, server in client_server_map.items():
                    client_dict = self._fetch_client_dict(client)
                    fun_test.simple_assert(client_dict, "Unable to find client %s info in hosts.json under asset. " %
                                           client)
                    server_dict = self._fetch_server_dict(server)
                    fun_test.simple_assert(server_dict, "Unable to find server %s info in hosts.json under asset. " %
                                           server)
                    hu_interface_ip = self._get_hu_interface_ip(server_name=server)
                    client_obj = RdmaClient(host_ip=client_dict['host_ip'], ssh_username=client_dict['ssh_username'],
                                            ssh_password=client_dict['ssh_password'], server_ip=None,
                                            rdma_port=None, client_id=client_id)
                    server_obj = RdmaServer(host_ip=server_dict['host_ip'], ssh_password=server_dict['ssh_password'],
                                            ssh_username=server_dict['ssh_username'], interface_ip=hu_interface_ip,
                                            server_port=None, server_id=server_id)
                    result.append({client_obj: server_obj})
                    self.host_objs.append(client_obj)
                    self.host_objs.append(server_obj)
                    client_id += 1
                    server_id += 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
