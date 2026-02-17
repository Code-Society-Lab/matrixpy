import shlex

from nio import Event
from typing import TYPE_CHECKING, Optional, Any, List

from .errors import MatrixError
from .message import Message
from .room import Room
from .types import File, Image

if TYPE_CHECKING:
    from .bot import Bot  # pragma: no cover
    from .command import Command  # pragma: no cover


class Context:
    """Represents the context in which a command is executed. Provides
    access to the bot instance, room and event metadata, parsed arguments,
    and other utilities.
    """

    def __init__(self, bot: "Bot", room: Room, event: Event):
        self.bot = bot
        self.room = room
        self.event = event

        self.body: str = getattr(event, "body", "")
        self.sender: str = event.sender

        # Command metadata
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
        return self.bot.log.getChild(self.room.room_id)

    async def reply(
        self,
        content: str | None = None,
        *,
        raw: bool = False,
        notice: bool = False,
        file: File | None = None,
    ) -> Message:
        """Reply to the command with a message.

        This is a convenience method that sends a message to the room where the
        command was invoked. Supports text messages (with optional markdown
        formatting) and file uploads (including images, videos, and audio).

        See `Room.send()` for detailed usage examples and documentation.

        ## Example

        ```python
        @bot.command()
        async def hello(ctx: Context):
            await ctx.reply("Hello **world**!")

        @bot.command()
        async def status(ctx: Context):
            await ctx.reply("Bot is online!", notice=True)

        @bot.command()
        async def cat(ctx: Context):
            # Upload and send an image
            from PIL import Image as PILImage

            with PILImage.open("cat.jpg") as img:
                width, height = img.size

            with open("cat.jpg", "rb") as f:
                resp, _ = await ctx.room.client.upload(f, content_type="image/jpeg")

            image = Image(
                path=resp.content_uri,
                filename="cat.jpg",
                mimetype="image/jpeg",
                width=width,
                height=height
            )
            await ctx.reply(file=image)
        ```
        """

        try:
            return await self.room.send(
                content,
                raw=raw,
                notice=notice,
                file=file,
            )
        except Exception as e:
            raise MatrixError(f"Failed to send message: {e}")

    async def send_help(self) -> None:
        """Send help from the current command context.

        Displays help text for the current subcommand, command, or the bot's
        general help menu depending on what's available in the context. The help
        hierarchy is: subcommand help > command help > bot help.

        ## Example

        ```python
        @bot.group()
        async def config(ctx: Context):
            # If user runs just "!config" with no subcommand
            await ctx.send_help()
        ```
        """
        if self.subcommand:
            await self.reply(self.subcommand.help)
            return

        if self.command:
            await self.reply(self.command.help)
            return

        await self.bot.help.execute(self)
