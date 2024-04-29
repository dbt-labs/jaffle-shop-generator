import datetime
import uuid
from jafgen.stores.store import StoreId, Store
from jafgen.customers.customers import (
    Customer,
    RemoteWorker,
    BrunchCrowd,
    HealthNut,
    Commuter,
    Casuals,
    Student,
)
from jafgen.time import Day, WeekHoursOfOperation, DayHoursOfOperation

T_7AM = 60 * 7
T_8AM = 60 * 8
T_3PM = 60 * 15
T_8PM = 60 * 20


def test_tweets():
    """Test that tweets only come after orders and in the range of 20 minutes after."""

    store = Store(
        store_id=StoreId(uuid.uuid4()),
        name="Testylvania",
        base_popularity=0.85,
        hours_of_operation=WeekHoursOfOperation(
            week_days=DayHoursOfOperation(opens_at=T_7AM, closes_at=T_8PM),
            weekends=DayHoursOfOperation(opens_at=T_8AM, closes_at=T_3PM),
        ),
        opened_day=0,
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
