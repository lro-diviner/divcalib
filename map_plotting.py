# -*- coding: utf-8 -*-
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib import cm
from numpy import histogram2d, ma

def get_store_data(kind, chid, term):
    store = pd.HDFStore('/raid1/maye/rdr20_month_samples/'+
                        kind+'/'+chid+'.h5')
    mine = store.select('df', [pd.Term(term)], 
                        columns=['clat','clon','cloctime','tb'])
    store.close()
    return mine


def get_x_y_tb(m, df):
    lats = df.clat
    lons = df.clon
    tb = df.tb
    # convert to map projection coordinates.
    x1, y1 = m(lons, lats)

    # remove points outside projection limb.
    x = np.compress(np.logical_or(x1 < 1.e20,y1 < 1.e20), x1)
    y = np.compress(np.logical_or(x1 < 1.e20,y1 < 1.e20), y1)
    tb = np.compress(np.logical_or(x1 < 1.e20, y1<1.e20), tb)
    return x, y, tb


def get_H_xedges_yedges(x, y, tb):
    bincount, xedges, yedges = histogram2d(x,y,bins=gridpts)
    mask = bincount == 0
    bincount = where(bincount == 0, 1, bincount)
    H, xedges, yedges = histogram2d(x,y, bins=gridpts, weights=tb)
    H = ma.masked_where(mask, H/bincount)
    return H, xedges, yedges


###
# setup
###
palette = cm.jet
bounding_lat = -85
blat = bounding_lat
gridpts = 1000
kind='no_rad_corr'
chid = 'C9'
term = 'clat {0} {1}'.format('<' if blat < 0 else '>', blat)

# get divdata
old = pd.io.parsers.read_csv('/raid1/maye/201303_C9_divdata_m90_m85_clat_'
                             'clon_cloctime_tb.txt',sep='\s+',
                       skipinitialspace=True, names=['clat','clon','cloctime','tb'])

old_night = old[(old.cloctime > 18) | (old.cloctime < 6)]
old_day = old[(old.cloctime < 18) & (old.cloctime > 6)]

# get my data
mine = get_store_data(kind, chid, term)
mine_night = mine[(mine.cloctime > 18) | (mine.cloctime < 6)]
mine_day = mine[(mine.cloctime < 18 ) & (mine.cloctime > 6) ]

# create south polar stereographic basemap
m = Basemap(lon_0=180, boundinglat=bounding_lat, projection='spstere',round=True)

xold,yold,tbold = get_x_y_tb(m, old_day)
xmine, ymine, tbmine = get_x_y_tb(m, mine_day)

Hold, xeold, yeold = get_H_xedges_yedges(xold, yold, tbold)
Hmine, xemine, yemine = get_H_xedges_yedges(xmine, ymine, tbmine)


Hdiff = Hold-Hmine

ax = gca()
palette.set_bad(ax.get_axis_bgcolor(), 1.0)
CS = m.pcolormesh(xedges, yedges, H.T, shading='flat',cmap=palette,
                  #vmax=4,vmin=-4,
                  )
m.colorbar()
savefig('_'.join(['southpole',chid,kind,str(gridpts),'old','day'])+'.png',dpi=300)




