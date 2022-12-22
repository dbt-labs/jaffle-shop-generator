class Supply(object):
    def __init__(self, id, name, cost, perishable, skus):
        self.id = id
        self.name = name
        self.cost = cost
        self.perishable = perishable
        self.skus = skus

    def __str__(self):
        return f"<{self.name} @ ${self.cost}>"

    def __repr__(self):
        return self.__str__()

    def to_dict(self, sku):
        return {
            "id": self.id,
            "name": self.name,
            "cost": int(self.cost * 100),
            "perishable": self.perishable,
            "sku": sku,
        }
