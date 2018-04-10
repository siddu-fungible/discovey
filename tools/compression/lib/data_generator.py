import random
from base64 import b64encode
import os
from string import printable


def generate_pattern(size):
    use_char = []
    printable_char = list(printable)
    remove_list = ['\t', '\f', '\r', '\n']
    for r in remove_list:
        if r in printable_char:
            printable_char.remove(r)

    printable_len = len(printable_char)
    factor = size / printable_len
    if factor:
        for i in xrange(factor + 1):
            random.shuffle(printable_char)
            use_char += printable_char
        use_char = use_char[:size]
    else:
        use_char = random.sample(printable, size)
        random.shuffle(use_char)
    return use_char


def junk_list(len):
    lst = []
    temp = len
    while len:
        len = len/2
        if len:
            lst.append(len)
    var = temp - sum(lst)
    if var:
        lst.append(var)
    return lst


def create_file(size, patern_len, file_name):
    bufer_size = 1024
    iterations = size/bufer_size

    patern = generate_pattern(size=patern_len)
    j_list = junk_list(bufer_size - patern_len)
    j_list.append('data_pos')
    f = open(file_name, 'wb')
    for i in xrange(iterations):
        random.shuffle(j_list)
        data = []
        for j in j_list:
            if isinstance(j, str):
                data.append(''.join(patern))
            else:
                data.append(''.join(generate_pattern(j)))
        data.append('\n')
        data_str = ' '.join(data)
        f.write(data_str)
    f.close()


def create_large_file(size, pat_len, distance, name):
    iterations = size / (pat_len + distance)
    pad = size % (pat_len + distance)
    junk_items = junk_list(distance)
    fd = open(name, 'wb')
    for i in xrange(iterations):
        random.shuffle(junk_items)
        data = [''.join(generate_pattern(x)) for x in junk_items]
        data.append(''.join(generate_pattern(pat_len)))
        fd.write(' '.join(data))
    fd.write(''.join(generate_pattern(pad)))
    fd.close()


def create_hex_file(size, name):
    bufer_size = 1024
    iterations = size / bufer_size
    if not iterations:
        iterations = 1
        bufer_size = size
    hex_list = [hex(x) for x in range(bufer_size)]
    f_obj = open(name, 'w')
    for i in xrange(iterations):
        random.shuffle(hex_list)
        data = ''.join(hex_list)
        f_obj.write(data)
    f_obj.close()


def create_data_file(size, name, data):
    pass


def generate_unique_literals(start, end, randomize=False):
    lit_arr = []
    for i in range(start, end + 1):
        lit_arr.append(chr(i))

    if randomize:
        random.shuffle(lit_arr)

    uniq_literals = ''.join(lit_arr)
    return uniq_literals


def generate_random_literals(size):
    byte_arr = os.urandom(int(size * 1024))
    #return b64encode(byte_arr).decode('utf-8')
    return byte_arr


if __name__ == '__main__':
    with open("/tmp/datagen.test", "w+") as infile:
        infile.write(generate_random_literals(2048))
