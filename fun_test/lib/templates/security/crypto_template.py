class CryptoTemplate:

    # common variabes used

    openssl = "openssl"
    sha1 = "sha1"
    dgst = "dgst"
    funcrypto = "funcrypto"
    version = "version"
    openssl_version = "1.0.2k"

    def __init__(self, host):
        self.host = host

    def compute_digest(self, openssl_type, algorithm, digest_input, engine=None):
        return True

    def encrypt(self, algorithm, encrypt_input, key):
        return True

    def decrypt(self, algorithm, decrypt_input, key):
        return True