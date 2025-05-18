import uuid
from dataclasses import dataclass, field
from typing import Any, List, NewType

from faker import Faker

import jafgen.customers.customer as customer
from jafgen.stores.product import Product
from jafgen.stores.store import Store
from jafgen.time import Day

fake = Faker()

OrderId = NewType("OrderId", uuid.UUID)
OrderItemId = NewType("OrderItemId", uuid.UUID)


@dataclass
class OrderItem:
    product: Product
    quantity: int = 1
    id: OrderItemId = field(
        default_factory=lambda: OrderItemId(uuid.UUID(fake.uuid4()))
    )


@dataclass
class Order:
    customer: "customer.Customer"
    day: Day
    store: Store
    order_items: list[OrderItem]
    id: OrderId = field(default_factory=lambda: OrderId(uuid.UUID(fake.uuid4())))

    subtotal: float = field(init=False)
    tax_paid: float = field(init=False)
    total: float = field(init=False)

    def __post_init__(self) -> None:
        self.subtotal = sum(i.product.price * i.quantity for i in self.order_items)
        self.tax_paid = self.store.tax_rate * self.subtotal
        self.total = self.subtotal + self.tax_paid

    def __str__(self):
        return f"{self.customer.name} bought {str(self.order_items)} at {self.day}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "customer_id": str(self.customer.id),
            "ordered_at": str(self.day.date.isoformat()),
            "store_id": str(self.store.id),
            "subtotal": int(self.subtotal * 100),
            "tax_paid": int(self.tax_paid * 100),
            # TODO: figure out why this is doesn't cause a test failure
            # in tests/test_order_totals.py
            # "order_total": int(self.order_total * 100),
            "order_total": int(int(self.subtotal * 100) + int(self.tax_paid * 100)),
        }

    def order_items_to_dict(self) -> List[dict[str, Any]]:
        return [
            {
                "id": str(order_item.id),
                "order_id": str(self.id),
                "sku": str(order_item.product.sku),
                "quantity": order_item.quantity,
            }
            for order_item in self.order_items
        ]
