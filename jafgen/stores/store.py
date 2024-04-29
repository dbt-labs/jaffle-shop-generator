import daytime
from dataclasses import dataclass
from typing import NewType

from jafgen.time import Day, WeekHoursOfOperation 

StoreId = NewType("StoreId", str)

@dataclass(frozen=True)
class Store:
    store_id: StoreId 
    name: str 
    base_popularity: float 
    hours_of_operation: WeekHoursOfOperation 
    opened_day: Day 
    tax_rate: float

    def p_buy(self, day: Day) -> float:
        return self.base_popularity * day.get_effect() 

    def minutes_open(self, day: Day) -> int:
        return self.hours_of_operation.minutes_open(day)

    def iter_minutes_open(self, day: Day) -> Iterator[int]:
        yield from self.hours_of_operation.iter_minutes(day)

    def is_open(self, day: Day):
        return day.date >= self.opened_date.date

    def is_open_at(self, day: Day) -> bool:
        return self.hours_of_operation.is_open(day)

    def days_since_open(self, day: Day) -> int:
        return day.date_index - self.opened_date.date_index

    def opens_at(self, day: Day):
        return self.hours_of_operation.opens_at(day)

    def closes_at(self, day: Day):
        return self.hours_of_operation.closes_at(day)

    def to_dict(self) -> dict[str, str]:
        return {
            "id": str(self.store_id),
            "name": str(self.name),
            "opened_at": str(self.opened_day.date.isoformat()),
            "tax_rate": str(self.tax_rate),
        }
