#!/Library/Frameworks/EPD64.framework/Versions/7.3/bin/enpkg
from __future__ import division
from scipy.constants import k as kb
from scipy.constants import c, h
import numpy as np
from matplotlib.pyplot import figure, show


def exp_term(T, wavelength=None, nu=None):
    if nu is None:
        return np.exp((h*c) / (wavelength*kb*T))
    else:
        return np.exp((h*nu) / (kb*T))


def planck_wavelength(T, wavelength):
    nom = 2*h*c*c
    denom = wavelength**5 * (exp_term(T, wavelength=wavelength) - 1)
    return nom/denom


def planck_frequency(T, nu):
    nom = 2*h*nu*nu*nu
    denom = c * c * (exp_term(T, nu=nu) - 1)
    return nom/denom


def planck_modis(T, wave):
    c1 = 3.741e-16
    c2 = 1.4393e-2
    denom = wave**5 * (np.exp((c2/(wave*T))) -1)
    return c1/denom


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
    waves = np.linspace(300, 3000, 100)
    waves = waves*1e-9

    fig = figure()
    ax = fig.add_subplot(111)
    for t in range(1000, 7500, 1000):
        planck = planck_wavelength(t, waves)
        # rj = rayleigh_jeans(t,waves)
        # wa = wien_approx(t,waves)
        # p_rj = planck/rj
        # p_wa = planck/wa
        # div by 1e6 to have radiance in per micron
        ax.plot(waves*1e6, planck, label='{0}K, Radiance: {1:.1e}'
                .format(t, np.sum(planck/1e6)))
    ax.grid()
    ax.legend(loc='best')
    ax.set_xlabel('Wavelength [micron]')
    ax.set_ylabel('Spectral radiance [mW / (m^2 sr micron)]')
    ax.set_title('Blackbody radiation at lowest temperatures.')
    show()
