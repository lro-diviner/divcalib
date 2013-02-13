#!/usr/bin/env python
from __future__ import division
from create_database import DataPump
import pandas as pd
from matplotlib.pylab import show
import sys
# from multiprocessing import Pool, Lock
from calib import CalibBlock

datadir = '/luna1/maye/data/div247/'

def get_time(df):
    t1 = df.index[0]
    t2 = df.index[-1]
    t = t1 + (t2-t1)//2
    return t

def get_first_sv_mean(df):
    """function to return mean value for first spaceview only"""
    d = dict(list(df.groupby('sv_block_labels')))
    return d[min(d.keys())].mean()
    
def get_data(month, det, view='is_spaceview', lock=None, container=None):
    print 'Working on',month
    pump = DataPump()
    store = pump.get_month_h5(month)
    df = store.select('df', (view+'=True'), columns=[det,'calib_block_labels'])
    store.close()
    return df

def get_all_dets_per_view(month, view='is_spaceview'):
    print 'Working on',month
    pump = DataPump()
    store = pump.get_month_h5(month)
    df = store.select('df', (view+'=True'))
    store.close()
    return df

def get_months_list(start, end):
    dr = list(pd.date_range(start=start+'01',end=end+'01',freq='M'))
    months = [i.strftime("%Y%m") for i in dr]
    months.append(str(int(months[-1])+1))
    return months
    
def by_det(start,end, det, view='is_spaceview'):
    l = []
    for month in get_months_list(start, end):
        df = get_data(month, det, view)
        grouped = df.groupby(df.calib_block_labels)
        times = grouped[det].apply(get_time)
        means = grouped[det].mean()
        s = pd.DataFrame(means.values, index=times.values, columns=[det])
        l.append(s)
        
    df = pd.concat(l)
    df.save(det+'_'+start+'_'+end+'.df')
    
    df.plot(style='.-')
    show()

def for_all_dets(start,end, view='is_spaceview'):
    l = []
    for month in get_months_list(start, end):
        df = get_all_dets_per_view(month, view)
        grouped = df.groupby(df.calib_block_labels)
        # this just uses any detector to make the calculation potentially faster
        times = grouped.a3_11.apply(get_time)
        # change here for method of means
        means = grouped.agg(get_first_sv_mean)
        means.index = times
        l.append(means)
        
    df = pd.concat(l)
    df.save('all_means'+'_'+view+'_'+start+'_'+end+'.df')
    
    print ("Done.")

if __name__ == '__main__':
    det = None
    try:
        start, end, view, det  = sys.argv[1:]
    except:
        try:
            det = 'a3_11'
            print 'Using default detector:',det
            start, end , view = sys.argv[1:]
        except:
            print "Usage: {0} startmonth endmonth".format(sys.argv[0])
            sys.exit()
    for_all_dets(start,end, view)