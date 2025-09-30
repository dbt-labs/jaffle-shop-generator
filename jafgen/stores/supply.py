from dataclasses import dataclass
from typing import NewType

SupplyId = NewType("SupplyId", str)
StorageKeepingUnit = NewType("StorageKeepingUnit", str)


@dataclass(frozen=True)
class Supply:
    id: SupplyId
    name: str
    cost: float
    perishable: bool
    skus: list[StorageKeepingUnit]

    def __str__(self):
        return f"<{self.name} @ ${self.cost}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self, sku: StorageKeepingUnit) -> dict[str, str | int]:
        return {
            "id": str(self.id),
            "name": str(self.name),
            "cost": int(self.cost * 100),
            "perishable": str(self.perishable),
            "sku": str(sku),
        }
