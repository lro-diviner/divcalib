import pandas as pd
import file_utils as fu
import calib as c
from matplotlib.pyplot import show

divrad_fname = '/raid1/maye/divdata/20110416_00-01_c3d11.txt'

columns = ['year','month','date','hour','minute','second','radiance']

# use pandas parser to read in text file
divdata = pd.io.parsers.read_table(divrad_fname, sep='\s+',names=columns)

# create time index for data
divc3d11rad = fu.index_by_time(divdata)

# sort it
divc3d11rad.sort_index()

# now get div247 file and calibrate

# get data pump
pump = fu.Div247DataPump("20110416")

# get first hour for that day
df = pump.get_n_hours(1)

#calibrate
calib = c.Calibrator(df)

myrad = calib.radiance.a3_11

# myrad.plot()

divc3d11rad.plot(style='r.',label='old')
myrad.plot(style='g.',label='new')
legend(loc='best')
show()

