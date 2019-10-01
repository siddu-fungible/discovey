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

    def configure_dataplane_ip(self, interface_name, ip, subnet_mask, next_hop, config_mode="static"):
        result = {"status": False, "data": {}}
        url = "{}/storage/storage_agent/dataplane_ip".format(self.base_url)
        data = {"ip_type": config_mode, "next_hop": next_hop, "dataplane_ip": ip, "subnet_mask": subnet_mask}
        response = request("post", url, auth=self.http_basic_auth, data=data)
        print response
        print response.json()

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
        url = "{}/ports/{}".format(self.base_url, port_uuid)
        response = request('delete', url)
        return response

    def delete_volume(self, vol_uuid):
        # Delete API doesn't accept pool id; so not using it
        url = "{}/volumes/{}".format(self.volume_url, vol_uuid)
        response = request('delete', url, auth=self.http_basic_auth)
        return response



