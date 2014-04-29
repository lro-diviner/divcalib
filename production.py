from __future__ import division, print_function
from diviner import calib
from diviner import file_utils as fu
from joblib import Parallel, delayed
import pandas as pd
import diviner
import logging
import os
import sys
import rdrx
import diviner


formats = pd.read_csv(os.path.join(diviner.__path__[0],
                      'data',
                      'joined_format_file.csv'))

cols_no_melt = [i for i in formats.colname if i in rdrx.no_melt]
cols_skip = 'c det tb radiance'.split()
cols_to_melt = set(formats.colname) - set(cols_no_melt) - set(cols_skip)
cols_to_melt = [i for i in cols_to_melt if i in rdrx.to_melt]


def read_and_clean(fname):
    with open(fname) as f:
        tstrings = f.readlines()
    return [i.strip() for i in tstrings]


def beta_0_circular_orbit():
    fname = os.path.join(diviner.__path__[0],
                         'data',
                         '2009082321_2009092002.txt')
    return read_and_clean(fname)


def beta_0_elliptical_orbit():
    fname = os.path.join(diviner.__path__[0],
                         'data',
                         '2012022408_2012032323.txt')

    return read_and_clean(fname)


def beta_90_circular_orbit():
    fname = os.path.join(diviner.__path__[0],
                         'data',
                         '2010120102_2010122712.txt')
    return read_and_clean(fname)


def beta_90_elliptical_orbit():
    fname = os.path.join(diviner.__path__[0],
                         'data',
                         '2012061211_2012062602.txt')
    return read_and_clean(fname)


def get_tb_savename(savedir, tstr):
    return os.path.join(savedir, tstr + '_tb.hdf')


def get_rad_savename(savedir, tstr):
    return os.path.join(savedir, tstr + '_radiance.hdf')


def get_example_data():
    tstr = '2013031707'
    df = fu.get_clean_l1a(tstr)
    rdr2 = calib.Calibrator(df)
    rdr2.calibrate()
    rdr1 = rdrx.RDRR(tstr)
    return rdr1, rdr2


def calibrate_fname(tstr, savedir):
    print(tstr)
    sys.stdout.flush()
    df = fu.open_and_accumulate(tstr=tstr)
    try:
        if len(df) == 0:
            return
    except TypeError:
        return
    rdr2 = calib.Calibrator(df, fix_noise=True)
    rdr2.calibrate()
    rdr2.Tb.to_hdf(get_tb_savename(savedir, tstr), 'df')
    rdr2.abs_radiance.to_hdf(get_rad_savename(savedir, tstr), 'df')


def only_calibrate():
    logging.basicConfig(filename='divcalib_only_calibrate.log',
                        format='%(asctime)s %(message)s',
                        level=logging.INFO)

    with open('/u/paige/maye/src/diviner/data/2010120102_2010122712.txt') as f:
        timestrings = f.readlines()

    savedir = '/raid1/maye/rdr_out/only_calibrate'
    Parallel(n_jobs=8,
             verbose=5)(delayed(calibrate_fname)
                        (tstr.strip(), savedir) for tstr in timestrings)


def melt_and_merge_rdr1(rdrxfile, c):
    """Melt and merge required columns out of RDRx file.

    Above defined formats file defines what columns are required for this
    production function.
    """
    # first get the columns that do not need melting
    no_melts = rdrxfile.df[cols_no_melt]

    # now go through each column of format that needs melting and save it in
    # a temp. container
    container = []
    for col in cols_to_melt:
        container.append(rdrxfile.get_molten_col(col, c))

    # now merge each entry of the container, until it's empty (IndexError)
    mergecols = 'index det'.split()
    res = None
    while True:
        try:
            if res is None:
                res = container.pop()
            res = res.merge(container.pop(),
                            left_on=mergecols,
                            right_on=mergecols)
        except IndexError:
            break
    final = pd.merge(no_melts.reset_index(),
                     res,
                     left_on='index',
                     right_on='index')
    return final


def merge_rdr1_rdr2(tstr):
    rdr1 = rdrx.RDRR(tstr)
    tb = pd.read_hdf(get_tb_savename(savedir, tstr), 'df')
    rad = pd.read_hdf(get_rad_savename(savedir, tstr), 'df')


def prepare_rdr2_write(df):
    pass


def write_rdr2(df, formatter, fname):
    formatter = Formatter()

    # read in old RDR
    print("Reading old RDR file.")
    rdr = fu.RDRReader('/u/paige/maye/rdr_data/' + timestr + '_RDR.TAB.zip')
    df = rdr.read_df(do_parse_times=False)
    print("Done reading.")

    # add cphase and roi
    df['cphase'] = 123.45678
    df['roi'] = 1234

    # adapt to new format
    # drop the old quality flags
    df = df.drop(['qca', 'qge', 'qmi'], axis=1)

    # flags = ['o', 'v', 'i', 'm', 'q', 'p', 'e', 'z', 't', 'h', 'd', 'n',
    #          's', 'a', 'b']

    set_orientation(df)
    set_view(df)
    set_instrument(df)
    set_moving(df)
    set_quality(df)
    set_pointing(df)
    set_ephemeris(df)
    process_qmi(df)
    set_noise(df)

    for flag in flags:
        df[flag] = 0

    # filter for the channel requested:
    df_ch = df[df.c == int(ch)]

    # fill the nan values of your tb and radiance calculations with -9999.0
    df_ch.fillna(-9999.0, inplace=True)

    # create channel id:
    chid = 'C' + ch

    # open file and start write-loop
    f = open(os.path.join(fu.outpath, timestr + '_' + chid + '_RDR.TAB'), 'w')

    # header defined above, globally for this file.
    print("Starting the write-out.")
    f.write(header + '\r\n')
    for i, data in enumerate(df_ch.values):
        if all(data[22:30] < -5000):
            fmt = formatter.nan
        # spaceview
        elif (all(data[22:24] > -5000)) and (all(data[24:30] < -5000)):
            fmt = formatter.space
        # solartarget view
        elif (all(data[22:24] > -5000) and (all(data[24:27] < -5000))
                and (all(data[27:29] > -5000))):
            fmt = formatter.solartarget
        # nominal
        elif all(data[22:30] > -5000):
            fmt = formatter.nominal
        # uncaught case, raise exception to notify user!
        else:
            print(i)  # which line
            print(data)  # print whole row
            # point out af status, might help to understand
            print("af:", data[14])
            for j, item in enumerate(data[22:30]):
                print(j + 22, item)
            raise Exception
        f.write(', '.join(fmt).format(*data) + '\r\n')
    f.close()


if __name__ == '__main__':
    only_calibrate()
