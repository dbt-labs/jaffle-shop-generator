import random
import uuid


class Tweet:
    def __init__(self, customer, tweet_time, order) -> None:
        if len(order.items) == 1:
            items = f"Ordered a {order.items[0].item.name}"
        elif len(order.items) == 2:
            items = (
                f"Ordered a {order.items[0].item.name} and a {order.items[1].item.name}"
            )
        else:
            items = f"Ordered a {', a '.join(item.item.name for item in order.items[:-1])}, and a {order.items[-1].item.name}"
        self.vibes = random.choice(["good", "bad", "neutral"])
        if self.vibes == "good":
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
            self.content = f"Jaffles from the Jaffle Shop are {adjective}! {items}."
        elif self.vibes == "bad":
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
            self.content = f"Jaffle Shop again. {items}. This place is {adjective}."
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
            self.content = f"Jaffle shop is {adjective}. {items}."

        self.uuid = str(uuid.uuid4())
        self.tweeted_at = tweet_time
        self.user_id = customer.customer_id

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.uuid,
            "user_id": self.user_id,
            "tweeted_at": str(self.tweeted_at.date.isoformat()),
            "content": self.content,
        }
