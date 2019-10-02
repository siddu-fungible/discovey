from lib.system.fun_test import FunTestLibException, fun_test
from requests import *
from requests.auth import HTTPBasicAuth


class StorageControllerApi(object):
    def __init__(self, api_server_ip, api_server_port=50220, username="admin", password="password"):
        self.username = username
        self.password = password
        self.base_url = "http://{}:{}/FunCC/v1".format(api_server_ip, api_server_port)
        self.storage_base_url = "{}/storage".format(self.base_url)
        self.http_basic_auth = HTTPBasicAuth(self.username, self.password)
        self.pool_url = "{}/{}".format(self.storage_base_url, "pools")
        self.volume_url = "{}/{}".format(self.storage_base_url, "volumes")

    def get_auth_token(self):
        auth_url = "{}/user/token".format(self.base_url)
        data = {"username": self.username, "password": self.password}
        print "Data to be passed:\n{}".format(data)
        response = request("post", auth_url, data=data)
        print response
        print "Response Object \n{}".format(dir(response))

    def get_dpu_ids(self):
        result = []
        url = "{}/topology".format(self.base_url)
        response = request("get", url, auth=self.http_basic_auth)
        if response.ok:
            json_response = response.json()
            # Looping around all the FSs and its properties in the current topology
            for fs_id, fs_props in json_response["data"].iteritems():
                # Checking whether the current FS is having DPUs details
                if "dpus" in fs_props:
                    # Extracting the DPU IDs alone from the list of DPUs from the current FS
                    for dpu in fs_props["dpus"]:
                        if "uuid" in dpu:
                            result.append(dpu["uuid"])
                        else:
                            fun_test.critical("No DPU found in the current FS")
                else:
                    fun_test.critical("No DPUs found in the current topology")

        # Sort the DPUs and DPU IDs before returning
        if result:
            result.sort(key=lambda key: (int(key.split('.')[0][2:]), int(key.split('.')[1])))
        return result

    def configure_dataplane_ip(self, interface_name, ip, subnet_mask, next_hop, use_dhcp=False, dpu_id="FS1.0"):
        result = {"status": False, "data": {}}
        url = "{}/topology/dpus/{}".format(self.base_url, dpu_id)
        data = {"op": "DPU_DP_IP", "node_id": dpu_id, "ip_assignment_dhcp": use_dhcp, "dataplane_ip": ip,
                "subnet_mask": subnet_mask, "next_hop": next_hop}
        response = request("patch", url, auth=self.http_basic_auth, json=data)
        if response.status_code == 200:
            result = response.json()
        return result

    def get_pools(self):
        response = request('get', self.pool_url, auth=self.http_basic_auth)
        if response.status_code != 200:
            response = {"status": False, "data": None}
        return response.json()["status"], response.json()["data"]

    def get_pool_by_uuid(self, pool_uuid):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = request('get', url)
        return response

    def create_pool(self, param=None):
        response = request('post', self.pool_url, auth=self.http_basic_auth, data=param)
        return response

    def update_pool(self, pool_uuid, param=None):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = request('put', url, auth=self.http_basic_auth, data=param)
        return response

    def delete_pool(self, pool_uuid=None):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = request('delete', url, auth=self.http_basic_auth, data=pool_uuid)
        return response

    def create_volume(self, pool_uuid, name, capacity, stripe_count, vol_type, encrypt=False, allow_expansion=False,
                      data_protection={}, compression_effort=0):
        url = "{}/pools/{}/volumes".format(self.volume_url, pool_uuid)
        data = {"name": name,  "capacity": capacity,  "vol_type": vol_type,
                "encrypt": encrypt, "allow_expansion": allow_expansion, "stripe_count": stripe_count,
                "data_protection": data_protection, "compression_effort": compression_effort}
        response = request('post', url, auth=self.http_basic_auth, data=data)
        return response

    def attach_volume(self, vol_uuid, remote_ip="", transport="TCP"):
        url = "{}/{}/ports".format(self.volume_url, vol_uuid)
        data = {"remote_ip": remote_ip, "transport": transport}
        response = request('post', url, auth=self.http_basic_auth, data=data)
        return response

    def detach_volume(self, port_uuid):
        url = "{}/ports/{}".format(self.storage_base_url, port_uuid)
        response = request('delete', url)
        return response

    def delete_volume(self, vol_uuid):
        # Delete API doesn't accept pool id; so not using it
        url = "{}/volumes/{}".format(self.volume_url, vol_uuid)
        response = request('delete', url, auth=self.http_basic_auth)
        return response