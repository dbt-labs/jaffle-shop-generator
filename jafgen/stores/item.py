from typing import Any


class Item(object):
    def __init__(self, sku, name, description, type, price):
        self.sku = sku
        self.name = name
        self.description = description
        self.type = type
        self.price = price

    def __str__(self):
        return f"<{self.name} @ ${self.price}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku": str(self.sku),
            "name": str(self.name),
            "type": str(self.type),
            "price": int(self.price * 100),
            "description": str(self.description),
        }
