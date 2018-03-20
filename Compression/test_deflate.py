from lib.data_generator import *
from lib.compress import *


# LZ77
# LZ77 compression
# compression for all byte values (0-255)
def test_compress_byte_data(byte_data, size):
    result = False
    seq = "{}" * (size)
    str = seq.format(*([byte_data] * size))
    resp = compress(str)
    if resp:
        result = True
    return result


# Compression with repeat for random patterns
def test_repeat_pattern(pattern, repeat_count):
    return test_compress_byte_data(pattern, size=len(pattern) * repeat_count)


# test with Offset Distance 1 to 32K-1.
def test_pattern_offset(pattern, distance):
    junk_count = junk_list(distance)
    offset_list = [''.join(generate_pattern(x)) for x in junk_count]
    offset_string = ''.join(offset_list)
    data_str = "{0}{1}{0}".format(pattern, offset_string)
    resp = compress(data_str)
    return True


# test with Supported pattern length (3-258)
# Negative case len <3,  len>258
def test_pattern_len(patern_len, distance):
    patern_data = ''.join(generate_pattern(patern_len))
    return test_pattern_offset(patern_data, distance)


# sliding window 4KB to 32KB

def test_sliding_window():
    pass    # ToDo determin how to modify window len


def test_repeat_patern_with_garbage(size, repeat_count, patern_len):
    patern_str = "".join(generate_pattern(patern_len))
    padding_size = size - (repeat_count*patern_len)
    str_list = [''.join(generate_pattern(x))for x in junk_list(padding_size)] + [patern_str] * repeat_count
    random.shuffle(str_list)
    data_str = ''.join(str_list)
    resp = compress(data_str)
    if resp:
        return True
    else:
        return False

# Duplicate pattern at beginning and end of window
# pattern splitting to next window
#
# decompression
# .


# static huffman
# Compression with static huffman

# Decompression with static huffman
# Dynamic Huffman:
# Compression with Dynamic Huffman
# Decompression with Dynamic Huffman


