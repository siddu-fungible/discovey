from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class LibkcapiTemplate(CryptoTemplate):

    GCM_AES = "gcm(aes)"
    CCM_AES = "ccm(aes)"
    CTR_AES = "ctr(aes)"
    ECB_AES = "ecb(aes)"
    XTS_AES = "xts(aes)"
    CBC_AES = "cbc(aes)"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    SHA512_224 = "sha512-224"
    SHA512_256 = "sha512-256"
    SHA3_224 = "sha3-224"
    SHA3_256 = "sha3-256"
    SHA3_384 = "sha3-384"
    SHA3_512 = "sha3-512"
    RFC3686 = "rfc3686(ctr(aes))"
    RFC4106 = "rfc4106(gcm(aes))"
    RFC4309 = "rfc4309(ccm(aes))"
    AUTH_ENC = "authenc(hmac(sha1),cbc(aes))"
    KCAPI_PATH = "/usr/bin/kcapi"

    # def setup(self,path):
    #     fun_test.scp(source_file_path=path, target_ip=self.host.host_ip, target_port=self.host.ssh_port,
    #                       target_username=self.host.ssh_username, target_password=self.host.ssh_password,
    #                  target_file_path="/tmp", timeout=90, recursive=True)
    #     self.host.command("export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/tmp/libkcapi/lib")
    #     return True

    def setup(self):
        self.load_funcrypto()
        self.verify_funcrypto()
        self.host.command("cat /proc/crypto | grep -i funcrypto")
        return True

    def parse_input_libkcapi(self, file_path):
        input_dict = eval((open(file_path, 'r')).read())
        return input_dict

    def kcapi_cmnd(self, algorithm, cipher_type, key, encrypt=True, plain_text=None, cipher_text=None, iv=None,
                   assoc_data=None, tag=None, tag_len=None, nonce=None, aux_param=None):
        if encrypt:
            cmd_str = self.KCAPI_PATH + " -x " + cipher_type + " -e -c  \"" + algorithm + "\" -k " + key
        else:
            cmd_str = self.KCAPI_PATH + " -x " + cipher_type + " -c  \"" + algorithm + "\" -k " + key
        if plain_text:
            cmd_str += " -p " + plain_text
        if cipher_text:
            cmd_str += " -q " + cipher_text
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
        if aux_param:
            cmd_str += aux_param

        output = self.host.command(cmd_str).strip()
        return output

    def kcapi_dgst(self, algorithm, cipher_type, msg=None):

        cmd_str = self.KCAPI_PATH + " -x " + cipher_type + " -c " + algorithm + " -p " + msg

        output = self.host.command(cmd_str).strip()
        return output
