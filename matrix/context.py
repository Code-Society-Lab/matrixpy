from nio import Event, MatrixRoom

class Context:
    def __init__(self, bot, room: MatrixRoom, event: Event):
        self.bot     = bot
        self.room    = room
        self.event   = event

    async def send(self, message: str):
        await self.bot.client.room_send(
            self.room.room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": message}
        )