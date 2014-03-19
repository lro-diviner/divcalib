from __future__ import division, print_function
import pandas as pd
import numpy as np
from scipy.interpolate import UnivariateSpline as Spline
#from plot_utils import ProgressBar
import logging
from numpy import poly1d
import os
import divconstants as config
import file_utils as fu
from exceptions import *
from div_l1a_fix import correct_noise

#logging.basicConfig(filename='divcalib.log',
#	   	    format='%(asctime)s %(message)s',
#		    level=logging.INFO)

channels = ['a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'b1', 'b2', 'b3']
thermal_channels = channels[2:]
tel_A_channels = channels[:6]
tel_B_channels = channels[6:]
detectors = [i + '_' + str(j).zfill(2) for i in channels for j in range(1, 22)]
tel_A_detectors = [det for det in detectors if det.startswith('a')]
tel_B_detectors = [det for det in detectors if det.startswith('b')]
thermal_detectors = detectors[-147:]

mcs_div_mapping = {'a1': 1, 'a2': 2, 'a3': 3,
                   'a4': 4, 'a5': 5, 'a6': 6,
                   'b1': 7, 'b2': 8, 'b3': 9}



def get_calib_blocks(df, blocktype, del_zero=True):
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
    """Determine mean time for a given dataframe.

    This calculation depends on the number of skipped samples. This is consistent with
    the existing approach that is done by JPL's previous calibration. They would
    calculate the time starting from the node counter 'bbstart', which is the starting
    point after skipping samples, compared to 'bborigstart' which is the first node
    of a bb-view.
    """
    # rec
    df = df_in[skipsamples:]
    try:
        t1 = df.index[0]
        t2 = df.index[-1]
    except IndexError:
        print("Problem with calculating mean time.")
        logging.error('Index not found in get_mean_time. '
                        'Length of df: {0}'.format(len(df.index)))
	raise MeanTimeCalcError('unknown')
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


def get_data_columns(df):
    return df.filter(items=detectors)


def get_thermal_detectors(df):
    return df.filter(items=thermal_detectors)


class RBBTable(object):
    """Table class to convert between temperatures and radiances."""
    def __init__(self):
        super(RBBTable, self).__init__()
        self.df = pd.read_hdf(os.path.join(fu.codepath,
                                           'data',
                                           't_to_norm_rad.hdf'),
                              'df')
        self.table_temps = self.df.index.values.astype('float')
        self.t2rad = {}
        self.rad2t = {}
        # the radiances for abs(T) < 3 K are 0 for channels 3-5 which means that during the
        # backward lookup of radiance to T, the 0 radiance can not be looked up functionally
        # (it's now a relation and not a function anymore). This makes the Spline interpolator
        # ignore the negative part which I cannot afford.
        # The work-around is to interpolate from T -3 to 3 (which are impossibly close to 0
        # anyway for channels 3-5), ignoring all 0 values for T in [-2..2]
        sliced = self.df.ix[abs(self.df.index) > 2]
        for ch in range(3, 10):
            # store the Spline interpolators in dictionary, 1 per channel
            self.t2rad[ch] = Spline(self.table_temps, self.df[ch],
                                    s=0.0, k=1)
            # for channels 3-5, take the data without the values around 0:
            if ch < 6:
                data = sliced[ch]
                temps = sliced.index.values.astype('float')
            else:
                data = self.df[ch]
                temps = self.table_temps
            # store the Spline interpolators in dictionary, 1 per channel
            self.rad2t[ch] = Spline(data, temps, s=0.0, k=1)

    def get_radiance(self, temps, ch):
        return self.t2rad[ch](temps)

    def get_tb(self, rads, ch):
        return self.rad2t[ch](rads)

    def get_telA_radiances(self, temp):
        rads = []
        for i in range(3,7):
            rads.extend(21*[float(self.get_radiance(temp, i))])
        return rads

    def get_telB_radiances(self, temp):
        rads = []
        for i in range(7,10):
            rads.extend(21*[float(self.get_radiance(temp, i))])
        return rads

    def lookup_radiances_for_thermal_channels(self, mapping_source, store):
        """Convert the temperatures to radiances.

        Parameters
        ==========
            mapping_source: pandas DataFrame that has to contain the columns
                            ['bb_1_temp_interp', 'bb_2_temp_interp'], ergo
                            this would be called *after* the interpolation
                            of the bb_x temps is done.
            store : pandas DataFrame for storing the result
        """
        # different mapping sources depending on if we lookup only for single
        # values at calblock times or for all interpolated temperatures
        # the caller of this function determines this by providing the mapping source
        mapping = {'a': mapping_source['bb_1_temp_interp'],
                   'b': mapping_source['bb_2_temp_interp']}

        # loop over thermal channels ('a3'..'b3', i.e. 3..9 in Diviner lingo)
        for channel in thermal_channels:
            #link to the correct bb temps by checking first letter of channel
            bbtemps = mapping[channel[0]]

            #look up the radiances for this channel
            RBBs = self.get_radiance(bbtemps, mcs_div_mapping[channel])
            channel_rbbs = pd.Series(RBBs, index=mapping_source.index)
            for i in range(1,22):
                col_name = channel + '_' + str(i).zfill(2)
                store[col_name] = channel_rbbs


###
### global
###
rbbtable = RBBTable()

class RadianceCorrection(object):
    """Polynomial correction for the interpolated radiances.

    This is the equivalent class to RConvertTable class in JPL's code.
    """
    def __init__(self, new_corr=True):
        super(RadianceCorrection, self).__init__()
        self.excelfile = pd.io.excel.ExcelFile(
                            os.path.join(fu.codepath,
                                         'data',
                                         'Rn_vs_Rn_interp_coefficients_new.xlsx'))
        # the delivered new excel file has both the old and new coeffcients on two
        # different worksheets inside the file.
        # the old correction coefficients are on sheet_names[0], the new ones on
        # sheet_names[1]
        if new_corr:
            sheet_index = 1
        else:
            sheet_index = 0
        shname = self.excelfile.sheet_names[sheet_index]
        df = self.excelfile.parse(shname, skiprows=[0,1],index_col=0,header=None)
        df.index.name = ""
        df.columns = thermal_detectors
        self.df = df

    def convertR(self, radiance, chan, det):
        detID = str(chan) + '_' + str(det).zfill(2)
        # put the reverse order (decreasing) of the excel sheet into poly1d object
        p = poly1d(self.df[detID][::-1].values)
        return p(radiance)

    def correct_radiance(self, radiance):
        "Apply polynomials from table on radiance"
        detID = radiance.name
        if detID not in thermal_detectors:
            return radiance
        # [::-1] is required because I have to invert the sequence of Marc Foote's
        # table, as poly1d needs it in highest order first
        p = poly1d(self.df[detID][::-1].values)
        return p(radiance)


class CalBlock(object):
    """Class to handle different options on how to deal with a single cal block.

    IN:
        dataframe, containing all meta-data like label numbers, H/K etc.
        skip_samples, integer, indicating how many samples to skip for
            mean value calculation
    OUT:
        via several class methods and properties (like members)
    """
    def __init__(self, df):
        """Initialize CalBlock instance.

        The init method creates for each of [space, bb, st] the following data item for the
        respective view:
        * xxviews (the dataframe filtered for the view)
        * xx_grouped (the groupby object to enable skipping samples for each spaceview uniquely
            (or for other double-views, should they exist, like the double stview I found.))
        * unique_xx_labels (the unique and sorted list of labels, useful to sequence operations
            on a view, in case that is required.)

        It also makes some checks on the appearance of the number of views and lengths of these
        views and logs any anomalies.
        Lastly, it sets a boolean to define if this CalBlock has all required data to enable
        a gain calculation. If not, it still could be useful for an offset determination.
        """
        self.df = df
        self.offsets_done = False
        for view in 'space bb st'.split():
            viewdf = get_data_columns(self.df[self.df['is_'+view+'view']])
            setattr(self, view + 'views', viewdf)
            label = view + '_block_labels'
            setattr(self, view + '_grouped', viewdf.groupby(self.df[label]))
            setattr(self, 'unique_' + view + '_labels', self.get_unique_labels(view))

        self.has_gain = self.has_complete_spaceview and self.has_complete_bbview
        self.logging()

    def logging(self):
        "Perform sanity checks and log anomalies"
        if len(self.unique_bb_labels) > 1:
            logging.info("Found more than one BB label in CalBlock"
                         " at {}.".format(self.df.index[0]))
        if len(self.unique_st_labels) > 1:
            logging.info("Found more than one ST label in CalBlock"
                         " at {}.".format(self.df.index[0]))
        if len(self.unique_space_labels) < 2:
            logging.info("Found less than 2 SPACE labels in CalBlock"
                         " at {}.".format(self.df.index[0]))
        if np.any(self.st_grouped.size() > config.ST_LENGTH):
            logging.info("ST views larger than {} at {}.".format(config.ST_LENGTH,
                                                        self.df.index[0]))
        if np.any(self.space_grouped.size() > config.SPACE_LENGTH):
            logging.info("Space-view larger than {} at {}.".format(config.SPACE_LENGTH,
                                                        self.df.index[0]))
        if len(self.bbviews) > config.BB_LENGTH:
            logging.info("BB-view larger than {} at {}.".format(config.BB_LENGTH,
                                                                self.df.index[0]))

    def get_unique_labels(self, view):
        labels = self.df[view + '_block_labels'].unique()
        return np.sort(labels[labels > 0])

    @property
    def has_complete_spaceview(self):
        return np.any(self.space_grouped.size() >= config.SPACE_LENGTH)

    @property
    def has_complete_bbview(self):
        bbview = self.bbviews
        return len(bbview) >= config.BB_LENGTH

    @property
    def has_complete_stview(self):
        return len(self.stviews) >= config.ST_LENGTH

    def check_length_get_mean(self, group, skip_samples):
        return group[skip_samples:].mean()

    def get_offsets(self, method='mean', skipsamples=config.SV_NUM_SKIP_SAMPLE):
        """Provide offsets for method as required.

        At initialisation, this object receives the number of samples to skip.
        That number `self.skipsamples` is used here for the offset calculation.
        IN:
            offset method. Choices:
                'mean': all available spaceviews will be averaged (after skipping
                        <skipsamples> samples)
                'each': each spaceview provides one time and one offset value.
        """
        # Check
        if not self.has_complete_spaceview:
            return None
        elif method=='mean':
            # first, mean values of each spaceview, with skipped removed:
            mean_spaceviews = self.space_grouped.agg(self.check_length_get_mean,
                                                     config.SV_NUM_SKIP_SAMPLE)
            # then return mean value of these 2 labels, detectors as index.
            return mean_spaceviews.mean()

    @property
    def offsets_time(self):
        # as i'm only in here when i don't use bb_time from calc_gain(), i don't
        # need to check anymore if this calblock has_gain, it should not have at this point
        return get_mean_time(self.spaceviews, config.SV_NUM_SKIP_SAMPLE)

    @property
    def bb_time(self):
        return get_mean_time(self.bbviews, config.BBV_NUM_SKIP_SAMPLE)

    @property
    def offsets(self):
        if self.offsets_done:
            offsets = pd.DataFrame(self.offsets_calculated).T
            offsets.index = [self.offsets_time_calculated]
	elif not self.has_complete_spaceview:
	    return
        else:
            offsets = pd.DataFrame(self.get_offsets()).T
            time = self.offsets_time
            if time == np.nan:
                logging.error("Found no offset time at  {}. Should not even reached"
                             " this point, as calblock must has_complete_spaceview."
                              .format(self.df.index[0]))
                return
            offsets.index = [self.offsets_time]
        return offsets

    def calc_BB_radiance(self):
        """Calculate like JPL only one RBB value for a mean BB temperature. """
        # procedure same as calib_cbb
        T_cols = ['bb_1_temp_interp','bb_2_temp_interp']

        # restrict the data to the BB view
        bbviews_temps = self.df[self.df.is_bbview][T_cols]
        # get the mean time for the BB view

        # determine the mean value of the interpolated BB temps, minus skipped
        bbtemps_mean = bbviews_temps[config.BBV_NUM_SKIP_SAMPLE:].mean()

        # convert the mean temps to radiances
        rads = []
        rads.extend(rbbtable.get_telA_radiances(bbtemps_mean[0]))
        rads.extend(rbbtable.get_telB_radiances(bbtemps_mean[1]))
        return pd.Series(np.array(rads), index=thermal_detectors)

    def get_gains(self):
        if not self.has_gain:
            return None
        RBB = self.calc_BB_radiance()
        offsets = self.get_offsets(method='mean')
        bb_time = self.bb_time
        CBB = self.get_mean_BB_counts()
        gains = pd.DataFrame(-RBB / get_thermal_detectors(offsets - CBB)).T
        gains.index = [bb_time]
        # as the CalBlock has gain, the offsets used here are the ones to be used for
        # calibration and no other calculation is required. Therefore save these for the
        # collector routine in Calibrator
        self.offsets_calculated = offsets
        self.offsets_time_calculated = bb_time
        self.offsets_done = True
        return gains

    def get_mean_BB_counts(self):
        return get_data_columns(self.check_length_get_mean(self.bbviews,
                                                           config.BBV_NUM_SKIP_SAMPLE))


class Calibrator(object):
    """currently set up to work with a 'wide' dataframe.

    Meaning, all detectors have their own column.
    """

    # temperature - radiance converter table
    rbbtable = RBBTable()
    def __init__(self, df, pad_bbtemps=False,
                           single_rbb=True, skipsamples=True,
                           do_rad_corr=True,
                           do_negative_corr=False,
                           calfitting_order=1,
                           new_rad_corr=True,
                           fix_noise=False,
                           do_jpl_calib=False):
        # quick way to simulate JPL calib as good as possible
        if do_jpl_calib:
            pad_bbtemps = True
            single_rbb = True
            skipsamples = True
            do_rad_corr = False
            fix_noise = False

        if fix_noise:
            self.df = correct_noise(df)
        else:
            self.df = df.copy()

        logging.info("Calibrating from {} to {}.".format(df.index[0], df.index[-1]))
        self.caldata = self.df[self.df.is_calib]
        self.calgrouped = self.caldata.groupby(self.df.calib_block_labels)

        # to control if bbtemps are interpolated or just forward-filled (=padded)
        self.pad_bbtemps = pad_bbtemps

        # to control if RBB are just determined for 1 mean bb temp (JPL's method)
        #or for all bbtemps of a bbview
        # I have confirmed in tests that the results differ negligibly (2e-16 rads)
        # and the JPL method (single_rbb=True) is better in speed
        self.single_rbb = single_rbb

        # to control if some of the first samples of views are being skipped
        self.skipsamples = skipsamples
        if skipsamples == True:
            self.BBV_NUM_SKIP_SAMPLE = config.BBV_NUM_SKIP_SAMPLE
            self.SV_NUM_SKIP_SAMPLE = config.SV_NUM_SKIP_SAMPLE
            self.STV_NUM_SKIP_SAMPLE = config.STV_NUM_SKIP_SAMPLE
        else:
            self.BBV_NUM_SKIP_SAMPLE = 0
            self.SV_NUM_SKIP_SAMPLE = 0
            self.STV_NUM_SKIP_SAMPLE = 0

        # control if radiance should be corrected
        self.do_rad_corr = do_rad_corr

        # subtract the radiance correction instead of adding
        self.do_negative_corr = do_negative_corr

        # degree of order for the fitting of calibration data
        self.calfitting_order = calfitting_order

        # radiance non-linearity correction
        self.radcorr = RadianceCorrection(new_corr=new_rad_corr)

        # loading converter factors norm-to-abs-radiances
        self.norm_to_abs_converter = pd.read_pickle(os.path.join(fu.codepath,
                                                  'data',
                                                  'Normalized_to_Absolute_Radiance.df'))
        # rename column names to match channel names here
        self.norm_to_abs_converter.columns = thermal_channels

            
    def call_up_to(self, wanted):
        keys = 'bbtemps rbb offsets cbb gain caldata rads tb'.split()
        methods =  {'bbtemps':self.interpolate_bb_temps,
                   'rbb':self.calc_one_RBB,
                   'offsets':self.calc_offsets,
                   'cbb':self.calc_CBB,
                   'gain':self.calc_gain,
                   'caldata':self.interpolate_caldata,
                   'rads':self.calc_radiances,
                   'tb':self.calc_tb}

        for key in keys:
            methods[key]()
            if key == wanted:
                break

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
        ### Process CalBlocks
        #####
        self.process_calblocks()

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

        # converting to float because the fitting libraries want to have floats
        all_times = df.index.values.astype('float64')

        # loop over both temperature arrays [D.R.Y. principle!]
        # the number of data points in bb1temps are much higher, but for
        # consistency we should interpolate both the same way.
        for bbtemp in [bb1temps, bb2temps]:
            # converting the time series to floats for interpolation
            ind = bbtemp.index.values.astype('float64')

            # s=0.0 means I do not allow distance from measured points for the spline
            # k=1 means that it will be a local-linear fitted spline between points

            # create interpolator function
            temp_interpolator = Spline(ind, bbtemp, s=0.0, k=1)

            # get new temperatures at all_times
            df[bbtemp.name + '_interp'] = temp_interpolator(all_times)

    def process_calblocks(self):
        calblocks = get_calib_blocks(self.df, 'calib')
        gain_container = []
        offset_container = []
        for label,calblock in calblocks.iteritems():
            logging.debug("Processing label {}".format(label))
            if not np.any(calblock[calblock.is_calib]):
                n_moving = len(calblock[calblock.is_moving])
                logging.warning("No caldata in calib_label at {}.  Found only {}"
                                " moving samples.".format(self.df.index[0], n_moving))
                continue
            cb = CalBlock(calblock)
            gain_container.append(cb.get_gains())
            offset_container.append(cb.offsets)
        self.gains = pd.concat(gain_container)
        self.offsets = pd.concat(offset_container)

    def interpolate_caldata_worker(self, offset_times, bbcal_times, all_times):

        sdata = get_data_columns(self.df)

        # create 2 new pd.DataFrames to hold the interpolated gains and offsets
        offsets_interp = pd.DataFrame(index=sdata.index)
        gains_interp   = pd.DataFrame(index=sdata.index)

        for det in thermal_detectors:
            # change k for the kind of fit you want
            s_offset = Spline(offset_times, self.offsets[det], s=0.0,
                              k=self.calfitting_order)
            s_gain   = Spline(bbcal_times, self.gains[det], s=0.0,
                              k=self.calfitting_order)
            offsets_interp[det] = s_offset(all_times)
            gains_interp[det]   = s_gain(all_times)

        return offsets_interp, gains_interp

    def interpolate_gains(self, bbcal_times, all_times):
        def do_spline(col, times):
            return Spline(times, col, s=0.0, k=self.calfitting_order)(all_times)

        np_gains = np.apply_along_axis(do_spline,
                                       0,
                                       self.gains[thermal_detectors],
                                       bbcal_times)

        gains_interp = pd.DataFrame(np_gains,
                                    index=self.df.index,
                                    columns=thermal_detectors)

        return gains_interp

    def interpolate_offsets(self, offset_times, all_times):

        def do_spline(col, times):
            return Spline(times, col, s=0.0, k=self.calfitting_order)(all_times)

        np_offsets = np.apply_along_axis(do_spline,
                                         0,
                                         self.offsets[thermal_detectors],
                                         offset_times)

        offsets_interp = pd.DataFrame(np_offsets,
                                      index=self.df.index,
                                      columns=thermal_detectors)
        return offsets_interp


    def interpolate_caldata(self):
        """Interpolate the offsets and gains all over the dataframe.

        This is needed AFTER the gain calculation, for applying the offsets and
        gains to all data.
        """

        ### create filter here for the kind of data to calibrate !!
        # before, I was only producing science data for non-calibblock data. now I do for all
        # as it was done like that before.
        # sdata = self.df[self.df.sdtype==0]
        sdata = self.df

        # only work with real data, filter out meta-data
        sdata = get_data_columns(sdata)

        # the target where we want to interpolate for
        all_times = sdata.index.values.astype('float64')

        if len(self.gains) == 1:
            logging.warning("Only one gain found. Propagating over whole hour at"
                            " {}.".format(self.df.index[0]))
            gains_interp = pd.DataFrame(index=sdata.index)
            for col in self.gains.columns:
                gains_interp[col] = self.gains[col].values[0]
        else:
            bbcal_times = self.gains.index.values.astype('float64')
            gains_interp = self.interpolate_gains(bbcal_times, all_times)

        if len(self.offsets) == 1:
            logging.warning("Only one offsets found. Propagating over whole hour"
                            " at {}.".format(self.df.index[0]))
            offsets_interp = pd.DataFrame(index=sdata.index)
            for col in self.offsets.columns:
                offsets_interp[col] = self.offsets[col].values[0]
        else:
            offset_times = self.offsets.index.values.astype('float64')
            offsets_interp = self.interpolate_offsets(offset_times, all_times)

        self.sdata = sdata
        self.offsets_interp = offsets_interp
        self.gains_interp = gains_interp

    def calc_radiances(self):
        norm_radiance = (self.sdata - self.offsets_interp) * self.gains_interp

        if self.do_rad_corr:
            logging.info("Performing radiance correction on {}".format(df.index[0]))
            # restricting to thermal dets is not required thanks to handling
            # it upstairs, so commenting it out for now.
            # thermal_dets = get_thermal_detectors(norm_radiance)
            corrected = norm_radiance.apply(self.radcorr.correct_radiance)
            diff = corrected - norm_radiance
            if self.do_negative_corr:
                norm_radiance = norm_radiance - diff
            else:
                norm_radiance = norm_radiance + diff
        abs_radiance = norm_radiance.copy()

        # as the conversion factor is only given per channel we only need
        # to loop over channels here, not single detectors
        for channel in thermal_channels:
            # this filter catches all detectors for the current channel
            abs_radiance[abs_radiance.filter(regex=channel+'_').columns] *= \
                self.norm_to_abs_converter.get_value(2, channel)
        self.norm_radiance = norm_radiance
        self.abs_radiance = abs_radiance
        logging.debug('Calculated radiances.')

    def calc_tb(self):
        container = []
        for channel in thermal_channels:
            tbch = self.norm_radiance.filter(regex=channel+'_').apply(self.rbbtable.get_tb,
                                                        args=(mcs_div_mapping[channel],))
            container.append(tbch)
        self.tb = pd.concat(container, axis=1)
        # to not render existing code useless
        self.Tb = self.tb
        logging.debug("Calculated brightness temperatures.")
