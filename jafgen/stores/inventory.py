from typing import Any

from faker import Faker

from jafgen.stores.product import Product, ProductType
from jafgen.stores.supply import StorageKeepingUnit as SKU

fake = Faker()


class Inventory:
    inventory: dict[ProductType, list[Product]] = {}

    @classmethod
    def update(cls, inventory_list: list[Product]):
        cls.inventory[ProductType.JAFFLE] = []
        cls.inventory[ProductType.BEVERAGE] = []
        for item in inventory_list:
            cls.inventory[item.type].append(item)

    @classmethod
    def get_item_type(cls, type: ProductType, count: int = 1):
        return [fake.random.choice(cls.inventory[type]) for _ in range(count)]

    @classmethod
    def to_dict(cls) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        for key in cls.inventory:
            all_items += [item.to_dict() for item in cls.inventory[key]]
        return all_items


Inventory.update(
    [
        Product(
            sku=SKU("JAF-001"),
            name="nutellaphone who dis?",
            description="nutella and banana jaffle",
            type=ProductType.JAFFLE,
            price=11,
        ),
        Product(
            sku=SKU("JAF-002"),
            name="doctor stew",
            description="house-made beef stew jaffle",
            type=ProductType.JAFFLE,
            price=11,
        ),
        Product(
            sku=SKU("JAF-003"),
            name="the krautback",
            description="lamb and pork bratwurst with house-pickled cabbage sauerkraut and mustard",
            type=ProductType.JAFFLE,
            price=12,
        ),
        Product(
            sku=SKU("JAF-004"),
            name="flame impala",
            description="pulled pork and pineapple al pastor marinated in ghost pepper sauce, kevin parker's favorite! ",
            type=ProductType.JAFFLE,
            price=14,
        ),
        Product(
            sku=SKU("JAF-005"),
            name="mel-bun",
            description="melon and minced beef bao, in a jaffle, savory and sweet",
            type=ProductType.JAFFLE,
            price=12,
        ),
        Product(
            sku=SKU("BEV-001"),
            name="tangaroo",
            description="mango and tangerine smoothie",
            type=ProductType.BEVERAGE,
            price=6,
        ),
        Product(
            sku=SKU("BEV-002"),
            name="chai and mighty",
            description="oatmilk chai latte with protein boost",
            type=ProductType.BEVERAGE,
            price=5,
        ),
        Product(
            sku=SKU("BEV-003"),
            name="vanilla ice",
            description="iced coffee with house-made french vanilla syrup",
            type=ProductType.BEVERAGE,
            price=6,
        ),
        Product(
            sku=SKU("BEV-004"),
            name="for richer or pourover ",
            description="daily selection of single estate beans for a delicious hot pourover",
            type=ProductType.BEVERAGE,
            price=7,
        ),
        Product(
            sku=SKU("BEV-005"),
            name="adele-ade",
            description="a kiwi and lime agua fresca, hello from the other side of thirst",
            type=ProductType.BEVERAGE,
            price=4,
        ),
    ]
)
