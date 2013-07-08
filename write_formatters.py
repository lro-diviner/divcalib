from collections import OrderedDict

# example data line, lined up with above header line:
header = '#        date,            utc,             jdate, orbit, sundist,   sunlat,    sunlon,             sclk,     sclat,     sclon,       scrad,       scalt,  el_cmd,  az_cmd,   af, orientlat, orientlon, c, det,    vlookx,    vlooky,    vlookz,   radiance,       tb,      clat,      clon,     cemis,   csunzen,   csunazi, cloctime,    cphase,  roi, o, v, i, m, q, p, e, z, t, h, d, n, s, a, b'
########  "09-Apr-2013", "03:00:00.117", 2456391.625001352, 17271, 0.99911,  0.71518, 200.07568, 0387169200.07077, -15.37966, 171.47133,  1823.75409,    86.43286, 180.000, 240.000,  110,   1.16902,  81.90193, 1,   1,  0.966543, -0.108465,  0.232444,    56.2600,  157.083, -15.47559, 171.36459,   2.96134,  32.66346,  15.76738, 10.08583, 180.00000, 0000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0


format_list =[('date','"{:>11s}"'),
              ('utc','"{:>12s}"'),
              ('jdate','{:17.9f}'),
              ('orbit','{:5d}'),
              ('sundist','{:7.5f}'),
              ('sunlat','{:8.5f}'),
              ('sunlon','{:9.5f}'),
              ('sclk','{:16.5f}'),
              ('sclat','{:9.5f}'),
              ('sclon','{:9.5f}'),
              ('scrad','{:11.5f}'),
              ('scalt','{:11.5f}'),
              ('el_cmd','{:7.3f}'),
              ('az_cmd','{:7.3f}'),
              ('af','{:4d}'),
              ('orientlat','{:9.5f}'),
              ('orientlon','{:9.5f}'),
              ('c','{:1d}'),
              ('det','{:3d}'),
              ('vlookx','{:9.6f}'),
              ('vlooky','{:9.6f}'),
              ('vlookz','{:9.6f}'),
              ('radiance','{:10.4f}'),
              ('tb','{:8.3f}'),
              ('clat','{:9.5f}'),
              ('clon','{:9.5f}'),
              ('cemis','{:9.5f}'),
              ('csunzen','{:9.5f}'),
              ('csunazi','{:9.5f}'),
              ('cloctime','{:8.5f}'),
              ('cphase','{:9.5f}'),
              ('roi','{:4d}'),
             ]
            
flags = ['o', 'v', 'i', 'm', 'q', 'p', 'e', 'z', 't', 'h', 'd', 'n', 
         's', 'a', 'b']
         
for flag in flags:
    format_list += [(flag,'{:1d}')]
    
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
