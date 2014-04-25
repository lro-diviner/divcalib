import pytest
from diviner import file_utils as fu


@pytest.fixture(scope='module')
def df():
    """Return a dataframe for testing."""
    return fu.DivObs('2012012414').get_l1a()


def pytest_addoption(parser):
    parser.addoption("--runluna", action="store_true",
                     help="run luna tests")


def pytest_runtest_setup(item):
    if 'luna' in item.keywords and not item.config.getoption("--runluna"):
        pytest.skip("need --runluna option to run")
