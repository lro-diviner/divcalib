# coding: utf-8
import os.path as path
import spice
from datetime import datetime as dt
from file_utils import kernelpath

def get_version_from_fname(fname):
    # cut off extension
    pre_ext = path.splitext(fname)[0]
    # split by _ and get last element (the version number string, if available)
    if not '_' in pre_ext:
        return None
    last_token = pre_ext.split('_')[-1]
    if not last_token.startswith('v'):
        return None
    return int(last_token[1:])
    
