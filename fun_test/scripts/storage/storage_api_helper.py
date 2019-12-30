from lib.templates.storage.storage_controller_api import StorageControllerApi
from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
import re


class StorageApiHelper:
    def __init__(self):
        self.get_storage_controller_api_obj()
        self.get_pool_id()

    def initialise_fs(self):
        fs_name = fun_test.get_job_environment_variable("test_bed_type")
        self.fs = AssetManager().get_fs_by_name(fs_name)

    def get_storage_controller_api_obj(self):
        if not getattr(self, "fs", False):
            self.initialise_fs()
        self.sc_api = StorageControllerApi(self.fs["come"]["mgmt_ip"])

    def create_stripe_volume_and_verify(self, volume_creation_detail):
        # todo: verify volume created
        response = self.sc_api.create_stripe_volume(pool_uuid=self.pool_uuid,
                                                    **volume_creation_detail)
        return response

    def attach_volumes_to_host(self, host_volume_map):
        vol_name = host_volume_map["vol_name"]
        host_name = host_volume_map["host_name"]
        volumes = self.sc_api.get_volumes()
        required_vol = volumes[vol_name]
        vol_uuid = required_vol["uuid"]
        remote_ip = required_vol["remote_ip"]
        response = self.sc_api.volume_attach_remote(vol_uuid, remote_ip)
        return response

    def get_pool_id(self):
        response = self.sc_api.get_pools()
        fun_test.log("pools log: {}".format(response))
        self.pool_id = str(response['data'].keys()[0])
        fun_test.log("pool_id: {}".format(self.pool_id))
        return self.pool_id

    def host_handle(self, host_name):
        host_name_new = host_name.replace("-", "_")
        host_info = self.hosts_asset[host_name]
        host_handle = Linux(host_ip=host_info['host_ip'],
                            ssh_username=host_info['ssh_username'],
                            ssh_password=host_info['ssh_password'])
        setattr(self, host_name_new, host_handle)
        return host_handle

    def verify_nvme_connect(self, host_name):
        host_name_new = host_name.replace("-", "_")
        if not getattr(self, host_name_new, False):
            self.host_handle(host_name)
        nsid = host_info["data"]["nsid"]
        output_lsblk = getattr(self, host_name_new).sudo_command("nvme list")
        lines = output_lsblk.split("\n")
        for line in lines:
            match_nvme_list = re.search(r'(?P<nvme_device>/dev/nvme\w+)\s+(?P<namespace>\d+)\s+(\d+)', line)
            if match_nvme_list:
                namespace = int(match_nvme_list.group("namespace"))
                if namespace == nsid:
                    host_info["nvme"] = match_nvme_list.group("nvme_device")
                    fun_test.log("Host: {} is connected by nvme device: {}".format(host_name, host_info["nvme"]))
                    break
        verify_nvme_connect = True if "nvme" in host_info else False
        fun_test.test_assert(verify_nvme_connect, "Host: {} nvme: {} verified NVME connect".format(host_name,
                                                                                                   host_info["nvme"]
                                                                                                   ))


