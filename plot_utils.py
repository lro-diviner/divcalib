# -*- coding: utf-8 -*-
from __future__ import print_function
from matplotlib.pylab import gcf,title, subplots
import sys

def save_to_www(fname, **kwargs):
    gcf().savefig("/u/paige/maye/WWW/calib/"+fname,**kwargs)
    
def plot_calib_block(df,label,id,det='a6_11'):
    """Plot one designated calibration block.
    
    Parameters:
    -----------
    
    df:     pandas Dataframe that has the block labels defined to use as filter.
    label:  one of 'calib','bb','sv','st'
    id:     number of block label to be plotted
    det:    identifier of the detector, a6_11 is default being used.
    """
    if not label.endswith('_block_labels'):
        label = label + '_block_labels'
    dfnow = df[df[label]==id]
    l = ['is_moving','is_spaceview','is_bbview','is_stview']
    lnew = []
    for item in l:
        dfnow2 = dfnow[dfnow[item]][det]
        if len(dfnow2) > 0:
            nitem = item.replace('is_','')
            dfnow[nitem] = dfnow2
            lnew.append(nitem)
    dfnow[lnew].plot(style='.',linewidth=2)
    title(det)

def plot_all_channels(df, det_list, **kwargs):
    """plot the data for each det in det_list for all channels.
    
    Parameters:
        df          pandas DataFrame
        det_list    list of detector numbers between 1..21
        **kwargs    keyword arguments for subplots call
    """
    fig, axes = subplots(3,3, **kwargs)
    for ch in range(1,7):
        axis = axes.flatten()[ch-1]
        cols = ['a'+str(ch)+'_'+str(i).zfill(2) for i in det_list]
        df[cols].plot(ax=axis)
        axis.set_title('Channel {0}'.format(ch))
    for ch in range(1,4):
        axis = axes.flatten()[ch-1+6]
        cols = ['b'+str(ch)+'_'+str(i).zfill(2) for i in det_list]
        df[cols].plot(ax=axes.flatten()[ch-1+6])
        axis.set_title('Channel {0}'.format(ch+6))
    
class ProgressBar:
    def __init__(self, iterations):
        self.iterations = iterations
        self.prog_bar = '[]'
        self.fill_char = '*'
        self.width = 50
        self.__update_amount(0)

    def animate(self, iter):
        print('\r', self, end='')
        sys.stdout.flush()
        self.update_iteration(iter + 1)

    def update_iteration(self, elapsed_iter):
        self.__update_amount((elapsed_iter / float(self.iterations)) * 100.0)
        self.prog_bar += '  %d of %s complete' % (elapsed_iter, self.iterations)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) // 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)