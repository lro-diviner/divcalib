#!/usr/local/epd/bin/python
import matplotlib
matplotlib.use('Agg')
import sys
from collections import OrderedDict
import struct
import time
import pandas
import matplotlib.pyplot as plt
import numpy as np

def rebin(a, newlength):
    sh = newlength,a.shape[0]//newlength,1,a.shape[1]
    return a.reshape(sh).mean(-1).mean(1)

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
    return d,l    
        
if __name__ == '__main__':
    d,l = main()
    pdata = pandas.DataFrame(l)
    ndata = pdata[0].values
    limit = 100000
    # if ndata.size > limit:
    #     ndata.shape=(ndata.size,1)
    #     print(ndata.shape)
    #     no_of_divides = int(round(np.log2(ndata.size/100000.0)))
    #     dsampled = rebin(ndata, ndata.size/no_of_divides)
    # else:
    #     dsampled = ndata
    plt.plot(dsampled,'r,')
    plt.grid(True)
    plt.savefig('foo_mpl.png')