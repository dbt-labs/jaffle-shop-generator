import datetime as dt
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator

from jafgen.curves import AnnualCurve, GrowthCurve, WeekendCurve


def time_to_delta(t: dt.time) -> dt.timedelta:
    """Reinterpret a time (fixed time at a day) as a timedelta (duration)."""
    return dt.datetime.combine(dt.datetime.min, t) - dt.datetime.min


def time_delta_add(t: dt.time, d: dt.timedelta) -> dt.time:
    """Add time and a timedelta without worrying about date overflow."""
    t_dt = dt.datetime.combine(dt.date.min, t)
    return (t_dt + d).time()


def time_delta_sub(t: dt.time, d: dt.timedelta) -> dt.time:
    """Subctract time and timedelta without worrying about date underflow."""
    return time_delta_add(t, -d)


def time_from_total_minutes(mins: int) -> dt.time:
    """Return a datetime.time from total minutes since midnight."""
    return dt.time(hour=mins // 60, minute=mins % 60)


def total_minutes_elapsed(t: dt.time | dt.timedelta) -> int:
    """Get the total minutes that passed since midnight for a time or timedelta."""
    if isinstance(t, dt.time):
        return t.second * 60 + t.minute

    return int(t.total_seconds() // 60)


class Season(str, Enum):

    """A season of the year."""

    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"

    @classmethod
    def from_date(cls, date: dt.date) -> "Season":
        """Get the date's Season (in the northern hemisphere)."""
        month_no = date.month
        day_no = date.day

        if month_no in (1, 2) or (month_no == 3 and day_no < 21):
            return cls.WINTER
        elif month_no in (3, 4, 5) or (month_no == 6 and day_no < 21):
            return cls.SPRING
        elif month_no in (6, 7, 8) or (month_no == 9 and day_no < 21):
            return cls.SUMMER
        elif month_no in (9, 10, 11) or (month_no == 12 and day_no < 21):
            return cls.FALL

        return cls.WINTER


@dataclass(frozen=True)
class Day:

    """A wrapper around `datetime.date` with some convenience functions."""

    EPOCH = dt.datetime(year=2018, month=9, day=1)
    SEASONAL_MONTHLY_CURVE = AnnualCurve()
    WEEKEND_CURVE = WeekendCurve()
    GROWTH_CURVE = GrowthCurve()

    date_index: int
    minutes: int = 0
    date: dt.datetime = field(init=False)
    effects: list[float] = field(init=False)

    def __post_init__(self):
        """Set `date` and `effects` based on `__init__` args."""
        # Have to use object.__setattr__ since it's frozen dataclass
        object.__setattr__(self, "date", self.EPOCH + dt.timedelta(
            days=self.date_index,
            minutes=self.minutes)
        )
        object.__setattr__(self, "effects", [
            self.SEASONAL_MONTHLY_CURVE.eval(self.date),
            self.WEEKEND_CURVE.eval(self.date),
            self.GROWTH_CURVE.eval(self.date),
        ])

    def at_minute(self, minutes: int) -> "Day":
        """Get a new instance of `Day` in the same day but different minute."""
        return Day(self.date_index, minutes=minutes)

    def get_effect(self) -> float:
        """Get a simulation effect multiplier based on all of this day's effects."""
        total = 1
        for effect in self.effects:
            total = total * effect
        return total

    @property
    def day_of_week(self) -> int:
        """Get the day of the week, where Monday=0 and Sunday=6."""
        return self.date.weekday()

    @property
    def is_weekend(self) -> bool:
        """Whether this day is in the weekend."""
        return self.date.weekday() >= 5

    @property
    def season(self) -> Season:
        """Get the season of the year this day is in."""
        return Season.from_date(self.date)

    @property
    def total_minutes(self) -> int:
        """Get the total elapsed minutes of this day."""
        return self.date.hour * 60 + self.date.minute


@dataclass(frozen=True)
class DayHoursOfOperation:

    """A shop's hours of operations during a single day."""

    opens_at: dt.time
    closes_at: dt.time

    @property
    def total_minutes_open(self) -> int:
        """The total minutes the shop will be open this day."""
        time_open = time_delta_sub(self.closes_at, time_to_delta(self.opens_at))
        return total_minutes_elapsed(time_open)

    def is_open(self, time: dt.time) -> bool:
        """Whether the shop will be open during `time`."""
        return time >= self.opens_at and time < self.closes_at

    def iter_minutes(self) -> Iterator[int]:
        """Iterate over all the minutes in this day of operation."""
        for minute in range(self.total_minutes_open):
            yield minute


@dataclass(frozen=True)
class WeekHoursOfOperation:

    """A shop's hours of operations during a week.

    Consists of two collections of `DayHoursOfOperation`: one for the week days
    and another one for the weekends.
    """

    week_days: DayHoursOfOperation
    weekends: DayHoursOfOperation

    def _get_todays_schedule(self, day: Day) -> DayHoursOfOperation:
        return self.weekends if day.is_weekend else self.week_days

    def opens_at(self, day: Day) -> dt.time:
        """Get the time the shop will open on `day`."""
        return self._get_todays_schedule(day).opens_at

    def closes_at(self, day: Day) -> dt.time:
        """Get the time the shop will close on `day`."""
        return self._get_todays_schedule(day).closes_at

    def total_minutes_open(self, day: Day) -> int:
        """Get the total minutes the shop will be open on `day`."""
        return self._get_todays_schedule(day).total_minutes_open

    def is_open(self, day: Day) -> bool:
        """Whether the shop is open on `day`."""
        time = time_from_total_minutes(day.total_minutes)
        return self._get_todays_schedule(day).is_open(time)

    def iter_minutes(self, day: Day) -> Iterator[int]:
        """Iterate over all the minutes in this day of operation."""
        yield from self._get_todays_schedule(day).iter_minutes()
