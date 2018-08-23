#!/usr/bin/env python

from diviner import file_utils as fu
from diviner import calib
import pandas as pd
import sys
import glob
import os
from os.path import join as pjoin
import pprint
from multiprocessing import Pool
from diviner import mypool

# leave out visual channels for now
l1a_channels = calib.channels[2:]
rdr_channels = list(range(1,10))[2:]

def process_one_channel(args):
    # unpack argument tuple
    fn, l1a_channel, rdr_channel, tbout_all, radout_all, rdrdf, dfdate, dfutc = args

    print("Processing channel",rdr_channel)
    
    # filter out for channel of interest
    tbout = tbout_all.filter(regex=l1a_channel+'_')
    radout = radout_all.filter(regex=l1a_channel+'_')

    # rename detector names to rdr standard, and reverse detector numbering for
    # detectors of telescope B
    if l1a_channel.startswith('b'):
        tbout.columns = radout.columns = list(range(21,0,-1))
    else:
        tbout.rename(columns=lambda x:int(x[3:]), inplace=True)
        radout.rename(columns=lambda x:int(x[3:]), inplace=True)
  
    rdrch = rdrdf[rdrdf.c == rdr_channel]

    rdrout = rdrch[['date','utc','jdate','clat','clon','sclat','sclon','scrad',
                    'orientlat','orientlon',
                    'sunlat','sunlon','sundist','orbit','scalt','af','c','det','cemis','cloctime',
                    'qca','qge','qmi']]

    rdrout.columns = ['date','utc','jdate','clat','clon','sclat','sclon','scrad',
                    'vert_lat','vert_lon',
                    'sunlat','sunlon','sundst','orbit','scalt','af','c','det','cemis','cloctime',
                    'qca','qge','qmi']


    #fix the columns names so the orientlat orientlon will be the wrong name from
    # divdata: vert_lan and vert_lon
    # because the index of tbout is less than df, only the dates for tbout's index 
    # should be picked out of df
    tbout['date'] = dfdate
    tbout['utc'] = dfutc
    radout['date'] = dfdate
    radout['utc'] = dfutc

    tbmolten = pd.melt(tbout, id_vars=['date','utc'], value_vars=list(range(1,22)))
    radmolten = pd.melt(radout, id_vars=['date','utc'], value_vars=list(range(1,22)))

    # the melting process left funny columns names. repair.
    tbmolten.columns = ['date','utc','det','tb']
    radmolten.columns = ['date','utc','det','radiance']

    data_out = tbmolten.merge(rdrout, on=['date','utc','det'])
    data_out = radmolten.merge(data_out, on=['date','utc','det'])
    print("Merged successfully. Writing out to csv now.")

    # create filename
    basename = fn.timestr + '_C' + str(rdr_channel) + '_' + mode + '_RDR20.csv'
    dirname = fu.get_month_sample_path_from_mode(mode)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    outfname = pjoin(dirname, basename)

    # don't write out the meaningless integer index
    data_out.to_csv(outfname, index=False)
    print("Finished",os.path.basename(outfname))
    
def main(input_tuple):

    # unpack the tuple
    l1afname, mode = input_tuple
    
    
    # create FileName handler object from given filename.
    fn = fu.FileName(l1afname)
    
    # only reason to use the pump currently is that it has the get_3_hour_block method
    pump = fu.L1ADataPump(fn.timestr)

    print("Loading L1A file",l1afname)
    df = pump.get_3_hour_block(l1afname)

    # Determine what kind of calibration is requested
    rad_corr = True
    skipsamples = True
    calfitting_order=1
    new_rad_corr = True
    if mode == 'no_rad_corr':
        rad_corr = False
    if mode == 'rad_corr_old':
        new_rad_corr = False
    elif mode == 'no_skip':
        skipsamples = False
    elif mode.startswith('calfit'):
        calfitting_order = int(mode[-1])
    elif mode == 'nominal':
        # means: rad_corr done with new coeff's and local linear fitting and 16
        # skipped samples
        pass
    else:
        print("Unrecognized calibration mode requested.")
        sys.exit(-1)
        
    c = calib.Calibrator(df, do_rad_corr=rad_corr, 
                             skipsamples=skipsamples,
                             calfitting_order=calfitting_order,
                             new_rad_corr=new_rad_corr)
    
    c.calibrate()
    
    print("\nFinished calibrating.")
    
    print("Reading old RDR for",fn.timestr)
    rdr = fu.RDRReader.from_timestr(fn.timestr)
    # don't parse times for speed reasons
    rdrdf = rdr.read_df(do_parse_times=False)
    print("Done reading RDR for",fn.timestr)

    # filter to middle hour of 3h interval
    tbout_all = c.Tb.ix[c.Tb.index.hour == int(fn.hour)]
    radout_all = c.abs_radiance.ix[c.abs_radiance.index.hour == int(fn.hour)]
    
    args = [(fn,
             l1a_channel,
             rdr_channel, 
             tbout_all, 
             radout_all, 
             rdrdf,
             df.date,
             df.utc) for l1a_channel,rdr_channel in zip(l1a_channels,rdr_channels)]

    # for arg in args:
    #     process_one_channel(arg)
    pool2 = Pool(4)
    pool2.map(process_one_channel, args)
    
    pool2.close()
    pool2.join()
    
    print("Finished", fn.timestr)

def usage():
    print("\nUsage: {0} timestr mode cpus\n".format(sys.argv[0]),
"""\nWhen using 'test' as second parameter, a list of found filenames using the timestr
of parameter 1 will be printed out.""")
    sys.exit()
    
         
if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    timestr = sys.argv[1]
    fnames = glob.glob(os.path.join(fu.l1adatapath, timestr + '*_L1A.TAB'))
    fnames.sort()
    if sys.argv[2] == 'test':
        pprint.pprint(fnames)
        sys.exit()

    mode = sys.argv[2]
    cpus = sys.argv[3]

    # find outpaths that are done
    try:
        fnames_done = glob.glob(pjoin(fu.get_month_sample_path_from_mode(mode),'*.csv'))
        timestrs_done = [fu.FileName(i).timestr for i in fnames_done]
        fnames_todo = [i for i in fnames if timestrs_done.count(fu.FileName(i).timestr) < 7]
    except OSError:
        fnames_todo = fnames
        
    fnames_todo.sort()
    # create input tuple to have pool.map only 1 parameter to provide
    list_of_input_tuples = [(i, mode) for i in fnames_todo]

    pool = mypool.MyPool(int(cpus))
    pool.map(main, list_of_input_tuples)
    
    pool.close()
    pool.join()
    
    
