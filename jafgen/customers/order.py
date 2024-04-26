import uuid
from typing import Any

from jafgen.customers.order_item import OrderItem


class Order(object):
    def __init__(self, customer, items, store, order_time):
        self.order_id = str(uuid.uuid4())
        self.customer = customer
        self.items = [OrderItem(self.order_id, item) for item in items]
        self.store = store
        self.order_time = order_time
        self.subtotal = sum(i.item.price for i in self.items)
        self.tax_paid = store.tax_rate * self.subtotal
        self.order_total = self.subtotal + self.tax_paid

    def __str__(self):
        return f"{self.customer.name} bought {str(self.items)} at {self.order_time}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.order_id),
            "customer": str(self.customer.customer_id),
            "ordered_at": str(self.order_time.date.isoformat()),
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
