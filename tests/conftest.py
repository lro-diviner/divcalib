import pytest
from diviner import file_utils as fu

@pytest.fixture(scope='module')
def df():
    """Return a dataframe for testing."""
    return fu.L1ADataFile.from_timestr('2012012414').open()

def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true",
        help="run slow tests")

def pytest_runtest_setup(item):
    if 'slow' in item.keywords and not item.config.getoption("--runslow"):
        pytest.skip("need --runslow option to run")

    