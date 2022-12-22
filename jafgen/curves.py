import datetime

import numpy as np


class Curve:
    @classmethod
    def eval(cls, date):
        x = cls.TranslateDomain(date)
        x_mod = x % len(cls.Domain)
        x_translated = cls.Domain[x_mod]
        return cls.Expr(x_translated)


class AnnualCurve(Curve):
    Domain = np.linspace(0, 2 * np.pi, 365)
    TranslateDomain = lambda date: date.timetuple().tm_yday
    Expr = lambda x: (np.cos(x) + 1) / 10 + 0.8


class WeekendCurve(Curve):
    Domain = tuple(range(6))
    TranslateDomain = lambda date: date.weekday() - 1
    Expr = lambda x: 0.6 if x >= 6 else 1


class GrowthCurve(Curve):
    Domain = tuple(range(500))
    TranslateDomain = lambda date: (date.year - 2016) * 12 + date.month
    # ~ aim for ~20% growth/year
    Expr = lambda x: 1 + (x / 12) * 0.2


class Day(object):
    EPOCH = datetime.datetime(year=2016, month=9, day=1)
    SEASONAL_MONTHLY_CURVE = AnnualCurve()
    WEEKEND_CURVE = WeekendCurve()
    GROWTH_CURVE = GrowthCurve()

    def __init__(self, date_index, minutes=0):
        self.date_index = date_index
        self.date = self.EPOCH + datetime.timedelta(days=date_index, minutes=minutes)

        self.day_of_week = self._get_day_of_week(self.date)
        self.is_weekend = self._is_weekend(self.date)
        self.season = self._get_season(self.date)

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

    def _get_day_of_week(self, date):
        return date.weekday()

    def _is_weekend(self, date):
        # 5 + 6 are weekends
        return date.weekday() >= 5

    def _get_season(self, date):
        month_no = date.month
        day_no = date.day

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
