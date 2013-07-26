from collections import OrderedDict

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
        for bitname,val in self.dic.iteritems():
            # add the flagname and it's status, but cut off initial
            # qf_ from the name
            setattr(self, bitname, self.check_bit(val))

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
    bits_data=(
        #  Bit 0: Interpolation but one or more marker out of bounds
    	('interp_marker_oob', 0x00000001),
        #  Bit 1: Offsets and Gains from Nearest Marker used
    	('nearest_marker', 0x00000002),
        #  Bit 2: Same as bit 1, but nearest marker is out of bounds
    	('nearest_marker_oob', 0x00000004),
        #  Bit 3: Use constants for offsets and gains
    	('constants_only', 0x00000008),
    )
    bits = OrderedDict()
    for t in bits_data:
        bits[t[0]]=t[1]
        
    def __init__(self,value=0):
        super(CalibFlag,self).__init__(value,dic=self.bits)


class GeomFlag(Flag):
    bits_data=(
        #  Bit 0: Reserved for future use
    	('pointing_res', 0x00000001),
        #  Bit 1: Reserved for future use
    	('ephem_res', 0x00000002),
        #  Bit 2: Tracking data used to generate pointing geometry
    	('pointing_def', 0x00000004),
        #  Bit 3: Tracking data used to generate ephemeris geometery
    	('ephem_def', 0x00000008),
        # Bit 4 : Predictive SPICE kernels used to generate pointing geometry
        ('pointing_pred', 0x00000010),
        # Bit 5 : Predictive SPICE kernels used to generate ephemeris geometry
        ('ephem_pred', 0x00000020),
        # Bit 6: No predictive SPICE kernels availabe to generate pointing geometry
        ('pointing_none', 0x00000040),
        # Bit 7 : No predictive SPICE kernels available to generate ephemeris geometry
        ('ephem_none', 0x00000080),
    )
    bits = OrderedDict()
    for t in bits_data:
        bits[t[0]]=t[1]

    def __init__(self,value=0):
        super(GeomFlag,self).__init__(value,dic=self.bits)


class MiscFlag(Flag):
    bits_data=(
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
    bits = OrderedDict()
    for t in bits_data:
        bits[t[0]]=t[1]

    def __init__(self,value=0):
        super(MiscFlag,self).__init__(value,dic=self.bits)

