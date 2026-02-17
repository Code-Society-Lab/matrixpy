from typing import Any

from nio import AsyncClient, MatrixRoom

from matrix.errors import MatrixError
from matrix.message import Message
from matrix.content import (
    BaseMessageContent,
    TextContent,
    MarkdownMessage,
    NoticeContent,
    ReplyContent,
    FileContent,
    ImageContent,
    AudioContent,
    VideoContent,
)
from matrix.types import File, Image, Audio, Video


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
    ) -> Message:
        """Send a message to the room.

        This is a convenience method that automatically routes to the appropriate
        send method based on the provided arguments. Supports text messages (with
        optional markdown formatting) and file uploads (including images, videos, and audio).

        For detailed text message examples, see `Room.send_text()`.
        For detailed file upload examples, see `Room.send_file()`.

        ## Example

        ```python
        # Send a markdown-formatted text message
        await room.send("Hello **world**!")

        # Send a file
        file = File(path="mxc://...", filename="document.pdf", mimetype="application/pdf")
        await room.send(file=file)

        # Send an image
        image = Image(path="mxc://...", filename="photo.jpg", mimetype="image/jpeg", width=800, height=600)
        await room.send(file=image)
        ```
        """
        if content:
            return await self.send_text(content, raw=raw, notice=notice)

        if file:
            return await self.send_file(file)
        raise ValueError("You must provide content or file.")

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
            updates) with `notice=True`. Use `reply_to` to create a threaded reply.

        ## Example

        ```python
        # Send markdown-formatted message
        await room.send_text("**Bold** and *italic* text")

        # Send raw text without formatting
        await room.send_text("This is plain text", raw=True)

        # Send a notice message
        await room.send_text("Bot restarted successfully", notice=True)

        # Reply to another message
        await room.send_text("Replying to you!", reply_to="$event_id")
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
        """Send a file, image, video, or audio to the room.

        Accepts any File object or its subclasses (Image, Video, Audio). The file must
        be uploaded to the Matrix content repository before sending. Use the room's
        client upload method to get the MXC URI.

        The method automatically detects the file type and sends it with the appropriate
        Matrix message type (m.file, m.image, m.video, or m.audio).

        For more information on the upload method, see the matrix-nio documentation:
        https://matrix-nio.readthedocs.io/en/latest/nio.html#nio.AsyncClient.upload

        ## Example

        ```python
        import os

        # Send a document
        file_path = "document.pdf"
        file_size = os.path.getsize(file_path)

        with open(file_path, "rb") as f:
            resp, _ = await room.client.upload(
                f,
                content_type="application/pdf",
                filesize=file_size
            )

        file = File(
            path=resp.content_uri,
            filename="document.pdf",
            mimetype="application/pdf"
        )
        await room.send_file(file)

        # Send an image
        from PIL import Image as PILImage

        image_path = "photo.jpg"

        with PILImage.open(image_path) as img:
            width, height = img.size

        file_size = os.path.getsize(image_path)

        with open(image_path, "rb") as f:
            resp, _ = await room.client.upload(
                f,
                content_type="image/jpeg",
                filesize=file_size
            )

        image = Image(
            path=resp.content_uri,
            filename="photo.jpg",
            mimetype="image/jpeg",
            width=width,
            height=height
        )
        await room.send_file(image)

        # Send a video
        import cv2

        video_path = "video.mp4"

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = int((frame_count / fps) * 1000)
        cap.release()

        file_size = os.path.getsize(video_path)

        with open(video_path, "rb") as f:
            resp, _ = await room.client.upload(
                f,
                content_type="video/mp4",
                filesize=file_size
            )

        video = Video(
            path=resp.content_uri,
            filename="video.mp4",
            mimetype="video/mp4",
            width=width,
            height=height,
            duration=duration
        )
        await room.send_file(video)

        # Send audio
        audio_path = "audio.mp3"
        file_size = os.path.getsize(audio_path)

        with open(audio_path, "rb") as f:
            resp, _ = await room.client.upload(
                f,
                content_type="audio/mpeg",
                filesize=file_size
            )

        audio = Audio(
            path=resp.content_uri,
            filename="audio.mp3",
            mimetype="audio/mpeg",
            duration=180000  # 3 minutes in milliseconds
        )
        await room.send_file(audio)
        ```
        """
        payload: FileContent

        match file:
            case Image():
                payload = ImageContent(
                    filename=file.filename,
                    url=file.path,
                    mimetype=file.mimetype,
                    height=file.height,
                    width=file.width,
                )
            case Audio():
                payload = AudioContent(
                    filename=file.filename,
                    url=file.path,
                    mimetype=file.mimetype,
                    duration=file.duration,
                )
            case Video():
                payload = VideoContent(
                    filename=file.filename,
                    url=file.path,
                    mimetype=file.mimetype,
                    height=file.height,
                    width=file.width,
                    duration=file.duration,
                )
            case _:
                payload = FileContent(
                    filename=file.filename, url=file.path, mimetype=file.mimetype
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
