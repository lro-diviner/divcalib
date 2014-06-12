from __future__ import division, print_function
import pytest
from diviner import file_utils as fu
from diviner import calib


@pytest.fixture
def cb(df):
    """Return a CalBlock object for testing."""
    from diviner import calib
    calblocks = calib.get_calib_blocks(df, 'calib')
    return calib.CalBlock(calblocks[1])

tstr = '2010011318'


class TestCalBlock:
    def test_Calibrator_init(self):
        tstr = '2010011318'
        obs = fu.DivObs(tstr)
        df = obs.get_l1a()
        calib.Calibrator(df)

    def test_calibrate(self):
        tstr = '2010011318'
        df = fu.open_and_accumulate(tstr)
        rdr2 = calib.Calibrator(df)
        rdr2.calibrate()
