import uuid
from dataclasses import dataclass, field
from typing import Any, NewType

from faker import Faker

from jafgen.customers.order_id import OrderId
from jafgen.stores.item import Item
from jafgen.stores.supply import StorageKeepingUnit

fake = Faker()

OrderItemId = NewType("OrderItemId", uuid.UUID)

@dataclass(frozen=True)
class OrderItem:
    item: Item
    id: OrderItemId = field(default_factory=lambda: OrderItemId(fake.uuid4()))

    @property
    def name(self) -> str:
        return self.item.name

    @property
    def price(self) -> float:
        return self.item.price

    @property
    def sku(self) -> StorageKeepingUnit:
        return self.item.sku

    def __str__(self):
        return f"<{self.name} @ ${self.price}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self, order_id: OrderId) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "order_id": str(order_id),
            "sku": str(self.sku),
        }
