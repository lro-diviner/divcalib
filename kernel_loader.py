# coding: utf-8
import os
import spice
from datetime import datetime as dt
from file_utils import kernelpath

os.chdir(kernelpath)
spice.furnsh("ck/moc42_2010100_2010101_v02.bc")
spice.furnsh("fk/lro_frames_2012255_v02.tf")
spice.furnsh("fk/lro_dlre_frames_2010132_v04.tf")
spice.furnsh("ick/lrodv_2010090_2010121_v01.bc")
spice.furnsh("lsk/naif0010.tls")
spice.furnsh('sclk/lro_clkcor_2010096_v00.tsc')
spice.furnsh("spk/fdf29_2010100_2010101_n01.bsp")
spice.furnsh('./spk/de421.bsp')

utc = dt.strptime('2010100 10','%Y%j %H').isoformat()
et = spice.utc2et(utc)
print spice.spkpos('sun',et,'LRO_DLRE_SCT_REF','lt+s','lro')