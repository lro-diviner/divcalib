# -*- coding: utf-8 -*-
from matplotlib.pylab import gcf

def save_to_www(fname, **kwargs):
    gcf().savefig("/u/paige/maye/WWW/calib/"+fname,**kwargs)
    
def plot_calib_block(df,label,id,det='a6_11'):
    if not label.endswith('_block_labels'):
        label = label + '_block_labels'
    dfnow = df[df[label]==id]
    l = ['is_moving','is_spaceview','is_bbview','is_stview']
    lnew = []
    for item in l:
        dfnow2 = dfnow[dfnow[item]][det]
        if len(dfnow2) > 0:
            nitem = item.replace('is_','')
            dfnow[nitem] = dfnow2
            lnew.append(nitem)
    dfnow[lnew].plot(style='.',linewidth=2)
    title(det)

