#! /usr/bin/env python
from __future__ import division, print_function
import numpy as np
import sys
# remove when cleanup done
from numpy import *
from sys import *
# end remove
from diviner import file_utils as fu
from divininer import calib

# Read in scaling factors
# These were derived from extensive stowed periods
# Individual detectors will be corrected for Ch. 3-6
# The same scaling factor will be used for all detectors of Ch. 7-9.
# Ch. 1-2 will not be corrected since they were used in the first place to derive the correction.

factors = np.loadtxt("scaling_factors.ascii", dtype=float)

# factors = transpose(factors, (1,0))
# equivalent
factors = factors.T

def main(infile):
    # Read in L1A count data. Isolate noise from Channels 1-2

    outfile = infile + ".corrected"

    original = fu.L1ADataFile(infile).open()
    data = original[calib.detectors]
    
    boxcar = np.zeros(75) + (1./75.)
    ch1and2 = data.filter(regex='a[1,2]_')
    
    ch1and2['averaged'] = ch1and2.mean(axis=1)
    ch1and2['convolved'] = np.convolve(ch1and2['averaged'], boxcar, mode='same')
    ch1and2['noise'] = ch1and2['averaged'] - ch1and2['convolved']


    # Calculate detector maximum/minimum DN values for Channels 1-2
    # This will be used to identify sunlit/warm surfaces and
    # calibration observations. If the maximum DN difference
    # for the previous and post 40 observations for any detector
    # exceeds 50, the noise is set to zero and the observation is
    # not corrected.

    length = data.shape[0]

    c1 = zeros((length,21,81))
    c2 = zeros((length,21,81))


    for i in xrange(0,81):
        c1[40:length-40, :, i] = data.ix[i:length-80+i, 'a1_01':'a1_21']
        c2[40:length-40, :, i] = data.ix[i:length-80+i, 'a2_01':'a2_21']


    # Look for highest difference in DN in Ch 1-2 all detectors

    max_diff1 = ma.max(ma.max(c1, axis=2) - ma.min(c1, axis=2), axis=1)
    max_diff2 = ma.max(ma.max(c2, axis=2) - ma.min(c2, axis=2), axis=1)
    max_diff = ma.max(transpose( dstack( (max_diff1, max_diff2) ),
                      (1,0,2)), 
                      axis=2)

    max_diff = max_diff.flatten()

    # Where the DN difference exceeds 50, set noise to zero.

    noise = where(max_diff<=50, noise, 0)

    # The first and last 40 lines cannot be checked.

    noise[0:40] = 0
    noise[length-40:length] = 0

    # Finally, correct the data - scale the noise and subtract it off
    # Clone the noise array for each detector - I'm sure there's a more elegant way to do this...

    noise=transpose(vstack((noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise, noise)), (1,0))

    data[:,42:63]=data[:,42:63]-factors[:,2]*noise
    data[:,63:84]=data[:,63:84]-factors[:,3]*noise
    data[:,84:105]=data[:,84:105]-factors[:,4]*noise
    data[:,105:126]=data[:,105:126]-factors[:,5]*noise
    data[:,126:147]=data[:,126:147]-factors[:,6]*noise
    data[:,147:168]=data[:,147:168]-factors[:,7]*noise
    data[:,168:189]=data[:,168:189]-factors[:,8]*noise

    savetxt(outfile, data, fmt='%.2f', delimiter=",")

if __name__ == '__main__':
    infile = sys.argv[1]
    
    main(infile)
