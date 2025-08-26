from matrix import Bot, Context, cooldown

bot = Bot("examples/config.yaml")


@cooldown(rate=1, period=10)
@bot.command("ping")
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


bot.start()
