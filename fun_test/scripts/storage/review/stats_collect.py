from scripts.storage.storage_helper import *
from lib.host.linux import Linux
from lib.templates.storage.storage_fs_template import FunCpDockerContainer

name = "F1-0"

come = Linux(host_ip="10.1.105.58", ssh_username="fun", ssh_password="123")
handle = FunCpDockerContainer(host_ip="10.1.105.58",
                              ssh_username="fun",
                              ssh_password="123",
                              ssh_port=22,
                              name=name)

cmd = "date; /opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme0 --nocli 'debug memory' | tee -a debug_memory_output.txt"

for i in range(720):
    handle.command("date >> debug_memory_output.txt")
    output = handle.command(cmd)
    print output
    fun_test.sleep("for 60 seconds", 60)

