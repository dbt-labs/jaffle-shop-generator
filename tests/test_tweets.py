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
from jafgen.time import Day


def test_tweets(default_store: Store):
    """Test that tweets only come after orders and in the range of 20 minutes after."""
    customers: list[Customer] = []
    personas = [RemoteWorker, BrunchCrowd, HealthNut, Commuter, Casuals, Student]
    for i in range(100):
        customers.append(personas[i % len(personas)](default_store))

    for i in range(100):
        day = Day(i)
        for customer in customers:
            order, tweet = customer.sim_day(day)
            if tweet:
                assert tweet.customer == customer
                assert tweet.order == order
                assert (
                    tweet.day.date
                    <= tweet.order.day.at_minute(
                        tweet.order.day.total_minutes + 20
                    ).date
                )
            if not order:
                assert not tweet
