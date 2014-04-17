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
