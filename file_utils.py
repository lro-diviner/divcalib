# -*- coding: utf-8 -*-
# file utilities for Diviner
from __future__ import print_function, division
import pandas as pd
import numpy as np
import sys
import glob
from dateutil.parser import parse as dateparser
import os
import socket
from datetime import timedelta
from datetime import datetime as dt
from data_prep import define_sdtype, prepare_data, index_by_time
from collections import deque
import logging


# from plot_utils import ProgressBar
import zipfile

hostname = socket.gethostname()
hostname = hostname.split('.')[0]

if sys.platform == 'darwin':
    datapath = '/Users/maye/data/diviner'
    outpath = '/Users/maye/data/diviner/out'
    kernelpath = '/Users/maye/data/spice/diviner'
    codepath = '/Users/maye/Dropbox/src/diviner'
else:
    datapath = os.path.join('/'+hostname, os.environ['USER'])
    outpath = os.path.join(datapath, 'rdr_out')
    kernelpath = os.path.join(datapath, 'kernels')
    codepath = os.path.join(os.environ['HOME'], 'src/diviner')

l1adatapath = os.path.join('/luna1', 'marks/feidata/DIV:opsL1A/data')
rdrdatapath = os.path.join('/'+hostname, 'u/marks/feidata/DIV:opsRdr/data')


### 
### general utilities
###

def get_timestr(fname):
    basename = os.path.basename(fname)
    return basename[:10]


def tstr_to_datetime(tstr):
    dtime = dt.strptime(tstr, '%Y%m%d%H')
    return dtime


def timestamp_to_timestring(val):
    dt = val.to_pydatetime()
    return dt.strftime("%Y%m%d%H")


def fname_to_tindex(fname):
    basename = os.path.basename(fname)
    tstr = basename.split('_')[0]
    return tstr[:8]+' '+tstr[8:]


###
### Tools for data output to tables
###


def get_month_sample_path_from_mode(mode):
    return os.path.join(datapath, 'rdr20_month_samples', mode)


class FileName(object):
    """Managing class for file name attributes """
    def __init__(self, fname):
        super(FileName, self).__init__()
        self.basename = os.path.basename(fname)
        self.dirname = os.path.dirname(fname)
        self.file_id, self.ext = os.path.splitext(self.basename)
        self.timestr= self.file_id.split('_')[0]
        # save everything after the first '_' as rest
        self.rest = self.basename[len(self.timestr):]
        # split of the time elements
        self.year = self.timestr[:4]
        self.month = self.timestr[4:6]
        self.day = self.timestr[6:8]
        # if timestr is not long enough, self.hour will be empty string ''
        self.hour = self.timestr[8:10]
        # set time member
        self.set_time()

    def set_time(self):
        if len(self.timestr) == 8:
            format = '%Y%m%d'
        elif len(self.timestr) == 10:
            format = "%Y%m%d%H"
        else:
            format = '%Y%m%d%H%M'
        self.time = dt.strptime(self.timestr, format)
        self.format = format

    @property
    def previous_dtime(self):
        return self.time - timedelta(hours=1)

    @property
    def previous_timestr(self):
        return self.previous_dtime.strftime(self.format)

    @property
    def previous_fname(self):
        timestr = self.previous_dtime.strftime(self.format)
        return os.path.join(self.dirname, timestr + self.rest)

    def set_previous_hour(self):
        self.time = self.previous_dtime
        self.timestr = self.time.strftime(self.format)
        return self.fname

    @property
    def next_dtime(self):
        return self.time + timedelta(hours=1)

    @property
    def next_timestr(self):
        return self.next_dtime.strftime(self.format)

    @property
    def next_fname(self):
        timestr = self.next_dtime.strftime(self.format)
        return os.path.join(self.dirname, timestr + self.rest)

    def set_next_hour(self):
        self.time = self.next_dtime
        self.timestr = self.time.strftime(self.format)
        return self.fname

    @property
    def fname(self):
        return os.path.join(self.dirname, self.timestr + self.rest)


####
#### Tools for parsing text files of data
####

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
    headerstring = "Q, DATE, UTC, SCLK, SOUNDING, FROM_PKT, PKT_COUNT, SAFING, SAFED, FREEZING, FROZEN, ROLLING, DUMPING, MOVING, TEMP_FAULT,   SC_TIME_SECS,   SC_TIME_SUBS, TICKS_PKT_START, TICKS_AT_SC_TIME, OST_INDEX, EST_INDEX, SST_INDEX, LAST_AZ_CMD, LAST_EL_CMD, FPA_TEMP, FPB_TEMP, BAFFLE_A_TEMP, BAFFLE_B_TEMP, BB_1_TEMP, OBA_1_TEMP, ERROR_TIME, ERROR_ID,  ERROR_DETAIL , ERROR_COUNT, COMMANDS_RECEIVED, COMMANDS_EXECUTED, COMMANDS_REJECTED,    LAST_COMMAND_REC ,      CMD,  REQ_ID , LAST_TIME_COMMAND, LAST_EQX_PREDICTION, HYBRID_TEMP, FPA_TEMP_CYC, FPB_TEMP_CYC, BAFFLE_A_TEMP_CYC, BAFFLE_B_TEMP_CYC, OBA_1_TEMP_CYC, OBA_2_TEMP, BB_1_TEMP_CYC, BB_2_TEMP, SOLAR_TARGET_TEMP, YOKE_TEMP, EL_ACTUATOR_TEMP, AZ_ACTUATOR_TEMP,  MIN_15V, PLU_15V, SOLAR_BASE_TEMP, PLU_5V, "\
    "A1_01, A1_02, A1_03, A1_04, A1_05, A1_06, A1_07, A1_08, A1_09, A1_10, A1_11, A1_12, A1_13, A1_14, A1_15, A1_16, A1_17, A1_18, A1_19, A1_20, A1_21, A2_01, A2_02, A2_03, A2_04, A2_05, A2_06, A2_07, A2_08, A2_09, A2_10, A2_11, A2_12, A2_13, A2_14, A2_15, A2_16, A2_17, A2_18, A2_19, A2_20, A2_21, A3_01, A3_02, A3_03, A3_04, A3_05, A3_06, A3_07, A3_08, A3_09, A3_10, A3_11, A3_12, A3_13, A3_14, A3_15, A3_16, A3_17, A3_18, A3_19, A3_20, A3_21, A4_01, A4_02, A4_03, A4_04, A4_05, A4_06, A4_07, A4_08, A4_09, A4_10, A4_11, A4_12, A4_13, A4_14, A4_15, A4_16, A4_17, A4_18, A4_19, A4_20, A4_21, A5_01, A5_02, A5_03, A5_04, A5_05, A5_06, A5_07, A5_08, A5_09, A5_10, A5_11, A5_12, A5_13, A5_14, A5_15, A5_16, A5_17, A5_18, A5_19, A5_20, A5_21, A6_01, A6_02, A6_03, A6_04, A6_05, A6_06, A6_07, A6_08, A6_09, A6_10, A6_11, A6_12, A6_13, A6_14, A6_15, A6_16, A6_17, A6_18, A6_19, A6_20, A6_21, B1_01, B1_02, B1_03, B1_04, B1_05, B1_06, B1_07, B1_08, B1_09, B1_10, B1_11, B1_12, B1_13, B1_14, B1_15, B1_16, B1_17, B1_18, B1_19, B1_20, B1_21, B2_01, B2_02, B2_03, B2_04, B2_05, B2_06, B2_07, B2_08, B2_09, B2_10, B2_11, B2_12, B2_13, B2_14, B2_15, B2_16, B2_17, B2_18, B2_19, B2_20, B2_21, B3_01, B3_02, B3_03, B3_04, B3_05, B3_06, B3_07, B3_08, B3_09, B3_10, B3_11, B3_12, B3_13, B3_14, B3_15, B3_16, B3_17, B3_18, B3_19, B3_20, B3_21"

    # beware: parse_header_line converts to lower case!
    columns = parse_header_line(headerstring)

    tel1cols = ["a{0}_{1}".format(i, str(j).zfill(2)) for i in range(1,7) for j in range(1,22)]
    tel2cols = ['b{0}_{1}'.format(i, str(j).zfill(2)) for i in range(1,4) for j in range(1,22)]

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
                                    skiprows=self.skip+1,
                                    skipinitialspace=True,
                                    names=self.headers,
                                    nrows=nrows)
        return parse_times(df)



class RDRReader(object):
    """RDRs are usually zipped, so this wrapper takes care of that."""
    datapath = rdrdatapath

    @classmethod
    def from_timestr(cls, timestr):
        fnames = glob.glob(os.path.join(cls.datapath,
                                        timestr + '*_RDR.TAB.zip'))
        return cls(fname=fnames[0])

    def __init__(self, fname, nrows=None):
        super(RDRReader, self).__init__()
        self.fname = fname
        self.get_rdr_headers()

    def find_fnames(self):
        self.fnames = glob.glob(os.path.join(self.datapath,
                                      self.timestr + '*_RDR.TAB.zip'))

    def open(self):
        if self.fname.lower().endswith('.zip'):
            zfile = zipfile.ZipFile(self.fname)
            self.f = zfile.open(zfile.namelist()[0])
        else:
            self.f = open(self.fname)

    def get_rdr_headers(self):
        """Get headers from both ops and PDS RDR files."""
        # skipcounter
        self.open()
        self.no_to_skip = 0
        while True:
            line = self.f.readline()
            self.no_to_skip += 1
            if not line.startswith('# Header'):
                break
        self.headers = parse_header_line(line)
        self.f.close()

    def read_df(self, nrows=None, do_parse_times=True):
        self.open()
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
    times = pd.to_datetime(df.date + ' ' + df.utc, format='%d-%b-%Y %H:%M:%S.%f',
                           utc=False)
    df.set_index(times, inplace=True)
    return df.drop(['date','utc'], axis=1)


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


####
#### tools for parsing binary data of Diviner
####


def parse_descriptor(fpath):
    f = open(fpath)
    lines = f.readlines()
    f.close()
    s = pd.Series(lines)
    s = s.drop(0)
    val = s[1]
    val2 = val.split(' ')
    [i.strip().strip("'") for i in val2]

    def unpack_str(value):
        val2 = value.split(' ')
        t = [i.strip().strip("'") for i in val2]
        return t[0].lower()
    columns = s.map(unpack_str)
    keys = columns.values
    rec_dtype = np.dtype([(key, 'f8') for key in keys])
    return rec_dtype, keys


def get_div247_dtypes():
    if 'darwin' in sys.platform:
        despath = '/Users/maye/data/diviner/div247/div247.des'
    else:
        despath = '/u/paige/maye/src/diviner/div247.des'
    return parse_descriptor(despath)


def get_div38_dtypes():
    if 'darwin' in sys.platform:
        despath = '/Users/maye/data/diviner/div38/div38.des'
    else:
        despath = os.path.join(codepath,'data/div38.des')
    return parse_descriptor(despath)

###
### rdrplus tools
###


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
    storename = os.path.join(dirname, basename + '.h5')
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

    def __init__(self, fname_pattern=None, timestr=None, fnames_only=False):
        self.fnames_only = fnames_only
        if fname_pattern and os.path.exists(fname_pattern):
            if os.path.isfile(fname_pattern):
                self.get_df(fname_pattern)
            elif os.path.isdir(fname_pattern):
                pass

        self.timestr = timestr
        self.current_time = dateparser(timestr)
        self.fname = os.path.join(datapath,
                                  self.current_time.strftime("%Y%m%d%H"))
        self.increment = timedelta(hours=1)

    #def gen_fnames(self, pattern, top):
    #    for path, dirlist, filelist in os.walk(top)

    def get_fnames(self):
        dirname = os.path.dirname(self.fname)
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
    datapath = os.path.join(datapath, 'h5_div247')

    def __init__(self, timestr):
        self.timestr = timestr
        self.fnames = self.get_fnames()
        if len(self.fnames) == 0:
            print("No files found.")
        self.fnames.sort()

    def get_fnames(self):
        return glob.glob(os.path.join(self.datapath, self.timestr[:4] + '*'))

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
    timestr_parser = {4: '%Y', 6: '%Y%m',
                      8: '%Y%m%d', 10: '%Y%m%d%H'}

    #overwrite in child class!!
    this_ext = '...'

    def __init__(self, timestr):
        """timestr is of format yyyymm[dd[hh]], used directly by glob.

        This means, less files are found if the timestr is longer, as it
        is then more restrictive.
        """
        self.timestr = timestr
        self.time = dt.strptime(timestr,
                                self.timestr_parser[len(timestr)])
        self.fnames = self.find_fnames()
        self.fname = FileName(self.fnames[0])
        self.fnames.sort()

    def find_fnames(self):
        "Needs self.datapath to be defined in derived class."
        searchpath = os.path.join(self.datapath, self.timestr[:6], self.timestr + '*')
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
        return time.strftime("%Y%m%d%H"+ self.this_ext)

    def process_one_file(self, f):
        data = np.fromfile(f, dtype=self.rec_dtype)
        return pd.DataFrame(data, columns=self.keys)

    def gen_dataframes(self, n=None):
        # caller actually doesn't allow n=None anyways. FIX?
        if n == None:
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
            dirname = os.path.dirname(self.fnames[0])
            fname = os.path.join(dirname, basename)
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
    datapath = os.path.join(datapath, 'div38')
    rec_dtype, keys = get_div38_dtypes()
    this_ext = '.div38'
    def find_fnames(self):
        return glob.glob(os.path.join(self.datapath, self.timestr + '*'))


class L1ADataFile(object):
    if sys.platform != 'darwin':
        datapath = l1adatapath
    else:
        datapath = '/Users/maye/data/diviner/l1a_data'

    this_ext = '_L1A.TAB'

    @classmethod
    def from_timestr(cls, timestr):
        "Globbing for matching files to timestr and opening first one."
        fnames = glob.glob(os.path.join(cls.datapath,
                                        timestr + '*' + cls.this_ext))
        return cls(fname=fnames[0])

    def __init__(self, fname):
        self.fname = fname
        self.fn_handler = FileName(fname)
        self.header = L1AHeader()

    def parse_tab(self, fname=None):
        if not fname:
            fname = self.fname
        self.df = pd.io.parsers.read_csv(fname,
                                    names=self.header.columns,
                                    na_values='-9999',
                                    skiprows=8,
                                    skipinitialspace=True)

    def parse_times(self):
        self.df = parse_times(self.df)

    def clean(self):
        df = prepare_data(self.df)
        define_sdtype(df)
        self.df = df

    def open_dirty(self):
        self.parse_tab()
        self.parse_times()
        return self.df

    def open(self):
        self.parse_tab()
        self.parse_times()
        self.clean()
        return self.df


def get_clean_l1a(timestr):
    l1afile = L1ADataFile.from_timestr(timestr)
    return l1afile.open()


def get_dirty_l1a(timestr):
    l1afile = L1ADataFile.from_timestr(timestr)
    return l1afile.open_dirty()


def get_raw_l1a(timestr):
    l1afile = L1ADataFile.from_timestr(timestr)
    l1afile.parse_tab()
    return l1afile.df


def open_and_accumulate(fname, minimum_number=3):
    """Open L1A datafile fname and accumulate neighboring data.

    One CAN NOT accumulate cleaned data files, because I rely on the numbering of calib-blocks
    to be unique! Each cleaning operation starts the numbering from 1 again!

    minimum_number controls how many files are attached as one block.
    """
    centerfile = L1ADataFile(fname)
    dataframes = deque()
    dataframes.append(centerfile.open())
    # append previous hours until calib blocks found
    # start with center file:
    fn_handler = FileName(fname)
    while True:
        fn_handler.set_previous_hour()
        f = L1ADataFile(fn_handler.fname)
        logging.debug("Appending {0} on the left.".format(fn_handler.timestr))
        try:
            dataframes.appendleft(f.open_dirty())
        except IOError:
            logging.warning('Could not find previous file {}'.format(fn_handler.fname))
            break
        if any(f.open().is_calib):
            break
    # append next hours until calib blocks found
    # go back to center file name
    fn_handler = FileName(fname)
    while True:
        fn_handler.set_next_hour()
        f = L1ADataFile(fn_handler.fname)
        print("Appending {0} on the right.".format(fn_handler.timestr))
        try:
            dataframes.append(f.open_dirty())
        except IOError:
            logging.warning('Could not find following file {}'.format(fn_handler.fname))
            break
        if any(f.open().is_calib):
            break
    df = prepare_data(pd.concat(list(dataframes)))
    define_sdtype(df)
    return df


class L1ADataPump(DivXDataPump):
    if sys.platform != 'darwin':
        datapath = l1adatapath
    else:
        datapath = '/Users/maye/data/diviner/l1a_data'

    this_ext = '_L1A.TAB'

    def find_fnames(self):
        return glob.glob(os.path.join(self.datapath,
                                      self.timestr + '*' + self.this_ext))

    def clean_final_df(self, df):
        df = prepare_data(df)
        define_sdtype(df)
        return df

    def process_one_file(self, f):
        return read_l1a_data(f)

    def get_3_hour_block(self, fname):
        fnobj = FileName(fname)
        self.fnobj = fnobj
        l = []
        l.append(read_l1a_data(fnobj.previous_fname))
        l.append(read_l1a_data(fnobj.fname))
        l.append(read_l1a_data(fnobj.next_fname))
        df = pd.concat(l)
        return self.clean_final_df(df)

    def get_default(self):
        df = read_l1a_data(self.fnames[0])
        return self.clean_final_df(df)


class RDRxReader(object):
    """docstring for RDRxReader"""
    def __init__(self, tstr):
        super(RDRxReader, self).__init__()
        fname = os.path.join(self.datapath, tstr + self.extension)
        dtypes, keys = parse_descriptor(self.descriptorpath)
        self.df = fname_to_df(fname, dtypes, keys)
        
    def parse_times(self):
        df = self.df
        timecols = [u'yyyy', u'mm', u'dd', u'hh', u'mn', u'ss']
        secs_only = df.ss.astype('int')
        msecs = (df.ss - secs_only).round(3)
        times = pd.to_datetime(df.yyyy.astype('int').astype('str')+
                               df.mm.astype('int').astype('str')+
                               df.dd.astype('int').astype('str')+
                               df.hh.astype('int').astype('str')+
                               df.mn.astype('int').astype('str')+
                               df.ss.astype('int').astype('str')+
                               (msecs).astype('str'), 
                               format='%Y%m%d%H%M%S0.%f',
                               utc=False)
        df.set_index(times, inplace=True)
        self.df = df.drop(timecols, axis=1)
    
    def open(self):
        self.df[self.df == -9999] = np.nan
        self.parse_times()
        df = prepare_data(self.df)
        define_sdtype(df)
        return df
        
    def open_raw(self):
        return self.df

    
class RDRRReader(RDRxReader):
    datapath = '/luna7/marks/rdrr_data'
    descriptorpath = os.path.join(datapath, 'rdrr.des')
    extension = '.rdrr'


class RDRSReader(RDRxReader):
    datapath = '/luna7/marks/rdrs_data'
    descriptorpath = os.path.join(datapath, 'rdrs.des')
    extension = '.rdrs'
