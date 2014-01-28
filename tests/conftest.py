import pytest
from diviner import file_utils as fu

@pytest.fixture(scope='module')
def df():
    """Return a dataframe for testing."""
    return fu.L1ADataFile.from_timestr('2012012414').open()

    