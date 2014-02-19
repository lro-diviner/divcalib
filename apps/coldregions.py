# -*- coding: utf-8 -*-
from __future__ import print_function, division
import pandas as pd
from diviner import file_utils as fu, calib
import numpy as np
from multiprocessing import Pool
import sys
import logging

root = '/raid1/maye/coldregions'
logging.basicConfig(filename='log_coldregions.log', level=logging.INFO)

def get_l1a_timestring(val):
    dt = val.to_pydatetime()
    return dt.strftime("%Y%m%d%H")


def get_column_from_timestr(t, col):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c = calib.Calibrator(df)
    c.calibrate()
    return getattr(c, col)

def process_one_timestring(args):
    t, region = args
    savename = os.path.join(root,'tstring_'+t+'.h5')
    # if os.path.exists(savename):
    #     print "Skipping",t,'. Already done.'
    #     return
    print(t)
    region_now = region[region.filetimestr == t]
    newrad = get_column_from_timestr(t, 'norm_radiance')
    dets = region_now.det.unique()
    container = []
    for det in dets:
        detstr = 'b3_' + str(det).zfill(2)
        subdf = region_now[region_now.det == det]
        joined = subdf.join(newrad[detstr], how='inner')
        container.append(joined.rename(
                    columns=lambda x: 'newrad' if x.startswith('b3_') else x))
    newregion = pd.concat(container)
    newregion.to_hdf(savename,'df')


if __name__ == '__main__':

#    sps = []
#    for region in '1 3 5'.split():
#        fname = root + 'region_sp' + region + '_9.txt'
#        sps.append(pd.read_csv(fname, sep='\s*'))
#
#    for df in sps:
#        df.second = np.round(df.second * 1000) / 1000
#        for col in ['year', 'month','date','hour','minute','det']:
#            df[col] = df[col].astype('int')
#        for col in ['year', 'month','date','hour','minute','second']:
#            df[col] = df[col].astype('string')
#        df.index = pd.to_datetime(df.year + '-' + df.month + '-' + df.date + ' ' +
#                   df.hour + ':' + df.minute + ':' + df.second, utc=True)
#        df['filetimestr'] = df.index.map(get_l1a_timestring)

    # pick region via argv, like so: python coldregions.py 1 [or 3, or 5]
    region = pd.read_hdf(root+'/sps.h5','region'+sys.argv[1])
    
    region_number = sys.argv[1]
    region = pd.read_hdf(root+'regions_data.h5', 'region'+region_number)
    
    root = root + 'region' + region_number + '/'
    timestrings = region.filetimestr.unique()
    no = len(timestrings)
    combined = zip(timestrings, no*[region])
    p = Pool(12)
    p.map(process_one_timestring, combined)

    # for sp, region in zip(sps,'1 3 5'.split()):
    #     newsp = process_one_region(sp)
    #     newsp.to_hdf(root + 'region_sp_newtb_added.h5', 'sp' + region)

