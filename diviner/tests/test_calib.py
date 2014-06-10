from __future__ import division, print_function
import pytest
from diviner import file_utils as fu
from diviner import calib


@pytest.fixture
def cb(df):
    """Return a CalBlock object for testing."""
    from diviner import calib
    from diviner import divconstants as config
    calblocks = calib.get_calib_blocks(df, 'calib')
    return calib.CalBlock(calblocks[1])

def get_l1a(tstr):
    obs = fu.DivObs(tstr)
    l1a = obs.get_l1a()
    return l1a

tstr = '2010011318'

class TestCalBlock:
    def test_Calibrator_init(self):
        tstr = '2010011318'
        l1a = get_l1a(tstr)
        rdr2 = calib.Calibrator(l1a)

    def test_calibrate(self):
        l1a = get_l1a(tstr)
        rdr2 = calib.Calibrator(l1a)
        rdr2.calibrate()
        

