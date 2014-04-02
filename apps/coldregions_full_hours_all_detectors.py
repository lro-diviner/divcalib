# -*- coding: utf-8 -*-
from __future__ import print_function, division
import pandas as pd
from diviner import file_utils as fu, calib
import numpy as np
from joblib import Parallel, delayed
import sys
import os
import logging


root = '/raid1/maye/coldregions'
logging.basicConfig(filename='log_coldregions_full_hours.log', level=logging.INFO)


def calibrate_from_timestr(args):
    t, path = args
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c_norad = calib.Calibrator(df, do_rad_corr=False, fix_noise=False)
    c_norad.calibrate()
    c_norad.norm_radiance.to_hdf(os.path.join(path, t+'_radiance.h5'), 'radiance')
    c_norad.Tb.to_hdf(os.path.join(path, t+'_tb.h5'), 'tb')


# def process_one_timestring(args):
#     t, region = args
#     savename = os.path.join(root, 'tstring_'+t+'.h5')
#     # if os.path.exists(savename):
#     #     print "Skipping",t,'. Already done.'
#     #     return
#     print(t)
#     region_now = region[region.filetimestr == t]
#     newrad = get_column_from_timestr(t, 'norm_radiance')
#     dets = region_now.det.unique()
#     container = []
#     for det in dets:
#         detstr = 'b3_' + str(det).zfill(2)
#         subdf = region_now[region_now.det == det]
#         joined = subdf.join(newrad[detstr], how='inner')
#         container.append(joined.rename(
#                     columns=lambda x: 'newrad' if x.startswith('b3_') else x))
#     newregion = pd.concat(container)
#     newregion.to_hdf(savename,'df')


if __name__ == '__main__':
    
    try:
        subfolder = sys.argv[1]
    except IndexError:
        print("Usage: {} subfolder".format(sys.argv[0]))
        sys.exit()

    datafname = os.path.join(root, 'regions_data.h5')
    for region_number in [1,3,5]:
        path = os.path.join(root, subfolder, 'region'+str(region_number))
        if not os.path.exists(path):
            # using mkdir and not makedirs ensures that if i created a wrong path, things don't get
            # stored somewhere weird (makedirs creates all intermediate folders as well, mkdir does
            # not)
            os.mkdir(path)
        region = pd.read_hdf(datafname, 'region'+str(region_number))
    
        timestrings = region.filetimestr.unique()
        no = len(timestrings)
    
        combined = zip(timestrings, no*[path])
        print(combined[0])
        Parallel(n_jobs=8, verbose=3)(delayed(calibrate_from_timestr)(args) for args in combined)
    
