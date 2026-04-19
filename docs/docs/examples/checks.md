# Checks

Shows how to restrict a command to a specific set of users using a [check](../reference/checks.md). The `!secret` command is only accessible to users in the `allowed_users` set — anyone else receives an "Access denied" reply.

```python
--8<-- "examples/checks.py"
```

Key points:

- `@secret_command.check` decorates an async function that returns `True` (allow) or `False` (deny). Returning `False` raises a [`CheckError`](../reference/errors.md).
- `@secret_command.error(CheckError)` handles the denial and sends a friendly reply instead of silently failing.
- `ctx.sender` is the full Matrix ID of the user who sent the command (e.g. `@alice:matrix.org`).

See the [Checks guide](../guides/checks.md) for built-in checks like `@is_owner` and how to compose multiple checks.
