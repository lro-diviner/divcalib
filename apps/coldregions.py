# -*- coding: utf-8 -*-
from __future__ import print_function, division
import pandas as pd
from diviner import file_utils as fu, calib
import numpy as np
from multiprocessing import Pool
import sys
import os
import logging

root = '/raid1/maye/coldregions'
logging.basicConfig(filename='log_coldregions.log', level=logging.INFO)


def get_l1a_timestring(val):
    dt = val.to_pydatetime()
    return dt.strftime("%Y%m%d%H")


def get_column_from_timestr(t, col, **kwargs):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c = calib.Calibrator(df, **kwargs)
    c.calibrate()
    return getattr(c, col)


def process_one_timestring(args):
    t, region = args
    savename = os.path.join(root, 'tstring_'+t+'.h5')
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
    
    try:
        region_number = sys.argv[1]
        subfolder = sys.argv[2]
    except IndexError:
        print('Use one of [1,3,5] to indicate which region to produce. And add a subfolder string'
              ' after that like so: {0} 1 no_rad_correction (for example)'.format(sys.argv[0]))
        sys.exit()
    region = pd.read_hdf(root+'/../regions_data.h5', 'region'+region_number)
    
    timestrings = region.filetimestr.unique()
    no = len(timestrings)
    
    combined = zip(timestrings, no*[region])
    p = Pool(12)
    p.map(process_one_timestring, combined)
    
    hours = glob.glob()

