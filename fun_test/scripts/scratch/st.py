import hashlib

def get_hex(value):
    return ''.join(x.encode('hex') for x in value)

def get_sha256_hex(value):
    m = hashlib.sha256()
    m.update(value)
    return get_hex(value=m.digest())

value = "000000000000003000000000000000300000000000000030"

print get_sha256_hex(value=value)