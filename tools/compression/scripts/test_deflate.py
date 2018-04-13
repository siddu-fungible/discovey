from lib.test_compression import TestCompression
from lib.data_generator import *
import os
import threading


def test_single_pattern(size, log_file):
    artifact_list = []
    comp = TestCompression(log_file)
    for i in xrange(255):
        file_name = "/tmp/{0}_{1}".format(i, size)
        deflated_file = file_name + ".deflate"
        inflated_file = file_name + "_inflate"
        create_pattern_distance_file(pattern=str(bytearray([i])), size=size, name=file_name)
        artifact_list.append(file_name)
        artifact_list.append(deflated_file)
        artifact_list.append(inflated_file)
        comp.log("Created File: {}".format(file_name))
        comp.execute_command(comp.compressor_binary, "-e", file_name)

        comp.execute_command(comp.compressor_binary, "-e", "-d", deflated_file, inflated_file)
        resp = comp.compare_files(file1=file_name,
                                  file2=inflated_file)
        assert resp, "Compressed and decompressed file matched"
        comp.log("Compressed and decompressed file matched")
        comp.log("Original file size: {0}\nCompressed File_size: {1}\nUncompressed File Size: {2}".format(
            comp.size_of_file(file_name), comp.size_of_file(deflated_file), comp.size_of_file(inflated_file)))
        comp.log("\n")

    cleanup(artifact_list)


def test_pattern_len(size, log_file):
    artifact_list = []
    comp = TestCompression(log_file)
    for i in xrange(3, 256):
        file_name = "/tmp/{0}_{1}".format(i, size)
        deflated_file = file_name + ".deflate"
        inflated_file = file_name + "_inflate"
        data_pattern = ''.join(generate_pattern(i))
        create_pattern_distance_file(pattern=data_pattern, size=size, name=file_name)
        artifact_list.append(file_name)
        artifact_list.append(deflated_file)
        artifact_list.append(inflated_file)
        comp.log("Created File: {0} with pattern: {1}".format(file_name, data_pattern.__repr__()))
        comp.execute_command(comp.compressor_binary, "-e", file_name)

        comp.execute_command(comp.compressor_binary, "-e", "-d", deflated_file, inflated_file)
        resp = comp.compare_files(file1=file_name,
                                  file2=inflated_file)
        assert resp, "Compressed and decompressed file matched"
        comp.log("Original  and decompressed file matched")
        comp.log("Original file size: {0}\nCompressed File_size: {1}\nUncompressed File Size: {2}".format(
            comp.size_of_file(file_name), comp.size_of_file(deflated_file), comp.size_of_file(inflated_file)))
        comp.log("\n")
    cleanup(artifact_list)


def cleanup(artifact_list):
    for a in artifact_list:
        try:
            os.remove(a)
            print "File Deleted: {}".format(a)
        except IOError:
            print Exception.message


def test_distance(size, log_file, pattern_len):
    artifact_list = []
    comp = TestCompression(log_file)
    pattern = ''.join(generate_pattern(pattern_len))

    distance_range = range(2, (size-pattern_len))
    for i in distance_range:
        file_name = "/tmp/{0}_{1}_pat_{2}".format(i, size, pattern_len)
        deflated_file = file_name + ".deflate"
        inflated_file = file_name + "_inflate"
        create_pattern_distance_file(pattern=pattern, size=size, name=file_name, distance=i)
        artifact_list.append(file_name)
        artifact_list.append(deflated_file)
        artifact_list.append(inflated_file)
        comp.log("Created File: {0}".format(file_name))
        comp.execute_command(comp.compressor_binary, "-e", file_name)

        comp.execute_command(comp.compressor_binary, "-e", "-d", deflated_file, inflated_file)
        resp = comp.compare_files(file1=file_name,
                                  file2=inflated_file)
        assert resp, "Compressed and decompressed file matched"
        comp.log("Compressed and decompressed file matched")
        comp.log("Original file size: {0}\nCompressed File_size: {1}\nUncompressed File Size: {2}".format(
            comp.size_of_file(file_name), comp.size_of_file(deflated_file), comp.size_of_file(inflated_file)))
        comp.log("Compression ratio: {}".format(float(comp.size_of_file(file_name)) / comp.size_of_file(deflated_file)))
        comp.log("\n")
    cleanup(artifact_list)


def test_deflate_all_chars(arg=0):
    thread_list = []
    test_method = ""
    if arg == 0:
        test_method = test_single_pattern
    elif arg == 1:
        test_method = test_pattern_len
    elif arg == 2:
        test_method = test_distance
    file_size = []
    for i in file_size:
        t = threading.Thread(target=test_method, args=(i, "deflate_{0}_{1}_pattern".format(i, test_method.__name__)))
        t.daemon = True
        t.start()
        thread_list.append(t)

    for i in thread_list:
        i.join()


def test_pattern_distance1():
    str = "a"*260 + "back" + "a" + "back"
    with open('/tmp/a1.txt', 'wb') as f:
        f.write(str)


def test_pattern_distance2():
    str = "a"*4 + "b" + "a" + "cked"
    with open('/tmp/a2.txt', 'wb') as f:
        f.write(str)


def test_overlapping_pattern1():
    pat = generate_garbage_data(100)
    str = "{0}{1}{0}{2}{0}".format(pat, "apple", generate_garbage_data(152))
    with open('/tmp/a12.txt', 'wb') as f:
        f.write(str)


if __name__ == "__main__":
    test_overlapping_pattern1()
