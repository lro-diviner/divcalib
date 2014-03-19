import pandas as pd
from diviner import file_utils as fu

def get_mcs_detid_from_divid(c, det=None):
    """One can provide 'c_det' as input for the first parameter, for convience."""
    if not det:
        c, det = c.split('_')
        c = int(c)
    if c in range(1,7):
        c = 'a'+str(c)
    else:
        c = 'b'+str(c - 6)
    
    return c+'_'+str(det).zfill(2)
    
    
class RDRHelper(object):
    def __init__(self, df):
        self.df = df
        
    def get_cdet(self, c, det):
        df = self.df
        return df[(df.c == c) & (df.det == det)]
    
    def get_cdet_rad(self, c, det):
        cdetdf = self.get_cdet(c, det)
        return cdetdf.radiance
        
        
class RDRR_Helper(object):
    def __init__(self, df):
        self.df = df

    def get_cdet_rad(self, c, det):
        colname = 'radiance_'+str(c)+'_'+str(det).zfill(2)
        return self.df[colname]


class CalibHelper(object):
    def __init__(self, calib_object):
        self.rdr2 = calib_object
        
    def get_cdet_rad(self, c, det, tstr):
        # the tstr is used to cut out the center-piece of a larger ROI
        data = self.rdr2.abs_radiance[fu.tstr_to_tindex(tstr)]
        cdet_str = get_mcs_detid_from_divid(c, det)
        return data[cdet_str]
        
    def get_data_for_tstr(self):
        pass
