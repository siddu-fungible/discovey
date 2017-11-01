from lib.system.fun_test import fun_test, FunTimer, FunTestLibException
from lib.system.utils import ToDictMixin
from fun_settings import *
from lib.host.linux import Linux
from docker.errors import APIError
from docker import DockerClient
import re, collections

# fun_test.enable_debug()


class DockerHost(Linux, ToDictMixin):

    BASE_CONTAINER_SSH_PORT = 3219
    BASE_QEMU_SSH_PORT = 2219
    BASE_DPCSH_PORT = 40219
    CONTAINER_START_UP_TIME_DEFAULT = 30

    CONTAINER_INTERNAL_SSH_PORT = 22

    DOCKER_STATUS_RUNNING = "running"
    def __init__(self,
                 properties):
        super(DockerHost, self).__init__(host_ip=properties["host_ip"],
                                         ssh_username=properties["mgmt_ssh_username"],
                                         ssh_password=properties["mgmt_ssh_password"],
                                         ssh_port=properties["mgmt_ssh_port"])
        self.remote_api_port = properties["remote_api_port"]
        self.spec = properties
        self.TO_DICT_VARS.extend(["allocated_container_ssh_ports",
                                  "allocated_qemu_ssh_ports",
                                  "allocated_qemu_dpcsh_ports",
                                  "containers_assets"])

    def health(self):
        fun_test.debug("Health of {}".format(self.name))
        health_result = {"result": False,
                         "error_message": None}
        images = self.get_images()
        expected_images = [x["name"] for x in self.spec["images"]]
        for expected_image in expected_images:
            if not expected_image in images:
                error_message = "Health: Unable to find image: {} in docker host: {}".format(expected_image,
                               self.host_ip)
                fun_test.critical(error_message)
                health_result["result"] = False
                health_result["error_message"] = error_message
                break
            else:
                health_result["result"] = True

        return health_result

    def get_images(self):
        images = []
        try:
            self.connect()
            images = [y[0].split(":")[0] for y in [x.tags for x in self.client.images.list(all=True)] if y]
        except Exception as ex:
            print ("get_images:" + str(ex))  #TODO: we use print as non fun-test code can access this
        return images

    def describe(self):
        fun_test.log_section("DockerHost Info: {}".format(self.host_ip))
        fun_test.log("Container Info")
        for container_name, container_asset in self.containers_assets.items():
            fun_test.print_key_value(title="Container Asset {}".format(container_name), data=container_asset)
            table_data_headers = ["Attribute", "Value"]
            table_data_rows = []
            for key, value in container_asset.items():
                table_data_rows.append([str(key), str(value)])
            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Docker Host Info",
                               table_name=container_name, table_data=table_data)

    def post_init(self):
        self.name = "DockerHost: {}".format(self.host_ip)
        self.containers_assets = collections.OrderedDict()
        self.client = None
        self.current_docker_host_asset = None
        self.allocated_container_ssh_ports = [self.BASE_CONTAINER_SSH_PORT]
        self.allocated_qemu_ssh_ports = [self.BASE_QEMU_SSH_PORT]
        self.allocated_dpcsh_ports = [self.BASE_DPCSH_PORT]

    @fun_test.safe
    def get_container_asset_by_internal_ip(self, internal_ip):
        result = None
        for container_name, container_asset in self.containers_assets.items():
            if internal_ip == container_asset["internal_ip"]:
                result = container_asset
                break
        return result

    def connect(self):
        if not self.client:
            self.client = DockerClient(base_url='tcp://{}:{}'.format(self.host_ip, self.remote_api_port))
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
        self.allocated_container_ssh_ports.append(port)
        self.allocated_container_ssh_ports = sorted(list(set(self.allocated_container_ssh_ports)))


    def allocate_qemu_ssh_port(self, port, internal_ip=None): #If called from outside this class, pass internal_ip as container_names are not known outside
        self.allocated_qemu_ssh_ports.append(port)
        self.allocated_qemu_ssh_ports = sorted(list(set(self.allocated_qemu_ssh_ports)))  #TODO Expensive

        if internal_ip:
            container_asset = self.get_container_asset_by_internal_ip(internal_ip=internal_ip)
            container_asset["qemu_ssh_ports"].append(port)

    def allocate_dpcsh_port(self, port):
        self.allocated_dpcsh_ports.append(port)
        self.allocated_dpcsh_ports = sorted(list(set(self.allocated_dpcsh_ports)))

    def get_next_container_ssh_port(self):
        next_port = self._get_next_port(source=self.allocated_container_ssh_ports)
        # self.allocate_container_ssh_port(port=next_port)
        return next_port

    def get_next_qemu_ssh_port(self):
        next_port = self._get_next_port(source=self.allocated_qemu_ssh_ports)
        # self.allocate_qemu_ssh_port(port=next_port)
        return next_port

    def get_next_dpcsh_port(self):
        next_port = self._get_next_port(source=self.allocated_dpcsh_ports)
        return next_port

    def _get_next_port(self, source):
        """Given a list of ports, finds and returns the first gap
        in the list. If there are no gaps, just return a new port from the tail
        """
        l = source
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
    def setup_integration_basic_container(self,
                                          image_name,
                                          base_name,
                                          id,
                                          funos_url,
                                          qemu_port_redirects,
                                          internal_dpcsh_port):
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

                ports_dict[str(self.CONTAINER_INTERNAL_SSH_PORT)] = str(container_ssh_port)

                '''
                qemu_ssh_ports = []
                for qemu_port_redirect in qemu_port_redirects:
                    qemu_ssh_port = self.get_next_qemu_ssh_port()
                    qemu_ssh_ports.append(qemu_ssh_port)
                    ports_dict[str(qemu_port_redirect)] = qemu_ssh_port
                    fun_test.debug("Container SSH port: {}".format(qemu_ssh_port))
                '''

                dpcsh_port = self.get_next_dpcsh_port()
                ports_dict[str(internal_dpcsh_port)] = dpcsh_port
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
                # map(lambda x: self.allocate_qemu_ssh_port(x), qemu_ssh_ports)
                fun_test.log("Launched container: {}".format(container_name))

                port_retries += 1
                container_asset = {"host_ip": self.host_ip}
                container_asset["mgmt_ssh_username"] = "root"
                container_asset["mgmt_ssh_password"] = "fun123"
                container_asset["mgmt_ssh_port"] = container_ssh_port
                container_asset["qemu_ssh_ports"] = []
                container_asset["internal_ip"] = allocated_container.attrs["NetworkSettings"]["IPAddress"]
                container_asset["dpcsh_port"] = dpcsh_port
                container_asset["name"] = container_name
                self.containers_assets[container_name] = container_asset
                break
            except APIError as ex:
                message = str(ex)
                fun_test.critical("Container creation error: {}". format(message))
                m = re.search("(\d+)\s+failed:\s+port\s+is\s+already", message)
                if m:
                    used_up_port = int(m.group(1))
                    self.allocate_qemu_ssh_port(used_up_port)
                    self.allocate_container_ssh_port(used_up_port)
                    self.allocate_dpcsh_port(used_up_port)

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
        return DockerHost(properties=asset_properties)

if __name__ == "__main__":
    funos_url = "http://172.17.0.1:8080/fs/funos-posix"
    import asset.asset_manager
    dm = asset.asset_manager.AssetManager().get_any_docker_host()
    print dm.health()
    #i = dm.setup_integration_basic_container(base_name="integration_john", id=0, funos_url=funos_url, qemu_port_redirects=[2220])
    #i = dm.setup_integration_basic_container(base_name="integration_john", id=1, funos_url=funos_url, qemu_port_redirects=[2220])
    #i = dm.setup_integration_basic_container(base_name="integration_john", id=2, funos_url=funos_url, qemu_port_redirects=[2220])
