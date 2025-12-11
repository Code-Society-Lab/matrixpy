from matrix import Bot, Context, cooldown
from matrix.errors import CooldownError

bot = Bot(config="examples/config.yaml")


# Invoke by using !hello
@cooldown(rate=2, period=10)
@bot.command("hello")
async def hello_command(ctx: Context) -> None:
    await ctx.reply("Hello World.")


@hello_command.error(CooldownError)
async def hello_command_error_handler(ctx: Context, error: CooldownError) -> None:
    print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")
    await ctx.reply(f"⏳ Try again in {error.retry:.1f}s")


# Invoke by using !cooldown_command
@bot.command(cooldown=(1, 10))
async def cooldown_command(ctx: Context) -> None:
    await ctx.reply("This is limited to 1 uses per 10s per user.")


@cooldown_command.error(CooldownError)
async def cooldown_function(ctx: Context, error: CooldownError) -> None:
    print(f"CooldownError invoked: Try again in {error.retry:.1f} seconds.")
    await ctx.reply(f"⏳ Try again in {error.retry:.1f}s")


bot.start()
