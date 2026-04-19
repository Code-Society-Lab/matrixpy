# Errors

matrix.py uses a structured exception hierarchy so you can catch errors at exactly the right level of specificity. All library exceptions inherit from `MatrixError`.

```python
from matrix.errors import CommandNotFoundError, CooldownError

@bot.error
async def on_error(ctx, error):
    if isinstance(error, CooldownError):
        await ctx.reply(f"Slow down! Retry in {error.retry:.1f}s.")
    elif isinstance(error, CommandNotFoundError):
        await ctx.reply("Unknown command.")
    else:
        raise error
```

::: matrix.errors
