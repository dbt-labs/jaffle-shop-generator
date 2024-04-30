from dataclasses import dataclass
from typing import NewType

SupplyId = NewType("SupplyId", str)
StorageKeepingUnit = NewType("StorageKeepingUnit", str)


@dataclass(frozen=True)
class Supply:

    """Any supply that's not an item itself.

    Examples: cuttlery, ingredients, napkins etc.
    """

    id: SupplyId
    name: str
    cost: float
    perishable: bool
    skus: list[StorageKeepingUnit]

    def to_dict(self, sku: StorageKeepingUnit) -> dict[str, str | int]:
        """Serialize to dict.

        TODO: replace this by serializer class.
        """
        return {
            "id": str(self.id),
            "name": str(self.name),
            "cost": int(self.cost * 100),
            "perishable": str(self.perishable),
            "sku": str(sku),
        }
