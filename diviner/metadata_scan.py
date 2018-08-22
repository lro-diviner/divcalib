# -*- coding: utf-8 -*-
import pandas as pd
from diviner import data_prep
from diviner import file_utils
from scipy.ndimage import label
import glob
import gc

root = '/raid1/maye/rdr_out/metadata'
fnames = glob.glob(root+"/20????.h5")
fnames.sort()
colname = 'last_el_cmd'

for i, fname in enumerate(fnames):
    if i % 4 == 0:
        gc.collect()
        print(gc.collect())
    print(fname)
    df = pd.read_hdf(fname, 'df', columns=[colname])
    df['mybool'] = df[colname] == 90
    df['label'] = label(df.mybool)[0]
    df['time'] = df.index
    g = df.groupby('label')['time']
    pd.DataFrame({'start': g.first(),
                  'duration': g.last() - g.first()})[1:].to_hdf('./test_scans.h5',
                                                                'df',
                                                                mode='a',
                                                                format='table',
                                                                append=True)
