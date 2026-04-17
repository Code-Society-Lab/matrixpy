from typing import Protocol

from matrix.config import Config
from matrix.room import Room


class BotLike(Protocol):
    prefix: str | None

    @property
    def config(self) -> Config: ...

    def get_room(self, room_id: str) -> Room | None: ...
