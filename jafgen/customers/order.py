import uuid

from jafgen.customers.order_item import OrderItem


class Order(object):
    def __init__(self, customer, items, store, day):
        self.order_id = str(uuid.uuid4())
        self.customer = customer
        self.items = [OrderItem(self.order_id, item) for item in items]
        self.store = store
        self.day = day
        self.subtotal = sum(i.item.price for i in self.items)
        self.tax_paid = store.tax_rate * self.subtotal
        self.order_total = self.subtotal + self.tax_paid

    def __str__(self):
        return f"{self.customer.name} bought {str(self.items)} at {self.day}"

    def to_dict(self):
        return {
            "id": self.order_id,
            "customer": self.customer.customer_id,
            "ordered_at": self.day.date.isoformat(),
            # "order_month": self.day.date.strftime("%Y-%m"),
            "store_id": self.store.store_id,
            "subtotal": int(self.subtotal * 100),
            "tax_paid": int(self.tax_paid * 100),
            "order_total": int(self.order_total * 100),
        }

    def items_to_dict(self):
        return [i.to_dict(self.order_id) for i in self.items]
