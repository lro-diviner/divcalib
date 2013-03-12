#!/usr/bin/env python
import pandas as pd
import file_utils as fu
import calib as c
import matplotlib.pyplot as plt
import warnings

print pd.__version__

#filter for current (<0.11) pandas warnings
warnings.filterwarnings('ignore',category=FutureWarning)
    
#
# first get divdata file
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
calib = c.Calibrator(df)
calib.calibrate()

myrad = pd.DataFrame(calib.abs_radiance.a6_11)

compare = myrad.merge(divdata, left_index=True, right_index=True)
compare.columns = ['new','old']
compare.rel_error = (1 - compare.new / compare.old) * 100
compare.rel_error.plot()
# compare.old.plot(secondary_y=True)
# divdata.radiance.plot(style='r.',label='old')
# myrad.plot(style='g.',label='new')
# plt.legend(loc='best')
plt.savefig(divrad_fname+'.png',dpi=100)
# plt.show()
print


