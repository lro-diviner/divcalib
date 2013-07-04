from diviner import file_utils as fu
from nose.tools import assert_equals

class TestDiv247DataPump():
    """docstring for test_Div247DataPump"""
    @classmethod
    def setup_class(cls):
        pump = fu.Div247DataPump('20110416')
        
    def test_find_fnames(self):
        pass

def test_get_rdr_headers():
    fname_ops = '/Users/maye/data/diviner/opsRDR/2013052205_RDR.TAB'
    fname_pds = '/Users/maye/data/diviner/pdsRDR/201205070100_RDR.TAB'
    headers_ops = fu.get_rdr_headers(fname_ops)
    headers_pds = fu.get_rdr_headers(fname_pds)
    answer_ops = ['date', 'utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk', 
              'sclat', 'sclon', 'scrad', 'scalt', 'el_cmd', 'az_cmd', 'af', 'orientlat', 
              'orientlon', 'c', 'det', 'vlookx', 'vlooky', 'vlookz', 'radiance', 'tb', 
              'clat', 'clon', 'cemis', 'csunzen', 'csunazi', 'cloctime', 'qca', 'qge', 'qmi']
    # due to an oversight, two columns in the PDS header have other names:
    answer_pds = ['date', 'utc', 'jdate', 'orbit', 'sundist', 'sunlat', 'sunlon', 'sclk', 
              'sclat', 'sclon', 'scrad', 'scalt', 'el_cmd', 'az_cmd', 'af', 'vert_lat', 
              'vert_lon', 'c', 'det', 'vlookx', 'vlooky', 'vlookz', 'radiance', 'tb', 
              'clat', 'clon', 'cemis', 'csunzen', 'csunazi', 'cloctime', 'qca', 'qge', 'qmi']
    assert_equals(headers_pds, answer_pds)
    assert_equals(headers_ops, answer_ops)

def test_get_fname_hour():
    fname = '/Users/maye/data/diviner/opsRDR/2013052205_RDR.TAB'
    fnameC = fu.FileName(fname)
    assert_equals(fnameC.year, '2013')
    assert_equals(fnameC.month, '05')
    assert_equals(fnameC.day, '22')
    assert_equals(fnameC.hour, '05')
