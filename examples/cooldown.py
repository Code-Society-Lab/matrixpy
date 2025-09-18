from matrix import Bot, Context, cooldown
from matrix.errors import CooldownError

bot = Bot("examples/config.yaml")


@bot.command(cooldown=(2, 15))
async def cooldown_command(ctx):
    await ctx.reply("This is limited to 2 uses per 15s per user.")


@cooldown_command.error(CooldownError)
async def cooldown_error(ctx, error):
    print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")
    await ctx.reply(f"⏳ Try again in {error.retry:.1f}s")


@cooldown(2, 10)
@bot.command("hi")
async def hello(ctx: Context):
    print(f"{ctx.sender} invoked {ctx.body} in room {ctx.room_name}.")
    await ctx.reply("Hello World.")


@hello.error(CooldownError)
async def hello_error(ctx, error):
    print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")
    await ctx.reply(f"⏳ Try again in {error.retry:.1f}s")


bot.start()
