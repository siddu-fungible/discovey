from lib.system.fun_test import FunTestLibException, fun_test
from lib.host.dpcsh_client import DpcshClient
import json, time
import socket, fcntl, errno
import os, sys


class StorageController(DpcshClient):
    TIMEOUT = 2
    def __init__(self, mode="storage", target_ip=None, target_port=None, verbose=True):
        super(StorageController, self).__init__(mode=mode, target_ip=target_ip, target_port=target_port, verbose=verbose)

    def ip_cfg(self, ip, command_duration=TIMEOUT):
        cfg_dict = {"class": "controller", "opcode": "IPCFG", "params": {"ip": ip}}
        return self.json_execute(verb=self.mode, data=cfg_dict, command_duration=command_duration)

    def create_thin_block_volume(self, capacity, uuid, block_size, name, use_ls=False, command_duration=TIMEOUT):
        create_dict = {}
        create_dict["class"] = "volume"
        create_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
        create_dict["params"] = {}
        create_dict["params"]["type"] = "VOL_TYPE_BLK_LOCAL_THIN"
        create_dict["params"]["capacity"] = capacity
        create_dict["params"]["block_size"] = block_size
        create_dict["params"]["uuid"] = uuid
        create_dict["params"]["name"] = name
        if use_ls:
            create_dict["params"]["use_ls"] = use_ls
        return self.json_execute(verb=self.mode, data=create_dict, command_duration=command_duration)

    def delete_thin_block_volume(self, capacity, uuid, block_size, name, command_duration=TIMEOUT):
        delete_dict = {"class": "volume", "opcode": "VOL_ADMIN_OPCODE_DELETE", "params": {}}
        delete_dict["params"]["type"] = "VOL_TYPE_BLK_LOCAL_THIN"
        delete_dict["params"]["capacity"] = capacity
        delete_dict["params"]["block_size"] = block_size
        delete_dict["params"]["uuid"] = uuid
        delete_dict["params"]["name"] = name
        return self.json_execute(verb=self.mode, data=delete_dict, command_duration=command_duration)

    def volume_attach_remote(self, ns_id, uuid, remote_ip, huid=7, ctlid=0, fnid=5, command_duration=TIMEOUT, **kwargs):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid,
                                  "remote_ip": remote_ip}}
        if kwargs:
            for key in kwargs:
                attach_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=attach_dict, command_duration=command_duration)

    def volume_detach_remote(self, ns_id, uuid, remote_ip, huid=7, ctlid=0, fnid=5, command_duration=TIMEOUT, **kwargs):
        detach_dict = {"class": "controller",
                       "opcode": "DETACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid,
                                  "remote_ip": remote_ip}}
        if kwargs:
            for key in kwargs:
                detach_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=detach_dict, command_duration=command_duration)

    def volume_attach_pcie(self, ns_id, uuid, huid=0, ctlid=0, fnid=2, command_duration=TIMEOUT):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid}}
        return self.json_execute(verb=self.mode, data=attach_dict, command_duration=command_duration)

    def attach_controller(self, command_duration=TIMEOUT, **kwargs):
        param_dict = {"class": "controller",
                      "opcode": "ATTACH",
                      "params": {}}
        for key in kwargs:
            param_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=param_dict, command_duration=command_duration)

    def create_controller(self, command_duration=TIMEOUT, **kwargs):
        param_dict = {"class": "controller", "opcode": "CREATE", "params": {}}
        for key in kwargs:
            param_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=param_dict, command_duration=command_duration)

    def volume_detach_pcie(self, ns_id, uuid, huid=0, ctlid=0, fnid=2, command_duration=TIMEOUT):
        detach_dict = {"class": "controller",
                       "opcode": "DETACH",
                       "params": {"huid": huid, "ctlid": ctlid, "fnid": fnid, "nsid": ns_id, "uuid": uuid}}
        return self.json_execute(verb=self.mode, data=detach_dict, command_duration=command_duration)

    def create_rds_volume(self, capacity, block_size, uuid, name, remote_ip, remote_nsid, command_duration=TIMEOUT):
        create_dict = {"class": "volume",
                       "opcode": "VOL_ADMIN_OPCODE_CREATE",
                       "params": {"type": "VOL_TYPE_BLK_RDS",
                                  "capacity": capacity,
                                  "block_size": block_size,
                                  "uuid": uuid,
                                  "name": name,
                                  "remote_ip": remote_ip,
                                  "remote_nsid": remote_nsid}}
        return self.json_execute(verb=self.mode, data=create_dict, command_duration=command_duration)

    def create_replica_volume(self, capacity, block_size, uuid, name, pvol_id, command_duration=TIMEOUT):
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
        return self.json_execute(verb=self.mode, data=create_dict, command_duration=command_duration)

    def create_volume(self, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_CREATE"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)

    def delete_volume(self, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_DELETE"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)

    def mount_volume(self, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_MOUNT"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)

    def unmount_volume(self, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_UNMOUNT"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)

    def peek(self, props_tree, legacy=True, command_duration=TIMEOUT):
        if legacy:
            props_tree = "peek " + props_tree
            return self.command(props_tree, legacy=True, command_duration=command_duration)
        else:
            return self.json_execute(verb="peek", data=props_tree, command_duration=command_duration)

    def poke(self, props_tree, legacy=True, command_duration=TIMEOUT):
        if legacy:
            props_tree = "poke " + props_tree
            return self.command(props_tree, legacy=True, command_duration=command_duration)
        else:
            return self.json_execute(verb="poke", data=props_tree, command_duration=command_duration)

    def fail_volume(self, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_INJECT_FAULT"
        volume_dict["params"] = {}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)


if __name__ == "__main__":
    sc = StorageController(target_ip="10.1.20.67", target_port=40220)
    output = sc.command("peek stats")
    sc.print_result(output)
