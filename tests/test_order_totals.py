from jafgen.customers.order import Order
from jafgen.curves import Day
from jafgen.stores.store import Store
from jafgen.customers.customers import RemoteWorker, BrunchCrowd, Student
from jafgen.stores.inventory import Inventory


def test_order_totals():
    """Ensure order totals are equivalent to the sum of the item prices and tax paid"""

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
                    inventory.get_food()[0],
                ],
                store=store,
                order_time=Day(date_index=i),
            )
        )
        orders.append(
            Order(
                customer=BrunchCrowd(store=store),
                items=[
                    inventory.get_food()[0],
                    inventory.get_drink()[0],
                    inventory.get_food()[0],
                ],
                store=store,
                order_time=Day(date_index=i),
            )
        )
        orders.append(
            Order(
                customer=Student(store=store),
                items=[
                    inventory.get_food()[0],
                    inventory.get_drink()[0],
                    inventory.get_food()[0],
                ],
                store=store,
                order_time=Day(date_index=i),
            )
        )
    for order in orders:
        assert (
            order.subtotal
            == order.items[0].item.price
            + order.items[1].item.price
            + order.items[2].item.price
        )
        assert order.tax_paid == order.subtotal * order.store.tax_rate
        assert order.order_total == order.subtotal + order.tax_paid
        assert round(float(order.order_total), 2) == round(
            float(order.subtotal), 2
        ) + round(float(order.tax_paid), 2)
        order_dict = order.to_dict()
        assert (
            order_dict["order_total"] == order_dict["subtotal"] + order_dict["tax_paid"]
        )
