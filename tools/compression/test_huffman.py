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
    random_str = generate_random_literals(file_size * 1024)

    substr = random_str[:int(size * 1024)]
    rest_data = random_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    pattern = substr[:-258] + repeated_bytes + rest_data

    return pattern


"""
a   b   c   d   e   a   b   c
------------------  ^
        |           |
"Sliding window" "Should match 'a' in window"  
"""
def duplicate_pattern_at_window_edge(size, file_size=32):
    random_str = generate_random_literals(file_size * 1024)

    substr = random_str[:int(size * 1024)]
    rest_data = random_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    pattern = substr + repeated_bytes + rest_data

    return pattern


"""
a   b   c   d   e   #   a   b   c
    ------------------  ^
            |           |
    "Sliding window" "Should not match any char in window"  
"""
def duplicate_pattern_outside_window(size, file_size=32):
    random_str = generate_random_literals(file_size * 1024)

    substr = random_str[:int(size * 1024)]
    rest_data = random_str[int(size * 1024):]
    repeated_bytes = substr[:259]
    pattern = substr + os.urandom(1) + repeated_bytes + rest_data

    return pattern


"""
a   b   c   d   e   a   b   c   d
-------------------------
            |
"Sliding window"    --------------
                            |
                    "Duplicate spanning window

"""
def duplicate_spanning_window(size, file_size=32):
    random_str = generate_random_literals(file_size * 1024)

    substr = random_str[:size * 1024]
    rest_data = random_str[size * 1024:]
    repeated_bytes = substr[:259]
    pattern = substr[:-(len(repeated_bytes) / 2)] + repeated_bytes + rest_data

    return pattern


def largest_uncompressed_win_size(size, file_size=32):
    repeat = ((size * 1024) / 258) + 1  # Window size passed in units of K
    random_str = []
    for n in range(0, repeat):
        random_str.append(generate_random_literals(258))
    pattern = ''.join(random_str) * (file_size / size)

    return pattern


def duplicate_len(length, window):
    random_str = generate_random_literals(window * 1024)
    substr = random_str[:-length]
    repeated_bytes = random_str[:length]
    pattern = substr + repeated_bytes

    return pattern


if __name__ == "__main__":


    """
    # Generate a 32K unique stream
    filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/randoms-32k.in"
    with open(filename, "w+") as infile:
        random_uniq_str = generate_random_literals(32)
        infile.write(random_uniq_str)
    """

    """
    ## For duplicate pattern spanning window
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_spanning_window(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-spanning-win/" \
                   "duplicate-span-win-%sk.in" % (str(size))
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
    
    ## For duplicate patterns within the window
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_in_window(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-inside-win/" \
                   "duplicate-%sk.in" % str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
    
    ## For duplicate patterns just at window edge
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_at_window_edge(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-at-win-edge/" \
                   "duplicate-at-win-edge-%sk.in" % str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)

    ## For duplicate patterns outside the sliding window
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 2
        dup_patterns = duplicate_pattern_outside_window(size, file_size=file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-out-win/" \
                   "duplicate-out-win-%sk.in" % str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
    """
    """
    ## Largest uncompressed size for each history size
    window_size = [4, 8, 16, 32, 64, 128, 256]
    for size in window_size:
        file_size = size * 16
        dup_patterns = largest_uncompressed_win_size(size, file_size)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/largest-uncompress-win/" \
                   "largest-uncompressed-win-%sk.in" % str(size)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
    """
    ## Duplicate patterns with different lengths
    start = 2
    end = 274
    window = 128     #Translates to window * 1024
    for length in range(2, end + 1):
        dup_patterns = duplicate_len(length, window)
        filename = "/Users/radhika/Documents/test-scripts/cntbry-crps-tst/cust-corpus/gen-data/duplicate-lens-lzma/" \
                   "duplicate-len-%s.in" % str(length)
        with open(filename, "w+") as infile:
            infile.write(dup_patterns)
