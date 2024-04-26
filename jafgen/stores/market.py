import random

import numpy as np

from jafgen.customers.customers import (
    BrunchCrowd,
    Casuals,
    Commuter,
    RemoteWorker,
    Student,
    HealthNut,
)


class Market(object):
    PersonaMix = [
        (Commuter, 0.25),
        (RemoteWorker, 0.25),
        (BrunchCrowd, 0.1),
        (Student, 0.2),
        (Casuals, 0.1),
        (HealthNut, 0.1),
    ]

    def __init__(self, store, num_customers, days_to_penetration=365):
        self.store = store
        self.num_customers = num_customers
        self.days_to_penetration = days_to_penetration

        self.addressable_customers = []

        for Persona, weight in self.PersonaMix:
            num_customers = int(weight * self.num_customers)
            for i in range(num_customers):
                self.addressable_customers.append(Persona(store))

        random.shuffle(self.addressable_customers)

        self.active_customers = []

    def sim_day(self, day):
        days_since_open = self.store.days_since_open(day)
        if days_since_open < 0:
            yield None
            return
        elif days_since_open < 7:
            pct_penetration = min(days_since_open / self.days_to_penetration, 1)
            market_penetration = min(np.log(1.2 + pct_penetration * (np.e - 1.2)), 1)
        else:
            pct_penetration = min(days_since_open / self.days_to_penetration, 1)
            market_penetration = min(np.log(1 + pct_penetration * (np.e - 1)), 1)

        num_desired_customers = market_penetration * len(self.addressable_customers)
        customers_to_add = int(num_desired_customers - len(self.active_customers))

        for i in range(customers_to_add):
            customer = self.addressable_customers.pop()
            self.active_customers.append(customer)

        for customer in self.active_customers:
            order, tweet = customer.sim_day(day)
            yield order, tweet
