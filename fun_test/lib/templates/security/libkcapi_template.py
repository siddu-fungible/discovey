from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class LibkcapiTemplate(CryptoTemplate):

    GCM_AES = "gcm(aes)"

    def __init__(self, host):
        self.host = host

    def setup(self,path):
        fun_test.scp(source_file_path=path, target_ip=self.host.host_ip, target_port=self.host.ssh_port, target_username=self.host.ssh_username, target_password=self.host.ssh_password,
                     target_file_path="/tmp", recursive=True)
        self.host.command("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/tmp/libkcapi/lib")
        return True

    def parse_input_libkcapi(self, file_path):
        input_dict = eval((open(file_path, 'r')).read())
        return input_dict

    def enc_aes(self, algorithm, cipher_type, plain_text, key, iv, assoc_data, tag_len):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv + " -a  " + assoc_data + " -l " + tag_len).strip()
        return output

    def dec_aes(self, algorithm, cipher_type, cipher_text, key, iv, assoc_data, tag):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -t " + tag + " -i " + iv + " -k " + key + " -a  " + assoc_data).strip()
        return output
