import os
import uuid

import pandas as pd
from rich.progress import track

from jafgen.curves import Day
from jafgen.stores.market import Market
from jafgen.stores.stock import Stock
from jafgen.stores.store import Store

T_7AM = 60 * 7
T_8AM = 60 * 8
T_2PM = 60 * 14
T_8PM = 60 * 20


class HoursOfOperation(object):
    def __init__(self, weekday_range, weekend_range):
        self.weekday_range = weekday_range
        self.weekend_range = weekend_range

    def minutes_open(self, date):
        if date.is_weekend:
            return self.weekend_range[1] - self.weekend_range[0]
        else:
            return self.weekday_range[1] - self.weekday_range[0]

    def opens_at(self, date):
        if date.is_weekend:
            return self.weekend_range[0]
        else:
            return self.weekday_range[0]

    def closes_at(self, date):
        if date.is_weekend:
            return self.weekend_range[1]
        else:
            return self.weekday_range[1]

    def is_open(self, date):
        opens_at = self.opens_at(date)
        closes_at = self.closes_at(date)

        dt = date.date.hour * 60 + date.date.minute
        return dt >= opens_at and dt < closes_at

    def iter_minutes(self, date):
        if date.is_weekend:
            start, end = self.weekend_range
        else:
            start, end = self.weekday_range

        for i in range(end - start):
            yield start + i


class Simulation(object):
    def __init__(self, years, prefix):
        self.years = years
        self.scale = 100
        self.prefix = prefix
        self.stores = [
            # id | name | popularity | opened | TAM | tax
            (str(uuid.uuid4()), "Philadelphia", 0.85, 0, 9 * self.scale, 0.06),
            (str(uuid.uuid4()), "Brooklyn", 0.95, 192, 14 * self.scale, 0.04),
            (str(uuid.uuid4()), "Chicago", 0.92, 605, 12 * self.scale, 0.0625),
            (str(uuid.uuid4()), "San Francisco", 0.87, 615, 11 * self.scale, 0.075),
            (str(uuid.uuid4()), "New Orleans", 0.92, 920, 8 * self.scale, 0.04),
        ]

        self.markets = []
        for (
            store_id,
            store_name,
            popularity,
            opened_date,
            market_size,
            tax,
        ) in self.stores:
            market = Market(
                Store(
                    store_id=store_id,
                    name=store_name,
                    base_popularity=popularity,
                    hours_of_operation=HoursOfOperation(
                        weekday_range=(T_7AM, T_8PM),
                        weekend_range=(T_8AM, T_2PM),
                    ),
                    opened_date=Day(opened_date),
                    tax_rate=tax,
                ),
                num_customers=market_size,
            )
            self.markets.append(market)

        self.customers = {}
        self.orders = []
        self.sim_days = 365 * self.years

    def run_simulation(self):
        for i in track(
            range(self.sim_days), description="🥪 Pressing fresh jaffles..."
        ):
            for market in self.markets:
                day = Day(i)
                for order in (o for o in market.sim_day(day) if o is not None):
                    self.orders.append(order)
                    if order.customer.customer_id not in self.customers:
                        self.customers[order.customer.customer_id] = order.customer

    def save_results(self):
        stock: Stock = Stock()
        entities: dict[str, pd.DataFrame] = {
            "customers": pd.DataFrame.from_dict(
                (customer.to_dict() for customer in self.customers.values())
            ),
            "orders": pd.DataFrame.from_dict(
                (order.to_dict() for order in self.orders)
            ),
            "items": pd.DataFrame.from_dict(
                (item.to_dict() for order in self.orders for item in order.items)
            ),
            "stores": pd.DataFrame.from_dict(
                (market.store.to_dict() for market in self.markets)
            ),
            "supplies": pd.DataFrame.from_dict(stock.to_dict()),
        }
        if not os.path.exists("./jaffle-data"):
            os.makedirs("./jaffle-data")
        # save output
        for entity, df in track(
            entities.items(), description="🚚 Delivering jaffles..."
        ):
            df.to_csv(
                f"./jaffle-data/{self.prefix}_{entity}.csv",
                header=df.columns.to_list(),
                index=False,
            )
