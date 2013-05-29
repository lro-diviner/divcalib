from __future__ import division
from collections import OrderedDict
import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline as Spline
import divconstants as c
from plot_utils import ProgressBar
import logging

logging.basicConfig(filename='calib.log', level=logging.INFO)

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
        return "Length of {0}-view not {1}."\
                " Instead: ".format(self.view,
                                    c.SV_LENGTH_TOTAL) + repr(self.value) + repr(self.value2)


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


def get_calib_block(df, blocktype, del_zero=True):
    "Allowed block-types: ['calib','sv','bb','st']."
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

def get_mean_time(df_in, skipsamples=0):
    df = df_in[skipsamples:]
    try:
        t1 = df.index[0]
        t2 = df.index[-1]
    except IndexError:
        print "Problem with calculating mean time."
        logging.warning('Index not found in get_mean_time. Length of df: {0}'.format(
                        len(df.index)
        ))
        return np.nan
    t = t1 + (t2 - t1) // 2
    return t

def calc_offsets_at_all_times(data, offsets):
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

def get_data_columns(df,strict=True):
    "Filtering for the div247 channel names"
    if strict:
        pattern = '^[ab][0-9]_[0-2][0-9]'
    else:
        pattern = '[ab][0-9]_[0-2][0-9]'
    return df.filter(regex=pattern)

def get_thermal_detectors(df):
    t1 = df.filter(regex='a[3-6]_[0-2][0-9]')
    t2 = df.filter(regex='b[1-3]_[0-2][0-9]')
    return pd.concat([t1,t2],axis=1)

class RBBTable(object):
    """Table class to convert between temperatures and radiances."""
    def __init__(self):
        super(RBBTable, self).__init__()
        self.df = pd.load('../data/T_to_Normalized_Radiance.df')
        self.table_temps = self.df.index.values.astype('float')
        self.t2rad = {}
        self.rad2t = {}
        sliced = self.df.ix[abs(self.df.index)> 2]
        for ch in range(3,10):
            self.t2rad[ch] = Spline(self.table_temps, self.df[ch],
                                    s=0.0, k=1)
            if ch < 6:
                data = sliced[ch]
                temps = sliced.index.values.astype('float')
            else:
                data = self.df[ch]
                temps = self.table_temps
            self.rad2t[ch] = Spline(data, temps, s=0.0, k=1)
    
    def get_radiance(self, temps, ch):
        return self.t2rad[ch](temps)
    def get_tb(self, rads, ch):
        return self.rad2t[ch](rads)

class CalBlock(object):
    """Class to handle different options on how to deal with a single cal block.
    
    IN:
        dataframe, containing all meta-data like label numbers, H/K etc.
    OUT:
        via several class methods
    """
    def __init__(self, df, skip_samples=0):
        self.df = df
        self.skip_samples = skip_samples
        self.sv_labels = self.get_unique_labels('sv')
        self.bb_labels = self.get_unique_labels('bb')
        self.st_labels = self.get_unique_labels('st')
        self.define_kind()
        self.calculate_offsets()

    @property
    def mean_time(self):
        """Use module function to calculate the mean value of the center data.
        
        The center_data dataframe is determined from the kind of this calibblock.
        For an ST block, it's the stview data, BB -> is_bbview respectively.
        """
        return get_mean_time(self.center_data, self.skip_samples)
        
    def calculate_offsets(self):
        """Determine offsets for each available spacelook.
        
        At initialisation, the object receives the number of samples to skip.
        This number is used here for the offset calculation
        """
        offsetdata = get_data_columns(self.df[self.df.is_spaceview])
        grouped = offsetdata.groupby(self.df.sv_block_labels)
        self.offsets = grouped.agg(lambda x: x[self.skip_samples:].mean())
        self.offset_stds = grouped.agg(lambda x: x[self.skip_samples:].std())
        
    def get_offsets(self, kind='both'):
        """Provide offsets for method as required.
        IN:
            offset_kind. If set to 'both', both sides will be used to determine
                the offset, 'left' and 'right' do the alternative, respectively.
        """

    def define_kind(self):
        """Define kind of calblock depending on containing bbview, st or both.

        Possible kinds: 'BB', 'ST', 'BOTH'
        """
        # more than 1 kind?
        if (self.st_labels.size + self.bb_labels.size) > 1:
            self.kind = 'BOTH'
            # for the lack of a better definition, if this calib block both
            # contains ST and BB data, I take both as 'center_data'
            self.center_data = self.df[(self.df.is_stview) | (self.df.is_bbview)]
        elif self.st_labels.size > 0:
            self.kind = 'ST'
            self.center_data = self.df[self.df.is_stview]
        else:
            self.kind = 'BB'
            self.center_data = self.df[self.df.is_bbview]
        
    def get_unique_labels(self,view):
        labels = self.df[view + '_block_labels'].unique()
        return np.sort(labels[labels > 0])
 
        
class View(object):
    def __init__(self, df, type, skip_samples=0):
        self.df = df[df['is_'+type+'view']]
        self.skip_samples=skip_samples
    
    def mean(self):
        return self.df[self.skip_samples:].mean()
        

class SpaceView(View):
    """docstring for SpaceView"""
    def __init__(self, df, skip_samples=0):
        super(SpaceView, self).__init__(df, 'space', skip_samples)


class BBView(View):
    """docstring for BBView"""
    def __init__(self, df, skip_samples=0):
        super(BBView, self).__init__(df, 'bb', skip_samples)


class STView(View):
    """docstring for STView"""
    def __init__(self, df, skip_samples=0):
        super(STView, self).__init__(df, 'st', skip_samples)

                            
class Calibrator(object):
    """currently set up to work with a 'wide' dataframe.
    
    Meaning, all detectors have their own column.
    """
    # map between div247 channel names and diviner channel ids
    mcs_div_mapping = {'a1': 1, 'a2': 2, 'a3': 3, 
                       'a4': 4, 'a5': 5, 'a6': 6, 
                       'b1': 7, 'b2': 8, 'b3': 9}
                           
    channels = ['a1','a2','a3','a4','a5','a6','b1','b2','b3']
    thermal_channels = channels[2:]
    
    def __init__(self, df, do_bbtimes=True, pad_bbtemps=False, 
                           single_rbb=True, skipsamples=True,
                           calfitting_order=1):
        self.df = df
        # to control if mean bbview times or mean calib_block_times determine the
        # time of a calibration point
        self.do_bbtimes = do_bbtimes
        # to control if bbtemps are interpolated or just forward-filled (=padded)
        self.pad_bbtemps = pad_bbtemps
        # to control if RBB are just determined for 1 mean bb temp or for all bbtemps
        # of a bbview
        self.single_rbb = single_rbb
        # to control if some of the first samples of views are being skipped
        self.skipsamples = skipsamples
        if skipsamples == True:
            self.BBV_NUM_SKIP_SAMPLE = c.BBV_NUM_SKIP_SAMPLE
            self.SV_NUM_SKIP_SAMPLE = c.SV_NUM_SKIP_SAMPLE
            self.STV_NUM_SKIP_SAMPLE = c.STV_NUM_SKIP_SAMPLE
        else:
            self.BBV_NUM_SKIP_SAMPLE = 0
            self.SV_NUM_SKIP_SAMPLE = 0
            self.STV_NUM_SKIP_SAMPLE = 0
        
        # degree of order for the fitting of calibration data
        self.calfitting_order = calfitting_order
        
        # temperature - radiance converter table
        self.rbbtable = RBBTable()
        
        # loading converter factors norm-to-abs-radiances
        self.norm_to_abs_converter = pd.load('../data/Normalized_to_Absolute_Radiance.df')
        # rename column names to match channel names here
        self.norm_to_abs_converter.columns = self.channels[2:]
    
    def calibrate(self):
        
        #####
        ### BB TEMPERATURES
        #####
        # interpolate the bb1 and bb2 temperatures for all times
        # or pad if to recreate JPL calibration
        if self.pad_bbtemps:
            ### WARNING!
            ## This can cut off a calib point and make the offset times unfit the calib
            ## mean times.
            ### WARNING!
            self.pad_bb_temps()
        else:
            self.interpolate_bb_temps()
        
        #####
        ### CALIBRATION BLOCK TIME STAMPS
        #####
        # determine calibration block mean time stamps
        self.calc_calib_mean_times()
        
        #####
        ### RADIANCES FROM TABLE
        #####
        if self.single_rbb:
            self.calc_one_RBB()
        else:
            # get the normalized radiance for the interpolated bb temps (so all over df)
            self.get_RBB()
            self.calc_many_RBB()
        
        #####
        ### OFFSETS
        #####
        # determine the offsets per calib_block
        self.calc_offsets()
        
        #####
        ### BB COUNTS
        #####
        # determine bb counts (=calcCBB) per calib_block
        self.calc_CBB()
        
        #####
        ### GAIN
        ###
        self.calc_gain()
        
        #####
        ### INTERPOLATION OF CALIB DATA
        #####
        # interpolate offsets (and gains?) over the big dataframe block
        self.interpolate_caldata()
        
        #####
        ### CALCULATE RADIANCES
        #####
        # Apply the interpolated values to create science data (T_b, radiances)
        self.calc_radiances()
        
        #####
        ### CALCULATE T_B
        #####
        # calculate brightness temperatures Tb
        self.calc_tb()
    
    def pad_bb_temps(self):
        """ Forward pad bb temps to recreate JPL's calibration. """
        df = self.df
        bbtemps = ['bb_1_temp','bb_2_temp']
        
        # first i forward pad from first filled value.
        for bbtemp in bbtemps:
            df[bbtemp+'_interp'] = df[bbtemp].replace(np.nan)
        
        # now find which is the first filled value and cut off dataframe, to be
        # exactly doing what JPL is doing
        iBB1 = df[df['bb_1_temp_interp'].notnull()].index[0]
        iBB2 = df[df['bb_2_temp_interp'].notnull()].index[0]
        cutoff = max(iBB1, iBB2)
        self.df = self.df.ix[cutoff:]
    
    def interpolate_bb_temps(self):
        """Interpolating the BB H/K temperatures all over the dataframe.
        
        This is necessary, as the frequency of the measurements is too low to have
        meaningful mean values during the BB-views. Also, bb_2_temps are measured so
        rarely that there might not be at all a measurement during a bb-view.
        """
        # just a shortcutting reference
        df = self.df
        
        # bb_1_temp is much more often sampled than bb_2_temp
        bb1temps = df.bb_1_temp.dropna()
        bb2temps = df.bb_2_temp.dropna()
        
        # accessing the multi-index like this provides the unique index set
        # at that level, in this case the dataframe timestamps
        all_times = df.index.values.astype('float64')
        
        # loop over both temperature arrays [DRY !]
        # the number of data points in bb1temps are much higher, but for
        # consistency we should interpolate both the same way.
        for bbtemp in [bb1temps,bb2temps]:
            # converting the time series to floats for interpolation
            ind = bbtemp.index.values.astype('float64')
            
            # I found the best parameters by trial and error, as to what looked
            # like a best compromise between smoothing and overfitting
            # note_2: decided to go back to k=1,s=0 (from s=0.05) review later?
            # k=1 basically is a linear interpolation between 2 points
            # k=2 quadratic, k=3 cubic, k=4 is maximum possible (but no sense)
            
            # create interpolator function
            temp_interpolator = Spline(ind, bbtemp, s=0.0, k=1)
            
            # get new temperatures at all_times
            df[bbtemp.name + '_interp'] = temp_interpolator(all_times)
    
    def calc_calib_mean_times(self):

        # if we use bb views to define the time of a calib block (a la JPL)
        if self.do_bbtimes:
            # filter for bbview data (leaves out stviews !!!)
            bbvdata = self.df[self.df.is_bbview]
            alldata = self.df[self.df.is_bbview | self.df.is_stview]
            to_skip = self.BBV_NUM_SKIP_SAMPLE
        else:
            # use the whole calib block to define time of it.
            # Advantage: spaceviews without bbviews still get their time marker
            calibdata = self.df[self.df.is_calib]
            to_skip = 0
        # each sv, bb, sv block or sv,st,sv(,bb,sv) block has one calib_block label
        # therefore grouping by it enables to determine a calib marker time
        grouped = bbvdata.groupby('calib_block_labels')
        bbtimes = grouped.apply(get_mean_time, to_skip)
        
        grouped = alldata.groupby('calib_block_labels')
        allcaltimes = grouped.apply(get_mean_time, to_skip)
        self.calib_times = allcaltimes
        self.bbcal_times = bbtimes
    
    def skipped_mean(self, df, num_to_skip):
        return df[num_to_skip:].mean()
    
    def calc_offsets(self):
        
        ##
        ### currently stviews are included here, but in calc_calib_mean_times not!!
        ##
        
        # get spaceviews here to kick out moving data
        spaceviews = self.df[self.df.is_spaceview]
        
        # only work with the real data, filter out meta-data
        spaceviews = get_data_columns(spaceviews, strict=True)
        
        # group by the calibration block labels
        grouped = spaceviews.groupby(self.df.calib_block_labels)
        
        ###
        # change here for method of means!!
        # the current method aggregates just 1 value for the whole calibration block
        ###
        offsets = grouped.agg(self.skipped_mean, self.SV_NUM_SKIP_SAMPLE)
        
        # # set the times as index for this dataframe of offsets
        offsets.index = self.calib_times
        
        self.offsets = offsets
    
    def calc_CBB(self):
        # kick out moving data and get only bbviews
        bbviews = self.df[self.df.is_bbview]
        
        # get only the science data columns
        bbviews_counts = get_data_columns(bbviews)
        
        # group by calibration block label
        # does bbview ever happen more than once in one calib
        # block?
        grouped = bbviews_counts.groupby(self.df.calib_block_labels)
        
        ###
        # change here for the aggregation method
        ###
        bbcounts = grouped.agg(self.skipped_mean, self.BBV_NUM_SKIP_SAMPLE)
        
        # set the times as index for this dataframe of bbcounts
        bbcounts.index = self.bbcal_times
        
        self.CBB = bbcounts
    
    def get_RBB(self):
        """Strictly speaking only required for the calib_block gain calculation.
        
        But because this is using all interpolated BB temperatures, this effectively
        creates RBBs for the whole dataframe.
        """
        # create mapping to look up the right temperature for different channels
        mapping = {'a': self.df['bb_1_temp_interp'],
                   'b': self.df['bb_2_temp_interp']}
        
        self.RBBs = pd.DataFrame(index=self.df.index)
        
        # loop over thermal channels 3..9
        for channel in self.thermal_channels:
            #link to the correct bb temps by checking first letter of channel
            bbtemps = mapping[channel[0]]
            
            #look up the radiances for this channel
            RBBs = self.rbbtable.get_radiance(bbtemps, self.mcs_div_mapping[channel])
            for i in range(1,22):
                self.RBBs[channel+'_'+str(i).zfill(2)] = \
                    pd.Series(RBBs,index=self.df.index)
    
    def calc_one_RBB(self):
        """Calculate like JPL only one RBB value for a mean BB temperature. """
        # procedure same as calib_cbb
        bbviews = self.df[self.df.is_bbview]
        bbviews_temps = bbviews[['bb_1_temp_interp','bb_2_temp_interp']]
        grouped = bbviews_temps.groupby(self.df.calib_block_labels)
        bbtemps = grouped.agg(self.skipped_mean, c.BBV_NUM_SKIP_SAMPLE)
        bbtemps.index = self.calib_times
        self.bbtemps = bbtemps
        
        # create mapping to look up the right temperature for different channels
        mapping = {'a':bbtemps['bb_1_temp_interp'] ,
                   'b':bbtemps['bb_1_temp_interp']}
        
        self.RBB = pd.DataFrame(index=self.calib_times)
        
        for channel in self.thermal_channels:
            temps = mapping[channel[0]]
            RBBs = self.rbbtable.get_radiance(temps, self.mcs_div_mapping[channel])
            # RBBs.index = temps.index
            for i in range(1,22):
                self.RBB[channel+'_'+str(i).zfill(2)] = \
                    pd.Series(RBBs,index=self.calib_times)
    
    def calc_many_RBB(self):
        bbview_rbbs = self.RBBs[self.df.is_bbview]
        grouped = bbview_rbbs.groupby(self.df.calib_block_labels)
        if self.skipsamples:
            calib_RBBs = grouped.agg(self.skipped_mean, c.BBV_NUM_SKIP_SAMPLE)
        else:
            calib_RBBs = grouped.mean()
        calib_RBBs.index = self.bbcal_times
        self.RBB = calib_RBBs
    
    def calc_gain(self):
        """Calc gain.
        
        Basically, gain = -rbbs / (calib_offsets - calib_bbcounts)
        
        This is how JPL did it:
        numerator = -1 * thermal_marker_node.calcRBB(chan,det)
        
        denominator = (thermal_marker_node.calc_offset_leftSV(chan, det) +
                       thermal_marker_node.calc_offset_rightSV(chan,det)) / 2.0
        
        Basically, that means: denominator = mean(loffset, roffset)
        
        For the second step of the denominator, they used calc_CBB, which is just
        the mean of counts in BB view:
        denominator -= thermal_marker_node.calc_CBB(chan, det)
        return numerator/denominator.
        """
        numerator = -1 * self.RBB
        
        # note how we are calculating only for thermal channels !!
        denominator = get_thermal_detectors(self.offsets) - \
                        get_thermal_detectors(self.CBB)
        gains = numerator / denominator
        self.gains = gains
    
    def interpolate_caldata(self):
        """Interpolated the offsets and gains all over the dataframe.
        
        This is needed AFTER the gain calculation, when applying the offsets and
        gains to all data.
        """
        
        ### create filter here for the kind of data to calibrate !!
        sdata = self.df[self.df.sdtype==0]
        
        # only work with real data, filter out meta-data
        sdata = get_data_columns(sdata, strict=True)
        
        # times are converted to float64 for the interpolation routine
        
        # the target where we want to interpolate for
        all_times = sdata.index.values.astype('float64')
        
        # these are the times as defined by above calc_calib_mean_times
        cal_times = self.calib_times.values.astype('float64')
        
        # create 2 new pd.DataFrames to hold the interpolated gains and offsets
        offsets_interp = pd.DataFrame(index=sdata.index)
        gains_interp   = pd.DataFrame(index=sdata.index)
        
        # get a list of columns for the thermal detectors only
        detectors = get_thermal_detectors(self.offsets).columns
        
        # just for printing out progress
        progressbar = ProgressBar(len(detectors))
        
        for i,det in enumerate(detectors):
            progressbar.animate(i+1)
            # change k for the kind of fit you want
            s_offset = Spline(cal_times, self.offsets[det], s=0.0, k=self.calfitting_order)
            s_gain   = Spline(cal_times, self.gains[det], s=0.0, k=self.calfitting_order)
            col_offset = s_offset(all_times)
            col_gain   = s_gain(all_times)
            offsets_interp[det] = col_offset
            gains_interp[det]   = col_gain
        
        self.sdata = sdata
        self.offsets_interp = offsets_interp
        self.gains_interp = gains_interp
    
    def calc_radiances(self):
        norm_radiance = (self.sdata - self.offsets_interp) * self.gains_interp
        abs_radiance = norm_radiance.copy()
        # as the conversion factor is only given per channel we only need
        # to loop over channels here, not single detectors
        for channel in self.thermal_channels:
            # this filter catches all detectors for the current channel
            abs_radiance[abs_radiance.filter(regex=channel+'_').columns] *= \
                self.norm_to_abs_converter.get_value(2,channel)
        self.norm_radiance = norm_radiance
        self.abs_radiance = abs_radiance
        logging.info('Calculated radiances.')
    
    def calc_tb(self):
        self.Tb = pd.DataFrame(index=self.abs_radiance.index)
        pbar = ProgressBar(147)
        i=0
        for channel in self.thermal_channels:
            for det in range(1,22):
                i+=1
                pbar.animate(i)
                cdet = channel + '_' + str(det).zfill(2)
                temps = self.rbbtable.get_tb(self.norm_radiance[cdet],
                                                self.mcs_div_mapping[channel])
                self.Tb[cdet] = pd.Series(temps,index=self.Tb.index)
        logging.info("Calculated brightness temperatures.")


#    counts = node.counts
#    offset = (tmnearest.offset_left_SV + tmnearest.offset_right_SV)/2.0
#    gain = tmnearest.gain
#    radiance = (counts - offset) * gain
   # radiance = rconverttable.convertR(radiance, chan, det)
   # tb = rbbtable.TB(radiance, chan, det)
   # radiance *= config.CalRadConstant(chan)
   #
    
