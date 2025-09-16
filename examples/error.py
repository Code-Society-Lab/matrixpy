from matrix import Bot, Context, cooldown
from matrix.errors import CommandNotFoundError, MissingArgumentError
bot = Bot("examples/config.yaml")


@bot.error(CommandNotFoundError)
async def global_error(error):
    print(f"Glable error handler {error}.")


@bot.command("div")
async def division(ctx: Context, a: int, b: int):
    c = a / b
    await ctx.reply(c)


@division.error(ZeroDivisionError)
async def div_error(ctx, error):
    print(f"Operation Not Allowed: {error}")
    await ctx.reply(f"Operation not allowed: {error}")


@division.error(ValueError)
async def val_error(ctx, error):
    print(f"ValueError: {error}")
    await ctx.reply(f"ValueError: {error}")


@division.error(MissingArgumentError)
async def command_error(ctx, error):
    print(error)
    await ctx.reply(error)


bot.start()
