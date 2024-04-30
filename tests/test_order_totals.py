from jafgen.customers.customers import BrunchCrowd, Customer, RemoteWorker, Student
from jafgen.customers.order import Order
from jafgen.stores.inventory import Inventory
from jafgen.stores.item import ItemType
from jafgen.stores.store import Store
from jafgen.time import Day


def test_order_totals(default_store: Store):
    """Ensure order totals are equivalent to the sum of the item prices and tax paid."""
    inventory = Inventory()
    orders: list[Order] = []
    customer_types: list[type[Customer]] = [RemoteWorker, BrunchCrowd, Student]
    for i in range(1000):
        for CustType in customer_types:
            orders.append(
                Order(
                    customer=CustType(store=default_store),
                    items=inventory.get_item_type(ItemType.JAFFLE, 2)
                    + inventory.get_item_type(ItemType.BEVERAGE, 1),
                    store=default_store,
                    day=Day(date_index=i),
                )
            )

    for order in orders:
        assert (
            order.subtotal
            == order.items[0].price + order.items[1].price + order.items[2].price
        )
        assert order.tax_paid == order.subtotal * order.store.tax_rate
        assert order.total == order.subtotal + order.tax_paid
        assert round(float(order.total), 2) == round(float(order.subtotal), 2) + round(
            float(order.tax_paid), 2
        )
        order_dict = order.to_dict()
        assert (
            order_dict["order_total"] == order_dict["subtotal"] + order_dict["tax_paid"]
        )
