#!/usr/bin/env python
from __future__ import print_function, division
from diviner import file_utils as fu
import sys
import pandas as pd
import os
from diviner import divtweet

savedir = os.path.join(fu.outpath,'metadata')
if not os.path.exists(savedir):
    os.makedirs(savedir)

def collect_data(pump):

    frames = []
    metadatacols = list(set(pump.keys) - set(fu.L1AHeader.datacols))
    for fname in pump.fnames:
        df = pump.process_one_file(fname)
        frames.append(df[metadatacols])
    print("Concatting...")
    df = pd.concat(frames)
    return df

def produce_store_file(timestr):
    pump = fu.Div247DataPump(timestr)
    print("Found {0} files.".format(len(pump.fnames)))

    if len(pump.fnames) == 0:
        return

    store = pd.HDFStore(os.path.join(savedir, timestr+'.h5'),'w')
    df = collect_data(pump)
    
    print("Polishing...")
    final = pump.clean_final_df(df)
    print("Writing to store...")
    store.append('df', final)
    store.close()
    print("Done.")
    

if __name__ == '__main__':
# try:
#     timestr = sys.argv[1]
# except IndexError:
#     print("Usage: {0} timestr".format(sys.argv[0]))
#     sys.exit()

    year = '2010'
    months = range(1,13)
    for month in months:
        timestr = year + str(month).zfill(2)
        divtweet.tweet_machine("Producing metadata for {0}".format(timestr))
        print("Producing", timestr)
        produce_store_file(timestr)
    
