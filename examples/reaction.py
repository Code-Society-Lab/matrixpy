from matrix import Bot

bot = Bot("examples/config.yaml")


@bot.event
async def on_message(room, event):
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
        # Or directly reply as a message instead of a reaction
        await room.send(message="❤️")


@bot.event
async def on_react(room, event):
    """
    This function listens for new member reaction to messages in a room,
    and reacts based on the reaction emoji.
    """
    room = bot.get_room(room.room_id)

    if event.key == "🙏":
        await room.react(event, "hi")


bot.start()
