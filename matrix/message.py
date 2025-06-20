from matrix.errors import MatrixError
import markdown
from typing import Dict, Optional


class Message:
    """
    Handle sending messages in a Matrix room.

    This class provides methods to send messages to a Matrix room, including
    formatting the message content as either plain text or HTML.

    :param bot: The bot instance to use for messages.
    :type bot: Bot
    """
    MESSAGE_TYPE = "m.room.message"
    MATRIX_CUSTOM_HTML = "org.matrix.custom.html"
    TEXT_MESSAGE_TYPE = "m.text"

    def __init__(self, bot) -> None:
        self.bot = bot

    async def _send_to_room(
        self,
        room_id: str,
        content: Dict,
        message_type: str = MESSAGE_TYPE
    ) -> None:
        """
        Send a message to the Matrix room.

        :param room_id: The ID of the room to send the message to.
        :type room_id: str
        :param content: The matrix JSON payload.
        :type content: Dict
        :param message_type: The type of the message.
        :type message_type: str

        :raise MatrixError: If sending the message fails.
        """
        try:
            await self.bot.client.room_send(
                room_id=room_id,
                message_type=message_type,
                content=content,
            )
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    def _make_content(self, body: str, html: Optional[bool]) -> Dict:
        """
        Create the content dictionary for a message.

        :param body: The body of the message.
        :type body: str
        :param html: Wheter to format the message as HTML.
        :type html: bool

        :return: The content of the dictionary.
        """

        base: Dict = {
            "msgtype": self.TEXT_MESSAGE_TYPE,
            "body": body,
        }
        if html:
            html_body = markdown.markdown(body, extensions=["nl2br"])
            base["format"] = self.MATRIX_CUSTOM_HTML
            base["formatted_body"] = html_body

        return base

    async def send(
        self, room_id: str,
        message: str,
        format_markdown: Optional[bool] = True
    ) -> None:
        """
        Send a message to a Matrix room.

        :param room_id: The ID of the room to send the message to.
        :type room_id: str
        :param message: The message to send.
        :type message: str
        :param format_markdown: Whether to format the message as Markdown
            (default to True).
        :type format_markdown: bool
        """
        await self._send_to_room(
            room_id=room_id,
            content=self._make_content(message, format_markdown),
        )
