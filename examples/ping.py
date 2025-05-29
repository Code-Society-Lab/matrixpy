from matrix.bot import Bot, Context

bot = Bot("https://matrix.org", prefix="!")


@bot.command("ping")
async def ping(ctx: Context):
  print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
  await ctx.send("Pong!")

bot.start("user id", "password")
