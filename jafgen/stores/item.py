from dataclasses import dataclass
from enum import Enum
from typing import Any

from jafgen.stores.supply import StorageKeepingUnit


class ItemType(str, Enum):
    JAFFLE = "JAFFLE"
    BEVERAGE = "BEVERAGE"


@dataclass(frozen=True)
class Item:
    sku: StorageKeepingUnit
    name: str
    description: str
    type: ItemType
    price: float

    def __str__(self):
        return f"<{self.name} @ ${self.price}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self, order_id: str = None) -> dict[str, Any]:
        result = {
            "sku": self.sku,
            "name": str(self.name),
            "type": str(self.type),
            "price": int(self.price * 100),
            "description": str(self.description),
        }
        if order_id is not None:
            result["order_id"] = order_id
        return result
