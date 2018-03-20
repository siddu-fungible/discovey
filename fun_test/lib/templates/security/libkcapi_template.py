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

    def __init__(self, host):
        self.host = host

    def setup(self,path):
        fun_test.scp(source_file_path=path, target_ip=self.host.host_ip, target_port=self.host.ssh_port, target_username=self.host.ssh_username, target_password=self.host.ssh_password,
                     target_file_path="/tmp", timeout=90, recursive=True)
        self.host.command("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/tmp/libkcapi/lib")
        return True

    def parse_input_libkcapi(self, file_path):
        input_dict = eval((open(file_path, 'r')).read())
        return input_dict

    def enc_gcm_aes(self, algorithm, cipher_type, plain_text, key, iv, assoc_data, tag_len):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv + " -a " + assoc_data + " -l " + tag_len).strip()
        return output

    def dec_gcm_aes(self, algorithm, cipher_type, cipher_text, key, iv, assoc_data, tag):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -t " + tag + " -i " + iv + " -k " + key + " -a " + assoc_data).strip()
        return output

    def enc_ccm_aes(self, algorithm, cipher_type, plain_text, nonce, key, assoc_data, tag):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -t " + tag + " -n " + nonce + " -k " + key + " -a " + assoc_data).strip()
        return output

    def dec_ccm_aes(self, algorithm, cipher_type, cipher_text, nonce, key, assoc_data, tag):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -t " + tag + " -n " + nonce + " -k " + key + " -a " + assoc_data).strip()
        return output

    def enc_ctr_aes(self, algorithm, cipher_type, plain_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv).strip()
        return output

    def dec_ctr_aes(self, algorithm, cipher_type, cipher_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -i " + iv + " -k " + key).strip()
        return output

    def enc_ecb_aes(self, algorithm, cipher_type, plain_text, key):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key ).strip()
        return output

    def dec_ecb_aes(self, algorithm, cipher_type, cipher_text, key):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -k " + key).strip()
        return output

    def enc_xts_aes(self, algorithm, cipher_type, plain_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv).strip()
        return output

    def dec_xts_aes(self, algorithm, cipher_type, cipher_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -i " + iv + " -k " + key).strip()
        return output

    def auth_enc(self, algorithm, cipher_type, plain_text, key, iv, assoc_data, tag_len):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv + " -a " + assoc_data + " -l " + tag_len).strip()
        return output

    def enc_cbc_aes(self, algorithm, cipher_type, plain_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -e -c  \"" + algorithm + "\" -p " + plain_text + " -k " + key + " -i " + iv).strip()
        return output

    def dec_cbc_aes(self, algorithm, cipher_type, cipher_text, key, iv):
        output = self.host.command("/tmp/libkcapi/bin/kcapi -x " + cipher_type + " -c  \"" + algorithm + "\" -q " + cipher_text + " -i " + iv + " -k " + key).strip()
        return output