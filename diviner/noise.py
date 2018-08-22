#!/usr/bin/env python
from __future__ import division
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import pandas
import numpy as np
import diviner as div
from scipy import fft
import os
import sys
from os.path import split, splitext
from glob import glob
from multiprocessing import Pool

resultsdir = '/u/paige/maye/WWW/noise'
debug = False


def isodd(number):
    return bool(number % 2)


def get_label(dataframe, label, ch, det=11):
    l = dataframe[label][(dataframe.c == ch) & (dataframe.det == det)]
    return l


def plot_all(ax, tbdata, azdata, elevdata, title):
    ax.plot(tbdata, label='tb')
    ax.plot(azdata, label='az_cmd')
    ax.plot(elevdata, label='el_cmd')
    ax.set_title(title)
    ax.legend(loc='best')


def get_abs_fft(data):
    f = fft(data)
    half = len(f)/2
    fix = 0
    if isodd(len(f)):
        fix = 1
    t = np.arange(-half, half+fix, 1)
    f_sorted = np.concatenate((f[half:], f[:half]))
    return t, abs(f_sorted)


def plot_fft(ax, datatuple, title):
    t, data = datatuple
    ax.semilogy(t, data)
    ax.set_xlim(0, 0.5*len(data))
    ax.set_ylim(0, 0.2*data.max())
    ax.set_title(title)


def fix_columns(df):
    headers = df.columns.tolist()
    headers[0] = 'year'
    headers[2] = 'date'
    df.columns = headers


def prep_data(fname):
    df = div.read_div_data(fname)
    fix_columns(df)
    df.set_index('jdate', inplace=True)
    return df


def plot_channel_means(ax, df, col_str, ch_start=1, ch_end=9):
    for i in range(ch_start, ch_end+1):
        series = div.get_channel_mean(df, col_str, i)
        if debug:
            print(i, series.min())
        ax.plot(series, label=str(i))
    ax.set_ylabel('c_mean('+col_str+')')


def plot_channel_stds(ax, df, col_str):
    for i in range(9):
        series = div.get_channel_std(df, col_str, i+1)
        if debug:
            print(i, series.min())
        ax.plot(series, label=str(i+1))
    ax.set_ylabel('c_std('+col_str+')')


def get_datasetname(fname):
    return splitext(split(fname)[1])[0]


def get_new_fname(datasetname, col_str):
    basename = '{0}_{1}.png'.format(datasetname, col_str)
    return os.path.join(resultsdir, basename)


def plot_csunzen(ax, df):
    csunzen = div.get_channel_mean(df, 'csunzen', 1)
    # csunzen[csunzen < -360]=np.nan
    ax2 = ax.twinx()
    ax2.plot(csunzen, label='csunzen', color='blue')
    ax2.axhline(y=90, color='black')
    for tl in ax2.get_yticklabels():
        tl.set_color('blue')
    ax2.set_ylabel('csunzen')


def process_fname(fname_col_str):
    fname, col_str = fname_col_str

    print("Preparing data...")
    df = prep_data(fname)
    print("Done.")
    fig = plt.figure()
    ax = fig.add_subplot(111)
    print("Plotting channels.")
    plot_channel_means(ax, df, col_str, 3, 5)
    print("Done plotting channels. Plotting csunzen.")
    plot_csunzen(ax, df)
    ax.legend(loc='best', ncol=3,)
    datasetname = get_datasetname(fname)
    ax.set_title(datasetname+'_'+col_str)
    plotfname = get_new_fname(datasetname, col_str)
    print("Result filename: ", plotfname)
    plt.savefig(plotfname)

    #
    # ##############
    # ### watch out!
    # for df in dfnoise:
    #     df.tb[df.tb < -9990] = 0
    #     df.tb[np.isnan(df.tb)] = 0
    # dfclean.tb[dfclean.tb < -9990] = 0
    # dfclean.tb[np.isnan(dfclean.tb)] = 0
    # ### watch this!
    # ##############
    #
    # tbcleans = get_label(dfclean, 'tb', channel, det)
    # azclean = get_label(dfclean, 'az_cmd', channel)
    # elevclean = get_label(dfclean, 'el_cmd', channel)
    # tbnoise = [get_label(df, 'tb', channel, det) for df in dfnoise]
    # aznoise = [get_label(df, 'az_cmd', channel) for df in dfnoise]
    # elevnoise = [get_label(df, 'el_cmd', channel) for df in dfnoise]
    #
    # fig, axes = plt.subplots(2,2, figsize=(10,10))
    #
    # plot_all(axes[0,0], tbcleans, azclean, elevclean,
    #     'Random 2012 PDS dataset, Ch {0}, Det {1}'.format(channel,det))
    #
    # for i,tbdata,azdata,elevdata,ax in zip([1,2,3],
    #                                      tbnoise,
    #                                      aznoise,
    #                                      elevnoise,
    #                                      axes.flatten()[1:]):
    #     plot_all(ax, tbdata, azdata, elevdata,
    #         'Noisy dataset {0}, Ch {1}, Det {2}'.format(i,channel,det))
    #
    # cleantup = get_abs_fft(tbcleans)
    # print(len(cleantup))
    # noisetub = [get_abs_fft(data) for data in tbnoise]
    #
    # figff, axes = plt.subplots(2,2, figsize=(10,10))
    # plot_fft(axes[0,0], cleantup, 'FFT of a 2012 PDS dataset')
    #
    # for i,ftbdata,ax in zip([1,2,3],
    #                         noisetub,
    #                         axes.flatten()[1:]):
    #     plot_fft(ax, ftbdata,
    #         'FFT of noisy data {0}, Ch {1}, Det {2}'.format(i,channel, det))
    #
    # plt.show()


if __name__ == '__main__':
    p = Pool(4)
    workdir = '/luna1/maye/'
    fnames = glob(workdir+'*.h5')
    fnames.sort()
    try:
        col_str = sys.argv[1]
        i_start, i_end = [int(i) for i in sys.argv[2:]]
    except (IndexError, ValueError):
        print('Provide "data_col i_start i_end" to work on.')
        sys.exit()
    fnames_and_col_str = [(fname, col_str) for fname in fnames]
    p.map(process_fname, fnames_and_col_str[i_start:i_end])
