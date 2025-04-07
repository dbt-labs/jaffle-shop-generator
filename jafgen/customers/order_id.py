import uuid
from typing import NewType

OrderId = NewType("OrderId", uuid.UUID)
