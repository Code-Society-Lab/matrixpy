from matrix import Extension, Context

extension = Extension("math")


@extension.group("math", description="Math Group")
async def math_group(ctx: Context):
    pass


@math_group.command()
async def add(ctx: Context, a: int, b: int):
    await ctx.reply(f"**{a} + {b} = {a + b}**")


@math_group.command()
async def subtract(ctx: Context, a: int, b: int):
    await ctx.reply(f"{a} - {b} = {a - b}")


@math_group.command()
async def multiply(ctx: Context, a: int, b: int):
    await ctx.reply(f"{a} x {b} = {a * b}")


@math_group.command()
async def divide(ctx: Context, a: int, b: int):
    await ctx.reply(f"{a} ÷ {b} = {a / b}")


@divide.error(ZeroDivisionError)
async def divide_error(ctx: Context, error):
    await ctx.reply(f"Divide error: {error}")


"""
# bot.py

from matrix import Bot
from math_extension import extension as math_extension

bot = Bot()


bot.load_extension(math_extension)
bot.start(config="config.yaml")
"""
