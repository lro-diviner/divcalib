#!/usr/bin/env python
# encoding: UTF-8

import pandas as pd
import glob

fnames = glob.glob('/u/paige/maye/raid/rdr20_month_samples/nominal/*_C9_*.csv')
store = pd.HDFStore('/u/paige/maye/raid/rdr20_month_samples/nominal/C9.h5')

todo = fnames
for i, fname in enumerate(todo):
    print(100*i/len(todo))
    df = pd.io.parsers.read_csv(fname)
    if len(df) == 0:
        continue
    store.append('df', df, data_columns=['clat', 'clon', 'cloctime'])
store.close()
