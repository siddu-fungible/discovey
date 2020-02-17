from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from swagger_client.models.body_volume_attach import BodyVolumeAttach
from swagger_client.models.body_node_update import BodyNodeUpdate
from swagger_client.models.volume_types import VolumeTypes
from swagger_client.models.transport import Transport
from swagger_client.rest import ApiException
from swagger_client.models.node_update_op import NodeUpdateOp
from lib.templates.storage.storage_controller_api import *
import ipaddress
import re
import copy


class StorageControllerOperationsTemplate():
    """
    Do basic API operations
    """
    def __init__(self, topology):
        self.topology = topology
        self.node_ids = []

    def get_health(self, storage_controller):
        return storage_controller.health()

    def set_dataplane_ips(self, storage_controller, dut_index, dpu_indexes=None):
        if dpu_indexes is None:
            dpu_indexes = [0, 1]
        result = False
        topology_result = None
        try:
            topology_result = storage_controller.topology_api.get_hierarchical_topology()
            fun_test.log(topology_result)
        except ApiException as e:
            fun_test.critical("Exception while getting topology%s\n" % e)

        self.node_ids = [x.uuid for x in topology_result.data.values()]

        for node in self.node_ids:
            dut = self.topology.get_dut(index=dut_index)
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            for f1_index in dpu_indexes:

                bond_interfaces = dut.get_bond_interfaces(f1_index=f1_index)
                fun_test.test_assert(expression=bond_interfaces, message="Bond interface info found")

                first_bond_interface = bond_interfaces[0]
                ip_obj = ipaddress.ip_network(address=unicode(first_bond_interface.ip), strict=False)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                subnet_mask = str(ip_obj.netmask)
                # TODO: Obtain next_hop from test_bed info
                next_hop = str(ip_obj.hosts().next())

                # body_node_update = BodyNodeUpdate(op=NodeUpdateOp().DPU_DP_ID, ip_assignment_dhcp=False,
                #                                 next_hop=next_hop, dataplane_ip=dataplane_ip, subnet_mask=subnet_mask)

                # WORKAROUND: SWOS-8586
                body_node_update = BodyNodeUpdate(op="DPU_DP_IP", ip_assignment_dhcp=False,
                                                  next_hop=next_hop, dataplane_ip=dataplane_ip, subnet_mask=subnet_mask)
                dpu_id = node + "." + str(f1_index)
                try:
                    assign_dataplane_ip = storage_controller.topology_api.update_dpu(
                        dpu_id=dpu_id, body_node_update=body_node_update)

                    fun_test.test_assert(expression=assign_dataplane_ip.status,
                                         message="Dataplane IP assignment on %s" % dpu_id)
                    result = assign_dataplane_ip.status
                except ApiException as e:
                    fun_test.critical("Exception while updating Dataplane IP %s\n" % e)
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
                    fun_test.critical("Exception while getting DPU state%s\n" % e)
            else:
                raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
                result = raw_sc_api.execute_api(method="GET", cmd_url="topology/dpus/{}/state".format(dpu_id)).json()
                if result['status']:
                    if result['data']['state'] == "Online" and result['data']['available']:
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
            storage_controller = fs_obj.get_storage_controller()
            topology_result = None
            try:
                topology_result = storage_controller.topology_api.get_hierarchical_topology()
            except ApiException as e:
                fun_test.critical("Exception while getting topology%s\n" % e)
            self.node_ids = [x.uuid for x in topology_result.data.values()]

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

    def initialize(self, already_deployed=False, dpu_indexes=None):
        if dpu_indexes is None:
            dpu_indexes = [0, 1]        
        for dut_index in self.topology.get_available_duts().keys():
            fs = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs.get_storage_controller()
            fun_test.test_assert(self.get_health(storage_controller=storage_controller),
                                 message="DUT: {} Health of API server".format(dut_index))
            if not already_deployed:
                fun_test.sleep(message="Wait before firing Dataplane IP commands", seconds=60)
                fun_test.test_assert(self.set_dataplane_ips(dut_index=dut_index, storage_controller=storage_controller,
                                                            dpu_indexes=dpu_indexes),
                                     message="DUT: {} Assign dataplane IP".format(dut_index))
            num_dpus = len(dpu_indexes)
            fun_test.test_assert_expected(expected=num_dpus, actual=self.get_online_dpus(dpu_indexes=dpu_indexes),
                                          message="Make sure {} DPUs are online".format(num_dpus))

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

    def __init__(self, topology):
        super(GenericVolumeOperationsTemplate, self).__init__(topology)
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
            storage_controller = fs_obj.get_storage_controller()
            try:
                create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
                vol_uuid = create_vol_result.data.uuid
                result.append(vol_uuid)
            except ApiException as e:
                fun_test.critical("Exception when creating volume on fs %s: %s\n" % (fs_obj, e))
        return result

    def attach_volume(self, fs_obj, volume_uuid, host_obj, validate_nvme_connect=True, raw_api_call=False,
                      nvme_io_queues=None):

        """
        :param fs_obj: fs_object from topology
        :param volume_uuid: uuid of volume returned after creating volume
        :param host_obj: host handle or list of host handles from topology to which the volume needs to be attached
        :param validate_nvme_connect: Use this flag to do NVMe connect from host along with attaching volume
        :param raw_api_call: Temporary workaround to use raw API call until swagger APi issues are resolved.
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
        for host_obj in host_obj_list:
            if host_obj not in self.host_nvme_device:
                self.host_nvme_device[host_obj] = []
            fun_test.add_checkpoint(checkpoint="Attaching volume %s to host %s" % (volume_uuid, host_obj.name))
            storage_controller = fs_obj.get_storage_controller()
            host_data_ip = host_obj.get_test_interface(index=0).ip.split('/')[0]
            if not raw_api_call:
                attach_fields = BodyVolumeAttach(transport=Transport().TCP,
                                                 host_nqn="nqn.2015-09.com.Fungible:{}".format(host_data_ip))

                try:
                    result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                                          body_volume_attach=attach_fields)
                    result_list.append(result)
                except ApiException as e:
                    fun_test.test_assert(expression=False,
                                         message="Exception when attach volume on fs %s: %s\n" % (fs_obj, e))
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
                else:
                    subsys_nqn = result.subsys_nqn
                    host_nqn = result.host_nqn
                    dataplane_ip = result.ip

                fun_test.test_assert(expression=self.nvme_connect_from_host(host_obj=host_obj, subsys_nqn=subsys_nqn,
                                                                            host_nqn=host_nqn, dataplane_ip=dataplane_ip,
                                                                            nvme_io_queues=nvme_io_queues),
                                     message="NVMe connect from host: {}".format(host_obj.name))
                nvme_filename = self.get_host_nvme_device(host_obj=host_obj, subsys_nqn=subsys_nqn)
                fun_test.test_assert(expression=nvme_filename,
                                     message="Get NVMe drive from Host {} using lsblk".format(host_obj.name))
        if isinstance(host_obj, list):
            result = result_list[0]
        else:
            result = result_list
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
                fun_test.test_assert(output[0]["status"],
                                     message="Attach volume {} to host {}".format(temp_volume_uuid_list[index],
                                                                                  temp_host_obj_list[index].name))
                result[temp_host_obj_list[index]].append(output[0])
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

    def get_host_nvme_device(self, host_obj, subsys_nqn=None):
        """

        :param host_obj: host handle from topology
        :param subsys_nqn: subsys_nqn to find the correct nvme filename
        :return: NVMe device name on Host or list of devices if susys_nqn is None
        """
        result = None
        host_linux_handle = host_obj.get_instance()
        nvme_volumes = self.get_nvme_namespaces(host_handle=host_linux_handle)
        result = nvme_volumes
        if len(nvme_volumes) > 0:
            if subsys_nqn:
                for namespace in nvme_volumes:
                    nvme_device = namespace[:-2]
                    namespace_subsys_nqn = host_linux_handle.command("cat /sys/class/nvme/{}/subsysnqn".format(
                        nvme_device))
                    if str(namespace_subsys_nqn).strip() == str(subsys_nqn):
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

    def get_nvme_namespaces(self, host_handle):
        lsblk_output = host_handle.lsblk(options="-b")
        nvme_volumes = []
        for volume_name in lsblk_output:
            if re.search("nvme", volume_name):
                nvme_volumes.append(volume_name)
        return nvme_volumes

    def deploy(self):
        fun_test.critical(message="Deploy is not available for BLT volume template")

    def initialize(self, already_deployed=False, dpu_indexes=None):
        super(GenericVolumeOperationsTemplate, self).initialize(already_deployed=already_deployed,
                                                                dpu_indexes=dpu_indexes)

    def cleanup(self):
        """
        Kill all FIO instances on Host
        NVMe disconnect from Host
        rmmod and modprobe nvme drivers
        Detach volumes from FS
        Delete created volumes
        :return:
        """
        for host_obj in self.host_nvme_device:
            host_handle = host_obj.get_instance()
            host_handle.sudo_command("killall fio")
            fun_test.add_checkpoint(checkpoint="Kill any running FIO processes")
            for nvme_namespace in self.host_nvme_device[host_obj]:
                nvme_device = nvme_namespace[:-2]
                if nvme_device:
                    host_handle.nvme_disconnect(device=nvme_device)
                    fun_test.add_checkpoint(checkpoint="Disconnect NVMe device: {} from host {}".
                                            format(nvme_device, host_obj.name))

            for driver in self.NVME_HOST_MODULES[::-1]:
                host_handle.sudo_command("rmmod {}".format(driver))
            fun_test.add_checkpoint(checkpoint="Unload all NVMe drivers")

            for driver in self.NVME_HOST_MODULES:
                host_handle.modprobe(driver)
            fun_test.add_checkpoint(checkpoint="Reload all NVMe drivers")

        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                for port in get_volume_result["data"][volume]["ports"]:
                    detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    fun_test.test_assert(expression=detach_volume.status,
                                         message="Detach Volume {} from host with host_nqn {}".format(
                                             volume, get_volume_result["data"][volume]['ports'][port]['host_nqn']))
                delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                fun_test.test_assert(expression=delete_volume.status, message="Delete Volume {}".format(volume))

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
