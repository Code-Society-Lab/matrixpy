# Checks

Checks are decorators that gate command execution. They run before the command callback and can block invocation by raising a `CheckError`. matrix.py ships with a built-in `cooldown` check; you can also write custom checks with `Registry.add_check`.

```python
from matrix import Bot, Context
from matrix.checks import cooldown

bot = Bot()

@bot.command("roll")
@cooldown(rate=1, period=10.0)
async def roll(ctx: Context):
    await ctx.reply("🎲 You rolled a 6!")
```

::: matrix.checks
