# -*- coding: utf-8 -*-
from matplotlib import pyplot as plt
from matplotlib.pylab import gcf
import pandas
import numpy as np
from dateutil.parser import parse as dateparser
from multiprocessing import Pool
import csv
import sys
import os
import glob
import fnmatch
from datetime import timedelta

if sys.platform == 'darwin':
    datapath = '/Users/maye/data/diviner'
else:
    datapath = '/luna1/maye/data'

def save_to_www(fname, **kwargs):
    gcf().savefig("/u/paige/maye/WWW/calib/"+fname,**kwargs)
    
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
    dataframe = pandas.DataFrame(ndata)
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
    return pandas.io.parsers.read_csv(fname,
                                      dialect = dialect,
                                      comment='#',
                                      names=headers, 
                                      na_values=['-9999.0'], 
                                      skiprows=4, 
                                      nrows=nrows,
                                      parse_dates=[[0,1]],
                                      index_col=0,
                                      )
    
def read_div_data(fname, **kwargs):
    with open(fname) as f:
        line = f.readline()
        if any(['dlre_edr.c' in line, 'Header' in line]):
            return read_pds(fname, **kwargs)
        elif fname.endswith('.h5'):
            return get_df_from_h5(fname)
        else:
            return read_pprint(fname)

def generate_date_index(dataframe):
    """Parse date fields/columns with pandas date converter parsers.

    Parse the date columns and create a date index from it
    In: pandas dataframe read in from diviner div38 data
    Out: DatetimeIndex
    """
    d = dataframe
    di = pandas.io.date_converters.parse_all_fields(
        d.year, d.month, d.date, d.hour, d.minute, d.second)
    return di

def index_by_time(df, drop_dates=True):
    "must return a new df because the use of drop"
    newdf = df.set_index(generate_date_index(df))
    if drop_dates:
        cols_to_drop = ['year','month','date','hour','minute','second']
        newdf = newdf.drop(cols_to_drop, axis=1)
    return newdf
    
def divplot(df, col, c=1, det=11):
    plt.plot(df[col][(df.c==c) & (df.det==det)])
    
    
def read_rdrplus(fpath,nrows):
    with open(fpath) as f:
        line = f.readline()
        headers = parse_header_line(line)
        
    return pandas.io.parsers.read_csv(fpath, names=headers, na_values=['-9999'],
                                      skiprows=1, nrows=nrows)

def get_df_from_h5(fname):
    """Provide df from h5 file."""
    store = pandas.HDFStore(fname)
    df = store[store.keys()[0]]
    store.close()
    return df

def get_channel_mean(df, col_str, channel):
    "The dataframe has to contain c and jdate for this to work."
    return df.groupby(['c',df.index])[col_str].mean()[channel]
    
def get_channel_std(df, col_str, channel):
    "The dataframe has to contain c and jdate for this to work."
    return df.groupby(['c',df.index])[col_str].std()[channel]

class DataPump(object):
    """class to provide Diviner data in different ways."""
    def __init__(self, timestr):
        self.timestr = timestr
        self.time = dateparser(timestr)
        self.fname = os.path.join(datapath,
                                  self.time.strftime("%Y%m%d%H"))
        self.increment = timedelta(hours=1)
    def next(self, fname_only=False):
        current_fname = self.fname
        found_path = glob.glob(current_fname + '*')[0]
        if not fname_only:
            df = read_div_data(found_path)
        self.update_time()
        return df if not fname_only else current_fname

    def update_time(self):
        "Can't be used the first time, because then I don't want to increase."
        self.time += self.increment
        self.fname = os.path.join(datapath,
                                  self.time.strftime("%Y%m%d%H") + '.h5')
    
    def __repr__(self):
        return self.time.isoformat()

def gen_fnames(pattern, top):
    for path, dirlist, filelist in os.walk(top):
        for name in fnmatch.filter(filelist, pattern):
            yield os.path.join(path, name)
    

if __name__ == '__main__':
    fnames = gen_fnames('2011*.div247',datapath)
    print list(fnames)




    