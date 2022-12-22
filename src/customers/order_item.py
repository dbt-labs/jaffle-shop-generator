import uuid


class OrderItem(object):
    def __init__(self, order_id, item):
        self.item_id = str(uuid.uuid4())
        self.order_id = order_id
        self.item = item

    def to_dict(self):
        return {
            "id": self.item_id,
            "order_id": self.order_id,
            "sku": self.item.sku,
        }
