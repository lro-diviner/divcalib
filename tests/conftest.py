import pytest
from diviner import file_utils as fu

@pytest.fixture(scope='module')
def df():
    """Return a dataframe for testing."""
    return fu.L1ADataFile.from_timestr('2012012414').open()

def pytest_addoption(parser):
    parser.addoption("--runluna", action="store_true",
        help="run luna tests")


def pytest_runtest_setup(item):
    if 'luna' in item.keywords and not item.config.getoption("--runluna"):
        pytest.skip("need --runluna option to run")

