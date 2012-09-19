#!/Library/Frameworks/Python.framework/Versions/Current/bin/python

from matplotlib import pyplot as plt
import pandas
import numpy as np
from diviner import read_pprint, read_pds, divplot
from scipy import fft

# all available channels in pprint files for noise
channels = [1,8,9]
# choose detector
det = 11

def isodd(number):
    return bool(number % 2)
    
def get_label(dataframe, label, ch, det=11):
    l = dataframe[label][(dataframe.c==ch) & (dataframe.det==det)]
    return l
    
def plot_channels(ax, data):
    for tb,ch in zip(data,channels):
        ax.plot(tb, label="{0}_{1}".format(ch, det))

def plot_all(fig, tbdata, azdata, elevdata, title):
    ax = fig.add_subplot(111)
    plot_channels(ax, tbdata)
    ax.plot(azdata, label='az_cmd')
    ax.plot(elevdata, label='el_cmd')
    ax.set_title(title)
    ax.legend(loc='best')
    return ax

def get_abs_fft(data):
    f = fft(data)
    print(len(f))
    half = len(f)/2
    fix = 0
    if isodd(len(f)):
        fix = 1
    print(half)
    t = np.arange(-half,half+fix,1)
    print(len(t))
    f_sorted = np.concatenate( (f[half:], f[:half]) )
    print(len(f_sorted))
    return t,abs(f_sorted)
    
def plot_fft(fig, datatuple, title):
    ax = fig.add_subplot(111)
    for t,data in datatuple:
        ax.plot(t,data)
    ax.set_title(title)
    return ax
   
def main(): 
    fclean = '/Users/maye/data/diviner/201204090110_RDR.TAB'
    fnoise = ['/Users/maye/data/diviner/noise1.tab',
              '/Users/maye/data/diviner/noise2.tab',
              '/Users/maye/data/diviner/noise3.tab',
             ]

    store = pandas.HDFStore('dataframes.h5','r')

    # this clean file comes from PDS, random choice
    print('Reading dataframes.')
    # dfclean = read_pds(fclean)
    dfclean = store['dfclean']
    dfnoise = store['dfnoise1']
    print('Done.')
    store.close()
    # # fnoise was created by pprint, different format therefore different reader
    # dfnoise = read_pprint(fnoise[1])

    ##############
    ### watch out!
    dfnoise.tb[dfnoise.tb < -9990] = 0
    dfclean.tb[dfclean.tb < -9990] = 0
    dfnoise.tb[np.isnan(dfnoise.tb)] = 0
    dfclean.tb[np.isnan(dfclean.tb)] = 0
    ### watch this!
    ##############

    tbcleans = [get_label(dfclean, 'tb', ch, det) for ch in channels]
    azclean = get_label(dfclean, 'az_cmd', 1)
    elevclean = get_label(dfclean, 'el_cmd', 1)
    tbnoise = [get_label(dfnoise, 'tb', ch, det) for ch in channels]
    aznoise = get_label(dfnoise, 'az_cmd', 1)
    elevnoise = get_label(dfnoise, 'el_cmd', 1)

    figclean = plt.figure()
    axclean = plot_all(figclean, tbcleans, azclean, elevclean, 'Random PDS dataset')

    fignoise = plt.figure()
    axnoise = plot_all(fignoise, tbnoise, aznoise, elevnoise, 'Noisy dataset')

    cleantup = [get_abs_fft(data) for data in tbcleans]
    noisetub = [get_abs_fft(data) for data in tbnoise]
    
    figfftclean = plt.figure()
    axfftclean = plot_fft(figfftclean, cleantup, 'FFT of random data')
    
    figfftnoise = plt.figure()
    axfftnoise = plot_fft(figfftnoise, noisetub, 'FFT of noisy data')

    plt.show()
    
if __name__ == '__main__':
    main()