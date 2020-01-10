from importlib.resources import path as resource_path

import pandas as pd

from . import rdrx

with resource_path("diviner.data", "divdata_columns.csv") as p:
    divdata_columns = pd.read_csv(p).iloc[:, 0]

with resource_path("diviner.data", "joined_format_file.csv") as p:
    rdr_columns = pd.read_csv(p)['colname']

with resource_path("diviner.data", "newfmt_master.csv") as p:
    rdr2_columns = pd.read_csv(p)['colname']

cols_no_melt = [i for i in rdr_columns if i in rdrx.no_melt]
cols_skip = "c det tb radiance".split()
cols_to_melt = list(set(rdr_columns) - set(cols_no_melt) - set(cols_skip))
cols_to_melt = [i for i in cols_to_melt if i in rdrx.to_melt]

flags = ["o", "v", "i", "m", "q", "p", "e", "z", "t", "h", "d", "n", "s", "a", "b"]

rdr2_pipe_cols = divdata_columns[:6].tolist() + rdr2_columns[2:].tolist()
