from lib.system.fun_test import *
from lib.host.linux import Linux
from lib.system.utils import MultiProcessingTasks
from prettytable import PrettyTable
from collections import OrderedDict
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


class RdmaServer(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password, server_id, server_port=20000):
        super(RdmaServer, self).__init__(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        self.rdma_process_id = None
        self.server_id = server_id
        self.rdma_server_port = server_port
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
    SCENARIO_TYPE_1_1 = "1_1"

    def __init__(self, servers, clients, client_server_objs, test_type, is_parallel=True,
                 connection_type=CONNECTION_TYPE_RC, size=100, inline_size=64, duration=10):
        """
        RDMA Scale Tool template
        :param servers: List of all RDMA server objs
        :param clients: List of all RDMA client objs
        :param test_type: Can be IB_WRITE_BANDWIDTH_TEST or IB_WRITE_LATENCY_TEST
        :param is_parallel: Default True. Flag to start traffic in parallel from all clients
        """
        self.clients = clients
        self.servers = servers
        self.is_parallel = is_parallel
        self.test_type = test_type
        self.connection_type = connection_type
        self.size = size
        self.inline_size = inline_size
        self.duration = duration
        self.client_server_objs = client_server_objs

    def setup_test(self):
        result = False
        try:
            module_cmds = ['sudo insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko',
                           'sudo modprobe rdma_ucm']
            for c_s_dict in self.client_server_objs:
                hosts = c_s_dict.keys() + c_s_dict.values()
                for host_obj in hosts:
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

    def setup_servers(self):
        result = False
        try:
            checkpoint = "Configure all servers and start the tool %s" % self.test_type
            for c_s_dict in self.client_server_objs:
                for client_obj, server_obj in c_s_dict.items():
                    fun_test.log_section("Setup %s server with RDMA port %d" % (str(server_obj),
                                                                                server_obj.rdma_server_port))
                    ibv_device = self.get_ibv_device(host_obj=server_obj)
                    # TODO: Add cmd args
                    if self.test_type == IB_WRITE_BANDWIDTH_TEST:
                        cmd = "%s -c %s -R -d %s -p %d -F -s %d" % (
                            self.test_type, self.connection_type, ibv_device['name'],
                            server_obj.rdma_server_port, self.size)
                    elif self.test_type == IB_WRITE_LATENCY_TEST:
                        cmd = "%s -c %s -R -d %s -p %d -F -I %d -s %d" % (
                            self.test_type, self.connection_type, ibv_device['name'], server_obj.rdma_server_port,
                            self.inline_size, self.size)
                    else:
                        # TODO: Set default test
                        cmd = None
                    fun_test.log("Server cmd formed: %s " % cmd)
                    tmp_output_file = "/tmp/%s_server_process_%d.log" % (
                        self.test_type, server_obj.rdma_server_port)
                    process_id = server_obj.start_bg_process(command=cmd, output_file=tmp_output_file)
                    fun_test.log("Server Process Started: %s" % process_id)
                    fun_test.simple_assert(process_id, "Rdma server process started")
                    server_obj.rdma_process_id = process_id
            fun_test.add_checkpoint(checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def start_test(self, client_obj, server_obj, iterations, set_paths=False):
        result_dict = {}
        try:
            fun_test.log_section("Run %s client" % (str(client_obj)))
            if set_paths:
                client_obj.add_path(additional_path=PATH)
                client_obj.set_ld_library_path()
                # server_obj.add_path(additional_path=PATH)
                # server_obj.set_ld_library_path()
            ibv_device = self.get_ibv_device(host_obj=client_obj)
            # TODO: Add cmd args
            if self.test_type == IB_WRITE_BANDWIDTH_TEST:
                cmd = "%s -c %s -R -d %s -p %d -F -s %d " % (
                    self.test_type, self.connection_type, ibv_device['name'], client_obj.rdma_port,
                    self.size)
            elif self.test_type == IB_WRITE_LATENCY_TEST:
                cmd = "%s -c %s -R -d %s -p %d -F -I %d -s %d " % (
                    self.test_type, self.connection_type, ibv_device['name'], client_obj.rdma_port,
                    self.inline_size, self.size)
            else:
                # TODO: Set default test
                cmd = None
            if iterations:
                cmd += "-n %d %s" % (iterations, client_obj.server_ip)
            else:
                cmd += "-D %d %s" % (self.duration, client_obj.server_ip)

            fun_test.log("Client Cmd Formed: %s" % cmd)
            output = client_obj.command(command=cmd, timeout=90)
            result_dict = self._parse_rdma_output(output=output)
            result_dict['client'] = str(client_obj)
            result_dict['server'] = str(server_obj)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_dict

    def run(self, iterations=None):
        result = []
        try:
            if self.is_parallel:
                multi_task_obj = MultiProcessingTasks()
                process_count = 0
                for c_s_dict in self.client_server_objs:
                    for client_obj, server_obj in c_s_dict.items():
                        multi_task_obj.add_task(func=self.start_test,
                                                func_args=(client_obj, server_obj, iterations, True),
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
                        result_dict = self.start_test(client_obj=client_obj, server_obj=server_obj,
                                                      iterations=iterations)
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
                    server_obj.disconnect()
        except Exception as ex:
            fun_test.critical(str(ex))


class RdmaHelper(object):
    SCENARIO_TYPE_1_1 = "1_1"
    CONFIG_JSON = SCRIPTS_DIR + "/networking/rdma/config.json"
    HOSTS_ASSET = ASSET_DIR + "/hosts.json"

    def __init__(self, scenario_type):
        self.scenario_type = scenario_type
        self.config = fun_test.parse_file_to_json(file_name=self.CONFIG_JSON)
        self.hosts = fun_test.parse_file_to_json(file_name=self.HOSTS_ASSET)

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

    def get_client_server_map(self):
        client_server_map = {}
        try:
            for key in self.config:
                if key == self.scenario_type:
                    client_server_map = self.config[key]['client_server_map']
                    break
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

    def create_client_server_objects(self, client_server_map):
        result = []
        try:
            rdma_port = 20000
            client_id = 1
            server_id = 1
            for client, server in client_server_map.items():
                client_dict = self._fetch_client_dict(client)
                fun_test.simple_assert(client_dict, "Unable to find client %s info in hosts.json under asset. " %
                                       client)
                server_dict = self._fetch_server_dict(server)
                fun_test.simple_assert(server_dict, "Unable to find server %s info in hosts.json under asset. " %
                                       server)
                hu_interface_ip = self._get_hu_interface_ip(server_name=server)
                client_obj = RdmaClient(host_ip=client_dict['host_ip'], ssh_username=client_dict['ssh_username'],
                                        ssh_password=client_dict['ssh_password'], server_ip=hu_interface_ip,
                                        rdma_port=rdma_port, client_id=client_id)
                server_obj = RdmaServer(host_ip=server_dict['host_ip'], ssh_password=server_dict['ssh_password'],
                                        ssh_username=server_dict['ssh_username'], server_port=rdma_port,
                                        server_id=server_id)
                result.append({client_obj: server_obj})
                rdma_port += 1
                client_id += 1
                server_id += 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
