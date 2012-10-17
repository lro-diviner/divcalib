import sys
from collections import OrderedDict
import struct
from itertools import izip_longest

def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(fillvalue=fillvalue, *args)
    
def get_token(s):
    s = s.strip().strip("'").strip().strip("'").strip()
    return s

d = OrderedDict()

for i,line in enumerate(sys.stdin):
    # print len(line),repr(line)
    noOfChars = len(line)
    # short descriptors have 54 chars
    if noOfChars == 54:
        tmp = get_token(line)
    # long descriptor names have 134 chars
    elif noOfChars ==  134:
        longdes = get_token(line)
        d[tmp] = longdes
    # the 'end' line has 15 but the very last 'line' is the data,
    # so if we assign anything not 54 or 134 to data, at the end
    # that's correct.
    else:
        data = line
    
print("{0} lines of descriptor read.".format(i-1))
print d
print repr(data)

n = len(d.keys())
n *= 8 # for having 2 bytes = 16 bit for each item
data = [data[i:i+n] for i in range(0, len(data), n)]
for line in data:
    print struct.unpack('dddd',line)