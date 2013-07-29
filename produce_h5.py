#!/usr/bin/env python
from __future__ import division, print_function
from diviner import file_utils as fu
import pandas as pd
import glob
import sys
from os.path import join as pjoin
import pprint
from multiprocessing import Pool
from diviner.divtweet import tweet_machine

rdr_datapath = '/u/paige/maye/raid/rdr_data'
hdf_path = '/u/paige/maye/raid/hdf_rdr'

def process_fname(fname):    
    print("Processing",fname)
    rdr = fu.RDRReader(fname)
    df = rdr.read_df()

    fn = fu.FileName(fname)
    fn.rest = '_RDR.TAB.h5'
    fn.dirname = hdf_path

    store = pd.HDFStore(fn.fname)
    store.append('df', df, data_columns=['clat','clon'])
    store.close()
    

def store_channel_csv_to_h5(args):
    mode, ch = args
    root = '/u/paige/maye/raid/rdr20_month_samples/'
    dirname = pjoin(root,mode)
    searchpath = pjoin(dirname, '*_C'+str(ch)+'_*.csv')
    fnames = glob.glob(searchpath)
    if not fnames:
        print("No files found.")
        return
    storepath = pjoin(dirname, 'C'+str(ch)+'.h5')
    store = pd.HDFStore(storepath)
    for i,fname in enumerate(fnames):
        print(100*i/len(fnames))
        if i % 50 == 0:
            tweet_machine("C{0} conversion to HDF, {1:g}"
                          " % done.".format(ch, 100*i/len(fnames)))
        df = pd.io.parsers.read_csv(fname)
        if len(df) == 0: continue
        store.append('df', df, data_columns=['clat','clon','cloctime'])
    store.close()
    print("C{0} done.".format(ch))


if __name__ == '__main__':
    # timestr = sys.argv[1]
    # 
    # fnames = glob.glob(pjoin(rdr_datapath,timestr+'*TAB.zip'))
    # 
    # pprint.pprint(fnames)
    
    mode = sys.argv[1]
    pool = Pool(4)
    args = [(mode, i) for i in range(3,9)]
    pool.map(store_channel_csv_to_h5, args)