from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController
from lib.fun.fs import Bmc
import struct
import os
import random
import json
# os.environ["DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/local_docker_host_with_storage.json"
#os.environ["DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/remote_docker_host_with_storage.json"


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Start QEMU within the container
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict) use locally defined dictionary variable

        #topology_obj_helper = TopologyHelper(spec_file="/Users/adevaraj/Projects/Integration/fun_test/scripts/examples/single_f1_with_qemu_plus_dpcsh_ubuntu.json")
        #self.topology_helper = TopologyHelper()
        #self.topology = self.topology_helper.deploy()
        #fun_test.test_assert(self.topology, "Topology deployed")
        pass


    def cleanup(self):
        if "topology" in fun_test.shared_variables:
            fun_test.shared_variables["topology"].cleanup()
        pass

def get_i2c_read_cmd(path, slave_address, m, rc, address):
    reg_hex_addr = []
    i2c_read_cmd = "i2c-test -b {} -s {} -m {} -rc {} -d 0x00 ".format(path, hex(slave_address), m, rc)
    addr_int = int(address, 16)
    # print hex(addr_int)
    reg_addr = struct.pack('>Q', addr_int)
    reg_addr = list(struct.unpack('BBBBBBBB', reg_addr))
    for x in range(8):
        reg_hex_addr.append(hex(reg_addr[x]))
    cmd_addr = reg_hex_addr[3:8]
    for n in cmd_addr:
        i2c_read_cmd = i2c_read_cmd + "{} ".format(n)
    #print i2c_read_cmd
    return i2c_read_cmd
def comp_data(exp_data, rcv_str,write_cmd):
    rcv_data = []
    rcv_str = rcv_str.split("\r\n")
    print(rcv_str)
    rcv_byte = rcv_str[1].split(" ")
    while("" in rcv_byte):
        rcv_byte.remove("")
    print(rcv_byte)
    for x in range(len(rcv_byte)):
        rcv_data.append(hex(int(rcv_byte[x],16)))
    #print(rcv_data)
    chk_status = rcv_data[0]
    chk_data = rcv_data[1:9]
    #print(chk_data)
    #print(exp_data)
    for x in range(8):
        #print(exp_data[x])
        #print(chk_data[x])
        #fun_test.test_assert((hex(exp_data[x]) == chk_data[x]), "Comparision failed")
        if(hex(exp_data[x]) != chk_data[x]):
            fun_test.log("Error: Read Data and write data mis-match for write cmd{} actual {} Expected {}".format(write_cmd,chk_data[x],exp_data[x]))
            fun_test.test_result = FunTest.FAILED
            #print(write_cmd)
        else:
            #print("Read Data and write data match")
            fun_test.test_result = FunTest.PASSED

        if(chk_status != '0x80'):
             fun_test.log("Error: Unexpected Status for write cmd{} Actual {} Expected {}".format(write_cmd,
                                                                                                          chk_status,
                                                                                                          0x80))
             fun_test.test_result = FunTest.FAILED
        else:
             # print("Read Data and write data match")
             fun_test.test_result = FunTest.PASSED

def get_i2c_write_cmd(path, slave_address, m, rc, address):
    reg_hex_addr = []
    i2c_write_cmd = "i2c-test -b {} -s {} -m {} -rc {} -d 0x01 ".format(path, hex(slave_address), m, rc)
    addr_int = int(address, 16)
    # print hex(addr_int)
    reg_addr = struct.pack('>Q', addr_int)
    reg_addr = list(struct.unpack('BBBBBBBB', reg_addr))
    for x in range(8):
        reg_hex_addr.append(hex(reg_addr[x]))
    cmd_addr = reg_hex_addr[3:8]
    for n in cmd_addr:
        i2c_write_cmd = i2c_write_cmd + "{} ".format(n)
    data_bytes = get_rand_bytes(8)
    for n in data_bytes:
        i2c_write_cmd = i2c_write_cmd + "{} ".format(hex(n))
    #print i2c_write_cmd
    return i2c_write_cmd, data_bytes

def get_rand_bytes(n):
    return bytearray((random.getrandbits(8) for i in xrange(n)))


class FunTestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Run some command on BMC prompt",
                              steps="""
    1. Connect to BMC
    2. Execute the i2c-test command
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass


    def run(self):
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        fun_test.get_asset_manager()
        fs = fun_test.asset_manager.get_fs_spec("fs-174")
        bmc_spec = fs.get("bmc")
        bmc = Bmc(host_ip=bmc_spec["mgmt_ip"], ssh_username=bmc_spec["mgmt_ssh_username"],
                  ssh_password=bmc_spec["mgmt_ssh_password"])
        f = open("/Users/karthiksiddavaram/sanity_f1_regs.json")
        #f = open("/Users/karthiksiddavaram/temp.json")
        dict = json.load(f)
        for address_name, address in dict.iteritems():
            data_arr = []
            write, data_arr = get_i2c_write_cmd(3, 0x70, 1, 9, address)
            output = bmc.command(write)
            read = get_i2c_read_cmd(3, 0x70, 1, 9, address)
            output = bmc.command(read)
            #print(data_arr)
            comp_data(data_arr,output,write)
            # TODO Interpret output and do comparison



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()