#!/Library/Frameworks/Python.framework/Versions/Current/bin/python

from matplotlib import pyplot as plt
import pandas
import numpy as np
from diviner import read_pprint, read_pds, divplot
from scipy import fft

# choose channel
channel = 9

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
    
def plot_fft(ax, datatuple, title):
    for t,data in datatuple:
        ax.plot(t,data)
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

    fig, axes = plt.subplots(2,2, figsize=(8,8))
    
    plot_all(axes[0,0], tbcleans, azclean, elevclean, 
        'Random PDS dataset, Ch {0}, Det {1}'.format(channel,det))

    for i,tbdata,azdata,elevdata,ax in zip([1,2,3],
                                         tbnoise,
                                         aznoise,
                                         elevnoise,
                                         axes.flatten()[1:]):
        plot_all(ax, tbdata, azdata, elevdata, 
            'Noisy dataset {0}, Ch {1}, Det {2}'.format(i,channel,det))

    cleantup = get_abs_fft(tbcleans)
    noisetub = [get_abs_fft(data) for data in tbnoise]
    
    # figff, axes = plt.figure()
    # axfftclean = plot_fft(, cleantup, 'FFT of random data')
    # 
    # figfftnoise = plt.figure()
    # axfftnoise = plot_fft(figfftnoise, noisetub, 'FFT of noisy data')

    plt.show()
    
if __name__ == '__main__':
    main()