# What is a Command Group?
A command group is a special type of commands that groups multiple commands together. See the [`Group`](../reference/group.md) reference for the full API.

Instead of having:
- `!math_add`
- `!math_subtract`
- `!math_multiply`
- `!math_divide`

You can have:
- `!math add`
- `!math subtract`
- `!math multiply`
- `!math divide`

Groups are especially useful for:
- **Organization**: Related commands are grouped logically
- **Shorter names**: `add` instead of `math_add`
- **Help system**: Groups appear together in help menus
- **Namespace**: Prevents command name conflicts

# Creating a Group
```python
@bot.group(description="Mathematical operations")
async def math(ctx: Context):
    # This runs when someone types just "!math"
    await ctx.reply("Available commands: add, subtract, multiply, divide")
```

# Adding Commands to the Group
Use the group name as a decorator:
```python
@math.command(description="Adds two numbers")
async def add(ctx: Context, a: int, b: int):
    result = a + b
    await ctx.reply(f"{a} + {b} = {result}")


@math.command(description="Subtracts two numbers")
async def subtract(ctx: Context, a: int, b: int):
    result = a - b
    await ctx.reply(f"{a} - {b} = {result}")


@math.command(description="Multiplies two numbers")
async def multiply(ctx: Context, a: int, b: int):
    result = a * b
    await ctx.reply(f"{a} × {b} = {result}")

@math.command(description="Divides two numbers")
async def divide(ctx: Context, a: int, b: int):
    result = a / b
    await ctx.reply(f"{a} / {b} = {result}")
```

### How Users Interact with Groups

| Command | Result |
|---------|--------|
| `!math` | Available commands: add, subtract, multiply, divide |
| `!math add 5 3` | 5 + 3 = 8 |
| `!math subtract 10 4` | 10 - 4 = 6 |
| `!math multiply 10 4` | 10 * 4 = 40 |
| `!math divide 10 2` | 10 / 2 = 5 |


# Organizing Groups in Separate Modules
As your bot grows, you'll want to organize related commands into separate files. The `@group` factory function makes this easy by creating groups that can be imported and registered later.

Create a file for your group (e.g., `groups/math_group.py`):
```python
# groups/math_group.py
from matrix import group


@group("math", description="Mathematical operations")
async def math(ctx: Context) -> None:
    await ctx.reply("Available commands: add, subtract, multiply, divide")


@math.command(description="Adds two numbers")
async def add(ctx: Context, a: int, b: int):
    result = a + b
    await ctx.reply(f"{a} + {b} = {result}")

...
```

### Registering the Group in Your Bot

Import and register the group in your main bot file:
```python
# bot.py
from matrix import Bot
from groups.math_group import math

bot = Bot(config="config.yaml")

...

bot.register_group(math)

bot.start()
```

### Why Use Separate Modules?

- **Better organization** - Related commands are grouped together
- **Easier maintenance** - Each file has a single responsibility
- **Reusability** - Groups can be shared across multiple bots
- **Cleaner code** - Main bot file stays focused and readable
