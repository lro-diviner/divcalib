from __future__ import print_function, division
from diviner.metadata import get_all_df
from bokeh.plotting import *
import pandas as pd


def create_hk_temps():
    output_file('hk_temps.html', title='H/K Temperatures')

    df = get_all_df()

    t_cols = df.filter(regex='temp').columns

    dates = df[t_cols].index.to_datetime().to_series()
    for col in t_cols:
        figure(x_axis_type='datetime',
               tools='pan,wheel_zoom,box_zoom,reset,previewsave')
        line(dates, df[col], legend=col)
        curplot().title = col

    save()


def create_other_hk():
    output_file('other_hk.html', title='Other H/K')
    df = get_all_df()
    t_cols = df.filter(regex='temp').columns
    rest_cols = list(set(df.columns) - set(t_cols))
    dates = df[t_cols].index.to_datetime().to_series()
    for col in rest_cols:
        figure(x_axis_type='datetime',
               tools='pan,wheel_zoom,box_zoom,reset,previewsave')
        line(dates, df[col], legend=col)
        curplot().title = col

    save()


def create_high_res(col):
    print('creating ', col)
    output_file('high_res.html', title='Highres')
    df = pd.read_hdf('/raid1/maye/rdr_out/metadata/201209_fastread.h5', 'df')
    df = df.resample('10s')
    dates = df.index.to_datetime().to_series()
    figure(x_axis_type='datetime',
           tools='pan,wheel_zoom,box_zoom,reset,previewsave')
    line(dates, df[col])
    curplot().title = col
    save()

if __name__ == '__main__':
    create_high_res('bb_1_temp')
