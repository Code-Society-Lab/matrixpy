# Room

`Room` wraps a Matrix room and provides high-level helpers for sending messages of every type — plain text, Markdown, notices, files, images, audio, and video. It delegates unknown attribute access to the underlying `MatrixRoom` from matrix-nio.

```python
from matrix import Bot, Context

bot = Bot()

@bot.command("announce")
async def announce(ctx: Context, *, message: str):
    await ctx.room.send_markdown(f"**Announcement:** {message}")
```

::: matrix.room.Room
