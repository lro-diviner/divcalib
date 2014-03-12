import pandas as pd


def get_mcs_detid_from_divid(ch, det=None):
    """One can provide 'c_det' as input for the first parameter, for convience."""
    if not det:
        ch, det = ch.split('_')
        ch = int(ch)
    if ch in range(1,7):
        c = 'a'+str(ch)
    else:
        c = 'b'+str(ch - 6)
    
    return c+'_'+str(det).zfill(2)
    
    
class RDRHelper(object):
    def __init__(self, df):
        self.df = df
        
    def get_chdet(self, ch, det):
        df = self.df
        return df[(df.c == ch) & (df.det == det)]
    
    def get_chdet_rad(self, ch, det):
        chdetdf = self.get_chdet(ch, det)
        return chdetdf.radiance
        
        
class CalibHelper(object):
    def __init__(self, calib_object):
        self.c = calib_object
        
    def get_chdet_rad(self, ch, det):
        chdet_str = get_mcs_detid_from_divid(ch, det)
        return self.c.abs_radiance[chdet_str]
        
    def get_data_for_tstr(self):
        pass