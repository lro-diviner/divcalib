from setuptools import setup, find_packages

setup(
    name = "Diviner",
    version = "2.0beta",
    packages = find_packages(),

    install_requires = ['pandas>=0.13.1'],

    author = "K.-Michael Aye",
    author_email = "kmichael.aye@gmail.com",
    description = "Software for the calibration of LRO Diviner data",
    license = "BSD 2-clause",
    keywords = "Diviner LRO calibration RDR",
    url = "http:www.diviner.ucla.edu",
)
