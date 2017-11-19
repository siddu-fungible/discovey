from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper, Dut
from lib.host.storage_controller import StorageController
import hashlib
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
                    "type": Dut.DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "simulation_start_mode": Dut.SIMULATION_START_MODE_DPCSH_ONLY
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
        self.topology = topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")

    def cleanup(self):
        TopologyHelper(spec=self.topology).cleanup()

def get_hex(value):
    return ''.join(x.encode('hex') for x in value)

def get_sha256_hex(value):
    m = hashlib.sha256()
    m.update(value)
    return get_hex(value=m.digest())

class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create and attach namespace",
                              steps="""
        1. Create and open ikv
        2. likv put the contents and retrieve a key hex
        3. likv get using the key hex from the put
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        dut_instance = self.script_obj.topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance, "Retrieved dut instance")
        storage_controller = StorageController(mode="likv",
                                               target_ip=dut_instance.host_ip,
                                               target_port=dut_instance.external_dpcsh_port)
        contents = "0123456789"
        input_value = get_hex(contents)
        key_hex = get_sha256_hex(value=input_value)
        create_d = {"init_lvs_bytes": 1048576,
                    "max_keys": 16384,
                    "max_lvs_bytes": 107374182,
                    "init_keys": 4096,
                    "volume_id": 0}
        result = storage_controller.json_command(action="create", data=create_d)
        fun_test.test_assert(result["status"], "Likv create")
        open_d = {"volume_id": 0}
        result = storage_controller.json_command(data=open_d, action="open")
        fun_test.test_assert(result["status"], "Likv open")

        put_d = {"key_hex": key_hex, "value": input_value, "volume_id": 0}
        result = storage_controller.json_command(action="put ", data=put_d)
        fun_test.test_assert(result["status"], "Likv put")

        get_d = {"key_hex": key_hex, "volume_id": 0}
        result = storage_controller.json_command(action="get", data=get_d)
        ba = bytearray.fromhex(result["data"]["value"])
        ba_str = str(ba)

        result = storage_controller.command("peek storage/volumes")

if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1(myscript))
    myscript.run()
