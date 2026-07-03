from typing import Self
from matrix.room import Room, make_room


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
