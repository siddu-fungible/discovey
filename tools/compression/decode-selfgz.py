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

if __name__ == "__main__":
    raw_infile = "/Users/radhika/Documents/selfgz.gz"
    decoded, header, trailer = decode_gzip_header(raw_infile)
    print decoded
    print decoded["compressed_block"]
    print header
    print trailer

    with open("/Users/radhika/Documents/selfgz.deflate", "wb+") as out:
        out.write(struct.pack('%dB' % len(decoded["compressed_block"]), *decoded["compressed_block"]))
