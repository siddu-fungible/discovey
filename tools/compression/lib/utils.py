import binascii
import os
import struct


# Test data for Huffman encoder
def gen_repeated_seq(seq_length, repeat_count):
    result = False
    seq = os.urandom(seq_length)
    str = seq * repeat_count
    return str


def fwrite_raw_bytes(filename, data):
    with open(filename, "w+") as in_file:
        in_file.write(data)
    return 0


def generate_filename(filepath, length, offset):
    file_prefix = "length-" + str(length) + "-offset-" + str(offset)
    filename = str(filepath) + '/' + str(file_prefix) + '.input'
    return filename


def generate_ascii_literals(start, end, file, repeat=1, random=False):
    with open(file, "w+") as in_file:
        for n in range(0, repeat):
            for i in range(start, end + 1):
                in_file.write(chr(i))
    return 0


def generate_static_huffman(start, end, start_huff_code, print_ascii=False):
    code_len = len(start_huff_code)
    code_list = [{"lit": start,
                  "code": start_huff_code,
                  "ascii_code": None}]
    if print_ascii:
        code_list[0]["ascii_code"] = chr(start)

    huff_code = start_huff_code
    for val in range(start + 1, end + 1):
        huff_code = bin(int(huff_code, 2) + 1)[2:]
        code_list.append({"lit": val,
                          "code": huff_code.zfill(code_len),
                          "ascii_code": chr(val) if print_ascii else None})

    return code_list


def get_huff_code(literal):
    """
    https://stackoverflow.com/questions/17398931/deflate-encoding-with-static-huffman-codes
    This method will get the 8 bit huff codes for literal values 0 - 143
    """
    # Get ascii code of literal; ord() returns decimal value
    ascii_code = ord(literal)
    if ascii_code < 0 or ascii_code > 143:
        return False
    # Add 0x30
    incr = int("0x30", 16)
    huff_code = ascii_code + incr
    bin_huff_code = bin(huff_code)[2:].zfill(8)

    # Returned the reversed code
    return bin_huff_code[::-1]


def create_deflate_block(block_type, literals):
    final_block = False
    last = '1'
    literals_reversed = literals[::-1]
    if str(block_type).lower() == 'fixed':
        code = '01'
        end_of_block = '0000000'
        lit_code_arr = []
        for lit in literals_reversed:
            lit_code = get_huff_code(lit)
            if not lit_code:
                return False
            lit_code_arr.append(get_huff_code(lit))

        # Since inflate reads bits LSB to MSB we create encoded block in reverse
        encoded_block = end_of_block + ''.join(lit_code_arr) + code + last # Append code + last to literal

        ## Bytes are read left to right, so we divide the encoded_block in 8 bits and string them in reverse

        #Extract first block
        final_block = bytearray()
        final_block.append(int(encoded_block[-8:], 2))
        remain_blocks = len(encoded_block)/8

        # print encoded_block[-8:].zfill(8)
        # print encoded_block[-16:-8].zfill(8)
        for i in range(1, remain_blocks+1):
            end = -(8 * i)
            start = end - 8
            final_block.append(int(encoded_block[start:end].zfill(8), 2))   # Zero fill last chunk if < 8 bits
    else:
        pass
        # Need to write logic to create stored and dynamic blocks

    return final_block


def zfill_bytearr(bytearr):
    out_arr = []
    for b in bytearr:
        out_arr.append(bin(int(binascii.hexlify(b), 16))[2:].zfill(8))

    return out_arr


def reorder_bits(byte_str):
    return byte_str[::-1]


def decode_gzip_header(file):
    """
    :param file:
    :return:
    $ hexdump a.txt.gz
    0000000 1f 8b 08 08 08 45 c5 5a 00 03 61 2e 74 78 74 00
    0000010 4b 04 00 43 be b7 e8 01 00 00 00
    000001b
    Header Info: http://www.forensicswiki.org/wiki/Gzip
    """

    with open(file, 'r') as infile:
        indata = bytearray(infile.read())

    print "Hexdump of entire file:\t%s" % binascii.hexlify(indata)

    # Parsing the gzip file header; Reference - http://www.zlib.org/rfc-gzip.html#file-format
    decoded = {}
    header = bytearray()
    trailer = bytearray()

    index = 0

    if str(indata[0]) + str(indata[1]) == '31139':

        # Gzip file
        header.extend(indata[0:2])     # Add to header

        index = 2  # Move index to compress type
        compress_type = indata[index]
        header.append(compress_type)

        if compress_type <= 7:
            return "Error: Unknown compression method"
        elif compress_type == 8:
            index = 3  # Move index to flags
            flags = indata[index]
            header.append(flags)
            ftext_set = (int('00000001', 2) & flags)
            fhcrc_set = (int('00000010', 2) & flags)
            fextra_set = (int('00000100', 2) & flags)
            fname_set = (int('00001000', 2) & flags)
            fcomment_set = (int('00010000', 2) & flags)
            # Bits 5, 6, 7 are reserved; so ignoring

            if ftext_set:
                decoded["is_ascii"] = True

            index = 4  # Move index to modified time
            mtime = indata[index:index + 4]  # Mtime is 4 bytes
            header.extend(mtime)
            decoded["mtime"] = mtime    # TODO: Need to convert into datatime repr

            index = 8  # Move index to xtra flags
            xfl = indata[index]
            header.append(xfl)
            decoded["xflags"] = xfl

            index = 9  # Move index to OS type
            os = indata[index]
            header.append(os)
            decoded["os"] = os

            index = 10  # Move index to beginning of remaining header
            if fextra_set:
                xlen = indata[index:index + 2]  # 2 byte length
                index += 2
                xtra_fields = indata[index:index + xlen]
                header.extend(xtra_fields)
                decoded["xtra_fields"] = xtra_fields
                index += xlen
            if fname_set:
                fname = []
                while True:
                    if indata[index] != 0:
                        fname.append(chr(indata[index]))
                        header.append(indata[index])
                        index += 1
                    else:
                        break
                decoded["fname"] = "".join(fname)
                index += 1
            if fcomment_set:
                fcomment = []
                while True:
                    if indata[index] != 0:
                        fcomment.append(chr(indata[index]))
                        header.append(indata[index])
                        index += 1
                    else:
                        break
                decoded["fcomment"] = "".join(fcomment)
                index += 1
            if fhcrc_set:
                fhcrc = indata[index:index + 2]  # CRC is 2 bytes
                header.extend(fhcrc)
                decoded["crc16"] = fhcrc
                index += 2

            # Compressed block
            decoded["compressed_block"] = indata[index:-8]  # Compressed block is rest except last 8 bytes

            crc32_isize = indata[-8:]
            crc32 = crc32_isize[:4]     # 4 bytes is CRC32
            isize = crc32_isize[-4:]    # 4 bytes is initial file size
            decoded["crc32"] = crc32
            decoded["input_size"] = int(binascii.hexlify(isize), 16)
            # TODO: Add code to return trailer; for now return remainder compressed file - header
            trailer = crc32_isize

    else:
        # Assuming no gzip header
        decoded["compressed_block"] = indata[index:]
        header = None
        trailer = None

    # hexdump = binascii.hexlify(indata)
    # return hexdump

    return (decoded, header, trailer)


if __name__ == '__main__':
    """
    print generate_static_huffman(0, 143, '00110000', print_ascii=True)
    print generate_static_huffman(144, 255, '110010000')
    # print generate_static_huffman(256, 279, '0000000')
    # print generate_static_huffman(280, 287, '11000000')
    print generate_static_huffman(0, 31, '00000')

    raw_infile = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/a.txt.deflate"
    decoded, header, trailer = decode_gzip_header(raw_infile)

    # print decoded
    print "Header:\t%s" % (binascii.hexlify(header) if header is not None else None)
    print "Compressed block:\t%s" % (binascii.hexlify(decoded["compressed_block"]))
    print "Trailer:\t%s" % (binascii.hexlify(trailer) if trailer is not None else None)

    # hex_compressed_data = binascii.hexlify(decoded["compressed_block"])
    # print bin(int(hex_compressed_data, 16))[2:]

    # compressed_data = decoded["compressed_block"]
    # reordered_bits = []
    # for b in compressed_data:
    #     reordered_bits.append(reorder_bits(bin(b)[2:].zfill(8)))
    #
    # print ''.join(reordered_bits)

    # hexdata = "73494dcb492c4955001100"
    # reordered_bits = []
    # for byte in zfill_bytearr(binascii.unhexlify(hexdata)):
    #     reordered_bits.append(reorder_bits(byte))
    # print ''.join(reordered_bits)
    """

    ascii_str = []
    # Pass ASCII literals from 0 to 143
    for i in range(0, 144):
        ascii_str.append(chr(i))

    # Create plain txt file
    with open("/tmp/ascii_str.txt", "wb+") as data:
        data.write(''.join(ascii_str))

    # Create deflate file
    with open("/tmp/ascii_str.deflate", "wb+") as out:
        result = create_deflate_block('fixed', ''.join(ascii_str))
        if result:
            out.write(struct.pack('%dB' % len(result), *result))

