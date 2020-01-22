from lib.system.fun_test import FunTestLibException, fun_test
import requests
import json

class StorageControllerApi(object):
    def __init__(self, api_server_ip, api_server_port=50220, username="admin", password="password"):
        self.username = username
        self.password = password
        self.base_url = "http://{}:{}/FunCC/v1".format(api_server_ip, api_server_port)
        self.storage_base_url = "{}/storage".format(self.base_url)
        self.http_basic_auth = requests.auth.HTTPBasicAuth(self.username, self.password)
        self.pool_url = "{}/{}".format(self.storage_base_url, "pools")
        self.volume_url = "{}/{}".format(self.storage_base_url, "volumes")

    def execute_api(self, method, cmd_url, data=None):
        method = method.upper()
        url = '{}/{}'.format(self.base_url, cmd_url)
        response = ""
        try:
            if method == "POST":
                response = requests.post(url, auth=self.http_basic_auth, json=data)
            elif method == "GET":
                response = requests.get(url, auth=self.http_basic_auth, json=data)
            elif method == "DELETE":
                response = requests.delete(url, auth=self.http_basic_auth, json=data)
            elif method == "PATCH":
                response = requests.patch(url, auth=self.http_basic_auth, json=data)
        except Exception as ex:
            fun_test.critical("API Exception: {}".format(str(ex)))

        return response

    def get_auth_token(self):
        auth_url = "user/token"
        data = {"username": self.username, "password": self.password}
        print "Data to be passed:\n{}".format(data)
        response = self.execute_api("post", auth_url, data=data)
        print response
        print "Response Object \n{}".format(dir(response))

    def get_dpu_ids(self):
        result = []
        url = "topology"
        response = self.execute_api("GET", url)
        try:
            if response.ok:
                json_response = response.json()
                if json_response["status"]:
                    # Looping around all the FSs and its properties in the current topology
                    for fs_id, fs_props in json_response["data"].iteritems():
                        # Checking whether the current FS is having DPUs details
                        if "dpus" in fs_props:
                            # Extracting the DPU IDs alone from the list of DPUs from the current FS
                            for dpu in fs_props["dpus"]:
                                if "uuid" in dpu:
                                    result.append(dpu["uuid"])
                                    fun_test.log("DPU ID is {}".format(dpu["uuid"]))
                                else:
                                    fun_test.critical("No DPU found in the current FS")
                        else:
                            fun_test.critical("No DPUs found in the current topology")
                else:
                    fun_test.critical("{} API execution failed".format(self.base_url + "/" + url))
        except Exception as ex:
            fun_test.critical(str(ex))

        # Sort the DPUs and DPU IDs before returning
        if result:
            result.sort(key=lambda key: (int(key.split('.')[0][2:]), int(key.split('.')[1])))
        return result

    def configure_dataplane_ip(self, dpu_id, interface_name, ip, subnet_mask, next_hop, use_dhcp=False):
        result = {"status": False, "data": {}}
        url = "topology/dpus/{}".format(dpu_id)
        data = {"op": "DPU_DP_IP", "node_id": dpu_id, "ip_assignment_dhcp": use_dhcp, "dataplane_ip": ip,
                "subnet_mask": subnet_mask, "next_hop": next_hop}
        fun_test.sleep("before firing the dataplane ip config commands", 60)
        response = self.execute_api("PATCH", url, data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_pools(self):
        result = {"status": False, "data": {}}
        url = "storage/pools"
        response = self.execute_api("GET", url)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_pool_uuid_by_name(self, name="global"):
        result = ""
        response = self.get_pools()
        try:
            if response["status"]:
                for pool_uuid, attributes in response["data"].iteritems():
                    cur_name = attributes.get("name")
                    if cur_name == name:
                        result = attributes.get("uuid")
            else:
                fun_test.critical("{} API execution failed".format(self.base_url + "/storage/pools"))
        except Exception as ex:
            fun_test.critical(str(ex))

        return result

    def get_pool_by_uuid(self, pool_uuid):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = self.execute_api('get', url)
        return response

    def create_pool(self, param=None):
        response = self.execute_api('post', self.pool_url, data=param)
        return response

    def update_pool(self, pool_uuid, param=None):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = self.execute_api('put', url, data=param)
        return response

    def delete_pool(self, pool_uuid=None):
        url = "{}/{}".format(self.pool_url, pool_uuid)
        response = self.execute_api('delete', url, data=pool_uuid)
        return response

    def create_stripe_volume(self, pool_uuid, name, capacity, pvol_type, stripe_count, encrypt=False,
                             allow_expansion=False, data_protection={}, compression_effort=0):
        result = {"status": False, "data": {}}
        url = "storage/pools/{}/volumes".format(pool_uuid)
        data = {"name": name, "capacity": capacity, "vol_type": pvol_type,
                "encrypt": encrypt, "allow_expansion": allow_expansion, "stripe_count": stripe_count,
                "data_protection": data_protection, "compression_effort": compression_effort}
        response = self.execute_api("POST", url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def create_volume(self, pool_uuid, name, capacity, stripe_count, vol_type, encrypt=False, allow_expansion=False,
                      data_protection={}, compression_effort=0):
        result = {"status": False, "data": {}}
        url = "storage/pools/{}/volumes".format(pool_uuid)
        data = {"name": name,  "capacity": capacity,  "vol_type": vol_type,
                "encrypt": encrypt, "allow_expansion": allow_expansion, "stripe_count": stripe_count,
                "data_protection": data_protection, "compression_effort": compression_effort}
        response = self.execute_api('post', url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def volume_attach_remote(self, vol_uuid, remote_ip, transport="TCP"):
        result = {"status": False, "data": {}}
        url = "storage/volumes/{}/ports".format(vol_uuid)
        data = {"remote_ip": remote_ip, "transport": transport}
        response = self.execute_api("POST", url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def volume_attach_pcie(self, vol_uuid, remote_ip, huid=3, ctlid=0, fnid=2, transport="PCI"):
        result = {"status": False, "data": {}}
        url = "storage/volumes/{}/ports".format(vol_uuid)
        data = {"transport": transport, "fnid":fnid, "huid":huid, "ctlid":ctlid, "remote_ip": remote_ip}
        response = self.execute_api("POST", url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def detach_volume(self, port_uuid):
        result = {"status": False, "data": {}}
        url = "storage/ports/{}".format(port_uuid)
        data = {}
        response = self.execute_api("DELETE", url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def delete_volume(self, vol_uuid):
        # Delete API doesn't accept pool id; so not using it
        result = {"status": False, "data": {}}
        url = "storage/volumes/{}".format(vol_uuid)
        data = {}
        response = self.execute_api('DELETE', url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_ports(self):
        result = {"status": False, "data": {}}
        url = "storage/ports"
        response = self.execute_api("GET", url)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_api_server_health(self):
        result = {"status": False, "data":{}}
        url = "api_server/health"
        response = self.execute_api("GET", url)
        fun_test.log("GET {}".format(url))
        try:
            if response.ok:
                result = response.json()
                fun_test.log(json.dumps(result, indent=4))
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_dpu_state(self, dpu_index):
        result = {"status": False, "data": {}}
        url = "topology/dpus/FS1.{}/state".format(dpu_index)
        response = self.execute_api("GET", url)
        fun_test.log("GET {}".format(url))
        try:
            if response.ok:
                result = response.json()
                fun_test.log(json.dumps(result, indent=4))
            else:
                fun_test.log("Response not ok: {}", response.text)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_version(self):
        version = ""
        try:
            topo_dict = self.execute_api("GET", "topology")
            topo_dict = topo_dict.json()
            version = topo_dict['data']["FS1"]['version']
        except Exception as ex:
            fun_test.critical(str(ex))

        return version

    def get_volumes(self):
        try:
            res = self.execute_api("GET", "storage/volumes")
            if res.ok:
                res = res.json()
            else:
                fun_test.test_assert(
                    "Unable to get the volume information from {}".format(fun_test.shared_variables["testbed"]))
        except Exception as ex:
            fun_test.critical(str(ex))
        return res


if __name__ == "__main__":
    s = StorageControllerApi(api_server_ip="fs144-come")
    s.get_dpu_ids()
