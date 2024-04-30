import uuid
from dataclasses import dataclass, field
from typing import NewType

from faker import Faker

from jafgen.time import Day, WeekHoursOfOperation

fake = Faker()

StoreId = NewType("StoreId", uuid.UUID)


@dataclass(frozen=True)
class Store:

    """A single Jaffle Shop store."""

    name: str
    base_popularity: float
    hours_of_operation: WeekHoursOfOperation
    opened_day: Day
    tax_rate: float
    id: StoreId = field(default_factory=lambda: StoreId(fake.uuid4()))

    def p_sell(self, day: Day) -> float:
        """Get the probability of this store selling something on a given day."""
        return self.base_popularity * day.get_effect()

    def is_open(self, day: Day) -> bool:
        """Whether the store is open on a given day."""
        if day.date < self.opened_day.date:
            return False
        return self.hours_of_operation.is_open(day)

    def days_since_open(self, day: Day) -> int:
        """Get the number of days since this store has opened."""
        return day.date_index - self.opened_day.date_index

    def to_dict(self) -> dict[str, str]:
        """Serialize to dict.

        TODO: replace this by serializer class.
        """
        return {
            "id": str(self.id),
            "name": str(self.name),
            "opened_at": str(self.opened_day.date.isoformat()),
            "tax_rate": str(self.tax_rate),
        }
