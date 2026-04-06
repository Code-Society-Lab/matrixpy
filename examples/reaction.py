from nio import MatrixRoom, RoomMessageText, ReactionEvent
from matrix import Bot
from matrix.message import Message

bot = Bot()


@bot.event
async def on_message(room: MatrixRoom, event: RoomMessageText) -> None:
    """
    This function listens for new messages in a room and reacts based
    on the message content.
    """
    room = bot.get_room(room.room_id)
    message = Message(
        room=room,
        event_id=event.event_id,
        body=event.body,
        client=bot.client,
    )

    if event.body.lower().startswith("thanks"):
        await message.react("🙏")

    if event.body.lower().startswith("hello"):
        # Can also react with a text message instead of emoji
        await message.react("hi")

    if event.body.lower().startswith("❤️"):
        await message.react("❤️")


@bot.event
async def on_react(room: MatrixRoom, event: ReactionEvent) -> None:
    """
    This function listens for new member reaction to messages in a room,
    and reacts based on the reaction emoji.
    """
    room = bot.get_room(room.room_id)
    message = Message(
        room=room,
        event_id=event.event_id,
        body=None,
        client=bot.client,
    )
    emoji = event.key

    if emoji == "🙏":
        await message.react("❤️")


bot.start(config="config.yaml")
