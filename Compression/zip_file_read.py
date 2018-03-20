import os

from string import printable
from zipfile import *
from gzip import *

file = "/Users/aameershaikh/Downloads/cant/asyoulik.txt.gz"
op = GzipFile(file, 'r')
print op.read()
#with ZipFile(file, 'r') as mz:
#    print mz.read(name='a.txt')




'''
def read_zip_file(name):
    with open(name, 'rb') as f_obj:
        content = f_obj.read()
    return content


zip_text = read_zip_file(file_name)
for i in zip_text:
    print i.__repr__(),

zip_hex = zip_text
hex_dict = {}
print len(zip_hex)
hex_dict['local_header'] = zip_hex[0:4]
hex_dict['version'] = zip_hex[4:6]
hex_dict['gp_bit_flag'] = zip_hex[6:8]
hex_dict['comp_method'] = zip_hex[8:10]
hex_dict['lat_mod_time'] = zip_hex[10:12]
hex_dict['lat_mod_date'] = zip_hex[12:14]
hex_dict['crc_32'] = zip_hex[14:18]
hex_dict['comp_size'] = zip_hex[18:22]
hex_dict['uncpm_size'] = zip_hex[22:26]
hex_dict['file_name_len'] = zip_hex[26:28]
hex_dict['extra_field_len'] = zip_hex[28:30]
hex_dict['file_cmt_len'] = zip_hex[30:32]
hex_dict['disk_no_start'] = zip_hex[32:34]
hex_dict['intrnl_file_attr'] = zip_hex[34:36]
hex_dict['ext_file_attr'] = zip_hex[36:40]
hex_dict['rel_ofset_hedr'] = zip_hex[40:44]
hex_dict['file_name'] = zip_hex[44: 44 + int(hex_dict['file_name_len'].encode('hex'))]
# extra fileld
# file comment
for k in hex_dict:
    print k,':', hex_dict[k].encode('hex')
'''
