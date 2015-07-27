import pandas as pd
import numpy as np
import .divconstants as c
from scipy import ndimage as nd
from datetime import datetime

###
### general tools for data preparation
###


def format_time(intime):
    t = intime.to_datetime()
    s = t.strftime('%Y-%m-%d %H:%M:%S.%f')
    tail = s[-7:]
    f = round(float(tail), 3)
    return pd.Timestamp(s[:-7] + str(f)[1:])


def generate_date_index(dataframe):
    """Parse date fields/columns with pandas date converter parsers.

    Parse the date columns and create a date index from it
    In: pandas dataframe read in from diviner div38 data
    Out: DatetimeIndex
    """
    d = dataframe
    try:
        d.second = np.round(d.second * 1000) / 1000
        date_index = pd.io.date_converters.parse_all_fields(
            d.year, d.month, d.date, d.hour, d.minute, d.second)
    except AttributeError:
        d.ss = np.round(d.ss * 1000) / 1000
        date_index = pd.io.date_converters.parse_all_fields(
            d.yyyy, d.mm, d.dd, d.hh, d.mn, d.ss)
    return date_index


def index_by_time(df, drop_dates=True):
    "must return a new df because the use of drop"
    df.index = generate_date_index(df)
    # force 3-digit precision on time stamp
    # newdf.index = (pd.Series(newdf.index)).map(format_time)
    if drop_dates:
        try:
            cols_to_drop = ['year', 'month', 'date',
                            'hour', 'minute', 'second']
            df.drop(cols_to_drop, axis=1, inplace=True)
        except ValueError:
            cols_to_drop = ['yyyy', 'mm', 'dd', 'hh', 'mn', 'ss']
            df.drop(cols_to_drop, axis=1, inplace=True)
    return df


def cutoff_msec(ts):
    dtime = ts.to_datetime()
    return pd.Timestamp(datetime(dtime.year, dtime.month, dtime.day,
                                 dtime.hour, dtime.minute, dtime.second))


def parse_divdata_times(df, drop_dates=True):
    format = "%Y%m%d%H%M"
    timecols = 'year month date hour minute'.split()
    subdf = df[timecols].astype('int')
    seconds = pd.Series(df.second*1e9, dtype='timedelta64[ns]')
    up_to_min = pd.to_datetime(subdf.year*int(1e8) + subdf.month*int(1e6) +
                               subdf.date*int(1e4) + subdf.hour*int(1e2) +
                               subdf.minute, format=format, utc=False)
    times = up_to_min + seconds
    index = pd.DatetimeIndex(times)
    ts = pd.TimeSeries(index.map(cutoff_msec))
    ms = pd.Series(index.microsecond.round(-3)*1000, dtype='timedelta64[ns]')
    df.index = ts + ms
    return df.drop(timecols+['second'], axis=1) if drop_dates else df


def prepare_data(df_in):
    """Declare NaN value and pad nan data for some."""
    # df = index_by_time(df_in)
    # df[df == -9999.0] = nan
    if not 'last_el_cmd' in df_in.columns:
        df_in.rename(columns={'el_cmd': 'last_el_cmd',
                              'az_cmd': 'last_az_cmd'},
                     inplace=True)
    df_in.last_el_cmd.replace([np.nan], inplace=True)
    df_in.last_az_cmd.replace([np.nan], inplace=True)
    df_in.moving.replace([np.nan], inplace=True)
    return df_in


def get_sv_selector(df):
    "Create dataframe selector for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.SV_AZ_MIN) & \
           (df.last_az_cmd <= c.SV_AZ_MAX) & \
           (df.last_el_cmd >= c.SV_EL_MIN) & \
           (df.last_el_cmd <= c.SV_EL_MAX)


def get_bb_selector(df):
    "Create dataframe selector for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.BB_AZ_MIN) & \
           (df.last_az_cmd <= c.BB_AZ_MAX) & \
           (df.last_el_cmd >= c.BB_EL_MIN) & \
           (df.last_el_cmd <= c.BB_EL_MAX)


def get_st_selector(df):
    "Create dataframe selector for pointing limits of divconstants 'c' file"
    return (df.last_az_cmd >= c.ST_AZ_MIN) & \
           (df.last_az_cmd <= c.ST_AZ_MAX) & \
           (df.last_el_cmd >= c.ST_EL_MIN) & \
           (df.last_el_cmd <= c.ST_EL_MAX)


def get_stowed_selector(df):
    return (df.last_az_cmd == 0) & (df.last_el_cmd == 0)


def define_sdtype(df):
    df['sdtype'] = 0
    df.loc[get_sv_selector(df), 'sdtype'] = 1
    df.loc[get_bb_selector(df), 'sdtype'] = 2
    df.loc[get_st_selector(df), 'sdtype'] = 3
    df.loc[get_stowed_selector(df), 'sdtype'] = -2
    # the following defines the sequential list of calibration blocks inside
    # the dataframe. nd.label provides an ID for each sequential part where
    # the given condition is true.
    # this still includes the moving areas, because i want the sv and bbv
    # attached to each other to deal with them later as a separate calibration
    # block
    # DECISION: block labels contain moving data as well
    # WARNING: But not all moving data is contained in block labels!
    # The end of calib block has pointing commands set to nadir.
    # below defined "is_xxx" do NOT contain moving data.
    df['calib_block_labels'] = nd.label((df.sdtype == 1) |
                                        (df.sdtype == 2) |
                                        (df.sdtype == 3))[0]
    # this resets data from sdtypes >0 above that is still 'moving' to be
    # sdtype=-1 (i.e. 'moving', defined by me)
    # doing this *after* the calib block labels are defined above ensures that
    # the spaceviews and bb/st views are connected in one calib block.
    # But resetting moving data now to -1 ensures that I don't get empty moving
    #  data marked as bb_block_labels
    df.loc[df.moving == 1, 'sdtype'] = -1

    df['space_block_labels'] = nd.label(df.sdtype == 1)[0]
    df['bb_block_labels'] = nd.label(df.sdtype == 2)[0]
    df['st_block_labels'] = nd.label(df.sdtype == 3)[0]

    # now I don't need to check for moving anymore, the sdtypes are clean
    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview'] = (df.sdtype == 2)
    df['is_stview'] = (df.sdtype == 3)
    df['is_moving'] = (df.sdtype == -1)
    df['is_stowed'] = (df.sdtype == -2)
    df['is_calib'] = df.is_spaceview | df.is_bbview | df.is_stview

    # this does the same as above labeling, albeit here the blocks are numbered
    # individually. Not sure I will need it but might come in handy.
