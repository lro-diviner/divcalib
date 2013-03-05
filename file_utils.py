# -*- coding: utf-8 -*-
# file utilities for Diviner
import pandas as pd
import numpy as np
import sys
import glob
from dateutil.parser import parse as dateparser
from scipy import ndimage as nd
import divconstants as c
import os
from datetime import timedelta
import csv
from plot_utils import ProgressBar

if sys.platform == 'darwin':
    datapath = '/Users/maye/data/diviner'
else:
    datapath = '/raid1/maye/'

####
#### Tools for parsing text files of data
####

def split_by_n(seq, n):
    while seq:
        yield seq[:n]
        seq = seq[n:]

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
    return [i.strip() for i in newline]
    
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

def get_headers_pds(fname):
    """Get headers from PDS RDR files.
    
    >>> fname = '/Users/maye/data/diviner/201204090110_RDR.TAB'
    >>> headers = get_headers_pds(fname)
    >>> headers[:7]
    ['utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk']
    """
    with open(fname) as f:
        for i in range(3):
            f.readline()
        headers = parse_header_line(f.readline())
    return headers
 
def read_pprint(fname):
    """Read tabular diviner data into pandas data frame and return it.
    
    Lower level function. Use read_div_data which calls this as appropriate.    
    """

    # pandas parser does not read this file correctly, but loadtxt does.
    # first will get the column headers

    headers = get_headers_pprint(fname)
    print("Found {0} headers: {1}".format(len(headers),headers))

    # use numpy's loadtxt to read the tabulated file into a numpy array
    ndata = np.loadtxt(fname, skiprows=1)
    dataframe = pd.DataFrame(ndata)
    dataframe.columns = headers
    dataframe.sort('jdate',inplace=True)
    return dataframe

def read_pds(fname,nrows=None):
    """Read tabular files from the PDS depository.
    
    Lower level function. Use read_div_data which calls this as appropriate.
    """
    headers = get_headers_pds(fname)
    with open(fname) as f:
        dialect = csv.Sniffer().sniff(f.read(2048))
    return pd.io.parsers.read_csv(fname,
                                      dialect = dialect,
                                      comment='#',
                                      names=headers, 
                                      na_values=['-9999.0'], 
                                      skiprows=4, 
                                      nrows=nrows,
                                      parse_dates=[[0,1]],
                                      index_col=0,
                                      )
    
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

def read_div_data(fname, **kwargs):
    with open(fname) as f:
        line = f.readline()
        if any(['dlre_edr.c' in line, 'Header' in line]):
            return read_pds(fname, **kwargs)
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
    rec_dtype = np.dtype([(key,'f8') for key in keys])
    return rec_dtype,keys

def get_div247_dtypes():
    if 'darwin' in sys.platform:
        despath = '/Users/maye/data/diviner/div247/div247.des'
    else:
        despath = 'div247.des'
    return parse_descriptor(despath)

def get_div38_dtypes():
    if 'darwin' in sys.platform:
        despath = '/Users/maye/data/diviner/div38/div38.des'
    else:
        despath = '/u/paige/maye/raid/div38/div38.des'
    return parse_descriptor(despath)
    
###
### rdrplus tools
###

def read_rdrplus(fpath,nrows):
    with open(fpath) as f:
        line = f.readline()
        headers = parse_header_line(line)
        
    return pd.io.parsers.read_csv(fpath, names=headers, na_values=['-9999'],
                                      skiprows=1, nrows=nrows)


###
### general tools for data preparation
###

def generate_date_index(dataframe):
    """Parse date fields/columns with pandas date converter parsers.

    Parse the date columns and create a date index from it
    In: pandas dataframe read in from diviner div38 data
    Out: DatetimeIndex
    """
    d = dataframe
    di = pd.io.date_converters.parse_all_fields(
        d.year, d.month, d.date, d.hour, d.minute, d.second)
    return di

def index_by_time(df, drop_dates=True):
    "must return a new df because the use of drop"
    newdf = df.set_index(generate_date_index(df))
    if drop_dates:
        cols_to_drop = ['year','month','date','hour','minute','second']
        newdf = newdf.drop(cols_to_drop, axis=1)
    return newdf

def prepare_data(df_in):
    """Declare NaN value and pad nan data for some."""
    nan = np.nan
    df = index_by_time(df_in)
    df[df==-9999.0] = nan
    df.last_el_cmd.replace(nan,inplace=True)
    df.last_az_cmd.replace(nan,inplace=True)
    df.moving.replace(nan,inplace=True)
    return df

def get_sv_selector(df):
    "Create dataframe selecotr for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.SV_AZ_MIN) & (df.last_az_cmd <= c.SV_AZ_MAX) & \
           (df.last_el_cmd >= c.SV_EL_MIN) & (df.last_el_cmd <= c.SV_EL_MAX)

def get_bb_selector(df):
    "Create dataframe selecotr for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.BB_AZ_MIN) & (df.last_az_cmd <= c.BB_AZ_MAX) & \
           (df.last_el_cmd >= c.BB_EL_MIN) & (df.last_el_cmd <= c.BB_EL_MAX)
    
def get_st_selector(df):
    "Create dataframe selecotr for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.ST_AZ_MIN) & (df.last_az_cmd <= c.ST_AZ_MAX) & \
           (df.last_el_cmd >= c.ST_EL_MIN) & (df.last_el_cmd <= c.ST_EL_MAX)

def get_stowed_selector(df):
    return (df.last_az_cmd == 0) & (df.last_el_cmd == 0)
    
def define_sdtype(df):
    df['sdtype'] = 0
    df.sdtype[get_sv_selector(df)] = 1
    df.sdtype[get_bb_selector(df)] = 2
    df.sdtype[get_st_selector(df)] = 3
    df.sdtype[get_stowed_selector(df)] = -2
    # the following defines the sequential list of calibration blocks inside
    # the dataframe. nd.label provides an ID for each sequential part where
    # the given condition is true.
    # this still includes the moving areas, because i want the sv and bbv
    # attached to each other to deal with them later as a separate calibration
    # block
    # DECISION: block labels contain moving data as well
    # below defined "is_xxx" do NOT contain moving data.
    df['calib_block_labels'] = nd.label( (df.sdtype==1) | (df.sdtype==2) | (df.sdtype==3))[0]
    df['sv_block_labels'] = nd.label( df.sdtype==1 )[0]
    df['bb_block_labels'] = nd.label( df.sdtype==2 )[0]
    df['st_block_labels'] = nd.label( df.sdtype==3 )[0]
    
    # this resets data from sdtypes >0 above that is still 'moving' to be 
    # sdtype=-1 (i.e. 'moving', defined by me)
    df.sdtype[df.moving==1] = -1
    
    # now I don't need to check for moving anymore, the sdtypes are clean
    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview']    = (df.sdtype == 2)
    df['is_stview']    = (df.sdtype == 3)
    df['is_moving']    = (df.sdtype == -1)
    df['is_stowed']    = (df.sdtype == -2)
    df['is_calib'] = df.is_spaceview | df.is_bbview | df.is_stview

    # this does the same as above labeling, albeit here the blocks are numbered
    # individually. Not sure I will need it but might come in handy.

def fname_to_df(fname,rec_dtype,keys):
    with open(fname) as f:
        data = np.fromfile(f,dtype=rec_dtype)
    df = pd.DataFrame(data,columns=keys)
    return df

def folder_to_df(folder, top_end=None, verbose=False):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder+'/*.div247')
    fnames.sort()
    if not top_end:
        top_end = len(fnames)
    dfall = pd.DataFrame()
    olddf = None
    for i,fname in enumerate(fnames[:top_end]):
        if verbose:
            print round(float(i)*100/top_end,1),'%'
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        if olddf is not None:
            for s in df.filter(regex='_labels'):
                df[s] += olddf[s].max()
        olddf = df.copy()
        dfall = pd.concat([dfall,df])
    to_store = dfall[dfall.calib_block_labels>0]
    return to_store
   
def get_storename(folder):
    path = os.path.realpath(folder)
    dirname = '/raid1/maye/data/h5_div247'
    basename = os.path.basename(path)
    storename = os.path.join(dirname,basename+'.h5')
    return storename
     
def folder_to_store(folder):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder+'/*.div247')
    if not fnames:
        print "Found no files."
        return
    fnames.sort()
    # opening store in overwrite-mode
    storename = get_storename(folder)
    print storename
    store = pd.HDFStore(storename,mode='w')
    nfiles = len(fnames)
    olddf = None
    cols = ['calib_block_labels','sv_block_labels','bb_block_labels',
            'st_block_labels','is_spaceview', 'is_bbview', 'is_stview',
            'is_moving', 'is_stowed', 'is_calib']
    for i,fname in enumerate(fnames):
        print round(float(i)*100/nfiles,1),'%'
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        to_store = df[df.calib_block_labels>0]
        if len(to_store) == 0:
            continue
        if olddf is not None:
            for s in to_store.filter(regex='_labels'):
                to_store[s] += olddf[s].max()
        olddf = to_store.copy()
        try:
            store.append('df',to_store, data_columns=cols )
        except Exception as e:
            store.close()
            print 'at',fname
            print 'something went wrong at appending into store.'
            print e
            return
    print "Done."
    store.close()


class DataPump(object):
    """class to provide Diviner data in different ways."""
    rec_dtype, keys  = get_div247_dtypes()
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
    def get_df(self,fname):
        self.fname = fname
        self.get_fnames()
        self.open_and_process()
        return self.df
    def get_next(self):
        self.fname = self.fnames[self.index+1]
        self.index+=1
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
        return glob.glob(os.path.join(self.datapath, self.timestr[:4]+'*'))
        
    def store_generator(self):
        for fname in self.fnames:
            yield pd.HDFStore(fname)
    
    def fname_generator(self):
        for fname in self.fnames:
            yield fname
        
    def df_generator(self):
        for fname in self.fnames:
            yield self.get_df_from_h5(fname)                


class Div247DataPump(object):
    "Class to stream div247 data."
    
    datapath = os.path.join(datapath, "div247")
    rec_dtype, keys  = get_div247_dtypes()
    def __init__(self, timestr):
        self.timestr = timestr
        self.fnames = self.find_fnames()
        if len(self.fnames) == 0:
            print("No files found.")
        self.fnames.sort()

    def find_fnames(self):
        return glob.glob(os.path.join(self.datapath, self.timestr[:6], 
                                      self.timestr+'*'))
    
    def gen_fnames(self):
        for fname in self.fnames:
            yield fname

    def gen_open(self):
        for fname in self.fnames:
            yield open(fname)
            
    def gen_dataframes(self, n=None):
        if n==None:
            n = len(self.fnames)
        pbar = ProgressBar(n)
        openfiles = self.gen_open()
        i = 0
        while i < n:
            data = np.fromfile(openfiles.next(), dtype=self.rec_dtype)
            df = pd.DataFrame(data, columns=self.keys)
            pbar.animate(i+1)
            yield df
            i += 1
            
    def clean_final_df(self, df):
        "need to wait until final df before defining sdtypes."
        df = prepare_data(df)
        define_sdtype(df)
        return df
        
    def get_n_hours(self, n):
        df = pd.concat(self.gen_dataframes(n))
        return self.clean_final_df(df)