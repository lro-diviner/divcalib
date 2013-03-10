#!/Library/Frameworks/EPD64.framework/Versions/7.3/bin/enpkg
from __future__ import division
import matplotlib
matplotlib.use('Qt4Agg')
from scipy.constants import k as kb
from scipy.constants import c,h
import numpy as np
from matplotlib.pyplot import figure, show
 
def planck_wavelength(T, wavelength):
    nom = 2*h*c*c
    denom = wavelength**5*(np.exp( h*c/(kb*T*wavelength)) - 1)
    return nom/denom
    
def rayleigh_jeans(T, wavelength):
    nom = 2*kb*c*T
    denom = wavelength**4
    return nom/denom
    
def wien_approx(T, wavelength):
    nom = 2*h*c*c
    denom = wavelength**5
    eterm = -h*c/(wavelength*kb*T)
    return nom/denom * np.exp(eterm)
    
if __name__ == '__main__':
    temps = np.arange(0, 500)
    waves = np.linspace(300,3000, 100)
    waves = waves*1e-9
    
    fig = figure()
    ax = fig.add_subplot(111)
    for t in range(1000,7500,1000):
        planck = planck_wavelength(t,waves)
        # rj = rayleigh_jeans(t,waves)
        # wa = wien_approx(t,waves)
        # p_rj = planck/rj
        # p_wa = planck/wa
        # div by 1e6 to have radiance in per micron
        ax.plot(waves*1e6, planck, label='{0}K, Radiance: {1:.1e}'.format(t,np.sum(planck/1e6)))
    ax.grid()
    ax.legend(loc='best')
    ax.set_xlabel('Wavelength [micron]')
    ax.set_ylabel('Spectral radiance [mW / (m^2 sr micron)]')
    ax.set_title('Blackbody radiation at lowest temperatures.')
    show()