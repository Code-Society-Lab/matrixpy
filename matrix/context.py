import shlex
from nio import Event, MatrixRoom
from typing import TYPE_CHECKING, Optional, Any, List
from matrix.errors import MatrixError


if TYPE_CHECKING:
    from matrix.bot import Bot  # pragma: no cover
    from matrix.command import Command  # pragma: no cover


class Context:
    """
    Represents the context in which a command is executed. Provides
    access to the bot instance, room and event metadata, parsed arguments,
    and other utilities.

    :param bot: The bot instance executing the command.
    :type bot: Bot
    :param room: The Matrix room where the event occurred.
    :type room: MatrixRoom
    :param event: The event that triggered the command or message.
    :type event: Event

    raises MatrixError: If a Matrix operation fails.
    """

    def __init__(self, bot: "Bot", room: MatrixRoom, event: Event):
        self.bot = bot
        self.room = room
        self.event = event

        self.body: str = getattr(event, "body", "")
        self.sender: str = event.sender

        # Room metadata.
        self.room_id: str = room.room_id
        self.room_name: str = room.name

        # Command metdata
        self.prefix: str = bot.prefix
        self.command: Optional[Command] = None
        self._args: List[str] = shlex.split(self.body)

    @property
    def args(self) -> List[str]:
        """
        Returns the list of parsed arguments from the message body.

        If a command is present, the command name is excluded.

        :return: The list of arguments.
        :rtype: List[str]
        """
        if self.command:
            return self._args[1:]
        return self._args

    @property
    def logger(self) -> Any:
        """Logger for instance specific to the current room or event."""
        return self.bot.log.getChild(self.room_id)

    async def send(self, message: str) -> None:
        """
        Send a message to the Matrix room.

        :param message: The message to send.
        :type message: str
        """
        try:
            await self.bot.client.room_send(
                room_id=self.room_id,
                message_type="m.room.message",
                content={"msgtype": "m.text", "body": message}
            )
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")
