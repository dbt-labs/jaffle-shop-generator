import uuid
from dataclasses import dataclass, field
from typing import NewType, Any

from faker import Faker

from jafgen.time import Day
from jafgen.stores.item import Item 
from jafgen.customers.customers import Customer
from jafgen.stores.store import Store

fake = Faker()

OrderId = NewType("OrderId", uuid.UUID)

@dataclass
class Order:
    customer: Customer
    day: Day
    store: Store
    items: list[Item]
    id: OrderId = field(default_factory=lambda: OrderId(fake.uuid4()))

    subtotal: float = field(init=False)
    tax_paid: float = field(init=False)
    total: float = field(init=False)

    def __post_init__(self) -> None:
        self.subtotal = sum(i.price for i in self.items)
        self.tax_paid = self.store.tax_rate * self.subtotal
        self.order_total = self.subtotal + self.tax_paid

    def __str__(self):
        return f"{self.customer.name} bought {str(self.items)} at {self.day}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "customer": str(self.customer.customer_id),
            "ordered_at": str(self.day.date.isoformat()),
            "store_id": str(self.store.store_id),
            "subtotal": int(self.subtotal * 100),
            "tax_paid": int(self.tax_paid * 100),
            # TODO: figure out why this is doesn't cause a test failure
            # in tests/test_order_totals.py
            # "order_total": int(self.order_total * 100),
            "order_total": int(int(self.subtotal * 100) + int(self.tax_paid * 100)),
        }

    def items_to_dict(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.items]
