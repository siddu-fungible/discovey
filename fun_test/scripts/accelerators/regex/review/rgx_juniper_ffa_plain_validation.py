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
                              summary="F1:JUNIPER PATTERNS compiled with FFA Strategy and DEFAULT Memory Allocation",
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
        mem_dist = ["dflt"]
        for tc in ["juniper_compile_full"]:
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
        #bbelow pat_ptah and pld_path are used for  the juniper_style of patterns to compile and validate
            pat_path = "/regex/"
            pld_path = "/regex/"
            #for gtype, en in zip(["dfa", "nfa", "ffa"], ["1", "0", ""]):
            for gtype, en in zip(["ffa"], [""]):
                res_path = "/regex/"+str(tc)+"/" + gtype + "_results/"
                con1.create_directory(res_path)
                print ("res_path is ",res_path)
                #res_path = "/regex/Users/fungible/ws/data_store/regression/" + str(tc) + "/" + gtype + "_results/"
                print ("res_path is ",res_path)
                exp_file_path= DATA_STORE_DIR+"/regex/"+str(tc)+"/"+gtype+"_exp_files/"
                print ("exp_file_path is",exp_file_path)
                print "CALLING compiler with ", res_path, " en:", en
                pat_pld_files = {}
                print ("exp_file_path is ", exp_file_path)
                print("pat_path is ", pat_path)
                print ("pld path is", pld_path)
                pat_file_dict = con1.list_files(pat_path+"*")
                print ("type of pat_file_dict is ", type(pat_file_dict))
                print ("pat_file_dict is ", pat_file_dict)
                pat_files = [fn['filename'].split(pat_path)[1] for fn in pat_file_dict if not fn['filename'].endswith(".tgz")]
                print ("pat_files are",pat_files)
                pat_files = [pat for pat in pat_files if pat != "juniper_compile_full"]
                print ("pat_files are ",pat_files)
                pat_files = [pat for pat in pat_files if not pat.isdigit()]
                print ("pat_file is", pat_files)
                for pat in pat_files:
                    pld_paths = pat_path + pat + "/payloads/"
                    print ("pld_path is ", pld_paths)
                    plds = con1.list_files(pld_paths+"*")
                    print("plds are", plds)
                    plds = [fn['filename'].split(pld_paths)[1] for fn in plds if not fn["filename"].isdigit()]
                    plds=sorted(plds)
                    pat_pld_files[pat + ".pat"] = plds
                print ("pat_pld_files are",pat_pld_files)

                RegexTemplate.compile_n_validate(con1, mem_dist, pat_path, pld_path, res_path, exp_file_path, pat_pld_files, ["ymsg-p2p-put-filename","ymsg-message","h225ras-location","mssql-login-user","imap-fetch","msn-sign-in-name","h225ras-admission","vnc-client-version","smb-account-name","nbname-resource-address","http-header-content-language","ymsg-user-name"],
                                                 en, juniper_style="yes")

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

