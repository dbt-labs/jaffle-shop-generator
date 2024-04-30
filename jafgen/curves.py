import datetime
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as npt
from typing_extensions import override

NumberArr = npt.NDArray[np.float64] | npt.NDArray[np.int32]



class Curve(ABC):
    @property
    @abstractmethod
    def Domain(self) -> NumberArr:
        raise NotImplementedError

    @abstractmethod
    def TranslateDomain(self, date: datetime.date) -> int:
        raise NotImplementedError

    @abstractmethod
    def Expr(self, x: float) -> float:
        raise NotImplementedError

    @classmethod
    def eval(cls, date: datetime.date) -> float:
        instance = cls()
        domain_value = instance.TranslateDomain(date)
        domain_index = domain_value % len(instance.Domain)
        translated_value = instance.Domain[domain_index]
        return instance.Expr(translated_value)


class AnnualCurve(Curve):
    @property
    @override
    def Domain(self) -> NumberArr:
        return np.linspace(0, 2 * np.pi, 365, dtype=np.float64)

    @override
    def TranslateDomain(self, date: datetime.date) -> int:
        return date.timetuple().tm_yday

    @override
    def Expr(self, x: float) -> float:
        return (np.cos(x) + 1) / 10 + 0.8


class WeekendCurve(Curve):
    @property
    def Domain(self) -> NumberArr:
        return np.array(range(6), dtype=np.float64)

    def TranslateDomain(self, date: datetime.date) -> int:
        return date.weekday() - 1

    def Expr(self, x: float):
        if x >= 6:
            return 0.6
        else:
            return 1.0


class GrowthCurve(Curve):
    @property
    def Domain(self) -> NumberArr:
        return np.arange(500, dtype=np.int32)

    def TranslateDomain(self, date: datetime.date) -> int:
        return (date.year - 2016) * 12 + date.month

    def Expr(self, x: float) -> float:
        # ~ aim for ~20% growth/year
        return 1 + (x / 12) * 0.2

