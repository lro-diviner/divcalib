# coding: utf-8
import os
import spice
from datetime import datetime as dt
from diviner.file_utils import kernelpath
from diviner import spicekerneltools
from nose.tools import assert_equals


def test_example_loading():
    currentdir = os.getcwd()
    os.chdir(kernelpath)
    spice.furnsh("ck/moc42_2010100_2010100_v01.bc")
    spice.furnsh("fk/lro_frames_2012255_v02.tf")
    spice.furnsh("fk/lro_dlre_frames_2010132_v04.tf")
    spice.furnsh("ick/lrodv_2010090_2010121_v01.bc")
    spice.furnsh("lsk/naif0010.tls")
    spice.furnsh('sclk/lro_clkcor_2010096_v00.tsc')
    spice.furnsh("spk/fdf29_2010100_2010101_n01.bsp")
    spice.furnsh('./planet_spk/de421.bsp')

    utc = dt.strptime('2010100 05', '%Y%j %H').isoformat()
    et = spice.utc2et(utc)
    t = spice.spkpos('sun', et, 'LRO_DLRE_SCT_REF', 'lt+s', 'lro')
    print(t)
    answer = ((-63972935.85033857, -55036272.7848299, 123524941.9877458),
                499.009424105693)
    for i, j in zip(t[0], answer[0]):
        assert_equals(round(i, 3), round(j, 3))
    os.chdir(currentdir)


def test_get_version_from_fname():
    fname = 'moc42_2009099_2009100_v01.bc'
    version = 1
    assert_equals(('v01',version), kerneltools.get_version_from_fname(fname))


def test_get_times_from_ck():
    fname = 'moc42_2009099_2009100_v01.bc'
    start_time = dt.strptime('2009099', '%Y%j')
    end_time = dt.strptime('2009100', '%Y%j')
    result = kerneltools.get_times_from_ck(fname)
    assert_equals(start_time, result[0])
    assert_equals(end_time, result[1])


def test_CKFileName():
    fname = 'moc42_2009099_2009100_v01.bc'
    start_time = dt.strptime('2009099', '%Y%j')
    end_time = dt.strptime('2009100', '%Y%j')
    ck = kerneltools.CKFileName(fname)
    assert_equals(ck.version_string, 'v01')
    assert_equals(ck.version, 1)
    assert_equals(ck.prefix, 'moc42')
    assert_equals(ck.start, start_time)
    assert_equals(ck.end, end_time)


def test_load_kernels_for_timestr():
    time = dt(2010, 10, 10)
    nr_kernels_to_load = 8
    assert_equals(kerneltools.load_kernels_for_timestr(time),
                  nr_kernels_to_load)

def test_find_ck_for_timestr():
    fname = 'moc42_2010100_2010101_v02.bc'
    time = dt(2010,04,10,17)
    assert_equals(os.path.basename(kerneltools.find_ck_for_timestr(time.isoformat())), fname)
    

    
    