from __future__ import division, print_function
import spice
import os
from diviner.file_utils import kernelpath
from datetime import datetime as dt
from numpy import degrees, arccos

currentdir = os.getcwd()
os.chdir(kernelpath)
spice.furnsh("fk/lro_frames_2012255_v02.tf")
spice.furnsh("fk/lro_dlre_frames_2010132_v04.tf")
spice.furnsh("ick/lrodv_2010090_2010121_v01.bc")
spice.furnsh("lsk/naif0010.tls")
spice.furnsh('sclk/lro_clkcor_2009182_v00.tsc')
spice.furnsh("spk/fdf29_2010100_2010101_n01.bsp")
spice.furnsh('./planet_spk/de421.bsp')
# spice.furnsh("ck/moc42_2010100_2010100_v01.bc")

time = dt(2009,6,24,0,1,8)

print("Testing for time ", time, '\nIn kernel-time: ', time.strftime("%Y%j"),
      'plus {0} hours.'.format(time.hour))
et = spice.utc2et(time.isoformat())

# ckernels = ['moc42_2010100_2010100_v01.bc', 'moc42_2010100_2010101_v01.bc',
            # 'moc42_2010100_2010101_v02.bc']
ckernels = ['moc42_2009174_2009175_v01.bc','moc42_2009175_2009176_v02.bc']

for ck in ckernels:
    spice.furnsh('ck/'+ck)
    print("Loading {0}".format(ck))
    t = spice.spkpos('sun', et, 'LRO_DLRE_SCT_REF', 'lt+s', 'lro')
    unitv = spice.vhat(t[0])
    print(t[0], "Zenith angle:", degrees(arccos(unitv[2])))
    spice.unload('ck/'+ck)

