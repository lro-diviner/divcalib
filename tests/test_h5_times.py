#!/usr/bin/env python

import pandas as pd
import time

store = pd.HDFStore('/u/paige/maye/raid/rdr20_month_samples/nominal/C9_compressed.h5')
t1 = time.time()
store.select('df','clat < -85',columns=['clat','clon','tb'])
print time.time() - t1
store.close()
store = pd.HDFStore('/u/paige/maye/raid/rdr20_month_samples/nominal/C9.h5')
t1 = time.time()
store.select('df','clat < -85',columns=['clat','clon','tb'])
print time.time() - t1

