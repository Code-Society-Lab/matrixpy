from typing import Optional
from nio import AsyncClient, Event, MatrixRoom
from .errors import MatrixError
from .message import Message
from .content import (
    TextContent,
    MarkdownMessage,
    NoticeContent,
    FileContent,
    ImageContent,
)
from matrix.types import File, Image


class Room:
    """Represents a Matrix room and provides methods to interact with it."""

    def __init__(self, matrix_room: MatrixRoom, client: AsyncClient) -> None:
        self.matrix_room = matrix_room
        self.client = client

        self.name = matrix_room.name
        self.room_id = matrix_room.room_id

    async def send(
        self,
        content: str | None = None,
        *,
        raw: bool = False,
        notice: bool = False,
        file: File | None = None,
        image: Image | None = None,
    ) -> Message:
        """Send a message to the room."""
        if content:
            return await self.send_text(content, raw=raw, notice=notice)

        if file:
            return await self.send_file(file)

        if image:
            return await self.send_image(image)
        raise ValueError("You must provide content, file, or image to send.")

    async def send_text(
        self, content: str, *, raw: bool = False, notice: bool = False
    ) -> Message:
        """Send a text message.

        Formatted in Markdown by default. Can be unformatted with `raw=True` or sent as a notice with `notice=True`.
        """
        if notice:
            payload = NoticeContent(content)
        elif raw:
            payload = TextContent(content)
        else:
            payload = MarkdownMessage(content)

        return await self._send_payload(payload)

    async def send_file(self, file: File) -> Message:
        """Send a file message."""
        payload = FileContent(
            filename=file.filename, url=file.path, mimetype=file.mimetype
        )
        return await self._send_payload(payload)

    async def send_image(self, image: Image) -> Message:
        """Send an image message."""
        payload = ImageContent(
            filename=image.filename,
            url=image.path,
            mimetype=image.mimetype,
        )
        return await self._send_payload(payload)

    async def _send_payload(self, payload) -> Message:
        """Send a BaseMessageContent payload and return a Message object."""
        try:
            resp = await self.client.room_send(
                room_id=self.room_id,
                message_type="m.room.message",
                content=payload.build(),
            )

            return Message(
                room=self,
                event_id=resp.event_id,
                body=getattr(payload, "body", None),
                client=self.client,
            )
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    async def invite_user(self, user_id: str) -> None:
        """
        Invite a user to the room.

        :param user_id: The ID of the user to invite.
        :raises MatrixError: If inviting the user fails.
        """
        try:
            await self.client.room_invite(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to invite user: {e}")

    async def ban_user(self, user_id: str, reason: Optional[str] = None) -> None:
        """
        Ban a user from a room.

        :param user_id: The ID of the user to ban of the room.
        :type user_id: str
        :param reason: The reason to ban the user.
        :type reason: Optional[str]

        :raises MatrixError: If banning the user fails.
        """
        try:
            await self.client.room_ban(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to ban user: {e}")

    async def unban_user(self, user_id: str) -> None:
        """
        Unban a user from a room.

        :param user_id: The ID of the user to unban of the room.
        :type user_id: str

        :raises MatrixError: If unbanning the user fails.
        """
        try:
            await self.client.room_unban(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to unban user: {e}")

    async def kick_user(self, user_id: str, reason: Optional[str] = None) -> None:
        """
        Kick a user from a room.

        :param user_id: The ID of the user to kick of the room.
        :type user_id: str
        :param reason: The reason to kick the user.
        :type reason: Optional[str]

        :raises MatrixError: If kicking the user fails.
        """
        try:
            await self.client.room_kick(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to kick user: {e}")
