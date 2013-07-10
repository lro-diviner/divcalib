#!/usr/bin/env python
from diviner import file_utils as fu
import os
import sys

# example data line, lined up with above header line:
header = '#        date,            utc,             jdate, orbit, sundist,   sunlat,    sunlon,             sclk,     sclat,     sclon,       scrad,       scalt,  el_cmd,  az_cmd,   af, orientlat, orientlon, c, det,    vlookx,    vlooky,    vlookz,   radiance,       tb,      clat,      clon,     cemis,   csunzen,   csunazi, cloctime,    cphase,  roi, o, v, i, m, q, p, e, z, t, h, d, n, s, a, b'
########  "09-Apr-2013", "03:00:00.117", 2456391.625001352, 17271, 0.99911,  0.71518, 200.07568, 0387169200.07077, -15.37966, 171.47133,  1823.75409,    86.43286, 180.000, 240.000,  110,   1.16902,  81.90193, 1,   1,  0.966543, -0.108465,  0.232444,    56.2600,  157.083, -15.47559, 171.36459,   2.96134,  32.66346,  15.76738, 10.08583, 180.00000, 0000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0


def create_formatdic_for_dataframe():
    """Generate format dictionary to be used for pandas.DataFrame.to_string().
    
    Currently not in use, because of DataFrame.to_string bug:
    https://github.com/pydata/pandas/issues/4158
    
    Saving his part can be used for when to_string() is being repaired.
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


def write_rdr20_file(timestr, ch):
    """Generate format strings for one whole line per dataframe.
    
    this is the alternative, hand-made formatting string for the whole line.
    """


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

    fmts_nominal     = [i[2] for i in format_nominal]
    fmts_space       = [i[2] for i in format_space]
    fmts_solartarget = [i[2] for i in format_solartarget]
    fmts_nan         = [i[2] for i in format_nan]
    
    # read in old RDR
    rdr = fu.RDRReader('/u/paige/maye/rdr_data/'+timestr+'_RDR.TAB.zip')
    df = rdr.read_df(do_parse_times=False)

    ### adapt to new format
    # drop the old quality flags
    df = df.drop(['qca','qge','qmi'],axis=1)
    
    # add cphase and roi
    df['cphase']=123.45678
    df['roi' ] = 1234
    
    # add flag columns as defined above and set to 0 for now.
    for flag in flags:
        df[flag] = 0
    
    # filter for the channel requested:
    df_ch = df[df.c==ch]
    
    # fill the nan values of your tb and radiance calculations with -9999.0
    df_ch.fillna(-9999.0, inplace=True)
    
    # create channel id:
    chid = 'C' + int(ch)
    
    # open file and start write-loop
    f = open(os.path.join(fu.outpath, timestr + '_' + chid + '_RDR.TAB'),'w')

    # header defined above, globally for this file.
    f.write(header+'\r\n')
    for i,data in enumerate(df_ch.values):
        if all(data[22:30] < -5000):
            fmt = fmts_nan
        # spaceview
        elif (all(data[22:24] > -5000)) and (all(data[24:30] < -5000)):
            fmt = fmts_space
        # solartarget view
        elif (all(data[22:24] > -5000) and (all(data[24:27] < -5000)) \
                                       and (all(data[27:29] > -5000))):
            fmt = fmts_solartarget
        # nominal
        elif all(data[22:30] > -5000):
            fmt = fmts_nominal
        # uncaught case, raise exception to notify user!
        else:
            print i # which line
            print data # print whole row
            print "af:",data[14] # point out af status, might help to understand
            for j,item in enumerate(data[22:30]):
                print j+22, item
            raise Exception
        f.write(', '.join(fmt).format(*data)+'\r\n')
    f.close()


def usage():
    print "Usage: {0} timestr ch"
    "timestr is used to identify which RDR file to read."
    "ch is the digital number 1..9 to identify for which channel to create the RDR\n"
    "output file."
    sys.exit()
    

if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    timestr, ch = sys.argv[1:3]
    write_rdr20_file(timestr, ch)

