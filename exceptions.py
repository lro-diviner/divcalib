class DivCalibError(Exception):
    """Base class for exceptions in this module."""
    pass


class ViewLengthError(DivCalibError):
    """ Exception for view length (9 ch * 21 det * 80 samples = 15120).

    SV/BBV/ST_LENGTH_TOTAL defined in divconstants.
    """
    def __init__(self, view, expected, received):
        self.view = view
        self.expected = expected
        self.received = received
    def __str__(self):
        return "Length of {0}-view not the expected {1}. "\
                "Instead: {2}".format(self.view,
                                      self.expected,
                                      self.received)


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
        self.method = method
        self.location = location
    def __str__(self):
        return "Method {0} not defined here. ({1})".format(self.method,
                                                           self.location)


class WrongTypeError(DivCalibError):
    def __init__(self, type_required, type_current):
        self.type_required = type_required
        self.type_current = type_current
    def __str__(self):
        return "Wrong type {0} for requested operation. "\
                "Need {1}".format(self.type_current,
                                  self.type_required)


class MeanTimeCalcError(DivCalibError):
    def __init__(self, t):
        self.t = t
    def __str__(self):
        return "Problem calculating mean time at hour {}".format(self.t)


class DivTimeLengthError(Exception):
    def __init__(self, tstr, expected):
        self.tstr = tstr
        self.expected = expected
    def __str__(self):
        return "Length of tstr {0} does not fit expected format {1}.".format(
                                                self.tstr,
                                                self.expected)


class RDRR_NotFoundError(Exception):
    pass

class RDRS_NotFoundError(Exception):
    pass

class L1ANotFoundError(Exception):
    pass
