import shlex
from nio import Event, MatrixRoom


class Context:
    def __init__(self, bot, room: MatrixRoom, event: Event):
        self.bot = bot
        self.room = room
        self.event = event

        self.body = getattr(event, "body", "")
        self.sender = event.sender

        # Room informations extracted.
        self.room_id = room.room_id
        self.room_name = room.name

        self.prefix = bot.prefix
        self.command = None
        self._args = shlex.split(self.body)

    @property
    def args(self):
        if self.command:
            return self._args[1:]
        return self._args

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
            print(f"Failed to send message: {e}")
            raise

    @property
    def logger(self):
        """Logger for instance specific to the current room or event."""
        return self.bot.log.getChild(self.room_id)
