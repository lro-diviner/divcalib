import operator
from datetime import datetime as dt
from datetime import timedelta

from .exceptions import DivTimeLengthError


class DivTime(object):

    """Manage time-related metadata for Diviner observations.

    Abstract class! Use the derivatives!
    """

    fmt_hour = "%Y%m%d%H"
    len_hour = 10
    fmt_day = "%Y%m%d"
    len_day = 8

    @classmethod
    def from_dtime(cls, dtime):
        tstr = dtime.strftime(cls.fmt_hour)
        return cls(tstr)

    def __init__(self, tstr):
        if not self.len_day <= len(tstr) <= self.len_hour:
            raise DivTimeLengthError(tstr, "8 <= len(tstr) <= 10")
        self.tstr = tstr
        self.year = self.tstr[:4]
        self.month = self.tstr[4:6]
        self.day = self.tstr[6:8]
        if len(self.tstr) > 8:
            self.hour = self.tstr[8:10]
        if len(tstr) == 8:
            fmt = self.fmt_day
        elif len(tstr) == 10:
            fmt = self.fmt_hour
        self.fmt = fmt
        self.dtime = dt.strptime(self.tstr, fmt)

    def __str__(self):
        s = f"{self.__class__.__name__}\n"
        s += f"{self.dtime}"
        return s

    def __repr__(self):
        return self.__str__()

    @property
    def tindex(self):
        return self.tstr[:8] + " " + self.tstr[8:]

    @property
    def previous(self):
        return DivTime.from_dtime(self.dtime - timedelta(hours=1))

    @property
    def next(self):
        return DivTime.from_dtime(self.dtime + timedelta(hours=1))

    def _time_comparison(self, other, op):
        if other.__class__ is self.__class__:
            return op(self.dtime, other.dtime)
        else:
            return NotImplemented

    def __lt__(self, other):
        return self._time_comparison(other, operator.lt)

    def __le__(self, other):
        return self._time_comparison(other, operator.le)

    def __eq__(self, other):
        return self._time_comparison(other, operator.eq)

    def __ne__(self, other):
        return self._time_comparison(other, operator.ne)

    def __gt__(self, other):
        return self._time_comparison(other, operator.gt)

    def __ge__(self, other):
        return self._time_comparison(other, operator.ge)
