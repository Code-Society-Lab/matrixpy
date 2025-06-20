from matrix.bot import Bot
from nio import RoomMessageText

bot = Bot("examples/config.yaml")


@bot.event(event_spec=RoomMessageText)
async def react_event(room, event):
    room = bot.get_room(room.room_id)
    if event.body.lower().startswith("thanks"):
        await room.send(event=event, key="🙏")

    if event.body.lower().startswith("hello"):
        # Can also react with a text message instead of emoji
        await room.send(event=event, key="hi")


bot.start()
