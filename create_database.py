import pandas as pd
import os
import glob
from matplotlib.pylab import title


def relabel(inputlist):
    value = 1
    newl = []
    old = None
    for i in inputlist:
        if i == 0:
            newl.append(0)
        elif not old:
            old = i
            newl.append(1)
        elif i == old:
            newl.append(value)
        else:
            value += 1
            old = i
            newl.append(value)
    return newl
  
def add_hdf_data_columns(fname):
    print 'starting',fname
    storeold = pd.HDFStore(fname)
    df = storeold.select('df')
    storeold.close()
    storenew = pd.HDFStore(fname,'w')
    cols1 = [col for col in df.filter(regex='_labels')]
    cols2 = [col for col in df.filter(regex='is_')]
    storenew.append('df',df,data_columns=cols1+cols2)
    storenew.close()
    print fname,'done.'


if __name__ == '__main__':
    folders = glob.glob('/Volumes/divaye/divdata/2011*')
    print folders
    for folder in folders:
        if os.path.isdir(folder):
            main(folder)