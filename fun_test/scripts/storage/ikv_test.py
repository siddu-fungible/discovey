from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
import hashlib
import pickle
import dill
# fun_test.enable_debug()



topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }

    }
}


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM
                              """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        topology.pickle(file_name="mypickle.pkl")
        fun_test.test_assert(topology, "Ensure deploy is successful")

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass

def get_hex(value):
    return ''.join(x.encode('hex') for x in value)

def get_sha256_hex(value):
    m = hashlib.sha256()
    m.update(value)
    return get_hex(value=m.digest())

class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create, open IKV store, puts and gets of kv",
                              steps="""
        1. Create and open ikv
        2. likv put the contents and retrieve a key hex
        3. likv get using the key hex from the put
        4. Compare the put value and get value
                              """)

    def setup(self):
        pass

    def cleanup(self):
        dut_instance = fun_test.shared_variables["topology"].get_dut_instance(index=0)

        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name="f1.log.txt")
        fun_test.scp(source_ip=dut_instance.host_ip,
                     source_file_path=dut_instance.F1_LOG,
                     source_username=dut_instance.ssh_username,
                     source_password=dut_instance.ssh_password,
                     source_port=dut_instance.ssh_port,
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="F1 Log", filename=artifact_file_name)


    def run(self):
        topology = dill.load( open("mypickle.pkl", "rb" ))

        # dut_instance = fun_test.shared_variables["topology"].get_dut_instance(index=0)
        dut_instance = topology.get_dut_instance(index=0)

        fun_test.test_assert(dut_instance, "Retrieved dut instance")
        storage_controller = StorageController(mode="likv",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)
        contents = "0123456789012345678901234567890123456789012345678901234567890123456789"
        input_value = get_hex(contents)
        key_hex = get_sha256_hex(value=input_value)
        dir_vol_uuid = '0020-0001'
        lvs_vol_uuid = '0020-0002'
        lvs_allocator_uuid = '0020-0003'
        volume_id = 10
        max_lvs_bytes = 1 << 30
        max_keys = 1 << 14
        init_lvs_bytes = 1 << 20
        init_keys = 1 << 12


        storage_controller = StorageController(mode="storage",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)
        result = storage_controller.create_thin_block_volume(capacity=4198400,
                                                      uuid=dir_vol_uuid,
                                                      name="vol-likv-dir-1",
                                                      block_size=4096)
        fun_test.test_assert(result["status"], "Create dir volume")


        result = storage_controller.create_thin_block_volume(capacity=1073741824,
                                                      block_size=4096,
                                                      name="vol-likv-lvs-1",
                                                      uuid=lvs_vol_uuid)

        fun_test.test_assert(result["status"], "Create lvs volume")

        result = storage_controller.create_thin_block_volume(capacity=5623808,
                                                      block_size=4096,
                                                      name="vol-lvs-allocator-1",
                                                      uuid=lvs_allocator_uuid)

        fun_test.test_assert(result["status"], "Create lvs allocator")



        storage_controller = StorageController(mode="likv",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)

        create_d = {"max_keys": max_keys,
                    "lvs_vol_uuid": lvs_vol_uuid,
                    "init_keys": init_keys,
                    "volume_id": volume_id,
                    "init_lvs_bytes": init_lvs_bytes,
                    "lvs_allocator_uuid": lvs_allocator_uuid,
                    "max_lvs_bytes": max_lvs_bytes,
                    "dir_uuid": dir_vol_uuid}
        result = storage_controller.json_command(action="cal_vols_size", data=create_d)
        fun_test.test_assert(result["status"], "cal_vols_size")

        create_d = {"init_lvs_bytes": init_lvs_bytes,
                    "max_keys": max_keys,
                    "max_lvs_bytes": max_lvs_bytes,
                    "init_keys": init_keys,
                    "volume_id": volume_id,
                    'dir_uuid': dir_vol_uuid,
                    'lvs_vol_uuid': lvs_vol_uuid,
                    'lvs_allocator_uuid': lvs_allocator_uuid
                    }
        result = storage_controller.json_command(action="create", data=create_d)
        fun_test.test_assert(result["status"], "Likv create")
        open_d = {"volume_id": volume_id}
        result = storage_controller.json_command(data=open_d, action="open")
        fun_test.test_assert(result["status"], "Likv open")

        put_d = {"key_hex": key_hex, "value": input_value, "volume_id": volume_id}

        result = storage_controller.json_command(action="put ", data=put_d)
        fun_test.test_assert(result["status"], "Likv put")

        get_d = {"key_hex": key_hex, "volume_id": volume_id}
        result = storage_controller.json_command(action="get", data=get_d)
        ba = bytearray.fromhex(result["data"]["value"])
        ba_str = str(ba)

        fun_test.test_assert_expected(actual=contents, expected=ba_str, message="Ensure put value and get value are same")
        result = storage_controller.command("peek stats/likv")
        fun_test.simple_assert(result["status"], "Fetch ikv stats")
        volume_id = str(volume_id)
        fun_test.test_assert(result["data"][volume_id]["LIKV get bytes"], "LIKV get bytes")
        fun_test.test_assert_expected(actual=result["data"][volume_id]["gets"],
                                      expected=1, message="LIKV gets")
        fun_test.test_assert_expected(actual=result["data"][volume_id]["puts"],
                                      expected=1, message="LIKV puts")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
