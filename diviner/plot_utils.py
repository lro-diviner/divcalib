# -*- coding: utf-8 -*-
from __future__ import print_function
from matplotlib.pylab import gcf, subplots, figure
# from mpl_toolkits.mplot3d import axes3d
import matplotlib.animation as animation
import numpy as np
import sys
import pandas as pd


def save_to_www(fname, **kwargs):
    gcf().savefig("/u/paige/maye/WWW/calib/"+fname,**kwargs)

def plot_calib_block(df, label, id, det='a6_11', limits=None, **kwargs):
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
    df_to_plot = pd.DataFrame(index=dfnow.index)
    boolean_selectors = ['is_moving','is_spaceview','is_bbview','is_stview']
    for sel in boolean_selectors:
        # get the timeseries for chosen detector where selector is true
        timeseries = dfnow[dfnow[sel]][det]
        if len(timeseries) > 0:
            # add to dataframe, cut off 'is_' from name (nicer for plot)
            df_to_plot[sel[3:]] = timeseries
    ax = df_to_plot.plot(style='.', **kwargs)
    # ax.yaxis.set_major_formatter(y_formatter)
    ax.set_title(det)
    if limits:
        ax.set_ylim(limits)


def plot_all_calib_blocks(df, **kwargs):
    """Plot all calibration blocks found in the provided dataframe.

    Parameters:
    ==========
    df:      pandas Dataframe with block labels defined (went through define_sdtype())
    kwargs:  same keyword arguments as plot_calib_block
    """
    calib_ids = df.calib_block_labels.unique().tolist()
    # check if the calib block has actually calibration data
    for calid in calib_ids[:]:
        if not any(df[df.calib_block_labels == calid]['is_calib']):
            print("Calib block {0} has no caldata.".format(calid))
            calib_ids.remove(calid)
    length = len(calib_ids)
    if not length%2 == 0:
        length += 1
    fig, axes = subplots(length/2, 2)
    for i, calid in enumerate(calib_ids):
        plot_calib_block(df, 'calib', calid, ax=axes.flatten()[i], **kwargs)
    fig.suptitle("Cal-Blocks {0}".format(calib_ids))


def plot_all_channels(df_in, det_list, only_thermal=True, **kwargs):
    """plot the data for each det in det_list for all channels.

    Parameters:
        df          pandas DataFrame
        det_list    list of detector numbers between 1..21
        **kwargs    keyword arguments for subplots call
    """
    df = df_in.resample('10s')
    print("Resampled to 10 s.")
    fig, axes = subplots(3,3, **kwargs)
    for ch in range(1,7):
        if ch in [1,2] and only_thermal: continue
        axis = axes.flatten()[ch-1]
        cols = ['a'+str(ch)+'_'+str(i).zfill(2) for i in det_list]
        df[cols].plot(ax=axis)
        axis.legend(loc='best')
        axis.set_title('Channel {0}'.format(ch))
    for ch in range(1,4):
        axis = axes.flatten()[ch-1+6]
        cols = ['b'+str(ch)+'_'+str(i).zfill(2) for i in det_list]
        df[cols].plot(ax=axis)
        axis.set_title('Channel {0}'.format(ch+6))
        axis.legend(loc='best')


def create_plot_pointings(azim_start=-60,
                          azim_min=-80,
                          azim_max=-40,
                          elev_start=30,
                          elev_min=-10):
    # azimuths
    azis_down = range(azim_start, azim_min, -1)
    azis_up = range(azim_min, azim_max)
    azis_down2 = range(azim_max, azim_start, -1)
    azis = azis_down + azis_up + azis_down2
    # elevations
    elevs_down = range(elev_start, elev_min, -1)
    elevs_up = range(elev_min, elev_start)
    elevs = elevs_down + elevs_up
    # return pointing tuples
    return zip(elevs, azis)


def plot3d_animation(df_in):
    df = df_in.resample('1min')
    Z = df.values.T
    x = np.arange(len(df))
    y = np.arange(21)
    X, Y = np.meshgrid(x, y)
    pointings = create_plot_pointings()

    def update_pointing(pointing):
        ax.view_init(*pointing)

    fig = figure(figsize=(10,8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_wireframe(X, Y, Z, rstride=5, cstride=5)

    view_ani = animation.FuncAnimation(fig, update_pointing, pointings,
                                       interval=100, repeat_delay=2000)


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
