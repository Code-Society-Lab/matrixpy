from matrix import Bot, Context

bot = Bot()


@bot.command("ping")
async def ping(ctx: Context) -> None:
    await ctx.reply("Pong!")


bot.start(config="config.yaml")
