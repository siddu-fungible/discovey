from lib.system.fun_test import *
from apc_pdu_auto import *
from scripts.storage.storage_helper import single_fs_setup


# --environment={\"test_bed_type\":\"fs-53\"}


class DataIntegrityTestcase(ApcPduTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Data Integrity test",
                              steps="""""")

    def setup(self):
        super(DataIntegrityTestcase, self).setup()
        # self = single_fs_setup(self)
        # Any additional setup can be added here

    def run(self):
        # super(DataIntegrityTestcase, self).run()
        self.pc_no = 0
        self.data_integrity_check()

    def data_integrity_check(self):
        if self.testbed_type == "suite-based":
            hosts_list = self.host_info.keys()
            required_write_hosts_list = hosts_list[:self.write_hosts]
            required_read_hosts_list = hosts_list[self.write_hosts:(self.read_hosts + 1):]
        else:
            required_hosts_list = self.verify_and_get_required_hosts_list(self.write_hosts + self.read_hosts)
            fun_test.log("Test beds: {}".format(required_hosts_list))
            required_write_hosts_list = required_hosts_list[:self.write_hosts]
            required_read_hosts_list = required_hosts_list[self.write_hosts:(self.read_hosts + 1):]
            self.sc_api = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'],
                                               api_server_port=self.api_server_port,
                                               username=self.username,
                                               password=self.password)
        fun_test.log("Test beds: {}".format(getattr(self, "host_info", "")))

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


class EcVolReboot(ApcPduTestcase):
    VOL_NAME = "EC"

    def describe(self):
        self.set_test_details(id=3,
                              summary="EC vol power",
                              steps="""""")

    def setup(self):
        testcase = self.__class__.__name__
        super(EcVolReboot, self).setup()
        self.initialize_test_case_variables(testcase)
        self = single_fs_setup(self)
        self.hosts_list = self.host_info.keys()

    def run(self):

        self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                ssh_username=self.fs['come']['mgmt_ssh_username'],
                                ssh_password=self.fs['come']['mgmt_ssh_password'])
        self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                              ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                              ssh_password=self.fs['bmc']['mgmt_ssh_password'])
        self.bmc_handle.set_prompt_terminator(r'# $')

        self.required_write_hosts_list = self.hosts_list[:self.write_hosts]
        # required_read_hosts_list = required_hosts_list[self.write_hosts:(self.read_hosts + 1):]
        self.pool_uuid = self.get_pool_id()
        self.volume_uuid_details = self.create_vol(self.write_hosts)
        self.attach_volumes_to_host(self.required_write_hosts_list)

        for pc_no in range(self.iterations):
            self.pc_no = pc_no
            fun_test.add_checkpoint(checkpoint="ITERATION : {} out of {}".format(pc_no + 1, self.iterations))
            self.attach_and_io()

            self.come_handle = ComE(host_ip=self.fs['come']['mgmt_ip'],
                                    ssh_username=self.fs['come']['mgmt_ssh_username'],
                                    ssh_password=self.fs['come']['mgmt_ssh_password'])
            self.bmc_handle = Bmc(host_ip=self.fs['bmc']['mgmt_ip'],
                                  ssh_username=self.fs['bmc']['mgmt_ssh_username'],
                                  ssh_password=self.fs['bmc']['mgmt_ssh_password'])
            self.bmc_handle.set_prompt_terminator(r'# $')

            self.sc_api = StorageControllerApi(api_server_ip=self.fs['come']['mgmt_ip'],
                                               api_server_port=self.api_server_port,
                                               username=self.username,
                                               password=self.password)

    def attach_and_io(self):
        self.get_host_handles()
        self.intialize_the_hosts()
        self.connect_the_host_to_volumes()
        self.verify_nvme_connect()
        self.start_fio_and_verify(fio_params=self.write_fio, host_names_list=self.required_write_hosts_list)
        self.disconnect_the_hosts()
        self.destoy_host_handles()
        self.reboot_test()
        self.basic_checks()
        fun_test.sleep("Wait for GUI to come up", seconds=150)

    def cleanup(self):
        try:
            self.disconnect_the_hosts()
        except:
            fun_test.log("unable to diconnect from the host")
        self.num_hosts = self.write_hosts
        super(EcVolReboot, self).cleanup()

    def initialize_test_case_variables(self, test_case_name):
        test_case_dict = getattr(self, test_case_name, {})
        if not test_case_dict:
            fun_test.critical("Unable to find the test case: {} in the json file".format(test_case_name))
        for k, v in test_case_dict.iteritems():
            setattr(self, k, v)
        fun_test.log("Initialized the test case variables: {}".format(test_case_dict))


if __name__ == "__main__":
    obj = ApcPduScript()
    obj.add_test_case(DataIntegrityTestcase())
    obj.add_test_case(EcVolReboot())
    obj.run()
