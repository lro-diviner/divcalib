#!/usr/bin/env python
# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>


import os
from datetime import timedelta

import matplotlib.pyplot as plt
from diviner import file_utils as fu
from diviner import calib
from matplotlib.pyplot import rcParams, subplots

rcParams['figure.figsize'] = (14, 10)


class HotOrbits(object):

    """docstring for HotOrbits"""
    savepath = os.path.join(fu.outpath, 'hot_orbits')

    def __init__(self, df, title_prefix='', rad_corr=True,
                 new_rad_corr=False, folder=''):
        super(HotOrbits, self).__init__()
        self.df = df
        self.savepath = os.path.join(self.savepath, folder)
        if not os.path.exists(self.savepath):
            os.makedirs(self.savepath)
        self.title_prefix = title_prefix
        self.rad_corr = rad_corr
        self.new_rad_corr = new_rad_corr

        # my calibration
        c = calib.Calibrator(df, do_rad_corr=rad_corr,
                             new_rad_corr=new_rad_corr)
        c.calibrate()
        self.c = c

    def set_ch2study(self, ch):
        ch2study = ch
        self.ch2study = ch
        # get only Tb
        Tb_all = calib.get_data_columns(self.c.Tb)
        Tb = Tb_all.filter(regex=ch2study + '_')

        # make all detectors integer numbers
        Tb = Tb.rename(columns=lambda x: int(x[3:]))

        # cut off first 30 minutes for boundary effects
        t0 = Tb.index[0]
        Tb = Tb.ix[(t0 + timedelta(minutes=30)):]

        self.Tb = Tb.resample('10s')
        self.chmedian = self.Tb.apply(lambda x: x - x.median(), axis=1)
        self.chmean = self.Tb.apply(lambda x: x - x.mean(), axis=1)

    def plot_detectors(self, det_list=None):
        if det_list is None:
            det_list = [1, 11, 21]
        fig, ax = subplots()

        self.Tb[det_list].plot(ax=ax)
        ax.legend()
        ax.set_ylabel('Tb [K]')
        ax.set_xlabel('Time [UTC]')
        ax.set_ylim(ymin=-100, ymax=450)
        corr_string = self.get_corr_string()
        titlestr = '{0} Tb Det 01 11 21 {1}'.format(self.ch2study, corr_string)
        ax.set_title(' '.join([self.title_prefix, titlestr]))
        savestring = os.path.join(self.savepath, '_'.join(titlestr.split()) + '.png')
        print(savestring)
        fig.savefig(savestring, dpi=200)

    def get_save_string(self):
        corr_string = self.get_corr_string()
        titlestr = '{0} Tb Det 01 11 21 {1}'.format(self.ch2study, corr_string)
        savestring = os.path.join(self.savepath, '_'.join(titlestr.split()) + '.png')
        return savestring

    def plot_raw(self, ):
        df = self.df
        ch2study = self.ch2study
        plt.figure()
        col = self.ch2study+'_11'
        # df[col].plot(style='k.', markersize=2, )
        plt.plot(df[col].index, df[col], 'k.', markersize=2)
        # df[df.is_spaceview][col].plot(style='b.', markersize=4)
        plt.plot(df[df.is_spaceview][col].index,
                 df[df.is_spaceview][col],
                 'b.', markersize=4)
        # choffsets[self.ch2study+'_11'].plot(style='b.', markersize=2, )
        plt.plot(df[df.is_bbview][col].index,
                 df[df.is_bbview][col],
                 'r.', markersize=2, )
        # chbbs[self.ch2study+'_11'].plot(style='r.', markersize=2, )
        # if len(df[df.is_stview]) is not 0:
        #     df[df.is_stview][col].plot(style='c.', markersize=5, )
        titlestr = ch2study + ' raw  plus marked calib views'
        plt.title(' '.join([self.title_prefix, titlestr]))
        plt.ylabel('Counts')
        plt.xlabel('Time [UTC')
        plt.savefig(os.path.join(self.savepath, '_'.join(titlestr.split()) + '.png'))

    def get_corr_string(self):
        if self.rad_corr:
            if self.new_rad_corr:
                corr_string = 'new_correction'
            else:
                corr_string = 'old_corrections'
        else:
            corr_string = 'uncorrected'
        return corr_string

    def plot_lips(self, kind='mean', separate=True):

        fig, ax = subplots()

        if kind == 'median':
            df = self.chmedian
        elif kind == 'mean':
            df = self.chmean

        if separate:
            for i in range(1, 12):
                df[i].plot(style='r', ax=ax)
            for i in range(12, 22):
                df[i].plot(style='g', ax=ax)
            df[20].plot(style='k', ax=ax)
        else:
            df.plot(ax=ax)
        ax.legend(ncol=5, loc='lower right')
        ax.set_ylim(ymin=-80, ymax=80)

        corr_string = self.get_corr_string()
        titlestr = self.ch2study + \
            ' Tb Deviations from {0} detector sides sorted_{1}'.format(kind, corr_string)
        ax.set_title(' '.join([self.title_prefix, titlestr]))
        savestring = os.path.join(self.savepath, '_'.join(titlestr.split()) + '.png')
        print(savestring)
        fig.savefig(savestring, dpi=200)

    def imshow(self):
        plt.figure(figsize=(21, 3))
        plt.imshow(self.Tb.values.T, interpolation='none', aspect='auto')
        plt.colorbar(orientation='horizontal')
        titlestr = self.ch2study + ' channel image plot'
        plt.title(' '.join([self.title_prefix, titlestr]))
        plt.savefig(os.path.join(self.savepath, '_'.join(titlestr.split()) + '.png'))

    def plot_max_deviation_det(self):
        plt.figure()
        self.chmedian.idxmax(axis=1).plot(style='.')
        plt.xlabel('Time [UTC]')
        plt.ylabel('Detector number')
        tstr = 'Which detector shows the largest deviation from the median'
        plt.title(' '.join([self.title_prefix, tstr]))
        plt.savefig(os.path.join(self.savepath, '_'.join(tstr.split()) + '.png'))

    def plot_kde(self):
        self.Tb.plot(kind='kde')
        plt.legend()
        tstr = 'Detector KDEs'
        plt.title(' '.join([self.title_prefix, tstr]))
        plt.savefig(os.path.join(self.savepath + '_'.join(tstr.split()) + '.png'))

    def plot_gains_interp(self):
        self.c.gains_interp.plot(style='*')
        plt.savefig(os.path.join(self.savepath + 'gains_interp.png'))


class HotOrbitsDivData(HotOrbits):

    def __init__(self, ch2study, Tb, title_prefix=""):
        self.ch2study = ch2study
        self.Tb = Tb
        self.chmedian = Tb.apply(lambda x: x - x.median(), axis=1)
        self.chmean = Tb.apply(lambda x: x - x.mean(), axis=1)
        self.savepath = os.path.join(self.savepath, 'divdata_')
        self.title_prefix = title_prefix
####
# start of script
####

# get L1A data
timestr = '2011041600'
offset = 4
pump = fu.Div247DataPump(timestr)
df = pump.get_n_hours_from_t(6, offset)

objects = []
objects.append(HotOrbits(df, timestr + str(offset),
                         rad_corr=True, new_rad_corr=True, folder=timestr))
objects.append(HotOrbits(df, timestr + str(offset),
                         rad_corr=False, new_rad_corr=False, folder=timestr))
# objects.append(HotOrbits(df, timestr + str(offset),
#                              rad_corr=True, new_rad_corr=False, folder=timestr))

detectors = ['a3', 'a4', 'a5', 'a6', 'b1', 'b2', 'b3']
#detectors = ['b1','b2','b3']
for ch in detectors:
    print("\nDoing", ch)
    for obj in objects:
        obj.set_ch2study(ch)
        obj.plot_detectors()
        obj.plot_lips(kind='mean', separate=True)
        plt.close('all')

# hotorbits.plot_raw()
# hotorbits.imshow()
# hotorbits.plot_max_deviation_det()
# hotorbits.plot_kde()
# hotorbits.plot_gains_interp()

# statistics for each channel
# hotorbits.Tb.boxplot()

# or this simple statistic?
# Tb.std()

# divdata = pd.io.parsers.read_csv('/Users/maye/data/diviner/hot_orbit_ch9.txt', sep=r'\s*', names=['year', 'month', 'date', 'hour', 'minute', 'second', 'det', 'tb', 'qca'])
#
# df = fu.index_by_time(divdata)
# print("\Index for divdata:", df.index)
# print("\nqca: ",df.qca.unique())
#
# df = df.reset_index()
# df = df.pivot(index='index', columns='det', values='tb')
# df.columns = range(1,22)
# divhotorbits = HotOrbitsDivData(ch2study, df, timestr + str(offset) + '_divdata')
# divhotorbits.plot_detectors()
# divhotorbits.imshow()
# divhotorbits.plot_max_deviation_det()
# divhotorbits.plot_kde()

# show()
