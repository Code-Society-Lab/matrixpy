from matrix.bot import Bot
from nio import MatrixRoom, RoomMessageText

bot = Bot("https://matrix.org", prefix="!")


@bot.command()
async def ping(room, event):
    await bot.client.room_send(room.room_id, "m.room.message", {
        "msgtype": "m.text", 
        "body": "Pong!"
    })


bot.start("user id", "password")
