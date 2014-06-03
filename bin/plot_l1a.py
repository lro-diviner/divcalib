#!/usr/bin/env python

from diviner import file_utils as fu
import sys
from matplotlib.pyplot import show

tstr = sys.argv[1]

obs = fu.DivObs(tstr)
df = obs.get_l1a()

df['b1_11'].plot()

show()
