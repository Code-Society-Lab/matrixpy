# Handling Errors
Errors happen! A user might provide invalid input, your API might fail, or someone might misuse a command. Let's make your bot handle these gracefully through error handlers. 

Error handlers can handle any type of exception, built-in by Python, from matrix.py or any other libraries. See the [`errors`](../reference/errors.md) reference for the full list of built-in error types.

# Bot-Level Error Handling
Handle errors across _all_ commands:
```python
@bot.error(MissingArgumentError)
async def missing_arg_handler(error):
    """Handles missing arguments for any command"""
    param_name = error.param.name
    print(f"❌ Missing required parameter: {param_name}")


@bot.error(CheckError)
async def check_failed_handler(error):
    """Handles failed checks"""
    command_name = error.command.name
    print(f"❌ Check failed for command: {command_name}")


@bot.error(CooldownError)
async def cooldown_handler(error):
    """Handles cooldown errors"""
    retry_after = int(error.retry)
    print(f"⏳ On cooldown! Retry in {retry_after} seconds")
```

### Getting the Context
By default, error handlers receive only the error object.

If you need access to the command context (for example, to reply to the user), enable it by setting context=True.

When enabled, the handler will receive the [`Context`](../reference/context.md) as the first argument, followed by the error.

```python
@bot.error(MissingArgumentError, context=True)
async def missing_arg_handler(ctx, error):
    """Handles missing arguments for any command"""
    param_name = error.param.name
    await ctx.reply(f"❌ Missing required parameter: {param_name}")
```

# Extension-Level Error Handling
The same pattern works for [`Extension`](../reference/extension.md):
```python
@extension.error(MissingArgumentError)
async def missing_arg_handler(error):
    """Handles missing arguments for any command"""
    param_name = error.param.name
    print(f"❌ Missing required parameter: {param_name}")

@extension.error(MissingArgumentError, context=True)
async def missing_arg_handler(ctx, error):
    """Handles missing arguments for any command"""
    param_name = error.param.name
    await ctx.reply(f"❌ Missing required parameter: {param_name}")
```

# Command-Level Error Handling
Handle errors for a specific command:
```python
@bot.command(description="Divides two numbers")
async def divide(ctx, a: int, b: int):
    result = a / b
    await ctx.reply(f"{a} ÷ {b} = {result}")

@divide.error()
async def handle_divide_errors(ctx, error):
    """Handle any errors from the divide command"""
    if isinstance(error, ZeroDivisionError):
        await ctx.reply("❌ Cannot divide by zero!")
    elif isinstance(error, ValueError):
        await ctx.reply("❌ Please provide valid numbers!")
    else:
        await ctx.reply(f"❌ An error occurred: {error}")
```

# Matrix.py Error Types

All library exceptions inherit from [`MatrixError`](../reference/errors.md#matrix.errors.MatrixError). See the [`errors`](../reference/errors.md) reference for full details.

| Error | When It Happens |
|-------|-----------------|
| [`MatrixError`](../reference/errors.md#matrix.errors.MatrixError) | Base class for all matrix.py exceptions |
| [`ConfigError`](../reference/errors.md#matrix.errors.ConfigError) | Required config value is missing |
| [`RoomNotFoundError`](../reference/errors.md#matrix.errors.RoomNotFoundError) | Room lookup failed |
| [`RegistryError`](../reference/errors.md#matrix.errors.RegistryError) | Base class for registry exceptions |
| [`AlreadyRegisteredError`](../reference/errors.md#matrix.errors.AlreadyRegisteredError) | A command, group, or extension is registered twice |
| [`CommandError`](../reference/errors.md#matrix.errors.CommandError) | Base class for command exceptions |
| [`CommandNotFoundError`](../reference/errors.md#matrix.errors.CommandNotFoundError) | Command doesn't exist |
| [`CommandAlreadyRegisteredError`](../reference/errors.md#matrix.errors.CommandAlreadyRegisteredError) | Command name is already taken |
| [`MissingArgumentError`](../reference/errors.md#matrix.errors.MissingArgumentError) | Required argument not provided |
| [`CheckError`](../reference/errors.md#matrix.errors.CheckError) | A check function returned `False` |
| [`CooldownError`](../reference/errors.md#matrix.errors.CooldownError) | User hit the rate limit |
| [`GroupError`](../reference/errors.md#matrix.errors.GroupError) | Base class for group exceptions |
