import re
import json
from asset.asset_manager import AssetManager
s = """
fs8-bmc 10.80.4.151
fs8-fpga 10.80.4.152
fs8-come 10.80.4.153
fs8-mgmt0 10.80.4.154
fs8-mgmt1 10.80.4.155
fs21-bmc 10.80.4.156
fs21-fpga 10.80.4.157
fs21-come 10.80.4.158 <= (64GB + 64GB) SATA
fs21-mgmt0 10.80.4.159
fs21-mgmt1 10.80.4.160
fs52-bmc 10.80.4.161
fs52-fpga 10.80.4.162
fs52-come 10.80.4.163 <= (64GB + 64GB) SATA
fs52-mgmt0 10.80.4.164
fs52-mgmt1 10.80.4.165
fs38-bmc 10.80.4.166
fs38-fpga 10.80.4.167
fs38-come 10.80.4.168
fs38-mgmt0 10.80.4.169
fs38-mgmt1 10.80.4.170
fs15-bmc 10.80.4.171
fs15-fpga 10.80.4.172
fs15-come 10.80.4.173 <= (64GB + 64GB) SATA
fs15-mgmt0 10.80.4.174
fs15-mgmt1 10.80.4.175
fs20-bmc 10.80.4.176
fs20-fpga 10.80.4.177
fs20-come 10.80.4.178 <= (64GB + 64GB) SATA
fs20-mgmt0 10.80.4.179
fs20-mgmt1 10.80.4.180
fs69-bmc 10.80.4.181
fs69-fpga 10.80.4.182
fs69-come 10.80.4.183 <= (64GB + 0GB) SATA
fs69-mgmt0 10.80.4.184
fs69-mgmt1 10.80.4.185
fs39-bmc 10.80.4.186
fs39-fpga 10.80.4.187
fs39-come 10.80.4.188 <= (8GB + 8GB) SATA
fs39-mgmt0 10.80.4.189
fs39-mgmt1 10.80.4.190
fs51-bmc 10.80.4.191
fs51-fpga 10.80.4.192
fs51-come 10.80.4.193
fs51-mgmt0 10.80.4.194
fs51-mgmt1 10.80.4.195
fs37-bmc 10.80.4.196
fs37-fpga 10.80.4.197
fs37-come 10.80.4.198
fs37-mgmt0 10.80.4.199
fs37-mgmt1 10.80.4.200
fs32-bmc 10.80.4.201
fs32-fpga 10.80.4.202
fs32-come 10.80.4.203
fs32-mgmt0 10.80.4.204
fs32-mgmt1 10.80.4.205
fs67-bmc 10.80.4.206
fs67-fpga 10.80.4.207
fs67-come 10.80.4.208 <= COMe does not boot, checked via web-page
fs67-mgmt0 10.80.4.209
fs67-mgmt1 10.80.4.210
"""
a = AssetManager()

def get_come_details(fs_number):
    d = {"mgmt_ip": "fs{}-come".format(fs_number), "mgmt_ssh_username": "fun", "mgmt_ssh_password": "123"}
    return d

def get_fpga_details(fs_number):
    d = {"mgmt_ip": "fs{}-fpga".format(fs_number), "mgmt_ssh_username": "root", "mgmt_ssh_password": "root"}
    return d

def get_bmc_details(fs_number):
    d = {"mgmt_ip": "fs{}-bmc".format(fs_number), "mgmt_ssh_username": "sysadmin", "mgmt_ssh_password": "superuser"}
    return d

new_fs = []
for line in s.split("\n"):
    if not line:
        continue
    m = re.search("fs(\d+)", line)
    if m:
        # print m.group(0)
        fs_number = int(m.group(1))
        fs_name = "fs-{}".format(fs_number)
        existing_fs = a.get_fs_spec(fs_name)
        d = {"name": fs_name,
             "fpga": get_fpga_details(fs_number),
             "come": get_come_details(fs_number),
             "bmc": get_bmc_details(fs_number),
             "gateway_ip": "10.1.105.1"}
        a.add_or_replace_fs_spec(fs_name=fs_name, spec=d)

        test_bed_spec = {
            "dut_info": {
              "0": {
                "type": "DUT_TYPE_FSU",
                "dut": fs_name
              }
            }
        }

        a.add_test_bed_spec(test_bed_name=fs_name, spec=test_bed_spec)

# print json.dumps(new_fs, indent=4)

