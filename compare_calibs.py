#!/usr/bin/env python
import pandas as pd
import file_utils as fu
import calib as c
import matplotlib.pyplot as plt

print pd.__version__

#
# first get divdata file
#

divrad_fname = '/Users/maye/data/diviner/rdr_data/20110416_00-01_c6d11.divdata'

columns = ['year','month','date','hour','minute','second','radiance']

# use pandas parser to read in text file
divdata = pd.io.parsers.read_table(divrad_fname, sep='\s+',names=columns)

# create time index for data
divdata = fu.index_by_time(divdata)

# sort it
divdata = divdata.sort_index()

#
# now get div247 file and calibrate
#
# get data pump
pump = fu.Div247DataPump("20110416")

fnames = list(pump.gen_fnames())

df1 = pump.process_one_file(fnames[0])
df2 = pump.process_one_file(fnames[1])
df = pd.concat([df1,df2])
# df = df1
df = pump.clean_final_df(df)

# get first hour for that day
# df = pump.get_n_hours(2)

#calibrate
calib = c.Calibrator(df)

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

