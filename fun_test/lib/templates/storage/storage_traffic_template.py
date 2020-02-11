from lib.system.fun_test import *


class StorageTrafficTemplate:
    """
    Storage Traffic using FIO
    """
    def __init__(self, storage_operations_template):
        self.storage_operations_template = storage_operations_template
        self.topology = self.storage_operations_template.topology

    def basic_rw_traffic(self, host_obj):
        host_obj_list = []
        if not isinstance(host_obj, list):
            host_obj_list.append(host_obj)
        else:
            host_obj_list = host_obj

        for host_obj in host_obj_list:
            nvme_device_name = self.storage_operations_template.get_host_nvme_device(host_obj=host_obj)
            traffic_result = self.fio_basic(host_obj=host_obj, filename="/dev/" + nvme_device_name)
            fun_test.test_assert(expression=traffic_result,
                                 message="Host : {} FIO traffic result".format(host_obj.name))
            fun_test.log(traffic_result)

    def fio_with_integrity_check(self, host_linux_handle, filename, job_name="Fungible_nvmeof", numjobs=1, iodepth=1,
                                 runtime=600, bs="4k", ioengine="libaio", direct=1, time_based=False, norandommap=True,
                                 verify="md5", verify_fatal=1,offset="0kb", verify_state_save=1, verify_dump=1,
                                 verify_state_load=1, verify_integrity=False):
        result = True
        if not verify_integrity:
            host_linux_handle.command("cd /tmp; rm -fr test_fio_with_integrity;"
                                      "mkdir test_fio_with_integrity; cd test_fio_with_integrity")
            fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw="write",
                                               filename=filename, ioengine=ioengine, direct=direct,
                                               timeout=1500, fill_device=1, do_verify=0,
                                               verify=verify, verify_fatal=verify_fatal, offset=offset,
                                               verify_state_save=verify_state_save, verify_dump=verify_dump)
            result &= fio_result

        host_linux_handle.command("cd /tmp/test_fio_with_integrity; ls")
        fio_result = host_linux_handle.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw="read",
                                           filename=filename, ioengine=ioengine, direct=direct,
                                           timeout=1500, offset=offset, fill_device=1,
                                           verify=verify, do_verify=1, verify_fatal=verify_fatal,
                                           verify_state_load=verify_state_load, verify_dump=verify_dump)
        result &= fio_result
        return result

    def fio_basic(self, host_obj, filename, job_name="Fungible_nvmeof", numjobs=1, iodepth=1, rw="readwrite",
                  runtime=60, bs="4k", ioengine="libaio", direct=1, time_based=True, norandommap=True, verify=None,
                  do_verify=None):
        fio_result = host_obj.fio(name=job_name, numjobs=numjobs, iodepth=iodepth, bs=bs, rw=rw,
                                  filename=filename, runtime=runtime, ioengine=ioengine, direct=direct,
                                  timeout=runtime+15, time_based=time_based, norandommap=norandommap,
                                  verify=verify, do_verify=do_verify)
        return fio_result
