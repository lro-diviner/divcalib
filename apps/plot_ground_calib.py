from __future__ import print_function, division
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import timedelta

root = '/raid1/maye/ground_calib/'

df = pd.read_hdf(root+'gc_a6_b1_b2_b3.h5','df')

print(df.info())

fig, ax = plt.subplots(figsize=(80,10))

fmt = '%Y%m%d %H:%M:%S'
deltahours = timedelta(hours=12)
start = pd.Timestamp('20080110 21:00:00')

def do_plot(df, ax, ymin, ymax):
    df[df < ymin] = np.nan
    df[df > ymax] = np.nan
    df.plot(rasterized=True, ax=ax)

while True:
    end = start + deltahours
    print(start,end)
    fig, axes = plt.subplots(nrows=2, figsize=(120, 4))
    roi = df[start.strftime(fmt):end.strftime(fmt)]
    if len(roi) == 0:
        break
    roi = roi.resample('1s')
    do_plot(roi['a6_11'], axes[0], 17000, 32000)
    do_plot(roi['b1_11 b2_11 b3_11'.split()], axes[1], 21000, 32000)
    fmt2 = '%Y%m%d%H'
    fname = 'gc_a6_b1_b2_b3_d11_'+start.strftime(fmt2)+'-' + end.strftime(fmt2) + '.png'
    plt.savefig(fname, dpi=200)
    print("Created",fname)
    start = start + deltahours
print('Done.')

