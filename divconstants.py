# define the default number of points that each view should have
SV_LENGTH = STV_LENGTH = BBV_LENGTH = 80

# integrated length of spaceview for all detectors (80*9*21):
SV_LENGTH_TOTAL = 15120

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
