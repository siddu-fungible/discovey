from lib.system.fun_test import *
from apc_pdu_auto import *


class DataIntegrityTestcase(ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Data Integrity test",
                              steps="""""")

    def setup(self):
        super(DataIntegrityTestcase, self).setup()
        # Any additional setup can be added here

    def run(self):
        super(DataIntegrityTestcase, self).run()
        # If you change the run

    def basic_checks(self):
        # super(DataIntegrityTestcase, self).basic_checks()
        pass

    def data_integrity_check(self):
        if self.write_hosts:
            self.sc_api = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'],
                                               api_server_port=self.api_server_port,
                                               username=self.username,
                                               password=self.password)
            required_hosts_list = self.verify_and_get_required_hosts_list(self.write_hosts)
            self.pool_uuid = self.get_pool_id()
            self.volume_uuid_details = self.create_vol(self.write_hosts)
            self.attach_volumes_to_host(required_hosts_list)
            self.get_host_handles()
            # self.intialize_the_hosts()
            self.connect_the_host_to_volumes()
            self.verify_nvme_connect()
            self.start_fio(required_hosts_list[0], fio_params=self.write_fio, timeout=10000)
            self.disconnect_the_hosts()
            self.destoy_host_handles()

    def cleanup(self):
        super(DataIntegrityTestcase, self).cleanup()
        #if required add any addtional cleanup


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(DataIntegrityTestcase())
    obj.run()