from lib.system.fun_test import *
from apc_pdu_auto import *


# --environment={\"test_bed_type\":\"fs-53\"}


class DataIntegrityTestcase(ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Data Integrity test",
                              steps="""""")

    def setup(self):
        super(DataIntegrityTestcase, self).setup()
        # Any additional setup can be added here

    def run(self):
        # super(DataIntegrityTestcase, self).run()
        self.pc_no = 0
        self.data_integrity_check()

    def data_integrity_check(self):
        if self.write_hosts:
            self.sc_api = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'],
                                               api_server_port=self.api_server_port,
                                               username=self.username,
                                               password=self.password)

            required_hosts_list = self.verify_and_get_required_hosts_list(self.write_hosts + self.read_hosts)
            required_write_hosts_list = required_hosts_list[:self.write_hosts]
            required_read_hosts_list = required_hosts_list[self.write_hosts:(self.read_hosts + 1):]
            self.pool_uuid = self.get_pool_id()
            self.volume_uuid_details = self.create_vol(self.write_hosts)
            self.attach_volumes_to_host(required_write_hosts_list)
            self.get_host_handles()
            self.intialize_the_hosts()
            self.connect_the_host_to_volumes()
            self.verify_nvme_connect()
            self.start_fio_and_verify(fio_params=self.write_fio, host_names_list=required_write_hosts_list)
            self.start_fio_and_verify(fio_params=self.read_fio, host_names_list=required_write_hosts_list, cd=self.read_fio["aux-path"])
            self.scp_aux_file(from_host=required_write_hosts_list[0], to_hosts=required_read_hosts_list)
            self.disconnect_the_hosts()
            self.destoy_host_handles()
            self.reboot_test()
            self.basic_checks()
            fun_test.sleep("Wait for GUI to come up", seconds=80)
            self.attach_volumes_to_host(required_read_hosts_list)
            self.get_host_handles()
            self.intialize_the_hosts()
            self.connect_the_host_to_volumes()
            self.verify_nvme_connect()
            self.start_fio_and_verify(fio_params=self.read_fio, host_names_list=required_read_hosts_list,
                                      cd=self.read_fio["aux-path"])
            self.disconnect_the_hosts()
            self.destoy_host_handles()

    def remove_write_host_from_read_hosts_list(self, write_hosts, read_hosts):
        for write_host in write_hosts:
            if write_host in read_hosts:
                read_hosts.remove(write_host)

    def scp_aux_file(self, from_host, to_hosts):
        file_name = "local-" + self.write_fio["name"] + "-0-verify.state"
        file_dir = self.write_fio["aux-path"]
        from_host_handle = self.get_host_handle(from_host)
        for to_host in to_hosts:
            host_info = self.hosts_asset[to_host]
            from_host_handle.scp(source_file_path=file_dir + "/" + file_name,
                                 target_file_path=file_dir + "/",
                                 target_ip=host_info['host_ip'],
                                 target_username=host_info['ssh_username'],
                                 target_password=host_info['ssh_password'])

    def cleanup(self):
        self.num_hosts = self.write_hosts
        super(DataIntegrityTestcase, self).cleanup()


        # if required add any addtional cleanup


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(DataIntegrityTestcase())
    obj.run()
