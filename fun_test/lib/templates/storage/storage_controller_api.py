from lib.system.fun_test import FunTestLibException, fun_test
import requests
import json
import re

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
        if data is None and method == "PUT":
            data = {}
        try:
            if method == "POST":
                response = requests.post(url, auth=self.http_basic_auth, json=data)
            elif method == "GET":
                response = requests.get(url, auth=self.http_basic_auth, json=data)
            elif method == "DELETE":
                response = requests.delete(url, auth=self.http_basic_auth, json=data)
            elif method == "PATCH":
                response = requests.patch(url, auth=self.http_basic_auth, json=data)
            elif method == "PUT":
                response = requests.put(url, auth=self.http_basic_auth, json=data)
        except Exception as ex:
            fun_test.critical("API Exception: {}".format(str(ex)))

        try:
            fun_test.log("API {} {}".format(method, url))
            fun_test.log("Response: text: {}".format(response.text))
        except Exception as ex:
            fun_test.critical(str(ex))
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

    def volume_attach_remote(self, vol_uuid, host_nqn, transport="TCP"):
        result = {"status": False, "data": {}}
        url = "storage/volumes/{}/ports".format(vol_uuid)
        data = {"host_nqn": host_nqn, "transport": transport}
        response = self.execute_api("POST", url, data=data)
        try:
            if response.ok:
                result = response.json()
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_volume_ports(self, vol_uuid):
        result = {"status": False, "data": {}}
        url = "storage/volumes/{}/ports".format(vol_uuid)
        response = self.execute_api("GET", url)
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

    def is_raw_vol_in_db(self, vol_uuid, come_handle, capacity, stripe_count, vol_type, encrypt, *args):
        result = {"status": False}
        command = "docker exec -ti run_sc cqlsh -e \"SELECT JSON * from storage_controller.volume_db\""
        output = self.convert_cqlsh_result_to_json(come_handle, command)
        if output:
            volume_db_uuid = self.get_uuid_from_db(output, vol_uuid)
            if volume_db_uuid["status"]:
                field_list = ["capacity", "stripe_count", "encrypt"]
                for i in field_list:
                    if eval(i) != volume_db_uuid["data"][i]:
                        result = {"status": False, "data": "{} doesn't match {} {}".
                            format(i, volume_db_uuid["data"][i], eval(i))}
                        return result
                if vol_type != volume_db_uuid["data"]["volume_type"]:
                    result = {"status": False, "data": "{} vol_type doesn't match".format(vol_type)}
                    return result
                result = {"status": True}
            else:
                result = {"status": False, "data": "Didn't find the uuid {}".format(vol_uuid)}
            return result
        else:
            result = {"status": False, "data": "Object not found in Cassandra DB"}
        return result

    def is_attach_in_db(self, port_uuid, come_handle, remote_ip, subsys_nqn, transport):
        result = {"status": False}
        command = "docker exec -ti run_sc cqlsh -e \"SELECT JSON * from storage_controller.port_db\""
        output = self.convert_cqlsh_result_to_json(come_handle, command)
        if output:
            port_db_uuid = self.get_uuid_from_db(output, port_uuid)
            if port_db_uuid["status"]:
                field_list = ["remote_ip", "subsys_nqn", "transport"]
                for i in field_list:
                    if eval(i) != port_db_uuid["data"][i]:
                        result = {"status": False, "data": "{} doesn't match".format(i)}
                        return result
                result = {"status": True}
            else:
                return result
        else:
            result = {"status": False, "data": "Object not found in Cassandra DB"}
            return result
        return result

    def is_detach_in_db(self, come_handle, port_uuid):
        result = {"status": True}
        command = "docker exec -ti run_sc cqlsh -e \"SELECT JSON * from storage_controller.port_db\""
        output = self.convert_cqlsh_result_to_json(come_handle, command)
        if output:
            port_db_uuid = self.get_uuid_from_db(output, port_uuid)
            if port_db_uuid["status"]:
                result = {"status": False, "data": "{} uuid is not detached".format(port_uuid)}
                return result
        return result

    def is_delete_in_db(self, come_handle, vol_uuid):
        result = {"status": True}
        command = "docker exec -ti run_sc cqlsh -e \"SELECT JSON * from storage_controller.volume_db\""
        output = self.convert_cqlsh_result_to_json(come_handle, command)
        if output:
            volume_db_uuid = self.get_uuid_from_db(output, vol_uuid)
            if volume_db_uuid["status"]:
                result = {"status": False, "data": "{} uuid is not deleted".format(vol_uuid)}
                return result
        return result

    def convert_cqlsh_result_to_json(self, come_handle, command):
        result = []
        output = come_handle.command(command)
        lines = output.split("\n")
        for line in lines:
            match_dictionary = re.search(r'{.*}', line)
            if match_dictionary:
                json_data = json.loads(match_dictionary.group())
                result.append(json_data.copy())
        return result

    # Check if a particular volume uuid or port uuid is in cassandra DB
    def get_uuid_from_db(self, db_data, uuid):
        result = {"status": False}
        for vol in db_data:
            if vol["uuid"] == uuid:
                result = {"status": True, "data": vol}
                return result

    def get_all_drives(self):
        result = {}
        url = "topology"
        try:
            response = self.execute_api("GET", url)
            topo_dict = response.json()
        except Exception as ex:
            fun_test.critical(ex.message)
        for dpu in topo_dict["data"]["FS1"]["dpus"]:
            result[dpu.get("uuid")] = []
            for drive in dpu["drives"]:
                drive_dict = {}
                drive_dict.update({"uuid": drive.get("uuid")})
                drive_dict.update({"slot_id": drive.get("slot_id")})
                drive_dict.update({'state': drive.get("state")})
                result[dpu.get("uuid")].append(drive_dict)
        return result

    def format_drives(self, dpu_dict):
        result = {}
        url = "topology/drives/"
        for dpu in dpu_dict:
            result[dpu] = []
            for drive in dpu_dict[dpu]:
                fun_test.log("UUID of drive in slot {} is: {}".format(drive.get("slot_id"), drive.get("uuid")))
                try:
                    response = self.execute_api("PUT", url + drive.get("uuid"))
                    response_dict = response.json()
                except Exception as ex:
                    fun_test.critical(ex.message)
                else:
                    elem = {}
                    if not response.ok:
                        elem.update({'status': False})
                        elem.update({'slot_id': drive.get("slot_id")})
                        elem.update({"uuid": drive.get("uuid")})
                    else:
                        elem.update({"status": True})
                        elem.update({"slot_id": drive.get("slot_id")})
                        elem.update({"uuid": drive.get("uuid")})
                result[dpu].append(elem)
        return result


if __name__ == "__main__":
    s = StorageControllerApi(api_server_ip="10.1.108.116")
    res = s.execute_api("GET", 'topology')
    res_dict = res.json()
    print res_dict["data"]["FS1"]["dpus"][0]["uuid"]
    print res_dict["data"]["FS1"]["dpus"][1]["uuid"]