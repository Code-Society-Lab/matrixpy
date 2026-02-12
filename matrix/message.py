from typing import TYPE_CHECKING, Optional
from nio import AsyncClient
from matrix.content import ReactionContent, ReplyContent

if TYPE_CHECKING:
    from .room import Room  # pragma: no cover


class Message:
    def __init__(
        self, *, room: "Room", event_id: str, body: Optional[str], client: AsyncClient
    ) -> None:
        self.room = room
        self.id = event_id
        self.body = body
        self.client = client

    async def reply(self, body: str) -> "Message":
        content = ReplyContent(body, reply_to_event_id=self.id)

        resp = await self.client.room_send(
            room_id=self.room.room_id,
            message_type="m.room.message",
            content=content.build(),
        )

        return Message(
            room=self.room,
            event_id=resp.event_id,
            body=body,
            client=self.client,
        )

    async def react(self, emoji: str) -> None:
        content = ReactionContent(event_id=self.id, emoji=emoji)

        await self.client.room_send(
            room_id=self.room.room_id,
            message_type="m.reaction",
            content=content.build(),
        )
