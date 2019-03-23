from lib.host.linux import Linux


class Host(Linux):
    pass

class Qemu(Host):
    PROMPT_TERMINATOR_DEFAULT = r'\$ '

'''
class DockerHost(Linux):
    pass


    @staticmethod
    def get(asset_properties):
        """

        :rtype: object
        """
        prop = asset_properties
        return DockerHost(host_ip=prop["host_ip"],
                     ssh_username=prop["mgmt_ssh_username"],
                     ssh_password=prop["mgmt_ssh_password"],
                     ssh_port=prop["mgmt_ssh_port"])
'''