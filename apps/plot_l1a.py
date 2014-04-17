#!/usr/bin/env python

from diviner import file_utils as fu
import sys
from matplotlib.pyplot import show

tstr = sys.argv[1]

df= fu.get_clean_l1a(tstr)

df['b1_11'].plot()

show()


