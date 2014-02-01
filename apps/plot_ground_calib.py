from __future__ import print_function, division
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from datetime import timedelta

root = '/raid1/maye/ground_calib/'

s = pd.read_hdf(root+'gc_b1_11.h5','df')

print(len(s))

fig, ax = plt.subplots(figsize=(80,10))

fmt = '%Y%m%d %H:%M:%S'
deltahours = timedelta(hours=12)
start = pd.Timestamp('20080110 21:00:00')

while True:
    end = start + deltahours
    print(start,end)
    fig, ax = plt.subplots(figsize=(120, 3))
    roi = s[start.strftime(fmt):end.strftime(fmt)]
    if len(roi) == 0:
        break
    roi = roi.resample('1s')
    roi.plot(rasterized=True, ax=ax)
    ymax = roi.mean()*1.1
    ymin = roi.mean()*0.9
    ax.set_ylim([ymin, ymax])
    fmt2 = '%Y%m%d%H'
    fname = 'b1_11_'+start.strftime(fmt2)+'-' + end.strftime(fmt2) + '.png'
    plt.savefig(fname, dpi=200)
    print("Created",fname)
    start = start + deltahours
print('Done.')

