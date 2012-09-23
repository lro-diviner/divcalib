from matplotlib import pyplot as plt
import pandas
import numpy as np
from dateutil.parser import parse

def parse_header_line(line):
    """Parse header lines.
    
    >>> s = ' a   b  c    '
    >>> parse_header_line(s)
    ['a', 'b', 'c']
    >>> s = '  a, b  ,   c '
    >>> parse_header_line(s)
    ['a', 'b', 'c']
    """
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
    >>> headers = get_headers_pds_rdr(fname)
    >>> headers[:7]
    ['utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk']
    """
    with open(fname) as f:
        for i in range(3):
            f.readline()
        headers = parse_header_line(f.readline())
        if '#' in headers[0]:
            headers.pop(0)
    # previous strip only removes whitespace, now strip off comma
    return headers
    
def read_pprint(fname):
    "Read tabular diviner data into pandas data frame and return it."

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
    "Read tabular files from the PDS depository."
    headers = get_headers_pds(fname)
    return pandas.io.parsers.read_csv(fname, names=headers, 
                                      skiprows=4, nrows=nrows)
    
def make_date_index(dataframe):
    """Parse date fields/columns with pandas date converter parsers.

    Parse the date columns and create a date index from it
    In: pandas dataframe read in from diviner div38 data
    Out: DatetimeIndex
    """
    d = dataframe
    di = pandas.io.date_converters.parse_all_fields(
        d.year, d.month, d.date, d.hour, d.minute, d.second)
    return di

def divplot(df, col, c=1, det=11):
    plt.plot(df[col][(df.c==ch_nr) & (df.det==det)])
    
    


