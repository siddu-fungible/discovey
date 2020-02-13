from lib.system.fun_test import *
from lib.fun.fs import Fs
from lib.topology.topology_helper import TopologyHelper


class NvdimmScripts(FunTestScript):
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



class NvdimmTest1(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Setup FS standalone with TopologyHelper",
                              steps="""
        1. Boot FunOS with bootargs - nvdimm_arm_backup=1 
        2. Generate HW_FAIL_INT_L by toggling BMC pin 208
        3. Re-boot FunOS with bootargs nvdimm_arm_backup=1 nvdimm_restore=1 
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")
        # fun_test.shared_variables["fs"].cleanup()

    def run(self):
        # fun_test.build_parameters["bundle_image_parameters"] = {"release_train": "rel_1_0a_aa", "build_number": -1}
        topology_helper = TopologyHelper()
        #topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")
        #topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods,nvdimm_demo nvdimm_arm_backup=1 demo-mode=backup syslog=6 --test-exit-fast --dpc-uart --dpc-server --csr-replay --all_100g")
        #topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods nvdimm_arm_backup=1 demo-mode=backup syslog=6 --test-exit-fast --dpc-uart --dpc-server --csr-replay --all_100g")
        #topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=nvdimm_demo nvdimm_arm_backup=1 demo-mode=backup syslog=6 --test-exit-fast --dpc-uart --dpc-server --csr-replay --all_100g")
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods nvdimm_arm_backup=1 --dpc-uart --dpc-server --csr-replay --all_100g")
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)

        fun_test.log("come start setup tools ...")
        come = fs.get_come()
        come.setup_tools()
        fun_test.log("come done setup tools ...")

        #fun_test.shared_variables["fs"] = fs


      #  #Get BMC handle and assert pin 208 which should assert the HW_INT_FAIL to MMIO
      #  fun_test.log("get bmc handle ...")
      #  bmc_handle = fs.get_bmc()
      #  fun_test.log("low pulse on bmc pin 208 ...")
      #  output = bmc_handle.command('gpiotool --set-data-low 208; sleep 1; gpiotool --set-data-high 208') #F1_0, for F1_1, use pin 209
      #  fun_test.log("sleep for 300 seconds ...")
      #  fun_test.sleep("Temporary Wait for backup complete", seconds=300) #TODO: Need to figure out how to poll on backup complete

      #  fun_test.log("Rebooting FS ...")
      #  topology_helper = TopologyHelper()
      #  #topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")
      #  topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods,hw_hsu_test sku=SKU_FS1600R2_0 --serial --dpc-server --dpc-uart --mgmt --all_100g --fec syslog=6 nvdimm_arm_backup=1 nvdimm_restore=1")
      #  topology = topology_helper.deploy()

        ##John's recommendation w.r.t. Reboot -
        #fs.reset()
        #fs.re_initialize()
        fun_test.log("Test Done !!!")

        topology.cleanup()

if __name__ == "__main__":
    myscript = NvdimmScripts()
    myscript.add_test_case(NvdimmTest1())
    #myscript.add_test_case(FunTestCase2())
    myscript.run()

