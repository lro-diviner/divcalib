#!/usr/bin/env python
from __future__ import division, print_function
from diviner import file_utils as fu
from diviner import calib
import pandas as pd
import sys
import glob
import os
import pprint

def main(l1afname, l1a_channel, rdr_channel):

    fn = fu.FileName(l1afname)
    pump = fu.L1ADataPump(fn.timestr)

    print("Loading L1A file",l1afname)
    df = pump.get_3_hour_block(l1afname)

    c = calib.Calibrator(df)
    c.calibrate()
    
    print("\nFinished calibrating.")
    
    # filter to middle hour of 3h interval
    tbout = c.Tb.ix[c.Tb.index.hour == int(fn.hour)]

    # filter out for channel of interest
    tbout = tbout.filter(regex=l1a_channel+'_')

    # rename detector names to rdr standard
    tbout.rename(columns=lambda x:int(x[3:]), inplace=True)

    print("Reading old RDR now.")
    rdr = fu.RDRReader.from_timestr(fn.timestr)
    # don't parse times for speed reasons
    rdrdf = rdr.read_df(do_parse_times=False)
    print("Done.")
    
    rdrch = rdrdf[rdrdf.c == rdr_channel]

    rdrout = rdrch[['date','utc','clat','clon','det']]

    # get the original date and utc columns for simplicity
    # (could also create them from index)
    orig_dateutc = df[['date','utc']].ix[df.index.hour == int(fn.hour)]

    # reindex to reduced dataset of Tb (only calibratable data points survived)
    orig_dateutc = orig_dateutc.reindex(index=tbout.index)

    tbout['date'] = orig_dateutc.date
    tbout['utc'] = orig_dateutc.utc

    tbmolten = pd.melt(tbout, id_vars=['date','utc'], value_vars=range(1,22))

    # the melting process left funny columns names. repair.
    tbmolten.columns = ['date','utc','det','tb']

    data_out = tbmolten.merge(rdrout, on=['date','utc','det'])

    print("Merged successfully. Writing out to csv now.")
    # don't write out the meaningless integer index
    data_out.to_csv('/u/paige/maye/raid/rdr20_samples/'+fn.timestr+'_rdr20.csv',
                    index=False)
                    
if __name__ == '__main__':
    timestr = sys.argv[1]
    l1a_channel = sys.argv[2]
    rdr_channel = calib.Calibrator.mcs_div_mapping[l1a_channel]
    
    fnames = glob.glob(os.path.join(fu.l1adatapath, timestr + '*_L1A.TAB'))
    fnames.sort()
    for fname in fnames[5:]:
        main(fname, l1a_channel, rdr_channel)
