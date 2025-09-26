import random
from datetime import datetime, timedelta
from typing import List, Tuple
import numpy as np
from faker import Faker

from jafgen.flowers.models import (
    FlowerOrder, DeliveryInfo, FlowerArrangement,
    DeliveryStatus, OrderStatus, FlowerOrderId, DeliveryId, ArrangementId
)
from jafgen.flowers.inventory import FlowerInventory
from jafgen.time import Day

fake = Faker()

class FlowerOrderGenerator:
    def __init__(self, scale: int = 100):
        self.scale = scale
        self.promo_codes = [
            "SPRING20", "LOVE15", "MOTHER10", "GRAD25", "BIRTHDAY5",
            "THANKS10", "NEWCUSTOMER", "FIRSTORDER"
        ]
        self.occasions = [
            "Valentine's Day", "Mother's Day", "Birthday", "Anniversary",
            "Get Well", "Thank You", "Congratulations", "Sympathy",
            "Just Because", "Graduation"
        ]

    def generate_delivery_info(self, order_date: datetime) -> DeliveryInfo:
        """Generate realistic delivery information"""
        delivery_date = order_date + timedelta(days=random.randint(1, 3))
        time_slots = ["9:00-12:00", "12:00-15:00", "15:00-18:00", "18:00-21:00"]

        return DeliveryInfo(
            delivery_address=fake.street_address(),
            delivery_city=fake.city(),
            delivery_state=fake.state_abbr(),
            delivery_zip=fake.zipcode(),
            delivery_date=delivery_date.date().isoformat(),
            delivery_time_slot=random.choice(time_slots),
            delivery_fee=round(random.uniform(5.0, 15.0), 2),
            delivery_status=random.choices(
                [DeliveryStatus.DELIVERED, DeliveryStatus.PENDING, DeliveryStatus.IN_TRANSIT],
                weights=[0.7, 0.2, 0.1]
            )[0],
            special_instructions=fake.sentence() if random.random() < 0.3 else "",
            recipient_name=fake.name(),
            recipient_phone=fake.phone_number(),
        )

    def generate_flower_order(self, day: Day) -> Tuple[FlowerOrder, DeliveryInfo]:
        """Generate a single flower order with corresponding delivery info"""
        arrangement = FlowerInventory.get_random_arrangement()
        if not arrangement:
            # Create a basic arrangement if none exist
            arrangement = FlowerArrangement(
                arrangement_name="Basic Bouquet",
                description="Simple mixed flower arrangement",
                base_price=30.00,
                flower_ids="FLW-001,FLW-009",
                flower_quantities="3,5",
                size="medium",
                occasion_type="general",
                is_custom=False
            )

        quantity = random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
        base_total = arrangement.base_price * quantity

        # Apply discount if promo code used
        use_promo = random.random() < 0.2  # 20% chance of using promo
        promo_code = random.choice(self.promo_codes) if use_promo else ""
        discount_amount = base_total * 0.1 if use_promo else 0.0  # 10% discount

        order_datetime = day.date.replace(
            hour=random.randint(8, 20),
            minute=random.randint(0, 59)
        )

        delivery_info = self.generate_delivery_info(order_datetime)

        total_amount = base_total - discount_amount + delivery_info.delivery_fee

        flower_order = FlowerOrder(
            customer_name=fake.name(),
            customer_email=fake.email(),
            customer_phone=fake.phone_number(),
            arrangement_id=arrangement.arrangement_id,
            quantity=quantity,
            total_amount=total_amount,
            delivery_id=delivery_info.delivery_id,
            occasion=random.choice(self.occasions) if random.random() < 0.6 else "",
            promo_code=promo_code,
            discount_amount=discount_amount,
            order_date=order_datetime.isoformat(),
            order_status=random.choices(
                [OrderStatus.DELIVERED, OrderStatus.CONFIRMED, OrderStatus.PREPARING],
                weights=[0.6, 0.3, 0.1]
            )[0],
        )

        return flower_order, delivery_info

    def generate_orders_for_day(self, day: Day) -> Tuple[List[FlowerOrder], List[DeliveryInfo]]:
        """Generate multiple flower orders for a given day based on seasonality"""
        # Base probability of orders per day
        base_orders_per_day = self.scale / 30  # Roughly scale/30 orders per day on average

        # Seasonal multipliers
        seasonal_multiplier = 1.0
        month = day.date.month
        day_of_year = day.date.timetuple().tm_yday

        # Valentine's Day spike (Feb 14)
        if 40 <= day_of_year <= 50:  # Around Valentine's Day
            seasonal_multiplier = 3.0
        # Mother's Day spike (2nd Sunday in May)
        elif 120 <= day_of_year <= 140:  # Around Mother's Day
            seasonal_multiplier = 2.5
        # Spring season (Mar-May)
        elif 3 <= month <= 5:
            seasonal_multiplier = 1.5
        # Christmas season (Dec)
        elif month == 12:
            seasonal_multiplier = 1.3
        # Summer (lower demand)
        elif 6 <= month <= 8:
            seasonal_multiplier = 0.7

        # Weekend multiplier (less business orders, more personal)
        if day.is_weekend:
            seasonal_multiplier *= 1.2

        # Calculate number of orders for this day
        expected_orders = base_orders_per_day * seasonal_multiplier
        num_orders = max(0, int(np.random.poisson(expected_orders)))

        orders = []
        deliveries = []

        for _ in range(num_orders):
            order, delivery = self.generate_flower_order(day)
            orders.append(order)
            deliveries.append(delivery)

        return orders, deliveries