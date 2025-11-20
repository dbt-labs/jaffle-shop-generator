import datetime as dt
import uuid
from dataclasses import dataclass, field
from typing import Iterator, NewType

from faker import Faker

from jafgen.time import Day, WeekHoursOfOperation

fake = Faker()

StoreId = NewType("StoreId", uuid.UUID)


@dataclass(frozen=True)
class Store:
    name: str
    base_popularity: float
    hours_of_operation: WeekHoursOfOperation
    opened_day: Day
    tax_rate: float
    id: StoreId = field(default_factory=lambda: StoreId(fake.uuid4()))  # type: ignore[arg-type]

    def p_buy(self, day: Day) -> float:
        """Calculate purchase probability for the store on a given day."""
        return self.base_popularity * day.get_effect()

    def minutes_open(self, day: Day) -> int:
        """Get total minutes the store is open on a given day."""
        return self.hours_of_operation.total_minutes_open(day)

    def iter_minutes_open(self, day: Day) -> Iterator[int]:
        """Iterate over all minutes the store is open on a given day."""
        yield from self.hours_of_operation.iter_minutes(day)

    def is_open(self, day: Day) -> bool:
        """Check if the store has opened by the given day."""
        return day.date >= self.opened_day.date

    def is_open_at(self, day: Day) -> bool:
        """Check if the store is open at the specific time on the given day."""
        return self.hours_of_operation.is_open(day)

    def days_since_open(self, day: Day) -> int:
        """Calculate days since the store opened."""
        return day.date_index - self.opened_day.date_index

    def opens_at(self, day: Day) -> dt.time:
        """Get the opening time for the given day."""
        return self.hours_of_operation.opens_at(day)

    def closes_at(self, day: Day) -> dt.time:
        """Get the closing time for the given day."""
        return self.hours_of_operation.closes_at(day)

    def to_dict(self) -> dict[str, str]:
        """Convert store to dictionary representation."""
        return {
            "id": str(self.id),
            "name": str(self.name),
            "opened_at": str(self.opened_day.date.isoformat()),
            "tax_rate": str(self.tax_rate),
        }
