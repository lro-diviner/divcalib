#!/usr/bin/env python
import pandas as pd
import file_utils as fu
import calib as c
import matplotlib.pyplot as plt

print pd.__version__
divrad_fname = '/Users/maye/data/diviner/20110416_00-01_c3d11.txt'

columns = ['year','month','date','hour','minute','second','radiance']

# use pandas parser to read in text file
divdata = pd.io.parsers.read_table(divrad_fname, sep='\s+',names=columns)

# create time index for data
divdata = fu.index_by_time(divdata)

# sort it
divdata = divdata.sort_index()

# now get div247 file and calibrate

# get data pump
pump = fu.Div247DataPump("20110416")

# get first hour for that day
df = pump.get_n_hours(2)

#calibrate
calib = c.Calibrator(df)

myrad = calib.abs_radiance.a3_11


divdata.radiance.plot(style='r.',label='new')
myrad.plot(style='g.',label='new')
# plt.legend(loc='best')
plt.show()

