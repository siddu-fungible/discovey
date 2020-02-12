from lib.system.fun_test import *
from lib.host.network_controller import NetworkController
from lib.host.linux import Linux
from lib.system import utils
import re


def configure_ec_volume_across_f1s(ec_info={}, command_timeout=5):
    """
    :param storage_controller_list:
    :param ec_info:
    :param command_timeout:
    :return: (status , ec_info)

    The user has to provide the additional ec_info attribute to configure the EC volume's plex volume across
    multiple F1
    * storage_controller_list - list of storage controller objects in which the volume needs to be configured
    * f1_ips - list of all F1s IP addresses
    * hosting_f1_list - list contains the F1s hosting each volume
    * plex_spread_list - Same as above, but instead of that the list containing the actual number of plexes to be
    configured in all the F1s, like [4, 2]
    """
    result = True
    compression_enabled = False
    if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
        result = False
        fun_test.simple_assert(False, "Mandatory ndata/nparity/capacity attributes available")

    if "storage_controller_list" not in ec_info:
        fun_test.simple_assert(False, "Storage controller object list available")

    if "f1_ips" not in ec_info:
        fun_test.simple_assert(False, "F1s IP addresses available")

    if "host_ips" not in ec_info:
        fun_test.simple_assert(False, "Host IP addresses available")

    fun_test.simple_assert(len(ec_info["storage_controller_list"]) == len(ec_info["f1_ips"]),
                           "F1 IP address available for all the storage controller")

    fun_test.simple_assert(ec_info["num_volumes"] == len(ec_info["host_ips"]),
                           "Host IP address available for all the volumes")

    if "num_volumes" not in ec_info:
        fun_test.critical("Number of volumes needs to be configured is not provided. So going to configure only one"
                          "EC/LSV volume")
        ec_info["num_volumes"] = 1

    if "transport_port" not in ec_info:
        ec_info["transport_port"] = 4420

    if "rds_port" not in ec_info:
        ec_info["rds_port"] = 1099

    if "remote_transport" not in ec_info:
        ec_info["remote_transport"] = "RDS"

    if "remote_connections" not in ec_info:
        ec_info["remote_connections"] = 1

    num_f1 = len(ec_info["storage_controller_list"])

    # If hosting_f1_list is not provided then the first volume will be host in first F1, second volume in second F1 and
    # so on
    if "hosting_f1_list" not in ec_info:
        ec_info["hosting_f1_list"] = [0] * ec_info["num_volumes"]
        for i in range(ec_info["num_volumes"]):
            ec_info["hosting_f1_list"][i] = i % num_f1

    # Check whether the spread list is given for all the volumes, else copy the one and only available spread to
    # all the volumes
    if "plex_spread_list" in ec_info and type(ec_info["plex_spread_list"][0] == int):
        cur_spread = ec_info["plex_spread_list"]
        ec_info["plex_spread_list"] = []
        for num in range(ec_info["num_volumes"]):
            ec_info["plex_spread_list"].append(cur_spread)

    # If plex spread list is not given, equally splitting the plex across all the F1
    if "plex_spread_list" not in ec_info:
        ec_info["plex_spread_list"] = []
        for num in range(ec_info["num_volumes"]):
            ec_info["plex_spread_list"].append([0] * num_f1)
            for i in range(ec_info["ndata"] + ec_info["nparity"]):
                ec_info["plex_spread_list"][num][i % num_f1] += 1

    # In case if the spread list is not equal to the num_volumes, then copy last spread to the rest of the volumes
    if len(ec_info["plex_spread_list"]) != ec_info["num_volumes"]:
        last_spread = ec_info["plex_spread_list"][-1]
        ec_info["plex_spread_list"].extend([last_spread] *
                                           (ec_info["num_volumes"] - len(ec_info["plex_spread_list"])))

    # Preparing which plex volume needs to configured in which F1
    plex_to_f1_map = []
    for num in range(ec_info["num_volumes"]):
        plex_to_f1_map.append([0] * (ec_info["ndata"] + ec_info["nparity"]))
        mindex = 0
        for sc_index, num_vol in enumerate(ec_info["plex_spread_list"][num]):
            for i in range(num_vol):
                plex_to_f1_map[num][mindex] = sc_index
                mindex += 1
    ec_info["plex_to_f1_map"] = plex_to_f1_map

    # Check if Compression has to be enabled on the Device
    if "compress" in ec_info.keys() and ec_info['compress']:
        compression_enabled = True
        ec_info['use_lsv'] = True
        # check if compression params are not passed assign default values
        ec_info["zip_effort"] = ec_info['zip_effort'] if 'zip_effort' in ec_info.keys() else "ZIP_EFFORT_AUTO"
        ec_info['zip_filter'] = ec_info['zip_filter'] if 'zip_filter' in ec_info.keys() else "FILTER_TYPE_DEFLATE"
        fun_test.log("Configuring Compression enabled EC volume with effort: {}, filter: {}".format(
            ec_info['zip_effort'], ec_info['zip_filter']))

    # Enabling network controller to listen in the given F1 ip and port
    print "storage controller list is: {}".format(ec_info["storage_controller_list"])
    print "dir of storage controller list is: {}".format(dir(ec_info["storage_controller_list"]))
    for index, sc in enumerate(ec_info["storage_controller_list"]):
        print "storage controller list is: {}".format(sc)
        print "dir of storage controller list is: {}".format(dir(sc))
        command_result = sc.ip_cfg(ip=ec_info["f1_ips"][index])
        fun_test.test_assert(command_result["status"], "Enabling controller to listen in {} on {} port in DUT {}".
                             format(ec_info["f1_ips"][index], ec_info["transport_port"], index))

    ec_info["uuids"] = {}
    ec_info["volume_capacity"] = {}
    ec_info["attach_uuid"] = {}
    ec_info["attach_size"] = {}
    ec_info["attach_nqn"] = {}
    ec_info["attach_nsid"] = {}
    ec_info["attach_ctlr"] = {}
    ec_info["rds_nsid"] = {}

    # Maintaining separate ns_id for each F1
    f1_ns_id = [0] * num_f1
    nqn = 0
    for num in xrange(ec_info["num_volumes"]):
        ec_info["uuids"][num] = {}
        ec_info["uuids"][num]["blt"] = []
        ec_info["uuids"][num]["ec"] = []
        ec_info["uuids"][num]["jvol"] = []
        ec_info["uuids"][num]["lsv"] = []
        ec_info["uuids"][num]["rds"] = []
        ec_info["uuids"][num]["nonrds"] = []
        ec_info["uuids"][num]["ctlr"] = []
        ec_info["rds_nsid"][num] = []

        # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
        ec_info["volume_capacity"][num] = {}
        ec_info["volume_capacity"][num]["lsv"] = ec_info["capacity"]
        ec_info["volume_capacity"][num]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
        ec_info["volume_capacity"][num]["nparity"] = ec_info["volume_capacity"][num]["ndata"]
        # ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by {}% and "
                         "rounding that to the nearest 4KB value".format(int(ec_info["lsv_pct"] * 100)))
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

        # Configuring the controller in all the F1s for the current volume
        cur_vol_host_f1 = ec_info["hosting_f1_list"][num]
        host_f1_ip = ec_info["f1_ips"][cur_vol_host_f1]
        cur_plex_to_f1_map = plex_to_f1_map[num]
        hosting_sc = ec_info["storage_controller_list"][cur_vol_host_f1]
        for index, sc in enumerate(ec_info["storage_controller_list"]):
            if sc not in ec_info:
                ec_info[sc] = {}
            if index == cur_vol_host_f1:
                transport = "TCP"
                port = ec_info["transport_port"]
                remote_ip = ec_info["host_ips"][num]
            else:
                transport = ec_info["remote_transport"]
                port = ec_info["rds_port"]
                remote_ip = ec_info["f1_ips"][cur_vol_host_f1]

            # Check whether the controller for the given remote IP and transport is already created in this current
            # storage controller. If not create it, else skip the controller creation
            if remote_ip not in ec_info[sc] or transport not in ec_info[sc][remote_ip]:
                if remote_ip not in ec_info[sc]:
                    ec_info[sc][remote_ip] = {}
                if transport not in ec_info[sc][remote_ip]:
                    ec_info[sc][remote_ip][transport] = {}

                ctrlr_uuid = utils.generate_uuid()
                nqn += 1

                ec_info["uuids"][num]["ctlr"].append(ctrlr_uuid)
                ec_info[sc][remote_ip][transport]["ctrlr_uuid"] = ctrlr_uuid
                ec_info[sc][remote_ip][transport]["nqn"] = "nqn" + str(nqn)

                command_result = sc.create_controller(ctrlr_uuid=ctrlr_uuid, transport=transport, remote_ip=remote_ip,
                                                      port=port, subsys_nqn="nqn" + str(nqn),
                                                      host_nqn=remote_ip, ctrlr_id=0, ctrlr_type="BLOCK",
                                                      command_duration=command_timeout)
                fun_test.test_assert(command_result["status"],
                                     "Configuring {} transport Storage Controller for {} remote IP on DUT {}".
                                     format(transport, remote_ip, index))

                if index == cur_vol_host_f1:
                    ec_info["attach_ctlr"][num] = ctrlr_uuid
                    ec_info["attach_nqn"][num] = "nqn" + str(nqn)
            else:
                fun_test.log("Skipping the controller creation, because controller for the remote IP {} with the {} "
                             "transport is already created with the controller ID: {}".
                             format(remote_ip, transport, ec_info[sc][remote_ip][transport]["ctrlr_uuid"]))
                if index == cur_vol_host_f1:
                    ec_info["attach_ctlr"][num] = ec_info[sc][remote_ip][transport]["ctrlr_uuid"]
                    ec_info["attach_nqn"][num] = ec_info[sc][remote_ip][transport]["nqn"]

        """
        # Old controller create code
        for index, sc in enumerate(ec_info["storage_controller_list"]):
            ctrlr_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["ctlr"].append(ctrlr_uuid)
            if index == cur_vol_host_f1:
                transport = "TCP"
                remote_ip = ec_info["host_ips"][num]
                ec_info["attach_nqn"][num] = "nqn" + str(index)
            else:
                transport = "RDS"
                remote_ip = ec_info["f1_ips"][cur_vol_host_f1]
            command_result = sc.create_controller(ctrlr_uuid=ctrlr_uuid, transport=transport, remote_ip=remote_ip,
                                                  nqn="nqn" + str(index), port=1099,
                                                  command_duration=command_timeout)
            fun_test.test_assert(command_result["status"],
                                 "Configuring {} transport Storage Controller for {} remote IP on DUT {}".
                                 format(transport, remote_ip, index))
        """

        # Configuring ndata and nparity number of BLT volumes
        plex_num = 0
        for vtype in ["ndata", "nparity"]:
            ec_info["uuids"][num][vtype] = []
            for i in range(ec_info[vtype]):
                this_uuid = utils.generate_uuid()
                ec_info["uuids"][num][vtype].append(this_uuid)
                ec_info["uuids"][num]["blt"].append(this_uuid)
                sc_index = cur_plex_to_f1_map[plex_num]
                sc = ec_info["storage_controller_list"][sc_index]
                command_result = sc.create_volume(
                    type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][num][vtype],
                    block_size=ec_info["volume_block"][vtype], name=vtype + "_" + this_uuid[-4:], uuid=this_uuid,
                    group_id=num+1, command_duration=command_timeout)
                fun_test.test_assert(command_result["status"], "Creating {} {} {} {} {} bytes volume on DUT {}".
                                     format(num, i, vtype, ec_info["volume_types"][vtype],
                                            ec_info["volume_capacity"][num][vtype], sc_index))
                if sc_index != cur_vol_host_f1:
                    f1_ns_id[sc_index] += 1
                    ns_id = f1_ns_id[sc_index]
                    ec_info["rds_nsid"][num].append((sc_index, ns_id, ec_info["f1_ips"][sc_index]))
                    remote_ip = ec_info["f1_ips"][cur_vol_host_f1]
                    transport = ec_info["remote_transport"]
                    command_result = sc.attach_volume_to_controller(
                        ctrlr_uuid=ec_info[sc][remote_ip][transport]["ctrlr_uuid"], ns_id=ns_id, vol_uuid=this_uuid,
                        command_duration=command_timeout)
                    fun_test.test_assert(command_result["status"],
                                         "Attaching {} {} {} {} bytes volume on DUT {}".
                                         format(num, i, vtype, ec_info["volume_capacity"][num][vtype], sc_index))
                else:
                    ec_info["uuids"][num]["nonrds"].append(this_uuid)
                plex_num += 1

        # Configuring RDS volume in the hosting F1 for all the remote BLTs
        for sc_index, cur_ns_id, cur_f1_ip in ec_info["rds_nsid"][num]:
            sc = ec_info["storage_controller_list"][sc_index]
            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["rds"].append(this_uuid)
            command_result = hosting_sc.create_volume(
                type="VOL_TYPE_BLK_RDS", capacity=ec_info["volume_capacity"][num]["ndata"],
                block_size=ec_info["volume_block"]["ndata"], name="RDS" + "_" + this_uuid[-4:], uuid=this_uuid,
                remote_nsid=cur_ns_id, remote_ip=cur_f1_ip, group_id=num+1, connections=ec_info["remote_connection"],
                ctrlr_id=0, host_nqn=ec_info["f1_ips"][cur_vol_host_f1],
                subsys_nqn=ec_info[sc][host_f1_ip][ec_info["remote_transport"]]["nqn"],
                command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creating RDS volume for the remote BLT {} in remote F1 {} "
                                                           "on DUT {}".format(cur_ns_id, cur_f1_ip, cur_vol_host_f1))
        """
        plex_num = 0
        for sc_index in cur_plex_to_f1_map:
            if sc_index == cur_vol_host_f1:
                plex_num += 1
                continue
            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["rds"].append(this_uuid)
            command_result = hosting_sc.create_volume(
                type="VOL_TYPE_BLK_RDS", capacity=ec_info["volume_capacity"][num]["ndata"],
                block_size=ec_info["volume_block"]["ndata"], name="RDS" + "_" + this_uuid[-4:], uuid=this_uuid,
                remote_nsid=int(str(num+1)+ str(plex_num)), remote_ip=ec_info["f1_ips"][sc_index],
                command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creating RDS volume for the remote BLT {} in remote F1 {} "
                                                           "on DUT {}".format(num+ plex_num,
                                                                              ec_info["f1_ips"][sc_index],
                                                                              cur_vol_host_f1))
            plex_num += 1
        """

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        ec_info["uuids"][num]["ec"].append(this_uuid)
        pvol_id = ec_info["uuids"][num]["nonrds"] + ec_info["uuids"][num]["rds"]
        command_result = hosting_sc.create_volume(
            type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"][num]["ec"],
            block_size=ec_info["volume_block"]["ec"], name="ec_" + this_uuid[-4:], uuid=this_uuid,
            ndata=ec_info["ndata"], nparity=ec_info["nparity"], pvol_id=pvol_id, group_id=num+1,
            command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Creating {} {}:{} {} bytes EC volume on DUT {}".
                             format(num, ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"][num]["ec"],
                                    cur_vol_host_f1))
        ec_info["attach_uuid"][num] = this_uuid
        ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["ec"]

        # Configuring LS volume and its associated journal volume based on the script config setting
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            ec_info["uuids"][num]["jvol"] = utils.generate_uuid()
            command_result = hosting_sc.create_volume(
                type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"][num]["jvol"],
                block_size=ec_info["volume_block"]["jvol"], name="jvol_" + this_uuid[-4:],
                uuid=ec_info["uuids"][num]["jvol"], group_id=num+1, command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes Journal volume on DUT {}".
                                 format(num, ec_info["volume_capacity"][num]["jvol"], cur_vol_host_f1))

            this_uuid = utils.generate_uuid()
            ec_info["uuids"][num]["lsv"].append(this_uuid)
            if compression_enabled:
                command_result = hosting_sc.create_volume(type=ec_info["volume_types"]["lsv"],
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
                                                          group_id=num + 1,
                                                          command_duration=command_timeout)
            else:
                command_result = hosting_sc.create_volume(type=ec_info["volume_types"]["lsv"],
                                                          capacity=ec_info["volume_capacity"][num]["lsv"],
                                                          block_size=ec_info["volume_block"]["lsv"],
                                                          name="lsv_" + this_uuid[-4:], uuid=this_uuid,
                                                          group=ec_info["ndata"],
                                                          jvol_uuid=ec_info["uuids"][num]["jvol"],
                                                          pvol_id=ec_info["uuids"][num]["ec"],
                                                          group_id=num+1,
                                                          command_duration=command_timeout)
            fun_test.test_assert(command_result["status"], "Creating {} {} bytes LS volume on DUT {}".
                                 format(num, ec_info["volume_capacity"][num]["lsv"], cur_vol_host_f1))
            ec_info["attach_uuid"][num] = this_uuid
            ec_info["attach_size"][num] = ec_info["volume_capacity"][num]["lsv"]

        # Attaching the EC/LSV
        f1_ns_id[cur_vol_host_f1] += 1
        ns_id = f1_ns_id[cur_vol_host_f1]
        ec_info["attach_nsid"][num] = ns_id
        command_result = hosting_sc.attach_volume_to_controller(ctrlr_uuid=ec_info["attach_ctlr"][num],
                                                                ns_id=ns_id, vol_uuid=ec_info["attach_uuid"][num],
                                                                command_duration=command_timeout)
        # command_result = hosting_sc.attach_volume_to_controller(
        #    ctrlr_uuid=ec_info["uuids"][num]["ctlr"][cur_vol_host_f1], ns_id=int(str(num+1) + str(plex_num)),
        #    vol_uuid=ec_info["attach_uuid"][num], command_duration=command_timeout)
        fun_test.test_assert(command_result["status"], "Attaching {} {} bytes EC/LS volume on DUT {}".
                             format(num, ec_info["attach_size"][num], cur_vol_host_f1))

    return (result, ec_info)


class FunCpDockerContainer(Linux):
    CUSTOM_PROMPT_TERMINATOR = r'# '

    def __init__(self, name, **kwargs):
        super(FunCpDockerContainer, self).__init__(**kwargs)
        self.name = name

    def _connect(self):
        result = False
        if (super(FunCpDockerContainer, self)._connect()):
            # the below set_prompt_terminator is the temporary workaround of the recent FunCP docker container change
            # Recently while logging into the docker container it gets logged in as root user
            self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
            self.command("docker exec -it {} bash".format(self.name))
            self.clean()
            self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
            self.command("export PS1='{}'".format(self.CUSTOM_PROMPT_TERMINATOR), wait_until_timeout=3,
                         wait_until=self.CUSTOM_PROMPT_TERMINATOR)
            result = True
        fun_test.simple_assert(result, "SSH connection to docker host: {}".format(self))
        return result


MODE_END_POINT = "ep"


class StorageFsTemplate(object):
    NUM_FS_CONTAINERS = 2
    FPG_L2_MTU = 1500
    FUNSDK_DIR = "/mnt/keep/FunSDK"
    WORKSPACE = "/home/fun/workspace"
    FUNGIBLE_ROOT = "opt/fungible"
    DEFAULT_TIMEOUT = 300
    PREP_TIMEOUT = 900
    DEPLOY_TIMEOUT = 300
    BOND_BRINGUP_TIMEOUT = 300
    LAUNCH_SCRIPT = "./integration_test/emulation/test_system.py "
    DEPLOY_SCRIPT = "cclinux/cclinux_service.sh "
    PREPARE_CMD = "{} --prepare --docker".format(LAUNCH_SCRIPT)
    DEPLOY_CONTAINER_CMD = "{} --start".format(DEPLOY_SCRIPT)
    DOCKER_LAUNCH_OUTPUT = "/tmp/docker_launch_output.txt"
    # F1_0_HANDLE = None
    # F1_1_HANDLE = None

    def __init__(self, come_obj):
        self.come_obj = come_obj
        self.container_info = {}
        self.workspace = ""
        self.fungible_root = ""

    def enter_funsdk(self):
        self.come_obj.command("cd {}".format(self.FUNSDK_DIR))

    def get_container_objs(self, stop_run_sc=False, include_storage=True):

        result = {'status': False, 'container_info': {}, 'container_names': []}

        if not self.come_obj.check_ssh():
            return result

        # Get the WORKSPACE & FUNGIBLE_ROOT environment variable
        workspace = self.come_obj.command("echo $WORKSPACE")
        workspace = workspace.strip()
        if workspace:
            self.workspace = workspace

        fungible_root = self.come_obj.command("echo $FUNGIBLE_ROOT")
        fungible_root = fungible_root.strip()
        if fungible_root:
            self.fungible_root = fungible_root

        get_containers = self.get_container_names(stop_run_sc=stop_run_sc, include_storage=include_storage)
        if not get_containers['status']:
            return result

        result['container_names'] = get_containers['container_name_list']
        for container_name in get_containers['container_name_list']:
            container_obj = FunCpDockerContainer(host_ip=self.come_obj.host_ip,
                                                 ssh_username=self.come_obj.ssh_username,
                                                 ssh_password=self.come_obj.ssh_password,
                                                 ssh_port=self.come_obj.ssh_port,
                                                 name=container_name)
            """
            if "0" in container_name:  # based on logic that container names will always be F1-1, F1-0
                self.F1_0_HANDLE = container_obj
            else:
                self.F1_1_HANDLE = container_obj
            """
            self.container_info[container_name] = container_obj

        result['container_info'] = self.container_info
        result['status'] = True
        return result

    def deploy_funcp_container(self, update_deploy_script=True, update_workspace=True, mode=None,
                               include_storage=False, stop_run_sc=True, launch_resp_parse=False):
        # check if come is up
        result = {'status': False, 'container_info': {}, 'container_names': []}
        self.mode = mode
        if not self.come_obj.check_ssh():
            return result

        # Get the WORKSPACE & FUNGIBLE_ROOT environment variable
        workspace = self.come_obj.command("echo $WORKSPACE")
        workspace = workspace.strip()
        if workspace:
            self.workspace = workspace

        fungible_root = self.come_obj.command("echo $FUNGIBLE_ROOT")
        fungible_root = fungible_root.strip()
        if fungible_root:
            self.fungible_root = fungible_root

        # get funsdk
        if update_deploy_script:
            if not self.update_fundsk():
                return result

        # prepare setup environment
        if update_workspace:
            response = self.prepare_docker(mode, timeout=self.PREP_TIMEOUT)
            if not response:
                return result

        # launch containers
        launch_resp = self.launch_funcp_containers(mode, timeout=self.DEPLOY_TIMEOUT)
        if not launch_resp:
            fun_test.critical("FunCP container launch failed")
            if launch_resp_parse:
                pass
            else:
                return result

        # get container names.
        result = self.get_container_objs(stop_run_sc=stop_run_sc, include_storage=include_storage)
        '''
        get_containers = self.get_container_names(include_storage=include_storage)
        if not get_containers['status']:
            return result
        result['container_names'] = get_containers['container_name_list']
        for container_name in get_containers['container_name_list']:
            container_obj = FunCpDockerContainer(host_ip=self.come_obj.host_ip,
                                                 ssh_username=self.come_obj.ssh_username,
                                                 ssh_password=self.come_obj.ssh_password,
                                                 ssh_port=self.come_obj.ssh_port,
                                                 name=container_name)
            """
            if "0" in container_name:  # based on logic that container names will always be F1-1, F1-0
                self.F1_0_HANDLE = container_obj
            else:
                self.F1_1_HANDLE = container_obj
            """
            self.container_info[container_name] = container_obj

        result['container_info'] = self.container_info
        result['status'] = True
        return result
        '''
        return result

    def update_fundsk(self):
        result = False
        response = self.come_obj.check_file_directory_exists(self.FUNSDK_DIR)
        if not response:
            fun_test.critical("{} dir does not exists".format(self.FUNSDK_DIR))
            return result
        self.enter_funsdk()
        # self.come_obj.command("cd {}".format(self.FUNSDK_DIR))
        self.come_obj.command("git pull", timeout=self.DEFAULT_TIMEOUT)
        if self.come_obj.exit_status() == 0:
            result = True
        return result

    def prepare_docker(self, mode, timeout=PREP_TIMEOUT):
        result = True
        self.enter_funsdk()
        prepare_cmd = self.PREPARE_CMD + "".join([" --{}".format(m) for m in mode])
        response = self.come_obj.command(prepare_cmd, timeout=timeout)
        sections = ["Cloning into 'FunSDK'",
                    "Cloning into 'fungible-host-drivers'",
                    # "Cloning into 'FunControlPlane'",
                    "Prepare End"]
        for sect in sections:
            if sect not in response:
                fun_test.critical("{} message not found in container prepare logs".format(sect))
                result = False
        return result

    def launch_funcp_containers(self, mode=None, timeout=DEPLOY_TIMEOUT):
        result = True
        response = ""
        self.enter_funsdk()
        cmd = "sudo -E {}/{}".format(self.fungible_root, self.DEPLOY_CONTAINER_CMD)
        if mode:
            cmd += "".join([" --{}".format(m) for m in mode])
            cmd = cmd + " &>{}".format(self.DOCKER_LAUNCH_OUTPUT)
        try:
            response = self.come_obj.command(cmd, timeout=timeout)
        except Exception as ex:
            fun_test.log(str(ex))
        docker_launch_status = self.come_obj.exit_status()
        fun_test.log("FunCP docker container deployment stats: {}".format(docker_launch_status))
        docker_launch_output = self.come_obj.read_file(self.DOCKER_LAUNCH_OUTPUT)

        sections = ['Discovered both F1 devices',
                    'Done with installing funeth driver',
                    'Done with installing libfunq',
                    'Bring up Control Plane',
                    'End of starting cclinux'
                    ]

        for sect in sections:
            if sect not in docker_launch_output:
                fun_test.critical("{} message not found in container deployment logs".format(sect))

        return True if not docker_launch_status else False

    def get_container_names(self, stop_run_sc=True, include_storage=False):
        result = {'status': False, 'container_name_list': []}

        # If SC docker container is not needed, kill the system_health_check.py and stop the run_sc container
        if stop_run_sc:
            health_check_pid = self.come_obj.get_process_id_by_pattern("system_health_check.py")
            if health_check_pid:
                self.come_obj.kill_process(process_id=health_check_pid)
            else:
                fun_test.critical("system_health_check.py script is not running")

            cmd = "docker ps -a --format '{{.Names}}' | grep run_sc"
            timer = FunTimer(max_time=self.DEPLOY_TIMEOUT / 2)
            while not timer.is_expired():
                container_name = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT).split("\n")[0]
                if container_name:
                    stop_cmd = "docker rm -f {}".format(container_name)
                    self.come_obj.command(stop_cmd, timeout=self.DEFAULT_TIMEOUT)
                    break
                else:
                    fun_test.sleep("for the run_sc docker to show up", 5)

        if not include_storage:
            cmd = "docker ps -a --format '{{.Names}}' | grep F1"
        else:
            cmd = "docker ps -a --format '{{.Names}}'"

        result['container_name_list'] = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT).split("\n")
        result['container_name_list'] = [name.strip("\r") for name in result['container_name_list']]
        container_count = len(result['container_name_list'])
        if not include_storage:
            expected_container_count = self.NUM_FS_CONTAINERS
        else:
            expected_container_count = self.NUM_FS_CONTAINERS + 1
        if container_count != expected_container_count:
            fun_test.critical(
                "{0} Containers should be deployed, Number of container deployed: {1}".format(expected_container_count,
                                                                                              container_count))
            return result
        else:
            result['status'] = True

        return result

    def stop_container(self, *container_names):
        result = True
        cmd = "docker stop"

        # If no container name is passed preparing the list with the container names already available in this object
        if not container_names:
            container_names = sorted(self.container_info)

        for name in container_names:
            cmd += " " + name

        # Stopping the container(s)
        stopped_container = self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT).split("\n")
        stopped_container = [name.strip("\r") for name in stopped_container]

        # Checking whether the container is not stopped or not. If not stopped the
        for name in container_names:
            if name not in stopped_container:
                fun_test.critical("Failed to stop the containter: {}".format(name))
                result = False
        return result

    """
    def clear_containers(self):
        # Stop Container F1_0
        if self.F1_0_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)
        # Stop Container F1_1
        if self.F1_1_HANDLE:
            self.stop_container(self.F1_0_HANDLE.name)

    def stop_container(self, container_name):
        cmd = "docker stop {}".format(container_name)
        self.come_obj.command(cmd, timeout=self.DEFAULT_TIMEOUT)

    def get_f10_handle(self):
        handle = None
        if self.F1_0_HANDLE:
            handle = self.F1_0_HANDLE
        return handle

    def get_f11_handle(self):
        handle = None
        if self.F1_0_HANDLE:
            handle = self.F1_0_HANDLE
        return handle
    """

    def get_funcp_docker_handle(self, container_name):
        handle = None
        if container_name in self.container_info:
            handle = self.container_info[container_name]
        return handle

    def configure_bond_interface(self, container_name, name, ip, slave_interface_list=[],
                                 bond_bringup_timeout=BOND_BRINGUP_TIMEOUT, **kwargs):
        """
        :param docker_handle:
        :param slave_interface_list:
        :param bond_dict:
        :return:

        * The user has to pass all the slave interface name which will be part of bond interface in the form list
        * Bond interface name and IP are mandatory one needs to be passed
        * The other bond properties can be passed the name=value or as a dictionary at the end
        """

        # Waiting for the DHCP discover process to begin before starting configure the bond interface
        if self.come_obj.check_file_directory_exists(self.DOCKER_LAUNCH_OUTPUT):
            cmd = "grep -c 'DHCPDISCOVER on bond' {}".format(self.DOCKER_LAUNCH_OUTPUT)
            timer = FunTimer(max_time=self.DEPLOY_TIMEOUT / 10)
            while not timer.is_expired():
                status = self.come_obj.command(cmd)
                if int(status.strip()) > 0:
                    fun_test.log("Auto DHCP discovery process started...Safe to proceed to configure bond interface")
                    break
                else:
                    fun_test.sleep("for the DHCP discover process to start", 5)

        container_obj = self.container_info[container_name]
        # Checking whether the two or more interfaces are passed to create the bond
        fun_test.simple_assert(len(slave_interface_list) >= 2, "Sufficient slave interfaces to form bond")

        bond_dict = {}
        bond_dict["name"] = name
        bond_dict["ip"] = ip

        if kwargs:
            for key in kwargs:
                bond_dict[key] = kwargs[key]

        if "mode" not in bond_dict:
            bond_dict["mode"] = "802.3ad"
        if "miimon" not in bond_dict:
            bond_dict["miimon"] = 100
        if "xmit_hash_policy" not in bond_dict:
            bond_dict["xmit_hash_policy"] = "layer3+4"
        if "min_links" not in bond_dict:
            bond_dict["min_links"] = 1

        # Disabling all the slave interfaces before adding them into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} down".format(interface_name))
            fun_test.simple_assert(not container_obj.exit_status(), "Disabling interface {}".format(interface_name))

        # Configuring the bond interface name
        bond_del_cmd = "sudo ip link del %(name)s" % bond_dict
        container_obj.command(bond_del_cmd)
        bond_cmd = "sudo ip link add %(name)s type bond mode %(mode)s miimon %(miimon)s xmit_hash_policy " \
                   "%(xmit_hash_policy)s min_links %(min_links)s" % bond_dict
        container_obj.command(bond_cmd)
        fun_test.simple_assert(not container_obj.exit_status(), "Creating bond {} interface".
                               format(bond_dict["name"]))

        # Adding slaves interfaces into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} master {}".format(interface_name, bond_dict["name"]))
            fun_test.simple_assert(not container_obj.exit_status(), "Adding interface {} into bond {}".
                                   format(interface_name, bond_dict["name"]))

        # Enabling all the slave interfaces after adding them into the bond interface
        for interface_name in slave_interface_list:
            container_obj.command("sudo ip link set {} up".format(interface_name))
            fun_test.simple_assert(not container_obj.exit_status(), "Enabling interface {}".format(interface_name))

        # Disabling the bond interface before configuring IP address to it
        bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="down")
        fun_test.simple_assert(bond_status, "Disabling {} interface".format(bond_dict["name"]))

        # Configuring IP address for the bond interface
        bond_ip_config = "sudo ip addr add %(ip)s dev %(name)s" % bond_dict
        container_obj.command(bond_ip_config)
        fun_test.simple_assert(not container_obj.exit_status(), "Configuring IP to {} interface".
                               format(bond_dict["name"]))

        # Enabling the bond interface after configuring IP address to it
        bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="up")
        fun_test.simple_assert(bond_status, "Enabling {} interface".format(bond_dict["name"]))

        # Checking whether the bond0 is UP and Running
        match = ""
        timer = FunTimer(max_time=bond_bringup_timeout)
        while not timer.is_expired():
            bond_output = container_obj.command("ifconfig {}".format(bond_dict["name"]))
            match = re.search(r'UP.*RUNNING', bond_output)
            if not match:
                fun_test.critical("{} interface is still not in running state...So going to flip it".
                                  format(bond_dict["name"]))
                bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="down")
                fun_test.sleep("Disabling {} interface".format(bond_dict["name"]), 2)
                bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="up")
                fun_test.sleep("Enabling {} interface".format(bond_dict["name"]), 2)
            else:
                break
        else:
            fun_test.simple_assert(match, "Bond {} interface is UP & RUNNING".format(bond_dict["name"]))

        # Display route and arp inside the container
        container_obj.command("ip route")
        container_obj.command("arp")

        # As a workaround for the bug SWOS-6456, checking L2 MTU of the fgp interface and setting them to 1518, if it
        # is less than that
        f1_index = int(container_name.split("-")[1])
        try:
            nc = NetworkController(dpc_server_ip=self.come_obj.host_ip,
                                   dpc_server_port=self.come_obj.get_dpc_port(f1_index))
        except Exception as ex:
            fun_test.critical("Unable to get Network Controller handle...So will not able to check & set the L2 MTU"
                              "for the FPG interfaces")
            fun_test.critical(str(ex))
            return True

        try:
            for interface_name in slave_interface_list:
                match = re.search(r"fpg(\d+)", interface_name)
                port_num = int(match.group(1))
                port_mtu = nc.get_port_mtu(port_num=port_num, shape=0)
                if port_mtu < self.FPG_L2_MTU:
                    fun_test.critical("F1_{} FPG{}'s MTU {} is less than {}...So setting it to {}".
                                      format(f1_index, port_num, port_mtu, self.FPG_L2_MTU, self.FPG_L2_MTU))
                    mtu_status = nc.set_port_mtu(port_num=port_num, mtu_value=self.FPG_L2_MTU, shape=0)
                    if mtu_status:
                        fun_test.log("Successfully the set F1_{} FPG{}'s MTU to {}".format(f1_index, port_num,
                                                                                           self.FPG_L2_MTU))
                    else:
                        fun_test.critical("Unable to set F1_{} FPG{}'s MTU to {}".format(f1_index, port_num,
                                                                                         self.FPG_L2_MTU))
                        return False
                else:
                    fun_test.log("Current MTU of F1_{} FPG {}'s is: {}".format(f1_index, port_num, port_mtu))
        except Exception as ex:
            fun_test.critical(str(ex))
            nc.disconnect()

        nc.disconnect()
        return True

    def is_bond_interface_up(self, container_name, name, bond_bringup_timeout=BOND_BRINGUP_TIMEOUT,
                             flip_interface=False, **kwargs):
        """
        :param container_name: String
        :param name: String: Interface Name
        :param bond_bringup_timeout: Integer: Timeout value
        :param kwargs: provisional for future use
        :param flip_interface: Whether to flip interface or not
        :return: Boolean: True for Success, False for Failure
        """
        result = False
        container_obj = self.container_info[container_name]
        bond_dict = {}
        bond_dict["name"] = name
        if kwargs:
            for key in kwargs:
                bond_dict[key] = kwargs[key]

        # Checking whether the bond0 is UP and Running
        match = ""
        interface_status_timer = FunTimer(max_time=bond_bringup_timeout * 2)
        while not interface_status_timer.is_expired():
            bond_output = container_obj.command("ifconfig {}".format(bond_dict["name"]))
            match = re.search(r'UP.*RUNNING', bond_output)
            if not match:
                fun_test.sleep("{} interface is still not in running state..".format(bond_dict["name"]), 10)
                fun_test.log("Remaining Time: {}\n".format(interface_status_timer.remaining_time()))
                if flip_interface:
                    fun_test.critical("Flipping {} interface".format(bond_dict["name"]))
                    bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="down")
                    fun_test.sleep("Disabling {} interface".format(bond_dict["name"]), 2)
                    bond_status = container_obj.ifconfig_up_down(interface=bond_dict["name"], action="up")
                    fun_test.sleep("Enabling {} interface".format(bond_dict["name"]), 2)
            else:
                result = True
                break
        return result
