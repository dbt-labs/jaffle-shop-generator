from typing import Any

from faker import Faker

from jafgen.stores.item import Item, ItemType
from jafgen.stores.supply import StorageKeepingUnit as SKU

fake = Faker()


class Inventory:

    """Holds all possible items to buy from a Jaffle Shop store."""

    inventory: dict[ItemType, list[Item]] = {}

    @classmethod
    def update(cls, inventory_list: list[Item]):
        """Update the inventory with a new list of items."""
        cls.inventory[ItemType.JAFFLE] = []
        cls.inventory[ItemType.BEVERAGE] = []
        for item in inventory_list:
            cls.inventory[item.type].append(item)

    @classmethod
    def get_item_type(cls, type: ItemType, count: int = 1):
        """Get a random assortment of N items of `type`."""
        return [fake.random.choice(cls.inventory[type]) for _ in range(count)]

    @classmethod
    def to_dict(cls) -> list[dict[str, Any]]:
        """Serialize to dict.

        TODO: replace this by serializer class.
        """
        all_items: list[dict[str, Any]] = []
        for key in cls.inventory:
            all_items += [item.to_dict() for item in cls.inventory[key]]
        return all_items


Inventory.update(
    [
        Item(
            sku=SKU("JAF-001"),
            name="nutellaphone who dis?",
            description="nutella and banana jaffle",
            type=ItemType.JAFFLE,
            price=11,
        ),
        Item(
            sku=SKU("JAF-002"),
            name="doctor stew",
            description="house-made beef stew jaffle",
            type=ItemType.JAFFLE,
            price=11,
        ),
        Item(
            sku=SKU("JAF-003"),
            name="the krautback",
            description="lamb and pork bratwurst with house-pickled "
                        "cabbage sauerkraut and mustard",
            type=ItemType.JAFFLE,
            price=12,
        ),
        Item(
            sku=SKU("JAF-004"),
            name="flame impala",
            description="pulled pork and pineapple al pastor marinated "
                        "in ghost pepper sauce, kevin parker's favorite! ",
            type=ItemType.JAFFLE,
            price=14,
        ),
        Item(
            sku=SKU("JAF-005"),
            name="mel-bun",
            description="melon and minced beef bao, in a jaffle, savory and sweet",
            type=ItemType.JAFFLE,
            price=12,
        ),
        Item(
            sku=SKU("BEV-001"),
            name="tangaroo",
            description="mango and tangerine smoothie",
            type=ItemType.BEVERAGE,
            price=6,
        ),
        Item(
            sku=SKU("BEV-002"),
            name="chai and mighty",
            description="oatmilk chai latte with protein boost",
            type=ItemType.BEVERAGE,
            price=5,
        ),
        Item(
            sku=SKU("BEV-003"),
            name="vanilla ice",
            description="iced coffee with house-made french vanilla syrup",
            type=ItemType.BEVERAGE,
            price=6,
        ),
        Item(
            sku=SKU("BEV-004"),
            name="for richer or pourover ",
            description="daily selection of single estate beans "
                        "for a delicious hot pourover",
            type=ItemType.BEVERAGE,
            price=7,
        ),
        Item(
            sku=SKU("BEV-005"),
            name="adele-ade",
            description="a kiwi and lime agua fresca, hello from the "
                        "other side of thirst",
            type=ItemType.BEVERAGE,
            price=4,
        ),
    ]
)
