from __future__ import division, print_function
import pytest

@pytest.fixture
def cb(df):
    """Return a CalBlock object for testing."""
    from diviner import calib
    from diviner import divconstants as config
    calblocks = calib.get_calib_blocks(df, 'calib')
    return calib.CalBlock(calblocks[1], config.SV_NUM_SKIP_SAMPLE)
    
class TestCalBlock:
    def test_sv_grouped(self, cb):
        assert len(cb.sv_grouped) == 2
    def test_sv_labels(self, cb):
        assert cb.sv_labels[0] == 1
        assert cb.sv_labels[1] == 2