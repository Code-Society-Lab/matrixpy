from matrix import Bot, Context, cooldown, CooldownError

bot = Bot("examples/config.yaml")


@bot.command(cooldown=(2, 15))
async def cooldown_command(ctx):
    await ctx.reply("This is limited to 2 uses per 15s per user.")


@bot.error()
async def on_error(error):
    if isinstance(error, CooldownError):
        print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")


@cooldown(2, 10)
@bot.command("hi")
async def hello(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Hello World.")


@hello.error
async def hello_error(ctx, error):
    if isinstance(error, CooldownError):
        print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")
        await ctx.reply(f"Try again in {error.retry:.1f} seconds.")


bot.start()
