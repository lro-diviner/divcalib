# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>
from __future__ import division, print_function
from matplotlib.pylab import *
from diviner import file_utils as fu
from diviner import calib
import pandas as pd
from diviner import file_utils as fu

rcParams['figure.figsize'] = (14, 10)


class HotOrbits(object):
    """docstring for HotOrbits"""
    savepath = '/Users/maye/Dropbox/DDocuments/DIVINER/calib/hot_orbits/jpl_meeting/'

    def __init__(self, ch2study, df):
        super(HotOrbits, self).__init__()
        self.ch2study = ch2study
        self.df = df
        
        # my calibration
        c = calib.Calibrator(df, pad_bbtemps=True, single_rbb=False)
        c.calibrate()
        
        # get only Tb
        Tb_all = calib.get_data_columns(c.Tb)
        Tb = Tb_all.filter(regex=ch2study + '_')
        
        # make all detectors integer numbers
        Tb = Tb.rename(columns=lambda x: int(x[3:]))
        self.Tb = Tb
        self.chmedian = Tb.apply(lambda x: x - x.median(), axis=1)
        self.chmean = Tb.apply(lambda x: x - x.mean(), axis=1)
        
    def plot_detectors(self, det_list=[1,11,21]):
        # figure()
        self.Tb[det_list].plot()
        legend()
        ylabel('Tb [K]')
        xlabel('Time [UTC]')
        titlestr = self.ch2study + ' Tb Det 01 11 21'
        title(titlestr)
        savefig(self.savepath + '_'.join(titlestr.split()) + '.png')

    def plot_raw(self, ):
        df = self.df
        ch2study = self.ch2study
        figure()
        col = self.ch2study+'_11'
        # df[col].plot(style='k.', markersize=2, )
        plot(df[col].index, df[col], 'k.', markersize=2)
        # df[df.is_spaceview][col].plot(style='b.', markersize=4)
        plot(df[df.is_spaceview][col].index, 
                df[df.is_spaceview][col], 
                'b.', markersize=4)
        # choffsets[self.ch2study+'_11'].plot(style='b.', markersize=2, )
        plot(df[df.is_bbview][col].index,
                df[df.is_bbview][col], 
                'r.', markersize=2, )
        # chbbs[self.ch2study+'_11'].plot(style='r.', markersize=2, )
        # if len(df[df.is_stview]) is not 0:
        #     df[df.is_stview][col].plot(style='c.', markersize=5, )
        titlestr = ch2study + ' raw  plus marked calib views'
        title(titlestr)
        ylabel('Counts')
        xlabel('Time [UTC')
        savefig(self.savepath + '_'.join(titlestr.split()) + '.png')
    
    def plot_lips(self, kind='mean'):
        Tb = self.Tb.resample('10s')
        if kind == 'median':
            df = self.chmedian
        elif kind == 'mean':
            df = self.chmean
        
        figure()
        for i in range(2, 12):
            df[i].plot(style='r')
        for i in range(12, 22):
            df[i].plot(style='g')
        df[1].plot(style='c')
        legend(ncol=5)
        titlestr = self.ch2study + ' Tb Deviations from {0} detector sides sorted'.format(kind)
        title(titlestr)
        savefig(self.savepath + '_'.join(titlestr.split()) + '.png')
        
    def imshow(self):
        figure(figsize=(21,3))
        imshow(self.Tb.values.T, interpolation='none', aspect='auto')  
        colorbar(orientation='horizontal')
        titlestr = self.ch2study + ' channel image plot'
        title(titlestr)
        savefig(self.savepath + '_'.join(titlestr.split()) + '.png')
        
    def plot_max_deviation_det(self):
        figure()
        chmedian.idxmax(axis=1).plot(style='.')
        xlabel('Time [UTC]')
        ylabel('Detector number')
        tstr = 'Which detector shows the largest deviation from the median'
        title(tstr)
        savefig(self.savepath + '_'.join(tstr.split()) + '.png')
        

class HotOrbitsDivData(HotOrbits):
    def __init__(self, ch2study, Tb):
        self.ch2study = ch2study
        self.Tb = Tb
        self.chmedian = Tb.apply(lambda x: x - x.median(), axis=1)
        self.chmean = Tb.apply(lambda x: x - x.mean(), axis=1)
        
# Orbit 8172: 2011-091T20:43:23 UTC date: 2011-04-01
#

# Channel to study:
ch2study = 'b3'

# get L1A data
pump = fu.Div247DataPump('20110402')
df = pump.get_n_hours_from_t(1, 4)

hotorbits = HotOrbits(ch2study, df)

hotorbits.plot_detectors()

# hotorbits.plot_raw()

hotorbits.imshow()

hotorbits.plot_lips()

# statistics for each channel
# hotorbits.Tb.boxplot()

# or this simple statistic?
# Tb.std()

# df.plot(kind='kde')

divdata = pd.io.parsers.read_csv('/Users/maye/data/diviner/hot_orbit_ch9.txt', sep=r'\s*', names=['year', 'month', 'date', 'hour', 'minute', 'second', 'det', 'tb', 'qca'])

df = fu.index_by_time(divdata)
print("\Index for divdata:", df.index)
print("\nqca: ",df.qca.unique())

df = df.reset_index()
df = df.pivot(index='index', columns='det', values='tb')
df.columns = range(1,22)
divhotorbits = HotOrbitsDivData(ch2study, df)
divhotorbits.plot_detectors()

show()