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
import numpy as np
from numpy.random import randn
import subprocess
import time

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
    dirname = fu.get_month_sample_path_from_mode(mode)
    searchpath = pjoin(dirname, '*_C'+str(ch)+'_*.csv')
    fnames = glob.glob(searchpath)
    if not fnames:
        print("No files found with searchpath\n",searchpath)
        return
    storepath = pjoin(dirname, 'C'+str(ch)+'.h5')
    store = pd.HDFStore(storepath,'w')
    for i,fname in enumerate(fnames):
        print(100*i/len(fnames))
        if i % 100 == 0:
            tweet_machine("C{0} conversion to HDF, {1:g}"
                          " % done.".format(ch, 100*i/len(fnames)))
        df = pd.io.parsers.read_csv(fname)
        if len(df) == 0: continue
        store.append('df', df, data_columns=['clat','clon','cloctime'], index=False)
    store.close()
    print("C{0} done.".format(ch))


def manage_store_channel():
    mode, chstart, chend = sys.argv[1:4]
    pool = Pool(4)
    args = [(mode, i) for i in range(int(chstart),int(chend)+1)]
    pool.map(store_channel_csv_to_h5, args)
        

def test_production_speeds(ncols=2):
    store = pd.HDFStore('test.h5','w')
    for i in range(2):
        df = pd.DataFrame(randn(1e6,ncols), columns=list('ABCDEFG')[:ncols])
        store.append('df',df, data_columns=['B'], index=False)# index=False)
    store.create_table_index('df', columns=['B'], kind='full')
    store.close()
    subprocess.call('ptrepack --chunkshape=auto --sortby=B -o test.h5 test_sorted.h5'.split())


def create_full_indexes(args):
    mode, chno = args
    dirname = fu.get_month_sample_path_from_mode(mode)
    path = pjoin(dirname, 'C'+str(chno)+'.h5')
    store = pd.HDFStore(path)
    store.create_table_index('df', columns=['clat'], kind='full')
    store.close()
    
    
def manage_create_full_indexes():
    mode, chstart, chend = sys.argv[1:4]
    pool = Pool(4)
    args = [(mode, i) for i in range(int(chstart), int(chend) + 1)]
    pool.map(create_full_indexes, args)
    
    
def ptrepack_all(args):
    mode, chno = args
    dirname = fu.get_month_sample_path_from_mode(mode)
    fname_root = pjoin(dirname, 'C'+str(chno))
    infile = fname_root + '.h5'
    outfile = fname_root + '_sorted.h5'
    cmd = ['ptrepack','--chunkshape=auto','--sortby=clat','--propindexes',
            infile, outfile]
    subprocess.call(cmd)
    
    
def manage_ptrepack():
    mode, chstart, chend = sys.argv[1:4]
    pool = Pool(4)
    args = [(mode, i) for i in range(int(chstart), int(chend) + 1)]
    pool.map(ptrepack_all, args)
    
    
if __name__ == '__main__':
    manage_ptrepack()
