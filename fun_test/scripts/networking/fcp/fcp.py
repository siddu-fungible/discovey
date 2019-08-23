from lib.system.fun_test import *


class Fcp:
    def __init__(self, linux_obj, ftep_dict):
        """Init

        :param linux_obj: linux obj
        :param ftep_dict: dict for DPU and FTEP list, e.g. {'F1-0': ['9.0.0.2',], 'F1-1': ['9.0.0.1']}
        """
        self.linux_obj = linux_obj
        self.ftep_dict = ftep_dict
        self.check_file = 'check'
        self.del_file = 'del'
        self.set_file = 'set'

        def create_file(file, cmds):
            linux_obj.command('{} rm {}'.format(cmd_prefix, file))
            linux_obj.command('{} touch {}'.format(cmd_prefix, file))
            for cmd in cmds:
                linux_obj.command('{} echo {} > {}'.format(cmd_prefix, cmd, file))

        for dpu in ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(dpu)
            # check
            cmds = ['SELECT 1', 'KEYS *fcp-tunnel*']
            create_file(self.check_file, cmds)

            cmds_del = ['SELECT 1', ]
            cmds_set = ['SELECT 1', ]
            for ftep in ftep_dict[dpu]:
                key = "openconfig-fcp:fcp-tunnel[ftep=\'{}\']".format(ftep)
                cmds_del.append('DEL {}'.format(key))
                cmds_set.append('SET {0} {0}'.format(key))

            # del
            create_file(self.del_file, cmds_del)
            # set
            create_file(self.set_file, cmds_set)

    def redis_get_ftep_keys(self):
        for dpu in self.ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(dpu)
            self.linux_obj.command('{} redis-cli < {}'.format(cmd_prefix, self.check_file))

    def redis_del_fteps(self):
        for dpu in self.ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(dpu)
            self.linux_obj.command('{} redis-cli < {}'.format(cmd_prefix, self.del_file))

    def redis_set_fteps(self):
        for dpu in self.ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(dpu)
            self.linux_obj.command('{} redis-cli < {}'.format(cmd_prefix, self.set_file))

    def redis_check_fteps(self):
        for dpu in self.ftep_dict:
            cmd_prefix = 'docker exec {} bash -c'.format(dpu)
            self.linux_obj.command('{} redis-cli < {}'.format(cmd_prefix, self.check_file))

