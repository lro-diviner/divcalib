from __future__ import print_function
from joblib import Parallel, delayed
import time


def process_channel(tstr, c, month):
    print("Processing channel", c, "for day", tstr, "of month", month)
    time.sleep(5)


def process_tstr(tstr, month):
    print("Processing day", tstr, "for month", month)
    Parallel(n_jobs=4, backend='threading')(delayed
                                            (process_channel)(tstr, i, month)
                                            for i in range(7, 10))


def process_month(month):
    print("Processing", month)
    for i in range(3):
        process_tstr(i+1, month)

if __name__ == '__main__':
    months = ['Jan', 'Feb', 'March', 'April']
    Parallel(n_jobs=4)(delayed
                       (process_month)(month)
                       for month in months)
