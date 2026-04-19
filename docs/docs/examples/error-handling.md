# Error Handling

Shows both per-command error handlers and a global error handler, covering argument validation, runtime errors, and unknown commands.

```python
--8<-- "examples/error_handling.py"
```

Three layers of error handling are demonstrated:

- **Global handler** — `@bot.error(CommandNotFoundError)` catches any command the bot doesn't recognise, across the whole bot. No `ctx` is available here since no command was matched.
- **Per-command handlers** — `@division.error(ZeroDivisionError)` and `@division.error(ValueError)` handle errors raised inside the `division` function itself.
- **Argument handler** — `@division.error(MissingArgumentError)` fires when the user doesn't supply enough arguments.

Handlers are matched by exception type. If no handler is registered for a raised exception, it propagates normally.

See the [Error Handling guide](../guides/error-handling.md) for the full picture.
