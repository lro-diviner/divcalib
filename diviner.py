from matplotlib import pyplot as plt
import pandas
import numpy as np
from dateutil.parser import parse

def get_headers_pprint(fname):
    with open(fname) as f:
        headers = f.readline().strip().split()
    return headers
    
def get_headers_pds(fname):
    with open(fname) as f:
        for i in range(3):
            f.readline()
        # [1:] pops off the first '#' character from the line
        headers = f.readline().strip().split()[1:]
    # previous strip only removes whitespace, now strip off comma
    return [i.rstrip(',') for i in headers]
    
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

def divplot(df, col, ch_nr=1, det=11):
    newdf = df[df.c==ch_nr]
    plt.plot(newdf[col][newdf.det==det])


