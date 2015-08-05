import numpy as np
import scipy.ndimage as nd
from scipy.optimize import curve_fit


# selection can only be made on the basis of the elevation command
# as the azimuth command value stays constant during ground calib


def get_sv_selector(df):
    return (df.last_el_cmd >= 75) & \
           (df.last_el_cmd <= 80)


def get_bb_selector(df):
    return (df.last_el_cmd < 5) & \
           (df.last_el_cmd > -5)


# fake entry to make calibrator work with ground calib
def get_st_selector(df):
    "Create dataframe selector for pointing limits of divconstants 'c' file"
    return df.last_el_cmd == 1000


def define_sdtype(df):
    df['sdtype'] = 0
    df.loc[get_sv_selector(df), 'sdtype'] = 1
    df.loc[get_bb_selector(df), 'sdtype'] = 2
    # fake to make calibrator work
    df.loc[get_st_selector(df), 'sdtype'] = 3

    df['calib_block_labels'] = nd.label((df.sdtype == 1) |
                                        (df.sdtype == 2))[0]

    df.loc[df.moving == 1, 'sdtype'] = -1

    df['space_block_labels'] = nd.label(df.sdtype == 1)[0]
    df['bb_block_labels'] = nd.label(df.sdtype == 2)[0]
    # fake entry
    df['st_block_labels'] = nd.label(df.sdtype == 3)[0]

    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview'] = (df.sdtype == 2)
    df['is_moving'] = (df.sdtype == -1)
    df['is_calib'] = df.is_spaceview | df.is_bbview
    df['is_stview'] = (df.sdtype == 3)


def data_prep(data, hk):
    data['last_az_cmd'] = hk.LAST_AZ_CMD
    data.last_az_cmd = data.last_az_cmd.fillna(method='ffill')
    data['last_el_cmd'] = hk.LAST_EL_CMD
    data.last_az_cmd = data.last_az_cmd.fillna(method='ffill')
    data['moving'] = hk.MOVING
    data.moving = data.moving.fillna(method='ffill')
    define_sdtype(data)


class DarkScaler(object):

    def __init__(self, data_in, data_out):
        self.data_in = data_in
        self.data_out = data_out

    def do_fit(self):
        self.p, self.pcov = curve_fit(self.model,
                                      self.data_in.ravel(),
                                      self.data_out.ravel())
        self.perr = np.sqrt(np.diag(self.pcov))

    @property
    def scaled(self):
        return self.model(self.data_in, self.p)

    @property
    def residual(self):
        return self.data_out - self.scaled

    @property
    def fractional(self):
        return self.residual / self.data_out

    def apply_fit(self, in_):
        return self.model(in_, self.p)


class PolyScaler(DarkScaler):

    """Manage polynomial fits. Default rank is 2."""

    def __init__(self, data_in, data_out, rank=2):
        super(PolyScaler, self).__init__(data_in, data_out)
        self.rank = rank

    @property
    def rank(self):
        return self._rank

    @rank.setter
    def rank(self, value):
        self._rank = value

    @property
    def poly(self):
        return np.poly1d(self.p)

    def model(self, x=None, p=None):
        if x is None:
            x = self.data_in
        if p is None:
            p = self.p
        poly = np.poly1d(p)
        return poly(x)

    def do_fit(self):
        self.p = np.polyfit(self.data_in.ravel(),
                            self.data_out.ravel(),
                            self.rank)

    @property
    def perr(self):
        print("Not defined yet for PolyFitter.")
        return
