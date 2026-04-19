# Bigger Bot - Extension

As your bot grows, keeping everything in a single file becomes harder to manage. That's where [`Extension`](../reference/extension.md) comes in, it lets you split your code into separate modules.

Here's an example file structure for a larger bot:
```
.
├─ bot
│  ├─ __init__.py
│  ├─ helpers.py
│  ├─ my_bot.py
│  └─ extensions
│     ├─ __init__.py
│     ├─ dev.py
│     ├─ moderation.py
│     └─ weather.py
```

The `bot` package contains everything related to your bot, with `my_bot.py` as its entry point. It's responsible for importing and registering all extensions. This is just one way to structure your project, extensions are flexible enough to fit whatever organization works best for you.

## What is an `Extension`?

An `Extension` is a mechanism that lets you split your bot's functionality across multiple modules. Extensions support everything a [`Bot`](../reference/bot.md) supports, including:

- Event handlers
- Error handlers
- Commands
- Groups
- Checks
- Cron tasks

...and more.

## How to Create an Extension

Below is a basic definition of a `moderation` extension. It registers two commands, `ban` and `kick`, and an event handler for `on_member_ban`:

```python
from nio import RoomMemberEvent
from matrix import Extension, Context
from bot.helpers import is_admin

extension = Extension("moderation")


@is_admin
@extension.command(description="Ban a member")
async def ban(ctx: Context, username: str) -> None:
    ...


@is_admin
@extension.command(description="Kick a member")
async def kick(ctx: Context, username: str) -> None:
    ...


@extension.event
def on_member_ban(event: RoomMemberEvent) -> None:
    # Triggered when a user is banned
    ...
```

## How to Register Extensions

To use an extension, import it and pass it to `bot.load_extension()`:

```python
from matrix import Bot, Context
from bot.extensions.moderation import extension as moderation_extension
from bot.extensions.weather import extension as weather_extension
from bot.extensions.dev import extension as dev_extension

bot = Bot()


@bot.command(description="Respond with 'Pong!'")
async def ping(ctx: Context):
    await ctx.reply("Pong!")


bot.load_extension(moderation_extension)
bot.load_extension(weather_extension)

# Load the dev extension only in development environments
if in_dev:
    bot.load_extension(dev_extension)


bot.start(config="config.yml")
```

Your bot now has three extensions registered: `moderation`, `weather`, and `dev` (the last one only in development).

You can also unload an extension using `bot.unload_extension()`.
