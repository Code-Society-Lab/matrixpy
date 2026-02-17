from typing import Any

from nio import AsyncClient, MatrixRoom

from matrix.errors import MatrixError
from matrix.message import Message
from matrix.content import (
    TextContent,
    MarkdownMessage,
    NoticeContent,
    FileContent,
    ImageContent,
    BaseMessageContent,
    ReplyContent,
)
from matrix.types import File, Image


class Room:
    """Represents a Matrix room and provides methods to interact with it."""

    def __init__(self, matrix_room: MatrixRoom, client: AsyncClient) -> None:
        self._matrix_room: MatrixRoom = matrix_room
        self._client: AsyncClient = client

    @property
    def matrix_room(self) -> MatrixRoom:
        """Access to underlying MatrixRoom object."""
        return self._matrix_room

    @property
    def client(self) -> AsyncClient:
        """Access to the Matrix client."""
        return self._client

    @property
    def name(self) -> str | None:
        """Room display name."""
        return self._matrix_room.name  # type: ignore[no-any-return]

    @property
    def room_id(self) -> str:
        """Room ID."""
        return self._matrix_room.room_id  # type: ignore[no-any-return]

    @property
    def display_name(self) -> str:
        """Room display name (alias for name)."""
        return self._matrix_room.display_name  # type: ignore[no-any-return]

    @property
    def topic(self) -> str | None:
        """Room topic."""
        return self._matrix_room.topic  # type: ignore[no-any-return]

    @property
    def member_count(self) -> int:
        """Number of members in the room."""
        return self._matrix_room.member_count  # type: ignore[no-any-return]

    @property
    def encrypted(self) -> bool:
        """Whether the room is encrypted."""
        return self._matrix_room.encrypted  # type: ignore[no-any-return]

    def __getattr__(self, name: str) -> Any:
        """
        Fallback to MatrixRoom for attributes not explicitly defined.

        This allows access to any MatrixRoom attribute not wrapped by this class.
        See matrix-nio's MatrixRoom documentation for available attributes.

        https://matrix-nio.readthedocs.io/en/latest/nio.html#nio.rooms.MatrixRoom
        """
        try:
            return getattr(self._matrix_room, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            ) from None

    async def send(
        self,
        content: str | None = None,
        *,
        raw: bool = False,
        notice: bool = False,
        file: File | None = None,
        image: Image | None = None,
    ) -> Message:
        """Send a message to the room.

        This is a convenience method that automatically routes to the appropriate
        send method based on the provided arguments. Supports text messages (with
        optional markdown formatting), file uploads, and image uploads.

        ## Example

        ```python
        # Send a markdown-formatted text message
        await room.send("Hello **world**!")

        # Send raw text without markdown
        await room.send("Hello world!", raw=True)

        # Send a notice message
        await room.send("Bot is starting up...", notice=True)

        # Send a file
        file = File(filename="document.pdf", path="mxc://...", mimetype="application/pdf")
        await room.send(file=file)

        # Send an image
        image = Image(filename="photo.jpg", path="mxc://...", mimetype="image/jpeg", width=800, height=600)
        await room.send(image=image)
        ```
        """
        if content:
            return await self.send_text(content, raw=raw, notice=notice)

        if file:
            return await self.send_file(file)

        if image:
            return await self.send_image(image)
        raise ValueError("You must provide content, file, or image to send.")

    async def send_text(
        self,
        content: str,
        *,
        raw: bool = False,
        notice: bool = False,
        reply_to: str | None = None,
    ) -> Message:
        """Send a text message to the room.

        By default, messages are formatted using Markdown. You can send raw unformatted
        text with `raw=True`, or send a notice message (typically used for bot status
        updates) with `notice=True`.

        ## Example

        ```python
        # Send markdown-formatted message
        await room.send_text("**Bold** and *italic* text")

        # Send raw text without formatting
        await room.send_text("This is plain text", raw=True)

        # Send a notice message
        await room.send_text("Bot restarted successfully", notice=True)

        # Reply to another message
        await room.send_text("Bot restarted successfully", replay_to=message.id)
        ```
        """
        payload: TextContent

        if reply_to:
            payload = ReplyContent(content, reply_to_event_id=reply_to)
        elif notice:
            payload = NoticeContent(content)
        elif raw:
            payload = TextContent(content)
        else:
            payload = MarkdownMessage(content)

        return await self._send_payload(payload)

    async def send_file(self, file: File) -> Message:
        """Send a file to the room.

        The file must be uploaded to the Matrix content repository before sending.
        Use the room's client upload method to get the MXC URI for the file.

        ## Example

        ```python
        # Upload file first, then send
        with open("document.pdf", "rb") as f:
            resp, _ = await room.client.upload(f, content_type="application/pdf")

        file = File(
            filename="document.pdf",
            path=resp.content_uri,
            mimetype="application/pdf"
        )
        await room.send_file(file)
        ```
        """
        payload = FileContent(
            filename=file.filename, url=file.path, mimetype=file.mimetype
        )
        return await self._send_payload(payload)

    async def send_image(self, image: Image) -> Message:
        """Send an image to the room.

        The image must be uploaded to the Matrix content repository before sending.
        Use the room's client upload method to get the MXC URI for the image.

        ## Example

        ```python
        from PIL import Image as PILImage

        # Get image dimensions
        with PILImage.open("photo.jpg") as img:
            width, height = img.size

        # Upload image first
        with open("photo.jpg", "rb") as f:
            resp, _ = await room.client.upload(f, content_type="image/jpeg")

        image = Image(
            filename="photo.jpg",
            path=resp.content_uri,
            mimetype="image/jpeg",
            width=width,
            height=height
        )
        await room.send_image(image)
        ```
        """
        payload = ImageContent(
            filename=image.filename,
            url=image.path,
            mimetype=image.mimetype,
            height=image.height,
            width=image.width,
        )
        return await self._send_payload(payload)

    async def _send_payload(self, payload: BaseMessageContent) -> Message:
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
        """Invite a user to the room.

        The bot must have permission to invite users to the room. The user will
        receive an invitation that they can accept or decline.

        ## Example

        ```python
        # Invite a user by their Matrix ID
        await room.invite_user("@alice:example.com")
        ```
        """
        try:
            await self.client.room_invite(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to invite user: {e}")

    async def ban_user(self, user_id: str, reason: str | None = None) -> None:
        """Ban a user from the room.

        The bot must have permission to ban users. Banned users cannot rejoin
        the room until they are unbanned. Optionally provide a reason for the ban.

        ## Example

        ```python
        # Ban a user without a reason
        await room.ban_user("@spammer:example.com")

        # Ban a user with a reason
        await room.ban_user("@spammer:example.com", reason="Spam and harassment")
        ```
        """
        try:
            await self.client.room_ban(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to ban user: {e}")

    async def unban_user(self, user_id: str) -> None:
        """Unban a user from the room.

        The bot must have permission to unban users. This removes the ban,
        allowing the user to rejoin the room if invited or if the room is public.

        ## Example

        ```python
        # Unban a previously banned user
        await room.unban_user("@alice:example.com")
        ```
        """
        try:
            await self.client.room_unban(room_id=self.room_id, user_id=user_id)
        except Exception as e:
            raise MatrixError(f"Failed to unban user: {e}")

    async def kick_user(self, user_id: str, reason: str | None = None) -> None:
        """Kick a user from the room.

        The bot must have permission to kick users. Unlike banning, kicked users
        can rejoin the room if they have an invite or if the room is public.
        Optionally provide a reason for the kick.

        ## Example

        ```python
        # Kick a user without a reason
        await room.kick_user("@troublemaker:example.com")

        # Kick a user with a reason
        await room.kick_user("@troublemaker:example.com", reason="Violating room rules")
        ```
        """
        try:
            await self.client.room_kick(
                room_id=self.room_id, user_id=user_id, reason=reason
            )
        except Exception as e:
            raise MatrixError(f"Failed to kick user: {e}")
