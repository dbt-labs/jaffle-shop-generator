import datetime as dt
from enum import Enum
from dataclasses import dataclass
from typing import Iterator 


from jafgen.curves import AnnualCurve, WeekendCurve, GrowthCurve

class Season(Enum, str):
    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"

    @classmethod
    def from_date(cls, date: dt.date) -> "Season":
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

@dataclass(init=False)
class Day:
    EPOCH = dt.datetime(year=2018, month=9, day=1)
    SEASONAL_MONTHLY_CURVE = AnnualCurve()
    WEEKEND_CURVE = WeekendCurve()
    GROWTH_CURVE = GrowthCurve()

    def __init__(self, date_index: int, minutes: int = 0):
        self.date_index = date_index
        self.date = self.EPOCH + dt.timedelta(days=date_index, minutes=minutes)
        self.effects = [
            self.SEASONAL_MONTHLY_CURVE.eval(self.date),
            self.WEEKEND_CURVE.eval(self.date),
            self.GROWTH_CURVE.eval(self.date),
        ]

    def at_minute(self, minutes: int) -> "Day":
        return Day(self.date_index, minutes=minutes)

    def get_effect(self) -> float:
        total = 1
        for effect in self.effects:
            total = total * effect
        return total

    @property
    def day_of_week(self) -> int:
        return self.date.weekday()

    @property
    def is_weekend(self) -> bool:
        # 5 + 6 are weekends
        return self.date.weekday() >= 5

    @property
    def season(self) -> Season:
        return Season.from_date(self.date)

    @property
    def total_minutes(self) -> int:
        return self.date.hour * 60 + self.date.minute

@dataclass(frozen=True)
class DayHoursOfOperation:
    opens_at: dt.time 
    closes_at: dt.time 

    @property
    def total_minutes_open(self) -> int:
        time_open = dt.datetime.combine(dt.date.min, self.closes_at) - dt.datetime.combine(dt.date.min, self.opens_at)
        return int(time_open.total_seconds() // 60)

    def is_open(self, time: dt.time) -> bool:
        return time >= self.opens_at and time < self.closes_at

    def iter_minutes(self) -> Iterator[int]:
        for minute in range(self.total_minutes_open):
            yield minute

@dataclass(frozen=True)
class WeekHoursOfOperation:
    week_days: DayHoursOfOperation
    weekends: DayHoursOfOperation

    def _get_todays_schedule(self, day: Day) -> DayHoursOfOperation:
        return self.weekends if day.is_weekend else self.week_days

    def total_minutes_open(self, day: Day) -> int:
        return self._get_todays_schedule(day).total_minutes_open

    def is_open(self, day: Day) -> bool:
        time = dt.time(minute=day.total_minutes)
        return self._get_todays_schedule(day).is_open(time)

    def iter_minutes(self, day: Day) -> Iterator[int]:
        yield from self._get_todays_schedule(day).iter_minutes()

