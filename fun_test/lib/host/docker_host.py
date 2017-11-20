from lib.system.fun_test import fun_test, FunTimer, FunTestLibException
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from docker.errors import APIError
from docker import DockerClient
import re, collections

# fun_test.enable_debug()


class PortAllocator:
    def __init__(self, base_port, internal_ports):
        self.internal_ports = internal_ports
        self.allocated_ports = [base_port]

    def prepare_ports_dict(self, ports_dict):
        allocation = []
        for index in range(len(self.internal_ports)):
            internal_port = self.internal_ports[index]
            external_port = self.get_next_port()
            self.allocate_port(port=external_port)
            ports_dict[str(internal_port)] = str(external_port)
            fun_test.debug("Container Port: {}".format(external_port))
            allocation.append({"internal": internal_port, "external": external_port})
        return allocation

    def allocate_port(self, port):
        fun_test.debug("Allocating port {}".format(port))
        self.allocated_ports.append(port)
        self.allocated_ports = sorted(list(set(self.allocated_ports))) #TODO Expensive

    def get_next_port(self):
        next_port = self._get_next_port(source=self.allocated_ports)
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

    def de_allocate_ports(self, ports):
        map(lambda x: self.allocated_ports.remove(x), ports)


class DockerHost(Linux, ToDictMixin):

    BASE_CONTAINER_SSH_PORT = 3219
    BASE_POOL1_PORT = 2219
    BASE_POOL2_PORT = 40219
    CONTAINER_START_UP_TIME_DEFAULT = 30

    SSH_USERNAME = "root"
    SSH_PASSWORD = "fun123"

    STORAGE_IMAGE_NAME = "integration_jenkins_fetch"


    DOCKER_STATUS_RUNNING = "running"
    def __init__(self,
                 properties):
        super(DockerHost, self).__init__(host_ip=properties["host_ip"],
                                         ssh_username=properties["mgmt_ssh_username"],
                                         ssh_password=properties["mgmt_ssh_password"],
                                         ssh_port=properties["mgmt_ssh_port"])
        self.remote_api_port = properties["remote_api_port"]
        self.spec = properties
        self.TO_DICT_VARS.extend(["containers_assets"])

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
    def setup_storage_container(self,
                               container_name,
                               build_url,
                               ssh_internal_ports,
                               qemu_internal_ports,
                               dpcsh_internal_ports):
        images = self.spec["images"]
        storage_image_names = [x["name"] for x in images if x["category"] == "storage_basic"]  #TODO
        return self.setup_container(image_name=storage_image_names[0],
                                    container_name=container_name,
                                    pool0_internal_ports=ssh_internal_ports,
                                    pool1_internal_ports=qemu_internal_ports,
                                    pool2_internal_ports=dpcsh_internal_ports,
                                    command=build_url)

    @fun_test.safe
    def stop_container(self, container_name, container=None):
        if container_name:
            container = self.get_container_by_name(name=container_name)
        container.stop()

    @fun_test.safe
    def remove_container(self, container_name, container=None):
        if container_name:
            container = self.get_container_by_name(name=container_name)
        container.remove()

    @fun_test.safe
    def destroy_container(self, container_name):
        container = self.get_container_by_name(name=container_name)
        if container:

            try:
                container.stop()
                fun_test.debug("Stopped Container: {}".format(container.name))
            except Exception as ex:
                fun_test.critical(str(ex))

            try:
                container.remove()
                fun_test.debug("Removed Container: {}".format(container.name))
            except Exception as ex:
                fun_test.critical(str(ex))

    @fun_test.safe
    def setup_container(self,
                        image_name,
                        container_name,
                        command,
                        pool0_internal_ports,
                        pool1_internal_ports,
                        pool2_internal_ports):
        container_asset = {}
        allocated_container = None

        self.connect()   #TODO validate connect

        ports_dict = collections.OrderedDict()

        port_retries = 0
        max_port_retries = 100

        port0_allocator = PortAllocator(base_port=self.BASE_CONTAINER_SSH_PORT,
                                        internal_ports=pool0_internal_ports)
        port1_allocator = PortAllocator(base_port=self.BASE_POOL1_PORT,
                                        internal_ports=pool1_internal_ports)
        port2_allocator = PortAllocator(base_port=self.BASE_POOL2_PORT,
                                        internal_ports=pool2_internal_ports)

        while port_retries < max_port_retries:
            container = self.get_container_by_name(name=container_name)
            if container:
                try:
                    self.stop_container(container_name=container_name)
                    fun_test.debug("Stopped Container: {}".format(container_name))
                    self.remove_container(container_name=container_name)
                    fun_test.debug("Removed Container: {}".format(container_name))
                except Exception as ex:
                    fun_test.critical(str(ex))

            if port_retries:
                fun_test.debug("Retrying container creation with a different port: port_retries: {}, max_retries: {}".format(port_retries, max_port_retries))

            try:


                pool0_allocation = port0_allocator.prepare_ports_dict(ports_dict=ports_dict)
                pool1_allocation = port1_allocator.prepare_ports_dict(ports_dict=ports_dict)
                pool2_allocation = port2_allocator.prepare_ports_dict(ports_dict=ports_dict)

                allocated_container = self.client.containers.run(image_name,
                                           command=command,
                                           detach=True,
                                           privileged=True,
                                           ports=ports_dict,
                                           name=container_name)
                fun_test.simple_assert(self.ensure_container_running(container_name=container_name,
                                                                     max_wait_time=self.CONTAINER_START_UP_TIME_DEFAULT),
                                       "Ensure container is started")
                fun_test.sleep("Really Ensuring container is started", seconds=15)
                fun_test.simple_assert(self.ensure_container_running(container_name=container_name,
                                                                     max_wait_time=self.CONTAINER_START_UP_TIME_DEFAULT),
                                       "Ensure container is started")


                allocated_container = self.client.containers.get(container_name)
                internal_ip = allocated_container.attrs["NetworkSettings"]["IPAddress"]


                fun_test.log("Launched container: {}".format(container_name))

                port_retries += 1
                container_asset = {"host_ip": self.host_ip}
                container_asset["mgmt_ssh_username"] = self.SSH_USERNAME
                container_asset["mgmt_ssh_password"] = self.SSH_PASSWORD
                container_asset["mgmt_ssh_port"] = pool0_allocation[0]["external"]
                container_asset["pool1_ports"] = pool1_allocation
                container_asset["pool2_ports"] = pool2_allocation
                container_asset["internal_ip"] = internal_ip
                container_asset["name"] = container_name
                self.containers_assets[container_name] = container_asset
                break
            except APIError as ex:
                message = str(ex)
                fun_test.critical("Container creation error: {}". format(message))
                self.destroy_container(container_name=container_name)
                port0_allocator.de_allocate_ports([x["external"] for x in pool0_allocation])
                port1_allocator.de_allocate_ports([x["external"] for x in pool1_allocation])
                port2_allocator.de_allocate_ports([x["external"] for x in pool2_allocation])
                m = re.search("(\d+)\s+failed:\s+port\s+is\s+already", message)
                if m:
                    used_up_port = int(m.group(1))
                    if used_up_port in [x["external"] for x in pool0_allocation]:
                        port0_allocator.allocate_port(used_up_port)
                    if used_up_port in [x["external"] for x in pool1_allocation]:
                        port1_allocator.allocate_port(used_up_port)
                    if used_up_port in [x["external"] for x in pool2_allocation]:
                        port2_allocator.allocate_port(used_up_port)

                port_retries += 1
                if port_retries >= max_port_retries:
                    raise FunTestLibException("Unable to bind to any port, max_retries: {} reached".format(max_port_retries))
            except Exception as ex:
                fun_test.critical(ex)
                self.destroy_container(container_name=container_name)
                if allocated_container:
                    logs = allocated_container.logs(stdout=True, stderr=True)
                    fun_test.log("Docker logs:\n {}".format(logs))
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
