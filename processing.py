from __future__ import print_function
from diviner import file_utils as fu, calib
from os.path import join as pjoin
import divtweet
import sys
from datetime import timedelta
import logging
import pandas as pd
import os
from joblib import Parallel, delayed

logname = 'divcalib.log'
logging.basicConfig(filename=logname,
                    format='%(asctime)s -%(levelname)s- %(message)s',
                    level=logging.INFO)

root = '/raid1/maye/l1b_production'

def process_fname(fname):
    tstr = fu.get_timestr(fname)
    print(tstr)
    sys.stdout.flush()
    df = fu.open_and_accumulate(fname)
    if not df.index.is_monotonic:
	logging.error("Founid non-monotonic 3-hour index at {}".format(fname))
	return
    c = calib.Calibrator(df)
    try:
	c.calibrate()
    except Exception as e:
	print("Caught error", e)
	logging.error("{} did not calibrate!!!".format(fname))
        return
    hdfname = pjoin(root, tstr + '.h5')
    tstamp = fu.tstr_to_datetime(tstr)
    end = tstamp + timedelta(hours=1)
    try:
        c.abs_radiance[tstamp:end].to_hdf(hdfname, 'radiance')
        c.Tb[tstamp:end].to_hdf(hdfname, 'tb')
    except KeyError:
        print("KeyError at {}".format(fname))
        logging.error("KeyError at {}".format(fname))


def main(start, end, startover=False):
    """Calibrate and create hdf files with radiance and tb.

    'start' and 'end' have to be 8-digit complete date strings because the
    date_range requires 8 digits as input. At the end it only works
    on a month precision, because I decided to do it monthly later on
    TODO: Create more user-friendly options here.
    """
    months = pd.date_range(start, end , freq='M')
    print("Created date range:",months)
    fnames = []
    for month in months:
        m = month.strftime('%Y%m')
        pump = fu.L1ADataPump(m)
        if not startover:
            print("Skipping existing h5 files.")
            for fname in pump.fnames:
                tstr = fu.get_timestr(fname)
                hdfname = pjoin(root, tstr + '.h5')
                if not os.path.exists(hdfname):
                    fnames.append(fname)
        else:
            print("Starting over.")
            fnames.extend(pump.fnames)

    print("Found",len(fnames),'files to do.')
    Parallel(n_jobs=8)(delayed(process_fname)(fname) for fname in fnames)
    #divtweet.tweet_machine("Finished processing {0}, {1} files.".format(month,
    #                                                            len(fnames)))

def usage():
    print("Usage: {} start end [new|skip]".format(sys.argv[0]))
    sys.exit()

if __name__=='__main__':
    start, end = sys.argv[1:3]
    # if user provided only 6 digits like 201001 as input, add another 01 for the date
    # because above code requires it.
    if len(start) == 6:
        start += '01'
    if len(end) == 6:
        end += '01'
    startover = False
    try:
        if sys.argv[3] == 'new':
            startover = True
        elif sys.argv[3] == 'skip':
            startover = False
        else:
            usage()
    except IndexError:
        usage()
    main(start, end, startover)

