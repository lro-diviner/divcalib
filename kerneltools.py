# coding: utf-8
import os
import spice
from datetime import datetime as dt
from file_utils import kernelpath
import glob

# from ConfigParser import ConfigParser
#
# config = ConfigParser()
# config.read('level1b.config')

def get_version_from_fname(fname):
    # cut off extension
    pre_ext = os.path.splitext(fname)[0]
    # split by _ and get last element (the version number string, if available)
    if not '_' in pre_ext:
        return None
    last_token = pre_ext.split('_')[-1]
    if not last_token.startswith('v'):
        return None
    return last_token, int(last_token[1:])


def get_times_from_ck(fname):
    "Parse times from a ck filename. Returns python datetime objects."
    # ex: 'moc42_2009099_2009100_v01.bc'
    # i checked: all ck files start with moc42
    tokens = os.path.splitext(fname)[0].split('_')
    startstr, endstr = tokens[1], tokens[2]
    formatstr = '%Y%j'
    starttime = dt.strptime(startstr, formatstr)
    endtime = dt.strptime(endstr, formatstr)
    return (starttime, endtime)


def load_kernels_for_timestr(timestr):
    number_of_kernels_loaded = 0
    return number_of_kernels_loaded


def get_available_ck():
    root = os.path.join(kernelpath, 'ck')
    return os.listdir(root)

def find_ck_for_timestr(timestr):
    """docstring for find_ck_for_timestr"""
    return 'bogus_path'

class CKFileName(object):
    """Class to create and handle CK file names."""
    extension = 'bc'
    prefix = 'moc42'  # have not seen any other one
    root = os.path.join(kernelpath, 'ck')

    @classmethod
    def from_fname(cls, fname):
        "Including this for better readability. same as CKFileName(fname=fname)"
        return cls(fname=fname)

    @classmethod
    def from_timestr(cls, timestr):
        return cls(timestr=timestr)

    def __init__(self, timestr=None, fname=None):
        super(CKFileName, self).__init__()
        if fname is not None:
            self.fname = fname
            self.dirname = os.path.dirname(fname)
            self.basename = os.path.basename(fname)
            self.version_string, self.version = get_version_from_fname(fname)
            self.start, self.end = get_times_from_ck(fname)
        elif timestr is not None:
            self.timestr = timestr
            time = dt.strptime(timestr, '%Y%m%d%H')

        else:
            raise Exception('CKFileName', 'You have to provide either timestr or fname.')
