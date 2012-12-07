#!/usr/local/epd/bin/python
import sys
from collections import OrderedDict
import numpy as np
import pandas
import os
from os.path import splitext,basename,join
import time

def split_by_n(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]

def get_token(s):
    s = s.strip().strip("'").strip().strip("'").strip()
    return s

def parse_des_header(f):
    "Parse the descriptor header and return dictionary with the found items."
    d = OrderedDict()
    while True:
        line = f.readline()
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
    return d
    
def des2npy(fname):
    with open(fname) as f:
        d = parse_des_header(f)
        # f.name is the way to get to the filename of a file handle
        # splitext creates tuple with everything until extension and .extension
        dataset_name = splitext(basename(fname))[0]
    
        # each colum is piped as a double, so 8 chars.
        ncols = len(d.keys())

        rec_dtype = np.dtype([(key,'f8') for key in d.keys()])
        print('\nStarting the read of {0}'.format(fname))
        t1 = time.time()
        data = np.fromfile(f, dtype = rec_dtype)
    return data

def des2df(fname):
    data = des2npy(fname)
    return pandas.DataFrame(data)
    
def des2hdf(fname,cleanup=False):
    "f has to expose the file methods readline and seek"
    data = des2npy(fname)
    if cleanup:
        os.remove(fname)
    print data.shape
    df = pandas.DataFrame(data)
    newfname = join('/luna1/maye',dataset_name+'.h5')
    print 'New filename:',newfname
    store = pandas.HDFStore(newfname,'w')#,complevel=1,complib='zlib')
    store[dataset_name] = df
    store.close()

def time_reading(f):
    t1 = time.time()
    store = pandas.HDFStore(f,'r')
    dataset_name = splitext(basename(f))[0].split('_')[0]
    df = store[dataset_name]
    print("Reading time: {0}".format(time.time()-t1))
    store.close()
    
if __name__ == '__main__':
        des2hdf(sys.argv[1])