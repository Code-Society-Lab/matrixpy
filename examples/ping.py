from matrix import Bot, Context

bot = Bot(config="examples/config.yaml")


@bot.command("ping")
async def ping(ctx: Context) -> None:
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Pong!")


bot.start()
