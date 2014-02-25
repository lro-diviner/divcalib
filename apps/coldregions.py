# -*- coding: utf-8 -*-
from __future__ import print_function, division
import pandas as pd
from diviner import file_utils as fu, calib
import numpy as np
from joblib import Parallel, delayed
import sys
import os
import logging
import glob



def get_l1a_timestring(val):
    dt = val.to_pydatetime()
    return dt.strftime("%Y%m%d%H")


def get_column_from_timestr(t, col, **kwargs):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c = calib.Calibrator(df, **kwargs)
    c.calibrate()
    return getattr(c, col)


def process_one_timestring(t, path, region):
    savename = os.path.join(path, 'tstring_'+t+'.h5')
    logging.info('Processing {}, savename: {}'.format(t, savename))
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
    root = '/raid1/maye/coldregions/no_rad_correction_padded_bbtemps'
    logging.basicConfig(filename='log_coldregions_no_rad_corr.log', level=logging.INFO)
    
    for region_no in [1,3,5]:
        print("Processing region {}".format(region_no))
        logging.info("Processing region {}".format(region_no))
        regionstr = 'region'+str(region_no)
        regiondata = pd.read_hdf(os.path.join(root,
                                              '..',
                                              'regions_data.h5'),
                                 regionstr)
        path = os.path.join(root, regionstr)
        
        timestrings = regiondata.filetimestr.unique()
        no = len(timestrings)
    
        # combined = zip(timestrings, no*[region])
        Parallel(n_jobs=10, verbose=3)(delayed(process_one_timestring)(tstr,
                                                                       path,
                                                                       regiondata) \
                                        for tstr in timestrings)
     
        container = []
        tstring_files = glob.glob(os.path.join(path, 'tstring_*.h5'))
        for f in tstring_files:
            container.append(pd.read_hdf(f, 'df'))
            os.remove(f)
        df = pd.concat(container)
        df.to_hdf(os.path.join(path, regionstr+'_no_rad_corr.h5'), 'df')

