#!/usr/bin/env python


import gc
import logging
import os
import sys
from os import path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

import diviner
from diviner import ana_utils as au
from diviner import calib
from diviner import file_utils as fu
from diviner import rdrx
from diviner.exceptions import RDRR_NotFoundError

from .bintools import cols_to_descriptor
from .divlogging import setup_logger

module_logger = logging.getLogger(name="diviner.production")

formats = pd.read_csv(path.join(diviner.__path__[0], "data", "joined_format_file.csv"))

cols_no_melt = set([i for i in formats.colname if i in rdrx.no_melt])
cols_skip = "c det tb radiance".split()
cols_to_melt = list(set(formats.colname) - set(cols_no_melt) - set(cols_skip))
cols_to_melt = [i for i in cols_to_melt if i in rdrx.to_melt]


def read_and_clean(fname):
    with open(fname) as f:
        tstrings = f.readlines()
    return [i.strip() for i in tstrings]


class SavePaths(object):
    def __init__(self, do_rad_corr):
        if do_rad_corr:
            savedir = "/luna4/maye/rdr_out/only_calibrate"
            rdr2_root = "/luna4/maye/rdr_out/verification"
        else:
            savedir = "/luna4/maye/rdr_out/no_jpl_correction"
            rdr2_root = "/luna4/maye/rdr_out/verification_no_jpl_corr"
        if not os.path.exists(savedir):
            os.makedirs(savedir)
        if not os.path.exists(rdr2_root):
            os.makedirs(rdr2_root)


    def get_other_folders(self):
        others = []
        for f in self.test_names:
            if f != self.run_name:
                others.append(f)
        return others

    def get_rdr2_savename(self, tstr, c, savedir=None):
        if savedir is None:
            savedir = self.rdr2savedir
        return path.join(savedir, "{0}_C{1}_RDR_2.{2}".format(tstr, c, self.out_format))

    @property
    def rdr2savedir(self):
        return path.join(self.rdr2_root, self.run_name)

    @property
    def Ben_2012_2(self):
        fname = path.join(diviner.__path__[0], "data", "A14_HOURS.txt")
        return read_and_clean(fname)

    @property
    def beta_0_circular(self):
        "low beta, circular orbit."
        fname = path.join(diviner.__path__[0], "data", "2009082321_2009092002.txt")
        return read_and_clean(fname)

    @property
    def beta_0_elliptical(self):
        "low beta, elliptical orbit"
        fname = path.join(diviner.__path__[0], "data", "2012022408_2012032323.txt")

        return read_and_clean(fname)

    @property
    def beta_90_circular(self):
        fname = path.join(diviner.__path__[0], "data", "2010120102_2010122712.txt")
        return read_and_clean(fname)

    @property
    def beta_90_elliptical(self):
        fname = path.join(diviner.__path__[0], "data", "2012061211_2012062602.txt")
        return read_and_clean(fname)





if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-r", "--run_name", help="use predefined run_name from" " Configurator."
    )
    group.add_argument(
        "-s",
        "--startstop",
        help="provide start and stop " "string comma-separated in YYYYMMDDHH format.",
    )

    overwrite_group = parser.add_mutually_exclusive_group()
    overwrite_group.add_argument(
        "--overwrite",
        help="overwrite existing files",
        dest="overwrite",
        action="store_true",
    )
    overwrite_group.add_argument(
        "--no-overwrite",
        help="do not overwrite exisiting files",
        dest="overwrite",
        action="store_false",
    )
    parser.set_defaults(overwrite=True)

    doradcorr_group = parser.add_mutually_exclusive_group()
    doradcorr_group.add_argument(
        "--do-rad-corr",
        help="do JPL radiance correction",
        dest="do_rad_corr",
        action="store_true",
    )
    doradcorr_group.add_argument(
        "--no-rad-corr",
        help="do NOT do radiance correction",
        dest="do_rad_corr",
        action="store_false",
    )
    parser.set_defaults(do_rad_corr=True)

    outformat_group = parser.add_mutually_exclusive_group()
    outformat_group.add_argument(
        "--save_as_pipes",
        help="save in pipes binary format",
        dest="save_as_pipes",
        action="store_true",
    )
    outformat_group.add_argument(
        "--save_as_csv",
        help="save in CSV text format",
        dest="save_as_pipes",
        action="store_false",
    )
    parser.set_defaults(save_as_pipes=True)
    parser.add_argument(
        "--swap_clons",
        help="swap clon values from 0..360 to -180..180 " "for Ben.",
        dest="swap_clons",
        action="store_true",
    )

    args = parser.parse_args()
    if args.startstop:
        start, stop = args.startstop.split(",")
        config = Configurator(
            startstop=(start, stop),
            overwrite=args.overwrite,
            do_rad_corr=args.do_rad_corr,
            save_as_pipes=args.save_as_pipes,
            swap_clons=args.swap_clons,
        )
        if not path.exists(config.rdr2savedir):
            os.mkdir(config.rdr2savedir)

        tstrings = config.tstrings
        Parallel(n_jobs=8, verbose=20)(
            delayed(produce_tstr)((tstr, config)) for tstr in tstrings
        )
    else:
        runs = [args.run_name]
        if runs == "all":
            runs = Configurator.test_names
        for name in runs:
            config = Configurator(
                name,
                c_start=3,
                c_end=9,
                overwrite=args.overwrite,
                do_rad_corr=args.do_rad_corr,
                swap_clons=args.swap_clons,
                save_as_pipes=args.save_as_pipes,
            )
            if not path.exists(config.rdr2savedir):
                os.mkdir(config.rdr2savedir)

            tstrings = config.tstrings

            Parallel(n_jobs=8, verbose=20)(
                delayed(produce_tstr)((tstr, config)) for tstr in tstrings
            )


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
