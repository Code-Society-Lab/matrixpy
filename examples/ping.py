from matrix import Bot, Context, Cooldown

bot = Bot("examples/config.yaml")


@bot.command("ping")
@Cooldown(rate=2, period=10)
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


bot.start()
