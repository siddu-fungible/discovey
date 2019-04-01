from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. No F1 related process is started
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict) use locally defined dictionary variable
        topology_obj_helper = TopologyHelper(spec_file="./single_f1_custom_app.json")
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

    def cleanup(self):
        fun_test.shared_variables["topology"].cleanup()
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Start apps on F1",
                              steps="""
    1. Create the nvfile
    2. Run the app mdt_test
    3. Run the app load_mods
    4. Start FunOs in dpc-server mode
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        topology = fun_test.shared_variables["topology"]
        dut_instance0 = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance0, "Retrieved dut instance 0")

        dut_instance0.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
        dut_instance0.run_app(app="mdt_test", args="nvfile=nvfile", foreground=True, timeout=60)
        dut_instance0.run_app(app="load_mods", foreground=True, timeout=60)
        dut_instance0.start(foreground=True, run_to_completion=True)

        fio = topology.get_tg_instance(tg_index=0)
        destination_ip = dut_instance0.data_plane_ip
        fio.send_traffic(destination_ip=destination_ip)



if __name__ == "__main__":


    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
