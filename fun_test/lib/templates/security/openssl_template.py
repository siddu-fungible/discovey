from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class OpenSslTemplate(CryptoTemplate):

    OPENSSL = "openssl"
    OPENSSL_VERSION = "1.0.2k"
    DGST = "dgst"
    MD5 = "md5"
    ENC = "enc"
    PASS = "pass"
    HMAC = "hmac"
    SHA1 = "sha1"
    SHA224 = "sha224"
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"
    AESCBC128 = "aes-128-cbc"

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

    def compute_md5(self, digest_input):
        openssl_command = self.OPENSSL + " " + self.DGST + " -" + self.MD5 + " " + digest_input
        md5_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return md5_output

    def compute_digest(self, algorithm, digest_input, engine=None):
        #openssl_command = self.OPENSSL + " " + self.DGST + " -" + CryptoTemplate.ENGINE + " " + CryptoTemplate.AF_ALG + " -" + algorithm + " " + digest_input
        openssl_command = self.OPENSSL + " " + self.DGST + " -" + algorithm + " " + digest_input
        digest_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return digest_output

    def compute_hmac(self, algorithm, hmac_input, key_type=None, key=None, engine=None):
        openssl_command = self.OPENSSL + " " + self.DGST + " -" + algorithm + " -" + self.HMAC + " " + key + " " + hmac_input
        hmac_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return hmac_output

    def encrypt(self, algorithm, encrypt_input_file, encrypt_output_file, key):
        openssl_command = self.OPENSSL + " " + self.ENC + " -e" + " -" + algorithm + " -in " + encrypt_input_file + " -out " + encrypt_output_file \
                          + " -" + self.PASS + " " + self.PASS + ":" + key
        self.host.command(openssl_command)
        return True

    def decrypt(self, algorithm, decrypt_input_file, decrypt_output_file, key):
        openssl_command = self.OPENSSL + " " + self.ENC + " -d" + " -" + algorithm + " -in " + decrypt_input_file + " -out " + decrypt_output_file \
                          + " -" + self.PASS + " " + self.PASS + ":" + key
        self.host.command(openssl_command)
        return True

    def get_error_logs(self):
        print "error logs"
