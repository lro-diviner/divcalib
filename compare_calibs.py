#!/usr/bin/env python
import pandas as pd
import file_utils as fu
import calib
import matplotlib.pyplot as plt
import warnings
import os

print pd.__version__

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
    
#filter for current (<0.11) pandas warnings
warnings.filterwarnings('ignore',category=FutureWarning)
    
#
# get divdata file
#

divrad_fname = '/Users/maye/data/diviner/rdr_data/20110416_00-01_c3d11.divdata'

columns = ['year','month','date','hour','minute','second','qmi','radiance']

# use pandas parser to read in text file
divdata = pd.io.parsers.read_table(divrad_fname, sep='\s+',names=columns)

# create time index for data
divdata = fu.index_by_time(divdata)

# sort it
divdata = divdata.sort_index()

# drop qmi
divdata = divdata.drop('qmi',axis=1)

#
# now get div247 file and calibrate
#
# get data pump
pump = fu.Div247DataPump("20110416")

# get first hour for that day
df = pump.get_n_hours(2)

#calibrate
calib_bb = calib.Calibrator(df)
calib_bb.calibrate()

calib_cb = calib.Calibrator(df, bbtimes=False)
calib_cb.calibrate()

# find out the channel that was used by divdata
cdet = get_channel_from_fname(divrad_fname)

# get a view to the right channel
myrad_bb = pd.DataFrame(calib_bb.abs_radiance[cdet])
myrad_cb = pd.DataFrame(calib_cb.abs_radiance[cdet])

compare = myrad_bb.merge(divdata, left_index=True, right_index=True)
compare.columns = ['new_bb','old']
compare['new_cb'] = myrad_cb

# compare['bb_error'] = (1 - compare.old / compare.new_bb) * 100
# compare['cb_error'] = (1 - compare.old / compare.new_cb) * 100


# compare['rel_error'].plot()
# compare.old.plot(secondary_y=True)
# divdata.radiance.plot(style='r.',label='old')
# myrad.plot(style='g.',label='new')
# plt.legend(loc='best')
# plt.savefig(divrad_fname+'.png',dpi=100)
# plt.show()
print

