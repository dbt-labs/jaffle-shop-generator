from dataclasses import dataclass
from enum import Enum
from typing import Any

from jafgen.stores.supply import StorageKeepingUnit


class ProductType(str, Enum):
    JAFFLE = "JAFFLE"
    BEVERAGE = "BEVERAGE"


@dataclass(frozen=True)
class Product:
    sku: StorageKeepingUnit
    name: str
    description: str
    type: ProductType
    price: float

    def __str__(self):
        return f"<{self.name} @ ${self.price}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": self.sku,
            "name": str(self.name),
            "type": str(self.type.value),
            "price": int(self.price * 100),
            "description": str(self.description),
        }
