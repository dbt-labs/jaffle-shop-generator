import uuid

import pandas as pd
from tqdm import tqdm

from curves import Day
from stores.inventory import Inventory
from stores.market import Market
from stores.stock import Stock
from stores.store import Store

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


scale = 100
stores = [
    # id | name | popularity | opened | TAM | tax
    (str(uuid.uuid4()), "Philadelphia", 0.85, 0, 9 * scale, 0.06),
    (str(uuid.uuid4()), "Brooklyn", 0.95, 192, 14 * scale, 0.04),
    (str(uuid.uuid4()), "Chicago", 0.92, 605, 12 * scale, 0.0625),
    (str(uuid.uuid4()), "San Francisco", 0.87, 615, 11 * scale, 0.075),
    (str(uuid.uuid4()), "New Orleans", 0.92, 920, 8 * scale, 0.04),
]

markets = []
for store_id, store_name, popularity, opened_date, market_size, tax in stores:
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
    markets.append(market)


customers = {}
orders = []

sim_days = 365 * 1
for i in tqdm(range(sim_days), desc="[SIM]"):

    for market in markets:
        store = market.store.name
        day = Day(i)
        for order in (o for o in market.sim_day(day) if o is not None):
            orders.append(order)
            if order.customer.customer_id not in customers:
                customers[order.customer.customer_id] = order.customer


# ask Drew about what the heck is up with the to_dict stuff
person = customers[list(customers.keys())[0]]
df_customers = pd.DataFrame.from_dict(customer.to_dict() for customer in customers.values())
df_orders = pd.DataFrame.from_dict(order.to_dict() for order in orders)
df_items = pd.DataFrame.from_dict(item.to_dict() for order in orders for item in order.items)
df_stores = pd.DataFrame.from_dict(market.store.to_dict() for market in markets)
df_products = pd.DataFrame.from_dict(Inventory.to_dict())
df_supplies = pd.DataFrame.from_dict(Stock.to_dict())

df_customers.to_csv("./data/customers.csv")
df_orders.to_csv("./data/orders.csv")
df_items.to_csv("./data/items.csv")
df_stores.to_csv("./data/stores.csv")
df_products.to_csv("./data/products.csv")
df_supplies.to_csv("./data/supplies.csv")
