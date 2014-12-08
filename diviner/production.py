#!/usr/bin/env python
from __future__ import division, print_function
from diviner import calib
from diviner import file_utils as fu
from diviner import ana_utils as au
from joblib import Parallel, delayed
import pandas as pd
import numpy as np
import diviner
import logging
import os
from os import path
import sys
import rdrx
import gc
from diviner.exceptions import RDRS_NotFoundError
from bintools import cols_to_descriptor
import ConfigParser

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - '
                              '%(message)s')

module_logger = logging.getLogger(name='diviner.production')

formats = pd.read_csv(path.join(diviner.__path__[0],
                                'data',
                                'joined_format_file.csv'))

cols_no_melt = [i for i in formats.colname if i in rdrx.no_melt]
cols_skip = 'c det tb radiance'.split()
cols_to_melt = set(formats.colname) - set(cols_no_melt) - set(cols_skip)
cols_to_melt = [i for i in cols_to_melt if i in rdrx.to_melt]


class Configurator(object):

    def __init__(self, startstop=None, overwrite=False, c_start=3, c_end=9,
                 do_rad_corr=False, swap_clons=True, save_as_pipes=True):
        # time scope of run definition
        self.start, self.stop = startstop
        self.tstrings = fu.calc_daterange(self.start, self.stop)
        self.run_name = start + '_' + stop

        self.overwrite = overwrite

        self.c_start = c_start
        self.c_end = c_end

        self.do_rad_corr = do_rad_corr
        self.swap_clons = swap_clons
        self.save_as_pipes = save_as_pipes
        if save_as_pipes is True:
            self.out_format = 'bin'
        else:
            self.out_format = 'csv'

        # set up paths
        self.savedir = self.paths.savedir
        self.rdr2_root = self.paths.rdr2_root

        # logging setup
        logger = logging.getLogger(name='diviner')
        logger.setLevel(logging.DEBUG)
        logfname = 'divcalib_verif_' + self.run_name + '.log'
        fh = logging.FileHandler(logfname)
        fh.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(stream=None)
        ch.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        logger.addHandler(fh)
        logger.addHandler(ch)

        if not os.path.exists(self.savedir):
            os.makedirs(self.savedir)
        if not os.path.exists(self.rdr2_root):
            os.makedirs(self.rdr2_root)

    def get_rdr2_savename(self, tstr, c, savedir=None):
        if savedir is None:
            savedir = self.rdr2savedir
        return path.join(savedir,
                         '{0}_C{1}_RDR_2.{2}'.format(tstr, c, self.out_format))


def get_tb_savename(savedir, tstr):
    return path.join(savedir, tstr + '_tb.hdf')


def get_rad_savename(savedir, tstr):
    return path.join(savedir, tstr + '_radiance.hdf')


def get_rdr2_savename(savedir, tstr, c):
    return path.join(savedir, '{0}_C{1}_RDR_2.CSV'.format(tstr, c))


def get_example_data():
    tstr = '2013031707'
    df = fu.get_clean_l1a(tstr)
    rdr2 = calib.Calibrator(df)
    rdr2.calibrate()
    rdr1 = rdrx.RDRS(tstr)
    return rdr1, rdr2


def calibrate_tstr(tstr, savedir, do_rad_corr):
    module_logger.info('Calibrating {}'.format(tstr))
    sys.stdout.flush()
    df = fu.open_and_accumulate(tstr=tstr)
    try:
        if len(df) == 0:
            return
    except TypeError:
        return
    rdr2 = calib.Calibrator(df, fix_noise=True, do_rad_corr=do_rad_corr)
    rdr2.calibrate()
    rdr2.Tb.to_hdf(get_tb_savename(savedir, tstr), 'df')
    rdr2.abs_radiance.to_hdf(get_rad_savename(savedir, tstr), 'df')


def only_calibrate(timestrings):

    savedir = '/raid1/maye/rdr_out/only_calibrate'
    Parallel(n_jobs=4,
             verbose=5)(delayed(calibrate_tstr)
                        (tstr.strip(), savedir) for tstr in timestrings)


def melt_and_merge_rdr1(rdrxobject, c):
    """Melt and merge required columns out of RDRx file.

    Above defined formats file defines what columns are required for this
    production function.
    """
    # first get the columns that do not need melting
    no_melts = rdrxobject.df[cols_no_melt]

    # now go through each column of format that needs melting and save it in
    # a temp. container
    container = []
    for col in cols_to_melt:
        container.append(rdrxobject.get_molten_col(col, c))

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


def grep_channel_and_melt(indf, colname, channel, obs, invert_dets=True):
    c = indf.filter(regex=channel.mcs+'_')[obs.time.tindex]
    renamer = lambda x: int(x[-2:])
    # for telescope B (channel.div > 6):
    if (channel.div > 6) and invert_dets:
        renamer = lambda x: 22 - int(x[-2:])
    c = c.rename(columns=renamer)
    c_molten = pd.melt(c.reset_index(), id_vars=['index'], var_name='det',
                       value_name=colname)
    return c_molten


def add_time_columns(df):
    tindex = pd.DatetimeIndex(df['index'])
    df['hour'] = tindex.hour
    df['minute'] = tindex.minute
    df['second'] = tindex.second
    df['micro'] = tindex.microsecond // 1000
    df['year'] = tindex.year
    df['month'] = tindex.month
    df['date'] = tindex.day
    df['second'] = df.second.astype('str') + '.' + df.micro.astype('str')
    df.drop('micro', axis=1, inplace=True)


def check_for_existing_files(config, tstr):
    channels_to_do = []
    # check which channels are not done yet, if so.
    all_done = True
    for c in range(config.c_start, config.c_end+1):
        fname = config.get_rdr2_savename(tstr, c)
        if path.exists(fname) and (not config.overwrite):
            module_logger.debug("Found existing RDR2, skipping: {}"
                                .format(path.basename(fname)))
        else:
            all_done = False
            channels_to_do.append(c)
    return all_done, channels_to_do


def get_data_for_merge(tstr, savedir):
    # start processing
    module_logger.info('Processing {0}'.format(tstr))
    obs = fu.DivObs(tstr)
    try:
        rdr1 = rdrx.RDRS(obs.rdrsfname.path)
    except RDRS_NotFoundError:
        module_logger.warning('RDRS not found for {}'.format(tstr))
        return
    if not path.exists(get_tb_savename(savedir, tstr)):
        try:
            calibrate_tstr(tstr, savedir, config.do_rad_corr)
        except:
            module_logger.error('Calibration failed for {}'.format(tstr))
            return
    try:
        tb = pd.read_hdf(get_tb_savename(savedir, tstr), 'df')
    except KeyError:
        module_logger.error("Could not find key 'df' in tb file for {}"
                            .format(tstr))
        return
    try:
        rad = pd.read_hdf(get_rad_savename(savedir, tstr), 'df')
    except KeyError:
        module_logger.error("Could not find key 'df' in rad file for {}"
                            .format(tstr))
        return
    return obs, rdr1, tb, rad


def produce_tstr(args):
    tstr, config = args

    module_logger.debug("Entered produce_tstr()")

    rdr2savedir = config.rdr2savedir
    savedir = config.savedir

    # determine what is left to do:
    all_done, channels_to_do = check_for_existing_files(config, tstr)

    if all_done:
        module_logger.info("Not overwriting existing files for {}. Returning.".
                           format(tstr))
        return

    try:
        obs, rdr1, tb, rad = get_data_for_merge(tstr, savedir)
    except Exception as e:
        module_logger.error("Error in get_data_for_merge: {}".format(e))

    mergecols = ['index', 'det']
    for c in channels_to_do:
        module_logger.debug('Processing channel {} of {}'.format(c, tstr))
        if not path.exists(rdr2savedir):
            os.mkdir(rdr2savedir)
        fname = config.get_rdr2_savename(tstr, c)
        channel = au.Channel(c)
        rdr1_merged = melt_and_merge_rdr1(rdr1, channel.div)

        tb_molten_c = grep_channel_and_melt(tb, 'tb', channel, obs)
        rad_molten_c = grep_channel_and_melt(rad, 'radiance', channel, obs)

        rdr2 = rdr1_merged.merge(tb_molten_c, left_on=mergecols,
                                 right_on=mergecols)
        rdr2 = rdr2.merge(rad_molten_c, left_on=mergecols, right_on=mergecols)
        add_time_columns(rdr2)
        rdr2.fillna(-9999, inplace=True)
        rdr2.det = rdr2.det.astype('int')
        rdr2.drop('index', inplace=True, axis=1)
        rdr2['c'] = channel.div
        clon_cols = rdr2.filter(regex="^clon_").columns
        if config.swap_clons:
            for col in clon_cols:
                rdr2[col] = rdr2[col].map(lambda x: -(360 - x)
                                          if x > 180 else x)
        if not config.save_as_pipes:
            rdr2.to_csv(fname, index=False)
        else:
            # first put a descriptor file next to it if it doesn't exist
            descpath = rdr2savedir + '/rdr2_verif.des'
            if not os.path.exists(descpath):
                with open(descpath, 'w') as f:
                    f.write(cols_to_descriptor(rdr2.columns))
            # now write the values in binary form
            rdr2.values.astype(np.double).tofile(fname)
    gc.collect()
    return "{} done.".format(tstr)


if __name__ == '__main__':

    try:
        configfile = sys.argv[1]
    except IndexError:
        print("Provide config file as argument")
        sys.exit()

    config = ConfigParser.ConfigParser()
    config.read(configfile)

    # paths and scope of production run
    start = config.get('run_control', 'start')
    stop = config.get('run_control', 'stop')
    rad_tb_path = config.get('paths', 'rad_tb')
    pipes_path = config.get('paths', 'pipes')

    # calibration control options
    overwrite = config.getbool('calibration', 'overwrite')
    c_start = config.getint('calibration', 'c_start')
    c_end = config.getint('calibration', 'c_end')
    do_rad_corr = config.getbool('calibration', 'do_rad_corr')
    swap_clons = config.getbool('calibration', 'swap_clons')
    save_as_pipes = config.getbool('calibration', 'save_as_pipes')

    config = Configurator(startstop=(start, stop),
                          overwrite=overwrite,
                          do_rad_corr=do_rad_corr,
                          save_as_pipes=save_as_pipes,
                          swap_clons=swap_clons)
    if not path.exists(config.rdr2savedir):
        os.mkdir(config.rdr2savedir)

    tstrings = config.tstrings
    Parallel(n_jobs=8, verbose=20)(delayed(produce_tstr)((tstr, config))
                                   for tstr in tstrings)


# def prepare_rdr2_write(df):
#     pass


# def write_rdr2(df, formatter, fname):
#     formatter = Formatter()

#     # read in old RDR
#     print("Reading old RDR file.")
#     rdr = fu.RDRReader('/u/paige/maye/rdr_data/' + timestr + '_RDR.TAB.zip')
#     df = rdr.read_df(do_parse_times=False)
#     print("Done reading.")

#     # add cphase and roi
#     df['cphase'] = 123.45678
#     df['roi'] = 1234

#     # adapt to new format
#     # drop the old quality flags
#     df = df.drop(['qca', 'qge', 'qmi'], axis=1)

#     # flags = ['o', 'v', 'i', 'm', 'q', 'p', 'e', 'z', 't', 'h', 'd', 'n',
#     #          's', 'a', 'b']

#     set_orientation(df)
#     set_view(df)
#     set_instrument(df)
#     set_moving(df)
#     set_quality(df)
#     set_pointing(df)
#     set_ephemeris(df)
#     process_qmi(df)
#     set_noise(df)

#     for flag in flags:
#         df[flag] = 0

#     # filter for the channel requested:
#     df_ch = df[df.c == int(ch)]

#     # fill the nan values of your tb and radiance calculations with -9999.0
#     df_ch.fillna(-9999.0, inplace=True)

#     # create channel id:
#     chid = 'C' + ch

#     # open file and start write-loop
#     f = open(path.join(fu.outpath, timestr + '_' + chid + '_RDR.TAB'), 'w')

#     # header defined above, globally for this file.
#     print("Starting the write-out.")
#     f.write(header + '\r\n')
#     for i, data in enumerate(df_ch.values):
#         if all(data[22:30] < -5000):
#             fmt = formatter.nan
#         # spaceview
#         elif (all(data[22:24] > -5000)) and (all(data[24:30] < -5000)):
#             fmt = formatter.space
#         # solartarget view
#         elif (all(data[22:24] > -5000) and (all(data[24:27] < -5000))
#                 and (all(data[27:29] > -5000))):
#             fmt = formatter.solartarget
#         # nominal
#         elif all(data[22:30] > -5000):
#             fmt = formatter.nominal
#         # uncaught case, raise exception to notify user!
#         else:
#             print(i)  # which line
#             print(data)  # print whole row
#             # point out af status, might help to understand
#             print("af:", data[14])
#             for j, item in enumerate(data[22:30]):
#                 print(j + 22, item)
#             raise Exception
#         f.write(', '.join(fmt).format(*data) + '\r\n')
#     f.close()
