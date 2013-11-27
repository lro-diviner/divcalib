#!/usr/bin/env python
from __future__ import division, print_function
import matplotlib.pyplot as plt
import glob
import os
from os.path import join as pjoin
import sys
from diviner import file_utils as fu
import pandas as pd

basedir = pjoin(fu.outpath, 'metadata')


def resampler(year):
    fnames = glob.glob(pjoin(basedir, year + '??.h5'))
    fnames.sort()
    l = []
    for fname in fnames:
        print("Reading {0}".format(fname))
        basename = os.path.basename(fname)
        store_key = os.path.splitext(basename)[0]
        store = pd.HDFStore(fname)
        l.append(store.select('df').resample('1d', kind='period'))
        store.close()

    df = pd.concat(l)
    store_fname = pjoin(basedir, str(year) + '_daily_means.h5')
    df.to_hdf(store_fname, 'df')


def get_all_df(colname):
    years = range(2009, 2014)
    l = []
    for year in years:
        store = pd.HDFStore(pjoin(basedir, str(year) + '_daily_means.h5'))
        l.append(store['df'])
        store.close()
    return pd.concat(l)

    
if __name__ == '__main__':
    try:
        year = sys.argv[1]
    except IndexError:
        print('Usage: {0} year(yyyy)'.format(sys.argv[0]))
        sys.exit()

    resampler(year)
