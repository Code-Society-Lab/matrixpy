from matrix import Bot, Context

bot = Bot(config="config.yaml")


@bot.command("ping")
async def ping(ctx: Context) -> None:
    await ctx.reply("Pong!")


bot.start()
