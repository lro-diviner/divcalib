#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, print_function
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.pyplot import cm
import matplotlib.pyplot as plt
import numpy as np


def get_store_data(kind, chid, term):
    store = pd.HDFStore('/raid1/maye/rdr20_month_samples/'+
                        kind+'/'+chid+'.h5')
    mine = store.select('df', [pd.Term(term)], 
                        columns=['clat','clon','cloctime','tb'])
    store.close()
    return mine


class Histogrammer(object):
    """docstring for Histogrammer"""
    def __init__(self, df, basemap, gridpts = 1000):
        super(Histogrammer, self).__init__()
        lats = df.clat
        lons = df.clon
        tb = df.tb
        # convert to map projection coordinates.
        x1, y1 = basemap(lons, lats)

        # remove points outside projection limb.
        x = np.compress(np.logical_or(x1 < 1.e20,y1 < 1.e20), x1)
        y = np.compress(np.logical_or(x1 < 1.e20,y1 < 1.e20), y1)
        tb = np.compress(np.logical_or(x1 < 1.e20, y1<1.e20), tb)

        print('Histogramming.')
        bincount, xedges, yedges = np.histogram2d(x, y, bins=gridpts)
        mask = bincount == 0
        bincount = np.where(bincount == 0, 1, bincount)
        H, self.xedges, self.yedges = np.histogram2d(x,y, bins=gridpts, weights=tb)
        self.H = np.ma.masked_where(mask, H/bincount)
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
        kind, chid, dayside = strings
        if not ax:
            fig, ax = plt.subplots()
        self.palette.set_bad(ax.get_axis_bgcolor(), 1.0)
        CS = self.basemap.pcolormesh(hdata.xedges, hdata.yedges, hdata.H.T,
                               shading='flat', cmap=self.palette,
                               ax = ax, vmin=vmin, vmax=vmax)
        self.basemap.colorbar(CS,ax=ax)
        ax.set_title(' '.join([self.pole, chid, kind, dayside]))
        plt.savefig('_'.join(['southpole', chid, kind, str(self.gridpts),
                              dayside]) + '.png', dpi=300)

    def create_multimap(self, data, strings):
        n = len(data)
        fig, ax = plt.subplots(1, n)
        for i,d in enumerate(data):
            self.create_map(d, strings[i], ax.flatten()[i])


def split_day_night(df):
    night = df[(df.cloctime > 18) | (df.cloctime < 6)]
    day = df[(df.cloctime < 18) & (df.cloctime > 6)]      
    return day, night
    
    
###
# setup
###
bounding_lat = -85
blat = bounding_lat
kind='no_rad_corr'
chid = 'C9'
timeofday = 'day'
term = 'clat {0} {1}'.format('<' if blat < 0 else '>', blat)

# get divdata
store = pd.HDFStore('/u/paige/maye/rdr20_month_samples/divdata.h5')

# get my data
print("Reading HDF file.")
mine = get_store_data(kind, chid, term)
print("Done reading.")

mine_day, mine_night = split_day_night(mine)
mines = {'day': mine_day, 'night': mine_night}

# create south polar stereographic basemapper
mapper = PoleMapper(blat, (kind, chid), round=False)
histogrammer1 = Histogrammer(store['old_' + timeofday], mapper.basemap)
histogrammer2 = Histogrammer(mines[timeofday], mapper.basemap)

print(len(histogrammer1.yedges), len(histogrammer2.yedges))
mapper.create_multimap((histogrammer1,histogrammer2),
                       (('divdata', chid, timeofday),
                        (kind, chid, timeofday)))

store.close()

plt.show()

# Hdiff = Hold-Hmine
