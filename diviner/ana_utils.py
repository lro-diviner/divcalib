import pandas as pd
from diviner import file_utils as fu
from diviner import calib


class Channel(object):
    mcs_div_mapping = {'a1': 1, 'a2': 2, 'a3': 3,
                       'a4': 4, 'a5': 5, 'a6': 6,
                       'b1': 7, 'b2': 8, 'b3': 9}

    div_mcs_mapping = {key: value for value, key in
                       mcs_div_mapping.items()}

    def __init__(self, c):
        if str(c).lower()[0] in ['a', 'b']:
            self._mcs = c[:2]
            self._div = self.mcs_div_mapping[c[:2]]
        else:
            c = int(c)
            self._div = c
            self._mcs = self.div_mcs_mapping[c]

    @property
    def mcs(self):
        return self.div_mcs_mapping[self._div]

    @property
    def div(self):
        return self.mcs_div_mapping[self._mcs]


class CDet(object):
    def __init__(self, c, det=None):
        self.c = Channel(c)
        if not det:
            self.det = int(c[3:])
        else:
            self.det = det

    @property
    def div(self):
        return (self.c.div, self.det)

    @property
    def mcs(self):
        return self.c.mcs+'_'+str(self.det).zfill(2)


def get_mcs_detid_from_divid(c, det=None):
    """One can provide 'c_det' as input for the first parameter."""
    if not det:
        c, det = c.split('_')
        c = int(c)
    if c in range(1, 7):
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

    def get_cdet_rad(self, c, det, tstr, kind='norm'):
        # the tstr is used to cut out the center-piece of a larger ROI
        data = self.rdr2[kind+'_radiance'][fu.tstr_to_tindex(tstr)]
        # switch detector layout for telescope B
        if c > 6:
            realdet = 22 - int(det)
        else:
            realdet = int(det)
        return data[CDet(c, realdet).mcs]

    def get_c_rad(self, c, tstr, kind='norm', invert_dets=True):
        col = getattr(self.rdr2, kind+'_radiance')
        data = col[fu.tstr_to_tindex(tstr)]
        chdata = data.filter(regex='^'+Channel(c).mcs)
        # invert channels if for telescope B
        renamer = lambda x: int(x[-2:])
        if (c > 6) and invert_dets:
            renamer = lambda x: 22 - int(x[-2:])
        return chdata.rename(columns=renamer)

    def get_c_rad_molten(self, c, tstr, kind='norm', invert_dets=True):
        newrad = self.get_c_rad(c, tstr, kind, invert_dets)
        newrad = newrad.reset_index()
        molten = pd.melt(newrad, id_vars=['index'],
                         value_vars=list(range(1, 22)),
                         var_name='det',
                         value_name='newrad')
        return molten
