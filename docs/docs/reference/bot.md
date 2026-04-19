# Bot

The `Bot` class is the heart of every matrix.py application. It manages the connection to a Matrix homeserver, registers
commands and event handlers, and drives the main event loop.

```python
from matrix import Bot, Context

bot = Bot()


@bot.command("ping")
async def ping(ctx: Context):
    await ctx.reply("Pong!")


bot.start(config="config.yml")
```

::: matrix.bot.Bot
