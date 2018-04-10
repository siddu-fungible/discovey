from lib.data_generator import *


"""
a   b   c   d   e   a   b   c
------------------------------
              |     ^        
  "Sliding window"  |
                    |
                "'a' should match"
                    
"""
def duplicate_pattern_in_window(size, file_size=32):
    random_uniq_str = generate_random_literals(file_size)

    substr = random_uniq_str[:int(size * 1024)]
    rest_data = random_uniq_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    dup_patterns_in_window = substr[:-258] + repeated_bytes + rest_data

    return dup_patterns_in_window


"""
a   b   c   d   e   a   b   c
------------------  ^
        |           |
"Sliding window" "Should match 'a' in window"  
"""
def duplicate_pattern_at_window_edge(size, file_size=32):
    random_uniq_str = generate_random_literals(file_size)

    substr = random_uniq_str[:int(size * 1024)]
    rest_data = random_uniq_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    dup_patterns_in_window = substr + repeated_bytes + rest_data

    return dup_patterns_in_window


"""
a   b   c   d   e   #   a   b   c
    ------------------  ^
            |           |
    "Sliding window" "Should not match any char in window"  
"""
def duplicate_pattern_outside_window(size, file_size=32):
    random_uniq_str = generate_random_literals(file_size)

    substr = random_uniq_str[:int(size * 1024)]
    rest_data = random_uniq_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    dup_patterns_in_window = substr + os.urandom(1) + repeated_bytes + rest_data

    return dup_patterns_in_window


"""
a   b   c   d   e   a   b   c   d
-------------------------
            |
"Sliding window"    --------------
                            |
                    "Duplicate spanning window

"""
def duplicate_spanning_window(size, file_size=32):
    random_uniq_str = generate_random_literals(file_size)

    substr = random_uniq_str[:size * 1024]
    rest_data = random_uniq_str[size * 1024:]
    repeated_bytes = substr[:259]
    dup_patterns_in_window = substr[:-(len(repeated_bytes) / 2)] + repeated_bytes + rest_data

    return dup_patterns_in_window


def largest_uncompressed_win_size(size, file_size=32):
    random_uniq_str = generate_random_literals(size)
    repeat = file_size / size
    dup_patterns_in_window = random_uniq_str * repeat

    return dup_patterns_in_window


if __name__ == "__main__":


    """
    # Generate a 32K unique stream
    filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/randoms-32k.in"
    with open(filename, "w+") as infile:
        random_uniq_str = generate_random_literals(32)
        infile.write(random_uniq_str)
    """

    ## For duplicate pattern spanning window
    size = 128
    file_size = size * 2
    dup_patterns = duplicate_spanning_window(size, file_size=file_size)
    filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/split-patn-in-hist-%sk-fsize-%sk.in" % \
               (str(size), str(file_size))
    with open(filename, "w+") as infile:
        infile.write(dup_patterns)

    ## For duplicate patterns within the window
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_in_window(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-%sk.in" % \
                   str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)

    ## For duplicate patterns just at window edge
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_at_window_edge(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-at-win-edge-%sk.in" % \
                   str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)

    ## For duplicate patterns outside the sliding window
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_outside_window(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-out-win-%sk.in" % \
                   str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)

    ## Largest uncompressed size for each history size
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 16
        dup_patterns = largest_uncompressed_win_size(size, file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/largest-uncompressed-win-%sk.in" % \
                   str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
