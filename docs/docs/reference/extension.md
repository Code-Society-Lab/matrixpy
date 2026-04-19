# Extension

Extensions let you split a bot's commands and event handlers across multiple files without losing access to the bot
instance or its config. An extension is loaded at runtime and can hook into bot lifecycle events via `on_load` and
`on_unload`.

```python
# greetings.py
from matrix import Context
from matrix.extension import Extension

greetings = Extension("greetings")


@greetings.command("hello")
async def hello(ctx: Context):
    await ctx.reply("Hello there!")
```

```python
# main.py
from matrix import Bot
from greetings import greetings

bot = Bot()
bot.load_extension(greetings)
bot.start(config="config.yml")
```

::: matrix.extension.Extension
