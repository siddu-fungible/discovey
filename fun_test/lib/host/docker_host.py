from lib.system.fun_test import fun_test, FunTimer, FunTestLibException
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
from docker.errors import APIError
from docker import DockerClient
from docker.types.services import Mount
import re, collections
from fun_settings import DEFAULT_BUILD_URL
from urllib3.connection import ConnectionError
# fun_test.enable_debug()


class PortAllocator:
    def __init__(self, base_port, internal_ports, allocated_ports):
        self.internal_ports = internal_ports if internal_ports else []
        self.allocated_ports = [base_port]
        self.allocated_ports.extend(allocated_ports)
        i = 0

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

    TYPE_DESKTOP = "TYPE_DESKTOP"
    TYPE_BARE_METAL = "TYPE_BARE_METAL"

    STORAGE_IMAGE_NAME = "integration_jenkins_fetch"

    DOCKER_STATUS_RUNNING = "running"
    def __init__(self,
                 properties):
        super(DockerHost, self).__init__(host_ip=properties["host_ip"],
                                         ssh_username=properties["mgmt_ssh_username"],
                                         ssh_password=properties["mgmt_ssh_password"],
                                         ssh_port=properties["mgmt_ssh_port"])
        self.remote_api_port = properties["remote_api_port"]
        self.localhost = None
        if "localhost" in properties:
            self.localhost = properties["localhost"]
        self.type = properties["type"]  # DESKTOP, BARE_METAL
        self.spec = properties
        self.TO_DICT_VARS.extend(["containers_assets"])
        self.pool0_allocated_ports = []
        self.pool1_allocated_ports = []
        self.pool2_allocated_ports = []

    def health(self):
        fun_test.log("Determining Health of Docker Host: {}".format(self.name))
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
        fun_test.log("Health: {}".format("OK" if health_result["result"] else "FAILED"))
        return health_result

    def wait_for_handoff(self, container_name, handoff_string, max_time=180):
        result = False
        timer = FunTimer(max_time=max_time)
        while not timer.is_expired():
            output = self.command(command="docker logs {}".format(container_name), include_last_line=True)
            if re.search(handoff_string, output):
                result = True
                break
            fun_test.sleep("Waiting for container handoff string", seconds=2)
        return result

    def get_images(self):
        images = []
        try:
            self.connect()
            for x in self.client.images.list(all=True):
                if x.tags:
                    images.extend(x.tags)

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
            docker_url = fun_test.get_environment_variable("DOCKER_URL")
            url = 'tcp://{}:{}'.format(self.host_ip, self.remote_api_port)
            if docker_url:
                url = docker_url
            self.client = DockerClient(base_url=url, timeout=15)
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

    def _get_image_name_by_category(self, category_name):
        images = self.spec["images"]
        images = [x["name"] for x in images if str(x["category"]) == category_name]
        return images[0]

    '''
    @fun_test.safe
    def setup_storage_container(self,
                               container_name,
                               build_url,
                               ssh_internal_ports,
                               qemu_internal_ports,
                               dpcsh_internal_ports,
                               funos_command=None,
                               dpc_server=False,
                               pre_dpcsh_sleep=None,
                               dpcsh_directory=None,
                               mounts=None,
                               ):
        storage_image_name = self._get_image_name_by_category(category_name="storage_basic")  #TODO
        if build_url:
            build_url += "/Linux"
        command = build_url
        if not build_url:
            command = "None"
        if funos_command:
            command += " {}".format(funos_command)
            if dpc_server:
                command += " True"
            if pre_dpcsh_sleep:
                command += " {}".format(pre_dpcsh_sleep)
            if dpcsh_directory:
                command += " {}".format(dpcsh_directory)
        return self.setup_container(image_name=storage_image_name,
                                    container_name=container_name,
                                    pool0_internal_ports=ssh_internal_ports,
                                    pool1_internal_ports=qemu_internal_ports,
                                    pool2_internal_ports=dpcsh_internal_ports,
                                    command=command, mounts=mounts)
        
    '''

    @fun_test.safe
    def setup_storage_container(self,
                                container_name,
                                ssh_internal_ports,
                                qemu_internal_ports,
                                dpcsh_internal_ports,
                                mounts=None):
        storage_image_name = self._get_image_name_by_category(category_name="storage_basic")  # TODO
        sdk_url = DEFAULT_BUILD_URL + "/Linux" if not fun_test.build_url else fun_test.build_url + "/Linux"
        local_sdk_url = fun_test.get_local_setting("SDK_URL")
        local_dpcsh_url = fun_test.get_local_setting("DPCSH_TGZ_URL")
        local_funos_tgz_url = fun_test.get_local_setting("FUNOS_TGZ_URL")
        local_qemu_tgz_url = fun_test.get_local_setting("QEMU_TGZ_URL")
        local_modules_tgz_url = fun_test.get_local_setting("MODULES_TGZ_URL")
        local_functrlp_tgz_url = fun_test.get_local_setting("FUNCTRLP_TGZ_URL")
        local_dochub_ip = fun_test.get_local_setting("DOCHUB_IP")

        sdk_url = sdk_url or local_sdk_url
        command = " -s {}".format(sdk_url)
        if local_dpcsh_url:
            command += " -d {}".format(local_dpcsh_url)
        if local_funos_tgz_url:
            command += " -f {}".format(local_funos_tgz_url)
        if local_qemu_tgz_url:
            command += " -q {}".format(local_qemu_tgz_url)
        if local_modules_tgz_url:
            command += " -m {}".format(local_modules_tgz_url)
        if local_functrlp_tgz_url:
            command += " -c {}".format(local_functrlp_tgz_url)
        if local_dochub_ip:
            command += " -h {}".format(local_dochub_ip)

        return self.setup_container(image_name=storage_image_name,
                                    container_name=container_name,
                                    pool0_internal_ports=ssh_internal_ports,
                                    pool1_internal_ports=qemu_internal_ports,
                                    pool2_internal_ports=dpcsh_internal_ports,
                                    command=command, mounts=mounts)

    def describe_storage_container(self, container_asset):
        fun_test.log_section("Container: {}".format(container_asset["name"]))
        fun_test.log("External Ip: {}".format(container_asset["host_ip"]), no_timestamp=True)
        fun_test.log("External Ssh Port: {}".format(container_asset["mgmt_ssh_port"]), no_timestamp=True)
        fun_test.log("Ssh Username: {}".format(container_asset["mgmt_ssh_username"]), no_timestamp=True)
        fun_test.log("Ssh Password: {}".format(container_asset["mgmt_ssh_password"]), no_timestamp=True)
        fun_test.log("Internal Ip: {}".format(container_asset["internal_ip"]), no_timestamp=True)
        fun_test.log("External Dpcsh port: {}".format(container_asset["pool2_ports"][0]["external"]), no_timestamp=True)
        fun_test.log("Internal Dpcsh port: {}".format(container_asset["pool2_ports"][0]["internal"]), no_timestamp=True)

        fun_test.log("Qemu Ports:", no_timestamp=True)
        for port_info in container_asset["pool1_ports"]:
            fun_test.log("External: {}, Internal: {}".format(port_info["external"], port_info["internal"]),
                         no_timestamp=True)


    @fun_test.safe
    def setup_fio_container(self,
                            container_name,
                            ssh_internal_ports):
        fio_image_name = self._get_image_name_by_category(category_name="fio_traffic_generator")
        return self.setup_container(image_name=fio_image_name,
                                    container_name=container_name,
                                    pool0_internal_ports=ssh_internal_ports)

    @fun_test.safe
    def setup_linux_container(self,
                            container_name,
                            ssh_internal_ports):
        linux_image_name = self._get_image_name_by_category(category_name="linux_traffic_generator")
        return self.setup_container(image_name=linux_image_name,
                                    container_name=container_name,
                                    pool0_internal_ports=ssh_internal_ports)

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
    def destroy_container(self, container_name, ignore_error=False):
        container = self.get_container_by_name(name=container_name)
        if container:

            try:
                container.stop()
                fun_test.debug("Stopped Container: {}".format(container.name))
            except Exception as ex:
                if not ignore_error:
                    fun_test.critical(str(ex))

            try:
                container.remove(force=True)
                fun_test.debug("Removed Container: {}".format(container.name))
            except Exception as ex:
                if not ignore_error:
                    fun_test.critical(str(ex))

    def get_container_asset(self, name):
        result = {}
        if name in self.containers_assets:
            result = self.containers_assets[name]
        return result

    @fun_test.safe
    def setup_container(self,
                        image_name,
                        container_name,
                        command=None,
                        pool0_internal_ports=None,
                        pool1_internal_ports=None,
                        pool2_internal_ports=None,
                        mounts=None,
                        environment_variables=None,
                        host_name=None,
                        user=None,
                        working_dir=None,
                        auto_remove=None,
                        read_only=False):
        container_asset = {}
        allocated_container = None

        self.connect()   #TODO validate connect

        ports_dict = collections.OrderedDict()

        port_retries = 0
        max_port_retries = 100

        port_allocator0 = PortAllocator(base_port=self.BASE_CONTAINER_SSH_PORT,
                                        internal_ports=pool0_internal_ports,
                                        allocated_ports=self.pool0_allocated_ports)
        port_allocator1 = PortAllocator(base_port=self.BASE_POOL1_PORT,
                                        internal_ports=pool1_internal_ports,
                                        allocated_ports=self.pool1_allocated_ports)
        port_allocator2 = PortAllocator(base_port=self.BASE_POOL2_PORT,
                                        internal_ports=pool2_internal_ports,
                                        allocated_ports=self.pool2_allocated_ports)

        while port_retries < max_port_retries:
            fun_test.log("Current Try: {}, Max Tries: {}".format(port_retries, max_port_retries))
            self.pool0_allocated_ports = port_allocator0.allocated_ports
            self.pool1_allocated_ports = port_allocator1.allocated_ports
            self.pool2_allocated_ports = port_allocator2.allocated_ports
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


                pool0_allocation = port_allocator0.prepare_ports_dict(ports_dict=ports_dict)
                pool1_allocation = port_allocator1.prepare_ports_dict(ports_dict=ports_dict)
                pool2_allocation = port_allocator2.prepare_ports_dict(ports_dict=ports_dict)


                mount_objects = []
                if mounts:
                    for mount_string in mounts:
                        if mount_string:
                            parts = mount_string.split(":")
                            one_mount = Mount(target=parts[1], source=parts[0], type="bind", read_only=read_only)
                            mount_objects.append(one_mount)
                if command:
                    allocated_container = self.client.containers.run(image_name,
                                                                     command=command,
                                                                     detach=True,
                                                                     privileged=True,
                                                                     ports=ports_dict,
                                                                     name=container_name,
                                                                     mounts=mount_objects,
                                                                     environment=environment_variables,
                                                                     hostname=host_name,
                                                                     user=user,
                                                                     working_dir=working_dir,
                                                                     auto_remove=auto_remove)
                else:
                    allocated_container = self.client.containers.run(image_name,
                                                                     detach=True,
                                                                     privileged=True,
                                                                     ports=ports_dict,
                                                                     name=container_name,
                                                                     mounts=mount_objects,
                                                                     environment=environment_variables,
                                                                     hostname=host_name,
                                                                     user=user,
                                                                     working_dir=working_dir,
                                                                     auto_remove=auto_remove)
                fun_test.simple_assert(self.ensure_container_running(container_name=container_name,
                                                                     max_wait_time=self.CONTAINER_START_UP_TIME_DEFAULT),
                                       "Ensure container is started")
                fun_test.sleep("Really Ensuring container is started", seconds=15)
                if fun_test.local_settings and "CONTAINER_START_TIME" in fun_test.local_settings:
                    fun_test.sleep("Additional sleep for {}".format(self.type), seconds=fun_test.local_settings["CONTAINER_START_TIME"])
                elif self.type == self.TYPE_DESKTOP:
                    fun_test.sleep("Additional sleep for {}".format(self.type), seconds=15)
                if not self.localhost:
                    self.sudo_command("docker logs {}".format(container_name))
                fun_test.simple_assert(self.ensure_container_running(container_name=container_name,
                                                                     max_wait_time=self.CONTAINER_START_UP_TIME_DEFAULT),
                                       "Ensure container is started")

                allocated_container = self.client.containers.get(container_name)
                internal_ip = allocated_container.attrs["NetworkSettings"]["IPAddress"]


                fun_test.log("Launched container: {}".format(container_name))
                if not self.localhost:
                    self.sudo_command("docker logs {}".format(container_name))

                port_retries += 1
                container_asset = {"host_ip": self.host_ip}
                container_asset["mgmt_ssh_username"] = user if user else self.SSH_USERNAME
                container_asset["mgmt_ssh_password"] = self.SSH_PASSWORD
                container_asset["mgmt_ssh_port"] = pool0_allocation[0]["external"]
                container_asset["pool1_ports"] = pool1_allocation
                container_asset["pool2_ports"] = pool2_allocation
                container_asset["internal_ip"] = internal_ip
                container_asset["name"] = container_name
                self.containers_assets[container_name] = container_asset
                self.pool0_allocated_ports = port_allocator0.allocated_ports
                self.pool1_allocated_ports = port_allocator1.allocated_ports
                self.pool2_allocated_ports = port_allocator2.allocated_ports
                break
            except APIError as ex:
                message = str(ex)
                fun_test.log("Container creation error: {}". format(message))
                self.destroy_container(container_name=container_name)
                port_allocator0.de_allocate_ports([x["external"] for x in pool0_allocation])
                port_allocator1.de_allocate_ports([x["external"] for x in pool1_allocation])
                port_allocator2.de_allocate_ports([x["external"] for x in pool2_allocation])
                m = re.search("(\d+)\s+failed:\s+port\s+is\s+already", message)
                if m:
                    used_up_port = int(m.group(1))
                    if used_up_port in [x["external"] for x in pool0_allocation]:
                        port_allocator0.allocate_port(used_up_port)
                    if used_up_port in [x["external"] for x in pool1_allocation]:
                        port_allocator1.allocate_port(used_up_port)
                    if used_up_port in [x["external"] for x in pool2_allocation]:
                        port_allocator2.allocate_port(used_up_port)

                port_retries += 1
                if port_retries >= max_port_retries:
                    raise FunTestLibException("Unable to bind to any port, max_retries: {} reached".format(max_port_retries))
                else:
                    fun_test.log("Retrying with different ports...")
            except Exception as ex:
                if (hasattr(ex, "message") and "Max retries" in str(ex.message)):
                    fun_test.log("Unable to reach the Docker remote API")
                    port_retries = max_port_retries
                port_retries += 1
                fun_test.critical(ex)
                self.destroy_container(container_name=container_name)
                if allocated_container:
                    if not self.localhost:
                        self.sudo_command("docker logs {}".format(container_name))
                    logs = allocated_container.logs(stdout=True, stderr=True)
                    fun_test.log("Docker logs:\n {}".format(logs))
                    break
                else:
                    if not self.localhost:
                        self.sudo_command("docker logs {}".format(container_name))

        return container_asset

    def ensure_container_running(self, container_name, max_wait_time=120):
        result = None
        timer = FunTimer(max_time=max_wait_time)
        while not timer.is_expired():
            container = self.client.containers.get(container_name)
            if container.status == self.DOCKER_STATUS_RUNNING:
                result = True
                break
            fun_test.sleep(seconds=5, message="Re-checking the container status")
        if timer.is_expired():
            fun_test.critical("Timer expired waiting for container to run")
        return result

    def ensure_container_idling(self, container_name, max_wait_time=180, idle_marker="Idling"):
        timer = FunTimer(max_time=180)
        container_up = False
        try:
            while not timer.is_expired():
                output = self.command(command="docker logs {}".format(container_name), include_last_line=True)
                if re.search(idle_marker, output):
                    container_up = True
                    break
                fun_test.sleep("Waiting for container to come up", seconds=10)
        except Exception as ex:
            fun_test.critical(str(ex))
        return container_up

    @staticmethod
    def get(asset_properties):
        """

        :rtype: object
        """
        return DockerHost(properties=asset_properties)

if __name__ == "__main2__":
    # funos_url = "http://172.17.0.1:8080/fs/funos-posix"
    import asset.asset_manager
    dm = asset.asset_manager.AssetManager().get_any_docker_host()
    print dm.health()

