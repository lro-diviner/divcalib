from __future__ import division
from collections import OrderedDict
import pandas as pd
import numpy as np
from scipy import ndimage as nd
from scipy.interpolate import UnivariateSpline as InterpSpline
import diviner as div

# define the default number of points that each view should have
SV_LENGTH = STV_LENGTH = BBV_LENGTH = 80

# define pointing boundaries for the spaceview (for offset calibration)
SV_AZ_MIN = 150.0
SV_AZ_MAX = 270.0
SV_EL_MIN = 45.0
SV_EL_MAX = 100.0

# define pointing boundaries for the blackbody view (for gain calibration)
BB_AZ_MIN = BB_EL_MIN = 0.0
BB_AZ_MAX = 270.0
BB_EL_MAX = 3.0

# define pointing boundaries for the solar target view (for visual channel calibration)
ST_AZ_MIN = 10.0
ST_AZ_MAX = 270.0
ST_EL_MIN = 35.00
ST_EL_MAX = 45.00

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
    """This needs the index to be integer, time indices are not supported by nd.label"""
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
    df['offsets'] = offsets.reindex_like(cdet, method='bfill')

def get_bb_means(grouped_bb):
    return grouped_bb.counts.mean()[1:]

def get_bb2_col(df):
    # get the bb2 temps without the nans
    bb2temps = df.bb_2_temp.dropna()
    #create interpolater function by interpolating over bb2temps.index (needs
    # to be integer!) and its values
    s = InterpSpline(bb2temps.index.values, bb2temps.values, k=1)
    return pd.Series(s(df.index), index=df.index)

def is_moving(df):
    miscflags = MiscFlag()
    movingflag = miscflags.dic['moving']
    return df.qmi.astype(int) & movingflag !=0
    
def define_sdtype(df):
    
    sv_selector = (df.az_cmd >= SV_AZ_MIN) & (df.az_cmd <= SV_AZ_MAX) & \
                  (df.el_cmd >= SV_EL_MIN) & (df.el_cmd <= SV_EL_MAX)
    bb_selector = (df.az_cmd >= BB_AZ_MIN) & (df.az_cmd <= BB_AZ_MAX) & \
                  (df.el_cmd >= BB_EL_MIN) & (df.el_cmd <= BB_EL_MAX)
    st_selector = (df.az_cmd >= ST_AZ_MIN) & (df.az_cmd <= ST_AZ_MAX) & \
                  (df.el_cmd >= ST_EL_MIN) & (df.el_cmd <= ST_EL_MAX)
    df['sdtype'] = 0
    df.sdtype[sv_selector] = 1
    df.sdtype[bb_selector] = 2
    df.sdtype[st_selector] = 3
    
    # the following defines the sequential list of calibration blocks inside
    # the dataframe. nd.label provides an ID for each sequential part where
    # the given condition is true.
    # this still includes the moving areas, because i want the sv and bbv
    # attached to each other to deal with them later as a separate calibration
    # block
    df['calib_block_labels'] = nd.label( (df.sdtype==2) | (df.sdtype==1) )[0]
    
    # this resets data from sdtypes >0 above that is still 'moving' to be 
    # sdtype=-1 (i.e. 'moving', defined by me)
    df.sdtype[is_moving(df)] = -1
    
    # now I don't need to check for moving anymore, the sdtypes are clean
    df['is_spaceview'] = (df.sdtype == 1)
    df['is_bbview']    = (df.sdtype == 2)
    df['is_stview']    = (df.sdtype == 3)
    df['is_moving']    = (df.sdtype == -1)
    df['is_calib'] = df.is_spaceview | df.is_bbview | df.is_stview

    # this does the same as above labeling, albeit here the blocks are numbered
    # individually. Not sure I will need it but might come in handy.
    df['sv_block_labels'] = nd.label(df.is_spaceview)[0]
    df['bb_block_labels'] = nd.label(df.is_bbview)[0]
    
def get_blocks(df, blocktype):
    "Allowed block-types: ['calib','sv','bb']."
        
    d = dict(list(df.groupby(blocktype + '_block_labels')))
        
    # throw away the always existing label id 0 that is not relevant for the 
    # requested blocktype
    # Note: I cannot do list[1:] because I cannot rely on things being in sequence
    del d[0]
    return d
    
class DivCalib(object):
    """docstring for DivCalib"""
    time_columns = ['year','month','date','hour','minute','second']
    def __init__(self, df):
        # only read required columns from big array
        self.dfsmall = df[self.time_columns + 
                          ['c','det','counts','bb_1_temp','bb_2_temp',
                           'el_cmd','az_cmd','qmi']]
                           # 'clat','clon','scalt']]
                           
        # generate time index from time-related columns
        index = div.generate_date_index(self.dfsmall)
        
        # change index from anonymous integers to ch,det,time and assign result
        # to new dataframe
        self.df = self.dfsmall.set_index(['c','det',index])
        
        # give the index columns a name
        self.df.index.names = ['c','det','time']
        
        # having indexed by time i don't need the time data columns anymore
        self.df = self.df.drop(self.time_columns, axis=1)
        
        # loading conversion table indexed in T*100 (for resolution)
        self.t2nrad = pd.load('Ttimes100_to_Radiance.df')
        
        # interpolate the bb1 and bb2 temperatures for all times
        self.interpolate_bb_temps()
        
        # get the normalized radiance for the interpolated bb temps
        self.get_nrad()
        
        # define science datatypes and boolean views
        define_sdtype(self.df)
        
        # drop these columns as they are not required anymore (i think)
        self.df.drop(['bb_1_temp','bb_2_temp','el_cmd','az_cmd','qmi'],axis=1)
        
        # sort the first level of index (channels) for indexing efficiency
        self.df.sortlevel(0, inplace=True)
        
        # get the calib blocks
        self.calib_blocks = get_blocks(self.df, 'calib')
                   
    def process_calib_blocks(self):
        # loop over calib blocks (id 0 is not calib_data, therefore exclude
        # in the loop
        for blockid, block in self.calib_blocks.items()[1:]:
            cblock = CalibBlock(block)
            
    def interpolate_bb_temps(self):
        # just a shortcutting reference
        df = self.df
        
        # take temperature measurements of ch1/det1
        # all temps were copied for all channel/detector pairs, so they are all
        # the same for all other channel-detector pairs
        bb1temps = df.ix[1].ix[1].bb_1_temp.dropna()
        bb2temps = df.ix[1].ix[1].bb_2_temp.dropna()

        # accessing the multi-index like this provides the unique index set
        # at that level, in this case the dataframe timestamps
        all_times = df.index.levels[2]

        # loop over both temperature arrays, to adhere to DRY principle
        # the number of data points in bb1temps are much higher, but most
        # consistently we should interpolate both the same way.
        for bbtemp in [bb1temps,bb2temps]:
            # converting the time series to floats for interpolation
            ind = bbtemp.index.values.astype('float64')
            
            # I found the best parameters by trial and error, as to what looked
            # like a best compromise between smoothing and overfitting
            s = InterpSpline(ind, bbtemp, s=0.05, k=3)
            
            # interpolate all_times to this function 
            newtemps = s(all_times.values.astype('float64'))
            
            # create a new pd.Series to be incorporated into the dataframe
            newseries = pd.Series(newtemps, index=all_times)
            
            # reindex the time indexed series to have c,det,time multi-index
            # the level index is the number of the index in the multi-index that
            # is already covered by the index of newseries
            df[bbtemp.name + '_interp'] = newseries.reindex(df.index, level=2)
                                     
    def get_nrad(self):
        # add the nrad column to be filled in pieces later
        self.df['nrad'] = 0.0
        
        # getting the interpolated bb temperatures. as before, they are all the same
        # for the other channel/detector pairs
        bb1temp = self.df.ix[1].ix[1].bb_1_temp_interp
        bb2temp = self.df.ix[1].ix[1].bb_2_temp_interp
        
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
            nrads = self.t2nrad.ix[bbtemps, ch]
            # nrads has still the T*100 as index, set them to the timestamps of 
            # the bb temperatures
            nrads.index = bbtemps.index
            
            # pick the target area inside the nrad column for this channel
            # this provides a view (= reference) inside the dataframe
            target = self.df.nrad.ix[ch]
            
            # reindex the nrads time index to include the detectors
            # the target index is ('det','time') therefore the level that is already
            # covered by nrads is level 1
            nrads = nrads.reindex(target.index,level=1)
            
            # store them in the dataframe at the target position (which is a
            # view(=reference))
            target = nrads
        
        



class DivCalibError(Exception):
    """Base class for exceptions in this module."""
    pass
    
class ViewLengthError(DivCalibError):
    """ Exception for view length (9 ch * 21 det * 80 samples = 15120).
    """
    def __init__(self, view, value):
        self.view = view
        self.value = value
    def __str__(self):
        return "Length of {0}-view not 15120. Instead: ".format(self.view) \
                + repr(self.value)

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

class CalibBlock(object):
    """The CalibBlock is purely defined by azimuth and elevation commands.
    
    Therefore it contains moving data that needs to be ignored. The advantage is
    that the spaceviews and bb view form a glued unit that can be found easily.
    
    >>> cb = CalibBlock(df)
    >>> cb.start_time
    <timestamp>
    >>> cb.end_time
    <timestamp>
    >>> cb.mean_time
    <timestamp>
    >>> cb.offset
    <value>
    """
    def __init__(self, df):
        self.df = df
        self.set_spaceviews()
        
        # levels[2] to pick out the timestamp from hierarchical index
        self.alltimes = self.df.index.levels[2]
        self.start_time_moving = self.alltimes[0]
        self.end_time_moving = self.alltimes[-1]
        self.static_df = get_non_moving_data(df)
        self.static_times = self.static_df.index.levels[2]
        self.static_start = self.static_times[0]
        self.static_end = self.static_times[-1]
        self.get_offset()
    def set_spaceviews(self):
        # get spaceviews
        self.spaceviews = get_blocks(self.df, 'sv')
        
        # I'm expecting 2 spaceviews, left and right, raise error if it's not
        if len(self.spaceviews) != 2:
            raise NoOfViewsError('space', 2, len(self.spaceviews),
                                 "CalibBlock constructor")
        
        # get the 2 item list of spaceview labels and sort them
        self.sv_labels = sorted(self.spaceviews.keys())
        
        # define the lower label id as the left spaceview
        self.left_sv  = SpaceView(self.spaceviews[self.sv_labels[0]])
        # and the other as the right spaceview
        self.right_sv = SpaceView(self.spaceviews[self.sv_labels[1]])

        # check for the right length of spaceview
        lenleft =  len(self.left_sv)
        lenright = len(self.right_sv)
        if lenleft  != 15120:
            raise ViewLengthError('space', lenleft )
        if lenright != 15120:
            raise ViewLengthError('space', lenright )
        
    def get_offset(self):
        pass


class SpaceView(object):
    """methods to deal with spaceviews"""
    def __init__(self, df):
        self.df = df
        self.start_time = self.df.index[0][2]
        self.end_time   = self.df.index[-1][2]
    def get_counts_mean(offset_left=0,offset_right=0):
        return df.counts
    def __len__(self):
        return len(self.df)

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
                   # calc_CBB is just the mean of counts in BB view
    denominator -= thermal_marker_node.calc_CBB(chan, det)
    return numerator/denominator
    
