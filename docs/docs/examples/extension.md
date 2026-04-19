# Extension

Demonstrates how to split a bot into modules using [`Extension`](../reference/extension.md) and how to organise related commands into a [`Group`](../reference/group.md).

```python
--8<-- "examples/extension.py"
```

Key points:

- `Extension("math")` creates a standalone module. It supports commands, groups, events, checks, and error handlers — everything `Bot` supports.
- `@extension.group("math")` creates a command group. Sub-commands are registered with `@math_group.command()` and invoked as `!math add`, `!math subtract`, etc.
- Per-command error handlers work the same as on `Bot`: `@divide.error(ZeroDivisionError)` handles division by zero inside the group.

To load this extension in your bot:

```python
from matrix import Bot
from math_extension import extension as math_extension

bot = Bot()
bot.load_extension(math_extension)
bot.start(config="config.yaml")
```

See the [Bigger Bot guide](../guides/bigger-bot.md) for a full project layout using multiple extensions.
