from jafgen.customers.customer import BrunchCrowd, Customer, RemoteWorker, Student
from jafgen.customers.order import Order, OrderItem
from jafgen.stores.inventory import Inventory
from jafgen.stores.product import ProductType
from jafgen.stores.store import Store
from jafgen.time import Day


def test_order_totals(default_store: Store):
    """Ensure order totals are equivalent to the sum of the item prices and tax paid."""
    inventory = Inventory()
    orders: list[Order] = []
    customer_types: list[type[Customer]] = [RemoteWorker, BrunchCrowd, Student]
    for i in range(1000):
        for CustType in customer_types:
            food = inventory.get_item_type(ProductType.JAFFLE, 2)
            beverage = inventory.get_item_type(ProductType.BEVERAGE, 1)
            all_items = food + beverage
            orders.append(
                Order(
                    customer=CustType(store=default_store),
                    order_items=[OrderItem(product=item) for item in all_items],
                    store=default_store,
                    day=Day(date_index=i),
                )
            )

    for order in orders:
        assert (
            order.subtotal
            == order.order_items[0].product.price
            + order.order_items[1].product.price
            + order.order_items[2].product.price
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
