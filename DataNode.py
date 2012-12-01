# /*
#  * DataNode.h
#  *
#  *  Created on: Oct 17, 2008
#  *      Author: romorris
#  */
# Adapted to Python on Nov 13, 2012
# Author: K.-Michael Aye

# leaving as reminder
#include <UtcTime.h>
#include <DetectorOffsets.h>
#include <GeomCache.h>
#include <CoverageMap.h>
#include <SpiceUsr.h>

#include "divl1b.h"

class Flag(object):
    """Helper class to deal with control words or flags.

    Bit setting and checking methods are implemented.
    """
    def __init__(self, value = 0):
        self.value = int(value)
    def set_bit(self, bit):
        self.value |= bit
    def check_bit(self, bit):
        return self.value & bit != 0
    def clear_bit(self, bit):    
        self.value &= ~bit

            
class DataNode(object):

	void setCounts(int channel, int detector, int cnts);
	void setActivityFlag();
	void setThermalQualityFlag(unsigned char mask)	{ tcalib_mask |= mask;					}
	void setVisibleQualityFlag(unsigned char mask)	{ vcalib_mask |= mask;					}
	void setCh1MiscQualityFlag(unsigned char mask)	{ ch1qmi_mask |= mask;					}
	void setMiscQualityFlag(unsigned char mask)		{ misc_mask |= mask; ch1qmi_mask |= mask;					}

	void setIsClear()							{ node_type_mask = clear;				}
	void setIsCalibratible()					{ node_type_mask |= calibratible;		}
	void setIsSpaceview()						{ node_type_mask |= spaceview;			}
	void setIsBlackbodyView()					{ node_type_mask |= blackbody_view;		}
	void setIsSolarTargetView()					{ node_type_mask |= solar_target_view;	}

	bool	isSaturated()						{ return(ch1_saturation);						}
	int		getCounts(int channel, int detector);

	bool isCalibratible()						{ return(node_type_mask & calibratible);		}
	bool isSpaceview()							{ return(node_type_mask & spaceview);			}
	bool isBBView()								{ return(node_type_mask & blackbody_view);		}
	bool isSTView()								{ return(node_type_mask & solar_target_view);	}

	#  Unlike isBBView() and isSTView() these determine whether we are looking
	#  at these targets without respect to whether the instrument is in motion or
	#  not.
	bool isBlackBodyLook();
	bool isSolarTargetLook();

	bool	setOrbit(int orb)		{ orbit = orb;							}
	void	setPerSclkGeom();							#  Assumes select fields are initialized
	void	setPerSclkDetectorGeom(CoverageMap *cm);	#  Assumes select fields are initialized

	#  Public accessors for values we need to calibrate
	void 	setCalRad(int c, int d, float val)			{ calrad[c][d] = val;	}
	void 	setTB(int c, int d, float val)				{ tb[c][d] = val;		}
	float 	getCalRad(int c, int d)						{ return(calrad[c][d]);	}
	float 	getTB(int c, int d)							{ return(tb[c][d]);		}
	
    # Per Dave Paige, TB values for channel 1 and 2 need to be scaled by 1000 for output, but not calculation.
    float 	getScaledTB(int c, int d);

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
    calib_quality = Flag()

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
    misc_quality = Flag()

	bool spice_debug;
        bool ch1_saturation;
	#  These are the fields that are loaded directly from L1A input records      #
	UtcTime *utc_time;
	double	sclk;							#  Decimal sclk
	string subsecond_sclk;					#  Subsecond-based sclk
	int	moving;
	int	dumping;
	int	rolling;
	int	safing;
	int	safed;
	int	freezing;
	int	frozen;
	double	azimuth;
	double 	elevation;
	double 	bb1_temp;
	double 	bb2_temp;
	int counts[9][21];
	int activity_flag;  					# TODO: Must derive activity flag, use enumerated types in DataNode

	unsigned char tcalib_mask;				#  Indicates quality of thermal channel calibration values (See SIS)
	unsigned char vcalib_mask;				#  Indicated quality of visible channel calibration values
	unsigned char ch1qmi_mask;				#  Indicated ch1 misc quality (channel 1 saturation)
	unsigned char geom_mask;				#  Indicates quality of geometry
	unsigned char misc_mask;				#  Indicated other quality

	unsigned int node_type_mask;			#  This identifies the kind of view, isolating geometry
											#  calculations to input loading time.

	DataNode *next_node,*last_node;
	DataNode *next_sview,*last_sview;
	DataNode *next_bbview,*last_bbview;
	DataNode *next_stview,*last_stview;


	#  Per-Sclk geometry fields
	SpiceDouble jdate;
	SpiceDouble sundist, sunlat, sunlon;
	SpiceDouble scrad, sclon, nadir_angle, boresight_angle;
	SpiceDouble sclat, scalt;
	SpiceDouble orient_lat, orient_lon;

	int orbit;

	#  Per-Sclk/Detector geometry fields
	float vlookx[9][21], vlooky[9][21], vlookz[9][21];
	float clat[9][21], clon[9][21];
	float cemis[9][21];
	float csunazi[9][21], csunzen[9][21];
	float cloctime[9][21];

	#  Enumerated type that classifies each input record by
	#  the kind of view.
	view_kind=dict(
		clear				= 0x00000000,
		calibratible		= 0x00000001,
		spaceview			= 0x00000002,
		blackbody_view		= 0x00000004,
		solar_target_view	= 0x00000008
	)

	#  Calibrated values we derive
	float calrad[9][21];
	float tb[9][21];

	DetectorOffsets *doffsets;

	bool show_geom_results(int c, int d);

	#  This object is a performance enhancement.
	GeomCache *gcache;

};

#endif
