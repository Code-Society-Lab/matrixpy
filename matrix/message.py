from typing import TYPE_CHECKING
from nio import AsyncClient
from matrix.content import ReactionContent, EditContent
from matrix.errors import MatrixError

if TYPE_CHECKING:
    from .room import Room  # pragma: no cover


class Message:
    """Represents a Matrix message with methods to interact with it."""

    def __init__(
        self, *, room: "Room", event_id: str, body: str | None, client: AsyncClient
    ) -> None:
        self._room = room
        self._event_id = event_id
        self._body = body
        self._client = client

    @property
    def room(self) -> "Room":
        """The room this message was sent in."""
        return self._room

    @property
    def id(self) -> str:
        """The event ID of this message."""
        return self._event_id

    @property
    def event_id(self) -> str:
        """The event ID of this message (alias for id)."""
        return self._event_id

    @property
    def body(self) -> str | None:
        """The text content of this message."""
        return self._body

    @property
    def client(self) -> AsyncClient:
        """The Matrix client."""
        return self._client

    async def reply(self, body: str) -> "Message":
        """Reply to this message.

        Creates a threaded reply to this message in the same room.

        ## Example
        ```python
        @bot.command()
        async def echo(ctx: Context):
            msg = await ctx.reply("Echo!")
            await msg.reply("Replying to my own message")
        ```
        """
        try:
            return await self.room.send_text(content=body, reply_to=self.id)
        except Exception as e:
            raise MatrixError(f"Failed to send reply: {e}")

    async def react(self, emoji: str) -> None:
        """Add a reaction emoji to this message.

        ## Example
        ```python
        @bot.command()
        async def thumbsup(ctx: Context):
            msg = await ctx.reply("React to this!")
            await msg.react("👍")
        ```
        """
        content = ReactionContent(event_id=self.id, emoji=emoji)

        try:
            await self.client.room_send(
                room_id=self.room.room_id,
                message_type="m.reaction",
                content=content.build(),
            )
        except Exception as e:
            raise MatrixError(f"Failed to add reaction: {e}")

    async def edit(self, new_body: str) -> None:
        """Updates the message content to the new text.

        ## Example

        ```python
        @bot.command()
        async def typo(ctx: Context):
            msg = await ctx.reply("Helo world!")
            await msg.edit("Hello world!")
        ```
        """
        content = EditContent(new_body, original_event_id=self.id)

        try:
            await self.client.room_send(
                room_id=self.room.room_id,
                message_type="m.room.message",
                content=content.build(),
            )
            self._body = new_body
        except Exception as e:
            raise MatrixError(f"Failed to edit message: {e}")

    async def delete(self) -> None:
        """Removes the message content from the room. This action cannot be undone.

        ## Example

        ```python
        @bot.command()
        async def oops(ctx: Context):
            msg = await ctx.reply("Secret info!")
            await msg.delete()
        ```
        """
        try:
            await self.client.room_redact(
                room_id=self.room.room_id,
                event_id=self.id,
            )
        except Exception as e:
            raise MatrixError(f"Failed to delete message: {e}")

    def __repr__(self) -> str:
        return f"<Message id={self.id!r} body={self.body!r}>"
