##############################################################################
#  secure_debug.py
#
#  Utility
#
#  Copyright (c) 2018. Fungible, inc. All Rights Reserved.
#
#  1. Start Python
#  2. >>> import secure_debug as sd
#  3. >>> sd.probe('sp491', '10.1.23.131')
#  4. [autodetected-target_offline] >>> sd.esecure_print_status()
#  5. [autodetected-target_offline] >>> sd.esecure_enable_debug('mykey.pem', 'mycertificate.bin', 0xFFFFFFFF, 'test')
#
#
#  3 connects to the Codescape probe (note the prompt change after)
#  4 prints the status
#  5 enables debugging access
##############################################################################


from imgtec.console.support import command
from imgtec.lib.namedenum import namedenum
from imgtec.lib.namedbitfield import namedbitfield
from imgtec.console import *
from imgtec.console import CoreFamily
import binascii
import struct
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding



##############################################################################
# Error handling
##############################################################################

class RunError(Exception):
   pass

def run(main):
   try:
      main()
   except RunError as e:
      print "ERROR: %s" % e
      exit(1)


##############################################################################
# File access
##############################################################################

def read(filename, nbytes=None):
   if filename==None:
      return ""
   print "Reading %s" % filename
   try:
      txt = open(filename, "rb").read()
   except:
      raise RunError("Cannot open file '%s' for read" % filename)
   if nbytes and len(txt)!=nbytes:
      raise RunError("File '%s' has invalid length" % filename)
   return txt

def write(filename, content, overwrite=True, tohex=False, tobyte=False):
   if not filename:
      return
   print "Writing %s" % filename
   # Overwrite
   if not overwrite and os.path.exists(filename):
      raise RunError("File '%s' already exists" % filename)
   # Open
   try:
      f = open(filename, "wb")
   except:
      raise RunError("Cannot open file '%s' for write" % filename)
   # Write
   if tohex:
      assert len(content)%4==0
      for pos in range(0, len(content), 4):
         f.write("%08X\n" % struct.unpack("<I", content[pos:pos+4]))
   elif tobyte:
      for pos in range(0, len(content)):
         f.write("%s\n" % binascii.hexlify(content[pos]))
   else:
      f.write(content)


##############################################################################
# Console commands
##############################################################################

IR_DEVICEADDR = 5
IR_APBACCESS = 6

ID_REGS = {
"CIDR3"   : 0xFFC,
"CIDR2"   : 0xFF8,
"CIDR1"   : 0xFF4,
"CIDR0"   : 0xFF0,
"PIDR3"   : 0xFEC,
"PIDR2"   : 0xFE8,
"PIDR1"   : 0xFE4,
"PIDR0"   : 0xFE0,
"PIDR4"   : 0xFD0,
"DEVTYPE" : 0xFCC,
"DEVID"   : 0xFC8
}

DEVIDS = {
"DEVID_MDH"             : 1,
"DEVID_DBU"             : 2,
"DEVID_APB2JTAG"        : 3,
"DEVID_CORE"            : 4,
"DEVID_MMBLOCK"         : 5,
"DEVID_M7000_BRIDGE"    : 6,
"DEVID_CM"              : 7,
"DEVID_ESECURE"         : 8,
}

MfrCertType = namedenum('MfrCertType',
    ChipMfr         = 0,
    SystemMfr       = 1,
)

SlaveAddr = namedbitfield('SlaveAddr',
    [('dest_id', 17, 12), ('core_id', 11, 6), ('vpe_id', 3, 0)])

BootInfo = namedbitfield('Bootinfo', [
    ('HostImage',20,20),
    ('eSecureImage',16,16),
    ('HostUpgradeFlag',12,12),
    ('eSecureUpgradeFlag',8,8),
    ('BootStep',7,0)])

WDATA = 0x8
RDATA = 0x4
CONTROL = 0x0
WR_REQ = 1<<3 #8
RD_REQ = 1<<2 #4
WR_ACK = 1<<1 #2
RD_ACK = 1<<0 #1

TIMEOUT = 1000
DEBUG = 0


def prepare_target():
    if probe().mode not in ('autodetected', 'table'):
        autodetect()
    check_use_fast_read()


#@command()
def mdh_read_new(byte_address):
    """ the inbuilt mdh read is broken on some console versions """
    try:
        return probe().tiny.ReadMemory(byte_address)
    except:
        raise RuntimeError("APB read failed try a lower TCK clock") #TODO retry abit if valid = 0

def mdh_read_old(byte_address):
    tapscan("5 %d" % IR_DEVICEADDR, "32 %d" % (byte_address & 0xf80) )
    tapscan("5 %d" % IR_APBACCESS, "39 %d" % ((byte_address & 0x7c) | 0x3) )
    result = tapd("39 %d" % ((byte_address & 0x7c) | 0x2) )

    if (result[0] & 0x3) == 0x3:
        return result[0] >> 7

    raise RuntimeError("APB read failed try a lower TCK clock") #TODO retry abit if valid = 0


#@command()
def mdh_write_new(byte_address,word):
    """ the inbuilt mdh read is broken on some console versions """
    try:
        probe().tiny.WriteMemory(byte_address, word)
    except:
        raise RuntimeError("APB read failed try a lower TCK clock") #TODO retry abit if valid = 0

def mdh_write_old(byte_address,word):
    tapscan("5 %d" % IR_DEVICEADDR, "32 %d" % (byte_address & 0xf80) )
    result = tapscan("5 %d" % IR_APBACCESS, "39 %d" % (word << 7 | (byte_address & 0x7c) | 0x1) )

    if (result[0] & 0x3) == 0x3:
        return

    raise RuntimeError("APB read failed try a lower TCK clock") #TODO retry abit if valid = 0

mdh_read_ = mdh_read_old
mdh_write_ = mdh_write_old

def check_use_fast_read():
    global  mdh_read_
    global  mdh_write_
    try:
        if listdevices()[0].family == CoreFamily.MIPSecure:
            mdh_read_ = mdh_read_new
            mdh_write_ = mdh_write_new
        else:
            mdh_read_ = mdh_read_old
            mdh_write_ = mdh_write_old
    except:
        mdh_read_ = mdh_read_old
        mdh_write_ = mdh_write_old

def esecure_read():
    """ internal only """
    mdh_write_(CONTROL,RD_REQ)
    timeout = 0
    while (mdh_read_(CONTROL) & RD_REQ) == 0: #wait for RD_REQ=1
        timeout+=1
        if timeout == TIMEOUT:
            raise RuntimeError("esecure_read: timeout waiting for RD_REQUEST to go high")
    data = mdh_read_(RDATA)
    mdh_write_(CONTROL,RD_ACK)
    timeout = 0
    while (mdh_read_(CONTROL) & RD_REQ) != 0: #wait for RD_REQ=0
        timeout+=1
        if timeout == TIMEOUT:
            raise RuntimeError("esecure_read: timeout waiting for RD_REQUEST to go low")
    mdh_write_(CONTROL,0)
    return data

def esecure_read_flush():
    mdh_read_(CONTROL)
    mdh_write_(CONTROL, 0)

#@command()
def esecure_write(data):
    """ internal only """
    mdh_write_(WDATA,data)
    mdh_write_(CONTROL,WR_REQ)
    timeout = 0
    while (mdh_read_(CONTROL) & WR_ACK) == 0:
        timeout+=1
        if timeout == TIMEOUT:
            raise RuntimeError("esecure_write: timeout waiting for WR_ACK to go high")
    mdh_write_(CONTROL,0)
    timeout = 0
    while (mdh_read_(CONTROL) & WR_ACK) != 0:
        timeout+=1
        if timeout == TIMEOUT:
            raise RuntimeError("esecure_read: timeout waiting for WR_ACK to go low")

def dump_id_regs():
    for k,v in ID_REGS.items():
        print k + " " + hex(mdh_read_(v))

#@command()
def dump_return_data(status=None):
    """internal"""
    if not status:
      status = esecure_read()
    if status >> 16 == 0:
        while (mdh_read_(CONTROL) & RD_REQ) != 0:
            print hex(esecure_read())
    else:
        print decode_cmd_status(status)

status_strs = [
"Status at last tamper    : ",
"Timestamp of last tamper : ",
"Raw tamper status        : ",
"Current Time             : ",
"Boot Status              : ",
"eSecure Firmware Version : ",
"Host Firmware Version    : "]

def dump_status_data():
    i = 0
    while (mdh_read_(CONTROL) & RD_REQ) != 0:
        if i == 0 :
            esecure_read() #dont print size field

        if i < len(status_strs):
            if i == 4:
                bs = esecure_read()
                print status_strs[i]  + hex(bs) + " : "
                print repr(BootInfo(bs))
            else:
                print status_strs[i] + hex(esecure_read())
        else:
            print "Extra data: " + hex(esecure_read())
        i+=1

status_code_str = [
   "OK",
   "Invalid Command",
   "Authorization Error",
   "Invalid Signature",
   "Bus Error",
   "Reserved",
   "Crypto Error",
   "Invalid Parameter"
]

def decode_cmd_status(status):
    sts = (status >> 16) & 0xf
    if sts >=0 and sts < len(status_code_str):
       return status_code_str[sts]

    return "reserved"

def cmd_status_ok(status):
    sts = (status >> 16) & 0xf
    return sts == 0

def dump_status():
    def get_key(id, index, name):
        esecure_write(0xC)
        esecure_write(0xFE020000 + id)
        esecure_write(index)
        status = esecure_read();
        if cmd_status_ok(status):
           print "\nPublic Key - %s [%d]:" % (name, index)
           dump_return_data(status)

    # PUF-ROM keys
    get_key(0, 2, "Debugging key")
    get_key(0, 3, "Fungible key")
    get_key(0, 4, "Fungible Enrollment key")
    get_key(1, 0, "Customer key")

    esecure_write(0x8)
    esecure_write(0xFE010000)
    print "\nStatus:"
    dump_status_data()

    esecure_write(0x8)
    esecure_write(0xFE000000)
    print "\nSerial Number:"
    dump_return_data()

def check_for_esecure():
    prepare_target()
    jtagchain()

    cidr1 = mdh_read_(ID_REGS["CIDR1"])

    if ((cidr1 >> 4) & 0xf) == 0xe:
        devid = mdh_read_(ID_REGS["DEVID"])
        if devid == 8:
            print "Found eSecure challenge interface"
            return

    print "Failed to find eSecure Challenge Interface"
    dump_id_regs()


def esecure_write_bytes(bytestr):
    if len(bytestr) % 4 != 0:
        raise RuntimeError("bytestr must always be a multiple of 4 bytes")

    words = []
    for pos in range(0, len(bytestr), 4):
        words.append(struct.unpack('<I',bytestr[pos:pos+4])[0])

    for word in words:
        if DEBUG: print "writing: "+ hex(word)
        esecure_write(word)

@command()
def esecure_print_status(device=None):
    """ Print the status from the esecure hardware """
    prepare_target()
    check_for_esecure()
    dump_status()

@command()
def esecure_enable_debug(developer_key,developer_certificate,dbg_grant,key_password=None,verbose=False,device=None):
    ''' Enable debug access to the requested devices
        developer_key - name (+ path) of the file containing the developers private (secret) key
        developer_certificate - name (+ path) of the file containing the developer certificate (signed by the manufacturer for the given developer key and allowed permissions).
        dbg_grant - 16bit bitmask, 1 bit for each dbg_grant[] in the cpu within the eSecure block,
        Note, that the request bitmask must not exceed the mask set in the certificate, as in such case eSecure will reject the request
    '''
    prepare_target()
    check_for_esecure()

    #Send Get Challenge Command
    esecure_write(0x8)
    esecure_write(0xFD000000)

    #Read Challenge
    status = esecure_read()
    if status != 0x14:
        print "Unexpected status from get challenge: " + hex(status)
        dump_return_data()
        raise RuntimeError()

    print "challenge_data:"
    challenge = [0,0,0,0]
    for i in range(len(challenge)):
        challenge[i] = esecure_read()
        print hex(challenge[i])

    if (mdh_read_(CONTROL) & RD_REQ) != 0:
        print "Warning Extra Read data still pending:"
        dump_return_data()
        #todo raise exception ??

    command = 0xFD010000

    challenge.insert(0,dbg_grant)
    challenge.insert(0,command)

    challenge_bs = ""
    for word in challenge:
        challenge_bs += struct.pack('<I',word)

    if DEBUG: print "data to sign (command + param + challenge): " +  binascii.hexlify(challenge_bs)

    #sign challenge
    developer_cert = read(developer_certificate)
    if verbose: print "developer cert:"
    if verbose: print binascii.hexlify(developer_cert)
    with open(developer_key, 'rb') as key_file:
       signing_key = serialization.load_pem_private_key(key_file.read(),
                                                        password=key_password,
                                                        backend=default_backend())

    signed_challenge = signing_key.sign(challenge_bs,
                                        padding.PKCS1v15(),
                                        hashes.SHA512())
    if DEBUG: print "signed challenge:"
    if DEBUG: print binascii.hexlify(signed_challenge)
    signed_challenge_len = len(signed_challenge)

    #Send Debug Access Request Command
    print "Unlocking..."

    # total length = 4 /length/ + 4 /command/ + 4 /dbg_grant/ + developer_cert + 4 /size/ + signed_challenge
    msglen = 4 + 4 + 4 + len(developer_cert) + 4 + signed_challenge_len

    if DEBUG: print "writing: " + hex(msglen)
    esecure_write(msglen)
    if DEBUG: print "writing: " + hex(command)
    esecure_write(command)
    if DEBUG: print "writing: " + hex(dbg_grant)
    esecure_write(dbg_grant)
    esecure_write_bytes(developer_cert)
    if DEBUG: print "writing: " + hex(signed_challenge_len)
    esecure_write(signed_challenge_len)
    esecure_write_bytes(signed_challenge)

    status = esecure_read()

    print "Status: " + decode_cmd_status(status)

    return status


@command()
def esecure_inject_certificate(certificate, customer=False):
   ''' Inject a start certificate into SBP for debugging
   Necessary only in secure mode when the PUF-ROM cannot be loaded from the ROM
   '''
   prepare_target()
   check_for_esecure()
   start_cert = read(certificate)

   command = 0xFE0A0001 if customer else 0xFE0A0000

   # total length = 4 /length/ + 4 /command/ + start_cert
   msglen = 4 + 4 + len(start_cert)

   if DEBUG: print "writing: " + hex(msglen)
   esecure_write(msglen)
   if DEBUG: print "writing: " + hex(command)
   esecure_write(command)
   esecure_write_bytes(start_cert)

   status = esecure_read()

   print "Status: " + decode_cmd_status(status)

   return status