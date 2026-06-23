from __future__ import annotations

from .room import Room


class Space(Room):
    def get_children(self) -> list[Room]:
        """Return the child rooms and spaces of this space.

        ## Example

        ```python
        space = bot.get_space("!space123:matrix.org")

        for child in space.get_children():
            print(child.name)
        ```
        """
        children = []

        for room_id in self.children:
            matrix_room = self._client.rooms.get(room_id)

            if not matrix_room:
                continue

            room_cls = Space if matrix_room.room_type == "m.space" else Room
            children.append(room_cls(matrix_room, self._client))

        return children
