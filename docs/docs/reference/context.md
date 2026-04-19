# Context

`Context` is passed as the first argument to every command callback. It bundles the bot instance, the room the message arrived in, the originating event, and the parsed arguments — giving commands everything they need to respond.

```python
from matrix import Bot, Context

bot = Bot()

@bot.command("info")
async def info(ctx: Context):
    await ctx.reply(f"Sent by {ctx.sender} in {ctx.room.room_id}")
```

::: matrix.context.Context
