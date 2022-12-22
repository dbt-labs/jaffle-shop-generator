import random
import uuid

import numpy as np
from faker import Faker

from jafgen.customers.order import Order
from jafgen.stores.inventory import Inventory

fake = Faker()
Faker.seed(123456789)


class Customer(object):
    def __init__(self, store):
        self.customer_id = str(uuid.uuid4())
        self.store = store
        self.name = fake.name()
        self.favorite_number = int(np.random.rand() * 100)

    def p_buy_season(self, day):
        return self.store.p_buy(day)

    def p_buy(self, day):
        p_buy_season = self.p_buy_season(day)
        p_buy_persona = self.p_buy_persona(day)
        p_buy_on_day = (p_buy_season * p_buy_persona) ** 0.5
        return p_buy_on_day

    def get_order(self, day):
        items = self.get_order_items(day)
        order_time_delta = self.get_order_time(day)

        order_time = day.at_minute(order_time_delta + self.store.opens_at(day))
        if not self.store.is_open_at(order_time):
            return None

        return Order(self, items, self.store, order_time)

    def get_order_items(self, day):
        raise NotImplementedError()

    def get_order_time(self, store, day):
        raise NotImplementedError()

    def p_buy_persona(self, day):
        raise NotImplementedError()

    def sim_day(self, day):
        p_buy = self.p_buy(day)
        p_buy_threshold = np.random.random()

        if p_buy_threshold < p_buy:
            return self.get_order(day)
        else:
            return None

    def to_dict(self):
        return {
            "id": self.customer_id,
            "name": self.name,
        }


class RemoteWorker(Customer):
    "This person works from a coffee shop"

    def p_buy_persona(self, day):
        buy_propensity = (self.favorite_number / 100) * 0.4
        return 0.001 if day.is_weekend else buy_propensity

    def get_order_time(self, day):
        # most likely to order in the morning
        # exponentially less likely to order in the afternoon
        avg_time = 420
        order_time = np.random.normal(loc=avg_time, scale=180)
        return max(0, int(order_time))

    def get_order_items(self, day):
        num_drinks = 1
        food = []

        if random.random() > 0.7:
            num_drinks = 2

        if random.random() > 0.7:
            food = Inventory.get_food(1)

        return Inventory.get_drink(num_drinks) + food


class BrunchCrowd(Customer):
    "Do you sell mimosas?"

    def p_buy_persona(self, day):
        buy_propensity = 0.2 + (self.favorite_number / 100) * 0.2
        return buy_propensity if day.is_weekend else 0

    def get_order_time(self, day):
        # most likely to order in the early afternoon
        avg_time = 300 + ((self.favorite_number - 50) / 50) * 120
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day):
        num_customers = 1 + int(self.favorite_number / 20)
        return Inventory.get_drink(num_customers) + Inventory.get_food(num_customers)


class Commuter(Customer):
    "the regular, thanks"

    def p_buy_persona(self, day):
        buy_propensity = 0.5 + (self.favorite_number / 100) * 0.3
        return 0.001 if day.is_weekend else buy_propensity

    def get_order_time(self, day):
        # most likely to order in the morning
        # exponentially less likely to order in the afternoon
        avg_time = 60
        order_time = np.random.normal(loc=avg_time, scale=30)
        return max(0, int(order_time))

    def get_order_items(self, day):
        return Inventory.get_drink(1)


class Student(Customer):
    "coffee might help"

    def p_buy_persona(self, day):
        if day.season == "summer":
            return 0
        else:
            buy_propensity = 0.1 + (self.favorite_number / 100) * 0.4
            return buy_propensity

    def get_order_time(self, day):
        # later is better
        avg_time = 9 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day):
        food = []
        if random.random() > 0.5:
            food = Inventory.get_food(1)

        return Inventory.get_drink(1) + food


class Casuals(Customer):
    "just popping in"

    def p_buy_persona(self, day):
        return 0.1

    def get_order_time(self, day):
        avg_time = 5 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    def get_order_items(self, day):
        num_drinks = int(random.random() * 10 / 3)
        num_food = int(random.random() * 10 / 3)
        return Inventory.get_drink(num_drinks) + Inventory.get_food(num_food)
