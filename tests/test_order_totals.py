from jafgen.customers.order import Order
from jafgen.curves import Day
from jafgen.stores.store import Store
from jafgen.customers.customers import RemoteWorker
from jafgen.stores.inventory import Inventory


def test_order_totals():
    """Ensure order totals are calculated correctly"""
    store = Store(str(1), "Testylvania", 0.85, 0, 9 * 100, 0.0659123)
    inventory = Inventory()
    orders = []
    for i in range(1000):
        orders.append(
            Order(
                customer=RemoteWorker(store=store),
                items=[
                    inventory.get_food()[0],
                    inventory.get_drink()[0],
                ],
                store=store,
                day=Day(date_index=i),
            )
        )
    for order in orders:
        assert order.subtotal == order.items[0].item.price + order.items[1].item.price
        assert order.tax_paid == order.subtotal * order.store.tax_rate
        assert order.order_total == order.subtotal + order.tax_paid
        assert round(float(order.order_total), 2) == round(
            float(order.subtotal), 2
        ) + round(float(order.tax_paid), 2)
