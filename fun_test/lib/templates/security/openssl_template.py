from lib.system.fun_test import fun_test
from lib.templates.security.crypto_template import CryptoTemplate


class OpenSslTemplate(CryptoTemplate):

    def __init__(self, host):
        self.host = host

    def setup(self):
        self.load_funcrypto()
        self.verify_openssl_version()
        self.verify_funcrypto()
        return True

    def compute_digest(self, openssl_type, algorithm, digest_input, engine=None):
        #openssl_command = CryptoTemplate.OPENSSL + " " + openssl_type + " -" + CryptoTemplate.ENGINE + " " + CryptoTemplate.AF_ALG + " -" + algorithm + " " + digest_input
        openssl_command = CryptoTemplate.OPENSSL + " " + openssl_type + " -" + algorithm + " " + digest_input
        digest_output = ((self.host.command(openssl_command)).split("="))[1].strip()
        return digest_output

    def get_error_logs(self):
        print "error logs"
