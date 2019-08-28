#!/usr/bin/env python
from diviner import file_utils as fu
import logging
from joblib import Parallel, delayed
import sys

logging.basicConfig(filename="log_monotonicity.log", level=logging.INFO)


def check_fname(fname):
    df = fu.open_and_accumulate(fname)
    if not df.index.is_monotonic:
        logging.warning("{} has non-monotonic index".format(fname))


def main():
    print("Use: {} year (4-digits)".format(sys.argv[0]))
    pump = fu.L1ADataPump(sys.argv[1])
    todo = pump.fnames

    Parallel(n_jobs=8)(delayed(check_fname)(fname) for fname in todo)


if __name__ == "__main__":
    main()
