from matrix import Bot, Context, cooldown

bot = Bot(config="examples/config.yaml")


@bot.command(cooldown=(2, 15))
async def cooldown_command(ctx):
    await ctx.reply("This is limited to 2 uses per 15s per user.")


@cooldown(rate=2, period=10)
@bot.command("hello")
async def hello_world(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Hello World.")


bot.start()
