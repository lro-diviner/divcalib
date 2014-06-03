#!/usr/bin/env python
from __future__ import division, print_function
from diviner.divtweet import * # imports api handle
import os, glob, sys
from diviner import file_utils as fu
import time
import platform

def get_percent_done(timestr, mode):
    """check how many files have been processed and tweet status regularly.
    
    >>> status_checker timestr mode 60[min]
    
    timestr determines which folders are being checked.
    """
    fnames_out = os.listdir(fu.get_month_sample_path_from_mode(mode))
    fnames = glob.glob(os.path.join(fu.l1adatapath, timestr + '*_L1A.TAB'))
    timestrs_done = [fu.FileName(i).timestr for i in fnames_out]
    # 7 = len[3,4,5,6,7,8,9], i.e. thermal channels
    # if there are not 7 channel files per timestr file, it's not done.
    fnames_todo = [i for i in fnames if timestrs_done.count(fu.FileName(i).timestr) < 7]
    all = len(fnames)
    left = len(fnames_todo)
    done = all - left
    return 100*done/all
    

def main(timestr, mode, sleeptime):
    while True:
        percent_done = get_percent_done(timestr, mode)
        api.update_status("[{3}] {0:5.1f} % of the production of '{1}'"
                          " samples for {2} done.".format(percent_done, mode, timestr,
                                                  platform.node().split('.')[0]))
        time.sleep(float(sleeptime))
        if percent_done > 99.9:
            break


def usage():
    print("Usage: {0} timestr mode sleep[s]".format(sys.argv[0]))
    sys.exit()
                
if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        usage()
        
    main(*sys.argv[1:4])