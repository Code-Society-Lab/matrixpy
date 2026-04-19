# What is a Check?
A check is a function that runs _before_ your command. It returns:
- `True` - Allow the command to run
- `False` - Block the command and raise [`CheckError`](../reference/errors.md)

See also the [`checks`](../reference/checks.md) reference for built-in check decorators.

# Add a Check
Let's create an admin-only command:
```python
@bot.command()
async def restricted(ctx):
    await ctx.reply("You passed all checks!")


@restricted.check
async def is_admin(ctx):
    admins = ["@alice:example.com", "@bob:example.com"]
    return ctx.sender in admins
```

# Multiple Checks
You can add multiple checks to one command. ALL checks must pass:

```python
@bot.command()
async def restricted(ctx):
    await ctx.reply("You passed all checks!")

@restricted.check
async def check_one(ctx):
    # Must be from a specific room
    allowed_rooms = ["!room1:example.com", "!room2:example.com"]
    return ctx.room_id in allowed_rooms

@restricted.check
async def check_two(ctx):
    # Must not be banned
    banned = ["@troublemaker:example.com"]
    return ctx.sender not in banned
```

Both checks must return `True` for the command to run.

# Global Checks (Bot-Level)
You can apply a check to _all_ commands with `@bot.check`:
```python
@bot.check
async def not_banned(ctx):
    """No banned users can run ANY commands"""
    banned_users = ["@spammer:example.com", "@troll:example.com"]
    return ctx.sender not in banned_users
```
Now this check runs before _every_ command on your bot.

# What is a Cooldown?
A cooldown prevents users from running a command too frequently. It's like a check, but specifically for rate limiting. When exceeded it raises a [`CooldownError`](../reference/errors.md).

### Adding a Cooldown
```python
@bot.command(
    description="Searches for something",
    cooldown=(3, 60.0)  # 3 calls per 60 seconds
)
async def search(ctx, query: str):
    # Simulate expensive operation
    await ctx.reply(f"Searching for: {query}")
```

**Cooldown format:** `(rate, period)`
- `rate` (int): Number of times the command can be called
- `period` (float): Time window in seconds

**Example interpretations:**
- `(1, 10.0)` - Once every 10 seconds
- `(5, 60.0)` - 5 times per minute
- `(10, 3600.0)` - 10 times per hour


### Setting Cooldowns Programmatically
```python
@bot.command()
async def limited(ctx):
    await ctx.reply("This command is rate-limited")

# Set cooldown after command creation
limited.set_cooldown(rate=2, period=30.0)  # 2 times per 30 seconds
```

### Handling Cooldown Errors
When a user hits the cooldown limit, you can tell them how long to wait:

```python
from matrix.errors import CooldownError

@bot.error(CooldownError)
async def handle_cooldown(error):
    # error.retry tells you how many seconds until they can retry
    wait_time = int(error.retry)
    # You can send a message here if you have access to context
    print(f"Cooldown hit! Wait {wait_time} seconds")
```


# Hooks
```python
@command.before_invoke
async def before(ctx):
    # Runs before command

@command.after_invoke
async def after(ctx):
    # Runs after command succeeds
```
