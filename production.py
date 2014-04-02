from diviner import calib
from diviner import file_utils as fu
from diviner import ana_utils as au
import rdrx

def get_example_data():
    tstr = '2013031707'
    df = fu.get_clean_l1a(tstr)
    rdr2 = calib.Calibrator(df)
    rdr2.calibrate()
    rdr1 = rdrx.RDRR(tstr)
    return rdr1,rdr2
