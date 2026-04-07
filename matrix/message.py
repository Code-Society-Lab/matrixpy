from typing import TYPE_CHECKING, Self

from nio import AsyncClient, Event

from matrix.types import Reaction
from matrix.content import ReactionContent, EditContent
from matrix.errors import MatrixError

if TYPE_CHECKING:
    from .room import Room  # pragma: no cover


class Message:
    """Represents a Matrix message with methods to interact with it."""

    def __init__(self, *, room: "Room", event: Event, client: AsyncClient) -> None:
        self._room = room
        self._matrix_event: Event = event
        self._client = client

        self._body = getattr(self._matrix_event, "body", None)

    def __repr__(self) -> str:
        return f"<Message id={self.event_id!r} body={self.body!r}>"

    @property
    def room(self) -> "Room":
        """The room this message was sent in."""
        return self._room

    @property
    def event(self) -> Event:
        """The matrix event of this message"""
        return self._matrix_event

    @property
    def client(self) -> AsyncClient:
        """The Matrix client."""
        return self._client

    @property
    def event_id(self) -> str:
        """The event ID of this message."""
        return str(self._matrix_event.event_id)

    @property
    def body(self) -> str | None:
        """The text content of this message."""
        return self._body

    @property
    def key(self) -> str | None:
        """The key of this message."""
        return getattr(self._matrix_event, "key", None)

    async def fetch_reactions(self) -> list[Reaction]:
        """Fetch all reactions for this message.

        Returns a dict mapping emoji to a list of sender IDs who reacted with it.

        ## Example
        ```python
            @bot.command()
            async def reactions(ctx: Context):
                reactions = await ctx.message.fetch_reactions()

                for emoji, senders in reactions.items():
                    await ctx.reply(f"{emoji}: {len(senders)} reaction(s)")
        ```
        """
        raw: dict[str, list[str]] = {}

        try:
            async for event in self.client.room_get_event_relations(
                room_id=self.room.room_id,
                event_id=self.event_id,
            ):
                emoji = getattr(event, "key", None)
                sender = getattr(event, "sender", None)

                if emoji and sender:
                    raw.setdefault(emoji, []).append(sender)
        except Exception as e:
            raise MatrixError(f"Failed to fetch reactions: {e}")

        return [Reaction(key=emoji, senders=senders) for emoji, senders in raw.items()]

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
            return await self.room.send_text(content=body, reply_to=self.event_id)
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
        content = ReactionContent(event_id=self.event_id, emoji=emoji)

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
        content = EditContent(new_body, original_event_id=self.event_id)

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
                event_id=self.event_id,
            )
        except Exception as e:
            raise MatrixError(f"Failed to delete message: {e}")
