from typing import Protocol

from matrix.room import Room


class BotLike(Protocol):
    prefix: str | None

    def get_room(self, room_id: str) -> Room: ...
