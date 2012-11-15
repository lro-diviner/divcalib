SV_LENGTH = 80

SV_NUM_SKIP_SAMPLE = 16
BBV_NUM_SKIP_SAMPLE = 16
SOLV_NUM_SKIP_SAMPLE = 16

#  Calibration quality mask
calib_quality_values=dict(
    #  Bit 0: Interpolation but one or more marker out of bounds
	qf_interp_marker_oob					= 0x00000001,
    #  Bit 1: Offsets and Gains from Nearest Marker used
	qf_nearest_marker						= 0x00000002,
    #  Bit 2: Same as bit 1, but nearest marker is out of bounds
	qf_nearest_marker_oob					= 0x00000004,
    #  Bit 3: Use constants for offsets and gains
	qf_constants_only						= 0x00000008
)

#  Misc quality mask
misc_quality_values=dict(
    #  Bit 0: Reserved for future use
	qf_misc_rfu0							= 0x00000001,
	qf_misc_eclipse							= 0x00000002,
	qf_misc_turn_on_transient				= 0x00000004,  
	qf_misc_abnormal_instrument_state		= 0x00000008,
	qf_misc_abnormal_instrument_temp_drift	= 0x00000010,
	qf_misc_noise							= 0x00000020,
	qf_misc_ch1_saturation					= 0x00000040,
	qf_misc_moving							= 0x00000080 
)

class Flag(object):
    """Helper class to deal with control words or flags.

    Bit setting and checking methods are implemented.
    """
    def __init__(self, value = 0,d = None):
        self.value = int(value)
        if d:
            self.d = d
            for flag,val in d.iteritems():
                    setattr(flag, self.check_bit(val))
    def set_bit(self, bit):
        self.value |= bit
    def check_bit(self, bit):
        return self.value & bit != 0
    def clear_bit(self, bit):    
        self.value &= ~bit


def get_offset_leftSV(chan, det):
    """docstring for get_offset_leftSV"""
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
    offset = tmnearest.offset