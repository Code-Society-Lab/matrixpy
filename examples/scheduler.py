from matrix import Bot, Context

bot = Bot(config="examples/config.yaml")

room_id = "!your_room_id:matrix.org"  # Replace with your room ID

room = bot.get_room(room_id)


@bot.command("ping")
async def ping(ctx: Context) -> None:
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


@bot.schedule("* * * * *")
async def scheduled_task() -> None:
    print("This task runs every minute.")
    await room.send(message="Scheduled ping!")


@bot.schedule("0 * * * *")
async def hourly_task() -> None:
    print("This task runs every hour.")
    await room.send(message="This is your hourly update!")


@bot.schedule("0 9 * * 1-5")
async def weekday_morning_task() -> None:
    print("This task runs every weekday at 9 AM.")
    await room.send(message="Good morning! Here's your weekday update!")


bot.start()
