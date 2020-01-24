from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.host.swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.host.swagger_client.models.body_volume_attach import BodyVolumeAttach
from lib.host.swagger_client.models.body_node_update import BodyNodeUpdate
from lib.host.swagger_client.models.volume_types import VolumeTypes
from lib.host.swagger_client.models.transport import Transport
import ipaddress


class StorageControllerTemplate():
    def __init__(self, topology):
        self.topology = topology
        self.node_ids = []
        self.update_dataplane_ip = {}

    def check_health(self, storage_controller):
        fun_test.test_assert(message="API server health", expression=storage_controller.health())

    def set_dataplane_ips(self, storage_controller, index):
        if self.update_dataplane_ip != {}:
            if self.update_dataplane_ip[index]:
                fun_test.add_checkpoint(expected=True, actual=True,
                                        checkpoint="DataPlane IP already updated for DUT : %s" % index)
                return

        topology_result = storage_controller.topology_api.get_hierarchical_topology()
        print topology_result

        for k in topology_result.data:
            self.node_ids.append(topology_result.data[k].uuid)

        for node in self.node_ids:

            for f1index in range(0, 2):
                dut = self.topology.get_dut(index=index)
                bond_interfaces = dut.get_bond_interfaces(f1_index=f1index)
                if bond_interfaces == {}:
                    fun_test.critical(message="Bond Interface info not present in test_bed")
                    return
                first_bond_interface = bond_interfaces[0]
                ip_obj = ipaddress.ip_network(address=unicode(first_bond_interface.ip), strict=False)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                subnet_mask = str(ip_obj.netmask)
                next_hop = str(ip_obj.hosts().next())

                body_node_update = BodyNodeUpdate(op="DPU_DP_IP", ip_assignment_dhcp=False, next_hop=next_hop,
                                                  dataplane_ip=dataplane_ip, subnet_mask=subnet_mask)
                dpu_id = node + "." + str(f1index)

                try:
                    assign_dataplane_ip = storage_controller.topology_api.update_dpu(
                        dpu_id=dpu_id, body_node_update=body_node_update)
                    fun_test.add_checkpoint(actual=assign_dataplane_ip.status, expected=True,
                                            checkpoint="Dataplane IP assignment on %s" % dpu_id)
                except:
                    fun_test.test_assert(expression=False, message="Error while updating dataplane IP for %s"
                                                                   % dpu_id)
        self.update_dataplane_ip[index] = True

    def initialize(self):
        for index in self.topology.get_duts().keys():
            fs = self.topology.get_dut_instance(index=index)
            storage_controller = fs.get_storage_controller()
            self.check_health(storage_controller=storage_controller)
            self.set_dataplane_ips(index=index, storage_controller=storage_controller)

    def cleanup(self):
        pass
        # check with storage team


class BltVolumeTemplate(StorageControllerTemplate, object):
    vol_type = VolumeTypes()

    def __init__(self, topology):
        super(BltVolumeTemplate, self).__init__(topology)
        self.topology = topology

    def create_volume(self, fs_obj_list, body_volume_intent_create):
        """
        :param fs_obj_list: List of fs objects
        :param body_volume_intent_create: object of class BodyVolumeIntentCreate with volume details
        :return: dict with format {fs_obj: volume_uuid}
        """
        result = {}
        count = 0
        for fs_obj in fs_obj_list:
            vol_type = VolumeTypes()

            if len(fs_obj_list) > 1:
                body_volume_intent_create.name = body_volume_intent_create.name + str(count)

            body_volume_intent_create.vol_type = vol_type.LOCAL_THIN
            storage_controller = fs_obj.get_storage_controller()
            create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
            vol_uuid = create_vol_result.data.uuid
            result[fs_obj] = vol_uuid
            count += 1
        return result

    def attach_volume(self, fs_obj, volume_uuid, host_obj):
        """
        :param fs_obj: fs_object from topology
        :param volume_uuid: uuid of volume returned after creating volume
        :param host_obj: host handle from topology to which the volume needs to be attached
        :return:
        """

        fun_test.add_checkpoint(expected=True, actual=True,
                                checkpoint="Attaching volume %s to host %s" % (volume_uuid, host_obj))
        storage_controller = fs_obj.get_storage_controller()
        host_data_ip = host_obj.get_test_interface(index=0).ip.split('/')[0]
        transport = Transport()
        attach_fields = BodyVolumeAttach(transport=transport.TCP_TRANSPORT, remote_ip=host_data_ip)

        result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                              body_volume_attach=attach_fields)
        return result

    def nvme_connect_from_host(self, host_obj, subsys_nqn, host_nqn, dataplane_ip,
                               transport_type='tcp', transport_port=1099, nvme_io_queues=None):
        """

        :param host_obj: host handle from topology
        :param subsys_nqn: returned after volume attach
        :param host_nqn: returned after volume attach
        :param dataplane_ip: IP of FS1600 reachable from host returned after volume attach
        :param nvme_io_queues: no of queues for nvme connect
        :return: output of nvme connect command
        """

        nvme_connect_command = host_obj.nvme_connect(target_ip=dataplane_ip, nvme_subsystem=subsys_nqn,
                                                     port=transport_port, transport=transport_type,
                                                     nvme_io_queues=nvme_io_queues, hostnqn=host_nqn)
        return nvme_connect_command

    def deploy(self):
        fun_test.critical(message="Deploy is not available for BLT volume template")

    def initialize(self):
        super(BltVolumeTemplate, self).initialize()

    def cleanup(self):
        """
        Delete created volumes

        :return:
        """
        for index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=index)
            storage_controller = fs_obj.get_storage_controller()
            volumes = storage_controller.storage_api.get_volumes()
            for volume in volumes:
                storage_controller.storage_api.delete_volume(volume_uuid=volumes[volume].uuid)
