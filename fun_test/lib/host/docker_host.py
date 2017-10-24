from lib.system.fun_test import fun_test, FunTimer, FunTestLibException
from fun_settings import *
from lib.host.linux import Linux
from docker.errors import APIError
from docker import DockerClient
import re, collections

# fun_test.enable_debug()


class DockerHost(Linux):

    BASE_CONTAINER_SSH_PORT = 3219
    BASE_QEMU_SSH_PORT = 2219
    CONTAINER_START_UP_TIME_DEFAULT = 30

    DOCKER_STATUS_RUNNING = "running"

    def post_init(self):
        self.client = None
        self.current_docker_host_asset = None
        self.allocated_container_ssh_ports = {self.BASE_CONTAINER_SSH_PORT}
        self.allocated_qemu_ssh_ports = {self.BASE_QEMU_SSH_PORT}

    def connect(self):
        if not self.client:
            self.client = DockerClient(base_url='tcp://{}:{}'.format(self.host_ip, DOCKER_REMOTE_API_PORT))
        return None  #TODO: validate this

    @fun_test.safe
    def get_container_by_image(self, image_name=None):
        # TODO validate client
        self.connect()
        container = self.client.containers.list(all=True, filters={"ancestor": image_name})
        return container

    @fun_test.safe
    def get_container_by_name(self, name):
        container = None
        try:
            container = self.client.containers.get(name)
        except Exception as ex:
            pass
        return container

    @fun_test.safe
    def get_integration_basic_container(self, image_name, launch=True):
        container = self.get_container_by_image(image_name=image_name)
        return container

    @fun_test.safe
    def remove_all_integration_containers(self):
        self.connect()
        # TODO

    def allocate_container_ssh_port(self, port):
        self.allocated_container_ssh_ports.add(port)
        self.allocated_container_ssh_ports = set(sorted(self.allocated_container_ssh_ports))  #TODO: Expensive


    def allocate_qemu_ssh_port(self, port):
        self.allocated_qemu_ssh_ports.add(port)
        self.allocated_qemu_ssh_ports = set(sorted(self.allocated_qemu_ssh_ports))  # TODO: Expensive

    def get_next_container_ssh_port(self):
        next_port = self._get_next_port(source=self.allocated_container_ssh_ports)
        # self.allocate_container_ssh_port(port=next_port)
        return next_port

    def get_next_qemu_ssh_port(self):
        next_port = self._get_next_port(source=self.allocated_qemu_ssh_ports)
        # self.allocate_qemu_ssh_port(port=next_port)
        return next_port

    def _get_next_port(self, source):
        l = list(source)
        next_port = l[0]
        for index in range(0, len(l) - 1):  # TODO: Upper limits
            a = l[index]
            b = l[index + 1]
            if (b - a) > 1:
                next_port = a
                break
            if index == len(l) - 2:
                next_port = b
        return next_port + 1

    @fun_test.safe
    def setup_integration_basic_container(self, image_name, base_name, id, funos_url, qemu_port_redirects):
        container_asset = {}
        allocated_container = None

        self.connect()   #TODO validate connect
        container = self.get_integration_basic_container(image_name)
        if container:
            fun_test.simple_assert(container, "Atleast one integration basic container")
            container = container[0]

        ports_dict = collections.OrderedDict()
        container_name = "{}_{}".format(base_name, id)

        port_retries = 0
        max_port_retries = 100
        while port_retries < max_port_retries:
            container = self.get_container_by_name(name=container_name)
            if container:

                try:
                    container.stop()
                    fun_test.debug("Stopped Container: {}".format(container.name))
                    container.remove()
                    fun_test.debug("Removed Container: {}".format(container.name))
                except Exception as ex:
                    fun_test.critical(str(ex))

            if port_retries:
                fun_test.debug("Retrying container creation with a different port: port_retries: {}, max_retries: {}".format(port_retries, max_port_retries))
            try:
                container_ssh_port = self.get_next_container_ssh_port()

                fun_test.debug("Container SSH port: {}".format(container_ssh_port))

                ports_dict["22"] = str(container_ssh_port)

                qemu_ssh_ports = []
                for qemu_port_redirect in qemu_port_redirects:
                    qemu_ssh_port = self.get_next_qemu_ssh_port()
                    qemu_ssh_ports.append(qemu_ssh_port)
                    ports_dict[str(qemu_port_redirect)] = qemu_ssh_port
                    fun_test.debug("Container SSH port: {}".format(qemu_ssh_port))

                allocated_container = self.client.containers.run(image_name,
                                           command=funos_url,
                                           detach=True,
                                           privileged=True,
                                           ports=ports_dict,
                                           name=container_name)
                fun_test.simple_assert(self.ensure_container_running(container_name=container_name,
                                                                     max_wait_time=self.CONTAINER_START_UP_TIME_DEFAULT),
                                       "Ensure container is started")
                allocated_container = self.client.containers.get(container_name)
                self.allocate_container_ssh_port(container_ssh_port) #TODO: allocate qemu
                map(lambda x: self.allocate_qemu_ssh_port(x), qemu_ssh_ports)
                fun_test.log("Launched container: {}".format(container_name))

                port_retries += 1
                container_asset = {"host_ip": self.host_ip}
                container_asset["mgmt_ssh_username"] = "root"
                container_asset["mgmt_ssh_password"] = "fun123"
                container_asset["mgmt_ssh_port"] = container_ssh_port
                container_asset["qemu_ssh_ports"] = qemu_ssh_ports
                container_asset["docker_host"] = self
                container_asset["internal_ip"] = allocated_container.attrs["NetworkSettings"]["IPAddress"]

                break
            except APIError as ex:
                message = str(ex)
                fun_test.critical("Container creation error: {}". format(message))
                if re.search("{}\s+failed:\s+port\s+is\s+already".format(container_ssh_port), message):
                    self.allocate_container_ssh_port(container_ssh_port)
                else:
                    m = re.search("(\d+)\s+failed:\s+port\s+is\s+already", message)
                    if m:
                        used_up_port = int(m.group(1))
                        self.allocate_qemu_ssh_port(used_up_port)
                port_retries += 1
                if port_retries >= max_port_retries:
                    raise FunTestLibException("Unable to bind to any port, max_retries: {} reached".format(max_port_retries))
            except Exception as ex:
                if allocated_container:
                    logs = allocated_container.logs(stdout=True, stderr=True)
                    fun_test.log("Docker logs:\n {}".format(logs))
                    fun_test.critical(ex)
                    break


        return container_asset

    def ensure_container_running(self, container_name, max_wait_time=60):
        result = None
        timer = FunTimer(max_time=max_wait_time)
        while not timer.is_expired():
            container = self.client.containers.get(container_name)
            if container.status == self.DOCKER_STATUS_RUNNING:
                result = True
                break
            fun_test.sleep(seconds=5, message="Re-checking the container status")
        return result


    @staticmethod
    def get(asset_properties):
        """

        :rtype: object
        """
        prop = asset_properties
        return DockerHost(host_ip=prop["host_ip"],
                     ssh_username=prop["mgmt_ssh_username"],
                     ssh_password=prop["mgmt_ssh_password"],
                     ssh_port=prop["mgmt_ssh_port"])

if __name__ == "__main__":
    funos_url = "http://172.17.0.1:8080/fs/funos-posix"
    dm = DockerHost(host_ip="10.1.20.67", ssh_username="root", ssh_password="fun123")
    i = dm.setup_integration_basic_container(base_name="integration_john", id=0, funos_url=funos_url, qemu_port_redirects=[2220])
    i = dm.setup_integration_basic_container(base_name="integration_john", id=1, funos_url=funos_url, qemu_port_redirects=[2220])
    i = dm.setup_integration_basic_container(base_name="integration_john", id=2, funos_url=funos_url, qemu_port_redirects=[2220])
