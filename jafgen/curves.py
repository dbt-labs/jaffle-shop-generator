import datetime
from abc import ABC, abstractmethod

import numpy as np
import numpy.typing as npt
from typing_extensions import override

NumberArr = npt.NDArray[np.float64] | npt.NDArray[np.int32]


class Curve(ABC):

    """Base class for numerical curves that produce trends."""

    @property
    @abstractmethod
    def Domain(self) -> NumberArr:
        """The function's domain, a.k.a the x-axis."""
        raise NotImplementedError

    @abstractmethod
    def TranslateDomain(self, date: datetime.date) -> int:
        """Translate the domain for a given date.

        This is useful for repeating series, like for making every
        "sunday" on a weekly trend have the same value.
        """
        raise NotImplementedError

    @abstractmethod
    def Expr(self, x: float) -> float:
        """Get `y` in `y=f(x)` where `f` is the trend."""
        raise NotImplementedError

    @classmethod
    def eval(cls, date: datetime.date) -> float:
        """Evaluate the curve's value (y-axis) on a given day."""
        instance = cls()
        domain_value = instance.TranslateDomain(date)
        domain_index = domain_value % len(instance.Domain)
        translated_value = instance.Domain[domain_index]
        return instance.Expr(translated_value)


class AnnualCurve(Curve):

    """Produces trends over a year."""

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

    """Produces trends over a weekend."""

    @property
    @override
    def Domain(self) -> NumberArr:
        return np.array(range(6), dtype=np.float64)

    @override
    def TranslateDomain(self, date: datetime.date) -> int:
        return date.weekday() - 1

    @override
    def Expr(self, x: float):
        if x >= 6:
            return 0.6
        else:
            return 1.0


class GrowthCurve(Curve):

    """Produces a growth over time trend."""

    @property
    @override
    def Domain(self) -> NumberArr:
        return np.arange(500, dtype=np.int32)

    @override
    def TranslateDomain(self, date: datetime.date) -> int:
        return (date.year - 2016) * 12 + date.month

    @override
    def Expr(self, x: float) -> float:
        # ~ aim for ~20% growth/year
        return 1 + (x / 12) * 0.2
