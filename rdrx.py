import ana_utils as au
from diviner import file_utils as fu
import pandas as pd

def get_example_rdrx():
    tstr = '2013031707'
    return RDRR(tstr)


def colnames(colbase, channel=None):
    "create rdrx column names for one or all channels."
    if not channel:
        channels = range(1,10)
    else:
        channels = [channel]
    colnames = []
    for c in channels:
        colnames.extend([colbase+'_'+str(c)+'_'+str(i).zfill(2) 
                            for i in range(1,22)])
    return colnames


# def renamer(colname):
#     cdetstr = '_'.join(colname.split('_')[1:])
#     cdet = au.CDet(cdetstr)
#     return cdet.
    
class RDRR(object):
    """The RDRR object has 2948 columns. This class is a data extractor for it."""
    def __init__(self, tstr_or_filename):
        self.df = fu.RDRR_Reader(tstr_or_filename).open()
        
    @property
    def columns(self):
        return self.df.columns

    def get_column(self, colbase):
        return self.df.filter(regex='^'+colbase+'_')
        
    def get_counts(self):
        return self.get_column('counts')
        
    def get_molten_col(self, colbase, channel):
        rdr1 = self.df
        df = rdr1[colnames(colbase, channel)]
        df = df.rename(columns=lambda x: int(x.split('_')[-1]))
        df = df.reset_index()
        return pd.melt(df, id_vars=['index'],
                       var_name='det', value_name=colbase)

    def get_edr_data(self):
        return self.df.filter(regex='edr_')
