#!/usr/bin/env python
import os
import glob
from pipetools import des2hdf
import subprocess as sp
from multiprocessing import Pool
from pipetools import parse_des_header
import numpy as np
import pandas
import time

# working only with the testdata range that was provided by JPL
# this is only done to define the time range
# the data itself is provided by the rdrp tool from Mark
srcdir = '/raid1/marks/feidata/DIV:instTestRdr/data'

# only save in 
destdir = '/luna1/maye'

# sourcefiles from where the timestamps of interest are determined
fpaths = glob.glob(srcdir+'/*.zip')

# descriptor files that have not been converted to hdf yet
despaths = glob.glob(destdir+'/*.des')

def rdrp2hdf(fpath):
    """Again, fpath/fname only used to define the time-stamp for rdrp."""
    fname = os.path.basename(fpath)
    timestamp = fname.split('_')[0]
    if os.path.exists(os.path.join(destdir,timestamp+'.h5')):
        print timestamp,'exists.'
        return
    newfname = os.path.join(destdir,timestamp+'.des')
    cmd = 'rdrp daterange=' + timestamp
    print(cmd)
    proc = sp.Popen(cmd, stdout = sp.PIPE, shell=True)

    d = parse_des_header(proc.stdout)
    rec_dtype = np.dtype([(key,'f8') for key in d.keys()])

    data = bytearray(proc.stdout.read())
    print('\nStarting the read of {0}'.format(timestamp))
    t1 = time.time()
    ndata = np.frombuffer(data, dtype = rec_dtype)
    print("Reading time: {0}".format(time.time()-t1))
    print ndata.shape
    df = pandas.DataFrame(ndata)
    newfname = os.path.join('/luna1/maye',timestamp+'.h5')
    print 'New filename:',newfname
    store = pandas.HDFStore(newfname,'w')
    store[timestamp] = df
    store.close()
    
pool = Pool(3)
if despaths:
    print "Found des files. First converting them:", despaths
    pool.map(des2hdf, despaths)
pool.map(rdrp2hdf, fpaths)    

    