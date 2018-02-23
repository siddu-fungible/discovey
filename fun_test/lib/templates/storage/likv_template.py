from lib.system.fun_test import *
import hashlib
import random
from string import printable,ascii_letters

from lib.host.storage_controller import *


class LikvTemplate(object):
    THIN_VOLUME = "VOL_TYPE_BLK_LOCAL_THIN"
    DIR_STORE = "lvs_dir_store"
    LVS_ALLOCATOR = "lvs_allocator_store"
    LVS_VOLUME = "lvs_volume"
    DPCSH_MODE_LIKV = "likv"
    DPCSH_MODE_STORAGE = "storage"
    LIKV_COMPRESSION_ON = 1
    LIKV_COMPRESSION_OFF = 0
    LIKV_STATUS_SUCCESS = 0
    LIKV_STATUS_UNEXPECTED_STATE = 1
    LIKV_STATUS_DIRECTORY_ERROR = 2
    LIKV_STATUS_LVS_ERROR = 3
    LIKV_STATUS_BAD_VALUE_SIZE = 4
    LIKV_STATUS_OPEN_KEY_TABLE_FULL = 5
    LIKV_STATUS_KEY_RETAINED = 6
    LIKV_STATUS_BAD_OPEN_KEY_HANDLE = 7
    LIKV_STATUS_BAD_KEY = 8
    LIKV_STATUS_MBUF_ALLOC_FAILED = 9
    LIKV_STATUS_BAD_MBUF_SIZE = 10
    LIKV_STATUS_CLIENT_ERROR = 11
    LIKV_STATUS_NOT_IMPLEMENTED = 12
    LIKV_STATUS_ERROR = 13

    def __init__(self, volume_info, storage_controller_obj, likv_volume_id, compression_enabled=False):
        self.volume_info = volume_info
        self.storage_controller_obj = storage_controller_obj
        self.volume_id = likv_volume_id
        self.compression_enabled = compression_enabled

    def create_volumes(self):
        result = {'status': False}
        vol_dict = self.volume_info['volume_info']
        self.storage_controller_obj.mode = self.DPCSH_MODE_STORAGE
        for v in vol_dict:  # Todo segregate for diff vol type
            create_volume = self.storage_controller_obj.create_thin_block_volume(name=v['name'],
                                                                                 uuid=v['uuid'],
                                                                                 capacity=v['capacity'],
                                                                                 block_size=v['block_size'])
            self.mode = self.DPCSH_MODE_STORAGE if create_volume['status'] else self.DPCSH_MODE_LIKV
            fun_test.test_assert(create_volume['status'], message='Create Volume: {}'.format(v))
        self.storage_controller_obj.mode = self.DPCSH_MODE_LIKV
        result['status'] = True
        return result

    def setup_likv_store(self):
        self.storage_controller_obj.mode = self.DPCSH_MODE_LIKV
        cal_vol_size = "cal_vols_size"
        max_keys = self.volume_info["max_keys"]
        init_key = self.volume_info["init_key"]
        init_lvs_bytes = self.volume_info["init_lvs_bytes"]
        max_lvs_bytes = self.volume_info["max_lvs_bytes"]
        lvs_allocator_uuid = None
        lvs_vol_uuid = None
        lvs_dir_uuid = None

        for vols in self.volume_info['volume_info']:
            if vols['likv_type'] == self.LVS_VOLUME:
                lvs_vol_uuid = vols['uuid']
            elif vols['likv_type'] == self.DIR_STORE:
                lvs_dir_uuid = vols['uuid']
            elif vols['likv_type'] == self.LVS_ALLOCATOR:
                lvs_allocator_uuid = vols['uuid']

        likv_data = {"max_keys": max_keys,
                     "init_keys": init_key,
                     "volume_id": self.volume_id,
                     "init_lvs_bytes": init_lvs_bytes,
                     "lvs_allocator_uuid": lvs_allocator_uuid,
                     "max_lvs_bytes": max_lvs_bytes,
                     "lvs_vol_uuid": lvs_vol_uuid,
                     "dir_uuid": lvs_dir_uuid}
        calc_output = self.storage_controller_obj.json_command(action=cal_vol_size, data=likv_data)
        fun_test.simple_assert(calc_output['status'], message="Execute likv_calc_vol_size")
        action_create = "create"
        likv_data["options"] = self.LIKV_COMPRESSION_ON if self.compression_enabled else self.LIKV_COMPRESSION_OFF
        return self.storage_controller_obj.json_command(action=action_create, data=likv_data, expected_command_duration=2)

    def open(self):
        action = "open"
        return self.storage_controller_obj.json_command(data={"volume_id": self.volume_id}, action=action)

    def close(self):
        action = "close"
        return self.storage_controller_obj.json_command(data={"volume_id": self.volume_id}, action=action)

    def put(self, key_hex, value_hex, expected_timeout=2, send_only=False):
        json_data = {"key_hex": key_hex,
                     "value": value_hex,
                     "volume_id": self.volume_id}
        action = "put"
        return self.storage_controller_obj.json_command(data=json_data, action=action,
                                                        expected_command_duration=expected_timeout)

    def delete_value(self, key):
        action = "delete"
        json_data = {"key_hex": key,
                     "volume_id": self.volume_id}
        return self.storage_controller_obj.json_command(data=json_data, action=action, expected_command_duration=2)

    def get(self, key):
        action = "get"
        json_data = {"key_hex": key,
                     "volume_id": self.volume_id}
        return self.storage_controller_obj.json_command(data=json_data, action=action)

    def get_string(self, hex_value):
        return bytearray.fromhex(hex_value).decode()

    def get_hex(self, value):
        return ''.join(x.encode('hex') for x in value)

    def get_sha256_hex(self, value):
        m = hashlib.sha256()
        m.update(value)
        return self.get_hex(value=m.digest())

    def kv_generator(self, size=40, max_time=70):
        sample_size = 16  # fixed size usable chars
        usable_char = random.sample(ascii_letters, sample_size)
        timer = FunTimer(max_time)
        padding = size - sample_size
        while not timer.is_expired():
            random.shuffle(usable_char)
            char_str = ''.join(usable_char)
            if padding:
                fs = "{}" * (padding)
                padding_string = fs.format(*(['0'] * padding))
                data_str = "{0}{1}".format(padding_string, char_str)
            else:
                data_str = char_str
            yield self.get_sha256_hex(data_str), data_str
            del data_str


if __name__ == "__main__":
    storage_obj = StorageController(target_port=40220,
                                    target_ip="192.168.56.12",
                                    mode="likv")
    likv_obj = LikvTemplate(volume_info={},
                            storage_controller_obj=storage_obj,
                            likv_volume_id=10)
    likv_obj.storage_controller_obj.peek("stats/likv")
