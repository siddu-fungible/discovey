from lib.system.fun_test import *
from lib.host.linux import Linux
from lib.system.utils import MultiProcessingTasks
from prettytable import PrettyTable
from collections import OrderedDict
from random import randint
import re

IB_WRITE_BANDWIDTH_TEST = "ib_write_bw"
IB_WRITE_LATENCY_TEST = "ib_write_lat"
LD_LIBRARY_PATH = "/mnt/ws/fungible-rdma-core/build/lib"
PATH = "/mnt/ws/fungible-rdma-core/build/bin:/mnt/ws/fungible-perftest:$PATH"


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
    # CONNECTION_TYPE_RC = "RC"
    CONNECTION_TYPE_RC = None

    def __init__(self, client_server_objs, test_type, hosts, is_parallel=True,
                 connection_type=CONNECTION_TYPE_RC, size=100, qpairs=1, inline_size=64, duration=10, iterations=100,
                 run_infinitely=10, combined_log=None):
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
        :param run_infinitely: To run the tool infinitely and dump stats at certain interval Default 10 secs.
        """
        self.is_parallel = is_parallel
        self.test_type = test_type
        self.connection_type = connection_type
        self.size = size if size else 1
        self.inline_size = inline_size
        self.duration = duration if duration else 10
        self.client_server_objs = client_server_objs
        self.hosts = hosts
        self.iterations = iterations if iterations else 100
        self.run_infinitely = run_infinitely
        self.qpairs = qpairs if qpairs else 1
        self.combined_log = combined_log

    def setup_test(self):
        result = False
        try:
            for host_obj in self.hosts:
                fun_test.log_section("Configure %s host load all modules and export necessary paths" %
                                     str(host_obj))
                if not host_obj.lsmod("funrdma"):
                    host_obj.sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko")
                if not host_obj.lsmod("rdma_ucm"):
                    host_obj.sudo_command("modprobe rdma_ucm")
                host_obj.sudo_command("rm -rf /tmp/*  /usr/bin/ib_write_bw /usr/bin/ib_write_lat")
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

                if 'run_infinitely' in kwargs and client_cmd:
                    self.run_infinitely = kwargs['--run_infinitely']

                if '-D' in kwargs and client_cmd:
                    self.duration = kwargs['-D']

                if '-s' in kwargs:
                    self.size = kwargs['-s']

                if not self.connection_type:
                    cmd = "%s -d %s -q %d -p %d -F -s %d --report_gbits " % (self.test_type, ibv_device,
                                                                             self.qpairs, port_num, self.size)
                else:
                    cmd = "%s -c %s -R -d %s -q %d -p %d -F -s %d --report_gbits " % (self.test_type,
                                                                                      self.connection_type,
                                                                                      self.qpairs, ibv_device,
                                                                                      port_num, self.size)
                if self.run_infinitely:
                    cmd += "--run_infinitely -D %d " % (self.run_infinitely)
                else:
                    cmd += "-D %d " % (self.duration)

                if client_cmd:
                        cmd += "%s " % (server_ip)
                        
                for key, val in kwargs.items():
                    if type(val) == list:
                        for op in val:
                            if op not in cmd:
                                cmd += "%s" % op
                    else:
                        if key not in cmd:
                            cmd += "%s %s " % (key, val)
            elif self.test_type == IB_WRITE_LATENCY_TEST:
                if '-c' in kwargs:
                    self.connection_type = kwargs['-c']

                if 'run_infinitely' in kwargs and client_cmd:
                    self.run_infinitely = kwargs['--run_infinitely']

                if '-s' in kwargs:
                    self.size = kwargs['-s']

                if '-I' in kwargs:
                    self.inline_size = kwargs['-I']

                if '-n' in kwargs:
                    self.iterations = kwargs['-n']

                if not self.connection_type:
                    cmd = "%s -d %s -p %d -F -I %d -s %d " % (self.test_type, ibv_device,
                                                              port_num, self.inline_size,
                                                              self.size)
                else:
                    cmd = "%s -c %s -R -d %s -p %d -F -I %d -s %d " % (self.test_type, self.connection_type,
                                                                       ibv_device, port_num,
                                                                       self.inline_size, self.size)

                # For latency test use self.iterations with run_infinitely. Coz when used with latency_under_load
                # duration field is used as kill_timer and run_infinitely value is used as logging interval
                if self.run_infinitely:
                    cmd += "--run_infinitely -n %d " % self.iterations
                else:
                    if '-n' not in cmd:
                        cmd += "-n %d" % self.iterations

                if client_cmd:
                    cmd += " %s" % server_ip
                    
                for key, val in kwargs.items():
                    if type(val) == list:
                        for op in val:
                            if op not in cmd:
                                cmd += "%s" % op
                    else:
                        if key not in cmd:
                            cmd += "%s %s " % (key, val)
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
            cmd = self.create_rdma_cmd(ibv_device=ibv_device['name'], port_num=server_obj.rdma_server_port,
                                       client_cmd=False, **kwargs)
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
        try:
            fun_test.log_section("Run traffic from %s -----> %s" % (str(client_obj), str(server_obj)))
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
            if self.run_infinitely:
                tmp_output_file = "/tmp/%s_client_process_%d.log" % (
                    self.test_type, server_obj.rdma_server_port)
                process_id = client_obj.start_bg_process(command=cmd, output_file=tmp_output_file, nohup=True)
                fun_test.log('Client Process Started: %s' % process_id)
                fun_test.sleep(message="Client cmd running infinitely", seconds=self.duration)
                client_obj.kill_process(process_id=process_id, signal=9)
                server_obj.kill_process(process_id=server_obj.rdma_process_id, signal=9)
                output = client_obj.read_file(file_name=tmp_output_file, include_last_line=True)
                result = self._parse_rdma_output(output=output)
            else:
                output = client_obj.command(command=cmd, timeout=2100)
                result = self._parse_rdma_output(output=output)
            if not self.combined_log:
                result.update({'client': str(client_obj)})
                result.update({'server': str(server_obj)})
        except Exception as ex:
            fun_test.critical(str(ex))
        finally:
            server_obj.kill_process(process_id=server_obj.rdma_process_id, signal=9)
        return result

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
        if self.combined_log:
            result = []
            try:
                m = re.search(r'(#bytes.*)', output, re.DOTALL)
                if m:
                    required_output = m.group()
                    host_name = re.search(r'@(.*):', required_output).group(1)
                    lines = required_output.split("\n")
                    for line in lines:
                        match_nu = re.findall(r'[\d.]+', line)
                        if match_nu:
                            bw_avg = match_nu[3]
                            one_data_set = {
                                host_name: bw_avg
                            }
                            result.append(one_data_set)
            except Exception as ex:
                fun_test.critical(str(ex))
            return result
        else:
            result = {}
            try:
                m = re.search(r'(#bytes.*)', output, re.DOTALL)
                if m:
                    chunk = m.group(1).strip()
                    m1 = re.search(r'\d+(\w+@.*)', chunk.strip(), re.DOTALL)
                    if m1:
                        pat = m1.group(1)
                        chunk = re.sub(pat, "", chunk)

                    keys = re.split(r'\s\s+', chunk.split('\n')[0].strip())
                    for i in range(0, len(keys)):
                        if '#bytes #iterations' in keys[i]:
                            v = keys[i].split()
                            keys.pop(i)
                            keys.insert(i, v[0])
                            keys.insert(i + 1, v[1])
                    if self.run_infinitely:
                        if "Latency" in output and "tps average" in output:
                            index = 1
                        else:
                            index = -1
                    else:
                        index = 1
                    values = list(map(float, re.split(r'\s+', chunk.split('\n')[index].strip())))
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


class RdmaLatencyUnderLoadTemplate(object):

    def __init__(self, lat_test_type, bw_test_type, lat_client_server_objs, bw_client_server_objs, bw_test_size,
                 lat_test_size, inline_size, qpairs,
                 duration, iterations, run_infinitely, hosts,
                 connection_type=RdmaTemplate.CONNECTION_TYPE_RC):
        self.duration = duration
        self.lat_client_server_objs = lat_client_server_objs
        self.bw_client_server_objs = bw_client_server_objs
        self.lat_test_template = RdmaTemplate(client_server_objs=self.lat_client_server_objs, hosts=hosts,
                                              test_type=lat_test_type, is_parallel=True,
                                              connection_type=connection_type, size=lat_test_size,
                                              inline_size=inline_size, duration=duration,
                                              iterations=iterations, run_infinitely=run_infinitely)
        self.bw_test_template = RdmaTemplate(client_server_objs=self.bw_client_server_objs, hosts=hosts,
                                             test_type=bw_test_type, is_parallel=True,
                                             connection_type=connection_type, size=bw_test_size,
                                             inline_size=inline_size, duration=duration,
                                             iterations=iterations, run_infinitely=run_infinitely)

    def setup_test(self):
        result = False
        try:
            result = self.lat_test_template.setup_test()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def run(self, **kwargs):
        result = []
        try:
            multi_task_obj = MultiProcessingTasks()
            process_count = 0
            for bw_dict in self.bw_client_server_objs:
                for client_obj, server_obj in bw_dict.items():
                    if type(server_obj) == list:
                        for obj in server_obj:
                            multi_task_obj.add_task(func=self.start_test,
                                                    func_args=(client_obj, obj, self.bw_test_template.test_type,
                                                               kwargs),
                                                    task_key="process_%s" % process_count)
                            process_count += 1
                    else:
                        multi_task_obj.add_task(func=self.start_test,
                                                func_args=(client_obj, server_obj, self.bw_test_template.test_type,
                                                           kwargs),
                                                task_key="process_%s" % process_count)
                        process_count += 1
            for lat_dict in self.lat_client_server_objs:
                for client_obj, server_obj in lat_dict.items():
                    if type(server_obj) == list:
                        for obj in server_obj:
                            multi_task_obj.add_task(func=self.start_test,
                                                    func_args=(client_obj, obj, self.lat_test_template.test_type,
                                                               kwargs),
                                                    task_key="process_%s" % process_count)
                            process_count += 1
                    else:
                        multi_task_obj.add_task(func=self.start_test,
                                                func_args=(client_obj, server_obj, self.lat_test_template.test_type,
                                                           kwargs),
                                                task_key="process_%s" % process_count)
                        process_count += 1

            run_started = multi_task_obj.run(max_parallel_processes=process_count, parallel=True)
            fun_test.simple_assert(run_started, "Ensure Clients initiated simultaneously")
            for index in range(process_count):
                result_dict = multi_task_obj.get_result(task_key="process_%s" % index)
                result.append(result_dict)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def setup_server(self, test_type, server_obj, **cmd_args):
        result = False
        try:
            fun_test.log_section("Setup %s server with RDMA port %d" % (str(server_obj),
                                                                        server_obj.rdma_server_port))
            ibv_device = self.lat_test_template.get_ibv_device(host_obj=server_obj)
            cmd = self.create_rdma_cmd(ibv_device=ibv_device['name'], port_num=server_obj.rdma_server_port,
                                       test_type=test_type, client_cmd=False, **cmd_args)
            tmp_output_file = "/tmp/%s_server_process_%d.log" % (test_type, server_obj.rdma_server_port)
            process_id = server_obj.start_bg_process(command=cmd, output_file=tmp_output_file)
            fun_test.log("Server Process Started: %s" % process_id)
            fun_test.simple_assert(process_id, "Rdma server process started")
            server_obj.rdma_process_id = process_id
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_rdma_cmd(self, ibv_device, test_type, port_num, client_cmd=False, server_ip=None, **cmd_args):

        if test_type == self.lat_test_template.test_type:
            return self.lat_test_template.create_rdma_cmd(ibv_device=ibv_device, port_num=port_num,
                                                          client_cmd=client_cmd, server_ip=server_ip, **cmd_args)
        else:
            return self.bw_test_template.create_rdma_cmd(ibv_device=ibv_device, port_num=port_num,
                                                         client_cmd=client_cmd, server_ip=server_ip, **cmd_args)

    def start_test(self, client_obj, server_obj, test_type, cmd_args=None):
        result_dict = {}
        try:
            fun_test.log_section("Run traffic from %s -----> %s" % (str(client_obj), str(server_obj)))
            port_no = RdmaHelper.generate_random_port_no()
            server_obj.rdma_server_port = port_no
            client_obj.rdma_port = port_no
            client_obj.server_ip = server_obj.interface_ip
            client_obj.add_path(additional_path=PATH)
            client_obj.set_ld_library_path()
            server_obj.add_path(additional_path=PATH)
            server_obj.set_ld_library_path()
            fun_test.simple_assert(self.setup_server(test_type=test_type, server_obj=server_obj, **cmd_args),
                                   "Ensure on %s server process started" % str(server_obj))
            ibv_device = self.lat_test_template.get_ibv_device(host_obj=client_obj)
            cmd = self.create_rdma_cmd(ibv_device=ibv_device['name'], test_type=test_type,
                                       port_num=client_obj.rdma_port, client_cmd=True, server_ip=client_obj.server_ip,
                                       **cmd_args)
            tmp_output_file = "/tmp/%s_client_process_%d.log" % (test_type, server_obj.rdma_server_port)
            process_id = client_obj.start_bg_process(command=cmd, output_file=tmp_output_file, nohup=True)
            fun_test.log('Client Process Started: %s' % process_id)
            fun_test.sleep(message="Client cmd running infinitely", seconds=self.duration)
            client_obj.kill_process(process_id=process_id, signal=9)
            server_obj.kill_process(process_id=server_obj.rdma_process_id, signal=9)
            output = client_obj.read_file(file_name=tmp_output_file, include_last_line=True)
            result_dict = self.lat_test_template._parse_rdma_output(output=output)
            result_dict.update({'test_type': test_type})
            result_dict.update({'client': str(client_obj)})
            result_dict.update({'server': str(server_obj)})
        except Exception as ex:
            fun_test.critical(str(ex))
        return result_dict

    def create_table(self, records):
        try:
            table_obj1 = None
            table_obj2 = None
            lat_columns = None
            bw_columns = None
            for record in records:
                if record['test_type'] == self.lat_test_template.test_type:
                    lat_columns = record.keys()
                    table_obj1 = PrettyTable(lat_columns)
                else:
                    bw_columns = record.keys()
                    table_obj2 = PrettyTable(bw_columns)
                if table_obj1 and table_obj2:
                    break
            lat_rows = []
            bw_rows = []
            for record in records:
                if record['test_type'] == self.lat_test_template.test_type:
                    table_obj1.add_row(record.values())
                    lat_rows.append(record.values())
                else:
                    table_obj2.add_row(record.values())
                    bw_rows.append(record.values())

            fun_test.log_section("Result table for Latency Under Load Test")
            fun_test.log_disable_timestamps()
            fun_test.log("\n")
            fun_test.log(table_obj1)
            fun_test.log("\n")
            fun_test.log(table_obj2)
            fun_test.log_enable_timestamps()

            headers = lat_columns
            table_name = "Latency Result table for Latency Under Load Test"
            table_data = {'headers': headers, 'rows': lat_rows}
            fun_test.add_table(panel_header='RDMA Test Result Table (Latency)',
                               table_name=table_name, table_data=table_data)

            headers = bw_columns
            table_name = "BW Result table for Latency Under Load Test"
            table_data = {'headers': headers, 'rows': bw_rows}
            fun_test.add_table(panel_header='RDMA Test Result Table (BW)',
                               table_name=table_name, table_data=table_data)
        except Exception as ex:
            fun_test.critical(str(ex))
        return True

    def cleanup(self):
        try:
            for c_s_dict in self.bw_client_server_objs:
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
    SCENARIO_TYPE_LATENCY_UNDER_LOAD = 'lat_under_load'
    SCENARIO_TYPE_ABBA_LATENCY_UNDER_LOAD = 'abba_under_load'
    CONFIG_JSON = SCRIPTS_DIR + "/networking/rdma/config_abba.json"
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
                                client_server_map[client['host_ip']] = server['host_ip']
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

    def get_combined_log(self):
        result = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    result = self.config[key]['combined_log']
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_traffic_size_in_bytes(self, key_name='size_in_bytes'):
        size = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if key_name in self.config[key]:
                        size = self.config[key][key_name]
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return size

    def get_traffic_duration_in_secs(self):
        duration_in_secs = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'duration_in_secs' in self.config[key]:
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

    def get_run_infinitely(self):
        run_infinitely = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'run_infinitely' in self.config[key]:
                        run_infinitely = self.config[key]['run_infinitely']
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return run_infinitely

    def get_iterations(self):
        iterations = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'iterations' in self.config[key]:
                        iterations = self.config[key]['iterations']
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return iterations

    def get_qpairs(self):
        qpairs = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'qpairs' in self.config[key]:
                        iterations = self.config[key]['qpairs']
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return qpairs

    def get_rate_limit(self):
        rate_limit = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'rate_limit' in self.config[key]:
                        rate_limit = self.config[key]['rate_limit']
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return rate_limit

    def get_rate_units(self):
        rate_units = None
        try:
            for key in self.config:
                if key == self.scenario_type:
                    if 'rate_units' in self.config[key]:
                        rate_units = self.config[key]['rate_units']
                        break
        except Exception as ex:
            fun_test.critical(str(ex))
        return rate_units

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
            if self.scenario_type == self.SCENARIO_TYPE_N_N or \
                    self.scenario_type == self.SCENARIO_TYPE_ABBA_LATENCY_UNDER_LOAD:
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

    def create_lat_under_load_topology(self):
        result = {'bw': [], 'lat': []}
        try:
            for key in self.config:
                if key == self.SCENARIO_TYPE_LATENCY_UNDER_LOAD and self.scenario_type == "lat_under_load":
                    lat_test_map = self.get_client_server_map()
                    bw_test_map = {}
                    clients = self.get_list_of_clients()
                    servers = self.get_list_of_servers()
                    for client in clients:
                        for server in servers:
                            bw_test_map[client['host_ip']] = server['host_ip']

                    result['bw'].extend(self._get_lat_under_test_map_objects(test_map=bw_test_map))
                    result['lat'].extend(self._get_lat_under_test_map_objects(test_map=lat_test_map))
                    for map_obj in result['bw']:
                        self.host_objs.extend(map_obj.keys())
                    self.host_objs.append(result['bw'][0].values()[0])
                if key == self.SCENARIO_TYPE_ABBA_LATENCY_UNDER_LOAD and self.scenario_type == "abba_under_load":
                    lat_test_map = {}
                    bw_test_map = self.create_client_server_map_full_mesh()
                    lat_test_map = bw_test_map
                    result['bw'].extend(bw_test_map)
                    result['lat'].extend(lat_test_map)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _get_lat_under_test_map_objects(self, test_map):
        result = []
        try:
            client_id = 1
            server_id = 1
            for client, server in test_map.items():
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
                client_id += 1
                server_id += 1
        except Exception as ex:
            fun_test.critical(str(ex))
        return result
