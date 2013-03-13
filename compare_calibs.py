#!/usr/bin/env python
import pandas as pd
import file_utils as fu
import calib
import matplotlib.pyplot as plt
import warnings
import os

print pd.__version__

#filter for current (<0.11) pandas warnings
warnings.filterwarnings('ignore',category=FutureWarning)
    
#
# get divdata file
#

divrad_fname = '/Users/maye/data/diviner/rdr_data/20110416_00-05_c3d11.divdata'

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
df = pump.get_n_hours(6)

#calibrate
calibrated = calib.Calibrator(df)
calibrated.calibrate()

# find out the channel that was used by divdata
b = os.path.basename(divrad_fname)
cdet = b.split('.')[0].split('_')[-1]
c = cdet[1:2]
det = cdet[3:]
if int(c) < 7:
    c = 'a'+c
else:
    c = 'b'+c
cdet = c+'_'+det

# get a view to the right channel
myrad = pd.DataFrame(calibrated.abs_radiance[cdet])

compare = myrad.merge(divdata, left_index=True, right_index=True)
compare.columns = ['new','old']
compare['rel_error'] = (1 - compare.old / compare.new) * 100
# compare['rel_error'].plot()
# compare.old.plot(secondary_y=True)
# divdata.radiance.plot(style='r.',label='old')
# myrad.plot(style='g.',label='new')
# plt.legend(loc='best')
# plt.savefig(divrad_fname+'.png',dpi=100)
# plt.show()
print

