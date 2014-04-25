
from bokeh.plotting import *
from diviner.metadata import get_all_df

df = get_all_df()

t_cols = df.filter(regex='temp').columns

output_file('hk_temps.html', title='H/K Temperatures')

dates = df[t_cols].index.to_datetime().to_series()
for col in t_cols:
    print col
    figure(x_axis_type='datetime',
           tools='pan,wheel_zoom,box_zoom,reset,previewsave')
    line(dates, df[col], legend=col)
    curplot().title = col
