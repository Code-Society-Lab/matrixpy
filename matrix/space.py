from matrix.room import Room, make_room


class Space(Room, room_type="m.space"):
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

            children.append(make_room(matrix_room, self._client))

        return children
