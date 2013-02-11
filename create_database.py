import pipetools as pt
import pandas as pd
import os
import sys
import numpy as np
import glob
import diviner as div
from divconstants import *
from scipy import ndimage as nd
from matplotlib.pylab import title

def get_sv_selector(df):
    return (df.last_az_cmd >= SV_AZ_MIN) & (df.last_az_cmd <= SV_AZ_MAX) & \
           (df.last_el_cmd >= SV_EL_MIN) & (df.last_el_cmd <= SV_EL_MAX)

def get_bb_selector(df):
    return (df.last_az_cmd >= BB_AZ_MIN) & (df.last_az_cmd <= BB_AZ_MAX) & \
           (df.last_el_cmd >= BB_EL_MIN) & (df.last_el_cmd <= BB_EL_MAX)
    
def get_st_selector(df):
    return (df.last_az_cmd >= ST_AZ_MIN) & (df.last_az_cmd <= ST_AZ_MAX) & \
           (df.last_el_cmd >= ST_EL_MIN) & (df.last_el_cmd <= ST_EL_MAX)

def get_stowed_selector(df):
    return (df.last_az_cmd == 0) & (df.last_el_cmd == 0)
    
def define_sdtype(df):
    df['sdtype'] = 0
    df.sdtype[get_sv_selector(df)] = 1
    df.sdtype[get_bb_selector(df)] = 2
    df.sdtype[get_st_selector(df)] = 3
    df.sdtype[get_stowed_selector(df)] = -2
    # the following defines the sequential list of calibration blocks inside
    # the dataframe. nd.label provides an ID for each sequential part where
    # the given condition is true.
    # this still includes the moving areas, because i want the sv and bbv
    # attached to each other to deal with them later as a separate calibration
    # block
    # DECISION: block labels contain moving data as well
    # below defined "is_xxx" do NOT contain moving data.
    df['calib_block_labels'] = nd.label( (df.sdtype==1) | (df.sdtype==2) | (df.sdtype==3))[0]
    df['sv_block_labels'] = nd.label( df.sdtype==1 )[0]
    df['bb_block_labels'] = nd.label( df.sdtype==2 )[0]
    df['st_block_labels'] = nd.label( df.sdtype==3 )[0]
    
    # this resets data from sdtypes >0 above that is still 'moving' to be 
    # sdtype=-1 (i.e. 'moving', defined by me)
    df.sdtype[df.moving==1] = -1
    
    # now I don't need to check for moving anymore, the sdtypes are clean
    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview']    = (df.sdtype == 2)
    df['is_stview']    = (df.sdtype == 3)
    df['is_moving']    = (df.sdtype == -1)
    df['is_stowed']    = (df.sdtype == -2)
    df['is_calib'] = df.is_spaceview | df.is_bbview | df.is_stview

    # this does the same as above labeling, albeit here the blocks are numbered
    # individually. Not sure I will need it but might come in handy.

def parse_descriptor(fpath):
    f = open(fpath)
    lines = f.readlines()
    f.close()
    s = pd.Series(lines)
    s = s.drop(0)
    val = s[1]
    val2 = val.split(' ')
    [i.strip().strip("'") for i in val2]
    def unpack_str(value):
        val2 = value.split(' ')
        t = [i.strip().strip("'") for i in val2]
        return t[0].lower()
    columns = s.map(unpack_str)
    keys = columns.values
    rec_dtype = np.dtype([(key,'f8') for key in keys])
    return rec_dtype,keys

def get_div247_dtypes():
    if 'darwin' in sys.platform:
        despath = '/Users/maye/data/diviner/div247/div247.des'
    else:
        despath = '/s3/marks/div247/div247.des'
    return parse_descriptor(despath)
    
def prepare_data(df_in):
    """Declare NaN value and pad nan data for some."""
    nan = np.nan
    df = div.index_by_time(df_in)
    df[df==-9999.0] = nan
    df.last_el_cmd.replace(nan,inplace=True)
    df.last_az_cmd.replace(nan,inplace=True)
    df.moving.replace(nan,inplace=True)
    return df

def plot_calib_block(df,label,id,det='a6_11'):
    dfnow = df[df[label]==id]
    dfnow['moving']= dfnow[dfnow.is_moving][det]
    dfnow['sv']=dfnow[dfnow.is_spaceview][det]
    dfnow['bb']=dfnow[dfnow.is_bbview][det]
    dfnow['st']=dfnow[dfnow.is_stview][det]
    dfnow[['st','sv','bb','moving']].plot(style='.',linewidth=2)
    title(det)

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
    
def get_storename(folder):
    path = os.path.realpath(folder)
    dirname = '/raid1/maye/data/div247'
    basename = os.path.basename(path)
    storename = os.path.join(dirname,basename+'.h5')
    return storename

def fname_to_df(fname,rec_dtype,keys):
    with open(fname) as f:
        data = np.fromfile(f,dtype=rec_dtype)
    df = pd.DataFrame(data,columns=keys)
    return df
    
class DataPump(object):
    rec_dtype, keys  = get_div247_dtypes()
    def get_fnames(self):
        dirname = os.path.dirname(self.fname)
        fnames = glob.glob(dirname + '/*.div247')
        fnames.sort()
        self.fnames = fnames
        self.index = self.fnames.index(self.fname)
    def open_and_process(self):
        df = fname_to_df(self.fname, self.rec_dtype, self.keys)
        df = prepare_data(df)
        define_sdtype(df)
        self.df = df
    def get_df(self,fname):
        self.fname = fname
        self.get_fnames()
        self.open_and_process()
        return self.df
    def get_next(self):
        self.fname = self.fnames[self.index+1]
        self.index+=1
        self.open_and_process()
        return self.df

def folder_to_df(folder, top_end=None, verbose=False):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder+'/*.div247')
    fnames.sort()
    if not top_end:
        top_end = len(fnames)
    dfall = pd.DataFrame()
    olddf = None
    for i,fname in enumerate(fnames[:top_end]):
        if verbose:
            if i*100/top_end % 10 ==0:
                print("{0:g} %".format(float(i)*100/top_end))
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        if olddf is not None:
            for s in df.filter(regex='_labels'):
                df[s] += olddf[s].max()
        olddf = df
        dfall = pd.concat([dfall,df])
    to_store = dfall[dfall.calib_block_labels>0]
    return to_store
        
def folder_to_store(folder):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder+'/*.div247')
    if not fnames:
        print "Found no files."
        return
    fnames.sort()
    # opening store in overwrite-mode
    storename = get_storename(folder)
    print storename
    store = pd.HDFStore(storename,mode='w')
    nfiles = len(fnames)
    olddf = None
    for i,fname in enumerate(fnames):
        print round(float(i)*100/nfiles,1),'%'
        df = fname_to_df(fname, rec_dtype, keys)
        df = prepare_data(df)
        define_sdtype(df)
        to_store = df[df.calib_block_labels>0]
        if olddf is not None:
            for s in to_store.filter(regex='_labels'):
                to_store[s] += olddf[s].max()
        olddf = to_store
        store.append('df',to_store )
    print "Done."
    store.close()

if __name__ == '__main__':
    folders = glob.glob('/Volumes/divaye/divdata/2011*')
    print folders
    for folder in folders:
        if os.path.isdir(folder):
            main(folder)