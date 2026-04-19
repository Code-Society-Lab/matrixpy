# Cooldowns

Demonstrates two ways to apply a rate limit to a command, and how to handle the [`CooldownError`](../reference/errors.md) when the limit is exceeded.

```python
--8<-- "examples/cooldown.py"
```

There are two ways to set a cooldown:

- **`@cooldown(rate, period)` decorator** — applied before `@bot.command`. `rate=2, period=10` means 2 uses per 10 seconds per user.
- **`cooldown=(rate, period)` argument** — passed directly to `@bot.command` for a more compact one-liner.

Both produce a `CooldownError` when the limit is exceeded. The error object exposes `error.retry` — the number of seconds until the user can try again — which you can surface in the reply.
