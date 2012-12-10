from __future__ import division
from collections import OrderedDict
import pandas as pd
import numpy as np
from scipy import ndimage as nd

SV_LENGTH = 80

SV_NUM_SKIP_SAMPLE = 16
BBV_NUM_SKIP_SAMPLE = 16
SOLV_NUM_SKIP_SAMPLE = 16

class Flag(object):
    """Helper class to deal with control words or flags.

    Bit setting and checking methods are implemented.
    """
    def __init__(self, value = 0, dic = None):
        self.value = int(value)
        if dic:
            self.dic = dic
            self.set_members()
            
    def set_members(self):
        for flagname,val in self.dic.iteritems():
            # add the flagname and it's status, but cut off initial
            # qf_ from the name
            setattr(self, flagname, self.check_bit(val))
    def set_bit(self, bit):
        self.value |= bit
        self.set_members()
    def check_bit(self, bit):
        return self.value & bit != 0
    def clear_bit(self, bit):    
        self.value &= ~bit
        self.set_members()
    def __str__(self):
        # find longest key
        lwidth = 0
        for key in self.dic.keys():
            if len(key) > lwidth:
                lwidth = len(key)
        s = ''
        for key in self.dic:
            s += '{0} : {1}\n'.format(key.ljust(lwidth), 
                                     str(getattr(self,key)).rjust(6))
        return s
    def __call__(self):
        print(self.__str__())

class CalibFlag(Flag):
    flag_data=(
        #  Bit 0: Interpolation but one or more marker out of bounds
    	('interp_marker_oob', 0x00000001),
        #  Bit 1: Offsets and Gains from Nearest Marker used
    	('nearest_marker', 0x00000002),
        #  Bit 2: Same as bit 1, but nearest marker is out of bounds
    	('nearest_marker_oob', 0x00000004),
        #  Bit 3: Use constants for offsets and gains
    	('constants_only', 0x00000008),
    )
    flags = OrderedDict()
    for t in flag_data:
        flags[t[0]]=t[1]
    def __init__(self,value=0):
        super(CalibFlag,self).__init__(value,dic=self.flags)
            
class MiscFlag(Flag):
    flag_data=(
        #  Bit 0: Reserved for future use
    	('rfu0', 0x00000001),
    	('eclipse', 0x00000002),
    	('turn_on_transient', 0x00000004),  
    	('abnormal_instrument_state', 0x00000008),
    	('abnormal_instrument_temp_drift', 0x00000010),
    	('noise', 0x00000020),
    	('ch1_saturation', 0x00000040),
    	('moving', 0x00000080), 
    )
    # this convoluted way is necessary to keep the dictionary in order
    flags = OrderedDict()
    for t in flag_data:
        flags[t[0]]=t[1]
    def __init__(self,value=0):
        super(MiscFlag,self).__init__(value,dic=self.flags)

def get_cdet_frame(df,c,det):
    return df[(df.c==c) & (df.det==det)]

def get_spaceviews(df, moving=False):
    newdf = df[df.el_cmd==80]
    if not moving:
        newdf = get_non_moving_data(newdf)
    return newdf
    
def get_bbviews(df):
    return df[df.el_cmd==0]

def check_moving_flag(df):
    miscflags = MiscFlag()
    movingflag = miscflags.dic['moving']
    return df.qmi.astype(int) & movingflag !=0
    
def get_non_moving_data(df):
    """take dataframe and filter for moving flag"""
    return df[-(check_moving_flag(df))]

def label_calibdata(cdet, calibdf, label):
    calib_id = pd.Series(np.zeros_like(cdet.index), index=cdet.index)
    calib_id[calibdf.index] = 1
    cdet[label] = nd.label(calib_id)[0]


def plot_calib_data(df, c, det):
    """plot the area around calibration data in different colors"""
    cdet = get_cdet_frame(df, c, det)
    # use sclk as index
    cdet.set_index('sclk',inplace=True)
    # plot data in space orientation 
    cdet.counts[cdet.el_cmd==80].plot(style='ko')
    # plot bb counts in blue
    cdet.counts[cdet.el_cmd==0].plot(style='bx',markersize=10)
    # plot moving data in red
    return cdet.counts[check_moving_flag(cdet)].plot(style='r+',markersize=10)
    
def thermal_alternative():
    """using the offset of visual channels???"""
    pass
        
def thermal_nearest(node, tmnearest):
    """Calibrate for nearest node only.
    
    If only one calibration marker is available, no interpolation is done and 
    the gain and offset will be determined only with one measurement.
    
    Input
    =====
    node: Datanode container
    tmnearest: ThermalMarkerNode container
    """
    counts = node.counts
    offset = (tmnearest.offset_left_SV + tmnearest.offset_right_SV)/2.0
    gain = tmnearest.gain
    radiance = (counts - offset) * gain
    radiance = rconverttable.convertR(radiance, chan, det)
    tb = rbbtable.TB(radiance, chan, det)
    radiance *= config.CalRadConstant(chan)
   
def calc_gain(chan, det, thermal_marker_node):
    numerator = -1 * thermal_marker_node.calcRBB(chan,det)
    denominator = (thermal_marker_node.calc_offset_leftSV(chan, det) + 
                   thermal_marker_node.calc_offset_rightSV(chan,det)) / 2.0
    denominator -= thermal_marker_node.calc_CBB(chan, det)
    return numerator/denominator
    
