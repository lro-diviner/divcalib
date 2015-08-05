#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.pyplot import cm
from mpl_toolkits.basemap import Basemap

from diviner import file_utils as fu


def get_store_data(mode, chid, term):
    store = pd.HDFStore('/raid1/maye/rdr20_month_samples/' +
                        mode + '/' + chid + '.h5')
    if 'm' not in chid:  # if no m85 in chid, no need for pd.Term
        mine = store.select('df', [pd.Term(term)],
                            columns=['clat', 'clon', 'cloctime', 'tb'])
    else:
        mine = store.select('df')
    store.close()
    return mine


class Histogrammer(object):
    """docstring for Histogrammer"""
    def __init__(self, df, basemap, gridpts=1000):
        super(Histogrammer, self).__init__()
        lats = df.clat
        lons = df.clon
        tb = df.tb
        # convert to map projection coordinates.
        x1, y1 = basemap(lons, lats)

        # remove points outside projection limb.
        x = np.compress(np.logical_or(x1 < 1.e20, y1 < 1.e20), x1)
        y = np.compress(np.logical_or(x1 < 1.e20, y1 < 1.e20), y1)
        tb = np.compress(np.logical_or(x1 < 1.e20, y1 < 1.e20), tb)

        print('Histogramming.')
        bincount, xedges, yedges = np.histogram2d(x, y, bins=gridpts)
        mask = bincount == 0
        bincount = np.where(bincount == 0, 1, bincount)
        H, self.xedges, self.yedges = np.histogram2d(x, y, bins=gridpts, weights=tb)
        self.H = np.ma.masked_where(mask, H / bincount)
        print('Done histogramming.')


class PoleMapper(object):
    """docstring for PoleMapper"""

    palette = cm.jet

    def __init__(self, blat, strings, gridpts=1000, round=True):
        super(PoleMapper, self).__init__()
        self.blat = blat
        self.gridpts = gridpts
        self.basemap = Basemap(lon_0=180, boundinglat=blat,
                               projection='spstere', round=round)
        self.pole = 'Southpole' if blat < 0 else 'Northpole'

    def create_map(self, hdata, strings, ax=None, vmin=None, vmax=None):
        mode, chid, dayside = strings
        if not ax:
            fig, ax = plt.subplots()
        self.palette.set_bad(ax.get_axis_bgcolor(), 1.0)
        CS = self.basemap.pcolormesh(hdata.xedges, hdata.yedges, hdata.H.T,
                                     shading='flat', cmap=self.palette,
                                     ax=ax, vmin=vmin, vmax=vmax)
        self.basemap.drawparallels(np.arange(-90, -85), latmax=-90, ax=ax,
                                   labels=[1, 1, 1, 1])
        self.basemap.drawmeridians(np.arange(0, 360, 30), latmax=-90, ax=ax,
                                   labels=[1, 1, 1, 1])
        self.basemap.colorbar(CS, ax=ax)
        ax.set_title(' '.join([self.pole, chid, mode, dayside]))
        plt.savefig('_'.join(['southpole', chid, mode, str(self.gridpts),
                              dayside]) + '.png', dpi=300)

    def create_multimap(self, data, strings):
        n = len(data)
        fig, ax = plt.subplots(1, n)
        for i, d in enumerate(data):
            self.create_map(d, strings[i], ax.flatten()[i])


def split_day_night(df):
    night = df[(df.cloctime > 18) | (df.cloctime < 6)]
    day = df[(df.cloctime < 18) & (df.cloctime > 6)]
    return day, night


def get_data_from_hour(mode, ch, timestr):
    ch = ch[:2]
    dirname = fu.get_month_sample_path_from_mode(mode)
    fname = '_'.join([timestr, ch, mode, 'RDR20'])
    fname += '.csv'
    return pd.io.parsers.read_csv(os.path.join(dirname, fname))

###
# setup
###
bounding_lat = -88
blat = bounding_lat
try:
    mode, timeofday, timestr = sys.argv[1:4]
except ValueError:
    print("Usage: {0} mode day|night timestr".format(sys.argv[0]))
    sys.exit()
# abusing for proper plot title
chid = 'C9'
term = 'clat {0} {1}'.format('<' if blat < 0 else '>', blat)

# get divdata
# store = pd.HDFStore('/u/paige/maye/rdr20_month_samples/divdata.h5')
store = pd.HDFStore('/u/paige/maye/rdr20_month_samples/'
                    '2013030101_clat_clon_cloctime_tb_divdata.h5')

# get my data
print("Reading new data.")
# mine = get_store_data(mode, chid, term)
# mine = get_data_from_hour(mode, chid, timestr)
# mine = mine[mine.clat < blat]
# mine_day, mine_night = split_day_night(mine)
# mines = {'day': mine_day, 'night': mine_night}
print("Done reading.")

old_day, old_night = split_day_night(store['df'])
olds = {'day': old_day, 'night': old_night}

# create south polar stereographic basemapper
mapper = PoleMapper(blat, (mode, chid), round=True, gridpts=4000)
histogrammer1 = Histogrammer(olds[timeofday], mapper.basemap, gridpts=120)
# histogrammer2 = Histogrammer(mines[timeofday], mapper.basemap, gridpts=120)

# print(len(histogrammer1.yedges), len(histogrammer2.yedges))
# mapper.create_multimap((histogrammer1,histogrammer2),
#                        (('divdata', chid, timeofday),
#                         (mode, chid, timeofday)))
mapper.create_map(histogrammer1, (mode, chid, timestr + '_' + timeofday))

store.close()

plt.show()

# Hdiff = Hold-Hmine
