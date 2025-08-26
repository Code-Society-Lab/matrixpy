import shlex

from nio import Event, MatrixRoom
from typing import TYPE_CHECKING, Optional, Any, List

from .errors import MatrixError
from .message import Message

if TYPE_CHECKING:
    from .bot import Bot  # pragma: no cover
    from .command import Command  # pragma: no cover
    from .group import Group


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
        self.subcommand: Optional[Command] = None
        self._args: List[str] = shlex.split(self.body)

    @property
    def args(self) -> List[str]:
        """
        Returns the list of parsed arguments from the message body.

        If a command is present, the command name is excluded.

        :return: The list of arguments.
        :rtype: List[str]
        """
        if self.subcommand:
            return self._args[2:]

        if self.command:
            return self._args[1:]

        return self._args

    @property
    def logger(self) -> Any:
        """Logger for instance specific to the current room or event."""
        return self.bot.log.getChild(self.room_id)

    async def reply(self, message: str) -> None:
        """
        Send a message to the Matrix room.

        :param message: The message to send.
        :type message: str

        :return: None
        """

        try:
            c = Message(self.bot)
            await c.send(room_id=self.room_id, message=message)
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    async def send_help(self) -> None:
        if self.subcommand:
            await self.reply(self.subcommand.help)
            return

        if self.command:
            await self.reply(self.command.help)
            return

        await self.bot.help.execute(self)
