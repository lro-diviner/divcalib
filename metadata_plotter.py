#!/usr/bin/env python
from __future__ import division, print_function
import matplotlib.pyplot as plt
import glob
import os
from os.path import join as pjoin
import sys
from diviner import file_utils as fu
import pandas as pd


def resampler(year):
    basedir = pjoin(fu.outpath, 'metadata')

    fnames = glob.glob(pjoin(basedir, year+'??.h5'))
    fnames.sort()
    for fname in fnames:
        print("Reading {0}".format(fname))
        basename = os.path.basename(fname)
        store_key = os.path.splitext(basename)[0]
        store_fname = pjoin(basedir, str(year) + '.h5')
        store = pd.HDFStore(fname)
        store.select('df').resample('1d', kind='period').to_hdf(store_fname, store_key)
        store.close()
        
    
if __name__ == '__main__':
    try:
        year = sys.argv[1]
    except IndexError:
        print('Usage: {0} year(yyyy)'.format(sys.argv[0]))
        sys.exit()
        
    resampler(year)