from matrix.bot import Bot, Context, Config


config = Config(config_file='examples/config.yaml')
bot = Bot(config)


@bot.command("ping")
async def ping(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.send("Pong!")


bot.start()
