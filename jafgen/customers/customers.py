import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, NewType

import numpy as np
from faker import Faker
from typing_extensions import override

from jafgen.customers.order import Order
from jafgen.customers.tweet import Tweet
from jafgen.stores.inventory import Inventory
from jafgen.stores.item import Item, ItemType
from jafgen.stores.store import Store
from jafgen.time import Day, Season

fake = Faker()

CustomerId = NewType("CustomerId", uuid.UUID)


@dataclass(frozen=True)
class Customer(ABC):

    """Abstract base class for customers.

    A concrete implementation of `Customer` models the behavior of a customer. This
    includes their probability to buy drinks/food, their probability to tweet about
    their purchase etc.
    """

    store: Store
    id: CustomerId = field(default_factory=lambda: CustomerId(fake.uuid4()))
    name: str = field(default_factory=fake.name)
    favorite_number: int = field(default_factory=lambda: fake.random.randint(1, 100))
    fan_level: int = field(default_factory=lambda: fake.random.randint(1, 5))

    def p_buy(self, day: Day) -> float:
        """Get the probability of buying something on a given day."""
        p_store_sell = self.store.p_sell(day)
        p_buy_persona = self.p_buy_persona(day)
        p_buy_on_day = (p_store_sell * p_buy_persona) ** 0.5
        return p_buy_on_day

    @abstractmethod
    def p_buy_persona(self, day: Day) -> float:
        """Get this customer's innate desire to buy something on a given day."""
        raise NotImplementedError()

    @abstractmethod
    def p_tweet_persona(self, day: Day) -> float:
        """Get this customer's innate desire to tweet about an order on a given day."""
        raise NotImplementedError()

    def p_tweet(self, day: Day) -> float:
        """Get the probability of tweeting about an order on a given day."""
        return self.p_tweet_persona(day)

    def get_order(self, day: Day) -> Order:
        """Get this customer's order on a given day."""
        items = self.get_order_items(day)

        order_minute = self.get_order_minute(day)
        order_day = day.at_minute(order_minute)

        return Order(customer=self, items=items, store=self.store, day=order_day)

    def get_tweet(self, order: Order) -> Tweet:
        """Get this customer's tweet about an order."""
        minutes_delta = int(fake.random.random() * 20)
        tweet_day = order.day.at_minute(order.day.total_minutes + minutes_delta)
        return Tweet(customer=self, order=order, day=tweet_day)

    @abstractmethod
    def get_order_items(self, day: Day) -> list[Item]:
        """Get the list of ordered items on a given day."""
        raise NotImplementedError()

    @abstractmethod
    def get_order_minute(self, day: Day) -> int:
        """Get the time the customer decided to order on a given day."""
        raise NotImplementedError()

    def sim_day(self, day: Day) -> tuple[Order | None, Tweet | None]:
        """Simulate a day in the life of this customer."""
        p_buy = self.p_buy(day)
        p_buy_threshold = np.random.random()
        p_tweet = self.p_tweet(day)
        p_tweet_threshold = np.random.random()
        if p_buy > p_buy_threshold:
            if p_tweet > p_tweet_threshold:
                order = self.get_order(day)
                if self.store.is_open(order.day) and len(order.items) > 0:
                    return order, self.get_tweet(order)
                else:
                    return None, None
            else:
                return self.get_order(day), None
        else:
            return None, None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict.

        TODO: replace this by serializer class.
        """
        return {
            "id": str(self.id),
            "name": str(self.name),
        }


class RemoteWorker(Customer):

    """Pretending to work while staring at their Macbook full of stickers."""

    @override
    def p_buy_persona(self, day: Day):
        buy_propensity = (self.favorite_number / 100) * 0.4
        return 0.001 if day.is_weekend else buy_propensity

    @override
    def p_tweet_persona(self, day: Day):
        return 0.01

    @override
    def get_order_minute(self, day: Day) -> int:
        # most likely to order in the morning
        # exponentially less likely to order in the afternoon
        avg_time = 60 * 7
        order_time = np.random.normal(loc=avg_time, scale=180)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        num_drinks = 1
        food = []

        if fake.random.random() > 0.7:
            num_drinks = 2

        if fake.random.random() > 0.7:
            food = Inventory.get_item_type(ItemType.JAFFLE, 1)

        return Inventory.get_item_type(ItemType.BEVERAGE, num_drinks) + food


class BrunchCrowd(Customer):

    """Do you sell mimosas?."""

    @override
    def p_buy_persona(self, day: Day):
        buy_propensity = 0.2 + (self.favorite_number / 100) * 0.2
        return buy_propensity if day.is_weekend else 0

    @override
    def p_tweet_persona(self, day: Day):
        return 0.8

    @override
    def get_order_minute(self, day: Day) -> int:
        # most likely to order in the early afternoon
        avg_time = 300 + ((self.favorite_number - 50) / 50) * 120
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        num_customers = 1 + int(self.favorite_number / 20)
        return Inventory.get_item_type(
            ItemType.JAFFLE, num_customers
        ) + Inventory.get_item_type(ItemType.BEVERAGE, num_customers)


class Commuter(Customer):

    """The regular, thanks."""

    @override
    def p_buy_persona(self, day: Day):
        buy_propensity = 0.5 + (self.favorite_number / 100) * 0.3
        return 0.001 if day.is_weekend else buy_propensity

    @override
    def p_tweet_persona(self, day: Day):
        return 0.2

    @override
    def get_order_minute(self, day: Day) -> int:
        # most likely to order in the morning
        # exponentially less likely to order in the afternoon
        avg_time = 60
        order_time = np.random.normal(loc=avg_time, scale=30)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        return Inventory.get_item_type(ItemType.BEVERAGE, 1)


class Student(Customer):

    """Coffee might help."""

    @override
    def p_buy_persona(self, day: Day):
        if day.season == Season.SUMMER:
            return 0

        buy_propensity = 0.1 + (self.favorite_number / 100) * 0.4
        return buy_propensity

    @override
    def p_tweet_persona(self, day: Day):
        return 0.8

    @override
    def get_order_minute(self, day: Day) -> int:
        # later is better
        avg_time = 9 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        food = []
        if fake.random.random() > 0.5:
            food = Inventory.get_item_type(ItemType.JAFFLE, 1)

        return Inventory.get_item_type(ItemType.BEVERAGE, 1) + food


class Casuals(Customer):

    """Just popping in."""

    @override
    def p_buy_persona(self, day: Day):
        return 0.1

    @override
    def p_tweet_persona(self, day: Day):
        return 0.1

    @override
    def get_order_minute(self, day: Day) -> int:
        avg_time = 5 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        num_drinks = int(fake.random.random() * 10 / 3)
        num_food = int(fake.random.random() * 10 / 3)
        return Inventory.get_item_type(
            ItemType.BEVERAGE, num_drinks
        ) + Inventory.get_item_type(ItemType.JAFFLE, num_food)


class HealthNut(Customer):

    """A light beverage in the sunshine as a treat."""

    @override
    def p_buy_persona(self, day: Day):
        if day.season == Season.SUMMER:
            buy_propensity = 0.1 + (self.favorite_number / 100) * 0.4
            return buy_propensity
        return 0.2

    @override
    def p_tweet_persona(self, day: Day):
        return 0.6

    @override
    def get_order_minute(self, day: Day) -> int:
        avg_time = 5 * 60
        order_time = np.random.normal(loc=avg_time, scale=120)
        return max(0, int(order_time))

    @override
    def get_order_items(self, day: Day):
        return Inventory.get_item_type(ItemType.BEVERAGE, 1)
