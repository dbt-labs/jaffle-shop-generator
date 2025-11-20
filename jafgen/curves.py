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
        """Return the domain array for the curve."""
        raise NotImplementedError

    @abstractmethod
    def TranslateDomain(self, date: datetime.date) -> int:
        """Translate a date to a domain index."""
        raise NotImplementedError

    @abstractmethod
    def Expr(self, x: float) -> float:
        """Evaluate the curve expression at a given point."""
        raise NotImplementedError

    @classmethod
    def eval(cls, date: datetime.date) -> float:
        """Evaluate the curve for a given date."""
        instance = cls()
        domain_value = instance.TranslateDomain(date)
        domain_index = domain_value % len(instance.Domain)
        translated_value = instance.Domain[domain_index]
        return instance.Expr(translated_value)


class AnnualCurve(Curve):
    @property
    @override
    def Domain(self) -> NumberArr:
        """Return annual domain spanning 365 days."""
        return np.linspace(0, 2 * np.pi, 365, dtype=np.float64)

    @override
    def TranslateDomain(self, date: datetime.date) -> int:
        """Translate date to day of year."""
        return date.timetuple().tm_yday

    @override
    def Expr(self, x: float) -> float:
        """Evaluate annual cosine curve."""
        return (np.cos(x) + 1) / 10 + 0.8  # type: ignore[no-any-return]


class WeekendCurve(Curve):
    @property
    def Domain(self) -> NumberArr:
        """Return weekly domain for 6 days."""
        return np.array(range(6), dtype=np.float64)

    def TranslateDomain(self, date: datetime.date) -> int:
        """Translate date to weekday index."""
        return date.weekday() - 1

    def Expr(self, x: float) -> float:
        """Evaluate weekend curve with reduced weekend values."""
        if x >= 6:
            return 0.6
        else:
            return 1.0


class GrowthCurve(Curve):
    @property
    def Domain(self) -> NumberArr:
        """Return growth domain spanning 500 months."""
        return np.arange(500, dtype=np.int32)

    def TranslateDomain(self, date: datetime.date) -> int:
        """Translate date to months since 2016."""
        return (date.year - 2016) * 12 + date.month

    def Expr(self, x: float) -> float:
        """Evaluate growth curve with 20% annual growth."""
        # ~ aim for ~20% growth/year
        return 1 + (x / 12) * 0.2
