from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class OpenSslTemplate(CryptoTemplate):

    OPENSSL = "openssl"
    OPENSSL_VERSION = "1.0.2k"
    DGST = "dgst"
    HMAC = "hmac"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"

    def __init__(self, host):
        self.host = host

    def setup(self):
        self.load_funcrypto()
        self.verify_openssl_version()
        self.verify_funcrypto()
        return True

    def verify_openssl_version(self):
        # validate existence of OpenSSL
        version_output = (self.host.command(self.OPENSSL + " " + self.VERSION)).split(" ")
        fun_test.debug("OpenSSL version output: {}".format(version_output))
        version = version_output[1]
        fun_test.test_assert_expected(expected=self.OPENSSL_VERSION,
                                      actual=version,
                                      message="OpenSSL version as expected")
        return True

    def compute_digest(self, algorithm, digest_input, engine=None):
        #openssl_command = self.OPENSSL + " " + self.DGST + " -" + CryptoTemplate.ENGINE + " " + CryptoTemplate.AF_ALG + " -" + algorithm + " " + digest_input
        openssl_command = self.OPENSSL + " " + self.DGST + " -" + algorithm + " " + digest_input
        digest_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return digest_output

    def compute_hmac(self, algorithm, key, hmac_input, engine=None):
        openssl_command = self.OPENSSL + " " + self.DGST + " -" + algorithm + " -" + self.HMAC + " " + key + " " + hmac_input
        hmac_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return hmac_output

    def get_error_logs(self):
        print "error logs"
