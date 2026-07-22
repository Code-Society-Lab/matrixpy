from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Self

from nio import (
    AsyncClient,
    Event,
    RoomGetStateEventError,
    RoomGetStateEventResponse,
)

from matrix.types import Reaction, ReactionEvent
from matrix.content import ReactionContent, EditContent
from matrix.errors import MatrixError
from matrix.api import matrix_call

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

        async for reaction_event in self._iter_reaction_events():
            raw.setdefault(reaction_event.emoji, []).append(reaction_event.sender)

        return [Reaction(key=emoji, senders=senders) for emoji, senders in raw.items()]

    async def _iter_reaction_events(self) -> AsyncIterator[ReactionEvent]:
        """Yield complete reaction relation events for this message."""
        try:
            async for event in self.client.room_get_event_relations(
                room_id=self.room.room_id,
                event_id=self.event_id,
            ):
                emoji = getattr(event, "key", None)
                sender = getattr(event, "sender", None)
                event_id = getattr(event, "event_id", None)

                if emoji and sender and event_id:
                    yield ReactionEvent(
                        emoji=emoji,
                        sender=sender,
                        event_id=event_id,
                    )
        except Exception as e:
            raise MatrixError(f"Failed to fetch reactions: {e}") from e

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

        await matrix_call(
            self.client.room_send(
                room_id=self.room.room_id,
                message_type="m.reaction",
                content=content.build(),
            ),
            error_message="Failed to add reaction",
        )

    async def unreact(self, emoji: str) -> None:
        """Remove this client's reaction emoji from the message.

        If the client has not reacted with the requested emoji, this method
        does nothing.

        ## Example
        ```python
        @bot.command()
        async def toggle(ctx: Context):
            msg = await ctx.reply("React to this!")
            await msg.react("👍")
            await msg.unreact("👍")
        ```
        """
        reaction_event_id = None
        async for reaction_event in self._iter_reaction_events():
            if (
                reaction_event.emoji == emoji
                and reaction_event.sender == self.client.user_id
            ):
                reaction_event_id = reaction_event.event_id
                break

        if reaction_event_id is None:
            return

        await matrix_call(
            self.client.room_redact(
                room_id=self.room.room_id,
                event_id=reaction_event_id,
            ),
            error_message="Failed to remove reaction",
        )

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

        await matrix_call(
            self.client.room_send(
                room_id=self.room.room_id,
                message_type="m.room.message",
                content=content.build(),
            ),
            error_message="Failed to edit message",
        )
        self._body = new_body

    async def delete(self, reason: str | None = None) -> None:
        """Removes the message content from the room. This action cannot be undone.

        Optionally provide a reason that will be visible to room moderators.

        ## Example

        ```python
        @bot.command()
        async def oops(ctx: Context):
            msg = await ctx.reply("Secret info!")
            await msg.delete()

        # Delete with a reason
        await message.delete(reason="Violated room rules")
        ```
        """
        await matrix_call(
            self.client.room_redact(
                room_id=self.room.room_id,
                event_id=self.event_id,
                reason=reason,
            ),
            error_message="Failed to delete message",
        )

    async def _fetch_pinned(self) -> list[str]:
        response = await self.client.room_get_state_event(
            room_id=self.room.room_id,
            event_type="m.room.pinned_events",
        )

        if isinstance(response, RoomGetStateEventResponse):
            return list(response.content.get("pinned", []))
        if isinstance(response, RoomGetStateEventError):
            if response.status_code == "M_NOT_FOUND":
                return []
            raise MatrixError(f"Failed to fetch pinned events: {response.message}")

        raise MatrixError("Unexpected response type when fetching pinned events")

    async def pin(self) -> None:
        """Pin this message to the room.

        ## Example
        ```python
        @bot.command()
        async def pin(ctx: Context):
            await ctx.message.pin()
        ```
        """
        pinned = await self._fetch_pinned()

        if self.event_id in pinned:
            return

        pinned.append(self.event_id)

        await matrix_call(
            self.client.room_put_state(
                room_id=self.room.room_id,
                event_type="m.room.pinned_events",
                content={"pinned": pinned},
            ),
            error_message="Failed to pin message",
        )

    async def unpin(self) -> None:
        """Unpin this message from the room.

        ## Example
        ```python
        @bot.command()
        async def unpin(ctx: Context):
            await ctx.message.unpin()
        ```
        """
        pinned = await self._fetch_pinned()

        if self.event_id not in pinned:
            return

        pinned.remove(self.event_id)

        await matrix_call(
            self.client.room_put_state(
                room_id=self.room.room_id,
                event_type="m.room.pinned_events",
                content={"pinned": pinned},
            ),
            error_message="Failed to unpin message",
        )
