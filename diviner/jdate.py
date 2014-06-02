#
# jdate.py
#
# Purpose:
#   Convert among JD, MJD, decimal year, and ordinal date
# By:
#  MRB, NYU, 2009-10-30
# $Id$
# 

"""
jdate converts among Julian Date, Modified Julian Date, Julian Year,
and proleptic Gregorian ordinal day.  The JD and MJD are defined in
accordance with the standard astronomical definitions, in units of
days. The Julian Year is defined as the Calendar Year C.E., with a
fractional offset equal to the days since beginning of year divided by
365.25. Proleptic Gregorian ordinal day is the ordinal day used by the
datetime module for python.
"""

__author__ = 'Michael Blanton <michael.blanton@gmail.com>'

__version__ = '$Revision: $'.split(': ')[1].split()[0]

__all__ = [ 'mjd2jd', 'jd2mjd',
            'jd2jyear', 'jyear2jd',
            'jd2ordinal', 'ordinal2jd' ]


#
# Modules
#
from math import *
from numpy import *
from datetime import *

#
# Classes
#
        
#
# Functions
#
def mjd2jd(mjd):
    """
    Convert Modified Julian Date (MJD) to Julian Date (JD)
    (offset of 2400000.5 days)
    """
    offset=2400000.5
    jd=mjd+offset
    return jd

def jd2mjd(jd):
    """
    Convert Julian Date (JD) to Modified Julian Date (MJD)
    (offset of 2400000.5 days)
    """
    offset=2400000.5
    mjd=jd-offset
    return mjd

def jd2jyear(jd):
    """
    Convert Julian Date (JD) to Julian Year 
    (in years CE; e.g. JD=2451544.50000 -> JY=2000.00)
    """
    ordinal= jd2ordinal(jd)
    jyear= zeros(len(ordinal))
    for i in range(len(ordinal)):
        dt= datetime.fromordinal(int(ordinal[i]))
        year= dt.year
        ordinalday1= (datetime(year, 1, 1)).toordinal()
        dordinal= ordinal[i]-float(ordinalday1)
        jyear[i]= float(year)+dordinal/365.25
    return jyear

def jyear2jd(jyear):
    """
    Convert Julian Year to Julian Date (JD) 
    (JY in years CE; e.g. JD=2451544.50000 -> JY=2000.00)
    """
    jd= zeros(len(jyear))
    for i in range(len(jyear)):
        iyear= int(jyear[i])
        offyear= jyear[i]- float(iyear)
        ordinalday1= (datetime(iyear,1,1)).toordinal()
        dordinal= offyear*365.25
        jd[i]= ordinal2jd(ordinalday1+dordinal)
    return jd

def jd2ordinal(jd):
    """
    Convert Julian Date (JD) to Proleptic Gregorian Ordinal Date
    (in latter, Year 1 Day 1 00:00:00 is 1). Returns a float type
    ordinal number, not int.
    """
    offset0=1721425.5
    ordinal=(jd-offset0)+1.
    return ordinal

def ordinal2jd(ordinal):
    """
    Convert Proleptic Gregorian Ordinal Date to Julian Date (JD) (in
    former, Year 1 Day 1 00:00:00 is 1). Can take a float type ordinal
    number, not limited to int.
    """
    offset0=1721425.5
    jd=ordinal-1.+offset0
    return jd

#
# Unit tests
#
if __name__ == '__main__':
    years= array((2000, 1, 2010, 2010))
    months= array((1, 1, 12, 12))
    days= array((1, 1, 25, 24))
    mjd=array((51544.0000, -678575., 55555., 55554.))

    # check conversions to JD
    print "Checking mjd2jd, jd2mjd ... "
    err=0
    jd= mjd2jd(mjd)
    mjdback= jd2mjd(jd)
    for i in range(len(mjdback)):
        if mjd[i]!=mjdback[i]:
            print "ERROR: mjd2jd -> jd2mjd failed!"
            err=1
    if err==0:
        print "OK!"

    # check conversions to JY
    print "Checking jd2jyear, jyear2jd ... "
    err=0
    jy= jd2jyear(jd)
    jdback= jyear2jd(jy)
    for i in range(len(jdback)):
        if jd[i]!=jdback[i]:
            print "ERROR: jd2jyear -> jyear2jd failed!"
            err=1
    if err==0:
        print "OK!"

    # check conversions to ordinal
    print "Checking ordinal2jd, jd2ordinal ... "
    err=0
    ordinal= jd2ordinal(jd)
    jdback= ordinal2jd(ordinal)
    for i in range(len(jdback)):
        if jd[i]!=jdback[i]:
            print "ERROR: jd2ordinal -> ordinal2jd failed!"
            err=1
    if err==0:
        print "OK!"
    
    # print dates
        print "Checking correctness of date translation ... "
        err=0
        for i in range(len(ordinal)):
            dt= datetime.fromordinal(int(ordinal[i]))
            if(days[i] != dt.day):
                print "ERROR: in day result ", dt
                err=1
            if(months[i] != dt.month):
                print "ERROR: in month result ", dt
                err=1
            if(years[i] != dt.year):
                print "ERROR: in year result ", dt
                err=1
        if err==0:
            print "OK!"