import datetime
from abc import ABC, abstractmethod
import numpy as np


class Curve(ABC):
    @property
    @abstractmethod
    def Domain(self):
        raise NotImplementedError

    @abstractmethod
    def TranslateDomain(self, date):
        raise NotImplementedError

    @abstractmethod
    def Expr(self, x):
        raise NotImplementedError

    @classmethod
    def eval(cls, date):
        instance = cls()
        domain_value = instance.TranslateDomain(date)
        domain_index = domain_value % len(instance.Domain)
        translated_value = instance.Domain[domain_index]
        return instance.Expr(translated_value)


class AnnualCurve(Curve):
    @property
    def Domain(self):
        return np.linspace(0, 2 * np.pi, 365)

    def TranslateDomain(self, date):
        return date.timetuple().tm_yday

    def Expr(self, x):
        return (np.cos(x) + 1) / 10 + 0.8


class WeekendCurve(Curve):
    @property
    def Domain(self):
        return tuple(range(6))

    def TranslateDomain(self, date):
        return date.weekday() - 1

    def Expr(self, x):
        if x >= 6:
            return 0.6
        else:
            return 1.0


class GrowthCurve(Curve):
    @property
    def Domain(self):
        return tuple(range(500))

    def TranslateDomain(self, date):
        return (date.year - 2016) * 12 + date.month

    def Expr(self, x):
        # ~ aim for ~20% growth/year
        return 1 + (x / 12) * 0.2


class Day(object):
    EPOCH = datetime.datetime(year=2018, month=9, day=1)
    SEASONAL_MONTHLY_CURVE = AnnualCurve()
    WEEKEND_CURVE = WeekendCurve()
    GROWTH_CURVE = GrowthCurve()

    def __init__(self, date_index, minutes=0):
        self.date_index = date_index
        self.date = self.EPOCH + datetime.timedelta(days=date_index, minutes=minutes)
        self.effects = [
            self.SEASONAL_MONTHLY_CURVE.eval(self.date),
            self.WEEKEND_CURVE.eval(self.date),
            self.GROWTH_CURVE.eval(self.date),
        ]

    def at_minute(self, minutes):
        return Day(self.date_index, minutes=minutes)

    def get_effect(self):
        total = 1
        for effect in self.effects:
            total = total * effect
        return total

        # weekend_effect = 0.8 if date.is_weekend else 1
        # summer_effect = 0.7 if date.season == 'summer' else 1

    @property
    def day_of_week(self):
        return self.date.weekday()

    @property
    def is_weekend(self):
        # 5 + 6 are weekends
        return self.date.weekday() >= 5

    @property
    def season(self):
        month_no = self.date.month
        day_no = self.date.day

        if month_no in (1, 2) or (month_no == 3 and day_no < 21):
            return "winter"
        elif month_no in (3, 4, 5) or (month_no == 6 and day_no < 21):
            return "spring"
        elif month_no in (6, 7, 8) or (month_no == 9 and day_no < 21):
            return "summer"
        elif month_no in (9, 10, 11) or (month_no == 12 and day_no < 21):
            return "fall"
        else:
            return "winter"
