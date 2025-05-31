from nio import Event, MatrixRoom

class Context:
    def __init__(self, bot, room: MatrixRoom, event: Event):
        self.bot     = bot
        self.room    = room
        self.event   = event

        self.prefix  = bot.prefix
        self.body    = getattr(event, "body", "")
        self.sender  = event.sender

        # Room informations extracted.
        self.room_id   = room.room_id
        self.room_name = room.name

        if self.prefix and self.body.startswith(self.prefix):
            parts        = self.body[len(self.prefix):].split()
            self.command = parts[0].lower() if parts else None
            self.args    = parts[1:]
        else:
            self.command = None
            self.args    = []

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
