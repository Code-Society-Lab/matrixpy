# Command

A `Command` wraps an async callback together with its metadata (name, description, usage, cooldown, and checks). Commands are normally created via the `@bot.command()` decorator rather than instantiated directly.

```python
from matrix import Bot, Context

bot = Bot()

@bot.command("greet", description="Greet a user by name", usage="<name>")
async def greet(ctx: Context, name: str):
    await ctx.reply(f"Hello, {name}!")
```

::: matrix.command.Command
