from jafgen.stores.inventory import Inventory
from jafgen.stores.stock import Stock
from jafgen.stores.supply import Supply


def test_stock_and_inventory_equal():
    """Ensure Stock and Inventory have an equal number of items"""
    assert len(Stock.stock) == len(Inventory.inventory["jaffle"]) + len(
        Inventory.inventory["beverage"]
    )


def test_all_inventory_beverages_are_beverages():
    """Ensure all the items in inventory.beverage are of type beverage"""
    for item in Inventory.inventory["beverage"]:
        assert item.type == "beverage"


def test_all_inventory_jaffles_are_jaffles():
    """Ensure all the items in inventory.jaffle are of type jaffle"""
    for item in Inventory.inventory["jaffle"]:
        assert item.type == "jaffle"


def test_inventory_stock_all_has_supplies():
    """Ensure all Supplies have the necessary properties"""
    for menu_item in Stock.stock:
        for supply in Stock.stock[menu_item]:
            assert isinstance(supply, Supply)


def test_supplies_have_all_props():
    """Ensure all Supplies have the necessary properties"""
    supply_attrs = ["id", "name", "cost", "perishable", "skus"]
    for menu_item in Stock.stock:
        for supply in Stock.stock[menu_item]:
            for attr in supply_attrs:
                assert hasattr(supply, attr)
