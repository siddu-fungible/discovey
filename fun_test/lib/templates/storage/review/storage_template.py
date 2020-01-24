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
                first_bond_interface = bond_interfaces[0]
                ip_obj = ipaddress.ip_network(address=unicode(first_bond_interface.ip), strict=False)
                dataplane_ip = str(first_bond_interface.ip).split('/')[0]
                subnet_mask = str(ip_obj.netmask)
                next_hop = str(ip_obj.hosts().next())

                body_node_update = BodyNodeUpdate(op="DPU_DP_IP", ip_assignment_dhcp=False, next_hop=next_hop,
                                                  dataplane_ip=dataplane_ip, subnet_mask=subnet_mask)
                dpu_id = node + "." + str(index)

                try:
                    storage_controller.topology_api.update_dpu(dpu_id=dpu_id, body_node_update=body_node_update)

                except:
                    fun_test.test_assert(expression=False, message="Error while updating dataplane IP for %s"
                                                                   % dpu_id)
        self.update_dataplane_ip[index] = True

    def deploy(self):
        for index in self.topology.get_duts().keys():
            fs = self.topology.get_dut_instance(index=index)
            storage_controller = fs.get_f1(0).get_dpc_storage_controller()
            self.check_health(storage_controller=storage_controller)
            self.set_dataplane_ips(index=index, storage_controller=storage_controller)

    def cleanup(self):
        pass
        # check with storage team


class BltVolumeTemplate(StorageControllerTemplate, object):
    vol_type = VolumeTypes()

    def __init__(self, topology, attach_volume_map):
        super(BltVolumeTemplate, self).__init__(topology)
        self.topology = topology
        self.attach_volume_map = attach_volume_map

    def create_volume(self, fs, body_volume_intent_create):
        vol_type = VolumeTypes()
        body_volume_intent_create.vol_type = vol_type.LOCAL_THIN
        storage_controller = fs.get_f1(0).get_dpc_storage_controller()
        create_vol_result = storage_controller.storage_api.create_volume(body_volume_intent_create)
        vol_uuid = create_vol_result.data.uuid
        return vol_uuid

    def attach_volume(self, fs, volume_uuid, host_instance):

        fun_test.add_checkpoint(expected=True, actual=True,
                                checkpoint="Attaching volume %s to host %s" % (volume_uuid, host_instance))
        storage_controller = fs.get_f1(0).get_dpc_storage_controller()

        host_data_ip = host_instance.get_test_interface(index=0).ip.split('/')[0]
        transport = Transport()
        attach_fields = BodyVolumeAttach(transport=transport.TCP_TRANSPORT, remote_ip=host_data_ip)

        result = storage_controller.storage_api.attach_volume(volume_uuid=volume_uuid,
                                                              body_volume_attach=attach_fields)
        return result

    def nvme_connect_from_host(self, host_handle, subsys_nqn, host_nqn, dataplane_ip, transport_type='tcp', transport_port=1099):
        command_result = host_handle.sudo_command("nvme connect -t {} -a {} -s {} -n {} -q {}"
                                                  .format(transport_type, dataplane_ip, transport_port,
                                                          subsys_nqn, host_nqn))
        return command_result

    def deploy(self):
        super(BltVolumeTemplate, self).deploy()

        for fs in self.attach_volume_map:
            for volumes_index in self.attach_volume_map[fs]:
                volume_uuid = self.create_volume(fs=fs,
                                                 body_volume_intent_create=volumes_index['body_volume_intent_create'])
                for host_instance in volumes_index['host_list']:
                    attach_volume = self.attach_volume(fs=fs, volume_uuid=volume_uuid, host_instance=host_instance)

                    subsys_nqn = attach_volume.data.subsys_nqn
                    host_nqn = attach_volume.data.host_nqn
                    dataplane_ip = attach_volume.data.ip
                    fun_test.test_assert(expression=self.nvme_connect_from_host(host_handle=host_instance,
                                                                                host_nqn=host_nqn,
                                                                                subsys_nqn=subsys_nqn,
                                                                                dataplane_ip=dataplane_ip))
