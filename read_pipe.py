import sys
from collections import OrderedDict
import struct
import time

def split_by_n(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]

def get_token(s):
    s = s.strip().strip("'").strip().strip("'").strip()
    return s

def main():
    """docstring for main"""
    d = OrderedDict()

    while True:
        line = sys.stdin.readline()
        # print len(line),repr(line)
        noOfChars = len(line)
        # short descriptors have 54 chars
        if noOfChars == 54:
            tmp = get_token(line)
        # long descriptor names have 134 chars
        elif noOfChars ==  134:
            longdes = get_token(line)
            d[tmp] = longdes
        elif noOfChars == 15:
            break

    # each colum is piped as a double, so 8 chars.
    ncols = len(d.keys())
    n = 8 * ncols

    unpacker = struct.Struct(ncols*'d')

    l = []
    while True:
        data = sys.stdin.read(n)
        if not data: break
        l.append(unpacker.unpack(data))
        if (len(l) % 100000) == 0:
            print('100 k lines read.')
    print len(l), 'lines of data collected.'
        
        
if __name__ == '__main__':
    main()
