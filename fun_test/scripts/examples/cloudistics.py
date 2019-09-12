from lib.system.fun_test import *
from lib.fun.fs import Fs, ComE
from lib.topology.topology_helper import TopologyHelper
from fun_settings import DATA_STORE_DIR


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Setup FS with TopologyHelper",
                              steps="""

                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")
        # fun_test.shared_variables["fs"].cleanup()

    def run(self):

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=hw_hsu_test --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog")
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        come = fs.get_come()
        source_file_path = "{}/a.txt".format(DATA_STORE_DIR)
        target_file_path = "/tmp/a.txt"
        fun_test.test_assert(fun_test.scp(source_file_path=source_file_path,
                                          target_file_path=target_file_path,
                                          target_ip=come.host_ip,
                                          target_username=come.ssh_username,
                                          target_password=come.ssh_password,
                                          target_port=come.ssh_port,
                                          recursive=False,
                                          timeout=300), "SCP file")
        fun_test.test_assert(come.list_files(target_file_path), "Ensure file is fetched")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase2())
    myscript.run()

