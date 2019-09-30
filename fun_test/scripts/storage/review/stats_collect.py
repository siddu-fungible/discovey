from lib.system.fun_test import *
from scripts.storage.storage_helper import *
from lib.templates.storage.storage_fs_template import FunCpDockerContainer


class StatsCollect(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Bring up the container
                """)

    def setup(self):
        pass

    def cleanup(self):
        pass


class StatsCollectTC(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect to a container",
                              steps="""
                1. Using dpcsh in nocli mode fetch debug memory stats every 60 secs.
                                      """)

    def setup(self):
        pass

    def run(self):
        name = "F1-0"

        handle = FunCpDockerContainer(host_ip="10.1.105.58", ssh_username="fun", ssh_password="123", ssh_port=22,
                                      name=name)

        cmd = "date; /opt/fungible/FunSDK/bin/Linux/dpcsh/dpcsh --pcie_nvme_sock=/dev/nvme0 --nocli 'debug memory' | tee -a debug_memory_stats.txt"

        for i in range(720):
            fun_test.log("Current iteration is: {}".format(i))
            handle.command("date >> debug_memory_stats.txt")
            output = handle.command(cmd)
            fun_test.sleep("for 60 seconds", 60)

    def cleanup(self):
        pass


if __name__ == "__main__":
    sc = StatsCollect()
    sc.add_test_case(StatsCollectTC())
    sc.run()