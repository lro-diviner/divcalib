#!/usr/bin/env python

import sys
from optparse import OptionParser
import datetime as dt


class OptionParser(object):

    """Manage command-line options for divcalib"""

    def __init__(self, argv):
        super(OptionParser, self).__init__()
        self.argv = argv
        try:
            time_option = argv[0]
        except IndexError:
            usage()
        times = time_option.split('=')[1].split(',')
        for i, time in enumerate(times):
            if time:
                dtime = self.parse_timestr(time)
                print("Found time", dtime)
                setattr(self, 'time{0}'.format(i), dtime)

    def parse_timestr(self, timestr):
        try:
            format = '%Y%m%d'
            dtime = dt.datetime.strptime(timestr, format)
        except ValueError:
            format = '%Y%m%d%H'
            dtime = dt.datetime.strptime(timestr, format)
        return dtime


def usage():
    print("usage: {0} -daterange=start[,end]".format(sys.argv[0]))
    sys.exit()


def parse_options():
    pass


def main():
    options = OptionParser(sys.argv[1:])
    print(options.time0)

if __name__ == '__main__':
    main()

    # usage = "usage: %prog -daterange start,end"
    # descript = """Tool to provide brightness temperatures calibrated the new way."""
    # """Currently, only the time columns, clat, clon and Tb are provided."""
    #
    # op = OptionParser(usage=usage, description=descript)
    # op.add_option("-d",
    #               "--daterange",
    #               action="store_true",
    #               dest="time_tuple",
    #               help="daterange in the same format as divdata",
    #               default=True)
    #
    # (options, args) = op.parse_args()
    # print(options)
    # print(args)
