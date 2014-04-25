#!/usr/bin/env python
from __future__ import print_function, division
from diviner import file_utils as fu
import sys
import pandas as pd
import os
from diviner import divtweet
from subprocess import call
import glob
from os.path import join as pjoin

savedir = os.path.join(fu.outpath, 'metadata')
if not os.path.exists(savedir):
    os.makedirs(savedir)


def collect_data(pump):
    frames = []
    metadatacols = list(set(pump.keys) - set(fu.L1AHeader.datacols))
    for fname in pump.fnames:
        df = pump.process_one_file(fname)
        frames.append(df[metadatacols])
    print("Concatting...")
    df = pd.concat(frames)
    return df


def produce_store_file(timestr):
    pump = fu.Div247DataPump(timestr)
    print("Found {0} files.".format(len(pump.fnames)))

    if len(pump.fnames) == 0:
        return

    savepath = os.path.join(savedir, timestr + '.h5')

    df = collect_data(pump)

    print("Polishing...")
    final = pump.clean_final_df(df)
    print("Writing to store...")
    final.to_hdf(savepath, 'df')
    print("Done.")


def produce_store_file_main():
    try:
        year = sys.argv[1]
    except IndexError:
        print("Usage: {0} year(yyyy)".format(sys.argv[0]))
        sys.exit()
    months = range(1, 13)
    for month in months:
        timestr = year + str(month).zfill(2)
        divtweet.tweet_machine("Producing metadata for {0}".format(timestr))
        print("Producing", timestr)
        produce_store_file(timestr)


def divmetadata():
    if len(sys.argv) < 3:
        print("Usage: {0} month_start month_end [YYYYMM]".format(sys.argv[0]))
        sys.exit()
    months = pd.period_range(sys.argv[1], sys.argv[2], freq='M')
    cmd_middle = (
        "clat=-90,90 c=3,3 det=11,11 | "
        "pextract extract=year,month,date,hour,minute,second,jdate,orbit,"
        "sundst,sunlat,sunlon,sclk,sclat,sclon,scrad,scalt,"
        "el_cmd,az_cmd,af,vert_lat,vert_lon,vlookx,vlooky,vlookz,clat,clon,"
        "cemis,csunzen,csunazi,cloctime,qca,qge,qmi,qual | "
        "pprint titles=0 > ")
    for month in months:
        print("Producing metadata for month {0}".format(month))
        ts = month.to_timestamp()
        cmd_base = 'divdata daterange={0}'.format(ts.strftime('%Y%m '))
        outfname = os.path.join(savedir,
                                '{0}_divmetadata.csv'
                                .format(ts.strftime('%Y%m')))
        cmd = cmd_base + cmd_middle + outfname
        call(cmd, shell=True)
        divtweet.tweet_machine(
            "Metadata for month {0} finished.".format(month))


def resampler(year, interval):
    """Resample the full resolution metadata files of year down to <interval>.

    Resample the full resolution metadata files of year <year> down to
    <interval>.
    <interval> can be format strings like '1d' for downsampling to days,
    '1h' for hours, '1min' for minutes, etc.
    <year> can be given as string or int.
    """
    fnames = glob.glob(pjoin(savedir, str(year) + '??.h5'))
    fnames.sort()
    l = []
    for fname in fnames:
        print("Reading {0}".format(fname))
        l.append(pd.read_hdf(fname, 'df').resample(interval, kind='period'))

    df = pd.concat(l)
    hdf_fname = pjoin(savedir, str(year) + '_daily_means.h5')
    df.to_hdf(hdf_fname, 'df')
    print("Created {}.".format(hdf_fname))
    divtweet.tweet_machine(
        "Fininshed resampling {0} to {1}".format(year, interval))


def get_all_df():
    """Load all Diviner mission metadata daily means."""
    years = range(2009, 2014)
    l = []
    for year in years:
        store = pd.HDFStore(pjoin(savedir, str(year) + '_daily_means.h5'))
        l.append(store['df'])
        store.close()
    return pd.concat(l)


if __name__ == '__main__':
    try:
        funcname = sys.argv[1]
    except IndexError:
        print("\nWhich function do you want? ['resampler', 'producemonth']")
        sys.exit()
    if funcname == 'resampler':
        try:
            resampler(*sys.argv[2:4])
        except TypeError:
            print("Provide <year> and <downsample> strings as input.")
            sys.exit()
    elif funcname == 'producemonth':
        timestr = sys.argv[2]
        produce_store_file(timestr)
