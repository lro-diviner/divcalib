# -*- coding: utf-8 -*-
# file utilities for Diviner
from __future__ import print_function, division
import pandas as pd
import numpy as np
import sys
import glob
from dateutil.parser import parse as dateparser
import os
from datetime import timedelta
from datetime import datetime as dt
from diviner.data_prep import define_sdtype, prepare_data, index_by_time

# from plot_utils import ProgressBar
import zipfile

if sys.platform == 'darwin':
    datapath = '/Users/maye/data/diviner'
    outpath = '/Users/maye/data/diviner/out'
    kernelpath = '/Users/maye/data/spice/diviner'
    codepath = '/Users/maye/Dropbox/src/diviner'
else:
    datapath = '/raid1/maye'
    outpath = '/raid1/maye/rdr_out'
    kernelpath = '/raid1/maye/kernels'
    codepath = '/u/paige/maye/src/diviner'

l1adatapath = '/raid1/u/marks/feidata/DIV:opsL1A/data'
rdrdatapath = '/raid1/u/marks/feidata/DIV:opsRdr/data'


###
### Tools for data output to tables
###


def get_month_sample_path_from_mode(mode):
    return os.path.join(datapath, 'rdr20_month_samples', mode)
    
    
def read_dlre_fmt():
    with open(os.path.join(datapath, 'dlre_rdr.fmt')) as f:
        lines = f.readlines()
    
    def parse_string(s):
        s = s[:-2]
        return int(s[s.find('=')+2:])
    
    bytes = []
    start_bytes = []
    for line in lines:
        if 'BYTES' in line:
            bytes.append(parse_string(line))
        elif 'START_BYTE' in line:
            start_bytes.append(parse_string(line)-1)
    
    return start_bytes, bytes
    
    
def prepare_write(Tb):
    Tb['year'] = Tb.index.year
    Tb['month'] = Tb.index.month
    Tb['day'] = Tb.index.day
    Tb['hour'] = Tb.index.hour
    Tb['minute'] = Tb.index.minute
    
    dtimes = Tb.index.to_pydatetime()
    
    
    Tb['second'] = ['.'.join([str(dt.second),str(dt.microsecond)]) for dt in dtimes]
    cols = Tb.columns
    time_cols = cols[-6:]
    dets = cols[:-6]
    new_cols = pd.Index(time_cols.tolist() + dets.tolist())
    return Tb.reindex(columns=new_cols)


class FileName(object):
    """Managing class for file name attributes """
    def __init__(self, fname):
        super(FileName, self).__init__()
        self.basename = os.path.basename(fname)
        self.dirname = os.path.dirname(fname)
        self.timestr= self.basename.split('_')[0]
        # save everything after the first '_' as rest
        self.rest = self.basename[self.basename.find('_'):]
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
    
    def get_previous_hour_dtime(self):
        return self.time - timedelta(hours=1)
        
    def get_previous_hour(self):
        dtime = self.get_previous_hour_dtime()
        return dtime.strftime(self.format)
        
    def get_previous_hour_fname(self):
        dtime = self.get_previous_hour_dtime()
        timestr = dtime.strftime(self.format)
        return os.path.join(self.dirname, timestr + self.rest)
        
    def set_previous_hour(self):
        newtime = self.get_previous_hour_dtime()
        self.time = newtime
        self.timestr = newtime.strftime(self.format)
        return self.fname
        
    def get_next_hour_dtime(self):
        return self.time + timedelta(hours=1)
        
    def get_next_hour_fname(self):
        dtime = self.get_next_hour_dtime()
        timestr = dtime.strftime(self.format)
        return os.path.join(self.dirname, timestr + self.rest)
        
    def set_next_hour(self):
        newtime = self.get_next_hour_dtime()
        self.time = newtime
        self.timestr = newtime.strftime(self.format)
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
                                             

def get_l1a_headers(fname):
    with open(fname) as f:
        for _ in range(6):
            f.readline()
        headers = parse_header_line(f.readline())
    return headers


def parse_times(df):
    format = '%d-%b-%Y %H:%M:%S.%f'

    parse = lambda x: dt.strptime(x, format)
    date_utc = df.date + ' ' + df.utc
    time = date_utc.map(parse)

    df.set_index(time, inplace=True)
    # dropped date and utc before, but i think it's simpler
    # to just keep it
    # return df.drop(['date','utc'], axis=1)
    return df

# this is currently broken so i take it out for now.    
# def parse_times(df):
#     format = format='%d-%b-%Y %H:%M:%S.%f'
#     # this is buggy, but was faster. replace it when fixed.
#     times = pd.to_datetime(df.date + ' ' + df.utc, format='%d-%b-%Y %H:%M:%S.%f')
#     
#     df.set_index(times, inplace=True)
#     return df.drop(['date','utc'], axis=1)
    

def read_l1a_data(fname, nrows=None):
    headers = get_l1a_headers(fname)
    df = pd.io.parsers.read_csv(fname,
                                names=headers,
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
    dirname = '/raid1/maye/data/h5_div247'
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
    cols = ['calib_block_labels', 'sv_block_labels', 'bb_block_labels',
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
    datapath = '/raid1/maye/data/div247/'

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

    def __init__(self, timestr):
        """timestr is of format yyyymm[dd[hh]], used directly by glob.

        This means, less files are found if the timestr is longer, as it
        is then more restrictive.
        """
        self.timestr = timestr
        self.time = dt.strptime(timestr,
                                self.timestr_parser[len(timestr)])
        self.fnames = self.find_fnames()
        if len(self.fnames) == 0:
            print("No files found.")
        self.fnames.sort()

    def find_fnames(self):
        "Needs self.datapath to be defined in derived class."
        return glob.glob(os.path.join(self.datapath, self.timestr[:6],
                                      self.timestr + '*'))

    def gen_open(self):
        for fname in self.fnames:
            self.current_fname = fname
            print(fname)
            yield open(fname)

    def get_fname_from_time(self, time):
        return time.strftime("%Y%m%d%H.div247")

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

    def get_n_hours(self, n):
        #broken
        print("Broken!!!")
        return
        df = pd.concat(self.gen_dataframes(n))
        return self.clean_final_df(df)

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

    def read_hour(self, hour):
        pass

    def add_next_hour(self):
        pass

    def get_one_hour(self):
        print("Broken!!")
        return
        for df in self.gen_dataframes():
            yield self.clean_final_df(df)


class L1ADataPump(DivXDataPump):
    datapath = l1adatapath
    
    def find_fnames(self):
        return glob.glob(os.path.join(self.datapath,
                                      self.timestr + '*_L1A.TAB'))
    
    def clean_final_df(self,df):
        df.last_el_cmd.replace(np.nan, inplace=True)
        df.last_az_cmd.replace(np.nan, inplace=True)
        df.moving.replace(np.nan, inplace=True)
        define_sdtype(df)
        return df
        
    def process_one_file(self, f):
        return read_l1a_data(f)
        
    def get_3_hour_block(self, fname):
        fnobj = FileName(fname)
        self.fnobj = fnobj
        l = []
        l.append(read_l1a_data(fnobj.get_previous_hour_fname()))
        l.append(read_l1a_data(fnobj.fname))
        l.append(read_l1a_data(fnobj.get_next_hour_fname()))
        df = pd.concat(l)
        return self.clean_final_df(df)
            
    def get_default(self):
        df = read_l1a_data(self.fnames[0])
        return self.clean_final_df(df) 
                                    

class Div247DataPump(DivXDataPump):
    "Class to stream div247 data."
    datapath = os.path.join(datapath, "div247")
    rec_dtype, keys = get_div247_dtypes()
    
    def clean_final_df(self, df_in):
        """Declare NaN value and pad nan data for some."""
        df = index_by_time(df_in)
        df[df == -9999.0] = np.nan
        df.last_el_cmd.replace(np.nan, inplace=True)
        df.last_az_cmd.replace(np.nan, inplace=True)
        df.moving.replace(np.nan, inplace=True)
        define_sdtype(df)
        return df
        

class Div38DataPump(DivXDataPump):
    datapath = os.path.join(datapath, 'div38')
    rec_dtype, keys = get_div38_dtypes()

    def find_fnames(self):
        return glob.glob(os.path.join(self.datapath, self.timestr + '*'))
