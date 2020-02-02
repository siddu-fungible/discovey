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


class StorageControllerOperationsTemplate():
    """
    Do basic API operations
    """
    def __init__(self, topology):
        self.topology = topology
        self.node_ids = []

    def get_health(self, storage_controller):
        return storage_controller.health()

    def set_dataplane_ips(self, storage_controller, dut_index):
        result = False
        topology_result = storage_controller.topology_api.get_hierarchical_topology()
        print topology_result

        for k in topology_result.data:
            self.node_ids.append(topology_result.data[k].uuid)

        for node in self.node_ids:
            dut = self.topology.get_dut(index=dut_index)
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            for f1_index in range(fs_obj.NUM_F1S):

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

    def initialize(self, already_deployed=False):
        for dut_index in self.topology.get_available_duts().keys():
            fs = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs.get_storage_controller()
            fun_test.test_assert(self.get_health(storage_controller=storage_controller),
                                 message="DUT: {} Health of API server".format(dut_index))
            if not already_deployed:
                fun_test.sleep(message="Wait before firing Dataplane IP commands", seconds=60)
                fun_test.test_assert(self.set_dataplane_ips(dut_index=dut_index, storage_controller=storage_controller),
                                     message="DUT: {} Assign dataplane IP".format(dut_index))

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

    def create_volume(self, fs_obj_list, body_volume_intent_create):
        """
        Create a volume for each fs_obj in fs_obj_list
        :param fs_obj_list: List of fs objects
        :param body_volume_intent_create: object of class BodyVolumeIntentCreate with volume details
        :return: dict with format {fs_obj: volume_uuid}
        """
        result = {}
        for fs_index, fs_obj in enumerate(fs_obj_list):

            if len(fs_obj_list) > 1:
                body_volume_intent_create.name = body_volume_intent_create.name + str(fs_index)

            body_volume_intent_create.vol_type = self.vol_type
            storage_controller = fs_obj.get_storage_controller()
            try:
                create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
                vol_uuid = create_vol_result.data.uuid
                result[fs_obj] = vol_uuid
            except ApiException as e:
                fun_test.critical("Exception when creating volume on fs %s: %s\n" % (fs_obj, e))
        return result

    def attach_volume(self, fs_obj, volume_uuid, host_obj, validate_nvme_connect=True, raw_api_call=False):

        """
        :param fs_obj: fs_object from topology
        :param volume_uuid: uuid of volume returned after creating volume
        :param host_obj: host handle from topology to which the volume needs to be attached
        :param validate_nvme_connect: Use this flag to do NVMe connect from host along with attaching volume
        :param raw_api_call: Temporary workaround to use raw API call until swagger APi issues are resolved.
        :return: Attach volume result
        """
        result = None
        fun_test.add_checkpoint(checkpoint="Attaching volume %s to host %s" % (volume_uuid, host_obj))
        storage_controller = fs_obj.get_storage_controller()
        host_data_ip = host_obj.get_test_interface(index=0).ip.split('/')[0]
        if not raw_api_call:
            attach_fields = BodyVolumeAttach(transport=Transport().TCP_TRANSPORT, remote_ip=host_data_ip)

            try:
                result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                                      body_volume_attach=attach_fields)

            except ApiException as e:
                fun_test.test_assert(expression=False,
                                     message="Exception when creating volume on fs %s: %s\n" % (fs_obj, e))
                result = None
        else:
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            result = raw_sc_api.volume_attach_remote(vol_uuid=volume_uuid, remote_ip=host_data_ip)

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
                                                                        host_nqn=host_nqn, dataplane_ip=dataplane_ip),
                                 message="NVMe connect from host: {}".format(host_obj.name))
            nvme_filename = self.get_host_nvme_device(host_obj=host_obj, subsys_nqn=subsys_nqn)
            fun_test.test_assert(expression=nvme_filename,
                                 message="Get NVMe drive from Host {} using lsblk".format(host_obj.name))

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
            if not host_linux_handle.lsmod(module=driver):
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
        :return: NVMe device name on Host
        """
        result = None
        host_linux_handle = host_obj.get_instance()
        nvme_volumes = self.get_nvme_namespaces(host_handle=host_linux_handle)

        if subsys_nqn:
            for namespace in nvme_volumes:
                nvme_device = namespace[:-2]
                namespace_subsys_nqn = host_linux_handle.command("cat /sys/class/nvme/{}/subsysnqn".format(
                    nvme_device))
                if str(namespace_subsys_nqn).strip() == str(subsys_nqn):
                    result = namespace
                    self.host_nvme_device[host_obj] = namespace
        else:
            result = nvme_volumes[-1:][0]
        return result

    def traffic_from_host(self, host_obj, filename, job_name="Fungible_nvmeof", numjobs=1, iodepth=1,
                          rw="readwrite", runtime=60, bs="4k", ioengine="libaio", direct=1,
                          time_based=True, norandommap=True, verify=None, do_verify=None):
        host_linux_handle = host_obj.get_instance()
        fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw=rw,
                                           filename=filename, runtime=runtime, ioengine=ioengine, direct=direct,
                                           timeout=runtime+15, time_based=time_based, norandommap=norandommap,
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

    def initialize(self, already_deployed=False):
        super(GenericVolumeOperationsTemplate, self).initialize(already_deployed=already_deployed)

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

            host_handle.nvme_disconnect(nvme_subsystem=self.host_nvme_device[host_obj])
            fun_test.add_checkpoint(checkpoint="Disconnect NVMe device")

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
                                         message="Detach Volume {} from host with remote IP {}".format(
                                             volume, get_volume_result["data"][volume]['ports'][port]['remote_ip']))
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
