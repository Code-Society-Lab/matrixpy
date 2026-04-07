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
    message = await room.fetch_message(event.event_id)

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
    message = await room.fetch_message(event.reacts_to)

    if message.key == "🙏":
        await message.react("❤️")


bot.start(config="config.yaml")
