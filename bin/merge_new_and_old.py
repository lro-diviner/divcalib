from __future__ import division, print_function
from diviner import calib
import os
import glob
import pandas as pd
from joblib import Parallel, delayed
from diviner import file_utils as fu
import logging
from datetime import timedelta

# this are the rdr-columns to merge from the old RDR data
rdr_columns = ['clat', 'clon']
logging.basicConfig(filename='log_coldregions_merged.log', level=logging.INFO)


def rename_column(colname):
    "Rename the RDRR columns to standard MCS scheme"
    dealwith = '_'.join(colname.split('_')[1:])
    if int(dealwith[0]) in range(1, 7):
        return 'a' + dealwith
    else:
        return 'b' + dealwith


def merge_rdr_column(target_df, colstring, rdrr):
    coldata = rdrr.filter(regex='^' + colstring + '_')
    coldata = coldata.rename(columns=rename_column)
    molten = pd.melt(coldata.reset_index(),
                     id_vars=['index'],
                     var_name='det',
                     value_name=colstring)
    return target_df.merge(molten, on=['index', 'det'])


def process_rad_file(rad_file):
    logging.info("Processing {}".format(rad_file))
    path = os.path.dirname(rad_file)
    tstr = fu.get_timestr(rad_file)
    try:
        # get old rdr data
        rdrr = fu.RDRR_Reader(tstr).open()
    except IOError:
        logging.error("rad_file {} had no counterpart rdrr.".format(rad_file))
        return
    time_covered = rdrr.index[-1] - rdrr.index[0]
    if time_covered < timedelta(minutes=59):
        logging.error(
            "rdrr file {} covers less than 59 minutes of data.".format(tstr))
        return
    rad = pd.read_hdf(rad_file, 'radiance')
    tb = pd.read_hdf(os.path.join(path, tstr + '_tb.h5'), 'tb')
    tindex = fu.fname_to_tindex(rad_file)
    rad = rad[calib.thermal_detectors][tindex]
    tb = tb[calib.thermal_detectors][tindex]
    molten_rad = pd.melt(rad.reset_index(), id_vars=['index'], var_name='det',
                         value_name='radiance')
    molten_tb = pd.melt(tb.reset_index(), id_vars=['index'], var_name='det',
                        value_name='tb')
    # molten_rad.sort(columns=['index'], inplace=True)
    # molten_tb.sort(columns=['index'], inplace=True)
    radtb = molten_tb.merge(molten_rad, on=['index', 'det'])

    for col in rdr_columns:
        radtb = merge_rdr_column(radtb, col, rdrr)
    jdate = rdrr.filter(regex='jdate')
    radtb = radtb.merge(jdate.reset_index(), on=['index'])
    radtb['c'] = radtb.det.str[:2].map(calib.mcs_div_mapping).astype('int')
    radtb['det'] = radtb['det'].str[-2:].astype('int')
    radtb.rename(columns={'index': 'isotime'})
    radtb.to_csv(os.path.join(path, tstr + '_merged.csv'),
                 index=False, na_rep=9999)


if __name__ == '__main__':
    regions = [1, 3, 5]

    root = '/raid1/maye/coldregions/no_rad_correction'

    for region_no in regions:
        print('Region', region_no)
        path = os.path.join(root, 'region' + str(region_no))
        print('Path:', path)
        rad_files = glob.glob(os.path.join(path, '*_radiance.h5'))
        tstrings = [fu.get_timestr(i) for i in rad_files]
        todo = []
        for rad_file, tstr in zip(rad_files, tstrings):
            mergedpath = os.path.join(path, tstr + '_merged.csv')
            if not os.path.exists(mergedpath):
                todo.append(rad_file)
        Parallel(n_jobs=8, verbose=3)(delayed(process_rad_file)(rad_file)
                                      for rad_file in todo)
    print("Done.")
