import random
from typing import Any

from jafgen.stores.item import Item


class Inventory(object):
    inventory: dict[Any, Any] = {}

    @classmethod
    def update(cls, inventory_list):
        cls.inventory["jaffle"] = []
        cls.inventory["beverage"] = []
        for item in inventory_list:
            ttype = item.type
            cls.inventory[ttype].append(item)

    @classmethod
    def get_food(cls, count=1):
        return [random.choice(cls.inventory["jaffle"]) for i in range(count)]

    @classmethod
    def get_drink(cls, count=1):
        return [random.choice(cls.inventory["beverage"]) for i in range(count)]

    @classmethod
    def to_dict(cls) -> list[dict[str, Any]]:
        all_items = []
        for key in cls.inventory:
            all_items += [item.to_dict() for item in cls.inventory[key]]
        return all_items


Inventory.update(
    [
        Item(
            sku="JAF-001",
            name="nutellaphone who dis?",
            description="nutella and banana jaffle",
            type="jaffle",
            price=11,
        ),
        Item(
            sku="JAF-002",
            name="doctor stew",
            description="house-made beef stew jaffle",
            type="jaffle",
            price=11,
        ),
        Item(
            sku="JAF-003",
            name="the krautback",
            description="lamb and pork bratwurst with house-pickled cabbage sauerkraut and mustard",
            type="jaffle",
            price=12,
        ),
        Item(
            sku="JAF-004",
            name="flame impala",
            description="pulled pork and pineapple al pastor marinated in ghost pepper sauce, kevin parker's favorite! ",
            type="jaffle",
            price=14,
        ),
        Item(
            sku="JAF-005",
            name="mel-bun",
            description="melon and minced beef bao, in a jaffle, savory and sweet",
            type="jaffle",
            price=12,
        ),
        Item(
            sku="BEV-001",
            name="tangaroo",
            description="mango and tangerine smoothie",
            type="beverage",
            price=6,
        ),
        Item(
            sku="BEV-002",
            name="chai and mighty",
            description="oatmilk chai latte with protein boost",
            type="beverage",
            price=5,
        ),
        Item(
            sku="BEV-003",
            name="vanilla ice",
            description="iced coffee with house-made french vanilla syrup",
            type="beverage",
            price=6,
        ),
        Item(
            sku="BEV-004",
            name="for richer or pourover ",
            description="daily selection of single estate beans for a delicious hot pourover",
            type="beverage",
            price=7,
        ),
        Item(
            sku="BEV-005",
            name="adele-ade",
            description="a kiwi and lime agua fresca, hello from the other side of thirst",
            type="beverage",
            price=4,
        ),
    ]
)
