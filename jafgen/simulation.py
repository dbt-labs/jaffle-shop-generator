import csv
import datetime as dt
import itertools
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import mashumaro.codecs.json as json_codec
from faker import Faker
from mashumaro.mixins.json import DataClassJSONMixin
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

CACHE_DIR = ".jafgen-cache/"
CACHE_AFTER_DAYS = 100

fake = Faker()


@dataclass
class SimulationState(DataClassJSONMixin):

    """Holds the state of a simulation at a certain point in time."""

    day: Day = field(default_factory=lambda: Day(date_index=True))
    customers: dict[CustomerId, Customer] = field(default_factory=dict)
    markets: list[Market] = field(default_factory=list)

    @property
    def random_state(self) -> tuple[Any, ...]:
        """Get the state of the underlying PRNG."""
        return fake.random.getstate()

    @random_state.setter
    def set_random_state(self, s: tuple[Any, ...]) -> None:
        """Set the state of the underlying PRNG."""
        fake.random.setstate(s)

    @classmethod
    def load_from_cache(cls, cache_file: Path) -> "SimulationState":
        """Load the state from a cache file."""
        with open(cache_file, "r") as file:
            blob = file.read()
        inst = json_codec.decode(blob, SimulationState)
        return inst

    def save_to_cache(self) -> Path:
        """Save the current state as a JSON file in cache."""
        os.makedirs(CACHE_DIR, exist_ok=True)

        dumped = json_codec.encode(self, SimulationState)
        iso_date = self.day.date.isoformat()
        file_name = os.path.join(CACHE_DIR, f"jafgen-state-{iso_date}.json")
        with open(file_name, "w") as file:
            file.write(dumped)
        return Path(file_name)

    @classmethod
    def fresh(cls, seed: Optional[int] = None) -> "SimulationState":
        """Pre-populate this state with the correct hardcoded data."""
        if seed is not None:
            Faker.seed(seed)

        inst = SimulationState()
        scale = 100
        stores = [
            # name | popularity | opened | TAM | tax
            ("Philadelphia", 0.85, 0, 9 * scale, 0.06),
            ("Brooklyn", 0.95, 192, 14 * scale, 0.04),
            ("Chicago", 0.92, 605, 12 * scale, 0.0625),
            ("San Francisco", 0.87, 615, 11 * scale, 0.075),
            ("New Orleans", 0.92, 920, 8 * scale, 0.04),
            ("Los Angeles", 0.87, 1107, 8 * scale, 0.08),
        ]
        inst.markets = [
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
            for store_name, popularity, opened_date, market_size, tax in stores
        ]
        return inst


@dataclass(frozen=True)
class SimulationDayData:

    """Holds the new data created every day of a simulation.

    All data stored in this class is used only for exports, and the state of the
    simulation should not depend on this.
    """

    day: Day
    new_customers: list[Customer] = field(default_factory=list)
    new_orders: list[Order] = field(default_factory=list)
    new_tweets: list[Tweet] = field(default_factory=list)


class Simulation:

    """Runs a simulation of multiple days of our customers' lives."""

    def __init__(
        self,
        sim_end: dt.datetime,
        seed: Optional[int] = None,
        cache_file: Optional[Path] = None,
    ):
        """Initialize the simulation."""
        self.sim_end = sim_end

        self.state: SimulationState
        if cache_file is None:
            self.state = SimulationState.fresh(seed)
        else:
            if seed is not None:
                raise ValueError("Cannot specify both seed and cache at the same time.")
            self.state = SimulationState.load_from_cache(cache_file)

        self.sim_start = self.state.day.date

        self.simulated_days: list[SimulationDayData] = []

    def run_simulation(self):
        """Run the simulation."""
        sim_days = (self.sim_end - self.sim_start).days

        for i in track(range(sim_days), description="🥪 Pressing fresh jaffles..."):
            day_data = SimulationDayData(day=Day(i))

            for market in self.state.markets:
                for order, tweet in market.sim_day(day_data.day):
                    if order:
                        day_data.new_orders.append(order)
                        if order.customer.id not in self.state.customers:
                            self.state.customers[order.customer.id] = order.customer
                            day_data.new_customers.append(order.customer)
                    if tweet:
                        day_data.new_tweets.append(tweet)

            self.simulated_days.append(day_data)

            if i % CACHE_AFTER_DAYS == 0 and i > 0:
                self.state.save_to_cache()

    def save_results(
        self, path: str, prefix: str, save_from: dt.datetime = Day.EPOCH
    ) -> None:
        """Save the simulated results to `path`."""
        stock: Stock = Stock()
        inventory: Inventory = Inventory()

        if save_from < self.sim_start:
            raise ValueError(
                "Cannot export from day before the simulation start. ",
                "If you need data before that, either use an earlier state cache "
                "snapshot or no cache at all.",
            )

        discard_days = (save_from - self.sim_start).days
        sim_days = (self.sim_end - self.sim_start).days
        if discard_days >= sim_days:
            discard_days = sim_days
            warnings.warn(
                "save_from is after end of simulation. All data will be empty "
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
                order.to_dict() for day in save_days for order in day.new_orders
            ],
            "items": list(
                itertools.chain.from_iterable(
                    [
                        order.items_to_dict()
                        for day in save_days
                        for order in day.new_orders
                    ]
                )
            ),
            "tweets": [
                tweet.to_dict() for day in save_days for tweet in day.new_tweets
            ],
            # slowly changing dimensions, produce the same everytime
            "stores": [market.store.to_dict() for market in self.state.markets],
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

            file_path = os.path.join(path, f"{prefix}_{entity}.csv")
            with open(file_path, "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
