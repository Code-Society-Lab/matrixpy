from matrix import Bot, Context, cooldown

bot = Bot("examples/config.yaml")


@bot.command("ping")
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


bot.start()
