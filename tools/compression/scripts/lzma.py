from lib.data_generator import *
# lzma packets types
# SHORTREP len=1 distance=last[0]
# 1 char repeating multiple times file size_limit=256+ char repeat count
# n chars repeating multiple times file size_limit=256+ char repeat count
# char1 rep after char2 eg: abcdefghacai i.e distance swings between 0th and 1st loc
# char1 rep after char2 eg: abcdefghacai i.e distance swings between 0th and 2st loc
# char1 rep after char2 eg: abcdefghacai i.e distance swings between 0th and 3st loc
# char1 rep after char2(len>1) eg: abcdefghacai i.e distance swings between 0th and 1st loc
# char1 rep after char2(len>1) eg: abcdefghacai i.e distance swings between 0th and 2nd loc
# char1 rep after char2(len>1) eg: abcdefghacai i.e distance swings between 0th and 3rd loc
# char rep after distance is removed from array
# char rep with distance range(3to256KB)

# MATCH len=2to273 distnce=256KB
# n len char dist not present last[]
# n len char dist popped out of last[]

# LONGREP
# Repetition of all scenarios for SHORTREP with char pattern len range()
# .

create_pattern_distance_file(size=1024, pattern="a", name="/tmp/a.txt")
'''
p = convert_to_binary(open('/tmp/a.txt.lzma-hdr', 'rb').read())
x = len(p)
bin_str = [p[i: i+8] for i in xrange(0, x, 8)]
for i in bin_str:
    i_int = int(i, 2)
    print i, hex(i_int), unichr(i_int)
'''
