from diviner import file_utils as fu
import datetime as dt
import pandas as pd
import os
import pytest
from diviner.exceptions import DivTimeLengthError

# define a time string that connects to an L1A file that is also available on laptop
tstr = '2012010100'

# get slow marker to exclude some tests on laptop
slow = pytest.mark.slow


class TestDiv247DataPump():
    """docstring for test_Div247DataPump"""
    @classmethod
    def setup_class(cls):
        pump = fu.Div247DataPump('20110416')
        
    def test_find_fnames(self):
        pass

@slow
def test_get_rdr_headers():
    fname_ops = os.path.join(fu.datapath,'rdr_data','2013052205_RDR.TAB.zip')
    rdr = fu.RDRReader(fname_ops)
    answer_ops = ['date', 'utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk', 
              'sclat', 'sclon', 'scrad', 'scalt', 'el_cmd', 'az_cmd', 'af', 'orientlat', 
              'orientlon', 'c', 'det', 'vlookx', 'vlooky', 'vlookz', 'radiance', 'tb', 
              'clat', 'clon', 'cemis', 'csunzen', 'csunazi', 'cloctime', 'qca', 'qge', 'qmi']
    assert rdr.headers == answer_ops



def test_parse_times():
    val = '01-Apr-2011 00:00:01.978000'
    format = '%d-%b-%Y %H:%M:%S.%f'
    dtime = dt.datetime.strptime(val, format)
    l = [dtime.strftime('%d-%b-%Y'),dtime.strftime('%H:%M:%S.%f')]
    df = pd.DataFrame(l)
    # previous assignment just provides 1 column with 2 values, need .T(ransform)
    df = df.T
    df.columns = ['date','utc']
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
        assert divhour.time == dt.datetime.strptime(tstr, fmt)
    
    def test_DivDay_faillong(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivDay('2012120110')

    def test_DivDay_failshort(self):
        with pytest.raises(DivTimeLengthError):
            fu.DivDay('201201')

    def test_DivDay(self):
        fmt = '%Y%m%d'
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
