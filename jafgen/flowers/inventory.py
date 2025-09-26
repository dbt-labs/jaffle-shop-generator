import json
from typing import Any, List
from faker import Faker

from jafgen.flowers.models import (
    Flower, FlowerArrangement, FlowerId, ArrangementId,
    FlowerSeason, CareDifficulty, ArrangementSize
)

fake = Faker()

class FlowerInventory:
    flowers: List[Flower] = []
    arrangements: List[FlowerArrangement] = []

    @classmethod
    def update_flowers(cls, flower_list: List[Flower]):
        cls.flowers = flower_list

    @classmethod
    def update_arrangements(cls, arrangement_list: List[FlowerArrangement]):
        cls.arrangements = arrangement_list

    @classmethod
    def get_random_flower(cls) -> Flower:
        return fake.random.choice(cls.flowers) if cls.flowers else None

    @classmethod
    def get_random_arrangement(cls) -> FlowerArrangement:
        return fake.random.choice(cls.arrangements) if cls.arrangements else None

    @classmethod
    def get_flowers_by_season(cls, season: FlowerSeason) -> List[Flower]:
        return [f for f in cls.flowers if f.seasonal_availability == season or f.seasonal_availability == FlowerSeason.YEAR_ROUND]

    @classmethod
    def flowers_to_dict(cls) -> List[dict[str, Any]]:
        return [flower.to_dict() for flower in cls.flowers]

    @classmethod
    def arrangements_to_dict(cls) -> List[dict[str, Any]]:
        return [arrangement.to_dict() for arrangement in cls.arrangements]

# Initialize with sample data
sample_flowers = [
    Flower(
        flower_id=FlowerId("FLW-001"),
        flower_name="Red Rose",
        color="red",
        price_per_stem=4.50,
        supplier_id="SUP-001",
        seasonal_availability=FlowerSeason.YEAR_ROUND,
        care_difficulty=CareDifficulty.MEDIUM,
        lifespan_days=7,
    ),
    Flower(
        flower_id=FlowerId("FLW-002"),
        flower_name="White Rose",
        color="white",
        price_per_stem=4.00,
        supplier_id="SUP-001",
        seasonal_availability=FlowerSeason.YEAR_ROUND,
        care_difficulty=CareDifficulty.MEDIUM,
        lifespan_days=7,
    ),
    Flower(
        flower_id=FlowerId("FLW-003"),
        flower_name="Yellow Tulip",
        color="yellow",
        price_per_stem=3.25,
        supplier_id="SUP-002",
        seasonal_availability=FlowerSeason.SPRING,
        care_difficulty=CareDifficulty.LOW,
        lifespan_days=5,
    ),
    Flower(
        flower_id=FlowerId("FLW-004"),
        flower_name="Pink Tulip",
        color="pink",
        price_per_stem=3.50,
        supplier_id="SUP-002",
        seasonal_availability=FlowerSeason.SPRING,
        care_difficulty=CareDifficulty.LOW,
        lifespan_days=5,
    ),
    Flower(
        flower_id=FlowerId("FLW-005"),
        flower_name="Sunflower",
        color="yellow",
        price_per_stem=5.00,
        supplier_id="SUP-003",
        seasonal_availability=FlowerSeason.SUMMER,
        care_difficulty=CareDifficulty.LOW,
        lifespan_days=9,
    ),
    Flower(
        flower_id=FlowerId("FLW-006"),
        flower_name="White Lily",
        color="white",
        price_per_stem=6.00,
        supplier_id="SUP-001",
        seasonal_availability=FlowerSeason.YEAR_ROUND,
        care_difficulty=CareDifficulty.HIGH,
        lifespan_days=6,
    ),
    Flower(
        flower_id=FlowerId("FLW-007"),
        flower_name="Purple Iris",
        color="purple",
        price_per_stem=4.75,
        supplier_id="SUP-004",
        seasonal_availability=FlowerSeason.SPRING,
        care_difficulty=CareDifficulty.MEDIUM,
        lifespan_days=4,
    ),
    Flower(
        flower_id=FlowerId("FLW-008"),
        flower_name="Orange Marigold",
        color="orange",
        price_per_stem=2.50,
        supplier_id="SUP-005",
        seasonal_availability=FlowerSeason.FALL,
        care_difficulty=CareDifficulty.LOW,
        lifespan_days=8,
    ),
    Flower(
        flower_id=FlowerId("FLW-009"),
        flower_name="Pink Carnation",
        color="pink",
        price_per_stem=3.00,
        supplier_id="SUP-002",
        seasonal_availability=FlowerSeason.YEAR_ROUND,
        care_difficulty=CareDifficulty.LOW,
        lifespan_days=10,
    ),
    Flower(
        flower_id=FlowerId("FLW-010"),
        flower_name="White Chrysanthemum",
        color="white",
        price_per_stem=3.75,
        supplier_id="SUP-006",
        seasonal_availability=FlowerSeason.FALL,
        care_difficulty=CareDifficulty.MEDIUM,
        lifespan_days=12,
    ),
]

sample_arrangements = [
    FlowerArrangement(
        arrangement_name="Classic Dozen Roses",
        description="Twelve beautiful red roses in a classic arrangement",
        base_price=75.00,
        flower_ids="FLW-001",
        flower_quantities="12",
        size=ArrangementSize.LARGE,
        occasion_type="romantic",
        is_custom=False,
    ),
    FlowerArrangement(
        arrangement_name="Spring Tulip Bouquet",
        description="Mixed tulips in spring colors",
        base_price=45.00,
        flower_ids="FLW-003,FLW-004",
        flower_quantities="6,6",
        size=ArrangementSize.MEDIUM,
        occasion_type="spring",
        is_custom=False,
    ),
    FlowerArrangement(
        arrangement_name="Sympathy Arrangement",
        description="White lilies and chrysanthemums for memorial services",
        base_price=65.00,
        flower_ids="FLW-006,FLW-010",
        flower_quantities="4,8",
        size=ArrangementSize.LARGE,
        occasion_type="funeral",
        is_custom=False,
    ),
    FlowerArrangement(
        arrangement_name="Birthday Bright Mix",
        description="Colorful mix of seasonal flowers",
        base_price=35.00,
        flower_ids="FLW-005,FLW-007,FLW-009",
        flower_quantities="3,3,4",
        size=ArrangementSize.MEDIUM,
        occasion_type="birthday",
        is_custom=False,
    ),
    FlowerArrangement(
        arrangement_name="Small Thank You Bouquet",
        description="Simple carnation arrangement to say thanks",
        base_price=25.00,
        flower_ids="FLW-009",
        flower_quantities="8",
        size=ArrangementSize.SMALL,
        occasion_type="thank_you",
        is_custom=False,
    ),
]

FlowerInventory.update_flowers(sample_flowers)
FlowerInventory.update_arrangements(sample_arrangements)