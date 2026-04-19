# Message

`Message` represents a Matrix room message and exposes methods to react to, edit, or reply to it. Instances are obtained from `Context.message` or event listener callbacks.

```python
from matrix import Bot, Context

bot = Bot()

@bot.command("like")
async def like(ctx: Context):
    await ctx.message.react("👍")
```

::: matrix.message.Message
