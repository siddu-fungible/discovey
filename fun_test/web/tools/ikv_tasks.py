from lib.utilities.test_dpcsh_tcp_proxy import DpcshClient
import hashlib, json, os



def get_sha256_hex(value):
    m = hashlib.sha256()
    m.update(value)
    return get_hex(value=m.digest())

def get_md5_hex(value):
    m = hashlib.md5()
    m.update(value)
    return get_hex(value=m.digest())

def get_hex(value):
    return ''.join(x.encode('hex') for x in value)

def get_file_binary(file_name):
    contents = None
    with open(file_name, "rb") as f:
        contents = f.read()
    return contents

def verifiy_md5sum(file_name1, file_name2):
    file_name1_md5 = get_md5_hex(get_file_binary(file_name1))
    file_name2_md5 = get_md5_hex(get_file_binary(file_name2))
    return file_name1_md5 == file_name2_md5


def ikv_put(bite):
    client_obj = DpcshClient(server_address="10.1.20.67", server_port=5001)
    input_value = get_hex(bite)
    key_hex = get_sha256_hex(value=input_value)
    create_d = {"init_lvs_bytes": 1048576,
                "max_keys": 16384,
                "max_lvs_bytes": 1073741824,
                "init_keys": 4096,
                "volume_id": 0}
    print client_obj.command("likv create " + json.dumps(create_d))
    open_d = {"volume_id": 0}

    print client_obj.command("likv open " + json.dumps(open_d))

    put_d = {"key_hex": key_hex, "value": input_value, "volume_id": 0}
    client_obj.command("likv put " + json.dumps(put_d, ensure_ascii=False))
    return key_hex
