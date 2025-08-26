from matrix.errors import MatrixError
import markdown
from typing import TYPE_CHECKING, Dict, Optional
from nio import ReactionEvent

if TYPE_CHECKING:
    from matrix.bot import Bot  # pragma: no cover


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

    def __init__(self, bot: "Bot", **kwargs) -> None:
        self.bot = bot
        self.id = kwargs.get("id", None)
        self.content = kwargs.get("content", None)
        self.sender = kwargs.get("sender", None)

    async def _send_to_room(
        self, room_id: str, content: Dict, message_type: str = MESSAGE_TYPE
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

    def _make_content(
        self,
        body: str = "",
        html: Optional[bool] = None,
        reaction: Optional[bool] = None,
        key: Optional[str] = None,
    ) -> Dict:
        """
        Create the content dictionary for a message.

        :param body: The body of the message.
        :type body: str
        :param html: Wheter to format the message as HTML.
        :type html: Optional[bool]
        :param reaction: Wheter to format the context with a reaction event.
        :type reaction: Optional[bool]
        :param key: The reaction to the message.
        :type key: Optional[str]

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

        if reaction:
            base["m.relates_to"] = {
                "event_id": self.id,
                "key": key,
                "rel_type": "m.annotation",
            }

        return base

    async def send_message(
        self,
        room_id: str,
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
        :type format_markdown: Optional[bool]
        """
        await self._send_to_room(
            room_id=room_id,
            content=self._make_content(body=message, html=format_markdown),
        )

    async def send_reaction(self, room_id: str, key: str) -> None:
        """
        Send a reaction to a message from a user in a Matrix room.

        :param room_id: The ID of the room to send the message to.
        :type room_id: str
        :param key: The reaction to the message.
        :type key: str
        """
        await self._send_to_room(
            room_id=room_id,
            content=self._make_content(key=key, reaction=True),
            message_type="m.reaction",
        )

    @staticmethod
    def from_event(bot, event):
        """
        Method to construct a Message instance from event.
        Support regular message events and reaction events.
        """
        if event is None:
            return Message(bot=bot)

        if isinstance(event, ReactionEvent):
            event_id = event.source["content"]["m.relates_to"]["event_id"]
            body = event.source["content"]
        else:
            event_id = event.event_id
            body = event.body

        return Message(
            bot=bot,
            id=event_id,
            content=body,
            sender=event.sender,
        )

