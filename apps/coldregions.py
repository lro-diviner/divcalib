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


def get_column_from_timestr(t, col, kwargs):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c = calib.Calibrator(df, **kwargs)
    c.calibrate()
    return getattr(c, col)


def process_one_timestring(t, path, region, kwargs):
    savename = os.path.join(path, 'tstring_'+t+'.h5')
    logging.info('Processing {}, savename: {}'.format(t, savename))
    region_now = region[region.filetimestr == t]
    newrad = get_column_from_timestr(t, 'norm_radiance', kwargs)
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
    session_name = 'my_calib'
    root = os.path.join('/raid1/maye/coldregions', session_name)
    if not os.path.exists(root):
        os.mkdir(root)
    logging.basicConfig(filename='log_coldregions_'+session_name+'.log', level=logging.INFO)
    
    for region_no in [1,3,5]:
        print("Processing region {}".format(region_no))
        logging.info("Processing region {}".format(region_no))
        regionstr = 'region'+str(region_no)
        regiondata = pd.read_hdf(os.path.join(root,
                                              '..',
                                              'regions_data.h5'),
                                 regionstr)
        path = os.path.join(root, regionstr)
        if not os.path.exists(path):
            os.mkdir(path)
        timestrings = regiondata.filetimestr.unique()
        no = len(timestrings)
    
        ###
        # Control here how the calibration should be run!!
        ###
        
        kwargs = dict(do_rad_corr=False)
        
        Parallel(n_jobs=10, 
                 verbose=3)(delayed(process_one_timestring)(tstr,
                                                            path,
                                                            regiondata,
                                                            kwargs)
                            for tstr in timestrings)
     
        container = []
        tstring_files = glob.glob(os.path.join(path, 'tstring_*.h5'))
        for f in tstring_files:
            container.append(pd.read_hdf(f, 'df'))
            os.remove(f)
        df = pd.concat(container)
        df.to_hdf(os.path.join(path, regionstr+'_'+session_name+'.h5'), 'df')

