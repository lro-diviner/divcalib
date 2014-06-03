#!/usr/bin/env python
from __future__ import division, print_function
import os
import glob
import sys
from diviner import file_utils as fu
import matplotlib.pyplot as plt


def plot_channel_filesizes(mode, show=False):
    
    dirname = fu.get_month_sample_path_from_mode(mode)
    
    fig, axes = plt.subplots(figsize=(12,10))
    
    for ch in range(3,10):
        searchpath = os.path.join(dirname, '*C'+str(ch)+'*.csv')
        fnames = glob.glob(searchpath)
        sizes = []
        fnames.sort()
        for fname in fnames:
            sizes.append(os.path.getsize(fname))
        axes.plot(sizes,label='Ch '+str(ch))
    axes.legend(loc='best')
    axes.set_title("Length of {0} files.".format(mode))
    savefname = 'filesizes_'+mode+'.png'
    plt.savefig(savefname,dpi=300)
    print("Saving", savefname)
    if show:
        plt.show()
        
if __name__ == '__main__':
    plot_channel_filesizes(sys.argv[1])