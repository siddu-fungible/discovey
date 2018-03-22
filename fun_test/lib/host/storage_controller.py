from lib.system.fun_test import FunTestLibException, fun_test
from lib.host.dpcsh_client import DpcshClient
import json, time
import socket, fcntl, errno
import os, sys


class StorageController(DpcshClient):
    def __init__(self, mode="storage", target_ip=None, target_port=None, verbose=True):
        super(StorageController, self).__init__(mode=mode, target_ip=target_ip, target_port=target_port, verbose=verbose)

    def ip_cfg(self, ip, command_duration=1):
        cfg_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": ip}}
        return self.json_command(cfg_dict, command_duration=command_duration)

    def create_thin_block_volume(self, capacity, uuid, block_size, name, command_duration=1):
        create_dict = {}
        create_dict["class"] = "volume"
        create_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
        create_dict["params"] = {}
        create_dict["params"]["type"] = "VOL_TYPE_BLK_LOCAL_THIN"
        create_dict["params"]["capacity"] = capacity
        create_dict["params"]["block_size"] = block_size
        create_dict["params"]["uuid"] = uuid
        create_dict["params"]["name"] = name
        return self.json_command(create_dict, command_duration=command_duration)

    def volume_attach_remote(self, ns_id, uuid, remote_ip, huid=7, ctlid=0, fnid=5, command_duration=3):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid,
                                  "remote_ip": remote_ip}}
        return self.json_command(attach_dict, command_duration=command_duration)

    def volume_attach_pcie(self, ns_id, uuid, huid=0, ctlid=0, fnid=4, command_duration=3):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid}}
        return self.json_command(attach_dict, command_duration=command_duration)

    def create_rds_volume(self, capacity, block_size, uuid, name, remote_ip, remote_nsid, command_duration=2):
        create_dict = {"class": "volume",
                       "opcode": "VOL_ADMIN_OPCODE_CREATE",
                       "params": {"type": "VOL_TYPE_BLK_RDS",
                                  "capacity": capacity,
                                  "block_size": block_size,
                                  "uuid": uuid,
                                  "name": name,
                                  "remote_ip": remote_ip,
                                  "remote_nsid": remote_nsid}}
        return self.json_command(create_dict, command_duration=command_duration)

    def create_replica_volume(self, capacity, block_size, uuid, name, pvol_id, command_duration=1):
        create_dict = {"class": "volume",
                       "opcode": "VOL_ADMIN_OPCODE_CREATE",
                       "params": {"type": "VOL_TYPE_BLK_REPLICA",
                                  "capacity": capacity,
                                  "block_size": block_size,
                                  "uuid": uuid,
                                  "name": name,
                                  "min_replicas_insync": 1,
                                  "pvol_type": "VOL_TYPE_BLK_RDS",
                                  "pvol_id": pvol_id}}
        return self.json_command(create_dict, command_duration=command_duration)

    def create_volume(self, command_duration=1, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_command(volume_dict, command_duration=command_duration)

    def delete_volume(self, command_duration=1, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_DELETE"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_command(volume_dict, command_duration=command_duration)

    def peek(self, props_tree):
        props_tree = "peek " + props_tree
        return self.command(props_tree)

    def fail_volume(self, command_duration=1, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_INJECT_FAULT"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_command(volume_dict, command_duration=command_duration)


if __name__ == "__main__":
    sc = StorageController(target_ip="10.1.20.67", target_port=40220)
    output = sc.command("peek stats")
    sc.print_result(output)
