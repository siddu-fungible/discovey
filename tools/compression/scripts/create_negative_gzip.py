from tools.compression.lib.utils import *

"""
# Minimum gzip header
+---+---+---+---+---+---+---+---+---+---+
|ID1|ID2|CM |FLG|     MTIME     |XFL|OS | (more-->)
+---+---+---+---+---+---+---+---+---+---+
Only ID1, ID2, & CM are required for decompression
ID1 - 0x1f
ID2 - 0x8b
CM - 0x08
"""
gzip_header = "1f8b0800000000000000"
gzip_bin_header = binascii.unhexlify(gzip_header)

# This trailer has CRC32 and ISIZE for uncompressed char 'a'
gzip_trailer = "43beb7e801000000"
gzip_bin_trailer = binascii.unhexlify(gzip_trailer)


def create_gzip_files(deflate_block, gzip_file):
    with open(gzip_file, "w+") as gzip:
        gzip.write(gzip_bin_header)
        gzip.write(struct.pack('%dB' % len(deflate_block), *deflate_block))
        gzip.write(gzip_bin_trailer)


if __name__ == "__main__":
    ascii_str = []
    # Pass ASCII literals from 0 to 143
    # for i in range(65, 91):
    #     ascii_str.append(chr(i))
    ascii_str.append(chr(97))

    # Create plain txt file
    with open("/tmp/A.plain", "wb+") as data:
        data.write(''.join(ascii_str))

    # Create deflate file
    with open("/tmp/A_invalid_stored.deflate", "wb+") as out:
        result = create_deflate_block('stored', ''.join(ascii_str))
        if result:
            out.write(struct.pack('%dB' % len(result), *result))
    create_gzip_files(result, "/tmp/A_invalid_stored.gz")

    with open("/tmp/A_invalid_fixed.deflate", "wb+") as out:
        result = create_deflate_block('fixed', ''.join(ascii_str))
        if result:
            out.write(struct.pack('%dB' % len(result), *result))
    create_gzip_files(result, "/tmp/A_invalid_fixed.gz")
