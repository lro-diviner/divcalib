from __future__ import division
from collections import OrderedDict
import pandas as pd
import numpy as np
from scipy import ndimage as nd
from scipy.interpolate import UnivariateSpline as InterpSpline
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
    s = InterpSpline(bb2temps.index.values, bb2temps.values, k=1)
    return pd.Series(s(df.index), index=df.index)

def is_moving(df):
    miscflags = MiscFlag()
    movingflag = miscflags.dic['moving']
    return df.qmi.astype(int) & movingflag !=0
        
def get_blocks(df, blocktype):
    "Allowed block-types: ['calib','sv','bb']."
        
    try:
        d = dict(list(df.groupby(blocktype + '_block_labels')))
    except KeyError:
        print("KeyError in get_blocks")
        raise KeyError
    # throw away the always existing label id 0 that is not relevant for the 
    # requested blocktype
    # Note: I cannot do list[1:] because I cannot rely on things being in sequence
    # try:
    #     del d[0]
    # except KeyError:
    #     pass
    return d
    
class Calibrator(object):
    """docstring for DivCalib"""
    time_columns = ['year','month','date','hour','minute','second']
    def __init__(self, df):
        self.df = df
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
        
    def old_setup(self, df):
        # only read required columns from big array
        self.dfsmall = df[self.time_columns + 
                          ['c','det','counts','bb_1_temp','bb_2_temp',
                           'el_cmd','az_cmd','qmi']]
                           # 'clat','clon','scalt']]
                           
        # generate time index from time-related columns
        index = fu.generate_date_index(self.dfsmall)
        
        # change index from anonymous integers to ch,det,time and assign result
        # to new dataframe
        self.df = self.dfsmall.set_index(['c','det',index])
        
        # give the index columns a name
        self.df.index.names = ['c','det','time']
        
        # having indexed by time i don't need the time data columns anymore
        self.df = self.df.drop(self.time_columns, axis=1)
        
        self.all_times = pd.Index(df.index.get_level_values(2).unique())
        
        # define science datatypes and boolean views
        define_sdtype(self.df)

    def process_calib_blocks(self):
        # create lists to save gains and offsets from the calib_blocks:
        d = {}
        # loop over calib blocks
        for blockid, block in self.calib_blocks.iteritems():
            try:
                cblock = CalibBlock(block)
            except ViewLengthError:
                # if it's the last key the data is most likely at the limit of
                # the dataset.
                # FIXME later.
                if blockid == sorted(self.calib_blocks.keys())[-1]:
                    continue
            d[blockid]=(cblock.bbview.mid_time, cblock.offset, cblock.gain)
        self.calib_data = d
        
    #def interpolate_calib_data(self):
    #    data = self.calib_data.values()
    #    times = [i[0] for i in data]
    #    offsets = [i[1] for i in data]
    #    gains = [i[2] for i in data]
        
    def interpolate_bb_temps(self):
        # just a shortcutting reference
        df = self.df
        
        # take temperature measurements of ch1/det1
        # all temps were copied for all channel/detector pairs, so they are all
        # the same for all other channel-detector pairs
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
            s = InterpSpline(ind, bbtemp, s=0.0, k=1)
            
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
        
        # as the incoming df should only be exactly one calib block I can just 
        # pick the first item in the calib_block_labels
        self.id = df.calib_block_labels[0]
        # set times for this calib block
        self.set_times()
        # to be set in process_spaceviews later, but set here so than i can catch None
        # later
        self.sv_labels = None 
        
        # Define and set spaceviews for object
        self.process_spaceviews()
        
        # check for correct length of spaceviews
        # self.check_spaceviews()
        
        if self.sv_labels:
            self.get_offset()
        
        # self.process_bbview()
        
        # self.gain = self.calc_gain()

        # # levels[2] to pick out the timestamp from hierarchical index
        # self.alltimes = pd.Index(self.df.index.get_level_values(2).unique())
        # self.start_time_moving = self.alltimes[0]
        # self.end_time_moving = self.alltimes[-1]
        
    def plot(self, **kwargs):
        pu.plot_calib_block(self.df,'calib',self.id, **kwargs)
        
    def set_times(self):
        self.start_time = self.df.index[0]
        self.end_time = self.df.index[-1]
        self.mid_time = self.start_time + (self.end_time - self.start_time)//2
        
    def process_bbview(self):
        """Process the bbview inside this CalibBlock.
        
        Defines:
        --------
        * self.bbv_label
        ** the ID of this BB view within this dataset
        * self.bbview
        ** the BBView object for this bb-view
        
        """
        bbview_group = get_blocks(self.df, 'bb')
        if len(bbview_group) == 0:
            raise NoOfViewsError('bb', '>0', 0, 'process_bbview')
        self.bbv_label = bbview_group.keys()
        self.bbview = BBView(bbview_group[self.bbv_label[0]])
        
    def process_spaceviews(self):
        """Process the spaceviews inside this CalibBlock.
        
        As this defines the left and right sv, this relies on their existence.
        Defining the spaceviews by creating:
        --------
        * self.spaceviews
        * self.sv_labels
        * self.left_sv
        * self.right_sv
        """
        # get spaceviews, has keys and df in blocks
        spaceviews = get_blocks(self.df, 'sv')
        
        if len(spaceviews) == 0:
            raise NoOfViewsError('sv', '>0', 0, 'process_spaceviews, calib block '+
                str(self.df.calib_block_labels.unique()))
        
        # get the 2 item list of spaceview labels and sort them
        self.sv_labels = sorted(spaceviews.keys())
        
        self.spaceviews = {}
        for label in self.sv_labels:
            self.spaceviews[label] = SpaceView(spaceviews[label])

    def check_spaceviews(self):
        # check for the right length of spaceview
        lenleft =  len(self.left_sv)
        lenright = len(self.right_sv)
        if any([lenleft!=c.SV_LENGTH_TOTAL, lenright!=c.SV_LENGTH_TOTAL]):
            raise ViewLengthError('space', lenleft, lenright )
        
    def get_offset(self, method='all',det='a3_11'):
        """calculate offset.
        
        TODO: Deal with solar target containers differently?
        
        Parameters
        ----------
        method: string
            Values: ['all','first','last'] to determine which sides of the 
            spaceviews are being used for the offset calculation.
            
        Returns:
        --------
        offset: pandas.Series
            data column copied attached to self
        """
        # get only the spaceviews now (excludes moving data, labels do not)
        subdf = self.df[self.df.is_spaceview]
        
        if method == 'all':
            offset = subdf[det].mean()
        elif method == 'first':
            offset = subdf[subdf.sv_block_label==self.sv_labels[0]][det].mean()
        elif method == 'last':
            offset = subdf[subdf.sv_block_label==self.sv_labels[-1]][det].mean()
        else:
            raise UnknownMethodError(method, 'CalibBlock.get_offset')
        self.offset = offset
        return offset
        
    def calc_gain(self):
        """Calc gain.
        
        This is how JPL did it:
        numerator = -1 * thermal_marker_node.calcRBB(chan,det)
        
        Then a first step for the denominator:
        denominator = (thermal_marker_node.calc_offset_leftSV(chan, det) + 
                       thermal_marker_node.calc_offset_rightSV(chan,det)) / 2.0
        
        Basically, that means: denominator = mean(loffset, roffset)
        
        For the second step of the denominator, they used calc_CBB, which is just 
        the mean of counts in BB view:
        denominator -= thermal_marker_node.calc_CBB(chan, det)
        return numerator/denominator.
        """
        numerator = -1 * self.bbview.rbb_average
        denominator = self.offset - self.bbview.average
        return numerator / denominator
                      

class View(object):
    """methods to deal with spaceviews.
    
    Each View object should offer a simple average and also a more intricate
    way to determine the count values of itself. (Like cutting of samples on the left
    or right side.)
    """
    def __init__(self, df):
        self.df = df
        self.start_time = self.df.index[0]
        self.end_time   = self.df.index[-1]
        self.mid_time =  self.start_time + (self.end_time-self.start_time)//2
        # self.average = self.counts.groupby(level=['c','det']).mean()
        
    def get_counts_mean(offset_left=0,offset_right=0):
        "Placeholder for getting counts in different ways."
        pass

    def __len__(self):
        "provide own answer to length for the safety checks in CalibBlock()"
        return len(self.counts)
    
        
class SpaceView(View):
    """docstring for SpaceView"""
    def __init__(self, df):
        super(SpaceView, self).__init__(df)
    
class BBView(View):
    """docstring for BBView"""
    def __init__(self, df):
        super(BBView, self).__init__(df)
        self.RBB = df.RBB
        # meaningfull is only the grouping on level=['c'] but we need the c,det indexing
        # anyway later so I might as well have the broadcasting here.
        self.rbb_average = self.RBB.groupby(level=['c','det']).mean()
        

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
    
