# -*- coding: utf-8 -*-
import pandas as pd
from diviner import data_prep
from diviner import file_utils
from scipy.ndimage import label
import glob
import gc
from multiprocessing import Pool
import os
import time

root = '/raid1/maye/rdr_out/metadata'
fnames = glob.glob(root+"/20????.h5")
fnames.sort()
colname = 'last_el_cmd'

def do_work(fname):
    print fname
    root = os.path.dirname(fname)
    base = os.path.basename(fname)
    base = os.path.splitext(base)[0]
    df = pd.read_hdf(fname, 'df', columns=[colname])
    df['mybool'] = df[colname] == 90
    df['label'] = label(df.mybool)[0]
    df['time'] = df.index
    g = df.groupby('label')['time']
    subdf = pd.DataFrame({'start':g.first(),
                          'duration':g.last() - g.first()})
    if len(subdf) > 0:
        newfname = os.path.join(root, 'analysis', base + '_test_' + colname + '.h5')
        subdf[1:].to_hdf(newfname,
                         'df',
                         mode='a',
                         format='table',
                         append=True)


p = Pool(3)

t1 = time.time()
p.map(do_work, fnames[:3])
print time.time() - t1