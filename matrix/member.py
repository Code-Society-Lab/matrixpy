from matrix.room import Room
from nio import AsyncClient


class Member:
    def __init__(self, user_id: str, client: AsyncClient) -> None:
        self._user_id: str = user_id
        self._client: AsyncClient = client

    @property
    def user_id(self) -> str:
        return self._user_id

    async def get_profile(self) -> dict | None:
        """Get the profile information for this member.

        ## Example

        ```python
        profile = await member.get_profile()
        for key, value in profile.other_info.items():
            print(f"{key}: {value}")
        ```
        """
        profile = await self._client.get_profile(self._user_id)
        return profile if profile else None

    async def get_display_name(self) -> str | None:
        """Get the display name for this member.

        ## Example

        ```python
        display_name = await member.get_display_name()
        print(f"Display name: {display_name}")
        ```
        """
        display_name = await self._client.get_displayname(self._user_id)
        return display_name.displayname if display_name else None

    async def get_avatar_url(self) -> str | None:
        """Get the avatar URL for this member.

        ## Example

        ```python
        avatar_url = await member.get_avatar_url()
        print(f"Avatar URL: {avatar_url}")
        ```
        """
        avatar = await self._client.get_avatar(self._user_id)
        return await self._client.mxc_to_http(avatar.avatar_url) if avatar else None

    async def get_room_power_level(self, room: Room) -> int:
        """Get the power level for this member in a specific room.

        ## Example

        ```python
        level = await member.get_room_power_level(ctx.room)
        print(f"Power level in room {room.room_id}: {level}")
        ```
        """
        power_level = await self._client.room_get_state_event(
            room.room_id, "m.room.power_levels", ""
        )

        content = getattr(power_level, "content", {}) or {}
        users = content.get("users", {})
        default = content.get("users_default", 0)

        return int(users.get(self._user_id, default))

    async def get_presence(self) -> str | None:
        """Get the presence status for this member.

        ## Example

        ```python
        presence = await member.get_presence()
        print(f"Presence status: {presence}")
        ```
        """
        presence = await self._client.get_presence(self._user_id)
        return presence.presence if presence else None

    async def has_permission(self, room: Room, permission: str) -> bool:
        """Check if this member has a specific permission in a room.

        ## Example

        ```python
        has_permission = await member.has_permission(ctx.room, "ban")
        print(f"Has ban permission: {has_permission}")
        ```
        """
        power_level = await self.get_room_power_level(room)
        power_levels_event = await self._client.room_get_state_event(
            room.room_id, "m.room.power_levels", ""
        )

        content = getattr(power_levels_event, "content", {}) or {}
        required_level = content.get(permission, 0)

        return bool(power_level >= required_level)

    async def has_event_permission(self, room: Room, event_type: str) -> bool:
        """Check if this member has permission to send a specific event type in a room.

        ## Example

        ```python
        can_send_message = await member.has_event_permission(ctx.room, "m.room.message")
        print(f"Can send messages: {can_send_message}")
        ```
        """
        power_level = await self.get_room_power_level(room)
        power_levels_event = await self._client.room_get_state_event(
            room.room_id, "m.room.power_levels", ""
        )

        content = getattr(power_levels_event, "content", {}) or {}
        events = content.get("events", {})
        required_level = events.get(event_type, 0)

        return bool(power_level >= required_level)
