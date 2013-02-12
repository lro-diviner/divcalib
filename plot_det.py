#!/usr/bin/env python
from create_database import DataPump
import pandas as pd
from matplotlib.pylab import show
import sys

datadir = '/luna1/maye/data/div247/'

def get_sv_mean(df):
    dfhere = df[df.is_spaceview]
    return dfhere['a3_11'].mean()

def main(start,end, det):
    pump = DataPump()
    dr = list(pd.date_range(start=start+'01',end=end+'01'))
    months = [i.strftime("%Y%m") for i in dr]

    l = []
    for month in months:
        print 'Working on',month
        store = pump.get_month_h5(str(month))
        df = store.select('df',columns=[det,'calib_block_labels','is_spaceview'])
        l.append(df.groupby(df.calib_block_labels).apply(get_sv_mean))
        store.close()
    
    df = pd.concat(l,ignore_index=True)
    df.save(det+'_'+start+'_'+end+'.df')
    
    df.plot(style='.-')
    show()

if __name__ == '__main__':
    det = None
    try:
        start, end, det  = sys.argv[1:]
    except:
        try:
            det = 'a3_11'
            print 'Using default detector:',det
            start, end = sys.argv[1:]
        except:
            print "Usage: {0} startmonth endmonth".format(sys.argv[0])
            sys.exit()
    main(start,end,det)