import uuid
from dataclasses import dataclass, field
from typing import NewType

from faker import Faker

import jafgen.customers.customer as customer
from jafgen.customers.order import Order
from jafgen.time import Day

fake = Faker()

TweetId = NewType("TweetId", uuid.UUID)


@dataclass
class Tweet:
    day: Day
    customer: "customer.Customer"
    order: Order
    id: TweetId = field(default_factory=lambda: TweetId(uuid.UUID(fake.uuid4())))
    content: str = field(init=False)

    def __post_init__(self) -> None:
        self.content = self._construct_tweet()

    def to_dict(self) -> dict[str, str]:
        return {
            "id": str(self.id),
            "user_id": str(self.customer.id),
            "tweeted_at": str(self.day.date.isoformat()),
            "content": self.content,
        }

    def _construct_tweet(self) -> str:
        if len(self.order.order_items) == 1:
            items_sentence = f"Ordered a {self.order.order_items[0].product.name}"
        elif len(self.order.order_items) == 2:
            items_sentence = f"Ordered a {self.order.order_items[0].product.name} and a {self.order.order_items[1].product.name}"
        else:
            items_sentence = f"Ordered a {', a '.join(item.product.name for item in self.order.order_items[:-1])}, and a {self.order.order_items[-1].product.name}"
        if self.customer.fan_level > 3:
            adjective = fake.random.choice(
                [
                    "the best",
                    "awesome",
                    "delicious",
                    "amazing",
                    "fantastic",
                    "sooo gooood",
                    "my favorite",
                ]
            )
            return f"Jaffles from the Jaffle Shop are {adjective}! {items_sentence}."
        elif self.customer.fan_level < 3:
            adjective = fake.random.choice(
                [
                    "terrible",
                    "the worst",
                    "awful",
                    "disgusting",
                    "gross",
                    "inedible",
                    "my least favorite",
                ]
            )
            return f"Jaffle Shop again. {items_sentence}. This place is {adjective}."
        else:
            adjective = fake.random.choice(
                [
                    "okay",
                    "fine",
                    "alright",
                    "average",
                    "pretty decent",
                    "solid",
                    "not bad",
                    "just meh",
                ]
            )
            return f"Jaffle shop is {adjective}. {items_sentence}."
