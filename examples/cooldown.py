from matrix import Bot, Context, cooldown

bot = Bot("examples/config.yaml")

@bot.command(cooldown=(2, 15))
async def cooldown_command(ctx):
    await ctx.reply("This is limited to 2 uses per 15s per user.")


@cooldown(2, 10)
@bot.command("hi")
async def hi_cooldown(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Hello World.")


bot.start()
