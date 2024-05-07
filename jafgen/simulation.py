import csv
import datetime as dt
import itertools
import os
from dataclasses import dataclass, field
from typing import Any
import warnings

from rich.progress import track

from jafgen.customers.customers import Customer, CustomerId
from jafgen.customers.order import Order
from jafgen.customers.tweet import Tweet
from jafgen.stores.inventory import Inventory
from jafgen.stores.market import Market
from jafgen.stores.stock import Stock
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

@dataclass(frozen=True)
class SimulationDayData:

    """Holds the new data created every day of a simulation."""

    day: Day
    new_customers: list[Customer] = field(default_factory=list)
    new_orders: list[Order] = field(default_factory=list)
    new_tweets: list[Tweet] = field(default_factory=list)



class Simulation:

    """Runs a simulation of multiple days of our customers' lives."""

    def __init__(self, days: int, prefix: str):
        """Initialize the simulation."""
        self.sim_days = days
        self.scale = 100
        self.prefix = prefix
        self.stores = [
            # name | popularity | opened | TAM | tax
            ("Philadelphia", 0.85, 0, 9 * self.scale, 0.06),
            ("Brooklyn", 0.95, 192, 14 * self.scale, 0.04),
            ("Chicago", 0.92, 605, 12 * self.scale, 0.0625),
            ("San Francisco", 0.87, 615, 11 * self.scale, 0.075),
            ("New Orleans", 0.92, 920, 8 * self.scale, 0.04),
            ("Los Angeles", 0.87, 1107, 8 * self.scale, 0.08),
        ]

        self.markets: list[Market] = [
            Market(
                Store(
                    name=store_name,
                    base_popularity=popularity,
                    hours_of_operation=WeekHoursOfOperation(
                        week_days=DayHoursOfOperation(opens_at=T_7AM, closes_at=T_8PM),
                        weekends=DayHoursOfOperation(opens_at=T_8AM, closes_at=T_3PM),
                    ),
                    opened_day=Day(opened_date),
                    tax_rate=tax,
                ),
                num_customers=market_size,
            )
            for store_name, popularity, opened_date, market_size, tax in self.stores
        ]

        self.simulated_days: list[SimulationDayData] = []
        self.customers: dict[CustomerId, Customer] = {}

    def run_simulation(self):
        """Run the simulation."""
        for i in track(
            range(self.sim_days), description="🥪 Pressing fresh jaffles..."
        ):
            day_data = SimulationDayData(day=Day(i))

            for market in self.markets:
                for order, tweet in market.sim_day(day_data.day):
                    if order:
                        day_data.new_orders.append(order)
                        if order.customer.id not in self.customers:
                            self.customers[order.customer.id] = order.customer
                            day_data.new_customers.append(order.customer)
                    if tweet:
                        day_data.new_tweets.append(tweet)

            self.simulated_days.append(day_data)

    def save_results(self, path: str, start_from: dt.datetime = Day.EPOCH) -> None:
        """Save the simulated results to `path`."""
        stock: Stock = Stock()
        inventory: Inventory = Inventory()

        if start_from < Day.EPOCH:
            raise ValueError("Cannot start from day before the EPOCH.")

        discard_days = (start_from - Day.EPOCH).days
        if discard_days >= self.sim_days:
            discard_days = self.sim_days
            warnings.warn(
                "start_from is after end of simulation. All data will be empty "
                "except for slowly changing dimensions."
            )

        save_days = self.simulated_days[discard_days:]

        entities: dict[str, list[dict[str, Any]]] = {
            # new data every day, produce only requested
            "customers": [
                customer.to_dict()
                for day in save_days
                for customer in day.new_customers
            ],
            "orders": [
                order.to_dict()
                for day in save_days
                for order in day.new_orders
            ],
            "items": list(itertools.chain.from_iterable([
                order.items_to_dict()
                for day in save_days
                for order in day.new_orders
            ])),
            "tweets": [
                tweet.to_dict()
                for day in save_days
                for tweet in day.new_tweets
            ],

            # slowly changing dimensions, produce the same everytime
            "stores": [market.store.to_dict() for market in self.markets],
            "supplies": stock.to_dict(),
            "products": inventory.to_dict(),
        }

        if not os.path.exists(path):
            os.makedirs(path)
        for entity, data in track(
            entities.items(), description="🚚 Delivering jaffles..."
        ):
            if len(data) == 0:
                continue

            file_path = os.path.join(path, f"{self.prefix}_{entity}.csv")
            with open(
                file_path, "w", newline=""
            ) as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
