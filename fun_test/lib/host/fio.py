from lib.system.fun_test import fun_test
from lib.host.linux import Linux

class Fio(Linux):

    def __init__(self, asset_properties):
        self.internal_ip = asset_properties["internal_ip"]
        super(Fio, self).__init__(host_ip=asset_properties["host_ip"],
                                  ssh_username=asset_properties["mgmt_ssh_username"],
                                  ssh_password=asset_properties["mgmt_ssh_password"],
                                  ssh_port=asset_properties["mgmt_ssh_port"])

    @fun_test.safe
    def send_traffic(self, destination_ip, block_size="4k", size="128k"):
        pass
        fio_command = "fio --name=fun_nvmeof --ioengine=fun --rw=readwrite --bs={} --size={} --numjobs=1  --iodepth=8 --do_verify=0 --verify=md5 --verify_fatal=1 --source_ip={} --dest_ip={} --io_queues=1 --nrfiles={} --nqn=nqn.2017-05.com.fungible:nss-uuid1 --nvme_mode=IO_ONLY".format(
            block_size, size, self.internal_ip, destination_ip, 1)
        return self.command(fio_command)

    @staticmethod
    def get(asset_properties):
        return Fio(asset_properties=asset_properties)
