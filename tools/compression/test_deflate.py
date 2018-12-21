from lib.data_generator import *
from lib.utils import *
from lib.compress import *

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


def generate_length_offset_data(in_file, length, offset):
    bytes = test_pattern_len(length, offset)
    fwrite_raw_bytes(in_file, bytes)


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


if __name__ == "__main__":

    """
    print "#### Non repeated within window length (default for deflate 32KB) ####"
    seq_len = 32 * 1024  # 32KB random sequence
    repeat = 2
    orig_data = gen_repeated_seq(seq_len, repeat)

    compare_results(orig_data)

    print "#### Repeated once within window length ####"
    seq_len = 16 * 1024
    repeat = 2

    orig_data = gen_repeated_seq(seq_len, repeat)

    compare_results(orig_data)

    print "#### Overlapping sequence ####"
    seq_len = 4
    repeat = 4
    orig_data = gen_repeated_seq(seq_len, repeat) + os.urandom(4)  # Adding a 4 byte random string at the end

    compare_results(orig_data)

    print "#### Sequence with incremental repeats ####"
    seq = ""
    repeat = 16
    for i in range(1, repeat):
        seq = seq + seq + os.urandom(1)
    #print seq
    compare_results(seq)

    #### Generate test data ####
    """
    # Input file path
    filepath = '/Users/radhika/Documents/test-scripts/cntbry-crps-tst/artificial'
    report_file = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/results.csv"
    report = open(report_file, "w+")
    input_files = []
    """
    # Literals 0 - 143
    filename = filepath + '/uniq-143-literals.input'
    generate_literals(0, 143, filename)
    input_files.append(filename)

    # Literals 144 - 255
    filename = filepath + '/uniq-255-literals.input'
    generate_literals(144, 255, filename)
    input_files.append(filename)

    # Literals 0-143 repeated once
    filename = filepath + '/repeat-143-literals.input'
    generate_literals(0, 143, filename, repeat=2)
    input_files.append(filename)

    # Literals 144-255 repeated once
    filename = filepath + '/repeat-255-literals.input'
    generate_literals(144, 255, filename, repeat=2)
    input_files.append(filename)

    # Repeat length < 3
    filename = filepath + '/repeat-length-lt-2.input'
    bytes = test_pattern_len(2, 16 * 1024)   # Taking offset as 1024 for now
    fwrite_raw_bytes(filename, bytes)
    input_files.append(filename)

    # Repeat 3 >= length <= 258

    length_list = [3, 11, 19, 35, 67, 131, 258, 259]
    offset_list = [1, 5, 9, 17, 33, 65, 129, 257, 513, 1025, 2049, 4097, 8193, 16385, 32768, 32769]
    for length in length_list:
        for offset in offset_list:
            filename = generate_filename(filepath, length, offset)
            generate_length_offset_data(filename, length, offset)
            input_files.append(filename)

    # Misc input data
    #### Overlapping sequence ####
    """
    filename = filepath + '/overlapping-sequence-2.in'
    seq_len = 8
    repeat = 32
    orig_data = gen_repeated_seq(seq_len, repeat) + os.urandom(4)  # Adding a 4 byte random string at the end
    fwrite_raw_bytes(filename, orig_data)
    input_files.append(filename)

    #### Sequence with incremental repeats ####
    filename = filepath + '/incremental-repeats-2.in'
    seq = ""
    repeat = 8
    for i in range(1, repeat):
        seq = seq + seq + os.urandom(1)
    fwrite_raw_bytes(filename, seq)
    input_files.append(filename)
    """
    print "#### Test with deflate\n"
    for in_file in input_files:
        result = test_f1_compress(in_file, compress_type='f1_deflate')
        print "%s,%s\n" % (in_file, result)
        # report.write("%s,%s\n" % (in_file, result))

    print "#### Test with gzip header\n"
    for in_file in input_files:
        result = test_f1_compress(in_file, compress_type='f1_gzip_hdr')
        print "%s,%s\n" % (in_file, result)
        # report.write("%s,%s\n" % (in_file, result))

    print "#### Test with gzip\n"
    for in_file in input_files:
        result = test_f1_compress(in_file, compress_type='gzip')
        print "%s,%s\n" % (in_file, result)
        # report.write("%s,%s\n" % (in_file, result))

    print "#### Test with 7z\n"
    for in_file in input_files:
        result = test_f1_compress(in_file, compress_type='7z')
        print "%s,%s\n" % (in_file, result)
        # report.write("%s,%s\n" % (in_file, result))

    report.close()
    """