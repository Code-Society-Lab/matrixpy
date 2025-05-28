from matrix.bot import Bot, Context

bot = Bot("https://matrix.org", prefix="!")


@bot.command()
async def ping(ctx: Context):
  print(f"{ctx.event.sender} sent a message.")
  await ctx.send("Pong!")

bot.start("user id", "password")
