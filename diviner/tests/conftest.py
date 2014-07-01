import pytest
from diviner import file_utils as fu


@pytest.fixture(scope='module')
def df():
    """Return a dataframe for testing."""
    return fu.DivObs('2012012414').get_l1a()
