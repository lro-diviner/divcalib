# coding: utf-8
import os
import spice
from datetime import datetime as dt
from file_utils import kernelpath

def get_version_from_fname(fname):
    # cut off extension
    pre_ext = os.path.splitext(fname)[0]
    # split by _ and get last element (the version number string, if available)
    if not '_' in pre_ext:
        return None
    last_token = pre_ext.split('_')[-1]
    if not last_token.startswith('v'):
        return None
    return int(last_token[1:])
    
def get_times_from_ck(fname):
    "Parse times from a ck filename."
    # ex: 'moc42_2009099_2009100_v01.bc'
    # i checked: all ck files start with moc42
    tokens = os.path.splitext(fname)[0].split('_')
    startstr, endstr = tokens[1], tokens[2]
    formatstr = '%Y%j'
    starttime = dt.strptime(startstr, formatstr)
    endtime = dt.strptime(endstr, formatstr)
    return (starttime, endtime)
    
def load_kernels_for_timestamp(timestamp):
    number_of_kernels_loaded = 0
    return number_of_kernels_loaded