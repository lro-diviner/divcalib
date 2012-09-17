import pandas
import numpy as np

def read_tab(fname):
    "Read tabular diviner data into pandas data frame and return it."

    # pandas parser does not read this file correctly, but loadtxt does.
    # first will get the column headers
    with open(fname) as f:
        headers = f.readline().strip().split()

    print("Found {0} headers: {1}".format(len(headers),headers))

    # use numpy's loadtxt to read the tabulated file into a numpy array
    ndata = np.loadtxt(fname, skiprows=1)

    # pandas DataFrame constructor takes numpy arrays
    dataframe = pandas.DataFrame(ndata)

    # replace numbered columns with pre-read ones
    dataframe.columns = headers

    return dataframe

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

    

    
