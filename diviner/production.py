#!/usr/bin/env python

import configparser
import gc
import logging
import os
import sys
from importlib.resources import path as resource_path
from os import path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from diviner import ana_utils as au
from diviner import calib
from diviner import file_utils as fu
from diviner.exceptions import DivCalibError, RDRS_NotFoundError

from . import configuration, rdrx
from .bintools import cols_to_descriptor

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - " "%(message)s")

module_logger = logging.getLogger(name="diviner.production")

with resource_path("diviner.data", "joined_format_file.csv") as p:
    formats = pd.read_csv(p)

with resource_path("diviner.data", "newfmt_master.txt") as p:
    newformat = pd.read_table(p, sep=" ", skipinitialspace=True, header=None)

cols_no_melt = [i for i in formats.colname if i in rdrx.no_melt]
cols_skip = "c det tb radiance".split()
cols_to_melt = list(set(formats.colname) - set(cols_no_melt) - set(cols_skip))
cols_to_melt = [i for i in cols_to_melt if i in rdrx.to_melt]


def get_example_data():
    tstr = "2013031707"
    df = fu.get_clean_l1a(tstr)
    rdr2 = calib.Calibrator(df)
    rdr2.calibrate()
    rdr1 = rdrx.RDRS(tstr)
    return rdr1, rdr2


def calibrate_tstr(tstr, savedir, do_rad_corr):
    "Main function for pure calibration part."
    module_logger.info("Calibrating {}".format(tstr))
    sys.stdout.flush()
    df = fu.open_and_accumulate(tstr=tstr)
    try:
        if len(df) == 0:
            return
    except TypeError:
        return
    if do_rad_corr in ("both", True):
        rdr2 = calib.Calibrator(df, fix_noise=False, do_rad_corr=True)
        rdr2.calibrate()
        rdr2.Tb.to_hdf(get_tb_savename(savedir, tstr), "df")
        rdr2.abs_radiance.to_hdf(get_rad_savename(savedir, tstr), "df")


def only_calibrate(timestrings):

    savedir = "/raid1/maye/rdr_out/only_calibrate"
    Parallel(n_jobs=4, verbose=5)(
        delayed(calibrate_tstr)(tstr.strip(), savedir) for tstr in timestrings
    )


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
    mergecols = "index det".split()
    res = None
    while True:
        try:
            if res is None:
                res = container.pop()
            res = res.merge(container.pop(), left_on=mergecols, right_on=mergecols)
        except IndexError:
            break
    final = pd.merge(no_melts.reset_index(), res, left_on="index", right_on="index")
    return final


# def symlink_existing_files(config, tstr):
#     """Find and symlink existing files to avoid duplication."""

#     for c in range(config.c_start, config.c_end + 1):
#         path_here = config.get_rdr2_savename(tstr, c)
#         # if I have the file in current folder, no need to look it up in others
#         if path.exists(path_here):
#             continue
#         for folder in config.get_other_folders():
#             othersavedir = path.join(config.rdr2_root, folder)
#             otherpath = config.get_rdr2_savename(tstr, c, savedir=othersavedir)
#             if path.exists(otherpath):
#                 os.symlink(otherpath, path_here)
#                 module_logger.info("Symlinked {} into {}".format(otherpath, path_here))


def grep_channel_and_melt(indf, colname, channel, obs, invert_dets=True):
    c = indf.filter(regex=channel.mcs + "_")[obs.time.tindex]
    renamer = lambda x: int(x[-2:])
    # for telescope B (channel.div > 6):
    if (channel.div > 6) and invert_dets:
        renamer = lambda x: 22 - int(x[-2:])
    c = c.rename(columns=renamer)
    c_molten = pd.melt(
        c.reset_index(), id_vars=["index"], var_name="det", value_name=colname
    )
    return c_molten


def add_time_columns(df):
    tindex = pd.DatetimeIndex(df["index"])
    df["hour"] = tindex.hour
    df["minute"] = tindex.minute
    df["second"] = tindex.second
    df["micro"] = tindex.microsecond // 1000
    df["year"] = tindex.year
    df["month"] = tindex.month
    df["date"] = tindex.day
    df["second"] = df.second.astype("str") + "." + df.micro.astype("str")
    df.drop("micro", axis=1, inplace=True)


# def check_for_existing_files(config, tstr):
#     channels_to_do = []
#     # check which channels are not done yet, if so.
#     all_done = True
#     for c in range(config.c_start, config.c_end + 1):
#         fname = config.get_rdr2_savename(tstr, c)
#         if path.exists(fname) and (not config.overwrite):
#             module_logger.debug(
#                 "Found existing RDR2, skipping: {}".format(path.basename(fname))
#             )
#         else:
#             all_done = False
#             channels_to_do.append(c)
#     return all_done, channels_to_do


def get_data_for_merge(tstr, config):
    """get_data_for merge does many things.

    1. Get the older, unchanged RDRS data, to be merged into the new RDR
    2. Perform the new calibration if the Tb and Radiance files aren't there yet.

    Parameters
    ----------
    tstr : str
        Format: %Y%m%d%H, a standard EDR time string to identify a data file
    config : configuration.Config
        config object holding all the paths.

    Returns
    -------
    obs, rdr1, tb, rad
    DivObs object, rdr1 reference, newly calibrated tb and rad data.
    """
    savedir = config.savedir
    # start processing
    module_logger.info("Processing {0}".format(tstr))
    obs = fu.DivObs(tstr)
    try:
        rdr1 = rdrx.RDRS(obs.rdrsfname.path)
    except RDRS_NotFoundError:
        module_logger.warning("RDRS not found for {}".format(tstr))
        raise RDRS_NotFoundError
    if not path.exists(get_tb_savename(savedir, tstr)):
        try:
            calibrate_tstr(tstr, savedir, config.do_rad_corr)
        except:  # noqa: E722
            module_logger.error("Calibration failed for {}".format(tstr))
            raise DivCalibError
    try:
        tb = pd.read_hdf(get_tb_savename(savedir, tstr), "df")
    except KeyError:
        module_logger.error("Could not find key 'df' in tb file for {}".format(tstr))
        return
    try:
        rad = pd.read_hdf(get_rad_savename(savedir, tstr), "df")
    except KeyError:
        module_logger.error("Could not find key 'df' in rad file for {}".format(tstr))
        return
    return obs, rdr1, tb, rad


def produce_tstr(args, return_df=False, convert_to_RDR2=True):
    tstr, config = args

    module_logger.debug("Entered produce_tstr()")

    savedir = config.savedir

    # first create symlinks to avoid duplication
    # symlink_existing_files(config, tstr)
    # now determine whatever else is left to do:
    # all_done, channels_to_do = check_for_existing_files(config, tstr)

    # if all_done:
    #     module_logger.info(
    #         "Not overwriting existing files for {}. Returning.".format(tstr)
    #     )
    #     return

    try:
        obs, rdr1, tb, rad = get_data_for_merge(tstr, config)
    except Exception as e:
        module_logger.error("Error in get_data_for_merge: {}".format(e))
        raise (e)

    mergecols = ["index", "det"]
    for c in channels_to_do:
        module_logger.debug("Processing channel {} of {}".format(c, tstr))
        channel = au.Channel(c)
        rdr1_merged = melt_and_merge_rdr1(rdr1, channel.div)

        tb_molten_c = grep_channel_and_melt(tb, "tb", channel, obs)
        return tb_molten_c
        rad_molten_c = grep_channel_and_melt(rad, "radiance", channel, obs)

        rdr2 = rdr1_merged.merge(tb_molten_c, left_on=mergecols, right_on=mergecols)
        rdr2 = rdr2.merge(rad_molten_c, left_on=mergecols, right_on=mergecols)
        add_time_columns(rdr2)
        rdr2.fillna(-9999, inplace=True)
        rdr2.det = rdr2.det.astype("int")
        rdr2.drop("index", inplace=True, axis=1)
        rdr2["c"] = channel.div
        clon_cols = rdr2.filter(regex="^clon_").columns
        if config.swap_clons:
            for col in clon_cols:
                rdr2[col] = rdr2[col].map(lambda x: -(360 - x) if x > 180 else x)
        if convert_to_RDR2:
            # big restructure, reshuffling of columns happens now:
            rdr2 = reformat_for_pipes(rdr2)
        # storing results
        fname = config.get_rdr2_savename(tstr, c)
        if config.out_format == "csv":
            rdr2.to_csv(fname, index=False)
        elif config.out_format == "bin":
            # put a descriptor file next to the data
            descpath = config.pipes_dir / "rdr2_verif.des"
            with open(descpath, "w") as f:
                f.write(cols_to_descriptor(rdr2.columns))
            # now write the values in binary form
            rdr2.values.astype(np.double).tofile(str(fname))
    gc.collect()
    if return_df:
        return rdr2


def reformat_for_pipes(df):
    # adapt to new format
    # drop the old quality flags
    df = df.drop(["qca", "qge"], axis=1)

    # get utc column
    df.rename({"date": "day"}, axis=1, inplace=True)
    time_cols = "year month day hour minute second".split()
    utc = pd.to_datetime(df[time_cols])
    df = df.drop(time_cols, axis=1)

    df["date"] = utc.dt.strftime("%Y%m%d")
    seconds = (
        utc.dt.hour * 3600
        + utc.dt.minute * 60
        + utc.dt.second
        + utc.dt.microsecond * 1e-6
    )
    df["time"] = seconds
    # df['utc'] = df.utc.dt.strftime("%H:%M:%S.%f").str[:-3]

    # add cphase and roi
    df["cphase"] = 123.45678
    df["roi"] = 1234

    flags = ["o", "v", "i", "m", "q", "p", "e", "z", "t", "h", "d", "n", "s", "a", "b"]

    for flag in flags:
        df[flag] = 0

    newcols = newformat[1]
    # dropping UTC column
    newcols = newcols.drop(1).values.tolist()
    newcols.insert(1, "time")
    return df[newcols]



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
