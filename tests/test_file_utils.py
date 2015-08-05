from diviner import file_utils as fu
import datetime as dt
import pandas as pd
import os
import pytest
from diviner.exceptions import DivTimeLengthError, RDRR_NotFoundError,\
    RDRS_NotFoundError, L1ANotFoundError

# define a time string that connects to an L1A file that is also available
# on laptop
tstr = '2013031707'
tstr_fail = '2006120123'
l1aext = '_L1A.TAB'
rdrrext = '.rdrr'
rdrsext = '.rdrs'
tstr_accumulate = '2010011315'
l1afname = '/Users/maye/data/diviner/l1a_data/2013052205_L1A.TAB'


@pytest.mark.luna
def test_get_rdr_headers():
    fname_ops = os.path.join(fu.datapath, 'rdr_data', '2013052205_RDR.TAB.zip')
    rdr = fu.RDRReader(fname_ops)
    answer_ops = [
        'date', 'utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk',
        'sclat', 'sclon', 'scrad', 'scalt', 'el_cmd', 'az_cmd', 'af',
        'orientlat', 'orientlon', 'c', 'det', 'vlookx', 'vlooky', 'vlookz',
        'radiance', 'tb', 'clat', 'clon', 'cemis', 'csunzen', 'csunazi',
        'cloctime', 'qca', 'qge', 'qmi']
    assert rdr.headers == answer_ops


def test_parse_times():
    val = '01-Apr-2011 00:00:01.978000'
    format = '%d-%b-%Y %H:%M:%S.%f'
    dtime = dt.datetime.strptime(val, format)
    l = [dtime.strftime('%d-%b-%Y'), dtime.strftime('%H:%M:%S.%f')]
    df = pd.DataFrame(l)
    # previous assignment just provides 1 column with 2 values, need
    # .T(ransform)
    df = df.T
    df.columns = ['date', 'utc']
    parsed = fu.parse_times(df).index[0].to_datetime()
    assert parsed == dtime


class TestDivTime:

    def test_DivHour_failshort(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivHour('20121201')

    def test_DivHour_faillong(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivHour('201212011012')

    def test_DivHour(self):
        fmt = '%Y%m%d%H'
        tstr = '2012070110'
        divhour = fu.DivHour(tstr)
        assert divhour.hour == '10'
        assert divhour.day == '01'
        assert divhour.month == '07'
        assert divhour.year == '2012'
        assert divhour.dtime == dt.datetime.strptime(tstr, fmt)

    def test_DivDay_faillong(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivDay('2012120110')

    def test_DivDay_failshort(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivDay('201201')

    def test_DivDay(self):
        tstr = '20120701'
        divday = fu.DivDay(tstr)
        assert divday.day == '01'
        assert divday.year == '2012'
        assert divday.month == '07'

    def test_DivHour_previous(self):
        tstr = '2012010210'
        divhour = fu.DivHour(tstr)
        previous = divhour.previous()
        assert previous.tstr == '2012010209'

    def test_DivHour_next(self):
        tstr = '2012010210'
        divhour = fu.DivHour(tstr)
        next = divhour.next()
        assert next.tstr == '2012010211'

    def test_DivTime_from_dtime(self):
        now = dt.datetime(2012, 10, 1, 17)
        divhour = fu.DivHour.from_dtime(now)
        assert divhour.dtime == now


class TestDivObs:

    def test_DivObs(self):
        obs = fu.DivObs(tstr)
        assert obs.time.hour == '07'

    def test_DivObs_l1a(self):
        obs = fu.DivObs(tstr)
        assert obs.l1afname.name == os.path.join(fu.l1adatapath, tstr + l1aext)

    def test_FileName_from_tstr(self):
        fname = fu.L1AFileName.from_tstr(tstr)
        assert fname.name == os.path.join(fu.l1adatapath, tstr + l1aext)

    def test_DivObs_general(self):
        fu.DivObs(tstr)

    def test_DivObs_get_fail(self):
        obs = fu.DivObs(tstr_fail)
        with pytest.raises(RDRR_NotFoundError):
            obs.get_rdrr()

    def test_DivObs_from_fname(self):
        fu.DivObs.from_fname(l1afname)


class TestL1ADataFile:

    def test_open(self):
        obs = fu.DivObs(tstr)
        fu.L1ADataFile(obs.l1afname.path).open()

    def test_open_fail(self):
        obs = fu.DivObs(tstr_fail)
        with pytest.raises(L1ANotFoundError):
            fu.L1ADataFile(obs.l1afname.path).open()


# def test_open_and_accumulate():
#     fu.open_and_accumulate(tstr=tstr_accumulate)

def test_open_and_accumulate_fail():
    with pytest.raises(L1ANotFoundError):
        fu.open_and_accumulate(tstr_fail)


def test_open_and_accumulate():
    fu.open_and_accumulate(tstr_accumulate)


class TestRDRXReader:

    def test_RDRR_Reader_init(self):
        obs = fu.DivObs(tstr)
        obs.get_rdrr()

    def test_RDRR_Reader_init_fail(self):
        obs = fu.DivObs(tstr_fail)
        with pytest.raises(RDRR_NotFoundError):
            fu.RDRR_Reader(obs.rdrrfname.path)
