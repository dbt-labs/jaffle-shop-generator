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

    def to_dict(self):
        return {
            "sku": self.sku,
            "name": self.name,
            "type": self.type,
            "price": int(self.price * 100),
            "description": self.description,
        }
