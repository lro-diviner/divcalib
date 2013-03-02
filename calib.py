from __future__ import division
from collections import OrderedDict
import pandas as pd
import numpy as np
from scipy import ndimage as nd
from scipy.interpolate import UnivariateSpline as Spline
import divconstants as c
from file_utils import define_sdtype
import plot_utils as pu
import file_utils as fu

class DivCalibError(Exception):
    """Base class for exceptions in this module."""
    pass
    

class ViewLengthError(DivCalibError):
    """ Exception for view length (9 ch * 21 det * 80 samples = 15120).
    
    SV_LENGTH_TOTAL defined at top of this file.
    """
    def __init__(self, view, value,value2):
        self.view = view
        self.value = value
        self.value2 = value2
    def __str__(self):
        return "Length of {0}-view not {1}. Instead: ".format(self.view,
                                        c.SV_LENGTH_TOTAL) + repr(self.value) +\
                                        repr(self.value2)


class NoOfViewsError(DivCalibError):
    def __init__(self, view, wanted, value, where):
        self.view = view
        self.wanted = wanted
        self.value = value
        self.where = where
    def __str__(self):
        return "Number of {0} views not as expected in {3}. "\
                "Wanted {1}, got {2}.".format(self.view, self.wanted, 
                                              self.value, self.where)

class UnknownMethodError(DivCalibError):
    def __init__(self, method, location):
        self.method
        self.location
    def __str__(self):
        return "Method {0} not defined here. ({1})".format(self.method,
                                                           self.location)

def get_channel_mean(df, col_str, channel):
    "The dataframe has to contain c and jdate for this to work."
    return df.groupby(['c',df.index])[col_str].mean()[channel]
    
def get_channel_std(df, col_str, channel):
    "The dataframe has to contain c and jdate for this to work."
    return df.groupby(['c',df.index])[col_str].std()[channel]


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

def plot_calib_data(df, c, det):
    """plot the area around calibration data in different colors"""
    cdet = get_cdet_frame(df, c, det)
    # # use sclk as index
    # cdet.set_index('sclk',inplace=True)
    # plot data in space orientation 
    cdet.counts[cdet.el_cmd==80].plot(style='ko')
    # plot bb counts in blue
    cdet.counts[cdet.el_cmd==0].plot(style='ro')
    # plot moving data in red
    return cdet.counts[is_moving(cdet)].plot(style='gx',markersize=15)

def get_cdet_frame(df,c,det):
    return df[(df.c==c) & (df.det==det)]

def get_calib_data(df, moving=False):
    newdf = df[df.el_cmd.isin([80,0])]
    return newdf if moving else get_non_moving_data(newdf)
        
def get_non_moving_data(df):
    """take dataframe and filter for moving flag"""
    return df[-(is_moving(df))]

def label_calibdata(df, calibdf, label):
    # get a series with the size and index of the incoming dataframe
    calib_id = pd.Series(np.zeros(len(df.index)), index=df.index)
    # set the value to 1 (or True) where the calibdf has an index
    calib_id[calibdf.index] = 1
    # label the calib_id series and add to the incoming dataframe
    df[label] = nd.label(calib_id)[0]
    
def get_offset_use_limits(grouped):
    # for now, use the end of 2nd spaceview as end of application time
    # for mean value of set of spaceviews
    return [g.index[-1] for i,g in grouped.counts if not i==0][1::2]

def add_offset_col(df, grouped):
    index = get_offset_use_limits
    data = grouped.coutns.mean()[[2,4,6,8]].values
    offsets = pd.Series(data, index=index)
    df['offsets'] = offsets.reindex_like(df, method='bfill')

def get_bb_means(grouped_bb):
    return grouped_bb.counts.mean()[1:]

def get_bb2_col(df):
    # get the bb2 temps without the nans
    bb2temps = df.bb_2_temp.dropna()
    #create interpolater function by interpolating over bb2temps.index (needs
    # to be integer!) and its values
    s = Spline(bb2temps.index.values, bb2temps.values, k=1)
    return pd.Series(s(df.index), index=df.index)

def is_moving(df):
    miscflags = MiscFlag()
    movingflag = miscflags.dic['moving']
    return df.qmi.astype(int) & movingflag !=0
        
def get_blocks(df, blocktype, del_zero=True):
    "Allowed block-types: ['calib','sv','bb']."
        
    try:
        d = dict(list(df.groupby(blocktype + '_block_labels')))
    except KeyError:
        print("KeyError in get_blocks")
        raise KeyError
    # throw away the always existing label id 0 that is not relevant for the 
    # requested blocktype
    if del_zero:
        try:
            del d[0]
        except KeyError:
            pass
    return d
    
def get_mean_time(df):
    t1 = df.index[0]
    t2 = df.index[-1]
    t = t1 + (t2 - t1) // 2
    return t

def get_offsets_at_all_times(data, offsets):
    real_time = np.array(data.index.values.view("i8") / 1000, dtype="datetime64[us]")
    cali_time = np.array(offsets.index.values.view("i8") / 1000, dtype="datetime64[us]")
    
    right_index = cali_time.searchsorted(real_time, side="left")
    left_index = np.clip(right_index - 1, 0, len(offsets)-1)
    right_index = np.clip(right_index, 0, len(offsets)-1)
    left_time = cali_time[left_index]
    right_time = cali_time[right_index]
    left_diff = np.abs(left_time - real_time)
    right_diff = np.abs(right_time - real_time)
    caldata2 = offsets.ix[np.where(left_diff < right_diff, left_time, right_time)]
    return caldata2

def get_data_columns(df):
    "Filtering for the div247 channel names"
    return df.filter(regex='[ab][0-9]_[0-2][0-9]')
    
def interpolate_data_column(col):
    all_times = col.index
    x = offsets.index.values.astype('float64')
    s = Spline(x, )
    
class Calibrator(object):
    """currently set up to work with a 'wide' dataframe.
    
    Meaning, all detectors have their own column.
    """
    def __init__(self, df):
        self.df = df
        
        self.get_offsets()
        self.interpolate_offsets()
        self.apply_offsets()
        
        # loading conversion table indexed in T*100 (for resolution)
        self.t2nrad = pd.load('data/Ttimes100_to_Radiance.df')
        
        # interpolate the bb1 and bb2 temperatures for all times
        self.interpolate_bb_temps()
        
        # get the normalized radiance for the interpolated bb temps
        #self.get_RBB()
        
        ## drop these columns as they are not required anymore (i think)
        #self.df = self.df.drop(['bb_1_temp','bb_2_temp','el_cmd','az_cmd','qmi'],axis=1)
        
        # sort the first level of index (channels) for indexing efficiency
        #self.df.sortlevel(0, inplace=True)
        
        # get the calib blocks
        #self.calib_blocks = get_blocks(self.df, 'calib')
                   
        #self.process_calib_blocks()
        
        
    def get_offsets(self):
        # get spaceviews here to kick out moving data
        spaceviews = self.df[self.df.is_spaceview]
        # group by the calibration block labels
        grouped = spaceviews.groupby(spaceviews.calib_block_labels)
        # get the mean times for each calib block
        times = grouped.a3_11.apply(get_mean_time)
        ###
        # change here for method of means!!
        ###
        offsets = grouped.mean()
        # set the times as index for this dataframe of offsets
        offsets.index = times
        self.offsets = get_data_columns(offsets)
        return self.offsets
        
    def interpolate_offsets(self):
        sdata = self.df[self.df.sdtype == 0]
        sdata = get_data_columns(sdata)
        all_times = sdata.index.values.astype('float64')
        x = self.offsets.index.values.astype('float64')
        
        offsets_interpolated = pd.DataFrame(index=sdata.index)
        for col in self.offsets:
            # change k for the kind of fit you want
            s = Spline(x, self.offsets[col], s=0.0, k=1)
            col_offset = s(all_times)
            offsets_interpolated[col] = col_offset
        self.sdata = sdata
        self.offsets_interpolated = offsets_interpolated
        return offsets_interpolated
        
    def apply_offsets(self):
        self.sdata = self.sdata - self.offsets_interpolated
        return self.sdata
        
    def interpolate_bb_temps(self):
        # just a shortcutting reference
        df = self.df
        
        # bb_1_temp is much more often sampled than bb_2_temp
        bb1temps = df.bb_1_temp.dropna()
        bb2temps = df.bb_2_temp.dropna()

        # accessing the multi-index like this provides the unique index set
        # at that level, in this case the dataframe timestamps
        all_times = pd.Index(df.index.get_level_values(2).unique())

        # loop over both temperature arrays, to adhere to DRY principle
        # the number of data points in bb1temps are much higher, but most
        # consistently we should interpolate both the same way.
        for bbtemp in [bb1temps,bb2temps]:
            # converting the time series to floats for interpolation
            ind = bbtemp.index.values.astype('float64')
            
            # I found the best parameters by trial and error, as to what looked
            # like a best compromise between smoothing and overfitting
            # note_2: decided to go back to k=1,s=0 (from s=0.05) review later?
            s = Spline(ind, bbtemp, s=0.0, k=1)
            
            # interpolate all_times to this function 
            newtemps = s(all_times.values.astype('float64'))
            
            # create a new pd.Series to be incorporated into the dataframe
            newseries = pd.Series(newtemps, index=all_times)
            
            # reindex the time indexed series to have c,det,time multi-index
            # the level index is the number of the index in the multi-index that
            # is already covered by the index of newseries
            df[bbtemp.name + '_interp'] = newseries.reindex(df.index, level=2)
                                     
    def get_RBB(self):
        # add the RBB column to be filled in pieces later
        self.df['RBB'] = 0.0
        
        # getting the interpolated bb temperatures. as before, they are all the same
        # for the other channel/detector pairs
        bb1temp = self.df.bb_1_temp_interp
        bb2temp = self.df.bb_2_temp_interp
        
        # create mapping to look up the right temperature for different channels
        mapping = {3: bb1temp, 4: bb1temp, 5: bb1temp, 6: bb1temp,
                   7: bb2temp, 8: bb2temp, 9: bb2temp}
        
        # loop over thermal channels 3..9           
        for ch in range(3,10):
            #link to the correct bb temps
            bbtemps = mapping[ch]
            
            # rounding to 2 digits and * 100 to lookup the values that have been 
            # indexed by T*100 (to enable float value table lookup)
            bbtemps = (bbtemps.round(2)*100).astype('int')
            
            #look up the radiances for this channel
            RBBs = self.t2nrad.ix[bbtemps, ch]
            # RBBs has still the T*100 as index, set them to the timestamps of 
            # the bb temperatures
            RBBs.index = bbtemps.index
            
            # pick the target area inside the RBB column for this channel
            # this provides a view (= reference) inside the dataframe
            target = self.df.RBB.ix[ch]
            
            # reindex the RBBs time index to include the detectors
            # the target index is ('det','time') therefore the level that is already
            # covered by RBBs is level 1
            RBBs = RBBs.reindex(target.index,level=1)
            
            # store them in the dataframe at the target position (which is a
            # view(=reference))
            self.df.RBB.ix[ch] = RBBs
        


        
    #def plot(self, **kwargs):
    #    pu.plot_calib_block(self.df,'calib',self.id, **kwargs)
    #    
    #def get_times(self):
    #    self.start_time = self.df.index[0]
    #    self.end_time = self.df.index[-1]
    #    self.mid_time = self.start_time + (self.end_time - self.start_time)//2
    #    
    #def process_bbview(self):
    #    """Process the bbview inside this CalibBlock.
    #    
    #    Defines:
    #    --------
    #    * self.bbv_label
    #    ** the ID of this BB view within this dataset
    #    * self.bbview
    #    ** the BBView object for this bb-view
    #    
    #    """
    #    bbview_group = get_blocks(self.df, 'bb')
    #    if len(bbview_group) == 0:
    #        raise NoOfViewsError('bb', '>0', 0, 'process_bbview')
    #    self.bbv_label = bbview_group.keys()
    #    self.bbview = BBView(bbview_group[self.bbv_label[0]])
    #    
    #            
    #def calc_gain(self):
    #    """Calc gain.
    #    
    #    This is how JPL did it:
    #    numerator = -1 * thermal_marker_node.calcRBB(chan,det)
    #    
    #    Then a first step for the denominator:
    #    denominator = (thermal_marker_node.calc_offset_leftSV(chan, det) + 
    #                   thermal_marker_node.calc_offset_rightSV(chan,det)) / 2.0
    #    
    #    Basically, that means: denominator = mean(loffset, roffset)
    #    
    #    For the second step of the denominator, they used calc_CBB, which is just 
    #    the mean of counts in BB view:
    #    denominator -= thermal_marker_node.calc_CBB(chan, det)
    #    return numerator/denominator.
    #    """
    #    numerator = -1 * self.bbview.rbb_average
    #    denominator = self.offset - self.bbview.average
    #    return numerator / denominator
                      

    
        # meaningfull is only the grouping on level=['c'] but we need the c,det indexing
        # anyway later so I might as well have the broadcasting here.
        #self.rbb_average = self.RBB.groupby(level=['c','det']).mean()
        

#def thermal_alternative():
#    """using the offset of visual channels???"""
#    pass
#        
#def thermal_nearest(node, tmnearest):
#    """Calibrate for nearest node only.
#    
#    If only one calibration marker is available, no interpolation is done and 
#    the gain and offset will be determined only with one measurement.
#    
#    Input
#    =====
#    node: Datanode container
#    tmnearest: ThermalMarkerNode container
#    """
#    counts = node.counts
#    offset = (tmnearest.offset_left_SV + tmnearest.offset_right_SV)/2.0
#    gain = tmnearest.gain
#    radiance = (counts - offset) * gain
   # radiance = rconverttable.convertR(radiance, chan, det)
   # tb = rbbtable.TB(radiance, chan, det)
   # radiance *= config.CalRadConstant(chan)
   #
    
