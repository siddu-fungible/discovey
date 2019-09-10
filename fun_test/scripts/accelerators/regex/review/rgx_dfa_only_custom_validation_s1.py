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
        print dir(self.dut)

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["dut_ip"] = self.dut.host_ip
        fun_test.shared_variables["data_plane_ip"] = self.dut.data_plane_ip
        print "dut_ip ", self.dut.host_ip, "data_plane_ip ", self.dut.data_plane_ip
        print "this one ", self.dut.ssh_port
        fun_test.shared_variables["ssh_port"] = self.dut.ssh_port

    def cleanup(self):
        pass
        #self.topology_obj_helper.cleanup()

class JuniperNFACustomCompileOnly(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="compile and load",
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
        print ("data_store dir is ",DATA_STORE_DIR)
        command_result = con1.create_directory("/regex")
        base = "/regex"
        fun_test.log("data store directory: " + DATA_STORE_DIR)
        con1.set_compiler_env(ffac_path)
        mem_dist = ["rbm", "exm", "rbm_exm", "rbm_exm_plr"]
        for tc in ["dfa_only_compile"]:
            tarball_path = "{}/{}.tgz".format(DATA_STORE_DIR + base, str(tc))
            print ("tarball path is ",tarball_path)
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
        #below pat and pld path are used to test compile only part with all patterns stored in a single folder and all payloads stored ina separate folder
          #  pat_path="/regex/"+str(tc)+"/patterns/"
           # pld_path="/regex/"+str(tc)+"/payloads/"
        #bbelow pat_ptah and pld_path are used for  the junieper_style of patterns to compile and validate
            pat_path = "/regex/patterns/"
            pld_path = "/regex/payloads/"
            #for gtype, en in zip(["dfa", "nfa", "ffa"], ["1", "0", ""]):
            for gtype, en in zip(["dfa"], ["1"]):
                res_path = "/regex/"+str(tc)+"/" + gtype + "_results/"
                con1.create_directory(res_path)
                print ("res_path is ",res_path)
                #res_path = "/regex/Users/fungible/ws/data_store/regression/" + str(tc) + "/" + gtype + "_results/"
                print ("res_path is ",res_path)
                exp_file_path = DATA_STORE_DIR + "/regex/" + str(tc) + "/" + gtype + "_exp_files/"
                #exp_file_path="/regex/Users/fungible/ws/data_store/regression/DFA_ONLY/"+gtype+"_exp_files/"
                print ("exp_file_path is",exp_file_path)
                print "CALLING compiler with ", res_path, " en:", en
                pat_pld_files = {}
                print ("exp_file_path is ", exp_file_path)
                print("pat_path is ", pat_path)
                print ("pld path is", pld_path)
                pat_file_dict = con1.list_files(pat_path+"*")
                print ("type of pat_file_dict is ", type(pat_file_dict))
                print ("pat_file_dict is ", pat_file_dict)
                pld_files = con1.list_files(pld_path+"*")
                pat_files = con1.list_files(pat_path+"*")
                print ("pat_files are ",pat_files)
                print ("pld_files are ",pld_files)
                pld_files = [fn['filename'].split(pld_path)[1] for fn in pld_files if not fn["filename"].isdigit()]
                pat_files= [fn['filename'].split(pat_path)[1] for fn in pat_files if not fn["filename"].isdigit()]

                print("pat_file are ",pat_files)
                print("pld_files are ",pld_files)
                pat_pld_files = {}
                for pat in pat_files:
                    id_ = pat.split(".pat")[0]
                    print("id_ is", id_)
                    x = id_ + "_*"
                    plds_list = con1.list_files(pld_path+x)



                    print ("plds list before extraction",plds_list)
                    plds_list=[str(fn['filename'].split(pld_path)[1]) for fn in plds_list if not fn["filename"].isdigit()]
                    print ("plds list after extraction is",plds_list)
                    plds_list=sorted(plds_list)
                    print ("plds_list after sorting is",plds_list)
                    try:
                        pat_pld_files[pat] = plds_list
                    #   print ("**************************")
                    #  print ("pat_pld_files is ",pat_pld_files)
                    except:
                        print ("caught an exception")
                print ("pat_pld_files are ",pat_pld_files)
                #pat_pld_files={"test_3.pat":["test_3_1.in","test_3_2.in","test_3_3.in"]}

                RegexTemplate.compile_n_validate(con1, mem_dist, pat_path, pld_path,res_path,exp_file_path,pat_pld_files, ["test_33", "test_28"], en, juniper_style="", target="s1")

                #RegexTemplate.compile_only(con1, mem_dist, pat_path, res_path, [], en, juniper_style="yes")

                print "SCP now con1 ssh_username:", con1.ssh_username, " passwd:", con1.ssh_password, " srt prt:", \
                    con1.ssh_port, " target port:", con1.ssh_port
                print "SCP now con2 ssh_username:", con2.ssh_username, " passwd:", con2.ssh_password, " srt prt:", \
                    con2.ssh_port, " target port:", con2.ssh_port

                res1_path=""
                try:
                    fun_test.test_assert(con1.scp(target_file_path="/local/auto_admin/data_store/" + res_path,
                         target_ip=con2.host_ip,
                         source_file_path=res_path+"*.json",
                         target_username=con2.ssh_username,
                         target_password=con2.ssh_password),
                         message="scp graphs to /local/auto_admin/data_store/{}".format(res_path))
                except:
                    pass




if __name__ == "__main__":
    myscript = RegExScript()
    myscript.add_test_case(JuniperNFACustomCompileOnly())
    myscript.run()

