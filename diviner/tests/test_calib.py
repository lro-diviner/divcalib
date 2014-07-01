from __future__ import division, print_function
import pytest
from diviner import file_utils as fu
from diviner import calib
import socket
from diviner.div_l1a_fix import correct_noise
import numpy as np

hostname = socket.gethostname().split('.')[0]


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


def test_noise_correction():
    """Comparing my implementation of Josh's algorithm.

    Josh made available some corrected files. I will simply compare
    the outcome of his correction with output from mine.
    """
    # get original data
    tstr = '2012011401'
    obs = fu.DivObs(tstr)
    data_in = obs.get_l1a()
    # get Josh's corrected data
    if hostname.startswith('luna'):
        corr_data_dir = '/raid1/maye'
    else:
        corr_data_dir = '/Users/maye/data/diviner'
    josh_corr = corr_data_dir + '/2012011401_L1A.TAB.corrected'
    josh_corr = fu.read_l1a_data(josh_corr)
    # apply my implementation
    my_corr = correct_noise(data_in)
    results = []
    for det in calib.thermal_detectors:
        results.append(np.allclose(my_corr[det], josh_corr[det]))
    assert np.array(results).all()
