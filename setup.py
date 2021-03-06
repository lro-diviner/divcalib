import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

pandas_version = '0.16.1'


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['-v', '-m', 'not luna']
        self.test_suite = True

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name="Diviner",
    version="2.4.0b4",
    packages=find_packages(),
    package_dir={'diviner': 'diviner'},
    package_data={'diviner': ['data/*']},
    install_requires=['pandas>=' + pandas_version],
    tests_require=['pytest'],

    cmdclass={'test': PyTest},

    entry_points={
        "console_scripts": [
            'scp_l1a = diviner.file_utils:scp_l1a_file'
        ]
    },

    # metadata
    author="K.-Michael Aye",
    author_email="kmichael.aye@gmail.com",
    description="Software for the calibration of LRO Diviner data",
    license="BSD 2-clause",
    keywords="Diviner LRO calibration RDR",
    url="http:www.diviner.ucla.edu",
)
