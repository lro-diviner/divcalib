#!/usr/local/epd/bin/python
import sys
from collections import OrderedDict
import numpy as np
import pandas
from os.path import splitext

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
    
def main(f):
    "f has to expose the file methods readline and seek"
    d = parse_des_header(f)
    dataset_name = splitext(f.name)[0]
    # each colum is piped as a double, so 8 chars.
    ncols = len(d.keys())

    rec_dtype = np.dtype([(key,'f8') for key in d.keys()])
    print(rec_dtype)
    print('\nStarting the read.')
    data = np.fromfile(f, dtype = rec_dtype)
    print data.shape
    df = pandas.DataFrame(data)
    store = pandas.HDFStore(dataset_name + '.h5','w')
    store[dataset_name] = df
    store.close()

if __name__ == '__main__':
    with open(sys.argv[1]) as f:
        main(f)
