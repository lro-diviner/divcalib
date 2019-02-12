#!/usr/bin/env python

from diviner import file_utils as fu
import os
import sys
import numpy as np
from diviner.formats import Formatter

header = '#        date,            utc,             jdate, orbit, sundist,   sunlat,    sunlon,             sclk,     sclat,     sclon,       scrad,       scalt,  el_cmd,  az_cmd,   af, orientlat, orientlon, c, det,    vlookx,    vlooky,    vlookz,   radiance,       tb,      clat,      clon,     cemis,   csunzen,   csunazi, cloctime,    cphase,  roi, o, v, i, m, q, p, e, z, t, h, d, n, s, a, b'
# example data line, lined up with above header line:
########  "09-Apr-2013", "03:00:00.117", 2456391.625001352, 17271, 0.99911,  0.71518, 200.07568, 0387169200.07077, -15.37966, 171.47133,  1823.75409,    86.43286, 180.000, 240.000,  110,   1.16902,  81.90193, 1,   1,  0.966543, -0.108465,  0.232444,    56.2600,  157.083, -15.47559, 171.36459,   2.96134,  32.66346,  15.76738, 10.08583, 180.00000, 0000, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

class AFHandler(object):
    def __init__(self, af):
        self.af = np.abs(af)

    @property
    def first_digit(self):
        # // is the old truncating way of division
        return self.af // 100

    @property
    def second_digit(self):
        return (self.af % 100) / 10

    @property
    def third_digit(self):
        return self.af % 10


def set_orientation(df):
    df['o'] = AFHandler(df.af).first_digit - 1
    df.o[df.o == 8] = 9

def set_view(df):
    #mapper for old values to new
    mapper = {0: 8,
              1: 0,
              2: 1,
              5: 4,
              6: 5,
              8: 6,
              9: 9}
    tmp = AFHandler(df.af).second_digit
    df['v'] = 0
    for oldval, newval in mapper.items():
        df['v'][tmp == oldval] = newval


def set_instrument(df):
    df['i'] = AFHandler(df.af).third_digit


def set_moving(df):
    df['m'] = 0
    df['m'][df.af < 0] = 1


def set_quality(df):
    df['q'] = df.qca


def set_pointing(df):
    mapper = ((16, 1),
              (4, 2),
              (1, 3))
    df['p']= 0
    for oldval, newval in mapper:
        df.p[np.bitwise_and(df.qge, oldval) !=0] = newval


def set_ephemeris(df):
    mapper = ((32, 1),
              (8, 2),
              (2, 3))
    df['e'] = 0
    for oldval, newval in mapper:
        df.e[np.bitwise_and(df.qge, oldval) !=0] = newval


def process_qmi(df):
    flags = 'zthdsab'
    for flag in flags:
        df[flag] = 0

    vals_to_check = [2, 4, 8, 16, 64]
    for flag, val in zip('zthds', vals_to_check):
        df[flag][np.bitwise_and(df.qmi, val) !=0] = 1


def set_noise(df):
    df['n'] = 0
    df.n[np.bitwise_and(df.qmi, 32) != 0] = 1


def write_rdr20_file(timestr, ch):
    """Generate format strings for one whole line per dataframe.

    this is the alternative, hand-made formatting string for the whole line.
    """

    formatter = Formatter()

    # read in old RDR
    print("Reading old RDR file.")
    rdr = fu.RDRReader('/u/paige/maye/rdr_data/' + timestr + '_RDR.TAB.zip')
    df = rdr.read_df(do_parse_times=False)
    print("Done reading.")

    # add cphase and roi
    df['cphase'] = 123.45678
    df['roi'] = 1234

    # adapt to new format
    # drop the old quality flags
    df = df.drop(['qca', 'qge', 'qmi'], axis=1)

    flags = ['o', 'v', 'i', 'm', 'q', 'p', 'e', 'z', 't', 'h', 'd', 'n',
             's', 'a', 'b']

    set_orientation(df)
    set_view(df)
    set_instrument(df)
    set_moving(df)
    set_quality(df)
    set_pointing(df)
    set_ephemeris(df)
    process_qmi(df)
    set_noise(df)

    for flag in flags:
        df[flag] = 0

    # filter for the channel requested:
    df_ch = df[df.c==int(ch)]

    # fill the nan values of your tb and radiance calculations with -9999.0
    df_ch.fillna(-9999.0, inplace=True)

    # create channel id:
    chid = 'C' + ch

    # open file and start write-loop
    f = open(os.path.join(fu.outpath, timestr + '_' + chid + '_RDR.TAB'), 'w')

    # header defined above, globally for this file.
    print("Starting the write-out.")
    f.write(header + '\r\n')
    for i, data in enumerate(df_ch.values):
        if all(data[22:30] < -5000):
            fmt = formatter.nan
        # spaceview
        elif (all(data[22:24] > -5000)) and (all(data[24:30] < -5000)):
            fmt = formatter.space
        # solartarget view
        elif (all(data[22:24] > -5000) and (all(data[24:27] < -5000)) \
                                       and (all(data[27:29] > -5000))):
            fmt = formatter.solartarget
        # nominal
        elif all(data[22:30] > -5000):
            fmt = formatter.nominal
        # uncaught case, raise exception to notify user!
        else:
            print(i)  # which line
            print(data)  # print whole row
            print("af:", data[14])  # point out af status, might help to understand
            for j, item in enumerate(data[22:30]):
                print(j + 22, item)
            raise Exception
        f.write(', '.join(fmt).format(*data) + '\r\n')
    f.close()
    print("Done writing.")


def usage():
    print("Usage: {0} timestr ch"
    "timestr is used to identify which RDR file to read."
    "ch is the digital number 1..9 to identify for which channel to create the RDR\n"
    "output file.")
    sys.exit()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        usage()
    timestr, ch = sys.argv[1:3]
    write_rdr20_file(timestr, ch)

