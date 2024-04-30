import pytest

from jafgen.stores.store import Store
from jafgen.time import (
    Day,
    DayHoursOfOperation,
    WeekHoursOfOperation,
    time_from_total_minutes,
)

T_7AM = time_from_total_minutes(60 * 7)
T_8AM = time_from_total_minutes(60 * 8)
T_3PM = time_from_total_minutes(60 * 15)
T_8PM = time_from_total_minutes(60 * 20)


@pytest.fixture
def default_store() -> Store:
    """Return a pre-initialized store that can be used for tests."""
    return Store(
        name="Testylvania",
        base_popularity=0.85,
        hours_of_operation=WeekHoursOfOperation(
            week_days=DayHoursOfOperation(opens_at=T_7AM, closes_at=T_8PM),
            weekends=DayHoursOfOperation(opens_at=T_8AM, closes_at=T_3PM),
        ),
        opened_day=Day(date_index=0, minutes=0),
        tax_rate=0.0659123,
    )
