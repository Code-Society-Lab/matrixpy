from matrix import Bot, Context
from matrix.errors import CommandNotFoundError, MissingArgumentError

bot = Bot(config="examples/config.yaml")


@bot.error(CommandNotFoundError)
async def global_error(error: CommandNotFoundError) -> None:
    print(f"Global error handler {error}.")


@bot.command("div")
async def division(ctx: Context, a: int, b: int) -> None:
    c = a / b
    await ctx.reply(f"{a} / {b} = {c}")


@division.error(ZeroDivisionError)
async def div_error(ctx: Context, error: ZeroDivisionError) -> None:
    print(f"Operation Not Allowed: {error}")
    await ctx.reply(f"Operation not allowed: {error}")


@division.error(ValueError)
async def val_error(ctx: Context, error: ValueError) -> None:
    print(f"ValueError: {error}")
    await ctx.reply(f"ValueError: {error}")


@division.error(MissingArgumentError)
async def command_error(ctx: Context, error: MissingArgumentError) -> None:
    await ctx.reply(f"{error}")


bot.start()
