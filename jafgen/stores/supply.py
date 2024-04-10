from typing import Any


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

    def to_dict(self, sku) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "name": str(self.name),
            "cost": int(self.cost * 100),
            "perishable": str(self.perishable),
            "sku": str(sku),
        }
