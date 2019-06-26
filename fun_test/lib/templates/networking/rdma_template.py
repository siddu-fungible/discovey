from lib.system.fun_test import *
from lib.host.linux import Linux
import re

IB_WRITE_BANDWIDTH_TEST = "ib_write_bw"
IB_WRITE_LATENCY_TEST = "ib_write_lat"
LD_LIBRARY_PATH = "/home/localadmin/mks/workspace/fungible-rdma-core/build/lib"
PATH = "/home/localadmin/mks/workspace/fungible-rdma-core/build/bin/:/home/localadmin/mks/workspace/fungible-perftest/"


class RdmaClient(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password):
        super(RdmaClient, self).__init__(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        self.add_path(additional_path=PATH)
        self.set_ld_library_path()

    def set_ld_library_path(self):
        self.command(command="export %s" % LD_LIBRARY_PATH)


class RdmaServer(Linux):

    def __init__(self, host_ip, ssh_username, ssh_password, rdma_port, server_id):
        super(RdmaServer, self).__init__(host_ip=host_ip, ssh_username=ssh_username, ssh_password=ssh_password)
        self.rdma_port = rdma_port
        self.server_id = server_id
        self.rdma_process_id = None
        self.add_path(additional_path=PATH)
        self.set_ld_library_path()

    def set_ld_library_path(self):
        self.command(command="export %s" % LD_LIBRARY_PATH)


class RdmaTemplate(object):
    CONNECTION_TYPE_RC = "RC"

    def __init__(self, servers, clients, test_type, is_parallel=True):
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

    def setup_test(self):
        result = False
        try:
            hosts = self.servers + self.clients
            module_cmds = ['sudo insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko',
                           'sudo mobprobe rdma_ucm']
            for host_obj in hosts:
                fun_test.log_section("Configure %s host load all modules and export necessary paths" % str(host_obj))
                for cmd in module_cmds:
                    host_obj.command(cmd, timeout=90)
            fun_test.add_checkpoint("Setup RDMA Test")
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

    def setup_servers(self, size, duration=10, iterations=None, inline_size=64, connection_type=CONNECTION_TYPE_RC):
        result = False
        try:
            checkpoint = "Configure all servers and start the tool %s" % self.test_type
            for server_obj in self.servers:
                fun_test.log_section("Setup %s server with RDMA port %d" % (str(server_obj), server_obj.rdma_port))
                ibv_device = self.get_ibv_device(host_obj=server_obj)
                if self.test_type == IB_WRITE_BANDWIDTH_TEST:
                    cmd = "%s -c %s -R -d %s -p %d -F -s %d" % (self.test_type, connection_type,
                                                                ibv_device['name'], server_obj.rdma_port, size)
                elif self.test_type == IB_WRITE_LATENCY_TEST:
                    cmd = "%s -c %s -R -d %s -p %d -F -I %d -R -s %d" % (self.test_type, connection_type,
                                                                         ibv_device['name'], server_obj.rdma_port,
                                                                         inline_size, size)
                else:
                    # TODO: Set default test
                    cmd = None
                if iterations:
                    cmd += " -n %d" % iterations
                else:
                    cmd += " -D %d" % duration
                fun_test.log("Server cmd formed: %s " % cmd)
                tmp_output_file = "/tmp/%s_server_process_%d_%d.log" % (self.test_type, server_obj.rdma_port,
                                                                        server_obj.server_id)
                process_id = server_obj.start_bg_process(command=cmd, output_file=tmp_output_file)
                fun_test.log("Server Process Started: %s" % process_id)
                fun_test.simple_assert(process_id, "Rdma server process started")
                server_obj.rdma_process_id = process_id
            fun_test.add_checkpoint(checkpoint)
            result = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def run(self):
        result = []
        try:
            if self.is_parallel:
                pass
            else:
                for client_obj in self.clients:
                    pass
        except Exception as ex:
            fun_test.critical(str(ex))
        return result




if __name__ == '__main__':
    c1 = RdmaClient(host_ip='cab02-qa-06', ssh_password='Precious1*', ssh_username='localadmin')


