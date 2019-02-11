#!/usr/bin/env python
import os
import warnings

import matplotlib.pyplot as plt
import pandas as pd

from diviner import calib
from diviner import file_utils as fu


def get_channel_from_fname(divrad_fname):
    b = os.path.basename(divrad_fname)
    cdet = b.split('.')[0].split('_')[-1]
    c = cdet[1:2]
    det = cdet[3:]
    if int(c) < 7:
        c = 'a'+c
    else:
        c = 'b'+c
    cdet = c+'_'+det
    return cdet


# filter for current (<0.11) pandas warnings
warnings.filterwarnings('ignore', category=FutureWarning)

#
# get divdata file
#

divrad_fname = '/Users/maye/data/diviner/rdr_data/20110416_00-01_c6d11.divdata'

columns = ['year', 'month', 'date', 'hour',
           'minute', 'second', 'qmi', 'radiance']

# use pandas parser to read in text file
divdata = pd.io.parsers.read_table(divrad_fname, sep='\s+', names=columns)

# create time index for data
divdata = fu.index_by_time(divdata)

# sort it
divdata = divdata.sort_index()

# drop qmi
divdata = divdata.drop('qmi', axis=1)

#
# now get div247 file and calibrate
#
# get data pump
pump = fu.Div247DataPump("20110416")

# get first hour for that day
df = pump.get_n_hours(2)

# options for calbibration
options = dict(do_bbtimes=True, pad_bbtemps=False,
               single_rbb=True, skipsamples=True)
# calibrate
calib_mine = calib.Calibrator(df, do_bbtimes=False, pad_bbtemps=False,
                              single_rbb=False, skipsamples=False)
calib_mine.calibrate()

calib_jpl = calib.Calibrator(df, do_bbtimes=True, pad_bbtemps=True,
                             single_rbb=True, skipsamples=True)
calib_jpl.calibrate()

# find out the channel that was used by divdata
cdet = get_channel_from_fname(divrad_fname)

# get a view to the right channel
myrad_new = pd.DataFrame(calib_mine.abs_radiance[cdet])
myrad_old = pd.DataFrame(calib_jpl.abs_radiance[cdet])

compare = myrad_new.merge(divdata, left_index=True, right_index=True)
compare.columns = ['new', 'divdata']
compare['jpl'] = myrad_old

compare['bb_error'] = (1 - compare.old / compare.new_bb) * 100
compare['cb_error'] = (1 - compare.old / compare.new_cb) * 100


compare['bb_error'].plot()
compare.old.plot(secondary_y=True)
divdata.radiance.plot(style='r.', label='old')
myrad.plot(style='g.', label='new')
plt.legend(loc='best')
plt.savefig(divrad_fname+'.png', dpi=100)
plt.show()
print()
