from lib.data_generator import *

# LZ77
# LZ77 compression
# compression for all byte values (0-255)


def test_compress_byte_data(byte_data, size):
    result = False
    seq = "{}" * (size)
    str = seq.format(*([byte_data] * size))
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
    return True


# test with Supported pattern length (3-258)
# Negative case len <3,  len>258
def test_pattern_len(patern_len, distance):
    patern_data = ''.join(generate_pattern(patern_len))
    return test_pattern_offset(patern_data, distance)


# sliding window 4KB to 32KB

def test_sliding_window(self):
    pass  # ToDo determine how to modify window len


def test_repeat_patern_with_garbage(self, size, repeat_count, patern_len):
    patern_str = "".join(generate_pattern(patern_len))
    padding_size = size - (repeat_count * patern_len)
    str_list = [''.join(generate_pattern(x)) for x in junk_list(padding_size)] + [patern_str] * repeat_count
    random.shuffle(str_list)
    data_str = ''.join(str_list)
    return True


# overlapping pattern
# pat1 + junk data + pat1+ junk_data + pat1(modified)
def test_overlapping_pattern1(self, size, pat_len, repeat_count, modifier_count):
    data_patern = ''.join(generate_pattern(pat_len))
    junk_byte_count = size - (repeat_count * pat_len)
    pattern_str = generate_pattern(pat_len)
    padding_count = junk_list(junk_byte_count)
    data_str = ""
    count = 0
    for i in padding_count:
        if count < repeat_count:
            data_str += data_patern + ''.join(generate_pattern(i))
            count += 1

    temp_patern = data_patern[:(-1 * modifier_count)]
    modified_pattern = temp_patern + ''.join(generate_pattern(modifier_count))
    data_str = data_str + modified_pattern
    return compress(data_str)


# pat1 + junk_data + (pat1)*n + (modified_pat1)*n
def test_overlapping_pattern2(self, size, pat_len, pat_count, mod_pat_count):
    data_patern = ''.join(generate_pattern(pat_len))
    data_format = "{}" * pat_count
    data_stream = data_format.format(*([data_patern] * pat_count))

    junk_size = size - pat_len * (pat_count + mod_pat_count)
    junk_data = [''.join(generate_pattern(x)) for x in junk_list(junk_size)]
    junk_str = ''.join(junk_data)
    data_str = data_patern + junk_str + ""


# junk_data + pat1 + pat2 + (pat1, pat2, junk_data)*n + pat2(n chars modified) + pat1(n chars modified)
# pat1 + junk + (pat1+junk)*n + pat1(n chars modified) + (pat1 +junk)*n + pat1(n +/- m chars modified)
# pat1 + junk + (pat1+junk)*n + pat1(n chars modified) + (pat1 +junk)*n + pat1(n chars modified)
# pat1 + junk + pat1 + pat1(mod) + junk + pat1(mod m chars) + junk + pat1(mod m +/- n chars) + junk + pat1(mod m +/- n chars) ...

# pat1 + (pat1)*n + pat2 + pat1
def test_overlapping_pattern2(pattern_size):
    pattern1 = generate_pattern(pattern_size)
    pattern2 = generate_pattern(pattern_size)
    data_list = [pattern1, pattern2, pattern1 * 7]
    pass


# pat1 + junk_data + (pat1)*n + (modified_pat1)*n
def test_overlapping_pattern3(self):
    pass


#

def test_overlapping_pattern(self, pat_len, distance, size, name):
    pass


def multiple_pattern_file(self, pattern_size_freq_dict, size, name):
    total_patern_size = 0
    data_list = []
    for p in pattern_size_freq_dict:
        if size - total_patern_size:
            total_patern_size += (pattern_size_freq_dict[p] * p)
            data_list += [''.join(generate_pattern(p))] * pattern_size_freq_dict[p]
        else:
            break

    data_list += [''.join(generate_pattern(x)) for x in junk_list(size - total_patern_size)]
    random.shuffle(data_list)
    data_str = ''.join(data_list)
    with open(name, 'wb') as f_wirter:
        f_wirter.write(data_str)


# pat1 + junk + pat1 + pat1(mod) + junk + pat1(mod m chars) + junk + pat1(mod m +/- n chars) + junk + pat1(mod m +/- n chars) ...
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


