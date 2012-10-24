#!/usr/bin/env python
import os
import glob
from pipetools import des2hdf
from subprocess import call
from multiprocessing import Pool

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
    cmd = 'rdrp daterange=' + timestamp + ' > ' + newfname
    print(cmd)
    call(cmd, shell=True)
    print("Produced {}.des".format(timestamp))
    des2hdf(newfname)
    
pool = Pool(3)
if despaths:
    print "Found des files. First converting them:", despaths
    pool.map(des2hdf, despaths)
pool.map(rdrp2hdf, fpaths)    

    