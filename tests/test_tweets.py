import datetime

from jafgen.customers.customers import (
    BrunchCrowd,
    Casuals,
    Commuter,
    Customer,
    HealthNut,
    RemoteWorker,
    Student,
)
from jafgen.stores.store import Store
from jafgen.time import Day, DayHoursOfOperation, WeekHoursOfOperation

T_7AM = datetime.time(minute=60 * 7)
T_8AM = datetime.time(minute=60 * 8)
T_3PM = datetime.time(minute=60 * 15)
T_8PM = datetime.time(minute=60 * 20)


def test_tweets():
    """Test that tweets only come after orders and in the range of 20 minutes after."""
    store = Store(
        name="Testylvania",
        base_popularity=0.85,
        hours_of_operation=WeekHoursOfOperation(
            week_days=DayHoursOfOperation(opens_at=T_7AM, closes_at=T_8PM),
            weekends=DayHoursOfOperation(opens_at=T_8AM, closes_at=T_3PM),
        ),
        opened_day=Day(date_index=0, minutes=0),
        tax_rate=0.0659123,
    )
    customers: list[Customer] = []
    personas = [RemoteWorker, BrunchCrowd, HealthNut, Commuter, Casuals, Student]
    for i in range(100):
        customers.append(personas[i % len(personas)](store))

    for i in range(100):
        day = Day(i)
        for customer in customers:
            order, tweet = customer.sim_day(day)
            if tweet:
                assert tweet.customer == customer
                assert tweet.order == order
                assert (
                    tweet.tweeted_at
                    <= tweet.order.order_time.date + datetime.timedelta(minutes=20)
                )
            if not order:
                assert not tweet
