import pipetools as pt
import pandas as pd
import os
import numpy as np
import glob
import diviner as div
from divconstants import *
from scipy import ndimage as nd

def define_sdtype(df):
    
    sv_selector = (df.last_az_cmd >= SV_AZ_MIN) & (df.last_az_cmd <= SV_AZ_MAX) & \
                  (df.last_el_cmd >= SV_EL_MIN) & (df.last_el_cmd <= SV_EL_MAX)
    bb_selector = (df.last_az_cmd >= BB_AZ_MIN) & (df.last_az_cmd <= BB_AZ_MAX) & \
                  (df.last_el_cmd >= BB_EL_MIN) & (df.last_el_cmd <= BB_EL_MAX)
    st_selector = (df.last_az_cmd >= ST_AZ_MIN) & (df.last_az_cmd <= ST_AZ_MAX) & \
                  (df.last_el_cmd >= ST_EL_MIN) & (df.last_el_cmd <= ST_EL_MAX)
    df['sdtype'] = 0
    df.sdtype[sv_selector] = 1
    df.sdtype[bb_selector] = 2
    df.sdtype[st_selector] = 3
    
    # the following defines the sequential list of calibration blocks inside
    # the dataframe. nd.label provides an ID for each sequential part where
    # the given condition is true.
    # this still includes the moving areas, because i want the sv and bbv
    # attached to each other to deal with them later as a separate calibration
    # block
    df['calib_block_labels'] = nd.label( (df.sdtype==2) | (df.sdtype==1) )[0]
    
    # this resets data from sdtypes >0 above that is still 'moving' to be 
    # sdtype=-1 (i.e. 'moving', defined by me)
    df.sdtype[df.moving==1] = -1
    
    # now I don't need to check for moving anymore, the sdtypes are clean
    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview']    = (df.sdtype == 2)
    df['is_stview']    = (df.sdtype == 3)
    df['is_moving']    = (df.sdtype == -1)
    df['is_calib'] = df.is_spaceview | df.is_bbview | df.is_stview

    # this does the same as above labeling, albeit here the blocks are numbered
    # individually. Not sure I will need it but might come in handy.
    df['sv_block_labels'] = nd.label(df.is_spaceview)[0]
    df['bb_block_labels'] = nd.label(df.is_bbview)[0]

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
    
def main(folder):
    rec_dtype, keys = get_div247_dtypes()
    fnames = glob.glob(folder+'/*.div247')
    # opening store in overwrite-mode
    dirname = os.path.dirname(folder)
    basename = os.path.basename(folder)
    storename = os.path.join(dirname,basename+'.h5')
    print storename
    store = pd.HDFStore(storename,mode='w')

    for fname in fnames:
        print("Working on {0}".format(os.path.basename(fname)))
        with open(fname) as f:
            data = np.fromfile(f,dtype=rec_dtype)
        df = pd.DataFrame(data,columns=keys)
        df = prepare_data(df)
        define_sdtype(df)
        to_store = df[df.is_calib]
        store.append('df',to_store )
    
    store.close()

if __name__ == '__main__':
    folders = glob.glob('/Volumes/divaye/divdata/2011*')
    print folders
    for folder in folders:
        if os.path.isdir(folder):
            main(folder)