from dataclasses import dataclass
from enum import Enum
from typing import Any

from jafgen.stores.supply import StorageKeepingUnit


class ItemType(Enum, str):
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": str(self.name),
            "type": str(self.type),
            "price": int(self.price * 100),
            "description": str(self.description),
        }
