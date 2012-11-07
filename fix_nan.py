import glob
import pandas
import numpy as np
from multiprocessing import Pool

fnames = glob.glob('/luna1/maye/*.h5')

def fixing_nan(fname):
    print 'Doing',fname
    store = pandas.HDFStore(fname)
    df = store[store.keys()[0]]
    df[df==-9999.0]=np.nan
    store[store.keys()[0]]=df
    store.close()

p = Pool(8)

p.map(fixing_nan,fnames[1:])

 
