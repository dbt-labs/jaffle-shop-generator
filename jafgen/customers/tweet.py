import random
import uuid


class Tweet:
    def __init__(self, customer, tweet_time, order) -> None:
        self.uuid = str(uuid.uuid4())
        self.tweeted_at = tweet_time
        self.customer = customer
        self.order = order
        self.content = self.construct_tweet()

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.uuid,
            "user_id": self.customer.customer_id,
            "tweeted_at": str(self.tweeted_at.isoformat()),
            "content": self.content,
        }

    def construct_tweet(self) -> str:
        if len(self.order.items) == 1:
            items_sentence = f"Ordered a {self.order.items[0].item.name}"
        elif len(self.order.items) == 2:
            items_sentence = f"Ordered a {self.order.items[0].item.name} and a {self.order.items[1].item.name}"
        else:
            items_sentence = f"Ordered a {', a '.join(item.item.name for item in self.order.items[:-1])}, and a {self.order.items[-1].item.name}"
        if self.customer.fan_level > 3:
            adjective = random.choice(
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
            adjective = random.choice(
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
            adjective = random.choice(
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
