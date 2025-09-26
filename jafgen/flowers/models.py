import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, NewType

from faker import Faker

fake = Faker()

FlowerId = NewType("FlowerId", str)
ArrangementId = NewType("ArrangementId", uuid.UUID)
DeliveryId = NewType("DeliveryId", uuid.UUID)
FlowerOrderId = NewType("FlowerOrderId", uuid.UUID)

class FlowerSeason(str, Enum):
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"
    YEAR_ROUND = "year_round"

class CareDifficulty(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ArrangementSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    FAILED = "failed"

class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class Flower:
    flower_id: FlowerId
    flower_name: str
    color: str
    price_per_stem: float
    supplier_id: str
    seasonal_availability: FlowerSeason
    care_difficulty: CareDifficulty
    lifespan_days: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "flower_id": self.flower_id,
            "flower_name": self.flower_name,
            "color": self.color,
            "price_per_stem": int(self.price_per_stem * 100),  # Store as cents
            "supplier_id": self.supplier_id,
            "seasonal_availability": self.seasonal_availability.value,
            "care_difficulty": self.care_difficulty.value,
            "lifespan_days": self.lifespan_days,
        }

@dataclass(frozen=True)
class FlowerArrangement:
    arrangement_id: ArrangementId = field(default_factory=lambda: ArrangementId(fake.uuid4()))
    arrangement_name: str = ""
    description: str = ""
    base_price: float = 0.0
    flower_ids: str = ""  # JSON-like string or comma-separated
    flower_quantities: str = ""  # JSON-like string or comma-separated
    size: ArrangementSize = ArrangementSize.MEDIUM
    occasion_type: str = ""
    is_custom: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "arrangement_id": str(self.arrangement_id),
            "arrangement_name": self.arrangement_name,
            "description": self.description,
            "base_price": int(self.base_price * 100),  # Store as cents
            "flower_ids": self.flower_ids,
            "flower_quantities": self.flower_quantities,
            "size": self.size.value,
            "occasion_type": self.occasion_type,
            "is_custom": self.is_custom,
        }

@dataclass(frozen=True)
class DeliveryInfo:
    delivery_id: DeliveryId = field(default_factory=lambda: DeliveryId(fake.uuid4()))
    delivery_address: str = ""
    delivery_city: str = ""
    delivery_state: str = ""
    delivery_zip: str = ""
    delivery_date: str = ""
    delivery_time_slot: str = ""
    delivery_fee: float = 0.0
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    special_instructions: str = ""
    recipient_name: str = ""
    recipient_phone: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "delivery_id": str(self.delivery_id),
            "delivery_address": self.delivery_address,
            "delivery_city": self.delivery_city,
            "delivery_state": self.delivery_state,
            "delivery_zip": self.delivery_zip,
            "delivery_date": self.delivery_date,
            "delivery_time_slot": self.delivery_time_slot,
            "delivery_fee": int(self.delivery_fee * 100),  # Store as cents
            "delivery_status": self.delivery_status.value,
            "special_instructions": self.special_instructions,
            "recipient_name": self.recipient_name,
            "recipient_phone": self.recipient_phone,
        }

@dataclass(frozen=True)
class FlowerOrder:
    flower_order_id: FlowerOrderId = field(default_factory=lambda: FlowerOrderId(fake.uuid4()))
    customer_name: str = ""
    customer_email: str = ""
    customer_phone: str = ""
    arrangement_id: ArrangementId = field(default_factory=lambda: ArrangementId(fake.uuid4()))
    quantity: int = 1
    total_amount: float = 0.0
    delivery_id: DeliveryId = field(default_factory=lambda: DeliveryId(fake.uuid4()))
    occasion: str = ""
    promo_code: str = ""
    discount_amount: float = 0.0
    order_date: str = ""
    order_status: OrderStatus = OrderStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        return {
            "flower_order_id": str(self.flower_order_id),
            "customer_name": self.customer_name,
            "customer_email": self.customer_email,
            "customer_phone": self.customer_phone,
            "arrangement_id": str(self.arrangement_id),
            "quantity": self.quantity,
            "total_amount": int(self.total_amount * 100),  # Store as cents
            "delivery_id": str(self.delivery_id),
            "occasion": self.occasion,
            "promo_code": self.promo_code,
            "discount_amount": int(self.discount_amount * 100),  # Store as cents
            "order_date": self.order_date,
            "order_status": self.order_status.value,
        }