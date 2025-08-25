from matrix import Bot, Context
from matrix.message import Message

bot = Bot("config.yaml")

room_id = "!your_room_id:matrix.org"  # Replace with your room ID


@bot.command("ping")
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


@bot.schedule("* * * * *")
async def scheduled_task():
    print("This task runs every minute.")
    message = Message(bot)
    await message.send(room_id=room_id, message="Scheduled ping!")


bot.start()
