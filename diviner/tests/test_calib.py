from __future__ import division, print_function
import pytest


@pytest.fixture
def cb(df):
    """Return a CalBlock object for testing."""
    from diviner import calib
    from diviner import divconstants as config
    calblocks = calib.get_calib_blocks(df, 'calib')
    return calib.CalBlock(calblocks[1])


class TestCalBlock:
    pass
