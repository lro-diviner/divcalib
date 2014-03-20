# -*- coding: utf-8 -*-
from __future__ import print_function, division
import pandas as pd
from diviner import file_utils as fu, calib, ana_utils as au
import numpy as np
from joblib import Parallel, delayed
import sys
import os
import logging
import glob


def get_calib(t, c, kwargs):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    rdr2 = calib.Calibrator(df, **kwargs)
    rdr2.calibrate()
    helper = au.CalibHelper(rdr2)
    return helper.get_c_rad_molten(c, t, 'norm')


def process_one_timestring(tstr, path, region, kwargs):
    savename = os.path.join(path, 'tstring_'+tstr+'.h5')
    logging.info('Processing {}, savename: {}'.format(tstr, savename))
    region_now = region[region.filetimestr == tstr]
    newrad = get_calib(tstr, 9, kwargs)
    oldrad = region_now[['det','radiance']]
    oldrad = oldrad.reset_index()
    newregion = newrad.merge(oldrad, on=['index','det']).set_index('index')
    newregion.to_hdf(savename,'df')


if __name__ == '__main__':
    session_name = 'my_calib'
    root = os.path.join('/raid1/maye/coldregions', session_name)
    if not os.path.exists(root):
        os.mkdir(root)
    logging.basicConfig(filename='log_coldregions_'+session_name+'.log', level=logging.INFO)
    
    for region_no in [1]:
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
    
        ###
        # Control here how the calibration should be run!!
        ###
        
        kwargs = dict(do_jpl_calib=False)
        
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

