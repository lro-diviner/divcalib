#!/usr/bin/env python
from __future__ import division, print_function
from diviner import file_utils as fu
from diviner import calib
import pandas as pd
import sys
import glob
import os
from os.path import join as pjoin
import pprint
from multiprocessing import Pool

def main(input_tuple):

    # unpack the tuple
    l1afname, l1a_channel, rdr_channel, mode = input_tuple
    
    # create FileName handler object from given filename.
    fn = fu.FileName(l1afname)
    
    # only reason to use the pump currently is that it has the get_3_hour_block method
    pump = fu.L1ADataPump(fn.timestr)

    print("Loading L1A file",l1afname)
    df = pump.get_3_hour_block(l1afname)

    c = calib.Calibrator(df)
    c.calibrate()
    
    print("\nFinished calibrating.")
    
    # filter to middle hour of 3h interval
    tbout = c.Tb.ix[c.Tb.index.hour == int(fn.hour)]
    radout = c.abs_radiance.ix[c.abs_radiance.index.hour == int(fn.hour)]
    
    # filter out for channel of interest
    tbout = tbout.filter(regex=l1a_channel+'_')
    radout = radout.filter(regex=l1a_channel+'_')
    
    # rename detector names to rdr standard
    tbout.rename(columns=lambda x:int(x[3:]), inplace=True)
    radout.rename(columns=lambda x:int(x[3:]), inplace=True)
    
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
    radout['date'] = orig_dateutc.date
    radout['utc'] = orig_dateutc.utc
    
    tbmolten = pd.melt(tbout, id_vars=['date','utc'], value_vars=range(1,22))
    radmolten = pd.melt(radout, id_vars=['date','utc'], value_vars=range(1,22))
    
    # the melting process left funny columns names. repair.
    tbmolten.columns = ['date','utc','det','tb']
    radmolten.columns = ['date','utc','det','radiance']
    
    data_out = tbmolten.merge(rdrout, on=['date','utc','det'])
    data_out = radmolten.merge(data_out, on=['date','utc','det'])
    
    print("Merged successfully. Writing out to csv now.")
    # create filename
    basename = fn.timestr + '_C' + str(rdr_channel) + '_' + str(mode) + '_RDR20.csv'
    outfname = pjoin('/u/paige/maye/raid/rdr20_samples', basename)

    # don't write out the meaningless integer index
    data_out.to_csv(outfname, index=False)
               

def usage():
    print("\nUsage: {0} timestr L1A_channel mode cpus\n".format(sys.argv[0]),
"""\nWhen using 'test' as second parameter, a list of found filenames using the timestr
of parameter 1 will be printed out.""")
    sys.exit()
    
         
if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    timestr = sys.argv[1]
    l1a_channel = sys.argv[2]
    fnames = glob.glob(os.path.join(fu.l1adatapath, timestr + '*_L1A.TAB'))
    fnames.sort()
    if sys.argv[2] == 'test':
        pprint.pprint(fnames)
        sys.exit()

    mode = sys.argv[3]
    cpus = sys.argv[4]

    rdr_channel = calib.Calibrator.mcs_div_mapping[l1a_channel]
    
    # create input tuple to have pool.map only 1 parameter to provide
    list_of_input_tuples = [(i, l1a_channel, rdr_channel, mode) for i in fnames]

    pool = Pool(int(cpus))
    pool.map(main, list_of_input_tuples)
    
    