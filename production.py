from __future__ import division, print_function
from diviner import calib
from diviner import file_utils as fu
from diviner import ana_utils as au
from joblib import Parallel, delayed
import pandas as pd
import logging
import os
import sys
import rdrx


def get_tb_savename(savedir, tstr):
    return os.path.join(savedir, tstr+'_tb.hdf')


def get_rad_savename(savedir, tstr):
    return os.path.join(savedir, tstr+'_radiance.hdf')


def get_example_data():
    tstr = '2013031707'
    df = fu.get_clean_l1a(tstr)
    rdr2 = calib.Calibrator(df)
    rdr2.calibrate()
    rdr1 = rdrx.RDRR(tstr)
    return rdr1,rdr2
def calibrate_fname(tstr, savedir):
    print(tstr)
    sys.stdout.flush()
    df = fu.open_and_accumulate(tstr=tstr)
    try:
        if len(df) == 0:
            return
    except TypeError:
        return
    rdr2 = calib.Calibrator(df, fix_noise=True)
    rdr2.calibrate()
    rdr2.Tb.to_hdf(get_tb_savename(savedir, tstr), 'df')
    rdr2.abs_radiance.to_hdf(get_rad_savename(savedir, tstr), 'df')


def only_calibrate():
    logging.basicConfig(filename='divcalib_only_calibrate.log',
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)
    
    with open('/u/paige/maye/src/diviner/data/2010120102_2010122712.txt') as f:
        timestrings = f.readlines()
    
    savedir = '/raid1/maye/rdr_out/only_calibrate'
    Parallel(n_jobs=8, 
             verbose=5)(delayed(calibrate_fname)(tstr.strip(),
                                                        savedir)
                                                        for tstr in timestrings)
                                                        