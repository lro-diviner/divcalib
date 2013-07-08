#!/usr/bin/env python
from __future__ import division, print_function
from diviner import file_utils as fu
import pandas as pd
import glob
import sys
from os.path import join as pjoin
import pprint
from multiprocessing import Pool

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
    
    
if __name__ == '__main__':
    timestr = sys.argv[1]

    fnames = glob.glob(pjoin(rdr_datapath,timestr+'*TAB.zip'))

    pprint.pprint(fnames)
    
    pool = Pool(4)
    
    pool.map(process_fname, fnames)