from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.traffic_generator import TrafficGenerator
from lib.system.fun_test import *
from lib.templates.regex.regex_template import RegexTemplate
from fun_settings import DATA_STORE_DIR
import re
import json
import glob

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
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
        }
    }
}


class RegExScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology.
        2. Bring up the container with Regex compiler
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()

        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["dut_ip"] = self.dut.host_ip
        fun_test.shared_variables["data_plane_ip"] = self.dut.data_plane_ip
        fun_test.shared_variables["ssh_port"] = self.dut.ssh_port

    def cleanup(self):
        pass
        #self.topology_obj_helper.cleanup()

class pcre_ffa_Plain_compile_only(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary=" F1: PCRE FFA  PATTERNS compiled with FFA Strategy and DEFAULT Memory Allocation",
                              steps="""
                              """)

    def setup(self):
        testcase = self.__class__.__name__
        self.my_shared_variables = {}

    def cleanup(self):
        pass

    def run(self):
        testcase = self.__class__.__name__
        dut_ip = fun_test.shared_variables["dut_ip"]
        dut_ssh_port = fun_test.shared_variables["ssh_port"]

        con1 = RegexTemplate(host_ip=dut_ip, ssh_username="root", ssh_password="fun123", ssh_port=dut_ssh_port)
        con2 = RegexTemplate(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
        ffac_path = '/regex/'
        command_result = con1.create_directory("/regex")
        base = "/regex"
        fun_test.log("data store directory: " + DATA_STORE_DIR)
        con1.set_compiler_env(ffac_path)
        mem_dist = ["dflt"]
        for tc in ["pcre1_ffa"]:    # Tar file name of patterns/payloads
            tarball_path = "{}/{}.tgz".format(DATA_STORE_DIR + base, str(tc))
            fun_test.test_assert(fun_test.scp(source_file_path=tarball_path,
                                              target_file_path="/regex",
                                              target_ip=con1.host_ip,
                                              target_username=con1.ssh_username,
                                              target_password=con1.ssh_password,
                                              target_port=con1.ssh_port,
                                              recursive=False,
                                              timeout=300),
                                 message="scp tarball {} to conatiner".format(tarball_path), ignore_on_success=True)

            con1.untar("/regex/"+str(tc)+".tgz", "/regex/")
            pat_path = "/regex/patterns/"
            pld_path = "/regex/payloads/"
            for gtype, en in zip(["ffa"], [""]):
                res_path = "/regex/F1/"+str(tc)+"/" + gtype + "_results/" # Change this for LOCAL run
                #res_path = "/Users/admin/python_scripts/pcre_extracted_new/ffa_filtered_graphs1/"
                con1.create_directory(res_path)
                #res_path = "/regex/Users/fungible/ws/data_store/regression/" + str(tc) + "/" + gtype + "_results/"
                exp_file_path = DATA_STORE_DIR + "/regex/" + str(tc) + "/" + gtype + "_exp_files/"  # Change this for LOCAL run
                #exp_file_path="/Users/admin/python_scripts/pcre_extracted_new/ffa_filtered_graphs1/"
                pat_pld_files = {}
                pat_file_dict = con1.list_files(pat_path+"*")
                pld_files = con1.list_files(pld_path+"*")
                pat_files = con1.list_files(pat_path+"*")
                pld_files = [fn['filename'].split(pld_path)[1] for fn in pld_files if not fn["filename"].isdigit()]
                pat_files= [fn['filename'].split(pat_path)[1] for fn in pat_files if not fn["filename"].isdigit()]

                pat_pld_files = {}
                for pat in pat_files:
                    id_ = pat.split(".pat")[0]
                    x = id_ + "_*"
                    plds_list = con1.list_files(pld_path+x)
                    plds_list=[str(fn['filename'].split(pld_path)[1]) for fn in plds_list if not fn["filename"].isdigit()]
                    plds_list=sorted(plds_list)
                    try:
                        pat_pld_files[pat] = plds_list
                    except:
                        print ("caught an exception")
                print ("pat_pld_files are ",pat_pld_files)

                RegexTemplate.compile_n_validate(con1, mem_dist, pat_path, pld_path, res_path, exp_file_path, pat_pld_files, [], en,
                                                 juniper_style="")

                res1_path=""
                try:
                    fun_test.test_assert(con1.scp(target_file_path="/project/users/QA/regression/data_store" + res_path,
                         target_ip=con2.host_ip,
                         source_file_path=res_path+"*.json",
                         target_username=con2.ssh_username,
                         target_password=con2.ssh_password),
                         message="scp graphs to /project/users/QA/regression/data_store")
                except:
                    pass




if __name__ == "__main__":
    myscript = RegExScript()
    myscript.add_test_case(pcre_ffa_Plain_compile_only())
    myscript.run()
