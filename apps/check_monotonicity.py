#!/usr/bin/env python
from __future__ import print_function, division
from diviner import file_utils as fu
import logging
from joblib import Parallel, delayed
from diviner import divtweet
import sys

logging.basicConfig(filename='log_monotonicity.log', level=logging.INFO)

def check_fname(fname):
    df = fu.open_and_accumulate(fname)
    if not df.index.is_monotonic:
        logging.warning("{} has non-monotonic index".format(fname))

def main():
    found = False
    try:
        pump = fu.L1ADataPump(sys.argv[1])
    except:
        print("Use: {} year (4-digits)".format(sys.argv[0]))
        sys.exit()
    todo = pump.fnames

    Parallel(n_jobs=12)(delayed(check_fname)(fname) for fname in todo)
    divtweet.tweet_machine('now really: {} checked for monotonicity.'.format(sys.argv[1]))

if __name__ == '__main__':
    main()

