from lib.templates.security.crypto_template import CryptoTemplate


class LibkcapiSpeedTemplate(CryptoTemplate):

    GCM_AES = "gcm-aes-"
    CCM_AES = "ccm-aes-"
    CTR_AES = "ctr-aes-"
    ECB_AES = "ecb-aes-"
    XTS_AES = "xts-aes-"
    CBC_AES = "cbc-aes-"
    SHA1 = "sha1-"
    SHA224 = "sha224-"
    SHA256 = "sha256-"
    SHA384 = "sha384-"
    SHA512 = "sha512-"
    HMAC_SHA1 = "hmac-sha1-"
    HMAC_SHA224 = "hmac-sha224-"
    HMAC_SHA256 = "hmac-sha256-"
    HMAC_SHA384 = "hmac-sha384-"
    HMAC_SHA512 = "hmac-sha512-"
    RFC3686 = "rfc3686(ctr(aes))"
    RFC4106 = "rfc4106(gcm(aes))"
    RFC4309 = "rfc4309(ccm(aes))"
    AUTH_ENC = "authenc(hmac(sha1),cbc(aes))"
    KCAPI_PATH = "/root/libkcapi/bin/kcapi-speed"
    TASKSET_CMD = "taskset --cpu-list 1 "

    def setup(self):
        pass


# Block size is multiplied by default size of 16.
    def kcapi_cmnd(self, algorithm, driver, speed=True, test_time=None, block_size=None, aux_param=None):
        if driver == "generic":
            self.unload_funcrypto()
        elif driver == "funcrypto":
            self.unload_aesni()
            self.unload_funcrypto()
            self.load_funcrypto()
            self.verify_funcrypto()
        else:
            self.unload_funcrypto()
            self.load_aesni()

        if speed:
            cmd_str = self.TASKSET_CMD + self.KCAPI_PATH + " --cipher \"" + algorithm + driver + "\""
        if test_time:
            cmd_str += " --time " + test_time
        if block_size:
            cmd_str += " --blocks " + block_size
        if aux_param:
            cmd_str += aux_param

        output = self.host.command(cmd_str, timeout=80).strip()
        return output
