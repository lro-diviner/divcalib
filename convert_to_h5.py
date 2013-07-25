#!/usr/bin/env python
# encoding: UTF-8
from __future__ import division, print_function
import pandas as pd
import glob
from diviner.divtweet import tweet_machine # imports api handle

fnames = glob.glob('/u/paige/maye/raid/rdr20_month_samples/nominal/*_C9_*.csv')
store = pd.HDFStore('/u/paige/maye/raid/rdr20_month_samples/nominal/C9.h5')

todo = fnames
for i,fname in enumerate(todo):
    print(100*i/len(todo))
    if i % 50 == 0:
        tweet_machine('Converting to h5, {0:g} % done.'.format(100*i/len(todo)))
    df = pd.io.parsers.read_csv(fname)
    if len(df) == 0: continue
    store.append('df',df,data_columns=['clat','clon','cloctime'])
store.close()

