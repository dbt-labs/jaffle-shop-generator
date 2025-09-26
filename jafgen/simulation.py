import csv
import os
from typing import Any

from rich.progress import track

from jafgen.customers.customers import Customer, CustomerId
from jafgen.customers.order import Order
from jafgen.customers.tweet import Tweet
from jafgen.flowers.generator import FlowerOrderGenerator
from jafgen.flowers.inventory import FlowerInventory
from jafgen.flowers.models import FlowerOrder, DeliveryInfo
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

class Simulation:
    def __init__(self, years: int, days: int, prefix: str):
        self.years = years
        self.days = days
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

        self.customers: dict[CustomerId, Customer] = {}
        self.orders: list[Order] = []
        self.tweets: list[Tweet] = []

        # Flower shop data
        self.flower_generator = FlowerOrderGenerator(self.scale)
        self.flower_orders: list[FlowerOrder] = []
        self.delivery_info: list[DeliveryInfo] = []

        self.sim_days = 365 * self.years + self.days

    def run_simulation(self):
        for i in track(
            range(self.sim_days), description=f"🥪 Pressing {self.sim_days} days of fresh jaffles and arranging flowers..."
        ):
            day = Day(i)

            # Generate jaffle shop data
            for market in self.markets:
                for order, tweet in market.sim_day(day):
                    if order:
                        self.orders.append(order)
                        if order.customer.id not in self.customers:
                            self.customers[order.customer.id] = order.customer
                    if tweet:
                        self.tweets.append(tweet)

            # Generate flower shop data
            daily_flower_orders, daily_deliveries = self.flower_generator.generate_orders_for_day(day)
            self.flower_orders.extend(daily_flower_orders)
            self.delivery_info.extend(daily_deliveries)

    def save_results(self) -> None:
        stock: Stock = Stock()
        inventory: Inventory = Inventory()
        entities: dict[str, list[dict[str, Any]]] = {
            "customers": [customer.to_dict() for customer in self.customers.values()],
            "orders": [order.to_dict() for order in self.orders],
            "items": [item.to_dict(order_id=str(order.id)) for order in self.orders for item in order.items],
            "stores": [market.store.to_dict() for market in self.markets],
            "supplies": stock.to_dict(),
            "products": inventory.to_dict(),
            "tweets": [tweet.to_dict() for tweet in self.tweets],
            # Flower shop data
            "flowers": FlowerInventory.flowers_to_dict(),
            "flower_arrangements": FlowerInventory.arrangements_to_dict(),
            "delivery_info": [delivery.to_dict() for delivery in self.delivery_info],
            "flower_orders": [order.to_dict() for order in self.flower_orders],
        }

        if not os.path.exists("./jaffle-data"):
            os.makedirs("./jaffle-data")
        for entity, data in track(
            entities.items(), description="🚚 Delivering jaffles and flowers..."
        ):
            if data:
                file = f"./jaffle-data/{self.prefix}_{entity}.csv"
                writer = csv.DictWriter(open(file, "w", newline=""), fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
