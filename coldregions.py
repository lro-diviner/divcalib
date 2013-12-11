# -*- coding: utf-8 -*-
import pandas as pd
from diviner import file_utils as fu, data_prep as dp, calib, plot_utils as pu
import numpy as np

root = "/raid1/maye/coldregions/"

sps = []
for region in '1 3 5'.split():
    fname = root + 'region_sp' + region + '_9.txt'
    sps.append(pd.read_csv(fname, sep='\s*'))


def get_l1a_timestring(val):
    dt = val.to_pydatetime()
    return dt.strftime("%Y%m%d%H")

for df in sps:
    df.second = np.round(df.second * 1000) / 1000
    for col in ['year', 'month','date','hour','minute','det']:
        df[col] = df[col].astype('int')
    for col in ['year', 'month','date','hour','minute','second']:
        df[col] = df[col].astype('string')
    df.index = pd.to_datetime(df.year + '-' + df.month + '-' + df.date + ' ' +
               df.hour + ':' + df.minute + ':' + df.second, utc=True)
    df['filetimestr'] = df.index.map(get_l1a_timestring)


def get_tb_from_timestr(t):
    l1a = fu.L1ADataFile.from_timestr(t)
    df = fu.open_and_accumulate(l1a.fname)
    c = calib.Calibrator(df)
    c.calibrate()
    return c.Tb


def process_one_timestring(region_now, newtb):
    dets = region_now.det.unique()
    container = []
    for det in dets:
        detstr = 'b3_' + str(det).zfill(2)
        subdf = region_now[region_now.det == det]
        joined = subdf.join(newtb[detstr], how='inner')
        container.append(joined.rename(columns= lambda x: 'newtb' if x.startswith('b3_') \
                                                                    else x))
    newregion = pd.concat(container)
    return newregion


def process_one_region(region):
    timestrings = region.filetimestr.unique()
    container = []
    for i,t in enumerate(timestrings):
        print
	print t
	print i, 'of', len(timestrings)
        tb = get_tb_from_timestr(t)
        region_now = region[region.filetimestr == t]
        container.append(process_one_timestring(region_now, tb))
    return pd.concat(container)


for sp, region in zip(sps,'1 3 5'.split()):
    newsp = process_one_region(sp)
    newsp.to_hdf(root + 'region_sp_newtb_added.h5', 'sp' + region)
