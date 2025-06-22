from matrix.bot import Bot

bot = Bot("examples/config.yaml")


@bot.event
async def on_message_react(room, event):
    room = bot.get_room(room.room_id)
    if event.body.lower().startswith("thanks"):
        await room.send(event=event, key="🙏")

    if event.body.lower().startswith("hello"):
        # Can also react with a text message instead of emoji
        await room.send(event=event, key="hi")


@bot.event
async def on_member_react(room, event):
    room = bot.get_room(room.room_id)

    emoji = event.key
    event_id = event.source["content"]["m.relates_to"]["event_id"]

    if emoji == "🙏":
        await room.send(event=event_id, key="❤️")


bot.start()
