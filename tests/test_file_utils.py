from diviner import file_utils as fu
import datetime as dt
import pandas as pd
import os
from nose.tools import assert_equals


class TestDiv247DataPump():
    """docstring for test_Div247DataPump"""
    @classmethod
    def setup_class(cls):
        pump = fu.Div247DataPump('20110416')
        
    def test_find_fnames(self):
        pass


def test_get_rdr_headers():
    fname_ops = os.path.join(fu.datapath,'rdr_data','2013052205_RDR.TAB.zip')
    rdr = fu.RDRReader(fname_ops)
    answer_ops = ['date', 'utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk', 
              'sclat', 'sclon', 'scrad', 'scalt', 'el_cmd', 'az_cmd', 'af', 'orientlat', 
              'orientlon', 'c', 'det', 'vlookx', 'vlooky', 'vlookz', 'radiance', 'tb', 
              'clat', 'clon', 'cemis', 'csunzen', 'csunazi', 'cloctime', 'qca', 'qge', 'qmi']
    assert_equals(rdr.headers, answer_ops)


def test_get_fname_hour():
    fname = '/Users/maye/data/diviner/opsRDR/2013052205_RDR.TAB'
    fnameC = fu.FileName(fname)
    assert_equals(fnameC.year, '2013')
    assert_equals(fnameC.month, '05')
    assert_equals(fnameC.day, '22')
    assert_equals(fnameC.hour, '05')


def test_parse_times_pd_to_datetime():
    val = '01-Apr-2011 00:00:01.978000'
    format = '%d-%b-%Y %H:%M:%S.%f'
    dtime = dt.datetime.strptime(val, format)
    l = [dtime.strftime('%d-%b-%Y'),dtime.strftime('%H:%M:%S.%f')]
    df = pd.DataFrame(l)
    # previous assignment just provides 1 column with 2 values, need .T(ransform)
    df = df.T
    df.columns = ['date','utc']
    parsed = fu.parse_times_pd_to_datetime(df).index[0].to_datetime()
    assert_equals(parsed, dtime)


def test_parse_times_dt_datetime():
    val = '01-Apr-2011 00:00:01.978000'
    format = '%d-%b-%Y %H:%M:%S.%f'
    dtime = dt.datetime.strptime(val, format)
    l = [dtime.strftime('%d-%b-%Y'),dtime.strftime('%H:%M:%S.%f')]
    df = pd.DataFrame(l)
    # previous assignment just provides 1 column with 2 values, need .T(ransform)
    df = df.T
    df.columns = ['date','utc']
    parsed = fu.parse_times_dt_datetime(df).index[0].to_datetime()
    assert_equals(parsed, dtime)
    