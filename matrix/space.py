import asyncio

from matrix.message import Message
from typing import Self
from matrix.room import Room, make_room

from matrix.types import File


class Space(Room, room_type="m.space"):
    def get_children(self, depth: int = 1) -> list[Room | Self]:
        """Return the child rooms and spaces of this space that the bot has joined.

        Children the bot has not joined are silently omitted. Use `depth` to
        recursively collect children of sub-spaces. `depth=1` returns direct
        children only (default).

        ## Example

        ```python
        space = bot.get_space("!space123:matrix.org")

        for child in space.get_children():
            print(child.name)

        for child in space.get_children(depth=3):
            print(child.name)
        ```
        """
        children: list[Room | Self] = []

        if depth < 0:
            raise ValueError(f"depth must be a non-negative integer, got {depth}")

        if depth == 0:
            return []

        for room_id in self.children:
            matrix_room = self._client.rooms.get(room_id)

            if not matrix_room:
                continue

            child = make_room(matrix_room, self._client)
            children.append(child)

            if isinstance(child, Space) and depth > 1:
                children.extend(child.get_children(depth - 1))

        return children

    async def broadcast(
        self,
        content: str | None = None,
        *,
        raw: bool = False,
        notice: bool = False,
        file: File | None = None,
        depth: int = 1,
    ) -> list[Message]:
        """Broadcasts a message to all rooms in this space.

        Supports text messages (with optional markdown formatting)
        and file uploads (including images, videos, and audio).

        Children the bot has not joined are silently omitted. Use `depth` to
        recursively broadcast to children of sub-spaces. `depth=1` broadcasts
        to direct children only (default).

        ## Example

        ```python
        # Broadcast a markdown-formatted text message
        await space.broadcast("Hello **world**!")

        # Broadcast a notice message
        await space.broadcast("Event started", notice=True)

        # Broadcast a file
        file = File(path="mxc://...", filename="document.pdf", mimetype="application/pdf")
        await space.broadcast(file=file)

        # Broadcast an image
        image = Image(path="mxc://...", filename="photo.jpg", mimetype="image/jpeg", width=800, height=600)
        await space.broadcast(file=image)

        # Broadcast a notice message to space's rooms and the rooms of its subspaces
        await space.broadcast("New Announcement", notice=True, depth=2)
        ```
        """
        rooms = filter(
            lambda room: not isinstance(room, Space), self.get_children(depth=depth)
        )
        async_send = [
            room.send(content, raw=raw, notice=notice, file=file) for room in rooms
        ]
        return await asyncio.gather(*async_send)
