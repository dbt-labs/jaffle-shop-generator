from typing import Any

from jafgen.stores.supply import Supply


class Stock(object):
    stock: dict[Any, Any] = {}

    @classmethod
    def update(cls, stock_list):
        for supply in stock_list:
            skus = supply.skus
            for sku in skus:
                if sku not in cls.stock:
                    cls.stock[sku] = []
                cls.stock[sku].append(supply)

    @classmethod
    def to_dict(cls):
        all_items = []
        for key in cls.stock:
            all_items += [item.to_dict(key) for item in cls.stock[key]]
        return all_items


Stock.update(
    [
        Supply(
            id="SUP-001",
            name="compostable cutlery - knife",
            cost=0.07,
            perishable=False,
            skus=["JAF-001", "JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(
            id="SUP-002",
            name="cutlery - fork",
            cost=0.07,
            perishable=False,
            skus=["JAF-001", "JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(
            id="SUP-003",
            name="serving boat",
            cost=0.11,
            perishable=False,
            skus=["JAF-001", "JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(
            id="SUP-004",
            name="napkin",
            cost=0.04,
            perishable=False,
            skus=["JAF-001", "JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(
            id="SUP-005",
            name="16oz compostable clear cup",
            cost=0.13,
            perishable=False,
            skus=["BEV-001", "BEV-002", "BEV-003", "BEV-004", "BEV-005"],
        ),
        Supply(
            id="SUP-006",
            name="16oz compostable clear lid",
            cost=0.04,
            perishable=False,
            skus=["BEV-001", "BEV-002", "BEV-003", "BEV-004", "BEV-005"],
        ),
        Supply(
            id="SUP-007",
            name="biodegradable straw",
            cost=0.13,
            perishable=False,
            skus=["BEV-001", "BEV-002", "BEV-003", "BEV-004", "BEV-005"],
        ),
        Supply(id="SUP-008", name="chai mix", cost=0.98, perishable=True, skus=["BEV-002"]),
        Supply(
            id="SUP-009",
            name="bread",
            cost=0.33,
            perishable=True,
            skus=["JAF-001", "JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(
            id="SUP-010",
            name="cheese",
            cost=0.2,
            perishable=True,
            skus=["JAF-002", "JAF-003", "JAF-004", "JAF-005"],
        ),
        Supply(id="SUP-011", name="nutella", cost=0.46, perishable=True, skus=["JAF-001"]),
        Supply(id="SUP-012", name="banana", cost=0.13, perishable=True, skus=["JAF-001"]),
        Supply(id="SUP-013", name="beef stew", cost=1.69, perishable=True, skus=["JAF-002"]),
        Supply(
            id="SUP-014",
            name="lamb and pork bratwurst",
            cost=2.34,
            perishable=True,
            skus=["JAF-003"],
        ),
        Supply(
            id="SUP-015",
            name="house-pickled cabbage sauerkraut",
            cost=0.43,
            perishable=True,
            skus=["JAF-003"],
        ),
        Supply(id="SUP-016", name="mustard", cost=0.07, perishable=True, skus=["JAF-003"]),
        Supply(id="SUP-017", name="pulled pork", cost=2.15, perishable=True, skus=["JAF-004"]),
        Supply(id="SUP-018", name="pineapple", cost=0.26, perishable=True, skus=["JAF-004"]),
        Supply(id="SUP-019", name="melon", cost=0.33, perishable=True, skus=["JAF-005"]),
        Supply(id="SUP-020", name="minced beef", cost=1.24, perishable=True, skus=["JAF-005"]),
        Supply(
            id="SUP-021", name="ghost pepper sauce", cost=0.2, perishable=True, skus=["JAF-004"]
        ),
        Supply(id="SUP-022", name="mango", cost=0.32, perishable=True, skus=["BEV-001"]),
        Supply(id="SUP-023", name="tangerine", cost=0.2, perishable=True, skus=["BEV-001"]),
        Supply(id="SUP-024", name="oatmilk", cost=0.11, perishable=True, skus=["BEV-002"]),
        Supply(id="SUP-025", name="whey protein", cost=0.36, perishable=True, skus=["BEV-002"]),
        Supply(
            id="SUP-026", name="coffee", cost=0.52, perishable=True, skus=["BEV-003", "BEV-004"]
        ),
        Supply(
            id="SUP-027", name="french vanilla syrup", cost=0.72, perishable=True, skus=["BEV-003"]
        ),
        Supply(id="SUP-028", name="kiwi", cost=0.2, perishable=True, skus=["BEV-005"]),
        Supply(id="SUP-029", name="lime", cost=0.13, perishable=True, skus=["BEV-005"]),
    ]
)
