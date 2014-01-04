from __future__ import division, print_function
import pytest

@pytest.fixture
def df():
    """Return a dataframe for testing."""
    from diviner import file_utils as fu
    df = fu.L1ADataFile.from_timestr('2012012414').open()
    return df
    
    
def test_calblock(df):
    from diviner import calib
    import sys
    print(df.info())
    calblocks = calib.get_calib_blocks(df, 'calib')
    for g,v in calblocks.iteritems():
        print(g)
        sys.stdout.flush()
        cb = calib.CalBlock(v)
        assert cb.mean_time
    
