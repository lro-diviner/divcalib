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
    
def des2hdf(f, dataset_name):
    d = parse_des_header(f)
    
    rec_dtype = np.dtype([(key,'f8') for key in d.keys()])
    
    # read all from the point where parse_des_header has left off
    datastr = f.read()
    print('\nStarting the read of {0}'.format(dataset_name))
    t1 = time.time()
    data = np.fromstring(datastr, dtype = rec_dtype)
    print("Reading time: {0}".format(time.time()-t1))
    print data.shape
    df = pandas.DataFrame(data)
    newfname = join('/luna1/maye',dataset_name+'.h5')
    print 'New filename:',newfname
    store = pandas.HDFStore(newfname,'w')
    store[dataset_name] = df
    store.close()
    f.close()

def time_reading(f):
    t1 = time.time()
    store = pandas.HDFStore(f,'r')
    dataset_name = splitext(basename(f))[0].split('_')[0]
    df = store[dataset_name]
    print("Reading time: {0}".format(time.time()-t1))
    store.close()
    
if __name__ == '__main__':
        des2hdf(sys.argv[1])