#!/Library/Frameworks/Python.framework/Versions/Current/bin/python

from matplotlib import pyplot as plt
import pandas
import numpy as np
from diviner import read_pprint, read_pds, divplot
from scipy import fft

# choose channel
channel = 1

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

def plot_all(ax, tbdata, azdata, elevdata, title):
    ax.plot(tbdata, label='tb')
    ax.plot(azdata, label='az_cmd')
    ax.plot(elevdata, label='el_cmd')
    ax.set_title(title)
    ax.legend(loc='best')

def get_abs_fft(data):
    f = fft(data)
    half = len(f)/2
    fix = 0
    if isodd(len(f)):
        fix = 1
    t = np.arange(-half,half+fix,1)
    f_sorted = np.concatenate( (f[half:], f[:half]) )
    return t,abs(f_sorted)
    
def plot_fft(ax, datatuple, title):
    t, data = datatuple
    ax.semilogy(t,data)
    ax.set_xlim(0,0.5*len(data))
    ax.set_ylim(0,0.2*data.max())
    ax.set_title(title)
   
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
    dfnoise = [store['dfnoise1'],store['dfnoise2'],store['dfnoise3']]
    print('Done.')
    store.close()
    # # fnoise was created by pprint, different format therefore different reader
    # dfnoise = read_pprint(fnoise[1])

    ##############
    ### watch out!
    for df in dfnoise:
        df.tb[df.tb < -9990] = 0
        df.tb[np.isnan(df.tb)] = 0
    dfclean.tb[dfclean.tb < -9990] = 0
    dfclean.tb[np.isnan(dfclean.tb)] = 0
    ### watch this!
    ##############

    tbcleans = get_label(dfclean, 'tb', channel, det)
    azclean = get_label(dfclean, 'az_cmd', channel)
    elevclean = get_label(dfclean, 'el_cmd', channel)
    tbnoise = [get_label(df, 'tb', channel, det) for df in dfnoise]
    aznoise = [get_label(df, 'az_cmd', channel) for df in dfnoise]
    elevnoise = [get_label(df, 'el_cmd', channel) for df in dfnoise]

    fig, axes = plt.subplots(2,2, figsize=(10,10))
    
    plot_all(axes[0,0], tbcleans, azclean, elevclean, 
        'Random 2012 PDS dataset, Ch {0}, Det {1}'.format(channel,det))

    for i,tbdata,azdata,elevdata,ax in zip([1,2,3],
                                         tbnoise,
                                         aznoise,
                                         elevnoise,
                                         axes.flatten()[1:]):
        plot_all(ax, tbdata, azdata, elevdata, 
            'Noisy dataset {0}, Ch {1}, Det {2}'.format(i,channel,det))

    cleantup = get_abs_fft(tbcleans)
    print(len(cleantup))
    noisetub = [get_abs_fft(data) for data in tbnoise]
    
    figff, axes = plt.subplots(2,2, figsize=(10,10))
    plot_fft(axes[0,0], cleantup, 'FFT of a 2012 PDS dataset')
    
    for i,ftbdata,ax in zip([1,2,3],
                            noisetub,
                            axes.flatten()[1:]):
        plot_fft(ax, ftbdata, 
            'FFT of noisy data {0}, Ch {1}, Det {2}'.format(i,channel, det))

    plt.show()
    
if __name__ == '__main__':
    main()