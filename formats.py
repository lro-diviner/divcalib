from pds.core.parser import Parser
import StringIO
from collections import OrderedDict, namedtuple

def get_columns_from_rdr_columns(fname=None):
    "Generator to yield items of the rdr_columns file."
    RDRColumn = namedtuple('RDRColumn', 'colno, colname, type_format, desc')
    if not fname:
        fname = '../../data/rdr_columns.txt'
    with open(fname) as f:
        data = f.readlines()
    # use this counter to know when 4 items were collected
    counter = 0
    container = []
    for line in data:
        if not line.strip():
            continue
        container.append(line.strip())
        counter += 1
        if counter == 4:
            yield RDRColumn(*container)
            counter = 0
            container = []


def get_formats_dict():
    dic = OrderedDict()
    for col in get_columns_from_rdr_columns():
        dic[col.colname] = col
    return dic


def create_formatdic_for_dataframe():
    """Generate format dictionary to be used for pandas.DataFrame.to_string().
    
    Currently not in use, because of DataFrame.to_string bug:
    https://github.com/pydata/pandas/issues/4158
    
    Saving this part, can be used for when to_string() is being repaired.
    """


    # general formatter
    def format_general(input, prec_string, type_string):
        return '{:>{prec}{type}},'.format(input, prec=prec_string,
                                          type=type_string)

    # general float formatter, receiving width and prec as input as well
    def format_float(input, prec_string):
        return format_general(input, prec_string, type_string='f')


    def format_integer(input, prec_string):
        return format_general(input, prec_string, type_string='d')


    def date(input):
        # return '"{:>11}",'.format(input.strip())
        return '"%11s",' % input

    def utc(input):
        return '"{:>12}",'.format(input.strip())
    

    def jdate(input):
        return format_float(input, '17.9')


    def orbit(input):
        return format_integer(input, '5')


    def sundist(input):
        return format_float(input, '7.5')


    def sunlat(input):
        return format_float(input, '8.5')


    def sunlon(input):
        return format_float(input, '9.5')


    def sclk(input):
        return format_float(input, '16.5')


    def sclatlon(input):
        return format_float(input, '9.5')


    def scradalt(input):
        return format_float(input, '11.5')


    def elaz_cmd(input):
        return format_float(input, '7.3')


    def af(input):
        return format_integer(input, '4')


    def orientlatlon(input):
        return format_float(input, '9.5')


    def c(input):
        return format_integer(input, '1')


    def det(input):
        return format_integer(input, '3')


    def vlook(input):
        return format_float(input, '9.6')


    def radiance(input):
        return format_float(input, '10.4')


    def tb(input):
        return format_float(input, '8.3')


    def clatlonemissunzenazi(input):
        return format_float(input, '9.5')


    def cloctime(input):
        return format_float(input, '8.5')


    def cphase(input):
        return format_float(input, '9.5')


    def flag(input):
        return format_integer(input, '1')


    def roi(input):
        return format_integer(input, '4')
    
    # this is the formatters dictionary for the dataframe.to_string() call  
    format_dic = {'date':date,
                  'utc':utc,
                  'jdate':jdate,
                  'orbit':orbit,
                  'sundist':sundist,
                  'sunlat':sunlat,
                  'sunlon':sunlon,
                  'sclk':sclk,
                  'sclat':sclatlon,
                  'sclon':sclatlon,
                  'scrad':scradalt,
                  'scalt':scradalt,
                  'el_cmd':elaz_cmd,
                  'az_cmd':elaz_cmd,
                  'af':af,
                  'orientlat':orientlatlon,
                  'orientlon':orientlatlon,
                  'c':c,
                  'det':det,
                  'vlookx':vlook,
                  'vlooky':vlook,
                  'vlookz':vlook,
                  'radiance':radiance,
                  'tb':tb,
                  'clat':clatlonemissunzenazi,
                  'clon':clatlonemissunzenazi,
                  'cemis':clatlonemissunzenazi,
                  'csunzen':clatlonemissunzenazi,
                  'csunazi':clatlonemissunzenazi,
                  'cloctime':cloctime,
                  'qca':flag,
                  'qge':flag,
                  'qmi':flag}

    return format_dic

#####
#######
#####


class Formatter(object):
    format_list =[(0,'date','"{:>11s}"'),
                  (1,'utc','"{:>12s}"'),
                  (2,'jdate','{:17.9f}'),
                  (3,'orbit','{:5d}'),
                  (4,'sundist','{:7.5f}'),
                  (5,'sunlat','{:8.5f}'),
                  (6,'sunlon','{:9.5f}'),
                  (7,'sclk','{:016.5f}'),
                  (8,'sclat','{:9.5f}'),
                  (9,'sclon','{:9.5f}'),
                  (10,'scrad','{:11.5f}'),
                  (11,'scalt','{:11.5f}'),
                  (12,'el_cmd','{:7.3f}'),
                  (13,'az_cmd','{:7.3f}'),
                  (14,'af','{:4d}'),
                  (15,'orientlat','{:9.5f}'),
                  (16,'orientlon','{:9.5f}'),
                  (17,'c','{:1d}'),
                  (18,'det','{:3d}'),
                  (19,'vlookx','{:9.6f}'),
                  (20,'vlooky','{:9.6f}'),
                  (21,'vlookz','{:9.6f}')]
              
    subformat_nominal = [
                      (22,'radiance','{:10.4f}'),
                      (23,'tb','{:8.3f}'),
                      (24,'clat','{:9.5f}'),
                      (25,'clon','{:9.5f}'),
                      (26,'cemis','{:9.5f}'),
                      (27,'csunzen','{:9.5f}'),
                      (28,'csunazi','{:9.5f}'),
                      (29,'cloctime','{:8.5f}'),
                      ]

    # for spaceviews
    subformat_space = [
                      (22,'radiance','{:10.4f}'),
                      (23,'tb','{:8.3f}'),
                      (24,'clat','{:9.1f}'),
                      (25,'clon','{:9.1f}'),
                      (26,'cemis','{:9.1f}'),
                      (27,'csunzen','{:9.1f}'),
                      (28,'csunazi','{:9.1f}'),
                      (29,'cloctime','{:8.1f}'),
                     ]

    # when looking at the solar target, we calculate csunzen and csunazi for the 
    # illumination of the target
    subformat_solartarget = [
                      (22,'radiance','{:10.4f}'),
                      (23,'tb','{:8.3f}'),
                      (24,'clat','{:9.1f}'),
                      (25,'clon','{:9.1f}'),
                      (26,'cemis','{:9.1f}'),
                      (27,'csunzen','{:9.5f}'),
                      (28,'csunazi','{:9.5f}'),
                      (29,'cloctime','{:8.1f}'),
                     ]

    subformat_nan = [
                      (22,'radiance','{:10.1f}'),
                      (23,'tb','{:8.1f}'),
                      (24,'clat','{:9.1f}'),
                      (25,'clon','{:9.1f}'),
                      (26,'cemis','{:9.1f}'),
                      (27,'csunzen','{:9.1f}'),
                      (28,'csunazi','{:9.1f}'),
                      (29,'cloctime','{:8.1f}'),
                     ]
                 
    subformat_rest = [
                      (30,'cphase','{:9.5f}'),
                      (31,'roi','{:4d}'),
                     ]
    flags = ['o', 'v', 'i', 'm', 'q', 'p', 'e', 'z', 't', 'h', 'd', 'n', 
             's', 'a', 'b']
         
    for i,flag in enumerate(flags):
        subformat_rest += [(i+32, flag, '{:1d}')]
       
    format_nominal = format_list + subformat_nominal + subformat_rest
    format_space = format_list + subformat_space + subformat_rest
    format_solartarget = format_list + subformat_solartarget + subformat_rest
    format_nan  = format_list + subformat_nan  + subformat_rest

    nominal     = [i[2] for i in format_nominal]
    space       = [i[2] for i in format_space]
    solartarget = [i[2] for i in format_solartarget]
    nan         = [i[2] for i in format_nan]


# def parse_rdr_format_file(fname=None):
#     if not fname:
#         fname = '../../data/rdr_format.txt'
#     parser = Parser()
#     with open(fname) as f:
#         rdrformat = f.readlines()
#     s = ''
#     for line in rdrformat:
#         if line == '\n':
#             sio = StringIO.StringIO(s)
#             yield parser.parse(sio)['COLUMN']
#             s = ''
#         s += line
#         
#     
# def get_formats_dic():
#     dic = OrderedDict()
#     for col in parse_rdr_format_file():
#         dic[col['NAME']] = col
#     return dic


