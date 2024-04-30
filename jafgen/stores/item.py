from dataclasses import dataclass
from enum import Enum
from typing import Any

from jafgen.stores.supply import StorageKeepingUnit


class ItemType(str, Enum):

    """The type of an item (food or drink)."""

    JAFFLE = "JAFFLE"
    BEVERAGE = "BEVERAGE"


@dataclass(frozen=True)
class Item:

    """Anything that can be sold on a Jaffle Shop store.

    Can be coffee, smoothies, sandwiches etc.
    """

    sku: StorageKeepingUnit
    name: str
    description: str
    type: ItemType
    price: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict.

        TODO: replace this by serializer class.
        """
        return {
            "sku": self.sku,
            "name": str(self.name),
            "type": str(self.type),
            "price": int(self.price * 100),
            "description": str(self.description),
        }
