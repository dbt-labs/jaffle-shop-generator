import datetime
from jafgen.stores.store import Store
from jafgen.customers.customers import (
    RemoteWorker,
    BrunchCrowd,
    HealthNut,
    Commuter,
    Casuals,
    Student,
)
from jafgen.curves import Day
from jafgen.simulation import HoursOfOperation

T_7AM = 60 * 7
T_8AM = 60 * 8
T_3PM = 60 * 15
T_8PM = 60 * 20


def test_tweets():
    """Test that tweets only come after orders and in the range of 20 minutes after."""

    store = Store(
        str(1),
        "Testylvania",
        0.85,
        HoursOfOperation(
            weekday_range=(T_7AM, T_8PM),
            weekend_range=(T_8AM, T_3PM),
        ),
        0,
        0.0659123,
    )
    customers = []
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
