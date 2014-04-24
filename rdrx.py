"""This module provides utilities to deal with RDRx files."""
from diviner import file_utils as fu
import pandas as pd

# this list are the column names in rdrr that have detector specific data.
list_to_melt = [
    'cemis',
    'radiance',
    'csunazi',
    'clat',
    'cloctime',
    'clon',
    'qge',
    'qmi',
    'qca',
    'csunzen',
    'counts',
    'tb',
    'vlookz',
    'vlooky',
    'vlookx'
]


def get_example_rdrx():
    tstr = '2013031707'
    obs = fu.DivObs(tstr)
    return RDRR(obs.rdrrfname.path)


def colnames(colbase, channel=None):
    "create rdrx column names for one or all channels."
    if not channel:
        channels = range(1, 10)
    else:
        channels = [channel]
    colnames = []
    for c in channels:
        colnames.extend([colbase + '_' + str(c) + '_' + str(i).zfill(2)
                         for i in range(1, 22)])
    return colnames


# def renamer(colname):
#     cdetstr = '_'.join(colname.split('_')[1:])
#     cdet = au.CDet(cdetstr)
#     return cdet.

class RDRR(object):

    """Class to enable extracting data from RDRx."""

    def __init__(self, tstr_or_filename):
        self.df = fu.RDRR_Reader(tstr_or_filename).open()

    @property
    def columns(self):
        return self.df.columns

    def get_column(self, colbase):
        return self.df.filter(regex='^' + colbase + '_')

    def get_counts(self):
        return self.get_column('counts')

    def get_molten_col(self, colbase, channel):
        rdr1 = self.df
        df = rdr1[colnames(colbase, channel)]
        df = df.rename(columns=lambda x: int(x.split('_')[-1]))
        df = df.reset_index()
        return pd.melt(df, id_vars=['index'],
                       var_name='det', value_name=colbase)

    def merge_with_molten(self, colbase, channel, target_df):
        molten = self.get_molten_col(colbase, channel)
        return target_df.merge(molten, on=['index', 'det'])

    def get_edr_data(self):
        return self.df.filter(regex='edr_')


no_melt = [
    'jdate',
    'orbit',
    'sundist',
    'sunlat',
    'sunlon',
    'sclk',
    'sclat',
    'sclon',
    'scrad',
    'scalt',
    'el_cmd',
    'az_cmd',
    'af',
    'orientlat',
    'orientlon',
    'sounding',
    'from_pkt',
    'pkt_count',
    'safing',
    'safed',
    'freezing',
    'frozen',
    'rolling',
    'dumping',
    'moving',
    'temp_fault',
    'sc_time_secs',
    'sc_time_subs',
    'ticks_pkt_start',
    'ticks_at_sc_time',
    'ost_index',
    'est_index',
    'sst_index',
    'last_az_cmd',
    'last_el_cmd',
    'fpa_temp',
    'fpb_temp',
    'baffle_a_temp',
    'baffle_b_temp',
    'bb_1_temp',
    'oba_1_temp',
    'error_time',
    'error_id',
    'error_count',
    'commands_received',
    'commands_executed',
    'commands_rejected',
    'last_time_command',
    'last_eqx_prediction',
    'hybrid_temp',
    'fpa_temp_cyc',
    'fpb_temp_cyc',
    'baffle_a_temp_cyc',
    'baffle_b_temp_cyc',
    'oba_1_temp_cyc',
    'oba_2_temp',
    'bb_1_temp_cyc',
    'bb_2_temp',
    'solar_target_temp',
    'yoke_temp',
    'el_actuator_temp',
    'az_actuator_temp',
    'min_15v',
    'plu_15v',
    'solar_base_temp',
    'plu_5v',
    'edr_fpa_temp',
    'edr_fpb_temp',
    'edr_baffle_a_temp',
    'edr_baffle_b_temp',
    'edr_bb_1_temp',
    'edr_oba_1_temp',
    'edr_rotating_value_1',
    'edr_rotating_value_2',
    'edr_rotating_index_1',
    'edr_rotating_index_2',
    'edr_vref_c2',
    'edr_vref_c1',
    'edr_prt_narrow_c2',
    'edr_prt_narrow_c1',
    'edr_prt_wide_c2',
    'edr_prt_wide_c1',
    'edr_hybrid_temp',
    'edr_fpa_temp_cyc',
    'edr_fpb_temp_cyc',
    'edr_baffle_a_temp_cyc',
    'edr_baffle_b_temp_cyc',
    'edr_oba_1_temp_cyc',
    'edr_oba_2_temp',
    'edr_bb_1_temp_cyc',
    'edr_bb_2_temp',
    'edr_solar_target_temp',
    'edr_yoke_temp',
    'edr_el_actuator_temp',
    'edr_az_actuator_temp',
    'edr_min_15v',
    'edr_plu_15v',
    'edr_solar_base_temp',
    'edr_plu_5v',
    'edr_aref1',
    'edr_aref2',
    'edr_bref',
    'sdtype',
    'calib_block_labels',
    'space_block_labels',
    'bb_block_labels',
    'st_block_labels',
    'is_spaceview',
    'is_bbview',
    'is_stview',
    'is_moving',
    'is_stowed',
    'is_calib'
    ]
