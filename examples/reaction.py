from asyncio import Event
from nio import MatrixRoom, RoomMessageText, ReactionEvent
from matrix import Bot, Room, Message

bot = Bot()


@bot.event
async def on_message(room: Room, event: RoomMessageText) -> None:
    """
    This function listens for new messages in a room and reacts based
    on the message content.
    """
    room = bot.get_room(room.room_id)
    message = Message.from_event(room, event)

    if message.body.lower().startswith("thanks"):
        await message.react("🙏")

    if message.body.lower().startswith("hello"):
        # Can also react with a text message instead of emoji
        await message.react("hi")

    if message.body.lower().startswith("❤️"):
        await message.react("❤️")


@bot.event
async def on_react(room: Room, event: ReactionEvent) -> None:
    """
    This function listens for new member reaction to messages in a room,
    and reacts based on the reaction emoji.
    """
    room = bot.get_room(room.room_id)
    message = Message.from_event(room, event)

    emoji = event.key

    if emoji == "🙏":
        await message.react("❤️")


bot.start(config="config.yaml")
