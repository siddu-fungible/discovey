from lib.system.fun_test import *
from swagger_client.models.body_volume_attach import BodyVolumeAttach
from swagger_client.models.body_node_update import BodyNodeUpdate
from swagger_client.models.volume_types import VolumeTypes
from swagger_client.models.transport import Transport
from swagger_client.rest import ApiException
from swagger_client.models.body_drive_format import BodyDriveFormat
from swagger_client.models.node_update_op import NodeUpdateOp
from lib.templates.storage.storage_controller_api import *
from asset.asset_global import AssetType
import ipaddress
import re
import copy


class DutsState:
    def __init__(self):
        pass

    f1_states = [{"dataplane_ips": {}}, {"dataplane_ips": {}}]

    def add_dataplane_ip(self, ip, f1_index, interface_name="bond0"):
        self.f1_states[f1_index]["dataplane_ips"][interface_name] = ip

    def get_dataplane_ips(self, f1_index, interface_name="bond0"):
        return self.f1_states[f1_index][interface_name]


class HostsState:
    def __init__(self):
        pass

    hosts_states = {}

    def add_host_nvme_namespace(self, hostname, nvme_namespace):
        self.hosts_states.setdefault(hostname, []).append(nvme_namespace)

    def get_host_nvme_namespaces(self, hostname):
        result = []
        if hostname in self.hosts_states:
            result = self.hosts_states[hostname]
        return result


class StorageControllerOperationsTemplate:
    """
    Do basic API operations
    """
    def __init__(self, topology, api_logging_level=logging.DEBUG):
        self.topology = topology
        self.node_ids = []
        self.duts_state_object = DutsState()
        self.hosts_state_object = HostsState()
        self.api_logging_level = api_logging_level

    def get_health(self, fs_obj):
        result = True
        fs_obj_list = []
        if not isinstance(fs_obj, list):
            fs_obj_list.append(fs_obj)
        else:
            fs_obj_list = fs_obj
        for fs_obj in fs_obj_list:
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            dut_health = storage_controller.health()
            fun_test.add_checkpoint(expected=True, actual=dut_health,
                                    checkpoint="Check health of DUT: {}".format(fs_obj))
            result &= dut_health
        return result

    def set_dataplane_ips(self, fs_obj, dpu_indexes=None):
        if dpu_indexes is None:
            dpu_indexes = [0, 1]
        result = False

        storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
        topology_result = None
        try:
            topology_result = storage_controller.topology_api.get_hierarchical_topology()
            fun_test.log(topology_result)
        except ApiException as e:
            fun_test.critical("Exception while getting topology{}\n".format(e))
        except Exception as e:
            fun_test.critical("Exception while getting topology{}\n".format(e))
        node_ids = [x.uuid for x in topology_result.data.values()]
        fun_test.test_assert(expression=node_ids, message="Fetch node IDs using topology API")
        for node in node_ids:
            for f1_index in dpu_indexes:
                first_bond_interface = fs_obj.networking.get_bond_interface(f1_index=f1_index, interface_index=0)
                ip_obj = ipaddress.ip_network(address=unicode(first_bond_interface.ip), strict=False)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                subnet_mask = str(ip_obj.netmask)
                # TODO: Obtain next_hop from test_bed info
                next_hop = str(ip_obj.hosts().next())

                # body_node_update = BodyNodeUpdate(op=NodeUpdateOp().DPU_DP_ID, ip_assignment_dhcp=False,
                #                             next_hop=next_hop, dataplane_ip=dataplane_ip, subnet_mask=subnet_mask)

                # WORKAROUND: SWOS-8586
                body_node_update = BodyNodeUpdate(op="DPU_DP_IP", ip_assignment_dhcp=False,
                                                  next_hop=next_hop, dataplane_ip=dataplane_ip,
                                                  subnet_mask=subnet_mask)
                dpu_id = node + "." + str(f1_index)
                try:
                    assign_dataplane_ip = storage_controller.topology_api.update_dpu(
                        dpu_id=dpu_id, body_node_update=body_node_update)

                    fun_test.test_assert(expression=assign_dataplane_ip.status,
                                         message="Dataplane IP assignment on %s" % dpu_id)
                    self.duts_state_object.add_dataplane_ip(ip=dataplane_ip, f1_index=f1_index)
                    result = assign_dataplane_ip.status
                except ApiException as e:
                    fun_test.critical("Exception while updating dataplane IP {}\n".format(e))
                    result = False
                except Exception as e:
                    fun_test.critical("Exception while updating dataplane IP {}\n".format(e))
                    result = False

        return result

    def ensure_dpu_online(self, storage_controller, dpu_id, raw_api_call=False, max_wait_time=120):
        result = False
        timer = FunTimer(max_time=max_wait_time)
        while not timer.is_expired():
            if not raw_api_call:
                try:
                    dpu_result = storage_controller.topology_api.get_dpu(dpu_id=dpu_id)
                    if dpu_result.status:
                        result = True
                        break
                except ApiException as e:
                    fun_test.critical("Exception while getting DPU state{}\n".format(e))
                except Exception as e:
                    fun_test.critical("Exception while getting DPU state{}\n".format(e))
            else:
                raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
                api_result = raw_sc_api.execute_api(method="GET",
                                                    cmd_url="topology/dpus/{}/state".format(dpu_id)).json()
                if api_result['status']:
                    if api_result['data']['state'] == "Online" and api_result['data']['available']:
                        result = True
                        break
            fun_test.sleep("Waiting for DPU to be online, remaining time: %s" % timer.remaining_time(), seconds=15)
        return result

    def get_online_dpus(self, dpu_indexes):
        """
        Find the number of DPUs online using API
        :return: Returns the number of DPUs online
        """
        result = 0
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            topology_result = None
            try:
                topology_result = storage_controller.topology_api.get_hierarchical_topology()
            except ApiException as e:
                fun_test.critical("Exception while getting topology{}\n".format(e))
            except Exception as e:
                fun_test.critical("Exception while getting topology{}\n".format(e))
            self.node_ids = [x.uuid for x in topology_result.data.values()]
            fun_test.test_assert(expression=self.node_ids, message="Fetch node IDs using topology API")
            for node in self.node_ids:

                for f1_index in dpu_indexes:
                    dpu_id = node + "." + str(f1_index)
                    dpu_status = self.ensure_dpu_online(storage_controller=storage_controller,
                                                        dpu_id=dpu_id, raw_api_call=True)
                    fun_test.add_checkpoint(expected=True, actual=dpu_status,
                                            checkpoint="DPU {} is online".format(dpu_id))
                    if dpu_status:
                        result += 1

        return result

    def verify_dataplane_ip(self, storage_controller, fs_obj, raw_api_call=True):
        result = True

        for node in self.node_ids:
            for f1_index in range(fs_obj.NUM_F1S):
                dpu_id = node + "." + str(f1_index)
                first_bond_interface = fs_obj.networking.get_bond_interface(f1_index=f1_index, interface_index=0)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                if raw_api_call:
                    raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
                    result_api = raw_sc_api.execute_api(method="GET", cmd_url="topology/dpus/{}".format(dpu_id)).json()
                    fun_test.test_assert(expression=result_api["status"], message="Fetch dataplane IP using Raw API")
                    result &= (str(result_api["data"]["dataplane_ip"]) == str(dataplane_ip))
                else:
                    get_dpu = None
                    try:
                        get_dpu = storage_controller.topology_api.get_dpu(dpu_id=dpu_id)
                    except ApiException as e:
                        fun_test.critical("Exception while getting DPU: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while getting DPU: {}\n".format(e))
                    fun_test.test_assert(expression=get_dpu, message="Fetch dataplane IP")
                    result &= (str(get_dpu.dataplane_ip) == str(dataplane_ip))
        return result

    def format_all_drives(self, fs_obj):
        storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
        topology = None
        try:
            topology = storage_controller.topology_api.get_hierarchical_topology()
        except ApiException as e:
            fun_test.critical("Exception while getting topology: {}\n".format(e))
        except Exception as e:
            fun_test.critical("Exception while getting topology: {}\n".format(e))
        for node in topology.data:
            for dpu in topology.data[node].dpus:
                for drive_info in dpu.drives:
                    fun_test.test_assert(self._format_drive(
                        drive_info=drive_info, storage_controller=storage_controller),
                        message="Formatting drive {}".format(drive_info.uuid))

    def _format_drive(self, drive_info, storage_controller, raw_api_call=False):
        result = False
        if raw_api_call:
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            format_drive = raw_sc_api.execute_api(method="PUT", cmd_url="topology/drives/{}".format(drive_info.uuid),
                                                  data={}).json()
            result = format_drive["status"]
        else:
            body_drive_format = BodyDriveFormat(dpu_id=drive_info.dpu, nguid_low=drive_info.nguid_low,
                                                nguid_high=drive_info.nguid_high, slot_id=drive_info.slot_id,
                                                fault_zones=drive_info.fault_zone, capacity=drive_info.capacity)
            format_drive = None
            try:
                format_drive = storage_controller.topology_api.format_drive_change_uuid(
                    drive_uuid=drive_info.uuid, body_drive_format=body_drive_format)
            except ApiException as e:
                fun_test.critical(message="ApiException Cannot format drive {}. Error:{}".format(drive_info.uuid, e))
            except Exception as e:
                fun_test.critical(message="Cannot format drive {}. Error:{}".format(drive_info.uuid, e))
            if format_drive:
                result = True
        return result

    def initialize(self, already_deployed=False, dpu_indexes=None, format_drives=True):
        if not already_deployed:
            already_deployed = fun_test.get_job_environment_variable("already_deployed")
        if dpu_indexes is None:
            dpu_indexes = [0, 1]
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            # pass fs_obj instead of dut info | Cant get bond interface using fs_obj..
            fun_test.test_assert(self.get_health(fs_obj=fs_obj),
                                 message="DUT: {} Health of API server".format(dut_index))
            if not already_deployed:
                fun_test.sleep(message="Wait before sending dataplane IP commands", seconds=60)  # WORKAROUND
                fun_test.test_assert(self.set_dataplane_ips(fs_obj=fs_obj, dpu_indexes=dpu_indexes),
                                     message="DUT: {} Assign dataplane IP".format(dut_index))
            num_dpus = len(dpu_indexes)
            fun_test.test_assert_expected(expected=num_dpus, actual=self.get_online_dpus(dpu_indexes=dpu_indexes),
                                          message="Make sure {} DPUs are online".format(num_dpus))
            if not already_deployed and format_drives:
                self.format_all_drives(fs_obj=fs_obj)

    def cleanup(self):
        pass
        # check with storage team


class GenericVolumeOperationsTemplate(StorageControllerOperationsTemplate, object):
    """
    This template abstracts the operations of all kinds of volumes.
    Extend this to define new volume templates
    """
    vol_type = VolumeTypes().LOCAL_THIN
    host_nvme_device = {}
    NVME_HOST_MODULES = ["nvme_core", "nvme", "nvme_fabrics", "nvme_tcp"]

    def __init__(self, topology, **kwargs):
        super(GenericVolumeOperationsTemplate, self).__init__(topology, **kwargs)
        self.topology = topology

    def create_volume(self, fs_obj, body_volume_intent_create):
        """
        Create a volume for each fs_obj in fs_obj_list
        :param fs_obj: List of fs objects
        :param body_volume_intent_create: object of class BodyVolumeIntentCreate with volume details
        :return: List of vol_uuids in same order as fs_obj
        """
        result = []
        fs_obj_list = []
        if not isinstance(fs_obj, list):
            fs_obj_list.append(fs_obj)
        else:
            fs_obj_list = fs_obj
        for fs_index, fs_obj in enumerate(fs_obj_list):

            if len(fs_obj_list) > 1:
                body_volume_intent_create.name = body_volume_intent_create.name + str(fs_index)

            body_volume_intent_create.vol_type = self.vol_type
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            try:
                create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
                vol_uuid = create_vol_result.data.uuid
                result.append(vol_uuid)
            except ApiException as e:
                fun_test.critical("Exception when creating volume on fs {}: {}\n" .format(fs_obj, e))
            except Exception as e:
                fun_test.critical("Exception when creating volume on fs {}: {}\n" .format(fs_obj, e))
        return result

    def attach_volume(self, fs_obj, volume_uuid, host_obj, validate_nvme_connect=True, raw_api_call=False,
                      nvme_io_queues=None):

        """
        :param fs_obj: fs_object from topology
        :param volume_uuid: uuid of volume returned after creating volume
        :param host_obj: host handle or list of host handles from topology to which the volume needs to be attached
        :param validate_nvme_connect: Use this flag to do NVMe connect from host along with attaching volume
        :param raw_api_call: Temporary workaround to use raw API call until swagger APi issues are resolved.
        :param nvme_io_queues: No of IO queues for NVMe connect command
        :return: Attach volume result in case of 1 host_obj
                 If multiple host_obj are provided, the result is a list of attach operation results,
                 in the same order of host_obj
        """
        result_list = []
        host_obj_list = []
        if not isinstance(host_obj, list):
            host_obj_list.append(host_obj)
        else:
            host_obj_list = host_obj
        for cur_host_obj in host_obj_list:
            if cur_host_obj not in self.host_nvme_device:
                self.host_nvme_device[cur_host_obj] = []
            fun_test.add_checkpoint(checkpoint="Attaching volume %s to host %s" % (volume_uuid, cur_host_obj.name))
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            host_data_ip = cur_host_obj.get_test_interface(index=0).ip.split('/')[0]
            if not raw_api_call:
                attach_fields = BodyVolumeAttach(transport=Transport().TCP,
                                                 host_nqn="nqn.2015-09.com.Fungible:{}".format(host_data_ip))

                try:
                    result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                                          body_volume_attach=attach_fields)
                    result_list.append(result)
                except ApiException as e:
                    fun_test.test_assert(expression=False,
                                         message="Exception when attach volume on fs {}: {}\n".format(fs_obj, e))
                    result = None
                except Exception as e:
                    fun_test.test_assert(expression=False,
                                         message="Exception when attach volume on fs {}: {}\n".format(fs_obj, e))
                    result = None
            else:
                raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
                result = raw_sc_api.volume_attach_remote(vol_uuid=volume_uuid,
                                                         host_nqn="nqn.2015-09.com.Fungible:{}".format(host_data_ip))
                result_list.append(result)
            if validate_nvme_connect:
                if raw_api_call:
                    fun_test.test_assert(expression=result["status"], message="Attach volume result")
                    subsys_nqn = result["data"]["subsys_nqn"]
                    host_nqn = result["data"]["host_nqn"]
                    dataplane_ip = result["data"]["ip"]
                    nsid = result["data"]["nsid"]
                else:
                    subsys_nqn = result.subsys_nqn
                    host_nqn = result.host_nqn
                    dataplane_ip = result.ip
                    nsid = result.nsid
                if not self._check_host_target_existing_connection(fs_obj=fs_obj, volume_uuid=volume_uuid,
                                                                   subsys_nqn=subsys_nqn, host_nqn=host_nqn,
                                                                   host_obj=cur_host_obj):
                    fun_test.test_assert(expression=self.nvme_connect_from_host(host_obj=cur_host_obj,
                                                                                subsys_nqn=subsys_nqn,
                                                                                host_nqn=host_nqn,
                                                                                dataplane_ip=dataplane_ip,
                                                                                nvme_io_queues=nvme_io_queues),
                                         message="NVMe connect from host: {}".format(cur_host_obj.name))
                else:
                    fun_test.log("Skipping NVMe connect, because connection from host: {host} exists for "
                                 "subsys-nqn: {subsys_nqn} and host-nqn: {host_nqn}".format(host=cur_host_obj.name,
                                                                                            subsys_nqn=subsys_nqn,
                                                                                            host_nqn=host_nqn))

                if cur_host_obj not in self.host_nvme_device:
                    self.host_nvme_device[cur_host_obj] = []
                nvme_filename = self.get_host_nvme_device(host_obj=cur_host_obj, subsys_nqn=subsys_nqn, nsid=nsid)
                fun_test.test_assert(expression=nvme_filename,
                                     message="Get NVMe drive from Host {} using nvme list".format(cur_host_obj.name))
                self.hosts_state_object.add_host_nvme_namespace(hostname=cur_host_obj.name, nvme_namespace=nvme_filename)
        if isinstance(host_obj, list):
            result = result_list
        else:
            result = result_list[0]
        return result

    def _check_host_target_existing_connection(self, fs_obj, volume_uuid, subsys_nqn, host_nqn, host_obj):
        result = False
        storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
        # get_volume_result = storage_controller.storage_api.get_volumes()
        # WORKAROUND : get_volumes errors out.
        raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
        get_volume_result = raw_sc_api.get_volumes()
        fun_test.test_assert(message="Get volume details", expression=get_volume_result["status"])
        for vol_uuid in get_volume_result['data']:
            if result:
                break
            if vol_uuid == volume_uuid:
                continue
            if subsys_nqn == get_volume_result['data'][vol_uuid]['subsys_nqn']:
                for port in get_volume_result["data"][vol_uuid]["ports"]:
                    if result:
                        break
                    port_details = None
                    try:
                        port_details = storage_controller.storage_api.get_port(port_uuid=port)
                    except ApiException as e:
                        fun_test.critical("Exception while getting port info: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while getting port info: {}\n".format(e))
                    if port_details.data.host_nqn == host_nqn:

                        host_handle = host_obj.get_instance()
                        nvme_volumes = self._get_fungible_nvme_namespaces(host_handle=host_obj.get_instance())
                        if nvme_volumes:
                            for namespace in nvme_volumes:
                                namespace_subsys_nqn = self._get_nvme_subsysnqn_by_namespace(
                                    host_handle=host_handle, namespace=namespace)
                                if namespace_subsys_nqn == str(subsys_nqn):
                                    result = True
                                    break
        return result

    def attach_m_vol_n_host(self, fs_obj, volume_uuid_list, host_obj_list, validate_nvme_connect=True,
                            raw_api_call=False, nvme_io_queues=None, volume_is_shared=False):
        """
        :param fs_obj: fs_object from topology
        :param volume_uuid_list: list of volumes to be attached
        :param host_obj_list: list of host handles from topology to which the volume needs to be attached
        :param validate_nvme_connect: Use this flag to do NVMe connect from host along with attaching volume
        :param raw_api_call: Temporary workaround to use raw API call until swagger APi issues are resolved.
        :param volume_is_shared: True indicates volume not shared between hosts
        :return: Attach volume result in case of 1 host_obj
                 If multiple host_obj are provided, the result is a list of attach operation results,
                 in the same order of host_obj
                """
        """
        The function attaches volume from param volume_uuid_list to host in param host_obj_list based on
        param volume_is_shared provided by user. If volume is to be shared among hosts then user needs to 
        set it to volume_is_shared true

        case1: set volume_is_shared=False when one vol is attached to one host
        eg: 12 vol on 12 different host

        case2: set volume_is_shared=True when one vol is shared among multiple hosts
        eg: 3 vols shared among 3 hosts

        case3: set volume_is_shared=False when num hosts < num volumes and volumes are not shared
        eg: 8 vols on 2 hosts such that each host has 4 volumes attached

        case4: set volume_is_shared=True when num hosts < num volumes and volumes are to be shared among hosts
        eg: 8 vols on 2 hosts such that each host has 8 volumes attached

        return-type: dict
        :returns dictionary with host objects as keys with list as value containing API response

        result = {<lib.topology.host.Host instance at 0x10e753d88>: 
            [{u'status': True, u'message': u'Attach Success', u'warning': u'', 
            u'data': {u'uuid': u'd2c3c947fef0480c', u'nsid': 1, u'host_nqn': 
            u'nqn.2015-09.com.Fungible:15.1.14.2', u'ip': u'15.104.1.2', 
            u'subsys_nqn': u'nqn.2015-09.com.fungible:FS1.0', u'transport': u'TCP', 
            u'remote_ip': u'0.0.0.0'}, u'error_message': u''}], 
        <lib.topology.host.Host instance at 0x10e579518>: 
            [{u'status': True, u'message': u'Attach Success', u'warning': u'', 
            u'data': {u'uuid': u'01b52e9650ad4643', u'nsid': 2, u'host_nqn':
            u'nqn.2015-09.com.Fungible:15.1.13.2', u'ip': u'15.104.1.2', 
            u'subsys_nqn': u'nqn.2015-09.com.fungible:FS1.0', u'transport': u'TCP',
             u'remote_ip': u'0.0.0.0'}, u'error_message': u''}]}
        """
        result = {}
        try:
            temp_volume_uuid_list = []
            temp_host_obj_list = []
            temp_volume_uuid_list.extend(x for x in volume_uuid_list)
            temp_host_obj_list.extend(x for x in host_obj_list)
            if volume_is_shared:
                # when volumes are shared among hosts
                temp_host_obj_list = temp_host_obj_list * len(temp_volume_uuid_list)
                for i in range(1, len(host_obj_list)):
                    temp_volume_uuid_list.extend(volume_uuid_list[i:] + volume_uuid_list[:i])
            else:
                if len(temp_host_obj_list) < len(temp_volume_uuid_list):
                    # when volumes are attached in round robin fashion
                    fun_test.log("Num volumes to attach is {} and num hosts is {} and volume_is_shared is False. "
                                 "So attaching volumes in round robin fashion".format(len(temp_volume_uuid_list),
                                                                                      len(temp_host_obj_list)))
                    for i in range(len(host_obj_list), len(volume_uuid_list)):
                        temp_host_obj_list.append(temp_host_obj_list[i % len(host_obj_list)])

                elif len(temp_host_obj_list) > len(temp_volume_uuid_list):
                    # when volumes are attached in round robin fashion
                    fun_test.log("Num volumes to attach is {} and num hosts is {} and volume_is_shared is False. "
                                 "So attaching volumes in round robin fashion".format(len(temp_volume_uuid_list),
                                                                                      len(temp_host_obj_list)))
                    for i in range(len(volume_uuid_list), len(host_obj_list)):
                        temp_volume_uuid_list.append(temp_volume_uuid_list[i % len(volume_uuid_list)])

            for index in range(len(temp_host_obj_list)):
                if not temp_host_obj_list[index] in result.keys():
                    result[temp_host_obj_list[index]] = []
                fun_test.log("Attaching {} volume to {} host".format(temp_volume_uuid_list[index],
                                                                     temp_host_obj_list[index].name))
                output = self.attach_volume(fs_obj=fs_obj, volume_uuid=temp_volume_uuid_list[index],
                                            host_obj=temp_host_obj_list[index],
                                            validate_nvme_connect=validate_nvme_connect, raw_api_call=raw_api_call,
                                            nvme_io_queues=nvme_io_queues)
                fun_test.test_assert(output["status"],
                                     message="Attach volume {} to host {}".format(temp_volume_uuid_list[index],
                                                                                  temp_host_obj_list[index].name))
                result[temp_host_obj_list[index]].append(output)
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def nvme_connect_from_host(self, host_obj, subsys_nqn, host_nqn, dataplane_ip,
                               transport_type='tcp', transport_port=4420, nvme_io_queues=None):
        """

        :param host_obj: host handle from topology
        :param subsys_nqn: returned after volume attach
        :param host_nqn: returned after volume attach
        :param dataplane_ip: IP of FS1600 reachable from host returned after volume attach
        :param nvme_io_queues: no of queues for nvme connect
        :param transport_type: NVMe connect transport
        :param transport_port: Port no to connect for NVMe TCP
        :return: output of nvme connect command
        """
        host_linux_handle = host_obj.get_instance()
        for driver in self.NVME_HOST_MODULES:
            # if not host_linux_handle.lsmod(module=driver):
            host_linux_handle.modprobe(driver)

        fun_test.test_assert(expression=host_linux_handle.ping(dst=dataplane_ip), message="Ping datapalne IP from Host")
        nvme_connect_command = host_linux_handle.nvme_connect(target_ip=dataplane_ip, nvme_subsystem=subsys_nqn,
                                                              port=transport_port, transport=transport_type,
                                                              nvme_io_queues=nvme_io_queues, hostnqn=host_nqn)
        return nvme_connect_command

    def get_host_nvme_device(self, host_obj, subsys_nqn=None, nsid=None):
        """

        :param host_obj: host handle from topology
        :param subsys_nqn: subsys_nqn to find the correct nvme filename
        :return: NVMe device name on Host or list of devices if susys_nqn is None
        """
        result = None
        host_linux_handle = host_obj.get_instance()
        self.get_nvme_namespaces_by_lsblk(host_handle=host_linux_handle)
        nvme_volumes = self._get_fungible_nvme_namespaces(host_handle=host_linux_handle)
        result = nvme_volumes
        if nvme_volumes:
            if len(nvme_volumes) > 0:
                if subsys_nqn:
                    for namespace in nvme_volumes:
                        namespace_subsys_nqn = self._get_nvme_subsysnqn_by_namespace(
                            host_handle=host_linux_handle, namespace=namespace)
                        if namespace_subsys_nqn == str(subsys_nqn):
                            if nsid:
                                if str(nsid) == str(host_linux_handle.nvme_get_ns_id(namespace=namespace)):
                                    result = namespace
                            else:
                                result = namespace
                                self.host_nvme_device[host_obj].append(namespace)

        return result

    def traffic_from_host(self, host_obj, filename, job_name="Fungible_nvmeof", numjobs=1, iodepth=1,
                          rw="readwrite", runtime=60, bs="4k", ioengine="libaio", direct=1,
                          time_based=True, norandommap=True, verify=None, do_verify=None):
        host_linux_handle = host_obj.get_instance()
        fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw=rw,
                                           filename=filename, runtime=runtime, ioengine=ioengine, direct=direct,
                                           timeout=runtime + 15, time_based=time_based, norandommap=norandommap,
                                           verify=verify, do_verify=do_verify)
        return fio_result

    def get_nvme_namespaces_by_lsblk(self, host_handle):
        lsblk_output = host_handle.lsblk(options="-b")
        nvme_volumes = []
        for volume_name in lsblk_output:
            if re.search("nvme", volume_name):
                nvme_volumes.append(volume_name)
        return nvme_volumes

    def _get_nvme_subsysnqn_by_namespace(self, host_handle, namespace):
        result = None
        nvme_id_ctrl = host_handle.nvme_id_ctrl(namespace=namespace)
        if 'subnqn' in nvme_id_ctrl:
            result = nvme_id_ctrl['subnqn']
        return result

    def _get_nvme_subsysnqn_by_device(self, host_handle, nvme_device):
        namespace_subsys_nqn = host_handle.command("cat /sys/class/nvme/{}/subsysnqn".format(nvme_device))
        return str(namespace_subsys_nqn).strip()

    def _get_nvme_device_namespace(self, namespace):
        result = None
        if "/dev/" in namespace:
            nvme_device = namespace[:-2].split('/dev/')[1]
        else:
            nvme_device = namespace[:-2]
        if nvme_device.split("nvme")[0] == '' and nvme_device.split("nvme")[1].isdigit():
            result = nvme_device
        return result

    def _get_fungible_nvme_namespaces(self, host_handle):
        # WORKAROUND - SWOS-8804
        result = None
        nvme_list_raw = host_handle.nvme_list(json_output=True)
        if nvme_list_raw:
            # This is used due to the error lines printed in json output
            if not nvme_list_raw.startswith("{"):
                nvme_list_raw = nvme_list_raw + "}"
                temp1 = nvme_list_raw.replace('\n', '')
                temp2 = re.search(r'{.*', temp1).group()
                nvme_list_dict = json.loads(temp2, strict=False)
            else:
                try:
                    nvme_list_dict = json.loads(nvme_list_raw)
                except:
                    nvme_list_raw = nvme_list_raw + "}"
                    nvme_list_dict = json.loads(nvme_list_raw, strict=False)
            try:
                nvme_device_list = []
                for device in nvme_list_dict["Devices"]:
                    if ("Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"] or "fs1600" in
                            device["ModelNumber"].lower()):
                        if "NameSpace" in device and device["NameSpace"] > 0:
                            nvme_device_list.append(device["DevicePath"])
                        elif "NameSpace" not in device:
                            nvme_device_list.append(device["DevicePath"])
                if nvme_device_list:
                    result = nvme_device_list
            except:
                fun_test.critical(message="Cannot find Fungible NVMe devices")
        return result

    def get_volume_attach_status(self, fs_obj, volume_uuid):
        result = False
        storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
        all_pools = None
        try:
            all_pools = storage_controller.storage_api.get_all_pools()
            for pool in all_pools.data:
                if result:
                    break
                for volume in all_pools.data[pool].volumes:
                    if volume == volume_uuid:
                        result = True
                        break
        except ApiException as e:
            fun_test.critical("Exception while getting port info: {}\n".format(e))
            result = False
        except Exception as e:
            fun_test.critical("Exception while getting port info: {}\n".format(e))
            result = False
        return result

    def deploy(self):
        fun_test.critical(message="Deploy is not available for BLT volume template")

    def initialize(self, already_deployed=False, dpu_indexes=None, format_drives=True):
        super(GenericVolumeOperationsTemplate, self).initialize(already_deployed=already_deployed,
                                                                dpu_indexes=dpu_indexes,
                                                                format_drives=format_drives)

    def host_diagnostics(self, host_obj):

        dmesg_output = host_obj.dmesg()

        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):
                first_bond_interface = fs_obj.networking.get_bond_interface(f1_index=f1_index, interface_index=0)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                fun_test.add_checkpoint(expected=True, actual=host_obj.ping(dataplane_ip),
                                        checkpoint="{host} can ping FS {fs_name} F1_{f1_index} dataplane IP"
                                        .format(host=host_obj, fs_name=fs_obj, f1_index=f1_index))

        artifact_file_name = fun_test.get_test_case_artifact_file_name(
            "host_{}_dmesg.txt".format(host_obj))
        with open(artifact_file_name, "w") as diag_file:
            diag_file.write(dmesg_output)
            diag_file.write("\n")

        fun_test.add_auxillary_file(description="Host {} dmesg".format(host_obj), filename=artifact_file_name)

    def fs_diagnostics(self, fs_obj):
        for f1_index in range(fs_obj.NUM_F1S):
            f1_container = fs_obj.get_funcp_container(f1_index=f1_index)  # Get funcp container is not working
            ifconfig = f1_container.ifconfig()
            arp = f1_container.command("arp -n")
            route = f1_container.command("route -n")
            artifact_file_name = fun_test.get_test_case_artifact_file_name(
                "{}_F1_{}_container_stats.txt".format(fs_obj, f1_index))
            # make a list
            with open(artifact_file_name, "w") as diag_file:
                diag_file.write(ifconfig)
                diag_file.write("\n")
                diag_file.write(arp)
                diag_file.write("\n")
                diag_file.write(route)
                diag_file.write("\n")
            # f1_container.ping()  # How to ping default gateway?

    def diagnostics(self):

        for host_obj in self.host_nvme_device:
            host_handle = host_obj.get_instance()
            self.host_diagnostics(host_obj=host_handle)

        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            # self.fs_diagnostics(fs_obj=fs_obj)

    def cleanup(self, test_result_failed=False):
        """
        Kill all FIO instances on Host
        NVMe disconnect from Host
        rmmod and modprobe nvme drivers
        Detach volumes from FS
        Delete created volumes
        :return:
        """
        if test_result_failed:

            self.diagnostics()
        for host_obj in self.topology.get_available_host_instances():
            host_handle = host_obj.get_instance()
            host_handle.sudo_command("killall fio")
            fun_test.add_checkpoint(checkpoint="Kill any running FIO processes")
            disconnected_nvme_devices = []
            host_namespaces = self.hosts_state_object.get_host_nvme_namespaces(hostname=host_obj.name)
            for nvme_namespace in self.hosts_state_object.get_host_nvme_namespaces(hostname=host_obj.name):
                nvme_device = self._get_nvme_device_namespace(namespace=nvme_namespace)
                if nvme_device and nvme_device not in disconnected_nvme_devices:
                    host_handle.nvme_disconnect(device=nvme_device)
                    fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                            format(nvme_device, host_obj.name))
                    disconnected_nvme_devices.append(nvme_device)

            for driver in self.NVME_HOST_MODULES[::-1]:
                host_handle.sudo_command("rmmod {}".format(driver))
            fun_test.add_checkpoint(checkpoint="Unload all NVMe drivers")

            for driver in self.NVME_HOST_MODULES:
                host_handle.modprobe(driver)
                fun_test.add_checkpoint(checkpoint="Reload all NVMe drivers")

        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller(api_logging_level=self.api_logging_level)
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                for port in get_volume_result["data"][volume]["ports"]:
                    detach_volume = None
                    try:
                        detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    except ApiException as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    detach_result = False
                    if detach_volume:
                        detach_result = detach_volume.status
                    fun_test.add_checkpoint(expected=True, actual=detach_result,
                                            checkpoint="Detach Volume {} from host with host_nqn {}".format(
                                                volume, get_volume_result["data"][volume]['ports'][port]['host_nqn']))
                delete_volume = None
                try:
                    delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                except ApiException as e:
                    fun_test.critical("Exception while detaching volume: {}\n".format(e))
                except Exception as e:
                    fun_test.critical("Exception while detaching volume: {}\n".format(e))
                delete_volume_result = False
                if delete_volume:
                    delete_volume_result = delete_volume.status
                fun_test.add_checkpoint(expected=True, actual=delete_volume_result,
                                        checkpoint="Delete Volume {}".format(volume))

        super(GenericVolumeOperationsTemplate, self).cleanup()


class BltVolumeOperationsTemplate(GenericVolumeOperationsTemplate, object):
    """
    This template abstracts the operations of BLT volume
    """
    vol_type = VolumeTypes().LOCAL_THIN


class EcVolumeOperationsTemplate(GenericVolumeOperationsTemplate, object):
    """
    This template abstracts the operations of EC volume
    """
    vol_type = VolumeTypes().EC


if __name__ == "__main__":
    BltVolumeOperationsTemplate(None, api_logging_level=logging.ERROR)