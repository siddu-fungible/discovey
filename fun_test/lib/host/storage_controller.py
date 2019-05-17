from lib.host.dpcsh_client import DpcshClient
from lib.system.fun_test import *
from lib.system import utils


class StorageController(DpcshClient):
    TIMEOUT = 2

    def __init__(self, mode="storage", target_ip=None, target_port=None, verbose=True):
        super(StorageController, self).__init__(mode=mode, target_ip=target_ip, target_port=target_port,
                                                verbose=verbose)

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

    def create_controller(self, ctrlr_uuid, transport, command_duration=TIMEOUT, **kwargs):
        create_dict = {"class": "controller",
                       "opcode": "CREATE",
                       "params": {"ctrlr_uuid": ctrlr_uuid, "transport": transport}}
        if kwargs:
            for key in kwargs:
                create_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=create_dict, command_duration=command_duration)

    def attach_volume_to_controller(self, ctrlr_uuid, ns_id, vol_uuid, command_duration=TIMEOUT):
        attach_dict = {"class": "controller",
                       "opcode": "ATTACH",
                       "params": {"ctrlr_uuid": ctrlr_uuid, "nsid": ns_id, "vol_uuid": vol_uuid}}
        return self.json_execute(verb=self.mode, data=attach_dict, command_duration=command_duration)

    def detach_volume_from_controller(self, ctrlr_uuid, ns_id, command_duration=TIMEOUT):
        detach_dict = {"class": "controller",
                       "opcode": "DETACH",
                       "params": {"ctrlr_uuid": ctrlr_uuid, "nsid": ns_id}}
        return self.json_execute(verb=self.mode, data=detach_dict, command_duration=command_duration)

    def delete_controller(self, ctrlr_uuid, command_duration=TIMEOUT):
        delete_dict = {"class": "controller",
                       "opcode": "DELETE",
                       "params": {"ctrlr_uuid": ctrlr_uuid}}
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

    def enable_device(self, device_id, command_duration=TIMEOUT):
        device_dict = {
            "class": "device",
            "opcode": "ERROR_INJECT_DISABLE",
            "params": {"device_id": device_id}}
        return self.json_execute(verb=self.mode, data=device_dict, command_duration=command_duration)

    def disable_device(self, device_id, command_duration=TIMEOUT):
        device_dict = {
            "class": "device",
            "opcode": "ERROR_INJECT_ENABLE",
            "params": {"device_id": device_id}}
        return self.json_execute(verb=self.mode, data=device_dict, command_duration=command_duration)

    def configure_ec_volume(self, ec_info, command_timeout):

        result = True
        compression_enabled = False
        if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
            result = False
            fun_test.critical("Mandatory attributes needed for the EC volume creation is missing in ec_info dictionary")
            return (result, ec_info)

        if "num_volumes" not in ec_info:
            fun_test.critical("Number of volumes needs to be configured is not provided. So going to configure only one"
                              "EC/LSV volume")
            ec_info["num_volumes"] = 1

        # Check if Compression has to be enabled on the Device
        if "compress" in ec_info.keys() and ec_info['compress']:
            compression_enabled = True
            ec_info['use_lsv'] = True
            # check if compression params are not passed assign default values
            ec_info["zip_effort"] = ec_info['zip_effort'] if 'zip_effort' in ec_info.keys() else "ZIP_EFFORT_AUTO"
            ec_info['zip_filter'] = ec_info['zip_filter'] if 'zip_filter' in ec_info.keys() else "FILTER_TYPE_DEFLATE"
            fun_test.log("Configuring Compression enabled EC volume with effort: {}, filter: {}".format(
                ec_info['zip_effort'], ec_info['zip_filter']))

        ec_info["uuids"] = {}
        ec_info["volume_capacity"] = {}
        ec_info["attach_uuid"] = {}
        ec_info["attach_size"] = {}

        for num in xrange(ec_info["num_volumes"]):
            ec_info["uuids"][num] = {}
            ec_info["uuids"][num]["blt"] = []
            ec_info["uuids"][num]["ec"] = []
            ec_info["uuids"][num]["jvol"] = []
            ec_info["uuids"][num]["lsv"] = []

            # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
            ec_info["volume_capacity"][num] = {}
            ec_info["volume_capacity"][num]["lsv"] = ec_info["capacity"]
            ec_info["volume_capacity"][num]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
            ec_info["volume_capacity"][num]["nparity"] = ec_info["volume_capacity"][num]["ndata"]
            # ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

            if "use_lsv" in ec_info and ec_info["use_lsv"]:
                fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                             "rounding that to the nearest 8KB value")
                ec_info["volume_capacity"][num]["jvol"] = ec_info["lsv_chunk_size"] * ec_info["volume_block"]["lsv"] * \
                                                          ec_info["jvol_size_multiplier"]

                for vtype in ["ndata", "nparity"]:
                    tmp = int(round(ec_info["volume_capacity"][num][vtype] * (1 + ec_info["lsv_pct"])))
                    # Aligning the capacity the nearest nKB(volume block size) boundary
                    ec_info["volume_capacity"][num][vtype] = ((tmp + (ec_info["volume_block"][vtype] - 1)) /
                                                              ec_info["volume_block"][vtype]) * \
                                                             ec_info["volume_block"][vtype]

            # Setting the EC volume capacity to ndata times of ndata volume capacity
            ec_info["volume_capacity"][num]["ec"] = ec_info["volume_capacity"][num]["ndata"] * ec_info["ndata"]

            # Adding one more block to the plex volume size to add room for super block
            for vtype in ["ndata", "nparity"]:
                ec_info["volume_capacity"][num][vtype] = ec_info["volume_capacity"][num][vtype] + \
                                                         ec_info["volume_block"][vtype]

            # Configuring ndata and nparity number of BLT volumes
            for vtype in ["ndata", "nparity"]:
                ec_info["uuids"][num][vtype] = []
                for i in range(ec_info[vtype]):
                    this_uuid = utils.generate_uuid()
                    ec_info["uuids"][num][vtype].append(this_uuid)
                    ec_info["uuids"][num]["blt"].append(this_uuid)
                    command_result = self.create_volume(
                        type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][num][vtype],
                        block_size=ec_info["volume_block"][vtype], name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                        command_duration=command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Creating {} {} {} {} {} bytes volume on DUT instance".
                                         format(num, i, vtype, ec_info["volume_types"][vtype],
                                                ec_info["volume_capacity"][num][vtype]))

            # Configuring EC volume on top of BLT volumes
            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["ec"].append(this_uuid)
            command_result = self.create_volume(
                type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"][num]["ec"],
                block_size=ec_info["volume_block"]["ec"], name="ec_" + this_uuid[-4:], uuid=this_uuid,
                ndata=ec_info["ndata"], nparity=ec_info["nparity"], pvol_id=ec_info["uuids"][num]["blt"],
                command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creating {} {}:{} {} bytes EC volume on DUT instance".
                                 format(num, ec_info["ndata"], ec_info["nparity"],
                                        ec_info["volume_capacity"][num]["ec"]))
            ec_info["attach_uuid"][num] = this_uuid
            ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["ec"]

            # Configuring LS volume and its associated journal volume based on the script config setting
            if "use_lsv" in ec_info and ec_info["use_lsv"]:
                ec_info["uuids"][num]["jvol"] = utils.generate_uuid()
                command_result = self.create_volume(
                    type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"][num]["jvol"],
                    block_size=ec_info["volume_block"]["jvol"], name="jvol_" + this_uuid[-4:],
                    uuid=ec_info["uuids"][num]["jvol"], command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating {} {} bytes Journal volume on DUT instance".
                                     format(num, ec_info["volume_capacity"][num]["jvol"]))

                this_uuid = utils.generate_uuid()
                ec_info["uuids"][num]["lsv"].append(this_uuid)
                if compression_enabled:
                    command_result = self.create_volume(type=ec_info["volume_types"]["lsv"],
                                                        capacity=ec_info["volume_capacity"][num]["lsv"],
                                                        block_size=ec_info["volume_block"]["lsv"],
                                                        name="lsv_" + this_uuid[-4:],
                                                        uuid=this_uuid,
                                                        group=ec_info["ndata"],
                                                        jvol_uuid=ec_info["uuids"][num]["jvol"],
                                                        pvol_id=ec_info["uuids"][num]["ec"],
                                                        compress=ec_info['compress'],
                                                        zip_effort=ec_info['zip_effort'],
                                                        zip_filter=ec_info['zip_filter'],
                                                        command_duration=command_timeout)
                else:
                    command_result = self.create_volume(type=ec_info["volume_types"]["lsv"],
                                                        capacity=ec_info["volume_capacity"][num]["lsv"],
                                                        block_size=ec_info["volume_block"]["lsv"],
                                                        name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                                                        group=ec_info["ndata"], jvol_uuid=ec_info["uuids"][num]["jvol"],
                                                        pvol_id=ec_info["uuids"][num]["ec"],
                                                        command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating {} {} bytes LS volume on DUT instance".
                                     format(num, ec_info["volume_capacity"][num]["lsv"]))
                ec_info["attach_uuid"][num] = this_uuid
                ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["lsv"]

        return (result, ec_info)

    def unconfigure_ec_volume(self, ec_info, command_timeout):

        # Unconfiguring LS volume based on the script config settting
        for num in xrange(ec_info["num_volumes"]):
            if "use_lsv" in ec_info and ec_info["use_lsv"]:
                this_uuid = ec_info["uuids"][num]["lsv"][0]
                command_result = self.delete_volume(
                    type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"][num]["lsv"],
                    block_size=ec_info["volume_block"]["lsv"], name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                    command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} bytes LS volume on DUT instance".
                                     format(num, ec_info["volume_capacity"][num]["lsv"]))

                this_uuid = ec_info["uuids"][num]["jvol"]
                command_result = self.delete_volume(
                    type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"][num]["jvol"],
                    block_size=ec_info["volume_block"]["jvol"], name="jvol_" + this_uuid[-4:], uuid=this_uuid,
                    command_duration=command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} bytes Journal volume on DUT instance".
                                     format(num, ec_info["volume_capacity"][num]["jvol"]))

            # Unconfiguring EC volume configured on top of BLT volumes
            this_uuid = ec_info["uuids"][num]["ec"][0]
            command_result = self.delete_volume(
                type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"][num]["ec"],
                block_size=ec_info["volume_block"]["ec"], name="ec_" + this_uuid[-4:], uuid=this_uuid,
                command_duration=command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} {}:{} {} bytes EC volume on DUT instance".
                                 format(num, ec_info["ndata"], ec_info["nparity"],
                                        ec_info["volume_capacity"][num]["ec"]))

            # Unconfiguring ndata and nparity number of BLT volumes
            for vtype in ["ndata", "nparity"]:
                for i in range(ec_info[vtype]):
                    this_uuid = ec_info["uuids"][num][vtype][i]
                    command_result = self.delete_volume(
                        type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][num][vtype],
                        block_size=ec_info["volume_block"][vtype], name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                        command_duration=command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "Deleting {} {} {} {} {} bytes volume on DUT instance".
                                         format(num, i, vtype, ec_info["volume_types"][vtype],
                                                ec_info["volume_capacity"][num][vtype]))

        return True

    def plex_rebuild(self, subcmd, command_duration=TIMEOUT, **kwargs):
        volume_dict = {}
        volume_dict["class"] = "volume"
        volume_dict["opcode"] = "VOL_ADMIN_OPCODE_REBUILD"
        volume_dict["params"] = {"subcmd": subcmd}
        if kwargs:
            for key in kwargs:
                volume_dict["params"][key] = kwargs[key]
        return self.json_execute(verb=self.mode, data=volume_dict, command_duration=command_duration)


if __name__ == "__main__":
    sc = StorageController(target_ip="10.1.20.67", target_port=40220)
    output = sc.command("peek stats")
    sc.print_result(output)
