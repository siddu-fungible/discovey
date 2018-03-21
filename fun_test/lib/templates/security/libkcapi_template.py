from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class LibkcapiTemplate(CryptoTemplate):

    GCM_AES = "gcm(aes)"
    CCM_AES = "ccm(aes)"
    CTR_AES = "ctr(aes)"
    ECB_AES = "ecb(aes)"
    XTS_AES = "xts(aes)"
    CBC_AES = "cbc(aes)"
    AUTH_ENC = "authenc(hmac(sha1),cbc(aes))"
    KCAPI_PATH = "/usr/bin/kcapi"

    # def setup(self,path):
    #     fun_test.scp(source_file_path=path, target_ip=self.host.host_ip, target_port=self.host.ssh_port, target_username=self.host.ssh_username, target_password=self.host.ssh_password,
    #                  target_file_path="/tmp", timeout=90, recursive=True)
    #     self.host.command("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/tmp/libkcapi/lib")
    #     return True

    def parse_input_libkcapi(self, file_path):
        input_dict = eval((open(file_path, 'r')).read())
        return input_dict

    def kcapi_encrypt(self, algorithm, cipher_type, plain_text, key, iv=None, assoc_data=None, tag=None, tag_len=None, nonce=None):
        cmd_str = self.KCAPI_PATH + " -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key
        if iv:
            cmd_str += " -i " + iv
        if assoc_data:
            cmd_str += " -a " + assoc_data
        if tag:
            cmd_str += " -t " + tag
        if tag_len:
            cmd_str += " -l " + tag_len
        if nonce:
            cmd_str += " -n " + nonce

        output = self.host.command(cmd_str).strip()
        return output

    def kcapi_decrypt(self, algorithm, cipher_type, cipher_text, key, iv=None, assoc_data=None, tag=None, tag_len=None, nonce=None):
        cmd_str = self.KCAPI_PATH + " -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -k " + key
        if iv:
            cmd_str += " -i " + iv
        if assoc_data:
            cmd_str += " -a " + assoc_data
        if tag:
            cmd_str += " -t " + tag
        if tag_len:
            cmd_str += " -l " + tag_len
        if nonce:
            cmd_str += " -n " + nonce

        output = self.host.command(cmd_str).strip()
        return output
