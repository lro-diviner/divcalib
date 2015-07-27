# -*- coding: utf-8 -*-
# file utilities for Diviner
from __future__ import print_function, division
import pandas as pd
import numpy as np
import sys
import glob
from dateutil.parser import parse as dateparser
import os
from os import path
from os.path import join as pjoin
import socket
from datetime import timedelta
from datetime import datetime as dt
from .data_prep import define_sdtype, prepare_data, index_by_time
from collections import deque
import logging
from diviner import __path__
from subprocess import call
from .exceptions import (DivTimeLengthError,
                         RDRR_NotFoundError,
                         RDRS_NotFoundError,
                         L1ANotFoundError)

from cliutils import cliargs
# from plot_utils import ProgressBar
import zipfile

hostname = socket.gethostname().split('.')[0]
user = os.environ['USER']
home = os.environ['HOME']
if sys.platform == 'darwin':
    datapath = pjoin(home, 'data', 'diviner')
    outpath = pjoin(datapath, 'out')
    kernelpath = pjoin(home, 'data', 'spice', 'diviner')
    codepath = pjoin(home, 'Dropbox', 'src', 'diviner')
    l1adatapath = pjoin(datapath, 'l1a_data')
    rdrdatapath = pjoin(datapath, 'opsRDR')
    rdrrdatapath = pjoin(
        os.environ['HOME'], 'data', 'diviner', 'rdrr_data')
    rdrsdatapath = pjoin(
        os.environ['HOME'], 'data', 'diviner', 'rdrs_data')
else:
    datapath = pjoin(path.sep, hostname, user)
    outpath = pjoin(datapath, 'rdr_out')
    kernelpath = pjoin(datapath, 'kernels')
    codepath = pjoin(os.environ['HOME'], 'src/diviner')
    feipath = pjoin(path.sep, 'luna1', 'marks', 'feidata')
    l1adatapath = pjoin(feipath, 'DIV:opsL1A', 'data')
    rdrdatapath = pjoin(feipath, 'DIV:opsRdr', 'data')
    rdrrdatapath = '/luna7/marks/rdrr_data'
    rdrsdatapath = '/luna6/marks/rdrs_data'


#
# data transport utilities
#
@cliargs
def scp_l1a_file(tstr):
    src_host = 'luna4'
    target_path = pjoin(datapath, 'l1a_data')
    src_datadir = '/luna1/marks/feidata/DIV:opsL1A/data'
    cmd = 'scp {0}:{1}/{2}_L1A.TAB {3}'.format(src_host, src_datadir,
                                               tstr, target_path)
    print(cmd)
    call(cmd, shell=True)


def scp_opsRDR_file(tstr):
    src_host = 'luna4'
    target_path = pjoin(datapath, 'opsRDR')
    cmd = 'scp {0}:{1}/{2}_RDR.TAB.zip {3}'.format(src_host, rdrdatapath,
                                                   tstr, target_path)
    call(cmd, shell=True)


#
# data browsing utils
#

def available_files(datapath, year=None, ext=None):
    "Provide year as constraining argument."
    globbedlist = glob.glob(datapath + '/*' + ext)
    if year is None:
        retval = globbedlist
    else:
        retval = []
        for fname in globbedlist:
            if str(year) in os.path.basename(fname):
                retval.append(fname)
    return retval


def available_l1a_files(year=None):
    return available_files(l1adatapath, year=year, ext='_L1A.TAB')


def available_rdrr_files(year=None):
    return available_files(rdrrdatapath, year=year, ext='.rdrr')


def available_rdrs_files(year=None):
    return available_files(rdrsdatapath, year=year, ext='.rdrs')


#
# general utilities
#
def get_tstr(indata):
    # datetime type
    if hasattr(indata, 'strftime'):
        return indata.strftime("%Y%m%d%H")
    # pandas timestamp
    elif hasattr(indata, 'to_pydatetime'):
        t = indata.to_pydatetime()
        return t.strftime("%Y%m%d%H")
    else:
        # filename string
        basename = path.basename(indata)
        return basename[:10]


def tstr_to_datetime(tstr):
    if not len(tstr) in [4, 6, 8, 10]:
        raise DivTimeLengthError(tstr, ['YYYY',
                                        'YYYYMM',
                                        'YYYYMMDD',
                                        'YYYYMMDDHH'])
    if len(tstr) == 4:
        tstr += '010100'
    elif len(tstr) == 6:
        tstr += '0100'
    elif len(tstr) == 8:
        tstr += '00'
    dtime = dt.strptime(tstr, '%Y%m%d%H')
    return dtime


def fname_to_tstr(fname):
    return path.basename(fname)[:10]


def fname_to_tindex(fname):
    """Convert filename to time-index for indexing pd.DataFrame.

    Convert a filename to a dataframe-index string to get the hour indicated by
    the filename.
    """
    tstr = fname_to_tstr(fname)
    return tstr_to_tindex(tstr)


def tstr_to_tindex(tstr):
    return tstr[:8] + ' ' + tstr[8:]


def tstr_to_l1a_fname(tstr):
    return pjoin(l1adatapath, tstr + '_L1A.TAB')


def timestrings_for_day(day_string):
    dr = pd.date_range(day_string, freq='H', periods=24)
    return [get_tstr(i) for i in dr]


def calc_daterange(start, end):
    """Return list of YYYYMMDDHH strings for each hour between start and end"""
    dr = pd.date_range(tstr_to_datetime(start),
                       tstr_to_datetime(end),
                       freq='H')
    return [get_tstr(i) for i in dr]


#
# Tools for data output to tables
#
def get_month_sample_path_from_mode(mode):
    return pjoin(datapath, 'rdr20_month_samples', mode)


class DivTime(object):

    """Manage time-related metadata for Diviner observations."""
    fmt = ''  # set in derived class!

    @classmethod
    def from_dtime(cls, dtime):
        tstr = dtime.strftime(cls.fmt)
        return cls(tstr)

    def __init__(self, tstr):
        if len(tstr) != self.lentstr:
            raise DivTimeLengthError(tstr, self.fmt)
        self.tstr = tstr
        self.year = self.tstr[:4]
        self.month = self.tstr[4:6]
        self.day = self.tstr[6:8]
        if self.lentstr > 8:
            self.hour = self.tstr[8:10]
        self.dtime = dt.strptime(self.tstr, self.fmt)


class DivHour(DivTime):

    """Class for the usual hour-strings."""
    fmt = '%Y%m%d%H'
    lentstr = 10

    @property
    def tindex(self):
        return self.tstr[:8] + ' ' + self.tstr[8:]

    def previous(self):
        return DivHour.from_dtime(self.dtime - timedelta(hours=1))

    def next(self):
        return DivHour.from_dtime(self.dtime + timedelta(hours=1))


class DivDay(DivTime):

    """Class for a full day of Diviner data."""
    fmt = '%Y%m%d'
    lentstr = 8


class DivObs(object):

    @classmethod
    def from_fname(cls, fname):
        basename = path.basename(fname)
        return cls(basename[:10])

    def __init__(self, tstr):
        self.time = DivHour(tstr)
        self.l1afname = L1AFileName.from_tstr(tstr)
        self.rdrrfname = RDRRFileName.from_tstr(tstr)
        self.rdrsfname = RDRSFileName.from_tstr(tstr)

    def next(self):
        nexthour = self.time.next()
        return DivObs(nexthour.tstr)

    def previous(self):
        prevhour = self.time.previous()
        return DivObs(prevhour.tstr)

    def get_l1a(self):
        return L1ADataFile(self.l1afname.path).open()

    def get_l1a_dirty(self):
        return L1ADataFile(self.l1afname.path).open_dirty()

    def get_rdrr(self):
        return RDRR_Reader(self.rdrrfname.path).open()

    def get_rdrs(self):
        return RDRS_Reader(self.rdrsfname.path).open()

    def copy(self):
        return DivObs(self.time.tstr)


class FileName(object):

    """Managing class for file name attributes."""

    ext = ''  # fill in child class !
    datapath = ''  # fill in child class !

    @classmethod
    def from_tstr(cls, tstr):
        fname = pjoin(cls.datapath, tstr + cls.ext)
        return cls(fname)

    def __init__(self, fname):
        super(FileName, self).__init__()
        self.basename = path.basename(fname)
        self.dirname = path.dirname(fname)
        self.file_id, self.ext = path.splitext(self.basename)
        self.tstr = self.file_id.split('_')[0]
        # as Diviner FILES only exist in separations of hours I use DivHour
        # here:
        self.divhour = DivHour(self.tstr)
        # save everything after the first '_' as rest
        self.rest = self.basename[len(self.tstr):]

    @property
    def path(self):
        return self.fname

    @property
    def name(self):
        return self.fname

    @property
    def fname(self):
        return pjoin(self.dirname, self.tstr + self.rest)


class L1AFileName(FileName):
    ext = '_L1A.TAB'
    datapath = l1adatapath


class RDRRFileName(FileName):
    ext = '.rdrr'
    datapath = rdrrdatapath


class RDRSFileName(FileName):
    ext = '.rdrs'
    datapath = rdrsdatapath


#
# Tools for parsing text files of data
#
def split_by_n(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]


def timediff(s):
    return s - s.shift(1)


def parse_header_line(line):
    """Parse header lines.

    >>> s = ' a   b  c    '
    >>> parse_header_line(s)
    ['a', 'b', 'c']
    >>> s = '  a, b  ,   c '
    >>> parse_header_line(s)
    ['a', 'b', 'c']
    """
    line = line.strip('#')
    if ',' in line:
        newline = line.split(',')
    else:
        newline = line.split()
    return [i.strip().lower() for i in newline]


class L1AHeader(object):
    from l1a_header import headerstring
    # beware: parse_header_line converts to lower case!
    columns = parse_header_line(headerstring)

    tel1cols = ["a{0}_{1}".format(i, str(j).zfill(2))
                for i in range(1, 7) for j in range(1, 22)]
    tel2cols = ['b{0}_{1}'.format(i, str(j).zfill(2))
                for i in range(1, 4) for j in range(1, 22)]

    datacols = tel1cols + tel2cols

    metadatacols = list(set(columns) - set(datacols))
    metadatacols.sort()


def get_rdr_headers(fname):
    """Get headers from both ops and PDS RDR files."""
    if isinstance(fname, zipfile.ZipFile):
        f = fname.open(fname.namelist()[0])
    else:
        f = open(fname)
    while True:
        line = f.readline()
        if not line.startswith('# Header'):
            break
    f.close()
    return parse_header_line(line)


class GroundCalibFile(file):

    def __init__(self, *args, **kwargs):
        super(GroundCalibFile, self).__init__(*args, **kwargs)
        self.get_headers()

    def get_headers(self):
        self.skip = 0
        while True:
            self.skip += 1
            line = self.readline()
            if not line.startswith('#'):
                self.headers = parse_header_line(line)
                return

    def read_data(self, nrows=None):
        self.seek(0)
        df = pd.io.parsers.read_csv(self,
                                    skiprows=self.skip + 1,
                                    skipinitialspace=True,
                                    names=self.headers,
                                    nrows=nrows)
        return parse_times(df)


class RDRReader(object):
    """RDRs are usually zipped, so this wrapper takes care of that."""

    datapath = rdrdatapath

    @classmethod
    def from_tstr(cls, tstr):
        fnames = glob.glob(pjoin(cls.datapath,
                                 tstr + '*_RDR.TAB.zip'))
        return cls(fname=fnames[0])

    def __init__(self, fname, nrows=None):
        super(RDRReader, self).__init__()
        self.fname = fname
        self.get_rdr_headers()
        # to not break existing code refererring to self.open
        self.read_df = self.open

    def find_fnames(self):
        self.fnames = glob.glob(pjoin(self.datapath,
                                      self.tstr + '*_RDR.TAB.zip'))

    def open_file(self):
        if self.fname.lower().endswith('.zip'):
            zfile = zipfile.ZipFile(self.fname)
            self.f = zfile.open(zfile.namelist()[0])
        else:
            self.f = open(self.fname)
        return

    def get_rdr_headers(self):
        """Get headers from both ops and PDS RDR files."""
        # skipcounter
        self.open_file()
        self.no_to_skip = 0
        while True:
            line = self.f.readline()
            self.no_to_skip += 1
            if not line.startswith('# Header'):
                break
        self.headers = parse_header_line(line)
        self.f.close()

    def open(self, nrows=None, do_parse_times=True):
        self.open_file()
        df = pd.io.parsers.read_csv(self.f,
                                    skiprows=self.no_to_skip,
                                    skipinitialspace=True,
                                    names=self.headers,
                                    nrows=nrows,
                                    )
        self.f.close()
        return parse_times(df) if do_parse_times else df

    def gen_open(self):
        for fname in self.fnames:
            zfile = zipfile.ZipFile(fname)
            yield zfile.open(zfile.namelist()[0])


def parse_times(df):
    format = '%d-%b-%Y %H:%M:%S.%f'
    # I don't need to round the seconds here because the df.utc data has
    # already a 3-digit millisecond string: '19:00:00.793'
    times = pd.to_datetime(df.date + ' ' + df.utc, format=format, utc=False)
    df.set_index(times, inplace=True)
    return df.drop(['date', 'utc'], axis=1)


def read_l1a_data(fname, nrows=None):
    df = pd.io.parsers.read_csv(fname,
                                names=L1AHeader.columns,
                                na_values='-9999',
                                skiprows=8,
                                skipinitialspace=True)
    return parse_times(df)


def get_headers_pprint(fname):
    """Get headers from pprint output.

    >>> fname = '/Users/maye/data/diviner/noise2.tab'
    >>> headers = get_headers_pprint(fname)
    >>> headers[:7]
    ['date', 'month', 'year', 'hour', 'minute', 'second', 'jdate']
    """
    with open(fname) as f:
        headers = parse_header_line(f.readline())
    return headers


def read_pprint(fname):
    """Read tabular diviner data into pandas data frame and return it.

    Lower level function. Use read_div_data which calls this as appropriate.
    """

    # pandas parser does not read this file correctly, but loadtxt does.
    # first will get the column headers

    headers = get_headers_pprint(fname)
    print("Found {0} headers: {1}".format(len(headers), headers))

    # use numpy's loadtxt to read the tabulated file into a numpy array
    ndata = np.loadtxt(fname, skiprows=1)
    dataframe = pd.DataFrame(ndata)
    dataframe.columns = headers
    dataframe.sort('jdate', inplace=True)
    return dataframe


def get_df_from_h5(fname):
    """Provide df from h5 file."""
    try:
        print("Opening {0}".format(fname))
        store = pd.HDFStore(fname)
        df = store[store.keys()[0]]
        store.close()
    except:
        print("file {0} not found.".format(fname))
    return df


def read_div_data(fname):
    with open(fname) as f:
        line = f.readline()
        if any(['dlre_edr.c' in line, 'Header' in line]):
            rdr = RDRReader(f.fname)
            return rdr.read_df()
        elif fname.endswith('.h5'):
            return get_df_from_h5(fname)
        else:
            return read_pprint(fname)


#
# tools for parsing binary data of Diviner
#

def get_dtypes_from_columns(keys):
    return np.dtype([(key, 'f8') for key in keys])


def parse_descriptor(fpath):
    f = open(fpath)
    lines = f.readlines()
    f.close()
    s = pd.Series(lines)
    s = s.drop(0)

    def unpack_str(value):
        val2 = value.split(' ')
        t = [i.strip().strip("'") for i in val2]
        return t[0].lower()

    columns = s.map(unpack_str)
    keys = columns.values
    rec_dtype = get_dtypes_from_columns(keys)
    return rec_dtype, keys


def get_dtypes_from_binary_pipe(lines):
    first = [i.split()[0].strip("'") for i in lines]
    second = [i for i in first if i][1:]
    keys = second[::2][:-1]
    rec_dtype = get_dtypes_from_columns(keys)
    return rec_dtype, keys


def read_binary_pipe(fpath):
    f = open(fpath)
    lines = []
    while True:
        line = f.readline()
        lines.append(line)
        if 'end' in line:
            break

    rec_dtype, keys = get_dtypes_from_binary_pipe(lines)

    data = np.fromfile(f, dtype=rec_dtype)
    df = pd.DataFrame(data, columns=keys)
    return df


def get_div247_dtypes():
    despath = pjoin(__path__[0], 'data', 'div247.des')
    return parse_descriptor(despath)


def get_div38_dtypes():
    despath = pjoin(__path__[0], 'data', 'div38.des')
    return parse_descriptor(despath)

#
# rdrplus tools
#


def read_rdrplus(fpath, nrows):
    with open(fpath) as f:
        line = f.readline()
        headers = parse_header_line(line)

    return pd.io.parsers.read_csv(fpath, names=headers, na_values=['-9999'],
                                  skiprows=1, nrows=nrows)


def fname_to_df(fname, rec_dtype, keys):
    with open(fname) as f:
        data = np.fromfile(f, dtype=rec_dtype)
    df = pd.DataFrame(data, columns=keys)
    return df


def folder_to_df(folder, top_end=None, verbose=False):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder + '/*.div247')
    fnames.sort()
    if not top_end:
        top_end = len(fnames)
    dfall = pd.DataFrame()
    olddf = None
    for i, fname in enumerate(fnames[:top_end]):
        if verbose:
            print(round(float(i) * 100 / top_end, 1), '%')
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        if olddf is not None:
            for s in df.filter(regex='_labels'):
                df[s] += olddf[s].max()
        olddf = df.copy()
        dfall = pd.concat([dfall, df])
    to_store = dfall[dfall.calib_block_labels > 0]
    return to_store


def get_storename(folder):
    path = os.path.realpath(folder)
    dirname = '/luna4/maye/data/h5_div247'
    basename = os.path.basename(path)
    storename = pjoin(dirname, basename + '.h5')
    return storename


def folder_to_store(folder):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder + '/*.div247')
    if not fnames:
        print("Found no files.")
        return
    fnames.sort()
    # opening store in overwrite-mode
    storename = get_storename(folder)
    print(storename)
    store = pd.HDFStore(storename, mode='w')
    nfiles = len(fnames)
    olddf = None
    cols = ['calib_block_labels', 'space_block_labels', 'bb_block_labels',
            'st_block_labels', 'is_spaceview', 'is_bbview', 'is_stview',
            'is_moving', 'is_stowed', 'is_calib']
    for i, fname in enumerate(fnames):
        print(round(float(i) * 100 / nfiles, 1), '%')
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        to_store = df[df.calib_block_labels > 0]
        if len(to_store) == 0:
            continue
        if olddf is not None:
            for s in to_store.filter(regex='_labels'):
                to_store[s] += olddf[s].max()
        olddf = to_store.copy()
        try:
            store.append('df', to_store, data_columns=cols)
        except Exception as e:
            store.close()
            print('at', fname)
            print('something went wrong at appending into store.')
            print(e)
            return
    print("Done.")
    store.close()


class DataPump(object):
    """class to provide Diviner data in different ways."""
    rec_dtype, keys = get_div247_dtypes()
    datapath = '/luna4/maye/data/div247/'

    def __init__(self, fname_pattern=None, tstr=None, fnames_only=False):
        self.fnames_only = fnames_only
        if fname_pattern and path.exists(fname_pattern):
            if path.isfile(fname_pattern):
                self.get_df(fname_pattern)
            elif path.isdir(fname_pattern):
                pass

        self.tstr = tstr
        self.current_time = dateparser(tstr)
        self.fname = pjoin(datapath,
                           self.current_time.strftime("%Y%m%d%H"))
        self.increment = timedelta(hours=1)

    # def gen_fnames(self, pattern, top):
    #    for path, dirlist, filelist in os.walk(top)

    def get_fnames(self):
        dirname = path.dirname(self.fname)
        fnames = glob.glob(dirname + '/*.div247')
        fnames.sort()
        self.fnames = fnames
        self.index = self.fnames.index(self.fname)

    def open_and_process(self):
        df = fname_to_df(self.fname, self.rec_dtype, self.keys)
        df = prepare_data(df)
        define_sdtype(df)
        self.df = df

    def get_df(self, fname):
        self.fname = fname
        self.get_fnames()
        self.open_and_process()
        return self.df

    def get_next(self):
        self.fname = self.fnames[self.index + 1]
        self.index += 1
        self.open_and_process()
        return self.df


class H5DataPump(object):
    datapath = pjoin(datapath, 'h5_div247')

    def __init__(self, tstr):
        self.tstr = tstr
        self.fnames = self.get_fnames()
        if len(self.fnames) == 0:
            print("No files found.")
        self.fnames.sort()

    def get_fnames(self):
        return glob.glob(pjoin(self.datapath, self.tstr[:4] + '*'))

    def store_generator(self):
        for fname in self.fnames:
            yield pd.HDFStore(fname)

    def fname_generator(self):
        for fname in self.fnames:
            yield fname

    def df_generator(self):
        for fname in self.fnames:
            yield self.get_df_from_h5(fname)


class DivXDataPump(object):
    """Abstract Class to stream div38 or div247 data.

    Needs to be completed in derived class.
    Things missing is self.datapath to be set in deriving class.
    """
    tstr_parser = {4: '%Y', 6: '%Y%m',
                   8: '%Y%m%d', 10: '%Y%m%d%H'}

    # overwrite in child class!!
    this_ext = '...'

    def __init__(self, tstr):
        """tstr is of format yyyymm[dd[hh]], used directly by glob.

        This means, less files are found if the tstr is longer, as it
        is then more restrictive.
        """
        self.tstr = tstr
        self.time = dt.strptime(tstr,
                                self.tstr_parser[len(tstr)])
        self.fnames = self.find_fnames()
        self.fname = FileName(self.fnames[0])
        self.fnames.sort()

    def find_fnames(self):
        "Needs self.datapath to be defined in derived class."
        searchpath = pjoin(
            self.datapath, self.tstr[:6], self.tstr + '*')
        fnames = glob.glob(searchpath)
        if not fnames:
            print("No files found. Searched like this:\n")
            print(searchpath)
        fnames.sort()
        return fnames

    def gen_open(self):
        for fname in self.fnames:
            self.current_fname = fname
            print(fname)
            yield open(fname)

    def get_fname_from_time(self, time):
        return time.strftime("%Y%m%d%H" + self.this_ext)

    def process_one_file(self, f):
        data = np.fromfile(f, dtype=self.rec_dtype)
        return pd.DataFrame(data, columns=self.keys)

    def gen_dataframes(self, n=None):
        # caller actually doesn't allow n=None anyways. FIX?
        if n is None:
            n = len(self.fnames)
        openfiles = self.gen_open()
        i = 0
        while i < n:
            i += 1
            df = self.process_one_file(openfiles.next())
            yield df

    def clean_final_df(self, df):
        "need to wait until final df before defining sdtypes."
        df = prepare_data(df)
        define_sdtype(df)
        return df

    def get_n_hours_from_t(self, n, t):
        "t in hours, n = how many hours."
        start_time = self.time + timedelta(hours=t)
        l = []
        for i in xrange(n):
            new_time = start_time + timedelta(hours=i)
            basename = self.get_fname_from_time(new_time)
            print(basename)
            dirname = path.dirname(self.fnames[0])
            fname = pjoin(dirname, basename)
            l.append(self.process_one_file(fname))
        df = pd.concat(l)
        return self.clean_final_df(df)


class Div247DataPump(DivXDataPump):
    "Class to stream div247 data."
    if sys.platform != 'darwin':
        datapath = "/luna1/marks/div247"
    else:
        datapath = "/Users/maye/data/diviner/div247"
    rec_dtype, keys = get_div247_dtypes()

    this_ext = '.div247'

    def clean_final_df(self, df_in):
        """Declare NaN value and pad nan data for some."""
        df = index_by_time(df_in)
        df[df == -9999.0] = np.nan
        df = prepare_data(df)
        define_sdtype(df)
        return df


class Div38DataPump(DivXDataPump):
    datapath = pjoin(datapath, 'div38')
    rec_dtype, keys = get_div38_dtypes()
    this_ext = '.div38'

    def find_fnames(self):
        return glob.glob(pjoin(self.datapath, self.tstr + '*'))


class L1ADataFile(object):
    def __init__(self, fname):
        self.fname = fname
        self.fn_handler = FileName(fname)
        self.header = L1AHeader()

    def parse_tab(self, fname=None):
        if not fname:
            fname = self.fname
        try:
            df = pd.io.parsers.read_csv(fname,
                                        names=self.header.columns,
                                        na_values='-9999',
                                        skiprows=8,
                                        skipinitialspace=True)
        except IOError as e:
            raise L1ANotFoundError(e)
        return df

    def parse_times(self, df=None):
        if df is None:
            df = self.df
        return parse_times(df)

    def clean(self, df=None):
        if df is None:
            df = self.df
        df = prepare_data(df)
        define_sdtype(df)
        return df

    def open_dirty(self):
        return self.read_dirty()

    def read_dirty(self):
        df = self.parse_tab()
        df = self.parse_times(df)
        return df

    def open(self):
        return self.read()

    def read(self, fname=None):
        df = self.parse_tab(fname)
        df = self.parse_times(df)
        return self.clean(df)


def get_clean_l1a(tstr):
    obs = DivObs(tstr)
    return obs.get_l1a()


def get_dirty_l1a(tstr):
    obs = DivObs(tstr)
    return obs.get_l1a_dirty()


def open_and_accumulate(tstr, minimum_number=1):
    """Open L1A datafile fname and accumulate neighboring data.

    To explain why I accumulate first dirty files:
    One CAN NOT accumulate cleaned data files, because I rely on the numbering
    of calib-blocks to be unique!
    Each cleaning operation starts the numbering from 1 again!

    'minimum_number' controls how many hour files are attached on each side.
    """

    # centerfile = L1ADataFile.from_tstr(tstr)
    obs = DivObs(tstr)
    if not path.exists(obs.l1afname.path):
        raise L1ANotFoundError(obs.l1afname.path)

    dataframes = deque()
    dataframes.append(obs.get_l1a_dirty())

    # append previous hours until calib blocks found
    # start with center file:
    # fn_handler = FileName(centerfile.fname)
    current = obs.copy()

    appended_counter = 0
    while True:
        previous = current.previous()
        try:
            dataframes.appendleft(previous.get_l1a_dirty())
        except L1ANotFoundError:
            logging.warning('Could not find previous L1A file {}'
                            .format(previous.time.tstr))
            break
        else:
            logging.debug("Appending {0} on the left."
                          .format(previous.time.tstr))
            appended_counter += 1
        if any(previous.get_l1a().is_calib) and \
                (appended_counter >= minimum_number):
            break
        current = previous.copy()

    # append next hours until calib blocks found
    # go back to center file name
    current = obs.copy()
    appended_counter = 0
    while True:
        next = current.next()
        try:
            dataframes.append(next.get_l1a_dirty())
        except IOError:
            logging.warning('Could not find following file {}'
                            .format(next.time.tstr))
            break
        else:
            logging.debug("Appending {0} on the right.".format(next.time.tstr))
            appended_counter += 1

        if any(next.get_l1a().is_calib) and \
                (appended_counter >= minimum_number):
            break
        current = next.copy()

    df = prepare_data(pd.concat(list(dataframes)))
    define_sdtype(df)
    return df


class L1ADataPump(DivXDataPump):
    datapath = l1adatapath

    this_ext = '_L1A.TAB'

    def find_fnames(self):
        return glob.glob(pjoin(self.datapath,
                               self.tstr + '*' + self.this_ext))

    def clean_final_df(self, df):
        df = prepare_data(df)
        define_sdtype(df)
        return df

    def process_one_file(self, f):
        return read_l1a_data(f)

    def get_default(self):
        df = read_l1a_data(self.fnames[0])
        return self.clean_final_df(df)


class RDRxReader(object):
    def __init__(self, fname):
        super(RDRxReader, self).__init__()
        dtypes, keys = parse_descriptor(self.descriptorpath)
        try:
            self.df = fname_to_df(fname, dtypes, keys)
        except IOError as e:
            raise self.exception(e)

    def parse_times(self):
        df = self.df
        timecols = [u'yyyy', u'mm', u'dd', u'hh', u'mn', u'ss']
        secs_only = df.ss.astype('int')
        msecs = (df.ss - secs_only).round(3)
        mapper = lambda x: str(int(x)).zfill(2)
        times = pd.to_datetime(df.yyyy.astype('int').astype('str') +
                               df.mm.map(mapper) +
                               df.dd.map(mapper) +
                               df.hh.map(mapper) +
                               df.mn.map(mapper) +
                               df.ss.map(mapper) +
                               (msecs).astype('str').str[1:],
                               format='%Y%m%d%H%M%S.%f',
                               utc=False)
        df.set_index(times, inplace=True)
        self.df = df.drop(timecols, axis=1)

    def open(self):
        self.df[self.df == -9999] = np.nan
        self.parse_times()
        # df = prepare_data(self.df)
        # define_sdtype(df)
        # self.df = df
        return self.df

    def open_raw(self):
        return self.df


class RDRR_Reader(RDRxReader):
    exception = RDRR_NotFoundError
    descriptorpath = pjoin(rdrrdatapath, 'rdrr.des')
    extension = '.rdrr'


class RDRS_Reader(RDRxReader):
    exception = RDRS_NotFoundError
    descriptorpath = pjoin(rdrsdatapath, 'rdrs.des')
    extension = '.rdrs'
