import glob
import pandas
from multiprocessing import Pool
from noise import fix_columns

fnames = glob.glob('/luna1/maye/*.h5')

def fixing_columns(fname):
    print 'Doing',fname
    store = pandas.HDFStore(fname)
    df = store[store.keys()[0]]
    fix_columns(df)
    store[store.keys()[0]]=df
    store.close()

p = Pool(4)

p.map(fixing_columns,fnames)

 
