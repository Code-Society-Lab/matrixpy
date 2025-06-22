from matrix.bot import Bot

bot = Bot("examples/config.yaml")


@bot.event
async def on_message_react(room, event):
    """
    This function listens for new messages in a room and reacts based
    on the message content.
    """
    room = bot.get_room(room.room_id)
    if event.body.lower().startswith("thanks"):
        await room.send(event=event, key="🙏")

    if event.body.lower().startswith("hello"):
        # Can also react with a text message instead of emoji
        await room.send(event=event, key="hi")

    if event.body.lower().startswith("❤️"):
        await room.send(event=event, message="❤️")


@bot.event
async def on_member_react(room, event):
    """
    This function listens for new member reaction to messages in a room,
    and reacts based on the reaction emoji.
    """
    room = bot.get_room(room.room_id)

    emoji = event.key
    event_id = event.source["content"]["m.relates_to"]["event_id"]

    if emoji == "🙏":
        await room.send(event=event_id, key="❤️")

    if emoji == "❤️":
        await room.send(message="❤️")


bot.start()
