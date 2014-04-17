from diviner import calib, file_utils as fu
from diviner import ana_utils as au
from diviner import get_divdata as gd
from diviner import data_prep as dp
import sys
import logging
from matplotlib.pyplot import subplots, savefig

logging.basicConfig(filename='divcalib.log',
               format='%(asctime)s %(message)s',
            level=logging.INFO)

c = 9
det = 1
detend=21
tstrings = ['2012070100','2013010100']
for tstr in tstrings:
    print tstr
    rdr1 = gd.get_divdata(tstr, c, det, detend=detend, save_hdf=True)
    l1a = fu.open_and_accumulate(tstr=tstr)
    rdr2 = calib.Calibrator(l1a, do_jpl_calib=True)
    rdr2.calibrate()
    helper = au.CalibHelper(rdr2)
    fig, ax = subplots(3, figsize=(13,10),sharex=True,sharey=True)
    for i,det in enumerate([1,11,21]):
        rad1 = rdr1[rdr1.det==det].radiance
        rad2 = helper.get_cdet_rad(c, det, tstr).ix[rad1.index]
        ratio = rad1/rad2
        ratio.plot(ax=ax[i])
        ax[i].set_ylim([-1,3])
        ax[i].set_title("Detector {}".format(det))
    fig.suptitle(tstr)
    savefig('plots/'+tstr+'_ratios_1_11_21.png',dpi=200)
