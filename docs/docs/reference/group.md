# Group

A `Group` is a command that can contain sub-commands, enabling hierarchical command structures. Invoke a sub-command by sending `<prefix><group> <subcommand>`.

```python
from matrix import Bot, Context

bot = Bot(prefix="!")

@bot.group("admin")
async def admin(ctx: Context):
    await ctx.reply("Use a subcommand: kick, ban")

@admin.command("kick")
async def kick(ctx: Context, user: str):
    await ctx.reply(f"Kicking {user}")
```

::: matrix.group.Group
